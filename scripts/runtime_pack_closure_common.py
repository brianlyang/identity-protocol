#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from runtime_fleet_closure_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    iter_active_runtime_catalog_rows,
    resolve_active_runtime_catalog_candidates,
)

PACK_SCAN_POLICY_ID = "active_runtime_pack_closure_scan_v1"

PackRowEvaluator = Callable[..., Mapping[str, Any]]


def resolve_runtime_pack_path(
    *,
    row: Mapping[str, Any],
    identity_id: str,
    catalog_path: Path,
    repo_root: Path,
    repo_catalog: Path,
    pack_path_keys: Sequence[str] = (),
) -> Path:
    candidate_keys = [str(key).strip() for key in pack_path_keys if str(key).strip()]
    if "pack_path" not in candidate_keys:
        candidate_keys.append("pack_path")
    for key in candidate_keys:
        raw_pack = str(row.get(key, "")).strip()
        if not raw_pack:
            continue
        pack_path = Path(raw_pack).expanduser()
        if not pack_path.is_absolute():
            pack_path = (catalog_path.parent / pack_path).resolve()
        return pack_path.resolve()
    if catalog_path.resolve() == repo_catalog.resolve():
        return (repo_root / "identity" / "packs" / identity_id).resolve()
    return (catalog_path.parent / identity_id).resolve()


def collect_active_runtime_pack_closure(
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
    row_evaluator: PackRowEvaluator,
    pack_path_keys: Sequence[str] = (),
    extra_payload: Mapping[str, Any] | None = None,
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
            pack_path = resolve_runtime_pack_path(
                row=row,
                identity_id=identity_id,
                catalog_path=catalog_path,
                repo_root=repo_root,
                repo_catalog=repo_catalog,
                pack_path_keys=pack_path_keys,
            )
            row_state = dict(
                row_evaluator(
                    identity_id=identity_id,
                    catalog_path=catalog_path,
                    catalog_row=row,
                    pack_path=pack_path,
                    repo_root=repo_root,
                    repo_catalog=repo_catalog,
                )
            )
            row_state.setdefault("identity_id", identity_id)
            row_state.setdefault("catalog_path", str(catalog_path))
            row_state.setdefault("pack_path", str(pack_path))
            row_state.setdefault("pack_scan_policy_id", PACK_SCAN_POLICY_ID)
            row_state.setdefault("catalog_selection_mode", catalog_selection_mode)
            row_status = str(row_state.get("status", "")).strip().upper()
            row_state["status"] = STATUS_PASS_REQUIRED if row_status == STATUS_PASS_REQUIRED else STATUS_FAIL_REQUIRED
            checked_rows.append(row_state)
            if row_state["status"] != STATUS_PASS_REQUIRED:
                violations.append(dict(row_state))

    if not checked_rows:
        stale_reasons.append("no_active_runtime_identities_found")

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        payload_status_key: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else error_code,
        "repo_catalog": str(repo_catalog),
        "repo_catalog_included": not workspace_runtime_only,
        "catalog_selection_mode": catalog_selection_mode,
        "pack_scan_policy_id": PACK_SCAN_POLICY_ID,
        "catalogs_checked": [str(path) for path in catalogs_checked],
        "skipped_catalogs": skipped_catalogs,
        "checked_identity_count": len(checked_rows),
        "checked_identity_ids": [str(row.get("identity_id", "")).strip() for row in checked_rows],
        "violation_count": len(violations),
        "checked_rows": checked_rows,
        "violations": violations,
        "stale_reasons": stale_reasons,
    }
    if extra_payload:
        payload.update(dict(extra_payload))
    return payload
