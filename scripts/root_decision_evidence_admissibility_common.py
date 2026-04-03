#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_DECISION_EVIDENCE_ADMISSIBILITY_CURRENT = "identity/protocol/mappings/root-decision-evidence-admissibility.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
DECISION_EVIDENCE_ADMISSIBILITY_COMPLETENESS_SECTION_MARKER = "## Root decision-evidence admissibility completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class EvidenceClassRow:
    order: int
    evidence_class_id: str
    contract_heading: str
    evidence_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class DecisionEvidenceProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


@dataclass(frozen=True)
class EvidenceClassProofAlignmentRow:
    order: int
    evidence_class_id: str
    proof_id: str
    alignment_role: str


@dataclass(frozen=True)
class AdjudicationPhaseAlignmentRow:
    order: int
    machine_surface: str
    evidence_class_id: str
    proof_id: str
    surface_role: str


@dataclass(frozen=True)
class DecisionEvidenceAdmissibilityCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class DecisionEvidenceAdmissibilityCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class DecisionEvidenceAdmissibilityCompletenessSurface:
    rel_path: str
    rows: tuple[DecisionEvidenceAdmissibilityCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_decision_evidence_admissibility(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_DECISION_EVIDENCE_ADMISSIBILITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_DECISION_EVIDENCE_ADMISSIBILITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_decision_evidence_admissibility_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def evidence_class_rows_from_doc(doc: Mapping[str, Any]) -> tuple[EvidenceClassRow, ...]:
    rows = doc.get("required_evidence_class_rows")
    if not isinstance(rows, list):
        return ()
    out: list[EvidenceClassRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        evidence_class_id = _norm_str(row.get("evidence_class_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        evidence_role = _norm_str(row.get("evidence_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not evidence_class_id or not contract_heading or not evidence_role:
            continue
        out.append(
            EvidenceClassRow(
                order=order,
                evidence_class_id=evidence_class_id,
                contract_heading=contract_heading,
                evidence_role=evidence_role,
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


def decision_evidence_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[DecisionEvidenceProofRow, ...]:
    rows = doc.get("required_decision_evidence_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[DecisionEvidenceProofRow] = []
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
            DecisionEvidenceProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def evidence_class_proof_alignment_rows_from_doc(doc: Mapping[str, Any]) -> tuple[EvidenceClassProofAlignmentRow, ...]:
    rows = doc.get("required_evidence_class_proof_alignment_rows")
    if not isinstance(rows, list):
        return ()
    out: list[EvidenceClassProofAlignmentRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        evidence_class_id = _norm_str(row.get("evidence_class_id"))
        proof_id = _norm_str(row.get("proof_id"))
        alignment_role = _norm_str(row.get("alignment_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not evidence_class_id or not proof_id or not alignment_role:
            continue
        out.append(
            EvidenceClassProofAlignmentRow(
                order=order,
                evidence_class_id=evidence_class_id,
                proof_id=proof_id,
                alignment_role=alignment_role,
            )
        )
    return tuple(out)


def adjudication_phase_alignment_rows_from_doc(doc: Mapping[str, Any]) -> tuple[AdjudicationPhaseAlignmentRow, ...]:
    rows = doc.get("required_adjudication_phase_alignment_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AdjudicationPhaseAlignmentRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        machine_surface = _norm_str(row.get("machine_surface"))
        evidence_class_id = _norm_str(row.get("evidence_class_id"))
        proof_id = _norm_str(row.get("proof_id"))
        surface_role = _norm_str(row.get("surface_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not machine_surface or not evidence_class_id or not proof_id or not surface_role:
            continue
        out.append(
            AdjudicationPhaseAlignmentRow(
                order=order,
                machine_surface=machine_surface,
                evidence_class_id=evidence_class_id,
                proof_id=proof_id,
                surface_role=surface_role,
            )
        )
    return tuple(out)


def decision_evidence_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_decision_evidence_limit_rows", row_key="limit_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")


def decision_evidence_admissibility_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[DecisionEvidenceAdmissibilityCompletenessRow, ...]:
    rows = doc.get("decision_evidence_admissibility_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[DecisionEvidenceAdmissibilityCompletenessRow] = []
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
            DecisionEvidenceAdmissibilityCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_decision_evidence_admissibility_completeness_surface(
    repo_root: Path,
) -> DecisionEvidenceAdmissibilityCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return DecisionEvidenceAdmissibilityCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[DecisionEvidenceAdmissibilityCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == DECISION_EVIDENCE_ADMISSIBILITY_COMPLETENESS_SECTION_MARKER:
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
            DecisionEvidenceAdmissibilityCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return DecisionEvidenceAdmissibilityCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )


def evaluate_ordering_adjudication_phase_alignment(
    *,
    ordering_surface_profiles: Iterable[Any],
    required_alignment_rows: Iterable[AdjudicationPhaseAlignmentRow],
) -> list[dict[str, Any]]:
    profile_map = {
        _norm_str(getattr(row, "machine_surface", "")): row
        for row in ordering_surface_profiles
        if _norm_str(getattr(row, "machine_surface", ""))
    }
    violations: list[dict[str, Any]] = []
    previous_phase_order = 0
    for row in sorted(required_alignment_rows, key=lambda item: item.order):
        profile = profile_map.get(row.machine_surface)
        if profile is None:
            violations.append(
                {
                    "field": "root_corpus_ordering",
                    "reason": "ordering_adjudication_surface_missing",
                    "machine_surface": row.machine_surface,
                }
            )
            continue

        phase_order = int(getattr(profile, "phase_order", 0) or 0)
        surface_role = _norm_str(getattr(profile, "surface_role", ""))
        closure_terminal = bool(getattr(profile, "closure_terminal", False))
        expected_closure_terminal = row.machine_surface == "receipts"

        if phase_order <= previous_phase_order:
            violations.append(
                {
                    "field": "root_corpus_ordering",
                    "reason": "ordering_adjudication_phase_order_not_increasing",
                    "machine_surface": row.machine_surface,
                    "phase_order": phase_order,
                    "previous_phase_order": previous_phase_order,
                }
            )
        previous_phase_order = phase_order
        if surface_role != row.surface_role:
            violations.append(
                {
                    "field": "root_corpus_ordering",
                    "reason": "ordering_adjudication_surface_role_mismatch",
                    "machine_surface": row.machine_surface,
                    "expected": row.surface_role,
                    "actual": surface_role,
                }
            )
        if closure_terminal != expected_closure_terminal:
            violations.append(
                {
                    "field": "root_corpus_ordering",
                    "reason": "ordering_adjudication_closure_terminal_mismatch",
                    "machine_surface": row.machine_surface,
                    "expected": expected_closure_terminal,
                    "actual": closure_terminal,
                }
            )
    return violations
