#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

STREAM_DOC_REGISTRY_CURRENT = "identity/protocol/mappings/stream-doc-registry.current.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def resolve_alias_entry_path(repo_root: Path, configured_ref: str | Path) -> Path:
    raw = Path(str(configured_ref or "").strip()).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    return (repo_root / _norm_path(configured_ref)).resolve()


def resolve_current_yaml_alias(repo_root: Path, configured_ref: str | Path) -> tuple[Path, str, str]:
    entry_path = resolve_alias_entry_path(repo_root, configured_ref)
    if not entry_path.exists() or not entry_path.is_file():
        return entry_path, "", "current_file_missing"
    if not entry_path.name.endswith(".current.yaml"):
        return entry_path, "", ""
    current_doc = _load_yaml(entry_path)
    if not current_doc:
        return entry_path, "", "current_file_parse_failed"
    active_file = _norm_path(current_doc.get("active_file", ""))
    if not active_file:
        return entry_path, "", "active_file_missing"
    active_path = Path(active_file).expanduser()
    if not active_path.is_absolute():
        active_path = (repo_root / active_file).resolve()
    else:
        active_path = active_path.resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""
