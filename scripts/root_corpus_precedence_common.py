#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_PRECEDENCE_CURRENT = "identity/protocol/mappings/root-corpus-precedence.current.yaml"


@dataclass(frozen=True)
class PrecedenceAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PrecedenceProfile:
    conflict_class: str
    conflict_scope: str
    resolution_mode: str
    semantic_precedence_chain: tuple[str, ...] = field(default_factory=tuple)
    terminal_machine_surfaces: tuple[str, ...] = field(default_factory=tuple)
    motivating_only_surface_classes: tuple[str, ...] = field(default_factory=tuple)
    forbidden_override_surface_classes: tuple[str, ...] = field(default_factory=tuple)


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


def load_root_corpus_precedence(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_PRECEDENCE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_PRECEDENCE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_precedence_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def precedence_anchor_checks_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[PrecedenceAnchorCheck, ...]:
    rows = precedence_doc.get("precedence_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[PrecedenceAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(
            PrecedenceAnchorCheck(
                rel_path=rel_path,
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def precedence_profiles_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[PrecedenceProfile, ...]:
    rows = precedence_doc.get("precedence_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[PrecedenceProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        conflict_class = _norm_str(row.get("conflict_class"))
        conflict_scope = _norm_str(row.get("conflict_scope"))
        resolution_mode = _norm_str(row.get("resolution_mode"))
        if not conflict_class or not conflict_scope or not resolution_mode:
            continue
        out.append(
            PrecedenceProfile(
                conflict_class=conflict_class,
                conflict_scope=conflict_scope,
                resolution_mode=resolution_mode,
                semantic_precedence_chain=_as_str_tuple(row.get("semantic_precedence_chain")),
                terminal_machine_surfaces=_as_str_tuple(row.get("terminal_machine_surfaces")),
                motivating_only_surface_classes=_as_str_tuple(row.get("motivating_only_surface_classes")),
                forbidden_override_surface_classes=_as_str_tuple(row.get("forbidden_override_surface_classes")),
            )
        )
    return tuple(out)
