#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

# Canonical L3 single egress contract.
FINAL_EMIT_CHANNEL_ID = "final_emit_governed"
FINAL_EMIT_POLICY_MODE = "tool_choice_required"
FINAL_EMIT_SCHEMA_ID = "hud_headstamp_final_emit_schema_v1"
FINAL_EMIT_SCHEMA_REQUIRED_FIELDS: tuple[str, ...] = (
    "identity_id",
    "actor_id",
    "work_layer",
    "source_layer",
    "lock_state",
    "run_id",
    "headstamp_text",
    "body_text",
)


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_status(value: Any) -> str:
    return normalize_text(value).upper()

