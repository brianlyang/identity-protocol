#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import yaml

from resolve_identity_context import resolve_local_catalog_path, resolve_repo_catalog_path

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
FLEET_PROJECTION_POLICY_ID = "active_runtime_validator_fleet_closure_v1"

RowProjection = Callable[..., Mapping[str, Any]]
ValidatorExtraArgsBuilder = Callable[[Path, Path, str], Sequence[str]]


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def iter_active_runtime_catalog_rows(*, catalog_path: Path) -> list[dict[str, Any]]:
    doc = _safe_load_yaml(catalog_path)
    rows = doc.get("identities")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        identity_id = str(row.get("id", "")).strip()
        status = str(row.get("status", "")).strip().lower()
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        if not identity_id or status != "active" or profile != "runtime" or runtime_mode == "demo_only":
            continue
        out.append(row)
    return out


def resolve_active_runtime_catalog_candidates(
    *,
    repo_catalog_arg: str | Path,
    raw_catalogs: Sequence[str],
    include_env_catalog: bool,
    workspace_runtime_only: bool,
    caller_anchor: Path,
    caller_start: str | Path,
) -> tuple[Path, list[Path], str]:
    repo_catalog = resolve_repo_catalog_path(repo_catalog_arg, start=caller_start)
    catalog_candidates: list[Path] = [] if workspace_runtime_only else [repo_catalog]
    for raw in raw_catalogs:
        token = str(raw or "").strip()
        if not token:
            continue
        catalog_candidates.append(resolve_local_catalog_path(token, start=caller_anchor))
    if include_env_catalog:
        env_catalog = str(os.environ.get("IDENTITY_CATALOG", "")).strip()
        if env_catalog:
            catalog_candidates.append(resolve_local_catalog_path(env_catalog, start=caller_anchor))

    dedup: list[Path] = []
    seen: set[Path] = set()
    for path in catalog_candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        dedup.append(resolved)

    catalog_selection_mode = "workspace_runtime_only" if workspace_runtime_only else "repo_catalog_inclusive"
    return repo_catalog, dedup, catalog_selection_mode


def run_json_validator(
    *,
    repo_root: Path,
    validator_script: str,
    catalog_path: Path,
    identity_id: str,
    extra_args: Sequence[str] | None = None,
) -> tuple[int, dict[str, Any]]:
    script_path = (repo_root / validator_script).resolve()
    cmd = [
        "python3",
        str(script_path),
        "--catalog",
        str(catalog_path),
        "--identity-id",
        str(identity_id or "").strip(),
    ]
    if extra_args:
        cmd.extend([str(item) for item in extra_args if str(item).strip()])
    cmd.append("--json-only")
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        check=False,
    )
    payload: dict[str, Any] = {}
    stdout = str(proc.stdout or "").strip()
    if stdout:
        try:
            decoded = json.loads(stdout)
            if isinstance(decoded, dict):
                payload = decoded
        except Exception:
            payload = {"validator_stdout": stdout}
    return proc.returncode, payload


def collect_runtime_validator_fleet_closure(
    *,
    repo_root: Path,
    repo_catalog_arg: str | Path,
    raw_catalogs: Sequence[str],
    include_env_catalog: bool,
    workspace_runtime_only: bool,
    caller_anchor: Path,
    caller_start: str | Path,
    payload_status_key: str,
    error_code: str,
    validator_script: str,
    validator_status_field: str,
    row_projection: RowProjection | None = None,
    validator_extra_args_builder: ValidatorExtraArgsBuilder | None = None,
) -> dict[str, Any]:
    repo_catalog, catalogs_checked, catalog_selection_mode = resolve_active_runtime_catalog_candidates(
        repo_catalog_arg=repo_catalog_arg,
        raw_catalogs=raw_catalogs,
        include_env_catalog=include_env_catalog,
        workspace_runtime_only=workspace_runtime_only,
        caller_anchor=caller_anchor,
        caller_start=caller_start,
    )

    checked_rows: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    skipped_catalogs: list[str] = []
    stale_reasons: list[str] = []

    for catalog_path in catalogs_checked:
        if not catalog_path.exists() or not catalog_path.is_file():
            skipped_catalogs.append(str(catalog_path))
            continue
        for row in iter_active_runtime_catalog_rows(catalog_path=catalog_path):
            identity_id = str(row.get("id", "")).strip()
            extra_args = (
                list(validator_extra_args_builder(repo_catalog, catalog_path, identity_id))
                if validator_extra_args_builder is not None
                else []
            )
            validator_rc, validator_payload = run_json_validator(
                repo_root=repo_root,
                validator_script=validator_script,
                catalog_path=catalog_path,
                identity_id=identity_id,
                extra_args=extra_args,
            )
            validator_status = str(validator_payload.get(validator_status_field, "")).strip().upper()
            row_state: dict[str, Any] = {
                "identity_id": identity_id,
                "catalog_path": str(catalog_path),
                "validator_rc": validator_rc,
                "validator_script": validator_script,
                "validator_status_field": validator_status_field,
                validator_status_field: validator_status,
                "fleet_projection_policy_id": FLEET_PROJECTION_POLICY_ID,
                "catalog_selection_mode": catalog_selection_mode,
            }
            if row_projection is not None:
                row_state.update(
                    dict(
                        row_projection(
                            identity_id=identity_id,
                            catalog_path=catalog_path,
                            catalog_row=row,
                            validator_rc=validator_rc,
                            validator_payload=validator_payload,
                        )
                    )
                )
            row_state["status"] = (
                STATUS_PASS_REQUIRED
                if validator_rc == 0 and validator_status == STATUS_PASS_REQUIRED
                else STATUS_FAIL_REQUIRED
            )
            checked_rows.append(row_state)
            if row_state["status"] != STATUS_PASS_REQUIRED:
                violations.append(dict(row_state))

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    return {
        payload_status_key: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else error_code,
        "repo_catalog": str(repo_catalog),
        "repo_catalog_included": not workspace_runtime_only,
        "catalog_selection_mode": catalog_selection_mode,
        "fleet_projection_policy_id": FLEET_PROJECTION_POLICY_ID,
        "validator_script": validator_script,
        "validator_status_field": validator_status_field,
        "catalogs_checked": [str(path) for path in catalogs_checked],
        "skipped_catalogs": skipped_catalogs,
        "checked_identity_count": len(checked_rows),
        "checked_identity_ids": [str(row.get("identity_id", "")).strip() for row in checked_rows],
        "violation_count": len(violations),
        "checked_rows": checked_rows,
        "violations": violations,
        "stale_reasons": stale_reasons,
    }
