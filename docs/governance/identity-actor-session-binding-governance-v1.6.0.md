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
4. `identity/protocol/*` and `identity/catalog/schema/*` are the kernel contract surfaces for v1.6; governance/review docs may map and audit them, but must not redefine their base semantics.
5. Instance-side automation may emit evidence only under instance runtime/protocol-feedback surfaces and must not mutate protocol-kernel sources.

## 3) v1.6 Workstream Targets

| Workstream | Target | Priority | Expected output |
| --- | --- | --- | --- |
| WS-1 | release unlock formula automation | P0 | single deterministic unlock report (`unlock_allowed`, blocking list, evidence refs) |
| WS-2 | capability activation boundary governance | P0 | explicit env/auth blocker contract with stable error mapping (`IP-CAP-*`) |
| WS-3 | requirement status promotion pipeline | P0 | machine-assisted `GATE_READY/VERIFIED -> DONE` promotion evidence contract |
| WS-4 | outlet/sidecar anti-regression | P0 | regression matrix for compose/send-time/sidecar across root/tmp/catalog lanes |
| WS-5 | cross-cwd runbook hardening | P1 | absolute-path invocation profile + deterministic replay recipe |
| WS-6 | docs bridge automation | P1 | governance/review status bridge template and consistency checker |
| WS-7 | office-ops deterministic self-drive hardening | P1 | run-id report binding, baseline bootstrap automation, temp/freshness/feedback emit helpers, dedup winner determinism, skill-path integrity, route pinning, fallback taxonomy |
| WS-8 | initial prompt capability bootstrap governance | P0 | capability-driver-native initialization contract + fail-closed matrix validator + business-interference runbook |
| WS-9 | discovery dual-track requiredization closure | P0 | trigger-conditioned requiredization policy + apply-time coverage fail-close gate + receipt/index evidence lock |
| WS-10 | identity kernel-first canonicalization | P0 | kernel SSOT contract surface + contract mapping projection + derived prompt compilation + instance write-boundary lock |
| WS-11 | semantic routing convergence and single-source governance | P0 | canonical semantic receipt contract + update/three-plane/full-scan convergence gate + deterministic mismatch fail-close |
| WS-12 | intake evidence quorum hard-gate for new v1.6 suggestions | P1 | roundtable+vendor+online-reference+spec anchors required before recommendation promotion beyond `PENDING_INTAKE` |
| WS-13 | protocol-kernel prompt import executable coupling + multimodal proof closure | P0 | text import must bind to executable validator mapping + actor-explicit strict lane + sample-evidence closure for trigger/knowledge/arbitration |

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

### 4.7 `identity_prompt_bootstrap_capability_contract_v1` (P0)

Input package boundary:

1. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
2. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
3. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
4. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
5. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`

Mandatory capability drivers for initialization templates:

1. source precedence driver
2. four-core capability driver (`judgement/reasoning/routing/rule-learning`)
3. baseline review driver
4. self-upgrade lifecycle driver (`trigger -> patch -> validate -> replay`)
5. trigger-regression + handoff driver
6. canonical collaboration-trigger driver
7. control-loop extension driver (`Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update`)
8. capability arbitration + conflict-order driver
9. lane separation driver (`instance` vs `protocol`)
10. dual-track governance + release declaration driver

Hard rules:

1. missing required driver in initialization template is fail-closed.
2. this contract must strengthen initialization semantics only and must not weaken existing runtime gates.

### 4.8 `prompt_capability_matrix_fail_closed_contract_v1` (P0)

Mandatory validator behavior:

1. a dedicated prompt capability validator must output machine-readable coverage and missing-driver list.
2. requiredized capability drivers must enforce `FAIL_REQUIRED` when absent.
3. validator output must be consumable by creator/readiness/full-scan/three-plane pipelines.

Mandatory output fields:

1. `capability_driver_required_total`
2. `capability_driver_present_total`
3. `capability_driver_coverage_rate`
4. `missing_capability_drivers`
5. `prompt_bootstrap_contract_status`
6. `error_code`

### 4.9 `bootstrap_runbook_business_interference_guard_contract_v1` (P1)

Mandatory runbook sequence after core-file edits (`IDENTITY_PROMPT.md` or `CURRENT_TASK.json`):

1. refresh replay (`baseline-policy=warn`) for tuple refresh
2. strict replay (`baseline-policy=strict`) for final closure
3. business interference matrix output with bounded impact window and mitigation pointers

Hard rules:

1. `IP-PVA-001` immediately after intentional core-file edits is treated as expected fail-safe before refresh and cannot be claimed as protocol regression by default.
2. refresh->strict sequence is mandatory in runbook examples and acceptance package.

### 4.10 `multi_source_cross_verification_evidence_contract_v1` (P1)

Cross-verification bundle is valid only when all four tracks are present:

1. roundtable track (local protocol roundtable/architect packet)
2. vendor track (official multi-vendor scan with source URLs)
3. OpenAI docs track (`openaidoc` anchors for strict schema/tool guidance)
4. Context7 track (OpenAI platform docs extraction, no contradictory guidance)

Vendor track minimum composition:

1. OpenAI official anchors (`strict mode`, `skills`, `security/sandbox-approvals`).
2. Google official anchors (`AI Studio build/full-stack` guidance).
3. Anthropic official anchors (`system prompt governance` guidance).
4. protocol-spec anchors (`MCP specification` and/or `Agent Skills specification`).

Hard rules:

1. if any track is missing, intake status cannot advance beyond `PENDING_INTAKE`.
2. evidence must remain protocol-only and cannot include business-sensitive runtime payloads.
3. vendor track without multi-vendor + protocol-spec coverage cannot satisfy `C11`.

### 4.11 `office_ops_regression_closure_extension_contract_v1` (P1)

Input package boundary:

1. `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-self-drive-regression-v2026-03-04.md`

Mandatory extension points:

1. dedup winner determinism:
   - winner must be monotonic by `(run_id, earliest_claim_ts, stable_tiebreaker)`;
   - conflict policy must be explicit and machine-readable.
2. cross-workflow closure evidence schema:
   - required fields: `run_id`, `route_action`, `quality_meta_state`, `dedup_state`, `evidence_hash`.
3. skill path integrity:
   - `SKILL.md` executable/script targets must exist in active repo layout for declared runtime mode.
4. route/version pinning consistency:
   - router endpoint must match active target workflow publish version evidence.
5. fallback taxonomy normalization:
   - fallback reasons must map to governed enum classes (`data_missing`, `model_weak_signal`, `transport_error`, `policy_blocked`).

Hard rules:

1. extension intake is `v1.6` backlog only and must not retroactively rewrite `v1.5` release blockers.
2. all evidence remains sanitized protocol-only payload, with no business/customer raw data.

### 4.12 `discovery_dual_track_requiredization_activation_contract_v1` (P0)

Input package boundary:

1. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
2. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-unified-feedback-index-2026-03-04.md`
3. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-discovery-dual-track-simulation-receipt-2026-03-04.md`

Mandatory behavior:

1. discovery contracts remain optional while no requiredization trigger class is active.
2. when trigger class is active (for example `repeat_platform_optimization_intent`), status must switch into requiredization path deterministically.
3. if trigger is active and requiredization is not applied, fail-close with `IP-DREQ-001` and machine-readable stale reasons.
4. lane separation must remain explicit (`work_layer=instance`) and cannot implicitly force protocol-layer write actions.

Hard rules:

1. conditional escalation is required; unconditional escalation is prohibited.
2. absence of trigger evidence must not be reclassified as trigger success.

### 4.13 `discovery_apply_coverage_fail_closed_contract_v1` (P0)

Mandatory apply-time closure gate:

1. if `requiredization_applied=true`, all requiredized discovery contracts must be evaluated in the same payload.
2. apply-time pass requires:
   - `discovery_required_total > 0`
   - `discovery_required_passed == discovery_required_total`
   - `discovery_required_coverage_rate == 100.0`
3. any mismatch must fail-close with dedicated error code (`IP-DREQ-002` reserved for v1.6 implementation).
4. apply path must emit and link both receipt and evidence-index records in the same execution window.

Cross-verification constraints (mandatory for intake advance):

1. roundtable track present.
2. vendor track present.
3. OpenAI docs track present (`strict-mode` + `codex skills/security` anchors).
4. Context7 track present with non-contradictory extraction.

### 4.14 `identity_kernel_ssot_contract_v1` (P0)

Kernel canonical boundary:

1. `identity/protocol/*` defines protocol-base contracts.
2. `identity/catalog/schema/*` defines machine-readable schema constraints.
3. `identity/catalog/identities.yaml` is the canonical registry payload surface.

Governance/review projection boundary:

1. `docs/governance/*` stores release-gate semantics, requirement status, and acceptance policy.
2. `docs/review/*` stores intake/replay/audit decisions.
3. Neither layer may introduce an unmapped base contract that is absent from kernel surfaces.

Hard rules:

1. base-contract edits must land in kernel surfaces before projection into governance/review.
2. script-only or docs-only semantic changes that bypass kernel are non-compliant.
3. each promoted contract must carry `kernel_contract_id` and source path.

### 4.15 `kernel_contract_mapping_projection_contract_v1` (P0)

Mandatory mapping tuple per contract:

1. `kernel_contract_id`
2. `kernel_source_path`
3. `validator_ids`
4. `gate_surfaces` (`creator/readiness/e2e/full-scan/three-plane/ci`)
5. `governance_anchor`
6. `review_anchor`

Hard rules:

1. mapping coverage for P0 contracts must be `100%`.
2. orphan entries (validator or requirement without `kernel_contract_id`) fail-closed.
3. mapping checks run before status promotion to `IMPL_READY`.

### 4.16 `derived_identity_prompt_compilation_contract_v1` (P0)

Prompt derivation model:

1. `IDENTITY_PROMPT.md` is generated from:
   - kernel base contracts (`identity/protocol/*`) and
   - identity-specific overlay (role/domain directives).
2. runtime must carry machine fields:
   - `kernel_contract_version`
   - `kernel_contract_digest`
   - `derived_from_contract_ids`
   - `overlay_digest`

Hard rules:

1. direct manual prompt mutation without derivation metadata is fail-closed in strict lanes.
2. prompt hash mismatch between derived metadata and runtime report is fail-closed.
3. derived prompt conformance is required for P0 release assertions.
4. protocol layer must not introduce same-name runtime artifact file `identity/protocol/IDENTITY_PROMPT.md`.
5. protocol-side prompt baseline, if needed, must be expressed as contract source (existing kernel anchors in `identity/protocol/IDENTITY_PROTOCOL.md` / `identity/protocol/IDENTITY_RUNTIME.md` or a dedicated prompt-bootstrap contract file) and then compiled into pack-level `IDENTITY_PROMPT.md`.
6. any protocol-side prompt baseline source is non-compliant unless mapping + validator + lane consumption are wired (`kernel_ref -> mapping_ref -> validator_ref -> acceptance replay`).
7. canonical protocol-side prompt baseline contract source for this track is `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`, which must remain continuously updatable with capability-ingestion traceability and replay obligations.

### 4.17 `instance_protocol_write_boundary_lock_contract_v1` (P0)

Allowed write surfaces for instance self-drive:

1. `<instance>/runtime/**`
2. `<instance>/runtime/protocol-feedback/**`

Forbidden write surfaces for instance self-drive:

1. `identity/protocol/**`
2. `docs/governance/**`
3. `docs/review/**`
4. protocol-level scripts and workflow files unless explicitly executed in protocol-owner lane.

Hard rules:

1. forbidden writes fail-closed with dedicated boundary code (`IP-KERNEL-WRITE-001`, reserved in v1.6).
2. evidence must show write-boundary enforcement decision in replay artifacts.
3. write-boundary lock is lane-scoped and write-surface scoped:
   - it must not rewrite routing outputs (`resolved_work_layer`, `protocol_entry_decision`, `applied_gate_set`).
4. protocol entry channels must remain reachable under boundary lock:
   - explicit `work_layer=protocol`,
   - `session_lane_lock=protocol`,
   - `protocol_entry_decision in {PROTOCOL_DIRECT, PROTOCOL_CANDIDATE}`.
5. protocol-context downgrade to instance without candidate/inquiry receipt chain is fail-closed:
   - canonical current-path codes are `IP-LAYER-GATE-006/007` and `IP-LAYER-CAND-001..004`.

### 4.18 `semantic_routing_single_source_convergence_contract_v1` (P0)

Problem class:

1. update lane can report green (`all_ok=true`) while cross-plane aggregators still produce semantic fail (`IP-SEM-001`) for same lineage.
2. mixed verdict indicates semantic-routing outcome is not represented as a canonical first-class machine source across planes.

Canonical contract:

1. semantic-routing verdict must be produced in one canonical receipt consumed by:
   - strict update report,
   - three-plane aggregation,
   - full-scan aggregation.
2. required fields:
   - `semantic_routing_status`
   - `semantic_routing_error_code`
   - `semantic_routing_evidence_path`
   - `semantic_routing_reason`
   - `semantic_routing_source`

Convergence gate:

1. same lineage must satisfy:
   - `update.semantic_routing_status == three_plane.semantic_routing_status == full_scan.semantic_routing_status`.
2. mismatch is fail-closed with deterministic convergence error code (`IP-SEM-CONV-001`, reserved in v1.6).
3. strict update cannot remain green when semantic-routing block is required but absent.

Hard rules:

1. semantic-routing verdict must not be privately derived by individual aggregators when canonical receipt is present.
2. dual-lane separation remains intact:
   - convergence enforcement must not convert instance update into protocol publish-gate blocking by default.
3. convergence evidence must be machine-readable and lineage-stable.

### 4.19 `v16_intake_evidence_quorum_contract_v1` (P1)

Goal:

1. Prevent guess-first requirement intake in v1.6 by enforcing cross-verified evidence quorum before recommendation promotion.
2. Require every new suggestion to carry explicit `T1..T4` evidence tracks with machine-readable anchors.

Mandatory semantics:

1. Any new v1.6 suggestion item must provide all four tracks before it can move beyond `PENDING_INTAKE`:
   - `T1 roundtable` track (local multi-role deliberation with explicit fact/inference split);
   - `T2 vendor` track (multi-vendor official guidance with source URLs);
   - `T3 openai_context` track (OpenAI official docs + Context7 extraction anchors with retrieval timestamp);
   - `T4 protocol_spec` track (`MCP`/`Agent Skills` + local skill protocol contract references).
2. Missing any required track keeps item locked at `PENDING_INTAKE` and blocks implementation-promotion.
3. Every intake section must include:
   - `cross_verification_bundle_id`
   - `source_url_set`
   - `reference_timestamp_utc`
   - `conflict_reconciliation_note`.
4. This quorum contract applies to all newly proposed v1.6 requirements after this governance update.

### 4.20 `v16_protocol_kernel_prompt_import_executable_coupling_contract_v1` (P0)

Goal:

1. Prevent "text-only strengthening" where protocol-kernel clauses are added to identity prompts but do not affect executable gates.
2. Ensure multimodal capability claims are backed by machine-verifiable sample evidence and strict actor-bound execution context.

Mandatory semantics:

1. Prompt import of kernel contracts (`identity/protocol/*`) must be executable-coupled:
   - runtime must emit machine-readable mapping fields linking `kernel_contract_ref -> validator_ref -> evidence_ref`.
2. Text import without executable coupling is fail-closed:
   - reserve `IP-PROMPT-CONTRACT-001` (`prompt_kernel_import_not_executable_coupled`).
3. Multimodal proof closure is required for self-drive identities:
   - trigger regression sample report exists and validates;
   - knowledge acquisition sample report exists and validates;
   - capability arbitration sample report exists and validates.
4. Strict update lane actor context must be explicit for protocol-class self-drive:
   - host-derived fallback actor context is not accepted for promotion-grade replay.
   - reserve `IP-ACTOR-CTX-001` (`strict_lane_actor_context_not_explicit`).
5. A/B replay proof is mandatory:
   - A: baseline prompt;
   - B: kernel-imported prompt;
   and verdict must be explained by executable mapping delta, not narrative-only prompt text.

### 4.21 `identity_context_headstamp_pre_send_hard_gate_contract_v1` (P0)

Goal:

1. Eliminate recurrent "missing headstamp on outbound reply" incidents.
2. Move headstamp enforcement from best-effort template discipline to transport-level fail-close.

Mandatory semantics:

1. Every outbound assistant reply must include canonical first-line headstamp before send:
   - `Identity-Context: actor_id=...; identity_id=...; scope=...; lock=...; source=...`
   - `Layer-Context: work_layer=...; source_layer=...`
2. Pre-send validator must execute regardless of composition path:
   - governed compose path and direct/manual reply path share the same pre-send gate.
3. Missing or malformed headstamp is fail-closed:
   - reserve `IP-HDSTAMP-001` (`headstamp_missing_or_malformed`).
4. Headstamp tuple must match actor-current binding and canonical identity pointer:
   - mismatch is fail-closed with `IP-HDSTAMP-002` (`headstamp_actor_binding_mismatch`).
5. Promotion-grade lanes (`update/readiness/e2e/ci/validate`) require machine receipt:
   - receipt must include `headstamp_status`, `error_code`, `evidence_ref`, `actor_binding_ref`.
   - missing receipt is fail-closed with `IP-HDSTAMP-003` (`headstamp_receipt_missing`).
6. Governance/review templates are advisory only; send decision is controlled exclusively by pre-send validator verdict.

## 5) Requirement Mapping (v1.6)

| Requirement ID | Protocol governance target | Surfaces | Priority | Status | Evidence pointer |
| --- | --- | --- | --- | --- | --- |
| ASB16-RQ-001 | automate v1.6 unlock formula computation and output | release readiness + dedicated unlock tool + review bridge | P0 | SPEC_READY | v1.6 kickoff + `8.5` batch-1 strengthening profile |
| ASB16-RQ-002 | capability activation boundary classification (`IP-CAP-*` env/auth) | capability validators + full-scan + three-plane | P0 | SPEC_READY | carry-over from v1.5 `16.8.48` + `8.5` classification hardening |
| ASB16-RQ-003 | `GATE_READY/VERIFIED -> DONE` promotion contract | governance ledger sync tooling + review decision log | P0 | SPEC_READY | v1.6 kickoff + `8.5` non-repudiation receipt hardening |
| ASB16-RQ-004 | outlet compose/send-time anti-regression matrix | creator/readiness/e2e/full-scan/three-plane | P0 | SPEC_READY | FIX-054 carry-over hardening + `8.5` negative-path binding (`ASB16-RQ-032`) |
| ASB16-RQ-005 | sidecar passthrough/cwd invariance regression lock | sidecar validator + scan/three-plane | P0 | SPEC_READY | FIX-051/FIX-054 carry-over hardening + `8.5` normalized parity rule |
| ASB16-RQ-006 | release plane cloud evidence readiness contract | release-plane checks + required gates evidence | P0 | SPEC_READY | current release-plane `NOT_STARTED` |
| ASB16-RQ-007 | cross-cwd absolute-input runbook contract | review runbook + governance references | P1 | SPEC_READY | review `16.8.47/16.8.48` note |
| ASB16-RQ-008 | docs bridge consistency automation | governance/review status bridge checker | P1 | SPEC_READY | repeated manual bridge rounds in v1.5 |
| ASB16-RQ-009 | strict report selection must prefer run-id binding before mtime fallback | strict preflight report resolver + session refresh/version alignment selectors | P0 | SPEC_READY | office-ops intake `16.8.75` (v1.5 candidate carry-over) |
| ASB16-RQ-010 | baseline missing-anchor should auto-bootstrap phase-A run_pinned before strict phase-B | baseline/session refresh orchestration + update strict lane | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-011 | regression self-drive temp strategy must be collision-safe in `/tmp` | regression scripts + temp allocator helper | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-012 | handoff/collab age-only freshness failures should support deterministic bootstrap auto-rotation | handoff/collab freshness validators + bootstrap receipt writer | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-013 | protocol-feedback atomic emit helper must write batch + index + receipt in one command | feedback emit helper + SSOT index updater + split receipt writer | P1 | SPEC_READY | office-ops intake `16.8.75` |
| ASB16-RQ-014 | initial identity prompt must be bootstrap capability-driver native | identity pack templates + prompt bootstrap contracts + strict update lanes | P0 | SPEC_READY | SRA batch `2026-03-04/002` + architect brief |
| ASB16-RQ-015 | prompt capability matrix validator must fail-closed on missing requiredized drivers | new prompt capability validator + required gate wiring | P0 | SPEC_READY | SRA batch `2026-03-04/003` |
| ASB16-RQ-016 | post-core-edit runbook must require refresh->strict and emit business interference matrix | runbook + replay scripts + reporting contracts | P1 | SPEC_READY | SRA batch `2026-03-04/001` + business-impact packet |
| ASB16-RQ-017 | v1.6 intake for bootstrap capability must include roundtable+vendor+openaidoc+context7 cross-verification | review intake checklist + governance evidence contract | P1 | SPEC_READY | SRA evidence index + vendor scan + OpenAI/context7 anchors + final reinforcement (`review v1.6 FIX16-027`) |
| ASB16-RQ-018 | dedup winner selection must be deterministic and monotonic for same `run_id` concurrency windows | serial orchestrator dedup contract + replay validator | P1 | SPEC_READY | office-ops supplemental intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-019 | cross-workflow closure evidence must enforce required schema fields for machine-checkable replay | workflow evidence schema validator + report normalizer | P1 | SPEC_READY | office-ops supplemental intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-020 | skill contract references must be path-valid in active repo/runtime layout before readiness/release acceptance | skill-path integrity validator + readiness/release wiring | P1 | SPEC_READY | office-ops supplemental intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-021 | route endpoint and target workflow publish version must remain pinned and auditable | route pinning validator + workflow version proof receipts | P1 | SPEC_READY | office-ops supplemental intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-022 | fallback reasons must be normalized to governed enum taxonomy for downstream arbitration | fallback taxonomy validator + report schema mapping | P1 | SPEC_READY | office-ops supplemental intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-023 | discovery path must escalate to requiredization only under deterministic trigger classes and keep fail-close semantics when apply is skipped | discovery requiredization validator + trigger-window classifier + update lane wiring | P0 | SPEC_READY | SRA discovery simulation intake (`review v1.6 FIX16-020`) |
| ASB16-RQ-024 | apply-time requiredization cannot pass with partial discovery coverage; coverage closure must be fail-closed | discovery coverage gate + receipt/index linker + scan/three-plane consumption | P0 | SPEC_READY | SRA discovery simulation intake (`review v1.6 FIX16-020`) |
| ASB16-RQ-025 | identity kernel surfaces (`identity/protocol/*`, `identity/catalog/schema/*`) must be canonical contract source for v1.6 | kernel contracts + release/docs projection validators | P0 | SPEC_READY | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-026 | every P0 contract must have machine-readable kernel-to-validator-to-doc mapping | mapping checker + status-promotion gate | P0 | SPEC_READY | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-027 | identity prompts must be kernel-derived artifacts with conformance metadata | prompt compiler + conformance validator + runtime report fields | P0 | SPEC_READY | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-028 | instance lanes must be blocked from protocol-kernel/governance/review writes by default | write-boundary validator + lane enforcement + fail-close error mapping + protocol-entry non-starvation guard | P0 | SPEC_READY | kernel-first baseline intake (`review v1.6 FIX16-021`) + non-starvation addendum (`review v1.6 FIX16-037`) |
| ASB16-RQ-029 | semantic-routing verdict must be single-sourced and convergent across update/three-plane/full-scan for same lineage | canonical semantic receipt + convergence validator + strict update schema uplift | P0 | SPEC_READY | semantic convergence intake (`review v1.6 FIX16-022`) |
| ASB16-RQ-030 | new v1.6 suggestions must satisfy intake evidence quorum (`T1 roundtable + T2 vendor + T3 openai_context + T4 protocol_spec`) before promotion beyond `PENDING_INTAKE` | intake validator/checklist + governance/review bridge + cross-verification metadata schema | P1 | SPEC_READY | intake hard-gate reinforcement (`review v1.6 FIX16-023`) + final replay reinforcement (`review v1.6 FIX16-027`) |
| ASB16-RQ-031 | protocol-kernel prompt imports must be executable-coupled and produce multimodal sample-proof closure under explicit actor context | prompt-kernel mapping validator + strict-lane actor-context gate + trigger/knowledge/arbitration sample-proof validators + A/B replay harness | P0 | SPEC_READY | self-drive experiment intake (`review v1.6 FIX16-024`) + architect instance pilot (`review v1.6 FIX16-026`) + final cross-track reinforcement (`review v1.6 FIX16-027`) |
| ASB16-RQ-032 | outbound reply must pass canonical identity/layer headstamp pre-send hard gate; missing or mismatched headstamp cannot be sent | pre-send headstamp validator + governed emitter wrapper + negative replay in e2e/ci | P0 | SPEC_READY | headstamp recurrence root-cause intake (`review v1.6 FIX16-029`) |

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
| C9 | initialization templates are capability-driver complete for requiredized matrix | prompt capability matrix report (`coverage_rate=100` for P0 set) |
| C10 | post-core-edit replay follows refresh->strict sequence with bounded business interference | paired refresh+strict reports + interference matrix receipt |
| C11 | cross-verification packet includes all `T1..T4` evidence tracks (`roundtable/vendor/openai_context/protocol_spec`) | intake checklist marked complete with four-track anchors + normalized track labels |
| C12 | discovery requiredization trigger semantics stay deterministic (`not_triggered -> optional`, `triggered_no_apply -> FAIL_REQUIRED`) | discovery requiredization report with trigger class + error code (`IP-DREQ-001`) |
| C13 | apply-time discovery coverage reaches full closure before `PASS_REQUIRED` | same-payload coverage proof (`passed==total`, `coverage_rate=100`) + linked receipt/index |
| C14 | kernel-first canonicalization holds (`identity/protocol/*` + `identity/catalog/schema/*` are source of base contracts) | kernel-source map report + projection diff check |
| C15 | P0 mapping coverage is complete and orphan-free | mapping coverage report (`coverage=100`, `orphan_count=0`) |
| C16 | active identity prompts are derived and metadata-consistent with kernel contracts | prompt conformance report with digest/version linkage |
| C17 | instance write attempts to protocol-kernel/governance/review paths are fail-closed | boundary validator replay with deterministic error code (`IP-KERNEL-WRITE-001`) |
| C18 | same-lineage semantic-routing verdict is convergent across update/three-plane/full-scan | convergence report (`mismatch_count=0`) + canonical semantic receipt path |
| C19 | new v1.6 suggestions pass intake evidence quorum before implementation promotion | cross-verification bundle proof (`T1..T4`) + timestamped source set + conflict reconciliation note |
| C20 | protocol-kernel prompt import produces executable uplift (not text-only) and multimodal sample-proof closure under explicit actor context | paired A/B replay bundle + mapping fields (`kernel_contract_ref`,`validator_ref`,`evidence_ref`) + trigger/knowledge/arbitration sample-proof pass set |
| C21 | outbound messages missing canonical `Identity-Context | Layer-Context` headstamp are blocked before send | pre-send negative replay (`missing/malformed headstamp -> FAIL_REQUIRED`, `IP-HDSTAMP-001`) + tuple mismatch replay (`IP-HDSTAMP-002`) + receipt-missing replay (`IP-HDSTAMP-003`) |
| C22 | write-boundary lock does not starve protocol entry channels (`explicit protocol`, `session lane lock`, `candidate/direct`) | lane-routing replay with boundary enabled and protocol-entry tuple kept live (`lane_resolution_decision`, `session_lane_lock`, `protocol_entry_decision`) |
| C23 | protocol-context silent fallback to instance is fail-closed and candidate/inquiry chain is mandatory | negative replay must emit deterministic fail-close (`IP-LAYER-GATE-006/007` or `IP-LAYER-CAND-001..004`) with candidate/inquiry receipts |
| C24 | lane-scoped routing and boundary telemetry are convergent across update/three-plane/full-scan | same-lineage telemetry tuple parity (`intent_source`, `protocol_context_detected`, `lane_resolution_decision`, `lane_resolution_error_code`, `applied_gate_set`, `base_repo_write_boundary_status`) |
| C25 | multi-agent delegated run must not hard-switch identity during execution state | switch-state gate replay (`RUNNING/TOOL_CALLING/STREAMING -> FAIL_REQUIRED`) + mandatory `switch_ack` verification receipt before dispatch |
| C26 | explicit protocol governance request must not be starved in instance lane; unresolved protocol route and missing headstamp are both fail-closed | lane-activation replay (`requested_lane=protocol`) with deterministic route verdict (`resolved_lane=protocol` or fail-close `IP-LANE-ROUTE-001/IP-LANE-ACT-002`) + send-time headstamp negative replay (`IP-HDSTAMP-001..003`) |
| C27 | strict surfaces must not hardcode fixed `/tmp` output paths; temp artifacts must be run/identity scoped | static scan + runtime replay proving dynamic temp resolver (`run_id + identity_id + operation`) and CI runner-temp parity (`${RUNNER_TEMP}`) with fail-close `IP-TMPPATH-*` |
| C28 | update execution verdict and aggregation verdict (`three-plane/full-scan`) must converge on identical gate-source snapshot | same-lineage replay must show `gate_source_ref` parity and `status/error_code` homomorphism; `update_pass + aggregation_fail` split is fail-closed (`IP-GSRC-001`) |
| C29 | required-contract enforcement must be producer-aware and applicability-scoped (`current-run linked` + run-type profile), not history-only or one-size-fits-all | requiredization receipt must include `producer_readiness`, `requiredization_current_round_linked`, `run_profile`; non-applicable contracts must resolve to `SKIPPED_NOT_REQUIRED` with explicit reason (`IP-GSRC-003/004/005`) |
| C30 | actor/catalog context drift and protocol-feedback write-path instability must be deterministic fail-close in strict surfaces | strict replay must block env/CLI catalog mismatch unless explicit override receipt is present, and must provide canonical write strategy (`primary protocol-feedback path` + controlled spool/reconcile fallback) with deterministic receipts (`IP-GSRC-006/007`) |

## 7) v1.6 Requirement Ledger (canonical tracker for unlock)

| Requirement ID | Requirement summary | Priority | Current status | Notes |
| --- | --- | --- | --- | --- |
| ASB16-RQ-001 | unlock formula automation | P0 | SPEC_READY | implementation landed (`scripts/validate_unlock_formula.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-002 | capability boundary classification | P0 | SPEC_READY | implementation landed (`scripts/validate_capability_boundary_classification.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-003 | status promotion evidence pipeline | P0 | SPEC_READY | implementation landed (`scripts/validate_promotion_pipeline.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-004 | outlet regression matrix | P0 | SPEC_READY | implementation landed (`scripts/validate_outlet_matrix.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-005 | sidecar invariance regression lock | P0 | SPEC_READY | implementation landed (`scripts/validate_sidecar_cwd_parity.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-006 | release-plane cloud evidence contract | P0 | SPEC_READY | implementation pending |
| ASB16-RQ-007 | cross-cwd runbook contract | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-008 | docs bridge consistency automation | P1 | SPEC_READY | implementation landed (`scripts/validate_docs_bridge_consistency.py`) + lane hooks wired; contradiction replay archive pending |
| ASB16-RQ-009 | run-id anchored strict report selection | P0 | SPEC_READY | v1.5 carry-over candidate; keep parity with review `16.8.75` |
| ASB16-RQ-010 | baseline phase-A bootstrap automation | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-011 | regression temp collision-safe strategy | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-012 | handoff/collab freshness auto-bootstrap | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-013 | protocol-feedback atomic emit helper | P1 | SPEC_READY | implementation pending |
| ASB16-RQ-014 | prompt bootstrap capability contract | P0 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-015 | prompt capability matrix fail-closed validator | P0 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-016 | refresh->strict + business interference runbook contract | P1 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-017 | roundtable/vendor/openaidoc/context7 cross-verification contract | P1 | SPEC_READY | implementation landed + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-018 | dedup winner determinism contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-019 | cross-workflow evidence schema contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-020 | skill-path integrity contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-021 | route/version pinning contract | P1 | SPEC_READY | implementation landed + lane hooks wired; emitter-before-gate sequence active, deterministic required=true replay archive pending |
| ASB16-RQ-022 | fallback taxonomy normalization contract | P1 | SPEC_READY | implementation landed + lane hooks wired; required=true replay archive pending and blocker-namespace isolation remains mandatory |
| ASB16-RQ-023 | discovery trigger-conditioned requiredization contract | P0 | SPEC_READY | SRA discovery dual-track intake pending implementation |
| ASB16-RQ-024 | discovery apply-time coverage fail-close contract | P0 | SPEC_READY | SRA discovery dual-track intake pending implementation |
| ASB16-RQ-025 | kernel-first canonical source contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-026 | kernel contract mapping projection contract | P0 | SPEC_READY | implementation landed (`scripts/validate_contract_mapping_coverage.py`) + lane hooks wired; full P0 coverage closure pending |
| ASB16-RQ-027 | derived prompt compilation contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-028 | instance write-boundary lock contract | P0 | SPEC_READY | boundary + lane telemetry hooks landed; non-starvation replay matrix closure remains pending in `8.12` |
| ASB16-RQ-029 | semantic single-source convergence contract | P0 | SPEC_READY | live replay mismatch confirmed; implementation pending |
| ASB16-RQ-030 | intake evidence quorum hard-gate contract | P1 | SPEC_READY | implementation landed (`single-parser dual-mode`) + lane hooks wired; promotion remains blocked until deterministic required=true replay archive is complete |
| ASB16-RQ-031 | protocol-kernel prompt import executable coupling contract | P0 | SPEC_READY | explicit lane/candidate non-starvation hooks landed with write-boundary addendum; mapping validator + actor-explicit strict lane + multimodal sample-proof closure still required before promotion |
| ASB16-RQ-032 | outbound headstamp pre-send hard-gate contract | P0 | SPEC_READY | enforce send-blocking when canonical identity/layer headstamp missing, malformed, or actor-mismatched; intake in `review FIX16-029` |

### 7.1 v1.6 status delta snapshot (2026-03-03 kickoff)

| Requirement ID | Status delta | Evidence pointer |
| --- | --- | --- |
| ASB16-RQ-001..008 | `NEW -> SPEC_READY` | this document kickoff baseline |
| ASB16-RQ-009..013 | `NEW -> SPEC_READY` | office-ops intake triage bridge (`review v1.5 16.8.75`) |
| ASB16-RQ-014..017 | `NEW -> SPEC_READY` | SRA bootstrap capability intake (`review v1.6 FIX16-015`) + final four-track reinforcement (`review v1.6 FIX16-027`) |
| ASB16-RQ-018..022 | `NEW -> SPEC_READY` | office-ops supplemental replay intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-023..024 | `NEW -> SPEC_READY` | SRA discovery dual-track simulation intake (`review v1.6 FIX16-020`) |
| ASB16-RQ-025..028 | `NEW -> SPEC_READY` | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-029 | `NEW -> SPEC_READY` | semantic convergence intake (`review v1.6 FIX16-022`) |
| ASB16-RQ-030 | `NEW -> SPEC_READY` | intake hard-gate reinforcement (`review v1.6 FIX16-023`) + final replay reinforcement (`review v1.6 FIX16-027`) |
| ASB16-RQ-031 | `NEW -> SPEC_READY` | self-drive experiment intake (`review v1.6 FIX16-024`) + architect pilot replay (`review v1.6 FIX16-026`) + final cross-track replay (`review v1.6 FIX16-027`) |
| ASB16-RQ-032 | `NEW -> SPEC_READY` | headstamp recurrence root-cause intake (`review v1.6 FIX16-029`) |

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

### 7.3 Deep-Scan lock inventory (`ASB16-RQ-001..032`, 2026-03-05)

Lock tuple definition (deterministic):

1. `KERNEL_LOCKED`: requirement has explicit normative anchor under `identity/protocol/*` (not only governance/review prose).
2. `SCRIPT_LOCKED`: requirement has executable gate mapping under `scripts/*` with machine-readable status/error/report fields.
3. `BRIDGE_LOCKED`: requirement appears in governance + review with aligned status semantics.
4. `FULL_LOCKED = KERNEL_LOCKED && SCRIPT_LOCKED && BRIDGE_LOCKED`.

Deep-scan result (`docs + scripts + identity/protocol`):

1. `BRIDGE_LOCKED = true` for `32/32` requirements (section 5 + review FIX16 rows are present).
2. `KERNEL_LOCKED = false` for `32/32` requirements (no `ASB16-RQ-*` anchor in `identity/protocol/*`).
3. `SCRIPT_LOCKED = false` for `32/32` requirements under contract-id lock criterion (`ASB16-RQ-*` / v1.6 contract IDs not anchored in scripts as enforceable keys).
4. Current `FULL_LOCKED` count is `0/32`; all rows remain `UNLOCKED` until kernel + script anchors are implemented.

| Requirement ID | Priority | Lock target (kernel + scripts) | KERNEL_LOCKED | SCRIPT_LOCKED | FULL_LOCK verdict |
| --- | --- | --- | --- | --- | --- |
| ASB16-RQ-001 | P0 | unlock formula canonical anchor + executable unlock computation gate | NO | NO | UNLOCKED |
| ASB16-RQ-002 | P0 | capability boundary taxonomy anchor + capability classification gates | NO | NO | UNLOCKED |
| ASB16-RQ-003 | P0 | promotion-state semantics anchor + promotion pipeline checker | NO | NO | UNLOCKED |
| ASB16-RQ-004 | P0 | outlet matrix contract anchor + compose/send-time regression gates | NO | NO | UNLOCKED |
| ASB16-RQ-005 | P0 | sidecar invariance contract anchor + passthrough/cwd regression gate | NO | NO | UNLOCKED |
| ASB16-RQ-006 | P0 | release-plane evidence contract anchor + cloud evidence readiness gate | NO | NO | UNLOCKED |
| ASB16-RQ-007 | P1 | cross-cwd runbook anchor + absolute-input enforcement utility | NO | NO | UNLOCKED |
| ASB16-RQ-008 | P1 | docs bridge consistency anchor + governance/review parity checker | NO | NO | UNLOCKED |
| ASB16-RQ-009 | P0 | run-id strict selector anchor + strict preflight report resolver | NO | NO | UNLOCKED |
| ASB16-RQ-010 | P1 | phase-A bootstrap anchor + refresh->strict orchestration gate | NO | NO | UNLOCKED |
| ASB16-RQ-011 | P1 | temp collision strategy anchor + regression temp allocator guard | NO | NO | UNLOCKED |
| ASB16-RQ-012 | P1 | freshness auto-bootstrap anchor + handoff/collab freshness gate | NO | NO | UNLOCKED |
| ASB16-RQ-013 | P1 | atomic emit anchor + batch/index/receipt atomic writer | NO | NO | UNLOCKED |
| ASB16-RQ-014 | P0 | prompt bootstrap capability anchor + template bootstrap gate | NO | NO | UNLOCKED |
| ASB16-RQ-015 | P0 | prompt capability matrix anchor + fail-closed matrix validator | NO | NO | UNLOCKED |
| ASB16-RQ-016 | P1 | post-core-edit runbook anchor + interference matrix writer | NO | NO | UNLOCKED |
| ASB16-RQ-017 | P1 | cross-verification intake anchor + intake evidence packet validator | NO | NO | UNLOCKED |
| ASB16-RQ-018 | P1 | dedup determinism anchor + same-run monotonic dedup validator | NO | NO | UNLOCKED |
| ASB16-RQ-019 | P1 | cross-workflow schema anchor + evidence schema validator | NO | NO | UNLOCKED |
| ASB16-RQ-020 | P1 | skill-path integrity anchor + runtime path integrity gate | NO | NO | UNLOCKED |
| ASB16-RQ-021 | P1 | route/version pinning anchor + route/workflow version pin gate | NO | NO | UNLOCKED |
| ASB16-RQ-022 | P1 | fallback enum taxonomy anchor + fallback normalization validator | NO | NO | UNLOCKED |
| ASB16-RQ-023 | P0 | discovery trigger requiredization anchor + trigger-conditioned fail-close gate | NO | NO | UNLOCKED |
| ASB16-RQ-024 | P0 | discovery apply coverage anchor + coverage=100 fail-close gate | NO | NO | UNLOCKED |
| ASB16-RQ-025 | P0 | kernel canonical source anchor + kernel-source projection checker | NO | NO | UNLOCKED |
| ASB16-RQ-026 | P0 | kernel->validator->doc mapping anchor + mapping coverage checker | NO | NO | UNLOCKED |
| ASB16-RQ-027 | P0 | derived prompt conformance anchor + prompt derivation validator | NO | NO | UNLOCKED |
| ASB16-RQ-028 | P0 | instance write boundary anchor + boundary fail-close gate mapping | NO | NO | UNLOCKED |
| ASB16-RQ-029 | P0 | semantic single-source anchor + cross-plane convergence validator | NO | NO | UNLOCKED |
| ASB16-RQ-030 | P1 | intake quorum anchor + `T1..T4` hard-blocking gate | NO | NO | UNLOCKED |
| ASB16-RQ-031 | P0 | prompt import executable-coupling anchor + actor-explicit multimodal proof gates | NO | NO | UNLOCKED |
| ASB16-RQ-032 | P0 | outbound headstamp pre-send anchor + send-blocking gate with actor/layer tuple checks | NO | NO | UNLOCKED |

### 7.4 Architect independent deep-rescan protocol (mandatory before promotion)

Execution directory:

1. `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local`

Mandatory command pack (all outputs must be archived in one receipt):

```bash
cd /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local

# 1) baseline snapshot
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git status --short

# 2) deep-scan volume baseline
rg --files docs | wc -l
rg --files scripts | wc -l
rg --files identity | wc -l

# 3) RQ anchor coverage in kernel+scripts (must not stay 0 for promoted rows)
rg -n "ASB16-RQ-[0-9]{3}" identity/protocol scripts

# 4) v1.6 contract-id coverage in kernel+scripts
rg '^### 4\\.[0-9]+ ' docs/governance/identity-actor-session-binding-governance-v1.6.0.md \
| sed -n 's/.*`\\([^`]*\\)`.*/\\1/p' \
| while IFS= read -r c; do
    s=$(rg -n "$c" scripts | wc -l | tr -d ' ')
    i=$(rg -n "$c" identity/protocol | wc -l | tr -d ' ')
    printf "%s\tscripts=%s\tidentity_protocol=%s\n" "$c" "$s" "$i"
  done

# 5) reserved fail-close error-code coverage
rg -n "IP-KERNEL-WRITE-001|IP-SEM-CONV-001|IP-PROMPT-CONTRACT-001|IP-ACTOR-CTX-001" \
  docs/governance/identity-actor-session-binding-governance-v1.6.0.md \
  docs/review/protocol-remediation-audit-ledger-v1.6.md \
  scripts identity/protocol

# 6) kernel version/source-map drift check
nl -ba identity/protocol/IDENTITY_PROTOCOL.md | sed -n '1,40p'
rg -n "protocol_contract_version|methodology_version" scripts/create_identity_pack.py scripts/identity_installer.py

# 7) document boundary gates
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_protocol_ssot_source.py
```

Receipt acceptance rule:

1. Architect must attach command outputs + SHA + date in review decision log before any row leaves `PENDING_INTAKE`.
2. Any claim of `FULL_LOCKED` without this independent rescan receipt is invalid.


Latest executed independent receipt (2026-03-05, architect):

1. `/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`
2. `/tmp/v16_architect_deep_scan_full_repo_20260305.json`
3. `/tmp/v16_architect_deep_scan_full_repo_20260305.md`
4. `/tmp/v16_one_by_one_requirement_review_20260305.md`

Receipt reconciliation result:

1. requirement cardinality reconciled to `32` (`ASB16-RQ-001..032`).
2. lock tuple unchanged after independent rerun: `BRIDGE_LOCKED=32/32`, `KERNEL_LOCKED=0/32`, `SCRIPT_LOCKED=0/32`, `FULL_LOCKED=0/32`.
3. Therefore no row is promotion-eligible; implementation anchoring in `identity/protocol/*` and `scripts/*` remains mandatory.

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

### 8.1 Kernel-Uplift Non-Regression Guardrails (mandatory)

Scope:

1. applies to implementation rollout of `ASB16-RQ-025..028` only.
2. enforces "kernel-first uplift without breaking v1.5 operating baseline".

Baseline invariants (must stay true during all rollout phases):

1. `v1.5` release-plane contract and D-gate semantics remain unchanged by v1.6 implementation tasks.
2. instance write boundary remains locked to:
   - `<instance>/runtime/**`
   - `<instance>/runtime/protocol-feedback/**`
   and does not allow protocol-kernel/governance/review writes.
3. anti-overclaim and unlock formula in section `7.2` remain authoritative and unmodified by partial implementation progress.
4. boundary lock must remain write-surface scoped and must not starve protocol entry channels (`explicit protocol`, `session_lane_lock=protocol`, `PROTOCOL_CANDIDATE/PROTOCOL_DIRECT`).

Phased rollout contract (hard order):

1. `Phase-A (shadow)`:
   - new kernel/mapping/prompt/boundary validators run in observe-only mode;
   - no status promotion side effects are allowed.
2. `Phase-B (required-no-promotion)`:
   - validators become required for intake acceptance;
   - requirement status may reach `IMPL_READY`, but promotion to `DONE` is still blocked.
3. `Phase-C (fail-close)`:
   - fail-close enforcement is enabled only after replay parity shows deterministic closure in both root/tmp execution contexts.

Promotion freeze triggers (any hit locks promotion):

1. detection of semantic drift between kernel contracts and governance/review projection tables.
2. mismatch between derived prompt metadata (`digest/version/contract IDs`) and runtime report values.
3. boundary replay showing instance-side writes outside allowed runtime/protocol-feedback surfaces.
4. unresolved replay variance between root/tmp runs for the same payload.
5. protocol-entry starvation under boundary lock (protocol context detected but forced instance fallback without candidate/inquiry receipt chain).

Evidence bundle required for Phase-B -> Phase-C transition:

1. kernel-to-validator mapping report (`coverage=100`, `orphan_count=0`).
2. prompt derivation conformance report (metadata/hash aligned).
3. write-boundary replay with deterministic fail-close code (`IP-KERNEL-WRITE-001`).
4. parity replay proof (same inputs, root/tmp equivalent outcomes).
5. protocol-entry non-starvation replay proof (explicit protocol/lane-lock/candidate positive path + silent-fallback negative path).

### 8.2 Cross-Verification Verdict and Implementation Hardening (2026-03-05)

Cross-verification bundle (`v16-xverify-20260305-r2`) intake scope:

1. `T1 roundtable`:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
2. `T2 vendor`:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
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
5. Runtime replay anchors:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
   - `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
   - `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`

Deterministic verdict:

1. Direction is confirmed: kernel-first + dual-lane governance remains valid and non-conflicting with vendor/spec tracks.
2. Execution closure is incomplete: same-lineage replay still shows `update all_ok=true` while three-plane reports semantic block (`IP-SEM-001`) and full-scan summary remains `p0=1`.
3. Requirement status consequence:
   - `ASB16-RQ-029` remains `SPEC_READY` until canonical semantic receipt + convergence validator are implemented.
   - `ASB16-RQ-015` remains `SPEC_READY` until prompt capability matrix fields are produced and wired to fail-close gate.
   - `ASB16-RQ-030` remains `SPEC_READY` until `T1..T4` quorum has automated hard-blocking (not checklist-only).

Mandatory positive-strengthening sequence (non-regression constrained):

1. `S0 shadow`: add semantic convergence comparator that emits `mismatch_count` and lineage refs without blocking release.
2. `S1 dual-write`: strict update emits canonical semantic block fields (`semantic_routing_status/error_code/evidence_path/source/reason`) consumed by three-plane/full-scan.
3. `S2 fail-close`: enable convergence blocker `IP-SEM-CONV-001` only after root/tmp parity replay is stable for two consecutive runs.
4. `S3 intake hard-gate`: implement validator that blocks promotion when any `T1..T4` track or mandatory metadata field is missing.
5. `S4 baseline guard`: keep instance/protocol lane split and kernel write-boundary lock unchanged during all S0..S3 phases.

Promotion policy impact:

1. This section upgrades evidence quality and terminology consistency.
2. It does not promote any P0/P1 row to `DONE` by itself.
3. Any promotion claim without S0..S3 implementation evidence is invalid.

### 8.3 v1.5 closure boundary vs v1.6 positive supplementation boundary (2026-03-05, normalization)

Boundary matrix:

1. `v1.5` closure lane (frozen historical governance track):
   - managed only in `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` + corresponding v1.5 review ledger.
   - no v1.6 section may rewrite v1.5 release verdicts or status rows.
2. `v1.6` positive supplementation lane (forward-only):
   - current pilot scope includes `ASB16-RQ-025..031`.
   - instance-level self-drive prompt strengthening evidence is admissible only as intake/proof-of-direction, not as release-status promotion.

Deterministic interpretation for `ASB16-RQ-031`:

1. Prompt text importing protocol-kernel contracts is required baseline strengthening.
2. Promotion remains blocked until executable coupling is implemented and replay-convergent:
   - mapping validator wired,
   - actor-explicit strict chain convergent,
   - trigger/knowledge/arbitration sample-proof set pass.
3. Therefore current state remains `SPEC_READY`; pilot intake (`review FIX16-026`) is positive evidence but non-promotional by design.

### 8.4 Final T1/T2/T3/T4 cross-verification reinforcement (2026-03-05, network re-check)

Cross-verification bundle (`v16-final-xverify-20260305-r3`) scope:

1. machine anchor:
   - `/tmp/v16_final_xverify_bundle_20260305.json`
2. `T1 roundtable`:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
3. `T2 vendor`:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
   - `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts`
   - `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
   - `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
4. `T3 openai_context`:
   - `https://developers.openai.com/codex/skills/`
   - `https://developers.openai.com/codex/security/#common-sandbox-and-approval-combinations`
   - `https://platform.openai.com/docs/guides/function-calling#strict-mode`
   - `context7:/openai/skills`
5. `T4 protocol_spec`:
   - `https://modelcontextprotocol.io/specification/latest`
   - `https://agentskills.io/specification`
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
   - `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`

Deterministic reinforcement verdict:

1. No external contradiction was found against v1.6 direction (`kernel-first`, `dual-lane`, `fail-close`).
2. The four-track evidence quorum is materially stronger than checklist-only intake; however, this remains evidence-level reinforcement, not executable closure.
3. Status consequence remains unchanged:
   - `ASB16-RQ-015` -> `SPEC_READY` (capability matrix validator not implemented);
   - `ASB16-RQ-029` -> `SPEC_READY` (semantic convergence validator not implemented);
   - `ASB16-RQ-030` -> `SPEC_READY` (quorum hard-gate automation not implemented);
   - `ASB16-RQ-031` -> `SPEC_READY` (prompt-kernel executable coupling + multimodal sample-proof chain not implemented).

Mandatory forward strengthening (v1.6 only):

1. `F1` enforce actor-explicit strict replay for promotion-grade evidence.
2. `F2` automate `T1..T4` quorum validator and fail-close missing tracks.
3. `F3` ship semantic single-source convergence comparator + canonical receipt fields.
4. `F4` bind multimodal sample-proof outputs to kernel->validator mapping fields.
5. `F5` preserve v1.5 freeze boundary; no status back-projection from v1.6 intake.

Promotion boundary:

1. This section is an evidence-hardening addendum only.
2. It cannot directly promote any requirement to `DONE`.
3. Independent executable replay audit remains mandatory before any promotion claim.

### 8.5 Batch-1 row-level strengthening profile (`ASB16-RQ-001..005`, 2026-03-05)

Scope rule:

1. This profile hardens only Batch-1 (`ASB16-RQ-001..005`) after architect+audit cross-review.
2. Status remains `SPEC_READY` until kernel anchors + script gates + mapping projection are all implemented and replay-proven.
3. This profile is non-promotional by design; it tightens closure predicates and removes ambiguity.

Mandatory P0 constraints (must all hold together):

1. `RQ-001` unlock formula must be acyclic:
   - `D1..D5` + `P0` status set are inputs;
   - `D6` is derived output only, never an input predicate.
2. `RQ-002` capability boundary must use explicit mapping table:
   - code-based default mapping + auditable override entry (`override_reason`, `reviewer_ref`, `timestamp`).
3. `RQ-003` promotion receipts must be non-repudiable:
   - required: `decision_hash`, `input_hash`, `reviewer_role`, `reviewer_signature_ref`, `evidence_bundle_refs`.
4. `RQ-004` outlet matrix must include negative paths:
   - governed pass + bypass/direct/manual fail-close set;
   - must bind to `ASB16-RQ-032` send-time headstamp gate.
5. `RQ-005` sidecar/direct equivalence must use normalized payload hash:
   - compare semantic fields after noise stripping (timestamps/path tails/runtime-only artifacts).
6. Mapping lock states cannot be hand-filled:
   - `kernel_locked/script_locked/full_locked` must be scanner-computed.
7. Every mapping row must include ownership and gate:
   - `owner_role`, `acceptance_gate`, `implementation_state`.

Implementation guardrail (to avoid false-closure claims):

1. As of this batch (`2026-03-05`), scanner-computed requirement is normative but implementation is pending.
2. Until scanner script is landed, any lock fields are evidence-only/provisional and cannot be used for promotion.
3. Promotion eligibility remains blocked unless scanner output is machine-generated and attached as replay receipt.

Batch-1 mapping tuple (mandatory five-link anchor per row):

| Requirement ID | kernel_ref target (v1.6) | runtime_ref target (v1.6) | mapping_ref target (v1.6) | validator_ref target (v1.6 planned) | Anchor state (current batch) |
| --- | --- | --- | --- | --- | --- |
| ASB16-RQ-001 | `rq_001_unlock_formula_contract_v1` | deterministic unlock output profile (`unlock_allowed`, `decision_gates`, `p0_*`, blockers, evidence refs) | `identity/protocol/mappings/contract-binding.v1.6.yaml#ASB16-RQ-001` | `scripts/validate_unlock_formula.py` | `PARTIAL (validator + lane hooks landed; deterministic required=true replay archive pending)` |
| ASB16-RQ-002 | `rq_002_capability_boundary_contract_v1` | capability boundary output profile (`boundary_classification`, `classification_source`) | `identity/protocol/mappings/contract-binding.v1.6.yaml#ASB16-RQ-002` | `scripts/validate_capability_boundary_classification.py` | `PARTIAL (validator + lane hooks landed; deterministic required=true replay archive pending)` |
| ASB16-RQ-003 | `rq_003_promotion_evidence_pipeline_contract_v1` | promotion receipt output profile (`decision_hash`, `input_hash`, reviewer fields) | `identity/protocol/mappings/contract-binding.v1.6.yaml#ASB16-RQ-003` | `scripts/validate_promotion_pipeline.py` | `PARTIAL (validator + lane hooks landed; deterministic required=true replay archive pending)` |
| ASB16-RQ-004 | `rq_004_outlet_matrix_contract_v1` | outlet matrix profile (positive + negative + cross-cwd parity lanes) | `identity/protocol/mappings/contract-binding.v1.6.yaml#ASB16-RQ-004` | `scripts/validate_outlet_matrix.py` | `PARTIAL (validator + lane hooks landed; deterministic required=true replay archive pending)` |
| ASB16-RQ-005 | `rq_005_sidecar_cwd_invariance_contract_v1` | sidecar/direct parity profile (`cwd_parity_status`, `passthrough_digest`) | `identity/protocol/mappings/contract-binding.v1.6.yaml#ASB16-RQ-005` | `scripts/validate_sidecar_cwd_parity.py` | `PARTIAL (validator + lane hooks landed; deterministic required=true replay archive pending)` |

Acceptance boundary for Batch-1:

1. For each row, all five anchors must exist:
   - `kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`.
2. `BRIDGE_LOCKED` alone cannot promote status; `KERNEL_LOCKED` and `SCRIPT_LOCKED` must be scanner-verifiable.
3. Until above conditions are met, all rows remain `UNLOCKED` under section `7.3`.
4. Any `PLANNED_ONLY` row in this table is non-promotional and must remain `PENDING_INTAKE`.

### 8.6 Batch-2A row-level strengthening profile (`ASB16-RQ-006..010`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-2A` and covers only `ASB16-RQ-006..010`.
2. It is intentionally separated from later strengthening batches (`ASB16-RQ-014/015/023` and beyond) to avoid ledger/ownership ambiguity.
3. Current decision class for all rows in this batch is `ACCEPT_WITH_FIX` (executable validators landed, replay closure pending, non-promotional).

Current lock snapshot (`7.3` binding, non-overridable by prose):

1. `ASB16-RQ-006..010` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Therefore all rows remain `SPEC_READY` in section `7`, with review state `PENDING_INTAKE`.
3. Any claim that this section alone enables promotion is invalid.

Batch-2A strengthening matrix:

| Requirement ID | Current anchor_state | Strengthening target (kernel + script) | Homomorphism assertion (mandatory) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-006 | `PARTIAL` | add `rq_006_release_plane_cloud_evidence_contract_v1`; wire release-plane cloud evidence validator into readiness + three-plane + full-scan consumption chain | `release_plane_detail.conditions` key-set must be identical across readiness/three-plane/full-scan outputs for same release evidence payload | keep `SPEC_READY/PENDING_INTAKE` until unified validator wiring + replay receipt |
| ASB16-RQ-007 | `PARTIAL` | add `rq_007_cross_cwd_absolute_input_contract_v1`; add cross-cwd scanner gate for root/tmp parity + absolute input enforcement | same payload under protocol-root cwd and tmp cwd must produce identical required verdict fields; missing absolute catalog in non-root replay must fail-close with `IP-CWD-004` semantics | keep `SPEC_READY/PENDING_INTAKE` until parity replay + negative fail-close replay are both archived |
| ASB16-RQ-008 | `PARTIAL` | add `rq_008_docs_bridge_consistency_contract_v1`; governance-review parity checker landed (`scripts/validate_docs_bridge_consistency.py`) and wired into creator/readiness/e2e/full-scan/three-plane/ci | identical docs inputs must generate stable contradiction tuple ordering and stable anchor refs across reruns | keep `SPEC_READY/PENDING_INTAKE` until contradiction replay set is deterministic under required=true archive |
| ASB16-RQ-009 | `PARTIAL` | add `rq_009_run_id_anchored_report_selection_contract_v1`; enforce `run_id -> explicit_report -> binding_match -> mtime_fallback` in shared selector used by freshness/baseline/alignment/readiness/three-plane | for same run-id and candidate set, `report_selected_path` must be identical in freshness + baseline + alignment + readiness + three-plane | keep `SPEC_READY/PENDING_INTAKE` until run-id-first selector is single-sourced and replay-proven under report collision scenarios |
| ASB16-RQ-010 | `PARTIAL` | add `rq_010_phase_a_bootstrap_before_strict_contract_v1`; align readiness flow with update two-phase orchestration and expose phase trace in three-plane/full-scan | strict recovery pass must prove `phase_a_refresh_applied=true` and `phase_b_strict_revalidate_status=PASS_REQUIRED` for qualifying stale-baseline scenario | keep `SPEC_READY/PENDING_INTAKE` until two-phase parity between update/readiness is replay-proven |

Batch-2A mandatory interpretation guard:

1. `ACCEPT_WITH_FIX` is design acceptance only and does not imply implementation closure.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion from this batch is blocked until per-row five-link anchors are implemented (`kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`) and lock-state is scanner-computed.

### 8.7 Batch-3B row-level strengthening profile (`ASB16-RQ-024..028`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-3B` and covers only `ASB16-RQ-024..028` (kernel-first cluster).
2. `Batch-3` label is reserved for `ASB16-RQ-011..015`; future extensions must use suffixed naming (`Batch-3A/3B/...`) to avoid tracker collision.
3. Current decision class for all rows in this batch is `ACCEPT_WITH_FIX` (partial executable landing, replay closure pending, non-promotional).

Current lock snapshot (`7.3` binding, non-overridable by prose):

1. `ASB16-RQ-024..028` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Therefore all rows remain `SPEC_READY` in section `7`, with review state `PENDING_INTAKE`.
3. Any claim that this section alone enables promotion is invalid.

Cross-batch output-field normalization guard (mandatory):

1. `ASB16-RQ-014` must define bootstrap driver semantics only; machine output fields must reuse `ASB16-RQ-015` canonical six-field set.
2. Parallel output families such as `prompt_bootstrap_driver_*` must not replace or fork `ASB16-RQ-015` canonical machine fields.
3. Field-family drift between governance/runtime/review is non-compliant and blocks promotion.

Batch-3B strengthening matrix:

| Requirement ID | Current anchor_state | Strengthening target (kernel + script) | Homomorphism assertion (mandatory) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-024 | `PARTIAL` | add `rq_024_discovery_apply_coverage_fail_closed_contract_v1`; enforce apply-time predicate in `validate_discovery_requiredization.py` (`discovery_required_total>0 && discovery_required_passed==discovery_required_total && discovery_required_coverage_rate==100.0`); reserve `IP-DREQ-002` for coverage mismatch only, move receipt-missing to dedicated code; force discovery coverage gate consumption in `update/readiness/e2e/full-scan/three-plane/ci` | for same requiredization payload and trigger state, `discovery_required_total/passed/coverage/status/error_code` must be identical across update/readiness/e2e/full-scan/three-plane/ci outputs | keep `SPEC_READY/PENDING_INTAKE` until error-code semantics are deconflicted and coverage=100 gate is default-on in all required lanes |
| ASB16-RQ-025 | `PARTIAL` | add `rq_025_kernel_canonical_source_contract_v1`; move v1.6 base-contract origin to `identity/protocol/* + identity/catalog/schema/*`; add `scripts/validate_kernel_ssot_source.py`; keep `validate_protocol_ssot_source.py` as compatibility boundary check | unchanged contract set must yield stable kernel-source census and `unmapped_base_contract_count=0` across reruns | keep `SPEC_READY/PENDING_INTAKE` until kernel-first source rule becomes machine-enforced and docs-projection-only guard is validated |
| ASB16-RQ-026 | `PARTIAL` | machine-readable mapping asset landed (`identity/protocol/mappings/contract-binding.v1.6.yaml`), checker landed (`scripts/validate_contract_mapping_coverage.py`) and wired into creator/readiness/e2e/full-scan/three-plane/ci | mapping checker must output deterministic tuple counts with `coverage_rate=100` and `orphan_count=0` for P0 cluster | keep `SPEC_READY/PENDING_INTAKE` until P0 mapping coverage reaches `100%` with `orphan_count=0` in required=true replay archive |
| ASB16-RQ-027 | `PARTIAL` | add `rq_027_derived_prompt_conformance_contract_v1`; extend `compile_identity_runtime.py` + conformance validator to require `kernel_contract_version`, `kernel_contract_digest`, `derived_from_contract_ids`, `overlay_digest` | same prompt derivation input must produce identical conformance metadata fields and digest chain across reruns | keep `SPEC_READY/PENDING_INTAKE` until derived prompt metadata is generated and consumed by readiness/e2e/full-scan/three-plane validators |
| ASB16-RQ-028 | `PARTIAL` | add `rq_028_instance_write_boundary_lock_contract_v1`; align runtime fail-close code to `IP-KERNEL-WRITE-001` (legacy `IP-GOV-BASE-001` may be compatibility alias only); introduce shared pre-write boundary guard in addition to replay validator | identical forbidden write attempts must yield same boundary verdict + canonical error code in creator/readiness/e2e/full-scan/three-plane/ci | keep `SPEC_READY/PENDING_INTAKE` until pre-write guard + replay validator both enforce canonical write-boundary semantics |

Batch-3B mandatory interpretation guard:

1. `ACCEPT_WITH_FIX` is design acceptance only and does not imply implementation closure.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion from this batch is blocked until per-row five-link anchors are implemented (`kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`) and lock-state is scanner-computed.

### 8.8 Batch-4 row-level strengthening profile (`ASB16-RQ-029/031/032/007/008`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-4` and covers only:
   - `ASB16-RQ-029`
   - `ASB16-RQ-031`
   - `ASB16-RQ-032`
   - `ASB16-RQ-007`
   - `ASB16-RQ-008`
2. Topic split for this batch:
   - `P0 convergence cluster`: `RQ-029/031/032`
   - `P1 bridge cluster`: `RQ-007/008`
3. Current decision class for all rows in this batch is `ACCEPT_WITH_FIX` (executable validators landed for `RQ-029/031/007/008`, replay closure pending, non-promotional).

Current lock snapshot (`7.3` binding, non-overridable by prose):

1. `ASB16-RQ-029/031/032/007/008` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Therefore all rows remain `SPEC_READY` in section `7`, with review state `PENDING_INTAKE`.
3. Any claim that this section alone enables promotion is invalid.

Four-track intake binding guard (mandatory):

1. `T1 roundtable` evidence must remain linked for semantic convergence rationale and lane-boundary interpretation.
2. `T2 vendor` evidence must remain linked for external policy consistency of fail-close and role/sandbox boundaries.
3. `T3 openai_context` evidence must remain linked for strict schema + tool/security guidance alignment.
4. `T4 protocol_spec` evidence must remain linked for MCP/Agent Skills contract compatibility.
5. Missing any track blocks promotion beyond `PENDING_INTAKE`.

Batch-4 strengthening matrix:

| Requirement ID | Current anchor_state | Strengthening target (kernel + script) | Homomorphism assertion (mandatory) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-029 | `PARTIAL` | add `rq_029_semantic_single_source_convergence_contract_v1`; implement canonical semantic receipt fields in validator output (`semantic_routing_status`, `semantic_routing_error_code`, `semantic_routing_evidence_path`, `semantic_routing_reason`, `semantic_routing_source`); add convergence comparator (`IP-SEM-CONV-001`) consuming update/three-plane/full-scan same-lineage artifacts | for same lineage, semantic verdict tuple must be identical across update/three-plane/full-scan; mismatches must produce deterministic `IP-SEM-CONV-001` | keep `SPEC_READY/PENDING_INTAKE` until canonical receipt + convergence comparator are implemented and replay-proven |
| ASB16-RQ-031 | `PARTIAL` | add `rq_031_prompt_import_executable_coupling_contract_v1`; require machine mapping chain (`kernel_contract_ref -> validator_ref -> evidence_ref`) + `actor_context_explicit`; add strict-lane explicit-actor gate (`--actor-id` mandatory for promotion-grade replay) and bind trigger/knowledge/arbitration sample proofs into unified mapping receipt | same prompt-import payload must produce deterministic executable-coupling mapping receipt; text-only uplift without mapping delta must fail-close | keep `SPEC_READY/PENDING_INTAKE` until mapping validator + explicit actor gate + multimodal sample-proof bundle all pass |
| ASB16-RQ-032 | `PARTIAL` | add `rq_032_headstamp_pre_send_hard_gate_contract_v1`; converge runtime error family to canonical `IP-HDSTAMP-001/002/003` (legacy `IP-ASB-STAMP-SESSION-*` allowed only as compatibility alias during transition); ensure governed + direct/manual paths share one pre-send blocking validator and canonical receipt fields (`headstamp_status`, `error_code`, `evidence_ref`, `actor_binding_ref`) | identical negative cases (missing/malformed/mismatch/receipt-missing) must map to identical canonical `IP-HDSTAMP-*` codes across creator/readiness/e2e/full-scan/three-plane/ci | keep `SPEC_READY/PENDING_INTAKE` until pre-send gate is single-sourced and error-family convergence replay passes |
| ASB16-RQ-007 | `PARTIAL` | strengthen `rq_007_cross_cwd_absolute_input_contract_v1`; add cross-cwd comparator (`protocol-root` vs `/tmp`) for readiness/freshness/baseline/alignment chains; enforce absolute `--repo-catalog` for non-root replay with stable `IP-CWD-004` semantics | same payload under protocol-root and `/tmp` must preserve required verdict fields; non-root relative-catalog path must fail-close deterministically | keep `SPEC_READY/PENDING_INTAKE` until root/tmp parity + negative replay archive are both complete |
| ASB16-RQ-008 | `PARTIAL` | add `rq_008_docs_bridge_consistency_contract_v1`; checker landed (`scripts/validate_docs_bridge_consistency.py`) with deterministic tuple sorting + stable anchor refs outputs (`bridge_consistency_status`, `contradiction_pairs`, `governance_anchor_refs`, `review_anchor_refs`) | unchanged docs must produce identical contradiction tuple ordering and identical anchor refs across reruns | keep `SPEC_READY/PENDING_INTAKE` until required=true contradiction replay archive is deterministic |

Batch-4 row-level five-link anchors (mandatory, non-optional):

1. `ASB16-RQ-029`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_029_semantic_single_source_convergence_contract_v1`
   - `runtime_ref`: canonical semantic receipt consumption in `report_three_plane_status.py` + `full_identity_protocol_scan.py`
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-029`
   - `validator_ref`: `scripts/validate_semantic_routing_guard.py` + `scripts/validate_semantic_convergence.py`
   - `acceptance_cmd`: convergence replay command set for update/three-plane/full-scan same-lineage artifacts
   - required convergence comparator outputs: `mismatch_count`, `lineage_ref`, `semantic_convergence_status`, `semantic_convergence_error_code`
2. `ASB16-RQ-031`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md#rq_031_prompt_import_executable_coupling_contract_v1`
   - `runtime_ref`: strict-lane explicit actor gate in creator/readiness/e2e chains
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-031`
   - `validator_ref`: `scripts/validate_prompt_kernel_executable_coupling.py`
   - `acceptance_cmd`: prompt-import executable-coupling replay command set with strict `--actor-id`
   - required compile/runtime hard-gate metadata: `kernel_contract_version`, `kernel_contract_digest`, `derived_from_contract_ids`, `overlay_digest`
   - canonical fail-close codes for this row: `IP-PROMPT-CONTRACT-001` and `IP-ACTOR-CTX-001`
3. `ASB16-RQ-032`:
   - `kernel_ref`: `identity/protocol/IDENTITY_RUNTIME.md#rq_032_headstamp_pre_send_hard_gate_contract_v1`
   - `runtime_ref`: unified pre-send validator shared by governed + direct/manual outbound paths
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-032`
   - `validator_ref`: `scripts/validate_send_time_reply_gate.py` + `scripts/validate_reply_identity_context_first_line.py` + `scripts/validate_v16_headstamp_error_family_convergence.py`
   - `acceptance_cmd`: send-time and compose-path negative replay command set
   - canonical migration rule: `IP-HDSTAMP-*` is v1.6 canonical family; `IP-ASB-STAMP-SESSION-*` is compatibility alias only and cannot be final classification in promotion-grade receipts
4. `ASB16-RQ-007`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_007_cross_cwd_absolute_input_contract_v1`
   - `runtime_ref`: readiness/freshness/baseline/alignment full-chain consumption (not three-plane only)
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-007`
   - `validator_ref`: `scripts/validate_cross_cwd_absolute_input.py`
   - `acceptance_cmd`: protocol-root vs `/tmp` parity replay + non-root relative-catalog fail-close replay
5. `ASB16-RQ-008`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_008_docs_bridge_consistency_contract_v1`
   - `runtime_ref`: governance/review contradiction tuples consumed by release/readiness/full-scan reporting surfaces
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-008`
   - `validator_ref`: `scripts/validate_docs_bridge_consistency.py`
   - `acceptance_cmd`: unchanged-doc deterministic contradiction replay command set

Batch-4 headstamp omission bypass decomposition + fail-close protocol (mandatory, `RQ-032` specific):

1. Why bypass can still happen before closure:
   - governance contract exists, but runtime send surfaces are not yet guaranteed to pass through one non-skippable pre-send gate;
   - validator coverage is currently partial, so some direct/manual output paths can avoid canonical send-time validation;
   - legacy error-family traces (`IP-ASB-STAMP-SESSION-*`) still appear in execution surfaces, indicating migration not fully converged.
2. Non-negotiable fail-close policy (v1.6 promotion-grade):
   - if first-line headstamp is missing or malformed, send must be blocked with canonical `IP-HDSTAMP-001` (`headstamp_missing_or_malformed`);
   - if actor/layer binding mismatches resolved runtime context, send must be blocked with canonical `IP-HDSTAMP-002` (`headstamp_actor_binding_mismatch`);
   - if promotion-grade lane output is missing pre-send machine receipt, send must be blocked with canonical `IP-HDSTAMP-003` (`headstamp_receipt_missing`);
   - no soft-warning mode is allowed for promotion-grade lanes.
3. Unified enforcement source rule:
   - governed compose path and direct/manual outbound path must invoke the same pre-send validator source;
   - route-specific bespoke checks cannot override canonical `IP-HDSTAMP-*` classification.
4. Mandatory pre-send receipt fields for anti-bypass audit:
   - `pre_send_headstamp_checked` (bool)
   - `pre_send_headstamp_gate_status` (`PASS_REQUIRED|FAIL_REQUIRED`)
   - `pre_send_headstamp_error_code` (canonical `IP-HDSTAMP-*` or empty on pass)
   - `pre_send_gate_source`
   - `pre_send_actor_binding_ref`
   - `pre_send_checked_at`
5. Promotion-grade replay obligations (anti-bypass proof set):
   - positive replay: valid dual-headstamp with aligned actor/layer binding must pass on all send surfaces;
   - negative replay A: missing-or-malformed headstamp must deterministically fail with `IP-HDSTAMP-001`;
   - negative replay B: actor/layer binding mismatch must deterministically fail with `IP-HDSTAMP-002`;
   - negative replay C: receipt-missing in promotion-grade lane must deterministically fail with `IP-HDSTAMP-003`;
   - replay outputs must be homomorphic across creator/readiness/e2e/full-scan/three-plane/ci.

Batch-4 mandatory interpretation guard:

1. `ACCEPT_WITH_FIX` is design acceptance only and does not imply implementation closure.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion from this batch is blocked until per-row five-link anchors are implemented (`kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`) and lock-state is scanner-computed.

Batch-4 actor-id fallback recurrence supplement (mandatory, `RQ-031/RQ-032` coupling):

1. Root-cause decomposition for recurring "hard switch" perception:
   - governance already requires strict lanes to use explicit actor binding, but some runtime surfaces still permit empty `--actor-id` input;
   - actor resolver currently remains `explicit actor -> CODEX_ACTOR_ID -> user:$USER` fallback chain;
   - when fallback resolves to `user:*` actor whose actor-session binding points to a different identity, pre-send gate correctly fails with actor-binding mismatch semantics (currently seen as `IP-ASB-STAMP-SESSION-005` on compatibility path), which is often misread as an identity hard-switch bug.
2. Non-negotiable closure rule:
   - promotion-grade lanes must forbid host fallback actor resolution;
   - explicit `--actor-id` is mandatory for compose/send-time/readiness/full-scan/three-plane strict evidence runs;
   - missing explicit actor input must fail-close with canonical actor-context contract code (`IP-ACTOR-CTX-001`) before transport-layer send-time verdict emission.
3. Script anchor convergence target:
   - `scripts/compose_and_validate_governed_reply.py` must not accept promotion-grade execution with empty `--actor-id`;
   - shared actor context guard must emit deterministic proof fields (`actor_id_input_mode`, `resolved_actor_id`, `actor_fallback_used`, `actor_binding_identity_id`, `actor_context_explicit_status`);
   - direct/manual and governed wrapper paths must consume the same actor-context guard output before invoking headstamp send gate.
4. Compatibility migration rule:
   - during migration, `IP-ASB-STAMP-SESSION-005` may exist as compatibility alias in legacy traces;
   - promotion-grade classification must converge to `IP-ACTOR-CTX-001` (actor explicitness fail-close) and canonical `IP-HDSTAMP-*` family for send-time headstamp outcomes.
5. Mandatory acceptance replay (anti-recurrence):
   - negative replay A: invoke compose/send-time strict path without `--actor-id`; expected deterministic fail-close (`IP-ACTOR-CTX-001`) and `actor_fallback_used=true`;
   - negative replay B: invoke strict path with explicit actor that is bound to a different identity; expected deterministic mismatch block and no outbound payload acceptance;
   - positive replay C: invoke strict path with explicit `--actor-id assistant:codex` bound to target identity; expected `PASS_REQUIRED` and canonical first-line headstamp emission;
   - homomorphism requirement: unchanged input must keep identical actor-context verdict tuple across creator/readiness/e2e/full-scan/three-plane/ci.

### 8.9 Batch-5 row-level orchestration strengthening profile (`ASB16-RQ-010/011/012/013/016`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-5` and covers only:
   - `ASB16-RQ-010`
   - `ASB16-RQ-011`
   - `ASB16-RQ-012`
   - `ASB16-RQ-013`
   - `ASB16-RQ-016`
2. Topic split for this batch:
   - `P1 orchestration closure`: `RQ-010/011/012/013/016`
   - `bridge posture`: close execution-lane parity gaps without changing promotion boundary.
3. Current decision class for all rows in this batch is `ACCEPT_WITH_FIX` (executable validators landed, replay closure pending, non-promotional).

Current lock snapshot (`7.3` binding, non-overridable by prose):

1. `ASB16-RQ-010/011/012/013/016` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Therefore all rows remain `SPEC_READY` in section `7`, with review state `PENDING_INTAKE`.
3. Any claim that this section alone enables promotion is invalid.

Four-track intake binding guard (mandatory):

1. `T1 governance` must keep contract clauses + `C10` matrix obligations as normative source.
2. `T2 review` must keep rolling-summary intake rows and decision log synchronized with this section.
3. `T3 scripts` must provide executable anchors; prose-only claims cannot close any row.
4. `T4 external spec/vendor/context` evidence must remain linked through review references and roundtable receipts.
5. Missing any track blocks promotion beyond `PENDING_INTAKE`.
6. Runtime audit snapshot must be timestamped and explicit (`observed_head_sha`, `working_tree_dirty`, `observed_at_utc`) to avoid stale “HEAD/clean” replay claims.

Batch-5 strengthening matrix:

| Requirement ID | Current anchor_state | Strengthening target (kernel + script) | Homomorphism assertion (mandatory) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-010 | `PARTIAL` | add `rq_010_phase_a_bootstrap_before_strict_contract_v1`; keep update two-phase semantics and introduce equivalent readiness orchestration (stale baseline must run phase-A refresh then phase-B strict revalidate); expose phase trace in three-plane/full-scan outputs | qualifying stale-baseline replay must deterministically output `phase_a_refresh_applied=true` and `phase_b_strict_revalidate_status=PASS_REQUIRED` across update/readiness/three-plane/full-scan | keep `SPEC_READY/PENDING_INTAKE` until readiness no longer fail-fast exits on baseline strict preflight and phase trace is machine-consumed |
| ASB16-RQ-011 | `PARTIAL` | add `rq_011_tmp_collision_safe_allocator_contract_v1`; replace identity-only fixed `/tmp` naming in required lanes with allocator-scoped tmp paths (`run_id/correlation_key/lane`), and add collision guard validator replay | same parallel run-set must produce deterministic `collision_count=0`, unique temp artifact paths, and stable digest set across readiness/e2e/three-plane/full-scan | keep `SPEC_READY/PENDING_INTAKE` until allocator + collision guard are landed and concurrent replay receipts are archived |
| ASB16-RQ-012 | `PARTIAL` | add `rq_012_handoff_collab_freshness_autorotation_contract_v1`; preserve existing age fail-close validators while adding deterministic auto-rotation bootstrap + freshness rotation receipt; remove dangling candidate validator references without implementation | unchanged stale handoff/collab inputs must deterministically produce same rotation decision tuple (`rotation_applied`, `freshness_age_days`, `rotation_receipt_ref`, `freshness_status`) across reruns | keep `SPEC_READY/PENDING_INTAKE` until auto-rotation capability is implemented and replay-verified; age-only fail-close is insufficient for closure |
| ASB16-RQ-013 | `PARTIAL` | add `rq_013_protocol_feedback_atomic_emit_contract_v1`; implement single-transaction atomic emit for feedback batch + index linkage + receipt output, with rollback semantics and `transaction_id` evidence | same atomic emit payload must produce deterministic `transaction_id`, `batch_ref/index_ref/receipt_ref` tuple and no partial-write leftovers on failure replays | keep `SPEC_READY/PENDING_INTAKE` until atomic helper + validator are wired into readiness/e2e/three-plane/full-scan/ci consumption lanes |
| ASB16-RQ-016 | `PARTIAL` | add `rq_016_refresh_strict_business_interference_matrix_contract_v1`; introduce machine-readable interference matrix writer + validator and force matrix consumption in update/readiness/three-plane/full-scan | paired replay (`refresh warn` + `strict`) must emit deterministic interference matrix receipt with stable row keys, lane IDs, and verdict tuple | keep `SPEC_READY/PENDING_INTAKE` until matrix fields are machine-emitted and strict replay can be revalidated from receipts |

Batch-5 precision lock (post-audit hardening, mandatory):

1. `RQ-012` historical missing-script blocker is resolved:
   - contract now anchors `scripts/rotate_handoff_collab_freshness.py` + `scripts/validate_handoff_collab_freshness_rotation.py`;
   - missing validator references were removed from pack defaults.
2. `RQ-016` review-binding correction is fixed as:
   - requirement mapping target is `FIX16-017` (refresh->strict + business interference),
   - not `FIX16-016` (prompt capability matrix track).
3. `RQ-016` is field-gap specific and must not be conflated with `RQ-010` phase fields:
   - existing `phase_a_refresh_applied/phase_b_strict_revalidate_status` fields prove two-phase baseline behavior only;
   - they do not satisfy required `business_interference/interference_matrix` output family.

Batch-5 row-level five-link anchors (mandatory, non-optional):

1. `ASB16-RQ-010`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_010_phase_a_bootstrap_before_strict_contract_v1`
   - `runtime_ref`: readiness + update two-phase parity with explicit phase trace consumption in aggregators
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-010`
   - `validator_ref`: `scripts/validate_phase_bootstrap_before_strict.py` + lane consumers (`release_readiness_check.py`, `report_three_plane_status.py`, `full_identity_protocol_scan.py`)
   - `acceptance_cmd`: stale-baseline paired replay command set requiring phase-A/B tuple convergence
2. `ASB16-RQ-011`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_011_tmp_collision_safe_allocator_contract_v1`
   - `runtime_ref`: allocator-scoped tmp artifact generation in readiness/e2e/three-plane/full-scan
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-011`
   - `validator_ref`: `scripts/validate_tmp_collision_safety.py`
   - `acceptance_cmd`: parallel replay command set requiring `collision_count=0`
3. `ASB16-RQ-012`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_012_handoff_collab_freshness_autorotation_contract_v1`
   - `runtime_ref`: deterministic handoff/collab freshness auto-rotation receipt emission
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-012`
   - `validator_ref`: `scripts/rotate_handoff_collab_freshness.py` + `scripts/validate_handoff_collab_freshness_rotation.py`
   - `acceptance_cmd`: stale log rotation replay command set (`validate` + `update` operations)
4. `ASB16-RQ-013`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_013_protocol_feedback_atomic_emit_contract_v1`
   - `runtime_ref`: single-command transactional emit for feedback artifacts
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-013`
   - `validator_ref`: `scripts/emit_protocol_feedback_atomic.py` + `scripts/validate_protocol_feedback_atomic_emit.py`
   - `acceptance_cmd`: atomic emit + rollback replay command set with fixed `transaction_id` tuple checks
5. `ASB16-RQ-016`:
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_016_refresh_strict_business_interference_matrix_contract_v1`
   - `runtime_ref`: refresh->strict paired execution with matrix receipt persistence
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-016`
   - `validator_ref`: `scripts/emit_business_interference_matrix.py` + `scripts/validate_refresh_strict_business_interference.py`
   - `acceptance_cmd`: paired refresh/strict replay command set requiring deterministic interference matrix fields

Roundtable-B5 kickoff package (execution-ready, mandatory before implementation promotion):

1. participants:
   - `base-repo-architect` (owner)
   - `audit-expert(codex)` (verdict)
   - `system-requirements-analyst` (runtime replay evidence)
   - `script owner` (implementation path)
   - `protocol-spec reviewer` (external spec consistency)
2. agenda order (`90 min` baseline):
   - `RQ-010 -> RQ-011 -> RQ-012 -> RQ-013 -> RQ-016`
3. mandatory output schema:
   - `rq_id`, `anchor_state`, `kernel_anchor_path`, `script_anchor_path`, `mapping_anchor_path`, `acceptance_command_set`, `promotion_blocker`, `owner`, `target_commit`.
4. hard exit condition:
   - any row missing `kernel + script + replay` three-piece closure remains `SPEC_READY/PENDING_INTAKE`;
   - `ACCEPT_WITH_FIX` remains non-promotional until lock-state becomes scanner-computed and replay receipts are deterministic.
5. review rubric (three mandatory questions per row):
   - kernel: are contract fields unique and unambiguous?
   - script: is there a single fail-close entrypoint with no bypass lane?
   - receipt: is output machine-replayable (repeatable/comparable/archiveable)?

Batch-5 mandatory interpretation guard:

1. `ACCEPT_WITH_FIX` is design acceptance only and does not imply implementation closure.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion from this batch is blocked until per-row five-link anchors are implemented (`kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance command`) and lock-state is scanner-computed.

### 8.10 Batch-6 row-level cross-workflow governance strengthening profile (`ASB16-RQ-017/018/019/020/021`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-6` and covers only:
   - `ASB16-RQ-017`
   - `ASB16-RQ-018`
   - `ASB16-RQ-019`
   - `ASB16-RQ-020`
   - `ASB16-RQ-021`
2. Topic lock for this batch:
   - four-track evidence contract (`RQ-017`);
   - dedup monotonic winner (`RQ-018`);
   - cross-workflow evidence schema (`RQ-019`);
   - skill path integrity (`RQ-020`);
   - route/workflow publish-version pinning (`RQ-021`).
3. Current decision class for all rows in this batch is `ACCEPT_WITH_FIX` (design accepted, executable closure pending, non-promotional).

Current lock snapshot (`7.3` binding, scanner-computed only):

1. `ASB16-RQ-017/018/019/020/021` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Lifecycle state for all rows remains `SPEC_READY` (decision class `ACCEPT_WITH_FIX`), while synchronized audit verdict is `PASS_WITH_BLOCKERS` for `Task-6..13`.
3. Any prose that claims promotion readiness without scanner lock-state change is invalid.

Four-track binding guard (mandatory in this batch):

1. `T1 governance` provides canonical contract fields and mandatory failure semantics.
2. `T2 review` must keep rolling summary, detail section, and decision log synchronized for this batch.
3. `T3 scripts` must provide executable `validator_ref` and lane-level consumption (`identity_creator`, `release_readiness_check`, `report_three_plane_status`, `full_identity_protocol_scan`, `e2e_smoke_test`).
4. `T4 external evidence` (`roundtable/vendor/openai_context/protocol_spec`) must be represented by machine-readable receipt fields, not checklist-only notes.
5. Missing any track or any required receipt field keeps the section non-promotional and prevents audit upgrade to full `PASS_REQUIRED` closure.

Batch-6 strengthening matrix (explicit hook plan, mandatory):

| Requirement ID | Current anchor_state | Kernel contract + mandatory fields | Concrete script hook plan (must all be wired) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-017 | `PARTIAL` | add `rq_017_multi_track_cross_verification_contract_v1`; required output fields: `t1_status`, `t2_status`, `t3_status`, `t4_status`, `cross_verification_bundle_id`, `source_url_set`, `reference_timestamp_utc`, `conflict_reconciliation_note` | canonical parser must be single-source: `scripts/validate_v16_intake_evidence_core.py --mode intake_contract`; `scripts/validate_v16_cross_verification_tracks.py` may exist only as wrapper (no independent field parsing); call chain: `scripts/identity_creator.py` (update/validate preflight) -> `scripts/release_readiness_check.py` (hard gate) -> `scripts/report_three_plane_status.py` + `scripts/full_identity_protocol_scan.py` (consume canonical receipt only) -> `scripts/e2e_smoke_test.sh` (negative replay with missing track/metadata) | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until four-track quorum + four intake metadata fields are machine-enforced as single fail-close verdict |
| ASB16-RQ-018 | `PARTIAL` | `rq_018_dedup_monotonic_winner_contract_v1` validator is implemented, but deterministic replay evidence for required=true concurrency windows remains incomplete | keep canonical validator path `scripts/validate_v16_dedup_monotonicity.py` (wrapper delegating to semantic core) and keep hooks active in creator/readiness/three-plane/full-scan/e2e/ci; aggregate only canonical `winner_id`/`winner_reason` fields | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until same-input parallel replay proves deterministic winner tuple across lanes |
| ASB16-RQ-019 | `PARTIAL` | `rq_019_cross_workflow_evidence_schema_contract_v1` normalizer+validator are implemented and lane-wired, but replay archive closure remains pending | keep canonical pair `scripts/normalize_v16_cross_workflow_evidence.py` + `scripts/validate_v16_cross_workflow_schema.py`; keep creator/readiness/three-plane/full-scan/e2e/ci consuming canonical schema fields only | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until cross-workflow schema is canonicalized and hash replay is deterministic |
| ASB16-RQ-020 | `PARTIAL` | `rq_020_skill_path_integrity_contract_v1` validator is implemented and lane-wired; out-of-layout/missing-path replay archive still pending | keep `scripts/validate_v16_skill_path_integrity.py` as single fail-close gate; capability-activation remains source-only; retain creator/readiness/three-plane/full-scan/e2e/ci consumption | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until skill path checks are layout-anchored and fail-close on out-of-layout references |
| ASB16-RQ-021 | `PARTIAL` | `rq_021_route_workflow_version_pinning_contract_v1` emitter-before-gate sequence is implemented; required=true replay archive still pending | keep phase order (`scripts/emit_route_version_pin_receipt.py` -> `scripts/validate_route_version_pinning.py`) and retain creator/readiness/three-plane/full-scan/e2e/ci hooks; CI/route metrics remain supplemental only | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until emitter proof source and mismatch fail-close are replay-proven |

Batch-6 row-level five-link anchors (mandatory, non-optional):

1. `ASB16-RQ-017`
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_017_multi_track_cross_verification_contract_v1`
   - `runtime_ref`: four-track canonical quorum receipt consumed by all mandatory lanes
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-017`
   - `validator_ref`: `scripts/validate_v16_intake_evidence_core.py --mode intake_contract` (wrapper alias `scripts/validate_v16_cross_verification_tracks.py` allowed only if parser is delegated)
   - `acceptance_cmd`: four-track quorum replay command set (positive all-present + negative missing-track)
2. `ASB16-RQ-018`
   - `kernel_ref`: `identity/protocol/IDENTITY_RUNTIME.md#rq_018_dedup_monotonic_winner_contract_v1`
   - `runtime_ref`: monotonic dedup winner receipt with deterministic tiebreak
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-018`
   - `validator_ref`: `scripts/validate_v16_dedup_monotonicity.py`
   - `acceptance_cmd`: same-`run_id` concurrent claim replay requiring stable `winner_id`
3. `ASB16-RQ-019`
   - `kernel_ref`: `identity/protocol/IDENTITY_RUNTIME.md#rq_019_cross_workflow_evidence_schema_contract_v1`
   - `runtime_ref`: normalized cross-workflow schema receipt with stable `evidence_hash`
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-019`
   - `validator_ref`: `scripts/validate_v16_cross_workflow_schema.py`
   - `acceptance_cmd`: schema-required-field replay + hash consistency check
4. `ASB16-RQ-020`
   - `kernel_ref`: `identity/protocol/IDENTITY_RUNTIME.md#rq_020_skill_path_integrity_contract_v1`
   - `runtime_ref`: active-layout skill-path proof receipt
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-020`
   - `validator_ref`: `scripts/validate_v16_skill_path_integrity.py`
   - `acceptance_cmd`: in-layout pass + out-of-layout fail-close replay
5. `ASB16-RQ-021`
   - `kernel_ref`: `identity/protocol/IDENTITY_RUNTIME.md#rq_021_route_workflow_version_pinning_contract_v1`
   - `runtime_ref`: route/workflow publish-version pin proof receipt
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-021`
   - `validator_ref`: `scripts/validate_route_version_pinning.py`
   - `acceptance_cmd`: pinned-positive + mismatch-negative replay set

Batch-6 acceptance command set (normative executable set; replay closure still required):

```bash
python3 scripts/validate_v16_intake_evidence_core.py --mode intake_contract --catalog <LOCAL_CATALOG> --identity-id <ID> --bundle-id <BUNDLE_ID> --operation readiness --json-only
python3 scripts/validate_v16_dedup_monotonicity.py --catalog <LOCAL_CATALOG> --identity-id <ID> --run-id <RUN_ID> --parallel-claims 5 --json-only
python3 scripts/validate_v16_cross_workflow_schema.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation three-plane --json-only
python3 scripts/validate_v16_skill_path_integrity.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation readiness --json-only
python3 scripts/emit_route_version_pin_receipt.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation readiness --route-endpoint <ROUTE_ENDPOINT> --workflow-id <WORKFLOW_ID> --workflow-publish-version <WORKFLOW_PUBLISH_VERSION> --out <PIN_RECEIPT_PATH> --json-only
python3 scripts/validate_route_version_pinning.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation readiness --receipt <PIN_RECEIPT_PATH> --expected-route-endpoint <ROUTE_ENDPOINT> --expected-workflow-id <WORKFLOW_ID> --expected-workflow-publish-version <WORKFLOW_PUBLISH_VERSION> --json-only
```

Passing criteria:

1. All validators must return `PASS_REQUIRED` on positive replay and deterministic `FAIL_REQUIRED` on matched negative replay.
2. `report_three_plane_status` and `full_identity_protocol_scan` must consume canonical verdict fields from validator receipts (no local inference forks).
3. `validate_required_contract_coverage.py` `TARGETS` and three-plane/full-scan payload extractors must include `RQ-017..021` gates; omission is treated as lock-computation failure.
4. Any missing validator, missing required field, or lane bypass keeps the row non-promotional (`ACCEPT_WITH_FIX`) and blocks audit upgrade to full `PASS_REQUIRED`.

Batch-6 execution hook closure snapshot (Task-6..13 + audit sync):

1. landed commits:
   - `9e59e0f`, `f63eb55`, `e214df9`, `9c0cf0a`, `19d02ab`, `b5a191c`, `fffc3c3`, `08c8f89`, `5f7eb44`, `228ba40`, `b7137e3`, `47f2f38`, `b258982`, `1beeb88`.
2. lane hook coverage now includes:
   - `identity_creator.py` (validate/update preflight),
   - `release_readiness_check.py`,
   - `report_three_plane_status.py`,
   - `full_identity_protocol_scan.py`,
   - `e2e_smoke_test.sh`,
   - `.github/workflows/_identity-required-gates.yml`.
3. task-level audit results (normalized):
   - `Task-6..13`: `PASS_WITH_BLOCKERS` (hooks landed; deterministic replay/semantic closure pending at audit time).
   - follow-up closure (`Task-15`, `1beeb88`): dedup path fallback + UTC receipt determinism + governance status drift correction reached `PASS_REQUIRED` on blocker items.
4. this snapshot does not change promotion posture:
   - lifecycle remains `SPEC_READY` with decision class `ACCEPT_WITH_FIX`;
   - audit remains `PASS_WITH_BLOCKERS` until deterministic positive/negative replay archive is complete (`Task-15` closed a blocker subset to `PASS_REQUIRED`).

### 8.11 Batch-7 row-level closure profile (`ASB16-RQ-022/030`, 2026-03-06)

Scope rule:

1. This section is explicitly `Batch-7` and covers only:
   - `ASB16-RQ-022`
   - `ASB16-RQ-030`
2. Topic lock for this batch:
   - fallback taxonomy normalization (`RQ-022`);
   - intake evidence quorum automation (`RQ-030`).
3. Current decision class for both rows is `ACCEPT_WITH_FIX` (design accepted, implementation pending, non-promotional).

Current lock snapshot (`7.3` binding, scanner-computed only):

1. `ASB16-RQ-022/030` remain `KERNEL_LOCKED=NO`, `SCRIPT_LOCKED=NO`, `FULL_LOCK verdict=UNLOCKED`.
2. Lifecycle for both rows stays `SPEC_READY` with decision class `ACCEPT_WITH_FIX`; synchronized audit verdict is `PASS_WITH_BLOCKERS`.
3. No prose in this section can override scanner-computed lock-state.

Batch-7 strengthening matrix (explicit hook plan, mandatory):

| Requirement ID | Current anchor_state | Kernel contract + mandatory fields | Concrete script hook plan (must all be wired) | Promotion guard |
| --- | --- | --- | --- | --- |
| ASB16-RQ-022 | `PARTIAL` | add `rq_022_fallback_taxonomy_normalization_contract_v1`; required fields: `fallback_reason_raw`, `fallback_taxonomy_class`, `taxonomy_version`, `normalization_status`, `normalization_error_code` | new `scripts/validate_fallback_taxonomy_normalization.py`; add normalization stage at `scripts/response_stamp_common.py` output boundary; **namespace separation is mandatory**: fallback taxonomy fields must not overwrite existing blocker taxonomy (`auth_login_required` etc.); enforce in `scripts/release_readiness_check.py`; consume same normalized class in `report_three_plane_status.py`, `full_identity_protocol_scan.py`, and `e2e_smoke_test.sh` | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until all fallback reasons deterministically map to governed enum (`data_missing/model_weak_signal/transport_error/policy_blocked`) without altering blocker taxonomy chain |
| ASB16-RQ-030 | `PARTIAL` | add `rq_030_intake_evidence_quorum_contract_v1`; required fields: `t1_roundtable_status`, `t2_vendor_status`, `t3_openai_context_status`, `t4_protocol_spec_status`, `cross_verification_bundle_id`, `source_url_set`, `reference_timestamp_utc`, `conflict_reconciliation_note` | canonical parser must reuse `scripts/validate_v16_intake_evidence_core.py --mode promotion_gate`; wrapper `scripts/validate_v16_intake_evidence_quorum.py` may exist only as delegated mode entry; call chain: `identity_creator` preflight -> readiness hard gate -> three-plane/full-scan promotion gate -> e2e negative replay with missing track/metadata; fail-close must be single entrypoint (no checklist bypass) | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until four-track+four-metadata quorum is automated as promotion blocker across all required lanes |

Batch-7 row-level five-link anchors (mandatory, non-optional):

1. `ASB16-RQ-022`
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_022_fallback_taxonomy_normalization_contract_v1`
   - `runtime_ref`: normalized fallback class emission at response stamp boundary
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-022`
   - `validator_ref`: `scripts/validate_fallback_taxonomy_normalization.py` (must emit `fallback_reason_raw + fallback_taxonomy_class`, never overwrite blocker taxonomy fields)
   - `acceptance_cmd`: taxonomy normalization replay (`positive` mappable set + `negative` unmappable set)
2. `ASB16-RQ-030`
   - `kernel_ref`: `identity/protocol/IDENTITY_PROTOCOL.md#rq_030_intake_evidence_quorum_contract_v1`
   - `runtime_ref`: intake evidence quorum hard gate with four-track/four-metadata receipt
   - `mapping_ref`: `identity/protocol/mappings/contract-binding.v1.6.yaml#asb16-rq-030`
   - `validator_ref`: `scripts/validate_v16_intake_evidence_core.py --mode promotion_gate` (wrapper alias `scripts/validate_v16_intake_evidence_quorum.py` allowed only if parser is delegated)
   - `acceptance_cmd`: quorum replay (`positive` complete bundle + `negative` missing-track/missing-metadata)

Batch-7 acceptance command set (normative executable set; replay closure still required):

```bash
python3 scripts/validate_fallback_taxonomy_normalization.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation three-plane --json-only
python3 scripts/validate_v16_intake_evidence_core.py --mode promotion_gate --catalog <LOCAL_CATALOG> --identity-id <ID> --operation validate --json-only
```

Passing criteria:

1. `RQ-022`: each fallback sample must map to one governed enum class; unmapped raw reason must deterministically fail-close.
2. `RQ-030`: promotion gate must fail-close when any T1/T2/T3/T4 track or any intake metadata field is missing.
3. `validate_required_contract_coverage.py` `TARGETS` and three-plane/full-scan payload extractors must include `RQ-022` + `RQ-030`; omission is treated as lock-computation failure.
4. Positive and negative replay outputs must remain deterministic for unchanged inputs.

Batch-7 execution hook closure snapshot (Task-6..13 + audit sync):

1. landed commits:
   - `f63eb55`, `e214df9`, `4f4930c`, `08c8f89`, `5f7eb44`, `228ba40`, `b7137e3`, `47f2f38`, `b258982`, `1beeb88`.
2. lane hook coverage now includes creator/readiness/three-plane/full-scan/e2e/ci mandatory surfaces.
3. task-level audit results (normalized):
   - `Task-6..13`: `PASS_WITH_BLOCKERS` (automation landed; required=true replay archive pending at audit time).
   - follow-up closure (`Task-15`, `1beeb88`): governance table drift and shared blocker posture synchronized without promotion.
4. this snapshot does not change promotion posture:
   - rows keep lifecycle `SPEC_READY` with decision class `ACCEPT_WITH_FIX`;
   - audit remains `PASS_WITH_BLOCKERS` until required=true replay archive is deterministic and complete.

Roundtable-B6/B7 kickoff package (execution-ready, mandatory before promotion):

1. participants:
   - `base-repo-architect` (owner)
   - `audit-expert(codex)` (verdict)
   - `runtime orchestration owner`
   - `schema owner`
   - `docs bridge owner`
2. input package (`T1..T4` all mandatory):
   - `T1`: governance anchors (`4.10/4.11/4.19`, `7.2`, `7.3`, `C11`, `C19`);
   - `T2`: review intake mappings (`FIX16-018/019/023`);
   - `T3`: script evidence and missing-validator inventory;
   - `T4`: roundtable/vendor/openai-context/protocol-spec receipts.
3. agenda (`90 min` baseline):
   - `RQ-030 -> RQ-018 -> RQ-021 -> RQ-019 -> RQ-020 -> RQ-022 -> RQ-017`.
4. mandatory output schema:
   - `rq_id`, `anchor_state`, `kernel_anchor_path`, `script_anchor_path`, `mapping_anchor_path`, `acceptance_command_set`, `promotion_blocker`, `owner`, `target_commit`.
5. hard exit condition:
   - any row missing `kernel + script + replay` three-piece closure remains non-promotional (`ACCEPT_WITH_FIX`) and cannot upgrade audit verdict to full `PASS_REQUIRED`;
   - lock-state must be scanner-computed; manual override is prohibited.

Batch-6/7 mandatory interpretation guard:

1. `ACCEPT_WITH_FIX` is design acceptance only and does not imply implementation closure.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. Promotion from Batch-6/7 is blocked until per-row five-link anchors are implemented and replay determinism is proven in required lanes.

Batch-6/7 post-audit blocker hardening addendum (mandatory, 2026-03-06):

1. Mapping asset is a hard prerequisite:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml` (and parent directory `identity/protocol/mappings`) must be landed before any lock computation for `RQ-017..022/030`.
   - without this asset, lock-state for this batch is interpreted as `BLOCKED_MAPPING_ASSET_MISSING` and cannot be promoted.
2. `RQ-017` and `RQ-030` must share one core parser and one canonical field schema:
   - canonical implementation: `validate_v16_intake_evidence_core.py` with `--mode intake_contract|promotion_gate`;
   - separate wrappers may exist for ergonomics, but parser logic duplication is prohibited.
3. `RQ-021` must follow emitter-before-gate order:
   - first emit publish-version proof receipt (`route_endpoint`, `workflow_id`, `workflow_publish_version`, `pin_proof_ref`);
   - then enforce pinning gate; gate without emitter proof source is invalid.
4. `RQ-022` must keep taxonomy namespaces separated:
   - normalization output is `fallback_reason_raw + fallback_taxonomy_class`;
   - existing blocker taxonomy fields must remain unchanged and must not be overwritten by fallback normalization.
5. Coverage aggregation is part of closure, not optional:
   - new gates (`RQ-017..022/030`) must be added to `validate_required_contract_coverage.py` `TARGETS`;
   - three-plane/full-scan payload extraction must include corresponding verdict fields for scanner-computed locks.

Batch-6/7 revised execution order (hard sequencing):

1. Land mapping base asset (`identity/protocol/mappings/contract-binding.v1.6.yaml`) with rows for `RQ-017..022/030`.
2. Implement intake evidence core validator (single parser, dual mode) for `RQ-017` + `RQ-030`.
3. Implement `RQ-022` fallback taxonomy normalization with dual fields (`raw + class`) and namespace separation from blocker taxonomy.
4. Implement `RQ-021` publish-version receipt emitter first, then pinning gate.
5. Wire all seven gates into coverage aggregator + three-plane/full-scan payload extraction before any lock or promotion claim.

### 8.12 Write-Boundary Non-Starvation Guard (`ASB16-RQ-028/031`, 2026-03-06)

Scope:

1. this addendum hardens the boundary semantics of `RQ-028` without creating a new requirement line.
2. purpose is to prevent recurrence of the historical "boundary lock becomes protocol-entry lock" regression class.

Hard rules (normative):

1. boundary lock governs write targets only and must execute after lane resolution.
2. boundary lock must not mutate `resolved_work_layer`, `applied_gate_set`, or `protocol_entry_decision`.
3. protocol entry must stay live when any of the following is true:
   - explicit `work_layer=protocol`;
   - `session_lane_lock=protocol`;
   - candidate bridge resolves to `PROTOCOL_DIRECT` or `PROTOCOL_CANDIDATE`.
4. protocol-context fallback to instance without candidate/inquiry receipt chain is prohibited and fail-closed.
5. canonical code convergence:
   - boundary violation canonical code remains `IP-KERNEL-WRITE-001` (legacy `IP-GOV-BASE-001` may remain compatibility alias only);
   - protocol-entry fallback path uses canonical current validators (`IP-LAYER-GATE-006/007`, `IP-LAYER-CAND-001..004`).

Required telemetry tuple (machine-auditable, lane-consumed):

1. `intent_source`
2. `protocol_context_detected`
3. `session_lane_lock`
4. `lane_resolution_decision`
5. `lane_resolution_error_code`
6. `applied_gate_set`
7. `base_repo_write_boundary_status`

Mandatory replay matrix (hard gate):

1. positive A: explicit `work_layer=protocol` with boundary enabled must produce `applied_gate_set=protocol_required_checks`.
2. positive B: `session_lane_lock=protocol` under weak signal must still resolve to protocol lane.
3. positive C: `PROTOCOL_CANDIDATE` must produce `QUESTION_REQUIRED/EVIDENCE_PENDING` chain with candidate/inquiry receipts.
4. negative D: instance write attempt to forbidden surface must fail-close with canonical boundary code (alias tolerated only during migration).
5. negative E: protocol-context fallback without candidate/inquiry chain must fail-close with deterministic lane/candidate error code.
6. convergence F: unchanged lineage input must preserve telemetry tuple parity across update/three-plane/full-scan.

Promotion guard:

1. this addendum is non-promotional by itself.
2. rows remain `SPEC_READY/PENDING_INTAKE` until replay matrix above is implemented and consumed by required lanes.

### 8.13 Prompt Bootstrap Kernel Source Continuity Guard (`ASB16-RQ-014/015/027/031`, 2026-03-06)

Decision lock:

1. protocol layer must not add same-name runtime artifact file `identity/protocol/IDENTITY_PROMPT.md`.
2. protocol-side prompt baseline source is tracked via `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`.
3. runtime prompt artifact remains pack-local (`identity/packs/<id>/IDENTITY_PROMPT.md` or resolved runtime pack path).

Continuous-update requirements (non-optional):

1. every update to prompt bootstrap kernel source must include capability-ingestion delta against identity base protocol capability set.
2. every update must define validator delta + replay obligations before any status promotion claim.
3. every update must carry four-track evidence metadata:
   - `cross_verification_bundle_id`
   - `source_url_set`
   - `reference_timestamp_utc`
   - `conflict_reconciliation_note`
4. prompt-bootstrap kernel source must maintain a full capability-absorption matrix against identity base protocol capability domains; row loss or stale anchor mapping is non-compliant.
5. prompt-bootstrap kernel source must keep append-only update ledger entries with `updated_at_utc`, `capability_delta`, `validator_delta`, `replay_obligations`, and `commit_sha`.

Machine hard-gate binding (required for lane consumption):

1. continuity constraints in this section must be enforced by dedicated validator:
   - planned validator hook (script path remains reserved until implementation lands in `scripts/`)
2. validator output fields are canonical and must be emitted without rename:
   - `prompt_bootstrap_continuity_status`
   - `error_code`
   - `missing_matrix_rows`
   - `stale_ledger`
   - `dead_anchors`
   - `evidence_ref`
3. fail-close classification (deterministic):
   - matrix incomplete -> `IP-PROMPT-CONT-002`
   - ledger stale or missing -> `IP-PROMPT-CONT-003`
   - dead/missing anchor -> `IP-PROMPT-CONT-004`
4. required lane consumption surfaces:
   - `identity_creator`
   - `release_readiness_check`
   - `report_three_plane_status`
   - `full_identity_protocol_scan`
   - `e2e_smoke_test`
5. acceptance replay hook is reserved as planned validator binding (activate only after script implementation lands in `scripts/` and command-contract checker can resolve it).

Five-link closure requirements:

1. `RQ-014`: bootstrap capability contract source + fail-close coverage validator.
2. `RQ-015`: canonical six-field capability matrix output and fail-close validator.
3. `RQ-027`: derived prompt conformance metadata tuple (`kernel_contract_version`, `kernel_contract_digest`, `derived_from_contract_ids`, `overlay_digest`).
4. `RQ-031`: executable coupling chain (`kernel_contract_ref -> validator_ref -> evidence_ref`) + explicit actor gate.
5. all four rows must close mapping + validator + lane consumption replay before promotion beyond `PENDING_INTAKE`.

Promotion guard:

1. adding this kernel source is structural hardening only.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` remains mandatory until executable closure is replay-proven.

### 8.14 Emergency Hotfix Track - FQG Multi-Agent × Multi-Identity Switch Guard (`HOTFIX16-P0-001`, 2026-03-06)

Scope and isolation lock:

1. this is an emergency hotfix intake track for architect escalation and is intentionally isolated from `FIX16-001..037` batch normalization.
2. this section does not rewrite or reinterpret existing requirement rows in section `7`; it adds a P0 incident guardrail package for multi-agent multi-identity runtime safety.
3. runtime bridge hardening is landed locally, but lifecycle remains non-promotional until independent rollout/audit closure is completed.
4. naming follows v1.5 hotfix-lane convention (`HOTFIX-P0-*`), while using v1.6-specific prefix `HOTFIX16-P0-*` to avoid cross-version ID collision.

Hard guardrail (non-negotiable):

1. execution-state hard identity switch is prohibited.
2. switch requests during execution states (`RUNNING/TOOL_CALLING/STREAMING` or equivalent) must fail-close.
3. switch is allowed only in guarded safe states (`WAITING_INPUT` / `DONE_WAITING_INPUT` baseline profile).

`allow_shared_session` semantic lock:

1. `allow_shared_session=true` means "allow entering gated switch mode", not "allow direct shared execution".
2. shared session without gated switch handshake is invalid.
3. no business dispatch is allowed before switch handshake verification is complete.

Mandatory switch chain (machine-verifiable):

1. `switch_request` (`from_identity`, `to_identity`, `actor_id`, `session_id`, `request_id`)
2. `pre_switch_gate` (state/policy validation)
3. `switch_apply`
4. `switch_ack` (canonical `Identity-Context` + `Layer-Context` + actor binding tuple)
5. `ack_verify`
6. `dispatch`

Fail-close policy:

1. missing `switch_ack` -> fail-close.
2. mismatched `switch_ack.identity_id` vs target identity -> fail-close.
3. timeout in handshake window -> fail-close.
4. policy/state disallow switch -> fail-close.

Canonical error-code family (reserved for this hotfix track):

1. `IP-SWITCH-GATE-001` (`switch_gate_rejected`)
2. `IP-SWITCH-HS-002` (`switch_handshake_mismatch`)
3. `IP-SWITCH-TIMEOUT-003` (`switch_handshake_timeout`)
4. `IP-SWITCH-STATE-004` (`switch_rejected_in_execution_state`)
5. `IP-SWITCH-POLICY-005` (`shared_session_policy_violation`)

Four-track evidence package (architect intake mandatory):

1. `T1 governance/spec`: explicit binding + switch guard + canonical headstamp fail-close (`v1.6 4.21`, `v1.4.12`, `v1.4.6`).
2. `T2 runtime implementation`: runtime bridge now exposes guarded route metadata (`allow_shared_session`, `switch_ack_ref`, `route_status`, `route_error`) and blocks conflict dispatch with `409` fail-close even under explicit override attempts.
3. `T3 live evidence`: local bridge tests replay pass (`tests/test_chat_inbound.py`, `tests/test_chat_bridge.py`, `28 passed`) including conflict + override bypass negative cases.
4. `T4 hotfix requirement docs`: v2 requirement clarification + v2 protocol-feedback batch package.

Implementation delta (2026-03-07):

1. runtime bridge files landed (fqsh workspace):
   - `src/feiqiao_guard/identity_router.py`
   - `src/feiqiao_guard/main.py`
   - `src/feiqiao_guard/models.py`
   - `src/feiqiao_guard/chat_bridge.py`
2. route conflict invariants added:
   - duplicate `session_id`/`codex_home` without gated shared-session semantics -> conflict issue,
   - inconsistent `switch_ack_ref` under shared mode -> conflict issue.
3. inbound fail-close now covers all identity-route paths (including explicit override).

Architect handoff inputs (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.json`
4. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
5. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
6. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
7. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
8. runtime route snapshot source (remote): `/root/feiqiao-guard/.runtime/identity_routes.json`

Promotion guard:

1. this hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent rollout/audit closure:
   - deployed route snapshot includes `route_status/route_error` fields,
   - conflict `409` + non-conflict success replay archived from live endpoint,
   - switch-ack handshake receipts verified in production pipeline.

### 8.15 Emergency Hotfix Track - Protocol Lane Activation Starvation + Headstamp Continuity (`HOTFIX16-P0-002`, 2026-03-06)

Scope and isolation lock:

1. this is a separate P0 emergency hotfix track and must not be merged into `FIX16-001..037` or `HOTFIX16-P0-001` closure state.
2. this track addresses two coupled runtime blockers only:
   - explicit protocol-governance request cannot deterministically activate `work_layer=protocol`,
   - outbound replies can still be observed without canonical dual headstamp.
3. lane-routing/headstamp guards are landed locally, but lifecycle remains non-promotional until independent rollout/audit closure is completed.

Hard guardrail:

1. explicit protocol governance request must resolve to protocol lane or fail-close with deterministic reason.
2. unresolved protocol route entry is fail-close; silent fallback to instance lane is prohibited.
3. canonical dual headstamp is mandatory on every outbound assistant message, regardless of path (`governed compose` and `direct/manual`).
4. lane activation success without headstamp continuity is invalid for promotion-grade evidence.

Mandatory lane-activation receipt fields (machine-verifiable):

1. `requested_lane`
2. `previous_lane`
3. `resolved_lane`
4. `lane_activation_status`
5. `lane_activation_error_code`
6. `route_source_ref`
7. `lane_activation_evidence_ref`

Canonical error-code family (reserved for this hotfix track):

1. `IP-LANE-ROUTE-001` (`protocol_lane_route_not_configured`)
2. `IP-LANE-ACT-002` (`explicit_protocol_request_downgraded`)
3. `IP-LANE-ACT-003` (`lane_activation_receipt_missing`)
4. `IP-HDSTAMP-001` (`headstamp_missing_or_malformed`)
5. `IP-HDSTAMP-002` (`headstamp_actor_binding_mismatch`)
6. `IP-HDSTAMP-003` (`headstamp_receipt_missing`)

Four-track evidence package (architect intake mandatory):

1. `T1 governance/spec`: protocol entry non-starvation + headstamp pre-send hard-gate (`4.21`, `C22..C26`, v1.4.12/v1.4.6 binding clauses).
2. `T2 runtime implementation`: lane-routing guard and headstamp continuity validators are wired on strict surfaces; route conflict state is now machine-readable via bridge route payload fields.
3. `T3 live evidence`: local replay shows deterministic conflict fail-close and unchanged non-conflict dispatch path (`pytest 28 passed` on inbound + bridge suites).
4. `T4 escalation package`: protocol escalation pack + lane activation receipt + gated-switch requirement/feedback v2 documents.

Implementation delta (2026-03-07):

1. protocol lane conflict is no longer silently downgraded on identity-route paths; conflict emits deterministic block.
2. route summary now carries explicit route error surface for downstream audit pipelines.
3. local runtime replay matrix (positive + negative) is executable and passing; production rollout evidence remains required for promotion.

Architect handoff inputs (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_ESCALATION_PACK_20260306T213707_multiagent_multiidentity.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T213517_protocol_lane_activation_receipt.md`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
4. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
5. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
6. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
7. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
8. runtime route snapshot source (remote): `/root/feiqiao-guard/.runtime/identity_routes.json`

Promotion guard:

1. this hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent rollout/audit closure:
   - live route snapshot confirms non-starvation semantics with canonical route fields,
   - live headstamp continuity replay archive is complete (`positive + negative`),
   - protocol-lane activation receipts are reproducible from production endpoint traces.

### 8.16 Emergency Hotfix Track - Strict-Surface Fixed `/tmp` Path Debt (`HOTFIX16-P1-003`, 2026-03-06)

Scope and isolation lock:

1. this is a separate P1 emergency hotfix track and must not be merged into `FIX16-*` or `HOTFIX16-P0-*` closure states.
2. this track addresses residual fixed `/tmp` output hardcoding in strict surfaces only.
3. resolver contract + strict-chain runtime refactor are landed, but lifecycle remains non-promotional until replay archive + independent audit closure are completed.

Hard guardrail:

1. strict surfaces (`validate/update/readiness/three-plane/full-scan/e2e/ci`) must not rely on fixed `/tmp/<static_name>` defaults.
2. default temp outputs must be dynamic and scoped by `run_id + identity_id + operation`.
3. CI flows must use runner-scoped temp root (`${RUNNER_TEMP}` or equivalent), not fixed `/tmp`.
4. `--out` remains explicit caller override only; absence of `--out` must never imply fixed hardcoded path.

Canonical error-code family (reserved for this hotfix track):

1. `IP-TMPPATH-001` (`fixed_tmp_path_detected_in_strict_surface`)
2. `IP-TMPPATH-002` (`tmp_path_not_identity_run_scoped`)
3. `IP-TMPPATH-003` (`ci_temp_root_not_runner_scoped`)

Four-track evidence package (architect intake mandatory):

1. `T1 governance/spec`: strict-path determinism + replay non-collision requirements.
2. `T2 runtime implementation`: strict-chain temp path resolver landed via `scripts/runtime_temp_path_common.py` and wired into `identity_creator/release_readiness_check/report_three_plane_status/full_identity_protocol_scan/e2e_smoke_test/validate_no_implicit_switch`.
3. `T3 live evidence`: strict-chain static scan confirms fixed `/tmp` literals removed from the above runtime-critical scripts; replay outputs now resolve from runtime temp root (`IDENTITY_RUNTIME_TMP_ROOT` / `RUNNER_TEMP` / `TMPDIR` / system temp).
4. `T4 protocol feedback`: canonical feedback batch + receipt + evidence-index entries for this governance gap.

Implementation delta (2026-03-07):

1. landing commit evidence: `093496b`.
2. added shared temp resolver: `scripts/runtime_temp_path_common.py`.
3. removed strict-chain fixed `/tmp` literals from:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/validate_no_implicit_switch.py`
4. strict-chain helper outputs are now operation/identity scoped, with optional run token scoping for mutation/e2e flows.

Architect handoff inputs (absolute paths):

1. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T140030Z_tmp_hardcoded_path_governance_gap.md`
2. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T140030Z_tmp_hardcoded_path_governance_gap.json`
3. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
4. commit evidence: `4179e47` (partial cleanup baseline)

Promotion guard:

1. this hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires independent replay/audit closure:
   - strict-chain fixed-path detector replay (`zero fixed /tmp literals`),
   - concurrent collision replay (`operation + identity + run scoped temp artifacts`),
   - CI runner-temp parity replay on at least one hosted runner.

### 8.17 Emergency Hotfix Track - Gate-Source Convergence and Requiredization Applicability (`HOTFIX16-P1-004`, 2026-03-07)

Scope and isolation lock:

1. this is a separate P1 emergency hotfix track and must not be merged into `FIX16-*` or earlier hotfix closure states.
2. this track addresses protocol-layer governance semantics only: gate-source convergence, producer-aware/applicability-scoped requiredization, and strict context/writeback determinism.
3. validator deltas are landed in strict-chain scripts, but lifecycle remains non-promotional until replay archive + independent audit closure are completed.

Hard guardrail:

1. lane split itself is not downgraded by this track; instance lane must remain independent from protocol publish gate while preserving protocol-feedback sidecar path.
2. `update` and aggregation surfaces (`three-plane`/`full-scan`) must consume the same gate-source snapshot for the same lineage and must not produce contradictory verdicts.
3. required-contract enforcement must be conditioned by producer readiness + current-round linkage + run-type applicability:
   - history-only activity must not auto-promote a contract into blocking required mode.
   - non-applicable contracts must resolve to explicit `SKIPPED_NOT_REQUIRED`, not synthetic failure.
4. fallback taxonomy must include legal terminal state for "no fallback event in current run" under required surfaces.
5. strict context operations must fail-fast on env/CLI catalog mismatch unless explicit audited override exists.
6. protocol-feedback primary write failure must use controlled spool/reconcile strategy with machine-verifiable receipt chain; silent drop is forbidden.

Canonical error-code family (reserved for this hotfix track):

1. `IP-GSRC-001` (`gate_source_convergence_mismatch`)
2. `IP-GSRC-002` (`required_contract_downgraded_by_optional_branch`)
3. `IP-GSRC-003` (`producer_not_ready_but_required_applied`)
4. `IP-GSRC-004` (`history_only_activity_requiredization_block`)
5. `IP-GSRC-005` (`no_fallback_in_run_legal_state_missing`)
6. `IP-GSRC-006` (`env_cli_catalog_mismatch_without_override`)
7. `IP-GSRC-007` (`protocol_feedback_primary_write_failed_without_reconcile`)

Four-track evidence package (architect intake mandatory):

1. `T1 governance/spec`: lane partition invariants, requiredization scope invariants, and context/writeback fail-close clauses (`C28..C30`).
2. `T2 runtime implementation`: applicability-scoped requiredization fields + observation-profile skip semantics are wired in the Batch-6/7 gates (`intake_core`, `dedup`, `cross_workflow_schema`, `route_version_pinning`, `fallback_taxonomy_normalization`).
3. `T3 replay evidence`: target scan replay now converges to non-failing applicability verdicts (`SKIPPED_NOT_REQUIRED` with machine reasons) instead of synthetic missing-evidence failures on non-current-run inputs.
4. `T4 protocol feedback`: canonical protocol-feedback outbox + upgrade proposal + evidence-index linkage for this hotfix stream.

Implementation delta (2026-03-07):

1. landing commit evidence: `093496b`.
2. producer/applicability fields added to canonical payloads:
   - `run_profile`
   - `producer_readiness`
   - `requiredization_current_round_linked`
3. observation-lane applicability handling landed:
   - non-applicable required contracts emit `SKIPPED_NOT_REQUIRED` with explicit stale reason,
   - no-fallback-event terminal state emits `no_fallback_event_in_current_run`.
4. landing scripts:
   - `scripts/validate_v16_intake_evidence_core.py`
   - `scripts/validate_dedup_monotonicity.py`
   - `scripts/validate_cross_workflow_schema.py`
   - `scripts/validate_route_version_pinning.py`
   - `scripts/validate_fallback_taxonomy_normalization.py`
5. deterministic dedup invariants remain fixed:
   - contract pattern does not hard-lock fallback search,
   - `earliest_claim_ts` normalized to UTC (`Z`) for cross-timezone replay parity.

Architect handoff inputs (canonical channel pattern):

1. `runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*_gate_source_convergence*.md`
2. `runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_*_requiredization_applicability*.md`
3. `runtime/protocol-feedback/evidence-index/INDEX.md`

Promotion guard:

1. this hotfix remains `ACCEPT_WITH_FIX` only at design level.
2. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion requires executable closure tuple:
   - same-lineage update/readiness/three-plane/full-scan convergence replay (`status/error_code` homomorphism),
   - producer/applicability requiredization replay (positive + non-applicable + negative),
   - strict context mismatch fail-fast replay,
   - protocol-feedback spool/reconcile replay proof.

## 9) References

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
3. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
4. `docs/review/protocol-remediation-audit-ledger-v1.6.md`
5. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
6. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`
7. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
8. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
9. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
10. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
11. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
12. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
13. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
14. `https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide/#frequented-asked-questions-faq`
15. `context7:/websites/developers_openai_api (strict schema/tool docs extraction)`
16. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
17. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-unified-feedback-index-2026-03-04.md`
18. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_FQG_MULTIAGENT_MULTIIDENTITY_SWITCH_GUARD_V2_20260306T211854.md`
19. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T134224Z_fqg_multiagent_multiidentity_gated_switch_v2.md`
20. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T210151_fqg_multiagent_multiidentity_blocker.md`
21. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_switch_live_verify_20260306_202556.md`
22. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/custom_creative_ecom_analyst_direct_query_20260306_202049.md`
23. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/office_ops_expert_direct_query_20260306_201211.md`
24. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-discovery-dual-track-simulation-receipt-2026-03-04.md`
25. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-cross-verification-execution-receipt-2026-03-04-roundtable-vendor-context7-openaidoc-skill.md`
26. `https://developers.openai.com/codex/skills/`
27. `https://developers.openai.com/codex/security/`
28. `context7:/websites/developers_openai (Codex skills/security extraction)`
29. `https://github.com/brianlyang/identity-protocol/tree/main/identity`
30. `identity/protocol/IDENTITY_PROTOCOL.md`
31. `identity/protocol/IDENTITY_RUNTIME.md`
32. `identity/protocol/IDENTITY_DISCOVERY.md`
33. `identity/catalog/schema/identities.schema.json`
34. `identity/catalog/identities.yaml`
35. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
36. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
37. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
38. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-v1.6-governance-review-cross-verification-verdict-2026-03-05.md`
39. `https://developers.openai.com/api/reference/resources/responses/`
40. `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
41. `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
42. `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/system-prompts`
43. `https://modelcontextprotocol.io/specification/latest`
44. `https://agentskills.io/specification`
45. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
46. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
47. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
48. `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
49. `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`
50. `https://platform.openai.com/docs/guides/function-calling#strict-mode`
51. `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role`
52. `context7:/openai/skills`
53. `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`
54. `https://developers.openai.com/codex/security/#common-sandbox-and-approval-combinations`
55. `/tmp/v16_final_xverify_bundle_20260305.json`
56. `/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`
57. `/tmp/v16_architect_deep_scan_full_repo_20260305.json`
58. `/tmp/v16_architect_deep_scan_full_repo_20260305.md`
59. `/tmp/v16_one_by_one_requirement_review_20260305.md`
60. `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md`
61. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_ESCALATION_PACK_20260306T213707_multiagent_multiidentity.md`
62. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T213517_protocol_lane_activation_receipt.md`
63. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260306T140030Z_tmp_hardcoded_path_governance_gap.md`
64. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/outbox-to-protocol/PROTOCOL_FEEDBACK_RECEIPT_20260306T140030Z_tmp_hardcoded_path_governance_gap.json`
65. `/Users/yangxi/claude/codex_project/fqsh/.agents/identity/feiqiao-guard-delivery-lead/runtime/protocol-feedback/evidence-index/INDEX.md`
