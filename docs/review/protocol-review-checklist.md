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

## Upgrade cross-validation (mandatory for version changes)
- [ ] Extension/archive evidence exists in `docs/references/` for this upgrade.
- [ ] Four-core capability non-conflict mapping is documented (`accurate judgement/reasoning loop/auto-routing/rule learning`).
- [ ] Baseline references reviewed and cited:
  - [ ] `identity/protocol/IDENTITY_PROTOCOL.md`
  - [ ] `identity/protocol/IDENTITY_RUNTIME.md`
  - [ ] `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
  - [ ] `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
- [ ] Required validators are integrated into required-gates workflows.
- [ ] Replay evidence exists for changed routing/update behavior.
