#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any


STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

REQUIRED_GATE_BUNDLE_SCOPE_CLASS_TARGETED_SUBSET = "bounded_targeted_subset_exclusion"
REQUIRED_GATE_BUNDLE_SCOPE_REASON_TARGETED_SUBSET = (
    "required_gate_bundle_out_of_scope_for_targeted_subset"
)

RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    "targeted_subset_required_gate_bundle_scope="
    "required_gate_bundle_status=SKIPPED_NOT_REQUIRED|"
    "required_gate_bundle_projection_status=SKIPPED_NOT_REQUIRED|"
    "required_gate_bundle_scope_class=bounded_targeted_subset_exclusion",
    "targeted_subset_required_gate_bundle_scope_reason="
    "required_gate_bundle_scope_reason=required_gate_bundle_out_of_scope_for_targeted_subset",
)


def targeted_subset_excludes_required_gate_bundle(summary: dict[str, Any]) -> bool:
    if not isinstance(summary, dict):
        return False
    selected_check_mode = str(summary.get("selected_check_mode", "") or "").strip().lower()
    return selected_check_mode == "targeted_subset"


def build_scope_excluded_required_gate_bundle_summary(
    path_text: str,
    *,
    selected_check_mode: str,
    selected_check_dependency_mode: str,
) -> dict[str, Any]:
    path = Path(path_text).expanduser().resolve()
    return {
        "receipt_path": str(path),
        "bundle_status": STATUS_SKIPPED_NOT_REQUIRED,
        "projection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "run_id_binding": "",
        "actor_id": "",
        "resolved_work_layer": "",
        "resolved_source_layer": "",
        "lock_state": "",
        "report_selected_path": "",
        "total_targets": 0,
        "required_target_count": 0,
        "failed_required_target_count": 0,
        "failed_target_names": [],
        "projection_stale_reasons": [],
        "rows_without_projected_report_fields": [],
        "missing_mapping_requirements": [],
        "scope_class": REQUIRED_GATE_BUNDLE_SCOPE_CLASS_TARGETED_SUBSET,
        "scope_reason": REQUIRED_GATE_BUNDLE_SCOPE_REASON_TARGETED_SUBSET,
        "scope_mode": "selected_check_bounded",
        "selected_check_mode": str(selected_check_mode or "").strip(),
        "selected_check_dependency_mode": str(selected_check_dependency_mode or "").strip(),
    }
