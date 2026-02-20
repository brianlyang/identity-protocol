# Identity Protocol v1.2.5 (draft)

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

## Protocol baseline review contract (v1.2.3+)

To avoid identity-level drift and unsupported architectural conclusions, identity upgrades MUST include baseline protocol review evidence.

When task intent involves identity-capability upgrades or architecture decisions:

- `gates.protocol_baseline_review_gate` MUST be `required`.
- `protocol_review_contract` MUST exist in CURRENT_TASK and include:
  - `must_review_sources` (required canonical references)
  - `required_evidence_fields`
  - `evidence_report_path_pattern`

A valid review evidence record MUST include, at minimum:
- review id/time/reviewer
- purpose
- reviewed source list
- findings
- decision

## Identity update lifecycle contract (v1.2.4+)

To match skill update discipline (`trigger -> patch -> validate -> replay`), identity updates MUST define and pass an explicit lifecycle contract.

When runtime detects operational failure or capability gap:

- `gates.identity_update_gate` MUST be `required`.
- `identity_update_lifecycle_contract` MUST exist in CURRENT_TASK and include:
  - `trigger_contract` (when update is mandatory)
  - `patch_surface_contract` (what files/contracts must be changed)
  - `validation_contract` (which checks must pass)
  - `replay_contract` (same-case regression requirements)

Mandatory patch surfaces:
- `CURRENT_TASK.json`
- `IDENTITY_PROMPT.md`
- `RULEBOOK.jsonl`
- `TASK_HISTORY.md`

Mandatory validators:
- `scripts/validate_identity_runtime_contract.py`
- `scripts/validate_identity_upgrade_prereq.py`
- `scripts/validate_identity_update_lifecycle.py`

No replay pass -> no identity learning completion.

## Identity trigger regression contract (new in v1.2.5)

To mirror mature skill trigger stability practice, identity route/update changes MUST pass trigger regression.

When routing, trigger conditions, or update gates are modified:

- `trigger_regression_contract` MUST exist in CURRENT_TASK.
- Required suites:
  - `positive_cases`
  - `boundary_cases`
  - `negative_cases`
- Each suite requires deterministic expected/observed route + trigger result.

Mandatory validator:
- `scripts/validate_identity_trigger_regression.py`

No trigger-regression pass -> no identity update completion/merge.

## Skill + MCP + Tool collaboration contract (new baseline in v1.2.5)

Identity capability decisions MUST align with collaboration boundaries:

- skill = strategy constraints (sequence/validation/fallback)
- MCP = capability access surface (registered tools)
- tool = concrete execution action

Identity must never assume:
- skill automatically grants external permissions
- skill trigger implies MCP/tools are necessarily available

Collaboration baseline reference:
- `docs/references/skill-mcp-tool-collaboration-contract-v1.0.md`

## Dual-track governance model

### Track A: hard guardrails

Non-bypassable constraints:
- compliance and legal boundaries
- rejection memory constraints
- media integrity constraints
- escalation triggers
- protocol baseline review gate for identity-upgrade decisions
- identity update lifecycle gate for runtime evolution decisions
- trigger regression gate for route/update changes

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

Conditional required blocks:
- `protocol_review_contract` (identity upgrade tasks)
- `identity_update_lifecycle_contract` (runtime evolution / update tasks)
- `trigger_regression_contract` (routing/trigger/update gate changes)

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
- Identity conclusions for protocol upgrades must be source-cited and evidence-backed.
- Identity updates must follow explicit trigger/patch/validate/replay lifecycle, mirroring skill update discipline.
- Identity route/update behavior must pass positive/boundary/negative trigger regression.
- Identity review must include skill+mcp+tool collaboration boundary checks.

## Email escalation policy

Email is only for offline blocking actions. Non-blocking updates are routed to logs or dashboards.
