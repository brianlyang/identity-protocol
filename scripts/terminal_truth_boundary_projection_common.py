#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from post_execution_report_repair_common import enrich_post_execution_report

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_UNKNOWN = "UNKNOWN"

ADMISSION_BLOCKED_BY_TERMINAL_TRUTH = "BLOCKED_BY_TERMINAL_TRUTH"
ADMISSION_NOT_BLOCKED_BY_TERMINAL_TRUTH = "NOT_BLOCKED_BY_TERMINAL_TRUTH"
ADMISSION_NOT_APPLICABLE = "NOT_APPLICABLE"
ADMISSION_UNRESOLVED = "UNRESOLVED"

BOUNDARY_HEALTH_NOT_APPLICABLE = "not_applicable"
BOUNDARY_HEALTH_REPAIR_GREEN_TERMINAL_TRUTH_BLOCKED = "repair_green_terminal_truth_blocked"
BOUNDARY_HEALTH_REPAIR_GREEN_TERMINAL_TRUTH_CLEAN = "repair_green_terminal_truth_clean"
BOUNDARY_HEALTH_REPAIR_BLOCKED_TERMINAL_TRUTH_BLOCKED = "repair_blocked_terminal_truth_blocked"
BOUNDARY_HEALTH_REPAIR_BLOCKED_TERMINAL_TRUTH_CLEAN = "repair_blocked_terminal_truth_clean"
BOUNDARY_HEALTH_PROJECTION_INCOMPLETE = "projection_incomplete"


def build_terminal_truth_boundary_projection_summary_skeleton() -> dict[str, Any]:
    return {
        "total_identities": 0,
        "projection_pass": 0,
        "projection_fail": 0,
        "not_applicable": 0,
        "blocked_by_terminal_truth": 0,
        "repair_green_terminal_truth_blocked": 0,
        "repair_green_terminal_truth_clean": 0,
        "blocked_identity_ids": [],
    }


def _clean_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _clean_reason_list(values: Any) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        token = _clean_string(value)
        if token:
            cleaned.append(token)
    return cleaned


def _skip_payload(*, reason: str, report_selected_path: str = "") -> dict[str, Any]:
    return {
        "terminal_truth_boundary_projection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "projection_mode": "post_execution_enrichment",
        "projection_applicability_status": STATUS_SKIPPED_NOT_REQUIRED,
        "projection_applicability_reason": reason,
        "report_selected_path": report_selected_path,
        "report_surface_class": "",
        "repair_lane_status": STATUS_SKIPPED_NOT_REQUIRED,
        "repair_observation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "repair_blocking_stale_reasons": [],
        "repair_observation_stale_reasons": [],
        "post_execution_obligation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "writeback_continuity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "experience_writeback_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "experience_writeback_validation_stale_reasons": [],
        "terminal_truth_observation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_truth_class": "",
        "terminal_state_class": "",
        "negative_feedback_class": "",
        "publishable": False,
        "canonical_result_eligible": False,
        "repair_success_not_clean_terminal_truth": False,
        "clean_terminal_truth_veto_observed": False,
        "admission_lane_projection": ADMISSION_NOT_APPLICABLE,
        "admission_lane_projection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "boundary_health_class": BOUNDARY_HEALTH_NOT_APPLICABLE,
        "outer_surface_non_owner_rule": (
            "outer summary surfaces may project repair/terminal-truth/admission split, "
            "but they must not replace root-law owners or creator/update admission authority"
        ),
        "stale_reasons": [reason] if reason else [],
    }


def build_terminal_truth_boundary_projection_from_enrichment(
    projection_result: dict[str, Any] | None,
    *,
    report_selected_path: str = "",
) -> dict[str, Any]:
    projection_result = projection_result if isinstance(projection_result, dict) else {}
    projection_applicability = (
        projection_result.get("projection_applicability")
        if isinstance(projection_result.get("projection_applicability"), dict)
        else {}
    )
    applicability_status = _clean_status(projection_applicability.get("status"))
    applicability_reason = _clean_string(projection_applicability.get("applicability_reason"))
    report_surface_class = _clean_string(projection_applicability.get("report_surface_class"))
    report_after = projection_result.get("report_after") if isinstance(projection_result.get("report_after"), dict) else {}

    if applicability_status == STATUS_SKIPPED_NOT_REQUIRED:
        return _skip_payload(
            reason=applicability_reason or "report_surface_not_applicable",
            report_selected_path=report_selected_path,
        )

    repair_lane_status = _clean_status(projection_result.get("repair_projection_status"))
    repair_blocking_stale_reasons = _clean_reason_list(projection_result.get("stale_reasons"))
    repair_observation_stale_reasons = _clean_reason_list(projection_result.get("observation_stale_reasons"))
    repair_observation_status = (
        STATUS_WARN_NON_BLOCKING
        if repair_observation_stale_reasons
        else (STATUS_PASS_REQUIRED if repair_lane_status == STATUS_PASS_REQUIRED else STATUS_UNKNOWN)
    )
    post_execution_status = _clean_status(
        ((projection_result.get("post_execution_validation") or {}).get("status", ""))
    )
    writeback_status = _clean_status(
        ((projection_result.get("writeback_continuity_validation") or {}).get("status", ""))
    )
    experience_writeback_validation = (
        projection_result.get("experience_writeback_validation")
        if isinstance(projection_result.get("experience_writeback_validation"), dict)
        else {}
    )
    experience_writeback_status = _clean_status(experience_writeback_validation.get("status"))
    experience_writeback_payload = (
        experience_writeback_validation.get("payload")
        if isinstance(experience_writeback_validation.get("payload"), dict)
        else {}
    )
    experience_writeback_stale_reasons = _clean_reason_list(
        experience_writeback_payload.get("stale_reasons")
    )
    terminal_truth_status = _clean_status(
        ((projection_result.get("terminal_truth_validation") or {}).get("status", ""))
    )

    admission_lane_projection = ADMISSION_UNRESOLVED
    admission_lane_projection_status = STATUS_FAIL_REQUIRED
    if terminal_truth_status == STATUS_PASS_REQUIRED:
        admission_lane_projection = ADMISSION_NOT_BLOCKED_BY_TERMINAL_TRUTH
        admission_lane_projection_status = STATUS_PASS_REQUIRED
    elif terminal_truth_status == STATUS_FAIL_REQUIRED:
        admission_lane_projection = ADMISSION_BLOCKED_BY_TERMINAL_TRUTH
        admission_lane_projection_status = STATUS_PASS_REQUIRED

    repair_success_not_clean_terminal_truth = (
        repair_lane_status == STATUS_PASS_REQUIRED and terminal_truth_status == STATUS_FAIL_REQUIRED
    )
    clean_terminal_truth_veto_observed = terminal_truth_status == STATUS_FAIL_REQUIRED

    if repair_lane_status == STATUS_PASS_REQUIRED and terminal_truth_status == STATUS_FAIL_REQUIRED:
        boundary_health_class = BOUNDARY_HEALTH_REPAIR_GREEN_TERMINAL_TRUTH_BLOCKED
    elif repair_lane_status == STATUS_PASS_REQUIRED and terminal_truth_status == STATUS_PASS_REQUIRED:
        boundary_health_class = BOUNDARY_HEALTH_REPAIR_GREEN_TERMINAL_TRUTH_CLEAN
    elif repair_lane_status == STATUS_FAIL_REQUIRED and terminal_truth_status == STATUS_FAIL_REQUIRED:
        boundary_health_class = BOUNDARY_HEALTH_REPAIR_BLOCKED_TERMINAL_TRUTH_BLOCKED
    elif repair_lane_status == STATUS_FAIL_REQUIRED and terminal_truth_status == STATUS_PASS_REQUIRED:
        boundary_health_class = BOUNDARY_HEALTH_REPAIR_BLOCKED_TERMINAL_TRUTH_CLEAN
    else:
        boundary_health_class = BOUNDARY_HEALTH_PROJECTION_INCOMPLETE

    stale_reasons: list[str] = []
    if not repair_lane_status:
        stale_reasons.append("repair_lane_status_missing")
    if not post_execution_status:
        stale_reasons.append("post_execution_obligation_status_missing")
    if not writeback_status:
        stale_reasons.append("writeback_continuity_status_missing")
    if experience_writeback_status not in {
        STATUS_PASS_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_FAIL_REQUIRED,
        STATUS_WARN_NON_BLOCKING,
    }:
        stale_reasons.append("experience_writeback_validation_status_missing")
    if not terminal_truth_status:
        stale_reasons.append("terminal_truth_observation_status_missing")
    if admission_lane_projection_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("admission_lane_projection_unresolved")

    projection_status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED

    return {
        "terminal_truth_boundary_projection_status": projection_status,
        "projection_mode": "post_execution_enrichment",
        "projection_applicability_status": applicability_status or STATUS_UNKNOWN,
        "projection_applicability_reason": applicability_reason,
        "report_selected_path": report_selected_path,
        "report_surface_class": report_surface_class,
        "repair_lane_status": repair_lane_status or STATUS_UNKNOWN,
        "repair_observation_status": repair_observation_status,
        "repair_blocking_stale_reasons": repair_blocking_stale_reasons,
        "repair_observation_stale_reasons": repair_observation_stale_reasons,
        "post_execution_obligation_status": post_execution_status or STATUS_UNKNOWN,
        "writeback_continuity_status": writeback_status or STATUS_UNKNOWN,
        "experience_writeback_validation_status": experience_writeback_status or STATUS_UNKNOWN,
        "experience_writeback_validation_stale_reasons": experience_writeback_stale_reasons,
        "terminal_truth_observation_status": terminal_truth_status or STATUS_UNKNOWN,
        "terminal_truth_class": _clean_string(report_after.get("terminal_truth_class")),
        "terminal_state_class": _clean_string(report_after.get("terminal_state_class")),
        "negative_feedback_class": _clean_string(report_after.get("negative_feedback_class")),
        "publishable": bool(report_after.get("publishable", False)),
        "canonical_result_eligible": bool(report_after.get("canonical_result_eligible", False)),
        "repair_success_not_clean_terminal_truth": repair_success_not_clean_terminal_truth,
        "clean_terminal_truth_veto_observed": clean_terminal_truth_veto_observed,
        "admission_lane_projection": admission_lane_projection,
        "admission_lane_projection_status": admission_lane_projection_status,
        "boundary_health_class": boundary_health_class,
        "outer_surface_non_owner_rule": (
            "outer summary surfaces may project repair/terminal-truth/admission split, "
            "but they must not replace root-law owners or creator/update admission authority"
        ),
        "stale_reasons": stale_reasons,
    }


def build_terminal_truth_boundary_projection_from_report(
    *,
    report_doc: dict[str, Any] | None,
    report_path: Path | None,
    catalog_path: Path,
    repo_catalog_path: Path,
    identity_id: str,
    operation: str = "readiness",
    work_layer: str = "",
    source_layer: str = "",
) -> dict[str, Any]:
    if not isinstance(report_doc, dict):
        report_doc = {}
    report_selected_path = str(report_path.resolve()) if isinstance(report_path, Path) else ""
    if not report_doc:
        return _skip_payload(reason="execution_report_missing_or_invalid", report_selected_path=report_selected_path)
    try:
        projection_result = enrich_post_execution_report(
            report_doc=report_doc,
            report_path=report_path,
            catalog_path=catalog_path,
            repo_catalog_path=repo_catalog_path,
            identity_id=identity_id,
            operation=operation,
            work_layer=work_layer,
            source_layer=source_layer,
        )
    except Exception as exc:
        return {
            "terminal_truth_boundary_projection_status": STATUS_FAIL_REQUIRED,
            "projection_mode": "post_execution_enrichment",
            "projection_applicability_status": STATUS_UNKNOWN,
            "projection_applicability_reason": "",
            "report_selected_path": report_selected_path,
            "report_surface_class": "",
            "repair_lane_status": STATUS_UNKNOWN,
            "repair_observation_status": STATUS_UNKNOWN,
            "repair_blocking_stale_reasons": [],
            "repair_observation_stale_reasons": [],
            "post_execution_obligation_status": STATUS_UNKNOWN,
            "writeback_continuity_status": STATUS_UNKNOWN,
            "experience_writeback_validation_status": STATUS_UNKNOWN,
            "experience_writeback_validation_stale_reasons": [],
            "terminal_truth_observation_status": STATUS_UNKNOWN,
            "terminal_truth_class": "",
            "terminal_state_class": "",
            "negative_feedback_class": "",
            "publishable": False,
            "canonical_result_eligible": False,
            "repair_success_not_clean_terminal_truth": False,
            "clean_terminal_truth_veto_observed": False,
            "admission_lane_projection": ADMISSION_UNRESOLVED,
            "admission_lane_projection_status": STATUS_FAIL_REQUIRED,
            "boundary_health_class": BOUNDARY_HEALTH_PROJECTION_INCOMPLETE,
            "outer_surface_non_owner_rule": (
                "outer summary surfaces may project repair/terminal-truth/admission split, "
                "but they must not replace root-law owners or creator/update admission authority"
            ),
            "stale_reasons": [f"projection_exception:{type(exc).__name__}"],
            "exception_message": str(exc),
        }
    return build_terminal_truth_boundary_projection_from_enrichment(
        projection_result,
        report_selected_path=report_selected_path,
    )
