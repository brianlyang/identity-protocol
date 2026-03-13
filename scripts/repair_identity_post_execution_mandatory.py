#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from final_emit_contract_common import FINAL_EMIT_CHANNEL_ID, FINAL_EMIT_POLICY_MODE, FINAL_EMIT_SCHEMA_ID
from tool_vendor_governance_common import boolish, latest_identity_upgrade_report, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, list):
        return len(value) > 0
    if isinstance(value, dict):
        return len(value) > 0
    return True


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _derive_writeback_defaults(report: dict[str, Any]) -> tuple[str, str, str]:
    upgrade_required = boolish(report.get("upgrade_required"))
    all_ok = boolish(report.get("all_ok"))
    writeback_status = str(report.get("writeback_status", "")).strip().upper()
    if all_ok and upgrade_required:
        ws = writeback_status or "WRITTEN"
    elif all_ok and not upgrade_required:
        ws = writeback_status or "NOT_REQUIRED"
    else:
        ws = writeback_status
        if ws in {"", "MISSING", "NOT_EXECUTED"}:
            ws = "DEFERRED_VALIDATION_FAILED"

    if all_ok and ((upgrade_required and ws == "WRITTEN") or ((not upgrade_required) and ws in {"WRITTEN", "NOT_REQUIRED"})):
        mode = "STRICT_WRITEBACK"
        next_recovery = ""
    else:
        mode = "DEGRADED_WRITEBACK"
        next_recovery = str(report.get("next_recovery_action", "")).strip() or str(report.get("next_action", "")).strip()
        if not next_recovery:
            next_recovery = "fix_failing_validators_and_rerun_update"
    return ws, mode, next_recovery


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair post-execution mandatory fields in the latest upgrade report.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 2

    try:
        pack_path, _task_path = resolve_pack_and_task(catalog, args.identity_id)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    explicit_report = str(args.report or "").strip()
    if explicit_report:
        report_path = Path(explicit_report).expanduser().resolve()
        if not report_path.exists():
            print(f"[FAIL] report not found: {report_path}")
            return 1
    else:
        report_candidate = latest_identity_upgrade_report(args.identity_id, pack_path)
        if report_candidate is None:
            payload = {
                "identity_id": args.identity_id,
                "catalog_path": str(catalog),
                "resolved_pack_path": str(pack_path),
                "post_execution_report_repair_status": STATUS_SKIPPED_NOT_REQUIRED,
                "error_code": "",
                "stale_reasons": ["upgrade_report_missing_skip_repair"],
            }
            _emit(payload, json_only=args.json_only)
            return 0
        report_path = report_candidate

    report_before = _load_json_safe(report_path)
    if not report_before:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog),
            "resolved_pack_path": str(pack_path),
            "post_execution_report_repair_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-WRB-REPAIR-001",
            "report_selected_path": str(report_path),
            "stale_reasons": ["report_invalid_json"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_after = dict(report_before)
    run_id = str(report_after.get("run_id", "")).strip() or f"report-repair-{int(datetime.now(timezone.utc).timestamp())}"
    receipt_path = (pack_path / "runtime" / "reports" / "postexec" / f"{run_id}-postexec-receipt.json").resolve()

    writeback_status, writeback_mode, next_recovery_action = _derive_writeback_defaults(report_after)
    next_action = str(report_after.get("next_action", "")).strip() or "satisfy_pre_mutation_gate_and_rerun_update"
    pre_mutation_receipt = str(report_after.get("pre_mutation_gate_receipt", "")).strip()
    outlet_receipt = str(report_after.get("outlet_preflight_receipt", "")).strip() or pre_mutation_receipt or str(receipt_path)

    report_after["permission_state"] = str(report_after.get("permission_state", "")).strip() or "BLOCKED"
    report_after["writeback_status"] = writeback_status
    report_after["writeback_mode"] = writeback_mode
    report_after["next_action"] = next_action
    report_after["next_recovery_action"] = next_recovery_action
    report_after["phase_a_refresh_applied"] = bool(report_after.get("phase_a_refresh_applied", False))
    report_after["phase_b_strict_revalidate_status"] = (
        str(report_after.get("phase_b_strict_revalidate_status", "")).strip() or "NOT_APPLICABLE"
    )
    report_after["phase_transition_reason"] = str(report_after.get("phase_transition_reason", "")).strip()
    report_after["phase_transition_error_code"] = str(report_after.get("phase_transition_error_code", "")).strip()
    report_after["governed_outlet_enforced"] = bool(report_after.get("governed_outlet_enforced", True))
    report_after["outlet_channel_id"] = str(report_after.get("outlet_channel_id", "")).strip() or FINAL_EMIT_CHANNEL_ID
    report_after["outlet_preflight_receipt"] = outlet_receipt
    report_after["outlet_bypass_detected"] = bool(report_after.get("outlet_bypass_detected", False))
    report_after["final_emit_channel_id"] = str(report_after.get("final_emit_channel_id", "")).strip() or FINAL_EMIT_CHANNEL_ID
    report_after["final_emit_policy_mode"] = str(report_after.get("final_emit_policy_mode", "")).strip() or FINAL_EMIT_POLICY_MODE
    report_after["final_emit_schema_id"] = str(report_after.get("final_emit_schema_id", "")).strip() or FINAL_EMIT_SCHEMA_ID
    report_after["final_emit_schema_status"] = (
        str(report_after.get("final_emit_schema_status", "")).strip().upper() or STATUS_PASS_REQUIRED
    )
    report_after["final_emit_contract_status"] = (
        str(report_after.get("final_emit_contract_status", "")).strip().upper() or STATUS_PASS_REQUIRED
    )

    experience_writeback = report_after.get("experience_writeback")
    if not isinstance(experience_writeback, dict):
        experience_writeback = {}
    experience_writeback["required"] = bool(experience_writeback.get("required", False))
    experience_writeback["status"] = str(experience_writeback.get("status", "")).strip() or (
        "WRITTEN" if writeback_status == "WRITTEN" else "NOT_REQUIRED"
    )
    experience_writeback["error_code"] = str(experience_writeback.get("error_code", "")).strip()
    experience_writeback["mode"] = str(experience_writeback.get("mode", "")).strip() or str(report_after.get("mode", "")).strip()
    notes = str(experience_writeback.get("notes", "")).strip()
    if not notes and writeback_mode == "DEGRADED_WRITEBACK":
        notes = "degraded writeback applied by repair_identity_post_execution_mandatory"
    experience_writeback["notes"] = notes
    report_after["experience_writeback"] = experience_writeback

    actions_taken = report_after.get("actions_taken")
    if not isinstance(actions_taken, list):
        actions_taken = []
    marker = f"post_execution_mandatory_repaired:{now}"
    if marker not in actions_taken:
        actions_taken.append(marker)
    report_after["actions_taken"] = actions_taken

    artifacts = report_after.get("artifacts")
    if not isinstance(artifacts, list):
        artifacts = []
    if str(receipt_path) not in artifacts:
        artifacts.append(str(receipt_path))
    report_after["artifacts"] = artifacts

    changed_keys = sorted([k for k in report_after.keys() if report_before.get(k) != report_after.get(k)])
    report_changed = report_after != report_before
    receipt_written = False
    if args.apply and report_changed:
        _write_json(report_path, report_after)
    if args.apply and not pre_mutation_receipt:
        _write_json(
            receipt_path,
            {
                "identity_id": args.identity_id,
                "run_id": run_id,
                "operation": "update",
                "status": "DEGRADED_WRITEBACK",
                "created_at": now,
                "reason": "post_execution_mandatory_repair_missing_outlet_preflight_receipt",
            },
        )
        receipt_written = True

    stale_reasons: list[str] = []
    if report_changed and not args.apply:
        stale_reasons.append("apply_required_for_post_execution_report_repair")

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "resolved_pack_path": str(pack_path),
        "report_selected_path": str(report_path),
        "post_execution_report_repair_status": STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED,
        "error_code": "" if not stale_reasons else "IP-WRB-REPAIR-DRYRUN",
        "report_updated": bool(args.apply and report_changed),
        "receipt_written": bool(receipt_written),
        "changed_key_count": len(changed_keys),
        "changed_keys": changed_keys,
        "writeback_status_after": writeback_status,
        "writeback_mode_after": writeback_mode,
        "outlet_preflight_receipt_after": outlet_receipt,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
