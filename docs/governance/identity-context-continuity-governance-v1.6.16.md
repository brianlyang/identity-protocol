# Identity Context Continuity Governance (v1.6.16)

Status: Active (opening-state contract freeze, 2026-03-22; validator/readiness/creator rollout pending)  
Layer: protocol  
Scope: identity-instance continuity checkpoints, migration handoff checkpoints, and startup-consumable re-entry briefing  
Execution mode: topic-level canonical SSOT for v1.6.16 identity-context-continuity governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_context_continuity`.
2. `v1.6.13` remains the semantic owner for canonical identity-instance pack topology and the pack-root `scripts/` executable surface.
3. `v1.6.14` remains the semantic owner for identity-bound Codex launcher/install/startup/resume/recover entry governance.
4. `v1.6.15` remains the semantic owner for route -> instance-script -> lower-capability -> receipt join.
5. `v1.6.16` does not reopen those streams; it freezes the continuity layer that bridges fresh-session recovery onto those already-governed boundaries.
6. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
7. `docs/governance/identity-context-continuity-preflight-v1.6.16.md` is retained as the pre-opening research record; this file is the active governance source.
8. This stream freezes continuity artifacts and re-entry semantics, not Codex product history semantics, not MCP capability negotiation semantics, and not raw transcript persistence as a new authority layer.

## 1) Why v1.6.16 is required

1. `v1.6.13` solved where instance-owned executable helpers belong.
2. `v1.6.14` solved how an identity-bound Codex process is launched, resumed, and recovered.
3. `v1.6.15` solved how governed routes bind to pack-local scripts and lower capability surfaces.
4. What remained under-modeled is how an identity instance safely preserves enough continuity to recover after:
   - fresh window / fresh session,
   - `clear` or explicit context reset,
   - compaction or context-window pressure,
   - restart / recover / resume migration,
   - large lane transitions or major task-plan turns.
5. Without a dedicated continuity stream, operators and instances drift back into the same unstable patterns:
   - over-trusting raw chat transcript,
   - relying on memory instead of governed artifacts,
   - mixing startup truth with late-turn summaries,
   - inventing ad hoc checkpoint files and directory conventions.
6. `v1.6.16` closes that gap by freezing a continuity model that is explicit, bounded, audit-friendly, and subordinate to existing authority surfaces.

## 2) Frozen continuity model (no ambiguity)

### 2.1 Continuity artifacts are derived assets, not authority sources

1. Continuity artifacts exist to accelerate re-entry and migration, not to replace protocol truth.
2. Authority remains in the already-governed sources:
   - `IDENTITY_PROMPT.md`
   - `CURRENT_TASK.json`
   - active governance/review docs resolved through `stream-doc-registry.current.yaml`
   - workbook control-plane surfaces
   - governed runtime receipts / reports / state artifacts
3. A continuity artifact may summarize, point at, or stitch together those authority sources, but it must not silently override them.
4. Raw transcript persistence, vendor session history, and ad hoc operator notes are therefore non-authoritative by default.

### 2.2 Canonical continuity artifact family

`v1.6.16` freezes exactly four canonical continuity roles:

1. `rolling_checkpoint`
   - short-horizon continuity snapshot for same-task re-entry;
   - cheap and frequent;
   - optimized for near-term restart or context recovery.
2. `stage_checkpoint`
   - deeper checkpoint after a meaningful phase boundary;
   - optimized for resuming after a larger interruption or plan transition.
3. `migration_checkpoint`
   - explicit cross-window / cross-session handoff checkpoint;
   - emitted before restart, recover, resume migration, or deliberate context reset.
4. `reentry_brief`
   - startup-consumable distilled brief for a new run;
   - references the latest valid checkpoint lineage and active authority surfaces.

No additional artifact role may be treated as canonical continuity motherline without a later governed stream.

### 2.3 Canonical trigger policy

1. Turn-count-only triggering is insufficient.
2. Event-only triggering is also insufficient.
3. The frozen default trigger profile for this stream is the named policy:
   - `default_turns_15_30_60`
4. Under that named policy:
   - `rolling_checkpoint` default cadence = every 15 turns
   - `stage_checkpoint` default cadence = every 30 turns
   - `migration_checkpoint` default cadence = every 60 turns
5. Forced trigger classes are also canonical and override cadence when present:
   - `clear_or_context_reset`
   - `compaction_boundary`
   - `launcher_restart_or_recover`
   - `resume_migration`
   - `major_commit`
   - `major_gate_flip`
   - `lane_switch`
   - `root_cause_turn`
6. Future alternative cadence schemes must be declared as named governed profiles; ad hoc per-script hidden constants or user-specific numeric flags are non-canonical.

### 2.4 Canonical artifact envelope

Every governed continuity artifact must remain compact, machine-readable, and bounded.

Minimum frozen field families are:

- `continuity_id`
- `artifact_kind`
- `generation_reason`
- `trigger_class`
- `source_identity_id`
- `source_layer`
- `work_layer`
- `authority_refs`
- `task_focus_summary`
- `completed_since_previous`
- `open_blockers`
- `next_actions`
- `receipt_refs`
- `supersedes_ref`
- `freshness`

Minimum additional requirements:

1. `authority_refs` must point back to governed truth surfaces rather than copy them wholesale by default.
2. `task_focus_summary`, `completed_since_previous`, `open_blockers`, and `next_actions` must remain bounded summaries, not full raw transcript dumps.
3. `receipt_refs` must preserve runtime evidence linkage so a checkpoint cannot claim progress without machine-auditable downstream artifacts.
4. `supersedes_ref` must preserve lineage when a newer artifact replaces an older one.
5. `artifact_kind` must be one of the four canonical roles above.

### 2.5 Canonical storage and path boundary

1. Continuity producers are instance-owned executable surfaces and therefore belong under pack-root `scripts/`, inheriting `v1.6.13`.
2. Continuity outputs are runtime-owned artifacts and must not be stored under `scripts/`.
3. The frozen target runtime families for this stream are:
   - `runtime/reports/context-continuity/`
   - `runtime/state/context-continuity/`
4. To prevent path sprawl, the canonical storage model is intentionally narrow:
   - machine artifacts live under the two target roots above;
   - artifact role is distinguished by the artifact payload and file naming, not by creating a new root per role.
5. The recommended canonical file families are:
   - `runtime/reports/context-continuity/continuity-*.json`
   - `runtime/state/context-continuity/active-reentry-brief.json`
6. This stream freezes those target families as the intended canonical destination, but no pack may claim adoption until the corresponding `v1.6.13` topology rows and `v1.6.8` path-registry rows are backfilled.
7. Creating uncontrolled new trees such as free-form `scripts/context-continuity/` or unregistered runtime continuity directories is non-canonical.

### 2.6 Canonical producer / consumer split

1. Producer responsibility belongs to pack-local instance scripts, not to workspace-global patch directories.
2. Consumer responsibility splits across already-governed layers:
   - launcher/startup/resume/recover entry consumption remains owned by `v1.6.14`
   - route-bound use of continuity-aware scripts remains owned by `v1.6.15`
   - tuple/bootstrap truth remains owned by `v1.6.12`
3. `v1.6.16` owns only:
   - which continuity artifacts are canonical,
   - when they are emitted,
   - what they must contain,
   - how they may be safely consumed for re-entry.
4. A resume thread UUID must not be reinterpreted as a continuity artifact id, and a continuity artifact id must not be reinterpreted as actor-session tuple truth.
5. Continuity consumption may narrow startup context to a bounded brief, but it must not bypass identity lock, source-layer, work-layer, or bootstrap tuple checks.

### 2.7 Canonical re-entry brief interpretation

1. `reentry_brief` is the continuity artifact intended for new-run consumption.
2. A `reentry_brief` must be compact enough to serve as startup/readback support rather than long-history replacement.
3. The preferred structure is:
   - stable prefix: identity truth, task truth, active lane, authority refs, contract refs
   - dynamic tail: latest checkpoint lineage, completed work, blockers, next actions, receipt refs
4. Optional transcript excerpts, if any, are evidence-only supplements and must remain secondary to the structured brief.
5. A `reentry_brief` must never claim to be the semantic owner of the task; it is an entry accelerator, not a substitute `CURRENT_TASK.json`.

## 3) Four-track cross-verification boundary

### 3.1 T1 roundtable / internal topology

1. Reuse `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` for explicit identity binding and no hidden ambient inheritance.
2. Reuse `identity/protocol/AGENT_HANDOFF_CONTRACT.md` for layer attribution:
   - identity = guidance and constraints
   - skill = process / strategy
   - MCP/tool = capability execution
3. Continuity artifacts must therefore remain identity-level control-plane objects, not covert skill/MCP replacements.
4. Workbook/governance/review/registry/validator together already form an automated protocol-governance family, so this stream must join that family instead of introducing a parallel informal audit layer.

### 3.2 T2 vendor / OpenAI Codex evidence

1. OpenAI Codex guidance states that instruction discovery happens when Codex starts, once per run / launched session.
2. OpenAI Codex config reference exposes startup-scoped surfaces such as `model_instructions_file` and `project_doc_fallback_filenames`, and separate history/compaction surfaces such as `history.persistence`, `history.max_bytes`, `compact_prompt`, and `model_auto_compact_token_limit`.
3. OpenAI Responses API reference distinguishes explicit conversation-state carriers (`conversation`, `previous_response_id`) from instructions and truncation policy.
4. Therefore continuity is correctly modeled as a startup/resume/recover-support layer rather than as a claim that raw history is protocol authority.
5. Canonical vendor anchors for this stream:
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/api/reference/resources/responses/methods/create/`
   - `https://platform.openai.com/docs/guides/prompt-caching`

### 3.3 T3 Context7 / persistence / MCP reference boundary

1. LangGraph persistence material treats checkpoints, thread state, cross-thread memory, replay, and fork as explicit durable-execution primitives.
2. MCP material treats initialization and capability negotiation as explicit lifecycle events and keeps `tools`, `resources`, and `prompts` as the base primitives, with `tasks` as a cross-cutting durable utility.
3. This strongly supports the `v1.6.16` boundary:
   - continuity is explicit and durable,
   - continuity is above MCP rather than inside MCP semantics,
   - checkpoint lineage should be explicit rather than inferred from transcript accidents.
4. Canonical reference family for this track:
   - Context7 library id `/websites/langchain_oss_python_langgraph`
   - Context7 library id `/modelcontextprotocol/modelcontextprotocol`

### 3.4 T4 protocol / inherited-stream references

1. `v1.6.13` owns canonical pack-root `scripts/` topology.
2. `v1.6.14` owns launcher/install/startup/resume/recover governance.
3. `v1.6.15` owns route/script/lower-capability/receipt join.
4. `v1.6.12` owns bootstrap tuple truth.
5. `docs/governance/identity-context-continuity-preflight-v1.6.16.md` is the pre-opening research record only; this stream is now the active owner.
6. `v1.6.16` owns only continuity checkpoints, migration handoff checkpoints, and startup-consumable re-entry briefing.

## 4) Closure scope and explicit non-goals

1. This stream freezes the continuity artifact model and the re-entry briefing boundary for identity instances.
2. This stream does not redefine Codex product history semantics.
3. This stream does not make raw transcript persistence the protocol authority source.
4. This stream does not reopen `v1.6.13` topology semantics, `v1.6.14` launcher semantics, or `v1.6.15` route/script semantics.
5. This stream does not redefine MCP capability negotiation or server startup health.
6. This stream does not authorize arbitrary new pack-root script subtrees or runtime path families outside governed registration.
7. This stream does not claim that validator, creator, launcher, and fleet rollout are already complete today.

## 5) Frozen implementation guidance

1. Treat continuity as infrastructure, not as ad hoc transcript dumping.
2. Keep continuity producers in pack-root `scripts/`, inheriting `v1.6.13`.
3. Keep continuity artifacts in runtime-owned continuity families only, inheriting `v1.6.8` path-governance discipline.
4. Keep launcher/resume/recover entry as the consumer boundary for startup re-entry, inheriting `v1.6.14`.
5. Keep route-bound script usage and lower-capability joins explicit, inheriting `v1.6.15`.
6. Prefer one narrow continuity report root plus one narrow continuity state root over proliferating many new directories.
7. Keep continuity payloads compact and structured; long transcript replay remains non-canonical by default.
8. Use named trigger policies rather than hidden numeric constants in implementation.

## 6) Future promotion exit criteria

1. `v1.6.16` opening-state closure is documentation and boundary freeze only.
2. Promotion to implementation closure requires, at minimum:
   - protocol-owned validator(s) for continuity artifact and re-entry brief integrity,
   - protocol-owned probe lane for positive + negative continuity cases,
   - creator/backfill rollout for contract and path registration,
   - launcher/startup integration that consumes continuity artifacts without bypassing tuple/bootstrap truth,
   - one pilot instance adoption proving continuity production and re-entry consumption under real runtime conditions.
3. Candidate implementation families for this stream are expected to include:
   - protocol-owned validator surfaces for continuity artifacts and re-entry briefs;
   - protocol-owned CI probe surfaces for positive / negative continuity cases;
   - shared creator / backfill / updater surfaces that can register continuity contracts and path families;
   - launcher/startup consumers that can read governed `reentry_brief` artifacts without bypassing tuple/bootstrap truth.
4. Those implementation families are frozen as the follow-on landing envelope; this opening document does not claim those surfaces are implemented yet.
