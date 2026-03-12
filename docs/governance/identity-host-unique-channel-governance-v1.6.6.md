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
2. Operationally, all mandatory routing refers to the **project-side identity runtime adapter + instance pack wrappers**.
3. `Host` in this document does **not** imply modifying unrelated external repositories.
4. The hard requirement is wrapper downsink and wrapper-only invocation under `.identity/{identity_id}/runtime/gate/*`.

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
4. Missing wrapper files in strict operations are `FAIL_REQUIRED`.

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
8. `catalog_path`
9. `entry_receipt_policy` (`required: true`)
10. `egress_receipt_policy` (`required: true`)
11. `headstamp_policy` (`required: true`)
12. `identity_tuple_fields` (must contain `actor_id`, `session_id`, `run_id`, `work_layer`, `source_layer`)

Schema/fail-close rules:

1. `additionalProperties` must be rejected by validator in strict mode.
2. `protocol_ingress_script` and `protocol_egress_script` must be explicit paths, not inferred defaults.
3. Any missing required field above is `FAIL_REQUIRED` during init/update validation.
4. Any canonical script mismatch is `FAIL_REQUIRED` (no alias authority).

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
2. Project-side runtime invokes per-instance ingress wrapper.
3. Ingress wrapper invokes `scripts/required_gate_bundle_runner.py`.
4. Execution is blocked unless unique-entry receipt is `PASS_REQUIRED`.

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

### 2.4.2 Failure-code family preservation contract (mandatory)

To keep audit replay stable across streams:

1. Missing/invalid unique-entry receipt must preserve bundle-entry family (`IP-GATE-ENTRY-*`).
2. Headstamp tuple failures must preserve headstamp family (`IP-HDSTAMP-*`).
3. Actor/session tuple failures must preserve actor-session family (`IP-ASB-*`) where applicable.
4. New wrappers must not replace canonical families with ad-hoc aliases.

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
