# Identity-Creator Implementation Runbook

## Step-by-step

1. Create protocol folders:
- `identity/catalog`
- `identity/protocol`
- `identity/runtime`

2. Create registry and schema:
- `identity/catalog/identities.yaml`
- `identity/catalog/schema/identities.schema.json`

3. Create protocol docs:
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

4. Create/upgrade identity pack:
- `IDENTITY_PROMPT.md`
- `CURRENT_TASK.json`
- `TASK_HISTORY.md`
- `META.yaml`
- `RULEBOOK.jsonl`
- `agents/identity.yaml`

5. Enforce baseline review controls for identity upgrades:
- Ensure `gates.protocol_baseline_review_gate = "required"` in runtime task.
- Ensure `protocol_review_contract` exists with:
  - mandatory review source list
  - required evidence fields
  - evidence artifact path pattern
- Create/update evidence artifact under:
  - `identity/runtime/examples/protocol-baseline-review-*.json`

6. Integrate `.codex/config.toml`:
- set `model_instructions_file = "../identity/runtime/IDENTITY_COMPILED.md"` (resolved from `.codex/`)
- keep skills and MCP in native keys

7. Validate:
- run `scripts/validate_identity_protocol.sh`
- run `scripts/check_codex_config_paths.py`
- run `scripts/validate_identity_runtime_contract.py`

8. Record rollout note:
- what changed
- affected guardrails
- rollback path

## Rollback

- Restore previous `identity/runtime/IDENTITY_COMPILED.md`
- Revert `.codex/config.toml` `model_instructions_file`
- Mark registry entry `inactive`
