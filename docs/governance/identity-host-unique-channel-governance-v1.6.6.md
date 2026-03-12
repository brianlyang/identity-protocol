# Identity Host Unique Channel Governance (v1.6.6)

Status: Active (pre-development governance freeze)  
Layer: protocol  
Scope: host-session unique ingress/egress enforcement + per-instance wrapper contract

Execution mode: topic-level canonical SSOT for v1.6.6 host-channel closure.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.6 host-channel closure.
2. Historical statements in v1.6.0-v1.6.5 remain valid only when not superseded by this stream.
3. Current-state judgment must prioritize machine outputs from:
   - `python3 scripts/validate_control_plane_invariants.py --json-only`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
   - `python3 scripts/docs_command_contract_check.py`
4. `/tmp/*` and ad-hoc logs are replay artifacts only and are never normative contract input.
5. Normative mapping entrypoints are current-pointer files only:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`

## 1) Why v1.6.6 exists

v1.6.1 closed protocol strict-surface headstamp/egress contracts.  
v1.6.4 closed plugin monotonic fail-close semantics.  
v1.6.5 hardened platform governance and required-check surfaces.

Remaining closure gap:

1. Host conversation dispatch can still bypass protocol ingress/egress contracts if runtime entrypoints call session-control directly.
2. Instance packs can declare unique-entry contract in `CURRENT_TASK.json`, but runtime routing may still skip enforcement when wrappers are absent or not consumed by host.
3. Result: configuration may be correct while user-visible output path is still weakly coupled.

v1.6.6 closes this by freezing one host-channel contract:

1. Instance-side wrappers are mandatory and generated.
2. Host dispatch must call wrappers only.
3. Protocol ingress/egress scripts remain single canonical authority.

## 2) Non-negotiable contracts (no ambiguity)

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

### 2.3 Host dispatch contract (mandatory)

Host session entrypoints must not dispatch user messages directly to instance business scripts.

Required model:

1. Host receives inbound message.
2. Host invokes per-instance ingress wrapper.
3. Ingress wrapper invokes `scripts/required_gate_bundle_runner.py`.
4. Execution is blocked unless unique-entry receipt is `PASS_REQUIRED`.

### 2.4 Host release contract (mandatory)

Any user-visible output must pass egress wrapper before release.

Required model:

1. Candidate output enters per-instance egress wrapper.
2. Egress wrapper invokes `scripts/final_emit_governed.py`.
3. Send-time/headstamp contracts must pass for current turn.
4. Missing/mismatched receipt or headstamp is `FAIL_REQUIRED`.

### 2.5 Layer boundary contract (protocol vs instance)

1. Protocol layer defines contracts, schema, validators, and fail-close semantics.
2. Instance layer defines business behavior and parameters only.
3. Protocol layer must not embed instance business logic.
4. Instance layer must not redefine protocol canonical ingress/egress semantics.

### 2.6 Performance boundary contract

1. Host gateway must be lightweight and deterministic.
2. Latency budget applies to gateway stage itself, not approval waiting time:
   - local gateway target: `P95 <= 300ms`.
3. Any new check added to ingress/egress must include budget impact evidence before promotion.

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
2. Rulesets model supports centralized enforcement layering compatible with protocol/host split.

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
3. `scripts/validate_required_gate_surface_drift.py` must detect host-side bypass surfaces where applicable.

### 4.2 Host-repo target

1. Host dispatch entrypoints must call ingress wrapper only.
2. Host user-visible output release must call egress wrapper only.
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
5. Host replay proves no direct-bypass outbound path under target entrypoints.
6. Stream PR binding receipt exists under persistent evidence path and matches current head SHA.

Release decision:

1. Any failure in items above blocks v1.6.6 closure claim.

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
