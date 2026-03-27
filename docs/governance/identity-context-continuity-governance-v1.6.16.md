# Identity Context Continuity Governance (v1.6.16)

Status: Active (shared validators + probe lane + pack-lifecycle rollout + instance-visible reentry answer surface + first live pilot adoption + launcher-owned startup consumer landing verified + same-workspace second live identity replay verified, 2026-03-23; cross-workspace breadth still pending)
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

### 0.1A Cross-stream breakthrough sequence atlas (2026-03-24)

1. The canonical explanatory visual atlas for this stream is:
   - `docs/references/identity-protocol-breakthrough-sequence-visual-atlas-v1.6.md`
   - asset root: `docs/references/assets/identity-protocol-breakthrough-sequence-visual-atlas/`
2. This atlas preserves the fixed order `headstamp -> runtime authority -> launcher command surface -> governed continuity proof -> cross-context stable short-command closure`.
3. For this stream, the atlas highlights that continuity is a bounded support layer consumed by launcher/runtime proof, not a replacement authority source; normative truth remains this governance doc, the protocol motherline, and machine validators.

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
6. Shared pack lifecycle surfaces now pre-register those runtime families through:
   - `instance_pack_topology_contract_v1.runtime_optional_dirs`
   - `protocol_downsink_path_immutability_contract_v1.path_registry.runtime_evidence`
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
7. Those registrations land the required `v1.6.13` topology + `v1.6.8` path-governance wiring for future adoption, but they still do not let a pack claim `v1.6.16` adoption without real continuity production / consumption evidence.
8. Creating uncontrolled new trees such as free-form `scripts/context-continuity/` or unregistered runtime continuity directories is non-canonical.

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

### 2.8 Machine contract frozen in this stream

1. `v1.6.16` is no longer only a narrative opening; it now freezes the coding-facing contract families that later shared validators, probes, creator/backfill flows, and launcher consumers must implement.
2. The frozen coding-facing families are:
   - continuity artifact integrity
   - re-entry brief consumption integrity
   - continuity receipt-family evidence
3. Exact requirement ids, mapping rows, and task-contract keys for those families must land together in the corresponding shared mappings rather than being improvised pack-by-pack.
4. Runtime receipt families remain runtime-owned and therefore are not task-contract keys; they are frozen here as runtime evidence families to be consumed by later validators and probes.
5. Any implementation that bypasses the future shared mapping/task-key surface and invents private continuity naming is non-canonical, even if the prose intent sounds similar.

### 2.9 Day-1 topology and path strategy (coding-safe)

1. The Day-1 implementation strategy for `v1.6.16` is explicitly `flat-script-first`.
2. Under that strategy, initial continuity producer surfaces must remain directly under pack-root `scripts/` rather than introducing new governed subtrees.
3. No implementation may assume `scripts/context-continuity/`, `scripts/checkpoints/`, or any similar new subtree is topology-legal until a later governed topology revision lands.
4. The runtime destination continues to be the already-frozen target families:
   - `runtime/reports/context-continuity/`
   - `runtime/state/context-continuity/`
5. No pack may claim those runtime families are adopted until the required `v1.6.13` / `v1.6.8` topology-path registration work is present in that pack's consumed contracts.
6. This means coding may begin now, but first-landing implementations must target canonical filenames and payloads under already-governed roots instead of inventing new directory structure.
7. Continuity implementation for live identities must be **hard-downsink materialization**, not operator folklore:
   - protocol owns the template grammar and validators,
   - identity packs own the materialized executable surfaces,
   - workspace helpers or chat-only procedures must not become the runtime producer.
8. The canonical materialization path family is frozen under the pack-local `scripts/` directory with these exact filenames:
   - `run_identity_context_continuity_guard.sh`
   - `emit_identity_context_checkpoint.py`
   - `materialize_identity_reentry_brief.py`
   - `emit_identity_reentry_consumption_receipt.py`
9. `run_identity_context_continuity_guard.sh` is the canonical proactive guard entry for this stream:
   - it owns cadence counting and forced-trigger dispatch,
   - it is invoked by lifecycle surfaces rather than by ad hoc operator memory,
   - it must not write checkpoint payloads directly; it orchestrates the Python writers below.
10. The canonical guard state / guard receipt paths are frozen under the pack-local runtime roots as:
   - `runtime/state/context-continuity/guard-state.json`
   - `runtime/reports/context-continuity/guard-*.json`
11. The canonical registration surface for those materialized executables is frozen as:
   - `scripts/INSTANCE_SCRIPT_MANIFEST.json`
12. The canonical runtime output paths are frozen as:
   - `runtime/reports/context-continuity/continuity-rolling-*.json`
   - `runtime/reports/context-continuity/continuity-stage-*.json`
   - `runtime/reports/context-continuity/continuity-migration-*.json`
   - `runtime/state/context-continuity/active-reentry-brief.json`
   - `runtime/reports/context-continuity/checkpoint-receipt.json`
   - `runtime/reports/context-continuity/migration-receipt.json`
   - `runtime/reports/context-continuity/reentry-brief-receipt.json`
   - `runtime/reports/context-continuity/reentry-consumption-receipt.json`
13. The canonical guard dispatch semantics are frozen as:
   - `tick` -> evaluate `default_turns_15_30_60`, update `guard-state.json`, and invoke checkpoint writer when cadence hits;
   - `pre-clear` / `pre-migrate` -> emit `continuity-migration-*.json`, refresh `active-reentry-brief.json`, and write `guard-*.json`;
   - `post-recover` -> emit `reentry-consumption-receipt.json` after governed reentry succeeds.
14. `create_identity_pack.py`, `repair_contract_backfill.py`, and later creator/update convergence must be the only canonical materializers for this family; hand-written per-workspace deviations are non-canonical even if they appear to work.
15. A live identity must not claim `v1.6.16` adoption merely because the directories exist or because the answer surface renders; adoption requires the materialized scripts above, manifest registration, guard-state persistence, and real runtime artifacts under the exact output paths above.
16. `base-repo-closure-orchestrator` has now completed the first canonical live pilot adoption for this stream: its own `.identity/base-repo-closure-orchestrator/` root contains the materialized pack-local scripts, manifest rows, guard-state persistence, continuity checkpoint artifacts, governed reentry brief, and the required checkpoint / migration / brief / consumption receipts.
17. That live pilot proof does **not** upgrade the stream into fleet rollout closure; it only proves that the shared protocol-owned materialization path works on one real runtime identity without workspace-specific patching.
18. Required-coverage semantics for this family are now frozen as part of adoption:
   - once `context_continuity_contract_v1` and/or `reentry_brief_consumption_contract_v1` are required in `CURRENT_TASK.json`,
   - and the canonical continuity runtime surfaces are materialized under `runtime/reports/context-continuity/**` plus `runtime/state/context-continuity/**`,
   - `scripts/validate_required_contract_coverage.py` must include these four targets inside instance-lane required coverage: `identity_context_continuity`, `identity_reentry_brief`, `identity_reentry_consumption`, `identity_context_continuity_receipts`.
19. Those four targets are therefore **instance-adopted protocol targets**: protocol owns their semantics, but after adoption they are active runtime obligations and must not be silently downgraded to lane-excluded `SKIPPED_NOT_REQUIRED` just because generic current-round protocol-entry correlation is absent.
20. This rule is intentionally narrow and does not reopen the generic lane-partition policy for unrelated protocol-governance targets; it applies only to protocol-defined families whose adopted truth is pack-local runtime evidence under the fixed continuity path families above.
21. Probe coverage for this rule is mandatory in the continuity probe lane so the adapter cannot regress back to “validators green, required-coverage blind”.
22. Continuity receipt-family join semantics are now explicitly frozen as **lineage-graph joins**, not single-hop-only joins:
    - `checkpoint-receipt.json` still anchors the bounded family root;
    - `migration-receipt.json` may legitimately supersede an earlier migration checkpoint, so long as the current migration ancestry remains joinable back to the anchored checkpoint;
    - `reentry-brief-receipt.json` and `reentry-consumption-receipt.json` must still bind only through canonical continuity ids emitted by the same bounded family.
23. Shared validators/probes must therefore prove repeated `pre-migrate -> pre-migrate -> post-recover` cycles without hand-edited receipt rewrites; a newer migration handoff chained through an earlier migration is canonical evidence, not drift.
24. `RQ-046` receipt-family validation is also frozen as a **bundle-compatible contract projection**, not just a direct validator verdict:
    - when the family is required through the inherited `context_continuity_contract_v1` / `reentry_brief_consumption_contract_v1` pair instead of a standalone task key,
    - `scripts/validate_identity_context_continuity_receipts.py` must still emit bundle-consumable fields `required_contract`, `auto_required_signal`, `contract_key`, `contract_id`, and `contract_derivation_mode`.
25. That projection rule exists so single-target `required_gate_bundle_runner.py --target-name identity_context_continuity_receipts` probes, required-gate bundle rows, and other shared control-plane consumers can reuse the same `RQ-046` truth without pack-specific shims or ad hoc bundle exceptions.
26. If the inherited reentry contract points at a missing or non-canonical `receipt_family_contract_id`, the receipt-family validator must fail-close before receipt-join interpretation rather than silently treating the join as valid evidence.
27. Shared creator/backfill surfaces must therefore restore `reentry_brief_consumption_contract_v1.receipt_family_contract_id` back to the canonical `rq_046_identity_context_continuity_receipt_family_contract_v1` binding whenever drift is detected; leaving a pack in a permanently fail-close state is not a canonical repair strategy.
28. This does **not** weaken fail-close behavior: a migration lineage still fails if its ancestry cannot be joined back to the bounded checkpoint root, and reentry consumption still fails if it no longer joins through the canonical reentry brief lineage.

### 2.10 Coding-facing schema freeze

1. `rolling_checkpoint`, `stage_checkpoint`, and `migration_checkpoint` share one canonical checkpoint schema family; `reentry_brief` is a distinct consumer-facing schema family.
2. The checkpoint schema family must preserve, at minimum:
   - identity tuple: `source_identity_id`, `source_layer`, `work_layer`
   - artifact tuple: `continuity_id`, `artifact_kind`, `generation_reason`, `trigger_class`
   - authority tuple: `authority_refs`, `receipt_refs`
   - task tuple: `task_focus_summary`, `completed_since_previous`, `open_blockers`, `next_actions`
   - lineage tuple: `supersedes_ref`, `freshness`
3. `reentry_brief` must preserve two bounded segments:
   - `stable_prefix`
   - `dynamic_tail`
4. `stable_prefix` must be sufficient to re-anchor the new run onto current authority without replaying full history; it must include identity truth, active task truth, active lane, governing refs, and contract refs.
5. `dynamic_tail` must carry only the minimum dynamic state needed for re-entry: checkpoint lineage, completed work, blockers, next actions, and receipt refs.
6. Optional transcript excerpts, when present, must live in a clearly secondary evidence field family and must never replace `stable_prefix` or `dynamic_tail`.
7. Follow-on validators must treat missing required schema families, unknown `artifact_kind`, malformed refs, stale lineage, or authority override attempts as fail-close conditions.

### 2.11 Launcher-entry bind and receipt-family freeze

1. `v1.6.16` does not own launcher entry, but it does freeze the continuity-side bind points that launcher ownership must consume.
2. The canonical launcher-entry bind object for this stream is a governed `reentry_brief` plus its linked continuity lineage and receipt refs.
3. Successful startup/resume/recover consumption must prove all of the following:
   - `reentry_brief` is structurally valid,
   - tuple/bootstrap truth remains authoritative,
   - referenced continuity lineage is fresh enough under policy,
   - required authority refs still resolve,
   - consumption outcome is emitted as a governed runtime receipt.
4. The canonical runtime receipt-family roles for this stream are:
   - `instance_continuity_checkpoint_receipt`
   - `instance_migration_handoff_receipt`
   - `instance_reentry_brief_receipt`
   - `instance_reentry_consumption_receipt`
5. These receipt families must remain distinct from actor-session tuple ids, thread UUIDs, and launcher installation receipts.
6. Auxiliary guard receipts written as `runtime/reports/context-continuity/guard-*.json` with `receipt_family=identity_context_continuity_guard_receipt_v1` are protocol-owned runtime control receipts, but they are **not** members of the four-role `RQ-046` join family and therefore must neither satisfy nor invalidate the receipt-family join on their own.
7. Any startup path that reads continuity artifacts without producing the governed re-entry consumption evidence is incomplete and must not claim `v1.6.16` implementation closure.
8. The canonical structured continuity-support bundle for launcher/internal consumers is:
   - `scripts/render_identity_context_continuity_bundle.py`
9. That bundle is internal support only; it must not create a new operator-facing continuity command family or shift user entry away from the inherited `v1.6.14` launcher surface.
10. The bundle must keep two states separate instead of collapsing them:
   - `startup_reentry_readiness_status`
   - `live_reentry_consumption_proof_status`
11. Launcher integration is now frozen on that protocol-owned bundle:
   - inherited `v1.6.14` launcher-owned prelaunch preparation consumes the bundle rather than re-deriving continuity interpretation ad hoc inside launcher code or instance chat logic;
   - when the bundle recommends `consume_governed_reentry_brief`, launcher-owned prelaunch preparation must invoke the canonical pack-local `post-recover` guard path and verify that governed runtime receipt proof is present before any downstream Codex delegation.
12. The canonical instance-visible reentry answer bundle for this stream is:
   - `scripts/render_identity_context_reentry_answers.py`
13. That answer bundle exists so an identity instance can answer direct user questions such as “open a new window and migrate me” or “clear now and then rejoin with memory recovery” without manually inventing recovery payloads.
14. The answer bundle is **not** a new terminal command family:
   - terminal start/resume command lookup remains owned by `v1.6.14`;
   - `v1.6.16` only supplies governed reentry answer state plus copyable governed reentry task blocks.
15. The answer bundle must expose intent-separated answer rows for:
   - `migrate_new_window`
   - `reload_after_clear`
16. The answer bundle must keep three facts separate instead of collapsing them:
   - answer-surface render status,
   - `overall_reentry_readiness_status`,
   - `live_reentry_consumption_proof_status`
17. When startup readiness is `PASS_REQUIRED` but live proof is not yet observed, the answer bundle may still return a governed reentry task block, but it must explicitly mark that live proof is pending and that successful recovery may only be claimed after `instance_reentry_consumption_receipt` is emitted.
18. Once live proof is `PASS_REQUIRED`, the answer bundle may report governed recovery as live-proven, but it still must not assemble launcher commands itself.
19. The continuity answer surface must never inject or hardcode thread UUIDs; launcher-command lookup stays delegated to `v1.6.14`, while `v1.6.16` governs only the reentry task and evidence side.

### 2.11A Governed outer support surface boundary (frozen)

1. `scripts/render_identity_context_continuity_bundle.py` remains a governed continuity-support bundle surface on an outer runtime-state layer.
2. It may compress continuity readiness/proof state for launcher/internal consumers, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.
3. `scripts/render_identity_context_reentry_answers.py` remains a governed identity-visible reentry answer surface on an outer runtime-state layer.
4. It may present copyable governed reentry task blocks, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.
5. Neither surface may become a new terminal command family, thread-UUID lookup authority, or raw-transcript authority.
6. Both renderers must self-describe this bounded authority in machine-readable payload form.

### 2.12 Implementation landing order (frozen)

1. Shared implementation for this stream has now landed through:
   - `RQ-044` artifact schema / integrity validators
   - `RQ-045` re-entry brief + startup consumption validators
   - `RQ-046` receipt-family validator
   - positive / negative continuity probe lane
   - creator / backfill / readiness / required-gate wiring
2. `RQ-046` was not allowed to land as an empty join shell; it lands only after `RQ-044` and `RQ-045` already prove artifact validity and startup-consumption validity.
3. The required `v1.6.13` topology-path and `v1.6.8` path-registration work for the canonical continuity runtime families is now landed in shared pack-lifecycle surfaces, so pilot adoption is no longer blocked on path discipline alone.
4. The first live pilot adoption is now frozen as `base-repo-closure-orchestrator`, proven through shared backfill/materialization plus real `tick` -> `pre-migrate` -> `post-recover` runtime evidence under its own pack root.
5. Launcher-owned startup consumption is now also replayed on a second real runtime identity in the same workspace:
   - `base-repo-audit-expert-v3` reproduces `pre-migrate -> launcher prepare-only prelaunch materialization -> reentry-consumption-receipt` through the inherited `v1.6.14` entry surface, using runtime-local catalog truth and the governed `post-recover` bridge rather than a manual continuity-side helper;
   - immediately after `pre-migrate`, the continuity bundle holds `startup_reentry_readiness_status=PASS_REQUIRED` while `receipt_family_observation_status=FAIL_REQUIRED`, proving that live-consumption proof is not being pre-credited;
   - after launcher-owned prelaunch materialization, the same bundle returns `live_reentry_consumption_proof_status=PASS_REQUIRED` plus `receipt_family_observation_status=PASS_REQUIRED`, proving the bridge now closes on more than one live identity without pack-specific hardcoding or downstream-Codex coupling.
6. The remaining landing order from this checkpoint forward is:
   - more real workspace pilots through the same shared materialization path and the same launcher-owned startup-consumer bridge
   - stricter readiness promotion only after live proof breadth is no longer single-workspace
7. Launcher-side positive proof remains insufficient if it proves only that a brief file exists; it must prove that governed startup consumption emitted governed runtime evidence.
8. The launcher-owned startup-consumer bridge is now machine-proven through the launcher probe lane, including real `pre-migrate -> launcher prepare-only prelaunch materialization -> reentry-consumption-receipt` proof in an isolated runtime, and the same bridge now has same-workspace replay on both `base-repo-closure-orchestrator` and `base-repo-audit-expert-v3`.
9. This landing order is frozen so teams do not skip directly from shared wiring to fleet-rollout claims.

### 2.13 Evidence interpretation discipline (frozen)

1. Stream-touch and requirement-touch claims for `v1.6.16` machine-contract changes are authoritative only when evaluated against a pinned commit range or an isolated workspace rooted at the target revision.
2. A bare current-HEAD run taken on a dirty tree is diagnostic-only when unrelated lane changes are present; it must not be re-labeled as the authoritative stream-touch proof for `v1.6.16`.
3. Repository dirty-state counts are situational runtime facts, not protocol claims; governance must freeze the interpretation rule rather than embedding transient file counts.
4. Before rollout or pilot claims, non-`v1.6.16` dirty lanes must be isolated, committed, or otherwise removed from the proof surface so continuity evidence is not cross-contaminated by unrelated deltas.

### 2.14 Chat-derived downsink semantic routing (frozen)

1. Runtime may absolutely derive compact, useful artifacts from dialogue / chat records, but `v1.6.16` owns only the **startup/reentry continuity** slice of that universe.
2. The deciding question is not “did this come from chat?” but “what is this artifact for, how long should it live, and who is allowed to consume it?”
3. Frozen routing rule:
   - if the artifact exists to help a fresh session, launcher recovery, clear-after-reset, or new-window migration resume the current task safely, it belongs to `v1.6.16` continuity;
   - if the artifact exists to prove conversation constraint capture, ambiguity closure, or claim traceability, it belongs to `dialogue_governance_contract`;
   - if the artifact exists to turn validated outcomes into durable rulebook deltas, replay-backed lessons, or scoped next-round operational prompts, it belongs to `experience_feedback_contract` and `v1.6.17` routing/learning strengthening;
   - if the artifact exists to report governance debt, escalation, upgrade proposals, or instance-to-protocol issue traffic, it belongs to `runtime/protocol-feedback/**` and the protocol-feedback atomic emit family.
4. `v1.6.16` continuity artifacts are therefore **bounded startup aids**:
   - short, structured, lineage-linked, and stale-able;
   - stored only under `runtime/reports/context-continuity/**` and `runtime/state/context-continuity/**`;
   - never promoted to long-term learning, protocol escalation, or transcript-archive authority by convenience.
5. Dialogue-governance artifacts are **traceability objects**, not startup authority:
   - they may summarize turns, constraints, ambiguities, and supporting artifacts;
   - they support “did we understand the conversation correctly?” rather than “how do we safely re-enter after reset?”
6. Experience-feedback / routing-learning artifacts are **durable improvement objects**, not continuity payloads:
   - they may persist rulebook deltas, validated lessons, replay-backed prompt artifacts, rollback refs, and TTL-bounded operational prompts;
   - they improve future rounds generically, not merely the next startup of the current interrupted task.
7. Protocol-feedback artifacts are **governance communication objects**, not continuity or learning shortcuts:
   - outbox/index/receipt chains are for escalation, reporting, and protocol-owned routing of issues and upgrade signals;
   - a protocol-feedback batch may cite dialogue or runtime evidence, but it must not masquerade as a `reentry_brief`.
8. Canonical fixed-path routing matrix:
   - continuity / reentry lane:
     - `runtime/reports/context-continuity/continuity-rolling-*.json`
     - `runtime/reports/context-continuity/continuity-stage-*.json`
     - `runtime/reports/context-continuity/continuity-migration-*.json`
     - `runtime/state/context-continuity/active-reentry-brief.json`
     - `runtime/reports/context-continuity/checkpoint-receipt.json`
     - `runtime/reports/context-continuity/migration-receipt.json`
     - `runtime/reports/context-continuity/reentry-brief-receipt.json`
     - `runtime/reports/context-continuity/reentry-consumption-receipt.json`
   - dialogue-governance lane:
     - `runtime/reports/dialogue-content-synthesis-<identity-id>-*.json`
     - `runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json`
     - `runtime/reports/dialogue-result-support-<identity-id>-*.json`
   - experience-feedback / learning lane:
     - `runtime/rulebooks/positive.jsonl`
     - `runtime/rulebooks/negative.jsonl`
     - `runtime/examples/*experience-feedback*.json`
     - `runtime/logs/feedback/*.json`
   - protocol-feedback lane:
     - `runtime/protocol-feedback/outbox-to-protocol/**`
     - `runtime/protocol-feedback/inbox-from-protocol/**`
     - `runtime/protocol-feedback/evidence-index/INDEX.md`
     - `runtime/protocol-feedback/upgrade-proposals/*.md`
     - `runtime/protocol-feedback/atomic/*.receipt.json`
     - `runtime/protocol-feedback/atomic/*.batch.json`
     - `runtime/protocol-feedback/atomic/*.index.json`
     - `runtime/protocol-feedback/roundtables/ROUNDTABLE_*.md`
     - `runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_*.md`
     - `runtime/protocol-feedback/business-partner-intel/BUSINESS_PARTNER_*.md`
     - `runtime/protocol-feedback/vendor-intel/VENDOR_*.md`
     - `runtime/protocol-feedback/issues/ISSUE_*.md`
     - `runtime/protocol-feedback/review-notes/*`
     - `runtime/protocol-feedback/validation/*.json`
9. Frozen anti-pollution rule:
   - the same conversation may legitimately feed multiple lanes, but each emitted artifact must land in its lane’s fixed canonical path family above;
   - do not store feedback-operational prompts, protocol escalation packs, or free-form transcript dumps under `context-continuity`;
   - do not treat dialogue synthesis reports or protocol-feedback batches as startup-consumable continuity bind objects;
   - do not turn `reentry_brief` into a generic “valuable memory sink.”
10. `runtime/memory-absorption/**` is a governed **legacy absorption / quarantine** family only:
   - it may temporarily absorb migrated or deprecated local artifacts,
   - but it is not an active continuity root, not a dialogue-governance report root, not an experience-feedback root, and not a protocol-feedback transport root,
   - anything promoted out of it must be re-materialized into the correct canonical family above rather than consumed in place.
11. In short: `v1.6.16` answers “how do I safely continue this interrupted task now?”, while dialogue / feedback / protocol-feedback answer “what did we learn, prove, or escalate from the conversation?”

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
7. This stream now claims one real live pilot adoption plus governed re-entry consumption proof for `base-repo-closure-orchestrator`, and it also claims that the shared launcher-owned startup-consumer bridge has replayed on a second live identity (`base-repo-audit-expert-v3`) in the same workspace; it still does not claim fleet rollout closure or cross-workspace breadth.

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

1. `v1.6.16` is no longer documentation-only; the shared validator / probe / pack-lifecycle layer is now landed.
2. Promotion from this checkpoint to live implementation closure requires, at minimum:
   - more than one workspace proving the same shared materialization path plus the same launcher-owned startup-consumer bridge under real runtime conditions,
   - governed live evidence breadth showing startup consumption emitted the required runtime receipt family beyond a single pilot.
3. The shared implementation families now landed for this stream are:
   - protocol-owned validator surfaces for continuity artifacts and re-entry briefs;
   - protocol-owned CI probe surface for positive / negative continuity cases;
   - shared creator / backfill / updater surfaces that register continuity contracts and path families.
4. The remaining follow-on landing envelope is therefore narrower:
   - pilot/runtime proof surfaces that demonstrate the same outcome across more than one workspace or identity.
5. The document is now sufficient to support shared protocol coding, first live pilot adoption, the first launcher-owned startup-consumer bridge, and a same-workspace second live replay of that bridge, but not yet sufficient to claim rollout closure until cross-workspace proof lands.
