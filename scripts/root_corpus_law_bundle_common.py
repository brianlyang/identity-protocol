#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_LAW_BUNDLE_CURRENT = "identity/protocol/mappings/root-corpus-law-bundle.current.yaml"


@dataclass(frozen=True)
class BundleAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootLawBundleComponent:
    order: int
    component_id: str
    component_role: str
    current_file: str
    validator_script: str
    probe_script: str
    status_key: str


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


def load_root_corpus_law_bundle(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_LAW_BUNDLE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_LAW_BUNDLE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_bundle_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def bundle_anchor_checks_from_doc(bundle_doc: Mapping[str, Any]) -> tuple[BundleAnchorCheck, ...]:
    rows = bundle_doc.get("bundle_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[BundleAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(BundleAnchorCheck(rel_path=rel_path, required_markers=_as_str_tuple(row.get("required_markers"))))
    return tuple(out)


def bundle_components_from_doc(bundle_doc: Mapping[str, Any]) -> tuple[RootLawBundleComponent, ...]:
    rows = bundle_doc.get("component_rows")
    if not isinstance(rows, list):
        return ()
    out: list[RootLawBundleComponent] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        component_id = _norm_str(row.get("component_id"))
        component_role = _norm_str(row.get("component_role"))
        current_file = _norm_str(row.get("current_file"))
        validator_script = _norm_str(row.get("validator_script"))
        probe_script = _norm_str(row.get("probe_script"))
        status_key = _norm_str(row.get("status_key"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not component_id or not current_file or not validator_script or not status_key:
            continue
        out.append(
            RootLawBundleComponent(
                order=order,
                component_id=component_id,
                component_role=component_role,
                current_file=current_file,
                validator_script=validator_script,
                probe_script=probe_script,
                status_key=status_key,
            )
        )
    return tuple(out)
