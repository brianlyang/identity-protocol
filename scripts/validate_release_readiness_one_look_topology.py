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
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_KEEP_FIELDS,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_STATUS_FIELDS,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
    release_readiness_governance_probe_summary_defaults,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_APPLIER_NAMES,
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER,
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
    RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_PROBE,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_PROBE_COMMAND,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_VALIDATOR,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_VALIDATOR_COMMAND,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_KEY = "release_readiness_one_look_topology_status"
ERR_SCAN = "IP-RROLT-001"
ERR_BINDING = "IP-RROLT-002"

EXPECTED_FAMILY_ORDER: tuple[str, ...] = (
    "foundational",
    "support_preflight",
    "selected_check_scope",
    "release_cloud_evidence",
    "terminal_truth_boundary",
    "health_report_experience_writeback",
    "required_gate_bundle",
    "repo_global_closure",
    "active_runtime_closure",
    "governance_probe",
)
EXPECTED_FAMILY_APPLIER_NAMES: tuple[str, ...] = (
    "apply_release_readiness_foundational_one_look",
    "apply_release_readiness_support_preflight_one_look",
    "apply_release_readiness_selected_check_scope_one_look",
    "apply_release_readiness_release_cloud_evidence_one_look",
    "apply_release_readiness_terminal_truth_boundary_one_look",
    "apply_release_readiness_health_report_experience_writeback_one_look",
    "apply_release_readiness_required_gate_bundle_one_look",
    "apply_release_readiness_repo_global_closure_one_look",
    "apply_release_readiness_active_runtime_closure_one_look",
    "apply_release_readiness_governance_probe_one_look",
)
EXPECTED_FAMILY_ORDER_MARKER = (
    "release_readiness_one_look_family_order=" + "|".join(EXPECTED_FAMILY_ORDER)
)
EXPECTED_TOPOLOGY_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_FAMILY_ORDER_MARKER,
    *(f"release_readiness_one_look_family={family_id}" for family_id in EXPECTED_FAMILY_ORDER),
)

EXPECTED_VALIDATOR_SCRIPT = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_VALIDATOR
EXPECTED_PROBE_SCRIPT = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_PROBE
EXPECTED_VALIDATOR_COMMAND = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_VALIDATOR_COMMAND
EXPECTED_PROBE_COMMAND = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_PROBE_COMMAND
EXPECTED_SUMMARY_KEY = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY
EXPECTED_ONE_LOOK_FIELD = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD
EXPECTED_KEEP_FIELDS: tuple[str, ...] = RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_KEEP_FIELDS
EXPECTED_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_STATUS_FIELDS
)

PROJECTION_COMMON_REL = "scripts/release_readiness_one_look_projection_common.py"
TOPOLOGY_COMMON_REL = "scripts/release_readiness_one_look_topology_common.py"
GOVERNANCE_PROJECTION_COMMON_REL = "scripts/release_readiness_governance_probe_projection_common.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
PROBE_REQUIRED_TOKENS: tuple[str, ...] = (
    "one_look_topology_validator",
    "one_look_topology_probe",
    "one_look_topology_validator_command_literal",
    "one_look_topology_probe_command_literal",
    "one_look_topology_probe_one_look_field",
    "one_look_topology_probe_self_check_reason",
    "projection_common_missing_shared_topology_apply",
    "topology_family_ids_not_unique",
    f"governance_probe_projection_missing_one_look_field:one_look.{EXPECTED_ONE_LOOK_FIELD}",
    "post_closure_bundle_missing_validator:",
    "post_closure_bundle_missing_probe:",
)
SHARED_TOPOLOGY_APPLY_CALL = "apply_release_readiness_one_look_families(summary, one_look)"


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
            "Validate the governed release-readiness one-look topology remains a "
            "shared primitive with a dedicated proof lane."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    derived_family_ids = tuple(spec.family_id for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS)
    derived_applier_names = tuple(spec.applier_name for spec in RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS)
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        "family_count": len(RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS),
        "family_order": list(derived_family_ids),
        "family_applier_names": list(derived_applier_names),
        "expected_summary_key": EXPECTED_SUMMARY_KEY,
        "expected_one_look_field": EXPECTED_ONE_LOOK_FIELD,
        "expected_probe_script": EXPECTED_PROBE_SCRIPT,
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if not RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS:
        stale_reasons.append("topology_family_specs_empty")
    if len(set(derived_family_ids)) != len(derived_family_ids):
        stale_reasons.append("topology_family_ids_not_unique")
    if len(set(derived_applier_names)) != len(derived_applier_names):
        stale_reasons.append("topology_applier_names_not_unique")
    if derived_family_ids != EXPECTED_FAMILY_ORDER:
        stale_reasons.append(
            "topology_family_order_changed:" + "|".join(derived_family_ids)
        )
    if derived_applier_names != EXPECTED_FAMILY_APPLIER_NAMES:
        stale_reasons.append(
            "topology_family_applier_names_changed:" + "|".join(derived_applier_names)
        )
    if RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER != EXPECTED_FAMILY_ORDER:
        stale_reasons.append("topology_family_order_constant_drift")
    if RELEASE_READINESS_ONE_LOOK_FAMILY_APPLIER_NAMES != EXPECTED_FAMILY_APPLIER_NAMES:
        stale_reasons.append("topology_family_applier_name_constant_drift")
    if RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER != EXPECTED_FAMILY_ORDER_MARKER:
        stale_reasons.append("topology_family_order_marker_drift")
    if RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS != EXPECTED_TOPOLOGY_SURFACE_CONSTRAINTS:
        stale_reasons.append("topology_surface_constraints_drift")

    projection_common_text = _read_text((repo_root / PROJECTION_COMMON_REL).resolve())
    if SHARED_TOPOLOGY_APPLY_CALL not in projection_common_text:
        stale_reasons.append("projection_common_missing_shared_topology_apply")
    for applier_name in EXPECTED_FAMILY_APPLIER_NAMES:
        if applier_name in projection_common_text:
            stale_reasons.append(f"projection_common_contains_direct_family_applier:{applier_name}")

    topology_common_text = _read_text((repo_root / TOPOLOGY_COMMON_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS",
        "RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER",
        "RELEASE_READINESS_ONE_LOOK_FAMILY_APPLIER_NAMES",
        "RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER",
        "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS",
        "apply_release_readiness_one_look_families(",
    ):
        if required_token not in topology_common_text:
            stale_reasons.append(f"topology_common_missing_token:{required_token}")

    governance_spec = _find_expected_governance_probe_spec()
    if governance_spec is None:
        stale_reasons.append(f"governance_probe_spec_missing:{EXPECTED_PROBE_SCRIPT}")
    else:
        if governance_spec.summary_key != EXPECTED_SUMMARY_KEY:
            stale_reasons.append(
                f"governance_probe_spec_summary_key_mismatch:{governance_spec.summary_key}"
            )
        if governance_spec.one_look_field != EXPECTED_ONE_LOOK_FIELD:
            stale_reasons.append(
                f"governance_probe_spec_one_look_field_mismatch:{governance_spec.one_look_field}"
            )
        if tuple(governance_spec.status_fields) != EXPECTED_STATUS_FIELDS:
            stale_reasons.append(
                "governance_probe_spec_status_fields_drift:"
                + "|".join(tuple(governance_spec.status_fields))
            )
        if tuple(governance_spec.keep_fields) != EXPECTED_KEEP_FIELDS:
            stale_reasons.append(
                "governance_probe_spec_keep_fields_drift:"
                + "|".join(tuple(governance_spec.keep_fields))
            )

    if EXPECTED_PROBE_SCRIPT not in RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES:
        stale_reasons.append(f"governance_probe_owner_lane_missing:{EXPECTED_PROBE_SCRIPT}")
    if f"one_look.{EXPECTED_ONE_LOOK_FIELD}" not in RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER:
        stale_reasons.append(
            f"governance_probe_projection_missing_one_look_field:one_look.{EXPECTED_ONE_LOOK_FIELD}"
        )

    capture_script = readiness_check.SUMMARY_CAPTURE_SCRIPTS.get(EXPECTED_PROBE_SCRIPT)
    if capture_script != EXPECTED_SUMMARY_KEY:
        stale_reasons.append(
            f"summary_capture_script_map_missing:{EXPECTED_PROBE_SCRIPT}:{capture_script or STATUS_UNKNOWN}"
        )
    structured_capture_spec = readiness_check.STRUCTURED_SUMMARY_CAPTURE_SPECS.get(
        EXPECTED_SUMMARY_KEY, {}
    )
    if tuple(structured_capture_spec.get("status_fields", ())) != EXPECTED_STATUS_FIELDS:
        stale_reasons.append(
            f"structured_capture_spec_missing_status_fields:{EXPECTED_SUMMARY_KEY}"
        )
    if tuple(structured_capture_spec.get("keep_fields", ())) != EXPECTED_KEEP_FIELDS:
        stale_reasons.append(f"structured_capture_spec_keep_fields_drift:{EXPECTED_SUMMARY_KEY}")
    summary_defaults = release_readiness_governance_probe_summary_defaults()
    if str((summary_defaults.get(EXPECTED_SUMMARY_KEY) or {}).get("status") or "").upper() != STATUS_UNKNOWN:
        stale_reasons.append(f"summary_defaults_missing_status:{EXPECTED_SUMMARY_KEY}")

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
    for marker in EXPECTED_TOPOLOGY_SURFACE_CONSTRAINTS:
        if marker not in constraints:
            stale_reasons.append(f"topology_surface_missing_constraint:{marker}")
    if RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER not in constraints:
        stale_reasons.append("topology_surface_missing_governance_probe_projection")
    if EXPECTED_PROBE_SCRIPT not in constraints:
        stale_reasons.append(
            f"topology_surface_missing_governance_probe_owner:{EXPECTED_PROBE_SCRIPT}"
        )

    governance_projection_text = _read_text((repo_root / GOVERNANCE_PROJECTION_COMMON_REL).resolve())
    for required_token in (
        EXPECTED_PROBE_SCRIPT,
        EXPECTED_SUMMARY_KEY,
        EXPECTED_ONE_LOOK_FIELD,
        "positive_validator_output",
    ):
        if required_token not in governance_projection_text:
            stale_reasons.append(f"governance_projection_common_missing_token:{required_token}")

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token in (
        json.dumps(list(EXPECTED_VALIDATOR_COMMAND)),
        json.dumps(list(EXPECTED_PROBE_COMMAND)),
    ):
        if required_token not in readiness_check_text:
            stale_reasons.append(f"release_readiness_check_missing_token:{required_token}")

    probe_script_text = _read_text((repo_root / EXPECTED_PROBE_SCRIPT).resolve())
    for required_token in PROBE_REQUIRED_TOKENS:
        if required_token not in probe_script_text:
            stale_reasons.append(f"probe_script_missing_required_token:{required_token}")

    payload["stale_reasons"] = stale_reasons
    payload["governance_probe_owner_lane_count"] = len(RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES)
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
