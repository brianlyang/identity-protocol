#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_DESIGN_QUESTION_CLOSURE_CURRENT = "identity/protocol/mappings/root-design-question-closure.current.yaml"


@dataclass(frozen=True)
class QuestionClosureRow:
    order: int
    question_id: str
    philosophy_marker: str
    admissibility_question_id: str
    admissibility_normative_focus: str
    target_component_id: str
    target_current_file: str
    target_validator_script: str
    target_status_key: str
    target_contract_file: str
    target_required_markers: tuple[str, ...] = field(default_factory=tuple)


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


def load_root_design_question_closure(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_DESIGN_QUESTION_CLOSURE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_DESIGN_QUESTION_CLOSURE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_design_question_closure_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def question_closure_rows_from_doc(doc: Mapping[str, Any]) -> tuple[QuestionClosureRow, ...]:
    rows = doc.get("required_question_closure_rows")
    if not isinstance(rows, list):
        return ()
    out: list[QuestionClosureRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = _norm_str(row.get("question_id"))
        philosophy_marker = str(row.get("philosophy_marker") or "").strip()
        admissibility_question_id = _norm_str(row.get("admissibility_question_id"))
        admissibility_normative_focus = _norm_str(row.get("admissibility_normative_focus"))
        target_component_id = _norm_str(row.get("target_component_id"))
        target_current_file = _norm_str(row.get("target_current_file"))
        target_validator_script = _norm_str(row.get("target_validator_script"))
        target_status_key = _norm_str(row.get("target_status_key"))
        target_contract_file = _norm_str(row.get("target_contract_file"))
        target_required_markers = _as_str_tuple(row.get("target_required_markers"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if (
            order <= 0
            or not question_id
            or not philosophy_marker
            or not admissibility_question_id
            or not admissibility_normative_focus
            or not target_component_id
            or not target_current_file
            or not target_validator_script
            or not target_status_key
            or not target_contract_file
            or not target_required_markers
        ):
            continue
        out.append(
            QuestionClosureRow(
                order=order,
                question_id=question_id,
                philosophy_marker=philosophy_marker,
                admissibility_question_id=admissibility_question_id,
                admissibility_normative_focus=admissibility_normative_focus,
                target_component_id=target_component_id,
                target_current_file=target_current_file,
                target_validator_script=target_validator_script,
                target_status_key=target_status_key,
                target_contract_file=target_contract_file,
                target_required_markers=target_required_markers,
            )
        )
    return tuple(out)
