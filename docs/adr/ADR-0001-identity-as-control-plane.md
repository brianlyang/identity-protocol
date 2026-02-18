# ADR-0001: Identity as Control Plane Parallel to Skills and MCP

- Status: Accepted
- Date: 2026-02-18

## Context

Agent capability scaled rapidly via skills and MCP. Operational reliability lagged without explicit governance and runtime identity state.

## Decision

Adopt identity as a first-class control-plane protocol with three layers:
1. Canon / governance layer
2. Identity prompt / cognition layer
3. Runtime task contract (`CURRENT_TASK.json`)

Keep skills and MCP as execution/capability planes.

## Consequences

Positive:
- deterministic conflict resolution
- durable runtime state
- explicit escalation boundaries
- reproducible role activation

Tradeoffs:
- requires registry and validation scripts
- requires disciplined updates of runtime state and history

## Guardrails

Conflict order:
1. Canon/hard guardrails
2. Runtime contract
3. Skill instructions
4. Tool preferences
