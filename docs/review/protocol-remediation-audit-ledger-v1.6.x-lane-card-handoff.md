# Protocol Remediation Audit Ledger v1.6.x — Lane Card Handoff

This audit ledger records the canonical handoff surface for `ISSUE-040A` and mirrors the governance truth exactly.

Chat is navigation-only and is not a durable handoff state.
No card, no handoff.
No card, no takeover.
Handoff state must land on repo durable surface.
Reopen is allowed only through the closed trigger set frozen in the lane card.

<!-- lane-card-handoff-contract:start -->
```json
{
  "lane_id": "issue_040a_lane_card_handoff_contract_v1",
  "governing_law": "chat_navigation_only__no_card_no_handoff_no_takeover",
  "fixed_write_set": [
    "docs/governance/identity-lane-card-handoff-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-card-handoff.md",
    "scripts/lane_card_handoff_contract_common.py",
    "scripts/validate_lane_card_handoff_contract.py",
    "scripts/ci/run_lane_card_handoff_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize lane_card_handoff_contract_v1 only",
    "freeze required fields: lane_id, governing_law, fixed_write_set, layer_state, next_exact_action, validation_bundle, reopen_triggers, commit_gate"
  ],
  "validation_bundle": [
    "python3 scripts/validate_lane_card_handoff_contract.py --json-only",
    "bash scripts/ci/run_lane_card_handoff_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-040A only"
}
```
<!-- lane-card-handoff-contract:end -->

## Acceptance ledger

- Lane card handoff is admitted only when the governance doc and this review ledger carry the same contract payload.
- Takeover consumers may read the lane card, but they may not reopen law selection unless a frozen reopen trigger fires.
- Validation must stay on the narrow bundle frozen above; anything outside that bundle is out of scope for `ISSUE-040A`.
