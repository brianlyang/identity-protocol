# Handoff Log SLA (v1.2.10)

## Decision

Adopt **strict mode** for handoff log freshness:

- keep `max_log_age_days = 7` as a hard gate
- require at least one fresh production handoff log in repo within the last 7 days

This matches control-plane intent: runtime evidence must be alive, not frozen samples.

## Why strict mode

1. Prevents sample-only false confidence.
2. Forces continuous production observability.
3. Keeps multi-agent routing metrics grounded in recent runs.

## Operational requirement

- Every week, maintainers must commit at least one new file under:
  - `identity/runtime/logs/handoff/*.json`
- The log must include:
  - `generated_at` (ISO-8601, UTC recommended)
  - `identity_id`
  - `task_id`
  - all fields required by `agent_handoff_contract.required_fields`

## Recommended cadence

- Weekly governance cadence: **Friday UTC** refresh.
- If no real incident occurred, create a controlled replay handoff log that still follows production schema.

## Fast operator runbook

1. Generate a fresh template:
   - `python scripts/create_handoff_log_template.py --identity-id store-manager`
2. Fill business-specific fields (`to_agent`, `input_scope`, actions, artifacts, next_action, result).
3. Commit log + referenced artifacts.
4. Open PR; required gates validate freshness and consistency.

## Failure handling

If CI fails with stale handoff logs:

1. Add a fresh production/replay handoff log.
2. Ensure `generated_at` is within 7 days.
3. Ensure `task_id` and `identity_id` match CURRENT_TASK and selected identity.
4. Re-run CI.
