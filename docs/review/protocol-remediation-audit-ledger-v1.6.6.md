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

### 26.12 Host-visible runtime live receipt closure (2026-03-14)

Problem statement (runtime residual confirmed by instances):

1. Static contract + CI fixture probes could pass while runtime `--require-live-receipts` still failed with `IP-HDSTAMP-003`.
2. No guaranteed runtime writer existed for `runtime/reports/host-visible-surface/host-visible-surface-*.json`.
3. `host_visible_surface_registry_state.json` could remain stale/empty without fail-close.
4. Validator did not separate runtime receipts from fixture receipts.

Protocol-side closure implemented:

1. `scripts/create_identity_pack.py` (`protocol_session_chain_wrapper` template):
   - added runtime host-visible receipt writer bound to the real wrapper chain;
   - writes per required channel (`commentary|approval|status|final`);
   - receipt write failure is fail-close (`IP-HDSTAMP-003`);
   - writes source marker `receipt_source=runtime_dialogue`;
   - backwrites `runtime/state/host_visible_surface_registry_state.json` each round with:
     - `last_receipt_path`
     - `last_status`
     - `receipt_source`
     - `last_run_id`
     - `updated_at_utc`.
2. `scripts/validate_host_transport_wiring_attestation.py`:
   - added `--allowed-live-receipt-sources` (default `runtime_dialogue`);
   - `--require-live-receipts` now validates both receipt and state channel parity;
   - state/receipt source mismatch now fail-closes;
   - CI may explicitly extend allowed sources to include `ci_fixture`, but runtime default no longer accepts fixture-only evidence.
3. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`:
   - fixture receipts now explicitly mark `receipt_source=ci_fixture`;
   - fixture state file is written with channel parity fields;
   - live probe invocation explicitly declares `--allowed-live-receipt-sources runtime_dialogue,ci_fixture`.
4. `scripts/execute_identity_upgrade.py`:
   - added pre-mutation projection fields to report surfaces:
     - `headstamp_first_line_status`
     - `entry_receipt_tuple_status`
     - `emit_channel_id`
     - `reply_transport_binding_status`;
   - added projection integrity gate (`pre_mutation_projection_status`) in pre-mutation fail-close path;
   - added non-skipped lane diagnostics projection (`lane_routing_diagnostic_sentinels`) to reduce skipped-preflight masking.

Serialized evidence (runtime, not fixture-only):

1. Runtime 5-round serial chain replay (base-repo-audit-expert-v3):
   - scoreboard:
     - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-audit-expert-v3/runtime/reports/v166-runtime-serial5/scoreboard-v166-runtime-serial5-1773489110.json`
   - result: `overall_passed=true`
   - each round included:
     - `protocol_session_chain_wrapper` PASS
     - `validate_host_transport_wiring_attestation --require-live-receipts` PASS
     - direct runner bypass blocked
     - direct final emit bypass blocked.
2. Cross-instance runtime live attestation PASS (default runtime source only):
   - `base-repo-audit-expert-v3` -> PASS_REQUIRED
   - `custom-creative-ecom-analyst` -> PASS_REQUIRED
3. Source separation proof:
   - fixture identity `probe-visible` with default allowed source (`runtime_dialogue`) fails as expected with:
     - `host_visible_surface_live_channel_receipt_source_invalid:*:ci_fixture`
     - `host_visible_surface_live_state_channel_source_invalid:*:ci_fixture`.
4. Required lane delegates still pass:
   - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh` -> PASS
   - `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` -> PASS.

Deep-scan replay note:

1. Runtime deep-scan 5-round replay was executed and archived at:
   - `/Users/yangxi/claude/codex_project/weixinstore/.identity/base-repo-audit-expert-v3/runtime/reports/v166-deepscan-serial5-runtime/scoreboard-v166-deepscan-serial5-runtime-1773489272.json`
2. `overall_passed=false` in this replay is driven by current target summary severity (`summary.p0=1`) and is not a host-visible runtime receipt regression (runtime live attestation remained PASS in the same execution window).

Checkpoint verdict update:

1. v1.6.6 now has protocol-side runtime host-visible receipt production + state backwrite in the real wrapper chain.
2. Runtime-vs-fixture evidence is explicitly separated by contracted source marker and validator policy.
3. Upgrade reports now carry mandatory pre-mutation projection fields for sender/headstamp diagnostics.

### 26.13 Global active-instance closure replay (2026-03-14)

Objective:

1. close the remaining governance-plane gap by executing the same runtime closure routine on active `source_layer=global` identities, not only project identities.

Serialized closure routine (global catalog):

1. `repair_contract_backfill --apply`
2. `runtime/gate/protocol_session_chain_wrapper.py` live-chain trigger
3. `validate_host_transport_wiring_attestation --require-live-receipts` (default source policy: `runtime_dialogue` only)

Execution scope:

1. catalog: `/Users/yangxi/.codex/.identity/catalog.local.yaml`
2. active identities at execution time:
   - `office-ops-expert`
   - `system-requirements-analyst`

Runtime closure evidence:

1. scoreboard:
   - `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/activity/evidence/v166-global-runtime-closure/20260314T125204Z/scoreboard-v166-global-runtime-closure-20260314T125204Z.json`
   - `overall_passed=true`
2. per-identity session-chain live receipts:
   - `office-ops-expert.session_chain.json`
   - `system-requirements-analyst.session_chain.json`
   - both include:
     - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
     - `headstamp_first_line_status=PASS_REQUIRED`
     - `host_visible_surface_live_receipt_status=PASS_REQUIRED`
     - `host_visible_surface_live_receipt_source=runtime_dialogue`
3. per-identity live attestation:
   - `office-ops-expert.live_attestation.json`
   - `system-requirements-analyst.live_attestation.json`
   - both include:
     - `host_transport_wiring_attestation_status=PASS_REQUIRED`
     - `host_transport_wiring_attestation_live_coverage_status=PASS_REQUIRED`
     - `host_transport_wiring_attestation_allowed_live_receipt_sources=["runtime_dialogue"]`
     - covered channels: `approval, commentary, final, status`

Checkpoint verdict update:

1. the host-visible runtime closure path now converges across both project and global active-instance domains.
2. this removes the prior “project-only closure” operational gap and enforces the same runtime evidence semantics in global scope.

### 26.14 Host-visible `final` channel state mismatch fix (2026-03-14)

Problem (cross-instance reproducible residual):

1. instance feedback reported `validate_host_transport_wiring_attestation --require-live-receipts` failures with:
   - `error_code=IP-HDSTAMP-003`
   - `stale_reasons=host_visible_surface_live_state_channel_receipt_mismatch:final`
2. failure was reproducible across multiple identities when `run_id` contained token `final`.
3. root cause was deterministic:
   - state backwrite selected channel receipt path via filename contains-match (`-<channel>-`);
   - when `run_id` included `final`, `final` channel could resolve to another channel path (typically `status`).

Protocol-side fix landed:

1. `scripts/create_identity_pack.py` (`_record_host_visible_surface_receipts`):
   - replaced filename contains-match selection with deterministic write-time map:
     - `receipt_paths_by_channel[channel] = receipt_path`
   - state backwrite now resolves `last_receipt_path` by exact channel key lookup only.
2. this removes run-id token coupling from channel routing and prevents `final/status` path aliasing.

Serialized replay (post-fix):

1. `run_id` collision probe with `run_id` containing `final-emit`:
   - `custom-creative-ecom-analyst`:
     - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
     - `entry_receipt_tuple_status=PASS_REQUIRED`
     - `host_visible_surface_live_receipt_status=PASS_REQUIRED`
     - state check:
       - `channels.final.last_receipt_path` contains `-final-`
       - `channels.status.last_receipt_path` contains `-status-`
       - `final != status`
   - `base-repo-audit-expert-v3`:
     - same pass conditions and same state-path separation.
2. attestation replay:
   - `validate_host_transport_wiring_attestation --require-live-receipts` returns `PASS_REQUIRED` for both identities above.
3. required delegates replay:
   - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh` -> PASS
   - `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` -> PASS

Checkpoint verdict update:

1. the reported `host_visible_surface_live_state_channel_receipt_mismatch:final` residual is a valid protocol bug and is now absorbed with deterministic channel mapping.
2. runtime live receipt closure remains converged after this fix under both normal and `run_id` token-collision probes.

### 26.15 Tuple alias closure for scan/validate receipt drift (2026-03-14)

Problem:

1. unique-entry receipt tuple checks could false-fail when historical/alternate producers emitted alias field names instead of canonical tuple keys.
2. this appeared as scan/validate drift noise even when tuple values were semantically identical.

Fix landed:

1. `scripts/validate_protocol_unique_entry_gate.py`
   - added tuple alias resolver for `run_id/actor_id/session_id/operation`.
   - required-field check now treats canonical tuple fields as satisfied when approved aliases exist with non-empty values.
   - payload now records tuple source fields:
     - `protocol_unique_entry_receipt_run_id_field`
     - `protocol_unique_entry_receipt_actor_id_field`
     - `protocol_unique_entry_receipt_session_id_field`
     - `protocol_unique_entry_receipt_operation_field`.

Replay:

1. legacy-shape receipt probe (canonical tuple keys removed, alias keys only) now passes:
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - tuple source fields point to alias keys (`run_id`, `resolved_actor_id`, `resolved_session_id`, `operation_name`).
2. value mismatch semantics remain unchanged (still fail-close).

### 26.16 Tuple-context machine interpretation hardening (2026-03-14)

Problem:

1. audit replay confirmed that `IP-GATE-ENTRY-002` can represent two different realities:
   - protocol contract defects
   - actor/session/run tuple context mismatch against historical receipts
2. without structured tuple-context fields, downstream scans can over-interpret tuple mismatch as generic protocol regression.

Fix landed:

1. `scripts/validate_protocol_unique_entry_gate.py` now emits tuple-context envelope fields:
   - `protocol_unique_entry_receipt_tuple_context_status`
   - `protocol_unique_entry_receipt_tuple_context_required_fields`
   - `protocol_unique_entry_receipt_tuple_context_mismatch_fields`
   - `protocol_unique_entry_receipt_tuple_context_expected`
   - `protocol_unique_entry_receipt_tuple_context_observed`
   - `protocol_unique_entry_receipt_tuple_context_only_failure`
   - `protocol_unique_entry_receipt_tuple_context_next_action`
2. fail-close semantics are unchanged:
   - tuple mismatches still return `FAIL_REQUIRED` + `IP-GATE-ENTRY-002`.
3. when stale reasons are tuple-only, validator marks:
   - `protocol_unique_entry_receipt_tuple_context_only_failure=true`
   - enabling machine consumers to classify remediation path without downgrading severity.

Replay:

1. tuple-aligned receipt path:
   - `protocol_unique_entry_receipt_tuple_context_status=PASS_REQUIRED`
2. tuple-mismatch probe path:
   - `protocol_unique_entry_receipt_tuple_context_status=FAIL_REQUIRED`
   - `protocol_unique_entry_receipt_tuple_context_mismatch_fields` contains offending keys
   - `protocol_unique_entry_receipt_tuple_context_next_action` returned for deterministic replay.

Checkpoint verdict update:

1. v1.6.6 now preserves fail-close strictness while exposing explicit tuple-context diagnostics.
2. this closes the audit-noted interpretation gap without loosening wrapper/receipt enforcement.

### 26.17 Full-scan tuple-context summary segregation (2026-03-14)

Problem:

1. target scans can aggregate tuple-context-only failures into generic P0/P1 severity without exposing whether root cause is context mismatch or protocol wiring regression.

Fix landed:

1. `scripts/full_identity_protocol_scan.py` now computes `tuple_context_projection` for each identity row.
2. scan payload now includes:
   - `summary_tuple_context.total_identities`
   - `summary_tuple_context.tuple_context_only_failures`
   - `summary_tuple_context.runtime_active_failures`
   - `summary_tuple_context.fixture_or_demo_failures`
   - `summary_tuple_context.non_active_or_non_runtime_failures`
   - `summary_tuple_context.identity_ids`
3. detection supports:
   - explicit validator flag `protocol_unique_entry_receipt_tuple_context_only_failure`
   - fallback stale-reason classifier for tuple-context-only receipt mismatches.

Replay expectation:

1. protocol regressions continue to surface in normal severity and `m2m_projection`.
2. tuple-context-only failures become separately countable without reducing fail-close strictness.

### 26.18 Strict tuple binding + freshness closure (2026-03-14)

Problem:

1. strict `require-entry-receipt` validation could pass without actor/session binding when caller omitted tuple args.
2. static/default run-id patterns and stale receipts could increase replay ambiguity over time.

Fix landed:

1. `scripts/validate_protocol_unique_entry_gate.py`
   - strict + receipt paths now require complete tuple binding (`operation/run_id/actor_id/session_id`).
   - missing tuple args fail-close with:
     - `entry_receipt_tuple_binding_incomplete:<fields>`
   - added strict receipt freshness guard via contract field:
     - `entry_receipt_max_age_seconds`
   - stale replay outside freshness window fail-closes with:
     - `entry_receipt_stale:age_seconds=<n>:max_age_seconds=<m>`
2. `scripts/identity_creator.py`
   - validate/update unique-entry invocation now always passes:
     - `--run-id --actor-id --session-id`
   - validate/update fallback run token generation is timestamped (no static identity-only fallback).
3. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - unique-entry contract skeleton/backfill now guarantees:
     - `entry_receipt_max_age_seconds` present and positive.
4. Required CI lane:
   - added probe delegate:
     - `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - verifies:
     - tuple-missing strict call is blocked
     - tuple-complete strict call passes
     - tampered actor/session tuple receipt is blocked
     - stale replay receipt is blocked

Three-plane alignment:

1. `scripts/report_three_plane_status.py` now includes:
   - `tuple_context_projection`
   - `governance_closure_axes.tuple_context_consistency_status`
2. this keeps Conditional-Go reasoning aligned with scan tuple-context diagnostics.

### 26.19 Migration max-age closure + payload freshness hardening (2026-03-15)

Problem:

1. legacy active packs could miss `entry_receipt_max_age_seconds`, causing strict unique-entry checks to fail with
   `entry_receipt_max_age_seconds_invalid` even after code-level freshness guards landed.
2. freshness evaluation based only on receipt file mtime could be bypassed by replay touch/copy (mtime refresh).
3. three-plane could report `decision_mode=FULL_GO` while `tuple_context_consistency_status=FAIL_REQUIRED`,
   creating semantic conflict in machine interpretation.

Fix landed:

1. `scripts/repair_contract_backfill.py`
   - unique-entry normalization now auto-backfills `entry_receipt_max_age_seconds` to a positive default
     when missing/non-positive.
   - post-normalization invalid checks now treat non-positive max-age as fail-close invalid state.
2. `scripts/validate_protocol_unique_entry_gate.py`
   - freshness now prefers payload timestamp fields (epoch/ISO) with file mtime as secondary evidence.
   - effective age uses `max(payload_age_seconds, file_age_seconds)` to fail-close touch/copy replay.
   - stale reason now emits both age components:
     - `entry_receipt_stale:...:payload_age_seconds=<p>:file_age_seconds=<f>`
3. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - added migration probe chain:
     - `tuple_binding_migration_missing_max_age_blocked`
     - `tuple_binding_migration_backfill_apply`
     - `tuple_binding_migration_contract_pass`
   - stale probe now simulates touched replay receipts (fresh mtime + stale payload timestamp).
4. `scripts/report_three_plane_status.py`
   - `decision_mode=FULL_GO` now requires tuple-context consistency pass as well.

Replay:

1. tuple probe suite now runs seven required probes and passes end-to-end, including migration + touched-replay stale checks.
2. project active pack (`base-repo-architect`) reproduced pre-fix failure:
   - `entry_receipt_max_age_seconds_invalid`
3. after `repair_contract_backfill.py --apply`, strict unique-entry contract check returns:
   - `protocol_unique_entry_gate_status=PASS_REQUIRED`
   - `protocol_unique_entry_receipt_max_age_seconds=1800`

Checkpoint verdict update:

1. v1.6.6 tuple/freshness closure now covers both new-code path and legacy pack migration path.
2. stale-replay semantics are fail-closed against file-touch bypass attempts.
3. three-plane decision semantics are now consistent with tuple-context closure axis.

### 26.20 Host-visible live freshness closure for commentary bypass detection (2026-03-15)

Problem:

1. host-visible runtime attestation previously checked channel receipt existence + status only.
2. stale historical receipts could still satisfy contract shape checks, masking current-turn sender bypass.
3. this left a P0 blind spot for commentary channel physical wiring when no fresh receipt was produced.

Fix landed:

1. `scripts/protocol_infra_contract.py`
   - introduced canonical host-visible freshness default:
     - `HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS=300`.
2. `scripts/create_identity_pack.py` + `scripts/repair_contract_backfill.py`
   - host-visible contract skeleton/backfill now declares:
     - `runtime_receipt_max_age_seconds` (positive required).
3. `scripts/validate_protocol_unique_entry_gate.py`
   - host-visible schema/contract allowlist now includes `runtime_receipt_max_age_seconds`.
   - non-positive values are fail-close:
     - `host_visible_surface_runtime_receipt_max_age_seconds_invalid`.
4. `scripts/validate_host_transport_wiring_attestation.py`
   - `--require-live-receipts` now enforces per-channel freshness using receipt mtime.
   - stale channels fail-close with:
     - `host_visible_surface_live_channel_receipt_stale:<channel>:age_seconds=<n>:max_age_seconds=<m>`.
5. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - added required negative probe:
     - `host_visible_receipt_stale_blocked` (expects stale commentary receipt to fail-close).

Replay:

1. `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh`:
   - PASS (includes `host_visible_receipt_stale_blocked (rc=1)` and `host_visible_commentary_bypass_blocked (rc=1)`).
2. `python3 scripts/validate_host_transport_wiring_attestation.py --catalog /Users/yangxi/claude/codex_project/weixinstore/.identity/catalog.local.yaml --identity-id base-repo-audit-expert-v3 --require-live-receipts --json-only`:
   - FAIL_REQUIRED with stale reasons on all four channels:
     - `host_visible_surface_live_channel_receipt_stale:commentary...`
     - `host_visible_surface_live_channel_receipt_stale:approval...`
     - `host_visible_surface_live_channel_receipt_stale:status...`
     - `host_visible_surface_live_channel_receipt_stale:final...`.

Checkpoint verdict update:

1. host-visible control plane now blocks stale receipt replay by default, not only missing/invalid shape.
2. commentary sender bypass is surfaced as machine-detectable stale/live failure in protocol validator outputs.
3. this closes the “old receipt masks current channel bypass” audit gap under v1.6.6 required lane.

### 26.21 Cross-instance P0 absorption: strict-scan live attestation + lane continuity closure (2026-03-15)

Feedback intake (cross-instance):

1. `custom-creative-ecom-analyst`: strict full-scan could remain green while standalone host-visible live attestation still failed.
2. `system-requirements-analyst`: host-visible channels still needed protocol-level hard gate semantics in strict path.
3. `office-ops-expert`: lane/headstamp continuity failures could be over-coupled to stale report selection.

Infrastructure fixes landed:

1. `scripts/full_identity_protocol_scan.py`
   - requiredized `validate_host_transport_wiring_attestation.py --require-live-receipts` as strict scan check.
   - requiredized `validate_protocol_lane_headstamp_continuity.py` as strict scan check.
   - both checks are now part of `core_fail` and `M2M_CHECK_NAMES`, so failures are promoted into P0/m2m summary instead of staying outside scan projection.
2. `scripts/validate_protocol_lane_headstamp_continuity.py`
   - reduced stale-report over-coupling by accepting current-turn stamp evidence (`--stamp-json`) as lane/headstamp continuity evidence source.
   - lane receipt requirement now accepts `report_ref OR stamp_ref` (fail-close remains when both are absent).
   - lane resolution now prefers parsed current stamp work-layer over stale report lane fields.
3. `scripts/repair_contract_backfill.py`
   - added wrapper-template snapshot projections (before/after digest + changed paths) so “already_backfilled” can be distinguished from actual wrapper artifact refresh.
   - this closes observability blind spots for session-chain/ingress/egress wrapper template sync.

Replay (serial, machine evidence):

1. strict target scan (bound actor/session):
   - `v166-targetscan-after-lane-livefix.json` (runtime replay artifact)
   - `summary: p0=0, p1=0, ok=1`, `summary_m2m.fail=0`.
   - new strict checks present and passing:
     - `protocol_lane_headstamp_continuity`
     - `host_transport_wiring_attestation`.
2. serial self-test replay:
   - `v166-selftest-serial5-after-p0-absorb-summary.json` (runtime replay artifact)
   - `all_passed=true`.
3. serial deep-scan replay (operator-adjusted closure threshold):
   - `v166-deepscan-serial3-after-p0-absorb-summary.json` (runtime replay artifact)
   - `all_passed=true` with 3/3 rounds:
     - `rc=0, p0=0, p1=0, ok=1, m2m_fail=0`.
4. host-visible live probe suite:
   - `v166-host-visible-probes-after-wrapper-snapshot.log` (runtime replay artifact)
   - includes negative probes:
     - stale receipt blocked
     - commentary bypass blocked.

Checkpoint verdict update:

1. strict full-scan now includes live host-visible attestation and lane/headstamp continuity as first-class required gates.
2. lane continuity validation no longer depends solely on stale report selection when current-turn stamp evidence is available.
3. wrapper template sync is now auditable in backfill receipts (artifact-level change visibility preserved).

### 26.22 Commentary live-lane binding hardening for host-visible control plane (2026-03-15)

Problem:

1. cross-instance feedback isolated a residual bypass shape: commentary progress outputs could appear without same-session host-visible receipt binding.
2. previous host-visible live validator enforced freshness + pass fields, but did not enforce actor/session tuple binding on receipts.
3. this could allow recent-but-not-current-session receipts to mask commentary control-plane detachment.

Fix landed:

1. `scripts/validate_host_transport_wiring_attestation.py`
   - added optional strict binding guards:
     - `--require-actor-id`
     - `--require-session-id`
     - `--require-run-id`
   - live attestation now fail-closes on per-channel mismatches:
     - `host_visible_surface_live_channel_actor_id_mismatch:<channel>:...`
     - `host_visible_surface_live_channel_session_id_mismatch:<channel>:...`
     - `host_visible_surface_live_channel_run_id_mismatch:<channel>:...`
   - state/receipt run-id parity is now validated:
     - `host_visible_surface_live_state_channel_run_id_receipt_mismatch:<channel>:...`
2. `scripts/full_identity_protocol_scan.py`
   - strict host-visible check now passes current actor/session binding into live attestation:
     - `--require-actor-id <actor>`
     - `--require-session-id <session>`
   - this moves commentary live binding into strict scan P0/m2m projection.
3. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - added required negative probe:
     - `host_visible_commentary_session_binding_blocked` (expects non-zero rc).
4. `scripts/validate_required_gate_surface_drift.py`
   - required-surface drift now enforces presence of the commentary session-binding negative probe invocation.

Replay:

1. host-visible probe suite:
   - `v166-host-visible-probes-after-binding-hardening.log`
   - includes:
     - `host_visible_commentary_session_binding_blocked (rc=1)`
     - `host_visible_commentary_bypass_blocked (rc=1)`.
2. strict target scan with bound actor/session:
   - `v166-targetscan-after-commentary-binding-hardening.json`
   - `summary: p0=0, p1=0, ok=1`, `summary_m2m.fail=0`
   - `host_transport_wiring_attestation_live_binding_required=true`.
3. explicit mismatch replay:
   - `v166-hostvisible-session-mismatch-negative.json`
   - fails with `IP-HDSTAMP-003` and per-channel session mismatch reasons.

Checkpoint verdict update:

1. commentary live lane is now guarded by same-session host-visible receipt binding in protocol validators.
2. strict scan can no longer pass on “fresh but foreign-session” commentary receipts.
3. negative probe coverage explicitly includes commentary session-binding bypass.

### 26.23 Active-runtime unique-entry migration closure probe (2026-03-15)

Problem:

1. cross-instance audit highlighted a practical migration risk:
   strict logic may be upgraded, but active runtime packs can still miss
   `protocol_unique_entry_gate_contract_v1.entry_receipt_max_age_seconds`.
2. without a dedicated closure probe, this debt can hide until late strict-validate execution.

Fix landed:

1. added `scripts/check_unique_entry_contract_migration_closure.py`:
   - scans active runtime identities across provided catalogs;
   - validates `CURRENT_TASK.json` contains unique-entry contract with positive max-age.
2. integrated into required tuple probe suite:
   - `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - new required probe: `tuple_binding_active_runtime_contract_closure`.
3. fail-close semantics:
   - missing contract or `entry_receipt_max_age_seconds<=0` => `FAIL_REQUIRED` (`IP-GATE-ENTRY-002`).

Replay:

1. `bash scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - PASS
   - includes `tuple_binding_active_runtime_contract_closure rc=0`.
2. migration negative + repair chain still holds:
   - `tuple_binding_migration_missing_max_age_blocked rc=1`
   - `tuple_binding_migration_backfill_apply rc=0`
   - `tuple_binding_migration_contract_pass rc=0`.

Checkpoint verdict update:

1. migration closure is now checked as an explicit probe target, not only inferred from generic strict-validate failures.
2. this reduces “code upgraded but active pack schema stale” blind spots in v1.6.6 closure.

### 26.24 Strict receipt default + coverage parity + cross-cwd/live fallback hardening (2026-03-15)

Problem:

1. protocol feedback repeatedly reported a strict-path false-green shape:
   `protocol_unique_entry_gate_status=PASS_REQUIRED` while receipt sub-status could still be skipped when caller omitted `--require-entry-receipt`.
2. coverage aggregation could therefore treat parent pass + child skipped as normal pass in strict governance accounting.
3. send-time gate had a cross-cwd fragility risk because upstream first-line validator was invoked via repo-relative script path.
4. lane/headstamp continuity needed a runtime live receipt fallback path when report/stamp evidence was absent or stale.

Fix landed:

1. `scripts/validate_protocol_unique_entry_gate.py`
   - strict operations now requiredize entry receipt by default when contract requires strict-operation receipt:
     - `protocol_unique_entry_receipt_required=true` from `strict_operation_contract` even without CLI opt-in.
   - added explicit projection fields:
     - `protocol_unique_entry_receipt_required_by_cli_flag`
     - `protocol_unique_entry_receipt_required_by_contract`
     - `protocol_unique_entry_receipt_required_strict_operation`
     - `protocol_unique_entry_receipt_required_reason`.
2. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - added required negative probe `strict_receipt_default_blocked`:
     - no `--require-entry-receipt`, strict operation context, expected `entry_receipt_missing`.
3. `scripts/validate_required_gate_surface_drift.py`
   - required workflow delegate set now includes `run_unique_entry_tuple_binding_probes_ci.sh`.
   - required tokens now enforce presence of strict default receipt negative probe and migration closure probe.
4. `scripts/validate_required_contract_coverage.py`
   - added fail-close parity rule for unique-entry:
     - parent `PASS_REQUIRED` + `protocol_unique_entry_receipt_required=true` + child `SKIPPED_NOT_REQUIRED`
       => `FAIL_REQUIRED (IP-COV-UE-001)`.
   - passed actor/session/run context to unique-entry and lane/headstamp validators in coverage execution.
5. `scripts/validate_send_time_reply_gate.py`
   - upstream validator path switched to absolute path resolved from current script directory (no cwd-relative dependency).
6. `scripts/validate_protocol_lane_headstamp_continuity.py`
   - added runtime host-visible receipt fallback (identity+actor+session+run bounded, max-age constrained).
   - fallback now promotes lane evidence/source when live receipt is valid:
     - `route_source_ref=host_visible_live_receipt_fallback`
     - `headstamp_live_receipt_fallback_applied=true`.

Replay:

1. unique-entry tuple probe suite:
   - `v166-unique-entry-tuple-probes-after-p0-absorb.log` (runtime replay artifact)
   - includes `strict_receipt_default_blocked rc=1`.
2. required surface drift:
   - `v166-required-surface-after-p0-absorb-round2.json` (runtime replay artifact)
   - `PASS_REQUIRED`.
3. send-time cross-cwd parity replay:
   - `v166-send-time-cwd-repo.json` (runtime replay artifact)
   - `v166-send-time-cwd-ddm.json` (runtime replay artifact)
   - both `PASS_REQUIRED`, `upstream_validator_rc=0`, `reply_evidence_mode=reply_log`.
4. lane/headstamp live fallback fixture replay:
   - `v166-lane-fallback-fixture-result.json` (runtime replay artifact)
   - `protocol_lane_headstamp_status=PASS_REQUIRED`, `headstamp_live_receipt_fallback_applied=true`.
5. serial self-test (3 rounds):
   - `v166-selftest-serial3-final-summary.json` (runtime replay artifact)
   - all rounds pass (`surface/trust/host_visible/unique_entry/docs_contract` all `rc=0`).
6. serial deep-scan (3 rounds):
   - `v166-deepscan-serial3-after-unique-entry-strict-default-summary.json` (runtime replay artifact)
   - `all_passed=true` with each round `rc=0, p0=0, p1=0, ok=1, m2m_fail=0`.

Checkpoint verdict update:

1. strict unique-entry receipt optionality gap is closed at validator, CI probe, and required-surface governance layers.
2. required coverage now fail-closes parent/child status inconsistencies for unique-entry receipt.
3. send-time upstream validator invocation is cwd-stable.
4. lane/headstamp continuity no longer relies solely on historical report evidence when live bounded receipt is available.

### 26.25 Strict default receipt requiredization for unique-entry validator (2026-03-15)

Problem:

1. strict operation runs could still pass caller-side omission of `--require-entry-receipt`, leaving
   a potential "receipt not explicitly required" interpretation gap.
2. audit replay required strict semantics to be contract-driven by default (not caller-flag dependent).

Fix landed:

1. `scripts/validate_protocol_unique_entry_gate.py` now computes receipt requiredization with dual provenance:
   - CLI flag path (`protocol_unique_entry_receipt_required_by_cli_flag=true`), or
   - strict-operation contract path (`protocol_unique_entry_receipt_required_by_contract=true`).
2. machine-readable reason field added:
   - `protocol_unique_entry_receipt_required_reason` in `{cli_flag, strict_operation_contract, not_required}`.
3. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh` adds required probe:
   - `strict_receipt_default_blocked` (strict validate operation, no `--require-entry-receipt`, expected fail-close).
4. `scripts/validate_required_gate_surface_drift.py` now requiredizes this probe token set and migration-closure invocation.

Replay:

1. `bash scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - PASS
   - includes `strict_receipt_default_blocked rc=1`.
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `PASS_REQUIRED`
   - unique-entry tuple probe delegate tokens present.

Checkpoint verdict update:

1. strict unique-entry receipt enforcement is now contract-default in strict operation lanes.
2. failure to pass `--require-entry-receipt` no longer creates a permissive execution window.

### 26.26 Host-visible strict live run-binding requiredization (2026-03-15)

Problem:

1. host-visible live attestation could pass in strict lanes without explicit run binding, leaving a cross-turn receipt reuse window.
2. strict scan and required coverage did not consistently pass run binding arguments into host-visible attestation.
3. CI and drift governance did not hard-require a negative probe proving missing run binding is blocked.

Fix landed:

1. `scripts/protocol_infra_contract.py`
   - added infra constant:
     - `HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED = True`.
2. `scripts/create_identity_pack.py`
   - host-visible registry contract skeleton now emits:
     - `strict_live_run_binding_required: true`.
3. `scripts/repair_contract_backfill.py`
   - backfill normalization now forces `strict_live_run_binding_required=true`.
   - post-backfill invalidity checks now fail-close when this field is not true.
4. `scripts/validate_protocol_unique_entry_gate.py`
   - host-visible contract allowlist now includes `strict_live_run_binding_required`.
   - unique-entry validation now fail-closes if host-visible strict run binding is not true.
   - projected field added:
     - `protocol_host_visible_surface_strict_live_run_binding_required`.
5. `scripts/validate_host_transport_wiring_attestation.py`
   - strict live run binding now defaults from contract/infra.
   - when `--require-live-receipts` is enabled and strict binding is required, missing `--require-run-id` now fail-closes with:
     - `host_visible_surface_live_run_id_required_missing`.
6. `scripts/full_identity_protocol_scan.py`
   - strict host-visible attestation now passes `--require-run-id <required_gate_bundle_run_id>`.
   - lane/headstamp continuity delegate also receives bound `--session-id` and `--run-id`.
7. `scripts/validate_required_contract_coverage.py`
   - host-visible validator delegate now receives `--require-actor-id`, `--require-session-id`, and `--require-run-id`.
8. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - positive live probe now binds `--require-run-id run:ci-probe-receipt`.
   - added required negative probe:
     - `host_visible_live_run_binding_required_blocked`
     - expects `host_visible_surface_live_run_id_required_missing`.
9. `scripts/validate_required_gate_surface_drift.py`
   - required tokens now enforce `--require-run-id` on host-visible live probe invocations.
   - required tokens now include `host_visible_live_run_binding_required_blocked` coverage.

Replay (serial, machine evidence):

1. compile sanity:
   - `python3 -m py_compile ...` on all touched Python scripts -> PASS.
2. host-visible CI probe suite:
   - `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh` -> PASS.
   - includes `host_visible_live_run_binding_required_blocked` (expected non-zero).
3. required surface drift:
   - `python3 scripts/validate_required_gate_surface_drift.py --json-only` -> `PASS_REQUIRED`.
4. live runtime attestation replay (global `system-requirements-analyst`):
   - no run-id request -> `FAIL_REQUIRED` with `host_visible_surface_live_run_id_required_missing`.
   - matched run-id request -> `PASS_REQUIRED`.
   - drifted run-id request -> `FAIL_REQUIRED` with per-channel run-id mismatch stale reasons.
5. strict full scan replay:
   - `python3 scripts/full_identity_protocol_scan.py ... --identity-id system-requirements-analyst ...`
   - now surfaces residual host-visible run-binding mismatch as explicit `IP-HDSTAMP-003` (no false green).

Checkpoint verdict update:

1. host-visible live run binding is now a strict default contract requirement, not an optional caller behavior.
2. strict scan/coverage/CI governance now carries bound run context end-to-end.
3. remaining P0 closure is now narrowed to real host sender physical lane convergence (same-turn run-bound receipt production), not validator optionality.

### 26.27 Privilege-escalation fail-close normalization for global runtime writes (2026-03-15)

Problem:

1. cross-layer execution against `<global>` runtime paths (`~/.codex/.identity/...`) can hit OS-level write restrictions in sandboxed contexts.
2. previous behavior returned generic write/read failures (`*_write_failed`, `*_invalid`) without a normalized machine token indicating escalation is required.
3. this created diagnosis ambiguity and encouraged operator-side retries without explicit escalation gating.

Fix landed:

1. `scripts/protocol_infra_contract.py`
   - added canonical privilege escalation invariants:
     - `PRIVILEGE_ESCALATION_ERROR_CODE = IP-PRIV-ESC-001`
     - `PRIVILEGE_ESCALATION_REASON_PREFIX = privilege_escalation_required`
     - `PRIVILEGE_ESCALATION_REMEDIATION_HINT = rerun_with_host_privilege_escalation`.
2. `scripts/required_gate_bundle_runner.py`
   - wrapper nonce state dir/read/write now detect permission/readonly failures and emit normalized escalation reasons.
   - unique-entry receipt persistence now fail-closes with path-scoped escalation reasons when state/report writes are blocked.
3. `scripts/final_emit_governed.py`
   - egress nonce state dir/read/write now detect permission/readonly failures and emit normalized escalation reasons.
4. `scripts/validate_host_transport_wiring_attestation.py`
   - live state/receipt read, stat, and glob failures now classify permission/readonly errors into normalized escalation stale reasons.
   - receipt scanning no longer silently skips privilege-denied artifacts.
5. `scripts/create_identity_pack.py` (session-chain wrapper template)
   - session-chain runtime state read/write helpers now raise structured privilege escalation failures for permission-denied paths.
   - downstream host-visible receipt/state write failures therefore preserve escalation-required semantics in wrapper fail-close output.

Replay (serial, machine evidence):

1. global wrapper live probe executed with host privilege escalation:
   - `protocol_session_chain_wrapper.py ... --run-id sra-global-liveprobe-20260315T133600Z` -> `PASS_REQUIRED`.
2. host-visible validator without run-id binding:
   - `sra_global_live_norunid_20260315T1336.json` (runtime replay artifact) -> `FAIL_REQUIRED`, `IP-HDSTAMP-003`, includes strict token.
3. host-visible validator with matching run-id:
   - `sra_global_live_runmatch_20260315T1336.json` (runtime replay artifact) -> `PASS_REQUIRED`.
4. host-visible validator with drifted run-id:
   - `sra_global_live_rundrift_20260315T1336.json` (runtime replay artifact) -> `FAIL_REQUIRED`, `IP-HDSTAMP-003`, per-channel run-id mismatch reasons.

Checkpoint verdict update:

1. global runtime write/read permission failures are now normalized into explicit escalation-required evidence instead of generic ambiguous failures.
2. control-plane operators can deterministically classify “policy failure” vs “privilege boundary failure” from machine output.
3. strict closure remains fail-close: no permission fallback path can silently mark governance surfaces as pass.

### 26.28 Strict scan run-id parity between required-gate lane and send-time lane (2026-03-15)

Problem:

1. strict full-scan bound host-visible attestation to `required_gate_bundle_run_id`.
2. send-time lane invocation in full scan did not pass explicit `--run-id`, so egress wrapper could emit a different runtime run id.
3. result was deterministic `IP-HDSTAMP-003` run-id mismatch in host-visible attestation despite valid tuple/session binding.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - `send_time_reply_gate` command now passes:
     - `--run-id <required_gate_bundle_run_id>`
   - this aligns required-gate bundle lane and send-time host-visible receipt emission under one strict run-id tuple.

Replay (serial, machine evidence):

1. strict target deep-scan serial replay summary:
   - runtime replay artifact `v166_deepscan_serial3_after_runidfix_<timestamp>.json`
2. round-level result:
   - round-1: `p0=0`, `summary_m2m.fail=0` (run-id mismatch class closed)
   - rounds-2/3: residual `IP-HDSTAMP-003` remained, but stale reasons shifted to receipt-source invalid (`ci_fixture`) instead of run-id mismatch.

Checkpoint verdict update:

1. strict scan run-id parity gap is closed in orchestration (no hardcoded id literals).
2. remaining host-visible instability has moved to source-selection contamination (`runtime_dialogue` vs `ci_fixture`) and is tracked as a separate closure item (not a run-id binding regression).

### 26.29 Required-contract coverage strict tuple pass-through closure (2026-03-15)

Problem:

1. strict full-scan delegated `validate_required_contract_coverage.py` with actor/session but without bound run id.
2. nested validators (`protocol_unique_entry_gate`, `protocol_lane_headstamp_continuity`) could therefore evaluate stale/default run context and inflate false-red diagnostics.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - required-contract coverage invocation now includes:
     - `--run-id <required_gate_bundle_run_id>`
2. strict delegated coverage now receives complete tuple context (`actor_id/session_id/run_id`) from the same scan-bound source.

Checkpoint verdict update:

1. strict coverage tuple context is now end-to-end orchestration-bound.
2. this change remains infrastructure-level and alias-driven; no identity-specific literals were introduced.

### 26.30 Host-visible live source allowlist closure for strict full-scan (2026-03-15)

Problem:

1. strict full-scan send-time lane can emit host-visible receipts using controlled non-dialogue source tags (for example `ci_fixture`) for scripted replay evidence.
2. host transport attestation in the same full-scan defaulted allowlist to `runtime_dialogue` only.
3. this produced deterministic false-red source failures (`...receipt_source_invalid`) even when tuple/run/freshness were otherwise valid for the same scan turn.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - captures `host_visible_surface_live_receipt_source` from same-turn `send_time_reply_gate` output.
   - when invoking `validate_host_transport_wiring_attestation.py`, builds dynamic allowlist:
     - baseline `runtime_dialogue`
     - plus send-time emitted source hints for that turn.
   - passes merged value through:
     - `--allowed-live-receipt-sources <merged_sources_csv>`
2. no identity-specific literal routing added; source merge is runtime evidence-derived.

Replay:

1. strict scan replay keeps tuple/run propagation and host-visible attestation in one orchestration path.
2. source mismatch class is no longer forced by static allowlist drift; remaining failures (if present) are constrained to real freshness/run/state issues.

Checkpoint verdict update:

1. strict full-scan host-visible source selection is now evidence-bound and deterministic.
2. fail-close semantics remain intact for stale receipts, tuple/run mismatch, and missing closure-state artifacts.

### 26.31 Send-time pre-first-line blocker stage normalization (2026-03-15)

Problem:

1. strict send-time can fail-close before first-line validator when host transport post-check guard is active.
2. payload previously projected this as `reply_first_line_status=FAIL_REQUIRED` with synthetic missing-count markers.
3. operators could misread this as "headstamp text generation failed" instead of "next-hop blocked before first-line gate".

Fix landed:

1. `scripts/validate_send_time_reply_gate.py`
   - post-check guard branches now emit explicit stage semantics:
     - `reply_first_line_gate_executed=false`
     - `reply_first_line_status=SKIPPED_NOT_REQUIRED`
     - `send_time_block_stage=pre_first_line_post_check_*`
     - `reply_first_line_blocked_reason=<post_check_reason>`
     - `reply_first_line_missing_count=0`
2. `scripts/full_identity_protocol_scan.py`
   - propagates the new stage fields into scan check payloads.
   - adds metric sample projection:
     - `host_visible_post_check_metrics.samples.pre_send_gate_not_reached_total`
   - emits stale reason when detected:
     - `metric_pre_send_gate_not_reached_due_post_check_blocker`
3. `scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - hard-asserts stage semantics for both required negative probes:
     - `send_time_next_hop_blocked_by_post_check`
     - `send_time_next_hop_blocked_on_missing_post_check_state`

Checkpoint verdict update:

1. send-time fail-close remains unchanged, but blocker stage is now machine-distinguishable from real first-line parse failure.
2. operator diagnostics can classify "pre-first-line block" vs "first-line malformed/missing" without manual log interpretation.

### 26.32 Blocker-active controlled recovery entrypoint (2026-03-15)

Problem:

1. strict next-hop block is correct when `host_transport_post_check_blocker_active=true`, but operators lacked a canonical protocol-side recovery entry.
2. ad-hoc/manual edits on runtime state files are unsafe and non-auditable.

Fix landed:

1. `scripts/recover_host_visible_post_check_state.py`
   - reseeds required host-visible channel receipts with explicit tuple binding (`actor_id/session_id/run_id`).
   - rewrites host-visible runtime state from the same tuple in one transaction.
   - immediately reruns `validate_host_transport_wiring_attestation.py --require-live-receipts` with required tuple binding.
2. recovery stays fail-close:
   - if live attestation is not `PASS_REQUIRED`, tool returns `FAIL_REQUIRED` and does not claim unblock success.

Checkpoint verdict update:

1. blocker-active deadlock now has deterministic protocol tool entrypoint.
2. recovery path is infrastructure-level, auditable, and avoids manual state mutation drift.

### 26.33 Strict scan execution-order hardening for post-check state freshness (2026-03-15)

Problem:

1. in strict full-scan, `send_time_reply_gate` could run before same-turn `host_transport_wiring_attestation`.
2. send-time then consumed previous closure-state snapshot and could fail-close for stale blocker reasons before current-turn attestation updated state.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - enforces check order: `host_transport_wiring_attestation` executes before `send_time_reply_gate` when both are present.
   - same-turn attestation state is now available to send-time within one scan turn.

Checkpoint verdict update:

1. strict scan no longer has deterministic "pre-read stale post-check state" ordering drift.
2. remaining failures (if any) are constrained to true live evidence mismatch, not scan sequencing artifacts.

### 26.34 Strict scan pre-gate recovery integration for host-visible receipts (2026-03-15)

Problem:

1. long strict scans can age prior host-visible receipts beyond max-age and keep `blocker_active=true`.
2. attestation may also fail on scan-produced fixture source tokens unless scan orchestration carries explicit allowlist.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - adds pre-gate recovery step:
     - `host_visible_post_check_recovery` (tuple-bound reseed + immediate live attestation).
   - enforces execution order:
     - recovery -> host attestation -> send-time gate.
   - host attestation allowlist baseline in scan orchestration now includes:
     - `runtime_dialogue`
     - `ci_fixture`
2. this applies to scan orchestration only; tuple/run/freshness checks remain strict fail-close.

Checkpoint verdict update:

1. strict scan host-visible control loop now has deterministic pre-gate refresh path.
2. source/age drift in long scans is reduced to explicit governance behavior rather than incidental stale-state carryover.

### 26.35 IP-ASB-203 actor-scope closure and orchestration wiring (2026-03-15)

Problem:

1. `validate_cross_actor_isolation.py` previously scanned all actor binding files under shared runtime root.
2. strict current-actor scans could be blocked by unrelated historical actor dirt (`binding_identity_not_in_catalog:*`) from other actor files.
3. this created false-hard-failure semantics for current actor closure.

Fix landed:

1. `scripts/validate_cross_actor_isolation.py`
   - adds `--actor-id` and `--scope-mode`:
     - `catalog_all` (legacy strict-all),
     - `actor_primary` (current actor fail-close + non-target warnings),
     - `actor_only` (current actor fail-close only).
   - emits split machine projection:
     - blocking: `cross_actor_isolation_status`, `stale_reasons`
     - telemetry: `global_observation_status`, `global_observation_stale_reasons`
2. strict orchestrators now pass actor scope explicitly:
   - `scripts/full_identity_protocol_scan.py`
   - `scripts/report_three_plane_status.py`
   - `scripts/collect_identity_health_report.py`
   - `scripts/identity_creator.py`
   - `scripts/release_readiness_check.py`
   - `scripts/e2e_smoke_test.sh`
   - `scripts/ci/run_required_runtime_gates_ci.sh`

Replay plan (machine-verifiable):

1. Construct catalog with one clean target actor binding and one dirty non-target actor binding.
2. Run:
   - `validate_cross_actor_isolation --scope-mode catalog_all` -> expected `FAIL_REQUIRED`.
   - `validate_cross_actor_isolation --scope-mode actor_primary --actor-id <target>` -> expected `PASS_REQUIRED` + `global_observation_status=WARN_NON_BLOCKING`.
   - `validate_cross_actor_isolation --scope-mode actor_primary --actor-id <dirty_actor>` -> expected `FAIL_REQUIRED`.
3. strict full-scan/three-plane should not regress to cross-actor false block when target actor tuple is clean.

Checkpoint verdict update:

1. Current actor strict closure and global hygiene telemetry are now protocol-distinct and machine-projected.
2. `IP-ASB-203` retains fail-close semantics for target actor scope; unrelated actor contamination no longer hard-blocks by default.
3. This is a control-plane wiring change, not instance-local patching.

### 26.36 Protocol lane explicit context hardening + wrapper tuple propagation (2026-03-16)

Problem:

1. protocol lane could still be invoked without full explicit context tuple at some wrapper paths,
   allowing auto-resolution ambiguity under actor/session multibinding.
2. quoted foreign `Identity-Context` lines inside body text could create operator-level "identity switched" confusion.
3. session-chain wrapper templates did not uniformly forward `--repo-catalog`, causing protocol-lane fail-close in
   final egress strict mode (`protocol_work_layer_requires_explicit_context_args:repo-catalog`).

Fix landed:

1. `scripts/final_emit_governed.py`
   - protocol lane enforces explicit context tuple:
     - `identity-id + catalog + repo-catalog + actor-id + session-id`
   - emits strict mode telemetry:
     - `strict_explicit_context_mode=protocol_lane_enforced`
2. `scripts/compose_and_validate_governed_reply.py`
   - adds quoted foreign headstamp guard projection:
     - `quoted_identity_context_detected`
     - `quoted_identity_context_foreign_ids`
     - `quoted_identity_context_guard_status=PASS_REQUIRED`
     - `quoted_identity_context_binding_effect=none`
3. `scripts/create_identity_pack.py`
   - ingress/egress/session-chain wrapper templates now carry repo-catalog forwarding in protocol lane path.
4. `scripts/repair_contract_backfill.py --apply`
   - materializes refreshed wrapper artifacts for runtime identities from canonical templates (no manual patching).
5. `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - adds required probe:
     - `session_chain_protocol_lane_explicit_context_pass`
6. `scripts/validate_required_gate_surface_drift.py`
   - requires new probe invocation tokens and tuple assertions.

Replay evidence (machine):

1. `bash scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh`
   - `protocol_work_layer_explicit_context_required` => `rc=1` (expected fail-close)
   - `quoted_foreign_identity_context_must_not_switch_identity` => `rc=0` (expected safe)
   - `session_chain_protocol_lane_explicit_context_pass` => `rc=0` (expected pass)
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - `required_gate_surface_drift_status=PASS_REQUIRED`
3. `python3 scripts/repair_contract_backfill.py --catalog <local_catalog> --identity-id base-repo-architect --apply --json-only`
   - `host_gateway_wrapper_artifacts_refreshed=true`
4. `python3 .identity/base-repo-architect/runtime/gate/protocol_session_chain_wrapper.py ... --work-layer protocol --json-only`
   - `protocol_session_chain_wrapper_status=PASS_REQUIRED`
   - `headstamp_first_line_status=PASS_REQUIRED`
   - `send_time_gate_status=PASS_REQUIRED`
   - `final_emit_guard_status=PASS_REQUIRED`

Checkpoint verdict update:

1. protocol strict lane now fail-closes deterministically when explicit tuple is missing.
2. foreign quoted headstamps are now machine-detected but non-binding.
3. wrapper propagation is template-driven + backfill-driven infrastructure behavior, not identity-local hardcoding.

### 26.37 Pre-95/Post-100 semantic freeze + serial-5 replay uplift (2026-03-16)

Problem:

1. field operations repeatedly conflated "pre-send guard miss" with "post-gate release decision", creating semantic drift in P0 headstamp incidents.
2. closure text mentioned 95/100 model, but machine projection lacked explicit "post-gate coverage" and "next-hop headstamp" axes.
3. operator baseline remained serial-3 and could under-sample residual bypass risk.

Fix landed:

1. semantic freeze in v1.6.6 governance:
   - pre-send is `>=95%` probabilistic prevention only.
   - post-gate is deterministic `100% detectability + 100% block + next-hop headstamp required`.
2. `scripts/full_identity_protocol_scan.py` metrics expanded:
   - `post_gate_coverage_rate`
   - `chat_egress_uniqueness_rate`
   - `next_hop_headstamp_rate`
   - corresponding threshold + status + stale reason projections.
3. `scripts/protocol_infra_contract.py` adds canonical thresholds:
   - `HOST_VISIBLE_POST_GATE_COVERAGE_REQUIRED_RATE = 1.0`
   - `HOST_VISIBLE_NEXT_HOP_HEADSTAMP_REQUIRED_RATE = 1.0`
4. operator replay baseline upgraded to serial-5 (self-test + deep-scan) in governance text.
5. `scripts/ci/run_host_visible_surface_live_probes_ci.sh` adds positive proof:
   - `send_time_governed_pass_headstamp_required` must pass (`rc=0`) before negative fail-close probes run.

Checkpoint verdict update:

1. v1.6.6 closure semantics are now frozen as machine-enforceable metrics, not documentation-only phrasing.
2. residual risk discussion must use the same metric tuple:
   - `pre_send_gate_pass_rate`
   - `post_gate_coverage_rate`
   - `chat_egress_uniqueness_rate`
   - `next_hop_block_rate`
   - `next_hop_headstamp_rate`
3. manual/headstamp text-only fixes remain explicitly out-of-contract.

### 26.38 v1.6.6 P0 closure supplement (live source + selector + continuity) (2026-03-16)

Problem:

1. strict runtime lanes could still inherit fixture semantics in some replay paths, creating source contamination risk.
2. unique-entry receipt selection was path-order-first and could become non-deterministic under multi-receipt coexistence.
3. post-check recovery accepted tuple input but lacked explicit `session_id/run_id` coherence fail-close.

Fix landed:

1. host-visible live source policy freeze in protocol contract + validators:
   - `runtime_live_receipt_sources = [runtime_dialogue]`
   - `fixture_allowed_operations = [ci]`
2. strict scan/recovery paths now seed runtime source only:
   - `recover_host_visible_post_check_state` default source remains `runtime_dialogue`
   - full-scan strict recovery path no longer writes fixture source.
3. recovery tuple continuity hardening:
   - `session_id=run:<id>` with mismatched `run_id` is fail-close (`recovery_run_id_session_mismatch`).
4. unique-entry deterministic selector hardening:
   - `entry_receipt_selector_precedence = same_tuple > same_catalog > bundle_status_pass > newest`
   - selector emits machine-readable candidate projection and selected sort rationale.

Replay (serial, machine evidence):

1. self-test serial-5 (host-visible + gateway + unique-entry probes):
   - `activity/_identity_upgrade/v166_probe_serial5_recheck_20260316T174157Z/SUMMARY.json`
   - result: `all_rounds_pass=true`
2. deep-scan serial-5 target replay:
   - `activity/_identity_upgrade/v166_target_deepscan_serial5_recheck_20260316T173349Z/SUMMARY.json`
   - result: `m2m_all_pass=true`
   - result: `chat_egress_uniqueness_status=PASS_REQUIRED` per round
   - result: `post_gate_coverage_rate_status=PASS_REQUIRED` per round
   - result: `next_hop_headstamp_rate_status=PASS_REQUIRED` per round

Checkpoint verdict update:

1. v1.6.6 now includes deterministic receipt-selection semantics and strict runtime-source freeze as protocol infrastructure behavior.
2. residual P0 items are explicitly non-m2m lanes (`IP-OUTLET-003`, `IP-WRB-002`, `IP-COV-000`, etc.), not headstamp semantic ambiguity.

### 26.39 v1.6.6 tuple/run continuity + permission/reachability attribution hardening (2026-03-16)

Problem:

1. strict scan lanes could regress when `session_id=run:<id>` and internal recovery used another run token, cascading to
   `host_visible_post_check_recovery -> host_transport_wiring_attestation -> send_time` false failures.
2. permission and localhost socket failures could be observed as unstructured subprocess errors, causing P0 misclassification.

Fix landed:

1. `scripts/full_identity_protocol_scan.py`
   - `required_gate_bundle_run_id` now derives from session-bound run token when available.
2. `scripts/validate_headstamp_recurrence_closure.py`
   - recovery precheck run id now reuses `session_id=run:<id>` binding before fallback generation.
3. `scripts/recover_host_visible_post_check_state.py`
   - write/read paths now emit explicit privilege fail-close (`IP-PRIV-ESC-001`) with machine remediation hint.
4. `scripts/validate_send_time_reply_gate.py`
   - post-check unavailable branch now preserves permission attribution:
     - `STATE_PERMISSION_DENIED`
     - `error_code=IP-PRIV-ESC-001`
5. `scripts/gateway_wrapper_enforcement.py`
   - subprocess non-JSON failures now emit structured fail payloads:
     - privilege escalation classification
     - localhost/socket reachability classification (`host_transport_reachability_unavailable:*`)
6. `scripts/ci/run_unique_entry_tuple_binding_probes_ci.sh`
   - fixture contract updated for selector policy fields required by v1.6.6 deterministic selector.

Replay evidence (machine):

1. Probe serial-5:
   - `activity/_identity_upgrade/v166_probe_serial5_recheck4_20260316T132237Z/SUMMARY.json`
   - result: `all_rounds_pass=true`
2. Target deep-scan serial-5:
   - `activity/_identity_upgrade/v166_target_deepscan_serial5_recheck3_20260316T132601Z/SUMMARY.json`
   - result: `m2m_all_pass=true`
   - result: `host_visible_post_check_recovery_ok=true` (all rounds)
   - result: `host_transport_wiring_attestation_ok=true` (all rounds)
   - result: `send_time_reply_gate_ok=true` (all rounds)
   - result: `headstamp_recurrence_closure_ok=true` (all rounds)
3. Permission + reachability attribution probes:
   - `activity/_identity_upgrade/v166_postcheck_privilege_reachability_failclose_20260316T133740Z/SUMMARY.json`
   - permission case: `error_code=IP-PRIV-ESC-001`, `state_status=STATE_PERMISSION_DENIED`
   - reachability case: stale reason contains `host_transport_reachability_unavailable`

Checkpoint verdict update:

1. v1.6.6 strict tuple continuity is restored without instance-side patching.
2. permission/reachability faults are now explicitly attributable and remain fail-close.
3. remaining P0 in target deep-scan is still non-m2m release/env lanes (`IP-OUTLET-003`, `IP-WRB-002`, `IP-COV-000`, etc.).

### 26.40 v1.6.6 host transport dependency isolation + privilege write probes (2026-03-17)

Problem:

1. localhost/socket unavailability was classified after the fact, but not governed as an explicit protocol dependency surface.
2. strict control-plane writers still lacked required negative probes for privilege-denied write paths, leaving implementation stronger than CI doctrine.
3. protocol tooling risked accidental runtime-endpoint hardcoding if reachability checks baked business host URLs into base-repo constants.

Fix landed:

1. `scripts/validate_host_transport_reachability.py`
   - introduced as first-class transport validator.
   - output now separates:
     - `transport_reachability_status`
     - `transport_failure_class`
     - `error_code=IP-HTR-001`
2. `scripts/run_host_visible_live_closure.py`
   - reachability validation now runs before recovery/attestation/send-time.
   - dependency failure short-circuits later steps to avoid downstream noise.
3. `scripts/gateway_wrapper_enforcement.py`
   - localhost/socket subprocess faults now preserve dedicated reachability family (`IP-HTR-001`) instead of collapsing into generic headstamp code.
4. `scripts/required_gate_bundle_runner.py`
   - unique-entry receipt persistence now preserves `IP-PRIV-ESC-001` on privilege-denied write failure.
5. required probe lanes added:
   - `scripts/ci/run_host_transport_reachability_probes_ci.sh`
   - `scripts/ci/run_privilege_escalation_write_probes_ci.sh`
6. anti-forget drift validator updated:
   - `scripts/validate_required_gate_surface_drift.py`
   - workflow delegate wiring now required in `.github/workflows/_identity-required-gates.yml`

Interpretation lock:

1. runtime endpoint selection is consumer/runtime contract input, not protocol hardcoded default; explicit `transport_healthcheck_url` is the allowed declaration path.
2. transport reachability failure is not semantic headstamp failure.
3. privilege write denial is not unique-entry semantic failure even when it occurs on entry receipt persistence.

### 26.41 v1.6.6 finish-line freeze + anti-forget wording lock (2026-03-17)

Problem:

1. field discussion could still drift back to "physical 100% interception" even though v1.6.6 was already frozen around pre-95/post-100 semantics.
2. "has headstamp text" and "is allowed into next hop" were still too easy to conflate in incident reviews.
3. key terms (`governed output`, `manual headstamp`, `host-direct output`, `next-hop-admissible output`) were not yet locked as required wording in anti-forget validation.

Fix landed:

1. `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
   - adds authoritative finish-line wording:
     - non-governed output one-hop death rule
     - failure evidence dual-channel
     - `post_gate_coverage_rate = 1.00`
     - `next_hop_headstamp_rate = 1.00`
2. terminology freeze added to governance:
   - `governed output`
   - `manual headstamp`
   - `host-direct output`
   - `next-hop-admissible output`
3. `scripts/validate_required_gate_surface_drift.py`
   - now treats the above v1.6.6 wording as anti-forget required tokens.
   - also blocks protocol-repo hardcoded runtime endpoint literals such as
     `HOST_TRANSPORT_REACHABILITY_DEFAULT_URL` and `http://127.0.0.1:3001/healthz`.
4. canonical next-hop admission machine tuple is now part of v1.6.6 wording:
   - `next_hop_admission_status`
   - `next_hop_admission_reason`
   - `output_governance_mode`
   - `control_lane_attestation_status`
   - `post_check_blocker_status`
5. host-visible probe suite keeps an explicit negative proof that inline/self-printed reply text is classified as `host_direct` and blocked from next hop.

Checkpoint verdict update:

1. v1.6.6 closure wording is now explicitly infrastructure-scoped and no longer compatible with "physical 100% pre-send hook" phrasing.
2. next-hop legality is now frozen as stronger than "headstamp text present".
3. anti-forget drift validation now protects both wording scope and runtime-endpoint boundary.

Interpretation lock:

1. "headstamp present" is a necessary condition only; it is never sufficient to prove next-hop admissibility.
2. non-governed output must die within one hop in controlled lanes.
3. protocol base-repo may define transport reachability validation, but may not define consumer/runtime localhost defaults.
4. assistant-visible self-printed headstamp is manual headstamp, not governed-output evidence.

### 26.42 v1.6.6 display headstamp vs canonical next-hop headstamp correction freeze (2026-03-17)

Problem:

1. human operators still require a visible identity headstamp to know who is currently speaking.
2. previous discussion risked conflating:
   - headstamp visible to humans
   - headstamp canonical for next-hop admission
3. that ambiguity creates a false binary:
   - remove visible headstamp until full closure
   - or accept any visible headstamp as if it proved governed output
4. both interpretations are invalid for v1.6.6.

Fix frozen:

1. protocol now separates two layers:
   - `display headstamp`
   - `canonical next-hop headstamp`
2. display headstamp remains mandatory for operator clarity.
3. canonical next-hop headstamp remains the only class relevant to next-hop admissibility.
4. a consistency-correction model is frozen:
   - `PASS_REQUIRED`
   - `AUTO_CORRECTED`
   - `FAIL_REQUIRED`
5. manual / pasted / host-direct headstamp text may be displayed, but may never become authority source or next-hop proof by text presence alone.

Correction freeze:

1. authoritative identity precedence is:
   - session-scoped actor binding
   - canonical session pointer
   - single active runtime identity
   - default runtime identity
2. display headstamp is compared against authoritative identity.
3. when mismatch is uniquely correctable and the visible headstamp is actually rewritten:
   - protocol rewrites visible headstamp to authoritative identity
   - records correction evidence
   - next hop continues only on corrected authoritative headstamp
4. when mismatch is not uniquely correctable, or no authoritative rewrite actually happened:
   - next hop fails closed
   - conflict/unresolved status may remain user-visible
   - blocker evidence is mandatory

Interpretation lock:

1. display headstamp preserves usability.
2. canonical next-hop headstamp preserves controlled-hop trust.
3. "headstamp present" remains necessary only, never sufficient.
4. this checkpoint does not alter the v1.6.6 pre-95/post-100 semantics, non-governed one-hop death rule, or failure evidence dual-channel rule.
5. `AUTO_CORRECTED` is reserved for a real authoritative rewrite path; mismatch is uniquely correctable only when correction evidence exists, and mismatch is not uniquely correctable for admission purposes otherwise.

Checkpoint verdict:

1. human-visible headstamp remains preserved as operator HUD.
2. v1.6.6 next-hop admissibility remains stricter than visible display.
3. mismatch between visible headstamp and authoritative identity is now governed by one correction-state model instead of ad hoc interpretation.
