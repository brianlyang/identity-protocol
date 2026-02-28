# Identity Actor-Scoped Session Binding Governance (v1.5.0)

Status: Draft (P0 remediation directive)  
Governance layer: protocol  
Scope: identity protocol base-repo only (no instance business policy)  
Owner: identity protocol base-repo architect
Execution mode: topic-level canonical SSOT for actor-session-binding governance  
Tag policy: `v1.5` remains locked until mandatory requirement ledger rows are `DONE` and audit sign-off is `PASS`

## 0) Governance Execution Mode and Release Lock (Mandatory)

### 0.1 Single execution entrypoint (topic SSOT)

1. This document is the only normative execution entrypoint for actor-session-binding governance.
2. `artifacts/**` and ad-hoc issue notes are evidence-only; they cannot override this document.
3. No same-topic parallel normative document is allowed.

### 0.2 SSOT layering relationship (to avoid ambiguity)

1. This file is **topic-canonical** for actor-session-binding governance.
2. `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` remains **global protocol execution SSOT**.
3. Core code changes from this topic must synchronize:
   - topic SSOT (`v1.5.0` actor-session-binding), and
   - global execution handoff (`v1.4.13` canonical handoff).

### 0.3 Release lock table (`v1.5` tag is hard-locked)

| Decision Gate | Unlock condition | Current state |
| --- | --- | --- |
| D1 Contract freeze | Contracts/fields/error semantics finalized in this doc | OPEN |
| D2 Implementation complete | Mandatory scripts/validators/tools landed | OPEN |
| D3 Gate wiring complete | creator/e2e/readiness/full-scan/three-plane/CI wired | OPEN |
| D4 Acceptance pass | Mandatory acceptance command set green | OPEN |
| D5 Audit sign-off | Architect + audit expert both PASS | OPEN |
| D6 Tag allowed | D1~D5 all PASS | LOCKED |

### 0.4 Requirement status model (machine-readable governance semantics)

Allowed status values:

1. `SPEC_READY` — requirement finalized in governance, implementation not complete.
2. `IMPL_READY` — implementation landed but not fully wired.
3. `GATE_READY` — implementation + gate wiring landed.
4. `VERIFIED` — acceptance commands pass with evidence.
5. `DONE` — verified and audit accepted for release gating.

Compatibility note (to avoid legacy ambiguity):

1. Historical `CODE_READY` is treated as alias of `IMPL_READY`.
2. New governance updates must use `IMPL_READY` as canonical status text.

Hard rule:

1. Any `P0`/`P1` requirement not reaching `DONE` keeps `v1.5` tag locked.

### 0.5 Baseline snapshot (normative as-of checkpoint)

As-of baseline:

1. `as_of_utc`: `2026-02-28`
2. `protocol_repo_head`: `f3d4836`
3. `topic_status`: governance specification substantially complete; runtime implementation not closed.

Normative interpretation:

1. This topic is not allowed to be declared `implemented` while requirement ledger rows remain `SPEC_READY`.
2. `SPEC_READY` coverage means governance direction is usable; it does not satisfy runtime closure claims.

Hard evidence (repository-local):

1. Topic P0 framing and explicit non-safe state:
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:54`
   - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md:97`
2. Runtime still enforces single-active semantics (conflicts with multi-actor target):
   - `scripts/identity_creator.py:150`
   - `scripts/identity_installer.py:253`
   - `scripts/validate_identity_state_consistency.py:44`
   - `scripts/validate_identity_session_pointer_consistency.py:124`
   - `scripts/sync_session_identity.py:21`
3. Required actor scripts declared but not yet landed:
   - `validate_actor_session_binding`
   - `validate_no_implicit_switch`
   - `validate_cross_actor_isolation`
   - `render_identity_response_stamp`
   - `validate_identity_response_stamp`
   - `refresh_identity_session_status`

## 1) Problem Statement (P0)

Current protocol runtime still uses catalog-level single-active identity semantics as the default control primitive.
Under multi-actor execution (subagent, parallel Codex windows, external runners), this creates implicit context override risk.

Observed failure pattern:

1. Actor-A activates identity-X.
2. Actor-B activates identity-Y in the same catalog domain.
3. Actor-A context is implicitly overwritten by single-active pointer state.

This is a protocol model issue, not an instance business policy issue.

## 2) Non-Negotiable Layer Boundary

Protocol layer responsibilities:

1. Binding model, contracts, validators, gate wiring, migration policy.
2. Canonical governance documents and SSOT lifecycle.
3. Health/self-heal control-plane tooling.

Instance layer responsibilities:

1. Business policy, scene anchors, thresholds, strategy weights.
2. Runtime content in `CURRENT_TASK.json` and per-instance artifacts.

Hard rules:

1. No business data is allowed as protocol gate criteria.
2. Protocol changes must be machine-verifiable and replayable.
3. Skill-trigger semantics follow skill protocol reference:
   - no implicit cross-turn carry,
   - explicit trigger/rematch required,
   - registry-driven routing must be reproducible.

## 3) Cross-Validation Summary (Roundtable Synthesis + Vendor + Skill Protocol)

### 3.1 Protocol implementation evidence (local repository)

Current single-active coupling is enforced in:

1. `scripts/identity_creator.py` (`_single_active_precheck`, activation demotion).
2. `scripts/validate_identity_state_consistency.py` (fails when active identities > 1).
3. `scripts/validate_identity_session_pointer_consistency.py` (expects single active row + canonical pointer).
4. activation/session-pointer sync routine in `scripts/identity_creator.py` (writes canonical pointer by active identity).

Conclusion: current default model is not multi-actor safe.

### 3.2 Vendor/spec parity evidence

Design references for actor/session-scoped isolation:

1. Kubernetes Lease (`holderIdentity`, lease lifecycle).
2. Redis lock pattern (`SET ... NX PX`, owner-token release script).
3. GitHub Actions concurrency groups (keyed isolation).
4. OpenAI/Anthropic/Gemini/MCP tool loops (explicit tool-call + result propagation).

Conclusion: protocol must move from global single-active semantics to actor-scoped binding semantics.

### 3.3 Skill protocol alignment

References:

1. `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`
2. `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`

Alignment points:

1. Mandatory layer split: identity / skill / mcp / tool runtime.
2. Multi-agent handoff must use explicit structured payloads.
3. Registry-based routing decisions must be reproducible, not implicit.

### 3.4 Cross-validation boundary declaration (anti-misrepresentation)

1. Vendor/spec alignment in this document is an engineering synthesis against public specifications and official documentation.
2. It is not a claim of direct vendor architect participation.
3. Any statement about external parity must reference concrete spec/docs links listed in section 12.
4. Skill protocol alignment is normative for runtime trigger/handoff semantics and must remain independent from instance business data.

## 4) Governance Targets (Mapped to P0 Closure Requirements)

| Requirement | Protocol governance target | Mandatory output |
| --- | --- | --- |
| 1. Standard governance doc + cleanup mixed info | Single canonical SSOT under `docs/governance/` and artifacts demoted to evidence-only | Canonical doc + SSOT validator pass |
| 2. Deep protocol remediation + cross-validation | Replace single-active runtime semantics with actor-scoped binding | New contracts + validators + gate wiring |
| 3. Instance health-check and heal | Health tooling must detect binding drift and provide repair path | health -> heal -> validate closure |
| 4. Dynamic response identity stamp (non-hardcoded) | Introduce runtime-generated response stamp contract | Dynamic stamp renderer + validator |
| 5. Self-check + refresh anytime | Add actor session refresh and status snapshot | refresh command + three-plane visibility |
| 6. Vendor/API discovery + solution governance | Enforce non-hardcoded example semantics and shot-mode policy | discovery/solution/coverage evidence + manual-review fallback |
| 7. Protocol-kernel capability evolution | Promote shot-mode + evidence chain from vendor-only to protocol-kernel model | unified capability lifecycle contract + cross-capability coverage semantics |

## 5) Protocol Contract Additions (Mandatory)

### 5.1 `actor_session_binding_contract_v1`

Minimum required fields:

1. `actor_id`
2. `actor_type` (`codex_window` | `subagent` | `runner`)
3. `identity_id`
4. `catalog_path`
5. `resolved_pack_path`
6. `scope`
7. `lease_id`
8. `lease_expires_at`
9. `lock_state`
10. `updated_at`

Storage contract:

1. Canonical binding records: `<catalog_dir>/session/actors/<actor_id>.json`
2. Legacy `active_identity.json` remains compatibility mirror only during migration.

### 5.2 `identity_response_stamp_contract_v1`

Every user-facing response must include runtime-generated stamp fields (header line or structured block):

1. `actor_id`
2. `identity_id`
3. `catalog_path`
4. `resolved_pack_path`
5. `scope`
6. `lock_state`
7. `lease_id` (full or shortened)

Hard rules:

1. Stamp must be generated from live binding context.
2. Hardcoded identity literals are forbidden.

Display safety boundary (mandatory):

1. External/user-facing stamp output must not expose host absolute paths directly.
2. Internal evidence view may include `catalog_path` / `resolved_pack_path`, but default external view should emit redacted references:
   - `catalog_ref`
   - `pack_ref`
   - `scope`
   - `lease_id_short`
3. Absolute path fields are reserved for audit logs/reports and validator consumption.

Canonical stamp format (example template, placeholders must be runtime-resolved):

1. `Identity-Context: actor_id=<actor_id>; identity_id=<identity_id>; catalog=<catalog_path>; pack=<resolved_pack_path>; scope=<scope>; lock=<lock_state>; lease=<lease_id_short>`
2. If structured output is used, the same fields must be present under a dedicated `identity_context` object.

### 5.3 `identity_health_self_heal_contract_v1`

Health report must include actor-binding risk classes:

1. binding mismatch
2. lease stale
3. implicit switch risk
4. pointer drift

Self-heal output must include deterministic remediation actions and re-validation commands.

### 5.4 `vendor_api_discovery_solution_contract_v1`

This capability is protocol-generic and must not be implemented as scattered business scripts.

#### 5.4.1 Normative target state

1. Vendor/API references in protocol-level docs/contracts are example-driven and non-hardcoded.
2. Tier model is explicit:
   - Tier-1: official machine-readable spec/discovery source.
   - Tier-2: official human-readable documentation.
   - Tier-3: community source (candidate only).
3. Without Tier-1 (or approved equivalent), status must be `manual_review`; auto-activation is forbidden.
4. Required evidence fields:
   - `actor_id`
   - `run_id`
   - `source_tier`
   - `spec_hash`
   - `spec_ref`
5. Shot-mode is explicit:
   - `shot_mode` in `{zero_shot, one_shot, multi_shot}`
   - `shot_sample_count` present and auditable.
6. One-shot closure means one validation chain determines pass/fail for:
   - discovery
   - solution selection
   - required coverage semantics
7. Policy by shot mode:
   - `zero_shot`: allowed only when Tier-1 evidence is complete and risk class is low/controlled.
   - `one_shot`: default mode for normal protocol closure replay.
   - `multi_shot`: required when Tier-1 evidence is incomplete, conflict risk is elevated, or prior one-shot replay is unstable.
8. Shot-mode execution referencing fixed vendor/API constants in protocol contract text is invalid.

Risk class criteria (to remove ambiguity):

1. `low`: read-only surface, no privileged write scopes, no PII export, explicit Tier-1 machine-readable contract, deterministic fallback.
2. `controlled`: not fully low-risk but has `approval_receipt_ref`, explicit rollback, explicit fallback route, and bounded rate-limit strategy.
3. Any class outside `low` or `controlled` cannot use `zero_shot`.

#### 5.4.2 Compatibility mapping (to current scripts/contracts)

Current scripts still validate legacy fields in:

1. `vendor_api_discovery_contract.required_report_fields`
2. `vendor_api_solution_contract.required_report_fields`
3. `attach_readiness_decision` state machine (`ready` | `defer` | `blocked`)

Compatibility rules to avoid semantic drift:

1. `manual_review` must map to `attach_readiness_decision in {defer, blocked}` plus explicit `manual_review_reason`.
2. `shot_mode`, `shot_sample_count`, `source_tier`, `spec_hash`, `spec_ref` are required governance fields in target state.
3. Before validator upgrade lands, missing shot-mode fields are `WARN` (governance gap), not silent pass.
4. Validator upgrade milestone must harden these as strict required fields.
5. Governance WARN must be tracked with an issue id and closure owner; silent WARN is invalid.

#### 5.4.3 Approved-equivalent criteria (for Tier-1 fallback)

`approved_equivalent` is valid only when all conditions are met:

1. Source is vendor-owned or standards-body-owned.
2. Response schema or endpoint contract is machine-readable and hashable.
3. Authentication mode and scope boundaries are explicitly documented.
4. Versioning and deprecation policy are discoverable.
5. Evidence includes approval receipt (`approval_receipt_ref`) and reviewer actor identity.

#### 5.4.4 Non-hardcoded policy examples

1. Allowed in governance/template text: `<vendor>`, `<api_family>`, `<spec_ref>`.
2. Forbidden as protocol norm: business-scene vendor names as mandatory constants.
3. Zero-shot/one-shot/multi-shot examples are templates, not fixed vendor mappings.

#### 5.4.5 Field-location contract (avoid implementation drift)

Shot and provenance fields must be persisted at report top-level (not only in free-text notes):

1. Discovery report (`vendor-api-discovery-*.json`):
   - `shot_mode`
   - `shot_sample_count`
   - `source_tier`
   - `spec_hash`
   - `spec_ref`
   - `manual_review_reason` (required when readiness is defer/blocked due to source tier constraints)
2. Solution report (`vendor-api-solution-*.json`):
   - `shot_mode`
   - `shot_sample_count`
   - `selected_source_tier`
   - `selected_spec_hash`
   - `selected_spec_ref`
3. Coverage output (`validate_required_contract_coverage`) must surface status classification for these contracts and reason codes.

### 5.5 `capability_evolution_kernel_contract_v1` (Protocol Internal Core)

Goal:

1. Do not limit shot-mode + evidence governance to vendor/API only.
2. Promote the same mechanism as protocol-kernel behavior across capability domains.

Applies to capability domains:

1. `identity_prompt`
2. `skill`
3. `mcp`
4. `tool`
5. `vendor_api`
6. `policy_rule`

#### 5.5.1 Unified lifecycle stages

Every capability change must follow:

1. `discover`
2. `propose`
3. `verify`
4. `bind`
5. `observe`
6. `learn`

Hard rule:

1. No direct `bind` without `verify` evidence.
2. No `done` without `observe` + `learn` writeback record.

#### 5.5.2 Unified evidence envelope

Each capability-upgrade event must emit a machine-readable envelope with required fields:

1. `capability_type`
2. `capability_id`
3. `change_intent`
4. `actor_id`
5. `run_id`
6. `source_tier`
7. `shot_mode`
8. `shot_sample_count`
9. `risk_class`
10. `verification_evidence_refs`
11. `decision_ref`
12. `fallback_ref`
13. `rollback_ref`
14. `protocol_commit_sha`
15. `result_status`

#### 5.5.3 Kernel shot-mode policy (generic, not vendor-only)

1. `zero_shot`:
   - only when risk class is `low` or `controlled`,
   - with complete Tier-1 (or approved-equivalent) evidence,
   - and deterministic fallback/rollback.
2. `one_shot`:
   - default mode for routine capability evolution closure.
3. `multi_shot`:
   - required for elevated-risk, unstable replay history, or partial source confidence.

#### 5.5.4 Cross-capability coverage semantics

Coverage is no longer interpreted per single domain only.
Protocol must expose both:

1. domain-level coverage (e.g., vendor_api only),
2. kernel-level coverage (across selected capability domains).

Status taxonomy:

1. `PASS_REQUIRED`
2. `SKIPPED_NOT_REQUIRED`
3. `FAIL_REQUIRED`
4. `FAIL_OPTIONAL`

Interpretation rule:

1. `SKIPPED_NOT_REQUIRED` is visibility state, not equivalent to pass.
2. Kernel-level dashboard must show `required_total`, `required_passed`, `coverage_rate`, and `skipped_count`.

#### 5.5.5 Non-hardcoded policy for all capability domains

1. Protocol text must use placeholders and schema contracts, not business-scene constants.
2. Examples are illustrative only; examples cannot become implicit production defaults.
3. Capability binding decisions must be derived from contract fields and evidence, not from script-local hardcoded mappings.

## 6) Required Protocol Changes

### 6.1 Core script change surface

1. `scripts/identity_creator.py`
2. `scripts/resolve_identity_context.py`
3. activation/session-pointer sync routine in `scripts/identity_creator.py`
4. `scripts/validate_identity_state_consistency.py`
5. `scripts/validate_identity_session_pointer_consistency.py`

### 6.2 New validators/tools (validator id and tool id)

1. `validate_actor_session_binding`
2. `validate_no_implicit_switch`
3. `validate_cross_actor_isolation`
4. `render_identity_response_stamp`
5. `validate_identity_response_stamp`
6. `refresh_identity_session_status`

### 6.3 Gate wiring surfaces

1. `scripts/identity_creator.py validate`
2. `scripts/e2e_smoke_test.sh`
3. `scripts/release_readiness_check.py`
4. `scripts/full_identity_protocol_scan.py`
5. `scripts/report_three_plane_status.py`
6. `.github/workflows/_identity-required-gates.yml`

Vendor/API chain must be wired in the same surfaces through:

1. `scripts/validate_identity_vendor_api_discovery.py`
2. `scripts/validate_identity_vendor_api_solution.py`
3. `scripts/validate_required_contract_coverage.py`

Kernel extension requirement:

1. The same coverage and evidence semantics must be gradually extended to `skill` / `mcp` / `tool` capability validators and release surfaces.
2. Migration must keep current vendor/tool gates backward-compatible while introducing kernel-level aggregation outputs.

### 6.4 Requirement ledger (canonical tracker for `v1.5` unlock)

| Requirement ID | Requirement summary | Code surface / validator | Blocking level | Current status | Evidence ref / notes |
| --- | --- | --- | --- | --- | --- |
| ASB-RQ-001 | actor session binding contract schema + storage contract (`session/actors/<actor_id>.json`) | `resolve_identity_context.py`, activation/session pointer sync routine | P0 | SPEC_READY | Spec defined in 5.1; code pending |
| ASB-RQ-002 | dual-write migration (actor pointer + legacy mirror) | activation/session pointer mirror routine, migration utilities | P0 | SPEC_READY | Phase A defined; code pending |
| ASB-RQ-003 | validator: actor session binding integrity | `validate_actor_session_binding` (new) | P0 | SPEC_READY | Command declared; script pending |
| ASB-RQ-004 | validator: no implicit switch across actors | `validate_no_implicit_switch` (new) | P0 | SPEC_READY | Command declared; script pending |
| ASB-RQ-005 | validator: cross-actor isolation | `validate_cross_actor_isolation` (new) | P0 | SPEC_READY | Command declared; script pending |
| ASB-RQ-006 | dynamic response stamp renderer (redacted external view + internal evidence view) | `render_identity_response_stamp` (new) | P0 | SPEC_READY | Display safety boundary defined in 5.2 |
| ASB-RQ-007 | response stamp validator + CI enforcement | `validate_identity_response_stamp` (new), required-gates | P0 | SPEC_READY | Validator/gate pending |
| ASB-RQ-008 | refresh command for live actor binding status | `refresh_identity_session_status` (new) | P1 | SPEC_READY | three-plane visibility binding pending |
| ASB-RQ-009 | mandatory gate wiring across creator/e2e/readiness/full-scan/three-plane/CI | multiple surfaces listed in 6.3 | P0 | SPEC_READY | Wiring pending |
| ASB-RQ-010 | single-active removal from activation/consistency path | `identity_creator.py`, `identity_installer.py`, `validate_identity_state_consistency.py`, `validate_identity_session_pointer_consistency.py`, `compile_identity_runtime.py` | P0 | SPEC_READY | Current repo still has single-active checks |
| ASB-RQ-011 | vendor discovery/solution baseline gates (legacy chain) remain wired and compatible | `validate_identity_vendor_api_discovery.py`, `validate_identity_vendor_api_solution.py`, `validate_required_contract_coverage.py` | P1 | GATE_READY | Existing chain already wired in protocol gates |
| ASB-RQ-012 | shot-mode/source-tier/spec-hash strict enforcement (vendor reports) | same validators as ASB-RQ-011 | P1 | SPEC_READY | Spec declared in 5.4; current validators not strict on these fields |
| ASB-RQ-013 | kernel-level capability evolution coverage aggregation | new kernel-level coverage surfaces | P1 | SPEC_READY | Spec declared in 5.5; implementation pending |

### 6.5 v1.5 unlock formula (release-lock hard rule)

`v1.5` tag unlock condition:

1. `unlock_allowed = true` iff all `P0` rows in section 6.4 are `DONE` and D1~D5 in section 0.3 are `PASS`.

Non-equivalence constraints:

1. `SPEC_READY != IMPL_READY`
2. `IMPL_READY != GATE_READY`
3. `GATE_READY != DONE`
4. Passing a subset of ad-hoc commands cannot override the formula above.

Audit output requirement:

1. Every architect return must include explicit calculation evidence for unlock formula inputs, not just narrative conclusions.

## 7) SSOT and Mixed-Source Cleanup Policy

Mandatory policy:

1. This document is canonical for actor-scoped binding governance.
2. Any `artifacts/**` note is evidence-only (non-normative).
3. Same-topic parallel normative documents are disallowed.
4. Topic-canonical status here does not override global execution SSOT ownership in `identity-protocol-strengthening-handoff-v1.4.13.md`.

Required cleanup actions:

1. Add canonical link in `README.md` and `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
2. Mark conflicting old notes as `superseded` or `evidence-only`.
3. Enforce via `scripts/validate_protocol_ssot_source.py`.

## 8) Migration Plan (No-Break Strategy)

### Phase A (dual-write)

1. Write actor pointers and legacy pointer mirror together.
2. Read path remains backward compatible.

### Phase B (actor-first read)

1. Runtime resolution prefers actor pointer.
2. Legacy pointer is warning/compatibility only.

### Phase C (strict enforcement)

1. `--actor-id` required in protocol-critical flows.
2. Ambiguous resolution without actor binding fails closed.

### Phase D (legacy removal)

1. Remove single-active assumptions from validators and activation paths.
2. Keep migration utility for historical reports.

### 8.1 Error semantics (fail-operational vs fail-closed)

Error code family: `IP-ASB-*`

Fail-closed (hard boundary):

1. `IP-ASB-PATH-001` actor pointer path boundary violation.
2. `IP-ASB-AUTH-001` actor identity spoofing / signature mismatch.
3. `IP-ASB-SCOPE-001` forbidden cross-scope actor binding write.

Fail-operational (recoverable blocked/warn):

1. `IP-ASB-BIND-001` actor binding missing.
2. `IP-ASB-LEASE-001` lease stale or expired.
3. `IP-ASB-MIRROR-001` legacy mirror drift while canonical actor binding remains valid.

Hard rule:

1. Recoverable actor-binding failures must not be silently promoted to hard-fail unless they cross hard-boundary conditions.

## 9) Acceptance Command Set (Cross-Validation)

```bash
# SSOT / coupling
python3 scripts/validate_protocol_ssot_source.py
python3 scripts/validate_protocol_handoff_coupling.py --base <base_sha> --head <head_sha>

# Health -> heal -> validate loop
python3 scripts/collect_identity_health_report.py --identity-id <id> --catalog <catalog> --out-dir /tmp/identity-health-reports
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog>
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog> --apply
python3 scripts/identity_creator.py validate --identity-id <id> --catalog <catalog>
python3 scripts/resolve_identity_context.py resolve --identity-id <id> --local-catalog <catalog>

# Vendor/API one-shot closure (current validator chain)
python3 scripts/validate_identity_vendor_api_discovery.py --identity-id <id> --catalog <catalog>
python3 scripts/validate_identity_vendor_api_solution.py --identity-id <id> --catalog <catalog>
python3 scripts/validate_required_contract_coverage.py --identity-id <id> --catalog <catalog> --json-only

# Three-plane visibility
python3 scripts/report_three_plane_status.py --identity-id <id> --catalog <catalog> --with-docs-contract
python3 scripts/full_identity_protocol_scan.py --scan-mode target --identity-ids <ids> --global-catalog <catalog>

# Docs command contract integrity
python3 scripts/docs_command_contract_check.py
```

Post-implementation command contract (must be enabled in same PR as script landing):

1. `validate_actor_session_binding` command + gate wiring.
2. `validate_no_implicit_switch` command + gate wiring.
3. `validate_cross_actor_isolation` command + gate wiring.
4. `render_identity_response_stamp` command + output contract.
5. `validate_identity_response_stamp` command + CI enforcement.
6. `refresh_identity_session_status` command + three-plane visibility.

## 10) Definition of Done (Split to Avoid False Closure)

### 10.1 Governance close (v1.5.0 document close)

All conditions must be true:

1. Canonical governance document exists and SSOT gates are green.
2. Layer boundary is explicit and non-ambiguous.
3. Vendor/API shot-mode + tier policy has compatibility mapping to current validators.
4. Non-hardcoded vendor/API rule is explicit and testable.
5. Required acceptance commands are runnable and documented.
6. Shot-mode and evidence-chain semantics are defined as protocol-kernel rules, not domain-only policy.

### 10.2 Runtime close (v1.5.x implementation close)

All conditions must be true:

1. Single-active coupling is removed from binding semantics.
2. Actor-scoped binding is enforced in activate/update/validate flow.
3. Multi-actor parallel execution no longer causes implicit identity switch.
4. Health tools detect and heal binding drift with replayable evidence.
5. Response stamp is dynamic and validator-enforced.
6. Status refresh command reports current actor binding deterministically.
7. e2e/readiness/full-scan/three-plane/required-gates all wired and green.
8. Vendor/API discovery-solution chain is one-shot verifiable under policy.
9. `zero_shot` / `one_shot` / `multi_shot` become validator-enforced fields.
10. Kernel-level capability evolution coverage is visible across `identity_prompt` / `skill` / `mcp` / `tool` / `vendor_api`.

### 10.3 Milestone assertion guard (mandatory wording)

When reporting status to any stakeholder, exactly one of the following assertions must be used:

1. `Governance baseline closed, runtime not closed` (allowed when section 10.1 satisfied and section 10.2 unsatisfied).
2. `Runtime milestone closed` (allowed only when section 10.2 satisfied).

Forbidden statement:

1. Any wording equivalent to `v1.5 implemented` while one or more P0 rows remain below `DONE`.

## 11) Architect Mandatory Reply Format

Use fixed reply schema:

1. commit sha list
2. changed file list
3. acceptance command outputs (rc + key tail lines)
4. residual risks + next milestone
5. layer declaration (`protocol`)

## 12) Official References (Vendor and Specification)

1. Kubernetes Lease concept  
   - https://kubernetes.io/docs/concepts/architecture/leases/
2. Redis distributed lock pattern  
   - https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
3. GitHub Actions concurrency  
   - https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency
4. OpenAPI specification (official)  
   - https://github.com/OAI/OpenAPI-Specification
5. GitHub official OpenAPI description repository  
   - https://github.com/github/rest-api-description
6. Google API Discovery documents  
   - https://developers.google.com/discovery/v1/building-a-client-library
7. OpenAI function calling and remote MCP  
   - https://platform.openai.com/docs/guides/function-calling  
   - https://platform.openai.com/docs/guides/tools-remote-mcp
8. Anthropic tool use and MCP connector  
   - https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use  
   - https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector
9. Gemini function calling  
   - https://ai.google.dev/gemini-api/docs/function-calling
10. MCP specification  
   - https://modelcontextprotocol.io/specification/2025-11-25/
11. Internal skill-governance references  
   - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`  
   - `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`

## 13) Roundtable Framing Note

This document is an engineering synthesis based on:

1. local protocol repository behavior,
2. official vendor/spec documentation,
3. internal skill-governance references.

It is not a transcript of direct human roundtable participation by vendor architects.

## 14) Repository Legacy-Residue Cleanup Program (Mandatory, Step-A/B/C)

Purpose:

1. Remove mixed legacy semantics (single-active / single-pointer assumptions) from protocol base-repo surfaces.
2. Prevent inconsistent implementation caused by partial memory or ad-hoc fixes.
3. Keep actor-scoped target model and repository-wide behavior aligned.

### 14.1 Step A — Semantic freeze and boundary declaration (must do first)

Scope:

1. Define legacy residue taxonomy and allowed compatibility zones.
2. Freeze normative semantics so all contributors use the same vocabulary.

Required outputs:

1. Residue taxonomy:
   - `legacy_single_active_enforcement`
   - `legacy_single_pointer_enforcement`
   - `legacy_single_actor_assumption`
   - `legacy_doc_norm_conflict`
   - `legacy_evidence_interpreted_as_norm`
2. Action class:
   - `REMOVE` (must be removed from normative/runtime path)
   - `COMPAT_TAG` (allowed only in migration compatibility path)
   - `EVIDENCE_ONLY` (historical artifact, never normative)
   - `ARCHIVE` (historical doc with explicit superseded marker)
3. Freeze rule:
   - no code/gate semantics change may merge unless mapped to a residue row in Step B.

### 14.2 Step B — Repository residue inventory ledger (machine-checkable)

Rule:

1. Every detected mixed legacy item must be recorded before cleanup execution.
2. No “silent cleanup” is allowed.

Ledger schema (mandatory columns):

1. `residue_id` (e.g., `ASB-RC-001`)
2. `file_path`
3. `line_or_pattern`
4. `residue_type` (from Step A taxonomy)
5. `current_behavior`
6. `target_behavior`
7. `action_class` (`REMOVE|COMPAT_TAG|EVIDENCE_ONLY|ARCHIVE`)
8. `blocking_level` (`P0|P1`)
9. `owner`
10. `status` (`SPEC_READY|CODE_READY|GATE_READY|VERIFIED|DONE`)
11. `evidence_ref`

Anti-forget rule:

1. If a residue is discussed in review but has no ledger row, it is treated as unresolved and cannot be marked done.

### 14.2.1 Initial residue ledger (Top set, must be tracked before implementation)

| residue_id | file_path | line_or_pattern | residue_type | current_behavior | target_behavior | action_class | blocking_level | owner | status | evidence_ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASB-RC-001 | `scripts/identity_creator.py` | `_single_active_precheck` | `legacy_single_active_enforcement` | activation/update enforces catalog single-active and demotes other active identities | actor-scoped binding arbitration replaces global single-active enforcement | REMOVE | P0 | protocol-architect | SPEC_READY | repo scan (`rg single-active`) |
| ASB-RC-002 | `scripts/identity_installer.py` | `_single_active_precheck` | `legacy_single_active_enforcement` | install/adopt path blocks on multiple active identities in catalog | installer path becomes actor-aware; no implicit global demotion | REMOVE | P0 | protocol-architect | SPEC_READY | repo scan (`rg single-active`) |
| ASB-RC-003 | `scripts/validate_identity_state_consistency.py` | `catalog has multiple active identities` | `legacy_single_active_enforcement` | validator hard-fails when active identities > 1 | validator checks actor-binding consistency instead of global active-count singleton | REMOVE | P0 | protocol-architect | SPEC_READY | repo scan (`rg multiple active identities`) |
| ASB-RC-004 | `scripts/validate_identity_session_pointer_consistency.py` | `Validate session pointer consistency with catalog single-active identity` | `legacy_single_pointer_enforcement` | canonical pointer check assumes exactly one active identity | canonical actor pointer checks (`session/actors/<actor_id>.json`) with legacy mirror compatibility | REMOVE | P0 | protocol-architect | SPEC_READY | repo scan (`rg session pointer consistency`) |
| ASB-RC-005 | `scripts/compile_identity_runtime.py` | `multiple active identities found; pass --identity-id explicitly` | `legacy_single_active_enforcement` | compile path depends on singleton active identity | compile selects identity by explicit actor binding or explicit identity input, never singleton assumption | REMOVE | P0 | protocol-architect | SPEC_READY | repo scan (`rg multiple active identities found`) |
| ASB-RC-006 | `scripts/sync_session_identity.py` + `identity_creator` session sync call chain | `active_identity.json` write as canonical | `legacy_single_pointer_enforcement` | single canonical pointer is primary state | actor pointer is canonical, `active_identity.json` becomes compatibility mirror during migration | COMPAT_TAG | P0 | protocol-architect | SPEC_READY | repo scan (`rg active_identity.json`) |
| ASB-RC-007 | `scripts/e2e_smoke_test.sh` | `validate session pointer consistency (catalog-scoped canonical + legacy mirror)` | `legacy_single_pointer_enforcement` | e2e step validates singleton session-pointer semantics | e2e validates actor-binding semantics + compatibility mirror policy | REMOVE | P1 | protocol-architect | SPEC_READY | repo scan (`rg session pointer consistency`) |
| ASB-RC-008 | `README.md` | `Session pointer canonical path: <catalog_dir>/session/active_identity.json` | `legacy_doc_norm_conflict` | normative readme still presents single-pointer canonical model | readme declares actor pointer canonical + legacy mirror compatibility scope | ARCHIVE | P1 | protocol-architect | SPEC_READY | repo scan (`rg Session pointer canonical path`) |
| ASB-RC-009 | `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` | `Mode A ... single active identity` | `legacy_doc_norm_conflict` | older governance note states single-active team default | mark superseded/evidence-only and reference v1.5.0 topic SSOT | ARCHIVE | P1 | protocol-architect | SPEC_READY | repo scan (`rg single active identity`) |
| ASB-RC-010 | `identity/runtime/reports/activation/*.json` | `"single_active_enforced": true` | `legacy_evidence_interpreted_as_norm` | historical activation artifacts embed old enforcement semantics | keep as historical evidence but enforce `EVIDENCE_ONLY` interpretation (non-normative) | EVIDENCE_ONLY | P1 | protocol-architect | SPEC_READY | historical activation reports |
| ASB-RC-011 | `identity/runtime/*/examples/identity-role-binding-*.json` | `demoted by single-active switch` | `legacy_evidence_interpreted_as_norm` | role-binding samples still narrate single-active demotion semantics | keep historical records, prevent normative reuse in validators/docs | EVIDENCE_ONLY | P1 | protocol-architect | SPEC_READY | sample evidence scan |
| ASB-RC-012 | cross-surface (creator/installer/state/session/compile/e2e/readiness/full-scan/three-plane) | any unresolved `single-active` semantic branch | `legacy_single_actor_assumption` | mixed old/new semantics can coexist and cause drift | all actor-binding mandatory branches mapped to ASB-RQ + ASB-RC rows before merge | REMOVE | P0 | protocol-architect | SPEC_READY | this SSOT + residue ledger |

### 14.3 Step C — Cleanup execution waves (P0 -> P1, no mixed merge)

Wave order:

1. `Wave-1 (P0 runtime/core validators)`:
   - remove single-active hard assumptions from activation/state/session critical path.
2. `Wave-2 (P1 gate/readiness/scan semantics)`:
   - align e2e/readiness/full-scan/three-plane interpretation with actor-scoped model.
3. `Wave-3 (P1 docs/history channel cleanup)`:
   - normalize docs to topic/global SSOT boundaries and mark old notes as archive/evidence-only.

Wave control fields (mandatory):

1. `entry_criteria`
2. `exit_criteria`
3. `rollback_trigger`
4. `acceptance_commands`

No-mix hard rule:

1. One PR belongs to one cleanup wave only.
2. Cross-wave bundling is forbidden unless explicitly approved in this document with reason and risk note.

### 14.4 Consistency guard (prevent oral drift and forgotten work)

1. Any status claim must reference:
   - requirement row (`ASB-RQ-*`) and
   - residue row (`ASB-RC-*`).
2. “Looks fixed” without row status transition is invalid.
3. Done transition requires:
   - command evidence,
   - row status update to `DONE`,
   - reviewer confirmation note in same change set.

### 14.5 Minimal acceptance commands for Step A/B/C governance loop

```bash
# docs contract and SSOT consistency
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_protocol_ssot_source.py

# full-scan baseline posture after each cleanup wave
python3 scripts/full_identity_protocol_scan.py --scan-mode full --out /tmp/full-identity-scan-asb-cleanup.json

# optional residue discovery probe (non-normative helper)
rg -n "single[-_ ]active|active_identity.json|multiple active identities|session pointer consistency" scripts docs README.md
```
