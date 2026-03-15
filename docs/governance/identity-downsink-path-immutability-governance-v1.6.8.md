# Identity Downsink Path Immutability Governance (v1.6.8)

Status: Active (implementation landed + serial replay verified, 2026-03-14)  
Layer: protocol  
Scope: all protocol-governed downsink assets (runtime gate / runtime broadcast / runtime protocol-feedback / future governed domains)

Execution mode: topic-level canonical SSOT for v1.6.8 path immutability closure.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.8 downsink path immutability.
2. v1.6.6 and v1.6.7 remain valid and are inherited unless explicitly superseded by this stream.
3. Current-state judgment must prioritize machine outputs from:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. Temporary runtime paths and ad-hoc logs are replay evidence only; they are never normative path contracts.
5. Canonical mapping entrypoints are current-pointer files only:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`

## 0.1) Terminology and boundary lock (mandatory)

1. Protocol base repository: `identity-protocol-local`.
2. Business project repository: `<project>` (example: `weixinstore`).
3. Identity runtime layers:
   - project layer instance: `<project>/.identity/<identity_id>/...`
   - global layer instance: `${CODEX_HOME}/.identity/<identity_id>/...`
4. This stream governs **path immutability of protocol-governed downsink assets**.
5. This stream does not change business logic ownership and does not authorize instance-side free-form path rewiring.

## 1) Why v1.6.8 is required

v1.6.6 closed wrapper channel routing (ingress/egress/session-chain).  
v1.6.7 closed dual-active cross-layer runtime ownership ambiguity.

Remaining closure gap:

1. Some protocol-governed paths are still “contract-consistent but mutable” instead of “immutably fixed”.
2. Runtime assets can remain machine-pass while drifting to non-canonical instance paths.
3. Protocol-feedback and future governed domains can fragment if path authority is not centralized.

v1.6.8 closes this by freezing a single rule:

1. Any protocol-governed downsink asset path must be declared in one core contract registry.
2. Runtime writes must resolve through that registry only.
3. Non-registry path writes are invalid and fail-close.

## 2) Non-negotiable contracts (no ambiguity)

### 2.1 Core contract (new mandatory)

Each runtime identity must declare:

- `protocol_downsink_path_immutability_contract_v1`

Minimum fields:

1. `required: true`
2. `contract_id: protocol_downsink_path_immutability_contract_v1`
3. `validator_id: validate_protocol_downsink_path_immutability`
4. `write_guard_validator_id: validate_protocol_downsink_path_write_guard`
5. `path_registry` (mandatory registry map, see 2.2)
6. `anchor_policy`:
   - `protocol_repo_root_ref`
   - `identity_pack_root_ref`
   - `allow_parent_escape: false`
   - `allow_symlink_escape: false`
7. `schema_policy`:
   - `reject_additional_properties: true`
   - `require_all_declared_paths_present_in_runtime_contract: true`
8. `operation_enforcement`:
   - `strict_operations`
   - `light_operations`
   - `strict_fail_mode: fail_required`
   - `light_fail_mode: fail_required`

### 2.2 Path registry model (new mandatory)

`path_registry` is the only authority for protocol-governed downsink paths.

#### 2.2.1 Required domains (v1.6.8 baseline)

1. `runtime_gate`
   - `runtime/gate/protocol_ingress_wrapper.py`
   - `runtime/gate/protocol_egress_wrapper.py`
   - `runtime/gate/protocol_session_chain_wrapper.py`
   - `runtime/gate/protocol_gateway_contract.json`
2. `runtime_broadcast`
   - `runtime/state/broadcast_state.json`
   - `runtime/reports/broadcast/broadcast-receipt-*.json`
   - `runtime/reports/broadcast/broadcast-ack-*.json`
3. `runtime_protocol_feedback`
   - `runtime/protocol-feedback/outbox-to-protocol/`
   - `runtime/protocol-feedback/evidence-index/INDEX.md`
   - `runtime/protocol-feedback/upgrade-proposals/`
4. `protocol_broadcast_source`
   - `identity/protocol/broadcast/items/`
   - `identity/protocol/broadcast/index.json`
   - `identity/protocol/broadcast/schema/broadcast-item.v1.json`

#### 2.2.2 Registry expansion rule

1. Any new protocol-governed downsink asset must first add a `path_id` entry in `path_registry`.
2. Runtime write logic must reference `path_id`, not free-form path literals.
3. Unregistered paths are write-blocked by policy.

### 2.3 Path resolution and hardening policy

1. All runtime path resolution must be anchor-based (`protocol_repo_root_ref` or `identity_pack_root_ref`).
2. User-specific absolute path literals are forbidden in protocol source contracts.
3. Runtime absolute paths may exist only as resolved mirrors generated from anchors.
4. Parent traversal (`../`) escape is forbidden.
5. Symlink escape outside anchor roots is forbidden.

### 2.4 CURRENT_TASK ↔ runtime contract parity policy

1. `CURRENT_TASK` is declaration source.
2. Runtime mirror contract must preserve field-level parity for `path_registry`, `anchor_policy`, and enforcement policies.
3. Any parity drift is `FAIL_REQUIRED`.

### 2.5 Protocol-feedback special hardening policy

1. `runtime/protocol-feedback` is governed runtime space, not a free-form scratch directory.
2. Outbox/index/proposal paths are mandatory fixed registry entries.
3. Any protocol-feedback emission outside registered paths is `FAIL_REQUIRED`.
4. Mirror-only evidence without canonical outbox linkage remains invalid.

### 2.6 Anti-forget protocol law lock (mandatory)

1. Path governance must be machine-enforced, not memory-enforced.
2. Source code introducing governed runtime path literals without registry linkage is `FAIL_REQUIRED`.
3. Inline bypass is forbidden by default and only allowed with explicit marker:
   - `downsink-path-lock: allow-nonregistry-literal`
4. The marker is governance-audited and does not relax runtime write-guard policy.

## 3) CI and validator closure model (mandatory)

### 3.1 New required validators

1. `validate_protocol_downsink_path_immutability` (planned validator entrypoint)
   - validates contract presence, schema strictness, required domains, path canonicality, anchor containment.
2. `validate_protocol_downsink_path_write_guard` (planned validator entrypoint)
   - validates writes/receipts/acks/outbox artifacts are inside registered path targets.
3. `validate_protocol_downsink_path_literal_lock` (planned validator entrypoint)
   - validates protocol source path literals are registry-bound and fail-close on unregistered governed literals.

### 3.2 New required CI probes (negative)

`required` pipeline must include fixed negative probes:

1. mutate one registry path to non-canonical sibling => must fail.
2. attempt parent-escape path (`../`) => must fail.
3. attempt symlink escape outside anchor => must fail.
4. write protocol-feedback batch to non-registry directory => must fail.
5. write broadcast receipt to non-registry directory => must fail.
6. introduce unregistered governed runtime path literal => must fail.

### 3.3 New required CI probes (positive)

1. canonical registry + canonical writes => pass.
2. CURRENT_TASK/runtime parity => pass.
3. gate/broadcast/feedback all resolve via registry path IDs => pass.

## 4) Reference implementation contract (for code landing)

v1.6.8 implementation must land with the following minimum code surfaces:

1. contract skeleton generation in `create_identity_pack.py`.
2. auto-backfill in `repair_contract_backfill.py`.
3. immutability validator(s) + write-guard validator(s).
4. CI job integration into required workflow.
5. negative probe script with deterministic JSON outputs.
6. source literal lock validator wired into validate/update/scan/three-plane flows.

No stream closure claim is valid without all six.

## 5) Acceptance gates (v1.6.8)

### 5.1 Policy acceptance

1. Governance + review docs registered in stream registry.
2. Evidence allowlist updated with v1.6.8 strict doc patterns.
3. `docs_command_contract_check` and `validate_doc_evidence_persistence` pass.

### 5.2 Implementation acceptance

1. At least 5 serial positive rounds on canonical paths pass.
2. At least 5 serial negative rounds (path drift/escape probes) fail as expected.
3. `Policy PASS / Implementation PASS` allowed only when both sets are satisfied.
4. Before that state, status remains `Implementation CONDITIONAL_PASS`.

## 6) Cross-verification synthesis (roundtable + vendor + network + reference)

This stream baseline is cross-checked against external and internal references:

1. MCP security principles (`consent`, boundary control, safe tool invocation) support explicit boundary enforcement and non-implicit path trust.
2. OPA CI/CD policy-as-code model supports fail-close pipeline checks for path policy violations.
3. OpenAI strict schema guidance supports rejecting unknown fields (`additionalProperties` hardening) for machine-stable contracts.
4. Agent Skills/Codex skills structure supports deterministic directory contracts and progressive-disclosure boundaries.
5. JSON Schema object validation references support strict object envelopes for contract/registry validation.

References:

- https://modelcontextprotocol.io/specification/latest
- https://www.openpolicyagent.org/docs/latest/cicd/
- https://developers.openai.com/api/docs/guides/function-calling/#strict-mode
- https://agentskills.io/specification
- https://developers.openai.com/codex/skills/
- https://json-schema.org/understanding-json-schema/reference/object

## 7) Broadcast directive template (for downstream identity rollout)

Protocol broadcast item for v1.6.8 must include:

1. required migration objective: “all protocol-governed downsink paths must be registry-fixed”.
2. required self-check commands:
   - `identity_creator update`
   - `downsink_path_immutability validator`
   - `downsink_path_write_guard validator`
   - `downsink_path_literal_lock validator`
3. required return payload fields:
   - `identity_id`, `source_layer`, `path_registry_status`, `negative_probe_status`, `error_code`, `stale_reasons`.
4. required receipt location pattern under canonical outbox path.

## 8) Stream posture (2026-03-14 closure)

1. Policy posture: `PASS` (governance baseline frozen and registry-anchored).
2. Implementation posture: `PASS` (immutability + write-guard + literal-lock validators, CI probe matrix, serial replay evidence landed).
3. Canonical evidence root:
   - `activity/evidence/v168-path-immutability/2026-03-14/EVIDENCE_MANIFEST.v168.20260314.json`

## 9) Stream continuity alias pointers

1. `identity/protocol/mappings/contract-binding.current.yaml`
2. `identity/protocol/mappings/control-plane-invariants.current.yaml`
3. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 10) Requirement mapping motherline integration (v1.6.8)

v1.6.8 is no longer allowed to exist as a “side-chain script bundle”.
It must be integrated into the v1.6 motherline row mapping (`contract-binding.current.yaml`)
and enforced through the unified execution bus (`required_gate_bundle_runner`).

| Requirement ID | Mapping Key | Target Name | Validator | Priority | Gate Surfaces |
| --- | --- | --- | --- | --- | --- |
| ASB16-RQ-036 | asb16-rq-036 | downsink_path_immutability | scripts/validate_protocol_downsink_path_immutability.py | P0 | creator/readiness/e2e/full-scan/three-plane/ci |
| ASB16-RQ-037 | asb16-rq-037 | downsink_path_write_guard | scripts/validate_protocol_downsink_path_write_guard.py | P0 | creator/readiness/e2e/full-scan/three-plane/ci |
| ASB16-RQ-038 | asb16-rq-038 | downsink_path_literal_lock | scripts/validate_protocol_downsink_path_literal_lock.py | P0 | creator/readiness/e2e/full-scan/three-plane/ci |

Closure requirements (all must hold simultaneously):

1. All three requirement rows must exist in the active file pointed to by `contract-binding.current.yaml`.
2. `required_gate_bundle_runner` must include key + target/status mappings for all three rows.
3. `validate_control_plane_invariants` must report bundle-mapping parity with zero gap.
4. Non-`*.current.*` alias files must never become governance entrypoints (no direct version-file wiring).

## 11) Anti-forget baseline for future streams (no version hardcode)

1. Stream discovery and validation must be dynamically resolved from `stream-doc-registry.current.yaml`.
2. `stream_version` must match regex `^v\\d+\\.\\d+\\.\\d+$`.
3. Coverage validation must not hardcode a single governance doc (for example, v1.6.0 only); it must resolve all active stream docs from current aliases.
4. For any new stream (for example, v1.6.9 or v1.7.3), it is forbidden to land “side-route validators not integrated into motherline row mapping.”

### 11.1 Governance handbook binding contract (mandatory)

To prevent future stream memory drift, onboarding/readiness guidance must be machine-linked instead of human-memory-only:

1. Canonical handbook pointer must remain alias-driven:
   - `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`
2. Handbook policy must remain contract-controlled:
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`
3. Required docs lane must verify handbook token linkage (no prose-only updates):
   - `python3 scripts/docs_command_contract_check.py`
4. Any new stream that modifies governance wiring without updating the handbook linkage contract is `FAIL_REQUIRED`.
5. This rule is version-agnostic and cannot be hardcoded to a fixed stream list.

## 12) Serial verification interpretation for motherline integration

For v1.6.8 motherline integration, serial replay interpretation is split into two dimensions:

1. **Infrastructure closure dimension (must pass)**  
   - control-plane invariants  
   - required gate surface drift  
   - contract-binding reference integrity  
   - docs/evidence contract gates  
   - contract mapping coverage (`--force-required`)  
2. **Runtime readiness dimension (monitored, may remain conditional)**  
   - deep-scan target identity P0/P1 state is reported and tracked, but does not invalidate already-closed infrastructure wiring by itself.

## 13) One-stream-per-PR governance boundary (mandatory, fail-close)

This section upgrades PR discipline from convention to required enforcement and is part of the v1.6.8 closure baseline.

### 13.1 Policy objective

1. Every governance-changing PR must be anchored to exactly one `stream_version` in the active stream registry.
2. A stream anchor is complete only when both documents change in the same PR range:
   - governance doc
   - review ledger doc
3. Core protocol changes (scripts, protocol mappings, CI workflow) without a stream-doc anchor are rejected.
4. This policy must not rely on hardcoded version literals; stream discovery is always alias-driven.

### 13.2 Enforcement mechanism

Required validator:

- `scripts/validate_stream_version_pr_boundary.py`

Required CI wiring:

- `.github/workflows/_identity-required-gates.yml`

The validator resolves stream coverage from:

- `identity/protocol/mappings/stream-doc-registry.current.yaml`

and validates each range (`--base`, `--head`) against dynamic registry entries.

### 13.3 Fail-close error model

1. `IP-STREAM-PR-001`: core protocol changes exist but no stream-doc anchor exists in the same range.
2. `IP-STREAM-PR-002`: more than one stream version is changed in one PR range.
3. `IP-STREAM-PR-003`: governance/review pair is incomplete for the resolved stream.
4. `IP-STREAM-PR-004`: stream registry entrypoint is missing or structurally invalid.

Any of the above statuses is `FAIL_REQUIRED` and blocks merge.

### 13.4 Anti-forget continuity contract

1. Future streams (for example `v1.6.9`, `v1.7.3`) are automatically covered when added to the active stream registry.
2. No script or workflow is allowed to pin enforcement to a fixed stream list.
3. PR governance remains stable even when stream versions evolve, because enforcement binds to the current alias and schema, not to remembered version names.

This rule prevents false negatives where governance motherline closure is complete, while target instance business/runtime debt still exists and is tracked separately.

## 13) Host-visible receipt provenance hardening (2026-03-14)

### 13.1 Objective

1. Prevent “receipt file exists” from being treated as sufficient proof when source/state parity is not attested.
2. Bind live host-visible coverage to canonical runtime registry state.
3. Keep CI probes deterministic while preserving production default trust boundary.

### 13.2 Governance requirements

1. Live receipt validation must check both:
   - receipt payload fields, and
   - runtime state mirror (`runtime/state/host_visible_surface_registry_state.json`) parity for each channel.
2. Live receipt source must be explicitly validated through `receipt_source` allowlist.
3. Production default allowlist remains strict:
   - `runtime_dialogue`.
4. CI probe suites may extend allowlist with fixture source:
   - `ci_fixture`.
5. Session-chain runtime emission must fail-close if host-visible live receipt write/update does not reach `PASS_REQUIRED`.

### 13.3 Non-hardcode guarantee

1. Source keys and receipt path patterns are centralized in protocol infra constants.
2. Validator behavior is parameterized (`--allowed-live-receipt-sources`) and not tied to identity IDs.
3. Runtime and fixture modes share one contract surface; only source allowlist differs by lane.

## 14) Protocol-feedback index auto-closure for SSOT continuity (2026-03-14)

### 14.1 Objective

1. Remove manual index-linking debt for `runtime/protocol-feedback/evidence-index/INDEX.md`.
2. Ensure outbox SSOT remains machine-linked whenever new `FEEDBACK_BATCH_*.md` files exist.
3. Keep path and linkage governance under protocol tooling (not manual instance edits).

### 14.2 Governance rules

1. Repair tooling must resolve paths via runtime contract + pack root; no absolute user-specific literals.
2. Auto-linking may append missing markdown links only; it must not rewrite unrelated index history blocks.
3. Any remaining unlinked batch after repair attempt is fail-close (`IP-GOV-FEEDBACK-002` family).
4. Update path must invoke protocol-feedback SSOT index repair in-band before mutation execution.

### 14.3 Required tooling surfaces

1. `scripts/repair_protocol_feedback_ssot_index.py` (new)
   - contract-driven index link backfill.
2. `scripts/identity_creator.py` update path
   - mandatory in-band `--apply` invocation of the repair tool.

### 14.4 Expected result

1. Full-scan `protocol_feedback_ssot_archival` no longer depends on ad-hoc manual index maintenance.
2. Custom/runtime identities can self-heal linkage drift via protocol tools only.

## 15) Observability segregation rule for deep-scan summaries (2026-03-14)

1. Full-scan output must expose summary buckets separately:
   - `summary_runtime_active`
   - `summary_fixture_or_demo`
   - `summary_non_active_or_non_runtime`
2. Session-binding enforcement (`requested_session_binding`) is strict-required only for active runtime rows.
3. This prevents inactive/global or fixture rows from polluting active-runtime closure narratives while keeping visibility intact.
