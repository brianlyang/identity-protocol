#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def pick_identity_id(local_catalog_path: Path) -> str:
    catalog = load_yaml(local_catalog_path)
    identities = [row for row in (catalog.get("identities") or []) if isinstance(row, dict)]
    default_identity = str(catalog.get("default_identity", "")).strip()
    if default_identity:
        return default_identity
    for row in identities:
        if str(row.get("status", "")).strip().lower() == "active":
            identity_id = str(row.get("id", "")).strip()
            if identity_id:
                return identity_id
    for row in identities:
        identity_id = str(row.get("id", "")).strip()
        if identity_id:
            return identity_id
    raise ValueError(f"no identity rows found in local catalog: {local_catalog_path}")


def run_json(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(command)}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid json output from {' '.join(command)}: {exc}") from exc


def _resolve_row_path(raw_path: str, *, catalog_path: Path, identity_id: str) -> Path:
    raw = str(raw_path or "").strip()
    if not raw:
        return (catalog_path.parent / identity_id).resolve()
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (catalog_path.parent / candidate).resolve()


def materialize_single_identity_runtime_workspace(
    *,
    source_catalog_path: Path,
    identity_id: str,
    target_workspace_root: Path,
) -> dict[str, Any]:
    source_catalog_path = source_catalog_path.resolve()
    target_workspace_root = target_workspace_root.resolve()
    catalog = load_yaml(source_catalog_path)
    rows = [row for row in (catalog.get("identities") or []) if isinstance(row, dict)]
    row = next((row for row in rows if str(row.get("id", "")).strip() == identity_id), None)
    if row is None:
        raise ValueError(f"missing identity row: {identity_id}")

    source_pack_path = _resolve_row_path(
        str(row.get("canonical_pack_path") or row.get("pack_path") or ""),
        catalog_path=source_catalog_path,
        identity_id=identity_id,
    )
    if not source_pack_path.exists():
        raise FileNotFoundError(f"missing source pack: {source_pack_path}")

    target_identity_home = (target_workspace_root / ".identity").resolve()
    if target_identity_home.exists():
        shutil.rmtree(target_identity_home)
    target_identity_home.mkdir(parents=True, exist_ok=True)

    target_pack_path = (target_identity_home / identity_id).resolve()
    shutil.copytree(source_pack_path, target_pack_path, symlinks=False, ignore=shutil.ignore_patterns("__pycache__"))

    materialized_row = dict(row)
    materialized_row["pack_path"] = str(target_pack_path)
    materialized_row["canonical_pack_path"] = str(target_pack_path)
    canonical_scope = str(materialized_row.get("canonical_scope", "")).strip().upper()
    if not canonical_scope or canonical_scope == "UNKNOWN":
        fallback_scope = str(materialized_row.get("scope", "")).strip().upper() or "USER"
        materialized_row["canonical_scope"] = fallback_scope

    target_catalog_path = (target_identity_home / "catalog.local.yaml").resolve()
    target_catalog_path.write_text(
        yaml.safe_dump({"identities": [materialized_row]}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return {
        "target_workspace_root": str(target_workspace_root),
        "target_identity_home": str(target_identity_home),
        "target_catalog_path": str(target_catalog_path),
        "target_pack_path": str(target_pack_path),
        "source_catalog_path": str(source_catalog_path),
        "source_pack_path": str(source_pack_path),
    }


def write_runtime_defaults(
    *,
    codex_home: Path,
    protocol_home: Path | None = None,
    identity_home: Path | None = None,
    identity_catalog: Path | None = None,
) -> Path:
    config_dir = (codex_home.resolve() / ".identity" / "config").resolve()
    config_dir.mkdir(parents=True, exist_ok=True)
    runtime_env_path = (config_dir / "runtime-paths.env").resolve()
    lines: list[str] = []
    if protocol_home is not None:
        lines.append(f"IDENTITY_PROTOCOL_HOME={protocol_home.resolve()}")
    if identity_home is not None:
        lines.append(f"IDENTITY_HOME={identity_home.resolve()}")
    if identity_catalog is not None:
        lines.append(f"IDENTITY_CATALOG={identity_catalog.resolve()}")
    runtime_env_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return runtime_env_path
