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

#### 3.1.1 Schema-contract parity (mandatory)

The minimum wiring tuple is not documentation-only. It must be machine-enforced as a three-way contract:

1. Documentation contract:
   - `plugin_id`, `requirement_key`, `bundle_target_name`, `gate_mode`, `ssot_mapping_ref`
2. Schema contract:
   - plugin registry schema must allow and validate the same tuple fields.
   - tuple fields must be required for fail-close plugin rows.
3. Validator contract:
   - at least one required gate must fail-close when schema/tuple parity is broken.

If documentation tuple and schema tuple diverge, this contract is `FAIL_REQUIRED` by design.

#### 3.1.2 Bundle runner decoupling rule (mandatory)

New plugin onboarding must not require adding plugin-specific static maps in bundle runner source.

1. Disallowed onboarding pattern:
   - extending hardcoded lookup maps for requirement->target->status as primary wiring path.
2. Required onboarding pattern:
   - derive wiring from mapping sources (`contract-binding` + plugin registry/governance metadata).
3. Any new plugin that can only be wired by editing bundle runner static maps is considered a control-plane regression.

#### 3.1.3 Single-intake + generated wiring contract (machine-wired mandatory)

Human onboarding must converge to one intake record, while control-plane audit remains layered:

1. Canonical intake:
   - one plugin-join row per plugin (minimum tuple + strict surfaces + report projection contract).
2. Generated artifacts:
   - registry/governance/contract-binding rows are generated from intake, not manually diverged.
3. Drift gate:
   - `scripts/sync_plugin_join_wiring.py --check --json-only` must fail-close when generated artifacts differ from intake intent.
4. Editing boundary:
   - generated files are not the primary authoring surface for new plugin join requests.

Current implementation boundary (v1.6.4):

1. Single authoring pointer: `identity/protocol/plugins/PLUGIN_JOIN_INTAKE.current.yaml`
2. Compiler/check tool: `scripts/sync_plugin_join_wiring.py`
3. Required-gate CI delegate must run intake parity check:
   `scripts/ci/run_required_runtime_gates_ci.sh`

Rationale:

1. Keep audit-safe layered governance model.
2. Deliver single-entry operator experience (`add one row` instead of hand-editing multiple files).
3. Remove tribal-memory dependency for newcomers and memory-loss scenarios.

#### 3.1.4 Integration-kind directory freeze (mandatory, no ambiguity)

To keep instance onboarding lightweight while preventing path drift, plugin integration kinds are fixed to one directory contract each:

| integration_kind | protocol_contract_root (fixed) | instance_runtime_root (fixed) |
|---|---|---|
| `skill` | `identity/protocol/plugins/skill` | `.identity/{identity_id}/runtime/plugins/skills` |
| `mcp` | `identity/protocol/plugins/mcp` | `.identity/{identity_id}/runtime/plugins/mcp` |
| `api` | `identity/protocol/plugins` | `.identity/{identity_id}/runtime/plugins/api` |

Hard rules:

1. Every fail-close plugin row must carry:
   - `integration_kind`
   - `protocol_contract_root`
   - `instance_runtime_root`
2. `contract_file` must stay within the declared `protocol_contract_root`.
3. Any non-canonical root (including ad-hoc folders) is `FAIL_REQUIRED`.
4. This freeze is protocol-level and applies to both:
   - newcomer onboarding
   - memory-loss replay scenarios

Operator intent (lightweight by design):

1. Humans still add one intake row.
2. Machines enforce fixed roots and projection parity.
3. Instance owners install/attach capabilities under fixed runtime roots only.

### 3.2 Monotonic level contract (allow upgrade, forbid downgrade)

1. Each strict contract must define an effective enforcement floor.
2. Execution may self-upgrade to stronger level when stronger evidence is available.
3. Execution must fail-close when reported effective level is below configured floor.
4. For strict operations (`activate`, `update`, `mutation`, `readiness`, `e2e`, `ci`, `validate`, `three-plane`):
   - top-level required contracts must not resolve to silent downgrade semantics.
   - `SKIPPED_NOT_REQUIRED` is only valid for declared non-applicable contexts (for example fixture/demo profiles), and must carry explicit reason.

#### 3.2.1 Machine wiring contract (second-item hard-close)

Monotonic no-downgrade is not documentation-only. It is now wired through plugin governance + runtime validators:

1. Canonical policy source:
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
   - per plugin profile fields:
     - `monotonic_policy.minimum_enforcement_level`
     - `monotonic_policy.allow_self_upgrade`
     - `monotonic_policy.allow_downgrade`
     - `monotonic_policy.strict_skip_policy`
     - `monotonic_policy.strict_skip_allowed_reasons`
2. Bundle strict no-skip gate:
   - `scripts/required_gate_bundle_runner.py` must fail-close strict required rows when
     `status=SKIPPED_NOT_REQUIRED` and skip policy is `fail_close/strict_no_skip/forbid_skip`,
     unless stale reasons are explicitly allowlisted.
3. Reasoning floor enforcement:
   - `scripts/validate_reasoning_loop_failclose.py` must fail-close when strict operation effective
     level is below floor and downgrade is not allowed.
   - receipt fields must include:
     - `reasoning_configured_level`
     - `reasoning_effective_level`
     - `reasoning_minimum_enforcement_level`
     - `reasoning_allow_self_upgrade`
     - `reasoning_allow_downgrade`
     - `reasoning_downgrade_block_status`
4. Multimodal strict defer boundary:
   - `scripts/validate_multimodal_plugin_enforcement.py` may defer only for declared pre-mutation
     operations.
   - terminal strict surfaces (`readiness/ci/three-plane/e2e/validate/activate/mutation`) must not
     pass with `multimodal_runtime_evidence_status=SKIPPED_NOT_REQUIRED`.
5. Error-code convergence boundary:
   - monotonic/no-skip hardening must reuse existing error-code families when semantics fit.
   - introducing new literal error codes for equivalent failure families is disallowed when it
     causes control-plane budget rebound.

### 3.3 Newcomer/memory-loss safety contract

Protocol control must be understandable and executable without relying on personal memory:

1. Stream docs are machine-registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`.
2. Mandatory alias references are machine-checked by `scripts/docs_command_contract_check.py`.
3. Plugin onboarding is machine-token-checked by:
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`
   - `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`.
4. If a new engineer follows only current-pointer files, they must be able to wire a new contract without hidden tribal knowledge.

#### 3.3.1 Unique-entry surface contract (mandatory)

To avoid memory-dependent routing, v1.6.4 freezes a unique-entry surface built from current-pointer files only:

1. `identity/protocol/mappings/stream-doc-registry.current.yaml`
2. `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`
3. `identity/protocol/plugins/PLUGIN_DOC_CONTROL.current.yaml`
4. `identity/protocol/plugins/PLUGIN_JOIN_INTAKE.current.yaml`

Hard boundary:

1. Any onboarding or protocol remediation instruction outside this unique-entry surface is non-normative.
2. Any document claiming canonical onboarding must reference these pointers or is treated as stale.

#### 3.3.2 Mandatory orientation contract (newcomer-safe)

Cold-start orientation must be reproducible in the same sequence, without tribal memory:

1. Resolve active stream docs from `stream-doc-registry.current.yaml`.
2. Resolve active plugin onboarding playbook from `PLUGIN_WIRING_PLAYBOOK.current.md`.
3. Run `python3 scripts/docs_command_contract_check.py`.
4. Run `python3 scripts/validate_control_plane_invariants.py --json-only`.
5. Run `python3 scripts/sync_plugin_join_wiring.py --check --json-only`.

Fail-close rule:

1. Any failure above blocks “ready-to-edit protocol control-plane” claim.

#### 3.3.3 Mutation-through-entry contract (anti-bypass)

Protocol edits must be auditable from the unique-entry surface:

1. Direct edits to plugin/mapping targets without pointer-chain consistency are invalid.
2. Drift is judged by machine gates (`docs_command_contract_check` + control-plane invariants), not by reviewer memory.
3. Required-gate CI must keep intake check wired in `scripts/ci/run_required_runtime_gates_ci.sh`.

#### 3.3.4 Cold-start replay contract (machine proof)

A memory-loss scenario is considered closed only when this replay is green:

1. `python3 scripts/docs_command_contract_check.py`
2. `python3 scripts/validate_control_plane_invariants.py --json-only`
3. `python3 scripts/sync_plugin_join_wiring.py --check --json-only`
4. `python3 scripts/validate_protocol_feedback_bootstrap_ready.py --identity-id <id> --catalog <path> --operation ci --force-check --json-only`
5. `python3 scripts/validate_protocol_entry_candidate_bridge.py --identity-id <id> --catalog <path> --operation ci --force-check --json-only`

Interpretation:

1. The first three commands validate protocol-level entry continuity.
2. The last two commands validate instance-side entry/feedback bridge continuity.
3. All five must pass before claiming newcomer-safe closure.

### 3.4 Dual exemplar plugins (AI folder governance + AI search)

v1.6.4 defines two exemplar plugins so that teams can copy a reusable pattern instead of inventing per-instance wiring:

1. AI folder governance plugin (protocol hygiene/control-plane plugin, not business logic plugin).
2. AI search plugin (provider-pluggable capability plugin, not provider-hardcoded script logic).

#### 3.4.1 AI folder governance plugin intent

1. Enforce canonical runtime directory boundaries.
2. Block non-canonical ad-hoc AI artifact roots in strict lanes.
3. Require deterministic pointer-based references instead of scattered literal paths.
4. Skill baseline is frozen to a lightweight file-organizer pattern:
   - reference seed:
     `https://github.com/ComposioHQ/awesome-claude-skills/blob/master/file-organizer/SKILL.md`
   - protocol scope only governs contract and evidence projection;
     instance installation stays instance-side under fixed runtime roots.

#### 3.4.2 AI search plugin intent

1. Provide a standard protocol plugin contract for web-search evidence intake.
2. Keep provider selection configuration-driven (`provider_profile_id` + runtime binding), not protocol-script hardcoded.
3. Support provider evolution without contract rewrites:
   - initial reference provider can be BigModel web-search:
     `https://docs.bigmodel.cn/cn/guide/tools/web-search`
   - alternate providers can be added/replaced by profile binding only.
4. Require search evidence projection fields before promotion:
   - provider/model profile used
   - query and attempt metadata
   - source URL references and freshness status
   - conflict resolution evidence when multiple sources disagree

#### 3.4.3 Shared join path (both exemplar plugins)

1. Register by `plugin_id + requirement_key + bundle_target_name + gate_mode + ssot_mapping_ref`.
2. Add projection/report fields before promotion.
3. Pass required-gate bundle and drift guards before release claim.

## 4) Cross-verification (roundtable + vendor + network + reference + context7)

### T1 Roundtable (repo-machine replay)

1. `validate_control_plane_invariants` and `validate_required_gate_surface_drift` are `PASS_REQUIRED`.
2. `full_identity_protocol_scan --scan-mode target` confirms:
   - fixture target can hold `p0=0` in strict profile replay.
   - non-fixture target still exposes binding-quality gaps if actor-session is not correctly pre-bound (operational, not semantic contract absence).
3. Projection replay confirms current weak-feel source:
   - multimodal can pass with deferred runtime-proof projection fields in strict flow.
4. Third-item newcomer chain replay is now explicitly commandized in section 3.3.4 and anchored to existing validators.

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
4. Add dual exemplar plugins as standard plugin-join template requirement rows:
   - AI folder governance plugin
   - AI search plugin (provider-pluggable, no hardcoded vendor in protocol scripts).
5. Keep all changes configuration-driven; no per-instance hardcoded policy in protocol scripts.
6. Third-item unique-entry closure is machine-closed (2026-03-11):
   - `PLUGIN_JOIN_INTAKE` must carry non-empty plugin rows for active fail-close plugins.
   - `sync_plugin_join_wiring --check` validates cross-plane parity (registry/governance/mapping), not only alias existence.
7. Promote newcomer cold-start replay into CI delegate form once stable:
   - compose section 3.3.4 commands into one deterministic CI lane for regression use.

## 6) Release gate for v1.6.4 claim

No “v1.6.4 closed” claim is valid unless all items pass:

1. `scripts/validate_control_plane_invariants.py --json-only`
2. `scripts/validate_required_gate_surface_drift.py --json-only`
3. `scripts/validate_control_plane_status_sync.py --json-only`
4. `scripts/docs_command_contract_check.py`
5. `scripts/full_identity_protocol_scan.py --scan-mode target` with strict profile and explicit actor/session binding
6. `scripts/ci/run_monotonic_floor_probes_ci.sh`
7. Negative probes (machine-enforced by item 6):
   - strict lane downgrade attempt must fail-close (`reasoning_floor_l0_fail`)
   - strict lane update may defer pre-mutation runtime stage (`multimodal_update_defer_allowed`)
   - strict lane terminal readiness cannot pass deferred skip (`multimodal_readiness_skip_blocked`)
8. Third-item newcomer replay baseline (from section 3.3.4) is green in strict profile.

## 7) Alias continuity (mandatory)

This stream is governed under:

1. `identity/protocol/mappings/stream-doc-registry.current.yaml`
2. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
3. `identity/protocol/mappings/contract-binding.current.yaml`
4. `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`

If any alias pointer drifts, current-state judgment is invalid until repaired.
