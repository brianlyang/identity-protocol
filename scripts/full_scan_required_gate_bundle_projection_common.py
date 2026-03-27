#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_UNKNOWN = "UNKNOWN"

FULL_SCAN_REQUIRED_GATE_BUNDLE_THREE_PLANE_PASSTHROUGH_FIELDS: tuple[tuple[str, str], ...] = (
    ("actor_id", "{prefix}_actor_id"),
    ("resolved_work_layer", "{prefix}_resolved_work_layer"),
    ("resolved_source_layer", "{prefix}_resolved_source_layer"),
    ("lock_state", "{prefix}_lock_state"),
    ("report_selected_path", "{prefix}_report_selected_path"),
    ("report_selection_mode", "{prefix}_report_selection_mode"),
    ("report_selected_authority_class", "{prefix}_report_authority_class"),
    ("report_pointer_resolution_mode", "{prefix}_report_pointer_resolution_mode"),
    ("report_pointer_path", "{prefix}_report_pointer_path"),
)


def full_scan_required_gate_bundle_three_plane_fields(prefix: str) -> tuple[str, ...]:
    field_prefix = str(prefix or "").strip()
    return (
        f"{field_prefix}_projection_status",
        f"{field_prefix}_scope_class",
        f"{field_prefix}_scope_reason",
        f"{field_prefix}_failed_required_targets",
        f"{field_prefix}_failed_target_names",
        f"{field_prefix}_projection_stale_reasons",
        f"{field_prefix}_rows_without_projected_report_fields",
        *(
            target_template.format(prefix=field_prefix)
            for _source_field, target_template in FULL_SCAN_REQUIRED_GATE_BUNDLE_THREE_PLANE_PASSTHROUGH_FIELDS
        ),
    )


FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_THREE_PLANE_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_three_plane_fields("required_gate_bundle")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_THREE_PLANE_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_three_plane_fields("required_gate_bundle_shadow")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER = (
    "full_scan_required_gate_bundle_projection="
    + "|".join(
        f"three_plane.{field}"
        for field in (
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_THREE_PLANE_FIELDS,
        )
    )
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    *(
        f"three_plane.{field}"
        for field in (
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_THREE_PLANE_FIELDS,
        )
    ),
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _clean_str(item)
        if text:
            out.append(text)
    return out


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def build_full_scan_required_gate_bundle_three_plane_projection(
    projection: dict[str, Any],
    *,
    prefix: str = "required_gate_bundle",
) -> dict[str, Any]:
    source = projection if isinstance(projection, dict) else {}
    field_prefix = str(prefix or "").strip() or "required_gate_bundle"
    payload: dict[str, Any] = {
        f"{field_prefix}_projection_status": _clean_str(source.get("projection_status")).upper() or STATUS_UNKNOWN,
        f"{field_prefix}_scope_class": _clean_str(source.get("scope_class")),
        f"{field_prefix}_scope_reason": _clean_str(source.get("scope_reason")),
        f"{field_prefix}_failed_required_targets": _safe_int(source.get("failed_required_target_count")),
        f"{field_prefix}_failed_target_names": _clean_list(source.get("failed_target_names")),
        f"{field_prefix}_projection_stale_reasons": _clean_list(source.get("stale_reasons")),
        f"{field_prefix}_rows_without_projected_report_fields": _clean_list(
            source.get("rows_without_projected_report_fields")
        ),
    }
    for source_field, target_template in FULL_SCAN_REQUIRED_GATE_BUNDLE_THREE_PLANE_PASSTHROUGH_FIELDS:
        payload[target_template.format(prefix=field_prefix)] = _clean_str(source.get(source_field))
    return payload


def apply_full_scan_required_gate_bundle_three_plane_projection(
    target: dict[str, Any],
    projection: dict[str, Any],
    *,
    prefix: str = "required_gate_bundle",
) -> None:
    if not isinstance(target, dict):
        return
    target.update(build_full_scan_required_gate_bundle_three_plane_projection(projection, prefix=prefix))
