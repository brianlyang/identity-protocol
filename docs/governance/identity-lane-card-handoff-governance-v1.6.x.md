# Identity Lane Card Handoff Governance v1.6.x

This document formalizes `lane_card_handoff_contract_v1` for `ISSUE-040A` as the only active lane in this change.

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

## Governance interpretation

- `lane_id` is immutable for this handoff surface.
- `governing_law` freezes the boundary: chat can navigate the operator, but chat cannot serve as takeover memory.
- `fixed_write_set` is closed. No adjacent workbook rows, neighboring issues, or protocol-wide sweeps are admitted by this lane.
- `next_exact_action` is singular and narrow: formalize the contract only.
- `validation_bundle` is the only admitted machine check for this lane.
- `reopen_triggers` are closed and fail-close. No other reopen path is valid.
- `commit_gate` allows exactly one isolated `ISSUE-040A` commit.
