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
from release_readiness_support_preflight_projection_common import (
    apply_release_readiness_support_preflight_one_look,
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
    return {
        "required_contract_coverage_status": _clean_str(coverage.get("status")).upper() or STATUS_UNKNOWN,
        "failed_required_contract_count": _safe_int(coverage.get("failed_required_contract_count")),
        "failed_required_contracts": _clean_list(coverage.get("failed_required_contracts")),
        "failed_optional_contract_count": _safe_int(coverage.get("failed_optional_contract_count")),
        "failed_optional_contracts": _clean_list(coverage.get("failed_optional_contracts")),
        "required_gate_recurrence_status": _clean_str(recurrence.get("status")).upper() or STATUS_UNKNOWN,
        "required_gate_tuple_parity_status": _clean_str(tuple_parity.get("status")).upper() or STATUS_UNKNOWN,
    }


def build_release_readiness_one_look_projection(summary: dict[str, Any]) -> dict[str, Any]:
    one_look = build_release_readiness_one_look_core_projection(summary)
    apply_release_readiness_support_preflight_one_look(summary, one_look)
    apply_release_readiness_selected_check_scope_one_look(summary, one_look)
    apply_release_readiness_release_cloud_evidence_one_look(summary, one_look)
    apply_release_readiness_terminal_truth_boundary_one_look(summary, one_look)
    apply_release_readiness_health_report_experience_writeback_one_look(summary, one_look)
    apply_release_readiness_required_gate_bundle_one_look(summary, one_look)
    apply_release_readiness_repo_global_closure_one_look(summary, one_look)
    apply_release_readiness_active_runtime_closure_one_look(summary, one_look)
    apply_release_readiness_governance_probe_one_look(summary, one_look)
    return one_look
