# Identity Actor-Scoped Session Binding Governance (v1.6.0)

Status: Historical baseline (v1.6 planning + release-governance execution directive; current-state redirected to active stream SSOT)
Governance layer: protocol
Scope: identity protocol base-repo only (no instance business policy)
Owner: identity protocol base-repo architect
Execution mode: topic-level canonical SSOT for v1.6 release governance and remediation closure
Tag policy: `v1.6` remains locked until all `P0` requirement ledger rows are `DONE` and audit sign-off is `PASS` (`P1` rows block only when explicitly promoted to `P0`)

## 0A) Current-state redirect (mandatory for all post-v1.6.0 operations)

1. This file is retained as **historical baseline + traceability ledger** and is not the sole current-state authority anymore.
2. Current-state contract resolution must follow active stream registry first:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. Current-state control-plane metrics/status must be read from current-pointer mappings:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/control-plane-budget.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/github-control-plane-offload.current.yaml`
4. Stream-specific normative clauses must follow active stream docs:
   - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
   - `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md`
   - `docs/governance/github-native-control-plane-specialization-v1.6.3.md`
5. Any numeric thresholds/status snapshots in this document (for example historical budget baselines such as `142/375`) are historical records only and cannot override current-pointer SSOT.
6. Any `/tmp/*` evidence reference in this file is historical replay context only and must not be treated as current wiring contract input.
7. New replay evidence for active streams must use persistent receipts under `activity/evidence/<stream>/<date>/...` with matching manifest tuples.

## 0B) v1.6 comprehensive closure baseline (mandatory, no side-route expansion)

1. `v1.6` is the single closure baseline for all `v1.6.x` protocol streams, including:
   - `v1.6.1` headstamp/HUD egress governance
   - `v1.6.2` multimodal plugin enforcement governance
   - `v1.6.3` GitHub-native control-plane specialization
   - `v1.6.4` fail-close monotonic governance
   - `v1.6.5` GitHub Rulesets + super-linter dual-layer governance
   - `v1.6.6` host unique channel governance
   - `v1.6.7` cross-layer runtime uniqueness governance
   - `v1.6.8` downsink path immutability governance
2. Any `v1.6.x` stream enhancement is treated as **v1.6 closure work**, not as a separate release line.
3. It is forbidden to postpone unresolved `v1.6` required-gate debt into future minor/major streams.
4. The release conclusion for `v1.6` must be determined by current-pointer machine gates only:
   - `contract-binding.current.yaml`
   - `required_gate_bundle_runner.py`
   - required CI workflow checks
   - control-plane status sync (`control-plane-status.current.yaml`)
5. Hard rule: no “v1.6 complete” claim is allowed while any required gate remains `FAIL_REQUIRED`.
6. Hard rule: no new stream can be considered closure-ready unless its requirement rows are integrated into `contract-binding.current.yaml` motherline and enforced by required CI.
7. Control-plane budget is part of the same v1.6 motherline closure gate:
   - `identity/protocol/mappings/control-plane-budget.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
8. Budget governance policy is **no-rebound with explicit baseline re-anchor only**:
   - never bypass `IP-CP-BUDGET-001` by narrative;
   - when motherline scope expands (for example, new required rows integrated in the same v1.6 line),
     thresholds/ceilings must be re-anchored explicitly in budget mapping and then re-synced into status mapping.

## 0) Governance Execution Mode and Release Lock (Mandatory)

### 0.1 Single execution entrypoint (topic SSOT)

1. This document is the historical execution baseline for `v1.6.0` actor-session-binding governance, not the active normative execution entrypoint.
2. `artifacts/**` and ad-hoc notes are evidence-only; they cannot override this document.
3. New normative updates must be written to active stream docs resolved from `identity/protocol/mappings/stream-doc-registry.current.yaml`, not appended here as current-state policy.

### 0.2 SSOT layering relationship (anti-drift)

1. This file is topic-canonical historical baseline for `v1.6.0` planning/execution snapshots.
2. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` remains global protocol execution SSOT.
3. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` remains the authoritative v1.5 closure record and historical baseline.
4. v1.6 governance updates must not rewrite historical v1.5 evidence; only carry-over boundaries may be referenced.
5. For current-state decisions, stream docs registered by `identity/protocol/mappings/stream-doc-registry.current.yaml` take precedence over this historical baseline.

### 0.2A Headstamp/HUD extraction freeze (v1.6.1 handoff)

1. As-of `2026-03-08`, headstamp/HUD governance is extracted to:
   - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
2. This v1.6.0 file keeps headstamp content as historical traceability baseline only.
3. New normative headstamp/HUD clauses, status promotion, and acceptance decisions must be written in v1.6.1 stream.
4. If v1.6.0 and v1.6.1 differ on headstamp/HUD semantics, v1.6.1 is authoritative.

### 0.3 Release lock table (`v1.6` tag hard-locked)

| Decision Gate | Unlock condition | Current state |
| --- | --- | --- |
| D1 Contract freeze | v1.6 contracts/fields/error semantics finalized in this doc | OPEN |
| D2 Implementation complete | Mandatory validators/tooling under `scripts/*` landed for v1.6 P0 items | OPEN |
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
   - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260304T041651Z_office_ops_protocol_upgrade_suggestions.md`
2. canonical proposal:
   - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_20260304T041651Z_office_ops_self_drive.md`

Mandatory triage split:

1. run-id anchored strict report selection is treated as v1.5 carry-over candidate and can be absorbed by v1.6 only if not landed in v1.5 closure window.
2. baseline phase-A anchor bootstrap, temp-file collision hardening, handoff/collab age-only bootstrap, and atomic feedback emit helper are v1.6 backlog items by default.

Hard rules:

1. v1.6 intake must not retroactively relabel current v1.5 unlock blockers.
2. every adopted suggestion must keep canonical protocol-feedback channel and SSOT linkage semantics unchanged.

### 4.7 `identity_prompt_bootstrap_capability_contract_v1` (P0)

Input package boundary:

1. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
2. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
3. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
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

1. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
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
4. protocol layer must not introduce the same-name runtime artifact file "identity/protocol/IDENTITY_PROMPT.md" (forbidden placeholder path; must remain absent).
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

Extraction note (`2026-03-08`):

1. This section is frozen as v1.6.0 historical baseline.
2. Active governance execution moved to `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`.

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

### 4.22 `execution_target_tuple_isolation_contract_v1` (P0)

Goal:

1. Remove hidden coupling that treats `codex_home` as the only practical runtime isolation key.
2. Support multi-agent × multi-identity dispatch in both persistent-session mode and one-shot process-call mode without bypass windows.

Mandatory semantics:

1. Every identity-route dispatch must resolve one canonical execution target tuple:
   - `execution_target_kind` (`tmux_session | codex_home | process_call | worker_queue`)
   - `execution_target_key` (stable isolation key in target-kind namespace)
   - `execution_target_ref` (audit/reference payload; may include route file + receipt pointer)
2. Conflict detection must be keyed by `(execution_target_kind, execution_target_key)` for all enabled routes under same runtime bridge scope.
3. Explicit request overrides (`session_id` / `codex_home` / direct target fields) must pass the same conflict gate and must not bypass conflict fail-close.
4. Shared-target mode requires gated handshake invariants:
   - `allow_shared_session=true` and consistent `switch_ack_ref` for all colliding identities;
   - missing/inconsistent handshake proof is fail-closed.
5. `process_call` targets are first-class:
   - dispatch may omit `codex_home` when `execution_target_kind=process_call`;
   - request/receipt must include deterministic tuple (`actor_id`, `identity_id`, `run_id`, `invocation_lane_id`, `execution_target_key`).
6. Fail-close error family (reserved for this contract):
   - `IP-XTARGET-001` (`execution_target_tuple_missing_or_ambiguous`)
   - `IP-XTARGET-002` (`execution_target_conflict_requires_switch_ack`)
   - `IP-XTARGET-003` (`execution_target_override_bypass_forbidden`)
   - `IP-XTARGET-004` (`process_call_receipt_incomplete`)

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
| ASB16-RQ-033 | runtime execution target isolation must be tuple-based (`kind+key`) and process-call compatible; `codex_home` cannot be mandatory for all dispatch paths | identity route resolver + inbound dispatch gate + conflict checker + switch-ack guard + process-call receipt emitter | P0 | SPEC_READY | multi-agent runtime escalation follow-up (`review v1.6 HOTFIX16-P0-006`) |

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
| C31 | multi-agent dispatch conflict isolation must be execution-target tuple based (not `codex_home`-only) and must remain fail-closed under explicit override | replay set must show: `(a)` conflicting tuple without handshake -> fail-close (`IP-XTARGET-002`), `(b)` override-bypass attempt blocked (`IP-XTARGET-003`), `(c)` process-call tuple without `codex_home` passes with complete receipt |

## 7) v1.6 Requirement Ledger (canonical tracker for unlock)

| Requirement ID | Requirement summary | Priority | Current status | Notes |
| --- | --- | --- | --- | --- |
| ASB16-RQ-001 | unlock formula automation | P0 | SPEC_READY | implementation landed (`scripts/validate_unlock_formula.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-002 | capability boundary classification | P0 | SPEC_READY | implementation landed (`scripts/validate_capability_boundary_classification.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-003 | status promotion evidence pipeline | P0 | SPEC_READY | implementation landed (`scripts/validate_promotion_pipeline.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-004 | outlet regression matrix | P0 | SPEC_READY | implementation landed (`scripts/validate_outlet_matrix.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-005 | sidecar invariance regression lock | P0 | SPEC_READY | implementation landed (`scripts/validate_sidecar_cwd_parity.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-006 | release-plane cloud evidence contract | P0 | SPEC_READY | implementation landed (`scripts/validate_release_plane_cloud_evidence.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-007 | cross-cwd runbook contract | P1 | SPEC_READY | implementation landed (`scripts/validate_cross_cwd_absolute_input.py`) + lane hooks wired; deterministic root/tmp parity replay archive pending |
| ASB16-RQ-008 | docs bridge consistency automation | P1 | SPEC_READY | implementation landed (`scripts/validate_docs_bridge_consistency.py`) + lane hooks wired; contradiction replay archive pending |
| ASB16-RQ-009 | run-id anchored strict report selection | P0 | SPEC_READY | implementation landed (`scripts/validate_run_id_report_selection.py`) + lane hooks wired; deterministic collision replay archive pending |
| ASB16-RQ-010 | baseline phase-A bootstrap automation | P1 | SPEC_READY | implementation landed (`scripts/validate_phase_bootstrap_before_strict.py`) + lane hooks wired; phase-A/phase-B strict replay archive pending |
| ASB16-RQ-011 | regression temp collision-safe strategy | P1 | SPEC_READY | implementation landed (`scripts/validate_tmp_collision_safety.py`) + lane hooks wired; deterministic parallel replay archive pending |
| ASB16-RQ-012 | handoff/collab freshness auto-bootstrap | P1 | SPEC_READY | implementation landed (`scripts/rotate_handoff_collab_freshness.py` + `scripts/validate_handoff_collab_freshness_rotation.py`) + lane hooks wired; deterministic rotation replay archive pending |
| ASB16-RQ-013 | protocol-feedback atomic emit helper | P1 | SPEC_READY | implementation landed (`scripts/emit_protocol_feedback_atomic.py` + `scripts/validate_protocol_feedback_atomic_emit.py`) + lane hooks wired; transaction replay archive pending |
| ASB16-RQ-014 | prompt bootstrap capability contract | P0 | SPEC_READY | implementation landed (`scripts/validate_prompt_bootstrap_capability.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-015 | prompt capability matrix fail-closed validator | P0 | SPEC_READY | implementation landed (`scripts/validate_prompt_capability_matrix.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-016 | refresh->strict + business interference runbook contract | P1 | SPEC_READY | implementation landed (`scripts/emit_business_interference_matrix.py` + `scripts/validate_refresh_strict_business_interference.py`) + lane hooks wired; paired refresh/strict replay archive pending |
| ASB16-RQ-017 | roundtable/vendor/openaidoc/context7 cross-verification contract | P1 | SPEC_READY | implementation landed + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-018 | dedup winner determinism contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-019 | cross-workflow evidence schema contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-020 | skill-path integrity contract | P1 | SPEC_READY | implementation landed + lane hooks wired; deterministic required=true replay archive pending (non-promotional) |
| ASB16-RQ-021 | route/version pinning contract | P1 | SPEC_READY | implementation landed + lane hooks wired; emitter-before-gate sequence active, deterministic required=true replay archive pending |
| ASB16-RQ-022 | fallback taxonomy normalization contract | P1 | SPEC_READY | implementation landed + lane hooks wired; required=true replay archive pending and blocker-namespace isolation remains mandatory |
| ASB16-RQ-023 | discovery trigger-conditioned requiredization contract | P0 | SPEC_READY | implementation landed (`scripts/validate_discovery_requiredization.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`); deterministic required=true replay archive pending |
| ASB16-RQ-024 | discovery apply-time coverage fail-close contract | P0 | SPEC_READY | implementation landed (`scripts/validate_discovery_requiredization.py`) + lane hooks wired; discovery coverage replay archive pending |
| ASB16-RQ-025 | kernel-first canonical source contract | P0 | SPEC_READY | implementation landed (`scripts/validate_kernel_ssot_source.py`) + lane hooks wired; deterministic required=true replay archive pending |
| ASB16-RQ-026 | kernel contract mapping projection contract | P0 | SPEC_READY | implementation landed (`scripts/validate_contract_mapping_coverage.py`) + lane hooks wired; full P0 coverage closure pending |
| ASB16-RQ-027 | derived prompt compilation contract | P0 | SPEC_READY | implementation landed (`scripts/compile_identity_runtime.py` + `scripts/validate_prompt_derivation_conformance.py`) + lane hooks wired; derivation replay archive pending |
| ASB16-RQ-028 | instance write-boundary lock contract | P0 | SPEC_READY | boundary + lane telemetry hooks landed; non-starvation replay matrix closure remains pending in `8.12` |
| ASB16-RQ-029 | semantic single-source convergence contract | P0 | SPEC_READY | implementation landed (`scripts/validate_semantic_convergence.py`) + lane hooks wired; same-lineage replay archive closure pending |
| ASB16-RQ-030 | intake evidence quorum hard-gate contract | P1 | SPEC_READY | implementation landed (`single-parser dual-mode`) + lane hooks wired; promotion remains blocked until deterministic required=true replay archive is complete |
| ASB16-RQ-031 | protocol-kernel prompt import executable coupling contract | P0 | SPEC_READY | explicit lane/candidate non-starvation hooks landed with write-boundary addendum; mapping validator + actor-explicit strict lane + multimodal sample-proof closure still required before promotion |
| ASB16-RQ-032 | outbound headstamp pre-send hard-gate contract | P0 | SPEC_READY | implementation landed (`scripts/validate_send_time_reply_gate.py` + `scripts/validate_headstamp_recurrence_closure.py`) + lane hooks wired; deterministic negative replay archive pending |
| ASB16-RQ-033 | execution-target tuple isolation contract | P0 | SPEC_READY | implementation landed (`scripts/validate_execution_target_tuple_isolation.py`) + lane hooks wired (`creator/readiness/three-plane/full-scan/e2e/ci`) with kernel+mapping anchor closure; deterministic replay archive + runtime bridge rollout evidence pending |

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

Historical-snapshot clarification:

1. this inventory is the pre-`RQ-033` deep-scan baseline captured on `2026-03-05`.
2. `ASB16-RQ-033` and later hotfix rows are governed by subsequent sections (`8.19+`) and do not retroactively alter the 2026-03-05 snapshot counts.

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
5. Runtime replay anchors:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
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
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
3. `T2 vendor`:
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
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

Implementation update (2026-03-07):

1. full requirement projection anchors were added for remaining P0 rows:
   - `rq_023_discovery_dual_track_requiredization_activation_contract_v1`
   - `rq_024_discovery_apply_coverage_fail_closed_contract_v1`
   - `rq_028_instance_write_boundary_lock_contract_v1`
   - `rq_032_headstamp_pre_send_hard_gate_contract_v1`
2. mapping asset `identity/protocol/mappings/contract-binding.v1.6.yaml` now projects all `ASB16-RQ-001..033` rows (`row_count=33`), with scanner-verifiable `coverage_rate=100.0` and `p0_coverage_rate=100.0` under forced coverage replay.
3. post-hotfix extension includes `rq_033_execution_target_tuple_isolation_contract_v1` kernel anchor + mapping row + lane hooks, while promotion boundary remains unchanged (`SPEC_READY/PENDING_INTAKE`) until deterministic required=true replay archive closes.

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
   - `validator_ref`: `scripts/validate_send_time_reply_gate.py` + `scripts/validate_reply_identity_context_first_line.py` + `scripts/validate_headstamp_recurrence_closure.py`
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
| ASB16-RQ-018 | `PARTIAL` | `rq_018_dedup_monotonic_winner_contract_v1` validator is implemented, but deterministic replay evidence for required=true concurrency windows remains incomplete | keep canonical validator path `scripts/validate_dedup_monotonicity.py`; optional compatibility wrapper `scripts/validate_v16_dedup_monotonicity.py` must delegate only (no independent parsing); keep hooks active in creator/readiness/three-plane/full-scan/e2e/ci and aggregate only canonical `winner_id`/`winner_reason` fields | keep `ACCEPT_WITH_FIX` with audit `PASS_WITH_BLOCKERS` until same-input parallel replay proves deterministic winner tuple across lanes |
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
   - `validator_ref`: `scripts/validate_dedup_monotonicity.py` (optional compatibility wrapper: `scripts/validate_v16_dedup_monotonicity.py`)
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
python3 scripts/validate_dedup_monotonicity.py --catalog <LOCAL_CATALOG> --identity-id <ID> --run-id <RUN_ID> --parallel-claims 5 --json-only
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
3. Current decision class for both rows is `ACCEPT_WITH_FIX` (implementation landed + replay closure pending, non-promotional).

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

1. protocol layer must not add the same-name runtime artifact file "identity/protocol/IDENTITY_PROMPT.md" (forbidden placeholder path; must remain absent).
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
5. outbound user-visible reply must have one canonical pre-send decision source:
   - final dispatch is allowed only after canonical gateway verdict is emitted;
   - distributed preflight checks may exist, but they cannot replace or bypass the canonical gateway verdict.

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

Round-6 recurrence replay (`HEAD=6a2ef0b`, 2026-03-07, protocol-layer only):

1. executable replay commands:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids <IDENTITY_A>,<IDENTITY_B> --project-catalog <PROJECT_CATALOG> --global-catalog /tmp/nonexistent-catalog.yaml --actor-id assistant:codex --out /tmp/hotfix_headstamp_r6_fullscan.json`
   - `python3 scripts/validate_headstamp_recurrence_closure.py --identity-id <IDENTITY_A> --catalog <PROJECT_CATALOG> --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
   - `python3 scripts/validate_headstamp_recurrence_closure.py --identity-id <IDENTITY_B> --catalog <PROJECT_CATALOG> --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
2. observed recurrence signal:
   - one strict-path identity fails with `headstamp_recurrence_closure_status=FAIL_REQUIRED`, `error_code=IP-ASB-STAMP-SCAN-004`;
   - dynamic positive case fails with compatibility trace `IP-ASB-STAMP-SESSION-005`;
   - another identity under the same replay suite returns `PASS_REQUIRED`.
3. cross-check confirms resolver divergence:
   - `validate_actor_session_binding.py` can pass under `binding_key_mode=actor_id+session_id`;
   - `validate_headstamp_recurrence_closure.py` mismatch probe currently calls `load_actor_binding(catalog_path, actor_id)` without explicit `identity_id/session_id`, selecting latest actor-binding entry rather than target-lineage binding.
4. protocol interpretation:
   - this is not a permitted hard switch;
   - this is protocol-layer actor-binding source divergence that surfaces as perceived headstamp continuity loss on strict send-time replay.

Positive reinforcement confirmed by this replay:

1. no-hard-switch baseline remains enforced (`IP-ACT-SWITCH-001` class still fail-closes unauthorized switching).
2. strict context mismatch remains fail-close on strict surfaces (`IP-ENV-003` class).
3. replay-archive contract remains stable on strict protocol replay set (`PASS_REQUIRED` closure retained).

Round-8 four-track convergence residual (`HEAD=f53f36a`, 2026-03-07):

1. `T1` contract intent and `T2` script wiring both state single-source headstamp enforcement.
2. `T3` replay still reveals applicability drift on direct gateway invocation:
   - `python3 scripts/validate_send_time_reply_gate.py --identity-id <ID> --catalog <PROJECT_CATALOG> --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
   - observed: `send_time_gate_status=SKIPPED_NOT_REQUIRED`, `required_contract=false`, `stale_reasons=[\"contract_not_required\"]`.
3. `T4` multi-source protocol-feedback batches independently report recurrence perception under mixed strict/non-strict surfaces.
4. interpretation:
   - resolver divergence closure is valid;
   - single-entry canonical egress enforcement is not yet universally requiredized, so recurrence perception can still appear.

Architect closure requirements (protocol layer, mandatory):

1. unify actor-binding resolution source for send-time gate and recurrence closure:
   - single resolver contract must require deterministic selection key (`actor_id + identity_id + session_id` when available);
   - strict surfaces must reject ambiguous actor binding selection.
2. extend mandatory telemetry/receipt tuple for headstamp closure:
   - `actor_binding_resolution_mode`
   - `actor_binding_session_id`
   - `actor_binding_compare_token`
   - `actor_binding_selected_identity_id`
3. fail-close policy for ambiguous binding:
   - if multiple actor bindings are present and no deterministic target key is supplied, return explicit actor-context fail-close before send-time headstamp verdict emission.
4. canonical code convergence remains mandatory:
   - `IP-ASB-STAMP-SESSION-*` stays compatibility trace only;
   - promotion-grade receipts must converge to canonical `IP-HDSTAMP-*` + actor-context family.
5. enforce single-entry canonical egress gateway:
   - canonical gateway source is `scripts/validate_send_time_reply_gate.py`;
   - user-visible outbound operations must set `required_contract=true` for this gateway;
   - `SKIPPED_NOT_REQUIRED(contract_not_required)` is invalid on promotion-grade replay for outbound headstamp checks;
   - any send path bypassing canonical gateway must fail-close with `IP-HDSTAMP-004` (`canonical_gateway_bypass`).
6. scope separation lock:
   - unified control-plane entrypoint management/wiring governance is tracked independently under `8.27` (`HOTFIX16-P0-007`);
   - this section (`8.15`) remains lane/headstamp-specific and must not absorb unrelated control-plane closure claims.

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
   - protocol-lane activation receipts are reproducible from production endpoint traces,
   - actor-binding resolver is single-sourced across headstamp recurrence closure and strict send-time gate (no latest-binding ambiguity).

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
3. `T3 live evidence`: strict-chain core scripts are migrated to dynamic temp roots, but replay/audit still shows residual fixed `/tmp` paths in CI workflow surfaces and legacy blocker-receipt defaults; this hotfix remains open until those residuals are removed or runner-scoped.
4. `T4 protocol feedback`: canonical feedback batch + receipt + evidence-index entries for this governance gap.

Implementation delta (2026-03-07):

1. landing commit evidence: `093496b`.
2. added shared temp resolver: `scripts/runtime_temp_path_common.py`.
3. removed strict-chain fixed `/tmp` literals from core runtime scripts:
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/validate_no_implicit_switch.py`
4. residual fixed `/tmp` debt still exists outside the core runtime set (not closed):
   - `/.github/workflows/_identity-required-gates.yml` still contains fixed `/tmp/identity-*.json` receipts in required-gates commands.
   - legacy default receipt outputs in stamp/coherence validators still resolve to `/tmp/...` when no explicit path is provided.
5. strict-chain helper outputs are now operation/identity scoped, with optional run token scoping for mutation/e2e flows.

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

### 8.18 Full-Fix Replay Audit Checkpoint (`FIX16-001..037 + HOTFIX16-*`, 2026-03-07)

Scope lock:

1. this checkpoint re-audits all active v1.6 fix streams (`FIX16-001..037`, `HOTFIX16-P0-001..HOTFIX16-P1-004`) using executable evidence only.
2. this checkpoint is protocol-layer only and does not prescribe instance business remediation.
3. row-level status synchronization between review rolling summary and review decision log is required and was rechecked in this round.
4. this checkpoint opens dedicated emergency track `HOTFIX16-P0-005` for gate-chain parser/runtime drift.

Replay evidence commands executed:

1. `python3 scripts/validate_required_contract_coverage.py --catalog ../.identity/catalog.local.yaml --identity-id base-repo-architect --operation validate --json-only`
2. `python3 scripts/validate_required_contract_coverage.py --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --identity-id office-ops-expert --operation validate --json-only`
3. `python3 scripts/report_three_plane_status.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex --out <tmp>`
4. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids office-ops-expert --global-catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --actor-id assistant:codex --out <tmp>`
5. `python3 scripts/release_readiness_check.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
6. `python3 scripts/identity_creator.py validate --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
7. `IDENTITY_CATALOG=/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml python3 scripts/validate_identity_runtime_mode_guard.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --expect-mode auto --scope USER`

Critical findings (protocol-layer only):

1. `P0-GATECHAIN-001` (tracked under `HOTFIX16-P0-005`):
   - `scripts/release_readiness_check.py` crashes before gate execution because runtime references parser fields that are not declared (`args.target_branch`, `args.release_head_sha`, `args.required_gates_run_id`, `args.run_url`, `args.workflow_file_sha`, `args.run_head_sha`, `args.run_workflow_file_sha`, `args.checks_json`).
   - Evidence: `scripts/release_readiness_check.py:976`, `scripts/release_readiness_check.py:1966`.
2. `P0-GATECHAIN-002` (tracked under `HOTFIX16-P0-005`):
   - `identity_creator validate` crashes because command construction reads `args.run_id` while validate subparser does not declare `--run-id`.
   - Evidence: `scripts/identity_creator.py:1827`, `scripts/identity_creator.py:1132`.
3. `P1-APPLICABILITY-003` (remains under `HOTFIX16-P1-004`):
   - `cross_workflow_schema` still blocks observation runs (`IP-XWF-002`) when `route_action`/`dedup_state` are absent in non-routed, non-dedup current runs.
   - Evidence: `required_contract_coverage` + `full_identity_protocol_scan` replay for `office-ops-expert`.
4. `P1-CONTEXT-004` (remains under `HOTFIX16-P1-004`):
   - env/CLI catalog mismatch is still `WARN` (`rc=0`) in strict surfaces, which is weaker than `C30` fail-close intent.
   - Evidence: `validate_identity_runtime_mode_guard` mismatch replay above.

Required protocol-layer remediation (no instance-layer scope):

1. `release_readiness_check` must align argparse schema and runtime field usage, then add a mandatory replay proving no pre-gate crash.
2. `identity_creator validate` must either add `--run-id` to validate subparser or internally derive stable run-id defaults before command assembly.
3. `validate_cross_workflow_schema.py` must enforce profile-scoped required sets (`core`, `routed`, `dedup`) with deterministic `SKIPPED_NOT_REQUIRED` for non-applicable profiles.
4. strict context surfaces must enforce catalog mismatch fail-close unless explicit override receipt is present.

State impact:

1. this checkpoint does not promote any row.
2. `FIX16-035` / `FIX16-036` remain `PASS_WITH_BLOCKERS` (non-promotional).
3. all other rows remain `SPEC_READY / PENDING_INTAKE` until replay closure and blocker fixes are complete.

### 8.19 Emergency Hotfix Track - Execution Target Tuple Isolation (`HOTFIX16-P0-006`, 2026-03-07)

Scope lock:

1. this is a dedicated P0 hotfix stream and does not inherit closure from `HOTFIX16-P0-001/002/005`.
2. scope is runtime dispatch contractization only: route resolution, conflict isolation, and machine receipts for process-call targets.
3. this section defines protocol-layer requirement semantics; instance-specific business rollout remains out of scope.

Why this hotfix is required:

1. current multi-agent workloads include both persistent-session dispatch and one-shot process dispatch; treating `codex_home` as mandatory creates false coupling and bypass pressure.
2. tuple-based conflict isolation (`kind+key`) is required to prevent "shared route appears valid but actually collides" incidents.
3. explicit override requests must remain under the same fail-close conflict semantics as normal route path.

Contractized mandatory fields:

1. `execution_target_kind`
2. `execution_target_key`
3. `execution_target_ref`
4. `route_source`
5. `allow_shared_session`
6. `switch_ack_ref`
7. `route_conflict_status`
8. `route_conflict_error_code`

Replay closure requirements (promotion blocker until complete):

1. conflicting tuple replay (`kind+key` collision, no handshake) -> deterministic fail-close `IP-XTARGET-002`.
2. explicit override bypass replay -> deterministic fail-close `IP-XTARGET-003`.
3. process-call replay (`execution_target_kind=process_call`, no `codex_home`) -> deterministic pass with full receipt fields.
4. same-lineage convergence replay across update/readiness/three-plane/full-scan consuming identical tuple fields and conflict verdict.

Architecture reinforcement verdict (this round):

1. verdict: `POSITIVE_REINFORCEMENT_CONFIRMED`.
2. rationale:
   - this requirement generalizes runtime isolation from storage-path coupling (`codex_home`) to canonical execution-target semantics (`kind+key`);
   - this closes a known architecture blind spot where one-shot process dispatch cannot be represented without forcing pseudo-session artifacts;
   - this keeps compatibility with existing `session_id/codex_home` routes while defining a non-bypass fail-close superset.

Deep-scan code confirmation snapshot (2026-03-07, base-repo-architect lane):

1. command:
   - `rg -n "identity_or_session_or_codex_home_required|session_or_codex_home_required|requested_session_id|requested_codex_home|_compute_route_issues|session_id_conflict_requires_switch_ack|codex_home_conflict_requires_switch_ack" /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/main.py /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/identity_router.py /Users/yangxi/claude/codex_project/fqsh/src/feiqiao_guard/models.py`
2. findings (code anchors):
   - inbound dispatch still hard-requires `session_id` or `codex_home`: `main.py:118..119`, `main.py:148..149`;
   - conflict computation is currently keyed by `session_id` and `codex_home` only: `identity_router.py:144..156`, `identity_router.py:158..196`;
   - route schema does not expose execution-target tuple fields yet (`execution_target_kind`, `execution_target_key` absent): `models.py:133..143`.
3. regression safety baseline:
   - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/pycache-fqsh pytest -p no:cacheprovider tests/test_chat_inbound.py tests/test_chat_bridge.py -q`
   - observed result: `28 passed, 1 warning` (no regression in current guarded-route behavior before tuple uplift).

State impact:

1. `ASB16-RQ-033` enters v1.6 as `P0 / SPEC_READY`, and protocol-layer machine-lock closure is landed (`kernel anchor + mapping row + validator + lane wiring`).
2. lifecycle remains non-promotional (`SPEC_READY / PENDING_INTAKE`) until replay closure + independent audit sign-off + runtime bridge rollout evidence are complete.

### 8.20 Round-2 Multi-Identity Replay Sweep (`FIX16-001..037 + HOTFIX16-*`, 2026-03-07)

Scope lock:

1. this sweep replays protocol-layer gates only; instance business remediation remains out of scope.
2. replay targets are global-catalog active identities: `office-ops-expert`, `base-repo-architect`, `custom-creative-ecom-analyst`, `system-requirements-analyst`.
3. all findings in this section are executable-replay derived; no speculative promotion statements are allowed.

Replay commands executed:

1. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids office-ops-expert --actor-id assistant:codex --out /tmp/v16_full_scan_office-ops-expert_20260307_round2.json`
2. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids base-repo-architect --actor-id assistant:codex --out /tmp/v16_full_scan_base-repo-architect_20260307_round2.json`
3. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids custom-creative-ecom-analyst --actor-id assistant:codex --out /tmp/v16_full_scan_custom-creative-ecom-analyst_20260307_round2.json`
4. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --actor-id assistant:codex --out /tmp/v16_full_scan_system-requirements-analyst_20260307_round2.json`
5. `python3 scripts/release_readiness_check.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
6. `python3 scripts/release_readiness_check.py --identity-id base-repo-architect --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
7. `python3 scripts/identity_creator.py validate --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
8. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex`
9. `python3 scripts/validate_v16_cross_workflow_schema.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --operation scan --json-only`
10. `IDENTITY_CATALOG=/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml python3 scripts/validate_identity_runtime_mode_guard.py --identity-id office-ops-expert --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --expect-mode auto`

Protocol-layer findings (round-2):

1. `P0-GATECHAIN-001` remains open (`HOTFIX16-P0-005`):
   - `release_readiness_check.py` still crashes on missing argparse field `args.target_branch` before downstream required gates execute.
2. `P0-GATECHAIN-002` remains open (`HOTFIX16-P0-005`):
   - `identity_creator.py validate` still crashes on missing argparse field `args.run_id` before downstream required gates execute.
3. `P1-APPLICABILITY-003` remains open (`HOTFIX16-P1-004`):
   - `office-ops-expert` observation replay still returns `cross_workflow_schema_status=FAIL_REQUIRED`, `error_code=IP-XWF-002`.
4. `P1-CONTEXT-004` remains open (`HOTFIX16-P1-004`):
   - env/CLI catalog mismatch still resolves to warning-only (`rc=0`, `[WARN]`) instead of fail-close.
5. actor-switch hard-gate behavior is confirmed and not regressed:
   - activation attempts for non-bound identities fail with `IP-ACT-SWITCH-001` when explicit switch-intent receipt is absent.
   - non-bound identity scans surface `IP-ASB-STAMP-SESSION-005` due actor-binding mismatch, consistent with no-hard-switch baseline.

Per-identity protocol blocker matrix:

1. `office-ops-expert`: `IP-XWF-002` (`cross_workflow_schema` observation applicability residual).
2. `base-repo-architect`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004` (actor-binding mismatch under shared actor replay).
3. `custom-creative-ecom-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004` (actor-binding mismatch under shared actor replay).
4. `system-requirements-analyst`: `IP-ASB-STAMP-SESSION-005`, `IP-ASB-STAMP-SCAN-004`, `IP-SEM-004`.

State impact:

1. no row is promoted in this sweep.
2. `HOTFIX16-P0-005` remains `SPEC_READY / PENDING_INTAKE` until crash-free replay is proven.
3. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` until applicability + context fail-fast closure is proven.
4. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` remains enforced.

### 8.21 Round-3 Head Re-Audit Checkpoint (`HEAD=a0c191e`, 2026-03-07)

Scope lock:

1. this checkpoint audits the current head only (`a0c191e`) with executable replay evidence.
2. this checkpoint remains protocol-layer only and does not prescribe instance business remediation.
3. this checkpoint re-validates previously open blockers (`HOTFIX16-P0-005`, `HOTFIX16-P1-004`) and newly landed machine-lock wiring (`HOTFIX16-P0-006`).

Replay commands executed (non-hardcoded runtime paths):

1. `source ./scripts/use_local_identity_env.sh`
2. `GLOBAL_CATALOG="${HOME}/.codex/.identity/catalog.local.yaml"`
3. `python3 scripts/release_readiness_check.py --identity-id base-repo-architect --catalog "${IDENTITY_CATALOG}" --scope USER --actor-id assistant:codex`
4. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog "${IDENTITY_CATALOG}" --scope USER --actor-id assistant:codex`
5. `IDENTITY_CATALOG="${GLOBAL_CATALOG}" python3 scripts/release_readiness_check.py --identity-id office-ops-expert --catalog "${GLOBAL_CATALOG}" --scope USER --actor-id assistant:codex`
6. `IDENTITY_CATALOG="${GLOBAL_CATALOG}" python3 scripts/identity_creator.py update --identity-id office-ops-expert --catalog "${GLOBAL_CATALOG}" --scope USER --mode review-required`
7. `python3 scripts/validate_cross_workflow_schema.py --identity-id office-ops-expert --catalog "${GLOBAL_CATALOG}" --operation scan --json-only`
8. `IDENTITY_CATALOG="${IDENTITY_CATALOG}" python3 scripts/validate_identity_runtime_mode_guard.py --identity-id office-ops-expert --catalog "${GLOBAL_CATALOG}" --repo-catalog identity/catalog/identities.yaml --expect-mode auto --operation validate`
9. `python3 scripts/validate_replay_archive_contract.py --identity-id office-ops-expert --catalog "${GLOBAL_CATALOG}" --operation scan --json-only`
10. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids office-ops-expert --project-catalog "${GLOBAL_CATALOG}" --actor-id assistant:codex --out /tmp/full_scan_office_fix_round3b.json`

Findings:

1. parser drift closure is verified:
   - `release_readiness_check.py` now declares release-plane pass-through args (`--target-branch`, `--release-head-sha`, `--required-gates-run-id`, `--run-url`, `--workflow-file-sha`, `--run-head-sha`, `--run-workflow-file-sha`, `--checks-json`).
   - `identity_creator.py validate` now declares `--run-id`.
2. strict context fail-fast is enforced on strict surfaces:
   - env/catalog mismatch now fails with `IP-ENV-003` for `validate/readiness/ci` operations.
   - `scan` operation remains observational (`rc=0` + warning).
3. `P1-APPLICABILITY-003` is closed on observation profile:
   - `validate_v16_cross_workflow_schema.py --operation scan` now returns `SKIPPED_NOT_REQUIRED` with `cross_workflow_not_applicable_no_route_or_dedup_signal`.
4. gate-chain now fails for contract reasons rather than parser/runtime crashes:
   - with catalog aligned, `identity_creator update` and delegated `release_readiness_check` preflight both progress into downstream contract gates and fail with deterministic business gate codes (for example `IP-EXEC-ORDER-001`, `IP-PVA-003`, `IP-INTAKE-EVID-001` depending on identity evidence state), not `AttributeError`/`NameError`.
5. replay-archive expectation drift is closed:
   - `validate_replay_archive_contract.py` now returns `PASS_REQUIRED` after updating `rq019_negative_missing_field` fixture to remain negative under applicability-aware schema extraction (`missing_run_id` + explicit dedup signal).
6. `HOTFIX16-P0-006` implementation landing is confirmed but required-path replay is still pending:
   - validator and lane hooks are present, but sample replay on all four audited identities returns `execution_target_tuple_isolation_status=SKIPPED_NOT_REQUIRED` (`contract_not_required`), so required=true deterministic archive is not yet closed.

State impact:

1. no row is promoted in this checkpoint.
2. `HOTFIX16-P0-005` remains `SPEC_READY / PENDING_INTAKE` (parser/runtime crash closure is verified; crash-class blocker is closed but downstream required-gate replay closure is still pending).
3. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` (applicability closure + strict mismatch fail-close + replay-archive drift fix are landed; independent audit sign-off remains pending).
4. `HOTFIX16-P0-006` remains `SPEC_READY / PENDING_INTAKE` until required=true tuple replay archive is attached.
5. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` remains enforced.

### 8.22 Round-4 Freeze Re-Audit Checkpoint (`HEAD=6a2ef0b`, 2026-03-07)

Scope lock:

1. this checkpoint audits frozen head `6a2ef0b` only.
2. this checkpoint remains protocol-layer only and excludes instance business remediation.
3. this checkpoint revalidates `FIX16-035/036` and `HOTFIX16-P1-003/004/P0-005/P0-006` using executable replay.

Replay commands executed (project-local catalog lineage):

1. `python3 scripts/docs_command_contract_check.py`
2. `python3 scripts/validate_protocol_ssot_source.py`
3. `python3 scripts/release_readiness_check.py --identity-id <store-manager|base-repo-audit-expert-v3|custom-creative-ecom-analyst|base-repo-architect> --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope <SYSTEM|USER> --actor-id assistant:codex`
4. `python3 scripts/identity_creator.py validate --identity-id <store-manager|base-repo-audit-expert-v3|custom-creative-ecom-analyst|base-repo-architect> --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope <SYSTEM|USER> --actor-id assistant:codex`
5. `python3 scripts/validate_required_contract_coverage.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation update --json-only`
6. `python3 scripts/validate_v16_cross_verification_tracks.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
7. `python3 scripts/validate_v16_intake_evidence_quorum.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
8. `python3 scripts/validate_route_version_pinning.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
9. `python3 scripts/validate_fallback_taxonomy_normalization.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
10. `python3 scripts/validate_dedup_monotonicity.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
11. `python3 scripts/validate_v16_cross_workflow_schema.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation <scan|update|readiness|ci> --json-only`
12. `python3 scripts/validate_replay_archive_contract.py --identity-id <base-repo-architect|base-repo-audit-expert-v3|custom-creative-ecom-analyst> --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --operation scan --json-only`
13. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids store-manager,base-repo-audit-expert-v3,custom-creative-ecom-analyst,base-repo-architect --project-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --global-catalog /tmp/nonexistent-catalog.yaml --actor-id assistant:codex --out /tmp/audit_r5_full_scan_project.json`

Findings:

1. parser/runtime crash class remains closed for `HOTFIX16-P0-005` (no missing argparse-field crash in `release_readiness` / `identity_creator validate`).
2. new strict-scope propagation defect is reproducible (`P1-SCOPE-005`, linked to `HOTFIX16-P1-004`):
   - `identity_creator.py validate` calls `validate_identity_instance_isolation.py` without forwarding `--scope`, so `store-manager` (`SYSTEM`) falls back to validator default `USER` and fails with scope mismatch.
3. requiredization applicability is still not converged on strict surfaces (`P1-APPLICABILITY-006`, linked to `HOTFIX16-P1-004`):
   - for `base-repo-architect`, `update/readiness/ci` return `FAIL_REQUIRED` for six Batch-6/7 gates while `producer_readiness=false` and `requiredization_current_round_linked=false`.
   - failing contracts/codes: `cross_verification_tracks` (`IP-INTAKE-EVID-001`), `intake_evidence_quorum` (`IP-INTAKE-EVID-001`), `route_version_pinning` (`IP-PIN-001`), `fallback_taxonomy_normalization` (`IP-FBTAX-002`), `dedup_monotonicity` (`IP-DEDUP-001`), `cross_workflow_schema` (`IP-XWF-001`).
4. intake auto-required inference is still history-sensitive under strict ops:
   - `validate_v16_intake_evidence_core.py` promotes required mode from historical `runtime/protocol-feedback` presence (`auto_required_signal=true`) even when current-round linkage is false.
5. replay-archive contract closure remains stable:
   - `validate_replay_archive_contract.py` returns `PASS_REQUIRED` with `15/15` passing cases for all three audited runtime identities.
6. strict context fail-fast remains enforced:
   - env/catalog mismatch still fails with `IP-ENV-003` on strict operations (`readiness` replay).
7. fixed `/tmp` debt remains open (`P1-TMPPATH-007`, linked to `HOTFIX16-P1-003`):
   - CI required-gates workflow and legacy default blocker receipt paths still contain fixed `/tmp/...` outputs.

State impact:

1. no row is promoted in this checkpoint.
2. `FIX16-035` and `FIX16-036` remain `PASS_WITH_BLOCKERS` and non-promotional.
3. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` until strict-scope forwarding and current-round applicability convergence are replay-closed.
4. `HOTFIX16-P1-003` remains `SPEC_READY / PENDING_INTAKE` until CI/legacy `/tmp` residuals are removed or runner-scoped with deterministic replay.
5. `HOTFIX16-P0-005` remains `SPEC_READY / PENDING_INTAKE` (crash class closed, downstream convergence closure pending).
6. `HOTFIX16-P0-006` remains `SPEC_READY / PENDING_INTAKE` until required=true tuple replay archive is attached.
7. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` remains enforced.

### 8.23 Round-6 Three-Point Closure Checkpoint (`HEAD=6a2ef0b+`, 2026-03-07)

Scope lock:

1. this checkpoint closes only the three protocol-layer residuals from `8.22`:
   - `P1-SCOPE-005` (`identity_creator` scope propagation),
   - `P1-APPLICABILITY-006` (strict requiredization over-block),
   - `P1-TMPPATH-007` (workflow/legacy fixed temp paths).
2. instance business-side evidence production remains out of scope for this section.
3. lifecycle boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

Replay commands executed (local catalog lineage, non-hardcoded temp roots):

1. `python3 scripts/resolve_identity_context.py resolve --identity-id base-repo-architect`
2. `CAT="${IDENTITY_CATALOG:-$PWD/../.identity/catalog.local.yaml}"`
3. `python3 scripts/identity_creator.py validate --identity-id store-manager --catalog "$CAT" --scope SYSTEM --actor-id assistant:codex | rg "validate_identity_instance_isolation.py|instance isolation"`
4. `python3 scripts/validate_required_contract_coverage.py --catalog "$CAT" --identity-id base-repo-architect --operation update --json-only`
5. `for gate in validate_v16_cross_verification_tracks.py validate_v16_intake_evidence_quorum.py validate_route_version_pinning.py validate_fallback_taxonomy_normalization.py validate_dedup_monotonicity.py validate_v16_cross_workflow_schema.py; do python3 "scripts/${gate}" --catalog "$CAT" --identity-id base-repo-architect --operation update --json-only; done`
6. `python3 scripts/validate_fallback_taxonomy_normalization.py --catalog "$CAT" --identity-id base-repo-architect --operation update --fallback-reason no_intent_signal --json-only`
7. `python3 scripts/validate_fallback_taxonomy_normalization.py --catalog "$CAT" --identity-id base-repo-architect --operation update --fallback-reason unknown_vendor_glitch --json-only`
8. `python3 scripts/validate_dedup_monotonicity.py --catalog "$CAT" --identity-id base-repo-architect --operation update --claims "<positive_claims.json>" --json-only`
9. `python3 scripts/validate_dedup_monotonicity.py --catalog "$CAT" --identity-id base-repo-architect --operation update --claims "<negative_missing_tiebreaker.json>" --json-only`
10. `rg -n "/tmp" .github/workflows/_identity-required-gates.yml scripts/validate_identity_response_stamp.py scripts/validate_reply_identity_context_first_line.py scripts/validate_execution_reply_identity_coherence.py`
11. `python3 scripts/docs_command_contract_check.py`
12. `python3 scripts/validate_protocol_ssot_source.py`

Findings:

1. `P1-SCOPE-005` closed at protocol layer:
   - `identity_creator` validate/update chains now forward `--scope` into `validate_identity_instance_isolation.py`.
   - replay on `store-manager --scope SYSTEM` confirms no default-USER fallback drift.
2. `P1-APPLICABILITY-006` closed for strict non-linked lanes:
   - Batch-6/7 gates now emit `SKIPPED_NOT_REQUIRED` + `required_contract_not_applicable_no_current_round_evidence_source` when strict surface lacks current-round linkage.
   - coverage replay (`operation=update`, `base-repo-architect`) reports `failed_required_contract_count=0`, and new gate rows resolve to non-blocking non-applicable state.
3. `P1-TMPPATH-007` protocol residuals closed:
   - `/.github/workflows/_identity-required-gates.yml` migrated to runner/runtime-scoped temp roots (`RUNNER_TEMP/TMPDIR/GITHUB_WORKSPACE`) without fixed `/tmp` output bindings.
   - legacy default blocker-receipt paths in stamp/first-line/coherence validators now use `runtime_temp_file(...)` resolver.
   - static grep replay for targeted files returns no `/tmp` literals.
4. fail-close negative controls remain intact after applicability closure:
   - explicit fallback negative still returns `FAIL_REQUIRED + IP-FBTAX-001`.
   - explicit dedup missing required field still returns `FAIL_REQUIRED + IP-DEDUP-002`.

State impact:

1. the three protocol residuals from `8.22` are closed at implementation level.
2. `FIX16-035`, `FIX16-036`, `HOTFIX16-P1-003`, `HOTFIX16-P1-004` remain non-promotional pending independent roundtable replay sign-off and required=true current-round evidence archive.
3. status boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.24 Round-7 Headstamp Resolver Convergence Checkpoint (`HEAD=d5f75d7+`, 2026-03-07)

Scope lock:

1. this checkpoint addresses protocol-layer residual under `HOTFIX16-P0-002` only:
   - actor-binding resolver divergence between headstamp recurrence probe and actor-session binding validator.
2. this checkpoint is protocol-layer only and does not replace required live endpoint replay closure.
3. no promotional state change is allowed in this section.

Replay commands executed (project-local lineage):

1. `python3 scripts/validate_headstamp_recurrence_closure.py --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
2. `python3 scripts/validate_headstamp_recurrence_closure.py --identity-id base-repo-audit-expert-v3 --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --operation scan --json-only`
3. `python3 scripts/validate_actor_session_binding.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id <base-repo-architect|base-repo-audit-expert-v3> --actor-id assistant:codex --operation scan --json-only`
4. `rg -n "/tmp" scripts/validate_headstamp_recurrence_closure.py scripts/compose_and_validate_governed_reply.py scripts/validate_reply_identity_context_first_line.py`

Findings:

1. resolver divergence class is closed in protocol layer:
   - `validate_headstamp_recurrence_closure.py` now resolves actor binding with identity-scoped lookup first (target identity), with explicit fallback mode annotation.
   - sampled identities (`base-repo-architect`, `base-repo-audit-expert-v3`) now both return `headstamp_recurrence_closure_status=PASS_REQUIRED`.
2. mismatch negative remains fail-close and machine-explainable:
   - dynamic case keeps `error_code=IP-ASB-STAMP-SESSION-005`,
   - receipt now includes binding tuple metadata (`binding_selection_mode`, `binding_key_mode`, `binding_compare_token`, `binding_session_id`, `binding_entry_count`).
3. send-time/first-line path tuple metadata is synchronized:
   - `compose_and_validate_governed_reply.py` and `validate_reply_identity_context_first_line.py` now emit actor-binding selection metadata with identity-scoped precedence.
4. temp-path hardcoding is further reduced:
   - headstamp recurrence temp artifacts and compose preflight defaults are migrated to runtime temp resolver; targeted grep shows no fixed `/tmp` literals in the three scripts.

State impact:

1. `HOTFIX16-P0-002` protocol-layer resolver divergence residual is closed.
2. `HOTFIX16-P0-002` remains `SPEC_READY / PENDING_INTAKE` pending independent live lane/headstamp replay archive.
3. release boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.25 Round-8 Multi-Source Protocol-Feedback Convergence Checkpoint (`HEAD=d5f75d7+`, 2026-03-07)

Scope lock:

1. this checkpoint ingests protocol-lane evidence only and excludes instance business scenarios.
2. this checkpoint consolidates three independent protocol-feedback channels under one convergence verdict.
3. no promotional state change is allowed in this section.

Four-track consolidation (`T1..T4`, protocol layer):

1. `T1` intake batches (protocol lane):
   - `FEEDBACK_BATCH_20260307T070548Z_v16_upgrade_cross_track_alignment_regression.md`
   - `FEEDBACK_BATCH_20260307T071111Z_protocol_lane_four_track_crosscheck_sanitized.md`
   - `FEEDBACK_BATCH_2026-03-07_002_protocol-lane-post-escalation.md`
2. `T2` channel integrity validators:
   - `validate_protocol_feedback_ssot_archival -> PASS_REQUIRED`
   - `validate_protocol_vendor_semantic_isolation -> PASS_REQUIRED`
   - `validate_protocol_feedback_reply_channel -> SKIPPED_NOT_REQUIRED (contract_not_required; non-failure)`
3. `T3` replay convergence checks:
   - run-id selection determinism,
   - strict-surface requiredization homomorphism (`update/readiness/three-plane/full-scan`),
   - headstamp/session-refresh strictness and semantic convergence.
4. `T4` evidence indexing:
   - each batch is indexed via canonical `runtime/protocol-feedback/evidence-index/INDEX.md` and linked with machine receipts.

Findings (protocol-layer only):

1. positive reinforcement remains confirmed:
   - no-hard-switch fail-close baseline remains effective,
   - parser/runtime crash class remains closed on strict chains,
   - canonical protocol-feedback archival integrity remains healthy.
2. convergence residuals remain open under `HOTFIX16-P1-004`:
   - run-id selector still has dual-naming compatibility gap (`identity-upgrade-exec-*.json` vs `<epoch>.json`) and may miss valid lineage.
   - strict surfaces can still split on same lineage (`update` required-failed non-zero vs `three-plane` required-failed zero).
   - three-plane may remain `BLOCKED` with `required_failed=0` when stale report fallback enters tuple/version alignment path.
   - session-refresh pointer/binding divergence still maps to warning-severity branch (`IP-ASB-RFS-002`) on strict paths, which is weaker than desired fail-close semantics.
   - semantic convergence residual remains visible; latest protocol-feedback rounds show active blocker shape has shifted from legacy `IP-SEM-004` trace to `IP-SEM-001` field-completeness failure (`intent_domain/intent_confidence/classifier_reason` missing under `ACTIVITY_UNSCOPED`).

Required protocol-layer hardening (architect lane):

1. unify run-id report selector to support dual report naming with deterministic tie-break in all strict surfaces.
2. enforce same-lineage convergence tuple parity across `validate_required_contract_coverage`, `report_three_plane_status`, and `full_identity_protocol_scan`:
   - `failed_required_contract_count`
   - `report_selected_path`
   - `run_id_binding`
3. promote strict session-refresh pointer/binding divergence from warning to fail-close on strict operations unless explicit audited override is present.
4. split reply-channel applicability from canonical egress gateway applicability:
   - `validate_protocol_feedback_reply_channel` may remain `SKIPPED_NOT_REQUIRED(contract_not_required)` when contract is not requiredized;
   - canonical send-time egress gateway (`validate_send_time_reply_gate`) must be requiredized for user-visible outbound strict operations and cannot stay skip-only.
5. require cross-surface egress tuple parity across creator/readiness/three-plane/full-scan/e2e/ci:
   - `send_time_gate_enforced`
   - `required_contract`
   - `send_time_gate_status`
   - `governed_outlet_enforced`
   - `outlet_bypass_detected`
6. enforce semantic metadata completeness contract on protocol-feedback path:
   - strict protocol-lane semantic guard must emit deterministic `intent_domain`, `intent_confidence`, and `classifier_reason`;
   - if activity correlation is not scoped, emit explicit correlated blocker receipt with recovery key instead of silently degrading semantic tuple completeness.

State impact:

1. this checkpoint confirms substantial protocol hardening but not closure.
2. `HOTFIX16-P1-004`, `FIX16-035`, and `FIX16-036` remain non-promotional pending convergence replay closure.
3. lifecycle boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.30 Round-11 Protocol-Feedback Semantic Regression Convergence Checkpoint (`HEAD=5c3dda4+`, 2026-03-07)

Scope lock:

1. this checkpoint ingests protocol-lane feedback only and excludes business-domain semantics.
2. this checkpoint targets recurrent semantic convergence blockers under `HOTFIX16-P1-004`.
3. no promotional state change is allowed from this section.

Cross-source intake (`T1..T4`, protocol layer):

1. `T1` protocol feedback batches:
   - `FEEDBACK_BATCH_20260307T090934Z_protocol_fix_reverify_semantic_routing_sanitized.md` (`custom-creative-ecom-analyst` protocol lane reverify).
   - `FEEDBACK_BATCH_2026-03-07_003_protocol-lane-regression-round3.md` (`system-requirements-analyst` protocol lane regression round3).
2. `T2` channel/index integrity:
   - both batches are indexed in canonical `runtime/protocol-feedback/evidence-index/INDEX.md` with paired validation/review artifacts.
3. `T3` machine evidence replay:
   - `custom-creative-ecom-analyst`: send-time/first-line/headstamp/actor-bound checks pass, but semantic guard remains `FAIL_REQUIRED` with `IP-SEM-001`.
   - `system-requirements-analyst`: lane routing remains protocol-correct, yet update remains non-green (`all_ok=false`, `writeback_status=DEFERRED_VALIDATION_FAILED`), three-plane remains `BLOCKED` (`IP-UPG-002`), and semantic guard remains `IP-SEM-001`.
4. `T4` externalized receipts:
   - absolute-path evidence references and canonical outbox/index linkage are present for both streams.

Findings (protocol-layer only):

1. semantic blocker family is now deterministically field-completeness-driven:
   - active strict blocker: `IP-SEM-001`;
   - missing semantic tuple fields: `intent_domain`, `intent_confidence`, `classifier_reason`;
   - activity correlation status frequently presents as `ACTIVITY_UNSCOPED`.
2. this is a protocol control-plane convergence issue, not a lane-routing failure:
   - protocol lane routing can be `PASS_REQUIRED` while semantic/writeback closure still blocks release.
3. convergence remains non-promotional until same-lineage strict surfaces consume identical semantic tuple outcomes.

Required protocol hardening (architect lane):

1. make semantic metadata tuple mandatory on protocol-feedback path for strict protocol operations.
2. when correlation cannot be scoped, emit deterministic blocker receipt + recovery key (no silent tuple omission).
3. tie writeback green state to semantic tuple completeness so `DEFERRED_VALIDATION_FAILED` (`IP-UPG-002`) cannot persist with unresolved `IP-SEM-001`.

State impact:

1. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` with updated active blocker shape (`IP-SEM-001`).
2. lifecycle boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.26 Round-8 Temp-Resolver Residual Pre-Implementation Reinforcement (`HEAD=f53f36a+`, 2026-03-07)

Scope lock:

1. this reinforcement section is protocol-layer only and targets residual fixed temp-root fallback debt.
2. this section is pre-implementation guidance for code landing; no closure claim is made here.
3. no promotion state change is allowed from this section.

Residuals identified by cross-check:

1. `scripts/execute_identity_upgrade.py` still contains fixed-path compatibility fallbacks that can bypass runtime temp resolver policy for:
   - capability report fallback output,
   - pre-mutation reply/blocker receipt defaults,
   - legacy output-dir default aliasing.
2. `scripts/validate_execution_report_freshness.py` still scans hardcoded temp roots in candidate fallback selection.
3. `scripts/validate_identity_protocol_baseline_freshness.py` still scans hardcoded temp roots in report fallback selection.

Architect hardening requirements before code landing:

1. all three scripts must consume `runtime_temp_path_common` as the sole dynamic temp-root source (`runtime_temp_root`, `runtime_temp_file`, or equivalent helper).
2. explicit CLI/report overrides remain highest priority, but fallback roots must be runtime/environment-driven and deterministic.
3. legacy compatibility aliases are allowed only when they resolve through runtime temp resolver semantics (no fixed `/tmp` literals).
4. replay contract must include both static and runtime verification:
   - static: targeted grep for `/tmp` literals on the three scripts,
   - runtime: positive replay with default paths and negative replay with missing-report/missing-candidate scenarios.

Required acceptance commands (post-implementation):

1. `rg -n "/tmp" scripts/execute_identity_upgrade.py scripts/validate_execution_report_freshness.py scripts/validate_identity_protocol_baseline_freshness.py`
2. `python3 -m py_compile scripts/execute_identity_upgrade.py scripts/validate_execution_report_freshness.py scripts/validate_identity_protocol_baseline_freshness.py`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. this section adds implementation guidance only and does not assert closure.
2. `HOTFIX16-P1-003` remains `SPEC_READY / PENDING_INTAKE` until the three-script residuals are code-landed and replay-verified.
3. release boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.27 Unified Protocol Control-Plane Entrypoint Freeze (`HOTFIX16-P0-007`, 2026-03-07)

Scope lock:

1. this checkpoint is protocol-layer only and excludes instance business semantics.
2. this checkpoint targets recurring scattered gate fixes by enforcing one management/wiring entrypoint.
3. this checkpoint is a control-plane freeze and cannot be used to claim promotion readiness.
4. this checkpoint is independent from `HOTFIX16-P0-002` (lane/headstamp); no mixed closure is allowed.

Unified control model (mandatory):

1. single registry source-of-truth:
   - all protocol required-gate definitions must originate from `identity/protocol/mappings/contract-binding.v1.6.yaml`.
2. single wiring entrypoint:
   - all required-gate additions/removals must be wired through `scripts/validate_required_contract_coverage.py` first;
   - direct per-surface ad-hoc gate lists are prohibited unless generated from the same registry tuple.
3. single strict-surface convergence requirement:
   - `scripts/release_readiness_check.py`
   - `scripts/identity_creator.py` (`validate/update`)
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `.github/workflows/_identity-required-gates.yml`
   - these surfaces must converge from one gate-set lineage and one tuple schema.
4. single outbound verdict source remains mandatory:
   - `scripts/validate_send_time_reply_gate.py` is the canonical user-visible outbound hard gate and cannot be bypassed.

Four-track mandatory closure for any control-plane mutation:

1. `T1 governance/spec`: clause + contract-id/version delta.
2. `T2 wiring`: registry-to-surface propagation proof on all strict surfaces.
3. `T3 replay`: deterministic `positive + negative + bypass-negative` with same `run_id`.
4. `T4 protocol-feedback`: canonical outbox batch + evidence-index pointer set.
5. this four-track bundle is a mutation verification workflow for control-plane changes only; it is not a blanket requirement for every unrelated protocol patch.

Reserved anti-drift error-code family (control-plane):

1. `IP-GATE-ENTRY-001` (`registry_source_missing_or_stale`)
2. `IP-GATE-ENTRY-002` (`surface_wiring_not_from_registry_tuple`)
3. `IP-GATE-ENTRY-003` (`cross_surface_tuple_divergence`)
4. `IP-GATE-ENTRY-004` (`control_plane_mutation_without_four_track_bundle`)

Required replay tuple parity (same lineage, strict surfaces):

1. `run_id_binding`
2. `report_selected_path`
3. `failed_required_contract_count`
4. `required_contract`
5. `send_time_gate_status`
6. `outlet_bypass_detected`

Minimum executable acceptance commands:

1. `python3 scripts/validate_required_contract_coverage.py --catalog <CATALOG> --identity-id <ID> --operation update --json-only`
2. `python3 scripts/report_three_plane_status.py --catalog <CATALOG> --identity-id <ID> --actor-id assistant:codex --json-only`
3. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids <ID> --project-catalog <CATALOG> --global-catalog /tmp/nonexistent-catalog.yaml --actor-id assistant:codex --json-only`
4. `python3 scripts/release_readiness_check.py --identity-id <ID> --catalog <CATALOG> --actor-id assistant:codex --json-only`
5. `python3 scripts/docs_command_contract_check.py`
6. `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. this section establishes continuous anti-drift governance for protocol control-plane entrypoint management.
2. lifecycle boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.28 Round-8 Actor-Bound Unified Strict Entry Closure (`HEAD=fc662b8+`, 2026-03-07)

Scope lock:

1. this checkpoint is protocol-layer only and focuses on strict operation entry semantics (`activate/update/validate` + wave apply path).
2. this checkpoint addresses canonical active pointer drift impacting default actor semantics at entry, without changing business-level validator rules.
3. no promotion state change is allowed in this section.

Four-track confirmation (`T1..T4`):

1. `T1 kernel/governance contract`
   - strict entry must be actor-bound and explicit; implicit actor fallback is disallowed for strict paths.
   - actor binding validation must run before strict operation chains continue.
2. `T2 script/runtime closure`
   - `scripts/identity_creator.py` now requires explicit `--actor-id` for strict `activate/update/validate` entry.
   - `scripts/identity_creator.py` now runs `validate_actor_session_binding.py` as entry preflight for strict validate/update.
   - `scripts/execute_identity_upgrade.py` auto header-first preflight now requires explicit actor context.
   - `scripts/run_protocol_upgrade_wave.py --apply` now requires explicit actor and forwards it into update invocations.
3. `T3 replay/acceptance behavior`
   - missing actor on strict entry fails fast with deterministic code `IP-ACTOR-ENTRY-001`;
   - explicit actor with binding mismatch remains fail-close via actor-session binding guard;
   - explicit actor with valid binding proceeds into downstream strict gate chain.
4. `T4 review/ledger synchronization`
   - review ledger includes this actor-entry convergence replay in hotfix evidence trail and decision row language.

Acceptance commands:

1. `python3 scripts/identity_creator.py validate --identity-id <id> --catalog <catalog> --scope <scope>`
2. `python3 scripts/identity_creator.py update --identity-id <id> --catalog <catalog> --mode review-required --scope <scope>`
3. `python3 scripts/identity_creator.py validate --identity-id <id> --catalog <catalog> --scope <scope> --actor-id <actor_id>`
4. `python3 scripts/run_protocol_upgrade_wave.py --catalog <catalog> --repo-catalog identity/catalog/identities.yaml --apply --actor-id <actor_id>`

Expected outcomes:

1. command (1) and (2) must fail with `IP-ACTOR-ENTRY-001` when actor is not explicit.
2. command (3) must pass entry guard and then follow normal downstream validator outcomes.
3. command (4) must reject `--apply` without actor and proceed deterministically with explicit actor.

State impact:

1. strict actor-entry ambiguity is reduced by moving to one explicit actor-bound entry contract.
2. `HOTFIX16-P0-006` remains `SPEC_READY / PENDING_INTAKE` until required=true tuple replay archive and runtime bridge rollout evidence are attached.
3. lifecycle boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.29 Round-10 UCG Pre-Code Readiness Reinforcement (`HEAD=30423c5+`, 2026-03-07)

Scope lock:

1. this checkpoint is discussion-only (no code landing claim) and prepares protocol-layer implementation for unified control-plane hardening.
2. this checkpoint addresses recurring control-plane regressions (`identity hard switch`, `headstamp loss`, `protocol lane entry split`) as one root-cause family.
3. no promotion state change is allowed from this section.

Observed baseline alignment (pre-code snapshot):

1. protocol repo snapshot is clean at checkpoint capture (`git status --short` empty).
2. prior separation remains intact:
   - lane/headstamp continuity track (`HOTFIX16-P0-002`) remains scoped to canonical egress/lane continuity.
   - unified control-plane entrypoint track (`HOTFIX16-P0-007`) remains independent and is not merged into lane/headstamp row semantics.

Four-track cross-check conclusion (`T1..T4`):

1. `T1 roundtable/governance`:
   - existing roundtable consensus confirms semantic verdict is not yet single-source and requires canonical contract convergence.
2. `T2 base-repo code audit`:
   - repeated gate wiring remains multi-surface and drift-prone when lists are maintained per surface.
   - send-time applicability still splits by operation class (`scan` vs strict operations), proving that script presence alone is insufficient without unified enforcement entry.
3. `T3 vendor trajectory`:
   - vendor scan posture supports layered governance with centralized control-plane boundaries, not scattered per-surface control mutation.
4. `T4 online references`:
   - zero-trust and policy-plane references support centralized decision/enforcement boundaries and unified audit chain (`NIST ZTA`, `OPA discovery/decision logs`, `Envoy ext_authz`, `MCP lifecycle`).

Unified control model (UCG) confirmed for implementation planning:

1. `1门` (`Single Entry Door`):
   - strict operations must enter through one actor-bound/lane-bound preflight entry and emit one entry receipt tuple.
2. `1判` (`Single Final Verdict`):
   - user-visible outbound path must consume one canonical egress verdict; bypass and side-channel verdict substitution are fail-close.
3. `1账` (`Single Machine Ledger`):
   - all strict surfaces must emit and consume one shared machine tuple contract for replay parity:
     - `run_id_binding`
     - `report_selected_path`
     - `required_contract`
     - `failed_required_contract_count`
     - `send_time_gate_status`
     - `outlet_bypass_detected`

Implementation prerequisites (before broader code rollout):

1. move strict-surface gate-set execution to one bundle runner (surfaces no longer own independent hardcoded gate arrays as control source).
2. keep mapping registry as single control-source and enforce CI drift detection against per-surface divergence.
3. add recurrence escalator:
   - when same error-code family reappears across multiple strict surfaces in bounded window, upgrade path is forced to control-plane change track (`HOTFIX16-P0-007`) instead of local patch-only closure.
4. apply four-track mandatory closure only to control-plane mutations (to avoid deadlock on ordinary business patches).

Implementation-freeze manifest (must be frozen before code landing):

1. canonical UCG artifacts (single-source naming freeze):
   - control-plane contract id: `hotfix_p0_007_ucg_control_plane_freeze_contract_v1`.
   - bundle-runner artifact key: `required_gate_bundle_runner` (target file name frozen as `required_gate_bundle_runner.py`, under scripts directory).
   - registry-source validator artifact key: `required_gate_registry_source_validator` (current canonical script remains `validate_required_contract_coverage.py`).
   - tuple-parity validator artifact key: `required_gate_tuple_parity_validator` (target file name frozen as `validate_required_gate_tuple_parity.py`, under scripts directory).
   - CI drift validator artifact key: `required_gate_surface_drift_validator` (target file name frozen as `validate_required_gate_surface_drift.py`, under scripts directory).
2. mandatory strict-surface migration list (all six must switch to bundle-runner lineage):
   - `scripts/identity_creator.py` (`validate/update` chains)
   - `scripts/release_readiness_check.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/e2e_smoke_test.sh`
   - `.github/workflows/_identity-required-gates.yml`
3. migration completion rule:
   - any strict surface still carrying independently maintained required-gate arrays after rollout is treated as convergence failure (`IP-GATE-ENTRY-002` family) and blocks promotion.

Recurrence escalator (quantitative trigger freeze):

1. identity of "same error family":
   - same prefix pattern up to numeric tail (example: `IP-ASB-STAMP-*`, `IP-GATE-ENTRY-*`).
2. window + threshold:
   - `L1` observation: `>=2` hits across `>=2` strict surfaces within rolling `24h` -> open recurrence receipt (non-promotional).
   - `L2` escalation: `>=3` hits across `>=2` strict surfaces within rolling `72h` -> force upgrade path to `HOTFIX16-P0-007` and require four-track mutation bundle.
   - `L3` freeze: `>=5` hits or second `L2` event within rolling `7d` -> control-plane merge freeze until tuple-parity replay is archived.
3. action level:
   - `L1`: evidence-index append only.
   - `L2`: mandatory governance/review hotfix mutation row + CI drift checks in required chain.
   - `L3`: promotion freeze on affected rows (`SPEC_READY / PENDING_INTAKE` lock persists).

UCG operation semantics matrix (required-contract consistency freeze):

| Operation | Run profile | required_contract formula | Legal non-applicable output | required=true failure behavior |
| --- | --- | --- | --- | --- |
| `scan` | observation | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + `required_contract_not_applicable_no_current_round_evidence_source` | `FAIL_REQUIRED` allowed as observational evidence (non-promotion) |
| `validate` | strict | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + same machine reason | fail-close gate |
| `update` | strict | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + same machine reason | fail-close gate |
| `readiness` | strict | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + same machine reason | fail-close gate |
| `e2e` | strict | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + same machine reason | fail-close gate |
| `ci` | strict | `mapping_required AND current_round_linked` | `SKIPPED_NOT_REQUIRED` + same machine reason | fail-close gate |

Send-time canonicalization freeze (pre-code binding):

1. canonical send-time verdict remains single-source and cannot be replaced by per-surface fallback verdict.
2. strict operations (`validate/update/readiness/e2e/ci`) are not allowed to return `contract_not_required` for canonical send-time gate when `required_contract=true`.
3. observation (`scan`) may report skip only under matrix-defined non-applicable condition; synthetic skip without machine reason is treated as drift.

State impact:

1. this checkpoint confirms high necessity and feasibility of UCG hardening at protocol layer.
2. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE` until bundle-runner + tuple-parity + CI hard-gate replay are archived.
3. lifecycle boundary remains unchanged: `SPEC_READY / PENDING_INTAKE`, `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.31 Round-12 UCG Code Landing Wave-1 (`HEAD=1deba9d+`, 2026-03-07)

Scope lock:

1. this wave implements control-plane wiring convergence only; it does not claim promotion closure.
2. this wave is constrained to `HOTFIX16-P0-007` implementation-freeze manifest and does not alter business-domain contracts.
3. non-promotional boundary remains mandatory.

Landed canonical artifacts (`single-source naming freeze`):

1. bundle-runner landed:
   - `scripts/required_gate_bundle_runner.py`
   - supports full bundle execution (`RQ-017/018/019/020/021/022/030/033`) and target-probe compatibility mode (`--target-name`) under same registry lineage.
2. tuple parity validator landed:
   - `scripts/validate_required_gate_tuple_parity.py`
   - tuple contract fields: `run_id_binding`, `report_selected_path`, `required_contract`, `failed_required_contract_count`, `send_time_gate_status`, `outlet_bypass_detected`.
3. surface drift validator landed:
   - `scripts/validate_required_gate_surface_drift.py`
   - blocks direct per-surface validator drift and enforces bundle-runner reference on strict surfaces.

Strict-surface migration closure (wave-1 wiring):

1. `scripts/identity_creator.py` (`validate/update`) now executes bundle-runner lineage for Batch-6/7 + execution-target gates.
2. `scripts/release_readiness_check.py` now executes bundle-runner lineage instead of per-validator direct wiring.
3. `scripts/report_three_plane_status.py` now resolves target checks through bundle-runner target-probe mode.
4. `scripts/full_identity_protocol_scan.py` now resolves target checks through bundle-runner target-probe mode.
5. `scripts/e2e_smoke_test.sh` now calls bundle-runner lineage for the same gate cluster.
6. `.github/workflows/_identity-required-gates.yml` now calls bundle-runner lineage and executes surface-drift validation preflight.
7. `scripts/create_identity_pack.py` default required-check set now points to bundle-runner lineage (removes direct per-validator list drift).

Replay posture (wave-1):

1. bundle-runner local probe (`operation=scan`) is executable and returns deterministic target rows.
2. surface drift validator returns `PASS_REQUIRED` after six-surface migration.
3. tuple parity validator is executable; required-chain mandatory replay archive remains pending before promotion.

State impact:

1. `HOTFIX16-P0-007` progresses from design freeze to executable wave-1 wiring closure.
2. row remains `SPEC_READY / PENDING_INTAKE` until required=true tuple-parity replay + independent audit replay archive are attached.
3. lifecycle boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.32 Round-13 UCG Code Landing Wave-2 (`HEAD=af0f684+dirty`, 2026-03-07)

Scope lock:

1. this wave is protocol-layer closure only and extends `HOTFIX16-P0-007` wave-1 lineage; no business-domain contract expansion is introduced.
2. this wave closes recurrence/tuple parity execution surfaces and payload projection parity; promotion state remains frozen.
3. this wave also absorbs replay audit findings for `HOTFIX16-P0-005` and `HOTFIX16-P1-004` runtime behavior consistency.

Wave-2 landed deltas:

1. bundle runner receipt persistence:
   - `scripts/required_gate_bundle_runner.py` now supports `--out` for deterministic receipt file emission in both bundle mode and target-probe mode.
2. recurrence escalator machine gate:
   - `scripts/validate_required_gate_recurrence_escalator.py` landed with quantized escalation (`L1/L2/L3`) over error-family recurrence windows and optional hard block mode (`--enforce-blocking`).
3. strict-surface lineage expansion:
   - `release_readiness_check`, `identity_creator(validate/update)`, `report_three_plane_status`, `full_identity_protocol_scan`, `e2e_smoke_test.sh`, and required-gates CI now invoke:
     - bundle runner receipt emission;
     - recurrence escalator;
     - tuple parity validator.
4. drift guard strengthening:
   - `scripts/validate_required_gate_surface_drift.py` now enforces all three mandatory lineage artifacts (`bundle_runner + recurrence_escalator + tuple_parity`) across six strict surfaces.
5. scanner/three-plane payload closure:
   - `report_three_plane_status` and `full_identity_protocol_scan` now project `required_gate_bundle_runner`, `required_gate_recurrence_escalator`, and `required_gate_tuple_parity` fields into machine-readable payloads.

Replay and consistency closure:

1. parser/runtime crash closure remains stable:
   - no `Namespace` attribute crash observed on `release_readiness_check` (`target_branch`) and `identity_creator validate` (`run_id`) entry path.
2. runtime mode guard strictness closure:
   - `validate_identity_runtime_mode_guard.py` strict operation set now includes `scan/three-plane/inspection`; env/catalog drift on these strict surfaces is fail-close unless audited override receipt exists.
3. observation applicability closure:
   - `validate_cross_workflow_schema.py` no longer forces `route_action/dedup_state` in observation profile without current-round linkage; non-applicable path returns deterministic `SKIPPED_NOT_REQUIRED`.

Cross-verified residual (not yet promotable):

1. external runtime replay on `system-requirements-analyst` (global lane) still reports:
   - `IP-UPG-002` (three-plane blocked),
   - `IP-SEM-001` (`intent_domain`, `intent_confidence`, `classifier_reason` missing).
2. this is treated as producer-side semantic metadata completeness debt and remains promotion-blocking until protocol-feedback emitter path provides deterministic semantic tuple fields per current round.

State impact:

1. `HOTFIX16-P0-007` stays `SPEC_READY / PENDING_INTAKE`; wave-2 improves enforcement homomorphism but does not satisfy replay-complete promotion threshold.
2. `HOTFIX16-P0-005` and `HOTFIX16-P1-004` retain non-promotional boundary pending independent replay archive closure on required=true datasets.
3. lifecycle boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.33 Round-14 UCG Four-Point Roundtable Reconciliation (`HEAD=af0f684+dirty`, 2026-03-07)

Scope lock:

1. this checkpoint is protocol-layer only and targets recurring control-plane defects (`identity hard switch perception`, `headstamp loss recurrence`, `protocol lane split verdict`).
2. this checkpoint is an implementation-vs-contract reconciliation pass for UCG (`1门 + 1判 + 1账`), not a business-domain validator expansion.
3. this checkpoint does not upgrade lifecycle state; it tightens wave-3 mutation requirements.

Four-track cross-verification anchors (`T1..T4`):

1. `T1 governance contract`: UCG contract remains `single entry + single final verdict + single machine tuple`, with replay tuple parity as mandatory closure.
2. `T2 code-path inspection` (current head):
   - `scripts/required_gate_bundle_runner.py` (line blocks: 185-199, 202-224, 321-340)
   - `scripts/validate_reply_identity_context_first_line.py:28,325,389-414`
   - `scripts/validate_send_time_reply_gate.py:21,228,242`
   - `.github/workflows/_identity-required-gates.yml` (line block: 288-290)
3. `T3 executable negative replay`:
   - `/tmp/ucg_bundle_badmap_now2.json` confirms bundle false-green window (`validator_rc=2`, row=`FAIL_OPTIONAL`, bundle=`PASS_REQUIRED`).
   - `/tmp/ucg_drift_gap_now.json` confirms drift detector bypass for non-listed direct validator alias.
4. `T4 runtime convergence replay`:
   - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260307T144051Z_v16_protocol_fix_post_verification.md` + `/tmp/office_ops_protocol_fix_verification_20260307.json` confirms `run_id_not_found`, `Conditional Go`, and `IP-PVA-003` tuple residuals.
   - `/tmp/cca_validate_protocol_handoff_20260307.log` vs `/tmp/cca_three_plane_protocol_handoff_20260307.log` confirms same-lineage layer-context divergence (`validate` fail-close vs `three-plane` non-blocking mismatch tails).
   - `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-07_003_protocol-lane-regression-round3.md` confirms `IP-UPG-002 + IP-SEM-001` protocol-lane residual blocker shape.

Roundtable verdict by the four mandatory control points:

1. control point A (`shared tuple resolver`): `PARTIAL`
   - tuple/layer/headstamp resolution is not yet single-function single-source across validate/three-plane/compose.
   - `three-plane` is still outside strict first-line operation set in current validator semantics.
2. control point B (`single canonical egress fail-close`): `PARTIAL`
   - canonical send-time path is present, but `WARN_NON_BLOCKING`/non-blocking mismatch branches remain reachable.
3. control point C (`entry tuple freeze: no fallback`): `NOT_CLOSED`
   - bundle runner still admits fallback tuple synthesis and optional failure downgrade when payload contract is absent.
4. control point D (`CI same-run cross-surface tuple equality`): `PARTIAL`
   - tuple parity validator is wired, but current CI invocation passes a single receipt and cannot prove cross-surface equality (`validate` vs `three-plane` vs `full-scan`).

Wave-3 required protocol-layer strengthening (mandatory for recurrence family):

1. enforce strict-operation homomorphism for headstamp tuple checks:
   - `validate` and `three-plane` must consume identical strictness policy for (`work_layer`, `source_layer`, `identity_id`, `actor_id`) mismatch handling.
2. close bundle false-green class:
   - validator execution failure with missing/invalid payload contract must fail-close under UCG control-plane track (no implicit optional downgrade).
3. harden tuple parity contract:
   - tuple parity validator must require at least two receipts from distinct strict surfaces and include surface labels in receipt schema.
4. harden CI parity replay:
   - required-gates CI must feed tuple parity with multi-surface receipts for same lineage token.
5. harden drift detection:
   - forbidden direct-validator set must be derived from mapping registry lineage rather than static script-name tuple.

Anti-deadlock guard (explicit):

1. four-track mandatory closure at this strict level applies only to recurring control-plane mutation class (`HOTFIX16-P0-007`) and its escalated recurrence windows.
2. non-control-plane updates keep tiered closure policy and are not forced into full freeze by default.

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`; round-14 confirms wave-2 is partially closed but not enforcement-complete.
2. promotion remains blocked until wave-3 closes control points `C` and `D`, and upgrades `A/B` from partial to deterministic pass.
3. lifecycle boundary remains unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.34 Round-15 UCG Wave-3 code hardening replay (`HEAD=working-tree+dirty`, 2026-03-07)

Scope lock:

1. this round implements round-14 mandatory wave-3 closure list only (no requirement expansion, no lifecycle promotion).
2. this round keeps protocol-layer boundary and preserves `SPEC_READY / PENDING_INTAKE`.
3. this round targets four control points `A/B/C/D` with executable replay evidence.

Implementation deltas (protocol code):

1. control point C (`entry tuple freeze`) closure:
   - `scripts/required_gate_bundle_runner.py` now enforces fail-close on row payload contract violations and validator non-zero return (`payload_contract_issues`, `row_contract_error_count`, `surface_label`, no tuple fallback synthesis).
2. control point D (`ci cross-surface tuple equality`) closure:
   - `scripts/validate_required_gate_tuple_parity.py` now requires multi-receipt parity (`--min-receipts`, distinct `surface_label` contract).
   - `.github/workflows/_identity-required-gates.yml` now feeds tuple parity with same-lineage dual receipts (`ci_validate` + `ci_three_plane`) instead of single receipt.
3. control point B strengthening (`canonical egress fail-close` on strict surfaces):
   - `scripts/validate_reply_identity_context_first_line.py` strict operation set now includes `three-plane` and `ci`.
   - `scripts/validate_send_time_reply_gate.py` strict operation set now includes `three-plane` and `ci`, and invalid-input branch now follows strict-context fail-close semantics.
4. control point A strengthening (`shared tuple resolver`) supporting hardening:
   - `scripts/report_three_plane_status.py` and `scripts/full_identity_protocol_scan.py` now emit/consume dual bundle receipts with explicit `surface_label` projection and parity payload fields.
5. drift guard closure:
   - `scripts/validate_required_gate_surface_drift.py` forbidden direct-validator set now derives from mapping registry rows (`identity/protocol/mappings/contract-binding.v1.6.yaml`) rather than static list.

Round-15 replay evidence (machine-replay):

1. bundle false-green closure replay:
   - `/tmp/ucg_wave3_badmap.yaml`
   - `/tmp/ucg_wave3_bundle_badmap.json`
   - observed result: target probe returns `FAIL_REQUIRED` + `IP-GATE-ENTRY-002` under invalid validator path.
2. tuple parity strict contract replay:
   - negative (`duplicate surface_label`) => `/tmp/ucg_wave3_tuple_dup.json` (`FAIL_REQUIRED`, `IP-GATE-ENTRY-003`).
   - positive (`cross-surface labels`) => `/tmp/ucg_wave3_tuple_cross_surface.json` (`PASS_REQUIRED`).
3. send-time strictness homomorphism replay:
   - `/tmp/ucg_wave3_sendtime_three_plane.json` confirms `three-plane` now fail-closes (`IP-ASB-STAMP-SESSION-002`) when strict send-time evidence is missing.
4. drift validator replay:
   - `/tmp/ucg_wave3_drift_mapping_derived.json` confirms mapping-derived forbidden-validator set and six-surface lineage pass.
5. bundle receipt dual-surface replay:
   - `/tmp/wave3-required-bundle-three-plane.json`
   - `/tmp/wave3-required-bundle-validate.json`

Control-point verdict update (after wave-3 landing):

1. control point A (`shared tuple resolver`): `PARTIAL` (strengthened; single-source function unification remains follow-up work).
2. control point B (`single canonical egress fail-close`): `PARTIAL` (strict surfaces aligned; non-strict observational operations intentionally preserved).
3. control point C (`entry tuple freeze: no fallback`): `CLOSED_FOR_WAVE3`.
4. control point D (`CI same-run cross-surface tuple equality`): `CLOSED_FOR_WAVE3`.

Acceptance commands (round-15 local replay):

1. `python3 -m py_compile scripts/required_gate_bundle_runner.py scripts/validate_required_gate_surface_drift.py scripts/validate_required_gate_tuple_parity.py scripts/release_readiness_check.py scripts/identity_creator.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py scripts/validate_reply_identity_context_first_line.py scripts/validate_send_time_reply_gate.py`
2. `bash -n scripts/e2e_smoke_test.sh`
3. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE` (wave-3 C/D closure landed; A/B still partial by design boundary).
2. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion remains blocked by unresolved protocol-lane residual family (`IP-UPG-002` + `IP-SEM-001`) and remaining A/B determinism convergence.

### 8.35 Round-16 semantic requiredization scope convergence (`HEAD=working-tree+dirty`, 2026-03-08)

Scope lock:

1. this round targets residual protocol-lane blocker family (`IP-SEM-001` / `IP-UPG-002`) under `HOTFIX16-P1-004`.
2. this is a protocol-layer applicability convergence patch; no lifecycle promotion is granted by this round alone.

Implementation deltas:

1. `scripts/validate_semantic_routing_guard.py`
   - adds inspection-path applicability short-circuit when required contract is not current-round linked.
   - prioritizes correlated current-round feedback batch selection before generic pattern fallback.
2. `scripts/validate_protocol_vendor_semantic_isolation.py`
   - migrates auto-required decision to lane-aware scope arbitration (`protocol_feedback_lane_common`).
   - adds current-round correlated batch preference and inspection-path skip for history-only activity.
3. `scripts/validate_external_source_trust_chain.py`
   - same lane-aware requiredization scope convergence as above.
   - same correlated batch preference and history-only inspection skip.
4. `scripts/validate_protocol_data_sanitization_boundary.py`
   - same lane-aware requiredization scope convergence as above.
   - same correlated batch preference and history-only inspection skip.

Replay evidence (local protocol-layer):

1. semantic/vendor/source/sanitization guard probes on `base-repo-architect` (`operation=three-plane`) now converge to deterministic non-blocking applicability result for history-only lane activity:
   - `SKIPPED_NOT_REQUIRED`
   - stale reason: `contract_not_required_due_lane_scope_history_only_activity`.
2. acceptance gate replay:
   - `python3 -m py_compile scripts/validate_semantic_routing_guard.py scripts/validate_protocol_vendor_semantic_isolation.py scripts/validate_external_source_trust_chain.py scripts/validate_protocol_data_sanitization_boundary.py`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` until independent multi-identity replay confirms `IP-SEM-001` / `IP-UPG-002` residual family is cleared in protocol lane.
2. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.36 Round-17 UCG wave-3.1 hard-boundary replay (`HEAD=working-tree+dirty`, 2026-03-08)

Scope lock:

1. this round only addresses the remaining wave-3 control-plane residuals reported in fixed audit conclusion (`P0 coherence non-blocking leak` + `P1 drift alias bypass` + `P1 same-surface shadow parity`).
2. no requirement expansion and no lifecycle promotion are introduced by this round.
3. protocol-layer boundary remains strict (`SPEC_READY / PENDING_INTAKE`).

Implementation deltas (protocol code):

1. coherence strictness closure (P0):
   - `scripts/validate_execution_reply_identity_coherence.py` strict operations now include `three-plane` and `ci`.
   - `scripts/report_three_plane_status.py` now hard-blocks on both `FAIL_REQUIRED` and `WARN_NON_BLOCKING` for coherence verdict projection.
2. drift alias-bypass closure (P1):
   - `scripts/validate_required_gate_surface_drift.py` now derives forbidden direct-validator set from mapping lineage plus deterministic alias expansion:
     - versioned wrapper alias (`validate_vXX_* -> validate_*`, `normalize_vXX_* -> normalize_*`),
     - wrapper delegate import alias (`from <module> import main`).
   - this closes the previously reproducible mapping-external direct-call gap (`validate_skill_path_integrity.py` style bypass).
3. tuple parity cross-operation closure (P1):
   - `scripts/validate_required_gate_tuple_parity.py` adds `--require-distinct-operations`.
   - strict surfaces now feed parity with operation-diverse receipts (no same-operation shadow-only parity):
     - `identity_creator.py` (`validate/update` vs `scan_probe`),
     - `release_readiness_check.py` (`readiness` vs `scan_probe`),
     - `report_three_plane_status.py` (`three-plane` vs `scan_probe`),
     - `full_identity_protocol_scan.py` (`scan` vs `validate_probe`),
     - `e2e_smoke_test.sh` (`e2e` vs `scan_probe`),
     - `.github/workflows/_identity-required-gates.yml` now enforces operation-diverse parity contract explicitly.

Round-17 replay evidence (machine-replay):

1. coherence strict replay (negative):
   - command emits `FAIL_REQUIRED` for tuple mismatch under `operation=three-plane`:
   - evidence: `/tmp/coh_three_plane_now.json` (`coherence_status=FAIL_REQUIRED`, `strict_operation=true`).
2. drift bypass replay (negative):
   - injected direct alias (`scripts/validate_skill_path_integrity.py`) on strict surface now fails drift gate.
   - evidence: `/tmp/ucg_wave31_drift_repro.json` (`required_gate_surface_drift_status=FAIL_REQUIRED`, `IP-GATE-ENTRY-002`).
3. tuple parity distinct-operation replay:
   - duplicate operation receipts now fail with deterministic reason (`distinct_operations_not_met`).
   - operation-diverse receipts pass.
   - evidence: `/tmp/tp_same_now.json` (fail), `/tmp/tp_diff_now.json` (pass), `/tmp/rg_parity_wave31.json` (pass).
4. strict-surface scan replay (non-crash + payload projection):
   - `full_identity_protocol_scan.py` target replay remained executable after operation-diverse parity wiring.
   - evidence: `/tmp/full_scan_wave31.json`.

Acceptance commands (round-17 local replay):

1. `python3 -m py_compile scripts/validate_execution_reply_identity_coherence.py scripts/validate_required_gate_surface_drift.py scripts/validate_required_gate_tuple_parity.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py`
2. `bash -n scripts/e2e_smoke_test.sh`
3. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`; this round closes the reported wave-3.1 P0/P1 residual classes in protocol code-path, pending independent auditor replay sign-off.
2. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.
3. promotion remains blocked by residual protocol-lane backlog family (`IP-UPG-002`, `IP-SEM-001`) until separate replay closure is archived.

### 8.37 Round-18 protocol-lane residual convergence (`HEAD=working-tree+dirty`, 2026-03-08)

Scope lock:

1. this round targets the remaining residual blocker family surfaced by `system-requirements-analyst` replay (`IP-UPG-002` with semantic/writeback non-green recurrence).
2. this round remains protocol-layer only; no identity-instance business mutation is introduced.
3. lifecycle boundary remains non-promotional (`SPEC_READY / PENDING_INTAKE`).

Implementation deltas (protocol code):

1. semantic metadata inference hardening (residual `IP-SEM-001` shape):
   - `scripts/validate_semantic_routing_guard.py` now infers deterministic semantic tuple defaults when feedback batches omit explicit fields:
     - `intent_domain`,
     - `intent_confidence`,
     - `classifier_reason`.
   - inference is machine-stamped (`semantic_fields_inferred`, `semantic_inference_mode`) and remains bounded to protocol/business/mixed/unknown enum.
2. handoff/collaboration stale-log false-block closure on update self-test lane:
   - `scripts/validate_agent_handoff_contract.py` and `scripts/validate_identity_collab_trigger.py` now select bounded recent evidence windows before strict validation.
   - both validators now disable age-based stale blocking when `--self-test` is explicitly requested (self-test remains structural + positive/negative sample integrity gate).
3. changelog backfill linkage closure for historical strict gate replay:
   - `CHANGELOG.md` now includes explicit backfill anchors for prior strict range heads (`0a6359a`, `6af084f`) to unblock deterministic historical-range replay of `validate_changelog_updated.py`.

Round-18 replay evidence:

1. semantic routing replay on the previously failing protocol-lane batch:
   - command output: `/tmp/semantic_guard_round3_wave18.json`
   - status: `PASS_REQUIRED`, `semantic_fields_inferred=true`, `semantic_inference_mode=protocol_context_inference`.
2. handoff validator replay (`system-requirements-analyst`, global lane):
   - `validate_agent_handoff_contract.py --self-test` now returns `PASSED` without stale-log false block.
3. collaboration trigger replay (`system-requirements-analyst`, global lane):
   - `validate_identity_collab_trigger.py --self-test` now returns `PASSED`; stale-age branch is no longer promotion-blocking in explicit self-test mode.
4. changelog range replay:
   - historical strict range for `0a6359a` now passes via explicit backfill linkage (`validate_changelog_updated PASSED (historical backfill linkage)`).

Acceptance commands (round-18 local replay):

1. `python3 -m py_compile scripts/validate_agent_handoff_contract.py scripts/validate_identity_collab_trigger.py scripts/validate_semantic_routing_guard.py`
2. `python3 scripts/validate_agent_handoff_contract.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --self-test`
3. `python3 scripts/validate_identity_collab_trigger.py --identity-id system-requirements-analyst --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --self-test`
4. `python3 scripts/validate_semantic_routing_guard.py --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --identity-id system-requirements-analyst --feedback-batch /Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-07_003_protocol-lane-regression-round3.md --operation three-plane --expected-work-layer protocol --expected-source-layer global --json-only`

State impact:

1. `HOTFIX16-P1-004` remains `SPEC_READY / PENDING_INTAKE` pending independent full-chain replay sign-off (`update + three-plane + full-scan`) on latest head.
2. `IP-UPG-002` and `IP-SEM-001` are narrowed from recurrent structural blockers to replay-closure verification items under auditor re-run.
3. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.38 Round-19 UCG tuple-source convergence audit (`HEAD=6af084f+dirty`, 2026-03-08)

Scope lock:

1. this round is protocol-layer audit reinforcement for recurring control-plane defects (`headstamp drift`, `identity drift`, `protocol lane split`) under `HOTFIX16-P0-007`.
2. this round is docs-only intake; no protocol code mutation is introduced in this checkpoint.
3. lifecycle boundary remains non-promotional (`SPEC_READY / PENDING_INTAKE`).

Four-track cross-verification (`T1..T4`):

1. `T1 runtime replay`:
   - `/tmp/audit_ctx_resolve_base_repo_architect_20260308_r2.json`
   - `/tmp/audit_ctx_render_base_repo_architect_20260308_r2.json`
   - `/tmp/audit_validate_latest_20260308.log`
   - `/tmp/tuple_parity_gap_result_r2.json`
   - `/tmp/audit_compose_reply.txt`
   - `/Users/yangxi/claude/codex_project/weixinstore/.identity/session/active_identity.json`
2. `T2 code-path replay anchors`:
   - source-layer normalization split:
     - `scripts/resolve_identity_context.py:221`
     - `scripts/resolve_identity_context.py:341`
     - `scripts/response_stamp_common.py:337`
     - `scripts/response_stamp_common.py:437`
   - strict chain actor propagation surfaces:
     - `scripts/identity_creator.py:1665`
     - `scripts/identity_creator.py:1713`
     - `scripts/identity_creator.py:1835`
     - `scripts/report_three_plane_status.py:522`
     - `scripts/report_three_plane_status.py:605`
     - `scripts/report_three_plane_status.py:787`
     - `scripts/release_readiness_check.py:594`
     - `scripts/full_identity_protocol_scan.py:622`
   - historical binding fallback surface:
     - `scripts/compose_and_validate_governed_reply.py:53`
     - `scripts/compose_and_validate_governed_reply.py:63`
     - `scripts/response_stamp_common.py:199`
     - `scripts/actor_session_common.py:231`
   - tuple parity contract surface:
     - `scripts/validate_required_gate_tuple_parity.py:12`
3. `T3 strict-surface bundle projection check`:
   - `/private/var/folders/3x/xy0h9s6x5p790dzwwrdzq3kh0000gn/T/identity-runtime/required-gate-bundle/three-plane/base-repo-architect/three-plane-base-repo-architect/required-gate-bundle-three-plane-base-repo-architect-three-plane-base-repo-architect.json`
   - `/private/var/folders/3x/xy0h9s6x5p790dzwwrdzq3kh0000gn/T/identity-runtime/required-gate-bundle/scan/base-repo-architect/three-plane-base-repo-architect-scan-probe/required-gate-bundle-three-plane-scan-probe-base-repo-architect-three-plane-base-repo-architect.json`
4. `T4 governance/review parity`:
   - this round requires synchronized update across governance section `8.38`, review rolling summary `HOTFIX16-P0-007`, review detail, and decision log row.

Round-19 confirmed residuals (protocol only):

1. source-layer taxonomy split remains reproducible:
   - resolver reports `source_layer=project` while response-stamp path normalizes to `source_layer=project`.
2. strict headstamp chain still has actor propagation gap:
   - strict surfaces call render/first-line/coherence paths without explicit `--actor-id`, which permits fallback actor resolution drift.
3. `LOCK_MATCH` can be produced from non-canonical historical binding path:
   - composed stamp can show `identity_id=base-repo-architect; lock=LOCK_MATCH` while canonical session pointer is `base-repo-audit-expert-v3`.
4. tuple parity contract is still partial:
   - parity checks currently cover only six fields (`run_id_binding`, `report_selected_path`, `required_contract`, `failed_required_contract_count`, `send_time_gate_status`, `outlet_bypass_detected`), allowing tuple drift (`identity_id`, `actor_id`, `work_layer`, `source_layer`, `lock_state`) to pass.
5. bundle receipt projection remains under-constrained on strict surfaces:
   - `send_time_gate_status` can remain empty in compared receipts and still pass parity.

Mandatory protocol closure target (UCG wave-4, control-plane only):

1. `validate` / `three-plane` / `compose-governed-reply` must consume one shared tuple resolver (single function + same field schema + same priority).
2. all user-visible replies must pass one canonical egress gate; tuple mismatch on (`identity_id`, `actor_id`, `work_layer`, `source_layer`, `lock_state`) must fail-close (`FAIL_REQUIRED`) with no non-blocking downgrade.
3. entry gate must freeze `run_id + tuple`; egress and strict validators must consume frozen tuple only (no late fallback re-resolution).
4. CI must enforce same-run tuple full equality between `validate` and `three-plane` receipts.
5. parity contract must include full HUD tuple and require non-empty `send_time_gate_status` for strict operations.

Acceptance commands (round-19 auditor replay):

1. `python3 scripts/resolve_identity_context.py resolve --identity-id base-repo-architect --repo-catalog identity/catalog/identities.yaml --local-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
2. `python3 scripts/render_identity_response_stamp.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --identity-id base-repo-architect --view external --disclosure-level standard --work-layer protocol --source-layer project --json-only`
3. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --scope USER --actor-id assistant:codex --baseline-policy warn --expected-work-layer protocol --expected-source-layer project`
4. `python3 scripts/validate_required_gate_tuple_parity.py --receipt /tmp/tuple_parity_gap_a_r2.json --receipt /tmp/tuple_parity_gap_b_r2.json --min-receipts 2 --require-distinct-operations --json-only`

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`; unified control entrypoint is landed but tuple-source convergence is not yet closed.
2. this round confirms recurrence root cause as control-plane contract incompleteness, not business-domain behavior.
3. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.39 Round-20 multi-instance protocol-boundary audit (`HEAD=6af084f+dirty`, 2026-03-08)

Scope lock:

1. this round absorbs two fresh runtime feedback batches (`custom-creative-ecom-analyst`, `office-ops-expert`) with protocol-layer-only triage.
2. this is evidence-boundary reinforcement only; no instance business payload is ingested into protocol governance.
3. lifecycle boundary remains non-promotional (`SPEC_READY / PENDING_INTAKE`).

Four-track replay evidence (`T1..T4`):

1. custom-creative protocol-lane replay:
   - `/tmp/cca_validate_accept_posthead_20260308.log`
   - `/tmp/cca_full_scan_accept_posthead_20260308.json`
   - `/tmp/cca_three_plane_accept_posthead_20260308.json`
2. custom-creative upgrade/heal execution traces (boundary classification only):
   - `/tmp/cca_update_instance_after_protocol_fix_20260308.log`
   - `/tmp/cca_update_instance_review_required_20260308.log`
   - `/tmp/cca_update_instance_review_required_rerun_20260308.log`
   - `/tmp/cca_heal_apply_20260308.log`
3. office post-fix replay:
   - `/tmp/three_plane_office_postfix_1772901986.json`
   - `/Users/yangxi/.codex/.identity/instances-canonical/office-ops-expert/runtime/reports/identity-upgrade-exec-office-ops-expert-1772901986.json`
4. office runtime summary handoff:
   - `/Users/yangxi/claude/codex_project/ddm/docs/governance/office-ops-instance-upgrade-and-live-regression-2026-03-08.md`

Round-20 confirmed protocol-layer residuals:

1. `custom-creative-ecom-analyst` validate lane still reproduces `IP-ASB-STAMP-SESSION-001` with first-line tuple mismatch (`expected protocol/env`, observed `instance/project`), showing unresolved tuple-source convergence on strict entry chain.
2. `required_gate_bundle_runner` failure in this batch is fail-close by design (`IP-GATE-ENTRY-001`) and is driven by one required row `skill_path_integrity -> IP-SPATH-002`, not by `SKIPPED_NOT_REQUIRED` rows.
3. current bundle semantics remain consistent with round-17/18 hardening:
   - history-only `required_contract=true` rows can emit `SKIPPED_NOT_REQUIRED` without automatic bundle failure;
   - bundle failure is tied to required row hard fail (`FAIL_REQUIRED`) and row contract errors.

Round-20 boundary segregation (protocol vs instance):

1. protocol-owned closure:
   - stamp/tuple consistency residual (`IP-ASB-STAMP-SESSION-001`) stays in `HOTFIX16-P0-007` control-plane wave-4 scope.
2. instance-owned closure (recorded, not promoted into protocol fix queue):
   - out-of-layout skill path (`IP-SPATH-002`) and local safe-auto/heal path policy blocks (`blocked_by_safe_auto_path_policy`, `IP-HEAL-003`).
3. non-regression signal:
   - office replay shows `instance_plane_status=CLOSED` while `repo/release` remain blocked; this does not indicate new protocol entrypoint regression.

Mandatory protocol closure carry-forward:

1. keep wave-4 requirements from `8.38` unchanged:
   - shared tuple resolver,
   - canonical egress strict fail-close,
   - entry freeze (`run_id + tuple`) with frozen tuple consumption,
   - CI same-run full tuple equality.
2. add boundary guardrail:
   - protocol backlog intake must reject instance-only path policy findings unless accompanied by protocol tuple/egress evidence.

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`.
2. this round reduces false routing of instance blockers into protocol remediation queue.
3. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.40 Round-21 headstamp multibinding + parser convergence replay (`HEAD=13aa0b0+dirty`, 2026-03-08)

Scope lock:

1. protocol-layer-only hotfix closure for recurring replay false blockers under `HOTFIX16-P0-007`.
2. this round lands code + governance/review synchronization; no instance business logic mutation is introduced.
3. lifecycle boundary remains non-promotional (`SPEC_READY / PENDING_INTAKE`).

Round-21 landed protocol deltas:

1. `scripts/validate_reply_identity_context_first_line.py`:
   - restored deterministic reply evidence parsing across `.jsonl/.json/.txt` payloads.
   - removed misplaced unreachable parser block that could suppress non-jsonl first-line extraction.
2. `scripts/validate_headstamp_recurrence_closure.py`:
   - actor-mismatch negative probe now recognizes `actor_id+session_id` multibinding without explicit session selector as `SKIPPED_INCONCLUSIVE_MULTIBINDING`.
   - avoids false fail-close escalation (`IP-ASB-STAMP-SCAN-007`) for catalogs where one actor legitimately binds multiple identities across session entries.

Replay evidence (protocol-layer):

1. direct recurrence replay:
   - `python3 scripts/validate_headstamp_recurrence_closure.py --catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --identity-id system-requirements-analyst --operation scan --actor-id user:yangxi --json-only`
   - receipt: `/tmp/headstamp_sra_scan_useryangxi_after.json` (`headstamp_recurrence_closure_status=PASS_REQUIRED`).
2. full-scan target replay:
   - `python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids system-requirements-analyst --global-catalog /Users/yangxi/.codex/.identity/catalog.local.yaml --actor-id user:yangxi --out /tmp/full_scan_sra_round19_after.json`
   - summary: `p0=0`, `ok=1`.
3. command gates:
   - `python3 -m py_compile scripts/validate_reply_identity_context_first_line.py scripts/validate_headstamp_recurrence_closure.py`
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

State impact:

1. residual `IP-SEM-001/IP-UPG-002` replay blockers are no longer reproduced in the SRA target full-scan path used for this round (`p0=0` in replay artifact above).
2. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE` until independent auditor replay signs off on latest head.
3. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

### 8.41 Round-22 UCG minimal control-plane decision freeze (`HEAD=13aa0b0+dirty`, 2026-03-08)

Decision priority:

1. this section is normative and supersedes design-branch complexity in `8.38/8.39/8.40`.
2. previous rounds remain as replay evidence only; implementation must follow this minimal model.

Final protocol control shape (authoritative):

1. strict source-layer model is fixed to two values only:
   - `source_layer ∈ {project, global}`.
2. scope is the separate actor-intent axis:
   - `scope ∈ {REPO, USER, ADMIN, SYSTEM}`.
3. non-layer tokens are demoted to migration metadata and are non-gating:
   - `catalog_origin_layer ∈ {LOCAL, REPO}`,
   - `resolution_mode ∈ {EXPLICIT, ENV, AUTO}`,
   - legacy source tokens do not participate in strict gate verdicts.
4. single entry freeze tuple (computed once, immutable in-run):
   - `actor_id`, `identity_id`, `work_layer`, `source_layer`, `scope`, `lock_state`, `run_id`, `session_id`.
5. single canonical egress gate:
   - user-visible reply must compare against frozen tuple;
   - any mismatch is `FAIL_REQUIRED`;
   - `WARN_NON_BLOCKING` cannot bypass egress for strict operations.
6. CI hard assertions are reduced to four only:
   - same-run full tuple equality (`validate` vs `three-plane`);
   - `send_time_gate_status` is non-empty on strict surfaces;
   - illegal `source_layer` token is fail-close;
   - missing explicit `--actor-id` on strict chain is fail-close.

Protocol/instance boundary (hard):

1. protocol backlog only accepts tuple/entry/egress control-plane defects.
2. instance runtime/path policy defects (for example `IP-SPATH-*`, local safe-auto/heal policy) stay in instance backlog and are not promoted into protocol hotfix scope.

Acceptance commands (decision-freeze verification):

1. `python3 scripts/docs_command_contract_check.py`
2. `python3 scripts/validate_protocol_ssot_source.py`
3. `python3 scripts/validate_required_gate_tuple_parity.py --receipt <validate_receipt> --receipt <three_plane_receipt> --min-receipts 2 --require-distinct-operations --json-only`
4. `python3 scripts/validate_send_time_reply_gate.py ... --operation three-plane --json-only` (must emit non-empty `send_time_gate_status`)

State impact:

1. `HOTFIX16-P0-007` remains `SPEC_READY / PENDING_INTAKE`.
2. control-plane governance is now intentionally minimal to prevent recurring branch drift.
3. lifecycle boundary unchanged: `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`.

## 8.41 Round-23 Canonical Path Two-Layer Cutover (protocol-only, migration-owned by instances)

Decision freeze (normative):

1. Runtime physical layout is reduced to exactly two canonical roots:
   - project: `<project>/.identity/<identity_id>/`
   - global: `${CODEX_HOME:-~/.codex}/.identity/<identity_id>/`
2. Canonical tuple (strict gate input/output) is frozen to:
   - `catalog_path`
   - `resolved_pack_path`
   - `runtime_root` (must be under `<resolved_pack_path>/runtime`)
3. `source_layer` strict semantics are reduced to `project|global`.
4. Legacy tags (`local/repo/env/auto`) are migration metadata only and are non-authoritative for strict verdicts.
5. Strict lane forbids implicit path fallback (including `/tmp` runtime fallback).
6. Legacy runtime paths are recognized only for migration diagnosis; after migration window, legacy hits are fail-close.

Protocol/instance responsibility split:

1. Protocol layer: identify / validate / reject only.
2. Instance layer: migration / debt cleanup / receipt backfill.

Implementation checkpoint (this round, protocol base repo):

1. Runtime selector defaults switched to `.identity` for both project/global mode.
2. Resolver defaults + scope inference switched to canonical `.identity` roots.
3. Runtime mode guard upgraded to strict `project|global` mode recognition and tuple checks.
4. Pack-path canonical validator tightened to canonical roots (fixture exceptions remain explicit).
5. Full-scan defaults switched to `.identity` catalogs (`project` + `${CODEX_HOME}/.identity`).

Acceptance commands:

1. `python3 -m py_compile scripts/resolve_identity_context.py scripts/validate_identity_runtime_mode_guard.py scripts/full_identity_protocol_scan.py`
2. `bash -n scripts/identity_runtime_select.sh scripts/use_project_identity_runtime.sh scripts/use_local_identity_env.sh`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_protocol_ssot_source.py`

State boundary:

1. This section is protocol-layer hardening only (non-promotional by itself).
2. Promotion still requires independent replay closure on migrated instance packs.


## 8.42 Round-24 Two-Layer Canonical Hard-Fail Closure (2026-03-08)

### Decision Freeze (Narrowed Model)

本轮冻结为最小稳定模型，不再扩展层级语义：

1. canonical `source_layer` 仅允许 `project` / `global` 进入 strict 判定。
2. protocol 层职责仅为 `识别` / `校验` / `拒绝`，不承担历史兼容兜底迁移。
3. instance 层职责为路径迁移、历史清债、报告回填；未迁移实例可被 protocol 严格拒绝。

### Canonical Path Contract

1. project 模式：`<project>/.identity/<identity_id>/`
2. global 模式：`${CODEX_HOME:-~/.codex}/.identity/<identity_id>/`
3. 非 canonical 路径（如 `.agents/identity`、legacy global root without `.identity`）在 strict operation 中必须 fail-close。

### Mandatory Controls (Round-24)

1. Source-Domain Determinism
   - `render/compose/first-line/send-time/coherence` 的 `source_layer` 必须来自同一 resolver 结果。
   - 禁止将 non-canonical catalog 通过 fallback 渲染为 `project/global` 的语义洗白。

2. Strict Surface Unified Preflight
   - 以下 strict surface 统一前置 `validate_identity_runtime_mode_guard`，guard 未通过不得继续执行后续 validator：
     - `identity_creator`
     - `report_three_plane_status`
     - `full_identity_protocol_scan`
     - `release_readiness_check`
     - `e2e_smoke_test.sh`

3. Expected Layer End-to-End Pass-through
   - `expected_work_layer/expected_source_layer` 必须从入口透传到 `render_identity_response_stamp` 与后续 strict reply gates。
   - 禁止同一 run 内出现 `expected=protocol` 但 render 输出 `instance` 的链路分叉。

4. No Compatibility Fallback in Protocol Lane
   - protocol lane 对 legacy source tokens 与 legacy runtime path 仅可标记为 migration metadata，不可作为 strict 判定真值来源。

### Round-24 Implementation Closure (protocol base repo)

1. strict requiredization/sanitization/routing 家族 validators 已从 `default_source_layer="auto"` 收敛到 `project`：
   - `scripts/validate_protocol_vendor_semantic_isolation.py`
   - `scripts/validate_protocol_data_sanitization_boundary.py`
   - `scripts/validate_semantic_routing_guard.py`
   - `scripts/validate_external_source_trust_chain.py`
   - `scripts/validate_vendor_namespace_separation.py`
   - `scripts/validate_required_contract_coverage.py`
   - `scripts/validate_protocol_feedback_sidecar_contract.py`
   - `scripts/validate_prompt_kernel_executable_coupling.py`
2. three-plane / full-scan 增补 runtime mode guard 预检，guard 失败即停止该 strict 链路执行。
3. `render_identity_response_stamp` 与 strict reply 链路完成 `expected_work_layer/expected_source_layer` 透传收口。
4. response stamp 与 structured context 不再把 non-canonical source 自动降级渲染为 `project`。

### Replay Acceptance (Protocol Layer Only)

以下条件全部满足才可标记本节闭环：

1. legacy catalog 输入在 strict surface 统一前置被拒绝（同一错误族、同一 fail-close 行为）。
2. non-canonical catalog 不再在头显中渲染为 `source_layer=project/global`。
3. validate/three-plane/full-scan 在同 run 上的 layer tuple 一致（至少包含 `work_layer`、`source_layer`）。
4. 状态边界保持：`SPEC_READY / PENDING_INTAKE`，`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### Scan & Replay Evidence

1. `/tmp/v16_round24_full_repo_scan_20260308.json`
2. `/tmp/v16_round24_full_repo_scan_20260308.md`
3. raw census: `total_hits=1415`（legacy tokens 主要来自 `identity/runtime/**` 历史证据归档）。
4. strict-normative closure: `non_compat_normative_hits=0`（`scripts/** + identity/protocol/** + README.md`）。

### Acceptance Commands

1. `rg -n 'default_source_layer="auto"|source_layer or "auto"|--source-layer.*default="auto"' scripts identity README.md`
2. `python3 -m py_compile scripts/response_stamp_common.py scripts/render_identity_response_stamp.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py scripts/release_readiness_check.py scripts/validate_reply_identity_context_first_line.py scripts/validate_execution_reply_identity_coherence.py scripts/validate_protocol_vendor_semantic_isolation.py scripts/validate_protocol_data_sanitization_boundary.py scripts/validate_semantic_routing_guard.py scripts/validate_external_source_trust_chain.py scripts/validate_vendor_namespace_separation.py scripts/validate_required_contract_coverage.py scripts/validate_protocol_feedback_sidecar_contract.py scripts/validate_prompt_kernel_executable_coupling.py`
3. `bash -n scripts/e2e_smoke_test.sh`
4. `python3 scripts/docs_command_contract_check.py`
5. `python3 scripts/validate_protocol_ssot_source.py`

### State impact

1. 本节为 protocol 控制面收口，仍为 non-promotional。
2. `HOTFIX16-P0-007` 状态维持 `SPEC_READY / PENDING_INTAKE`。
3. instance 迁移债务继续由实例层承担；协议层保持识别/校验/拒绝边界。


## 8.43 Round-26 Uncovered Scope Deep-Scan Closure (2026-03-08)

### Scope Clarification

1. Round-24 扫描范围是 `scripts/** + identity/** + README.md`，并非全仓闭环。
2. 本轮新增目标是对 Round-24 未覆盖目录做机器分层，明确哪些必须进入 strict 治理闭环，哪些属于归档/元数据面。

### Uncovered Root Classification (machine-audited)

1. must-close-now（执行面）：
   - `.github/**`
2. should-close-this-wave（规范面）：
   - `docs/**`
   - `skills/**`
   - `CHANGELOG.md`
   - `VERSIONING.md`
3. archive-or-meta（非 strict 规范面）：
   - `.codex/**`
   - `.identity-protocol/**`
   - `.tmp-fixtures/**`
   - `.gitignore`
   - `requirements-dev.txt`

### P0 Residual Found in Uncovered Execution Surface

1. CI strict HUD 链路存在显式 actor 透传缺口：
   - `.github/workflows/_identity-required-gates.yml:218`
   - `.github/workflows/_identity-required-gates.yml:221`
   - `.github/workflows/_identity-required-gates.yml:227`
2. 上述三处仍未显式传递 actor 参数，会触发 actor fallback 链。
3. fallback 来源仍可落到环境 actor：
   - `scripts/actor_session_common.py:17`
   - `scripts/actor_session_common.py:25`
4. 这类缺口不被当前 drift 检查器捕获（现有 drift 只校验接线，不校验关键参数一致性）：
   - `scripts/validate_required_gate_surface_drift.py:156`
   - `scripts/validate_required_gate_surface_drift.py:167`

### Governance Strengthening (Round-26 Freeze)

1. Round-26 起将 `.github/**` 纳入 required scan scope（执行面不再允许遗漏）。
2. strict HUD egress 链新增参数合同：render/first-line/coherence 在 CI 路径必须显式使用同一 actor tuple。
3. drift guard 从“接线存在性”扩展到“关键参数合同一致性”。
4. `docs/**` 与 `skills/**` 进入“规范面扫描”，但与 `.codex/**`、`.identity-protocol/**` 的归档面隔离审计，避免历史证据噪声污染 strict 结论。

### Round-26 Evidence

1. `/tmp/v16_round26_uncovered_scope_audit_20260308.json`
2. `/tmp/v16_round26_uncovered_scope_audit_20260308.md`
3. `python3 scripts/validate_required_gate_surface_drift.py --json-only`（当前返回 PASS，不代表参数合同已闭环）
4. `python3 scripts/docs_command_contract_check.py`（PASS）
5. `python3 scripts/validate_protocol_ssot_source.py`（OK）

### State Boundary

1. 本节为协议层治理补强，不涉及实例业务能力提级。
2. `HOTFIX16-P0-007` 继续保持 `SPEC_READY / PENDING_INTAKE`。
3. `ACCEPT_WITH_FIX != READY_FOR_PROMOTION` 约束不变。

### 8.44 Round-26.1 Execution-Surface Parameter Contract Closure (2026-03-08)

#### Closure scope (code + runtime migration)

1. strict HUD 链路 actor 参数透传已收口到执行面：
   - `.github/workflows/_identity-required-gates.yml` 的 render / first-line / send-time / coherence 均显式 `--actor-id`.
   - `scripts/e2e_smoke_test.sh` 对同链路命令补齐显式 `--actor-id`.
   - `scripts/report_three_plane_status.py`、`scripts/full_identity_protocol_scan.py`、`scripts/release_readiness_check.py`、`scripts/identity_creator.py` 同步补齐并保留 fail-close。
2. drift 守卫升级为“接线 + 参数合同”双重校验：
   - `scripts/validate_required_gate_surface_drift.py` 新增 actor 参数合同检查；若 strict surface 命中目标脚本但缺失 `--actor-id`，返回 `IP-GATE-ENTRY-003`.
3. project runtime 迁移残余收口：
   - `.identity/*/CURRENT_TASK.json`、`.identity/session/*`、`.identity/config/runtime-paths.env`、`.identity/*/runtime/{state,metrics}` 完成 `.agents/identity -> .identity` 收口；
   - canonical triplet 保持 project/global 双层模型，不新增兼容层。

#### Round-26.1 replay anchors

1. `python3 scripts/validate_required_gate_surface_drift.py --json-only` → `PASS_REQUIRED`（`actor_id_passthrough_missing={}`）
2. `python3 scripts/docs_command_contract_check.py` → `PASS`
3. `python3 scripts/validate_protocol_ssot_source.py` → `OK`
4. `python3 scripts/resolve_identity_context.py resolve --identity-id base-repo-audit-expert-v3 --local-catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml` → source/canonical tuple anchored on project `.identity`.

#### Decision boundary

1. Round-26.1 完成“执行面参数合同缺口”修复，属于 HOTFIX16-P0-007 下的 required closure 子项。
2. Promotion posture 不变：继续 `SPEC_READY / PENDING_INTAKE`，等待审计回放矩阵统一签收后再提级。

### 8.45 Round-26.2 Base-Repo-Architect self-run full-chain closure replay (2026-03-08)

#### Code closures landed in this round

1. `collect_identity_health_report` strict-operation 参数注入收口：
   - `scripts/collect_identity_health_report.py` 增加 `OPERATION_AWARE_CHECKS`，只对支持 `--operation` 的校验器透传，消除 `argparse` 预检崩溃。
2. release-readiness capability gate 语义收口：
   - `scripts/release_readiness_check.py` 为 `collect_identity_health_report` 显式透传 `--actor-id`；
   - `validate_identity_capability_activation` 终态校验改为基于 catalog + activation policy 的实时判定，避免旧 report `BLOCKED` 状态导致假阻断。
3. e2e strict chain actor 透传与时序收口：
   - `scripts/e2e_smoke_test.sh` 所有 `collect_identity_health_report` 调用显式 `--actor-id`；
   - capability arbitration 前新增 route metrics 刷新，避免 `metrics/threshold linkage` 因陈旧指标误阻断。
4. handoff/export 运行面路径收口：
   - `scripts/validate_agent_handoff_contract.py` 的 self-test sample 路径新增 `identity/runtime/**` 候选映射；
   - `scripts/export_route_quality_metrics.py` 支持 pack-root `runtime/**` handoff log 映射，并允许 project canonical `.identity/**` 输出（不再误判为 repo 污染路径）。
5. update fail-fast evidence completeness 收口：
   - `scripts/execute_identity_upgrade.py` 在 pre-mutation/lane-routing 早退分支也强制落盘 `<run_id>-patch-plan.json`，消除 `validate_identity_self_upgrade_enforcement` 对应的 patch-plan 缺失阻断。

#### Runtime evidence backfill (base-repo-architect, project mode)

1. `runtime/examples/base-repo-architect-trigger-regression-sample.json`
2. `runtime/logs/collaboration/base-repo-architect-20260308T041046Z.json`
3. `runtime/logs/handoff/base-repo-architect-20260308T041623Z.json`
4. `runtime/examples/base-repo-architect-knowledge-acquisition-sample.json`
5. `runtime/rulebooks/{positive,negative}.jsonl`
6. `runtime/examples/base-repo-architect-experience-feedback-sample.json`

#### Replay matrix (self-run, actor-bound)

1. `resolve_context` PASS
2. `docs_command_contract_check` PASS
3. `validate_protocol_ssot_source` OK
4. `validate_required_gate_surface_drift --json-only` PASS_REQUIRED
5. `identity_creator.py validate` PASS
6. `report_three_plane_status.py` PASS
7. `full_identity_protocol_scan.py --scan-mode target` PASS
8. `release_readiness_check.py` PASS
9. `e2e_smoke_test.sh` PASS（protocol lane, project source-layer, actor=`assistant:codex`）

Machine report artifacts:

1. `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-20260308T045542Z.json`
2. `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-20260308T045542Z.md`

#### State boundary

1. 本轮完成的是“代码执行面 + 实例回放证据”闭环，不改变 v1.6 审计生命周期边界。
2. 提级口径保持不变：`SPEC_READY / PENDING_INTAKE`，待审计专家按同命令回放签收后推进状态。

### 8.46 Round-26.3 Expected-layer pass-through closure for validate chain (2026-03-08)

#### Problem replay (strict expected layer mismatch)

1. 在 `identity_creator.py validate` 显式传入 `--expected-work-layer protocol --expected-source-layer project` 时，
   strict first-line gate 可出现 `reply_first_line_work_layer=instance`，导致 `IP-ASB-STAMP-SESSION-001`。
2. 根因是 validate 链只把 expected tuple 传给后续 validators，没有把同一 tuple 传入 stamp renderer，
   使 render 与 validator 判定源分叉。

#### Code closure

1. `scripts/identity_creator.py` validate 链补齐 renderer 透传：
   - 当存在 `expected_work_layer` 时，`render_identity_response_stamp.py` 显式追加 `--work-layer`.
   - 当存在 `expected_source_layer` 时，`render_identity_response_stamp.py` 显式追加 `--source-layer`.
2. 收口后，render/first-line/send-time/coherence 共享同一 expected tuple 输入，消除“validator strict、renderer fallback”分叉。

#### Replay evidence

1. `source ../scripts/use_local_identity_env.sh`
2. `python3 scripts/identity_creator.py validate --identity-id base-repo-architect --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --actor-id assistant:codex --expected-work-layer protocol --expected-source-layer project --layer-intent-text 'protocol full validation replay'`
3. replay output: `/tmp/base_repo_architect_identity_validate_now.log`（`rc=0`）。
4. cross-surface sanity:
   - `/tmp/base_repo_architect_three_plane_now.log`（`rc=0`）
   - `/tmp/base_repo_architect_full_scan_now.log`（`rc=0`）
5. machine report:
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-round26_3-20260308T051524Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-self-run-round26_3-20260308T051524Z.md`

#### Boundary

1. 本节属于 UCG 参数合同补完，不新增模型层级，不改变 project/global 双层 canonical 约束。
2. 状态边界维持：`SPEC_READY / PENDING_INTAKE`，继续等待独立审计回放签收。

### 8.47 Round-26.4 HUD tuple hardening + actor strict-entry closure (2026-03-08)

#### Closure scope (protocol control-plane only)

1. tuple parity 从“最小 6 字段”升级为 HUD 核心 tuple 合同：
   - `scripts/validate_required_gate_tuple_parity.py` 新增 core/conditional 字段组与别名解析；
   - 核心字段新增 `identity_id`，条件字段新增 `actor_id`、`resolved_work_layer`、`resolved_source_layer`、`lock_state`；
   - 当条件字段在任一 receipt 出现时，要求跨 receipt 全等，否则 `FAIL_REQUIRED`.
2. governed-reply 入口升级为显式 actor 必填：
   - `scripts/compose_and_validate_governed_reply.py` 在缺失 `--actor-id` 时 fail-close (`IP-ACTOR-ENTRY-001`)，禁止脚本内隐式 actor 回退进入 strict send-time path。
3. source-layer 推断修正：
   - `scripts/identity_creator.py` 的 `_infer_source_domain_from_catalog` 调整匹配顺序，优先识别 `/.codex/.identity/` 为 `global`，避免被 `/.identity/` 前缀误判为 `project`.
4. strict bundle runner 参数合同补齐：
   - `scripts/required_gate_bundle_runner.py` 增加 `actor_id/resolved_work_layer/resolved_source_layer/lock_state` 载荷字段与 `--outlet-bypass-detected true|false` 显式布尔解析；
   - strict surface 调用补齐 `--run-id/--send-time-gate-status/--outlet-bypass-detected` 参数（`report_three_plane_status/full_identity_protocol_scan/identity_creator/release_readiness_check/e2e/_identity-required-gates.yml`）。
5. three-plane/full-scan 可观测性补齐：
   - parity 投影新增 `operations_checked/duplicate_operations/require_distinct_operations`；
   - sidecar 投影新增 `requiredization_scope_reason/activity_correlation_status` 等关键字段，避免“raw 有值、summary 丢失”。
   - full-scan `required_gate_bundle_runner(_shadow)` 投影补齐 HUD tuple 关键字段（`actor_id/resolved_work_layer/resolved_source_layer/lock_state`），避免 audit 侧出现“bundle raw 有值但 summary 丢失”的观测断层。
6. drift guard 参数合同补齐：
   - `scripts/validate_required_gate_surface_drift.py` 新增 bundle-runner 关键参数合同检查（`run-id/send-time-gate-status/outlet-bypass/actor/work/source/lock`）；
   - strict surface 任一 bundle 调用缺参即 `FAIL_REQUIRED` (`IP-GATE-ENTRY-004`)。
7. target probe 入口收口：
   - `scripts/required_gate_bundle_runner.py` 对 `--target-name` 场景同样强制 `run_id`；
   - 禁止 “target probe 无 run_id 仍 PASS” 的旁路（无 run_id -> `IP-GATE-ENTRY-001`）。
8. sidecar 可观测升级（非阻断）：
   - `scripts/validate_protocol_feedback_sidecar_contract.py` 在 `ACTIVITY_UNSCOPED` + history-only 场景下由 `SKIPPED_NOT_REQUIRED` 升级为 `WARN_NON_BLOCKING` + `IP-SID-004`；
   - 新增 `activity_unscoped_count / observability_alert_level / observability_escalation_required`，用于稳定告警而非直接 release 阻断。
9. target full-scan 统计收口：
   - `scripts/full_identity_protocol_scan.py` 新增 `summary_unique_targets`，按 identity 去重输出 P0/P1/OK 计数，避免 project/global 双层行统计导致误判膨胀。

#### Replay anchors

1. parity 负向探针（核心 tuple 漂移应 fail-close）：
   - `python3 scripts/validate_required_gate_tuple_parity.py --receipt /tmp/tuple_gap_a_roundtable.json --receipt /tmp/tuple_gap_b_roundtable.json --min-receipts 2 --require-distinct-operations --json-only`
   - evidence: `/tmp/tuple_gap_roundtable_recheck_20260308.json`（`FAIL_REQUIRED`）。
2. compose 无 actor 探针（应 fail-close）：
   - evidence: `/tmp/compose_probe_no_actor_roundtable_custom_recheck.json`（`IP-ACTOR-ENTRY-001`）。
3. source 推断探针：
   - evidence: `/tmp/source_infer_recheck_20260308.log`（`global`）。
4. projection 探针：
   - evidence: `/tmp/three_plane_projection_recheck_20260308.json`（parity/sidecar 关键字段可见）。
   - evidence: `/tmp/full_scan_projection_recheck2_20260308.json`（full-scan checks 投影可见 bundle HUD tuple 字段与 parity/sidecar 扩展字段）。
5. bundle 参数合同静态复核：
   - evidence: `/tmp/audit_recheck_bundle_args_20260308.json`（missing `run-id/send-time/outlet` = `0/0/0`）。
   - evidence: `/tmp/audit_recheck_bundle_args_surface_20260308.json`（strict six surfaces bundle 参数合同缺口全零，含 actor/work/source/lock 透传）。
   - evidence: `/tmp/surface_drift_recheck6_20260308.json`（drift gate 已内建参数合同校验且回放 `PASS_REQUIRED`）。
6. target probe run-id 收口探针：
   - evidence: `/tmp/target_probe_no_runid_recheck4_20260308.json`（`FAIL_REQUIRED` + `IP-GATE-ENTRY-001`）。
7. sidecar 非阻断可观测升级探针：
   - evidence: `/tmp/three_plane_sidecar_recheck8_20260308.json`（`sidecar_contract_status=WARN_NON_BLOCKING`，`sidecar_error_code=IP-SID-004`，`observability_alert_level=L1`）。
8. full-scan target 去重统计探针：
   - evidence: `/tmp/full_scan_target3_recheck8_20260308.json`（新增 `summary_unique_targets`）。
9. gate 复检：
   - evidence: `/tmp/surface_drift_recheck9_20260308.json`（`PASS_REQUIRED`）；
   - evidence: `/tmp/docs_contract_recheck9_20260308.log`（PASS）；
   - evidence: `/tmp/ssot_recheck9_20260308.log`（OK）。
6. round report:
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

#### Boundary

1. 本节仅收口协议控制面，实例历史债务（如 session_refresh/writeback）仍按实例层清债链路处理。
2. 状态边界维持：`SPEC_READY / PENDING_INTAKE`，`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.48 Round-26.5 Lane-lock deterministic pass-through closure (2026-03-08)

#### Closure scope (protocol control-plane only)

1. 本节仅处理“lane-lock 已存在但执行面仍 default fallback 到 instance”的控制面残口，不扩展实例业务逻辑。
2. 目标是让 `full_scan` 与 `three_plane` 在“无显式 expected tuple”情况下仍使用同一 deterministic tuple 来源，避免 `IP-LAYER-GATE-006` 反复出现。

#### Code closure

1. `scripts/full_identity_protocol_scan.py`
   - 新增 per-identity `effective_expected_work_layer/effective_expected_source_layer` 计算；
   - 当无显式 `--expected-work-layer` 且检测到 protocol lane lock 时，自动将 `effective_expected_work_layer=protocol`；
   - `work_layer_gate_set_routing`、`required_gate_bundle_runner(_shadow)` 与 `three_plane` 调用统一消费 effective tuple；
   - scan output 显式投影 `effective_expected_*` 与 `detected_session_lane_lock`，用于审计复放。
2. `scripts/report_three_plane_status.py`
   - `_instance_plane_status` 新增 lane-lock 感知逻辑（actor binding + lane lock receipts）；
   - 在未显式传入 expected tuple 时，按 `resolved source_layer + lane lock` 生成 effective tuple 并贯穿 render/first-line/layer-intent/send-time/coherence/lane-routing/bundle；
   - instance detail 新增 `effective_expected_work_layer/effective_expected_source_layer/detected_session_lane_lock`。

#### Replay evidence

1. full-scan lane closure replay:
   - `/tmp/full_scan_projection_recheck3_20260308.json`
   - 关键结果：`work_layer_gate_set_routing_status=PASS_REQUIRED`，`error_code=""`，`work_layer=protocol`，`session_lane_lock=protocol`（project layer）。
2. three-plane lane closure replay:
   - `/tmp/three_plane_sidecar_recheck11_20260308.json`
   - 关键结果：`instance_plane_detail.effective_expected_work_layer=protocol`，lane routing `PASS_REQUIRED`（不再 `IP-LAYER-GATE-006`）。
3. sidecar non-blocking observability continuity:
   - `/tmp/three_plane_sidecar_recheck11_20260308.json`
   - 关键结果：`sidecar_contract_status=WARN_NON_BLOCKING`，`sidecar_error_code=IP-SID-004`，`activity_correlation_status=ACTIVITY_UNSCOPED`，`observability_alert_level=L1`。
4. gate sanity:
   - `/tmp/surface_drift_recheck11_20260308.json`（`PASS_REQUIRED`）
   - `/tmp/docs_contract_recheck11_20260308.log`（PASS）
   - `/tmp/ssot_recheck11_20260308.log`（OK）
5. round report:
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_9-lane-pass-through-20260308T072635Z.json`
   - `.identity/base-repo-architect/runtime/reports/identity-protocol-round26_9-lane-pass-through-20260308T072635Z.md`

#### Boundary

1. 本节关闭的是 lane fallback 的协议控制面残口；实例层残余阻断（如 `IP-WRB-003`）仍按实例迁移/清债链路处理。
2. 基线状态仍非单 SHA clean replay（worktree 仍有并行改动）；本节维持 `SPEC_READY / PENDING_INTAKE`，不宣称 promotion 就绪。

### 8.49 Round-27 v1.6 auditable sweep and review-status promotion (2026-03-08)

#### Scope

1. 本轮仅做审计复放与文档状态更新，不改协议代码。
2. 审计目标是把“可机器复放且通过”的 v1.6 条目从 `PENDING_INTAKE` 提升到 `PASS_WITH_BLOCKERS`，并保持非提级边界。

#### Replayed anchors

1. docs/ssot baseline:
   - `/tmp/deepscan_docs_contract_refresh_20260308.log`（PASS）
   - `/tmp/deepscan_ssot_refresh_20260308.log`（OK）
2. strict UCG entrypoint contract:
   - `/tmp/deepscan_surface_drift_refresh_20260308.json`（`PASS_REQUIRED`）
   - `/tmp/deepscan_bundle_arg_contract_exec_only_20260308.json`（执行位点参数缺口为 0）
3. HUD tuple + actor strict-entry:
   - `/tmp/deepscan_tuple_probe_result2_20260308.json`（tuple 漂移 fail-close）
   - `/tmp/deepscan_compose_no_actor_probe_20260308.json`（缺 actor fail-close）
4. validate expected-layer pass-through:
   - `/tmp/round27_validate_bra_expected_layers_20260308.log`（`reply_first_line_status=PASS_REQUIRED`，`send_time_gate_status=PASS_REQUIRED`）
5. residual blocker anchors (non-control-plane):
   - `/tmp/deepscan_e2e_braudit_20260308.log`（`IP-ASB-RFS-004` + `IP-PBL-006`）
   - `/tmp/deepscan_three_plane_matrix_v3_20260308.json`（4/4 `Conditional Go`）
   - `/tmp/deepscan_required_coverage_matrix_20260308.json`
   - `/tmp/deepscan_project_global_overlap_yaml_v2_20260308.json`

#### Governance decision

1. 允许在 review ledger 中将以下条目审计状态提升为 `PASS_WITH_BLOCKERS`：
   - `FIX16-001`
   - `HOTFIX16-P0-005`
   - `HOTFIX16-P0-007`
   - `HOTFIX16-P1-009`
   - `HOTFIX16-P0-010`
2. 上述状态提升仅代表“对应协议控制面条目复放通过”，不代表 release 可放行。
3. v1.6 tag lock 条件不变：任一 `P0` requirement 未到 `DONE` 且审计未 `PASS`，`v1.6` 继续锁定。
4. 生命周期边界保持：`SPEC_READY / PENDING_INTAKE` 主边界不变，`ACCEPT_WITH_FIX != READY_FOR_PROMOTION` 不变。

### 8.50 Round-27.1 auditable-scope completion replay (2026-03-08)

#### Scope

1. 在 `8.49` 状态提升后，对 remaining auditable `PENDING_INTAKE` 条目做补充独立复跑（不改代码）。
2. 本轮目标是确认是否存在“遗漏可升状态”条目，并确保 review decision-log 全量对齐。

#### Replayed anchors

1. baseline sanity:
   - `/tmp/deepscan_docs_contract_refresh2_20260308.log`（PASS）
   - `/tmp/deepscan_ssot_refresh2_20260308.log`（OK）
   - `/tmp/deepscan_surface_drift_refresh2_20260308.json`（`PASS_REQUIRED`）
2. base-repo-architect independent full-chain replay:
   - `/tmp/round27_identity_creator_validate_bra_20260308.log`（`rc=1`）
   - `/tmp/round27_three_plane_bra_20260308.json`（`overall_release_decision=Conditional Go`）
   - `/tmp/round27_full_scan_bra_20260308.json`（`summary.p0=1, ok=0`）
   - `/tmp/round27_release_readiness_bra_20260308.log`（`rc=1`）
   - `/tmp/round27_e2e_bra_20260308.log`（`rc=2`）
3. persistent blocker evidence:
   - `post_execution_mandatory_status=FAIL_REQUIRED` / `error_code=IP-WRB-003` remains active in validate/readiness/scan lanes.

#### Governance decision

1. `8.49` 提升列表保持不变，本轮无新增 `PASS_WITH_BLOCKERS` 条目。
2. Review ledger 必须补齐 `HOTFIX16-P0-008` 的 decision-log 行；审计结论维持 `PENDING_INTAKE`。
3. `FIX16-037` 与 `HOTFIX16-P1-004` 本轮复放后仍不满足 promotion guard，保持 `PENDING_INTAKE`。
4. 生命周期边界不变：`SPEC_READY / PENDING_INTAKE`，`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。


### 8.49 Round-26.6 Two-layer source determinism + target-scan de-inflation closure (2026-03-08)

#### Closure scope (protocol control-plane only)

1. 关闭 `resolve_identity_context` 在 monorepo root 下将 project catalog 误判为 `source_layer=unknown` 的控制面残口。
2. 关闭 `full_scan --scan-mode target` 默认 project/global 双层并扫导致的 target severity 膨胀。
3. 关闭 sidecar 在“本轮无相关 key”场景下长期 `ACTIVITY_UNSCOPED` 噪声复发。
4. 对 `session_refresh` 增加“非变更 strict 操作”的 baseline-mode 容错，避免 `IP-PBL-006` 历史报告模式直接卡死 validate/readiness/e2e。

#### Code closure

1. `scripts/resolve_identity_context.py`
   - 新增基于 `repo_catalog` 的 project root 推断（`_project_identity_home_from_repo_catalog`）；
   - `source_layer` 与 scope 统一以 canonical project/global triplet 判定，不再受外层 git root 偏移影响。
2. `scripts/full_identity_protocol_scan.py`
   - 新增 `--target-source-layer {auto,project,global,both}`；
   - target mode 默认 `auto`：优先 `expected_source_layer`，其次 `IDENTITY_CATALOG` 绑定层，最后 fail-safe 到 `project`；
   - 输出新增 `target_source_layer_mode/target_source_layer_effective`，避免双层重叠 max-severity 膨胀。
3. `scripts/validate_protocol_feedback_sidecar_contract.py`
   - 新增 `--current-round-anchor-utc` 显式本轮锚点；
   - sidecar 活动采集新增 `activity_ignored_missing_correlation_key_refs` 观测字段。
4. `scripts/protocol_feedback_lane_common.py`
   - 在缺失 correlation keys 时不再把历史噪声计为 `ACTIVITY_UNSCOPED`；
   - 该类条目进入 ignored 集合，仅做观测，不触发 sidecar 噪声升级。
5. `scripts/report_three_plane_status.py` / `scripts/full_identity_protocol_scan.py`
   - sidecar 调用统一透传 `--current-round-anchor-utc`；
   - projection 补齐 `activity_ignored_missing_correlation_key_refs`。
6. `scripts/validate_identity_session_refresh_status.py`
   - 对 `validate/readiness/e2e`（非变更 strict 操作）且未显式 execution-report 的 `IP-PBL-005/006` 场景降级为 `WARN_NON_BLOCKING`；
   - `ci/update/activate/mutation` 仍维持 strict fail-close。

#### Replay anchors

1. source-layer determinism:
   - `/tmp/resolve_context_recheck_final_20260308.json`（`source_layer=project`）。
2. target scan de-inflation:
   - `/tmp/full_scan_recheck_final3_20260308.json`（`target_source_layer_effective=project`）。
3. sidecar unscoped closure:
   - `/tmp/three_plane_recheck_final2_20260308.json`（sidecar=`NO_ACTIVITY/SKIPPED_NOT_REQUIRED`）。
   - `/tmp/sidecar_recheck_final_braudit_20260308.json`（standalone replay 同口径）。
4. gate sanity:
   - `/tmp/surface_drift_recheck_final2_20260308.json`（`PASS_REQUIRED`）；
   - `/tmp/docs_contract_recheck_final3_20260308.log`（PASS）；
   - `/tmp/ssot_recheck_final3_20260308.log`（OK）。
5. e2e lane pass-through replay:
   - `/tmp/e2e_recheck_final2_20260308.log`（`work_layer_gate_set_routing_status=PASS_REQUIRED`，不再 `IP-LAYER-GATE-006`）。

#### Boundary

1. 本节仅收口协议控制面，不宣称实例历史债务（`IP-WRB-003/004` 等）已清零。
2. 状态边界维持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。


### 8.50 Round-26.7 Health self-upgrade playbook emission (2026-03-08)

#### Decision

1. 对“实例债务由实例自行迁移修复”的治理原则进行可执行化：健康检查报告必须输出可直接执行的升级回放命令链。
2. 协议层职责不变：仅识别/校验/拒绝；实例层按 playbook 自主完成 update + writeback + mandatory + alignment 修复闭环。

#### Code closure

1. `scripts/collect_identity_health_report.py` 新增 `self_upgrade_plan`：
   - `plan_status` (`NOT_REQUIRED` / `ACTION_REQUIRED`)；
   - `trigger_checks` + `trigger_error_codes`；
   - `upgrade_report_dir`；
   - `commands`（逐条可执行，覆盖 update / writeback / post_execution / alignment / re-health）。
2. 控制台输出新增 `[UPGRADE]` 段：
   - 当健康检查存在升级触发项时，直接打印完整命令链，供实例 owner 原地执行。

#### Replay anchors

1. `/tmp/health-upgrade-test/identity-health-base-repo-audit-expert-v3-1772958922.json`
   - 包含 `self_upgrade_plan.plan_status=ACTION_REQUIRED` 与完整 `commands`。
2. `/tmp/health-upgrade-test/identity-health-base-repo-audit-expert-v3-1772958922.json` 对应控制台回放：
   - `[UPGRADE] instance self-upgrade plan is required before next health pass.`
   - `$ python3 scripts/identity_creator.py update ...`
   - `$ python3 scripts/validate_writeback_continuity.py ...`
   - `$ python3 scripts/validate_post_execution_mandatory.py ...`
   - `$ python3 scripts/validate_identity_protocol_version_alignment.py ...`
   - `$ python3 scripts/collect_identity_health_report.py ... --enforce-pass`

#### Boundary

1. 本节只增加“实例自愈说明与执行链路输出”，不改变 strict gate fail-close 语义。


### 8.51 Round-28 Multi-Agent × Multi-Identity semantics closure (2026-03-08)

#### Roundtable decision (protocol control-plane)

1. 本节冻结多 agent × 多 identity 的唯一语义键：`(actor_id, session_id) -> identity_id`。
2. `switch_intent_receipt` 的强制触发条件从“actor 全局最新绑定”收口到“同 actor + 同 session 发生 identity 切换”。
3. 保留兼容闸门：`--switch-guard-scope actor_global` 可显式启用 legacy actor-wide 守卫（用于回放旧口径）。
4. 头显（HUD）控制面新增严格入口约束：`three-plane/full-scan` 禁止隐式 actor/session fallback，未显式 `--actor-id` 或 `--session-id` 一律 fail-close（`IP-ACTOR-ENTRY-001` / `IP-ASB-SESSION-ENTRY-001`）。

#### Code closure

1. `scripts/identity_creator.py`
   - activate 新增参数：
     - `--session-id`（默认 `run:<run_id>`）
     - `--switch-guard-scope {actor_session,actor_global}`（默认 `actor_session`）
   - switch 守卫改为按 guard scope 选择绑定源：
     - `actor_session`：仅检查同 actor+session 绑定；
     - `actor_global`：保持 legacy actor-wide 检查。
   - activation switch report 补齐观测字段：
     - `session_id` / `session_id_source`
     - `switch_guard_scope`
     - `switch_guard_binding_ref`
2. `scripts/report_three_plane_status.py`
   - `--actor-id` / `--session-id` 改为 strict 必填；缺失直接 fail-close。
3. `scripts/full_identity_protocol_scan.py`
   - `--actor-id` / `--session-id` 改为 strict 必填；缺失直接 fail-close。

#### Cross-verification replay (roundtable + vendor + reference)

1. Roundtable replay（同 actor 同 session 切换必须 receipt）：
   - `/tmp/round28_activate_alpha_seed.log`（session alpha 首次绑定 PASS）
   - `/tmp/round28_activate_alpha_no_receipt.log`（同 session 切换 -> `IP-ACT-SWITCH-001`）
   - `/tmp/round28_activate_alpha_with_receipt.log`（补 receipt 后 PASS）
2. Multi-session replay（同 actor 不同 session 并行绑定允许）：
   - `/tmp/round28_activate_beta_parallel.log`（session beta 并行绑定 PASS）
3. Legacy compatibility replay（actor_global 仍保持旧闸门）：
   - `/tmp/round28_activate_global_no_receipt.log`（跨 session 仍触发 `IP-ACT-SWITCH-001`）
4. HUD strict-entry replay：
   - `/tmp/round28_three_plane_no_actor.log`（`IP-ACTOR-ENTRY-001`）
   - `/tmp/round28_three_plane_no_session.log`（`IP-ASB-SESSION-ENTRY-001`）
   - `/tmp/round28_full_scan_no_actor.log`（`IP-ACTOR-ENTRY-001`）
   - `/tmp/round28_full_scan_no_session.log`（`IP-ASB-SESSION-ENTRY-001`）
   - `/tmp/round28_three_plane_with_actor.json`（explicit actor 可执行）
   - `/tmp/round28_full_scan_with_actor.json`（explicit actor 可执行）

#### Vendor/reference alignment verdict

1. MCP lifecycle（session/initialization 协商）与本节 `actor+session` 绑定键一致，不支持隐式跨会话真值漂移。
2. Codex 安全与审批模型（显式输入、集中控制面）与本节“strict actor entry + fail-close”一致。
3. Agent Skills 元数据/契约模型（显式输入输出、可测试触发）与本节“无 actor 不执行 strict surface”一致。

#### Boundary

1. 本节收口“语义键与 strict 入口”两类控制面缺口，不宣称实例历史债务（`IP-WRB-*`, prompt lifecycle）已清零。
2. 生命周期边界保持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.52 Round-28.1 Protocol tuple-parity optimization handoff (2026-03-08)

#### Decision (architect-facing)

1. 实例侧自修复已达可复放基线：
   - `identity_creator validate` 已 PASS（`/tmp/fixrun27_identity_validate.log`）。
   - `full_identity_protocol_scan --scan-mode target` 已 `p0=0`（`/tmp/fixrun25_full_scan_target.json`）。
2. 当前剩余主阻断已收敛到协议控制面：
   - `release_readiness_check` 与 `e2e_smoke_test.sh` 同步失败于 `IP-GATE-ENTRY-003`。
   - 失败根因为 tuple parity 将 `update/e2e` 与 `scan-probe` 两类 receipt 直接做 `required_contract` 全等比对，触发结构性误阻断。
3. 本节定义 v1.6 的协议优化执行单，仅用于指导架构师改协议，不回退到实例兼容兜底。

#### Cross-verified evidence

1. `release_readiness_check` 的 parity 阻断：
   - `/tmp/fixrun27_release_readiness.log`（`required_gate_tuple_parity_status=FAIL_REQUIRED`, `error_code=IP-GATE-ENTRY-003`）。
2. `e2e_smoke_test.sh` 的 parity 阻断：
   - `/tmp/fixrun28_e2e.log`（`required_gate_tuple_parity_status=FAIL_REQUIRED`, `error_code=IP-GATE-ENTRY-003`）。
3. mismatch 字段可复放：
   - 两条 receipt 操作分别为 `update/e2e` 与 `scan`，`mismatches.required_contract` 显式为 `true vs false`。
4. e2e 非阻断噪声：
   - `/tmp/fixrun28_e2e.log` 出现 `validate_cross_cwd_absolute_input` 的 `python -c` quoting `SyntaxError`，当前为 `SKIPPED_NOT_REQUIRED` 分支噪声，但会污染审计可读性。

#### Protocol optimization directives (must-do)

1. 在 `scripts/validate_required_gate_tuple_parity.py` 引入分层 tuple 合同：
   - `invariant_tuple`：跨 operation 必须全等（`run_id_binding`, `identity_id`, `actor_id`, `resolved_work_layer`, `resolved_source_layer`, `lock_state`）。
   - `operation_scoped_tuple`：仅同 operation 组内比较，不跨组全等（至少包含 `required_contract`）。
2. 对 `*_scan_probe` receipt 增加显式语义标记并写入 parity 判定上下文（建议字段：`parity_operation_scope=scan_probe`），禁止隐式按 baseline operation 推断。
3. `required_gate_bundle_runner.py` 与 parity 联动：
   - 若 receipt 标记 `operation=scan` 且 `surface_label` 以 `_scan_probe` 结尾，必须输出 `required_contract=false` 的显式原因字段；
   - parity 读取该原因后执行“可比性降阶”，而非直接 `FAIL_REQUIRED`。
4. `scripts/e2e_smoke_test.sh` / `scripts/validate_cross_cwd_absolute_input.py` 修复 `python -c` 引号构造，消除 `SyntaxError` 审计噪声。

#### Acceptance gates (architect replay checklist)

1. `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog <project>/.identity/catalog.local.yaml --actor-id assistant:codex --expected-work-layer protocol --expected-source-layer project`
   - 期望：RC=0；`required_gate_tuple_parity_status=PASS_REQUIRED`。
2. `IDENTITY_IDS=base-repo-audit-expert-v3 CATALOG_PATH=<project>/.identity/catalog.local.yaml ACTOR_ID=assistant:codex EXPECTED_WORK_LAYER=protocol EXPECTED_SOURCE_LAYER=project bash scripts/e2e_smoke_test.sh`
   - 期望：RC=0；无 `IP-GATE-ENTRY-003`；无 quoting `SyntaxError`。
3. 负向探针保留：
   - 构造 `invariant_tuple` 漂移（如 `actor_id` 不同）时，parity 必须继续 `FAIL_REQUIRED`。

#### Boundary

1. 本节仅定义协议控制面优化，不改变实例层“路径迁移/历史清债”的职责切分。
2. 生命周期边界保持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.53 Round-28.2 Headstamp recurrence de-dup closure statement (2026-03-08)

#### Decision (direct answer to recurring concern)

1. “头显丢失”在 v1.6 文档中已被反复记录，不是 17 个独立根因；当前应按去重口径治理，不再按轮次重复叙事。
2. 本轮 machine scan 统计显示：
   - v1.6 governance + review 中 headstamp/HUD/egress 相关命中共 `332` 条；
   - 相关章节标题共 `17` 条；
   - 高频错误码族集中在同一簇（`IP-ASB-STAMP-SESSION-005`, `IP-HDSTAMP-001/002/003`, `IP-ASB-STAMP-SCAN-004`）。
3. 结论：17 次修改形成的是“局部收口叠加”，但并未形成“最终输出口硬封闭”，因此会表现为复发。

#### Deduplicated root-cause set (frozen IDs)

1. `RC-HUD-001`（主根因，未闭环）：
   - 最终 user-visible emission 未被平台级强制绑定到 canonical egress（`compose -> send_time -> final emission`）。
2. `RC-HUD-002`（放大器）：
   - requiredization applicability drift，strict 场景出现 `SKIPPED_NOT_REQUIRED(contract_not_required)`。
3. `RC-HUD-003`（放大器）：
   - strict 链路 actor 参数透传不完整，触发 fallback actor 漂移。
4. `RC-HUD-004`（放大器）：
   - tuple/parser/source 分叉（render/first-line/coherence 输入不完全同构）。

#### Why 17 rounds still recur

1. 已落地修复主要覆盖“脚本执行面 + CI surface”，并未硬接线到“平台最终输出面”。
2. 因此会出现：
   - protocol validators replay 通过；
   - 但真实对话最终输出仍可能绕过 canonical egress，导致头显偶发丢失。
3. 后续 round 必须按 `RC-HUD-001..004` 归类，不允许新增同义“新根因”条目。

#### Protocol hard-close directive (single remaining closure)

1. 引入唯一最终出口 API（建议名：`final_emit_governed`）：
   - 所有 user-visible 输出仅允许通过该 API 发送。
2. `final_emit_governed` 必须强制执行：
   - `compose_and_validate_governed_reply.py`；
   - `validate_send_time_reply_gate.py`；
   - canonical receipt 检查。
3. 缺失 canonical receipt 时：
   - 直接 `FAIL_REQUIRED`；
   - 禁止 direct text fallback。
4. 将“final emission hard-gate”纳入 required gate mapping 与 drift guard（P0）。

#### Acceptance criteria (must all pass)

1. 负向 A：绕过 compose 直接发 user-visible 文本 -> 必须 fail-close（无正文下发）。
2. 负向 B：构造 actor tuple 漂移 -> 必须 fail-close 且输出 canonical blocker 码族。
3. 正向：通过 governed compose 发文 -> 首行稳定包含 `Identity-Context | Layer-Context`，且 `send_time_gate_status=PASS_REQUIRED`。

#### Evidence refs (this round)

1. `/tmp/v16_headstamp_hits_20260308.txt`
2. `/tmp/v16_headstamp_sections_20260308.txt`
3. `/tmp/v16_headstamp_code_freq_20260308.txt`
4. `/tmp/hud_probe_reply_20260308.txt`

#### Boundary

1. 本节为“去重治理 + 单剩余闭环项”声明，不宣称 `RC-HUD-001` 已代码关闭。
2. 生命周期边界不变：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.54 Round-28.3 Prompt Contract Auto-Wiring Hard Requirement (2026-03-08)

#### Problem statement (must-close)

1. 本轮深扫确认：当实例 `CURRENT_TASK.json` 缺失 prompt 合同键时，RQ-014/015/027/031 validators 会稳定落到 `SKIPPED_NOT_REQUIRED`，形成“执行过但未接线”的假收敛。
2. 该现象不允许继续依赖“定向人工命令 + 手工改实例文件”修复；v1.6 必须将其收口为协议层默认行为。
3. 冻结结论：`prompt contract null/missing = protocol wiring failure`，按 P0 控制面缺口处理。

#### Protocol-layer hardening directive (mandatory)

1. `identity_creator init/update`、`execute_identity_upgrade(review-required/safe-auto)`、`heal --apply` 必须内置 prompt 合同自动接线器；缺失即自动写入 canonical defaults，不允许静默跳过。
2. canonical defaults 来源固定为 `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` 与协议映射，不允许实例私有模板漂移。
3. 自动接线覆盖面固定四项（全部 `required=true`）：
   - `prompt_bootstrap_capability_contract_v1`
   - `prompt_capability_matrix_fail_closed_contract_v1`
   - `prompt_import_executable_coupling_contract_v1`
   - `derived_prompt_conformance_contract_v1`
4. 自动接线完成后，协议层必须同步维护 prompt validators 显式驱动集合（不得依赖隐式推断），确保 RQ-014/015 进入 required 分支。
5. 自动接线失败时必须 `FAIL_REQUIRED` 并输出专用错误码族（建议 `IP-PROMPT-WIRE-001..003`）；禁止降级为 `SKIPPED_NOT_REQUIRED`。
6. `compile_identity_runtime`、`execution_report_freshness` 与 upgrade report 需形成一致的 prompt hash 语义（文件字节 hash）；不得出现 trim-text 与 file-bytes 双口径。

#### Command contract (single explicit entrypoint)

1. 协议层必须提供单条可复放入口用于实例升级接线，不需要实例维护者追加定向手工参数链。
2. 该入口最少满足：
   - 一次执行即可触发 prompt 合同自动接线；
   - 输出可审计 receipt；
   - 后续四个 prompt validators 可直接进入 `PASS_REQUIRED`。

#### Acceptance (must all pass)

1. 对“缺失四个 prompt 合同键”的实例执行单入口升级命令后：
   - RQ-014/015/027/031 全部 `required_contract=true` 且 `PASS_REQUIRED`。
2. 不允许再出现 `required_contract_disabled_or_missing` 或 `SKIPPED_NOT_REQUIRED(contract_not_required)`。
3. `validate_execution_report_freshness.py` 必须 `freshness_status=PASS` 且 `report_newer_than_key_inputs=true`。
4. 负向探针：关闭或删除任一必需 prompt 合同键时，必须 `FAIL_REQUIRED`（而非跳过）。

#### This-round replay evidence (gap proof + closure target)

1. Gap proof (`before wiring`):
   - `/tmp/prompt_bootstrap_now_20260308.json`
   - `/tmp/prompt_cap_matrix_now_20260308.json`
   - `/tmp/prompt_kernel_coupling_now_20260308.json`
   - `/tmp/prompt_derivation_now_20260308.json`
2. Wiring proof (`after controlled wiring`):
   - `/tmp/prompt_bootstrap_after_wire_20260308.json`
   - `/tmp/prompt_cap_matrix_after_wire_20260308.json`
   - `/tmp/prompt_kernel_coupling_after_wire_20260308.json`
   - `/tmp/prompt_derivation_after_wire_20260308.json`
3. Freshness proof:
   - `/tmp/execution_report_freshness_after_upgrade_20260308.json`

#### Boundary

1. 本节将“prompt 合同接线”责任固定在协议层；实例层仅负责业务内容与历史债务，不负责协议合同结构补丁。
2. 生命周期边界不变：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.55 Round-29 L3 Final Egress Hard-Gate Closure (official alignment, 2026-03-08)

#### Why this section exists

1. Round-28.2 已冻结 `RC-HUD-001`（最终输出口未硬封闭）为主根因。
2. 本轮执行要求是：把“最终 user-visible 输出”从“建议约束”升级为“协议硬闸门”，并且对齐官方可验证能力（tool required + strict schema + deterministic final output contract）。

#### Official alignment (control philosophy)

1. Codex CLI 文档已给出“可脚本化确定输出”能力：`codex exec --json --output-last-message --output-schema`（用于最终输出形状约束与事件化审计）。
2. Chat Completions / OpenAPI 明确 `tool_choice=required` 语义：模型必须调用一个或多个工具，不允许自由文本直出作为主路径。
3. Function calling strict mode 明确：`strict=true` 时需满足 schema 约束（含 `additionalProperties=false` 与 required 字段完整），从“best effort”升级为“合同输出”。
4. Codex approvals/security 明确控制面分层：sandbox + approvals；协议层应采用同构策略（统一出口 + fail-close），而不是分散 fallback。

#### Canonical final egress contract (frozen)

1. `final_emit_channel_id = final_emit_governed`
2. `final_emit_policy_mode = tool_choice_required`
3. `final_emit_schema_id = hud_headstamp_final_emit_schema_v1`
4. `final_emit_schema_status = PASS_REQUIRED`
5. `final_emit_contract_status = PASS_REQUIRED`
6. `send_time_gate_status = PASS_REQUIRED`

任一字段缺失、漂移、或 bypass（含 outlet bypass）均必须 fail-close。

#### Code-level hardening landed (this round)

1. `scripts/validate_send_time_reply_gate.py`
   - strict 场景下新增 final emit 合同硬校验（channel/policy/schema）。
   - 错误码：`IP-ASB-STAMP-SESSION-006`（channel/policy）、`IP-ASB-STAMP-SESSION-007`（schema）。
2. `scripts/execute_identity_upgrade.py`
   - 新增 final emit passthrough 合同校验；当 `--header-first-gate-status PASS_REQUIRED` 但 final emit 关键字段缺失/不一致时，直接 fail-close。
   - 错误码对齐：`IP-OUTLET-004`。
   - 禁止“external_override”语义兜底被当作可接受真值。
3. `scripts/identity_creator.py`
   - update surface 的 `required_gate_bundle_runner` 改为透传 pre-mutation 真实 final emit/send-time tuple，不再写死 `UNKNOWN`。
4. `scripts/release_readiness_check.py`
   - bundle passthrough 改为从 selected execution report 回填 final emit/send-time 字段，避免固定 `UNKNOWN` 扩散到 strict 审计面。

#### Replay acceptance (executed)

1. Positive compose（canonical egress）：
   - `/tmp/final_emit_compose_positive_20260308.json`
   - 期望并已验证：`send_time_gate_status=PASS_REQUIRED`，`final_emit_contract_status=PASS_REQUIRED`。
2. Negative probes（必须 fail-close）：
   - channel mismatch：`/tmp/final_emit_sendtime_negative_channel_20260308.json` -> `IP-ASB-STAMP-SESSION-006`
   - policy mismatch：`/tmp/final_emit_sendtime_negative_policy_20260308.json` -> `IP-ASB-STAMP-SESSION-006`
   - schema mismatch：`/tmp/final_emit_sendtime_negative_schema_20260308.json` -> `IP-ASB-STAMP-SESSION-007`
3. Execute passthrough guard（L3 hard gate）：
   - 缺 final emit passthrough：`/tmp/final_emit_execute_missing_probe_20260308.log` + `/private/tmp/final_emit_missing_probe_reports/FINAL-EMIT-MISSING-PT-20260308.json`
   - 期望并已验证：`header_first_gate_status=FAIL_REQUIRED`，`pre_mutation_gate_error_code=IP-OUTLET-004`。
4. Post-exec invariants：
   - `/tmp/final_emit_outlet_matrix_replay_20260308.json` -> `outlet_matrix_status=PASS_REQUIRED`
   - `/tmp/final_emit_postexec_mandatory_replay_20260308.json` -> `post_execution_mandatory_status=PASS_REQUIRED`
5. Drift/surface wiring：
   - `/tmp/final_emit_surface_drift_after_patch_20260308.json` -> `required_gate_surface_drift_status=PASS_REQUIRED`

#### Boundary and truth-in-reporting

1. 本节声明“L3 final egress 控制面硬闸门已落地”，不是宣称全局发布闭环完成。
2. 实例历史债务（如 writeback continuity / prompt lifecycle 等）仍按实例层职责推进，不并入本节“控制面闭环”结论。
3. 生命周期边界保持：`SPEC_READY / PENDING_INTAKE`；`ACCEPT_WITH_FIX != READY_FOR_PROMOTION`。

### 8.56 Round-29.1 Health-check upgrade emission for final egress only-mode (2026-03-08)

#### Why this addendum is required

1. Round-29 已把 L3 `final_emit_governed` 控制面做成 fail-close，但实例侧仍会出现“未进入 required_contract 分支 -> 视觉上像是已收口，实则仍可跳过强校验”的落差。
2. 为避免再次出现“修了 20 轮但健康检查没有把升级路径直接抛给实例”的循环，本节把 final egress 升级动作写入 health check 的机器化输出链路。

#### Landed protocol changes

1. `scripts/collect_identity_health_report.py` 新增 `outlet_matrix` 检查（调用 `validate_outlet_matrix.py`）。
2. 在 strict operation（`validate/readiness/e2e/ci/three-plane`）下：
   - 自动透传 `--force-required` 给 `validate_outlet_matrix.py`，强制进入 required_contract 分支；
   - 不再允许 strict health 面以 `SKIPPED_NOT_REQUIRED` 作为静默结论。
3. `self_upgrade_plan.commands` 新增强制项：
   - `python3 scripts/validate_outlet_matrix.py ... --operation validate --force-required --json-only`
4. 健康报告新增可观测字段：
   - `final_emit_only_mode_required`
   - `final_emit_only_mode_status`
   - `final_emit_only_mode_enforced`
   - `final_emit_contract_status`

#### Replay evidence (this round)

1. `/private/tmp/health-final-emit-round291/identity-health-base-repo-architect-1772976720.json`
   - `final_emit_only_mode_required=true`（strict operation）
   - `checks[outlet_matrix].status=WARN`（旧行为：未强制 required 的对照样本）
2. `/private/tmp/health-selftest-round292/identity-health-base-repo-architect-1772977142.json`
   - `final_emit_only_mode_required=true`
   - `final_emit_only_mode_status=PASS_REQUIRED`
   - `final_emit_only_mode_enforced=true`
   - `checks[outlet_matrix].status=PASS`
2. `/tmp/health_final_emit_round291_validate_console.log`
   - 旧行为样本中 `warn:outlet_matrix` 已出现并进入升级链。
3. `/tmp/round292_health_after_patch.log`
   - strict health 回放后不再出现 `warn:outlet_matrix`；
   - 升级链仍保留 `validate_outlet_matrix --force-required` 作为强制复核项。

#### Acceptance

1. 实例执行 health check（strict operation）时，必须强制 required_contract 校验，不得再 `SKIPPED_NOT_REQUIRED`。
2. 必须输出可执行升级命令链，且包含 final egress 合同校验命令。
3. 当实例完成升级并提供新 execution report 后，`outlet_matrix_status` 应达到 `PASS_REQUIRED`（或在非 strict operation 下明确标注为非 required 场景）。

#### Boundary

1. 本节仍只处理协议控制面的“识别/校验/拒绝与升级指引输出”。
2. 实例是否完成迁移与债务清理，继续由实例层负责并回填报告。

### 8.57 Round-29.2 Validator contract alignment hotfix (2026-03-08)

#### Why this hotfix was required

1. strict health self-test 中仍出现两条误阻断：
   - `headstamp_recurrence_closure`：`IP-ASB-STAMP-SCAN-005`
   - `post_execution_mandatory`：`IP-WRB-003`
2. 复盘确认属于“验证器口径漂移”，不是 L3 final emit 合同本身失效。

#### Root-cause alignment fixes

1. `scripts/validate_headstamp_recurrence_closure.py`
   - non-governed outlet 负向探针原先仅接受 legacy 错误码 `IP-ASB-STAMP-SESSION-004`；
   - 在 Round-29 的 strict final emit 合同下，channel mismatch 已升级为 `IP-ASB-STAMP-SESSION-006`；
   - 本轮补齐兼容判定：`004 | 006` 都视为“负向探针正确 fail-close”。
2. `scripts/validate_post_execution_mandatory.py`
   - 与 `execute_identity_upgrade` 的 strict non-upgrade closure 语义对齐：
   - 当 `upgrade_required=false && all_ok=true && writeback_mode=STRICT_WRITEBACK && writeback_status in {NOT_REQUIRED, WRITTEN}`，判定为闭环通过，不再错误要求降级写回与 `next_recovery_action`。

#### Replay evidence (self-run, architect instance)

1. `/tmp/fix_verify_headstamp.json`
   - `headstamp_recurrence_closure_status=PASS_REQUIRED`
2. `/tmp/fix_verify_postexec.json`
   - `post_execution_mandatory_status=PASS_REQUIRED`
3. `/tmp/fix_verify_health_enforce.log`
   - `overall_status=PASS`
   - `warning_count=0`
   - `failed_count=0`
4. `/private/tmp/health-selftest-round292/identity-health-base-repo-architect-1772977729.json`
   - strict health `--enforce-pass` 回放通过。

#### Boundary

1. 本节仅修正“验证器合同漂移”；
2. 不改变实例层历史债务归属原则（实例负责迁移与清债，协议负责识别/校验/拒绝）。

### 8.58 Round-29.3 Default report binding and sidecar anchor stabilization (2026-03-08)

#### Why this addendum is required

1. Round-29.2 后，strict health 在“显式 `--execution-report` 绑定”已可闭环；
2. 但默认 latest_report 路径仍有漂移风险（mtime 依赖、扫描面过宽、protocol-feedback 备份文件污染活动统计）。

#### Landed protocol changes

1. `scripts/execute_identity_upgrade.py`
   - 每次写 execution report 后同步写入 canonical pointer：
   - `runtime/state/active_execution_report.json`（`run_id/report_path/updated_at`）。
2. `scripts/tool_vendor_governance_common.py`
   - `latest_identity_upgrade_report()` 优先读取 pointer；
   - 报告候选根收敛为 `runtime/reports` + `resource/reports`（去除对整个 `runtime` 根的泛扫描）；
   - 默认排除 `runtime/protocol-feedback/**` 与 archive 目录。
3. `scripts/validate_protocol_feedback_sidecar_contract.py`
   - 新增 `anchor_source` / `anchor_report_path`，并在无显式 report 时回退到 default report anchor；
   - 补齐 activity 计数字段（`activity_ref_count` 等）；
   - `track_a` 增补关键观测字段（含 report_selected_path 与 final_emit* 投影）。
4. `scripts/protocol_feedback_lane_common.py`
   - protocol-feedback 活动扫描新增 ignore 策略：`*.bak*`, `*.tmp`, `*~`, `*.swp`, `.DS_Store`。

#### Replay evidence

1. base-repo-architect（strict health, no explicit report）
   - `/tmp/audit_postcommit_base_health_noreport.log`
   - `/private/tmp/audit-postcommit/identity-health-base-repo-architect-1772979281.json`
   - 结果：`overall_status=PASS`。
2. pointer 生效快照：
   - `/tmp/audit_pointer_base_snapshot.txt`
   - 结果：`active_execution_report.json` 已写入，`latest_identity_upgrade_report` 命中 pointer 指向报告。
3. sidecar anchor 稳定性与污染收敛（custom-creative-ecom-analyst）：
   - `/tmp/sidecar_compare_no_report_afterpatch_6537307.json`
   - `/tmp/sidecar_compare_with_report_afterpatch_6537307.json`
   - 结果：`anchor_source` 明确、`activity_ref_count` 可观测、活动 refs 不再包含 `.bak` 文件。

#### Boundary

1. 本节解决“默认绑定/锚点/扫描污染”协议控制面问题；
2. 不等于实例历史债务清零（例如 custom-creative-ecom-analyst 当前仍有 `IP-SID-002` 链路阻断，需实例升级与债务回填）。

### 8.59 Round-29.4 Prompt contract auto-wiring closure in update lane (2026-03-08)

#### Why this addendum is required

1. Round-28.3 明确了“prompt contract null/missing = protocol wiring failure”，但代码侧仍缺“update lane 自动接线 + fail-close 错误码”闭环。
2. 本节只补协议层接线能力，不替代实例业务债务修复。

#### Landed protocol changes

1. `scripts/execute_identity_upgrade.py`
   - 新增 `_ensure_prompt_contract_auto_wiring()`：
     - 在 update 执行前自动补齐四个 canonical prompt 合同键：
       - `prompt_bootstrap_capability_contract_v1`
       - `prompt_capability_matrix_fail_closed_contract_v1`
       - `derived_prompt_conformance_contract_v1`
       - `prompt_import_executable_coupling_contract_v1`
     - 对已存在但被降级的合同强制回写 `required=true`（禁止静默降级为非 required）。
   - 新增错误码族并接入 pre-mutation fail-close：
     - `IP-PROMPT-WIRE-001`：合同写回失败（I/O）
     - `IP-PROMPT-WIRE-002`：自动接线后仍缺失必需合同
     - `IP-PROMPT-WIRE-003`：合同结构非法/不可执行
2. update 报告新增机器可观测字段：
   - `prompt_contract_auto_wire_status`
   - `prompt_contract_auto_wire_error_code`
   - `prompt_contract_auto_wire_missing_before/after`
   - `prompt_contract_auto_wire_forced_required_keys`

#### Replay evidence (architect self-run)

1. `python3 scripts/execute_identity_upgrade.py ... --identity-id base-repo-architect --actor-id assistant:codex ...`
   - 产物：`/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/runtime/reports/identity-upgrade-exec-base-repo-architect-1772980888.json`
   - 关键字段：
     - `prompt_contract_auto_wire_status=PASS_REQUIRED`
     - `prompt_contract_auto_wire_missing_before` 含四个 prompt 合同键
     - `prompt_contract_auto_wire_missing_after=[]`
2. update 后 CURRENT_TASK 合同实态（同 identity）：
   - 四个 prompt 合同键均存在，`required=true`，validator 路径完整。
3. 边界一致性：
   - 本次回放仍可能命中实例环境阻断（如 `IP-CAP-003`），但 prompt 接线不再是跳过型阻断源。

#### Boundary

1. 本节只关闭“update lane prompt 合同自动接线”协议缺口。
2. 不宣称实例能力驱动内容已达标；能力缺失仍应由实例升级与回填解决。

### 8.60 Round-29.5 Heal-lane prompt contract wiring parity (2026-03-08)

#### Why this addendum is required

1. Round-29.4 关闭了 update lane 的自动接线，但 `heal --apply` 仍通过 `repair_contract_backfill.py` 进入修复链，必须保证同级 fail-close 合同。
2. 协议层目标是不让 heal lane 成为 prompt 合同“弱约束旁路”。

#### Landed protocol changes

1. `scripts/repair_contract_backfill.py`
   - 新增 prompt contract 必需键集合（四项与 Round-29.4 一致）；
   - 新增 `_normalize_prompt_contracts()`：
     - 自动补齐缺失 prompt 合同键；
     - 强制 `required=true`；
     - `validator` 空值回填 canonical default。
2. 新增 prompt wiring fail-close 错误码语义（与 update lane 对齐）：
   - `IP-PROMPT-WIRE-002`：auto-wire 后仍缺 required prompt 合同键；
   - `IP-PROMPT-WIRE-003`：auto-wire 后合同结构仍非法（如 validator 为空）。
3. 回填报告新增机器字段：
   - `prompt_contract_auto_wire_status`
   - `prompt_contract_auto_wire_error_code`
   - `missing_prompt_contract_keys_before/after`
   - `forced_prompt_required_keys`
   - `restored_prompt_validator_keys`
4. `scripts/identity_creator.py` heal strict 面接线补齐：
   - `heal` 子命令新增 `--actor-id`；
   - heal 内部 `validate` 与 `health_post_validate_recheck` 统一透传 actor，避免 strict validate 因缺 actor 直接触发 `IP-ACTOR-ENTRY-001` 伪阻断。

#### Replay evidence

1. `python3 scripts/repair_contract_backfill.py --catalog <project>/.identity/catalog.local.yaml --identity-id base-repo-architect --apply --json-only`
   - 证据：`/tmp/round295_repair_contract_backfill_base.json`
   - 结果：`contract_backfill_status=PASS_REQUIRED`，`prompt_contract_auto_wire_status=PASS_REQUIRED`。
2. `python3 scripts/identity_creator.py heal --identity-id base-repo-architect --catalog <project>/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --apply`
   - 证据：`/tmp/round295_heal_base.log`
   - 结果：heal 链路中的 backfill 步骤已输出 prompt wiring 字段并通过；后续失败点落在 actor/session 健康项（实例/会话态债务），非 prompt 接线缺口。
3. `python3 scripts/identity_creator.py heal --identity-id base-repo-architect --actor-id assistant:codex --catalog <project>/.identity/catalog.local.yaml --repo-catalog identity/catalog/identities.yaml --scope USER --apply`
   - 证据：`/tmp/round295_heal_base_actorwired.log`
   - 结果：不再出现 `IP-ACTOR-ENTRY-001`；当前失败收敛到 `IP-ASB-201`（实例会话绑定债务）。

#### Boundary

1. 协议层职责：自动接线 + 校验 + 拒绝（已补齐 update/heal 双入口）。
2. 实例层职责：能力驱动内容、actor/session 健康、历史债务回填（如 `IP-CAP-003`、`IP-ASB-RFS-*`）。


### 8.61 Round-29.6 strict egress actor + bundle UNKNOWN literal closure (2026-03-09)

#### Closure scope (protocol control-plane)

1. `scripts/final_emit_governed.py` 移除隐式 actor 默认回退：
   - 不再允许 `DEFAULT_ACTOR_ID` 自动兜底；
   - 缺 `--actor-id` 且无 `CODEX_ACTOR_ID` 时 fail-close（`IP-FE-006`）。
2. strict surface 的 `required_gate_bundle_runner` 参数值语义收敛：
   - `--send-time-gate-status`
   - `--final-emit-contract-status`
   - `--final-emit-schema-status`
   - 以上三项禁止 literal `UNKNOWN`，统一收敛为显式语义值（本轮收口到 `NOT_APPLICABLE`）。
3. `scripts/validate_required_gate_surface_drift.py` 增加值域门禁：
   - 新增 `bundle_arg_value_invalid` 检测；
   - 任一 strict surface 在上述三项出现 `UNKNOWN` 时 fail-close：`IP-GATE-ENTRY-007`。

#### Landed files

1. `scripts/final_emit_governed.py`
2. `scripts/validate_required_gate_surface_drift.py`
3. `scripts/identity_creator.py`
4. `scripts/release_readiness_check.py`
5. `scripts/full_identity_protocol_scan.py`
6. `scripts/e2e_smoke_test.sh`
7. `.github/workflows/_identity-required-gates.yml`

#### Cross-verification (before/after)

1. final egress actor fallback probe：
   - before: no `--actor-id` => `PASS_REQUIRED`（`actor_resolution_mode=default`）
   - after: no `--actor-id` => `FAIL_REQUIRED`（`IP-FE-006`）
   - with actor: `PASS_REQUIRED`
2. strict bundle UNKNOWN literal probe：
   - before: strict surfaces 存在 `UNKNOWN` literal 占位；
   - after: target surfaces `UNKNOWN` literal count = `0`。
3. gate replay：
   - `validate_required_gate_surface_drift --json-only` => `PASS_REQUIRED`（`bundle_arg_value_invalid={}`）
   - `docs_command_contract_check` => `PASS`
   - `validate_protocol_ssot_source` => `OK`

### 8.62 Round-29.7 control-plane invariants + growth budget hardening (2026-03-09)

#### Why this section exists

1. repository growth is no longer small-scale; contract drift now comes from structural expansion pressure, not single bug class.
2. governance objective is to keep protocol control-plane stable while preserving model capability expansion in execution layer.

#### Normative control-plane invariants (10 red lines)

1. user-visible outbound text must pass through `scripts/final_emit_governed.py`.
2. strict required-gate aggregation must pass through `scripts/required_gate_bundle_runner.py`.
3. strict surfaces must include recurrence escalator and tuple parity lineage artifacts.
4. strict surfaces must not directly invoke forbidden required validators from mapping rows in bundle scope.
5. strict surfaces must not directly invoke `scripts/compose_and_validate_governed_reply.py`.
6. strict surfaces must pass actor context for all mandatory headstamp/egress validators.
7. strict surfaces must pass session context for actor-session binding validators.
8. strict bundle calls must include full required argument contract (`run-id`, send-time/final-emit tuple, actor/work/source/lock).
9. strict bundle calls must not use literal `UNKNOWN` for:
   - `--send-time-gate-status`
   - `--final-emit-contract-status`
   - `--final-emit-schema-status`
10. status promotion text must be machine-derived from gate receipts; manual green-label edits are non-normative.

#### Machine enforcement wiring

1. drift gate remains authoritative for invariants 1..9:
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
2. growth budget gate is now mandatory in CI:
   - `python3 scripts/validate_control_plane_budget.py --json-only`
3. budget source of truth:
   - `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
4. budget semantics:
   - dual threshold (`warn` / `fail`) is used to avoid no-headroom lockups while still fail-closing structural overgrowth.

#### Growth-budget contract (minimal, non-overfitted)

1. validator scripts budget: controls uncontrolled script-surface explosion.
2. error-code budget: controls taxonomy inflation and semantic fragmentation.
3. mapping-vs-bundle gap budget: prevents required-plane divergence from silently growing.
4. strict direct-validate call budget: freezes direct-call expansion until migration to bundle single-entry is complete.

#### Promotion boundary

1. `FAIL_REQUIRED` from budget gate blocks promotion.
2. `WARN_NON_BLOCKING` does not block promotion, but must be logged as review debt.
3. `PASS_REQUIRED` is required to claim control-plane budget stability at current head.

#### Acceptance commands (replay)

1. `python3 scripts/validate_control_plane_budget.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/docs_command_contract_check.py`
4. `python3 scripts/validate_protocol_ssot_source.py`

### 8.63 Round-29.8 machine promotion-state artifact + sync gate (2026-03-09)

#### Why this section exists

1. review text can drift from executable gate reality when status is edited manually.
2. governance requirement is machine-only status promotion derived from current gate receipts.

#### Implementation scope

1. add machine status renderer:
   `scripts/render_control_plane_status.py`
2. add status sync validator (fail-close on drift):
   `scripts/validate_control_plane_status_sync.py`
3. add machine status artifact ssot:
   `identity/protocol/mappings/control-plane-status.v1.6.json`
4. wire sync gate into CI:
   `.github/workflows/_identity-required-gates.yml`
5. fail-close code for artifact drift:
   `IP-CP-STATUS-001`

#### Promotion-state semantics

1. `control_plane_status=PASS_REQUIRED` => `promotion_ready=true`.
2. `control_plane_status=PASS_WITH_BLOCKERS` => `promotion_ready=false`.
3. `control_plane_status=FAIL_REQUIRED` => `promotion_ready=false`.
4. `PASS_WITH_BLOCKERS` is machine-derived from gate warnings (`WARN_NON_BLOCKING`), not manual state text.

#### Acceptance commands (replay)

1. `python3 scripts/render_control_plane_status.py --json-only`
2. `python3 scripts/validate_control_plane_status_sync.py --json-only`
3. `python3 scripts/validate_control_plane_invariants.py --json-only`
4. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
5. `python3 scripts/docs_command_contract_check.py`
6. `python3 scripts/validate_protocol_ssot_source.py`

### 8.64 Round-29.9 control-plane budget re-anchor closure (2026-03-09)

#### Why this section exists

1. after adding invariants/status-sync gates, budget warn thresholds became stale against current machine baseline.
2. stale warn baselines kept control-plane status at `PASS_WITH_BLOCKERS` despite all structural gates passing.

#### Re-anchor scope

1. update budget warning baselines in:
   `identity/protocol/mappings/control-plane-budget.v1.6.yaml`
2. keep fail thresholds unchanged (no downgrade of hard-stop boundary).
3. re-render status artifact:
   `identity/protocol/mappings/control-plane-status.v1.6.json`

#### Updated warn baselines

1. `validator_scripts.warn: 140 -> 142`
2. `error_codes.warn: 373 -> 375`
3. `.github/workflows/_identity-required-gates.yml direct_validate_calls.warn: 101 -> 103`

#### Decision boundary

1. this is a baseline synchronization closure, not a relaxation of fail-close policy.
2. current machine control-plane status after re-anchor:
   - `control_plane_budget_status=PASS_REQUIRED`
   - `control_plane_status=PASS_REQUIRED`
   - `promotion_ready=true` (control-plane scope only)
3. required-plane coverage debt remains explicitly frozen by invariants (`mapping_rows_missing_in_bundle=25`) and is out of this re-anchor scope.

#### Acceptance commands (replay)

1. `python3 scripts/validate_control_plane_budget.py --json-only`
2. `python3 scripts/render_control_plane_status.py --json-only`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. `python3 scripts/validate_control_plane_invariants.py --json-only`
5. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
6. `python3 scripts/docs_command_contract_check.py`
7. `python3 scripts/validate_protocol_ssot_source.py`

### 8.65 Round-30.0 prompt-capability nested-validator convergence + full-scan zero-P0 closure (2026-03-09)

#### Why this section exists

1. full-scan `scan-mode=full` still produced a residual `P0` on `base-repo-architect` even after control-plane gates were green.
2. root cause was validator input projection drift: prompt-capability validators only read top-level `required_validators`, while the instance had validator contracts under nested nodes.

#### Protocol patch scope

1. `scripts/validate_prompt_bootstrap_capability.py`
   - aggregate configured validators from:
     - top-level `required_validators`
     - `ci_enforcement_contract.required_validators`
     - `identity_update_lifecycle_contract.validation_contract.required_checks`
2. `scripts/validate_prompt_capability_matrix.py`
   - apply the same multi-source validator aggregation model.
3. behavior remains fail-close:
   - missing drivers still returns `FAIL_REQUIRED` (`IP-PBOOT-001` / `IP-PCAPM-001`).

#### Instance closure action (non-protocol tracked runtime)

1. add explicit `required_validators` capability drivers in:
   `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect/CURRENT_TASK.json`
2. this action closes runtime debt without weakening protocol fail-close semantics.

#### Replay evidence

1. pre-fix failing probe:
   - `/tmp/audit_round302_prompt_bootstrap_architect_20260309.json` (`FAIL_REQUIRED`, `IP-PBOOT-001`)
   - `/tmp/audit_round302_prompt_matrix_architect_20260309.json` (`FAIL_REQUIRED`, `IP-PCAPM-001`)
2. post-fix validator replay:
   - `/tmp/audit_round302_prompt_bootstrap_architect_afterfix_20260309.json` (`PASS_REQUIRED`)
   - `/tmp/audit_round302_prompt_matrix_architect_afterfix_20260309.json` (`PASS_REQUIRED`)
3. full-scan closure replay:
   - `/tmp/audit_round302_full_scan_full_afterfix_20260309.json`
   - summary: `total=4, p0=0, p1=0, ok=4`
4. control-plane cross-check after patch:
   - `/tmp/audit_round302_budget_afterfix_20260309.json`
   - `/tmp/audit_round302_invariants_afterfix_20260309.json`
   - `/tmp/audit_round302_status_sync_afterfix_20260309.json`
   - `/tmp/audit_round302_surface_drift_afterfix2_20260309.json`
   - `/tmp/audit_round302_docs_contract_afterfix_20260309.log`
   - `/tmp/audit_round302_ssot_afterfix_20260309.log`

#### Decision boundary

1. this closure removes the remaining round302 `P0` in full-scan while preserving strict fail-close behavior.
2. protocol scope closes validator projection drift; instance scope closes missing runtime capability-driver declaration.
3. promotion statements remain machine-derived only.

### 8.66 Round-30.1 prompt-lifecycle no-upgrade false-blocker closure + three-loop replay (2026-03-09)

#### Why this section exists

1. Round-303 full-scan (`scan-mode=full`, `target-source-layer=auto`) regressed to `p0=1`.
2. root cause was in `validate_identity_prompt_lifecycle.py`: no-upgrade reports (`upgrade_required=false`) with `runtime_state_artifact_path` placeholder still failed when artifact file was absent, producing a false blocker.

#### Protocol patch scope

1. `scripts/validate_identity_prompt_lifecycle.py`
2. add conditional allowance for missing runtime state artifact only when:
   - `upgrade_required=false`
   - `prompt_change_required=false`
   - `prompt_change_applied=false`
   - `prompt_runtime_state_binding_status in {"MISSING", "", "SKIPPED_NOT_REQUIRED"}`
3. keep fail-close for upgrade paths unchanged.

#### Cross-verification probes

1. positive replay (no-upgrade):
   - `/tmp/audit_round303_prompt_lifecycle_architect_afterfix.log`
   - result: `[OK] prompt lifecycle validated`
2. negative replay (upgrade-required + missing runtime artifact):
   - `/tmp/audit_round303_prompt_lifecycle_negative2.log`
   - result: `[FAIL] runtime state artifact missing ...`

#### Three-loop convergence evidence

1. Round-303B:
   - `/tmp/audit_round303b_full_auto_20260309.json`
   - summary: `total=4, p0=0, p1=0, ok=4`
2. Round-304:
   - `/tmp/audit_round304_full_auto_20260309.json`
   - summary: `total=4, p0=0, p1=0, ok=4`
3. Round-305C:
   - `/private/tmp/audit_round305c_full_auto_20260309.json`
   - summary: `total=4, p0=0, p1=0, ok=4`

#### Boundary note (cross-layer scan)

1. `target-source-layer=both` still shows global-lane `P0` entries when current env is project-bound.
2. those are runtime mode guard (`IP-ENV-003`) boundary signals, not project control-plane regressions.

### 8.57 Round-30.2: RQ-034 Runtime-Proof Strict/Scan Convergence

Decision:

1. strict operations keep fail-close runtime-proof enforcement for multimodal plugin gating.
2. scan operations remain observational and must not be upgraded to strict runtime-proof blockers.
3. full-scan shadow probe keeps tuple parity validation but no longer forces strict semantics in scan path.

Implementation anchors:

1. `scripts/validate_multimodal_plugin_enforcement.py`
   - strict-only runtime evidence enforcement with `IP-MM-RUN-*`.
   - `scan` stays `multimodal_runtime_evidence_status=SKIPPED_NOT_REQUIRED`.
2. `scripts/required_gate_bundle_runner.py`
   - strict row contract requires multimodal runtime proof fields only on strict operations.
3. `scripts/release_readiness_check.py`
   - bundle passthrough includes selected execution report path for runtime-proof binding.
4. `scripts/report_three_plane_status.py`
   - multimodal runtime-proof projection fields are emitted in instance-plane detail.
5. `scripts/full_identity_protocol_scan.py`
   - `required_gate_bundle_runner_shadow` changed to `operation=scan`.
   - tuple parity in full-scan probe uses `--require-distinct-surface-labels` (not strict-operation forcing).

Replay evidence (2026-03-09):

1. strict fail-close replay:
   - `/tmp/rq034_runtime_validate_fail_20260309_r2.json` (`FAIL_REQUIRED`, `IP-MM-RUN-001`)
2. strict positive replay:
   - `/tmp/rq034_runtime_validate_pass_20260309_r2.json` (`PASS_REQUIRED`)
3. scan non-blocking replay:
   - `/tmp/rq034_runtime_scan_nonblocking_20260309_r2.json` (`PASS_REQUIRED`, runtime evidence `SKIPPED_NOT_REQUIRED`)
4. full-scan target convergence:
   - `/tmp/rq034_runtime_fullscan_target_braev3_20260309_r4.json`
   - summary `p0=0, p1=0, ok=1`
5. baseline gates after convergence:
   - `/tmp/rq034_runtime_surface_drift_20260309_r4.json` (`PASS_REQUIRED`)
   - `/tmp/rq034_runtime_docs_contract_20260309_r4.log` (rc=0)
   - `/tmp/rq034_runtime_ssot_20260309_r4.log` (rc=0)

### 8.58 Round-30.3: Runtime-Proof Producer Emission + Target-Scan CI Regression Gate

Decision:

1. runtime-proof fields for RQ-034 must be producer-emitted by upgrade report generation, not inferred only at validator layer.
2. three-plane multimodal target probe must bind the selected execution report explicitly (`--report-selected-path`) to remove latest-report fallback drift.
3. CI adds a fixed regression gate: `full_identity_protocol_scan --scan-mode target` must keep `summary.p0 == 0` (fail-close on regression).

Implementation anchors:

1. `scripts/execute_identity_upgrade.py`
   - report writer now guarantees multimodal runtime-proof fields are always emitted:
   - `multimodal_preflight_status`
   - `multimodal_calls/resolved/unresolved/errors/retry_calls`
   - `multimodal_evidence_refs`
   - `runtime_gate_mode`, `runtime_gate_required_confidence`
   - `multimodal_runtime_field_emission_status=PASS_REQUIRED`
2. `scripts/report_three_plane_status.py`
   - multimodal bundle target call now forwards `--report-selected-path`.
   - projection adds `report_selected_path` for direct observability in instance plane.
3. `scripts/full_identity_protocol_scan.py`
   - when latest runtime report is available, multimodal target probe receives `--report-selected-path`.
   - multimodal projection includes `report_selected_path` field.
4. `scripts/validate_full_scan_target_regression.py` (new)
   - validates target full-scan summary and blocks on:
   - `IP-SCAN-REG-001`: `p0 != 0`
   - `IP-SCAN-REG-002`: scan command failed
   - `IP-SCAN-REG-003`: invalid/missing scan report
5. `.github/workflows/_identity-required-gates.yml`
   - adds mandatory step `Validate full-scan target regression (p0=0)`.

Replay evidence (2026-03-09):

1. producer emission proof:
   - `/tmp/rq034_upgrade_reports_r3/identity-upgrade-exec-rq034-production-fields-20260309.json`
   - includes `multimodal_runtime_field_emission_status=PASS_REQUIRED` and full multimodal runtime-proof key set.
2. three-plane explicit report binding:
   - `/tmp/rq034_three_plane_runtime_fields_20260309_r6.json`
   - `instance_plane_detail.multimodal_plugin_enforcement.report_selected_path` equals `runtime_report_path`.
3. target scan fixed regression gate:
   - `/tmp/rq034_full_scan_target_regression_20260309_r3.result.json`
   - `/tmp/rq034_full_scan_target_regression_20260309_r3.json`
   - result: `PASS_REQUIRED`, `p0=0`, `p1=0`, `ok=1`.
4. baseline control gates:
   - `/tmp/rq034_surface_drift_20260309_r3.json` (`PASS_REQUIRED`)
   - `/tmp/rq034_docs_contract_20260309_r3.log` (rc=0)
   - `/tmp/rq034_ssot_20260309_r3.log` (rc=0)

## 9) References

1. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
3. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
4. `docs/review/protocol-remediation-audit-ledger-v1.6.md`
5. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
6. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`
7. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
8. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
9. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
10. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
11. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
12. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
13. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
14. `https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide/#frequented-asked-questions-faq`
15. `context7:/websites/developers_openai_api (strict schema/tool docs extraction)`
16. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
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
45. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
46. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
47. `/Users/yangxi/.codex/.identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
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
66. `https://developers.openai.com/codex/cli/reference/#codex-exec`
67. `https://developers.openai.com/codex/agent-approvals-security/#sandbox-and-approvals`
68. `https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create/`
69. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
70. `https://github.com/openai/codex`

## v1.6.0 Addendum (2026-03-16): Control-plane scoped residue scan

### A1) Problem statement

1. Broad scans over archival trees (`runtime/reports`, `sanitization-backups`) can surface historical `.agents/identity` literals and trigger false P0 attribution.
2. Ownership then drifts between protocol and instance, slowing P0 closure.

### A2) Mandatory behavior

1. Canonical scanner: `scripts/scan_identity_path_residue.py`.
2. Scanner include scope must be control-plane only:
   - `catalog.local.yaml`
   - `CURRENT_TASK.json`
   - `IDENTITY_PROMPT.md`
   - `META.yaml`
   - `runtime/state/**/*`
   - `runtime/plugins/**/*`
   - `runtime/gate/**/*`
3. Scanner exclude scope must always include:
   - `runtime/reports/**`
   - `sanitization-backups/**`
   - `*.bak*`
4. Attribution rule:
   - scoped scan `PASS_REQUIRED` + live headstamp loss => default to instance-governance issue unless cross-instance protocol transport bypass evidence exists.

### A3) Required scan metrics

1. `scanned_file_count`
2. `hit_count`
3. `total_match_count`
4. `path_residue_status`
5. `identity_home`

### A4) Unified headstamp closure semantics (authoritative wording)

1. Current-phase objective is fixed to:
   - **95% pre-send hard gating + 100% post-check detectability + next-hop hard block**.
2. Governance communication must use this wording consistently and must not introduce alternate phase targets.
3. Runtime fail-close baseline in this phase:
   - if post-check state is missing/invalid/mismatch, next-hop must block with fail-close receipt.
   - no pass-through is allowed when headstamp continuity is not provable on the next hop.
4. Ownership baseline:
   - protocol-side enforces detectability + next-hop blocker contracts;
   - instance-side fixes lane/runtime implementations surfaced by those contracts.
