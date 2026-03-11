# GitHub-Native Control Plane Specialization (v1.6.3)

Status: In execution (repository code development completed, platform activation pending)

Governance layer: protocol

Scope: simplify protocol control-plane complexity by offloading platform-generic controls to GitHub native capabilities while retaining protocol semantic fail-close gates in-repo.

Companion review ledger:

- `docs/review/protocol-remediation-audit-ledger-v1.6.3.md`

## State interpretation guard (mandatory)

1. Sections marked as Round-31 intake/pre-development are historical baseline snapshots.
2. Current-state judgment must follow the latest implemented addendum in this stream (Round-32 or newer) plus mapping status:
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
3. If historical intake text conflicts with latest addendum, historical text is archival evidence only and must not drive present-tense closure claims.

## 0) Why v1.6.3 is a dedicated stream

1. This is a control-plane migration, not a single validator patch.
2. Changes cross repository policy, workflow triggers, required-check naming, merge strategy, and review ownership.
3. Safe rollout requires evaluate -> active phases and reversible checkpoints.

Therefore this stream is split from v1.6.2 and must be executed as a dedicated governance version.

## 1) Full-repo deep-scan baseline (2026-03-10)

### 1.1 Measured complexity baseline

1. Baseline metric SSOT is **mapping-first**:
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
   - (active file) `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
2. Latest measured snapshot for this stream is anchored at:
   - `activity/evidence/v163-predev/2026-03-10/v163_state_gap_summary.json`
3. Governance text should not duplicate raw numeric baselines if the same field already exists in mapping/evidence SSOT.

### 1.2 Control-plane integration gap snapshot

1. Merge queue compatibility gap:
   - `merge_group` trigger is not wired in `protocol-ci` / `identity-protocol-ci` workflow triggers.
2. Ownership hard-gate gap:
   - repository has no `CODEOWNERS` contract at this point.
3. Policy-as-code gap:
   - branch/merge policy is still partially documented as manual checklist (`branch-protection-required-checks-v1.2.8.md`) instead of GitHub ruleset-managed source of truth.

Judgment: current system is functionally strong but structurally heavy; complexity now justifies GitHub-native offload for platform-generic controls.

## 2) Roundtable cross-verification

### T1: Internal protocol telemetry (repo scan)

1. Existing required-gates already uses reusable workflow shape (`workflow_call`) but execution payload remains script-heavy.
2. Protocol semantic controls for RQ-034/RQ-035 are functioning and must not be downgraded.
3. Current risk is not missing validation, but maintenance overhead and drift probability under continued growth.

### T2: Vendor capability track (GitHub official)

Validated against GitHub official documentation:

1. Rulesets can enforce required status checks, pull-request constraints, and branch protection policy at platform level.
2. Merge queue requires workflow support for `merge_group` events so required checks can report on queue entries.
3. CODEOWNERS provides native ownership boundaries and can be required for merges.
4. Reusable workflows support central CI logic with stable, policy-controlled entry points.
5. Actions policy can constrain action sources and reduce workflow supply-chain drift.

References:

1. https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
2. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
3. https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group
4. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
5. https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
6. https://docs.github.com/github/administering-a-repository/managing-repository-settings/disabling-or-limiting-github-actions-for-a-repository

### T3: Protocol contract compatibility track

1. GitHub-native controls can replace process and policy checks.
2. GitHub-native controls cannot replace protocol semantics:
   - multimodal evidence consistency (`asb16-rq-034`)
   - reasoning-loop fail-close semantics (`asb16-rq-035`)
   - bundle dispatch/parity semantics (`asb16-rq-019`)
3. Therefore migration principle is strict split:
   - platform handles generic governance
   - protocol scripts keep semantic contracts

### T4: Documentation and evidence operability track

1. Governance docs must remain readable and long-term replayable.
2. `/tmp` or ad-hoc log paths must not become normative evidence pointers in governance streams.
3. Canonical evidence pointers must use repo-persistent paths or a manifest index.

## 3) v1.6.3 migration SSOT (config-first, no hardcoding)

Machine-readable migration source of truth:

- `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
- Stable tooling entrypoint:
  - `identity/protocol/mappings/github-control-plane-offload.current.yaml`

This file defines:

1. baseline metrics
2. platform-offload control IDs (`cp-gh-*`)
3. repo-retained semantic contracts
4. phase targets and rollback modes

Hard rule: implementation steps in v1.6.3 must reference this YAML; avoid one-off script hardcoding for migration decisions.

### 3.1 Anti-break-chain contract (mandatory)

1. Tooling/scripts must read `*.current.yaml`, not versioned files directly.
2. `*.current.yaml` must expose `active_file` and point to a single versioned snapshot.
3. `scripts/validate_control_plane_invariants.py` fail-closes when:
   - current file is missing/unparseable
   - `active_file` is missing/unparseable
   - active file misses required fields/control IDs/retained semantic keys
4. Version upgrades are done by pointer switch (`current -> new version`), not in-place overwrite of old snapshot.

## 4) Execution phases

### Phase 1: Platform control activation (safe minimum)

1. Stabilize required-check names and bind them in rulesets.
2. Add `merge_group` event coverage to required CI workflows.
3. Keep existing semantic validators unchanged.

Exit criteria:

1. ruleset required checks active
2. merge queue run reports same required checks as pull_request runs
3. required-gate invocation count reduced to target defined in YAML phase_1

### Phase 2: Ownership + workflow policy hardening

1. Introduce `CODEOWNERS` for protocol-critical paths.
2. Enable required code-owner review in branch policy.
3. Constrain Actions sources according to repository policy.

Exit criteria:

1. code-owner review enforced for protocol-critical paths
2. actions-policy drift controls active
3. required-gate invocation count reduced to target defined in YAML phase_2

### Phase 3: Complexity debt retirement

1. Retire repo-local checks that are fully covered by GitHub native controls.
2. Keep only semantic fail-close gates in protocol scripts.
3. Re-baseline control-plane budget and invariants.

Exit criteria:

1. required-gate invocation count reduced to target defined in YAML phase_3
2. manual branch-protection checklist is no longer primary control
3. no semantic regression in RQ-034/RQ-035 negative probes

## 5) Non-negotiable invariants

1. No weakening of `FAIL_REQUIRED` semantics for multimodal/reasoning contracts.
2. No migration that makes status promotion depend on manual wording rather than machine receipts.
3. No instance-specific credential/path hardcoding introduced into protocol governance.
4. Any offload must remain reversible per phase rollback rules in the mapping YAML.

## 6) Ready-to-start judgment

1. Intake is complete for v1.6.3 start.
2. Baseline metrics and migration boundaries are explicit.
3. Offload scope is constrained and does not dilute protocol semantic guarantees.

Current judgment: Conditional Go (implementation start approved, phase-gated).

## 7) Round-31 final pre-development cross-verification addendum (2026-03-10)

### 7.1 Why this addendum exists

1. v1.6.3 has crossed the "design is correct" threshold, but development must start only with one unified, machine-replayable prep package.
2. This section freezes cross-verification outputs so implementation can be audited against a stable starting point.
3. Scope is still protocol control-plane only; no instance business logic is moved into protocol contracts.

### 7.2 Four-track deep cross-verification (T1/T2/T3/T4)

#### T1 — Internal full-repo telemetry (machine replay)

1. Required core checks remain green:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`
2. v1.6.3 phase baseline is persisted at:
   - `activity/evidence/v163-predev/2026-03-10/PREDEV_MIN_ANCHOR.json`
3. Canonical evidence index for this addendum:
   - `activity/evidence/v163-predev/2026-03-10/EVIDENCE_MANIFEST.v163-predev-round31.json`
4. Additional files are replay artifacts referenced from anchor + manifest; avoid duplicating long file lists in governance body.

#### T2 — Vendor track (GitHub official, revalidated)

Revalidated against official GitHub docs (latest pages at audit time):

1. Rulesets available rules (required checks / PR constraints / branch protection):
   - https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
2. Merge queue behavior:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
3. `merge_group` event requirement for Actions:
   - https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group
4. Required status checks troubleshooting (skip/pending behavior and merge blocking implications):
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/troubleshooting-required-status-checks
5. CODEOWNERS behavior:
   - https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
6. Reusable workflows:
   - https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
7. Repository-level Actions settings/policy:
   - https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository

Vendor-reference snapshot for this addendum:

- `activity/evidence/v163-predev/2026-03-10/github_vendor_reference_snapshot.json`

#### T3 — Protocol compatibility track (no semantic dilution)

1. Offload scope remains platform-generic only (`cp-gh-*`).
2. Semantic contracts remain repo-retained and fail-close:
   - `asb16-rq-019`
   - `asb16-rq-034`
   - `asb16-rq-035`
3. Alias-chain contract remains mandatory:
   - tooling reads `identity/protocol/mappings/github-control-plane-offload.current.yaml`
   - never direct-couple scripts + workflows to versioned `v1.6.3` file path.

#### T4 — Operability/evidence track (non-ephemeral)

1. This addendum uses persistent evidence pointers only.
2. Evidence tuple manifest:
   - `activity/evidence/v163-predev/2026-03-10/EVIDENCE_MANIFEST.v163-predev-round31.json`
3. Tuple fields remain mandatory (`sha256`, `command`, `rc`, `timestamp`).

### 7.3 No-conflict integration matrix (v1.6.2 <-> v1.6.3)

| Domain | Existing SSOT | v1.6.3 action | Conflict rule |
| --- | --- | --- | --- |
| Plugin semantic contracts | `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml` | unchanged | Never offload semantic checks to GitHub primitives |
| Control-plane invariants | `identity/protocol/mappings/control-plane-invariants.current.yaml` | add/keep offload alias checks | Fail-close if current alias chain breaks |
| Offload plan | `identity/protocol/mappings/github-control-plane-offload.current.yaml` | phase-gated implementation source | Scripts/workflows must read `.current.yaml`, not versioned file |
| Docs contracts | `scripts/docs_command_contract_check.py` | continue mandatory coverage for v1.6.3 docs | No drift between docs and executable flags |
| Evidence persistence | `scripts/validate_doc_evidence_persistence.py` | enforce persistent paths + tuple manifest | No `/tmp`-only normative evidence in governance/review deltas |

### 7.4 Phase-1 development-ready task package (implementation handoff)

#### Slice A — merge queue compatibility (lowest-risk first)

1. Add `merge_group` triggers to:
   - `.github/workflows/protocol-ci.yml`
   - `.github/workflows/identity-protocol-ci.yml`
2. Ensure required checks reported on `merge_group` and `pull_request` are name-stable.

Acceptance:

1. phase_1 `merge_group_trigger_coverage=true`.
2. No regression in required-check status publication.

#### Slice B — required check stabilization + ruleset sync

1. Freeze required check naming surface used by rulesets.
2. Remove transient naming ambiguity before slimming invocation count.

Acceptance:

1. ruleset required checks active.
2. troubleshooting-required-checks constraints have no unresolved pending/skipped blockers.

#### Slice C — ownership hard gate

1. Introduce `.github/CODEOWNERS` for protocol-critical surfaces.
2. Enable required code-owner review in policy/ruleset.

Acceptance:

1. phase_2 `codeowners_required_review_active=true`.

#### Slice D — workflow policy hardening

1. Enforce approved Actions source policy and reusable-workflow boundaries.
2. Keep semantic validators in-repo; do not over-offload.

Acceptance:

1. phase_2 `actions_policy_active=true`.

#### Slice E — controlled invocation budget reduction

1. Reduce `_identity-required-gates.yml` python invocations from `121` to phase_1 target `<=95`.
2. Reduction must come from platform-equivalent controls, not semantic gate removal.

Acceptance:

1. phase_1 invocation target met.
2. RQ-019/RQ-034/RQ-035 negative probes remain fail-close.

### 7.5 Development start gate (must all pass before coding phase closure claim)

Run:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_protocol_ssot_source.py`
5. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids store-manager,base-repo-audit-expert-v3,custom-creative-ecom-analyst,base-repo-architect --project-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --global-catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --target-source-layer both --with-docs-contract --actor-id assistant:codex --session-id run:V163-PREDEV-CHECK-20260310 --expected-work-layer protocol --out activity/evidence/v163-predev/2026-03-10/target_scan_project_global_both.summary.json`

Gate rule:

1. No claim of "phase delivered" is allowed unless the corresponding phase target fields in `github-control-plane-offload` YAML are machine-evidenced.
2. No v1.6.3 implementation claim can bypass this addendum with prose-only signoff.
3. v1.6.x stream governance/review doc set is SSOT-driven by `identity/protocol/mappings/stream-doc-registry.current.yaml`; validators must not hardcode stream doc paths independently.

### 7.6 Audit-feedback absorption (Round-31.1, 2026-03-10)

This subsection absorbs latest roundtable audit feedback and freezes the pre-dev risk order before implementation.

#### A) P1 — merge queue trigger gap (confirmed)

1. Current gap remains true:
   - `.github/workflows/protocol-ci.yml` has no `merge_group` trigger.
   - `.github/workflows/identity-protocol-ci.yml` has no `merge_group` trigger.
2. This is a **phase-1 blocker**, not a backlog nice-to-have.
3. No phase-1 closure claim is valid until both workflows emit required checks on `merge_group`.

#### B) P1 — CODEOWNERS gap (confirmed)

1. Current gap remains true:
   - no `.github/CODEOWNERS` (and no root `CODEOWNERS`) is present.
2. This is a **phase-2 hard-gate prerequisite** and must be introduced with protected-path coverage for:
   - `identity/protocol/**`
   - `scripts/**`
   - `.github/workflows/**`

#### C) P2 — branch-protection dual-source risk (confirmed)

1. `branch-protection-required-checks-v1.2.8.md` is still useful as migration-era operator guidance.
2. Under v1.6.3, it must not be interpreted as the primary normative control once rulesets are active.
3. Transitional rule:
   - policy SSOT = ruleset + offload mapping YAML;
   - checklist doc = operator mirror and troubleshooting aid.

#### D) P2 — control-plane budget boundary risk (confirmed)

1. Current budget validator uses strict `>` comparators.
2. Boundary-equal values (e.g., `error_codes == fail_threshold`) are currently WARN-space and may cause interpretation drift.
3. v1.6.3 pre-dev rule:
   - treat "equal-to-fail-threshold" as **red-adjacent risk** in review language;
   - do not describe this state as healthy headroom.
4. A comparator-tightening change (`>=`) is deferred to implementation-phase proposal so it can be assessed with CI blast-radius evidence.

#### E) P3 — evidence scope noise (confirmed)

1. Untracked evidence directories can create review noise if they are not declared as round scope.
2. v1.6.3 pre-dev convention:
   - keep one canonical evidence root per round (`activity/evidence/v163-predev/<date>/`);
   - avoid parallel ad-hoc evidence roots in the same review packet.

#### F) Priority lock (authoritative order for implementation)

1. `merge_group` parity for required checks.
2. required-check naming stability for ruleset binding.
3. CODEOWNERS + required owner-review enforcement.
4. Actions policy hardening.
5. invocation-budget reduction (without semantic contract downgrade).

## 8) Round-32 implementation completion addendum (2026-03-10)

### 8.1 Scope of this round

1. This round closes **repo-side code development** for v1.6.3 control-plane specialization.
2. Scope is implementation in repository code/config only; external GitHub settings (ruleset activation / required-owner-review toggle) are outside repo write-scope.
3. Semantic contracts remain in-repo and unchanged in responsibility boundary:
   - `asb16-rq-019`
   - `asb16-rq-034`
   - `asb16-rq-035`
4. Any earlier text in this document that describes missing `merge_group`/CODEOWNERS is historical Round-31 intake state and is superseded by this section for current-state judgment.

### 8.2 Implemented code deltas

1. Merge queue parity wired:
   - `.github/workflows/protocol-ci.yml` adds `merge_group`.
   - `.github/workflows/identity-protocol-ci.yml` adds `merge_group`.
2. Required-gates workflow flattened to reusable script entry:
   - `.github/workflows/_identity-required-gates.yml` delegates heavy runtime validation chain to:
     - `scripts/ci/run_required_runtime_gates_ci.sh`
     - `scripts/ci/run_full_scan_target_regression_ci.sh`
3. Ownership contract landed:
   - `.github/CODEOWNERS` added with protected surfaces:
     - `identity/protocol/**`
     - `scripts/**`
     - `.github/workflows/**`

### 8.3 Measured outcome (machine)

Source:

1. `activity/evidence/v163-predev/2026-03-10/v163_state_gap_summary.json`

Outcome:

1. Required-gate workflow python invocations:
   - baseline `121` -> live `15` (phase_1 target `<=95` achieved).
2. `merge_group` trigger coverage:
   - `protocol-ci=true`, `identity-protocol-ci=true`.
3. CODEOWNERS presence:
   - `true`.
4. Mapping status aligned:
   - `identity/protocol/mappings/github-control-plane-offload.v1.6.3.yaml`
   - `status=implementation_code_completed_platform_activation_pending`.

### 8.4 Mandatory replay gate status for this round

1. `python3 scripts/validate_control_plane_invariants.py --json-only` -> PASS_REQUIRED
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> PASS_REQUIRED
3. `python3 scripts/docs_command_contract_check.py` -> PASS
4. `python3 scripts/validate_protocol_ssot_source.py` -> OK
5. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> PASS_REQUIRED

Evidence mirrors:

1. `activity/evidence/v163-predev/2026-03-10/round32_control_plane_invariants.json`
2. `activity/evidence/v163-predev/2026-03-10/round32_surface_drift.json`
3. `activity/evidence/v163-predev/2026-03-10/round32_docs_command_contract_check.log`
4. `activity/evidence/v163-predev/2026-03-10/round32_ssot_source.log`
5. `activity/evidence/v163-predev/2026-03-10/round32_doc_evidence_persistence.json`

### 8.5 Residual boundary (explicitly not over-claimed)

1. Repository code development is complete for v1.6.3 phase objectives in-repo.
2. Platform-side activation remains pending:
   - ruleset required-check binding activation
   - required code-owner review enforcement
3. Therefore stream posture is:
   - **implementation code completed**
   - **platform activation pending**
   - not yet “platform fully closed”.

### 8.6 Round-32 canonical evidence entry

1. Anchor:
   - `activity/evidence/v163-predev/2026-03-10/PREDEV_MIN_ANCHOR.json`
2. Resolution matrix:
   - `activity/evidence/v163-predev/2026-03-10/audit_feedback_resolution_round32.json`
3. Manifest:
   - `activity/evidence/v163-predev/2026-03-10/EVIDENCE_MANIFEST.v163-round32-implementation.json`

## 9) Round-33 layer-targeted gate profile addendum (2026-03-10)

### 9.1 Why this addendum exists

1. Single-layer target regression previously had no canonical gate-profile contract, so scan replay always executed full required-gate bundle.
2. This created avoidable coupling between target-layer replay and non-target-layer checks.
3. v1.6.3 now standardizes this as config-first protocol control behavior.

### 9.2 Canonical contract surface

1. Mapping SSOT:
   - `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
2. Bundle execution entry:
   - `scripts/required_gate_bundle_runner.py`
   - added `--gate-profile` / `--gate-profile-file`
3. Validation gate:
   - `scripts/validate_layer_targeted_gate_profile.py`
4. Control-plane status integration:
   - `scripts/render_control_plane_status.py`
   - `scripts/validate_control_plane_status_sync.py`

### 9.3 Hard boundary (fail-close preserved)

1. Default profile is `strict_full`; existing strict behavior remains the default and is backward-compatible.
2. `targeted` profiles are accepted only for `scan` / `inspection` operations.
3. Strict operations (`activate/update/readiness/e2e/ci/validate/three-plane/mutation`) are non-trimmable; if a targeted profile is used there, bundle runner returns fail-close.
4. Target probes excluded by profile return `SKIPPED_NOT_REQUIRED` with explicit profile metadata; they are not treated as silent pass.

### 9.4 Full-scan wiring update

1. `scripts/full_identity_protocol_scan.py` now accepts:
   - `--gate-profile`
   - `--gate-profile-file`
2. The scan executor forwards both arguments to every required-gate bundle runner call.
3. Bundle receipts now carry profile metadata fields for replay:
   - `gate_profile`
   - `gate_profile_mode`
   - `gate_profile_requirement_keys`
4. `scripts/validate_required_gate_surface_drift.py` now validates delegated full-scan command arguments from parsed shell invocations (comment lines are ignored), so lineage tokens cannot be spoofed by annotation-only text.

### 9.5 Scope statement

1. This addendum introduces optional scan-layer trimming only.
2. It does not change semantic validators for retained contracts (`asb16-rq-019/034/035`).
3. It does not offload protocol semantics to GitHub platform controls.

### 9.6 Plugin alias completeness note (2026-03-10)

1. Plugin control-plane alias contract now includes:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - `identity/protocol/plugins/PROVIDER_PROFILES.current.yaml`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`
2. Rationale:
   - plugin governance pointers are managed as one control-plane family; one pointer outside alias enforcement reintroduces drift risk.
3. Enforcement:
   - `scripts/validate_control_plane_invariants.py` fail-closes alias breakage for all four pointers.
   - `scripts/validate_plugin_contract_literal_paths.py` blocks non-canonical literals for all four pointer tokens.

## 10) Round-34 cross-stream hardening addendum (2026-03-11)

### 10.1 Why this addendum exists

1. Round-33 closed alias anti-break-chain, but review feedback still highlighted three convergence items:
   - budget must enforce **continuous no-rebound**
   - `identity_creator.py` direct validator coupling remained red-adjacent
   - error-code governance needed family-level convergence framing (not only raw literal count)
2. This addendum cross-checks `v1.6.1` / `v1.6.2` / `v1.6.3` in one packet and hardens the control plane without weakening fail-close semantics.

### 10.2 Implemented hardening deltas

1. Budget validator upgraded to convergence-aware mode:
   - `scripts/validate_control_plane_budget.py`
   - adds `error_code_families` metric (numeric-suffix family collapse)
   - adds `convergence_guard` (`mode=no_rebound`) and fail-close rebound detection
2. Budget SSOT updated to dual-threshold + family convergence policy:
   - `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
   - includes `convergence_guard.ceilings` for script/error/direct-call envelopes
3. Direct validate density reduced on creator strict surface:
   - `scripts/identity_creator.py`
   - `scripts/run_identity_dialogue_feedback_bundle.py` (delegated bundle for dialogue/feedback block)
   - result: strict-surface direct validate literals for `identity_creator.py` dropped to threshold-safe range.

### 10.3 Cross-stream replay outcomes (v1.6.1 / v1.6.2 / v1.6.3)

1. `v1.6.1` headstamp closure:
   - `validate_headstamp_recurrence_closure` -> `PASS_REQUIRED` (with bound session replay)
2. `v1.6.2` plugin/governance control surface:
   - `validate_plugin_contract_literal_paths` -> `PASS_REQUIRED`
   - `validate_reasoning_loop_failclose` -> `PASS_REQUIRED`
   - `validate_multimodal_plugin_enforcement`:
     - strict `operation=validate` currently returns `FAIL_REQUIRED` + `IP-MM-RUN-002` for `base-repo-architect` due missing runtime multimodal evidence in instance report path.
     - `operation=inspection` remains `PASS_REQUIRED`.
   - interpretation rule: `IP-MM-RUN-002` in this round is instance execution-evidence debt, not protocol control-plane wiring regression.
3. `v1.6.3` control-plane core:
   - `validate_control_plane_budget` -> `PASS_REQUIRED` (no warn, no rebound)
   - `validate_control_plane_invariants` -> `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` -> `PASS_REQUIRED`
   - `validate_contract_binding_reference_integrity` -> `PASS_REQUIRED`
   - `validate_control_plane_status_sync` -> `PASS_REQUIRED`
   - rendered status: `control_plane_status=PASS_REQUIRED`.

### 10.4 Evidence (persistent-only, tuple complete)

1. Canonical root:
   - `activity/evidence/v163-predev/2026-03-11/round34-hardclose/`
2. Manifest:
   - `activity/evidence/v163-predev/2026-03-11/round34-hardclose/EVIDENCE_MANIFEST.round34-hardclose.json`
3. Every evidence row in manifest includes:
   - `sha256`
   - `command`
   - `rc`
   - `timestamp_utc`

### 10.5 Governance lock for future rounds

1. Budget is now governed by both threshold and monotonic convergence:
   - crossing warn/fail thresholds remains guarded
   - rebound above frozen ceilings is fail-close
2. Error-code governance must track both views:
   - raw count (telemetry continuity)
   - family-normalized count (convergence decision signal)
3. Creator strict-surface validator fan-out should continue to prefer delegated bundles for repeatable blocks to avoid reintroducing direct literal sprawl.

## 11) Round-35 file-level semantic unification addendum (2026-03-11)

### 11.1 Why this addendum exists

1. Deep-scan feedback identified a file-level semantics risk: legacy v1.6/v1.2 governance-review docs still carried historical thresholds/snapshots that could be misread as current-state truth.
2. Control-plane runtime already follows current-pointer mappings, but docs-side semantics needed the same machine-enforced convergence to avoid dual-source interpretation.

### 11.2 What was hardened (code + mapping + legacy docs)

1. Legacy v1.6 governance/review docs now include explicit current-state redirects:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.md`
2. Legacy branch-protection checklist migration routing now explicitly references stream registry pointer:
   - `docs/governance/branch-protection-required-checks-v1.2.8.md`
3. Stream registry now defines static-doc alias-reference requirements (not only stream-doc requirements):
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. Docs contract gate now fail-closes when mandatory static docs miss required current-pointer alias refs:
   - `scripts/docs_command_contract_check.py`

### 11.3 Unified semantic contract (frozen)

1. Runtime execution truth:
   - `scripts/**` + `identity/protocol/mappings/*.current.yaml`
2. Documentation truth boundary:
   - legacy docs may retain historical snapshots, but must include explicit redirect to current-pointer SSOT.
3. Machine anti-drift:
   - static legacy docs are now covered by alias-reference checks through the stream-doc registry contract.

### 11.4 Replay results for this round

1. `python3 scripts/docs_command_contract_check.py` -> PASS
2. `python3 scripts/validate_protocol_ssot_source.py` -> OK
3. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> PASS_REQUIRED
4. `python3 scripts/validate_control_plane_invariants.py --json-only` -> PASS_REQUIRED
5. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> PASS_REQUIRED
6. `python3 scripts/validate_control_plane_status_sync.py --json-only` -> PASS_REQUIRED

### 11.5 Evidence (persistent mirror + tuple-complete)

1. Root:
   - `activity/evidence/v163-predev/2026-03-11/round35-file-level-unification/`
2. Manifest:
   - `activity/evidence/v163-predev/2026-03-11/round35-file-level-unification/EVIDENCE_MANIFEST.round35-file-level-unification.json`
3. Tuple contract:
   - every record contains `sha256`, `command`, `rc`, `timestamp_utc`.

## 12) Round-36 seven-pass serial deep-scan addendum (2026-03-11)

### 12.1 Execution requirement and scope

1. A serial deep-scan replay was executed **7 consecutive iterations** under the same repository head to validate convergence depth and anti-flake stability.
2. Scan scope:
   - active v1.6 streams (`v1.6.1 / v1.6.2 / v1.6.3`)
   - legacy v1.6-and-earlier docs coverage visibility against stream-registry authority boundary
   - code-plane contract gates bound to docs semantics.

### 12.2 Seven-pass replay status (all iterations)

For each iteration (`1..7`):

1. `validate_control_plane_invariants` -> `PASS_REQUIRED`
2. `validate_required_gate_surface_drift` -> `PASS_REQUIRED`
3. `docs_command_contract_check` -> `PASS`
4. `validate_protocol_ssot_source` -> `OK`
5. `validate_doc_evidence_persistence` -> `PASS_REQUIRED`
6. `validate_control_plane_status_sync` -> `PASS_REQUIRED`

### 12.3 File-level semantics result

1. Legacy docs discovered by version pattern (`<= v1.6.*`): `54`.
2. Current authoritative set coverage via stream registry (`stream_docs + mandatory_static_docs`): `8`.
3. Interpretation contract:
   - uncovered legacy docs are archival/context corpus by default,
   - current-state decisions must resolve through the authoritative set from:
     - `identity/protocol/mappings/stream-doc-registry.current.yaml`.
4. To prevent boundary drift, static authority checks were expanded to include:
   - `docs/governance/AUDIT_SNAPSHOT_INDEX.md` in mandatory static coverage + alias-reference checks.

### 12.4 Evidence

1. Root:
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/`
2. Manifest:
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/EVIDENCE_MANIFEST.round36-seven-pass-deepscan.json`
3. Iteration summary:
   - `activity/evidence/v163-predev/2026-03-11/round36-seven-pass-deepscan/round36_iteration_summary.json`

## 13) Round-39 five-pass serial deep-scan green closure (2026-03-11)

### 13.1 Execution scope

1. Replayed the same deep-scan packet serially for **5 iterations** after extending static authority boundary to include v1.4.13/v1.5.0 governance anchors.
2. Scope remained file-level semantic convergence (not business logic):
   - stream/current-pointer authority alignment
   - docs contract + evidence persistence
   - required-gate strict surface drift
   - control-plane status projection sync.

### 13.2 Five-pass replay outcome (all iterations green)

For each iteration (`1..5`):

1. `validate_control_plane_invariants` -> `PASS_REQUIRED`
2. `validate_required_gate_surface_drift` -> `PASS_REQUIRED`
3. `docs_command_contract_check` -> `PASS`
4. `validate_protocol_ssot_source` -> `OK`
5. `validate_doc_evidence_persistence` -> `PASS_REQUIRED`
6. `validate_control_plane_status_sync` -> `PASS_REQUIRED`

### 13.3 Coverage signal (legacy corpus vs authority boundary)

1. legacy docs discovered by version pattern (`<= v1.6.*`): `54`
2. covered by authoritative set (`stream_docs + mandatory_static_docs`): `10`
3. uncovered legacy docs: `44` (archival/context by default, non-authoritative for current-state decisions unless promoted into stream registry authority set).

### 13.4 Evidence

1. root:
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/`
2. manifest:
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/EVIDENCE_MANIFEST.round39-five-pass-green.json`
3. iteration summary:
   - `activity/evidence/v163-predev/2026-03-11/round39-five-pass-green/round39_iteration_summary.json`

## 14) Round-42 three-pass post-repair deep-scan closure (2026-03-11)

### 14.1 Why this pass exists

1. After extending static authority boundaries to include v1.5 review lane and collapsing doc-evidence error code inflation, a fresh serial replay was required to confirm stability under repaired control-plane budgets.
2. Goal: verify no regression on file-level unified semantics while preserving strict fail-close gates.

### 14.2 Three-pass serial replay outcome

For each iteration (`1..3`):

1. `validate_control_plane_invariants` -> `PASS_REQUIRED`
2. `validate_required_gate_surface_drift` -> `PASS_REQUIRED`
3. `docs_command_contract_check` -> `PASS`
4. `validate_protocol_ssot_source` -> `OK`
5. `validate_doc_evidence_persistence` -> `PASS_REQUIRED`
6. `validate_control_plane_status_sync` -> `PASS_REQUIRED`

### 14.3 Legacy coverage telemetry

1. legacy docs discovered by version pattern (`<= v1.6.*`): `54`
2. covered by authoritative set (`stream_docs + mandatory_static_docs`): `10`
3. uncovered legacy docs: `44` (explicit archive/context default unless promoted into stream registry authority set).

### 14.4 Evidence

1. root:
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/`
2. manifest:
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/EVIDENCE_MANIFEST.round42-three-pass-post-repair.json`
3. summary:
   - `activity/evidence/v163-predev/2026-03-11/round42-three-pass-post-repair/round42_iteration_summary.json`
