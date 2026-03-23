# Protocol Remediation Audit Ledger (v1.6.18 artifact-family routing stream)

Status: Active (protocol-owned semantic/path freeze opened 2026-03-23; workbook routing + semantic registry truth-sync + shared validator follow-on remain open)  
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
2. runtime experience-feedback families exist:
   - `runtime/examples/base-repo-closure-orchestrator-experience-feedback-sample.json`
   - `runtime/logs/feedback/*.json`
3. runtime protocol-feedback families exist:
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
   - `runtime/protocol-feedback/outbox-to-protocol/*.json`
4. continuity families are already declared:
   - `context_continuity_contract_v1`
   - `reentry_brief_consumption_contract_v1`
   - canonical continuity roots under `runtime/reports/context-continuity/` and `runtime/state/context-continuity/`
5. dialogue-governance is already a distinct contract family even while optional:
   - `dialogue_governance_contract.required=false`
6. `reject_memory_gate` is already required.

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
3. `runtime/protocol-feedback/**` must not collapse into learning or dialogue proof.
4. `runtime/memory-absorption/**` must not collapse into any active family.
5. declaration keys/gates must not be misreported as the family outputs themselves.

### 3.4 T4 implementation readiness review

1. Governance must freeze the routing matrix before validators or creator/readiness wiring can enforce it.
2. The later validator must check path-family alignment, not just file existence.
3. Future creator/backfill/readiness integration must reuse the same matrix instead of re-deriving family semantics pack by pack.

## 4) Frozen implementation checklist

1. `memory` is non-canonical shorthand and must always be resolved to an exact protocol family name plus fixed path family.
2. The canonical persisted families now frozen for protocol scope are:
   - pack rulebook family,
   - pack task-history family,
   - runtime dialogue-governance family,
   - runtime experience-feedback family,
   - runtime protocol-feedback family,
   - runtime continuity/reentry family,
   - runtime memory-absorption family.
3. `runtime/memory-absorption/**` remains quarantine/re-materialization only.
4. Declaration keys and gates remain control-plane declarations, not sinks.
5. Any future new protocol-owned persisted family requires a later governed stream rather than silent introduction under “memory” wording.

## 5) Opening-state closure target

This stream is not complete merely because the governance doc exists. The remaining protocol-owned follow-on work is narrow and explicit:

1. workbook routing of this ambiguity as a protocol issue;
2. semantic-term registry truth-sync;
3. protocol/runtime/README truth-sync to one compact matrix;
4. later shared validator and creator/readiness consumption.

Frozen audit interpretation:

- the semantic owner problem is now correctly identified and protocol-owned;
- later machine enforcement should extend this stream rather than reinvent the family boundaries in each validator.

## 6) Non-goals frozen for audit

1. This opening does not claim a new generic memory subsystem exists.
2. This opening does not claim `runtime/memory-absorption/**` is an active success-path sink.
3. This opening does not reopen `v1.6.13`, `v1.6.16`, or `v1.6.17` semantics.
4. This opening does not pull non-protocol product/session/history paths into protocol scope.
