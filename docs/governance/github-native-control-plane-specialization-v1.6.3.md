# GitHub-Native Control Plane Specialization (v1.6.3)

Status: Planned (intake completed, implementation not started)

Governance layer: protocol

Scope: simplify protocol control-plane complexity by offloading platform-generic controls to GitHub native capabilities while retaining protocol semantic fail-close gates in-repo.

## 0) Why v1.6.3 is a dedicated stream

1. This is a control-plane migration, not a single validator patch.
2. Changes cross repository policy, workflow triggers, required-check naming, merge strategy, and review ownership.
3. Safe rollout requires evaluate -> active phases and reversible checkpoints.

Therefore this stream is split from v1.6.2 and must be executed as a dedicated governance version.

## 1) Full-repo deep-scan baseline (2026-03-10)

### 1.1 Measured complexity baseline

1. Script inventory:
   - total scripts under `scripts/`: 208
   - `validate_*.py` scripts: 145
2. Error-code surface:
   - unique `IP-*` codes in scripts/identity/docs: 457
3. Required-gate workflow load:
   - Python script invocations in `.github/workflows/_identity-required-gates.yml`: 121
   - unique scripts invoked in the same workflow: 115
4. Large control-plane hot files (LOC):
   - `scripts/report_three_plane_status.py`: 4561
   - `scripts/full_identity_protocol_scan.py`: 4152
   - `scripts/identity_creator.py`: 3924
   - `scripts/release_readiness_check.py`: 2295

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

This file defines:

1. baseline metrics
2. platform-offload control IDs (`cp-gh-*`)
3. repo-retained semantic contracts
4. phase targets and rollback modes

Hard rule: implementation steps in v1.6.3 must reference this YAML; avoid one-off script hardcoding for migration decisions.

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
