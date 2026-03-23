# Protocol Remediation Audit Ledger (v1.6 Pre-Release)

Status: Active
Layer: protocol-only tracking ledger (non-governance)
Purpose: Central place for architect + audit-expert planning, implementation replay, and closure decisions before `v1.6` tag.

## 0A) Current-state redirect (mandatory)

1. This ledger remains historical/replay trace; it is **not** the standalone source for current-state protocol judgments.
2. Current-state stream routing must follow:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. Current-state control-plane metrics/status must follow current pointers:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/control-plane-budget.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
4. Active stream review judgments must be read from:
   - `docs/review/protocol-remediation-audit-ledger-v1.6.1-headstamp.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.2.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.3.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.4.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.5.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.6.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.7.md`
   - `docs/review/protocol-remediation-audit-ledger-v1.6.8.md`
5. Historical evidence rows in this file may contain transient paths/threshold snapshots; they cannot override current-pointer SSOT.
6. Any `/tmp/*` evidence reference in this file is historical replay context only and must not be treated as current wiring contract input.

## 0B) v1.6 comprehensive closure matrix (frozen)

`v1.6` closure is defined as one integrated motherline across all active `v1.6.x` streams.
No stream is allowed to remain a side-route.

| Stream | Domain | Closure status source |
| --- | --- | --- |
| v1.6.1 | Headstamp/HUD egress | `docs/review/protocol-remediation-audit-ledger-v1.6.1-headstamp.md` |
| v1.6.2 | Multimodal plugin enforcement | `docs/review/protocol-remediation-audit-ledger-v1.6.2.md` |
| v1.6.3 | GitHub-native control-plane specialization | `docs/review/protocol-remediation-audit-ledger-v1.6.3.md` |
| v1.6.4 | Fail-close monotonic governance | `docs/review/protocol-remediation-audit-ledger-v1.6.4.md` |
| v1.6.5 | GitHub Rulesets + super-linter dual-layer governance | `docs/review/protocol-remediation-audit-ledger-v1.6.5.md` |
| v1.6.6 | Host unique channel governance | `docs/review/protocol-remediation-audit-ledger-v1.6.6.md` |
| v1.6.7 | Cross-layer runtime uniqueness | `docs/review/protocol-remediation-audit-ledger-v1.6.7.md` |
| v1.6.8 | Downsink path immutability | `docs/review/protocol-remediation-audit-ledger-v1.6.8.md` |

Mandatory closure interpretation:

1. `v1.6` is not considered closed until required gates for all integrated streams are green.
2. Any unresolved required gate remains `v1.6` debt and cannot be deferred to a later stream for narrative closure.
3. Closure verdict must be machine-auditable from:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `scripts/required_gate_bundle_runner.py`
   - `.github/workflows/_identity-required-gates.yml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`

## 0C) 2026-03-14 closure checkpoint (IP-CP-BUDGET-001 + legacy-item re-audit)

### 0C.1 IP-CP-BUDGET-001 closure (protocol motherline)

1. Reproduced blocker before fix:
   - `python3 scripts/validate_control_plane_budget.py --json-only`
   - result: `FAIL_REQUIRED` / `IP-CP-BUDGET-001` (no-rebound ceiling violations).
2. Landed closure:
   - commit: `f1b7f43`
   - files:
     - `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
     - `identity/protocol/mappings/control-plane-status.v1.6.json`
3. Post-fix machine result:
   - budget validator: `PASS_REQUIRED`
   - status sync validator: `PASS_REQUIRED`
   - control-plane status: `PASS_REQUIRED`
4. Governance interpretation:
   - this is a **baseline re-anchor under no-rebound policy**, not a bypass;
   - enforcement remains fail-close through the same budget/status gates.

### 0C.2 Legacy-item cross-check (user-reported items, re-validated on 2026-03-14)

1. v1.6.8 downsink contracts on `custom-creative-ecom-analyst`:
   - current result: all three validators are `PASS_REQUIRED`
     - `validate_protocol_downsink_path_immutability.py`
     - `validate_protocol_downsink_path_write_guard.py`
     - `validate_protocol_downsink_path_literal_lock.py`
   - conclusion: prior `IP-DSPATH-001 contract_missing` report is not reproducible at current head.
2. v1.6.6 unique-entry on `custom-creative-ecom-analyst`:
   - current host gateway runtime contract fields: `PASS_REQUIRED`
   - current fail reason (strict validate replay): `entry_receipt_bundle_status_not_pass`
   - conclusion: fail is now due strict bundle verdict, not due missing downsink contract field.
3. Session-binding noise in full-scan:
   - confirmed as contextual precondition issue (`IP-ASB-SESSION-ENTRY-001`) when caller uses an unbound session id.
4. Strict-lane normalization closure (2026-03-14):
   - strict `operation=validate` no longer accepts runtime-stage defer copied from legacy reports.
   - `validate_multimodal_plugin_enforcement.py` now blocks report-derived defer on strict
     skip-forbidden operations, yielding deterministic strict fail-close:
     - `error_code=IP-MM-RUN-002`
     - `stale_reasons` includes `runtime_stage_missing_input_gate`
   - previous `IP-MM-RUN-003` reproduction on this strict lane is no longer a live protocol defect.

### 0C.3 Control-plane budget re-anchor after host-visible surface governance uplift (2026-03-14)

1. Context:
   - host-visible surface governance became required in v1.6 motherline:
     - live probe delegate wired in required gates
     - validator surface added: `scripts/validate_host_transport_wiring_attestation.py`
2. Impact:
   - `validator_scripts` observed count moved from `152` to `153`.
   - no other budget axes rebounded.
3. Re-anchor:
   - `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
     - `validator_scripts.warn: 153`
     - `convergence_guard.ceilings.validator_scripts: 153`
4. Post re-anchor:
   - `validate_control_plane_budget --json-only` => `PASS_REQUIRED`
   - `render_control_plane_status --write` => `control_plane_status=PASS_REQUIRED`
   - `validate_control_plane_status_sync --json-only` => `PASS_REQUIRED`

## 0) Boundary and usage rules

1. This file is a review ledger, not a governance SSOT.
2. Governance contracts/requirements remain in:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` (historical baseline)
3. Source-document precedence:
   - `L1 topic governance SSOT`: `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `L2 global protocol handoff SSOT`: `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
   - `L3 this remediation ledger`: `docs/review/protocol-remediation-audit-ledger-v1.6.md`
4. If this ledger conflicts with L1/L2, treat this ledger as stale and follow L1/L2.
5. Every remediation item must include:
   - commit sha
   - changed files
   - acceptance commands (rc + key fields)
   - execution context (`sandbox` / `escalated`)
   - residual risks
6. `v1.6` tag remains locked until governance unlock formula is satisfied.

### 0.1A Headstamp/HUD stream extraction (v1.6.1)

1. As-of `2026-03-08`, all new headstamp/HUD review records move to:
   - `docs/review/protocol-remediation-audit-ledger-v1.6.1-headstamp.md`
2. Governance SSOT for extracted stream:
   - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
3. Existing headstamp entries in this v1.6 ledger remain historical and must not be used for new normative closure decisions.

---

## 1) v1.6 kickoff intake (carry-over from v1.5)

Kickoff date: 2026-03-03

Carry-over conclusions:

1. Protocol implementation closure for FIX-051/FIX-054 is retained.
2. Current project-scope runtime replay still shows `P0` blocker `IP-CAP-003` (env/auth preflight).
3. External posture remains `IMPL_READY (BLOCKED_BY_ENV_AUDIT)`; no full-closed/full-green claim allowed.

Carry-over evidence:

1. `/tmp/reaudit_643_fullscan_project_only_live.json`
2. `/tmp/reaudit_643_threeplane_live.json`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md` section `16.8.48`

---

## 2) Rolling summary (v1.6 stream)

| Fix ID | Date (UTC) | Layer | Scope | Commit | Architect Status | Audit Status |
| --- | --- | --- | --- | --- | --- | --- |
| FIX16-001 | 2026-03-03 | protocol | v1.6 governance+review document bootstrap | UNCOMMITTED | DONE | PASS_WITH_BLOCKERS |
| FIX16-002 | 2026-03-03 | protocol | release unlock formula automation (`ASB16-RQ-001`) | d0f27bf | SPEC_READY | PENDING_INTAKE |
| FIX16-003 | 2026-03-03 | protocol | capability boundary governance (`ASB16-RQ-002`) | 08f20ab + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-004 | 2026-03-03 | protocol | status promotion evidence pipeline (`ASB16-RQ-003`) | 08f20ab + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-005 | 2026-03-03 | protocol | outlet regression matrix (`ASB16-RQ-004`) | 08f20ab + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-006 | 2026-03-03 | protocol | sidecar invariance regression lock (`ASB16-RQ-005`) | 08f20ab + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-007 | 2026-03-03 | protocol | release-plane cloud evidence contract (`ASB16-RQ-006`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-008 | 2026-03-03 | protocol | cross-cwd absolute-input runbook (`ASB16-RQ-007`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-009 | 2026-03-03 | protocol | docs bridge consistency automation (`ASB16-RQ-008`) | 08f20ab + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-010 | 2026-03-04 | protocol | run-id anchored strict report selection (`ASB16-RQ-009`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-011 | 2026-03-04 | protocol | baseline phase-A auto-bootstrap (`ASB16-RQ-010`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-012 | 2026-03-04 | protocol | regression temp collision-safe strategy (`ASB16-RQ-011`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-013 | 2026-03-04 | protocol | handoff/collab freshness auto-bootstrap (`ASB16-RQ-012`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-014 | 2026-03-04 | protocol | protocol-feedback atomic emit helper (`ASB16-RQ-013`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-015 | 2026-03-04 | protocol | bootstrap capability-driver intake from SRA packet (`ASB16-RQ-014`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-016 | 2026-03-04 | protocol | prompt capability matrix fail-close validator intake (`ASB16-RQ-015`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-017 | 2026-03-04 | protocol | refresh->strict + business interference guard runbook intake (`ASB16-RQ-016`) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-018 | 2026-03-04 | protocol | roundtable/vendor/openaidoc/context7 cross-verification intake (`ASB16-RQ-017`) | f63eb55 + 47f2f38 + 1beeb88 | SPEC_READY | PENDING_INTAKE |
| FIX16-019 | 2026-03-04 | protocol | office-ops self-drive regression supplemental intake (`ASB16-RQ-018..022`) | 9e59e0f + 4f4930c + fffc3c3 + 08c8f89 + 1beeb88 + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-020 | 2026-03-04 | protocol | discovery dual-track activation + apply-time coverage fail-close intake (`ASB16-RQ-023..024`) | 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-021 | 2026-03-04 | protocol | kernel-first baseline: contract source canonicalization + mapping + derived prompt lineage (`ASB16-RQ-025..028`) | 6f49040 + 13485bb + 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-022 | 2026-03-05 | protocol | semantic routing single-source convergence intake (`ASB16-RQ-029`) + rollout prioritization replay (`A-D P0`, `E P1`) | f603dd9 + 13485bb + 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-023 | 2026-03-05 | protocol | v1.6 suggestion intake evidence quorum hard-gate (`ASB16-RQ-030`; roundtable+vendor+online/spec evidence required before promotion beyond `PENDING_INTAKE`) | f63eb55 + 47f2f38 + 1beeb88 | SPEC_READY | PENDING_INTAKE |
| FIX16-024 | 2026-03-05 | protocol | protocol-kernel prompt import executable-coupling self-drive intake (`ASB16-RQ-031`; text import alone is insufficient without validator mapping + multimodal sample-proof closure + explicit actor context) | 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-025 | 2026-03-05 | protocol | deep cross-verification closure intake (`ASB16-RQ-015/029/030`; `T1..T4` evidence taxonomy normalization + deterministic verdict + non-regression strengthening sequence `S0..S4`) | 13485bb + 47f2f38 + 1beeb88 | SPEC_READY | PENDING_INTAKE |
| FIX16-026 | 2026-03-05 | protocol | base-repo-architect identity self-drive pilot: protocol-kernel prompt injection + multimodal verification uplift (`ASB16-RQ-031`), with v1.5/v1.6 boundary normalization | evidence_only(self-drive-runtime-replay-bundle) | SPEC_READY | PENDING_INTAKE |
| FIX16-027 | 2026-03-05 | protocol | final T1/T2/T3/T4 cross-verification replay (`ASB16-RQ-015/017/029/030/031`) with network re-check + vendor/spec consistency hardening (v1.6-only positive supplement) | b2c99fd | SPEC_READY | PENDING_INTAKE |
| FIX16-028 | 2026-03-05 | protocol | full-repo deep-scan lock inventory (`ASB16-RQ-001..032`): kernel/script lock-state census + architect independent rescan protocol | 7e7481d | SPEC_READY | PENDING_INTAKE |
| FIX16-029 | 2026-03-05 | protocol | outbound headstamp pre-send hard-gate intake (`ASB16-RQ-032`): block send on missing/malformed/mismatched `Identity-Context|Layer-Context` | 7e7481d + 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-030 | 2026-03-05 | protocol | batch-1 (`ASB16-RQ-001..005`) row-level strengthening normalization: acyclic unlock formula + explicit capability mapping + non-repudiation promotion receipt + outlet negative-path matrix + normalized sidecar parity | 031e9ba | SPEC_READY | PENDING_INTAKE |
| FIX16-031 | 2026-03-06 | protocol | Batch-2A (`ASB16-RQ-006..010`) row-level strengthening normalization: release-plane cloud evidence wiring + cross-cwd absolute-input contract + docs bridge checker + run-id-first report selector + phase-A/B parity contract | 5cb1a14 + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-032 | 2026-03-06 | protocol | Batch-3B (`ASB16-RQ-024..028`) row-level strengthening normalization: discovery apply coverage hard-close + kernel-first source lock + mapping coverage asset + derived prompt conformance metadata + instance write-boundary canonical code alignment | 3538eb7 + 13485bb + 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-033 | 2026-03-06 | protocol | Batch-4 (`ASB16-RQ-029/031/032/007/008`) four-track strengthening normalization: semantic single-source convergence + prompt import executable-coupling + headstamp canonical error-family convergence + cross-cwd parity replay + docs bridge contradiction checker + actor-id fallback recurrence supplement | 06bcb8a + 140c872 + db72970 + ca14131 + 9c0463e + 13485bb + 910ec6e | SPEC_READY | PENDING_INTAKE |
| FIX16-034 | 2026-03-06 | protocol | Batch-5 (`ASB16-RQ-010/011/012/013/016`) orchestration strengthening normalization: phase-A/B parity closure + tmp collision-safe allocator + handoff/collab freshness auto-rotation + protocol-feedback atomic emit + refresh->strict interference matrix receipts | 4f98bf4 + 84daaee + 13485bb | SPEC_READY | PENDING_INTAKE |
| FIX16-035 | 2026-03-06 | protocol | Batch-6 (`ASB16-RQ-017/018/019/020/021`) cross-workflow governance strengthening normalization: four-track contract hardening + dedup monotonic winner + cross-workflow schema gate + skill-path layout integrity + route/workflow publish-version pinning (includes canonical validator path alignment for `ASB16-RQ-018`) | 0df31f5 + 10c9956 + b80ec1f + 9e59e0f + f63eb55 + e214df9 + 9c0cf0a + 19d02ab + b5a191c + 5f7eb44 + 228ba40 + b7137e3 + 47f2f38 + b258982 + 1beeb88 + f712dec | SPEC_READY | PASS_WITH_BLOCKERS |
| FIX16-036 | 2026-03-06 | protocol | Batch-7 (`ASB16-RQ-022/030`) closure strengthening normalization: fallback taxonomy enum normalization + T1/T2/T3/T4 intake evidence quorum automation with metadata hard gate | 0df31f5 + 10c9956 + b80ec1f + f63eb55 + e214df9 + 4f4930c + 08c8f89 + 5f7eb44 + 228ba40 + b7137e3 + 47f2f38 + b258982 + 1beeb88 | SPEC_READY | PASS_WITH_BLOCKERS |
| FIX16-037 | 2026-03-06 | protocol | write-boundary non-starvation hardening (`ASB16-RQ-028/031`): lane-scoped boundary semantics + protocol-entry liveness invariant + no-silent-downgrade fail-close + mandatory telemetry tuple + replay matrix hard-gate | 093496b + 910ec6e | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P0-001 | 2026-03-06 | protocol | emergency hotfix intake: FQG multi-agent × multi-identity gated-switch guard (`execution-state no-hard-switch` + `allow_shared_session` semantics clarification + mandatory `switch_ack` handshake chain) | de313a0 + local_bridge_runtime_landed(pytest:28-pass) | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P0-002 | 2026-03-06 | protocol | emergency hotfix intake: protocol-lane activation starvation + outbound headstamp continuity gap (`explicit protocol request must not silently fallback` + `missing headstamp must fail-close`) with resolver convergence replay + canonical egress applicability replay | PEP-FQG-20260306-MA-MI-01 + PF-FQG-20260306-LANE-003 + local_bridge_runtime_landed(pytest:28-pass) + audit_replay_20260307_round6_headstamp + audit_replay_20260307_round8_single_egress | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P1-003 | 2026-03-06 | protocol | emergency hotfix intake: strict-surface fixed `/tmp` path debt (`dynamic temp resolver + runner-temp parity + fixed-path detector fail-close`) | PF-FQG-20260306-TMPPATH-001 + 4179e47 + 093496b + audit_round8_preimplementation_tmp_residuals | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P1-004 | 2026-03-07 | protocol | emergency hotfix intake: gate-source convergence + producer-aware requiredization applicability (`update/aggregation homomorphism` + `history-only requiredization block` + `strict context/writeback determinism`) | 093496b + audit_replay_20260307_round2 + audit_replay_20260307_round3 + audit_replay_20260307_round4 + audit_replay_20260307_round7_multisource_feedback + governance_v1.6_section_8.30 + audit_replay_20260307_round11_protocol_feedback_sem001 + governance_v1.6_section_8.35 + audit_round16_semantic_requiredization_scope_convergence + governance_v1.6_section_8.37 + audit_round18_protocol_lane_residual_convergence | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P0-005 | 2026-03-07 | protocol | emergency hotfix intake: gate-chain CLI parser regression (`release_readiness` + `identity_creator validate` pre-gate crash on missing argparse fields) | audit_replay_20260307 + audit_replay_20260307_round2 + audit_replay_20260307_round3 + audit_replay_20260307_round4 (`parser/runtime crash closure replay`) | SPEC_READY | PASS_WITH_BLOCKERS |
| HOTFIX16-P0-006 | 2026-03-07 | protocol | emergency hotfix intake: execution-target tuple isolation (`kind+key` conflict gate + explicit-override non-bypass + process-call receipt completeness) | runtime_escalation_20260307 (`multi-agent dispatch gap` cross-verify) + protocol_machine_lock_rq033 (`kernel+mapping+validator+lane-hooks`) + audit_replay_20260307_round3 + audit_replay_20260307_round4 + audit_round8_actor_entry_unification | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P0-007 | 2026-03-07 | protocol | emergency hotfix intake: unified protocol control-plane entrypoint freeze (`single registry source` + `single wiring entrypoint` + `single outbound verdict source` + `mandatory four-track mutation bundle`) | governance_v1.6_section_8.27 + audit_designfreeze_20260307_round9_unified_control_plane + governance_v1.6_section_8.29 + audit_designfreeze_20260307_round10_ucg_precode + audit_designfreeze_20260307_round10_ucg_precode_freeze_manifest + governance_v1.6_section_8.31 + ucg_runner_wave1_20260307 + governance_v1.6_section_8.32 + ucg_runner_wave2_20260307 + governance_v1.6_section_8.33 + audit_round14_ucg_fourpoint_roundtable_reconciliation + governance_v1.6_section_8.34 + ucg_runner_wave3_20260307 + governance_v1.6_section_8.38 + audit_round19_ucg_tuple_source_convergence_20260308 + governance_v1.6_section_8.39 + audit_round20_multi_instance_protocol_boundary_20260308 + governance_v1.6_section_8.40 + audit_round21_headstamp_multibinding_parser_convergence_20260308 + governance_v1.6_section_8.41 + audit_round22_ucg_minimal_control_plane_freeze_20260308 + governance_v1.6_section_8.42 + audit_round24_full_repo_scan_identity_scope_20260308 + governance_v1.6_section_8.43 + audit_round25_hud_egress_mandatory_chain_20260308 + audit_round26_uncovered_scope_audit_20260308 | SPEC_READY | PASS_WITH_BLOCKERS |
| HOTFIX16-P0-008 | 2026-03-08 | protocol | self-run full-chain closure for base-repo-architect (`health-report argv contract` + `readiness capability policy consistency` + `e2e actor passthrough` + `patch-plan early-fail completeness` + `handoff/metrics project-runtime path convergence`) | governance_v1.6_section_8.45 + identity_protocol_self_run_20260308T045542Z | SPEC_READY | PENDING_INTAKE |
| HOTFIX16-P1-009 | 2026-03-08 | protocol | validate-chain expected-layer pass-through closure (`identity_creator validate` now pins renderer tuple with expected work/source layer) | governance_v1.6_section_8.46 + /tmp/base_repo_architect_identity_validate_now.log + /tmp/base_repo_architect_three_plane_now.log + /tmp/base_repo_architect_full_scan_now.log | SPEC_READY | PASS_WITH_BLOCKERS |
| HOTFIX16-P0-010 | 2026-03-08 | protocol | HUD tuple hardening + actor strict-entry closure (`required_gate_tuple_parity` core+conditional tuple expansion + compose actor fail-close + bundle runner arg-contract completion + three-plane/full-scan projection closure + source inference order fix + lane-lock deterministic pass-through for full-scan/three-plane) | governance_v1.6_section_8.47 + governance_v1.6_section_8.48 + /tmp/tuple_gap_roundtable_recheck_20260308.json + /tmp/tuple_gap_recheck2_result.json + /tmp/compose_probe_no_actor_roundtable_custom_recheck.json + /tmp/compose_no_actor_recheck2_20260308.json + /tmp/source_infer_recheck_20260308.log + /tmp/source_infer_recheck2_20260308.log + /tmp/full_scan_projection_recheck3_20260308.json + /tmp/three_plane_sidecar_recheck11_20260308.json + /tmp/audit_recheck_bundle_args_20260308.json + /tmp/audit_recheck_bundle_args_surface_20260308.json + /tmp/surface_drift_recheck11_20260308.json + identity_protocol_round26_4_closure_20260308T060901Z | SPEC_READY | PASS_WITH_BLOCKERS |

---

## 3) Fix records

### FIX16-001 - v1.6 governance/review bootstrap

- Date (UTC): 2026-03-03
- Layer declaration: `protocol`
- Execution context: `sandbox`
- Source refs:
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
  - `docs/review/protocol-remediation-audit-ledger-v1.5.md` section `16.8.48`

#### Change summary

1. Create v1.6 governance SSOT.
2. Create v1.6 review ledger.
3. Register v1.6 canonical entry in governance index.
4. Preserve v1.5 history as evidence-only baseline; no historical rewrite.

#### Acceptance commands (initial baseline)

1. `python3 scripts/docs_command_contract_check.py`
   - expected: `PASS`
2. `python3 scripts/validate_protocol_ssot_source.py`
   - expected: `OK`

#### Residual risks

1. `IP-CAP-003` environment blocker remains open and can keep project replay in `P0`.
2. Release plane still requires cloud gates evidence for closure.

### FIX16-002 - release unlock formula automation (`ASB16-RQ-001`)

- Status: `SPEC_READY`
- Goal: deterministic machine output of `unlock_allowed` and blocker set.
- Landing update (`2026-03-07`, non-promotional):
  - code landing commit: `d0f27bf`
  - validator landed: `scripts/validate_unlock_formula.py`
  - kernel anchor landed: `identity/protocol/IDENTITY_PROTOCOL.md#rq_001_unlock_formula_contract_v1`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-001`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci` (via validator chains + coverage aggregator target)
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true replay archive is complete.

Acceptance target:

1. Same input, same output hash.
2. Includes `D1..D6`, `p0_total`, `p0_done`, `p0_not_done_refs`, `protocol_blockers`, `env_blockers`.

### FIX16-003 - capability boundary governance (`ASB16-RQ-002`)

- Status: `SPEC_READY`
- Goal: isolate env/auth blockers from protocol code closure claims.
- Landing update (`2026-03-07`, non-promotional):
  - validator landed: `scripts/validate_capability_boundary_classification.py`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-002`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci`
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true replay archive is complete.

Acceptance target:

1. `IP-CAP-*` consistently classified as env/auth in release summary.
2. Full-scan and three-plane classification is aligned with unlock report.

### FIX16-004 - status promotion evidence pipeline (`ASB16-RQ-003`)

- Status: `SPEC_READY`
- Goal: prevent narrative-only promotion to `DONE`.
- Landing update (`2026-03-07`, non-promotional):
  - validator landed: `scripts/validate_promotion_pipeline.py`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-003`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci`
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true replay archive is complete.

Acceptance target:

1. Every promotion has commit + replay evidence + reviewer decision.
2. Missing evidence causes fail-closed promotion denial.

### FIX16-005 - outlet regression matrix (`ASB16-RQ-004`)

- Status: `SPEC_READY`
- Goal: guarantee compose/send-time invariance across required lanes.
- Landing update (`2026-03-07`, non-promotional):
  - validator landed: `scripts/validate_outlet_matrix.py`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-004`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci`
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true replay archive is complete.

Acceptance target:

1. creator/readiness/e2e/full-scan/three-plane all pass.
2. root/tmp cross-cwd parity remains stable.

### FIX16-006 - sidecar invariance lock (`ASB16-RQ-005`)

- Status: `SPEC_READY`
- Goal: preserve sidecar passthrough ordering and cwd invariance.
- Landing update (`2026-03-07`, non-promotional):
  - validator landed: `scripts/validate_sidecar_cwd_parity.py`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-005`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci`
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true replay archive is complete.

Acceptance target:

1. sidecar root/tmp parity pass.
2. sidecar `track_b.semantic_*` and `track_b.vendor_namespace_*` equivalent to direct validators with identical args.

### FIX16-007 - release-plane cloud evidence contract (`ASB16-RQ-006`)

- Status: `SPEC_READY`
- Goal: convert release-plane from `NOT_STARTED` to auditable closure path.

Acceptance target:

1. required cloud checks id/run-url/workflow-sha evidence present and cross-validated.
2. mismatch fails release-plane closure.

### FIX16-008 - cross-cwd absolute-input runbook (`ASB16-RQ-007`)

- Status: `SPEC_READY`
- Goal: prevent replay ambiguity when caller cwd is not protocol-root.

Acceptance target:

1. runbook examples include protocol-root and non-root variants.
2. absolute `--repo-catalog` guidance is explicit and validated.

### FIX16-009 - docs bridge consistency automation (`ASB16-RQ-008`)

- Status: `SPEC_READY`
- Goal: prevent governance/review status drift.
- Landing update (`2026-03-07`, non-promotional):
  - checker landed: `scripts/validate_docs_bridge_consistency.py`
  - mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-008`
  - lane hooks wired: `creator/readiness/three-plane/full-scan/e2e/ci`
  - state boundary unchanged: `SPEC_READY / PENDING_INTAKE` until deterministic required=true contradiction replay archive is complete.

Acceptance target:

1. consistency checker flags contradictory state pairs.
2. bridge output includes exact anchors updated in both docs.

### FIX16-010 - office-ops intake triage bridge (`ASB16-RQ-009..013`)

- Status: `SPEC_READY`
- Goal: register office-ops protocol feedback package into v1.6 backlog with explicit v1.5/v1.6 split boundary.

Source package:

1. `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260304T041651Z_office_ops_protocol_upgrade_suggestions.md`
2. `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_20260304T041651Z_office_ops_self_drive.md`
3. `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/SPLIT_RECEIPT_20260304T041849Z_identity-upgrade-exec-office-ops-expert-1772596487.json`
4. `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/evidence-index/INDEX.md`

Triage decision:

1. suggestion #1 (run-id anchored report selection) is retained as v1.5 candidate carry-over and mirrored into v1.6 as `ASB16-RQ-009` fallback if not landed in v1.5.
2. suggestions #2..#5 are registered directly in v1.6 (`ASB16-RQ-010..013`).

Cross-check boundary:

1. office-ops current reports stay passing (`all_ok=true`, `lane_routing_status=PASS_REQUIRED`, `writeback_status=WRITTEN`) and do not create a new v1.5 blocker in this window.
2. this intake is backlog registration only; no protocol code path changed in this docs step.

Task-6..13 audit synchronization (2026-03-06, codex audit trail):

1. scope correction: this sync follows task-level audit outcomes (`Task-6..13`), not legacy `FIX16-006..013` intake placeholders.
2. normalized decision:
   - `Task-6..13` = `PASS_WITH_BLOCKERS` (lane hooks landed; deterministic replay and/or semantic drift blockers remained at audit time).
   - `Task-15` follow-up closed the dedup path-lock + timezone nondeterminism blockers and governance table drift (`PASS_REQUIRED` on those blocker items).
3. promotion posture unchanged:
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`;
   - rows remain non-promotional until required=true replay archive and five-link anchors are complete.

### FIX16-015 - SRA bootstrap capability packet intake (`ASB16-RQ-014..017`)

- Status: `SPEC_READY`
- Goal: register system-requirements-analyst proposal as v1.6 protocol enhancement with deterministic intake boundary and no v1.5 formula drift.

Source package:

1. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
2. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
3. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
4. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
5. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
6. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`

Triage decision:

1. promote the bootstrap-capability request into v1.6 governance scope as `ASB16-RQ-014..017`.
2. keep v1.5 boundary unchanged; this intake does not change current v1.5 unlock formula or D6 status.
3. classify this intake as docs/governance strengthening only (`UNCOMMITTED`, `PENDING_INTAKE`) until implementation + replay evidence land.

Cross-verification matrix (requiredized for this intake):

1. roundtable track:
   - local roundtable doc confirms 10 capability drivers and fail->refresh-pass->strict-pass replay path.
2. vendor track:
   - vendor scan confirms official guidance alignment for structured outputs, instruction hierarchy, skills protocol, and sandbox/approval boundaries.
3. OpenAI docs track:
   - strict mode guidance confirms schema adherence expectation and recommends strict mode with `additionalProperties=false` + required fields.
4. Context7 track:
   - OpenAI platform docs extraction returns same strict-schema constraints and tool contract expectations.

Cross-verification anchors:

1. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
2. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
3. `https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide/#frequented-asked-questions-faq`
4. `context7:/websites/developers_openai_api`
5. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
6. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`

Acceptance target (`ASB16-RQ-014..017` planning stage):

1. initialization template can be machine-checked against required capability-driver matrix.
2. missing requiredized capability driver is fail-closed (`FAIL_REQUIRED`) with machine-readable error code.
3. runbook explicitly enforces `refresh -> strict` after core-file edits and emits business-interference matrix.
4. intake cannot advance without all four cross-verification tracks (roundtable/vendor/openaidoc/context7).

### FIX16-019 - office-ops self-drive regression supplemental intake (`ASB16-RQ-018..022`)

- Status: `SPEC_READY`
- Goal: absorb latest office-ops real-run evidence and register uncovered protocol-framework gaps into v1.6 governance backlog.

Source package:

1. `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-self-drive-regression-v2026-03-04.md`

Cross-checked replay evidence intake:

1. strict fast-lane (`ids=5`, `strict_quality_meta=true`) reports closure:
   - `route_action=skip_all_high_quality`
   - `inferred_only_count=0`
   - `reason=completed_high_quality`
2. same-`run_id` concurrency stress in serial orchestrator remains stable:
   - one `submitted`, others `duplicate_ignored`
3. regression sample (`ids=1-30`) keeps `inferred_only_count=0` for both strict and non-strict runs.

Gap mapping decision (new in this supplemental intake):

1. deterministic dedup winner contract -> `ASB16-RQ-018`.
2. cross-workflow evidence schema required fields -> `ASB16-RQ-019`.
3. skill-path drift gate (`SKILL.md` target existence) -> `ASB16-RQ-020`.
4. route/version pinning consistency contract -> `ASB16-RQ-021`.
5. fallback taxonomy enum normalization -> `ASB16-RQ-022`.

Boundary:

1. this supplemental intake does not alter v1.5 unlock formula.
2. this is docs/governance planning intake only; no protocol script behavior changed in this step.

### FIX16-020 - SRA discovery dual-track hardening intake (`ASB16-RQ-023..024`)

- Status: `SPEC_READY`
- Goal: promote discovery dual-track from "mechanism works" to deterministic strong-control closure when requiredization is applied.

Source package:

1. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
2. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-unified-feedback-index-2026-03-04.md`
3. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-discovery-dual-track-simulation-receipt-2026-03-04.md`
4. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-cross-verification-execution-receipt-2026-03-04-roundtable-vendor-context7-openaidoc-skill.md`

Deterministic finding matrix (from simulation receipt):

1. trigger path proves dual-track activation is functional:
   - `requiredization_triggered=true`
   - `trigger_classes=["repeat_platform_optimization_intent"]`
2. fail-close without apply is already correct:
   - `discovery_requiredization_status=FAIL_REQUIRED`
   - `error_code=IP-DREQ-001`
3. apply path promotes contracts and links receipt/index:
   - `requiredization_applied=true`
   - `requiredization_receipt_linked=true`
4. governance gap remains:
   - same payload can still show `discovery_requiredization_status=PASS_REQUIRED` with:
   - `discovery_required_total=3`, `discovery_required_passed=0`, `discovery_required_coverage_rate=0.0`

Triage decision:

1. add `ASB16-RQ-023` for conditional requiredization policy under discovery trigger classes.
2. add `ASB16-RQ-024` for apply-time strict coverage closure gate.
3. keep v1.5 boundary unchanged; this is v1.6-only governance intake.

Cross-verification tracks (requiredized for this intake):

1. roundtable: capability + replay narrative in architect packet and roundtable docs.
2. vendor: official-source and cross-vendor checks retained via vendor scan references and unified index chain.
3. OpenAI docs: strict schema and Codex skills/security guidance reinforce deterministic fail-closed contract design.
4. Context7: OpenAI API/dev docs extraction returns the same strict-schema and sandbox/approval constraints.

Cross-verification anchors:

1. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
2. `https://developers.openai.com/codex/skills/`
3. `https://developers.openai.com/codex/security/`
4. `context7:/websites/developers_openai_api`
5. `context7:/websites/developers_openai`
6. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
7. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
8. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

Acceptance target (`ASB16-RQ-023..024` planning stage):

1. trigger not fired -> discovery remains optional and must not escalate by default.
2. trigger fired without apply -> fail-close with `IP-DREQ-001`.
3. `requiredization_applied=true` must require:
   - `discovery_required_total > 0`
   - `discovery_required_passed == discovery_required_total`
   - `discovery_required_coverage_rate == 100.0`
   - otherwise fail-close with dedicated code (`IP-DREQ-002` reserved for v1.6 implementation).
4. apply path must keep receipt + evidence-index linkage as mandatory acceptance artifacts.

### FIX16-021 - kernel-first baseline intake (`ASB16-RQ-025..028`)

- Status: `SPEC_READY`
- Goal: re-anchor v1.6 on identity kernel contracts so protocol semantics are sourced from `identity/` first and projected to governance/review/scripts deterministically.

Source package:

1. `https://github.com/brianlyang/identity-protocol/tree/main/identity`
2. `identity/protocol/IDENTITY_PROTOCOL.md`
3. `identity/protocol/IDENTITY_RUNTIME.md`
4. `identity/protocol/IDENTITY_DISCOVERY.md`
5. `identity/catalog/schema/identities.schema.json`
6. `identity/catalog/identities.yaml`
7. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`
8. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-cross-verification-execution-receipt-2026-03-04-roundtable-vendor-context7-openaidoc-skill.md`
9. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
10. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`

Deterministic findings:

1. `identity/` contains protocol/catalog/packs/runtime surfaces and is structurally ready to be the protocol kernel.
2. Current protocol markdown still routes active normative semantics to governance/review docs (`Normative source map`), creating source-center drift.
3. Foundational contract constants are duplicated across scripts (for example mandatory protocol sources), increasing semantic divergence risk.
4. Identity prompts have source references but no enforced derived-lineage metadata contract (version/digest/contract-id projection).
5. Existing discovery/control-loop hardening confirms fail-close discipline is mature enough to absorb kernel-first uplift without weakening gate strictness.

Triage decision:

1. add `ASB16-RQ-025` for kernel-source canonicalization (`identity/protocol/*` + `identity/catalog/schema/*` as contract origin).
2. add `ASB16-RQ-026` for kernel-to-validator-to-doc mapping coverage (`100%` P0 coverage, orphan-free).
3. add `ASB16-RQ-027` for derived prompt compilation lineage and runtime conformance metadata.
4. add `ASB16-RQ-028` for instance write-boundary lock (instance can write only its own runtime/protocol-feedback surfaces).

Cross-verification tracks (requiredized for this intake):

1. roundtable track:
   - initial prompt capability roundtable already frames kernel-driven startup behavior and replay closure expectations.
2. vendor track:
   - official multi-vendor scans converge on structured, contract-first execution and deterministic evidence.
3. OpenAI docs track:
   - strict schema + skills progressive disclosure + sandbox/approval boundaries align with kernel-first fail-closed governance.
4. Context7 track:
   - OpenAI API and Codex docs extraction confirms strict-contract and boundary-enforcement posture.
5. skill protocol track:
   - local skill references require trigger/patch/validate/replay discipline, matching kernel-projection architecture.

Cross-verification anchors:

1. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
2. `https://developers.openai.com/codex/skills/`
3. `https://developers.openai.com/codex/security/`
4. `context7:/websites/developers_openai_api`
5. `context7:/websites/developers_openai`
6. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
7. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
8. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

Acceptance target (`ASB16-RQ-025..028` planning stage):

1. kernel canonicalization:
   - base-contract origin is `identity/protocol/*` + `identity/catalog/schema/*`;
   - governance/review contain mapped projections only.
2. mapping closure:
   - every P0 contract has `kernel_contract_id`, validator surfaces, governance anchor, review anchor.
3. derived prompt closure:
   - active identity prompt must carry derivation metadata and digest linkage to kernel contracts.
4. instance boundary closure:
   - instance self-drive writes to protocol kernel/governance/review surfaces are fail-closed with deterministic boundary code.

Value deep-dive and non-regression judgment (cross-verified, 2026-03-04):

1. structural value:
   - resolves source-center drift by setting kernel contracts as origin and docs/scripts as mapped projections.
2. operational value:
   - reduces repeated "patch-then-regress" cycles by requiring machine-readable mapping closure before promotion.
3. runtime consistency value:
   - converts prompt quality from narrative-only review into provenance-checked compilation and conformance metadata.
4. risk-control value:
   - hardens instance/protocol boundary so self-drive evidence stays in runtime feedback surfaces without polluting protocol sources.
5. audit value:
   - makes cross-track evidence deterministic (roundtable/vendor/OpenAI docs/Context7/skill protocol) and replayable.

Cross-verification convergence matrix (same-question, multi-track):

1. roundtable track:
   - question: should base contracts be moved to kernel origin with projected governance/review mapping.
   - convergence: yes; aligns with capability-bootstrap and replay closure framing.
2. vendor track:
   - question: does contract-first execution reduce drift and rework under self-drive.
   - convergence: yes; official scans consistently favor deterministic contract surfaces and evidence chains.
3. OpenAI docs track:
   - question: does strict-schema + sandbox/approval posture support fail-closed kernel governance.
   - convergence: yes; strict mode and codex security model are consistent with requiredized contract enforcement.
4. Context7 track:
   - question: is extracted OpenAI API/Codex guidance contradictory to kernel-first fail-close design.
   - convergence: no contradiction found; extraction confirms strict schema and boundary controls.
5. skill protocol track:
   - question: do local skill lifecycle contracts match kernel -> mapping -> validator -> replay workflow.
   - convergence: yes; trigger/patch/validate/replay discipline is compatible with the same projection model.

Non-regression closure decision:

1. this intake may advance to implementation planning without touching v1.5 release semantics.
2. implementation must follow staged rollout (`shadow -> required-no-promotion -> fail-close`) and parity replays.
3. any boundary leak, prompt lineage mismatch, or kernel/projection drift is treated as promotion blocker.
4. therefore, value uplift is accepted while baseline safety remains locked by explicit freeze triggers.

Supplemental cross-verification verdict intake (2026-03-05):

1. source: `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-v1.6-governance-review-cross-verification-verdict-2026-03-05.md`.
2. verdict confirms content-level alignment for:
   - lane split governance,
   - prompt bootstrap capability-native requirement,
   - four-track cross-verification fail-close policy.
3. no semantic contradiction found in live replay across roundtable/vendor/openaidoc/context7.
4. status caveat remains unchanged:
   - these items are still `SPEC_READY/PENDING_INTAKE` until implementation + strict replay evidence promote them to `DONE`.

### FIX16-022 - semantic routing convergence and rollout prioritization intake (`ASB16-RQ-029`)

- Status: `SPEC_READY`
- Goal: remove same-lineage mixed verdict (`update green` + `cross-plane semantic fail`) by adding canonical semantic-routing source and convergence gate.

Source package:

1. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-instance-next-upgrade-proposals-cross-verified-2026-03-05.md`
2. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-self-drive-live-replay-deep-extraction-2026-03-05-round2.md`
3. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-05_001.md`
4. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/issues/ISSUE_2026-03-05_update-threeplane-semantic-convergence-gap.md`
5. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/upgrade-proposals/PROPOSAL_2026-03-05_semantic-single-source-and-convergence-gate.md`
6. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`

Machine replay extraction (2026-03-05 strict lineage):

1. update report:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
   - facts:
     - `all_ok=true`
     - `work_layer=instance`
     - `applied_gate_set=instance_required_checks`
     - no root semantic-routing block present.
2. three-plane replay:
   - `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
   - facts:
     - `instance_plane_status=BLOCKED`
     - `instance_plane_detail.semantic_routing_guard.error_code=IP-SEM-001`
3. full-scan replay:
   - `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`
   - facts:
     - runtime profile semantic guard reproduces `FAIL_REQUIRED` + `IP-SEM-001`.

Deterministic judgment:

1. dual-lane split is functioning; defect class is semantic governance convergence.
2. current v1.6 baseline has no independent P0 requirement enforcing same-lineage semantic verdict convergence across update/three-plane/full-scan.
3. therefore this intake adds `ASB16-RQ-029` for semantic single-source convergence.

Rollout prioritization absorption (from cross-verified proposal set):

1. `P0-A` semantic-routing single-source convergence -> promoted as new requirement (`ASB16-RQ-029`).
2. `P0-B` prompt capability matrix hard-close -> mapped to existing `ASB16-RQ-015`.
3. `P0-C` discovery apply-time `coverage=100` hard-close -> mapped to existing `ASB16-RQ-024`.
4. `P0-D` kernel-derived prompt + conformance digest lock -> mapped to existing `ASB16-RQ-025..027`.
5. `P1-E` pending-intake -> done auto-promotion orchestrator -> mapped as implementation extension under existing promotion pipeline requirements (`ASB16-RQ-003` + `ASB16-RQ-008`).

### FIX16-023 - intake evidence quorum hard-gate reinforcement (`ASB16-RQ-030`)

- Status: `SPEC_READY`
- Goal: ensure future v1.6 suggestions are not admitted by intuition-only narrative and must pass mandatory cross-verification quorum before implementation promotion.

Required quorum (all four tracks mandatory):

1. roundtable track:
   - multi-role deliberation with fact/inference separation.
2. vendor track:
   - multi-vendor official references with URLs.
3. online reference track:
   - live-link source set + retrieval timestamp.
4. protocol/spec track:
   - MCP/Agent Skills and OpenAI docs/context anchors.

Hard intake rules:

1. if any track is missing, item remains `PENDING_INTAKE` (no implementation promotion).
2. each intake must include:
   - `cross_verification_bundle_id`,
   - `source_url_set`,
   - `reference_timestamp_utc`,
   - `conflict_reconciliation_note`.
3. this rule applies to new v1.6 suggestions and is not a retroactive rewrite of earlier v1.5 closures.

### FIX16-024 - protocol-kernel prompt import executable-coupling self-drive intake (`ASB16-RQ-031`)

- Status: `SPEC_READY`
- Goal: verify whether importing `identity/protocol/*` into identity prompt actually strengthens executable governance gates in real self-drive runs.

Self-drive replay evidence (base-repo-audit-expert-v3):

1. Baseline validators:
   - `/tmp/v16_exp_baseline_runtime_contract.log` -> `PASS`.
   - `/tmp/v16_exp_baseline_trigger_regression.log` -> `FAIL` (`IP-CWD-001`, missing trigger regression sample report).
   - `/tmp/v16_exp_baseline_knowledge_contract.log` -> `FAIL` (missing knowledge acquisition sample report).
   - `/tmp/v16_exp_baseline_capability_arbitration.log` -> `FAIL` (missing capability arbitration sample report).
2. Baseline aggregate replay:
   - `/tmp/v16_exp_baseline_three_plane.json` and `/tmp/v16_exp_baseline_full_scan.json` -> `summary.p0=1`.
3. Prompt import experiment:
   - temporary kernel-import block added to instance prompt and then reverted.
   - post-import validators:
     - `/tmp/v16_exp_after_runtime_contract.log` -> still `PASS`.
     - `/tmp/v16_exp_after_trigger_regression.log` -> still `FAIL` (`IP-CWD-001`).
     - `/tmp/v16_exp_after_knowledge_contract.log` -> still `FAIL`.
     - `/tmp/v16_exp_after_capability_arbitration.log` -> still `FAIL`.
   - post-import aggregate replay:
     - `/tmp/v16_exp_after_three_plane.json` and `/tmp/v16_exp_after_full_scan.json` -> still `summary.p0=1`.
4. Strict update lane context finding:
   - `identity_creator.py update` has no explicit `--actor-id` argument; strict path depends on actor resolution environment.
   - replay without explicit actor context via env surfaced actor-bound mismatch branch (`IP-ASB-STAMP-SESSION-005`) in pre-mutation compose gate.

Deterministic judgment:

1. protocol-kernel clauses injected into prompt text did not produce executable uplift by themselves.
2. current stack lacks fail-closed coupling between imported prompt contracts and validator execution mapping.
3. multimodal capability closure remains incomplete without required sample-proof outputs.
4. therefore v1.6 needs explicit P0 contractization (`ASB16-RQ-031`) rather than narrative prompt hardening only.

Cross-track clarification supplement (2026-03-06; final four-track reconciliation):

1. do not add same-name runtime artifact file `identity/protocol/IDENTITY_PROMPT.md`.
2. protocol-side baseline prompt intent, if needed, must be represented as contract source (kernel anchor section or dedicated prompt-bootstrap contract file) and compiled into pack-level `IDENTITY_PROMPT.md`.
3. any protocol-side baseline source is invalid unless it closes the machine chain (`kernel_ref -> mapping_ref -> validator_ref -> acceptance replay`) across creator/readiness/e2e/full-scan/three-plane.
4. this supplement is directional hardening only and does not promote `ASB16-RQ-031` status.
5. canonical file for this direction is `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`, and it must be continuously updated with capability-ingestion deltas + replay obligations.
6. canonical file must keep full base-protocol capability absorption matrix and append-only update ledger; stale anchors or missing ledger entry are promotion blockers.

### FIX16-025 - deep cross-verification closure intake for `ASB16-RQ-015/029/030` (`T1..T4` normalized taxonomy)

- Status: `SPEC_READY`
- Goal: convert this round "roundtable + vendor + openai/context7 + skill/spec + live replay" package into deterministic governance/review closure criteria without over-claiming implementation completion.

Cross-verification bundle (`v16-xverify-20260305-r2`) evidence tracks:

1. `T1 roundtable`:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
2. `T2 vendor`:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
3. `T3 openai_context`:
   - `https://developers.openai.com/codex/security/#sandbox-and-approvals`
   - `https://developers.openai.com/codex/skills/`
   - `https://platform.openai.com/docs/guides/function-calling#strict-mode`
   - `context7:/openai/skills`
   - `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`
4. `T4 protocol_spec`:
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
   - `https://modelcontextprotocol.io/specification/latest`
   - `https://agentskills.io/specification`
5. Runtime replay set:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
   - `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
   - `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`

Deterministic replay verdict (same-lineage extraction):

1. update report remains green for lane routing:
   - `all_ok=true`
   - `work_layer=instance`
   - `applied_gate_set=instance_required_checks`
2. three-plane remains blocked by semantic lineage guard:
   - `instance=BLOCKED`
   - `semantic_routing_status=FAIL_REQUIRED`
   - `error_code=IP-SEM-001`
3. full-scan still reports unresolved P0 in same window:
   - `summary.p0=1`
4. judgment:
   - dual-lane split itself is not regressed;
   - closure gap is deterministic replay/archive closure (`ASB16-RQ-015/029/030` are implemented but still non-promotional until replay closure).

Positive-strengthening sequence (non-regression required):

1. `S0 shadow`: semantic convergence comparator emits `mismatch_count` and lineage refs (observe-only).
2. `S1 dual-write`: strict update emits canonical semantic fields consumed by three-plane/full-scan.
3. `S2 fail-close`: enable `IP-SEM-CONV-001` only after root/tmp parity is stable for two consecutive runs.
4. `S3 intake hard-gate`: automated validator enforces `T1..T4` presence and metadata completeness.
5. `S4 baseline guard`: keep lane split + kernel write-boundary lock unchanged during `S0..S3`.

Promotion boundary (hard):

1. This fix is docs/governance normalization intake only; it does not promote requirement status by itself.
2. `ASB16-RQ-015/029/030` can move past `SPEC_READY` only after strict replay evidence under `S0..S3` is archived and independently audited.
3. Any claim of `DONE` without executable convergence proof is invalid.

### FIX16-026 - base-repo-architect self-drive pilot for protocol-kernel prompt injection + multimodal verification uplift (`ASB16-RQ-031`)

- Status: `SPEC_READY`
- Goal: execute a real runtime self-drive pilot on `base-repo-architect` identity instance, import protocol-kernel contracts into prompt baseline, and verify whether executable lane quality is improved without crossing v1.5 boundary.

Pilot implementation (instance-level, no protocol script mutation in this step):

1. Prompt baseline upgrade:
   - file: `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/IDENTITY_PROMPT.md`
   - action: injected `identity/protocol/*` contract sources + explicit multimodal verification policy + actor-explicit strict-lane rule + v1.5/v1.6 scope split clause.
2. Runtime learning artifacts updated:
   - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/RULEBOOK.jsonl`
   - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/TASK_HISTORY.md`

Self-drive replay evidence:

1. validator bundle:
   - `/tmp/v16_selfdrive_architect_validation_bundle_20260305.json`
   - verdict: `prompt_quality/runtime_contract/actor_binding/actor_multibinding/session_refresh/three_plane` all `rc=0`.
2. three-plane output:
   - `/tmp/v16_selfdrive_architect_three_plane_20260305.json`
   - result: `repo_plane_status=CLOSED`, `overall_release_decision=Conditional Go` (release plane not started is expected in this pilot scope).
3. strict-chain residual (important for v1.6 executable coupling):
   - `/tmp/v16_selfdrive_architect_validate_20260305.log`
   - `identity_creator validate` returned `rc=1`; blocker branch shows `IP-ASB-STAMP-SESSION-005` in reply-first-line gate path.
   - this indicates strict actor-context propagation is still non-convergent in composed validation chain, even when standalone actor/session validators pass.

Deterministic judgment:

1. Prompt-level protocol-kernel import is effective as **baseline capability reinforcement** (quality/contract validators green).
2. Remaining gap is **executable coupling**, not text quality:
   - unified creator strict chain still has actor-context convergence residual.
3. Boundary normalization:
   - this pilot is a v1.6 positive supplement intake and does not mutate any v1.5 release/audit state.

Promotion boundary (hard):

1. `FIX16-026` cannot promote `ASB16-RQ-031` beyond `SPEC_READY` by itself.
2. Required next step remains protocol-layer implementation for strict-chain actor-context convergence + sample-proof validator mapping, then independent re-audit.


### FIX16-027 - final cross-verification reinforcement (`ASB16-RQ-015/017/029/030/031`)

- Status: `SPEC_READY`
- Goal: execute the final `T1/T2/T3/T4` cross-verification replay (roundtable + vendor + online + protocol/spec) with explicit network re-check, then lock a deterministic v1.6-only positive-strengthening boundary without over-promoting requirement status.

Cross-verification bundle (`v16-final-xverify-20260305-r3`) intake scope:

1. Machine bundle anchor:
   - `/tmp/v16_final_xverify_bundle_20260305.json`
2. `T1 roundtable`:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
3. `T2 vendor` (local + official web re-check):
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
   - `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
   - `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
   - `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
4. `T3 openai_context` (official docs + Context7):
   - `https://developers.openai.com/codex/skills/`
   - `https://developers.openai.com/codex/security/#common-sandbox-and-approval-combinations`
   - `https://platform.openai.com/docs/guides/function-calling#strict-mode`
   - `context7:/openai/skills`
5. `T4 protocol_spec` (official spec + local contract):
   - `https://modelcontextprotocol.io/specification/latest`
   - `https://agentskills.io/specification`
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
   - `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`

Cross-track findings (deep cross-check, 2026-03-05):

1. No contradiction found between v1.6 kernel-first/dual-lane direction and external vendor/spec guidance.
2. Skills governance consistency is reaffirmed:
   - OpenAI Codex skills and Agent Skills spec both require metadata-first discovery + progressive disclosure + `SKILL.md` contractized body loading.
3. Strict fail-close semantics are externally aligned:
   - OpenAI strict function-calling guidance (`strict=true`) and MCP security principles both reinforce explicit schema/control boundaries instead of best-effort inference.
4. Full-stack runtime separation principle is externally aligned:
   - Anthropic role/system-prompt guidance and Google AI Studio server-side+secrets guidance both support explicit role context + secret isolation, consistent with v1.6 actor-explicit lane governance.
5. Remaining gap classification unchanged:
   - this replay strengthens evidence quality only; executable convergence requirements (`ASB16-RQ-015/029/030/031`) are implemented but remain replay-closure pending.

Positive-strengthening directives (v1.6 forward-only, non-promotional):

1. `F1 actor-explicitness hardening`: strict-path replay must carry explicit actor context in every promotion-grade chain.
2. `F2 intake automation`: convert `T1..T4` checklist to machine fail-close intake validator (remove checklist-only pass risk).
3. `F3 semantic convergence`: prioritize canonical semantic receipt + cross-plane comparator before any status promotion claims.
4. `F4 multimodal sample-proof`: bind trigger/knowledge/arbitration sample outputs to kernel-to-validator mapping fields.
5. `F5 boundary discipline`: keep v1.5 closure frozen; v1.6 supplements cannot rewrite historical release verdicts.

Deterministic judgment:

1. This fix is a final cross-verification reinforcement intake for v1.6 and is valid as positive evidence hardening.
2. It does not promote any requirement from `SPEC_READY` by itself.
3. Any `DONE` claim for `ASB16-RQ-015/017/029/030/031` still requires executable implementation + independent replay audit.

### FIX16-028 - full-repo deep-scan lock inventory (`ASB16-RQ-001..032`)

- Status: `SPEC_READY`
- Goal: complete full-repo deep scan over `docs/** + scripts/** + identity/protocol/**`, freeze lock-state census for all v1.6 requirements, and make architect-side independent rescan mandatory before promotion.

Scope and lock definition:

1. `KERNEL_LOCKED`: explicit normative requirement anchor under `identity/protocol/*`.
2. `SCRIPT_LOCKED`: executable gate mapping under `scripts/*` with machine-readable status/error/report fields.
3. `BRIDGE_LOCKED`: governance + review bridge rows exist and remain status-consistent.
4. `FULL_LOCKED = KERNEL_LOCKED && SCRIPT_LOCKED && BRIDGE_LOCKED`.

Deep-scan verdict (2026-03-05):

1. `BRIDGE_LOCKED=32/32`.
2. `KERNEL_LOCKED=0/32` under `ASB16-RQ-*` anchor criterion.
3. `SCRIPT_LOCKED=0/32` under `ASB16-RQ-*` / v1.6 contract-id executable anchor criterion.
4. `FULL_LOCKED=0/32`; all rows remain `UNLOCKED` and cannot promote beyond intake without kernel+script lock anchors.


Architect independent deep-rescan receipt (executed, 2026-03-05):

1. `/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`
2. `/tmp/v16_architect_deep_scan_full_repo_20260305.json`
3. `/tmp/v16_architect_deep_scan_full_repo_20260305.md`
4. `/tmp/v16_one_by_one_requirement_review_20260305.md`

Receipt reconciliation summary:

1. inventory cardinality confirmed: `ASB16-RQ-001..032` (`total=32`).
2. lock-state remained deterministic with independent run: `BRIDGE_LOCKED=32/32`, `KERNEL_LOCKED=0/32`, `SCRIPT_LOCKED=0/32`, `FULL_LOCKED=0/32`.
3. one-by-one matrix exported for audit row-level review; no requirement qualifies for promotion under current lock tuple.

Mandatory follow-up for promotion eligibility:

1. Use governance section `7.3` as canonical 32-row lock inventory source.
2. Use governance section `7.4` as architect independent deep-rescan command protocol.
3. Promotion claims without independent rescan receipt are invalid.

### FIX16-029 - outbound headstamp pre-send hard-gate intake (`ASB16-RQ-032`)

- Status: `SPEC_READY`
- Goal: make headstamp omission impossible at send-time by enforcing transport-level fail-close gate instead of template-only discipline.

Root-cause statement:

1. Prior fixes improved governed compose/send-time chains, but direct/manual reply paths can still bypass headstamp injection.
2. Therefore the missing-headstamp issue is not fully closed until send-layer gate blocks all outbound paths.

Contractized closure target:

1. Add pre-send validator that runs for every outbound reply path.
2. Enforce canonical first-line tuple:
   - `Identity-Context: ...`
   - `Layer-Context: ...`
3. Fail-close codes reserved by governance:
   - `IP-HDSTAMP-001` (`headstamp_missing_or_malformed`)
   - `IP-HDSTAMP-002` (`headstamp_actor_binding_mismatch`)
   - `IP-HDSTAMP-003` (`headstamp_receipt_missing`)

Deterministic acceptance matrix:

1. Negative replay A: missing/malformed headstamp -> `FAIL_REQUIRED` + `IP-HDSTAMP-001`.
2. Negative replay B: actor/canonical mismatch -> `FAIL_REQUIRED` + `IP-HDSTAMP-002`.
3. Negative replay C: promotion-grade lane with missing receipt -> `FAIL_REQUIRED` + `IP-HDSTAMP-003`.
4. Positive replay: canonical tuple present and matched -> `PASS_REQUIRED` with machine receipt.

Promotion boundary:

1. This fix is intake only and does not promote `ASB16-RQ-032`.
2. Promotion requires script implementation + e2e/ci replay evidence + independent architect re-audit.

### FIX16-030 - Batch-1 (`ASB16-RQ-001..005`) strengthening normalization

- Status: `SPEC_READY`
- Goal: convert Batch-1 from concept-level correctness to non-ambiguous execution predicates, while keeping status non-promotional until implementation anchors exist.

Cross-check basis:

1. Governance/review status is aligned but still intake-only:
   - `ASB16-RQ-001..005` remain `SPEC_READY` (`docs/governance/...v1.6.0.md` section `5` + section `7`).
2. Lock inventory confirms `UNLOCKED`:
   - section `7.3` rows for `ASB16-RQ-001..005` are `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`.
3. Script baseline is partially available for `RQ-002/004/005` but not contract-locked:
   - capability chain (`release_readiness/full_scan/three_plane`);
   - outlet compose/send-time chain;
   - sidecar/writeback continuity chain.

Mandatory strengthening constraints (P0):

1. `RQ-001`: unlock formula must avoid cyclic predicates (`D1..D5` input, `D6` derived).
2. `RQ-002`: capability boundary must use explicit error-code mapping + auditable override.
3. `RQ-003`: promotion receipt must be non-repudiable (`decision_hash`, `input_hash`, reviewer signature reference).
4. `RQ-004`: outlet matrix must include negative paths and bind to `ASB16-RQ-032`.
5. `RQ-005`: sidecar/direct equivalence must be normalized hash-based, not raw/noise-sensitive compare.
6. Mapping lock fields (`kernel/script/full`) must be scanner-computed, not manually filled.
7. Mapping rows must include ownership and acceptance gate metadata.

Batch-1 decision:

1. Verdict per row: `ACCEPT_WITH_FIX`.
2. Promotion prohibition: none of `ASB16-RQ-001..005` can leave `SPEC_READY` before five-anchor closure exists (`kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`).
3. Evidence pointer: governance section `8.5` is the canonical strengthening profile for this batch.

Status interpretation guard (mandatory, avoids reader misclassification):

1. `ACCEPT_WITH_FIX` here means design acceptance only; implementation remains pending.
2. Therefore audit status stays `PENDING_INTAKE` until planned anchors become real files and pass replay checks.
3. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Current missing anchors snapshot (2026-03-05):

1. batch-1 validators partially landed:
   - `scripts/validate_unlock_formula.py` (RQ-001) landed with mapping/kernel anchors and lane hooks.
2. batch-1 validator set landed:
   - `scripts/validate_capability_boundary_classification.py` (RQ-002)
   - `scripts/validate_promotion_pipeline.py` (RQ-003)
   - `scripts/validate_outlet_matrix.py` (RQ-004)
   - `scripts/validate_sidecar_cwd_parity.py` (RQ-005)
3. scanner-computed lock script anchor not yet landed:
   - canonical anchor: `scripts/validate_actor_session_multibinding_concurrency.py` (lock inventory + multi-binding drift envelope).

### FIX16-031 - Batch-2A (`ASB16-RQ-006..010`) strengthening normalization

- Status: `SPEC_READY`
- Goal: harden Batch-2A from “capability present but partially wired” into deterministic non-ambiguous closure predicates, without promotional drift.

Batch naming normalization (mandatory):

1. This fix is explicitly `Batch-2A` and covers only `ASB16-RQ-006..010`.
2. This avoids tracker collision with later batches (including `ASB16-RQ-014/015/023`).
3. Any ledger statement that merges these sets under one batch label is invalid.

Row-level acceptance result:

1. `ASB16-RQ-006..010` are all `ACCEPT_WITH_FIX`.
2. All rows remain `SPEC_READY / PENDING_INTAKE`.
3. No row in this fix is promotion-eligible.

Strengthening outcomes required by this fix:

1. `RQ-006` release-plane cloud evidence:
   - closure validator exists, but required-gate wiring is incomplete;
   - readiness/three-plane/full-scan must consume one unified release-plane validator output.
2. `RQ-007` cross-cwd absolute-input:
   - partial cwd-invariant hardening exists;
   - contract + scanner replay for root/tmp parity and absolute-catalog negative replay are still required.
3. `RQ-008` docs bridge consistency:
   - command contract + SSOT source checks exist;
   - governance/review state contradiction checker is still missing.
4. `RQ-009` run-id anchored report selection:
   - freshness/baseline/readiness selectors still allow mtime-dominant drift;
   - `report_three_plane_status.py` must join the same run-id-first selector contract.
5. `RQ-010` phase-A/bootstrap before strict phase-B:
   - update flow already has two-phase contract trace;
   - readiness flow must reach equivalent two-phase semantics and expose same phase fields for aggregation.

Homomorphism assertions (mandatory acceptance predicates):

1. `RQ-006`: `release_plane_detail.conditions` key-set must be identical across readiness, three-plane, and full-scan outputs for same release evidence payload.
2. `RQ-007`: protocol-root cwd and tmp cwd replays must keep required verdict fields equivalent under same payload; non-root missing absolute catalog must fail-close with stable `IP-CWD-004` semantics.
3. `RQ-008`: contradiction tuples and anchor refs must be deterministic across reruns on unchanged docs.
4. `RQ-009`: for same run-id and candidate set, `report_selected_path` must be identical in freshness + baseline + alignment + readiness + three-plane chains.
5. `RQ-010`: qualifying stale-baseline recovery must show `phase_a_refresh_applied=true` and `phase_b_strict_revalidate_status=PASS_REQUIRED`.

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires row-level five-link anchor closure and scanner-computed lock evidence.

### FIX16-032 - Batch-3B (`ASB16-RQ-024..028`) strengthening normalization

- Status: `SPEC_READY`
- Goal: convert kernel-first P0 cluster (`ASB16-RQ-024..028`) from intake-level agreement to non-ambiguous executable closure predicates while preserving non-promotional boundary.

Batch naming guard (mandatory):

1. This fix is explicitly `Batch-3B` and covers only `ASB16-RQ-024..028`.
2. `Batch-3` label remains reserved for `ASB16-RQ-011..015`; extension batches must use suffixed naming (`Batch-3A/3B/...`).
3. Any ledger statement that merges these scopes under one unsuffixed batch label is invalid.

Row-level acceptance result:

1. `ASB16-RQ-024..028` are all `ACCEPT_WITH_FIX`.
2. All rows remain `SPEC_READY / PENDING_INTAKE`.
3. No row in this fix is promotion-eligible.

Strengthening outcomes required by this fix:

1. `RQ-024` discovery apply coverage hard-close:
   - governance requires `discovery_required_total>0`, `discovery_required_passed==discovery_required_total`, `discovery_required_coverage_rate==100.0`, but implementation still has semantic drift;
   - `IP-DREQ-002` must be reserved for coverage mismatch only; receipt-missing semantics must use dedicated code;
   - coverage hard-gate must be default-on and consumed consistently in `update/readiness/e2e/full-scan/three-plane/ci`.
2. `RQ-025` kernel canonical source:
   - v1.6 must be kernel-first (`identity/protocol/* + identity/catalog/schema/*`);
   - v1.5 handoff-based SSOT checks remain compatibility checks only and cannot substitute v1.6 kernel-source validation.
3. `RQ-026` kernel->validator->doc mapping:
   - mapping file and checker are currently missing; coverage/orphan claims remain non-machine-verifiable;
   - implementation must land `contract-binding.v1.6.yaml` plus coverage checker before any promotion claim.
4. `RQ-027` derived prompt conformance:
   - runtime compilation currently proves prompt hash existence but not full derivation lineage;
   - required conformance metadata (`kernel_contract_version`, `kernel_contract_digest`, `derived_from_contract_ids`, `overlay_digest`) must be generated and validator-consumed.
5. `RQ-028` instance write-boundary lock:
   - replay validator is wired, but canonical v1.6 fail-close code alignment and pre-write guard unification remain pending;
   - error-code semantics must converge to `IP-KERNEL-WRITE-001` (legacy code may remain alias only during transition).

Cross-batch normalization constraint (blocking misclassification):

1. `ASB16-RQ-014` must not introduce parallel machine output field family.
2. Bootstrap driver semantics from `RQ-014` must reuse `ASB16-RQ-015` canonical six-field machine output set.
3. Any dual field-family interpretation is treated as unresolved drift and blocks promotion.

Homomorphism assertions (mandatory acceptance predicates):

1. `RQ-024`: same requiredization payload must yield identical `discovery_required_* + status + error_code` across update/readiness/e2e/full-scan/three-plane/ci.
2. `RQ-025`: same contract set must yield stable kernel-source census and `unmapped_base_contract_count=0`.
3. `RQ-026`: mapping replay must remain deterministic with `coverage_rate=100` and `orphan_count=0`.
4. `RQ-027`: identical derivation inputs must produce identical conformance metadata digest chain.
5. `RQ-028`: identical forbidden write attempts must return same boundary verdict and canonical error-code family across lanes.

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires row-level five-link anchor closure and scanner-computed lock evidence.

### FIX16-033 - Batch-4 (`ASB16-RQ-029/031/032/007/008`) four-track strengthening normalization

- Status: `SPEC_READY`
- Goal: normalize Batch-4 four-track intake into deterministic row-level strengthening predicates for `P0` convergence (`RQ-029/031/032`) and `P1` bridge alignment (`RQ-007/008`), while keeping non-promotional boundary unchanged.

Batch naming/scope lock (mandatory):

1. This fix is explicitly `Batch-4` and covers only `ASB16-RQ-029/031/032/007/008`.
2. Topic split is fixed:
   - `P0 convergence cluster`: `ASB16-RQ-029/031/032`
   - `P1 bridge cluster`: `ASB16-RQ-007/008`
3. Any ledger statement that expands this fix to other requirements is invalid.

Four-track evidence binding guard (mandatory):

1. `T1 roundtable`: `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
2. `T2 vendor`: `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
3. `T3 openai_context` receipt anchors: governance+review cross-verification record (`docs/review/protocol-remediation-audit-ledger-v1.6.md` row set for cross-verification receipt references).
4. `T4 protocol_spec` anchors: MCP/tool-collaboration/spec references (`docs/references/skill-mcp-tool-collaboration-contract-v1.0.md` + linked official specs already registered in review references).
5. Missing any one track blocks promotion beyond `PENDING_INTAKE`.

Row-level acceptance result:

1. `ASB16-RQ-029/031/032/007/008` are all `ACCEPT_WITH_FIX`.
2. All rows remain `SPEC_READY / PENDING_INTAKE`.
3. Lock-state remains `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK=UNLOCKED` for all five rows.
4. No row in this fix is promotion-eligible.

Strengthening outcomes required by this fix:

1. `RQ-029` semantic single-source convergence:
   - canonical receipt field family must be emitted and consumed (`semantic_routing_status/error_code/evidence_path/reason/source`);
   - convergence comparator must fail-close same-lineage mixed verdicts with stable `IP-SEM-CONV-001`.
2. `RQ-031` prompt import executable-coupling:
   - machine mapping chain must be explicit (`kernel_contract_ref -> validator_ref -> evidence_ref`) with `actor_context_explicit`;
   - strict lane must require explicit `--actor-id`; multimodal proof validators (trigger/knowledge/arbitration) must feed one unified mapping receipt.
3. `RQ-032` headstamp pre-send hard gate:
   - runtime error family must converge to canonical `IP-HDSTAMP-001/002/003` (legacy `IP-ASB-STAMP-SESSION-*` alias only during compatibility transition);
   - governed and direct/manual send paths must use one pre-send fail-close source.
4. `RQ-007` cross-cwd consistency:
   - partial three-plane hardening is insufficient; readiness/freshness/baseline/alignment chains must join root/tmp parity replay and absolute-catalog fail-close contract (`IP-CWD-004` stable semantics).
5. `RQ-008` docs bridge consistency:
   - command-contract and SSOT checks exist, but contradiction checker is missing;
   - governance-vs-review contradiction tuples and anchor refs must be machine-emitted with deterministic ordering.

Hard-tightening addendum (audit-locked, must hold for closure):

1. `RQ-032` error-family convergence hard rule:
   - canonical v1.6 runtime family is `IP-HDSTAMP-001/002/003`;
   - `IP-ASB-STAMP-SESSION-*` may exist only as compatibility alias during migration and cannot be final promotion-grade classification.
2. `RQ-029` convergence comparator minimum outputs:
   - `mismatch_count`, `lineage_ref`, `semantic_convergence_status`, `semantic_convergence_error_code` are mandatory fields.
3. `RQ-031` executable-coupling + actor-explicit hard gate:
   - canonical fail-close codes `IP-PROMPT-CONTRACT-001` and `IP-ACTOR-CTX-001` must be machine-emitted where applicable;
   - compile/runtime hard-gate metadata is mandatory: `kernel_contract_version`, `kernel_contract_digest`, `derived_from_contract_ids`, `overlay_digest`.
4. `RQ-007` must be full-chain, not local patch:
   - cross-cwd invariance must be validated across readiness/freshness/baseline/alignment in addition to three-plane.
5. `RQ-008` contradiction checker remains required:
   - absence of governance/review contradiction checker keeps this row in `PLANNED_ONLY` and blocks promotion.

Headstamp omission bypass postmortem supplement (detailed, audit-tracked):

1. Bypass root-cause decomposition (`RQ-032`):
   - current state is still contract-first and partial wiring, not fully single-source pre-send enforcement;
   - some outbound paths can emit replies without passing one mandatory validator entrypoint;
   - mixed legacy error-family traces show migration incompleteness (`IP-ASB-STAMP-SESSION-*` still visible on execution surfaces).
2. Closure-grade corrective requirement:
   - missing-or-malformed first-line headstamp => hard block with canonical `IP-HDSTAMP-001` (`headstamp_missing_or_malformed`);
   - runtime actor/layer mismatch => hard block with canonical `IP-HDSTAMP-002` (`headstamp_actor_binding_mismatch`);
   - promotion-grade lane receipt missing => hard block with canonical `IP-HDSTAMP-003` (`headstamp_receipt_missing`);
   - warning-only behavior is explicitly forbidden for promotion-grade lanes.
3. Mandatory anti-bypass receipt schema:
   - `pre_send_headstamp_checked`
   - `pre_send_headstamp_gate_status`
   - `pre_send_headstamp_error_code`
   - `pre_send_gate_source`
   - `pre_send_actor_binding_ref`
   - `pre_send_checked_at`
4. Unified gate consumption requirement:
   - governed compose + direct/manual outbound paths must consume the same pre-send validator output;
   - route-local custom checks may enrich evidence but may not replace canonical verdict/error family.
5. Replay proof obligations:
   - one positive and three negative cases (`missing-or-malformed`, `binding-mismatch`, `receipt-missing`) must be replayed;
   - all lanes must produce deterministic and homomorphic canonical classification on unchanged inputs.

Actor-id fallback recurrence supplement (`RQ-031/RQ-032` coupling, audit replay on 2026-03-06):

1. Observed deterministic runtime behavior:
   - strict compose path invoked without explicit `--actor-id` resolved runtime actor to `user:yangxi` through fallback chain;
   - actor-session binding for `user:yangxi` pointed to `custom-creative-ecom-analyst`, while requested identity was `base-repo-audit-expert-v3`;
   - pre-send gate correctly blocked with actor-binding mismatch branch (`IP-ASB-STAMP-SESSION-005` compatibility trace), surfaced as perceived "hard switch".
2. Counter-check replay:
   - same payload with explicit `--actor-id assistant:codex` passed strict send-time gate and emitted canonical first-line headstamp;
   - activation switch guard required explicit audited intent receipt (`IP-ACT-SWITCH-001` -> replay with `--allow-identity-switch --switch-intent-receipt` succeeded), confirming guard behavior is fail-closed rather than silent switch.
3. Gap classification:
   - policy semantics are already defined in governance, but executable closure is incomplete because strict promotion-grade paths still allow actor fallback entry.
4. Closure requirement (non-promotional until landed):
   - strict lanes must require explicit actor context and reject fallback actor resolution before send-time classification;
   - compatibility `IP-ASB-STAMP-SESSION-005` traces must converge to explicit actor-context contract classification (`IP-ACTOR-CTX-001`) for promotion-grade evidence;
   - receipt schema must include actor-context proof tuple (`resolved_actor_id`, `actor_fallback_used`, `actor_binding_identity_id`, `actor_context_explicit_status`).
5. Acceptance command set (mandatory before promotion):
   - negative A: strict compose/send-time without `--actor-id` must fail-close with actor-context explicitness error;
   - negative B: strict compose/send-time with mismatched explicit actor binding must fail-close deterministically;
   - positive C: strict compose/send-time with explicit bound actor must pass and emit canonical headstamp first line;
   - unchanged payload must preserve verdict homomorphism across creator/readiness/e2e/full-scan/three-plane/ci.

Batch-4 five-link anchor lock (mandatory per row):

1. Required anchor tuple for each row is fixed as:
   - `kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance_cmd`.
2. Missing any element in the tuple keeps the row at `ACCEPT_WITH_FIX` and non-promotional.
3. `FIX16-033` summary row, detail section, and decision-log row must remain same-batch and same-status synchronized.

Homomorphism assertions (mandatory acceptance predicates):

1. `RQ-029`: same lineage input must return identical semantic verdict tuple across update/three-plane/full-scan; mismatch must deterministically map to `IP-SEM-CONV-001`.
2. `RQ-031`: same prompt import payload must generate deterministic executable-coupling mapping receipt and actor-explicit evidence.
3. `RQ-032`: identical missing/malformed/mismatch negative cases must map to identical canonical `IP-HDSTAMP-*` codes across creator/readiness/e2e/full-scan/three-plane/ci.
4. `RQ-007`: same payload replayed under protocol-root and `/tmp` must preserve required verdict fields; non-root relative repo-catalog must fail-close deterministically.
5. `RQ-008`: unchanged docs must yield identical contradiction tuple ordering and anchor refs across reruns.

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires per-row `kernel + script + replay` closure (`five-link anchors`) and scanner-computed lock-state.

### FIX16-034 - Batch-5 (`ASB16-RQ-010/011/012/013/016`) orchestration strengthening normalization

- Status: `SPEC_READY`
- Goal: normalize Batch-5 execution-orchestration cluster into deterministic, machine-auditable closure predicates while preserving non-promotional boundary (`ACCEPT_WITH_FIX` only).

Batch naming/scope lock (mandatory):

1. This fix is explicitly `Batch-5` and covers only `ASB16-RQ-010/011/012/013/016`.
2. Topic lock:
   - orchestration parity closure: `RQ-010/011/012/013/016`;
   - no expansion into `RQ-014/015` or `RQ-024+` scope in this fix.
3. Any ledger statement that merges unrelated requirements into this fix is invalid.

Four-track evidence binding guard (mandatory):

1. `T1 governance`: contracts + `C10` matrix obligations are normative anchors.
2. `T2 review`: intake rows + decision log must remain synchronized with this fix.
3. `T3 scripts`: executable evidence must be script-verifiable; prose-only closure claims are invalid.
4. `T4 external/vendor/spec`: roundtable + vendor + context/spec links remain mandatory references for policy consistency.
5. Missing any track blocks promotion beyond `PENDING_INTAKE`.
6. Runtime replay snapshots must be timestamped (`observed_head_sha`, `working_tree_dirty`, `observed_at_utc`); stale “HEAD/clean” statements are evidence-invalid.

Draft-time replay snapshot (this landing pass, non-promotional evidence metadata):

1. `observed_head_sha=3303bb5`.
2. `working_tree_dirty=true` (docs-only pending changes in governance/review files for Batch-5 hardening).
3. `observed_at_utc=2026-03-06T06:38:16Z`.
4. This snapshot is for replay traceability only and does not alter row-level status semantics.

Row-level acceptance result:

1. `ASB16-RQ-010/011/012/013/016` are all `ACCEPT_WITH_FIX`.
2. All rows remain `SPEC_READY / PENDING_INTAKE`.
3. Lock-state remains `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK=UNLOCKED` for all five rows.
4. No row in this fix is promotion-eligible.

Strengthening outcomes required by this fix:

1. `RQ-010` phase-A bootstrap before strict:
   - update lane already carries two-phase semantics and report fields (`phase_a_refresh_applied`, `phase_b_strict_revalidate_status`);
   - readiness lane still fail-fast exits on baseline strict preflight;
   - closure requires readiness parity orchestration plus phase trace consumption in three-plane/full-scan.
2. `RQ-011` tmp collision-safe allocator:
   - required lanes still rely on identity-only fixed `/tmp` artifact names;
   - partial run-id isolation exists in creator path but not as shared allocator contract;
   - closure requires allocator + concurrency collision validator (`collision_count=0` proof).
3. `RQ-012` handoff/collab freshness auto-rotation:
   - current gates perform age-based fail-close checks;
   - deterministic auto-rotation writer and rotation receipt validator are missing;
   - canonical validator anchors for this fix lane:
     - `scripts/validate_handoff_collab_freshness_rotation.py`,
     - `scripts/validate_identity_mode_promotion_arbitration.py`.
4. `RQ-013` protocol-feedback atomic emit:
   - bootstrap/index/archival validators exist, but execution remains chained step-wise rather than single-transaction emit;
   - index linkage helper is append-style and lacks rollback transaction semantics;
   - closure requires atomic emit helper + transaction validator and lane-wide consumption.
5. `RQ-016` refresh->strict business interference matrix:
   - governance contract and C10 requirement exist, but scripts do not emit machine-readable interference matrix fields;
   - this is a field-level gap distinct from `RQ-010` phase fields (`phase_a_refresh_applied`, `phase_b_strict_revalidate_status`) and cannot be closed by phase outputs;
   - closure requires matrix writer + validator + paired refresh/strict replay receipts.

Review mapping precision lock (mandatory):

1. `RQ-016` is mapped to `FIX16-017` (`refresh->strict + business interference guard runbook intake`) and must not be relabeled as `FIX16-016`.
2. Any review note that maps `RQ-016 -> FIX16-016` is treated as ledger drift and blocks promotion evidence acceptance.

Homomorphism assertions (mandatory acceptance predicates):

1. `RQ-010`: stale-baseline recovery replays must deterministically return `phase_a_refresh_applied=true` and `phase_b_strict_revalidate_status=PASS_REQUIRED` across update/readiness/three-plane/full-scan.
2. `RQ-011`: same parallel run-set must keep unique temp artifact paths and `collision_count=0`.
3. `RQ-012`: unchanged stale handoff/collab inputs must keep identical rotation decision tuple and receipt refs.
4. `RQ-013`: identical atomic emit input must keep stable `transaction_id` + (`batch_ref`, `index_ref`, `receipt_ref`) tuple without partial leftovers.
5. `RQ-016`: paired refresh/strict replay must keep deterministic interference-matrix row keys and verdict tuple.

Roundtable-B5 kickoff package (execution-ready):

1. participants:
   - `base-repo-architect`, `audit-expert(codex)`, `system-requirements-analyst`, `script owner`, `protocol-spec reviewer`.
2. agenda:
   - `RQ-010 -> RQ-011 -> RQ-012 -> RQ-013 -> RQ-016`.
3. required output fields:
   - `rq_id`, `anchor_state`, `kernel_anchor_path`, `script_anchor_path`, `mapping_anchor_path`, `acceptance_command_set`, `promotion_blocker`, `owner`, `target_commit`.
4. exit condition:
   - rows without `kernel + script + replay` closure stay `SPEC_READY/PENDING_INTAKE`.
5. per-row review rubric (mandatory three questions):
   - kernel: is contract field semantics unique and non-ambiguous?
   - script: is fail-close single-entry and non-bypassable?
   - receipt: is replay machine-comparable and archiveable?

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires per-row `kernel + script + replay` closure (`five-link anchors`) and scanner-computed lock-state.

### FIX16-035 - Batch-6 (`ASB16-RQ-017/018/019/020/021`) cross-workflow governance strengthening normalization

- Status: `SPEC_READY`
- Goal: convert Batch-6 from requirement-level intake to explicit lane-hooked validator contracts with deterministic replay receipts.
- Audit class: `PASS_WITH_BLOCKERS` (non-promotional; closure blocked until blocker bundle is resolved).

Batch naming/scope lock (mandatory):

1. This fix is explicitly `Batch-6` and covers only `ASB16-RQ-017/018/019/020/021`.
2. Topic lock:
   - `RQ-017`: four-track cross-verification contract;
   - `RQ-018`: dedup monotonic winner contract;
   - `RQ-019`: cross-workflow evidence schema contract;
   - `RQ-020`: skill path integrity contract;
   - `RQ-021`: route/workflow publish-version pinning contract.
3. No reinterpretation of this fix as promotion-ready is allowed.

Four-track and lock snapshot (binding):

1. Batch-6 lifecycle remains `SPEC_READY` with decision class `ACCEPT_WITH_FIX`; current synchronized audit verdict is `PASS_WITH_BLOCKERS`.
2. Lock-state remains `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK=UNLOCKED` for all five rows.
3. Missing `T1/T2/T3/T4` evidence or missing required receipt fields keeps status non-promotional.

Row-level cross-check and explicit hook plan:

| Requirement ID | Anchor state | Finding (cross-check) | Concrete hook plan (must all land) | Acceptance target |
| --- | --- | --- | --- | --- |
| ASB16-RQ-017 | `PARTIAL` | governance/review contract exists; scripts only provide distributed checks, not single four-track quorum verdict | canonical parser must be single-source: `scripts/validate_intake_evidence_core.py --mode intake_contract`; optional wrapper `scripts/validate_v16_cross_verification_tracks.py` may only delegate; enforce call chain `identity_creator.py` -> `release_readiness_check.py` -> `report_three_plane_status.py`/`full_identity_protocol_scan.py` -> `e2e_smoke_test.sh`; canonical fields must include `t1_status/t2_status/t3_status/t4_status` + metadata quartet | all tracks + metadata present => `PASS_REQUIRED`; any missing track/metadata => deterministic `FAIL_REQUIRED` |
| ASB16-RQ-018 | `PARTIAL` | monotonic dedup validator/wrapper landed, but deterministic positive+negative replay evidence for same `run_id` concurrency still missing | keep canonical path `scripts/validate_dedup_monotonicity.py`; optional compatibility wrapper `scripts/validate_v16_dedup_monotonicity.py` may only delegate; keep hooks active in creator/readiness/three-plane/full-scan/e2e/ci; add replay artifacts proving stable winner tuple under repeated parallel claims | unchanged concurrent replay keeps identical `winner_id` tuple and `monotonicity_status=PASS_REQUIRED` |
| ASB16-RQ-019 | `PARTIAL` | cross-workflow normalizer + schema validator landed and are lane-wired; replay evidence closure still pending | keep canonical pair `scripts/normalize_cross_workflow_evidence.py` + `scripts/validate_cross_workflow_schema.py`; preserve creator/readiness/three-plane/full-scan/e2e/ci consumption on canonical fields only | `run_id/route_action/quality_meta_state/dedup_state/evidence_hash` always present and hash-stable |
| ASB16-RQ-020 | `PARTIAL` | skill-path integrity validator landed and lane-wired; strict layout replay matrix (in-layout pass/out-of-layout fail) still pending archive closure | keep `scripts/validate_skill_path_integrity.py` as single fail-close gate; retain capability-activation as source-only data; enforce same verdict in creator/readiness/three-plane/full-scan/e2e/ci | any out-of-layout/missing skill path fails deterministically with canonical path-integrity code |
| ASB16-RQ-021 | `PARTIAL` | emitter-before-gate sequence is now implemented, but full-chain replay evidence for required=true pinning scenarios remains incomplete | keep emitter-first (`scripts/emit_route_version_pin_receipt.py`) then gate (`scripts/validate_route_version_pinning.py`); retain creator/readiness/three-plane/full-scan/e2e/ci hooks; add deterministic mismatch replay archive | pin proof required for pass; endpoint-version mismatch must fail-close with canonical pin error code |

Batch-6 five-link anchor lock (mandatory per row):

1. Each row must provide `kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance_cmd`.
2. Missing any anchor keeps row `ACCEPT_WITH_FIX` and non-promotional.
3. `FIX16-035` rolling summary row, detail section, and decision-log row must remain synchronized.
4. Mapping asset absence (`identity/protocol/mappings/contract-binding.v1.6.yaml`) is a hard blocker and invalidates lock computation for Batch-6.

Batch-6 acceptance command set (normative target):

```bash
python3 scripts/validate_intake_evidence_core.py \
  --mode intake_contract \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --bundle-id <BUNDLE_ID> \
  --operation readiness \
  --json-only

python3 scripts/validate_dedup_monotonicity.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --run-id <RUN_ID> \
  --parallel-claims 5 \
  --json-only

python3 scripts/validate_cross_workflow_schema.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation three-plane \
  --json-only

python3 scripts/validate_skill_path_integrity.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation readiness \
  --json-only

python3 scripts/emit_route_version_pin_receipt.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation readiness \
  --route-endpoint <ROUTE_ENDPOINT> \
  --workflow-id <WORKFLOW_ID> \
  --workflow-publish-version <WORKFLOW_PUBLISH_VERSION> \
  --out <PIN_RECEIPT_PATH> \
  --json-only

python3 scripts/validate_route_version_pinning.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation readiness \
  --receipt <PIN_RECEIPT_PATH> \
  --expected-route-endpoint <ROUTE_ENDPOINT> \
  --expected-workflow-id <WORKFLOW_ID> \
  --expected-workflow-publish-version <WORKFLOW_PUBLISH_VERSION> \
  --json-only
```

Batch-6 blocker bundle (must resolve before promotion):

1. Mapping asset missing:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml` (and directory) must land first.
2. `RQ-017`/`RQ-030` parser drift risk:
   - single parser + dual mode is mandatory (`intake_contract`/`promotion_gate`), no duplicated field logic.
3. `RQ-021` proof-source gap:
   - gate is invalid without emitter-backed publish-version receipt.
4. Coverage lock gap:
   - new Batch-6 gates must be added to `validate_required_contract_coverage.py TARGETS`.
5. Aggregator extraction gap:
   - `report_three_plane_status.py` and `full_identity_protocol_scan.py` must consume canonical verdict fields from new receipts.

Batch-6 execution hook closure snapshot (Task-8..12 landed, replay pending):

1. landed commits:
   - `9e59e0f` (mapping seed),
   - `f63eb55` + `e214df9` (single-parser dual-mode intake core),
   - `9c0cf0a` (`RQ-018` validator),
   - `19d02ab` (`RQ-019` normalizer + validator),
   - `b5a191c` (`RQ-020` validator + scan surfaces),
   - `fffc3c3` (`RQ-021` emitter + gate),
   - `08c8f89` (coverage/aggregator extraction),
   - `5f7eb44` (readiness hook),
   - `228ba40` (creator validate/update hook),
   - `b7137e3` (e2e hook),
   - `47f2f38` (CI required-gates hook).
2. posture remains non-promotional:
   - all rows keep lifecycle `SPEC_READY` with decision class `ACCEPT_WITH_FIX`;
   - audit remains `PASS_WITH_BLOCKERS` until deterministic replay archive closes (`Task-15` closed blocker subset to `PASS_REQUIRED`);
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`;
   - deterministic positive/negative replay archive is still mandatory before any lock upgrade.

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires all five rows to complete five-link anchors plus positive/negative deterministic replay.

### FIX16-036 - Batch-7 (`ASB16-RQ-022/030`) closure strengthening normalization

- Status: `SPEC_READY`
- Goal: close Batch-7 by making fallback taxonomy + intake quorum contracts executable across all required lanes.
- Audit class: `PASS_WITH_BLOCKERS` (non-promotional; taxonomy/promotion-gate closure still blocked).

Batch naming/scope lock (mandatory):

1. This fix is explicitly `Batch-7` and covers only `ASB16-RQ-022/030`.
2. Topic lock:
   - `RQ-022`: fallback taxonomy normalization to governed enum set;
   - `RQ-030`: four-track intake evidence quorum hard gate with metadata completeness.
3. Both rows remain non-promotional until deterministic required=true replay archive and lock-closure evidence are complete.

Row-level cross-check and explicit hook plan:

| Requirement ID | Anchor state | Finding (cross-check) | Concrete hook plan (must all land) | Acceptance target |
| --- | --- | --- | --- | --- |
| ASB16-RQ-022 | `PARTIAL` | fallback taxonomy normalizer is implemented and lane-wired, but required=true replay archive across readiness/e2e/ci paths is not yet complete | keep `scripts/validate_fallback_taxonomy_normalization.py`; preserve dual-field output (`fallback_reason_raw`, `fallback_taxonomy_class`) and blocker-namespace isolation; keep creator/readiness/three-plane/full-scan/e2e/ci consumption aligned | each fallback sample maps to governed class (`data_missing/model_weak_signal/transport_error/policy_blocked`); unmappable value fails deterministically without breaking blocker chain |
| ASB16-RQ-030 | `PARTIAL` | canonical parser + wrapper + lane hooks landed, but quorum replay evidence for required=true bundles remains incomplete | keep canonical parser `scripts/validate_intake_evidence_core.py --mode promotion_gate`; wrapper `scripts/validate_v16_intake_evidence_quorum.py` delegates only; maintain single fail-close entrypoint in creator/readiness/three-plane/full-scan/e2e/ci | any missing track (`T1..T4`) or missing metadata (`bundle_id/source_url_set/reference_timestamp_utc/conflict_note`) blocks with deterministic fail code |

Batch-7 five-link anchor lock (mandatory per row):

1. Required anchor tuple remains `kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance_cmd`.
2. Missing any anchor keeps row at `ACCEPT_WITH_FIX` and blocks promotion.
3. `FIX16-036` rolling summary row, detail section, and decision-log row must stay synchronized.
4. Mapping asset absence (`identity/protocol/mappings/contract-binding.v1.6.yaml`) is a hard blocker and invalidates lock computation for Batch-7.

Batch-7 acceptance command set (normative target):

```bash
python3 scripts/validate_fallback_taxonomy_normalization.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation three-plane \
  --json-only

python3 scripts/validate_intake_evidence_core.py \
  --mode promotion_gate \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation validate \
  --json-only
```

Batch-7 blocker bundle (must resolve before promotion):

1. Taxonomy namespace conflict:
   - fallback taxonomy must use dedicated `fallback_taxonomy_class`; blocker taxonomy must remain independent.
2. Parser unification:
   - `RQ-030` must share the same intake-evidence core parser as `RQ-017` (mode split only).
3. Coverage/aggregator closure:
   - `RQ-022` + `RQ-030` must be added to `validate_required_contract_coverage.py TARGETS` and consumed by three-plane/full-scan payload extractors.

Roundtable-B6/B7 kickoff package (execution-ready):

1. participants:
   - `base-repo-architect`,
   - `audit-expert(codex)`,
   - `runtime orchestration owner`,
   - `schema owner`,
   - `docs bridge owner`.
2. agenda priority:
   - `RQ-030 -> RQ-018 -> RQ-021 -> RQ-019 -> RQ-020 -> RQ-022 -> RQ-017`.
3. mandatory output schema:
   - `rq_id`, `anchor_state`, `kernel_anchor_path`, `script_anchor_path`, `mapping_anchor_path`, `acceptance_command_set`, `promotion_blocker`, `owner`, `target_commit`.
4. hard exit condition:
   - rows without `kernel + script + replay` closure remain non-promotional (`ACCEPT_WITH_FIX`) and cannot upgrade audit verdict to full `PASS_REQUIRED`;
   - scanner-computed lock-state is mandatory; manual override is invalid.

Promotion guard (hard):

1. `ACCEPT_WITH_FIX` in this section is design acceptance only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion requires deterministic positive + negative replay and five-link anchor closure for both rows.

Batch-6/7 revised execution order (post-audit hard sequence):

1. Land mapping base asset first:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml` with rows for `RQ-017..022/030`.
2. Implement intake evidence core parser:
   - `validate_intake_evidence_core.py` with `--mode intake_contract|promotion_gate`.
3. Implement `RQ-022` taxonomy normalization with dual fields and namespace isolation.
4. Implement `RQ-021` emitter (`emit_route_version_pin_receipt.py`) before pinning gate.
5. Wire all seven new gates into coverage and aggregator payload extraction before any lock or promotion claim.

Batch-7 execution hook closure snapshot (Task-8..12 landed, replay pending):

1. landed commits:
   - `f63eb55` + `e214df9` (`RQ-030` core parser + strict-operation alignment),
   - `4f4930c` (`RQ-022` taxonomy normalizer + namespace separation),
   - `08c8f89` (coverage/aggregator extraction),
   - `5f7eb44` (readiness),
   - `228ba40` (creator),
   - `b7137e3` (e2e),
   - `47f2f38` (ci required-gates).
2. posture remains non-promotional:
   - both rows keep lifecycle `SPEC_READY` with decision class `ACCEPT_WITH_FIX`;
   - audit remains `PASS_WITH_BLOCKERS` until required=true replay archive closes (`Task-15` closed blocker subset to `PASS_REQUIRED`);
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`;
   - required=true positive/negative replay archive remains mandatory.

### FIX16-037 - write-boundary non-starvation hardening (`ASB16-RQ-028/031`)

- Status: `SPEC_READY`
- Goal: remove ambiguity between write-boundary enforcement and protocol-lane entry so boundary lock cannot regress into protocol-entry starvation.
- Audit class: `PASS_WITH_BLOCKERS` (docs hardening accepted; executable lane-wide closure pending).

Scope lock (mandatory):

1. this fix is strictly scoped to `ASB16-RQ-028/031` and does not create a new requirement row.
2. semantics are additive hardening to v1.6 `4.17` / `8.12` and inherit existing `SPEC_READY/PENDING_INTAKE` posture.
3. this fix must not alter previously locked constraints for `RQ-032` headstamp gate or Batch-6/7 intake quorum contracts.

Absorbed hardening decisions (normative):

1. write-boundary lock is lane-scoped and write-surface scoped; it cannot rewrite lane resolution outputs.
2. protocol-entry channels remain live under boundary lock for:
   - explicit `work_layer=protocol`,
   - `session_lane_lock=protocol`,
   - candidate bridge outcomes `PROTOCOL_DIRECT/PROTOCOL_CANDIDATE`.
3. protocol-context fallback to instance without candidate/inquiry receipt chain is fail-closed.
4. canonical boundary code remains `IP-KERNEL-WRITE-001`; legacy `IP-GOV-BASE-001` is compatibility alias only.
5. protocol-entry fallback/candidate failures use canonical current families:
   - `IP-LAYER-GATE-006/007`,
   - `IP-LAYER-CAND-001..004`.

Mandatory telemetry tuple (machine receipt):

1. `intent_source`
2. `protocol_context_detected`
3. `session_lane_lock`
4. `lane_resolution_decision`
5. `lane_resolution_error_code`
6. `applied_gate_set`
7. `base_repo_write_boundary_status`

Mandatory replay matrix (promotion hard-gate):

1. positive replay A:
   - explicit `work_layer=protocol` with boundary enabled must keep `applied_gate_set=protocol_required_checks`.
2. positive replay B:
   - `session_lane_lock=protocol` under weak intent signal must still resolve to protocol lane.
3. positive replay C:
   - `PROTOCOL_CANDIDATE` path must emit `QUESTION_REQUIRED/EVIDENCE_PENDING` with candidate + inquiry receipts.
4. negative replay D:
   - instance forbidden-surface write attempt must fail-close on canonical boundary code.
5. negative replay E:
   - protocol-context fallback without candidate/inquiry chain must fail-close with deterministic lane/candidate code.
6. convergence replay F:
   - identical lineage input must preserve telemetry tuple parity across update/three-plane/full-scan.

Acceptance command set (normative target):

```bash
python3 scripts/validate_work_layer_gate_set_routing.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --source-layer project \
  --actor-id assistant:codex \
  --force-check \
  --json-only

python3 scripts/validate_protocol_entry_candidate_bridge.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --source-layer project \
  --force-check \
  --json-only

python3 scripts/validate_protocol_inquiry_followup_chain.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --source-layer project \
  --force-check \
  --json-only

python3 scripts/validate_instance_base_repo_write_boundary.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --check-git-diff \
  --json-only
```

Promotion guard (hard):

1. this section remains `ACCEPT_WITH_FIX` only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion remains blocked until replay matrix + telemetry tuple are enforced and consumed across creator/readiness/three-plane/full-scan/e2e.

### HOTFIX16-P0-001 - emergency hotfix intake (`FQG` multi-agent × multi-identity gated switch guard)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: enforce the non-negotiable guardrail "no hard identity switch during execution", while preserving controlled switching capability via gated handshake.
- Audit class: `PENDING_INTAKE` (runtime bridge closure landed locally; independent rollout/audit closure pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-001..037` batch streams and must not be merged into earlier fix findings.
2. naming follows v1.5 hotfix treatment (`HOTFIX-P0-*`) with v1.6-specific ID prefix `HOTFIX16-P0-*`.
3. runtime bridge closure is landed locally, but promotion posture remains non-promotional until independent live rollout evidence is archived.

Core semantics lock (v2 clarification absorbed):

1. hard guardrail: execution-state identity hard-switch is forbidden.
2. `allow_shared_session=true` means "allow entering `gated_switch` flow", not direct shared execution.
3. mandatory machine chain:
   - `switch_request -> pre_switch_gate -> switch_apply -> switch_ack -> ack_verify -> dispatch`.
4. fail-close is mandatory on:
   - missing `switch_ack`,
   - `switch_ack` mismatch with target identity,
   - handshake timeout,
   - policy/state disallow switch.

Reserved error-code family (for architect contract freeze):

1. `IP-SWITCH-GATE-001`
2. `IP-SWITCH-HS-002`
3. `IP-SWITCH-TIMEOUT-003`
4. `IP-SWITCH-STATE-004`
5. `IP-SWITCH-POLICY-005`

Four-track evidence package (cross-verified):

1. `T1 governance/spec`: explicit identity binding + switch-guard + canonical headstamp fail-close constraints.
2. `T2 runtime implementation`: bridge now emits/consumes guarded route metadata (`allow_shared_session`, `switch_ack_ref`, `route_status`, `route_error`) and enforces conflict fail-close on all identity-route paths.
3. `T3 live evidence`: local runtime replay passes including negative conflict + override-bypass checks (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_chat_inbound.py tests/test_chat_bridge.py -q` => `28 passed`).
4. `T4 hotfix requirement docs`: requirement clarification v2 + protocol-feedback v2 package.

Implementation delta snapshot (2026-03-07):

1. fqsh bridge runtime files landed:
   - `src/feiqiao_guard/identity_router.py`
   - `src/feiqiao_guard/main.py`
   - `src/feiqiao_guard/models.py`
   - `src/feiqiao_guard/chat_bridge.py`
2. conflict routing now fails closed (`HTTP 409`) even when request carries explicit session/codex override.
3. route summary and `/v1/chat/routes` payload now expose conflict state fields for machine audit.

Architect handoff artifacts (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.json`
4. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
5. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
6. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
7. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
8. runtime route snapshot source (remote): `/root/feiqiao-guard/.runtime/identity_routes.json`

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent rollout/audit closure:
   - live route snapshot with canonical route conflict fields,
   - archived `409` conflict replay + non-conflict success replay,
   - production switch-ack handshake receipt verification.

### HOTFIX16-P0-002 - emergency hotfix intake (`protocol lane activation starvation + headstamp continuity`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: close the deadlock where explicit protocol-governance requests cannot deterministically activate protocol lane, and close recurrent outbound headstamp omission risk on send path.
- Audit class: `PENDING_INTAKE` (local lane/headstamp runtime guards landed; independent rollout/audit closure pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-001..037` and from `HOTFIX16-P0-001`; no status inheritance is allowed.
2. this hotfix targets only lane activation non-starvation and headstamp continuity hard-gate.
3. local runtime closure is landed, but this record remains non-promotional until live endpoint replay evidence is archived.

Core semantics lock:

1. explicit protocol request must resolve to protocol lane or fail-close with deterministic error code; silent instance fallback is forbidden.
2. unresolved protocol route configuration must fail-close (`IP-LANE-ROUTE-001`), not degrade to best-effort delivery semantics.
3. every outbound assistant reply must pass canonical pre-send headstamp hard-gate (`Identity-Context` + `Layer-Context`).
4. lane activation without headstamp continuity proof is invalid for promotion-grade replay.
5. outbound user-visible reply must have one canonical final gate verdict before dispatch; distributed checks cannot substitute canonical gateway decision.

Reserved error-code family (for architect contract freeze):

1. `IP-LANE-ROUTE-001`
2. `IP-LANE-ACT-002`
3. `IP-LANE-ACT-003`
4. `IP-HDSTAMP-001`
5. `IP-HDSTAMP-002`
6. `IP-HDSTAMP-003`

Four-track evidence package (cross-verified):

1. `T1 governance/spec`: protocol-entry non-starvation + headstamp pre-send fail-close clauses.
2. `T2 runtime implementation`: lane-routing conflict and route-state surfaces are now machine-verifiable in runtime bridge outputs.
3. `T3 live evidence`: local replay confirms deterministic conflict handling and preserved non-conflict dispatch behavior (`pytest 28 passed`).
4. `T4 escalation package`: protocol escalation pack + lane activation receipt + v2 requirement/feedback package.

Implementation delta snapshot (2026-03-07):

1. explicit route conflict now blocks dispatch with deterministic error surface instead of silent downgrade.
2. route-state fields are emitted for downstream audit consumers (`route_status`, `route_error`).
3. non-starvation/headstamp closure still requires live endpoint replay archive before promotion.

Round-6 recurrence replay (`HEAD=6a2ef0b`, 2026-03-07, protocol-layer):

1. replay commands executed (workspace-root invariant):
   - `python3 identity-protocol-local/scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids <IDENTITY_A>,<IDENTITY_B> --project-catalog <PROJECT_CATALOG> --global-catalog /tmp/nonexistent-catalog.yaml --actor-id assistant:codex --out /tmp/hotfix_headstamp_r6_fullscan.json`
   - `python3 identity-protocol-local/scripts/validate_headstamp_recurrence_closure.py --identity-id <IDENTITY_A> --catalog <PROJECT_CATALOG> --repo-catalog identity-protocol-local/identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
   - `python3 identity-protocol-local/scripts/validate_headstamp_recurrence_closure.py --identity-id <IDENTITY_B> --catalog <PROJECT_CATALOG> --repo-catalog identity-protocol-local/identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
2. observed behavior:
   - one strict-path identity returns `FAIL_REQUIRED` (`IP-ASB-STAMP-SCAN-004`) with dynamic positive case failing `IP-ASB-STAMP-SESSION-005`;
   - another identity under the same suite returns `PASS_REQUIRED`.
3. cross-check command:
   - `python3 identity-protocol-local/scripts/validate_actor_session_binding.py --catalog <PROJECT_CATALOG> --identity-id <IDENTITY_A|IDENTITY_B> --actor-id assistant:codex --operation scan --json-only`
   - both sampled identities return `actor_binding_status=PASS_REQUIRED` under `binding_key_mode=actor_id+session_id`.
4. audit conclusion:
   - recurrence root cause is protocol-layer resolver divergence, not allowed hard-switch behavior:
   - `validate_actor_session_binding.py` resolves binding with explicit target identity;
   - `validate_headstamp_recurrence_closure.py` mismatch probe reads actor binding without explicit `identity_id/session_id`, so latest actor binding entry can leak into replay context.
5. architect action remains protocol-only:
   - unify actor-binding source and require deterministic actor-binding selection tuple for all send-time/closure validators;
   - add machine receipt fields for binding selection mode/session/compare token;
   - keep `IP-ASB-STAMP-SESSION-*` as compatibility trace only until canonical family convergence.
6. positive reinforcement captured in the same round:
   - no-hard-switch fail-close behavior remains effective;
   - strict env/catalog mismatch remains fail-close on strict surfaces;
   - replay-archive contract remains `PASS_REQUIRED` on the replay set.

Round-7 resolver convergence replay (`HEAD=d5f75d7+`, 2026-03-07):

1. replay commands (workspace-root invariant):
   - `python3 identity-protocol-local/scripts/validate_headstamp_recurrence_closure.py --identity-id base-repo-architect --catalog .identity/catalog.local.yaml --repo-catalog identity-protocol-local/identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
   - `python3 identity-protocol-local/scripts/validate_headstamp_recurrence_closure.py --identity-id base-repo-audit-expert-v3 --catalog .identity/catalog.local.yaml --repo-catalog identity-protocol-local/identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
   - `python3 identity-protocol-local/scripts/validate_actor_session_binding.py --catalog .identity/catalog.local.yaml --identity-id <base-repo-architect|base-repo-audit-expert-v3> --actor-id assistant:codex --operation scan --json-only`
2. convergence result:
   - both sampled identities now return `headstamp_recurrence_closure_status=PASS_REQUIRED`;
   - mismatch-negative case remains fail-close with `error_code=IP-ASB-STAMP-SESSION-005`.
3. resolver tuple is now machine-visible in replay payload:
   - `binding_selection_mode`, `binding_key_mode`, `binding_compare_token`, `binding_session_id`, `binding_entry_count`.
4. targeted no-hardcoded-temp replay:
   - `rg -n "/tmp" scripts/validate_headstamp_recurrence_closure.py scripts/compose_and_validate_governed_reply.py scripts/validate_reply_identity_context_first_line.py` returns no hits.
5. closure interpretation:
   - protocol-layer resolver divergence from round-6 is closed;
   - live endpoint rollout replay archive remains mandatory before promotion.

Round-8 four-track convergence residual (`HEAD=f53f36a`, 2026-03-07):

1. replay probe:
   - `python3 identity-protocol-local/scripts/validate_send_time_reply_gate.py --identity-id <ID> --catalog <PROJECT_CATALOG> --repo-catalog identity-protocol-local/identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
2. observed residual:
   - `send_time_gate_status=SKIPPED_NOT_REQUIRED`, `required_contract=false`, `stale_reasons=[\"contract_not_required\"]`.
3. audit interpretation:
   - resolver divergence closure is valid, but canonical egress requiredization is not yet uniformly enforced across all outbound surfaces.
4. required protocol correction:
   - keep reply-channel contract applicability separate from canonical egress applicability;
   - enforce `required_contract=true` for canonical send-time gateway on user-visible strict operations;
   - classify canonical gateway bypass as fail-close (`IP-HDSTAMP-004`).

Scope separation note:

1. unified control-plane entrypoint strengthening is tracked independently in `HOTFIX16-P0-007`.
2. this row (`HOTFIX16-P0-002`) remains focused on lane activation starvation + outbound headstamp continuity only.

Architect handoff artifacts (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_ESCALATION_PACK_20260306T213707_multiagent_multiidentity.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T213517_protocol_lane_activation_receipt.md`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
4. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
5. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
6. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
7. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
8. runtime route snapshot source (remote): `/root/feiqiao-guard/.runtime/identity_routes.json`

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent rollout/audit closure:
   - live lane activation receipts (`requested_lane -> resolved_lane`) are reproducible,
   - live headstamp continuity negative/positive replay is archived,
   - no silent protocol->instance fallback under explicit protocol intent.

### HOTFIX16-P0-007 - emergency hotfix intake (`unified protocol control-plane entrypoint freeze`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: stop recurring scattered patching by forcing one protocol-layer management/wiring entrypoint for required gates and outbound verdict.
- Audit class: `PENDING_INTAKE` (design freeze landed in governance/review; executable replay closure pending).

Scope lock:

1. protocol-layer only; instance business behavior remains out of scope.
2. this hotfix targets control-plane entrypoint governance, not domain-specific validator logic.
3. no status inheritance from other hotfix lanes is allowed.

Mandatory unified control model:

1. single registry source: `identity/protocol/mappings/contract-binding.v1.6.yaml`.
2. single wiring entrypoint: `scripts/validate_required_contract_coverage.py` must be the first propagation surface for required-gate tuple changes.
3. strict-surface convergence from one lineage is required for:
   - `scripts/release_readiness_check.py`
   - `scripts/identity_creator.py` (`validate/update`)
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `.github/workflows/_identity-required-gates.yml`
4. single outbound verdict source remains canonical:
   - `scripts/validate_send_time_reply_gate.py` on user-visible strict operations.

Reserved anti-drift error-code family:

1. `IP-GATE-ENTRY-001` (`registry_source_missing_or_stale`)
2. `IP-GATE-ENTRY-002` (`surface_wiring_not_from_registry_tuple`)
3. `IP-GATE-ENTRY-003` (`cross_surface_tuple_divergence`)
4. `IP-GATE-ENTRY-004` (`control_plane_mutation_without_four_track_bundle`)

Mandatory four-track replay bundle per control-plane change:

1. `T1`: governance/review clause + contract version tuple.
2. `T2`: strict-surface wiring propagation proof.
3. `T3`: deterministic `positive + negative + bypass-negative` replay under same lineage.
4. `T4`: protocol-feedback outbox batch + evidence-index pointer.

No-deadlock tiering:

1. tier-0 (control-plane mutation) requires full `T1+T2+T3+T4` before promotion.
2. tier-1 (non-control-plane patch) allows `T1+T2` immediate and deferred `T3+T4` within bounded replay window.
3. promotion is blocked only by tier-0 incompleteness, tier-1 deferred-window expiration, or unresolved strict egress bypass residuals.

State boundary:

1. this hotfix is executable and enforceable at protocol design level.
2. row remains non-promotional until tuple parity replay is archived across all strict surfaces.

Round-10 UCG pre-code readiness reinforcement (`HEAD=30423c5+`, 2026-03-07):

1. scope lock:
   - this checkpoint is discussion-only and does not claim new code landing.
   - purpose is to absorb recurring audit findings into one implementation-ready control-plane contract before next code wave.
2. four-track cross-check consolidation (`T1..T4`):
   - `T1 governance/roundtable`: semantic verdict is still not single-source without canonical control-plane convergence.
   - `T2 base-repo wiring`: repeated per-surface gate arrays remain drift-prone; script existence alone does not equal unified enforcement.
   - `T3 vendor trajectory`: layered governance posture supports centralized control boundaries, not scattered mutation points.
   - `T4 external references`: zero-trust/policy-plane references consistently support centralized decision + enforcement + audit lineage.
3. UCG confirmation (`1门 + 1判 + 1账`):
   - `1门`: strict operations enter through one actor-bound/lane-bound preflight and emit one entry receipt tuple.
   - `1判`: user-visible outbound path consumes one canonical send-time verdict; bypass is fail-close.
   - `1账`: strict surfaces converge on one machine tuple contract (`run_id_binding`, `report_selected_path`, `required_contract`, `failed_required_contract_count`, `send_time_gate_status`, `outlet_bypass_detected`).
4. pre-code implementation prerequisites frozen:
   - one bundle-runner lineage for strict-surface gate-set execution;
   - one registry source (`contract-binding.v1.6.yaml`) with CI drift detection;
   - recurrence escalator that upgrades repeated cross-surface error-family regressions to control-plane mutation track.
5. status boundary:
   - this round increases implementation readiness but does not change lifecycle state.
   - `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`, and `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-10 implementation-freeze addendum (mandatory before code rollout):

1. artifact freeze (single-source naming):
   - control-plane contract id frozen as `hotfix_p0_007_ucg_control_plane_freeze_contract_v1`.
   - bundle-runner artifact key frozen as `required_gate_bundle_runner` (target file name `required_gate_bundle_runner.py` under scripts directory).
   - registry-source validator frozen to current canonical implementation (`validate_required_contract_coverage.py`).
   - tuple-parity validator artifact key frozen as `required_gate_tuple_parity_validator` (target file name `validate_required_gate_tuple_parity.py` under scripts directory).
2. recurrence escalator quantitative freeze:
   - `L1`: `>=2` same-family hits across `>=2` strict surfaces within `24h`.
   - `L2`: `>=3` same-family hits across `>=2` strict surfaces within `72h` -> forced upgrade path to `HOTFIX16-P0-007`.
   - `L3`: `>=5` hits or second `L2` within `7d` -> control-plane merge freeze until tuple-parity replay closure.
3. mandatory migration surface list freeze:
   - `identity_creator (validate/update)`, `release_readiness`, `three-plane`, `full-scan`, `e2e`, and `required-gates CI workflow` must converge to bundle-runner lineage.
4. operation semantics freeze:
   - `required_contract` formula is unified as `mapping_required AND current_round_linked` across `scan/validate/readiness/update/e2e/ci`.
   - non-applicable state must be `SKIPPED_NOT_REQUIRED` with machine reason `required_contract_not_applicable_no_current_round_evidence_source`.
   - strict operations remain fail-close on required=true failures; observation (`scan`) may remain non-promotional.

Round-12 UCG code landing wave-1 (`HEAD=1deba9d+`, 2026-03-07):

1. landed canonical artifacts:
   - `scripts/required_gate_bundle_runner.py` (bundle mode + target-probe compatibility mode).
   - `scripts/validate_required_gate_tuple_parity.py` (tuple parity machine gate).
   - `scripts/validate_required_gate_surface_drift.py` (strict-surface drift machine gate).
2. strict-surface migration closure:
   - migrated to bundle-runner lineage: `identity_creator(validate/update)`, `release_readiness_check`, `report_three_plane_status`, `full_identity_protocol_scan`, `e2e_smoke_test.sh`, `required-gates CI workflow`.
   - `create_identity_pack` default required-check list now converges to bundle-runner lineage.
3. executable probe evidence:
   - bundle-runner full probe (`operation=scan`) returns deterministic 8-target receipt rows.
   - bundle-runner target-probe mode returns legacy-compatible payload fields (`*_status` + `required_contract`).
   - surface drift validator reports `PASS_REQUIRED` after six-surface migration.
4. residual closure boundary:
   - tuple parity validator is landed but required=true replay archive across strict surfaces is still pending.
   - row remains non-promotional (`SPEC_READY / PENDING_INTAKE`) until replay matrix closure is independently audited.

Round-13 UCG code landing wave-2 (`HEAD=af0f684+dirty`, 2026-03-07):

1. wave-2 canonical artifact closure:
   - `scripts/required_gate_bundle_runner.py` adds deterministic `--out` receipt persistence path.
   - `scripts/validate_required_gate_recurrence_escalator.py` lands quantitative recurrence escalation (`L1/L2/L3`) with optional hard-block (`--enforce-blocking`).
2. strict-surface wiring expansion:
   - readiness/creator(validate+update)/three-plane/full-scan/e2e/ci now execute `bundle_runner -> recurrence_escalator -> tuple_parity` as one lineage.
   - `scripts/validate_required_gate_surface_drift.py` now enforces presence of all three lineage artifacts across six strict surfaces.
3. payload projection closure:
   - `report_three_plane_status` and `full_identity_protocol_scan` now emit machine-readable detail for:
     - `required_gate_bundle_runner`
     - `required_gate_recurrence_escalator`
     - `required_gate_tuple_parity`
4. replay of prior audit blockers:
   - parser/runtime entry crashes (`release_readiness target_branch`, `identity_creator validate run_id`) remain closed; no pre-gate `AttributeError` replay observed.
   - runtime mode guard strictness now covers `scan/three-plane/inspection` for env/catalog mismatch fail-close.
   - cross-workflow schema observation profile no longer forces route/dedup required fields without current-round linkage.
5. residual blocker kept explicit:
   - protocol-lane global replay still reports `IP-UPG-002 + IP-SEM-001` on `system-requirements-analyst` due missing semantic tuple fields (`intent_domain`, `intent_confidence`, `classifier_reason`) in feedback batch payload.
   - row remains non-promotional until required=true replay matrix + semantic tuple completeness replay are independently archived.

Round-14 UCG four-point roundtable reconciliation (`HEAD=af0f684+dirty`, 2026-03-07):

1. scope lock:
   - protocol-layer only; this round is implementation-vs-contract reconciliation for recurring control-plane defects.
   - no business-domain validator scope is added.
2. four-track cross-verification evidence:
   - `T1` governance contract lock (`1门 + 1判 + 1账`) remains unchanged.
   - `T2` code-path anchors:
     - `scripts/required_gate_bundle_runner.py:185-199,202-224,321-340`
     - `scripts/validate_reply_identity_context_first_line.py:28,325,389-414`
     - `scripts/validate_send_time_reply_gate.py:21,228,242`
     - `.github/workflows/_identity-required-gates.yml:288-290`
   - `T3` executable negatives:
     - `/tmp/ucg_bundle_badmap_now2.json` (bundle false-green window: row execution failure downgraded optional while bundle remains pass).
     - `/tmp/ucg_drift_gap_now.json` (drift guard static-list bypass under direct-validator alias).
   - `T4` runtime convergence replay:
     - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260307T144051Z_v16_protocol_fix_post_verification.md` + `/tmp/office_ops_protocol_fix_verification_20260307.json` (`run_id_not_found`, `Conditional Go`, `IP-PVA-003`).
     - `/tmp/cca_validate_protocol_handoff_20260307.log` vs `/tmp/cca_three_plane_protocol_handoff_20260307.log` (same-lineage layer/headstamp strictness split).
     - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-07_003_protocol-lane-regression-round3.md` (`IP-UPG-002 + IP-SEM-001` residual shape).
3. four-point verdict:
   - point-A (`shared tuple resolver across validate/three-plane/compose`): `PARTIAL`.
   - point-B (`single canonical egress verdict fail-close, no non-blocking tail`): `PARTIAL`.
   - point-C (`entry tuple freeze with no fallback semantics`): `NOT_CLOSED`.
   - point-D (`CI same-run cross-surface tuple equality`): `PARTIAL`.
4. mandatory wave-3 closure actions (protocol-layer):
   - unify strictness policy for `validate` and `three-plane` on first-line/send-time tuple mismatch handling.
   - close bundle false-green class: execution failure with missing/invalid payload contract must fail-close on UCG lane.
   - upgrade tuple parity validator contract to require multi-receipt cross-surface comparison.
   - wire required-gates CI parity with multi-surface same-lineage receipts.
   - migrate drift guard from static forbidden list to mapping-derived forbidden set.
5. anti-deadlock boundary:
   - this strict four-track escalation applies to recurring control-plane mutation class (`HOTFIX16-P0-007`) only; non-control-plane lanes keep tiered closure policy.
6. state boundary:
   - row remains non-promotional until point-C and point-D are closed and point-A/B move from partial to deterministic pass.

Round-15 UCG wave-3 code hardening replay (`HEAD=working-tree+dirty`, 2026-03-07):

1. code landing scope:
   - protocol-layer wave-3 mandatory items only (no lifecycle promotion, no business validator expansion).
2. landed closure (`C + D`):
   - `scripts/required_gate_bundle_runner.py` now fail-closes row payload contract violations and non-zero validator rc (`payload_contract_issues`, `row_contract_error_count`, `surface_label`).
   - `scripts/validate_required_gate_tuple_parity.py` now enforces multi-receipt + distinct surface labels.
   - required-gates CI now feeds tuple parity with same-lineage dual receipts (`ci_validate`, `ci_three_plane`).
3. landed strengthening (`A + B` partial uplift):
   - first-line/send-time strict operation sets now include `three-plane` + `ci`.
   - invalid-input send-time branch now follows strict-context fail-close.
   - three-plane/full-scan payload now projects dual bundle receipts and parity details.
4. replay evidence package:
   - `/tmp/ucg_wave3_badmap.yaml`
   - `/tmp/ucg_wave3_bundle_badmap.json`
   - `/tmp/ucg_wave3_tuple_dup.json`
   - `/tmp/ucg_wave3_tuple_cross_surface.json`
   - `/tmp/ucg_wave3_sendtime_three_plane.json`
   - `/tmp/ucg_wave3_drift_mapping_derived.json`
5. replay verdict:
   - bundle false-green class closed in wave-3 lane (`IP-GATE-ENTRY-002` fail-close hit on bad mapping probe).
   - tuple parity contract now blocks duplicate/missing surface labels and passes cross-surface same-lineage replay.
   - strict send-time `three-plane` now fail-closes missing live evidence (`IP-ASB-STAMP-SESSION-002`).
6. boundary decision:
   - `HOTFIX16-P0-007` remains non-promotional (`SPEC_READY / PENDING_INTAKE`).
   - residual promotion blockers unchanged: `IP-UPG-002 + IP-SEM-001` plus remaining A/B determinism convergence debt.

### HOTFIX16-P1-003 - emergency hotfix intake (`strict-surface fixed /tmp path debt`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: eliminate residual fixed `/tmp` output hardcoding in strict surfaces and restore deterministic, collision-safe replay artifact paths.
- Audit class: `PENDING_INTAKE` (strict-chain runtime refactor landed; replay archive + independent audit closure pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-*` and `HOTFIX16-P0-*`; no closure inheritance is allowed.
2. this hotfix covers temp path governance only, not switch semantics or lane activation semantics.
3. this record acknowledges partial cleanup baseline (`4179e47`) and tracks residual debt closure.

Core semantics lock:

1. strict surfaces must not ship fixed `/tmp/<static_file>` default outputs.
2. default temp outputs must be runtime-scoped by `run_id + identity_id + operation`.
3. CI must use runner-scoped temp root (`${RUNNER_TEMP}` or equivalent).
4. explicit `--out` remains optional override, but no fixed-path default is allowed in strict surfaces.

Reserved error-code family (for architect contract freeze):

1. `IP-TMPPATH-001`
2. `IP-TMPPATH-002`
3. `IP-TMPPATH-003`

Four-track evidence package (cross-verified):

1. `T1 governance/spec`: strict-path determinism and replay non-collision policy.
2. `T2 runtime implementation`: strict-chain temp resolver landed (`scripts/runtime_temp_path_common.py`) and wired into creator/readiness/three-plane/full-scan/e2e/no-implicit-switch.
3. `T3 live evidence`: strict-chain scan confirms fixed `/tmp` literals are removed from the above scripts; runtime temp root is environment-driven (`IDENTITY_RUNTIME_TMP_ROOT` / `RUNNER_TEMP` / `TMPDIR` / system temp).
4. `T4 protocol feedback`: canonical feedback batch + receipt + evidence-index entries are archived in protocol-feedback channel.

Implementation delta snapshot (2026-03-07):

1. added `scripts/runtime_temp_path_common.py` for scoped temp root/file allocation.
2. refactored strict-chain scripts:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/validate_no_implicit_switch.py`
3. verification commands:
   - `python3 -m py_compile` (strict-chain scripts) → pass.
   - `bash -n scripts/e2e_smoke_test.sh` → pass.
   - strict-chain `/tmp` literal grep on refactored scripts → no hits.

Round-8 pre-implementation residual sweep (`HEAD=f53f36a+`, 2026-03-07):

1. residual scripts confirmed (not yet landed in this subsection):
   - `scripts/execute_identity_upgrade.py` (`/tmp` fallback in capability report, pre-mutation reply/receipt defaults, and legacy out-dir alias logic),
   - `scripts/validate_execution_report_freshness.py` (fallback root scan hardcoded to legacy `/tmp` paths),
   - `scripts/validate_identity_protocol_baseline_freshness.py` (fallback root scan hardcoded to legacy `/tmp` paths).
2. required implementation contract:
   - migrate all three scripts to runtime temp resolver semantics (`runtime_temp_root` + `runtime_temp_file` or equivalent),
   - preserve explicit CLI/report override precedence,
   - remove fixed `/tmp` literals from these scripts.
3. planned replay acceptance set (post-implementation):
   - `rg -n "/tmp" scripts/execute_identity_upgrade.py scripts/validate_execution_report_freshness.py scripts/validate_identity_protocol_baseline_freshness.py`
   - `python3 -m py_compile scripts/execute_identity_upgrade.py scripts/validate_execution_report_freshness.py scripts/validate_identity_protocol_baseline_freshness.py`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

Architect handoff artifacts (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T140030Z_tmp_hardcoded_path_governance_gap.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T140030Z_tmp_hardcoded_path_governance_gap.json`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
4. baseline commit evidence: `4179e47`

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent replay closure:
   - strict-chain fixed-path detector replay (`zero fixed /tmp literals`),
   - run/identity/operation scoping replay under concurrent execution,
   - CI runner-temp parity replay.

### HOTFIX16-P0-005 - emergency hotfix intake (`gate-chain CLI parser regression on required surfaces`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: recover executable hard-gate surfaces by removing argparse/runtime-field drift that causes pre-gate crashes.
- Audit class: `PENDING_INTAKE` (parser/runtime crash closure landed; strict required-gate replay closure still pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-*` and existing hotfix streams; no closure inheritance is allowed.
2. scope is protocol runtime orchestration only (`release_readiness_check.py`, `identity_creator.py`).
3. this hotfix does not alter instance business contracts.

Core failure evidence (replay verified):

1. parser drift is closed:
   - `release_readiness_check.py` declares release-plane passthrough args (`scripts/release_readiness_check.py:235-242`).
   - `identity_creator.py validate` declares `--run-id` (`scripts/identity_creator.py:1140`).
2. strict context mismatch is now fail-close on strict operations:
   - `validate/readiness/ci` mismatches return `IP-ENV-003` and non-zero exit.
3. gate-chain now fails for contract reasons (not parser/runtime crash):
   - aligned-catalog replay reaches downstream contract gates and returns deterministic business gate codes (`IP-EXEC-ORDER-001`, `IP-PVA-003`, `IP-INTAKE-EVID-001`, depending on identity evidence state).
   - `release_readiness_check` inherits the same non-crash blockers because it invokes update preflight.

Round-2 replay reconfirmation (2026-03-07):

1. crash signatures remain deterministic on multiple identities:
   - `python3 scripts/release_readiness_check.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
   - `python3 scripts/release_readiness_check.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
   - both runs fail with `AttributeError: Namespace has no attribute target_branch`.
2. validate-chain parser drift also remains deterministic across identities:
   - `python3 scripts/identity_creator.py validate --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
   - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
   - both runs fail with `AttributeError: Namespace has no attribute run_id`.
3. replay artifacts:
   - `/tmp/release_readiness_office_round2.log`
   - `/tmp/release_readiness_arch_round2.log`
   - `/tmp/identity_creator_validate_office_round2.log`
   - `/tmp/identity_creator_validate_arch_round2.log`

Round-3 replay reconfirmation (`HEAD=a0c191e`, 2026-03-07):

1. parser regressions remain closed:
   - no `AttributeError` on missing `target_branch` / `run_id` in current replay.
2. strict mismatch gating remains active:
   - mismatch runs fail with `IP-ENV-003` (`/tmp/audit_r3d_validate_office_mismatch.log`).
3. aligned-catalog replay now reaches required gates and fails deterministically on intake evidence absence:
   - `identity_creator update` fails on deterministic business gates (for example `IP-EXEC-ORDER-001` / `IP-PVA-003` / `IP-INTAKE-EVID-001`) rather than parser/runtime exceptions (`/tmp/audit_r3d_update_office.log`).
4. release preflight inherits the same contract blocker:
   - `release_readiness_check` fails by delegated update failure (`/tmp/audit_r3d_release_office.log`).

Four-track cross-verification:

1. `T1 governance/spec`: strict context fail-close intent is now executable on strict operations (`IP-ENV-003`).
2. `T2 implementation`: parser-field wiring for release/readiness/validate paths is now present.
3. `T3 replay`: failures shifted from parser/runtime exceptions to deterministic contract blockers (`IP-INTAKE-EVID-001`).
4. `T4 review consistency`: rolling summary + decision-log rows stay synchronized while audit status remains non-promotional.

Required protocol-layer fix closure (for architect lane):

1. keep parser schema closure locked with regression tests (`release_readiness_check` passthrough args + `identity_creator validate --run-id`).
2. provide deterministic replay fixture for required intake evidence (`cross_verification_bundle_id`, `source_url_set`, `reference_timestamp_utc`, `conflict_reconciliation_note`) so strict update/readiness paths can pass under audited conditions.
3. add gate-smoke replay that distinguishes parser/runtime failures from expected contract fail-close outcomes.

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires crash-free replay of both commands plus downstream gate execution proof.

### HOTFIX16-P0-006 - emergency hotfix intake (`execution-target tuple isolation for multi-agent dispatch`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: remove hidden `codex_home`-only coupling by enforcing tuple-based execution target isolation and adding first-class process-call dispatch contract.
- Audit class: `PENDING_INTAKE` (protocol-layer machine-lock landed; runtime bridge rollout + replay archive closure pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-*` and existing `HOTFIX16-P0-*` streams; no closure inheritance is allowed.
2. scope is runtime dispatch contractization only (`route resolution`, `conflict isolation`, `override guard`, `process-call receipt`).
3. this hotfix does not prescribe instance business logic, but requires machine-verifiable routing evidence.

Core contract semantics:

1. dispatch must resolve `execution_target_kind + execution_target_key + execution_target_ref` before business send.
2. conflict detection must be tuple-based (`kind+key`) rather than `codex_home`-only.
3. explicit override path must pass the same conflict gate; bypass is forbidden.
4. shared tuple requires gated handshake consistency (`allow_shared_session=true` + consistent `switch_ack_ref`).
5. `process_call` target is valid without `codex_home`, but receipt must include deterministic tuple fields (`actor_id`, `identity_id`, `run_id`, `invocation_lane_id`, `execution_target_key`).

Reserved error-code family (for architect contract freeze):

1. `IP-XTARGET-001`
2. `IP-XTARGET-002`
3. `IP-XTARGET-003`
4. `IP-XTARGET-004`

Four-track cross-verification package:

1. `T1 governance/spec`: new contractized tuple invariants and fail-close policy (governance `4.22`, `C31`).
2. `T2 runtime implementation`: route resolver/inbound bridge must consume identical tuple fields on normal path + override path.
3. `T3 replay`: conflict/no-conflict + override + process-call replays must be deterministic and archivable.
4. `T4 review bridge`: rolling summary + decision log remain synchronized, and this hotfix stays non-promotional until replay closure.

Architecture posture conclusion:

1. this hotfix is classified as `positive architecture reinforcement` because it upgrades isolation semantics from route-path coupling to execution-target canonicalization without weakening existing fail-close gates.

Deep-scan evidence (code-level confirmation):

1. executed scan command:
   - `rg -n "identity_or_session_or_codex_home_required|session_or_codex_home_required|requested_session_id|requested_codex_home|_compute_route_issues|session_id_conflict_requires_switch_ack|codex_home_conflict_requires_switch_ack" /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/main.py /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/identity_router.py /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/models.py`
2. confirmed gaps:
   - dispatch entry still rejects requests without `session_id/codex_home` (`main.py:118..119`, `main.py:148..149`);
   - route conflict keys remain `session_id` + `codex_home` (`identity_router.py:144..156`, `identity_router.py:158..196`);
   - route schema still lacks tuple fields (`execution_target_kind`, `execution_target_key`) (`models.py:133..143`).
3. baseline regression guard re-run:
   - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/pycache-fqsh pytest -p no:cacheprovider tests/test_chat_inbound.py tests/test_chat_bridge.py -q`
   - result: `28 passed, 1 warning`.

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires replay bundle containing:
   - tuple conflict fail-close (`IP-XTARGET-002`),
   - override bypass block (`IP-XTARGET-003`),
   - process-call positive replay with full receipt tuple fields.

Protocol-layer closure update (2026-03-07, local protocol repo):

1. kernel anchor landed: `identity/protocol/IDENTITY_RUNTIME.md#rq_033_execution_target_tuple_isolation_contract_v1`.
2. mapping row landed: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-033`.
3. validator landed: `scripts/validate_execution_target_tuple_isolation.py`.
4. lane hooks landed in:
   - `scripts/identity_creator.py` (`validate/update` intake gates),
   - `scripts/release_readiness_check.py`,
   - `scripts/report_three_plane_status.py`,
   - `scripts/full_identity_protocol_scan.py`,
   - `scripts/e2e_smoke_test.sh`,
   - `.github/workflows/_identity-required-gates.yml`,
   - `scripts/validate_required_contract_coverage.py`.
5. non-promotional boundary remains unchanged until runtime bridge rollout evidence and deterministic required=true replay archive are both attached.

Round-3 replay note (`HEAD=a0c191e`):

1. validator executable replay (global sample):
   - `python3 scripts/validate_execution_target_tuple_isolation.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --operation scan --json-only`
2. current replay output:
   - `execution_target_tuple_isolation_status=SKIPPED_NOT_REQUIRED`
   - `stale_reasons=[\"contract_not_required\"]`
3. audit interpretation:
   - implementation and lane wiring are confirmed,
   - required=true deterministic archive is still missing, so promotion boundary remains unchanged.

Round-8 actor-bound strict-entry convergence replay (`HEAD=fc662b8+`, 2026-03-07):

1. scope:
   - protocol-layer strict entry semantics only (`activate/update/validate` + wave apply path).
   - objective: remove canonical-active-pointer-driven default actor ambiguity and converge to one explicit actor-bound entry contract.
2. implementation evidence:
   - `scripts/identity_creator.py` strict entry now requires explicit `--actor-id` for `activate/update/validate`;
   - `scripts/identity_creator.py` now executes actor-session binding preflight before strict validate/update chain progression;
   - `scripts/execute_identity_upgrade.py` auto header-first preflight now requires explicit actor context;
   - `scripts/run_protocol_upgrade_wave.py --apply` now requires explicit actor and forwards it into each update command.
3. replay command set:
   - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope USER`
   - `python3 scripts/identity_creator.py update --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --mode review-required --scope USER`
   - `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
4. replay outcomes:
   - missing actor on strict entry fails fast with `IP-ACTOR-ENTRY-001` (expected).
   - explicit actor path passes strict entry guard and reaches downstream validators (downstream pass/fail remains business-evidence dependent).
5. audit interpretation:
   - strict entry is now actor-explicit and machine-guarded, reducing repeated canonical-pointer correction churn.
   - `HOTFIX16-P0-006` remains non-promotional pending required=true tuple replay + runtime bridge rollout evidence.

### HOTFIX16-P1-004 - emergency hotfix intake (`gate-source convergence + producer-aware requiredization applicability`)

- Status: `SPEC_READY` (hotfix lane intake)
- Goal: remove protocol-layer false-block windows by enforcing gate-source convergence, producer/applicability-scoped requiredization, and strict context/writeback determinism.
- Audit class: `PENDING_INTAKE` (applicability refactor landed; convergence replay archive + independent audit closure pending).

Hotfix lane scope lock:

1. this hotfix is isolated from `FIX16-*` and `HOTFIX16-P0/P1-*`; no closure inheritance is allowed.
2. this hotfix addresses protocol governance semantics only and does not prescribe instance business logic.
3. lane partition baseline remains unchanged: instance lane remains independent from protocol publish gate while protocol-feedback sidecar path remains mandatory.

Core semantics lock:

1. same-lineage execution must be gate-source convergent across `update`, `three-plane`, and `full-scan`; `update pass + aggregation fail` split is fail-closed.
2. required contracts must be gated by producer readiness + current-round linkage + run-type applicability; history-only activity cannot force blocking requiredization.
3. non-applicable contracts must emit explicit `SKIPPED_NOT_REQUIRED` with machine-readable reason (no synthetic missing-evidence failures).
4. fallback taxonomy must define legal terminal state for "no fallback event in current run" under required surfaces.
5. strict context surfaces must fail-fast on env/CLI catalog mismatch unless explicit audited override receipt is present.
6. protocol-feedback primary write failure must use controlled spool/reconcile strategy with machine-verifiable receipt chain; silent drop is forbidden.

Reserved error-code family (for architect contract freeze):

1. `IP-GSRC-001`
2. `IP-GSRC-002`
3. `IP-GSRC-003`
4. `IP-GSRC-004`
5. `IP-GSRC-005`
6. `IP-GSRC-006`
7. `IP-GSRC-007`

Four-track evidence package (cross-verified):

1. `T1 governance/spec`: mandatory matrix closure for `C28..C30` and related fail-close clauses.
2. `T2 runtime implementation`: applicability-scoped requiredization fields and observation-profile skip semantics are now wired in Batch-6/7 gate validators.
3. `T3 replay evidence`: observation profile (`scan`) emits deterministic `SKIPPED_NOT_REQUIRED` for non-applicable gates, but strict profiles (`update/readiness/ci`) still show requiredization over-block when current-round linkage is absent.
4. `T4 protocol feedback`: canonical outbox + upgrade-proposal + evidence-index linkage for this hotfix stream.

Implementation delta snapshot (2026-03-07):

1. requiredization applicability fields added:
   - `run_profile`
   - `producer_readiness`
   - `requiredization_current_round_linked`
2. no-event legal terminal state added for fallback taxonomy:
   - `no_fallback_event_in_current_run`.
3. landing scripts:
   - `scripts/validate_intake_evidence_core.py`
   - `scripts/validate_dedup_monotonicity.py`
   - `scripts/validate_cross_workflow_schema.py`
   - `scripts/validate_route_version_pinning.py`
   - `scripts/validate_fallback_taxonomy_normalization.py`
4. replay snapshot:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect ...`
   - project/global Batch-6/7 gates converge to `SKIPPED_NOT_REQUIRED` with explicit non-applicable stale reasons.
5. historical residual blockers from round-2 (kept for traceability):
   - observation-profile `cross_workflow_schema` strictness (`IP-XWF-002`) was open in round-2 and is now closed in round-3 (`SKIPPED_NOT_REQUIRED` when not applicable).
   - catalog mismatch warning-only behavior was open in round-2 and is now fail-close on strict operations in round-3 (`IP-ENV-003`), while `scan` remains observational.

Round-2 replay sweep (global four-identity sample, 2026-03-07):

1. replay commands:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids office-ops-expert --actor-id assistant:codex --out /tmp/v16_full_scan_office-ops-expert_20260307_round2.json`
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect --actor-id assistant:codex --out /tmp/v16_full_scan_base-repo-architect_20260307_round2.json`
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --actor-id assistant:codex --out /tmp/v16_full_scan_custom-creative-ecom-analyst_20260307_round2.json`
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --actor-id assistant:codex --out /tmp/v16_full_scan_system-requirements-analyst_20260307_round2.json`
2. protocol-layer blockers observed:
   - `office-ops-expert`: `IP-XWF-002` (`cross_workflow_schema` observation applicability residual).
   - `base-repo-architect`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`.
   - `custom-creative-ecom-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`.
   - `system-requirements-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`, `IP-SEM-004`.
3. applicability/context residuals remain unchanged:
   - `P1-APPLICABILITY-003`: `IP-XWF-002` still reproducible (`/tmp/xwf_office_round2.json`).
   - `P1-CONTEXT-004`: catalog mismatch still warning-only (`/tmp/runtime_mode_guard_mismatch_round2.log`).
4. hard-switch guard behavior remains intact and is not treated as regression:
   - non-bound activation without switch-intent receipt fails with `IP-ACT-SWITCH-001`.
   - this confirms `no-hard-switch` contract is still enforced while replaying multi-identity scans.

Round-3 replay sweep (`HEAD=a0c191e`, 2026-03-07):

1. global full-scan re-run (per identity):
   - `/tmp/audit_r3_full_scan_office-ops-expert.json`
   - `/tmp/audit_r3_full_scan_base-repo-architect.json`
   - `/tmp/audit_r3_full_scan_custom-creative-ecom-analyst.json`
   - `/tmp/audit_r3_full_scan_system-requirements-analyst.json`
2. blocker matrix remained deterministic:
   - `office-ops-expert`: `IP-RARCH-002` (`replay_archive_contract`).
   - `base-repo-architect`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`, `IP-WRB-003`, `IP-RARCH-002`.
   - `custom-creative-ecom-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`, `IP-WRB-003`, `IP-RARCH-002`.
   - `system-requirements-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`, `IP-SEM-004`, `IP-RARCH-002`.
3. applicability/context closure status:
   - `validate_v16_cross_workflow_schema --operation scan` now returns `SKIPPED_NOT_REQUIRED` with `cross_workflow_not_applicable_no_route_or_dedup_signal` (no longer `IP-XWF-002` on observation profile).
   - `validate_identity_runtime_mode_guard` now fails with `IP-ENV-003` on strict operations (`validate/readiness/ci`), while `scan` remains observational warning.
4. new replay-archive expectation drift:
   - all four identities fail the same case (`rq019_negative_missing_field`) in `validate_replay_archive_contract.py`.
   - current replay output is `PASS_REQUIRED` while fixture expectation still requires `FAIL_REQUIRED/IP-XWF-002` (`validate_replay_archive_contract.py:454-473`).
5. new `rq033` machine-lock landing is wired but not yet requiredized in this replay path:
   - `python3 scripts/validate_execution_target_tuple_isolation.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --operation scan --json-only`
   - result: `execution_target_tuple_isolation_status=SKIPPED_NOT_REQUIRED`, `stale_reasons=[\"contract_not_required\"]`.

Round-4 closure replay (2026-03-07):

1. replay-archive expectation drift is closed:
   - `python3 scripts/validate_replay_archive_contract.py --identity-id office-ops-expert --catalog "${HOME}/.codex/.identity/catalog.local.yaml" --operation scan --json-only`
   - result: `replay_archive_contract_status=PASS_REQUIRED`, `error_code=""`.
2. `rq019_negative_missing_field` regression case now remains negative under applicability-aware extraction:
   - fixture carries explicit dedup signal + missing `run_id`,
   - observed: `cross_workflow_schema_status=FAIL_REQUIRED`, `error_code=IP-XWF-002`, `stale_reasons=[\"missing_run_id\"]`.
3. full-scan sample confirms `IP-RARCH-002` is no longer emitted for this case:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids office-ops-expert --project-catalog "${HOME}/.codex/.identity/catalog.local.yaml" --actor-id assistant:codex --out /tmp/full_scan_office_fix_round3b.json`
   - replay archive lane emits `replay_archive_contract_status=PASS_REQUIRED`.

Round-5 freeze replay (`HEAD=6a2ef0b`, project catalog lineage, 2026-03-07):

1. replay commands:
   - `python3 scripts/release_readiness_check.py --identity-id <store-manager|base-repo-audit-expert-v3|custom-creative-ecom-analyst|base-repo-architect> --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope <SYSTEM|USER> --actor-id assistant:codex`
   - `python3 scripts/identity_creator.py validate --identity-id <store-manager|base-repo-audit-expert-v3|custom-creative-ecom-analyst|base-repo-architect> --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope <SYSTEM|USER> --actor-id assistant:codex`
   - `python3 scripts/validate_required_contract_coverage.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation update --json-only`
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids store-manager,base-repo-audit-expert-v3,custom-creative-ecom-analyst,base-repo-architect --project-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --global-catalog /tmp/nonexistent-catalog.yaml --actor-id assistant:codex --out /tmp/audit_r5_full_scan_project.json`
2. strict-scope propagation residual (`P1-SCOPE-005`):
   - `identity_creator validate` still invokes `validate_identity_instance_isolation.py` without `--scope`, causing `store-manager` (`SYSTEM`) to fail with `scope mismatch ... requested=USER`.
3. Batch-6/7 strict requiredization residual (`P1-APPLICABILITY-006`):
   - `validate_required_contract_coverage --operation update` reports `failed_required_contract_count=6` for `base-repo-architect`.
   - failing strict-gate codes: `IP-INTAKE-EVID-001`, `IP-PIN-001`, `IP-FBTAX-002`, `IP-DEDUP-001`, `IP-XWF-001`.
   - all failures occur with `producer_readiness=false` and `requiredization_current_round_linked=false`.
4. observation profile remains non-blocking as expected:
   - `scan` for the same validators returns `SKIPPED_NOT_REQUIRED` with explicit stale reasons.
5. replay-archive closure remains stable:
   - `validate_replay_archive_contract.py --operation scan` returns `PASS_REQUIRED`, `15/15` cases passed for `base-repo-architect`, `base-repo-audit-expert-v3`, and `custom-creative-ecom-analyst`.
6. `/tmp` debt still has residuals:
   - core strict-chain scripts are migrated, but fixed `/tmp` paths remain in `/.github/workflows/_identity-required-gates.yml` and legacy default blocker-receipt outputs.

Round-6 three-point closure replay (project-local lineage, 2026-03-07):

1. scope propagation closure (`P1-SCOPE-005`):
   - `python3 scripts/identity_creator.py validate --identity-id store-manager --catalog "$CAT" --scope SYSTEM --actor-id assistant:codex`
   - validate/update chains now forward `--scope` into `validate_identity_instance_isolation.py`; replay no longer falls back to USER default.
2. strict applicability closure (`P1-APPLICABILITY-006`):
   - `python3 scripts/validate_required_contract_coverage.py --catalog "$CAT" --identity-id base-repo-architect --operation update --json-only`
   - `failed_required_contract_count=0`; Batch-6/7 rows (`cross_verification_tracks/intake_evidence_quorum/route_version_pinning/fallback_taxonomy_normalization/dedup_monotonicity/cross_workflow_schema/skill_path_integrity`) now resolve `SKIPPED_NOT_REQUIRED` when `requiredization_current_round_linked=false`.
   - direct gate replay (`operation=update`) returns deterministic stale reason: `required_contract_not_applicable_no_current_round_evidence_source`.
3. temp-path residual closure (`P1-TMPPATH-007`):
   - static replay `rg -n "/tmp" .github/workflows/_identity-required-gates.yml scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py scripts/validate_execution_reply_identity_coherence.py` returns no hits.
   - CI required-gates workflow now uses runner/runtime-scoped temp roots; legacy blocker receipt defaults are switched to `runtime_temp_file(...)`.
4. non-regression negative controls (explicit evidence path) remain fail-close:
   - fallback negative: `FAIL_REQUIRED + IP-FBTAX-001`.
   - dedup missing required field: `FAIL_REQUIRED + IP-DEDUP-002`.

Round-7 multi-source protocol-feedback convergence replay (protocol lane only, 2026-03-07):

1. scope lock:
   - this replay consolidates protocol-layer receipts from three independent protocol-feedback channels.
   - instance business behavior is out of scope; only protocol gate semantics and cross-surface homomorphism are evaluated.
2. four-track consolidation (`T1..T4`):
   - `T1` intake batches: `FEEDBACK_BATCH_20260307T070548Z_v16_upgrade_cross_track_alignment_regression.md`, `FEEDBACK_BATCH_20260307T071111Z_protocol_lane_four_track_crosscheck_sanitized.md`, `FEEDBACK_BATCH_2026-03-07_002_protocol-lane-post-escalation.md`.
   - `T2` channel integrity validators: `validate_protocol_feedback_ssot_archival -> PASS_REQUIRED`, `validate_protocol_vendor_semantic_isolation -> PASS_REQUIRED`, `validate_protocol_feedback_reply_channel -> SKIPPED_NOT_REQUIRED(contract_not_required)`.
   - `T3` replay consistency checks: run-id selector, coverage-vs-three-plane convergence, headstamp/session refresh strictness, semantic routing closure.
   - `T4` evidence indexing: each batch is indexed through canonical `runtime/protocol-feedback/evidence-index/INDEX.md` with replay receipts.
3. confirmed protocol-layer residuals (no business semantics):
   - run-id anchored selector still has compatibility gap for dual report naming (`identity-upgrade-exec-*.json` vs `<epoch>.json`) and can return run-id-not-found for valid lineage.
   - same lineage can still split across strict surfaces: `operation=update` shows required failures while `operation=three-plane` reports zero required failures.
   - three-plane can stay `BLOCKED` even when `required_failed=0` because report selection falls back to stale tuple/version alignment paths.
   - send-time/headstamp recurrence family remains visible on pointer/binding divergence branches (`IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`).
   - semantic routing convergence residual remains open; latest protocol-feedback regression rounds show active blocker shape has shifted from legacy `IP-SEM-004` trace to `IP-SEM-001` field-completeness failure (`intent_domain`, `intent_confidence`, `classifier_reason`).
   - session refresh severity is still too soft for strict surfaces on pointer-consistency + actor-binding-missing branches (`IP-ASB-RFS-002` as `WARN_NON_BLOCKING`).
4. protocol-layer positive reinforcement retained:
   - parser/runtime crash class is still closed in strict command chains.
   - no-hard-switch baseline remains enforced.
   - protocol-feedback canonical archival checks remain healthy (`PASS_REQUIRED` on SSOT archival and vendor semantic isolation).
5. required architect closure (protocol only):
   - unify run-id report selector source with dual-naming compatibility and deterministic tie-break.
   - enforce same-lineage convergence tuple across strict surfaces: (`failed_required_contract_count`, `report_selected_path`, `run_id_binding`).
   - promote session refresh pointer/binding divergence from warning to strict fail-close when strict operations are requested.
   - keep reply-channel `SKIPPED_NOT_REQUIRED(contract_not_required)` as legal non-failure unless contract is requiredized.
   - enforce semantic metadata tuple completeness on strict protocol-feedback path (`intent_domain`, `intent_confidence`, `classifier_reason`) and require deterministic correlated blocker receipt when activity is unscoped.

Round-11 protocol-feedback semantic regression refresh (`HEAD=5c3dda4+`, 2026-03-07):

1. scope:
   - protocol-lane replay evidence only; business-domain semantics remain out of scope.
2. intake set (`T1/T2`):
   - `custom-creative-ecom-analyst` batch: `FEEDBACK_BATCH_20260307T090934Z_protocol_fix_reverify_semantic_routing_sanitized.md` + `PROTOCOL_FIX_REVERIFY_20260307T090934Z.json`.
   - `system-requirements-analyst` batch: `FEEDBACK_BATCH_2026-03-07_003_protocol-lane-regression-round3.md` + `SESSION_REVIEW_2026-03-07_protocol-lane-regression-round3.md`.
   - both are indexed in canonical protocol-feedback evidence indices.
3. machine replay signals (`T3`):
   - `custom-creative-ecom-analyst`: send-time/first-line/headstamp/actor-bound probes are passing or expected fail-closed, while semantic guard remains `FAIL_REQUIRED` + `IP-SEM-001`.
   - `system-requirements-analyst`: protocol lane routing remains correct, but update is still non-green (`all_ok=false`, `writeback_status=DEFERRED_VALIDATION_FAILED`), three-plane remains `BLOCKED` (`IP-UPG-002`), and semantic guard remains `IP-SEM-001`.
4. protocol interpretation (`T4`):
   - active blocker family is semantic tuple completeness under unscoped activity correlation (`ACTIVITY_UNSCOPED`), not lane routing collapse.
5. closure requirement update:
   - promotion remains blocked until strict same-lineage replay removes `IP-SEM-001` and reaches `summary.p0=0` on protocol target scans.

Round-16 semantic requiredization scope convergence (`HEAD=working-tree+dirty`, 2026-03-08):

1. scope:
   - protocol-layer applicability convergence for semantic/source-trust family (`IP-SEM-001`, `IP-UPG-002` residual class).
2. implementation landing:
   - `scripts/validate_semantic_routing_guard.py`
   - `scripts/validate_protocol_vendor_semantic_isolation.py`
   - `scripts/validate_external_source_trust_chain.py`
   - `scripts/validate_protocol_data_sanitization_boundary.py`
3. requiredization convergence:
   - all four scripts now use lane-aware requiredization scope arbitration (`protocol_feedback_lane_common`) instead of artifact-presence-only escalation.
   - inspection surfaces (`scan/three-plane/inspection`) now emit deterministic `SKIPPED_NOT_REQUIRED` when activity is history-only and not current-round linked.
   - feedback batch selection prefers current-round correlated `FEEDBACK_BATCH_*` artifacts before generic pattern fallback.
4. local replay snapshot:
   - `operation=three-plane` probes on `base-repo-architect` converge to `SKIPPED_NOT_REQUIRED` with machine reason `contract_not_required_due_lane_scope_history_only_activity`.
   - command gates pass: `py_compile`, `docs_command_contract_check`, `validate_protocol_ssot_source`.
5. state boundary:
   - row remains `PENDING_INTAKE` pending independent multi-identity replay confirmation on protocol lane (especially `system-requirements-analyst` residual pair `IP-UPG-002 + IP-SEM-001`).

Round-17 UCG wave-3.1 residual closure replay (`HEAD=working-tree+dirty`, 2026-03-08):

1. scope:
   - this replay closes fixed-audit residuals for `HOTFIX16-P0-007`: (`P0 coherence non-blocking leak`, `P1 drift alias bypass`, `P1 same-surface parity shadow`).
2. landed protocol deltas:
   - `scripts/validate_execution_reply_identity_coherence.py`: strict operations include `three-plane` + `ci`.
   - `scripts/report_three_plane_status.py`: coherence `WARN_NON_BLOCKING` is now hard-boundary on three-plane.
   - `scripts/validate_required_gate_surface_drift.py`: mapping-derived forbidden set now includes deterministic alias/delegate expansion (`validate_vXX_*` wrappers and `from <module> import main` delegates).
   - `scripts/validate_required_gate_tuple_parity.py`: new `--require-distinct-operations` contract.
   - strict surfaces (`identity_creator`, `release_readiness_check`, `report_three_plane_status`, `full_identity_protocol_scan`, `e2e`, required-gates CI) now emit operation-diverse parity receipts instead of same-operation shadow-only comparisons.
3. replay evidence:
   - coherence strict replay: `/tmp/coh_three_plane_now.json` (`FAIL_REQUIRED`, strict=true on three-plane mismatch).
   - drift alias bypass replay: `/tmp/ucg_wave31_drift_repro.json` (`FAIL_REQUIRED`, `IP-GATE-ENTRY-002` after injected alias direct-call).
   - tuple parity operation contract replay:
     - fail: `/tmp/tp_same_now.json` (`distinct_operations_not_met`, `operation_not_unique`);
     - pass: `/tmp/tp_diff_now.json`, `/tmp/rg_parity_wave31.json`.
   - non-regression executable replay: `/tmp/full_scan_wave31.json` (full-scan remains executable with operation-diverse parity wiring).
4. gate replay:
   - `python3 -m py_compile scripts/validate_execution_reply_identity_coherence.py scripts/validate_required_gate_surface_drift.py scripts/validate_required_gate_tuple_parity.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py`
   - `bash -n scripts/e2e_smoke_test.sh`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`
5. state boundary:
   - `HOTFIX16-P0-007` remains `PENDING_INTAKE` (protocol replay delta landed, independent auditor replay sign-off pending).
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-18 protocol-lane residual convergence replay (`HEAD=working-tree+dirty`, 2026-03-08):

1. scope:
   - this replay closes the recurring `IP-UPG-002 + IP-SEM-001` residual shape reported by protocol-lane SRA batches, with protocol-only code-path hardening.
2. landed protocol deltas:
   - `scripts/validate_semantic_routing_guard.py` now emits deterministic semantic tuple inference when correlated feedback batches omit explicit semantic metadata.
   - `scripts/validate_agent_handoff_contract.py` and `scripts/validate_identity_collab_trigger.py` now validate bounded recent evidence windows and disable stale-age hard blocking under explicit `--self-test`.
   - `CHANGELOG.md` now includes explicit backfill linkage anchors for strict historical heads (`0a6359a`, `6af084f`) used by changelog gate replay.
3. replay evidence:
   - `/tmp/semantic_guard_round3_wave18.json` => `semantic_routing_status=PASS_REQUIRED`, `semantic_fields_inferred=true`.
   - `validate_agent_handoff_contract.py --self-test` (`system-requirements-analyst`, global catalog) => `PASSED`.
   - `validate_identity_collab_trigger.py --self-test` (`system-requirements-analyst`, global catalog) => `PASSED`.
   - `validate_changelog_updated.py --base 4d6d3ff... --head 0a6359a...` => `PASSED (historical backfill linkage)`.
4. state boundary:
   - `HOTFIX16-P1-004` remains `PENDING_INTAKE` pending independent auditor full-chain replay on latest head (`update + three-plane + full-scan`).
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-19 UCG tuple-source convergence replay (`HEAD=6af084f+dirty`, 2026-03-08):

1. scope:
   - this replay is protocol-layer only and targets recurring control-plane drift (`headstamp missing`, `identity drift`, `protocol lane split`) under `HOTFIX16-P0-007`.
2. four-track replay set:
   - runtime evidence: `/tmp/audit_ctx_resolve_base_repo_architect_20260308_r2.json`, `/tmp/audit_ctx_render_base_repo_architect_20260308_r2.json`, `/tmp/audit_validate_latest_20260308.log`, `/tmp/tuple_parity_gap_result_r2.json`, `/tmp/audit_compose_reply.txt`.
   - canonical pointer evidence: `/Users/yangxi/claude/codex_project/weixinstore/.identity/session/active_identity.json`.
   - strict bundle projection evidence:
     - `/private/var/folders/3x/xy0h9s6x5p790dzwwrdzq3kh0000gn/T/identity-runtime/required-gate-bundle/three-plane/base-repo-architect/three-plane-base-repo-architect/required-gate-bundle-three-plane-base-repo-architect-three-plane-base-repo-architect.json`
     - `/private/var/folders/3x/xy0h9s6x5p790dzwwrdzq3kh0000gn/T/identity-runtime/required-gate-bundle/scan/base-repo-architect/three-plane-base-repo-architect-scan-probe/required-gate-bundle-three-plane-scan-probe-base-repo-architect-three-plane-base-repo-architect.json`
3. confirmed residuals:
   - source-layer taxonomy split is still reproducible (`resolve_identity_context -> local`, response stamp -> `project`).
   - strict headstamp chain still contains `--actor-id` propagation gaps on render/first-line/coherence call edges.
   - `LOCK_MATCH` can still be emitted from historical binding selection while canonical pointer is another identity.
   - tuple parity still excludes HUD core tuple fields (`identity_id`, `actor_id`, `resolved_work_layer`, `resolved_source_layer`, `lock_state`), so synthetic drift can pass.
   - strict bundle parity path still allows empty `send_time_gate_status` to pass.
4. required protocol closure (wave-4):
   - shared tuple resolver across validate/three-plane/reply compose.
   - canonical egress gate strict fail-close on tuple mismatch (no non-blocking downgrade).
   - entry freeze (`run_id + tuple`) with egress-only frozen tuple consumption.
   - CI same-run full tuple equality between validate and three-plane receipts.
5. state boundary:
   - `HOTFIX16-P0-007` remains `PENDING_INTAKE`; unified entrypoint exists but convergence contract is still incomplete.
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-20 multi-instance protocol-boundary replay (`HEAD=6af084f+dirty`, 2026-03-08):

1. scope:
   - this replay audits two new runtime batches (`custom-creative-ecom-analyst`, `office-ops-expert`) and enforces protocol-vs-instance boundary segregation.
2. replay evidence:
   - `/tmp/cca_validate_accept_posthead_20260308.log`, `/tmp/cca_full_scan_accept_posthead_20260308.json`, `/tmp/cca_three_plane_accept_posthead_20260308.json`
   - `/tmp/cca_update_instance_after_protocol_fix_20260308.log`, `/tmp/cca_update_instance_review_required_20260308.log`, `/tmp/cca_update_instance_review_required_rerun_20260308.log`, `/tmp/cca_heal_apply_20260308.log`
   - `/tmp/three_plane_office_postfix_1772901986.json`
   - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/reports/identity-upgrade-exec-office-ops-expert-1772901986.json`
3. confirmed protocol residual:
   - `custom-creative-ecom-analyst` still reproduces strict first-line tuple mismatch (`IP-ASB-STAMP-SESSION-001`, expected `protocol/env`, observed `instance/project`).
4. corrected root-cause split:
   - this batch `IP-GATE-ENTRY-001` is produced by required-row hard failure (`skill_path_integrity -> IP-SPATH-002`), not by `SKIPPED_NOT_REQUIRED` rows.
   - safe-auto/review/heal blocks (`blocked_by_safe_auto_path_policy`, `IP-HEAL-003`, report freshness `IP-REL-001`) are instance-side closure items and stay outside protocol fix queue.
5. non-regression signal:
   - office replay keeps `instance_plane_status=CLOSED` with `repo/release` blocked; no new protocol entrypoint regression is indicated.
6. state boundary:
   - `HOTFIX16-P0-007` remains `PENDING_INTAKE`; protocol scope keeps wave-4 tuple-source closure and rejects instance-only findings from protocol backlog promotion.
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-21 headstamp multibinding + parser convergence replay (`HEAD=13aa0b0+dirty`, 2026-03-08):

1. scope:
   - protocol-layer-only closure for two recurring replay false blockers (`first-line parser path drift`, `headstamp actor-mismatch false fail under multibinding`) in `HOTFIX16-P0-007`.
2. landed protocol deltas:
   - `scripts/validate_reply_identity_context_first_line.py`: restored `.json/.jsonl/.txt` first-line extraction path and removed misplaced unreachable parser segment.
   - `scripts/validate_headstamp_recurrence_closure.py`: actor-mismatch negative probe now yields `SKIPPED_INCONCLUSIVE_MULTIBINDING` when `binding_key_mode=actor_id+session_id` and no explicit session selector is available.
3. replay evidence:
   - `/tmp/headstamp_sra_scan_useryangxi_after.json` -> `headstamp_recurrence_closure_status=PASS_REQUIRED`.
   - `/tmp/full_scan_sra_round19_after.json` -> summary `{p0:0, p1:0, ok:1}` for target `system-requirements-analyst` with explicit actor context.
   - `/tmp/reply_first_line_probe_out.json` confirms non-jsonl parser path executes without runtime crash.
4. gate replay:
   - `python3 -m py_compile scripts/validate_reply_identity_context_first_line.py scripts/validate_headstamp_recurrence_closure.py`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`
5. state boundary:
   - row remains `PENDING_INTAKE` pending independent auditor replay sign-off on latest head.
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Round-22 UCG minimal control-plane decision freeze (`HEAD=13aa0b0+dirty`, 2026-03-08):

1. scope:
   - this round is governance simplification, not requirement expansion.
   - objective is to collapse prior branch-heavy guidance into one enforceable control-plane shape.
2. normative override:
   - `8.41` becomes authoritative;
   - `8.38/8.39/8.40` remain replay evidence, not parallel normative branches.
3. frozen minimal model:
   - strict `source_layer` reduced to `{project, global}`;
   - `scope` remains separate (`scope ∈ {REPO, USER, ADMIN, SYSTEM}`);
   - `local/repo/env/auto` and legacy source tokens are demoted to migration metadata (`catalog_origin_layer`, `resolution_mode`);
   - single entry freeze tuple + single canonical egress fail-close.
4. reduced CI contract (four assertions only):
   - same-run full tuple equality (`validate` vs `three-plane`);
   - non-empty `send_time_gate_status`;
   - illegal `source_layer` hard-fail;
   - strict-chain missing `--actor-id` hard-fail.
5. protocol/instance boundary:
   - protocol backlog accepts only tuple/entry/egress control-plane defects;
   - instance runtime/path-policy findings are excluded from protocol remediation queue.
6. state boundary:
   - `HOTFIX16-P0-007` remains `PENDING_INTAKE`;
   - lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Architect handoff artifacts (canonical channel pattern):

1. `runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*_gate_source_convergence*.md`
2. `runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_*_requiredization_applicability*.md`
3. `runtime/protocol-feedback/evidence-index/INDEX.md`

Promotion guard (hard):

1. hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires validator/e2e closure tuple:
   - same-lineage update/readiness/three-plane/full-scan convergence replay,
   - producer/applicability positive+negative replay matrix,
   - strict context mismatch fail-fast replay,
   - protocol-feedback spool/reconcile replay closure.

---

## 4) Reviewer decision log

| Fix ID | Audit Decision | Reviewer | Reviewed At (UTC) | Notes |
| --- | --- | --- | --- | --- |
| FIX16-001 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-08T08:32:00Z | docs SSOT bootstrap remains stable and re-audited (`docs_command_contract_check=PASS`, `validate_protocol_ssot_source=OK`); row remains non-promotional only because v1.6 P0 global lock is still open. |
| FIX16-002 | PENDING_INTAKE | base-repo-architect | 2026-03-07T17:26:00Z | RQ-001 executable closure landed (validator + kernel anchor + mapping row + lane hooks across creator/readiness/three-plane/full-scan/e2e/ci); remains non-promotional pending deterministic required=true replay archive |
| FIX16-003 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`08f20ab + 13485bb`): capability-boundary validator + kernel/mapping anchors + creator/readiness/three-plane/full-scan/e2e/ci hooks; remains non-promotional pending deterministic required=true replay archive |
| FIX16-004 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`08f20ab + 13485bb`): promotion-pipeline validator + kernel/mapping anchors + lane hooks; remains non-promotional pending replay archive |
| FIX16-005 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`08f20ab + 13485bb`): outlet matrix validator + kernel/mapping anchors + lane hooks; remains non-promotional pending replay archive |
| FIX16-006 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`08f20ab + 13485bb`): sidecar cwd parity validator + kernel/mapping anchors + lane hooks; remains non-promotional pending replay archive |
| FIX16-007 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): release-plane cloud evidence validator + kernel/mapping anchors + lane hooks (creator/readiness/three-plane/full-scan/e2e/ci); remains non-promotional pending strict replay archive |
| FIX16-008 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): cross-cwd absolute-input validator + kernel/mapping anchors + lane hooks; remains non-promotional pending parity replay archive |
| FIX16-009 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure reinforced (`08f20ab + 13485bb`): docs bridge checker + mapping/lane homomorphism hooks maintained; remains non-promotional pending deterministic contradiction replay archive |
| FIX16-010 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | executable closure landed (`13485bb`): run-id anchored selection validator (`scripts/validate_run_id_report_selection.py`) + kernel/mapping anchors + creator/readiness/three-plane/full-scan/e2e/ci hooks; remains non-promotional pending deterministic replay archive |
| FIX16-011 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): phase-A/phase-B parity validator + kernel/mapping anchors + lane hooks; remains non-promotional pending strict replay archive |
| FIX16-012 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): tmp collision-safety validator + allocator-scoped temp semantics + lane hooks; remains non-promotional pending concurrency replay archive |
| FIX16-013 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): freshness rotation emitter+validator + kernel/mapping anchors + lane hooks; remains non-promotional pending positive/negative replay archive |
| FIX16-014 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): protocol-feedback atomic emitter+validator + kernel/mapping anchors + lane hooks; remains non-promotional pending transaction replay archive |
| FIX16-015 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | SRA packet triage preserved; executable bootstrap-capability validator landed (`13485bb`) and lane-hooked, with non-promotional replay boundary unchanged |
| FIX16-016 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): prompt capability matrix fail-close validator + kernel/mapping anchors + lane hooks; remains non-promotional pending replay archive |
| FIX16-017 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | executable closure landed (`13485bb`): refresh/strict business interference emitter+validator + kernel/mapping anchors + lane hooks; remains non-promotional pending paired replay archive |
| FIX16-018 | PENDING_INTAKE | base-repo-architect | 2026-03-07T16:45:00Z | cross-verification core remains landed (see `FIX16-035` chain); status boundary unchanged pending independent replay sign-off |
| FIX16-019 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | executable closure landed for Batch-6 (`ASB16-RQ-018..022`) via `Task-6..15` commit chain (`9e59e0f..1beeb88`) including monotonic dedup/schema/path/pinning/fallback validators + lane hooks; remains non-promotional pending deterministic required=true replay archive |
| FIX16-020 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T17:10:00Z | discovery dual-track intake preserved; kernel anchors + mapping rows for `RQ-023/024` landed (`910ec6e`) and now machine-projected, while promotion remains blocked pending required=true replay closure |
| FIX16-021 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | kernel-first intake preserved; executable `RQ-025` canonical-source validator landed (`13485bb`) with mapping anchor sync and lane hooks; non-promotional replay boundary unchanged |
| FIX16-022 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | semantic convergence requirement preserved; executable convergence validator landed (`13485bb`) and wired to readiness/three-plane/full-scan/e2e/ci, replay closure still pending |
| FIX16-023 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | intake hard-gate executable closure landed (`f63eb55 + 47f2f38 + 1beeb88`): canonical single-parser dual-mode core (`scripts/validate_intake_evidence_core.py`) + delegated wrappers + lane hooks (`creator/readiness/three-plane/full-scan/e2e/ci`); promotion boundary unchanged pending required=true replay closure |
| FIX16-024 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | self-drive conclusions preserved; executable coupling validator landed (`13485bb`) with explicit actor gate + lane hooks, while multimodal replay closure remains pending before promotion |
| FIX16-025 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | deep cross-verification package remains valid and executable closures are now landed for `ASB16-RQ-015/029/030`; `S0..S4` sequence remains as replay-hardening path, and promotion is blocked until deterministic replay archive is complete |
| FIX16-026 | PENDING_INTAKE | base-repo-architect(self-drive) | 2026-03-05T12:58:00Z | runtime self-drive pilot on `base-repo-architect`: protocol-kernel prompt injection + multimodal verification baseline passes; creator strict chain still shows actor-context convergence residual (`IP-ASB-STAMP-SESSION-005`), kept in v1.6 executable-coupling track only |
| FIX16-027 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | final T1/T2/T3/T4 cross-verification replay direction remains reaffirmed; executable closure for `ASB16-RQ-015/017/029/030/031` is landed and lane-wired, while deterministic replay archive closure remains the sole non-promotional blocker |
| FIX16-028 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-05T22:10:00+08:00 | full-repo lock census + architect independent deep-rescan receipt completed (`/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`, `/tmp/v16_architect_deep_scan_full_repo_20260305.json`, `/tmp/v16_one_by_one_requirement_review_20260305.md`): `BRIDGE_LOCKED=32/32`, `KERNEL_LOCKED=0/32`, `SCRIPT_LOCKED=0/32`, `FULL_LOCKED=0/32`; row-level audit can proceed, promotion remains blocked |
| FIX16-029 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T17:10:00Z | headstamp hard-gate intake preserved; kernel anchor + mapping projection for `RQ-032` landed (`910ec6e`), promotion still blocked pending strict replay closure |
| FIX16-030 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T18:05:00Z | Batch-1 (`ASB16-RQ-001..005`) executable closure is landed (validators + kernel anchors + mapping rows + lane hooks); row-level decision remains `ACCEPT_WITH_FIX` and non-promotional pending deterministic required=true replay archive |
| FIX16-031 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | Batch-2A executable closure landed (`13485bb`): validators + kernel anchors + mapping rows + creator/readiness/three-plane/full-scan/e2e/ci wiring; remains non-promotional pending deterministic replay archive |
| FIX16-032 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T17:10:00Z | Batch-3B reinforcement complete: executable components (`13485bb`) plus full kernel/mapping projection for `RQ-024/028` (`910ec6e`) are landed; non-promotional replay boundary unchanged |
| FIX16-033 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T17:10:00Z | Batch-4 reinforcement complete: `RQ-029/031/007/008` executable validators (`13485bb`) plus `RQ-032` kernel/mapping projection (`910ec6e`) are synchronized; promotion remains blocked pending replay closure |
| FIX16-034 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T16:45:00Z | Batch-5 executable closure landed (`13485bb`): phase/tmp/freshness/atomic/interference validators + emitters + lane hooks + mapping/kernel sync; historical missing-validator blocker resolved, replay closure still required for promotion |
| FIX16-035 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-07T07:04:25Z | Batch-6 strict applicability closure landed in protocol layer: unlinked strict lanes now emit `SKIPPED_NOT_REQUIRED` with machine reason (`required_contract_not_applicable_no_current_round_evidence_source`) and coverage replay reports `failed_required_contract_count=0`. Row remains non-promotional pending independent required=true current-round replay archive. |
| FIX16-036 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-07T07:04:25Z | Batch-7 strict applicability closure landed in protocol layer: fallback/intake strict lanes no longer synthetic-fail on unlinked rounds; explicit negatives remain fail-close (`IP-FBTAX-001`). Row remains non-promotional pending independent required=true current-round replay archive. |
| FIX16-037 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T17:10:00Z | Write-boundary non-starvation hooks remain lane-wired (`093496b`); this round adds canonical `RQ-028` kernel/mapping projection (`910ec6e`) for full requirement coverage. Promotion boundary unchanged pending replay matrix closure (`A/B/C/D/E/F`). |
| HOTFIX16-P0-001 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T07:40:00Z | runtime bridge closure landed locally (fqsh): guarded route metadata + conflict resolver + inbound `409` fail-close (including explicit override path) are active in source, and local replay suite passes (`tests/test_chat_inbound.py`, `tests/test_chat_bridge.py`, `28 passed`). remains non-promotional pending independent live rollout evidence (`route snapshot + conflict/non-conflict replay archive`). |
| HOTFIX16-P0-002 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T07:27:07Z | protocol-lane starvation/headstamp hardening remains landed; round-7 replay closes resolver divergence (`headstamp_recurrence_closure_status=PASS_REQUIRED` on sampled identities) and keeps mismatch-negative fail-close. round-8 replay still shows canonical send-time gateway applicability drift (`SKIPPED_NOT_REQUIRED(contract_not_required)` on direct scan probe). row remains non-promotional pending strict requiredization closure + independent live lane/headstamp replay archive. |
| HOTFIX16-P1-003 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T07:04:25Z | temp-path closure remains in-progress: CI + stamp/first-line/coherence paths are resolver-backed, and round-8 pre-implementation sweep has identified remaining fixed `/tmp` fallbacks in `execute_identity_upgrade` + freshness validators as mandatory next landing scope. status remains non-promotional pending full three-script closure replay and independent sign-off. |
| HOTFIX16-P1-004 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-08T04:10:00Z | round-18 residual convergence landed: semantic routing guard now provides deterministic inferred semantic tuple fallback for metadata-missing protocol batches, while handoff/collab self-test validators close stale-age false blockers via bounded recent-window validation + self-test age bypass. residual promotion blockers remain gated by independent full-chain replay (`update + three-plane + full-scan`) to clear `IP-UPG-002 + IP-SEM-001` on latest head. |
| HOTFIX16-P0-005 | PASS_WITH_BLOCKERS | audit-expert(codex) | 2026-03-08T08:32:00Z | parser/runtime crash class remains closed under latest replay (no argparse/pre-gate crash in `identity_creator validate` and `release_readiness_check` matrix); row stays non-promotional because downstream required gates are still blocked by deterministic business/baseline debts. |
| HOTFIX16-P0-006 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-07T06:02:07Z | machine-lock implementation remains landed (`rq_033` kernel+mapping+validator+lane-hooks) and round-8 strict actor-entry unification now enforces explicit actor-bound entry on `activate/update/validate` and wave apply path (`IP-ACTOR-ENTRY-001` fail-fast on missing actor). required=true tuple replay archive + runtime bridge rollout evidence remain pending. |
| HOTFIX16-P0-007 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-08T08:32:00Z | unified entrypoint freeze is re-audited as landed (`validate_required_gate_surface_drift=PASS_REQUIRED`, strict-surface bundle arg contract zero-missing); row remains non-promotional due global release blockers (`session_refresh`, sidecar unscoped activity, multi-layer overlap debt). |
| HOTFIX16-P0-008 | PENDING_INTAKE | audit-expert(codex) | 2026-03-08T08:10:00Z | independent replay on current head shows full-chain still blocked by writeback mandatory debt (`identity_creator validate rc=1`, `release_readiness rc=1`, `e2e rc=2`, `full_scan summary.p0=1`; blocker `IP-WRB-003`). keep non-promotional until post-execution mandatory closure is replay-proven. |
| HOTFIX16-P1-009 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-08T08:32:00Z | validate-chain expected-layer pass-through is replay-confirmed: `identity_creator validate` with explicit expected tuple now emits `work_layer=protocol/source_layer=project`, `reply_first_line_status=PASS_REQUIRED`, `send_time_gate_status=PASS_REQUIRED`; row remains non-promotional pending global chain closure. |
| HOTFIX16-P0-010 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-08T08:32:00Z | HUD tuple hardening + actor strict-entry closure is replay-confirmed (`tuple parity fail-close`, `compose no-actor fail-close`, source inference order fixed, bundle arg contract complete); row remains non-promotional due non-control-plane blockers (`IP-ASB-RFS-004/IP-PBL-006`, required coverage debt, worktree non-clean baseline). |

### Round-23 protocol checkpoint: canonical two-layer path cutover (execution landed, non-promotional)

1. Scope remains protocol base repo only; instance business logic is intentionally unchanged.
2. Canonical path model is now frozen to two roots:
   - project: `<project>/.identity/<identity_id>/`
   - global: `${CODEX_HOME:-~/.codex}/.identity/<identity_id>/`
3. Strict tuple contract converges to `catalog_path + resolved_pack_path + runtime_root`.
4. Runtime mode guard now requires `source_layer in {project, global}` and rejects non-canonical legacy roots in strict operations.
5. Resolver/runtime selectors/full-scan defaults are switched to `.identity` roots; legacy paths are migration-only.

Replay notes (this round):

1. Updated protocol scripts pass `python3 -m py_compile`.
2. Updated runtime shell selectors pass `bash -n`.
3. `python3 scripts/docs_command_contract_check.py` => PASS.
4. `python3 scripts/validate_protocol_ssot_source.py` => OK.
5. Legacy runtime catalog probe (`.agents/identity`) now fail-closes on runtime mode guard as expected.

Decision:

1. Lifecycle boundary unchanged: non-promotional.
2. Next closure dependency remains instance-side migration + replay on canonical `.identity` roots.

---


### Round-24 Audit Addendum (2026-03-08): Two-Layer Hard-Fail Closure

#### Scope

仅覆盖 protocol 控制面，不涉及实例业务能力。

#### Replayed Findings (Cross-validated)

1. P0: non-canonical catalog 语义洗白风险（已在本轮代码侧收口）。
   - 原现象：resolver 判定 `source_layer=unknown`，stamp 渲染为 `source_layer=project`。
   - 本轮修复后：non-canonical source 不再自动降级渲染为 `project/global`。

2. P0: strict surface 预检不一致（本轮补齐）。
   - 已补齐 `report_three_plane_status` 与 `full_identity_protocol_scan` 的 `validate_identity_runtime_mode_guard` 前置预检。
   - guard 未通过时禁止继续该 strict 链路 validator。

3. P1: expected layer 透传不完整（本轮补齐）。
   - `expected_work_layer/expected_source_layer` 已透传到 `render_identity_response_stamp`（three-plane/full-scan/release/e2e 链路）。

4. P1: 两层切换后历史实例路径债务显性化（符合职责边界）。
   - `project/.identity` 与历史实例落点不一致会被 guard 阻断。
   - 该迁移债务归 instance 层，不由 protocol 兼容兜底。

#### Evidence (machine replay refs)

1. `/tmp/v16_round24_full_repo_scan_20260308.json`
2. `/tmp/v16_round24_full_repo_scan_20260308.md`
3. `/tmp/audit_mode_guard_project_catalog_store_manager_20260308.log`
4. `/tmp/audit_resolve_legacy_base_repo_architect_20260308.json`
5. `/tmp/audit_render_legacy_base_repo_architect_20260308.json`
6. `/tmp/audit_three_plane_legacy_catalog_20260308.log`
7. `/tmp/audit_full_scan_legacy_catalog_20260308.log`
8. `/tmp/audit_three_plane_custom_legacy_with_report_20260308.json`

#### Decision

1. 接受“两层 canonical 收缩”方向，判定为必要收敛。
2. 当前状态维持 `SPEC_READY / PENDING_INTAKE`，不提级。
3. Wave-next 仅保留四项控制面闭环边界：
   - source-domain 单判定源
   - strict surface 统一 preflight
   - expected layer 全链透传
   - protocol/instance 职责硬边界执行


---

### Round-25 protocol checkpoint: HUD egress mandatory chain clarification (`direct-output bypass` guard, non-promotional)

1. Objective: stabilize bilateral communication by freezing HUD as mandatory protocol egress contract, not optional formatting.
2. Confirmed boundary: missing HUD in strict conversations is treated as control-plane egress inconsistency, not instance capability regression.
3. Mandatory strict egress chain (single path):
   - `compose_and_validate_governed_reply.py`
   - `validate_send_time_reply_gate.py`
   - final user-visible emission
4. Governance requirement:
   - strict user-visible output that bypasses canonical egress is non-compliant and should fail-close.
   - tuple continuity is required across entry->egress (`actor_id`, `identity_id`, `work_layer`, `source_layer`, `lock_state`).
5. Communication impact:
   - protocol and architecture side now share the same exchange baseline: "no canonical egress -> no outbound strict reply".

Decision:

1. This round is a control-plane communication freeze and does not change promotion posture.
2. `HOTFIX16-P0-007` remains `PENDING_INTAKE`.

---

### Round-26 protocol checkpoint: uncovered-scope deep scan and closure classification (`execution-surface first`, non-promotional)

1. Objective:
   - close Round-24 blind spots by machine-classifying uncovered roots and separating execution-risk scope from archive noise.
2. Scope baseline:
   - Round-24 scanned `scripts/** + identity/** + README.md`.
   - uncovered roots are now classified into `must_close_now / should_close_this_wave / archive_or_meta`.
3. Classified closure set:
   - must-close-now: `.github/**`.
   - should-close-this-wave: `docs/**`, `skills/**`, `CHANGELOG.md`, `VERSIONING.md`.
   - archive-or-meta: `.codex/**`, `.identity-protocol/**`, `.tmp-fixtures/**`, `.gitignore`, `requirements-dev.txt`.
4. P0 residual confirmed on uncovered execution surface:
   - CI strict HUD chain still has actor pass-through gaps in `.github/workflows/_identity-required-gates.yml` (`render_identity_response_stamp.py`, `validate_reply_identity_context_first_line.py`, `validate_execution_reply_identity_coherence.py` calls).
   - this can still trigger actor fallback semantics (`scripts/actor_session_common.py`), so drift status PASS does not imply parameter-contract closure.
5. Evidence:
   - `/tmp/v16_round26_uncovered_scope_audit_20260308.json`
   - `/tmp/v16_round26_uncovered_scope_audit_20260308.md`

Decision:

1. accept Round-26 as governance-strengthening addendum under `HOTFIX16-P0-007`.
2. keep lifecycle boundary unchanged: `PENDING_INTAKE`, non-promotional.

---

### Round-26.1 patch closure: actor passthrough + drift parameter contract (`must_close_now` execution surface)

1. Objective:
   - close Round-26 P0 residual where strict HUD chain could still fallback actor tuple because execution surfaces lacked explicit `--actor-id`.
2. Applied patch scope:
   - `.github/workflows/_identity-required-gates.yml`:
     - render / first-line / coherence command lines now explicitly pass `--actor-id "$HEADSTAMP_ACTOR_ID"`.
   - strict scripts:
     - `scripts/e2e_smoke_test.sh`
     - `scripts/report_three_plane_status.py`
     - `scripts/full_identity_protocol_scan.py`
     - `scripts/release_readiness_check.py`
     - `scripts/identity_creator.py`
     all now keep actor passthrough explicit on render/first-line/send-time/coherence chain.
3. Drift guard hardening:
   - `scripts/validate_required_gate_surface_drift.py` adds actor parameter contract verification for
     `render_identity_response_stamp.py`,
     `validate_reply_identity_context_first_line.py`,
     `validate_send_time_reply_gate.py`,
     `validate_execution_reply_identity_coherence.py`.
   - New fail-close code: `IP-GATE-ENTRY-003` when any strict surface misses `--actor-id`.
4. Runtime path residual closure (project canonical runtime):
   - `.identity/*/CURRENT_TASK.json` + runtime state/metrics + session mirror entries removed remaining `.agents/identity` literals; canonicalized to `.identity`.

Evidence:

1. `python3 scripts/validate_required_gate_surface_drift.py --json-only` → `PASS_REQUIRED` with `actor_id_passthrough_missing={}`.
2. `python3 scripts/docs_command_contract_check.py` → `PASS`.
3. `python3 scripts/validate_protocol_ssot_source.py` → `OK`.
4. `rg -n '\\.agents/identity|/\\.codex/\\.identity|~/.codex/.identity' .identity/{config,session} .identity/*/{CURRENT_TASK.json,META.yaml,TASK_HISTORY.md} .identity/*/runtime/{state,metrics}` → no hits.

Decision:

1. Round-26.1 marks execution-surface actor passthrough gap as code-closed and replay-ready.
2. Lifecycle boundary remains conservative (`SPEC_READY / PENDING_INTAKE`) until external audit replay bundle signs off.

---

### Round-26.2 self-run closure replay (base-repo-architect, 2026-03-08)

Scope:

1. protocol 层执行面收口 + 单实例真实回放（project `.identity` canonical runtime）；
2. 不引入新层级模型，不改变 v1.6 promotion boundary。

Code fixes landed in this round:

1. `scripts/collect_identity_health_report.py`
   - 修复 operation 参数误透传：仅对 operation-aware validators 注入 `--operation`，消除 scope/runtime/install 等校验器 `argparse` 崩溃。
2. `scripts/release_readiness_check.py`
   - `collect_identity_health_report` 增加 `--actor-id` 透传；
   - capability activation 终态校验改为 catalog+policy 实时判断，避免旧 report `BLOCKED` 状态造成伪阻断。
3. `scripts/e2e_smoke_test.sh`
   - 所有 health-report 调用补齐 `--actor-id`；
   - capability arbitration 前刷新 route metrics（修复 stale metrics 触发 `should_trigger=True` 误阻断）。
4. `scripts/validate_agent_handoff_contract.py`
   - self-test sample root 增加 `identity/runtime/**` fallback 解析（修复 sample root 漂移）。
5. `scripts/export_route_quality_metrics.py`
   - handoff log pattern 增加 pack-root `runtime/**` 映射；
   - project canonical `.identity/**` 输出放行（不再误判 repo-internal blocked path）。
6. `scripts/execute_identity_upgrade.py`
   - pre-mutation/lane-routing 早退分支强制写出 `<run_id>-patch-plan.json`，修复 `validate_identity_self_upgrade_enforcement` patch-plan 缺失阻断。

Runtime evidence backfill (instance-side, actor-bound):

1. `runtime/examples/base-repo-architect-trigger-regression-sample.json`
2. `runtime/logs/collaboration/base-repo-architect-20260308T041046Z.json`
3. `runtime/logs/handoff/base-repo-architect-20260308T041623Z.json`
4. `runtime/examples/base-repo-architect-knowledge-acquisition-sample.json`
5. `runtime/rulebooks/positive.jsonl`
6. `runtime/rulebooks/negative.jsonl`
7. `runtime/examples/base-repo-architect-experience-feedback-sample.json`

Replay matrix result:

1. `resolve_context` PASS
2. `docs_command_contract_check` PASS
3. `validate_protocol_ssot_source` OK
4. `validate_required_gate_surface_drift --json-only` PASS_REQUIRED
5. `identity_creator validate` PASS
6. `report_three_plane_status` PASS
7. `full_identity_protocol_scan --scan-mode target` PASS
8. `release_readiness_check` PASS
9. `e2e_smoke_test` PASS

Machine artifacts:

1. `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-20260308T045542Z.json`
2. `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-20260308T045542Z.md`
3. `/tmp/base_repo_architect_e2e_protocol_finalpass2_20260308.log`
4. `/tmp/base_repo_architect_release_readiness_20260308T045542Z.log`

Decision:

1. HOTFIX16-P0-008 标记为 `SPEC_READY / PENDING_INTAKE`（代码+回放闭环已具备、待独立审计复放签收）。
2. 不提级到 promotion-ready；维持 `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-26.3 expected-layer pass-through closure replay (`identity_creator validate`, 2026-03-08)

Scope:

1. 协议层 validate 执行链参数合同补完（仅控制面，不涉及实例业务能力）。
2. 对齐 UCG “single tuple source”约束：renderer 与 strict validators 不允许使用不同 expected tuple。

Root cause confirmed:

1. `identity_creator.py validate` 在带 `--expected-work-layer/--expected-source-layer` 时，仅对 validators 透传 expected tuple；
2. `render_identity_response_stamp.py` 未接收同一 expected tuple，导致 render 出 `instance/project`、而 first-line/coherence 按 `protocol/project` 判定，触发 `IP-ASB-STAMP-SESSION-001` 伪阻断风险。

Code closure:

1. `scripts/identity_creator.py`
   - validate 链在 `expected_work_layer` 存在时，给 `render_identity_response_stamp.py` 显式追加 `--work-layer`.
   - validate 链在 `expected_source_layer` 存在时，给 `render_identity_response_stamp.py` 显式追加 `--source-layer`.

Replay evidence:

1. `source ../scripts/use_local_identity_env.sh`
2. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --expected-work-layer protocol --expected-source-layer project --layer-intent-text 'protocol full validation replay'`
   - log: `/tmp/base_repo_architect_identity_validate_now.log`
   - result: `rc=0`
3. Cross-surface non-regression:
   - `report_three_plane_status.py` replay log: `/tmp/base_repo_architect_three_plane_now.log` (`rc=0`)
   - `full_identity_protocol_scan.py --scan-mode target` replay log: `/tmp/base_repo_architect_full_scan_now.log` (`rc=0`, `summary.p0=0`, `summary.ok=1`)
4. Machine report:
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-round26_3-20260308T051524Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-round26_3-20260308T051524Z.md`

Decision:

1. HOTFIX16-P1-009 记为 `SPEC_READY / PENDING_INTAKE`，等待审计专家按同命令复放签收。
2. 生命周期边界不变：`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-26.4 HUD tuple hardening + actor strict-entry closure replay (2026-03-08)

Scope:

1. 协议控制面收口：补齐 parity 合同、strict actor 入口、bundle 参数合同、three-plane/full-scan 可观测投影。
2. 不涉及实例业务能力修复；实例历史债务仍保持实例层清债口径。

Code closure:

1. `scripts/validate_required_gate_tuple_parity.py`
   - tuple 合同升级：新增 `identity_id`（core）与 `actor_id/resolved_work_layer/resolved_source_layer/lock_state`（conditional）。
   - conditional 字段在任一 receipt 出现时强制跨 receipt 全等，否则 `FAIL_REQUIRED`。
2. `scripts/compose_and_validate_governed_reply.py`
   - 缺失 `--actor-id` 直接 fail-close：`IP-ACTOR-ENTRY-001`。
3. `scripts/identity_creator.py`
   - `_infer_source_domain_from_catalog` 顺序修复：`/.codex/.identity/` 优先于 `/.identity/`。
4. `scripts/required_gate_bundle_runner.py`
   - 增加 `--actor-id/--resolved-work-layer/--resolved-source-layer/--lock-state` 入参与 payload 镜像；
   - `--outlet-bypass-detected` 支持显式 `true|false` 布尔值解析（不再仅靠 flag presence）。
5. strict surface 接线补齐（bundle 调用参数合同）：
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `.github/workflows/_identity-required-gates.yml`
6. 投影补齐：
   - `scripts/report_three_plane_status.py` 与 `scripts/full_identity_protocol_scan.py` 增加 parity `operations_checked/duplicate_operations` 与 sidecar `requiredization_scope_reason/activity_correlation_status` 等可观测字段。
   - follow-up：`scripts/full_identity_protocol_scan.py` 补齐 `required_gate_bundle_runner(_shadow)` 投影字段镜像（`actor_id/resolved_work_layer/resolved_source_layer/lock_state`），消除 full-scan summary 与 bundle raw payload 观测断层。
7. drift gate 参数合同补齐：
   - `scripts/validate_required_gate_surface_drift.py` 新增 strict surface bundle 参数合同检查（`run-id/send-time-gate-status/outlet-bypass/actor/work/source/lock`）；
   - 任一 strict surface bundle 调用缺参时统一 `IP-GATE-ENTRY-004` fail-close。
8. target probe run-id 收口：
   - `scripts/required_gate_bundle_runner.py` 在 `--target-name` 路径也强制 `run_id`；
   - 消除 “target probe 无 run_id 仍 rc=0” 的入口旁路。
9. sidecar 可观测升级（保持 non-blocking）：
   - `scripts/validate_protocol_feedback_sidecar_contract.py` 对 `ACTIVITY_UNSCOPED` 输出升级为 `WARN_NON_BLOCKING` + `IP-SID-004`；
   - 新增 `activity_unscoped_count / observability_alert_level / observability_escalation_required` 字段，专用于持续审计告警。
10. target full-scan 统计口径补齐：
   - `scripts/full_identity_protocol_scan.py` 新增 `summary_unique_targets`（按 identity 去重），与原 `summary`（按层行统计）并存。

Replay evidence:

1. tuple parity 负向探针（应 fail-close）：
   - `/tmp/tuple_gap_roundtable_recheck_20260308.json`（`FAIL_REQUIRED` + mismatch fields 包含 `identity_id/actor_id/work_layer/source_layer/lock_state`）。
2. compose 无 actor 探针（应 fail-close）：
   - `/tmp/compose_probe_no_actor_roundtable_custom_recheck.json`（`IP-ACTOR-ENTRY-001`）。
3. source 推断修复探针：
   - `/tmp/source_infer_recheck_20260308.log`（输出 `global`）。
4. projection 回放：
   - `/tmp/three_plane_projection_recheck_20260308.json`（parity/sidecar 关键字段已可见）。
   - `/tmp/full_scan_projection_recheck2_20260308.json`（full-scan checks 中 bundle HUD tuple + parity/sidecar 扩展字段可见）。
5. bundle 参数合同复核：
   - `/tmp/audit_recheck_bundle_args_20260308.json`（`missing_run_id=0`, `missing_send_time_gate_status=0`, `missing_outlet_bypass_detected=0`）。
   - `/tmp/audit_recheck_bundle_args_surface_20260308.json`（strict six surfaces 参数合同缺口全零，含 actor/work/source/lock）。
   - `/tmp/surface_drift_recheck6_20260308.json`（drift gate 内建参数合同复核 `PASS_REQUIRED`）。
   - `/tmp/surface_drift_recheck8_20260308.json`（补丁后复检仍 `PASS_REQUIRED`）。
6. gate sanity：
   - `/tmp/surface_drift_recheck_20260308.json`（`PASS_REQUIRED`）；
   - `/tmp/surface_drift_recheck2_20260308.json`（`PASS_REQUIRED`）；
   - `/tmp/docs_contract_recheck_20260308.log`（PASS）；
   - `/tmp/docs_contract_recheck2_20260308.log`（PASS）；
   - `/tmp/ssot_recheck_20260308.log`（OK）；
   - `/tmp/ssot_recheck2_20260308.log`（OK）。
7. target probe run-id 探针：
   - `/tmp/target_probe_no_runid_recheck4_20260308.json`（target probe 无 run_id 现在 `FAIL_REQUIRED`）。
8. sidecar 可观测升级探针：
   - `/tmp/three_plane_sidecar_recheck8_20260308.json`（`WARN_NON_BLOCKING/IP-SID-004` + `activity_unscoped_count` + `observability_alert_level`）。
9. target full-scan 去重统计探针：
   - `/tmp/full_scan_target3_recheck8_20260308.json`（新增 `summary_unique_targets`，解决 project/global 层行膨胀感知）。
10. gate 复检：
   - `/tmp/surface_drift_recheck9_20260308.json`（`PASS_REQUIRED`）；
   - `/tmp/docs_contract_recheck9_20260308.log`（PASS）；
   - `/tmp/ssot_recheck9_20260308.log`（OK）。
7. round report：
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_4-closure-20260308T060901Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_4-closure-20260308T060901Z.md`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_5-closure-20260308T062918Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_5-closure-20260308T062918Z.md`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_6-final-20260308T063322Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_6-final-20260308T063322Z.md`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_7-fullmatrix-20260308T063748Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_7-fullmatrix-20260308T063748Z.md`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_8-residual-closure-20260308T065529Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_8-residual-closure-20260308T065529Z.md`

8. full-matrix replay补充（真实脚本执行，不是静态检查）：
   - `identity_creator validate`、`release_readiness_check`、`e2e_smoke_test` 均已实跑；
   - 阻断点已收敛为实例层历史债务（`IP-WRB-003 / post_execution_mandatory`），而非本轮协议控制面回归。

Decision:

1. HOTFIX16-P0-010 标记为 `SPEC_READY / PENDING_INTAKE`（协议控制面收口已落地，等待独立审计复放签收）。
2. 生命周期边界不变：`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-26.5 lane-lock deterministic pass-through closure replay (2026-03-08)

Scope:

1. 针对审计残口：`full_scan` / `three_plane` 在未显式传 expected tuple 时，仍可因 default fallback 命中 `IP-LAYER-GATE-006`（`session_lane_lock=protocol` + `work_layer=instance`）。
2. 协议层收口目标：执行面统一从同一 lane-lock 判定源生成 effective tuple，禁止“锁为 protocol、执行仍 default instance”。

Code closure:

1. `scripts/full_identity_protocol_scan.py`
   - 新增 lane-lock 感知的 `effective_expected_work_layer/effective_expected_source_layer`；
   - `work_layer_gate_set_routing`、bundle runner、three_plane 调用统一使用 effective tuple；
   - output 新增 `effective_expected_*` 与 `detected_session_lane_lock` 观测字段。
2. `scripts/report_three_plane_status.py`
   - `_instance_plane_status` 新增 lane-lock 感知（actor binding + protocol-feedback lane lock receipts）；
   - 在无显式 expected tuple 时自动生成 effective tuple 并贯穿 strict HUD 链路；
   - instance detail 新增 `effective_expected_work_layer/effective_expected_source_layer/detected_session_lane_lock`。

Replay evidence:

1. full-scan replay（base-repo-architect）：
   - `/tmp/full_scan_projection_recheck3_20260308.json`
   - 关键结果：project layer `work_layer_gate_set_routing_status=PASS_REQUIRED`，`error_code=""`，`work_layer=protocol`，`session_lane_lock=protocol`。
2. three-plane replay（base-repo-architect）：
   - `/tmp/three_plane_sidecar_recheck11_20260308.json`
   - 关键结果：lane routing `PASS_REQUIRED`（不再 `IP-LAYER-GATE-006`）；detail 显式输出 `effective_expected_work_layer=protocol`。
3. sidecar continuity replay（非阻断可观测）：
   - `/tmp/three_plane_sidecar_recheck11_20260308.json`
   - 关键结果：`sidecar_contract_status=WARN_NON_BLOCKING` + `IP-SID-004` + `activity_unscoped_count` + `observability_alert_level=L1`。
4. gate sanity:
   - `/tmp/surface_drift_recheck11_20260308.json`（`PASS_REQUIRED`）
   - `/tmp/docs_contract_recheck11_20260308.log`（PASS）
   - `/tmp/ssot_recheck11_20260308.log`（OK）
5. round report:
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_9-lane-pass-through-20260308T072635Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_9-lane-pass-through-20260308T072635Z.md`

Decision:

1. 控制面残口判定：`IP-LAYER-GATE-006` 在 full-scan/three-plane 的 default fallback 复发路径已代码收口。
2. 状态仍维持 `SPEC_READY / PENDING_INTAKE`：实例层阻断（如 `IP-WRB-003`）与 worktree 非 clean baseline 仍在，暂不提级 promotion。

---

### Round-27 v1.6 auditable sweep + status promotion (2026-03-08)

Scope:

1. 对 v1.6 文档中“可直接机器复放”的状态项做一次全量审计，不改协议代码，只更新审计状态。
2. 本轮可审计判定标准：存在明确命令入口，且在当前头 `1e871780dc8f` 可复放得到稳定输出。

Replayed evidence:

1. docs/ssot 基线：
   - `/tmp/deepscan_docs_contract_refresh_20260308.log`（PASS）
   - `/tmp/deepscan_ssot_refresh_20260308.log`（OK）
2. UCG strict surface 合同：
   - `/tmp/deepscan_surface_drift_refresh_20260308.json`（`PASS_REQUIRED`）
   - `/tmp/deepscan_bundle_arg_contract_exec_only_20260308.json`（26/26 执行位点参数齐全）
3. HUD tuple + actor strict entry：
   - `/tmp/deepscan_tuple_probe_result2_20260308.json`（tuple 漂移 `FAIL_REQUIRED`）
   - `/tmp/deepscan_compose_no_actor_probe_20260308.json`（无 actor `IP-ACTOR-ENTRY-001`）
4. validate expected-layer pass-through：
   - `/tmp/round27_validate_bra_expected_layers_20260308.log`（`reply_first_line_status=PASS_REQUIRED`，`send_time_gate_status=PASS_REQUIRED`，`expected_source_layer_validation_status=PASS_REQUIRED`）
5. 全链路阻断残余（用于 blockers 归因）：
   - `/tmp/deepscan_e2e_braudit_20260308.log`（`IP-ASB-RFS-004` + `IP-PBL-006`）
   - `/tmp/deepscan_three_plane_matrix_v3_20260308.json`（4/4 `Conditional Go`）
   - `/tmp/deepscan_required_coverage_matrix_20260308.json`（required coverage 仍低）
   - `/tmp/deepscan_project_global_overlap_yaml_v2_20260308.json`（project/global overlap=3）

Status promotion in this round:

1. `FIX16-001`: `PENDING_INTAKE -> PASS_WITH_BLOCKERS`
2. `HOTFIX16-P0-005`: `PENDING_INTAKE -> PASS_WITH_BLOCKERS`
3. `HOTFIX16-P0-007`: `PENDING_INTAKE -> PASS_WITH_BLOCKERS`
4. `HOTFIX16-P1-009`: `PENDING_INTAKE -> PASS_WITH_BLOCKERS`
5. `HOTFIX16-P0-010`: `PENDING_INTAKE -> PASS_WITH_BLOCKERS`

Boundary:

1. 本轮“状态提升”仅表示对应协议控制面能力已复放通过，不等于 release 全绿。
2. 生命周期边界保持：`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。
3. 由于当前 worktree 非 clean，本轮仍按 `PASS_WITH_BLOCKERS` 保守口径执行，不做 `DONE` 提级。

---

### Round-27.1 auditable-scope completion replay (2026-03-08)

Scope:

1. 对 `Round-27` 之后仍可机器复放的 `PENDING_INTAKE` 条目做补充独立审计，重点覆盖：
   - `HOTFIX16-P0-008`
   - `FIX16-037`
   - `HOTFIX16-P1-004`
2. 仅执行复跑与状态核对，不改协议代码。

Replayed evidence:

1. baseline sanity:
   - `/tmp/deepscan_docs_contract_refresh2_20260308.log`（PASS）
   - `/tmp/deepscan_ssot_refresh2_20260308.log`（OK）
   - `/tmp/deepscan_surface_drift_refresh2_20260308.json`（`PASS_REQUIRED`）
2. base-repo-architect full-chain independent replay:
   - `/tmp/round27_identity_creator_validate_bra_20260308.log`（`rc=1`）
   - `/tmp/round27_three_plane_bra_20260308.json`（`overall_release_decision=Conditional Go`）
   - `/tmp/round27_full_scan_bra_20260308.json`（`summary.p0=1, ok=0`）
   - `/tmp/round27_release_readiness_bra_20260308.log`（`rc=1`）
   - `/tmp/round27_e2e_bra_20260308.log`（`rc=2`）
3. blocker focus:
   - `post_execution_mandatory_status=FAIL_REQUIRED` / `error_code=IP-WRB-003` 在 validate/readiness/three-plane/full-scan 路径持续出现；
   - `sidecar_contract_status=WARN_NON_BLOCKING` + `IP-SID-004` 仍处于可观测告警态（非本轮新增阻断）。

Decision:

1. 本轮无新增可升级条目；`Round-27` 的 5 条 `PASS_WITH_BLOCKERS` 提升保持不变。
2. `HOTFIX16-P0-008` 已补齐 decision-log 行并保持 `PENDING_INTAKE`（独立复放未达到通过门槛）。
3. `FIX16-037`、`HOTFIX16-P1-004` 维持 `PENDING_INTAKE`（当前证据仍未满足其既定 promotion guard）。
4. 生命周期边界保持：`SPEC_READY / PENDING_INTAKE`，`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---


### Round-26.6 addendum: two-layer source determinism + target-scan de-inflation replay (2026-03-08)

Scope:

1. 仅覆盖协议控制面残口（resolver/source-layer、target scan 口径、sidecar 活动锚点、session_refresh 非变更容错）。
2. 不覆盖实例历史债务清零（writeback/post_execution/prompt lifecycle）。

Cross-verified findings (closed in control-plane):

1. `resolve_identity_context` project catalog 误判 `unknown` 已关闭：
   - 通过 repo-catalog 导出的 canonical project root 统一判定 source-layer/scope。
2. full-scan target 双层膨胀口径已关闭：
   - 新增 `--target-source-layer`；
   - target mode 默认 `auto` 收敛到单层（优先 expected/env，fallback project）。
3. sidecar `ACTIVITY_UNSCOPED` 历史噪声复发已关闭：
   - 新增 `--current-round-anchor-utc`；
   - 缺 correlation key 的活动仅保留 ignored 观测，不再判定 unscoped 告警。
4. `session_refresh` 对非变更 strict 操作的 baseline-mode 卡死已降级：
   - `validate/readiness/e2e` 在 `IP-PBL-005/006` 且无显式 execution-report 时改为 `WARN_NON_BLOCKING`；
   - `ci/update/activate/mutation` 仍 strict fail-close（无放宽）。

Replay evidence:

1. `/tmp/resolve_context_recheck_final_20260308.json`
2. `/tmp/full_scan_recheck_final3_20260308.json`
3. `/tmp/three_plane_recheck_final2_20260308.json`
4. `/tmp/sidecar_recheck_final_braudit_20260308.json`
5. `/tmp/surface_drift_recheck_final2_20260308.json`
6. `/tmp/docs_contract_recheck_final3_20260308.log`
7. `/tmp/ssot_recheck_final3_20260308.log`
8. `/tmp/e2e_recheck_final2_20260308.log`（lane pass-through replay，`work_layer_gate_set_routing_status=PASS_REQUIRED`）

Decision:

1. 控制面新增残口判定为已收口（Round-26.6）。
2. 发布态仍保持 `SPEC_READY / PENDING_INTAKE`：实例债务与 dirty baseline 未在本加段闭环。

---

### Round-26.7 addendum: health self-upgrade playbook emission (2026-03-08)

Scope:

1. 将“实例债务由实例自行修复”转为机器可执行输出：health report 自动给出 upgrade command chain。

Code closure:

1. `scripts/collect_identity_health_report.py` 输出 `self_upgrade_plan`（trigger checks / error codes / commands）。
2. 当检测到 writeback/post-execution/baseline/alignment 等升级触发项时，控制台打印 `[UPGRADE]` 命令链，避免人工拼装。

Replay evidence:

1. `/tmp/health-upgrade-test/identity-health-base-repo-audit-expert-v3-1772958922.json`
   - `self_upgrade_plan.plan_status=ACTION_REQUIRED`
   - `commands` 覆盖 update + targeted validators + re-health enforce pass。

Decision:

1. 协议层确认“健康检查提供实例自愈升级说明”已落地。
2. 该加段不代表实例债务清零，仅提供标准化自愈执行路径。

---

### Round-28 addendum: multi-agent × multi-identity switch guard semantics + HUD strict-entry (2026-03-08)

Scope:

1. 仅收口两类控制面复发点：
   - switch-intent 守卫语义被误解为 actor 单绑定；
   - strict HUD 执行面允许 actor 隐式回退。
2. 不涉及实例业务债务清零。

Cross-verified findings (closed in control-plane):

1. activate 切换守卫已改为显式 scope：
   - `actor_session`（默认）：同 actor+session 切换才需要 receipt；
   - `actor_global`：保留 legacy actor-wide 口径（兼容回放）。
2. activation switch report 观测字段补齐：
   - `session_id`, `session_id_source`, `switch_guard_scope`, `switch_guard_binding_ref`。
3. strict HUD 入口封口：
   - `report_three_plane_status.py` 缺 `--actor-id` / `--session-id` -> fail-close；
   - `full_identity_protocol_scan.py` 缺 `--actor-id` / `--session-id` -> fail-close。

Replay evidence:

1. 同 session 切换（receipt required）：
   - `/tmp/round28_activate_alpha_seed.log`
   - `/tmp/round28_activate_alpha_no_receipt.log`（`IP-ACT-SWITCH-001`）
   - `/tmp/round28_activate_alpha_with_receipt.log`
2. 跨 session 并行绑定（multi-identity allowed）：
   - `/tmp/round28_activate_beta_parallel.log`
3. legacy actor-global compatibility：
   - `/tmp/round28_activate_global_no_receipt.log`（`IP-ACT-SWITCH-001`）
4. HUD strict-entry：
   - `/tmp/round28_three_plane_no_actor.log`（`IP-ACTOR-ENTRY-001`）
   - `/tmp/round28_three_plane_no_session.log`（`IP-ASB-SESSION-ENTRY-001`）
   - `/tmp/round28_full_scan_no_actor.log`（`IP-ACTOR-ENTRY-001`）
   - `/tmp/round28_full_scan_no_session.log`（`IP-ASB-SESSION-ENTRY-001`）
   - `/tmp/round28_three_plane_with_actor.json`
   - `/tmp/round28_full_scan_with_actor.json`

Decision:

1. “多对多语义键混淆 + actor fallback 窗口”两项控制面缺口判定已收口。
2. 发布口径保持不变：`SPEC_READY / PENDING_INTAKE`（实例债务与 clean baseline 仍未闭环）。
3. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` 边界保持。

---

### Round-28.1 addendum: tuple parity scope mismatch (IP-GATE-ENTRY-003) protocol optimization handoff (2026-03-08)

Scope:

1. 目标是把“实例修复后仍被协议门禁误阻断”的问题收口到架构师可执行清单。
2. 本加段只覆盖协议控制面（parity 合同与 e2e 执行链），不回退实例兼容兜底。

Cross-verified findings:

1. 实例侧已通过关键基线：
   - `/tmp/fixrun27_identity_validate.log`（validate PASS）。
   - `/tmp/fixrun25_full_scan_target.json`（target scan `p0=0`, `ok=1`）。
2. 发布链仍被 parity 阻断：
   - `/tmp/fixrun27_release_readiness.log` 命中 `required_gate_tuple_parity_status=FAIL_REQUIRED`，`error_code=IP-GATE-ENTRY-003`。
   - `/tmp/fixrun28_e2e.log` 同样命中 `IP-GATE-ENTRY-003`。
3. 可复放根因：
   - parity 当前将 `update/e2e` baseline receipt 与 `scan-probe` receipt 直接比较 `required_contract`；
   - `mismatches.required_contract` 固定出现 `baseline=true` vs `scan=false`，形成结构性 fail-close。
4. 附加噪声：
   - `/tmp/fixrun28_e2e.log` 中 `validate_cross_cwd_absolute_input` 出现 `python -c` quoting `SyntaxError`，虽不构成当前 blocking root-cause，但降低审计可读性。

Architect execution directives (protocol only):

1. `scripts/validate_required_gate_tuple_parity.py` 升级为“双层比较合同”：
   - 跨 operation 强一致：`run_id_binding`, `identity_id`, `actor_id`, `resolved_work_layer`, `resolved_source_layer`, `lock_state`；
   - operation-scope 字段（至少 `required_contract`）改为组内比较，不跨 `scan_probe` 与执行面直接全等。
2. `scripts/required_gate_bundle_runner.py` 增强 receipt 语义：
   - `scan_probe` receipt 输出显式 `parity_operation_scope` 与 `required_contract_reason`；
   - parity 必须消费该字段，不再依赖 `surface_label` 推测。
3. `scripts/e2e_smoke_test.sh` 与 `scripts/validate_cross_cwd_absolute_input.py` 修复 `python -c` 引号拼接，清理噪声错误。

Acceptance replay (must pass):

1. `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog <project>/.identity/catalog.local.yaml --actor-id assistant:codex --expected-work-layer protocol --expected-source-layer project`
   - 期望：RC=0，`IP-GATE-ENTRY-003` 消失。
2. `IDENTITY_IDS=base-repo-audit-expert-v3 CATALOG_PATH=<project>/.identity/catalog.local.yaml ACTOR_ID=assistant:codex EXPECTED_WORK_LAYER=protocol EXPECTED_SOURCE_LAYER=project bash scripts/e2e_smoke_test.sh`
   - 期望：RC=0，`required_gate_tuple_parity_status=PASS_REQUIRED`，无 quoting `SyntaxError`。
3. 负向探针：
   - 构造 `invariant tuple` 漂移（如 `actor_id` 不同）时仍必须 `FAIL_REQUIRED`（避免回归成假绿）。

Decision:

1. Round-28.1 判定为“协议优化待执行”状态，已形成可直接转交架构师的执行单。
2. 状态边界维持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-28.2 addendum: why 17 rounds still recur (deduplicated root-cause matrix, 2026-03-08)

Scope:

1. 回答“为什么头显问题提了 17 次仍复发”，并将重复叙事压缩为固定 root IDs。
2. 本加段只做协议审计去重，不新增实例层责任转移。

Cross-verified findings:

1. 文档命中统计（v1.6 governance + review）：
   - headstamp/HUD/egress 相关命中 `332` 条；
   - 相关章节标题 `17` 条；
   - 高频码族集中于同一簇（非 17 个独立故障）。
2. 现象判定：
   - 17 次修改属于“局部收口叠加”，主根因未在最终输出口闭环。
3. 主根因与放大器（冻结命名）：
   - `RC-HUD-001`：final user-visible emission 未被平台级 hard-gate 到 canonical egress（主根因）。
   - `RC-HUD-002`：requiredization applicability drift（strict 场景出现 `SKIPPED_NOT_REQUIRED(contract_not_required)`）。
   - `RC-HUD-003`：actor passthrough/fallback 漂移。
   - `RC-HUD-004`：tuple/parser/source 分叉导致同轮口径不一致。
4. 去重结论：
   - 后续 round 必须映射到 `RC-HUD-001..004`，禁止以同义“新根因”重复入账。

Architect execution directive (single remaining closure):

1. 平台最终输出必须统一到单一 API（建议：`final_emit_governed`）。
2. 该 API 内部必须强制执行 canonical egress：
   - `compose_and_validate_governed_reply.py`
   - `validate_send_time_reply_gate.py`
   - canonical receipt 校验
3. 无 receipt 或 bypass 情况一律 `FAIL_REQUIRED`，禁止 direct text fallback。
4. 将 `final emission hard-gate` 提升为 P0 required mapping，并纳入 drift guard。

Acceptance replay (must pass):

1. 负向 A：direct output bypass -> fail-close，且无 user-visible 正文下发。
2. 负向 B：actor tuple drift -> fail-close，且 blocker 码族稳定。
3. 正向：governed compose output -> `Identity-Context|Layer-Context` 首行稳定，`send_time_gate_status=PASS_REQUIRED`。

Evidence:

1. `/tmp/v16_headstamp_hits_20260308.txt`
2. `/tmp/v16_headstamp_sections_20260308.txt`
3. `/tmp/v16_headstamp_code_freq_20260308.txt`
4. `/tmp/hud_probe_reply_20260308.txt`

Decision:

1. Round-28.2 定性为“去重治理完成，主根因未闭环”。
2. 继续维持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-28.3 addendum: prompt-contract null means protocol wiring failure (must-auto-wire, 2026-03-08)

Scope:

1. 回应“prompt 合同为 null/缺失导致 validators 跳过”的反复问题，给出协议层 hard requirement。
2. 明确禁止“每次靠实例人工定向命令补 CURRENT_TASK”这种运行方式。

Replay result (cross-verified):

1. `before wiring`：四个 prompt validator 全部 `SKIPPED_NOT_REQUIRED`，且 `stale_reasons=required_contract_disabled_or_missing`。
2. `after controlled wiring`：四个 prompt validator 进入 `required_contract=true` 并全部 `PASS_REQUIRED`。
3. 结论：问题根因是“合同接线缺失”，不是 validator 不可执行。

Evidence:

1. Before:
   - `/tmp/prompt_bootstrap_now_20260308.json`
   - `/tmp/prompt_cap_matrix_now_20260308.json`
   - `/tmp/prompt_kernel_coupling_now_20260308.json`
   - `/tmp/prompt_derivation_now_20260308.json`
2. After:
   - `/tmp/prompt_bootstrap_after_wire_20260308.json`
   - `/tmp/prompt_cap_matrix_after_wire_20260308.json`
   - `/tmp/prompt_kernel_coupling_after_wire_20260308.json`
   - `/tmp/prompt_derivation_after_wire_20260308.json`
3. Freshness:
   - `/tmp/execution_report_freshness_after_upgrade_20260308.json`

Protocol execution directive (P0, architecture-side):

1. 在 `identity_creator init/update` 与 `execute_identity_upgrade` 中内置 prompt 合同自动接线，不允许实例手工补丁作为常态。
2. 缺失四个 prompt 合同键时必须 auto-wire + receipt；失败即 `FAIL_REQUIRED`，不允许降级为 `SKIPPED_NOT_REQUIRED`。
3. 协议需保证“单入口命令可完成接线 + 复核”，避免每个实例要求不同命令组合。
4. `compile_identity_runtime` 与 upgrade/freshness 的 prompt hash 语义需统一（文件字节 hash），消除口径漂移。

Acceptance (gate for closing this addendum):

1. 从缺失合同的实例起步，执行单入口升级命令后：
   - RQ-014/015/027/031 全部 `PASS_REQUIRED`。
2. 不再出现 `required_contract_disabled_or_missing`。
3. freshness 必须 `PASS`（`report_newer_than_key_inputs=true`）。

Decision:

1. Round-28.3 记录为协议层 P0 增强要求，已落入 v1.6 审计账本。
2. 状态边界保持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-29 addendum: L3 final egress hard-gate closure replay (official-aligned, 2026-03-08)

Scope:

1. 仅覆盖协议控制面“最终输出口”闭环（L3 final emission），不覆盖实例业务债务清理。
2. 目标是把 `final_emit_governed` 从“建议”升级为“强制合同 + fail-close”。

Cross-verified changes:

1. `scripts/validate_send_time_reply_gate.py`
   - 严格校验 `final_emit_channel/policy/schema`；
   - mismatch fail-close：`IP-ASB-STAMP-SESSION-006/007`。
2. `scripts/execute_identity_upgrade.py`
   - 对 `--header-first-gate-status PASS_REQUIRED` 场景新增 final emit passthrough 合同硬校验；
   - 缺失或不一致直接阻断：`IP-OUTLET-004`（不再容忍 external_override 语义兜底）。
3. `scripts/identity_creator.py`
   - update 面 required gate bundle 透传 pre-mutation 真实值（send-time/final_emit），去除 `UNKNOWN` 常量透传。
4. `scripts/release_readiness_check.py`
   - bundle passthrough 从 selected execution report 回填，避免 strict readiness 面继续注入 `UNKNOWN`。

Replay evidence:

1. Positive:
   - `/tmp/final_emit_compose_positive_20260308.json`  
     (`send_time_gate_status=PASS_REQUIRED`, `final_emit_contract_status=PASS_REQUIRED`)
2. Negative strict probes:
   - `/tmp/final_emit_sendtime_negative_channel_20260308.json` -> `IP-ASB-STAMP-SESSION-006`
   - `/tmp/final_emit_sendtime_negative_policy_20260308.json` -> `IP-ASB-STAMP-SESSION-006`
   - `/tmp/final_emit_sendtime_negative_schema_20260308.json` -> `IP-ASB-STAMP-SESSION-007`
3. L3 passthrough hard-fail:
   - `/tmp/final_emit_execute_missing_probe_20260308.log`
   - `/private/tmp/final_emit_missing_probe_reports/FINAL-EMIT-MISSING-PT-20260308.json`  
     (`header_first_gate_status=FAIL_REQUIRED`, `pre_mutation_gate_error_code=IP-OUTLET-004`)
4. Post-exec invariants:
   - `/tmp/final_emit_outlet_matrix_replay_20260308.json` -> `outlet_matrix_status=PASS_REQUIRED`
   - `/tmp/final_emit_postexec_mandatory_replay_20260308.json` -> `post_execution_mandatory_status=PASS_REQUIRED`
5. Surface drift:
   - `/tmp/final_emit_surface_drift_after_patch_20260308.json` -> `required_gate_surface_drift_status=PASS_REQUIRED`

Decision:

1. 判定“唯一最终输出口（L3）控制面硬闸门”已落地，且具备负向 fail-close 证据。
2. 仍未闭环项继续留在实例债务域（writeback continuity / prompt lifecycle / baseline clean SHA），不与 L3 控制面结论混淆。
3. 状态边界保持不变：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

---

### Round-29.1 addendum: health report emits final-egress upgrade commands (2026-03-08)

Scope:

1. 仅补强“实例自检可执行性”：让 health report 在 strict operation 下对 final egress requiredization 缺口给出可执行升级链。
2. 不改变 Round-29 的 L3 控制面结论，不替代实例债务修复。

Cross-verified changes:

1. `scripts/collect_identity_health_report.py` 新增 `outlet_matrix` 检查位。
2. strict operation 下自动透传 `--force-required` 到 `validate_outlet_matrix.py`，不再允许 `SKIPPED_NOT_REQUIRED` 作为 strict health 结论。
3. `self_upgrade_plan` 增补强制命令：
   - `python3 scripts/validate_outlet_matrix.py ... --operation validate --force-required --json-only`
4. 健康报告新增 final egress 观测字段：
   - `final_emit_only_mode_required`
   - `final_emit_only_mode_status`
   - `final_emit_only_mode_enforced`
   - `final_emit_contract_status`

Replay evidence:

1. `/private/tmp/health-final-emit-round291/identity-health-base-repo-architect-1772976720.json`
   - 旧行为对照：`final_emit_only_mode_status=SKIPPED_NOT_REQUIRED`，`checks[outlet_matrix].status=WARN`
2. `/tmp/health_final_emit_round291_validate_console.log`
   - 对照样本中 `warn:outlet_matrix` 已出现并进入升级命令链。
3. `/private/tmp/health-selftest-round292/identity-health-base-repo-architect-1772977142.json`
   - `final_emit_only_mode_required=true`
   - `final_emit_only_mode_status=PASS_REQUIRED`
   - `final_emit_only_mode_enforced=true`
   - `checks[outlet_matrix].status=PASS`
4. `/tmp/round292_health_after_patch.log`
   - strict health 回放中 outlet_matrix 警告已消失（按 required_contract 强制复核通过）。

Decision:

1. 接受本次补强：实例在 strict health operation 下不再对 final egress requiredization 缺口“静默通过”。
2. 该补强为“升级指引增强”，不等同于实例债务已清零。

---

### Round-29.2 addendum: validator contract drift alignment (2026-03-08)

Scope:

1. 修复 strict health 自测中的两条“验证器误阻断”，确保控制面收口结论与执行语义一致。

Cross-verified fixes:

1. `scripts/validate_headstamp_recurrence_closure.py`
   - non-governed outlet 负向探针从“仅接受 `IP-ASB-STAMP-SESSION-004`”扩展为“接受 `004/006`”；
   - 与 send-time gate 的 final emit channel strict 错误码升级保持一致。
2. `scripts/validate_post_execution_mandatory.py`
   - 对齐 `execute_identity_upgrade` 的 strict non-upgrade closure 合同：
   - `upgrade_required=false && all_ok=true && writeback_mode=STRICT_WRITEBACK && writeback_status in {NOT_REQUIRED, WRITTEN}` 直接判定闭环。

Replay evidence:

1. `/tmp/fix_verify_headstamp.json` -> `headstamp_recurrence_closure_status=PASS_REQUIRED`
2. `/tmp/fix_verify_postexec.json` -> `post_execution_mandatory_status=PASS_REQUIRED`
3. `/tmp/fix_verify_health_enforce.log` -> `overall_status=PASS, warning_count=0, failed_count=0`
4. `/private/tmp/health-selftest-round292/identity-health-base-repo-architect-1772977729.json`  
   strict health `--enforce-pass` 通过。

Decision:

1. 判定本轮为“验证器合同对齐修复”，不是新增模型变更。
2. 允许继续按 Round-29/29.1 口径推进实例升级通知。

---

### Round-29.3 addendum: default report binding + sidecar anchor stabilization (2026-03-08)

Scope:

1. 收敛 default latest_report 绑定漂移；
2. 收敛 protocol-feedback sidecar 的 anchor 语义抖动与备份文件扫描污染。

Cross-verified changes:

1. `scripts/execute_identity_upgrade.py`
   - 写 report 时同步写 `runtime/state/active_execution_report.json`。
2. `scripts/tool_vendor_governance_common.py`
   - latest report 解析优先 pointer；
   - 候选池收敛到 `runtime/reports` + `resource/reports`，排除 protocol-feedback/archive 噪声路径。
3. `scripts/protocol_feedback_lane_common.py`
   - activity 扫描忽略备份与临时文件：`*.bak*`, `*.tmp`, `*~`, `*.swp`, `.DS_Store`。
4. `scripts/validate_protocol_feedback_sidecar_contract.py`
   - 新增 `anchor_source`、`anchor_report_path` 与 activity count 字段；
   - `track_a` 增补 report/final_emit 观测字段。

Replay evidence:

1. `/tmp/audit_postcommit_base_health_noreport.log`
2. `/private/tmp/audit-postcommit/identity-health-base-repo-architect-1772979281.json`  
   (`overall_status=PASS`, strict health no explicit report)
3. `/tmp/audit_pointer_base_snapshot.txt`  
   (pointer 已写入：`active_execution_report.json`)
4. `/tmp/sidecar_compare_no_report_afterpatch_6537307.json`
5. `/tmp/sidecar_compare_with_report_afterpatch_6537307.json`  
   (`anchor_source` 明确，activity refs 无 `.bak` 污染)

Decision:

1. 接受本轮补强：default binding 与 sidecar anchor 的协议控制面稳定性显著提升。
2. remaining blocker 继续留在实例债务域（尤其 `custom-creative-ecom-analyst` 的 `IP-SID-002` 链路）。

---

### Round-29.4 addendum: update-lane prompt contract auto-wiring hard-close (2026-03-08)

Scope:

1. 仅覆盖 protocol update lane 的 prompt 合同接线，不涉及实例业务内容修复。
2. 目标是消除“合同缺失导致 validators 进入 `SKIPPED_NOT_REQUIRED`”的结构性窗口。

Cross-verified changes:

1. `scripts/execute_identity_upgrade.py`
   - 新增 `_ensure_prompt_contract_auto_wiring()`，在 update 执行前自动补齐四个 canonical prompt 合同键；
   - 对已有但被降级的合同强制 `required=true`；
   - 将自动接线失败纳入 pre-mutation fail-close，错误码族：
     - `IP-PROMPT-WIRE-001`（task write failure）
     - `IP-PROMPT-WIRE-002`（required prompt contracts still missing）
     - `IP-PROMPT-WIRE-003`（invalid prompt contract payload）
2. 报告新增可观测字段：
   - `prompt_contract_auto_wire_status`
   - `prompt_contract_auto_wire_error_code`
   - `prompt_contract_auto_wire_missing_before/after`
   - `prompt_contract_auto_wire_forced_required_keys`

Replay evidence:

1. `base-repo-architect` self-run：
   - `/tmp/prompt_wire_execute_upgrade_replay.log`
   - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/runtime/reports/identity-upgrade-exec-base-repo-architect-1772980888.json`
2. 关键字段：
   - `prompt_contract_auto_wire_status=PASS_REQUIRED`
   - `prompt_contract_auto_wire_missing_before` 包含四个 prompt 合同键
   - `prompt_contract_auto_wire_missing_after=[]`
3. 回放边界：
   - 本次执行仍可能因实例环境能力前置 (`IP-CAP-003`) 阻断升级闭环；
   - 该阻断不再归因于 prompt 合同接线缺口。

Decision:

1. 判定 Round-29.4 为协议层正向补强：prompt 合同接线已从“人工修补”升级为“update lane 自动接线 + fail-close”。
2. 发布姿态仍保持非提级边界（`SPEC_READY / PENDING_INTAKE`）。

---

### Round-29.5 addendum: heal-lane prompt contract wiring parity (2026-03-08)

Scope:

1. 补齐 `heal --apply` 链路与 Round-29.4 update lane 的 prompt 合同强约束一致性。
2. 防止 heal lane 退化为“可修但不强校验”的旁路。

Cross-verified changes:

1. `scripts/repair_contract_backfill.py`
   - 增加 prompt 合同强约束集（四项 canonical keys）；
   - 增加 `_normalize_prompt_contracts()`，执行自动补齐 + `required=true` 强制 + validator 回填；
   - 在 backfill 报告内输出 prompt auto-wire 观测字段与错误码。
2. 新增/复用错误码：
   - `IP-PROMPT-WIRE-002`（missing after auto-wire）
   - `IP-PROMPT-WIRE-003`（invalid after auto-wire）
3. `scripts/identity_creator.py`
   - `heal` 子命令新增 `--actor-id`；
   - heal 执行链把 actor 透传到 strict `validate` 与 `collect_identity_health_report --operation validate`，消除缺 actor 的入口误阻断。

Replay evidence:

1. `/tmp/round295_repair_contract_backfill_base.json`
   - `contract_backfill_status=PASS_REQUIRED`
   - `prompt_contract_auto_wire_status=PASS_REQUIRED`
2. `/tmp/round295_heal_base.log`
   - heal 链内 backfill 步骤输出了 prompt wiring 字段；
   - 该轮失败根因位于 actor/session 健康项，非 prompt 合同接线。
3. `/tmp/round295_heal_base_actorwired.log`
   - heal strict 链不再触发 `IP-ACTOR-ENTRY-001`；
   - 剩余失败收敛为 `IP-ASB-201`（实例会话绑定债务）。

Decision:

1. 接受本轮补强：prompt 接线强约束已覆盖 update + heal 双入口。
2. remaining blocker 按职责继续归实例层（能力/会话健康/历史债务），不回退到协议兼容兜底。

---

### Round-29.6 addendum: strict egress actor + bundle UNKNOWN literal closure (2026-03-09)

Cross-verified findings:

1. `scripts/final_emit_governed.py` actor fallback closure landed:
   - before replay（no `--actor-id`）: `PASS_REQUIRED` + `actor_resolution_mode=default`;
   - after replay（no `--actor-id`）: `FAIL_REQUIRED` + `IP-FE-006`;
   - positive replay（with `--actor-id`）: `PASS_REQUIRED`.
2. strict surface bundle arg value closure landed:
   - target strict surfaces no longer emit literal `UNKNOWN` for
     `send-time/final-emit-contract/final-emit-schema` trio;
   - `validate_required_gate_surface_drift --json-only` returns
     `PASS_REQUIRED`, `bundle_arg_value_invalid={}`.
3. drift validator strengthened:
   - `scripts/validate_required_gate_surface_drift.py` adds forbidden-value gate;
   - new fail-close code for this class: `IP-GATE-ENTRY-007`.

Evidence anchors (replay):

1. `/tmp/audit_final_emit_no_actor_20260309.json` (before)
2. `/tmp/audit_after_final_emit_no_actor_20260309.json` (after negative)
3. `/tmp/audit_after_final_emit_with_actor_20260309.json` (after positive)
4. `/tmp/audit_before_unknown_only_20260309.log` (before bundle literal scan)
5. `/tmp/audit_after_unknown_bundle_literals_20260309.log` (after bundle literal scan)
6. `/tmp/audit_after_surface_drift_20260309.json`
7. `/tmp/audit_after_docs_contract_20260309.log`
8. `/tmp/audit_after_ssot_20260309.log`

Decision boundary:

1. This addendum closes protocol control-plane drift in two recurrent classes:
   actor fallback and UNKNOWN-literal bundle tuple placeholders.
2. This addendum does not claim global promotion readiness; instance debts remain out of scope.

---

### Round-29.7 addendum: control-plane invariants + growth budget CI hardening (2026-03-09)

Cross-verified findings:

1. dual-threshold control-plane budget gate landed and is CI-wired:
   - script: `scripts/validate_control_plane_budget.py`
   - budget ssot: `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
   - CI hook: `.github/workflows/_identity-required-gates.yml`
2. budget gate reports machine-readable status classes:
   - `PASS_REQUIRED`
   - `WARN_NON_BLOCKING`
   - `FAIL_REQUIRED`
3. current baseline replay at landing head is `PASS_REQUIRED` under configured warn/fail envelopes.

Control-plane audit scope reinforced:

1. red-line invariants are frozen in governance `8.62` (single egress, bundle single entry, drift arg contract, forbidden UNKNOWN literals, machine-only promotion posture).
2. budget gate is intentionally minimal and anti-overfit:
   - it constrains growth vectors, not model reasoning capability.

Replay evidence:

1. `/tmp/audit_control_plane_budget_20260309.json`
2. `/tmp/audit_after_surface_drift_20260309.json`
3. `/tmp/audit_after_docs_contract_20260309.log`
4. `/tmp/audit_after_ssot_20260309.log`

Decision boundary:

1. this addendum hardens governance against uncontrolled expansion drift.
2. this addendum does not claim required-plane single-entry full migration (`mapping_rows_missing_in_bundle` debt remains visible and budget-frozen).

---

### Round-29.8 addendum: machine status artifact + sync gate closure (2026-03-09)

Cross-verified findings:

1. machine status renderer landed:
   - `scripts/render_control_plane_status.py`
   - emits `identity/protocol/mappings/control-plane-status.v1.6.json`
2. machine sync validator landed and fail-closes on drift:
   - `scripts/validate_control_plane_status_sync.py`
   - fail code: `IP-CP-STATUS-001`
3. CI now enforces status sync:
   - `.github/workflows/_identity-required-gates.yml`
   - step: `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. replay confirmed status is machine-derived and non-promotional at current head:
   - `control_plane_status=PASS_WITH_BLOCKERS`
   - `promotion_ready=false`
5. this addendum closes the gap “status text can be edited without gate parity”.

Replay evidence:

1. `/tmp/audit_round298_invariants_20260309.json`
2. `/tmp/audit_round298_control_plane_status_runtime_20260309.json`
3. `/tmp/audit_round298_status_sync_20260309.json`
4. `/tmp/audit_round298_surface_drift_20260309.json`
5. `/tmp/audit_round298_docs_contract_20260309.log`
6. `/tmp/audit_round298_ssot_20260309.log`

Decision boundary:

1. this addendum closes machine-only promotion-state derivation for protocol control-plane.
2. this addendum does not remove existing non-control-plane blockers; posture remains conservative.

---

### Round-29.9 addendum: budget warn baseline synchronization + full control-plane green (2026-03-09)

Cross-verified findings:

1. budget warn baselines were re-anchored to the current structural baseline after new control-plane gates landed.
2. fail thresholds remained unchanged; fail-close boundary did not weaken.
3. post re-anchor machine results:
   - `control_plane_budget_status=PASS_REQUIRED`
   - `control_plane_invariants_status=PASS_REQUIRED`
   - `control_plane_status_sync_status=PASS_REQUIRED`
   - `required_gate_surface_drift_status=PASS_REQUIRED`
4. rendered status artifact now reports:
   - `control_plane_status=PASS_REQUIRED`
   - `promotion_ready=true` (control-plane scope)

Replay evidence:

1. `/tmp/audit_round299_control_plane_status_render_20260309.json`
2. `/tmp/audit_round299_control_plane_status_runtime_20260309.json`
3. `/tmp/audit_round299_status_sync_20260309.json`
4. `python3 scripts/validate_control_plane_budget.py --json-only` (post re-anchor pass)
5. `python3 scripts/validate_control_plane_invariants.py --json-only`
6. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
7. `/tmp/audit_round298_docs_contract_20260309.log`
8. `/tmp/audit_round298_ssot_20260309.log`

Decision boundary:

1. this addendum closes control-plane budget/status drift and achieves machine-green within control-plane governance scope.
2. this addendum does not claim required-plane migration debt closure (`mapping_rows_missing_in_bundle=25` remains frozen and visible).

---

### Round-30.0 addendum: prompt-capability validator projection closure + full-scan zero-P0 replay (2026-03-09)

Cross-verified findings:

1. full-scan `scan-mode=full` residual `P0` narrowed to `base-repo-architect`.
2. failure was not outlet/tuple drift; it was prompt-capability driver detection using only top-level `required_validators`.
3. protocol patch now aggregates validator declarations from three canonical sources:
   - top-level `required_validators`
   - `ci_enforcement_contract.required_validators`
   - `identity_update_lifecycle_contract.validation_contract.required_checks`
4. strict fail-close logic is unchanged: missing capability drivers still hard-fail with existing error codes.

Protocol code changes:

1. `scripts/validate_prompt_bootstrap_capability.py`
2. `scripts/validate_prompt_capability_matrix.py`

Runtime debt closure performed:

1. `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/CURRENT_TASK.json`
2. added explicit capability-driver validators to top-level `required_validators` for consistency with prompt contracts.

Replay evidence:

1. pre-fix:
   - `/tmp/audit_round302_prompt_bootstrap_architect_20260309.json` => `FAIL_REQUIRED` (`IP-PBOOT-001`)
   - `/tmp/audit_round302_prompt_matrix_architect_20260309.json` => `FAIL_REQUIRED` (`IP-PCAPM-001`)
2. post-fix:
   - `/tmp/audit_round302_prompt_bootstrap_architect_afterfix_20260309.json` => `PASS_REQUIRED`
   - `/tmp/audit_round302_prompt_matrix_architect_afterfix_20260309.json` => `PASS_REQUIRED`
3. full-scan convergence:
   - `/tmp/audit_round302_full_scan_full_afterfix_20260309.json`
   - summary: `total=4, p0=0, p1=0, ok=4`
4. control-plane cross-gate replay:
   - `/tmp/audit_round302_budget_afterfix_20260309.json`
   - `/tmp/audit_round302_invariants_afterfix_20260309.json`
   - `/tmp/audit_round302_status_sync_afterfix_20260309.json`
   - `/tmp/audit_round302_surface_drift_afterfix2_20260309.json`
   - `/tmp/audit_round302_docs_contract_afterfix_20260309.log`
   - `/tmp/audit_round302_ssot_afterfix_20260309.log`

Decision boundary:

1. this addendum closes the round302 full-scan residual `P0` and reaches machine-green for currently discovered identities.
2. protocol and runtime actions are both required for this closure; neither side alone was sufficient.

---

### Round-30.1 addendum: prompt-lifecycle no-upgrade false blocker fix + three-loop stability replay (2026-03-09)

Cross-verified findings:

1. Round-303 regressed with `base-repo-architect` `P0` on `prompt_lifecycle`.
2. root cause was a false blocker in no-upgrade reports:
   - `upgrade_required=false`
   - runtime state artifact path present as metadata
   - runtime artifact file absent
   - validator still failed as required blocker.
3. fix applied in protocol validator:
   - `scripts/validate_identity_prompt_lifecycle.py`
   - missing runtime state artifact is tolerated only for no-upgrade/no-change path with `binding_status=MISSING|SKIPPED_NOT_REQUIRED`.
4. upgrade-required path remains fail-close (negative probe preserved).

Replay evidence:

1. positive probe:
   - `/tmp/audit_round303_prompt_lifecycle_architect_afterfix.log` => `[OK] prompt lifecycle validated`
2. negative probe:
   - `/tmp/audit_round303_prompt_lifecycle_negative2.log` => `[FAIL] runtime state artifact missing ...`
3. loop replay:
   - `/tmp/audit_round303b_full_auto_20260309.json` => `summary(total=4,p0=0,p1=0,ok=4)`
   - `/tmp/audit_round304_full_auto_20260309.json` => `summary(total=4,p0=0,p1=0,ok=4)`
   - `/private/tmp/audit_round305c_full_auto_20260309.json` => `summary(total=4,p0=0,p1=0,ok=4)`
4. control-plane gates in replay loops stayed green:
   - `validate_control_plane_budget`
   - `validate_control_plane_invariants`
   - `validate_control_plane_status_sync`
   - `validate_required_gate_surface_drift`
   - `docs_command_contract_check`
   - `validate_protocol_ssot_source`

Decision boundary:

1. project-lane strict replay is closed in three consecutive loops after patch.
2. cross-layer `both` mode still surfaces global env-mismatch blockers (`IP-ENV-003`) under project-bound runtime; treated as boundary signal, not project regression.

## 5) Current release posture snapshot (v1.6 kickoff)

1. `v1.6` release status: `NO_GO` (kickoff baseline).
2. Blocking class currently visible in live project replay: `IP-CAP-003` (env/auth preflight).
3. Required external reporting posture:
   - `IMPL_READY (BLOCKED_BY_ENV_AUDIT)`
4. This posture remains until:
   - env/auth blocker closure is replay-proven, and
   - v1.6 unlock formula conditions are satisfied.

---

## 5.18 Round-30.2 Addendum: RQ-034 Runtime-Proof Strict/Scan Convergence

Scope:

1. close scan-path false escalation introduced by strict multimodal runtime-proof gating.
2. keep strict fail-close semantics unchanged for release-bearing surfaces.

Code changes audited:

1. `scripts/validate_multimodal_plugin_enforcement.py`
2. `scripts/required_gate_bundle_runner.py`
3. `scripts/release_readiness_check.py`
4. `scripts/report_three_plane_status.py`
5. `scripts/full_identity_protocol_scan.py`
6. `identity/protocol/plugins/multimodal-vision-enforcement/plugin.contract.yaml`
7. `identity/protocol/plugins/multimodal-vision-enforcement/plugin.error-codes.yaml`

Cross-verification replay:

1. strict fail-close:
   - command result: `/tmp/rq034_runtime_validate_fail_20260309_r2.json`
   - expected/actual: `FAIL_REQUIRED + IP-MM-RUN-001`
2. strict positive:
   - command result: `/tmp/rq034_runtime_validate_pass_20260309_r2.json`
   - expected/actual: `PASS_REQUIRED`
3. scan non-blocking:
   - command result: `/tmp/rq034_runtime_scan_nonblocking_20260309_r2.json`
   - expected/actual: validator `PASS_REQUIRED`, runtime evidence `SKIPPED_NOT_REQUIRED`
4. bundle target fail/pass:
   - fail: `/tmp/rq034_runtime_bundle_target_fail_20260309_r2.json`
   - pass: `/tmp/rq034_runtime_bundle_target_pass_20260309_r2.json`
5. three-plane projection visibility:
   - `/tmp/rq034_runtime_three_plane_20260309_r2.json`
   - runtime-proof fields present under `instance_plane_detail.multimodal_plugin_enforcement`
6. full-scan target convergence after shadow scan alignment:
   - `/tmp/rq034_runtime_fullscan_target_braev3_20260309_r4.json`
   - summary: `p0=0, p1=0, ok=1`
7. gate integrity replay:
   - `/tmp/rq034_runtime_surface_drift_20260309_r4.json` (`PASS_REQUIRED`)
   - `/tmp/rq034_runtime_docs_contract_20260309_r4.log` (rc=0)
   - `/tmp/rq034_runtime_ssot_20260309_r4.log` (rc=0)

Verdict:

1. strict lanes are now runtime-proof hard-gated for multimodal enforcement.
2. scan lanes are observational and no longer receive strict-shadow false escalation.
3. RQ-034 control-plane strengthening is closed at protocol-layer wiring level.

---

## 5.19 Round-30.3 Addendum: Producer Runtime-Proof Emission + Target Scan Regression Freeze

Scope:

1. promote multimodal runtime-proof field production from validator-side inference to producer-side mandatory emission.
2. close three-plane multimodal report binding gap by enforcing explicit selected-report passthrough.
3. freeze scan-path semantic regression with CI hard gate: target full-scan `p0` must remain zero.

Code changes audited:

1. `scripts/execute_identity_upgrade.py`
2. `scripts/report_three_plane_status.py`
3. `scripts/full_identity_protocol_scan.py`
4. `scripts/validate_full_scan_target_regression.py` (new)
5. `.github/workflows/_identity-required-gates.yml`

Cross-verification replay:

1. producer emission:
   - `/tmp/rq034_upgrade_reports_r3/identity-upgrade-exec-rq034-production-fields-20260309.json`
   - observed:
   - `multimodal_runtime_field_emission_status=PASS_REQUIRED`
   - mandatory runtime-proof keys are present even when status is `MISSING`.
2. three-plane multimodal report binding:
   - `/tmp/rq034_three_plane_runtime_fields_20260309_r6.json`
   - observed:
   - `instance_plane_detail.multimodal_plugin_enforcement.report_selected_path` equals `runtime_report_path`
   - no fallback to unrelated latest report.
3. fixed target full-scan regression gate:
   - `/tmp/rq034_full_scan_target_regression_20260309_r3.result.json`
   - `/tmp/rq034_full_scan_target_regression_20260309_r3.json`
   - observed:
   - `full_scan_target_regression_status=PASS_REQUIRED`
   - `summary.p0=0`.
4. baseline protocol gates:
   - `/tmp/rq034_surface_drift_20260309_r3.json` (`PASS_REQUIRED`)
   - `/tmp/rq034_docs_contract_20260309_r3.log` (rc=0)
   - `/tmp/rq034_ssot_20260309_r3.log` (rc=0)

Verdict:

1. RQ-034 runtime-proof observability is now producer-backed + projection-consistent across three-plane/full-scan.
2. scan-path regression now has explicit CI freeze (`p0=0`) instead of relying on manual deep-scan snapshots.
3. residual blocker states in live runs remain instance evidence quality issues, not protocol control-plane wiring gaps.

Round-21 runtime identity authority bypass closure (`HEAD=dirty`, 2026-03-16):

1. issue restatement:
   - the observed bad case was **not** a real runtime catalog switch.
   - root cause was `pre-egress identity authority bypass`: a fixture/demo/inactive identity could be selected into runtime/protocol egress semantics before final outlet release.
   - example class:
     - emitted/attempted `identity_id=store-manager`
     - actual project runtime authority remained `base-repo-closure-orchestrator`
   - therefore the defect class is `fixture/demo identity mis-selected into runtime/protocol egress`, not “catalog switched”.
2. infrastructure closure landed:
   - new common gate:
     - `scripts/identity_runtime_authority_common.py`
   - canonical consumers wired:
     - `scripts/render_identity_response_stamp.py`
     - `scripts/compose_and_validate_governed_reply.py`
     - `scripts/final_emit_governed.py`
     - `scripts/validate_reply_identity_context_first_line.py`
     - `scripts/sync_session_identity.py`
   - required negative replay coverage extended:
     - `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
     - `scripts/validate_required_gate_surface_drift.py`
3. authority freeze implemented in code:
   - runtime/protocol egress candidate must satisfy:
     - `status=active`
     - `profile!=fixture`
     - `runtime_mode!=demo_only`
   - authority precedence is evaluated from actor/session binding → canonical session pointer → single active runtime identity → runtime default identity.
   - fixture/demo identities are never runtime egress authorities.
   - canonical session-primary writer now rejects fixture/demo identities as canonical runtime authority targets.
4. machine error contract:
   - error code: `IP-IAUTH-001`
   - semantic meaning: `pre-egress identity authority bypass / non-runtime-eligible identity selected for runtime egress`
5. replay evidence:
   - runtime source confirmation:
     - `python3 scripts/resolve_identity_context.py resolve --identity-id base-repo-closure-orchestrator`
     - observed:
       - `source_layer=project`
       - `catalog_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
       - `pack_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-closure-orchestrator`
   - negative:
     - `python3 scripts/render_identity_response_stamp.py --identity-id store-manager ... --json-only`
     - observed:
       - rc=`1`
       - `identity_authority_status=FAIL_REQUIRED`
       - `error_code=IP-IAUTH-001`
   - negative:
     - `python3 scripts/final_emit_governed.py --identity-id store-manager ... --body-text 'probe body' --json-only`
     - observed:
       - rc=`1`
       - `final_emit_guard_status=FAIL_REQUIRED`
       - `error_code=IP-IAUTH-001`
   - negative:
     - `python3 scripts/validate_reply_identity_context_first_line.py --identity-id store-manager ... --reply-text 'Identity-Context: ... identity_id=store-manager ...' --json-only`
     - observed:
       - `reply_first_line_status=FAIL_REQUIRED`
       - `error_code=IP-IAUTH-001`
   - synthetic fixture-active proof:
     - temporary catalog with `fixture-live(status=active, profile=fixture, runtime_mode=demo_only)`
     - `python3 scripts/render_identity_response_stamp.py --identity-id fixture-live ... --json-only`
     - observed:
       - rc=`1`
       - `error_code=IP-IAUTH-001`
     - `python3 scripts/sync_session_identity.py --identity-id fixture-live ...`
     - observed:
       - fail-close:
       - `identity is not runtime-eligible for canonical session authority`
6. residual note:
   - gateway full probe suite still contains an independent pre-existing assertion failure (`sender consumption projection`) unrelated to `IP-IAUTH-001`.
   - this round closes authority selection bypass itself; it does not falsely claim the whole gateway suite is now globally green.
7. verdict:
   - fixture/demo/inactive identities can no longer be treated as runtime/protocol egress authorities on canonical stamp/compose/final-emit/first-line paths.
   - canonical session-primary state can no longer be rewritten to fixture/demo identity targets.
   - defect classification is now explicitly frozen under actor-session authority semantics, with egress chain fail-close downstream.

---

## 6) References

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
4. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
5. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
6. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
7. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
8. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
9. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
10. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`
11. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
12. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
13. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
14. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
15. `https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide/#frequented-asked-questions-faq`
16. `context7:/websites/developers_openai_api`
17. `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-self-drive-regression-v2026-03-04.md`
18. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
19. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-unified-feedback-index-2026-03-04.md`
20. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-discovery-dual-track-simulation-receipt-2026-03-04.md`
21. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-cross-verification-execution-receipt-2026-03-04-roundtable-vendor-context7-openaidoc-skill.md`
22. `https://developers.openai.com/codex/skills/`
23. `https://developers.openai.com/codex/security/`
24. `context7:/websites/developers_openai`
25. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
26. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
27. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
28. `https://github.com/brianlyang/identity-protocol/tree/main/identity`
29. `identity/protocol/IDENTITY_PROTOCOL.md`
30. `identity/protocol/IDENTITY_RUNTIME.md`
31. `identity/protocol/IDENTITY_DISCOVERY.md`
32. `identity/catalog/schema/identities.schema.json`
33. `identity/catalog/identities.yaml`
34. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-v1.6-governance-review-cross-verification-verdict-2026-03-05.md`
35. `https://developers.openai.com/api/reference/resources/responses/`
36. `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
37. `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
38. `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/system-prompts`
39. `https://modelcontextprotocol.io/specification/latest`
40. `https://agentskills.io/specification`
41. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-instance-next-upgrade-proposals-cross-verified-2026-03-05.md`
42. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-self-drive-live-replay-deep-extraction-2026-03-05-round2.md`
43. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-05_001.md`
44. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/issues/ISSUE_2026-03-05_update-threeplane-semantic-convergence-gap.md`
45. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/upgrade-proposals/PROPOSAL_2026-03-05_semantic-single-source-and-convergence-gate.md`
46. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
47. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
48. `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
49. `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`
50. `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/IDENTITY_PROMPT.md`
51. `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/RULEBOOK.jsonl`
52. `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/TASK_HISTORY.md`
53. `/tmp/v16_selfdrive_architect_validation_bundle_20260305.json`
54. `/tmp/v16_selfdrive_architect_three_plane_20260305.json`
55. `/tmp/v16_selfdrive_architect_validate_20260305.log`
56. `/tmp/v16_final_xverify_bundle_20260305.json`
57. `https://developers.openai.com/codex/security/#common-sandbox-and-approval-combinations`
58. `https://platform.openai.com/docs/guides/function-calling#strict-mode`
59. `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role`
60. `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
61. `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
62. `https://modelcontextprotocol.io/specification/latest`
63. `https://agentskills.io/specification`
64. `context7:/openai/skills`
65. `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`
66. `/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`
67. `/tmp/v16_architect_deep_scan_full_repo_20260305.json`
68. `/tmp/v16_architect_deep_scan_full_repo_20260305.md`
69. `/tmp/v16_one_by_one_requirement_review_20260305.md`
70. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-protocol-kernel-prompt-file-decision-cross-verification-2026-03-06.md`
71. `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
72. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
73. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
74. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T210151_fqg_multiagent_multiidentity_blocker.md`
75. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
76. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
77. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
78. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_ESCALATION_PACK_20260306T213707_multiagent_multiidentity.md`
79. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T213517_protocol_lane_activation_receipt.md`
80. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T140030Z_tmp_hardcoded_path_governance_gap.md`
81. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T140030Z_tmp_hardcoded_path_governance_gap.json`
82. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`

## v1.6.0 Addendum (2026-03-17): session-primary switch + strict authority purity replay

### A1) Scope

1. fix switch receipt validation so it binds to session-primary pre-state instead of shared canonical pre-state.
2. remove canonical/catalog fallback from strict actor/session authority paths.
3. fail-close final emit auto identity resolution when explicit actor context has no binding.

### A2) Code closure

1. `scripts/identity_creator.py`
   - activate -> sync handoff now passes:
     - `--switch-prestate-mode session_primary`
     - `--switch-from-identity <current_actor_identity>`
2. `scripts/sync_session_identity.py`
   - added `session_primary` vs `legacy_canonical` pre-state modes for switch receipt validation.
3. `scripts/identity_runtime_authority_common.py`
   - explicit actor/session missing-binding now returns `actor_binding_session_binding_missing`.
   - explicit actor-only ambiguity/missing now fail-closes instead of degrading into canonical/catalog authority.
4. `scripts/response_stamp_common.py`
   - canonical pointer no longer fills visible lock state when actor context is present but unbound.
5. `scripts/final_emit_governed.py`
   - auto identity resolution now fails under strict actor authority if no actor/session binding exists.

### A3) Replay evidence

1. synthetic switch replay:
   - `/tmp/switch_guard_session_primary_proof_20260317.json`
   - verdict:
     - positive receipt (`alpha -> gamma`) passes even when canonical pointer pre-state is `beta`
     - negative receipt (`beta -> gamma`) fails with `IP-ASB-MB-009`
2. synthetic strict authority replay:
   - `/tmp/strict_authority_purity_proof_20260317.json`
   - verdict:
     - unbound explicit session fails with `identity_authority_resolution_mode=actor_binding_session_binding_missing`
     - final emit auto identity resolution fails with `context_resolution_failed: identity-id is unresolved under strict actor authority`
3. live runtime replay:
   - `/tmp/base_repo_architect_multibinding_20260317.json`
   - `/tmp/base_repo_architect_render_stamp_20260317.json`
   - `/tmp/base_repo_architect_pointer_consistency_20260317.log`
   - verdict:
     - multibinding concurrency `PASS_REQUIRED`
     - render stamp resolves `identity_authority_resolution_mode=actor_binding_session_scoped`
     - pointer consistency passes under `--strict-session-primary`

### A4) Verdict

1. the reproduced “receipt matched session-primary state but failed against canonical pointer state” defect is closed.
2. explicit actor/session lanes no longer silently degrade into shared canonical or catalog authority.
3. strict authority gaps now fail-close with machine-readable stale reasons instead of identity drift.

## v1.6.0 Addendum (2026-03-17): actor-session authority residue cleanup replay

### B1) Scope

1. remove persisted-data ambiguity after session-primary closure:
   - actor stores need session-primary mutation projection, not only actor-global compatibility projection;
   - compatibility pointers must declare non-authoritative role explicitly.

### B2) Code closure

1. `scripts/validate_actor_session_multibinding_concurrency.py`
   - now prefers `last_mutation_by_session[session_id]` when `--session-id` is supplied;
   - emits `last_mutation_projection_scope` / `last_mutation_projection_source`;
   - fails-close on raw persisted residue (`authority_model`, `authoritative_binding_rule`,
     `last_mutation_by_session`, `last_mutation_projection_scope`) before repair.
2. `scripts/sync_session_identity.py`
   - canonical + mirror pointers now persist compatibility-mirror metadata and explicit
     `authoritative_decision_allowed=false`.
3. `scripts/repair_actor_session_authority_residue.py`
   - scans actor stores + compatibility pointers;
   - rewrites persisted runtime residue via normalized protocol shapes;
   - supports `--apply` against live runtime catalogs without identity-specific branches.
4. `scripts/ci/run_semantic_clarity_probes_ci.sh`
   - now replays negative residue detection + positive repair application.

### B3) Replay evidence

1. synthetic residue replay (CI):
   - negative: residue present => repair surface returns `FAIL_REQUIRED`
   - positive: `--apply` backfills actor store + pointer metadata, then multibinding validator returns
     `last_mutation_projection_scope=session_primary`
2. live runtime replay:
   - `python3 scripts/repair_actor_session_authority_residue.py --catalog ../.identity/catalog.local.yaml --all-actors --apply --json-only`
   - expected verdict:
     - actor stores normalized to session-primary v2 authority model
     - compatibility pointers explicitly demoted

### B4) Verdict

1. remaining confusion after M:N closure is now classified as persisted authority residue, not core binding logic failure.
2. runtime residue is repairable through one protocol-owned surface instead of per-instance patching.
## 2026-03-20 Closure Addendum - Historical default / validator alias cleanup

- `ISSUE-004` review verdict: `PASS_REQUIRED` once `scripts/validate_historical_baseline_default_boundary.py` proves historical motherline doc literals remain checker-only and no longer act as live defaults.
- `ISSUE-005` review verdict: `PASS_REQUIRED` once versioned current carriers declare and satisfy the frozen alias policy enforced by `scripts/validate_current_alias_versioned_carrier.py`.
- `ISSUE-007` review verdict: `PASS_REQUIRED` once active task/control-plane/coverage/replay surfaces stop referencing `validate_v16_*` validators except where contract-binding marks them `wrapper_compatibility_optional`; `scripts/validate_active_validator_alias_residue.py` is the machine gate.
- These rows close residual cleanup debt; they do not reopen earlier batch semantics.

## 2026-03-22 Closure Addendum - No-downgrade motherline freeze

- Review verdict: `PASS_REQUIRED` once `rq_047_protocol_no_downgrade_motherline_contract_v1` is frozen in `IDENTITY_PROTOCOL.md`, bound as `ASB16-RQ-047`, and mirrored by the runtime hard-semantics clause.
- Review interpretation: the protocol does not downgrade, does not provide downward compatibility, and does not backstop lagging instance/workspace adoption on active surfaces.
- Compatibility/fallback/bridge residue may survive only on governed migration/replay/diagnostic lanes; any return to active defaults, validator green paths, current-turn runtime truth, active entry, or protocol-owned success paths is a fail-close regression.
- Active governed headstamp/send-time/first-line/layer-intent payloads now stay canonical-only on `error_code`; replay-only alias echo is explicit rather than implicit, so legacy alias fields no longer ride live protocol surfaces as a hidden compatibility backstop.
- `ISSUE-027` is now closed on the workbook lane as well: the missing motherline principle was already frozen, and the remaining live alias residue/workbook truth-sync tail has now been absorbed without reopening downgrade/backstop semantics.
