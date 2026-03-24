#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_ORDERING_CURRENT = "identity/protocol/mappings/root-corpus-ordering.current.yaml"


@dataclass(frozen=True)
class SourceOrderRow:
    order: int
    corpus_class: str
    source_role: str
    law_bearing_required: bool


@dataclass(frozen=True)
class ReadingOrderRow:
    order: int
    rel_path: str
    entry_role: str


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_corpus_ordering(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_ORDERING_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_ORDERING_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_ordering_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def source_order_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[SourceOrderRow, ...]:
    rows = ordering_doc.get("source_order")
    if not isinstance(rows, list):
        return ()
    out: list[SourceOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        source_role = _norm_str(row.get("source_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not corpus_class or not source_role:
            continue
        out.append(
            SourceOrderRow(
                order=order,
                corpus_class=corpus_class,
                source_role=source_role,
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)


def reading_order_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[ReadingOrderRow, ...]:
    rows = ordering_doc.get("reading_order")
    if not isinstance(rows, list):
        return ()
    out: list[ReadingOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        entry_role = _norm_str(row.get("entry_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not rel_path or not entry_role:
            continue
        out.append(
            ReadingOrderRow(
                order=order,
                rel_path=rel_path,
                entry_role=entry_role,
            )
        )
    return tuple(out)
