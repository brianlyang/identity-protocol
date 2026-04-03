# identity execution-loop-after-mutation-not-closing governance (`v1.6.x`)

## Governing law

Once any post-mutation closeout trigger has materialized, the lane is no longer admitted to
re-open reading or reassurance work.

The trigger is satisfied when at least one of the following is true:

- `mutation_phase_entry_status=ENTERED`
- staged paths are already present
- validator / probe / targeted-regression evidence already exists

After that point, `allowed_next_actions` must collapse exactly to:

1. `run_validator`
2. `run_probe`
3. `stage_and_commit`
4. `emit_blocker_receipt`
5. `emit_fail_close_token`

The following actions are not admitted after post-mutation closeout begins:

- `reread`
- `recap`
- `re-anchor`
- `whole-family reinspection`
- `reassurance browsing`

Any admitted surface that observes one of those forbidden actions after the trigger must
fail-close as:

- `execution_loop_after_mutation_not_closing`

## Canonical machine contract

The phase-1 core contract is carried by:

- `scripts/execution_loop_after_mutation_not_closing_contract_common.py`
- `scripts/validate_execution_loop_after_mutation_not_closing.py`
- `scripts/ci/run_execution_loop_after_mutation_not_closing_probes_ci.sh`

Required machine-visible fields:

- `candidate_id`
- `governing_law`
- `mutation_phase_entry_status`
- `staged_paths_status`
- `validation_evidence_status`
- `allowed_next_actions`
- `forbidden_post_mutation_actions`
- `fail_close_reason`

Canonical candidate id:

- `execution_loop_after_mutation_not_closing_candidate`

Canonical fail-close reason:

- `execution_loop_after_mutation_not_closing`

## Fixed write set and isolation rule

Phase-1 is restricted to the following five paths only:

- `docs/governance/identity-execution-loop-after-mutation-not-closing-governance-v1.6.x.md`
- `docs/review/protocol-remediation-audit-ledger-v1.6.x-execution-loop-after-mutation-not-closing.md`
- `scripts/execution_loop_after_mutation_not_closing_contract_common.py`
- `scripts/validate_execution_loop_after_mutation_not_closing.py`
- `scripts/ci/run_execution_loop_after_mutation_not_closing_probes_ci.sh`

This candidate is independent root infra. It must not absorb:

- `protocol_lane_headstamp_continuity`
- ISSUE-043
- ISSUE-044
- ISSUE-045
- ISSUE-046
- workbook / register phase-2 residuals

## Commit gate

The phase-1 commit is admitted only when:

- staged paths are exactly the phase-1 fixed write set
- validator returns `PASS_REQUIRED`
- probe returns `PASS_REQUIRED`
- targeted regression returns `PASS_REQUIRED`
- the commit is isolated and single-lane
