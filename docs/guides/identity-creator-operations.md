# Identity-Creator Operations Guide

This guide documents end-to-end operator steps to create, register, validate, and publish identity packs.

## 1) Create a new identity pack (scaffold)

Option A (skill script):

```bash
bash skills/identity-creator/scripts/init_identity_pack.sh \
  quality-supervisor \
  "Quality Supervisor" \
  "Cross-checks listing quality and rejection remediation" \
  identity/packs
```

Generated files:
- `identity/packs/<id>/META.yaml`
- `identity/packs/<id>/IDENTITY_PROMPT.md`
- `identity/packs/<id>/CURRENT_TASK.json`
- `identity/packs/<id>/TASK_HISTORY.md`
- `identity/packs/<id>/agents/identity.yaml`

## 2) Register in catalog

Update `identity/catalog/identities.yaml`:
- add identity object
- set `pack_path`
- add optional `interface/policy/dependencies/observability`

## 3) Validate protocol + manifest

```bash
python3 scripts/validate_identity_protocol.py
python3 scripts/validate_identity_manifest.py
python3 scripts/test_identity_discovery_contract.py
```

## 4) Compile runtime brief

```bash
python3 scripts/identity_creator.py compile \
  --catalog /path/to/.identity/catalog.local.yaml \
  --actor-id assistant:codex
```

Notes:
- compile now resolves the active runtime identity from the local runtime catalog plus actor binding / compatibility projection, not from repo fixture defaults
- generated `identity/runtime/IDENTITY_COMPILED.md` includes the frozen native-chat contract:
  - `Identity-Context`
  - `Machine-Verification`
  - body
- native chat ordering is human-first (`Identity-Context`) then machine-proof (`Machine-Verification`)

## 5) Run e2e smoke

```bash
bash scripts/e2e_smoke_test.sh
```

## 6) Consumer-side upgrade verification

In consumer repo:

```bash
bash scripts/protocol_consumer/upgrade_and_verify_v1.sh
```

## 7) Publish protocol changes

```bash
git add .
git commit -m "feat(identity): ..."
git push origin main
```

If workflow file push is blocked by OAuth workflow scope, use GitHub MCP write as fallback.

## 8) Activation side effect

`python3 scripts/identity_creator.py activate ...` now recompiles `identity/runtime/IDENTITY_COMPILED.md` at the end of a successful activation so the default Codex `model_instructions_file` stays aligned with the active runtime identity.
