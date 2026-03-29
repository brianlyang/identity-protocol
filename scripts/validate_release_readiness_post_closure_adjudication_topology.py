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
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
    release_readiness_governance_probe_capture_script_map,
    release_readiness_governance_probe_structured_capture_specs,
    release_readiness_governance_probe_summary_defaults,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_COMMAND_SEQUENCE,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_COMMAND,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_KEEP_FIELDS,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_STATUS_FIELDS,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROOF_LANES,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_MARKERS,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR_COMMAND,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_KEY = "release_readiness_post_closure_adjudication_topology_status"
ERR_SCAN = "IP-RRPCAT-001"
ERR_BINDING = "IP-RRPCAT-002"

EXPECTED_STAGE_ORDER: tuple[str, ...] = (
    "runtime_summary_surface_governance",
    "one_look_topology",
    "repo_global_closure_topology",
    "active_runtime_closure_topology",
    "terminal_truth_bridge",
    "governance_probe_topology",
)
EXPECTED_COMMAND_SEQUENCE: tuple[tuple[str, ...], ...] = (
    ("bash", "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh"),
    ("python3", "scripts/validate_release_readiness_one_look_topology.py", "--json-only"),
    ("bash", "scripts/ci/run_release_readiness_one_look_topology_probes_ci.sh"),
    (
        "python3",
        "scripts/validate_release_readiness_repo_global_closure_topology.py",
        "--json-only",
    ),
    (
        "bash",
        "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
    ),
    (
        "python3",
        "scripts/validate_release_readiness_active_runtime_closure_topology.py",
        "--json-only",
    ),
    (
        "bash",
        "scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh",
    ),
    ("python3", "scripts/validate_release_readiness_terminal_truth_bridge.py", "--json-only"),
    ("bash", "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh"),
    (
        "python3",
        "scripts/validate_release_readiness_governance_probe_topology.py",
        "--json-only",
    ),
    ("bash", "scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh"),
)
EXPECTED_ORDER_MARKER = (
    "release_readiness_post_closure_adjudication_order="
    + "|".join(EXPECTED_STAGE_ORDER)
)
EXPECTED_STAGE_MARKERS: tuple[str, ...] = tuple(
    f"release_readiness_post_closure_adjudication_stage={stage_id}"
    for stage_id in EXPECTED_STAGE_ORDER
)
EXPECTED_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_ORDER_MARKER,
    *EXPECTED_STAGE_MARKERS,
    "scripts/validate_release_readiness_post_closure_adjudication_topology.py",
    "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh",
)
EXPECTED_VALIDATOR_COMMAND = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR_COMMAND
)
EXPECTED_PROBE_COMMAND = RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_COMMAND
EXPECTED_PROBE_SUMMARY_KEY = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_SUMMARY_KEY
)
EXPECTED_PROBE_ONE_LOOK_FIELD = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_ONE_LOOK_FIELD
)
EXPECTED_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_STATUS_FIELDS
)
EXPECTED_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_KEEP_FIELDS
)

PROJECTION_COMMON_REL = "scripts/release_readiness_governance_probe_projection_common.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
SUMMARY_BINDING_PROBE_REL = "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
GOVERNANCE_TOPOLOGY_VALIDATOR_REL = (
    "scripts/validate_release_readiness_governance_probe_topology.py"
)
PROBE_REQUIRED_TOKENS: tuple[str, ...] = (
    "release_readiness_post_closure_adjudication_common",
    "post_closure_adjudication_validator",
    "post_closure_adjudication_probe",
    "post_closure_adjudication_validator_command_literal",
    "post_closure_adjudication_probe_command_literal",
    "post_closure_adjudication_probe_summary_key",
    "post_closure_adjudication_probe_one_look_field",
    "post_closure_adjudication_probe_self_check_reason",
    "post_closure_adjudication_stage_order_changed",
    "post_closure_adjudication_command_slice_drift",
    "governance_probe_capture_map_missing_post_closure_adjudication_probe",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _build_post_closure_command_list() -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(command) for command in readiness_check.POST_CLOSURE_GOVERNANCE_SCRIPTS)


def _find_probe_spec() -> Any | None:
    for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS:
        if spec.script_rel == EXPECTED_PROBE_COMMAND[1]:
            return spec
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the release-readiness post-closure adjudication order remains a "
            "shared machine-owned topology rather than helper-local sequencing."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    docs = resolve_release_closure_doc_paths(repo_root)

    derived_stage_order = tuple(
        spec.stage_id for spec in RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS
    )
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        "stage_count": len(RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS),
        "stage_order": list(derived_stage_order),
        "command_sequence": [list(command) for command in RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_COMMAND_SEQUENCE],
        "surface_constraints": list(RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if not RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_SPECS:
        stale_reasons.append("post_closure_adjudication_stage_specs_empty")
    if len(set(derived_stage_order)) != len(derived_stage_order):
        stale_reasons.append("post_closure_adjudication_stage_ids_not_unique")
    if derived_stage_order != EXPECTED_STAGE_ORDER:
        stale_reasons.append("post_closure_adjudication_stage_order_changed")
    if RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER != EXPECTED_STAGE_ORDER:
        stale_reasons.append("post_closure_adjudication_order_constant_drift")
    if (
        RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_COMMAND_SEQUENCE
        != EXPECTED_COMMAND_SEQUENCE
    ):
        stale_reasons.append("post_closure_adjudication_command_sequence_drift")
    if RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER != EXPECTED_ORDER_MARKER:
        stale_reasons.append("post_closure_adjudication_order_marker_drift")
    if RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_STAGE_MARKERS != EXPECTED_STAGE_MARKERS:
        stale_reasons.append("post_closure_adjudication_stage_markers_drift")
    if (
        RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS
        != EXPECTED_SURFACE_CONSTRAINTS
    ):
        stale_reasons.append("post_closure_adjudication_surface_constraints_drift")
    if (
        RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROOF_LANES
        != EXPECTED_SURFACE_CONSTRAINTS[-2:]
    ):
        stale_reasons.append("post_closure_adjudication_proof_lanes_drift")
    if RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR != EXPECTED_VALIDATOR_COMMAND[1]:
        stale_reasons.append("post_closure_adjudication_validator_path_drift")
    if RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE != EXPECTED_PROBE_COMMAND[1]:
        stale_reasons.append("post_closure_adjudication_probe_path_drift")

    post_closure_commands = _build_post_closure_command_list()
    indices: list[int] = []
    for command in EXPECTED_COMMAND_SEQUENCE:
        try:
            indices.append(post_closure_commands.index(command))
        except ValueError:
            stale_reasons.append(f"post_closure_adjudication_missing_command:{' '.join(command)}")
    if indices:
        if indices != sorted(indices):
            stale_reasons.append("post_closure_adjudication_command_order_changed")
        else:
            start = indices[0]
            end = indices[-1] + 1
            if post_closure_commands[start:end] != EXPECTED_COMMAND_SEQUENCE:
                stale_reasons.append("post_closure_adjudication_command_slice_drift")
    if EXPECTED_VALIDATOR_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}"
        )
    if EXPECTED_PROBE_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_probe:{' '.join(EXPECTED_PROBE_COMMAND)}"
        )

    probe_spec = _find_probe_spec()
    if probe_spec is None:
        stale_reasons.append("governance_probe_projection_missing_post_closure_adjudication_probe")
    else:
        if probe_spec.summary_key != EXPECTED_PROBE_SUMMARY_KEY:
            stale_reasons.append(
                f"governance_probe_projection_post_closure_summary_key_drift:{probe_spec.summary_key}"
            )
        if probe_spec.one_look_field != EXPECTED_PROBE_ONE_LOOK_FIELD:
            stale_reasons.append(
                f"governance_probe_projection_post_closure_one_look_field_drift:{probe_spec.one_look_field}"
            )
        if tuple(probe_spec.status_fields) != EXPECTED_PROBE_STATUS_FIELDS:
            stale_reasons.append("governance_probe_projection_post_closure_status_fields_drift")
        if tuple(probe_spec.keep_fields) != EXPECTED_PROBE_KEEP_FIELDS:
            stale_reasons.append("governance_probe_projection_post_closure_keep_fields_drift")

    capture_map = release_readiness_governance_probe_capture_script_map()
    if capture_map.get(EXPECTED_PROBE_COMMAND[1]) != EXPECTED_PROBE_SUMMARY_KEY:
        stale_reasons.append("governance_probe_capture_map_missing_post_closure_adjudication_probe")

    structured_specs = release_readiness_governance_probe_structured_capture_specs()
    structured_spec = structured_specs.get(EXPECTED_PROBE_SUMMARY_KEY) or {}
    if tuple(structured_spec.get("status_fields", ())) != EXPECTED_PROBE_STATUS_FIELDS:
        stale_reasons.append("governance_probe_structured_post_closure_status_fields_drift")
    if tuple(structured_spec.get("keep_fields", ())) != EXPECTED_PROBE_KEEP_FIELDS:
        stale_reasons.append("governance_probe_structured_post_closure_keep_fields_drift")

    summary_defaults = release_readiness_governance_probe_summary_defaults()
    if (
        str((summary_defaults.get(EXPECTED_PROBE_SUMMARY_KEY) or {}).get("status") or "").upper()
        != STATUS_UNKNOWN
    ):
        stale_reasons.append("governance_probe_summary_defaults_post_closure_status_drift")

    if f"one_look.{EXPECTED_PROBE_ONE_LOOK_FIELD}" not in RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER:
        stale_reasons.append("governance_probe_projection_missing_post_closure_one_look_field")

    surface_payload = build_governed_runtime_summary_surface_payload("release_readiness_summary")
    constraints = tuple(surface_payload.get("operational_constraints") or ())
    for marker in EXPECTED_SURFACE_CONSTRAINTS:
        if marker not in constraints:
            stale_reasons.append(f"governed_surface_missing_post_closure_adjudication_marker:{marker}")

    governance_projection_text = _read_text((repo_root / PROJECTION_COMMON_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SCRIPT",
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SUMMARY_KEY",
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_ONE_LOOK_FIELD",
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_KEEP_FIELDS",
    ):
        if required_token not in governance_projection_text:
            stale_reasons.append(
                f"governance_probe_projection_common_missing_token:{required_token}"
            )

    governance_topology_text = _read_text(
        (repo_root / GOVERNANCE_TOPOLOGY_VALIDATOR_REL).resolve()
    )
    for required_token in (
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SCRIPT",
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SUMMARY_KEY",
        "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_ONE_LOOK_FIELD",
    ):
        if required_token not in governance_topology_text:
            stale_reasons.append(
                f"governance_probe_topology_validator_missing_token:{required_token}"
            )

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token in (
        '["python3", "scripts/validate_release_readiness_post_closure_adjudication_topology.py", "--json-only"]',
        '["bash", "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"]',
    ):
        if required_token not in readiness_check_text:
            stale_reasons.append(f"release_readiness_check_missing_token:{required_token}")

    summary_binding_probe_text = _read_text((repo_root / SUMMARY_BINDING_PROBE_REL).resolve())
    for required_token in (
        EXPECTED_PROBE_SUMMARY_KEY,
        EXPECTED_PROBE_ONE_LOOK_FIELD,
    ):
        if required_token not in summary_binding_probe_text:
            stale_reasons.append(f"summary_binding_probe_missing_token:{required_token}")

    for label, path in (
        ("summary_doc", docs.summary_path),
        ("governance_doc", docs.governance_path),
        ("review_doc", docs.review_path),
    ):
        text = _read_text(path)
        for marker in EXPECTED_SURFACE_CONSTRAINTS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_post_closure_adjudication_marker:{marker}"
                )

    probe_script_text = _read_text((repo_root / EXPECTED_PROBE_COMMAND[1]).resolve())
    for required_token in PROBE_REQUIRED_TOKENS:
        if required_token not in probe_script_text:
            stale_reasons.append(f"probe_script_missing_required_token:{required_token}")

    payload["surface_constraint_count"] = len(constraints)
    payload["probe_script_required_token_count"] = len(PROBE_REQUIRED_TOKENS)
    payload["stale_reasons"] = stale_reasons

    if stale_reasons:
        payload["error_code"] = ERR_BINDING
    else:
        payload[STATUS_KEY] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""

    _emit(payload, json_only=args.json_only)
    return 0 if payload[STATUS_KEY] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
