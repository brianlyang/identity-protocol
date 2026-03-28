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
ROOT_CORPUS_ORDERING_CURRENT = "identity/protocol/mappings/root-corpus-ordering.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
ROOT_READING_ORDER_SECTION_MARKER = "## Root reading order"
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class SourceOrderRow:
    order: int
    corpus_class: str
    source_role: str
    law_bearing_required: bool


@dataclass(frozen=True)
class ReadingOrderRow:
    order: int
    rel_path: str
    entry_role: str


@dataclass(frozen=True)
class RootReadingOrderStage:
    order: int
    stage_label: str
    bound_reading_order_rel_paths: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootReadingOrderStageSurfaceRow:
    order: int
    stage_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootReadingOrderStageSurface:
    rel_path: str
    rows: tuple[RootReadingOrderStageSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class ProtocolBoundaryRootContractProjectionRow:
    order: int
    rel_path: str
    projection_label: str


@dataclass(frozen=True)
class AdjudicationOrderRow:
    order: int
    machine_surface: str


OrderingAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class AdjudicationSurfaceProfile:
    machine_surface: str
    phase_order: int
    surface_role: str
    closure_terminal: bool


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def _as_path_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (_norm_str(item) for item in value) if token)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_corpus_ordering(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_ORDERING_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_ORDERING_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_ordering_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def ordering_anchor_checks_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[OrderingAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        ordering_doc,
        field_name="ordering_anchor_checks",
        require_markers=False,
    )


def source_order_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[SourceOrderRow, ...]:
    rows = ordering_doc.get("source_order")
    if not isinstance(rows, list):
        return ()
    out: list[SourceOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        source_role = _norm_str(row.get("source_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not corpus_class or not source_role:
            continue
        out.append(
            SourceOrderRow(
                order=order,
                corpus_class=corpus_class,
                source_role=source_role,
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)


def reading_order_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[ReadingOrderRow, ...]:
    rows = ordering_doc.get("reading_order")
    if not isinstance(rows, list):
        return ()
    out: list[ReadingOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        entry_role = _norm_str(row.get("entry_role"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not rel_path or not entry_role:
            continue
        out.append(
            ReadingOrderRow(
                order=order,
                rel_path=rel_path,
                entry_role=entry_role,
            )
        )
    return tuple(out)


def root_reading_order_stages_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[RootReadingOrderStage, ...]:
    rows = ordering_doc.get("root_reading_order_stages")
    if not isinstance(rows, list):
        return ()
    out: list[RootReadingOrderStage] = []
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
            RootReadingOrderStage(
                order=order,
                stage_label=stage_label,
                bound_reading_order_rel_paths=_as_path_tuple(row.get("bound_reading_order_rel_paths")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def protocol_boundary_root_contract_projection_rows_from_doc(
    ordering_doc: Mapping[str, Any],
) -> tuple[ProtocolBoundaryRootContractProjectionRow, ...]:
    rows = ordering_doc.get("protocol_boundary_root_contract_projections")
    if not isinstance(rows, list):
        return ()
    out: list[ProtocolBoundaryRootContractProjectionRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        projection_label = str(row.get("projection_label") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not rel_path or not projection_label:
            continue
        out.append(
            ProtocolBoundaryRootContractProjectionRow(
                order=order,
                rel_path=rel_path,
                projection_label=projection_label,
            )
        )
    return tuple(out)


def adjudication_order_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[AdjudicationOrderRow, ...]:
    rows = ordering_doc.get("adjudication_order")
    if not isinstance(rows, list):
        return ()
    out: list[AdjudicationOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        machine_surface = _norm_str(row.get("machine_surface"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not machine_surface:
            continue
        out.append(AdjudicationOrderRow(order=order, machine_surface=machine_surface))
    return tuple(out)


def adjudication_surface_profiles_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[AdjudicationSurfaceProfile, ...]:
    rows = ordering_doc.get("adjudication_surface_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[AdjudicationSurfaceProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        machine_surface = _norm_str(row.get("machine_surface"))
        surface_role = _norm_str(row.get("surface_role"))
        try:
            phase_order = int(row.get("phase_order"))
        except Exception:
            continue
        if phase_order <= 0 or not machine_surface or not surface_role:
            continue
        out.append(
            AdjudicationSurfaceProfile(
                machine_surface=machine_surface,
                phase_order=phase_order,
                surface_role=surface_role,
                closure_terminal=bool(row.get("closure_terminal", False)),
            )
        )
    return tuple(out)


def readme_root_reading_order_surface(repo_root: Path) -> RootReadingOrderStageSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return RootReadingOrderStageSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[RootReadingOrderStageSurfaceRow] = []
    current_order = 0
    current_label = ""
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_order, current_label, current_body_lines
        if current_order <= 0 or not current_label:
            return
        rows.append(
            RootReadingOrderStageSurfaceRow(
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
        if stripped == ROOT_READING_ORDER_SECTION_MARKER:
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

    return RootReadingOrderStageSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
