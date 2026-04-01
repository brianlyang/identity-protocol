# Identity Control Plane MVP

contract_id: `control_plane_authoritative_checkout_execution_workspace_binding_bootstrap`  
classification: `existing_surface_alignment`

## Scope

This bootstrap package narrows the control-plane MVP to one machine-checkable concern:
authoritative checkout and execution workspace binding for closure execution.

admitted_delta_only:

- control_plane_authoritative_checkout_execution_workspace_binding_only
- no reopen or writeback of ISSUE-040 / ISSUE-041 / ISSUE-042 / ISSUE-043 / ISSUE-044 / ISSUE-045 / ISSUE-046 / ISSUE-047 / ISSUE-048
- no registration-transaction bootstrap
- no protocol_feedback / instance_feedback / archival / reply-channel strengthening
- no broader roadmap, operator projection, or human-only routing

## Exact success target

A success receipt is admissible only when all of the following are machine-true:

1. the command is executed from the authoritative checkout root;
2. the active registry pointer resolves to the versioned registry in the same package;
3. the structured receipt stages exactly the fixed write set for this bootstrap;
4. the validator result is exactly `PASS_REQUIRED`;
5. the probe result is exactly `PASS`;
6. the reported commit id resolves in the authoritative checkout before terminal success.

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
tuple literals. The following are forbidden in this bootstrap package:

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

The active lane for this package carries these machine-visible fields:

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

- architect authors the authoritative package
- executor performs mutation / validator / probe / commit
- auditor and office remain read-only roles after closure

## Fixed write set

The closure executor may mutate only the following files:

1. `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
2. `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
3. `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
4. `scripts/control_plane_lane_registry_common.py`
5. `scripts/control_plane_lane_preflight.py`
6. `scripts/control_plane_lane_render.py`
7. `scripts/control_plane_lane_ingest.py`
8. `scripts/control_plane_lane_next.py`
9. `scripts/control_plane_lane_stream_guard.py`
10. `scripts/validate_identity_control_plane_bootstrap_mvp.py`
11. `scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh`

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

The machine fail-close token for this bootstrap package is:

- `control_plane_authoritative_checkout_execution_workspace_binding_not_machine_authoritative`

Representative fail-close reasons include:

- current working directory is not the authoritative checkout root
- git top-level diverges from the authoritative checkout root
- staged paths escape the fixed write set or are not exact
- commit id does not resolve in the authoritative checkout
- canonical reusable templates contain forbidden concrete runtime tuple literals

## Post-success routing

After a successful closure receipt is ingested, the lane advances to:

- `status = closure_done`
- `next_role = auditor`
- `suggested_next_status = audit_ready`
