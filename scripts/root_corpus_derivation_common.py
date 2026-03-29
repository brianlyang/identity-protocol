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
ROOT_CORPUS_DERIVATION_CURRENT = "identity/protocol/mappings/root-corpus-derivation.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
DERIVATION_COMPLETENESS_SECTION_MARKER = "## Root derivation completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


DerivationAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class DerivationClassProfile:
    corpus_class: str
    derivation_mode: str
    allowed_upstream_classes: tuple[str, ...] = field(default_factory=tuple)
    law_bearing_required: bool = False


@dataclass(frozen=True)
class DerivationCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class DerivationCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class DerivationCompletenessSurface:
    rel_path: str
    rows: tuple[DerivationCompletenessSurfaceRow, ...]
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


def load_root_corpus_derivation(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_DERIVATION_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_DERIVATION_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_derivation_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def derivation_anchor_checks_from_doc(derivation_doc: Mapping[str, Any]) -> tuple[DerivationAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        derivation_doc,
        field_name="derivation_anchor_checks",
        require_markers=False,
    )


def derivation_class_profiles_from_doc(derivation_doc: Mapping[str, Any]) -> tuple[DerivationClassProfile, ...]:
    rows = derivation_doc.get("derivation_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[DerivationClassProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        derivation_mode = _norm_str(row.get("derivation_mode"))
        if not corpus_class or not derivation_mode:
            continue
        out.append(
            DerivationClassProfile(
                corpus_class=corpus_class,
                derivation_mode=derivation_mode,
                allowed_upstream_classes=_as_str_tuple(row.get("allowed_upstream_classes")),
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)


def derivation_completeness_rows_from_doc(
    derivation_doc: Mapping[str, Any],
) -> tuple[DerivationCompletenessRow, ...]:
    rows = derivation_doc.get("derivation_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[DerivationCompletenessRow] = []
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
            DerivationCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_derivation_completeness_surface(repo_root: Path) -> DerivationCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return DerivationCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[DerivationCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == DERIVATION_COMPLETENESS_SECTION_MARKER:
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
            DerivationCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return DerivationCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
