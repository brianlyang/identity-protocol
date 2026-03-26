#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

KNOWN_STATUS_VALUES: tuple[str, ...] = (
    STATUS_PASS_REQUIRED,
    STATUS_SKIPPED_NOT_REQUIRED,
    STATUS_FAIL_REQUIRED,
    STATUS_FAIL_OPTIONAL,
    STATUS_WARN_NON_BLOCKING,
)

SCRIPT_STATUS_FIELD_CANDIDATES: dict[str, tuple[str, ...]] = {
    "scripts/validate_identity_weak_live_linkage.py": (
        "overall_linkage_status",
        "identity_weak_live_linkage_status",
    ),
}

TARGET_STATUS_FIELD_CANDIDATES: dict[str, tuple[str, ...]] = {
    "identity_weak_live_linkage": (
        "overall_linkage_status",
        "identity_weak_live_linkage_status",
    ),
}


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def resolve_status_field_candidates(
    *,
    script: str = "",
    target_name: str = "",
    default_field: str = "",
) -> tuple[str, ...]:
    candidates: list[str] = []
    for field in TARGET_STATUS_FIELD_CANDIDATES.get(clean_string(target_name), ()):
        token = clean_string(field)
        if token and token not in candidates:
            candidates.append(token)
    for field in SCRIPT_STATUS_FIELD_CANDIDATES.get(clean_string(script), ()):
        token = clean_string(field)
        if token and token not in candidates:
            candidates.append(token)
    token = clean_string(default_field)
    if token and token not in candidates:
        candidates.append(token)
    return tuple(candidates)


def resolve_projected_status_value(
    payload: dict[str, Any],
    *,
    script: str = "",
    target_name: str = "",
    default_field: str = "",
) -> tuple[str, str]:
    candidates = resolve_status_field_candidates(
        script=script,
        target_name=target_name,
        default_field=default_field,
    )
    if not isinstance(payload, dict):
        return "", (candidates[0] if candidates else clean_string(default_field))
    for field in candidates:
        status_value = clean_string(payload.get(field)).upper()
        if status_value in KNOWN_STATUS_VALUES:
            return status_value, field
    return "", (candidates[0] if candidates else clean_string(default_field))
