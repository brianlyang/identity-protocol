# Identity Multimodal Plugin Enforcement Governance (v1.6.2)

Status: Active (protocol-control-plane specialization stream)  
Governance layer: protocol  
Scope: multimodal-plugin contract enforcement only  
Owner: identity protocol base-repo architect  
Execution mode: topic-level canonical SSOT for multimodal-plugin hard-gate closure

## 0) Extraction Directive (Mandatory)

### 0.1 Why v1.6.2 exists

1. Multimodal-plugin enforcement requiredization has now landed in protocol control-plane, but document state must remain single-stream to prevent stale rollback claims.
2. This topic is no longer manageable as scattered addenda in v1.6.0/v1.6.1 and needs one dedicated closure stream.
3. From this document onward, multimodal-plugin protocol enforcement updates must be landed here first.

### 0.2 SSOT precedence for this topic

1. L1 (topic SSOT): `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md` (this file)
2. L2 (historical baseline): `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
3. L3 (headstamp stream baseline): `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
4. L4 (global baseline): `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`

Hard rule:

1. Any new multimodal-plugin normative clause must be appended to this v1.6.2 stream.
2. Historical sections in v1.6.0/v1.6.1 are frozen evidence and cannot be treated as active implementation SSOT for this topic.

## 1) Current State Snapshot (Cross-verified)

### 1.1 Confirmed closure anchors (code-level)

1. Bundle requirement order includes multimodal key:
   - `scripts/required_gate_bundle_runner.py:23`
   - `scripts/required_gate_bundle_runner.py:32` (`asb16-rq-034`)
2. Strict drift requirement key set includes multimodal key:
   - `scripts/validate_required_gate_surface_drift.py:44`
   - `scripts/validate_required_gate_surface_drift.py:53` (`asb16-rq-034`)
3. Mapping row is present:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml:896`
4. Single-source validator is present:
   - `scripts/validate_multimodal_plugin_enforcement.py`
5. three-plane/full-scan projection includes provider fields:
   - `scripts/report_three_plane_status.py:3500`
   - `scripts/full_identity_protocol_scan.py:2969`
6. Release projection is closed by governance-driven projection wiring:
   - `scripts/release_readiness_check.py` -> `scripts/validate_failclose_plugin_projection.py`
   - projection keys come from `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml` (no release-script hardcoding).

### 1.2 Judgment

1. Path locking and strict entry foundations: **present**.
2. Multimodal-plugin requiredization in bundle+drift: **closed**.
3. Release-surface projection parity is closed under configuration-driven validator wiring.
4. Therefore current state is “control-plane landed with extensible fail-close projection enforcement.”

## 2) Decision Freeze: Canonical Plugin Topology + Ownership

### 2.1 Canonical location (base-repo only)

1. Plugin system canonical root is fixed to:
   - `identity/protocol/plugins/`
2. Any plugin metadata or contract file outside this tree is non-canonical.
3. Strict protocol surfaces must treat non-canonical source as `FAIL_REQUIRED` (`IP-MM-REG-001`).

### 2.2 Canonical folder/file naming contract (frozen)

Required files under base-repo plugin system:

1. Global registry layer:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`
   - `identity/protocol/plugins/schemas/plugin-registry.schema.json`
2. Per-plugin layer:
   - `identity/protocol/plugins/<plugin_id>/plugin.contract.yaml`
   - `identity/protocol/plugins/<plugin_id>/plugin.input.schema.json`
   - `identity/protocol/plugins/<plugin_id>/plugin.output.schema.json`
   - `identity/protocol/plugins/<plugin_id>/plugin.error-codes.yaml`
   - `identity/protocol/plugins/<plugin_id>/README.md`
   - `identity/protocol/plugins/<plugin_id>/fixtures/*.json`
3. Optional implementation adapter layer (if plugin has runtime adapter):
   - `identity/protocol/plugins/<plugin_id>/adapters/<adapter_id>.py`
   - `identity/protocol/plugins/<plugin_id>/adapters/README.md`

### 2.3 Naming regex (strict)

1. `plugin_id`:
   - `^[a-z][a-z0-9-]{2,63}$`
2. `adapter_id`:
   - `^[a-z][a-z0-9_]{2,63}$`
3. Validator script naming:
   - `validate_plugin_<plugin_slug>.py` (under `scripts/`)
   - where `plugin_slug` maps from `plugin_id` via `- -> _`
4. Invalid naming is hard fail-close:
   - `IP-MM-NAME-001` (plugin_id invalid)
   - `IP-MM-NAME-002` (file/entry naming invalid)

### 2.4 Deep binding to `identity/protocol/IDENTITY_PROTOCOL.md` Four core capability contracts

1. This stream is not standalone; it is the executable projection of:
   - `IDENTITY_PROTOCOL.md` -> `Four core capability contracts` -> `Accurate judgement contract`.
2. Canonical binding tuple is frozen:
   - core contract: `Accurate judgement contract`
   - kernel contract id: `rq_034_multimodal_plugin_enforcement_contract_v1`
   - requirement key: `asb16-rq-034`
   - validator: `scripts/validate_multimodal_plugin_enforcement.py`
3. Enforcement meaning is explicit:
   - `requires_multimodal_evidence_consistency=true`
   - `inconsistent_evidence_transition=block_done`
4. No business hardcoding rule:
   - protocol layer validates contract shape/capability compatibility/path policy only;
   - protocol layer must not embed domain workflow logic (for example office-ops/business-specific heuristics).
5. Business-specific orchestration remains instance-layer responsibility and must consume protocol plugin contracts by reference.

## 3) Instance Copy Policy (final answer to deployment model)

### 3.1 Default policy (mandatory)

1. **Do not copy plugin code into identity instances.**
2. Plugin contracts/registry/adapters are maintained centrally in the identity protocol base repo.
3. Identity instances are consumers only and may keep runtime artifacts only.

### 3.2 What instances are allowed to store

Allowed in instance runtime domain (for execution traceability only):

1. Activation/binding receipts:
   - `<pack>/runtime/plugins/activation/*.json`
2. Runtime decision receipts:
   - `<pack>/runtime/plugins/receipts/*.json`
3. Projection snapshots:
   - `<pack>/runtime/plugins/projections/*.json`

Forbidden in instance packs:

1. `plugin.contract.yaml`, `plugin.*.schema.json`, `plugin.error-codes.yaml` copies
2. plugin adapter source copies under instance runtime
3. ad-hoc plugin registries in instance-local paths

Any forbidden copy hit in strict operation => `FAIL_REQUIRED` (`IP-MM-COPY-001`).

### 3.3 Exception mode (narrow, explicit)

1. Air-gapped/offline environments may use **signed plugin snapshot** mode only.
2. Snapshot must carry:
   - source registry SHA
   - generated_at
   - signer
   - signature verification status
3. Unsigned snapshot or stale snapshot is `FAIL_REQUIRED` (`IP-MM-COPY-002`).
4. Exception mode is opt-in and disabled by default.

## 4) Runtime Contract (requiredization)

### 4.1 Requirement identity

1. New canonical requirement key: `asb16-rq-034`
2. Kernel contract ID: `rq_034_multimodal_plugin_enforcement_contract_v1`
3. Validator entrypoint (single-source): `scripts/validate_multimodal_plugin_enforcement.py`

### 4.2 Required control fields (must be machine-emitted)

1. `multimodal_plugin_enforcement_status`
2. `plugin_registry_status`
3. `plugin_naming_status`
4. `plugin_schema_status`
5. `plugin_threshold_status`
6. `plugin_path_status`
7. `plugin_copy_policy_status`
8. `error_code`
9. `evidence_ref`

### 4.3 Threshold contract (strict)

1. Character-count threshold and confidence threshold must be pulled from governed config source only:
   - env override (if explicitly allowed by contract)
   - runtime/state config
   - CURRENT_TASK contract fields
2. Threshold missing/NaN/out-of-range is fail-close (`IP-MM-THR-*`).
3. Strict operations cannot downgrade to `SKIPPED_NOT_REQUIRED` for threshold checks.

### 4.4 Runtime-path contract

1. Path sources remain two-layer canonical:
   - project: `<project>/.identity/<identity_id>/...`
   - global: `${CODEX_HOME:-~/.codex}/.identity/<identity_id>/...`
2. Multimodal plugin runtime roots must stay under resolved pack runtime domain.
3. Any out-of-domain plugin root is fail-close (`IP-MM-PATH-*`).

### 4.5 Role boundary (do not blur)

1. Protocol layer: identify + validate + reject only.
2. Instance layer: migrate plugin assets, backfill manifests, clear historical debt.
3. Protocol layer must not reintroduce legacy compatibility fallback for multimodal paths.

### 4.6 Provider/API configuration contract (including GLM4.6V-like vision providers)

1. Provider capability profiles are governed centrally in base repo only:
   - `identity/protocol/plugins/PROVIDER_PROFILES.v1.6.2.yaml`
   - `identity/protocol/plugins/schemas/provider-profiles.schema.json`
2. Plugin contracts must reference provider by `provider_profile_id` only (no inline secrets, no ad-hoc endpoint literals).
3. Instance runtime can store binding pointers only (non-secret):
   - `<pack>/runtime/plugins/provider-bindings.local.yaml`
   - fields: `plugin_id`, `provider_profile_id`, `credential_ref`, `enabled`
4. Secret material must not be written into repo/runtime JSON receipts:
   - allowed: environment variable names or vault key references
   - forbidden: plaintext API keys/tokens in yaml/json under repo/pack
5. Capability gate is strict:
   - if plugin requires vision but selected profile lacks `capabilities.vision=true` => `FAIL_REQUIRED` (`IP-MM-CONF-005`)
6. Configuration integrity gate is strict:
   - unknown `provider_profile_id` => `IP-MM-CONF-001`
   - missing required profile fields => `IP-MM-CONF-002`
   - unresolved `credential_ref` => `IP-MM-CONF-003`
   - non-HTTPS or non-allowlisted API endpoint => `IP-MM-CONF-004`
7. This allows GLM4.6V-like visual APIs to be onboarded by profile registration, not per-instance hardcode forks.

## 5) Mandatory Wiring (Protocol, landed)

1. `asb16-rq-034` is wired to:
   - `BUNDLE_REQUIREMENT_ORDER` (`scripts/required_gate_bundle_runner.py`)
   - `BUNDLE_REQUIREMENT_KEYS` (`scripts/validate_required_gate_surface_drift.py`)
2. Mapping row is wired in:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`
3. Contract default skeleton is wired in pack/backfill flows:
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
4. Strict-surface parity is wired for:
   - creator/readiness/three-plane/full-scan/e2e/ci all consume same status field and same error family.
5. Canonical plugin ownership markers are emitted in receipts:
   - `plugin_contract_owner=protocol_base_repo`
   - `plugin_resolution_mode=central_registry`
6. Provider profile resolution is enforced in `validate_multimodal_plugin_enforcement.py`:
   - verify `provider_profile_id` exists in provider registry
   - verify capability match (`vision/tool/json-mode`) for plugin contract
   - verify credential reference is resolvable without exposing secret material
7. Provider projection is closed for three-plane/full-scan/release-readiness output.

## 6) Four-Track Cross Verification (Roundtable/Vendor/Reference/Replay)

### T1 Governance roundtable

1. Two governance options were evaluated:
   - Option A: copy plugin code into each identity instance
   - Option B: central plugin governance in base repo, instances only invoke
2. Decision: **Option B is frozen** due to lower drift risk, single SSOT, and stronger auditability.
3. Ownership split stays immutable:
   - protocol controls contract correctness
   - instance controls runtime migration debt

### T2 Vendor track

1. MCP lifecycle favors explicit capability negotiation and deterministic server capability surfaces.
2. Codex approvals/security favors centralized policy + strict controlled execution entry.
3. Therefore plugin registry centralization is aligned with vendor-grade control-plane design.

### T3 Reference track

1. Structured output strict schema disciplines align with deterministic plugin IO contracts.
2. Agent Skills metadata discipline aligns with explicit package naming and trigger boundaries.
3. Therefore strict naming + schema + ownership policy is reference-consistent.

### T4 Replay track

Cross-verified replay (2026-03-09):

1. Positive replay passed:
   - `validate_multimodal_plugin_enforcement` -> `PASS_REQUIRED`
2. Bundle replay passed with requiredized multimodal key:
   - `required_gate_bundle_runner --operation validate` -> `PASS_REQUIRED`
3. Evidence retrieval is index-first:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
4. Remaining replay debt is baseline freshness / workspace cleanliness, not plugin wiring.

Closure replay set to retain:

1. Positive: canonical topology + valid schema + valid thresholds -> `PASS_REQUIRED`
2. Negative A: invalid naming -> `FAIL_REQUIRED` + `IP-MM-NAME-*`
3. Negative B: path escape -> `FAIL_REQUIRED` + `IP-MM-PATH-*`
4. Negative C: instance copy policy violation -> `FAIL_REQUIRED` + `IP-MM-COPY-*`
5. Negative D: provider profile missing -> `FAIL_REQUIRED` + `IP-MM-CONF-001`
6. Negative E: vision capability mismatch -> `FAIL_REQUIRED` + `IP-MM-CONF-005`

## 7) Acceptance checklist (stateful)

1. `required_gate_bundle_runner` includes `asb16-rq-034` in strict surfaces. (`PASS`)
2. `validate_required_gate_surface_drift` includes multimodal requirement key coverage. (`PASS`)
3. Three-plane/full-scan projection includes multimodal + provider status fields. (`PASS`)
4. Strict validator result for multimodal contract is requiredized. (`PASS`)
5. Plugin non-canonical path is fail-close. (`PASS`)
6. Instance-local plugin source copy is fail-close. (`PASS`)
7. Provider profile resolution and capability matching are strict required checks. (`PASS`)
8. Runtime receipts do not expose plaintext secret material. (`PASS`)
9. Release-readiness projection carries `provider_config_status` + `provider_profile_id`. (`PASS`)

## 8) Command contract and replay notes

1. `scripts/validate_multimodal_plugin_enforcement.py` CLI contract is:
   - `--catalog`
   - `--identity-id`
   - `--operation`
   - `--json-only` (optional)
2. `--repo-catalog` is not a valid argument for this validator and must not appear in acceptance command templates.
3. Baseline command-check gates remain mandatory:
   - `python3 scripts/docs_command_contract_check.py`
   - `python3 scripts/validate_protocol_ssot_source.py`

## 9) Boundary and release posture

1. This stream closes protocol control-plane gaps only.
2. Instance plugin content quality and migration backlog remain instance debt.
3. Lifecycle boundary remains non-promotional:
   - `SPEC_READY / PENDING_INTAKE`
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`

## 10) Reference anchors

1. `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
2. `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
3. `docs/review/protocol-remediation-audit-ledger-v1.6.md`
4. `/Users/yangxi/claude/codex_project/ddm/identity_protocol_feedback/multimodal-plugin-enforcement-mechanism-deepdive-20260308.md`
5. `https://modelcontextprotocol.io/specification/latest`
6. `https://developers.openai.com/codex/agent-approvals-security/`
7. `https://developers.openai.com/api/docs/guides/function-calling/#strict-mode`
8. `https://developers.openai.com/api/docs/guides/structured-outputs/#additionalproperties-false-must-always-be-set-in-objects`
9. `https://agentskills.io/specification`

## 11) Round-29.3 implementation closure addendum (2026-03-09)

### 11.1 Protocol-layer code closure landed this round

1. Plugin literal-path lint false positives are closed without weakening canonical policy:
   - `scripts/validate_plugin_contract_literal_paths.py`
   - contextual allow only for canonical dynamic resolution in `validate_multimodal_plugin_enforcement.py`
2. Target-probe bundle receipts now carry HUD parity tuple fields (no projection loss in target mode):
   - `scripts/required_gate_bundle_runner.py`
   - added passthrough defaults for `actor_id`, `resolved_work_layer`, `resolved_source_layer`, `lock_state`
3. Provider binding enforcement is hardened in multimodal validator:
   - `scripts/validate_multimodal_plugin_enforcement.py`
   - required plugin binding missing => `FAIL_REQUIRED` (`IP-MM-CONF-001`)
4. Instance-side minimal binding template is standardized:
   - `identity/protocol/plugins/templates/provider-bindings.local.template.yaml`
   - only non-secret pointers (`provider_profile_id`, `credential_ref`, `enabled`)
5. Doc command checker now includes v1.6.2 governance/review streams in mandatory checks:
   - `scripts/docs_command_contract_check.py`

### 11.2 Instance-side self-repair replay (non-protocol mutation)

1. Backfill replay for real instance (`base-repo-audit-expert-v3`) confirms RQ-034 contract auto-wire:
   - detailed artifacts are indexed in `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Capability arbitration contract replay passes after backfill:
   - anchor in manifest stream (`rq034_capability_arbitration_validate_braev3_20260309.log`)
3. Provider binding replay passes with minimal non-secret binding file:
   - anchor in manifest stream (`rq034_validator_braev3_after_binding_20260309.json`)

### 11.3 Cross-check evidence set (current round)

1. Canonical index (mandatory for full artifact lookup):
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Minimal anchor set kept in-governance doc:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json`
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json`
   - `activity/evidence/rq034/2026-03-09/rq034_full_scan_target_regression_20260309_r5.result.json`
3. Readability policy freeze:
   - governance/review docs keep index + anchor set only;
   - exhaustive per-run logs stay in evidence manifest and mirror directory.

### 11.4 Current closure judgment

1. RQ-034 strict bundle/drift/validator/full-scan wiring is closed in this round.
2. Release-readiness projection parity is closed in this round (see §1.1 / §7 item-9).
3. Remaining non-green signal includes instance report freshness churn (`IP-REL-001`) and workspace dirty baseline; these are outside multimodal plugin wiring regression scope.
4. Governance boundary remains unchanged:
   - protocol layer: identify/validate/reject
   - instance layer: migration/backfill/debt cleanup

## 12) Round-29.4 plugin interface exposure normalization addendum (2026-03-09)

### 12.1 Scope freeze (prevent topic drift)

1. v1.6.2 keeps one focused mission: **plugin-system interface normalization under protocol control-plane**.
2. This addendum does **not** redefine generic full-protocol interfaces from v1.6.0/v1.6.1 streams.
3. Any cross-topic requirement must still be anchored in:
   - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
   - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`

### 12.2 Interface exposure contract matrix (protocol-owned vs instance-writable)

| Interface surface | Canonical location / shape | Owner | Instance writable | Secret policy | Stability |
| --- | --- | --- | --- | --- | --- |
| Plugin registry + plugin contracts + schemas | `identity/protocol/plugins/**` | protocol base repo | No | No secrets allowed | Stable |
| Provider profile registry | `identity/protocol/plugins/PROVIDER_PROFILES.v1.6.2.yaml` | protocol base repo | No | No secrets allowed | Stable |
| Instance provider binding pointer | `<pack>/runtime/plugins/provider-bindings.local.yaml` | instance runtime | Yes (pointer-only) | Only `credential_ref` pointer (`env:`/`vault:`), never plaintext key | Stable |
| Active execution report pointer | `<pack>/runtime/state/active_execution_report.json` | protocol execution chain | Runtime-generated | No secrets required | Extendable |
| Strict bundle tuple passthrough | `scripts/required_gate_bundle_runner.py` args/receipt fields | protocol orchestration | Input only via orchestrator | No secrets required | Stable |
| Multimodal enforcement receipt | `scripts/validate_multimodal_plugin_enforcement.py` JSON payload | protocol validator | No (consume-only) | No secrets in receipt | Stable |

### 12.3 Protocol-exposed extension hooks (what instances may do)

Instances can extend capability under protocol governance only through these hooks:

1. Provide local binding pointers (`provider_profile_id`, `credential_ref`, `enabled`) in:
   - `runtime/plugins/provider-bindings.local.yaml`
2. Select provider profile by registry ID (no profile copy/fork in instance pack).
3. Supply runtime execution context (`run_id`, actor/layer tuple) through strict orchestrator entry.
4. Emit protocol-feedback evidence into canonical runtime feedback directories for correlation.

Instances must **not**:

1. Copy plugin contracts/schemas/adapters into identity pack runtime tree.
2. Replace canonical plugin registry/provider-profile source paths.
3. Bypass strict validator/error-code contract by ad-hoc local scripts.

### 12.4 Fail-close invariants (frozen)

1. Non-canonical plugin literal path => `FAIL_REQUIRED` (`IP-MM-LINT-001`).
2. Missing provider binding for required plugin => `FAIL_REQUIRED` (`IP-MM-CONF-001`).
3. Provider capability mismatch to required plugin contract => `FAIL_REQUIRED` (`IP-MM-CONF-005`).
4. Instance-side plugin source copy detected => `FAIL_REQUIRED` (`IP-MM-COPY-001`).
5. Any unresolved/invalid credential reference pointer => `FAIL_REQUIRED` (`IP-MM-CONF-003`).

### 12.5 Four-track cross verification (Roundtable / Vendor / Reference / Replay)

#### T1 Governance roundtable

1. Option A (rejected): per-instance plugin code/contracts copy.
2. Option B (accepted): centralized plugin SSOT in protocol repo + instance pointer binding only.
3. Decision freeze: retain Option B to minimize drift entropy and keep single audit choke-point.

#### T2 Vendor track

1. MCP lifecycle emphasizes explicit capability surfaces and deterministic negotiation boundaries.
2. Codex approvals/security emphasizes centralized policy + controlled execution gateway.
3. The protocol-owned plugin registry + instance pointer binding model matches both patterns.

#### T3 Reference track

1. Structured-output strictness aligns with schema-first plugin IO contracts.
2. Agent-skills metadata style aligns with explicit naming, discoverability, and trigger boundaries.
3. Therefore plugin interface normalization remains reference-consistent without business hardcoding.

#### T4 Replay track

Current replay set (this round):

1. Canonical evidence index:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Minimal anchors for this replay:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json`
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json`
3. Detailed lint/negative matrices are tracked in manifest only to keep governance doc readable.

### 12.6 Updated judgment for v1.6.2 interface layer

1. Plugin-scope interface exposure contract is now normalized and replay-verifiable on strict lint/validator surfaces.
2. Protocol/instance boundary is explicit:
   - protocol controls schema + validation + rejection policy;
   - instances provide pointer-level bindings and evidence only.
3. Promotion status remains unchanged from §11.4 due to remaining non-v1.6.2 items (external baseline debt).

## 13) Round-29.5 evidence persistence hard-gate addendum (2026-03-09)

### 13.1 Why this addendum

1. `/tmp` evidence is ephemeral and hard to replay after handoff.
2. Prior rounds repeatedly reported “evidence path exists in text but not in durable storage”.
3. For v1.6.2 plugin stream, evidence references are now normalized to persistent mirrors and machine-checkable tuple metadata.

### 13.2 Hard rules (gate-level, frozen)

1. Governance doc stream must not use `/tmp/...` as evidence path.
2. Review stream may mention `/tmp/...` only when mirror + tuple metadata are present (see §13.3).
3. Persistent mirror path is restricted to:
   - `activity/evidence/<stream>/<date>/...`
   - `.identity/<id>/runtime/reports/...`
4. Every mirrored evidence item must expose tuple fields:
   - `sha256`
   - `command`
   - `rc`
   - `timestamp`
5. Strict doc evidence admission is allowlist-driven (reverse standard):
   - config: `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
   - only canonical manifest + minimal replay anchors are allowed in strict governance/review docs.

### 13.3 Canonical mirror index for this stream

1. Evidence mirror root:
   - `activity/evidence/rq034/2026-03-09/`
2. Evidence tuple manifest:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
3. This manifest is now the canonical replay index for all v1.6.2 evidence references in this document/review ledger pair.

### 13.4 Gate wiring

1. `scripts/validate_doc_evidence_persistence.py` enforces this addendum.
2. `scripts/docs_command_contract_check.py` now invokes this validator fail-close.
3. CI required-gates workflow now executes both checks explicitly.
4. Delta hardening is enabled in CI:
   - `--enforce-delta --base <base_sha> --head <head_sha>`
   - semantics: governance/review docs cannot introduce new `/tmp` evidence debt in changed lines.
5. Admission hardening:
   - strict docs fail on non-allowlisted `activity/evidence/*` references or excessive evidence-link counts.

### 13.5 Cross-check alignment (roundtable/vendor/reference/replay)

1. Roundtable:
   - We preserve protocol/instance boundary by storing protocol evidence in repo-controlled `activity/evidence/**`.
2. Vendor:
   - Codex security guidance emphasizes auditable control layers and controlled execution boundaries.
3. Reference:
   - MCP lifecycle emphasizes explicit lifecycle boundaries and deterministic state transitions.
4. Replay:
   - All prior v1.6.2 `/tmp` references in this stream are replaced by persistent mirrors under `activity/evidence/rq034/2026-03-09/`, with tuple metadata in manifest.

Reference anchors:

1. `https://developers.openai.com/codex/agent-approvals-security/`
2. `https://modelcontextprotocol.io/specification/latest/basic/lifecycle`
3. `https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts`
4. `https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-artifact-attestations`

## 14) Round-30.0 addendum: multi-agent × multi-identity (M:N) closure statement (2026-03-09)

### 14.1 Scope and objective (frozen)

1. This addendum freezes only **protocol control-plane M:N closure**:
   - actor × identity × session strict binding
   - strict surface/session passthrough consistency
   - final egress ambiguity fail-close behavior
2. This addendum does **not** reclassify instance capability debt as M:N debt.
3. Promotion posture remains governed by all planes; M:N closure alone does not imply `READY_FOR_PROMOTION`.

### 14.2 Protocol hardening landed (code-level)

1. Strict-surface session passthrough hardening:
   - `scripts/validate_required_gate_surface_drift.py`
   - `.github/workflows/_identity-required-gates.yml`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/identity_creator.py`
2. Scan/projection hardening for multimodal preflight and target probe report linkage:
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
3. Intake quorum target probe now receives explicit report path:
   - `scripts/report_three_plane_status.py`
4. Commits:
   - `1b4d6fb`
   - `d476fc6`
   - `423c0e0`

### 14.3 Four-track cross verification (deep replay)

#### T1 Governance roundtable

1. M:N classification now has deterministic split:
   - `m2m_projection.m2m_binding_closure_status`
   - `m2m_projection.non_m2m_failure_scope`
2. Decision freeze:
   - M:N failures only include actor/session/final-egress ambiguity families.
   - generic bundle/instance capability failures are not auto-labeled M:N.

#### T2 Vendor track

1. MCP lifecycle aligns with explicit negotiated context and deterministic transitions.
2. Codex approvals/security aligns with centralized control-plane enforcement and fail-close outlets.
3. The current architecture (single protocol control-plane + strict entry tuple + fail-close final egress) remains vendor-consistent.

#### T3 Reference track

1. Strict structured contract posture remains aligned with schema-first deterministic checks.
2. Evidence persistence remains aligned with controlled artifact retention and auditable command execution.

#### T4 Replay track (persistent evidence only)

Canonical evidence root:

1. `activity/evidence/m2m-full-scan/2026-03-09-afterfix-v6/`

Key closure artifacts:

1. `m2m_closure_status.afterfix_v6.json`
2. `m2m_deep_scan_summary.afterfix_v6.json`
3. `release_readiness_blockers.afterfix_v6.json`
4. `EVIDENCE_MANIFEST.m2m-deep-scan-afterfix-v6.json`
5. `m2m_post_commit_quickcheck.423c0e0.json`

Acceptance snapshot (this round):

1. `m2m_core_closure_status = PASS`
2. `strict_surface_drift_status = PASS_REQUIRED`
3. `final_emit_positive_all_pass = true`
4. `final_emit_ambiguous_failclose = true`
5. `full_scan_target3_m2m = { total_identities: 3, pass: 3, fail: 0 }`

### 14.4 Misjudgment prevention contract (new freeze)

When evaluating closure, enforce this order:

1. Check `m2m_projection.m2m_binding_closure_status` first.
2. If M:N is `PASS` but overall plane is non-green, classify as non-M:N and read:
   - `m2m_projection.non_m2m_failure_scope`
   - `release_readiness_blockers.afterfix_v6.json`
3. Do not reopen M:N root-cause tickets for non-M:N blockers (`instance_plane/release_plane/repo_plane` scope) unless M:N projection turns FAIL.

### 14.5 Residual blockers (explicitly non-M:N)

Current non-M:N blockers remain:

1. `IP-MM-RUN-002` (runtime multimodal evidence completeness) — **superseded by 15.6 closure addendum**
2. `IP-CAP-003` (capability env/auth boundary)
3. Residual bundle/readiness chain impacts under instance/release/repo scopes

These are instance/release control-plane debts and are excluded from M:N closure reopening.

### 14.6 Final governance judgment for this stream

1. **M:N protocol control-plane is closed in this round.**
2. Stream posture remains non-promotional due non-M:N blockers.
3. Future audits must distinguish:
   - `M:N closure status`
   - `global release readiness status`

## 15) Round-30.1 addendum: standardized fail-close plugin wiring baseline (2026-03-09)

### 15.1 Why this addendum

1. RQ-034 has proven that strict fail-close plugin governance is workable in production.
2. Repeated instance-side regressions show soft prompt constraints are insufficient for protocol-core contracts.
3. We need a reusable protocol-level standard that binds: file path + config + gate + SSOT + wiring.

### 15.2 Standardized governance assets (new baseline)

1. Single-source plugin fail-close governance file:
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`
2. Registry row now carries explicit wiring metadata:
   - `requirement_key`
   - `bundle_target_name`
   - `gate_mode=fail_close_strict`
   - `ssot_mapping_ref`
3. Mapping SSOT (`contract-binding.v1.6`) for `asb16-rq-034` is expanded with runtime-proof report fields:
   - `multimodal_runtime_evidence_status`
   - `multimodal_preflight_status`
   - `runtime_report_path`
   - `runtime_report_run_id`
   - `multimodal_calls/resolved/unresolved/errors/retry_calls`
   - `runtime_gate_mode`
   - `runtime_gate_required_confidence`
   - `multimodal_runtime_evidence_refs`

### 15.3 Gate wiring (fail-close, machine-enforced)

1. `scripts/validate_control_plane_invariants.py` now validates:
   - bundle/mapping parity mode invariants,
   - unique egress invariants (`scripts/final_emit_governed.py` + `final_emit_governed`),
   - single bundle-entry invariants (`scripts/required_gate_bundle_runner.py`),
   - plugin registry ↔ mapping ↔ bundle target consistency,
   - strict-surface anti-bypass (no direct validator wiring on strict surfaces),
   - prompt fail-close binding tokens in `scripts/execute_identity_upgrade.py`.
2. This validator is already wired into required CI gates (`_identity-required-gates.yml`).

### 15.4 Cross-verification replay (this addendum)

1. Canonical replay index:
   - `activity/evidence/rq034/2026-03-09/EVIDENCE_MANIFEST.v1.6.2.json`
2. Required anchors:
   - `activity/evidence/rq034/2026-03-09/rq034_invariants_plugin_wiring_20260309_r3.json` (`PASS_REQUIRED`)
   - `activity/evidence/rq034/2026-03-09/rq034_surface_drift_20260309_r7.json` (`PASS_REQUIRED`)

### 15.5 Normative decision

1. Identity protocol core contracts that affect release reliability must be protocol-layer fail-close plugins.
2. Instance lanes may supply bindings/evidence only; they must not redefine protocol fail-close semantics.
3. Prompt soft constraints remain advisory; contract closure remains controlled by executable protocol gates.

## 15.6 Round-30.2 addendum: IP-MM-RUN-002 protocol closure + M:N re-verification freeze (2026-03-09)

### 15.6.1 Why this addendum

1. Round-30.0 previously tagged `IP-MM-RUN-002` as a non-M:N residual blocker.
2. Deep replay showed the remaining hit pattern came from legacy reports missing runtime-stage producer fields under strict `three-plane/readiness` operations.
3. We needed a protocol-layer migration-safe closure that:
   - does not relax strict fail-close for fresh producer reports,
   - but prevents false-blocking on legacy pre-producer reports.

### 15.6.2 Protocol patch (governance intent)

1. Validator: `scripts/validate_multimodal_plugin_enforcement.py`
2. Closure mechanism:
   - Introduce legacy runtime-stage defer scope for strict replay surfaces:
     - `update`, `readiness`, `three-plane`
   - Gate defer by producer-detection signal:
     - defer allowed only when `runtime_stage_producer_detected=false` and legacy stage fields are absent
   - Emit explicit deferred metadata:
     - `runtime_stage_deferred=true`
     - `runtime_stage_deferred_reason=legacy_report_missing_runtime_stage_pre_execution`
3. Resulting contract posture:
   - fresh reports with producer receipts still follow strict runtime-stage checks;
   - legacy reports are migrated through explicit defer semantics, not silent pass-through.

### 15.6.3 Four-track cross-verification (persistent evidence)

Canonical evidence root:

1. `activity/evidence/m2m-full-scan/2026-03-09-ipmmrun002-closure-v2/`

Replay snapshots:

1. Final summary: `mn_closure_final_summary.ipmmrun002_v2.json`
2. Evidence tuple manifest (command/rc/sha256/timestamp):
   - `evidence_manifest.ipmmrun002_closure_v2.json`
3. M:N deep scan (target3, project layer):
   - `full_scan.target3.codex.r2.json`
   - `full_scan.target3.yangxi.r3.json`
4. Bound-session three-plane matrix:
   - `three_plane.bound_sessions.summary.ipmmrun002_v2.json`
5. Release-readiness bound summary:
   - `release_readiness.bound.summary.ipmmrun002_v2.json`
6. Gate sanity:
   - `surface_drift.json`
   - `docs_contract.log`
   - `protocol_ssot.log`

### 15.6.4 Frozen decision update

1. `IP-MM-RUN-002` is closed at protocol layer for v1.6.2 control-plane semantics.
2. M:N closure remains `PASS` in both actor lanes (`assistant:codex`, `user:yangxi`) under project-layer target scan.
3. Remaining non-green state is now classified as **non-multimodal/non-M:N residual debt**, primarily:
   - `IP-CAP-003` phase transition marker (instance capability env/auth boundary),
   - readiness changelog governance gate (`validate_changelog_updated`) in current working range.

## 16) Round-30.3 reasoning-loop fail-close standardization addendum (2026-03-09)

### 16.1 Why this addendum

1. `Reasoning loop contract` has long been validated at structure level, but semantic fail-close was not fully protocolized.
2. The core semantic gap is explicit in `IDENTITY_PROTOCOL.md`: `"No-target-reached" cannot be treated as completion`.
3. This round promotes reasoning-loop semantics to the same plugin-governance rail used by `asb16-rq-034`.

### 16.2 Standardized protocol wiring landed

1. New requirement key:
   - `asb16-rq-035`
2. New contract and validator:
   - `rq_035_reasoning_loop_failclose_contract_v1`
   - `scripts/validate_reasoning_loop_failclose.py`
3. New plugin governance assets:
   - `identity/protocol/plugins/reasoning-loop-enforcement/plugin.contract.yaml`
   - `identity/protocol/plugins/reasoning-loop-enforcement/plugin.input.schema.json`
   - `identity/protocol/plugins/reasoning-loop-enforcement/plugin.output.schema.json`
   - `identity/protocol/plugins/reasoning-loop-enforcement/plugin.error-codes.yaml`
4. Registry/governance/mapping are now all connected:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`
5. Bundle/surface wiring is landed:
   - `scripts/required_gate_bundle_runner.py`
   - `scripts/validate_required_gate_surface_drift.py`

### 16.3 Semantic fail-close rules (non-hardcoded level model)

1. `reasoning_enforcement_level` is config-driven (`L0/L1/L2/L3`), not script hardcoding.
2. Hard semantic closure (all strict lanes):
   - `no_target_reached=true` + completion state => `FAIL_REQUIRED`
   - failed attempt without `next_action` => `FAIL_REQUIRED`
   - failed attempts beyond threshold without escalation signal => `FAIL_REQUIRED`
3. Level gates:
   - `L1`: attempt trace integrity
   - `L2`: `L1` + four-track evidence refs (`roundtable/vendor/network/reference`)
   - `L3`: `L2` + external freshness/reconciliation constraints

### 16.4 Projection parity closure

1. `three-plane` and `full-scan` now both emit reasoning-loop plugin projection fields from target probe receipts.
2. `release-readiness` inherits closure through `validate_failclose_plugin_projection.py` from governance profile (configuration-driven, no release-script plugin hardcoding).

### 16.5 Boundary and posture

1. This addendum closes protocol control-plane semantics for reasoning-loop fail-close.
2. It does not auto-close instance historical debt; instance lanes still own migration/backfill freshness.
3. Stream posture remains non-promotional:
   - `SPEC_READY / PENDING_INTAKE`
   - `ACCEPT_WITH_FIX != READY_FOR_PROMOTION`

## 17) Round-30.4 deep cross-verification addendum (2026-03-10)

### 17.1 New protocol defect found during cross-verification (fixed this round)

1. Defect class: cross-plugin validator coupling.
2. Root cause:
   - `validate_multimodal_plugin_enforcement.py` iterated all registry plugins and unconditionally enforced `required_thresholds`.
   - after introducing `reasoning-loop-enforcement`, multimodal validator could fail with `IP-MM-THR-001` even when multimodal contract itself was valid.
3. Protocol fix:
   - threshold/provider-capability checks are now scoped to multimodal plugin rows only (`validator_script == scripts/validate_multimodal_plugin_enforcement.py` or `plugin_id == multimodal-vision-enforcement`).
4. Impact:
   - removes false fail-close coupling between `asb16-rq-034` and `asb16-rq-035`.

### 17.2 Cross-verification matrix (roundtable / vendor / reference / replay)

#### T1 Governance roundtable

1. `asb16-rq-034` and `asb16-rq-035` remain separately owned contracts; registry co-location must not imply semantic coupling.
2. New invariant frozen:
   - plugin-specific validator may only enforce plugin-specific contract semantics.

#### T2 Vendor track

1. Capability-specific validators should remain deterministic and scoped; cross-capability bleed introduces non-deterministic policy outcomes.
2. This fix keeps plugin control-plane aligned with explicit capability negotiation boundaries.

#### T3 Reference track

1. Structured contract governance requires field constraints to apply only in-schema for that contract.
2. The fix re-aligns runtime enforcement with schema/contract ownership boundaries.

#### T4 Replay track (persistent evidence only)

Evidence root:

1. `activity/evidence/v162-cross-verify/2026-03-10/`

Key replay outcomes:

1. Core gates:
   - `validate_control_plane_invariants` -> `PASS_REQUIRED`
   - `validate_plugin_contract_literal_paths` -> `PASS_REQUIRED`
   - `validate_required_gate_surface_drift` -> `PASS_REQUIRED`
2. Multimodal strict explicit report path:
   - `operation=validate`, explicit `run_id + report_selected_path` -> `FAIL_REQUIRED + IP-MM-RUN-002` (strict current-report path, expected).
3. Multimodal strict three-plane autorun path:
   - `operation=three-plane`, no explicit report path, run id `three-plane-*` -> `PASS_REQUIRED` with
     - `multimodal_runtime_evidence_status=SKIPPED_NOT_REQUIRED`
     - `runtime_stage_deferred=true`
     - `runtime_stage_deferred_reason=legacy_report_missing_runtime_stage_pre_execution`
4. Projection parity:
   - `validate_failclose_plugin_projection --operation three-plane` (autorun path) -> `PASS_REQUIRED`.
5. Cross-surface:
   - `report_three_plane_status` (strict actor/session bound) -> rc=0, `m2m_binding_closure_status=PASS`
   - `full_identity_protocol_scan --scan-mode target --target-source-layer project` -> rc=0, `summary.ok=1`, `summary_m2m.pass=1`

### 17.3 Decision freeze after round-30.4

1. v1.6.2 plugin wiring remains closed on protocol control-plane.
2. `IP-MM-RUN-002` remains a valid strict fail-close on explicit current-report path when runtime-stage producer fields are missing.
3. The deferred-pass behavior is limited to explicitly governed legacy replay scope (e.g., three-plane autorun path), not a global downgrade.

### 17.4 Full-scan regression gate hardening (round-30.5)

1. `scripts/validate_full_scan_target_regression.py` now emits `summary_m2m`, `m2m_pass_count`, `m2m_fail_count`, and `m2m_fail_rows` in receipt payload.
2. Optional strict switch is introduced:
   - `--enforce-m2m-pass`
   - semantics: keep existing `summary.p0==0` check and additionally fail-close when `summary_m2m.fail != 0`.
3. Default behavior remains backward compatible (switch off), so fixture-heavy lanes do not get broken by default.
4. Protocol strict lanes can turn the switch on to block “`p0=0` but m2m closure failed” shadow regressions.
