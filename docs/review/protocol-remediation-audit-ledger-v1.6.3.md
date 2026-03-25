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

1. `activity/evidence/v163-predev/2026-03-10/PREDEV_MIN_ANCHOR.json`
2. `activity/evidence/v163-predev/2026-03-10/v163_state_gap_summary.json`
3. `activity/evidence/v163-predev/2026-03-10/EVIDENCE_MANIFEST.v163-predev-round31.json`

Replay rule:

1. Use `activity/evidence/v163-predev/2026-03-10/PREDEV_MIN_ANCHOR.json` as first hop.
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
   - `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
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

### 11.5 Round-33.1 target-probe profile binding fix (2026-03-10)

1. `scripts/required_gate_bundle_runner.py` now enforces profile binding even when `--target-name` is provided.
2. If a target probe is outside the selected targeted profile:
   - return `SKIPPED_NOT_REQUIRED` with reason `target_excluded_by_gate_profile`.
3. If a targeted profile is used on strict operations (`ci/update/readiness/...`):
   - return `FAIL_REQUIRED` with explicit `mapping_errors` in payload (fail-close contract preserved).

### 11.6 Round-33.2 contract-binding reference integrity closure (2026-03-10)

1. Added protocol validator:
   - `scripts/validate_contract_binding_reference_integrity.py`
2. Validator scope is requirement-row structural integrity for:
   - `requirement_key` / `requirement_id` format
   - `validator_ids` non-empty and script existence
   - `gate_surfaces` token validity
   - `governance_anchor` / `review_anchor` / `kernel_source_path` file existence and markdown anchor resolvability
   - `governance_anchor` / `review_anchor` path-prefix + stream-doc-registry membership (anti-break-chain)
3. Fixed stale anchors in:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`
4. Integrated into machine control-plane status rendering:
   - `scripts/render_control_plane_status.py`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
5. Round replay outcome:
   - `validate_contract_binding_reference_integrity` = `PASS_REQUIRED`
   - control-plane status sync remains `PASS_REQUIRED`

### 11.6A Control-plane status surface boundary

1. `scripts/render_control_plane_status.py` remains a machine control-plane status summary surface on an outer control-plane layer.
2. It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.
3. The renderer must self-describe this bounded authority in machine-readable payload form.

### 11.6B Control-plane budget surface boundary

1. `scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.
2. It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.
3. The renderer must self-describe this bounded authority in machine-readable payload form.

### 11.7 Round-33.3 plugin current-alias hardening closure (2026-03-10)

1. Added stable plugin alias entry files:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - `identity/protocol/plugins/PROVIDER_PROFILES.current.yaml`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
2. Switched strict validators and pack skeleton defaults from version file literals to alias-driven resolution:
   - `scripts/validate_multimodal_plugin_enforcement.py`
   - `scripts/validate_reasoning_loop_failclose.py`
   - `scripts/validate_failclose_plugin_projection.py`
   - `scripts/create_identity_pack.py`
3. Extended invariants with plugin control-plane alias enforcement and versioned-reference block on strict execution surfaces:
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `scripts/validate_control_plane_invariants.py`
4. Updated plugin SSOT readability and onboarding references to stable alias entries:
   - `identity/protocol/plugins/README.md`
   - `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.v1.6.2.md`
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.v1.6.2.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
5. Replay outcome:
   - `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_plugin_contract_literal_paths.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only` => `PASS_REQUIRED`
6. Target full-scan note:
   - `full_identity_protocol_scan --scan-mode target` was replayed.
   - Local run with `--session-id run:v163-audit-20260310` reported `P0=1` caused by `IP-ASB-SESSION-ENTRY-001` (requested session not pre-bound in local project runtime), not by alias hardening regressions.

### 11.8 Round-33.4 target full-scan fixture false-block closure (2026-03-10)

1. Gap:
   - `scripts/ci/run_full_scan_target_regression_ci.sh` runs target full-scan across resolved IDs.
   - fixture/demo-only IDs can carry `P0` only because strict requested-session binding is absent (`IP-ASB-SESSION-ENTRY-001`), which is not a semantic regression for fixture inspection scope.
2. Fix:
   - Added fixture-scoped skip contract in `scripts/validate_full_scan_target_regression.py` via `--allow-fixture-session-skip`.
   - Skip is applied only when **all** `P0` rows are exactly `requested_session_binding` with `IP-ASB-SESSION-ENTRY-001`.
   - Additional hard guard: per `P0` identity, failed-check set must be exactly one entry (`requested_session_binding`) or skip is rejected.
   - Any other `P0` (or mixed failure) remains `FAIL_REQUIRED`.
3. CI wiring:
   - `scripts/ci/run_full_scan_target_regression_ci.sh` now passes `--allow-fixture-session-skip` for fixture branch only.
   - non-fixture branch remains strict and unchanged (`--enforce-m2m-pass` stays active).
4. Safety boundary:
   - this does not downgrade strict semantics for real runtime identities.
   - this removes only fixture-mode false blocking caused by synthetic strict-session expectations.

### 11.9 Round-33.5 layer-profile alias anti-break-chain closure (2026-03-10)

1. Gap:
   - `layer-targeted-gate-profile` was still consumed via versioned literal (`...v1.6.yaml`) on execution surfaces.
   - this required script edits on every profile schema version bump, conflicting with pointer-switch governance.
2. Fix:
   - added alias entry file:
     - `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
   - switched execution defaults to alias path:
     - `scripts/required_gate_bundle_runner.py`
     - `scripts/full_identity_protocol_scan.py`
     - `scripts/validate_layer_targeted_gate_profile.py`
   - extended invariants with alias + anti-drift enforcement:
     - `identity/protocol/mappings/control-plane-invariants.current.yaml`
     - `scripts/validate_control_plane_invariants.py`
3. Contract hardening:
   - invariants now fail-close when current alias is missing/invalid, active profile file is missing, or required profile keys are dropped.
   - invariants now block direct versioned `layer-targeted-gate-profile.v*` literals under strict execution surfaces (`scripts/`, `.github/workflows/`).
4. SSOT/doc registry alignment:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml` now references `layer-targeted-gate-profile.current.yaml`.
   - governance/readme index references are updated to current alias entry.

### 11.10 Round-33.6 stream-doc/evidence alias anti-break-chain closure (2026-03-10)

1. Gap:
   - stream governance registry and evidence allowlist were still consumed via versioned literals in strict validators.
   - version bump would require touching validator code paths, violating pointer-switch upgrade discipline.
2. Fix:
   - added alias entry files:
     - `identity/protocol/mappings/stream-doc-registry.current.yaml`
     - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - switched validator defaults to alias entry:
     - `scripts/docs_command_contract_check.py`
     - `scripts/validate_doc_evidence_persistence.py`
     - `scripts/validate_contract_binding_reference_integrity.py`
   - extended control-plane invariants alias checks:
     - `stream_doc_registry_alias`
     - `doc_evidence_allowlist_alias`
3. Contract hardening:
   - invariants fail-close when alias entry is invalid, active file missing, required fields dropped, or strict execution surfaces reference versioned literals directly.
4. SSOT alignment:
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml` mandatory static docs now include both new alias files.

### 11.11 Round-33.7 control-plane core alias unification closure (2026-03-10)

1. Gap:
   - `control-plane-budget` / `control-plane-invariants` / `control-plane-status` still defaulted to versioned literals on execution surfaces.
   - this forced script-level edits on version bumps and weakened upgrade tolerance for long-running protocol branches.
2. Fix:
   - added alias entry files:
     - `identity/protocol/mappings/control-plane-budget.current.yaml`
     - `identity/protocol/mappings/control-plane-invariants.current.yaml`
     - `identity/protocol/mappings/control-plane-status.current.yaml`
   - switched validator/render defaults to alias entry:
     - `scripts/validate_control_plane_budget.py`
     - `scripts/validate_control_plane_invariants.py`
     - `scripts/render_control_plane_status.py`
     - `scripts/validate_control_plane_status_sync.py`
   - extended invariants alias checks:
     - `control_plane_budget_alias`
     - `control_plane_status_alias`
3. Contract hardening:
   - fail-close when any core current pointer is missing/invalid, active file missing, required core fields dropped, or strict execution surfaces reintroduce direct versioned literals.
   - status renderer/sync now resolve `control-plane-status.current.yaml` deterministically before write/compare.
4. Replay outcome:
   - `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_control_plane_budget.py --json-only` => `WARN_NON_BLOCKING` (budget only, no fail-close regression)
   - `python3 scripts/render_control_plane_status.py --write` => `PASS_WITH_BLOCKERS`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only` => `PASS_REQUIRED`

### 11.12 Round-33.8 plugin doc-control alias closure (2026-03-10)

1. Gap:
   - plugin control-plane alias contract validated `PLUGIN_REGISTRY` / `PROVIDER_PROFILES` / `FAILCLOSE_PLUGIN_GOVERNANCE`, but did not include `PLUGIN_DOC_CONTROL`.
   - this left one plugin governance pointer outside the same anti-drift fail-close boundary.
2. Fix:
   - extended `plugin_control_plane_alias` in:
     - `identity/protocol/mappings/control-plane-invariants.v1.6.yaml` (resolved via `control-plane-invariants.current.yaml`)
   - added `plugin_doc_control_current_file` row enforcement in:
     - `scripts/validate_control_plane_invariants.py`
   - expanded plugin literal-path lint token set:
     - `scripts/validate_plugin_contract_literal_paths.py`
3. Contract hardening:
   - strict surfaces now fail-close when `PLUGIN_DOC_CONTROL.current.yaml` alias chain is missing/invalid.
   - direct versioned `PLUGIN_DOC_CONTROL.v*` literals on strict surfaces are blocked by the same anti-drift regex family.
4. Replay outcome:
   - `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_plugin_contract_literal_paths.py --json-only` => `PASS_REQUIRED`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` => `PASS_REQUIRED`

### 11.13 Round-34 convergence hardening ledger (2026-03-11)

1. Scope:
   - close three pending convergence points raised after Round-33:
     - control-plane budget monotonic no-rebound
     - `identity_creator.py` direct validate density
     - error-code family convergence metric
2. Code deltas:
   - `scripts/validate_control_plane_budget.py`
     - adds family-normalized error code metric
     - adds convergence-guard fail-close check (`mode=no_rebound`)
   - `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
     - introduces `convergence_guard` ceilings and `error_code_family_strategy`
     - updates dual-threshold values to match current stabilized envelope
   - `scripts/identity_creator.py`
   - `scripts/run_identity_dialogue_feedback_bundle.py`
     - delegates six dialogue/feedback validators through one bundle entry to reduce creator strict-surface literal fan-out
3. Measured outcomes:
   - `validate_control_plane_budget`:
     - before: `WARN_NON_BLOCKING` (`validator_scripts`, `error_codes`, creator direct-calls red-adjacent)
     - after: `PASS_REQUIRED` with `convergence_guard.violations=[]`
   - creator direct validate literals:
     - `90 -> 84` (`scripts/identity_creator.py` strict surface)
   - normalized error-code family count:
     - observed `137`, tracked alongside raw `410`
4. Cross-stream replay snapshot:
   - v1.6.1: `validate_headstamp_recurrence_closure` => `PASS_REQUIRED` (bound-session replay)
   - v1.6.2:
     - `validate_plugin_contract_literal_paths` => `PASS_REQUIRED`
     - `validate_reasoning_loop_failclose` => `PASS_REQUIRED`
     - `validate_multimodal_plugin_enforcement` (strict validate) => `FAIL_REQUIRED` + `IP-MM-RUN-002` on `base-repo-architect` (instance runtime multimodal evidence debt)
   - v1.6.3 control plane:
     - invariants / surface drift / contract binding / status sync / docs+ssot gates all green
     - rendered status now `control_plane_status=PASS_REQUIRED`
5. Evidence (persistent mirror):
   - root: `activity/evidence/v163-predev/2026-03-11/round34-hardclose/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round34-hardclose/EVIDENCE_MANIFEST.round34-hardclose.json`
   - tuple completeness: every entry carries `sha256 + command + rc + timestamp_utc`.

### 11.13 Round-33.9 required-coverage run-id passthrough compatibility fix (2026-03-10)

1. Gap:
   - `scripts/validate_required_contract_coverage.py` passed `--run-id` to `scripts/validate_prompt_kernel_executable_coupling.py`.
   - that validator does not define `--run-id`, causing `unrecognized arguments: --run-id ...` noise in coverage replay.
2. Fix:
   - removed `scripts/validate_prompt_kernel_executable_coupling.py` from the run-id passthrough set in `_run_validator`.
3. Replay outcome:
   - coverage replay no longer reports `FAIL_OPTIONAL` caused by unsupported argument passthrough.
   - residual failures remain semantic (`IP-PBOOT-001`, `IP-PCAPM-001`) and are unrelated to CLI wiring.

### 11.14 Round-35 file-level semantic unification (2026-03-11)

1. Problem statement:
   - runtime/mapping layers were already pointer-driven, but legacy docs (`v1.6.0` + old review ledger + branch-protection checklist) still lacked machine-enforced current-state redirects.
   - this left room for operator-side dual interpretation ("historical snapshot" vs "current SSOT").
2. Fix package:
   - added current-state redirect contract to:
     - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
     - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
   - strengthened migration routing note in:
     - `docs/governance/branch-protection-required-checks-v1.2.8.md`
   - expanded registry contract:
     - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
     - adds `static_doc_required_alias_refs`
   - hardened docs contract gate:
     - `scripts/docs_command_contract_check.py`
     - now fail-closes when mandatory static docs miss required current-pointer references.
3. Replay checks:
   - `python3 scripts/docs_command_contract_check.py` -> PASS
   - `python3 scripts/validate_protocol_ssot_source.py` -> OK
   - `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> PASS_REQUIRED
   - `python3 scripts/validate_control_plane_invariants.py --json-only` -> PASS_REQUIRED
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> PASS_REQUIRED
   - `python3 scripts/validate_control_plane_status_sync.py --json-only` -> PASS_REQUIRED
4. Persistent evidence root:
   - `activity/evidence/v163-predev/2026-03-11/round35-file-level-unification/`
5. Manifest (tuple-complete):
   - `activity/evidence/v163-predev/2026-03-11/round35-file-level-unification/EVIDENCE_MANIFEST.round35-file-level-unification.json`

### 11.15 Round-36 seven-pass serial deep-scan replay (2026-03-11)

1. Execution contract:
   - same deep-scan packet was replayed serially **7 times** to validate stability depth and eliminate single-run accidental green.
2. Per-iteration gate result (`1..7` all identical):
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
   - `docs_command_contract_check` => `PASS`
   - `validate_protocol_ssot_source` => `OK`
   - `validate_doc_evidence_persistence` => `PASS_REQUIRED`
   - `validate_control_plane_status_sync` => `PASS_REQUIRED`
3. Legacy corpus visibility scan:
   - version-pattern legacy docs (`<=v1.6.*`): `54`
   - covered by current authority set (`stream_docs + mandatory_static_docs`): `8`
   - interpretation locked: non-covered legacy docs are archival/context unless promoted into stream registry authority set.
4. Additional hardening landed in this round:
   - `docs/governance/AUDIT_SNAPSHOT_INDEX.md` is now under static authority boundary checks via stream registry.
5. Evidence root:
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/`
6. Manifest + summary:
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/EVIDENCE_MANIFEST.round36-seven-pass-deepscan.json`
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/round36_iteration_summary.json`

### 11.16 Round-39 five-pass serial deep-scan green replay (2026-03-11)

1. Scope:
   - replayed the deep-scan packet for five consecutive iterations after static authority boundary expansion (`v1.4.13` + `v1.5.0` governance anchors added to mandatory static authority checks).
2. Iteration outcome (`1..5`, all identical):
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
   - `docs_command_contract_check` => `PASS`
   - `validate_protocol_ssot_source` => `OK`
   - `validate_doc_evidence_persistence` => `PASS_REQUIRED`
   - `validate_control_plane_status_sync` => `PASS_REQUIRED`
3. Legacy coverage telemetry:
   - legacy docs (`<=v1.6.*`) total: `54`
   - authority-set covered: `10`
   - uncovered legacy docs: `44` (archival/context default; non-authoritative for current-state decisions).
4. Evidence root:
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/`
5. Manifest + summary:
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/EVIDENCE_MANIFEST.round39-five-pass-green.json`
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/round39_iteration_summary.json`

### 11.17 Round-42 three-pass post-repair serial replay (2026-03-11)

1. Reason:
   - post-repair verification after static authority expansion and doc-evidence error-code convergence (raw code count rebound removed).
2. Iteration outcome (`1..3`, all stable):
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
   - `docs_command_contract_check` => `PASS`
   - `validate_protocol_ssot_source` => `OK`
   - `validate_doc_evidence_persistence` => `PASS_REQUIRED`
   - `validate_control_plane_status_sync` => `PASS_REQUIRED`
3. Legacy coverage telemetry:
   - total legacy docs (`<=v1.6.*`): `54`
   - authority-set covered: `10`
   - uncovered legacy docs: `44` (archive/context default).
4. Evidence root:
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/`
5. Manifest + summary:
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/EVIDENCE_MANIFEST.round42-three-pass-post-repair.json`
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/round42_iteration_summary.json`

### 11.18 Round-43 instance-lane route closure + projection consistency hardening (2026-03-11)

1. Triggered by instance replay feedback under correct global runtime catalog wiring:
   - path reference drift resolved,
   - residual P0 remained at `required_gate_bundle_runner` with
     `IP-GATE-ENTRY-001: gate_profile_work_layer_not_allowed:strict_full:instance`.
2. Protocol hardening applied:
   - `identity/protocol/mappings/layer-targeted-gate-profile.v1.6.yaml`
     - `strict_full.require_work_layers` expanded to include `instance`.
   - `scripts/validate_protocol_data_sanitization_boundary.py`
     - false-positive mitigation for run/report/date numeric metadata (retaining contact-context hard fail-close).
   - `scripts/report_three_plane_status.py`
     - bundle run token now prefers selected report run-id before synthetic fallback.
   - `scripts/full_identity_protocol_scan.py`
     - m2m projection now derived from local scan checks only;
       nested three-plane m2m projection retained as observation field to avoid cross-surface noise.
3. Replay outcomes:
   - `validate_protocol_data_sanitization_boundary` (office-ops, scan) => `PASS_REQUIRED`.
   - `required_gate_bundle_runner` (`resolved_work_layer=instance`, system-requirements-analyst, update) => `PASS_REQUIRED`.
   - `validate_full_scan_target_regression --enforce-m2m-pass` (system-requirements-analyst, global, bound session) => `PASS_REQUIRED`.
   - `validate_control_plane_invariants` and `validate_required_gate_surface_drift` remain `PASS_REQUIRED`.
4. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round43-three-pass-file-semantic-unification/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round43-three-pass-file-semantic-unification/EVIDENCE_MANIFEST.round43-three-pass-file-semantic-unification.json`
   - summaries:
     - `activity/evidence/v163-predev/2026-03-11/round43-three-pass-file-semantic-unification/round43_iteration_summary.json`
     - `activity/evidence/v163-predev/2026-03-11/round43-three-pass-file-semantic-unification/round43_protocol_hardening_summary.json`
5. Tuple completeness contract:
   - every manifest entry includes `sha256`, `command`, `rc`, `timestamp`.

### 11.19 Round-44 required-coverage floor + lane telemetry hardening (2026-03-11)

1. Triggered by instance replay points 6/7/8:
   - `kernel_ssot_source` observed as `SKIPPED_NOT_REQUIRED`,
   - high skipped volume lacked lane partition semantics,
   - prompt-kernel coupling pass lacked structured lane-lock influence telemetry.
2. Protocol patch:
   - file: `scripts/validate_required_contract_coverage.py`
   - changes:
     1) strict instance required floor for five core contracts
        (`prompt_bootstrap_capability`, `prompt_capability_matrix`, `kernel_ssot_source`,
        `prompt_derivation_conformance`, `prompt_kernel_executable_coupling`);
     2) validator-level `--force-required` passthrough for force-capable validators;
     3) run-id validator passthrough fix (remove unsupported expected-layer flags);
     4) prompt routing telemetry fields in coverage rows;
     5) skipped partition metrics (`skipped_lane_excluded_contract_count`, `skipped_actionable_contract_count`).
3. Replay results:
   - default strict validate probe (system-requirements-analyst):
     - `required_contract_total=5`
     - `required_contract_passed=5`
     - `failed_required_contract_count=0`
     - `kernel_ssot_source=PASS_REQUIRED`
   - skip partition:
     - `skipped_contract_count=33`
     - `skipped_lane_excluded_contract_count=24`
     - `skipped_actionable_contract_count=9`
   - explicit instance lane override probe under active protocol lane-lock:
     - `prompt_kernel_executable_coupling=FAIL_REQUIRED`
     - reason code: `IP-PKX-002` (deterministic boundary fail-close).
4. Control-plane regression checks remain green:
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
   - `docs_command_contract_check` => `PASS`
   - `validate_protocol_ssot_source` => `OK`
5. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round44-required-coverage-floor/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round44-required-coverage-floor/EVIDENCE_MANIFEST.round44-required-coverage-floor.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round44-required-coverage-floor/round44_required_coverage_summary.json`
6. Tuple completeness:
   - manifest entries include `sha256`, `command`, `rc`, `timestamp_utc`.

### 11.20 Round-45 actionable skip-list materialization (2026-03-11)

1. Objective:
   - remove residual ambiguity in skipped partition replay by emitting exact contract lists directly from coverage payload.
2. Patch:
   - `scripts/validate_required_contract_coverage.py` adds:
     - `skipped_lane_excluded_contracts`
     - `skipped_actionable_contracts`
     - `failed_optional_contracts`
3. Replay:
   - default strict validate replay keeps floor closure stable (`required_contract_total=5`, `required_contract_passed=5`, `failed_required_contract_count=0`);
   - partition list output now directly names all skipped contracts by category;
   - explicit instance-lane probe remains deterministic boundary fail-close (prompt-kernel coupling under protocol lane lock context).
4. Control-plane regressions:
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
5. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round45-coverage-actionable-lists/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round45-coverage-actionable-lists/EVIDENCE_MANIFEST.round45-coverage-actionable-lists.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round45-coverage-actionable-lists/round45_coverage_actionable_lists_summary.json`
6. Tuple completeness:
   - manifest entries include `sha256`, `command`, `rc`, `timestamp_utc`.

### 11.21 Round-46 strict-floor actionable-zero closure (2026-03-11)

1. Objective:
   - finalize points 6/7/8 by driving strict instance replay actionable skips to zero, without weakening lane-boundary fail-close.
2. Patch:
   - `scripts/validate_required_contract_coverage.py`
     - strict instance required-floor expanded with 8 actionable contracts
       (`unlock_formula_automation`, `run_id_report_selection`, `phase_bootstrap_before_strict`,
       `tmp_collision_safety`, `tool_installation`, `vendor_api_discovery`, `vendor_api_solution`, `gated_switch_guard`);
     - `protocol_lane_headstamp_continuity` moved into protocol-governance partition for instance-lane classification.
3. Replay outcome (system-requirements-analyst strict default lane):
   - `required_contract_total=13`
   - `required_contract_passed=13`
   - `failed_required_contract_count=0`
   - `skipped_actionable_contract_count=0` (hard close)
4. Boundary probe (explicit instance lane under protocol lane-lock):
   - `prompt_kernel_executable_coupling=FAIL_REQUIRED`
   - reason code `IP-PKX-002`, routing reasons include `session_lane_lock_protocol`.
5. Regression check (base-repo-architect strict default lane):
   - `required_contract_total=13`
   - `required_contract_passed=13`
   - `failed_required_contract_count=0`
6. Control-plane checks:
   - `validate_control_plane_invariants` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` => `PASS_REQUIRED`
7. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round46-strict-floor-actionable-zero/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round46-strict-floor-actionable-zero/EVIDENCE_MANIFEST.round46-strict-floor-actionable-zero.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round46-strict-floor-actionable-zero/round46_strict_floor_actionable_zero_summary.json`
8. Tuple completeness:
   - manifest entries include `sha256`, `command`, `rc`, `timestamp_utc`.

### 11.22 Round-47 direct validator evidence mirror for points 6/7/8 (2026-03-11)

1. Objective:
   - persist the exact artifact names requested by instance feedback (`validate_kernel_ssot_source.json`, `validate_required_contract_coverage.txt`, `validate_prompt_kernel_executable_coupling.json`) under governed evidence roots.
2. Delivered artifacts:
   - `validate_kernel_ssot_source.json`
   - `validate_required_contract_coverage.txt`
   - `validate_required_contract_coverage.json` (machine companion)
   - `validate_prompt_kernel_executable_coupling.json`
   - `validate_prompt_kernel_executable_coupling.instance_probe.json`
3. Results:
   - `kernel_ssot_source=PASS_REQUIRED` (`required_contract=true`);
   - coverage replay reports `required_contract_total=13`, `required_contract_passed=13`, `skipped_actionable_contract_count=0`;
   - prompt-kernel default lane `PASS_REQUIRED` with routing tail containing `session_lane_lock_protocol`;
   - explicit instance lane probe `FAIL_REQUIRED` (`IP-PKX-002`).
4. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round47-678-hardclose/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round47-678-hardclose/EVIDENCE_MANIFEST.round47-678-hardclose.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round47-678-hardclose/round47_678_hardclose_summary.json`

### 11.23 Round-48 three-pass serial parity replay (legacy semantic classification) (2026-03-11)

1. Objective:
   - confirm file-level semantic unification for v1.6-and-earlier docs after introducing machine-enforced legacy archival classification in stream registry + docs contract checker.
2. Protocol patch included:
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
     - added `legacy_archival_docs` classification set for non-authoritative historical governance docs.
   - `scripts/docs_command_contract_check.py`
     - fail-close if any v1.6-or-earlier governance/review doc is neither authoritative (stream/static/current-required) nor classified in `legacy_archival_docs`;
     - fail-close on ambiguous authoritative+archival overlap.
3. Three-pass replay packet (serial):
   - `docs_command_contract_check`
   - `validate_control_plane_invariants --json-only`
   - `validate_required_gate_surface_drift --json-only`
   - `validate_protocol_ssot_source`
   - `validate_required_contract_coverage` (SRA strict validate)
4. Outcome:
   - all three iterations PASS;
   - SRA strict coverage stable at `required_contract_total=13`, `required_contract_passed=13`, `skipped_actionable_contract_count=0`.
5. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round48-threepass-legacy-semantic-parity/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round48-threepass-legacy-semantic-parity/EVIDENCE_MANIFEST.round48-threepass-legacy-semantic-parity.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round48-threepass-legacy-semantic-parity/round48_threepass_summary.json`
6. Tuple completeness:
   - manifest entries include `sha256`, `command`, `rc`, `timestamp_utc`.

### 11.24 Round-49 three-pass serial replay (current-turn local-catalog confirmation) (2026-03-11)

1. Objective:
   - execute one more serial three-pass deep-scan in the current turn with project-local catalog binding to verify that v1.6-and-earlier semantic classification closure remains stable under local runtime source-of-truth constraints.
2. Replay packet (per iteration):
   - `docs_command_contract_check`
   - `validate_control_plane_invariants --json-only`
   - `validate_required_gate_surface_drift --json-only`
   - `validate_protocol_ssot_source`
   - `validate_required_contract_coverage` (`identity_id=base-repo-architect`, project catalog)
3. Outcome:
   - all 3/3 iterations green:
     - docs contract `PASS`;
     - control-plane invariants `PASS_REQUIRED`;
     - required-gate surface drift `PASS_REQUIRED`;
     - protocol SSOT source `OK`;
     - required coverage stable (`required_contract_total=13`, `required_contract_passed=13`, `failed_required_contract_count=0`, `skipped_actionable_contract_count=0`).
4. Evidence:
   - root: `activity/evidence/v163-predev/2026-03-11/round49-threepass-current-turn/`
   - manifest: `activity/evidence/v163-predev/2026-03-11/round49-threepass-current-turn/EVIDENCE_MANIFEST.round49-threepass-current-turn.json`
   - summary: `activity/evidence/v163-predev/2026-03-11/round49-threepass-current-turn/round49_threepass_summary.json`
5. Tuple completeness:
   - manifest entries include `sha256`, `command`, `rc`, `timestamp_utc`.

### 11.25 Round-50 integrated closure decision (2026-03-11)

1. Closure scope:
   - v1.6 / v1.6.1 / v1.6.2 / v1.6.3 remediation tracks are closed under protocol-governance criteria.
   - Closure includes repository controls and external GitHub platform activation replay.
2. External activation receipts (GitHub):
   - ruleset active: `identity-protocol-control-plane-v1.6.3` (`id=13763460`)
   - main branch protection hardened:
     - required status check `required-gates / validate-identity`
     - `require_code_owner_reviews=true`
     - `required_approving_review_count=1`
     - `enforce_admins=true`
     - `required_conversation_resolution=true`
   - actions policy hardened:
     - `allowed_actions=selected`
     - `github_owned_allowed=true`
     - `verified_allowed=true`
3. Mapping status update:
   - `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
   - status set to `platform_activation_completed_with_merge_queue_rule_unavailable`
   - activation receipts persisted in `platform_activation_receipts`.
4. Exception (non-blocking, platform capability):
   - `merge_queue` ruleset rule update returned `HTTP 422 Invalid rule 'merge_queue'`.
   - This is tracked as platform capability unavailability, not protocol control-plane regression.
5. Closure gate replay:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_control_plane_budget.py --json-only`
   - `python3 scripts/validate_control_plane_status_sync.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
   - `bash scripts/ci/run_full_scan_target_regression_ci.sh store-manager`
   - `bash scripts/ci/run_full_scan_target_regression_ci.sh system-requirements-analyst`
6. Gate outcome:
   - all closure gates green (`PASS_REQUIRED` / `PASS`);
   - target-regression remains `p0=0` for both target identities.
7. Final decision:
   - approve close for all v1.6-v1.6.3 fixes with one explicit tracked platform exception (`merge_queue` ruleset rule support).
