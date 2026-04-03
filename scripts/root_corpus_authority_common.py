#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import RootDocAnchorCheck, root_doc_anchor_checks_from_doc

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_AUTHORITY_CURRENT = "identity/protocol/mappings/root-corpus-authority.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
AUTHORITY_LAYERING_SECTION_MARKER = "## Authority layering"
AUTHORITY_COMPLETENESS_SECTION_MARKER = "## Root authority completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


AuthorityAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class AuthorityClassProfile:
    corpus_class: str
    authority_role: str
    authority_mode: str
    philosophical_primacy: bool
    law_bearing_required: bool


@dataclass(frozen=True)
class EntryAuthorityProjection:
    rel_path: str
    corpus_class: str
    authority_role: str
    authority_mode: str


@dataclass(frozen=True)
class AuthorityLayerStage:
    order: int
    stage_label: str
    bound_corpus_classes: tuple[str, ...]
    bound_authority_roles: tuple[str, ...]
    bound_machine_surfaces: tuple[str, ...]
    required_markers: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityLayerStageSurfaceRow:
    order: int
    stage_label: str
    body_lines: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityLayerStageSurface:
    rel_path: str
    rows: tuple[AuthorityLayerStageSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class AuthorityCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class AuthorityCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class AuthorityCompletenessSurface:
    rel_path: str
    rows: tuple[AuthorityCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


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


def load_root_corpus_authority(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_AUTHORITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_AUTHORITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_authority_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def authority_anchor_checks_from_doc(authority_doc: Mapping[str, Any]) -> tuple[AuthorityAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        authority_doc,
        field_name="authority_anchor_checks",
        require_markers=False,
    )


def authority_class_profiles_from_doc(authority_doc: Mapping[str, Any]) -> tuple[AuthorityClassProfile, ...]:
    rows = authority_doc.get("authority_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[AuthorityClassProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        if not corpus_class or not authority_role or not authority_mode:
            continue
        out.append(
            AuthorityClassProfile(
                corpus_class=corpus_class,
                authority_role=authority_role,
                authority_mode=authority_mode,
                philosophical_primacy=bool(row.get("philosophical_primacy", False)),
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)


def entry_authority_projections_from_doc(authority_doc: Mapping[str, Any]) -> tuple[EntryAuthorityProjection, ...]:
    rows = authority_doc.get("entry_authority_projection")
    if not isinstance(rows, list):
        return ()
    out: list[EntryAuthorityProjection] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        corpus_class = _norm_str(row.get("corpus_class"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        if not rel_path or not corpus_class or not authority_role or not authority_mode:
            continue
        out.append(
            EntryAuthorityProjection(
                rel_path=rel_path,
                corpus_class=corpus_class,
                authority_role=authority_role,
                authority_mode=authority_mode,
            )
        )
    return tuple(out)


def authority_layer_stages_from_doc(authority_doc: Mapping[str, Any]) -> tuple[AuthorityLayerStage, ...]:
    rows = authority_doc.get("authority_layer_stages")
    if not isinstance(rows, list):
        return ()
    out: list[AuthorityLayerStage] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        stage_label = _norm_str(row.get("stage_label"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not stage_label:
            continue
        out.append(
            AuthorityLayerStage(
                order=order,
                stage_label=stage_label,
                bound_corpus_classes=_as_str_tuple(row.get("bound_corpus_classes")),
                bound_authority_roles=_as_str_tuple(row.get("bound_authority_roles")),
                bound_machine_surfaces=_as_str_tuple(row.get("bound_machine_surfaces")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def authority_completeness_rows_from_doc(
    authority_doc: Mapping[str, Any],
) -> tuple[AuthorityCompletenessRow, ...]:
    rows = authority_doc.get("authority_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[AuthorityCompletenessRow] = []
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
            AuthorityCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_authority_completeness_surface(repo_root: Path) -> AuthorityCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return AuthorityCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[AuthorityCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == AUTHORITY_COMPLETENESS_SECTION_MARKER:
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
            AuthorityCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return AuthorityCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )


def readme_authority_layer_surface(repo_root: Path) -> AuthorityLayerStageSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return AuthorityLayerStageSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[AuthorityLayerStageSurfaceRow] = []
    current_order = 0
    current_label = ""
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_order, current_label, current_body_lines
        if current_order <= 0 or not current_label:
            return
        rows.append(
            AuthorityLayerStageSurfaceRow(
                order=current_order,
                stage_label=current_label,
                body_lines=tuple(line for line in current_body_lines if line),
            )
        )
        current_order = 0
        current_label = ""
        current_body_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped == AUTHORITY_LAYERING_SECTION_MARKER:
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
    elif any(not row.body_lines for row in rows):
        violations.append("stage_body_missing")

    return AuthorityLayerStageSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
