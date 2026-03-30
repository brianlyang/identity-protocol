# Protocol Remediation Audit Ledger v1.6.x — Lane Reopen Gate

This audit ledger records the canonical reopen gate surface for `ISSUE-040C` and mirrors the governance truth exactly.

Reopen must be machine-triggered after handoff.
Freeform reinterpretation cannot reopen a closed lane.
Freeform takeover cannot replace admitted reopen triggers.
Broad reopen without admitted trigger is fail-close.
Only the closed trigger set frozen in the lane reopen gate contract may reopen the lane.

<!-- lane-reopen-gate-contract:start -->
```json
{
  "lane_id": "issue_040c_lane_reopen_gate_contract_v1",
  "governing_law": "reopen_must_be_machine_triggered__no_freeform_reinterpretation_after_handoff",
  "fixed_write_set": [
    "docs/governance/identity-lane-reopen-gate-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-reopen-gate.md",
    "scripts/lane_reopen_gate_contract_common.py",
    "scripts/validate_lane_reopen_gate_contract.py",
    "scripts/ci/run_lane_reopen_gate_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize lane_reopen_gate_contract_v1 only",
    "freeze reopen triggers as machine-admitted conditions only",
    "fail-close freeform takeover / freeform reinterpretation / broad reopen without admitted trigger"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_lane_reopen_gate_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_lane_reopen_gate_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-040C only"
}
```
<!-- lane-reopen-gate-contract:end -->

## Acceptance ledger

- Reopen after handoff is admitted only when the governance doc and this review ledger carry the same contract payload.
- Freeform reinterpretation, freeform takeover, and broad reopen without admitted trigger are all fail-close for `ISSUE-040C`.
- Only the closed trigger set frozen above may reopen the lane after handoff.
- Validation must stay on the narrow bundle frozen above; anything outside that bundle is out of scope for `ISSUE-040C`.
