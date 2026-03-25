#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_STREAM_DESIGN_ADMISSIBILITY_CURRENT = "identity/protocol/mappings/root-stream-design-admissibility.current.yaml"


@dataclass(frozen=True)
class RequiredQuestionRow:
    order: int
    question_id: str
    contract_heading: str
    normative_focus: str


@dataclass(frozen=True)
class OutcomeClassRow:
    order: int
    outcome_class: str


@dataclass(frozen=True)
class AdmissibilityProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


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


def load_root_stream_design_admissibility(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_STREAM_DESIGN_ADMISSIBILITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_STREAM_DESIGN_ADMISSIBILITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_admissibility_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def required_question_rows_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[RequiredQuestionRow, ...]:
    rows = admissibility_doc.get("required_question_rows")
    if not isinstance(rows, list):
        return ()
    out: list[RequiredQuestionRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = _norm_str(row.get("question_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        normative_focus = _norm_str(row.get("normative_focus"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not question_id or not contract_heading or not normative_focus:
            continue
        out.append(
            RequiredQuestionRow(
                order=order,
                question_id=question_id,
                contract_heading=contract_heading,
                normative_focus=normative_focus,
            )
        )
    return tuple(out)


def outcome_class_rows_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[OutcomeClassRow, ...]:
    rows = admissibility_doc.get("admissibility_outcome_rows")
    if not isinstance(rows, list):
        return ()
    out: list[OutcomeClassRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        outcome_class = _norm_str(row.get("outcome_class"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not outcome_class:
            continue
        out.append(OutcomeClassRow(order=order, outcome_class=outcome_class))
    return tuple(out)


def admissibility_proof_rows_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[AdmissibilityProofRow, ...]:
    rows = admissibility_doc.get("required_admissibility_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AdmissibilityProofRow] = []
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
            AdmissibilityProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def admissibility_limit_rows_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    rows = admissibility_doc.get("required_admissibility_limit_rows")
    if not isinstance(rows, list):
        return ()
    out: list[PhraseRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_id = _norm_str(row.get("limit_id"))
        contract_phrase = str(row.get("contract_phrase") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not row_id or not contract_phrase:
            continue
        out.append(PhraseRow(order=order, row_id=row_id, contract_phrase=contract_phrase))
    return tuple(out)


def required_projection_surfaces_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[str, ...]:
    return _as_str_tuple(admissibility_doc.get("required_projection_surfaces"))
