#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from actor_session_common import (
    actor_session_path,
    list_session_primary_conflicts,
    load_actor_binding_store,
    resolve_actor_id,
    write_actor_binding_store,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _entry_sort_key(row: dict[str, Any], *, prefer_identity: str = "") -> tuple[int, int, int, str]:
    identity_id = str(row.get("identity_id", "")).strip()
    lane = str(row.get("mutation_lane", "")).strip().lower()
    lane_rank = 20
    if lane == "activate":
        lane_rank = 40
    elif lane == "session_chain_wrapper":
        lane_rank = 5
    elif lane in {"validate", "readiness", "inspection", "scan", "three-plane", "ci"}:
        lane_rank = 10
    preferred_rank = 1 if prefer_identity and identity_id == prefer_identity else 0
    version = _safe_int(row.get("binding_version"), default=0)
    updated = str(row.get("updated_at", "")).strip() or str(row.get("bound_at", "")).strip()
    return (preferred_rank, lane_rank, version, updated)


def _conflict_rows(bindings: list[dict[str, Any]], session_id: str) -> list[dict[str, Any]]:
    token = str(session_id or "").strip()
    return [
        copy.deepcopy(row)
        for row in bindings
        if isinstance(row, dict) and str(row.get("session_id", "")).strip() == token
    ]


def _select_survivor(rows: list[dict[str, Any]], *, prefer_identity: str = "") -> dict[str, Any]:
    ranked = sorted(rows, key=lambda row: _entry_sort_key(row, prefer_identity=prefer_identity))
    return copy.deepcopy(ranked[-1]) if ranked else {}


def _apply_projection_from_binding(store: dict[str, Any], binding: dict[str, Any]) -> None:
    if not binding:
        return
    for key in (
        "identity_id",
        "pack_path",
        "status",
        "bound_at",
        "session_pointer_type",
        "compatibility_mirror_pointer_path",
        "run_id",
        "switch_reason",
        "entrypoint_pid",
        "cross_actor_override_receipt",
        "updated_at",
        "session_id",
    ):
        value = binding.get(key)
        if value is None:
            continue
        store[key] = value


def _write_governance_receipt(
    *,
    catalog_path: Path,
    actor_id: str,
    run_id: str,
    approved_by: str,
    repairs: list[dict[str, Any]],
) -> Path:
    receipt_dir = (catalog_path.parent / "session" / "receipts").resolve()
    receipt_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = receipt_dir / f"actor-session-primary-repair-{actor_id.replace(':', '_')}-{timestamp}.json"
    payload = {
        "receipt_id": receipt_path.stem,
        "actor_id": actor_id,
        "run_id": run_id,
        "approved_by": approved_by,
        "approved_at": _utc_now(),
        "reason": "session_primary_conflict_repair",
        "repairs": repairs,
    }
    receipt_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair same-actor same-session cross-identity conflicts in actor binding store.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--session-id", default="", help="optional conflict session id filter")
    ap.add_argument("--prefer-identity", default="", help="identity to prefer when selecting survivor")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--approved-by", default="system:auto")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    actor_id = resolve_actor_id(args.actor_id)
    session_id_filter = str(args.session_id or "").strip()
    prefer_identity = str(args.prefer_identity or "").strip()
    run_id = str(args.run_id or "").strip() or f"session-primary-repair-{int(datetime.now(timezone.utc).timestamp())}"
    approved_by = str(args.approved_by or "").strip() or "system:auto"

    store = load_actor_binding_store(catalog_path, actor_id)
    store_path = actor_session_path(catalog_path, actor_id)
    bindings = [x for x in (store.get("bindings") or []) if isinstance(x, dict)]
    conflicts = list_session_primary_conflicts(store, session_id=session_id_filter)

    payload: dict[str, Any] = {
        "catalog_path": str(catalog_path),
        "actor_id": actor_id,
        "actor_session_path": str(store_path),
        "session_id_filter": session_id_filter,
        "prefer_identity": prefer_identity,
        "run_id": run_id,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "repair_status": STATUS_PASS_REQUIRED if conflicts else STATUS_SKIPPED_NOT_REQUIRED,
        "applied": False,
        "receipt_path": "",
        "repairs": [],
    }

    if not conflicts:
        if args.json_only:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    repairs: list[dict[str, Any]] = []
    survivors_by_session: dict[str, dict[str, Any]] = {}
    for conflict in conflicts:
        session_id = str(conflict.get("session_id", "")).strip()
        rows = _conflict_rows(bindings, session_id)
        if not rows:
            continue
        survivor = _select_survivor(rows, prefer_identity=prefer_identity)
        survivor_ref = str(survivor.get("binding_ref", "")).strip()
        removed = [
            {
                "identity_id": str(row.get("identity_id", "")).strip(),
                "binding_ref": str(row.get("binding_ref", "")).strip(),
                "binding_version": _safe_int(row.get("binding_version"), default=0),
                "mutation_lane": str(row.get("mutation_lane", "")).strip(),
                "run_id": str(row.get("run_id", "")).strip(),
            }
            for row in rows
            if str(row.get("binding_ref", "")).strip() != survivor_ref
        ]
        repairs.append(
            {
                "session_id": session_id,
                "survivor_identity_id": str(survivor.get("identity_id", "")).strip(),
                "survivor_binding_ref": survivor_ref,
                "removed_bindings": removed,
            }
        )
        survivors_by_session[session_id] = survivor

    payload["repairs"] = repairs

    if args.apply:
        receipt_path = _write_governance_receipt(
            catalog_path=catalog_path,
            actor_id=actor_id,
            run_id=run_id,
            approved_by=approved_by,
            repairs=repairs,
        )
        keep_bindings: list[dict[str, Any]] = []
        for row in bindings:
            if not isinstance(row, dict):
                continue
            sid = str(row.get("session_id", "")).strip()
            if sid not in survivors_by_session:
                keep_bindings.append(copy.deepcopy(row))
                continue
            survivor = survivors_by_session[sid]
            if str(row.get("binding_ref", "")).strip() == str(survivor.get("binding_ref", "")).strip():
                keep_bindings.append(copy.deepcopy(survivor))

        version_before = str(store.get("compare_token", "")).strip() or str(store.get("binding_version", 0))
        version_after = max(
            _safe_int(store.get("binding_version"), default=0),
            max((_safe_int(row.get("binding_version"), default=0) for row in keep_bindings), default=0),
        ) + 1
        now = _utc_now()
        updated_store = copy.deepcopy(store)
        updated_store["binding_version"] = version_after
        updated_store["compare_token"] = str(version_after)
        updated_store["session_entry_count"] = len(keep_bindings)
        updated_store["bindings"] = keep_bindings
        updated_store["updated_at"] = now
        updated_store["actor_session_path"] = str(store_path)
        updated_store["last_mutation"] = {
            "mutation_lane": "inspection",
            "session_id": session_id_filter,
            "run_id": run_id,
            "switch_reason": "session_primary_conflict_repair",
            "governance_override_receipt": str(receipt_path),
            "approved_by": approved_by,
            "compare_token_before": version_before,
            "compare_token_after": str(version_after),
            "applied_at": now,
        }
        rebind_receipts = [x for x in (updated_store.get("rebind_receipts") or []) if isinstance(x, dict)]
        for repair in repairs:
            for removed in repair.get("removed_bindings") or []:
                rebind_receipts.append(
                    {
                        "from_binding_ref": str(removed.get("binding_ref", "")).strip() or "NONE",
                        "to_binding_ref": str(repair.get("survivor_binding_ref", "")).strip() or "NONE",
                        "actor_id": actor_id,
                        "session_id": str(repair.get("session_id", "")).strip(),
                        "run_id": run_id,
                        "switch_reason": "session_primary_conflict_repair",
                        "approved_by": approved_by,
                        "applied_at": now,
                    }
                )
        updated_store["rebind_receipts"] = rebind_receipts

        overall_survivor = _select_survivor(keep_bindings, prefer_identity=prefer_identity)
        _apply_projection_from_binding(updated_store, overall_survivor)
        updated_store["governance_override_receipt"] = str(receipt_path)
        write_actor_binding_store(store_path, updated_store)
        payload["repair_status"] = STATUS_PASS_REQUIRED
        payload["applied"] = True
        payload["receipt_path"] = str(receipt_path)
        payload["compare_token_before"] = version_before
        payload["compare_token_after"] = str(version_after)

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
