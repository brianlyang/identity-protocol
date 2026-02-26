# Identity Base Protocol Runtime Retro And Governance Feedback (v1.4.13)

Date: 2026-02-26
Type: Protocol-layer retrospective + governance hardening
Status: Implemented baseline + continuous hardening
Audience: base-repo architect / audit expert / protocol maintainers

---

## 0. Scope Statement (Mandatory)

This document is protocol-only.

1. It does not include any real business scenario.
2. It does not include domain-specific output claims.
3. It does not include user-specific absolute paths as normative requirements.
4. It does not encode one identity instance as protocol truth.

Protocol baseline must remain instance-agnostic and environment-agnostic, similar to skill protocol governance.

---

## 1. Cross-Validation Baseline (Protocol Only)

Validation date baseline: 2026-02-26 (local run)

### 1.1 Required protocol gates

Preflight command (recommended before running protocol gates):

```bash
bash scripts/preflight_protocol_audit_env.sh
```

Release-grade strict profile (requires GitHub auth readiness):

```bash
bash scripts/preflight_protocol_audit_env.sh --require-gh-auth
```

Interpretation rule:

1. `IP-CAP-003` under strict capability policy with invalid/missing `gh auth` is environment-auth blocked.
2. It is not a protocol-regression signal by itself.

Command set:

```bash
python3 scripts/validate_identity_protocol.py
python3 scripts/validate_identity_local_persistence.py
python3 scripts/validate_identity_creation_boundary.py
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_release_workspace_cleanliness.py
python3 scripts/validate_protocol_ssot_source.py
python3 scripts/validate_protocol_handoff_coupling.py --base HEAD~1 --head HEAD
```

Observed result:

1. `validate_identity_protocol.py`: PASS
2. `validate_identity_local_persistence.py`: PASS
3. `validate_identity_creation_boundary.py`: PASS (4/4)
4. `docs_command_contract_check.py`: PASS (index-driven dynamic coverage; current run: `docs checked=23`, `command snippets checked=103`)
5. `validate_release_workspace_cleanliness.py`: PASS
6. `validate_protocol_ssot_source.py`: PASS
7. `validate_protocol_handoff_coupling.py`: PASS

### 1.2 Path governance proof

Command set:

```bash
python3 scripts/export_route_quality_metrics.py --catalog identity/catalog/identities.yaml --identity-id store-manager
IDENTITY_RUNTIME_OUTPUT_ROOT=/tmp/identity-runtime \
python3 scripts/export_route_quality_metrics.py --catalog identity/catalog/identities.yaml --identity-id store-manager
```

Observed result:

1. Default output path inside protocol repo is blocked with `IP-PATH-001` (expected hard boundary).
2. Explicit runtime root (`IDENTITY_RUNTIME_OUTPUT_ROOT`) passes (expected recoverable behavior).

### 1.3 Tool-chain governance proof

Command set:

```bash
actionlint .github/workflows/*.yml
sg scan -r .github/ast-grep/no-default-repo-runtime-fallback.yml .
gitleaks dir . -f json -r ${TMPDIR:-/tmp}/gitleaks-ip-local.json --redact --no-banner
```

Observed result:

1. `actionlint`: PASS
2. `ast-grep`: PASS
3. `gitleaks`: no leaks found (`[]`)

### 1.4 Landing snapshot (implemented in this branch)

The following protocol hardening items from this retro are now landed:

1. `IP-DCIC` dialogue validator chain:
   - `scripts/validate_identity_dialogue_content.py`
   - `scripts/validate_identity_dialogue_cross_validation.py`
   - `scripts/validate_identity_dialogue_result_support.py`
2. Shared contract helper:
   - `scripts/dialogue_governance_common.py`
3. Gate wiring:
   - `scripts/e2e_smoke_test.sh`
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `.github/workflows/_identity-required-gates.yml`
4. Documentation/index sync:
   - `docs/governance/AUDIT_SNAPSHOT_INDEX.md`
   - compatibility alias
     `docs/governance/office-ops-expert-instance-runtime-retro-and-protocol-feedback-v1.4.13.md`
5. SSOT enforcement validators:
   - `scripts/validate_protocol_ssot_source.py`
   - `scripts/validate_protocol_handoff_coupling.py`

---

## 2. Protocol-Level Findings (No Business Coupling)

### 2.1 Confirmed strengths

1. Path hard isolation is enforced (`IP-PATH-001` default block).
2. Repo exception model is explicit and audited (confirm token + purpose string).
3. Docs command contract and workspace cleanliness are machine-gated.
4. CI-side static governance stack is active (`actionlint`, `ast-grep`, `gitleaks`).

### 2.2 Remaining protocol concerns

1. Recoverable blocked flow must remain fail-operational across all validators.
2. Capability arbitration linkage should distinguish capability-blocked versus metrics-triggered upgrade semantics.
3. Three-plane repo status should stay tied to tracked workspace state to prevent false-closed claims.

---

## 3. Mandatory Anti-Coupling Requirements (New)

### 3.1 No business-scene contamination

Base protocol docs and validators MUST NOT depend on:

1. Business filenames, business folders, or domain-specific data schemas.
2. Business acceptance criteria as protocol gate requirements.
3. Any real task payload as protocol truth.

Allowed:

1. Generic examples in `identity/runtime/examples/...`.
2. Synthetic fixtures designed for protocol contract validation.

### 3.2 No hardcoded environment paths

Protocol baseline MUST use placeholders instead of user-specific absolute paths.

Required placeholders:

1. `${REPO_ROOT}`
2. `${IDENTITY_HOME}`
3. `${IDENTITY_CATALOG}`
4. `${IDENTITY_RUNTIME_OUTPUT_ROOT}`

Disallowed in protocol contracts:

1. `/Users/<name>/...` as normative path.
2. One fixed local machine directory as mandatory requirement.
3. Hardcoded runtime fallback without explicit opt-in flag.

### 3.3 No hardcoded identity binding

Protocol contracts MUST NOT hardcode a single identity id as baseline behavior.

Allowed:

1. `--identity-id <target>` as runtime parameter.
2. `IDENTITY_IDS` for deterministic target scope.

Disallowed:

1. Hidden default identity in protocol-critical validators.
2. Cross-identity fallback in validation and learning loops.

---

## 4. Skill-Protocol Parity Requirements

Identity protocol should match skill protocol governance patterns:

1. Explicit install/runtime scope selection before execution.
2. Default-safe mode with explicit and auditable escape-hatches.
3. Contract-first validation before state mutation.
4. Machine-verifiable evidence for every state transition.

This parity is about governance model, not reusing business task content.

---

## 5. Architect Execution Plan (Protocol Layer)

### P0

1. Add a protocol-doc purity validator to block business-coupled and hardcoded path patterns in governance docs.
2. Enforce capability-blocked recoverable semantics across upgrade/arbitration validators.
3. Keep path hard-boundary failures (`IP-PATH-*`) as fail-closed and recoverable blocked states as fail-operational.

### P1

1. Add explicit validator for canonical session pointer consistency (catalog-scoped session state).
2. Add validator for no-default-identity hardcoding in protocol scripts.
3. Extend ast-grep policy set for path governance anti-pattern variants.

### P2

1. Add trend metrics for protocol-gate stability and false-green reduction.
2. Publish protocol-only reference templates for new identity instances.

---

## 6. Release Gate Language (Protocol Only)

### Go

All protocol gates pass and no hardcoded/business-coupled policy violations exist.

### Conditional Go

Protocol gates pass but release-plane cloud closure evidence is missing.

### Blocked

Any hard-boundary path violation, contract purity violation, or state-pointer inconsistency remains unresolved.

---

## 7. Final Conclusion

Current protocol baseline is significantly hardened, but long-term closure requires formalizing two things as mandatory contracts:

1. protocol purity (no business coupling, no hardcoding)
2. recoverable blocked semantics consistency across validators

These two constraints must be enforced by machine gates, not by reviewer memory.

---

## 8. Requirement Breakdown (For Architect Implementation)

This section is the executable requirement spec. It is protocol-layer only.

### 8.1 Problem statement

Current identity protocol has reached a stable baseline, but three governance gaps still cause recurring review disputes:

1. protocol docs and scripts can still drift into business-coupled examples.
2. hardcoded paths/identity defaults can still leak into protocol surfaces.
3. recoverable blocked semantics are not fully consistent across all validators.

### 8.2 Objectives

#### O1 (mandatory)

Establish protocol purity:

1. no business-scene dependency in protocol contracts.
2. no machine-specific hardcoded path in protocol contracts.
3. no hidden default identity behavior in protocol-critical logic.

#### O2 (mandatory)

Establish semantic consistency:

1. recoverable blocked states are fail-operational.
2. hard boundary violations remain fail-closed.
3. plane-level status outputs are deterministic and machine-verifiable.

#### O3 (mandatory)

Establish skill-parity governance:

1. explicit mode selection.
2. explicit escape-hatch with audit evidence.
3. contract-first, mutation-after-validation.

### 8.3 In scope / out of scope

In scope:

1. protocol docs under `docs/governance/`.
2. protocol validators and scanners under `scripts/`.
3. CI required-gates integration.

Out of scope:

1. any real business file/data/task.
2. domain-level business acceptance criteria.
3. product UX/design workflows unrelated to protocol contracts.

### 8.4 Functional requirements

#### FR-001 Protocol doc purity gate

Implement `validate_protocol_doc_purity.py` (new):

1. block business-coupled keywords/patterns in protocol-governance docs.
2. block user-specific absolute paths as normative requirements.
3. allow placeholders (`${REPO_ROOT}`, `${IDENTITY_HOME}`, `${IDENTITY_CATALOG}`, `${IDENTITY_RUNTIME_OUTPUT_ROOT}`).

Failure code recommendation:

1. `IP-DOC-001` business-coupled content detected.
2. `IP-DOC-002` hardcoded path detected.

#### FR-002 No default identity hardcoding gate

Implement `validate_no_default_identity_hardcoding.py` (new):

1. detect hidden default identity selection in protocol-critical scripts.
2. require explicit `--identity-id` / `IDENTITY_IDS` for critical commands.
3. block cross-identity fallback in validation and learning paths.

Failure code recommendation:

1. `IP-ID-001` hidden default identity.
2. `IP-ID-002` cross-identity fallback detected.

#### FR-003 Recoverable-blocked semantics unification

Update upgrade/arbitration validators to align semantics:

1. if `capability_activation_status=BLOCKED` with explicit next action, treat as recoverable flow.
2. avoid forcing metrics-trigger equality against upgrade-required in capability-blocked branch.
3. keep `IP-PATH-*` / `IP-PERM-*` as hard boundary.

Failure code recommendation:

1. `IP-SEM-001` semantic mismatch between recoverable flow and validator outcome.

#### FR-004 Session canonical pointer consistency gate

Implement `validate_identity_session_pointer_consistency.py` (new):

1. canonical pointer must be catalog-scoped session pointer.
2. activation transaction fails/rolls back if canonical pointer sync fails.
3. legacy `/tmp` mirror may exist as best-effort compatibility output.

Failure code recommendation:

1. `IP-SES-001` catalog/session pointer mismatch.
2. `IP-SES-002` activation half-committed state detected.

#### FR-005 Dialogue Content Intelligence Contract (DCIC)

Add protocol-level DCIC with mandatory gates:

1. `dialogue_content_gate=required`
2. `dialogue_cross_validation_gate=required`
3. `dialogue_result_support_gate=required`

Required artifacts for each run:

1. `dialogue-content-synthesis-<run_id>.json`
   required fields: `user_objective`, `hard_constraints`, `soft_preferences`, `acceptance_criteria`, `ambiguities`, `resolved_decisions`.
2. `dialogue-cross-validation-matrix-<run_id>.json`
   required mapping: `UserTurnRef -> ExtractedConstraint -> PlanStepRef -> ArtifactRef -> FinalClaimRef`.
3. `dialogue-result-support-<run_id>.json`
   required evidence links: each `FinalClaimRef` must point to upstream `UserTurnRef` and `ArtifactRef`.

Required validators (new):

1. `validate_identity_dialogue_content.py`
2. `validate_identity_dialogue_cross_validation.py`
3. `validate_identity_dialogue_result_support.py`

Hard validation rules:

1. any hard constraint without `ArtifactRef` => fail.
2. any final claim without upstream `UserTurnRef` and `ArtifactRef` => fail.
3. dialogue changes without matrix rebuild => fail.
4. `unresolved ambiguity > 0` => cannot enter done state.

Failure code recommendation:

1. `IP-DCIC-001` dialogue synthesis missing required fields.
2. `IP-DCIC-002` cross-validation trace broken.
3. `IP-DCIC-003` result support evidence missing.
4. `IP-DCIC-004` unresolved ambiguity prevents done.

Core capability alignment requirements:

1. Accurate judgement: enforce dialogue semantic consistency before final claims.
2. Reasoning loop: each hypothesis/patch/result must bind `ConstraintRef`.
3. Auto-routing: route selection must derive from extracted constraints, not ad-hoc guess.
4. Rule learning: dialogue misread/success patterns must be written into rule learning artifacts.

Protocol KPI model (3+2, keep focus and self-drive space):

Top3 optimization metrics:

1. `dialogue_constraint_coverage_rate`
   definition: extracted constraints / required constraints.
   target: `>=95%` (hard constraints subset must be `100%`).
2. `dialogue_traceability_rate`
   definition: constraints with full trace chain (`UserTurnRef -> ExtractedConstraint -> PlanStepRef -> ArtifactRef -> FinalClaimRef`) / total constraints.
   target: `>=95%`.
3. `dialogue_change_reconciliation_rate`
   definition: changed constraints with rebuilt trace matrix / total changed constraints.
   target: phase-1 `>=90%`, phase-2 `>=95%`.

Redline metrics (hard gate):

1. `hard_constraint_missing_artifact_count`
   target: `=0`.
2. `untraceable_final_claim_count`
   target: `=0`.

Done-state blocker:

1. `unresolved_ambiguity_count` must be `0` before done state.

Metric governance rules:

1. KPI set size must stay <= 5 (do not expand without architecture review).
2. All metrics must be validator-calculated (no self-reported scores).
3. Denominator identities must be deduplicated by `ConstraintRef` / `FinalClaimRef`.
4. Redline metrics are enforce gates; Top3 metrics are trend-governed (not over-blocking).
5. rollout policy: `warn` for one stabilization window, then `enforce` for redlines.

#### FR-006 CI integration

Integrate FR-001~FR-005 into required-gates:

1. validators execute before release-plane closure checks.
2. any purity/semantic/session/dialogue violation blocks merge.

### 8.5 Non-functional requirements

#### NFR-001 Determinism

All validators must produce stable output given identical inputs.

#### NFR-002 Portability

No machine-specific path required for passing protocol gates.

#### NFR-003 Auditability

Every failure must include:

1. deterministic error code.
2. minimal remediation hint.
3. machine-checkable evidence location.

#### NFR-004 Backward compatibility

Legacy compatibility paths can exist but cannot be canonical truth.

### 8.6 Gate mapping

Required gate mapping proposal:

1. `protocol_doc_purity_gate=required` -> FR-001
2. `identity_hardcoding_gate=required` -> FR-002
3. `recoverable_semantic_gate=required` -> FR-003
4. `session_pointer_consistency_gate=required` -> FR-004
5. `dialogue_content_gate=required` -> FR-005
6. `dialogue_cross_validation_gate=required` -> FR-005
7. `dialogue_result_support_gate=required` -> FR-005

### 8.7 Acceptance criteria

AC-001:

1. protocol docs contain no business-coupled normative content.
2. protocol docs contain no user-specific absolute path as rule text.

AC-002:

1. hidden default identity and cross-identity fallback are blocked.

AC-003:

1. capability-blocked recoverable flow passes intended follow-up validators.
2. hard boundaries remain blocked.

AC-004:

1. activation leaves no catalog/session split state.
2. canonical session pointer always matches active catalog identity.

AC-005:

1. all new validators are wired into required-gates.
2. CI failure messages include stable error codes.

AC-006:

1. all three DCIC artifacts are generated for each required run.
2. each hard constraint is traceable to at least one concrete artifact reference.

AC-007:

1. unresolved ambiguities block done state.
2. dialogue change reconciliation is enforced by validator, not reviewer judgement.

AC-008:

1. Top3 metrics meet threshold policy (`>=95%`, `>=95%`, `>=90%/95%` by phase).
2. Redline metrics stay zero (`hard_constraint_missing_artifact_count=0`, `untraceable_final_claim_count=0`).

### 8.8 Delivery plan

P0:

1. FR-001 + FR-003 + FR-005 contract surfaces + required-gates wiring.

P1:

1. FR-002 + FR-004 + FR-005 validators + e2e/readiness integration.

P2:

1. trend metrics and governance dashboarding.

### 8.9 Risks and rollback

Primary risks:

1. false positive in doc purity regex/patterns.
2. over-strict semantic checks blocking valid recoverable flows.
3. compatibility impact for consumers reading legacy `/tmp` session pointer.

Rollback strategy:

1. validators support staged mode (`warn` -> `enforce`).
2. enable feature flags for first rollout window.
3. keep compatibility mirror output during migration period.

### 8.10 Definition of done

Done only when all are true:

1. FR-001~FR-006 implemented.
2. AC-001~AC-008 pass in CI.
3. no protocol document regression to business-coupled/hardcoded form.
4. release decision language remains three-plane consistent.
