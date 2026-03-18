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
    ACTOR_GLOBAL_LAST_MUTATION_PROJECTION_SCOPE,
    AUTHORITY_MODEL,
    AUTHORITATIVE_BINDING_RULE,
    COMPATIBILITY_PROJECTION_STATUS_AVAILABLE,
    COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY,
    DEFAULT_BINDING_KEY_MODE,
    SESSION_ONLY_BINDING_KEY_MODE,
    actor_session_path,
    binding_compatibility_projection_allowed,
    load_actor_binding_store,
    load_actor_global_compatibility_projection_state,
    resolve_actor_id,
    write_actor_binding_store,
)

ERR_MB_001 = "IP-ASB-MB-001"
ERR_MB_002 = "IP-ASB-MB-002"
ERR_MB_003 = "IP-ASB-MB-003"
ERR_MB_004 = "IP-ASB-MB-004"
ERR_MB_005 = "IP-ASB-MB-005"
ERR_MB_006 = "IP-ASB-MB-006"
ERR_MB_007 = "IP-ASB-MB-007"
ERR_MB_008 = "IP-ASB-MB-008"
ERR_MB_009 = "IP-ASB-MB-009"
ERR_MB_010 = "IP-ASB-MB-010"
SWITCH_PRESTATE_MODE_LEGACY_CANONICAL = "legacy_canonical"
SWITCH_PRESTATE_MODE_SESSION_PRIMARY = "session_primary"
SWITCH_PRESTATE_MODE_CHOICES = {
    SWITCH_PRESTATE_MODE_LEGACY_CANONICAL,
    SWITCH_PRESTATE_MODE_SESSION_PRIMARY,
}
POINTER_SEMANTICS_VERSION = "session_pointer_compatibility_v2"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _default_canonical_out(catalog: Path) -> Path:
    return (catalog.parent / "session" / "active_identity.json").resolve()


def _default_mirror_out(catalog: Path) -> Path:
    return (catalog.parent / "session" / "mirror" / "current.json").resolve()


def _authoritative_binding_store_root(catalog: Path) -> Path:
    return (catalog.parent / "session" / "actors").resolve()


def _write_payload(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(err_code: str, reason: str) -> int:
    print(f"[FAIL] {err_code} {reason}")
    return 1


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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


def _load_canonical_identity_id(canonical_out: Path) -> str:
    if not canonical_out.exists():
        return ""
    doc = _load_json(canonical_out)
    return str(doc.get("identity_id", "")).strip()


def _compatibility_projection_metadata(*, projection: dict[str, Any] | None) -> dict[str, Any]:
    raw = projection if isinstance(projection, dict) else {}
    return {
        "compatibility_projection_scope": str(raw.get("projection_scope", "")).strip(),
        "compatibility_projection_role": str(raw.get("projection_role", "")).strip(),
        "compatibility_projection_actor_id": str(raw.get("actor_id", "")).strip(),
        "compatibility_projection_identity_id": str(raw.get("identity_id", "")).strip(),
        "compatibility_projection_session_id": str(raw.get("session_id", "")).strip(),
        "compatibility_projection_binding_ref": str(raw.get("binding_ref", "")).strip(),
        "compatibility_projection_run_id": str(raw.get("run_id", "")).strip(),
        "compatibility_projection_compare_token": str(raw.get("compare_token", "")).strip(),
        "compatibility_projection_binding_version": int(raw.get("binding_version", 0) or 0),
        "compatibility_projection_switch_reason": str(raw.get("switch_reason", "")).strip(),
        "compatibility_projection_applied_at": str(raw.get("applied_at", "")).strip(),
        "compatibility_projection_updated_at": str(raw.get("updated_at", "")).strip(),
    }


def _pointer_projection_surface(
    *,
    projection_state: dict[str, Any] | None,
    fallback_identity_id: str,
    fallback_pack_path: str,
    fallback_status: str,
) -> dict[str, str]:
    state = projection_state if isinstance(projection_state, dict) else {}
    projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    projection_status = str(state.get("projection_status", "")).strip()
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_AVAILABLE and projection:
        return {
            "identity_id": str(projection.get("identity_id", "")).strip() or fallback_identity_id,
            "pack_path": fallback_pack_path,
            "status": fallback_status,
        }
    if projection_status == COMPATIBILITY_PROJECTION_STATUS_SUPPRESSED_MULTI_IDENTITY:
        return {
            "identity_id": "",
            "pack_path": "",
            "status": "compatibility_projection_suppressed",
        }
    return {
        "identity_id": "",
        "pack_path": "",
        "status": "compatibility_projection_unavailable",
    }


def _pointer_metadata(
    *,
    catalog: Path,
    canonical_out: Path,
    projection_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = projection_state if isinstance(projection_state, dict) else {}
    projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    payload = {
        "authority_role": "compatibility_mirror",
        "authority_model": AUTHORITY_MODEL,
        "authoritative_binding_rule": AUTHORITATIVE_BINDING_RULE,
        "authoritative_binding_store_root": str(_authoritative_binding_store_root(catalog)),
        "authoritative_decision_allowed": False,
        "pointer_semantics_version": POINTER_SEMANTICS_VERSION,
        "authoritative_source": "actor_session_store",
        "canonical_session_pointer": str(canonical_out),
        "compatibility_projection_status": str(state.get("projection_status", "")).strip(),
        "compatibility_projection_reason": str(state.get("projection_reason", "")).strip(),
        "compatibility_projection_candidate_identity_ids": [
            str(item).strip()
            for item in (state.get("projection_candidate_identity_ids") or [])
            if str(item).strip()
        ],
    }
    payload.update(_compatibility_projection_metadata(projection=projection))
    return payload


def _current_projection_identity(projection_state: dict[str, Any] | None) -> str:
    state = projection_state if isinstance(projection_state, dict) else {}
    projection = state.get("projection") if isinstance(state.get("projection"), dict) else {}
    return str(projection.get("identity_id", "")).strip()


def _resolve_compatibility_projection_decision(
    *,
    store: dict[str, Any],
    mutation_lane: str,
    actor_id: str,
    target_identity_id: str,
    switch_intent_receipt: str,
) -> dict[str, Any]:
    projection_before = _actor_global_projection_state_for_store(store)
    previous_identity_id = _current_projection_identity(projection_before)
    receipt_path = str(switch_intent_receipt or "").strip()
    if mutation_lane != "activate":
        return {
            "allowed": False,
            "reason": "non_activate_lane_observation_only",
            "receipt_path": "",
            "previous_identity_id": previous_identity_id,
        }
    if not previous_identity_id or previous_identity_id == target_identity_id:
        return {
            "allowed": True,
            "reason": "bootstrap_or_same_identity_refresh",
            "receipt_path": receipt_path,
            "previous_identity_id": previous_identity_id,
        }
    if not receipt_path:
        return {
            "allowed": False,
            "reason": "actor_global_projection_switch_receipt_missing",
            "receipt_path": "",
            "previous_identity_id": previous_identity_id,
        }
    receipt_errors = _validate_switch_intent_receipt(
        receipt_path=receipt_path,
        actor_id=actor_id,
        from_identity_id=previous_identity_id,
        to_identity_id=target_identity_id,
    )
    if receipt_errors:
        raise ValueError(f"{ERR_MB_010}:compatibility_projection_switch_intent_receipt_invalid:{','.join(receipt_errors)}")
    return {
        "allowed": True,
        "reason": "actor_global_projection_switch_receipt_validated",
        "receipt_path": receipt_path,
        "previous_identity_id": previous_identity_id,
    }


def _actor_global_projection_state_for_store(store: dict[str, Any]) -> dict[str, Any]:
    return load_actor_global_compatibility_projection_state(
        Path(str(store.get("catalog_path", "")).strip()),
        str(store.get("actor_id", "")).strip(),
    )


def _resolve_switch_from_identity(
    *,
    switch_prestate_mode: str,
    switch_from_identity: str,
    canonical_out: Path,
) -> tuple[str, str]:
    mode = str(switch_prestate_mode or "").strip().lower() or SWITCH_PRESTATE_MODE_LEGACY_CANONICAL
    if mode not in SWITCH_PRESTATE_MODE_CHOICES:
        mode = SWITCH_PRESTATE_MODE_LEGACY_CANONICAL
    explicit_before = str(switch_from_identity or "").strip()
    if mode == SWITCH_PRESTATE_MODE_SESSION_PRIMARY:
        return explicit_before, mode
    return explicit_before or _load_canonical_identity_id(canonical_out), mode


def _validate_switch_intent_receipt(
    *,
    receipt_path: str,
    actor_id: str,
    from_identity_id: str,
    to_identity_id: str,
) -> list[str]:
    p = Path(receipt_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return ["switch_intent_receipt_missing"]
    data = _load_json(p)
    if not data:
        return ["switch_intent_receipt_not_object_or_parse_failed"]
    errors: list[str] = []
    actor_receipt = str(data.get("actor_id", "")).strip()
    from_receipt = str(data.get("from_identity_id", "")).strip()
    to_receipt = str(data.get("to_identity_id", "")).strip()
    if actor_receipt != actor_id:
        errors.append("switch_intent_receipt_actor_mismatch")
    if from_receipt != from_identity_id:
        errors.append("switch_intent_receipt_from_identity_mismatch")
    if to_receipt != to_identity_id:
        errors.append("switch_intent_receipt_to_identity_mismatch")
    return errors


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
    compatibility_projection_decision: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    now = _utc_now()
    existing_bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
    key_mode = str(store.get("binding_key_mode", "")).strip() or DEFAULT_BINDING_KEY_MODE

    def binding_key(row: dict[str, Any]) -> str:
        sid = str(row.get("session_id", "")).strip()
        iid = str(row.get("identity_id", "")).strip()
        if key_mode == SESSION_ONLY_BINDING_KEY_MODE:
            return sid
        return f"{iid}::{sid}"

    target_key = f"{target_identity_id}::{session_id}" if key_mode != SESSION_ONLY_BINDING_KEY_MODE else session_id

    pre_binding_ref = next(
        (
            str(x.get("binding_ref", "")).strip()
            for x in existing_bindings
            if binding_key(x) == target_key and str(x.get("binding_ref", "")).strip()
        ),
        "NONE",
    )
    existing_for_session = [x for x in existing_bindings if binding_key(x) == target_key]
    bound_at = now
    if existing_for_session:
        latest = sorted(existing_for_session, key=_entry_sort_key)[-1]
        bound_at = str(latest.get("bound_at", "")).strip() or bound_at

    next_version = int(store.get("binding_version", 0)) + 1
    next_binding_ref = f"{actor_id}:{target_identity_id}:{session_id}:v{next_version}"
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
        "compatibility_projection_allowed": bool(compatibility_projection_decision.get("allowed")),
        "compatibility_projection_reason": str(compatibility_projection_decision.get("reason", "")).strip(),
        "compatibility_projection_receipt": str(compatibility_projection_decision.get("receipt_path", "")).strip(),
        "compatibility_projection_previous_identity_id": str(
            compatibility_projection_decision.get("previous_identity_id", "")
        ).strip(),
    }

    merged: list[dict[str, Any]] = []
    replaced = False
    for row in existing_bindings:
        if binding_key(row) == target_key:
            if not replaced:
                merged.append(updated_entry)
                replaced = True
            continue
        merged.append(row)
    if not replaced:
        merged.append(updated_entry)

    if bool(compatibility_projection_decision.get("allowed")):
        previous_identity_id = str(compatibility_projection_decision.get("previous_identity_id", "")).strip()
        if previous_identity_id and previous_identity_id != target_identity_id:
            for row in merged:
                if not isinstance(row, dict):
                    continue
                if row is updated_entry:
                    continue
                if not binding_compatibility_projection_allowed(row):
                    continue
                if str(row.get("identity_id", "")).strip() == target_identity_id:
                    continue
                row["compatibility_projection_allowed"] = False
                row["compatibility_projection_reason"] = "superseded_by_actor_global_projection_switch"
                row["compatibility_projection_previous_identity_id"] = previous_identity_id
                row["compatibility_projection_receipt"] = str(
                    compatibility_projection_decision.get("receipt_path", "")
                ).strip()

    pre_keys = {binding_key(x) for x in existing_bindings if binding_key(x)}
    post_keys = {binding_key(x) for x in merged if binding_key(x)}
    dropped_peers = sorted(x for x in pre_keys if x != target_key and x not in post_keys)
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
            "compatibility_projection_allowed": bool(compatibility_projection_decision.get("allowed")),
            "compatibility_projection_reason": str(compatibility_projection_decision.get("reason", "")).strip(),
            "compatibility_projection_receipt": str(compatibility_projection_decision.get("receipt_path", "")).strip(),
            "compatibility_projection_previous_identity_id": str(
                compatibility_projection_decision.get("previous_identity_id", "")
            ).strip(),
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
    ap.add_argument(
        "--switch-intent-receipt",
        default="",
        help="receipt required when canonical pointer switches identity (actor_id/from_identity_id/to_identity_id tuple-bound)",
    )
    ap.add_argument(
        "--switch-from-identity",
        default="",
        help="explicit pre-switch identity authority; identity_creator passes session-primary state here",
    )
    ap.add_argument(
        "--switch-prestate-mode",
        default=SWITCH_PRESTATE_MODE_LEGACY_CANONICAL,
        choices=sorted(SWITCH_PRESTATE_MODE_CHOICES),
        help=(
            "selects the authority used for switch-intent receipt validation: "
            "legacy_canonical uses canonical pointer fallback; session_primary uses only --switch-from-identity"
        ),
    )
    ap.add_argument(
        "--session-id-source",
        default="",
        help="session id source tag (explicit_session_id/run_id); activate lane requires explicit_session_id",
    )
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
    profile = str(target.get("profile", "")).strip().lower()
    runtime_mode = str(target.get("runtime_mode", "")).strip().lower()
    if status != "active":
        print(f"[FAIL] identity is not active; status={status}")
        return 1
    if profile == "fixture" or runtime_mode == "demo_only":
        print(
            "[FAIL] identity is not runtime-eligible for canonical session authority; "
            f"profile={profile or 'missing'} runtime_mode={runtime_mode or 'missing'}"
        )
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
    payload.update(_pointer_metadata(catalog=catalog, canonical_out=canonical_out))

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

    actor_id = resolve_actor_id(args.actor_id)
    actor_out = actor_session_path(catalog, actor_id)
    mutation_lane = str(args.mutation_lane or "").strip().lower() or "activate"
    override_receipt = str(args.governance_override_receipt or "").strip()
    if mutation_lane != "activate" and not override_receipt:
        return _fail(ERR_MB_004, "non_activation_mutation_without_override_receipt")

    session_id, session_id_source = _derive_session_id(args.session_id, args.run_id)
    session_id_source_input = str(args.session_id_source or "").strip()
    if session_id_source_input:
        session_id_source = session_id_source_input
    if not session_id:
        return _fail(ERR_MB_005, "session_id_missing_and_run_id_missing")
    if mutation_lane == "activate" and session_id_source != "explicit_session_id":
        return _fail(ERR_MB_007, "activate_requires_explicit_session_id")

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
    switch_before_identity, switch_prestate_mode = _resolve_switch_from_identity(
        switch_prestate_mode=str(args.switch_prestate_mode or "").strip(),
        switch_from_identity=str(args.switch_from_identity or "").strip(),
        canonical_out=canonical_out,
    )
    if switch_before_identity and switch_before_identity != args.identity_id:
        switch_receipt = str(args.switch_intent_receipt or "").strip()
        if not switch_receipt:
            if switch_prestate_mode == SWITCH_PRESTATE_MODE_SESSION_PRIMARY:
                missing_reason = "session_primary_identity_switch_requires_switch_intent_receipt"
            else:
                missing_reason = "canonical_pointer_identity_switch_requires_switch_intent_receipt"
            return _fail(
                ERR_MB_008,
                (
                    f"{missing_reason} "
                    f"from={switch_before_identity} to={args.identity_id}"
                ),
            )
        receipt_errors = _validate_switch_intent_receipt(
            receipt_path=switch_receipt,
            actor_id=actor_id,
            from_identity_id=switch_before_identity,
            to_identity_id=args.identity_id,
        )
        if receipt_errors:
            return _fail(ERR_MB_009, "switch_intent_receipt_invalid:" + ",".join(receipt_errors))
    try:
        compatibility_projection_decision = _resolve_compatibility_projection_decision(
            store=store,
            mutation_lane=mutation_lane,
            actor_id=actor_id,
            target_identity_id=args.identity_id,
            switch_intent_receipt=str(args.switch_intent_receipt or "").strip(),
        )
    except ValueError as exc:
        token = str(exc)
        if token.startswith(f"{ERR_MB_010}:"):
            return _fail(ERR_MB_010, token.split(":", 1)[1])
        raise
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
            compatibility_projection_decision=compatibility_projection_decision,
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
    projection_after = load_actor_global_compatibility_projection_state(catalog, actor_id)
    pointer_surface = _pointer_projection_surface(
        projection_state=projection_after,
        fallback_identity_id=args.identity_id,
        fallback_pack_path=str(target.get("pack_path", "")),
        fallback_status=status,
    )
    payload["identity_id"] = pointer_surface["identity_id"]
    payload["pack_path"] = pointer_surface["pack_path"]
    payload["status"] = pointer_surface["status"]
    payload["compatibility_projection_write_allowed"] = bool(compatibility_projection_decision.get("allowed"))
    payload["compatibility_projection_write_reason"] = str(compatibility_projection_decision.get("reason", "")).strip()
    payload["compatibility_projection_previous_identity_id"] = str(
        compatibility_projection_decision.get("previous_identity_id", "")
    ).strip()
    payload.update(_pointer_metadata(catalog=catalog, canonical_out=canonical_out, projection_state=projection_after))
    print(
        "[OK] session identity actor-bound: "
        f"{actor_out} session_id={session_id} compare_token={compare_token_after} lane={mutation_lane}"
    )
    if not bool(compatibility_projection_decision.get("allowed")):
        print(
            "[INFO] canonical pointer write skipped: "
            f"reason={str(compatibility_projection_decision.get('reason', '')).strip() or 'not_projection_eligible'}"
        )
        return 0
    try:
        _write_payload(canonical_out, payload)
    except Exception as exc:
        # Rollback actor binding store to pre-mutation snapshot when canonical write fails.
        try:
            write_actor_binding_store(actor_out, store)
        except Exception as rb_exc:
            print(f"[FAIL] canonical session sync failed and actor rollback failed: {canonical_out} ({exc}); rollback_error={rb_exc}")
            return 1
        print(f"[FAIL] canonical session sync failed: {canonical_out} ({exc}); actor binding rolled back")
        return 1
    print(f"[OK] session identity synced (canonical): {canonical_out}")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
