# Identity scope-locked mutation-phase runtime enforcement governance v1.6.x

## Status

- ISSUE-046-candidate
- ACTIVE_ROOT_INFRA_CANDIDATE
- sibling-anchor only against ISSUE-045 root-infra family filenames/structure

## Governing law

Once `scope_lock_status=LOCKED` and `fixed_write_set_lock_status=LOCKED`, `allowed_next_actions` collapse exactly to:

- `mutate_fixed_write_set`
- `run_validator`
- `run_probe`
- `stage_and_commit`
- `emit_blocker_receipt`
- `emit_fail_close_token`

All other actions are not admitted, including non-compliant reply-envelope output.

## Machine-visible state family

Required machine-visible fields:

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
- `stale_reasons`

Bridged guard fields:

- `planning_budget_status`
- `repeated_plan_restatement_status`
- `repeated_reanchor_status`
- `repeated_compaction_without_progress_status`
- `execution_loop_status`

Required fail-close reason family:

- `execution_loop_not_entering_mutation_phase`
- `scope_locked_reread_not_admitted`
- `scope_locked_reanchor_not_admitted`
- `scope_locked_plan_restatement_not_admitted`
- `reply_envelope_not_admitted`
- `tool_use_outside_fixed_write_set_after_lock`
- `pre_mutation_budget_exhausted`
- `mutation_required_but_not_entered`

## PASS / FAIL semantics

- `PASS_REQUIRED`: the canonical payload, machine state family, allowed-next-action collapse, runtime guard, and reply-envelope gate are all present and mutually aligned.
- `FAIL_REQUIRED`: if scope/write-set lock exists but runtime behavior or declared state still admits reread, reanchor, plan restatement, compaction without progress, tool use outside fixed write set, or reply-envelope drift.
- After fail-close triggers, the reply envelope is restricted to:
  - `mutation receipt`
  - `validation receipt`
  - `probe receipt`
  - `blocker receipt`
  - `single-token fail-close`

## Canonical lane payload

```json
{
  "issue_id_or_candidate_id": "ISSUE-046-candidate",
  "lane_id": "scope_locked_mutation_phase_runtime_enforcement_contract_v1",
  "governing_law": "once scope_lock_status=LOCKED and fixed_write_set_lock_status=LOCKED, allowed_next_actions collapse exactly to {mutate_fixed_write_set, run_validator, run_probe, stage_and_commit, emit_blocker_receipt, emit_fail_close_token}; all other actions are not admitted, including non-compliant reply-envelope output.",
  "unique_delta_vs_issue_045": "ISSUE-045 forbids repeated pre-mutation planning/reanchor/compaction loops; ISSUE-046 additionally enforces post-lock live runtime actuator control and reply-envelope gating after scope/write-set lock.",
  "fixed_write_set": [
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md",
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py",
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py",
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh"
  ],
  "validator_command": "TMPDIR=$PWD/.tmp python3 scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py --json-only",
  "probe_command": "TMPDIR=$PWD/.tmp bash scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh",
  "allowed_next_actions": [
    "mutate_fixed_write_set",
    "run_validator",
    "run_probe",
    "stage_and_commit",
    "emit_blocker_receipt",
    "emit_fail_close_token"
  ],
  "required_machine_fields": [
    "current_execution_phase",
    "scope_lock_status",
    "fixed_write_set_lock_status",
    "pre_mutation_turn_count",
    "pre_mutation_tool_count",
    "mutation_phase_entry_status",
    "last_mutation_receipt_turn",
    "allowed_next_actions",
    "reply_envelope_status",
    "runtime_guard_status",
    "forced_fail_close_reason",
    "planning_budget_status",
    "repeated_plan_restatement_status",
    "repeated_reanchor_status",
    "repeated_compaction_without_progress_status",
    "execution_loop_status",
    "stale_reasons"
  ],
  "fail_close_reason_family": [
    "execution_loop_not_entering_mutation_phase",
    "scope_locked_reread_not_admitted",
    "scope_locked_reanchor_not_admitted",
    "scope_locked_plan_restatement_not_admitted",
    "reply_envelope_not_admitted",
    "tool_use_outside_fixed_write_set_after_lock",
    "pre_mutation_budget_exhausted",
    "mutation_required_but_not_entered"
  ],
  "reopen_triggers": [
    "validator/probe drift on locked allowed_next_actions",
    "required machine fields/guard fields missing",
    "reply-envelope gate not enforced",
    "fixed_write_set changes",
    "candidate id collision with an already-admitted lane"
  ],
  "commit_gate": "single-lane single commit only if validator=PASS_REQUIRED, probe=PASS, and staged paths equal the 5-path fixed_write_set exactly"
}
```

## Closure effect

This law closes the live runtime gap left after scope lock by collapsing the actuator surface to mutation, validation, probe, commit, blocker receipt, or fail-close token only. It does not reopen ISSUE-045, does not touch workbook/register in this lane, and does not mix ISSUE-044 adoption.
