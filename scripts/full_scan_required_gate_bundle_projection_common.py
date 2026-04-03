#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_UNKNOWN = "UNKNOWN"

FULL_SCAN_REQUIRED_GATE_BUNDLE_THREE_PLANE_PASSTHROUGH_FIELDS: tuple[tuple[str, str], ...] = (
    ("actor_id", "{prefix}_actor_id"),
    ("resolved_work_layer", "{prefix}_resolved_work_layer"),
    ("resolved_source_layer", "{prefix}_resolved_source_layer"),
    ("lock_state", "{prefix}_lock_state"),
    ("run_id_binding", "{prefix}_run_id_binding"),
    ("report_selected_path", "{prefix}_report_selected_path"),
    ("report_logical_identity_key", "{prefix}_report_logical_identity_key"),
    ("report_selection_mode", "{prefix}_report_selection_mode"),
    ("report_selected_authority_class", "{prefix}_report_authority_class"),
    ("report_pointer_resolution_mode", "{prefix}_report_pointer_resolution_mode"),
    ("report_pointer_path", "{prefix}_report_pointer_path"),
)


def full_scan_required_gate_bundle_three_plane_fields(prefix: str) -> tuple[str, ...]:
    field_prefix = str(prefix or "").strip()
    return (
        f"{field_prefix}_status",
        f"{field_prefix}_projection_status",
        f"{field_prefix}_scope_class",
        f"{field_prefix}_scope_reason",
        f"{field_prefix}_failed_required_targets",
        f"{field_prefix}_failed_target_names",
        f"{field_prefix}_projection_stale_reasons",
        f"{field_prefix}_rows_without_projected_report_fields",
        f"{field_prefix}_missing_mapping_requirements",
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
FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_THREE_PLANE_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_three_plane_fields("required_gate_bundle_scan_probe")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_FIELDS: tuple[str, ...] = (
    "identities_with_projection",
    "projection_pass",
    "projection_fail",
    "projection_skipped_not_required",
    "projection_fail_identity_ids",
    "projection_scope_excluded_identity_ids",
    "projection_scope_classes",
    "projection_scope_reasons",
    "identities_with_failed_required_targets",
    "total_targets",
    "failed_required_targets",
    "failed_target_names",
    "failed_target_counts",
    "target_status_counts",
    "rows_without_projected_report_fields",
    "missing_mapping_requirements",
    "projection_stale_reasons",
)


def full_scan_required_gate_bundle_summary_field_refs(summary_key: str) -> tuple[str, ...]:
    summary_prefix = str(summary_key or "").strip()
    return tuple(f"{summary_prefix}.{field}" for field in FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_FIELDS)


FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_SUMMARY_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_summary_field_refs("summary_required_gate_bundle_projection")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_SUMMARY_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_summary_field_refs("summary_required_gate_bundle_shadow_projection")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_SUMMARY_FIELDS: tuple[str, ...] = (
    full_scan_required_gate_bundle_summary_field_refs("summary_required_gate_bundle_scan_probe_projection")
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER = (
    "full_scan_required_gate_bundle_projection="
    + "|".join(
        f"three_plane.{field}"
        for field in (
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_THREE_PLANE_FIELDS,
        )
    )
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER = (
    "full_scan_required_gate_bundle_summary="
    + "|".join(
        field
        for field in (
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_SUMMARY_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_SUMMARY_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_SUMMARY_FIELDS,
        )
    )
)
FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER,
    *(
        f"three_plane.{field}"
        for field in (
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_THREE_PLANE_FIELDS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_THREE_PLANE_FIELDS,
        )
    ),
    *FULL_SCAN_REQUIRED_GATE_BUNDLE_PRIMARY_SUMMARY_FIELDS,
    *FULL_SCAN_REQUIRED_GATE_BUNDLE_SHADOW_SUMMARY_FIELDS,
    *FULL_SCAN_REQUIRED_GATE_BUNDLE_SCAN_PROBE_SUMMARY_FIELDS,
)


def build_full_scan_required_gate_bundle_projection_summary_skeleton() -> dict[str, Any]:
    return {
        "identities_with_projection": 0,
        "projection_pass": 0,
        "projection_fail": 0,
        "projection_skipped_not_required": 0,
        "projection_fail_identity_ids": [],
        "projection_scope_excluded_identity_ids": [],
        "projection_scope_classes": [],
        "projection_scope_reasons": [],
        "identities_with_failed_required_targets": 0,
        "total_targets": 0,
        "failed_required_targets": 0,
        "failed_target_names": [],
        "failed_target_counts": {},
        "target_status_counts": {},
        "rows_without_projected_report_fields": [],
        "missing_mapping_requirements": [],
        "projection_stale_reasons": [],
    }


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
        f"{field_prefix}_status": _clean_str(source.get("bundle_status")).upper() or STATUS_UNKNOWN,
        f"{field_prefix}_projection_status": _clean_str(source.get("projection_status")).upper() or STATUS_UNKNOWN,
        f"{field_prefix}_scope_class": _clean_str(source.get("scope_class")),
        f"{field_prefix}_scope_reason": _clean_str(source.get("scope_reason")),
        f"{field_prefix}_failed_required_targets": _safe_int(source.get("failed_required_target_count")),
        f"{field_prefix}_failed_target_names": _clean_list(source.get("failed_target_names")),
        f"{field_prefix}_projection_stale_reasons": _clean_list(source.get("stale_reasons")),
        f"{field_prefix}_rows_without_projected_report_fields": _clean_list(
            source.get("rows_without_projected_report_fields")
        ),
        f"{field_prefix}_missing_mapping_requirements": _clean_list(source.get("missing_mapping_requirements")),
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
