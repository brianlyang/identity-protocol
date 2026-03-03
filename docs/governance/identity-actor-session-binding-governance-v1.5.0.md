# Identity Actor-Scoped Session Binding Governance (v1.5.0)

Status: Draft (P0 remediation directive)  
Governance layer: protocol  
Scope: identity protocol base-repo only (no instance business policy)  
Owner: identity protocol base-repo architect
Execution mode: topic-level canonical SSOT for actor-session-binding governance  
Tag policy: `v1.5` remains locked until all `P0` requirement ledger rows are `DONE` and audit sign-off is `PASS` (`P1` rows block only when explicitly promoted to `P0`)

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

1. Any `P0` requirement not reaching `DONE` keeps `v1.5` tag locked.
2. `P1` requirements are mandatory backlog items and remain visible in the ledger; they block `v1.5` only if explicitly promoted to `P0`.

### 0.5 Baseline snapshot (normative as-of checkpoint)

As-of baseline:

1. `as_of_utc`: `2026-03-01`
2. `protocol_repo_head`: `baed7ba`
3. `topic_status`: governance specification substantially complete; runtime implementation not closed.

Normative interpretation:

1. This topic is not allowed to be declared `implemented` while requirement ledger rows remain `SPEC_READY`.
2. `SPEC_READY` coverage means governance direction is usable; it does not satisfy runtime closure claims.

Hard evidence (repository-local):

1. Topic P0 framing and explicit non-safe state:
   - section `0.4 Hard rule`
   - section `1) Problem Statement (P0)` observed failure pattern
2. Runtime still enforces single-active semantics (conflicts with multi-actor target):
   - `scripts/identity_creator.py:150`
   - `scripts/identity_installer.py:253`
   - `scripts/validate_identity_state_consistency.py:44`
   - `scripts/validate_identity_session_pointer_consistency.py:124`
   - `scripts/sync_session_identity.py:21`
3. Landed-vs-gap script state (as-of this snapshot):
   - landed:
     - `validate_actor_session_binding`
     - `validate_no_implicit_switch`
     - `validate_cross_actor_isolation`
     - `render_identity_response_stamp`
     - `validate_identity_response_stamp`
     - `refresh_identity_session_status`
     - `validate_identity_response_stamp_blocker_receipt`
     - `validate_identity_session_refresh_status`
   - remaining P0 governance gaps from latest roundtable intake:
     - `validate_instance_base_repo_write_boundary`
     - `validate_protocol_feedback_ssot_archival`

### 0.6 Baseline snapshot refresh policy (anti-stale)

Mandatory refresh triggers:

1. Update `protocol_repo_head` when this document receives normative changes.
2. Update snapshot fields before any release-lock or milestone status report.
3. If snapshot is not updated after normative edits, reviewer must mark status as `WARN` (baseline stale) until corrected.

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
| 8. Governance-boundary hardening lane | Codify base-repo write boundary + protocol-feedback SSOT archival + scope arbitration + reply stamp replay counter | new contracts (`5.8`) + required gates + release-blocking replay metrics |

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

Every user-facing response must include runtime-generated stamp fields (header line or structured block).
To avoid path leakage and semantic ambiguity, fields are split into external and internal views:

1. External/user-facing required fields:
   - `actor_id`
   - `identity_id`
   - `catalog_ref`
   - `pack_ref`
   - `scope`
   - `lock_state`
   - `lease_id_short`
2. Internal evidence required fields:
   - `actor_id`
   - `identity_id`
   - `catalog_path`
   - `resolved_pack_path`
   - `scope`
   - `lock_state`
   - `lease_id` (full or shortened)

Hard rules:

1. Stamp must be generated from live binding context.
2. Hardcoded identity literals are forbidden.
3. For governed user-facing text replies, stamp must appear on the first line (`Identity-Context: ...`).
4. Structured `identity_context` blocks are allowed as supplemental output, but cannot replace the first-line stamp requirement for governed text replies.

Display safety boundary (mandatory):

1. External/user-facing stamp output must not expose host absolute paths directly.
2. Internal evidence view may include `catalog_path` / `resolved_pack_path`, but default external view should emit redacted references:
   - `catalog_ref`
   - `pack_ref`
   - `scope`
   - `lease_id_short`
3. Absolute path fields are reserved for audit logs/reports and validator consumption.

Canonical stamp format (example template, placeholders must be runtime-resolved):

1. External/user-facing (redacted):
   - `Identity-Context: actor_id=<actor_id>; identity_id=<identity_id>; catalog_ref=<catalog_ref>; pack_ref=<pack_ref>; scope=<scope>; lock=<lock_state>; lease=<lease_id_short>; source=<source_domain>`
2. Internal evidence/audit:
   - `Identity-Context-Internal: actor_id=<actor_id>; identity_id=<identity_id>; catalog_path=<catalog_path>; resolved_pack_path=<resolved_pack_path>; scope=<scope>; lock=<lock_state>; lease=<lease_id_short>; source=<source_domain>`
3. If structured output is used, the same fields must be present under a dedicated `identity_context` object.

### 5.2A Response stamp enforcement hardening profile (mandatory)

This subsection operationalizes requirement-4 ("every user-facing reply must include dynamic identity stamp; no hardcoding")
into fail-safe runtime and gate semantics.

Mandatory response-stamp behavior:

1. Stamp must be generated from live resolved binding context at response time (not from prompt literals, cached constants, or static templates).
2. Required runtime fields (external view):
   - `actor_id`
   - `identity_id`
   - `scope`
   - `lock_state`
   - `lease_id_short`
   - `source_domain` (`project` | `global` | `auto` | `env`)
   - `catalog_ref` (redacted reference, not host absolute path)
   - `pack_ref` (redacted reference, not host absolute path)
3. Required runtime fields (internal evidence view):
   - all external view fields, plus canonical resolved pointers used for validation/audit replay.
4. `source_domain=auto` must follow deterministic arbitration:
   - prefer project-scoped pointer when present,
   - do not let ambient env silently override project pointer.

Mismatch and blocker semantics (hard boundary):

1. If stamp context mismatches current binding (`identity_id`, pointer tuple, or lock state), business reply must be blocked.
2. System must emit `blocker_receipt` first, then stop business payload.
3. `blocker_receipt` minimum fields:
   - `error_code`
   - `expected_identity_id`
   - `actual_identity_id`
   - `source_domain`
   - `resolver_ref`
   - `next_action`
4. Recommended error code family:
   - `IP-ASB-STAMP-001` (stamp/binding mismatch)
   - `IP-ASB-STAMP-002` (stamp source arbitration conflict)
   - `IP-ASB-STAMP-003` (stamp hardcoded/placeholder leakage)

Determinism and portability guard:

1. Stamp renderer and stamp validator must be CWD-invariant (no execution-directory-dependent resolution).
2. Relative-path parsing inside stamp validation is forbidden in closure gates; canonical absolute resolution is required before comparison.

### 5.2B Response stamp configuration profile (message/email style, governance-safe)

Response stamp may be configured for presentation style, but must not weaken protocol safety rules.

Config contract (recommended location: identity runtime contract fields):

1. `response_stamp_profile.enabled`:
   - allowed values: `true` only when protocol stamp gate is required,
   - `false` is allowed only for explicitly declared non-governed/debug channels and must never apply to governed user-facing outputs.
2. `response_stamp_profile.format`:
   - allowed values: `header_line` | `structured_block` | `mail_header`
3. `response_stamp_profile.audience_mode`:
   - allowed values: `external` | `internal` | `dual`
4. `response_stamp_profile.redaction_policy`:
   - allowed values: `strict` | `standard`
   - `strict` is default for external outputs.
5. `response_stamp_profile.template_ref`:
   - reference to template id/path (placeholders only),
   - hardcoded identity literals in templates are forbidden.
6. `response_stamp_profile.on_mismatch`:
   - allowed values: `blocker_receipt` only for governed flows.

Governance invariants (cannot be configured away):

1. Dynamic runtime resolution is mandatory.
2. Non-hardcoded policy is mandatory.
3. Mismatch fail-closed + blocker receipt is mandatory.
4. External redaction boundary is mandatory.

### 5.2C Disclosure level and user-named explicit trigger

Stamp display may vary by configured disclosure level, with user-named explicit trigger support.
This allows message/email-style ergonomics without weakening governance controls.

Disclosure level contract:

1. `response_stamp_profile.disclosure_level`:
   - `minimal`: concise one-line external stamp (required core fields only).
   - `standard`: default external stamp with required core fields + source domain.
   - `verbose`: external stamp with additional diagnostic refs allowed by redaction policy.
   - `audit`: internal evidence-oriented structured stamp (for authorized internal channels only).
2. Required core fields remain mandatory for all governed user-facing levels.
3. Level changes are presentation-only; they must not alter binding resolution or gate results.
4. Operational runtime default for governed user-facing replies is `standard` unless an explicit level override is applied.
5. Any runtime implementation that still defaults governed user-facing replies to `minimal` is non-conformant and must be tracked as protocol-layer closure gap.
6. Session-scope level persistence must be actor-scoped and auditable:
   - recommended path: `<catalog_dir>/session/response-stamp-profiles/<actor_token>.json`
   - required fields: `actor_id`, `identity_id`, `disclosure_level`, `trigger_text`, `trigger_source`, `scope`, `updated_at`
7. Natural-language trigger normalization confidence must be recorded; ambiguous trigger must not silently alter session-level profile.
8. External stamp must keep responsibility/source cues separated:
   - identity block keeps `source=<...>` as runtime provenance field,
   - tail block must append `| Layer-Context: work_layer=<...>; source_layer=<...>` at line end.
9. `work_layer` and `source_layer` are governance fields and must be machine-readable in validator payloads.

User-named explicit trigger contract:

1. Trigger must be explicit and user-named (no implicit carry-over), for example:
   - `identity stamp level=minimal`
   - `identity stamp level=standard`
   - `identity stamp level=verbose`
2. Trigger effect scope must be declared:
   - `once` (single response),
   - `session` (until changed by explicit trigger or session reset).
3. Every trigger application must be auditable with:
   - `actor_id`
   - `identity_id`
   - `trigger_text`
   - `applied_level`
   - `scope`
   - `timestamp`
   - `parse_confidence`
   - `disclosure_source`
4. Explicit trigger cannot bypass mismatch fail-closed behavior; blocker receipt remains mandatory on mismatch.
5. Explicit trigger cannot request unredacted absolute paths in external mode.

Natural-language explicit trigger parsing contract:

1. Natural-language command is allowed as explicit trigger source when parser confidence is sufficient.
2. Recommended trigger intent examples (illustrative, non-hardcoded):
   - "把身份回显切到简洁"
   - "身份标头用标准模式"
   - "把 identity stamp 调成 verbose（本轮）"
3. Parser output must be normalized into structured command fields:
   - `intent=identity_stamp_level_switch`
   - `target_level in {minimal, standard, verbose, audit}`
   - `scope in {once, session}`
   - `trigger_source=natural_language`
4. Ambiguous natural-language trigger must not be silently applied:
   - require clarification or fallback to `standard` with explicit notice.
5. Natural-language trigger execution must be logged with parse confidence and normalization result.
6. Natural-language trigger may include layer intent and must be normalized into:
   - `work_layer in {protocol, instance, dual}`
   - `source_layer in {project, global, env, auto}`
7. Ambiguous layer intent must not be silently applied:
   - require clarification and enter `PROTOCOL_CANDIDATE` when candidate bridge is enabled.
   - if candidate bridge is unavailable, fallback must remain `work_layer=instance` with explicit `fallback_reason`.

### 5.2D Dynamic disclosure rendering profile (cross-instance replay alignment)

This subsection clarifies how "message/email-style identity disclosure" should be rendered without violating protocol safety.

Rendering channels and allowed payload:

1. `external` channel (default governed user-facing):
   - must use redacted references (`catalog_ref`, `pack_ref`),
   - must not expose host absolute paths,
   - must include runtime-resolved identity fields (no hardcoded literals).
2. `internal/audit` channel:
   - may include absolute `catalog_path` / `resolved_pack_path`,
   - may include resolver evidence pointer (for example `resolver_ref=<.../CURRENT_TASK.json:line>`),
   - remains non-user-default and must be explicitly configured/authorized.

Recommended mail-header style templates (placeholders are runtime-only):

1. External default:
   - `Identity-Context: actor_id=<actor_id>; identity_id=<identity_id>; catalog_ref=<catalog_ref>; pack_ref=<pack_ref>; scope=<scope>; lock=<lock_state>; source=<source_domain> | Layer-Context: work_layer=<work_layer>; source_layer=<source_layer>`
2. Internal/audit diagnostic:
   - `identity_id=<identity_id> | catalog_path=<catalog_path> | resolved_pack_path=<resolved_pack_path> | scope=<scope> | lock_state=<lock_state> | source=<source_domain> | work_layer=<work_layer> | source_layer=<source_layer> | resolver_ref=<resolver_ref>`

Tail-block hard rules (governed user-facing first line):

1. `Layer-Context` must be appended at line tail after `Identity-Context`.
2. `work_layer` and `source_layer` are mandatory machine-readable fields.
3. `source` and `source_layer` must be semantically consistent.
4. `source` and `source_layer` are intentionally non-identical provenance fields:
   - `source` tracks identity resolution provenance (`project` / `global` / `env` / `auto`).
   - `source_layer` tracks layer-intent provenance for `work_layer` resolution (`project` / `global` / `env` / `auto`).
5. Legacy alias handling:
   - historical replay inputs may contain `source=local`; mapper must normalize it to `project`,
   - new outputs must not emit `source=local`.
6. Equal token values across `source` and `source_layer` are allowed but must not be treated as semantic equivalence without explicit mapper evidence.
7. Missing tail block or invalid layer enum is fail-closed under strict operations.

Cross-instance replay requirement:

1. For any replay evidence claiming "dynamic disclosure", at least two different identity instances must produce distinct `identity_id`/pack references under the same renderer logic.
2. Replays that only show one fixed identity literal are invalid for non-hardcoded closure claims.
3. Validation output should include a machine-readable flag set:
   - `dynamic_identity_resolved=true|false`
   - `redaction_boundary_respected=true|false`
   - `resolver_binding_consistent=true|false`

### 5.3 `identity_health_self_heal_contract_v1`

Health report must include actor-binding risk classes:

1. binding mismatch
2. lease stale
3. implicit switch risk
4. pointer drift

Self-heal output must include deterministic remediation actions and re-validation commands.

### 5.3A Health/heal cross-validation hardening profile (mandatory)

This subsection operationalizes requirement-3 ("instance can self-check and self-repair using protocol health tooling")
into machine-verifiable closure semantics.

Health contract hard requirements:

1. Health report must expose actor-risk checks explicitly (not inferred from generic status):
   - `actor_binding_integrity`
   - `actor_lease_freshness`
   - `implicit_switch_guard`
   - `pointer_drift_guard`
2. Every non-pass actor-risk check must include:
   - `error_code` (prefer `IP-ASB-*` family),
   - deterministic `suggestion` command,
   - `status in {PASS, WARN, FAIL}`.
3. Health report must include coverage metadata for actor-risk profile:
   - `actor_risk_required_count`
   - `actor_risk_present_count`
   - `actor_risk_coverage_rate`
4. Actor-risk profile coverage below 100% is not allowed to be treated as runtime-closed.

Self-heal contract hard requirements:

1. `identity_creator heal --apply` must support actor-centric repair branches for:
   - actor binding repair,
   - lease repair/renewal,
   - pointer reconciliation (actor canonical pointer first, legacy mirror compatibility only).
2. Self-heal report must include replay references:
   - `health_report_ref`
   - `heal_report_ref`
   - `post_validate_ref`
3. Any "auto-repaired" claim without post-validate evidence is invalid.

Deterministic replay binding rule (anti-stale):

1. Health validators consumed in acceptance/release flow must use explicit report binding (`--report <path>`) when available.
2. "latest file by timestamp" is allowed only for exploratory runs; it is not sufficient as release/audit closure evidence.
3. Closure evidence must demonstrate a single bound chain:
   `health_report -> heal_report -> validate_result`.

### 5.3B Health/heal acceptance semantics and execution-context declaration (mandatory)

Purpose:

1. Prevent false "self-heal closed" claims caused by mixed execution context or non-replayable evidence.

Acceptance semantics (must all hold):

1. Phase-1 (`detect`): first `collect_identity_health_report` run must produce a bound report artifact, even when status is `WARN`/`FAIL`.
2. Phase-2 (`repair`): `identity_creator heal --apply` must emit a heal report that references the Phase-1 health report.
3. Phase-3 (`verify`): post-repair `identity_creator validate` must be executed on the same identity/catalog tuple.
4. Phase-4 (`recheck`): a second health report must be generated and compared against Phase-1 for closure evidence.
5. Runtime closure claim is valid only when:
   - Phase-1 proves findings were detectable,
   - Phase-3 returns pass,
   - Phase-4 has no unresolved actor-risk `FAIL` entries.
6. If actor-risk findings remain unresolved after Phase-3/Phase-4, status must remain `blocked` (not `done`).

Execution-context declaration (must be included in architect/audit return):

1. `collect_identity_health_report` can run in sandbox when target paths are read-only accessible.
2. `identity_creator heal --apply` and any command mutating runtime catalog/session state must declare writable context (typically escalated for `~/.codex`).
3. `identity_creator validate` after repair must run in the same effective catalog context used in Phase-2.
4. Return payload must include:
   - `execution_context_detect`
   - `execution_context_repair`
   - `execution_context_verify`
   - `catalog_path`
   - `identity_id`

### 5.3C Anytime self-check/refresh contract (including protocol version visibility)

Purpose:

1. Allow operators and instances to self-check current identity binding state at any time.
2. Ensure "current protocol baseline lag" is visible in the same self-check output.

Refresh command contract:

1. `refresh_identity_session_status` must be callable on-demand outside release windows.
2. Required output fields:
   - `identity_id`
   - `actor_id`
   - `catalog_path`
   - `resolved_pack_path`
   - `resolved_scope`
   - `lease_status` (`ACTIVE` | `STALE` | `MISSING`)
   - `pointer_consistency` (`PASS` | `WARN` | `FAIL`)
   - `risk_flags` (array)
   - `next_action`
3. Protocol version visibility fields are mandatory:
   - `report_protocol_commit_sha`
   - `current_protocol_head_sha`
   - `baseline_status`
   - `baseline_error_code`
   - `lag_commits`
4. Output must be machine-readable (`--json-only`) for gate reuse.

Consistency and cross-surface rule:

1. Refresh output for the same identity/catalog tuple must be semantically consistent with:
   - `report_three_plane_status.py`
   - `full_identity_protocol_scan.py`
2. Any mismatch between refresh output and three-plane/full-scan visibility is treated as governance drift and must surface as `WARN`/`FAIL`.

Three-plane/full-scan mandatory visibility fields (same identity/catalog tuple):

1. `report_three_plane_status` instance detail must expose actor-refresh fields:
   - `actor_id`
   - `lease_status`
   - `pointer_consistency`
   - `risk_flags`
   - `baseline_status`
   - `baseline_error_code`
   - `report_protocol_commit_sha`
   - `current_protocol_head_sha`
2. `full_identity_protocol_scan` must include `session_refresh_status` check payload with machine-readable actor/baseline fields:
   - `identity_id`
   - `actor_id`
   - `lease_status`
   - `pointer_consistency`
   - `risk_flags`
   - `baseline_status`
   - `baseline_error_code`
   - `lag_commits`
3. Missing fields above are not allowed to be interpreted as implicit pass.

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
4. Script-only edits cannot be claimed as capability upgrade closure; closure requires evidence envelope completeness + required-gates pass + requirement-ledger status transition.

### 5.6 `identity_system_path_governance_contract_v1` (P0)

Goal:

1. Close the path-governance chain across catalog/runtime/report so evidence is replayable and non-ambiguous.
2. Prevent mixed-source path tuples (e.g., catalog from one domain, pack/report from another) from being interpreted as valid closure.
3. Keep all path checks machine-verifiable and CWD-invariant.

Problem framing (protocol layer):

1. Catalog `pack_path` can be non-canonical (relative/missing/out-of-boundary).
2. Execution reports can persist non-canonical `resolved_pack_path` values.
3. `identity_home` / `catalog_path` / `resolved_pack_path` can be sourced from inconsistent domains if no strict tuple guard exists.
4. Runtime entry/guard can pass without enforcing canonical `identity_home == dirname(identity_catalog)` alignment.

Mandatory path gates:

1. `pack_path_canonical_gate`
   - catalog `pack_path` must be canonical absolute and exist,
   - path must remain in allowed runtime root for selected mode.
2. `resolved_pack_report_gate`
   - report `resolved_pack_path` must be canonical absolute,
   - forbidden values include empty, `.`, `..`, relative strings, and unresolved symbolic traversals.
3. `identity_home_catalog_alignment_gate`
   - canonical `identity_home` must equal canonical `dirname(identity_catalog)`,
   - mismatch is fail-closed for runtime mutation flows.
4. `fixture_runtime_boundary_gate`
   - fixture/demo assets cannot enter runtime active/update path without explicit override + audit receipt.

Path evidence envelope (required fields):

1. `identity_id`
2. `catalog_path`
3. `identity_home`
4. `resolved_pack_path`
5. `path_scope`
6. `path_governance_status` (`PASS_REQUIRED|FAIL_REQUIRED|SKIPPED_NOT_REQUIRED`)
7. `path_error_codes` (array)
8. `canonicalization_ref` (resolver/version/timestamp)

Hard rule:

1. If any mandatory path gate is `FAIL_REQUIRED`, runtime closure claim is invalid.
2. Path-governance failures cannot be masked by unrelated PASS checks.

### 5.7 `protocol_feedback_robustness_contract_v1` (P0, non-merge twin-track)

Non-merge rule (hard boundary):

1. `Track-A` writeback freeze and `Track-B` semantic routing retrigger are independent P0 tracks.
2. They MUST be remediated and audited separately; one track passing cannot be used to close the other.
3. Architect/auditor returns MUST include explicit A/B separation in commit diff, gate output, and residual risk.
4. Architect/auditor returns MUST expose separate per-track fields: `commit_sha_list`, `changed_files`, `acceptance_rc_tail`, `residual_risk`.

#### 5.7.1 Track-A `writeback_continuity_contract_v1`

Goal:

1. Prevent runtime executions from completing without mandatory state writeback.
2. Preserve strict governance while allowing controlled degraded writeback for non-fatal checks.
3. Keep execution report path semantics canonical and identical across producer/consumer/gates.

Mandatory semantics:

1. Writeback mode MUST be explicit and machine-readable:
   - `STRICT_WRITEBACK`
   - `DEGRADED_WRITEBACK`
2. `DEGRADED_WRITEBACK` is allowed only for non-fatal failures with required risk fields:
   - `writeback_mode`
   - `degrade_reason`
   - `risk_level`
   - `next_recovery_action`
3. `post_execution_mandatory` validation MUST run after each upgrade execution and before closure claims.
4. Canonical report path MUST be shared by:
   - execution producer,
   - freshness/coverage/readiness consumers,
   - health/scan/three-plane report readers.

Failure code family (`IP-WRB-*`):

1. `IP-WRB-001` missing mandatory writeback in execution closure.
2. `IP-WRB-002` degraded writeback used without required risk fields.
3. `IP-WRB-003` post-execution mandatory state not advanced.
4. `IP-WRB-004` report path mismatch between producer and gate consumers.

#### 5.7.2 Track-B `semantic_routing_guard_contract_v1`

Goal:

1. Eliminate semantic retrigger caused by mixing `protocol_vendor` and `business_partner` domains.
2. Make terminology boundary executable through deterministic validators.
3. Keep business main loop fail-operational by default, but fail-closed on governance boundary violations.

Mandatory semantics:

1. Pre-routing classification is required before retrieval when intent contains vendor-like trigger terms.
2. Required fields:
   - `intent_domain`
   - `intent_confidence`
   - `classifier_reason`
3. Domain enum:
   - `protocol_vendor`
   - `business_partner`
   - `mixed`
   - `unknown`
4. Namespace policy:
   - `runtime/protocol-feedback/protocol-vendor-intel/*`
   - `runtime/protocol-feedback/business-partner-intel/*`
   - legacy broad namespace `vendor-intel/*` MUST NOT be default write target.
5. `mixed` handling policy:
   - auto split + tagged output, or explicit manual review handoff.
6. `unknown` handling policy:
   - ask/clarify or split-and-tag; no silent one-domain default.

Failure code family (`IP-SEM-*`):

1. `IP-SEM-001` missing intent classification.
2. `IP-SEM-002` mixed-domain output without split.
3. `IP-SEM-003` namespace violation.
4. `IP-SEM-004` domain whitelist violation.

#### 5.7.3 Cross-track coexistence rule (A/B with sidecar)

1. `protocol-feedback sidecar` remains default non-blocking for routine signals.
2. Escalation to blocking is allowed only for governance-boundary P0 violations.
3. Track-A and Track-B validators MUST emit deterministic machine-readable outputs so that sidecar escalation is auditable.

### 5.8 `protocol_governance_boundary_contract_v1` (P0 hotfix lane)

This section codifies roundtable-intake P0 governance gaps discovered after initial v1.5 actor/path/Track-A/Track-B landing.

#### 5.8.1 `instance_base_repo_mutation_policy_v1`

Goal:

1. Prevent identity instances from mutating protocol/code assets in base repo while still allowing documentation collaboration.
2. Make governance enforcement independent from runtime sandbox/profile differences.

Mandatory semantics:

1. Allowlist default: `docs/**` (including `docs/governance/**` and `docs/review/**`).
2. Denylist default: protocol/code assets (for example `scripts/**`, workflow yaml, protocol runtime/config files).
3. Mixed change set rule: if any denylist path is changed, result is `FAIL_REQUIRED` (docs changes cannot mask code/protocol mutation).
4. Override is exceptional and requires auditable receipt fields:
   - `approved_by`
   - `ticket_id`
   - `purpose`
   - `scope_paths`
   - `expiry`
5. Missing/expired/over-scope receipt must remain `FAIL_REQUIRED`.

#### 5.8.2 `protocol_feedback_ssot_archival_contract_v1`

Goal:

1. Ensure protocol-feedback outputs are archived in identity protocol SSOT channels before any mirror publication.
2. Prevent mirror-only reporting drift.

Mandatory semantics:

1. Required archival targets:
   - `runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md`
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
2. Trigger condition: protocol-upgrade/governance/gate feedback semantics are present in task scope or output labels.
3. Mirror channels (for example project-level issue reports) are evidence copies only and cannot replace SSOT archival.
4. Fail-closed behavior:
   - required outbox missing => `FAIL_REQUIRED`
   - evidence-index link missing => `FAIL_REQUIRED`
   - mirror-only without SSOT archival => `FAIL_REQUIRED`

#### 5.8.3 `scope_arbitration_contract_v1` (dual-catalog deterministic rule)

Goal:

1. Remove ambiguity when same `identity_id` exists in multiple catalogs/domains.
2. Make readiness/runtime arbitration explicit and replayable.

Mandatory semantics:

1. `release_readiness_check.py` must accept explicit `--scope`.
2. Allowed scope enum: `REPO | USER | ADMIN | SYSTEM`.
3. `--scope` must be forwarded to runtime-mode/scope validators and resolver preflight commands.
4. Ambiguous no-scope resolution under multi-catalog conflict must fail-closed with actionable hint.

#### 5.8.4 `response_stamp_reply_channel_observability_contract_v1`

Goal:

1. Turn "stamp required on every user-facing reply" into machine-counted replay evidence.
2. Prevent long-thread or compaction windows from hiding missing-stamp turns.

Mandatory semantics:

1. Replay surfaces must expose `reply_stamp_missing_count`.
2. Required visibility targets:
   - audit replay output
   - `report_three_plane_status.py`
   - `full_identity_protocol_scan.py`
3. Release closure window requires `reply_stamp_missing_count=0` for governed response channels.

#### 5.8.5 `readiness_scope_health_passthrough_contract_v1`

Goal:

1. Ensure explicit scope arbitration is preserved through readiness health branch, not only through preflight guards.

Mandatory semantics:

1. When `release_readiness_check.py` receives `--scope`, the same `scope` must be propagated to health collection calls that execute scope validators.
2. No-scope dual-catalog ambiguity must still fail-closed with `IP-ENV-002`.
3. Scoped readiness must not regress into scope false-fail due to omitted passthrough in downstream checks.

#### 5.8.6 `baseline_policy_stratification_contract_v1`

Goal:

1. Keep baseline freshness policy strict where release/mutation decisions are made.
2. Preserve observability surfaces for drift visibility without blocking exploratory scans.

Mandatory semantics:

1. `strict` baseline policy is required for release/mutation decision paths (readiness closure, e2e release gate, mutation/activation closure).
2. `warn` baseline policy is allowed only for observability/reporting surfaces (scan/three-plane/health observe mode).
3. Any path that can claim release/mutation closure must not downgrade baseline mismatch (`IP-PBL-001`) to non-blocking.

#### 5.8.7 `protocol_version_alignment_contract_v1`

Goal:

1. Unify protocol version consistency checks into one deterministic closure contract.

Mandatory tuple:

1. `execution_report.protocol_commit_sha`
2. `execution_report.identity_prompt_sha256`
3. `execution_report.identity_prompt_path`
4. `execution_report.identity_id`
5. `execution_report.catalog_path`
6. `execution_report.resolved_pack_path`
7. current runtime `CURRENT_TASK` + prompt + binding tuple resolved context

Mandatory semantics:

1. Closure paths must validate this tuple as one alignment unit.
2. Mismatch in any required tuple field is fail-closed on release/mutation closure surfaces.
3. Alignment output must remain machine-readable and replayable.

#### 5.8.8 `instance_protocol_split_receipt_contract_v1`

Goal:

1. Eliminate repeated oral reminders by making lane split (`instance execution` vs `protocol governance feedback`) machine-enforced.
2. Keep business execution content and protocol governance content isolated in user-visible replies and replay artifacts.
3. Ensure split evidence is auditable and linked to protocol-feedback SSOT when governance feedback is triggered.

Mandatory semantics:

1. Every governed user-visible round must emit a split receipt with required fields:
   - `split_notice`
   - `instance_actions`
   - `protocol_actions`
   - `feedback_triggered`
   - `evidence_index`
2. Backward-compatible aliases are temporarily accepted with warning:
   - `split_reminder` -> `split_notice`
   - `instance_action_receipt` -> `instance_actions`
   - `protocol_action_receipt` -> `protocol_actions`
   - `protocol_feedback_triggered` -> `feedback_triggered`
   - `evidence_index_receipt` -> `evidence_index`
3. `split_notice` must include machine-readable lane declaration:
   - `instance_lane=business_execution`
   - `protocol_lane=governance_feedback`
4. `feedback_triggered` must be explicit `true|false`.
5. When `feedback_triggered=true`, `protocol_actions` must include `feedback_paths` with SSOT path(s) under:
   - `runtime/protocol-feedback/outbox-to-protocol/`
   - `runtime/protocol-feedback/evidence-index/`
6. When `feedback_triggered=false`, `protocol_actions` must be explicit `none` (silence is invalid).
7. Business execution statements and protocol governance proposals must not be merged in one paragraph/section.
8. Split receipt payloads must remain protocol-sanitized:
   - no tenant identifiers
   - no customer identifiers
   - no business-scene constants in protocol contract fields
9. Failure code family (`IP-SPLIT-*`):
   - `IP-SPLIT-001`: `split_notice` missing
   - `IP-SPLIT-002`: trigger field missing/invalid
   - `IP-SPLIT-003`: `feedback_triggered=true` but SSOT path missing
   - `IP-SPLIT-004`: mixed lane content in same section
   - `IP-SPLIT-005`: protocol payload contains business-scene constants

#### 5.8.9 `protocol_feedback_trigger_hard_condition_contract_v1`

Goal:

1. Replace subjective escalation decisions with deterministic, auditable trigger conditions.
2. Preserve dual-track execution: instance lane executes now, protocol lane is fed into governance gates.

Hard trigger conditions (`feedback_triggered=true` when any true):

1. Same governance issue class recurs `>=2` rounds in audit window.
2. Any required gate exhibits false-green or false-red behavior.
3. Runtime evidence required by closure chain is missing, stale, or unlinked.
4. Lane contamination detected (`instance` and `protocol` semantics mixed in one execution section).

Dual-track enforcement:

1. Instance lane remains action-first (delivery/execution is not blocked by drafting protocol proposals).
2. Protocol lane is governed through SSOT archival and required gate replay.
3. Closure claims are valid only when both lanes have verifiable receipts.

#### 5.8.10 `cwd_invariant_execution_contract_v1`

Goal:

1. Remove current-working-directory sensitivity from protocol validators and orchestration scripts.
2. Prevent false failures caused by relative path interpretation drift.

Mandatory semantics:

1. Relative sample/evidence patterns in identity contracts must resolve against identity pack root (`CURRENT_TASK.json` parent), not process CWD.
2. Handoff self-test sample roots must resolve against identity pack root for positive/negative fixtures.
3. Orchestration scripts that invoke validator subprocesses must resolve script paths from protocol root (`Path(__file__).resolve().parent`) or explicit `--protocol-root`, never from shell CWD assumption.
4. Default repo catalog path resolution must be protocol-root deterministic; missing path must return actionable hint with explicit `--repo-catalog`.
5. `three-plane` and sibling orchestration surfaces must produce identical outcomes when invoked from non-repo CWD.

Failure code family (`IP-CWD-*`):

1. `IP-CWD-001`: relative pattern resolved against CWD instead of pack root.
2. `IP-CWD-002`: self-test sample root not pack-root anchored.
3. `IP-CWD-003`: subprocess validator path CWD-dependent.
4. `IP-CWD-004`: repo catalog default resolution CWD-sensitive.

#### 5.8.11 `execution_reply_identity_coherence_contract_v1` (P0)

Goal:

1. Eliminate perceived "identity hard-switch" caused by cross-domain tuple drift between executed command context and user-visible reply context.
2. Ensure one deterministic identity tuple (`identity_id`, `catalog_path`, `resolved_pack_path`, `actor_id`) is used from command execution through reply emission.

Mandatory semantics:

1. Strict operations (`activate`, `update`, `readiness`, `e2e`, `validate`, mutation flows) must verify command-target tuple and reply-stamp tuple coherence before user-visible business text is emitted.
2. Reply pipeline must run a fresh runtime resolver step in the same execution domain before composing user-visible output.
3. If command tuple and reply tuple mismatch on identity/catalog/pack domain, operation must fail-closed and emit blocker receipt (no silent downgrade).
4. Dual-catalog environments must expose both lane refs in machine-readable output:
   - `command_catalog_ref`
   - `resolved_catalog_ref`
   - `reply_catalog_ref`
   - `coherence_decision`
5. Inspection operations (`scan`, `three-plane`, `ci`) remain visibility-first and should surface warnings without forcing hard closure, unless explicitly promoted.
6. Strict gate artifact rendering must pin disclosure level to include tuple refs (`catalog_ref`, `pack_ref`) before coherence compare (`--disclosure-level standard` or higher). Session/user display preferences must not alter strict gate semantics.

Failure code family (`IP-ASB-CTX-*`):

1. `IP-ASB-CTX-001`: command identity tuple != reply identity tuple.
2. `IP-ASB-CTX-002`: resolver evidence missing for reply tuple.
3. `IP-ASB-CTX-003`: dual-catalog lane ambiguity unresolved in strict operation.

#### 5.8.12 `send_time_reply_gate_contract_v1` (P0)

Goal:

1. Ensure governed user-visible replies are checked at send-time unified outlet, not only in readiness/e2e/scan artifact lanes.
2. Keep first-line `Identity-Context` failure semantics deterministic and fail-closed before business content delivery.

Mandatory semantics:

1. Send-time outlet must execute unified gate before reply emission:
   - `validate_send_time_reply_gate.py`.
2. Missing first-line `Identity-Context` in send-time channel must fail-closed with blocker receipt:
   - error code family reuses `IP-ASB-STAMP-SESSION-001`.
3. Gate payload must be machine-readable and visible in scan surfaces with fields:
   - `send_time_gate_status`
   - `error_code`
   - `reply_evidence_mode`
   - `reply_sample_count`
   - `reply_first_line_missing_count`
   - `reply_first_line_missing_refs`
4. three-plane/full-scan must expose send-time gate fields under response-stamp detail.
5. At least one replay must validate real dialogue outlet evidence (`reply-file` / `reply-log`), not only `stamp-json` artifact input.

#### 5.8.13 `layer_intent_resolution_contract_v1` (P1)

Goal:

1. Improve usability of layer declaration by auto-resolving `work_layer` when intent is clear, while preserving strict fail-safe behavior.
2. Keep `Layer-Context` machine-readable and deterministic across render/validate/scan surfaces.

Mandatory semantics:

1. Resolver must emit machine-readable fields:
   - `layer_intent_resolution_status`
   - `resolved_work_layer`
   - `resolved_source_layer`
   - `intent_confidence`
   - `intent_source` (`explicit_arg` / `natural_language` / `default_fallback`)
   - `fallback_reason`
2. Explicit command args remain highest priority (`explicit_arg`).
3. Default work layer is `instance`; natural-language layer intent may auto-switch to `protocol` only when protocol trigger conditions are met and confidence is high. Ambiguous/low-confidence signals must fallback to safe default (`instance`) with `fallback_reason`.
4. Strict operations must remain fail-closed on inconsistent tuple semantics (mismatch/invalid tail/illegal enum), reusing strict gate family semantics (`IP-ASB-STAMP-SESSION-001`).
5. `three-plane` and `full-scan` must expose layer-intent telemetry fields for audit visibility.
6. Protocol layer must remain business-data neutral; no business-scene constants may be introduced for intent resolution.

#### 5.8.14 `default_work_layer_and_protocol_trigger_contract_v1` (P0)

Goal:

1. Ensure identity instances default to `instance` work layer for routine delivery.
2. Prevent implicit escalation to `protocol` layer without auditable trigger evidence.

Mandatory semantics:

1. `default_work_layer_contract_v1`:
   - resolver fallback must be `work_layer=instance` (never implicit `protocol`).
2. `protocol_trigger_contract_v1`:
   - `work_layer=protocol` is allowed only when protocol trigger conditions are met (explicit protocol override, protocol error-code signal, or protocol-governance trigger phrase with action semantics).
3. `layer_consistency_gate`:
   - strict operations must fail-closed when `work_layer=protocol` but trigger evidence is missing.
4. Trigger evidence must be machine-readable:
   - `protocol_triggered`
   - `protocol_trigger_reasons`
   - `protocol_trigger_confidence`
5. Regression gate must cover three deterministic samples:
   - `instance-intent -> instance`
   - `protocol-intent -> protocol`
   - `ambiguous-intent -> instance`
6. `source_layer` remains source-lane metadata only and must not be used as work-layer escalation substitute.

#### 5.8.15 `actor_session_multibinding_concurrency_contract_v1` (P0)

Goal:

1. Eliminate same-actor implicit rebind overwrite ("line-grab") under concurrent or interleaved activation sessions.
2. Upgrade actor binding storage from single-record overwrite semantics to deterministic multi-binding semantics.
3. Keep strict protocol lanes fail-closed when write conflict, missing receipt, or non-activation mutation is detected.

Mandatory semantics:

1. Canonical actor binding storage must support multi-binding entries keyed by runtime work key:
   - required key tuple: `actor_id + session_id` (or equivalent deterministic work-unit key declared by contract),
   - `session/actors/<actor>.json` may remain the carrier file, but payload must be multi-entry (`bindings[]` or equivalent keyed map),
   - single-object last-write-wins payload is forbidden for strict lanes.
2. Actor-binding write path must enforce CAS-style precondition:
   - required field: `binding_version` (monotonic) or equivalent compare token,
   - write must fail-closed on stale compare token (no silent overwrite).
3. Only activation lane may mutate canonical actor binding:
   - `activate` is mutable,
   - `validate` / `scan` / `readiness` / `three-plane` / `full-scan` must be read-only for canonical actor binding unless explicit governance override receipt exists.
4. Every rebind mutation must emit append-only receipt (no in-place loss):
   - `from_binding_ref`
   - `to_binding_ref`
   - `actor_id`
   - `session_id`
   - `run_id`
   - `switch_reason`
   - `approved_by` (when manual override)
   - `applied_at`
5. Same-actor multi-session coexistence must be machine-checkable:
   - adding or updating one `session_id` entry must not drop peer active entries for same `actor_id`.
6. Required failure codes (fail-closed in strict lanes):
   - `IP-ASB-MB-001`: single-record overwrite shape detected.
   - `IP-ASB-MB-002`: CAS/compare token missing.
   - `IP-ASB-MB-003`: CAS conflict (stale token).
   - `IP-ASB-MB-004`: non-activation mutation attempt on canonical binding.
   - `IP-ASB-MB-005`: rebind receipt missing or incomplete.
   - `IP-ASB-MB-006`: same-actor peer-session entry dropped after mutation.
7. Protocol layer remains business-data neutral:
   - contract fields must use generic governance terms only; no tenant or business constants.
8. Session key derivation must be deterministic and auditable:
   - `session_id` must be explicitly supplied by activation lane (`run_id` may be used only when declared as derivation source),
   - implicit process-local defaults (PID/time-only) are forbidden as sole key source in strict lanes.
9. Schema migration and compatibility boundary:
   - read path may provide compatibility adapter for legacy single-object payload during migration window,
   - write path in strict lanes must emit multi-entry shape only,
   - migration adapter usage must be surfaced in telemetry (`binding_key_mode`, `stale_reasons`).
10. CAS token scope and monotonicity:
   - canonical payload must include monotonic compare token at store scope (`binding_version` or equivalent),
   - CAS success must increment token exactly once per accepted mutation.
11. Write atomicity requirement:
   - canonical write and rebind receipt append must be atomic from gate perspective (no "binding updated / receipt missing" split-commit state in strict lanes).

#### 5.8.16 `protocol_feedback_canonical_reply_channel_contract_v1` (P0)

Goal:

1. Eliminate hidden-gate behavior where protocol-feedback appears complete but strict operations can still pass with missing canonical reply-channel evidence.
2. Force one canonical protocol-feedback reply channel and prevent non-standard path promotion to primary evidence.
3. Ensure split-receipt contract cannot silently remain `SKIPPED_NOT_REQUIRED` when protocol-feedback activity is present.

Mandatory semantics:

1. Protocol-layer feedback (`work_layer=protocol`) must use canonical root only:
   - `<resolved_pack_path>/runtime/protocol-feedback/`
2. Canonical primary reply-channel directories are mandatory:
   - `runtime/protocol-feedback/outbox-to-protocol/`
   - `runtime/protocol-feedback/evidence-index/`
   - `runtime/protocol-feedback/upgrade-proposals/`
3. Non-standard paths may be referenced only as `mirror_reference` and must never be primary evidence channel in strict operations.
4. Strict operations (`update/readiness/e2e/ci/validate/mutation`) must fail-closed if:
   - canonical primary channel missing,
   - non-standard channel used as primary,
   - mirror reference is provided without canonical SSOT primary linkage.
5. Failure code family (`IP-PFB-CH-*`):
   - `IP-PFB-CH-001`: `missing_protocol_feedback_standard_channel`
   - `IP-PFB-CH-002`: `non_standard_channel_as_primary`
   - `IP-PFB-CH-003`: `mirror_reference_without_ssot_primary`
6. Sidecar governance escalation must treat `IP-PFB-*` as blocking prefixes in strict operations (same blocking class as P0 governance boundaries).
7. Split-receipt requiredization bridge:
   - if protocol-feedback activity exists (outbox/index/upgrade proposal evidence present), split-receipt contract is auto-required,
   - strict operations must not return `SKIPPED_NOT_REQUIRED` for split-receipt in this case.
8. three-plane/full-scan must expose channel compliance telemetry:
   - `protocol_feedback_reply_channel_status`
   - `error_code`
   - `primary_channel_root`
   - `non_standard_primary_refs`
   - `mirror_reference_refs`
   - `split_receipt_requiredized`
   - `protocol_feedback_activity_detected`
   - `protocol_feedback_activity_refs`
9. Protocol layer remains business-data neutral:
   - channel contract fields must remain generic and must not include tenant/business constants.
10. Protocol-entry bootstrap readiness is mandatory when protocol lane is selected:
   - if `resolved_work_layer=protocol` or `protocol_triggered=true`, canonical protocol-feedback channel roots must be ready before protocol conclusion payload emission.
   - when roots are missing, deterministic bootstrap is allowed only if it emits SSOT-linked receipt under canonical outbox/index paths.
11. Strict operations must fail-closed when bootstrap readiness is not proven:
   - `IP-PFB-CH-004`: `protocol_layer_without_bootstrap_readiness`
   - `IP-PFB-CH-005`: `bootstrap_receipt_missing_or_unlinked`
12. three-plane/full-scan must expose bootstrap readiness telemetry:
   - `protocol_feedback_bootstrap_status`
   - `protocol_feedback_bootstrap_mode` (`preexisting` / `auto_created` / `failed`)
   - `bootstrap_created_paths`
   - `bootstrap_receipt_path`
13. Protocol-feedback activity detector is mandatory for split-receipt requiredization bridge:
   - activity signal is true when any canonical root has evidences:
     - `runtime/protocol-feedback/outbox-to-protocol/*`
     - `runtime/protocol-feedback/evidence-index/*`
     - `runtime/protocol-feedback/upgrade-proposals/*`
   - detector output must be machine-readable (`protocol_feedback_activity_detected`, `protocol_feedback_activity_refs`).
14. Strict operations must fail-closed if protocol-feedback activity exists but split-receipt remains `SKIPPED_NOT_REQUIRED`:
   - `IP-PFB-CH-006`: `split_receipt_requiredization_missing_under_activity`
15. FIX boundary (non-merge rule):
   - `FIX-029` covers `ASB-RQ-075..078` (canonical reply channel + sidecar `IP-PFB-*` blocking + split-receipt requiredization bridge),
   - bootstrap readiness (`ASB-RQ-079..081`) remains in `FIX-030` and must be audited independently.
16. Anti-deadlock bootstrap rule (strict lanes):
   - missing canonical roots are a recoverable bootstrap state, not an automatic terminal failure,
   - bootstrap gate must support deterministic constructor flow under `<resolved_pack_path>/runtime/protocol-feedback/` (create missing roots + emit bootstrap receipt + SSOT index linkage),
   - check-only implementation that rejects missing roots without bootstrap attempt is non-compliant for `FIX-030`,
   - strict fail-closed applies only when constructor flow is unavailable/disabled or bootstrap proof is incomplete (`IP-PFB-CH-004/005`).

#### 5.8.17 `protocol_entry_candidate_clarification_bridge_contract_v1` (P0)

Goal:

1. Prevent protocol-lane deadlock where weak governance concern signals cannot enter protocol workflow unless explicit `work_layer=protocol` is provided.
2. Convert weak protocol concern statements into deterministic clarification and evidence-seeding flow, rather than silent fallback.
3. Keep dual-lane stability by allowing instance execution continuity while protocol evidence chain is being built.

Mandatory semantics:

1. Layer resolution must classify protocol-entry decisions into machine-readable states:
   - `INSTANCE_DEFAULT`
   - `PROTOCOL_DIRECT`
   - `PROTOCOL_CANDIDATE`
2. `PROTOCOL_CANDIDATE` must be emitted when protocol concern signal is present but direct strict trigger evidence is insufficient.
3. `PROTOCOL_CANDIDATE` must not silently downgrade to `INSTANCE_DEFAULT` without clarification workflow evidence.
4. Candidate clarification workflow is mandatory and must emit:
   - `clarification_required=true`
   - `clarification_questions` (deterministic set)
   - `candidate_reason`
   - `candidate_confidence`
5. Clarification question set must include at least:
   - `which_gate_or_stage_failed`
   - `latest_replay_or_evidence_path`
   - `expected_protocol_optimization_target`
6. Candidate flow must seed protocol-feedback SSOT artifacts even before final protocol conclusion:
   - canonical outbox seed under `runtime/protocol-feedback/outbox-to-protocol/`
   - canonical evidence linkage under `runtime/protocol-feedback/evidence-index/`
7. Candidate seed artifacts must remain protocol-sanitized (no tenant/customer/business constants).
8. Promotion and fallback transitions must be explicit:
   - candidate + sufficient evidence -> `PROTOCOL_DIRECT`
   - candidate + unresolved/timeout -> `INSTANCE_DEFAULT` with unresolved candidate receipt retained
9. Strict operations must fail-closed when candidate governance flow is violated:
   - `IP-LAYER-CAND-001`: candidate silently downgraded without clarification receipt
   - `IP-LAYER-CAND-002`: candidate clarification questions missing/incomplete
   - `IP-LAYER-CAND-003`: candidate seed not archived to canonical protocol-feedback path
   - `IP-LAYER-CAND-004`: candidate seed exists but evidence-index linkage missing
10. three-plane/full-scan must expose candidate bridge telemetry:
   - `protocol_entry_decision`
   - `candidate_reason`
   - `clarification_required`
   - `clarification_questions`
   - `candidate_seed_outbox_ref`
   - `candidate_seed_index_ref`
   - `candidate_promotion_status`

#### 5.8.18 `protocol_inquiry_followup_chain_contract_v1` (P0)

Goal:

1. Convert weak protocol concerns into deterministic analysis + follow-up flow instead of pass/block deadlock.
2. Ensure protocol conclusions are emitted only after canonical protocol-feedback seed/index linkage is established.
3. Prevent business-scene statements from contaminating protocol-layer governance evidence.

Mandatory semantics:

1. Inquiry state machine is mandatory when protocol concern exists but evidence is incomplete:
   - `QUESTION_REQUIRED`
   - `EVIDENCE_PENDING`
   - `READY_FOR_PROTOCOL_FEEDBACK`
   - `FEEDBACK_EMITTED`
2. Inquiry state must emit deterministic follow-up question set at minimum:
   - `which_gate_or_stage_failed`
   - `latest_replay_or_evidence_path`
   - `expected_protocol_optimization_target`
3. Inquiry receipts must classify signal origin:
   - `signal_origin in {governance_statement, business_statement, mixed_statement}`
4. `business_statement` or `mixed_statement` inputs must produce a protocol-sanitized paraphrase receipt before protocol conclusion promotion.
5. Raw customer/tenant/business constants from inquiry text must not be copied into governance/review protocol conclusions.
6. Transition to `READY_FOR_PROTOCOL_FEEDBACK` requires canonical protocol-feedback seed + index linkage evidence.
7. Protocol conclusion emission requires `FEEDBACK_EMITTED`; otherwise strict fail-closed.
8. Strict fail-closed errors:
   - `IP-LAYER-INQ-001`: inquiry required but deterministic follow-up set missing
   - `IP-LAYER-INQ-002`: inquiry evidence missing/stale for declared protocol conclusion
   - `IP-LAYER-INQ-003`: canonical protocol-feedback seed/index linkage missing before conclusion
   - `IP-LAYER-INQ-004`: unsanitized business statement promoted into protocol conclusion
9. three-plane/full-scan telemetry must expose:
   - `inquiry_state`
   - `followup_question_set`
   - `signal_origin`
   - `sanitization_paraphrase_ref`
   - `protocol_feedback_seed_ref`
   - `protocol_feedback_index_ref`
10. Canonical inquiry receipt schema is mandatory (machine-readable, append-only):
   - `inquiry_id`
   - `inquiry_state`
   - `followup_question_set`
   - `signal_origin`
   - `sanitization_paraphrase_ref`
   - `protocol_feedback_seed_ref`
   - `protocol_feedback_index_ref`
   - `next_transition`
   - `updated_at`
11. Deterministic transition guards are mandatory:
   - `QUESTION_REQUIRED -> EVIDENCE_PENDING` requires complete deterministic follow-up set,
   - `EVIDENCE_PENDING -> READY_FOR_PROTOCOL_FEEDBACK` requires canonical seed + evidence-index linkage,
   - `READY_FOR_PROTOCOL_FEEDBACK -> FEEDBACK_EMITTED` requires protocol-feedback emission receipt.
12. Anti-starvation convergence policy is mandatory:
   - each inquiry chain must carry `followup_round_count`, `max_followup_rounds`, `evidence_ttl_hours`,
   - if rounds/TTL exceed without valid transition, strict lanes must fail-closed as stale inquiry evidence (`IP-LAYER-INQ-002`) and persist unresolved inquiry receipt.
13. Inquiry-to-requiredization bridge is mandatory:
   - unresolved inquiry chain (`rounds>=2` or TTL exceeded) must emit requiredization trigger class `inquiry_chain_unresolved`,
   - trigger receipt must be archived in canonical protocol-feedback outbox + evidence-index,
   - strict lanes must not remain warn-only after this trigger.

#### 5.8.19 `protocol_feedback_entry_component_orchestration_contract_v1` (P0 orchestration profile)

Goal:

1. Keep one protocol system with component-level dependency control for `FIX-029..FIX-032` while preserving audit non-merge boundaries.
2. Eliminate implementation drift where later protocol-entry logic lands before canonical channel/requiredization foundations are closed.
3. Keep strict-lane fail-closed semantics deterministic across channel/bootstrap/candidate/inquiry stages.

Mandatory semantics:

1. Stage dependency order is mandatory:
   - Stage-A (`FIX-029`, `ASB-RQ-075..078`): canonical channel + sidecar `IP-PFB-*` blocking + split requiredization bridge.
   - Stage-B (`FIX-030`, `ASB-RQ-079..081`): protocol bootstrap readiness gate.
   - Stage-C (`FIX-031`, `ASB-RQ-082..085`): candidate clarification bridge + canonical candidate seed linkage.
   - Stage-D (`FIX-032`, `ASB-RQ-086..089`): inquiry follow-up state machine + sanitization promotion boundary.
2. Cross-stage fail-closed propagation:
   - if Stage-A is open, Stage-B/C/D may not be labeled closure-ready,
   - if Stage-B is open, Stage-C/D may not claim protocol-entry closure,
   - if Stage-C is open, Stage-D may not claim inquiry-driven promotion closure.
3. Non-merge audit rule remains mandatory:
   - each stage keeps independent required gate verdict and replay package,
   - pass of one stage cannot substitute another stage.
4. Shared machine-readable telemetry contract (must be visible in three-plane/full-scan):
   - `protocol_feedback_reply_channel_status`
   - `protocol_feedback_activity_detected`
   - `protocol_feedback_activity_refs`
   - `split_receipt_requiredized`
   - `protocol_feedback_bootstrap_status`
   - `protocol_entry_decision`
   - `candidate_promotion_status`
   - `inquiry_state`
5. Unified strict-lane blocking error families:
   - channel/bootstrap: `IP-PFB-CH-*`
   - candidate bridge: `IP-LAYER-CAND-*`
   - inquiry chain: `IP-LAYER-INQ-*`
   - strict operations must treat all above families as fail-closed boundaries.
6. Unified implementation acceptance profile:
   - patch order must follow Stage-A -> Stage-B -> Stage-C -> Stage-D,
   - each stage must replay negative/positive samples before next stage merge.
7. Release lock rule:
   - `FIX-029..FIX-032` must all be `DONE + PASS` before protocol-entry closure can be marked release-ready.

#### 5.8.20 `work_layer_gate_set_split_contract_v1` (P0, FIX-033)

Goal:

1. Eliminate cross-lane hard blocking where instance self-drive execution is stopped by protocol publish gates.
2. Preserve strict protocol governance by enforcing protocol publish gates only when protocol lane is selected.
3. Keep lane routing auditable and machine-checkable in send-time and replay surfaces.

Mandatory semantics:

1. Lane-default rule:
   - if no explicit override is provided, `work_layer=instance` is default.
2. Gate-set routing rule:
   - `work_layer=instance` -> run `instance_required_checks` only,
   - `work_layer=protocol` -> run `protocol_required_checks` only.
3. `work_layer=dual` boundary:
   - `dual` is not a routable closure lane for strict operations (`update/readiness/e2e/ci`),
   - strict operations must fail-closed and require explicit rerun in one deterministic lane (`instance` or `protocol`).
4. Instance-lane non-blocking protocol publish boundary:
   - in `work_layer=instance`, protocol publish gates (including changelog/release-metadata protocol publish checks) must not block self-drive closure,
   - when protocol-relevant diff is detected in instance lane, emit deterministic protocol-feedback pending receipt instead of blocking.
5. Protocol-lane strict boundary:
   - in `work_layer=protocol`, protocol publish gates are mandatory and fail-closed on missing required publish artifacts.
6. Canonical protocol-feedback closure (protocol lane):
   - protocol conclusions must archive to canonical SSOT roots:
     - `runtime/protocol-feedback/outbox-to-protocol/`
     - `runtime/protocol-feedback/evidence-index/`
     - `runtime/protocol-feedback/upgrade-proposals/`
7. Lane consistency gate:
   - strict operations must fail-closed when `work_layer` and `applied_gate_set` mismatch.
8. Required machine-readable telemetry per governed round:
   - `work_layer`
   - `applied_gate_set`
   - `protocol_feedback_triggered`
   - `protocol_feedback_paths`
   - `lane_transition_reason`
9. send-time first-line stamp remains mandatory:
   - tail block must continue to expose `Layer-Context` and must stay consistent with applied gate set.
10. Mixed-lane prohibition remains mandatory:
   - same execution section cannot mix instance business closure and protocol governance proposal payload.
11. Suggested failure code family (`IP-LAYER-GATE-*`):
   - `IP-LAYER-GATE-001`: lane/gate-set mismatch in strict operations,
   - `IP-LAYER-GATE-002`: instance lane blocked by protocol publish gate,
   - `IP-LAYER-GATE-003`: protocol lane missing required publish gate replay,
   - `IP-LAYER-GATE-004`: protocol lane conclusion without canonical protocol-feedback closure evidence,
   - `IP-LAYER-GATE-005`: `work_layer=dual` used in strict closure operations.
12. Deterministic acceptance profile (must pass before closure claim):
   - sample A (`work_layer=instance`, protocol files changed, no changelog update): instance lane must not be blocked; protocol-feedback pending receipt required,
   - sample B (`work_layer=protocol`, protocol files changed, no changelog update): strict fail-closed required,
   - sample C (multi-round replay): each round must expose lane telemetry fields and protocol-feedback trigger/path evidence when applicable,
   - sample D (`work_layer=dual` in strict closure operation): deterministic fail-closed with rerun hint to `instance` or `protocol`.

#### 5.8.21 `protocol_context_lane_lock_contract_v1` (P0, FIX-034)

Goal:

1. Prevent protocol-governance sessions from silently falling back to `work_layer=instance` when intent text is missing.
2. Eliminate false-green closure where protocol diagnostics are reported while protocol lane gates were never active.

Mandatory semantics:

1. Protocol-context trigger must be explicit and machine-checkable:
   - explicit `work_layer=protocol`,
   - or active protocol session lane lock (`session_lane_lock=protocol`),
   - or protocol-governance intent classifier confidence above strict threshold.
2. In protocol-context sessions, empty/ambiguous intent must not silently downgrade to instance:
   - strict operations must fail-closed with explicit remediation hint (`provide --expected-work-layer protocol` or protocol lane lock receipt).
3. Session lane lock contract:
   - protocol lane lock must persist for current governed round until explicit exit receipt is written.
   - explicit exit receipt must be archived under canonical protocol-feedback channel and indexed:
     - `runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_*.json`
     - `runtime/protocol-feedback/evidence-index/INDEX.md`
   - unified exit writer entrypoint:
     - `python3 scripts/write_session_lane_lock_exit.py --identity-id <id> --catalog <catalog> --repo-catalog identity/catalog/identities.yaml --operation update --source-layer <global|project|env|auto> --exit-reason <reason> --json-only`
   - if a newer exit receipt is not present, strict instance-lane operations remain blocked by `IP-LAYER-GATE-007`.
   - creator update path must provide deterministic automation switch for exit emission (`--release-session-lane-lock`) before strict lane re-entry validation.
4. Required telemetry fields:
   - `protocol_context_detected`
   - `session_lane_lock`
   - `lane_resolution_decision`
   - `lane_resolution_blocked`
   - `lane_resolution_error_code`
5. Suggested error codes:
   - `IP-LAYER-GATE-006`: protocol context detected but lane resolution attempted default fallback.
   - `IP-LAYER-GATE-007`: protocol context requires explicit lane confirmation but no confirmation evidence provided.

#### 5.8.22 `run_pinned_protocol_baseline_freshness_contract_v1` (P0, FIX-035)

Goal:

1. Remove non-deterministic strict failures caused by protocol HEAD movement during a single long-running governed run.
2. Keep baseline freshness strict but evaluated against run-start immutable baseline anchor.

Mandatory semantics:

1. Every governed run (`update/readiness/e2e`) must persist:
   - `protocol_head_sha_at_run_start`
   - `baseline_reference_mode` (`run_pinned` / `live_head`).
2. Strict freshness checks inside the same run must compare execution report SHA against pinned run-start SHA, not moving live HEAD.
3. Live HEAD drift after run start must be surfaced as warning evidence and next-run action, not immediate in-run hard failure.
4. Required telemetry fields:
   - `protocol_head_sha_at_run_start`
   - `current_protocol_head_sha`
   - `head_drift_detected`
   - `baseline_status`
   - `baseline_error_code`
5. Suggested error/warning codes:
   - `IP-PBL-005`: run-pinned baseline anchor missing in strict operation.
   - `IP-PBL-006`: in-run baseline check attempted against live head while run-pinned mode required.

#### 5.8.23 `e2e_hermetic_runtime_import_contract_v1` (P0, FIX-036)

Goal:

1. Ensure e2e gate behavior is hermetic and independent of caller shell environment.
2. Remove `PYTHONPATH` external dependency drift between CI and local replay.

Mandatory semantics:

1. `scripts/e2e_smoke_test.sh` must bootstrap Python import path internally (or call package entrypoint that does so).
2. Direct invocation without external env preparation must pass import preflight:
   - `IDENTITY_CATALOG=... IDENTITY_IDS=... bash scripts/e2e_smoke_test.sh`.
3. Missing hermetic import path must fail with deterministic error code and actionable hint.
4. Required telemetry fields:
   - `e2e_hermetic_runtime_status`
   - `pythonpath_bootstrap_mode`
   - `import_preflight_status`
   - `import_preflight_error_code`
5. Suggested error code:
   - `IP-E2E-HERM-001`: hermetic import path preflight failed (e.g., `response_stamp_common` import unavailable).

#### 5.8.24 `skill_contract_execution_integrity_contract_v1` (P1, FIX-037)

Goal:

1. Keep skill protocol contracts executable-as-documented.
2. Prevent skill/runtime drift where documented command path is missing in repository.

Mandatory semantics:

1. Skill contract verification must check executable command existence for required skills referenced by protocol identities.
2. If command path is missing, strict mutation/release operations must emit warning/receipt and block only when skill is required by active profile policy.
3. Required telemetry fields:
   - `skill_contract_integrity_status`
   - `missing_skill_command_refs`
   - `required_skill_blocking`
   - `skill_contract_error_code`
4. Suggested error code:
   - `IP-SKILL-001`: required skill command target missing or non-executable.

#### 5.8.25 `strict_self_repair_two_phase_refresh_contract_v1` (P1-high, FIX-038)

Goal:

1. Avoid strict self-update self-lock for pure stale-baseline cases.
2. Keep strict guarantee while enabling one-command deterministic recovery.

Mandatory semantics:

1. When strict preflight fails solely due to stale baseline (`IP-PBL-001`-class) and no other P0 blockers exist:
   - phase A: run controlled baseline refresh substep,
   - phase B: re-run strict validation in same command context.
   - phase-A entry predicate must be explicit and fail-closed:
     - `baseline_error_code` must be in stale-baseline whitelist (`IP-PBL-001`-class only),
     - `stale_reasons` must be non-empty and each reason must be baseline-scoped.
   - baseline-mode violations (for example `IP-PBL-006`) must not enter phase A and must remain strict fail-closed.
2. If non-baseline blockers coexist, command remains strict fail-closed (no hidden downgrade).
3. Two-phase path must emit machine-readable execution trace:
   - `phase_a_refresh_applied`
   - `phase_b_strict_revalidate_status`
   - `phase_transition_reason`
   - `phase_transition_error_code`
   - trace reason taxonomy must distinguish:
     - `stale_baseline_only_detected`
     - `baseline_mode_violation`
4. Suggested error code:
   - `IP-UPG-BASE-001`: strict self-repair two-phase refresh unavailable when stale-baseline-only scenario detected.

#### 5.8.26 `requiredization_lane_scope_contract_v1` (P0, FIX-039)

Goal:

1. Prevent protocol governance requiredization from leaking into instance lane via historical artifact presence alone.
2. Preserve FIX-033 lane split intent (`instance` lane self-drive not blocked by unrelated protocol-history noise).

Mandatory semantics:

1. Auto-required promotion for protocol governance contracts (`semantic_routing_guard`, `split_receipt`, `vendor_namespace`, `sidecar`) must be scoped to current round linkage, not mere directory existence.
2. Requiredization effective trigger in strict operations must satisfy at least one current-round condition:
   - `resolved_work_layer=protocol`, or
   - `protocol_triggered=true` for this round, or
   - current-round receipt/batch linkage (`run_id` / `candidate_receipt_ref` / `inquiry_receipt_ref` / equivalent deterministic correlation key).
3. Historical activity without current-round linkage must remain non-blocking evidence in instance lane.
4. Required telemetry fields:
   - `requiredization_scope_decision`
   - `requiredization_scope_reason`
   - `requiredization_current_round_linked`
   - `requiredization_historical_activity_detected`
5. Suggested error code:
   - `IP-SPLIT-006`: requiredization scope leak detected (history-only activity promoted to strict required in instance lane).

#### 5.8.27 `split_receipt_activity_correlation_contract_v1` (P0, FIX-040)

Goal:

1. Ensure protocol-feedback activity detector is correlation-aware and does not treat stale/historical outbox files as current protocol intent.
2. Eliminate false strict failures (`IP-PFB-CH-006`) when current round did not enter protocol lane.

Mandatory semantics:

1. `_protocol_feedback_activity` style detectors must enforce current-round correlation:
   - bind evidence to at least one deterministic key (`run_id`, `seed_ref`, `candidate_receipt_ref`, `inquiry_receipt_ref`, or explicit linkage receipt).
2. Activity detectors must support bounded time window for stale evidence filtering.
3. Strict `split_receipt` fail-closed under activity (`IP-PFB-CH-006`) is allowed only when correlated current-round protocol activity is proven.
4. Required telemetry fields:
   - `activity_correlation_status`
   - `activity_correlation_key`
   - `activity_window_hours`
   - `activity_correlated_refs`
   - `activity_unscoped_refs`
5. Suggested error code:
   - `IP-PFB-CH-007`: protocol-feedback activity detected but current-round correlation missing.

#### 5.8.28 `expected_source_layer_validation_contract_v1` (P1, FIX-041)

Goal:

1. Prevent silent semantic downgrade of invalid `--expected-source-layer` input.
2. Keep strict lane caller intent machine-checkable and auditable.

Mandatory semantics:

1. Invalid `expected_source_layer` input must not be silently normalized in strict operations.
2. Strict operations must fail-closed (or emit explicit non-pass status) when invalid source layer enum is provided.
3. Non-strict operations may fallback, but must emit explicit downgrade telemetry.
4. Required telemetry fields:
   - `expected_source_layer_input`
   - `expected_source_layer_effective`
   - `expected_source_layer_validation_status`
   - `expected_source_layer_validation_error_code`
   - `source_layer_downgrade_applied`
5. Suggested error code:
   - `IP-SOURCE-LAYER-001`: invalid expected-source-layer input in strict operation.

#### 5.8.29 `required_contract_coverage_lane_partition_contract_v1` (P1, FIX-042)

Goal:

1. Reduce instance-lane noise and responsibility mixing in coverage aggregation.
2. Ensure protocol governance contracts are evaluated in correct lane policy.

Mandatory semantics:

1. Required coverage aggregator must support lane-aware target sets:
   - `instance_targets`
   - `protocol_targets`
   - optional `shared_targets`.
2. In `work_layer=instance`, protocol governance targets must not be hard-failed unless current-round protocol-entry correlation is present.
3. In `work_layer=protocol`, protocol governance targets remain required and fail-closed.
4. Required telemetry fields:
   - `coverage_lane`
   - `coverage_target_set`
   - `coverage_protocol_targets_included`
   - `coverage_protocol_targets_blocking`
5. Suggested error code:
   - `IP-COV-LANE-001`: lane-aware coverage policy missing or mismatched with resolved work layer.

#### 5.8.30 `prompt_runtime_state_externalization_contract_v1` (P1, FIX-043)

Goal:

1. Keep immutable prompt policy text separate from mutable runtime lifecycle state.
2. Eliminate prompt-file churn that can blur governance semantics and create unnecessary alignment drift.

Mandatory semantics:

1. Runtime lifecycle fields (`last_upgrade_run_id`, `last_upgrade_at`, `last_trigger_reasons` or equivalent mutable traces) must be written to dedicated runtime state artifact, not embedded into `IDENTITY_PROMPT.md` body.
2. `IDENTITY_PROMPT.md` remains policy/role/instruction contract and should change only when policy intent changes.
3. Prompt lifecycle validator must verify:
   - prompt hash / prompt version integrity, and
   - runtime lifecycle state artifact integrity (including binding with the active prompt hash/version).
4. Required telemetry fields:
   - `prompt_runtime_state_externalization_status`
   - `prompt_policy_hash`
   - `runtime_state_artifact_path`
   - `runtime_state_artifact_hash`
   - `prompt_runtime_state_binding_status`
5. Suggested error code:
   - `IP-PROMPT-STATE-001`: mutable runtime lifecycle state embedded in prompt policy file under strict lifecycle governance.

#### 5.8.31 `session_lane_lock_exit_writer_contract_v1` (P0, FIX-044)

Goal:

1. Provide a deterministic, auditable, machine-executable exit path for protocol lane locks.
2. Remove closure ambiguity where lock-exit semantics are documented but no unified writer entrypoint exists.

Mandatory semantics:

1. Exit writer must emit canonical receipt in protocol-feedback outbox:
   - `runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_*.json`
2. Exit writer must enforce evidence-index linkage in canonical index:
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
3. Exit writer payload must include:
   - `identity_id`
   - `actor_id`
   - `from_lock_receipt_ref`
   - `source_layer`
   - `exit_reason`
   - `generated_at`
4. Strict lane behavior remains fail-closed:
   - protocol lock present + no newer EXIT => strict instance lane blocked by `IP-LAYER-GATE-007`.
   - EXIT write failure / index linkage failure => `IP-LAYER-GATE-008/009` fail-closed in strict operations.
5. Update orchestration must expose an automation switch for deterministic exit emission:
   - `identity_creator.py update --release-session-lane-lock`.

### 5.9 `semantic_isolation_and_source_trust_contract_v1` (P0)

Goal:

1. Prevent protocol-layer semantic pollution between `protocol_vendor` and `business_partner` domains.
2. Ensure conclusion-layer evidence is built from trusted sources only.
3. Keep protocol layer free of concrete business scenario contamination.

#### 5.9.1 `protocol_vendor_semantic_isolation_contract_v1`

Mandatory semantics:

1. `protocol_vendor` tasks must not route into `business_partner` retrieval without explicit, auditable domain switch.
2. `business_partner` tasks must not write protocol-vendor API intelligence into conclusion-layer protocol outputs.
3. Domain switch requires machine-readable receipt fields:
   - `trigger_text`
   - `intent_domain_before`
   - `intent_domain_after`
   - `intent_confidence`
   - `approved_by` (if manual override)
4. Missing switch receipt under mixed-domain behavior is `FAIL_REQUIRED`.

#### 5.9.2 `external_source_trust_chain_contract_v1`

Mandatory semantics:

1. Every external source consumed by protocol-upgrade conclusions must carry trust tier:
   - `official`
   - `primary`
   - `secondary`
   - `unknown`
2. `unknown` tier is forbidden in conclusion-layer evidence.
3. `unknown` tier may only appear in candidate lead sections with explicit downgrade note and follow-up retrieval requirement.
4. Conclusion-layer statements require traceable `official/primary` references.

#### 5.9.3 `protocol_data_sanitization_boundary_v1`

Mandatory semantics:

1. Protocol-layer artifacts (contracts/validators/gates/review/governance) must not include tenant-specific business scenarios, customer identifiers, or sensitive business constants.
2. Protocol examples must use neutral placeholders and generic domain descriptors.
3. Business-instance details are allowed only in instance-level runtime artifacts and must not be promoted into protocol SSOT contract language.
4. Violation of sanitization boundary in protocol closure payloads is `FAIL_REQUIRED`.

### 5.10 `platform_optimization_discovery_and_feeding_contract_v1` (P1 with P0 requiredization bridge)

Goal:

1. Upgrade protocol from passive fault prevention to active optimization discovery for high-frequency platform requests.
2. Standardize one-shot executable feeding packages for vibe-coding style workflows.

#### 5.10.1 `platform_optimization_discovery_trigger_v1`

Mandatory semantics:

1. Trigger when optimization-intent signal repeats across two consecutive rounds for same platform class.
2. Trigger when user signals repeated "flow not closed" outcomes under platform optimization context.
3. Trigger output must include:
   - discovery scope
   - official-doc retrieval set
   - cross-validation summary
   - upgrade proposal link in protocol-feedback outbox.

#### 5.10.2 `vibe_coding_feeding_pack_contract_v1`

Standard output pack (single-directory upload ready):

1. `PROMPT_MAIN.txt`
2. `INPUT_FILES/`
3. `RUN_ORDER.txt`
4. `REVIEW_REQUEST.txt`

Mandatory semantics:

1. Pack output must be deterministic and reproducible from protocol-feedback evidence chain.
2. Pack must remain business-data sanitized at protocol layer (no tenant-sensitive constants in template text).
3. Pack generation outcome must be machine-readable and traceable in evidence index.

#### 5.10.3 `capability_fit_self_drive_optimization_contract_v1`

Goal:

1. Ensure protocol can continuously improve capability match quality even when current toolchain is already usable.
2. Convert ad-hoc optimization discussions into deterministic, machine-checkable review cycles.

Mandatory semantics:

1. Optimization cycle is `inventory-first`:
   - every cycle must snapshot currently installed/available capability inventory before introducing new external candidates.
2. Optimization cycle is `compose-before-discover`:
   - at least one `existing_composition_candidate` must be evaluated before selecting external installation path.
3. External discovery is conditional:
   - allowed only when existing composition is `not_sufficient` or `not_cost_effective`, and decision basis is machine-readable.
4. Every decision cycle must emit a `capability_fit_matrix` with required fields:
   - `candidate_id`
   - `candidate_type` (`existing_composition` / `external_candidate`)
   - `fit_score`
   - `risk_score`
   - `operational_cost_score`
   - `provenance_ref`
   - `decision` (`selected` / `rejected`)
5. Exactly one candidate in a decision window may be `selected`.
6. Each selected plan must include:
   - `fallback_ref`
   - `rollback_ref`
   - `review_interval_days`
   - `next_review_at`
7. If review is overdue, status must become `WARN_STALE_OPTIMIZATION_REVIEW` and cannot be represented as full closure.

#### 5.10.4 `capability_fit_roundtable_evidence_contract_v1`

Mandatory semantics:

1. For optimization decisions affecting `tool_routing`, `vendor_api_discovery`, or `solution_architecture`, roundtable review is mandatory.
2. Roundtable outputs must separate `fact` and `inference` in machine-readable structure.
3. Final selected decision must map to at least one `fact` evidence reference.
4. Source priority for fit decisions is fixed:
   - official vendor docs / official protocol specs > standard organization specs > community mirrors/wrappers.

#### 5.10.5 `discovery_requiredization_contract_v1`

Goal:

1. Prevent permanent "soft-pass" behavior for discovery contracts once repeated risk signals are observed.
2. Upgrade discovery checks from `not required` to `required` deterministically when trigger conditions are met.

Requiredization scope:

1. `tool_installation_contract`
2. `vendor_api_discovery_contract`
3. `vendor_api_solution_contract`

Mandatory semantics:

1. Requiredization trigger must be machine-evaluated from replay evidence and protocol-feedback records.
2. Trigger conditions (`any true -> requiredization_triggered=true`):
   - same platform-class optimization intent repeats in `>=2` consecutive rounds;
   - "usable but quality-not-sufficient" feedback repeats in `>=2` rounds in the same audit window;
   - at least `1` closure failure is explicitly attributed to capability/tooling gap.
3. When triggered, contracts in requiredization scope must be flipped from `required=false` to `required=true` with deterministic writeback.
4. Requiredization writeback must emit a machine-readable receipt including:
   - `requiredization_triggered`
   - `trigger_classes`
   - `window_rounds`
   - `evidence_refs`
   - `previous_required_state`
   - `new_required_state`
   - `requiredized_at`
5. Requiredization receipt must be archived in protocol-feedback SSOT:
   - outbox batch
   - evidence-index linkage
6. Requiredization gate errors (`IP-DREQ-*`):
   - `IP-DREQ-001`: trigger condition met but requiredization not applied
   - `IP-DREQ-002`: requiredization applied but receipt missing/incomplete
   - `IP-DREQ-003`: requiredization receipt not linked in protocol-feedback SSOT index
   - `IP-DREQ-004`: requiredized discovery validators missing from CI required validator set
7. Non-blocking expiry rule:
   - discovery-related non-blocking warnings may exist during exploration window;
   - if unresolved beyond configured expiry days, status must auto-escalate to `FAIL_REQUIRED`.

#### 5.10.6 `discovery_required_coverage_subgate_contract_v1`

Mandatory semantics:

1. `validate_required_contract_coverage.py` must expose discovery-subset metrics for requiredized contracts:
   - `discovery_required_total`
   - `discovery_required_passed`
   - `discovery_required_coverage_rate`
   - `discovery_required_gate_failed`
2. Optional discovery contracts may remain `SKIPPED_NOT_REQUIRED` before requiredization; after requiredization they must count toward required coverage.
3. Release/readiness closure surfaces must support a dedicated threshold:
   - `min_discovery_required_coverage`
4. If discovery requiredization is active and discovery coverage is below threshold, closure must fail-closed.

## 6) Required Protocol Changes

### 6.1 Core script change surface

1. `scripts/identity_creator.py`
2. `scripts/resolve_identity_context.py`
3. activation/session-pointer sync routine in `scripts/identity_creator.py`
4. `scripts/validate_identity_state_consistency.py`
5. `scripts/validate_identity_session_pointer_consistency.py`
6. `scripts/collect_identity_health_report.py`
7. `scripts/validate_identity_health_contract.py`
8. `scripts/execute_identity_upgrade.py`
9. `scripts/validate_identity_runtime_mode_guard.py`
10. `scripts/use_project_identity_runtime.sh`
11. report writers/readers persisting `identity_home` / `catalog_path` / `resolved_pack_path`
12. `scripts/execute_identity_upgrade.py` writeback branch and closure payload writer
13. `scripts/validate_agent_handoff_contract.py` (post-execution dependency for writeback continuity)
14. `scripts/validate_identity_update_lifecycle.py`
15. protocol-feedback outbox writer and feedback-batch serializer surfaces
16. vendor/biz retrieval router surfaces used by protocol-feedback sidecar
17. gate/report surfaces persisting `intent_domain` / `intent_confidence` / `classifier_reason`
18. `validate_instance_base_repo_write_boundary` (new validator surface)
19. `validate_protocol_feedback_ssot_archival` (new validator surface)
20. readiness scope passthrough chain in `scripts/release_readiness_check.py` (`--scope` forwarding to runtime-mode/scope guards)
21. replay/scan visibility surfaces exposing `reply_stamp_missing_count`
22. `validate_protocol_vendor_semantic_isolation` (new validator surface)
23. `validate_external_source_trust_chain` (new validator surface)
24. protocol-feedback source tier tagging + conclusion-layer evidence writer surfaces
25. protocol-layer sanitization guard surfaces for governance/review outputs
26. platform optimization discovery trigger orchestration and report writer surfaces
27. vibe-coding feeding pack builder surfaces (`PROMPT_MAIN/INPUT_FILES/RUN_ORDER/REVIEW_REQUEST`)
28. capability inventory snapshot + fit-matrix emission surfaces
29. compose-before-discover arbitration surfaces in capability orchestration
30. optimization review freshness status writer surfaces (`next_review_at` + stale warnings)
31. roundtable fact/inference evidence mapping writer surfaces for optimization decisions
32. discovery requiredization state writer surfaces (`requiredization_triggered`, trigger classes, required-state transitions)
33. CI required-validator set synchronizer for requiredized discovery contracts
34. required-contract coverage engine extension for discovery-subset hard threshold (`min_discovery_required_coverage`)
35. actor-session multibinding storage serializer + CAS write precondition + append-only rebind receipt writer surfaces
36. protocol-feedback canonical reply-channel validator + primary/mirror channel classifier surfaces
37. sidecar blocking-prefix synchronizer surfaces (`IP-PFB-*` inclusion in strict lanes)
38. split-receipt requiredization bridge when protocol-feedback activity is detected in strict operations

### 6.2 New validators/tools (validator id and tool id)

1. `validate_actor_session_binding`
2. `validate_no_implicit_switch`
3. `validate_cross_actor_isolation`
4. `render_identity_response_stamp`
5. `validate_identity_response_stamp`
6. `refresh_identity_session_status`
7. `validate_identity_actor_health_profile`
8. `validate_identity_heal_replay_closure`
9. `validate_identity_response_stamp_blocker_receipt`
10. `validate_identity_session_refresh_status`
11. `validate_identity_pack_path_canonical`
12. `validate_identity_execution_report_path_contract`
13. `validate_identity_home_catalog_alignment`
14. `validate_fixture_runtime_boundary`
15. `validate_writeback_continuity`
16. `validate_post_execution_mandatory`
17. `validate_semantic_routing_guard`
18. `validate_vendor_namespace_separation`
19. `validate_protocol_feedback_sidecar_contract`
20. `validate_instance_base_repo_write_boundary`
21. `validate_protocol_feedback_ssot_archival`
22. `validate_identity_response_stamp` (reply-channel coverage mode, emits `reply_stamp_missing_count`)
23. `validate_protocol_vendor_semantic_isolation`
24. `validate_external_source_trust_chain`
25. `validate_protocol_data_sanitization_boundary`
26. `trigger_platform_optimization_discovery` (tool/trigger surface)
27. `build_vibe_coding_feeding_pack` (tool surface)
28. `validate_identity_capability_fit_optimization`
29. `validate_capability_composition_before_discovery`
30. `validate_capability_fit_review_freshness`
31. `trigger_capability_fit_review` (tool/trigger surface)
32. `build_capability_fit_matrix` (tool surface)
33. `validate_discovery_requiredization`
34. `validate_required_contract_coverage` (discovery-subset threshold mode)
35. `validate_actor_session_multibinding_concurrency`
36. `validate_protocol_feedback_reply_channel`

### 6.3 Gate wiring surfaces

1. `scripts/identity_creator.py validate`
2. `scripts/e2e_smoke_test.sh`
3. `scripts/release_readiness_check.py`
4. `scripts/full_identity_protocol_scan.py`
5. `scripts/report_three_plane_status.py`
6. `.github/workflows/_identity-required-gates.yml`

Health/heal closure must be wired in the same surfaces through:

1. actor-risk profile checks in health report generation.
2. deterministic health report contract validation (`--report` binding in closure flows).
3. heal replay closure validation (`health -> heal --apply -> validate`).

Response-stamp closure must be wired in the same surfaces through:

1. dynamic stamp rendering before user-facing output.
2. stamp contract validation (non-hardcoded + redaction + field completeness).
3. mismatch fail-closed behavior (`blocker_receipt` before any business payload).

Refresh closure must be wired in the same surfaces through:

1. on-demand `refresh_identity_session_status` output collection.
2. refresh output contract validation (including protocol baseline fields).
3. consistent actor/baseline visibility in three-plane and full-scan outputs.

Path-governance closure must be wired in the same surfaces through:

1. catalog/runtime canonical path check (`pack_path_canonical_gate`).
2. report path contract check (`resolved_pack_report_gate`).
3. home/catalog alignment check (`identity_home_catalog_alignment_gate`).
4. fixture/runtime boundary check (`fixture_runtime_boundary_gate`).

Writeback-continuity closure (Track-A) must be wired in the same surfaces through:

1. `validate_writeback_continuity` and `validate_post_execution_mandatory` invocation after upgrade execution.
2. `writeback_mode/degrade_reason/risk_level` mandatory field checks in readiness/e2e/scan pipelines.
3. canonical report path parity check between execution output and all gate consumers.
4. CI required-gates deterministic fail-closed on `IP-WRB-*` when contract is required.

Semantic-routing closure (Track-B) must be wired in the same surfaces through:

1. `validate_semantic_routing_guard` and `validate_vendor_namespace_separation` on feedback artifacts.
2. required-gates fail-closed on `IP-SEM-*`.
3. sidecar escalation only when semantic violation crosses governance boundary (`P0-blocking`).

Governance-boundary hotfix lane closure must be wired in the same surfaces through:

1. `validate_instance_base_repo_write_boundary` (`docs allow` + `protocol/code deny`, fail-closed).
2. `validate_protocol_feedback_ssot_archival` (outbox + evidence-index SSOT archival required, mirror-only fail-closed).
3. readiness explicit `--scope` passthrough to runtime mode/scope guards under dual-catalog arbitration.
4. reply-channel stamp observability output (`reply_stamp_missing_count`) in replay/three-plane/full-scan surfaces.

Semantic isolation + source trust closure must be wired in the same surfaces through:

1. `validate_protocol_vendor_semantic_isolation` before conclusion-layer protocol-feedback output emission.
2. `validate_external_source_trust_chain` on external references included in upgrade conclusions.
3. required-gates fail-closed on semantic/source/sanitization violations (`IP-SEM-*`, `IP-SRC-*`, `IP-DSN-*`).
4. protocol-layer sanitization boundary checks to prevent tenant/business scenario leakage into governance contracts.

Platform optimization discovery + feeding-pack enhancement (P1) should be wired in the same surfaces through:

1. optimization-intent trigger evaluation in `identity_creator` and scan/report surfaces.
2. machine-readable discovery receipts in protocol-feedback outbox/evidence-index.
3. deterministic `vibe_coding_feeding_pack_contract_v1` artifact generation (`PROMPT_MAIN`, `INPUT_FILES`, `RUN_ORDER`, `REVIEW_REQUEST`).

Discovery requiredization bridge (P0) must be wired in the same surfaces through:

1. trigger classifier -> contract `required` state transition writeback.
2. requiredization receipt archival to protocol-feedback outbox + evidence-index.
3. CI required validator set synchronization for requiredized discovery trio.
4. discovery-subset coverage threshold enforcement (`min_discovery_required_coverage`) in release/readiness closure surfaces.

Actor-session multibinding concurrency closure (P0) must be wired in the same surfaces through:

1. canonical actor binding multi-entry schema validation (`actor_id + session_id` uniqueness and peer-entry preservation).
2. CAS compare token validation before canonical binding mutation.
3. non-activation mutation denial checks in strict operation lanes.
4. append-only rebind receipt emission + linkage visibility in three-plane/full-scan outputs.
5. required-gates fail-closed on `IP-ASB-MB-*` under strict/release lanes.

Protocol-feedback canonical reply-channel closure (P0) must be wired in the same surfaces through:

1. canonical path validation for protocol-feedback primary reply channel.
2. fail-closed strict-lane guard when non-standard path is promoted as primary.
3. sidecar blocking-prefix extension to include `IP-PFB-*`.
4. split-receipt requiredization bridge when protocol-feedback activity evidence exists.
5. machine-readable channel compliance fields in three-plane/full-scan surfaces.
6. protocol-entry bootstrap readiness gate before protocol conclusion emission (strict fail-closed if readiness evidence is missing).

Protocol-entry candidate clarification bridge (P0) must be wired in the same surfaces through:

1. layer-intent classifier emits `PROTOCOL_CANDIDATE` decision state when weak protocol concern exists.
2. candidate clarification question generator emits deterministic question set and machine-readable candidate receipt.
3. candidate seed writer archives to canonical protocol-feedback outbox + evidence-index before protocol conclusion.
4. strict-lane fail-closed checks for silent candidate downgrade or missing candidate seed linkage.
5. three-plane/full-scan telemetry exposure for candidate decision and promotion status.

Protocol inquiry follow-up chain (P0) must be wired in the same surfaces through:

1. layer-intent and candidate bridge adapters emit inquiry states and deterministic follow-up receipts.
2. inquiry classifier emits `signal_origin` and sanitization paraphrase receipts for non-governance-native inputs.
3. strict-lane adapters block protocol conclusion until canonical protocol-feedback seed/index linkage is ready.
4. three-plane/full-scan/readiness/e2e/CI surfaces expose inquiry telemetry and `IP-LAYER-INQ-*` fail-closed errors.

Capability-fit self-drive optimization enhancement (P1) should be wired in the same surfaces through:

1. periodic capability inventory snapshot and fit-matrix generation.
2. compose-before-discover decision gate (`existing composition` must be evaluated first).
3. stale-review warning visibility in health/readiness/scan/three-plane outputs.
4. mandatory roundtable fact/inference evidence mapping for selected optimization plans.

Vendor/API chain must be wired in the same surfaces through:

1. `scripts/validate_identity_vendor_api_discovery.py`
2. `scripts/validate_identity_vendor_api_solution.py`
3. `scripts/validate_required_contract_coverage.py`

Kernel extension requirement:

1. The same coverage and evidence semantics must be gradually extended to `skill` / `mcp` / `tool` capability validators and release surfaces.
2. Migration must keep current vendor/tool gates backward-compatible while introducing kernel-level aggregation outputs.

### 6.3A P0 mandatory confirmation matrix (multi-agent x multi-identity)

This subsection is a no-ambiguity lock for architect and auditor communication.
The eleven items below are mandatory protocol targets and must be treated as one closure set.

| Confirm item | Mandatory protocol statement | Acceptance signal (must be explicit) | Current baseline interpretation |
| --- | --- | --- | --- |
| C1 | Session model must move from `single-active` to actor-scoped binding (`actor_id` as first-class runtime key). | Runtime no longer uses global single-active as authoritative control for activation/consistency decisions. | Closure replayed and audit-passed (`ASB-RQ-010`, `FIX-015`, review `16.7.13` + `16.7.17`). |
| C2 | New contract `actor_session_binding_contract_v1` is required. | Contract schema fields and validation behavior are implemented and versioned. | Implemented and validated via actor-binding replay chain (`ASB-RQ-001/003`, review `16.7.13` + `16.7.17`). |
| C3 | Canonical source of truth must be `<catalog_dir>/session/actors/<actor_id>.json`. | Resolver and validators read actor-scoped canonical records by default. | Canonical actor-session source behavior verified in replay (`ASB-RQ-001`, review `16.7.13` + `16.7.17`). |
| C4 | Legacy `active_identity.json` is compatibility mirror only (not authoritative). | Any authoritative decision that still depends on legacy pointer is removed. | Authoritative decision path is actor-scoped; legacy pointer retained as compatibility mirror (`ASB-RQ-002/010`, review `16.7.13` + `16.7.17`). |
| C5 | Three new validators are mandatory: `validate_actor_session_binding`, `validate_no_implicit_switch`, `validate_cross_actor_isolation`. | Scripts exist, produce stable machine-readable outputs, and are referenced by acceptance gates. | Validators are wired and replayed with pass outcomes (`ASB-RQ-003/004/005`, review `16.7.13` + `16.7.17`). |
| C6 | Gate wiring must cover `identity_creator`, `e2e_smoke_test.sh`, `release_readiness_check.py`, `full_identity_protocol_scan.py`, `report_three_plane_status.py`, and CI required-gates workflow. | Wire-up evidence exists in code and acceptance output across all listed surfaces. | Six-surface + CI wiring evidence is available and replayed (`ASB-RQ-009`, review ledger fix-chain sections). |
| C7 | Path governance must be canonical and mixed-source safe across catalog/runtime/report surfaces. | Canonical path gates pass and no relative or cross-domain ambiguous path tuple appears in closure evidence. | Canonical path governance gates are audit-passed (`ASB-RQ-028/029/030/031`, review `FIX-002~FIX-007`). |
| C8 | Governance-boundary lane must be machine-enforced (`base-repo mutation boundary` + `feedback SSOT archival` + `readiness scope arbitration` + `reply-stamp missing-turn counter`). | required gates are wired and replay evidence proves docs-only pass, protocol/code mutation fail, mirror-only fail, no-scope ambiguity fail, and zero missing-stamp turns for closure claim. | Closure replayed and audit-passed (`ASB-RQ-037/038/039/040`, `HOTFIX-P0-004/005/006/007`, review `16.6.8` + `16.7.17` + `16.7.18`). |
| C9 | Strict execution and reply channels must share one coherent identity tuple in dual-catalog lanes (no command/reply drift). | command-target identity/catalog tuple and reply identity stamp tuple are machine-compared; mismatch is fail-closed with blocker receipt. | validator + six-surface wiring landed (`ASB-RQ-067`, `IP-ASB-CTX-*`); replay closure pending audit verdict. |
| C10 | Same-actor binding writes must be multi-session safe and conflict-controlled (no single-record overwrite semantics). | canonical actor binding write path is `actor_id + session_id` keyed with CAS precondition and append-only receipt; non-activation write attempts fail-closed. | implementation landed (`FIX-028`): multibinding store + CAS mutation boundary + required validator/six-surface wiring; independent replay audit pending. |
| C11 | Protocol-feedback reply channel must be canonical and strict-lane fail-closed; split-receipt cannot silently skip under feedback activity; protocol-layer entry must prove bootstrap readiness. | canonical reply-channel gate + sidecar `IP-PFB-*` blocking + split-receipt requiredization bridge + bootstrap-readiness gate are all wired and replayed in strict operations. | implementation landed (`FIX-029/030`, commit `a95f5a2`); independent replay audit pending final verdict. |

Hard interpretation rules:

1. C1~C11 are jointly mandatory for P0 closure; partial completion cannot be labeled as implementation complete.
2. Narrative claims cannot override section 6.4 ledger states and section 6.5 unlock formula.
3. C1~C11 must all be `DONE` before this topic can be declared runtime-closed; authoritative closure state is tracked in section `6.4A` + review ledger latest audit verdicts.

### 6.3B Status synchronization note (2026-03-01, anti-drift)

This subsection prevents ambiguity between the baseline rows above and current replay evidence.

1. `IP-ENV-002` remains a required fail-closed gate (not a false-positive class by itself).
2. The required upgrade objective is:
   - keep `IP-ENV-002` fail-closed behavior for ambiguous dual-catalog resolution, and
   - ensure explicit `--scope` passthrough lets readiness proceed deterministically.
3. Governance-boundary hotfix lane (`ASB-RQ-037/038/039`) is implementation-closed with replay evidence in review ledger:
   - `validate_instance_base_repo_write_boundary`
   - `validate_protocol_feedback_ssot_archival`
   - readiness `--scope` passthrough chain.
4. Concurrent activation model migration (`ASB-RQ-010`, `ASB-RC-001~005`) is replay-closed in current audit window:
   - actor-scoped multi-active behavior is validated with cross-actor replay evidence,
   - closure is anchored by committed patch + audit verdict (`FIX-015`, review `16.7.13` + `16.7.17`).
5. Strict user-visible lock-bound stamp lane (`HOTFIX-P0-008` / `FIX-020`) is replay-closed:
   - strict mismatch must fail-closed (`IP-ASB-STAMP-001` / `IP-ASB-STAMP-SESSION-001`),
   - inspection mode keeps observability non-blocking,
   - closure replay is synchronized in review `16.7.17` + `16.7.18`.
6. New P0 lane (`ASB-RQ-067`) has implementation landing for execution-vs-reply tuple coherence:
   - command lane and reply lane must share same identity/catalog tuple under strict operations,
   - dual-domain mismatch must fail-closed with `IP-ASB-CTX-*`,
   - lane remains release-blocking until replay closure is audit-confirmed.

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
| ASB-RQ-010 | single-active removal from activation/consistency path | `identity_creator.py`, `identity_installer.py`, `validate_identity_state_consistency.py`, `validate_identity_session_pointer_consistency.py`, `compile_identity_runtime.py` | P0 | VERIFIED | actor-scoped multi-active patch is committed and replay-audited (`FIX-015`) |
| ASB-RQ-011 | vendor discovery/solution baseline gates (legacy chain) remain wired and compatible | `validate_identity_vendor_api_discovery.py`, `validate_identity_vendor_api_solution.py`, `validate_required_contract_coverage.py` | P1 | GATE_READY | Existing chain already wired in protocol gates |
| ASB-RQ-012 | shot-mode/source-tier/spec-hash strict enforcement (vendor reports) | same validators as ASB-RQ-011 | P1 | SPEC_READY | Spec declared in 5.4; current validators not strict on these fields |
| ASB-RQ-013 | kernel-level capability evolution coverage aggregation | new kernel-level coverage surfaces | P1 | SPEC_READY | Spec declared in 5.5; implementation pending |
| ASB-RQ-014 | actor-risk health profile coverage (binding/lease/implicit-switch/pointer) is mandatory and machine-counted | `collect_identity_health_report.py`, `validate_identity_actor_health_profile` (new) | P0 | SPEC_READY | Spec defined in 5.3A; implementation pending |
| ASB-RQ-015 | heal apply supports actor-centric repair branches with deterministic output refs | `identity_creator.py heal`, `validate_identity_heal_replay_closure` (new) | P0 | SPEC_READY | Spec defined in 5.3A; implementation pending |
| ASB-RQ-016 | deterministic report-binding in closure gates (explicit `--report` for health contract checks) | readiness/e2e/CI health-contract invocation surfaces | P0 | SPEC_READY | Anti-stale closure rule defined in 5.3A; wiring pending |
| ASB-RQ-017 | health-heal-validate chain evidence exported in three-plane/full-scan views | `report_three_plane_status.py`, `full_identity_protocol_scan.py` | P1 | SPEC_READY | Visibility semantics declared; implementation pending |
| ASB-RQ-018 | dynamic response stamp fields are runtime-resolved and non-hardcoded | `render_identity_response_stamp`, `validate_identity_response_stamp` | P0 | SPEC_READY | Spec defined in 5.2/5.2A; implementation pending |
| ASB-RQ-019 | stamp mismatch must fail-closed with `blocker_receipt` contract | `validate_identity_response_stamp_blocker_receipt` (new), release/e2e gate behavior | P0 | SPEC_READY | Spec defined in 5.2A; implementation pending |
| ASB-RQ-020 | external stamp output is redacted by default; absolute paths reserved for internal evidence view | `render_identity_response_stamp`, `validate_identity_response_stamp` | P0 | SPEC_READY | Display boundary hardened in 5.2/5.2A |
| ASB-RQ-021 | stamp render/validate must be CWD-invariant and deterministic across project/global pointer arbitration | stamp renderer + stamp validator + readiness/e2e/full-scan/three-plane/CI surfaces | P0 | SPEC_READY | Portability guard defined in 5.2A; implementation pending |
| ASB-RQ-022 | response stamp presentation is configurable (message/email style) under governance-safe invariants | renderer + runtime contract + stamp validator | P1 | SPEC_READY | Spec defined in 5.2B; style configurable, safety invariants non-configurable |
| ASB-RQ-023 | disclosure-level + user-named explicit trigger support with auditable scope and non-bypass guarantees | runtime stamp config + trigger parser + stamp validator | P1 | SPEC_READY | Spec defined in 5.2C; explicit trigger allowed, governance invariants unchanged |
| ASB-RQ-024 | natural-language explicit trigger normalization and confidence-gated execution | trigger parser + stamp config applier + audit log + stamp validator | P1 | SPEC_READY | Spec defined in 5.2C; NL trigger allowed with non-ambiguous normalization |
| ASB-RQ-025 | anytime refresh command exports actor session status and risk hints | `refresh_identity_session_status` (new), `validate_identity_session_refresh_status` (new) | P1 | SPEC_READY | Spec defined in 5.3C; implementation pending |
| ASB-RQ-026 | refresh output includes protocol baseline version visibility fields | refresh command + baseline payload contract | P1 | SPEC_READY | Spec defined in 5.3C; implementation pending |
| ASB-RQ-027 | three-plane/full-scan include refresh-consistent actor and baseline visibility for same identity context | `report_three_plane_status.py`, `full_identity_protocol_scan.py` + refresh validator wiring | P1 | SPEC_READY | Spec defined in 5.3C; visibility/wiring pending |
| ASB-RQ-028 | runtime catalog `pack_path` canonicalization is strict and machine-validated | `validate_identity_pack_path_canonical` (new), resolver/catalog write paths | P0 | SPEC_READY | Spec defined in 5.6; implementation pending |
| ASB-RQ-029 | report `resolved_pack_path` is canonical absolute and non-relative | `validate_identity_execution_report_path_contract` (new), `execute_identity_upgrade.py` | P0 | SPEC_READY | Spec defined in 5.6; implementation pending |
| ASB-RQ-030 | `identity_home == dirname(identity_catalog)` alignment is fail-closed for runtime mutation | `validate_identity_home_catalog_alignment` (new), runtime mode guard surfaces | P0 | SPEC_READY | Spec defined in 5.6; implementation pending |
| ASB-RQ-031 | fixture/runtime boundary is validator-enforced for activate/update/readiness paths | `validate_fixture_runtime_boundary` (new), creator/update/readiness/scan surfaces | P0 | SPEC_READY | Spec defined in 5.6; implementation pending |
| ASB-RQ-032 | writeback continuity contract enforces strict/degraded writeback semantics with mandatory risk fields | `validate_writeback_continuity` (new), `execute_identity_upgrade.py`, readiness/e2e/scan surfaces | P0 | SPEC_READY | Spec defined in 5.7.1; implementation pending |
| ASB-RQ-033 | post-execution mandatory validator blocks closure when runtime state machine is not advanced | `validate_post_execution_mandatory` (new), upgrade execution closure surfaces | P0 | SPEC_READY | Spec defined in 5.7.1; implementation pending |
| ASB-RQ-034 | semantic routing guard contract enforces intent-domain pre-classification before retrieval | `validate_semantic_routing_guard` (new), protocol-feedback router surfaces | P0 | SPEC_READY | Spec defined in 5.7.2; implementation pending |
| ASB-RQ-035 | protocol-vendor and business-partner namespace separation is validator-enforced | `validate_vendor_namespace_separation` (new), feedback artifact writers/readers | P0 | SPEC_READY | Spec defined in 5.7.2; implementation pending |
| ASB-RQ-036 | protocol-feedback sidecar escalation remains auditable and non-blocking-by-default | `validate_protocol_feedback_sidecar_contract` (new), required-gates escalation logic | P0 | SPEC_READY | Spec defined in 5.7.3; implementation pending |
| ASB-RQ-037 | instance-to-base-repo mutation boundary is codified as docs-allow/protocol-code-deny and fail-closed | `validate_instance_base_repo_write_boundary` (new), readiness/e2e/CI change-range surfaces | P0 | VERIFIED | replayed and audit-confirmed in HOTFIX-P0-005 lane |
| ASB-RQ-038 | protocol-feedback outputs must be SSOT-archived before mirror publication | `validate_protocol_feedback_ssot_archival` (new), outbox/evidence-index writer surfaces | P0 | VERIFIED | replayed and audit-confirmed in HOTFIX-P0-006 lane |
| ASB-RQ-039 | readiness dual-catalog arbitration must be explicit via `--scope` and deterministic fail-closed on ambiguity | `release_readiness_check.py` + runtime mode/scope validators (`validate_identity_runtime_mode_guard`) | P0 | VERIFIED | no-scope fail-closed + scoped passthrough replayed and confirmed in HOTFIX-P0-007 lane |
| ASB-RQ-040 | user-facing reply stamp presence must be machine-counted in replay outputs (`reply_stamp_missing_count`) | `validate_identity_response_stamp` (coverage mode), three-plane/full-scan replay surfaces | P0 | GATE_READY | user-visible zero-miss closure is audit-passed (`HOTFIX-P0-004`) |
| ASB-RQ-041 | readiness explicit scope must propagate into health branch validators (`collect_identity_health_report` path) | `release_readiness_check.py`, `collect_identity_health_report.py` | P0 | GATE_READY | implemented and audit-passed (`FIX-017`) |
| ASB-RQ-042 | baseline policy must be stratified (`strict` for release/mutation, `warn` for observability-only paths) | readiness/e2e/creator/scan/three-plane baseline policy wiring | P0 | GATE_READY | implemented and audit-passed (`FIX-018`) |
| ASB-RQ-043 | protocol version alignment must be validated as unified tuple across report/prompt/task/binding context | baseline/prompt/binding validators + closure surfaces | P0 | GATE_READY | unified validator implemented and audit-passed (`FIX-019`) |
| ASB-RQ-044 | protocol-vendor semantic isolation validator blocks cross-domain pollution in conclusion layer | `validate_protocol_vendor_semantic_isolation` (new), protocol-feedback conclusion writer surfaces | P0 | GATE_READY | implemented and audit-passed (`P0-D`) |
| ASB-RQ-045 | external source trust chain validator enforces trusted source tiers for conclusion-layer evidence | `validate_external_source_trust_chain` (new), external retrieval/evidence aggregation surfaces | P0 | GATE_READY | implemented and audit-passed (`P0-E`) |
| ASB-RQ-046 | protocol data sanitization boundary prevents tenant/business scenario leakage into protocol SSOT layer | `validate_protocol_data_sanitization_boundary` (new), governance/review document checks | P0 | GATE_READY | implemented and audit-passed (`P0-F`) |
| ASB-RQ-047 | platform optimization discovery trigger emits auditable deep-discovery tasks under repeated optimization signals | trigger/routing surfaces + protocol-feedback outbox receipts | P1 | IMPL_READY (NON_BLOCKING) | surface implemented and replay-visible (`P1-D`) |
| ASB-RQ-048 | vibe-coding feeding pack contract produces deterministic single-directory upload bundle | pack builder surface + evidence-index linkage | P1 | IMPL_READY (NON_BLOCKING) | surface implemented and replay-visible (`P1-E`) |
| ASB-RQ-049 | capability optimization cycle is inventory-first and machine-checkable | capability inventory snapshot + fit-matrix surfaces | P1 | IMPL_READY (NON_BLOCKING) | validator chain implemented and replay-visible (`P1-F`) |
| ASB-RQ-050 | compose-before-discover is enforced before external candidate selection | capability orchestration + composition decision gate surfaces | P1 | IMPL_READY (NON_BLOCKING) | validator chain implemented and replay-visible (`P1-F`) |
| ASB-RQ-051 | capability fit matrix requires single selected plan with fallback/rollback refs | fit-matrix builder + optimization validators | P1 | IMPL_READY (NON_BLOCKING) | builder/validator surfaces implemented and replay-visible (`P1-F/H`) |
| ASB-RQ-052 | optimization review freshness is machine-visible and stale state is non-closed | health/readiness/full-scan/three-plane status surfaces | P1 | IMPL_READY (NON_BLOCKING) | freshness validator implemented and replay-visible (`P1-F`) |
| ASB-RQ-053 | optimization decisions affecting routing/discovery/architecture require roundtable fact/inference mapping | roundtable evidence writer + optimization validators | P1 | IMPL_READY (NON_BLOCKING) | roundtable validator implemented and replay-visible (`P1-G`) |
| ASB-RQ-054 | user-visible identity stamp hard gate must fail-closed when actor/session lock is not `LOCK_MATCH` in strict operations (prevent perceived hard-switch under dual-catalog drift) | `validate_identity_response_stamp.py`, `validate_reply_identity_context_first_line.py`, creator/readiness/e2e wiring | P0 | VERIFIED | implementation + strict/inspection replay audit-passed (`HOTFIX-P0-008` / `FIX-020`) |
| ASB-RQ-055 | per-round instance/protocol split receipt is mandatory and machine-readable (`split_notice`, `instance_actions`, `protocol_actions`, `feedback_triggered`, `evidence_index`) | runtime reply receipt schema + replay parsers + three-plane/full-scan visibility | P0 | GATE_READY | implemented via `validate_instance_protocol_split_receipt.py` + replay payload mapping (`8778bdf`) |
| ASB-RQ-056 | required gate `validate_instance_protocol_split_receipt.py` enforces split fields + trigger semantics + SSOT path linkage | creator/readiness/e2e/full-scan/three-plane/CI wiring | P0 | GATE_READY | six-surface wiring landed (`8778bdf`) |
| ASB-RQ-057 | protocol-feedback trigger must follow hard conditions (recurrence, false-green/red, evidence missing, lane contamination) | trigger classifier + receipt validator + protocol-feedback archival bridge | P0 | GATE_READY | hard-condition classifier + IP-SPLIT failure paths landed (`8778bdf`) |
| ASB-RQ-058 | dual-track section isolation (`instance` vs `protocol`) must be enforced and protocol lane must remain business-data sanitized | receipt parser + `validate_protocol_data_sanitization_boundary.py` extension | P0 | GATE_READY | anti-mixed-lane + sanitization checks landed in split-receipt validator (`8778bdf`) |
| ASB-RQ-059 | trigger-regression sample report path patterns must resolve against identity pack root, never process CWD | `validate_identity_trigger_regression.py` path resolver + replay fixtures | P0 | GATE_READY | CWD-invariant resolution landed and replayed from `/tmp` (`8778bdf`) |
| ASB-RQ-060 | handoff self-test sample roots must be pack-root anchored for positive/negative fixture discovery | `validate_agent_handoff_contract.py` self-test sample root resolver | P0 | GATE_READY | pack/protocol-root deterministic fallback landed (`8778bdf`) |
| ASB-RQ-061 | orchestration subprocess and repo-catalog resolution must be protocol-root deterministic across invocation directories | `report_three_plane_status.py` subprocess launcher + repo-catalog resolver (`--protocol-root` aware) | P0 | GATE_READY | protocol-root deterministic launch + IP-CWD-004 error semantics landed (`8778bdf`) |
| ASB-RQ-062 | discovery requiredization trigger classifier must deterministically promote discovery contracts from optional to required when risk conditions are met | requiredization state evaluator + CURRENT_TASK contract writeback surfaces | P0 | GATE_READY | `validate_discovery_requiredization.py` + update preflight apply path landed (`295daf7`,`3baa355`) |
| ASB-RQ-063 | `validate_discovery_requiredization.py` must fail-closed when trigger met but requiredization/writeback/SSOT linkage is missing | validator + creator/readiness/e2e/full-scan/three-plane/CI wiring | P0 | GATE_READY | IP-DREQ-001..004 fail-closed + six-surface wiring landed (`295daf7`,`3baa355`) |
| ASB-RQ-064 | CI required validator set must auto-include discovery trio when requiredization is active | `ci_enforcement_contract.required_validators` synchronizer + CI required-gates adapter | P0 | GATE_READY | apply-requiredization path auto-syncs CI required validators (`3baa355`) |
| ASB-RQ-065 | non-blocking discovery warnings must auto-escalate to fail-closed after configured expiry window | trigger/builder/fit status lifecycle + expiry evaluator surfaces | P1 | GATE_READY (NON_BLOCKING) | expiry evaluator + `IP-DREQ-005` auto escalation landed (`3baa355`) |
| ASB-RQ-066 | required-contract coverage must expose discovery-subset hard threshold for requiredized contracts | `validate_required_contract_coverage.py` discovery subset counters + `min_discovery_required_coverage` gate | P0 | GATE_READY | discovery subset counters + threshold gate landed (`295daf7`) |
| ASB-RQ-067 | strict operations must enforce execution-to-reply identity tuple coherence under dual-catalog lanes | `execution_reply_identity_coherence_contract_v1` + coherence validator/wiring across creator/readiness/e2e/full-scan/three-plane/CI | P0 | GATE_READY | implementation landed via `validate_execution_reply_identity_coherence.py` + six-surface wiring (`FIX-021`), audit replay pending |
| ASB-RQ-068 | send-time unified reply outlet gate must enforce first-line Identity-Context fail-closed semantics and emit machine-readable telemetry in three-plane/full-scan | `validate_send_time_reply_gate.py` + creator/readiness/e2e/full-scan/three-plane/CI wiring | P0 | GATE_READY | send-time validator + six-surface wiring landed (`FIX-024`), audit replay pending |
| ASB-RQ-069 | layer intent resolution must auto-resolve `work_layer/source_layer` with confidence + fallback telemetry and keep strict tuple fail-closed semantics | `resolve_layer_intent` + `validate_layer_intent_resolution.py` + render/readiness/e2e/full-scan/three-plane/CI wiring | P1 | IMPL_READY (NON_BLOCKING) | implementation landed (`FIX-025`), pass-through closure landed (`FIX-026`), independent audit replay pending |
| ASB-RQ-070 | default work layer must be `instance`, and protocol escalation must be trigger-auditable with deterministic sample regression gate | `default_work_layer_contract_v1` + `protocol_trigger_contract_v1` + `layer_consistency_gate` in resolver/validators (render + first-line + coherence + send-time + layer-intent regression samples) | P0 | GATE_READY | implementation landed (`FIX-027`), independent audit replay pending |
| ASB-RQ-071 | canonical actor binding payload must be multi-entry and key-safe for same-actor concurrent sessions (`actor_id + session_id`), forbidding single-record overwrite semantics in strict lanes | actor binding serializer/reader + migration shims (`session/actors/<actor>.json`) | P0 | GATE_READY | implementation landed in `FIX-028` (multibinding schema + legacy read shim, strict write emits multi-entry only); replay audit pending |
| ASB-RQ-072 | actor binding mutation must enforce CAS-style precondition and fail-closed on stale compare token | activation binding writer + validator | P0 | GATE_READY | implementation landed in `FIX-028` (`compare_token` CAS on writer + `IP-ASB-MB-002/003` validator checks); replay audit pending |
| ASB-RQ-073 | canonical actor binding mutation must be activation-only and append-only rebind receipt must be mandatory | creator/readiness/scan mutation boundary + receipt writer surfaces | P0 | GATE_READY | implementation landed in `FIX-028` (mutation-lane boundary + append-only rebind receipts + `IP-ASB-MB-004/005/006` checks); replay audit pending |
| ASB-RQ-074 | required gate `validate_actor_session_multibinding_concurrency.py` must be wired across creator/e2e/readiness/full-scan/three-plane/CI and expose machine-readable conflict telemetry | six-surface + CI required-gates wiring | P0 | GATE_READY | validator + six-surface/CI wiring landed in `FIX-028`; replay audit pending |
| ASB-RQ-075 | protocol-layer feedback must use canonical reply-channel root and whitelist subpaths; non-standard primary channel is forbidden in strict operations | protocol-feedback reply writer/reader + channel classifier surfaces | P0 | GATE_READY | implementation landed in `FIX-029` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-076 | required gate `validate_protocol_feedback_reply_channel.py` must enforce canonical primary channel + mirror-reference constraints across creator/e2e/readiness/full-scan/three-plane/CI | six-surface + CI required-gates wiring | P0 | GATE_READY | validator + six-surface/CI wiring landed in `FIX-029` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-077 | sidecar escalation blocking prefixes must include `IP-PFB-*` in strict operations so protocol-feedback channel violations become fail-closed | `validate_protocol_feedback_sidecar_contract.py` + readiness/CI sidecar adapter surfaces | P0 | GATE_READY | strict blocking-prefix extension landed in `FIX-029` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-078 | split-receipt requiredization bridge must auto-promote split contract to required when protocol-feedback activity exists; strict operations must not return `SKIPPED_NOT_REQUIRED` in this case | split-receipt validator + requiredization bridge + strict lane orchestration surfaces | P0 | GATE_READY | activity-aware requiredization bridge + `IP-PFB-CH-006` path landed in `FIX-029` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-079 | protocol-lane entry must be trigger-auditable and bootstrap-ready: when `work_layer=protocol` / `protocol_triggered=true`, canonical protocol-feedback roots must be ready before protocol conclusions are emitted | layer-intent/send-time/reply bridge + bootstrap readiness classifier surfaces | P0 | GATE_READY | bootstrap-readiness classifier/constructor landed in `FIX-030` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-080 | required gate `validate_protocol_feedback_bootstrap_ready.py` must enforce canonical root readiness (`outbox-to-protocol`, `evidence-index`, `upgrade-proposals`) and emit machine-readable bootstrap telemetry | creator/readiness/e2e/full-scan/three-plane/CI wiring | P0 | GATE_READY | required gate + telemetry + six-surface/CI wiring landed in `FIX-030` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-081 | strict operations must fail-closed (`IP-PFB-CH-004/005`) when protocol lane is selected but bootstrap readiness or SSOT linkage is missing | strict-lane adapters + blocker-receipt integration + scan/report telemetry surfaces | P0 | GATE_READY | strict fail-closed semantics landed in `FIX-030` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-082 | layer-intent resolver must expose `PROTOCOL_CANDIDATE` decision state so weak protocol concern can enter governed clarification flow instead of silent instance fallback | layer-intent classifier + reply/send-time bridge surfaces | P0 | GATE_READY | candidate decision-state bridge landed in `FIX-031` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-083 | required gate `validate_protocol_entry_candidate_bridge.py` must enforce candidate clarification receipt completeness and deterministic question set (`which_gate_or_stage_failed`, `latest_replay_or_evidence_path`, `expected_protocol_optimization_target`) | creator/readiness/e2e/full-scan/three-plane/CI wiring | P0 | GATE_READY | required gate + deterministic question-set enforcement landed in `FIX-031` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-084 | candidate protocol-entry flow must seed canonical protocol-feedback outbox/index before final protocol conclusion; missing seed/index linkage is strict fail-closed (`IP-LAYER-CAND-003/004`) | candidate seed writer + SSOT archival bridge + strict-lane adapters | P0 | GATE_READY | canonical seed/index linkage enforcement landed in `FIX-031` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-085 | strict operations must fail-closed on silent candidate downgrade without clarification evidence (`IP-LAYER-CAND-001`) and expose candidate promotion telemetry in three-plane/full-scan | strict-lane adapters + scan/report telemetry surfaces | P0 | GATE_READY | anti-silent-downgrade semantics + telemetry landed in `FIX-031` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-086 | weak protocol concerns must enter deterministic inquiry follow-up states (`QUESTION_REQUIRED -> EVIDENCE_PENDING -> READY_FOR_PROTOCOL_FEEDBACK`) instead of silent downgrade/drop | layer-intent classifier + candidate/inquiry adapters + inquiry receipt writer surfaces | P0 | GATE_READY | inquiry state machine landed in `FIX-032` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-087 | inquiry receipts must classify `signal_origin` and require sanitized paraphrase before promoting business-origin statements into protocol conclusions | inquiry classifier + sanitization receipt writer + protocol conclusion adapters | P0 | GATE_READY | signal-origin classification + sanitization receipt enforcement landed in `FIX-032` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-088 | `source` (identity provenance) and `source_layer` (layer-intent provenance) must remain machine-distinct and mapper-auditable; ambiguity must not silently alter `work_layer` | stamp parser/coherence validator + layer-intent resolver + telemetry surfaces | P0 | GATE_READY | semantic distinction is now carried through FIX-032 telemetry path (`a95f5a2`); independent replay audit pending |
| ASB-RQ-089 | required gate `validate_protocol_inquiry_followup_chain.py` must fail-closed on missing follow-up receipts, missing protocol-feedback linkage, unsanitized promotion, and stale/expired inquiry chains (`IP-LAYER-INQ-001..004`) across creator/readiness/e2e/full-scan/three-plane/CI | six-surface + required-gates workflow wiring + requiredization trigger bridge | P0 | GATE_READY | required gate + six-surface/CI wiring + requiredization trigger bridge landed in `FIX-032` (`a95f5a2`); independent replay audit pending |
| ASB-RQ-090 | work-layer must deterministically route to lane-specific required gate set (`instance_required_checks` vs `protocol_required_checks`) with strict mismatch fail-closed semantics | readiness/e2e/creator/full-scan/three-plane gate orchestration routers + lane tuple receipts | P0 | GATE_READY | `FIX-033` implementation landed (`0d7ebc7`) + lane applied-gate-set propagation patch (`913973a`); independent replay closed in review (`16.8.27`) |
| ASB-RQ-091 | `work_layer=instance` self-drive upgrades must not be hard-blocked by protocol publish gates (e.g., changelog/release metadata); protocol diffs emit side-channel protocol-feedback receipt instead of blocking | readiness/e2e/creator lane filter + protocol-feedback pending receipt writer | P0 | GATE_READY | `FIX-033` implementation landed (`0d7ebc7`) + re-audit docs closure (`9d830d8`); independent replay closed in review (`16.8.27`) |
| ASB-RQ-092 | `work_layer=protocol` must enforce protocol publish governance gates and canonical protocol-feedback closure (`runtime/protocol-feedback/...`) as fail-closed boundaries | protocol lane required gate set + canonical outbox/index/upgrade proposal validators + strict blocker receipts | P0 | GATE_READY | `FIX-033` implementation landed (`0d7ebc7`) + lane applied-gate-set replay closure (`913973a`,`9d830d8`); independent replay closed in review (`16.8.27`) |
| ASB-RQ-093 | send-time/replay telemetry must expose lane execution proof (`work_layer`, `applied_gate_set`, `protocol_feedback_triggered`, `protocol_feedback_paths`, `lane_transition_reason`) for each governed round | response-stamp tail + first-line/send-time validators + full-scan/three-plane payload mapping | P0 | GATE_READY | telemetry closure verified by independent replay after patch (`913973a`,`9d830d8`), review record `16.8.27` |
| ASB-RQ-094 | protocol-topic sessions must not silently downgrade to `work_layer=instance` on empty intent fallback; strict operations require explicit protocol lane confirmation or session lane lock evidence | lane-intent resolver + readiness/e2e/creator strict gate routing + session-lane lock receipt surfaces | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-034` landed in `c310ab4` with protocol-context lane-lock telemetry + strict fallback fail-closed (`IP-LAYER-GATE-006/007`); independent replay closure pending in review `16.8.33` |
| ASB-RQ-095 | strict baseline freshness must evaluate against run-pinned protocol SHA to avoid in-run nondeterministic failures caused by moving HEAD | baseline/session-refresh validators + run context pin writer + readiness/e2e preflight adapters | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-035` landed in `c310ab4` with run-pinned anchor semantics (`protocol_head_sha_at_run_start`, `baseline_reference_mode`) + strict fail-closed (`IP-PBL-005/006`); independent replay closure pending in review `16.8.33` |
| ASB-RQ-096 | e2e runner must be hermetic and pass without external `PYTHONPATH` preparation | `e2e_smoke_test.sh` import-path bootstrap + hermetic preflight validator + CI replay adapter | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-036` landed in `c310ab4` with hermetic preflight validator + e2e/bootstrap/readiness/full-scan/three-plane/CI wiring; independent replay closure pending in review `16.8.33` |
| ASB-RQ-097 | required skill contracts must remain executable-as-documented; missing command targets must be machine-detectable | skill contract integrity validator + required-skill CI check + creator/readiness visibility surfaces | P1 | SPEC_READY | re-attributed to ecosystem lane (non protocol-core blocker) in review `16.8.31`; protocol SSOT keeps compatibility note only |
| ASB-RQ-098 | strict self-repair must support two-phase stale-baseline refresh (refresh + strict revalidate) to avoid self-lock in stale-only cases | identity_creator update flow + baseline preflight adapter + machine-readable phase trace receipts | P1 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-038` landed in `c310ab4` with phase-A refresh + phase-B strict revalidate trace fields and stale-only blocker code path (`IP-UPG-BASE-001`); independent replay closure pending in review `16.8.33` |
| ASB-RQ-099 | protocol governance requiredization must be lane-scoped to current-round protocol linkage and must not harden instance lane by historical artifact presence alone | semantic/split/vendor/sidecar validators + required coverage adapter + lane correlation evaluator | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | implementation landed in `FIX-039` (`83e5a03`) with lane-scope decision telemetry + current-round linkage gates; replay closure pending in review `16.8.32` |
| ASB-RQ-100 | split-receipt activity detection must enforce current-round correlation before strict `IP-PFB-CH-006` fail-closed path | split receipt validator activity detector + correlation receipt linkage + windowed stale filter | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | implementation landed in `FIX-040` (`83e5a03`) with correlation window + `IP-PFB-CH-007` uncorrelated path; replay closure pending in review `16.8.32` |
| ASB-RQ-101 | invalid `expected-source-layer` input must not be silently downgraded in strict operations; caller intent must remain auditable | stamp/common resolver + first-line/send-time validators source-layer input validator | P1 | IMPL_READY (BLOCKED_BY_AUDIT) | implementation landed in `FIX-041` (`83e5a03`) with strict invalid-input fail-closed (`IP-SOURCE-LAYER-001`) + downgrade telemetry; replay closure pending in review `16.8.32` |
| ASB-RQ-102 | required-contract coverage aggregator must be lane-aware (`instance_targets/protocol_targets`) and avoid protocol-governance hard-fails in pure instance lane without current-round protocol linkage | `validate_required_contract_coverage.py` lane partition policy + orchestration mapping | P1 | IMPL_READY (BLOCKED_BY_AUDIT) | implementation landed in `FIX-042` (`83e5a03`) with lane target partition + protocol-target inclusion/blocking telemetry; replay closure pending in review `16.8.32` |
| ASB-RQ-103 | runtime lifecycle state must be externalized from `IDENTITY_PROMPT.md`; prompt policy text remains immutable across non-policy upgrade runs | `execute_identity_upgrade.py` prompt-state writer split + prompt lifecycle validator/state artifact binder + readiness/scan telemetry surfaces | P1 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-043` landed in `c310ab4` with runtime state artifact (`runtime/state/prompt_contract.json`) and lifecycle validator externalization binding checks; independent replay closure pending in review `16.8.33` |
| ASB-RQ-104 | protocol lane lock exit must have a unified writer entrypoint with canonical outbox + index linkage; strict lane exit without newer EXIT remains fail-closed | `write_session_lane_lock_exit.py` + `identity_creator.py update --release-session-lane-lock` + lane-routing exit telemetry surfaces | P0 | IMPL_READY (BLOCKED_BY_AUDIT) | `FIX-044` landed in `62bdc1c` with canonical EXIT writer (`IP-LAYER-GATE-008/009`) and creator automation switch; independent replay closure pending in review `16.8.34` |

### 6.4A Requirement status delta snapshot (2026-03-01)

The table in 6.4 is baseline-oriented and may lag active remediation windows.
This delta snapshot is the authoritative synchronization bridge until the next full ledger rewrite.

| Requirement ID | Status delta | Evidence pointer |
| --- | --- | --- |
| ASB-RQ-003 / ASB-RQ-004 / ASB-RQ-005 | `SPEC_READY -> GATE_READY` | validator scripts landed + creator/readiness/e2e/full-scan/three-plane/CI wiring replayed in review ledger (`FIX-008~FIX-010`, `HOTFIX-P0-002`) |
| ASB-RQ-001 / ASB-RQ-002 / ASB-RQ-009 | `SPEC_READY -> GATE_READY` | actor-scoped canonical session source + mirror compatibility + six-surface wiring replayed in fix-chain evidence (`FIX-009/010/015`, `HOTFIX-P0-002`) |
| ASB-RQ-006 / ASB-RQ-007 / ASB-RQ-018 / ASB-RQ-019 / ASB-RQ-020 / ASB-RQ-021 | `SPEC_READY -> GATE_READY` | dynamic stamp render/validate + blocker receipt + replay counters (`FIX-004`, `HOTFIX-P0-001`, `HOTFIX-P0-003`) |
| ASB-RQ-025 / ASB-RQ-026 / ASB-RQ-027 | `SPEC_READY -> GATE_READY` | refresh command + refresh validator + three-plane/full-scan visibility (`HOTFIX-P0-007 prerequisite chain`) |
| ASB-RQ-028 / ASB-RQ-029 / ASB-RQ-030 / ASB-RQ-031 | `SPEC_READY -> GATE_READY` | path-governance fix chain (`FIX-002~FIX-007`) |
| ASB-RQ-032 / ASB-RQ-033 | `SPEC_READY -> GATE_READY` | Track-A writeback/post-execution gates (`FIX-011`) |
| ASB-RQ-034 / ASB-RQ-035 / ASB-RQ-036 | `SPEC_READY -> GATE_READY` | Track-B routing/namespace + sidecar escalation (`FIX-012`, `FIX-013`) |
| ASB-RQ-037 / ASB-RQ-038 / ASB-RQ-039 | `SPEC_READY -> VERIFIED` | governance-boundary hotfix lane replayed and audit-passed (`HOTFIX-P0-005/006/007`) |
| ASB-RQ-010 | `SPEC_READY -> VERIFIED` | actor-scoped multi-active runtime semantics audit-passed (`FIX-015`, review ledger `16.7.13` + `16.7.17`) |
| ASB-RQ-040 | `SPEC_READY -> GATE_READY` | reply first-line `Identity-Context` hard gate closure audit-passed (`HOTFIX-P0-004`, review ledger `16.6.8`) |
| ASB-RQ-041 / ASB-RQ-042 | `SPEC_READY -> GATE_READY` | readiness health-branch scope passthrough + baseline-policy stratification audit-passed (`FIX-017`, `FIX-018`, review ledger `16.7.5~16.7.7`) |
| ASB-RQ-043 | `SPEC_READY -> GATE_READY` | unified protocol version alignment contract validator + six-surface wiring audit-passed (`FIX-019`, review ledger `16.7.8`) |
| ASB-RQ-044 / ASB-RQ-045 / ASB-RQ-046 | `SPEC_READY -> GATE_READY` | protocol validators + six-surface wiring audit-passed (`P0-D/E/F`, review ledger `16.6.1~16.6.3`) |
| ASB-RQ-047 / ASB-RQ-048 | `SPEC_READY -> IMPL_READY (NON_BLOCKING)` | trigger/builder surfaces audit-passed under non-required contracts (`P1-D/E`, review ledger `16.7.1~16.7.2`) |
| ASB-RQ-049 / ASB-RQ-050 / ASB-RQ-051 / ASB-RQ-052 / ASB-RQ-053 | `SPEC_READY -> IMPL_READY (NON_BLOCKING)` | capability-fit validator/roundtable/trigger/matrix surfaces audit-passed under non-required contracts (`P1-F/G/H`, review ledger `16.7.3~16.7.4A`) |
| ASB-RQ-054 | `SPEC_READY -> VERIFIED` | lock-bound user-visible stamp guard strict/inspection replay audit-passed (`HOTFIX-P0-008` / `FIX-020`, review `16.7.17` + `16.7.18`) |
| ASB-RQ-055 / ASB-RQ-056 / ASB-RQ-057 / ASB-RQ-058 | `SPEC_READY -> GATE_READY (P0)` | split-receipt validator + fail-closed semantics + six-surface wiring landed (`8778bdf`) |
| ASB-RQ-059 / ASB-RQ-060 / ASB-RQ-061 | `SPEC_READY -> GATE_READY (P0)` | CWD-invariant validator/orchestrator path resolution landed and non-repo-CWD replayed (`8778bdf`) |
| ASB-RQ-062 / ASB-RQ-063 / ASB-RQ-064 / ASB-RQ-066 | `SPEC_READY -> GATE_READY (P0)` | discovery requiredization gate + writeback apply path + CI sync + discovery coverage subgate landed (`295daf7`,`3baa355`) |
| ASB-RQ-065 | `SPEC_READY -> GATE_READY (P1)` | non-blocking expiry evaluator and `IP-DREQ-005` auto escalation landed (`3baa355`) |
| ASB-RQ-067 | `SPEC_READY -> GATE_READY (P0)` | execution/reply coherence validator + strict fail-closed semantics + six-surface wiring landed (`FIX-021`); replay closure pending |
| ASB-RQ-068 | `SPEC_READY -> GATE_READY (P0)` | send-time unified reply outlet gate + real dialogue replay path + three-plane/full-scan visibility landed (`FIX-024`); replay closure pending |
| ASB-RQ-069 | `SPEC_READY -> IMPL_READY (P1)` | layer-intent resolver + validator landed (`FIX-025`) and pass-through closure landed (`FIX-026`); replay closure pending |
| ASB-RQ-070 | `SPEC_READY -> GATE_READY (P0)` | default fallback switched to `instance`; protocol escalation now requires trigger evidence; regression samples (`instance/protocol/ambiguous`) are machine-validated in layer-intent gate (`FIX-027`) |
| ASB-RQ-071 / ASB-RQ-072 / ASB-RQ-073 / ASB-RQ-074 | `SPEC_READY -> GATE_READY (P0)` | `FIX-028` landed: multibinding store/CAS/mutation-boundary/rebind-receipt contract + required validator wired into creator/readiness/e2e/full-scan/three-plane/CI; independent replay audit pending (`16.8.14`) |
| ASB-RQ-075 / ASB-RQ-076 / ASB-RQ-077 / ASB-RQ-078 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-029` landed (`a95f5a2`) and P0 remediation rework landed (`560f710`), but independent replay verdict is still pending; historical reject snapshot is `review 16.8.21`, superseded for current-state replay by `16.8.28`/`16.8.31` |
| ASB-RQ-079 / ASB-RQ-080 / ASB-RQ-081 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-030` landed (`a95f5a2`) and readiness/layer passthrough rework landed (`560f710`), but independent replay verdict is still pending; historical reject snapshot is `review 16.8.21`, superseded for current-state replay by `16.8.28`/`16.8.31` |
| ASB-RQ-082 / ASB-RQ-083 / ASB-RQ-084 / ASB-RQ-085 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-031` landed (`a95f5a2`) and CWD-deterministic candidate-chain rework landed (`560f710`), but independent replay verdict is still pending; historical reject snapshot is `review 16.8.21`, superseded for current-state replay by `16.8.28`/`16.8.31` |
| ASB-RQ-086 / ASB-RQ-087 / ASB-RQ-088 / ASB-RQ-089 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-032` landed (`a95f5a2`) and inquiry emission-correlation rework landed (`560f710`), but independent replay verdict is still pending; historical reject snapshot is `review 16.8.21`, superseded for current-state replay by `16.8.28`/`16.8.31` |
| ASB-RQ-090 / ASB-RQ-091 / ASB-RQ-092 / ASB-RQ-093 | `SPEC_READY -> GATE_READY (P0)` | `FIX-033` implementation (`0d7ebc7`) + lane propagation patch (`913973a`) + replay/doc closure (`9d830d8`, review `16.8.27`) closed prior `IP-LAYER-GATE-001` mismatch path |
| ASB-RQ-094 / ASB-RQ-095 / ASB-RQ-096 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-034..036` landed in `c310ab4` with protocol-context lane-lock + run-pinned baseline semantics + hermetic e2e import preflight; independent replay closure pending in review `16.8.33` |
| ASB-RQ-097 | `NEW -> SPEC_READY (P1, ecosystem-lane note)` | office-ops replay reported skill command drift, later re-attributed as ecosystem/non protocol-core in review `16.8.31`; protocol SSOT keeps compatibility note |
| ASB-RQ-098 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P1)` | `FIX-038` landed in `c310ab4` with two-phase stale-baseline refresh trace (`phase_a_refresh_applied`, `phase_b_strict_revalidate_status`, `phase_transition_*`); independent replay closure pending in review `16.8.33` |
| ASB-RQ-099 / ASB-RQ-100 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-039..040` implementation landed (`83e5a03`) with lane-scope requiredization + correlation-aware split activity gating; independent replay closure pending in review `16.8.32` |
| ASB-RQ-101 / ASB-RQ-102 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P1)` | `FIX-041..042` implementation landed (`83e5a03`) with strict invalid source-layer validation + lane-aware coverage partition; independent replay closure pending in review `16.8.32` |
| ASB-RQ-103 | `SPEC_READY -> IMPL_READY (BLOCKED_BY_AUDIT, P1)` | `FIX-043` landed in `c310ab4` with runtime prompt-state externalization and lifecycle binding validator updates; independent replay closure pending in review `16.8.33` |
| ASB-RQ-104 | `NEW -> IMPL_READY (BLOCKED_BY_AUDIT, P0)` | `FIX-044` landed in `62bdc1c` with canonical lane-lock EXIT writer + index linkage and creator automation switch (`--release-session-lane-lock`); independent replay closure pending in review `16.8.34` |

### 6.5 v1.5 unlock formula (release-lock hard rule)

`v1.5` tag unlock condition:

1. `unlock_allowed = true` iff all `P0` rows in section 6.4 are `DONE` and D1~D5 in section 0.3 are `PASS`.
2. `P1` rows remain mandatory backlog visibility items and block unlock only when explicitly promoted to `P0`.

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

Path-governance gate codes (aligned with section 5.6):

1. `IP-PATH-001` non-canonical catalog `pack_path` (fail-closed).
2. `IP-PATH-002` report `resolved_pack_path` invalid/non-canonical (fail-closed).
3. `IP-PATH-003` `identity_home` / `identity_catalog` alignment mismatch in runtime mutation flow (fail-closed).
4. `IP-PATH-004` fixture/runtime boundary violation without explicit override + receipt (fail-closed).
5. `IP-PATH-005` path tuple mixed-source warning in non-mutation inspection flow (fail-operational warning, must be tracked).

Writeback-continuity codes (aligned with section 5.7.1):

1. `IP-WRB-001` missing mandatory writeback in closure path (fail-closed).
2. `IP-WRB-002` degraded writeback without mandatory risk fields (fail-closed).
3. `IP-WRB-003` post-execution mandatory state not advanced (fail-closed).
4. `IP-WRB-004` canonical report path mismatch between producer and gate consumers (fail-closed).

Semantic-routing codes (aligned with section 5.7.2):

1. `IP-SEM-001` missing intent classification (fail-operational warning by default; escalates when repeated).
2. `IP-SEM-002` mixed-domain output without split (fail-closed for protocol-feedback track).
3. `IP-SEM-003` namespace violation (fail-closed for protocol-feedback track).
4. `IP-SEM-004` domain whitelist violation (fail-closed).
5. `IP-SEM-005` protocol-vendor semantic isolation breach in conclusion layer (fail-closed).

External source trust-chain codes (aligned with section 5.9.2):

1. `IP-SRC-001` conclusion-layer evidence includes `unknown` source tier (fail-closed).
2. `IP-SRC-002` required official/primary trace for conclusion statement missing (fail-closed).
3. `IP-SRC-003` source tier metadata missing/incomplete on external evidence rows (fail-closed on closure paths).

Protocol-layer sanitization boundary codes (aligned with section 5.9.3):

1. `IP-DSN-001` tenant/business scenario data leaked into protocol-layer contract/governance text (fail-closed).
2. `IP-DSN-002` protocol-layer examples include unredacted business identifiers or sensitive constants (fail-closed).

Governance-boundary hotfix lane codes (aligned with section 5.8):

1. `IP-GOV-BASE-001` base-repo mutation boundary violation (`docs allow`/`protocol-code deny` contract breach, fail-closed).
2. `IP-GOV-FEEDBACK-001` required protocol-feedback SSOT outbox artifact missing (fail-closed).
3. `IP-GOV-FEEDBACK-002` evidence-index linkage missing/incomplete for required feedback batch (fail-closed).
4. `IP-GOV-FEEDBACK-003` mirror-only feedback report without SSOT archival evidence (fail-closed).

Environment arbitration code (cross-linked to section 5.8.3):

1. `IP-ENV-002` dual-catalog ambiguity without explicit scope arbitration (`--scope` required, fail-closed).

Hard rule:

1. Recoverable actor-binding failures must not be silently promoted to hard-fail unless they cross hard-boundary conditions.

## 9) Acceptance Command Set (Cross-Validation)

Command interpretation note (to avoid execution ambiguity):

1. This section contains both current-runnable checks and target-state checks.
2. For commands whose owning ledger rows remain `SPEC_READY`, runtime failure is expected and must be reported as implementation gap evidence (not treated as protocol contradiction).
3. Release-lock closure requires converting target-state commands into runnable passes via status transitions (`SPEC_READY -> ... -> DONE`).

```bash
# SSOT / coupling
python3 scripts/validate_protocol_ssot_source.py
python3 scripts/validate_protocol_handoff_coupling.py --base <base_sha> --head <head_sha>

# Health -> heal -> validate loop
HEALTH_REPORT=$(python3 scripts/collect_identity_health_report.py --identity-id <id> --catalog <catalog> --out-dir /tmp/identity-health-reports | awk -F= '/^report=/{print $2}')
python3 scripts/validate_identity_health_contract.py --identity-id <id> --report "${HEALTH_REPORT}"
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog>
python3 scripts/identity_creator.py heal --identity-id <id> --catalog <catalog> --apply
python3 scripts/identity_creator.py validate --identity-id <id> --catalog <catalog>
python3 scripts/resolve_identity_context.py resolve --identity-id <id> --local-catalog <catalog>

# Dynamic response stamp closure (must be fail-closed on mismatch)
python3 scripts/render_identity_response_stamp --identity-id <id> --catalog <catalog> --view external
python3 scripts/validate_identity_response_stamp --identity-id <id> --catalog <catalog> --require-dynamic --require-redacted-external --require-lock-match
python3 scripts/validate_identity_response_stamp_blocker_receipt --identity-id <id> --catalog <catalog>

# Anytime self-check + refresh (including protocol baseline visibility)
python3 scripts/refresh_identity_session_status --identity-id <id> --catalog <catalog> --json-only
python3 scripts/validate_identity_session_refresh_status --identity-id <id> --catalog <catalog>

# Path-governance closure (canonical + alignment + boundary)
python3 scripts/validate_identity_pack_path_canonical --identity-id <id> --catalog <catalog>
python3 scripts/validate_identity_execution_report_path_contract --identity-id <id> --catalog <catalog> --report <report_path>
python3 scripts/validate_identity_home_catalog_alignment --identity-id <id> --catalog <catalog>
python3 scripts/validate_fixture_runtime_boundary --identity-id <id> --catalog <catalog>
rg -n "\"resolved_pack_path\"\\s*:\\s*\"\\.\"" <runtime_reports_root>

# Track-A writeback continuity closure
python3 scripts/validate_writeback_continuity --identity-id <id> --catalog <catalog> --report <report_path>
python3 scripts/validate_post_execution_mandatory --identity-id <id> --catalog <catalog> --report <report_path>

# Track-B semantic routing closure
python3 scripts/validate_semantic_routing_guard --identity-id <id> --catalog <catalog> --feedback-batch <batch_path>
python3 scripts/validate_vendor_namespace_separation --identity-id <id> --catalog <catalog> --feedback-root <runtime_protocol_feedback_dir>
python3 scripts/validate_protocol_feedback_sidecar_contract --identity-id <id> --catalog <catalog> --feedback-root <runtime_protocol_feedback_dir>

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

Governance-boundary hotfix lane command note:

1. `ASB-RQ-037/038/039/040` are target-state required commands and become runnable command rows when corresponding scripts/flags land.
2. Until then, closure is tracked by requirement rows + replay evidence in review ledger; no implicit PASS is allowed.

### 9.1 P0 deep-remediation closure checklist (no-ambiguity lock)

This checklist is the protocol-level closure contract for "deep remediation + cross-validation" and must be read together with section 6.3A (C1~C8) and section 6.4 (`ASB-RQ-*`).

| Closure item | Mandatory statement | Evidence requirement | Tracker linkage |
| --- | --- | --- | --- |
| DRC-1 | Session model is upgraded from `single-active` to `actor-scoped binding` (multi-agent, multi-identity capable). | activation/update/state/session paths no longer treat catalog single-active as authoritative decision primitive. | `C1`, `ASB-RQ-010`, `ASB-RC-001~005` |
| DRC-2 | Contract `actor_session_binding_contract_v1` is implemented and versioned. | contract schema + validator behavior are machine-checkable and replayable in CI. | `C2`, `ASB-RQ-001` |
| DRC-3 | Canonical session source is `<catalog_dir>/session/actors/<actor_id>.json`. | resolver/validators use actor pointer as first source; report includes canonical actor pointer evidence. | `C3`, `ASB-RQ-001`, `ASB-RC-004/006` |
| DRC-4 | `active_identity.json` remains compatibility mirror only and cannot be authoritative. | mirror drift is reported as compatibility warning path; canonical actor pointer remains the binding source. | `C4`, `ASB-RQ-002`, `ASB-RC-006` |
| DRC-5 | Three validators are mandatory: `validate_actor_session_binding`, `validate_no_implicit_switch`, `validate_cross_actor_isolation`. | each validator has command contract, machine-readable output, and gate visibility in readiness/scan/three-plane/CI. | `C5`, `ASB-RQ-003/004/005` |
| DRC-6 | Gate wiring covers: `identity_creator`, `e2e_smoke_test.sh`, `release_readiness_check.py`, `full_identity_protocol_scan.py`, `report_three_plane_status.py`, CI required-gates. | same target identity shows consistent semantics across all listed surfaces; no silent pass when required wiring is missing. | `C6`, `ASB-RQ-009`, `ASB-RC-012` |
| DRC-7 | Health/heal closure is actor-risk complete and replay-deterministic. | health report shows actor-risk coverage fields; heal apply output binds to health report ref and post-validate ref; closure checks use explicit `--report` binding. | `ASB-RQ-014/015/016` |
| DRC-8 | Response stamp closure is dynamic, non-hardcoded, redacted-by-default, and mismatch fail-closed. | stamp is present on every user-facing reply; validator confirms live-binding fields; mismatch produces blocker receipt before business output; CWD-invariant behavior verified. | `ASB-RQ-018/019/020/021` |
| DRC-9 | Anytime self-check/refresh closure is available and protocol baseline visibility is included. | refresh command callable anytime; output contains actor/session status + baseline lag fields; three-plane/full-scan remain consistent with refresh semantics. | `ASB-RQ-025/026/027` |
| DRC-10 | Path-governance closure is canonical, aligned, and boundary-safe across catalog/runtime/report surfaces. | path gates pass; report path contract rejects relative path values; home/catalog alignment enforced; fixture/runtime boundary is auditable and enforced. | `ASB-RQ-028/029/030/031` |
| DRC-11 | Track-A writeback continuity closure prevents frozen runtime state. | `STRICT_WRITEBACK/DEGRADED_WRITEBACK` semantics are enforced; post-execution mandatory validation passes; no closure report with missing writeback. | `ASB-RQ-032/033` |
| DRC-12 | Track-B semantic routing closure prevents vendor/business domain retrigger drift. | pre-classification fields are present; namespace split is enforced; `IP-SEM-*` violations are deterministically caught by required-gates. | `ASB-RQ-034/035/036` |
| DRC-13 | Governance-boundary hotfix lane is codified and machine-enforced (base-repo write boundary + feedback SSOT archival + explicit scope arbitration + reply-stamp missing-turn counter). | docs-only change can pass while protocol/code mutation fails; mirror-only feedback fails; readiness ambiguity fails without `--scope`; replay window reports `reply_stamp_missing_count=0` for closure claim. | `ASB-RQ-037/038/039/040` |

Hard closure rule:

1. Any one of `DRC-1..DRC-10` not reaching `DONE` means runtime milestone is not closed.
2. `DRC-11` and `DRC-12` are P0 closures for protocol-feedback robustness and must be `DONE` before declaring v1.5 runtime closure.
3. `DRC-13` is release-blocking for multi-agent governance safety and must be `DONE` before declaring v1.5 runtime closure.
4. Narrative "cross-validated" claim without evidence on all mandatory surfaces and closure items is invalid.

Post-implementation command contract (must be enabled in same PR as script landing):

1. `validate_actor_session_binding` command + gate wiring.
2. `validate_no_implicit_switch` command + gate wiring.
3. `validate_cross_actor_isolation` command + gate wiring.
4. `render_identity_response_stamp` command + output contract.
5. `validate_identity_response_stamp` command + CI enforcement.
6. `refresh_identity_session_status` command + three-plane visibility.
7. `validate_identity_actor_health_profile` command + health coverage contract.
8. `validate_identity_heal_replay_closure` command + replay-bound closure contract.
9. `validate_identity_response_stamp_blocker_receipt` command + mismatch fail-closed contract.
10. `validate_identity_session_refresh_status` command + anytime self-check/refresh contract.
11. `validate_identity_pack_path_canonical` command + catalog/runtime canonical path contract.
12. `validate_identity_execution_report_path_contract` command + report path contract.
13. `validate_writeback_continuity` command + strict/degraded writeback closure contract.
14. `validate_post_execution_mandatory` command + post-execution state advancement contract.
15. `validate_semantic_routing_guard` command + intent-domain pre-classification contract.
16. `validate_vendor_namespace_separation` command + protocol-vendor/business-partner namespace contract.
17. `validate_protocol_feedback_sidecar_contract` command + sidecar escalation contract.
18. `validate_identity_home_catalog_alignment` command + home/catalog alignment contract.
19. `validate_fixture_runtime_boundary` command + fixture/runtime boundary contract.
20. `validate_instance_base_repo_write_boundary` command + docs-allow/protocol-code-deny boundary contract.
21. `validate_protocol_feedback_ssot_archival` command + outbox/evidence-index mandatory archival contract.
22. `release_readiness_check.py --scope` passthrough contract + dual-catalog fail-closed behavior.
23. `validate_identity_response_stamp` reply-channel counter contract (`reply_stamp_missing_count`).

## 10) Definition of Done (Split to Avoid False Closure)

### 10.1 Governance close (v1.5.0 document close)

All conditions must be true:

1. Canonical governance document exists and SSOT gates are green.
2. Layer boundary is explicit and non-ambiguous.
3. Vendor/API shot-mode + tier policy has compatibility mapping to current validators.
4. Non-hardcoded vendor/API rule is explicit and testable.
5. Required acceptance commands are runnable and documented.
6. Shot-mode and evidence-chain semantics are defined as protocol-kernel rules, not domain-only policy.
7. Governance-boundary hotfix lane contracts (`5.8`) are included in requirement/gate/acceptance sections.

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
11. Path governance chain is validator-enforced and replay-stable (`pack_path` + report `resolved_pack_path` + home/catalog alignment + fixture/runtime boundary).
12. Track-A writeback continuity is validator-enforced (`STRICT_WRITEBACK` / `DEGRADED_WRITEBACK` + `post_execution_mandatory`).
13. Track-B semantic routing boundary is validator-enforced (`intent_domain` pre-classification + namespace separation + deterministic `IP-SEM-*` gates).
14. Base-repo mutation boundary is validator-enforced (`docs/**` allowlist, protocol/code denylist, fail-closed).
15. Protocol-feedback SSOT archival is validator-enforced (outbox + evidence-index mandatory; mirror-only blocked).
16. Readiness dual-catalog ambiguity is scope-arbitrated (`--scope`) and fails closed when omitted.
17. Reply-channel stamp observability shows `reply_stamp_missing_count=0` in release replay window.

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
6. non-merge A/B closure status (`Track-A writeback` and `Track-B semantic routing` reported separately)
7. Track-A fields (must be independent):
   - `track_a_commit_sha_list`
   - `track_a_changed_files`
   - `track_a_acceptance_rc_tail`
   - `track_a_residual_risk`
8. Track-B fields (must be independent):
   - `track_b_commit_sha_list`
   - `track_b_changed_files`
   - `track_b_acceptance_rc_tail`
   - `track_b_residual_risk`

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
   - https://developers.openai.com/api/docs/guides/function-calling  
   - https://developers.openai.com/api/docs/guides/tools-connectors-mcp/
8. Anthropic tool use and MCP connector  
   - https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/implement-tool-use  
   - https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector
9. Gemini function calling  
   - https://ai.google.dev/gemini-api/docs/function-calling
10. MCP specification  
   - https://modelcontextprotocol.io/specification/2025-11-25
11. Internal skill-governance references  
   - `docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md`  
   - `docs/references/identity-skill-mcp-cross-vendor-governance-guide-v1.0.md`
12. Canonical path resolution references  
   - https://www.gnu.org/software/coreutils/manual/html_node/realpath-invocation.html  
   - https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve  
   - https://www.gnu.org/software/bash/manual/html_node/Bourne-Shell-Builtins.html

## 13) Roundtable Framing Note

This document is an engineering synthesis based on:

1. local protocol repository behavior,
2. official vendor/spec documentation,
3. Context7 indexed specification extracts (for cross-check, not as sole authority),
4. internal skill-governance references.

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
   - `path_canonicalization_gap`
   - `path_mixed_source_drift`
   - `runtime_fixture_boundary_gap`
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
10. `status` (`SPEC_READY|IMPL_READY|CODE_READY(alias)|GATE_READY|VERIFIED|DONE`)
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
| ASB-RC-013 | runtime catalogs (`*.local.yaml`) | `pack_path` is relative / non-canonical / missing | `path_canonicalization_gap` | runtime catalog may carry non-canonical pack path entries | catalog entries must be canonical absolute and mode-root compliant | REMOVE | P0 | protocol-architect | SPEC_READY | local runtime catalog evidence + path gate replay |
| ASB-RC-014 | execution reports (`identity-upgrade-exec-*.json`) | `resolved_pack_path` is relative token (`.`/`..`) or non-canonical | `path_canonicalization_gap` | report persists non-canonical pack path values | report writer must normalize/reject non-canonical path values before persistence | REMOVE | P0 | protocol-architect | SPEC_READY | report contract replay evidence |
| ASB-RC-015 | `scripts/execute_identity_upgrade.py` path tuple persistence | mixed source for `identity_home` vs runtime-resolved catalog/pack fields | `path_mixed_source_drift` | one report can contain path fields from different domains | all path fields derive from one canonical runtime resolution tuple | REMOVE | P0 | protocol-architect | SPEC_READY | code inspection + tuple consistency validator evidence |
| ASB-RC-016 | runtime entry/guard surfaces (`use_project_identity_runtime.sh`, `validate_identity_runtime_mode_guard.py`) | missing strict home/catalog alignment + fixture boundary enforcement | `runtime_fixture_boundary_gap` | runtime mutation can proceed with home/catalog drift or fixture leakage | enforce fail-closed alignment and boundary guard before mutation | REMOVE | P0 | protocol-architect | SPEC_READY | guard replay evidence |

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

### 14.6 Dual-catalog hard-switch perception guard (P0, actor/session lock-bound stamp policy)

Incident class:

1. Under dual-catalog execution lanes, actor binding can remain on identity `A` while a canonical mirror pointer is switched by another actor replay to identity `B`.
2. This is legal under actor-scoped multi-active semantics, but it can produce perceived “identity hard-switch” if user-visible reply channels do not fail-closed on lock mismatch.

Normative rule:

1. For strict operations (`activate`, `update`, `mutation`, `readiness`, `e2e`, `validate`), user-visible identity context gates MUST require `LOCK_MATCH`.
2. If resolved stamp context lock is not `LOCK_MATCH`, validators must fail-closed and emit blocker receipt.
3. Non-strict inspection operations (`scan`, `three-plane`, `inspection`, `ci`) remain visibility-first and must not force lock-bound closure.

Error-code contract:

1. `IP-ASB-STAMP-005`: response stamp lock-bound gate failed (`validate_identity_response_stamp.py`).
2. `IP-ASB-STAMP-SESSION-001`: first-line identity-context lock clause failed (`validate_reply_identity_context_first_line.py`).

Machine-readable requirements:

1. Validators must expose:
   - `operation`
   - `lock_boundary_enforced`
   - `expected_lock_state`
   - parsed lock state field (`parsed_lock_state` / `reply_first_line_lock_state`)
2. Fail path must emit blocker receipt with actionable next action:
   - `activate_identity_for_actor_then_retry` (or equivalent lock-recovery action).

Acceptance commands (minimal):

```bash
# mismatch lane (strict op) must fail-closed
python3 scripts/validate_identity_response_stamp.py \
  --identity-id <id> --catalog <project_or_conflict_catalog> --repo-catalog identity/catalog/identities.yaml \
  --stamp-json <stamp_json> --force-check --enforce-user-visible-gate --operation validate --json-only

python3 scripts/validate_reply_identity_context_first_line.py \
  --identity-id <id> --catalog <project_or_conflict_catalog> --repo-catalog identity/catalog/identities.yaml \
  --stamp-json <stamp_json> --force-check --enforce-first-line-gate --operation validate --json-only

# inspection op remains non-blocking visibility mode
python3 scripts/validate_identity_response_stamp.py \
  --identity-id <id> --catalog <project_or_conflict_catalog> --repo-catalog identity/catalog/identities.yaml \
  --stamp-json <stamp_json> --force-check --enforce-user-visible-gate --operation scan --json-only
```

### 14.7 Dual-domain execution/reply coherence guard (P0, command-target vs reply tuple)

Incident class:

1. Under long-running dual-catalog operations, command execution can target identity tuple `A` while user-visible reply stamp is generated from tuple `B`.
2. This produces operator-facing ambiguity ("command shows one identity, reply shows another") even when each lane is internally valid.
3. The ambiguity is protocol-layer critical because it weakens audit replay trust and can be perceived as hidden identity switching.

Normative rule:

1. Strict operations must compare command-target tuple with reply tuple before emitting business content.
2. Required tuple keys include:
   - `identity_id`
   - `catalog_ref` (or canonical catalog path hash reference)
   - `resolved_pack_path` (or pack reference hash)
   - `actor_id`
3. Any tuple mismatch in strict operations is fail-closed and must emit blocker receipt first.
4. Inspection operations remain non-blocking but must expose mismatch as machine-readable warning for audit visibility.

Error-code contract:

1. `IP-ASB-CTX-001`: command tuple and reply tuple mismatch.
2. `IP-ASB-CTX-002`: resolver evidence missing for reply tuple.
3. `IP-ASB-CTX-003`: strict operation executed under unresolved dual-catalog ambiguity.

Gate wiring requirement:

1. `identity_creator` (strict ops)
2. `release_readiness_check.py`
3. `e2e_smoke_test.sh`
4. `full_identity_protocol_scan.py`
5. `report_three_plane_status.py`
6. CI required-gates workflow

Status note:

1. This lane is tracked as `ASB-RQ-067` (`P0`, `GATE_READY`) until replay closure is audit-confirmed.
