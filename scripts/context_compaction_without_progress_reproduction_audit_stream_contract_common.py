from __future__ import annotations

from pathlib import Path
from typing import Any

PASS_REQUIRED = "PASS_REQUIRED"
FAIL_REQUIRED = "FAIL_REQUIRED"

STREAM_ID = "context_compaction_without_progress_reproduction_audit_stream"
CLASSIFICATION = "read_only_residual_reproduction_audit_stream"
FAIL_CLOSE_REASON = "read_only_residual_reproduction_audit_stream_drift"
TARGET_RESIDUAL_CLASS = (
    "context compact / repeated compaction / repeated pre-mutation summary replacing "
    "real mutation / validator / probe / commit progress"
)
GOVERNING_LAW = (
    "This stream is admitted only as read-only residual audit infrastructure that "
    "machine-visibly checks whether context compact / repeated compaction / repeated "
    "pre-mutation summary is substituting for real mutation / validator / probe / commit "
    "progress, while remaining strictly separate from protocol feedback / instance feedback "
    "rail-switch / emission obligation consumption gap and from canonical hard identity "
    "binding / owner-binding lock-in."
)
CURRENT_COVERAGE_JUDGMENT = (
    "Current known residual coverage is already machine-visible through ISSUE-045 and "
    "ISSUE-046-candidate surfaces; the stream does not reopen ISSUE-040 through ISSUE-048 "
    "and does not create a new issue by default."
)
SEPARATION_BOUNDARIES = (
    "protocol feedback / instance feedback rail-switch / emission obligation consumption gap",
    "canonical hard identity binding / owner-binding lock-in",
)
ALLOWED_AUDIT_OUTCOMES = (
    "no_machine_visible_reproduction_observed",
    "reproduction_observed_but_already_covered_by_issue_045_or_046",
    "uncovered_machine_visible_reproduction_candidate",
)
UNCOVERED_PROMOTION_GATE = (
    "new machine-visible reproduction observed",
    "current ISSUE-040 through ISSUE-048 family cannot classify or fail-close the reproduction",
    "separation from protocol feedback and identity binding streams remains intact",
)
REQUIRED_MACHINE_FIELDS = (
    "stream_mode",
    "residual_target_class",
    "coverage_classification_status",
    "issue_family_reopen_status",
    "new_issue_candidate_status",
    "protocol_feedback_mixing_status",
    "identity_binding_mixing_status",
    "observed_reproduction_status",
    "stale_reasons",
)

FIXED_WRITE_SET = (
    "docs/governance/identity-context-compaction-without-progress-reproduction-audit-stream-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-context-compaction-without-progress-reproduction-audit-stream.md",
    "scripts/context_compaction_without_progress_reproduction_audit_stream_contract_common.py",
    "scripts/validate_context_compaction_without_progress_reproduction_audit_stream.py",
    "scripts/ci/run_context_compaction_without_progress_reproduction_audit_stream_probes_ci.sh",
)
READ_ONLY_INPUT_SURFACES = (
    "docs/workbook/protocol-issue-register-v1.6.md",
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-segmented-infrastructure-admission.md",
    "scripts/lane_segmented_infrastructure_admission_contract_common.py",
    "scripts/validate_lane_segmented_infrastructure_admission.py",
    "scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh",
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md",
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py",
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py",
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh",
)
VALIDATOR_COMMAND = (
    "TMPDIR=$PWD/.tmp python3 scripts/validate_context_compaction_without_progress_reproduction_audit_stream.py --json-only"
)
PROBE_COMMAND = (
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_context_compaction_without_progress_reproduction_audit_stream_probes_ci.sh"
)

DOC_EXPECTATIONS = {
    FIXED_WRITE_SET[0]: (
        STREAM_ID,
        CLASSIFICATION,
        TARGET_RESIDUAL_CLASS,
        "ISSUE-045",
        "ISSUE-046-candidate",
        *SEPARATION_BOUNDARIES,
        "do not reopen ISSUE-040 through ISSUE-048",
        "do not create a new issue by default",
        *ALLOWED_AUDIT_OUTCOMES,
    ),
    FIXED_WRITE_SET[1]: (
        STREAM_ID,
        CLASSIFICATION,
        "current known residual coverage is already machine-visible through ISSUE-045 and ISSUE-046-candidate surfaces",
        "registration of a new issue remains blocked unless uncovered reproduction appears",
        *SEPARATION_BOUNDARIES,
        *ALLOWED_AUDIT_OUTCOMES,
    ),
}

READ_ONLY_INPUT_EXPECTATIONS = {
    "docs/workbook/protocol-issue-register-v1.6.md": (
        "ISSUE-045 Lane segmented infrastructure admission is not frozen and handoff still depends on chat reconstruction",
        "repeated_compaction_without_progress_status",
        "execution_loop_not_entering_mutation_phase",
    ),
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md": (
        "Bounded planning is admitted, but repeated pre-mutation planning / re-anchoring / compaction without mutation progress is not admitted.",
        "repeated_compaction_without_progress_status",
        "execution_loop_not_entering_mutation_phase",
    ),
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-segmented-infrastructure-admission.md": (
        "repeated compaction without mutation progress is not admitted;",
        "execution_loop_not_entering_mutation_phase",
    ),
    "scripts/validate_lane_segmented_infrastructure_admission.py": (
        "repeated_compaction_without_progress_status",
        "execution_loop_not_entering_mutation_phase",
    ),
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md": (
        "ISSUE-045 forbids repeated pre-mutation planning/reanchor/compaction loops; ISSUE-046 additionally enforces post-lock live runtime actuator control and reply-envelope gating after scope/write-set lock.",
        "reply-envelope output",
        "emit_fail_close_token",
    ),
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md": (
        "ISSUE-045 forbids repeated pre-mutation planning, re-anchoring, and compaction loops before mutation progress.",
        "single-token fail-close",
        "reply-envelope gate",
    ),
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py": (
        "reply_envelope_not_admitted",
        "execution_loop_not_entering_mutation_phase",
    ),
}


def repo_root(start: Path | None = None) -> Path:
    if start is not None:
        return start.resolve()
    return Path(__file__).resolve().parents[1]


def canonical_payload() -> dict[str, Any]:
    return {
        "stream_id": STREAM_ID,
        "classification": CLASSIFICATION,
        "governing_law": GOVERNING_LAW,
        "target_residual_class": TARGET_RESIDUAL_CLASS,
        "current_coverage_judgment": CURRENT_COVERAGE_JUDGMENT,
        "fixed_write_set": list(FIXED_WRITE_SET),
        "read_only_input_surfaces": list(READ_ONLY_INPUT_SURFACES),
        "validator_command": VALIDATOR_COMMAND,
        "probe_command": PROBE_COMMAND,
        "separation_boundaries": list(SEPARATION_BOUNDARIES),
        "allowed_audit_outcomes": list(ALLOWED_AUDIT_OUTCOMES),
        "uncovered_promotion_gate": list(UNCOVERED_PROMOTION_GATE),
        "non_goals": [
            "do not reopen ISSUE-040 through ISSUE-048",
            "do not create a new issue by default",
            "do not mix protocol feedback / instance feedback gap handling into this stream",
            "do not mix canonical hard identity binding / owner-binding lock-in into this stream",
        ],
    }


def default_machine_state() -> dict[str, Any]:
    return {
        "stream_mode": "READ_ONLY",
        "residual_target_class": TARGET_RESIDUAL_CLASS,
        "coverage_classification_status": "CURRENTLY_COVERED_BY_ISSUE_045_AND_046",
        "issue_family_reopen_status": "NOT_ADMITTED_BY_DEFAULT",
        "new_issue_candidate_status": "NOT_ADMITTED_BY_DEFAULT",
        "protocol_feedback_mixing_status": "NOT_ADMITTED",
        "identity_binding_mixing_status": "NOT_ADMITTED",
        "observed_reproduction_status": "REQUIRES_MACHINE_VISIBLE_EVIDENCE",
        "stale_reasons": [],
    }
