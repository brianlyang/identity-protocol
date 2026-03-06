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

### Change governance

Every content update must provide:

1. change summary (`what changed`)
2. capability delta (`which checklist items were affected`)
3. validator impact (`which validators/fields must change`)
4. replay obligations (`positive + negative`)
5. review trace (`governance anchor + review anchor + commit`)

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

## Acceptance command baseline

```bash
python3 scripts/compile_identity_runtime.py --catalog <LOCAL_CATALOG> --identity-id <ID>
python3 scripts/validate_identity_prompt_quality.py --catalog <LOCAL_CATALOG> --identity-id <ID>
python3 scripts/validate_v16_prompt_kernel_executable_coupling.py --catalog <LOCAL_CATALOG> --identity-id <ID> --operation update --json-only
```

Promotion boundary:

1. This file alone does not unlock promotion.
2. Promotion requires mapping + validator + lane-consumption + replay closure.
