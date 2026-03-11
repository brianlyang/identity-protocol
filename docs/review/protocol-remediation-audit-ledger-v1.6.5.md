# Protocol Remediation Audit Ledger (v1.6.5 dual-layer stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review ledger for v1.6.5 platform-native file-governance offload + super-linter stabilization.

Companion governance SSOT:

1. `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`
2. `identity/protocol/mappings/github-control-plane-offload.current.yaml`
3. `identity/protocol/mappings/control-plane-status.current.yaml`
4. `identity/protocol/mappings/control-plane-invariants.current.yaml`
5. `identity/protocol/mappings/stream-doc-registry.current.yaml`
6. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`

## State interpretation guard

1. This file records review posture and replay checkpoints.
2. Normative contract semantics remain in the companion governance document.
3. If this ledger conflicts with governance SSOT or mapping status, this ledger is stale.

## 0) Baseline replay (2026-03-11)

Machine baseline at stream start:

1. `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only` => `PASS_REQUIRED`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only` => `PASS_REQUIRED`
4. `python3 scripts/docs_command_contract_check.py` => `PASS`

Baseline posture at stream intake:

1. v1.6.3 platform-activation receipts exist and remain active.
2. v1.6.4 monotonic fail-close hardening is retained in required gate lane.
3. Ruleset-level path/extension/size specialization is not yet fully codified in this repository stream.
4. Super-linter is not yet standardized as an explicit required check in protocol CI.

Verdict: `Policy PASS / Implementation CONDITIONAL PASS`.

## 1) Review focus (what v1.6.5 must close)

1. **Platform-native offload depth**
   - move path/extension/size style controls to rulesets where semantics are equivalent.
2. **Repository lint convergence**
   - provide one fixed-profile super-linter required check, not fragmented ad-hoc lint behavior.
3. **No semantic dilution**
   - ensure RQ-019/RQ-034/RQ-035 fail-close semantics stay repo-retained and unchanged in strictness.
4. **Performance guard**
   - keep business preflight loop under target latency (`P95 < 3 minutes`).

## 2) Cross-verification findings (frozen for this stream)

### 2.1 Roundtable/internal replay

1. Existing required checks are stable and green.
2. Required-gates CI surfaces are already drift-checked and merge-group compatible.
3. Complexity reduction target should focus on platform-expressible controls, not semantic validator deletion.

### 2.2 Vendor/platform references

1. GitHub rulesets are the primary vehicle for native repository restrictions.
2. Required-check/merge-queue behavior depends on stable check naming and proper workflow trigger coverage.
3. OpenAI Codex GitHub Action safety guidance is aligned with strict boundary and minimal-scope automation patterns.

### 2.3 Protocol reference anchors

1. `identity/protocol/mappings/github-control-plane-offload.current.yaml`
2. `.github/workflows/protocol-ci.yml`
3. `.github/workflows/identity-protocol-ci.yml`
4. `.github/workflows/_identity-required-gates.yml`
5. `scripts/validate_required_gate_surface_drift.py`

### 2.4 Instance feedback absorption (2026-03-11, system-requirements-analyst)

Accepted high-value findings from instance-side four-track replay:

1. Manageability verdict is positive for the dual-layer design itself:
   - governance model `YES` (clear platform-vs-repo split).
2. Closure verdict must remain conditional at this checkpoint:
   - script-side 4/6 release gates are currently machine-green.
   - remaining 2/6 are implementation/activation closures:
     - super-linter required-check activation in workflow/check surface
     - ruleset receipt closure for path/extension/size controls (or explicit platform exception).
3. Merge-queue capability limitation must remain explicit in mapping receipts:
   - no silent omission when platform API rejects `merge_queue` ruleset rule.
4. `/tmp` replay files are acceptable for local diagnosis but cannot be promoted as sole governance evidence.

Action taken:

1. Findings above are now normalized into stream-level acceptance wording (section 4 and section 6).
2. No semantic validator scope was expanded/reduced based on this feedback; only closure posture and activation obligations are tightened.

## 3) Implementation checklist (v1.6.5)

### 3.1 Governance/data-plane readiness (must complete first)

1. stream docs registered in stream-doc registry and alias requirements.
2. strict evidence allowlist rows registered for v1.6.5 governance/review docs.
3. audit index updated with v1.6.5 canonical pointers.

### 3.2 Code/CI hardening

1. add super-linter workflow (or reusable lane) with fixed profile.
2. bind super-linter check name into required checks/ruleset intent map.
3. enforce anti-bypass in drift/invariant validators for newly introduced lint lane.
4. keep existing semantic validators unchanged except integration wiring.

### 3.3 Platform activation and receipt closure

1. apply ruleset restrictions for file path/extension/size.
2. verify required-check binding includes required gates + super-linter.
3. record activation receipts and exceptions (if any) in offload mapping status.

## 4) Acceptance criteria

No implementation closure is accepted unless all checks pass:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. super-linter required check green in PR context
6. ruleset activation receipt includes path/extension/size outcome (or explicit platform exception)

## 5) Residual risk register (initial)

1. **P1**: ruleset capability drift across repository plans/tiers may leave partial activation.
   - mitigation: explicit receipt + exception capture in mapping.
2. **P1**: super-linter profile over-expansion may violate fast feedback SLO.
   - mitigation: fixed minimal profile first, expand only with measured budget.
3. **P2**: duplicate enforcement between rulesets and repo scripts may re-introduce complexity.
   - mitigation: offload matrix review before adding new script-level controls.

## 6) Current posture

Posture: `CONDITIONAL_GO` for v1.6.5 implementation.

Reason:

1. governance/review baseline and boundaries are explicit and machine-checkable.
2. repository-side v1.6.5 code landing is complete and integrated into control-plane gates.
3. final closure still depends on platform activation receipts (ruleset file-governance controls + required-check activation confirmation).

## 7) Integration closure round (2026-03-12, base-repo-architect self-drive)

### 7.1 Code landing and immediate commits

This round finished the repository-side v1.6.5 integration with immediate-per-file commits:

1. `2f314ed` — add `.github/workflows/super-linter.yml` with `pull_request` + `push(main)` + `merge_group(checks_requested)` triggers.
2. `81c7856` — add `identity/protocol/mappings/github-control-plane-offload.v1.6.5.yaml`.
3. `3605915` — switch `github-control-plane-offload.current.yaml` to v1.6.5.
4. `8aed679` — extend `validate_required_gate_surface_drift.py` with super-linter workflow/token contract.
5. `205b02b` — require `cp-gh-006` in `control-plane-invariants.v1.6.yaml`.
6. `2c85d37` — fix `validate_control_plane_budget.py` to resolve versioned acceptance target keys (`acceptance_targets_v165/v164/v163` + generic fallback).
7. `e27c267` — refresh `control-plane-status.v1.6.json` after budget resolver fix.

### 7.2 Self-test rounds (>=5 required; 5 executed)

All rounds passed:

1. Round-1: `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`.
2. Round-2: `python3 scripts/validate_required_gate_surface_drift.py --json-only` => `PASS_REQUIRED`.
3. Round-3: `python3 scripts/validate_control_plane_budget.py --json-only` => `PASS_REQUIRED`.
4. Round-4: `python3 scripts/validate_control_plane_status_sync.py --json-only` => `PASS_REQUIRED`.
5. Round-5: `python3 scripts/docs_command_contract_check.py` => `PASS`.

### 7.3 Deep-scan rounds (>=5 required; 5 executed)

All rounds passed under strict actor/session binding:

1. Round-1: `full_identity_protocol_scan --scan-mode target` (`base-repo-architect`, project) => `summary.p0=0`, `summary_m2m.fail=0`.
2. Round-2: `full_identity_protocol_scan --scan-mode target` (`base-repo-audit-expert-v3`, project) => `summary.p0=0`, `summary_m2m.fail=0`.
3. Round-3: `validate_full_scan_target_regression --identity-id base-repo-architect --enforce-m2m-pass` => `PASS_REQUIRED`.
4. Round-4: `validate_full_scan_target_regression --identity-id base-repo-audit-expert-v3 --enforce-m2m-pass` => `PASS_REQUIRED`.
5. Round-5: `full_identity_protocol_scan --scan-mode target --with-docs-contract` (`base-repo-architect`, project) => `summary.p0=0`, `summary_m2m.fail=0`.

Cross-check note:

1. A deliberate negative probe (reusing one session id across multiple identities) produced expected strict failure (`summary_m2m.fail>0`), confirming actor-session isolation hardening still blocks silent cross-identity drift.

### 7.4 Cross-CWD robustness hardening (2026-03-12 follow-up)

During serial replay from workspace root (not `identity-protocol-local` cwd), two path-coupling defects were reproduced and fixed:

1. `validate_full_scan_target_regression.py` invoked `scripts/full_identity_protocol_scan.py` via relative path and inherited caller cwd.
   - Fix commits:
     - `ab13d5a` (repo-path aware script/catalog resolution)
     - `6ad7b61` (force subprocess cwd to protocol repo root)
2. `full_identity_protocol_scan.py` defaulted `--repo-root` to `"."`, causing repo-catalog miss when invoked outside protocol repo cwd.
   - Fix commit:
     - `8fd8808` (default repo-root switched to script-local protocol root)

Post-fix serial replay results:

1. `validate_full_scan_target_regression` (workspace root invocation) => `PASS_REQUIRED`.
2. `full_identity_protocol_scan --scan-mode target --with-docs-contract` (workspace root invocation) => `summary.p0=0`, `summary_m2m.fail=0`.
