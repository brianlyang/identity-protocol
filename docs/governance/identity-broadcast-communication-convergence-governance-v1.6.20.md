# Identity Broadcast Delivery and Communication Transport Convergence Governance (v1.6.20)

Status: Active (`ISSUE-038` closed on 2026-03-24; dedicated broadcast-delivery and identity-communication-transport convergence lanes are now protocol-owned, machine-consumed, and fleet-green across the workspace runtime catalog)
Layer: protocol
Scope: additive convergence stream for active identity adoption of protocol broadcast delivery and identity communication transport across host-gateway broadcast projection, handoff/collaboration, protocol-feedback reply/inbox/atomic, and shared fleet migration closure
Execution mode: topic-level canonical SSOT for v1.6.20 broadcast-delivery / communication-transport convergence governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_broadcast_delivery_communication_transport_convergence`.
2. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md` remains the semantic owner for the host gateway wrapper/unique-channel boundary and the upstream protocol broadcast source.
3. `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md` remains the semantic owner for fixed runtime roots and protocol-generated runtime boundary semantics.
4. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` remains the semantic owner for protocol-feedback atomic emit, reply/inbox channels, and collaboration-trigger family semantics.
5. `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md` remains the semantic owner for canonical identity-pack topology and pack-local `scripts/` ownership.
6. `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` remains the semantic owner for artifact-family routing; `identity_communication_transport` is not a new artifact family.
7. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
8. Scope is intentionally narrow:
   - `ASB16-RQ-053` dedicated broadcast-delivery adoption lane;
   - `ASB16-RQ-054` aggregate identity-communication-transport convergence lane;
   - shared migration closure and shared convergence execution only.
9. Scope explicitly excludes:
   - business routing policy,
   - vendor ranking or search heuristics,
   - pack-local exception logic,
   - narrowing the transport topic to strict identity-to-identity-only messaging.
10. The no-downgrade motherline remains frozen: this stream must close through shared creator/backfill/runner/validator infrastructure, not compatibility backstops, validator loosening, or manual pack patching.

## 1) Why v1.6.20 is required

1. Protocol broadcast source semantics were already landed at the host-gateway layer, but active runtime identities were still uneven in consuming the dedicated broadcast-delivery contract and runtime state projection.
2. Agent handoff, collaboration-trigger, protocol-feedback reply/inbox, protocol-feedback atomic emit, and protocol broadcast already existed as component lanes, but there was no protocol-owned aggregate convergence executor or fleet closure checker for the full transport surface.
3. As a result, owner semantics could be green while fleet adoption remained red.
4. `v1.6.20` closes that gap by adding:
   - dedicated broadcast-delivery validator + runner + closure checker,
   - dedicated communication-transport validator + runner + closure checker,
   - creator/update auto-repair entry wiring,
   - workspace fleet convergence proof.

## 2) Frozen semantic boundary

### 2.1 `rq_053_identity_broadcast_delivery_contract_v1`

1. Broadcast delivery is the dedicated lane that projects the host-gateway broadcast source into per-pack runtime visibility/state and optional delivery receipts.
2. It is not the reply channel, not the inbox channel, not protocol-feedback atomic emit, and not a learning/continuity sink.
3. Delivery sync may materialize visibility/read state, but it must not silently acknowledge pending critical broadcasts on behalf of the instance/operator.
4. Broadcast delivery remains bounded to delivery/projection truth only; upstream broadcast source ownership stays with the host-gateway stream.

### 2.2 `rq_054_identity_communication_transport_contract_v1`

1. Identity communication transport is the aggregate convergence surface across:
   - agent handoff,
   - collaboration trigger,
   - protocol-feedback reply channel,
   - protocol-feedback inbox channel,
   - protocol-feedback atomic emit,
   - broadcast delivery.
2. It is not strict identity-to-identity-only messaging.
3. It is not a new semantic owner replacing those component contracts.
4. It is not a fallback sink, not a memory bucket, and not a new artifact family.
5. A green transport state therefore means the aggregate lane has consumed the required component contracts plus bounded live bootstrap proof; it does not mean the component-owner streams were semantically reopened.

### 2.3 Shared convergence execution model

1. `scripts/run_identity_communication_transport.py` is the shared convergence executor for this stream.
2. Canonical bootstrap sequence:
   - broadcast-delivery sync,
   - protocol-feedback atomic emit bootstrap,
   - aggregate validator replay.
3. Contract backfill may restore missing/wrong contract surfaces, but live convergence is not complete until the shared executor replays the bounded bootstrap steps and `scripts/validate_identity_communication_transport.py` returns `PASS_REQUIRED`.
4. This execution model is protocol-owned shared infrastructure, not a per-pack script recipe.

## 3) Shared implementation surfaces

Shared protocol-owned surfaces landed in this stream:

1. `scripts/identity_broadcast_delivery_common.py`
2. `scripts/run_identity_broadcast_delivery.py`
3. `scripts/validate_identity_broadcast_delivery.py`
4. `scripts/check_identity_broadcast_migration_closure.py`
5. `scripts/identity_communication_transport_common.py`
6. `scripts/run_identity_communication_transport.py`
7. `scripts/validate_identity_communication_transport.py`
8. `scripts/check_identity_communication_transport_closure.py`
9. `scripts/ci/run_identity_broadcast_delivery_probes_ci.sh`
10. `scripts/ci/run_identity_communication_transport_probes_ci.sh`
11. `scripts/create_identity_pack.py`
12. `scripts/repair_contract_backfill.py`
13. `scripts/identity_creator.py`
14. `scripts/required_gate_bundle_runner.py`
15. `scripts/ci/run_required_runtime_gates_ci.sh`
16. `scripts/release_readiness_check.py`

## 4) Machine closure landed

### 4.1 ASB16-RQ-053 broadcast-delivery machine closure landed

1. `scripts/validate_identity_broadcast_delivery.py` now fail-closes on missing dedicated contract adoption, broken runtime gateway/source projection, broken runtime state, or broken projection parity.
2. `scripts/run_identity_broadcast_delivery.py` now provides the shared delivery-sync executor instead of forcing per-pack/manual replay.
3. `scripts/check_identity_broadcast_migration_closure.py` now scans active runtime identities and fail-closes lingering adoption drift at the workspace fleet level.
4. `scripts/create_identity_pack.py` and `scripts/repair_contract_backfill.py` now materialize/restore the dedicated broadcast-delivery contract rather than relying on host-gateway structural presence alone.
5. `scripts/ci/run_identity_broadcast_delivery_probes_ci.sh` proves the positive sync path, the missing-contract fail-close path, the shared backfill repair path, and the closure-checker green path.
6. `scripts/identity_broadcast_delivery_common.py`, `scripts/validate_identity_broadcast_delivery.py`, and `scripts/run_identity_broadcast_delivery.py` now emit a bundle-compatible required-contract projection (`required_contract`, canonical contract identity, and shared evidence reference) so `scripts/required_gate_bundle_runner.py` can consume `ASB16-RQ-053` without special-casing or validator loosening.
7. `scripts/execute_identity_upgrade.py` now forwards explicit actor context into `scripts/validate_work_layer_gate_set_routing.py` during live replay, preventing false `IP-LAYER-GATE-007` lane-gate failures when the owning identity is correctly bound to an active protocol lane lock.

### 4.2 ASB16-RQ-054 identity-communication-transport machine closure landed

1. `scripts/validate_identity_communication_transport.py` now validates the aggregate transport surface as one protocol-owned convergence row.
2. `scripts/identity_communication_transport_common.py` now fail-closes on missing component contracts, missing runtime roots, missing convergence executor wiring, incomplete bootstrap-step declaration, or failing component validator projections.
3. `scripts/run_identity_communication_transport.py` now provides the shared convergence executor that performs broadcast sync, protocol-feedback atomic bootstrap emission, and aggregate transport replay in one bounded lane.
4. `scripts/check_identity_communication_transport_closure.py` now scans active runtime identities and fail-closes fleet-level adoption drift.
5. `scripts/create_identity_pack.py` and `scripts/repair_contract_backfill.py` now restore the aggregate contract with:
   - canonical validator,
   - canonical convergence executor,
   - canonical migration-closure checker,
   - canonical component-contract set,
   - canonical runtime-root set,
   - canonical live-bootstrap-step set.
6. `scripts/ci/run_identity_communication_transport_probes_ci.sh` now proves the missing-contract fail-close lane, the shared backfill repair lane, the shared convergence executor lane, the missing-runtime-root fail-close lane, and the closure-checker green lane.

## 5) Live fleet convergence proof

1. Direct runtime replay on `base-repo-audit-expert-v3` now returns `PASS_REQUIRED` for `scripts/run_identity_communication_transport.py`, including:
   - `broadcast_sync_executor_status=PASS_REQUIRED`,
   - `atomic_emit_bootstrap_status=PASS_REQUIRED`,
   - `transport_projection_status=PASS_REQUIRED`.
2. The same shared repair + convergence executor path was then replayed on the remaining workspace runtime identities:
   - `custom-creative-ecom-analyst`
   - `base-repo-architect`
   - `base-repo-closure-orchestrator`
3. `python3 scripts/check_identity_broadcast_migration_closure.py --catalog ../.identity/catalog.local.yaml --workspace-runtime-only --json-only` now returns `PASS_REQUIRED`.
4. `python3 scripts/check_identity_communication_transport_closure.py --catalog ../.identity/catalog.local.yaml --workspace-runtime-only --json-only` now returns `PASS_REQUIRED`.
5. Closure is therefore no longer docs-only or owner-only; it is live fleet-green on the active workspace runtime catalog.

## 6) Closed-state stop condition

`ISSUE-038` is closed only because all of the following now hold together:

1. dedicated broadcast-delivery and communication-transport contracts are machine-restorable through shared backfill;
2. dedicated convergence executors exist and are reusable;
3. dedicated closure checkers exist and are wired into creator/update/gates/readiness;
4. dedicated probe suites prove positive + negative + repair lanes;
5. the workspace runtime fleet has consumed the stream and replays green;
6. the fix is shared infrastructure, not manual pack editing or validator softening.

## 7) Non-goals and forbidden shortcuts

1. Do not relabel communication transport as strict identity-to-identity-only messaging.
2. Do not collapse broadcast delivery into the reply/inbox/atomic lanes.
3. Do not treat `runtime/protocol-feedback/**` as a memory/continuity substitute.
4. Do not loosen transport validation to hide missing component adoption.
5. Do not use compatibility/backstop semantics to carry lagging identities.
6. Do not hand-edit instance packs as the final closure mechanism; creator/backfill/runner/closure-checker infrastructure is the canonical path.
