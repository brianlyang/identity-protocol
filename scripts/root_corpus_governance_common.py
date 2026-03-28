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
ROOT_CORPUS_REGISTRY_CURRENT = "identity/protocol/mappings/root-corpus-registry.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
ROOT_INDEX_CLASS_SECTION_MARKER = "## What belongs at protocol root"
ROOT_MAINTENANCE_GUARDRAILS_SECTION_MARKER = "## Root maintenance guardrails"
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


@dataclass(frozen=True)
class ForbiddenContentClass:
    class_id: str
    description: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class RootCorpusEntry:
    rel_path: str
    entry_kind: str
    corpus_class: str
    law_bearing: bool
    required_markers: tuple[str, ...] = field(default_factory=tuple)
    required_children: tuple[str, ...] = field(default_factory=tuple)
    forbidden_content_classes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CorpusClassProfile:
    corpus_class: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)
    forbidden_content_classes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootIndexClassProjection:
    order: int
    projection_label: str
    bound_corpus_classes: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootIndexClassProjectionSurfaceRow:
    order: int
    projection_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootIndexClassProjectionSurface:
    rel_path: str
    rows: tuple[RootIndexClassProjectionSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class RootMaintenanceGuardrail:
    order: int
    guardrail_label: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootMaintenanceGuardrailSurfaceRow:
    order: int
    guardrail_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootMaintenanceGuardrailSurface:
    rel_path: str
    rows: tuple[RootMaintenanceGuardrailSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class ForbiddenHit:
    class_id: str
    pattern: str
    line_no: int
    line_excerpt: str


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _as_path_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (_norm_path(item) for item in value) if token)


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def _iter_forbidden_class_rows(registry_doc: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = registry_doc.get("forbidden_content_classes")
    return raw if isinstance(raw, list) else []


def _iter_corpus_class_profile_rows(registry_doc: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = registry_doc.get("corpus_class_profiles")
    return raw if isinstance(raw, list) else []


def _iter_root_index_class_projection_rows(registry_doc: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = registry_doc.get("root_index_class_projections")
    return raw if isinstance(raw, list) else []


def _iter_root_maintenance_guardrail_rows(registry_doc: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = registry_doc.get("root_maintenance_guardrails")
    return raw if isinstance(raw, list) else []


def load_root_corpus_registry(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_REGISTRY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_REGISTRY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_registry_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def forbidden_classes_from_registry(registry_doc: Mapping[str, Any]) -> dict[str, ForbiddenContentClass]:
    classes: dict[str, ForbiddenContentClass] = {}
    for row in _iter_forbidden_class_rows(registry_doc):
        if not isinstance(row, dict):
            continue
        class_id = _norm_path(row.get("class_id"))
        if not class_id:
            continue
        description = str(row.get("description") or "").strip()
        patterns = _as_str_tuple(row.get("patterns"))
        classes[class_id] = ForbiddenContentClass(
            class_id=class_id,
            description=description,
            patterns=patterns,
        )
    return classes


def corpus_class_profiles_from_registry(registry_doc: Mapping[str, Any]) -> dict[str, CorpusClassProfile]:
    profiles: dict[str, CorpusClassProfile] = {}
    for row in _iter_corpus_class_profile_rows(registry_doc):
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_path(row.get("corpus_class"))
        if not corpus_class:
            continue
        profiles[corpus_class] = CorpusClassProfile(
            corpus_class=corpus_class,
            required_markers=_as_str_tuple(row.get("required_markers")),
            forbidden_content_classes=_as_str_tuple(row.get("forbidden_content_classes")),
        )
    return profiles


def root_index_class_projections_from_registry(
    registry_doc: Mapping[str, Any],
) -> tuple[RootIndexClassProjection, ...]:
    projections: list[RootIndexClassProjection] = []
    for row in _iter_root_index_class_projection_rows(registry_doc):
        if not isinstance(row, dict):
            continue
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        projection_label = str(row.get("projection_label") or "").strip()
        if order <= 0 or not projection_label:
            continue
        projections.append(
            RootIndexClassProjection(
                order=order,
                projection_label=projection_label,
                bound_corpus_classes=_as_str_tuple(row.get("bound_corpus_classes")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(projections)


def root_maintenance_guardrails_from_registry(
    registry_doc: Mapping[str, Any],
) -> tuple[RootMaintenanceGuardrail, ...]:
    guardrails: list[RootMaintenanceGuardrail] = []
    for row in _iter_root_maintenance_guardrail_rows(registry_doc):
        if not isinstance(row, dict):
            continue
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        guardrail_label = str(row.get("guardrail_label") or "").strip()
        if order <= 0 or not guardrail_label:
            continue
        guardrails.append(
            RootMaintenanceGuardrail(
                order=order,
                guardrail_label=guardrail_label,
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(guardrails)


def root_corpus_entries_from_registry(registry_doc: Mapping[str, Any]) -> tuple[RootCorpusEntry, ...]:
    rows = registry_doc.get("registered_top_level_entries")
    if not isinstance(rows, list):
        return ()
    entries: list[RootCorpusEntry] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_path(row.get("rel_path"))
        entry_kind = _norm_path(row.get("entry_kind"))
        corpus_class = _norm_path(row.get("corpus_class"))
        if not rel_path or not entry_kind or not corpus_class:
            continue
        entries.append(
            RootCorpusEntry(
                rel_path=rel_path,
                entry_kind=entry_kind,
                corpus_class=corpus_class,
                law_bearing=bool(row.get("law_bearing", False)),
                required_markers=_as_str_tuple(row.get("required_markers")),
                required_children=_as_path_tuple(row.get("required_children")),
                forbidden_content_classes=_as_str_tuple(row.get("forbidden_content_classes")),
            )
        )
    return tuple(entries)


def merge_required_markers(
    entry: RootCorpusEntry,
    *,
    class_profiles: Mapping[str, CorpusClassProfile],
) -> tuple[str, ...]:
    profile = class_profiles.get(entry.corpus_class)
    merged: list[str] = []
    for marker in ((profile.required_markers if profile else ()) + entry.required_markers):
        if marker and marker not in merged:
            merged.append(marker)
    return tuple(merged)


def merge_forbidden_content_classes(
    entry: RootCorpusEntry,
    *,
    class_profiles: Mapping[str, CorpusClassProfile],
) -> tuple[str, ...]:
    profile = class_profiles.get(entry.corpus_class)
    merged: list[str] = []
    for class_id in ((profile.forbidden_content_classes if profile else ()) + entry.forbidden_content_classes):
        if class_id and class_id not in merged:
            merged.append(class_id)
    return tuple(merged)


def collect_protocol_root_top_level_entries(repo_root: Path, root_dir_rel: str) -> list[str]:
    root_dir = (repo_root / _norm_path(root_dir_rel)).resolve()
    if not root_dir.exists() or not root_dir.is_dir():
        return []
    entries: list[str] = []
    for child in sorted(root_dir.iterdir(), key=lambda item: item.name):
        if child.name.startswith("."):
            continue
        entries.append(_norm_path(str(Path(root_dir_rel) / child.name)))
    return entries


@dataclass(frozen=True)
class _OrderedBoldSurfaceRow:
    order: int
    label: str
    body_lines: tuple[str, ...]


@dataclass(frozen=True)
class _OrderedBoldSurface:
    rel_path: str
    rows: tuple[_OrderedBoldSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


def _readme_ordered_bold_surface(
    repo_root: Path,
    *,
    section_marker: str,
    missing_rows_reason: str,
    missing_body_reason: str,
) -> _OrderedBoldSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return _OrderedBoldSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[RootIndexClassProjectionSurfaceRow] = []
    current_order = 0
    current_label = ""
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_order, current_label, current_body_lines
        if current_order <= 0 or not current_label:
            return
        rows.append(
            _OrderedBoldSurfaceRow(
                order=current_order,
                label=current_label,
                body_lines=tuple(line for line in current_body_lines if line),
            )
        )
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
        violations.append(missing_rows_reason)
    elif any(not row.body_lines for row in rows):
        violations.append(missing_body_reason)

    return _OrderedBoldSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )


def readme_root_index_class_projection_surface(repo_root: Path) -> RootIndexClassProjectionSurface:
    surface = _readme_ordered_bold_surface(
        repo_root,
        section_marker=ROOT_INDEX_CLASS_SECTION_MARKER,
        missing_rows_reason="projection_rows_missing",
        missing_body_reason="projection_body_missing",
    )
    return RootIndexClassProjectionSurface(
        rel_path=surface.rel_path,
        rows=tuple(
            RootIndexClassProjectionSurfaceRow(
                order=row.order,
                projection_label=row.label,
                body_lines=row.body_lines,
            )
            for row in surface.rows
        ),
        extraction_violations=surface.extraction_violations,
    )


def readme_root_maintenance_guardrail_surface(repo_root: Path) -> RootMaintenanceGuardrailSurface:
    surface = _readme_ordered_bold_surface(
        repo_root,
        section_marker=ROOT_MAINTENANCE_GUARDRAILS_SECTION_MARKER,
        missing_rows_reason="guardrail_rows_missing",
        missing_body_reason="guardrail_body_missing",
    )
    return RootMaintenanceGuardrailSurface(
        rel_path=surface.rel_path,
        rows=tuple(
            RootMaintenanceGuardrailSurfaceRow(
                order=row.order,
                guardrail_label=row.label,
                body_lines=row.body_lines,
            )
            for row in surface.rows
        ),
        extraction_violations=surface.extraction_violations,
    )


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold()


def find_missing_markers(text: str, required_markers: tuple[str, ...]) -> list[str]:
    normalized_text = _normalize_whitespace(text)
    missing: list[str] = []
    for marker in required_markers:
        if _normalize_whitespace(marker) not in normalized_text:
            missing.append(marker)
    return missing


def scan_forbidden_content(
    text: str,
    *,
    content_classes: Mapping[str, ForbiddenContentClass],
    class_ids: tuple[str, ...],
) -> list[ForbiddenHit]:
    hits: list[ForbiddenHit] = []
    for class_id in class_ids:
        content_class = content_classes.get(class_id)
        if content_class is None:
            continue
        for pattern in content_class.patterns:
            compiled = re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE)
            match = compiled.search(text)
            if not match:
                continue
            start = match.start()
            line_no = text.count("\n", 0, start) + 1
            line = text.splitlines()[line_no - 1] if text.splitlines() else ""
            hits.append(
                ForbiddenHit(
                    class_id=class_id,
                    pattern=pattern,
                    line_no=line_no,
                    line_excerpt=line.strip(),
                )
            )
            break
    return hits
