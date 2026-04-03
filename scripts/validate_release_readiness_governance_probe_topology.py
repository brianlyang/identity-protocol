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
from repo_root_resolution_common import resolve_repo_root
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS,
    RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES,
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SCRIPT,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SCRIPT,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SUMMARY_KEY,
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_SUMMARY_KEY,
    release_readiness_governance_probe_capture_script_map,
    release_readiness_governance_probe_structured_capture_specs,
    release_readiness_governance_probe_summary_defaults,
)
from release_readiness_governance_probe_topology_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE_COMMAND,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROOF_LANES,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_KEEP_FIELDS,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_ONE_LOOK_FIELD,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_STATUS_FIELDS,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_SUMMARY_KEY,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR,
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR_COMMAND,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_KEY = "release_readiness_governance_probe_topology_status"
ERR_SCAN = "IP-RRGPT-001"
ERR_BINDING = "IP-RRGPT-002"

EXPECTED_SCRIPT_ORDER: tuple[str, ...] = (
    "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh",
    "scripts/ci/run_full_scan_health_projection_probes_ci.sh",
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SCRIPT,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh",
    "scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh",
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SCRIPT,
    "scripts/ci/run_required_gate_surface_drift_probes_ci.sh",
    "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
    "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
    "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
    "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
    "scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh",
    "scripts/ci/run_strict_live_contract_resolution_probes_ci.sh",
    "scripts/ci/run_execution_report_selection_convergence_probes_ci.sh",
    "scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh",
    "scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh",
    "scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh",
)
EXPECTED_SUMMARY_KEY_ORDER: tuple[str, ...] = (
    "terminal_truth_boundary_outer_surface_e2e_probe",
    "full_scan_health_projection_probe",
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY,
    "release_readiness_terminal_truth_bridge_probe",
    "release_readiness_governance_probe_topology_probe",
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_SUMMARY_KEY,
    "required_gate_surface_drift_probe",
    "release_readiness_summary_binding_probe",
    "release_readiness_continuation_probe",
    "release_plane_context_resolution_probe",
    "active_execution_report_pointer_locality_probe",
    "strict_live_active_pointer_locality_probe",
    "strict_live_contract_resolution_probe",
    "execution_report_selection_convergence_probe",
    "identity_codex_launcher_convergence_probe",
    "identity_transport_fleet_closure_convergence_probe",
    "active_runtime_pack_closure_convergence_probe",
)
EXPECTED_ONE_LOOK_FIELD_ORDER: tuple[str, ...] = (
    "terminal_truth_boundary_outer_surface_e2e_probe_status",
    "full_scan_health_projection_probe_status",
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
    "release_readiness_terminal_truth_bridge_probe_status",
    "release_readiness_governance_probe_topology_probe_status",
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    "required_gate_surface_drift_probe_status",
    "release_readiness_summary_binding_probe_status",
    "release_readiness_continuation_probe_status",
    "release_plane_context_resolution_probe_status",
    "active_execution_report_pointer_locality_probe_status",
    "strict_live_active_pointer_locality_probe_status",
    "strict_live_contract_resolution_probe_status",
    "execution_report_selection_convergence_probe_status",
    "identity_codex_launcher_convergence_probe_status",
    "identity_transport_fleet_closure_convergence_probe_status",
    "active_runtime_pack_closure_convergence_probe_status",
)
EXPECTED_PROJECTION_MARKER = (
    "governance_probe_projection="
    + "|".join(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELD_ORDER)
)
EXPECTED_VALIDATOR_SCRIPT = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR
EXPECTED_PROBE_SCRIPT = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE
EXPECTED_VALIDATOR_COMMAND = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR_COMMAND
EXPECTED_PROBE_COMMAND = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE_COMMAND
EXPECTED_SELF_SUMMARY_KEY = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_SUMMARY_KEY
EXPECTED_SELF_ONE_LOOK_FIELD = RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_ONE_LOOK_FIELD
EXPECTED_SELF_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_STATUS_FIELDS
)
EXPECTED_SELF_KEEP_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_KEEP_FIELDS
)

PROJECTION_COMMON_REL = "scripts/release_readiness_governance_probe_projection_common.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
SUMMARY_BINDING_PROBE_REL = "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
CONTINUATION_MARKER_REL = "scripts/release_closure_continuation_marker_common.py"
PROBE_REQUIRED_TOKENS: tuple[str, ...] = (
    "release_readiness_governance_probe_topology_common",
    "governance_probe_topology_validator",
    "governance_probe_topology_probe",
    "governance_probe_topology_validator_command_literal",
    "governance_probe_topology_probe_command_literal",
    "governance_probe_topology_self_summary_key",
    "governance_probe_topology_self_one_look_field",
    "governance_probe_topology_self_check_reason",
    "governance_probe_summary_keys_not_unique",
    "governance_probe_one_look_field_order_changed",
    "continuation_markers_missing_governance_probe_surface_constraints",
)


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
            "Validate release-readiness governance-probe projection topology remains "
            "a shared primitive with a dedicated proof lane."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    derived_script_order = tuple(spec.script_rel for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS)
    derived_summary_key_order = tuple(spec.summary_key for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS)
    derived_one_look_field_order = tuple(
        spec.one_look_field for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS
    )
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        "probe_count": len(RELEASE_READINESS_GOVERNANCE_PROBE_SPECS),
        "script_order": list(derived_script_order),
        "summary_key_order": list(derived_summary_key_order),
        "one_look_field_order": list(derived_one_look_field_order),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if not RELEASE_READINESS_GOVERNANCE_PROBE_SPECS:
        stale_reasons.append("governance_probe_specs_empty")
    if len(set(derived_script_order)) != len(derived_script_order):
        stale_reasons.append("governance_probe_scripts_not_unique")
    if len(set(derived_summary_key_order)) != len(derived_summary_key_order):
        stale_reasons.append("governance_probe_summary_keys_not_unique")
    if len(set(derived_one_look_field_order)) != len(derived_one_look_field_order):
        stale_reasons.append("governance_probe_one_look_fields_not_unique")
    if derived_script_order != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("governance_probe_script_order_changed")
    if derived_summary_key_order != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("governance_probe_summary_key_order_changed")
    if derived_one_look_field_order != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("governance_probe_one_look_field_order_changed")
    if RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("governance_probe_owner_lanes_constant_drift")
    if RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("governance_probe_one_look_fields_constant_drift")
    if RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER != EXPECTED_PROJECTION_MARKER:
        stale_reasons.append("governance_probe_projection_marker_drift")
    if RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_MARKER != EXPECTED_PROJECTION_MARKER:
        stale_reasons.append("governance_probe_surface_marker_drift")
    if not RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS:
        stale_reasons.append("governance_probe_surface_constraints_empty")
    else:
        if RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_MARKER not in RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS:
            stale_reasons.append("governance_probe_surface_constraints_marker_drift")
        for owner_lane in EXPECTED_SCRIPT_ORDER:
            if owner_lane not in RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS:
                stale_reasons.append(
                    f"governance_probe_surface_constraints_missing_owner_lane:{owner_lane}"
                )

    capture_map = release_readiness_governance_probe_capture_script_map()
    if tuple(capture_map.keys()) != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("governance_probe_capture_script_order_changed")
    if tuple(capture_map.values()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("governance_probe_capture_summary_order_changed")

    structured_specs = release_readiness_governance_probe_structured_capture_specs()
    if tuple(structured_specs.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("governance_probe_structured_capture_order_changed")
    self_structured_spec = structured_specs.get(EXPECTED_SELF_SUMMARY_KEY) or {}
    if tuple(self_structured_spec.get("status_fields", ())) != EXPECTED_SELF_STATUS_FIELDS:
        stale_reasons.append("governance_probe_self_structured_status_fields_drift")
    if tuple(self_structured_spec.get("keep_fields", ())) != EXPECTED_SELF_KEEP_FIELDS:
        stale_reasons.append("governance_probe_self_structured_keep_fields_drift")

    summary_defaults = release_readiness_governance_probe_summary_defaults()
    if tuple(summary_defaults.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("governance_probe_summary_defaults_order_changed")
    if str((summary_defaults.get(EXPECTED_SELF_SUMMARY_KEY) or {}).get("status") or "").upper() != STATUS_UNKNOWN:
        stale_reasons.append("governance_probe_self_summary_default_status_drift")

    post_closure_commands = _build_post_closure_command_index()
    if EXPECTED_VALIDATOR_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}"
        )
    if EXPECTED_PROBE_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_probe:{' '.join(EXPECTED_PROBE_COMMAND)}"
        )
    for owner_lane in EXPECTED_SCRIPT_ORDER:
        expected_command = ("bash", owner_lane)
        if owner_lane.endswith(".sh") and expected_command not in post_closure_commands:
            stale_reasons.append(f"post_closure_bundle_missing_governance_probe_owner:{owner_lane}")

    surface_payload = build_governed_runtime_summary_surface_payload("release_readiness_summary")
    constraints = tuple(surface_payload.get("operational_constraints") or ())
    if EXPECTED_PROJECTION_MARKER not in constraints:
        stale_reasons.append("governed_surface_missing_governance_probe_projection_marker")
    if EXPECTED_PROBE_SCRIPT not in constraints:
        stale_reasons.append(
            f"governed_surface_missing_governance_probe_owner:{EXPECTED_PROBE_SCRIPT}"
        )

    projection_common_text = _read_text((repo_root / PROJECTION_COMMON_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_GOVERNANCE_PROBE_SPECS",
        "RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS",
        "RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES",
        "RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER",
        "release_readiness_governance_probe_capture_script_map",
        "release_readiness_governance_probe_structured_capture_specs",
        "release_readiness_governance_probe_summary_defaults",
        "apply_release_readiness_governance_probe_one_look(",
        "for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS:",
        "one_look[spec.one_look_field]",
        EXPECTED_PROBE_SCRIPT,
        EXPECTED_SELF_SUMMARY_KEY,
        EXPECTED_SELF_ONE_LOOK_FIELD,
    ):
        if required_token not in projection_common_text:
            stale_reasons.append(f"governance_probe_projection_common_missing_token:{required_token}")

    topology_common_text = _read_text(
        (repo_root / "scripts/release_readiness_governance_probe_topology_common.py").resolve()
    )
    for required_token in (
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR_COMMAND",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE_COMMAND",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROOF_LANES",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_SUMMARY_KEY",
        "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_ONE_LOOK_FIELD",
    ):
        if required_token not in topology_common_text:
            stale_reasons.append(f"governance_probe_topology_common_missing_token:{required_token}")

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token in (
        '["python3", "scripts/validate_release_readiness_governance_probe_topology.py", "--json-only"]',
        '["bash", "scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh"]',
    ):
        if required_token not in readiness_check_text:
            stale_reasons.append(f"release_readiness_check_missing_token:{required_token}")

    summary_binding_probe_text = _read_text((repo_root / SUMMARY_BINDING_PROBE_REL).resolve())
    for required_token in (
        "release_readiness_governance_probe_topology_probe",
        "release_readiness_governance_probe_topology_probe_status",
    ):
        if required_token not in summary_binding_probe_text:
            stale_reasons.append(f"summary_binding_probe_missing_token:{required_token}")

    continuation_marker_text = _read_text((repo_root / CONTINUATION_MARKER_REL).resolve())
    if "RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS" not in continuation_marker_text:
        stale_reasons.append("continuation_markers_missing_governance_probe_surface_constraints")

    probe_script_text = _read_text((repo_root / EXPECTED_PROBE_SCRIPT).resolve())
    for required_token in PROBE_REQUIRED_TOKENS:
        if required_token not in probe_script_text:
            stale_reasons.append(f"probe_script_missing_required_token:{required_token}")

    payload["stale_reasons"] = stale_reasons
    payload["surface_constraint_count"] = len(constraints)
    payload["probe_script_required_token_count"] = len(PROBE_REQUIRED_TOKENS)

    if stale_reasons:
        payload["error_code"] = ERR_BINDING
    else:
        payload[STATUS_KEY] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""

    _emit(payload, json_only=args.json_only)
    return 0 if payload[STATUS_KEY] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
