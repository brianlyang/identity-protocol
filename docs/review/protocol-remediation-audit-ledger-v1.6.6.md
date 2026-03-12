# Protocol Remediation Audit Ledger (v1.6.6 host-channel stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review ledger for project-side identity runtime ingress/egress closure and per-instance wrapper enforcement.

Companion governance SSOT:

1. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
2. `identity/protocol/mappings/stream-doc-registry.current.yaml`
3. `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
4. `identity/protocol/mappings/contract-binding.current.yaml`
5. `identity/protocol/mappings/control-plane-invariants.current.yaml`
6. `identity/protocol/mappings/control-plane-status.current.yaml`

## State interpretation guard

1. This file records review posture and replay checkpoints.
2. Normative contract semantics remain in companion governance SSOT.
3. If this ledger conflicts with governance SSOT or current-pointer mappings, this ledger is stale.

## State boundary lock (anti-misread)

1. `host-channel` in v1.6.6 is a stream label, not a requirement to modify unrelated external repositories.
2. Canonical layer naming for this stream is fixed:
   - protocol base repository: `identity-protocol-local`
   - business project repository: `<project>` (for example `weixinstore`)
   - identity instance pack: `<project>/.identity/<identity_id>/`
3. Instance source layers include both project and global roots, and review must accept both:
   - project-layer pack under `<project>/.identity/<identity_id>/...`
   - global-layer pack under `${CODEX_HOME}/.identity/<identity_id>/...`
4. This stream validates **project-side runtime adapter + instance pack wrapper** closure.
5. Wrapper materialization scope is `.identity/{identity_id}/runtime/gate/*` with declaration in `CURRENT_TASK.json`.

## 0) Baseline posture at stream opening (2026-03-12)

Machine baseline retained from active control-plane checks:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`

Semantic baseline confirmed at opening:

1. Protocol strict-surface ingress/egress contracts exist and are machine-checkable.
2. Unique-entry contract is declared in instance `CURRENT_TASK.json` and validator chain exists.
3. Residual risk remains at project runtime session entrypoints if dispatch bypasses wrapper contract.

Opening verdict: `Policy PASS / Implementation CONDITIONAL PASS`.

## 1) Review focus for v1.6.6

1. Freeze one host-channel contract with no ambiguous alternates.
2. Ensure per-instance wrapper generation is mandatory, deterministic, and replayable.
3. Ensure project runtime dispatch/release paths are wrapper-only in strict operations.
4. Preserve protocol-instance layer split while closing runtime bypasses.
5. Ensure project non-mutation conversation rounds are also wrapper-enforced.

## 2) Four-track cross-verification summary

### 2.1 Track A - Roundtable/local replay

1. Required-gate drift validator enforces canonical bundle entry and egress wrapper surfaces.
2. Unique-entry validator enforces contract keys and receipt parity on strict operations.
3. Existing fleet replay indicates bypass blocking can be proven when dispatch path is aligned.

### 2.2 Track B - Vendor references

1. Boundary enforcement model aligns with OpenAI security model (sandbox + approvals).
2. Strict schema-first principle aligns with fail-close gateway contracts.

### 2.3 Track C - Network/platform references

1. GitHub required-check and merge-group model supports centralized enforcement and anti-bypass lanes.
2. Ruleset model supports policy centralization while leaving semantic checks inside protocol validators.

### 2.4 Track D - Protocol references

1. `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
2. `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
3. `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`
4. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`

## 3) Implementation checklist (review posture)

### 3.1 Protocol side

1. `identity_creator` init/update path writes deterministic wrapper contract fields into `CURRENT_TASK.json`.
2. Wrapper generation targets are fixed and auditable:
   - `.identity/{identity_id}/runtime/gate/protocol_ingress_wrapper.py`
   - `.identity/{identity_id}/runtime/gate/protocol_egress_wrapper.py`
   - `.identity/{identity_id}/runtime/gate/protocol_gateway_contract.json`
3. Unique-entry validator scope includes strict-operation receipt parity.
4. Generated `protocol_gateway_contract.json` must satisfy governance required fields:
   - canonical ingress/egress script references
   - tuple propagation keys (`actor_id`, `session_id`, `run_id`, `work_layer`, `source_layer`)
   - explicit receipt policies for ingress and egress

### 3.2 Project runtime side

1. Inbound dispatch goes through ingress wrapper before execution handoff.
2. User-visible outbound release goes through egress wrapper before send.
3. Egress release verifies ingress receipt parity for current turn:
   - same `run_id`
   - same `session_id`
   - same `actor_id`
4. Direct dispatch/release paths without wrapper/receipt are blocked with fail-close status.
5. Project non-mutation rounds still require wrapper traversal and egress headstamp/send-time pass.
6. Project wrapper discovery order must follow governance (runtime declaration first, then deterministic runtime file; no implicit mono-repo fallback).

### 3.3 Cross-repo interoperability

1. Protocol repo and instance repo may be different roots.
2. Wrapper contract resolves protocol path mapping explicitly.
3. No hidden same-repo relative-path dependency is allowed.

### 3.4 Stream numbering and PR lifecycle binding

1. v1.6.6 must be present in `identity/protocol/mappings/stream-doc-registry.current.yaml` resolved file.
2. Governance and review docs must remain paired with one stream version (no orphan stream docs).
3. Every implementation round must produce:
   - `activity/evidence/v166-host-channel/<date>/stream_pr_binding.json`
4. PR binding receipt required fields:
   - `stream_version`
   - `repository`
   - `pull_request_number`
   - `pull_request_url`
   - `head_branch`
   - `base_branch`
   - `head_sha`
   - `merge_status`
   - `opened_at_utc`
5. If PR binding receipt is missing or stale to current head SHA, posture remains `CONDITIONAL_GO`.

### 3.5 Serial replay matrix (minimum, no parallel substitution)

To avoid "policy green but runtime bypass" false confidence, review requires serial replay of at least:

1. Strict `validate` operation replay with wrapper-only dispatch/release.
2. Strict mutation-class replay (`update` or equivalent) with entry receipt parity.
3. Non-mutation conversation replay proving wrappers still mandatory.
4. Negative probe: direct dispatch bypass attempt must fail-close.
5. Negative probe: direct release bypass attempt must fail-close.

### 3.6 YAML sprawl control check

1. v1.6.6 stream registration must reuse existing mapping YAML files.
2. Review must fail if stream onboarding introduces unnecessary new mapping YAML files for registry/allowlist scope.
3. Current accepted files:
   - `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`

## 4) Acceptance criteria

Implementation is not accepted unless all items pass:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_protocol_unique_entry_gate.py --catalog <catalog> --identity-id <id> --operation validate --require-entry-receipt --json-only`
4. `python3 scripts/docs_command_contract_check.py`
5. Project replay confirms wrapper-only dispatch and wrapper-only release for strict operations.
6. Stream PR binding receipt exists and matches stream version + head SHA.
7. Project replay confirms wrapper-only dispatch and wrapper-only release for non-mutation conversation rounds.
8. Negative probe (`direct dispatch -> direct release`) is `FAIL_REQUIRED`.
9. Serial replay matrix in 3.5 is fully executed and recorded in persistent evidence.
10. Evidence package contains:
    - `stream_pr_binding.json`
    - `wrapper_contract_snapshot.<identity_id>.json`
    - `host_channel_replay.<scenario>.json`
    - `EVIDENCE_MANIFEST.<tag>.json`

## 5) Residual risk register (initial)

1. **P1**: project runtime may still include legacy direct dispatch callsites.
   - mitigation: explicit project-runtime fail-close branch + negative probe in CI/replay.
2. **P1**: wrapper files may exist but not be consumed by project routing.
   - mitigation: routing assertions and dispatch receipts at project-runtime entrypoints.
3. **P2**: cross-repo path mapping drift can break wrapper invocation consistency.
   - mitigation: explicit protocol path mapping in wrapper contract + strict validation on init/update.
4. **P2**: stream docs can drift from implementation lifecycle when PR binding is not recorded.
   - mitigation: required `stream_pr_binding.json` receipt and SSOT registry parity checks.
5. **P2**: implementation may incorrectly map non-strict profile to wrapper bypass.
   - mitigation: explicit wrapper-vs-profile acceptance checks in replay matrix.

## 6) Current posture

Posture: `CONDITIONAL_GO` for v1.6.6 implementation.

Reason:

1. Governance contract is now explicit and non-ambiguous.
2. Review closure still depends on project runtime entrypoint wiring completion and replay evidence.

## 7) Code landing checkpoint (2026-03-12, protocol repo)

### 7.1 Landed files

1. `scripts/create_identity_pack.py`
   - scaffold now writes `protocol_host_unique_channel_contract_v1`.
   - init emits deterministic runtime gate artifacts (`ingress_wrapper`, `egress_wrapper`, `gateway_contract`).
2. `scripts/repair_contract_backfill.py`
   - update/backfill now auto-wires host gateway contract for existing instances.
   - `--apply` now materializes/refreshes wrapper files and `protocol_gateway_contract.json`.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - strict validation extended from unique-entry only to unique-entry + project-wrapper parity.
   - runtime file presence, canonical script binding, tuple fields, and gateway JSON schema-required fields are now machine-checked.

### 7.2 Serial run evidence summary (this round)

1. Backfill apply (`base-repo-audit-expert-v3`) passed:
   - `contract_backfill_status=PASS_REQUIRED`
   - `host_gateway_contract_auto_wire_status=PASS_REQUIRED`
2. Bundle entry + receipt binding passed:
   - `required_gate_bundle_runner` returned `protocol_unique_entry_receipt_status=PASS_REQUIRED`
   - `run_id_binding` matched validator `--run-id`
3. Unique-entry validator with receipt requirement passed:
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - `protocol_host_gateway_contract_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_files_status=PASS_REQUIRED`
   - `protocol_host_gateway_runtime_contract_status=PASS_REQUIRED`
4. Control-plane/doc gates remained green in the same serial run:
   - `validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
   - `validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
   - `validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
   - `docs_command_contract_check.py` -> `PASS`
   - `validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`

### 7.3 Review interpretation

1. v1.6.6 host-channel stream has moved from docs-only contract to executable protocol tooling.
2. Protocol-side init/update/validate closure is materially strengthened.
3. Final stream closure remains `CONDITIONAL_GO` until project runtime entrypoints are proven wrapper-only in replay/CI lanes.

### 7.4 Creator/Installer downsink real-run verification (self-driven, serial)

This round explicitly validates your requirement that wrapper files are down-sunk into instance packs
(`CURRENT_TASK.json`/`IDENTITY_PROMPT.md` style artifact placement), and that wrappers point back to protocol canonical scripts.

#### A) identity-creator init downsink (real runtime pack)

Evidence contract (non-temp, machine-observable fields):

1. `host_gateway_downsink_status=PASS_REQUIRED`
2. `protocol_host_gateway_runtime_files_status=PASS_REQUIRED`
3. `protocol_host_gateway_runtime_contract_status=PASS_REQUIRED`

Observed:

1. creator init generated instance-side files under pack runtime gate root:
   - `runtime/gate/protocol_ingress_wrapper.py`
   - `runtime/gate/protocol_egress_wrapper.py`
   - `runtime/gate/protocol_gateway_contract.json`
2. `CURRENT_TASK.json` includes `protocol_host_unique_channel_contract_v1` with required=true.

#### B) identity-installer install downsink (real load path)

Observed via install report:

1. `host_gateway_downsink_status=PASS_REQUIRED`
2. down-sunk target pack contains same three runtime gate artifacts and passes unique-entry host-gateway validation.
3. Runtime temporary paths generated during execution are treated as non-canonical scratch and are intentionally excluded from governance docs.

#### C) Canonical pointer closure (wrapper -> protocol scripts)

Observed in generated `protocol_gateway_contract.json`:

1. `protocol_ingress_script = scripts/required_gate_bundle_runner.py`
2. `protocol_egress_script = scripts/final_emit_governed.py`
3. wrappers and gateway contract paths are explicit, not implicit defaults.

#### D) Self identity serial 5-round deep replay (non-fixed-path)

Evidence contract (serial run scoreboard fields):

1. `round_count=5`
2. `all_rounds_passed=true`
3. `unexpected_failures=0`

Result:

1. each round covers positive + negative probes (precheck fail, bypass fail, wrapper ingress pass, wrapper egress pass, mismatch fail, surface/invariants/status sync pass).

Interpretation:

1. Wrapper downsink capability is now executable in both creation and installation lifecycle.
2. Wrapper artifacts are instance-local, and contract pointers remain protocol-canonical.
3. This closes the previous “declared but not materialized” gap for v1.6.6 host unique channel baseline.

### 7.5 Receipt tuple hardening + base-repo-architect serial chain proof (2026-03-12)

This round closes the remaining weak edge where entry receipts lacked full actor/session tuple data.

Code hardening landed:

1. `scripts/required_gate_bundle_runner.py`
   - unique-entry receipt now persists `actor_id` and `session_id` with `run_id_binding`.
2. `scripts/create_identity_pack.py`
   - `protocol_unique_entry_gate_contract_v1.entry_receipt_required_fields` now includes `actor_id` and `session_id`.
   - generated egress wrapper now fail-closes when ingress receipt tuple is incomplete.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - adds optional `--actor-id/--session-id` checks.
   - validator now enforces receipt actor/session parity when those tuple fields are provided.

Real serial proof (base-repo-architect identity):

1. Contract backfill apply updated instance runtime contract and wrappers in-place.
2. Serial rounds executed: 5 (no parallel substitution).
3. Each round covered:
   - precheck without same-run receipt -> expected `FAIL_REQUIRED`
   - ingress wrapper -> `PASS_REQUIRED` receipt emission
   - postcheck same run/actor/session -> `PASS_REQUIRED`
   - egress wrapper same run/actor/session -> `PASS_REQUIRED`
   - negative probe (egress run_id mismatch) -> fail-close
4. Deep checks after rounds remained green:
   - `validate_control_plane_invariants.py --json-only`
   - `validate_required_gate_surface_drift.py --json-only`
   - `validate_control_plane_status_sync.py --json-only`
   - `docs_command_contract_check.py`
   - `validate_doc_evidence_persistence.py --json-only`

Persistent runtime scoreboard:

1. `.identity/base-repo-architect/runtime/reports/v166-wrapper-chain-selftest/scoreboard-*.json`

### 7.6 Wrapper-only hard enforcement closure (2026-03-12, follow-up)

This follow-up closes the audit delta: “configurable and runnable, but not fully forced.”

Hardening landed:

1. `scripts/validate_protocol_unique_entry_gate.py`
   - now hard-fails when `host_dispatch_mode != wrapper_only` or `host_release_mode != wrapper_only`.
   - now hard-fails when ingress wrapper dispatch token drifts.
2. `scripts/required_gate_bundle_runner.py`
   - strict `host_ingress_wrapper` entry now requires wrapper dispatch token.
   - direct protocol entry without wrapper token returns `FAIL_REQUIRED`.
3. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - instance contracts/runtime gateway artifacts now carry required wrapper-only modes and ingress dispatch token.
   - backfill normalizes legacy packs to same hard baseline.

Serial multidimensional probe replay (base-repo-architect):

1. Rounds: 5, strictly serial.
2. Per-round probes include:
   - direct protocol bypass probe (no wrapper token) -> fail-close
   - wrapper ingress pass -> receipt emission pass
   - receipt tuple integrity (`run_id`/`actor_id`/`session_id`) -> pass
   - entry postcheck parity pass
   - actor/session mismatch probes -> fail-close
   - egress pass
   - egress run/session mismatch probes -> fail-close
3. Deep checks after rounds: all green.

Persistent runtime scoreboard:

1. `.identity/base-repo-architect/runtime/reports/v166-wrapper-multidim-serial5/scoreboard-hardening-rerun-*.json`

### 7.7 No-hardcode closure + strict provenance anti-bypass (2026-03-12, continuation)

This round closes the remaining “hardcoded policy constant” risk by converting strict wrapper checks to contract-derived policy.

Code hardening landed (same v1.6.6 stream, incremental commits):

1. `scripts/required_gate_bundle_runner.py`
   - strict wrapper surface/token expectations now resolve from instance contract (`protocol_host_unique_channel_contract_v1`) instead of fixed constants.
   - strict operations now mark non-wrapper surface as contract violation and fail-close.
   - unique-entry receipt persists wrapper provenance fields:
     - `surface_label`
     - `wrapper_dispatch_required`
     - `wrapper_surface_status`
     - `wrapper_dispatch_token_status`
   - strict flow now marks `protocol_unique_entry_receipt_status=FAIL_REQUIRED` whenever bundle result is non-pass (no more “receipt persisted but status pass” ambiguity on bypass/error paths).
2. `scripts/create_identity_pack.py`
   - `protocol_unique_entry_gate_contract_v1.entry_receipt_required_fields` adds wrapper provenance fields.
   - `protocol_host_unique_channel_contract_v1.entry_receipt_policy` now carries required provenance constraints:
     - `required_surface_label`
     - `required_wrapper_surface_status`
     - `required_wrapper_dispatch_token_status`
   - generated runtime gateway contract writes the same policy fields.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - strict receipt validation now enforces provenance from contract policy (not hardcoded constants).
   - receipt without wrapper provenance parity is `FAIL_REQUIRED`.
4. `scripts/repair_contract_backfill.py`
   - backfill normalizes existing instance contracts to include the new entry receipt provenance policy fields.

Serial verification outcome (base-repo-architect identity):

1. 5 rounds, strictly serial, each round includes:
   - precheck without same-run receipt -> blocked
   - ingress wrapper positive path -> pass + receipt emitted
   - postcheck tuple parity (`run_id/actor_id/session_id`) -> pass
   - actor mismatch negative probe -> blocked
   - direct runner bypass (`surface_label=bypass_probe`) -> blocked with entry-family fail-close
   - bypass receipt re-validation -> blocked
2. overall serial focused scoreboard: all rounds passed.

Interpretation:

1. v1.6.6 now enforces wrapper provenance as a contract policy, not script hardcode.
2. direct strict script invocation no longer masquerades as wrapper flow in receipt validation.
3. “配置即规则、执行即校验、绕行即失败” is now machine-closed for the unique-entry chain.

### 7.8 Light/heavy upgrade-only routing + per-round receipt closure (2026-03-12, freeze alignment)

This round aligns implementation with the frozen v1.6.6 acceptance clauses for “every round must pass wrapper path” while keeping normal rounds lightweight.

Implementation closure:

1. `scripts/create_identity_pack.py`
   - host gateway contract now embeds `operation_profile_policy`:
     - `strict_operations`
     - `light_operations`
     - `strict_gate_profile`
     - `light_gate_profile`
     - `allow_upgrade_only`
   - ingress wrapper template now resolves gate profile from contract policy (contract-driven routing), then forwards `--gate-profile` to canonical ingress script.
2. `scripts/required_gate_bundle_runner.py`
   - instance work-layer rounds now enforce wrapper provenance (`surface + dispatch token`) for both strict and light rounds under `wrapper_only`.
   - ingress receipt now persists on all instance wrapper rounds (not strict-only).
3. `scripts/validate_protocol_unique_entry_gate.py`
   - validates host gateway `operation_profile_policy` presence/completeness.
   - validates runtime gateway contract parity against CURRENT_TASK policy.
   - ingress dispatch token check is contract-derived (runtime token must match CURRENT_TASK contract token), not fixed constant matching.
4. `scripts/repair_contract_backfill.py`
   - backfills legacy packs with `operation_profile_policy` defaults.
5. `identity/protocol/mappings/layer-targeted-gate-profile.v1.6.yaml`
   - `inspection_targeted` now supports `work_layer=instance`.
   - lightweight requirement set trimmed to low-overhead safety probes.

Serial replay proof (base-repo-architect):

1. 5 rounds, strict serial.
2. each round includes:
   - strict precheck without same-run receipt -> blocked
   - light ingress (`inspection`) -> `inspection_targeted` pass + receipt
   - light postcheck with receipt -> pass
   - strict ingress (`validate`) -> `strict_full` pass + receipt
   - strict postcheck with receipt -> pass
   - actor mismatch negative probe -> blocked
   - light/strict direct bypass probes -> both blocked
3. scoreboard:
   - `.identity/base-repo-architect/runtime/reports/v166-wrapper-multidim-serial5/scoreboard-v166-light-strict-serial5-1773299699.json`

Result:

1. v1.6.6 now satisfies “轻重分流 + 只升不降 + 每轮入口收据” on instance wrapper path.
2. no-hardcode policy for wrapper routing is contract-derived and backfillable.

### 7.9 Session-scoped egress continuity replay (2026-03-12, 5-round serial)

To close the acceptance clause “ingress/egress both mandatory per round”, session-scoped actor binding was refreshed for `base-repo-architect` and replayed with full I/O chain.

Replay setup:

1. activate binding refresh:
   - `python3 scripts/identity_creator.py activate --catalog <project>/.identity/catalog.local.yaml --identity-id base-repo-architect --actor-id assistant:codex --session-id sid-egress-fix --run-id <...>`
2. serial rounds use fixed session binding `sid-egress-fix`.

Per-round checks (5 rounds, serial):

1. ingress wrapper pass (`inspection_targeted`) + receipt pass
2. egress wrapper pass (`send_time_gate_status=PASS_REQUIRED`, `final_emit_guard_status=PASS_REQUIRED`)
3. egress run-id mismatch negative probe -> blocked
4. direct ingress bypass probe -> blocked (`IP-GATE-ENTRY-001`)
5. bypass receipt postcheck -> blocked

Scoreboard:

1. `.identity/base-repo-architect/runtime/reports/v166-wrapper-multidim-serial5/scoreboard-v166-io-serial5-1773300763.json`

Result:

1. v1.6.6 now has replay evidence for per-round inbound+outbound mandatory wrapper path under session-scoped actor binding.

## 8) External references

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

## 9) Dialogue-derived audit baseline (2026-03-12, frozen for item-by-item review)

This section records the multi-round alignment points from the latest review dialogue,
and converts them into deterministic audit checks to prevent “policy green, runtime bypass”.

### 9.1 Frozen problem statement (from dialogue consensus)

1. v1.6.6 core target is not “wrapper declaration exists”; it is “instance runtime I/O must be wrapper-bound”.
2. The most critical failure mode is not only `runner` bypass, but conversation-layer bypass:
   - instance replies directly without ingress/egress wrapper traversal.
3. Wrapper-only must apply to both project and global source layers:
   - `<project>/.identity/<identity_id>/...`
   - `${CODEX_HOME}/.identity/<identity_id>/...`
4. `full strict bundle` is not required for every round, but wrapper traversal is required for every round.
5. Heavy operations must remain strict; light rounds may be lightweight but cannot bypass wrapper or egress hard gates.

### 9.2 Frozen boundary semantics (must not drift)

1. Layer boundaries:
   - protocol base repo: `identity-protocol-local`
   - business project repo: `<project>`
   - instance runtime pack: `<global>|<project>/.identity/<identity_id>/`
2. Canonical protocol scripts:
   - ingress authority: `scripts/required_gate_bundle_runner.py`
   - egress authority: `scripts/final_emit_governed.py`
3. Mandatory per-instance downsink artifacts (same governance tier as `CURRENT_TASK.json`/`IDENTITY_PROMPT.md`):
   - `runtime/gate/protocol_ingress_wrapper.py`
   - `runtime/gate/protocol_egress_wrapper.py`
   - `runtime/gate/protocol_gateway_contract.json`
4. Controller split (must stay separated):
   - `identity_creator`: contract semantics generation/update
   - `identity_installer`: runtime artifact downsink/repair
5. Global runtime root is fixed:
   - `${CODEX_HOME}/.identity/`
   - legacy `${CODEX_HOME}/identity/` is non-canonical.

### 9.3 Dialogue-frozen acceptance checklist (audit must check item by item)

1. `host_dispatch_mode=wrapper_only` and `host_release_mode=wrapper_only` are present in CURRENT_TASK contract and runtime gateway contract.
2. Inbound conversation execution path resolves to ingress wrapper, not direct business script dispatch.
3. User-visible outbound release path resolves to egress wrapper, not direct emit path.
4. Non-mutation rounds are still wrapper-traversed.
5. Heavy rounds (`validate/update/activate/mutation/readiness/e2e/ci/three-plane`) use strict profile.
6. Light rounds (`inspection/scan`) use lightweight profile unless self-upgraded to strict.
7. Heavy-to-light downgrade is blocked; light-to-strict self-upgrade is allowed.
8. Ingress receipt includes tuple and provenance fields:
   - `run_id_binding`, `actor_id`, `session_id`, `surface_label`,
   - `wrapper_dispatch_required`, `wrapper_surface_status`, `wrapper_dispatch_token_status`.
9. Egress verifies same-turn ingress receipt tuple parity (`run_id/session_id/actor_id`).
10. `identity_creator` init/update and `identity_installer` install/update both materialize wrapper artifacts.
11. Protocol/instance split-repo path mapping remains explicit (no hidden mono-repo fallback).
12. Global and project source-layer instances both pass the same wrapper contract checks.

### 9.4 Anti-false-green checks (must be executed as negative probes)

1. Direct ingress script call without wrapper proof must fail-close.
2. Direct egress script call without wrapper flow proof must fail-close.
3. Actor mismatch receipt replay must fail-close.
4. Session mismatch receipt replay must fail-close.
5. Run-id mismatch receipt replay must fail-close.
6. Stale receipt reuse (previous run) must fail-close.
7. Strict operation with non-wrapper provenance must fail-close.
8. Any route that can output user-visible content without egress wrapper must fail-close.

### 9.5 Known non-closure indicators (if any hit, v1.6.6 remains CONDITIONAL_GO)

1. Wrapper enforcement depends on caller-self-reported tuple/layer flags that can be spoofed.
2. Runtime has wrapper files, but project session entrypoints do not consume them.
3. Egress can emit without same-turn ingress receipt parity.
4. Global source-layer path is unresolved or drifts from `${CODEX_HOME}/.identity/`.
5. Replay evidence covers strict-only path but misses non-mutation wrapper-mandatory path.

### 9.6 Audit verdict rule (dialogue-frozen)

1. Only when all checklist items in 9.3 pass and all negative probes in 9.4 fail-close,
   and no non-closure indicator in 9.5 is present, can the stream move to `Implementation PASS`.
2. Otherwise posture remains `CONDITIONAL_GO`, even if control-plane static validators are green.

## 10) P1 audit remediation checkpoint (2026-03-12, anti-spoof enforcement pass)

This checkpoint addresses the explicit audit finding that wrapper enforcement could be bypassed
by spoofing caller parameters (for example `--resolved-work-layer protocol`) during direct runner calls.

### 10.1 Code-level closure applied

1. `scripts/required_gate_bundle_runner.py`
   - wrapper provenance requirement is now derived from host gateway contract policy (`host_dispatch_mode` + `operation_profile_policy`), not from caller-reported `--resolved-work-layer`.
   - strict/light operation sets from contract are consumed to decide wrapper provenance requirement.
   - unknown operations under `wrapper_only` are fail-close wrapped as strict-equivalent provenance required.
2. `scripts/validate_protocol_unique_entry_gate.py`
   - receipt provenance checks are now gated by wrapper policy (`provenance_required`) rather than `strict_operation` only.
   - host gateway contract and runtime gateway contract now reject unexpected additional fields (additionalProperties fail-close).
   - nested policy objects (`operation_profile_policy`, `entry_receipt_policy`, `egress_receipt_policy`, `headstamp_policy`) also reject unexpected fields.

### 10.2 Replay result (serial, local, no tmp evidence references)

1. Negative bypass replay (direct runner with forged work-layer):
   - command: direct `required_gate_bundle_runner.py` call using `--resolved-work-layer protocol --surface-label bypass_probe`.
   - result: `rc=1`, `bundle_status=FAIL_REQUIRED`,
     `mapping_errors` includes:
     - `wrapper_surface_not_configured_wrapper:bypass_probe:expected=host_ingress_wrapper`
     - `wrapper_dispatch_token_missing_or_invalid`
2. Receipt validator replay on same run-id:
   - command: `validate_protocol_unique_entry_gate.py --require-entry-receipt --run-id <same>`
   - result: `FAIL_REQUIRED` with provenance failures:
     - `entry_receipt_surface_label_mismatch`
     - `entry_receipt_wrapper_surface_status_not_pass_required`
     - `entry_receipt_wrapper_dispatch_status_not_pass_required`
3. Control-plane regression gates after patch:
   - `validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
   - `validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
   - `validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
   - `sync_plugin_join_wiring.py --check --json-only` -> `PASS_REQUIRED`
   - `docs_command_contract_check.py` -> `PASS`

### 10.3 Updated review interpretation

1. Closed in this checkpoint:
   - caller-parameter spoof path (`resolved_work_layer` gating) no longer controls wrapper enforcement.
   - contract/runtime additionalProperties drift now has machine fail-close protection.
2. Still tracked for full stream closure:
   - per-turn dynamic wrapper proof (`nonce + time-window + replay block`) for anti-replay hardening.
   - project session dispatcher must expose wrapper-only execution APIs (conversation-layer physical routing proof).
3. Posture remains: `Policy PASS / Implementation CONDITIONAL PASS`.

## 11) Deep self-check against frozen dialogue baseline (2026-03-12)

This section performs an explicit item-by-item replay against section 9 (`9.3 + 9.4 + 9.5`) and records current machine-observed status.

### 11.1 Scope and method

1. Identity under replay: `base-repo-architect` (project layer runtime pack).
2. Catalog source: `/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`.
3. Replay mode: serial command execution, no parallel substitution for decision probes.
4. Evidence form: command outputs only (no temporary-path references added to strict docs).

### 11.2 9.4 negative-probe replay status

1. `9.4-1` direct ingress call without wrapper proof -> **PASS (blocked as expected)**.
   - probe: direct `required_gate_bundle_runner.py` call, no wrapper token.
   - observed: `bundle_status=FAIL_REQUIRED`, `wrapper_dispatch_token_status=FAIL_REQUIRED`.
2. `9.4-2` direct egress script call without wrapper flow proof -> **FAIL (not yet blocked)**.
   - probe: direct `scripts/final_emit_governed.py` call with explicit context.
   - observed: `final_emit_guard_status=PASS_REQUIRED`.
3. `9.4-3` actor mismatch replay -> **PASS (blocked as expected)**.
   - observed: `protocol_egress_wrapper_status=FAIL_REQUIRED`, `error_code=IP-ASB-201`.
4. `9.4-4` session mismatch replay -> **PASS (blocked as expected)**.
   - observed: `protocol_egress_wrapper_status=FAIL_REQUIRED`, `error_code=IP-ASB-201`.
5. `9.4-5` run-id mismatch replay -> **PASS (blocked as expected)**.
   - observed: `protocol_egress_wrapper_status=FAIL_REQUIRED`, `error_code=IP-GATE-ENTRY-002`.
6. `9.4-6` stale receipt reuse -> **FAIL (anti-replay hardening pending)**.
   - observed: receipt tuple-parity passes when reused with matching tuple context; no nonce/time-window replay blocker yet.
7. `9.4-7` strict non-wrapper provenance -> **PASS (blocked as expected)**.
   - probe: direct runner call with forged `--resolved-work-layer protocol --surface-label bypass_probe`.
   - observed: `rc=1`, `bundle_status=FAIL_REQUIRED`.
8. `9.4-8` any user-visible output path without egress wrapper -> **FAIL (not yet physically sealed)**.
   - observed: direct canonical egress script can emit pass without wrapper envelope.

### 11.3 9.5 non-closure indicator check

1. `9.5-1` caller-self-reported layer spoof bypass -> **cleared in this round**.
   - wrapper enforcement no longer keyed by caller `resolved_work_layer`.
2. `9.5-2` runtime has wrapper files but project entrypoints might not consume them -> **still open (project-runtime proof required)**.
3. `9.5-3` egress emit without same-turn ingress parity -> **open via direct canonical egress path**.
4. `9.5-4` global source-layer canonical path drift -> **not reopened in this replay**.
5. `9.5-5` strict-only replay coverage bias -> **partially mitigated** (light/strict replays exist), but full closure still depends on item 2/3 above.

### 11.4 Verdict after deep self-check

1. Section-9 baseline is correctly materialized and useful as an audit checklist.
2. P1 spoofed-layer ingress bypass is now closed in code.
3. Full closure is not yet achieved because egress physical bypass and anti-replay hardening are still pending.
4. Stream posture remains: `Policy PASS / Implementation CONDITIONAL PASS`.
