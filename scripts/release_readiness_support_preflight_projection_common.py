#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_SUPPORT_PREFLIGHT_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "control_plane_budget_status",
    "control_plane_budget_sync_status",
    "control_plane_status_sync_status",
    "doc_command_surface_registry_status",
    "control_plane_live_status",
    "control_plane_file_status",
    "control_plane_sync_mismatch_count",
    "control_plane_surface_materialization_status",
    "control_plane_materialized_control_plane_status",
    "control_plane_materialized_promotion_ready",
    "resolve_identity_context_local_catalog_closure_status",
    "failclose_plugin_projection_status",
    "full_scan_target_regression_status",
)
RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER = (
    "release_readiness_support_preflight_projection="
    + "|".join(
        f"one_look.{field}"
        for field in RELEASE_READINESS_SUPPORT_PREFLIGHT_ONE_LOOK_FIELDS
    )
)
RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
    *(
        f"one_look.{field}"
        for field in RELEASE_READINESS_SUPPORT_PREFLIGHT_ONE_LOOK_FIELDS
    ),
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def build_release_readiness_support_preflight_one_look_projection(
    summary: dict[str, Any] | None,
) -> dict[str, Any]:
    summary_payload = summary if isinstance(summary, dict) else {}
    control_plane_budget = summary_payload.get("control_plane_budget") or {}
    control_plane_budget_sync = summary_payload.get("control_plane_budget_sync") or {}
    control_plane_status_sync = summary_payload.get("control_plane_status_sync") or {}
    control_plane_surface_materialization = summary_payload.get("control_plane_surface_materialization") or {}
    doc_command_surface_registry = summary_payload.get("doc_command_surface_registry") or {}
    resolve_identity_context_local_catalog_closure = (
        summary_payload.get("resolve_identity_context_local_catalog_closure") or {}
    )
    plugin_projection = summary_payload.get("failclose_plugin_projection") or {}
    full_scan = summary_payload.get("full_scan_target_regression") or {}

    return {
        "control_plane_budget_status": _clean_str(control_plane_budget.get("status")).upper()
        or STATUS_UNKNOWN,
        "control_plane_budget_sync_status": _clean_str(control_plane_budget_sync.get("status")).upper()
        or STATUS_UNKNOWN,
        "control_plane_status_sync_status": _clean_str(control_plane_status_sync.get("status")).upper()
        or STATUS_UNKNOWN,
        "doc_command_surface_registry_status": _clean_str(
            doc_command_surface_registry.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_live_status": _clean_str(
            control_plane_status_sync.get("live_control_plane_status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_file_status": _clean_str(
            control_plane_status_sync.get("file_control_plane_status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_sync_mismatch_count": _safe_int(
            control_plane_status_sync.get("mismatch_count")
        ),
        "control_plane_surface_materialization_status": _clean_str(
            control_plane_surface_materialization.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_materialized_control_plane_status": _clean_str(
            control_plane_surface_materialization.get("control_plane_status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_materialized_promotion_ready": bool(
            control_plane_surface_materialization.get("promotion_ready")
        ),
        "resolve_identity_context_local_catalog_closure_status": _clean_str(
            resolve_identity_context_local_catalog_closure.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "failclose_plugin_projection_status": _clean_str(plugin_projection.get("status")).upper()
        or STATUS_UNKNOWN,
        "full_scan_target_regression_status": _clean_str(full_scan.get("status")).upper()
        or STATUS_UNKNOWN,
    }


def apply_release_readiness_support_preflight_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(one_look, dict):
        return
    one_look.update(build_release_readiness_support_preflight_one_look_projection(summary))
