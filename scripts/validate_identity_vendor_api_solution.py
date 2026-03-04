#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, nonempty, resolve_pack_and_task, resolve_report_path


REQ_CONTRACT_KEYS = (
    "required",
    "report_path_pattern",
    "required_report_fields",
    "enforcement_validator",
)

DEFAULT_REQUIRED_FIELDS = (
    "problem_statement_ref",
    "selected_vendor_api_ref",
    "solution_pattern",
    "decision_rationale_ref",
    "option_comparison_ref",
    "security_boundary_ref",
    "auth_scope_strategy_ref",
    "rate_limit_strategy_ref",
    "fallback_solution_ref",
    "rollback_solution_ref",
    "owner_layer_declaration_ref",
)


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    c = task.get("vendor_api_solution_contract")
    return c if isinstance(c, dict) else {}


def _extract_option_matrix(report: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("solution_option_matrix", "options", "option_matrix"):
        rows = report.get(key)
        if isinstance(rows, list):
            return [x for x in rows if isinstance(x, dict)]
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate vendor/API solution closure contract.")
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
        print(f"[OK] vendor/api solution contract not required for identity={args.identity_id}; skipped")
        return 0

    missing_contract = [k for k in REQ_CONTRACT_KEYS if k not in contract]
    if missing_contract:
        print(f"[FAIL] IP-VAP-101 vendor/api solution contract missing fields: {missing_contract}")
        return 1

    report_path = resolve_report_path(
        report=args.report,
        pattern=str(contract.get("report_path_pattern", "")),
        pack_root=pack_path,
    )
    if report_path is None:
        print("[FAIL] IP-VAP-102 vendor/api solution report not found")
        return 1

    try:
        report = load_json(report_path)
    except Exception as exc:
        print(f"[FAIL] IP-VAP-102 invalid report json: {report_path} ({exc})")
        return 1

    required_fields = contract.get("required_report_fields")
    if not isinstance(required_fields, list) or not required_fields:
        required_fields = list(DEFAULT_REQUIRED_FIELDS)
    missing_report = [k for k in required_fields if k not in report]
    if missing_report:
        print(f"[FAIL] IP-VAP-103 solution report missing required fields: {missing_report}")
        return 1

    option_rows = _extract_option_matrix(report)
    if not option_rows:
        print("[FAIL] IP-VAP-104 solution option matrix missing")
        return 1

    selected_rows = [x for x in option_rows if str(x.get("selected", "")).strip().lower() == "yes"]
    selected_count = len(selected_rows)
    run_state = str(report.get("run_state", report.get("status", ""))).strip().lower()
    if selected_count != 1:
        if selected_count == 0 and run_state in {"defer", "blocked"}:
            print(f"[OK] no selected option and run_state={run_state}; expected defer/blocked path")
            print(f"[OK] vendor/api solution closure validated (deferred): {report_path}")
            return 0
        print(f"[FAIL] IP-VAP-105 exactly one option must be selected=yes, got={selected_count}")
        return 1

    selected = selected_rows[0]
    selected_missing = [
        key
        for key in (
            "solution_pattern",
            "expected_capability_gain",
        )
        if not nonempty(selected.get(key))
    ]
    if selected_missing:
        print(f"[FAIL] IP-VAP-106 selected option missing fields: {selected_missing}")
        return 1

    # Required safety references may live at top-level or selected-option level.
    safety_missing = [
        key
        for key in (
            "security_boundary_ref",
            "auth_scope_strategy_ref",
            "rate_limit_strategy_ref",
            "fallback_solution_ref",
            "rollback_solution_ref",
        )
        if not nonempty(report.get(key)) and not nonempty(selected.get(key))
    ]
    if safety_missing:
        print(f"[FAIL] IP-VAP-107 selected option missing safety/rollback refs: {safety_missing}")
        return 1

    print(f"[OK] vendor/api solution closure validated: {report_path}")
    print("validate_identity_vendor_api_solution PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

