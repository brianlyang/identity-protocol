#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_SUCCESS_PATH_STATE_ADMISSIBILITY_CURRENT = "identity/protocol/mappings/root-success-path-state-admissibility.current.yaml"


@dataclass(frozen=True)
class StateClassRow:
    order: int
    state_class_id: str
    contract_heading: str
    state_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class StateAdmissionProofRow:
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


def load_root_success_path_state_admissibility(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_SUCCESS_PATH_STATE_ADMISSIBILITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_SUCCESS_PATH_STATE_ADMISSIBILITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_success_path_state_admissibility_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def state_class_rows_from_doc(doc: Mapping[str, Any]) -> tuple[StateClassRow, ...]:
    rows = doc.get("required_state_class_rows")
    if not isinstance(rows, list):
        return ()
    out: list[StateClassRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        state_class_id = _norm_str(row.get("state_class_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        state_role = _norm_str(row.get("state_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not state_class_id or not contract_heading or not state_role:
            continue
        out.append(
            StateClassRow(
                order=order,
                state_class_id=state_class_id,
                contract_heading=contract_heading,
                state_role=state_role,
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


def differentiation_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_differentiation_rows", row_key="differentiation_id")


def state_admission_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[StateAdmissionProofRow, ...]:
    rows = doc.get("required_state_admission_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[StateAdmissionProofRow] = []
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
            StateAdmissionProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def state_admission_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_state_admission_limit_rows", row_key="limit_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")
