# Identity Codex Launcher Workspace-Convergence Roundtable v1.6.14

Status: Discussion package open for architect + audit + implementation alignment
Date: 2026-03-22
Semantic owner: `v1.6.14` launcher lane
Workbook role: track decision status, audit checkpoints, and rollout readiness only

## Current control-plane alias refs

- `identity/protocol/mappings/workbook-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/control-plane-status.current.yaml`

## 0) Why this package exists

1. `v1.6.14` already froze the canonical follow-on rollout direction as a **workspace-level launcher convergence entry**.
2. That direction is strong enough to block ad hoc per-identity repair as the fleet operating model, but the single protocol-owned convergence entry is not yet landed as code.
3. This package exists so architecture, audit, and implementation owners can align on one control-plane discussion surface before coding the entry.
4. This package does **not** reopen launcher semantics, command naming, install directories, or inherited bootstrap/topology streams.
5. This package also does **not** create a new stream by default; it keeps the topic inside `v1.6.14` unless scope later expands beyond launcher-only convergence.

## 1) Fixed role boundary

1. Semantic ownership remains in `docs/governance/identity-codex-launcher-governance-v1.6.14.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`.
2. The workbook family may record issue state, decision checkpoints, and audit readiness, but it does not become launcher-semantics authority.
3. This roundtable package is a governance support surface for discussion and decision capture; it is not a replacement for the stream governance/review pair.
4. If the outcome stays launcher-specific, the landing remains part of `v1.6.14`.
5. A new stream should be opened only if the scope is deliberately promoted into a generic multi-lane convergence framework that goes beyond launcher rollout/orchestration.

## 2) Participants and expected responsibilities

| Role | Required focus | Non-negotiable boundary |
| --- | --- | --- |
| Identity protocol architect | freeze semantic owner, orchestration boundary, and control-plane shape | do not reopen `v1.6.12` bootstrap semantics, `v1.6.13` pack topology, or launcher command/path ownership |
| Audit expert | freeze receipt family, evidence refs, fail-close semantics, negative probes, and replay/readiness expectations | do not accept a convenience runner without governed receipts and red-state proofs |
| Closure / implementation owner | land one canonical protocol-owned entry and reuse existing primitives | do not fork launcher logic into workspace-private wrappers or hardcoded identity lists |
| Pilot workspace owner | prove unchanged portability against another workspace-local runtime catalog | do not request workspace-specific launcher exceptions or alternate shortcut naming |

## 3) Frozen inputs that the roundtable must reuse

### 3.1 Stream-owner inputs

1. `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
3. `identity/protocol/IDENTITY_PROTOCOL.md`
4. `identity/protocol/IDENTITY_RUNTIME.md`

### 3.2 Existing protocol primitives

1. Aggregate fleet checker: `scripts/check_identity_codex_launcher_migration_closure.py`
2. Single-identity validator: `scripts/validate_identity_codex_launcher.py`
3. Launcher contract/asset common layer: `scripts/identity_codex_launcher_common.py`
4. Backfill surface: `scripts/repair_contract_backfill.py`
5. Lifecycle orchestration: `scripts/identity_creator.py`
6. Launcher install surface: `scripts/install_identity_codex_launcher.py`
7. Required runtime gates consumer: `scripts/ci/run_required_runtime_gates_ci.sh`
8. Readiness consumer: `scripts/release_readiness_check.py`

### 3.3 Workbook and authority boundary inputs

1. `docs/workbook/protocol-issue-register-v1.6.md`
2. `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
3. `identity/protocol/mappings/workbook-registry.v1.6.yaml`
4. `scripts/validate_issue_register_consistency.py`

## 4) Questions that must be frozen before coding

### 4.1 Canonical entry surface

1. What is the one authoritative protocol-owned entry surface:
   - an `identity_creator` workspace-level subcommand,
   - a dedicated runner under `scripts/`,
   - or a thin alias/delegation pair with only one authority surface?
2. The decision must prevent multiple equally-canonical launch/convergence commands from reintroducing drift.

### 4.2 Runtime source-of-truth and catalog policy

1. The convergence entry must operate over the **workspace-local runtime catalog**.
2. The roundtable must freeze whether repo fixture catalogs are:
   - excluded entirely,
   - reference-only for dry-run inspection,
   - or visible but never mutable.
3. The entry must not mutate demo/fixture identities by accident.

### 4.3 Repair composition path

1. The convergence entry must reuse existing protocol primitives rather than restating launcher logic.
2. The roundtable must freeze whether the authoritative repair pipeline is:
   - aggregate checker -> shared backfill/apply -> launcher install -> recheck,
   - or `identity_creator update` orchestration that delegates to the same primitives.
3. The decision must keep single-identity truth in the existing validator and fleet truth in the aggregate checker.

### 4.4 Mutation scope

1. The roundtable must decide whether launcher convergence is allowed to reuse shared backfill with its current transitive repair behavior.
2. If transitive repair is accepted, the receipt must expose that broader mutation scope instead of pretending the run was launcher-only.
3. If transitive repair is rejected, a launcher-scoped backfill mode must be specified before implementation starts.

### 4.5 Dry-run / apply / failure semantics

1. Dry-run must remain non-mutating and still emit a governed result.
2. Apply mode must repair, rerun closure validation, and fail-close if violations remain.
3. The roundtable must freeze whether partial success is allowed, and if so how it is represented in the final governed receipt.

### 4.6 Receipt contract and evidence path

1. The convergence entry must emit a governed convergence receipt.
2. The roundtable must freeze:
   - receipt path family,
   - schema,
   - whether failed and partial runs still emit receipts,
   - mandatory evidence refs,
   - and the relationship to existing allowlist/evidence families.
3. The receipt must record at least:
   - workspace-local catalog truth,
   - checked identities,
   - repaired identities,
   - remaining violations after recheck,
   - and evidence refs for pre-repair detection plus post-repair proof.

### 4.7 Lifecycle / gate boundary

1. The current required gates and readiness surfaces consume the aggregate checker, not a mutating convergence runner.
2. The roundtable must freeze whether the new entry remains an explicit rollout tool only, or whether it later becomes part of a governed lifecycle surface.
3. The discussion must keep repair mutation distinct from passive fail-close validation unless an explicit governance change is approved.

### 4.8 Cross-workspace proof rule

1. Cross-workspace validation must come from running the **same** convergence entry against another workspace-local runtime catalog such as `fqsh` or `office-ops`.
2. Cross-workspace proof must not be satisfied by workspace-specific wrapper exceptions or alternate launcher shortcuts.
3. Pilot proof from a single manually repaired identity is acceptable only as evidence that the shared toolchain works end-to-end, not as fleet-closure proof.

### 4.9 Accepted control-plane decision freeze (2026-03-22)

1. **Canonical entry surface**
   - Freeze one authoritative protocol-owned convergence entry at `scripts/run_identity_codex_launcher_workspace_convergence.py`.
   - The entry exposes one governed interface with `--mode dry-run|apply`; dry-run remains non-repairing while still emitting governed result artifacts.
   - `identity_creator update` may delegate to this entry for explicit launcher auto-repair, but that delegation is non-authoritative; launcher convergence semantics still belong to this single script.
2. **Catalog authority**
   - Freeze workspace-local runtime catalog authority only: the convergence entry must operate on `<workspace>/.identity/catalog.local.yaml` or an equivalent external workspace-local runtime catalog passed explicitly.
   - Repository fixture catalogs such as `identity/catalog/identities.yaml` are excluded from the convergence entry and must fail closed instead of being mutated or silently inspected as runtime truth.
3. **Repair composition path**
   - Freeze the authoritative repair pipeline as:
     - aggregate checker `scripts/check_identity_codex_launcher_migration_closure.py`
     - shared contract backfill `scripts/repair_contract_backfill.py --apply`
     - launcher rollout `scripts/install_identity_codex_launcher.py`
     - single-identity validation `scripts/validate_identity_codex_launcher.py --require-installed`
     - aggregate recheck through the same checker
   - This keeps fleet truth in the aggregate checker and single-identity truth in the existing launcher validator.
4. **Mutation scope**
   - Freeze shared backfill reuse as accepted for this lane; launcher convergence does not get a launcher-only private repair dialect.
   - The convergence receipt must disclose that the mutation scope is `transitive_backfill_plus_launcher_install` so apply mode cannot pretend it was launcher-only if shared backfill touched other required protocol contract surfaces.
   - Partial execution may occur operationally, but any unresolved post-repair violation remains fail-close and must surface as a non-green final receipt.
5. **Receipt family and evidence path**
   - Freeze the canonical receipt family as `identity_codex_launcher_workspace_convergence_receipt_v1`.
   - Freeze the canonical archival root at `activity/evidence/v1614-identity-codex-launcher/<YYYY-MM-DD>/`.
   - The convergence entry must emit:
     - `launcher_convergence_precheck.<run_token>_summary.json`
     - `launcher_convergence_receipt.<run_token>_summary.json`
     - and, for apply mode, `launcher_convergence_postcheck.<run_token>_summary.json`
   - The receipt must keep workspace-local catalog truth, checked identities, repaired identities, remaining violations, mutation scope, and pre/post evidence refs machine-visible.
6. **Gate boundary**
   - Freeze required gates and readiness as passive live-surface consumers of the aggregate checker; they do not directly run the mutating live convergence entry against the active workspace tree.
   - Synthetic probe coverage for the convergence entry is acceptable inside required gates because it validates the control-plane asset without mutating live workspace runtime state.
   - Lifecycle delegation is limited to explicit repair surfaces such as `identity_creator update`; passive validate/readiness flows remain fail-close on the checker rather than auto-mutating.
7. **Cross-workspace pilot rule**
   - Freeze pilot proof to “same convergence entry, different workspace-local runtime catalog, no workspace-specific exceptions.”
   - One repaired identity may prove the toolchain works end-to-end, but protocol-owned breadth claims still require multi-identity and eventually multi-workspace evidence through the same entry.
   - A generic multi-lane convergence framework remains deferred until launcher-specific convergence is landed and replay-proven across more than one workspace.

## 5) Default recommendation for this roundtable

1. Keep the topic inside `v1.6.14`; do **not** open a new stream while the scope is still launcher-only convergence.
2. Use the workbook family to track decision status and rollout readiness, but keep stream semantics and implementation contracts in `v1.6.14` governance/review.
3. Prefer one protocol-owned convergence interface, with any secondary wrapper or alias explicitly delegated and non-authoritative.
4. Prefer workspace-local catalog authority only.
5. Prefer explicit dry-run and apply modes.
6. Prefer governed receipt emission for both dry-run and apply, with fail-close on unresolved post-repair violations.
7. Defer any generic multi-lane convergence framework until the launcher-specific convergence entry is landed and proven across more than one workspace.

## 6) Roundtable exit criteria before coding may start

1. One canonical entry surface is selected.
2. Catalog authority and mutation boundary are frozen.
3. Repair composition path is frozen.
4. Mutation scope is frozen.
5. Dry-run / apply / fail-close semantics are frozen.
6. Receipt family, schema, and evidence path are frozen.
7. Gate/readiness boundary is frozen.
8. Cross-workspace pilot rule is frozen.
9. The architect and audit owners both accept the package as sufficient to start implementation.

## 7) Post-roundtable landing sequence

1. Freeze the chosen interface and receipt family back into the `v1.6.14` governance/review pair.
2. Land the single protocol-owned convergence entry in code by reusing the existing checker/backfill/install/recheck primitives.
3. Add dedicated probes and any required negative proofs for convergence failure modes.
4. Wire any newly approved evidence/receipt family into the required allowlist or evidence registry surfaces.
5. Prove unchanged portability by running the same convergence entry against another workspace-local runtime catalog.
6. Only after that proof may reviewers describe launcher convergence as protocol-owned fleet rollout infrastructure rather than as a workspace-local pilot.
