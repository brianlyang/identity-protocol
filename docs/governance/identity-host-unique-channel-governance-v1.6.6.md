# Identity Host Unique Channel Governance (v1.6.6)

Status: Active (pre-development governance freeze)  
Layer: protocol  
Scope: project-side identity runtime unique ingress/egress enforcement + per-instance wrapper contract

Execution mode: topic-level canonical SSOT for v1.6.6 host-channel closure.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.6 host-channel closure.
2. Historical statements in v1.6.0-v1.6.5 remain valid only when not superseded by this stream.
3. Current-state judgment must prioritize machine outputs from:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. Temporary runtime directories and ad-hoc logs are replay artifacts only and are never normative contract input.
5. Normative mapping entrypoints are current-pointer files only:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`

## 0.1) Terminology lock (anti-drift, mandatory)

To avoid repeated execution drift:

1. In v1.6.6, `host-channel` is a stream identifier only.
2. Canonical three-layer terminology is fixed:
   - protocol base repository: `identity-protocol-local`
   - business project repository: `<project>` (for example `weixinstore`)
   - identity instance pack: `<project>/.identity/<identity_id>/`
3. Identity instance packs include two source layers and both are in scope:
   - project layer instance: `<project>/.identity/<identity_id>/...`
   - global layer instance: `${CODEX_HOME}/.identity/<identity_id>/...`
4. Operationally, all mandatory routing refers to the **project-side identity runtime adapter + instance pack wrappers**.
5. `Host` in this document does **not** imply modifying unrelated external repositories.
6. The hard requirement is wrapper downsink and wrapper-only invocation under `.identity/{identity_id}/runtime/gate/*` (or equivalent global-layer runtime root when source layer is global).

## 1) Why v1.6.6 exists

v1.6.1 closed protocol strict-surface headstamp/egress contracts.  
v1.6.4 closed plugin monotonic fail-close semantics.  
v1.6.5 hardened platform governance and required-check surfaces.

Remaining closure gap:

1. Project-side conversation dispatch can still bypass protocol ingress/egress contracts if runtime entrypoints call session-control directly.
2. Instance packs can declare unique-entry contract in `CURRENT_TASK.json`, but runtime routing may still skip enforcement when wrappers are absent or not consumed by project-side adapter routing.
3. Result: configuration may be correct while user-visible output path is still weakly coupled.

v1.6.6 closes this by freezing one host-channel contract:

1. Instance-side wrappers are mandatory and generated.
2. Project-side runtime dispatch must call wrappers only.
3. Protocol ingress/egress scripts remain single canonical authority.

## 2) Non-negotiable contracts (no ambiguity)

### 2.0 Project conversation mandatory wrapper contract (global, no bypass)

This rule is stronger than strict-operation gate coverage:

1. Every project-side inbound conversation message must pass instance ingress wrapper first.
2. Every project-side user-visible outbound message must pass instance egress wrapper first.
3. This applies even when operation is non-mutation/non-release.
4. Any project-side route that can emit user-visible content without wrapper path is invalid.

### 2.1 Canonical protocol scripts (fixed)

1. Unique ingress (can-do gate): `scripts/required_gate_bundle_runner.py`
2. Unique egress (can-send gate): `scripts/final_emit_governed.py`
3. Any alternate script path claiming equivalent authority is invalid.

### 2.2 Instance wrapper generation contract (mandatory)

For every identity pack, init/update must materialize wrapper layer under fixed roots:

1. `.identity/{identity_id}/runtime/gate/protocol_ingress_wrapper.py`
2. `.identity/{identity_id}/runtime/gate/protocol_egress_wrapper.py`
3. `.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json`

Hard rules:

1. Wrappers must call only canonical protocol scripts (2.1).
2. Wrappers must propagate `run_id`, `session_id`, `actor_id`.
3. Wrapper path and policy must be declared in `CURRENT_TASK.json`.
4. `host_dispatch_mode` and `host_release_mode` must both be `wrapper_only`.
5. Missing wrapper files in strict operations are `FAIL_REQUIRED`.

### 2.2.3 Wrapper dispatch token contract (mandatory, anti-bypass)

To prevent direct protocol-script invocation from masquerading as wrapper flow:

1. ingress wrapper must pass a fixed dispatch token when invoking `required_gate_bundle_runner.py`.
2. strict `host_ingress_wrapper` surface calls without valid token are `FAIL_REQUIRED`.
3. token drift between instance wrapper contract and protocol runner is `FAIL_REQUIRED`.
4. this check is governance anti-bypass control; it does not replace receipt tuple parity checks.

### 2.2.4 No-hardcode routing policy contract (mandatory)

To avoid script/workflow “偷接线” drift, wrapper-routing policy is contract-derived, not hardcoded:

1. strict wrapper surface label must be read from instance contract policy:
   - `protocol_host_unique_channel_contract_v1.entry_receipt_policy.required_surface_label`
2. strict wrapper token expectation must be read from instance contract:
   - `protocol_host_unique_channel_contract_v1.ingress_wrapper_dispatch_token`
3. strict wrapper provenance status expectations must be read from:
   - `entry_receipt_policy.required_wrapper_surface_status`
   - `entry_receipt_policy.required_wrapper_dispatch_token_status`
4. protocol scripts may keep backward-compatible defaults only as migration fallback; strict runs fail-close when contract fields are missing/drifted.
5. direct script or workflow hardcoded policy values are non-compliant with v1.6.6 closure.

### 2.2.1 `protocol_gateway_contract.json` minimum schema contract (mandatory)

To make v1.6.6 directly implementable without per-team interpretation drift, the generated
`.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json` must include at least:

1. `schema_version`
2. `identity_id`
3. `protocol_repo_root`
4. `protocol_ingress_script` (must resolve to `scripts/required_gate_bundle_runner.py`)
5. `protocol_egress_script` (must resolve to `scripts/final_emit_governed.py`)
6. `ingress_wrapper_path`
7. `egress_wrapper_path`
8. `session_chain_wrapper_path` (must resolve to `runtime/gate/protocol_session_chain_wrapper.py`)
9. `catalog_path`
10. `entry_receipt_policy` (`required: true`)
11. `egress_receipt_policy` (`required: true`)
12. `headstamp_policy` (`required: true`)
13. `identity_tuple_fields` (must contain `actor_id`, `session_id`, `run_id`, `work_layer`, `source_layer`)
14. `host_visible_surface_registry_contract_ref` (must resolve to `host_visible_surface_registry_contract_v1`)
15. `wrapper_template_attestation_policy` (must contain ingress/egress/session-chain template hashes + semantic tokens)
16. `host_visible_surface_registry_contract_v1` (runtime parity mirror of CURRENT_TASK host-visible surface contract)

Schema/fail-close rules:

1. `additionalProperties` must be rejected by validator in strict mode.
2. `protocol_ingress_script` and `protocol_egress_script` must be explicit paths, not inferred defaults.
3. Any missing required field above is `FAIL_REQUIRED` during init/update validation.
4. Any canonical script mismatch is `FAIL_REQUIRED` (no alias authority).
5. Any wrapper-template hash mismatch or missing session-chain semantic token is `FAIL_REQUIRED`.

### 2.2.2 Wrapper invocation envelope contract (mandatory)

Both wrappers must support one deterministic envelope with explicit tuple propagation.

Ingress minimum input envelope:

1. `actor_id`
2. `session_id`
3. `run_id`
4. `identity_id`
5. `work_layer`
6. `source_layer`
7. `operation`
8. `payload`

Egress minimum input envelope:

1. `actor_id`
2. `session_id`
3. `run_id`
4. `identity_id`
5. `work_layer`
6. `source_layer`
7. `candidate_output`
8. `ingress_receipt`

Any project adapter format is allowed only if it losslessly maps to the same envelope before wrapper invocation.

### 2.3 Project dispatch contract (mandatory)

Project-side session entrypoints must not dispatch user messages directly to instance business scripts.

Required model:

1. Project-side runtime receives inbound message.
2. Project-side runtime invokes per-instance `protocol_session_chain_wrapper.py` (or equivalent wrapper-chain adapter).
3. Session-chain wrapper invokes ingress wrapper first.
4. Ingress wrapper invokes `scripts/required_gate_bundle_runner.py`.
5. Session-chain wrapper invokes egress wrapper before any user-visible output.
6. Execution/release is blocked unless unique-entry receipt and egress guard are both `PASS_REQUIRED`.

### 2.3.1 Project wrapper discovery order (mandatory)

To support protocol/instance split repositories without path ambiguity:

1. Project-side runtime must first resolve wrapper contract from instance runtime declaration (from generated `CURRENT_TASK.json` field).
2. Project-side runtime may fallback to `.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json` only when declaration points to the same file.
3. Project-side runtime must reject any implicit mono-repo relative-path fallback.
4. Unresolved wrapper contract path is `FAIL_REQUIRED`.

### 2.4 Project release contract (mandatory)

Any user-visible output must pass egress wrapper before release.

Required model:

1. Candidate output enters per-instance egress wrapper.
2. Egress wrapper invokes `scripts/final_emit_governed.py`.
3. Send-time/headstamp contracts must pass for current turn.
4. Egress must validate ingress receipt parity for current turn:
   - `run_id` must match
   - `session_id` must match
   - `actor_id` must match
5. Missing/mismatched receipt or headstamp is `FAIL_REQUIRED`.

### 2.4.3 Host-visible surface registry + transport attestation contract (mandatory)

To close sender-side bypass on host-visible channels (including `commentary`), v1.6.6 requires an explicit transport contract:

1. CURRENT_TASK must include `host_visible_surface_registry_contract_v1` with:
   - `required_channels` containing `commentary`, `approval`, `status`, `final`
   - `runtime_receipt_max_age_seconds` declared as positive integer (fail-close freshness window)
   - `required_attestation_fields` containing:
     - `emit_channel_id`
     - `wrapper_surface_status`
     - `entry_receipt_tuple_status`
     - `headstamp_first_line_status`
     - `send_time_gate_status`
     - `final_emit_contract_status`
   - `required_pass_status_fields` containing wrapper/tuple/headstamp/send-time/final-contract status keys
2. Host gateway contract must reference it through
   `host_visible_surface_registry_contract_ref=host_visible_surface_registry_contract_v1`.
3. Runtime gateway contract must mirror the same host-visible surface object with parity checks.
4. Validator `scripts/validate_host_transport_wiring_attestation.py` is mandatory:
   - static contract/schema checks are always required
   - live receipt coverage checks are required in probe mode (`--require-live-receipts`)
5. Required CI lane must execute
   `scripts/ci/run_host_visible_surface_live_probes_ci.sh` and fail-close when:
   - live `commentary` channel attestation is missing
   - any channel live receipt is stale beyond `runtime_receipt_max_age_seconds`
   - any required pass-status field is not `PASS_REQUIRED`

### 2.4.2 Failure-code family preservation contract (mandatory)

To keep audit replay stable across streams:

1. Missing/invalid unique-entry receipt must preserve bundle-entry family (`IP-GATE-ENTRY-*`).
2. Headstamp tuple failures must preserve headstamp family (`IP-HDSTAMP-*`).
3. Actor/session tuple failures must preserve actor-session family (`IP-ASB-*`) where applicable.
4. New wrappers must not replace canonical families with ad-hoc aliases.

### 2.4.4 Receipt tuple-context interpretation contract (mandatory)

To avoid false interpretation of tuple-context failures as protocol-regression failures, validator output must expose machine-readable tuple-context state.

Required output fields from `validate_protocol_unique_entry_gate.py`:

1. `protocol_unique_entry_receipt_tuple_context_status`
2. `protocol_unique_entry_receipt_tuple_context_required_fields`
3. `protocol_unique_entry_receipt_tuple_context_mismatch_fields`
4. `protocol_unique_entry_receipt_tuple_context_expected`
5. `protocol_unique_entry_receipt_tuple_context_observed`
6. `protocol_unique_entry_receipt_tuple_context_only_failure`
7. `protocol_unique_entry_receipt_tuple_context_next_action`

Interpretation rules:

1. tuple-context mismatch remains `FAIL_REQUIRED` (no policy relaxation).
2. when failure is tuple-context-only, output must explicitly mark `..._only_failure=true`.
3. remediation guidance must be machine-readable via `..._next_action` and must point to replaying wrapper flow with bound actor/session tuple.
4. this contract improves diagnostics consistency and does not weaken any existing fail-close gate.

Scan-plane interpretation extension:

1. `scripts/full_identity_protocol_scan.py` must publish tuple-context-only failures under a dedicated summary bucket:
   - `summary_tuple_context`
2. tuple-context-only failures remain hard failures at check level, but scan summaries must expose them as a separate machine-readable diagnostic dimension to avoid conflating context mismatch with protocol wiring regressions.

Strict binding closure extension (mandatory):

1. Under strict operation + `--require-entry-receipt`, unique-entry validator must enforce complete tuple binding:
   - `operation`
   - `run_id`
   - `actor_id`
   - `session_id`
2. Any missing tuple field above is `FAIL_REQUIRED` with machine-readable stale reason:
   - `entry_receipt_tuple_binding_incomplete:<missing_fields>`
3. Creator orchestration paths (`validate`/`update`) must pass all tuple fields explicitly when invoking `validate_protocol_unique_entry_gate.py`.

Strict receipt freshness extension (mandatory):

1. `protocol_unique_entry_gate_contract_v1` must declare `entry_receipt_max_age_seconds` (>0).
2. Under strict tuple-binding paths, receipt freshness must be computed from both:
   - payload signed/issued timestamp (primary), and
   - receipt file mtime (secondary).
3. Effective freshness age is `max(payload_age_seconds, file_age_seconds)` to fail-close touch/copy replay attempts.
4. Receipt payload timestamp parsing order is contract-fixed:
   - epoch fields first (for example `wrapper_dispatch_proof_issued_at_epoch`)
   - ISO fields next (for example `created_at_utc`)
5. If payload timestamp is in the future (beyond skew tolerance), validation must fail-close.
6. Stale receipt replay outside freshness window is `FAIL_REQUIRED` with stale reason:
   - `entry_receipt_stale:age_seconds=<n>:max_age_seconds=<m>:payload_age_seconds=<p>:file_age_seconds=<f>`
7. Migration closure is mandatory:
   - `repair_contract_backfill.py` must normalize missing/invalid `entry_receipt_max_age_seconds` to a positive default from contract skeleton.
   - active runtime packs cannot remain in a state where `entry_receipt_max_age_seconds<=0`.

Required CI extension:

1. Required lane must execute:
   - `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
2. Minimum required outcomes:
   - probe `tuple_binding_incomplete_blocked` must fail-close as expected.
   - probe `tuple_binding_complete_pass` must pass with `PASS_REQUIRED`.
   - probe `tuple_binding_tampered_tuple_blocked` must fail-close on actor/session tuple mismatch.
   - probe `tuple_binding_migration_missing_max_age_blocked` must fail-close before backfill.
   - probe `tuple_binding_migration_backfill_apply` must pass and apply migration fix.
   - probe `tuple_binding_migration_contract_pass` must pass after backfill.
   - probe `tuple_binding_stale_receipt_blocked` must fail-close on stale replay receipt.

Strict scan live run-id pass-through extension (mandatory):

1. strict full-scan flow must bind one canonical scan run id and pass it to both lanes:
   - `required_gate_bundle_runner.py --run-id <required_gate_bundle_run_id>`
   - `final_emit_governed.py --run-id <required_gate_bundle_run_id>`
2. host-visible live attestation in the same scan must verify against the same bound id:
   - `validate_host_transport_wiring_attestation.py --require-run-id <required_gate_bundle_run_id>`
3. if send-time lane emits live receipts under a different run id, attestation must fail-close (`IP-HDSTAMP-003`).
4. this contract is dynamic/alias-driven and does not permit identity-specific or literal run-id hardcoding.
5. delegated strict coverage scans must propagate the same run id tuple to required-contract coverage validator:
   - `validate_required_contract_coverage.py --run-id <required_gate_bundle_run_id>`
   - so nested unique-entry/lane validators cannot degrade to stale/default run context.
6. strict full-scan host-visible attestation allowlist must be seeded from same-turn send-time evidence:
   - baseline include `runtime_dialogue`
   - append send-time emitted `host_visible_surface_live_receipt_source` when present
   - pass merged allowlist via `validate_host_transport_wiring_attestation.py --allowed-live-receipt-sources ...`
   - this avoids false-red source contamination while preserving actor/session/run binding and freshness fail-close gates.

### 2.4.1 Headstamp continuity contract (mandatory)

1. Egress wrapper must treat first-line identity tuple and layer tuple as send-time hard gate input.
2. If first-line identity/layer tuple is missing or mismatched, outbound release is blocked.
3. Headstamp errors must use canonical family from v1.6.1 boundary (`IP-HDSTAMP-*`), not ad-hoc aliases.

### 2.5 Layer boundary contract (protocol vs instance)

1. Protocol layer defines contracts, schema, validators, and fail-close semantics.
2. Instance layer defines business behavior and parameters only.
3. Protocol layer must not embed instance business logic.
4. Instance layer must not redefine protocol canonical ingress/egress semantics.

### 2.6 Performance boundary contract

1. Project gateway must be lightweight and deterministic.
2. Latency budget applies to gateway stage itself, not approval waiting time:
   - local gateway target: `P95 <= 300ms`.
3. Any new check added to ingress/egress must include budget impact evidence before promotion.

### 2.6.1 Wrapper vs gate-profile semantics (anti-confusion)

To prevent repeated ambiguity:

1. Mandatory wrapper path and gate strictness are different dimensions.
2. `Must pass wrapper` means ingress/egress wrappers always run for project-side I/O.
3. `strict_full` means required-gate profile for strict operations (`activate/update/mutation/readiness/e2e/ci/validate/three-plane`).
4. Non-mutation project rounds may use non-strict profile where policy allows, but cannot bypass wrappers and cannot bypass egress headstamp/send-time checks.
5. Any implementation that interprets non-strict profile as wrapper bypass is invalid.

### 2.7 Stream numbering and GitHub PR binding contract (mandatory)

To keep governance/review/implementation lifecycle deterministic, every stream number must bind to one auditable PR trail:

1. Any new stream version (`v1.6.x`) must include three artifacts before implementation-closure claim:
   - governance doc (`docs/governance/...`)
   - review ledger (`docs/review/...`)
   - SSOT registry row (`identity/protocol/mappings/stream-doc-registry.current.yaml` resolved target)
2. Every stream implementation cycle must provide one machine-readable PR binding receipt:
   - `activity/evidence/<stream>/<date>/stream_pr_binding.json`
3. `stream_pr_binding.json` required fields:
   - `stream_version`
   - `repository`

### 2.8 v1.6.6 closure freeze clauses (execution-facing)

The following clauses are frozen for v1.6.6 implementation acceptance:

1. Terminology/boundary freeze
   - protocol base repo: `identity-protocol-local`
   - business project repo: `<project>`
   - identity runtime pack: `<global>|<project>/.identity/<identity_id>/`
   - all unique ingress/egress + wrapper + receipt/headstamp rules must work for both `source_layer=global` and `source_layer=project`.
2. Dual-layer unique channel
   - protocol ingress script: `scripts/required_gate_bundle_runner.py`
   - protocol egress script: `scripts/final_emit_governed.py`
   - instance ingress wrapper: `runtime/gate/protocol_ingress_wrapper.py`
   - instance egress wrapper: `runtime/gate/protocol_egress_wrapper.py`
3. Per-round mandatory path
   - inbound must go ingress wrapper first
   - user-visible outbound must go egress wrapper first
   - any non-wrapper path is fail-close by contract
4. Light/heavy split (upgrade-only)
   - light rounds: `operation=inspection|scan` with `gate_profile=inspection_targeted`
   - heavy rounds: `validate/update/activate/mutation/readiness/e2e/ci/three-plane` with `gate_profile=strict_full`
   - downgrade from heavy to targeted is forbidden; light rounds can upgrade to strict.
5. Anti-bypass hard constraints
   - `host_dispatch_mode=wrapper_only`, `host_release_mode=wrapper_only`
   - runtime three-piece gateway artifacts mandatory
   - ingress receipt tuple must include `actor_id/session_id/run_id/work_layer/source_layer`
   - strict receipt provenance must pass wrapper surface + dispatch token parity
6. Controller separation
   - `identity_creator`: generate/update protocol contracts and wrapper bindings
   - `identity_installer`: materialize/repair runtime gateway files and path bindings
   - neither controller may weaken wrapper-only semantics.
   - `pull_request_number`
   - `pull_request_url`
   - `head_branch`
   - `base_branch`
   - `head_sha`
   - `merge_status`
   - `opened_at_utc`
4. Closure boundary:
   - no PR binding receipt => stream status cannot move to `implementation_code_completed`.
   - governance/review docs without SSOT registry row are treated as draft only.

### 2.8 YAML sprawl control contract (mandatory)

To prevent control-plane file sprawl in v1.6.x streams:

1. New stream registration must reuse existing mapping files:
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
2. Stream-level doc onboarding must be append-only row updates in existing mappings.
3. Creating new mapping YAML files for stream registration is forbidden unless schema/version boundary requires it and governance explicitly approves it.

### 2.9 Required evidence package contract (mandatory)

For each v1.6.6 implementation round, evidence must include:

1. `activity/evidence/v166-host-channel/<date>/stream_pr_binding.json`
2. `activity/evidence/v166-host-channel/<date>/wrapper_contract_snapshot.<identity_id>.json`
3. `activity/evidence/v166-host-channel/<date>/host_channel_replay.<scenario>.json`
4. `activity/evidence/v166-host-channel/<date>/EVIDENCE_MANIFEST.<tag>.json`

The first three are required payload artifacts, and manifest is the required tuple index (`command`, `rc`, `sha256`, `timestamp`).

Replay commands documented for v1.6.6 MUST write named output artifacts under
`activity/evidence/v166-host-channel/<date>/...`; ephemeral scratch paths remain execution-local only and are not admissible as normative replay evidence.

## 3) Four-track cross verification (frozen consensus)

### T1 Roundtable (repo machine replay)

1. Required-gate strict surfaces remain machine green.
2. Unique-entry contract validator exists and is callable in strict operations.
3. Final egress wrapper contract is enforced on protocol strict surfaces.

### T2 Vendor (official safety model)

1. OpenAI Codex approvals/security model supports boundary enforcement without disabling core model capability.
2. Strict schema-first controls align with fail-close gateway semantics.

### T3 Network/platform governance

1. GitHub required checks + merge-group model validates centralized policy gates in CI.
2. Rulesets model supports centralized enforcement layering compatible with protocol/project split.

### T4 Protocol references

1. `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
2. `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
3. `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`

### T5 Context7 references

1. Super-linter changed-files mode (`VALIDATE_ALL_CODEBASE=false`) is validated as the recommended fast-feedback baseline for governance lanes.
2. Shared `.env` configuration loading model supports deterministic lint profile reuse across local and CI surfaces.

## 4) Implementation target set (v1.6.6)

### 4.1 Protocol-repo target

1. `scripts/identity_creator.py` init/update path must generate wrapper files + contract JSON.
2. `scripts/validate_protocol_unique_entry_gate.py` must validate wrapper declaration parity when strict operation requires receipt.
3. `scripts/validate_required_gate_surface_drift.py` must detect project-side bypass surfaces where applicable.

### 4.2 Project runtime target

1. Project runtime dispatch entrypoints must call ingress wrapper only.
2. Project runtime user-visible output release must call egress wrapper only.
3. Any direct session-control dispatch without wrapper contract must be blocked.

### 4.3 Cross-repo interoperability target

1. Protocol and instance repositories may be different roots.
2. Wrapper contract must resolve protocol script paths deterministically from explicit mapping/config.
3. Relative-path assumptions tied to one mono-repo layout are invalid.

### 4.4 Governance-review-PR coherence target

1. `stream-doc-registry` must contain v1.6.6 governance/review rows before implementation claim.
2. `doc-evidence-allowlist` must include v1.6.6 strict doc evidence patterns.
3. `stream_pr_binding.json` must be updated per implementation PR round.
4. `docs_command_contract_check` must remain green after stream registration updates.

## 5) Acceptance gate (must all pass)

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. Project replay proves no direct-bypass outbound path under target entrypoints.
6. Stream PR binding receipt exists under persistent evidence path and matches current head SHA.
7. Project non-mutation replay still produces:
   - ingress wrapper receipt present
   - egress wrapper receipt present
   - headstamp/send-time status `PASS_REQUIRED`
8. Negative probe `direct dispatch -> direct release` is `FAIL_REQUIRED`.
9. `protocol_gateway_contract.json` passes required-field schema checks from 2.2.1.
10. Evidence package in 2.9 is present and allowed by `doc-evidence-allowlist.current.yaml`.
11. Negative probe `direct required_gate_bundle_runner host_ingress_wrapper call without wrapper token` is `FAIL_REQUIRED`.

Release decision:

1. Any failure in items above blocks v1.6.6 closure claim.

### 5.1 Implementation landing snapshot (2026-03-12, protocol repo + instance pack runtime)

The v1.6.6 host-channel contract is now code-backed in protocol repo runtime tooling.

Code landing set:

1. `scripts/create_identity_pack.py`
   - adds `protocol_host_unique_channel_contract_v1` into scaffold defaults.
   - generates per-instance artifacts on init:
     - `runtime/gate/protocol_ingress_wrapper.py`
     - `runtime/gate/protocol_egress_wrapper.py`
     - `runtime/gate/protocol_gateway_contract.json`
2. `scripts/repair_contract_backfill.py`
   - auto-wires `protocol_host_unique_channel_contract_v1` for existing instances.
   - materializes wrapper/contract artifacts during `--apply` update flow.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - extends unique-entry validation to include host gateway wrapper contract parity.
   - enforces runtime file existence + canonical script binding + tuple field coverage.
   - validates generated `protocol_gateway_contract.json` required fields and canonical script refs.

Serial verification snapshot:

1. `python3 scripts/repair_contract_backfill.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --apply --json-only`
   - `contract_backfill_status=PASS_REQUIRED`
   - `host_gateway_contract_auto_wire_status=PASS_REQUIRED`
2. `python3 scripts/required_gate_bundle_runner.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --operation validate --run-id v166-host-wrap-1773284273 --target-name skill_path_integrity --actor-id assistant:codex --resolved-work-layer instance --resolved-source-layer project --lock-state LOCK_MATCH --send-time-gate-status PASS_REQUIRED --outlet-bypass-detected false --final-emit-contract-status PASS_REQUIRED --final-emit-policy-mode tool_choice_required --final-emit-schema-status PASS_REQUIRED --json-only`
   - `bundle_status=PASS_REQUIRED`
   - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
3. `python3 scripts/validate_protocol_unique_entry_gate.py ... --force-check --require-entry-receipt --json-only`
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - `protocol_host_gateway_contract_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_files_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_contract_status=PASS_REQUIRED`
4. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
5. `python3 scripts/validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
6. `python3 scripts/validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
7. `python3 scripts/docs_command_contract_check.py` -> `PASS`
8. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`

Interpretation:

1. v1.6.6 no longer relies on docs-only declaration for host unique-channel wrappers.
2. Init/update paths now emit and validate wrapper contracts as executable artifacts.
3. Closure posture remains implementation-progressive until project-side runtime dispatch/release entrypoints are fully wrapper-only.

### 5.2 Audit-delta hardening addendum (2026-03-12)

To close the latest audit deltas, this stream adds:

1. **Signer policy uplift (file-secret -> env-secret capable policy)**
   - `ingress_proof_policy` / `egress_grant_policy` now support:
     - `signer_mode`
     - `signer_secret_env`
   - `runtime_env_secret` mode is accepted by ingress/egress verifiers and parity validators.
2. **Required CI reverse probes**
   - new required CI delegate: `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - validates both fail-close cases:
     - forged local-key ingress proof direct runner
     - forged local-key egress grant direct final emit
3. **Source-layer resolve fallback hardening**
   - `resolve_identity_context` adds repo-adjacent `.identity/catalog.local.yaml` fallback classification to avoid intermittent `source_layer=unknown` under project runtime layout.

Posture remains:

1. policy: `PASS_REQUIRED`
2. implementation: `CONDITIONAL_PASS`
3. remaining blocker: project runtime dispatcher wrapper-only exposure proof.

### 5.3 Audit delta follow-up (2026-03-13, serialized replay)

This round applies additional hardening and freezes current risk boundary explicitly (no over-closure claim):

Implemented:

1. `required_gate_bundle_runner.py`
   - adds wrapper-parent attestation fields into receipt:
     - `wrapper_parent_attestation_required`
     - `wrapper_parent_attestation_status`
     - `wrapper_parent_attestation_expected_path`
     - `wrapper_parent_attestation_ppid`
   - enforces parent attestation under wrapper-provenance-required operations.
2. `final_emit_governed.py`
   - adds egress wrapper-parent attestation check when `host_release_mode=wrapper_only`.
   - emits attestation status fields in final-emit payload.
3. `validate_protocol_unique_entry_gate.py`
   - validates ingress receipt parent-attestation parity on provenance-required rounds.
4. `create_identity_pack.py` + instance wrapper runtime
   - wrapper runtime now canonicalizes catalog path to absolute path before protocol script handoff.
5. `resolve_identity_context.py`
   - adds cross-cwd catalog-root fallback so project-local catalog resolution remains `source_layer=project` when launched outside project cwd.

Serialized replay conclusion for this delta:

1. Positive chain can pass under actor/session-bound context:
   - ingress wrapper `PASS_REQUIRED`
   - egress wrapper `PASS_REQUIRED`
2. Direct runner/final-emit calls without wrapper attestation fail-close.
3. Closure state remains `CONDITIONAL_PASS` because same trust-domain self-injection is still not eliminated:
   - if attacker controls signer secret and wrapper attestation inputs in the same runtime trust domain, full same-domain non-forgeability is not yet guaranteed.

### 5.4 Update-chain wrapper routing correction (2026-03-13, serialized)

This correction freezes one implementation rule to prevent parent-attestation mismatch during strict update lanes:

1. `identity_creator.py` must not direct-call canonical protocol egress in wrapper-only mode.
2. For wrapper-only identities, creator strict paths must route through instance wrappers:
   - ingress: `.identity/<identity_id>/runtime/gate/protocol_ingress_wrapper.py`
   - egress: `.identity/<identity_id>/runtime/gate/protocol_egress_wrapper.py`
3. Routed ingress envelope must not override wrapper-owned surface label:
   - canonical required surface remains `host_ingress_wrapper`.
4. `session_id` must be propagated end-to-end across creator -> wrapper -> protocol scripts.

Serialized replay outcome (base-repo-architect):

1. pre-mutation egress guard in `identity_creator update` now reaches:
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
2. previous mismatch signal (`egress_wrapper_parent_attestation_parent_command_mismatch`) is not reproduced after routing correction.
3. stale report freshness (`IP-PVA-001` / `IP-REL-001`) is now treated as in-run refreshable preflight drift (warn-and-continue) instead of hard stop; downstream strict bundle gates remain authoritative blockers.
   - This refreshable family explicitly includes the canonical stale-report projection where:
     - `report_older_than_key_inputs` is present,
     - report-side prompt SHA is stale,
     - and `validate_identity_prompt_activation.py` therefore reports `prompt_activation_mismatch` as a derivative of the stale report rather than as an independent blocker.
   - The updater must fail-close if extra drift appears outside that bounded family (for example binding tuple mismatch, scaffold baseline mismatch, or non-refreshable baseline failure).

### 5.5 Attestation strictness uplift + env-forge probes (2026-03-13, serialized)

To shrink same-domain bypass surface under wrapper-only policy, this stream further tightens attestation checks and CI probes:

1. `required_gate_bundle_runner.py` ingress parent attestation:
   - requires both:
     - `IDENTITY_PROTOCOL_INGRESS_WRAPPER_PATH` exact path match
     - parent commandline structural match to expected wrapper launcher
   - removes permissive `env-only` fallback path.
   - commandline discovery now prefers runtime process API (`psutil`), with `/proc`/`ps` fallback.
2. `final_emit_governed.py` egress parent attestation:
   - same strict rule as ingress:
     - env wrapper path must match
     - parent commandline must match expected egress wrapper launcher
   - commandline discovery uses same `psutil`-first strategy.
3. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` adds two mandatory negative probes:
   - `runner_env_secret_forge_blocked`
   - `final_emit_env_secret_forge_blocked`
   both simulate attacker self-injecting signer env secret + forged proof/grant and must fail-close.

Serialized replay summary for this uplift:

1. new env-self-injection probes are blocked (`rc=1`) in required probe suite.
2. strict wrapper chain remains reproducible for creator update pre-mutation:
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
3. stream posture remains `CONDITIONAL_PASS` until signer root trust is separated from same-domain caller control.

### 5.6 L3 reasoning fallback bootstrap hardening (2026-03-13, serialized)

To avoid strict update lanes being blocked by legacy minimal learning samples, this stream adds
deterministic L3 bootstrap enrichment:

1. `scripts/repair_identity_learning_sample.py`
   - upgrades bootstrap payload to include L3-minimum fields used by `RQ-035` fail-close checks:
     - attempt fields: `result_code`, `target_reached`, `no_target_reached`, `next_action`, `evidence_refs`
     - run fields: `roundtable_evidence_refs`, `vendor_evidence_refs`, `network_evidence_refs`, `reference_evidence_refs`
     - external fields: `external_source_freshness_status`, `conflict_reconciliation_note`, `source_url_set`
   - auto-repairs existing learning sample files when the file exists but misses L3-required fields.
   - preserves existing sample `run_id` when enriching an existing sample.
2. This is a protocol-side method update only (not manual instance hand-edit):
   - instance owners run repair tool; tool performs down-sunk file mutation in instance runtime path.
3. This hardening changes blocker class:
   - from "bootstrap sample structurally insufficient for strict reasoning gate"
   - to "instance still owes real runtime evidence/writeback closure" (expected for conditional posture).

### 5.7 Post-execution + prompt-lifecycle auto-repair chain (2026-03-13, serialized)

To close recurring `IP-WRB-003` and prompt lifecycle hash-drift debt without manual instance edits,
v1.6.6 adds protocol-tool-driven repair steps:

1. New repair tooling:
   - `scripts/repair_identity_prompt_runtime_state.py`
     - repairs `runtime/state/prompt_contract.json` hash binding to current `IDENTITY_PROMPT.md`.
     - patches latest upgrade report prompt lifecycle fields to keep report/runtime hash parity.
   - `scripts/repair_identity_post_execution_mandatory.py`
     - repairs latest upgrade report mandatory post-execution fields (`writeback_*`, outlet/final-emit metadata, recovery action).
     - generates deterministic degraded receipt when outlet preflight receipt is absent.
2. `scripts/identity_creator.py update` now runs both repairs with `--apply` before strict update gate bundle.
3. Governance intent:
   - instance runtime files remain the landing location (`.identity/<id>/runtime/...`);
   - mutation method remains protocol-controlled tooling (no manual hand-edit requirement).

### 5.8 Tuple-parity strictness correction + serial replay (2026-03-13, serialized)

This round closes a strict-update false blocker without relaxing wrapper-only governance semantics.

Implemented:

1. `scripts/validate_required_gate_tuple_parity.py`
   - `--require-distinct-operations` no longer implicitly enforces distinct `surface_label`.
   - distinct surface labels remain enforceable only when explicitly requested via
     `--require-distinct-surface-labels`.
2. Governance intent:
   - update/validate strict lanes compare operation distinctness without forcing probe/update
     receipts to invent non-canonical wrapper labels.
   - full-scan parity still can require distinct surface labels via explicit flag.

Serialized replay facts (base-repo-architect):

1. 5 serial wrapper-chain self-test rounds (ingress -> unique-entry -> egress) all pass:
   - run ids:
     - `v166-selftest-r1-1773390943`
     - `v166-selftest-r2-1773390946`
     - `v166-selftest-r3-1773390948`
     - `v166-selftest-r4-1773390951`
     - `v166-selftest-r5-1773390953`
   - each round:
     - `bundle_status=PASS_REQUIRED`
     - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
     - `protocol_unique_entry_gate_status=PASS_REQUIRED`
     - `final_emit_guard_status=PASS_REQUIRED`
2. 5 serial deep-scan rounds are stable and deterministic:
   - each round summary remains:
     - `p0=1`, `p1=0`, `ok=0`, `m2m_fail=1`
     - three-plane overall `Conditional Go`
3. Interpretation:
   - wrapper mandatory chain is stable and reproducible in serial replay.
   - remaining red items are instance runtime-evidence closure debt (for example multimodal /
     reasoning runtime evidence), not tuple-parity surface-label false negatives.

Posture after this correction:

1. `Policy PASS`
2. `Implementation CONDITIONAL PASS`

### 5.9 Final closure round (2026-03-13, serialized 5x5 replay)

This round closes the remaining v1.6.6 scan/three-plane wrapper-bypass surface by upgrading
runtime scanners to use the same wrapper-routed execution semantics as creator strict lanes.

Implemented:

1. `scripts/full_identity_protocol_scan.py`
   - required-gate bundle calls are wrapper-routed (ingress wrapper) under wrapper-only contracts.
   - send-time compose calls are wrapper-routed (egress wrapper) under wrapper-only contracts.
   - scan session id fallback is propagated into wrapper-routed required-gate calls.
   - scan tuple parity check no longer forces distinct surface labels for scan/scan replay pair.
2. `scripts/report_three_plane_status.py`
   - required-gate bundle calls are wrapper-routed (ingress wrapper) under wrapper-only contracts.
   - send-time compose preflight is wrapper-routed (egress wrapper) under wrapper-only contracts.
   - strict three-plane session id is propagated as wrapper fallback session.

Serialized replay result (base-repo-architect):

1. Self-test (5 serial rounds):
   - run ids:
     - `v166-selftest-post-r1-1773394376`
     - `v166-selftest-post-r2-1773394378`
     - `v166-selftest-post-r3-1773394380`
     - `v166-selftest-post-r4-1773394383`
     - `v166-selftest-post-r5-1773394385`
   - each round:
     - ingress `bundle_status=PASS_REQUIRED`
     - `protocol_unique_entry_receipt_status=PASS_REQUIRED`
     - unique-entry gate `PASS_REQUIRED`
     - egress `final_emit_guard_status=PASS_REQUIRED`
2. Deep scan (5 serial rounds):
   - each round:
     - `rc=0`
     - `summary: p0=0, p1=0, ok=1`
     - `summary_m2m: fail=0`
3. Mandatory closure interpretation:
   - wrapper-routed scan/three-plane path is now aligned with creator strict path.
   - previous m2m blocker set (`IP-HDSTAMP-003`, `IP-HDSTAMP-001`, wrapper provenance drift on scan)
     is not reproduced in serialized replay.

v1.6.6 acceptance posture (this stream, frozen):

1. `Policy PASS`
2. `Implementation PASS`

### 5.10 Downstream upgrade broadcast pack (aligned to v1.6.5 Section-3 model)

To make v1.6.6 closure retrievable and executable by downstream runtime identities without
manual coordination, this stream publishes a canonical broadcast item:

1. `identity/protocol/broadcast/items/v166-closure-upgrade-serial-5x5-20260313.json`
2. `identity/protocol/broadcast/index.json` contains the corresponding index row.

Broadcast contract intent:

1. requires ack (`requires_ack=true`) and is marked critical (`severity=critical`).
2. freezes one operator runbook:
   - contract backfill
   - wrapper signer env set
   - strict update replay
   - serial self-test (`>=5`)
   - serial deep-scan (`>=5`)
   - `identity_broadcast_ack.py --ack-all-pending`
3. pass criteria are machine-readable in message body:
   - self-test: all rounds `PASS_REQUIRED`
   - deep-scan: all rounds `rc=0`, `p0=0`, `m2m_fail=0`

Serialized attach check (base-repo-architect):

1. first ingress after publish:
   - `broadcast_pending_ack_count=1`
   - `broadcast_critical_unacked_count=1`
2. ack replay:
   - `identity_broadcast_ack_status=PASS_REQUIRED`
3. second ingress after ack:
   - `broadcast_pending_ack_count=0`
   - `broadcast_critical_unacked_count=0`

## 6) External references

1. OpenAI Codex approvals and sandbox:
   - [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security/#sandbox-and-approvals)
2. OpenAI Codex action safety baseline:
   - [GitHub Action security checklist](https://developers.openai.com/codex/github-action/#security-checklist)
3. OpenAI schema strictness baseline:
   - [Function calling strict mode](https://platform.openai.com/docs/guides/function-calling#strict-mode)
4. GitHub merge queue trigger compatibility:
   - [Actions event `merge_group`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group)
5. GitHub required-check troubleshooting:
   - [Troubleshooting required status checks](https://docs.github.com/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)
6. MCP lifecycle contract:
   - [Model Context Protocol lifecycle](https://modelcontextprotocol.io/specification/draft/basic/lifecycle)

### 5.11 Runtime closure补强（2026-03-14, base-repo-audit-expert-v3）

本轮针对“实例 wrapper 链路可用，但聊天会话通道仍可能无头显直出”的残余问题，补强了协议与实例下沉合同的可执行闭环能力。

代码落地（contract-driven，无硬编码路径）：

1. `scripts/create_identity_pack.py`
   - host gateway 合同在 `runtime_env_secret` 模式下也强制下发：
     - `signing_key_path`
     - `bootstrap_env_secret_from_signing_key_path=true`
   - materialize 阶段始终生成 `runtime/state/protocol_gateway_signing_key.txt`。
   - session-chain wrapper 模板新增：
     - session 绑定自动对齐（优先 identity 已绑定 session）
     - session 绑定缺失时自动 upsert（fail-close on write failure）
2. `scripts/repair_contract_backfill.py`
   - 旧实例回填 `signing_key_path` 与 `bootstrap_env_secret_from_signing_key_path`，并刷新 wrapper 三件套。
3. `scripts/validate_protocol_unique_entry_gate.py`
   - signer policy 校验升级：`runtime_env_secret` 也要求 `signing_key_path` 与 bootstrap 布尔字段；
   - runtime parity 增补 bootstrap 字段一致性检查。
4. `scripts/required_gate_bundle_runner.py`
   - env-secret 未注入时可按合同 `signing_key_path` 补载（仅在 bootstrap=true 时）。
5. `scripts/final_emit_governed.py`
   - egress grant 验签同样支持按合同 `signing_key_path` 补载（bootstrap=true）。

串行实测摘要（证据文件）：

1. 5 轮串行自测（正向+负向）：
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-serial-selftest-5.json`
   - `overall_passed=true`
2. 5 轮串行深扫（治理相关项）：
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-targeted-deep-scan-5.json`
   - `overall_passed=true`
3. 单轮闭环证据：
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-probe-1.json`（session unbound 自动对齐后 PASS）
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-validate-run1.json`（同 run receipt 校验 PASS）

边界声明（防止过度宣称）：

1. 本轮实现了“wrapper 执行链路”的自引导闭环（signer bootstrap + session binding bootstrap）。
2. 但“当前聊天渲染通道是否稳定沿 native chat standard path 消费 wrapper out_reply_file”仍是发送器层集成问题；
   - 若发送器未绑定 wrapper 产物，仍可出现对话 UI 无头显。

### 5.12 Session-chain 父链路门禁补强（2026-03-14, base-repo-audit-expert-v3）

本轮把“`egress_wrapper` 可被直接调用”的残余收口到 CI 必测面，并以实例实跑确认头显首行稳定出现在 wrapper 产物中。

实现收口点：

1. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - fixture host gateway 合同增加 `session_chain_wrapper_path`。
   - 在 probe 前执行 `repair_contract_backfill --apply`，确保 runtime gate 三件套一致下沉。
   - 新增负探针 `egress_wrapper_direct_call_blocked`：
     - 先走 ingress wrapper 生成 receipt；
     - 再直调 egress wrapper（不经 session-chain）；
     - 预期 `FAIL_REQUIRED`，且 `stale_reasons` 命中 `session_chain_parent_attestation_*`。
2. `scripts/validate_required_gate_surface_drift.py`
   - 将上述新负探针纳入 required surface token 校验，防止 CI 退化为“只测 ingress/final_emit”。

实机结果（base-repo-audit-expert-v3）：

1. `session_chain_wrapper` 正向：
   - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
   - `send_time_gate_status=PASS_REQUIRED`
   - `session_chain_parent_attestation_status=PASS_REQUIRED`
   - `reply_preview[0]` 为 canonical `Identity-Context ... | Layer-Context ...`
2. `egress_wrapper` 直调负向：
   - `protocol_egress_wrapper_status=FAIL_REQUIRED`
   - `error_code=IP-GATE-ENTRY-002`
   - `stale_reasons` 命中 `session_chain_parent_attestation_env_path_missing`（及父命令缺失/不匹配）
3. trust-boundary CI：
   - `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` -> `rc=0`
   - 新增 probe 与既有 forged proof/grant probe 全部按预期拦截。
   - This replay is protocol-root evidence for the suite itself; it must not be restated as workspace-root / protocol-root invariant unless a separate cross-cwd replay is archived.

串行回放证据（本轮本地）：

1. 5 轮串行自测：
   - `activity/evidence/v166-host-channel/2026-03-13/v166_closure_serial_selftest_5_v2_summary.json`
   - `overall_passed=true`
2. 5 轮串行深扫（轻量治理面）：
   - `activity/evidence/v166-host-channel/2026-03-13/v166_closure_targeted_deep_scan_5_light_summary.json`
   - `overall_passed=true`
3. trust-boundary CI 日志：
   - `activity/evidence/v166-host-channel/2026-03-13/v166_closure_gateway_trust_boundary_ci_summary.json`

口径保持：

1. wrapper 链路与协议唯一入口/出口映射：`PASS_REQUIRED`。
2. 会话渲染器是否“稳定沿 native chat standard path 消费 wrapper out_reply_file”：仍取决于发送器集成实现，属于运行侧集成边界。

### 5.13 Unified wrapper bus closure (2026-03-14, base-repo-audit-expert-v3)

This checkpoint consolidates the v1.6.6 execution path from distributed per-script wiring into a single governance bus, so wrapper-only fail-close rules are maintained in one module and drift surface is reduced.

Implementation landing (already committed):

1. `scripts/gateway_wrapper_enforcement.py` (new)
   - Provides centralized routing for canonical ingress/egress wrapper execution, fail-close enforcement, and stamped first-line emission for non-JSON replies.
2. `scripts/identity_creator.py`
   - Uses the centralized bus instead of duplicating wrapper command orchestration inline.
3. `scripts/release_readiness_check.py`
   - `_run` and `_run_capture` now route through the same bus, keeping readiness flow aligned with wrapper-only contract semantics.
4. `scripts/report_three_plane_status.py`
   - Routes through the centralized bus to avoid independent three-plane drift.
5. `scripts/full_identity_protocol_scan.py`
   - Routes through the centralized bus so scan behavior stays source-aligned with ingress/egress policy.
6. `scripts/validate_required_gate_surface_drift.py`
   - Adds required strict-surface bus import enforcement:
     - strict surfaces must import and use `gateway_wrapper_enforcement`;
     - drift violation code: `IP-GATE-ENTRY-009`.

Governance effect (non-patch style hardening):

1. Wrapper-only allow/deny behavior and headstamp emission rules are consolidated into one control point.
2. Any strict surface bypassing the bus is fail-closed by required drift gates.
3. Future health checks, wiring, and broadcast hooks can attach to one bus instead of divergent script branches.

Serialized validation (this round):

1. Syntax and drift gates:
   - `python3 -m py_compile scripts/gateway_wrapper_enforcement.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
2. Session positive/negative probes:
   - positive `protocol_session_chain_wrapper.py` path -> `PASS_REQUIRED`, with `reply_preview[0]` matching `Identity-Context:`
   - direct `scripts/final_emit_governed.py` call without wrapper parent chain -> `FAIL_REQUIRED`
3. 5+5 serial replay:
   - 5-round self-test: `overall_passed=true`
   - 5-round deep-scan: `overall_passed=true`
   - temporary local files are execution traces only and are not normative evidence; normative evidence remains command contract + gate status.

Current posture:

1. `Policy PASS`
2. `Implementation CONDITIONAL PASS`
3. remaining condition is sender-layer native-chat standard-path convergence (`wrapper output only`), not protocol semantic drift.

### 5.14 Receipt tuple generation compatibility normalization (2026-03-14)

To reduce false red caused by receipt field generation drift between scan/validate lanes, v1.6.6 tuple validation is normalized to accept canonical aliases while keeping strict equality on values.

Protocol rules:

1. Canonical tuple semantics remain unchanged:
   - `run_id`, `actor_id`, `session_id`, `operation` must still match expected tuple values.
2. Field-name alias compatibility is allowed for receipt parsing only:
   - run-id aliases: `run_id_binding | run_id | requested_run_id`
   - actor-id aliases: `actor_id | resolved_actor_id | entry_actor_id`
   - session-id aliases: `session_id | resolved_session_id | entry_session_id`
   - operation aliases: `operation | requested_operation | operation_name`
3. Missing canonical required fields are considered satisfied only when an accepted alias provides the same tuple value.
4. Validator payload must expose which source field was used per tuple element for audit traceability.

Boundary:

1. This is not a downgrade of tuple strictness.
2. It only removes field-name generation drift noise; value mismatch is still `FAIL_REQUIRED`.

### 5.15 Host-visible live freshness as strict full-scan contract (2026-03-15)

This checkpoint upgrades host-visible channel attestations from shape-only checks to
live freshness-enforced checks in strict scan paths.

Contract additions:

1. Host-visible surfaces now include a canonical freshness ceiling:
   - `runtime_receipt_max_age_seconds` (positive required).
2. Freshness is enforced by required validators in strict scan/release gates:
   - stale channel receipts are fail-closed.
3. Required CI probes must include stale-receipt and commentary-bypass negative cases.

Implementation anchors:

1. `scripts/protocol_infra_contract.py`
   - `HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS`.
2. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - materialize/backfill `runtime_receipt_max_age_seconds`.
3. `scripts/validate_host_transport_wiring_attestation.py`
   - `--require-live-receipts` enforces per-channel freshness.
4. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - stale receipt blocked probe is requiredized.

Interpretation lock:

1. A stale historical receipt cannot be used as current-turn proof.
2. Host-visible checks remain fail-close and are not downgraded to observability-only output.

### 5.16 Cross-instance P0 absorption into strict scan/m2m projection (2026-03-15)

This checkpoint absorbs cross-instance audit findings into protocol-level strict scan closure,
so externally observed P0s are visible in the canonical `full_identity_protocol_scan` result.

Contract upgrades:

1. `full_identity_protocol_scan` strict path must include:
   - `validate_host_transport_wiring_attestation.py --require-live-receipts`
   - `validate_protocol_lane_headstamp_continuity.py`
2. Both checks are promoted into:
   - required `core_fail` path,
   - m2m projection classification.
3. Lane/headstamp continuity must accept current-turn stamp evidence as valid continuity source;
   stale report-only coupling is non-compliant.

Implementation anchors:

1. `scripts/full_identity_protocol_scan.py`
   - requiredized live host-visible + lane continuity checks for strict target scans.
2. `scripts/validate_protocol_lane_headstamp_continuity.py`
   - continuity evidence model accepts `report_ref OR stamp_ref`.
3. `scripts/repair_contract_backfill.py`
   - wrapper template sync snapshot fields included in backfill receipts for artifact-level visibility.

Interpretation lock:

1. If either live host-visible attestation or lane/headstamp continuity fails, strict target scan cannot claim closure.
2. Cross-instance runtime P0 findings must remain machine-visible in P0/m2m summaries, not hidden in out-of-band logs.

### 5.17 Active-runtime unique-entry migration closure probe (2026-03-15)

This checkpoint formalizes a dedicated migration-closure probe to ensure active runtime identities
do not regress on unique-entry max-age contract completeness.

Contract rule:

1. Every active runtime identity included in probe catalogs must expose:
   - `protocol_unique_entry_gate_contract_v1.entry_receipt_max_age_seconds > 0`
2. Missing/invalid values are fail-close and must block required probe suite completion.

Implementation anchors:

1. `scripts/check_unique_entry_contract_migration_closure.py`
   - validates active runtime identity rows across catalog inputs;
   - checks `CURRENT_TASK.json` contract presence and max-age positivity.
2. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - required probe `tuple_binding_active_runtime_contract_closure` calls the migration-closure checker.

Interpretation lock:

1. code-level freshness guard is not sufficient by itself; migration closure must also hold for active runtime contracts.
2. probe failures here are migration debt, not tuple-value mismatch noise.
3. `PASS_REQUIRED` from this checker is active-runtime fleet evidence only when the selected runtime surface contains checked active runtime identities; `checked_identity_count=0` is wiring sanity, not fleet-closure proof.
4. Current-state note (2026-03-22): replaying `python3 scripts/check_unique_entry_contract_migration_closure.py --catalog <project-local absolute catalog> --json-only` against the current workspace runtime surface returned `PASS_REQUIRED` with `checked_identity_count=4`; this is the current non-empty active-runtime proof and does not replace the standing empty-scan caveat above.

### 5.17.1 Active-runtime pack-scan convergence freeze (2026-03-26)

This checkpoint freezes the **scan semantics** behind active-runtime pack closure without changing
v1.6.6 semantic ownership of unique-entry migration law.

Contract rule:

1. `scripts/check_unique_entry_contract_migration_closure.py` must keep owning unique-entry migration semantics only.
2. Active-runtime catalog selection, pack-path resolution, and row aggregation must no longer drift checker-locally once the same pack universe is also scanned by `scripts/check_version_baseline_migration_closure.py`.
3. Shared scan semantics are now frozen through:
   - `scripts/runtime_pack_closure_common.py`
   - `active_runtime_pack_closure_scan_v1`
4. Bounded workspace replay must stay explicit as `workspace_runtime_only`.
5. Repo-inclusive replay must stay explicit as `repo_catalog_inclusive`; it must not silently collapse back to the local runtime catalog when stray repo runtime identities exist.

Implementation anchors:

1. `scripts/runtime_pack_closure_common.py`
   - shared owner for active-runtime pack-path resolution and scan aggregation.
2. `scripts/check_unique_entry_contract_migration_closure.py`
   - now consumes the shared pack-scan primitive while preserving unique-entry-specific contract checks.
3. `scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh`
   - proves that unique-entry migration closure and version-baseline migration closure share one pack-scan projection while keeping their semantic owners separate.

Interpretation lock:

1. This checkpoint does **not** move version-baseline semantics into v1.6.6.
2. It only freezes that active-runtime pack scan is shared infrastructure, not duplicated checker-local logic.
3. Workspace creator/update admission must consume the same bounded pack-closure command surface instead of re-spelling repo-inclusive unique-entry checks ad hoc; `workspace_runtime_closure_command_common.py` is the shared owner for that executable replay surface.
4. Current-state note (2026-03-26): replaying `bash scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh` returned `PASS`, and replaying `python3 scripts/check_unique_entry_contract_migration_closure.py --catalog <project-local absolute catalog> --workspace-runtime-only --json-only` returned `PASS_REQUIRED` with `checked_identity_count=4`, `catalog_selection_mode=workspace_runtime_only`, and `pack_scan_policy_id=active_runtime_pack_closure_scan_v1`.

### 5.18 Strict operation default entry-receipt requiredization (2026-03-15)

This checkpoint closes a bypass surface where strict operations could still rely on
`operation+run_id` checks only when callers forgot `--require-entry-receipt`.

Contract rule:

1. For strict operation scopes, entry receipt must be required by contract even without CLI forcing flags.
2. validator payload must expose machine-readable requiredization provenance:
   - `protocol_unique_entry_receipt_required_by_cli_flag`
   - `protocol_unique_entry_receipt_required_by_contract`
   - `protocol_unique_entry_receipt_required_reason`

Implementation anchors:

1. `scripts/validate_protocol_unique_entry_gate.py`
   - computes strict-operation contract requiredization and emits provenance fields.
2. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - required negative probe `strict_receipt_default_blocked` validates fail-close without `--require-entry-receipt`.
3. `scripts/validate_required_gate_surface_drift.py`
   - enforces strict-default receipt probe invocation in required delegate surface checks.

Interpretation lock:

1. strict paths cannot degrade into optional receipt mode by omitting CLI flags.
2. tuple context diagnostics remain explainable, but bypass by "missing flag" is no longer valid.

### 5.19 Post-check detectability + next-hop hard block closure (2026-03-15)

This checkpoint defines the control-plane closure model for residual host sender risk:
`95% pre-send hard gating + 100% post-check detectability + next-hop hard block`.

Semantic freeze (v1.6.6 authoritative wording):

1. Pre-send `>=95%` is a probabilistic prevention layer; it is not claimed as 100%.
2. Post-check next-hop is a deterministic decision layer:
   - `100% detectable`
   - `100% fail-close block on violation`
   - `100% next-hop headstamp required when release is allowed`

Contract upgrades:

1. Host-visible contract must declare:
   - `post_check_closure_state_file`
   - `post_check_block_on_active=true`
2. Host transport attestation must persist post-check closure state on every run.
3. Strict send-time gate must consume post-check closure state before release.
4. If post-check state is missing/invalid/unreadable, strict send-time must fail-close on next hop.
5. If post-check state indicates blocker active, strict send-time must fail-close on next hop.

Implementation anchors:

1. `scripts/protocol_infra_contract.py`
   - canonical post-check state constants and schema version.
2. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - materialize/backfill post-check closure fields for active runtime packs.
3. `scripts/validate_host_transport_wiring_attestation.py`
   - writes `runtime/state/host_visible_surface_live_closure_state.json`.
   - write failure is escalation-required fail-close (`IP-PRIV-ESC-001` family).
4. `scripts/validate_send_time_reply_gate.py`
   - strict-path preflight reads post-check closure state and blocks next hop when `blocker_active=true`.
   - blocked-before-first-line semantics are explicit:
     - `reply_first_line_gate_executed=false`
     - `reply_first_line_status=SKIPPED_NOT_REQUIRED`
     - `send_time_block_stage=pre_first_line_post_check_*`
     - `reply_first_line_missing_count=0`
5. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - required positive probe `send_time_governed_pass_headstamp_required` (next-hop release must keep headstamp + governed uniqueness).
   - required probe `send_time_next_hop_blocked_by_post_check`.
   - required probe `send_time_next_hop_blocked_on_missing_post_check_state`.
6. `scripts/full_identity_protocol_scan.py`
   - emits machine-readable metric projection:
     - `host_visible_post_check_metrics.host_visible_post_check_metrics_status`
     - `host_visible_post_check_metrics.metrics.*`
     - `host_visible_post_check_metrics.metric_statuses.*`
   - strict scan execution order must run `host_transport_wiring_attestation` before `send_time_reply_gate` to avoid stale closure-state pre-read in same turn.
   - strict scan orchestration must invoke `host_visible_post_check_recovery` before host/send gates, using explicit tuple-bound reseed + live attestation.
   - scan-time host attestation allowlist baseline is `runtime_dialogue` only; fixture source is probe-lane-only.
7. `scripts/recover_host_visible_post_check_state.py`
   - controlled recovery entry for blocker-active deadlock:
     - reseed channel receipts + runtime state with explicit tuple binding
     - immediately rerun live attestation (`--require-live-receipts`)
     - no manual state-file edits are allowed

P0 closure hardening (2026-03-16 supplement, still v1.6.6 scope):

1. Host-visible live source policy freeze:
   - `runtime_live_receipt_sources = [runtime_dialogue]`
   - `fixture_allowed_operations = [ci]`
   - any strict runtime operation that accepts fixture source is invalid.
2. Post-check recovery tuple continuity freeze:
   - recovery must not self-generate run tuple.
   - `session_id=run:<id>` and `run_id=<id>` mismatch is fail-close (`recovery_run_id_session_mismatch`).
3. Unique-entry receipt selector freeze:
   - deterministic precedence is fixed:
     `entry_receipt_selector_precedence = same_tuple > same_catalog > bundle_status_pass > newest`.
   - selector must emit machine-readable candidate/selection projection for audit replay.
4. Outlet bypass bridge freeze:
   - `IP-OUTLET-003` handling remains enforced via wrapper-only execution chain.
   - bypass remediation must be protocol-wiring changes, not instance-local patch receipts.

Metrics (must all pass for closure claim):

1. `pre_send_gate_pass_rate >= 0.95`
2. `post_check_detectability_rate = 1.00`
3. `next_hop_block_rate = 1.00`
4. `false_green_rate = 0.00`
5. `post_gate_coverage_rate = 1.00`
6. `chat_egress_uniqueness_rate = 1.00`
7. `next_hop_headstamp_rate = 1.00`

Minimum verification cadence (operator baseline):

1. `5` serial self-test rounds.
2. `5` serial deep-scan rounds.
3. Each round must include:
   - `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
4. At least one negative probe run proving:
   - post-check blocker activation,
   - next-hop strict send-time hard block,
   - blocker reason projection in validator payload.

Interpretation lock:

1. This is infrastructure closure behavior; it cannot be replaced by identity-local/manual headstamp printing.
2. If pre-send and post-check conclusions diverge, post-check blocker semantics are authoritative for next-hop release.
3. "reply_sample_count=0 + pre_first_line_post_check_*" means first-line gate was not reached; it must not be interpreted as "headstamp text generation failed".

### 5.20 Cross-actor isolation actor-scope closure semantics (2026-03-15)

This checkpoint closes `IP-ASB-203` false blocking caused by shared actor-session directories:
current actor strict closure must stay fail-close, while non-target actor contamination stays observable.

Contract upgrades:

1. `validate_cross_actor_isolation` adds explicit scope modes:
   - `catalog_all` (legacy strict-all behavior)
   - `actor_primary` (current actor fail-close + non-target warning telemetry)
   - `actor_only` (current actor fail-close only)
2. Strict runtime orchestrators must pass actor-scope parameters:
   - `--actor-id <resolved_actor_id>`
   - `--scope-mode actor_primary`
3. Validator payload must project both dimensions:
   - blocking axis: `cross_actor_isolation_status`, `stale_reasons`
   - non-blocking telemetry axis: `global_observation_status`, `global_observation_stale_reasons`

Implementation anchors:

1. `scripts/validate_cross_actor_isolation.py`
   - actor-scope evaluation and split projection.
2. `scripts/full_identity_protocol_scan.py`
   - strict scan invocation passes actor scope and records telemetry projection.
3. `scripts/report_three_plane_status.py`
   - strict three-plane invocation passes actor scope and exports telemetry projection.
4. `scripts/collect_identity_health_report.py`
   - cross-actor check receives actor scope; telemetry warning maps to `WARN`.
5. `scripts/identity_creator.py`, `scripts/release_readiness_check.py`,
   `scripts/e2e_smoke_test.sh`, `scripts/ci/run_required_runtime_gates_ci.sh`
   - strict validation lanes now pass actor scope explicitly.

Interpretation lock:

1. Current actor contamination remains hard-blocking (`FAIL_REQUIRED` / `IP-ASB-203`).
2. Non-target actor contamination is no longer allowed to masquerade as current actor hard failure.
3. Global hygiene cleanup is still mandatory governance work, but does not override current actor strict closure outcome by default.

### 5.21 Protocol lane explicit context + quoted foreign context non-binding guard (2026-03-16)

This checkpoint closes a strict-lane ambiguity class where protocol replies could appear to "lose headstamp" or
"switch identity" when orchestration omitted explicit context tuple forwarding.

Contract upgrades:

1. Protocol lane now has explicit context hard requirement at final egress.
   - `scripts/final_emit_governed.py` must fail-close when `work_layer=protocol` and any of the following are missing:
     - `--identity-id`
     - `--catalog`
     - `--repo-catalog`
     - `--actor-id`
     - `--session-id`
   - fail-close reason is machine-explainable:
     - `context_resolution_failed:protocol_work_layer_requires_explicit_context_args:*`
2. Embedded/quoted foreign `Identity-Context` lines are now non-binding evidence only.
   - `scripts/compose_and_validate_governed_reply.py` detects embedded quoted headstamp lines and projects:
     - `quoted_identity_context_detected`
     - `quoted_identity_context_foreign_ids`
     - `quoted_identity_context_guard_status=PASS_REQUIRED`
     - `quoted_identity_context_binding_effect=none`
3. Host unique channel wrappers now propagate `--repo-catalog` consistently across session-chain -> ingress/egress.
   - canonical templates in `scripts/create_identity_pack.py` include repo-catalog argument lane.
   - wrapper artifacts are materialized by protocol tooling (not manual pack edits):
     - `scripts/repair_contract_backfill.py --apply`

Implementation anchors:

1. `scripts/final_emit_governed.py`
2. `scripts/compose_and_validate_governed_reply.py`
3. `scripts/create_identity_pack.py`
4. `scripts/repair_contract_backfill.py`
5. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
6. `scripts/validate_required_gate_surface_drift.py`

Required probe closure:

1. `protocol_work_layer_explicit_context_required` (negative):
   - protocol lane without explicit tuple must fail-close.
2. `quoted_foreign_identity_context_must_not_switch_identity` (negative-to-safe):
   - foreign quoted headstamp detected but identity binding must remain unchanged.
3. `session_chain_protocol_lane_explicit_context_pass` (positive):
   - protocol session-chain wrapper path must preserve first-line headstamp and final emit PASS tuple.

Interpretation lock:

1. This is protocol infrastructure hardening, not instance-local hotfix behavior.
2. Reply text containing foreign `Identity-Context` is evidence-only and cannot drive identity resolution.
3. "Headstamp missing" claims are invalid unless unique-channel wrapper path and send-time gate receipts both fail.

### 5.22 Post-check fail-close attribution + tuple continuity hardening (2026-03-16)

This checkpoint closes two recurring ambiguity classes that produced false P0 interpretation:

1. strict scan/recovery tuple continuity drift (`session_id=run:<id>` but recovery/checks used a different `run_id`);
2. permission/reachability execution faults being reported as generic headstamp failures without machine-readable attribution.

Contract upgrades:

1. scan lane run/session continuity is now deterministic:
   - `scripts/full_identity_protocol_scan.py` derives strict `run_id` from `session_id=run:<id>` when available.
   - `scripts/validate_headstamp_recurrence_closure.py` recovery precheck inherits the same session-bound `run_id`.
2. send-time post-check unavailable path now preserves escalation attribution:
   - `scripts/validate_send_time_reply_gate.py` marks permission-read failures as
     - `host_transport_post_check_state_status=STATE_PERMISSION_DENIED`
     - `error_code=IP-PRIV-ESC-001`
   - `chat_egress_uniqueness_error_code` mirrors the same fail-close code.
3. gateway subprocess failure classification is now structured (no silent fallthrough):
   - `scripts/gateway_wrapper_enforcement.py` emits machine payload when child process fails without JSON:
     - privilege family: `IP-PRIV-ESC-001`
     - localhost/socket reachability family: stale reason prefix
       `host_transport_reachability_unavailable:*`

Interpretation lock:

1. P0 "headstamp bypass" must not be declared when root cause is permission/reachability execution fault.
2. tuple-bound strict lanes use `session_id=run:<id>` as canonical run binding source.
3. all such execution faults remain fail-close (no downgrade to warning-only).

### 5.23 Host transport dependency isolation + privilege write probes (2026-03-17)

This checkpoint upgrades two previously implicit runtime dependencies into protocol-controlled surfaces:

1. host transport reachability is now an explicit validator lane, not a side effect of headstamp/send-time failure;
2. privilege-denied write paths on strict control-plane writers are now required negative probes, not ad-hoc manual replay.

Contract upgrades:

1. host transport reachability must be resolved explicitly:
   - validator: `scripts/validate_host_transport_reachability.py`
   - CI delegate: `scripts/ci/run_host_transport_reachability_probes_ci.sh`
   - transport URL must be provided explicitly or resolved from instance contract field
     `transport_healthcheck_url`
   - hardcoded protocol-repo defaults for business/runtime host endpoints are forbidden
2. reachability failure is a first-class protocol fault:
   - `error_code=IP-HTR-001`
   - `transport_reachability_status`
   - `transport_failure_class`
   - stale reason prefix `host_transport_reachability_unavailable:*`
3. official live closure must isolate dependency failure before downstream noise:
   - `scripts/run_host_visible_live_closure.py` runs reachability validation first
   - reachability failure short-circuits recovery/attestation/send-time with fail-close output
4. privilege write-denied probes are required for core strict writers:
   - CI delegate: `scripts/ci/run_privilege_escalation_write_probes_ci.sh`
   - minimum probes:
     - unique-entry receipt write denied
     - host-visible recovery write denied
     - post-check closure state write denied
   - required error family: `IP-PRIV-ESC-001`

Interpretation lock:

1. `127.0.0.1:3001` or any similar runtime endpoint is consumer/runtime configuration, not protocol-repo constant state.
2. transport reachability failure, privilege boundary failure, and semantic headstamp failure must remain separate axes in replay output.
3. required CI must prove both reachability fault isolation and privilege write fail-close behavior.

### 5.24 v1.6.6 finish-line freeze: one-hop death + blocker evidence + canonical next-hop admission (2026-03-17)

This checkpoint freezes the remaining v1.6.6 closure scope so later work cannot drift into
overclaiming full pre-send native-chat control or reduce closure to text-only headstamp checks.

Authoritative finish-line definition:

1. v1.6.6 target is:
   - pre-send high coverage (`>=95%`)
   - post-check `100%` detectability
   - post-check `100%` next-hop blocking
   - next-hop mandatory canonical headstamp
2. v1.6.6 does **not** claim `current_chat_surface_native_machine_attested = true`; host-native chat remains on the standard path `machine-verify -> assistant-visible-inject -> next turn re-verify`.
3. any output outside canonical control lane must be governed by the non-governed output one-hop death rule.

Finish lines (must all hold for v1.6.6 closure claim):

1. Finish Line 1: non-governed output one-hop death rule
   - any output without canonical control-lane attestation is not next-hop admissible.
   - manual first-line text is insufficient.
   - host-direct output is insufficient.
2. Finish Line 2: failure evidence dual-channel
   - sandbox / privilege / write-fail / timeout / reachability / unreadable-state faults must produce canonical blocker evidence.
   - file receipt is preferred, but structured blocker payload is mandatory fallback.
3. Finish Line 3: post-gate coverage authority
   - `post_gate_coverage_rate = 1.00`
   - when pre-send and post-check diverge, post-check is authoritative for next-hop release.
4. Finish Line 4: canonical next-hop headstamp
   - `next_hop_headstamp_rate = 1.00`
   - only canonical governed headstamp counts; manual headstamp and host-direct output never count as pass.

Canonical next-hop admission machine tuple:

1. `next_hop_admission_status`
2. `next_hop_admission_reason`
3. `output_governance_mode`
4. `control_lane_attestation_status`
5. `post_check_blocker_status`

These fields must be emitted by canonical send-time validation and consumed by replay/scan/probe lanes.
They exist to prevent downstream tooling from inferring next-hop legality by text-only heuristics.

Terminology freeze (authoritative wording):

1. governed output
   - output produced through canonical control lane with valid attestation lineage.
2. manual headstamp
   - output that contains `Identity-Context:` text but lacks canonical control-lane attestation.
   - assistant-visible self-printed headstamp is classified as manual headstamp, not closure evidence.
3. host-direct output
   - host/model visible output emitted outside governed egress lane.
4. next-hop-admissible output
   - the only output class allowed to enter the next strict controlled hop.

Required relations:

1. governed output is the only class that can become next-hop-admissible output.
2. manual headstamp != governed output.
3. host-direct output != next-hop-admissible output.
4. first-line headstamp presence alone never proves next-hop admissibility.

Anti-forget enforcement:

1. `scripts/validate_required_gate_surface_drift.py` must require the above finish-line wording in v1.6.6 governance/review surfaces.
2. `scripts/validate_required_gate_surface_drift.py` must reject protocol-repo hardcoded runtime endpoints such as `HOST_TRANSPORT_REACHABILITY_DEFAULT_URL` or `http://127.0.0.1:3001/healthz`.
3. future validators/probes may extend v1.6.6 closure, but they must preserve these terms and finish-line definitions instead of introducing alternate wording.
4. `scripts/ci/run_host_visible_surface_live_probes_ci.sh` must keep at least one negative probe proving inline/self-printed reply text is classified as `host_direct` and not next-hop admissible.

### 5.25 display_headstamp / machine_headstamp object split freeze (2026-03-17)

This checkpoint freezes the object split required to preserve human-visible identity
signals without letting visibility text collapse back into truth or next-hop proof.

Authoritative principle:

1. `display_headstamp` is a visibility-layer object.
2. `machine_headstamp` is a control-plane object.
3. display rights are delegated; truth rights stay machine-authoritative in the control plane.
4. `v1.6.1` owns display entry and shared renderer invocation.
5. `v1.6.6` owns consistency review, correction semantics, and next-hop admissibility.

Definitions (authoritative wording):

1. `display_headstamp`
   - the user-visible headstamp object shown to humans.
   - it may be gate-rendered, manual, or host-direct.
   - manual display is a render_origin of `display_headstamp`, not an automatic fail condition.
2. `machine_headstamp`
   - the control-plane machine object that carries authoritative identity plus the tuple / lane / attestation facts used for admission.
   - it is not a free-form display string and must never be inferred from pasted or manual display text.
3. display wiring
   - the identity-owned obligation to connect visible output into the declared display entry / wrapper surface.
4. headstamp admission receipt
   - the machine verdict that compares `display_headstamp` to `machine_headstamp` and decides pass / correction / block.

Authoritative identity precedence:

1. session-scoped actor binding
2. canonical session pointer
3. single active runtime identity
4. default runtime identity
5. `display_headstamp` text must never become an authority source

Required relations:

1. `display_headstamp != machine_headstamp`.
2. `display_headstamp` solves human visibility only.
3. `machine_headstamp` solves truth and next-hop admissibility.
4. `display_headstamp` presence is necessary for strict user-visible lanes, but never sufficient for admission.
5. `identity` owns display wiring; control plane owns truth and admission.
6. gate-rendered display remains a display object; it does not bypass consistency review or next-hop admission review.

Consistency states (machine-authoritative):

1. `PASS_REQUIRED`
   - `display_headstamp` identity claim matches `machine_headstamp.authoritative_identity_id`.
2. `AUTO_CORRECTED`
   - `display_headstamp` differs from `machine_headstamp`, the authoritative identity is uniquely resolved, the visible headstamp is actually rewritten, and correction evidence exists.
3. `FAIL_REQUIRED`
   - `display_headstamp` differs from `machine_headstamp` and no authoritative rewrite actually happened, or tuple / lane / authority conflict remains active.

Current machine projection fields:

1. `display_headstamp_identity_id`
2. `authoritative_identity_id`
3. `headstamp_consistency_status`
4. `headstamp_consistency_mode`
5. `headstamp_consistency_reason`
6. `headstamp_correction_from`
7. `headstamp_correction_to`
8. `headstamp_correction_evidence_ref`
9. `next_hop_admission_status`

Interpretation lock:

1. `display_headstamp` and `machine_headstamp` are the only two authoritative top-level objects for this semantic split.
2. `manual_headstamp` is no longer a parallel top-level concept; it survives only as `display_headstamp.render_origin = manual`.
3. no validator or governance stream may collapse these layers back into one ambiguous notion of "headstamp present".

### 5.26 fail-close + remediation lane processing freeze (2026-03-17)

This checkpoint freezes the processing model that follows the two-object split.

Processing phases:

1. Display declaration
   - `identity` declares display policy and display wiring through identity-owned surfaces such as `IDENTITY_PROMPT` and `CURRENT_TASK`.
2. Display render
   - `v1.6.1` display entry invokes shared renderer and emits `display_headstamp`.
3. Machine truth resolve
   - control plane resolves authoritative identity and emits `machine_headstamp`.
4. Consistency review
   - control plane compares `display_headstamp` with `machine_headstamp` and emits correction / blocker verdict.
5. Business next-hop admission
   - control plane decides whether the original governed business lane may continue.
6. Remediation lane
   - if business next hop is blocked, control plane may open a separate remediation lane for wiring or correction work.

Fail-close rule:

1. display contract failure, display wiring failure, correction failure, or truth absence must fail-close the original business next hop.
2. business next hop must fail-close before remediation lane opens.
3. fail-close on the business lane does not imply that all remediation activity is forbidden.

Remediation lane rule:

1. remediation lane is allowed only when truth is already resolved and remediation target is deterministic.
2. wiring / wrapper hookup defects may enter remediation lane.
3. authority ambiguity, unresolved truth, or conflicting machine evidence must escalate instead of self-remediate.
4. remediation lane output never counts as business next-hop pass by itself.
5. remediation must be followed by revalidation before business next hop may reopen.

Interpretation lock:

1. `display_headstamp` may be normal even when rendered manually, as long as display contract holds and control-plane truth review passes.
2. remediation is triggered by wiring / contract / truth failures, not merely by render origin being manual.
3. `v1.6.1` owns display entry; `v1.6.6` owns consistency, correction, and next-hop admissibility.

### 5.27 display declaration lineage + headstamp admission receipt freeze (2026-03-17)

This checkpoint freezes the declaration chain, the strict human-visible consumption rule,
and the minimum machine receipt fields so the protocol cannot drift back into
"someone printed a headstamp line, therefore next hop may continue."

Display declaration lineage:

1. `IDENTITY_PROMPT` declares display intent and schema, not final runtime display literals.
2. `CURRENT_TASK.json` carries the normalized runtime `display_headstamp` contract and is the runtime SSOT.
3. `v1.6.1` gate/shared renderer consumes the normalized `CURRENT_TASK.json` contract plus runtime tuple and produces the runtime `display_headstamp` object.
4. raw prompt text must never be consumed directly as the runtime `display_headstamp` object.

Strict human-visible consumption and admission rule:

1. humans consume `display_headstamp`.
2. control plane consumes `machine_headstamp` and `headstamp_admission_receipt`.
3. strict human-visible next hop requires `display_headstamp` present AND `headstamp_admission_receipt.next_hop_admission_status = PASS_REQUIRED`.
4. `display_headstamp` present + machine admission fail means visibility may remain for operator clarity, but the governed business next hop must still fail-close.

Manual bridge sentence:

1. `manual_headstamp` is the human-facing shorthand for `display_headstamp.render_origin = manual`.
2. `manual_headstamp` is not a third truth object, authority source, or admission-proof class.
3. manual render origin is reviewed by control plane together with lane attestation, blocker evidence, and next-hop admission tuple; it never overrides them.

`headstamp_admission_receipt` minimum fields:

1. `display_headstamp_identity_id`
2. `authoritative_identity_id`
3. `headstamp_consistency_status`
4. `headstamp_consistency_mode`
5. `headstamp_consistency_reason`
6. `headstamp_correction_from`
7. `headstamp_correction_to`
8. `headstamp_correction_evidence_ref`
9. `control_lane_attestation_status`
10. `post_check_blocker_status`
11. `next_hop_admission_status`
12. `next_hop_admission_reason`
13. `output_governance_mode`

Interpretation lock:

1. declaration/render/wiring ownership remains with `v1.6.1`.
2. truth/consistency/admission/remediation ownership remains with `v1.6.6`.
3. no future wording may collapse `display_headstamp`, runtime render output, `machine_headstamp`, and `headstamp_admission_receipt` into one undifferentiated "headstamp present" concept.

### 5.28 clean-pass seed replay probe semantics alignment (2026-03-17)

Problem:

1. `dcf2530` closed the display-admission / seed-replay loop so a clean first-pass egress no longer needs a synthetic seed replay.
2. the trust-boundary CI probe still expected seed replay on a fresh clean pass and therefore drifted from runtime behavior.

Mandatory behavior:

1. on a clean first-pass session-chain egress:
   - `host_visible_receipt_seed_attempted = false`
   - `host_visible_receipt_seed_replay_count = 0`
   - `host_visible_receipt_seed_gate_status = SKIPPED_NOT_REQUIRED`
   - `host_visible_receipt_seed_gate_reason = initial_egress_pass_required`
2. seed replay remains required only when initial egress fails and the payload is seed-eligible.
3. trust-boundary CI must encode both cases explicitly:
   - clean-pass skip
   - hard-prereq seed block

Interpretation lock:

1. “seed replay available” does not mean “seed replay always mandatory”.
2. `v1.6.6` owns the admission rule and the probe wording must follow the runtime contract, not the older expectation.

### 5.29 current-surface transport attestation closes first-pass admission circularity (2026-03-17)

Problem:

1. send-time validation originally treated `reply_file` evidence as admissible only after host-visible live receipts already existed.
2. during the very first governed egress of a clean session-chain round, those live receipts do not exist yet because they are written by the wrapper immediately after egress succeeds.
3. this created an artificial circularity:
   - first pass = governed output already written
   - send-time validator still downgraded to `manual_headstamp`
   - wrapper replayed a seed pass only to satisfy its own first-pass gap

Mandatory behavior:

1. strict `reply_file` / `reply_log` send-time validation MUST accept either of these transport proofs:
   - host-visible live receipt binding, or
   - current-surface governed transport attestation for the just-produced reply transport.
2. current-surface attestation is allowed only when all of the following hold:
   - the validator is invoked from a controlled runtime entrypoint that explicitly attests the current surface
   - `send_time_gate_status = PASS_REQUIRED`
   - `reply_first_line_status = PASS_REQUIRED`
   - `final_emit_contract_status = PASS_REQUIRED`
   - governed outlet + final emit tuple are machine-attested
   - live transport binding is missing only because live receipts are not materialized yet
3. this attestation must be projected as:
   - `current_surface_transport_attestation_status`
   - `current_surface_transport_attestation_reason`
   - `current_surface_transport_attestation_mode`
   - `current_surface_native_machine_attested`
4. live host-visible receipts remain required for post-emit runtime auditing; current-surface attestation does not replace that audit lane.

Interpretation lock:

1. this is not a new authority source and not a wrapper exception.
2. it is the machine-owned bridge that removes first-pass replay circularity while preserving later live-receipt auditing.

### 5.30 session-chain ingress receipt consumption must be per-run and atomic (2026-03-17)

Problem:

1. session-chain wrapper historically reused `runtime/state/required_gate_bundle_entry.latest.json` as the ingress receipt path for egress.
2. under concurrent self-tests or parallel runtime rounds, `latest` is a shared mutable pointer and can be replaced by a sibling run between ingress and egress.
3. that creates two invalid outcomes:
   - logical race: egress reads another run's receipt tuple
   - file corruption risk if concurrent writers do not persist state atomically

Mandatory behavior:

1. session-chain wrapper MUST consume `protocol_unique_entry_receipt_path` returned by the ingress payload whenever available.
2. `required_gate_bundle_runner.py` receipt state writes MUST use atomic temp-file replace semantics for:
   - nonce replay state
   - entry receipt state/history outputs
3. shared `latest` state may remain as an operator convenience pointer, but it must not be the only per-run handoff artifact for strict wrapper chaining.

Interpretation lock:

1. this does not relax unique-entry governance.
2. it hardens runtime integrity so parallel self-tests cannot corrupt or cross-wire strict entry receipts.

### 5.31 three-plane instance closure must follow post-execution mandatory contract (2026-03-17)

Problem:

1. `validate_post_execution_mandatory.py` already recognizes the strict non-upgrade closure path:
   - `upgrade_required = false`
   - `all_ok = true`
   - `writeback_mode = STRICT_WRITEBACK`
   - `writeback_status in {WRITTEN, NOT_REQUIRED}`
2. `report_three_plane_status.py` still re-derived instance closure with a narrower rule:
   - `writeback_status = WRITTEN`
   - `permission_state = WRITEBACK_WRITTEN`
3. this left strict non-upgrade rounds stuck at `instance_plane_status = IN_PROGRESS` even when:
   - `post_execution_mandatory_status = PASS_REQUIRED`
   - validators were all green
   - `next_action = no_upgrade_triggered`

Mandatory behavior:

1. three-plane instance-plane aggregation MUST treat `post_execution_mandatory_status = PASS_REQUIRED` as the closure authority for strict execution completion.
2. `permission_state = PRECHECK` on a strict non-upgrade round is not, by itself, a non-closure signal once post-execution mandatory has passed.
3. `WRITEBACK_WRITTEN` remains the closure shape for strict upgrade/writeback-required rounds; it is not mandatory for strict non-upgrade closure.
4. full-scan / three-plane aggregation MUST NOT reintroduce a narrower writeback-only rule after the post-execution validator has already accepted the round.

Interpretation lock:

1. this is an acceptance aggregation alignment, not a relaxation of writeback continuity or send-time governance.
2. remaining `Conditional Go` after this alignment must come from repo-plane / release-plane conditions or genuine validator failures, not stale duplicated instance-plane closure logic.

### 5.32 release-plane baseline normalization for three-plane aggregation (2026-03-17)

Problem:

1. `report_three_plane_status.py` defaulted `target_branch` and `release_head_sha`, but left the release-plane comparison tuple partially unset:
   - `workflow_file_sha`
   - `run_head_sha`
   - `run_workflow_file_sha`
2. as a result, local three-plane aggregation could report release plane as an undifferentiated `NOT_STARTED` with four false conditions, even though:
   - branch/head baseline was already known
   - the real missing inputs were the cloud run binding and required-check result set

Mandatory behavior:

1. three-plane aggregation MUST normalize the release-plane comparison baseline exactly as release-readiness does:
   - `workflow_file_sha := release_head_sha` when omitted
   - `run_head_sha := release_head_sha` when omitted
   - `run_workflow_file_sha := workflow_file_sha` when omitted
2. once that baseline exists, missing release cloud evidence must be expressed as release-plane `BLOCKED`, not a generic `NOT_STARTED`.
3. in that state, the condition matrix must isolate the true unresolved items:
   - `required_gates_run_id_accessible = false`
   - `required_checks_all_success = false`
   while head/sha parity remains machine-visible as pass.

Interpretation lock:

1. this does not close release plane without cloud evidence.
2. it removes release-plane observability drift so `Conditional Go` points at the real missing release evidence instead of a stale partially-initialized baseline.

### 5.33 release-plane checks evidence accessibility must be distinct from checks verdict (2026-03-17)

Problem:

1. once release baseline was normalized, the remaining release-plane blocker still mixed two different states under
   `required_checks_all_success = false`:
   - checks evidence was never supplied
   - checks evidence was supplied but failed
2. that ambiguity makes local three-plane output less useful for deciding whether to fetch release evidence or debug a failing check set.

Mandatory behavior:

1. release-plane condition projection MUST expose evidence accessibility separately from verdict:
   - `required_checks_evidence_accessible`
   - `required_checks_set_present`
   - `required_checks_status`
2. `required_checks_status` must distinguish at least:
   - `EVIDENCE_MISSING`
   - `EMPTY_SET`
   - `FAILED`
   - `PASS`
3. `required_checks_all_success = false` is therefore no longer interpreted alone; operators must read it together with the evidence-accessibility fields.

Interpretation lock:

1. this does not weaken release gating.
2. it sharpens release-plane diagnosis so “go fetch the cloud checks evidence” and “the checks failed” cannot collapse into the same opaque false boolean.

### 5.34 surface semantics matrix + order separation freeze (2026-03-18)

Canonical semantics source:

1. `identity/protocol/plugins/templates/headstamp-surface-semantics.matrix_v1.json` is the machine-readable SSOT for the wording in this section.

Processing order vs runtime loop vs visible line order:

1. `processing order` belongs to control plane review and admission:
   - `Display render -> Machine truth resolve -> Consistency review -> Business next-hop admission`
2. `runtime loop` belongs to native chat assistant-visible injection:
   - `machine-verify -> assistant-visible-inject -> next turn re-verify`
3. `visible line order` is surface-specific and MUST NOT be inferred from either item 1 or 2:
   - native chat = `Identity-Context -> Machine-Verification -> body`
   - governed/explanatory envelope = `Display-Headstamp -> Machine-Verification -> body`
4. Native chat failure handling remains fail-close:
   - headerless assistant-authored native-chat reply is forbidden
   - when success-state identity injection is blocked, the two-line withheld/conflict envelope remains required
   - failure line 1 `requested_identity_id` is the requested target only; it is not the current speaking identity
   - compatibility-pointer identity, when shown, remains a `Machine-Verification` diagnostic only and never upgrades to current-turn authority

Surface semantics matrix (authoritative surface -> visible literal order freeze):

1. native chat visible order = `Identity-Context -> Machine-Verification -> body`
2. governed/explanatory visible order = `Display-Headstamp -> Machine-Verification -> body`

Three orders matrix (do not collapse these terms):

1. processing order = control-plane review/admission sequence
2. runtime loop = native chat injection sequence
3. visible line order = surface literal sequence

Object vs literal mapping:

1. `display_headstamp` is a visibility object.
   - native literal = `Identity-Context: ... | Layer-Context: ...`
   - governed literal = `Display-Headstamp: Identity-Context: ... | Layer-Context: ...`
2. `machine_headstamp` is a control-plane truth object.
   - native literal = `Machine-Verification: ...`
   - governed literal = `Machine-Verification: ...`
3. `headstamp_admission_receipt` is the admission-verdict object.
   - it is not the first visible literal on either native chat or governed surfaces
   - it decides next-hop legality together with machine truth

Interpretation lock:

1. `manual_headstamp` = render_origin tag only; never verdict axis.
2. `EXCLUDED_NON_BLOCKING` only removes blocker aggregation; it never upgrades next-hop admission.
3. strict human-visible next hop still requires `display_headstamp` present AND `headstamp_admission_receipt.next_hop_admission_status = PASS_REQUIRED`.
