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
ROOT_CORPUS_TRANSITION_CURRENT = "identity/protocol/mappings/root-corpus-transition.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
TRANSITION_COMPLETENESS_SECTION_MARKER = "## Root transition completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


TransitionAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class TransitionSurfaceProfile:
    surface_class: str
    surface_scope: str
    law_bearing: bool
    transition_mode: str
    direct_root_targets: tuple[str, ...] = field(default_factory=tuple)
    direct_current_turn_legality_allowed: bool = False
    strengthening_gateways: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TransitionCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class TransitionCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class TransitionCompletenessSurface:
    rel_path: str
    rows: tuple[TransitionCompletenessSurfaceRow, ...]
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


def load_root_corpus_transition(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_TRANSITION_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_TRANSITION_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_transition_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def transition_anchor_checks_from_doc(transition_doc: Mapping[str, Any]) -> tuple[TransitionAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        transition_doc,
        field_name="transition_anchor_checks",
        require_markers=False,
    )


def transition_surface_profiles_from_doc(transition_doc: Mapping[str, Any]) -> tuple[TransitionSurfaceProfile, ...]:
    rows = transition_doc.get("surface_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[TransitionSurfaceProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        surface_class = _norm_str(row.get("surface_class"))
        surface_scope = _norm_str(row.get("surface_scope"))
        transition_mode = _norm_str(row.get("transition_mode"))
        if not surface_class or not surface_scope or not transition_mode:
            continue
        out.append(
            TransitionSurfaceProfile(
                surface_class=surface_class,
                surface_scope=surface_scope,
                law_bearing=bool(row.get("law_bearing", False)),
                transition_mode=transition_mode,
                direct_root_targets=_as_str_tuple(row.get("direct_root_targets")),
                direct_current_turn_legality_allowed=bool(row.get("direct_current_turn_legality_allowed", False)),
                strengthening_gateways=_as_str_tuple(row.get("strengthening_gateways")),
            )
        )
    return tuple(out)


def transition_completeness_rows_from_doc(
    transition_doc: Mapping[str, Any],
) -> tuple[TransitionCompletenessRow, ...]:
    rows = transition_doc.get("transition_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[TransitionCompletenessRow] = []
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
            TransitionCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_transition_completeness_surface(repo_root: Path) -> TransitionCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return TransitionCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[TransitionCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == TRANSITION_COMPLETENESS_SECTION_MARKER:
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
            TransitionCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return TransitionCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
