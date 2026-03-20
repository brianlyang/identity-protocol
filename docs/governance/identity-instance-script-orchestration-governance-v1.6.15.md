# Identity Instance Script Orchestration Governance (v1.6.15)

Status: Active (contract-first stream frozen, 2026-03-21; implementation landing pending)  
Layer: protocol  
Scope: route -> instance-script declarative join, pack-local script manifest, lower-capability dependency join, and instance-script execution receipt family

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
6. `v1.6.15` closes the architecture lane by freezing the orchestration model without pretending that validator/creator/readiness implementation is already complete.

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

### 2.3 Canonical route-to-script additive contract

1. Route-to-script binding lives inside `CURRENT_TASK.json` under the existing `capability_orchestration_contract.task_type_routes.<route>` family.
2. The frozen additive route fields in this stream are:
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
   - `script_receipt_pattern`
3. `primary_instance_scripts` and `fallback_instance_scripts` contain only `script_id` values that resolve through `scripts/INSTANCE_SCRIPT_MANIFEST.json`.
4. A single route may bind multiple role-distinct `script_id` values when the flow legitimately separates probe/render/emit/recovery responsibilities; role separation must stay explicit in the manifest and receipt expectations rather than hidden in prose.
5. `script_preconditions` is the machine-readable admission surface for script execution and may constrain at least these condition families:
   - `identity_lock`
   - `work_layer`
   - `source_layer`
   - `required_contracts`
   - `gate_policies`
6. `script_receipt_pattern` defines the route-level expected receipt family and may narrow or specialize the manifest default, but it must stay runtime-relative and machine-readable.
7. Route admission may not silently discover scripts by filename, by operator convention, or by workspace-global helper directories.
8. When a route declares `primary_instance_scripts`, route readiness depends on those script ids resolving and on `script_preconditions` passing.
9. Route-scoped admission must remain machine-evaluable against only the lower-capability dependencies declared on that route unless some stronger activation policy explicitly freezes a stricter union rule; unrelated route dependencies are not implicit blockers by default.

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

### 2.5 Canonical receipt-family interpretation

1. `v1.6.15` freezes receipt-family classes for route-targeted instance-script execution.
2. The canonical family is:
   - `route_admission_receipt`
   - `instance_script_execution_receipt`
   - `instance_script_emit_receipt`
   - `instance_script_recovery_receipt`
3. Not every script kind requires all four receipts, but every governed route must declare the subset it expects via `script_receipt_pattern` or the manifest default.
4. Receipt families must land under governed runtime-owned report/state areas, not under `scripts/`.
5. Receipt families must be reusable across packs; hardcoded per-pack absolute output paths are non-canonical.
6. A later implementation stream may freeze exact file schemas and validators, but it must preserve these receipt-family roles.
7. Non-normative interpretation example: a probe/helper script may satisfy `instance_script_execution_receipt` before any host-visible receipt exists, while a later emitter script satisfies `instance_script_emit_receipt` and may carry delegated references to inherited host-visible or relay receipt families.
8. Receipt-family projection should remain compatible with the route evidence schema already carried by `capability_orchestration_contract`; at minimum, `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts` must remain machine-projectable rather than recoverable only from free-form narrative.
9. If a governed route produces user-visible final text, that route must bind to at least one pack-local emitter script through `primary_instance_scripts` or `fallback_instance_scripts`.
10. Direct free-form assistant text is not a substitute for route-bound script emission when a route claims governed output.
11. Such governed-output routes must declare an emit-family receipt through `script_receipt_pattern` or the manifest default so final-output governance remains machine-checkable before any outer relay/visible-surface stage begins.

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
11. Review-time diagnostic labels should descend in this order unless a later machine gate freezes a stricter variant: `route_contract_missing`, `manifest_binding_missing`, `script_precondition_blocked`, `mcp_capability_unavailable`, `tool_pipeline_failure`, `script_receipt_mismatch`, `outer_delivery_gap`.
12. Freezing that diagnostic order does not claim that all labels already have protocol-owned validators today; it prevents review from collapsing lower-layer outages back into route/script semantics while implementation is still landing.

### 2.7 Canonical protocol implementation targets

1. The frozen protocol-owned target surfaces for future implementation are the validator and CI families named:
   - `validate_identity_instance_script_orchestration.py`
   - `validate_route_script_receipt_join.py`
   - `validate_instance_script_manifest.py`
   - `run_identity_instance_script_orchestration_probes_ci.sh`
   These future files are protocol-owned targets for the shared `scripts/` and `scripts/ci/` directories once implementation lands.
2. The frozen shared consumers for later landing are:
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/validate_identity_capability_activation.py`
3. Naming these targets does not claim they are already implemented; it freezes the protocol-owned landing path so instances do not invent parallel ad hoc validators.

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

1. This stream freezes route-to-script declarative binding, the canonical pack-local script manifest path, and the execution receipt-family model needed to make pack-root `scripts/` a first-class orchestration unit.
2. This stream does not create new pack-root directories or reopen `v1.6.13` topology semantics.
3. This stream does not reopen `v1.6.14` launcher/install/startup semantics.
4. This stream does not redefine Codex product behavior, MCP transport semantics, or host-visible final-surface promotion rules.
5. This stream does not convert instance scripts into skills or make skills optional when strategy constraints are still required.
6. This stream does not authorize workspace-global script dropzones, user-specific absolute paths, or hardcoded per-instance orchestration logic as the long-term answer.
7. This stream does not claim that validator/creator/readiness implementation is complete today.

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

## 6) Future promotion exit criteria

1. `v1.6.15` promotion beyond contract freeze requires more than documents.
2. At minimum, future implementation closure must prove all of the following together:
   - protocol-owned validators land for manifest integrity and route/script/receipt join,
   - creator/backfill/update/readiness surfaces consume the same contract family,
   - `validate_identity_capability_activation.py` (or its successor) understands instance scripts as a first-class route surface instead of skills/MCP only,
   - route-scoped capability activation can evaluate script-backed routes without unrelated-route union blocking unless a stronger activation policy explicitly requires it,
   - proof packs adopt `scripts/INSTANCE_SCRIPT_MANIFEST.json` and the additive route fields without topology drift,
   - receipt-family enforcement is reusable across packs,
   - receipt-family projection preserves route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`,
   - positive and negative CI probes exist for missing script bindings, missing receipts, and lower-capability join regressions.
3. Until those conditions are proven, the correct interpretation is:
   - `v1.6.15` contract freeze may be active,
   - implementation landing remains open,
   - instances must not improvise parallel orchestration standards.
