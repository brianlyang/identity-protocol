# Identity Lane Execution Receipt Governance v1.6.x

This document formalizes `lane_execution_receipt_contract_v1` for `ISSUE-040B` as the only active lane in this change.

Execution receipt is required for handoff and continuation.
Handoff state must be durable and repo-native, not chat-native.
Only durable success receipt or durable blocked receipt is admitted.
Chat recap cannot serve as execution receipt.
Reopen is allowed only through the closed trigger set frozen in the lane execution receipt contract.

<!-- lane-execution-receipt-contract:start -->
```json
{
  "lane_id": "issue_040b_lane_execution_receipt_contract_v1",
  "governing_law": "execution_receipt_required__handoff_state_must_be_durable_not_chat_native",
  "fixed_write_set": [
    "docs/governance/identity-lane-execution-receipt-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-execution-receipt.md",
    "scripts/lane_execution_receipt_contract_common.py",
    "scripts/validate_lane_execution_receipt_contract.py",
    "scripts/ci/run_lane_execution_receipt_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize lane_execution_receipt_contract_v1 only",
    "freeze durable execution receipt fields required for handoff/continuation",
    "admit only durable success/blocked receipt, not chat recap"
  ],
  "validation_bundle": [
    "python3 scripts/validate_lane_execution_receipt_contract.py --json-only",
    "bash scripts/ci/run_lane_execution_receipt_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-040B only"
}
```
<!-- lane-execution-receipt-contract:end -->

## Governance interpretation

- `lane_id` is immutable for this execution receipt surface.
- `governing_law` freezes the boundary: execution state must survive handoff on durable repo surface instead of chat recap.
- `fixed_write_set` is closed. Adjacent issues, workbook expansions, and protocol-wide sweeps are out of scope for this lane.
- `next_exact_action` is singular and narrow: formalize the contract only and freeze the durable receipt boundary.
- `validation_bundle` is the only admitted machine check for this lane.
- `reopen_triggers` are closed and fail-close. No other reopen path is valid.
- `commit_gate` allows exactly one isolated `ISSUE-040B` commit.
