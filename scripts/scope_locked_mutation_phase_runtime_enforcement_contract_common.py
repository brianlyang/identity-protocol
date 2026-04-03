from __future__ import annotations

from pathlib import Path
from typing import Any

PASS_REQUIRED = "PASS_REQUIRED"
FAIL_REQUIRED = "FAIL_REQUIRED"

ISSUE_ID = "ISSUE-046-candidate"
LANE_ID = "scope_locked_mutation_phase_runtime_enforcement_contract_v1"
GOVERNING_LAW = (
    "once scope_lock_status=LOCKED and fixed_write_set_lock_status=LOCKED, "
    "allowed_next_actions collapse exactly to {mutate_fixed_write_set, run_validator, run_probe, "
    "stage_and_commit, emit_blocker_receipt, emit_fail_close_token}; all other actions are not admitted, "
    "including non-compliant reply-envelope output."
)
UNIQUE_DELTA_VS_ISSUE_045 = (
    "ISSUE-045 forbids repeated pre-mutation planning/reanchor/compaction loops; ISSUE-046 additionally "
    "enforces post-lock live runtime actuator control and reply-envelope gating after scope/write-set lock."
)
FAIL_CLOSE_REASON = "execution_loop_not_entering_mutation_phase"
FAIL_CLOSE_REASON_FAMILY = (
    "execution_loop_not_entering_mutation_phase",
    "scope_locked_reread_not_admitted",
    "scope_locked_reanchor_not_admitted",
    "scope_locked_plan_restatement_not_admitted",
    "reply_envelope_not_admitted",
    "tool_use_outside_fixed_write_set_after_lock",
    "pre_mutation_budget_exhausted",
    "mutation_required_but_not_entered",
)
ALLOWED_NEXT_ACTIONS = (
    "mutate_fixed_write_set",
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token",
)
REQUIRED_MACHINE_FIELDS = (
    "current_execution_phase",
    "scope_lock_status",
    "fixed_write_set_lock_status",
    "pre_mutation_turn_count",
    "pre_mutation_tool_count",
    "mutation_phase_entry_status",
    "last_mutation_receipt_turn",
    "allowed_next_actions",
    "reply_envelope_status",
    "runtime_guard_status",
    "forced_fail_close_reason",
    "stale_reasons",
)
BRIDGED_GUARD_FIELDS = (
    "planning_budget_status",
    "repeated_plan_restatement_status",
    "repeated_reanchor_status",
    "repeated_compaction_without_progress_status",
    "execution_loop_status",
)
FIXED_WRITE_SET = (
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md",
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py",
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py",
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh",
)
VALIDATOR_COMMAND = "TMPDIR=$PWD/.tmp python3 scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py --json-only"
PROBE_COMMAND = "TMPDIR=$PWD/.tmp bash scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh"
REOPEN_TRIGGERS = (
    "validator/probe drift on locked allowed_next_actions",
    "required machine fields/guard fields missing",
    "reply-envelope gate not enforced",
    "fixed_write_set changes",
    "candidate id collision with an already-admitted lane",
)
COMMIT_GATE = (
    "single-lane single commit only if validator=PASS_REQUIRED, probe=PASS, and staged paths equal the 5-path fixed_write_set exactly"
)

DOC_EXPECTATIONS = {
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md": (
        "scope_locked_mutation_phase_runtime_enforcement_contract_v1",
        "allowed_next_actions",
        "emit_fail_close_token",
        "reply-envelope output",
        "execution_loop_not_entering_mutation_phase",
        "scope_locked_reread_not_admitted",
        "scope_locked_reanchor_not_admitted",
        "scope_locked_plan_restatement_not_admitted",
        "reply_envelope_not_admitted",
        "tool_use_outside_fixed_write_set_after_lock",
        "pre_mutation_budget_exhausted",
        "mutation_required_but_not_entered",
    ),
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md": (
        "ISSUE-046-candidate",
        "ISSUE-045",
        "reply-envelope gate",
        "mutation receipt",
        "validation receipt",
        "probe receipt",
        "blocker receipt",
        "single-token fail-close",
    ),
}
SCRIPT_EXPECTATIONS = {
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py": (
        "ALLOWED_NEXT_ACTIONS",
        "REQUIRED_MACHINE_FIELDS",
        "BRIDGED_GUARD_FIELDS",
        "FAIL_CLOSE_REASON_FAMILY",
        "reply_envelope_status",
        "runtime_guard_status",
    ),
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py": (
        "FAIL_REQUIRED",
        "PASS_REQUIRED",
        "canonical_payload",
        "default_machine_state",
        "allowed_next_actions",
        "reply_envelope_not_admitted",
    ),
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh": (
        "execution_loop_not_entering_mutation_phase",
        "emit_fail_close_token",
        "PASS",
        "FAIL_REQUIRED",
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def canonical_payload() -> dict[str, Any]:
    return {
        "issue_id_or_candidate_id": ISSUE_ID,
        "lane_id": LANE_ID,
        "governing_law": GOVERNING_LAW,
        "unique_delta_vs_issue_045": UNIQUE_DELTA_VS_ISSUE_045,
        "fixed_write_set": list(FIXED_WRITE_SET),
        "validator_command": VALIDATOR_COMMAND,
        "probe_command": PROBE_COMMAND,
        "allowed_next_actions": list(ALLOWED_NEXT_ACTIONS),
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "bridged_guard_fields": list(BRIDGED_GUARD_FIELDS),
        "fail_close_reason_family": list(FAIL_CLOSE_REASON_FAMILY),
        "reopen_triggers": list(REOPEN_TRIGGERS),
        "commit_gate": COMMIT_GATE,
    }


def default_machine_state() -> dict[str, Any]:
    return {
        "current_execution_phase": "scope_locked_mutation_phase_runtime_enforcement",
        "scope_lock_status": "LOCKED",
        "fixed_write_set_lock_status": "LOCKED",
        "pre_mutation_turn_count": "BOUNDED",
        "pre_mutation_tool_count": "BOUNDED",
        "mutation_phase_entry_status": "REQUIRED_IMMEDIATELY_AFTER_LOCK",
        "last_mutation_receipt_turn": "REQUIRED_ON_PROGRESS",
        "allowed_next_actions": list(ALLOWED_NEXT_ACTIONS),
        "reply_envelope_status": "LOCKED_TO_RUNTIME_RECEIPTS",
        "runtime_guard_status": "ENFORCED",
        "forced_fail_close_reason": FAIL_CLOSE_REASON,
        "planning_budget_status": "BOUNDED_PLANNING_ADMITTED_AT_MOST_ONCE",
        "repeated_plan_restatement_status": "NOT_ADMITTED_AFTER_LOCK",
        "repeated_reanchor_status": "NOT_ADMITTED_AFTER_LOCK",
        "repeated_compaction_without_progress_status": "NOT_ADMITTED_AFTER_LOCK",
        "execution_loop_status": "FAIL_CLOSE_IF_PRE_MUTATION_REPEATS_AFTER_LOCK",
        "stale_reasons": [],
    }
