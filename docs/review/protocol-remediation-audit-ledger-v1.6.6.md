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
