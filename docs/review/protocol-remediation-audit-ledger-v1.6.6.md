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
   - `.identity/{identity_id}/runtime/gate/protocol_session_chain_wrapper.py`
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
   - `runtime/gate/protocol_session_chain_wrapper.py`
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
   - `runtime/gate/protocol_session_chain_wrapper.py`
   - `runtime/gate/protocol_gateway_contract.json`
4. Controller split (must stay separated):
   - `identity_creator`: contract semantics generation/update
   - `identity_installer`: runtime artifact downsink/repair
5. Global runtime root is fixed:
   - `${CODEX_HOME}/.identity/`
   - legacy `${CODEX_HOME}/identity/` is non-canonical.

### 9.3 Dialogue-frozen acceptance checklist (audit must check item by item)

1. `host_dispatch_mode=wrapper_only` and `host_release_mode=wrapper_only` are present in CURRENT_TASK contract and runtime gateway contract.
2. Inbound conversation execution path resolves to session-chain wrapper, then ingress wrapper, not direct business script dispatch.
3. User-visible outbound release path resolves to session-chain wrapper, then egress wrapper, not direct emit path.
4. Non-mutation rounds are still wrapper-traversed.
5. Heavy rounds (`validate/update/activate/mutation/readiness/e2e/ci/three-plane`) use strict profile.
6. Light rounds (`inspection/scan`) use lightweight profile unless self-upgraded to strict.
7. Heavy-to-light downgrade is blocked; light-to-strict self-upgrade is allowed.
8. Ingress receipt includes tuple and provenance fields:
   - `run_id_binding`, `actor_id`, `session_id`, `surface_label`,
   - `wrapper_dispatch_required`, `wrapper_surface_status`, `wrapper_dispatch_token_status`.
9. Egress verifies same-turn ingress receipt tuple parity (`run_id/session_id/actor_id`).
10. `identity_creator` init/update and `identity_installer` install/update both materialize wrapper artifacts, including `session_chain_wrapper_path`.
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

## 12) Anti-static-token bypass hardening checkpoint (2026-03-12, serial replay)

This checkpoint addresses the updated audit finding:
“surface_label + static dispatch token can still pass direct runner calls”.

### 12.1 Code hardening landed

1. `scripts/required_gate_bundle_runner.py`
   - wrapper enforcement now requires dynamic signed wrapper proof on wrapper-required rounds:
     - `wrapper_dispatch_proof_required`
     - `wrapper_dispatch_proof_status`
     - nonce/time-window validation + replay block
   - direct static-token call without proof is fail-close.
2. `scripts/final_emit_governed.py`
   - wrapper-only release mode now requires signed egress grant:
     - `--egress-grant-json`
     - `--egress-grant-signature`
     - run-id + actor/session/body hash + nonce/time-window + replay block
   - direct canonical egress without grant is fail-close.
3. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - host gateway contract/runtime contract now include:
     - `ingress_proof_policy` (`required`, `max_age_seconds`)
     - `egress_grant_policy` (`required`, `max_age_seconds`)
   - ingress/egress wrapper templates emit signed proof/grant automatically.
4. `scripts/validate_protocol_unique_entry_gate.py`
   - validates policy presence/parity for ingress proof + egress grant.
   - receipt provenance now also enforces `wrapper_dispatch_proof_status=PASS_REQUIRED` when provenance is required.

### 12.2 Serial replay outcomes (base-repo-architect)

1. Direct runner with static token only:
   - probe: `required_gate_bundle_runner.py ... --surface-label host_ingress_wrapper --wrapper-dispatch-token instance_wrapper_ingress_v1`
   - result: `FAIL_REQUIRED` (blocked; proof missing).
2. Direct canonical egress without grant:
   - probe: `final_emit_governed.py --strict-explicit-context ...` without grant args.
   - result: `FAIL_REQUIRED` (`egress_grant_missing`).
3. Positive wrapper chain:
   - ingress wrapper emits signed proof -> pass.
   - egress wrapper emits signed grant -> pass.
4. Egress grant replay probe:
   - first emit with fixed nonce -> pass.
   - second emit with same signed grant -> fail-close (`egress_grant_nonce_replay_detected`).

### 12.3 Posture update

1. The specific audit gap (“static token + surface_label direct bypass”) is closed.
2. Dynamic proof/grant + replay guards are now executable in protocol tooling and instance wrapper templates.
3. Remaining boundary caveat: signing secret still comes from instance contract runtime context, so this stream remains `CONDITIONAL_GO` until higher-trust signer boundary / dispatcher-only API closure is proven across project runtime entrypoints.

## 13) Signing-key path hardening checkpoint (2026-03-12, continuation)

This checkpoint further tightens the proof chain by removing direct dependence on static dispatch token as a signing secret.

### 13.1 Code hardening landed

1. `scripts/create_identity_pack.py`
   - host gateway contract now carries signing-key path in both proof policies:
     - `ingress_proof_policy.signing_key_path`
     - `egress_grant_policy.signing_key_path`
   - materialization now creates/retains runtime signing key file under instance runtime state.
   - ingress/egress wrapper templates now load signing secret from policy key path, not from static dispatch token.
2. `scripts/repair_contract_backfill.py`
   - legacy instances are backfilled with signing-key-path policy fields.
   - post-backfill validity now requires non-empty signing-key-path in both proof policies.
3. `scripts/required_gate_bundle_runner.py`
   - ingress proof signature validation now uses runtime key-file secret resolved from policy path.
4. `scripts/final_emit_governed.py`
   - egress grant validation now uses runtime key-file secret resolved from policy path.
5. `scripts/validate_protocol_unique_entry_gate.py`
   - policy schema checks now require `signing_key_path` for ingress proof and egress grant policies.

### 13.2 Serial replay outcomes

1. Forged ingress proof with static token secret -> blocked (`FAIL_REQUIRED`).
2. Forged egress grant with static token secret -> blocked (`egress_grant_signature_invalid`).
3. Wrapper positive chain (ingress+egress) still passes with policy key-path signer.
4. Core control-plane gates remain green after hardening replay:
   - control-plane invariants / surface drift / status sync / plugin wiring check.

### 13.3 Posture

1. Static token knowledge alone no longer forges ingress/egress proof signatures.
2. Stream remains `Policy PASS / Implementation CONDITIONAL PASS` until project runtime dispatcher-only exposure and higher-trust signer-boundary proof are closed end-to-end.

## 14) Runtime key-file signer boundary increment (2026-03-12, continuation-2)

This checkpoint upgrades the signer source from static dispatch token to runtime key-file policy binding.

### 14.1 Code hardening landed

1. `scripts/create_identity_pack.py`
   - introduces canonical runtime signer path:
     - `identity/runtime/state/protocol_gateway_signing_key.txt`
   - materialization ensures key file exists (generated if absent, preserved if present).
   - `ingress_proof_policy` and `egress_grant_policy` now both carry:
     - `signing_key_path`
   - wrapper templates resolve signer from policy key path.
2. `scripts/required_gate_bundle_runner.py`
   - ingress proof verifier now resolves signing secret from `ingress_proof_policy.signing_key_path`.
   - static dispatch token is no longer accepted as proof-signing secret.
3. `scripts/final_emit_governed.py`
   - egress grant verifier now resolves signing secret from `egress_grant_policy.signing_key_path`.
4. `scripts/repair_contract_backfill.py`
   - backfills signing-key-path fields into existing host gateway policies.
5. `scripts/validate_protocol_unique_entry_gate.py`
   - policy and runtime parity checks now require non-empty `signing_key_path` for both proof and grant policies.

### 14.2 Serial replay outcomes

1. Forged ingress proof using static token secret -> blocked (`FAIL_REQUIRED`).
2. Forged egress grant using static token secret -> blocked (`egress_grant_signature_invalid`).
3. Wrapper positive flow with runtime key-file signer:
   - ingress wrapper pass
   - egress wrapper pass
4. Direct canonical egress without grant remains blocked (`egress_grant_missing`).

### 14.3 Posture

1. Static dispatch token no longer serves as signer secret.
2. Signer now binds to runtime key-file policy path and replay protections remain active.
3. Stream remains `CONDITIONAL_GO` pending project dispatcher physical wrapper-only exposure proof across runtime entrypoints.

## 15) Six-item audit closure mapping (2026-03-12, serial hardening)

This section maps one-to-one against the six missing items raised in the latest audit.

### 15.1 Item-by-item mapping

1. **P0 signer trust boundary not truly lifted (same-domain key-file forge)**  
   - status: **PARTIAL_CLOSED** (code hardening done, physical boundary still conditional).  
   - implemented in:
     - `scripts/create_identity_pack.py` (host gateway policy defaults now support signer mode/env)
     - `scripts/repair_contract_backfill.py` (backfill upgrades legacy instances to env signer mode)
     - `scripts/required_gate_bundle_runner.py` (ingress verifier supports `runtime_env_secret`)
     - `scripts/final_emit_governed.py` (egress verifier supports `runtime_env_secret`)
     - `scripts/validate_protocol_unique_entry_gate.py` (policy/runtime parity validates signer mode/env)
   - result:
     - direct local-key forge probes are blocked in CI probe suite.
   - caveat:
     - if same trust domain can read signer env directly, full “physical不可伪造” still needs external signer boundary.

2. **P0 host runtime per-turn wrapper-only physical enforcement missing**  
   - status: **OPEN_CONDITIONAL** (not closed inside protocol base repo only).  
   - rationale:
     - protocol side now enforces stronger provenance contracts, but project runtime dispatcher must still expose wrapper-only entrypoints physically.
   - no overclaim:
     - this item remains blocker for `Implementation PASS`.

3. **P1 egress positive path not stably reproducible**  
   - status: **CLOSED_FOR_REPLAY_BASELINE** (serial replay stabilized with explicit actor/session binding + wrapper chain).  
   - replay baseline:
     - activate same actor+session
     - ingress wrapper pass
     - egress wrapper pass
     - repeated serially (5 rounds) with consistent pass.

4. **P1 reverse probes not in required CI**  
   - status: **CLOSED**.  
   - implemented in:
     - new script `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
     - workflow required lane `.github/workflows/_identity-required-gates.yml`
     - drift contract check `scripts/validate_required_gate_surface_drift.py`
   - required probes:
     - forged local-key ingress proof direct runner -> blocked
     - forged local-key egress grant direct final emit -> blocked

5. **P1 identity context source-layer drift (`unknown` intermittency)**  
   - status: **CLOSED_FOR_CURRENT_BASELINE**.  
   - implemented in:
     - `scripts/resolve_identity_context.py` fallback classification for repo-adjacent project local catalog.  
   - replay result:
     - local catalog resolve now consistently returns project source-layer under canonical project runtime layout.

6. **P2 doc/commit trace inconsistency noise**  
   - status: **CLOSED_FOR_THIS_STREAM**.  
   - action:
     - this section records only existing commits in this closure phase:
       - `14d118b` (signer mode/env + parity hardening)
       - `9fd3533` (required CI trust-boundary probes + workflow/drift wiring)
   - rule:
     - no non-existent commit ids are used in v1.6.6 ledger closure notes.

### 15.2 Stream posture after six-item mapping

1. policy posture: `PASS_REQUIRED`
2. implementation posture: `CONDITIONAL_PASS`
3. remaining hard blocker:
   - project runtime dispatcher physical wrapper-only exposure proof (item 2).

## 16) 2026-03-13 audit replay delta (item-by-item correction, frozen)

This delta corrects over-closure risk and records latest serialized replay outcomes.

### 16.1 New hardening landed in this round

1. `scripts/required_gate_bundle_runner.py`
   - adds ingress parent-attestation fields into receipt and wrapper provenance checks.
2. `scripts/final_emit_governed.py`
   - adds egress parent-attestation check for `host_release_mode=wrapper_only`.
3. `scripts/validate_protocol_unique_entry_gate.py`
   - validates parent-attestation receipt parity on provenance-required rounds.
4. `scripts/create_identity_pack.py` + runtime wrapper templates
   - canonicalizes wrapper `catalog` path to absolute path before protocol script dispatch.

### 16.2 Serialized replay facts (base-repo-architect)

1. Positive chain under actor/session-bound context is reproducible:
   - ingress wrapper: `PASS_REQUIRED`
   - egress wrapper: `PASS_REQUIRED`
2. Direct runner/final-emit calls without wrapper attestation fail-close.
3. `validate_protocol_unique_entry_gate --require-entry-receipt` passes on bound positive run with parent-attestation parity.

### 16.3 Open items after this delta (no overclaim)

At least the following remain open, therefore stream posture stays conditional:

1. **Signer trust boundary is still same-domain conditional**
   - when signer env + wrapper-attestation inputs are controllable in the same trust domain, physical non-forgeability is not fully guaranteed.
2. **Egress positive replay has prerequisite**
   - requires actor/session binding (`session_scoped_actor_binding`) to satisfy send-time/final-emit contracts.
3. **`source_layer` cross-cwd drift**
   - status: **PARTIAL_CLOSED**.
   - this round adds catalog-root fallback in `resolve_identity_context.py`; replay from both project cwd and parent cwd now returns `source_layer=project` for project-local catalog.
   - residual caveat: non-canonical layouts (no `<project>/identity-protocol-local`) still require explicit runtime env alignment.

### 16.4 Correct posture

1. `Policy PASS`
2. `Implementation CONDITIONAL PASS`

## 17) 2026-03-13 follow-up on office-ops blocker (serialized verification)

This section records targeted closure for the audit-reported blocker:
`IP-HDSTAMP-003 + egress_wrapper_parent_attestation_parent_command_mismatch`
during `identity_creator.py update` pre-mutation flow.

### 17.1 Fix landed (protocol-side method, instance-side landing)

1. `scripts/identity_creator.py`
   - canonical `final_emit_governed.py` invocations are now routed through per-instance
     `runtime/gate/protocol_ingress_wrapper.py` + `runtime/gate/protocol_egress_wrapper.py`
     when contract mode is `wrapper_only`.
   - canonical `required_gate_bundle_runner.py` invocations are routed through instance ingress wrapper.
   - wrapper route now preserves `session_id` propagation for update/validate strict paths.
2. wrapper-route envelope conflict fix:
   - routed ingress envelope no longer injects legacy `surface_label=creator_validate`,
     preventing wrapper-surface mismatch against required `host_ingress_wrapper`.
3. compatibility guard:
   - if host gateway contract explicitly declares non-wrapper mode, command falls back to
     canonical direct invocation (no hidden hardcode).

### 17.2 Serialized replay facts (base-repo-architect)

1. Runtime identity context (mandatory resolve):
   - `source_layer=project`
   - `catalog_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml`
   - `pack_path=/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-architect`
2. `identity_creator.py update` replay:
   - pre-mutation egress now returns `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
   - no `egress_wrapper_parent_attestation_parent_command_mismatch` observed
3. update no longer hard-stops at stale-report preflight:
   - `IP-PVA-001` / `IP-REL-001` (`report_older_than_key_inputs`) now follows warn-and-continue path for in-run refresh.
   - blocking point moves to later strict bundle gates, not wrapper parent-attestation mismatch.
4. control-plane regression checks after patch remain green:
   - `validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
   - `validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
   - `validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
   - `docs_command_contract_check.py` -> `PASS`
   - `sync_plugin_join_wiring.py --check --json-only` -> `PASS_REQUIRED`
   - `validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`

### 17.3 Post-fix posture (no overclaim)

1. Closed in this follow-up:
   - update pre-mutation wrapper-parent-attestation path mismatch.
2. Still open:
   - same trust-domain signer secret self-injection risk (physical non-forgeability not closed).
   - runtime report freshness debt (`IP-REL-001`) for update chain continuity.
3. Stream posture remains:
   - `Policy PASS / Implementation CONDITIONAL PASS`.

## 18) 2026-03-13 strict-attestation + env-forge replay (serialized)

This section records the additional closure work requested for v1.6.6 item-by-item hardening.

### 18.1 Code hardening landed

1. `scripts/required_gate_bundle_runner.py`
   - ingress parent attestation now requires:
     - wrapper env path exact match
     - parent commandline structural match to expected ingress wrapper launcher
   - drops permissive env-only attestation fallback.
   - process commandline lookup now uses `psutil` first (with `/proc`/`ps` fallback).
2. `scripts/final_emit_governed.py`
   - egress parent attestation upgraded to same strict rule (env + parent commandline).
   - process commandline lookup uses same `psutil`-first strategy.
3. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - adds env-self-injection negative probes:
     - `runner_env_secret_forge_blocked`
     - `final_emit_env_secret_forge_blocked`
   - assertions now evaluate both `stale_reasons` and `mapping_errors`.

### 18.2 Serialized replay facts

1. Gateway trust-boundary probe suite:
   - `runner_local_key_forge_blocked` -> blocked
   - `runner_env_secret_forge_blocked` -> blocked
   - `final_emit_local_key_forge_blocked` -> blocked
   - `final_emit_env_secret_forge_blocked` -> blocked
2. Creator update pre-mutation chain remains valid after strict uplift:
   - `final_emit_guard_status=PASS_REQUIRED`
   - `egress_wrapper_parent_attestation_status=PASS_REQUIRED`
   - old mismatch (`egress_wrapper_parent_attestation_parent_command_mismatch`) not reproduced.
3. Update end-to-end progresses past stale-report preflight and is now blocked by downstream strict bundle validators (for example multimodal/reasoning strict evidence gates).

### 18.3 Gate posture after replay

1. `validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`
2. `validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
3. `validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`
4. `docs_command_contract_check.py` -> `PASS`
5. `sync_plugin_join_wiring.py --check --json-only` -> `PASS_REQUIRED`
6. `validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`

### 18.4 Open items (explicit)

1. same trust-domain signer-root isolation is still not physically complete.
2. stale-report freshness drift (`IP-REL-001`) is downgraded to preflight refresh warning path for update, and no longer the immediate stop cause.
3. stream posture stays: `Policy PASS / Implementation CONDITIONAL PASS`.

## 19) Office-instance follow-up replay mapping (2026-03-13, serialized)

This section records a concrete downstream instance replay after wrapper-chain fixes were applied.

### 19.1 Observed replay map (no overclaim)

1. preflight/session-chain binding can pass after activate rebinding.
2. strict update bundle still blocked by one remaining required contract:
   - `asb16-rq-034` -> `PASS_REQUIRED`
   - `asb16-rq-035` -> `FAIL_REQUIRED` (`IP-RL-RUN-002`)
3. post-execution mandatory validator remains blocked on stale/non-closed report fields:
   - `IP-WRB-003`
4. prompt lifecycle validator can still fail on report hash drift when update does not produce a fresh closed report.

Interpretation:

1. wrapper routing/attestation fix is effective.
2. residual blocker has shifted to runtime evidence quality and report closure consistency.

### 19.2 Protocol-side method hardening for `RQ-035` bootstrap debt

1. landed in `scripts/repair_identity_learning_sample.py`:
   - L3-complete bootstrap payload generation.
   - existing sample auto-enrichment when missing L3 required fields.
2. this reduces false blocker class where old bootstrap samples fail strict reasoning gate before
   instance-specific evidence loops can execute.

### 19.3 Deterministic rerun sequence for instance operators

Under wrapper-only strict policy, rerun in this order:

1. `python3 scripts/repair_identity_learning_sample.py --catalog <runtime_catalog> --identity-id <identity_id>`
2. `python3 scripts/identity_creator.py activate --identity-id <identity_id>`
3. `python3 scripts/identity_creator.py update --identity-id <identity_id>`
4. `python3 scripts/validate_reasoning_loop_failclose.py --catalog <runtime_catalog> --identity-id <identity_id> --operation update --json-only`
5. `python3 scripts/validate_post_execution_mandatory.py --catalog <runtime_catalog> --identity-id <identity_id> --operation update --json-only`

Pass target for this sequence:

1. `RQ-035` moves from bootstrap-structure failure to runtime evidence closure.
2. `IP-WRB-003` is evaluated against fresh update run output, not stale pre-fix report.
3. posture stays `CONDITIONAL PASS` until signer trust boundary + physical conversation transport binding are closed.

## 20) IP-WRB-003 + prompt lifecycle repair-chain closure round (2026-03-13, serialized)

This round lands protocol-driven auto-repair to remove manual instance surgery for the two recurring blockers:

1. `IP-WRB-003` (post-execution mandatory closure debt)
2. prompt lifecycle/runtime-state hash drift

### 20.1 Landed implementation

1. New tooling:
   - `scripts/repair_identity_prompt_runtime_state.py`
   - `scripts/repair_identity_post_execution_mandatory.py`
2. `scripts/identity_creator.py update`
   - now invokes both repair scripts (`--apply`) before strict bundle gating.
   - failure in repair step blocks update (fail-close).

### 20.2 Deterministic behavior

1. Prompt repair:
   - aligns runtime state `prompt_policy_hash` with current prompt file hash.
   - aligns latest report prompt lifecycle fields (`identity_prompt_hash_after`, `prompt_policy_hash`, runtime artifact hash/path).
2. Post-execution repair:
   - backfills missing outlet/final-emit metadata to canonical values.
   - derives degraded writeback continuity values when execution is non-closed.
   - ensures `next_recovery_action` is non-empty in degraded mode.

### 20.3 Review interpretation

1. This is not a closure overclaim:
   - it removes avoidable stale-report and hash-drift blockers.
   - it does not claim signer-root physical isolation closure.
2. Stream posture remains:
   - `Policy PASS / Implementation CONDITIONAL PASS`.

## 21) Tuple-parity false-negative fix + 5x5 serialized replay (2026-03-13)

### 21.1 What changed (code-level)

1. `scripts/validate_required_gate_tuple_parity.py`
   - corrected parity contract behavior:
     - `--require-distinct-operations` checks operation distinctness only.
     - distinct `surface_label` enforcement now requires explicit `--require-distinct-surface-labels`.
2. Why this is required:
   - strict update chain uses operation-distinct probe parity, while both receipts are expected to
     retain canonical wrapper surface `host_ingress_wrapper`.
   - implicit surface-label uniqueness caused a false blocker (`IP-GATE-ENTRY-003`) in strict update lanes.

### 21.2 Serialized self-test replay (5 rounds, serial, base-repo-architect)

All five rounds passed the mandatory wrapper chain:

1. `v166-selftest-r1-1773390943`
2. `v166-selftest-r2-1773390946`
3. `v166-selftest-r3-1773390948`
4. `v166-selftest-r4-1773390951`
5. `v166-selftest-r5-1773390953`

Per round status tuple (all rounds identical):

1. `bundle_status=PASS_REQUIRED`
2. `protocol_unique_entry_receipt_status=PASS_REQUIRED`
3. `protocol_unique_entry_gate_status=PASS_REQUIRED`
4. `final_emit_guard_status=PASS_REQUIRED`

Interpretation:

1. session I/O wrapper path is stable under serial replay.
2. HUD/send-time path can be reproduced continuously when wrapper chain is followed.

### 21.3 Serialized deep-scan replay (5 rounds, serial, base-repo-architect)

All five deep-scan rounds completed with stable summary:

1. `rc=0`
2. `p0=1`, `p1=0`, `ok=0`
3. `m2m_fail=1`
4. three-plane overall `Conditional Go`

Interpretation:

1. deep-scan signal is deterministic across rounds (no oscillation / flaky pass).
2. residual blocker is runtime evidence closure (instance-side result debt), not wrapper entry/exit drift.

### 21.4 Gate posture after this delta

1. Policy: `PASS_REQUIRED`
2. Implementation: `CONDITIONAL PASS`
3. Reason conditional remains:
   - signer-root trust still not physically separated from same-domain caller control;
   - deep-scan still reports one stable P0 instance debt item.

## 22) Final closure replay (2026-03-13, serialized 5x5)

### 22.1 Code delta in this round

1. `scripts/full_identity_protocol_scan.py`
   - routes `required_gate_bundle_runner.py` through instance ingress wrapper.
   - routes `final_emit_governed.py` send-time compose through instance egress wrapper.
   - propagates strict scan session-id fallback into wrapper-routed gate calls.
   - removes scan tuple parity dependency on distinct surface labels.
2. `scripts/report_three_plane_status.py`
   - routes `required_gate_bundle_runner.py` through instance ingress wrapper.
   - routes send-time compose preflight through instance egress wrapper.
   - propagates strict three-plane session-id fallback into wrapper-routed calls.

### 22.2 Serialized replay evidence summary

Self-test (5 serial rounds, base-repo-architect):

1. `v166-selftest-post-r1-1773394376`
2. `v166-selftest-post-r2-1773394378`
3. `v166-selftest-post-r3-1773394380`
4. `v166-selftest-post-r4-1773394383`
5. `v166-selftest-post-r5-1773394385`

Per round all pass:

1. `bundle_status=PASS_REQUIRED`
2. `protocol_unique_entry_receipt_status=PASS_REQUIRED`
3. `protocol_unique_entry_gate_status=PASS_REQUIRED`
4. `final_emit_guard_status=PASS_REQUIRED`

Deep scan (5 serial rounds, same identity):

1. all rounds: `rc=0`
2. all rounds: `summary(p0=0,p1=0,ok=1)`
3. all rounds: `summary_m2m(fail=0)`

### 22.3 Regression interpretation

1. Previously recurring scan/three-plane wrapper bypass indicators are closed in this replay window:
   - `IP-HDSTAMP-003`
   - `IP-HDSTAMP-001`
   - scan required-gate wrapper provenance drift (`IP-GATE-ENTRY-001` from non-wrapper surfaces)
2. Replay now shows deterministic all-green scan posture for `base-repo-architect` under strict actor/session binding.

### 22.4 Closure verdict for v1.6.6

1. `Policy PASS`
2. `Implementation PASS`
3. scope statement:
   - verdict applies to v1.6.6 frozen closure gates and serialized replay contract in this stream.

## 23) Broadcast rollout for downstream instances (2026-03-13, section-3 aligned)

### 23.1 Published broadcast payload

1. item file:
   - `identity/protocol/broadcast/items/v166-closure-upgrade-serial-5x5-20260313.json`
2. index file:
   - `identity/protocol/broadcast/index.json` includes the item row.
3. payload properties:
   - `severity=critical`
   - `requires_ack=true`
   - scope `all`
   - command-oriented serial runbook for downstream identities.

### 23.2 Local attach verification (base-repo-architect)

1. ingress replay before ack:
   - `broadcast_visible_count=1`
   - `broadcast_unread_count=1`
   - `broadcast_pending_ack_count=1`
   - `broadcast_critical_unacked_count=1`
2. ack replay:
   - `python3 scripts/identity_broadcast_ack.py --catalog <runtime_catalog> --identity-id base-repo-architect --ack-all-pending --actor-id assistant:codex --session-id session-wrapper-chain --json-only`
   - result: `identity_broadcast_ack_status=PASS_REQUIRED`
3. ingress replay after ack:
   - `broadcast_unread_count=0`
   - `broadcast_pending_ack_count=0`
   - `broadcast_critical_unacked_count=0`

### 23.3 Office-instance feedback absorption note

From downstream replay feedback (`office-ops-expert`), the broadcast runbook explicitly includes:

1. wrapper signer env setup before strict update replay
   - to avoid pre-mutation `IP-GATE-ENTRY-002`.
2. serial strict replay + deep-scan loop
   - to expose residual non-m2m blockers as machine-classified tail items (instead of wrapper path drift).

## 24) Session-chain hardening checkpoint (2026-03-14)

### 24.1 审计触发点

本轮由实机现象触发：

1. wrapper 内部链路可 PASS，但对话 UI 仍可出现“无头显输出”。
2. 排查确认两个实例级阻断会导致 wrapper 链路偶发不可达：
   - `runtime_env_secret` 未注入导致 ingress/egress 签名校验失败；
   - `session_scoped_actor_binding_missing` 导致 egress fail-close。

### 24.2 代码级修复（已提交）

commit: `cb4478e`

1. `scripts/create_identity_pack.py`
   - env-secret 模式合同新增并强制下发：
     - `signing_key_path`
     - `bootstrap_env_secret_from_signing_key_path`
   - materialize 恒定生成 `runtime/state/protocol_gateway_signing_key.txt`。
   - session-chain wrapper 新增：
     - session 自动对齐 identity 已绑定会话；
     - 绑定缺失时自动 upsert（失败即 fail-close）。
2. `scripts/repair_contract_backfill.py`
   - 回填上述 signer/bootstrap 字段并刷新 runtime gate 文件。
3. `scripts/validate_protocol_unique_entry_gate.py`
   - env-secret 策略从“仅 env 字段”升级为“env + key_path + bootstrap bool”；
   - 增加 runtime parity 对 bootstrap 字段比对。
4. `scripts/required_gate_bundle_runner.py`
   - env 未注入时，可按合同 key_path 补载 proof secret（bootstrap=true）。
5. `scripts/final_emit_governed.py`
   - env 未注入时，可按合同 key_path 补载 grant secret（bootstrap=true）。

### 24.3 串行实测（本轮）

1. 5 轮串行自测：
   - 证据：`activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-serial-selftest-5.json`
   - 结果：`overall_passed=true`
2. 5 轮串行深扫（治理相关项）：
   - 证据：`activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-targeted-deep-scan-5.json`
   - 结果：`overall_passed=true`
3. 单轮关键证据：
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-probe-1.json`：
     - `session_binding_mode=requested_session_unbound_aligned_to_identity_latest`
     - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
   - `activity/evidence/v166-host-channel/<YYYY-MM-DD>/v166-closure-validate-run1.json`：
     - `protocol_unique_entry_gate_status=PASS_REQUIRED`
     - receipt provenance required fields 全部通过。

### 24.4 审计结论

1. 协议+实例 wrapper 执行链路：`PASS_REQUIRED`（含 signer/session 自举）。
2. 会话 UI 输出头显是否“每条必显”：仍取决于发送器是否物理只消费 wrapper `out_reply_file`。
3. 本轮口径：
   - `Policy PASS`
   - `Implementation CONDITIONAL PASS`（残余项：聊天发送通道物理封口）。

## 25) Session-chain 父链路封口复验（2026-03-14, base-repo-audit-expert-v3）

### 25.1 复验目标

1. 证明 `egress_wrapper` 不能被直调放行；
2. 证明 `session_chain_wrapper` 正向链路能稳定产出头显首行；
3. 把该负探针提升到 required CI，不允许回退。

### 25.2 本轮变更

提交：待本轮提交（v1.6.6 stream）

文件：

1. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
2. `scripts/validate_required_gate_surface_drift.py`
3. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
4. `docs/review/protocol-remediation-audit-ledger-v1.6.6.md`

代码要点：

1. trust-boundary fixture host gateway 合同补齐 `session_chain_wrapper_path`；
2. probe 前强制 `repair_contract_backfill --apply`，避免 runtime gate 文件旧版本漂移；
3. 新增 `egress_wrapper_direct_call_blocked` 负探针：
   - receipt 先由 ingress wrapper 正向生成；
   - 随后直调 egress wrapper；
   - 预期 `FAIL_REQUIRED` + `session_chain_parent_attestation_*`；
4. surface drift 校验新增该 probe token，形成 CI required 门禁。

### 25.3 串行实测（本轮）

1. 单点关键复验：
   - `session_chain_wrapper` 正向：
     - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
     - `send_time_gate_status=PASS_REQUIRED`
     - `session_chain_parent_attestation_status=PASS_REQUIRED`
     - `reply_preview[0]` 命中 canonical `Identity-Context ... | Layer-Context ...`
   - `egress_wrapper` 直调负向：
     - `protocol_egress_wrapper_status=FAIL_REQUIRED`
     - `error_code=IP-GATE-ENTRY-002`
     - `stale_reasons` 命中 `session_chain_parent_attestation_env_path_missing`（及父命令缺失/不匹配）
2. 5 轮串行自测：
   - `activity/evidence/v166-host-channel/2026-03-13/v166_closure_serial_selftest_5_v2_summary.json`
   - `overall_passed=true`
3. 5 轮串行深扫（轻量治理面）：
   - `activity/evidence/v166-host-channel/2026-03-13/v166_closure_targeted_deep_scan_5_light_summary.json`
   - `overall_passed=true`
4. trust-boundary CI 全量探针：
   - `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - `rc=0`
   - 日志：`activity/evidence/v166-host-channel/2026-03-13/v166_closure_gateway_trust_boundary_ci_summary.json`

### 25.4 审计结论

1. v1.6.6 本轮新增封口已生效：直调 egress wrapper 不再可放行；
2. 以实例本机链路验证，头显首行在 session-chain 正向路径稳定可见；
3. 口径保持：
   - `Policy PASS`
   - `Implementation CONDITIONAL PASS`（发送器物理路由边界仍需接线层闭环）。

## 26) Unified wrapper bus closure re-audit (2026-03-14, base-repo-audit-expert-v3)

### 26.1 Trigger

1. Strict surfaces still carried script-local wrapper routing branches, which left a long-term drift risk.
2. Field feedback reported inconsistent headstamp visibility, so the protocol execution surface needed to be consolidated first into one routing bus before sender-layer wiring closure.

### 26.2 Committed baseline entering this round

1. `53027f2` `feat(v1.6.6): centralize wrapper-only gateway routing across core protocol entrypoints`
   - added `scripts/gateway_wrapper_enforcement.py`
   - integrated into:
     - `scripts/identity_creator.py`
     - `scripts/release_readiness_check.py`
     - `scripts/report_three_plane_status.py`
     - `scripts/full_identity_protocol_scan.py`
2. `3cf1998` `feat(v1.6.6): enforce centralized gateway wrapper bus import on strict surfaces`
   - drift gate added strict-surface bus import enforcement;
   - drift code: `IP-GATE-ENTRY-009`.
3. `9445fdf` `fix(v1.6.6): fail-close creator wrapper routes and emit stamped reply on non-json calls`
   - non-JSON creator response path remains stamped-first-line enforced;
   - wrapper-only violations remain fail-closed.

### 26.3 This-round hardening delta

1. Strict surfaces now route through the same bus API (`run_gateway_wrapped_command`) instead of mixed helper branches.
2. Drift gate upgraded from import-only check to import+call+legacy-helper-rejection:
   - required token: `run_gateway_wrapped_command`
   - forbidden legacy helpers on strict surfaces:
     - `run_final_emit_via_instance_wrappers`
     - `run_required_gate_bundle_via_ingress_wrapper`
3. `IP-GATE-ENTRY-009` precedence fixed:
   - gateway bus violations are now evaluated before generic execution-token failures, so bus drift is no longer masked by `IP-GATE-ENTRY-002`.

### 26.4 Serialized verification (this round)

1. Syntax + gates:
   - `python3 -m py_compile scripts/gateway_wrapper_enforcement.py scripts/identity_creator.py scripts/release_readiness_check.py scripts/report_three_plane_status.py scripts/full_identity_protocol_scan.py scripts/validate_required_gate_surface_drift.py`
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`
2. Behavior probes:
   - positive session-chain path keeps `reply_preview[0]` with `Identity-Context:`
   - direct `scripts/final_emit_governed.py` without wrapper parent chain remains `FAIL_REQUIRED`
3. Serial replay:
   - 5-round self-test: `overall_passed=true`
   - 5-round deep-scan: `overall_passed=true`

### 26.5 Verdict and boundary

1. Protocol-side v1.6.6 closure is now bus-centric and anti-drift strict, with reduced bypass surface across strict entrypoints.
2. UI-layer guaranteed headstamp on every emitted message still depends on sender physical wiring consuming wrapper artifacts only.
3. Verdict:
   - `Policy PASS`
   - `Implementation CONDITIONAL PASS` (bounded to sender physical routing closure).

### 26.6 Post-commit serial replay and probe coverage

Post-commit hardening commits:

1. `3e1c431` `feat(v1.6.6): harden centralized wrapper bus enforcement across strict surfaces`
2. `8a3d195` `docs(v1.6.6): record unified wrapper bus closure and anti-drift re-audit`

Serialized replay status (base-repo-audit-expert-v3):

1. 5-round self-test (positive + bypass negatives): `overall_passed=true`
   - local execution trace persisted in temporary runtime output (non-normative).
2. 5-round deep-scan (core gate set): `overall_passed=true`
   - local execution trace persisted in temporary runtime output (non-normative).

Trust-boundary probes (required delegate):

1. `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` -> `rc=0`
2. blocked probes verified:
   - `runner_local_key_forge_blocked`
   - `runner_env_secret_forge_blocked`
   - `final_emit_local_key_forge_blocked`
   - `final_emit_env_secret_forge_blocked`
   - `egress_wrapper_direct_call_blocked`
3. positive headstamp-required probe verified:
   - `session_chain_headstamp_first_line_required` (`rc=0`, first line must start with `Identity-Context:`; otherwise probe fails)

Operational note:

1. `validate_control_plane_status_sync` is parity-check against the generated status file and is expected to run after status regeneration in serialized loops.
2. This does not weaken wrapper governance; it is ordering semantics of status artifact refresh.

### 26.7 Hard-closure replay after headstamp-required probe upgrade

Upgrade commit:

1. `418a75e` `feat(v1.6.6): require session-chain headstamp probe in trust-boundary gates`

Closure replay (serialized):

1. 5-round self-test replay: `overall_passed=true`
   - positive path: session-chain wrapper status `PASS_REQUIRED` with `Identity-Context:` first line.
   - negative path: direct egress and direct runner bypass both fail-closed.
2. 5-round deep-scan replay: `overall_passed=true`
   - `validate_required_gate_surface_drift`: `PASS_REQUIRED`
   - `validate_control_plane_invariants`: `PASS_REQUIRED`
   - `render_control_plane_status --write`: expected control-plane status rendering completed each round
   - `validate_control_plane_status_sync`: `PASS_REQUIRED`
3. trust-boundary suite replay remains green after upgrade:
   - forged runner/grant probes blocked
   - direct egress-wrapper call blocked
   - `session_chain_headstamp_first_line_required` positive probe passed

### 26.8 Deep-scan residual closure checkpoint (2026-03-14)

Commit landed in this checkpoint:

1. `abb3e3f` `feat(v1.6.6): enforce AST-level wrapper bus import/call checks on strict surfaces`
   - upgraded strict-surface bus enforcement from plain token matching to AST-level validation;
   - requires real import + real call of `run_gateway_wrapped_command`;
   - rejects legacy helper usage on strict surfaces with fail-close drift reporting.

Serialized verification in this checkpoint:

1. `python3 -m py_compile scripts/validate_required_gate_surface_drift.py` -> pass.
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`.
3. `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` -> `rc=0` (all forged/direct-bypass negatives blocked, headstamp-required positive probe passed).
4. `python3 scripts/validate_control_plane_invariants.py --json-only` -> `PASS_REQUIRED`.
5. `python3 scripts/validate_control_plane_status_sync.py --json-only` -> `PASS_REQUIRED`.
6. `python3 scripts/docs_command_contract_check.py` -> `PASS`.
7. `python3 scripts/validate_doc_evidence_persistence.py --json-only` -> `PASS_REQUIRED`.
8. `python3 scripts/full_identity_protocol_scan.py --scan-mode target --target-source-layer project --identity-ids base-repo-audit-expert-v3 --actor-id assistant:codex --session-id run:v166-broadcast-follow-session --expected-work-layer protocol --expected-source-layer project` completed with:
   - `m2m_binding_closure_status=PASS`;
   - remaining `P0` items are non-m2m instance feedback contracts (`IP-SPLIT-001`, `IP-SEM-004`, `IP-COV-001`), not protocol wrapper bus execution regressions.

Verdict update:

1. v1.6.6 protocol-side drift governance is now resistant to comment/string spoof on strict surfaces.
2. Required trust-boundary probes and control-plane gates remain green after AST hardening.
3. No new protocol-level wrapper bus residuals detected in this checkpoint.

### 26.9 Send-time wrapper tuple fallback hardening (2026-03-14)

Commit landed in this checkpoint:

1. `gateway_wrapper_enforcement.py` tuple fallback enhancement in `run_final_emit_via_instance_wrappers`.

Problem observed:

1. target deep-scan `send_time_reply_gate` could fail with
   `IP-HDSTAMP-003` + `session_chain_canonical_tuple_missing:actor_id_mismatch`
   when instance session-chain wrapper payload omitted `actor_id` in return body.
2. this was a transport-shape mismatch, not an actor/session bypass acceptance.

Fix:

1. wrapper bridge now fills missing tuple fields from the already explicit caller tuple:
   - `run_id`
   - `actor_id`
   - `session_id`
2. fallback is **missing-only** (no override when payload already carries a value);
   mismatched explicit values still fail-close.
3. bridge emits `session_chain_tuple_fallback_fields` for replay observability.

Result:

1. send-time wrapper path no longer fails only due absent tuple fields in legacy
   session-chain payload shape.
2. tuple consistency guard remains active for real mismatches.

### 26.10 Commentary-channel P0 closure checkpoint (2026-03-14)

Commits landed in this checkpoint:

1. `3036466` `feat(v1.6.6): add host-visible surface registry and wrapper template attestation contracts`
2. `13948ec` `feat(v1.6.6): require host-visible surface live probes in required lane`

Root-cause class addressed:

1. Host-visible sender channel bypass (especially `commentary`) could evade physical attestation in prior baseline.
2. Wrapper files existed, but no canonical host-visible channel registry + live transport attestation probe existed as required infrastructure.

Protocol-side infrastructure added:

1. New contract key: `host_visible_surface_registry_contract_v1`.
2. New validator: `scripts/validate_host_transport_wiring_attestation.py`.
3. New required CI delegate: `scripts/ci/run_host_visible_surface_live_probes_ci.sh`.
4. Required lane wiring:
   - `.github/workflows/_identity-required-gates.yml` now executes host-visible live probes.
   - `scripts/validate_required_gate_surface_drift.py` fail-closes if this delegate/probe tokens drift.
5. Wrapper attestation hardening:
   - `wrapper_template_attestation_policy` is now required in host gateway contract.
   - validator checks ingress/egress/session-chain template hashes and required semantic tokens.
6. Runtime parity hardening:
   - runtime gateway contract must mirror both:
     - `host_visible_surface_registry_contract_v1`
     - `wrapper_template_attestation_policy`

Serialized verification (base-repo-audit-expert-v3):

1. Backfill/materialize:
   - `python3 scripts/repair_contract_backfill.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --apply --json-only`
   - result: `host_visible_surface_contract_auto_wire_status=PASS_REQUIRED`
2. 5-round self serial replay:
   - scoreboard:
     - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-audit-expert-v3/runtime/reports/v166-self-serial5/scoreboard-v166-self-serial5-1773482502.json`
   - result: `overall_passed=true`
   - each round included:
     - session-chain positive pass
     - unique-entry receipt validation pass
     - host-transport attestation validator pass
     - direct runner bypass blocked
     - direct final-emit bypass blocked
3. 5-round deep-scan serial replay:
   - scoreboard:
     - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-audit-expert-v3/runtime/reports/v166-deepscan-serial5/scoreboard-v166-deepscan-serial5-1773482601.json`
   - result: `overall_passed=true`
4. Host-visible live probe suite:
   - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh` -> `rc=0`
   - enforced probes:
     - `host_visible_contract_static`
     - `host_visible_live_receipts_pass`
     - `host_visible_commentary_bypass_blocked` (`rc=1` expected fail-close probe)

Checkpoint verdict update:

1. v1.6.6 now has protocol-native host-visible channel registry + live attestation probes in required lane.
2. Commentary-channel bypass class is now machine-detected and required-lane fail-close, not operator memory-dependent.

### 26.11 Inspection-lane correlation seeding closure (2026-03-14)

Commit landed in this checkpoint:

1. `fix(v1.6.6): gate default correlation seeding by operation scope for protocol-feedback lane validators`
   - introduced operation-aware default correlation seeding policy in:
     - `scripts/protocol_feedback_lane_common.py`
   - strict operations (`activate|update|readiness|e2e|ci|validate|mutation`) keep historical default seeding for resilience;
   - inspection operations (`scan|three-plane|inspection`) disable historical default seeding when no explicit `run_id` / `correlation_key` is provided, preventing false current-round linkage.

Surfaces aligned under this closure:

1. `scripts/validate_instance_protocol_split_receipt.py`
2. `scripts/validate_vendor_namespace_separation.py`
3. `scripts/validate_protocol_feedback_sidecar_contract.py`
4. `scripts/validate_semantic_routing_guard.py`
5. `scripts/validate_protocol_vendor_semantic_isolation.py`
6. `scripts/validate_protocol_data_sanitization_boundary.py`
7. `scripts/validate_external_source_trust_chain.py`

Serialized verification in this checkpoint:

1. `python3 -m py_compile` across all touched validators/common helper -> `PYC_OK`.
2. Inspection-lane explicit checks (no run-id) now resolve to scoped skip instead of false requiredization:
   - `validate_instance_protocol_split_receipt --operation scan` -> `SKIPPED_NOT_REQUIRED`.
   - `validate_vendor_namespace_separation --operation scan` -> `SKIPPED_NOT_REQUIRED`.
   - `validate_protocol_feedback_sidecar_contract --operation scan` -> non-blocking skip path with `required_contract=false`.
3. Strict-lane behavior preserved:
   - same validators under `--operation validate` remain required and fail-close where evidence is missing.
4. Coverage closure:
   - `validate_required_contract_coverage --operation scan` for `base-repo-audit-expert-v3` now exits `rc=0`, with prior false `IP-COV-001` pressure removed from inspection lane.
5. Deep-scan target replay with actor-bound session:
   - `full_identity_protocol_scan --scan-mode target --identity-ids base-repo-audit-expert-v3 --target-source-layer project --actor-id assistant:codex --session-id run:v166-broadcast-follow-session`
   - result: `summary.p0=0`, `summary_m2m.pass=1`, `severity=OK` for the target identity.

Checkpoint verdict update:

1. v1.6.6 inspection-lane protocol-feedback requiredization no longer over-links historical activity by default.
2. strict lanes retain fail-close pressure; no downgrade of strict governance semantics was introduced.
