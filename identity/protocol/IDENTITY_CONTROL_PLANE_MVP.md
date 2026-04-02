# Identity Control Plane MVP

contract_id: `control_plane_lane_registration_transaction_only`  
classification: `existing_surface_alignment`

## Scope

This package is registration-only. It narrows the control-plane MVP to one machine-checkable concern:
append `control_plane_protocol_feedback_instance_state_runner_hardening` into authoritative registry truth
without executing the target hardening lane itself.

admitted_delta_only:

- control_plane_protocol_feedback_instance_state_runner_hardening
- no target-lane hardening execution in this package
- no reopen or writeback of ISSUE-040 / ISSUE-041 / ISSUE-042 / ISSUE-043 / ISSUE-044 / ISSUE-045 / ISSUE-046 / ISSUE-047 / ISSUE-048
- no bootstrap-family reentry
- no broader roadmap, operator projection, or human-only routing

## Exact success target

A success receipt is admissible only when all of the following are machine-true:

1. the command is executed from the authoritative checkout root;
2. the active registry pointer resolves to the versioned registry in the same package;
3. the active registration-only lane is exactly `control_plane_lane_registration_transaction_only`;
4. `identity/protocol/mappings/control-plane-lane-registry.v1.yaml` contains a lane entry whose `lane_id` is exactly `control_plane_protocol_feedback_instance_state_runner_hardening`;
5. `python3 scripts/control_plane_lane_render.py --lane-id control_plane_protocol_feedback_instance_state_runner_hardening --json-only` returns `status = PASS_REQUIRED` rather than lane not found;
6. the structured receipt stages exactly the fixed write set for this package;
7. the validator result is exactly `PASS_REQUIRED`;
8. the probe result is exactly `PASS`;
9. the reported commit id resolves in the authoritative checkout before terminal success.

## Authoritative checkout binding

The package binds execution to the local checkout through file-anchored surfaces:

- `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
- the control-plane scripts co-located in this repository root

The validator and probes therefore treat the current working directory as admissible only
when it equals the repository root resolved from the script location and the Git top-level.
A divergent execution workspace must fail-close before success receipt ingestion.

## Canonical runtime tuple pollution policy

Reusable command templates and canonical execution truth must not carry concrete runtime
tuple literals. The following are forbidden in this package:

- a concrete `session_id`
- a concrete `run:*` token
- a concrete `actor_id` embedded in reusable execution templates
- a concrete executor identity embedded in runtime-resolved command templates

Allowed literal exception surfaces remain bounded to:

- `role_bindings`
- actor/session store
- runtime reports
- CI/probe fixtures
- docs/examples

## Lane schema excerpt

The active registration-only lane for this package carries these machine-visible fields:

- `lane_id`
- `classification`
- `status`
- `execution_mode`
- `role_bindings`
- `exact_fixed_write_set`
- `read_only_input_surfaces`
- `validator_command`
- `probe_command`
- `validator_expected_status`
- `probe_expected_status`
- `admitted_delta_only`
- `fail_close_token`
- `scope_lock_allowed_actions`
- `receipt_schema_version`

## Execution mode

This package remains `split_roles`:

- architect authors the authoritative registration-only package
- executor performs mutation / validator / probe / commit
- auditor and office remain read-only roles after closure

## Fixed write set

The closure executor may mutate only the following files:

1. `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
2. `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
3. `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
4. `scripts/control_plane_lane_registry_common.py`
5. `scripts/control_plane_lane_render.py`
6. `scripts/validate_identity_control_plane_bootstrap_mvp.py`
7. `scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh`

## Command templates

Validator command:

```bash
TMPDIR=$PWD/.tmp python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only
```

Probe command:

```bash
TMPDIR=$PWD/.tmp bash scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh
```

These templates are intentionally runtime-generic and contain no concrete actor/session tuple.

## Fail-close contract

The machine fail-close token for this registration-only package is:

- `control_plane_lane_registration_transaction_only_not_machine_authoritative`

Representative fail-close reasons include:

- current working directory is not the authoritative checkout root
- git top-level diverges from the authoritative checkout root
- the target hardening lane is not appended into the versioned registry
- staged paths escape the fixed write set or are not exact
- commit id does not resolve in the authoritative checkout
- canonical reusable templates contain forbidden concrete runtime tuple literals

## Post-success routing

After a successful closure receipt is ingested, the registration-only lane advances to:

- `status = closure_done`
- `next_role = auditor`
- `suggested_next_status = audit_ready`
