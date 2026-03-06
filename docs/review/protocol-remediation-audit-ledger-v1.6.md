# Protocol Remediation Audit Ledger (v1.6 Pre-Release)

Status: Active
Layer: protocol-only tracking ledger (non-governance)
Purpose: Central place for architect + audit-expert planning, implementation replay, and closure decisions before `v1.6` tag.

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
| FIX16-001 | 2026-03-03 | protocol | v1.6 governance+review document bootstrap | UNCOMMITTED | DONE | PENDING_REVIEW |
| FIX16-002 | 2026-03-03 | protocol | release unlock formula automation (`ASB16-RQ-001`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-003 | 2026-03-03 | protocol | capability boundary governance (`ASB16-RQ-002`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-004 | 2026-03-03 | protocol | status promotion evidence pipeline (`ASB16-RQ-003`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-005 | 2026-03-03 | protocol | outlet regression matrix (`ASB16-RQ-004`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-006 | 2026-03-03 | protocol | sidecar invariance regression lock (`ASB16-RQ-005`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-007 | 2026-03-03 | protocol | release-plane cloud evidence contract (`ASB16-RQ-006`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-008 | 2026-03-03 | protocol | cross-cwd absolute-input runbook (`ASB16-RQ-007`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-009 | 2026-03-03 | protocol | docs bridge consistency automation (`ASB16-RQ-008`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-010 | 2026-03-04 | protocol | run-id anchored strict report selection (`ASB16-RQ-009`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-011 | 2026-03-04 | protocol | baseline phase-A auto-bootstrap (`ASB16-RQ-010`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-012 | 2026-03-04 | protocol | regression temp collision-safe strategy (`ASB16-RQ-011`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-013 | 2026-03-04 | protocol | handoff/collab freshness auto-bootstrap (`ASB16-RQ-012`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-014 | 2026-03-04 | protocol | protocol-feedback atomic emit helper (`ASB16-RQ-013`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-015 | 2026-03-04 | protocol | bootstrap capability-driver intake from SRA packet (`ASB16-RQ-014`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-016 | 2026-03-04 | protocol | prompt capability matrix fail-close validator intake (`ASB16-RQ-015`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-017 | 2026-03-04 | protocol | refresh->strict + business interference guard runbook intake (`ASB16-RQ-016`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-018 | 2026-03-04 | protocol | roundtable/vendor/openaidoc/context7 cross-verification intake (`ASB16-RQ-017`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-019 | 2026-03-04 | protocol | office-ops self-drive regression supplemental intake (`ASB16-RQ-018..022`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-020 | 2026-03-04 | protocol | discovery dual-track activation + apply-time coverage fail-close intake (`ASB16-RQ-023..024`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-021 | 2026-03-04 | protocol | kernel-first baseline: contract source canonicalization + mapping + derived prompt lineage (`ASB16-RQ-025..028`) | 6f49040 | SPEC_READY | PENDING_INTAKE |
| FIX16-022 | 2026-03-05 | protocol | semantic routing single-source convergence intake (`ASB16-RQ-029`) + rollout prioritization replay (`A-D P0`, `E P1`) | f603dd9 | SPEC_READY | PENDING_INTAKE |
| FIX16-023 | 2026-03-05 | protocol | v1.6 suggestion intake evidence quorum hard-gate (`ASB16-RQ-030`; roundtable+vendor+online/spec evidence required before promotion beyond `PENDING_INTAKE`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-024 | 2026-03-05 | protocol | protocol-kernel prompt import executable-coupling self-drive intake (`ASB16-RQ-031`; text import alone is insufficient without validator mapping + multimodal sample-proof closure + explicit actor context) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-025 | 2026-03-05 | protocol | deep cross-verification closure intake (`ASB16-RQ-015/029/030`; `T1..T4` evidence taxonomy normalization + deterministic verdict + non-regression strengthening sequence `S0..S4`) | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-026 | 2026-03-05 | protocol | base-repo-architect identity self-drive pilot: protocol-kernel prompt injection + multimodal verification uplift (`ASB16-RQ-031`), with v1.5/v1.6 boundary normalization | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |
| FIX16-027 | 2026-03-05 | protocol | final T1/T2/T3/T4 cross-verification replay (`ASB16-RQ-015/017/029/030/031`) with network re-check + vendor/spec consistency hardening (v1.6-only positive supplement) | b2c99fd | SPEC_READY | PENDING_INTAKE |
| FIX16-028 | 2026-03-05 | protocol | full-repo deep-scan lock inventory (`ASB16-RQ-001..032`): kernel/script lock-state census + architect independent rescan protocol | 7e7481d | SPEC_READY | PENDING_INTAKE |
| FIX16-029 | 2026-03-05 | protocol | outbound headstamp pre-send hard-gate intake (`ASB16-RQ-032`): block send on missing/malformed/mismatched `Identity-Context|Layer-Context` | 7e7481d | SPEC_READY | PENDING_INTAKE |
| FIX16-030 | 2026-03-05 | protocol | batch-1 (`ASB16-RQ-001..005`) row-level strengthening normalization: acyclic unlock formula + explicit capability mapping + non-repudiation promotion receipt + outlet negative-path matrix + normalized sidecar parity | 031e9ba | SPEC_READY | PENDING_INTAKE |
| FIX16-031 | 2026-03-06 | protocol | Batch-2A (`ASB16-RQ-006..010`) row-level strengthening normalization: release-plane cloud evidence wiring + cross-cwd absolute-input contract + docs bridge checker + run-id-first report selector + phase-A/B parity contract | 5cb1a14 | SPEC_READY | PENDING_INTAKE |
| FIX16-032 | 2026-03-06 | protocol | Batch-3B (`ASB16-RQ-024..028`) row-level strengthening normalization: discovery apply coverage hard-close + kernel-first source lock + mapping coverage asset + derived prompt conformance metadata + instance write-boundary canonical code alignment | 3538eb7 | SPEC_READY | PENDING_INTAKE |
| FIX16-033 | 2026-03-06 | protocol | Batch-4 (`ASB16-RQ-029/031/032/007/008`) four-track strengthening normalization: semantic single-source convergence + prompt import executable-coupling + headstamp canonical error-family convergence + cross-cwd parity replay + docs bridge contradiction checker + actor-id fallback recurrence supplement | 06bcb8a + 140c872 + db72970 + ca14131 + 9c0463e | SPEC_READY | PENDING_INTAKE |
| FIX16-034 | 2026-03-06 | protocol | Batch-5 (`ASB16-RQ-010/011/012/013/016`) orchestration strengthening normalization: phase-A/B parity closure + tmp collision-safe allocator + handoff/collab freshness auto-rotation + protocol-feedback atomic emit + refresh->strict interference matrix receipts | 4f98bf4 + 84daaee | SPEC_READY | PENDING_INTAKE |
| FIX16-035 | 2026-03-06 | protocol | Batch-6 (`ASB16-RQ-017/018/019/020/021`) cross-workflow governance strengthening normalization: four-track contract hardening + dedup monotonic winner + cross-workflow schema gate + skill-path layout integrity + route/workflow publish-version pinning | 0df31f5 + 10c9956 + b80ec1f + 9e59e0f + f63eb55 + e214df9 + 9c0cf0a + 19d02ab + b5a191c + 5f7eb44 + 228ba40 + b7137e3 + 47f2f38 + b258982 + 1beeb88 | SPEC_READY | PASS_WITH_BLOCKERS |
| FIX16-036 | 2026-03-06 | protocol | Batch-7 (`ASB16-RQ-022/030`) closure strengthening normalization: fallback taxonomy enum normalization + T1/T2/T3/T4 intake evidence quorum automation with metadata hard gate | 0df31f5 + 10c9956 + b80ec1f + f63eb55 + e214df9 + 4f4930c + 08c8f89 + 5f7eb44 + 228ba40 + b7137e3 + 47f2f38 + b258982 + 1beeb88 | SPEC_READY | PASS_WITH_BLOCKERS |
| FIX16-037 | 2026-03-06 | protocol | write-boundary non-starvation hardening (`ASB16-RQ-028/031`): lane-scoped boundary semantics + protocol-entry liveness invariant + no-silent-downgrade fail-close + mandatory telemetry tuple + replay matrix hard-gate | UNCOMMITTED | SPEC_READY | PENDING_INTAKE |

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

Acceptance target:

1. Same input, same output hash.
2. Includes `D1..D6`, `p0_total`, `p0_done`, `p0_not_done_refs`, `protocol_blockers`, `env_blockers`.

### FIX16-003 - capability boundary governance (`ASB16-RQ-002`)

- Status: `SPEC_READY`
- Goal: isolate env/auth blockers from protocol code closure claims.

Acceptance target:

1. `IP-CAP-*` consistently classified as env/auth in release summary.
2. Full-scan and three-plane classification is aligned with unlock report.

### FIX16-004 - status promotion evidence pipeline (`ASB16-RQ-003`)

- Status: `SPEC_READY`
- Goal: prevent narrative-only promotion to `DONE`.

Acceptance target:

1. Every promotion has commit + replay evidence + reviewer decision.
2. Missing evidence causes fail-closed promotion denial.

### FIX16-005 - outlet regression matrix (`ASB16-RQ-004`)

- Status: `SPEC_READY`
- Goal: guarantee compose/send-time invariance across required lanes.

Acceptance target:

1. creator/readiness/e2e/full-scan/three-plane all pass.
2. root/tmp cross-cwd parity remains stable.

### FIX16-006 - sidecar invariance lock (`ASB16-RQ-005`)

- Status: `SPEC_READY`
- Goal: preserve sidecar passthrough ordering and cwd invariance.

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

Acceptance target:

1. consistency checker flags contradictory state pairs.
2. bridge output includes exact anchors updated in both docs.

### FIX16-010 - office-ops intake triage bridge (`ASB16-RQ-009..013`)

- Status: `SPEC_READY`
- Goal: register office-ops protocol feedback package into v1.6 backlog with explicit v1.5/v1.6 split boundary.

Source package:

1. `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_20260304T041651Z_office_ops_protocol_upgrade_suggestions.md`
2. `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/upgrade-proposals/PROTOCOL_UPGRADE_PROPOSAL_20260304T041651Z_office_ops_self_drive.md`
3. `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/outbox-to-protocol/SPLIT_RECEIPT_20260304T041849Z_identity-upgrade-exec-office-ops-expert-1772596487.json`
4. `/Users/yangxi/.codex/identity/instances-canonical/office-ops-expert/runtime/protocol-feedback/evidence-index/INDEX.md`

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

1. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
2. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
3. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
4. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
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
5. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
6. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`

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

1. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
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
9. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
10. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`

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
3. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-05_001.md`
4. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/issues/ISSUE_2026-03-05_update-threeplane-semantic-convergence-gap.md`
5. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/upgrade-proposals/PROPOSAL_2026-03-05_semantic-single-source-and-convergence-gate.md`
6. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`

Machine replay extraction (2026-03-05 strict lineage):

1. update report:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
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
5. Runtime replay set:
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
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
   - closure gap is convergence/executability (`ASB16-RQ-015/029/030` still implementation-pending).

Positive-strengthening sequence (non-regression required):

1. `S0 shadow`: semantic convergence comparator emits `mismatch_count` and lineage refs (observe-only).
2. `S1 dual-write`: strict update emits canonical semantic fields consumed by three-plane/full-scan.
3. `S2 fail-close`: enable `IP-SEM-CONV-001` only after root/tmp parity is stable for two consecutive runs.
4. `S3 intake hard-gate`: automated validator enforces `T1..T4` presence and metadata completeness.
5. `S4 baseline guard`: keep lane split + kernel write-boundary lock unchanged during `S0..S3`.

Promotion boundary (hard):

1. This fix is docs/governance normalization intake only; it does not promote requirement status by itself.
2. `ASB16-RQ-015/029/030` can move past `SPEC_READY` only after implementation + strict replay evidence under `S0..S3`.
3. Any claim of `DONE` without executable convergence proof is invalid.

### FIX16-026 - base-repo-architect self-drive pilot for protocol-kernel prompt injection + multimodal verification uplift (`ASB16-RQ-031`)

- Status: `SPEC_READY`
- Goal: execute a real runtime self-drive pilot on `base-repo-architect` identity instance, import protocol-kernel contracts into prompt baseline, and verify whether executable lane quality is improved without crossing v1.5 boundary.

Pilot implementation (instance-level, no protocol script mutation in this step):

1. Prompt baseline upgrade:
   - file: `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/IDENTITY_PROMPT.md`
   - action: injected `identity/protocol/*` contract sources + explicit multimodal verification policy + actor-explicit strict-lane rule + v1.5/v1.6 scope split clause.
2. Runtime learning artifacts updated:
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/RULEBOOK.jsonl`
   - `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/TASK_HISTORY.md`

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
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
3. `T2 vendor` (local + official web re-check):
   - `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
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
   - this replay strengthens evidence quality only; executable convergence requirements (`ASB16-RQ-015/029/030/031`) remain implementation-pending.

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

1. mapping file not yet landed:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`
2. v1.6 validator skeletons not yet landed:
   - `scripts/validate_v16_unlock_formula.py`
   - `scripts/validate_v16_promotion_pipeline.py`
   - `scripts/validate_v16_outlet_matrix.py`
   - `scripts/validate_v16_sidecar_cwd_parity.py`
3. scanner-computed lock script anchor not yet landed:
   - expected class: `scripts/validate_v16_lock_inventory*.py` (name TBD by architect implementation).

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

1. `T1 roundtable`: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
2. `T2 vendor`: `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
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
   - candidate validator references in pack creation include files not yet landed, which is a hard blocker:
     - `scripts/validate_identity_feedback_freshness.py` (missing),
     - `scripts/validate_identity_feedback_promotion.py` (missing).
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
| ASB16-RQ-017 | `PARTIAL` | governance/review contract exists; scripts only provide distributed checks, not single four-track quorum verdict | canonical parser must be single-source: `scripts/validate_v16_intake_evidence_core.py --mode intake_contract`; optional wrapper `scripts/validate_v16_cross_verification_tracks.py` may only delegate; enforce call chain `identity_creator.py` -> `release_readiness_check.py` -> `report_three_plane_status.py`/`full_identity_protocol_scan.py` -> `e2e_smoke_test.sh`; canonical fields must include `t1_status/t2_status/t3_status/t4_status` + metadata quartet | all tracks + metadata present => `PASS_REQUIRED`; any missing track/metadata => deterministic `FAIL_REQUIRED` |
| ASB16-RQ-018 | `PARTIAL` | monotonic dedup validator/wrapper landed, but deterministic positive+negative replay evidence for same `run_id` concurrency still missing | keep canonical path `scripts/validate_v16_dedup_monotonicity.py` (delegating to semantic core); keep hooks active in creator/readiness/three-plane/full-scan/e2e/ci; add replay artifacts proving stable winner tuple under repeated parallel claims | unchanged concurrent replay keeps identical `winner_id` tuple and `monotonicity_status=PASS_REQUIRED` |
| ASB16-RQ-019 | `PARTIAL` | cross-workflow normalizer + schema validator landed and are lane-wired; replay evidence closure still pending | keep canonical pair `scripts/normalize_v16_cross_workflow_evidence.py` + `scripts/validate_v16_cross_workflow_schema.py`; preserve creator/readiness/three-plane/full-scan/e2e/ci consumption on canonical fields only | `run_id/route_action/quality_meta_state/dedup_state/evidence_hash` always present and hash-stable |
| ASB16-RQ-020 | `PARTIAL` | skill-path integrity validator landed and lane-wired; strict layout replay matrix (in-layout pass/out-of-layout fail) still pending archive closure | keep `scripts/validate_v16_skill_path_integrity.py` as single fail-close gate; retain capability-activation as source-only data; enforce same verdict in creator/readiness/three-plane/full-scan/e2e/ci | any out-of-layout/missing skill path fails deterministically with canonical path-integrity code |
| ASB16-RQ-021 | `PARTIAL` | emitter-before-gate sequence is now implemented, but full-chain replay evidence for required=true pinning scenarios remains incomplete | keep emitter-first (`scripts/emit_route_version_pin_receipt.py`) then gate (`scripts/validate_route_version_pinning.py`); retain creator/readiness/three-plane/full-scan/e2e/ci hooks; add deterministic mismatch replay archive | pin proof required for pass; endpoint-version mismatch must fail-close with canonical pin error code |

Batch-6 five-link anchor lock (mandatory per row):

1. Each row must provide `kernel_ref + runtime_ref + mapping_ref + validator_ref + acceptance_cmd`.
2. Missing any anchor keeps row `ACCEPT_WITH_FIX` and non-promotional.
3. `FIX16-035` rolling summary row, detail section, and decision-log row must remain synchronized.
4. Mapping asset absence (`identity/protocol/mappings/contract-binding.v1.6.yaml`) is a hard blocker and invalidates lock computation for Batch-6.

Batch-6 acceptance command set (normative target):

```bash
python3 scripts/validate_v16_intake_evidence_core.py \
  --mode intake_contract \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --bundle-id <BUNDLE_ID> \
  --operation readiness \
  --json-only

python3 scripts/validate_v16_dedup_monotonicity.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --run-id <RUN_ID> \
  --parallel-claims 5 \
  --json-only

python3 scripts/validate_v16_cross_workflow_schema.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation three-plane \
  --json-only

python3 scripts/validate_v16_skill_path_integrity.py \
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
| ASB16-RQ-030 | `PARTIAL` | canonical parser + wrapper + lane hooks landed, but quorum replay evidence for required=true bundles remains incomplete | keep canonical parser `scripts/validate_v16_intake_evidence_core.py --mode promotion_gate`; wrapper `scripts/validate_v16_intake_evidence_quorum.py` delegates only; maintain single fail-close entrypoint in creator/readiness/three-plane/full-scan/e2e/ci | any missing track (`T1..T4`) or missing metadata (`bundle_id/source_url_set/reference_timestamp_utc/conflict_note`) blocks with deterministic fail code |

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

python3 scripts/validate_v16_intake_evidence_core.py \
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
   - `validate_v16_intake_evidence_core.py` with `--mode intake_contract|promotion_gate`.
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
  --source-layer local \
  --actor-id assistant:codex \
  --force-check \
  --json-only

python3 scripts/validate_protocol_entry_candidate_bridge.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --source-layer local \
  --force-check \
  --json-only

python3 scripts/validate_protocol_inquiry_followup_chain.py \
  --catalog <LOCAL_CATALOG> \
  --identity-id <ID> \
  --operation update \
  --source-layer local \
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

---

## 4) Reviewer decision log

| Fix ID | Audit Decision | Reviewer | Reviewed At (UTC) | Notes |
| --- | --- | --- | --- | --- |
| FIX16-001 | PENDING_REVIEW | audit-expert(codex) | - | bootstrap created; waiting command-contract replay |
| FIX16-002 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-003 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-004 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-005 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-006 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-007 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-008 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-009 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-010 | PENDING_INTAKE | audit-expert(codex) | 2026-03-04T04:30:00Z | office-ops package triaged; mapping to `ASB16-RQ-009..013` recorded with v1.5/v1.6 split boundary |
| FIX16-011 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-012 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-013 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-014 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-015 | PENDING_INTAKE | audit-expert(codex) | 2026-03-04T05:20:00Z | SRA 001/002/003 packet triaged into `ASB16-RQ-014..017`; v1.5 boundary explicitly preserved |
| FIX16-016 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-017 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-018 | PENDING_INTAKE | - | - | requires implementation |
| FIX16-019 | PENDING_INTAKE | audit-expert(codex) | 2026-03-04T06:55:00Z | latest office-ops self-drive replay evidence ingested; new gaps mapped to `ASB16-RQ-018..022` |
| FIX16-020 | PENDING_INTAKE | audit-expert(codex) | 2026-03-04T08:45:00Z | discovery dual-track simulation ingested; apply-time `PASS_REQUIRED` with `0/3` coverage formalized into `ASB16-RQ-023..024` |
| FIX16-021 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T02:20:00Z | kernel-first baseline ingested; source-center drift and prompt-lineage gap formalized into `ASB16-RQ-025..028`; supplemental verdict confirms content-level alignment and keeps status caveat (`SPEC_READY/PENDING_INTAKE`) |
| FIX16-022 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T03:10:00Z | live replay confirms semantic convergence gap (`update green` + `IP-SEM-001` in aggregators); new requirement `ASB16-RQ-029` added; `A-D P0` and `E P1` priorities mapped to requirement set |
| FIX16-023 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T09:40:00Z | intake hard-gate reinforcement added: new suggestions require roundtable/vendor/online/spec evidence quorum (`ASB16-RQ-030`) before promotion beyond `PENDING_INTAKE` |
| FIX16-024 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T10:40:00Z | self-drive A/B replay shows prompt text import alone yields no executable uplift; added `ASB16-RQ-031` for fail-closed executable coupling + multimodal sample-proof closure + explicit actor context in strict lane; 2026-03-06 supplement confirms protocol layer should not add same-name `identity/protocol/IDENTITY_PROMPT.md`, requires contract-source -> compile-chain closure, and locks `identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md` as continuously updated kernel baseline source |
| FIX16-025 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T12:20:00Z | deep cross-verification package normalized to `T1..T4` taxonomy and replay verdict locked: lane split healthy but `ASB16-RQ-015/029/030` remain implementation-pending; `S0..S4` sequence added as non-regression strengthening path |
| FIX16-026 | PENDING_INTAKE | base-repo-architect(self-drive) | 2026-03-05T12:58:00Z | runtime self-drive pilot on `base-repo-architect`: protocol-kernel prompt injection + multimodal verification baseline passes; creator strict chain still shows actor-context convergence residual (`IP-ASB-STAMP-SESSION-005`), kept in v1.6 executable-coupling track only |
| FIX16-027 | PENDING_INTAKE | base-repo-architect | 2026-03-05T14:20:00Z | final T1/T2/T3/T4 cross-verification replay executed with network/vendor/spec re-check; direction reaffirmed, but `ASB16-RQ-015/017/029/030/031` remain `SPEC_READY` pending executable closure |
| FIX16-028 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-05T22:10:00+08:00 | full-repo lock census + architect independent deep-rescan receipt completed (`/tmp/v16_architect_independent_deep_rescan_receipt_20260305.log`, `/tmp/v16_architect_deep_scan_full_repo_20260305.json`, `/tmp/v16_one_by_one_requirement_review_20260305.md`): `BRIDGE_LOCKED=32/32`, `KERNEL_LOCKED=0/32`, `SCRIPT_LOCKED=0/32`, `FULL_LOCKED=0/32`; row-level audit can proceed, promotion remains blocked |
| FIX16-029 | PENDING_INTAKE | audit-expert(codex) | 2026-03-05T16:05:00Z | headstamp recurrence elevated to P0 transport-gate gap: new `ASB16-RQ-032` requires pre-send hard-blocking for all outbound paths with deterministic fail-close (`IP-HDSTAMP-001/002/003`) before promotion |
| FIX16-030 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-05T16:40:00Z | Batch-1 (`ASB16-RQ-001..005`) strengthening normalized into enforceable P0 constraints; row-level decision=`ACCEPT_WITH_FIX` only, pending kernel/script/mapping anchor closure per governance `8.5` |
| FIX16-031 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-06T00:00:00Z | Batch-2A (`ASB16-RQ-006..010`) strengthening normalized with naming split and homomorphism assertions; all rows remain `ACCEPT_WITH_FIX` and non-promotional pending kernel/script/mapping closure per governance `8.6` |
| FIX16-032 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-06T08:30:00Z | Batch-3B (`ASB16-RQ-024..028`) strengthening normalized: RQ-024 error-code semantic deconflict + apply-coverage hard-close default-on requirement; kernel-first source/mapping/prompt-derivation/write-boundary cluster remains `ACCEPT_WITH_FIX` only and non-promotional pending executable closure per governance `8.7` |
| FIX16-033 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-06T14:20:00Z | Batch-4 (`ASB16-RQ-029/031/032/007/008`) four-track strengthening normalized with `T1..T4` evidence guard, row-level homomorphism predicates, hard-tightening addendum (`RQ-032` canonical `IP-HDSTAMP-*`, `RQ-029` convergence comparator outputs, `RQ-031` compile/runtime metadata + actor-explicit fail-close, `RQ-007` full-chain replay, `RQ-008` checker required), and actor-id fallback recurrence supplement (missing explicit actor can resolve to host `user:*` binding and trigger compatibility mismatch trace); all rows remain `ACCEPT_WITH_FIX` and non-promotional pending executable closure per governance `8.8` |
| FIX16-034 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-06T16:40:00Z | Batch-5 (`ASB16-RQ-010/011/012/013/016`) orchestration strengthening normalized: readiness two-phase parity requirement + tmp collision-safe allocator contract + handoff/collab auto-rotation closure (missing validator files treated as hard blocker) + protocol-feedback atomic emit transactionality + refresh/strict interference matrix receipts (field-gap lock, mapped to `FIX16-017`); all rows remain `ACCEPT_WITH_FIX` and non-promotional pending executable closure per governance `8.9` |
| FIX16-035 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-06T19:20:00Z | Batch-6 (`ASB16-RQ-017/018/019/020/021`) post-audit hardening absorbed as `PASS_WITH_BLOCKERS`: mapping asset, single-parser dual-mode intake core, emitter-before-gate sequencing, and coverage/aggregator wiring are now implemented and lane-hooked (`creator/readiness/three-plane/full-scan/e2e/ci`) via commits `9e59e0f..47f2f38`; follow-up hardening (`Task-15`, `1beeb88`) closed dedup path-lock + UTC determinism blockers to `PASS_REQUIRED`; batch remains `ACCEPT_WITH_FIX` and non-promotional until deterministic replay archive closure per governance `8.10` |
| FIX16-036 | PASS_WITH_BLOCKERS | base-repo-architect + audit-expert(codex) | 2026-03-06T19:25:00Z | Batch-7 (`ASB16-RQ-022/030`) post-audit hardening absorbed as `PASS_WITH_BLOCKERS`: dual-field taxonomy normalization + intake core promotion mode are implemented and lane-hooked (`creator/readiness/three-plane/full-scan/e2e/ci`) via commits `f63eb55..47f2f38`; follow-up synchronization (`Task-13/15`, `b258982 + 1beeb88`) aligned status semantics and blocker posture; both rows remain `ACCEPT_WITH_FIX` and non-promotional until required=true replay closure per governance `8.11` |
| FIX16-037 | PENDING_INTAKE | base-repo-architect + audit-expert(codex) | 2026-03-06T20:10:00Z | Write-boundary non-starvation hardening absorbed for `ASB16-RQ-028/031`: lane-scoped boundary semantics locked, protocol-entry liveness channels explicitly preserved, no-silent-downgrade fail-close mapped to canonical lane/candidate code families, telemetry tuple + replay matrix elevated to mandatory promotion gate; remains `ACCEPT_WITH_FIX` and non-promotional pending executable closure per governance `8.12` |

---

## 5) Current release posture snapshot (v1.6 kickoff)

1. `v1.6` release status: `NO_GO` (kickoff baseline).
2. Blocking class currently visible in live project replay: `IP-CAP-003` (env/auth preflight).
3. Required external reporting posture:
   - `IMPL_READY (BLOCKED_BY_ENV_AUDIT)`
4. This posture remains until:
   - env/auth blocker closure is replay-proven, and
   - v1.6 unlock formula conditions are satisfied.

---

## 6) References

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
3. `docs/review/protocol-remediation-audit-ledger-v1.5.md`
4. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
5. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_001.md`
6. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_002.md`
7. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_003.md`
8. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/evidence-index/INDEX.md`
9. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/to-identity-base-architect-brief-2026-03-04-initial-prompt-base-contract-capability-and-business-impact.md`
10. `/Users/yangxi/claude/codex_project/cqsw/governance/protocol-issue-reports/identity-prompt-initial-base-contract-capability-roundtable-2026-03-04.md`
11. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-01_official-vibe-coding-playbook.md`
12. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_SCAN_2026-03-02_official-cross-verification-work-layer.md`
13. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
14. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
15. `https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide/#frequented-asked-questions-faq`
16. `context7:/websites/developers_openai_api`
17. `/Users/yangxi/claude/codex_project/ddm/docs/governance/identity-protocol-feedback-office-ops-self-drive-regression-v2026-03-04.md`
18. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-04_004.md`
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
43. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_2026-03-05_001.md`
44. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/issues/ISSUE_2026-03-05_update-threeplane-semantic-convergence-gap.md`
45. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/upgrade-proposals/PROPOSAL_2026-03-05_semantic-single-source-and-convergence-gate.md`
46. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/protocol-feedback/roundtables/ROUNDTABLE_2026-03-05_semantic-convergence-and-dual-lane-governance.md`
47. `/Users/yangxi/.codex/identity/instances/system-requirements-analyst/runtime/reports/identity-upgrade-exec-system-requirements-analyst-1772691244.json`
48. `/tmp/three_plane_system_requirements_analyst_20260305_replay2.json`
49. `/tmp/full_scan_system_requirements_analyst_20260305_replay2.json`
50. `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/IDENTITY_PROMPT.md`
51. `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/RULEBOOK.jsonl`
52. `/Users/yangxi/claude/codex_project/weixinstore/.agents/identity/base-repo-architect/TASK_HISTORY.md`
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
