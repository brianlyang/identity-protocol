# Identity Fail-Close Monotonic Governance (v1.6.4)

Status: Active (pre-development governance freeze)  
Layer: protocol  
Scope: standard plugin control-plane hardening for configurable flow + no-downgrade + newcomer-safe handoff

Execution mode: topic-level canonical SSOT for v1.6.4 semantic hardening.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for v1.6.4 monotonic fail-close hardening.
2. Historical statements in v1.6.0-v1.6.3 remain valid only when not superseded by this stream.
3. Runtime behavior judgments must prioritize machine outputs from:
   - `scripts/validate_control_plane_invariants.py`
   - `scripts/validate_required_gate_surface_drift.py`
   - `scripts/validate_failclose_plugin_projection.py`
   - `scripts/full_identity_protocol_scan.py --scan-mode target`
4. `/tmp/*` and ad-hoc logs are replay artifacts only and are never normative contract input.

## 1) Why v1.6.4 exists

v1.6.0-v1.6.3 solved most wiring and control-plane consistency, but there are still semantic gaps that make strict plugin enforcement feel weaker than intended:

1. Strict lanes can still surface `SKIPPED_NOT_REQUIRED` in runtime-proof branches for multimodal checks.
2. Reasoning enforcement can silently stay on `L1` when no stronger level is declared.
3. Required-gate bundle routing can avoid strict run-id semantics for reasoning in fallback-shaped invocations.

v1.6.4 is dedicated to closing those gaps without breaking existing extensibility.

## 2) Current baseline (cross-verified on 2026-03-11)

### 2.1 What is already strong

1. Control-plane invariants are green:
   - `contract_binding_meta_row_count=35`
   - `contract_binding_actual_row_count=35`
   - plugin wiring and prompt binding violation counts are `0`.
2. Required-gate surface drift guard is green and command-level strict:
   - required scripts and required tokens are parsed from executable invocations (not comment text).
3. v1.6.3 platform-facing repo controls are wired in code:
   - `merge_group` event in key workflows
   - `.github/CODEOWNERS` exists
   - offload mapping status is tracked by `identity/protocol/mappings/github-control-plane-offload.current.yaml`.

### 2.2 Residual semantic gaps to close in v1.6.4

1. Multimodal strict lane runtime-proof defer can still yield overall pass while runtime evidence is not materialized:
   - `scripts/validate_multimodal_plugin_enforcement.py` (`runtime_stage_deferred*` branches).
2. Reasoning default level remains `L1` unless explicit stronger configuration is present:
   - `identity/protocol/plugins/reasoning-loop-enforcement/plugin.contract.yaml`
   - `scripts/validate_reasoning_loop_failclose.py`.
3. Bundle runner does not always pass `--run-id` into reasoning validator unless `--report-selected-path` is present:
   - `scripts/required_gate_bundle_runner.py`.

## 3) v1.6.4 non-negotiable contracts

### 3.1 Config-first standard flow (no hardcoding)

Every new protocol fail-close plugin must be wired through:

1. `identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml`
2. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
3. `identity/protocol/mappings/contract-binding.current.yaml`
4. `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
5. `identity/protocol/mappings/stream-doc-registry.current.yaml`

No direct workflow-shell business logic is accepted as a substitute for those mappings.

### 3.2 Monotonic level contract (allow upgrade, forbid downgrade)

1. Each strict contract must define an effective enforcement floor.
2. Execution may self-upgrade to stronger level when stronger evidence is available.
3. Execution must fail-close when reported effective level is below configured floor.
4. For strict operations (`activate`, `update`, `mutation`, `readiness`, `e2e`, `ci`, `validate`, `three-plane`):
   - top-level required contracts must not resolve to silent downgrade semantics.
   - `SKIPPED_NOT_REQUIRED` is only valid for declared non-applicable contexts (for example fixture/demo profiles), and must carry explicit reason.

### 3.3 Newcomer/memory-loss safety contract

Protocol control must be understandable and executable without relying on personal memory:

1. Stream docs are machine-registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`.
2. Mandatory alias references are machine-checked by `scripts/docs_command_contract_check.py`.
3. Plugin onboarding is machine-token-checked by:
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`
   - `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`.
4. If a new engineer follows only current-pointer files, they must be able to wire a new contract without hidden tribal knowledge.

### 3.4 AI folder governance plugin exemplar (new stream template)

v1.6.4 uses AI folder normalization as a standardization exemplar:

1. Plugin category: protocol hygiene/control-plane plugin, not business logic plugin.
2. Contract intent:
   - enforce canonical runtime directory boundaries
   - block non-canonical ad-hoc AI artifact roots in strict lanes
   - require deterministic pointer-based references instead of scattered literal paths
3. Join path:
   - register by `plugin_id + requirement_key + bundle_target_name + gate_mode + ssot_mapping_ref`
   - add projection/report fields before promotion
   - pass required-gate bundle and drift guards before release claim.

## 4) Cross-verification (roundtable + vendor + network + reference + context7)

### T1 Roundtable (repo-machine replay)

1. `validate_control_plane_invariants` and `validate_required_gate_surface_drift` are `PASS_REQUIRED`.
2. `full_identity_protocol_scan --scan-mode target` confirms:
   - fixture target can hold `p0=0` in strict profile replay.
   - non-fixture target still exposes binding-quality gaps if actor-session is not correctly pre-bound (operational, not semantic contract absence).
3. Projection replay confirms current weak-feel source:
   - multimodal can pass with deferred runtime-proof projection fields in strict flow.

### T2 Vendor (OpenAI official docs)

1. Codex approvals/sandbox controls reinforce explicit execution boundaries and approval-safe gates:
   - https://developers.openai.com/codex/agent-approvals-security/
2. Codex GitHub Action security checklist reinforces strict trigger/scope and secrets hygiene:
   - https://developers.openai.com/codex/github-action/#security-checklist
3. Function calling strict mode explicitly recommends strict schema enforcement:
   - https://platform.openai.com/docs/guides/function-calling#strict-mode
4. Structured outputs guidance explicitly prefers schema-adherent mode over plain JSON mode:
   - https://platform.openai.com/docs/guides/structured-outputs#structured-outputs-vs-json-mode

### T3 Network references (platform governance + workflow semantics)

1. GitHub Actions `merge_group` trigger requirement for merge queue checks:
   - https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#merge_group
2. GitHub rulesets “most restrictive wins” behavior aligns with no-downgrade governance layering:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
3. GitHub merge queue required-check caution on branch/path filtering:
   - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
4. AWS Step Functions terminal-state + retry/catch model supports “terminal semantics over historical noise” reasoning design:
   - https://docs.aws.amazon.com/step-functions/latest/dg/workflow-states.html
   - https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html

### T4 Protocol reference replay (local code anchors)

1. `scripts/required_gate_bundle_runner.py`
2. `scripts/validate_multimodal_plugin_enforcement.py`
3. `scripts/validate_reasoning_loop_failclose.py`
4. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
5. `identity/protocol/mappings/contract-binding.current.yaml`

### T5 Context7 track

1. MCP lifecycle/capability negotiation and tools list-change semantics support explicit, machine-negotiated plugin capability control:
   - `/modelcontextprotocol/specification` (initialize/capabilities/tools/list_changed)
2. GitHub Actions workflow trigger semantics from Context7 mirror official merge-queue trigger requirements:
   - `/websites/github_en_actions` (`merge_group` event usage).

## 5) v1.6.4 implementation targets (code phase)

Code phase starts only after this governance freeze is accepted.

1. Add monotonic-level policy config (floor + upgrade-only) and wire it to strict validators.
2. For strict operations, reasoning bundle invocation must always propagate run-id semantics consistently.
3. For strict operations, multimodal runtime-proof defer must not be interpreted as silent pass for done-transition-eligible paths.
4. Add AI folder governance plugin as a standard plugin-join template requirement row.
5. Keep all changes configuration-driven; no per-instance hardcoded policy in protocol scripts.

## 6) Release gate for v1.6.4 claim

No “v1.6.4 closed” claim is valid unless all items pass:

1. `scripts/validate_control_plane_invariants.py --json-only`
2. `scripts/validate_required_gate_surface_drift.py --json-only`
3. `scripts/validate_control_plane_status_sync.py --json-only`
4. `scripts/docs_command_contract_check.py`
5. `scripts/full_identity_protocol_scan.py --scan-mode target` with strict profile and explicit actor/session binding
6. Negative probes:
   - strict lane downgrade attempt must fail-close
   - strict lane `run_id` mismatch must fail-close for required reasoning runtime-proof
   - strict lane unresolved multimodal evidence cannot be promoted to done-transition-safe status

## 7) Alias continuity (mandatory)

This stream is governed under:

1. `identity/protocol/mappings/stream-doc-registry.current.yaml`
2. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
3. `identity/protocol/mappings/contract-binding.current.yaml`
4. `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`

If any alias pointer drifts, current-state judgment is invalid until repaired.
