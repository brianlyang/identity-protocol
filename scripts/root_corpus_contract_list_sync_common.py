#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ROOT_PROTOCOL_DIR = "identity/protocol"
README_REL_PATH = f"{ROOT_PROTOCOL_DIR}/README.md"
IDENTITY_PROTOCOL_REL_PATH = f"{ROOT_PROTOCOL_DIR}/IDENTITY_PROTOCOL.md"
README_ROOT_CONTRACT_INDEX_SURFACE_ID = "readme_root_contract_index"
PROTOCOL_BOUNDARY_ROOT_CONTRACT_INDEX_SURFACE_ID = "protocol_boundary_root_contract_index"
ROOT_CONTRACT_ENTRY_ROLE = "root_contract_entry"
README_ROOT_CONTRACT_SECTION_MARKER = "4. **root contract files**"
PROTOCOL_BOUNDARY_SECTION_MARKER = "## Foundational design philosophy boundary"
BACKTICK_TOKEN_RE = re.compile(r"`([^`]+)`")
ORDERED_ITEM_RE = re.compile(r"^\d+\.\s+\*\*")
HEADING_RE = re.compile(r"^##\s+")


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

    section_found = False
    rel_paths: list[str] = []
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
        if normalized:
            rel_paths.append(normalized)

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


def manual_root_contract_index_surfaces(repo_root: Path) -> tuple[ManualRootContractIndexSurface, ...]:
    return (
        readme_root_contract_index_surface(repo_root),
        protocol_boundary_root_contract_index_surface(repo_root),
    )
