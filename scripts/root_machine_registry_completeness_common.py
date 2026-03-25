#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT = (
    "identity/protocol/mappings/root-machine-registry-completeness.current.yaml"
)


@dataclass(frozen=True)
class AnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_machine_registry_completeness(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(
        repo_root, ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT
    )
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_completeness_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def anchor_checks_from_doc(doc: Mapping[str, Any]) -> tuple[AnchorCheck, ...]:
    rows = doc.get("anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[AnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        required_markers = _as_str_tuple(row.get("required_markers"))
        if not rel_path or not required_markers:
            continue
        out.append(AnchorCheck(rel_path=rel_path, required_markers=required_markers))
    return tuple(out)
