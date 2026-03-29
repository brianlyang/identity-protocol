#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import release_readiness_check as readiness_check
from release_closure_doc_common import resolve_release_closure_doc_paths
from repo_root_resolution_common import resolve_repo_root
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD,
    release_readiness_governance_probe_capture_script_map,
    release_readiness_governance_probe_structured_capture_specs,
    release_readiness_governance_probe_summary_defaults,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_ACTIVE_RUNTIME_FIELDS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_BOUNDARY_FIELDS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_ORDER,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_SPECS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_REVIEW_REQUIRED_CASE_MARKER,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_COMMAND,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROOF_LANES,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR_COMMAND,
    STATUS_UNKNOWN,
)
from terminal_truth_boundary_projection_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_ONE_LOOK_FIELDS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_KEY = "release_readiness_terminal_truth_bridge_status"
ERR_CODE = "IP-RRTTB-001"

EXPECTED_BOUNDARY_FIELDS: tuple[str, ...] = (
    "one_look.terminal_truth_boundary_projection_status",
    "one_look.terminal_truth_observation_status",
    "one_look.admission_lane_projection",
    "one_look.repair_success_not_clean_terminal_truth",
    "one_look.terminal_truth_class",
    "one_look.terminal_state_class",
    "one_look.terminal_truth_negative_feedback_class",
    "one_look.terminal_truth_publishable",
    "one_look.terminal_truth_canonical_result_eligible",
)
EXPECTED_ACTIVE_RUNTIME_FIELDS: tuple[str, ...] = (
    "one_look.identity_terminal_truth_cleanliness_status",
    "one_look.identity_terminal_truth_execution_closure_status",
    "one_look.identity_terminal_truth_canonical_publishable_result_status",
    "one_look.identity_terminal_truth_class",
    "one_look.identity_terminal_truth_state_machine_status",
    "one_look.identity_terminal_truth_state_class",
    "one_look.identity_terminal_truth_negative_feedback_class",
    "one_look.identity_terminal_truth_negative_feedback_terminal_veto_status",
    "one_look.identity_terminal_truth_loopback_required",
    "one_look.identity_terminal_truth_publishable",
    "one_look.identity_terminal_truth_next_state_after_veto",
    "one_look.identity_terminal_truth_alias_surface_status",
)
EXPECTED_CASE_MARKERS: tuple[str, ...] = (
    "terminal_truth_bridge_case=clean_terminal_truth",
    "terminal_truth_bridge_case=review_required_execution_closure",
)
EXPECTED_CASE_ORDER: tuple[str, ...] = (
    "clean_terminal_truth",
    "review_required_execution_closure",
)
EXPECTED_REVIEW_REQUIRED_CASE_MARKER = (
    "terminal_truth_bridge_case=review_required_execution_closure"
)
EXPECTED_SURFACE_MARKER = (
    "terminal_truth_bridge_surface="
    + "|".join((*EXPECTED_BOUNDARY_FIELDS, *EXPECTED_ACTIVE_RUNTIME_FIELDS))
)
EXPECTED_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_SURFACE_MARKER,
    *EXPECTED_CASE_MARKERS,
    "scripts/validate_release_readiness_terminal_truth_bridge.py",
    "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh",
)
EXPECTED_PROBE_SUMMARY_KEY = RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_SUMMARY_KEY
EXPECTED_PROBE_ONE_LOOK_FIELD = RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD
EXPECTED_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    "release_readiness_terminal_truth_bridge_probe_status",
)
EXPECTED_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    "positive_validator_output",
    "bridge_case_count",
    "bridge_cases",
    "seeded_identity_ids",
)
EXPECTED_VALIDATOR_COMMAND = RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR_COMMAND
EXPECTED_PROBE_COMMAND = RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_COMMAND
SUMMARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_summary.py"
BOUNDARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_boundary.py"
SUMMARY_BINDING_PROBE_REL = "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _build_post_closure_command_index() -> set[tuple[str, ...]]:
    return {tuple(command) for command in readiness_check.POST_CLOSURE_GOVERNANCE_SCRIPTS}


def _derive_terminal_truth_active_runtime_fields() -> tuple[str, ...]:
    terminal_truth_spec = next(
        (
            spec
            for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
            if spec.summary_key == "identity_terminal_truth_cleanliness"
        ),
        None,
    )
    if terminal_truth_spec is None:
        return ()
    derived_fields = [f"one_look.{terminal_truth_spec.one_look_field}"]
    derived_fields.extend(
        f"one_look.{one_look_field}"
        for _, one_look_field in terminal_truth_spec.one_look_passthrough_fields
        if f"one_look.{one_look_field}" in EXPECTED_ACTIVE_RUNTIME_FIELDS
    )
    return tuple(derived_fields)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the shared release-readiness terminal-truth bridge stays frozen across "
            "boundary projection, active-runtime one-look companions, governance-probe capture, "
            "and release-closure docs."
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
        "boundary_fields": list(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_BOUNDARY_FIELDS),
        "active_runtime_fields": list(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_ACTIVE_RUNTIME_FIELDS),
        "surface_constraints": list(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS),
        "bridge_case_order": list(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_ORDER),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_BOUNDARY_FIELDS != EXPECTED_BOUNDARY_FIELDS:
        stale_reasons.append("terminal_truth_bridge_boundary_fields_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_ACTIVE_RUNTIME_FIELDS != EXPECTED_ACTIVE_RUNTIME_FIELDS:
        stale_reasons.append("terminal_truth_bridge_active_runtime_fields_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_ORDER != EXPECTED_CASE_ORDER:
        stale_reasons.append("terminal_truth_bridge_case_order_drift")
    if len(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_SPECS) != len(EXPECTED_CASE_ORDER):
        stale_reasons.append("terminal_truth_bridge_case_count_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS != EXPECTED_CASE_MARKERS:
        stale_reasons.append("terminal_truth_bridge_case_markers_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER != EXPECTED_SURFACE_MARKER:
        stale_reasons.append("terminal_truth_bridge_surface_marker_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS != EXPECTED_SURFACE_CONSTRAINTS:
        stale_reasons.append("terminal_truth_bridge_surface_constraints_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROOF_LANES != EXPECTED_SURFACE_CONSTRAINTS[-2:]:
        stale_reasons.append("terminal_truth_bridge_proof_lanes_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_VALIDATOR != EXPECTED_VALIDATOR_COMMAND[1]:
        stale_reasons.append("terminal_truth_bridge_validator_path_drift")
    if RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE != EXPECTED_PROBE_COMMAND[1]:
        stale_reasons.append("terminal_truth_bridge_probe_path_drift")
    if (
        EXPECTED_REVIEW_REQUIRED_CASE_MARKER
        != RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_REVIEW_REQUIRED_CASE_MARKER
    ):
        stale_reasons.append("terminal_truth_bridge_review_required_case_marker_drift")

    expected_boundary_source_fields = tuple(
        f"one_look.{field}"
        for field in RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_ONE_LOOK_FIELDS
        if f"one_look.{field}" in EXPECTED_BOUNDARY_FIELDS
    )
    if expected_boundary_source_fields != EXPECTED_BOUNDARY_FIELDS:
        stale_reasons.append("terminal_truth_bridge_boundary_source_fields_drift")

    if _derive_terminal_truth_active_runtime_fields() != EXPECTED_ACTIVE_RUNTIME_FIELDS:
        stale_reasons.append("active_runtime_terminal_truth_bridge_source_fields_drift")

    probe_spec = next(
        (
            spec for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS
            if spec.script_rel == EXPECTED_PROBE_COMMAND[1]
        ),
        None,
    )
    if probe_spec is None:
        stale_reasons.append("governance_probe_projection_missing_terminal_truth_bridge_probe")
    else:
        if probe_spec.summary_key != EXPECTED_PROBE_SUMMARY_KEY:
            stale_reasons.append("governance_probe_projection_bridge_summary_key_drift")
        if probe_spec.one_look_field != EXPECTED_PROBE_ONE_LOOK_FIELD:
            stale_reasons.append("governance_probe_projection_bridge_one_look_field_drift")
        if probe_spec.status_fields != EXPECTED_PROBE_STATUS_FIELDS:
            stale_reasons.append("governance_probe_projection_bridge_status_fields_drift")
        if probe_spec.keep_fields != EXPECTED_PROBE_KEEP_FIELDS:
            stale_reasons.append("governance_probe_projection_bridge_keep_fields_drift")

    capture_map = release_readiness_governance_probe_capture_script_map()
    if capture_map.get(EXPECTED_PROBE_COMMAND[1]) != EXPECTED_PROBE_SUMMARY_KEY:
        stale_reasons.append("governance_probe_capture_map_missing_terminal_truth_bridge_probe")

    structured_specs = release_readiness_governance_probe_structured_capture_specs()
    structured_spec = structured_specs.get(EXPECTED_PROBE_SUMMARY_KEY) or {}
    if tuple(structured_spec.get("status_fields", ())) != EXPECTED_PROBE_STATUS_FIELDS:
        stale_reasons.append("governance_probe_structured_bridge_status_fields_drift")
    if tuple(structured_spec.get("keep_fields", ())) != EXPECTED_PROBE_KEEP_FIELDS:
        stale_reasons.append("governance_probe_structured_bridge_keep_fields_drift")

    summary_defaults = release_readiness_governance_probe_summary_defaults()
    if str((summary_defaults.get(EXPECTED_PROBE_SUMMARY_KEY) or {}).get("status") or "").upper() != STATUS_UNKNOWN:
        stale_reasons.append("governance_probe_summary_defaults_bridge_status_drift")

    post_closure_commands = _build_post_closure_command_index()
    if EXPECTED_VALIDATOR_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}"
        )
    if EXPECTED_PROBE_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_probe:{' '.join(EXPECTED_PROBE_COMMAND)}"
        )

    summary_validator_text = _read_text((repo_root / SUMMARY_VALIDATOR_REL).resolve())
    boundary_validator_text = _read_text((repo_root / BOUNDARY_VALIDATOR_REL).resolve())
    summary_binding_probe_text = _read_text((repo_root / SUMMARY_BINDING_PROBE_REL).resolve())
    for label, text in (
        ("summary_validator", summary_validator_text),
        ("boundary_validator", boundary_validator_text),
    ):
        if "RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS" not in text:
            stale_reasons.append(f"{label}_missing_terminal_truth_bridge_surface_constraints")

    if EXPECTED_PROBE_SUMMARY_KEY not in summary_binding_probe_text:
        stale_reasons.append(
            f"summary_binding_probe_missing_token:{EXPECTED_PROBE_SUMMARY_KEY}"
        )

    for label, path in (
        ("summary_doc", docs.summary_path),
        ("governance_doc", docs.governance_path),
        ("review_doc", docs.review_path),
    ):
        text = _read_text(path)
        for marker in EXPECTED_SURFACE_CONSTRAINTS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_terminal_truth_bridge_marker:{marker}")

    payload[STATUS_KEY] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_CODE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
