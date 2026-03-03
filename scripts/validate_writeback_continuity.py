#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import (
    contract_required,
    latest_identity_upgrade_report,
    load_json,
    resolve_pack_and_task,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MISSING_WRITEBACK = "IP-WRB-001"
ERR_DEGRADED_FIELDS = "IP-WRB-002"
ERR_PATH_MISMATCH = "IP-WRB-004"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}
ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _resolve_report(identity_id: str, pack_path: Path, explicit: str) -> Path | None:
    if explicit.strip():
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() else None
    return latest_identity_upgrade_report(identity_id, pack_path)


def _required_contract(task: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    contract: dict[str, Any] = {}
    raw = task.get("writeback_continuity_contract_v1")
    if isinstance(raw, dict):
        contract = raw
    elif isinstance(task.get("writeback_continuity_contract"), dict):
        contract = task.get("writeback_continuity_contract")  # type: ignore[assignment]

    if contract:
        return contract_required(contract), contract

    gates = task.get("gates") or {}
    gate_required = str((gates or {}).get("identity_update_gate", "")).strip().lower() == "required"
    return gate_required, contract


def _path_contract_ok(identity_id: str, catalog_path: Path, repo_catalog_path: Path, report_path: Path) -> tuple[bool, str]:
    cmd = [
        "python3",
        "scripts/validate_identity_execution_report_path_contract.py",
        "--identity-id",
        identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--report",
        str(report_path),
        "--json-only",
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    payload = _parse_json_payload((p.stdout or "").strip()) or {}
    status = str(payload.get("path_governance_status", "")).strip().upper()
    if p.returncode != 0 or status == "FAIL_REQUIRED":
        return False, ERR_PATH_MISMATCH
    return True, ""


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate writeback continuity contract for identity upgrade execution.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--report", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = Path(args.repo_catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2
    if not repo_catalog_path.exists():
        print(f"[FAIL] repo catalog not found: {repo_catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    required_contract, contract_doc = _required_contract(task)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "contract_ref": "writeback_continuity_contract_v1" if contract_doc else "",
        "report_selected_path": "",
        "writeback_continuity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "writeback_mode": "",
        "writeback_status": "",
        "upgrade_required": False,
        "all_ok": False,
        "degrade_reason": "",
        "risk_level": "",
        "next_recovery_action": "",
        "stale_reasons": [],
    }

    if not required_contract:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    report_path = _resolve_report(args.identity_id, pack_path, args.report)
    if report_path is None:
        payload["error_code"] = ERR_MISSING_WRITEBACK
        payload["stale_reasons"] = ["execution_report_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["writeback_continuity_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["writeback_continuity_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["report_selected_path"] = str(report_path)

    ok_path, path_error = _path_contract_ok(args.identity_id, catalog_path, repo_catalog_path, report_path)
    if not ok_path:
        payload["writeback_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = path_error
        payload["stale_reasons"] = ["execution_report_path_contract_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        report = load_json(report_path)
    except Exception as exc:
        payload["writeback_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MISSING_WRITEBACK
        payload["stale_reasons"] = [f"execution_report_invalid_json:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    upgrade_required = _bool(report.get("upgrade_required"))
    all_ok = _bool(report.get("all_ok"))
    writeback_status = str(report.get("writeback_status", "")).strip().upper()
    writeback_mode = str(report.get("writeback_mode", "")).strip().upper()
    degrade_reason = str(report.get("degrade_reason", "")).strip()
    risk_level = str(report.get("risk_level", "")).strip().lower()
    next_recovery_action = str(report.get("next_recovery_action", "")).strip()

    payload.update(
        {
            "upgrade_required": upgrade_required,
            "all_ok": all_ok,
            "writeback_status": writeback_status,
            "writeback_mode": writeback_mode,
            "degrade_reason": degrade_reason,
            "risk_level": risk_level,
            "next_recovery_action": next_recovery_action,
        }
    )

    stale_reasons: list[str] = []
    error_code = ""

    if writeback_mode not in {"STRICT_WRITEBACK", "DEGRADED_WRITEBACK"}:
        stale_reasons.append("writeback_mode_missing_or_invalid")
        error_code = ERR_MISSING_WRITEBACK

    if writeback_mode == "DEGRADED_WRITEBACK":
        missing = []
        if not degrade_reason:
            missing.append("degrade_reason")
        if not risk_level:
            missing.append("risk_level")
        if not next_recovery_action:
            missing.append("next_recovery_action")
        if missing:
            stale_reasons.append(f"degraded_writeback_missing_fields:{','.join(missing)}")
            error_code = ERR_DEGRADED_FIELDS
        elif risk_level not in ALLOWED_RISK_LEVELS:
            stale_reasons.append("risk_level_invalid")
            error_code = ERR_DEGRADED_FIELDS

    if upgrade_required:
        if writeback_mode == "STRICT_WRITEBACK":
            if writeback_status != "WRITTEN":
                stale_reasons.append("strict_writeback_requires_written_status")
                error_code = ERR_MISSING_WRITEBACK
            if not all_ok:
                stale_reasons.append("strict_writeback_requires_all_ok")
                error_code = ERR_MISSING_WRITEBACK
        elif writeback_mode == "DEGRADED_WRITEBACK":
            if writeback_status in {"", "MISSING", "NOT_EXECUTED", "NOT_REQUIRED"}:
                stale_reasons.append("degraded_writeback_requires_non_missing_status")
                error_code = ERR_MISSING_WRITEBACK

    if stale_reasons:
        payload["writeback_continuity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_MISSING_WRITEBACK
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["writeback_continuity_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
