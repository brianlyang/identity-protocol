#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import release_readiness_check as readiness_check
from governed_runtime_summary_surface_common import (
    build_governed_runtime_summary_surface_payload,
)
from release_closure_doc_common import resolve_release_closure_doc_paths
from repo_root_resolution_common import resolve_repo_root
from health_report_experience_writeback_projection_common import (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_BOUNDARY_FIELDS,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_MARKER,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_ONE_LOOK_FIELDS,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROJECTION_MARKER,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROBE,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROOF_LANES,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_NAME,
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_VALIDATOR,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_KEY = "release_readiness_health_projection_bridge_status"
ERR_CODE = "IP-RRHPB-001"

EXPECTED_SURFACE_NAME = "health_report_experience_writeback_closure"
EXPECTED_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "health_report_experience_writeback_projection_status",
    "health_report_contract_status",
    "health_report_experience_writeback_validation_status",
    "health_report_selected_path_matches_execution_report",
    "health_report_repair_lane_status",
    "health_report_post_execution_obligation_status",
    "health_report_writeback_continuity_status",
    "health_report_boundary_bridge_status",
    "health_report_report_selection_mode",
    "health_report_report_selected_authority_class",
    "health_report_report_pointer_resolution_mode",
    "health_report_writeback_status",
    "health_report_writeback_rule_id",
)
EXPECTED_BOUNDARY_FIELDS: tuple[str, ...] = (
    "terminal_truth_boundary_projection.repair_lane_status",
    "terminal_truth_boundary_projection.post_execution_obligation_status",
    "terminal_truth_boundary_projection.writeback_continuity_status",
    "terminal_truth_boundary_projection.experience_writeback_validation_status",
)
EXPECTED_PROJECTION_MARKER = (
    "release_readiness_health_report_writeback_projection="
    + "|".join(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELDS)
)
EXPECTED_BRIDGE_MARKER = (
    "release_readiness_health_projection_bridge="
    + "|".join(
        (
            *EXPECTED_BOUNDARY_FIELDS,
            *(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELDS),
        )
    )
)
EXPECTED_VALIDATOR = "scripts/validate_release_readiness_health_projection_bridge.py"
EXPECTED_PROBE = "scripts/ci/run_release_readiness_health_projection_bridge_probes_ci.sh"
EXPECTED_PROOF_LANES: tuple[str, ...] = (
    "scripts/ci/run_release_readiness_health_projection_probes_ci.sh",
    EXPECTED_VALIDATOR,
    EXPECTED_PROBE,
)
EXPECTED_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_SURFACE_NAME,
    EXPECTED_PROJECTION_MARKER,
    EXPECTED_BRIDGE_MARKER,
    *EXPECTED_BOUNDARY_FIELDS,
    *(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELDS),
    *EXPECTED_PROOF_LANES,
)
EXPECTED_VALIDATOR_COMMAND: tuple[str, ...] = ("python3", EXPECTED_VALIDATOR, "--json-only")
EXPECTED_PROBE_COMMAND: tuple[str, ...] = ("bash", EXPECTED_PROBE)
SUMMARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_summary.py"
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_REL = "scripts/validate_runtime_summary_surface_governance.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
THREE_PLANE_REL = "scripts/report_three_plane_status.py"
FULL_SCAN_REL = "scripts/full_identity_protocol_scan.py"
COMPANION_BUNDLE_REL = "scripts/release_closure_projection_companion_marker_bundle_common.py"
HEALTH_PROJECTION_COMMON_REL = "scripts/health_report_experience_writeback_projection_common.py"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))



def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""



def _build_post_closure_command_index() -> set[tuple[str, ...]]:
    return {tuple(command) for command in readiness_check.POST_CLOSURE_GOVERNANCE_SCRIPTS}



def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate release-readiness health projection keeps its richer repair/writeback "
            "bridge machine-visible across summary, three-plane, full-scan, docs, and proof lanes."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    docs = resolve_release_closure_doc_paths(repo_root)

    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_CODE,
        "repo_root": str(repo_root),
        "health_surface_name": RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_NAME,
        "one_look_fields": list(RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_ONE_LOOK_FIELDS),
        "boundary_fields": list(RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_BOUNDARY_FIELDS),
        "proof_lanes": list(RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROOF_LANES),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_NAME != EXPECTED_SURFACE_NAME:
        stale_reasons.append("health_projection_surface_name_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_ONE_LOOK_FIELDS != EXPECTED_ONE_LOOK_FIELDS:
        stale_reasons.append("health_projection_one_look_fields_drift")
    if (
        RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_BOUNDARY_FIELDS
        != EXPECTED_BOUNDARY_FIELDS
    ):
        stale_reasons.append("health_projection_bridge_boundary_fields_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROJECTION_MARKER != EXPECTED_PROJECTION_MARKER:
        stale_reasons.append("health_projection_projection_marker_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_MARKER != EXPECTED_BRIDGE_MARKER:
        stale_reasons.append("health_projection_bridge_marker_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_VALIDATOR != EXPECTED_VALIDATOR:
        stale_reasons.append("health_projection_validator_path_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROBE != EXPECTED_PROBE:
        stale_reasons.append("health_projection_probe_path_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROOF_LANES != EXPECTED_PROOF_LANES:
        stale_reasons.append("health_projection_proof_lanes_drift")
    if RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS != EXPECTED_SURFACE_CONSTRAINTS:
        stale_reasons.append("health_projection_surface_constraints_drift")

    post_closure_commands = _build_post_closure_command_index()
    for expected_command in (
        ("bash", "scripts/ci/run_release_readiness_health_projection_probes_ci.sh"),
        EXPECTED_VALIDATOR_COMMAND,
        EXPECTED_PROBE_COMMAND,
    ):
        if expected_command not in post_closure_commands:
            stale_reasons.append(
                f"post_closure_bundle_missing_health_projection_lane:{' '.join(expected_command)}"
            )

    governed_surface = build_governed_runtime_summary_surface_payload("release_readiness_summary")
    constraints = tuple(governed_surface.get("operational_constraints") or ())
    for marker in (
        EXPECTED_SURFACE_NAME,
        EXPECTED_PROJECTION_MARKER,
        EXPECTED_BRIDGE_MARKER,
        EXPECTED_VALIDATOR,
        EXPECTED_PROBE,
    ):
        if marker not in constraints:
            stale_reasons.append(f"governed_summary_missing_health_projection_marker:{marker}")

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token in (
        "boundary_repair_lane_status=_clean_str(boundary_projection.get(\"repair_lane_status\"))",
        "boundary_post_execution_obligation_status=_clean_str(",
        "boundary_projection.get(\"post_execution_obligation_status\")",
        "boundary_writeback_continuity_status=_clean_str(",
        "boundary_projection.get(\"writeback_continuity_status\")",
        '["bash", "scripts/ci/run_release_readiness_health_projection_probes_ci.sh"]',
        '["python3", "scripts/validate_release_readiness_health_projection_bridge.py", "--json-only"]',
        '["bash", "scripts/ci/run_release_readiness_health_projection_bridge_probes_ci.sh"]',
    ):
        if required_token not in readiness_check_text:
            stale_reasons.append(f"release_readiness_check_missing_health_projection_token:{required_token}")

    three_plane_text = _read_text((repo_root / THREE_PLANE_REL).resolve())
    for required_token in (
        "boundary_repair_lane_status: str",
        "boundary_post_execution_obligation_status: str",
        "boundary_writeback_continuity_status: str",
        "boundary_repair_lane_status=STATUS_SKIPPED_NOT_REQUIRED",
        "boundary_post_execution_obligation_status=STATUS_SKIPPED_NOT_REQUIRED",
        "boundary_writeback_continuity_status=STATUS_SKIPPED_NOT_REQUIRED",
        "terminal_truth_boundary_projection.get(\"repair_lane_status\", \"\")",
        "terminal_truth_boundary_projection.get(\"post_execution_obligation_status\", \"\")",
        "terminal_truth_boundary_projection.get(\"writeback_continuity_status\", \"\")",
    ):
        if required_token not in three_plane_text:
            stale_reasons.append(f"three_plane_missing_health_projection_token:{required_token}")

    health_projection_common_text = _read_text((repo_root / HEALTH_PROJECTION_COMMON_REL).resolve())
    for required_token in (
        '"boundary_bridge_fail": 0',
        '"boundary_bridge_fail_identity_ids": []',
        "boundary_bridge_status",
    ):
        if required_token not in health_projection_common_text:
            stale_reasons.append(
                f"health_projection_common_missing_bridge_summary_token:{required_token}"
            )

    full_scan_text = _read_text((repo_root / FULL_SCAN_REL).resolve())
    for required_token in (
        'projection.get("boundary_bridge_status", "")',
        'summary["boundary_bridge_fail"]',
        'summary["boundary_bridge_fail_identity_ids"]',
    ):
        if required_token not in full_scan_text:
            stale_reasons.append(f"full_scan_missing_health_projection_token:{required_token}")

    companion_bundle_text = _read_text((repo_root / COMPANION_BUNDLE_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS",
        "RELEASE_CLOSURE_SUMMARY_HEALTH_PROJECTION_COMPANION_MARKERS = (",
        "RELEASE_CLOSURE_BOUNDARY_HEALTH_PROJECTION_COMPANION_MARKERS = (",
    ):
        if required_token not in companion_bundle_text:
            stale_reasons.append(f"companion_bundle_missing_health_projection_token:{required_token}")

    for label, rel_path in (
        ("runtime_summary_surface_governance", RUNTIME_SUMMARY_SURFACE_GOVERNANCE_REL),
        ("summary_validator", SUMMARY_VALIDATOR_REL),
    ):
        text = _read_text((repo_root / rel_path).resolve())
        if (
            label == "runtime_summary_surface_governance"
            and "RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS"
            not in text
        ):
            stale_reasons.append(
                f"{label}_missing_health_projection_surface_constraints"
            )

    for label, path in (
        ("summary_doc", docs.summary_path),
        ("governance_doc", docs.governance_path),
        ("review_doc", docs.review_path),
    ):
        text = _read_text(path)
        for marker in EXPECTED_SURFACE_CONSTRAINTS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_health_projection_marker:{marker}")

    payload[STATUS_KEY] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_CODE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
