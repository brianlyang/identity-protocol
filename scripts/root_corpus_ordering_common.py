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
ORDER_PLANE_SECTION_MARKER = "## Source-order, reading-order, and adjudication-order"
ORDERING_COMPLETENESS_SECTION_MARKER = "## Root ordering completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
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
class OrderPlaneStage:
    order: int
    stage_label: str
    bound_row_families: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OrderPlaneStageSurfaceRow:
    order: int
    stage_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OrderPlaneStageSurface:
    rel_path: str
    rows: tuple[OrderPlaneStageSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class OrderingCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class OrderingCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class OrderingCompletenessSurface:
    rel_path: str
    rows: tuple[OrderingCompletenessSurfaceRow, ...]
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


def order_plane_stages_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[OrderPlaneStage, ...]:
    rows = ordering_doc.get("order_plane_stages")
    if not isinstance(rows, list):
        return ()
    out: list[OrderPlaneStage] = []
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
            OrderPlaneStage(
                order=order,
                stage_label=stage_label,
                bound_row_families=_as_str_tuple(row.get("bound_row_families")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def ordering_completeness_rows_from_doc(ordering_doc: Mapping[str, Any]) -> tuple[OrderingCompletenessRow, ...]:
    rows = ordering_doc.get("ordering_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[OrderingCompletenessRow] = []
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
            OrderingCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
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


def _extract_readme_ordered_bold_surface(
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
    elif any(not body_lines for _order, _label, body_lines in rows):
        violations.append("stage_body_missing")

    return tuple(rows), tuple(violations)


def readme_root_reading_order_surface(repo_root: Path) -> RootReadingOrderStageSurface:
    rows, violations = _extract_readme_ordered_bold_surface(
        repo_root,
        section_marker=ROOT_READING_ORDER_SECTION_MARKER,
    )
    return RootReadingOrderStageSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(
            RootReadingOrderStageSurfaceRow(order=order, stage_label=stage_label, body_lines=body_lines)
            for order, stage_label, body_lines in rows
        ),
        extraction_violations=violations,
    )


def readme_order_plane_surface(repo_root: Path) -> OrderPlaneStageSurface:
    rows, violations = _extract_readme_ordered_bold_surface(
        repo_root,
        section_marker=ORDER_PLANE_SECTION_MARKER,
    )
    return OrderPlaneStageSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(
            OrderPlaneStageSurfaceRow(order=order, stage_label=stage_label, body_lines=body_lines)
            for order, stage_label, body_lines in rows
        ),
        extraction_violations=violations,
    )


def readme_ordering_completeness_surface(repo_root: Path) -> OrderingCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return OrderingCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[OrderingCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == ORDERING_COMPLETENESS_SECTION_MARKER:
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
            OrderingCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("completeness_rows_missing")

    return OrderingCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
