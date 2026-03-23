# Protocol Remediation Audit Ledger (v1.6.18 artifact-family routing stream)

Status: Active (`ISSUE-032` closed on 2026-03-23; protocol-owned semantic/path freeze, raw dialogue-retention landing, and whole-matrix routing validator/gate closure are now absorbed into the stream)
Scope: protocol review ledger for canonical artifact-family routing across governed identity pack/runtime surfaces

## 0) Stream objective

Current-state judgment for this stream must remain anchored to:

- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

This stream freezes one bounded review judgment:

1. protocol already owns multiple distinct persisted artifact families inside identity packs/runtime;
2. those families were previously frozen piecemeal by different streams;
3. what remained under-modeled was the motherline routing matrix that keeps them from being collapsed into one vague “memory” concept;
4. `v1.6.18` therefore opens as a semantic-routing stream, not as a new storage subsystem and not as a non-protocol product/history discussion.

## 1) Opening findings absorbed into this stream

### 1.1 The ambiguity is real inside protocol scope, not just in operator wording

Current local runtime inspection of `base-repo-closure-orchestrator` confirms that protocol scope already contains multiple persisted families with different owners:

1. pack-root durable families exist:
   - `RULEBOOK.jsonl`
   - `TASK_HISTORY.md`
2. runtime raw dialogue-retention family now exists as a governed sink:
   - `runtime/reports/dialogue-retention/**`
   - `runtime/state/dialogue-retention/**`
   - shared producer bridge `scripts/run_identity_delivery_runtime_hooks.py` -> `scripts/run_identity_dialogue_retention_guard_runtime.py`
3. runtime experience-feedback families exist:
   - `runtime/examples/base-repo-closure-orchestrator-experience-feedback-sample.json`
   - `runtime/logs/feedback/*.json`
4. runtime protocol-feedback families exist:
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
   - `runtime/protocol-feedback/outbox-to-protocol/*.json`
5. continuity families are already declared:
   - `context_continuity_contract_v1`
   - `reentry_brief_consumption_contract_v1`
   - canonical continuity roots under `runtime/reports/context-continuity/` and `runtime/state/context-continuity/`
6. dialogue-governance is already a distinct contract family even while optional:
   - `dialogue_governance_contract.required=false`
7. `reject_memory_gate` is already required.

Frozen audit interpretation:

- the protocol does **not** lack persisted artifact families;
- it lacks one shared routing matrix that prevents those families from being semantically blurred together.

### 1.2 The most dangerous ambiguity is not continuity vs dialogue alone

Audit judgment after cross-scan:

1. the risk is broader than `v1.6.16` continuity;
2. the same “memory” overloading can collapse at least these distinct families:
   - pack rulebook,
   - pack task-history,
   - runtime dialogue-governance,
   - runtime dialogue-retention,
   - runtime experience-feedback,
   - runtime protocol-feedback,
   - runtime continuity/reentry,
   - runtime memory-absorption quarantine.
3. this means the real debt is a protocol motherline routing problem, not a one-lane local clarification.

### 1.3 `runtime/memory-absorption/**` is the highest-risk semantic trap

Audit judgment:

1. `runtime/memory-absorption/**` is already registered in pack topology/path-governance surfaces.
2. That registration is useful for quarantine/migration, but it becomes dangerous when instances/operators start treating it as a generic active sink.
3. Therefore this family must be frozen as **quarantine/re-materialization only**, never active continuity, dialogue, learning, or protocol-feedback authority.

### 1.4 Declaration keys and gates must stay out of the artifact matrix

Audit judgment:

1. `reject_memory_gate` is a gate, not a sink.
2. `dialogue_governance_contract`, `experience_feedback_contract`, `context_continuity_contract_v1`, and `reentry_brief_consumption_contract_v1` are declaration surfaces, not stored artifact families.
3. Without this distinction, implementations drift into claiming “the contract key is the storage path”, which is semantically wrong.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces landed in this opening package

1. `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
5. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
6. `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`
7. `identity/protocol/IDENTITY_PROTOCOL.md`
8. `identity/protocol/IDENTITY_RUNTIME.md`
9. `README.md`

### 2.2 Inherited protocol-owned owner streams consumed by this opening

1. `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`
2. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
3. `docs/governance/identity-context-continuity-governance-v1.6.16.md`
4. `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`
5. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`

### 2.3 What this stream owns and what it intentionally does not own

1. `v1.6.18` owns only the routing matrix and semantic anti-pollution boundary across already-existing protocol-owned artifact families.
2. It does not reopen the continuity schema, launcher semantics, topology freeze, or learning-loop strengthening semantics.
3. It does not create a new “memory family”.
4. It does not authorize instances to invent new roots or treat non-protocol surfaces as active protocol fallbacks.

## 3) Four-track review checklist

### 3.1 T1 roundtable / internal topology and runtime scan

1. Verify current packs already contain multiple semantically distinct persisted families.
2. Verify those families already sit on different path roots and different contract keys.
3. Verify the missing piece is the shared routing matrix, not absence of pack/runtime structure.

### 3.2 T2 inherited governance streams

1. `v1.6.13` already distinguishes pack-root durable files from runtime subtrees.
2. `v1.6.8` already distinguishes governed runtime path families.
3. `v1.6.16` already distinguishes continuity from raw transcript/memory folklore.
4. `v1.6.17` already distinguishes learning/loopback artifacts from current-turn truth.
5. `v1.6.18` therefore sits above those streams and freezes the cross-family routing matrix.

### 3.3 T3 semantic anti-pollution review

1. `RULEBOOK.jsonl` must not collapse into `runtime/rulebooks/*.jsonl`.
2. `TASK_HISTORY.md` must not collapse into continuity or feedback.
3. `runtime/reports/dialogue-retention/**` and `runtime/state/dialogue-retention/**` must not collapse into dialogue-governance summaries or continuity.
4. `runtime/protocol-feedback/**` must not collapse into learning or dialogue proof.
5. `runtime/memory-absorption/**` must not collapse into any active family.
6. declaration keys/gates must not be misreported as the family outputs themselves.

### 3.4 T4 implementation readiness review

1. Governance must freeze the routing matrix before validators or creator/readiness wiring can enforce it.
2. `rq_051_identity_dialogue_retention_contract_v1` now demonstrates the first machine-consumed family landing for this stream: it checks governed path-family alignment, delivery-hook production, exact snapshot mirroring, and live-thread drift semantics.
3. Future creator/backfill/readiness integration must reuse the same matrix instead of re-deriving family semantics pack by pack.

## 4) Frozen implementation checklist

1. `memory` is non-canonical shorthand and must always be resolved to an exact protocol family name plus fixed path family.
2. The canonical persisted families now frozen for protocol scope are:
   - pack rulebook family,
   - pack task-history family,
   - runtime dialogue-retention family,
   - runtime dialogue-governance family,
   - runtime experience-feedback family,
   - runtime protocol-feedback family,
   - runtime continuity/reentry family,
   - runtime memory-absorption family.
3. `runtime/memory-absorption/**` remains quarantine/re-materialization only.
4. Declaration keys and gates remain control-plane declarations, not sinks.
5. Any future new protocol-owned persisted family requires a later governed stream rather than silent introduction under “memory” wording.

## 5) Machine-consumer and whole-matrix routing closure landed

The stream has now moved beyond a docs-only opening. Audit-accepted machine landing in this round is:

1. `scripts/identity_dialogue_retention_common.py`, `scripts/run_identity_dialogue_retention_guard_runtime.py`, and `scripts/run_identity_delivery_runtime_hooks.py` define the protocol-owned raw dialogue retention bridge instead of leaving raw transcript handling to per-pack folklore.
2. `scripts/validate_identity_dialogue_retention.py` now fail-closes on missing delivery-hook installation, missing runtime roots, broken snapshot mirror exactness, broken sync receipts, or broken supplement/state joins.
3. `scripts/ci/run_identity_dialogue_retention_probes_ci.sh` proves the bridge on a fixture pack and verifies coexistence with continuity tick/post-recover semantics.
4. `scripts/create_identity_pack.py`, `scripts/repair_contract_backfill.py`, `scripts/release_readiness_check.py`, `scripts/ci/run_required_runtime_gates_ci.sh`, `scripts/validate_required_contract_coverage.py`, and `scripts/required_gate_bundle_runner.py` now consume the same family rather than treating raw dialogue retention as docs-only guidance.
5. `scripts/validate_identity_artifact_family_routing.py` now fail-closes on missing routing-contract coverage, `reject_memory_gate` drift, pack rulebook/task-history collisions, protocol-feedback root drift, continuity/reentry anchor drift, and memory-absorption active-path leakage while explicitly deferring family-specific deep semantics to their inherited validator lanes.
6. `scripts/ci/run_identity_artifact_family_routing_probes_ci.sh` now proves positive whole-matrix pass, missing-contract fail-close, backfill repair, and cross-family collision fail-close on a fixture pack.
7. `scripts/create_identity_pack.py`, `scripts/repair_contract_backfill.py`, `scripts/release_readiness_check.py`, `scripts/ci/run_required_runtime_gates_ci.sh`, `scripts/validate_required_contract_coverage.py`, and `scripts/required_gate_bundle_runner.py` now consume the same `rq_052` routing row instead of leaving whole-matrix routing as governance prose only.
8. `scripts/required_gate_bundle_runner.py --target-name identity_artifact_family_routing` now preserves target-probe compatibility mode under the same registry lineage: `run_id` and profile binding remain enforced, but full-bundle ingress wrapper / unique-entry receipt obligations no longer incorrectly fail-close isolated routing probes.
9. Current live proof breadth is no longer fixture-only:
   - the current weixinstore workspace-local runtime catalog replays `PASS_REQUIRED` on `scripts/validate_identity_artifact_family_routing.py` for all four active runtime identities: `base-repo-audit-expert-v3`, `custom-creative-ecom-analyst`, `base-repo-architect`, and `base-repo-closure-orchestrator`;
   - `base-repo-closure-orchestrator` no longer carries the earlier inherited `rq_051_identity_dialogue_retention_contract_v1` residual on the routed lane, so the routing closeout now reflects current live truth instead of preserving stale inherited-red prose;
   - `base-repo-architect` remains green on `rq_052` while its optional dialogue-retention family stays `SKIPPED_NOT_REQUIRED`, confirming the routing lane is not overreaching into optional-family debt.

## 6) Closure state

Audit interpretation after cross-check:

1. the routing matrix is semantically frozen;
2. the first family-specific machine lane (`rq_051`) remains live and reusable;
3. the whole-matrix routing lane (`rq_052`) is now machine-landed and consumed by creator/backfill/readiness/CI/required-gates surfaces;
4. `ISSUE-032` is therefore closed without reopening semantic ownership or collapsing the eight families back into one bucket;
5. future new families still require governed stream openings rather than silent attachment under generic “memory”.

## 7) Accepted role split for whole-matrix closeout

Audit acceptance in this round also freezes the execution boundary so later follow-on work does not drift:

1. semantic ownership remains with `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` and the inherited owner streams it explicitly references;
2. execution closeout owns the bounded whole-matrix machine path, live replay breadth, truth-sync maintenance, and any future inherited-family residual triage so long as it stays inside the frozen routing matrix;
3. execution closeout must return to semantic-owner review before shipping any change that adds/renames a family, repoints a canonical root, changes canonical producer/consumer roles, relaxes the `memory` anti-pollution boundary, promotes `runtime/memory-absorption/**` back onto an active success path, or uses compatibility/backstop shortcuts to hide inherited-family failures;
4. audit verifies whether the closeout extends the frozen matrix faithfully and whether truth surfaces stay synchronized; audit does not become a replacement semantic owner;
5. raw dialogue retention remains the first machine-landed family, while `rq_052` now closes the routing matrix without becoming a replacement semantic owner for the eight families;
6. if a future routed red is caused by an inherited family-owner validator, audit interprets it as execution-closeout evidence debt unless the proposed fix would cross one of the semantic-owner boundaries above.

Frozen audit interpretation:

- the semantic owner problem is correctly protocol-owned;
- the first machine-consumed family landing is real and reusable;
- whole-matrix routing enforcement is now landed on the same stream rather than reinvented pack by pack.

## 8) Non-goals frozen for audit

1. This opening does not claim a new generic memory subsystem exists.
2. This opening does not claim `runtime/memory-absorption/**` is an active success-path sink.
3. This opening does not reopen `v1.6.13`, `v1.6.16`, or `v1.6.17` semantics.
4. This opening does not pull non-protocol product/session/history paths into protocol scope.
