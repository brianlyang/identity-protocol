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
RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "terminal_truth_boundary_projection_status",
    "repair_lane_status",
    "experience_writeback_validation_status",
    "terminal_truth_observation_status",
    "admission_lane_projection",
    "repair_success_not_clean_terminal_truth",
    "terminal_truth_class",
    "terminal_state_class",
    "terminal_truth_negative_feedback_class",
    "terminal_truth_publishable",
    "terminal_truth_canonical_result_eligible",
)
RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_PROJECTION_MARKER = (
    "release_readiness_terminal_truth_boundary_projection="
    + "|".join(
        f"one_look.{field}"
        for field in RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_ONE_LOOK_FIELDS
    )
)
RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_PROJECTION_MARKER,
    *(
        f"one_look.{field}"
        for field in RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_ONE_LOOK_FIELDS
    ),
)


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


def _pick_status(
    primary: dict[str, Any],
    primary_key: str,
    fallback: dict[str, Any],
    fallback_key: str | None = None,
) -> str:
    if not isinstance(primary, dict):
        primary = {}
    if not isinstance(fallback, dict):
        fallback = {}
    value = _clean_status(primary.get(primary_key))
    if value:
        return value
    return _clean_status(fallback.get(fallback_key or primary_key))


def _pick_string(
    primary: dict[str, Any],
    primary_key: str,
    fallback: dict[str, Any],
    fallback_key: str | None = None,
) -> str:
    if not isinstance(primary, dict):
        primary = {}
    if not isinstance(fallback, dict):
        fallback = {}
    value = _clean_string(primary.get(primary_key))
    if value:
        return value
    return _clean_string(fallback.get(fallback_key or primary_key))


def _pick_bool(
    primary: dict[str, Any],
    primary_key: str,
    fallback: dict[str, Any],
    fallback_key: str | None = None,
) -> bool:
    if isinstance(primary, dict) and primary_key in primary:
        return bool(primary.get(primary_key))
    if isinstance(fallback, dict):
        return bool(fallback.get(fallback_key or primary_key))
    return False


def _pick_reason_list(
    primary: dict[str, Any],
    primary_key: str,
    fallback: dict[str, Any],
    fallback_key: str | None = None,
) -> list[str]:
    if isinstance(primary, dict):
        value = _clean_reason_list(primary.get(primary_key))
        if value:
            return value
    if isinstance(fallback, dict):
        return _clean_reason_list(fallback.get(fallback_key or primary_key))
    return []


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
        "terminal_truth_execution_closure_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_truth_class": "",
        "terminal_truth_state_machine_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_state_class": "",
        "negative_feedback_class": "",
        "terminal_truth_negative_feedback_terminal_veto_status": STATUS_SKIPPED_NOT_REQUIRED,
        "terminal_truth_loopback_required": False,
        "terminal_truth_next_state_after_veto": "",
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_dirty_signals": [],
        "terminal_truth_blockers": [],
        "terminal_truth_placeholder_result_fields": [],
        "terminal_truth_contradiction_fields": [],
        "terminal_truth_confidence_blocker_fields": [],
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
    terminal_truth_observation_projection = (
        projection_result.get("terminal_truth_observation_projection")
        if isinstance(projection_result.get("terminal_truth_observation_projection"), dict)
        else {}
    )

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
    if not terminal_truth_observation_projection:
        stale_reasons.append("terminal_truth_observation_projection_missing")

    terminal_truth_execution_closure_status = _pick_status(
        terminal_truth_observation_projection,
        "execution_closure_status",
        report_after,
    )
    terminal_truth_class = _pick_string(
        terminal_truth_observation_projection,
        "terminal_truth_class",
        report_after,
    )
    terminal_truth_state_machine_status = _pick_status(
        terminal_truth_observation_projection,
        "terminal_state_machine_status",
        report_after,
    )
    terminal_state_class = _pick_string(
        terminal_truth_observation_projection,
        "terminal_state_class",
        report_after,
    )
    negative_feedback_class = _pick_string(
        terminal_truth_observation_projection,
        "negative_feedback_class",
        report_after,
    )
    terminal_truth_negative_feedback_terminal_veto_status = _pick_status(
        terminal_truth_observation_projection,
        "negative_feedback_terminal_veto_status",
        report_after,
    )
    terminal_truth_loopback_required = _pick_bool(
        terminal_truth_observation_projection,
        "loopback_required",
        report_after,
    )
    terminal_truth_next_state_after_veto = _pick_string(
        terminal_truth_observation_projection,
        "next_state_after_veto",
        report_after,
    )
    publishable = _pick_bool(
        terminal_truth_observation_projection,
        "publishable",
        report_after,
    )
    canonical_result_eligible = _pick_bool(
        terminal_truth_observation_projection,
        "canonical_result_eligible",
        report_after,
    )
    terminal_truth_dirty_signals = _pick_reason_list(
        terminal_truth_observation_projection,
        "dirty_signals",
        report_after,
    )
    terminal_truth_blockers = _pick_reason_list(
        terminal_truth_observation_projection,
        "terminal_truth_blockers",
        report_after,
    )
    terminal_truth_placeholder_result_fields = _pick_reason_list(
        terminal_truth_observation_projection,
        "placeholder_result_fields",
        report_after,
    )
    terminal_truth_contradiction_fields = _pick_reason_list(
        terminal_truth_observation_projection,
        "contradiction_fields",
        report_after,
    )
    terminal_truth_confidence_blocker_fields = _pick_reason_list(
        terminal_truth_observation_projection,
        "confidence_blocker_fields",
        report_after,
    )

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
        "terminal_truth_execution_closure_status": terminal_truth_execution_closure_status or STATUS_UNKNOWN,
        "terminal_truth_class": terminal_truth_class,
        "terminal_truth_state_machine_status": terminal_truth_state_machine_status or STATUS_UNKNOWN,
        "terminal_state_class": terminal_state_class,
        "negative_feedback_class": negative_feedback_class,
        "terminal_truth_negative_feedback_terminal_veto_status": (
            terminal_truth_negative_feedback_terminal_veto_status or STATUS_UNKNOWN
        ),
        "terminal_truth_loopback_required": terminal_truth_loopback_required,
        "terminal_truth_next_state_after_veto": terminal_truth_next_state_after_veto,
        "publishable": publishable,
        "canonical_result_eligible": canonical_result_eligible,
        "terminal_truth_dirty_signals": terminal_truth_dirty_signals,
        "terminal_truth_blockers": terminal_truth_blockers,
        "terminal_truth_placeholder_result_fields": terminal_truth_placeholder_result_fields,
        "terminal_truth_contradiction_fields": terminal_truth_contradiction_fields,
        "terminal_truth_confidence_blocker_fields": terminal_truth_confidence_blocker_fields,
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


def build_release_readiness_terminal_truth_boundary_one_look_projection(
    projection: dict[str, Any] | None,
) -> dict[str, Any]:
    source = projection if isinstance(projection, dict) else {}
    return {
        "terminal_truth_boundary_projection_status": _clean_status(
            source.get("terminal_truth_boundary_projection_status")
        )
        or STATUS_UNKNOWN,
        "repair_lane_status": _clean_status(source.get("repair_lane_status")) or STATUS_UNKNOWN,
        "experience_writeback_validation_status": _clean_status(
            source.get("experience_writeback_validation_status")
        )
        or STATUS_UNKNOWN,
        "terminal_truth_observation_status": _clean_status(
            source.get("terminal_truth_observation_status")
        )
        or STATUS_UNKNOWN,
        "admission_lane_projection": _clean_string(source.get("admission_lane_projection")),
        "repair_success_not_clean_terminal_truth": bool(
            source.get("repair_success_not_clean_terminal_truth")
        ),
        "terminal_truth_class": _clean_string(source.get("terminal_truth_class")),
        "terminal_state_class": _clean_string(source.get("terminal_state_class")),
        "terminal_truth_negative_feedback_class": _clean_string(
            source.get("negative_feedback_class")
        ),
        "terminal_truth_publishable": bool(source.get("publishable")),
        "terminal_truth_canonical_result_eligible": bool(
            source.get("canonical_result_eligible")
        ),
    }


def apply_release_readiness_terminal_truth_boundary_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(one_look, dict):
        return
    summary_payload = summary if isinstance(summary, dict) else {}
    projection = summary_payload.get("terminal_truth_boundary_projection") or {}
    one_look.update(
        build_release_readiness_terminal_truth_boundary_one_look_projection(projection)
    )


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
            "terminal_truth_execution_closure_status": STATUS_UNKNOWN,
            "terminal_truth_class": "",
            "terminal_truth_state_machine_status": STATUS_UNKNOWN,
            "terminal_state_class": "",
            "negative_feedback_class": "",
            "terminal_truth_negative_feedback_terminal_veto_status": STATUS_UNKNOWN,
            "terminal_truth_loopback_required": False,
            "terminal_truth_next_state_after_veto": "",
            "publishable": False,
            "canonical_result_eligible": False,
            "terminal_truth_dirty_signals": [],
            "terminal_truth_blockers": [],
            "terminal_truth_placeholder_result_fields": [],
            "terminal_truth_contradiction_fields": [],
            "terminal_truth_confidence_blocker_fields": [],
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
