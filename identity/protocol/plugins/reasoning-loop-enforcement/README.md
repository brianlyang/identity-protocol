# Reasoning Loop Enforcement Plugin

This plugin hardens the `Reasoning loop contract` into a protocol-level fail-close gate.

## Foundational philosophy inheritance

1. This plugin inherits `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` as the semantic source for fail-close enforcement and lifecycle closure.
2. It inherits `identity/protocol/IDENTITY_RUNTIME.md` for current-run authority boundaries.

## Contract

- Requirement key: `asb16-rq-035`
- Bundle target name: `reasoning_loop_failclose_enforcement`
- Contract id: `rq_035_reasoning_loop_failclose_contract_v1`
- Validator: `scripts/validate_reasoning_loop_failclose.py`
- Wiring playbook: `identity/protocol/plugins/PLUGIN_WIRING_PLAYBOOK.current.md`

## Enforcement levels

- `L0`: wiring presence only (compatibility seed mode)
- `L1`: mandatory attempt trace integrity
- `L2`: L1 + four-track evidence refs (`roundtable/vendor/network/reference`)
- `L3`: L2 + external freshness/reconciliation source constraints

## Hard semantics

- done-transition blocking is controlled by `no_target_completion_mode`:
  - default `terminal_attempt_only`: terminal unresolved attempt cannot transition to completion/done.
  - optional `any_attempt`: any historical `no_target_reached=true` blocks completion/done.
- `done_requires_terminal_target_reached=true` keeps strict closure for unresolved terminal completion.
- Failed attempts must carry `next_action`.
- Escalation threshold mode is config-driven via `escalation_requirement_mode` (default `at_or_exceed`).
- Generic retry `next_action` text is not escalation by default; escalation requires boolean/token markers or non-empty escalation refs.
- Escalation accepts boolean/token signals and configurable non-empty reference fields when enabled.
- Strict operations use `strict_run_id_binding=true`: once a `run_id` is provided, runtime proof must stay on the same run id even if report source falls back; mismatch is fail-close (`IP-RL-RUN-006`).
- Runtime proof source selection is config-driven by `runtime_report_selection_mode` (`prefer_run_id` default, optional `latest_first`), so strict lanes do not depend on explicit `report_selected_path` in normal cases.

## Runtime adjudication boundary

1. This README freezes reasoning-loop extension law; it is not by itself a current-turn legality surface.
2. Current-turn legality must resolve from `scripts/validate_reasoning_loop_failclose.py`, machine-consumed mappings, runtime state, and receipts.

## Truth lifecycle note

1. `truth_exists`: the reasoning-loop contract exists.
2. `truth_discoverable`: the plugin registry and bound runtime surfaces expose it.
3. `truth_admissible`: the requirement/gate stack accepts it as authoritative for the turn.
4. `truth_bound`: run-bound evidence stays attached to the current run.
5. `truth_consumed`: the next operational step consumes that bound evidence instead of treating it as inert prose.
