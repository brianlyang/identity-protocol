# Identity Instance Script Orchestration Governance (v1.6.15)

Status: Active (shared validator/probe/consumer landing in place, including execution-lane admission governance, 2026-03-21; cross-pack adoption rollout still in progress)  
Layer: protocol  
Scope: route -> instance-script declarative join, route -> execution-lane admission, pack-local script manifest, lower-capability dependency join, and instance-script receipt families

Execution mode: topic-level canonical SSOT for v1.6.15 identity-instance script orchestration governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_instance_script_orchestration`.
2. `v1.6.13` remains the semantic owner for canonical identity-instance pack topology and the pack-root `scripts/` surface.
3. `v1.6.14` remains the semantic owner for identity-bound Codex launcher/install/startup governance.
4. `v1.6.12` remains the owner for native-chat bootstrap tuple semantics and `v1.6.11` remains the owner for governed outer relay semantics.
5. `v1.6.15` does not reopen any of those streams; it freezes the missing orchestration join that sits between them.
6. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
7. `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md` is retained as the pre-freeze design record; this stream is now the active governance source.

## 1) Why v1.6.15 is required

1. `v1.6.13` froze where instance-owned helper execution lives: pack-root `scripts/`.
2. `v1.6.14` froze how an identity-bound Codex process should be installed, started, resumed, and recovered.
3. What remained under-modeled was how `CURRENT_TASK.json` routes select pack-local scripts and how those scripts join to lower capability surfaces such as skills, MCP servers, and tool pipelines.
4. Without this join, a pack can be topology-ready and launcher-ready while still relying on operator memory or ad hoc local reasoning to decide:
   - which script serves a route,
   - which fallback script is allowed,
   - which lower capability dependencies are required,
   - which receipts must exist after execution.
5. That gap causes drift, weak diagnostics, and repeated confusion between protocol debt, instance migration debt, runtime dirt, and lower-capability availability problems.
6. `v1.6.15` closes the architecture lane by freezing the orchestration model and landing the shared validator/probe/consumer family without pretending that every target pack has already adopted it.

## 2) Frozen orchestration model (no ambiguity)

### 2.1 One join chain, not a new pack-root layer

1. `v1.6.15` does not create a fourth pack-root directory or a parallel execution tree.
2. The frozen join chain is:
   - `IDENTITY_PROMPT.md` for identity guidance and policy,
   - `CURRENT_TASK.json` for machine-routed task admission,
   - `scripts/INSTANCE_SCRIPT_MANIFEST.json` for pack-local script catalog and relative entry resolution,
   - pack-root `scripts/` for instance-owned executable sources,
   - `primary_skills` / `fallback_skills` / `required_mcp` / `pipeline` for lower capability execution.
3. `agents/identity.yaml` remains descriptive sidecar metadata only; it is not promoted by this stream into the authoritative orchestration join surface.
4. `v1.6.15` therefore builds on the `v1.6.13` topology freeze rather than redefining it.

### 2.2 Canonical pack-local script manifest

1. The canonical pack-local manifest path is:
   - `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`
2. The manifest is the only canonical script-catalog surface for route-targetable instance scripts.
3. Manifest entries are keyed by `script_id` and must resolve only to files under the same pack-root `scripts/` subtree.
4. The minimum frozen manifest fields for each entry are:
   - `script_id`
   - `entry_relpath`
   - `script_kind`
   - `default_receipt_pattern`
5. `entry_relpath` must be pack-relative under `scripts/`; absolute paths and cross-pack references are forbidden.
6. `script_kind` exists to distinguish orchestration roles such as entry helpers, workers, emitters, probes, and recovery helpers without creating extra executable roots.
7. `default_receipt_pattern` must point only at governed runtime-owned receipt families; source files under `scripts/` are never the receipt sink.

### 2.3 Canonical route-to-script / execution-lane additive contract

1. Route-to-script binding lives inside `CURRENT_TASK.json` under the existing `capability_orchestration_contract.task_type_routes.<route>` family.
2. The frozen additive route fields in this stream are:
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
   - `script_receipt_pattern`
   - `allowed_execution_lanes`
   - `lane_admission_policy`
   - `lane_receipt_pattern`
   - `lane_block_on_fallback`
3. `primary_instance_scripts` and `fallback_instance_scripts` contain only `script_id` values that resolve through `scripts/INSTANCE_SCRIPT_MANIFEST.json`.
4. A single route may bind multiple role-distinct `script_id` values when the flow legitimately separates probe/render/emit/recovery responsibilities; role separation must stay explicit in the manifest and receipt expectations rather than hidden in prose.
5. `script_preconditions` is the machine-readable admission surface for script execution and may constrain at least these condition families:
   - `identity_lock`
   - `work_layer`
   - `source_layer`
   - `required_contracts`
   - `gate_policies`
6. `script_receipt_pattern` defines the route-level expected execution/emit/recovery receipt family and may narrow or specialize the manifest default, but it must stay runtime-relative and machine-readable.
7. `allowed_execution_lanes` contains only machine-readable lane rows; each row freezes:
   - `lane_id`
   - `lane_class`
   - `lane_source`
   - `endpoint_class`
8. `lane_admission_policy` freezes how route admission interprets declared lanes and whether admission receipts must report a passing lane-admission result.
9. `lane_receipt_pattern` defines the route-level expected admission receipt family for the selected lane and must stay runtime-relative and machine-readable.
10. `lane_block_on_fallback` is the explicit fail-close switch for routes that must not silently fall back to undeclared manual/editor/webhook execution lanes once a declared lane contract exists.
11. Route admission may not silently discover scripts or execution lanes by filename, operator convention, ambient browser/editor state, or workspace-global helper directories.
12. When a route declares `primary_instance_scripts`, route readiness depends on those script ids resolving and on `script_preconditions` passing.
13. When a route declares execution-lane governance, route readiness additionally depends on the lane contract staying machine-evaluable without narrative-only exceptions.
14. Route-scoped admission must remain machine-evaluable against only the lower-capability dependencies declared on that route unless some stronger activation policy explicitly freezes a stricter union rule; unrelated route dependencies are not implicit blockers by default.

### 2.4 Lower-capability dependency join is explicit, not implicit

1. Instance scripts are a first-class orchestration unit, but they do not replace skills, MCP servers, or tools.
2. The frozen lower-layer join is:
   - skill layer: `primary_skills`, `fallback_skills`
   - MCP capability layer: `required_mcp`
   - tool execution layer: `pipeline`, `max_tool_calls`, `max_runtime_minutes`, and future tool-route validators
3. A route that needs a pack-local script plus lower capabilities must declare both sides; a script id alone is not permission to bypass required skills, MCP servers, or downstream tool constraints.
4. Skill guidance remains strategy, MCP remains capability access, and tools remain execution primitives; instance scripts are the pack-local orchestration glue that binds those lower layers to identity-owned flows.
5. `script_preconditions.required_contracts` and `script_preconditions.gate_policies` may reference inherited gateway, tuple, headstamp, host-visible, or relay contracts when a route depends on them, but that reference does not transfer semantic ownership of those contracts into `v1.6.15`.
6. Provider-specific MCP incidents and business-tool failures remain lower-layer failures; they must not be relabeled as proof that the script-orchestration contract is wrong.
7. The canonical responsibility matrix for this stream is:
   - `agent/codex` = route selection, orchestration decisions, and protocol-gate interpretation
   - `identity instance/scripts` = pack-local control plane, governed emit/recovery glue, route-bound receipt join, and protocol-to-lower-layer bridge
   - `skills/scripts` = business execution surface
   - `mcp/tool` = capability access and execution primitives
8. Review and implementation must preserve non-substitution between those roles; an identity-pack instance script may bind, gate, or evidence lower execution, but it is not a substitute for a skill/business script library.
9. A request to make `identity instance/scripts` behave as a full business-execution script pack is semantic misuse against this stream, not proof that the route/script orchestration contract is incomplete.
10. Lower-layer defects must still be attributed to the correct role boundary after route/script correctness is established; this stream does not authorize role collapse by narrative convenience.

### 2.5 Canonical receipt-family interpretation

1. `v1.6.15` freezes receipt-family classes for route-targeted instance-script execution.
2. The canonical family is:
   - `instance_script_admission_receipt`
   - `instance_script_execution_receipt`
   - `instance_script_emit_receipt`
   - `instance_script_recovery_receipt`
3. Not every script kind requires all four receipts, but every governed route must declare the subset it expects via `script_receipt_pattern` or the manifest default.
4. Receipt families must land under governed runtime-owned report/state areas, not under `scripts/`.
5. Receipt families must be reusable across packs; hardcoded per-pack absolute output paths are non-canonical.
6. A later implementation stream may freeze exact file schemas and validators, but it must preserve these receipt-family roles.
7. Non-normative interpretation example: a probe/helper script may satisfy `instance_script_execution_receipt` before any host-visible receipt exists, while a later emitter script satisfies `instance_script_emit_receipt` and may carry delegated references to inherited host-visible or relay receipt families.
8. Admission-family receipts must preserve machine-readable lane provenance; at minimum, `lane_id`, `lane_class`, `lane_source`, `lane_endpoint_class`, `lane_admission_status`, and `fallback_used` must remain machine-projectable rather than narrative-only.
9. Receipt-family projection should remain compatible with the route evidence schema already carried by `capability_orchestration_contract`; at minimum, `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts` must remain machine-projectable rather than recoverable only from free-form narrative.
10. Execution-family receipts do not substitute for admission-family receipts when a route explicitly freezes execution-lane governance.
11. If a governed route produces user-visible final text, that route must bind to at least one pack-local emitter script through `primary_instance_scripts` or `fallback_instance_scripts`.
12. Direct free-form assistant text is not a substitute for route-bound script emission when a route claims governed output.
13. Such governed-output routes must declare an emit-family receipt through `script_receipt_pattern` or the manifest default so final-output governance remains machine-checkable before any outer relay/visible-surface stage begins.

### 2.6 Failure-attribution ladder (frozen)

1. Missing `primary_instance_scripts` / `fallback_instance_scripts` on an otherwise route-ready pack is an orchestration-gap diagnosis by default, not a topology failure.
2. A route referencing unknown `script_id` values is manifest/join drift.
3. A manifest entry resolving outside pack-root `scripts/` is a topology violation and falls back to `v1.6.13` ownership rules.
4. Missing lower dependencies (`primary_skills`, `required_mcp`, tool pipeline availability) are capability-activation failures, not script-surface failures.
5. Missing tuple/bootstrap truth at process start is a launcher/bootstrap failure owned by `v1.6.12` / `v1.6.14`, not by this stream.
6. Missing governed outer delivery receipts remains a relay/visible-surface issue owned by `v1.6.11` / `v1.6.12`, not by this stream.
7. Reviewers must classify failures in that order before proposing changes, so runtime dirt and lower-layer incidents do not get misread as orchestration-semantics regressions.
8. A topology-ready, exit-ready pack that has not yet adopted `scripts/INSTANCE_SCRIPT_MANIFEST.json` or the additive route fields is an instance-adoption gap for this stream, not a reopen of `v1.6.13` or `v1.6.14`.
9. A route blocked only by skills, MCP servers, or tools that are not declared on that route is a capability-activation policy or wiring defect, not evidence that route/script semantics are wrong.
10. A route/script receipt family that omits `route_selected` / `skills_used` / `mcp_tools_used` provenance is a receipt-projection gap; teams must repair the receipt model rather than bypass it with narrative-only explanations.
11. Review-time diagnostic labels should descend in this order unless a later machine gate freezes a stricter variant: `route_contract_missing`, `manifest_binding_missing`, `script_precondition_blocked`, `lane_admission_mismatch`, `mcp_capability_unavailable`, `tool_pipeline_failure`, `script_receipt_mismatch`, `outer_delivery_gap`.
12. Freezing that diagnostic order does not claim that all labels already have protocol-owned validators today; it prevents review from collapsing lower-layer outages back into route/script semantics while implementation is still landing.

### 2.7 Canonical protocol implementation targets

1. The landed protocol-owned shared surfaces for this stream are:
   - `scripts/validate_identity_instance_script_orchestration.py`
   - `scripts/validate_instance_script_manifest.py`
   - `scripts/validate_route_script_receipt_join.py`
   - `scripts/validate_route_execution_lane_admission.py`
   - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - `scripts/release_readiness_check.py`
   - `scripts/validate_identity_capability_activation.py`
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
   - `scripts/identity_creator.py`
2. The remaining protocol-owned follow-on obligations are:
   - adopt the same contract family across target packs without topology drift,
   - keep receipt-family provenance reusable across packs as additional admission/execution/recovery specializations appear,
   - avoid reintroducing pack-local one-off consumers outside the landed shared path.
3. Shared stream-doc-registry current-pointer consumption for the touched validator family now resolves through one protocol-owned helper plus one invariant guard, so those consumers do not each carry their own default-path or alias-resolution drift.
4. Freezing both the landed surfaces and the remaining rollout obligations keeps the protocol-owned path explicit so instances do not invent parallel ad hoc validators, consumers, or receipt rules.

### 2.8 Additive reinforcement envelope (non-reopen, machine-governed)

1. `v1.6.15` may absorb additive reinforcement that strengthens route/script/dependency/receipt machine traceability without reopening topology, launcher, bootstrap, relay, or business-heuristic ownership.
2. Aggregate capability-activation artifacts that summarize multiple route rows under `route-any-ready` or an equivalent multi-route policy are not single-route receipts.
3. Such aggregate artifacts may omit `route_selected` only when they machine-project aggregate scope/cardinality explicitly; at minimum, the additive projection must preserve:
   - `route_scope`
   - `route_activation_strategy`
   - `route_ready_count`
   - `route_total_count`
   - `route_selection_cardinality`
4. Any route-scoped admission/execution/emit/recovery receipt, or any artifact that explicitly claims single-route scope, continues to require non-empty `route_selected`.
5. Protocol-owned artifacts may add declared-vs-observed dependency projection when they preserve machine comparability between route contract and runtime evidence.
6. The preferred additive model is one machine-readable declared/observed pair plus gap reasons, for example:
   - `declared_dependency_projection`
   - `observed_dependency_projection`
   - `dependency_gap_reasons`
7. A later implementation stream may freeze exact field names, but the semantic minimum is that declared route dependencies, observed activations/executions, and the machine-readable gap between them remain comparable without narrative-only reconciliation.
8. Protocol-owned route/script consumers may add a governed semantic-anchor envelope by reference, digest, or both when downstream consumers must prove they preserved route-selected semantic basis rather than silently narrowing it.
9. Any such semantic-anchor envelope must preserve at least:
   - `semantic_anchor_ref`
   - `semantic_anchor_schema_id`
   - `semantic_anchor_source`
   - `semantic_anchor_revision`
   - `semantic_anchor_digest`
   - `semantic_anchor_status`
10. If any semantic-anchor field is present on a protocol-owned artifact, the complete semantic-anchor family must be present; partial semantic-anchor projection fails closed for the affected route-/report-family validator.
11. Aggregate/report builders may promote a semantic-anchor family to aggregate top-level only when exactly one fully formed observed family can be projected across contributing route rows without ambiguity; otherwise the route-row evidence remains scoped and a machine-visible ambiguity reason is emitted instead of inventing a merged anchor.
12. The semantic-anchor envelope is a transfer/control primitive only; it must not hardcode domain-specific scoring fields, search heuristics, or product-level business taxonomy into the core protocol contract.
13. Protocol-owned artifacts may also expose an optional outcome-sentinel reference hook when downstream risk signals need governed traceability without redefining orchestration ownership.
14. If an outcome-sentinel hook is present, it must preserve at least:
   - `outcome_sentinel_ref`
   - `outcome_sentinel_schema_id`
   - `outcome_sentinel_status`
15. If any outcome-sentinel field is present on a protocol-owned artifact, the complete outcome-sentinel family must be present; partial sentinel projection fails closed for the affected route-/report-family validator.
16. Aggregate/report builders may promote an outcome-sentinel family to aggregate top-level only when exactly one fully formed observed family can be projected across contributing route rows without ambiguity; otherwise the route-row evidence remains scoped and a machine-visible ambiguity reason is emitted instead of inventing a merged sentinel.
17. Outcome sentinels do not become universal core pass/fail semantics merely by existing; a stream-specific policy must explicitly freeze whether a sentinel is advisory, gating, or ignored for the affected artifact family.
18. Additive implementation must reuse the frozen field families above rather than minting parallel aliases for the same semantics; `route_scope` / `route_activation_strategy` / `route_ready_count` / `route_total_count` / `route_selection_cardinality` and `declared_dependency_projection` / `observed_dependency_projection` / `dependency_gap_reasons` remain the canonical motherline names for this stream.
19. These additive reinforcements belong to `v1.6.15` only insofar as they strengthen route/script/dependency/receipt governance; they must not be used to smuggle workbook-only narrative or instance-specific business heuristics into protocol SSOT.

## 3) Four-track cross-verification boundary

### 3.1 T1 roundtable / internal topology

1. `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` already freezes explicit identity binding, runtime isolation, and no hidden inheritance from ambient state.
2. `identity/protocol/AGENT_HANDOFF_CONTRACT.md` already freezes identity vs skill vs MCP/tool role boundaries and requires failures to be attributed to one layer before patching.
3. `v1.6.15` reuses those boundaries to keep route/script join explicit instead of hidden inside operator memory or workspace conventions.

### 3.2 T2 vendor / OpenAI Codex evidence

1. OpenAI Codex config reference documents startup-scoped surfaces such as project/user `config.toml`, `model_instructions_file`, `project_doc_fallback_filenames`, and `mcp_servers.<id>.command`.
2. OpenAI Codex guidance documents that Codex builds its instruction chain when it starts, once per run, by reading `AGENTS.md` or configured fallback filenames.
3. Therefore the identity protocol must keep launcher/startup concerns (`v1.6.14`) separate from route/script orchestration concerns (`v1.6.15`): startup decides how Codex enters, while this stream decides how governed routes bind to pack-local scripts and then to lower capabilities.
4. Canonical vendor anchors for this stream:
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`

### 3.3 T3 Context7 / MCP / reference boundary

1. MCP initialization negotiates protocol version, client/server capabilities, and readiness before normal operations.
2. MCP servers expose primitives such as `tools`, `resources`, and `prompts`; those are lower capability surfaces, not identity-pack route catalogs.
3. Therefore instance-script orchestration belongs above MCP in the stack: scripts may depend on MCP, but they do not redefine MCP capability negotiation.
4. Canonical references for this track:
   - Context7 library id `/modelcontextprotocol/modelcontextprotocol`
   - MCP initialize lifecycle and server capability materials covering `initialize`, `notifications/initialized`, `tools`, `resources`, and `prompts`
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

### 3.4 T4 protocol / inherited-stream references

1. `v1.6.13` owns canonical pack-root `scripts/` topology.
2. `v1.6.14` owns launcher/install/startup governance.
3. `v1.6.12` owns bootstrap tuple truth and entry interpretation.
4. `v1.6.11` owns governed relay final-answer semantics.
5. `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md` is the pre-freeze design record that this stream promotes into an active governance lane.
6. `v1.6.15` owns only the route/script/dependency/receipt join model and must not be used to reopen the inherited streams above.

## 4) Closure scope and explicit non-goals

1. This stream freezes route-to-script declarative binding, route-to-execution-lane admission, the canonical pack-local script manifest path, and the receipt-family model needed to make pack-root `scripts/` a first-class orchestration unit.
2. This stream does not create new pack-root directories or reopen `v1.6.13` topology semantics.
3. This stream does not reopen `v1.6.14` launcher/install/startup semantics.
4. This stream does not redefine Codex product behavior, MCP transport semantics, or host-visible final-surface promotion rules.
5. This stream does not convert instance scripts into skills or make skills optional when strategy constraints are still required.
6. This stream does not authorize workspace-global script dropzones, user-specific absolute paths, or hardcoded per-instance orchestration logic as the long-term answer.
7. This stream does not claim that cross-pack adoption rollout is complete today.

## 5) Frozen implementation guidance

1. Treat instance scripts as infrastructure-owned orchestration surfaces, not as ad hoc local patches.
2. Route selection lives in `CURRENT_TASK.json`; pack-local path resolution lives in `scripts/INSTANCE_SCRIPT_MANIFEST.json`; executable sources live in pack-root `scripts/`.
3. Keep lower dependencies explicit on the route contract even when a route is primarily served by a script.
4. Keep receipts in governed runtime subtrees; keep source files in pack-root `scripts/`.
5. Keep manifest entries relative-path-friendly and pack-local.
6. Keep pack-local scripts thin: they may consume shared protocol builders, renderers, and validators, but they must not fork protocol semantics.
7. Governed user-visible final output must come from a route-bound emitter script rather than direct free-form assistant text.
8. Keep failure attribution layered so teams can distinguish orchestration gaps from topology drift, launcher drift, lower-capability failures, and outer-delivery gaps.

### 5.1 Developer-ready coding checklist

Any implementation that claims to follow `v1.6.15` should satisfy this checklist before code review:

1. A route that uses pack-local script execution declares `primary_instance_scripts` and any required `fallback_instance_scripts`.
2. Every referenced `script_id` resolves through `scripts/INSTANCE_SCRIPT_MANIFEST.json` to a path under pack-root `scripts/`.
3. `script_preconditions` and `script_receipt_pattern` stay machine-readable and do not embed user-specific absolute paths.
4. Lower capability dependencies remain declared through `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
5. All new runtime artifacts land under governed `runtime/` paths, never under `scripts/`.
6. Shared validator/creator/readiness surfaces are extended rather than duplicated by per-pack one-off logic.
7. Route-scoped capability activation can evaluate script-backed routes without union-blocking unrelated routes unless a stronger activation policy explicitly requires that stricter behavior.
8. Receipt outputs preserve machine-readable route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`.
9. Any governed route that returns user-visible final text binds to at least one pack-local emitter script and declares an emit-family receipt.
10. If a protocol-generated wrapper seeds final-channel relay receipts on behalf of a route-bound emitter, that wrapper must carry the canonical final-relay constants/helpers and remain executable under the wrapper-template smoke contract; SHA freshness and token presence alone are not sufficient.
11. Aggregate activation/report artifacts that summarize multiple routes declare explicit scope/cardinality instead of pretending to be route-scoped receipts.
12. If declared-vs-observed dependency projection, semantic-anchor projection, or outcome-sentinel hooks are adopted on this lane, they remain machine-readable and stay on the shared validator/probe/control path rather than forking into per-pack narrative-only variants.

## 6) Future promotion exit criteria

1. `v1.6.15` promotion beyond contract freeze still requires more than documents.
2. The following implementation elements are now landed:
   - protocol-owned validators for manifest integrity, route/script join, route/script-to-receipt join, and route-to-execution-lane admission,
   - positive and negative probes through `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`,
   - `scripts/release_readiness_check.py` consumption of those validators,
   - `scripts/validate_identity_capability_activation.py` awareness of instance scripts as a first-class route surface,
   - `scripts/create_identity_pack.py`, `scripts/repair_contract_backfill.py`, and `scripts/identity_creator.py` consumption of the same contract family,
   - generated session-chain wrappers now freeze a `session_chain_executable_smoke_policy`, and the protocol gate executes that smoke against the final-channel relay branch so generator completeness defects fail closed instead of hiding behind template SHA parity,
   - governed final emit now auto-recovers stale host-visible post-check blockers through `scripts/recover_host_visible_post_check_state.py`, and the gateway trust-boundary probe suite proves under protocol-root invocation that a pre-seeded closure blocker can return to `PASS_REQUIRED` without manual runtime surgery.
   - this consumer citation does not, by itself, claim workspace-root / protocol-root invariance for the trust-boundary suite; cross-cwd invariance must be evidenced separately if needed.
3. Full implementation closure still requires all of the following together:
   - proof packs adopt `scripts/INSTANCE_SCRIPT_MANIFEST.json` and the additive route fields without topology drift,
   - proof packs adopt `allowed_execution_lanes`, `lane_admission_policy`, `lane_receipt_pattern`, and `lane_block_on_fallback` where external/manual/editor/webhook fallback risk exists,
   - target packs adopt the same shared consumer path through create/backfill/update flows rather than per-pack ad hoc rollout,
   - route-scoped capability activation remains reusable without unrelated-route union blocking unless a stronger activation policy explicitly requires it,
   - lane-admission receipts keep `lane_id`, `lane_class`, `lane_source`, `lane_endpoint_class`, `lane_admission_status`, and `fallback_used` machine-visible under live pack execution,
   - receipt-family projection keeps route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts` under live pack execution,
   - aggregate activation/report artifacts that summarize multiple routes keep scope/cardinality machine-visible and do not masquerade as single-route receipts,
   - any adopted declared-vs-observed dependency projection, semantic-anchor envelope, or outcome-sentinel hook stays compatible with one shared validator/probe/control family instead of fragmenting into pack-local dialects,
   - future admission/execution/recovery receipt specializations, if introduced, stay compatible with the landed shared validator family rather than forking it.
4. Until those conditions are proven, the correct interpretation is:
   - `v1.6.15` contract freeze is active,
   - shared validator/probe/consumer landing is present,
   - cross-pack adoption rollout remains open,
   - instances must not improvise parallel orchestration standards.
