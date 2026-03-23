#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

CONTRACT_BINDING_CURRENT_REF = "identity/protocol/mappings/contract-binding.current.yaml"
SEMANTIC_TERM_REGISTRY_CURRENT_REF = "identity/protocol/mappings/semantic-term-registry.current.yaml"
DEFAULT_ALIAS_REFS = (
    STREAM_DOC_REGISTRY_CURRENT,
    CONTRACT_BINDING_CURRENT_REF,
    SEMANTIC_TERM_REGISTRY_CURRENT_REF,
)


@dataclass(frozen=True)
class VisualAtlasConfig:
    status_key: str
    error_code: str
    canonical_doc: str
    canonical_asset_root: str
    required_svg_files: tuple[str, ...]
    svg_family_pattern: str
    atlas_doc_pattern: str
    atlas_required_markers: tuple[str, ...]
    index_required_markers: tuple[str, ...]
    owner_doc_markers: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    audit_index_doc: str = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
    stream_doc_registry_ref: str = STREAM_DOC_REGISTRY_CURRENT
    alias_refs: tuple[str, ...] = DEFAULT_ALIAS_REFS
    anti_scatter_scope_mode: str = "protocol_repo_internal_only"


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_stream_doc_registry(repo_root: Path, configured_ref: str) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / configured_ref).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, configured_ref)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_registry_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def _append_violation(violations: list[str], reason: str, detail: str) -> None:
    violations.append(f"{reason}:{detail}")


def _collect_stray_atlas_docs(repo_root: Path, canonical_doc: Path, atlas_doc_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    for candidate in repo_root.rglob("*.md"):
        if not atlas_doc_re.match(candidate.name):
            continue
        rel = candidate.relative_to(repo_root).as_posix()
        if rel != canonical_doc.relative_to(repo_root).as_posix():
            out.append(rel)
    return sorted(set(out))


def _collect_stray_svg_files(
    repo_root: Path,
    canonical_asset_root: Path,
    svg_family_re: re.Pattern[str],
) -> list[str]:
    out: list[str] = []
    for candidate in repo_root.rglob("*.svg"):
        if not svg_family_re.match(candidate.name):
            continue
        rel = candidate.relative_to(repo_root).as_posix()
        if canonical_asset_root not in candidate.parents:
            out.append(rel)
    return sorted(set(out))


def _static_alias_row_for(doc: str, registry_doc: dict[str, Any]) -> list[str]:
    rows = registry_doc.get("static_doc_required_alias_refs")
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if _norm_path(row.get("doc", "")) != doc:
            continue
        return [_norm_path(item) for item in (row.get("alias_refs") or []) if _norm_path(item)]
    return []


def validate_visual_atlas_governance(config: VisualAtlasConfig, repo_root_override: str = "") -> dict[str, Any]:
    repo_root = resolve_repo_root(repo_root_override, start=__file__)
    canonical_doc = (repo_root / config.canonical_doc).resolve()
    canonical_asset_root = (repo_root / config.canonical_asset_root).resolve()
    index_doc = (repo_root / config.audit_index_doc).resolve()

    svg_family_re = re.compile(config.svg_family_pattern)
    atlas_doc_re = re.compile(config.atlas_doc_pattern)

    violations: list[str] = []

    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = _load_stream_doc_registry(
        repo_root, config.stream_doc_registry_ref
    )
    if registry_alias_error:
        _append_violation(violations, "stream_doc_registry_alias_error", registry_alias_error)

    if not canonical_doc.exists() or not canonical_doc.is_file():
        _append_violation(violations, "canonical_atlas_doc_missing", config.canonical_doc)
        atlas_text = ""
    else:
        atlas_text = canonical_doc.read_text(encoding="utf-8")
        for marker in config.atlas_required_markers:
            if marker not in atlas_text:
                _append_violation(violations, "atlas_doc_marker_missing", marker)
        for alias_ref in config.alias_refs:
            if alias_ref not in atlas_text:
                _append_violation(violations, "atlas_doc_alias_ref_missing", alias_ref)
        for svg_name in config.required_svg_files:
            if svg_name not in atlas_text:
                _append_violation(violations, "atlas_doc_svg_ref_missing", svg_name)

    if not canonical_asset_root.exists() or not canonical_asset_root.is_dir():
        _append_violation(violations, "canonical_asset_root_missing", config.canonical_asset_root)

    required_svg_paths: list[str] = []
    for svg_name in config.required_svg_files:
        svg_path = (canonical_asset_root / svg_name).resolve()
        required_svg_paths.append(
            svg_path.relative_to(repo_root).as_posix()
            if svg_path.exists()
            else f"{config.canonical_asset_root}/{svg_name}"
        )
        if not svg_path.exists() or not svg_path.is_file():
            _append_violation(violations, "required_svg_missing", f"{config.canonical_asset_root}/{svg_name}")

    if not index_doc.exists() or not index_doc.is_file():
        _append_violation(violations, "audit_snapshot_index_missing", config.audit_index_doc)
    else:
        index_text = index_doc.read_text(encoding="utf-8")
        for marker in config.index_required_markers:
            if marker not in index_text:
                _append_violation(violations, "audit_index_marker_missing", marker)

    if registry_doc:
        mandatory_static_docs = {
            _norm_path(item)
            for item in (registry_doc.get("mandatory_static_docs") or [])
            if _norm_path(item)
        }
        if config.canonical_doc not in mandatory_static_docs:
            _append_violation(violations, "mandatory_static_doc_missing", config.canonical_doc)
        alias_refs = _static_alias_row_for(config.canonical_doc, registry_doc)
        if not alias_refs:
            _append_violation(violations, "static_alias_row_missing", config.canonical_doc)
        else:
            missing_alias_refs = sorted(set(config.alias_refs) - set(alias_refs))
            for alias_ref in missing_alias_refs:
                _append_violation(violations, "static_alias_ref_missing", alias_ref)
    else:
        _append_violation(violations, "stream_doc_registry_unavailable", str(registry_active_path))

    for owner_doc_rel, markers in config.owner_doc_markers.items():
        owner_doc = (repo_root / owner_doc_rel).resolve()
        if not owner_doc.exists() or not owner_doc.is_file():
            _append_violation(violations, "owner_doc_missing", owner_doc_rel)
            continue
        owner_text = owner_doc.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in owner_text:
                _append_violation(violations, "owner_doc_marker_missing", f"{owner_doc_rel}:{marker}")

    stray_atlas_docs = _collect_stray_atlas_docs(repo_root, canonical_doc, atlas_doc_re)
    for rel in stray_atlas_docs:
        _append_violation(violations, "stray_atlas_doc", rel)

    stray_svg_files = _collect_stray_svg_files(repo_root, canonical_asset_root, svg_family_re)
    for rel in stray_svg_files:
        _append_violation(violations, "stray_svg_file", rel)

    return {
        config.status_key: STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED,
        "error_code": "" if not violations else config.error_code,
        "anti_scatter_scope_mode": config.anti_scatter_scope_mode,
        "repo_root": str(repo_root),
        "scan_root": str(repo_root),
        "workspace_external_surfaces_in_scope": False,
        "workspace_external_scope_examples": ["activity/evidence/", "sibling-workspace staging copies"],
        "stream_doc_registry_entry": str(registry_entry_path),
        "stream_doc_registry_active": str(registry_active_path),
        "stream_doc_registry_alias_error": registry_alias_error,
        "canonical_atlas_doc": config.canonical_doc,
        "canonical_asset_root": config.canonical_asset_root,
        "required_svg_files": list(config.required_svg_files),
        "required_svg_paths": required_svg_paths,
        "required_svg_count": len(config.required_svg_files),
        "stray_atlas_docs": stray_atlas_docs,
        "stray_svg_files": stray_svg_files,
        "violation_count": len(violations),
        "violations": violations,
    }


def emit_visual_atlas_cli(config: VisualAtlasConfig, *, description: str) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = validate_visual_atlas_governance(config, repo_root_override=args.repo_root)
    status = payload.get(config.status_key)
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return 0 if status == STATUS_PASS_REQUIRED else 1

    if status != STATUS_PASS_REQUIRED:
        print(f"[FAIL] {config.error_code} visual atlas governance drift detected")
        for violation in payload.get("violations", []):
            print(f" - {violation}")
        return 1
    print(f"[PASS] visual atlas governance OK: {config.canonical_doc}")
    return 0
