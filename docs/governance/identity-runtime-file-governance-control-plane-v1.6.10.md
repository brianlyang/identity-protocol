# Identity Runtime File Governance Control Plane (v1.6.10)

Status: Draft for new PR (protocol-only, 2026-03-16)
Layer: protocol
Scope: all protocol-governed instance runtime files under `runtime/state`, `runtime/gate`, `runtime/plugins`, and `runtime/protocol-feedback`

Execution mode: v1.6.x continuity stream. This stream extends v1.6.8 and v1.6.9 and does not fork into v1.7.x.

## 0) Version discipline and stream boundary (mandatory)

1. Stream version is fixed at `v1.6.10`.
2. This stream inherits and must not weaken:
   - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
   - `docs/governance/identity-headstamp-last-hop-closure-governance-v1.6.9.md`
3. Any proposal that bypasses v1.6.x motherline mapping is out-of-scope.
4. This stream is protocol infrastructure only, not instance-specific patching.
5. Current-pointer continuity refs (mandatory):
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 1) Problem statement (frozen)

Current protocol checks are strong at gateway/receipt validation, but runtime-file governance is still fragmented:

1. Not all runtime file writes are bound to a single governed writer API.
2. Some validators judge final state only; they do not enforce write provenance per mutation.
3. "runtime == contract" can pass while write-path discipline is incomplete for non-wrapper runtime artifacts.
4. Review and CI currently rely on multiple scripts with partial overlap, raising drift risk.

## 2) Design objective (non-conflicting positive strengthening)

The objective is to move from "validator-centered" to "file-lifecycle-centered" governance without breaking existing v1.6.x controls.

1. Keep existing unique-entry/headstamp controls as-is.
2. Add a unified runtime file governance contract and validators.
3. Add mandatory mutation receipts and post-check blocker wiring.
4. Enforce strict fail-close on missing/invalid governance state.

## 3) New control plane contract (v1.6.10)

### 3.1 Contract ID

`protocol_runtime_file_governance_contract_v1`

### 3.2 Mandatory fields

1. `required: true`
2. `contract_id: protocol_runtime_file_governance_contract_v1`
3. `validator: scripts/validate_runtime_file_governance.py`
4. `write_guard_validator: scripts/validate_runtime_file_write_guard.py`
5. `registry`:
   - canonical file IDs and relative paths
   - allowed writers per file ID
   - required receipt class per file ID
6. `mutation_receipt_policy`:
   - required tuple: `identity_id`, `actor_id`, `session_id`, `run_id`, `operation`
   - required integrity fields: `before_sha256`, `after_sha256`, `writer_id`, `timestamp_utc`
7. `post_check_policy`:
   - `closure_state_file`
   - `block_on_missing_or_invalid: true`
   - `block_on_blocker_active: true`

### 3.3 Registry baseline (v1.6.10 initial set)

1. `runtime_state`
2. `runtime_gate`
3. `runtime_plugins`
4. `runtime_protocol_feedback`

### 3.4 Chat egress uniqueness contract (v1.6.10 required)

`chat_egress_uniqueness_contract_v1`

This stream formalizes the governance boundary as:
`95% pre-send pass + 100% post-check detectability + 100% next-hop block + 100% egress-uniqueness detectability`.

Required machine fields (from send-time payload, strict lanes):

1. `chat_egress_uniqueness_contract_id`
2. `chat_egress_uniqueness_status`
3. `chat_egress_uniqueness_reason`
4. `chat_egress_uniqueness_error_code`
5. `chat_egress_uniqueness_observed_send_time_status`

Fail-close mapping (strict):

1. post-check blocker active => `chat_egress_uniqueness_status=FAIL_REQUIRED`, `chat_egress_uniqueness_error_code=IP-HDSTAMP-003`, `chat_egress_uniqueness_reason=post_check_blocker_active_next_hop_blocked`
2. post-check state missing/invalid/unreadable => `chat_egress_uniqueness_status=FAIL_REQUIRED`, `chat_egress_uniqueness_error_code=IP-HDSTAMP-003`, `chat_egress_uniqueness_reason=post_check_state_unavailable_fail_close`
3. no silent downgrade to `SKIPPED_NOT_REQUIRED` for strict required probes

## 4) Validator and CI closure model

### 4.1 New validators (required)

1. `scripts/validate_runtime_file_governance.py`
   - schema strictness
   - registry completeness
   - contract/runtime parity
2. `scripts/validate_runtime_file_write_guard.py`
   - write provenance receipt validation
   - unauthorized writer detection
3. `scripts/validate_runtime_file_governance_post_check.py`
   - closure state enforcement
   - next-hop blocker mapping

### 4.2 Required negative probes

1. unregistered runtime file mutation => `FAIL_REQUIRED`
2. registered file mutated by unauthorized writer => `FAIL_REQUIRED`
3. mutation without governance receipt => `FAIL_REQUIRED`
4. forged/mismatched `before_sha256`/`after_sha256` => `FAIL_REQUIRED`
5. post-check state missing/invalid => next-hop hard block
6. send-time `post_check_blocker_active` branch must emit `chat_egress_uniqueness_error_code=IP-HDSTAMP-003` + blocker reason
7. send-time `post_check_state_unavailable` branch must emit `chat_egress_uniqueness_error_code=IP-HDSTAMP-003` + missing-state reason

### 4.3 Required positive probes

1. registered file mutation by allowed writer with valid receipt => `PASS_REQUIRED`
2. runtime/governance parity for all registry entries => `PASS_REQUIRED`
3. strict update path with governance post-check clean => `PASS_REQUIRED`
4. full-scan strict projection includes `chat_egress_uniqueness_status` and enforces required threshold

## 5) Conflict-avoidance matrix (must remain true)

1. No weakening of `validate_protocol_unique_entry_gate` strict tuple requirements.
2. No weakening of host-visible post-check blocker behavior in send-time gate.
3. No compatibility branch for legacy ad-hoc runtime paths.
4. No hardcoded per-identity exceptions.
5. No silent downgrade from `FAIL_REQUIRED` to `SKIPPED_NOT_REQUIRED` in strict operations.

### 5.1 Wrapper mirror discipline (mandatory)

1. `runtime/gate/protocol_ingress_wrapper.py`, `runtime/gate/protocol_egress_wrapper.py`, and `runtime/gate/protocol_session_chain_wrapper.py` are governed mirrors, not source of truth.
2. Canonical control-plane source remains protocol repo scripts and contracts:
   - `scripts/final_emit_governed.py`
   - `scripts/validate_send_time_reply_gate.py`
   - `scripts/protocol_infra_contract.py`
3. Wrapper refresh is allowed and expected via protocol backfill/upgrade flows, but wrappers must never redefine channel governance semantics independently.
4. Any `runtime wrapper == local contract` but `runtime wrapper != canonical template` condition is governance drift and must fail-close in strict lane.

## 6) Cross-verification synthesis (roundtable/vendor/reference/search/context7/openaidoc)

### 6.1 Roundtable / internal

1. v1.6.8 path immutability requires registry-first governance and fail-close probes.
2. v1.6.9 last-hop closure requires post-check detectability and next-hop block.

### 6.2 Vendor / policy-as-code

1. OPA model supports policy testability and decision logging for replayable governance.
2. Sigstore model supports artifact signing, verification, and transparency-backed provenance.

### 6.3 Reference / standards

1. SLSA v1.0 defines progressive supply-chain integrity and provenance requirements.
2. W3C Trace Context defines cross-hop trace continuity primitives (`traceparent`, `tracestate`).
3. OpenTelemetry defines log/trace correlation and exemplar linkage for observability integrity.

### 6.4 Search / external practice guidance

1. OpenAI eval guidance emphasizes pass/fail graders, CI integration, and production-failure feedback loops.
2. OpenAI agent tracing guidance emphasizes workflow visibility and auditability during development and production.

### 6.5 Context7 / OpenAI doc tracks

1. Context7 lane captured OPA, OpenTelemetry, Sigstore references as implementation-aligned source evidence.
2. OpenAIDoc lane captured Evals and tracing guidance for CI and observability strategy alignment.

## 7) Implementation phases (single PR plan)

1. Phase A: contract + registry + skeleton validators
2. Phase B: write-guard + mutation receipt persistence + strict post-check
3. Phase C: required CI negative/positive probes + full scan aggregation wiring

Each phase must be merge-safe and independently fail-close.

## 8) Metrics and acceptance gates

1. `RUNTIME_FILE_REGISTRY_COVERAGE_REQUIRED_RATE = 1.0`
2. `RUNTIME_FILE_MUTATION_RECEIPT_REQUIRED_RATE = 1.0`
3. `RUNTIME_FILE_UNAUTHORIZED_WRITER_BLOCK_RATE = 1.0`
4. `RUNTIME_FILE_POST_CHECK_BLOCK_ON_INVALID_RATE = 1.0`
5. `RUNTIME_FILE_FALSE_GREEN_MAX_RATE = 0.0`
6. `HOST_VISIBLE_CHAT_EGRESS_UNIQUENESS_REQUIRED_RATE = 1.0`

Serial acceptance baseline:

1. 3 serial self-test rounds
2. 3 serial deep-scan rounds
3. required CI probe matrix all pass with expected red/green behavior

## 9) Evidence and report contract

1. Evidence root:
   - PR-tracked manifest: `docs/review/evidence/v1.6.10/`
   - runtime run artifacts: `activity/evidence/v1610-runtime-file-governance/<date>/`
2. Required artifacts:
   - governance parity snapshot
   - mutation receipt matrix
   - negative probe report
   - positive probe report
   - unified manifest

## 10) References

1. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
2. `docs/governance/identity-headstamp-last-hop-closure-governance-v1.6.9.md`
3. https://slsa.dev/spec/v1.0/
4. https://w3c.github.io/trace-context/
5. https://github.com/open-policy-agent/opa/tree/main/docs
6. https://github.com/sigstore/docs
7. https://developers.openai.com/api/docs/guides/evals/
8. https://developers.openai.com/api/docs/guides/evaluation-best-practices/
9. https://developers.openai.com/cookbook/examples/realtime_eval_guide/
10. https://developers.openai.com/cookbook/examples/agents_sdk/app_assistant_voice_agents/

## 11) One-to-one anti-forget correspondence matrix (mandatory)

This stream remains draft/continuity, but anti-forget closure is machine-enforced:

1. runtime-file governance correspondence must stay wired through:
   - `scripts/validate_required_gate_surface_drift.py`
2. strict coverage visibility must stay wired through:
   - `scripts/validate_required_contract_coverage.py`
3. runtime-file mutation/path immutability probes must stay wired through:
   - `scripts/ci/run_downsink_path_immutability_probes_ci.sh`
4. skill artifact supply-chain probes (absorbed motherline controls) must stay wired through:
   - `scripts/ci/run_skill_supply_chain_probes_ci.sh`
5. if any mapping row or doc clause is added without the above strict surfaces, it is a fail-close anti-forget breach.

## 12) Fixed runtime/protocol-feedback downsink scope (mandatory)

`runtime/protocol-feedback` is part of control-plane downsink and must be governed by fixed paths + fixed filename patterns, not free-form writes.

Fixed subdirectories:

1. `runtime/protocol-feedback/outbox-to-protocol/`
2. `runtime/protocol-feedback/inbox-from-protocol/`
3. `runtime/protocol-feedback/evidence-index/`
4. `runtime/protocol-feedback/upgrade-proposals/`
5. `runtime/protocol-feedback/atomic/`
6. `runtime/protocol-feedback/roundtables/`
7. `runtime/protocol-feedback/protocol-vendor-intel/`
8. `runtime/protocol-feedback/business-partner-intel/`
9. `runtime/protocol-feedback/vendor-intel/`
10. `runtime/protocol-feedback/issues/`
11. `runtime/protocol-feedback/review-notes/`
12. `runtime/protocol-feedback/validation/`

Fixed filename pattern families (representative required set):

1. `outbox-to-protocol/FEEDBACK_BATCH_*.md`
2. `outbox-to-protocol/*_RECEIPT_*.json`
3. `outbox-to-protocol/*_SEED_*.md`
4. `outbox-to-protocol/*_PACK_*.md`
5. `outbox-to-protocol/REQUIREMENTS_*.md`
6. `outbox-to-protocol/*_PENDING_*.json`
7. `outbox-to-protocol/BROADCAST_*.json`
8. `outbox-to-protocol/INQUIRY_REQUIREDIZATION_TRIGGER_*.json`
9. `outbox-to-protocol/SANITIZATION_PARAPHRASE_*.json`
10. `outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_*.json`
11. `outbox-to-protocol/SESSION_LANE_LOCK_EXIT_*.json`
12. `inbox-from-protocol/PROTOCOL_INBOX_*.md`
13. `inbox-from-protocol/PROTOCOL_INBOX_RECEIPT_*.json`
14. `evidence-index/INDEX.md`
15. `upgrade-proposals/*.md`
16. `atomic/*.receipt.json`, `atomic/*.batch.json`, `atomic/*.index.json`
17. `roundtables/ROUNDTABLE_*.md`
18. `protocol-vendor-intel/PROTOCOL_VENDOR_*.md`
19. `business-partner-intel/BUSINESS_PARTNER_*.md`
20. `vendor-intel/VENDOR_*.md`
21. `issues/ISSUE_*.md`
22. `review-notes/*.log`
23. `validation/*.json`

Fail-close rule:

1. any file under `runtime/protocol-feedback/**` that does not match registry patterns is `FAIL_REQUIRED`.
2. canonical directory + noncanonical filename is also `FAIL_REQUIRED`.
