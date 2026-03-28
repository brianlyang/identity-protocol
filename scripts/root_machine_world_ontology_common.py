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
ROOT_MACHINE_WORLD_ONTOLOGY_CURRENT = "identity/protocol/mappings/root-machine-world-ontology.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
MACHINE_WORLD_ONTOLOGY_COMPLETENESS_SECTION_MARKER = "## Root machine-world ontology completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class StratumRow:
    order: int
    stratum_id: str
    contract_heading: str
    stratum_role: str


@dataclass(frozen=True)
class PhraseRow:
    order: int
    row_id: str
    contract_phrase: str


@dataclass(frozen=True)
class OntologyProofRow:
    order: int
    proof_id: str
    contract_heading: str
    proof_role: str


@dataclass(frozen=True)
class MachineWorldOntologyCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class MachineWorldOntologyCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class MachineWorldOntologyCompletenessSurface:
    rel_path: str
    rows: tuple[MachineWorldOntologyCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_machine_world_ontology(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_MACHINE_WORLD_ONTOLOGY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_MACHINE_WORLD_ONTOLOGY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_machine_world_ontology_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def stratum_rows_from_doc(doc: Mapping[str, Any]) -> tuple[StratumRow, ...]:
    rows = doc.get("required_strata_rows")
    if not isinstance(rows, list):
        return ()
    out: list[StratumRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        stratum_id = _norm_str(row.get("stratum_id"))
        contract_heading = str(row.get("contract_heading") or "").strip()
        stratum_role = _norm_str(row.get("stratum_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not stratum_id or not contract_heading or not stratum_role:
            continue
        out.append(
            StratumRow(
                order=order,
                stratum_id=stratum_id,
                contract_heading=contract_heading,
                stratum_role=stratum_role,
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


def object_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_object_rows", row_key="object_id")


def ontology_proof_rows_from_doc(doc: Mapping[str, Any]) -> tuple[OntologyProofRow, ...]:
    rows = doc.get("required_ontology_proof_rows")
    if not isinstance(rows, list):
        return ()
    out: list[OntologyProofRow] = []
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
            OntologyProofRow(
                order=order,
                proof_id=proof_id,
                contract_heading=contract_heading,
                proof_role=proof_role,
            )
        )
    return tuple(out)


def ontology_limit_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_ontology_limit_rows", row_key="limit_id")


def collapse_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhraseRow, ...]:
    return _phrase_rows_from_field(doc, "required_collapse_rows", row_key="collapse_id")


def machine_world_ontology_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[MachineWorldOntologyCompletenessRow, ...]:
    rows = doc.get("machine_world_ontology_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[MachineWorldOntologyCompletenessRow] = []
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
            MachineWorldOntologyCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_machine_world_ontology_completeness_surface(
    repo_root: Path,
) -> MachineWorldOntologyCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return MachineWorldOntologyCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[MachineWorldOntologyCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == MACHINE_WORLD_ONTOLOGY_COMPLETENESS_SECTION_MARKER:
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
            MachineWorldOntologyCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("completeness_rows_missing")

    return MachineWorldOntologyCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
