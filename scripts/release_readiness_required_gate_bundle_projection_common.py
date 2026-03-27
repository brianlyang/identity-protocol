#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS: tuple[tuple[str, str], ...] = (
    ("report_selected_path", "required_gate_bundle_report_selected_path"),
    ("report_selection_mode", "required_gate_bundle_report_selection_mode"),
    ("report_selected_authority_class", "required_gate_bundle_report_authority_class"),
    ("report_pointer_resolution_mode", "required_gate_bundle_report_pointer_resolution_mode"),
    ("report_pointer_path", "required_gate_bundle_report_pointer_path"),
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "required_gate_bundle_status",
    "required_gate_bundle_projection_status",
    "required_gate_bundle_scope_class",
    "required_gate_bundle_scope_reason",
    "failed_required_target_count",
    "failed_target_names",
    "projection_stale_reasons",
    "rows_without_projected_report_fields",
    "missing_mapping_requirements",
    *(target for _, target in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS),
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER = (
    "required_gate_bundle_projection="
    + "|".join(f"one_look.{field}" for field in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_FIELDS)
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    *(f"one_look.{field}" for field in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_FIELDS),
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


def build_release_readiness_required_gate_bundle_one_look_projection(bundle: dict[str, Any]) -> dict[str, Any]:
    source = bundle if isinstance(bundle, dict) else {}
    projection: dict[str, Any] = {
        "required_gate_bundle_status": _clean_str(source.get("bundle_status")).upper() or STATUS_UNKNOWN,
        "required_gate_bundle_projection_status": _clean_str(source.get("projection_status")).upper()
        or STATUS_UNKNOWN,
        "required_gate_bundle_scope_class": _clean_str(source.get("scope_class")),
        "required_gate_bundle_scope_reason": _clean_str(source.get("scope_reason")),
        "failed_required_target_count": _safe_int(source.get("failed_required_target_count")),
        "failed_target_names": _clean_list(source.get("failed_target_names")),
        "projection_stale_reasons": _clean_list(source.get("projection_stale_reasons")),
        "rows_without_projected_report_fields": _clean_list(source.get("rows_without_projected_report_fields")),
        "missing_mapping_requirements": _clean_list(source.get("missing_mapping_requirements")),
    }
    for source_field, target_field in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS:
        projection[target_field] = _clean_str(source.get(source_field))
    return projection


def apply_release_readiness_required_gate_bundle_one_look(summary: dict[str, Any], one_look: dict[str, Any]) -> None:
    if not isinstance(one_look, dict):
        return
    bundle = summary.get("required_gate_bundle") if isinstance(summary, dict) else {}
    one_look.update(build_release_readiness_required_gate_bundle_one_look_projection(bundle or {}))
