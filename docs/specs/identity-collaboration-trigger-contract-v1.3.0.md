# Identity Collaboration Trigger Contract v1.3.0

Status: Draft
Updated: 2026-02-21

## Purpose

Standardize mandatory human-collaboration trigger behavior (skill-like strictness) so identity runtime cannot silently stall on login/captcha/session/manual-verification blockers.

## Required runtime keys

`CURRENT_TASK.json` MUST include:

- `gates.collaboration_trigger_gate = "required"`
- `blocker_taxonomy_contract`
- `collaboration_trigger_contract`

## Blocker taxonomy contract

`blocker_taxonomy_contract.required_blocker_types` MUST include:

- `login_required`
- `captcha_required`
- `session_expired`
- `manual_verification_required`

`blocker_taxonomy_contract.blocker_classification_required_fields` MUST include:

- `blocker_type`
- `source`
- `detected_at`
- `requires_human_collab`
- `next_action`

## Collaboration trigger contract

Minimum required fields:

- `hard_rule`
- `trigger_conditions[]`
- `notify_policy`
- `notify_timing` (must be `immediate`)
- `notify_channel` (default `ops-notification-router`)
- `dedupe_window_hours` (>0)
- `state_change_bypass_dedupe=true`
- `must_emit_receipt_in_chat=true`
- `receipt_required_fields[]`
- `evidence_log_path_pattern`
- `minimum_evidence_logs_required`
- `max_log_age_days`
- `validator`

## Evidence log minimum schema

Each collaboration log record MUST include:

- `identity_id`
- `task_id`
- `blocker_type`
- `source`
- `detected_at`
- `requires_human_collab`
- `notify_channel`
- `notified_at`
- `notify_status`
- `dedupe_key`
- `state_change_bypass_dedupe`
- `chat_receipt` (with required receipt fields)
- `next_action`

## Validation and CI gate

Validator:

- `scripts/validate_identity_collab_trigger.py`

CI required gate chain MUST call:

```bash
python3 scripts/validate_identity_collab_trigger.py --identity-id <id> --self-test
```

No collaboration-trigger pass -> no merge/no release for affected identity updates.
