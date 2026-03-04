# Identity Onboarding 72h Audit Return Template

Purpose:

1. Standardize architect ↔ audit-expert handoff for onboarding closure.
2. Enforce strict protocol/instance layer separation and dual-ledger discipline.
3. Keep output machine-checkable, replayable, and evidence-traceable.
4. Preserve deep domain-learning analysis in instance artifacts while keeping protocol records clean.

Status: template
Primary layer of this file: reporting interface (protocol + instance tracks)
Protocol guardrails source: canonical SSOT handoff (protocol layer)
SSOT execution rule: execute protocol decisions only from `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`; external artifacts are evidence mirrors, not normative sources.

---

## 0) Layer boundary declaration (mandatory)

### 0.1 Layered governance boundary

- A-track = `protocol` layer, for contract/rule/gate integrity.
- B-track = `instance` layer, for identity runtime upgrade/activation closure.
- Mixed-layer conclusions are prohibited in one sentence/claim.

### 0.2 Dual-ledger boundary

- Governance ledger may store only machine-checkable governance facts and redacted summaries.
- Domain ledger (instance artifacts) may store deep business details and analysis outputs.
- Protocol/governance records must not inline non-redacted business details.
- Business details must be linked through `domain_artifact_refs` only.

---

## 1) Report metadata

- Date (UTC):
- Reporter:
- Branch:
- Target identity:
- Runtime mode:
- Catalog path:
- Scope:
- Run window:
- Layer package type (`A-only` / `B-only` / `A+B split package`):

---

## 2) A-track (protocol) return block

### 2.1 Commit SHA list

- SHA-1:
- SHA-2:

### 2.2 Changed file list

- File:
- File:

### 2.3 Acceptance command outputs

Provide exact command + terminal summary:

1. SSOT source validator
   - command:
   - rc:
   - output summary:
2. Handoff coupling validator
   - command:
   - rc:
   - output summary:
3. Docs command contract checker
   - command:
   - rc:
   - output summary:

### 2.4 Residual risks + next milestone

- Residual risks:
- Next milestone:

### 2.5 Layer declaration

- layer declaration: `protocol`

---

## 3) B-track (instance) return block

### 3.1 Commit SHA list

- SHA-1:
- SHA-2:

### 3.2 Changed file list

- File:
- File:

### 3.3 Acceptance command outputs

Minimum recommended set:

1. Identity protocol baseline validator
   - command:
   - rc:
   - output summary:
2. Runtime contract validator
   - command:
   - rc:
   - output summary:
3. Role-binding validator
   - command:
   - rc:
   - output summary:
4. Prompt quality validator
   - command:
   - rc:
   - output summary:
5. Learning-loop validator
   - command:
   - rc:
   - output summary:
6. Capability arbitration self-test
   - command:
   - rc:
   - output summary:
7. e2e smoke (target identity)
   - command:
   - rc:
   - output summary:
8. Readiness (policy declared)
   - command:
   - rc:
   - output summary:
9. Three-plane status
   - command:
   - rc:
   - output summary:
10. Self-driven upgrade ledger validator (when available)
    - command:
    - rc:
    - output summary:
11. Roundtable/cross-validation output check
    - command:
    - rc:
    - output summary:
12. Install safety validator (when tool-install path is used)
    - command:
    - rc:
    - output summary:
13. Install provenance validator (when tool-install path is used)
    - command:
    - rc:
    - output summary:
14. Vendor API discovery validator (when vendor/api onboarding path is used)
    - command:
    - rc:
    - output summary:
15. Vendor API solution validator (when vendor/api onboarding path is used)
    - command:
    - rc:
    - output summary:

### 3.4 Skill protocol execution attachment (mandatory)

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

1. `selected_skills` must contain only actually activated skills for this run window.
2. `skill_trigger_basis` must reference concrete evidence/command ids.
3. `update_chain_status(trigger/patch/validate/replay)` must be fully populated.
4. `creator_plane_changes` and `installer_plane_distribution` must declare owner layer.

### 3.5 Multimodal evidence role closure (mandatory)

Core semantics (must keep):

1. Multimodal inputs are fact-input layer inputs, not display-only attachment defaults.
2. Attachments are allowed, but default role is `DISPLAY_ONLY`.
3. Only gated evidence can transition to `FACT_INPUT`.
4. `DISPLAY_ONLY` evidence cannot support final claims.
5. Critical gate failure must downgrade state to `manual_review` or `blocked`.
6. Thresholds are instance-config referenced and not hardcoded in protocol templates.
7. `inconsistent evidence cannot transition to done`.

Fields:

- evidence_role:
- role_transition_state:
- role_transition_gate_refs:
- final_claim_evidence_refs:

### 3.6 Residual risks + next milestone

- Residual risks:
- Next milestone:

### 3.7 Layer declaration

- layer declaration: `instance`

### 3.8 Tool discovery and installation return block (mandatory when tool-gap path is triggered)

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

1. `tool_gap_detected=yes` requires full evidence chain from plan -> approval -> execution -> verify -> route binding.
2. Missing healthcheck or smoke evidence means installation is not accepted as active route.
3. Installation failure must include fallback route evidence and rollback reference.

### 3.9 New-object discovery trust return block (mandatory when introducing new `skill`/`mcp_server`/`tool_runtime`)

- object_type:
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

Discovery source matrix:

| object_type | source_url | source_kind (`official_doc`/`official_registry`/`official_repo`/`community_repo`) | trust_tier (`T0`/`T1`/`T2`) | provenance_or_signature_ref | decision (`selected`/`rejected`) | rejection_reason |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Rules:

1. `selected` source rows must carry trust and provenance/signature evidence.
2. `T2` source usage requires explicit approval receipt.
3. For `tool_runtime`, active-route acceptance requires post-attach validators and rollback references.

---

### 3.10 Vendor/API solution return block (mandatory after vendor/API discovery selection)

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

1. Exactly one option must be `selected=yes` for each decision window.
2. Selected option must include security/auth/rate-limit strategy references.
3. Selected option must include both fallback and rollback references.
4. `owner_layer_declaration_ref` must clearly separate protocol and instance responsibilities.
5. If no option is selected, status must remain `defer` or `blocked`; no implicit default.

---

## 4) self-driven upgrade ledger (mandatory)

Rules:

1. Include one row per upgrade event in the reporting window.
2. `trigger_mode` must be `active` or `passive`.
3. `capability_axis` must be one value from allowed enum list.
4. If `result_status != PASS`, `next_action` is mandatory.
5. `domain_artifact_refs` is required when business learning evidence exists.
6. `upgrade_targets` must enumerate all changed components.

Allowed `capability_axis` values:

- `prompt_contract`
- `skill_routing`
- `mcp_binding`
- `tool_routing`
- `validator_chain`
- `vendor_api_discovery`
- `solution_architecture`
- `workflow_gate`
- `report_contract`
- `session_orchestration`
- `path_boundary`
- `roundtable_intelligence`

| upgrade_id | run_id | ts_utc | trigger_mode | trigger_source | capability_axis | change_surface_ref | selected_skills | skill_trigger_basis | update_chain_status | creator_plane_changes | installer_plane_distribution | acceptance_command | evidence_ref | domain_artifact_refs | upgrade_targets | result_status | next_action | owner_layer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  | trigger/patch/validate/replay |  |  |  |  |  |  |  |  |  |

`upgrade_targets` schema (mandatory fields per item):

- target_type
- target_ref
- change_kind
- owner_layer

Allowed `target_type` values:

- `identity_prompt`
- `identity_task_contract`
- `skill`
- `mcp_server`
- `tool_route`
- `tool_runtime`
- `validator`
- `vendor_api_contract`
- `vendor_adapter`
- `integration_solution_contract`
- `other` (requires `target_type_other_reason`)
- `workflow_gate`
- `report_contract`
- `session_orchestration`
- `path_boundary`

If `target_type=other`, add this required field per item:

- `target_type_other_reason` (why existing enum cannot represent this target yet)

Allowed `change_kind` values:

- `add`
- `update`
- `remove`
- `rewire`
- `tuning`
- `fix`

---

## 5) Roundtable and cross-vendor validation evidence (mandatory for complex upgrades)

Roundtable required when any impacted axis includes:

- `skill_routing`
- `mcp_binding`
- `tool_routing`
- `vendor_api_discovery`
- `solution_architecture`
- `validator_chain`
- `path_boundary`

Roundtable output fields:

- discussion_topic:
- participants_role_set:
- decision_matrix_ref:
- final_decision_ref:
- unresolved_items_count:
- skip_reason_if_not_required:

Cross-vendor matrix (fact/inference separated):

| vendor | source_url | retrieved_at | claim | claim_type (`fact`/`inference`) | mapped_contract_or_validator | risk_note |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Constraint:

1. Final claims must reference at least one `fact` row.
2. Each `inference` row must include mapped validator/contract basis and explicit risk note.

---

## 6) Three-plane final declaration (mandatory)

- instance_plane_status:
- repo_plane_status:
- release_plane_status:
- overall_release_decision:

Rule:

1. Any plane not CLOSED => overall decision remains Conditional Go.
2. Full Go requires release-plane cloud closure evidence.

---

## 7) Identity context tuple evidence (mandatory)

Attach tuple from resolver:

- source_layer:
- catalog_path:
- pack_path:
- resolved_scope:
- resolved_pack_path:

If catalog_path is unexpected for current runtime mode, report as misconfiguration.

---

## 8) Sign-off

- Architect sign-off:
- Audit expert sign-off:
- Pending follow-ups:
