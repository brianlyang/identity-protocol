#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import (
    _default_user_identity_home,
    _detect_repo_root,
    _project_identity_home_from_repo_catalog,
)

ARCHIVE_KEY = "identity_uniqueness_archive"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def find_identity_row(catalog: dict[str, Any], identity_id: str) -> tuple[int, dict[str, Any]]:
    for idx, row in enumerate(catalog.get("identities", []) or []):
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() == identity_id:
            return idx, row
    return -1, {}


def is_runtime_row(row: dict[str, Any]) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile != "fixture" and runtime_mode != "demo_only"


def is_active_row(row: dict[str, Any]) -> bool:
    return str((row or {}).get("status", "")).strip().lower() in {"active", "enabled", "on"}


def resolve_project_catalog_from_repo(repo_catalog: Path) -> Path:
    repo_catalog = repo_catalog.expanduser().resolve()
    repo_root = _detect_repo_root(repo_catalog.parent)
    project_identity_home = _project_identity_home_from_repo_catalog(repo_root, repo_catalog)
    return (project_identity_home / "catalog.local.yaml").resolve()


def resolve_global_catalog() -> Path:
    return (_default_user_identity_home() / "catalog.local.yaml").resolve()


def analyze_cross_layer_identity_uniqueness(
    identity_id: str,
    *,
    project_catalog: Path,
    global_catalog: Path,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for layer, path in (("project", project_catalog), ("global", global_catalog)):
        catalog_path = path.expanduser().resolve()
        doc = load_yaml(catalog_path)
        idx, row = find_identity_row(doc, identity_id)
        row_exists = idx >= 0
        runtime_row = is_runtime_row(row)
        active_row = is_active_row(row)
        entries.append(
            {
                "layer": layer,
                "catalog_path": str(catalog_path),
                "row_exists": row_exists,
                "row_index": idx,
                "row": row if isinstance(row, dict) else {},
                "runtime_row": runtime_row,
                "active_row": active_row,
                "status": str((row or {}).get("status", "")).strip(),
                "profile": str((row or {}).get("profile", "")).strip(),
                "runtime_mode": str((row or {}).get("runtime_mode", "")).strip(),
                "pack_path": str((row or {}).get("pack_path", "")).strip(),
            }
        )

    runtime_entries = [entry for entry in entries if entry.get("row_exists") and entry.get("runtime_row")]
    active_runtime_entries = [entry for entry in runtime_entries if entry.get("active_row")]
    pack_paths = sorted({str(entry.get("pack_path", "")).strip() for entry in runtime_entries if str(entry.get("pack_path", "")).strip()})
    return {
        "identity_id": identity_id,
        "project_catalog": str(project_catalog.expanduser().resolve()),
        "global_catalog": str(global_catalog.expanduser().resolve()),
        "entries": entries,
        "runtime_duplicate_detected": len(runtime_entries) > 1,
        "active_runtime_duplicate_detected": len(active_runtime_entries) > 1,
        "runtime_duplicate_layers": [str(entry.get("layer", "")).strip() for entry in runtime_entries],
        "active_runtime_duplicate_layers": [str(entry.get("layer", "")).strip() for entry in active_runtime_entries],
        "duplicate_pack_paths": pack_paths,
    }


def archive_removed_identity_row(
    doc: dict[str, Any],
    *,
    removed_row: dict[str, Any],
    removed_layer: str,
    kept_layer: str,
    archived_at: str,
    archive_reason: str,
) -> None:
    archive = doc.get(ARCHIVE_KEY)
    if not isinstance(archive, list):
        archive = []
        doc[ARCHIVE_KEY] = archive
    archive.append(
        {
            "identity_id": str((removed_row or {}).get("id", "")).strip(),
            "removed_layer": removed_layer,
            "kept_layer": kept_layer,
            "archived_at": archived_at,
            "archived_by": "repair_identity_cross_layer_uniqueness.py",
            "archive_reason": archive_reason,
            "row": removed_row,
        }
    )
