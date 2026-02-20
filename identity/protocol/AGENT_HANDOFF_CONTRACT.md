# Agent Handoff Contract v1.2.9 (draft)

## Purpose

Define a strict, auditable handoff protocol between master and sub agents to prevent scope drift.

This contract is identity-level control-plane policy and is scenario-agnostic.

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
- `rulebook_update.evidence_run_id` is required when `rulebook_update.applied=true`

---

## Production + sample dual-track validation (new in v1.2.9)

Handoff validation must run in two tracks:

1) Production track:
- validate runtime logs from production path, e.g.:
  - `identity/runtime/logs/handoff/*.json`
- enforce minimum log count
- enforce freshness (`generated_at` max age)
- enforce cross-file consistency (`task_id` + `identity_id`)

2) Sample track:
- run self-test fixtures under:
  - `identity/runtime/examples/handoff/positive/`
  - `identity/runtime/examples/handoff/negative/`

This prevents "sample always passes while runtime logs are unconstrained".

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
- `scripts/validate_agent_handoff_contract.py --identity-id <id> --self-test`

Recommended CI mode:
- validate production handoff logs from runtime path
- run positive and negative samples in self-test mode

Sample logs live in:
- `identity/runtime/examples/handoff/positive/`
- `identity/runtime/examples/handoff/negative/`

Production logs live in:
- `identity/runtime/logs/handoff/`

---

## Merge policy

If handoff validation fails:
- identity update merge is blocked
- return to update loop
- replay is required after fix
