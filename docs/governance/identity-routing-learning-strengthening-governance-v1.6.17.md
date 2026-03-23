# Identity Routing/Learning Strengthening Governance (v1.6.17)

Status: Active (`ASB16-RQ-048` / `ASB16-RQ-049` landed as protocol-owned upper-layer runtime contracts on 2026-03-23; `ASB16-RQ-050` remains open as a docs-owned 4→1 loopback bridge pending a dedicated machine consumer lane)  
Layer: protocol  
Scope: upper-layer strengthening for the third and fourth core capability contracts plus the bounded fourth-loop-to-first-loop loopback bridge  
Execution mode: topic-level canonical SSOT for v1.6.17 routing/learning strengthening governance.

## 0) State interpretation guard (mandatory)

1. This document is the active governance source for `identity_routing_learning_strengthening`.
2. `identity/protocol/IDENTITY_PROTOCOL.md` remains the kernel source for the four core capability contracts.
3. `v1.6.2` remains the semantic owner for the first two loops after kernel freeze:
   - `Accurate judgement contract` -> canonical multimodal enforcement binding
   - `Reasoning loop contract` -> canonical fail-close reasoning binding
4. `v1.6.17` does **not** redefine or replace the kernel source text for:
   - `Auto-routing contract`
   - `Rule learning contract`
5. `v1.6.17` strengthens upward from those kernel contracts with the same class of runtime-consumable clarity already enjoyed by the first two loops.
6. Current-state judgment for this stream must anchor to:
   - `identity/protocol/mappings/stream-doc-registry.current.yaml`
   - `identity/protocol/mappings/stream-scope-matrix.current.yaml`
   - `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`
   - `identity/protocol/mappings/contract-binding.current.yaml`
   - `identity/protocol/mappings/semantic-term-registry.v1.6.yaml`
   - `identity/protocol/IDENTITY_PROTOCOL.md`
   - `identity/protocol/IDENTITY_RUNTIME.md`
   - `docs/workbook/protocol-issue-register-v1.6.md`
   - `docs/workbook/protocol-deep-audit-workbook-v1.6.md`
7. This stream owns only the strengthening gap between kernel contracts and runtime-consumable enforcement, plus the bounded 4→1 loopback bridge:
   - route-discovery convergence
   - feedback-derived operational-prompt injection
   - shared four-track cross-validation primitive consumption
   - CURRENT_TASK / required-gate / readiness symmetry
   - fourth-loop-to-first-loop loopback semantics as governed preflight aid only
8. This stream owns mechanism strengthening only. It does **not** own business policy, search-keyword invention, product strategy, scenario datasets, vendor/product examples, ranking heuristics, or instance-specific operating playbooks.
9. `rq_047_protocol_no_downgrade_motherline_contract_v1` remains active in this stream with full force: no downgrade, no backward compatibility, and no live backstop for lagging packs/workspaces.
10. Frozen current-state interpretation:
   - `ISSUE-030` is **closed** for the core third/fourth-loop strengthening pair;
   - `ISSUE-031` remains **open** only for the standalone 4→1 loopback bridge.

## 1) Why v1.6.17 is required

1. The kernel already froze the source contracts:
   - `Auto-routing contract`: requires problem-type routing map + route-switch policy, and requires route discovery when uncertainty persists.
   - `Rule learning contract`: requires append-only rulebook linkage to run evidence, plus both positive and negative rule accumulation over time.
2. The runtime contract family already carried nearby surfaces:
   - `capability_orchestration_contract`
   - `knowledge_acquisition_contract`
   - `experience_feedback_contract`
   - `capability_arbitration_contract`
3. Shared validators already existed for large portions of this area:
   - `scripts/validate_discovery_requiredization.py`
   - `scripts/validate_capability_fit_roundtable_evidence.py`
   - `scripts/validate_identity_orchestration_contract.py`
   - `scripts/validate_identity_knowledge_contract.py`
   - `scripts/validate_identity_experience_feedback.py`
   - `scripts/validate_identity_experience_feedback_governance.py`
   - `scripts/validate_identity_capability_arbitration.py`
4. The missing gap was never kernel absence; it was the absence of **symmetric upper-layer strengthening** that instances could consume like first-class runtime capability primitives.
5. `v1.6.17` closes that symmetry gap for the third/fourth-loop center through `ASB16-RQ-048` / `ASB16-RQ-049` and keeps the 4→1 bridge separate through `ASB16-RQ-050`.

## 2) Frozen strengthening model

### 2.1 Kernel source contracts stay where they are

1. `Auto-routing contract` remains the kernel source statement for the third loop.
2. `Rule learning contract` remains the kernel source statement for the fourth loop.
3. `v1.6.17` strengthens upward from those kernel contracts rather than replacing them with a parallel motherline.
4. This mirrors how the protocol previously strengthened upward from source-level capability language into explicit stream-owned binding on the first two loops.

### 2.2 Auto-routing upper-layer strengthening (third loop)

Opening strengthening family names frozen by this stream:

- `route_discovery_convergence_contract_v1`
- `route_discovery_enforcement`

Frozen strengthening obligations:

1. Persistent uncertainty must not leave route discovery as a narrative suggestion.
2. Discovery may fan out across identity / skill / tool candidates, but acceptance must converge serially.
3. Candidate comparison must be machine-auditable rather than chat-only.
4. A selected route must be explicit, and rejected candidates must not disappear silently.
5. Failure of the selected route must preserve a governed fallback decision rather than returning to ambient improvisation.

Minimum strengthening evidence family:

- `trigger_reason`
- `uncertainty_type`
- `candidate_rows`
- `selected_candidate_id`
- `selection_basis`
- `convergence_status`
- `next_action`
- `fallback_route_if_selected_fails`

Frozen fail-close interpretation:

- discovery-triggered lanes may not claim healthy routing with zero candidate set;
- more than one effective selected candidate is non-canonical;
- missing `selection_basis` after candidate comparison is non-canonical;
- route switching under persistent uncertainty may not bypass the strengthening evidence surface.

### 2.3 Rule-learning upper-layer strengthening (fourth loop)

Opening strengthening family names frozen by this stream:

- `feedback_operational_prompt_contract_v1`
- `feedback_operational_prompt_enforcement`

Frozen strengthening obligations:

1. Append-only rulebook linkage to run evidence remains mandatory and is not replaced by prompt text.
2. Positive and negative rule accumulation remain mandatory and are not collapsed into one undifferentiated summary.
3. The added governed derived layer turns validated feedback into a scoped operational prompt artifact for the next round.
4. Derived operational prompts must stay scoped, replay-verified, rollback-capable, and TTL-bounded.
5. Derived operational prompts must not silently mutate kernel/system/identity baseline instructions.

Minimum strengthening evidence family:

- `feedback_summary_ref`
- `source_feedback_ids`
- `rulebook_delta`
- `operational_prompt_ref`
- `operational_prompt_digest`
- `prompt_scope`
- `prompt_target_route`
- `prompt_target_stage`
- `prompt_injection_status`
- `replay_case_ref`
- `replay_status`
- `rollback_prompt_ref`
- `ttl_rounds`

Frozen fail-close interpretation:

- feedback may not be claimed as “learned” without append-only evidence-linked rulebook impact;
- a derived operational prompt may not become active without replay evidence;
- an expired or rollback-required operational prompt may not remain on the live success path;
- operational prompt injection may not be used as a compatibility backstop for lagging packs.

### 2.4 Feedback-to-judgement loopback bridge (4→1)

1. `feedback_to_judgement_loopback_contract_v1` is frozen as a **standalone bridge contract**, not as a sub-bullet of the fourth-loop center and not as a synonym for first-loop truth.
2. Loopback artifacts are governed **preflight aids only**; they may accelerate next-round first-loop preparation but may not replace current-round first-loop revalidation.
3. The loopback bridge stays distinct from both:
   - `feedback_operational_prompt_contract_v1`
   - `roundtable_four_track_cross_validation_contract_v1`
4. Frozen loopback obligations:
   - scope-bounded reentry
   - TTL-bounded validity
   - replay / rollback control
   - explicit demotion when current evidence conflicts
   - negative-feedback writeback preservation
5. Frozen fail-close interpretation:
   - fourth-loop artifacts may not be promoted into current-round first-loop truth by narrative convenience;
   - loopback must remain subordinate to first-loop evidence revalidation;
   - any future machine consumer of the bridge must preserve no-downgrade / no-backstop semantics.

#### 2.4.1 Closed-loop topology and PDCA-isomorphic interpretation

1. The frozen topology is `first-loop judgement -> second-loop reasoning -> third-loop route discovery -> fourth-loop operational prompt strengthening -> governed 4→1 loopback -> first-loop revalidation`.
2. This topology is intentionally **PDCA-isomorphic as a control structure**, but it does **not** rewrite the protocol kernel into generic business-process jargon; the semantic owners remain judgement / reasoning / routing / learning.
3. The first loop stays authoritative for current-round evidence truth even after loopback reentry.
4. The third loop may fan out across governed parallel probes only while the shared four-track primitive is still unsatisfied.
5. The fourth loop may promote a derived operational prompt only after evidence-linked feedback and shared four-track cross-validation satisfy promotion requirements.
6. The 4→1 bridge may return only governed preflight aids, never current-round truth, so the loop improves preparation without collapsing revalidation.
7. A first-loop conflict after reentry must write back into fourth-loop negative feedback and/or rollback action rather than lingering as silent prompt residue.

### 2.5 Shared four-track cross-validation primitive

1. `roundtable_four_track_cross_validation_contract_v1` is the shared cross-validation primitive consumed by the strengthened third and fourth loops.
2. The frozen four tracks are:
   - roundtable
   - vendor / official capability
   - reference / specification
   - search / runtime probe
3. First-loop multimodal evidence may feed these tracks when required, but it does **not** become a fifth track.
4. The third loop and fourth loop keep independent centers; they both consume this primitive.
5. Third-loop parallel probes require serial acceptance through this primitive.
6. Fourth-loop promotion may occur only after this primitive is satisfied, and any next-round first-loop reentry must occur separately through `feedback_to_judgement_loopback_contract_v1`.
7. Candidate rows promoted inside the third loop must preserve per-track evidence linkage and explicit rejection rationale for non-selected candidates.
8. Derived operational prompts promoted inside the fourth loop must preserve the same four-track promotion basis before activation, not merely before archival.
9. The 4→1 bridge may reuse promotion outputs from this primitive, but loopback admission and first-loop truth remain separately governed rather than implied by the shared primitive alone.

### 2.6 Symmetry rule for CURRENT_TASK, gates, and readiness

The frozen symmetry targets are now machine-landed for the third/fourth-loop center:

1. pack-visible enforcement hooks under `capability_arbitration_contract`:
   - `route_discovery_enforcement`
   - `feedback_operational_prompt_enforcement`
2. required-gate bundle status projection:
   - `route_discovery_convergence_status`
   - `feedback_operational_prompt_status`
3. explicit readiness-row citizenship for the same two strengthening families;
4. shared probe coverage;
5. creator/backfill/adoption wiring for pack consumption.

Current landed interpretation:

1. `create_identity_pack.py` and `repair_contract_backfill.py` materialize the strengthening hooks.
2. `scripts/validate_identity_routing_learning_strengthening.py` machine-validates the pair.
3. `scripts/validate_identity_capability_arbitration.py` consumes the strengthening hooks directly.
4. `scripts/required_gate_bundle_runner.py`, `scripts/ci/run_required_runtime_gates_ci.sh`, and `scripts/release_readiness_check.py` now carry the strengthening lane.

This stream therefore judges the third/fourth-loop center as landed protocol infrastructure, not as workbook-only prose.

## 3) Business boundary and non-goals

1. `v1.6.17` solves a protocol-side structural blocker: instances already confirm better and reason better, but previously lacked equally explicit motherline strengthening for “find a better route” and “turn validated feedback into the next-round operational push”.
2. The stream does **not** claim protocol can guarantee perfect business outcomes, perfect search quality, or perfect vendor/tool behavior.
3. It claims that once the stream is fully built and consumed correctly, protocol should no longer be the reason an identity instance lacks:
   - a governed mechanism for route discovery under persistent uncertainty,
   - a governed mechanism for validated feedback reinjection,
   - a bounded 4→1 preflight bridge that does not pollute first-loop truth,
   - a governed demotion / rollback path when current first-loop evidence conflicts with previously promoted prompt artifacts.
4. This claim remains **generic across business domains**: it resolves control-plane absence, not business scoring, ranking, content generation, or domain data quality by itself.
5. Do not invent business-specific routing tables, search phrases, operating heuristics, example products, or scenario datasets inside protocol docs.
6. Do not mutate `IDENTITY_PROMPT.md` directly as the learning surface.
7. Do not reopen `v1.6.15` direct-tool admission semantics or `v1.6.16` continuity semantics.
8. Do not create a backward-compatibility or fallback bridge for lagging packs.

## 4) Current landed state and remaining open state

1. `ISSUE-030` is closed: the strengthened third/fourth-loop center is now protocol-owned, machine-gated, and consumed by required/readiness lanes.
2. `ISSUE-031` remains open: the 4→1 loopback bridge is intentionally kept docs-owned until a dedicated machine consumer lane lands.
3. Therefore the stream as a whole remains active, but the remaining open surface is narrow and explicitly bounded.

## 5) Stream closure boundary

`v1.6.17` is not reopened by residual live-quality misses once the strengthened surfaces are present and healthy. The stream closes when all of the following are true:

1. `ASB16-RQ-048` remains machine-landed and consumed on the success path;
2. `ASB16-RQ-049` remains machine-landed and consumed on the success path;
3. `ASB16-RQ-050` gains a dedicated machine consumer lane without collapsing loopback artifacts into first-loop truth;
4. the same lane proves the bounded closed-loop topology (`third-loop exploration -> fourth-loop promotion -> first-loop revalidation`) as a machine-auditable round trip with explicit demotion / rollback on first-loop conflict;
5. audit can attribute residual live-quality misses below protocol by default unless the `v1.6.17` surfaces are absent, skipped, or semantically broken.

### 6.1 Opening binding reference freeze (ASB16-RQ-048 ASB16-RQ-049, 2026-03-23)

The canonical strengthening pair is frozen as follows:

1. `ASB16-RQ-048`
   - kernel contract: `route_discovery_convergence_contract_v1`
   - shared primitive: `roundtable_four_track_cross_validation_contract_v1`
   - required machine-visible family includes at least:
     - `route_discovery_convergence_status`
     - `route_discovery_enforcement`
     - `selected_candidate_id`
     - `selection_basis`
     - `convergence_status`
     - `parallel_probe_allowed`
     - `four_track_cross_validation_required`
     - `roundtable_track_status`
     - `vendor_track_status`
     - `reference_track_status`
     - `runtime_probe_status`
2. `ASB16-RQ-049`
   - kernel contract: `feedback_operational_prompt_contract_v1`
   - shared primitive: `roundtable_four_track_cross_validation_contract_v1`
   - required machine-visible family includes at least:
     - `feedback_operational_prompt_status`
     - `feedback_operational_prompt_enforcement`
     - `rulebook_delta`
     - `prompt_injection_status`
     - `replay_status`
     - `four_track_cross_validation_required`
     - `roundtable_track_status`
     - `vendor_track_status`
     - `reference_track_status`
     - `runtime_probe_status`
     - `loop_back_to_first_loop_status`
3. The fourth-loop center continues to govern the wider evidence family frozen in §2.3, especially `feedback_summary_ref`, `operational_prompt_ref`, `operational_prompt_digest`, `prompt_scope`, `prompt_target_route`, `prompt_target_stage`, `rollback_prompt_ref`, and `ttl_rounds`; §6.1 names the minimum opening projection expected on shared machine-visible surfaces.
4. The strengthening pair is frozen as generic protocol infrastructure only; no business-specific routing policy or prompt content is canonicalized here.

### 6.2 Opening semantic freeze (ASB16-RQ-050, 2026-03-23)

The standalone 4→1 bridge is frozen as follows:

1. `ASB16-RQ-050`
   - kernel contract: `feedback_to_judgement_loopback_contract_v1`
   - shared primitive consumed by context, but not replaced by it: `roundtable_four_track_cross_validation_contract_v1`
   - canonical machine-visible loopback family includes at least:
     - `loopback_artifact_ref`
     - `loopback_artifact_kind`
     - `preflight_context_injection_ref`
     - `loopback_scope`
     - `loopback_ttl_rounds`
     - `first_loop_revalidation_required`
     - `judgement_reentry_status`
     - `adoption_decision`
     - `conflict_with_current_evidence`
     - `demotion_or_rollback_action`
     - `negative_feedback_ref`
2. The bridge is considered healthy only when prior fourth-loop artifacts can be accepted, demoted, or rolled back under current first-loop evidence without narrative ambiguity.
3. Loopback artifacts remain governed preflight aids only, never current-round truth.
4. First-loop revalidation remains authoritative, and no future machine consumer may weaken that rule.
