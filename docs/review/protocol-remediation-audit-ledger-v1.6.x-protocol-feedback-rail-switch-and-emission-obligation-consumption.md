# Protocol Remediation Audit Ledger v1.6.x — Protocol Feedback Rail Switch and Emission Obligation Consumption

## Status

- `status`: CLOSED
- `governing_issue`: `ISSUE-049`
- `governance_doc`: `docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md`
- `validator`: `TMPDIR=$PWD/.tmp python3 scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py --json-only`
- `probe`: `TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh`

## Why ISSUE-049 existed

Explicit protocol-feedback / escalation requests could be semantically understood yet still remain inside explanation-only handling. The request was not reliably consumed into machine action, the runtime could remain off the `protocol-feedback` rail, and canonical emission / receipt flow could be skipped even after explicit escalation had been recognized.

## Accepted remediation judgment

Explicit protocol-feedback escalation must be consumed into machine action.
Once `protocol_feedback_request_detected=true`, explanation-only handling is not admitted completion.
Protocol feedback request detection, rule knowledge, rail selection, emission obligation status, channel entry, emit invocation, artifact materialization, rule consumption status, and stale reasons are required machine-visible fields.
Recognized protocol-feedback escalation must switch to the protocol-feedback rail and enter canonical emission / receipt flow.
The shared validator composes bootstrap readiness, atomic emit, and atomic emit validation into one executable proof lane.

## Machine-visible state family

Required machine-visible protocol-feedback consumption fields:
- protocol_feedback_request_detected
- protocol_feedback_rule_known
- protocol_feedback_rail_selected
- protocol_feedback_emission_obligation_status
- protocol_feedback_channel_entered
- protocol_feedback_emit_invoked
- protocol_feedback_artifact_materialized
- protocol_feedback_rule_consumption_status
- stale_reasons

## Canonical lane payload

```json
{
  "lane_id": "protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_v1",
  "governing_law": "recognized_protocol_feedback_escalation_must_switch_rail_and_enter_canonical_emit_receipt_flow",
  "fixed_write_set": [
    "docs/governance/identity-protocol-feedback-rail-switch-and-emission-obligation-consumption-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py",
    "scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py",
    "scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize explicit protocol-feedback escalation consumption only",
    "require recognized protocol-feedback escalation to select the protocol-feedback rail",
    "require canonical emission / receipt flow and the machine-visible ISSUE-049 state family"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-049 only after validator=PASS_REQUIRED and probe=PASS"
}
```

## Acceptance evidence

- `scripts/protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_common.py` freezes the bounded ISSUE-049 contract payload, required machine-visible state family, and workbook closure expectations.
- `scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py` composes `scripts/validate_protocol_feedback_bootstrap_ready.py`, `scripts/emit_protocol_feedback_atomic.py`, and `scripts/validate_protocol_feedback_atomic_emit.py` on an isolated fixture pack so explicit escalation is consumed into rail selection plus canonical emission / receipt flow without mutating the repo-local runtime.
- `scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh` proves positive `PASS_REQUIRED` on explicit request consumption and negative `FAIL_REQUIRED` on skipped atomic emit, skipped outbox sync, and document drift.
- `TMPDIR=$PWD/.tmp python3 scripts/validate_protocol_feedback_rail_switch_and_emission_obligation_consumption.py --json-only` now returns `PASS_REQUIRED`.
- `TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_feedback_rail_switch_and_emission_obligation_consumption_probes_ci.sh` now returns `PASS`.

## Closure boundary

This closes ISSUE-049 as the narrow protocol-feedback consumption lane only. It does not reopen owner-binding portability, anti-loop family semantics, or generalized protocol-feedback scope.
