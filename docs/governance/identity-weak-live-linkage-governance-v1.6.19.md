# Identity Weak Live Linkage Governance (v1.6.19)

Status: Active (`ISSUE-037` opened on 2026-03-24; the stream opened from the tool/vendor trio path, and deep-sweep review now confirms a broader weak-live-linkage consumer-gap family that still lacks strict current-run closure)
Layer: protocol
Scope: additive strengthening for current-run live evidence binding across trio, prompt, sample, and loop-consumer surfaces so protocol-owned validators stop equating declaration/presence/sample/meta success with full operational closure
Execution mode: topic-level canonical SSOT for v1.6.19 weak-live-linkage governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_weak_live_linkage`.
2. The stream name remains stable because the opening signal came from the tool-installation / vendor-api-discovery / vendor-api-solution trio. That naming stability does **not** limit the stream to trio-only symptoms once deep-sweep review proves the same weak-live-linkage pattern on adjacent protocol-owned consumers.
3. `docs/governance/identity-actor-session-binding-governance-v1.5.0.md` and `docs/governance/identity-actor-session-binding-governance-v1.6.0.md` remain the semantic owners for the trio contract family and discovery-requiredization baseline.
4. `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md` remains the semantic owner for third-loop / fourth-loop strengthening and the bounded `4 -> 1` loopback bridge.
5. `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` remains the semantic owner for artifact-family routing and the frozen boundary that sample/live/meta surfaces must not be reclassified as a new artifact family.
6. `v1.6.19` does **not** reopen `v1.6.17` or `v1.6.18`; it strengthens live-consumption interpretation on top of already-landed trio / strengthening / routing surfaces.
7. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.current.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
8. `v1.6.19` now freezes two protocol-level concerns together:
   - strict current-run strengthening for the trio-led consumer path;
   - the shared `weak_live_linkage` differential-audit method for same-class protocol-owned consumers.
9. Scope explicitly excludes:
   - vendor ranking policy,
   - business strategy,
   - keyword invention,
   - scenario heuristics,
   - pack-local workaround logic.
10. `v1.6.19` is an additive strengthening stream only; it must not weaken `rq_047_protocol_no_downgrade_motherline_contract_v1`, must not introduce backward-compatibility shortcuts, and must not let history/sample/meta artifacts masquerade as strict current-run success.
11. Frozen non-goal boundary:
    - the trio does not become a ninth artifact family,
    - `runtime/protocol-feedback/**` does not become trio truth,
    - `runtime/memory-absorption/**` does not become a live success path,
    - sample/self-test artifacts do not disappear,
    - semantic-center validators do not become omnipotent business executors.

## 1) Why v1.6.19 is required

1. The protocol already contains strong structural owner lanes for the affected families:
   - trio contract presence and discovery requiredization,
   - prompt bootstrap / prompt matrix / prompt derivation guards,
   - loop-3 / loop-4 semantic-center strengthening,
   - freshness governance on experience-feedback logs.
2. The remaining problem is therefore **not** “missing protocol structure”.
3. The remaining problem is that several current consumers still accept one of the following as if it were equivalent to full live closure:
   - historical report presence,
   - prompt presence or configured-driver literals,
   - sample-report closure,
   - hook/field-name alignment,
   - latest-log freshness without same-run binding.
4. That defect family is more dangerous than an ordinary red gate because it can produce false-green interpretation.
5. `v1.6.19` exists to close exactly that gap without redefining the underlying loop semantics or the artifact-family taxonomy.

## 2) Base-repo achievements already built and explicitly preserved

The deep review for this stream does **not** classify the current base-repo achievements as failures. It classifies them correctly by layer so they can be strengthened instead of erased.

### 2.1 Structural achievements that remain valid

1. Trio contract presence is already protocol-owned.
2. Discovery requiredization already treats the trio as a governed dependency set.
3. `v1.6.17` already froze the upper-layer third-loop / fourth-loop semantic centers and the bounded `4 -> 1` bridge.
4. `v1.6.18` already froze artifact-family routing so trio/sample/meta surfaces cannot be collapsed into generic `memory` wording.

### 2.2 Layered achievements that must be preserved but reinterpreted correctly

1. Prompt validators are valid **presence/coverage** guards.
   - They correctly prove that prompt surfaces exist and declare their required driver names.
   - They do **not** yet prove that current-run live driver receipts were consumed.
2. Sample validators are valid **sample/self-test** guards.
   - They correctly prove sample payload shape and baseline schema expectations.
   - They do **not** yet prove strict live runtime closure.
3. Loop-center validators are valid **semantic-center** guards.
   - They correctly prove that loop-3 / loop-4 owner hooks and core projections exist.
   - They do **not** yet prove that live bridge evidence was consumed on the active route.
4. Latest-log freshness validators are valid **freshness** guards.
   - They correctly prove that a latest log exists and is fresh enough for the governed freshness rule.
   - They do **not** yet prove same-run binding by themselves.

These achievements are protocol assets and must remain green on their own terms. The `v1.6.19` task is to stop misreading them as full operational closure when only a lower layer has been proven.

## 3) Confirmed current-state gap families

### 3.1 Prompt presence-only family

The following prompt-side consumers can currently return `PASS_REQUIRED` while proving prompt presence / declared driver coverage rather than current-run live consumption:

1. `scripts/validate_prompt_bootstrap_capability.py`
2. `scripts/validate_prompt_capability_matrix.py`
3. `scripts/validate_prompt_derivation_conformance.py`

Current deep-sweep signature:

- `requiredization_current_round_linked` can become true from prompt existence and/or configured driver literals;
- `validate_prompt_capability_matrix.py` can keep `prompt_capability_matrix_status=PASS_REQUIRED` while `discovery_requiredized_all=false`.

### 3.2 Sample-report-only family

The following validators currently default to `runtime/examples/*` or `sample_report_path_pattern` surfaces and therefore prove sample/self-test closure unless explicitly given a live report:

1. `scripts/validate_identity_capability_arbitration.py`
2. `scripts/validate_identity_experience_feedback.py`
3. `scripts/validate_identity_knowledge_acquisition.py`
4. `scripts/validate_identity_trigger_regression.py`

This is valid for sample/self-test hygiene, but not sufficient for strict live closure.

### 3.3 Loop meta-only family

The following loop consumers currently prove semantic-center readiness more strongly than live bridge consumption:

1. `scripts/validate_identity_routing_learning_strengthening.py`
2. `scripts/validate_feedback_to_judgement_loopback.py`
3. `scripts/feedback_to_judgement_loopback_common.py`

Current deep-sweep signature:

- route/feedback enforcement blocks, validators, and field-name hooks are present and aligned;
- `selected_candidate_id` / `selection_basis` can still be republished as hook field names rather than live route truth;
- semantic-center status can remain green while supporting live validators are `SKIPPED_NOT_REQUIRED` or red.

### 3.4 Secondary risk: latest-log-no-run-binding

`scripts/validate_identity_experience_feedback_governance.py` already enforces freshness and is therefore **not** a primary false-green source. However, it still represents a secondary strengthening target because latest-log freshness alone does not yet guarantee same-run binding.

### 3.5 Explicit exclusions from this stream

The following surfaces were rechecked and must **not** be misclassified into `ISSUE-037`:

1. protocol-feedback current-round validators that reuse `scripts/protocol_feedback_lane_common.py`
   - they already derive current-round linkage from correlated protocol-feedback activity rather than simple prompt/sample/meta presence;
2. documentation / registry meta-lanes such as mapping-coverage or docs-bridge checks
   - they are documentation/control-plane checks rather than runtime live-truth consumers;
3. artifact-family routing itself
   - `v1.6.18` remains about path/semantic routing boundaries, not about strict run-bound evidence consumption.

This deep-sweep boundary is mandatory. `v1.6.19` must fix the real shared consumer gap, not opportunistically absorb unrelated lanes.

## 4) Weak Live Linkage Differential Audit method (frozen for v1.6.19)

### 4.1 Core definition

`weak_live_linkage` means a validator/contract/prompt/hook surface can pass on declaration, prompt/sample/meta evidence, or latest-log presence while current-run binding and next-hop consumption remain unproven.

### 4.2 Four-layer closure model

Any strict success claim must be decomposed into four layers:

1. `contract_layer`
   - the contract exists, is required, and names its validator/hook surfaces.
2. `artifact_layer`
   - the correct governed artifact family exists, rather than prompt-only text or sample-only evidence.
3. `run_binding_layer`
   - the evidence is causally bound to the current run through fields such as run id, freshness, receipt refs, or selected-candidate binding.
4. `consumption_layer`
   - the next hop actually consumed the evidence rather than merely coexisting with it.

### 4.3 Allowed verdict classes

The stream freezes the following interpretation classes:

1. `structure_green`
   - contract layer only.
2. `sample_or_history_green`
   - contract + artifact layers pass, but run-binding is not yet proven.
3. `unabsorbed_green`
   - run-binding exists, but next-hop consumption is not yet proven.
4. `full_operational_closure`
   - all four layers pass.

A generic `PASS_REQUIRED` must not be narrated as `full_operational_closure` unless the relevant live-binding and consumption layers are also green.

### 4.4 Differential probes required by method

The method freezes four probe styles for detecting false-green strength mismatches:

1. `presence_probe`
   - preserve prompt text / tokens / validator declarations while removing live receipts or projection digests;
   - if strict success survives, classify as prompt presence-only drift.
2. `sample_probe`
   - preserve sample/example artifacts while removing or withholding live report families;
   - if strict success survives, classify as sample-report-only drift.
3. `meta_probe`
   - preserve hook/field-name alignment while forcing supporting live validators to `FAIL_REQUIRED` or `SKIPPED_NOT_REQUIRED`;
   - if semantic-center success survives as if it were full closure, classify as loop meta-only drift.
4. `run_binding_probe`
   - preserve latest/fresh artifacts while breaking same-run binding;
   - if strict success survives, classify as latest-log-no-run-binding risk.

## 5) Frozen strengthening targets for this stream

### 5.1 Prompt-live-driver join

Prompt-side validators must strengthen from presence coverage to current-run driver absorption. Minimum shared fields to freeze:

1. `driver_receipt_refs`
2. `driver_run_id`
3. `driver_projection_digest`
4. `current_run_driver_binding_status`

`requiredization_current_round_linked` must no longer derive directly from `prompt_path.exists()` or configured driver literals alone.

### 5.2 Sample / live family split

Sample/self-test families remain valid, but strict live closure must differentiate them explicitly. Minimum shared status family to freeze:

1. `evidence_origin=sample|live`
2. `report_freshness_status`
3. `run_id_binding_status`
4. `strict_live_proof_status`

Strict validators must default to live families for strict operations. Sample families may remain for fixture/self-test/fallback interpretation only and must not silently satisfy full strict success.

### 5.3 Loop semantic-center vs live-bridge split

Loop-center validators must stop conflating owner-lane correctness with active-route evidence consumption. Minimum split to freeze:

1. `semantic_center_status`
2. `live_bridge_status`

Minimum route-side live bridge fields:

1. `selected_candidate_receipt_ref`
2. `roundtable_receipt_ref`
3. `route_live_binding_status`

Minimum feedback / `4 -> 1` live bridge fields:

1. `operational_prompt_receipt_ref`
2. `feedback_run_id`
3. `preflight_reentry_receipt_ref`
4. `loopback_live_binding_status`

### 5.4 Latest-log same-run binding

Freshness-only governance remains valuable, but when same-run binding matters the stream must freeze explicit join fields such as:

1. `required_run_id`
2. `latest_feedback_run_id_match_status`
3. `operational_prompt_run_join_status`

## 6) Cross-validation intake that justifies this stream

### 6.1 Base-repo deep sweep

Repo-local review confirms a bounded same-class family:

1. trio history-only strict success,
2. prompt presence-only strict success,
3. sample-report-only strict success,
4. loop meta-only strict success,
5. latest-log-no-run-binding as a secondary strengthening target.

### 6.2 Roundtable / routing track

Internal routing replays show that the strengthening lane is present, but live decision projection is not yet consumed as current-run route truth.

### 6.3 OpenAI docs / Context7 / reference track

External references align with the strengthening direction rather than contradicting it:

1. OpenAI tracing guidance emphasizes that traces should capture prompts, tool calls, hand-offs, execution details, and related metadata, which supports run-linked consumer truth rather than historical-presence substitution.
2. OpenTelemetry trace-context guidance emphasizes parent context, propagated context, and trace linkage as first-class binding primitives, which supports the protocol-side requirement that downstream decision evidence must stay causally bound to the active run.

These references are justificatory only. Normative truth remains protocol-owned inside this repository.

### 6.4 Root philosophy inheritance and truth-lifecycle anchor

`v1.6.19` is not a validator convenience stream. It is a direct operationalization of the root philosophy frozen in:

1. `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`
2. `identity/protocol/README.md`

The inherited runtime rule is:

- truth existence != operational possession;
- operational possession != current-run binding;
- current-run binding != next-hop consumption.

So this stream must keep those layers machine-separate rather than narratively collapsed into one generic green.

### 6.5 Roundtable four-track primitive alignment

`v1.6.19` reuses the shared `roundtable_four_track_cross_validation_contract_v1` primitive as a bounded cross-validation intake for route/loop evidence discrimination.

Frozen boundary:

1. the primitive may help prove whether a route/loop surface is only semantically green or actually run-bound;
2. the primitive does **not** become a new loop;
3. the primitive does **not** become a new artifact family;
4. the primitive does **not** replace the semantic owners of `v1.6.17` or `v1.6.18`.

### 6.6 Machine-law landing target ASB16-RQ-055 (2026-03-24)

`v1.6.19` now requires one dedicated machine-consumed intake row:

- `ASB16-RQ-055`
- kernel contract: `rq_055_identity_weak_live_linkage_differential_audit_contract_v1`
- shared validator: `scripts/validate_identity_weak_live_linkage.py`
- shared probe runner: `scripts/ci/run_identity_weak_live_linkage_probes_ci.sh`

This row closes the machine-law differential-audit intake for weak live linkage, but it does **not** by itself close `ISSUE-037`.

Its required role is narrower and stricter:

1. freeze the four-layer closure model on machine-consumed runtime payloads;
2. freeze the allowed verdict classes on machine-consumed runtime payloads;
3. project current runtime state as closure class instead of narrating every green as full closure;
4. keep the stream additive and compatible with the frozen `v1.6.17` / `v1.6.18` ownership split.

### 6.7 Machine observability projection strengthening (2026-03-24)

`ASB16-RQ-055` is not fully useful if its closure-class payload stays buried inside raw required-gate bundle rows. Therefore the stream also freezes one additive observability rule:

1. three-plane and full-scan surfaces must expose a mapping-driven compact target projection derived from `contract-binding.current.yaml`;
2. the compact projection must reuse `report_field_refs` rather than hardcoding target-specific field names into scan surfaces;
3. the compact projection must preserve the distinction between:
   - machine-law intake landed (`identity_weak_live_linkage_status=PASS_REQUIRED`),
   - current operational state (`overall_linkage_status` / `operational_closure_class`),
   - and projection-surface health (`projection_status`);
4. the projection is explanatory and observability-oriented only:
   - it does not change bundle verdict semantics,
   - it does not close `ISSUE-037`,
   - it does not loosen any validator or required gate.

## 7) Stop condition

`ISSUE-037` may close only when all of the following are simultaneously true:

1. `weak_live_linkage` terminology, the four-layer differential-audit method, and `ASB16-RQ-055` machine-law intake are frozen on canonical protocol surfaces;
2. prompt-side validators fail-close or downgrade interpretation when only prompt presence/configured drivers exist without current-run driver receipts;
3. sample-report-only validators explicitly distinguish sample/self-test closure from strict live closure;
4. loop-center validators expose separate `semantic_center_status` and `live_bridge_status` semantics instead of narrating center-green as full route/loop closure;
5. same-run binding is enforced where freshness-only latest-log checks are insufficient for strict closure;
6. the fix remains shared infrastructure, not per-pack patching;
7. the fix preserves:
   - `v1.6.17` semantic ownership,
   - `v1.6.18` artifact-family boundaries,
   - no-downgrade / no-backstop rules.
8. three-plane / full-scan machine consumers can compare compact closure-class projections without parsing raw nested bundle payloads by hand.

## 8) Non-goals and forbidden shortcuts

1. Do not reopen `v1.6.17` loop semantics.
2. Do not reopen `v1.6.18` family taxonomy.
3. Do not add a new artifact family for trio/sample/meta evidence.
4. Do not accept historical trio reports as strict-pass substitutes.
5. Do not accept sample/example reports as silent strict-pass substitutes.
6. Do not patch only one validator while leaving the rest on presence-only or meta-only semantics.
7. Do not turn prompt validators into business executors.
8. Do not delete sample/self-test families to hide the distinction.
9. Do not hide the gap by loosening upper-layer validators or inventing pack-local overrides.
