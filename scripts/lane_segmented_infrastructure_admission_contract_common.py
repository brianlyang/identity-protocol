from __future__ import annotations

from pathlib import Path

PASS_REQUIRED = "PASS_REQUIRED"
FAIL_REQUIRED = "FAIL_REQUIRED"

ISSUE_ID = "ISSUE-045"
LANE_ID = "issue_045_lane_segmented_infrastructure_admission_contract_v1"
GOVERNING_LAW = "segmented_lane_entry_and_closure_must_be_repo_visible_and_non_reinterpretive"
FAIL_CLOSE_REASON = "execution_loop_not_entering_mutation_phase"

EXPECTED_SEGMENTS = ("root", "middle", "tail")
EXPECTED_BATON_FIELDS = (
    "lane_id",
    "governing_law",
    "fixed_write_set",
    "layer_state",
    "next_exact_action",
    "validation_bundle",
    "reopen_triggers",
    "commit_gate",
)
EXECUTION_LOOP_STATE_FIELDS = (
    "planning_budget_status",
    "scope_lock_status",
    "mutation_phase_entry_status",
    "repeated_plan_restatement_status",
    "repeated_reanchor_status",
    "repeated_compaction_without_progress_status",
    "execution_loop_status",
    "stale_reasons",
)
ORDERED_EXECUTION_SEQUENCE = (
    "common",
    "governance/review",
    "validator",
    "probe",
    "workbook/register",
)

FIXED_WRITE_SET = (
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-segmented-infrastructure-admission.md",
    "scripts/lane_segmented_infrastructure_admission_contract_common.py",
    "scripts/validate_lane_segmented_infrastructure_admission.py",
    "scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
)

BOUNDED_PLANNING_RULE = (
    "bounded planning is admitted, but repeated pre-mutation planning / re-anchoring / "
    "compaction without mutation progress is not admitted"
)

DOC_EXPECTATIONS = {
    FIXED_WRITE_SET[0]: (
        "Lane segmented infrastructure admission must be machine-visible, bounded, and repo-consumable.",
        "Continuation and takeover must consume repo-visible baton surfaces, not chat reconstruction.",
        "Tail truth-sync must not become a source of root law.",
        BOUNDED_PLANNING_RULE,
        *EXECUTION_LOOP_STATE_FIELDS,
        *ORDERED_EXECUTION_SEQUENCE,
        FAIL_CLOSE_REASON,
    ),
    FIXED_WRITE_SET[1]: (
        "Lane segmented infrastructure admission must be machine-visible, bounded, and repo-consumable.",
        "Tail truth-sync must not become a source of root law.",
        BOUNDED_PLANNING_RULE,
        *EXECUTION_LOOP_STATE_FIELDS,
        FAIL_CLOSE_REASON,
    ),
    FIXED_WRITE_SET[5]: (
        "`status`: CLOSED",
        "execution_loop_not_entering_mutation_phase",
        "planning_budget_status",
        "repeated_compaction_without_progress_status",
    ),
    FIXED_WRITE_SET[6]: (
        "| ISSUE-045 Lane segmented infrastructure admission is not frozen and handoff still depends on chat reconstruction | CLOSED |",
        "execution_loop_not_entering_mutation_phase",
        "planning_budget_status",
        "repeated_compaction_without_progress_status",
    ),
}


def repo_root(start: Path | None = None) -> Path:
    if start is not None:
        return start.resolve()
    return Path(__file__).resolve().parents[1]


def canonical_payload() -> dict[str, object]:
    return {
        "lane_id": LANE_ID,
        "governing_law": GOVERNING_LAW,
        "fixed_write_set": list(FIXED_WRITE_SET),
        "layer_state": "protocol-lane-infrastructure",
        "next_exact_action": [
            "formalize lane segmented infrastructure admission only",
            "freeze admissible entry rules for root, middle, and tail lane segments",
            "freeze required baton fields: lane_id, governing_law, fixed_write_set, layer_state, next_exact_action, validation_bundle, reopen_triggers, commit_gate",
            "fail-close tail truth-sync when it reinterprets or rewrites accepted root law",
        ],
        "validation_bundle": [
            "TMPDIR=$PWD/.tmp python3 scripts/validate_lane_segmented_infrastructure_admission.py --json-only",
            "TMPDIR=$PWD/.tmp bash scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh",
        ],
        "execution_loop_state_fields": list(EXECUTION_LOOP_STATE_FIELDS),
        "ordered_execution_sequence": list(ORDERED_EXECUTION_SEQUENCE),
        "bounded_planning_rule": BOUNDED_PLANNING_RULE,
        "fail_close_reason": FAIL_CLOSE_REASON,
        "reopen_triggers": [
            "validator/probe fail",
            "same-file same-line conflict",
            "fixed_write_set insufficiency only",
        ],
        "commit_gate": "one isolated commit for ISSUE-045 only",
    }


def default_machine_state() -> dict[str, object]:
    return {
        "planning_budget_status": "bounded_planning_admitted",
        "scope_lock_status": "fixed_write_set_locked",
        "mutation_phase_entry_status": "required_before_repetition",
        "repeated_plan_restatement_status": FAIL_REQUIRED,
        "repeated_reanchor_status": FAIL_REQUIRED,
        "repeated_compaction_without_progress_status": FAIL_REQUIRED,
        "execution_loop_status": PASS_REQUIRED,
        "stale_reasons": [],
    }
