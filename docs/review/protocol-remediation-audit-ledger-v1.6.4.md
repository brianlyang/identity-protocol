# Protocol Remediation Audit Ledger (v1.6.4 monotonic fail-close stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review ledger for v1.6.4 semantic hardening (config-first standard flow, upgrade-only levels, newcomer-safe continuity).

Companion governance SSOT:

1. `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
2. `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml`
4. `identity/protocol/mappings/contract-binding.current.yaml`
5. `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`

## State interpretation guard

1. This file records review posture and replay checkpoints.
2. Normative contract semantics remain in the companion governance document.
3. If this ledger conflicts with governance SSOT, this ledger is stale.

## 0) Baseline replay (2026-03-11)

Machine status snapshot:

1. `validate_control_plane_invariants` => `PASS_REQUIRED`
2. `validate_required_gate_surface_drift` => `PASS_REQUIRED`
3. `validate_control_plane_status_sync` => `PASS_REQUIRED`
4. `docs_command_contract_check` => `PASS`
5. v1.6.4 strict-doc evidence policy is closed by allowlist registration:
   `identity/protocol/mappings/doc-evidence-allowlist.current.yaml` includes both stream docs.

Observed semantic gaps (to be fixed in code phase):

1. Multimodal runtime-proof defer can still keep top-level pass in strict lanes under some report shapes.
2. Reasoning effective level can remain `L1` by default without explicit floor promotion.
3. Required-gate reasoning path can skip run-id propagation when no explicit report path is given.

## 0.1 Discussion alignment snapshot (2026-03-11)

This round records cross-verified discussion conclusions and freezes them as v1.6.4 planning constraints.

1. Four core items are locked as stream-level non-negotiable scope:
   - config-first standard flow
   - upgrade-only (no-downgrade) monotonic enforcement
   - newcomer/memory-loss-safe unique-entry control
   - dual exemplar plugins for reusable onboarding.
2. Dual exemplar plugins are explicitly in-scope for planning:
   - AI folder governance plugin (runtime boundary + pointerized references)
   - AI search plugin (provider-pluggable, configuration-driven, no protocol hardcoding).
3. AI search provider strategy is frozen as profile-based replaceable wiring:
   - BigModel web-search can be first provider reference
     (`https://docs.bigmodel.cn/cn/guide/tools/web-search`)
   - provider replacement must not require protocol contract rewrites.
4. This stream phase is documentation-first:
   - no validator/business script changes are claimed in this checkpoint.
   - code-phase starts only after governance/review docs are accepted.

## 0.2 First-contract closure verdict (2026-03-11)

Verdict: `Policy PASS / Implementation CONDITIONAL PASS`.

Independent cross-check (repo-local) confirms two mandatory hardening gaps before first-contract can be called machine-closed:

1. Schema-contract mismatch exists:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml` carries the minimum tuple fields.
   - `identity/protocol/plugins/schemas/plugin-registry.schema.json` still rejects those tuple fields.
2. Bundle runner still has static requirement/target/status maps:
   - `BUNDLE_REQUIREMENT_ORDER`
   - `TARGET_NAME_BY_REQUIREMENT`
   - `STATUS_FIELD_BY_TARGET`
   New plugin onboarding can still require script edits, which conflicts with config-first-only intent.

Action freeze for this item:

1. Promote tuple parity to schema+validator fail-close.
2. Move plugin onboarding path away from static map additions to mapping-driven derivation.

## 0.3 First-contract code-sync closure (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (plugin-failclose scope)`.

Code-sync confirmation:

1. Schema-contract parity is machine-closed:
   - `identity/protocol/plugins/schemas/plugin-registry.schema.json`
   - fail-close rows now require minimum tuple and active status.
2. Validator fail-close is wired:
   - `scripts/validate_control_plane_invariants.py`
   - plugin registry now runs schema validation and tuple-missing hard fail.
3. Bundle runner plugin onboarding decoupling is in place:
   - `scripts/required_gate_bundle_runner.py`
   - fail-close plugin requirement/target/status mapping can be derived from registry + contract-binding without adding plugin-specific static maps.
4. Operational playbook wording is aligned to implemented behavior:
   - `identity/protocol/plugins/README.md`

## 0.4 Second-item monotonic no-downgrade closure (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (strict no-skip + floor enforcement)`.

Cross-verified hardening landed:

1. Central monotonic policy is now profile-configured:
   - `identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml`
   - per-plugin `monotonic_policy` includes floor + downgrade + strict-skip policy.
2. Bundle strict no-skip is machine-enforced:
   - `scripts/required_gate_bundle_runner.py`
   - strict required rows with `SKIPPED_NOT_REQUIRED` now fail-close unless stale reasons are
     explicitly allowlisted in policy.
3. Reasoning floor and receipt semantics are strengthened:
   - `scripts/validate_reasoning_loop_failclose.py`
   - governance-backed monotonic policy read-path + receipt fields for configured/effective/minimum levels
     and downgrade policy flags.
4. Multimodal defer semantics are tightened on terminal strict lanes:
   - `scripts/validate_multimodal_plugin_enforcement.py`
   - terminal strict operations cannot pass with runtime evidence `SKIPPED_NOT_REQUIRED`.
5. Mapping/projection parity updated for new monotonic receipt fields:
   - `identity/protocol/mappings/contract-binding.v1.6.yaml`

Acceptance notes:

1. This closure removes the implicit downgrade channel for strict required gates.
2. Single-intake generation moved out of backlog and into machine wiring closure (see section 0.6).
3. Hardening keeps control-plane budget convergence stable by reusing existing error-code families
   (`IP-RL-CONF-001`, `IP-MM-RUN-003`) instead of introducing new literal codes.

## 0.5 Release-gate monotonic probes wiring closure (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (release lane wired)`.

Closure details:

1. CI now runs dedicated monotonic probes via:
   - `scripts/ci/run_monotonic_floor_probes_ci.sh`
   - workflow hook:
     `.github/workflows/_identity-required-gates.yml` (`Validate monotonic floor probes (v1.6.4)`).
2. Probe suite is machine-fixed to three outcomes:
   - `reasoning_floor_l0_fail` => strict downgrade blocked (`FAIL_REQUIRED`)
   - `multimodal_update_defer_allowed` => pre-mutation defer allowed (`PASS_REQUIRED`)
   - `multimodal_readiness_skip_blocked` => terminal strict skip blocked (`FAIL_REQUIRED`).
3. Probe run emits machine evidence manifest (sha256/command/rc/timestamp) at runtime:
   - `${RUNNER_TEMP}/identity-monotonic-floor-probes/manifest.monotonic_floor_probes.json`
4. Surface-drift anti-bypass is extended:
   - `scripts/validate_required_gate_surface_drift.py` now requires
     `scripts/ci/run_monotonic_floor_probes_ci.sh` to stay wired and checks probe command tokens.

## 0.6 First-item single-intake wiring closure (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (single-entry plugin join)`.

Closure details:

1. Single authoring pointer is active:
   - `identity/protocol/plugins/PLUGIN_JOIN_INTAKE.current.yaml`
   - `identity/protocol/plugins/PLUGIN_JOIN_INTAKE.v1.6.4.yaml`
2. Intake compiler/check is executable and fail-close:
   - `scripts/sync_plugin_join_wiring.py --check --json-only`
   - checks parity across intake, plugin registry, fail-close governance, and contract-binding mapping.
3. CI required-gates delegate now enforces intake parity pre-loop:
   - `scripts/ci/run_required_runtime_gates_ci.sh`
4. Plugin onboarding docs are aligned to single-entry flow:
   - `identity/protocol/plugins/README.md`
   - `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.v1.6.2.md`
   - `identity/protocol/plugins/PLUGIN_DOC_CONTROL.v1.6.2.yaml`

## 0.7 Third-item newcomer/memory-loss closure cross-verify (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (entry continuity + tuple parity closed)`.

Roundtable replay (repo-local):

1. `python3 scripts/docs_command_contract_check.py` => `PASS`.
2. `python3 scripts/validate_control_plane_invariants.py --json-only` => `PASS_REQUIRED`.
3. `python3 scripts/sync_plugin_join_wiring.py --check --json-only` => `PASS_REQUIRED`.
4. Closure payload facts:
   - `intake_row_count=2` on `PLUGIN_JOIN_INTAKE.v1.6.4.yaml` (strict plugin rows materialized).
   - no parity violations across intake, registry, governance, and contract-binding.

## 0.8 Unique Protocol Ingress Core Closure (2026-03-12)

Verdict: `Policy PASS / Implementation PASS (machine-enforced unique ingress contract)`.

Closure details:

1. Unique-ingress contract validator is added:
   - `scripts/validate_protocol_unique_entry_gate.py`
   - validates one frozen ingress script/key pair:
     - `scripts/required_gate_bundle_runner.py`
     - `required_gate_bundle_runner`
2. Required-contract coverage gate now includes unique-ingress target:
   - `scripts/validate_required_contract_coverage.py`
   - strict lanes fail-close when unique-ingress contract is missing/invalid.
3. Legacy instance upgrade path now auto-backfills unique-ingress contract:
   - `scripts/repair_contract_backfill.py --apply --json-only`
   - adds `protocol_unique_entry_gate_contract_v1` to `CURRENT_TASK.json`.
4. New identity scaffold defaults now include unique-ingress contract:
   - `scripts/create_identity_pack.py`
5. Governance SSOT is updated with explicit unique-ingress freeze:
   - `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`

Acceptance probes (repo-local):

1. Backfill before/after proves closure:
   - before: `validate_protocol_unique_entry_gate` -> `FAIL_REQUIRED` (`unique_entry_contract_missing`)
   - after: `repair_contract_backfill --apply` + validator -> `PASS_REQUIRED`.
2. This closure is protocol-core only:
   - no business-repo specific script is normative ingress.

Cross-track interpretation:

1. T1 Roundtable:
   - entry pointers and command contracts are stable and machine-checkable.
2. T2 Vendor (OpenAI):
   - strict schema-first guidance supports newcomer-safe deterministic entry contracts.
3. T3 Network (GitHub):
   - required checks + rulesets reinforce “memory-independent guardrails” pattern.
4. T4 Protocol reference:
   - `scripts/docs_command_contract_check.py`
   - `scripts/validate_control_plane_invariants.py`
   - `scripts/sync_plugin_join_wiring.py`
   - `scripts/validate_protocol_feedback_bootstrap_ready.py`
   - `scripts/validate_protocol_entry_candidate_bridge.py`

Action lock for third-item full closure:

1. Keep section 3.3.4 cold-start replay chain green in CI regression lanes.
2. Keep `sync_plugin_join_wiring.py` as tuple-parity fail-close (no downgrade to alias-only checks).

## 0.8 Integration-kind fixed-directory decision freeze (2026-03-11)

Verdict: `Policy PASS / Implementation PASS (schema + intake + parity + invariants)`.

Decision locked for v1.6.4:

1. Plugin architecture keeps one lightweight intake, but directories are protocol-fixed by `integration_kind`.
2. Three canonical roots are frozen:
   - `skill`: `identity/protocol/plugins/skill` + `.identity/{identity_id}/runtime/plugins/skills`
   - `mcp`: `identity/protocol/plugins/mcp` + `.identity/{identity_id}/runtime/plugins/mcp`
   - `api`: `identity/protocol/plugins` + `.identity/{identity_id}/runtime/plugins/api`
3. Non-canonical roots are governance drift and now fail-close in machine checks.
4. File-management skill reference is accepted as lightweight seed pattern (instance-side install):
   - `https://github.com/ComposioHQ/awesome-claude-skills/blob/master/file-organizer/SKILL.md`

Implementation closure:

1. Intake rows now carry fixed-root fields:
   - `identity/protocol/plugins/PLUGIN_JOIN_INTAKE.v1.6.4.yaml`
2. Registry rows now carry fixed-root fields:
   - `identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml`
3. Registry schema now enforces `integration_kind` with fixed root constants:
   - `identity/protocol/plugins/schemas/plugin-registry.schema.json`
4. Intake parity checker fail-closes integration-root drift:
   - `scripts/sync_plugin_join_wiring.py`
5. Control-plane invariant scan fail-closes integration-root drift:
   - `scripts/validate_control_plane_invariants.py`

Replay evidence (this round):

1. Self-tests (5 scenarios):
   - positive parity pass: `sync_plugin_join_wiring --check` => `PASS_REQUIRED`
   - negative probes (invalid kind / wrong protocol root / contract out-of-root / registry runtime root mismatch)
     all return `FAIL_REQUIRED`
2. Deep scans (5 validators):
   - `validate_control_plane_invariants --json-only` => `PASS_REQUIRED`
   - `validate_required_gate_surface_drift --json-only` => `PASS_REQUIRED`
   - `validate_control_plane_status_sync --json-only` => `PASS_REQUIRED`
   - `validate_control_plane_budget --json-only` => `PASS_REQUIRED`
   - `docs_command_contract_check` => `PASS`

## 1) Four-track + context verification summary

### T1 Roundtable/internal replay

1. Target scan confirms strict control-plane checks are wired and replayable.
2. Residual risk is semantic hardness consistency, not missing base pointers.

### T2 Vendor (OpenAI)

1. Codex approvals/sandbox/network control guidance supports strict controlled execution.
2. Codex GitHub Action security checklist supports narrow trigger + secret hygiene.
3. Function-calling strict mode and structured outputs guidance support schema-hard enforcement expectations.

### T3 Network references

1. GitHub merge queue requires `merge_group`-compatible checks.
2. GitHub rulesets enforce restrictive composition patterns useful for no-downgrade strategy.
3. AWS Step Functions terminal/retry semantics align with terminal-state-centric reasoning closure.

### T4 Protocol reference anchors

1. `scripts/required_gate_bundle_runner.py`
2. `scripts/validate_multimodal_plugin_enforcement.py`
3. `scripts/validate_reasoning_loop_failclose.py`

### T5 Context7

1. MCP capability negotiation/tool notification semantics support explicit plugin capability contracts.
2. Context7 GitHub Actions corpus confirms `merge_group` trigger usage pattern.

## 2) Implementation acceptance checklist (v1.6.4)

1. Monotonic level floor is configuration-driven and enforced.
2. Strict lane reasoning path propagates run-id semantics consistently.
3. Strict lane multimodal path cannot silently pass with non-materialized runtime proof when done-transition safety is claimed.
4. AI folder governance plugin template is added via standard plugin-join flow (registry + governance + mapping + bundle).
5. All stream docs and aliases stay machine-consistent via `docs_command_contract_check`.
6. AI search plugin template is added with provider-pluggable runtime bindings and evidence projection fields.
7. Third-item newcomer replay chain (governance section 3.3.4) is green and reproducible from current pointers only.
8. `PLUGIN_JOIN_INTAKE` carries active rows for all strict fail-close plugins; zero-row intake is not accepted for final closure.

## 3) Residual risk after code-phase closure

1. No blocking residual risk remains for v1.6.4 fixed-directory integration-kind closure.
2. Future exemplar plugin expansion (`ai-folder-governance`, `ai-search`) should continue as
   config-first onboarding and is tracked as stream evolution, not v1.6.4 closure blocker.

## 4) Current posture

Posture: `GO` for v1.6.4 code-phase closure.

Reason:

1. Control-plane foundations are strong and stable.
2. Integration-kind fixed-directory rules are now machine-enforced in intake parity, schema, and invariants.
3. 5 self-tests + 5 deep scans completed with expected pass/fail semantics.

## 5) Round-31.1 addendum: monotonic probe wrapper-policy isolation (2026-03-14)

1. Problem:
   - `scripts/ci/run_monotonic_floor_probes_ci.sh` fixture started inheriting host-gateway
     wrapper-default mapping errors (`host_gateway_contract_missing`) after wrapper policy became
     mandatory in `required_gate_bundle_runner`.
   - This polluted monotonic-floor probe semantics with unrelated wrapper provenance failures.
2. Fix:
   - probe fixture now injects a minimal `protocol_host_unique_channel_contract_v1` contract
     for `probe-mm`, with explicit operation-profile and `host_dispatch_mode=advisory`.
   - result: monotonic probes test multimodal/reasoning floor behavior only, not host-wrapper policy debt.
3. Replay:
   - `reasoning_floor_l0_fail` => rc=1 (expected)
   - `multimodal_update_defer_allowed` => rc=0 (expected)
   - `multimodal_readiness_skip_blocked` => rc=1 (expected)
   - manifest emitted at runtime temp root:
     `identity-monotonic-floor-probes/manifest.monotonic_floor_probes.json`.
