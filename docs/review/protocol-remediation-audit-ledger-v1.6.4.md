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

## 3) Residual risk before code-phase closure

1. If monotonic floor remains documentation-only, downgrade risk remains.
2. If run-id propagation remains conditional in reasoning strict paths, fallback ambiguity remains.
3. If multimodal defer semantics remain too permissive in strict done-transition contexts, user-perceived enforcement weakness remains.
4. If AI search onboarding is provider-hardcoded instead of profile-driven, plugin extensibility will regress.

## 4) Current posture

Posture: `CONDITIONAL_GO` for code-phase hardening.

Reason:

1. Control-plane foundations are strong and stable.
2. v1.6.4 semantic tightening items are clearly scoped and ready for implementation.
3. No further stream sprawl is needed; this stream should close with focused validator/policy hardening only.
