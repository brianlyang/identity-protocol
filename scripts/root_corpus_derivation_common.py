#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_DERIVATION_CURRENT = "identity/protocol/mappings/root-corpus-derivation.current.yaml"


@dataclass(frozen=True)
class DerivationAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DerivationClassProfile:
    corpus_class: str
    derivation_mode: str
    allowed_upstream_classes: tuple[str, ...] = field(default_factory=tuple)
    law_bearing_required: bool = False


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


def load_root_corpus_derivation(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_DERIVATION_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_DERIVATION_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_derivation_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def derivation_anchor_checks_from_doc(derivation_doc: Mapping[str, Any]) -> tuple[DerivationAnchorCheck, ...]:
    rows = derivation_doc.get("derivation_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[DerivationAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(
            DerivationAnchorCheck(
                rel_path=rel_path,
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def derivation_class_profiles_from_doc(derivation_doc: Mapping[str, Any]) -> tuple[DerivationClassProfile, ...]:
    rows = derivation_doc.get("derivation_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[DerivationClassProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        derivation_mode = _norm_str(row.get("derivation_mode"))
        if not corpus_class or not derivation_mode:
            continue
        out.append(
            DerivationClassProfile(
                corpus_class=corpus_class,
                derivation_mode=derivation_mode,
                allowed_upstream_classes=_as_str_tuple(row.get("allowed_upstream_classes")),
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)
