# Identity Onboarding 72h Playbook Template

Status: discussion template (safe to tailor per identity)
Primary layer: instance
Protocol guardrails source: canonical SSOT handoff (protocol layer)
SSOT execution rule: execute protocol decisions only from `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`; external artifacts are evidence mirrors, not normative sources.

Normative boundary (must keep):

1. Identity instance must deeply analyze business details to improve domain expertise.
2. Protocol governance records must not store non-redacted business details.
3. Protocol governance records must not inline unredacted business details.
4. Business details must be mapped by `domain_artifact_refs` references.
5. Business details must be preserved in instance knowledge artifacts and linked from governance records via references.

---

## 0) Metadata

- Identity ID:
- Owner:
- Start time (UTC):
- Target finish time (UTC):
- Repo branch:
- Catalog used:
- Scope used:
- Runtime mode:

---

## 1) Scope and layer declaration (mandatory)

### 1.1 This playbook controls

1. Instance onboarding execution and evidence closure within 72 hours.
2. Instance-plane and repo-plane reporting for the target identity.
3. Recoverable blocked handling (fail-operational) for instance iteration.

### 1.2 This playbook does NOT control

1. Protocol-gate schema redesign.
2. Release-plane cloud closure declaration.
3. Business-domain strategy expansion unrelated to onboarding baseline.

### 1.3 A/B track declaration

- A-track (protocol): only if protocol-core files are changed.
- B-track (instance): identity pack/catalog/runtime evidence changes.
- If both tracks exist, must submit separate review packages.

### 1.4 Dual-ledger declaration (mandatory)

- Governance ledger (this playbook): capability-upgrade facts, machine-checkable fields, and evidence references only.
- Domain knowledge ledger (instance runtime): business details, domain hypotheses, and outcome analysis.
- Cross-ledger rule: governance entries must reference domain artifacts through `domain_artifact_refs`, not inline business details.
- Cross-ledger rule (hard): protocol records cannot carry raw business payloads; use reference-only pointers.

---

## 2) Mandatory boundary checks before execution

Fill these fields before any onboarding command:

- Identity context tuple (resolve output):
  - source_layer:
  - catalog_path:
  - pack_path:
  - resolved_scope:
- Single-active state precheck result:
- Session pointer consistency precheck result:
- Runtime writeability precheck result:
- Roundtable readiness precheck result (roles/inputs/scope frozen):

If tuple mismatch or path/scope drift exists, stop and fix first.

---

## 3) 72-hour execution phases

## Phase 1 (T+0h ~ T+8h): bootstrap and boundary lock

Objective:

1. Create/prepare identity pack baseline.
2. Bind correct catalog + scope + runtime mode.
3. Ensure no cross-identity fallback and no path contamination.

Execution notes:

- Commands executed:
- Reports generated:
- Blocking issues:
- Repairs applied:

Exit criteria:

- Bootstrap baseline exists.
- Identity tuple resolved deterministically.
- Boundary prechecks pass.

## Phase 2 (T+8h ~ T+24h): minimum runnable closure

Objective:

1. Pass runtime contract, role binding, prompt quality baseline.
2. Produce first structured update report.
3. Ensure failure-path reports are field-complete.

Execution notes:

- Commands executed:
- Reports generated:
- Blocking issues:
- Repairs applied:

Exit criteria:

- Required local validators pass.
- Structured report contains mandatory fields and next_action.

## Phase 3 (T+24h ~ T+48h): capability activation closure

Objective:

1. Verify skill / MCP / tool route activation evidence.
2. Confirm no false-green on auth-required dependencies.
3. Record activation policy used (strict-union or route-any-ready).

Execution notes:

- Commands executed:
- Reports generated:
- Blocking issues:
- Repairs applied:

Exit criteria:

- Capability activation status is auditable.
- skills_used / mcp_tools_used / tool_calls_used evidence is present.

## Phase 4 (T+48h ~ T+72h): regression and handoff package

Objective:

1. Run e2e / readiness / three-plane regression.
2. Produce fixed-format handoff to architect + audit expert.
3. Classify residual risks with next milestone.

Execution notes:

- Commands executed:
- Reports generated:
- Blocking issues:
- Repairs applied:

Exit criteria:

- Instance status can be conclusively reported.
- Layer-separated handoff package is complete.

---

## 4) Skill protocol attachment block (mandatory)

Fill before concluding onboarding:

- selected_skills:
- skill_trigger_basis:
- update_chain_status:
  - trigger:
  - patch:
  - validate:
  - replay:
- creator_plane_changes:
- installer_plane_distribution:

Rules:

1. `selected_skills` must list only actually activated skills in this run window.
2. `skill_trigger_basis` must reference explicit trigger evidence (command/report id), not free-form claim.
3. `update_chain_status(trigger/patch/validate/replay)` must be fully populated and machine-checkable.
4. `creator_plane_changes` and `installer_plane_distribution` must be layer-tagged (`protocol` or `instance`).

---

## 4.1 Tool discovery and installation closure (mandatory when `capability_gap` includes tool/runtime gaps)

Purpose:

1. Keep identity self-drive capable of discovering and adopting new tools under controlled governance.
2. Separate "can use existing tools" from "can drive installation of new tools" with auditable steps.

Fields:

- tool_gap_detected: yes/no
- tool_gap_summary_ref:
- install_plan_ref:
- approval_receipt_ref:
- execution_log_ref:
- installed_artifact_ref:
- installed_version:
- post_install_healthcheck_ref:
- task_smoke_result_ref:
- route_binding_update_ref:
- fallback_route_if_install_fails:
- rollback_ref:

Rules:

1. If `tool_gap_detected=yes`, `install_plan_ref` and `approval_receipt_ref` are mandatory before execute stage.
2. Installation outcome is valid only when healthcheck and task smoke evidence both exist.
3. Install failure must not deadlock task flow; `fallback_route_if_install_fails` is mandatory.
4. Protocol templates define fields only; implementation details stay in scripts/workflow wiring.

## 4.2 New-object discovery trust closure (mandatory when introducing new `skill`/`mcp_server`/`tool_runtime`)

Purpose:

1. Prevent weak-source discovery from polluting protocol execution.
2. Force trusted-source selection before attach/install.
3. Keep discovery and installation decisions replayable and auditable.

Fields:

- object_type: `skill | mcp_server | tool_runtime`
- object_name:
- discovery_trigger_ref:
- selected_source_ref:
- source_selection_rationale:
- trust_verification_refs:
- attach_or_install_plan_ref:
- approval_receipt_ref:
- execution_log_ref:
- post_attach_validator_refs:
- fallback_route_ref:
- rollback_ref:

Discovery source matrix (fill at least one row per candidate source):

| object_type | source_url | source_kind (`official_doc`/`official_registry`/`official_repo`/`community_repo`) | trust_tier (`T0`/`T1`/`T2`) | provenance_or_signature_ref | decision (`selected`/`rejected`) | rejection_reason |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Rules:

1. Any `selected` source must include `trust_tier` and `trust_verification_refs`.
2. `T2` sources (community) require explicit `approval_receipt_ref` before execution.
3. `tool_runtime` installation must include provenance/hash/signature evidence, otherwise cannot transition to active route.
4. `mcp_server` onboarding must record tool scoping (`allowed_tools`) and approval policy (`require_approval`) in `attach_or_install_plan_ref`.
5. Missing `fallback_route_ref` blocks completion for object onboarding.

---

## 4.3 Vendor and API interface discovery closure (mandatory when introducing or upgrading vendor integrations)

Purpose:

1. Ensure vendor/API selection is based on official, machine-readable contracts before changing execution scripts.
2. Prevent hardcoded endpoint-driven integrations without provenance, auth, and version governance.
3. Keep vendor/API attach decisions reproducible, reviewable, and reversible.

Fields:

- vendor_name:
- vendor_surface_name:
- api_surface_type: `rest | graphql | rpc | mcp | webhook | mixed`
- official_reference_url:
- machine_readable_contract_ref:
- contract_kind: `openapi | graphql_schema | odata_metadata | mcp_tool_list | other`
- auth_discovery_ref:
- versioning_policy_ref:
- rate_limit_policy_ref:
- deprecation_policy_ref:
- sandbox_or_test_env_ref:
- sdk_reference_ref:
- capability_probe_command_ref:
- attach_readiness_decision: `ready | defer | blocked`
- fallback_vendor_or_route_ref:
- rejection_reason:

Vendor/API candidate matrix (fill at least one row per candidate):

| vendor_name | vendor_surface_name | official_doc_url | contract_kind (`openapi`/`graphql_schema`/`odata_metadata`/`mcp_tool_list`/`other`) | machine_readable_contract_ref | auth_model_ref | rate_limit_ref | decision (`selected`/`rejected`) | rejection_reason |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

Rules:

1. Any `selected` candidate must include both `official_doc_url` and `machine_readable_contract_ref`.
2. Source priority must follow: `official vendor source` -> `standards body source` -> `community mirror/wrapper`.
3. Community-only candidates cannot become active route without explicit exception approval and fallback route evidence.
4. Protocol templates must not hardcode vendor endpoints; endpoint values live in runtime/config artifacts referenced by `*_ref` fields.
5. Vendor/API selection must include a successful capability probe and rollback/fallback evidence.

---

## 4.4 Vendor/API solution closure (mandatory after discovery selection)

Purpose:

1. Convert vendor/API discovery outputs into an executable integration solution instead of direct script patching.
2. Make architectural tradeoffs explicit and auditable before route activation.
3. Bind solution choice to rollback and ownership boundaries.

Fields:

- problem_statement_ref:
- selected_vendor_api_ref:
- solution_pattern: `direct_api | official_sdk_adapter | managed_connector | mcp_bridge | hybrid`
- decision_rationale_ref:
- option_comparison_ref:
- security_boundary_ref:
- auth_scope_strategy_ref:
- rate_limit_strategy_ref:
- change_management_ref:
- fallback_solution_ref:
- rollback_solution_ref:
- owner_layer_declaration_ref:

Solution option matrix:

| option_id | solution_pattern (`direct_api`/`official_sdk_adapter`/`managed_connector`/`mcp_bridge`/`hybrid`) | expected_capability_gain | implementation_complexity (`low`/`medium`/`high`) | governance_risk (`low`/`medium`/`high`) | selected (`yes`/`no`) | rejection_reason |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Rules:

1. Exactly one option must be marked `selected=yes` for each onboarding decision.
2. Selected option must include `security_boundary_ref`, `auth_scope_strategy_ref`, and `rate_limit_strategy_ref`.
3. Selected option must include both fallback and rollback solution references.
4. `owner_layer_declaration_ref` must explicitly separate protocol-layer governance from instance-layer execution.
5. If no option is acceptable, run state must remain `defer` or `blocked`; no silent default route.

---

## 5) Multimodal fact-input role contract (mandatory)

Core semantics (must keep):

1. Multimodal inputs are fact-input layer inputs, not display-only attachment defaults.
2. Attachments are allowed, but default role is `DISPLAY_ONLY`.
3. Non-gated attachments cannot support final claims.
4. Critical gate failure must downgrade run state to `manual_review` or `blocked`.
5. Thresholds are instance-config referenced and must not be hardcoded into protocol templates.

Evidence role fields:

- evidence_role: `DISPLAY_ONLY | FACT_INPUT`
- role_transition_state:
- role_transition_gate_refs:
- final_claim_evidence_refs:

Role transition hard rules:

1. Default on ingest: `DISPLAY_ONLY`.
2. Only when mandatory gates pass can role transition to `FACT_INPUT`.
3. `DISPLAY_ONLY` evidence cannot support final claim.
4. `inconsistent evidence cannot transition to done`.

---

## 6) Roundtable intelligence and cross-validation (mandatory for complex upgrades)

Trigger rule:

1. Required when upgrade affects any of: `skill_routing`, `mcp_binding`, `tool_routing`, `vendor_api_discovery`, `solution_architecture`, `validator_chain`, `path_boundary`.
2. Optional for isolated low-risk edits, but skip reason must be explicitly recorded.

Roundtable output fields:

- discussion_topic:
- participants_role_set:
- decision_matrix_ref:
- disputed_items:
- final_decision_ref:
- unresolved_items_count:

Cross-vendor evidence matrix (fact vs inference separated):

| vendor | source_url | retrieved_at | claim | claim_type (`fact`/`inference`) | mapped_contract_or_validator | risk_note |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Rule:

1. Claims used for final conclusion must include `source_url` and `claim_type`.
2. Final conclusion must map to at least one `fact` row.
3. `inference` claims must include mapped validator/contract basis and explicit risk note.

---

## 7) Completion gates (DoD checklist)

### 7.1 Instance-plane DoD

- [ ] Target identity update report exists.
- [ ] Mandatory report fields are complete.
- [ ] Binding/session/prompt/capability validators pass.
- [ ] e2e target run reaches terminal output with deterministic status.
- [ ] Self-driven upgrade ledger entries are complete (`run_id`, `acceptance_command`, `evidence_ref`).
- [ ] Business details are referenced via `domain_artifact_refs` only (no inline non-redacted details).
- [ ] Skill protocol attachment block fields are complete.
- [ ] Tool discovery/installation closure fields are complete when tool-gap path is triggered.
- [ ] Vendor/API discovery closure fields are complete when vendor or API onboarding path is triggered.
- [ ] Vendor/API solution closure fields are complete and selected-option rules are satisfied.
- [ ] Multimodal evidence-role contract is complete and consistent.
- [ ] `inconsistent evidence cannot transition to done` is respected.

### 7.2 Repo-plane DoD (only when touched)

- [ ] SSOT/coupling/document-contract checks pass.
- [ ] Workspace cleanliness check is clean.
- [ ] No repo-only validator is wired into instance main chain by mistake.

### 7.3 Release-plane note

- [ ] If Full Go is claimed, cloud closure evidence is attached.
- [ ] If cloud closure is missing, final decision remains Conditional Go.

---

## 8) Self-driven upgrade ledger (mandatory)

Purpose:

1. Track every self-driven upgrade event (active or passive).
2. Keep governance records machine-checkable while preserving domain learning continuity.

Record rules:

1. One upgrade event must produce one ledger entry.
2. Each entry must bind `run_id + acceptance_command + evidence_ref`.
3. Governance ledger stores redacted summaries only; domain details belong to referenced domain artifacts.
4. Keep latest 5 entries here; store full details in runtime artifacts.
5. If `result_status != PASS`, `next_action` is mandatory.
6. `upgrade_targets` must enumerate all changed components.

Allowed `trigger_mode`:

- `active`: proactive improvement before failure.
- `passive`: reactive upgrade after failure/blocker/regression.

Allowed `capability_axis`:

- `prompt_contract`
- `skill_routing`
- `mcp_binding`
- `tool_routing`
- `vendor_api_discovery`
- `solution_architecture`
- `validator_chain`
- `workflow_gate`
- `report_contract`
- `session_orchestration`
- `path_boundary`
- `roundtable_intelligence`

| upgrade_id | run_id | ts_utc | trigger_mode | trigger_source | capability_axis | change_surface_ref | selected_skills | skill_trigger_basis | update_chain_status | creator_plane_changes | installer_plane_distribution | acceptance_command | evidence_ref | domain_artifact_refs | upgrade_targets | result_status | next_action | owner_layer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  | trigger/patch/validate/replay |  |  |  |  |  |  |  |  |  |

Upgrade targets schema (mandatory):

- `upgrade_targets` row format:
  - target_type
  - target_ref
  - change_kind
  - owner_layer

Allowed `target_type`:

- `identity_prompt`
- `identity_task_contract`
- `skill`
- `mcp_server`
- `tool_route`
- `tool_runtime`
- `vendor_api_contract`
- `vendor_adapter`
- `integration_solution_contract`
- `other` (requires `target_type_other_reason`)
- `validator`
- `workflow_gate`
- `report_contract`
- `session_orchestration`
- `path_boundary`

If `target_type=other`, add this required field per item:

- `target_type_other_reason` (why existing enum cannot represent this target yet)

Allowed `change_kind`:

- `add`
- `update`
- `remove`
- `rewire`
- `tuning`
- `fix`

---

## 9) Residual risk register

Use one row per unresolved risk.

| Risk ID | Layer | Severity | Description | Current impact | Next mitigation | Owner | ETA |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

---

## 10) Final handoff summary (fixed)

- Instance-plane status:
- Repo-plane status:
- Release-plane status:
- Overall release decision:
- Next milestone:
- Escalation needed: yes/no
