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

5. Integrate `.codex/config.toml`:
- set `model_instructions_file = "../identity/runtime/IDENTITY_COMPILED.md"` (resolved from `.codex/`)
- keep skills and MCP in native keys

6. Validate:
- run `scripts/validate_identity_protocol.sh`
- run `scripts/check_codex_config_paths.py`

7. Record rollout note:
- what changed
- affected guardrails
- rollback path

## Rollback

- Restore previous `identity/runtime/IDENTITY_COMPILED.md`
- Revert `.codex/config.toml` `model_instructions_file`
- Mark registry entry `inactive`
