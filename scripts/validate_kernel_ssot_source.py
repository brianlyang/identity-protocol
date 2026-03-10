#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CANONICAL_PATH_MISSING = "IP-KSSOT-001"
ERR_SSOT_VALIDATION_FAILED = "IP-KSSOT-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
CANONICAL_PATHS = (
    "identity/protocol/IDENTITY_PROTOCOL.md",
    "identity/protocol/IDENTITY_RUNTIME.md",
    "identity/protocol/mappings/contract-binding.current.yaml",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "kernel_canonical_source_contract_v1",
        "kernel_canonical_source_contract",
        "rq_025_kernel_canonical_source_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate kernel canonical source contract (RQ-025).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
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

    repo_root = Path(__file__).resolve().parent.parent
    canonical_paths = [str((repo_root / p).resolve()) for p in CANONICAL_PATHS]
    missing = [p for p in canonical_paths if not Path(p).exists()]

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": False,
        "requiredization_current_round_linked": True,
        "kernel_ssot_source_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "canonical_source_paths": canonical_paths,
        "missing_source_paths": missing,
        "ssot_validator_rc": 0,
        "ssot_validator_tail": "",
        "evidence_ref": canonical_paths[0] if canonical_paths else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if missing:
        payload["kernel_ssot_source_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CANONICAL_PATH_MISSING
        payload["stale_reasons"] = ["canonical_source_path_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    proc = subprocess.run(["python3", "scripts/validate_protocol_ssot_source.py"], capture_output=True, text=True)
    payload["producer_readiness"] = True
    payload["ssot_validator_rc"] = proc.returncode
    payload["ssot_validator_tail"] = (proc.stdout or proc.stderr or "").strip().splitlines()[-1] if (proc.stdout or proc.stderr) else ""
    if proc.returncode != 0:
        payload["kernel_ssot_source_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SSOT_VALIDATION_FAILED
        payload["stale_reasons"] = ["protocol_ssot_validator_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["kernel_ssot_source_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
