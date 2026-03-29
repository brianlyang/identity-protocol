#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_IDENTITY_INSTANCE_SELF_JUDGEMENT_CURRENT = "identity/protocol/mappings/root-identity-instance-self-judgement.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_SECTION_MARKER = "## Root identity-instance self-judgement completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class QuestionRow:
    order: int
    question_id: str
    contract_heading: str
    judgement_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class SelfJudgementProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


@dataclass(frozen=True)
class IdentityInstanceSelfJudgementCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class IdentityInstanceSelfJudgementCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class IdentityInstanceSelfJudgementCompletenessSurface:
    rel_path: str
    rows: tuple[IdentityInstanceSelfJudgementCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_identity_instance_self_judgement(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_IDENTITY_INSTANCE_SELF_JUDGEMENT_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_IDENTITY_INSTANCE_SELF_JUDGEMENT_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_self_judgement_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def question_rows_from_doc(doc: Mapping[str, Any]) -> tuple[QuestionRow, ...]:
    rows = doc.get("required_question_rows")
    if not isinstance(rows, list):
        return ()
    out: list[QuestionRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_id = _norm_str(row.get("question_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        judgement_role = _norm_str(row.get("judgement_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not question_id or not contract_heading or not judgement_role:
            continue
        out.append(
            QuestionRow(
                order=order,
                question_id=question_id,
                contract_heading=contract_heading,
                judgement_role=judgement_role,
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


def anchor_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_anchor_rows", row_key="anchor_id")


def self_judgement_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[SelfJudgementProofRow, ...]:
    rows = doc.get("required_self_judgement_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[SelfJudgementProofRow] = []
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
            SelfJudgementProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def self_judgement_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_self_judgement_limit_rows", row_key="limit_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")


def identity_instance_self_judgement_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[IdentityInstanceSelfJudgementCompletenessRow, ...]:
    rows = doc.get("identity_instance_self_judgement_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[IdentityInstanceSelfJudgementCompletenessRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        completeness_id = _norm_str(row.get("completeness_id"))
        contract_phrase = str(row.get("contract_phrase") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not completeness_id or not contract_phrase:
            continue
        out.append(
            IdentityInstanceSelfJudgementCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_identity_instance_self_judgement_completeness_surface(
    repo_root: Path,
) -> IdentityInstanceSelfJudgementCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return IdentityInstanceSelfJudgementCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[IdentityInstanceSelfJudgementCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == IDENTITY_INSTANCE_SELF_JUDGEMENT_COMPLETENESS_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if HEADING_RE.match(stripped) or HORIZONTAL_RULE_RE.match(stripped):
            break
        match = ORDERED_ITEM_RE.match(stripped)
        if not match:
            continue
        rows.append(
            IdentityInstanceSelfJudgementCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return IdentityInstanceSelfJudgementCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
