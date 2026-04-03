#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

PROJECTION_PROFILE_EXCLUSION_SCOPE_CLASS = "bounded_projection_profile_exclusion"
PROJECTION_PROFILE_EXCLUSION_SCOPE_REASON = "projection_profile_out_of_scope"
PROJECTION_PROFILE_EXCLUSION_SCOPE_MODE = "projection_profile_bounded"

PROJECTION_PROFILE_EXCLUSION_SCOPE_MARKER = (
    "projection_profile_exclusion_scope="
    "projection_skip_status=SKIPPED_NOT_REQUIRED|"
    "projection_skip_scope_class=bounded_projection_profile_exclusion|"
    "projection_skip_scope_reason=projection_profile_out_of_scope|"
    "projection_excluded_area"
)
PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    PROJECTION_PROFILE_EXCLUSION_SCOPE_MARKER,
)


def build_projection_profile_exclusion_reason(*, area: str, profile_id: str) -> str:
    return f"projection_profile_excludes_{str(area or '').strip()}:{str(profile_id or '').strip()}"


def build_projection_profile_exclusion_payload(
    *,
    profile_id: str,
    execution_mode: str,
    description: str,
    excluded_area: str,
    owner_surface: str,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = dict(extra_fields or {})
    payload.update(
        {
            "projection_profile": str(profile_id or "").strip(),
            "projection_profile_execution_mode": str(execution_mode or "").strip(),
            "projection_profile_description": str(description or "").strip(),
            "projection_skip_status": STATUS_SKIPPED_NOT_REQUIRED,
            "projection_skip_reason": build_projection_profile_exclusion_reason(
                area=excluded_area,
                profile_id=profile_id,
            ),
            "projection_skip_scope_class": PROJECTION_PROFILE_EXCLUSION_SCOPE_CLASS,
            "projection_skip_scope_reason": PROJECTION_PROFILE_EXCLUSION_SCOPE_REASON,
            "projection_skip_scope_mode": PROJECTION_PROFILE_EXCLUSION_SCOPE_MODE,
            "projection_excluded_area": str(excluded_area or "").strip(),
            "projection_owner_surface": str(owner_surface or "").strip(),
            "stale_reasons": [],
        }
    )
    return payload
