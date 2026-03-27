#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from experience_writeback_closure_projection_common import (
    build_experience_writeback_closure_projection,
    clean_list as extract_clean_list,
    clean_str as extract_clean_str,
    safe_int as extract_safe_int,
)
from projection_profile_exclusion_scope_common import build_projection_profile_exclusion_payload
from runtime_temp_path_common import runtime_temp_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"

DEFAULT_HEALTH_REPORT_COLLECTION_SCRIPT = "scripts/collect_identity_health_report.py"
DEFAULT_HEALTH_REPORT_CONTRACT_SCRIPT = "scripts/validate_identity_health_contract.py"
HEALTH_REPORT_EXPERIENCE_WRITEBACK_CLOSURE_EXCLUDED_AREA = "health_report_experience_writeback_closure"


def default_health_report_dir() -> Path:
    return (runtime_temp_root() / "identity-health-reports").resolve()


def _clean_str(value: Any) -> str:
    return extract_clean_str(value)


def _clean_list(values: Any) -> list[str]:
    return extract_clean_list(values)


def _safe_int(value: Any) -> int:
    return extract_safe_int(value)


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_identity_health_report_for_execution_report(
    report_dir: Path,
    *,
    identity_id: str,
    execution_report: Path,
) -> Path | None:
    if not report_dir.exists():
        return None
    execution_report_ref = str(execution_report).strip()
    rows = sorted(
        report_dir.glob(f"identity-health-{identity_id}-*.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    latest: Path | None = None
    for candidate in rows:
        if not candidate.is_file():
            continue
        if latest is None:
            latest = candidate
        doc = _safe_load_json(candidate)
        if _clean_str(doc.get("identity_id")) != identity_id:
            continue
        if _clean_str(doc.get("execution_report_ref")) == execution_report_ref:
            return candidate
        closure = doc.get("experience_writeback_closure")
        if isinstance(closure, dict) and _clean_str(closure.get("report_selected_path")) == execution_report_ref:
            return candidate
    return latest


def _health_report_projection_blocked_by_upstream_failure(
    command_execution: dict[str, Any] | None,
    *,
    collect_script: str,
    contract_script: str,
) -> bool:
    first_failed_script = _clean_str((command_execution or {}).get("first_failed_script"))
    return bool(first_failed_script) and first_failed_script not in {collect_script, contract_script}


def _apply_upstream_blocked_health_projection(
    projection: dict[str, Any],
    *,
    collect_expected: bool,
    contract_expected: bool,
) -> dict[str, Any]:
    if collect_expected:
        projection["health_report_collection_status"] = STATUS_SKIPPED_NOT_REQUIRED
    if contract_expected:
        projection["health_report_contract_status"] = STATUS_SKIPPED_NOT_REQUIRED
    projection["projection_status"] = STATUS_SKIPPED_NOT_REQUIRED
    projection["stale_reasons"].append("health_report_projection_blocked_by_upstream_failure")
    return projection


def _base_projection(*, boundary_experience_writeback_validation_status: str) -> dict[str, Any]:
    return {
        "projection_status": STATUS_PASS_REQUIRED,
        "health_report_collection_status": STATUS_PASS_REQUIRED,
        "health_report_contract_status": STATUS_PASS_REQUIRED,
        "health_report_path": "",
        "execution_report_ref": "",
        "execution_report_ref_matches": False,
        "status": "",
        "validation_status": "",
        "report_selected_path": "",
        "report_selected_path_matches_execution_report": False,
        "report_selection_mode": "",
        "report_selected_authority_class": "",
        "report_pointer_resolution_mode": "",
        "report_run_id": "",
        "writeback_status": "",
        "writeback_rule_id": "",
        "rulebook_match_count": 0,
        "task_history_contains_run_id": False,
        "boundary_experience_writeback_validation_status": _clean_str(
            boundary_experience_writeback_validation_status
        ).upper()
        or STATUS_UNKNOWN,
        "stale_reasons": [],
    }


def build_health_report_experience_writeback_closure_projection(
    *,
    identity_id: str,
    health_report_dir: str | Path,
    execution_report: str | Path,
    command_execution: dict[str, Any] | None = None,
    selected_check_mode: str = "full",
    selected_check_names: Iterable[str] | None = None,
    boundary_experience_writeback_validation_status: str = STATUS_UNKNOWN,
    collect_script: str = DEFAULT_HEALTH_REPORT_COLLECTION_SCRIPT,
    contract_script: str = DEFAULT_HEALTH_REPORT_CONTRACT_SCRIPT,
) -> dict[str, Any]:
    execution_report_token = _clean_str(execution_report)
    if not execution_report_token:
        projection = _base_projection(
            boundary_experience_writeback_validation_status=STATUS_SKIPPED_NOT_REQUIRED,
        )
        projection.update(
            {
                "projection_status": STATUS_SKIPPED_NOT_REQUIRED,
                "health_report_collection_status": STATUS_SKIPPED_NOT_REQUIRED,
                "health_report_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
                "validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "boundary_experience_writeback_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "stale_reasons": ["execution_report_missing"],
            }
        )
        return projection

    selected_mode = _clean_str(selected_check_mode).lower() or "full"
    selected_names = set(_clean_list(list(selected_check_names or [])))
    collect_expected = selected_mode != "targeted_subset" or collect_script in selected_names
    contract_expected = selected_mode != "targeted_subset" or contract_script in selected_names
    if not collect_expected and not contract_expected:
        projection = _base_projection(
            boundary_experience_writeback_validation_status=STATUS_SKIPPED_NOT_REQUIRED,
        )
        projection.update(
            {
                "projection_status": STATUS_SKIPPED_NOT_REQUIRED,
                "health_report_collection_status": STATUS_SKIPPED_NOT_REQUIRED,
                "health_report_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
                "validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "boundary_experience_writeback_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
                "stale_reasons": ["post_execution_health_projection_not_selected"],
            }
        )
        return projection

    failed_scripts = set(_clean_list((command_execution or {}).get("failed_scripts")))
    projection = _base_projection(
        boundary_experience_writeback_validation_status=boundary_experience_writeback_validation_status,
    )
    projection["health_report_collection_status"] = (
        STATUS_SKIPPED_NOT_REQUIRED
        if not collect_expected
        else (STATUS_FAIL_REQUIRED if collect_script in failed_scripts else STATUS_PASS_REQUIRED)
    )
    projection["health_report_contract_status"] = (
        STATUS_SKIPPED_NOT_REQUIRED
        if not contract_expected
        else (STATUS_FAIL_REQUIRED if contract_script in failed_scripts else STATUS_PASS_REQUIRED)
    )

    if projection["health_report_collection_status"] == STATUS_FAIL_REQUIRED:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_collection_failed")
    if projection["health_report_contract_status"] == STATUS_FAIL_REQUIRED:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_contract_failed")

    upstream_blocked = _health_report_projection_blocked_by_upstream_failure(
        command_execution,
        collect_script=collect_script,
        contract_script=contract_script,
    )
    report_dir = Path(health_report_dir).expanduser().resolve()
    if not report_dir.exists():
        if upstream_blocked:
            return _apply_upstream_blocked_health_projection(
                projection,
                collect_expected=collect_expected,
                contract_expected=contract_expected,
            )
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_dir_missing")
        return projection

    execution_report_path = Path(execution_report_token).expanduser().resolve()
    health_report_path = resolve_identity_health_report_for_execution_report(
        report_dir,
        identity_id=identity_id,
        execution_report=execution_report_path,
    )
    if health_report_path is None:
        if upstream_blocked:
            return _apply_upstream_blocked_health_projection(
                projection,
                collect_expected=collect_expected,
                contract_expected=contract_expected,
            )
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_not_found")
        return projection

    projection["health_report_path"] = str(health_report_path)
    health_doc = _safe_load_json(health_report_path)
    if not health_doc:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_json_invalid")
        return projection

    projection["execution_report_ref"] = _clean_str(health_doc.get("execution_report_ref"))
    projection["execution_report_ref_matches"] = projection["execution_report_ref"] == str(execution_report_path)
    if not projection["execution_report_ref_matches"]:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_execution_report_ref_mismatch")

    closure = health_doc.get("experience_writeback_closure")
    if not isinstance(closure, dict):
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_experience_writeback_closure_missing")
        return projection

    closure_projection = build_experience_writeback_closure_projection(
        health_doc,
        execution_report=execution_report_path,
    )
    projection["status"] = _clean_str(closure_projection.get("status")).upper()
    projection["validation_status"] = _clean_str(closure_projection.get("validation_status")).upper()
    projection["report_selected_path"] = _clean_str(closure_projection.get("report_selected_path"))
    projection["report_selected_path_matches_execution_report"] = bool(
        closure_projection.get("report_selected_path_matches_execution_report")
    )
    projection["report_selection_mode"] = _clean_str(closure_projection.get("report_selection_mode"))
    projection["report_selected_authority_class"] = _clean_str(
        closure_projection.get("report_selected_authority_class")
    )
    projection["report_pointer_resolution_mode"] = _clean_str(
        closure_projection.get("report_pointer_resolution_mode")
    )
    projection["report_run_id"] = _clean_str(closure_projection.get("report_run_id"))
    projection["writeback_status"] = _clean_str(closure_projection.get("writeback_status")).upper()
    projection["writeback_rule_id"] = _clean_str(closure_projection.get("writeback_rule_id"))
    projection["rulebook_match_count"] = _safe_int(closure_projection.get("rulebook_match_count"))
    projection["task_history_contains_run_id"] = bool(
        closure_projection.get("task_history_contains_run_id")
    )
    projection["stale_reasons"].extend(_clean_list(closure_projection.get("stale_reasons")))

    if not projection["status"]:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_experience_writeback_status_missing")
    if not projection["validation_status"]:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_experience_writeback_validation_status_missing")
    if (
        projection["validation_status"] != STATUS_SKIPPED_NOT_REQUIRED
        and not projection["report_selected_path"]
    ):
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_selected_path_missing")
    if projection["validation_status"] == STATUS_PASS_REQUIRED and not projection["report_selected_path_matches_execution_report"]:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_selected_path_execution_report_mismatch")

    boundary_status = projection["boundary_experience_writeback_validation_status"]
    if (
        boundary_status != STATUS_UNKNOWN
        and boundary_status != STATUS_SKIPPED_NOT_REQUIRED
        and projection["validation_status"]
        and projection["validation_status"] != boundary_status
    ):
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"].append("health_report_boundary_validation_status_mismatch")

    return projection


def build_projection_profile_excluded_health_report_experience_writeback_closure(
    *,
    profile_id: str,
    execution_mode: str,
    description: str,
    owner_surface: str,
) -> dict[str, Any]:
    return build_projection_profile_exclusion_payload(
        profile_id=profile_id,
        execution_mode=execution_mode,
        description=description,
        excluded_area=HEALTH_REPORT_EXPERIENCE_WRITEBACK_CLOSURE_EXCLUDED_AREA,
        owner_surface=owner_surface,
        extra_fields={
            "projection_status": STATUS_SKIPPED_NOT_REQUIRED,
            "health_report_collection_status": STATUS_SKIPPED_NOT_REQUIRED,
            "health_report_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
            "health_report_path": "",
            "execution_report_ref": "",
            "execution_report_ref_matches": False,
            "status": "",
            "validation_status": STATUS_SKIPPED_NOT_REQUIRED,
            "report_selected_path": "",
            "report_selected_path_matches_execution_report": False,
            "report_selection_mode": "",
            "report_selected_authority_class": "",
            "report_pointer_resolution_mode": "",
            "report_run_id": "",
            "writeback_status": "",
            "writeback_rule_id": "",
            "rulebook_match_count": 0,
            "task_history_contains_run_id": False,
            "boundary_experience_writeback_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
        },
    )
