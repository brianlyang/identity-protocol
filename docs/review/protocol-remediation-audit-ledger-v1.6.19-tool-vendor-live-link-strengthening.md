# Protocol Remediation Audit Ledger (v1.6.19 Tool/Vendor Live-Link Strengthening)

Status: Active (`ISSUE-037` opened on 2026-03-24; trio contracts and strengthening/routing prerequisites are already landed, but live consumer closure is still incomplete)
Layer: protocol
Scope: audit evidence for the additive stream that strengthens trio current-run binding and live loop/prompt consumption without reopening `v1.6.17` or `v1.6.18`
Execution mode: canonical review ledger for the v1.6.19 tool/vendor live-link strengthening stream.

## 0) Current control-plane alias refs

- `identity/protocol/mappings/control-plane-status.current.yaml`
- `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/stream-scope-matrix.current.yaml`

## 1) Audit conclusion

This stream is worth absorbing.

The core diagnosis from protocol feedback is confirmed:

1. the trio is already on the protocol mainline;
2. the gap is not missing structure;
3. the gap is that current consumers still accept structural presence where live current-run evidence binding should be required.

Therefore the correct response is an additive shared-infrastructure strengthening stream, not:

- reopening earlier semantics,
- creating a new artifact family,
- or writing pack-local workarounds.

## 2) Local machine facts rechecked on 2026-03-24

### 2.1 Trio validators currently pass on historical evidence

Direct replay on `custom-creative-ecom-analyst` shows:

1. `python3 identity-protocol-local/scripts/validate_identity_tool_installation.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/tool-installation-custom-creative-ecom-analyst-20260227T040733Z.json`
2. `python3 identity-protocol-local/scripts/validate_identity_vendor_api_discovery.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/vendor-api-discovery-custom-creative-ecom-analyst-20260227T040733Z.json`
3. `python3 identity-protocol-local/scripts/validate_identity_vendor_api_solution.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst`
   - `PASS`
   - selected report: `runtime/reports/vendor-api-solution-custom-creative-ecom-analyst-20260227T040733Z.json`

Observed boundary:

1. these reports carry historical timestamps (`generated_at=2026-02-27T04:07:34Z`);
2. they do not currently prove strict current-run binding through a shared trio live-binding contract.

### 2.2 Discovery requiredization already treats the trio as landed structure

Direct replay:

- `python3 identity-protocol-local/scripts/validate_discovery_requiredization.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `discovery_requiredization_status=PASS_REQUIRED`
2. `requiredized_all_discovery_contracts=true`
3. `discovery_required_total=3`
4. `discovery_required_passed=3`
5. current receipt is historical requiredized state, not proof of current-run trio live consumption.

### 2.3 v1.6.17 strengthening currently proves structure, not trio live decision truth

Direct replay:

- `python3 identity-protocol-local/scripts/validate_identity_routing_learning_strengthening.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `routing_learning_strengthening_status=PASS_REQUIRED`
2. `selected_candidate_id="selected_candidate_id"`
3. `selection_basis="selection_basis"`

This proves the upper strengthening lane is present, but the published values are currently field-name placeholders rather than live trio decision projection.

### 2.4 v1.6.17 loopback currently proves generic prompt-flow closure, not trio-specific absorption

Direct replay:

- `python3 identity-protocol-local/scripts/validate_feedback_to_judgement_loopback.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed facts:

1. `feedback_to_judgement_loopback_status=PASS_REQUIRED`
2. loopback fields are generic prompt/revalidation/rollback projections;
3. trio-specific decision fields are not yet required for tool/vendor-selected routes.

### 2.5 Prompt-side consumers still accept presence-only linkage

Direct replays:

1. `validate_prompt_bootstrap_capability.py --json-only`
2. `validate_prompt_capability_matrix.py --json-only`
3. `validate_prompt_derivation_conformance.py --json-only`

Confirmed facts:

1. all three return `PASS_REQUIRED`;
2. all three set `requiredization_current_round_linked=true`;
3. the current implementation derives that linkage from prompt existence and/or configured validator presence rather than current-run trio evidence.

### 2.6 Roundtable lane boundary proves this is not a universal routing failure

Direct replay:

- `python3 identity-protocol-local/scripts/validate_capability_fit_roundtable_evidence.py --catalog .identity/catalog.local.yaml --identity-id custom-creative-ecom-analyst --json-only`

Confirmed fact:

1. `capability_fit_roundtable_status=SKIPPED_NOT_REQUIRED`

Interpretation:

1. the custom identity currently does not carry a required roundtable evidence contract on this lane;
2. yet the upper strengthening validator still returns `PASS_REQUIRED`;
3. therefore the verified defect is specifically “structure accepted without live trio consumer proof”, not “roundtable validator itself is broken everywhere”.

## 3) Base-repo deep-sweep result

### 3.1 Confirmed same-class gap cluster

The same-class gap is bounded to these consumers:

1. trio validators,
2. routing-strengthening projection,
3. loopback absorption,
4. prompt bootstrap / prompt matrix / prompt derivation linkage.

### 3.2 Explicit non-matches from the deep sweep

The following lanes were rechecked and intentionally excluded from `ISSUE-037`:

1. protocol-feedback current-round validators using `scripts/protocol_feedback_lane_common.py`
   - they already derive current-round linkage from correlated protocol-feedback activity;
2. mapping/docs meta-lanes
   - they are documentation/control-plane checks rather than runtime trio truth consumers.

This boundary matters because the correct fix is targeted shared infrastructure, not a blanket semantic rewrite of every `requiredization_current_round_linked` field in the repository.

## 4) External cross-validation that supports the strengthening direction

### 4.1 OpenAI docs track

Official OpenAI docs currently describe traces as capturing prompts, tool calls, hand-offs, files written, execution durations, and related metadata. That supports the protocol-side principle that downstream consumer truth should stay tied to the actual run/execution context rather than historical presence alone.

Primary reference:

- https://developers.openai.com/codex/guides/agents-sdk/#trace-the-workflow

### 4.2 Context7 / OpenTelemetry track

OpenTelemetry specification references reinforce the same design direction:

1. parent context must be derived from actual active context;
2. propagated context is a first-class binding surface;
3. links should be attached at creation time when causal context is available.

That supports:

1. run-bound trio evidence,
2. explicit causal linkage into loop-3 / loop-4 consumers,
3. no substitution of historical artifacts for current-run parentage.

Primary reference family:

- `/open-telemetry/opentelemetry-specification`

## 5) Audit verdict

The additive `v1.6.19` stream should be opened and kept narrow.

### 5.1 What is already closed and must stay closed

1. `v1.6.17` loop strengthening ownership
2. `v1.6.17` bounded `4 -> 1` bridge ownership
3. `v1.6.18` artifact-family routing ownership

### 5.2 What remains open

1. strict trio live evidence binding,
2. third-loop live trio projection,
3. fourth-loop trio decision absorption,
4. prompt live-evidence linkage.

### 5.3 What must not happen

1. no pack-local fixes,
2. no validator loosening,
3. no historical-report-as-live shortcut,
4. no new artifact family,
5. no semantic reopen of `v1.6.17` / `v1.6.18`.
