#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    ADMITTED_DELTA_ONLY,
    CLASSIFICATION,
    CONTRACT_ID,
    CURRENT_SCHEMA_VERSION,
    DEFAULT_VERSIONED_REGISTRY_REL,
    EXPECTED_ALLOWED_ACTIONS,
    EXPECTED_FIXED_WRITE_SET,
    EXPECTED_ROLE_BINDINGS,
    FAIL_CLOSE_TOKEN,
    PROBE_COMMAND,
    PROBE_EXPECTED_STATUS,
    RECEIPT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    VALIDATOR_COMMAND,
    VALIDATOR_EXPECTED_STATUS,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    emit,
    ensure_authoritative_checkout_binding,
    get_lane,
    resolve_registry_bundle,
    route_next_role,
)


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


REQUIRED_DOC_TOKENS = [
    "contract_id: `control_plane_authoritative_checkout_execution_workspace_binding_bootstrap`",
    "classification: `existing_surface_alignment`",
    "control_plane_authoritative_checkout_execution_workspace_binding_only",
    "control_plane_authoritative_checkout_execution_workspace_binding_not_machine_authoritative",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle()
        lane = get_lane(bundle.registry_doc, ACTIVE_LANE_ID)
        checks = []
        failures = []

        binding_ok, binding_detail = ensure_authoritative_checkout_binding(bundle)
        _record(checks, failures, "authoritative_checkout_binding", binding_ok, binding_detail)
        _record(
            checks,
            failures,
            "current_registry_schema",
            bundle.current_doc.get("schema_version") == CURRENT_SCHEMA_VERSION,
            "current registry uses narrowed current schema",
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
            "current registry pointer is narrowed and has no overbound read-only inputs",
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
            "versioned registry matches the narrowed bootstrap contract",
        )
        _record(
            checks,
            failures,
            "lane_shape",
            lane.get("classification") == CLASSIFICATION
            and lane.get("execution_mode") == "split_roles"
            and lane.get("status") == "architect_ready"
            and lane.get("writer_role") == "executor"
            and lane.get("role_bindings") == EXPECTED_ROLE_BINDINGS,
            "active lane exposes split-role execution for the executor",
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
            "lane commands and exact status contracts are machine-locked",
        )
        _record(
            checks,
            failures,
            "fixed_write_set_and_delta",
            lane.get("exact_fixed_write_set") == EXPECTED_FIXED_WRITE_SET
            and lane.get("read_only_input_surfaces") == []
            and lane.get("admitted_delta_only") == ADMITTED_DELTA_ONLY
            and lane.get("fail_close_token") == FAIL_CLOSE_TOKEN,
            "fixed write set is exact and the package is narrowed to checkout/workspace binding only",
        )
        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP document exposes the narrowed authoritative binding contract",
        )
        runtime_literal_failures = check_forbidden_runtime_literals(canonical_package_paths(bundle.repo_root))
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
