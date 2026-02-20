# Identity Trigger Regression Contract v1.2.5

## Goal

Define a deterministic trigger-regression contract for identity updates, mirroring mature skill protocol practice.

This contract prevents two classes of failures:
- over-trigger: identity routes/actions fire in unrelated cases
- under-trigger: identity fails to route/update when capability gap is present

## Contract scope

Applies when any of the following change:
- identity routing policy (`routing_contract`)
- update trigger policy (`identity_update_lifecycle_contract.trigger_contract`)
- gate semantics that affect route/update behavior
- identity-creator update-operation logic

## Required suites

Every trigger regression record MUST include three suites:

1. `positive_cases`
   - expected to trigger update/routing behavior
2. `boundary_cases`
   - near-boundary prompts/tasks, expected deterministic route decision
3. `negative_cases`
   - must not trigger update/routing behavior

## Required fields per case

Each case entry MUST include:
- `case_id`
- `input_summary`
- `expected_route`
- `expected_trigger` (true/false)
- `observed_route`
- `observed_trigger` (true/false)
- `result` (`PASS` | `FAIL`)
- `notes`

## Runtime key contract

`CURRENT_TASK.json` MUST include `trigger_regression_contract`:

- `required`: true
- `required_suites`: [`positive_cases`, `boundary_cases`, `negative_cases`]
- `result_enum`: [`PASS`, `FAIL`]
- `sample_report_path_pattern`: `identity/runtime/examples/*trigger-regression*.json`
- `fail_action`: `block_merge_and_reenter_identity_update`

## Validation requirements

The following validator MUST pass:
- `scripts/validate_identity_trigger_regression.py --identity-id <id>`

And MUST be included in:
- e2e smoke workflow
- update lifecycle validation chain

## Merge/release policy

If any suite or case fails:
- merge is blocked
- release tag must not be advanced
- identity update loop must continue with patch + replay

## Alignment note

This contract intentionally mirrors skill update regression discipline:
`trigger -> patch surface -> validation -> replay`

Identity keeps scenario-agnostic protocol semantics, while runtime packs implement concrete business routes.
