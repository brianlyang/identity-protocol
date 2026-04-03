#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from repo_root_resolution_common import resolve_protocol_repo_root

ROOT_PROTOCOL_DIR = "identity/protocol"
README_REL_PATH = f"{ROOT_PROTOCOL_DIR}/README.md"
IDENTITY_PROTOCOL_REL_PATH = f"{ROOT_PROTOCOL_DIR}/IDENTITY_PROTOCOL.md"
README_ROOT_CONTRACT_INDEX_SURFACE_ID = "readme_root_contract_index"
PROTOCOL_BOUNDARY_ROOT_CONTRACT_INDEX_SURFACE_ID = "protocol_boundary_root_contract_index"
PROTOCOL_BOUNDARY_ROOT_CONTRACT_PROJECTION_SURFACE_ID = "protocol_boundary_root_contract_projection_surface"
ROOT_CONTRACT_ENTRY_ROLE = "root_contract_entry"
README_ROOT_CONTRACT_SECTION_MARKER = "4. **root contract files**"
PROTOCOL_BOUNDARY_SECTION_MARKER = "## Foundational design philosophy boundary"
BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")
ORDERED_ITEM_RE = re.compile(r"^\d+\.\s+\*\*")
HEADING_RE = re.compile(r"^##\s+")
PROTOCOL_BOUNDARY_DESCRIPTOR_RE = re.compile(
    r"^(?P<boundary_order>\d+)\.\s+(?P<descriptor>.*?)\s+is frozen separately in\s+"
)


@dataclass(frozen=True)
class ManualRootContractIndexRow:
    order: int
    rel_path: str


@dataclass(frozen=True)
class ManualRootContractIndexSurface:
    surface_id: str
    rel_path: str
    rows: tuple[ManualRootContractIndexRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class ManualRootContractProjectionRow:
    order: int
    rel_path: str
    projection_label: str
    boundary_order: int = 0


@dataclass(frozen=True)
class ManualRootContractProjectionSurface:
    surface_id: str
    rel_path: str
    rows: tuple[ManualRootContractProjectionRow, ...]
    extraction_violations: tuple[str, ...]


def _normalize_rel_path(token: str) -> str:
    normalized = str(token or "").strip().strip("`").replace("\\", "/")
    if not normalized:
        return ""
    if normalized.startswith(f"{ROOT_PROTOCOL_DIR}/"):
        return normalized if normalized.endswith(".md") else ""
    if "/" not in normalized and normalized.endswith(".md"):
        return f"{ROOT_PROTOCOL_DIR}/{normalized}"
    return ""


def _build_rows(rel_paths: list[str]) -> tuple[ManualRootContractIndexRow, ...]:
    return tuple(
        ManualRootContractIndexRow(order=index, rel_path=rel_path)
        for index, rel_path in enumerate(rel_paths, start=1)
        if rel_path
    )


def _build_projection_rows(
    projection_items: list[tuple[int, str, str]],
) -> tuple[ManualRootContractProjectionRow, ...]:
    return tuple(
        ManualRootContractProjectionRow(
            order=index,
            rel_path=rel_path,
            projection_label=projection_label,
            boundary_order=boundary_order,
        )
        for index, (boundary_order, projection_label, rel_path) in enumerate(projection_items, start=1)
        if rel_path
    )


def _read_lines(repo_root: Path, rel_path: str) -> tuple[list[str], tuple[str, ...]]:
    path = (repo_root / rel_path).resolve()
    if not path.exists() or not path.is_file():
        return [], ("target_missing",)
    return path.read_text(encoding="utf-8", errors="ignore").splitlines(), ()


def canonical_root_contract_rel_paths(reading_rows) -> tuple[str, ...]:
    return tuple(
        row.rel_path
        for row in sorted(reading_rows, key=lambda item: item.order)
        if getattr(row, "entry_role", "") == ROOT_CONTRACT_ENTRY_ROLE
    )


def _protocol_boundary_projection_items(lines: list[str]) -> list[tuple[int, str, str]]:
    section_found = False
    items: list[tuple[int, str, str]] = []
    for line in lines:
        stripped = line.strip()
        if stripped == PROTOCOL_BOUNDARY_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if HEADING_RE.match(stripped):
            break
        if "frozen separately in" not in line:
            continue
        tokens = BACKTICK_TOKEN_RE.findall(line)
        if not tokens:
            continue
        normalized = _normalize_rel_path(tokens[0])
        if not normalized:
            continue
        descriptor_match = PROTOCOL_BOUNDARY_DESCRIPTOR_RE.match(stripped)
        boundary_order = int(descriptor_match.group("boundary_order")) if descriptor_match else 0
        descriptor = descriptor_match.group("descriptor").strip() if descriptor_match else ""
        items.append((boundary_order, descriptor, normalized))
    return items


def manual_root_contract_projection_sentence(row: ManualRootContractProjectionRow) -> str:
    prefix_order = int(row.boundary_order or row.order)
    return f"{prefix_order}. {row.projection_label} is frozen separately in `{row.rel_path}`."


def readme_root_contract_index_surface(repo_root: Path) -> ManualRootContractIndexSurface:
    lines, read_errors = _read_lines(repo_root, README_REL_PATH)
    if read_errors:
        return ManualRootContractIndexSurface(
            surface_id=README_ROOT_CONTRACT_INDEX_SURFACE_ID,
            rel_path=README_REL_PATH,
            rows=(),
            extraction_violations=read_errors,
        )

    section_found = False
    rel_paths: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == README_ROOT_CONTRACT_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if ORDERED_ITEM_RE.match(stripped):
            break
        rel_paths.extend(
            normalized
            for normalized in (_normalize_rel_path(token) for token in BACKTICK_TOKEN_RE.findall(line))
            if normalized
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rel_paths:
        violations.append("contract_list_missing")

    return ManualRootContractIndexSurface(
        surface_id=README_ROOT_CONTRACT_INDEX_SURFACE_ID,
        rel_path=README_REL_PATH,
        rows=_build_rows(rel_paths),
        extraction_violations=tuple(violations),
    )


def protocol_boundary_root_contract_index_surface(repo_root: Path) -> ManualRootContractIndexSurface:
    lines, read_errors = _read_lines(repo_root, IDENTITY_PROTOCOL_REL_PATH)
    if read_errors:
        return ManualRootContractIndexSurface(
            surface_id=PROTOCOL_BOUNDARY_ROOT_CONTRACT_INDEX_SURFACE_ID,
            rel_path=IDENTITY_PROTOCOL_REL_PATH,
            rows=(),
            extraction_violations=read_errors,
        )

    section_found = any(line.strip() == PROTOCOL_BOUNDARY_SECTION_MARKER for line in lines)
    rel_paths = [rel_path for _boundary_order, _descriptor, rel_path in _protocol_boundary_projection_items(lines)]

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rel_paths:
        violations.append("contract_list_missing")

    return ManualRootContractIndexSurface(
        surface_id=PROTOCOL_BOUNDARY_ROOT_CONTRACT_INDEX_SURFACE_ID,
        rel_path=IDENTITY_PROTOCOL_REL_PATH,
        rows=_build_rows(rel_paths),
        extraction_violations=tuple(violations),
    )


def protocol_boundary_root_contract_projection_surface(repo_root: Path) -> ManualRootContractProjectionSurface:
    lines, read_errors = _read_lines(repo_root, IDENTITY_PROTOCOL_REL_PATH)
    if read_errors:
        return ManualRootContractProjectionSurface(
            surface_id=PROTOCOL_BOUNDARY_ROOT_CONTRACT_PROJECTION_SURFACE_ID,
            rel_path=IDENTITY_PROTOCOL_REL_PATH,
            rows=(),
            extraction_violations=read_errors,
        )

    section_found = any(line.strip() == PROTOCOL_BOUNDARY_SECTION_MARKER for line in lines)
    projection_items = _protocol_boundary_projection_items(lines)

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not projection_items:
        violations.append("projection_list_missing")
    elif any(not descriptor for _boundary_order, descriptor, _rel_path in projection_items):
        violations.append("projection_label_missing")

    return ManualRootContractProjectionSurface(
        surface_id=PROTOCOL_BOUNDARY_ROOT_CONTRACT_PROJECTION_SURFACE_ID,
        rel_path=IDENTITY_PROTOCOL_REL_PATH,
        rows=_build_projection_rows(projection_items),
        extraction_violations=tuple(violations),
    )


def current_protocol_boundary_root_contract_projection_probe_target() -> dict[str, str]:
    repo_root = resolve_protocol_repo_root("", start=__file__)
    surface = protocol_boundary_root_contract_projection_surface(repo_root)
    if not surface.rows:
        return {
            "rel_path": "",
            "projection_label": "",
            "sentence": "",
            "drifted_projection_label": "",
            "drifted_sentence": "",
        }
    target = surface.rows[-1]
    drifted_projection_label = f"{target.projection_label} [probe drift]"
    drifted_sentence = manual_root_contract_projection_sentence(
        ManualRootContractProjectionRow(
            order=target.order,
            rel_path=target.rel_path,
            projection_label=drifted_projection_label,
            boundary_order=target.boundary_order,
        )
    )
    return {
        "rel_path": target.rel_path,
        "projection_label": target.projection_label,
        "sentence": manual_root_contract_projection_sentence(target),
        "drifted_projection_label": drifted_projection_label,
        "drifted_sentence": drifted_sentence,
    }


def manual_root_contract_index_surfaces(repo_root: Path) -> tuple[ManualRootContractIndexSurface, ...]:
    return (
        readme_root_contract_index_surface(repo_root),
        protocol_boundary_root_contract_index_surface(repo_root),
    )
