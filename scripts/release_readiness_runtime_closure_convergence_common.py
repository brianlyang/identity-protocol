#!/usr/bin/env python3
from __future__ import annotations

from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
)
from runtime_fleet_closure_common import FLEET_PROJECTION_POLICY_ID
from runtime_pack_closure_common import PACK_SCAN_POLICY_ID
from workspace_runtime_closure_command_common import (
    WORKSPACE_RUNTIME_CLOSURE_RUNNER_GOVERNANCE_PROBE_SCRIPT,
    WORKSPACE_RUNTIME_CLOSURE_RUNNER_SURFACE_CONSTRAINTS,
    workspace_runtime_closure_target_scripts,
)


RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CHECKER_MARKERS: tuple[str, ...] = (
    "check_identity_broadcast_migration_closure.py",
    "check_identity_communication_transport_closure.py",
)

RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CHECKER_MARKERS: tuple[str, ...] = (
    "check_unique_entry_contract_migration_closure.py",
    "check_version_baseline_migration_closure.py",
)

RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_TARGET_MARKERS: tuple[str, ...] = (
    *workspace_runtime_closure_target_scripts(),
)
RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER = (
    "scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh"
)
RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER = (
    "scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh"
)
RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER = (
    "scripts/run_workspace_runtime_closure_checks.py"
)

RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS: tuple[str, ...] = (
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER,
    "runtime_fleet_closure_common.py",
    FLEET_PROJECTION_POLICY_ID,
    *RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CHECKER_MARKERS,
    "workspace_runtime_only",
    "repo_catalog_inclusive",
)

RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS: tuple[str, ...] = (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER,
    "runtime_pack_closure_common.py",
    PACK_SCAN_POLICY_ID,
    *RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CHECKER_MARKERS,
    "workspace_runtime_only",
    "repo_catalog_inclusive",
)

RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS: tuple[str, ...] = (
    "workspace_runtime_closure_command_common.py",
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER,
    "scripts/ci/run_required_runtime_gates_ci.sh",
    WORKSPACE_RUNTIME_CLOSURE_RUNNER_GOVERNANCE_PROBE_SCRIPT,
    "release_readiness_check.py",
    "identity_creator.py",
    "identity_codex_launcher_evidence_common.py",
    "validate_workspace_runtime_closure_command_surface.py",
    "workspace_runtime_only",
    *WORKSPACE_RUNTIME_CLOSURE_RUNNER_SURFACE_CONSTRAINTS,
    *RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_TARGET_MARKERS,
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
)
