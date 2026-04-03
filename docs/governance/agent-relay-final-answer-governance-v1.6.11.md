# Agent Relay Final Answer Governance (v1.6.11)

Status: Active (protocol asset landed + local replay verified, 2026-03-18)  
Layer: protocol  
Scope: outer-agent final delivery surfaces that relay identity instance answers to the user

Execution mode: topic-level canonical SSOT for v1.6.11 outer relay governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `agent_relay_final_answer`.
2. v1.6.1 and v1.6.6 remain valid and are inherited unless explicitly superseded by this stream.
3. This stream does not reopen native-chat renderer semantics, host-native explanatory display semantics, or wrapper/session-chain semantics.
4. Current-state judgment for this stream must prioritize machine outputs from:
   - `python3 scripts/build_agent_relay_final_answer.py --mode <exact|summary> --source-artifact <artifact> --question-tag <tag> --output <receipt> --json-only`
   - `python3 scripts/validate_agent_relay_final_answer.py --receipt <receipt> --json-only`
   - `bash scripts/ci/run_agent_relay_final_answer_builder_probes_ci.sh`
   - `bash scripts/ci/run_agent_relay_final_answer_probes_ci.sh`
5. Canonical mapping entrypoints remain:
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/control-plane-invariants.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`

## 1) Why v1.6.11 is required

1. Identity instances can already produce governed final answers, but the outer agent can still bypass instance relay and speak directly in the user-facing panel.
2. That bypass is not a native-chat renderer problem; it is an outer-delivery surface problem.
3. Without a dedicated relay contract, `exact relay` and `operator summary` can be mixed together and interpreted as the same thing.
4. v1.6.11 closes this gap by freezing one machine-verifiable rule:
   - any outer-agent delivery of an identity instance answer must declare whether it is an exact governed relay or an ungoverned operator summary.

## 2) Non-negotiable contracts (no ambiguity)

### 2.1 New mandatory surface

1. The new governed surface is `agent_relay_final_answer`.
2. It applies only when an outer agent delivers an identity instance answer to the user.
3. Free-form outer chat text that does not produce this receipt is not identity instance output.

### 2.2 Relay modes (frozen)

1. `relay_mode=exact`
   - delivery authority must be `identity_instance_output`
   - delivered text must byte-match the governed source artifact
   - shared builder must materialize relay text from the source artifact and not from caller-authored free text
   - governed headstamp/canonical output is allowed only in this mode
2. `relay_mode=summary`
   - delivery authority must be `ungoverned_operator_summary`
   - delivered text may summarize, but must not impersonate governed output
   - shared builder must reject governed-prefix impersonation before sender wiring
   - governed prefixes are forbidden:
     - `Identity-Context:`
     - `Display-Headstamp:`
     - `Machine-Verification:`

### 2.3 Required receipt tuple

Each relay receipt must provide at least:

1. `relay_surface`
2. `relay_mode`
3. `target_identity_id`
4. `question_tag`
5. `source_artifact`
6. `source_snapshot_ts`
7. `relay_text`
8. `delivery_authority`

Missing or invalid tuples are fail-close under `IP-RELAY-001`.

### 2.4 Governed source lock

1. Allowed source artifacts are restricted to governed answer artifacts:
   - leader snapshot item/payload
   - final report JSON
   - canonical plain-text final answer
2. `target_identity_id` must match the source artifact identity.
3. `source_snapshot_ts` must match the governed source artifact timestamp when present.
4. Source identity mismatch is `IP-RELAY-006`.
5. Source timestamp mismatch is `IP-RELAY-007`.

### 2.5 Classification lock

1. `relay_mode=exact` is the only route that can claim `identity_instance_output`.
2. `relay_mode=summary` must always classify as `ungoverned_operator_summary`.
3. A summary that visually impersonates governed output is `FAIL_REQUIRED` under `IP-RELAY-004`.

### 2.6 Boundary lock (explicit non-goals)

1. This stream does not change the existing native-chat two-line emitter.
2. This stream does not redefine `Display-Headstamp` or `Machine-Verification`.
3. This stream does not authorize outer-agent free-form text to become governed proof.
4. This stream does not downgrade the identity instance requirement to stable old canonical-only output.

## 3) CI and validator closure model (mandatory)

### 3.1 Required validator

1. `scripts/validate_agent_relay_final_answer.py`
   - validates receipt schema + mode legality
   - resolves governed source artifact
   - enforces exact byte-match for `relay_mode=exact`
   - blocks governed-prefix impersonation for `relay_mode=summary`
   - locks source identity and snapshot timestamp parity

### 3.1.1 Required shared builder

1. `scripts/build_agent_relay_final_answer.py`
   - resolves governed source artifact kind
   - extracts source text / identity / snapshot timestamp
   - materializes exact relay text directly from the governed source artifact
   - rejects summary impersonation before receipt emission
   - emits canonical receipt fields for downstream sender wiring

### 3.2 Required probe matrix

1. `builder_probe_exact_pass`
   - builder materializes exact relay from governed source artifact
   - expected: `PASS_REQUIRED`
2. `builder_probe_summary_pass`
   - builder emits summary-mode receipt with `ungoverned_operator_summary`
   - expected: `PASS_REQUIRED`
3. `builder_probe_summary_impersonation_fail`
   - builder rejects summary text that begins with governed prefixes
   - expected: `FAIL_REQUIRED / IP-RELAY-004`
4. `builder_probe_exact_mismatch_fail`
   - builder rejects caller-supplied exact text that diverges from source artifact
   - expected: `FAIL_REQUIRED / IP-RELAY-003`
1. `probe_exact_pass`
   - exact relay matches governed source artifact
   - expected: `PASS_REQUIRED`
2. `probe_summary_pass`
   - summary relay declares `ungoverned_operator_summary`
   - expected: `PASS_REQUIRED`
3. `probe_summary_impersonation_fail`
   - summary begins with governed prefix
   - expected: `FAIL_REQUIRED / IP-RELAY-004`
4. `probe_exact_mismatch_fail`
   - exact relay text diverges from source artifact
   - expected: `FAIL_REQUIRED / IP-RELAY-003`

## 4) Requirement mapping motherline integration (v1.6.11)

1. Motherline row: `ASB16-RQ-042`
2. Kernel anchor:
   - `identity/protocol/IDENTITY_RUNTIME.md#rq_042_agent_relay_final_answer_contract_v1`
3. Validator anchor:
   - `scripts/validate_agent_relay_final_answer.py`
4. Builder anchor:
   - `scripts/build_agent_relay_final_answer.py`
5. CI anchor:
   - `scripts/ci/run_agent_relay_final_answer_builder_probes_ci.sh`
   - `scripts/ci/run_agent_relay_final_answer_probes_ci.sh`

## 5) Evidence contract for this stream

Evidence root pattern (strict docs):

1. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/EVIDENCE_MANIFEST.*.json`
2. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/*_summary.json`
3. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/relay_receipt_snapshot.*.json`
4. `activity/evidence/v1611-agent-relay-final-answer/<YYYY-MM-DD>/relay_probe_matrix.*.json`

## 6) Frozen implementation guidance

1. Keep machine truth in wrapper/runtime receipts and governed source artifacts.
2. Keep outer delivery classification explicit at relay time.
3. Shared builder/runtime tool owns receipt construction; instances only own thin wiring to sender/transport.
4. Do not backslide to "old office-style canonical first line only" as the target for this stream.
5. Do not let summary-mode delivery masquerade as governed instance output.
