#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CONSTITUTIONAL_SPINE_CURRENT = "identity/protocol/mappings/root-constitutional-spine.current.yaml"


@dataclass(frozen=True)
class ConstitutionalEntryRow:
    order: int
    rel_path: str
    corpus_class: str
    reading_order: int
    entry_role: str
    authority_role: str
    authority_mode: str
    question_classes: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BridgeRow:
    order: int
    bridge_id: str
    source_rel_path: str
    source_markers: tuple[str, ...] = field(default_factory=tuple)
    target_rel_path: str = ""
    target_markers: tuple[str, ...] = field(default_factory=tuple)


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


def load_root_constitutional_spine(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CONSTITUTIONAL_SPINE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CONSTITUTIONAL_SPINE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_constitutional_spine_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def constitutional_entry_rows_from_doc(doc: Mapping[str, Any]) -> tuple[ConstitutionalEntryRow, ...]:
    rows = doc.get("required_constitutional_entry_rows")
    if not isinstance(rows, list):
        return ()
    out: list[ConstitutionalEntryRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        corpus_class = _norm_str(row.get("corpus_class"))
        entry_role = _norm_str(row.get("entry_role"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        try:
            order = int(row.get("order"))
            reading_order = int(row.get("reading_order"))
        except Exception:
            continue
        question_classes = _as_str_tuple(row.get("question_classes"))
        required_markers = _as_str_tuple(row.get("required_markers"))
        if (
            order <= 0
            or reading_order <= 0
            or not rel_path
            or not corpus_class
            or not entry_role
            or not authority_role
            or not authority_mode
        ):
            continue
        out.append(
            ConstitutionalEntryRow(
                order=order,
                rel_path=rel_path,
                corpus_class=corpus_class,
                reading_order=reading_order,
                entry_role=entry_role,
                authority_role=authority_role,
                authority_mode=authority_mode,
                question_classes=question_classes,
                required_markers=required_markers,
            )
        )
    return tuple(out)


def bridge_rows_from_doc(doc: Mapping[str, Any]) -> tuple[BridgeRow, ...]:
    rows = doc.get("required_spine_bridge_rows")
    if not isinstance(rows, list):
        return ()
    out: list[BridgeRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        bridge_id = _norm_str(row.get("bridge_id"))
        source_rel_path = _norm_str(row.get("source_rel_path"))
        target_rel_path = _norm_str(row.get("target_rel_path"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        source_markers = _as_str_tuple(row.get("source_markers"))
        target_markers = _as_str_tuple(row.get("target_markers"))
        if order <= 0 or not bridge_id or not source_rel_path or not target_rel_path:
            continue
        out.append(
            BridgeRow(
                order=order,
                bridge_id=bridge_id,
                source_rel_path=source_rel_path,
                source_markers=source_markers,
                target_rel_path=target_rel_path,
                target_markers=target_markers,
            )
        )
    return tuple(out)
