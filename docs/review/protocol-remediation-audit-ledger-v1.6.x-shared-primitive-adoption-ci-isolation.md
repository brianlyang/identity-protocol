# protocol-remediation-audit-ledger-v1.6.x-shared-primitive-adoption-ci-isolation

- lane_id: `shared_primitive_adoption_ci_isolation_residual`
- governing_law: `shared_primitive_adoption_ci_must_be_isolated_from_preexisting_dirty_state_and_nonlane_context`
- commit_gate: `one isolated commit for this residual lane only`

## validation_bundle

- `TMPDIR=$PWD/.tmp python3 scripts/validate_shared_primitive_adoption_ci_isolation.py --json-only`
- `TMPDIR=$PWD/.tmp bash scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh`

## reopen_triggers

- `validator/probe fail`
- `same-file same-line conflict`
- `fixed_write_set insufficiency only`

## audit expectation

- the residual lane must not consume unrelated dirty-state evidence.
- the residual lane must not consume ambient wildcard root-family context.
- the shared `protocol_root_probe_shadow_common.sh` helper is admissible only as a fixed-write-set implementation primitive and does not relax the nonlane-context boundary.
- stage and commit boundaries must remain equal to the fixed_write_set.
