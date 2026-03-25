#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT = (
    "identity/protocol/mappings/root-machine-registry-completeness.current.yaml"
)


@dataclass(frozen=True)
class AnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def _as_bool(value: Any) -> bool:
    return value is True


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_machine_registry_completeness(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(
        repo_root, ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT
    )
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_completeness_mapping_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def require_self_describing_families(doc: Mapping[str, Any]) -> bool:
    return _as_bool(doc.get("require_self_describing_families"))


def required_descriptor_fields_from_doc(doc: Mapping[str, Any]) -> tuple[str, ...]:
    return _as_str_tuple(doc.get("required_descriptor_fields"))


def required_descriptor_field_modes_from_doc(doc: Mapping[str, Any]) -> dict[str, str]:
    rows = doc.get("required_descriptor_field_modes")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        field = _norm_str(key)
        mode = _norm_str(value)
        if field and mode:
            out[field] = mode
    return out


def repo_rel_path_scope_policy_from_doc(doc: Mapping[str, Any]) -> str:
    return _norm_str(doc.get("repo_rel_path_scope_policy"))


def repo_rel_path_escape_policy_from_doc(doc: Mapping[str, Any]) -> str:
    return _norm_str(doc.get("repo_rel_path_escape_policy"))


def repo_rel_path_role_typing_policy_from_doc(doc: Mapping[str, Any]) -> str:
    return _norm_str(doc.get("repo_rel_path_role_typing_policy"))


def repo_rel_path_surface_stem_policy_from_doc(doc: Mapping[str, Any]) -> str:
    return _norm_str(doc.get("repo_rel_path_surface_stem_policy"))


def family_surface_stem_binding_policy_from_doc(doc: Mapping[str, Any]) -> str:
    return _norm_str(doc.get("family_surface_stem_binding_policy"))


def family_surface_stem_overrides_from_doc(doc: Mapping[str, Any]) -> dict[str, str]:
    rows = doc.get("family_surface_stem_overrides")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        family_id = _norm_str(key)
        surface_stem = _norm_str(value)
        if family_id and surface_stem:
            out[family_id] = surface_stem
    return out


def required_repo_rel_path_patterns_from_doc(doc: Mapping[str, Any]) -> dict[str, str]:
    rows = doc.get("required_repo_rel_path_patterns")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        field = _norm_str(key)
        pattern = _clean_str(value)
        if field and pattern:
            out[field] = pattern
    return out


def load_mapping_descriptor(path: Path) -> dict[str, Any]:
    return _load_yaml(path)


def resolve_repo_relative_surface(repo_root: Path, raw_path: Any) -> tuple[str, str, str]:
    rel_path = _norm_str(raw_path)
    if not rel_path:
        return "", "path_missing", ""
    candidate_path = Path(rel_path)
    if candidate_path.is_absolute():
        return rel_path, "absolute_path_forbidden", rel_path
    resolved = (repo_root / rel_path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return rel_path, "repo_root_escape_forbidden", str(resolved)
    if not resolved.exists():
        return rel_path, "path_missing", str(resolved)
    return rel_path, "", str(resolved)


def repo_rel_path_pattern_matches(rel_path: str, pattern: str) -> bool:
    norm_path = _norm_str(rel_path)
    norm_pattern = _clean_str(pattern)
    if not norm_path or not norm_pattern:
        return False
    try:
        return re.fullmatch(norm_pattern, norm_path) is not None
    except re.error:
        return False


def extract_repo_rel_path_surface_stem(rel_path: str, pattern: str) -> tuple[str, str]:
    norm_path = _norm_str(rel_path)
    norm_pattern = _clean_str(pattern)
    if not norm_path or not norm_pattern:
        return "", "surface_stem_pattern_missing"
    try:
        match = re.fullmatch(norm_pattern, norm_path)
    except re.error:
        return "", "surface_stem_pattern_invalid"
    if not match:
        return "", "surface_stem_pattern_mismatch"
    stem = _norm_str(match.groupdict().get("surface_stem"))
    if not stem:
        return "", "surface_stem_capture_missing"
    return stem, ""


def default_surface_stem_from_family_id(family_id: str) -> tuple[str, str]:
    norm_family_id = _norm_str(family_id)
    if not norm_family_id:
        return "", "family_id_missing"
    if not re.fullmatch(r"root-[a-z0-9-]+", norm_family_id):
        return "", "family_id_invalid"
    return norm_family_id.replace("-", "_"), ""


def extract_validator_status_key(repo_root: Path, validator_script: str) -> tuple[str, str]:
    validator_path = (repo_root / _norm_str(validator_script)).resolve()
    if not validator_path.exists() or not validator_path.is_file():
        return "", "validator_script_missing"
    text = validator_path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r'^STATUS_KEY\s*=\s*"([^"]+)"', text, re.M)
    if not match:
        return "", "validator_status_key_missing"
    return _norm_str(match.group(1)), ""


def extract_validator_error_codes(repo_root: Path, validator_script: str) -> tuple[tuple[str, ...], str]:
    validator_path = (repo_root / _norm_str(validator_script)).resolve()
    if not validator_path.exists() or not validator_path.is_file():
        return (), "validator_script_missing"
    text = validator_path.read_text(encoding="utf-8", errors="ignore")
    codes = tuple(
        _norm_str(match.group(1))
        for match in re.finditer(r'^ERR_[A-Z0-9_]+\s*=\s*"([^"]+)"', text, re.M)
        if _norm_str(match.group(1))
    )
    if not codes:
        return (), "validator_error_codes_missing"
    return codes, ""


def anchor_checks_from_doc(doc: Mapping[str, Any]) -> tuple[AnchorCheck, ...]:
    rows = doc.get("anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[AnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        required_markers = _as_str_tuple(row.get("required_markers"))
        if not rel_path or not required_markers:
            continue
        out.append(AnchorCheck(rel_path=rel_path, required_markers=required_markers))
    return tuple(out)
