#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-GATE-ENTRY-001"
ERR_CONTRACT_INVALID = "IP-GATE-ENTRY-002"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
}

EXPECTED_ENTRY_SCRIPT = "scripts/required_gate_bundle_runner.py"
EXPECTED_BUNDLE_KEY = "required_gate_bundle_runner"
EXPECTED_SCOPE = "all_identity_instance_actions"
EXPECTED_ENTRY_ERROR_FAMILY = {"IP-GATE-ENTRY-001", "IP-GATE-ENTRY-002"}

CONTRACT_KEYS = (
    "protocol_unique_entry_gate_contract_v1",
    "protocol_unique_entry_gate_contract",
    "rq_036_protocol_unique_entry_gate_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw, key
    for key, raw in task.items():
        if not isinstance(raw, dict):
            continue
        token = str(key or "").strip().lower()
        if "unique_entry" in token and "contract" in token:
            return raw, str(key)
    return {}, CONTRACT_KEYS[0]


def _as_str_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol unique-entry gate contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=[
            "activate",
            "update",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "scan",
            "three-plane",
            "inspection",
            "mutation",
        ],
        default="validate",
    )
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        _pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 2

    contract, contract_key = _resolve_contract(task)
    declared_required = contract_required(contract)
    strict_operation = str(args.operation).strip().lower() in STRICT_OPERATIONS
    required = bool(args.force_check or declared_required or strict_operation)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required,
        "declared_required_contract": declared_required,
        "strict_operation": strict_operation,
        "contract_key_used": contract_key,
        "protocol_unique_entry_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_script": "",
        "protocol_unique_entry_bundle_key": "",
        "protocol_unique_entry_scope": "",
        "protocol_unique_entry_required_operations": [],
        "protocol_unique_entry_error_family": [],
        "error_code": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["unique_entry_contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    entry_script = str(contract.get("entry_script", "")).strip()
    validator_script = str(contract.get("validator", "")).strip()
    bundle_key = str(contract.get("bundle_key", "")).strip()
    scope = str(contract.get("scope", "")).strip()
    required_ops = _as_str_set(contract.get("enforce_on_operations"))
    error_family = _as_str_set(contract.get("entry_error_family"))

    payload["protocol_unique_entry_script"] = entry_script
    payload["protocol_unique_entry_bundle_key"] = bundle_key
    payload["protocol_unique_entry_scope"] = scope
    payload["protocol_unique_entry_required_operations"] = sorted(required_ops)
    payload["protocol_unique_entry_error_family"] = sorted(error_family)

    if contract.get("required") is not True:
        issues.append("contract_required_flag_not_true")
    if validator_script != "scripts/validate_protocol_unique_entry_gate.py":
        issues.append("validator_script_mismatch")
    if entry_script != EXPECTED_ENTRY_SCRIPT:
        issues.append("entry_script_mismatch")
    if bundle_key != EXPECTED_BUNDLE_KEY:
        issues.append("bundle_key_mismatch")
    if scope != EXPECTED_SCOPE:
        issues.append("scope_mismatch")
    if not STRICT_OPERATIONS.issubset(required_ops):
        issues.append("strict_operations_not_fully_covered")
    if not EXPECTED_ENTRY_ERROR_FAMILY.issubset(error_family):
        issues.append("entry_error_family_missing_required_codes")

    if issues:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_unique_entry_gate_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
