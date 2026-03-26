#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from execution_report_selection_common import collect_reports, select_report
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_NOT_FOUND = "IP-RSEL-001"
ERR_RUN_ID_NO_MATCH = "IP-RSEL-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "run_id_report_selection_contract_v1",
        "run_id_report_selection_contract",
        "rq_009_run_id_anchored_report_selection_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate run-id anchored report selection contract (RQ-009).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report", default="")
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

    run_id = str(args.run_id or contract.get("run_id", "")).strip()
    explicit_report = str(args.report or "").strip()
    reports = collect_reports(pack_path, args.identity_id)
    selected_report, selection_strategy = select_report(explicit_report=explicit_report, run_id=run_id, reports=reports)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": bool(reports),
        "requiredization_current_round_linked": False,
        "run_id_report_selection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "run_id": run_id,
        "selection_strategy": selection_strategy,
        "report_selected_path": str(selected_report) if selected_report else "",
        "candidate_count": len(reports),
        "candidate_paths": [str(p) for p in reports[-10:]],
        "evidence_ref": str(selected_report) if selected_report else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if selected_report is None:
        if args.operation in INSPECTION_OPERATIONS:
            if selection_strategy == "run_id_not_found":
                payload["stale_reasons"] = ["required_contract_not_applicable_current_round_unlinked"]
                _emit(payload, json_only=args.json_only)
                return 0
            if selection_strategy in {"no_reports"}:
                payload["stale_reasons"] = ["required_contract_not_applicable_no_reports"]
                _emit(payload, json_only=args.json_only)
                return 0
            if not run_id and not explicit_report:
                payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
                _emit(payload, json_only=args.json_only)
                return 0
        if (
            args.operation in {"update", "validate"}
            and selection_strategy == "run_id_not_found"
            and run_id
            and not explicit_report
        ):
            payload["stale_reasons"] = ["required_contract_not_applicable_current_round_unmaterialized"]
            _emit(payload, json_only=args.json_only)
            return 0
        if selection_strategy in {"no_reports"} and args.operation in INSPECTION_OPERATIONS:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_reports"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["run_id_report_selection_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RUN_ID_NO_MATCH if selection_strategy == "run_id_not_found" else ERR_REPORT_NOT_FOUND
        payload["stale_reasons"] = [selection_strategy]
        _emit(payload, json_only=args.json_only)
        return 1

    if explicit_report:
        payload["requiredization_current_round_linked"] = True
    elif run_id and selection_strategy == "run_id_bound":
        payload["requiredization_current_round_linked"] = True
    elif args.operation in INSPECTION_OPERATIONS:
        payload["stale_reasons"] = ["required_contract_not_applicable_no_current_round_evidence_source"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["run_id_report_selection_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
