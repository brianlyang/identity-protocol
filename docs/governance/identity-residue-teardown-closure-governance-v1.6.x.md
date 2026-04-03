# Identity Residue Teardown Closure Governance v1.6.x

Minimal governance skeleton for ISSUE-041A residue teardown closure.

Closure is incomplete if residue teardown receipt is missing.
Residue teardown must remain machine-visible at closure time.
Residue teardown status, owner, scope, removed bytes, and live runtime exclusion status are required closure fields.
Closure cannot be admitted when teardown receipt is missing.
Fail-close applies whenever residue teardown cannot be proven.

Required machine-visible closure fields:
- residue_teardown_status
- residue_teardown_owner
- residue_teardown_scope
- residue_teardown_removed_bytes
- live_runtime_exclusion_status

```json
{
  "lane_id": "issue_041a_residue_teardown_closure_contract_v1",
  "governing_law": "closure_incomplete_if_residue_teardown_missing",
  "fixed_write_set": [
    "docs/governance/identity-residue-teardown-closure-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-residue-teardown-closure.md",
    "scripts/residue_teardown_closure_contract_common.py",
    "scripts/validate_residue_teardown_closure_contract.py",
    "scripts/ci/run_residue_teardown_closure_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize residue_teardown_closure_contract_v1 only",
    "freeze machine-visible teardown fields:\n  residue_teardown_status\n  residue_teardown_owner\n  residue_teardown_scope\n  residue_teardown_removed_bytes\n  live_runtime_exclusion_status",
    "closure must fail-close when teardown receipt is missing"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_residue_teardown_closure_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_residue_teardown_closure_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-041A only"
}
```

Interpretation:
- closure requires a residue teardown receipt before admission;
- teardown evidence must stay durable and machine-visible at closure time;
- freeform completion claims cannot bypass missing teardown evidence.
