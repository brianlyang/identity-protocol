# identity-creator CLI Contract (Draft v1)

This document defines a stable command contract for `identity-creator`, modeled after the predictability goals of `skill-creator`.

## Design goals

- Deterministic outputs
- Minimal required parameters
- Schema-first validation
- Runtime-safe compile behavior

## Commands

### 1) `init`

Scaffold a new identity pack and optional catalog registration.

```bash
identity-creator init \
  --id store-manager \
  --title "WeChat Shop Store Manager" \
  --description "Revenue-oriented autonomous operator" \
  --pack-root identity/packs
```

Expected output:
- `META.yaml`
- `IDENTITY_PROMPT.md`
- `CURRENT_TASK.json`
- `TASK_HISTORY.md`

### 2) `register`

Register or update identity metadata in `identity/catalog/identities.yaml`.

```bash
identity-creator register \
  --id store-manager \
  --catalog identity/catalog/identities.yaml \
  --pack-path identity/store-manager
```

Validation:
- unique id
- valid status enum
- required metadata fields present

### 3) `validate`

Validate catalog + active pack + runtime contract.

```bash
identity-creator validate \
  --catalog identity/catalog/identities.yaml \
  --schema identity/catalog/schema/identities.schema.json
```

Validation includes:
- schema pass
- default_identity exists
- required pack files exist
- runtime keys exist in `CURRENT_TASK.json`

### 4) `compile`

Compile concise runtime brief from active identity.

```bash
identity-creator compile \
  --catalog identity/catalog/identities.yaml \
  --output identity/runtime/IDENTITY_COMPILED.md
```

Output constraints:
- concise
- includes hard guardrails
- includes current objective and state

### 5) `activate`

Switch active identity and recompile runtime brief.

```bash
identity-creator activate --id store-manager
```

Effects:
- update `default_identity` (or runtime active pointer)
- compile runtime brief
- append activation log (optional)

## Exit codes

- `0` success
- `1` validation/config/runtime failure
- `2` misuse/invalid arguments

## Non-goals

- Does not replace native Codex skills/MCP config.
- Does not automatically mutate consumer business payloads.

## Compatibility notes

Identity remains a project extension protocol today.
Native Codex integration points remain:
- `model_instructions_file`
- AGENTS/project instruction chain
- native `skills` and `mcp_servers` config blocks
