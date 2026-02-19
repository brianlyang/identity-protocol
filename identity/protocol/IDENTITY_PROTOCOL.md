# Identity Protocol v1.0

## Goal

Define identity as a first-class control-plane protocol, parallel to skills and MCP.

- Skills: capability packaging and procedure execution.
- MCP: tool transport and action execution.
- Identity: strategy, boundaries, state transitions, and learning loop.

## Layer contract

1. Canon layer (hard governance)
2. Identity prompt layer (role cognition + decision principles)
3. Runtime task layer (single source of truth state)

## Required identity pack files

For each identity id `<id>`:
- `identity/packs/<id>/IDENTITY_PROMPT.md`
- `identity/packs/<id>/CURRENT_TASK.json`
- `identity/packs/<id>/TASK_HISTORY.md`
- `identity/packs/<id>/META.yaml`

Compatibility note: legacy packs can stay in `identity/<id>/` if catalog `pack_path` points there.

## Registry contract

`identity/catalog/identities.yaml` must include:
- id
- title
- description
- status
- methodology_version
- pack_path

`default_identity` must reference a valid id.

Optional v1.1 metadata blocks per identity:
- `interface` (display_name, short_description, default_prompt)
- `policy` (allow_implicit_activation, activation_priority, conflict_resolution)
- `dependencies` (tool/env/network/filesystem requirements)
- `observability` (event_topics, required_artifacts)

See discovery draft: `identity/protocol/IDENTITY_DISCOVERY.md`.

## Dual-track governance model

### Track A: hard guardrails

Non-bypassable constraints:
- compliance and legal boundaries
- rejection memory constraints
- media integrity constraints
- escalation triggers

### Track B: adaptive growth

Continuously updated strategy:
- failed-case pattern extraction
- hypothesis -> experiment -> replay
- skill and prompt tuning proposals

## Runtime state requirements (CURRENT_TASK.json)

Minimum required blocks:
- `objective`
- `state_machine`
- `gates`
- `source_of_truth`
- `escalation_policy`
- `required_artifacts`
- `post_execution_mandatory`

## Conflict resolution

Priority order:
1. Canon/hard guardrails
2. CURRENT_TASK runtime contract
3. Skill instructions
4. MCP/tool preference

## Email escalation policy

Email is only for offline blocking actions. Non-blocking updates are routed to logs or dashboards.
