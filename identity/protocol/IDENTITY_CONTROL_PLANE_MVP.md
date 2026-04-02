# Identity Control Plane MVP

contract_id: `control_plane_protocol_feedback_instance_state_runner_hardening`  
classification: `existing_surface_alignment`

## Scope

This package hardens the machine-authoritative normal execution contract for
`control_plane_protocol_feedback_instance_state_runner_hardening` inside the authoritative checkout.
It upgrades the target lane from registration-only metadata to a full executable control-plane lane
without reopening `control_plane_lane_registration_transaction_only`.

admitted_delta_only:

- protocol_feedback_instance_state_runner_contract_only
- protocol_feedback_validator_probe_surface_reuse_only
- no_absolute_host_path_literals_in_target_executable_surfaces
- no_reopen_of_control_plane_lane_registration_transaction_only

## Exact success target

A success receipt is admissible only when all of the following are machine-true:

1. the command is executed from the authoritative checkout root;
2. the active registry pointer resolves to the versioned registry in the same package;
3. the active lane is exactly `control_plane_protocol_feedback_instance_state_runner_hardening`;
4. the target lane row carries a full executable contract, including `execution_mode`, `role_bindings`, `exact_fixed_write_set`, `read_only_input_surfaces`, `validator_command`, `probe_command`, `validator_expected_status`, `probe_expected_status`, `admitted_delta_only`, `fail_close_token`, and `receipt_schema_version`;
5. the target executable script surfaces remain free of forbidden reusable absolute host-path literals such as `/Users/yangxi/...`;
6. `bash scripts/ci/run_protocol_feedback_sidecar_contract_probes_ci.sh` exits successfully;
7. `bash scripts/ci/run_protocol_feedback_ssot_archival_probes_ci.sh` exits successfully;
8. `bash scripts/ci/run_sidecar_cwd_parity_probes_ci.sh` exits successfully;
9. `python3 scripts/validate_identity_state_consistency.py --catalog ../.agents/identity/catalog.local.yaml` exits successfully;
10. the structured receipt stages exactly the fixed write set for this package;
11. the validator result is exactly `PASS_REQUIRED`;
12. the probe result is exactly `PASS`;
13. the reported commit id resolves in the authoritative checkout before terminal success.

## CWD / path-risk adjudication

Allowed repo-root execution bindings remain in scope for this lane:

- `cwd_must_equal_repo_root`
- `TMPDIR=$PWD/.tmp`

These bindings are lane-local execution controls, not reusable-host-path pollution.

Forbidden reusable absolute host-path literals remain out of scope for this lane unless they appear inside the target executable script surfaces:

- `/Users/yangxi/...`

Current adjudication for this lane: the target executable script surfaces are free of forbidden reusable absolute host-path literals, so absolute-host-path cleanup remains a separate remediation track rather than a prerequisite blocker for this lane.

Representative target executable surfaces for this adjudication include:

- `scripts/validate_protocol_feedback_sidecar_contract.py`
- `scripts/ci/run_protocol_feedback_sidecar_contract_probes_ci.sh`
- `scripts/ci/run_protocol_feedback_ssot_archival_probes_ci.sh`
- `scripts/ci/run_sidecar_cwd_parity_probes_ci.sh`
- `scripts/validate_identity_state_consistency.py`

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

This package remains `split_roles` at the machine-contract layer:

- architect authors the authoritative package
- executor performs mutation / validator / probe / commit
- auditor and office remain read-only roles after closure

The user is not a relay surface for these roles.

## Fixed write set

The closure executor may mutate only the following files:

1. `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
2. `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
3. `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
4. `scripts/control_plane_lane_registry_common.py`
5. `scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py`
6. `scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh`

## Command templates

Validator command:

```bash
TMPDIR=$PWD/.tmp python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only
```

Probe command:

```bash
TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh
```

These templates are intentionally runtime-generic and contain no concrete actor/session tuple.

## Fail-close contract

The machine fail-close token for this package is:

- `control_plane_protocol_feedback_instance_state_runner_hardening_execution_contract_not_machine_authoritative`

Representative fail-close reasons include:

- current working directory is not the authoritative checkout root
- git top-level diverges from the authoritative checkout root
- the target lane row does not carry a full executable contract
- target executable surfaces contain forbidden reusable absolute host-path literals
- staged paths escape the fixed write set or are not exact
- commit id does not resolve in the authoritative checkout
- canonical reusable templates contain forbidden concrete runtime tuple literals

## Post-success routing

After a successful closure receipt is ingested, the lane advances to:

- `status = closure_done`
- `next_role = auditor`
- `suggested_next_status = audit_ready`
