# Protocol Remediation Audit Ledger (v1.6.3 GitHub-native control-plane stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review and replay ledger for GitHub-native control-plane specialization (`v1.6.3`).

Companion governance SSOT:

1. `docs/governance/github-native-control-plane-specialization-v1.6.3.md`
2. `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
3. `identity/protocol/mappings/github-control-plane-offload.current.yaml` (stable alias entry)

## State interpretation guard

1. Intake and pre-dev sections are historical review records.
2. Current-state verdict must prioritize the latest execution section (Round-32 or newer) and machine status files.
3. Historical gap statements are archival unless reaffirmed by newer machine receipts.

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

1. Baseline metric source is mapping/evidence SSOT (no duplicated literal table in review body):
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
   - `activity/evidence/v163-predev/2026-03-10/v163_state_gap_summary.json`
2. Review stream only records deviations or phase-gate decisions; raw baseline numbers are replayed from evidence summary.

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
2. Repository code implementation has been executed in Round-32.
3. Platform activation remains pending (ruleset/owner-review switches).
4. Posture: `CONDITIONAL_GO` for platform closure, with `repo_code_completed` achieved.

## 7) Anti-break-chain update (2026-03-10)

1. Added current-alias pointer for offload mapping:
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
2. Added invariant checks so alias chain is fail-closed:
   - missing/unparseable `current` or `active_file` now fails control-plane invariants.
3. This removes version-file direct-coupling in tooling and reduces pointer break risk during future upgrades.

## 8) Round-31 final pre-development readiness package (2026-03-10)

### 8.1 Review objective

1. Freeze one implementation-ready package for v1.6.3 before phase coding starts.
2. Ensure governance/mapping/CI boundaries are consistent and non-conflicting.
3. Provide replayable evidence pointers for architect + auditor joint sign-off.

### 8.2 Replay evidence (persistent mirrors)

Canonical root:

1. `activity/evidence/v163-predev/2026-03-10/`

Core evidence files:

1. `PREDEV_MIN_ANCHOR.json`
2. `v163_state_gap_summary.json`
3. `EVIDENCE_MANIFEST.v163-predev-round31.json`

Replay rule:

1. Use `PREDEV_MIN_ANCHOR.json` as first hop.
2. Expand to full artifact set through manifest records (do not duplicate file lists in review prose).

### 8.3 Measured pre-dev state (machine extracted)

1. Mapping status:
   - `offload_plan_version=v1.6.3`
   - `mapping_status=predev_package_completed`
2. Phase-1 hard gaps:
   - required-gate python invocations: `121` (target `<=95`, gap `26`)
   - `merge_group` trigger coverage: missing on both `protocol-ci` and `identity-protocol-ci`
3. Ownership/policy gaps:
   - `.github/CODEOWNERS` not present

### 8.4 Vendor cross-verification snapshot (GitHub official)

Validated references for this round:

1. rulesets available rules
2. merge queue
3. actions `merge_group` event
4. required status checks troubleshooting
5. CODEOWNERS behavior
6. reusable workflows
7. repository actions settings/policy

Source index:

1. `activity/evidence/v163-predev/2026-03-10/github_vendor_reference_snapshot.json`

### 8.5 No-conflict checkpoint (must remain true during implementation)

1. `asb16-rq-019`, `asb16-rq-034`, `asb16-rq-035` remain repo-retained semantic contracts.
2. Offload controls are limited to `cp-gh-001..005` in mapping YAML.
3. Tooling reads `github-control-plane-offload.current.yaml` only; no direct versioned-file coupling in scripts/workflows.
4. v1.6.2 plugin governance SSOT remains authoritative for semantic fail-close logic.

### 8.6 Development handoff checklist (auditor gate)

Before claiming any phase completion:

1. Run:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`
2. Recompute phase metrics and persist under:
   - `activity/evidence/v163-predev/<date>/`
3. Update mapping status/targets only with matching machine receipts.
4. Reject prose-only phase closure claims.

### 8.7 Stream posture update

1. v1.6.3 is now **pre-development complete** (documentation + mapping + replay package).
2. Implementation remains **not started**.
3. Posture remains `CONDITIONAL_GO` pending architect/auditor approval to begin phase-1 code changes.

## 9) Round-31.1 audit absorption matrix (2026-03-10)

### 9.1 Findings -> disposition

| Finding | Severity | Disposition | Implementation phase |
| --- | --- | --- | --- |
| `merge_group` trigger missing in protocol/identity CI | P1 | accepted (hard blocker) | phase_1 |
| CODEOWNERS missing | P1 | accepted (hard blocker) | phase_2 |
| branch-protection checklist vs ruleset dual-source | P2 | accepted (migration-language fix + ruleset snapshot requirement) | phase_1/2 |
| budget boundary equal-to-fail interpreted as non-fail | P2 | accepted (review red-adjacent classification; comparator change deferred) | phase_2 proposal |
| parallel untracked evidence roots create review noise | P3 | accepted (single canonical evidence root per round) | immediate process rule |

### 9.2 Unified roundtable judgment after absorption

1. T1 (repo telemetry): semantic gates and core contracts remain green.
2. T2 (vendor/GitHub): offload direction remains correct but execution gaps are real (`merge_group`, ruleset binding, CODEOWNERS).
3. T3 (protocol boundaries): no semantic downgrade observed; RQ-019/034/035 remain repo-retained.
4. T4 (operability): highest near-term risk is migration-era dual-interpretation, not validator capability loss.

### 9.3 Pre-implementation lock (what must be true before phase closure claims)

1. Do not claim phase_1 done while either CI workflow lacks `merge_group`.
2. Do not claim phase_2 done without CODEOWNERS + required owner review enforcement.
3. Do not describe checklist-only branch protection as normative once ruleset rollout starts.
4. Keep v1.6.3 evidence in one canonical root per date and include tuple manifest.

## 10) Round-32 implementation execution ledger (2026-03-10)

### 10.1 Executed code changes

1. Added `merge_group` trigger coverage:
   - `.github/workflows/protocol-ci.yml`
   - `.github/workflows/identity-protocol-ci.yml`
2. Replaced heavy inline gate chain in reusable workflow with script delegation:
   - `.github/workflows/_identity-required-gates.yml`
   - `scripts/ci/run_required_runtime_gates_ci.sh`
   - `scripts/ci/run_full_scan_target_regression_ci.sh`
3. Added ownership baseline:
   - `.github/CODEOWNERS`
4. Earlier Round-31 entries describing `merge_group`/CODEOWNERS as open gaps are historical intake records; current-state verdict uses Round-32 evidence in this section.

### 10.2 Machine outcomes (round32)

Primary metric snapshot:

1. `activity/evidence/v163-predev/2026-03-10/v163_state_gap_summary.json`

Observed:

1. required-gate workflow python invocations:
   - `121 -> 15` (phase_1 target `<=95` satisfied)
2. merge-group coverage:
   - `protocol-ci=true`
   - `identity-protocol-ci=true`
3. codeowners file:
   - `exists=true`

### 10.3 Mandatory checks (round32 replay)

1. `python3 scripts/validate_control_plane_invariants.py --json-only` -> PASS_REQUIRED
   - `activity/evidence/v163-predev/2026-03-10/round32_control_plane_invariants.json`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> PASS_REQUIRED
   - `activity/evidence/v163-predev/2026-03-10/round32_surface_drift.json`
3. `python3 scripts/docs_command_contract_check.py` -> PASS
   - `activity/evidence/v163-predev/2026-03-10/round32_docs_command_contract_check.log`
4. `python3 scripts/validate_protocol_ssot_source.py` -> OK
   - `activity/evidence/v163-predev/2026-03-10/round32_ssot_source.log`
5. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> PASS_REQUIRED
   - `activity/evidence/v163-predev/2026-03-10/round32_doc_evidence_persistence.json`

### 10.4 Mapping status sync

1. Updated:
   - `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
2. Status:
   - `implementation_code_completed_platform_activation_pending`
3. This status is intentionally precise:
   - repo code done
   - platform switches pending

### 10.5 Round-32 evidence tuple entry

1. Anchor:
   - `activity/evidence/v163-predev/2026-03-10/PREDEV_MIN_ANCHOR.json`
2. Resolution matrix:
   - `activity/evidence/v163-predev/2026-03-10/audit_feedback_resolution_round32.json`
3. Manifest:
   - `activity/evidence/v163-predev/2026-03-10/EVIDENCE_MANIFEST.v163-round32-implementation.json`

## 11) Round-33 layer-targeted gate profile absorption (2026-03-10)

### 11.1 Change set (repo)

1. Added canonical mapping:
   - `identity/protocol/mappings/layer-targeted-gate-profile.v1.6.yaml`
2. Added profile validator:
   - `scripts/validate_layer_targeted_gate_profile.py`
3. Extended bundle runner with profile contract:
   - `scripts/required_gate_bundle_runner.py`
4. Extended full-scan forwarding:
   - `scripts/full_identity_protocol_scan.py`
5. Added control-plane status check integration:
   - `scripts/render_control_plane_status.py`
6. Hardened delegated full-scan drift validation:
   - `scripts/validate_required_gate_surface_drift.py`
   - required tokens are now verified from parsed command args (comment-only tokens do not satisfy lineage checks)

### 11.2 Contract judgment

1. Optional recommendation is accepted as protocol-level standard.
2. Trimming is configuration-driven and limited to target scan/inspection use.
3. Strict operations remain hard fail-close full-bundle execution.

### 11.3 Replay checklist for this round

1. `python3 scripts/validate_layer_targeted_gate_profile.py --json-only`
2. `python3 scripts/validate_control_plane_invariants.py --json-only`
3. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. `python3 scripts/validate_doc_evidence_persistence.py --json-only`
6. `python3 scripts/render_control_plane_status.py --write --json-only`
7. `python3 scripts/validate_control_plane_status_sync.py --json-only`

### 11.4 Round-33 posture

1. Layer-targeted profile capability is now protocolized and machine-checkable.
2. Default runtime path remains `strict_full`; no strict-chain relaxation introduced.
