#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

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


STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_ONE_LOOK_CORE_FIELDS: tuple[str, ...] = (
    "required_contract_coverage_status",
    "failed_required_contract_count",
    "failed_required_contracts",
    "failed_optional_contract_count",
    "failed_optional_contracts",
    "selected_check_scope_projection_status",
    "selected_check_scope_class",
    "selected_check_scope_reason",
    "selected_check_scope_excluded_summary_key_count",
    "selected_check_scope_excluded_summary_keys",
    "required_gate_recurrence_status",
    "required_gate_tuple_parity_status",
    "release_plane_cloud_evidence_status",
    "release_plane_required_checks_status",
    "release_cloud_evidence_adapter_status",
    "release_cloud_evidence_adapter_source_kind",
    "release_cloud_evidence_adapter_local_dev_canonical",
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
    "terminal_truth_boundary_projection_status",
    "repair_lane_status",
    "experience_writeback_validation_status",
    "health_report_experience_writeback_projection_status",
    "health_report_contract_status",
    "health_report_experience_writeback_validation_status",
    "health_report_selected_path_matches_execution_report",
    "terminal_truth_observation_status",
    "admission_lane_projection",
    "repair_success_not_clean_terminal_truth",
    "terminal_truth_class",
    "terminal_state_class",
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
    selected_check_scope_projection = summary_payload.get("selected_check_scope_projection") or {}
    recurrence = summary_payload.get("required_gate_recurrence") or {}
    tuple_parity = summary_payload.get("required_gate_tuple_parity") or {}
    release_plane = summary_payload.get("release_plane_cloud_evidence") or {}
    release_adapter = summary_payload.get("release_cloud_evidence_adapter") or {}
    if not release_adapter and isinstance(release_plane, dict):
        release_adapter = release_plane.get("adapter") or {}
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
    terminal_truth_boundary = summary_payload.get("terminal_truth_boundary_projection") or {}
    health_report_writeback_closure = summary_payload.get("health_report_experience_writeback_closure") or {}

    return {
        "required_contract_coverage_status": _clean_str(coverage.get("status")).upper() or STATUS_UNKNOWN,
        "failed_required_contract_count": _safe_int(coverage.get("failed_required_contract_count")),
        "failed_required_contracts": _clean_list(coverage.get("failed_required_contracts")),
        "failed_optional_contract_count": _safe_int(coverage.get("failed_optional_contract_count")),
        "failed_optional_contracts": _clean_list(coverage.get("failed_optional_contracts")),
        "selected_check_scope_projection_status": _clean_str(
            selected_check_scope_projection.get("status")
        ).upper()
        or STATUS_UNKNOWN,
        "selected_check_scope_class": _clean_str(selected_check_scope_projection.get("scope_class")),
        "selected_check_scope_reason": _clean_str(selected_check_scope_projection.get("scope_reason")),
        "selected_check_scope_excluded_summary_key_count": _safe_int(
            selected_check_scope_projection.get("excluded_summary_key_count")
        ),
        "selected_check_scope_excluded_summary_keys": _clean_list(
            selected_check_scope_projection.get("excluded_summary_keys")
        ),
        "required_gate_recurrence_status": _clean_str(recurrence.get("status")).upper() or STATUS_UNKNOWN,
        "required_gate_tuple_parity_status": _clean_str(tuple_parity.get("status")).upper() or STATUS_UNKNOWN,
        "release_plane_cloud_evidence_status": _clean_str(release_plane.get("status")).upper() or STATUS_UNKNOWN,
        "release_plane_required_checks_status": _clean_str(
            (release_plane.get("conditions") or {}).get("required_checks_status")
        ).upper()
        or STATUS_UNKNOWN,
        "release_cloud_evidence_adapter_status": _clean_str(
            (release_adapter or {}).get("release_cloud_evidence_adapter_status")
        ).upper()
        or STATUS_UNKNOWN,
        "release_cloud_evidence_adapter_source_kind": _clean_str((release_adapter or {}).get("adapter_source_kind")),
        "release_cloud_evidence_adapter_local_dev_canonical": bool(
            (release_adapter or {}).get("adapter_local_dev_canonical")
        ),
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
        "terminal_truth_boundary_projection_status": _clean_str(
            terminal_truth_boundary.get("terminal_truth_boundary_projection_status")
        ).upper()
        or STATUS_UNKNOWN,
        "repair_lane_status": _clean_str(terminal_truth_boundary.get("repair_lane_status")).upper()
        or STATUS_UNKNOWN,
        "experience_writeback_validation_status": _clean_str(
            terminal_truth_boundary.get("experience_writeback_validation_status")
        ).upper()
        or STATUS_UNKNOWN,
        "health_report_experience_writeback_projection_status": _clean_str(
            health_report_writeback_closure.get("projection_status")
        ).upper()
        or STATUS_UNKNOWN,
        "health_report_contract_status": _clean_str(
            health_report_writeback_closure.get("health_report_contract_status")
        ).upper()
        or STATUS_UNKNOWN,
        "health_report_experience_writeback_validation_status": _clean_str(
            health_report_writeback_closure.get("validation_status")
        ).upper()
        or STATUS_UNKNOWN,
        "health_report_selected_path_matches_execution_report": bool(
            health_report_writeback_closure.get("report_selected_path_matches_execution_report")
        ),
        "terminal_truth_observation_status": _clean_str(
            terminal_truth_boundary.get("terminal_truth_observation_status")
        ).upper()
        or STATUS_UNKNOWN,
        "admission_lane_projection": _clean_str(terminal_truth_boundary.get("admission_lane_projection")),
        "repair_success_not_clean_terminal_truth": bool(
            terminal_truth_boundary.get("repair_success_not_clean_terminal_truth")
        ),
        "terminal_truth_class": _clean_str(terminal_truth_boundary.get("terminal_truth_class")),
        "terminal_state_class": _clean_str(terminal_truth_boundary.get("terminal_state_class")),
    }


def build_release_readiness_one_look_projection(summary: dict[str, Any]) -> dict[str, Any]:
    one_look = build_release_readiness_one_look_core_projection(summary)
    apply_release_readiness_required_gate_bundle_one_look(summary, one_look)
    apply_release_readiness_repo_global_closure_one_look(summary, one_look)
    apply_release_readiness_active_runtime_closure_one_look(summary, one_look)
    apply_release_readiness_governance_probe_one_look(summary, one_look)
    return one_look
