#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS: tuple[tuple[str, str], ...] = (
    ("required_gate_surface_drift", "required_gate_surface_drift_status"),
    ("runtime_file_boundary_governance", "runtime_file_boundary_governance_status"),
    ("issue_register_consistency", "issue_register_consistency_status"),
    ("protocol_broadcast_doc_control", "protocol_broadcast_doc_control_status"),
    (
        "protocol_governed_subdomain_doc_control_registry",
        "protocol_governed_subdomain_doc_control_registry_status",
    ),
    ("identity_codex_launcher_migration_closure", "identity_codex_launcher_migration_closure_status"),
    ("identity_broadcast_migration_closure", "identity_broadcast_migration_closure_status"),
    ("identity_communication_transport_closure", "identity_communication_transport_closure_status"),
    ("unique_entry_contract_migration_closure", "unique_entry_contract_migration_closure_status"),
    ("version_baseline_migration_closure", "version_baseline_migration_closure_status"),
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "executable_surface_runtime_literal_lock_status",
    *(one_look_field for _, one_look_field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS),
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS: tuple[str, ...] = tuple(
    f"one_look.{field}" for field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES: tuple[str, ...] = (
    "scripts/validate_executable_surface_runtime_literal_lock.py",
    "scripts/validate_required_gate_surface_drift.py",
    "scripts/validate_runtime_file_boundary_governance.py",
    "scripts/validate_issue_register_consistency.py",
    "scripts/validate_protocol_broadcast_doc_control.py",
    "scripts/validate_protocol_governed_subdomain_doc_control_registry.py",
    "scripts/check_identity_codex_launcher_migration_closure.py",
    "scripts/check_identity_broadcast_migration_closure.py",
    "scripts/check_identity_communication_transport_closure.py",
    "scripts/check_unique_entry_contract_migration_closure.py",
    "scripts/check_version_baseline_migration_closure.py",
)

RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS: tuple[str, ...] = (
    "identity_codex_launcher_migration_closure",
    "identity_broadcast_migration_closure",
    "identity_communication_transport_closure",
    "unique_entry_contract_migration_closure",
    "version_baseline_migration_closure",
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS: tuple[str, ...] = tuple(
    f"one_look.{summary_key}_checked_identity_count"
    for summary_key in RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS
)

RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER = (
    "repo_global_closure_projection="
    + "|".join(f"one_look.{field}" for field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_FIELDS)
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
)
RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS: tuple[str, ...] = (
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def apply_release_readiness_repo_global_closure_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(summary, dict) or not isinstance(one_look, dict):
        return

    control_plane_surface_materialization = summary.get("control_plane_surface_materialization") or {}
    if not isinstance(control_plane_surface_materialization, dict):
        control_plane_surface_materialization = {}
    control_plane_check_projection = control_plane_surface_materialization.get("control_plane_check_projection") or {}
    if not isinstance(control_plane_check_projection, dict):
        control_plane_check_projection = {}
    executable_surface_runtime_literal_lock = (
        control_plane_check_projection.get("executable_surface_runtime_literal_lock")
        or summary.get("executable_surface_runtime_literal_lock")
        or {}
    )
    if not isinstance(executable_surface_runtime_literal_lock, dict):
        executable_surface_runtime_literal_lock = {}

    one_look["executable_surface_runtime_literal_lock_status"] = (
        _clean_str(executable_surface_runtime_literal_lock.get("status")).upper() or STATUS_UNKNOWN
    )
    one_look["executable_surface_runtime_literal_lock_violation_count"] = _safe_int(
        executable_surface_runtime_literal_lock.get("violation_count")
    )

    for summary_key, one_look_field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS:
        payload = summary.get(summary_key) or {}
        if not isinstance(payload, dict):
            payload = {}
        one_look[one_look_field] = _clean_str(payload.get("status")).upper() or STATUS_UNKNOWN
        if "checked_identity_count" in payload:
            one_look[f"{summary_key}_checked_identity_count"] = _safe_int(
                payload.get("checked_identity_count")
            )
        if "violation_count" in payload:
            one_look[f"{summary_key}_violation_count"] = _safe_int(payload.get("violation_count"))
