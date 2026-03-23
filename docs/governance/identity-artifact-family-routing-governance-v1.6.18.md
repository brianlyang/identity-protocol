# Identity Artifact Family Routing Governance (v1.6.18)

Status: Active (protocol-scoped semantic/path freeze opened 2026-03-23; raw dialogue retention family plus shared validator/creator/readiness consumption landed 2026-03-23; whole cross-family matrix enforcement remains follow-on work)  
Layer: protocol  
Scope: protocol-owned persisted artifact families inside governed identity packs/runtime; fixed-path routing and anti-semantic-pollution boundary  
Execution mode: topic-level canonical SSOT for v1.6.18 artifact-family routing governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_artifact_family_routing`.
2. `v1.6.13` remains the semantic owner for pack topology and pack-root `scripts/` executable ownership.
3. `v1.6.8` remains the semantic owner for downsink path immutability and path-registry enforcement.
4. `v1.6.16` remains the semantic owner for continuity and re-entry artifacts.
5. `v1.6.17` remains the semantic owner for routing/learning strengthening and the bounded 4→1 loopback bridge.
6. `v1.6.18` does not reopen those streams; it freezes the cross-family routing matrix for protocol-owned persisted artifacts that are often colloquially miscalled “memory”.
7. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
8. Scope is intentionally narrow: only protocol-owned identity-pack/runtime artifact families listed here are in scope. This stream does not create a catch-all “memory layer”, and it does not treat non-protocol product/history/session surfaces as fallback semantic owners.

## 1) Why v1.6.18 is required

1. The protocol already froze multiple individual artifact lanes:
   - pack-root `RULEBOOK.jsonl` and `TASK_HISTORY.md`,
   - dialogue-governance reports,
   - experience-feedback rulebooks/examples/logs,
   - protocol-feedback communication channels,
   - continuity/re-entry artifacts,
   - legacy `runtime/memory-absorption/**` quarantine roots.
2. What was still missing is one explicit motherline routing matrix saying these are **different artifact families**, not one vague “memory” bucket.
3. Without that matrix, the system keeps drifting into the same semantic failures:
   - treating `RULEBOOK.jsonl` and `runtime/rulebooks/*.jsonl` as one object,
   - trying to use `TASK_HISTORY.md` as continuity or startup state,
   - writing protocol-governance traffic as if it were learning memory,
   - treating `runtime/memory-absorption/**` as a valid active sink,
   - mistaking declaration/gate keys for persisted artifact families.
4. `v1.6.18` closes that gap by freezing, for each protocol-owned family:
   - semantic owner,
   - canonical fixed path family,
   - payload/content class,
   - production standard,
   - production method,
   - primary consumer surface.

## 2) Non-negotiable routing law (no ambiguity)

### 2.1 `memory` is not a canonical protocol artifact family

1. `memory` is not a canonical path family, contract id, report family, or success-path storage class in the identity protocol.
2. Any persisted protocol-owned artifact that matters to governance, runtime recovery, learning, or protocol communication must resolve to one canonical family defined in this stream or in an inherited owner stream.
3. “Put it into memory” is therefore non-canonical language unless it is immediately resolved to the exact governed family name and canonical path root.

### 2.2 Family identity is determined by semantics + path + producer + consumer together

1. Path alone is not sufficient.
2. Payload wording alone is not sufficient.
3. A canonical artifact family is defined by the conjunction of:
   - semantic owner,
   - canonical path family,
   - payload/content class,
   - production method,
   - primary consumer surface.
4. Two artifacts with superficially similar content must still remain separate when their owners or consumers differ.

### 2.3 Declaration keys and gates are not artifact families

1. `reject_memory_gate` is a gate, not a storage sink.
2. `dialogue_retention_contract_v1`, `dialogue_governance_contract`, `experience_feedback_contract`, `context_continuity_contract_v1`, and `reentry_brief_consumption_contract_v1` are declaration/contract surfaces, not persisted artifact families.
3. `INSTANCE_SCRIPT_MANIFEST.json` is a script-catalog/manifest surface, not a “memory” sink.
4. Validators and creators may consume those declarations, but no declaration key may be misreported as the canonical output family.

## 3) Frozen canonical routing matrix

| Family | Canonical fixed paths | Semantic owner | Payload/content class | Primary producer method | Primary consumer surface |
| --- | --- | --- | --- | --- | --- |
| Pack rulebook family | `RULEBOOK.jsonl` | durable identity rulebook / patch surface | append-only durable rule rows | identity update lifecycle + governed rule writeback | identity update / learning validators and durable pack evolution |
| Pack task-history family | `TASK_HISTORY.md` | chronological task/result writeback | human-readable task chronology | post-execution append / governed task writeback | operator audit, lifecycle chronology, pack-local historical trace |
| Runtime dialogue-retention family | `runtime/reports/dialogue-retention/**`; `runtime/state/dialogue-retention/**` | governed raw dialogue truth mirror | current-thread jsonl mirror, delivery supplement, sync receipt, rolling state | shared post-delivery hook + dialogue-retention validator | operator truth inspection, raw-dialogue audit, downstream bounded analysis |
| Runtime dialogue-governance family | `runtime/reports/dialogue-content-synthesis-<identity-id>-*.json`; `runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json`; `runtime/reports/dialogue-result-support-<identity-id>-*.json` | conversation-to-result justification | structured dialogue synthesis / cross-validation / result-support reports | dialogue-governance bundle + validators | dialogue/result proof / done-state support |
| Runtime experience-feedback family | `runtime/rulebooks/positive.jsonl`; `runtime/rulebooks/negative.jsonl`; `runtime/examples/*experience-feedback*.json`; `runtime/logs/feedback/*.json` | replay-backed learning deltas | positive/negative rule deltas, feedback samples, feedback logs | governed experience-feedback writeback and replay-backed learning flows | fourth-loop strengthening, learning replay, rule promotion |
| Runtime protocol-feedback family | `runtime/protocol-feedback/**` | instance↔protocol governance communication | feedback batches, inbox/outbox traffic, proposals, issues, roundtables, validation, indexes, receipts | protocol-feedback emit/inbox/index/upgrade helpers | protocol remediation / audit / governance circulation |
| Runtime continuity/reentry family | `runtime/reports/context-continuity/**`; `runtime/state/context-continuity/**` | bounded checkpoint and re-entry support | checkpoints, reentry brief, guard state, continuity receipts | v1.6.16 continuity guard + deterministic writers | startup/resume/recover continuity consumption |
| Runtime memory-absorption family | `runtime/memory-absorption/**` | quarantine / migration absorption only | absorbed legacy evidence awaiting re-materialization | explicit migration/absorption/backfill only | migration/backfill/re-materialization only |

## 4) Per-family semantic freeze

### 4.1 Pack rulebook family

1. Canonical path family:
   - `RULEBOOK.jsonl`
2. Semantic owner:
   - durable identity rulebook and pack-level rule accumulation.
3. Payload/content class:
   - append-only durable rule rows used as long-lived pack knowledge and patch surface.
4. Production standard:
   - rows must remain machine-structured and update-lifecycle compatible.
5. Production method:
   - governed rulebook writeback during identity update / learning closure; schema repair/backfill may normalize historical rows but does not change family semantics.
6. Primary consumer surface:
   - pack evolution, durable learning review, lifecycle validation, and rulebook-backed decision reinforcement.
7. Hard boundary:
   - `RULEBOOK.jsonl` is **not** the same object as `runtime/rulebooks/positive.jsonl` or `runtime/rulebooks/negative.jsonl`.

### 4.2 Pack task-history family

1. Canonical path family:
   - `TASK_HISTORY.md`
2. Semantic owner:
   - chronological task/result writeback for the identity pack.
3. Payload/content class:
   - human-readable historical log of task turns, outcomes, and major milestones.
4. Production standard:
   - append after governed task progression or task completion; remain chronological rather than semantic-summary-first.
5. Production method:
   - post-execution mandatory append under governed task/lifecycle flows.
6. Primary consumer surface:
   - operator review, pack-local chronology, and historical traceability.
7. Hard boundary:
   - `TASK_HISTORY.md` is not a continuity checkpoint, not a reentry brief, and not a protocol-feedback or learning sink.

### 4.3 Runtime dialogue-retention family

1. Canonical fixed roots:
   - `runtime/reports/dialogue-retention/**`
   - `runtime/state/dialogue-retention/**`
2. Canonical payload families include at minimum:
   - `dialogue-thread-<thread-id>.jsonl` current-thread mirror,
   - `dialogue-final-reply-<thread-id>-*.json` delivery supplement,
   - `dialogue-retention-sync-*.json` governed sync receipt,
   - `current-thread.json` rolling state.
3. Semantic owner:
   - governed raw dialogue truth retention bridged from the product-sidecar session stream.
4. Payload/content class:
   - exact source snapshot mirror plus delivery supplement/receipt/state metadata for the current thread.
5. Production standard:
   - mirror exactness is measured against the recorded source snapshot captured by the sync receipt/state; live sidecar advance after sync on the active thread does not reclassify the recorded mirror as corrupt.
6. Production method:
   - shared post-delivery runtime hook calling `scripts/run_identity_delivery_runtime_hooks.py` -> `scripts/run_identity_dialogue_retention_guard_runtime.py sync`, bound from pack-local `scripts/emit_current_thread_final_reply.py`.
7. Primary consumer surface:
   - operator truth inspection, governed raw-dialogue validation, and downstream bounded analysis that needs exact delivered dialogue rather than synthesized summaries.
8. Hard boundary:
   - raw dialogue retention is not dialogue-governance summary, not continuity/reentry bind state, not protocol-feedback traffic, and not `runtime/memory-absorption/**`.

### 4.4 Runtime dialogue-governance family

1. Canonical fixed paths:
   - `runtime/reports/dialogue-content-synthesis-<identity-id>-*.json`
   - `runtime/reports/dialogue-cross-validation-matrix-<identity-id>-*.json`
   - `runtime/reports/dialogue-result-support-<identity-id>-*.json`
2. Semantic owner:
   - dialogue-derived objective/constraint/evidence/result justification.
3. Payload/content class:
   - structured reports that explain what the dialogue required, what evidence supported the result, and where ambiguities remained.
4. Production standard:
   - must stay in the governed dialogue report family and remain identity-scoped.
5. Production method:
   - dialogue-governance renderers/validators or a governed dialogue feedback bundle.
6. Primary consumer surface:
   - dialogue-quality review, done-state support, result traceability, and contradiction detection.
7. Hard boundary:
   - dialogue reports are not continuity, not protocol-feedback traffic, and not the learning rulebook sink.

### 4.5 Runtime experience-feedback family

1. Canonical fixed paths:
   - `runtime/rulebooks/positive.jsonl`
   - `runtime/rulebooks/negative.jsonl`
   - `runtime/examples/*experience-feedback*.json`
   - `runtime/logs/feedback/*.json`
2. Semantic owner:
   - replay-backed positive/negative learning and operational feedback deltas.
3. Payload/content class:
   - rule deltas, replay-linked sample cases, and bounded feedback logs.
4. Production standard:
   - promotion remains replay-gated; raw feedback alone does not equal active learning closure.
5. Production method:
   - governed experience-feedback writeback, replay validation, and fourth-loop strengthening flows.
6. Primary consumer surface:
   - learning replay, rule promotion/demotion, fourth-loop strengthening, and loopback preparation.
7. Hard boundary:
   - runtime experience-feedback rulebooks are distinct from pack-root `RULEBOOK.jsonl`, and they are not protocol-feedback or continuity sinks.

### 4.6 Runtime protocol-feedback family

1. Canonical fixed root:
   - `runtime/protocol-feedback/**`
2. Canonical subfamilies include at minimum:
   - `outbox-to-protocol/**`
   - `inbox-from-protocol/**`
   - `evidence-index/INDEX.md`
   - `upgrade-proposals/**`
   - `atomic/**`
   - `roundtables/**`
   - `issues/**`
   - `validation/**`
   - `review-notes/**`
   - governed intel subtrees already registered by contract.
3. Semantic owner:
   - governed communication between runtime identities and the protocol control plane.
4. Payload/content class:
   - protocol-facing batches, receipts, pending notices, proposals, issues, roundtables, validation artifacts, and channel indexes.
5. Production standard:
   - channel outputs must remain inside the governed protocol-feedback tree and follow registered outbox/inbox/index semantics.
6. Production method:
   - protocol-feedback emit helpers, inbox processors, validation surfaces, and governance circulation tooling.
7. Primary consumer surface:
   - protocol remediation, audit intake, governance negotiation, and protocol upgrade routing.
8. Hard boundary:
   - protocol-feedback is not the canonical sink for continuity checkpoints, dialogue result proof, or learning rule promotion.

### 4.7 Runtime context-continuity / reentry family

1. Canonical fixed roots:
   - `runtime/reports/context-continuity/**`
   - `runtime/state/context-continuity/**`
2. Canonical payload families include at minimum:
   - continuity checkpoints,
   - `active-reentry-brief.json`,
   - guard state / guard reports,
   - continuity receipt families.
3. Semantic owner:
   - bounded identity continuity, migration handoff, and startup-consumable re-entry support.
4. Payload/content class:
   - machine-readable checkpoints, reentry brief, guard-state, and continuity consumption receipts.
5. Production standard:
   - derived continuity artifacts remain subordinate to authority surfaces and stay compact/bounded.
6. Production method:
   - `v1.6.16` guard and deterministic continuity writers under pack-root `scripts/`.
7. Primary consumer surface:
   - startup / resume / recover continuity consumption.
8. Hard boundary:
   - continuity artifacts are not task history, not protocol-feedback, and not the generic learning sink.

### 4.8 Runtime memory-absorption family

1. Canonical fixed root:
   - `runtime/memory-absorption/**`
2. Semantic owner:
   - quarantine / migration absorption of legacy or imported material only.
3. Payload/content class:
   - absorbed historical material awaiting explicit re-materialization into a governed active family.
4. Production standard:
   - this family is non-active by default; presence alone does not satisfy any active contract obligation.
5. Production method:
   - explicit migration/absorption/backfill flows only.
6. Primary consumer surface:
   - migration, repair, and re-materialization tooling.
7. Hard boundary:
   - `runtime/memory-absorption/**` may not be consumed as if it were active continuity, dialogue-governance, experience-feedback, protocol-feedback, or durable pack rulebook/task-history truth.

### 4.9 Gates and declaration keys (control plane, not storage)

1. `reject_memory_gate` remains a mandatory semantic guard rail, not a persisted artifact family.
2. `dialogue_retention_contract_v1`, `dialogue_governance_contract`, `experience_feedback_contract`, `context_continuity_contract_v1`, and `reentry_brief_consumption_contract_v1` declare obligations and canonical validators; they do not themselves store the resulting artifacts.
3. Any implementation or answer surface that confuses a declaration key with an output family is semantically non-compliant.

## 5) Cross-family hard boundaries

1. `RULEBOOK.jsonl` and `runtime/rulebooks/*.jsonl` must never be collapsed into one “rule memory” object.
2. `TASK_HISTORY.md` must never be promoted to continuity/reentry authority.
3. `runtime/reports/dialogue-retention/**` and `runtime/state/dialogue-retention/**` must never be collapsed into dialogue-governance summaries or continuity/reentry artifacts.
4. Dialogue-governance reports must never be used as the canonical learning sink or protocol-feedback channel.
5. Protocol-feedback traffic must never be used as a substitute continuity or dialogue-proof family.
6. Continuity artifacts must never become durable pack history or learning rulebooks.
7. `runtime/memory-absorption/**` must never satisfy active continuity, dialogue, experience-feedback, or protocol-feedback obligations.
8. New protocol-owned persisted artifact families require a later governed stream; they must not silently appear under generic “memory” wording.
9. When an identity instance or operator asks “这段记忆应该存哪里”, the only canonical answer is: resolve it to the exact family name and canonical path family above.

## 6) Current scan anchors absorbed into this stream

Current local runtime inspection of `base-repo-closure-orchestrator` confirms that the ambiguity is real and must be frozen protocol-side rather than left to per-instance folklore:

1. pack-root durable families are already present:
   - `RULEBOOK.jsonl`
   - `TASK_HISTORY.md`
2. governed experience-feedback families are already present:
   - `runtime/examples/base-repo-closure-orchestrator-experience-feedback-sample.json`
   - `runtime/logs/feedback/*.json`
   - `experience_feedback_contract.required=true`
3. governed protocol-feedback families are already present:
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
   - `runtime/protocol-feedback/outbox-to-protocol/*.json`
4. continuity families are already registered and contract-keyed:
   - `context_continuity_contract_v1`
   - `reentry_brief_consumption_contract_v1`
   - canonical roots `runtime/reports/context-continuity/` and `runtime/state/context-continuity/`
5. raw dialogue retention is now a distinct governed family and live bridge:
   - `dialogue_retention_contract_v1`
   - canonical roots `runtime/reports/dialogue-retention/` and `runtime/state/dialogue-retention/`
   - shared producer bridge `scripts/run_identity_delivery_runtime_hooks.py` + `scripts/run_identity_dialogue_retention_guard_runtime.py`
6. dialogue-governance is already a distinct contract family even when not required:
   - `dialogue_governance_contract.required=false`
7. `reject_memory_gate` is already required.

Frozen interpretation:

- the protocol already has multiple distinct persisted families;
- the missing piece was the motherline routing matrix tying them together so they cannot keep being mislabeled as one “memory” bucket.

## 7) Machine-consumer landing absorbed into v1.6.18

This stream is no longer docs-only. The following machine-consumed closure is now part of the stream without reopening owner boundaries:

1. `rq_051_identity_dialogue_retention_contract_v1` is now bound in the motherline mapping and backed by `scripts/validate_identity_dialogue_retention.py`.
2. `scripts/identity_dialogue_retention_common.py`, `scripts/run_identity_dialogue_retention_guard_runtime.py`, and `scripts/run_identity_delivery_runtime_hooks.py` now provide the shared raw-dialogue retention bridge.
3. `scripts/create_identity_pack.py` and `scripts/repair_contract_backfill.py` now materialize `dialogue_retention_contract_v1`, the canonical runtime roots, and validator/readiness wiring instead of leaving raw dialogue retention as per-pack folklore.
4. `scripts/release_readiness_check.py`, `scripts/ci/run_required_runtime_gates_ci.sh`, `scripts/validate_required_contract_coverage.py`, and `scripts/required_gate_bundle_runner.py` now consume the dialogue-retention machine lane.
5. `scripts/ci/run_identity_dialogue_retention_probes_ci.sh` proves:
   - exact source snapshot mirror on the canonical family,
   - delivery-hook invocation from the final visible emitter surface,
   - continuity tick coexistence without semantic collapse,
   - active-thread live-drift reporting without reclassifying the recorded mirror as corrupt.

## 8) Follow-on closure boundary

This stream has landed raw dialogue retention machine consumers, but one follow-on boundary still remains open without reopening semantic ownership:

1. a later whole-matrix validator may enforce cross-family routing for every family, not only the raw dialogue retention lane;
2. workbook closure should be updated to reflect the new eight-family matrix and the distinction between raw-dialogue retention vs dialogue-governance vs continuity;
3. future new families must still arrive through governed stream openings rather than ad hoc pack additions.

## 9) Execution ownership boundary for ISSUE-032 closeout

This stream now explicitly freezes the owner split so whole-matrix closure can proceed without semantic drift:

1. Semantic ownership remains with this `v1.6.18` governance stream plus the inherited owner streams already referenced here; execution closure must not reinterpret family names, fixed paths, canonical producer/consumer roles, or frozen non-goals.
2. Execution closeout may continue the protocol-owned machine landing for `ISSUE-032`, including shared validators, probes, required-gate wiring, readiness consumption, workbook truth-sync, and cross-family misuse fail-close, as long as it extends this same routing matrix rather than inventing a new one.
3. Audit/review lanes verify closure, evidence, and truth-sync state; they do not become replacement semantic owners for any artifact family.
4. Any proposal that adds a new family, repoints a canonical root, collapses two frozen families into one sink, or promotes `runtime/memory-absorption/**` onto an active success path must reopen governed owner review instead of shipping through execution closeout.
5. These roles are protocol functions, not person-specific appointments: semantic owner, execution closeout owner, and audit verifier remain stable even if the current humans on those lanes change.

## 10) Frozen non-goals

1. This stream does not create a new generic “memory subsystem”.
2. This stream does not reopen `v1.6.13`, `v1.6.16`, or `v1.6.17` as owner streams.
3. This stream does not authorize instances to invent ad hoc new artifact roots.
4. This stream does not turn declaration keys/gates into storage families.
5. This stream does not promote `runtime/memory-absorption/**` back onto any active success path.
