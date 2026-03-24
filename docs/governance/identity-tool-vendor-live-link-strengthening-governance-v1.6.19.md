# Identity Tool/Vendor Live-Link Strengthening Governance (v1.6.19)

Status: Active (`ISSUE-037` opened on 2026-03-24; trio contracts are already protocol-owned, but current-run live-consumption closure is still incomplete)
Layer: protocol
Scope: additive strengthening for tool-installation / vendor-api-discovery / vendor-api-solution evidence so loop-3, loop-4, and prompt consumers bind to current-run live truth instead of historical presence-only structure
Execution mode: topic-level canonical SSOT for v1.6.19 tool/vendor live-link strengthening governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_tool_vendor_live_link_strengthening`.
2. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` and `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` remain the semantic owners for the trio contract family and discovery-requiredization baseline.
3. `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md` remains the semantic owner for third-loop / fourth-loop strengthening and the bounded `4 -> 1` loopback bridge.
4. `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` remains the semantic owner for artifact-family routing and the frozen boundary that the trio is **not** a new artifact family.
5. `v1.6.19` does **not** reopen `v1.6.17` or `v1.6.18`; it strengthens live consumption on top of already-landed trio / strengthening / routing surfaces.
6. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
7. Scope is intentionally narrow:
   - strict current-run trio evidence binding,
   - loop-3 live selection projection,
   - loop-4 trio decision absorption,
   - prompt live-evidence linkage.
8. Scope explicitly excludes:
   - vendor ranking policy,
   - business strategy,
   - keyword invention,
   - scenario heuristics,
   - pack-local workaround logic.
9. `v1.6.19` is an additive strengthening stream only; it must not weaken `rq_047_protocol_no_downgrade_motherline_contract_v1`, must not introduce backward-compatibility shortcuts, and must not let historical trio reports masquerade as strict current-run success.
10. Frozen non-goal boundary:
    - the trio does not become a ninth artifact family,
    - `runtime/protocol-feedback/**` does not become trio truth,
    - `runtime/memory-absorption/**` does not become a live success path,
    - `protocol-vendor-intel` style descriptive surfaces do not replace trio run-bound evidence.

## 1) Why v1.6.19 is required

1. The trio contracts already exist and are already required on active runtime packs where this capability family is in use:
   - `tool_installation_contract`
   - `vendor_api_discovery_contract`
   - `vendor_api_solution_contract`
2. The trio already participates in protocol structure:
   - discovery requiredization,
   - prompt bootstrap,
   - prompt capability matrix,
   - `v1.6.17` routing/learning strengthening adjacency,
   - `v1.6.18` artifact-family routing freeze.
3. The remaining gap is therefore **not** “missing protocol structure”.
4. The remaining gap is that the current consumer chain still accepts:
   - historical trio reports,
   - field-name placeholders,
   - prompt presence-only linkage,
   as if that were equivalent to current-run live consumption.
5. This stream exists to close exactly that gap without redefining the underlying loop semantics or the artifact-family taxonomy.

## 2) Confirmed current-state diagnosis

### 2.1 What is already landed

1. Trio contract presence is already protocol-owned.
2. Discovery requiredization already treats the trio as a governed dependency set.
3. `v1.6.17` already froze the upper-layer third-loop / fourth-loop strengthening centers and the bounded `4 -> 1` loopback bridge.
4. `v1.6.18` already froze artifact-family routing so trio evidence cannot be misclassified as generic `memory`.

### 2.2 What is still incomplete

1. Trio validators still validate primarily on:
   - report existence,
   - required field presence,
   - basic selected-row structure.
2. Trio strict live-binding is not yet frozen as a shared contract for strict operations.
3. Third-loop strengthening still republishes hook field names instead of current-run trio selection truth.
4. Fourth-loop loopback/prompt absorption still validates generic prompt-flow semantics rather than trio decision absorption when the selected route is tool/vendor-based.
5. Prompt validators still treat prompt existence / configured validator presence as sufficient linkage, which is weaker than current-run trio evidence consumption.

## 3) Deep-sweep classification (what is the same class, what is not)

### 3.1 Confirmed same-class consumer-gap surfaces

The confirmed same-class gap is bounded to the trio live-consumption chain:

1. `scripts/validate_identity_tool_installation.py`
2. `scripts/validate_identity_vendor_api_discovery.py`
3. `scripts/validate_identity_vendor_api_solution.py`
4. `scripts/validate_identity_routing_learning_strengthening.py`
5. `scripts/feedback_to_judgement_loopback_common.py`
6. `scripts/validate_prompt_bootstrap_capability.py`
7. `scripts/validate_prompt_capability_matrix.py`
8. `scripts/validate_prompt_derivation_conformance.py`

These are the surfaces where current machine replays prove “protocol strong / consumer still structural”.

### 3.2 Adjacent surfaces intentionally excluded from this stream

The following surfaces were explicitly rechecked and must **not** be misclassified as the same defect family:

1. protocol-feedback current-round validators that reuse `scripts/protocol_feedback_lane_common.py`
   - they already derive `requiredization_current_round_linked` from correlated current-round activity rather than simple presence;
2. documentation / registry meta-lanes such as mapping-coverage or docs-bridge checks
   - they can legitimately project broad linkage booleans because they are not execution-time trio truth consumers;
3. artifact-family routing itself
   - `v1.6.18` remains about path/semantic routing boundaries, not about loop-3 / loop-4 live decision projection.

This deep-sweep boundary is mandatory. `v1.6.19` must fix the real shared consumer gap, not opportunistically absorb unrelated lanes.

## 4) Frozen strengthening target for this stream

### 4.1 Trio live evidence binding

Strict operations (`validate`, `readiness`, `update`, `e2e`, `ci`) must distinguish:

1. current-run live trio evidence,
2. scan/history-only trio evidence.

Minimum binding family to freeze under shared infrastructure:

1. `run_id_binding`
2. `current_round_linked`
3. `active_execution_report_ref`
4. `upstream_trigger_ref`
5. `generated_at`

Historical trio reports may remain available for scans and audit, but they must not satisfy strict live success by presence alone.

### 4.2 Third-loop live selection projection

When the selected route belongs to the tool/vendor class, loop-3 must not stop at generic candidate convergence. It must project live trio decision truth, including:

1. `selected_candidate_id`
2. `selection_basis`
3. `selected_vendor_api_ref`
4. `selected_solution_ref`
5. `solution_pattern`
6. `fallback_vendor_or_route_ref`
7. `fallback_solution_ref`

Field-name placeholders are non-canonical once this stream lands.

### 4.3 Fourth-loop trio decision absorption

When the previous selected route belongs to the tool/vendor class, loop-4 must not treat learning as a generic prompt/link/replay success. It must absorb trio decision truth into the replay-governed operational-prompt path, including:

1. `selected_vendor_api_ref`
2. `solution_pattern`
3. `decision_rationale_ref`

This stream strengthens absorption, not semantic ownership: the operational prompt remains a bounded preflight aid, not first-loop truth.

### 4.4 Prompt live-evidence linkage

Prompt-facing validators must stop treating:

1. prompt existence,
2. validator literal presence,
3. configured driver presence,

as sufficient proof that trio live evidence was consumed.

Prompt linkage must instead derive from live trio evidence binding and the actual selected/absorbed projection path.

## 5) Cross-validation intake that justifies this stream

### 5.1 Roundtable / routing track

Internal routing replays show that the strengthening lane is present, but live decision projection is not yet consumed as current-run trio truth.

### 5.2 Vendor trio track

Internal trio replays show that historical reports can still pass the three validator surfaces even when they are not bound to the current execution round.

### 5.3 Reference / search / OpenAI docs / Context7 track

External references align with the strengthening direction rather than contradicting it:

1. OpenAI tracing guidance emphasizes that traces should capture prompts, tool calls, hand-offs, and execution details, which supports run-linked consumer truth rather than historical-presence substitution.
2. OpenTelemetry trace-context guidance emphasizes parent context, propagated context, and trace linkage as first-class binding primitives, which supports the protocol-side requirement that downstream decision evidence must stay causally bound to the active run.

These references are justificatory only. Normative truth remains protocol-owned inside this repository.

## 6) Stop condition

`ISSUE-037` may close only when all of the following are simultaneously true:

1. strict trio validators fail-close on history-only evidence that lacks current-run binding;
2. third-loop strengthening consumes actual trio live selection projection when tool/vendor routes are selected;
3. fourth-loop strengthening consumes trio decision absorption when tool/vendor routes are selected;
4. prompt bootstrap / prompt matrix / prompt derivation no longer claim current-round linkage from prompt presence alone;
5. the fix is shared infrastructure, not per-pack patching;
6. the fix preserves:
   - `v1.6.17` semantic ownership,
   - `v1.6.18` artifact-family boundaries,
   - no-downgrade / no-backstop rules.

## 7) Non-goals and forbidden shortcuts

1. Do not reopen `v1.6.17` loop semantics.
2. Do not reopen `v1.6.18` family taxonomy.
3. Do not add a new artifact family for trio evidence.
4. Do not accept historical trio reports as strict-pass substitutes.
5. Do not patch only one validator while leaving the rest on presence-only semantics.
6. Do not hide the gap by loosening upper-layer validators or by inventing pack-local overrides.
