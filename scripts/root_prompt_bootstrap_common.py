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
ROOT_PROMPT_BOOTSTRAP_CURRENT = "identity/protocol/mappings/root-prompt-bootstrap.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
PROMPT_BOOTSTRAP_COMPLETENESS_SECTION_MARKER = "## Root prompt-bootstrap completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class AnchorRow:
    order: int
    anchor_id: str
    contract_heading: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class PromptBootstrapProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


@dataclass(frozen=True)
class PromptBootstrapCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class PromptBootstrapCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class PromptBootstrapCompletenessSurface:
    rel_path: str
    rows: tuple[PromptBootstrapCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_prompt_bootstrap(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_PROMPT_BOOTSTRAP_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_PROMPT_BOOTSTRAP_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_prompt_bootstrap_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def anchor_rows_from_doc(doc: Mapping[str, Any]) -> tuple[AnchorRow, ...]:
    rows = doc.get("required_anchor_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AnchorRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        anchor_id = _norm_str(row.get("anchor_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not anchor_id or not contract_heading:
            continue
        out.append(AnchorRow(order=order, anchor_id=anchor_id, contract_heading=contract_heading))
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


def output_field_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_output_field_rows", row_key="output_field_id")


def binding_field_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_binding_field_rows", row_key="binding_field_id")


def prompt_bootstrap_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PromptBootstrapProofRow, ...]:
    rows = doc.get("required_prompt_bootstrap_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[PromptBootstrapProofRow] = []
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
            PromptBootstrapProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def prompt_bootstrap_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_prompt_bootstrap_limit_rows", row_key="limit_id")


def native_literal_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_native_literal_rows", row_key="native_literal_id")


def prompt_bootstrap_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[PromptBootstrapCompletenessRow, ...]:
    rows = doc.get("prompt_bootstrap_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[PromptBootstrapCompletenessRow] = []
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
            PromptBootstrapCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_prompt_bootstrap_completeness_surface(repo_root: Path) -> PromptBootstrapCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return PromptBootstrapCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[PromptBootstrapCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == PROMPT_BOOTSTRAP_COMPLETENESS_SECTION_MARKER:
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
            PromptBootstrapCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("completeness_rows_missing")

    return PromptBootstrapCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
