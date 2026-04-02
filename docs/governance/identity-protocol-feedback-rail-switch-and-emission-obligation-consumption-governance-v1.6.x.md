# Identity Protocol Feedback Rail Switch and Emission Obligation Consumption Governance v1.6.x

Minimal governance skeleton for ISSUE-049 explicit protocol-feedback rail switch and canonical emission / receipt flow consumption.

Explicit protocol-feedback escalation must be consumed into machine action.
Once `protocol_feedback_request_detected=true`, explanation-only handling is not admitted completion.
Protocol feedback request detection, rule knowledge, rail selection, emission obligation status, channel entry, emit invocation, artifact materialization, rule consumption status, and stale reasons are required machine-visible fields.
Recognized protocol-feedback escalation must switch to the protocol-feedback rail and enter canonical emission / receipt flow.
The shared validator composes bootstrap readiness, atomic emit, and atomic emit validation into one executable proof lane.

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

Interpretation:
- explicit protocol-feedback escalation must leave explanation-only handling and become protocol action;
- rail selection and canonical emission / receipt flow must be machine-visible together;
- skipped emit, skipped channel entry, or missing artifacts remain fail-closed under ISSUE-049.
