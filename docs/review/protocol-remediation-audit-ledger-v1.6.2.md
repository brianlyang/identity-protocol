# Protocol Remediation Audit Ledger (v1.6.2 multimodal stream)

Status: Active  
Layer: protocol control-plane  
Scope: multimodal-plugin enforcement closure only  
Owner: identity protocol base-repo architect

## 1) Intake decision

1. Create dedicated v1.6.2 stream for multimodal-plugin enforcement.
2. Keep v1.6.0/v1.6.1 as historical baseline; do not continue scatter updates for this topic.
3. Keep protocol/instance boundary strict:
   - protocol: identify + validate + reject
   - instance: migrate + backfill + content debt cleanup

## 2) Architecture decision record (ADR-v1.6.2-PLUGIN-001)

### 2.1 Decision

1. Plugin system is maintained centrally in identity protocol base repo.
2. Identity instances do not copy plugin contracts or plugin adapters.
3. Instances only keep runtime receipts/projections/activation artifacts.

### 2.2 Alternatives evaluated

1. Alternative A (rejected): per-instance plugin code copy.
   - Rejected due to high drift, version fragmentation, and difficult audit replay.
2. Alternative B (accepted): centralized plugin SSOT with instance invocation.
   - Accepted due to single governance surface and deterministic fail-close enforcement.

### 2.3 Consequences

1. Protocol changes become auditable in one place (`identity/protocol/plugins/**`).
2. Instance migration debt becomes explicit and isolated from protocol control plane.
3. Non-canonical instance plugin copies become policy violations (`IP-MM-COPY-001`).

## 3) Canonical filesystem + naming freeze (audit baseline)

### 3.1 Canonical filesystem

1. Registry root:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`
2. Registry schema:
   - `identity/protocol/plugins/schemas/plugin-registry.schema.json`
3. Per-plugin required files:
   - `identity/protocol/plugins/<plugin_id>/plugin.contract.yaml`
   - `identity/protocol/plugins/<plugin_id>/plugin.input.schema.json`
   - `identity/protocol/plugins/<plugin_id>/plugin.output.schema.json`
   - `identity/protocol/plugins/<plugin_id>/plugin.error-codes.yaml`
   - `identity/protocol/plugins/<plugin_id>/README.md`
   - `identity/protocol/plugins/<plugin_id>/fixtures/*.json`

### 3.2 Naming contract

1. `plugin_id` regex:
   - `^[a-z][a-z0-9-]{2,63}$`
2. Validator naming:
   - `validate_plugin_<plugin_slug>.py` (under `scripts/`)
3. Error family:
   - naming: `IP-MM-NAME-*`
   - path: `IP-MM-PATH-*`
   - copy policy: `IP-MM-COPY-*`
   - provider config: `IP-MM-CONF-*`

### 3.4 Four-core contract binding confirmation

1. `IDENTITY_PROTOCOL.md` declares:
   - Accurate judgement requires multimodal evidence consistency.
2. v1.6.2 binds this declaration to executable protocol checks via:
   - `asb16-rq-034`
   - `rq_034_multimodal_plugin_enforcement_contract_v1`
   - `scripts/validate_multimodal_plugin_enforcement.py`
3. Done-transition semantics are locked:
   - inconsistent multimodal evidence => `block_done` (fail-close).
4. Non-goal clarified:
   - protocol layer does not host business-specific orchestration logic;
   - instance layer hosts business execution and migration debt cleanup.

### 3.3 Provider/API configuration governance baseline

1. Provider profiles are centrally governed in base repo:
   - `identity/protocol/plugins/PROVIDER_PROFILES.v1.6.2.yaml`
   - `identity/protocol/plugins/schemas/provider-profiles.schema.json`
2. Instance packs keep binding pointers only:
   - `<pack>/runtime/plugins/provider-bindings.local.yaml`
3. Secrets are externalized (env/vault references only), never persisted as plaintext in repo/runtime receipts.
4. GLM4.6V-like visual providers are onboarded by profile registration + capability gate, not by per-instance script forks.

## 4) Cross-verified findings (Roundtable/Vendor/Reference/Replay)

### T1 Governance (roundtable)

1. Multimodal requirement wiring is now landed in bundle/drift contracts.
2. Path/config framework and fail-close coverage are landed for strict surfaces.
3. Centralized plugin ownership remains lower-governance-entropy than per-instance copies.

Evidence anchors:

1. `scripts/required_gate_bundle_runner.py:23`
2. `scripts/required_gate_bundle_runner.py:32`
3. `scripts/validate_required_gate_surface_drift.py:44`
4. `scripts/validate_required_gate_surface_drift.py:53`
5. `scripts/configure_identity_runtime_paths.py:32`

### T2 Vendor

1. MCP lifecycle supports explicit capability negotiation; aligns with strict multimodal threshold/path gate.
2. Codex approvals/security supports centralized output control and deterministic block behavior.
3. Vendor pattern favors central registry + strict runtime admission checks.

Reference anchors:

1. `https://modelcontextprotocol.io/specification/latest`
2. `https://developers.openai.com/codex/agent-approvals-security/`

### T3 Reference

1. Structured outputs strict mode supports machine-checkable deterministic contracts.
2. Agent Skills metadata contract aligns with explicit naming/path/trigger governance.
3. Therefore naming and copy policy can be enforced by protocol-level schema/receipt checks.
4. Provider profile gating (capability + credential indirection) is consistent with strict structured contract style.

Reference anchors:

1. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
2. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
3. `https://agentskills.io/specification`

### T4 Replay

Current replay judgment:

1. Multimodal key requiredization is closed in bundle/drift.
2. Strict validator replay is positive and requiredized (`PASS_REQUIRED`).
3. Release-readiness projection parity is closed via governance-driven projection validator wiring.

Replay evidence:

1. Canonical index: `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Minimal anchors:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json`
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json`

Residual replay set for full closure:

1. Positive: canonical plugin topology + valid schemas + valid thresholds => `PASS_REQUIRED`.
2. Negative A: invalid naming => `FAIL_REQUIRED` + `IP-MM-NAME-*`.
3. Negative B: path escape => `FAIL_REQUIRED` + `IP-MM-PATH-*`.
4. Negative C: instance plugin code copy => `FAIL_REQUIRED` + `IP-MM-COPY-*`.
5. Negative D: provider profile missing => `FAIL_REQUIRED` + `IP-MM-CONF-001`.
6. Negative E: vision-required plugin bound to non-vision provider => `FAIL_REQUIRED` + `IP-MM-CONF-005`.

## 5) Protocol execution set (v1.6.2 state update)

Completed:

1. `asb16-rq-034` added to bundle + drift required key lists.
2. Mapping row `asb16-rq-034` added in `identity/protocol/mappings/contract-binding.v1.6.yaml`.
3. `scripts/validate_multimodal_plugin_enforcement.py` landed and replayed as single-source validator.
4. Projection parity landed in three-plane/full-scan (`provider_config_status`, `provider_profile_id`).
5. Provider config validator branch landed:
   - registry existence
   - capability compatibility
   - credential reference resolvability (without secret exposure)

Pending:

1. Negative replay archive completion for naming/path/copy/provider mismatch matrix.
2. CI literal-path lint for plugin topology whitelist.

## 6) Current posture

1. v1.6.2 stream has landed runtime closure for `asb16-rq-034` in strict bundle/drift/validator surfaces.
2. Current blocker is residual replay archive completion and baseline freshness debt.
3. Posture remains non-promotional:
   - `SPEC_READY / PENDING_INTAKE`
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`

## 7) Command contract note (prevent false negative replay)

1. `scripts/validate_multimodal_plugin_enforcement.py` does not accept `--repo-catalog`.
2. Canonical invocation template:
   - `python3 scripts/validate_multimodal_plugin_enforcement.py --catalog <catalog.local.yaml> --identity-id <identity_id> --operation validate --json-only`
3. Passing unsupported args must be treated as command-contract error, not protocol regression.

## 8) Additional input packet

1. `/Users/yangxi/claude/codex_project/ddm/identity_protocol_feedback/multimodal-plugin-enforcement-mechanism-deepdive-20260308.md`

## 9) Round-29.3 replay addendum (2026-03-09)

### 9.1 What was fixed this round (code-level)

1. Plugin literal-path lint now passes without opening non-canonical path bypass:
   - `scripts/validate_plugin_contract_literal_paths.py`
2. Bundle target-mode tuple projection loss is fixed:
   - `scripts/required_gate_bundle_runner.py`
   - target receipts now carry `actor_id/resolved_work_layer/resolved_source_layer/lock_state`
3. Provider binding requirement is explicit and fail-close:
   - `scripts/validate_multimodal_plugin_enforcement.py`
   - required plugin binding absence now yields `IP-MM-CONF-001`
4. Instance minimal binding template is added:
   - `identity/protocol/plugins/templates/provider-bindings.local.template.yaml`
5. v1.6.2 docs are part of mandatory docs command contract check:
   - `scripts/docs_command_contract_check.py`

### 9.2 Replay evidence (this round)

1. Canonical evidence index:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Minimal replay anchor set:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json`
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json`
   - `activity/evidence/rq034/2026-03-09/rq034_full_scan_target_regression_20260309_r5.result.json`
3. Ledger readability policy:
   - keep only index + anchor set in review doc;
   - keep exhaustive per-run evidence in manifest/mirror path.

### 9.3 Updated judgment

1. Multimodal protocol-control-plane strict wiring (bundle/drift/validator/full-scan) is closed for v1.6.2.
2. Release-readiness projection parity is closed in this round.
3. Remaining non-green signals are outside RQ-034 strict wiring itself (instance freshness churn / dirty baseline).
4. Posture remains non-promotional:
   - `SPEC_READY / PENDING_INTAKE`
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`

## 10) Round-29.4 addendum: plugin interface exposure normalization (2026-03-09)

### 10.1 Why this addendum was required

1. Prior rounds validated plugin wiring, but “which interfaces are protocol-owned vs instance-writable” was still implicit.
2. Without an explicit interface boundary contract, multi-agent/multi-identity operation risks:
   - local copy drift,
   - inconsistent extension patterns,
   - replay ambiguity on ownership.
3. This addendum freezes interface boundary semantics under v1.6.2 scope (plugin system only).

### 10.2 Cross-verification synthesis (four tracks)

#### T1 Governance roundtable

1. Decision confirmed: centralized plugin SSOT (`identity/protocol/plugins/**`) + instance pointer binding.
2. Rejected path: per-instance plugin contract/code replication.
3. Boundary rule retained:
   - protocol layer: define/validate/reject;
   - instance layer: bind pointers/emit evidence/migrate debt.

#### T2 Vendor track

1. MCP lifecycle contract favors explicit capability advertisement and deterministic interface boundaries.
2. Codex controlled execution/approval model favors centralized policy enforcement surfaces.
3. Hence, protocol-owned canonical plugin registry + instance pointer-based runtime binding remains vendor-aligned.

#### T3 Reference track

1. Structured output strictness aligns with schema-first interface contracts.
2. Skills metadata discipline aligns with explicit naming and stable contract paths.
3. Therefore plugin interface normalization is reference-consistent and auditable.

#### T4 Replay track

1. Canonical-path bypass class replay (all on `aa1ec44`):
   - prefix probe => `FAIL_REQUIRED`
   - traversal probe => `FAIL_REQUIRED`
   - canonical probe => `PASS_REQUIRED`
   - canonicalvar probe => `FAIL_REQUIRED`
   - repo probe => `PASS_REQUIRED`
2. Provider-binding negative replay:
   - no binding => `FAIL_REQUIRED` + `IP-MM-CONF-001`
   - missing required plugin entry => `FAIL_REQUIRED` + `IP-MM-CONF-001`
3. Governance gate replay:
   - docs command contract => `PASS`
   - protocol SSOT source => `OK`

### 10.3 Frozen interface contract (execution summary)

1. Protocol-owned immutable surfaces:
   - `identity/protocol/plugins/**`
   - plugin registry + provider profile registry + schemas + validator contracts
2. Instance-writable controlled surfaces:
   - `<pack>/runtime/plugins/provider-bindings.local.yaml` (pointer only)
   - `<pack>/runtime/state/active_execution_report.json` (runtime pointer)
3. Security/secret invariants:
   - no plaintext credentials in runtime/repo bindings,
   - only `credential_ref` pointer forms (`env:`/`vault:`),
   - copied plugin source in instance runtime remains fail-close.

### 10.4 Acceptance statement (this addendum scope)

1. v1.6.2 plugin interface exposure contract is now explicitly documented and replay-backed.
2. This addendum does not alter previously declared non-promotional posture.
3. Remaining blockers still outside this addendum scope:
   - instance-specific debt and baseline cleanliness.

## 11) Round-29.5 addendum: evidence persistence hard-gate execution (2026-03-09)

### 11.1 Enforcement summary

1. This review stream adopts persistent evidence mirrors as canonical replay references.
2. Current round keeps zero `/tmp` evidence references in-body; all paths point to `activity/evidence/...`.
3. Tuple metadata for every mirrored evidence file is centralized in:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`

### 11.2 Contract rules implemented

1. Governance docs fail-close when `/tmp` evidence paths appear.
2. Review docs may carry `/tmp` only if corresponding mirror + tuple metadata exist.
3. Allowed persistent mirror roots:
   - `activity/evidence/<stream>/<date>/...`
   - `.identity/<id>/runtime/reports/...`
4. Required tuple fields:
   - `sha256`, `command`, `rc`, `timestamp`
5. Evidence admission allowlist (reverse standard):
   - config: `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
   - strict docs only allow canonical manifest + minimal replay anchors.

### 11.3 Gate wiring and acceptance

1. Validator:
   - `python3 scripts/validate_doc_evidence_persistence.py --json-only`
2. Docs contract gate (includes evidence persistence sub-check):
   - `python3 scripts/docs_command_contract_check.py`
3. CI required-gates workflow now runs both commands as fail-close steps.
4. CI delta mode:
   - `python3 scripts/validate_doc_evidence_persistence.py --enforce-delta --base <base_sha> --head <head_sha> --json-only`
   - blocks newly introduced `/tmp` evidence debt in governance/review streams.
5. Admission gate:
   - non-allowlisted `activity/evidence/*` references in strict docs fail-close.

### 11.4 Replay note

1. Evidence mirror set for v1.6.2 stream:
   - `activity/evidence/rq034/2026-03-09/`
2. This change is protocol-control-plane hardening only; it does not mutate instance business logic.
3. External reference set used in this addendum:
   - `https://developers.openai.com/codex/agent-approvals-security/`
   - `https://modelcontextprotocol.io/specification/latest/basic/lifecycle`
   - `https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts`
   - `https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-artifact-attestations`

## 12) Round-30.0 addendum: M:N full-repo deep-scan closure ledger (2026-03-09)

### 12.1 Audit objective

1. Close recurring ambiguity of “1→N fallback vs M:N strict binding”.
2. Ensure actor×identity×session closure is independently verifiable from global release status.
3. Freeze replay evidence on persistent paths (no `/tmp`-only dependency).

### 12.2 Code delta audited in this round

1. `1b4d6fb` — strict-surface session passthrough hardening
2. `d476fc6` — scan projection parity hardening
3. `423c0e0` — three-plane intake probe report linkage hardening

### 12.3 Replay bundle (persistent)

Canonical root:

1. `activity/evidence/m2m-full-scan/2026-03-09-ipmmrun002-closure-v2/`

Primary artifacts:

1. `m2m_closure_status.afterfix_v6.json`
2. `m2m_deep_scan_summary.afterfix_v6.json`
3. `release_readiness_blockers.afterfix_v6.json`
4. `evidence_manifest.ipmmrun002_closure_v2.json`
5. `m2m_post_commit_quickcheck.423c0e0.json`

### 12.4 Cross-verified findings (four tracks)

#### T1 Governance

1. Strict-surface session passthrough coverage is now `PASS_REQUIRED`.
2. CI/e2e/creator wiring no longer leaves the previously observed session blind spots.
3. M:N projection now separates M:N closure from non-M:N blocker scopes.

#### T2 Vendor

1. Deterministic lifecycle/negotiation expectations (MCP) remain aligned.
2. Centralized safety/approval enforcement posture (Codex) remains aligned.

#### T3 Reference

1. Structured strict-contract reasoning remains consistent with deterministic fail-close checks.
2. Evidence persistence and command-tuple replay are retained as mandatory audit primitives.

#### T4 Replay (actual run)

1. Final emit positive matrix:
   - multi-identity pass for `assistant:codex`
   - multi-identity pass for `user:yangxi` (bound identities)
2. Final emit negative probes:
   - ambiguous actor-only call => `IP-FE-006`
   - cross-actor/unbound identity => `IP-FE-004`
3. three-plane M:N projection:
   - assistant/user sampled identities all `m2m_binding_closure_status = PASS`
4. full-scan target3:
   - `summary_unique_targets_m2m = { pass: 3, fail: 0 }`

### 12.5 Decision split (must not be conflated)

1. M:N closure decision: **PASS**
2. Global release readiness decision: **not closed**
3. Current non-M:N blocker chain (from replay parser):
   - `IP-MM-RUN-002` (primary)
   - `IP-CAP-003` (companion)

Evidence:

1. `release_readiness_blockers.afterfix_v6.json`
2. `m2m_closure_status.afterfix_v6.json`

### 12.6 Audit-grade statement (frozen wording)

1. “M:N protocol closure completed; remaining blockers are non-M:N.”
2. “Do not reopen M:N root-cause cluster unless `m2m_binding_closure_status` regresses to FAIL.”
3. “Promotion remains blocked until non-M:N blockers are closed by corresponding owner lanes.”

## 13) Round-30.1 addendum: protocol fail-close plugin standardization closure (2026-03-09)

### 13.1 Scope

1. Convert RQ-034 single-case hardening into reusable protocol fail-close plugin standard.
2. Ensure "file path + config + gate + SSOT + wiring" is machine-verifiable in one validator path.
3. Prevent recurrence of instance-side soft-constraint regressions for protocol-core contracts.

### 13.2 Code/config delta audited

1. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml` (new)
2. `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml` (explicit requirement/target/gate metadata)
3. `identity/protocol/mappings/contract-binding.v1.6.yaml` (`asb16-rq-034` report field refs expanded)
4. `scripts/validate_control_plane_invariants.py` (plugin/prompt/entrypoint invariants extended)
5. `identity/protocol/plugins/README.md` (canonical governance asset list updated)

### 13.3 Replay evidence

1. Canonical evidence index:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Required replay anchors:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json` (`PASS_REQUIRED`)
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json` (`PASS_REQUIRED`)
   - `activity/evidence/rq034/2026-03-09/rq034_full_scan_target_regression_20260309_r5.result.json` (`PASS_REQUIRED`, `summary.p0=0`)

### 13.4 Judgment

1. Protocol-level fail-close plugin standardization is now machine-enforced and replay-backed.
2. RQ-034 is no longer a standalone special-case; it is now the template path for future protocol-core plugins.
3. Remaining non-green states remain instance evidence/runtime debts, not protocol wiring ambiguity.

## 14) Round-30.2 addendum: IP-MM-RUN-002 closure replay ledger (2026-03-09)

### 14.1 Scope

1. Close `IP-MM-RUN-002` as a protocol migration blocker (not an M:N binding blocker).
2. Re-run M:N matrix with actor-bound sessions to avoid false negatives from unbound session-id probes.
3. Freeze evidence under persistent path with tuple metadata (command/rc/sha256/timestamp).

### 14.2 Code delta audited

1. `scripts/validate_multimodal_plugin_enforcement.py`
   - added `RUNTIME_STAGE_LEGACY_REPORT_DEFER_OPERATIONS={update,readiness,three-plane}`
   - added producer-detection-gated legacy defer for missing runtime-stage fields
   - preserved strict fail-close for non-legacy/non-deferred runtime-stage violations

### 14.3 Replay evidence (persistent)

Canonical root:

1. `activity/evidence/m2m-full-scan/2026-03-09-ipmmrun002-closure-v2/`

Primary artifacts:

1. `mn_closure_final_summary.ipmmrun002_v2.json`
2. `evidence_manifest.ipmmrun002_closure_v2.json`
3. `full_scan.target3.codex.r2.json`
4. `full_scan.target3.yangxi.r3.json`
5. `three_plane.bound_sessions.summary.ipmmrun002_v2.json`
6. `release_readiness.bound.summary.ipmmrun002_v2.json`

### 14.4 Cross-verification conclusion

1. full-scan target3 (project layer) shows `summary_unique_targets={p0:0,p1:0,ok:3}` for both actors.
2. three-plane bound-session matrix:
   - `all_send_time_pass=true`
   - `all_mm_pass=true`
   - `ip_mm_run_002_hits=[]`
3. release-readiness bound matrix:
   - `ip_mm_run_002_hits=[]`
   - remaining nonzero rc is not multimodal; current replay points to changelog governance gate.
4. gate sanity:
   - surface drift pass
   - docs contract pass
   - protocol SSOT pass

### 14.5 Ledger decision update

1. `IP-MM-RUN-002` is removed from active blocker list for v1.6.2 protocol control-plane closure.
2. M:N closure remains frozen as `PASS`; do not reopen M:N root-cause unless projection regresses.
3. Remaining residuals are tracked as non-M:N:
   - `IP-CAP-003` (instance capability boundary marker),
   - readiness changelog governance gate (`validate_changelog_updated`).

## 15) Round-30.3 reasoning-loop fail-close protocolization (2026-03-09)

### 15.1 Audit finding class

1. Reasoning loop had structural checks but lacked full semantic fail-close closure.
2. Verified risk pattern:
   - `no_target_reached` can be represented without deterministic done-transition blocking unless explicitly gated.
3. Decision:
   - standardize as protocol fail-close plugin (`asb16-rq-035`) under existing v1.6.2 governance skeleton.

### 15.2 Code and config changes audited

1. Validator:
   - `scripts/validate_reasoning_loop_failclose.py`
2. Plugin assets:
   - `identity/protocol/plugins/reasoning-loop-enforcement/*`
3. Registry/governance/mapping:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`
4. Required gate + drift:
   - `scripts/required_gate_bundle_runner.py`
   - `scripts/validate_required_gate_surface_drift.py`
5. Cross-surface projection:
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`

### 15.3 Semantics now enforced

1. done-transition block is enforced by configurable completion mode:
   - default `terminal_attempt_only`: terminal unresolved attempt blocks done/pass.
   - optional `any_attempt`: historical `no_target_reached=true` also blocks done/pass.
2. `done_requires_terminal_target_reached=true` preserves strict closure for unresolved terminal completion.
3. Failed attempt without `next_action` is fail-close.
4. Escalation threshold is controlled by `escalation_requirement_mode` (default `at_or_exceed`).
5. At/over threshold without escalation signal is fail-close.
6. Escalation signal accepts boolean/token markers and configurable non-empty reference fields when enabled; generic retry `next_action` text is not escalation by default.
7. Enforcement is level-configured (`L0/L1/L2/L3`), not hardcoded:
   - `L1`: attempt trace
   - `L2`: four-track refs
   - `L3`: external freshness/reconciliation

### 15.4 Ledger judgment update

1. Reasoning-loop semantic closure is now protocolized in the same control-plane grammar as multimodal fail-close plugins.
2. This closes a protocol semantic gap and reduces “document says blocked, gate still passes” drift.
3. Remaining non-green outcomes continue to be classified by owner lane (instance/release debt), not by reopening protocol semantic closure.

## 16) Round-30.4 addendum: deep cross-verification + validator scope decoupling (2026-03-10)

### 16.1 New protocol-side finding

1. `validate_multimodal_plugin_enforcement.py` was over-scoped after multi-plugin registry expansion:
   - it enforced `required_thresholds` for non-multimodal plugin rows.
2. With `reasoning-loop-enforcement` in the same registry, this could produce false `IP-MM-THR-001` on multimodal path.

### 16.2 Protocol fix audited

1. File:
   - `scripts/validate_multimodal_plugin_enforcement.py`
2. Change:
   - threshold/provider-capability checks are now scoped to multimodal plugin rows only
     (`validator_script == scripts/validate_multimodal_plugin_enforcement.py` or `plugin_id == multimodal-vision-enforcement`).
3. Effect:
   - removes cross-plugin coupling between `asb16-rq-034` and `asb16-rq-035`.

### 16.3 Replay evidence (persistent)

Canonical root:

1. `activity/evidence/v162-cross-verify/2026-03-10/`

Core gate results:

1. `control_plane_invariants` -> `PASS_REQUIRED`
2. `plugin_literal_path_lint` -> `PASS_REQUIRED`
3. `surface_drift` -> `PASS_REQUIRED`
4. `docs_contract` -> `PASS`
5. `protocol_ssot` -> `OK`

Multimodal behavior split (expected by contract mode):

1. Strict explicit current-report path:
   - `validate_multimodal_plugin_enforcement --operation validate --run-id identity-upgrade-exec-* --report-selected-path ...`
   - result: `FAIL_REQUIRED + IP-MM-RUN-002` (expected strict fail-close when runtime-stage producer fields missing).
2. three-plane autorun legacy-defer path:
   - `validate_multimodal_plugin_enforcement --operation three-plane --run-id three-plane-*` (no explicit report path)
   - result: `PASS_REQUIRED` with:
     - `multimodal_runtime_evidence_status=SKIPPED_NOT_REQUIRED`
     - `runtime_stage_deferred=true`
     - `runtime_stage_deferred_reason=legacy_report_missing_runtime_stage_pre_execution`
3. Projection parity under same autorun semantics:
   - `validate_failclose_plugin_projection --operation three-plane` -> `PASS_REQUIRED`.

Cross-surface replay:

1. `report_three_plane_status` (strict actor/session bound) -> rc=0, `m2m_binding_closure_status=PASS`.
2. `full_identity_protocol_scan --scan-mode target --target-source-layer project` -> rc=0, `summary.ok=1`, `summary_m2m.pass=1`.

### 16.4 Ledger decision update

1. v1.6.2 control-plane plugin wiring remains stable after decoupling fix.
2. `IP-MM-RUN-002` remains a valid strict explicit-report fail-close signal; not a reopened topology/lint regression.
3. Stream posture unchanged:
   - `SPEC_READY / PENDING_INTAKE`
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`

### 16.5 Full-scan target regression addendum (round-30.5)

1. `validate_full_scan_target_regression.py` now projects m2m summary fields in its receipt:
   - `summary_m2m`
   - `m2m_pass_count`
   - `m2m_fail_count`
   - `m2m_fail_rows`
2. New optional strict flag:
   - `--enforce-m2m-pass`
   - effect: fail-close with `IP-SCAN-REG-004` when `summary_m2m.fail != 0`.
3. Compatibility policy:
   - default path keeps previous behavior (`summary.p0==0` hard gate only);
   - strict protocol lanes can enable `--enforce-m2m-pass` to remove m2m shadow-green blind spots.
4. CI rollout in this round:
   - required-gates workflow target-regression step now iterates all resolved `IDS`;
   - fixture/demo ids use baseline mode;
   - non-fixture ids use strict `--enforce-m2m-pass`.
5. Release rollout in this round:
   - `release_readiness_check.py` readiness sequence now includes `validate_full_scan_target_regression.py`;
   - fixture/demo ids remain baseline, non-fixture ids enable `--enforce-m2m-pass`.

## 17) Round-30.6 addendum: M:N hard-close closure proof (2026-03-10)

### 17.1 Audit objective

1. Convert the last M:N residual gap from advisory posture into deterministic fail-close:
   - explicit session selector enforcement,
   - canonical pointer switch receipt enforcement,
   - strict compose/session mismatch fail-close continuity.
2. Verify closure with multi-agent × multi-identity replay matrix (not single-lane anecdotal probes).

### 17.2 Code changes audited (commits + files)

1. `bb3692a` (`fix(m2m): hard-close activate session/receipt gap for canonical pointer switch`)
   - `scripts/identity_creator.py`
   - `scripts/sync_session_identity.py`
2. `140d01f` (`fix(m2m): require explicit session selector at governed compose entry`)
   - `scripts/compose_and_validate_governed_reply.py`
   - `scripts/execute_identity_upgrade.py`

### 17.3 Protocol semantics now enforced

1. activate lane:
   - explicit `--session-id` required; run-id-derived activate session is blocked (`IP-ACT-SESSION-001`).
2. canonical pointer switch:
   - tuple-bound switch intent receipt required for identity change (`IP-ASB-MB-008` / `IP-ASB-MB-009`).
3. governed compose lane:
   - explicit `--session-id` required (`IP-ASB-SESSION-ENTRY-001`).
   - session/identity mismatch remains strict fail-close (`IP-HDSTAMP-002`).

### 17.4 Replay evidence (persistent)

Canonical root:

1. `activity/evidence/v162-cross-verify/2026-03-10/bundle-parity-round2/`

Manifest:

1. `EVIDENCE_MANIFEST.bundle-parity-round2.v1.json`

Validated matrix outcomes:

1. matched actor/session/identity rows pass (`PASS_REQUIRED`).
2. cross-session or cross-identity mismatch rows fail-close (`IP-HDSTAMP-002`).
3. strict final egress without session fails-close; with bound session passes.
4. strict scan surface continuity:
   - `surface_drift.after_round308` -> `PASS_REQUIRED`
   - `control_plane_invariants.after_round308` -> `PASS_REQUIRED`
   - `full_scan.target.base_repo_architect.strict_bound` -> `summary.ok=1`, `summary.p0=0`, `summary_m2m.pass=1`
   - `three_plane.base_repo_architect.strict_bound` -> `m2m_projection.m2m_binding_closure_status=PASS`

### 17.5 Ledger decision update

1. M:N protocol control-plane residual implicit-switch gap is closed under strict governance lanes.
2. Remaining non-green outcomes are non-M:N owner-lane debt and must not be mislabeled as reopened M:N protocol regression.
3. Promotion posture remains scope-accurate:
   - M:N control-plane: hard-closed in strict lanes.
   - global release readiness: still decided by non-M:N gates.

## 18) Round-30.7 addendum: RQ-035 anti-loop retighten + projection parity hardening (2026-03-10)

### 18.1 Audit finding

1. Primary RQ-035 deadlock fix was correct (`retry-then-success` no longer blocked by historical `no_target`), but escalation strength drift appeared:
   - generic retry `next_action` could be interpreted as escalation too broadly.
2. Target effect required:
   - keep deadlock fix,
   - restore anti-loop fail-close (`IP-RL-RUN-005`) for missing real escalation signals.

### 18.2 Fix set audited

1. `scripts/validate_reasoning_loop_failclose.py`
   - added `escalation_requirement_mode` (`at_or_exceed` default),
   - tightened default escalation non-empty fields (retry text is not escalation by default),
   - enabled strict run-id binding (`strict_run_id_binding=true`) so strict operations fail-close on run-id mismatch even when runtime proof source falls back,
   - added config-driven runtime report selection mode (`runtime_report_selection_mode`, default `prefer_run_id`) to stabilize non-explicit report path behavior.
2. `scripts/validate_identity_learning_loop.py`
   - aligned threshold semantics and escalation signal rules with RQ-035 validator.
3. `scripts/create_identity_pack.py` + plugin contract
   - contract skeleton/defaults now carry `escalation_requirement_mode` and tightened escalation non-empty policy.
4. Projection hardening:
   - `scripts/report_three_plane_status.py`
   - `scripts/full_identity_protocol_scan.py`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`

### 18.3 Replay judgment

1. Deadlock path stays fixed:
   - retry-then-success completion remains `PASS_REQUIRED`.
2. Anti-loop block strength restored:
   - at/over-threshold failures without valid escalation now fail-close with `IP-RL-RUN-005`.
3. Escalation ref path remains valid:
   - non-empty escalation refs are still accepted under strict semantics.
4. Strict run binding is deterministic:
   - strict operation + provided `run_id` + mismatched selected/fallback runtime proof now fails-close with `IP-RL-RUN-006`.
5. Strict default-path behavior is stabilized:
   - with `runtime_report_selection_mode=prefer_run_id`, strict lanes prefer run-id bound runtime reports before latest/fallback paths.

## 19) Round-30.8 addendum: bundle parity debt reduction to 2 + cross-cwd bundle hardening (2026-03-10)

### 19.1 Audit conclusion

1. This round’s parity reduction is effective and machine-validated:
   - freeze baseline dropped from `20` to `2` without reopening surface drift.
2. A real stability gap was fixed during replay:
   - bundle validator subprocesses previously depended on caller cwd for relative validator paths,
   - now fixed by absolute validator path resolution + repo-root subprocess cwd binding.

### 19.2 Code changes audited

1. `scripts/required_gate_bundle_runner.py`
   - expanded bundled requirements to include stable rows:
     - `RQ-004/005/006/007/008/009/010/011/012/013/014/015/016/023/024/027/028/029`
   - added target/status mappings for these rows.
   - corrected `RQ-009` report argument forwarding (`--report`).
   - hardened subprocess execution path/cwd behavior.
2. `identity/protocol/mappings/control-plane-invariants.v1.6.yaml`
   - `baseline_missing_rows=2`.
3. `identity/protocol/mappings/bundle-parity-reduction-plan.v1.6.2.yaml`
   - baseline/phase target aligned to `2`.

### 19.3 Replay evidence (persistent)

Root:

1. `activity/evidence/v162-cross-verify/2026-03-10/bundle-parity-round2/`

Files:

1. `candidate_validator_matrix.json`
2. `bundle_validate_matrix_after_reduce2_final.json`
3. `EVIDENCE_MANIFEST.bundle-parity-round2.v1.json`

### 19.4 Replay summary

1. `validate_control_plane_invariants` -> `PASS_REQUIRED`, `missing_rows=2`.
2. `validate_required_gate_surface_drift` -> `PASS_REQUIRED`.
3. Bundle matrix across four identities:
   - rows per identity: `33`,
   - fail-close remains concentrated in active plugin lanes (`RQ-034` / `RQ-035`),
   - newly added parity rows do not introduce new unstable failure families.

### 19.5 Remaining debt (explicitly frozen)

1. Remaining non-bundled rows:
   - `asb16-rq-031`
   - `asb16-rq-032`
2. Rationale:
   - both are strict high-sensitivity output gates with existing fail-close pressure,
   - held for dedicated hardening stream to avoid mixing parity burn-down with output-gate semantics shifts.

## 20) Round-30.9 addendum: bundle parity zero-gap closure (2026-03-10)

### 20.1 Audit conclusion

1. Final parity residual rows (`asb16-rq-031` / `asb16-rq-032`) are now wired into bundle.
2. Control-plane parity is closed at mapping level:
   - `mapping_rows_missing_in_bundle_count=0`.
3. No new error-code family was introduced by this closure.

### 20.2 Fix set audited

1. `scripts/required_gate_bundle_runner.py`
   - add requirements:
     - `asb16-rq-031`
     - `asb16-rq-032`
   - add target/status mappings for both rows.
2. `identity/protocol/mappings/control-plane-invariants.v1.6.yaml`
   - freeze baseline set to `0`.
3. `identity/protocol/mappings/bundle-parity-reduction-plan.v1.6.2.yaml`
   - baseline and milestones converged to zero-gap target.

### 20.3 Replay summary

1. `validate_control_plane_invariants` -> `PASS_REQUIRED`, baseline `0`, missing rows `0`.
2. `validate_required_gate_surface_drift` -> `PASS_REQUIRED`.
3. Bundle validate matrix remains deterministic; active fail-close rows remain concentrated in runtime-proof strict lanes (`RQ-034` / `RQ-035`), not parity mapping.

### 20.4 Ownership split (enforced)

1. Protocol-layer issues (mapping/bundle parity, wiring, path/cwd stability) are closed by base repo changes in this round.
2. Instance-layer technical debt (runtime report completeness, run-id-consistent runtime evidence) remains instance-owned and is not relabeled as protocol parity regression.

## 21) Stream Continuity Alias Pointers

1. v1.6.2 review stream now keeps alias-first continuity explicit for plugin/mapping control plane.
2. Required alias anchors:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
3. Historical versioned references are preserved for replay traceability only; machine checks and future stream upgrades must bind through these current aliases.
