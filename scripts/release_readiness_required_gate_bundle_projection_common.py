#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS: tuple[tuple[str, str], ...] = (
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


def release_readiness_required_gate_bundle_one_look_fields(prefix: str) -> tuple[str, ...]:
    field_prefix = str(prefix or "").strip()
    return (
        f"{field_prefix}_status",
        f"{field_prefix}_projection_status",
        f"{field_prefix}_scope_class",
        f"{field_prefix}_scope_reason",
        f"{field_prefix}_failed_required_target_count",
        f"{field_prefix}_failed_target_names",
        f"{field_prefix}_projection_stale_reasons",
        f"{field_prefix}_rows_without_projected_report_fields",
        f"{field_prefix}_missing_mapping_requirements",
        *(
            target_template.format(prefix=field_prefix)
            for _source_field, target_template in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS
        ),
    )


RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PRIMARY_ONE_LOOK_FIELDS: tuple[str, ...] = (
    release_readiness_required_gate_bundle_one_look_fields("required_gate_bundle")
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCAN_PROBE_ONE_LOOK_FIELDS: tuple[str, ...] = (
    release_readiness_required_gate_bundle_one_look_fields("required_gate_bundle_scan_probe")
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER = (
    "required_gate_bundle_projection="
    + "|".join(
        f"one_look.{field}"
        for field in (
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PRIMARY_ONE_LOOK_FIELDS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCAN_PROBE_ONE_LOOK_FIELDS,
        )
    )
)
RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    *(
        f"one_look.{field}"
        for field in (
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PRIMARY_ONE_LOOK_FIELDS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCAN_PROBE_ONE_LOOK_FIELDS,
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


def build_release_readiness_required_gate_bundle_one_look_projection(
    bundle: dict[str, Any],
    *,
    prefix: str = "required_gate_bundle",
) -> dict[str, Any]:
    source = bundle if isinstance(bundle, dict) else {}
    field_prefix = str(prefix or "").strip() or "required_gate_bundle"
    projection: dict[str, Any] = {
        f"{field_prefix}_status": _clean_str(source.get("bundle_status")).upper() or STATUS_UNKNOWN,
        f"{field_prefix}_projection_status": _clean_str(source.get("projection_status")).upper() or STATUS_UNKNOWN,
        f"{field_prefix}_scope_class": _clean_str(source.get("scope_class")),
        f"{field_prefix}_scope_reason": _clean_str(source.get("scope_reason")),
        f"{field_prefix}_failed_required_target_count": _safe_int(source.get("failed_required_target_count")),
        f"{field_prefix}_failed_target_names": _clean_list(source.get("failed_target_names")),
        f"{field_prefix}_projection_stale_reasons": _clean_list(source.get("projection_stale_reasons")),
        f"{field_prefix}_rows_without_projected_report_fields": _clean_list(source.get("rows_without_projected_report_fields")),
        f"{field_prefix}_missing_mapping_requirements": _clean_list(source.get("missing_mapping_requirements")),
    }
    for source_field, target_field in RELEASE_READINESS_REQUIRED_GATE_BUNDLE_ONE_LOOK_PASSTHROUGH_FIELDS:
        projection[target_field.format(prefix=field_prefix)] = _clean_str(source.get(source_field))
    return projection


def apply_release_readiness_required_gate_bundle_one_look(summary: dict[str, Any], one_look: dict[str, Any]) -> None:
    if not isinstance(one_look, dict):
        return
    summary_payload = summary if isinstance(summary, dict) else {}
    bundle = summary_payload.get("required_gate_bundle") or {}
    scan_probe = summary_payload.get("required_gate_bundle_scan_probe") or {}
    one_look.update(
        build_release_readiness_required_gate_bundle_one_look_projection(
            bundle or {},
            prefix="required_gate_bundle",
        )
    )
    one_look.update(
        build_release_readiness_required_gate_bundle_one_look_projection(
            scan_probe or {},
            prefix="required_gate_bundle_scan_probe",
        )
    )
