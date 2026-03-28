#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import RootDocAnchorCheck, root_doc_anchor_checks_from_doc

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_PRECEDENCE_CURRENT = "identity/protocol/mappings/root-corpus-precedence.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
CONFLICT_HANDLING_RULE_SECTION_MARKER = "## Conflict-handling rule"
CONFLICT_PRECEDENCE_COMPLETENESS_SECTION_MARKER = "## Root conflict-precedence completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


PrecedenceAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class PrecedenceProfile:
    conflict_class: str
    conflict_scope: str
    resolution_mode: str
    semantic_precedence_chain: tuple[str, ...] = field(default_factory=tuple)
    terminal_machine_surfaces: tuple[str, ...] = field(default_factory=tuple)
    motivating_only_surface_classes: tuple[str, ...] = field(default_factory=tuple)
    forbidden_override_surface_classes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GatewayAuthorshipProjection:
    gateway_class: str
    preserved_effect_target_class: str
    preserved_question_class: str
    preserved_answer_mode: str


@dataclass(frozen=True)
class ConflictHandlingRule:
    order: int
    rule_text: str


@dataclass(frozen=True)
class ConflictHandlingRuleSurfaceRow:
    order: int
    rule_text: str


@dataclass(frozen=True)
class ConflictHandlingRuleSurface:
    rel_path: str
    rows: tuple[ConflictHandlingRuleSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class ConflictPrecedenceCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class ConflictPrecedenceCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class ConflictPrecedenceCompletenessSurface:
    rel_path: str
    rows: tuple[ConflictPrecedenceCompletenessSurfaceRow, ...]
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


def load_root_corpus_precedence(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_PRECEDENCE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_PRECEDENCE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_precedence_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def precedence_anchor_checks_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[PrecedenceAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        precedence_doc,
        field_name="precedence_anchor_checks",
        require_markers=False,
    )


def precedence_profiles_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[PrecedenceProfile, ...]:
    rows = precedence_doc.get("precedence_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[PrecedenceProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        conflict_class = _norm_str(row.get("conflict_class"))
        conflict_scope = _norm_str(row.get("conflict_scope"))
        resolution_mode = _norm_str(row.get("resolution_mode"))
        if not conflict_class or not conflict_scope or not resolution_mode:
            continue
        out.append(
            PrecedenceProfile(
                conflict_class=conflict_class,
                conflict_scope=conflict_scope,
                resolution_mode=resolution_mode,
                semantic_precedence_chain=_as_str_tuple(row.get("semantic_precedence_chain")),
                terminal_machine_surfaces=_as_str_tuple(row.get("terminal_machine_surfaces")),
                motivating_only_surface_classes=_as_str_tuple(row.get("motivating_only_surface_classes")),
                forbidden_override_surface_classes=_as_str_tuple(row.get("forbidden_override_surface_classes")),
            )
        )
    return tuple(out)


def gateway_authorship_projections_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[GatewayAuthorshipProjection, ...]:
    rows = precedence_doc.get("gateway_authorship_projection")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayAuthorshipProjection] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gateway_class = _norm_str(row.get("gateway_class"))
        preserved_effect_target_class = _norm_str(row.get("preserved_effect_target_class"))
        preserved_question_class = _norm_str(row.get("preserved_question_class"))
        preserved_answer_mode = _norm_str(row.get("preserved_answer_mode"))
        if not gateway_class or not preserved_effect_target_class or not preserved_question_class or not preserved_answer_mode:
            continue
        out.append(
            GatewayAuthorshipProjection(
                gateway_class=gateway_class,
                preserved_effect_target_class=preserved_effect_target_class,
                preserved_question_class=preserved_question_class,
                preserved_answer_mode=preserved_answer_mode,
            )
        )
    return tuple(out)


def conflict_handling_rules_from_doc(precedence_doc: Mapping[str, Any]) -> tuple[ConflictHandlingRule, ...]:
    rows = precedence_doc.get("conflict_handling_rules")
    if not isinstance(rows, list):
        return ()
    out: list[ConflictHandlingRule] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        rule_text = str(row.get("rule_text") or "").strip()
        if order <= 0 or not rule_text:
            continue
        out.append(
            ConflictHandlingRule(
                order=order,
                rule_text=rule_text,
            )
        )
    return tuple(out)


def conflict_precedence_completeness_rows_from_doc(
    precedence_doc: Mapping[str, Any],
) -> tuple[ConflictPrecedenceCompletenessRow, ...]:
    rows = precedence_doc.get("conflict_precedence_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[ConflictPrecedenceCompletenessRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        completeness_id = _norm_str(row.get("completeness_id"))
        contract_phrase = str(row.get("contract_phrase") or "").strip()
        if order <= 0 or not completeness_id or not contract_phrase:
            continue
        out.append(
            ConflictPrecedenceCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_conflict_handling_rule_surface(repo_root: Path) -> ConflictHandlingRuleSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return ConflictHandlingRuleSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[ConflictHandlingRuleSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == CONFLICT_HANDLING_RULE_SECTION_MARKER:
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
            ConflictHandlingRuleSurfaceRow(
                order=int(match.group(1)),
                rule_text=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("rule_rows_missing")

    return ConflictHandlingRuleSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )


def readme_conflict_precedence_completeness_surface(repo_root: Path) -> ConflictPrecedenceCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return ConflictPrecedenceCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[ConflictPrecedenceCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == CONFLICT_PRECEDENCE_COMPLETENESS_SECTION_MARKER:
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
            ConflictPrecedenceCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("completeness_rows_missing")

    return ConflictPrecedenceCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
