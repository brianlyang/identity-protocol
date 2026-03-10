# Protocol Remediation Audit Ledger (v1.6.3 GitHub-native control-plane stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review and replay ledger for GitHub-native control-plane specialization (`v1.6.3`).

Companion governance SSOT:

1. `docs/governance/github-native-control-plane-specialization-v1.6.3.md`
2. `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
3. `identity/protocol/mappings/github-control-plane-offload.current.yaml` (stable alias entry)

## 0) Boundary rules

1. This file is a review ledger, not a normative governance contract.
2. Normative requirements remain in the companion governance SSOT and mapping YAML.
3. If ledger text conflicts with governance SSOT, treat this ledger as stale.
4. Every phase entry must include:
   - changed files
   - machine checks run
   - replay verdict
   - residual risk
5. No manual promotion wording is allowed without matching machine receipt.

## 1) Intake replay baseline (2026-03-10)

### 1.1 Current measured baseline

1. `scripts/` total: 208
2. `validate_*.py`: 145
3. Unique `IP-*` codes: 457
4. `_identity-required-gates.yml` python invocations: 121
5. `_identity-required-gates.yml` unique python scripts: 115

### 1.2 Structural gaps confirmed

1. `merge_group` trigger not yet wired in CI entry workflows.
2. `CODEOWNERS` not yet present.
3. Branch protection policy still partially checklist-driven rather than ruleset-driven.

### 1.3 Intake judgment

1. `v1.6.3` stream is required and justified.
2. Migration must be phased with rollback points.
3. Semantic fail-close contracts (`asb16-rq-034/035/019`) remain in repo validators.

## 2) Control review matrix (v1.6.3)

| Control ID | Topic | Target platform | Current state | Phase target |
| --- | --- | --- | --- | --- |
| `cp-gh-001` | branch protection | GitHub Rulesets | manual checklist dominant | Phase 1 |
| `cp-gh-002` | required check stability | GitHub Rulesets | workflow/job naming coupled | Phase 1 |
| `cp-gh-003` | merge queue compatibility | GitHub Merge Queue | trigger gap (`merge_group`) | Phase 1 |
| `cp-gh-004` | ownership approval | CODEOWNERS | not wired | Phase 2 |
| `cp-gh-005` | workflow policy | GitHub Actions policy | partially centralized | Phase 2 |

Source of truth for this matrix:

1. `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`

## 3) Cross-verification log (T1/T2/T3/T4)

### T1 Internal telemetry

1. Required-gate chain is functional but script-heavy.
2. Semantic validators are effective and should be retained.
3. Complexity risk now comes from orchestration sprawl, not semantic under-validation.

### T2 Vendor track (GitHub official)

1. Rulesets can enforce branch + required-check policies.
2. Merge queue requires workflow support for `merge_group` events.
3. CODEOWNERS can enforce path-level review ownership.
4. Reusable workflows and Actions policy support centralized, controlled CI behavior.

### T3 Reference track (protocol compatibility)

1. Platform controls are suitable for process governance.
2. Platform controls are not suitable for protocol semantic contracts.
3. Offload scope is valid only when semantic guards stay in protocol validators.

### T4 Replay operability track

1. Governance/review docs must keep evidence pointers readable and replayable.
2. Avoid introducing `/tmp` as normative evidence in strict streams.
3. Keep this ledger as summary + pointer; avoid dumping raw logs inline.

## 4) Phase gate criteria

### 4.1 Phase 1 gate

1. Required checks are bound in ruleset with stable names.
2. CI workflows report on `pull_request`, `push`, and `merge_group` consistently.
3. Required-gate invocation count reduced to `<=95`.

### 4.2 Phase 2 gate

1. `CODEOWNERS` exists and required owner review is enabled.
2. Actions policy restrictions are active.
3. Required-gate invocation count reduced to `<=85`.

### 4.3 Phase 3 gate

1. Redundant checklist-only policy dependencies are removed.
2. Required-gate invocation count reduced to `<=75`.
3. No regression on RQ-034/RQ-035 negative probes.

## 5) Regression guard set (must remain green)

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_protocol_ssot_source.py`

## 6) Current stream posture

1. Intake and review scaffolding are complete.
2. Implementation is not started in this ledger yet.
3. Posture: `CONDITIONAL_GO` (phase-1 executable, phase-gated).

## 7) Anti-break-chain update (2026-03-10)

1. Added current-alias pointer for offload mapping:
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
2. Added invariant checks so alias chain is fail-closed:
   - missing/unparseable `current` or `active_file` now fails control-plane invariants.
3. This removes version-file direct-coupling in tooling and reduces pointer break risk during future upgrades.
