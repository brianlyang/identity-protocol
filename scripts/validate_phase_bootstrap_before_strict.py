#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, latest_identity_upgrade_report, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REPORT_MISSING = "IP-PHASE-001"
ERR_PHASE_B_MISSING = "IP-PHASE-002"
ERR_PHASE_B_FAILED = "IP-PHASE-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "phase_bootstrap_before_strict_contract_v1",
        "phase_bootstrap_before_strict_contract",
        "rq_010_phase_a_bootstrap_before_strict_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _load_report(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate phase-A bootstrap before strict contract (RQ-010).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
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

    report_path: Path | None = None
    if args.report.strip():
        candidate = Path(args.report).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            report_path = candidate
    else:
        latest = latest_identity_upgrade_report(args.identity_id, pack_path)
        if latest and latest.exists():
            report_path = latest.resolve()

    report_doc = _load_report(report_path) if report_path else None
    phase_a_applied = bool((report_doc or {}).get("phase_a_refresh_applied", False))
    phase_b_status = str((report_doc or {}).get("phase_b_strict_revalidate_status", "")).strip().upper()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": report_doc is not None,
        "requiredization_current_round_linked": bool(report_doc),
        "phase_bootstrap_before_strict_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "report_path": str(report_path) if report_path else "",
        "phase_a_refresh_applied": phase_a_applied,
        "phase_b_strict_revalidate_status": phase_b_status,
        "phase_trace_status": "",
        "evidence_ref": str(report_path) if report_path else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if report_doc is None:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_execution_report"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["phase_bootstrap_before_strict_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPORT_MISSING
        payload["stale_reasons"] = ["execution_report_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if phase_a_applied:
        if not phase_b_status:
            payload["phase_bootstrap_before_strict_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_PHASE_B_MISSING
            payload["phase_trace_status"] = "phase_a_without_phase_b"
            payload["stale_reasons"] = ["phase_b_status_missing_after_phase_a"]
            _emit(payload, json_only=args.json_only)
            return 1
        if phase_b_status != STATUS_PASS_REQUIRED:
            payload["phase_bootstrap_before_strict_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_PHASE_B_FAILED
            payload["phase_trace_status"] = "phase_a_with_phase_b_not_pass"
            payload["stale_reasons"] = ["phase_b_strict_revalidate_not_pass_required"]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["phase_trace_status"] = "phase_a_then_phase_b_pass"
    else:
        payload["phase_trace_status"] = "phase_a_not_required_or_not_applied"

    payload["phase_bootstrap_before_strict_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
