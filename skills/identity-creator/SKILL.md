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

## Required outputs

- Identity protocol docs under `identity/protocol/`.
- Identity metadata registry under `identity/catalog/`.
- Identity pack files (`IDENTITY_PROMPT.md`, `CURRENT_TASK.json`, `TASK_HISTORY.md`, `META.yaml`).
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

Use references:
- `references/standards-alignment.md`

### 2) Define identity protocol contract

- Establish dual tracks:
  - hard guardrails (non-bypassable)
  - adaptive growth (iterative learning)
- Define lifecycle:
  - register -> activate -> execute -> learn -> update
- Define conflict priority:
  - canon > runtime state > skill > tool preference

Use references:
- `references/identity-protocol-v1.md`

### 3) Scaffold identity package

- Use `scripts/init_identity_pack.sh` to generate a new pack scaffold.
- Register identity in `identity/catalog/identities.yaml`.
- Ensure title/description and capability bindings are explicit.

### 4) Validate runtime contracts

- Use `scripts/validate_identity_protocol.sh` to verify required files and runtime keys.
- Use `scripts/check_codex_config_paths.py` to verify `.codex/config.toml` path resolution.
- Ensure runtime task contains mandatory blocks:
  - `objective`
  - `state_machine`
  - `gates`
  - `source_of_truth`
  - `escalation_policy`

### 5) Compile runtime brief and integrate config

- Build/update `identity/runtime/IDENTITY_COMPILED.md` from active identity.
- Ensure `.codex/config.toml` points `model_instructions_file` to compiled brief.
- Keep skills and MCP configured via native Codex keys.

### 6) Record operational guidance

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
- Compiled runtime brief is concise and current.
- No conflict with existing skills/MCP config.

## Notes

- Identity is currently a project extension protocol; Codex has no native `identity` config key.
- Integrate through native hooks:
  - AGENTS/model instructions
  - config precedence
  - skills + MCP native configuration
