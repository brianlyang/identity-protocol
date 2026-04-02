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
    EXPECTED_OWNER_BINDINGS,
    FAIL_CLOSE_TOKEN,
    FORBIDDEN_HOST_PATH_PATTERN,
    OWNER_BINDING_ACTIVE_PROFILE_ID,
    OWNER_BINDING_CURRENT_SCHEMA_VERSION,
    OWNER_BINDING_POLICY,
    OWNER_BINDING_SCHEMA_VERSION,
    OWNER_BINDING_SCOPE,
    OWNER_BINDING_TRUTH_CLASS,
    PROBE_COMMAND,
    PROBE_EXPECTED_STATUS,
    RECEIPT_SCHEMA_VERSION,
    REGISTRATION_BOOTSTRAP_LANE_ID,
    REGISTRATION_TRANSACTION_LANE_ID,
    REGISTERED_TARGET_LANE_ID,
    SCHEMA_VERSION,
    VALIDATOR_COMMAND,
    VALIDATOR_EXPECTED_STATUS,
    canonical_package_paths,
    check_forbidden_runtime_literals,
    display_path,
    emit,
    ensure_control_plane_execution_context,
    get_lane,
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
    "control_plane_role_binding_overlay_hardening_not_machine_authoritative",
    "canonical registry no longer persists `role_bindings`",
    "role_to_identity_binding_overlay",
    "`scripts/control_plane_lane_stream_guard.py`",
]
REQUIRED_REVIEW_TOKENS = [
    "## Closure supplement — control_plane_role_binding_overlay_hardening",
    "identity lock-in",
    "identity/protocol/mappings/control-plane-owner-binding.current.yaml",
    "scripts/control_plane_lane_stream_guard.py",
]


def _record(checks, failures, name, ok, detail):
    checks.append({"name": name, "status": "PASS" if ok else "FAIL", "detail": detail})
    if not ok:
        failures.append(name)


def _scan_host_paths(paths: list[Path], repo_root: Path) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if FORBIDDEN_HOST_PATH_PATTERN.search(path.read_text(encoding="utf-8")):
            hits.append(f"absolute_host_path_literal:{display_path(path, repo_root)}")
    return hits


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
            "current registry points at the active overlay lane and resolves the repo-local owner binding overlay",
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
        _record(
            checks,
            failures,
            "owner_binding_current_doc",
            bundle.owner_binding_current_doc.get("schema_version") == OWNER_BINDING_CURRENT_SCHEMA_VERSION
            and bundle.owner_binding_current_doc.get("truth_class") == OWNER_BINDING_TRUTH_CLASS
            and bundle.owner_binding_current_doc.get("scope") == OWNER_BINDING_SCOPE
            and bundle.owner_binding_current_doc.get("portable") is False
            and bundle.owner_binding_current_doc.get("binding_policy") == OWNER_BINDING_POLICY
            and bundle.owner_binding_current_doc.get("active_binding_id") == OWNER_BINDING_ACTIVE_PROFILE_ID
            and str(bundle.owner_binding_current_doc.get("active_file", "")).strip() in ACCEPTABLE_OWNER_VERSIONED_REFS,
            "owner-binding current doc is repo-local, non-portable, and points at the versioned binding profile",
        )
        _record(
            checks,
            failures,
            "owner_binding_versioned_doc",
            bundle.owner_binding_doc.get("schema_version") == OWNER_BINDING_SCHEMA_VERSION
            and bundle.owner_binding_doc.get("truth_class") == OWNER_BINDING_TRUTH_CLASS
            and bundle.owner_binding_doc.get("scope") == OWNER_BINDING_SCOPE
            and bundle.owner_binding_doc.get("portable") is False
            and bundle.owner_binding_doc.get("binding_policy") == OWNER_BINDING_POLICY
            and bundle.owner_binding_doc.get("active_binding_id") == OWNER_BINDING_ACTIVE_PROFILE_ID
            and bundle.owner_binding_doc.get("role_to_identity_bindings") == EXPECTED_OWNER_BINDINGS,
            "versioned owner-binding overlay carries the canonical repo-local role -> identity map",
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
        _record(
            checks,
            failures,
            "route_semantics_identity_resolution_split",
            "identity_id" not in closure_semantics
            and closure_semantics.get("role") == "auditor"
            and preflight_semantics.get("role") == "executor"
            and closure_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["auditor"]
            and preflight_projection.get("identity_id") == EXPECTED_OWNER_BINDINGS["executor"],
            "route_next_role_semantics returns role-only law, while route_next_role resolves concrete identity from the owner-binding overlay",
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
            "MVP doc records the overlay hardening contract, fixed write set, and fail-close token",
        )
        _record(
            checks,
            failures,
            "review_doc_tokens",
            all(token in review_text for token in REQUIRED_REVIEW_TOKENS),
            "review ledger records both the original identity lock-in concern and the exact closure supplement",
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
