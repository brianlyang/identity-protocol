# Standards Alignment Matrix

## Goal

Align identity-creator with:
- local skill-creator methodology
- official Codex skills and config model
- AGENTS instruction-chain behavior

## Alignment checkpoints

1. Discovery and metadata
- Skill standard: frontmatter `name` + `description`.
- Skill ecosystem extension: optional `agents/openai.yaml` for `interface`, `policy`, `dependencies`.
- Identity extension: `identity/catalog/identities.yaml` with `id`, `title`, `description`, `pack_path`, `status`,
  and optional `interface/policy/dependencies/observability` blocks.

2. Progressive disclosure
- Skill standard: metadata always loaded, full SKILL.md loaded on trigger.
- Identity extension: registry metadata is always light-load; runtime brief is compact; full pack files are loaded on activation.

3. Deterministic resources
- Skill standard: scripts when determinism is required.
- Identity extension: runtime state and protocol docs are deterministic artifacts.

4. Config integration
- Skill/MCP are native Codex config objects.
- Identity is integrated through native keys:
  - `model_instructions_file`
  - project instruction discovery and AGENTS chain
  - identity discovery contract (`identity/protocol/IDENTITY_DISCOVERY.md`) to mirror `skills/list` style behavior.

5. Safety and approvals
- Keep sandbox and approval policies explicit in project config and governance docs.

6. Invocation and activation parity
- Skill standard: explicit invocation (`$skill-name`) + implicit invocation based on description/policy.
- Identity extension: explicit identity selection has highest priority; implicit activation is policy-gated
  (`allow_implicit_activation`, `activation_priority`, `conflict_resolution`).

7. Dependency declaration parity
- Skill standard: tool dependencies can be declared in `openai.yaml`.
- Identity extension: dependencies are declared in catalog manifest so execution/runtime planners can preflight
  MCP/env/network prerequisites before role activation.

8. API and server-side evolution awareness
- Official Codex ecosystem includes app-server skill list/config operations and API-level Skills resources.
- Identity extension should maintain server-agnostic contracts (`identity/list`) now, then implement transport bindings
  after contract stabilization.
