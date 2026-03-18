# Identity Prompt Bootstrap Contract (v1.6 draft)

## Scope and non-goals

1. This file is a protocol-kernel prompt contract source for v1.6.
2. It is not a runtime artifact and must not be consumed as `pack_path/IDENTITY_PROMPT.md`.
3. Runtime `IDENTITY_PROMPT.md` remains a compiled pack-level artifact.

## Source model

Prompt derivation source order:

1. protocol kernel contracts (`identity/protocol/*`)
2. this bootstrap contract file (prompt-specific kernel source)
3. identity overlay directives (pack-specific role/domain constraints)

Derived output target:

1. `identity/packs/<id>/IDENTITY_PROMPT.md` (or equivalent runtime pack path from catalog)

## Versioning and ownership

1. Contract stream: `v1.6.x` (contract-first, replay-locked).
2. Owner lane: `work_layer=protocol` only.
3. Update mode:
   - event-driven updates are mandatory when base protocol capability contracts change,
   - periodic hygiene refresh is mandatory at least once per release cycle.
4. Runtime lane must not mutate this file directly.

## Contract anchors

### rq_014_prompt_bootstrap_capability_contract_v1

Required bootstrap capability set:

1. source precedence
2. judgement/reasoning/routing/rule-learning (four-core)
3. protocol baseline review
4. update lifecycle (`trigger -> patch -> validate -> replay`)
5. trigger regression + handoff
6. collaboration trigger
7. control-loop extension (`Observe -> Decide -> Orchestrate -> Validate -> Learn -> Update`)
8. capability arbitration + conflict order
9. lane separation (`instance` vs `protocol`)
10. dual-track governance and release declaration

Fail-close rule:

1. Any missing required capability driver is `FAIL_REQUIRED`.

### rq_015_prompt_capability_matrix_fail_closed_contract_v1

Canonical output fields (must not be renamed):

1. `capability_driver_required_total`
2. `capability_driver_present_total`
3. `capability_driver_coverage_rate`
4. `missing_capability_drivers`
5. `prompt_bootstrap_contract_status`
6. `error_code`

Fail-close rule:

1. Coverage below `100%` for required drivers is `FAIL_REQUIRED`.

### rq_027_derived_prompt_conformance_contract_v1

Required compile/runtime metadata:

1. `kernel_contract_version`
2. `kernel_contract_digest`
3. `derived_from_contract_ids`
4. `overlay_digest`

Conformance rule:

1. Missing or mismatched metadata chain is `FAIL_REQUIRED`.

### rq_031_prompt_import_executable_coupling_contract_v1

Required executable coupling tuple:

1. `kernel_contract_ref`
2. `validator_ref`
3. `evidence_ref`
4. `actor_context_explicit`

Required fail-close families:

1. `IP-PROMPT-CONTRACT-001`
2. `IP-ACTOR-CTX-001`

Non-compliant pattern:

1. text-only prompt import without executable mapping delta.

### rq_033_native_chat_headstamp_prompt_contract_v1

Required native-chat prompt literals:

1. `Native Chat Headstamp Hard Guard`
2. every assistant-authored native-chat reply begins with a two-line headstamp before body text
3. headerless native-chat reply path is forbidden
4. failure path still emits withheld/conflict `Identity-Context` + `Machine-Verification: verification_status=FAIL_REQUIRED ...`
5. native chat keeps `Identity-Context -> Machine-Verification -> body`
6. governed surfaces keep `Display-Headstamp -> Machine-Verification -> body`
7. default native-chat `Machine-Verification` profile is `mini`
8. failure line 1 may claim only `requested_identity_id`
9. compatibility pointer diagnostics stay on `Machine-Verification` and remain diagnostic-only

Conformance rule:

1. Missing any required native-chat hard-guard literal is `FAIL_REQUIRED`.
2. Prompt derivation must consume the prompt hard-guard template source rather than ad hoc identity-local wording.

## Base protocol capability absorption matrix (full set)

The file must continuously absorb identity base protocol capabilities from `identity/protocol/IDENTITY_PROTOCOL.md`.

Coverage rule:

1. Every capability row below must remain mapped; missing row is non-compliant.
2. Any source-anchor update in base protocol must be reflected here in the same change window.
3. Matrix drift blocks promotion-grade claims.

| Capability domain | Canon source anchor | Prompt-bootstrap absorption requirement | Mandatory validators / gates | Evidence tuple |
| --- | --- | --- | --- | --- |
| runtime source-of-truth boundary | `IDENTITY_PROTOCOL.md#runtime-source-of-truth-boundary-v14x-hardening` | prompt content must preserve fixture/runtime split language and forbid runtime-state ambiguity | `validate_identity_runtime_contract.py`, creator/readiness | `runtime_mode`, `source_of_truth`, `evidence_scope` |
| scope resolution | `IDENTITY_PROTOCOL.md#scope-resolution-contract-v1412-uplift` | prompt policy must not bypass explicit scope/collision arbitration requirements | `validate_identity_scope_resolution.py`, `validate_identity_scope_isolation.py` | `scope`, `catalog_path`, `resolved_pack_path` |
| permission-state | `IDENTITY_PROTOCOL.md#permission-state-contract-ci-gated` | prompt must keep writeback permission checks in hard-guardrail path | `validate_identity_permission_state.py` | `permission_state`, `permission_error_code`, `writeback_precheck` |
| identity-scoped evidence isolation | `IDENTITY_PROTOCOL.md#identity-scoped-evidence-rule-mandatory` | prompt guidance must require identity-scoped sample/evidence paths | `validate_identity_instance_isolation.py` | `identity_id`, `evidence_path`, `cross_identity_hits` |
| state-source strategy | `IDENTITY_PROTOCOL.md#state-source-strategy-mandatory-v14x` | prompt policy must keep catalog/META strong-consistency assumptions | `validate_identity_state_consistency.py` | `catalog_status`, `meta_status`, `consistency_status` |
| four-core capability contracts | `IDENTITY_PROTOCOL.md#four-core-capability-contracts` | prompt drivers must cover judgement/reasoning/routing/rule-learning | `validate_prompt_capability_matrix.py` (planned), readiness/e2e | `capability_driver_required_total`, `capability_driver_present_total` |
| protocol baseline review | `IDENTITY_PROTOCOL.md#protocol-baseline-review-contract-v123` | prompt must require source-cited protocol review before architecture upgrades | `validate_identity_runtime_contract.py` | `protocol_review_contract`, `sources_reviewed`, `decision` |
| update lifecycle | `IDENTITY_PROTOCOL.md#identity-update-lifecycle-contract-v124` | prompt must preserve `trigger -> patch -> validate -> replay` lifecycle invariants | `validate_identity_update_lifecycle.py`, `validate_identity_upgrade_prereq.py` | `patched_files`, `validation_checks_passed`, `replay_status` |
| trigger regression | `IDENTITY_PROTOCOL.md#identity-trigger-regression-contract-v125` | prompt must require positive/boundary/negative trigger replay suites | `validate_identity_trigger_regression.py` | `suite_status`, `expected_route`, `observed_route` |
| agent handoff | `IDENTITY_PROTOCOL.md#agent-handoff-contract-v127` | prompt must keep delegated execution mutation boundaries explicit | `validate_agent_handoff_contract.py` | `handoff_required_fields`, `forbidden_mutations`, `handoff_verdict` |
| collaboration trigger | `IDENTITY_PROTOCOL.md#human-collaboration-trigger-contract-v130` | prompt must preserve blocker taxonomy + immediate notify + receipt requirements | `validate_identity_collab_trigger.py` | `blocker_type`, `notify_status`, `receipt_status` |
| control-loop extension | `IDENTITY_PROTOCOL.md#control-loop-extension-contracts-v140` | prompt must reflect closed-loop stages and evidence closure expectation | `validate_identity_orchestration_contract.py`, `validate_identity_knowledge_contract.py`, `validate_identity_experience_feedback.py` | `orchestration_status`, `knowledge_status`, `feedback_status` |
| capability arbitration | `IDENTITY_PROTOCOL.md#capability-arbitration-contract-v142` | prompt must include arbitration priority and conflict-order semantics | `validate_identity_capability_arbitration.py` | `priority_order`, `conflict_rule`, `arbitration_status` |
| dual-track governance + release declaration | `IDENTITY_PROTOCOL.md#dual-track-governance-model` | prompt must preserve hard guardrails > adaptive growth ordering and release-plane declaration constraints | release/readiness + required gates | `protocol_mode`, `overall_release_decision`, `hard_guardrail_hits` |

## Continuous iteration protocol (mandatory)

### Capability ingestion checklist

Each revision of this file must explicitly reconcile against identity base protocol capabilities:

1. four core capability contracts
2. protocol baseline review contract
3. identity update lifecycle contract
4. trigger regression contract
5. agent handoff contract
6. collaboration trigger contract
7. control-loop extension contracts
8. capability arbitration contract
9. dual-track governance model
10. runtime source-of-truth boundary
11. scope resolution and permission-state constraints
12. identity-scoped evidence isolation and state-source consistency

### Change governance

Every content update must provide:

1. change summary (`what changed`)
2. capability delta (`which checklist items were affected`)
3. validator impact (`which validators/fields must change`)
4. replay obligations (`positive + negative`)
5. review trace (`governance anchor + review anchor + commit`)
6. matrix sync proof (`capability matrix rows re-checked against base protocol anchors`)

### Drift triggers (must update this file immediately)

1. Any change to capability contracts in `identity/protocol/IDENTITY_PROTOCOL.md`.
2. Any governance change affecting `RQ-014/015/027/031`.
3. Any validator or error-code family change used by prompt bootstrap/executable coupling.
4. Any replay incident where prompt-text update does not produce executable delta.

### Iteration cadence contract

1. Immediate update when drift triggers occur.
2. Minimum one hygiene synchronization per release cycle even without drift trigger.
3. Missing cadence evidence is `PENDING_INTAKE` blocker for promotion-grade claims.

### Update ledger template

Use this template for each update entry:

```text
update_id:
updated_at_utc:
owner:
changed_sections:
capability_delta:
validator_delta:
replay_obligations:
governance_anchor:
review_anchor:
commit_sha:
```

### Update ledger (append-only)

```text
update_id: prompt-bootstrap-2026-03-06-phase2
updated_at_utc: 2026-03-06T23:05:00Z
owner: base-repo-audit-expert-v3
changed_sections: scope/versioning + capability matrix + drift triggers + cadence + four-track binding
capability_delta: added full-set base protocol capability absorption matrix and continuous iteration constraints
validator_delta: mapped existing required validators; planned validators for RQ-014/015/027/031 kept explicit
replay_obligations: requires positive/negative replay for bootstrap coverage, derivation conformance, executable coupling
governance_anchor: docs/governance/identity-actor-session-binding-governance-v1.6.0.md#813-prompt-bootstrap-kernel-source-continuity-guard-asb16-rq-014015027031-2026-03-06
review_anchor: docs/review/protocol-remediation-audit-ledger-v1.6.md#fix16-024---protocol-kernel-prompt-import-executable-coupling-self-drive-intake-asb16-rq-031
commit_sha: ee07aa1
```

## Four-track evidence binding (T1/T2/T3/T4)

Each promotion-grade update using this file must carry a four-track bundle:

1. T1 roundtable
2. T2 vendor/offical guidance
3. T3 OpenAI/context tooling evidence
4. T4 protocol/spec references

Required metadata:

1. `cross_verification_bundle_id`
2. `source_url_set`
3. `reference_timestamp_utc`
4. `conflict_reconciliation_note`

Hard rule:

1. missing any track or metadata field is non-compliant for promotion-grade claims.

## Acceptance command baseline

```bash
python3 scripts/compile_identity_runtime.py --catalog <LOCAL_CATALOG> --identity-id <ID>
python3 scripts/validate_identity_prompt_quality.py --catalog <LOCAL_CATALOG> --identity-id <ID>
python3 scripts/validate_v16_prompt_kernel_executable_coupling.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation update --json-only
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_protocol_ssot_source.py
```

Promotion boundary:

1. This file alone does not unlock promotion.
2. Promotion requires mapping + validator + lane-consumption + replay closure.
