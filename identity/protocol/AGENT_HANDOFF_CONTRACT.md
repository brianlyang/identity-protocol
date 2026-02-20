# Agent Handoff Contract (Master/Sub) v1.0

## Purpose

Define a strict, auditable handoff protocol between master and sub agents to prevent scope drift.

This contract is identity-level control plane policy and is scenario-agnostic.

---

## Core principles

1. identity = direction and constraints
2. skill = process and strategy
3. mcp/tool = capability execution
4. failures must be attributed to one layer before patching

---

## Role boundaries

### Master responsibilities (only)

1. objective decomposition and completion criteria
2. routing decisions (which sub-agent, why)
3. gate decision (allow/deny next phase)
4. audit closeout (evidence acceptance)

### Sub responsibilities (only)

1. execute within assigned scope
2. emit structured evidence output
3. report failure via hypothesis/patch/result
4. do not mutate global identity contracts

---

## Mandatory handoff payload fields

Each handoff record MUST include:

- `handoff_id`
- `task_id`
- `from_agent`
- `to_agent`
- `input_scope`
- `actions_taken`
- `artifacts`
- `result`
- `next_action`
- `rulebook_update`

Missing any required field = invalid delivery.

---

## Violation definitions

The following are contract violations:

1. sub-agent modifies identity top-level contracts (`gates`, lifecycle contracts, protocol review contracts)
2. handoff claims completion without evidence artifacts
3. handoff lacks executable next action
4. handoff result contradicts provided evidence

---

## Evidence contract

- each artifact item should include `path` and `kind`
- artifact path must be readable from repo context
- `rulebook_update.evidence_run_id` required when `rulebook_update.applied=true`

---

## Result and next-action contract

`result` allowed values:
- `PASS`
- `FAIL`
- `BLOCKED`

`next_action` must include:
- `owner`
- `action`
- `input`

---

## Validation

Use:
- `scripts/validate_agent_handoff_contract.py --identity-id <id>`

Recommended CI mode:
- run handoff validator for active identities
- run positive and negative samples in self-test mode

---

## Merge policy

If handoff validation fails:
- identity update merge is blocked
- return to update loop
- replay is required after fix
