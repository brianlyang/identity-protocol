# Identity Protocol Contract v1.0.0 (Frozen)

Status: **Stable**

This document freezes the minimum interoperable contract for identity protocol consumers.

## 1. Scope

Identity protocol is the control plane parallel to:
- Skills (capability packaging)
- MCP (execution transport)

Identity is responsible for:
- hard governance boundaries
- runtime single-source-of-truth state
- adaptive learning lifecycle

## 2. Required repository structure

Required directories:
- `identity/catalog/`
- `identity/protocol/`
- `identity/runtime/`

Required files:
- `identity/catalog/identities.yaml`
- `identity/catalog/schema/identities.schema.json`
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`
- `identity/runtime/IDENTITY_COMPILED.md`

## 3. Catalog contract

`identity/catalog/identities.yaml` must contain:
- `version`
- `default_identity`
- `identities[]`

Each identity entry must contain:
- `id`
- `title`
- `description`
- `status`
- `methodology_version`
- `pack_path`

`default_identity` must resolve to one identity in `identities`.

## 4. Active identity pack minimum

At `pack_path` (or legacy fallback `identity/<id>/`) the following files must exist:
- `IDENTITY_PROMPT.md`
- `CURRENT_TASK.json`
- `TASK_HISTORY.md`

`CURRENT_TASK.json` must include keys:
- `objective`
- `state_machine`
- `gates`
- `source_of_truth`
- `escalation_policy`
- `required_artifacts`
- `post_execution_mandatory`

## 5. Runtime compile contract

`scripts/compile_identity_runtime.py` must produce `identity/runtime/IDENTITY_COMPILED.md` including at least:
- active identity id
- hard guardrails
- current objective
- current state
- source pointers

Generated brief should be concise and deterministic.

## 6. Conflict resolution order

Normative order:
1. Canon / hard guardrails
2. Runtime state contract
3. Skill instructions
4. Tool preferences

## 7. Consumer integration rules

- Native Codex config remains authoritative for `skills` and `mcp_servers`.
- Identity remains extension protocol integrated via runtime instruction file.
- `.codex/config.toml` paths must be resolved relative to `.codex/` directory.

## 8. Compatibility and upgrade policy

- `v1.x` guarantees backward compatibility for required keys and structure.
- Breaking changes require `v2.0.0`.
- Consumers should pin tags and upgrade intentionally using migration checklist.
