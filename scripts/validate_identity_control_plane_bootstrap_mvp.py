#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    CLASSIFICATION,
    CONTRACT_ID,
    CURRENT_SCHEMA_VERSION,
    DEFAULT_OWNER_BINDING_CURRENT_REL,
    DEFAULT_VERSIONED_REGISTRY_REL,
    EXPECTED_OWNER_BINDINGS,
    RECEIPT_SCHEMA_VERSION,
    REGISTRATION_BOOTSTRAP_LANE_ID,
    REGISTRATION_TRANSACTION_LANE_ID,
    REGISTERED_TARGET_LANE_ID,
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
    REGISTRATION_TRANSACTION_LANE_ID,
}
ACCEPTABLE_CURRENT_ACTIVE_LANES = {
    ACTIVE_LANE_ID,
    REGISTRATION_TRANSACTION_LANE_ID,
}
REGISTRATION_FIXED_WRITE_SET = [
    "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md",
    "identity/protocol/mappings/control-plane-lane-registry.current.yaml",
    "identity/protocol/mappings/control-plane-lane-registry.v1.yaml",
    "scripts/control_plane_lane_registry_common.py",
    "scripts/control_plane_lane_render.py",
    "scripts/validate_identity_control_plane_bootstrap_mvp.py",
    "scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh",
]
REGISTRATION_ADMITTED_DELTA_ONLY = [
    "control_plane_protocol_feedback_instance_state_runner_hardening",
]
REGISTRATION_FAIL_CLOSE_TOKEN = "control_plane_lane_registration_transaction_only_not_machine_authoritative"
REGISTRATION_VALIDATOR_COMMAND = (
    "TMPDIR=$PWD/.tmp python3 scripts/validate_identity_control_plane_bootstrap_mvp.py --json-only"
)
REGISTRATION_PROBE_COMMAND = (
    "TMPDIR=$PWD/.tmp bash scripts/ci/run_identity_control_plane_bootstrap_mvp_probes_ci.sh"
)
REQUIRED_DOC_TOKENS = [
    "## Historical lane compatibility",
    "`control_plane_lane_registration_transaction_only`",
    "`control_plane_protocol_feedback_instance_state_runner_hardening`",
    "owner-binding overlay",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        bootstrap_lane = get_lane(bundle.registry_doc, REGISTRATION_BOOTSTRAP_LANE_ID)
        registration_lane = get_lane(bundle.registry_doc, REGISTRATION_TRANSACTION_LANE_ID)
        target_lane = get_lane(bundle.registry_doc, REGISTERED_TARGET_LANE_ID)
        checks = []
        failures = []

        ctx_ok, ctx_detail = ensure_registration_transaction_execution_context(bundle)
        _record(checks, failures, "registration_transaction_execution_context", ctx_ok, ctx_detail)
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
            "current registry may point at the active overlay lane or a registration-lane shadow current file while still resolving the owner-binding overlay",
        )
        _record(
            checks,
            failures,
            "versioned_registry_contract",
            bundle.registry_doc.get("schema_version") == SCHEMA_VERSION
            and bundle.registry_doc.get("contract_id") == CONTRACT_ID
            and bundle.registry_doc.get("classification") == CLASSIFICATION
            and bundle.registry_doc.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION,
            "versioned registry remains anchored to the overlay hardening family while preserving historical rows",
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
            role_binding_hits or "historical lanes remain machine-readable without canonical concrete role_bindings",
        )
        _record(
            checks,
            failures,
            "bootstrap_lane_preserved",
            bootstrap_lane.get("status") == "closure_done"
            and bootstrap_lane.get("active") is False
            and bootstrap_lane.get("next_role") == "auditor",
            "bootstrap lane remains preserved as a closed historical row",
        )
        _record(
            checks,
            failures,
            "registration_lane_preserved",
            registration_lane.get("classification") == CLASSIFICATION
            and registration_lane.get("status") in {"closure_done", "preflight_passed"}
            and registration_lane.get("active") is False
            and registration_lane.get("execution_mode") == "split_roles"
            and registration_lane.get("writer_role") == "executor"
            and registration_lane.get("read_only_roles") == ["architect", "auditor", "office"]
            and registration_lane.get("exact_fixed_write_set") == REGISTRATION_FIXED_WRITE_SET
            and registration_lane.get("read_only_input_surfaces") == []
            and registration_lane.get("validator_command") == REGISTRATION_VALIDATOR_COMMAND
            and registration_lane.get("probe_command") == REGISTRATION_PROBE_COMMAND
            and registration_lane.get("validator_expected_status") == "PASS_REQUIRED"
            and registration_lane.get("probe_expected_status") == "PASS"
            and registration_lane.get("admitted_delta_only") == REGISTRATION_ADMITTED_DELTA_ONLY
            and registration_lane.get("fail_close_token") == REGISTRATION_FAIL_CLOSE_TOKEN
            and registration_lane.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION,
            "registration-only lane remains preserved as a historical executable contract and can still be replayed through a shadow current pointer",
        )
        _record(
            checks,
            failures,
            "registered_target_lane_preserved",
            target_lane.get("lane_id") == REGISTERED_TARGET_LANE_ID
            and target_lane.get("status") == "closure_done"
            and target_lane.get("active") is False,
            "the historically registered target lane remains present after the overlay split",
        )
        preflight_projection = route_next_role(
            registration_lane,
            bundle=bundle,
            status_override="preflight_passed",
        )
        closure_projection = route_next_role(
            registration_lane,
            bundle=bundle,
            status_override="closure_done",
        )
        bootstrap_closure_projection = route_next_role(
            bootstrap_lane,
            bundle=bundle,
            status_override="closure_done",
        )
        _record(
            checks,
            failures,
            "route_compatibility_via_owner_binding_overlay",
            preflight_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["executor"]
            and closure_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["auditor"]
            and bootstrap_closure_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["auditor"],
            "historical registration lanes remain route-compatible because concrete identity resolution now comes from the owner-binding overlay",
        )
        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP doc records historical lane compatibility under the overlay split",
        )
        runtime_literal_failures = check_forbidden_runtime_literals(
            canonical_package_paths(bundle.repo_root, lane=registration_lane)
        )
        _record(
            checks,
            failures,
            "runtime_tuple_literal_pollution",
            not runtime_literal_failures,
            runtime_literal_failures or "historical registration package surfaces remain free of forbidden concrete runtime tuple literals",
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
