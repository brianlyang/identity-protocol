#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_OPERATOR_ANSWER_SURFACE_CURRENT = "identity/protocol/mappings/root-operator-answer-surface.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
ANSWER_SURFACE_DISCIPLINE_SECTION_MARKER = "## Root operator answer-surface discipline"
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class SurfaceRow:
    order: int
    surface_id: str
    contract_heading: str
    surface_role: str


@dataclass(frozen=True)
class AnswerSurfaceStageRow:
    order: int
    stage_label: str
    bound_surface_ids: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnswerSurfaceStageSurfaceRow:
    order: int
    stage_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AnswerSurfaceStageSurface:
    rel_path: str
    rows: tuple[AnswerSurfaceStageSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


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


@dataclass(frozen=True)
class AnswerClaimAlignmentRow:
    order: int
    claim_id: str
    support_id: str
    decision_evidence_proof_id: str
    answer_claim_role: str


@dataclass(frozen=True)
class AnswerClaimEpistemicAlignmentRow:
    order: int
    claim_id: str
    current_truth_proof_id: str
    claim_epistemic_role: str


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


def answer_surface_stage_rows_from_doc(doc: Mapping[str, Any]) -> tuple[AnswerSurfaceStageRow, ...]:
    rows = doc.get("answer_surface_stage_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AnswerSurfaceStageRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        stage_label = str(row.get("stage_label") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not stage_label:
            continue
        out.append(
            AnswerSurfaceStageRow(
                order=order,
                stage_label=stage_label,
                bound_surface_ids=_as_str_tuple(row.get("bound_surface_ids")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def _readme_ordered_bold_section_rows(
    repo_root: Path,
    *,
    section_marker: str,
) -> tuple[tuple[tuple[int, str, tuple[str, ...]], ...], tuple[str, ...]]:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return (), ("target_missing",)

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[tuple[int, str, tuple[str, ...]]] = []
    current_order = 0
    current_label = ""
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_order, current_label, current_body_lines
        if current_order <= 0 or not current_label:
            return
        rows.append((current_order, current_label, tuple(line for line in current_body_lines if line)))
        current_order = 0
        current_label = ""
        current_body_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped == section_marker:
            section_found = True
            continue
        if not section_found:
            continue
        if HEADING_RE.match(stripped) or HORIZONTAL_RULE_RE.match(stripped):
            break
        match = ORDERED_BOLD_ITEM_RE.match(stripped)
        if match:
            flush_current()
            current_order = int(match.group(1))
            current_label = match.group(2).strip()
            continue
        if current_order <= 0:
            continue
        if stripped.startswith("- "):
            current_body_lines.append(stripped[2:].strip())
        elif stripped and line.startswith((" ", "\t")):
            current_body_lines.append(stripped)
        elif stripped:
            flush_current()
            break
    flush_current()

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("stage_rows_missing")
    elif any(not row[2] for row in rows):
        violations.append("stage_body_missing")

    return tuple(rows), tuple(violations)


def readme_answer_surface_stage_surface(repo_root: Path) -> AnswerSurfaceStageSurface:
    rows_data, violations = _readme_ordered_bold_section_rows(
        repo_root,
        section_marker=ANSWER_SURFACE_DISCIPLINE_SECTION_MARKER,
    )
    return AnswerSurfaceStageSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(
            AnswerSurfaceStageSurfaceRow(
                order=order,
                stage_label=stage_label,
                body_lines=body_lines,
            )
            for order, stage_label, body_lines in rows_data
        ),
        extraction_violations=violations,
    )


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


def answer_claim_alignment_rows_from_doc(doc: Mapping[str, Any]) -> tuple[AnswerClaimAlignmentRow, ...]:
    rows = doc.get("required_answer_claim_alignment_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AnswerClaimAlignmentRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        claim_id = _norm_str(row.get("claim_id"))
        support_id = _norm_str(row.get("support_id"))
        decision_evidence_proof_id = _norm_str(row.get("decision_evidence_proof_id"))
        answer_claim_role = _norm_str(row.get("answer_claim_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not claim_id or not support_id or not decision_evidence_proof_id or not answer_claim_role:
            continue
        out.append(
            AnswerClaimAlignmentRow(
                order=order,
                claim_id=claim_id,
                support_id=support_id,
                decision_evidence_proof_id=decision_evidence_proof_id,
                answer_claim_role=answer_claim_role,
            )
        )
    return tuple(out)


def answer_claim_epistemic_alignment_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[AnswerClaimEpistemicAlignmentRow, ...]:
    rows = doc.get("required_answer_claim_epistemic_alignment_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AnswerClaimEpistemicAlignmentRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        claim_id = _norm_str(row.get("claim_id"))
        current_truth_proof_id = _norm_str(row.get("current_truth_proof_id"))
        claim_epistemic_role = _norm_str(row.get("claim_epistemic_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not claim_id or not current_truth_proof_id or not claim_epistemic_role:
            continue
        out.append(
            AnswerClaimEpistemicAlignmentRow(
                order=order,
                claim_id=claim_id,
                current_truth_proof_id=current_truth_proof_id,
                claim_epistemic_role=claim_epistemic_role,
            )
        )
    return tuple(out)


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
