#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_OPERATOR_ANSWER_SURFACE_CURRENT = "identity/protocol/mappings/root-operator-answer-surface.current.yaml"


@dataclass(frozen=True)
class SurfaceRow:
    order: int
    surface_id: str
    contract_heading: str
    surface_role: str


@dataclass(frozen=True)
class SupportMemoryRow:
    order: int
    support_id: str
    contract_heading: str
    support_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class AnswerSurfaceProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_operator_answer_surface(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_OPERATOR_ANSWER_SURFACE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_OPERATOR_ANSWER_SURFACE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_answer_surface_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def surface_rows_from_doc(doc: Mapping[str, Any]) -> tuple[SurfaceRow, ...]:
    rows = doc.get("required_surface_rows")
    if not isinstance(rows, list):
        return ()
    out: list[SurfaceRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        surface_id = _norm_str(row.get("surface_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        surface_role = _norm_str(row.get("surface_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not surface_id or not contract_heading or not surface_role:
            continue
        out.append(
            SurfaceRow(
                order=order,
                surface_id=surface_id,
                contract_heading=contract_heading,
                surface_role=surface_role,
            )
        )
    return tuple(out)


def support_memory_rows_from_doc(doc: Mapping[str, Any]) -> tuple[SupportMemoryRow, ...]:
    rows = doc.get("required_support_memory_rows")
    if not isinstance(rows, list):
        return ()
    out: list[SupportMemoryRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        support_id = _norm_str(row.get("support_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        support_role = _norm_str(row.get("support_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not support_id or not contract_heading or not support_role:
            continue
        out.append(
            SupportMemoryRow(
                order=order,
                support_id=support_id,
                contract_heading=contract_heading,
                support_role=support_role,
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


def support_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_support_limit_rows", row_key="limit_id")


def answer_surface_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[AnswerSurfaceProofRow, ...]:
    rows = doc.get("required_answer_surface_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AnswerSurfaceProofRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        proof_id = _norm_str(row.get("proof_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        proof_role = _norm_str(row.get("proof_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not proof_id or not contract_heading or not proof_role:
            continue
        out.append(
            AnswerSurfaceProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def answer_surface_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_answer_surface_limit_rows", row_key="limit_id")


def boundary_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_boundary_rows", row_key="boundary_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")
