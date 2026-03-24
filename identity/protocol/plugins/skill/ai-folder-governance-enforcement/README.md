# ai-folder-governance-enforcement

This plugin wires file governance skill enforcement into required gates.

## Foundational philosophy inheritance

1. This plugin inherits `identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` as the source for governed adaptation and fail-close semantics.
2. It inherits `identity/protocol/IDENTITY_RUNTIME.md` for runtime authority boundaries.

## Contract

- requirement_key: `asb16-rq-020`
- bundle_target_name: `skill_path_integrity`
- validator: `scripts/validate_skill_path_integrity.py`
- integration_kind: `skill`
- protocol_contract_root: `identity/protocol/plugins/skill`
- instance_runtime_root: `.identity/{identity_id}/runtime/plugins/skills`

Source of truth and wiring constraints are governed by `PLUGIN_WIRING_PLAYBOOK.current.md`.

## Runtime adjudication boundary

1. This README records frozen extension law for folder-governance skill wiring; it is not the final surface for current-turn legality.
2. Current-turn legality must resolve from registry/mapping bindings, `scripts/validate_skill_path_integrity.py`, runtime state, and receipts.

## Truth lifecycle note

1. `truth_exists`: the skill contract exists.
2. `truth_discoverable`: plugin registry and skill runtime roots expose it.
3. `truth_admissible`: the required-gate and mapping surfaces admit it for the turn.
4. `truth_bound`: the current run binds to the governed skill path evidence.
5. `truth_consumed`: the next operational step actually uses that evidence in enforcement.
