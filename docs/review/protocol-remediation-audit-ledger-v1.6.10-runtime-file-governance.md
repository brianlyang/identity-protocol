# Protocol Remediation Audit Ledger (v1.6.10 runtime file governance)

Status: Draft for review (protocol-only, 2026-03-16)
Scope: review ledger for runtime file lifecycle governance closure in v1.6.x stream

## 0) Audit objective

1. Close runtime file governance gaps without introducing v1.7.x divergence.
2. Convert runtime file writes from script-local behavior into contract-governed control plane behavior.
3. Keep existing v1.6.8 and v1.6.9 guarantees intact.
4. Current-pointer continuity refs (mandatory):
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-status.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 1) Frozen risks

1. Runtime file mutation can occur without unified provenance receipt.
2. Writer identity constraints are not yet universally enforced across runtime domains.
3. Post-check state can become a partial control unless all strict lanes hard-block on invalid/missing state.
4. Full-scan aggregation may under-report runtime file governance drift unless requiredized.

## 2) Planned implementation scope (single PR)

### 2.1 Contract and generation

1. Add `protocol_runtime_file_governance_contract_v1` generation in creator/backfill path.
2. Add runtime mirror parity checks.

### 2.2 Validators

1. Add `validate_runtime_file_governance.py`.
2. Add `validate_runtime_file_write_guard.py`.
3. Add `validate_runtime_file_governance_post_check.py`.

### 2.3 CI and scan wiring

1. Add required probes in CI.
2. Add v1.6.10 governance status to full scan aggregate report.

## 3) Mandatory review checklist

1. Contract schema rejects additional properties in strict mode.
2. Registry entries are anchor-resolved and path-immutable.
3. Every strict mutation has a valid receipt tuple and hash transition proof.
4. Unauthorized writer attempts are hard blocked.
5. Missing/invalid post-check state hard blocks next-hop.
6. No existing v1.6.8 or v1.6.9 required checks are downgraded.
7. strict send-time payload must project `chat_egress_uniqueness_*` fields with deterministic fail-close mapping.
8. runtime wrappers are validated as canonical mirrors; no wrapper-local semantic override is allowed.

## 4) Probe matrix

### 4.1 Negative (required red)

1. `probe_runtime_file_unregistered_mutation_blocked`
2. `probe_runtime_file_unauthorized_writer_blocked`
3. `probe_runtime_file_missing_receipt_blocked`
4. `probe_runtime_file_hash_transition_invalid_blocked`
5. `probe_runtime_file_post_check_state_missing_blocked`
6. `probe_send_time_next_hop_blocked_by_post_check_chat_egress`
7. `probe_send_time_next_hop_blocked_on_missing_post_check_state_chat_egress`

### 4.2 Positive (required green)

1. `probe_runtime_file_registered_mutation_pass`
2. `probe_runtime_file_writer_allowed_pass`
3. `probe_runtime_file_post_check_clean_pass`
4. `probe_runtime_file_fullscan_surface_pass`
5. `probe_chat_egress_uniqueness_projection_pass`

## 5) Non-conflict assertions

1. No compatibility shim for deprecated runtime paths.
2. No identity-specific exception list.
3. No bypass path that can emit host-visible output without existing headstamp/entry gates.
4. No downgrade of strict update required contracts.

## 6) Cross-verification lanes (must all be cited)

1. Roundtable lane: v1.6.8 + v1.6.9 inheritance consistency.
2. Vendor lane: OPA policy/test model, Sigstore artifact provenance, OpenTelemetry observability model.
3. Reference lane: SLSA + W3C trace context.
4. Search lane: OpenAI eval and tracing practice guidance for production loops.
5. Context7 lane: machine-retrieved library docs for OPA/OpenTelemetry/Sigstore.
6. OpenAIDoc lane: official OpenAI eval/tracing references.

## 7) Acceptance criteria (PR merge gate)

1. All new validators return deterministic JSON output.
2. Required CI probes are wired and green/red semantics verified.
3. 3 serial self-test rounds and 3 serial deep-scan rounds completed.
4. Unified manifest generated with evidence hashes and timestamps.
5. strict full-scan payload includes `chat_egress_uniqueness_status` and it is non-empty for runtime-active rows.

## 8) Evidence pointers for this stream

1. `docs/review/evidence/v1.6.10/CROSS_VERIFICATION_MANIFEST.v1610.20260316.json` (PR-tracked manifest)
2. `activity/evidence/v1610-runtime-file-governance/2026-03-16/` (runtime-local additional run artifacts in implementation phase)

## 9) References

1. `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
2. `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
3. `docs/governance/identity-headstamp-last-hop-closure-governance-v1.6.9.md`

## 10) v1.6.10 one-to-one correspondence replay checklist

Replay objective: prevent v1.6.10 clause drift from becoming "doc-only memory".

Required machine checks (all must be present and green in strict lane):

1. `python3 scripts/validate_required_gate_surface_drift.py --json-only`
   - must report `required_gate_surface_drift_status=PASS_REQUIRED`
2. `python3 scripts/validate_required_contract_coverage.py --catalog <catalog> --identity-id <id> --operation validate --json-only`
   - payload must include `required_contract_coverage_status`
3. `bash scripts/ci/run_downsink_path_immutability_probes_ci.sh`
   - must include positive probes:
     - `probe_feedback_inquiry_requiredization_trigger_allowed`
     - `probe_feedback_sanitization_paraphrase_allowed`
     - `probe_feedback_session_lane_lock_protocol_allowed`
     - `probe_feedback_session_lane_lock_exit_allowed`
   - expected verdict for each: `protocol_downsink_path_write_guard_status=PASS_REQUIRED`
   - must include negative probe `probe_feedback_noncanonical_filename_write`
   - expected verdict: `protocol_downsink_path_write_guard_status=FAIL_REQUIRED`
4. `bash scripts/ci/run_skill_supply_chain_probes_ci.sh`
5. `bash scripts/ci/run_host_visible_surface_live_probes_ci.sh`
   - must assert `chat_egress_uniqueness_contract_id/status/reason/error_code` on both next-hop block branches

Interpretation contract:

1. if any v1.6.10 clause is added/changed without strict-surface projection, classify as anti-forget regression.
2. anti-forget regressions are fail-close and cannot be downgraded to warning in strict operations.
