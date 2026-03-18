# Protocol Remediation Audit Ledger (v1.6.11 agent relay final answer stream)

Status: Active (protocol asset landed + local replay verified, 2026-03-18)  
Scope: protocol-only review ledger for outer-agent exact/summary relay governance

## 0) Stream objective

1. Turn outer-agent final delivery from "discipline only" into a machine-verifiable relay contract.
2. Keep identity instance output and operator summary permanently distinguishable.
3. Close the bypass where an outer agent can skip the governed instance relay and still look authoritative.

## 1) Problem statement frozen for audit

1. Identity instances can already emit governed final answers through snapshot/final-report artifacts.
2. The remaining gap is the last outer-delivery hop from agent to user.
3. Without a relay receipt, outer delivery can bypass the governed instance outlet and collapse exact relay vs summary into one ambiguous surface.

## 2) Files landed in this stream

### 2.1 New protocol assets

1. `identity/protocol/plugins/templates/agent-relay-final-answer.contract_v1.json`
2. `scripts/agent_relay_final_answer_common.py`
3. `scripts/build_agent_relay_final_answer.py`
4. `scripts/validate_agent_relay_final_answer.py`
5. `scripts/ci/run_agent_relay_final_answer_builder_probes_ci.sh`
6. `scripts/ci/run_agent_relay_final_answer_probes_ci.sh`

### 2.2 Motherline and registry updates

1. `identity/protocol/IDENTITY_RUNTIME.md`
2. `identity/protocol/mappings/contract-binding.v1.6.yaml`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`

### 2.3 Stream docs

1. `docs/governance/agent-relay-final-answer-governance-v1.6.11.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.11-agent-relay-final-answer.md`

## 3) Frozen implementation checklist (item-by-item)

### 3.1 Contract layer

1. Introduce canonical outer-delivery surface `agent_relay_final_answer`.
2. Freeze `relay_mode=exact|summary`.
3. Freeze delivery authority split:
   - `identity_instance_output`
   - `ungoverned_operator_summary`
4. Freeze shared protocol builder ownership for receipt construction.

### 3.2 Validator layer

1. Require governed source artifact resolution before validating relay.
2. Enforce exact-mode byte match.
3. Enforce summary-mode impersonation guard.
4. Enforce source identity and source timestamp parity.

### 3.2 Builder layer

1. Shared builder resolves governed source artifact kinds.
2. Shared builder materializes exact relay text from source artifact instead of caller-authored text.
3. Shared builder rejects summary impersonation before sender handoff.
4. Shared builder emits canonical receipt structure for all instances.

### 3.3 Mapping layer

1. Promote relay governance into motherline row `ASB16-RQ-042`.
2. Register v1.6.11 stream docs in the canonical registry.
3. Register strict-doc evidence allowlist patterns.

### 3.4 CI layer

1. Add dedicated builder probe runner.
2. Add dedicated validator probe runner.
3. Lock both positive and negative probe cases into machine-verifiable outputs.

## 4) Probe matrix (required)

### 4.1 Positive probes

1. builder exact relay pass
2. builder summary relay pass
3. validator exact relay pass
4. validator summary relay pass

### 4.2 Negative probes

1. builder summary impersonates governed output -> `IP-RELAY-004`
2. builder exact relay diverges from source artifact -> `IP-RELAY-003`
3. validator summary impersonates governed output -> `IP-RELAY-004`
4. validator exact relay diverges from source artifact -> `IP-RELAY-003`

## 5) Audit verdict rules (frozen)

1. **Policy PASS** requires:
   - governance doc registered in stream-doc registry
   - review doc registered in stream-doc registry
   - allowlist entries present for both docs
2. **Implementation PASS** requires:
   - shared builder exists and is the canonical receipt constructor
   - validator parses receipts and source artifacts correctly
   - builder + validator positive/negative probes all behave as expected
   - motherline row `ASB16-RQ-042` is present
3. Any missing tuple field, relay/source mismatch, or summary impersonation remains `FAIL_REQUIRED`.

## 6) Evidence contract for this stream

Evidence root pattern (strict docs):

1. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/EVIDENCE_MANIFEST.*.json`
2. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/*_summary.json`
3. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/relay_receipt_snapshot.*.json`
4. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/relay_probe_matrix.*.json`

## 7) Local verification performed for this landing

1. `python3 -m py_compile scripts/validate_agent_relay_final_answer.py`
2. `python3 -m py_compile scripts/agent_relay_final_answer_common.py`
3. `python3 -m py_compile scripts/build_agent_relay_final_answer.py`
4. `bash scripts/ci/run_agent_relay_final_answer_builder_probes_ci.sh`
5. `bash scripts/ci/run_agent_relay_final_answer_probes_ci.sh`

## 8) Boundary lock for reviewers

1. This stream does not reopen native-chat renderer semantics.
2. This stream does not downgrade target behavior to old canonical-first-line-only output.
3. This stream exists specifically to govern outer relay, not to relitigate existing wrapper/display contracts.
