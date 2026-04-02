
# Protocol remediation audit ledger v1.6.x - protocol feedback rail switch and emission obligation consumption

## Status

- `status`: OPEN
- `governing_issue`: `ISSUE-049`
- `owner_doc`: `docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md`

## Why ISSUE-049 exists

Current protocol-feedback infrastructure already contains canonical emitters and validator surfaces, but one narrow machine-consumption gap remains open: when a user explicitly asks for protocol feedback or escalation, the instance may still remain inside ordinary explanation/chat handling instead of consuming that request into the protocol-feedback rail and entering canonical emission / receipt flow.

`ISSUE-049` exists to freeze that this is not an optional interpretation-layer courtesy. Once explicit protocol-feedback escalation is recognized, the request must become machine action.

## Narrow scope boundary

This lane is intentionally narrow.

It does **not** reopen or absorb:

- context compact / repeated compaction without progress;
- ISSUE-045 / ISSUE-046 / ISSUE-047 / ISSUE-048 anti-loop family semantics;
- hardcoded identity / owner binding decoupling;
- historical `IP-PFB-CH-006` single-code blame framing;
- a generalized claim that “protocol feedback as a whole is missing”.

This lane governs one specific contract gap only: recognized protocol-feedback escalation must be consumed into rail switch + canonical emission / receipt flow.

## Opening remediation judgment

Explicit protocol-feedback escalation must be machine-consumed.

Once the request is recognized as protocol-feedback / escalation, the instance must switch to the protocol-feedback rail.

Once the protocol-feedback rail is selected, canonical emission / receipt flow must be entered.

Explanation-only handling, acknowledgement-only handling, or generic chat continuation is not admitted completion for this request class.

## Machine-visible state family

The following state family is frozen as the minimum machine-visible contract surface for `ISSUE-049`:

- `protocol_feedback_request_detected`
- `protocol_feedback_rule_known`
- `protocol_feedback_rail_selected`
- `protocol_feedback_emission_obligation_status`
- `protocol_feedback_channel_entered`
- `protocol_feedback_emit_invoked`
- `protocol_feedback_artifact_materialized`
- `protocol_feedback_rule_consumption_status`
- `stale_reasons`

Review interpretation:

- explicit protocol-feedback / escalation detection must become visible rather than inferred from chat wording;
- rule knowledge must become visible so the instance cannot hide behind vague awareness claims;
- rail selection must become visible so the runtime cannot remain on a generic chat rail after recognizing escalation;
- emission obligation, channel entry, emit invocation, and artifact materialization must become visible so explanation-only handling cannot masquerade as completion;
- stale or incomplete handling must remain machine-visible through `stale_reasons`.

## Audit consequence

- `PASS_REQUIRED` when explicit protocol-feedback escalation is recognized, the protocol-feedback rail is selected, canonical emission / receipt flow is entered, and the machine-visible state family shows the request was consumed into protocol action.
- `FAIL_REQUIRED` when explicit escalation is recognized but the runtime remains on explanation-only handling, never enters the protocol-feedback channel, never invokes canonical emit, never materializes the required artifact, or leaves rule consumption implicit.

## Why this is an issue lane, not a stream

The current defect is a single narrow contract gap with a bounded invariant and bounded machine-visible state family.

It should therefore open as an ISSUE-level lane first.

Only if later evidence shows multiple sibling protocol-feedback defects with distinct boundaries should this be promoted into a broader stream.

## Canonical lane payload

```json
{
  "lane_id": "protocol_feedback_rail_switch_and_emission_obligation_consumption_contract_v1",
  "governing_law": "recognized_protocol_feedback_escalation_must_switch_rail_and_enter_canonical_emit_receipt_flow",
  "fixed_write_set": [
    "docs/workbook/protocol-issue-register-v1.6.md",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-protocol-feedback-rail-switch-and-emission-obligation-consumption.md"
  ],
  "layer_state": "issue-level protocol-feedback contract opening",
  "next_exact_action": [
    "formalize this as a narrow ISSUE-level lane only",
    "freeze the rail-switch and canonical emission-obligation consumption invariant",
    "require the machine-visible state family for explicit protocol-feedback escalation",
    "fail-close explanation-only handling as non-completion"
  ],
  "validation_bundle": [
    "python3 scripts/validate_issue_register_consistency.py --json-only",
    "python3 scripts/docs_command_contract_check.py"
  ],
  "reopen_triggers": [
    "future validator/probe evidence shows the same invariant regressed",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-049 only"
}
```

## Review opening note

This ledger opens `ISSUE-049` as a bounded protocol-feedback contract lane only. It does not claim that the full implementation lane is closed, and it does not permit explanation-only handling to be treated as admitted completion once explicit escalation has been recognized.
