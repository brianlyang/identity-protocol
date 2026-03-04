#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import (
    DEFAULT_BINDING_KEY_MODE,
    actor_session_path,
    load_actor_binding_store,
    resolve_actor_id,
    write_actor_binding_store,
)

ERR_MB_001 = "IP-ASB-MB-001"
ERR_MB_002 = "IP-ASB-MB-002"
ERR_MB_003 = "IP-ASB-MB-003"
ERR_MB_004 = "IP-ASB-MB-004"
ERR_MB_005 = "IP-ASB-MB-005"
ERR_MB_006 = "IP-ASB-MB-006"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _default_canonical_out(catalog: Path) -> Path:
    return (catalog.parent / "session" / "active_identity.json").resolve()


def _default_mirror_out(catalog: Path) -> Path:
    return (catalog.parent / "session" / "mirror" / "current.json").resolve()


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(err_code: str, reason: str) -> int:
    print(f"[FAIL] {err_code} {reason}")
    return 1


def _entry_sort_key(row: dict[str, Any]) -> tuple[int, str]:
    try:
        version = int(row.get("binding_version", 0))
    except Exception:
        version = 0
    updated = str(row.get("updated_at", "")).strip() or str(row.get("bound_at", "")).strip()
    return (version, updated)


def _derive_session_id(explicit_session_id: str, run_id: str) -> tuple[str, str]:
    sid = str(explicit_session_id or "").strip()
    if sid:
        return sid, "explicit_session_id"
    rid = str(run_id or "").strip()
    if rid:
        return f"run:{rid}", "run_id"
    return "", ""


def _build_actor_payload(
    *,
    store: dict[str, Any],
    actor_id: str,
    session_id: str,
    session_id_source: str,
    target_identity_id: str,
    pack_path: str,
    catalog: Path,
    status: str,
    canonical_out: Path,
    run_id: str,
    switch_reason: str,
    entrypoint_pid: str,
    cross_actor_override_receipt: str,
    mutation_lane: str,
    override_receipt: str,
    approved_by: str,
    compare_token_before: str,
) -> tuple[dict[str, Any], str]:
    now = _utc_now()
    existing_bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]

    pre_binding_ref = next(
        (
            str(x.get("binding_ref", "")).strip()
            for x in existing_bindings
            if str(x.get("session_id", "")).strip() == session_id and str(x.get("binding_ref", "")).strip()
        ),
        "NONE",
    )
    existing_for_session = [x for x in existing_bindings if str(x.get("session_id", "")).strip() == session_id]
    bound_at = now
    if existing_for_session:
        latest = sorted(existing_for_session, key=_entry_sort_key)[-1]
        bound_at = str(latest.get("bound_at", "")).strip() or bound_at

    next_version = int(store.get("binding_version", 0)) + 1
    next_binding_ref = f"{actor_id}:{session_id}:v{next_version}"
    updated_entry = {
        "actor_id": actor_id,
        "session_id": session_id,
        "session_id_source": session_id_source,
        "identity_id": target_identity_id,
        "catalog_path": str(catalog),
        "pack_path": pack_path,
        "status": status,
        "bound_at": bound_at,
        "updated_at": now,
        "session_pointer_type": "actor_binding",
        "canonical_session_pointer": str(canonical_out),
        "run_id": run_id,
        "switch_reason": switch_reason,
        "entrypoint_pid": entrypoint_pid,
        "cross_actor_override_receipt": cross_actor_override_receipt,
        "binding_ref": next_binding_ref,
        "binding_version": next_version,
        "compare_token": str(next_version),
        "mutation_lane": mutation_lane,
        "governance_override_receipt": override_receipt,
        "approved_by": approved_by,
    }

    merged: list[dict[str, Any]] = []
    replaced = False
    for row in existing_bindings:
        sid = str(row.get("session_id", "")).strip()
        if sid == session_id:
            if not replaced:
                merged.append(updated_entry)
                replaced = True
            continue
        merged.append(row)
    if not replaced:
        merged.append(updated_entry)

    pre_sessions = {str(x.get("session_id", "")).strip() for x in existing_bindings if str(x.get("session_id", "")).strip()}
    post_sessions = {str(x.get("session_id", "")).strip() for x in merged if str(x.get("session_id", "")).strip()}
    dropped_peers = sorted(x for x in pre_sessions if x != session_id and x not in post_sessions)
    if dropped_peers:
        raise ValueError(f"{ERR_MB_006}:peer_session_dropped:{','.join(dropped_peers)}")

    receipt = {
        "from_binding_ref": pre_binding_ref,
        "to_binding_ref": next_binding_ref,
        "actor_id": actor_id,
        "session_id": session_id,
        "run_id": run_id,
        "switch_reason": switch_reason,
        "approved_by": approved_by,
        "applied_at": now,
        "mutation_lane": mutation_lane,
        "governance_override_receipt": override_receipt,
        "compare_token_before": compare_token_before,
        "compare_token_after": str(next_version),
    }
    required_receipt_fields = (
        "to_binding_ref",
        "actor_id",
        "session_id",
        "run_id",
        "switch_reason",
        "applied_at",
    )
    missing_receipt = [k for k in required_receipt_fields if not str(receipt.get(k, "")).strip()]
    if missing_receipt:
        raise ValueError(f"{ERR_MB_005}:rebind_receipt_missing_fields:{','.join(missing_receipt)}")

    old_receipts = [x for x in (store.get("rebind_receipts") or []) if isinstance(x, dict)]
    next_receipts = [*old_receipts, receipt]

    actor_payload = {
        "schema_version": store.get("schema_version") or "actor_session_multibinding_v1",
        "actor_id": actor_id,
        "catalog_path": str(catalog),
        "binding_key_mode": DEFAULT_BINDING_KEY_MODE,
        "binding_version": next_version,
        "compare_token": str(next_version),
        "session_entry_count": len(merged),
        "bindings": merged,
        "rebind_receipts": next_receipts,
        "last_mutation": {
            "mutation_lane": mutation_lane,
            "session_id": session_id,
            "run_id": run_id,
            "switch_reason": switch_reason,
            "governance_override_receipt": override_receipt,
            "approved_by": approved_by,
            "compare_token_before": compare_token_before,
            "compare_token_after": str(next_version),
            "applied_at": now,
        },
        # compatibility mirrors (for legacy readers in migration window)
        "identity_id": target_identity_id,
        "pack_path": pack_path,
        "status": status,
        "bound_at": bound_at,
        "session_pointer_type": "actor_binding",
        "canonical_session_pointer": str(canonical_out),
        "run_id": run_id,
        "switch_reason": switch_reason,
        "entrypoint_pid": entrypoint_pid,
        "cross_actor_override_receipt": cross_actor_override_receipt,
        "updated_at": now,
    }
    return actor_payload, str(next_version)


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync active identity into session evidence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--out",
        default="",
        help="canonical session pointer output path; default: <catalog_dir>/session/active_identity.json",
    )
    ap.add_argument(
        "--mirror-out",
        default="",
        help=(
            "optional mirror pointer path; default: <catalog_dir>/session/mirror/current.json. "
            "empty string disables mirror write"
        ),
    )
    ap.add_argument(
        "--legacy-mirror-out",
        default="",
        help=(
            "optional legacy mirror pointer path (for compatibility only, e.g. /tmp/identity-session/current.json). "
            "empty string disables legacy mirror write"
        ),
    )
    ap.add_argument(
        "--require-mirror",
        action="store_true",
        help="treat mirror/legacy-mirror write failure as fatal (default failure is warning-only)",
    )
    ap.add_argument("--actor-id", default="", help="actor id for actor-scoped session binding write")
    ap.add_argument("--run-id", default="", help="run id associated with this session sync")
    ap.add_argument("--switch-reason", default="", help="reason for activation/switch")
    ap.add_argument("--entrypoint-pid", default="", help="entrypoint process id for audit trail")
    ap.add_argument(
        "--cross-actor-override-receipt",
        default="",
        help="override receipt path when cross-actor demotion was explicitly approved",
    )
    ap.add_argument("--session-id", default="", help="actor session id; defaults to run:<run-id> when run-id provided")
    ap.add_argument(
        "--compare-token",
        default="",
        help="CAS compare token for actor binding store (required in strict lanes)",
    )
    ap.add_argument(
        "--mutation-lane",
        default="activate",
        choices=["activate", "validate", "scan", "readiness", "three-plane", "full-scan", "ci", "inspection"],
        help="operation lane for canonical actor binding mutation boundary",
    )
    ap.add_argument(
        "--governance-override-receipt",
        default="",
        help="explicit governance override receipt required for non-activate canonical mutations",
    )
    ap.add_argument("--approved-by", default="", help="manual override approver for rebind receipt")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 1
    data = _load_yaml(catalog)
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    target = next((x for x in rows if str(x.get("id", "")).strip() == args.identity_id), None)
    if not target:
        print(f"[FAIL] identity not found in catalog: {args.identity_id}")
        return 1
    status = str(target.get("status", "")).strip().lower()
    if status != "active":
        print(f"[FAIL] identity is not active; status={status}")
        return 1

    canonical_out = Path(args.out).expanduser().resolve() if args.out.strip() else _default_canonical_out(catalog)
    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(target.get("pack_path", "")),
        "status": status,
        "synced_at": _utc_now(),
        "session_pointer_type": "canonical",
    }
    try:
        _write_payload(canonical_out, payload)
    except Exception as exc:
        print(f"[FAIL] canonical session sync failed: {canonical_out} ({exc})")
        return 1
    print(f"[OK] session identity synced (canonical): {canonical_out}")

    mirror_targets: list[Path] = []
    mirror_raw = args.mirror_out.strip()
    if mirror_raw:
        mirror_targets.append(Path(mirror_raw).expanduser().resolve())
    else:
        mirror_targets.append(_default_mirror_out(catalog))
    legacy_mirror_raw = args.legacy_mirror_out.strip()
    if legacy_mirror_raw:
        mirror_targets.append(Path(legacy_mirror_raw).expanduser().resolve())

    dedup_targets: list[Path] = []
    seen: set[str] = set()
    for t in mirror_targets:
        k = str(t)
        if k in seen:
            continue
        seen.add(k)
        dedup_targets.append(t)

    for mirror_out in dedup_targets:
        if mirror_out == canonical_out:
            print("[INFO] mirror path equals canonical path; mirror write skipped")
            continue
        mirror_payload = dict(payload)
        mirror_payload["session_pointer_type"] = "mirror"
        mirror_payload["canonical_session_pointer"] = str(canonical_out)
        try:
            _write_payload(mirror_out, mirror_payload)
            print(f"[OK] session identity mirrored: {mirror_out}")
        except Exception as exc:
            msg = f"mirror session sync failed: {mirror_out} ({exc})"
            if args.require_mirror:
                print(f"[FAIL] {msg}")
                return 1
            print(f"[WARN] {msg}")

    actor_id = resolve_actor_id(args.actor_id)
    actor_out = actor_session_path(catalog, actor_id)
    mutation_lane = str(args.mutation_lane or "").strip().lower() or "activate"
    override_receipt = str(args.governance_override_receipt or "").strip()
    if mutation_lane != "activate" and not override_receipt:
        return _fail(ERR_MB_004, "non_activation_mutation_without_override_receipt")

    session_id, session_id_source = _derive_session_id(args.session_id, args.run_id)
    if not session_id:
        return _fail(ERR_MB_005, "session_id_missing_and_run_id_missing")

    store = load_actor_binding_store(catalog, actor_id)

    compare_token = str(args.compare_token or "").strip()
    if not compare_token:
        return _fail(ERR_MB_002, "compare_token_missing")
    expected_token = str(store.get("compare_token", "")).strip() or str(store.get("binding_version", 0))
    if compare_token != expected_token:
        return _fail(ERR_MB_003, f"stale_compare_token expected={expected_token} got={compare_token}")

    run_id = str(args.run_id or "").strip()
    switch_reason = str(args.switch_reason or "").strip() or "explicit_activate"
    entrypoint_pid = str(args.entrypoint_pid or "").strip() or str(os.getpid())
    approved_by = str(args.approved_by or "").strip() or "system:auto"
    cross_actor_override_receipt = str(args.cross_actor_override_receipt or "").strip()
    try:
        actor_payload, compare_token_after = _build_actor_payload(
            store=store,
            actor_id=actor_id,
            session_id=session_id,
            session_id_source=session_id_source,
            target_identity_id=args.identity_id,
            pack_path=str(target.get("pack_path", "")),
            catalog=catalog,
            status=status,
            canonical_out=canonical_out,
            run_id=run_id,
            switch_reason=switch_reason,
            entrypoint_pid=entrypoint_pid,
            cross_actor_override_receipt=cross_actor_override_receipt,
            mutation_lane=mutation_lane,
            override_receipt=override_receipt,
            approved_by=approved_by,
            compare_token_before=compare_token,
        )
    except ValueError as exc:
        token = str(exc)
        if token.startswith(f"{ERR_MB_005}:"):
            return _fail(ERR_MB_005, token.split(":", 1)[1])
        if token.startswith(f"{ERR_MB_006}:"):
            return _fail(ERR_MB_006, token.split(":", 1)[1])
        return _fail(ERR_MB_005, token)

    try:
        write_actor_binding_store(actor_out, actor_payload)
    except Exception as exc:
        print(f"[FAIL] actor session binding sync failed: {actor_out} ({exc})")
        return 1
    print(
        "[OK] session identity actor-bound: "
        f"{actor_out} session_id={session_id} compare_token={compare_token_after} lane={mutation_lane}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
