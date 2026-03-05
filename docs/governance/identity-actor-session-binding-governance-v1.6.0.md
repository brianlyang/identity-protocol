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
3. lock policy applies regardless of work-layer narrative claims.

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
| ASB16-RQ-014 | initial identity prompt must be bootstrap capability-driver native | identity pack templates + prompt bootstrap contracts + strict update lanes | P0 | SPEC_READY | SRA batch `2026-03-04/002` + architect brief |
| ASB16-RQ-015 | prompt capability matrix validator must fail-closed on missing requiredized drivers | new prompt capability validator + required gate wiring | P0 | SPEC_READY | SRA batch `2026-03-04/003` |
| ASB16-RQ-016 | post-core-edit runbook must require refresh->strict and emit business interference matrix | runbook + replay scripts + reporting contracts | P1 | SPEC_READY | SRA batch `2026-03-04/001` + business-impact packet |
| ASB16-RQ-017 | v1.6 intake for bootstrap capability must include roundtable+vendor+openaidoc+context7 cross-verification | review intake checklist + governance evidence contract | P1 | SPEC_READY | SRA evidence index + vendor scan + OpenAI/context7 anchors |
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
| ASB16-RQ-028 | instance lanes must be blocked from protocol-kernel/governance/review writes by default | write-boundary validator + lane enforcement + fail-close error mapping | P0 | SPEC_READY | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-029 | semantic-routing verdict must be single-sourced and convergent across update/three-plane/full-scan for same lineage | canonical semantic receipt + convergence validator + strict update schema uplift | P0 | SPEC_READY | semantic convergence intake (`review v1.6 FIX16-022`) |
| ASB16-RQ-030 | new v1.6 suggestions must satisfy intake evidence quorum (`T1 roundtable + T2 vendor + T3 openai_context + T4 protocol_spec`) before promotion beyond `PENDING_INTAKE` | intake validator/checklist + governance/review bridge + cross-verification metadata schema | P1 | SPEC_READY | intake hard-gate reinforcement (`review v1.6 FIX16-023`) |
| ASB16-RQ-031 | protocol-kernel prompt imports must be executable-coupled and produce multimodal sample-proof closure under explicit actor context | prompt-kernel mapping validator + strict-lane actor-context gate + trigger/knowledge/arbitration sample-proof validators + A/B replay harness | P0 | SPEC_READY | self-drive experiment intake (`review v1.6 FIX16-024`) |

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
| ASB16-RQ-014 | prompt bootstrap capability contract | P0 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-015 | prompt capability matrix fail-closed validator | P0 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-016 | refresh->strict + business interference runbook contract | P1 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-017 | roundtable/vendor/openaidoc/context7 cross-verification contract | P1 | SPEC_READY | SRA intake pending implementation |
| ASB16-RQ-018 | dedup winner determinism contract | P1 | SPEC_READY | office-ops supplemental intake pending implementation |
| ASB16-RQ-019 | cross-workflow evidence schema contract | P1 | SPEC_READY | office-ops supplemental intake pending implementation |
| ASB16-RQ-020 | skill-path integrity contract | P1 | SPEC_READY | office-ops supplemental intake pending implementation |
| ASB16-RQ-021 | route/version pinning contract | P1 | SPEC_READY | office-ops supplemental intake pending implementation |
| ASB16-RQ-022 | fallback taxonomy normalization contract | P1 | SPEC_READY | office-ops supplemental intake pending implementation |
| ASB16-RQ-023 | discovery trigger-conditioned requiredization contract | P0 | SPEC_READY | SRA discovery dual-track intake pending implementation |
| ASB16-RQ-024 | discovery apply-time coverage fail-close contract | P0 | SPEC_READY | SRA discovery dual-track intake pending implementation |
| ASB16-RQ-025 | kernel-first canonical source contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-026 | kernel contract mapping projection contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-027 | derived prompt compilation contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-028 | instance write-boundary lock contract | P0 | SPEC_READY | baseline accepted; implementation pending |
| ASB16-RQ-029 | semantic single-source convergence contract | P0 | SPEC_READY | live replay mismatch confirmed; implementation pending |
| ASB16-RQ-030 | intake evidence quorum hard-gate contract | P1 | SPEC_READY | new suggestion promotion requires `T1..T4` bundle before leaving `PENDING_INTAKE` |
| ASB16-RQ-031 | protocol-kernel prompt import executable coupling contract | P0 | SPEC_READY | requires mapping validator + actor-explicit strict lane + multimodal sample-proof closure before promotion |

### 7.1 v1.6 status delta snapshot (2026-03-03 kickoff)

| Requirement ID | Status delta | Evidence pointer |
| --- | --- | --- |
| ASB16-RQ-001..008 | `NEW -> SPEC_READY` | this document kickoff baseline |
| ASB16-RQ-009..013 | `NEW -> SPEC_READY` | office-ops intake triage bridge (`review v1.5 16.8.75`) |
| ASB16-RQ-014..017 | `NEW -> SPEC_READY` | SRA bootstrap capability intake (`review v1.6 FIX16-015`) |
| ASB16-RQ-018..022 | `NEW -> SPEC_READY` | office-ops supplemental replay intake (`review v1.6 FIX16-019`) |
| ASB16-RQ-023..024 | `NEW -> SPEC_READY` | SRA discovery dual-track simulation intake (`review v1.6 FIX16-020`) |
| ASB16-RQ-025..028 | `NEW -> SPEC_READY` | kernel-first baseline intake (`review v1.6 FIX16-021`) |
| ASB16-RQ-029 | `NEW -> SPEC_READY` | semantic convergence intake (`review v1.6 FIX16-022`) |
| ASB16-RQ-030 | `NEW -> SPEC_READY` | intake hard-gate reinforcement (`review v1.6 FIX16-023`) |
| ASB16-RQ-031 | `NEW -> SPEC_READY` | self-drive experiment intake (`review v1.6 FIX16-024`) |

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

Evidence bundle required for Phase-B -> Phase-C transition:

1. kernel-to-validator mapping report (`coverage=100`, `orphan_count=0`).
2. prompt derivation conformance report (metadata/hash aligned).
3. write-boundary replay with deterministic fail-close code (`IP-KERNEL-WRITE-001`).
4. parity replay proof (same inputs, root/tmp equivalent outcomes).

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
18. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-discovery-dual-track-simulation-receipt-2026-03-04.md`
19. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-cross-verification-execution-receipt-2026-03-04-roundtable-vendor-context7-openaidoc-skill.md`
20. `https://developers.openai.com/codex/skills/`
21. `https://developers.openai.com/codex/security/`
22. `context7:/websites/developers_openai (Codex skills/security extraction)`
23. `https://github.com/brianlyang/identity-protocol/tree/main/identity`
24. `identity/protocol/IDENTITY_PROTOCOL.md`
25. `identity/protocol/IDENTITY_RUNTIME.md`
26. `identity/protocol/IDENTITY_DISCOVERY.md`
27. `identity/catalog/schema/identities.schema.json`
28. `identity/catalog/identities.yaml`
29. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
30. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
31. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
32. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-v1.6-governance-review-cross-verification-verdict-2026-03-05.md`
33. `https://developers.openai.com/api/reference/resources/responses/`
34. `https://ai.google.dev/gemini-api/docs/aistudio-build-mode`
35. `https://ai.google.dev/gemini-api/docs/aistudio-fullstack`
36. `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/system-prompts`
37. `https://modelcontextprotocol.io/specification/latest`
38. `https://agentskills.io/specification`
39. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
40. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
41. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
42. `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
43. `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`
44. `https://platform.openai.com/docs/guides/function-calling#strict-mode`
45. `context7:/openai/skills`
46. `context7:/websites/modelcontextprotocol_io_specification_2025-11-25`
