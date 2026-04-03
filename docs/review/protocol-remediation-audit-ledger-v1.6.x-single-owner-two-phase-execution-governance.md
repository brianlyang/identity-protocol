# Protocol remediation audit ledger v1.6.x - single-owner two-phase execution governance

## Status

- `status`: ACCEPTED
- `governing_issue`: `ISSUE-050`
- `owner_doc`: `docs/governance/identity-single-owner-two-phase-execution-governance-v1.6.x.md`

## Why ISSUE-050 exists

Existing execution-governance owner surfaces had already frozen two important protections:

- `ISSUE-045` made segmented continuation repo-visible and fail-closed chat reconstruction;
- `ISSUE-046` collapsed post-lock runtime actions to mutation / validator / probe / commit / blocker / fail-close only;
- `ISSUE-049` ensured explicit protocol-feedback escalation enters rail-switch plus canonical emission / receipt flow.

But a residual governance ambiguity remained for architect-owned follow-on work:

- a packet could diagnose the right execution-loop gap;
- yet still mix role fields with concrete identity;
- or let runtime-evidence literals project back into canonical truth;
- or force a second-owner handoff before the law was frozen;
- or let implementation start without a repo-visible contract-freeze receipt.

`ISSUE-050` closes that ambiguity by machine-admitting one non-canonical
`protocol_feedback_packet` that carries `single_owner_two_phase` semantics.

## Distinction vs ISSUE-045 / ISSUE-046 / ISSUE-049

- `ISSUE-045` governs segmented lane baton continuity and prohibition on chat reconstruction.
- `ISSUE-046` governs post-lock runtime actuator / reply-envelope collapse.
- `ISSUE-049` governs explicit protocol-feedback escalation entering rail-switch + canonical emission / receipt flow.
- `ISSUE-050` governs how an architect-authorized execution-governance follow-on packet is admitted as one same-owner two-phase lane without role/identity pollution, runtime-evidence reentry, or silent handoff drift.

`ISSUE-050` does not reopen `ISSUE-045`, `ISSUE-046`, `ISSUE-049`, or accepted control-plane runtime-evidence-only closure.

## Accepted remediation judgment

The accepted packet semantics are:

- `truth_class = protocol_feedback_packet`
- `canonical = false`
- `portable = true`
- `runtime_binding_not_authoritative = true`
- `lane_execution_model = single_owner_two_phase`

The accepted canonical-truth boundary is:

- canonical protocol truth remains role-level and portable only;
- concrete runtime identity, session, transaction, checkout-instance, host-path, or other runtime-specific literals are admitted only in explicit non-canonical runtime-evidence surfaces;
- any reentry, projection, copy-through, normalization, or dependency of those literals into canonical truth is `FAIL_REQUIRED`.

The accepted role / identity split is:

- `owner_role` and `suggested_executor_role` remain role-level only;
- concrete identity is not admitted in any `*_role` field;
- `suggested_executor_identity` is admitted only in non-canonical handoff / blocker receipts.

The accepted phase ordering is:

1. `phase_a = contract_freeze`
2. `phase_b = bounded_implementation_closeout`

`phase_b` is `FAIL_REQUIRED` unless `execution_governance_contract_freeze_receipt` is already repo-visible.

Same-owner continuation is the default.
Second-owner entry is not admitted unless a blocker or handoff receipt is machine-visible.

## Audit consequence

- `PASS_REQUIRED` when the packet remains non-canonical, role-pure, same-owner by default, receipt-gated across `phase_a -> phase_b`, and keeps runtime-evidence literals out of canonical truth.
- `FAIL_REQUIRED` when the packet drifts into canonical truth, places concrete identity in any role field, reintroduces runtime-evidence literals into canonical truth, admits `phase_b` before the freeze receipt, or silently allows a second owner to take over.

## Canonical packet payload

```json
{
  "issue_id": "ISSUE-050",
  "contract_id": "architect_authorized_single_owner_two_phase_execution_governance_contract_v1",
  "governing_law": "architect-authorized execution-governance follow-on may be admitted as one non-canonical protocol_feedback_packet with same-owner two-phase semantics only when canonical protocol truth remains role-level portable, concrete runtime bindings stay inside explicit runtime-evidence surfaces, and any reentry into canonical truth fails closed",
  "truth_class": "protocol_feedback_packet",
  "canonical": false,
  "portable": true,
  "runtime_binding_not_authoritative": true,
  "canonical_truth_invariant": "canonical protocol truth remains role-level and portable only; concrete runtime identity/session/transaction/checkout-instance/host-path literals are admitted only in explicit non-canonical runtime-evidence surfaces, and any reentry into canonical truth must fail-close",
  "owner_role": "architect",
  "suggested_executor_role": "architect",
  "optional_handoff_receipt_field_family": [
    "suggested_executor_identity",
    "handoff_reason",
    "blocker_reason"
  ],
  "lane_execution_model": "single_owner_two_phase",
  "current_phase": "phase_a",
  "phase_a": {
    "phase_id": "contract_freeze",
    "required_outputs": [
      "execution_governance_contract_doc",
      "execution_governance_contract_freeze_receipt"
    ],
    "allowed_actions": [
      "freeze_contract",
      "emit_contract_freeze_receipt",
      "emit_blocker_receipt",
      "emit_fail_close_token"
    ]
  },
  "phase_b": {
    "phase_id": "bounded_implementation_closeout",
    "precondition_receipt": "execution_governance_contract_freeze_receipt",
    "required_outputs": [
      "validator",
      "probe",
      "review_ledger_entry",
      "acceptance_package"
    ],
    "allowed_actions": [
      "mutate_fixed_write_set",
      "run_validator",
      "run_probe",
      "stage_and_commit",
      "emit_blocker_receipt",
      "emit_fail_close_token"
    ]
  },
  "required_machine_fields": [
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
    "stale_reasons"
  ],
  "fixed_write_set": [
    "docs/governance/identity-single-owner-two-phase-execution-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-single-owner-two-phase-execution-governance.md",
    "scripts/single_owner_two_phase_execution_governance_contract_common.py",
    "scripts/validate_single_owner_two_phase_execution_governance.py",
    "scripts/ci/run_single_owner_two_phase_execution_governance_probes_ci.sh",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/workbook/protocol-issue-register-v1.6.md"
  ],
  "read_only_input_surfaces": [
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_single_owner_two_phase_execution_governance.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_single_owner_two_phase_execution_governance_probes_ci.sh"
  ],
  "handoff_policy": {
    "default_mode": "single_owner_no_handoff",
    "exception_mode": "explicit_blocker_or_handoff_receipt_only"
  },
  "related_closed_streams": [
    "ISSUE-045",
    "ISSUE-046",
    "ISSUE-049",
    "control_plane_role_binding_overlay_hardening"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-050 only after validator=PASS_REQUIRED, probe=PASS, and staged paths equal the fixed_write_set exactly"
}
```

## Review closing note

`ISSUE-050` proves that one expert can now close the full lane when that expert is acting under
architect-owned law freeze and keeps the packet non-canonical. The protocol no longer requires a
forced second-owner relay merely to preserve machine-law hygiene; it requires only that the same
owner produce the freeze receipt first, preserve role/identity separation throughout the lane,
and fail-close any attempt to project runtime-evidence literals back into canonical truth.
