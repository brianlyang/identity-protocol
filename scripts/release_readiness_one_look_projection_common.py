#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

from health_report_experience_writeback_projection_common import (
    apply_release_readiness_health_report_experience_writeback_one_look,
)
from release_cloud_evidence_projection_common import (
    apply_release_readiness_release_cloud_evidence_one_look,
)
from release_readiness_active_runtime_closure_projection_common import (
    apply_release_readiness_active_runtime_closure_one_look,
)
from release_readiness_governance_probe_projection_common import (
    apply_release_readiness_governance_probe_one_look,
)
from release_readiness_repo_global_closure_projection_common import (
    apply_release_readiness_repo_global_closure_one_look,
)
from release_readiness_required_gate_bundle_projection_common import (
    apply_release_readiness_required_gate_bundle_one_look,
)
from release_readiness_selected_check_scope_common import (
    apply_release_readiness_selected_check_scope_one_look,
)
from terminal_truth_boundary_projection_common import (
    apply_release_readiness_terminal_truth_boundary_one_look,
)


STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_ONE_LOOK_CORE_FIELDS: tuple[str, ...] = (
    "required_contract_coverage_status",
    "failed_required_contract_count",
    "failed_required_contracts",
    "failed_optional_contract_count",
    "failed_optional_contracts",
    "required_gate_recurrence_status",
    "required_gate_tuple_parity_status",
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


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def build_release_readiness_one_look_core_projection(summary: dict[str, Any]) -> dict[str, Any]:
    summary_payload = summary if isinstance(summary, dict) else {}
    coverage = summary_payload.get("required_contract_coverage") or {}
    recurrence = summary_payload.get("required_gate_recurrence") or {}
    tuple_parity = summary_payload.get("required_gate_tuple_parity") or {}
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
        "required_contract_coverage_status": _clean_str(coverage.get("status")).upper() or STATUS_UNKNOWN,
        "failed_required_contract_count": _safe_int(coverage.get("failed_required_contract_count")),
        "failed_required_contracts": _clean_list(coverage.get("failed_required_contracts")),
        "failed_optional_contract_count": _safe_int(coverage.get("failed_optional_contract_count")),
        "failed_optional_contracts": _clean_list(coverage.get("failed_optional_contracts")),
        "required_gate_recurrence_status": _clean_str(recurrence.get("status")).upper() or STATUS_UNKNOWN,
        "required_gate_tuple_parity_status": _clean_str(tuple_parity.get("status")).upper() or STATUS_UNKNOWN,
        "control_plane_budget_status": _clean_str(control_plane_budget.get("status")).upper() or STATUS_UNKNOWN,
        "control_plane_budget_sync_status": _clean_str(control_plane_budget_sync.get("status")).upper()
        or STATUS_UNKNOWN,
        "control_plane_status_sync_status": _clean_str(control_plane_status_sync.get("status")).upper()
        or STATUS_UNKNOWN,
        "doc_command_surface_registry_status": _clean_str(
            doc_command_surface_registry.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "control_plane_live_status": _clean_str(control_plane_status_sync.get("live_control_plane_status")).upper()
        or STATUS_UNKNOWN,
        "control_plane_file_status": _clean_str(control_plane_status_sync.get("file_control_plane_status")).upper()
        or STATUS_UNKNOWN,
        "control_plane_sync_mismatch_count": _safe_int(control_plane_status_sync.get("mismatch_count")),
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
        "failclose_plugin_projection_status": _clean_str(plugin_projection.get("status")).upper() or STATUS_UNKNOWN,
        "full_scan_target_regression_status": _clean_str(full_scan.get("status")).upper() or STATUS_UNKNOWN,
    }


def build_release_readiness_one_look_projection(summary: dict[str, Any]) -> dict[str, Any]:
    one_look = build_release_readiness_one_look_core_projection(summary)
    apply_release_readiness_selected_check_scope_one_look(summary, one_look)
    apply_release_readiness_release_cloud_evidence_one_look(summary, one_look)
    apply_release_readiness_terminal_truth_boundary_one_look(summary, one_look)
    apply_release_readiness_health_report_experience_writeback_one_look(summary, one_look)
    apply_release_readiness_required_gate_bundle_one_look(summary, one_look)
    apply_release_readiness_repo_global_closure_one_look(summary, one_look)
    apply_release_readiness_active_runtime_closure_one_look(summary, one_look)
    apply_release_readiness_governance_probe_one_look(summary, one_look)
    return one_look
