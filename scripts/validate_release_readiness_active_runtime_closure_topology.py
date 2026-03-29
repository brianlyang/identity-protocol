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
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_ONE_LOOK_FIELDS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_OWNER_LANES,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_COMMAND,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_KEEP_FIELDS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_STATUS_FIELDS,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROOF_LANES,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_VALIDATOR_COMMAND,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
    release_readiness_active_runtime_closure_capture_script_map,
    release_readiness_active_runtime_closure_structured_capture_specs,
    release_readiness_active_runtime_closure_summary_defaults,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES,
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_GOVERNANCE_PROBE_SPECS,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
STATUS_KEY = "release_readiness_active_runtime_closure_topology_status"
ERR_SCAN = "IP-RRACT-001"
ERR_BINDING = "IP-RRACT-002"

EXPECTED_SCRIPT_ORDER: tuple[str, ...] = (
    "scripts/validate_identity_codex_launcher.py",
    "scripts/validate_identity_context_continuity.py",
    "scripts/validate_identity_context_continuity_receipts.py",
    "scripts/validate_identity_reentry_brief.py",
    "scripts/validate_identity_reentry_consumption.py",
    "scripts/validate_identity_dialogue_retention.py",
    "scripts/validate_identity_artifact_family_routing.py",
    "scripts/validate_identity_broadcast_delivery.py",
    "scripts/validate_identity_communication_transport.py",
    "scripts/validate_identity_experience_writeback.py",
    "scripts/validate_identity_weak_live_linkage.py",
    "scripts/validate_terminal_truth_cleanliness.py",
)
EXPECTED_SUMMARY_KEY_ORDER: tuple[str, ...] = (
    "identity_codex_launcher",
    "identity_context_continuity",
    "identity_context_continuity_receipts",
    "identity_reentry_brief",
    "identity_reentry_consumption",
    "identity_dialogue_retention",
    "identity_artifact_family_routing",
    "identity_broadcast_delivery",
    "identity_communication_transport",
    "identity_experience_writeback",
    "identity_weak_live_linkage",
    "identity_terminal_truth_cleanliness",
)
EXPECTED_ONE_LOOK_FIELD_ORDER: tuple[str, ...] = (
    "identity_codex_launcher_status",
    "identity_context_continuity_status",
    "identity_context_continuity_receipt_family_status",
    "identity_reentry_brief_status",
    "identity_reentry_consumption_status",
    "protocol_dialogue_retention_status",
    "artifact_family_routing_status",
    "identity_broadcast_delivery_status",
    "identity_communication_transport_status",
    "identity_experience_writeback_status",
    "identity_weak_live_linkage_status",
    "identity_terminal_truth_cleanliness_status",
)
EXPECTED_DETAIL_FIELDS: tuple[str, ...] = (
    "one_look.identity_codex_launcher_ambient_runtime_default_status",
    "one_look.identity_experience_writeback_report_selection_mode",
    "one_look.identity_experience_writeback_report_authority_class",
    "one_look.identity_experience_writeback_report_pointer_resolution_mode",
    "one_look.identity_communication_transport_reply_transport_status",
    "one_look.identity_weak_live_operational_closure_class",
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
EXPECTED_TOPOLOGY_PROOF_LANES: tuple[str, ...] = (
    "scripts/validate_release_readiness_active_runtime_closure_topology.py",
    "scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh",
)
EXPECTED_PROJECTION_MARKER = (
    "active_runtime_closure_projection="
    + "|".join(f"one_look.{field}" for field in EXPECTED_ONE_LOOK_FIELD_ORDER)
)
EXPECTED_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    EXPECTED_PROJECTION_MARKER,
    *EXPECTED_DETAIL_FIELDS,
    *EXPECTED_SCRIPT_ORDER,
    *EXPECTED_TOPOLOGY_PROOF_LANES,
)
EXPECTED_ONE_LOOK_FAMILY_ID = "active_runtime_closure"
EXPECTED_ONE_LOOK_APPLIER_NAME = "apply_release_readiness_active_runtime_closure_one_look"
EXPECTED_VALIDATOR_SCRIPT = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT
EXPECTED_PROBE_SCRIPT = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT
EXPECTED_VALIDATOR_COMMAND = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_VALIDATOR_COMMAND
EXPECTED_PROBE_COMMAND = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_COMMAND
EXPECTED_GOVERNANCE_SUMMARY_KEY = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY
EXPECTED_GOVERNANCE_ONE_LOOK_FIELD = RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD
EXPECTED_GOVERNANCE_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_STATUS_FIELDS
)
EXPECTED_GOVERNANCE_KEEP_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_KEEP_FIELDS
)

PROJECTION_COMMON_REL = "scripts/release_readiness_active_runtime_closure_projection_common.py"
READINESS_CHECK_REL = "scripts/release_readiness_check.py"
ONE_LOOK_TOPOLOGY_COMMON_REL = "scripts/release_readiness_one_look_topology_common.py"
GOVERNANCE_PROJECTION_COMMON_REL = "scripts/release_readiness_governance_probe_projection_common.py"
SUMMARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_summary.py"
BOUNDARY_VALIDATOR_REL = "scripts/validate_v16x_release_closure_boundary.py"
SUMMARY_PROBE_REL = "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
BOUNDARY_PROBE_REL = "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
SUMMARY_BINDING_PROBE_REL = "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
PROBE_REQUIRED_TOKENS: tuple[str, ...] = (
    "release_readiness_active_runtime_closure_projection_common",
    "active_runtime_topology_validator",
    "active_runtime_topology_probe",
    "active_runtime_topology_validator_command_literal",
    "active_runtime_topology_probe_command_literal",
    "active_runtime_topology_probe_summary_key",
    "active_runtime_topology_probe_one_look_field",
    "active_runtime_closure_summary_keys_not_unique",
    "active_runtime_closure_one_look_field_order_changed",
    "release_readiness_check_missing_capture_map_injection",
    "release_readiness_check_missing_structured_capture_injection",
    "release_readiness_check_missing_summary_defaults_injection",
    "active_runtime_summary_probe_missing_projection_marker_resolution",
    "active_runtime_boundary_probe_missing_detail_field_resolution",
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
            "Validate release-readiness active-runtime closure topology remains a shared primitive "
            "with dedicated proof lanes and cross-surface absorption."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    derived_script_order = tuple(spec.script_rel for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS)
    derived_summary_key_order = tuple(spec.summary_key for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS)
    derived_one_look_field_order = tuple(
        spec.one_look_field for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
    )
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        "active_runtime_lane_count": len(RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS),
        "script_order": list(derived_script_order),
        "summary_key_order": list(derived_summary_key_order),
        "one_look_field_order": list(derived_one_look_field_order),
        "topology_proof_lanes": list(RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROOF_LANES),
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []

    if not RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS:
        stale_reasons.append("active_runtime_closure_specs_empty")
    if len(set(derived_script_order)) != len(derived_script_order):
        stale_reasons.append("active_runtime_closure_scripts_not_unique")
    if len(set(derived_summary_key_order)) != len(derived_summary_key_order):
        stale_reasons.append("active_runtime_closure_summary_keys_not_unique")
    if len(set(derived_one_look_field_order)) != len(derived_one_look_field_order):
        stale_reasons.append("active_runtime_closure_one_look_fields_not_unique")
    if derived_script_order != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("active_runtime_closure_script_order_changed")
    if derived_summary_key_order != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("active_runtime_closure_summary_key_order_changed")
    if derived_one_look_field_order != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("active_runtime_closure_one_look_field_order_changed")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_OWNER_LANES != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("active_runtime_closure_owner_lane_constant_drift")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_ONE_LOOK_FIELDS != EXPECTED_ONE_LOOK_FIELD_ORDER:
        stale_reasons.append("active_runtime_closure_one_look_constant_drift")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS != EXPECTED_DETAIL_FIELDS:
        stale_reasons.append("active_runtime_closure_detail_fields_drift")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROOF_LANES != EXPECTED_TOPOLOGY_PROOF_LANES:
        stale_reasons.append("active_runtime_closure_topology_proof_lanes_drift")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER != EXPECTED_PROJECTION_MARKER:
        stale_reasons.append("active_runtime_closure_projection_marker_drift")
    if RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS != EXPECTED_SURFACE_CONSTRAINTS:
        stale_reasons.append("active_runtime_closure_surface_constraints_drift")

    capture_map = release_readiness_active_runtime_closure_capture_script_map()
    if tuple(capture_map.keys()) != EXPECTED_SCRIPT_ORDER:
        stale_reasons.append("active_runtime_closure_capture_script_order_changed")
    if tuple(capture_map.values()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("active_runtime_closure_capture_summary_order_changed")

    structured_specs = release_readiness_active_runtime_closure_structured_capture_specs()
    if tuple(structured_specs.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("active_runtime_closure_structured_capture_order_changed")
    experience_writeback_spec = structured_specs.get("identity_experience_writeback") or {}
    if tuple(experience_writeback_spec.get("keep_fields", ())) != (
        "report_selection_mode",
        "report_selected_authority_class",
        "report_pointer_resolution_mode",
        "writeback_status",
    ):
        stale_reasons.append("active_runtime_closure_experience_writeback_keep_fields_drift")
    terminal_truth_spec = structured_specs.get("identity_terminal_truth_cleanliness") or {}
    if tuple(terminal_truth_spec.get("keep_fields", ())) != (
        "execution_closure_status",
        "canonical_publishable_result_status",
        "terminal_truth_class",
        "terminal_state_machine_status",
        "terminal_state_class",
        "negative_feedback_class",
        "negative_feedback_terminal_veto_status",
        "loopback_required",
        "publishable",
        "next_state_after_veto",
        "terminal_clean_alias_surface_status",
    ):
        stale_reasons.append("active_runtime_closure_terminal_truth_keep_fields_drift")
    if tuple(
        (
            spec.one_look_passthrough_fields
            for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
            if spec.summary_key == "identity_terminal_truth_cleanliness"
        ),
    ) != (
        (
            ("execution_closure_status", "identity_terminal_truth_execution_closure_status"),
            (
                "canonical_publishable_result_status",
                "identity_terminal_truth_canonical_publishable_result_status",
            ),
            ("terminal_truth_class", "identity_terminal_truth_class"),
            ("terminal_state_machine_status", "identity_terminal_truth_state_machine_status"),
            ("terminal_state_class", "identity_terminal_truth_state_class"),
            ("negative_feedback_class", "identity_terminal_truth_negative_feedback_class"),
            (
                "negative_feedback_terminal_veto_status",
                "identity_terminal_truth_negative_feedback_terminal_veto_status",
            ),
            ("loopback_required", "identity_terminal_truth_loopback_required"),
            ("publishable", "identity_terminal_truth_publishable"),
            ("next_state_after_veto", "identity_terminal_truth_next_state_after_veto"),
            ("terminal_clean_alias_surface_status", "identity_terminal_truth_alias_surface_status"),
        ),
    ):
        stale_reasons.append("active_runtime_closure_terminal_truth_passthrough_fields_drift")

    summary_defaults = release_readiness_active_runtime_closure_summary_defaults()
    if tuple(summary_defaults.keys()) != EXPECTED_SUMMARY_KEY_ORDER:
        stale_reasons.append("active_runtime_closure_summary_defaults_order_changed")
    if any(
        str((summary_defaults.get(summary_key) or {}).get("status") or "").upper() != STATUS_UNKNOWN
        for summary_key in EXPECTED_SUMMARY_KEY_ORDER
    ):
        stale_reasons.append("active_runtime_closure_summary_default_status_drift")

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
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_ONE_LOOK_FIELDS",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_OWNER_LANES",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROOF_LANES",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS",
        "release_readiness_active_runtime_closure_capture_script_map",
        "release_readiness_active_runtime_closure_structured_capture_specs",
        "release_readiness_active_runtime_closure_summary_defaults",
        "apply_release_readiness_active_runtime_closure_one_look(",
        EXPECTED_VALIDATOR_SCRIPT,
        EXPECTED_PROBE_SCRIPT,
    ):
        if required_token not in projection_common_text:
            stale_reasons.append(f"active_runtime_projection_common_missing_token:{required_token}")

    readiness_check_text = _read_text((repo_root / READINESS_CHECK_REL).resolve())
    for required_token, stale_reason in (
        (
            "**release_readiness_active_runtime_closure_capture_script_map(),",
            "release_readiness_check_missing_capture_map_injection",
        ),
        (
            "**release_readiness_active_runtime_closure_structured_capture_specs(),",
            "release_readiness_check_missing_structured_capture_injection",
        ),
        (
            "**release_readiness_active_runtime_closure_summary_defaults(),",
            "release_readiness_check_missing_summary_defaults_injection",
        ),
        (
            '["python3", "scripts/validate_release_readiness_active_runtime_closure_topology.py", "--json-only"]',
            f"post_closure_bundle_missing_validator:{' '.join(EXPECTED_VALIDATOR_COMMAND)}",
        ),
        (
            '["bash", "scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh"]',
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
            stale_reasons.append(f"governed_surface_missing_active_runtime_constraint:{marker}")

    summary_validator_text = _read_text((repo_root / SUMMARY_VALIDATOR_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS",
        "summary_doc_missing_active_runtime_closure_projection_marker",
    ):
        if required_token not in summary_validator_text:
            stale_reasons.append(f"summary_validator_missing_token:{required_token}")

    boundary_validator_text = _read_text((repo_root / BOUNDARY_VALIDATOR_REL).resolve())
    for required_token in (
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS",
        "missing_active_runtime_closure_projection_marker",
    ):
        if required_token not in boundary_validator_text:
            stale_reasons.append(f"boundary_validator_missing_token:{required_token}")

    summary_probe_text = _read_text((repo_root / SUMMARY_PROBE_REL).resolve())
    for required_token in (
        '"release_readiness_active_runtime_closure_projection_common"',
        '"RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"',
        '"RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD"',
    ):
        if required_token not in summary_probe_text:
            stale_reasons.append("active_runtime_summary_probe_missing_projection_marker_resolution")
            break

    boundary_probe_text = _read_text((repo_root / BOUNDARY_PROBE_REL).resolve())
    for required_token, stale_reason in (
        (
            '"release_readiness_active_runtime_closure_projection_common"',
            "active_runtime_boundary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"',
            "active_runtime_boundary_probe_missing_projection_marker_resolution",
        ),
        (
            '"RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD"',
            "active_runtime_boundary_probe_missing_detail_field_resolution",
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
        "release_readiness_active_runtime_closure_projection_common",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD",
        "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_KEEP_FIELDS",
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
