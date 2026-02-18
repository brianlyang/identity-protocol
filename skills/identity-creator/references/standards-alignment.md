# Standards Alignment Matrix

## Goal

Align identity-creator with:
- local skill-creator methodology
- official Codex skills and config model
- AGENTS instruction-chain behavior

## Alignment checkpoints

1. Discovery and metadata
- Skill standard: frontmatter `name` + `description`.
- Identity extension: `identity/catalog/identities.yaml` with `id`, `title`, `description`, `pack_path`, `status`.

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

5. Safety and approvals
- Keep sandbox and approval policies explicit in project config and governance docs.
