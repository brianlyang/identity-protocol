# Identity Protocol v1.6.13 (draft)

## Normative source map (v1.6 stream execution)

This file is kept as protocol overview/baseline context.  
For active governance execution in v1.6 lanes, normative sources are:

1. Historical motherline baseline:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. Active stream registry (current-state routing SSOT):
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. Current review/audit baseline:
   - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
4. Global protocol handoff baseline:
   - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`

Governance rule:

1. Script updates under `scripts/` are implementation surfaces only.
2. Any P0/P1 contract change must first land in governance/review docs, then code/wiring/replay.
3. Script-only semantic changes without governance/review delta are non-compliant.

## Governance execution stack (how work is controlled)

1. **Contract layer** (`docs/governance/...v1.6.0.md` + active stream docs resolved by `stream-doc-registry.current.yaml`)
   - fields, enums, error-codes, fail-closed semantics, acceptance commands.
2. **Review layer** (`docs/review/...v1.6.md` + active stream review ledgers)
   - intake, replay verdict, non-merge stage status, residual risks.
3. **Implementation layer** (`scripts/*.py`, `scripts/*.sh`)
   - validators/writers/parsers and strict gate logic.
4. **Wiring layer** (creator/readiness/e2e/full-scan/three-plane/CI)
   - six-surface + required-gates wiring.
5. **Replay evidence layer** (reports + machine-readable payloads)
   - deterministic pass/fail with error-code families.

Status transitions are controlled by governance/review, not by script commit alone:
`SPEC_READY -> IMPL_READY -> GATE_READY -> VERIFIED -> DONE`.

## Goal

Define identity as a first-class control-plane protocol, parallel to skills and MCP.

- **Skills**: capability packaging and reusable procedures.
- **MCP**: tool transport and execution surface.
- **Identity**: role cognition, governance boundaries, decision loop, and learning closure.

This protocol is scenario-agnostic by design.

## Core ownership and escalation contract (v1.6.10 additive)

1. `identity protocol` is the shared contract and upgrade framework; it does **not** backstop instance-owned technical debt.
2. `identity instance` is an autonomous optimization unit and must absorb protocol upgrades, complete self-heal, and clear its own technical debt.
3. `instance_owned_technical_debt` includes missing instance-local skills/config/transport/install/replay hygiene and other local recovery obligations.
4. `instance_clean_proof` is required before any remaining issue may be escalated as `protocol_residual_issue`.
5. `No instance-clean proof, no protocol escalation.`
6. `protocol_residual_issue` means a shared contract / wiring / validator / CI / governance defect that still remains **after** `instance_clean_proof`.
7. Host/runtime entry gaps remain a separate boundary and must not be relabeled as either `instance_owned_technical_debt` or `protocol_residual_issue`.
8. Closed protocol layers must not be reopened by unresolved instance-owned technical debt.

## Layer contract

1. Canon layer (hard governance)
2. Identity prompt layer (role cognition + decision principles)
3. Runtime task layer (single source of truth state)

### Protocol-side prompt bootstrap source (v1.6 additive)

1. Runtime `IDENTITY_PROMPT.md` is a pack-level artifact and must remain under identity pack paths.
2. Protocol layer must not add same-name runtime artifact file `identity/protocol/IDENTITY_PROMPT.md`.
3. Prompt baseline source for protocol-side capability evolution is tracked in:
   - `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
4. Any update to the bootstrap source must close mapping + validator + replay chain before promotion-grade claims.

## Required identity pack files

For each identity id `<id>`:
- `identity/packs/<id>/IDENTITY_PROMPT.md`
- `identity/packs/<id>/CURRENT_TASK.json`
- `identity/packs/<id>/TASK_HISTORY.md`
- `identity/packs/<id>/META.yaml`
- `identity/packs/<id>/agents/identity.yaml`
- `identity/packs/<id>/scripts/README.md`

Compatibility note: legacy packs can stay in `identity/<id>/` if catalog `pack_path` points there.

### Canonical identity instance pack topology (v1.6.13 additive)

1. Governed identity packs must keep the canonical root topology: `agents/`, `runtime/`, `scripts/`.
2. Pack-root `scripts/` is the only canonical identity-instance executable source surface.
3. `runtime/` remains reserved for runtime/autonomy/state/report/downsink assets; `runtime/scripts/` is forbidden.
4. Instance-local helper automation belongs in the instance pack, not in a workspace-global shared patch directory.
5. Required validator: `scripts/validate_identity_instance_pack_topology.py`.
6. Directory drift is fail-close; unregistered additional directories are non-compliant until promoted by governance.

## Runtime source-of-truth boundary (v1.4.x hardening)

Identity runtime must distinguish demo fixtures from local runtime instances:

- **fixture/demo identity**: repository-local references for examples and protocol fixtures.
- **runtime identity**: local instance under `IDENTITY_HOME`, resolved from local catalog.

Runtime decisions (validate/activate/update/install/writeback) must use local runtime context.
Repository fixture files must not be treated as live runtime state.

### Scope resolution contract (v1.4.12 uplift)

Identity resolution must be deterministic and auditable across layered scopes:

1. CLI explicit parameters (`--catalog`, `--target-root`, `--scope`)
2. Environment/config (`IDENTITY_HOME`, `runtime-paths.env`)
3. Project runtime scope (`<project>/.identity`)
4. Global runtime scope (`${CODEX_HOME:-~/.codex}/.identity`)

Legacy labels/paths (`local`, `repo`, `env`, `auto`, `.agents/identity`, `~/.codex/.identity`) are migration metadata only and must not enter strict runtime gate semantics.

If one `identity_id` resolves to multiple pack paths across scopes, tooling MUST fail unless explicit arbitration (`--scope`) is provided.

Mandatory validator:
- `scripts/validate_identity_scope_resolution.py`
- `scripts/validate_identity_scope_isolation.py`
- `scripts/validate_identity_scope_persistence.py`

Operational remediation entrypoint:
- `python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog> [--apply]`

Health diagnostics contract (CI-gated):
- `python3 scripts/collect_identity_health_report.py --identity-id <id> --catalog <catalog> --out-dir <dir> --enforce-pass`
- `python3 scripts/validate_identity_health_contract.py --identity-id <id> --report-dir <dir> --require-pass`

Protocol requirement:
- Health report must include failed-check recommendations.
- Required-gates/release/e2e MUST run health collection + contract validation.

Permission-state contract (CI-gated):
- `scripts/validate_identity_permission_state.py`
- upgrade report MUST include:
  - `permission_state`
  - `permission_error_code`
  - `writeback_precheck`
- CI/release requires `writeback_status=WRITTEN`; deferred permission status is not release-pass eligible.

### Cross-actor isolation scope semantics (v1.6.8 additive)

`IP-ASB-203` enforcement must distinguish current-actor closure from global hygiene telemetry.

1. Canonical validator:
   - `scripts/validate_cross_actor_isolation.py`
2. Supported scope modes:
   - `catalog_all`: fail-close on any actor binding anomaly in catalog scope.
   - `actor_primary`: fail-close on current actor scope, keep non-target actor anomalies as warning telemetry.
   - `actor_only`: fail-close on current actor scope only.
3. Strict runtime orchestrators (full-scan/three-plane/readiness/e2e/ci) must pass:
   - `--actor-id <resolved_actor_id>`
   - `--scope-mode actor_primary`
4. Telemetry contract (machine-readable):
   - `cross_actor_isolation_status` remains blocking status for current actor scope.
   - `global_observation_status` + `global_observation_stale_reasons` expose non-target actor contamination.
5. Fail-close boundary:
   - current actor scope anomalies remain `FAIL_REQUIRED` (`IP-ASB-203`);
   - unrelated actor-file anomalies are visible warnings and must not hard-block current actor closure by default.

## Registry contract

`identity/catalog/identities.yaml` must include:
- id
- title
- description
- status
- methodology_version
- pack_path

`default_identity` must reference a valid id.

Optional metadata blocks per identity:
- `interface` (display_name, short_description, default_prompt)
- `policy` (allow_implicit_activation, activation_priority, conflict_resolution)
- `dependencies` (tool/env/network/filesystem requirements)
- `observability` (event_topics, required_artifacts)

See discovery draft: `identity/protocol/IDENTITY_DISCOVERY.md`.

### Identity-scoped evidence rule (mandatory)

For runtime identities, evidence/sample/log path patterns must be identity-scoped:

- path fields must include target `identity_id`
- cross-identity hits (including `store-manager` for non-store identities) are invalid
- global fallback to unrelated identity samples is forbidden

Mandatory validator:
- `scripts/validate_identity_instance_isolation.py`

### State-source strategy (mandatory, v1.6 semantic freeze)

To avoid catalog/META drift, protocol adopts **dual-write + strong consistency**:

- single decision source: runtime catalog status (`catalog.local.yaml` for runtime identities)
- mirrored audit field: `META.status` is required and must equal catalog status
- activation/switch operation must update both layers transactionally
- any mismatch is a protocol violation
- `catalog_multi_active` is allowed for actor-scoped parallelism
- `session_primary_binding` is mandatory in strict lanes (same actor/session tuple must not drift across identities)

Mandatory validator:
- `scripts/validate_identity_state_consistency.py`

## Four core capability contracts

Identity protocol must be verifiable against four capability contracts:

1. **Accurate judgement contract**
   - Requires multimodal evidence consistency checks.
   - Inconsistent evidence cannot transition to `done`.

2. **Reasoning loop contract**
   - Requires hypothesis/patch/result trace per attempt.
   - "No-target-reached" cannot be treated as completion.

3. **Auto-routing contract**
   - Requires problem-type routing map and route-switch policy.
   - When uncertainty persists, route discovery must execute (identity/skill/tool).

4. **Rule learning contract**
   - Requires append-only rulebook linkage to run evidence.
   - Requires both negative and positive rule accumulation over time.

### Accurate judgement canonical binding (v1.6.2 multimodal stream)

To avoid “statement-only” drift, the accurate judgement contract is hard-bound to protocol plugin governance:

1. Contract ID: `rq_034_multimodal_plugin_enforcement_contract_v1`
2. Requirement key: `asb16-rq-034`
3. Canonical validator: `scripts/validate_multimodal_plugin_enforcement.py`
4. Canonical plugin root: `identity/protocol/plugins/`
5. Canonical registries:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - `identity/protocol/plugins/PROVIDER_PROFILES.current.yaml`
6. Mandatory done-transition gate:
   - `requires_multimodal_evidence_consistency=true`
   - `inconsistent_evidence_transition=block_done`
7. Any non-canonical plugin contract/profile source in strict lane must fail-close (`IP-MM-REG-001`).

### Reasoning loop canonical binding (v1.6.2 fail-close stream)

To avoid “trace-present but semantic-invalid” drift, the reasoning loop contract is hard-bound to protocol fail-close plugin governance:

1. Contract ID: `rq_035_reasoning_loop_failclose_contract_v1`
2. Requirement key: `asb16-rq-035`
3. Canonical validator: `scripts/validate_reasoning_loop_failclose.py`
4. Canonical plugin root:
   - `identity/protocol/plugins/reasoning-loop-enforcement/`
5. Mandatory semantic gate:
   - done/pass completion block is controlled by `no_target_completion_mode`:
     - default `terminal_attempt_only`: terminal unresolved attempt cannot transition to done/pass.
     - optional `any_attempt`: any historical `no_target_reached=true` blocks done/pass.
   - `done_requires_terminal_target_reached=true` preserves strict closure for unresolved terminal completion.
   - failed attempt without `next_action` is fail-close.
   - escalation threshold is controlled by `escalation_requirement_mode` (default `at_or_exceed`).
   - once escalation threshold is hit, missing escalation signal is fail-close.
   - escalation signal accepts boolean/token markers and configurable non-empty reference fields when enabled; generic retry text is not escalation by default.
   - strict operations use `strict_run_id_binding=true`: when `run_id` is provided, any selected runtime proof source (including fallback sources) must bind to the same run id or fail-close with `IP-RL-RUN-006`.
   - runtime proof source selection is configuration-driven via `runtime_report_selection_mode` (default `prefer_run_id`) to reduce strict-lane volatility without requiring explicit `report_selected_path`.
6. Enforcement-level policy is configuration-driven (no validator hardcoding):
   - `L1`: attempt trace integrity
   - `L2`: `L1` + four-track evidence refs
   - `L3`: `L2` + external freshness/reconciliation constraints
7. Any registry/profile/contract mismatch for reasoning plugin in strict lane must fail-close (`IP-RL-REG-001` / `IP-RL-CONF-001`).

## Protocol baseline review contract (v1.2.3+)

To avoid identity-level drift and unsupported architectural conclusions, identity upgrades MUST include baseline protocol review evidence.

When task intent involves identity-capability upgrades or architecture decisions:

- `gates.protocol_baseline_review_gate` MUST be `required`.
- `protocol_review_contract` MUST exist in CURRENT_TASK and include:
  - `must_review_sources` (required canonical references)
  - `required_evidence_fields`
  - `evidence_report_path_pattern`

A valid review evidence record MUST include, at minimum:
- review id/time/reviewer
- purpose
- reviewed source list
- findings
- decision

## Identity update lifecycle contract (v1.2.4+)

To match skill update discipline (`trigger -> patch -> validate -> replay`), identity updates MUST define and pass an explicit lifecycle contract.

When runtime detects operational failure or capability gap:

- `gates.identity_update_gate` MUST be `required`.
- `identity_update_lifecycle_contract` MUST exist in CURRENT_TASK and include:
  - `trigger_contract` (when update is mandatory)
  - `patch_surface_contract` (what files/contracts must be changed)
  - `validation_contract` (which checks must pass)
  - `replay_contract` (same-case regression requirements)

Mandatory patch surfaces:
- `CURRENT_TASK.json`
- `IDENTITY_PROMPT.md`
- `RULEBOOK.jsonl`
- `TASK_HISTORY.md`

Mandatory validators:
- `scripts/validate_identity_runtime_contract.py`
- `scripts/validate_identity_upgrade_prereq.py`
- `scripts/validate_identity_update_lifecycle.py`

No replay pass -> no identity learning completion.

## Identity trigger regression contract (v1.2.5+)

To mirror mature skill trigger stability practice, identity route/update changes MUST pass trigger regression.

When routing, trigger conditions, or update gates are modified:

- `trigger_regression_contract` MUST exist in CURRENT_TASK.
- Required suites:
  - `positive_cases`
  - `boundary_cases`
  - `negative_cases`
- Each suite requires deterministic expected/observed route + trigger result.

Mandatory validator:
- `scripts/validate_identity_trigger_regression.py`

No trigger-regression pass -> no identity update completion/merge.

## Agent handoff contract (v1.2.7+)

To prevent master/sub execution drift, identity updates with delegated sub-agent execution MUST pass handoff contract validation.

When handoff is used:

- `gates.agent_handoff_gate` MUST be `required`.
- `agent_handoff_contract` MUST exist in CURRENT_TASK and include:
  - required handoff fields
  - forbidden mutation list
  - handoff log pattern
  - allowed result enum

Mandatory validator:
- `scripts/validate_agent_handoff_contract.py`

No handoff pass -> no merge.

Contract reference:
- `identity/protocol/AGENT_HANDOFF_CONTRACT.md`

## Human-collaboration trigger contract (v1.3.0+)

To avoid silent stalls when runtime is blocked by human-only interactions, identity runtime MUST carry explicit collaboration-trigger controls.

When collaboration blockers are possible:

- `gates.collaboration_trigger_gate` MUST be `required`.
- `blocker_taxonomy_contract` MUST exist in CURRENT_TASK and include mandatory blocker types:
  - `login_required`
  - `captcha_required`
  - `session_expired`
  - `manual_verification_required`
- `collaboration_trigger_contract` MUST exist in CURRENT_TASK and include:
  - hard rule and trigger conditions
  - immediate notify policy (`notify_policy` + `notify_timing=immediate`)
  - `notify_channel` (default: `ops-notification-router`)
  - dedupe controls (`dedupe_window_hours` + `state_change_bypass_dedupe`)
  - `must_emit_receipt_in_chat=true`
  - evidence log path + freshness window

Mandatory validator:
- `scripts/validate_identity_collab_trigger.py`

No collaboration-trigger pass -> no merge/no release for affected identity update.

## Control-loop extension contracts (v1.4.0+)

To keep identity as an auditable control-plane (not a prompt-only layer), runtime MUST enforce the closed-loop extension contracts:

`Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update`

Required runtime contracts:

- `capability_orchestration_contract`
  - defines skill orchestration strategy, MCP/tool selection constraints, and routing budget/risk boundaries.
- `knowledge_acquisition_contract`
  - defines when retrieval is mandatory, source tiers, evidence format, and refresh policy.
- `experience_feedback_contract`
  - defines positive/negative experience feedback, rulebook impact, and replay promotion rules.
- `install_safety_contract`
  - defines non-destructive local-instance install defaults, idempotent reinstall behavior, and backup/rollback requirements for replace operations.
- `ci_enforcement_contract`
  - defines required validator/check inventory and CI gate alignment.

Mandatory validators:

- `scripts/validate_identity_orchestration_contract.py`
- `scripts/validate_identity_knowledge_contract.py`
- `scripts/validate_identity_experience_feedback.py`
- `scripts/validate_identity_install_safety.py`
- `scripts/validate_identity_experience_feedback_governance.py`
- `scripts/validate_identity_ci_enforcement.py`

No control-loop contract pass -> no identity update completion/merge.

## Capability arbitration contract (v1.4.2+)

To keep four core capabilities aligned under runtime tension, identity MUST define conflict arbitration rather than implicit trade-offs.

When routing/latency/learning priorities conflict:

- `gates.arbitration_gate` MUST be `required`.
- `capability_arbitration_contract` MUST exist in CURRENT_TASK and include:
  - `priority_order`
  - `conflict_rules` (judgement_vs_routing / reasoning_vs_latency / routing_vs_learning / learning_vs_hotfix)
  - `trigger_thresholds`
  - `decision_record_required_fields`
  - `sample_report_path_pattern`

Mandatory validator:
- `scripts/validate_identity_capability_arbitration.py`

No arbitration pass -> no merge for affected route/update changes.

## Skill + MCP + Tool collaboration contract (new baseline in v1.2.5)

Identity capability decisions MUST align with collaboration boundaries:

- skill = strategy constraints (sequence/validation/fallback)
- MCP = capability access surface (registered tools)
- tool = concrete execution action

Identity must never assume:
- skill automatically grants external permissions
- skill trigger implies MCP/tools are necessarily available

Collaboration baseline reference:
- `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

## Dual-track governance model

### Track A: hard guardrails

Non-bypassable constraints:
- compliance and legal boundaries
- rejection memory constraints
- media integrity constraints
- escalation triggers
- collaboration trigger gate for human-collab blockers
- protocol baseline review gate for identity-upgrade decisions
- identity update lifecycle gate for runtime evolution decisions
- trigger regression gate for route/update changes
- agent handoff gate for delegated execution changes
- orchestration gate for capability composition decisions
- knowledge acquisition gate for source-grounded decisions
- experience feedback gate for rule learning closure
- ci enforcement gate for required-check integrity
- arbitration gate for four-core conflict resolution integrity

## Release-plane declaration rule

- `Conditional Go`: allowed when local acceptance chain passes but cloud required-gates is not yet green on release head.
- `Full Go`: allowed only when both local acceptance and cloud required-gates pass on same release head.
- install safety gate for local-instance preservation integrity

### Track B: adaptive growth

Continuously updated strategy:
- failed-case pattern extraction
- hypothesis -> experiment -> replay
- skill and prompt tuning proposals

## Runtime state requirements (CURRENT_TASK.json)

Minimum required blocks:
- `objective`
- `state_machine`
- `gates`
- `source_of_truth`
- `escalation_policy`
- `required_artifacts`
- `post_execution_mandatory`
- `evaluation_contract`
- `reasoning_loop_contract`
- `routing_contract`
- `rulebook_contract`
- `blocker_taxonomy_contract`
- `collaboration_trigger_contract`
- `capability_orchestration_contract`
- `knowledge_acquisition_contract`
- `experience_feedback_contract`
- `install_safety_contract`
- `ci_enforcement_contract`
- `capability_arbitration_contract`

Conditional required blocks:
- `protocol_review_contract` (identity upgrade tasks)
- `identity_update_lifecycle_contract` (runtime evolution / update tasks)
- `trigger_regression_contract` (routing/trigger/update gate changes)
- `agent_handoff_contract` (master/sub delegated execution)
- `blocker_taxonomy_contract` + `collaboration_trigger_contract` (human-collab blockers)

## Conflict resolution

Priority order:
1. Canon/hard guardrails
2. CURRENT_TASK runtime contract
3. Skill instructions
4. MCP/tool preference

## Alignment with skill and MCP protocol patterns

To reduce protocol drift and avoid ad-hoc logic:
- Identity must remain declarative and schema-verifiable (like skill metadata discipline).
- Runtime decisions must be contract-driven and testable (like MCP interface determinism).
- Discovery, validation, and release gates must be explicit and automated.
- Identity conclusions for protocol upgrades must be source-cited and evidence-backed.
- Identity updates must follow explicit trigger/patch/validate/replay lifecycle, mirroring skill update discipline.
- Identity route/update behavior must pass positive/boundary/negative trigger regression.
- Identity review must include skill+mcp+tool collaboration boundary checks.
- Identity delegation must pass master/sub handoff payload and mutation-safety checks.
- Identity human-collab blockers must pass taxonomy + immediate auto-notify + receipt constraints.

## Email escalation policy

Email is only for offline blocking actions. Non-blocking updates are routed to logs or dashboards.

## Batch-1 anchor placeholders (v1.6 intake, non-promotional)

The following sections provide stable kernel anchors for v1.6 Batch-1 mapping rows.
Execution closure remains governed by v1.6 governance/review and must stay
`SPEC_READY / PENDING_INTAKE` until validator + replay closure is complete.

### rq_001_unlock_formula_contract_v1

Required receipt fields:

- `unlock_allowed`
- `decision_gates`
- `p0_total`
- `p0_done`
- `p0_not_done_refs`
- `audit_signoff_status`
- `env_blockers`
- `protocol_blockers`
- `evidence_refs`

Hard constraints:

1. `D6` is derived output only (`D1..D5` + `P0` ledger are the only formula inputs).
2. Same governance/review inputs must produce stable `formula_input_digest`.

### rq_002_capability_boundary_contract_v1

Required receipt fields:

- `boundary_classification`
- `classification_source`
- `capability_activation_status`
- `capability_activation_error_code`

Hard constraints:

1. `IP-CAP-*` must classify to `env_auth_blocker` by default.
2. Classification must keep env/auth blockers separate from protocol-code blockers.

### rq_003_promotion_evidence_pipeline_contract_v1

Required receipt fields:

- `decision_hash`
- `input_hash`
- `reviewer_role`
- `reviewer_signature_ref`
- `evidence_bundle_refs`

Hard constraints:

1. Promotion evidence must be non-repudiable and deterministic for same inputs.
2. Narrative-only promotion without receipt fields is invalid.

### rq_004_outlet_matrix_contract_v1

Required receipt fields:

- `outlet_matrix_status`
- `matrix_positive_status`
- `matrix_negative_status`
- `cross_cwd_parity_status`
- `send_time_gate_status`
- `governed_outlet_enforced`
- `outlet_channel_id`
- `outlet_bypass_detected`

Hard constraints:

1. Positive + negative paths are both mandatory.
2. Bypass/manual/direct outlet drift must be fail-closed.

### rq_005_sidecar_cwd_invariance_contract_v1

Required receipt fields:

- `cwd_parity_status`
- `passthrough_digest`
- `sidecar_contract_status`
- `sidecar_error_code`

Hard constraints:

1. Root and temp execution must produce identical normalized passthrough digest.
2. CWD-only noise cannot change sidecar verdict semantics.

### rq_006_release_plane_cloud_evidence_contract_v1

Required receipt fields:

- `target_branch`
- `release_head_sha`
- `required_gates_run_id`
- `run_url`
- `workflow_file_sha`
- `run_head_sha`
- `run_workflow_file_sha`
- `conditions`
- `release_plane_status`

Hard constraints:

1. Release-plane evidence must bind to one run tuple (`run_id + head + workflow_file_sha`).
2. Missing cloud evidence under strict lanes must fail-close.

### rq_007_cross_cwd_absolute_input_contract_v1

Required receipt fields:

- `repo_catalog_input`
- `repo_catalog_is_absolute`
- `repo_cwd_resolved_repo_catalog`
- `tmp_cwd_resolved_repo_catalog`
- `cwd_parity_status`

Hard constraints:

1. Non-absolute `repo_catalog` must fail-close in strict lanes.
2. Root-cwd and temp-cwd resolution must converge to the same canonical path.

### rq_008_docs_bridge_consistency_contract_v1

Required receipt fields:

- `bridge_consistency_status`
- `contradiction_pairs`
- `governance_anchor_refs`
- `review_anchor_refs`

Hard constraints:

1. Contradiction tuples must be deterministic for unchanged docs inputs.
2. Bridge checker output must be machine-replayable.

### rq_009_run_id_anchored_report_selection_contract_v1

Required receipt fields:

- `run_id`
- `selection_strategy`
- `report_selected_path`
- `candidate_count`

Hard constraints:

1. If run-id is present, selection must be run-id anchored before mtime fallback.
2. Same run-id + candidate set must produce stable selected report path.

### rq_010_phase_a_bootstrap_before_strict_contract_v1

Required receipt fields:

- `phase_a_refresh_applied`
- `phase_b_strict_revalidate_status`
- `phase_trace_status`

Hard constraints:

1. Strict revalidate must preserve phase-A bootstrap traceability.
2. Update/readiness/aggregation lanes must consume the same phase tuple semantics.

### rq_011_tmp_collision_safe_allocator_contract_v1

Required receipt fields:

- `tmp_root`
- `generated_paths`
- `collision_count`
- `unique_path_count`
- `path_scope_guard_status`

Hard constraints:

1. Runtime temp allocation must be run-scoped and collision-safe.
2. Temp artifacts must remain within runtime temp root (no path escape).

### rq_012_handoff_collab_freshness_autorotation_contract_v1

Required receipt fields:

- `rotation_applied`
- `freshness_age_days`
- `rotation_receipt_ref`
- `freshness_status`

Hard constraints:

1. Freshness decisions must be receipted and replayable.
2. Stale freshness without rotation closure must fail-close in strict lanes.

### rq_013_protocol_feedback_atomic_emit_contract_v1

Required receipt fields:

- `transaction_id`
- `batch_ref`
- `index_ref`
- `receipt_ref`

Hard constraints:

1. Feedback emit must be atomic across batch/index/receipt.
2. Partial-write failure must rollback and emit deterministic failure code.

### rq_016_refresh_strict_business_interference_matrix_contract_v1

Required receipt fields:

- `refresh_receipt_ref`
- `strict_receipt_ref`
- `interference_row_count_refresh`
- `interference_row_count_strict`

Hard constraints:

1. Refresh and strict modes must both emit interference matrix receipts.
2. Missing either replay side invalidates closure.

### rq_023_discovery_dual_track_requiredization_activation_contract_v1

Required receipt fields:

- `requiredization_triggered`
- `trigger_classes`
- `required_contract_declared`
- `required_contract`
- `discovery_requiredization_status`

Hard constraints:

1. Requiredization must be trigger-conditioned (`not_triggered -> optional`, `triggered_no_apply -> fail-close`).
2. Trigger classification and requiredization status must be deterministic for same inputs.

### rq_024_discovery_apply_coverage_fail_closed_contract_v1

Required receipt fields:

- `discovery_required_total`
- `discovery_required_passed`
- `discovery_required_coverage_rate`
- `discovery_requiredization_status`
- `error_code`

Hard constraints:

1. Apply-time requiredization cannot pass with partial coverage.
2. Coverage mismatch must fail-close with canonical discovery error semantics.

### rq_025_kernel_canonical_source_contract_v1

Required receipt fields:

- `canonical_source_paths`
- `missing_source_paths`
- `kernel_ssot_source_status`
- `ssot_validator_rc`

Hard constraints:

1. Canonical kernel source set is fixed to protocol/runtime/mapping artifacts.
2. Any canonical source drift or missing path is fail-close.

### rq_026_kernel_contract_mapping_projection_contract_v1

Required receipt fields:

- `total_requirements`
- `p0_total`
- `p0_mapped`
- `p0_coverage_rate`
- `orphan_count`
- `unmapped_p0_requirements`

Hard constraints:

1. P0 mapping coverage target is `100%`.
2. Orphan mapping rows must be `0`.

### rq_028_instance_write_boundary_lock_contract_v1

Required receipt fields:

- `base_repo_write_boundary_status`
- `error_code`
- `violation_path`
- `normalized_violation_path`
- `evidence_ref`

Hard constraints:

1. Instance lanes must fail-close on protocol/governance/review write attempts.
2. Canonical boundary classification must stay deterministic across lanes.

### rq_029_semantic_single_source_convergence_contract_v1

Required receipt fields:

- `semantic_tuple_update`
- `semantic_tuple_three_plane`
- `semantic_tuple_full_scan`
- `mismatch_count`
- `mismatch_fields`

Hard constraints:

1. Same lineage must converge to identical semantic tuple across lanes.
2. Tuple mismatch is deterministic fail-close with canonical convergence error code.

### rq_032_headstamp_pre_send_hard_gate_contract_v1

Required receipt fields:

- `headstamp_status`
- `error_code`
- `evidence_ref`
- `actor_binding_ref`

Hard constraints:

1. Missing/malformed/mismatched headstamp must block outbound send.
2. Governed and direct/manual send paths must share canonical pre-send verdict semantics.

### rq_036_host_visible_post_check_next_hop_block_contract_v1

Required receipt/state fields:

- `host_transport_post_check_closure_state_file`
- `host_transport_post_check_state_write_status`
- `host_transport_post_check_block_on_active`
- `host_transport_post_check_blocker_active`
- `host_transport_post_check_closure_status`
- `host_transport_post_check_error_code`
- `reply_first_line_gate_executed`
- `send_time_block_stage`
- `reply_first_line_blocked_reason`

Hard constraints:

1. Host-visible transport attestation MUST persist a post-check closure state on every run.
2. Any write failure on closure state MUST fail-close with escalation-required semantics (`IP-PRIV-ESC-001` family).
3. In strict operations, send-time gate MUST read the post-check closure state before release.
4. If post-check closure state is missing/invalid/unreadable in strict operations, send-time MUST hard-block next hop (`FAIL_REQUIRED`).
5. If `block_on_active=true` and `blocker_active=true`, send-time MUST hard-block next hop (`FAIL_REQUIRED`).
6. This contract is control-plane level only: instance-local manual prefixing is not a valid substitute.
7. When strict send-time is blocked before first-line validator execution, payload MUST mark:
   - `reply_first_line_gate_executed=false`
   - `reply_first_line_status=SKIPPED_NOT_REQUIRED`
   - `send_time_block_stage=pre_first_line_post_check_*`
   and MUST NOT report synthetic first-line-missing evidence (`reply_first_line_missing_count=0`).
8. In strict scan orchestration, same-turn ordering MUST run host transport attestation before send-time gate evaluation when both are required.
9. In strict scan orchestration, tuple-bound post-check recovery MUST execute before host/send gates when blocker-active risk is present.

Operational recovery path (control-plane only):

1. If `host_transport_post_check_blocker_active=true` due stale/mismatched live receipts, recovery MUST use protocol toolchain, not manual state edits:
   - `scripts/recover_host_visible_post_check_state.py`
2. Recovery tool MUST:
   - reseed required host-visible channel receipts with explicit tuple (`actor_id/session_id/run_id`)
   - rewrite runtime state using same tuple
   - immediately rerun `validate_host_transport_wiring_attestation.py --require-live-receipts`
3. If live attestation does not return `PASS_REQUIRED`, recovery remains failed and next-hop strict block stays active.

Metrics (release gate thresholds):

1. `pre_send_gate_pass_rate >= 0.95`
2. `post_check_detectability_rate = 1.00` for injected negative probes.
3. `next_hop_block_rate = 1.00` after post-check blocker activation.
4. `false_green_rate = 0.00` for strict run-bound host-visible attestation.

Machine projection (required in strict scans):

1. `host_visible_post_check_metrics.host_visible_post_check_metrics_status`
2. `host_visible_post_check_metrics.metrics.*`
3. `host_visible_post_check_metrics.metric_statuses.*`

## Batch-6/7 anchor placeholders (v1.6 intake, non-promotional)

The following sections are **kernel anchor placeholders** for v1.6 Batch-6/7 mapping survivability.
They are intentionally non-promotional until corresponding runtime validators and replay evidence are
fully wired. Governance/review authority remains in:

- `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` (`8.10`, `8.11`)
- `docs/review/protocol-remediation-audit-ledger-v1.6.md` (`FIX16-035`, `FIX16-036`)

### rq_017_multi_track_cross_verification_contract_v1

Required receipt fields:

- `t1_status`, `t2_status`, `t3_status`, `t4_status`
- `cross_verification_bundle_id`
- `source_url_set`
- `reference_timestamp_utc`
- `conflict_reconciliation_note`

### rq_022_fallback_taxonomy_normalization_contract_v1

Required receipt fields:

- `fallback_reason_raw`
- `fallback_taxonomy_class`
- `taxonomy_version`
- `normalization_status`
- `normalization_error_code`

### rq_030_intake_evidence_quorum_contract_v1

Required receipt fields:

- `t1_roundtable_status`
- `t2_vendor_status`
- `t3_openai_context_status`
- `t4_protocol_spec_status`
- `cross_verification_bundle_id`
- `source_url_set`
- `reference_timestamp_utc`
- `conflict_reconciliation_note`
