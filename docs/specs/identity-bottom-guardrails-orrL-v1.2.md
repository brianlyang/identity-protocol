# Identity Bottom Guardrails (ORRL) v1.2

Status: Draft for v1.2.0
Updated: 2026-02-20

## Why

Skills have native protocol/runtime support in Codex.
Identity is an extension protocol and therefore needs explicit bottom guardrails to achieve comparable reliability.

## ORRL gates

A high-impact run is invalid unless all gates pass:

1. **Observe** (`multimodal_consistency_gate`)
   - Require triplet evidence: `api_evidence`, `event_evidence`, `ui_evidence`.
   - Mark run `inconsistent` when triplet conflicts.
   - `inconsistent` cannot transition to `done`.

2. **Reason** (`reasoning_loop_gate`)
   - Each failed attempt must include:
     - `attempt`, `hypothesis`, `patch`, `expected_effect`, `result`
   - Guesswork resubmission is forbidden.

3. **Route** (`routing_gate`)
   - Must resolve `problem_type -> route` from `routing_contract.problem_type_routes`.
   - If no improvement after configured retries, force route switch.

4. **Ledger** (`rulebook_gate`)
   - Append-only `RULEBOOK.jsonl` required.
   - Must include both negative and positive rule records over time.

## Runtime contract location

- `identity/store-manager/CURRENT_TASK.json`
- `identity/store-manager/RULEBOOK.jsonl`

## Validator

- `scripts/validate_identity_runtime_contract.py`

## Smoke test integration

- `scripts/e2e_smoke_test.sh` includes ORRL contract validation.
