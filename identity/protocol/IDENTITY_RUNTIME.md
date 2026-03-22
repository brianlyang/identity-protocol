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

### rq_043_identity_instance_pack_topology_contract_v1

Required receipt fields:

- `instance_pack_topology_status`
- `pack_root_dir_lock_status`
- `runtime_dir_lock_status`
- `scripts_surface_status`
- `required_contract`
- `contract_key`
- `missing_required_file_rows`
- `missing_required_dir_rows`
- `unknown_dir_rows`
- `forbidden_dir_rows`
- `stale_reasons`
- `evidence_ref`

Hard semantics:

1. Governed identity packs must keep the canonical pack-root topology `agents/ + runtime/ + scripts/`; arbitrary additional root directories are not allowed without a later governed contract revision.
2. Pack-root `scripts/` is the canonical instance-owned executable source surface; `runtime/scripts/` is forbidden.
3. `runtime/` is reserved for runtime/autonomy/state/report/downsink surfaces and must not be repurposed as an executable source tree.
4. Generated cache directories such as `__pycache__` and `.pytest_cache` are forbidden inside governed pack topology.
5. Creator/bootstrap/update strict lanes must keep the topology contract and validator aligned; ad hoc instance-local topology keys are non-canonical.

### Canonical identity-Codex launcher execution boundary (v1.6.14 additive)

Hard semantics:

1. Identity-bound Codex launcher governance is a startup-entry concern and must not be implemented by overriding the product command `codex`.
2. Canonical installed launcher shims belong under `${CODEX_HOME}/bin/`:
   - `${CODEX_HOME}/bin/identity-codex`
   - `${CODEX_HOME}/bin/id-<identity-id>`
3. Canonical pack-local launcher assets belong under `<pack_path>/scripts/launchers/`; `runtime/` and `scripts/identity/` are non-canonical launcher homes.
4. Launcher-owned startup injection must preserve `v1.6.12` tuple/bootstrap truth and keep manual `model_instructions_file` / `project_doc_fallback_filenames` override attempts fail-closed.
5. Workspace bridge helpers under `scripts/codex_native_chat/` remain migration/evidence paths only until protocol-owned launcher render/install/validate assets land.

### Canonical identity-instance script orchestration boundary (v1.6.15 additive)

Hard semantics:

1. Governed route-to-script binding is a machine contract, not filename discovery or operator memory.
2. The canonical pack-local script catalog file is `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`, and every route-targetable `script_id` must resolve through it.
3. Canonical additive route fields are `primary_instance_scripts`, `fallback_instance_scripts`, `script_preconditions`, and `script_receipt_pattern` under `capability_orchestration_contract.task_type_routes.<route>`.
4. A single route may bind multiple role-distinct `script_id` values when probe/render/emit/recovery responsibilities are intentionally separated.
5. `script_preconditions` constrains admission conditions such as identity lock, work/source layer, required contracts, and gate policies; it is not free-form prose.
6. `script_preconditions` may reference inherited gateway/headstamp/host-visible/relay contracts when a route depends on them, but that does not transfer ownership of those contracts into `v1.6.15`.
7. Lower capability dependencies remain explicit through skills, MCP servers, and governed tool-route fields; instance scripts do not bypass those layers.
8. Route-scoped admission must be machine-evaluable against only that route's declared lower dependencies unless a stronger activation policy is explicitly selected.
9. Canonical receipt-family roles are route admission, execution, emit, and recovery, and those receipts remain runtime-owned artifacts rather than source files under `scripts/`.
10. Governed receipt families must preserve machine-readable route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`, including layered execution-then-emit receipt mapping.
11. If a governed route produces user-visible final text, that route must resolve to at least one pack-local emitter script and emit an `instance_script_emit_receipt`; direct free-form assistant text is non-canonical for that route.
12. Any manifest entry that resolves outside pack-root `scripts/` is non-canonical and falls back to `v1.6.13` topology enforcement.


### Canonical identity context continuity boundary (v1.6.16 additive)

Hard semantics:

1. Governed continuity is a machine-readable checkpoint and re-entry system, not raw transcript persistence and not operator memory.
2. Canonical continuity artifact roles are `rolling_checkpoint`, `stage_checkpoint`, `migration_checkpoint`, and `reentry_brief`.
3. Continuity artifacts remain derived continuity assets; they must not override `IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, active governance/review docs, workbook surfaces, or governed runtime receipts.
4. The default trigger policy is the named profile `default_turns_15_30_60`, with canonical forced trigger classes for clear/reset, compaction, launcher restart/recover, resume migration, major commit, major gate flip, lane switch, and root-cause turns.
5. Continuity producers remain pack-local executable surfaces under pack-root `scripts/`, inheriting `v1.6.13`; continuity outputs remain runtime-owned artifacts.
6. Canonical target runtime families are `runtime/reports/context-continuity/` and `runtime/state/context-continuity/`; packs may not claim adoption until those targets are registered through the relevant topology/path contracts.
7. `reentry_brief` is the canonical startup-consumable artifact; it must stay compact, structured, and bounded rather than becoming a long-history replay blob.
8. Resume thread UUIDs, actor-session tuple ids, and continuity ids are distinct identity classes and must not be semantically collapsed.
9. Continuity consumption under startup/resume/recover remains subordinate to `v1.6.12` tuple/bootstrap truth and `v1.6.14` launcher ownership.
10. Optional transcript excerpts remain evidence-only supplements; they are never the authority source for continuity.
