# Protocol Review Checklist

## Contract correctness
- [ ] Catalog schema validates against `identities.schema.json`.
- [ ] `default_identity` exists in registry.
- [ ] Active identity pack contains required files.
- [ ] `CURRENT_TASK.json` contains minimum required blocks.

## Runtime consistency
- [ ] `scripts/compile_identity_runtime.py` runs successfully.
- [ ] `identity/runtime/IDENTITY_COMPILED.md` matches compiled output.
- [ ] `.codex/config.toml` path resolution is valid in consumer repos.

## Governance quality
- [ ] Hard guardrails are explicit.
- [ ] Escalation policy is blocker-only for offline actions.
- [ ] Conflict priority remains versioned and clear.

## Learning loop quality
- [ ] Known failure patterns are documented.
- [ ] Backward compatibility impact assessed.
- [ ] Migration note exists when behavior changes.
