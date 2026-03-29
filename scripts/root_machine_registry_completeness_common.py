#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import RootDocAnchorCheck, root_doc_anchor_checks_from_doc

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_MACHINE_REGISTRY_COMPLETENESS_CURRENT = (
    "identity/protocol/mappings/root-machine-registry-completeness.current.yaml"
)
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
MACHINE_REGISTRY_COMPLETENESS_SECTION_MARKER = "## Root machine-registry completeness discipline"
MACHINE_REGISTRY_COMPLETENESS_SURFACE_START_MARKER = "Hidden enforcement knowledge does not satisfy registry completeness."
MACHINE_REGISTRY_COMPLETENESS_BINDING_MARKER = (
    "These machine-registry-completeness rules must remain bound to canonical machine-registry-completeness rows rather than drifting into soft summary prose."
)
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


AnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class MachineRegistryCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class MachineRegistryCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class MachineRegistryCompletenessSurface:
    rel_path: str
    rows: tuple[MachineRegistryCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


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


def required_validator_surface_contract_fields_from_doc(doc: Mapping[str, Any]) -> tuple[str, ...]:
    return _as_str_tuple(doc.get("required_validator_surface_contract_fields"))


def required_validator_surface_contract_values_from_doc(doc: Mapping[str, Any]) -> dict[str, str]:
    rows = doc.get("required_validator_surface_contract_values")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        field = _norm_str(key)
        contract = _norm_str(value)
        if field and contract:
            out[field] = contract
    return out


def required_probe_surface_contract_fields_from_doc(doc: Mapping[str, Any]) -> tuple[str, ...]:
    return _as_str_tuple(doc.get("required_probe_surface_contract_fields"))


def required_probe_surface_contract_values_from_doc(doc: Mapping[str, Any]) -> dict[str, str]:
    rows = doc.get("required_probe_surface_contract_values")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        field = _norm_str(key)
        contract = _norm_str(value)
        if field and contract:
            out[field] = contract
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
    return root_doc_anchor_checks_from_doc(doc, field_name="anchor_checks")


def machine_registry_completeness_rows_from_doc(
    doc: Mapping[str, Any],
) -> tuple[MachineRegistryCompletenessRow, ...]:
    rows = doc.get("machine_registry_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[MachineRegistryCompletenessRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        completeness_id = _norm_str(row.get("completeness_id"))
        contract_phrase = _clean_str(row.get("contract_phrase"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not completeness_id or not contract_phrase:
            continue
        out.append(
            MachineRegistryCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_machine_registry_completeness_surface(
    repo_root: Path,
) -> MachineRegistryCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return MachineRegistryCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    surface_start_found = False
    rows: list[MachineRegistryCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == MACHINE_REGISTRY_COMPLETENESS_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if surface_start_found and (HEADING_RE.match(stripped) or HORIZONTAL_RULE_RE.match(stripped)):
            break
        if not surface_start_found:
            if stripped == MACHINE_REGISTRY_COMPLETENESS_SURFACE_START_MARKER:
                surface_start_found = True
            continue
        match = ORDERED_ITEM_RE.match(stripped)
        if not match:
            continue
        rows.append(
            MachineRegistryCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    elif not surface_start_found:
        extraction_violations.append("surface_start_marker_missing")
    elif not rows:
        extraction_violations.append("ordered_items_missing")

    return MachineRegistryCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
