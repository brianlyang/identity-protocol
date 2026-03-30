# Protocol remediation audit ledger v1.6.x - scope-locked mutation-phase runtime enforcement

## Status

- ISSUE-046-candidate
- REVIEW_READY_ON_VALIDATOR_AND_PROBE_PASS

## Why ISSUE-046 exists

The unresolved gap is not segmented-lane law selection; it is the live runtime actuator and reply-envelope gate after `scope_lock_status=LOCKED` and `fixed_write_set_lock_status=LOCKED`. Once lock is declared, the runtime must stop admitting reread, reanchor, repeated plan restatement, compaction without progress, or tool use outside the locked write set.

## Distinction vs ISSUE-045

- ISSUE-045 forbids repeated pre-mutation planning, re-anchoring, and compaction loops before mutation progress.
- ISSUE-046 adds post-lock runtime actuator enforcement and reply-envelope gating.
- ISSUE-046 is materialization only and does not reopen ISSUE-045, does not touch workbook/register, and does not mix ISSUE-044 adoption.

## Accepted remediation judgment

Accepted candidate judgment: once scope and fixed write set are both locked, `allowed_next_actions` collapse exactly to:

- `mutate_fixed_write_set`
- `run_validator`
- `run_probe`
- `stage_and_commit`
- `emit_blocker_receipt`
- `emit_fail_close_token`

Everything else is not admitted. That includes reply-envelope output that is not a mutation receipt, validation receipt, probe receipt, blocker receipt, or single-token fail-close.

## Audit consequence

The contract is only satisfied if machine-visible state preserves:

- `current_execution_phase`
- `scope_lock_status`
- `fixed_write_set_lock_status`
- `pre_mutation_turn_count`
- `pre_mutation_tool_count`
- `mutation_phase_entry_status`
- `last_mutation_receipt_turn`
- `allowed_next_actions`
- `reply_envelope_status`
- `runtime_guard_status`
- `forced_fail_close_reason`
- `planning_budget_status`
- `repeated_plan_restatement_status`
- `repeated_reanchor_status`
- `repeated_compaction_without_progress_status`
- `execution_loop_status`
- `stale_reasons`

And fail-close reason family preserves:

- `execution_loop_not_entering_mutation_phase`
- `scope_locked_reread_not_admitted`
- `scope_locked_reanchor_not_admitted`
- `scope_locked_plan_restatement_not_admitted`
- `reply_envelope_not_admitted`
- `tool_use_outside_fixed_write_set_after_lock`
- `pre_mutation_budget_exhausted`
- `mutation_required_but_not_entered`

## Canonical lane payload

```json
{
  "issue_id_or_candidate_id": "ISSUE-046-candidate",
  "lane_id": "scope_locked_mutation_phase_runtime_enforcement_contract_v1",
  "validator_command": "TMPDIR=$PWD/.tmp python3 scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py --json-only",
  "probe_command": "TMPDIR=$PWD/.tmp bash scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh",
  "fixed_write_set": [
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md",
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py",
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py",
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh"
  ],
  "allowed_next_actions": [
    "mutate_fixed_write_set",
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token"
  ],
  "reply_envelope_rule": "after fail-close triggers, only mutation receipt, validation receipt, probe receipt, blocker receipt, or single-token fail-close are admitted"
}
```

## Review closing note

If validator/probe drift appears on `allowed_next_actions`, required machine fields disappear, reply-envelope gate is not enforced, fixed write set changes, or the candidate id collides with an already admitted lane, the lane must reopen.
