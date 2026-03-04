#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import (
    contract_required,
    load_json,
    nonempty,
    resolve_pack_and_task,
    resolve_report_path,
)


REQ_CONTRACT_KEYS = (
    "required",
    "report_path_pattern",
    "required_report_fields",
    "enforcement_validator",
)

DEFAULT_REQUIRED_REPORT_FIELDS = (
    "tool_gap_detected",
    "tool_gap_summary_ref",
    "install_plan_ref",
    "approval_receipt_ref",
    "execution_log_ref",
    "installed_artifact_ref",
    "installed_version",
    "post_install_healthcheck_ref",
    "task_smoke_result_ref",
    "route_binding_update_ref",
    "fallback_route_if_install_fails",
    "rollback_ref",
)


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    # Keep backward compatibility with older naming candidates.
    for key in ("tool_installation_contract", "tool_discovery_installation_contract"):
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate tool discovery/installation closure contract.")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    args = ap.parse_args()

    try:
        pack_path, task_path = resolve_pack_and_task(Path(args.catalog).expanduser().resolve(), args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    if not contract_required(contract):
        print(f"[OK] tool installation contract not required for identity={args.identity_id}; skipped")
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if missing_contract:
        print(f"[FAIL] IP-TIN-001 tool installation contract missing fields: {missing_contract}")
        return 1

    report_path = resolve_report_path(
        report=args.report,
        pattern=str(contract.get("report_path_pattern", "")),
        pack_root=pack_path,
    )
    if report_path is None:
        print("[FAIL] IP-TIN-002 tool installation report not found")
        return 1

    try:
        report = load_json(report_path)
    except Exception as exc:
        print(f"[FAIL] IP-TIN-002 invalid report json: {report_path} ({exc})")
        return 1

    required_fields = contract.get("required_report_fields")
    if not isinstance(required_fields, list) or not required_fields:
        required_fields = list(DEFAULT_REQUIRED_REPORT_FIELDS)

    missing_report_fields = [k for k in required_fields if k not in report]
    if missing_report_fields:
        print(f"[FAIL] IP-TIN-003 report missing required fields: {missing_report_fields}")
        return 1

    gap_detected = str(report.get("tool_gap_detected", "")).strip().lower() in {"yes", "true", "1"}
    if gap_detected:
        chain_missing = [
            key
            for key in (
                "install_plan_ref",
                "approval_receipt_ref",
                "execution_log_ref",
                "post_install_healthcheck_ref",
                "task_smoke_result_ref",
                "route_binding_update_ref",
                "fallback_route_if_install_fails",
                "rollback_ref",
            )
            if not nonempty(report.get(key))
        ]
        if chain_missing:
            print(f"[FAIL] IP-TIN-004 tool gap chain incomplete: missing={chain_missing}")
            return 1

    print(f"[OK] tool installation closure validated: {report_path}")
    print("validate_identity_tool_installation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

