# protocol remediation audit ledger - execution-loop-after-mutation-not-closing (`v1.6.x`)

## Accepted candidate judgment

Accepted phase-1 candidate:

- `execution_loop_after_mutation_not_closing_candidate`

Accepted governing law:

- once `mutation_phase_entry_status=ENTERED`, staged paths exist, or validator / probe /
  targeted-regression evidence already exists, the lane must stop reopening read-oriented work
  and collapse immediately to `run_validator / run_probe / stage_and_commit /
  emit_blocker_receipt / emit_fail_close_token`
- `reread / recap / re-anchor / whole-family reinspection / reassurance browsing` are not
  admitted after that point
- any such post-mutation reopen attempt must fail-close as
  `execution_loop_after_mutation_not_closing`

## Phase-1 evidence surfaces

Canonical phase-1 surfaces:

- `docs/governance/identity-execution-loop-after-mutation-not-closing-governance-v1.6.x.md`
- `docs/review/protocol-remediation-audit-ledger-v1.6.x-execution-loop-after-mutation-not-closing.md`
- `scripts/execution_loop_after_mutation_not_closing_contract_common.py`
- `scripts/validate_execution_loop_after_mutation_not_closing.py`
- `scripts/ci/run_execution_loop_after_mutation_not_closing_probes_ci.sh`

Required machine fields:

- `candidate_id`
- `governing_law`
- `mutation_phase_entry_status`
- `staged_paths_status`
- `validation_evidence_status`
- `allowed_next_actions`
- `forbidden_post_mutation_actions`
- `fail_close_reason`
- `stale_reasons`

## Audit expectations

Validator command:

```bash
python3 scripts/validate_execution_loop_after_mutation_not_closing.py --json-only
```

Probe command:

```bash
TMPDIR=$PWD/.tmp bash scripts/ci/run_execution_loop_after_mutation_not_closing_probes_ci.sh
```

Targeted regression command:

```bash
TMPDIR=$PWD/.tmp python3 scripts/validate_execution_loop_after_mutation_not_closing.py --targeted-regression mutation_entered_closeout_only --json-only
```

Audit pass condition:

- validator = `PASS_REQUIRED`
- probe = `PASS_REQUIRED`
- targeted regression = `PASS_REQUIRED`
- staged paths equal the 5-file fixed write set exactly

## Reopen triggers

The candidate must reopen if any of the following appears:

- `allowed_next_actions` drift from the canonical closeout set
- post-mutation forbidden actions are admitted or not machine-visible
- fail-close reason drifts from `execution_loop_after_mutation_not_closing`
- any phase-1 change lands outside the 5-file fixed write set
- the candidate absorbs `protocol_lane_headstamp_continuity`, ISSUE-043, ISSUE-044,
  ISSUE-045, ISSUE-046, or any other blocker

## Closure verdict

Phase-1 closes only as isolated root infra core. Workbook/register updates are deferred to a
separate phase-2 after ISSUE-043 no longer occupies those shared files.
