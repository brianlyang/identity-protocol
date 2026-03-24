#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_PROTOCOL_INSTANCE_RESPONSIBILITY_CURRENT = "identity/protocol/mappings/root-protocol-instance-responsibility.current.yaml"


@dataclass(frozen=True)
class LayerRow:
    order: int
    layer_id: str
    contract_heading: str
    layer_role: str


@dataclass(frozen=True)
class ResponsibilityRow:
    order: int
    owner_id: str
    contract_heading: str
    responsibility_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


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


def load_root_protocol_instance_responsibility(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_PROTOCOL_INSTANCE_RESPONSIBILITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_PROTOCOL_INSTANCE_RESPONSIBILITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_responsibility_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def layer_rows_from_doc(doc: Mapping[str, Any]) -> tuple[LayerRow, ...]:
    rows = doc.get("required_layer_rows")
    if not isinstance(rows, list):
        return ()
    out: list[LayerRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        layer_id = _norm_str(row.get("layer_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        layer_role = _norm_str(row.get("layer_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not layer_id or not contract_heading or not layer_role:
            continue
        out.append(LayerRow(order=order, layer_id=layer_id, contract_heading=contract_heading, layer_role=layer_role))
    return tuple(out)


def responsibility_rows_from_doc(doc: Mapping[str, Any]) -> tuple[ResponsibilityRow, ...]:
    rows = doc.get("required_responsibility_rows")
    if not isinstance(rows, list):
        return ()
    out: list[ResponsibilityRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        owner_id = _norm_str(row.get("owner_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        responsibility_role = _norm_str(row.get("responsibility_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not owner_id or not contract_heading or not responsibility_role:
            continue
        out.append(
            ResponsibilityRow(
                order=order,
                owner_id=owner_id,
                contract_heading=contract_heading,
                responsibility_role=responsibility_role,
            )
        )
    return tuple(out)


def _phrase_rows_from_field(doc: Mapping[str, Any], field: str, *, row_key: str) -> tuple[PhraseRow, ...]:
    rows = doc.get(field)
    if not isinstance(rows, list):
        return ()
    out: list[PhraseRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_id = _norm_str(row.get(row_key))
        contract_phrase = str(row.get("contract_phrase") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not row_id or not contract_phrase:
            continue
        out.append(PhraseRow(order=order, row_id=row_id, contract_phrase=contract_phrase))
    return tuple(out)


def escalation_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_escalation_rows", row_key="trigger_id")


def boundary_collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_boundary_collapse_rows", row_key="collapse_id")
