# Protocol Baseline Review (Identity Upgrade MUST)

When a task involves **identity capability upgrades** or **identity architecture decisions**, review and cite protocol baselines before producing conclusions.

## Mandatory sources

1. `brianlyang/identity-protocol::identity/protocol/IDENTITY_PROTOCOL.md`
2. `brianlyang/identity-protocol::docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md`
3. `https://developers.openai.com/codex/skills/`
4. `https://agentskills.io/specification`
5. `https://modelcontextprotocol.io/specification/latest`

## Required evidence fields

- `review_id`
- `reviewed_at`
- `reviewer_identity`
- `purpose`
- `sources_reviewed`
- `findings`
- `decision`

## Evidence artifact pattern

Use:

- `identity/runtime/examples/protocol-baseline-review-*.json`

## Gate semantics

- If `gates.protocol_baseline_review_gate` is `required`, runtime validation must fail when:
  - evidence artifact is missing
  - required fields are incomplete
  - any mandatory source is not covered

## Why this exists

This prevents identity-level drift and unsupported claims. It enforces the same discipline expected from skill and MCP protocols: source-backed, testable, deterministic decisions.
