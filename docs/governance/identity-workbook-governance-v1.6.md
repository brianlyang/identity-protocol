# Identity Workbook Governance (v1.6)

Status: Active governance
Layer: protocol
Scope: canonical workbook control plane for cross-stream issue governance inside `identity-protocol-local`

## 0) Frozen control-plane rule

1. Cross-stream issue governance must live inside `identity-protocol-local` or not exist at all.
2. External workspace notes, mirrors, or evidence packs are never authoritative for protocol workbook truth.
3. The canonical workbook control plane is the minor-family bundle formed by:
   - `docs/workbook/`,
   - `identity/protocol/mappings/workbook-registry.current.yaml`,
   - `identity/protocol/mappings/workbook-registry.v1.6.yaml`,
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`,
   - `scripts/validate_issue_register_consistency.py`.
4. The active workbook family is selected only by `identity/protocol/mappings/workbook-registry.current.yaml`, and the versioned workbook registry defines both authority surfaces and optional external projections.
5. Naming discipline is frozen:
   - `workbook = X.X`
   - `governance/review = X.X.X`

## 1) Why `docs/workbook/` exists

1. `docs/review/` remains stream-owner review ledger space.
2. Some cleanup families cross multiple stream-owner docs and cannot be reduced to one `docs/review/` file.
3. Those cross-stream cleanup families must therefore be centralized under `docs/workbook/` instead of being scattered across ad hoc audit files.
4. A workbook family is keyed by the governed minor family such as `v1.6`, and it radiates over the current `v1.6.x` stream-owner lanes selected through the protocol doc registry.
5. This is why workbook control-plane meaning must not be attached to a specific patch stream such as `v1.6.14`.

## 1.1 Migration boundary

1. The current `v1.6` workbook pair is the canonical migration target for the earlier issue-routing files that were not previously stored inside the protocol base repo.
2. After migration, those outer copies are demoted to projection-only artifacts.
3. Validators must default to the protocol-internal workbook pair, never to the migrated outer copies.
4. If optional projection copies are kept in the outer workspace, they must be declared through the versioned workbook registry instead of being rediscovered ad hoc.

## 2) Fixed directory and file roles

### 2.1 Canonical directory

- `docs/workbook/`

No other directory is allowed to host the authoritative cross-stream issue workbook surface.

### 2.2 Mandatory workbook pair

Every active workbook family must contain exactly two canonical Markdown files:

1. `protocol-issue-register-<minor>.md`
   - authoritative current-status table;
   - current issue count and status semantics;
   - the only file allowed to declare whether an issue row is currently `OPEN`, `REOPENED`, or `CLOSED`.
2. `protocol-deep-audit-workbook-<minor>.md`
   - canonical intake/routing workbook;
   - root-cause clustering, serial deep-scan consolidation, and issue section detail;
   - mirrors status rows from the issue register, but does not override them.

### 2.3 Companion governance file

- `docs/governance/identity-workbook-governance-v1.6.md`

This file freezes the workbook model itself and is not a substitute for any individual workbook family.

### 2.4 Registry pointer

- `identity/protocol/mappings/workbook-registry.current.yaml`
- `identity/protocol/mappings/workbook-registry.v1.6.yaml`

Validators and CI must resolve the active workbook family through the registry, not by guessing filenames.

### 2.5 Optional projection exports

1. The versioned workbook registry may list optional external projection docs under the active workbook family.
2. These projections are mirror-only:
   - they may be deleted without changing protocol truth;
   - they may summarize or export workbook state for workspace operators;
   - they must never become status authority inputs.
3. If a projection is present, it must declare:
   - projection-only mode,
   - its canonical workbook source,
   - the current workbook registry pointer that governs it.
4. If the registry opts a projection into freshness enforcement, the projection must also record machine-readable workbook issue counts and docs-checker counts so the validator can prove it still mirrors the active workbook family.

## 3) Relationship to `docs/review/`

1. `docs/review/` is still the owner-ledger surface for one specific stream lane.
2. `docs/workbook/` is the concentrated cross-stream issue-governance surface for one cleanup family.
3. These surfaces are related but not interchangeable.
4. A stream review ledger may be one closure anchor for an issue row, but it is not the issue register itself.

## 4) Naming and range rules

1. Workbook names must encode the governed minor family, for example:
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
2. A `v1.6` workbook governs the current `v1.6.x` stream-owner docs collectively, rather than hardcoding one closing patch range into the workbook filename.
3. Stream governance and stream review remain `v1.6.x`; workbook stays at `v1.6`.

## 5) Documentation-governance binding

1. Workbook docs are mandatory static docs under the protocol doc registry.
2. The workbook registry current pointer and the versioned workbook registry are part of the same workbook control plane and must evolve with the workbook docs rather than as disconnected YAML sidecars.
3. Workbook docs must carry explicit current-pointer alias refs, at minimum:
   - `identity/protocol/mappings/workbook-registry.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
4. `docs/workbook/README.md` is part of the workbook control plane and must carry the same alias-ref discipline as the canonical workbook pair.
5. `scripts/docs_command_contract_check.py` must validate workbook docs under the same documentation-governance discipline as `docs/governance/` and `docs/review/`.
6. Any workbook drift that breaks alias-ref or executable-doc contract must fail in the same doc-governance lane.

## 6) Machine-gate binding

1. `scripts/validate_issue_register_consistency.py` must consume the active workbook pair from `identity/protocol/mappings/workbook-registry.current.yaml` by default.
2. The validator must fail-close when:
   - workbook docs resolve outside `identity-protocol-local/docs/workbook/`;
   - issue register rows and deep-audit workbook statuses diverge;
   - either canonical workbook surface uses historical/open wording that silently overrides current closed rows;
   - the active minor family resolves to more or fewer authority-shaped workbook docs than the canonical pair selected by the registry;
   - recorded docs-checker counts drift away from live checker output.
3. If the versioned workbook registry declares optional projection exports, the validator may inspect them only to confirm projection-only boundary markers and canonical-source pointers; it must not use them as default status authority.
4. If the versioned workbook registry opts a projection export into freshness enforcement, the validator must fail-close when the projection's summary counts drift from the active workbook family.
5. `scripts/release_readiness_check.py` and `scripts/ci/run_required_runtime_gates_ci.sh` must keep the workbook-consistency gate in the formal release/runtime bundle.

## 7) Frozen authority boundary

1. `protocol-issue-register-<minor>.md` is authoritative for current row status.
2. `protocol-deep-audit-workbook-<minor>.md` is authoritative for intake/routing structure and root-cause grouping.
3. Owner governance docs and owner review ledgers remain authoritative for stream semantics and stream-local closure evidence.
4. The versioned workbook registry is authoritative for selecting the active minor-family workbook pair and for declaring any optional external projections.
5. External copies, exports, or mirrored workbooks never outrank the protocol-internal workbook pair and never participate in status authority.
