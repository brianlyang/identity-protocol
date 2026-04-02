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
    DEFAULT_OWNER_BINDING_CURRENT_REL,
    DEFAULT_OWNER_BINDING_VERSIONED_REL,
    DEFAULT_VERSIONED_REGISTRY_REL,
    EXPECTED_ALLOWED_ACTIONS,
    EXPECTED_FIXED_WRITE_SET,
    HELPER_LITERAL_LOCK_IN_SURFACES,
    REQUIRED_OWNER_BINDING_ROLES,
    FAIL_CLOSE_TOKEN,
    FORBIDDEN_HOST_PATH_PATTERN,
    OWNER_BINDING_ACTIVE_PROFILE_ID,
    OWNER_BINDING_CANONICAL_REENTRY_POLICY,
    OWNER_BINDING_CURRENT_SCHEMA_VERSION,
    OWNER_BINDING_POLICY,
    OWNER_BINDING_RUNTIME_EVIDENCE_CLASS,
    OWNER_BINDING_RUNTIME_EVIDENCE_SURFACE,
    OWNER_BINDING_SCHEMA_VERSION,
    OWNER_BINDING_SCOPE,
    OWNER_BINDING_TRUTH_CLASS,
    PROBE_COMMAND,
    PROBE_EXPECTED_STATUS,
    RECEIPT_SCHEMA_VERSION,
    REGISTRATION_BOOTSTRAP_LANE_ID,
    REGISTRATION_TRANSACTION_LANE_ID,
    REGISTERED_TARGET_LANE_ID,
    RUNTIME_ALLOWED_LITERAL_EXCEPTION_SURFACES,
    SCHEMA_VERSION,
    VALIDATOR_COMMAND,
    VALIDATOR_EXPECTED_STATUS,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    check_helper_literal_lock_in,
    display_path,
    emit,
    ensure_control_plane_execution_context,
    get_lane,
    owner_binding_policy_issues,
    resolve_registry_bundle,
    route_next_role,
    route_next_role_semantics,
)

ACCEPTABLE_VERSIONED_REFS = {
    DEFAULT_VERSIONED_REGISTRY_REL.as_posix(),
    "control-plane-lane-registry.v1.yaml",
}
ACCEPTABLE_OWNER_CURRENT_REFS = {
    DEFAULT_OWNER_BINDING_CURRENT_REL.as_posix(),
    "control-plane-owner-binding.current.yaml",
}
ACCEPTABLE_OWNER_VERSIONED_REFS = {
    DEFAULT_OWNER_BINDING_VERSIONED_REL.as_posix(),
    "control-plane-owner-binding.v1.yaml",
}
REQUIRED_DOC_TOKENS = [
    "contract_id: `control_plane_role_binding_overlay_hardening`",
    "canonical protocol truth must remain role-level, portable, and free of concrete runtime bindings",
    "owner_binding_runtime_evidence",
    "receipt_scoped_runtime_evidence_only",
    "subagent is treated as a governed sidecar infrastructure object",
    "control_plane_role_binding_overlay_hardening_not_machine_authoritative",
]
REQUIRED_REVIEW_TOKENS = [
    "## Closure supplement — control_plane_role_binding_overlay_hardening",
    "identity lock-in",
    "runtime-evidence-only + fail-close standard",
    "subagent as a governed sidecar infrastructure object",
    "collaborator identity instance",
    "outer delivery surface",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def _scan_host_paths(paths: list[Path], repo_root: Path) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if path.name == "control_plane_lane_registry_common.py":
            continue
        if FORBIDDEN_HOST_PATH_PATTERN.search(path.read_text(encoding="utf-8")):
            hits.append(f"absolute_host_path_literal:{display_path(path, repo_root)}")
    return hits


def _binding_surface_issues(projection, bundle) -> list[str]:
    if not isinstance(projection, dict):
        return ["projection_not_mapping"]
    issues: list[str] = []
    surface = projection.get("binding_surface")
    if not isinstance(surface, dict):
        return ["binding_surface_not_mapping"]
    expected_current = display_path(bundle.owner_binding_current, bundle.repo_root)
    expected_versioned = display_path(bundle.owner_binding_versioned, bundle.repo_root)
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
        "current_file": expected_current,
        "versioned_file": expected_versioned,
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
        lane = get_lane(bundle.registry_doc, ACTIVE_LANE_ID)
        bootstrap_lane = get_lane(bundle.registry_doc, REGISTRATION_BOOTSTRAP_LANE_ID)
        registration_lane = get_lane(bundle.registry_doc, REGISTRATION_TRANSACTION_LANE_ID)
        target_lane = get_lane(bundle.registry_doc, REGISTERED_TARGET_LANE_ID)
        checks = []
        failures = []

        ctx_ok, ctx_detail = ensure_control_plane_execution_context(bundle)
        _record(checks, failures, "control_plane_execution_context", ctx_ok, ctx_detail)
        _record(
            checks,
            failures,
            "current_registry_contract",
            bundle.current_doc.get("schema_version") == CURRENT_SCHEMA_VERSION
            and bundle.current_doc.get("contract_id") == CONTRACT_ID
            and bundle.current_doc.get("classification") == CLASSIFICATION
            and str(bundle.current_doc.get("active_file", "")).strip() in ACCEPTABLE_VERSIONED_REFS
            and bundle.current_doc.get("active_lane_id") == ACTIVE_LANE_ID
            and str(bundle.current_doc.get("owner_binding_file", "")).strip() in ACCEPTABLE_OWNER_CURRENT_REFS
            and bundle.current_doc.get("read_only_input_surfaces") == [],
            "current registry points at the active overlay lane and resolves the repo-local runtime-evidence binding surface",
        )
        _record(
            checks,
            failures,
            "versioned_registry_contract",
            bundle.registry_doc.get("schema_version") == SCHEMA_VERSION
            and bundle.registry_doc.get("contract_id") == CONTRACT_ID
            and bundle.registry_doc.get("classification") == CLASSIFICATION
            and bundle.registry_doc.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION
            and bundle.registry_doc.get("active_lane_id") == ACTIVE_LANE_ID
            and str(bundle.registry_doc.get("owner_binding_file", "")).strip() in ACCEPTABLE_OWNER_CURRENT_REFS,
            "versioned registry carries the overlay hardening contract without canonical concrete owner bindings",
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
            "current and versioned registry tuple policies admit concrete literals only through runtime-evidence surfaces and other explicitly marked exception surfaces",
        )
        current_binding_issues = owner_binding_policy_issues(
            bundle.owner_binding_current_doc,
            require_active_file=True,
        )
        _record(
            checks,
            failures,
            "owner_binding_current_doc",
            bundle.owner_binding_current_doc.get("schema_version") == OWNER_BINDING_CURRENT_SCHEMA_VERSION
            and str(bundle.owner_binding_current_doc.get("active_file", "")).strip() in ACCEPTABLE_OWNER_VERSIONED_REFS
            and not current_binding_issues,
            current_binding_issues
            or "owner-binding current doc is repo-local, non-portable, receipt-scoped runtime evidence metadata",
        )
        versioned_binding_issues = owner_binding_policy_issues(
            bundle.owner_binding_doc,
            require_required_roles=True,
            require_runtime_roots=True,
        )
        _record(
            checks,
            failures,
            "owner_binding_versioned_doc",
            bundle.owner_binding_doc.get("schema_version") == OWNER_BINDING_SCHEMA_VERSION
            and not versioned_binding_issues,
            versioned_binding_issues
            or "versioned owner-binding document carries runtime-evidence-only policy metadata and required roles without concrete bindings",
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
            role_binding_hits or "canonical registry no longer persists concrete role_bindings at top level or lane level",
        )
        _record(
            checks,
            failures,
            "active_lane_shape",
            lane.get("classification") == CLASSIFICATION
            and lane.get("status") == "closure_done"
            and lane.get("active") is True
            and lane.get("execution_mode") == "split_roles"
            and lane.get("writer_role") == "executor"
            and lane.get("read_only_roles") == ["architect", "auditor", "office"]
            and lane.get("exact_fixed_write_set") == EXPECTED_FIXED_WRITE_SET
            and lane.get("read_only_input_surfaces") == []
            and lane.get("validator_command") == VALIDATOR_COMMAND
            and lane.get("probe_command") == PROBE_COMMAND
            and lane.get("validator_expected_status") == VALIDATOR_EXPECTED_STATUS
            and lane.get("probe_expected_status") == PROBE_EXPECTED_STATUS
            and lane.get("admitted_delta_only") == ADMITTED_DELTA_ONLY
            and lane.get("fail_close_token") == FAIL_CLOSE_TOKEN
            and lane.get("scope_lock_allowed_actions") == EXPECTED_ALLOWED_ACTIONS
            and lane.get("receipt_schema_version") == RECEIPT_SCHEMA_VERSION
            and lane.get("next_role") == "auditor",
            "active overlay lane is closed on the machine-authoritative fixed write set and routes next hop to auditor",
        )
        historical_ok = (
            bootstrap_lane.get("status") == "closure_done"
            and bootstrap_lane.get("active") is False
            and registration_lane.get("status") == "closure_done"
            and registration_lane.get("active") is False
            and target_lane.get("status") == "closure_done"
            and target_lane.get("active") is False
        )
        _record(
            checks,
            failures,
            "historical_lane_preservation",
            historical_ok,
            "bootstrap, registration-only, and protocol-feedback lanes remain preserved as inactive historical rows",
        )
        closure_semantics = route_next_role_semantics(lane, status_override="closure_done")
        preflight_semantics = route_next_role_semantics(lane, status_override="preflight_passed")
        closure_projection = route_next_role(lane, bundle=bundle, status_override="closure_done")
        preflight_projection = route_next_role(lane, bundle=bundle, status_override="preflight_passed")
        closure_projection_issues = _binding_surface_issues(closure_projection, bundle)
        preflight_projection_issues = _binding_surface_issues(preflight_projection, bundle)
        _record(
            checks,
            failures,
            "route_semantics_runtime_evidence_only",
            "identity_id" not in closure_semantics
            and "identity_id" not in preflight_semantics
            and closure_semantics.get("role") == "auditor"
            and preflight_semantics.get("role") == "executor"
            and closure_projection.get("role") == "auditor"
            and closure_projection.get("suggested_next_status") == "audit_ready"
            and preflight_projection.get("role") == "executor"
            and preflight_projection.get("suggested_next_status") == "closure_running"
            and not closure_projection_issues
            and not preflight_projection_issues,
            closure_projection_issues + preflight_projection_issues
            or "route_next_role returns role-level law plus runtime-evidence binding metadata only",
        )

        helper_paths = [
            (bundle.repo_root / rel).resolve()
            for rel in HELPER_LITERAL_LOCK_IN_SURFACES
            if (bundle.repo_root / rel).exists()
        ]
        helper_literal_hits = check_helper_literal_lock_in(helper_paths, root=bundle.repo_root)
        _record(
            checks,
            failures,
            "helper_constraints_fail_closed_on_reentry",
            not helper_literal_hits,
            helper_literal_hits
            or "helper validators/probes no longer reintroduce concrete identity bindings or stale owner-binding overlay projections",
        )

        doc_text = (bundle.repo_root / "identity/protocol/IDENTITY_CONTROL_PLANE_MVP.md").read_text(encoding="utf-8")
        review_text = (
            bundle.repo_root
            / "docs/review/protocol-remediation-audit-ledger-v1.6.x-post-closure-handoff-projection-drift.md"
        ).read_text(encoding="utf-8")
        _record(
            checks,
            failures,
            "mvp_doc_tokens",
            all(token in doc_text for token in REQUIRED_DOC_TOKENS),
            "MVP doc records the runtime-evidence-only contract, fail-close rule, and fixed write set",
        )
        _record(
            checks,
            failures,
            "review_doc_tokens",
            all(token in review_text for token in REQUIRED_REVIEW_TOKENS),
            "review ledger records identity lock-in, runtime-evidence-only standard, and sidecar governance supplement",
        )

        package_paths = canonical_package_paths(bundle.repo_root, lane=lane)
        runtime_literal_failures = check_forbidden_runtime_literals(package_paths)
        _record(
            checks,
            failures,
            "runtime_tuple_literal_pollution",
            not runtime_literal_failures,
            runtime_literal_failures or "canonical overlay package surfaces contain no forbidden concrete runtime tuple literals",
        )
        host_path_failures = _scan_host_paths(package_paths, bundle.repo_root)
        _record(
            checks,
            failures,
            "canonical_package_host_path_literals",
            not host_path_failures,
            host_path_failures or "canonical overlay package surfaces contain no forbidden reusable absolute host-path literals",
        )

        payload = {
            "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
            "checks": checks,
            "failures": failures,
            "registry_current": display_path(bundle.current_registry, bundle.repo_root),
            "registry_versioned": display_path(bundle.versioned_registry, bundle.repo_root),
            "owner_binding_current": display_path(bundle.owner_binding_current, bundle.repo_root),
            "owner_binding_versioned": display_path(bundle.owner_binding_versioned, bundle.repo_root),
        }
        emit(payload, json_only=args.json_only)
        return 1 if failures else 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
