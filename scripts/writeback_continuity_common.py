#!/usr/bin/env python3
from __future__ import annotations


def derive_writeback_continuity_fields(
    *,
    upgrade_required: bool,
    all_ok: bool,
    writeback_status: str,
    writeback_error_code: str,
    permission_error_code: str,
    next_action: str,
) -> dict[str, str]:
    ws = str(writeback_status or "").strip().upper()
    wb_err = str(writeback_error_code or "").strip().upper()
    perm_err = str(permission_error_code or "").strip().upper()
    na = str(next_action or "").strip()

    if all_ok and (not upgrade_required or ws == "WRITTEN"):
        return {
            "writeback_mode": "STRICT_WRITEBACK",
            "degrade_reason": "",
            "risk_level": "",
            "next_recovery_action": "",
        }

    degrade_reason = "validator_failure_before_writeback"
    risk_level = "medium"
    recovery = na or "fix_failing_validators_and_rerun_update"

    if ws == "DEFERRED_PERMISSION_BLOCKED" or wb_err.startswith("IP-PERM-") or perm_err.startswith("IP-PERM-"):
        degrade_reason = "permission_blocked_writeback"
        risk_level = "high"
        recovery = na or "restore_write_permission_or_escalate_then_rerun_update"
    elif ws == "DEFERRED_POLICY_BLOCKED" or wb_err.startswith("IP-SAFEAUTO-") or perm_err.startswith("IP-UPG-001"):
        degrade_reason = "policy_blocked_writeback"
        risk_level = "high"
        recovery = na or "adjust_safe_auto_policy_or_switch_mode_then_rerun_update"
    elif ws == "DEFERRED_VALIDATION_FAILED" or wb_err.startswith("IP-UPG-"):
        degrade_reason = "validator_failure_before_writeback"
        risk_level = "medium"
        recovery = na or "resolve_validation_failures_then_rerun_update"
    elif ws in {"MISSING", "NOT_EXECUTED"}:
        degrade_reason = "writeback_not_executed"
        risk_level = "high"
        recovery = na or "produce_valid_execution_report_with_degraded_or_strict_writeback"

    return {
        "writeback_mode": "DEGRADED_WRITEBACK",
        "degrade_reason": degrade_reason,
        "risk_level": risk_level,
        "next_recovery_action": recovery,
    }
