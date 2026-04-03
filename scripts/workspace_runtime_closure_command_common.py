#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspaceRuntimeClosureCheckerSpec:
    checker_id: str
    status_field: str
    closure_family: str


WORKSPACE_RUNTIME_CLOSURE_CHECKER_SPECS: tuple[WorkspaceRuntimeClosureCheckerSpec, ...] = (
    WorkspaceRuntimeClosureCheckerSpec(
        checker_id="scripts/check_identity_codex_launcher_migration_closure.py",
        status_field="identity_codex_launcher_migration_closure_status",
        closure_family="launcher",
    ),
    WorkspaceRuntimeClosureCheckerSpec(
        checker_id="scripts/check_identity_broadcast_migration_closure.py",
        status_field="identity_broadcast_migration_closure_status",
        closure_family="transport",
    ),
    WorkspaceRuntimeClosureCheckerSpec(
        checker_id="scripts/check_identity_communication_transport_closure.py",
        status_field="identity_communication_transport_closure_status",
        closure_family="transport",
    ),
    WorkspaceRuntimeClosureCheckerSpec(
        checker_id="scripts/check_unique_entry_contract_migration_closure.py",
        status_field="unique_entry_contract_migration_closure_status",
        closure_family="pack",
    ),
    WorkspaceRuntimeClosureCheckerSpec(
        checker_id="scripts/check_version_baseline_migration_closure.py",
        status_field="version_baseline_migration_closure_status",
        closure_family="pack",
    ),
)

WORKSPACE_RUNTIME_CLOSURE_RUNNER_REQUIRED_TOKENS: tuple[str, ...] = (
    "--catalog",
    "--repo-catalog",
    "--json-only",
)

WORKSPACE_RUNTIME_CLOSURE_RUNNER_FORBIDDEN_SELECTOR_TOKENS: tuple[str, ...] = (
    "--family",
    "--checker-id",
)

WORKSPACE_RUNTIME_CLOSURE_RUNNER_SELECTOR_POLICY_MARKER = (
    "workspace_runtime_runner_selector_policy=full_surface_non_shrinkable"
)

WORKSPACE_RUNTIME_CLOSURE_RUNNER_GOVERNANCE_PROBE_SCRIPT = (
    "scripts/ci/run_required_gate_surface_drift_probes_ci.sh"
)

WORKSPACE_RUNTIME_CLOSURE_RUNNER_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    "workspace_runtime_runner_required_tokens=--catalog|--repo-catalog|--json-only",
    "workspace_runtime_runner_forbidden_selector_tokens=--family|--checker-id",
    WORKSPACE_RUNTIME_CLOSURE_RUNNER_SELECTOR_POLICY_MARKER,
    "workspace_runtime_runner_validator=scripts/validate_required_gate_surface_drift.py",
    f"workspace_runtime_runner_governance_probe={WORKSPACE_RUNTIME_CLOSURE_RUNNER_GOVERNANCE_PROBE_SCRIPT}",
)


def resolve_workspace_runtime_closure_path_token(
    value: str | Path,
    *,
    repo_root: Path | None = None,
) -> str:
    raw_path = Path(str(value).strip())
    if raw_path.is_absolute():
        return str(raw_path.resolve())
    if repo_root is None:
        return str(raw_path)
    return str((repo_root / raw_path).resolve())


def workspace_runtime_closure_checker_specs(
    *,
    families: set[str] | None = None,
) -> tuple[WorkspaceRuntimeClosureCheckerSpec, ...]:
    if not families:
        return WORKSPACE_RUNTIME_CLOSURE_CHECKER_SPECS
    normalized = {str(item).strip().lower() for item in families if str(item).strip()}
    return tuple(
        spec
        for spec in WORKSPACE_RUNTIME_CLOSURE_CHECKER_SPECS
        if spec.closure_family in normalized
    )


def workspace_runtime_closure_target_scripts(
    *,
    families: set[str] | None = None,
) -> tuple[str, ...]:
    return tuple(spec.checker_id for spec in workspace_runtime_closure_checker_specs(families=families))


def resolve_workspace_runtime_closure_checker_spec(
    checker_id: str,
) -> WorkspaceRuntimeClosureCheckerSpec:
    token = str(checker_id or "").strip()
    for spec in WORKSPACE_RUNTIME_CLOSURE_CHECKER_SPECS:
        if spec.checker_id == token:
            return spec
    raise KeyError(f"unknown_workspace_runtime_closure_checker:{token}")


def build_workspace_runtime_closure_checker_command(
    *,
    checker_id: str,
    catalog_path: str | Path,
    repo_root: Path | None = None,
    repo_catalog_path: str | Path | None = None,
    json_only: bool = True,
) -> list[str]:
    spec = resolve_workspace_runtime_closure_checker_spec(checker_id)
    script_token = resolve_workspace_runtime_closure_path_token(spec.checker_id, repo_root=repo_root)
    cmd = [
        "python3",
        script_token,
    ]
    if repo_catalog_path is not None and str(repo_catalog_path).strip():
        cmd.extend(
            [
                "--repo-catalog",
                resolve_workspace_runtime_closure_path_token(repo_catalog_path, repo_root=repo_root),
            ]
        )
    cmd.extend(
        [
            "--catalog",
            resolve_workspace_runtime_closure_path_token(catalog_path, repo_root=repo_root),
            "--workspace-runtime-only",
        ]
    )
    if json_only:
        cmd.append("--json-only")
    return cmd
