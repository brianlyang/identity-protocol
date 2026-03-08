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
6. Release projection for multimodal provider fields still requires dedicated closure check:
   - `scripts/release_readiness_check.py` (no `provider_config_status` / `provider_profile_id` projection anchors observed in current replay)

### 1.2 Judgment

1. Path locking and strict entry foundations: **present**.
2. Multimodal-plugin requiredization in bundle+drift: **closed**.
3. Remaining closure item is release-surface projection parity for provider fields.
4. Therefore current state is “control-plane landed, one projection parity item pending.”

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
7. Provider projection is closed for three-plane/full-scan and pending verification for release-readiness output.

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
   - evidence: `/tmp/mm_enforcement_validate_20260309.json`
2. Bundle replay passed with requiredized multimodal key:
   - `required_gate_bundle_runner --operation validate` -> `PASS_REQUIRED`
   - evidence: `/tmp/mm_bundle_validate_20260309.json`
3. Remaining replay debt is not key wiring; it is release-readiness projection parity for provider fields.

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
9. Release-readiness projection carries `provider_config_status` + `provider_profile_id`. (`PENDING`)

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
   - dry-run: `/tmp/rq034_backfill_dryrun_braev3_20260309.json`
   - apply: `/tmp/rq034_backfill_apply_braev3_20260309.json`
2. Capability arbitration contract replay passes after backfill:
   - `/tmp/rq034_capability_arbitration_validate_braev3_20260309.log`
3. Provider binding replay passes with minimal non-secret binding file:
   - `/tmp/rq034_validator_braev3_after_binding_20260309.json`

### 11.3 Cross-check evidence set (current round)

1. Plugin literal lint: `/tmp/rq034_plugin_literal_lint_20260309.json`
2. Multimodal validator positive/negative:
   - `/tmp/rq034_validator_positive_20260309.json`
   - `/tmp/rq034_validator_negative_20260309.json`
3. Bundle + tuple parity (target probe):
   - `/tmp/rq034_bundle_target_20260309.json`
   - `/tmp/rq034_bundle_target_scanprobe_20260309.json`
   - `/tmp/rq034_tuple_parity_20260309.json`
4. Strict surface drift: `/tmp/rq034_surface_drift_20260309.json`
5. Three-plane/full-scan (real instance):
   - `/tmp/rq034_three_plane_v4_20260309.json`
   - `/tmp/rq034_full_scan_v4_20260309.json`

### 11.4 Current closure judgment

1. RQ-034 strict bundle/drift/validator/full-scan wiring is closed in this round.
2. Release-readiness projection parity remains pending (see §1.1 / §7 item-9); this stream is not promotion-ready.
3. Remaining non-green signal also includes instance report freshness churn (`IP-REL-001`) and workspace dirty baseline; these are outside multimodal plugin wiring regression scope.
4. Governance boundary remains unchanged:
   - protocol layer: identify/validate/reject
   - instance layer: migration/backfill/debt cleanup
