# Identity Governed Root Replay Exclusion Governance v1.6.x

Minimal governance skeleton for ISSUE-041C governed-root replay exclusion.

Nested governed-root replay inside governed scratch is not admitted.
Paths shaped like repo/.tmp/identity-runtime/... must fail-close when governed roots are re-materialized inside governed scratch.
Governed root replay exclusion status, replay path shape, governed scratch root, guard cleanup admission status, and live runtime exclusion status are required exclusion fields.
Guard cleanup may delete only machine-admitted stale residue and must not overreach into live runtime by heuristic cleanup.
Live runtime exclusion must remain machine-visible wherever governed-root replay exclusion is evaluated.

Required machine-visible governed-root replay exclusion fields:
- governed_root_replay_exclusion_status
- governed_root_replay_path_shape
- governed_scratch_root
- guard_cleanup_admission_status
- live_runtime_exclusion_status

```json
{
  "lane_id": "issue_041c_governed_root_replay_exclusion_contract_v1",
  "governing_law": "nested_governed_root_replay_not_admitted__guard_must_not_overreach_live_runtime",
  "fixed_write_set": [
    "docs/governance/identity-governed-root-replay-exclusion-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-governed-root-replay-exclusion.md",
    "scripts/governed_root_replay_exclusion_contract_common.py",
    "scripts/validate_governed_root_replay_exclusion_contract.py",
    "scripts/ci/run_governed_root_replay_exclusion_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize recursive governed-root replay fail-close only",
    "fail-close paths shaped like repo/.tmp/identity-runtime/... when governed roots are re-materialized inside governed scratch",
    "freeze live_runtime_exclusion boundary where required by this contract",
    "guard cleanup may delete only machine-admitted stale residue, never live runtime by heuristic overreach"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_governed_root_replay_exclusion_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_governed_root_replay_exclusion_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-041C only"
}
```

Interpretation:
- nested governed-root replay inside governed scratch fails admission rather than being heuristically tolerated;
- guard cleanup may remove only machine-admitted stale residue and may not overreach into live runtime;
- live-runtime exclusion must stay visible wherever governed-root replay exclusion is reviewed.
