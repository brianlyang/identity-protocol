#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    ADMITTED_DELTA_ONLY,
    CLASSIFICATION,
    CONTRACT_ID,
    CURRENT_SCHEMA_VERSION,
    DEFAULT_VERSIONED_REGISTRY_REL,
    EXPECTED_ALLOWED_ACTIONS,
    EXPECTED_EXECUTABLE_SURFACES,
    EXPECTED_FIXED_WRITE_SET,
    EXPECTED_ROLE_BINDINGS,
    FAIL_CLOSE_TOKEN,
    FORBIDDEN_HOST_PATH_LITERAL,
    PROBE_COMMAND,
    PROBE_EXPECTED_STATUS,
    RECEIPT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    VALIDATOR_COMMAND,
    VALIDATOR_EXPECTED_STATUS,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    emit,
    ensure_registration_transaction_execution_context,
    get_lane,
    load_yaml,
    repo_root,
    resolve_registry_bundle,
    route_next_role,
)


TARGET_LANE_ID = "control_plane_protocol_feedback_instance_state_runner_hardening"
REGISTRATION_LANE_ID = "control_plane_lane_registration_transaction_only"
REQUIRED_DOC_TOKENS = [
    "contract_id: `control_plane_protocol_feedback_instance_state_runner_hardening`",
    "classification: `existing_surface_alignment`",
    "control_plane_protocol_feedback_instance_state_runner_hardening_execution_contract_not_machine_authoritative",
    "validate_protocol_feedback_sidecar_contract.py",
    "run_protocol_feedback_sidecar_contract_probes_ci.sh",
    "run_protocol_feedback_ssot_archival_probes_ci.sh",
    "run_sidecar_cwd_parity_probes_ci.sh",
    "validate_identity_state_consistency.py",
    "cwd_must_equal_repo_root",
    "TMPDIR=$PWD/.tmp",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def _scan_host_path_literals(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    root = repo_root()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_HOST_PATH_LITERAL in text:
            failures.append(f"absolute_host_path_literal:{path.resolve().relative_to(root).as_posix()}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle()
        lane = get_lane(bundle.registry_doc, ACTIVE_LANE_ID)
        registration_lane = get_lane(bundle.registry_doc, REGISTRATION_LANE_ID)
        checks = []
        failures = []

        binding_ok, binding_detail = ensure_registration_transaction_execution_context(bundle)
        _record(checks, failures, "control_plane_execution_context", binding_ok, binding_detail)
        _record(
            checks,
            failures,
            "current_registry_schema",
            bundle.current_doc.get("schema_version") == CURRENT_SCHEMA_VERSION,
            "current registry uses control-plane current schema",
        )
        _record(
            checks,
            failures,
            "current_registry_contract",
            bundle.current_doc.get("contract_id") == CONTRACT_ID
            and bundle.current_doc.get("classification") == CLASSIFICATION
            and bundle.current_doc.get("active_lane_id") == ACTIVE_LANE_ID
            and bundle.current_doc.get("active_file") == DEFAULT_VERSIONED_REGISTRY_REL.as_posix()
            and bundle.current_doc.get("read_only_input_surfaces") == [],
            "current registry pointer is bound to the active protocol-feedback instance-state hardening lane",
        )
        _record(
            checks,
            failures,
            "versioned_registry_contract",
            bundle.registry_doc.get("schema_version") == SCHEMA_VERSION
            and bundle.registry_doc.get("contract_id") == CONTRACT_ID
            and bundle.registry_doc.get("classification") == CLASSIFICATION
            and bundle.registry_doc.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION
            and bundle.registry_doc.get("active_lane_id") == ACTIVE_LANE_ID,
            "versioned registry top contract matches the active hardening lane",
        )
        _record(
            checks,
            failures,
            "registration_lane_closed",
            registration_lane.get("status") == "closure_done"
            and registration_lane.get("active") is False
            and registration_lane.get("next_role") == "auditor",
            "registration-only lane is no longer the active lane",
        )
        _record(
            checks,
            failures,
            "target_lane_shape",
            lane.get("lane_id") == TARGET_LANE_ID
            and lane.get("classification") == CLASSIFICATION
            and lane.get("status") == "architect_ready"
            and lane.get("active") is True
            and lane.get("execution_mode") == "split_roles"
            and lane.get("writer_role") == "executor"
            and lane.get("role_bindings") == EXPECTED_ROLE_BINDINGS,
            "target lane exposes a full executable split-role contract",
        )
        _record(
            checks,
            failures,
            "lane_commands_and_statuses",
            lane.get("validator_command") == VALIDATOR_COMMAND
            and lane.get("probe_command") == PROBE_COMMAND
            and lane.get("validator_expected_status") == VALIDATOR_EXPECTED_STATUS
            and lane.get("probe_expected_status") == PROBE_EXPECTED_STATUS
            and lane.get("scope_lock_allowed_actions") == EXPECTED_ALLOWED_ACTIONS,
            "target lane commands and status contracts are machine-locked",
        )
        _record(
            checks,
            failures,
            "fixed_write_set_and_delta",
            lane.get("exact_fixed_write_set") == EXPECTED_FIXED_WRITE_SET
            and lane.get("read_only_input_surfaces") == []
            and lane.get("admitted_delta_only") == ADMITTED_DELTA_ONLY
            and lane.get("fail_close_token") == FAIL_CLOSE_TOKEN,
            "fixed write set is exact and narrowed to the target hardening contract",
        )
        root = repo_root()
        executable_paths = [(root / rel).resolve() for rel in EXPECTED_EXECUTABLE_SURFACES]
        missing = [path.relative_to(root).as_posix() for path in executable_paths if not path.exists()]
        _record(
            checks,
            failures,
            "executable_surface_presence",
            not missing,
            missing or "all target executable validator/probe surfaces exist",
        )
        host_path_failures = _scan_host_path_literals([path for path in executable_paths if path.exists()])
        _record(
            checks,
            failures,
            "cwd_and_absolute_host_path_adjudication",
            not host_path_failures,
            host_path_failures or "target executable surfaces use repo-root binding only; forbidden reusable absolute host-path literals are absent",
        )
        doc_text = (root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP document exposes the active target-lane execution contract and path-risk adjudication",
        )
        runtime_literal_failures = check_forbidden_runtime_literals(canonical_package_paths(root))
        _record(
            checks,
            failures,
            "runtime_tuple_literal_pollution",
            not runtime_literal_failures,
            runtime_literal_failures or "canonical package files contain no forbidden concrete runtime tuple literals",
        )
        _record(
            checks,
            failures,
            "next_role_resolution",
            route_next_role(lane)["identity_id"] == EXPECTED_ROLE_BINDINGS["executor"]
            and route_next_role(lane, status_override="closure_done")["identity_id"] == EXPECTED_ROLE_BINDINGS["auditor"],
            "executor owns closure; auditor owns the post-closure acceptance hop",
        )
        payload = {
            "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
            "checks": checks,
            "failures": failures,
            "registry_current": str(bundle.current_registry.relative_to(bundle.repo_root)),
            "registry_versioned": str(bundle.versioned_registry.relative_to(bundle.repo_root)),
        }
        emit(payload, json_only=args.json_only)
        return 1 if failures else 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
