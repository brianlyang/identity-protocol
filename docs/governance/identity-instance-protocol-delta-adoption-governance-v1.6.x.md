# Identity Instance Protocol Delta Adoption Governance v1.6.x

## ISSUE-044 narrow absorb lane

This governance surface materializes the narrow ISSUE-044 absorb lane for
`instance_protocol_delta_adoption_contract_v1`.

### absorbed protocol delta

- absorbed_law_id: `scope_locked_mutation_phase_runtime_enforcement_contract_v1`
- absorbed_protocol_delta_commit: `f616889`
- absorb_only_boundary: `runtime-enforcement semantics remain defined by the root infra law; this lane only requires consumer-facing adoption surfaces to recognize and adopt that law as a relevant protocol delta`

### governing requirement

Consumer-facing identity instances must treat
`scope_locked_mutation_phase_runtime_enforcement_contract_v1` as a relevant
protocol delta and must surface it as adopted when the consumer-facing
instance adoption surface claims current adoption.

### machine-visible adoption requirement

The consumer-facing adoption surface must keep the following machine-visible
truth aligned:

- `protocol_current_head`
- `protocol_current_head_short`
- `protocol_current_head_subject`
- `last_seen_protocol_commit`
- `last_adopted_protocol_commit`
- `capability_family_count`
- `capability_families`
- `relevant_protocol_delta_laws`
- `adopted_protocol_delta_laws`
- `scanned_commit_count`
- `relevant_unadopted_commit_count`
- `relevant_unadopted_commits`
- `protocol_delta_adoption_status`
- `protocol_delta_adoption_mode`
- `protocol_delta_state_written`
- `protocol_root`
- `policy_path`
- `fallback_path`
- `state_path`
- `stale_reasons`

### fail-close requirement

Validation must fail-close when the consumer-facing adoption surface does not
recognize `scope_locked_mutation_phase_runtime_enforcement_contract_v1` as a
relevant adopted protocol delta.

Required stale reason families include:

- `relevant_protocol_delta_pending_adoption`
- `protocol_authority_resolution_failed`
- `protocol_owner_surface_not_ready`
- `instance_local_adoption_markers_missing`
- `relevant_unadopted_protocol_commits:scope_locked_mutation_phase_runtime_enforcement_contract_v1`
- `runtime_guard_law_not_adopted:scope_locked_mutation_phase_runtime_enforcement_contract_v1`

### adoption / enforcement boundary

- `protocol_delta_adoption != runtime_enforcement_semantics`
- this lane absorbs the runtime guard law into consumer-facing adoption logic
- this lane does not redefine the runtime guard law itself
