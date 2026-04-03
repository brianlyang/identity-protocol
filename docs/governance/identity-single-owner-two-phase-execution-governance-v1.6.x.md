# Identity single-owner two-phase execution governance v1.6.x

## Status

- `status`: ACTIVE
- `scope`: `v1.6.x` root infra follow-on
- `governing_issue`: `ISSUE-050`

## Governing law

Architect-authorized execution-governance follow-on may be admitted as one non-canonical
`protocol_feedback_packet` with `single_owner_two_phase` lane semantics when it does not
reopen already accepted truth packages.

The packet itself must remain:

- `truth_class = protocol_feedback_packet`
- `canonical = false`
- `portable = true`
- `runtime_binding_not_authoritative = true`

Canonical protocol truth must remain role-level and portable.
Concrete runtime identity, session, transaction, checkout-instance, host-path, or other
runtime-specific literals are admitted only in explicitly marked runtime-evidence surfaces.
Any reentry, projection, copy-through, normalization, or dependency of those literals into
canonical truth must fail-close before success.

Role and identity must remain strictly separated:

- `owner_role` and `suggested_executor_role` must be role-valued only;
- concrete identity is not admitted in any `*_role` field;
- `suggested_executor_identity` is admitted only in a non-canonical handoff receipt or blocker receipt surface.

The lane execution model is `single_owner_two_phase`:

1. `phase_a = contract_freeze`
2. `phase_b = bounded_implementation_closeout`

`phase_b` is not admitted before the repo-visible `execution_governance_contract_freeze_receipt`
is materialized.

Default handoff policy is `single_owner_no_handoff`.
A second owner may enter only through `explicit_blocker_or_handoff_receipt_only`.
Silent parallel mutation of root semantics is not admitted.

This follow-on builds on, but does not reopen:

- `ISSUE-045` segmented lane baton continuity
- `ISSUE-046` scope-locked mutation-phase runtime enforcement
- `ISSUE-049` protocol-feedback rail-switch / emission obligation consumption
- accepted control-plane runtime-evidence-only package closure

## Machine-visible packet fields

Required machine-visible fields:

- `truth_class`
- `canonical`
- `portable`
- `runtime_binding_not_authoritative`
- `owner_role`
- `suggested_executor_role`
- `lane_execution_model`
- `current_phase`
- `phase_a_completion_receipt_status`
- `phase_b_precondition_status`
- `exact_write_set_lock_status`
- `monotonic_progress_status`
- `repeated_inspection_budget_status`
- `compaction_continuation_receipt_status`
- `canonical_truth_projection_status`
- `runtime_evidence_reentry_status`
- `handoff_policy`
- `second_owner_entry_status`
- `stale_reasons`

## Admitted actions by phase

### Phase A

Allowed next actions collapse to:

- `freeze_contract`
- `emit_contract_freeze_receipt`
- `emit_blocker_receipt`
- `emit_fail_close_token`

### Phase B

Allowed next actions collapse to:

- `mutate_fixed_write_set`
- `run_validator`
- `run_probe`
- `stage_and_commit`
- `emit_blocker_receipt`
- `emit_fail_close_token`

## PASS / FAIL semantics

- `PASS_REQUIRED`
  - the packet remains non-canonical and portable;
  - role / identity separation is preserved;
  - canonical truth remains role-level portable only;
  - runtime-evidence literals do not reenter canonical truth;
  - `phase_b` is gated by the repo-visible freeze receipt from `phase_a`;
  - same-owner continuation is explicitly admitted;
  - second-owner entry requires explicit blocker / handoff receipt;
  - monotonic progress, repeat budget, compaction continuation receipt, exact write-set lock,
    and reentry fail-close remain machine-visible.
- `FAIL_REQUIRED`
  - the packet drifts into canonical truth;
  - a concrete identity appears inside `owner_role` or `suggested_executor_role`;
  - runtime-evidence literals reenter canonical truth;
  - `phase_b` is admitted without the phase-A freeze receipt;
  - second-owner entry is admitted without blocker / handoff receipt;
  - the packet reopens `ISSUE-045`, `ISSUE-046`, `ISSUE-049`, or accepted control-plane runtime-evidence-only closure.

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

## Closure effect

`ISSUE-050` closes the missing admission rule for architect-authorized execution-governance
follow-on. One owner may now freeze the law and implement the bounded closeout in the same lane,
but only through `phase_a` then `phase_b`, with non-canonical packet semantics, explicit
role/identity separation, role-level portable canonical truth, runtime-evidence-only concrete
bindings, and fail-close on silent second-owner takeover or runtime-evidence reentry.
