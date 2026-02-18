# Weixinstore Consumer Integration Playbook

This guide explains how a business repository (example: `weixinstore`) should consume `identity-protocol` releases.

## 1) Pin protocol version

Use a tagged release (`v0.1.x`) rather than tracking `main`.

Recommended:
- pin to a tag in release notes
- upgrade intentionally through review checklist

## 2) Keep local identity instances

In consumer repo, keep business-specific identity packs and runtime state local:
- `identity/store-manager/*`
- `.codex/config.toml`
- business guardrails and escalation policy

Do not overwrite consumer-specific rules blindly when syncing protocol updates.

## 3) Required config checks

Because `.codex/config.toml` paths are resolved relative to `.codex/` directory:

- `model_instructions_file = "../identity/runtime/IDENTITY_COMPILED.md"`
- `[[skills.config]].path = "../skills/<skill>/SKILL.md"`

Run after every update:

```bash
python3 skills/identity-creator/scripts/check_codex_config_paths.py
bash skills/identity-creator/scripts/validate_identity_protocol.sh .
```

## 4) Upgrade flow

1. Fetch new tag from `identity-protocol`.
2. Apply protocol docs/scripts updates.
3. Re-run local validation.
4. Review runtime brief diff.
5. Run one low-risk execution test.
6. Promote to production branch.

## 5) Rollback flow

If post-upgrade checks fail:

1. Revert to previous protocol tag.
2. Restore previous compiled runtime brief.
3. Re-run validation scripts.
4. Record incident in reject-memory / task history.

## 6) Change control requirements

Every protocol upgrade PR should include:
- target from-tag and to-tag
- expected behavior changes
- migration notes
- rollback commit or command
- reviewer sign-off
