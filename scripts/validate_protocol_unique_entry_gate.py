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
ENTRY_RECEIPT_STATE_FILE = "required_gate_bundle_entry.latest.json"
ENTRY_RECEIPT_HISTORY_GLOB = "required-gate-bundle-entry-*.json"

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


def _resolve_entry_receipt_path(*, pack_path: Path, explicit_path: str) -> Path | None:
    if str(explicit_path or "").strip():
        p = Path(explicit_path).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    latest = (pack_path / "runtime" / "state" / ENTRY_RECEIPT_STATE_FILE).resolve()
    if latest.exists() and latest.is_file():
        return latest

    history_dir = (pack_path / "runtime" / "reports" / "required-gate-bundle-entry").resolve()
    if not history_dir.exists() or not history_dir.is_dir():
        return None
    candidates = sorted(history_dir.glob(ENTRY_RECEIPT_HISTORY_GLOB), key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0].resolve() if candidates else None


def _load_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("receipt_payload_not_object")
    return data


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
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--entry-receipt", default="")
    ap.add_argument("--require-entry-receipt", action="store_true")
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
        return 2

    contract, contract_key = _resolve_contract(task)
    declared_required = contract_required(contract)
    strict_operation = str(args.operation).strip().lower() in STRICT_OPERATIONS
    required = bool(args.force_check or args.force_required or declared_required or strict_operation)
    run_id = str(args.run_id or "").strip()

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
        "protocol_unique_entry_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_receipt_path": "",
        "protocol_unique_entry_receipt_bundle_key": "",
        "protocol_unique_entry_receipt_run_id": "",
        "protocol_unique_entry_receipt_operation": "",
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

    receipt_required = bool(args.require_entry_receipt or strict_operation)
    if receipt_required:
        receipt_path = _resolve_entry_receipt_path(pack_path=pack_path, explicit_path=str(args.entry_receipt or ""))
        if receipt_path is None:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = ["entry_receipt_missing"]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["protocol_unique_entry_receipt_path"] = str(receipt_path)
        try:
            receipt = _load_receipt(receipt_path)
        except Exception as exc:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = [f"entry_receipt_invalid:{exc}"]
            _emit(payload, json_only=args.json_only)
            return 1

        receipt_bundle_key = str(receipt.get("bundle_key", "")).strip()
        receipt_identity_id = str(receipt.get("identity_id", "")).strip()
        receipt_operation = str(receipt.get("operation", "")).strip().lower()
        receipt_run_id = str(receipt.get("run_id_binding", "")).strip()
        receipt_bundle_status = str(receipt.get("bundle_status", "")).strip().upper()
        payload["protocol_unique_entry_receipt_bundle_key"] = receipt_bundle_key
        payload["protocol_unique_entry_receipt_run_id"] = receipt_run_id
        payload["protocol_unique_entry_receipt_operation"] = receipt_operation

        receipt_issues: list[str] = []
        if receipt_bundle_key != EXPECTED_BUNDLE_KEY:
            receipt_issues.append("entry_receipt_bundle_key_mismatch")
        if receipt_identity_id != str(args.identity_id).strip():
            receipt_issues.append("entry_receipt_identity_mismatch")
        if receipt_operation != str(args.operation).strip().lower():
            receipt_issues.append("entry_receipt_operation_mismatch")
        if receipt_bundle_status != STATUS_PASS_REQUIRED:
            receipt_issues.append("entry_receipt_bundle_status_not_pass")
        if run_id and receipt_run_id != run_id:
            receipt_issues.append("entry_receipt_run_id_mismatch")

        if receipt_issues:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = receipt_issues
            _emit(payload, json_only=args.json_only)
            return 1

        payload["protocol_unique_entry_receipt_status"] = STATUS_PASS_REQUIRED

    payload["protocol_unique_entry_gate_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
