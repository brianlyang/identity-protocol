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
    RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES,
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES,
    release_readiness_repo_global_closure_capture_script_map,
    release_readiness_repo_global_closure_structured_capture_specs,
    release_readiness_repo_global_closure_summary_defaults,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_KEY = "release_readiness_repo_global_closure_topology_status"
ERR_SCAN = "IP-RRRGCT-001"
ERR_BINDING = "IP-RRRGCT-002"

EXPECTED_SCRIPT_ORDER: tuple[str, ...] = (
    "scripts/validate_executable_surface_runtime_literal_lock.py",
    "scripts/validate_required_gate_surface_drift.py",
    "scripts/validate_runtime_file_boundary_governance.py",
    "scripts/validate_issue_register_consistency.py",
    "scripts/validate_protocol_broadcast_doc_control.py",
    "scripts/validate_protocol_governed_subdomain_doc_control_registry.py",
    "scripts/check_identity_codex_launcher_migration_closure.py",
    "scripts/check_identity_broadcast_migration_closure.py",
    "scripts/check_identity_communication_transport_closure.py",
    "scripts/check_unique_entry_contract_migration_closure.py",
    "scripts/check_version_baseline_migration_closure.py",
)
EXPECTED_SUMMARY_KEY_ORDER: tuple[str, ...] = (
    "executable_surface_runtime_literal_lock",
    "required_gate_surface_drift",
    "runtime_file_boundary_governance",
    "issue_register_consistency",
    "protocol_broadcast_doc_control",
    "protocol_governed_subdomain_doc_control_registry",
    "identity_codex_launcher_migration_closure",
    "identity_broadcast_migration_closure",
    "identity_communication_transport_closure",
    "unique_entry_contract_migration_closure",
    "version_baseline_migration_closure",
)
EXPECTED_ONE_LOOK_FIELD_ORDER: tuple[str, ...] = (
    "executable_surface_runtime_literal_lock_status",
    "required_gate_surface_drift_status",
    "runtime_file_boundary_governance_status",
    "issue_register_consistency_status",
    "protocol_broadcast_doc_control_status",
    "protocol_governed_subdomain_doc_control_registry_status",
    "identity_codex_launcher_migration_closure_status",
    "identity_broadcast_migration_closure_status",
    "identity_communication_transport_closure_status",
    "unique_entry_contract_migration_closure_status",
    "version_baseline_migration_closure_status",
)
EXPECTED_SUMMARY_BINDINGS: tuple[tuple[str, str], ...] = (
    ("required_gate_surface_drift", "required_gate_surface_drift_status"),
    ("runtime_file_boundary_governance", "runtime_file_boundary_governance_status"),
    ("issue_register_consistency", "issue_register_consistency_status"),
    ("protocol_broadcast_doc_control", "protocol_broadcast_doc_control_status"),
    (
        "protocol_governed_subdomain_doc_control_registry",
        "protocol_governed_subdomain_doc_control_registry_status",
    ),
    ("identity_codex_launcher_migration_closure", "identity_codex_launcher_migration_closure_status"),
    ("identity_broadcast_migration_closure", "identity_broadcast_migration_closure_status"),
    ("identity_communication_transport_closure", "identity_communication_transport_closure_status"),
    ("unique_entry_contract_migration_closure", "unique_entry_contract_migration_closure_status"),
    ("version_baseline_migration_closure", "version_baseline_migration_closure_status"),
)
EXPECTED_ACTIVE_RUNTIME_SUMMARY_KEYS: tuple[str, ...] = (
    "identity_codex_launcher_migration_closure",
    "identity_broadcast_migration_closure",
    "identity_communication_transport_closure",
    "unique_entry_contract_migration_closure",
    "version_baseline_migration_closure",
)
EXPECTED_CHECKED_IDENTITY_COUNT_FIELDS: tuple[str, ...] = tuple(
    f"one_look.{summary_key}_checked_identity_count"
    for summary_key in EXPECTED_ACTIVE_RUNTIME_SUMMARY_KEYS
)
EXPECTED_TOPOLOGY_PROOF_LANES: tuple[str, ...] = (
    "scripts/validate_release_readiness_repo_global_closure_topology.py",
    "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
)
EXPECTED_PROJECTION_MARKER = (
    "repo_global_closure_projection="
    + "|".join(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELD_ORDER)
)
EXPECTED_OUTER_SURFACE_E2E_MARKERS: tuple[str, ...] = (
    *(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELD_ORDER),
    *EXPECTED_CHECKED_IDENTITY_COUNT_FIELDS,
    *EXPECTED_SCRIPT_ORDER,
    *EXPECTED_TOPOLOGY_PROOF_LANES,
    EXPECTED_PROJECTION_MARKER,
)
EXPECTED_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_PROJECTION_MARKER,
    *EXPECTED_CHECKED_IDENTITY_COUNT_FIELDS,
    *EXPECTED_SCRIPT_ORDER,
    *EXPECTED_TOPOLOGY_PROOF_LANES,
)
EXPECTED_ONE_LOOK_FAMILY_ID = "repo_global_closure"
EXPECTED_ONE_LOOK_APPLIER_NAME = "apply_release_readiness_repo_global_closure_one_look"
EXPECTED_VALIDATOR_SCRIPT = "scripts/validate_release_readiness_repo_global_closure_topology.py"
EXPECTED_PROBE_SCRIPT = "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh"
EXPECTED_VALIDATOR_COMMAND = ("python3", EXPECTED_VALIDATOR_SCRIPT, "--json-only")
EXPECTED_PROBE_COMMAND = ("bash", EXPECTED_PROBE_SCRIPT)
EXPECTED_GOVERNANCE_SUMMARY_KEY = "release_readiness_repo_global_closure_topology_probe"
EXPECTED_GOVERNANCE_ONE_LOOK_FIELD = "release_readiness_repo_global_closure_topology_probe_status"
EXPECTED_GOVERNANCE_STATUS_FIELDS: tuple[str, ...] = (
    "release_readiness_repo_global_closure_topology_probe_status",
)
EXPECTED_GOVERNANCE_KEEP_FIELDS: tuple[str, ...] = ("positive_validator_output",)

PROJECTION_COMMON_REL = "scripts/release_readiness_repo_global_closure_projection_common.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
ONE_LOOK_TOPOLOGY_COMMON_REL = "scripts/release_readiness_one_look_topology_common.py"
GOVERNANCE_PROJECTION_COMMON_REL = "scripts/release_readiness_governance_probe_projection_common.py"
SUMMARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_summary.py"
BOUNDARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_boundary.py"
SUMMARY_PROBE_REL = "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
BOUNDARY_PROBE_REL = "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
SUMMARY_BINDING_PROBE_REL = "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
PROBE_REQUIRED_TOKENS: tuple[str, ...] = (
    "scripts/validate_release_readiness_repo_global_closure_topology.py --json-only",
    "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
    "repo_global_closure_summary_keys_not_unique",
    "repo_global_closure_one_look_field_order_changed",
    "release_readiness_check_missing_repo_global_capture_map_injection",
    "release_readiness_check_missing_repo_global_structured_capture_injection",
    "release_readiness_check_missing_repo_global_summary_defaults_injection",
    "repo_global_summary_probe_missing_projection_marker_resolution",
    "repo_global_summary_probe_missing_checked_count_resolution",
    "repo_global_summary_probe_missing_topology_lane_resolution",
    "repo_global_boundary_probe_missing_projection_marker_resolution",
    "repo_global_boundary_probe_missing_checked_count_resolution",
    "repo_global_boundary_probe_missing_topology_lane_resolution",
    "summary_binding_probe_missing_token:release_readiness_repo_global_closure_topology_probe",
    "post_closure_bundle_missing_validator:scripts/validate_release_readiness_repo_global_closure_topology.py --json-only",
    "post_closure_bundle_missing_probe:scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
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


def _find_expected_governance_probe_spec() -> Any | None:
    for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS:
        if spec.script_rel == EXPECTED_PROBE_SCRIPT:
            return spec
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate release-readiness repo-global closure topology remains a shared primitive "
            "with dedicated proof lanes and cross-surface absorption."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    derived_script_order = tuple(spec.script_rel for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS)
    derived_summary_key_order = tuple(spec.summary_key for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS)
    derived_one_look_field_order = tuple(
        spec.one_look_field for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS
    )
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        "repo_global_lane_count": len(RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS),
        "script_order": list(derived_script_order),
        "summary_key_order": list(derived_summary_key_order),
        "one_look_field_order": list(derived_one_look_field_order),
        "topology_proof_lanes": list(RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if not RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS:
        stale_reasons.append("repo_global_closure_specs_empty")
    if len(set(derived_script_order)) != len(derived_script_order):
        stale_reasons.append("repo_global_closure_scripts_not_unique")
    if len(set(derived_summary_key_order)) != len(derived_summary_key_order):
        stale_reasons.append("repo_global_closure_summary_keys_not_unique")
    if len(set(derived_one_look_field_order)) != len(derived_one_look_field_order):
        stale_reasons.append("repo_global_closure_one_look_fields_not_unique")
    if derived_script_order != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("repo_global_closure_script_order_changed")
    if derived_summary_key_order != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("repo_global_closure_summary_key_order_changed")
    if derived_one_look_field_order != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("repo_global_closure_one_look_field_order_changed")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS != EXPECTED_SUMMARY_BINDINGS:
        stale_reasons.append("repo_global_closure_summary_bindings_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("repo_global_closure_owner_lane_constant_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("repo_global_closure_one_look_constant_drift")
    if RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS != EXPECTED_ACTIVE_RUNTIME_SUMMARY_KEYS:
        stale_reasons.append("repo_global_closure_active_runtime_summary_keys_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS != EXPECTED_CHECKED_IDENTITY_COUNT_FIELDS:
        stale_reasons.append("repo_global_closure_checked_identity_count_fields_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES != EXPECTED_TOPOLOGY_PROOF_LANES:
        stale_reasons.append("repo_global_closure_topology_proof_lanes_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER != EXPECTED_PROJECTION_MARKER:
        stale_reasons.append("repo_global_closure_projection_marker_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS != EXPECTED_SURFACE_CONSTRAINTS:
        stale_reasons.append("repo_global_closure_surface_constraints_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS != EXPECTED_OUTER_SURFACE_E2E_MARKERS:
        stale_reasons.append("repo_global_closure_outer_surface_e2e_markers_drift")
    if RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS != tuple(
        f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELD_ORDER
    ):
        stale_reasons.append("repo_global_closure_one_look_markers_drift")

    capture_map = release_readiness_repo_global_closure_capture_script_map()
    if tuple(capture_map.keys()) != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("repo_global_closure_capture_script_order_changed")
    if tuple(capture_map.values()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("repo_global_closure_capture_summary_order_changed")

    structured_specs = release_readiness_repo_global_closure_structured_capture_specs()
    if tuple(structured_specs.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("repo_global_closure_structured_capture_order_changed")
    executable_surface_spec = structured_specs.get("executable_surface_runtime_literal_lock") or {}
    if tuple(executable_surface_spec.get("keep_fields", ())) != ("violation_count", "stale_reasons"):
        stale_reasons.append("repo_global_closure_executable_surface_keep_fields_drift")
    launcher_closure_spec = structured_specs.get("identity_codex_launcher_migration_closure") or {}
    if tuple(launcher_closure_spec.get("keep_fields", ())) != (
        "checked_identity_count",
        "violation_count",
        "runtime_catalog_metadata_hygiene_status",
        "launcher_runtime_admissibility_projection_status",
        "launcher_runtime_admissibility_status",
        "stale_reasons",
    ):
        stale_reasons.append("repo_global_closure_launcher_keep_fields_drift")

    summary_defaults = release_readiness_repo_global_closure_summary_defaults()
    if tuple(summary_defaults.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("repo_global_closure_summary_defaults_order_changed")
    if any(
        str((summary_defaults.get(summary_key) or {}).get("status") or "").upper() != STATUS_UNKNOWN
        for summary_key in EXPECTED_SUMMARY_KEY_ORDER
    ):
        stale_reasons.append("repo_global_closure_summary_default_status_drift")

    one_look_family_spec = next(
        (spec for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS if spec.family_id == EXPECTED_ONE_LOOK_FAMILY_ID),
        None,
    )
    if one_look_family_spec is None:
        stale_reasons.append(f"one_look_family_missing:{EXPECTED_ONE_LOOK_FAMILY_ID}")
    elif one_look_family_spec.applier_name != EXPECTED_ONE_LOOK_APPLIER_NAME:
        stale_reasons.append(
            f"one_look_family_applier_name_mismatch:{one_look_family_spec.applier_name}"
        )

    projection_common_text = _read_text((repo_root / PROJECTION_COMMON_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS",
        "release_readiness_repo_global_closure_capture_script_map",
        "release_readiness_repo_global_closure_structured_capture_specs",
        "release_readiness_repo_global_closure_summary_defaults",
        "apply_release_readiness_repo_global_closure_one_look(",
        EXPECTED_VALIDATOR_SCRIPT,
        EXPECTED_PROBE_SCRIPT,
    ):
        if required_token not in projection_common_text:
            stale_reasons.append(f"repo_global_projection_common_missing_token:{required_token}")

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token, stale_reason in (
        (
            "**release_readiness_repo_global_closure_capture_script_map(),",
            "release_readiness_check_missing_repo_global_capture_map_injection",
        ),
        (
            "**release_readiness_repo_global_closure_structured_capture_specs(),",
            "release_readiness_check_missing_repo_global_structured_capture_injection",
        ),
        (
            "**release_readiness_repo_global_closure_summary_defaults(),",
            "release_readiness_check_missing_repo_global_summary_defaults_injection",
        ),
        (
            '["python3", "scripts/validate_release_readiness_repo_global_closure_topology.py", "--json-only"]',
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}",
        ),
        (
            '["bash", "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh"]',
            f"post_closure_bundle_missing_probe:{' '.join(EXPECTED_PROBE_COMMAND)}",
        ),
    ):
        if required_token not in readiness_check_text:
            stale_reasons.append(stale_reason)

    post_closure_commands = _build_post_closure_command_index()
    if EXPECTED_VALIDATOR_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}"
        )
    if EXPECTED_PROBE_COMMAND not in post_closure_commands:
        stale_reasons.append(
            f"post_closure_bundle_missing_probe:{' '.join(EXPECTED_PROBE_COMMAND)}"
        )

    surface_payload = build_governed_runtime_summary_surface_payload("release_readiness_summary")
    constraints = tuple(surface_payload.get("operational_constraints") or ())
    for marker in EXPECTED_SURFACE_CONSTRAINTS:
        if marker not in constraints:
            stale_reasons.append(f"governed_surface_missing_repo_global_constraint:{marker}")

    summary_validator_text = _read_text((repo_root / SUMMARY_VALIDATOR_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS",
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER",
        "summary_doc_missing_outer_surface_e2e_marker",
    ):
        if required_token not in summary_validator_text:
            stale_reasons.append(f"summary_validator_missing_token:{required_token}")

    boundary_validator_text = _read_text((repo_root / BOUNDARY_VALIDATOR_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS",
        "missing_repo_global_closure_boundary_marker",
    ):
        if required_token not in boundary_validator_text:
            stale_reasons.append(f"boundary_validator_missing_token:{required_token}")

    summary_probe_text = _read_text((repo_root / SUMMARY_PROBE_REL).resolve())
    for required_token, stale_reason in (
        (
            '"release_readiness_repo_global_closure_projection_common"',
            "repo_global_summary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"',
            "repo_global_summary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD"',
            "repo_global_summary_probe_missing_checked_count_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT"',
            "repo_global_summary_probe_missing_topology_lane_resolution",
        ),
    ):
        if required_token not in summary_probe_text:
            stale_reasons.append(stale_reason)

    boundary_probe_text = _read_text((repo_root / BOUNDARY_PROBE_REL).resolve())
    for required_token, stale_reason in (
        (
            '"release_readiness_repo_global_closure_projection_common"',
            "repo_global_boundary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"',
            "repo_global_boundary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD"',
            "repo_global_boundary_probe_missing_checked_count_resolution",
        ),
        (
            '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT"',
            "repo_global_boundary_probe_missing_topology_lane_resolution",
        ),
    ):
        if required_token not in boundary_probe_text:
            stale_reasons.append(stale_reason)

    governance_probe_spec = _find_expected_governance_probe_spec()
    if governance_probe_spec is None:
        stale_reasons.append(f"governance_probe_spec_missing:{EXPECTED_PROBE_SCRIPT}")
    else:
        if governance_probe_spec.summary_key != EXPECTED_GOVERNANCE_SUMMARY_KEY:
            stale_reasons.append(
                f"governance_probe_spec_summary_key_mismatch:{governance_probe_spec.summary_key}"
            )
        if governance_probe_spec.one_look_field != EXPECTED_GOVERNANCE_ONE_LOOK_FIELD:
            stale_reasons.append(
                f"governance_probe_spec_one_look_field_mismatch:{governance_probe_spec.one_look_field}"
            )
        if tuple(governance_probe_spec.status_fields) != EXPECTED_GOVERNANCE_STATUS_FIELDS:
            stale_reasons.append("governance_probe_spec_status_fields_drift")
        if tuple(governance_probe_spec.keep_fields) != EXPECTED_GOVERNANCE_KEEP_FIELDS:
            stale_reasons.append("governance_probe_spec_keep_fields_drift")

    if EXPECTED_PROBE_SCRIPT not in RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES:
        stale_reasons.append(f"governance_probe_owner_lane_missing:{EXPECTED_PROBE_SCRIPT}")
    if f"one_look.{EXPECTED_GOVERNANCE_ONE_LOOK_FIELD}" not in RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER:
        stale_reasons.append(
            "governance_probe_projection_missing_one_look_field:"
            + f"one_look.{EXPECTED_GOVERNANCE_ONE_LOOK_FIELD}"
        )

    governance_projection_common_text = _read_text((repo_root / GOVERNANCE_PROJECTION_COMMON_REL).resolve())
    for required_token in (
        EXPECTED_PROBE_SCRIPT,
        EXPECTED_GOVERNANCE_SUMMARY_KEY,
        EXPECTED_GOVERNANCE_ONE_LOOK_FIELD,
        "positive_validator_output",
    ):
        if required_token not in governance_projection_common_text:
            stale_reasons.append(f"governance_projection_common_missing_token:{required_token}")

    summary_binding_probe_text = _read_text((repo_root / SUMMARY_BINDING_PROBE_REL).resolve())
    for required_token in (
        EXPECTED_GOVERNANCE_SUMMARY_KEY,
        EXPECTED_GOVERNANCE_ONE_LOOK_FIELD,
    ):
        if required_token not in summary_binding_probe_text:
            stale_reasons.append(f"summary_binding_probe_missing_token:{required_token}")

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
