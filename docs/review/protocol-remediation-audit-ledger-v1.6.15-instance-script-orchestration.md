# Protocol Remediation Audit Ledger (v1.6.15 instance-script orchestration stream)

Status: Active (baseline shared validator/probe/consumer closure, including execution-lane admission governance, plus minimal non-empty orchestration-family cross-pack proof verified, 2026-03-22; topology-clean live proof and broader adoption rollout remain open)  
Scope: protocol review ledger for route -> instance-script declarative join, route -> execution-lane admission, pack-local script manifest governance, and instance-script receipt-family modeling

## 0) Stream objective

1. Freeze the canonical route-to-script additive fields under `CURRENT_TASK.json`.
2. Freeze the canonical pack-local script manifest path under pack-root `scripts/`.
3. Freeze the lower-capability join model that connects instance scripts to skills, MCP servers, and tool pipelines.
4. Freeze the canonical receipt-family interpretation for governed instance-script execution.
5. Freeze the route-level execution-lane admission contract needed to fail-close undeclared manual/editor/webhook fallback.

## 1) Problem statement frozen for audit

1. `v1.6.13` made pack-root `scripts/` canonical, and `v1.6.14` made identity-bound launcher/startup governance explicit, but neither stream froze how governed routes bind to pack-local scripts.
2. Without a dedicated orchestration stream, teams can still drift into:
   - filename-based script discovery,
   - undocumented route-to-script pairing,
   - lower-capability dependencies declared only in human prose,
   - per-pack receipt conventions that do not compose.
3. That ambiguity encourages recurring misdiagnosis between:
   - protocol orchestration debt,
   - instance migration debt,
   - lower capability availability failures,
   - runtime dirt,
   - outer-delivery gaps.
4. The stream exists to freeze the orchestration join without reopening topology, launcher, bootstrap, or relay semantics.

## 2) Ownership boundary frozen in this stream

### 2.1 Protocol-owned surfaces

1. `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
2. `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
3. `identity/protocol/mappings/stream-doc-registry.v1.6.yaml`
4. `identity/protocol/mappings/stream-scope-matrix.v1.6.yaml`
5. `identity/protocol/mappings/doc-evidence-allowlist.v1.6.2.yaml`
6. `identity/protocol/IDENTITY_PROTOCOL.md`
7. `identity/protocol/IDENTITY_RUNTIME.md`
8. `identity/protocol/mappings/control-plane-status.current.yaml`
9. `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md`
10. Landed implementation surfaces for this stream now include:
   - `scripts/validate_identity_instance_script_orchestration.py`
   - `scripts/validate_instance_script_manifest.py`
   - `scripts/validate_route_script_receipt_join.py`
   - `scripts/validate_route_execution_lane_admission.py`
   - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - `scripts/release_readiness_check.py`
   - `scripts/validate_identity_capability_activation.py`
   - `scripts/validate_identity_instance_script_cross_pack_adoption.py`
   - `scripts/create_identity_pack.py`
   - `scripts/repair_contract_backfill.py`
   - `scripts/identity_creator.py`
11. Remaining follow-on implementation obligations are:
   - roll the same shared family through target-pack adoption without topology drift
   - keep future receipt-family specializations inside the same validator/probe/control path
12. Shared stream-doc-registry current-pointer consumption for the touched validator family is now expected to flow through one protocol-owned helper plus one invariant guard rather than per-script literal defaults.

### 2.2 Workspace / instance-owned surfaces consumed by this stream

1. `CURRENT_TASK.json` route entries under `capability_orchestration_contract.task_type_routes`.
2. Pack-local manifest destination under `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`.
3. Pack-root `scripts/` executable sources inherited from `v1.6.13`.
4. Lower-capability dependencies already expressed as `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
5. Runtime receipt/report destinations under governed `runtime/` subtrees.

## 3) Four-track review checklist

### 3.1 T1 roundtable / internal topology

1. Reuse `docs/governance/roundtable-multi-agent-multi-identity-binding-governance-v1.4.12.md` for explicit identity binding and runtime-isolation baseline.
2. Reuse `identity/protocol/AGENT_HANDOFF_CONTRACT.md` for identity/skill/MCP-tool layer attribution and structured failure ownership.
3. Confirm that route-to-script governance does not create a hidden ambient arbitration layer.

### 3.2 T2 vendor / OpenAI Codex evidence

1. Confirm that Codex startup guidance and config surfaces remain startup-scoped rather than late-turn orchestration patches.
2. Confirm that `model_instructions_file`, `project_doc_fallback_filenames`, and `mcp_servers.<id>.command` are real Codex concepts.
3. Keep launcher/startup semantics (`v1.6.14`) separate from route/script orchestration semantics (`v1.6.15`).
4. Canonical vendor anchors:
   - `https://developers.openai.com/codex/config-reference/#configtoml`
   - `https://developers.openai.com/codex/guides/agents-md/#how-codex-discovers-guidance`

### 3.3 T3 Context7 / MCP / reference boundary

1. Confirm that MCP initialization negotiates readiness and capabilities before normal operations.
2. Confirm that MCP servers expose `tools`, `resources`, and `prompts` as lower capability primitives.
3. Keep route/script orchestration above MCP rather than collapsing the two layers.
4. Canonical reference family:
   - Context7 library id `/modelcontextprotocol/modelcontextprotocol`
   - MCP initialize lifecycle and capability declaration materials
   - `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

### 3.4 T4 protocol / inherited-stream references

1. Reuse `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md` for pack-root `scripts/` ownership.
2. Reuse `docs/governance/identity-codex-launcher-governance-v1.6.14.md` for launcher/startup ownership.
3. Reuse `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md` for bootstrap tuple semantics.
4. Reuse `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md` and `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md` as inherited review baselines.
5. Treat `docs/governance/identity-instance-script-orchestration-roadmap-2026-03-21.md` as pre-freeze design record only; this stream is the active owner.

## 4) Frozen implementation checklist

1. Canonical route fields are:
   - `primary_instance_scripts`
   - `fallback_instance_scripts`
   - `script_preconditions`
   - `script_receipt_pattern`
   - `allowed_execution_lanes`
   - `lane_admission_policy`
   - `lane_receipt_pattern`
   - `lane_block_on_fallback`
2. A single route may bind multiple role-distinct `script_id` values when execution legitimately separates probe/render/emit/recovery stages.
3. Canonical script catalog file is `<pack_path>/scripts/INSTANCE_SCRIPT_MANIFEST.json`.
4. Manifest entries resolve only to pack-local paths under `scripts/`.
5. Lower dependencies remain explicit through `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
6. `allowed_execution_lanes` rows stay machine-readable and freeze `lane_id`, `lane_class`, `lane_source`, and `endpoint_class`.
7. `lane_admission_policy` and `lane_block_on_fallback` are the only canonical route-level controls for fail-closing undeclared lane fallback; operator memory is never an authority surface.
8. Canonical admission receipt family is `instance_script_admission_receipt`; it must keep `lane_id`, `lane_class`, `lane_source`, `lane_endpoint_class`, `lane_admission_status`, and `fallback_used` machine-visible.
9. Lower dependencies remain explicit through `primary_skills`, `fallback_skills`, `required_mcp`, and governed tool-route fields.
10. `script_preconditions.required_contracts` and `script_preconditions.gate_policies` may reference inherited gateway/headstamp/host-visible/relay contracts, but that does not transfer ownership of those contracts into this stream.
11. Receipt families stay runtime-owned and classify at least:
   - `instance_script_admission_receipt`
   - execution,
   - emit,
   - recovery.
12. Route/script join must never rely on operator memory, workspace-global shared helper directories, or filename guessing.
13. Route-scoped capability admission must be evaluable without blocking a route on lower dependencies that it does not itself declare unless a stronger activation policy explicitly says otherwise.
14. Receipt outputs must preserve machine-readable route provenance compatible with `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts`.
15. Reviewers may accept layered receipt mapping where probe/helper scripts satisfy execution receipts first, admission receipts freeze lane selection, and emitter scripts later satisfy emit receipts plus delegated refs to inherited host-visible or relay receipts.
16. Any governed user-visible final output route must bind to a pack-local emitter script and declare an emit-family receipt before outer relay or visible-surface handling is considered valid evidence.

## 5) Audit verdict rules (frozen)

1. **Policy PASS** for this stream requires:
   - governance doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - review doc registered in `identity/protocol/mappings/stream-doc-registry.current.yaml`,
   - scope-matrix row present in `identity/protocol/mappings/stream-scope-matrix.current.yaml`,
   - allowlist rows present in `identity/protocol/mappings/doc-evidence-allowlist.current.yaml`,
   - audit index discoverability updated in `docs/governance/AUDIT_SNAPSHOT_INDEX.md`.
2. **Architecture PASS** for this stream requires:
   - route/script binding fields are frozen,
   - route/execution-lane admission fields are frozen,
   - multi-role route-to-script binding semantics are frozen,
   - execution-lane admission semantics are frozen,
   - manifest path is frozen,
   - lower capability join is frozen,
   - inherited precondition reference semantics are frozen,
   - route-scoped capability-attribution rules are frozen,
   - receipt-family interpretation is frozen,
   - receipt-provenance projection expectations are frozen,
   - reviewer failure-attribution order is explicit.
3. **Implementation PASS** for this stream is not satisfied by documentation alone. The following implementation pieces are now landed:
   - protocol-owned manifest, route/script, route/script-to-receipt, and route/execution-lane validators,
   - positive and negative probes through `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`,
   - readiness wiring through `scripts/release_readiness_check.py`,
   - capability-activation awareness of instance scripts through `scripts/validate_identity_capability_activation.py`,
   - shared create/backfill/update consumer rollout through `scripts/create_identity_pack.py`, `scripts/repair_contract_backfill.py`, and `scripts/identity_creator.py`.
4. Full **Implementation PASS** still requires:
   - route-scoped activation behavior that does not union-block unrelated routes unless an explicit stronger policy is selected,
   - proof-pack adoption without topology drift across target identities,
   - proof-pack adoption of execution-lane admission fields where external/manual/editor/webhook fallback risk exists,
   - lane-admission receipts that keep `lane_id`, `lane_class`, `lane_source`, `lane_endpoint_class`, `lane_admission_status`, and `fallback_used` machine-visible under live pack execution,
   - receipt-provenance projection that keeps `route_selected`, `skills_used`, `mcp_tools_used`, `actions_taken`, `result`, and `artifacts` machine-visible under live pack execution,
   - future receipt-family specializations, when needed, stay on the same shared validator/probe/control path instead of forking it.
5. Reviewers must not collapse `Architecture PASS` into `Implementation PASS`.
6. **Diagnostic Attribution PASS** requires reviewers to classify failures in this order:
   - `route_contract_missing`: one or more of `primary_instance_scripts`, `fallback_instance_scripts`, `script_preconditions`, or `script_receipt_pattern` is absent, contradictory, or unresolved in `CURRENT_TASK.json`.
   - `manifest_binding_missing`: route fields are present, but `scripts/INSTANCE_SCRIPT_MANIFEST.json` has no matching entry or resolves outside pack-root `scripts/`.
   - `script_precondition_blocked`: route and manifest are valid, but `script_preconditions` are unsatisfied before execution starts.
   - `lane_admission_mismatch`: route/script surfaces are valid, but the selected execution lane is undeclared, fallback is blocked, or the admission receipt does not prove the declared lane.
   - `mcp_capability_unavailable`: route/manifest/preconditions are valid, but a declared `required_mcp` server fails readiness for the required primitive.
   - `tool_pipeline_failure`: declared lower-capability surfaces are ready, but the governed tool pipeline fails during execution.
   - `script_receipt_mismatch`: execution returns, but runtime receipts do not satisfy `script_receipt_pattern`.
   - `outer_delivery_gap`: route/script/receipt checks pass, but governed host-visible delivery still fails later.

## 6) Accepted closure boundary

1. `v1.6.15` is closed at the contract-freeze level when the route/script/dependency/receipt/execution-lane model is frozen in protocol docs and mappings.
2. Baseline implementation closure for this stream is now satisfied because the landed shared validator/probe/consumer family has non-empty orchestration-family cross-pack reuse proof instead of chat-only adoption claims.
3. Current-state note (2026-03-22):
   - `python3 scripts/validate_identity_instance_script_cross_pack_adoption.py --catalog .identity/catalog.local.yaml --json-only`
   - observed `PASS_REQUIRED` with `eligible_identity_count=2`, `checked_identity_count=2`, and `adoption_ready_identity_count=2`
   - the same payload now projects topology hygiene explicitly through `topology_clean_adoption_ready_count` and `topology_interlock_violation_rows`
   - current orchestration-family proof packs: `custom-creative-ecom-analyst`, `base-repo-closure-orchestrator`
   - `python3 scripts/validate_identity_instance_script_cross_pack_adoption.py --catalog .identity/catalog.local.yaml --proof-boundary topology_clean --json-only`
   - current live outcome is not yet satisfied because `custom-creative-ecom-analyst` still fails inherited `v1.6.13` topology hygiene
   - `bash scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh` now proves positive topology-clean cross-pack replay plus negative topology-interlock fail-close on a synthetic multi-pack catalog
4. Broader rollout breadth and topology-clean live proof remain open until wider target-pack evidence confirms the same shared family continues to hold without topology drift.
5. Instance packs may already be able to self-organize around pack-root `scripts/`, but chat evidence alone does not promote a private local pattern into protocol motherline.
6. This stream remains independent from provider runtime incidents, launcher install incidents, and host-visible final-surface auto-binding work.
7. A pack may be `topology-ready` and `exit-ready` yet still be pre-adoption for `v1.6.15` until manifest and additive route fields land; that migration state must not be misreported as a reopen of inherited streams.
8. Even before host auto-binding is solved, `v1.6.15` may require the governed producer for final user-visible text to be a route-bound emitter script instead of direct free-form assistant delivery.

## 7) Follow-on reinforcement mapping (non-reopen, architect-owned)

1. `RF-ORCH-001 aggregate_route_scope_cardinality_projection`
   - current judgment: landed shared builders/validators now freeze aggregate capability-activation artifacts as multi-route summaries rather than route-scoped receipts, so the protocol-owned requirement is explicit scope/cardinality projection instead of any synthetic `route_selected`.
   - target protocol surfaces:
     - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
     - `scripts/instance_script_orchestration_common.py`
     - `scripts/validate_identity_capability_activation.py`
     - `scripts/validate_route_script_receipt_join.py`
     - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - audit acceptance:
     - aggregate artifacts now reuse one canonical field family: `route_scope`, `route_scope_mode`, `route_activation_strategy`, `route_ready_count`, `route_total_count`, `route_ids`, and `route_selection_cardinality`,
     - route-scoped receipts remain strict on `route_selected` and project `route_scope_mode=route_receipt` plus `route_ids=[route_selected]`,
     - validator/probe coverage fail-closes when a single-route artifact omits route provenance or when an aggregate artifact drifts into parallel alias vocabulary.
2. `RF-ORCH-002 declared_vs_observed_dependency_projection`
   - current judgment: landed shared builders/validators now standardize one declared-vs-observed dependency projection across route-scoped and aggregate artifacts instead of leaving the diff fragmented across report families.
   - target protocol surfaces:
     - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
     - `scripts/instance_script_orchestration_common.py`
     - `scripts/validate_route_script_receipt_join.py`
     - `scripts/validate_identity_capability_activation.py`
     - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
   - audit acceptance:
     - declared dependencies, observed activations/executions, and gap reasons are machine-visible through `declared_dependency_projection`, `observed_dependency_projection`, `dependency_gap_reasons`, `undeclared_usage_*`, and `missing_declared_dependency_*`,
     - undeclared observed usage and missing declared dependency are surfaced through one governed gap model rather than per-artifact narrative-only wording,
     - the same field family is reused across route-scoped and aggregate artifacts where applicable, with no parallel business- or pack-specific dependency dialect.
3. `RF-ORCH-003 semantic_anchor_extension_hook`
   - current judgment: downstream semantic narrowing can happen even when route/script orchestration remains correct, so the missing control is a governed anchor envelope rather than protocol-owned business scoring.
   - target protocol surfaces:
     - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
     - `scripts/instance_script_orchestration_common.py`
     - `scripts/validate_route_script_receipt_join.py`
     - `scripts/validate_identity_capability_activation.py`
     - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
     - pack-generation/backfill flows only if the anchor envelope becomes canonical
   - audit acceptance:
     - anchor ref/schema/source/revision/digest/status remain machine-visible,
     - downstream consumers cannot silently drop a declared anchor without a governed mismatch signal,
     - partial anchor families fail closed once any anchor field is emitted,
     - aggregate promotion occurs only under single-family, non-ambiguous projection across contributing route rows,
     - no domain-specific business fields become core protocol SSOT.
4. `RF-ORCH-004 outcome_sentinel_reference_hook`
   - current judgment: downstream risk signals should be referenceable without promoting business KPIs into core orchestration semantics.
   - target protocol surfaces:
     - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
     - `scripts/instance_script_orchestration_common.py`
     - `scripts/validate_route_script_receipt_join.py`
     - `scripts/validate_identity_capability_activation.py`
     - `scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh`
     - release/audit consumers only if a stream explicitly freezes sentinel gating
   - audit acceptance:
     - sentinel hook remains optional, schema-bound, and machine-visible when present,
     - partial sentinel families fail closed once any sentinel field is emitted,
     - aggregate promotion occurs only under single-family, non-ambiguous projection across contributing route rows,
     - advisory vs fail-close semantics are explicit,
     - protocol does not absorb instance-specific scoring thresholds as universal contract.
5. `RF-ORCH-005 role_boundary_non_substitution_matrix`
   - current judgment: the stream already states that instance scripts do not replace skills, MCP servers, or tools, but review can still drift unless the four-role matrix and non-substitution rule are frozen as an explicit canonical clause.
   - target protocol surfaces:
     - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
     - `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
   - audit acceptance:
     - the agent/codex, identity instance/scripts, skills/scripts, and MCP/tool roles are explicitly separated,
     - reviewer wording classifies “identity instance/scripts must replace skill business scripts” as semantic misuse rather than protocol defect,
     - the reinforcement does not create a fake new machine gate or reopen inherited streams.

## 8) Boundary lock for reviewers

1. Do not reinterpret this stream as permission to add new pack-root directories or revive `runtime/scripts/`.
2. Do not reinterpret this stream as permission to override launcher or bootstrap ownership already frozen by `v1.6.14` and `v1.6.12`.
3. Do not classify lower-capability outages as proof that route/script orchestration semantics are wrong.
4. Do not accept user-specific absolute paths, shared workspace helper dropzones, or per-pack hardcoded receipts as canonical answers.
5. Do not reopen `v1.6.13` or `v1.6.14` while reviewing this stream; `v1.6.15` exists specifically to keep those layers separate.
6. Do not classify route blocks caused only by undeclared lower dependencies as proof that the route/script contract failed; first verify whether the route actually declared those skills, MCP servers, or tool constraints.
7. Do not accept receipt families that drop `route_selected` / `skills_used` / `mcp_tools_used` provenance and then compensate with narrative-only explanation.
8. Do not demand that `identity instance/scripts` replace skill/business script libraries; that request is a role-boundary semantic misuse for this stream, not a protocol-owned completeness target.

## 9) 2026-03-21 machine-verified protocol landing snapshot

1. Runtime truth was rechecked through the protocol resolver before interpreting this stream:
   - `python3 scripts/resolve_identity_context.py resolve --identity-id base-repo-architect`
   - expected outcome observed: `source_layer=project` with project-local catalog / pack resolution.
2. The new route-to-execution-lane protocol gate is landed as a first-class validator surface:
   - `python3 scripts/validate_route_execution_lane_admission.py --help` resolves successfully
   - `bash scripts/ci/run_identity_instance_script_orchestration_probes_ci.sh` returns `identity_instance_script_orchestration_probe_status=PASS_REQUIRED`
   - the same probe now proves lane-specific positive / negative coverage:
     - `positive_execution_lane_status=PASS_REQUIRED`
     - `negative_lane_contract_failure=missing_field:lane_receipt_pattern`
     - `negative_lane_receipt_failure=lane_receipt_lane_id_undeclared`
3. Shared consumers now see the same execution-lane contract family instead of route/script-only semantics:
   - `python3 scripts/validate_identity_capability_activation.py --identity-id base-repo-closure-orchestrator --catalog ../.identity/catalog.local.yaml --activation-policy route-any-ready`
   - observed outcome: `capability_activation_status=ACTIVATED`
   - the payload now exposes `route_execution_lane_rows`, route-level `execution_lane_*` fields, and reserves `IP-CAP-006` for lane-governance closure failures.
4. The inherited host-gateway generator/control plane now fail-closes the final-channel relay branch instead of trusting static template freshness alone:
   - `scripts/create_identity_pack.py` now freezes final-relay constants/helpers into the generated session-chain wrapper and extends the wrapper-template attestation with `session_chain_executable_smoke_policy`
   - `scripts/validate_protocol_unique_entry_gate.py` now executes that smoke against the generated final-channel branch and projects `protocol_host_gateway_session_chain_executable_smoke_status`
   - the positive protocol probe suite keeps the smoke green on canonical generated wrappers, while the negative wrapper-mutation probe now proves that executable-smoke regressions fail closed
   - a live inherited pack that still carries the broken canonical wrapper now surfaces `protocol_host_gateway_session_chain_semantic_status=FAIL_REQUIRED` together with `protocol_host_gateway_session_chain_executable_smoke_status=FAIL_REQUIRED` instead of hiding behind template-latest PASS
5. Governed final emit now repairs stale host-visible post-check blockers instead of treating inherited closure-state drift as a permanent first-line gate failure:
   - `scripts/final_emit_governed.py` now retries through `scripts/recover_host_visible_post_check_state.py` when the governed final outlet fails in the pre-first-line post-check blocker/state-unavailable branch
   - `scripts/ci/run_gateway_wrapper_trust_boundary_probes_ci.sh` now seeds a synthetic `host_visible_surface_live_closure_state.json` blocker and proves under protocol-root invocation that the session-chain wrapper returns to `PASS_REQUIRED`
   - this keeps stale host-visible closure state in the runtime-repair bucket instead of misclassifying it as a new route/script orchestration regression
6. Protocol hygiene and inherited motherline checks remain green after the upgrade:
   - `python3 scripts/docs_command_contract_check.py` -> `docs checked: 79`, `command snippets checked: 860`, `PASS`
   - `python3 scripts/validate_native_chat_bootstrap_entry_stream.py --json-only` -> `status=PASS_REQUIRED`, `standard_closure_status=CLOSED`, `promotion_status=PROMOTION_REVIEW_ELIGIBLE`
7. The stream-doc-registry current-pointer lane is also now single-sourced for the touched validator family, and control-plane invariants fail close if the literal current pointer resurfaces outside the shared helper.
8. This snapshot closes the protocol-owned execution-lane governance gap for `v1.6.15`, but it does not claim repo-wide clean freeze, whole-repo worktree cleanliness beyond the touched lane, active-fleet migration proof in inherited motherlines, or cross-pack adoption closure.
