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
python3 scripts/compile_identity_runtime.py
```

## 5) Run e2e smoke

```bash
bash scripts/e2e_smoke_test.sh
```

## 6) Consumer-side upgrade verification

In consumer repo:

```bash
bash scripts/identity/upgrade_and_verify_v1.sh
```

## 7) Publish protocol changes

```bash
git add .
git commit -m "feat(identity): ..."
git push origin main
```

If workflow file push is blocked by OAuth workflow scope, use GitHub MCP write as fallback.

