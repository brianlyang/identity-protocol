#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import RootDocAnchorCheck, root_doc_anchor_checks_from_doc

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_AUTHORITY_CURRENT = "identity/protocol/mappings/root-corpus-authority.current.yaml"


AuthorityAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class AuthorityClassProfile:
    corpus_class: str
    authority_role: str
    authority_mode: str
    philosophical_primacy: bool
    law_bearing_required: bool


@dataclass(frozen=True)
class EntryAuthorityProjection:
    rel_path: str
    corpus_class: str
    authority_role: str
    authority_mode: str


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


def load_root_corpus_authority(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_AUTHORITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_AUTHORITY_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_authority_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def authority_anchor_checks_from_doc(authority_doc: Mapping[str, Any]) -> tuple[AuthorityAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        authority_doc,
        field_name="authority_anchor_checks",
        require_markers=False,
    )


def authority_class_profiles_from_doc(authority_doc: Mapping[str, Any]) -> tuple[AuthorityClassProfile, ...]:
    rows = authority_doc.get("authority_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[AuthorityClassProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        corpus_class = _norm_str(row.get("corpus_class"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        if not corpus_class or not authority_role or not authority_mode:
            continue
        out.append(
            AuthorityClassProfile(
                corpus_class=corpus_class,
                authority_role=authority_role,
                authority_mode=authority_mode,
                philosophical_primacy=bool(row.get("philosophical_primacy", False)),
                law_bearing_required=bool(row.get("law_bearing_required", False)),
            )
        )
    return tuple(out)


def entry_authority_projections_from_doc(authority_doc: Mapping[str, Any]) -> tuple[EntryAuthorityProjection, ...]:
    rows = authority_doc.get("entry_authority_projection")
    if not isinstance(rows, list):
        return ()
    out: list[EntryAuthorityProjection] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        corpus_class = _norm_str(row.get("corpus_class"))
        authority_role = _norm_str(row.get("authority_role"))
        authority_mode = _norm_str(row.get("authority_mode"))
        if not rel_path or not corpus_class or not authority_role or not authority_mode:
            continue
        out.append(
            EntryAuthorityProjection(
                rel_path=rel_path,
                corpus_class=corpus_class,
                authority_role=authority_role,
                authority_mode=authority_mode,
            )
        )
    return tuple(out)
