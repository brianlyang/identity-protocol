#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReleaseReadinessRepoGlobalClosureSpec:
    script_rel: str
    summary_key: str
    one_look_field: str
    status_fields: tuple[str, ...]
    error_fields: tuple[str, ...] = ("error_code",)
    keep_fields: tuple[str, ...] = ()


RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS: tuple[ReleaseReadinessRepoGlobalClosureSpec, ...] = (
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_executable_surface_runtime_literal_lock.py",
        summary_key="executable_surface_runtime_literal_lock",
        one_look_field="executable_surface_runtime_literal_lock_status",
        status_fields=("executable_surface_runtime_literal_lock_status",),
        keep_fields=("violation_count", "stale_reasons"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_required_gate_surface_drift.py",
        summary_key="required_gate_surface_drift",
        one_look_field="required_gate_surface_drift_status",
        status_fields=("required_gate_surface_drift_status",),
        keep_fields=("missing_surface_files", "missing_lineage_refs", "missing_execution_tokens"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_runtime_file_boundary_governance.py",
        summary_key="runtime_file_boundary_governance",
        one_look_field="runtime_file_boundary_governance_status",
        status_fields=("runtime_file_boundary_governance_status",),
        keep_fields=(
            "gitignore_missing_patterns",
            "runtime_selector_missing_tokens",
            "governance_doc_missing_tokens",
            "review_doc_missing_tokens",
            "stale_reasons",
        ),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_issue_register_consistency.py",
        summary_key="issue_register_consistency",
        one_look_field="issue_register_consistency_status",
        status_fields=("issue_register_consistency_status",),
        keep_fields=(
            "current_issue_horizon",
            "issue_register_issue_count",
            "deep_audit_workbook_issue_count",
            "stale_reasons",
        ),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_protocol_broadcast_doc_control.py",
        summary_key="protocol_broadcast_doc_control",
        one_look_field="protocol_broadcast_doc_control_status",
        status_fields=("protocol_broadcast_doc_control_status",),
        keep_fields=("subdomain_id", "required_token_count", "required_file_count", "stale_reasons"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/validate_protocol_governed_subdomain_doc_control_registry.py",
        summary_key="protocol_governed_subdomain_doc_control_registry",
        one_look_field="protocol_governed_subdomain_doc_control_registry_status",
        status_fields=("protocol_governed_subdomain_doc_control_registry_status",),
        keep_fields=("subdomain_count", "stale_reasons"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/check_identity_codex_launcher_migration_closure.py",
        summary_key="identity_codex_launcher_migration_closure",
        one_look_field="identity_codex_launcher_migration_closure_status",
        status_fields=("identity_codex_launcher_migration_closure_status",),
        keep_fields=(
            "checked_identity_count",
            "violation_count",
            "runtime_catalog_metadata_hygiene_status",
            "launcher_runtime_admissibility_projection_status",
            "launcher_runtime_admissibility_status",
            "stale_reasons",
        ),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/check_identity_broadcast_migration_closure.py",
        summary_key="identity_broadcast_migration_closure",
        one_look_field="identity_broadcast_migration_closure_status",
        status_fields=("identity_broadcast_migration_closure_status",),
        keep_fields=("checked_identity_count", "violation_count", "stale_reasons"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/check_identity_communication_transport_closure.py",
        summary_key="identity_communication_transport_closure",
        one_look_field="identity_communication_transport_closure_status",
        status_fields=("identity_communication_transport_closure_status",),
        keep_fields=("checked_identity_count", "violation_count", "stale_reasons"),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/check_unique_entry_contract_migration_closure.py",
        summary_key="unique_entry_contract_migration_closure",
        one_look_field="unique_entry_contract_migration_closure_status",
        status_fields=("unique_entry_contract_migration_closure_status",),
        keep_fields=(
            "checked_identity_count",
            "violation_count",
            "catalog_selection_mode",
            "repo_catalog_included",
            "pack_scan_policy_id",
            "stale_reasons",
        ),
    ),
    ReleaseReadinessRepoGlobalClosureSpec(
        script_rel="scripts/check_version_baseline_migration_closure.py",
        summary_key="version_baseline_migration_closure",
        one_look_field="version_baseline_migration_closure_status",
        status_fields=("version_baseline_migration_closure_status",),
        keep_fields=(
            "checked_identity_count",
            "violation_count",
            "catalog_selection_mode",
            "repo_catalog_included",
            "pack_scan_policy_id",
            "stale_reasons",
        ),
    ),
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS: tuple[tuple[str, str], ...] = tuple(
    (spec.summary_key, spec.one_look_field)
    for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS
    if spec.summary_key != "executable_surface_runtime_literal_lock"
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS: tuple[str, ...] = tuple(
    spec.one_look_field for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS: tuple[str, ...] = tuple(
    f"one_look.{field}" for field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES: tuple[str, ...] = tuple(
    spec.script_rel for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS
)

RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_SUMMARY_KEY = (
    "identity_codex_launcher_migration_closure"
)
RELEASE_READINESS_REPO_GLOBAL_BROADCAST_SUMMARY_KEY = (
    "identity_broadcast_migration_closure"
)
RELEASE_READINESS_REPO_GLOBAL_COMMUNICATION_TRANSPORT_SUMMARY_KEY = (
    "identity_communication_transport_closure"
)
RELEASE_READINESS_REPO_GLOBAL_UNIQUE_ENTRY_SUMMARY_KEY = (
    "unique_entry_contract_migration_closure"
)
RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_SUMMARY_KEY = (
    "version_baseline_migration_closure"
)

RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS: tuple[str, ...] = (
    RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_BROADCAST_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_COMMUNICATION_TRANSPORT_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_UNIQUE_ENTRY_SUMMARY_KEY,
    RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_SUMMARY_KEY,
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS: tuple[str, ...] = tuple(
    f"one_look.{summary_key}_checked_identity_count"
    for summary_key in RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS
)
RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD = (
    f"one_look.{RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_SUMMARY_KEY}_checked_identity_count"
)
RELEASE_READINESS_REPO_GLOBAL_BROADCAST_CHECKED_IDENTITY_COUNT_FIELD = (
    f"one_look.{RELEASE_READINESS_REPO_GLOBAL_BROADCAST_SUMMARY_KEY}_checked_identity_count"
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES: tuple[str, ...] = (
    "scripts/validate_release_readiness_repo_global_closure_topology.py",
    "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT = (
    "scripts/validate_release_readiness_repo_global_closure_topology.py"
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT = (
    "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh"
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_COMMAND: tuple[str, ...] = (
    "python3",
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT,
    "--json-only",
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_COMMAND: tuple[str, ...] = (
    "bash",
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY = (
    "release_readiness_repo_global_closure_topology_probe"
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD = (
    "release_readiness_repo_global_closure_topology_probe_status"
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD,
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    "positive_validator_output",
)
RELEASE_READINESS_REPO_GLOBAL_REQUIRED_GATE_SURFACE_DRIFT_ONE_LOOK_MARKER = (
    "one_look.required_gate_surface_drift_status"
)
RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_ONE_LOOK_MARKER = (
    f"one_look.{RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_SUMMARY_KEY}_status"
)
RELEASE_READINESS_REPO_GLOBAL_EXECUTABLE_SURFACE_RUNTIME_LITERAL_LOCK_LANE = (
    "scripts/validate_executable_surface_runtime_literal_lock.py"
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER = (
    "repo_global_closure_projection="
    + "|".join(f"one_look.{field}" for field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS)
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES,
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS: tuple[str, ...] = (
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _resolve_repo_global_payload(
    summary: dict[str, Any],
    spec: ReleaseReadinessRepoGlobalClosureSpec,
) -> dict[str, Any]:
    payload = summary.get(spec.summary_key) or {}
    if spec.summary_key == "executable_surface_runtime_literal_lock":
        control_plane_surface_materialization = summary.get("control_plane_surface_materialization") or {}
        if not isinstance(control_plane_surface_materialization, dict):
            control_plane_surface_materialization = {}
        control_plane_check_projection = (
            control_plane_surface_materialization.get("control_plane_check_projection") or {}
        )
        if not isinstance(control_plane_check_projection, dict):
            control_plane_check_projection = {}
        nested_payload = control_plane_check_projection.get("executable_surface_runtime_literal_lock") or {}
        if isinstance(nested_payload, dict) and nested_payload:
            payload = nested_payload
    if not isinstance(payload, dict):
        return {}
    return payload


def release_readiness_repo_global_closure_capture_script_map() -> dict[str, str]:
    return {spec.script_rel: spec.summary_key for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS}


def release_readiness_repo_global_closure_structured_capture_specs() -> dict[str, dict[str, tuple[str, ...]]]:
    return {
        spec.summary_key: {
            "status_fields": spec.status_fields,
            "error_fields": spec.error_fields,
            "keep_fields": spec.keep_fields,
        }
        for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS
    }


def release_readiness_repo_global_closure_summary_defaults() -> dict[str, dict[str, Any]]:
    return {spec.summary_key: {"status": STATUS_UNKNOWN} for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS}


def apply_release_readiness_repo_global_closure_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(summary, dict) or not isinstance(one_look, dict):
        return
    for spec in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SPECS:
        payload = _resolve_repo_global_payload(summary, spec)
        one_look[spec.one_look_field] = _clean_str(payload.get("status")).upper() or STATUS_UNKNOWN
        if "checked_identity_count" in payload:
            one_look[f"{spec.summary_key}_checked_identity_count"] = _safe_int(
                payload.get("checked_identity_count")
            )
        if "violation_count" in payload:
            one_look[f"{spec.summary_key}_violation_count"] = _safe_int(payload.get("violation_count"))
