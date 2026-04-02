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
    OWNER_BINDING_ACTIVE_PROFILE_ID,
    OWNER_BINDING_CANONICAL_REENTRY_POLICY,
    OWNER_BINDING_POLICY,
    OWNER_BINDING_RUNTIME_EVIDENCE_CLASS,
    OWNER_BINDING_RUNTIME_EVIDENCE_SURFACE,
    OWNER_BINDING_SCOPE,
    OWNER_BINDING_TRUTH_CLASS,
    RECEIPT_SCHEMA_VERSION,
    REGISTRATION_BOOTSTRAP_LANE_ID,
    REGISTRATION_TRANSACTION_LANE_ID,
    REGISTERED_TARGET_LANE_ID,
    REQUIRED_OWNER_BINDING_ROLES,
    RUNTIME_ALLOWED_LITERAL_EXCEPTION_SURFACES,
    SCHEMA_VERSION,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    display_path,
    emit,
    ensure_registration_transaction_execution_context,
    get_lane,
    owner_binding_policy_issues,
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
    "route_next_role now emits role-level projections plus a runtime-evidence binding surface only.",
    "historical lanes remain route-compatible because their projections defer concrete binding to runtime evidence instead of persisting `identity_id`.",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def _binding_surface_issues(projection) -> list[str]:
    if not isinstance(projection, dict):
        return ["projection_not_mapping"]
    surface = projection.get("binding_surface")
    if not isinstance(surface, dict):
        return ["binding_surface_not_mapping"]
    issues: list[str] = []
    expected_pairs = {
        "resolution_status": "DEFERRED_TO_RUNTIME_EVIDENCE",
        "truth_class": OWNER_BINDING_TRUTH_CLASS,
        "scope": OWNER_BINDING_SCOPE,
        "portable": False,
        "runtime_evidence_surface": OWNER_BINDING_RUNTIME_EVIDENCE_SURFACE,
        "runtime_evidence_class": OWNER_BINDING_RUNTIME_EVIDENCE_CLASS,
        "canonical_reentry_policy": OWNER_BINDING_CANONICAL_REENTRY_POLICY,
        "binding_policy": OWNER_BINDING_POLICY,
        "active_binding_id": OWNER_BINDING_ACTIVE_PROFILE_ID,
    }
    for field_name, expected_value in expected_pairs.items():
        if surface.get(field_name) != expected_value:
            issues.append(f"{field_name}_mismatch")
    if list(surface.get("required_roles") or []) != list(REQUIRED_OWNER_BINDING_ROLES):
        issues.append("required_roles_mismatch")
    roots = surface.get("admitted_runtime_evidence_roots")
    if not isinstance(roots, list) or not roots:
        issues.append("admitted_runtime_evidence_roots_invalid")
    if "identity_id" in projection:
        issues.append("identity_id_reentered")
    return issues


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
            "current registry may point at the active overlay lane or a registration-lane shadow current file while still resolving runtime-evidence metadata",
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
        current_runtime_policy = bundle.current_doc.get("runtime_tuple_policy") or {}
        versioned_runtime_policy = bundle.registry_doc.get("canonical_runtime_tuple_policy") or {}
        _record(
            checks,
            failures,
            "runtime_tuple_exception_surfaces",
            current_runtime_policy.get("concrete_tuple_literals_allowed") is False
            and current_runtime_policy.get("allowed_literal_exception_surfaces")
            == RUNTIME_ALLOWED_LITERAL_EXCEPTION_SURFACES
            and versioned_runtime_policy.get("concrete_tuple_literals_allowed") is False
            and versioned_runtime_policy.get("allowed_literal_exception_surfaces")
            == RUNTIME_ALLOWED_LITERAL_EXCEPTION_SURFACES,
            "historical registration replay admits concrete literals only through explicitly marked runtime-evidence surfaces",
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
        binding_issues = owner_binding_policy_issues(
            bundle.owner_binding_doc,
            require_required_roles=True,
            require_runtime_roots=True,
        )
        _record(
            checks,
            failures,
            "owner_binding_runtime_evidence_shape",
            not binding_issues,
            binding_issues or "owner-binding document exposes required roles and runtime-evidence roots without concrete identity bindings",
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
        preflight_issues = _binding_surface_issues(preflight_projection)
        closure_issues = _binding_surface_issues(closure_projection)
        bootstrap_issues = _binding_surface_issues(bootstrap_closure_projection)
        _record(
            checks,
            failures,
            "route_compatibility_via_runtime_evidence_surface",
            preflight_projection.get("role") == "executor"
            and preflight_projection.get("suggested_next_status") == "closure_running"
            and closure_projection.get("role") == "auditor"
            and closure_projection.get("suggested_next_status") == "audit_ready"
            and bootstrap_closure_projection.get("role") == "auditor"
            and bootstrap_closure_projection.get("suggested_next_status") == "audit_ready"
            and not preflight_issues
            and not closure_issues
            and not bootstrap_issues,
            preflight_issues + closure_issues + bootstrap_issues
            or "historical registration lanes remain route-compatible because projections stay role-level and defer concrete binding to runtime evidence",
        )
        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP doc records historical lane compatibility under the runtime-evidence-only split",
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
