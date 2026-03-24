# Agent Handoff Contract

## Document positioning

This file is a root-domain contract law file inside `identity/protocol/`.

It exists to freeze the concrete machine-law rules for governed handoff between
master and sub agents.

It is not:

1. an operator tutorial;
2. a workspace-local execution memo;
3. a stream-closure narrative;
4. a substitute for machine-consumed adjudication surfaces such as validators,
   runtime logs, or receipts.

## Root-law scope and non-goals

1. This file freezes root-domain handoff law for governed coordination between master and sub agents.
2. It is not an execution playbook for any single stream, workspace, or business scenario.
3. It is not a substitute for constitutional law in `IDENTITY_PROTOCOL.md` / `IDENTITY_RUNTIME.md`.
4. It must not be treated as a current-turn success receipt or as a shortcut around machine-consumed handoff evidence.

## Purpose

Define a strict, auditable handoff protocol between master and sub agents to prevent scope drift.

This contract is identity-level control-plane policy and is scenario-agnostic.

## Foundational design philosophy anchor

This handoff contract inherits its bottom-theory assumptions from:

- `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`

Interpretive boundary:

1. the design philosophy explains why identity protocol treats handoff as machine-law coordination rather than informal collaboration;
2. this file freezes the concrete handoff law: role boundaries, payload fields, evidence requirements, validation, and merge blocking;
3. this file is authoritative for root-domain handoff law, but current-turn legality is still adjudicated through machine-consumed validators, logs, and receipts;
4. philosophical grounding does not replace the fail-close authority of this contract.

## Constitutional inheritance and authority boundary

This root-domain handoff contract lives beneath the constitutional layer defined by:

- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

Constitutional inheritance rule:

1. `IDENTITY_PROTOCOL.md` freezes the shared-law boundaries for delegation, ownership split, escalation, and protocol-governed control loops that handoff must preserve.
2. `IDENTITY_RUNTIME.md` freezes how governed handoff becomes embodied in runtime execution, evidence production, and merge/replay blocking.
3. this file freezes the root-domain handoff contract that must be obeyed by orchestrators, validators, and replay lanes without scenario-specific reinterpretation.
4. root-contract authority must not be collapsed into either philosophical primacy or present-turn runtime verdict.

## Machine-world audience

This contract is written primarily for:

- identity instances;
- launchers and orchestrators;
- validators and probes;
- runtime gates;
- protocol maintainers acting on behalf of machine truth.

It is not optimized as a human-memory aid. Its job is to make handoff law
stable enough for machine-world consumption.

## Runtime adjudication boundary

This file does not itself decide whether a concrete handoff was legal in the present turn.

Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces such as:

1. governed handoff validators and probes;
2. runtime logs, evidence artifacts, and receipts produced for the current run;
3. merge/replay gates that fail-close on missing or contradictory evidence.

So this file freezes handoff law, while runtime adjudication determines whether that law has actually been satisfied in execution.

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

## Production + sample dual-track validation

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
