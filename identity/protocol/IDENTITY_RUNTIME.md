# Identity Runtime Integration

## Integration objective

Make identity runtime behavior explicit while staying compatible with current Codex capabilities.

## Native vs extension boundary

Native Codex features:
- skill discovery and invocation
- MCP server configuration
- AGENTS instruction chain loading

Project extension features:
- identity catalog parsing
- identity pack validation
- runtime state and compile steps

## Startup sequence

1. Read `.codex/config.toml`.
2. Resolve `model_instructions_file` relative to `.codex/config.toml` directory.
   - Consumer workspace (protocol repo checked out as `<workspace>/identity-protocol-local`):
     `../identity-protocol-local/identity/runtime/IDENTITY_COMPILED.md`
   - Legacy mirror example: `../identity/runtime/IDENTITY_COMPILED.md` (only if that bridge file is maintained).
3. Resolve runtime catalog via `runtime_catalog_resolution_contract_v1` (strict):
   - runtime lane default source: `${IDENTITY_CATALOG}` when set;
   - otherwise project-local `${IDENTITY_HOME}/catalog.local.yaml` when present;
   - repo fixture `identity/catalog/identities.yaml` is metadata-only and must not be used as runtime status source.
4. Validate identity pack exists and required files are present.
5. Validate CURRENT_TASK minimum required blocks.
6. Validate baseline-review evidence if `protocol_baseline_review_gate` is `required`.
7. Validate identity update lifecycle contract if `identity_update_gate` is `required`.
8. Validate collaboration trigger contract if `collaboration_trigger_gate` is `required`.
9. Allow execution.

If validation fails, block high-impact actions and require repair.

## Compile artifact

`identity/runtime/IDENTITY_COMPILED.md` is a compact runtime brief containing:
- active identity metadata
- hard guardrails summary
- current objective and state
- allowed skills and MCP dependencies

## Execution guard checks

Before high-impact actions (listing/relisting/repricing):
- guardrails present
- reject-memory gate present
- payload evidence path present

Before identity-level capability upgrade conclusions:
- protocol baseline review gate must pass
- review evidence must include mandatory sources and decision trace

Before identity runtime evolution/update conclusions:
- identity update lifecycle gate must pass
- update trigger/patch/validation/replay contracts must all pass

Before any flow that can hit login/captcha/session/manual verification blockers:
- collaboration_trigger_gate must pass
- blocker taxonomy must include required collaboration blocker classes
- immediate notification + dedupe + receipt constraints must be active

## Post-action requirements

After each high-impact action:
- update CURRENT_TASK state
- append TASK_HISTORY entry
- persist evidence artifact paths

## Batch-6 anchor placeholders (v1.6 intake, non-promotional)

The following sections provide stable kernel anchors for v1.6 Batch-6 mapping rows.
Execution closure remains governed by v1.6 governance/review and must stay
`SPEC_READY / PENDING_INTAKE` until validator + replay closure is complete.

### rq_018_dedup_monotonic_winner_contract_v1

Required receipt fields:

- `run_id`
- `earliest_claim_ts`
- `stable_tiebreaker`
- `winner_id`
- `winner_reason`
- `monotonicity_status`

### rq_019_cross_workflow_evidence_schema_contract_v1

Required receipt fields:

- `run_id`
- `route_action`
- `quality_meta_state`
- `dedup_state`
- `evidence_hash`
- `schema_version`

### rq_020_skill_path_integrity_contract_v1

Required receipt fields:

- `active_repo_root`
- `active_runtime_root`
- `layout_mode`
- `path_integrity_status`
- `path_integrity_error_code`

Recommended determinism field:

- `active_repo_root_resolution_source`

Hard semantics:

1. Strict operations must not silently rely on ambiguous cwd fallback for `active_repo_root`.
2. When `active_repo_root` cannot be derived from catalog/pack context and falls back to cwd in strict mode, fail-close must use dedicated family `IP-SPATH-005`.

### rq_021_route_workflow_version_pinning_contract_v1

Required receipt fields:

- `route_endpoint`
- `workflow_id`
- `workflow_publish_version`
- `pin_proof_ref`
- `pin_status`
- `pin_error_code`

### rq_033_execution_target_tuple_isolation_contract_v1

Required receipt fields:

- `execution_target_tuple_isolation_status`
- `execution_target_kind`
- `execution_target_key`
- `execution_target_ref`
- `route_conflict_status`
- `route_conflict_error_code`
- `conflict_key_mode`
- `override_non_bypass_status`
- `process_call_support_status`
- `evidence_ref`

Hard semantics:

1. Conflict keying must be tuple-first (`execution_target_kind + execution_target_key`) and must not silently downgrade to `codex_home`-only mode.
2. Explicit override paths (`session_id`/`codex_home`/direct tuple overrides) are governed by the same conflict gate and cannot bypass fail-close.
3. `process_call` targets are valid without mandatory `codex_home`, but receipt tuple fields must be complete and deterministic.
4. Reserved fail-close family:
   - `IP-XTARGET-001`
   - `IP-XTARGET-002`
   - `IP-XTARGET-003`
   - `IP-XTARGET-004`

### rq_039_skill_installation_supply_chain_contract_v1

Required receipt fields:

- `skill_installation_supply_chain_status`
- `dependent_contract_keys`
- `missing_dependent_contract_keys`
- `required_capability_drivers`
- `missing_capability_drivers`
- `skill_path_integrity`
- `stale_reasons`
- `evidence_ref`

Hard semantics:

1. Skill installation governance is not a parallel protocol; it is an artifact subtype under tool/vendor installation governance.
2. Strict lane execution must validate dependent contracts (`tool_installation`, `vendor_api_discovery`, `vendor_api_solution`, `skill_path_integrity`) before claiming supply-chain closure.
3. Missing capability-driver validators in strict lane are fail-close (`IP-SSUP-002`).

### rq_040_skill_frontmatter_contract_v1

Required receipt fields:

- `skill_frontmatter_status`
- `required_frontmatter_fields`
- `frontmatter_rows`
- `missing_frontmatter_skills`
- `missing_required_field_rows`
- `stale_reasons`
- `evidence_ref`

Hard semantics:

1. In strict lane, required skills must expose structured SKILL frontmatter with required fields (`skill_id`, `version`, `owner`, `source`) unless contract explicitly relaxes.
2. Frontmatter validation depends on `rq_020` path integrity and inherits fail-close boundary from the same identity tuple.
3. Missing/invalid frontmatter must fail-close with dedicated family `IP-SFRONT-*` and cannot degrade to non-blocking warning.

### rq_041_skill_sync_drift_guard_contract_v1

Required receipt fields:

- `skill_sync_drift_guard_status`
- `required_skills`
- `drift_roots`
- `skill_sync_rows`
- `drift_skills`
- `missing_skills`
- `stale_reasons`
- `evidence_ref`

Hard semantics:

1. Skill sync drift is hash-based (`sha256`) by default and evaluates multi-root replicas (`workspace`, `runtime`, `codex_home`) as one governed tuple.
2. Drift detection must distinguish “missing” vs “content divergence” and preserve machine-readable error families (`IP-SDRIFT-*`).
3. Strict lane cannot claim pass when required skill artifacts diverge across roots.

### rq_042_agent_relay_final_answer_contract_v1

Required receipt fields:

- `relay_surface`
- `relay_mode`
- `target_identity_id`
- `question_tag`
- `source_artifact`
- `source_snapshot_ts`
- `relay_text`
- `delivery_authority`
- `agent_relay_final_answer_status`
- `stale_reasons`

Hard semantics:

1. When an outer agent delivers an identity instance final answer to the user, the delivery surface must be `agent_relay_final_answer`; free-form outer replies cannot impersonate governed instance output.
2. `relay_mode=exact` is the only mode allowed to carry governed headstamp or canonical final-answer text, and the delivered text must byte-match the governed source artifact.
3. `relay_mode=summary` must classify as `ungoverned_operator_summary` and must not begin with governed-output prefixes such as `Identity-Context:`, `Display-Headstamp:`, or `Machine-Verification:`.
4. Relay receipts must stay anchored to a governed source artifact (`leader_snapshot`, `final_report`, or canonical plain-text final answer) with matching `target_identity_id` and `source_snapshot_ts`; mismatches are fail-close.
5. Instances must reuse the shared protocol builder/validator toolchain for `agent_relay_final_answer`; local receipt-construction logic is non-authoritative and must stay thin.
