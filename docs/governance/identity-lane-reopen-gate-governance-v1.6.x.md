# Identity Lane Reopen Gate Governance v1.6.x

This document formalizes `lane_reopen_gate_contract_v1` for `ISSUE-040C` as the only active lane in this change.

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

## Governance interpretation

- `lane_id` is immutable for this reopen gate surface.
- `governing_law` freezes the boundary: reopen after handoff must come only from machine-admitted triggers.
- `fixed_write_set` is closed. Adjacent issues, workbook expansions, and protocol-wide sweeps are out of scope for this lane.
- `next_exact_action` is singular and narrow: formalize the reopen gate contract only and freeze the admitted trigger boundary.
- `validation_bundle` is the only admitted machine check for this lane and remains repo-local through `TMPDIR=$PWD/.tmp`.
- `reopen_triggers` are closed and fail-close. Freeform reinterpretation, freeform takeover, and broad reopen are invalid unless the frozen trigger set admits them.
- `commit_gate` allows exactly one isolated `ISSUE-040C` commit.
