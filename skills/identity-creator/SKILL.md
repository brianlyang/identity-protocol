---
name: identity-creator
description: Design, scaffold, validate, and evolve an identity control-plane package that is parallel to skills and MCP. Use when the user asks to create or update identity architecture, identity metadata registry, runtime identity contracts, or identity-creator standards.
metadata:
  short-description: Create or update identity protocol and packs
---

# Identity Creator

Create and maintain identity as a first-class control-plane protocol.

## Use this skill when

- The user asks to create/update identity architecture.
- The project needs role governance beyond skill-only workflows.
- You need a standardized identity registry with title/description metadata.
- You need deterministic runtime contracts (`CURRENT_TASK.json`) and lifecycle rules.

## Do not use this skill when

- The request is only to build a single task skill with no role-control requirements.
- The request only touches MCP server connectivity.
- The request is pure business content editing with no protocol/governance impact.

## Protocol objectives

1. Keep identity parallel to skills and MCP (same architectural tier).
2. Keep hard guardrails and adaptive learning as dual tracks.
3. Keep runtime state as single source of truth.
4. Keep compatibility with official Codex config and skill standards.
5. Enforce source-backed protocol baseline review before identity-upgrade conclusions.

## Required outputs

- Identity protocol docs under `identity/protocol/`.
- Identity metadata registry under `identity/catalog/`.
- Identity pack files (`IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, `TASK_HISTORY.md`, `META.yaml`, `RULEBOOK.jsonl`).
- Runtime brief at `identity/runtime/IDENTITY_COMPILED.md`.
- Project config integration in `.codex/config.toml`.

## Workflow

### 1) Audit and align with standards

- Compare against local `skill-creator` principles:
  - concise metadata
  - progressive disclosure
  - deterministic resources
- Cross-check official docs for:
  - Codex skills structure and discovery
  - AGENTS instruction chain precedence
  - config layering and security controls
  - MCP specification baseline

Use references:
- `references/standards-alignment.md`
- `references/protocol-baseline-review.md`

### 2) Define identity protocol contract

- Establish dual tracks:
  - hard guardrails (non-bypassable)
  - adaptive growth (iterative learning)
- Define lifecycle:
  - register -> activate -> execute -> learn -> update
- Define conflict priority:
  - canon > runtime state > skill > tool preference
- For identity-upgrade scopes, require:
  - `gates.protocol_baseline_review_gate = required`
  - `protocol_review_contract` with mandatory sources + evidence fields

Use references:
- `references/identity-protocol-v1.md`

### 3) Scaffold identity package

- Use `scripts/init_identity_pack.sh` to generate a new pack scaffold.
- This scaffold includes:
  - `agents/identity.yaml`
  - ORRL-ready runtime skeleton
  - `protocol_baseline_review_gate` and `protocol_review_contract`
  - review evidence sample under `identity/runtime/examples/`
- For deterministic/automated creation, use root script `scripts/create_identity_pack.py`
  from repository root.
- Register identity in `identity/catalog/identities.yaml`.
- Ensure title/description and capability bindings are explicit.

### 4) Update existing identities (mandatory)

When modifying an existing identity (e.g. store-manager / audit-officer), treat it as an **update operation** just like `skill-creator` update flow:

1. Run baseline review first (identity-protocol + skills + MCP references).
2. Update `CURRENT_TASK.json` contracts/gates and affected docs.
3. Run validation gates in order:
   - `scripts/validate_identity_runtime_contract.py`
   - `scripts/validate_identity_upgrade_prereq.py --identity-id <id>`
4. Only after both pass, continue to merge/release decisions.

### 5) Validate runtime contracts

- Use `scripts/validate_identity_protocol.sh` to verify required files and runtime keys.
- Use `scripts/validate_identity_manifest.py` to validate identity manifest semantics.
- Use `scripts/test_identity_discovery_contract.py` to verify local `identity/list` draft output.
- Use `scripts/check_codex_config_paths.py` to verify `.codex/config.toml` path resolution.
- Use `scripts/validate_identity_runtime_contract.py` to enforce:
  - required gates
  - protocol baseline review evidence completeness
  - mandatory source coverage

### 6) Compile runtime brief and integrate config

- Build/update `identity/runtime/IDENTITY_COMPILED.md` from active identity.
- Ensure `.codex/config.toml` points `model_instructions_file` to compiled brief.
- Keep skills and MCP configured via native Codex keys.

### 7) Record operational guidance

- Produce a runbook with:
  - operator steps
  - failure modes
  - rollback instructions
- Include repository strategy recommendation (single repo vs dedicated repo).

Use references:
- `references/implementation-runbook.md`
- `references/github-repo-strategy.md`

## Quality gates

- Identity registry has valid schema shape.
- Active identity exists and pack path resolves.
- Runtime contract is complete and parseable.
- Protocol baseline review gate is present for identity-upgrade scopes.
- Baseline review evidence cites identity-protocol + skill + mcp standards.
- Compiled runtime brief is concise and current.
- No conflict with existing skills/MCP config.

## Notes

- Identity is currently a project extension protocol; Codex has no native `identity` config key.
- Integrate through native hooks:
  - AGENTS/model instructions
  - config precedence
  - skills + MCP native configuration
