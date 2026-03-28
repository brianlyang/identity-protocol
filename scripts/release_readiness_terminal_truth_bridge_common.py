#!/usr/bin/env python3
from __future__ import annotations

from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"

ADMISSION_BLOCKED_BY_TERMINAL_TRUTH = "BLOCKED_BY_TERMINAL_TRUTH"
ADMISSION_NOT_BLOCKED_BY_TERMINAL_TRUTH = "NOT_BLOCKED_BY_TERMINAL_TRUTH"

RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_BOUNDARY_FIELDS: tuple[str, ...] = (
    "one_look.terminal_truth_boundary_projection_status",
    "one_look.terminal_truth_observation_status",
    "one_look.admission_lane_projection",
    "one_look.repair_success_not_clean_terminal_truth",
    "one_look.terminal_truth_class",
    "one_look.terminal_state_class",
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_ACTIVE_RUNTIME_FIELDS: tuple[str, ...] = (
    "one_look.identity_terminal_truth_cleanliness_status",
    "one_look.identity_terminal_truth_execution_closure_status",
    "one_look.identity_terminal_truth_class",
    "one_look.identity_terminal_truth_state_machine_status",
    "one_look.identity_terminal_truth_state_class",
    "one_look.identity_terminal_truth_negative_feedback_class",
    "one_look.identity_terminal_truth_publishable",
    "one_look.identity_terminal_truth_next_state_after_veto",
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER = (
    "terminal_truth_bridge_surface="
    + "|".join(
        (
            *RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_BOUNDARY_FIELDS,
            *RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_ACTIVE_RUNTIME_FIELDS,
        )
    )
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS: tuple[str, ...] = (
    "terminal_truth_bridge_case=clean_terminal_truth",
    "terminal_truth_bridge_case=review_required_execution_closure",
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR = (
    "scripts/validate_release_readiness_terminal_truth_bridge.py"
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE = (
    "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh"
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
    *RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE,
)


def _clean_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _alignment_status(ok: bool) -> str:
    return STATUS_PASS_REQUIRED if ok else STATUS_FAIL_REQUIRED



def build_release_readiness_terminal_truth_bridge_projection(
    summary: dict[str, Any] | None,
) -> dict[str, Any]:
    summary = summary if isinstance(summary, dict) else {}
    boundary = summary.get("terminal_truth_boundary_projection")
    if not isinstance(boundary, dict):
        boundary = {}
    one_look = summary.get("one_look")
    if not isinstance(one_look, dict):
        one_look = {}
    return build_release_readiness_terminal_truth_bridge_from_parts(
        boundary_projection=boundary,
        one_look=one_look,
    )



def build_release_readiness_terminal_truth_bridge_from_parts(
    *,
    boundary_projection: dict[str, Any] | None,
    one_look: dict[str, Any] | None,
) -> dict[str, Any]:
    boundary_projection = boundary_projection if isinstance(boundary_projection, dict) else {}
    one_look = one_look if isinstance(one_look, dict) else {}

    boundary_projection_status = _clean_status(
        boundary_projection.get("terminal_truth_boundary_projection_status")
    ) or STATUS_UNKNOWN
    boundary_observation_status = _clean_status(
        boundary_projection.get("terminal_truth_observation_status")
    ) or STATUS_UNKNOWN
    admission_lane_projection = _clean_str(
        boundary_projection.get("admission_lane_projection")
    )
    boundary_terminal_truth_class = _clean_str(
        boundary_projection.get("terminal_truth_class")
    )
    boundary_terminal_state_class = _clean_str(
        boundary_projection.get("terminal_state_class")
    )
    boundary_publishable = _clean_bool(boundary_projection.get("publishable"))
    repair_success_not_clean_terminal_truth = _clean_bool(
        boundary_projection.get("repair_success_not_clean_terminal_truth")
    )

    active_runtime_cleanliness_status = _clean_status(
        one_look.get("identity_terminal_truth_cleanliness_status")
    ) or STATUS_UNKNOWN
    active_runtime_execution_closure_status = _clean_status(
        one_look.get("identity_terminal_truth_execution_closure_status")
    ) or STATUS_UNKNOWN
    active_runtime_state_machine_status = _clean_status(
        one_look.get("identity_terminal_truth_state_machine_status")
    ) or STATUS_UNKNOWN
    active_runtime_terminal_truth_class = _clean_str(
        one_look.get("identity_terminal_truth_class")
    )
    active_runtime_terminal_state_class = _clean_str(
        one_look.get("identity_terminal_truth_state_class")
    )
    active_runtime_negative_feedback_class = _clean_str(
        one_look.get("identity_terminal_truth_negative_feedback_class")
    )
    active_runtime_publishable = _clean_bool(
        one_look.get("identity_terminal_truth_publishable")
    )
    active_runtime_next_state_after_veto = _clean_str(
        one_look.get("identity_terminal_truth_next_state_after_veto")
    )

    stale_reasons: list[str] = []

    if boundary_projection_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            f"boundary_projection_not_pass:{boundary_projection_status or STATUS_UNKNOWN}"
        )
    if boundary_observation_status not in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED}:
        stale_reasons.append(
            f"boundary_observation_status_unusable:{boundary_observation_status or STATUS_UNKNOWN}"
        )
    if active_runtime_cleanliness_status not in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED}:
        stale_reasons.append(
            f"active_runtime_cleanliness_status_unusable:{active_runtime_cleanliness_status or STATUS_UNKNOWN}"
        )
    if active_runtime_state_machine_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            f"active_runtime_state_machine_not_pass:{active_runtime_state_machine_status or STATUS_UNKNOWN}"
        )
    if not boundary_terminal_truth_class:
        stale_reasons.append("boundary_terminal_truth_class_missing")
    if not boundary_terminal_state_class:
        stale_reasons.append("boundary_terminal_state_class_missing")
    if not active_runtime_terminal_truth_class:
        stale_reasons.append("active_runtime_terminal_truth_class_missing")
    if not active_runtime_terminal_state_class:
        stale_reasons.append("active_runtime_terminal_state_class_missing")
    if admission_lane_projection not in {
        ADMISSION_BLOCKED_BY_TERMINAL_TRUTH,
        ADMISSION_NOT_BLOCKED_BY_TERMINAL_TRUTH,
    }:
        stale_reasons.append(
            f"admission_lane_projection_unusable:{admission_lane_projection or STATUS_UNKNOWN}"
        )

    terminal_truth_class_alignment_status = _alignment_status(
        boundary_terminal_truth_class == active_runtime_terminal_truth_class
    )
    if terminal_truth_class_alignment_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            "terminal_truth_class_bridge_mismatch:"
            f"{boundary_terminal_truth_class or STATUS_UNKNOWN}!={active_runtime_terminal_truth_class or STATUS_UNKNOWN}"
        )

    terminal_state_class_alignment_status = _alignment_status(
        boundary_terminal_state_class == active_runtime_terminal_state_class
    )
    if terminal_state_class_alignment_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            "terminal_state_class_bridge_mismatch:"
            f"{boundary_terminal_state_class or STATUS_UNKNOWN}!={active_runtime_terminal_state_class or STATUS_UNKNOWN}"
        )

    terminal_truth_observation_alignment_status = _alignment_status(
        boundary_observation_status == active_runtime_cleanliness_status
    )
    if terminal_truth_observation_alignment_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            "terminal_truth_observation_bridge_mismatch:"
            f"{boundary_observation_status or STATUS_UNKNOWN}!={active_runtime_cleanliness_status or STATUS_UNKNOWN}"
        )

    publishable_alignment_status = _alignment_status(
        boundary_publishable is active_runtime_publishable
    )
    if publishable_alignment_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            "terminal_truth_publishable_bridge_mismatch:"
            f"{boundary_publishable}!={active_runtime_publishable}"
        )

    admission_semantics_alignment_ok = False
    if admission_lane_projection == ADMISSION_NOT_BLOCKED_BY_TERMINAL_TRUTH:
        admission_semantics_alignment_ok = (
            active_runtime_cleanliness_status == STATUS_PASS_REQUIRED
            and active_runtime_execution_closure_status == STATUS_PASS_REQUIRED
            and active_runtime_publishable is True
            and active_runtime_next_state_after_veto == ""
        )
    elif admission_lane_projection == ADMISSION_BLOCKED_BY_TERMINAL_TRUTH:
        admission_semantics_alignment_ok = (
            active_runtime_cleanliness_status == STATUS_FAIL_REQUIRED
            and active_runtime_publishable is False
        )
    admission_semantics_alignment_status = _alignment_status(
        admission_semantics_alignment_ok
    )
    if admission_semantics_alignment_status != STATUS_PASS_REQUIRED:
        stale_reasons.append(
            "admission_lane_projection_bridge_mismatch:"
            f"{admission_lane_projection or STATUS_UNKNOWN}"
        )

    if repair_success_not_clean_terminal_truth:
        review_veto_semantics_alignment_ok = (
            admission_lane_projection == ADMISSION_BLOCKED_BY_TERMINAL_TRUTH
            and active_runtime_execution_closure_status == STATUS_PASS_REQUIRED
            and active_runtime_cleanliness_status == STATUS_FAIL_REQUIRED
            and active_runtime_next_state_after_veto == boundary_terminal_state_class
            and active_runtime_negative_feedback_class not in {"", "none"}
        )
        review_veto_semantics_alignment_status = _alignment_status(
            review_veto_semantics_alignment_ok
        )
        if review_veto_semantics_alignment_status != STATUS_PASS_REQUIRED:
            stale_reasons.append(
                "review_veto_bridge_mismatch:"
                f"{active_runtime_execution_closure_status or STATUS_UNKNOWN}|"
                f"{active_runtime_cleanliness_status or STATUS_UNKNOWN}|"
                f"{active_runtime_negative_feedback_class or STATUS_UNKNOWN}|"
                f"{active_runtime_next_state_after_veto or STATUS_UNKNOWN}"
            )
    else:
        review_veto_semantics_alignment_status = STATUS_SKIPPED_NOT_REQUIRED

    return {
        "terminal_truth_bridge_status": STATUS_PASS_REQUIRED
        if not stale_reasons
        else STATUS_FAIL_REQUIRED,
        "boundary_projection_status": boundary_projection_status,
        "boundary_observation_status": boundary_observation_status,
        "admission_lane_projection": admission_lane_projection,
        "boundary_terminal_truth_class": boundary_terminal_truth_class,
        "boundary_terminal_state_class": boundary_terminal_state_class,
        "boundary_publishable": boundary_publishable,
        "repair_success_not_clean_terminal_truth": repair_success_not_clean_terminal_truth,
        "active_runtime_cleanliness_status": active_runtime_cleanliness_status,
        "active_runtime_execution_closure_status": active_runtime_execution_closure_status,
        "active_runtime_state_machine_status": active_runtime_state_machine_status,
        "active_runtime_terminal_truth_class": active_runtime_terminal_truth_class,
        "active_runtime_terminal_state_class": active_runtime_terminal_state_class,
        "active_runtime_negative_feedback_class": active_runtime_negative_feedback_class,
        "active_runtime_publishable": active_runtime_publishable,
        "active_runtime_next_state_after_veto": active_runtime_next_state_after_veto,
        "terminal_truth_class_alignment_status": terminal_truth_class_alignment_status,
        "terminal_state_class_alignment_status": terminal_state_class_alignment_status,
        "terminal_truth_observation_alignment_status": terminal_truth_observation_alignment_status,
        "publishable_alignment_status": publishable_alignment_status,
        "admission_semantics_alignment_status": admission_semantics_alignment_status,
        "review_veto_semantics_alignment_status": review_veto_semantics_alignment_status,
        "stale_reasons": stale_reasons,
    }
