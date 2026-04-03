# Identity Post-Closure Governance Mode (v1.6.14)

Status: Active guidance (2026-03-21)  
Layer: protocol  
Scope: post-issue governance mode after `ISSUE-001` through `ISSUE-023` closure

Execution mode: governance interpretation layer for how to handle remaining debt without misreporting closed correctness lanes as reopened.

## 0) State interpretation guard (mandatory)

1. This document does not reopen any `v1.6.x` stream semantics by itself.
2. Current correctness judgment must still anchor to machine-gated stream owners such as:
   - `scripts/validate_native_chat_bootstrap_entry_stream.py`
   - `scripts/validate_cli_catalog_default_semantics.py`
   - `scripts/docs_command_contract_check.py`
   - `scripts/validate_issue_register_consistency.py`
3. Current-state interpretation for this governance mode must anchor to:
   - `identity/protocol/mappings/workbook-registry.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. `ISSUE-001` through `ISSUE-023` being `CLOSED` means the governed active issue register currently has no live correctness-red rows on that lane.
5. Closed issue registers do not imply:
   - clean workspace freeze,
   - complete architecture implementation roadmap,
   - low control-plane complexity,
   - zero maintenance cost.
6. Therefore reviewers must classify residual work by debt family before opening a new issue or declaring a closed stream reopened.

## 1) Why this governance mode is required

1. The repository has moved past the phase where the dominant risk was undiscovered live correctness bugs in the already-audited `ISSUE-001` to `ISSUE-023` family.
2. The dominant risk now is classification drift:
   - enhancement work being mislabeled as semantic regression,
   - release hygiene being mislabeled as protocol correctness failure,
   - historical workbook text being misread as current machine truth,
   - control-plane growth being mistaken for a new defect class rather than a maintainability problem.
3. Without a post-closure governance mode, saturation-style issue hunting has poor marginal return and tends to create false reopens.
4. This document freezes the interpretation model needed to keep later work rigorous without collapsing every residual into the old issue-hunt lane.
5. The canonical cross-stream issue workbook now lives inside `docs/workbook/`, not in any outer workspace evidence directory.
6. Naming discipline stays split by governance grain:
   - `workbook = X.X`
   - `governance/review = X.X.X`

## 2) Three-layer debt taxonomy (frozen)

### 2.1 Correctness closure lane

1. This lane covers active machine-gated correctness invariants.
2. Examples:
   - headstamp order / tuple truth / fail-close semantics,
   - launch-context parity,
   - docs executable path correctness on governed surfaces,
   - current issue register consistency.
3. A correctness item may reopen only when at least one of the following is true:
   - an existing machine gate regresses from green to red on an already-governed surface,
   - the same semantic invariant fails on a newly promoted active surface,
   - a prior stop-condition is falsified by replay on the active owner lane.
4. Dirty worktree, stale historical prose, missing future implementation, or topology/roadmap gaps by themselves do not reopen correctness closure.

### 2.2 Architecture roadmap lane

1. This lane covers real platform gaps that are not current correctness failures.
2. Examples:
   - route -> instance scripts -> receipt declarative join,
   - execution receipt family standardization,
   - `v1.6.14` launcher implementation landing,
   - later orchestration or simplification streams built on already-closed invariants.
3. Architecture gaps are governed as versioned enhancement streams, contracts, or roadmap items.
4. They must not be backported into the issue register as reopened correctness debt unless they actually break an existing governed invariant.

### 2.3 Release hygiene and simplification lane

1. This lane covers release readiness, workspace cleanliness, workbook freshness, and maintenance cost.
2. Examples:
   - dirty worktree preventing clean freeze,
   - workbook stale counts or historical/open-state ambiguity,
   - validator surface sprawl,
   - high parity-recheck cost after routine changes.
3. These are real debts, but they are release-grade or maintenance-grade, not correctness-grade, unless they directly falsify a live machine invariant.
4. Hygiene debt should be closed through cleanup batches, consistency validators, and simplification work, not by reopening semantically closed streams.

## 3) Reopen boundary (strict)

1. Do reopen a closed issue family when:
   - the active machine gate for that family reproduces a prior red condition,
   - the same owner lane reproduces the same root cause on current governed inputs,
   - or the frozen stop-condition is directly falsified.
2. Do not reopen a closed issue family when:
   - a future enhancement is still unimplemented,
   - a workspace remains dirty,
   - a workbook retains trace text from an older round,
   - a release marker, topology lane, or instance-owned artifact needs separate cleanup,
   - control-plane complexity feels high but no governed invariant has failed.
3. When in doubt, classify first:
   - correctness closure,
   - architecture roadmap,
   - release hygiene / simplification.
4. Only the first category is allowed to reopen an already-closed issue family by default.

## 4) Governance operating mode after issue closure

### 4.1 Event-triggered correctness checks

1. Keep correctness validation event-triggered and lane-scoped.
2. Run the relevant existing machine gates when:
   - a governed active surface changes,
   - a stream owner document changes,
   - a current-pointer mapping changes,
   - a launch-context-sensitive command surface changes.
3. Do not return to open-ended saturation sweeps whose main output is stale-text rediscovery.

### 4.2 Lane-driven enhancement work

1. Route non-bug enhancements into explicit versioned lanes.
2. At current state, the highest-value architecture lanes are:
   - `v1.6.15` route-to-script declarative join,
   - `v1.6.15` instance script orchestration contract,
   - `v1.6.15` execution receipt family standardization,
   - `v1.6.14` launcher implementation landing.
3. The active governance anchor for the first three items is:
   - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
4. The roadmap companion remains:
   - `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md`
5. These lanes may add validators and docs, but they must inherit rather than reinterpret already-closed correctness boundaries.

### 4.3 Release hygiene discipline

1. Track clean-freeze readiness separately from correctness closure.
2. Keep workbook freshness machine-checked.
3. Prefer shared validators over one-off prose edits.
4. Prefer simplification and consolidation when a new guard duplicates an existing semantic owner.
5. Keep the authoritative workbook pair fixed to:
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`

## 5) Current remaining deep debts, properly classified

### 5.1 Architecture-grade debt

1. `v1.6.15` now freezes route -> instance-script -> receipt as a first-class contract family, so the remaining debt is implementation landing rather than architecture ambiguity.
2. The next major protocol/platform gap is therefore shared validator + creator/readiness + capability-activation wiring for that frozen `v1.6.15` contract, not a reopen of `v1.6.12` or the closed issue register.

### 5.2 Release-grade debt

1. The repository and workspace may still be dirty even when issue registers are green.
2. Clean freeze therefore remains an explicit release hygiene task rather than a correctness verdict.

### 5.3 Maintenance-grade debt

1. Control-plane surface area is now large enough that validator sprawl and parity-recheck cost matter.
2. Future work should include simplification, consolidation, and clearer current-authoritative-source boundaries.

## 6) Owner split after issue closure

1. Protocol owner:
   - owns correctness gates,
   - owns new architecture contracts,
   - owns shared simplification infrastructure.
2. Audit owner:
   - owns workbook accuracy,
   - owns issue register classification discipline,
   - owns replay-based acceptance of reopened correctness claims.
3. Instance owner:
   - owns pack-local runtime debt,
   - owns instance migration completeness,
   - owns non-protocol stale evidence unless a protocol gate proves otherwise.
4. Release owner:
   - owns clean freeze,
   - owns hygiene blocking judgments,
   - owns release bundle readiness once correctness closure is already green.

## 7) Required machine guardrails for this mode

1. `scripts/validate_issue_register_consistency.py` must stay green:
   - issue table and audit workbook statuses agree,
   - historical snapshot language does not silently override current closed rows,
   - recorded docs-checker counts match the live checker output,
   - and the active workbook pair resolves through `identity/protocol/mappings/workbook-registry.current.yaml` into `docs/workbook/`.
2. Stream-owner validators must remain the source of truth for correctness:
   - `scripts/validate_native_chat_bootstrap_entry_stream.py`
   - `scripts/validate_cli_catalog_default_semantics.py`
   - `scripts/docs_command_contract_check.py`
3. New lanes must add their own contracts instead of smuggling new scope into an already-closed issue family.

## 8) Frozen review guidance

1. Do not use “there is still technical debt” as shorthand for “a closed correctness stream reopened.”
2. Do not let dirty worktree state masquerade as protocol semantic failure.
3. Do not let missing enhancement implementation masquerade as issue-register incompleteness.
4. Do not treat historical workbook snapshots as current status when the issue table and machine gates say otherwise.
5. Do treat architecture gaps, hygiene blockers, and complexity growth as real work; just classify them into the correct lane.

## 9) Immediate next-step guidance

1. Keep issue hunting closed by default unless a live machine gate actually regresses.
2. Move next major effort into architecture lanes:
   - `v1.6.15` route-to-script declarative join,
   - `v1.6.15` receipt-family modeling,
   - `v1.6.14` launcher implementation landing.
3. Use `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md` as the active non-reopen architecture anchor for route/script/receipt modeling.
4. Keep `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md` only as the design-history companion.
5. Run release hygiene as a separate owner lane:
   - clean freeze,
   - workbook freshness,
   - simplification / consolidation of validators and current-authoritative-source boundaries,
   - governed outer runtime summary lifecycle discipline, including `scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh`, `scripts/ci/run_release_readiness_summary_binding_probes_ci.sh`, and `scripts/ci/run_release_readiness_continuation_probes_ci.sh`.
