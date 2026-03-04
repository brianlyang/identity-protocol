#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STRICT_OPS = {"update", "readiness", "e2e", "ci", "validate", "activate"}
ERR_MISSING_FIELDS = "IP-HLT-001"
ERR_REPORT_BINDING = "IP-HLT-002"
ERR_COVERAGE_MISMATCH = "IP-HLT-003"
ERR_NON_PASS_DETAILS = "IP-HLT-004"


def _latest_for_identity(report_dir: Path, identity_id: str) -> Path | None:
    rows = sorted(report_dir.glob(f"identity-health-{identity_id}-*.json"), key=lambda p: p.stat().st_mtime)
    return rows[-1] if rows else None


def _status_name(ok: bool) -> str:
    return "PASS_REQUIRED" if ok else "FAIL_REQUIRED"


def _emit(payload: dict[str, Any], json_only: bool) -> int:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        status = payload.get("actor_health_profile_status")
        code = payload.get("error_code", "")
        if status == "PASS_REQUIRED":
            print("[OK] actor health profile contract validated")
        else:
            print(f"[FAIL] actor health profile contract invalid (error_code={code})")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("actor_health_profile_status") == "PASS_REQUIRED" else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate actor-risk health profile coverage contract.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--report-dir", default="/tmp/identity-health-reports")
    ap.add_argument("--execution-report", default="")
    ap.add_argument(
        "--operation",
        default="validate",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
    )
    ap.add_argument("--enforce-bound-report", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    stale_reasons: list[str] = []
    error_code = ""

    if args.report.strip():
        report_path = Path(args.report).expanduser().resolve()
    else:
        latest = _latest_for_identity(Path(args.report_dir).expanduser().resolve(), args.identity_id)
        if latest is None:
            payload = {
                "identity_id": args.identity_id,
                "report_path": "",
                "operation": args.operation,
                "actor_health_profile_status": _status_name(False),
                "error_code": ERR_MISSING_FIELDS,
                "stale_reasons": ["health_report_not_found"],
            }
            return _emit(payload, args.json_only)
        report_path = latest

    if not report_path.exists():
        payload = {
            "identity_id": args.identity_id,
            "report_path": str(report_path),
            "operation": args.operation,
            "actor_health_profile_status": _status_name(False),
            "error_code": ERR_MISSING_FIELDS,
            "stale_reasons": ["health_report_path_missing"],
        }
        return _emit(payload, args.json_only)

    try:
        doc = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        payload = {
            "identity_id": args.identity_id,
            "report_path": str(report_path),
            "operation": args.operation,
            "actor_health_profile_status": _status_name(False),
            "error_code": ERR_MISSING_FIELDS,
            "stale_reasons": ["health_report_json_invalid"],
        }
        return _emit(payload, args.json_only)

    if str(doc.get("identity_id", "")).strip() != args.identity_id:
        stale_reasons.append("health_report_identity_mismatch")
        error_code = ERR_MISSING_FIELDS

    required_fields = [
        "actor_binding_integrity",
        "actor_lease_freshness",
        "implicit_switch_guard",
        "pointer_drift_guard",
        "actor_risk_required_count",
        "actor_risk_present_count",
        "actor_risk_coverage_rate",
    ]
    missing = [k for k in required_fields if k not in doc]
    if missing:
        stale_reasons.append("actor_risk_fields_missing")
        error_code = error_code or ERR_MISSING_FIELDS

    actor_rows = [
        doc.get("actor_binding_integrity"),
        doc.get("actor_lease_freshness"),
        doc.get("implicit_switch_guard"),
        doc.get("pointer_drift_guard"),
    ]
    present_count = 0
    non_pass_missing_detail = False
    for row in actor_rows:
        if not isinstance(row, dict):
            continue
        status = str(row.get("status", "")).strip().upper()
        if status in {"PASS", "WARN", "FAIL"}:
            present_count += 1
        if status in {"WARN", "FAIL"}:
            if not str(row.get("error_code", "")).strip() or not str(row.get("suggestion", "")).strip():
                non_pass_missing_detail = True
    required_count = int(doc.get("actor_risk_required_count", 0) or 0)
    report_present = int(doc.get("actor_risk_present_count", 0) or 0)
    computed_rate = round((present_count / required_count) * 100.0, 2) if required_count > 0 else 0.0
    report_rate = float(doc.get("actor_risk_coverage_rate", 0.0) or 0.0)
    if required_count <= 0 or report_present != present_count or abs(report_rate - computed_rate) > 0.01 or computed_rate < 100.0:
        stale_reasons.append("actor_risk_coverage_mismatch")
        error_code = error_code or ERR_COVERAGE_MISMATCH
    if non_pass_missing_detail:
        stale_reasons.append("non_pass_actor_risk_missing_detail")
        error_code = error_code or ERR_NON_PASS_DETAILS

    execution_report = str(args.execution_report or "").strip()
    report_exec_ref = str(doc.get("execution_report_ref", "")).strip()
    report_binding_mode = str(doc.get("report_binding_mode", "")).strip()
    enforce_bound_report = bool(args.enforce_bound_report or (args.operation in STRICT_OPS and execution_report))
    if enforce_bound_report:
        if not execution_report:
            stale_reasons.append("execution_report_ref_missing_for_strict_operation")
            error_code = error_code or ERR_REPORT_BINDING
        else:
            expected_report = str(Path(execution_report).expanduser().resolve())
            if report_exec_ref != expected_report:
                stale_reasons.append("health_report_execution_ref_mismatch")
                error_code = error_code or ERR_REPORT_BINDING
            if report_binding_mode != "explicit_report":
                stale_reasons.append("health_report_binding_mode_not_explicit")
                error_code = error_code or ERR_REPORT_BINDING

    ok = not stale_reasons
    payload = {
        "identity_id": args.identity_id,
        "report_path": str(report_path),
        "operation": args.operation,
        "actor_health_profile_status": _status_name(ok),
        "error_code": "" if ok else error_code,
        "actor_risk_required_count": required_count,
        "actor_risk_present_count": report_present,
        "actor_risk_coverage_rate": report_rate,
        "execution_report_ref": report_exec_ref,
        "report_binding_mode": report_binding_mode,
        "stale_reasons": stale_reasons,
    }
    return _emit(payload, args.json_only)


if __name__ == "__main__":
    raise SystemExit(main())

