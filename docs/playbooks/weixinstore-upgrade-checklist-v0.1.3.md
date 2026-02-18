# Weixinstore Upgrade Checklist (to identity-protocol v0.1.3)

## Pre-check
- [ ] Snapshot current repo state / create rollback branch
- [ ] Confirm `.codex/config.toml` exists

## Apply
- [ ] Sync protocol files from tag `v0.1.3`
- [ ] Preserve local business identity pack customizations

## Config path validation
- [ ] `model_instructions_file` resolves from `.codex/` directory
- [ ] all `[[skills.config]].path` values resolve from `.codex/`

Run:
```bash
python3 skills/identity-creator/scripts/check_codex_config_paths.py
bash skills/identity-creator/scripts/validate_identity_protocol.sh .
```

## Runtime contract validation
- [ ] `CURRENT_TASK.json` has required keys
- [ ] `IDENTITY_COMPILED.md` is present and current

## Smoke test
- [ ] `codex resume` no config loading errors
- [ ] identity runtime brief visible and consistent
- [ ] one low-risk operation executed successfully

## Rollback
- [ ] revert protocol files to previous pinned tag
- [ ] rerun path + protocol validation scripts
