# Reasoning Loop Enforcement Plugin

This plugin hardens the `Reasoning loop contract` into a protocol-level fail-close gate.

## Contract

- Requirement key: `asb16-rq-035`
- Contract id: `rq_035_reasoning_loop_failclose_contract_v1`
- Validator: `scripts/validate_reasoning_loop_failclose.py`

## Enforcement levels

- `L0`: wiring presence only (compatibility seed mode)
- `L1`: mandatory attempt trace integrity
- `L2`: L1 + four-track evidence refs (`roundtable/vendor/network/reference`)
- `L3`: L2 + external freshness/reconciliation source constraints

## Hard semantics

- `no_target_reached=true` cannot transition to completion/done.
- Failed attempts must carry `next_action`.
- Beyond `max_attempts_before_escalation`, escalation signal is mandatory.
