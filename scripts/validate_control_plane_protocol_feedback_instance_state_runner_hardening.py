#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    CLASSIFICATION,
    CONTRACT_ID,
    CURRENT_SCHEMA_VERSION,
    DEFAULT_OWNER_BINDING_CURRENT_REL,
    DEFAULT_VERSIONED_REGISTRY_REL,
    EXPECTED_EXECUTABLE_SURFACES,
    EXPECTED_OWNER_BINDINGS,
    FORBIDDEN_HOST_PATH_PATTERN,
    RECEIPT_SCHEMA_VERSION,
    REGISTRATION_TRANSACTION_LANE_ID,
    SCHEMA_VERSION,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    display_path,
    emit,
    ensure_registration_transaction_execution_context,
    get_lane,
    resolve_registry_bundle,
    route_next_role,
)

TARGET_LANE_ID = "control_plane_protocol_feedback_instance_state_runner_hardening"
ACCEPTABLE_VERSIONED_REFS = {
    DEFAULT_VERSIONED_REGISTRY_REL.as_posix(),
    "control-plane-lane-registry.v1.yaml",
}
ACCEPTABLE_OWNER_CURRENT_REFS = {
    DEFAULT_OWNER_BINDING_CURRENT_REL.as_posix(),
    "control-plane-owner-binding.current.yaml",
}
ACCEPTABLE_CURRENT_CONTRACTS = {
    CONTRACT_ID,
    TARGET_LANE_ID,
}
ACCEPTABLE_CURRENT_ACTIVE_LANES = {
    ACTIVE_LANE_ID,
    TARGET_LANE_ID,
}
TARGET_FIXED_WRITE_SET = [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py",
    "scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh",
]
TARGET_ADMITTED_DELTA_ONLY = [
    "protocol_feedback_instance_state_runner_contract_only",
    "protocol_feedback_validator_probe_surface_reuse_only",
    "protocol_feedback_live_closure_state_admissibility_only",
    "stage_equality_target_redefined_to_machine_authoritative_necessity_subset_only",
    "no_absolute_host_path_literals_in_target_executable_surfaces",
    "no_reopen_of_control_plane_lane_registration_transaction_only",
]
TARGET_FAIL_CLOSE_TOKEN = (
    "control_plane_protocol_feedback_instance_state_runner_hardening_execution_contract_not_machine_authoritative"
)
TARGET_VALIDATOR_COMMAND = (
    "TMPDIR=$PWD/.tmp python3 scripts/validate_control_plane_protocol_feedback_instance_state_runner_hardening.py --json-only"
)
TARGET_PROBE_COMMAND = (
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_control_plane_protocol_feedback_instance_state_runner_hardening_probes_ci.sh"
)
REQUIRED_DOC_TOKENS = [
    "## Historical lane compatibility",
    "`control_plane_protocol_feedback_instance_state_runner_hardening`",
    "owner-binding overlay",
    "cwd_must_equal_repo_root",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def _scan_host_path_literals(paths: list[Path], repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_HOST_PATH_PATTERN.search(text):
            failures.append(f"absolute_host_path_literal:{display_path(path, repo_root)}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        registration_lane = get_lane(bundle.registry_doc, REGISTRATION_TRANSACTION_LANE_ID)
        target_lane = get_lane(bundle.registry_doc, TARGET_LANE_ID)
        checks = []
        failures = []

        ctx_ok, ctx_detail = ensure_registration_transaction_execution_context(bundle)
        _record(checks, failures, "control_plane_execution_context", ctx_ok, ctx_detail)
        _record(
            checks,
            failures,
            "current_registry_contract",
            bundle.current_doc.get("schema_version") == CURRENT_SCHEMA_VERSION
            and bundle.current_doc.get("classification") == CLASSIFICATION
            and str(bundle.current_doc.get("active_file", "")).strip() in ACCEPTABLE_VERSIONED_REFS
            and str(bundle.current_doc.get("owner_binding_file", "")).strip() in ACCEPTABLE_OWNER_CURRENT_REFS
            and bundle.current_doc.get("contract_id") in ACCEPTABLE_CURRENT_CONTRACTS
            and bundle.current_doc.get("active_lane_id") in ACCEPTABLE_CURRENT_ACTIVE_LANES,
            "current registry may point at the active overlay lane or a protocol-feedback shadow current file while still resolving the owner-binding overlay",
        )
        _record(
            checks,
            failures,
            "versioned_registry_contract",
            bundle.registry_doc.get("schema_version") == SCHEMA_VERSION
            and bundle.registry_doc.get("contract_id") == CONTRACT_ID
            and bundle.registry_doc.get("classification") == CLASSIFICATION
            and bundle.registry_doc.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION,
            "versioned registry remains anchored to the overlay hardening family while preserving the protocol-feedback lane row",
        )

        role_binding_hits = []
        if "role_bindings" in bundle.current_doc:
            role_binding_hits.append("current_registry.role_bindings")
        if "role_bindings" in bundle.registry_doc:
            role_binding_hits.append("versioned_registry.role_bindings")
        for row in bundle.registry_doc.get("lanes", []):
            if "role_bindings" in row:
                role_binding_hits.append(f"lane:{row.get('lane_id')}")
        _record(
            checks,
            failures,
            "canonical_role_bindings_removed",
            not role_binding_hits,
            role_binding_hits or "protocol-feedback historical row remains machine-readable without canonical concrete role_bindings",
        )
        _record(
            checks,
            failures,
            "registration_lane_preserved",
            registration_lane.get("status") == "closure_done"
            and registration_lane.get("active") is False
            and registration_lane.get("next_role") == "auditor",
            "registration-only lane remains closed and preserved after the overlay split",
        )
        _record(
            checks,
            failures,
            "target_lane_contract_preserved",
            target_lane.get("classification") == CLASSIFICATION
            and target_lane.get("status") in {"closure_done", "preflight_passed", "architect_ready"}
            and target_lane.get("active") is False
            and target_lane.get("execution_mode") == "split_roles"
            and target_lane.get("writer_role") == "executor"
            and target_lane.get("read_only_roles") == ["architect", "auditor", "office"]
            and target_lane.get("exact_fixed_write_set") == TARGET_FIXED_WRITE_SET
            and target_lane.get("read_only_input_surfaces") == []
            and target_lane.get("validator_command") == TARGET_VALIDATOR_COMMAND
            and target_lane.get("probe_command") == TARGET_PROBE_COMMAND
            and target_lane.get("validator_expected_status") == "PASS_REQUIRED"
            and target_lane.get("probe_expected_status") == "PASS"
            and target_lane.get("admitted_delta_only") == TARGET_ADMITTED_DELTA_ONLY
            and target_lane.get("fail_close_token") == TARGET_FAIL_CLOSE_TOKEN
            and target_lane.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION,
            "protocol-feedback lane remains preserved as a historical executable contract and can still be replayed through a shadow current pointer",
        )
        executable_paths = [(bundle.repo_root / rel).resolve() for rel in EXPECTED_EXECUTABLE_SURFACES]
        missing = [display_path(path, bundle.repo_root) for path in executable_paths if not path.exists()]
        _record(
            checks,
            failures,
            "executable_surface_presence",
            not missing,
            missing or "all protocol-feedback executable surfaces remain present",
        )
        host_path_failures = _scan_host_path_literals(
            [path for path in executable_paths if path.exists()],
            bundle.repo_root,
        )
        _record(
            checks,
            failures,
            "cwd_and_absolute_host_path_adjudication",
            not host_path_failures,
            host_path_failures or "protocol-feedback executable surfaces remain free of forbidden reusable absolute host-path literals",
        )
        preflight_projection = route_next_role(
            target_lane,
            bundle=bundle,
            status_override="preflight_passed",
        )
        closure_projection = route_next_role(
            target_lane,
            bundle=bundle,
            status_override="closure_done",
        )
        _record(
            checks,
            failures,
            "route_compatibility_via_owner_binding_overlay",
            preflight_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["executor"]
            and closure_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["auditor"],
            "protocol-feedback lane remains route-compatible because concrete identity resolution now comes from the owner-binding overlay",
        )
        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP doc records protocol-feedback historical compatibility under the overlay split",
        )
        runtime_literal_failures = check_forbidden_runtime_literals(
            canonical_package_paths(bundle.repo_root, lane=target_lane)
        )
        _record(
            checks,
            failures,
            "runtime_tuple_literal_pollution",
            not runtime_literal_failures,
            runtime_literal_failures or "protocol-feedback historical package surfaces remain free of forbidden concrete runtime tuple literals",
        )

        payload = {
            "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
            "checks": checks,
            "failures": failures,
            "registry_current": display_path(bundle.current_registry, bundle.repo_root),
            "registry_versioned": display_path(bundle.versioned_registry, bundle.repo_root),
        }
        emit(payload, json_only=args.json_only)
        return 1 if failures else 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
