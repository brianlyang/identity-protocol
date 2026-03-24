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
