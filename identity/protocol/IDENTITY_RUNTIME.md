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
3. Read active identity from `identity/catalog/identities.yaml` (`default_identity` or override).
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
