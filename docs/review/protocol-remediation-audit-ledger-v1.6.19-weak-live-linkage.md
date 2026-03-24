# Protocol Remediation Audit Ledger (v1.6.19 Weak Live Linkage)

Status: Active (`ISSUE-037` opened on 2026-03-24; the stream opened from trio live-link review and now captures the broader weak-live-linkage consumer-gap family confirmed by deep-sweep rechecks)
Layer: protocol
Scope: audit evidence for the additive stream that strengthens current-run binding and next-hop consumption across trio, prompt, sample, and loop-consumer surfaces without reopening `v1.6.17` or `v1.6.18`
Execution mode: canonical review ledger for the v1.6.19 weak-live-linkage stream.

## 0) Current control-plane alias refs

- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`

## 1) Audit conclusion

This stream is worth absorbing, and its scope should now be documented more precisely.

The deep-sweep conclusion is no longer only “the tool/vendor trio is history-tolerant.” It is:

1. the protocol already has strong structural owner lanes;
2. several validators still permit `weak_live_linkage` interpretations;
3. those false-green patterns cluster into prompt presence-only, sample-report-only, loop meta-only, and latest-log-no-run-binding risk;
4. therefore the correct response is an additive shared-infrastructure strengthening stream plus a frozen differential-audit method, not:
   - reopening earlier semantics,
   - creating a new artifact family,
   - deleting sample/self-test families,
   - or writing pack-local workarounds.

## 2) Current repo achievements rechecked one by one

### 2.1 Trio structure remains genuinely landed

Direct replays on `custom-creative-ecom-analyst` still show:

1. `python3 identity-protocol-local/scripts/validate_identity_tool_installation.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/tool-installation-custom-creative-ecom-analyst-20260227T040733Z.json`
2. `python3 identity-protocol-local/scripts/validate_identity_vendor_api_discovery.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/vendor-api-discovery-custom-creative-ecom-analyst-20260227T040733Z.json`
3. `python3 identity-protocol-local/scripts/validate_identity_vendor_api_solution.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/vendor-api-solution-custom-creative-ecom-analyst-20260227T040733Z.json`

Interpretation:

- trio contract structure is landed;
- strict current-run binding is still not proven by those passes alone.

### 2.2 Discovery requiredization remains a real achievement, but it is structural

Direct replay:

- `python3 identity-protocol-local/scripts/validate_discovery_requiredization.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `discovery_requiredization_status=PASS_REQUIRED`
2. `requiredized_all_discovery_contracts=true`
3. `discovery_required_total=3`
4. `discovery_required_passed=3`

Interpretation:

- requiredization is genuinely landed;
- it still proves required structure more strongly than live current-run consumption.

### 2.3 Prompt validators currently prove presence/coverage, not live driver absorption

Direct replays:

1. `python3 identity-protocol-local/scripts/validate_prompt_bootstrap_capability.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`
2. `python3 identity-protocol-local/scripts/validate_prompt_capability_matrix.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`
3. `python3 identity-protocol-local/scripts/validate_prompt_derivation_conformance.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. all three return `PASS_REQUIRED`;
2. `validate_prompt_bootstrap_capability.py` sets `requiredization_current_round_linked=true` directly from `prompt_path.exists()`;
3. `validate_prompt_capability_matrix.py` sets `requiredization_current_round_linked=true` from `prompt_path.exists()` or configured validator presence, and can keep `prompt_capability_matrix_status=PASS_REQUIRED` while `discovery_requiredized_all=false`;
4. `validate_prompt_derivation_conformance.py` also derives `requiredization_current_round_linked=true` from prompt existence.

Interpretation:

- current prompt green is real as a declaration/coverage green;
- it is not yet a live-driver-consumption green.

### 2.4 Sample validators currently prove sample/self-test closure, not strict live closure

Direct replays:

1. `python3 identity-protocol-local/scripts/validate_identity_capability_arbitration.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `Capability arbitration contract validation PASSED`
2. `python3 identity-protocol-local/scripts/validate_identity_experience_feedback.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `Experience feedback contract validation PASSED`
3. `python3 identity-protocol-local/scripts/validate_identity_knowledge_acquisition.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `Knowledge acquisition contract validation PASSED`
4. `python3 identity-protocol-local/scripts/validate_identity_trigger_regression.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `Trigger regression contract validation PASSED`

Source-level recheck confirms the current default report selection is sample-oriented:

1. `validate_identity_capability_arbitration.py` defaults to `runtime/examples/<identity>-capability-arbitration-sample.json` or `sample_report_path_pattern`.
2. `validate_identity_experience_feedback.py` defaults to `runtime/examples/<identity>-experience-feedback-sample.json` or `sample_report_path_pattern`.
3. `validate_identity_knowledge_acquisition.py` defaults to `runtime/examples/<identity>-knowledge-acquisition-sample.json` or `sample_report_path_pattern`.
4. `validate_identity_trigger_regression.py` defaults to `runtime/examples/<identity>-trigger-regression-sample.json` or `sample_report_path_pattern`.

Interpretation:

- these validators are not fake; they correctly validate sample/self-test families;
- but the protocol currently lacks an explicit sample-vs-live interpretation boundary on the strict lane.

### 2.5 Loop-center validators currently prove semantic-center readiness more strongly than live bridge closure

Direct replay:

- `python3 identity-protocol-local/scripts/validate_identity_routing_learning_strengthening.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `routing_learning_strengthening_status=PASS_REQUIRED`
2. `selected_candidate_id="selected_candidate_id"`
3. `selection_basis="selection_basis"`

Direct replay:

- `python3 identity-protocol-local/scripts/validate_feedback_to_judgement_loopback.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `feedback_to_judgement_loopback_status=PASS_REQUIRED`
2. the payload proves generic prompt/revalidation/rollback structure;
3. trio-specific decision-absorption fields are not yet required on this lane.

Interpretation:

- the loop centers are genuinely landed;
- current green proves semantic-center correctness more strongly than live bridge consumption.

### 2.6 Supporting live validators prove the distinction is real

Direct replays show that center-green does not imply full live closure:

1. `python3 identity-protocol-local/scripts/validate_capability_fit_roundtable_evidence.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`
   - `capability_fit_roundtable_status=SKIPPED_NOT_REQUIRED`
2. `python3 identity-protocol-local/scripts/validate_identity_experience_feedback_governance.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `FAIL`
   - reason: `latest feedback log too old: 15d > max_log_age_days=7`

Interpretation:

- the center validators are not globally broken;
- they simply need an explicit `semantic_center` versus `live_bridge` interpretation split.

### 2.7 Latest-log governance is already stronger than the primary false-green families

`validate_identity_experience_feedback_governance.py` already enforces:

1. minimum log count,
2. top-level field presence,
3. freshness bounded by `max_log_age_days`,
4. sample replay-pass expectations when a sample report is checked.

Interpretation:

- this validator is a real freshness gate, not a primary false-green source;
- the remaining improvement is same-run binding, not a total redesign.

## 3) Confirmed weak-live-linkage family map

### 3.1 Primary families

1. `prompt_presence_only`
   - `scripts/validate_prompt_bootstrap_capability.py`
   - `scripts/validate_prompt_capability_matrix.py`
   - `scripts/validate_prompt_derivation_conformance.py`
2. `sample_report_only`
   - `scripts/validate_identity_capability_arbitration.py`
   - `scripts/validate_identity_experience_feedback.py`
   - `scripts/validate_identity_knowledge_acquisition.py`
   - `scripts/validate_identity_trigger_regression.py`
3. `loop_meta_only`
   - `scripts/validate_identity_routing_learning_strengthening.py`
   - `scripts/validate_feedback_to_judgement_loopback.py`
   - `scripts/feedback_to_judgement_loopback_common.py`

### 3.2 Secondary family

1. `latest_log_no_run_binding`
   - `scripts/validate_identity_experience_feedback_governance.py`

### 3.3 Explicit exclusions

The following were rechecked and intentionally excluded from `ISSUE-037`:

1. protocol-feedback current-round validators using `scripts/protocol_feedback_lane_common.py`
2. docs/registry meta-lanes
3. artifact-family routing itself

## 4) External cross-validation that supports the strengthening direction

### 4.1 OpenAI docs track

Official OpenAI documentation describes traces as capturing prompts, tool calls, hand-offs, execution durations, file writes, and related metadata. That supports the protocol-side principle that downstream consumer truth should stay tied to actual execution context rather than historical presence alone.

Primary reference:

- https://developers.openai.com/cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk/#tracing-the-agentic-behavior-using-traces

### 4.2 Context7 / OpenTelemetry track

OpenTelemetry specification references reinforce the same design direction:

1. parent context must be derived from actual active context;
2. propagated context is a first-class binding surface;
3. links should be attached while causal context is available.

That supports:

1. run-bound evidence,
2. explicit causal linkage into downstream consumers,
3. no substitution of history/sample artifacts for current-run parentage.

Primary reference family:

- `https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/trace/api.md`
- `https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/context/api-propagators.md`

### 4.3 Root philosophy and roundtable inheritance

Deep review confirms that `v1.6.19` is best understood as a machine-world projection of the root philosophy, not a local validator workaround:

1. truth may exist without being operationally possessed;
2. possession may exist without current-run binding;
3. current-run binding may exist without next-hop consumption.

The review also confirms that the shared `roundtable_four_track_cross_validation_contract_v1` primitive is the correct reusable cross-validation intake for the route/loop side of this stream, while staying explicitly below the semantic ownership of `v1.6.17` and outside artifact-family ownership of `v1.6.18`.

## 5) Audit verdict

The additive `v1.6.19` stream should remain open and should now be documented as the protocol's weak-live-linkage strengthening lane.

### 5.1 What is already closed and must stay closed

1. `v1.6.17` loop strengthening ownership
2. `v1.6.17` bounded `4 -> 1` bridge ownership
3. `v1.6.18` artifact-family routing ownership

### 5.2 What remains open

1. prompt live-driver join,
2. sample/live interpretation split,
3. loop semantic-center vs live-bridge split,
4. same-run binding where freshness-only gates are insufficient.

### 5.3 Machine-law landing target ASB16-RQ-055 (2026-03-24)

The immediate positive-strengthening move is now clear and bounded:

1. land `ASB16-RQ-055` as the dedicated machine-consumed intake row for the weak-live-linkage differential audit;
2. land `scripts/validate_identity_weak_live_linkage.py` plus `scripts/ci/run_identity_weak_live_linkage_probes_ci.sh`;
3. wire the row into contract binding, required-gate bundle routing, required-contract coverage, release/readiness, and CI;
4. keep `ISSUE-037` open until the downstream consumer families themselves absorb the stronger live-binding semantics.

### 5.4 What must not happen

1. no pack-local fixes,
2. no validator loosening,
3. no history/sample artifact silently promoted to strict live truth,
4. no new artifact family,
5. no semantic reopen of `v1.6.17` / `v1.6.18`,
6. no business-scenario logic injected into protocol semantics.
