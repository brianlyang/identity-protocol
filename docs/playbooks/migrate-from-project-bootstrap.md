# Migration Playbook: Project Bootstrap -> Protocol Repository

## Goal

Move protocol artifacts from business repository bootstrap into this dedicated protocol repository while preserving behavior.

## Migration checklist

1. Copy protocol artifacts:
   - `identity/catalog/*`
   - `identity/protocol/*`
   - `identity/runtime/IDENTITY_COMPILED.md` (template/runtime example)
2. Copy creator skill package:
   - `skills/identity-creator/*`
3. Validate script executability:
   - `scripts/*.sh` executable bit set
4. Add ADR and references:
   - `docs/adr/*`
   - `docs/references/*`
5. Tag baseline release:
   - `v0.1.0`

## Consumer repository integration

In consumer repo (e.g., weixinstore):
- keep identity pack instances in project
- optionally pin this protocol repo via subtree/submodule
- run path check and protocol validation scripts on every upgrade

## Verification commands

```bash
python3 skills/identity-creator/scripts/check_codex_config_paths.py
bash skills/identity-creator/scripts/validate_identity_protocol.sh .
```
