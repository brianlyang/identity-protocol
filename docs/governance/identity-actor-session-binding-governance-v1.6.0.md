# Identity Actor-Scoped Session Binding Governance (v1.6.0)

Status: Draft (v1.6 planning + release-governance execution directive)
Governance layer: protocol
Scope: identity protocol base-repo only (no instance business policy)
Owner: identity protocol base-repo architect
Execution mode: topic-level canonical SSOT for v1.6 release governance and remediation closure
Tag policy: `v1.6` remains locked until all `P0` requirement ledger rows are `DONE` and audit sign-off is `PASS` (`P1` rows block only when explicitly promoted to `P0`)

## 0) Governance Execution Mode and Release Lock (Mandatory)

### 0.1 Single execution entrypoint (topic SSOT)

1. This document is the only normative execution entrypoint for actor-session-binding governance in v1.6.
2. `artifacts/**` and ad-hoc notes are evidence-only; they cannot override this document.
3. No same-topic parallel normative document is allowed.

### 0.2 SSOT layering relationship (anti-drift)

1. This file is topic-canonical for v1.6 planning/execution.
2. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` remains global protocol execution SSOT.
3. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` remains the authoritative v1.5 closure record and historical baseline.
4. v1.6 governance updates must not rewrite historical v1.5 evidence; only carry-over boundaries may be referenced.

### 0.3 Release lock table (`v1.6` tag hard-locked)

| Decision Gate | Unlock condition | Current state |
| --- | --- | --- |
| D1 Contract freeze | v1.6 contracts/fields/error semantics finalized in this doc | OPEN |
| D2 Implementation complete | Mandatory scripts/validators/tools landed for v1.6 P0 items | OPEN |
| D3 Gate wiring complete | creator/e2e/readiness/full-scan/three-plane/CI wired for v1.6 P0 items | OPEN |
| D4 Acceptance pass | Mandatory acceptance command set green under current live replay window | OPEN |
| D5 Audit sign-off | Architect + audit expert both PASS on v1.6 P0 closure set | OPEN |
| D6 Tag allowed | D1~D5 all PASS | LOCKED |

### 0.4 Requirement status model (machine-readable semantics)

Allowed status values:

1. `SPEC_READY` - requirement finalized in governance, implementation not complete.
2. `IMPL_READY` - implementation landed but not fully wired or still blocked by audit/env boundary.
3. `GATE_READY` - implementation + gate wiring landed.
4. `VERIFIED` - acceptance commands pass with evidence.
5. `DONE` - verified and audit accepted for release gating.

Hard rule:

1. Any `P0` requirement not reaching `DONE` keeps `v1.6` tag locked.
2. `P1` requirements remain mandatory backlog visibility items and block `v1.6` only when explicitly promoted to `P0`.

### 0.5 v1.5 carry-over boundary (normative for v1.6 kickoff)

As-of 2026-03-03 live replay boundary:

1. Protocol code-gap closure for FIX-051/FIX-054 is retained.
2. Project-scope runtime remains blocked by `IP-CAP-003` (env/auth preflight).
3. External posture must remain `IMPL_READY (BLOCKED_BY_ENV_AUDIT)` until capability activation boundary is closed.

Carry-over evidence anchors:

1. `docs/review/protocol-remediation-audit-ledger-v1.5.md` section `16.8.48`.
2. `/tmp/reaudit_643_fullscan_project_only_live.json`.
3. `/tmp/reaudit_643_threeplane_live.json`.

## 1) v1.6 Problem Statement (P0)

v1.5 converged major protocol implementation gaps, but release readiness still lacks deterministic closure due to two classes of residual risk:

1. Runtime environment/auth blockers (`IP-CAP-003`) can hold project-scope replay in P0 even when protocol code contracts pass.
2. Release decision remains partially narrative; formula inputs are not fully machine-computed as a single source for `unlock_allowed`.

v1.6 objective is to turn closure posture into machine-auditable release governance with strict boundary separation:

1. Protocol code defects vs environment/auth blockers must be classified and reported separately.
2. Release unlock decision must be reproducible by one command path and one evidence set.

## 2) Non-Negotiable Layer Boundary

Protocol layer responsibilities:

1. Binding/routing contracts, validators, gate wiring, release formula computation, evidence contracts.
2. Canonical governance and review SSOT documents.
3. Runbook contracts for deterministic replay and audit.

Instance/environment responsibilities:

1. Credential/auth activation and external provider readiness.
2. Business strategy and domain content.

Hard rules:

1. Environment/auth blockers cannot be silently reclassified as protocol code closure.
2. Protocol release claims must include machine-readable formula evidence.
3. No release status claim may override D1~D6 table results.

## 3) v1.6 Workstream Targets

| Workstream | Target | Priority | Expected output |
| --- | --- | --- | --- |
| WS-1 | release unlock formula automation | P0 | single deterministic unlock report (`unlock_allowed`, blocking list, evidence refs) |
| WS-2 | capability activation boundary governance | P0 | explicit env/auth blocker contract with stable error mapping (`IP-CAP-*`) |
| WS-3 | requirement status promotion pipeline | P0 | machine-assisted `GATE_READY/VERIFIED -> DONE` promotion evidence contract |
| WS-4 | outlet/sidecar anti-regression | P0 | regression matrix for compose/send-time/sidecar across root/tmp/catalog lanes |
| WS-5 | cross-cwd runbook hardening | P1 | absolute-path invocation profile + deterministic replay recipe |
| WS-6 | docs bridge automation | P1 | governance/review status bridge template and consistency checker |
| WS-7 | office-ops deterministic self-drive hardening | P1 | run-id report binding, baseline bootstrap automation, temp/freshness/feedback emit helpers |

## 4) Protocol Contract Additions (v1.6)

### 4.1 `release_unlock_formula_automation_contract_v1` (P0)

Mandatory fields in unlock output:

1. `unlock_allowed`
2. `decision_gates` (`D1`..`D6`)
3. `p0_total`
4. `p0_done`
5. `p0_not_done_refs`
6. `audit_signoff_status`
7. `env_blockers`
8. `protocol_blockers`
9. `evidence_refs`

Hard rules:

1. Output must be deterministic for same repo head and same evidence inputs.
2. Any missing required field is fail-closed.

### 4.2 `capability_activation_boundary_contract_v2` (P0)

Mandatory behavior:

1. Capability activation checks must emit machine-readable blocker class and code.
2. `IP-CAP-*` blockers are environment/auth class by default, not protocol-code class.
3. Release summary must surface `env_blockers` separately from protocol blockers.

### 4.3 `status_promotion_evidence_contract_v1` (P0)

Mandatory behavior:

1. Promotion to `DONE` requires explicit replay evidence + auditor verdict.
2. Promotion cannot be performed by narrative-only updates.
3. Every promotion event must record commit anchor + evidence paths.

### 4.4 `outbound_reply_outlet_regression_matrix_contract_v1` (P0)

Mandatory coverage matrix:

1. `identity_creator validate` lane
2. readiness lane
3. e2e lane
4. full-scan lane
5. three-plane lane
6. cross-cwd replay (`repo root` / `/tmp`)

### 4.5 `cross_cwd_runbook_absolute_input_contract_v1` (P1)

Mandatory runbook note:

1. non-protocol-root caller must pass absolute `--repo-catalog` for post-execution chain consistency.
2. runbook examples must include both protocol-root and non-root invocations.

### 4.6 `office_ops_self_drive_determinism_contract_v1` (P1)

Input package boundary:

1. canonical feedback batch:
   - `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260304T041651Z_office_ops_protocol_upgrade_suggestions.md`
2. canonical proposal:
   - `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_20260304T041651Z_office_ops_self_drive.md`

Mandatory triage split:

1. run-id anchored strict report selection is treated as v1.5 carry-over candidate and can be absorbed by v1.6 only if not landed in v1.5 closure window.
2. baseline phase-A anchor bootstrap, temp-file collision hardening, handoff/collab age-only bootstrap, and atomic feedback emit helper are v1.6 backlog items by default.

Hard rules:

1. v1.6 intake must not retroactively relabel current v1.5 unlock blockers.
2. every adopted suggestion must keep canonical protocol-feedback channel and SSOT linkage semantics unchanged.

## 5) Requirement Mapping (v1.6)

| Requirement ID | Protocol governance target | Surfaces | Priority | Status | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| ASB16-RQ-001 | automate v1.6 unlock formula computation and output | release readiness + dedicated unlock tool + review bridge | P0 | SPEC_READY | v1.6 kickoff |
| ASB16-RQ-002 | capability activation boundary classification (`IP-CAP-*` env/auth) | capability validators + full-scan + three-plane | P0 | SPEC_READY | carry-over from v1.5 `16.8.48` |
| ASB16-RQ-003 | `GATE_READY/VERIFIED -> DONE` promotion contract | governance ledger sync tooling + review decision log | P0 | SPEC_READY | v1.6 kickoff |
| ASB16-RQ-004 | outlet compose/send-time anti-regression matrix | creator/readiness/e2e/full-scan/three-plane | P0 | SPEC_READY | FIX-054 carry-over hardening |
| ASB16-RQ-005 | sidecar passthrough/cwd invariance regression lock | sidecar validator + scan/three-plane | P0 | SPEC_READY | FIX-051/FIX-054 carry-over hardening |
| ASB16-RQ-006 | release plane cloud evidence readiness contract | release-plane checks + required gates evidence | P0 | SPEC_READY | current release-plane `NOT_STARTED` |
| ASB16-RQ-007 | cross-cwd absolute-input runbook contract | review runbook + governance references | P1 | SPEC_READY | review `16.8.47/16.8.48` note |
| ASB16-RQ-008 | docs bridge consistency automation | governance/review status bridge checker | P1 | SPEC_READY | repeated manual bridge rounds in v1.5 |
| ASB16-RQ-009 | strict report selection must prefer run-id binding before mtime fallback | strict preflight report resolver + session refresh/version alignment selectors | P0 | SPEC_READY | office-ops intake `16.8.75` (v1.5 candidate carry-over) |
| ASB16-RQ-010 | baseline missing-anchor should auto-bootstrap phase-A run_pinned before strict phase-B | baseline/session refresh orchestration + update strict lane | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-011 | regression self-drive temp strategy must be collision-safe in `/tmp` | regression scripts + temp allocator helper | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-012 | handoff/collab age-only freshness failures should support deterministic bootstrap auto-rotation | handoff/collab freshness validators + bootstrap receipt writer | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-013 | protocol-feedback atomic emit helper must write batch + index + receipt in one command | feedback emit helper + SSOT index updater + split receipt writer | P1 | SPEC_READY | office-ops intake `16.8.75` |

## 6) Mandatory Confirmation Matrix (v1.6)

| Check ID | Closure condition | Evidence requirement |
| --- | --- | --- |
| C1 | unlock formula output reproducible for same inputs | two reruns with identical output hash |
| C2 | all P0 blockers machine-classified (`protocol` vs `env`) | full-scan + three-plane + unlock report alignment |
| C3 | `IP-CAP-003` boundary explicitly surfaced as env blocker | capability activation replay + release summary |
| C4 | outlet compose/send-time matrix all pass in required lanes | matrix report with lane-by-lane rc/status |
| C5 | sidecar passthrough equivalence remains stable | direct validator vs sidecar track equivalence replay |
| C6 | cross-cwd runbook replay deterministic | root/tmp replay parity records |
| C7 | governance/review bridge has no contradictory status pair | consistency checker output |
| C8 | promotion to `DONE` only via evidence-backed decision | promotion receipt with commit + evidence + reviewer |

## 7) v1.6 Requirement Ledger (canonical tracker for unlock)

| Requirement ID | Requirement summary | Priority | Current status | Notes |
| --- | --- | --- | --- | --- |
| ASB16-RQ-001 | unlock formula automation | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-002 | capability boundary classification | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-003 | status promotion evidence pipeline | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-004 | outlet regression matrix | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-005 | sidecar invariance regression lock | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-006 | release-plane cloud evidence contract | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-007 | cross-cwd runbook contract | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-008 | docs bridge consistency automation | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-009 | run-id anchored strict report selection | P0 | SPEC_READY | v1.5 carry-over candidate; keep parity with review `16.8.75` |
| ASB16-RQ-010 | baseline phase-A bootstrap automation | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-011 | regression temp collision-safe strategy | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-012 | handoff/collab freshness auto-bootstrap | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-013 | protocol-feedback atomic emit helper | P1 | SPEC_READY | implementation pending |

### 7.1 v1.6 status delta snapshot (2026-03-03 kickoff)

| Requirement ID | Status delta | Evidence pointer |
| --- | --- | --- |
| ASB16-RQ-001..008 | `NEW -> SPEC_READY` | this document kickoff baseline |
| ASB16-RQ-009..013 | `NEW -> SPEC_READY` | office-ops intake triage bridge (`review v1.5 16.8.75`) |

### 7.2 v1.6 unlock formula (release-lock hard rule)

`v1.6` tag unlock condition:

1. `unlock_allowed = true` iff all `P0` rows in section 7 are `DONE` and D1~D5 in section 0.3 are `PASS`.
2. `P1` rows remain mandatory backlog items and block `v1.6` only when explicitly promoted to `P0`.

Non-equivalence constraints:

1. `SPEC_READY != IMPL_READY`
2. `IMPL_READY != GATE_READY`
3. `GATE_READY != VERIFIED`
4. `VERIFIED != DONE`
5. Passing subset replays cannot override the formula above.

## 8) Anti-Overclaim Policy (Mandatory)

Prohibited statements until formula is satisfied:

1. `v1.6 implemented`
2. `v1.6 full closed`
3. `v1.6 full green`

Required reporting format:

1. state `unlock_allowed`.
2. list unresolved P0 requirement IDs.
3. list current blocker codes (protocol vs env classification).
4. include evidence paths.

## 9) References

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
3. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
4. `docs/review/protocol-remediation-audit-ledger-v1.6.md`
