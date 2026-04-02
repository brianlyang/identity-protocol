# identity-shared-primitive-adoption-ci-isolation-governance-v1.6.x

- lane_id: `shared_primitive_adoption_ci_isolation_residual`
- governing_law: `shared_primitive_adoption_ci_must_be_isolated_from_preexisting_dirty_state_and_nonlane_context`
- layer_state: `protocol-base-repo`

## fixed_write_set

- `scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh`
- `docs/governance/identity-shared-primitive-adoption-ci-isolation-governance-v1.6.x.md`
- `docs/review/protocol-remediation-audit-ledger-v1.6.x-shared-primitive-adoption-ci-isolation.md`
- `scripts/shared_primitive_adoption_ci_isolation_common.py`
- `scripts/validate_shared_primitive_adoption_ci_isolation.py`

## machine contract

- shared primitive adoption CI must be isolated from pre-existing dirty/untracked state and nonlane context.
- lane evidence must be computed from the fixed_write_set only.
- the shared `protocol_root_probe_shadow_common.sh` bootstrap helper is admitted when it is consumed as a fixed-write-set implementation primitive rather than as ambient wildcard scope.
- ambient root-family wildcard expansion is not admitted.
- fail-close when CI admission depends on unrelated pre-existing state or ambient repo context.
- compatibility with broader root probe families is not a truth source for this residual lane.
