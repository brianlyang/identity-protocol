# Identity Result-Only Progress Accounting Governance v1.6.x

Minimal governance skeleton for ISSUE-042A result-only progress accounting.

No durable repo write means no progress claim.
Durable repo write status, durable repo output scope, progress claim admission status, narrative effort exclusion status, time spent exclusion status, repo rescan exclusion status, and explanation depth exclusion status are required progress-accounting fields.
Narrative effort, time spent, repo rescans, and explanation depth must fail-close as progress evidence when durable repo output is missing.
Durable repo output must remain machine-visible wherever result-only progress accounting is evaluated.
Progress claims without durable repo output are not admitted.

Required machine-visible result-only progress accounting fields:
- durable_repo_write_status
- durable_repo_output_scope
- progress_claim_admission_status
- narrative_effort_exclusion_status
- time_spent_exclusion_status
- repo_rescan_exclusion_status
- explanation_depth_exclusion_status

```json
{
  "lane_id": "issue_042a_result_only_progress_accounting_contract_v1",
  "governing_law": "not_written_not_progressed",
  "fixed_write_set": [
    "docs/governance/identity-result-only-progress-accounting-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-result-only-progress-accounting.md",
    "scripts/result_only_progress_accounting_contract_common.py",
    "scripts/validate_result_only_progress_accounting_contract.py",
    "scripts/ci/run_result_only_progress_accounting_probes_ci.sh"
  ],
  "layer_state": "protocol-base-repo",
  "next_exact_action": [
    "formalize result-only progress accounting only",
    "freeze the rule that no durable repo write means no progress claim",
    "fail-close narrative effort, time spent, repo rescans, or explanation depth as progress without durable repo output"
  ],
  "validation_bundle": [
    "TMPDIR=$PWD/.tmp python3 scripts/validate_result_only_progress_accounting_contract.py --json-only",
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_result_only_progress_accounting_probes_ci.sh"
  ],
  "reopen_triggers": [
    "validator/probe fail",
    "same-file same-line conflict",
    "fixed_write_set insufficiency only"
  ],
  "commit_gate": "one isolated commit for ISSUE-042A only"
}
```
