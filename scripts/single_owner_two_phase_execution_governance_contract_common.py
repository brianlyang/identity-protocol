#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

PASS_REQUIRED = "PASS_REQUIRED"
FAIL_REQUIRED = "FAIL_REQUIRED"

ISSUE_ID = "ISSUE-050"
CONTRACT_ID = "architect_authorized_single_owner_two_phase_execution_governance_contract_v1"
GOVERNING_LAW = (
    "architect-authorized execution-governance follow-on may be admitted as one non-canonical "
    "protocol_feedback_packet with same-owner two-phase semantics only when canonical protocol "
    "truth remains role-level portable, concrete runtime bindings stay inside explicit "
    "runtime-evidence surfaces, and any reentry into canonical truth fails closed"
)
TRUTH_CLASS = "protocol_feedback_packet"
OWNER_ROLE = "architect"
SUGGESTED_EXECUTOR_ROLE = "architect"
LANE_EXECUTION_MODEL = "single_owner_two_phase"
CANONICAL_TRUTH_INVARIANT = (
    "canonical protocol truth remains role-level and portable only; concrete runtime "
    "identity/session/transaction/checkout-instance/host-path literals are admitted only in "
    "explicit non-canonical runtime-evidence surfaces, and any reentry into canonical truth "
    "must fail-close"
)
FAIL_CLOSE_REASON = "single_owner_two_phase_execution_governance_drift"
FAIL_CLOSE_REASON_FAMILY = (
    "feedback_packet_must_not_be_canonical",
    "role_identity_field_pollution",
    "runtime_evidence_reentry_into_canonical_truth",
    "phase_b_requires_phase_a_receipt",
    "second_owner_without_handoff_receipt_not_admitted",
    "execution_governance_scope_reopen_not_admitted",
    "monotonic_progress_not_machine_visible",
    "repeat_budget_not_machine_visible",
    "compaction_continuation_receipt_not_machine_visible",
    "exact_write_set_lock_not_machine_visible",
)

PHASE_A_ALLOWED_ACTIONS = (
    "freeze_contract",
    "emit_contract_freeze_receipt",
    "emit_blocker_receipt",
    "emit_fail_close_token",
)
PHASE_B_ALLOWED_ACTIONS = (
    "mutate_fixed_write_set",
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token",
)
REQUIRED_MACHINE_FIELDS = (
    "truth_class",
    "canonical",
    "portable",
    "runtime_binding_not_authoritative",
    "owner_role",
    "suggested_executor_role",
    "lane_execution_model",
    "current_phase",
    "phase_a_completion_receipt_status",
    "phase_b_precondition_status",
    "exact_write_set_lock_status",
    "monotonic_progress_status",
    "repeated_inspection_budget_status",
    "compaction_continuation_receipt_status",
    "canonical_truth_projection_status",
    "runtime_evidence_reentry_status",
    "handoff_policy",
    "second_owner_entry_status",
    "stale_reasons",
)
FIXED_WRITE_SET = (
    "docs/governance/identity-single-owner-two-phase-execution-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-single-owner-two-phase-execution-governance.md",
    "scripts/single_owner_two_phase_execution_governance_contract_common.py",
    "scripts/validate_single_owner_two_phase_execution_governance.py",
    "scripts/ci/run_single_owner_two_phase_execution_governance_probes_ci.sh",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
)
READ_ONLY_INPUT_SURFACES = (
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md",
)
VALIDATOR_COMMAND = (
    "TMPDIR=$PWD/.tmp python3 scripts/validate_single_owner_two_phase_execution_governance.py --json-only"
)
PROBE_COMMAND = (
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_single_owner_two_phase_execution_governance_probes_ci.sh"
)
REOPEN_TRIGGERS = (
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only",
)
COMMIT_GATE = (
    "one isolated commit for ISSUE-050 only after validator=PASS_REQUIRED, probe=PASS, and "
    "staged paths equal the fixed_write_set exactly"
)

DOC_EXPECTATIONS = {
    FIXED_WRITE_SET[0]: (
        "truth_class = protocol_feedback_packet",
        "canonical = false",
        "portable = true",
        "runtime_binding_not_authoritative = true",
        "Canonical protocol truth must remain role-level and portable.",
        "Any reentry, projection, copy-through, normalization, or dependency of those literals into",
        "single_owner_two_phase",
        "execution_governance_contract_freeze_receipt",
        "single_owner_no_handoff",
        "explicit_blocker_or_handoff_receipt_only",
        "ISSUE-045",
        "ISSUE-046",
        "ISSUE-049",
        "accepted control-plane runtime-evidence-only package closure",
    ),
    FIXED_WRITE_SET[1]: (
        "`status`: ACCEPTED",
        "`ISSUE-050`",
        "canonical protocol truth remains role-level and portable only",
        "concrete identity is not admitted in any `*_role` field",
        "phase_b` is `FAIL_REQUIRED` unless `execution_governance_contract_freeze_receipt` is already repo-visible",
        "Same-owner continuation is the default.",
        "Second-owner entry is not admitted unless a blocker or handoff receipt is machine-visible.",
    ),
    FIXED_WRITE_SET[5]: (
        "### ISSUE-050 - Architect-authorized execution-governance follow-on lacks machine-admitted single-owner two-phase lane semantics",
        "- `status`: CLOSED",
        "architect_authorized_single_owner_two_phase_execution_governance_contract_v1",
        "single_owner_two_phase",
        "role/identity pollution",
    ),
    FIXED_WRITE_SET[6]: (
        "| ISSUE-050 Architect-authorized execution-governance follow-on lacks machine-admitted single-owner two-phase lane semantics | CLOSED | `architect_authorized_single_owner_two_phase_execution_governance_contract_v1` |",
        "single-owner two-phase execution-governance",
        "role/identity separation",
        "do not reopen accepted control-plane runtime-evidence-only packages",
    ),
}
READ_ONLY_INPUT_EXPECTATIONS = {
    READ_ONLY_INPUT_SURFACES[0]: (
        "Continuation and takeover must consume repo-visible baton surfaces, not chat reconstruction.",
        "next_exact_action",
        "execution_loop_not_entering_mutation_phase",
    ),
    READ_ONLY_INPUT_SURFACES[1]: (
        "allowed_next_actions collapse exactly to",
        "emit_fail_close_token",
        "reply-envelope output",
    ),
    READ_ONLY_INPUT_SURFACES[2]: (
        "Recognized protocol-feedback escalation must switch to the protocol-feedback rail and enter canonical emission / receipt flow.",
        "protocol-feedback rail",
        "canonical emission / receipt flow",
    ),
    READ_ONLY_INPUT_SURFACES[3]: (
        "follow-on hardening package is **accepted** for the scoped control-plane package",
        "validator replay is green",
        "probe replay is green",
    ),
}
SCRIPT_EXPECTATIONS = {
    FIXED_WRITE_SET[2]: (
        "CANONICAL_TRUTH_INVARIANT",
        "FAIL_CLOSE_REASON_FAMILY",
        "REQUIRED_MACHINE_FIELDS",
        "READ_ONLY_INPUT_SURFACES",
        "ROLE_FIELD_NAMES",
        "extract_json_payload",
    ),
    FIXED_WRITE_SET[3]: (
        "governance_review_contract_mismatch",
        "feedback_packet_must_not_be_canonical",
        "runtime_evidence_reentry_into_canonical_truth",
        "phase_b_requires_phase_a_receipt",
        "second_owner_without_handoff_receipt_not_admitted",
    ),
    FIXED_WRITE_SET[4]: (
        "feedback_packet_must_not_be_canonical",
        "role_identity_field_pollution",
        "PASS single_owner_two_phase_execution_governance_probes",
    ),
}

ROLE_FIELD_NAMES = ("owner_role", "suggested_executor_role")
ROLE_FIELD_IDENTITY_RE = re.compile(r"^base-repo-[A-Za-z0-9._-]+$")
CANONICAL_TRUE_RE = re.compile(r'"canonical"\s*:\s*true')
JSON_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def repo_root(start: Path | None = None) -> Path:
    return Path(start).resolve() if start is not None else Path(__file__).resolve().parents[1]


def extract_json_payload(text: str) -> dict[str, Any]:
    match = JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError("missing_json_contract_block")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError("json_contract_block_not_object")
    return payload


def canonical_payload() -> dict[str, Any]:
    return {
        "issue_id": ISSUE_ID,
        "contract_id": CONTRACT_ID,
        "governing_law": GOVERNING_LAW,
        "truth_class": TRUTH_CLASS,
        "canonical": False,
        "portable": True,
        "runtime_binding_not_authoritative": True,
        "canonical_truth_invariant": CANONICAL_TRUTH_INVARIANT,
        "owner_role": OWNER_ROLE,
        "suggested_executor_role": SUGGESTED_EXECUTOR_ROLE,
        "optional_handoff_receipt_field_family": [
            "suggested_executor_identity",
            "handoff_reason",
            "blocker_reason",
        ],
        "lane_execution_model": LANE_EXECUTION_MODEL,
        "current_phase": "phase_a",
        "phase_a": {
            "phase_id": "contract_freeze",
            "required_outputs": [
                "execution_governance_contract_doc",
                "execution_governance_contract_freeze_receipt",
            ],
            "allowed_actions": list(PHASE_A_ALLOWED_ACTIONS),
        },
        "phase_b": {
            "phase_id": "bounded_implementation_closeout",
            "precondition_receipt": "execution_governance_contract_freeze_receipt",
            "required_outputs": [
                "validator",
                "probe",
                "review_ledger_entry",
                "acceptance_package",
            ],
            "allowed_actions": list(PHASE_B_ALLOWED_ACTIONS),
        },
        "required_machine_fields": list(REQUIRED_MACHINE_FIELDS),
        "fixed_write_set": list(FIXED_WRITE_SET),
        "read_only_input_surfaces": list(READ_ONLY_INPUT_SURFACES),
        "validation_bundle": [VALIDATOR_COMMAND, PROBE_COMMAND],
        "handoff_policy": {
            "default_mode": "single_owner_no_handoff",
            "exception_mode": "explicit_blocker_or_handoff_receipt_only",
        },
        "related_closed_streams": [
            "ISSUE-045",
            "ISSUE-046",
            "ISSUE-049",
            "control_plane_role_binding_overlay_hardening",
        ],
        "reopen_triggers": list(REOPEN_TRIGGERS),
        "commit_gate": COMMIT_GATE,
    }


def default_machine_state() -> dict[str, Any]:
    return {
        "truth_class": TRUTH_CLASS,
        "canonical": False,
        "portable": True,
        "runtime_binding_not_authoritative": True,
        "owner_role": OWNER_ROLE,
        "suggested_executor_role": SUGGESTED_EXECUTOR_ROLE,
        "lane_execution_model": LANE_EXECUTION_MODEL,
        "current_phase": "phase_a",
        "phase_a_completion_receipt_status": "REQUIRED_BEFORE_PHASE_B",
        "phase_b_precondition_status": "BLOCKED_UNTIL_FREEZE_RECEIPT",
        "exact_write_set_lock_status": "REQUIRED_IN_PHASE_B",
        "monotonic_progress_status": "REQUIRED",
        "repeated_inspection_budget_status": "BOUNDED",
        "compaction_continuation_receipt_status": "REQUIRED_AFTER_COMPACTION",
        "canonical_truth_projection_status": "ROLE_LEVEL_PORTABLE_ONLY",
        "runtime_evidence_reentry_status": "FAIL_CLOSE_ON_REENTRY",
        "handoff_policy": {
            "default_mode": "single_owner_no_handoff",
            "exception_mode": "explicit_blocker_or_handoff_receipt_only",
        },
        "second_owner_entry_status": "BLOCKED_UNLESS_HANDOFF_RECEIPT_PRESENT",
        "stale_reasons": [],
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
