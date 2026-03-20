# Identity Instance Script Orchestration Roadmap (2026-03-21)

Status: Active roadmap guidance  
Layer: protocol  
Scope: architecture roadmap for route -> instance scripts -> receipt contract modeling after issue-register closure

Execution mode: roadmap-only governance document. This file defines the next architecture lane and its non-reopen boundary; it does not declare a new correctness failure by itself.

## 0) State interpretation guard (mandatory)

1. This document is not an issue register and must not be used as evidence that `ISSUE-001` through `ISSUE-023` are reopened.
2. Current correctness status still anchors to the active machine gates and current issue register surfaces.
3. Current-state interpretation for this roadmap must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. This roadmap inherits already-frozen boundaries:
   - `v1.6.12` owns native-chat bootstrap and promotion semantics,
   - `v1.6.13` owns canonical pack-root topology,
   - `v1.6.14` owns launcher/install/startup governance.
5. Therefore this roadmap may extend architecture, but it must not reinterpret those streams as incomplete correctness closure.

## 1) Why this lane exists

1. `v1.6.13` froze where instance-owned helper execution lives: pack-root `scripts/`.
2. What remains under-modeled is how current-task routing, pack-local scripts, and receipt families should join into one declarative contract.
3. Today the repository has working pieces:
   - governed pack-root scripts,
   - route and gate infrastructure,
   - several receipt-producing validators and emitters,
   - proof-pack examples showing entry-owned and exit-owned helper execution.
4. What it lacks is a single architecture contract for:
   - which scripts a route may invoke,
   - what preconditions or gate tuples those scripts require,
   - what receipt families must exist after execution,
   - how creator/update/readiness surfaces validate that join consistently.

## 2) Already-closed prerequisites

1. Pack-root executable home is already frozen by `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`.
2. Launch-context parity for active script entry is already closed and machine-gated.
3. Native-chat headstamp correctness is already closed on the `v1.6.12` standard lane.
4. Therefore this roadmap starts from an existing stable base rather than from an open defect pool.

## 3) The architecture gap, precisely stated

1. A pack can be topology-ready while still lacking a formal route-to-script declarative join.
2. A pack can execute scripts and generate receipts without a standardized receipt-family contract.
3. Reviewers can currently tell these states apart by reasoning, but the contract is not yet first-class.
4. That gap creates three long-term risks:
   - orchestration drift across instances,
   - receipt-family inconsistency,
   - rising control-plane complexity when new helper paths are added without a common model.

## 4) Target contract families

### 4.1 Route-to-script declarative join

1. Future lanes should model route-to-script binding as explicit pack/runtime contract rather than implicit script discovery.
2. The target surface is a pack-local/current-task contract layer that can answer:
   - which primary scripts serve a route,
   - which fallback scripts are allowed,
   - which work-layer / source-layer tuple is required,
   - which route may remain observation-only versus mutation-capable.
3. Candidate future contract keys may include names like:
   - `instance_script_orchestration_contract_v1`
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
4. These names are roadmap candidates, not frozen motherline semantics yet.

### 4.2 Receipt-family standardization

1. Future lanes should standardize what counts as completion evidence for instance-owned script execution.
2. The target model should separate:
   - route admission receipt,
   - execution receipt,
   - emit/visible-surface receipt,
   - recovery or replay receipt.
3. Receipt families should be explicit enough that creator/update/readiness tooling can validate them without bespoke per-script logic.
4. Candidate future contract keys may include names like:
   - `instance_script_receipt_family_v1`
   - `required_execution_receipts`
   - `route_completion_receipts`

### 4.3 Validator and creator integration

1. Future lanes should validate the orchestration join through shared validators, not by open-coded per-pack checks.
2. Candidate future validator surfaces may include:
   - `scripts/validate_instance_script_orchestration_contract.py`
   - `scripts/validate_instance_script_receipt_family.py`
   - `scripts/validate_route_script_receipt_join.py`
3. Creator/update/readiness surfaces should consume those contracts through shared wiring rather than inventing new ad hoc paths.

## 5) Phased landing model

### Phase A - contract freeze

1. Freeze the route-to-script and receipt-family schemas.
2. Choose whether the owning stream is a dedicated `v1.6.x` lane or a roadmap-to-stream promotion from this document.
3. Keep this phase non-reopening unless a live correctness gate is actually falsified.

### Phase B - validator landing

1. Land the shared validators for route-to-script and receipt-family consistency.
2. Backfill proof-pack examples first.
3. Only then promote the new contract into creator/update/readiness required checks.

### Phase C - orchestration wiring

1. Route readiness, creator/update, and pack validation should consume the same contract family.
2. Receipt families should become machine-readable and reusable across packs.
3. At this point, architecture debt starts shrinking without redefining already-closed correctness lanes.

## 6) Explicit non-goals

1. This roadmap does not reopen `v1.6.12` headstamp semantics.
2. This roadmap does not reopen `v1.6.13` topology semantics.
3. This roadmap does not imply that every pack must immediately adopt a new script manifest before the contract lands.
4. This roadmap does not classify dirty worktree or workbook freshness as orchestration failures.
5. This roadmap does not authorize hardcoded per-pack script paths as the long-term answer.

## 7) Review guidance

1. If an instance is topology-ready but lacks declarative route-to-script binding, classify that as architecture debt by default.
2. If a future route-to-script contract lands and then a machine gate regresses, only then may it become correctness debt.
3. If receipt families vary across packs today, classify that as standardization debt, not a reopen of topology closure.
4. Reviewers must preserve the distinction between:
   - topology,
   - orchestration,
   - receipt standardization,
   - release hygiene.

## 8) Immediate next-step recommendation

1. Promote this roadmap into a dedicated implementation lane only when owner bandwidth is ready.
2. Start with the schema and validator layer, not with per-pack script rewrites.
3. Keep the shared post-closure governance mode as the parent interpretation rule while this architecture lane remains open.
