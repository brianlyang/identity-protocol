#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MANDATORY_STATE = "IP-WRB-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

MANDATORY_REPORT_FIELDS = (
    "permission_state",
    "writeback_status",
    "next_action",
    "skills_used",
    "mcp_tools_used",
    "tool_calls_used",
    "capability_activation_status",
    "capability_activation_error_code",
    "writeback_mode",
    "phase_a_refresh_applied",
    "phase_b_strict_revalidate_status",
    "phase_transition_reason",
    "phase_transition_error_code",
)


def _bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


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


def _latest_report(identity_id: str, pack_path: Path) -> Path | None:
    roots = [(pack_path / "runtime" / "reports").resolve(), (pack_path / "runtime").resolve()]
    rows: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        rows.extend(
            p
            for p in root.glob(f"**/identity-upgrade-exec-{identity_id}-*.json")
            if not p.name.endswith("-patch-plan.json")
        )
    if not rows:
        return None
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows[-1]


def _resolve_report(identity_id: str, pack_path: Path, explicit: str) -> Path | None:
    if explicit.strip():
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() else None
    return _latest_report(identity_id, pack_path)


def _run_experience_writeback_validator(
    *,
    identity_id: str,
    catalog_path: Path,
    repo_catalog_path: Path,
    report_path: Path,
) -> tuple[int, str, str]:
    cmd = [
        "python3",
        "scripts/validate_identity_experience_writeback.py",
        "--repo-catalog",
        str(repo_catalog_path),
        "--local-catalog",
        str(catalog_path),
        "--identity-id",
        identity_id,
        "--execution-report",
        str(report_path),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate post-execution mandatory closure contract.")
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

    post_exec = task.get("post_execution_mandatory")
    required_contract = isinstance(post_exec, list) and len(post_exec) > 0
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "post_execution_mandatory_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "report_selected_path": "",
        "missing_fields": [],
        "writeback_mode": "",
        "writeback_status": "",
        "next_action": "",
        "next_recovery_action": "",
        "phase_a_refresh_applied": False,
        "phase_b_strict_revalidate_status": "",
        "phase_transition_reason": "",
        "phase_transition_error_code": "",
        "stale_reasons": [],
    }

    if not required_contract:
        payload["stale_reasons"] = ["post_execution_mandatory_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    report_path = _resolve_report(args.identity_id, pack_path, args.report)
    if report_path is None:
        payload["error_code"] = ERR_MANDATORY_STATE
        payload["stale_reasons"] = ["execution_report_not_found"]
        if args.operation in INSPECTION_OPERATIONS:
            payload["post_execution_mandatory_status"] = STATUS_SKIPPED_NOT_REQUIRED
            _emit(payload, json_only=args.json_only)
            return 0
        payload["post_execution_mandatory_status"] = STATUS_FAIL_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 1

    payload["report_selected_path"] = str(report_path)
    try:
        report = load_json(report_path)
    except Exception as exc:
        payload["post_execution_mandatory_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANDATORY_STATE
        payload["stale_reasons"] = [f"execution_report_invalid_json:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    missing_fields = [k for k in MANDATORY_REPORT_FIELDS if k not in report]
    experience_writeback = report.get("experience_writeback") or {}
    if not isinstance(experience_writeback, dict):
        missing_fields.append("experience_writeback")
    else:
        if "status" not in experience_writeback:
            missing_fields.append("experience_writeback.status")
        if "error_code" not in experience_writeback:
            missing_fields.append("experience_writeback.error_code")

    writeback_mode = str(report.get("writeback_mode", "")).strip().upper()
    writeback_status = str(report.get("writeback_status", "")).strip().upper()
    next_action = str(report.get("next_action", "")).strip()
    next_recovery_action = str(report.get("next_recovery_action", "")).strip()
    upgrade_required = _bool(report.get("upgrade_required"))
    all_ok = _bool(report.get("all_ok"))

    payload.update(
        {
            "missing_fields": missing_fields,
            "writeback_mode": writeback_mode,
            "writeback_status": writeback_status,
            "next_action": next_action,
            "next_recovery_action": next_recovery_action,
            "phase_a_refresh_applied": bool(report.get("phase_a_refresh_applied", False)),
            "phase_b_strict_revalidate_status": str(report.get("phase_b_strict_revalidate_status", "")).strip(),
            "phase_transition_reason": str(report.get("phase_transition_reason", "")).strip(),
            "phase_transition_error_code": str(report.get("phase_transition_error_code", "")).strip(),
        }
    )

    stale_reasons: list[str] = []
    if missing_fields:
        stale_reasons.append("mandatory_report_fields_missing")

    if not next_action:
        stale_reasons.append("next_action_missing")
    elif next_action.strip().lower() in {"pending", "intake"}:
        stale_reasons.append("next_action_not_advanced")

    if payload.get("phase_a_refresh_applied"):
        phase_b = str(payload.get("phase_b_strict_revalidate_status", "")).strip()
        if not phase_b or phase_b in {"NOT_APPLICABLE", "UNKNOWN"}:
            stale_reasons.append("phase_b_strict_revalidate_status_missing_after_phase_a")

    if upgrade_required and all_ok and writeback_status == "WRITTEN":
        rc_ew, out_ew, err_ew = _run_experience_writeback_validator(
            identity_id=args.identity_id,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            report_path=report_path,
        )
        if rc_ew != 0:
            tail = ""
            if out_ew:
                tail = out_ew.splitlines()[-1]
            elif err_ew:
                tail = err_ew.splitlines()[-1]
            stale_reasons.append(f"experience_writeback_linkage_failed:{tail or 'validator_failed'}")
    else:
        if writeback_mode != "DEGRADED_WRITEBACK":
            stale_reasons.append("degraded_mode_required_for_non_closed_execution")
        if writeback_status in {"MISSING", "NOT_EXECUTED", ""}:
            stale_reasons.append("writeback_status_missing_for_post_execution")
        if not next_recovery_action:
            stale_reasons.append("next_recovery_action_missing")

    if stale_reasons:
        payload["post_execution_mandatory_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MANDATORY_STATE
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["post_execution_mandatory_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
