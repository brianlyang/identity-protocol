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
ROOT_CONSTITUTIONAL_SPINE_CURRENT = "identity/protocol/mappings/root-constitutional-spine.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
WHY_PHILOSOPHY_COMES_FIRST_SECTION_MARKER = "## Why philosophy comes first"
CONSTITUTIONAL_SPINE_COMPLETENESS_SECTION_MARKER = "## Root constitutional-spine completeness discipline"
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class ConstitutionalEntryRow:
    order: int
    rel_path: str
    corpus_class: str
    reading_order: int
    entry_role: str
    authority_role: str
    authority_mode: str
    question_classes: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BridgeRow:
    order: int
    bridge_id: str
    source_rel_path: str
    source_markers: tuple[str, ...] = field(default_factory=tuple)
    target_rel_path: str = ""
    target_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PhilosophyPrimacyRow:
    order: int
    primacy_label: str
    bound_entry_paths: tuple[str, ...] = field(default_factory=tuple)
    bound_bridge_ids: tuple[str, ...] = field(default_factory=tuple)
    bound_reading_roles: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PhilosophyPrimacySurfaceRow:
    order: int
    primacy_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PhilosophyPrimacySurface:
    rel_path: str
    rows: tuple[PhilosophyPrimacySurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class ConstitutionalSpineCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class ConstitutionalSpineCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class ConstitutionalSpineCompletenessSurface:
    rel_path: str
    rows: tuple[ConstitutionalSpineCompletenessSurfaceRow, ...]
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


def load_root_constitutional_spine(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CONSTITUTIONAL_SPINE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CONSTITUTIONAL_SPINE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_constitutional_spine_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def constitutional_entry_rows_from_doc(doc: Mapping[str, Any]) -> tuple[ConstitutionalEntryRow, ...]:
    rows = doc.get("required_constitutional_entry_rows")
    if not isinstance(rows, list):
        return ()
    out: list[ConstitutionalEntryRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        corpus_class = _norm_str(row.get("corpus_class"))
        entry_role = _norm_str(row.get("entry_role"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        try:
            order = int(row.get("order"))
            reading_order = int(row.get("reading_order"))
        except Exception:
            continue
        question_classes = _as_str_tuple(row.get("question_classes"))
        required_markers = _as_str_tuple(row.get("required_markers"))
        if (
            order <= 0
            or reading_order <= 0
            or not rel_path
            or not corpus_class
            or not entry_role
            or not authority_role
            or not authority_mode
        ):
            continue
        out.append(
            ConstitutionalEntryRow(
                order=order,
                rel_path=rel_path,
                corpus_class=corpus_class,
                reading_order=reading_order,
                entry_role=entry_role,
                authority_role=authority_role,
                authority_mode=authority_mode,
                question_classes=question_classes,
                required_markers=required_markers,
            )
        )
    return tuple(out)


def bridge_rows_from_doc(doc: Mapping[str, Any]) -> tuple[BridgeRow, ...]:
    rows = doc.get("required_spine_bridge_rows")
    if not isinstance(rows, list):
        return ()
    out: list[BridgeRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        bridge_id = _norm_str(row.get("bridge_id"))
        source_rel_path = _norm_str(row.get("source_rel_path"))
        target_rel_path = _norm_str(row.get("target_rel_path"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        source_markers = _as_str_tuple(row.get("source_markers"))
        target_markers = _as_str_tuple(row.get("target_markers"))
        if order <= 0 or not bridge_id or not source_rel_path or not target_rel_path:
            continue
        out.append(
            BridgeRow(
                order=order,
                bridge_id=bridge_id,
                source_rel_path=source_rel_path,
                source_markers=source_markers,
                target_rel_path=target_rel_path,
                target_markers=target_markers,
            )
        )
    return tuple(out)


def philosophy_primacy_rows_from_doc(doc: Mapping[str, Any]) -> tuple[PhilosophyPrimacyRow, ...]:
    rows = doc.get("philosophy_primacy_rows")
    if not isinstance(rows, list):
        return ()
    out: list[PhilosophyPrimacyRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        primacy_label = _norm_str(row.get("primacy_label"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not primacy_label:
            continue
        out.append(
            PhilosophyPrimacyRow(
                order=order,
                primacy_label=primacy_label,
                bound_entry_paths=_as_str_tuple(row.get("bound_entry_paths")),
                bound_bridge_ids=_as_str_tuple(row.get("bound_bridge_ids")),
                bound_reading_roles=_as_str_tuple(row.get("bound_reading_roles")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def constitutional_spine_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[ConstitutionalSpineCompletenessRow, ...]:
    rows = doc.get("constitutional_spine_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[ConstitutionalSpineCompletenessRow] = []
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
            ConstitutionalSpineCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
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


def readme_philosophy_primacy_surface(repo_root: Path) -> PhilosophyPrimacySurface:
    rows_data, violations = _readme_ordered_bold_section_rows(
        repo_root,
        section_marker=WHY_PHILOSOPHY_COMES_FIRST_SECTION_MARKER,
    )
    return PhilosophyPrimacySurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(
            PhilosophyPrimacySurfaceRow(
                order=order,
                primacy_label=primacy_label,
                body_lines=body_lines,
            )
            for order, primacy_label, body_lines in rows_data
        ),
        extraction_violations=violations,
    )


def readme_constitutional_spine_completeness_surface(
    repo_root: Path,
) -> ConstitutionalSpineCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return ConstitutionalSpineCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[ConstitutionalSpineCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == CONSTITUTIONAL_SPINE_COMPLETENESS_SECTION_MARKER:
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
            ConstitutionalSpineCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return ConstitutionalSpineCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
