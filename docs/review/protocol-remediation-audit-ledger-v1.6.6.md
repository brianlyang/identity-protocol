# Protocol Remediation Audit Ledger (v1.6.6 host-channel stream)

Status: Active

Layer: protocol control-plane review ledger (non-governance SSOT)

Scope: implementation review ledger for host-session unique ingress/egress closure and per-instance wrapper enforcement.

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

## 0) Baseline posture at stream opening (2026-03-12)

Machine baseline retained from active control-plane checks:

1. `python3 scripts/validate_control_plane_invariants.py --json-only`
2. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
3. `python3 scripts/validate_control_plane_status_sync.py --json-only`
4. `python3 scripts/docs_command_contract_check.py`

Semantic baseline confirmed at opening:

1. Protocol strict-surface ingress/egress contracts exist and are machine-checkable.
2. Unique-entry contract is declared in instance `CURRENT_TASK.json` and validator chain exists.
3. Residual risk remains at host session entrypoints if dispatch bypasses wrapper contract.

Opening verdict: `Policy PASS / Implementation CONDITIONAL PASS`.

## 1) Review focus for v1.6.6

1. Freeze one host-channel contract with no ambiguous alternates.
2. Ensure per-instance wrapper generation is mandatory, deterministic, and replayable.
3. Ensure host dispatch/release paths are wrapper-only in strict operations.
4. Preserve protocol-instance layer split while closing runtime bypasses.
5. Ensure host non-mutation conversation rounds are also wrapper-enforced.

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

### 3.2 Host side

1. Inbound dispatch goes through ingress wrapper before execution handoff.
2. User-visible outbound release goes through egress wrapper before send.
3. Egress release verifies ingress receipt parity for current turn:
   - same `run_id`
   - same `session_id`
   - same `actor_id`
4. Direct dispatch/release paths without wrapper/receipt are blocked with fail-close status.
5. Host non-mutation rounds still require wrapper traversal and egress headstamp/send-time pass.

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

### 3.5 YAML sprawl control check

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
5. Host replay confirms wrapper-only dispatch and wrapper-only release for strict operations.
6. Stream PR binding receipt exists and matches stream version + head SHA.
7. Host replay confirms wrapper-only dispatch and wrapper-only release for non-mutation conversation rounds.
8. Negative probe (`direct dispatch -> direct release`) is `FAIL_REQUIRED`.

## 5) Residual risk register (initial)

1. **P1**: host runtime may still include legacy direct dispatch callsites.
   - mitigation: explicit host-side fail-close branch + negative probe in CI/replay.
2. **P1**: wrapper files may exist but not be consumed by host routing.
   - mitigation: routing assertions and dispatch receipts at host entrypoints.
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
2. Review closure still depends on host runtime entrypoint wiring completion and replay evidence.

## 7) External references

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
