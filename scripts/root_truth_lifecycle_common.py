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
ROOT_TRUTH_LIFECYCLE_CURRENT = "identity/protocol/mappings/root-truth-lifecycle.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
TRUTH_LIFECYCLE_COMPLETENESS_SECTION_MARKER = "## Root truth-lifecycle completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class LifecycleRow:
    order: int
    lifecycle_id: str
    contract_heading: str
    lifecycle_role: str


@dataclass(frozen=True)
class MemoryStratumRow:
    order: int
    memory_id: str
    contract_heading: str
    memory_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class TruthLifecycleProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


@dataclass(frozen=True)
class TruthLifecycleCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class TruthLifecycleCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class TruthLifecycleCompletenessSurface:
    rel_path: str
    rows: tuple[TruthLifecycleCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_truth_lifecycle(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_TRUTH_LIFECYCLE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_TRUTH_LIFECYCLE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_truth_lifecycle_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def lifecycle_rows_from_doc(doc: Mapping[str, Any]) -> tuple[LifecycleRow, ...]:
    rows = doc.get("required_lifecycle_rows")
    if not isinstance(rows, list):
        return ()
    out: list[LifecycleRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lifecycle_id = _norm_str(row.get("lifecycle_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        lifecycle_role = _norm_str(row.get("lifecycle_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not lifecycle_id or not contract_heading or not lifecycle_role:
            continue
        out.append(
            LifecycleRow(
                order=order,
                lifecycle_id=lifecycle_id,
                contract_heading=contract_heading,
                lifecycle_role=lifecycle_role,
            )
        )
    return tuple(out)


def memory_strata_rows_from_doc(doc: Mapping[str, Any]) -> tuple[MemoryStratumRow, ...]:
    rows = doc.get("required_memory_strata_rows")
    if not isinstance(rows, list):
        return ()
    out: list[MemoryStratumRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        memory_id = _norm_str(row.get("memory_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        memory_role = _norm_str(row.get("memory_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not memory_id or not contract_heading or not memory_role:
            continue
        out.append(
            MemoryStratumRow(
                order=order,
                memory_id=memory_id,
                contract_heading=contract_heading,
                memory_role=memory_role,
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


def truth_lifecycle_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[TruthLifecycleProofRow, ...]:
    rows = doc.get("required_truth_lifecycle_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[TruthLifecycleProofRow] = []
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
            TruthLifecycleProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def truth_lifecycle_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_truth_lifecycle_limit_rows", row_key="limit_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")


def truth_lifecycle_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[TruthLifecycleCompletenessRow, ...]:
    rows = doc.get("truth_lifecycle_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[TruthLifecycleCompletenessRow] = []
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
            TruthLifecycleCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_truth_lifecycle_completeness_surface(repo_root: Path) -> TruthLifecycleCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return TruthLifecycleCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[TruthLifecycleCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == TRUTH_LIFECYCLE_COMPLETENESS_SECTION_MARKER:
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
            TruthLifecycleCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return TruthLifecycleCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
