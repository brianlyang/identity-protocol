#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_LAW_BUNDLE_CURRENT = "identity/protocol/mappings/root-corpus-law-bundle.current.yaml"


@dataclass(frozen=True)
class BundleAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RootLawBundleComponent:
    order: int
    component_id: str
    component_role: str
    current_file: str
    validator_script: str
    probe_script: str
    common_script: str
    status_key: str
    error_codes: tuple[str, ...] = field(default_factory=tuple)


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


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


def load_root_corpus_law_bundle(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_LAW_BUNDLE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_LAW_BUNDLE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_bundle_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def machine_registry_completeness_current_file_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("machine_registry_completeness_current_file"))


def descriptor_schema_source_component_id_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_source_component_id"))


def descriptor_schema_source_binding_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_source_binding_mode"))


def descriptor_schema_source_substitution_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_source_substitution_policy"))


def descriptor_schema_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_fallback_policy"))


def descriptor_schema_local_reconstruction_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_local_reconstruction_policy"))


def component_self_describing_family_requirement_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_inheritance_mode"))


def component_self_describing_family_requirement_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_local_override_policy"))


def component_self_describing_family_requirement_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_fallback_policy"))


def descriptor_family_surface_binding_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_inheritance_mode"))


def descriptor_family_surface_binding_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_local_override_policy"))


def descriptor_family_surface_binding_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_fallback_policy"))


def descriptor_repo_rel_path_pattern_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_pattern_inheritance_mode"))


def descriptor_repo_rel_path_pattern_local_redeclaration_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_pattern_local_redeclaration_policy"))


def descriptor_repo_rel_path_pattern_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_pattern_fallback_policy"))


def descriptor_repo_rel_path_discipline_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_discipline_inheritance_mode"))


def descriptor_repo_rel_path_discipline_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_discipline_local_override_policy"))


def descriptor_repo_rel_path_discipline_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_discipline_fallback_policy"))


def component_current_version_naming_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_inheritance_mode"))


def component_current_version_naming_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_local_override_policy"))


def component_current_version_naming_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_fallback_policy"))


def component_registry_child_membership_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_inheritance_mode"))


def component_registry_child_membership_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_local_override_policy"))


def component_registry_child_membership_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_fallback_policy"))


def component_descriptor_resolution_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_descriptor_resolution_mode"))


def component_descriptor_version_pinning_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_descriptor_version_pinning_policy"))


def require_component_descriptor_concordance(bundle_doc: Mapping[str, Any]) -> bool:
    return _as_bool(bundle_doc.get("require_component_descriptor_concordance"))


def required_component_descriptor_fields_from_doc(bundle_doc: Mapping[str, Any]) -> tuple[str, ...]:
    return _as_str_tuple(bundle_doc.get("required_component_descriptor_fields"))


def required_component_descriptor_field_modes_from_doc(bundle_doc: Mapping[str, Any]) -> dict[str, str]:
    rows = bundle_doc.get("required_component_descriptor_field_modes")
    if not isinstance(rows, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in rows.items():
        norm_key = _norm_str(key)
        norm_value = _norm_str(value)
        if norm_key and norm_value:
            out[norm_key] = norm_value
    return out


def load_mapping_descriptor(path: Path) -> dict[str, Any]:
    return _load_yaml(path)


def component_mapping_family_id_from_current_file(current_file: str) -> tuple[str, str]:
    norm_current_file = _norm_str(current_file)
    if not norm_current_file:
        return "", "component_current_file_missing"
    name = Path(norm_current_file).name
    if not name.endswith(".current.yaml"):
        return "", "component_current_file_not_current_entry"
    family_id = name[: -len(".current.yaml")]
    if not family_id:
        return "", "component_current_family_id_missing"
    return family_id, ""


def bundle_anchor_checks_from_doc(bundle_doc: Mapping[str, Any]) -> tuple[BundleAnchorCheck, ...]:
    rows = bundle_doc.get("bundle_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[BundleAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(BundleAnchorCheck(rel_path=rel_path, required_markers=_as_str_tuple(row.get("required_markers"))))
    return tuple(out)


def bundle_components_from_doc(bundle_doc: Mapping[str, Any]) -> tuple[RootLawBundleComponent, ...]:
    rows = bundle_doc.get("component_rows")
    if not isinstance(rows, list):
        return ()
    out: list[RootLawBundleComponent] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        component_id = _norm_str(row.get("component_id"))
        component_role = _norm_str(row.get("component_role"))
        current_file = _norm_str(row.get("current_file"))
        validator_script = _norm_str(row.get("validator_script"))
        probe_script = _norm_str(row.get("probe_script"))
        common_script = _norm_str(row.get("common_script"))
        status_key = _norm_str(row.get("status_key"))
        error_codes = _as_str_tuple(row.get("error_codes"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if (
            order <= 0
            or not component_id
            or not current_file
            or not validator_script
            or not probe_script
            or not common_script
            or not status_key
            or not error_codes
        ):
            continue
        out.append(
            RootLawBundleComponent(
                order=order,
                component_id=component_id,
                component_role=component_role,
                current_file=current_file,
                validator_script=validator_script,
                probe_script=probe_script,
                common_script=common_script,
                status_key=status_key,
                error_codes=error_codes,
            )
        )
    return tuple(out)
