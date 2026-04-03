# Identity Control Plane MVP

This file is admitted at protocol root only as clearly demoted support material.
It is not a protocol-root constitution, not a root contract, and not active-runtime truth outside the machine-bound control-plane lane it documents.

contract_id: `control_plane_role_binding_overlay_hardening`  
classification: `existing_surface_alignment`

## Scope

This package closes the control-plane hardening that separates canonical role law
from repo-local concrete owner binding.
The active machine-authoritative lane is now
`control_plane_role_binding_overlay_hardening`.

admitted_delta_only:

- canonical_role_law_owner_binding_overlay_split_only
- owner_binding_overlay_current_and_versioned_surface_only
- route_next_role_semantics_identity_resolution_split_only
- historical_control_plane_lane_compatibility_probe_only
- canonical_registry_deconcretizes_role_bindings_only
- no_reopen_of_control_plane_protocol_feedback_instance_state_runner_hardening

## Runtime-evidence-only + fail-close standard

The control plane MUST machine-enforce the following invariant:
**canonical protocol truth must remain role-level, portable, and free of concrete runtime bindings**.
Canonical truth may define roles, contracts, admission rules, state transitions, and receipt semantics,
but it MUST NOT embed, freeze, inherit, or derive authority from any concrete identity, session,
transaction, checkout-instance, host-path, or other runtime-specific literal.

Concrete runtime bindings are admitted only within explicitly marked runtime-evidence surfaces.
Those surfaces are non-canonical, non-portable, and receipt-scoped.
Any reentry, projection, copy-through, normalization, or dependency of those concrete runtime literals
back into canonical truth is a protocol violation and MUST fail-close before render success,
ingest success, validation success, probe success, staging success, commit success, or terminal success receipt.

## Exact success target

A success receipt is admissible only when all of the following are machine-true:

1. the command is executed from the authoritative checkout root;
2. the active registry pointer resolves to the versioned registry in the same package;
3. the active lane is exactly `control_plane_role_binding_overlay_hardening`;
4. canonical role law remains in the lane registry, while concrete owner binding is admitted only through `owner_binding_runtime_evidence` surfaces:
   - `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`
5. canonical registry no longer persists `role_bindings` at the top level or inside lane rows;
6. `route_next_role` and `route_next_role_semantics` remain role-only and portable; the returned binding surface is metadata-only and explicitly marked `DEFERRED_TO_RUNTIME_EVIDENCE`;
7. the historical lanes `control_plane_lane_registration_transaction_only` and `control_plane_protocol_feedback_instance_state_runner_hardening` remain machine-readable without reintroducing concrete `identity_id` into canonical success paths;
8. the structured receipt stages exactly the machine-authoritative closeout subset for this package;
9. the validator result is exactly `PASS_REQUIRED`;
10. the probe result is exactly `PASS`;
11. the reported commit id resolves in the authoritative checkout before terminal success.

## Canonical role law vs runtime evidence

Canonical control-plane truth now carries role semantics only:

- `status -> next_role`
- `writer_role`
- `read_only_roles`
- `execution_mode`
- `scope_lock_allowed_actions`

Concrete owner resolution is no longer frozen into canonical lane truth.
Instead, repo-local owner binding is materialized only through the owner-binding runtime-evidence surfaces:

route_next_role now emits role-level projections plus a runtime-evidence binding surface only.

- `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`

Those surfaces are explicitly non-portable and metadata-only:

- `truth_class = owner_binding_overlay`
- `scope = repo_local`
- `portable = false`
- `runtime_evidence_surface = true`
- `runtime_evidence_class = concrete_identity_binding`
- `binding_policy = receipt_scoped_runtime_evidence_only`
- `canonical_reentry_policy = fail_close`

Helper validators and probes do not freeze exact concrete identity literals.
They validate required role coverage, admitted runtime-evidence roots, and fail-close reentry policy.
They do not derive or assert `identity_id` from canonical/versioned surfaces.

## Authoritative checkout binding

The package binds execution to the local checkout through file-anchored surfaces:

- `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
- `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
- `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`
- the control-plane scripts co-located in this repository root

The validator and probes therefore treat the current working directory as admissible only
when it equals the repository root resolved from the script location and the Git top-level.
A divergent execution workspace must fail-close before success receipt ingestion.

Machine-exact binding token:

- `cwd_must_equal_repo_root`

## Canonical runtime tuple pollution policy

Reusable command templates and canonical execution truth must not carry concrete runtime
tuple literals. The following are forbidden in this package:

- a concrete `session_id`
- a concrete `run:*` token
- a concrete `actor_id` embedded in reusable execution templates
- a concrete executor identity embedded in canonical runtime-resolved command templates
- concrete subagent, collaborator, or outer delivery bindings embedded in canonical truth

Allowed literal exception surfaces remain bounded to:

- `runtime_evidence_surfaces`
- actor/session store
- runtime reports
- CI/probe fixtures
- docs/examples

## Protocol-governed sidecar supplement

For long-chain repository governance, subagent orchestration is admitted as a useful sidecar capability,
but it is not canonical authority.
A subagent is treated as a governed sidecar infrastructure object.
In protocol terms, this is a subagent sidecar infrastructure object.
It must be distinguished from:

1. the **subagent** itself as sidecar infrastructure;
2. the **collaborator identity instance** that may operate within or alongside that sidecar;
3. the **outer delivery surface** that presents receipts, reviews, or handoff artifacts to users.

Canonical control-plane truth MUST NOT bind any of those three layers back into role law.
If a helper, validator, probe, or receipt path attempts to make canonical truth depend on a concrete subagent,
a collaborator identity instance, or an outer delivery surface literal, the control plane must fail-close.

Current governance gap note: subagent usage is a net gain, but formal work contract, capability discovery,
closure receipt, integration receipt, and timeout/fail-close semantics still need explicit protocolization.
That gap is documented here as governance debt, not as permission to let subagent literals reenter canonical truth.

## Lane schema excerpt

The active lane for this package carries these machine-visible fields:

- `lane_id`
- `classification`
- `status`
- `execution_mode`
- `writer_role`
- `read_only_roles`
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

The canonical registry no longer persists `role_bindings`.
Concrete identity mapping is admitted only as runtime evidence and is never projected back into canonical truth.

## Execution mode

This package remains `split_roles` at the machine-contract layer:

- architect defines canonical role law
- executor performs mutation / validator / probe / commit
- auditor and office remain read-only post-closure roles

The user is not a relay surface for these roles.

## Historical lane compatibility

This hardening does not reopen already-closed control-plane lanes.
Instead it preserves historical lane rows while removing concrete owner bindings from
canonical registry truth:

- `control_plane_lane_registration_transaction_bootstrap`
- `control_plane_lane_registration_transaction_only`
- `control_plane_protocol_feedback_instance_state_runner_hardening`

Those rows remain route-compatible because canonical law still resolves the next role,
while concrete authority remains deferred to runtime evidence and therefore absent from canonical outputs.
Historical lanes remain route-compatible because their projections defer concrete binding to runtime evidence instead of persisting `identity_id`.
route_next_role now emits role-level projections plus a runtime-evidence binding surface only.
historical lanes remain route-compatible because their projections defer concrete binding to runtime evidence instead of persisting `identity_id`.

## Fixed write set

The machine-authoritative closeout subset for this package is:

1. `identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md`
2. `identity/protocol/mappings/control-plane-lane-registry.current.yaml`
3. `identity/protocol/mappings/control-plane-lane-registry.v1.yaml`
4. `identity/protocol/mappings/control-plane-owner-binding.current.yaml`
5. `identity/protocol/mappings/control-plane-owner-binding.v1.yaml`
6. `docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md`
7. `scripts/control_plane_lane_registry_common.py`
8. `scripts/control_plane_lane_render.py`
9. `scripts/control_plane_lane_next.py`
10. `scripts/control_plane_lane_ingest.py`
11. `scripts/control_plane_lane_stream_guard.py`
12. `scripts/validate_identity_control_plane_bootstrap_mvp.py`
13. `scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh`
14. `scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py`
15. `scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh`
16. `scripts/validate_control_plane_role_binding_overlay_hardening.py`
17. `scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh`

## Command templates

Validator command:

```bash
TMPDIR=$PWD/.tmp python3 scripts/validate_control_plane_role_binding_overlay_hardening.py --json-only
```

Probe command:

```bash
TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_role_binding_overlay_hardening_probes_ci.sh
```

These templates are intentionally runtime-generic and contain no concrete actor/session/subagent tuple.

## Fail-close contract

The machine fail-close token for this package is:

- `control_plane_role_binding_overlay_hardening_not_machine_authoritative`

Representative fail-close reasons include:

- current working directory is not the authoritative checkout root
- git top-level diverges from the authoritative checkout root
- canonical registry still persists `role_bindings`
- owner-binding runtime-evidence policy is missing or malformed
- helper / validator / probe paths reenter concrete identity or subagent literals into canonical truth
- staged paths escape the fixed write set or are not exact
- commit id does not resolve in the authoritative checkout
- canonical reusable templates contain forbidden concrete runtime tuple literals

## Post-success routing

After a successful closure receipt is ingested, the lane advances to:

- `status = closure_done`
- `next_role = auditor`
- `suggested_next_status = audit_ready`
