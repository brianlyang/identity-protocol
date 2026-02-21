# Upgrade Cross-Validation Template

Use this template for **every identity-protocol version upgrade** to prevent drift from skill/MCP baselines.

## 1) Upgrade metadata

- Version:
- Date:
- Owner:
- Scope:
- PR:
- Commit:

## 2) Baseline references reviewed (must cite)

1. `identity/protocol/IDENTITY_PROTOCOL.md`
2. `identity/protocol/IDENTITY_RUNTIME.md`
3. `docs/references/skill-installer-skill-creator-skill-update-lifecycle.md`
4. `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`
5. (Optional) other skill/MCP references used:

## 3) Four-core non-conflict mapping

Document how changes are extensions (implementation controls), not redefinitions.

| Core capability | Upgrade change | Non-conflict rationale |
|---|---|---|
| Accurate judgement |  |  |
| Reasoning loop |  |  |
| Auto-routing |  |  |
| Rule learning |  |  |

## 4) Contract/validator/CI alignment

- Runtime contract keys changed:
- Validators added/updated:
- Required-gates workflow updates:
- e2e smoke updates:

## 5) Replay and regression evidence

- Trigger regression suites:
- Replay case(s):
- Outcome:

## 6) Residual risks and controls

- Residual risk:
- Mitigation:
- Next action:

## 7) Final assertion

> This upgrade is a controlled extension aligned with identity four-core capability contracts and cross-validated against skill + MCP protocol boundaries.
