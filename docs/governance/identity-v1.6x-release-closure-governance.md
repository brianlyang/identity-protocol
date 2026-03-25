# Identity v1.6.x Release Closure Governance

Status: Active static closure boundary (2026-03-25)
Layer: protocol
Scope: final version-boundary governance for closing `1.6.x` on root / machine / runtime terms without silently exporting current-universe closure debt into `1.7.x`
Execution mode: canonical static SSOT for `1.6.x` release-closure interpretation and `1.7.x` admission boundary.

## 0) State interpretation guard (mandatory)

1. This document is a release-closure governance surface, not a replacement semantic owner for any individual `v1.6.x` stream.
2. Current-state judgment for this boundary must anchor to:
   - identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md
   - identity/protocol/IDENTITY_PROTOCOL.md
   - identity/protocol/IDENTITY_RUNTIME.md
   - identity/protocol/mappings/stream-doc-registry.current.yaml
   - identity/protocol/mappings/contract-binding.current.yaml
   - identity/protocol/mappings/control-plane-status.current.yaml
   - identity/protocol/mappings/control-plane-budget.current.yaml
   - identity/protocol/mappings/workbook-registry.current.yaml
   - docs/workbook/protocol-issue-register-v1.6.md
   - docs/workbook/protocol-deep-audit-workbook-v1.6.md
3. This document freezes the version-boundary interpretation for `1.6.x`; it does **not** by itself declare a tag issuance, bypass stream owners, or replace release gates/readiness validators.
4. `1.6.x` closure means current-protocol-universe debt is closed on the `1.6.x` side rather than narratively deferred into `1.7.x`.
5. `1.7.x` admission is future-facing only after `1.6.x` is treated as root-closed, machine-closed, and runtime-closed on the problems that already belong to the current protocol universe.
6. The authoritative current workbook horizon for this release boundary is `ISSUE-001` through `ISSUE-039`; if that horizon moves, this boundary doc must truth-sync instead of freezing a stale issue universe.
7. The canonical derived summary surface for this boundary is `docs/release/identity-v1.6x-release-closure-summary.md`; it may compress this law for handoff, but it must not replace this governance surface, current runtime verdict surfaces, or fleet-scope closure matrices.
8. Historical `docs/release/*.md` surfaces must remain explicitly archival and must not silently reclaim current release-boundary authority.

## 1) Why this boundary must be frozen

1. The bottom theory in identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md already fixes source-order:
   - bottom theory -> constitutions -> root contracts -> machine-consumed enforcement surfaces.
2. Under that order, a new version line must not become a dumping ground for already-known closure debt from the current protocol universe.
3. If `1.6.x` leaves current-universe closure debt intentionally open and rebrands it as `1.7.x` work, the system loses:
   - semantic boundary clarity,
   - machine adjudication clarity,
   - release-history truth,
   - future-version cleanliness.
4. Therefore `1.6.x` must close what it already discovered about the current identity-protocol universe before `1.7.x` is allowed to define genuinely new futures.

## 2) Three release-closure classes for `1.6.x`

### 2.1 Root-closed

`1.6.x` is root-closed when:

1. the relevant stream semantics are derivable from the philosophy root and constitutional root rather than only from local review prose;
2. stream-local interpretations do not reverse-author the protocol root;
3. root corpus / ontology / gateway / no-downgrade boundaries stay explicit.

### 2.2 Machine-closed

`1.6.x` is machine-closed when:

1. known issues are no longer only human-recognized;
2. they are projected into machine-consumed contracts, mappings, validators, probes, CI, and required-gate/readiness surfaces;
3. the machine can fail-close the relevant drift without pack-local narrative rescue.

### 2.3 Runtime-closed

`1.6.x` is runtime-closed when:

1. closure is not asserted from hermetic proof alone;
2. creator / backfill / producer / consumer lanes are all shared and protocol-owned where needed;
3. real runtime identities can replay the closure on the governed lane.

## 3) Frozen release-boundary law

### 3.1 What must stay inside `1.6.x`

The following stay in `1.6.x` until closed:

1. any already-discovered current-universe semantic gap whose owner lane already exists in the `1.6.x` protocol world;
2. any gap that can be closed by additive shared infrastructure on top of already-landed owners;
3. any gap whose real fix is still creator/backfill/producer/consumer wiring rather than a new protocol ontology;
4. any gap that would otherwise force `1.7.x` to inherit residual `1.6.x` release debt.

### 3.2 What must **not** be misreported as `1.7.x`

The following do **not** justify version rollover by themselves:

1. hermetic proof without real runtime closure;
2. pack-local workaround desire;
3. historical wording that predates newer machine closure;
4. control-plane sprawl that is still closing the current protocol universe;
5. an already-open `1.6.x` stream that still has shared-infrastructure closure left to land.

### 3.3 What may legitimately enter `1.7.x`

A topic is a legitimate `1.7.x` starter only when it primarily requires one or more of:

1. a genuinely new protocol object class;
2. a genuinely new relation/topology between already-legal objects;
3. a genuinely new machine-world capability boundary not already implied by the current `1.6.x` owner lanes.

## 4) Version-boundary interpretation for late `1.6.x` streams

Late `1.6.x` streams demonstrate the correct closure pattern and therefore establish the boundary for `1.7.x` admission:

1. `v1.6.14` closes launcher/operator surfaces back onto machine executability truth;
2. `v1.6.16` closes continuity/re-entry as governed runtime law rather than operator memory;
3. `v1.6.17` closes upper-layer loop strengthening and bounded `4 -> 1` loopback as machine-consumed law;
4. `v1.6.18` closes artifact-family ontology so persisted protocol objects stop collapsing into generic “memory” language;
5. `v1.6.19` closes weak-live-linkage by requiring contract / artifact / run-binding / consumption closure on real runtime identities;
6. `v1.6.20` closes broadcast-delivery and aggregate communication transport as protocol-owned fleet/runtime convergence lanes.
7. `v1.6.21` closes higher-order clean terminal truth / canonical publishability / explicit pending-state equivalence / generic completed-done alias drift inside one shared machine-law lane.

Interpretive consequence:

1. `1.6.x` is the line that must finish closing the current protocol universe;
2. `1.7.x` inherits a cleaned ground, not an unfinished workbook tail.

### 4.1 Outer runtime verdict / summary surfaces remain bounded

1. three-plane verdict remains a governed outer runtime-state surface.
2. `scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
3. `scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
4. `scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.
5. All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.
6. `scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh` is the dedicated additive freeze for this requirement and must keep verifying:
   - `scripts/report_three_plane_status.py` emits `terminal_truth_boundary_projection` and preserves the same split in `instance_plane_detail.terminal_truth_boundary_projection`;
   - `scripts/release_readiness_check.py --summary-out` emits `terminal_truth_boundary_projection` and compresses it into one-look fields such as `one_look.terminal_truth_boundary_projection_status`;
   - `scripts/full_identity_protocol_scan.py` emits per-row `three_plane_terminal_truth_boundary_projection` and aggregate `summary_terminal_truth_boundary`.
7. `ASB16-RQ-006` release-plane cloud evidence must also self-describe its acquisition boundary:
   - materialized external evidence (`checks_json`, `jobs_json`, `gh-runs-json`) is the canonical local replay surface;
   - protocol consumers remain the semantic aggregation authority;
   - shell/API live fetch paths are acquisition mechanisms only and must not be overclaimed as stronger semantic truth than the materialized evidence they produce.
8. The canonical sequenced refresh lane for release-boundary control-plane artifacts is `python3 scripts/materialize_control_plane_surfaces.py --write --json-only`; release-readiness may dry-run the same machine action for health projection, but that projection must not replace the direct control-plane validators or the current canonical files themselves.

### 4.2 Repair / observation / admission split remains frozen

`v1.6.21` also freezes one release-boundary reading rule that must stay explicit across `1.6.x` closure:

1. the **repair lane** may pass when shared post-execution repair successfully restores mandatory writeback/runtime projection fields;
2. the **terminal-truth observation lane** remains the direct owner of clean terminal truth and canonical publishability verdicts;
3. the **creator/update admission lane** may still block when contract backfill observes a non-clean current run, even if the repair lane is green;
4. `repair success != clean terminal truth`;
5. dirty current-run terminal truth must not be upgraded into admissible update closure merely because a repair executor projected mandatory fields successfully.

Frozen consequence:

1. `scripts/repair_identity_post_execution_mandatory.py` is a shared repair executor, not the clean-terminal-truth owner;
2. `scripts/validate_terminal_truth_cleanliness.py` keeps fail-close authority over non-clean terminal truth;
3. `scripts/repair_contract_backfill.py` may therefore fail update preflight on terminal-truth projection even when repair projection succeeded;
4. shared probes must preserve this split rather than collapsing it back into “repair executor failed”.

## 5) Release-closure and future-admission rule

1. The authoritative current workbook rows for `ISSUE-001` through `ISSUE-039` remain the machine-readable release-closure ledger for the known `1.6.x` universe.
2. Release issuance still depends on the active machine gates, not this document alone.
3. But any attempt to classify a still-current-universe closure debt as a `1.7.x` item must fail the interpretation test in this document.
4. The admission rule for `1.7.x` is therefore:
   - first prove the current topic is not unresolved `1.6.x` closure debt;
   - only then treat it as a new object / relation / capability stream.

### 5.1 Outer runtime verdict / summary surfaces must stay explicitly bounded

1. three-plane verdict remains a governed outer runtime-state surface.
2. `scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
3. `scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.
4. `scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.
5. `scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh` must keep the three surfaces above honest by verifying `terminal_truth_boundary_projection`, `three_plane_terminal_truth_boundary_projection`, and `summary_terminal_truth_boundary` on real emitted payloads.
6. All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.
7. Release-plane cloud evidence summaries must expose whether their evidence came from materialized input or live fetch, so local replay never depends on operator memory about `gh`/API transport behavior.
8. The canonical control-plane refresh sequence remains owned by `scripts/materialize_control_plane_surfaces.py`; summary surfaces may project its health, but they must not silently collapse direct validator receipts into derived prose.

## 6) Frozen one-line version law

1. `1.6.x` must close the current identity-protocol universe to root-closed, machine-closed, and runtime-closed terms.
2. `1.7.x` begins only as a future-facing line for new objects, new relations, and new capabilities on top of that closed ground.
