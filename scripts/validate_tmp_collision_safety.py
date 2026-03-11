#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from runtime_temp_path_common import runtime_temp_dir, runtime_temp_file, runtime_temp_root
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_TMP_COLLISION = "IP-TMP-001"
ERR_TMP_SCOPE_MISSING = "IP-TMP-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "tmp_collision_safe_allocator_contract_v1",
        "tmp_collision_safe_allocator_contract",
        "rq_011_tmp_collision_safe_allocator_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate tmp collision-safe allocator contract (RQ-011).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required = contract_required(contract)
    if args.force_required:
        required = True

    run_id = str(args.run_id or "").strip() or f"tmp-{int(time.time())}"
    run_id_2 = f"{run_id}-peer"
    d1 = runtime_temp_dir(channel="collision-safe", operation=args.operation, identity_id=args.identity_id, run_token=run_id)
    d2 = runtime_temp_dir(channel="collision-safe", operation=args.operation, identity_id=args.identity_id, run_token=run_id_2)
    d3 = runtime_temp_dir(channel="collision-safe", operation=args.operation, identity_id=f"{args.identity_id}-peer", run_token=run_id)
    f1 = runtime_temp_file(channel="collision-safe", operation=args.operation, identity_id=args.identity_id, run_token=run_id, stem="evidence", ext="json")
    f2 = runtime_temp_file(channel="collision-safe", operation=args.operation, identity_id=args.identity_id, run_token=run_id_2, stem="evidence", ext="json")
    f3 = runtime_temp_file(channel="collision-safe", operation=args.operation, identity_id=f"{args.identity_id}-peer", run_token=run_id, stem="evidence", ext="json")
    paths = [d1, d2, d3, f1, f2, f3]

    serialized = [str(p.resolve()) for p in paths]
    unique_count = len(set(serialized))
    collision_count = len(serialized) - unique_count
    root = runtime_temp_root()
    within_root = all(Path(p).resolve().as_posix().startswith(root.as_posix()) for p in paths)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": True,
        "requiredization_current_round_linked": True,
        "tmp_collision_safety_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "tmp_root": str(root),
        "generated_paths": serialized,
        "collision_count": collision_count,
        "unique_path_count": unique_count,
        "path_scope_guard_status": STATUS_PASS_REQUIRED if within_root else STATUS_FAIL_REQUIRED,
        "evidence_ref": str(root),
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not within_root:
        payload["tmp_collision_safety_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TMP_SCOPE_MISSING
        payload["stale_reasons"] = ["generated_path_outside_runtime_temp_root"]
        _emit(payload, json_only=args.json_only)
        return 1

    if collision_count > 0:
        payload["tmp_collision_safety_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TMP_COLLISION
        payload["stale_reasons"] = ["tmp_path_collision_detected"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["tmp_collision_safety_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
