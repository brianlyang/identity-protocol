# Identity Protocol v1.2.2 (draft)

## Goal

Define identity as a first-class control-plane protocol, parallel to skills and MCP.

- **Skills**: capability packaging and reusable procedures.
- **MCP**: tool transport and execution surface.
- **Identity**: role cognition, governance boundaries, decision loop, and learning closure.

This protocol is scenario-agnostic by design.

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

Optional metadata blocks per identity:
- `interface` (display_name, short_description, default_prompt)
- `policy` (allow_implicit_activation, activation_priority, conflict_resolution)
- `dependencies` (tool/env/network/filesystem requirements)
- `observability` (event_topics, required_artifacts)

See discovery draft: `identity/protocol/IDENTITY_DISCOVERY.md`.

## Four core capability contracts

Identity protocol must be verifiable against four capability contracts:

1. **Accurate judgement contract**
   - Requires multimodal evidence consistency checks.
   - Inconsistent evidence cannot transition to `done`.

2. **Reasoning loop contract**
   - Requires hypothesis/patch/result trace per attempt.
   - "No-target-reached" cannot be treated as completion.

3. **Auto-routing contract**
   - Requires problem-type routing map and route-switch policy.
   - When uncertainty persists, route discovery must execute (identity/skill/tool).

4. **Rule learning contract**
   - Requires append-only rulebook linkage to run evidence.
   - Requires both negative and positive rule accumulation over time.

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
- `evaluation_contract`
- `reasoning_loop_contract`
- `routing_contract`
- `rulebook_contract`

## Conflict resolution

Priority order:
1. Canon/hard guardrails
2. CURRENT_TASK runtime contract
3. Skill instructions
4. MCP/tool preference

## Alignment with skill and MCP protocol patterns

To reduce protocol drift and avoid ad-hoc logic:
- Identity must remain declarative and schema-verifiable (like skill metadata discipline).
- Runtime decisions must be contract-driven and testable (like MCP interface determinism).
- Discovery, validation, and release gates must be explicit and automated.

## Email escalation policy

Email is only for offline blocking actions. Non-blocking updates are routed to logs or dashboards.
