# Identity Control Loop v1.4.0

## Objective

Define identity as a single control-plane loop that orchestrates skills, MCP, tools, and LLM reasoning under one runtime contract.

Loop stages:

1. **Observe** — gather task intent, available capabilities, and evidence context.
2. **Decide** — route by scored policy and risk/cost constraints.
3. **Orchestrate** — execute skill + MCP + tool pipeline with preflight checks.
4. **Validate** — enforce gates and semantic checks.
5. **Learn** — write positive/negative experiences into structured feedback stores.
6. **Update** — trigger patch/validate/replay lifecycle when drift or repeated failures occur.

## Required runtime contracts

- `capability_orchestration_contract`
- `knowledge_acquisition_contract`
- `experience_feedback_contract`
- `ci_enforcement_contract`

## Gate alignment

Required gate flags in `CURRENT_TASK.gates`:

- `orchestration_gate = required`
- `knowledge_acquisition_gate = required`
- `experience_feedback_gate = required`
- `ci_enforcement_gate = required`

## Validator map

- `scripts/validate_identity_orchestration_contract.py`
- `scripts/validate_identity_knowledge_acquisition.py`
- `scripts/validate_identity_experience_feedback.py`
- `scripts/validate_identity_ci_enforcement.py`

## Metrics baseline

Route metrics should include at least:

- `route_hit_rate`
- `first_pass_success_rate`
- `fallback_rate`
- `knowledge_reuse_rate`
- `replay_success_rate`
- `policy_drift_incidents`

## CI requirement

Both workflows must include all required validators under job `required-gates`:

- `protocol-ci / required-gates`
- `identity-protocol-ci / required-gates`

## Ops preflight

Before runtime tests, sync local protocol repo to remote head and run required gates locally.

Reference: `scripts/preflight_identity_runtime_sync.sh`
