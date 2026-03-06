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

ERR_DRIVER_MISSING = "IP-PBOOT-001"
ERR_PROMPT_MISSING = "IP-PBOOT-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
DEFAULT_DRIVERS = (
    "scripts/validate_identity_tool_installation.py",
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "prompt_bootstrap_capability_contract_v1",
        "prompt_bootstrap_capability_contract",
        "rq_014_prompt_bootstrap_capability_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _required_drivers(contract: dict[str, Any]) -> list[str]:
    rows = contract.get("required_capability_drivers")
    if isinstance(rows, list):
        vals = [str(x).strip() for x in rows if str(x).strip()]
        if vals:
            return vals
    return [str(x) for x in DEFAULT_DRIVERS]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate prompt bootstrap capability contract (RQ-014).")
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

    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="ignore") if prompt_path.exists() else ""
    required_drivers = _required_drivers(contract)
    configured_validators = [str(x).strip() for x in (task.get("required_validators") or []) if str(x).strip()]

    present: list[str] = []
    missing: list[str] = []
    for driver in required_drivers:
        if driver in configured_validators or Path(driver).name in prompt_text:
            present.append(driver)
        else:
            missing.append(driver)

    total = len(required_drivers)
    passed = len(present)
    coverage = round((passed / total) * 100.0, 2) if total > 0 else 100.0

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "prompt_path": str(prompt_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": prompt_path.exists(),
        "requiredization_current_round_linked": prompt_path.exists(),
        "prompt_bootstrap_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "capability_driver_required_total": total,
        "capability_driver_present_total": passed,
        "capability_driver_coverage_rate": coverage,
        "missing_capability_drivers": missing,
        "required_capability_drivers": required_drivers,
        "evidence_ref": str(prompt_path) if prompt_path.exists() else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not prompt_path.exists():
        payload["prompt_bootstrap_contract_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_PROMPT_MISSING
        payload["stale_reasons"] = ["identity_prompt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if missing:
        payload["prompt_bootstrap_contract_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DRIVER_MISSING
        payload["stale_reasons"] = ["capability_driver_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["prompt_bootstrap_contract_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
