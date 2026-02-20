# Identity Learning-Loop Validation (v1.2.1)

## Purpose

Make core capability #2 and #4 verifiable at protocol level:

2) strong reasoning loop until target is reached
4) strong rule ability with positive/negative rule completion

## Validation contract

Inputs:
- `identity/store-manager/CURRENT_TASK.json`
- run report JSON (`--run-report`)
- `identity/store-manager/RULEBOOK.jsonl`

Checks:
1. run report has `run_id` when required.
2. run report has non-empty `reasoning_attempts` when required.
3. each attempt includes mandatory fields from `reasoning_loop_contract.mandatory_fields_per_attempt`.
4. rulebook contains at least one row linked to the run by `rulebook_link_field` (default `evidence_run_id`).

Validator:
- `scripts/validate_identity_learning_loop.py`

Smoke-test integration:
- `scripts/e2e_smoke_test.sh` includes learning-loop validation.
