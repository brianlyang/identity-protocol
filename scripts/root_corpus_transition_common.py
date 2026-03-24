#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_TRANSITION_CURRENT = "identity/protocol/mappings/root-corpus-transition.current.yaml"


@dataclass(frozen=True)
class TransitionAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TransitionSurfaceProfile:
    surface_class: str
    surface_scope: str
    law_bearing: bool
    transition_mode: str
    direct_root_targets: tuple[str, ...] = field(default_factory=tuple)
    direct_current_turn_legality_allowed: bool = False
    strengthening_gateways: tuple[str, ...] = field(default_factory=tuple)


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


def load_root_corpus_transition(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_TRANSITION_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_TRANSITION_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_transition_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def transition_anchor_checks_from_doc(transition_doc: Mapping[str, Any]) -> tuple[TransitionAnchorCheck, ...]:
    rows = transition_doc.get("transition_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[TransitionAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(
            TransitionAnchorCheck(
                rel_path=rel_path,
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def transition_surface_profiles_from_doc(transition_doc: Mapping[str, Any]) -> tuple[TransitionSurfaceProfile, ...]:
    rows = transition_doc.get("surface_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[TransitionSurfaceProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        surface_class = _norm_str(row.get("surface_class"))
        surface_scope = _norm_str(row.get("surface_scope"))
        transition_mode = _norm_str(row.get("transition_mode"))
        if not surface_class or not surface_scope or not transition_mode:
            continue
        out.append(
            TransitionSurfaceProfile(
                surface_class=surface_class,
                surface_scope=surface_scope,
                law_bearing=bool(row.get("law_bearing", False)),
                transition_mode=transition_mode,
                direct_root_targets=_as_str_tuple(row.get("direct_root_targets")),
                direct_current_turn_legality_allowed=bool(row.get("direct_current_turn_legality_allowed", False)),
                strengthening_gateways=_as_str_tuple(row.get("strengthening_gateways")),
            )
        )
    return tuple(out)
