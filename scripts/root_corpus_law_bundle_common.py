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
ROOT_CORPUS_LAW_BUNDLE_CURRENT = "identity/protocol/mappings/root-corpus-law-bundle.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_SECTION_MARKER = "## Root law-bundle component-row completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


BundleAnchorCheck = RootDocAnchorCheck


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


@dataclass(frozen=True)
class LawBundleComponentRowCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class LawBundleComponentRowCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class LawBundleComponentRowCompletenessSurface:
    rel_path: str
    rows: tuple[LawBundleComponentRowCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


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


def descriptor_schema_local_reauthoring_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_local_reauthoring_policy"))


def descriptor_schema_local_reconstruction_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_schema_local_reconstruction_policy"))


def component_self_describing_family_requirement_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_inheritance_mode"))


def component_self_describing_family_requirement_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_local_override_policy"))


def component_self_describing_family_requirement_local_redeclaration_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_local_redeclaration_policy"))


def component_self_describing_family_requirement_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_self_describing_family_requirement_fallback_policy"))


def descriptor_family_surface_binding_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_inheritance_mode"))


def descriptor_family_surface_binding_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_local_override_policy"))


def descriptor_family_surface_binding_local_redeclaration_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_family_surface_binding_local_redeclaration_policy"))


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


def descriptor_repo_rel_path_discipline_local_redeclaration_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_discipline_local_redeclaration_policy"))


def descriptor_repo_rel_path_discipline_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("descriptor_repo_rel_path_discipline_fallback_policy"))


def component_current_version_naming_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_inheritance_mode"))


def component_current_version_naming_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_local_override_policy"))


def component_current_version_naming_local_redeclaration_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_local_redeclaration_policy"))


def component_current_version_naming_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_current_version_naming_fallback_policy"))


def component_registry_child_membership_inheritance_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_inheritance_mode"))


def component_registry_child_membership_local_override_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_local_override_policy"))


def component_registry_child_membership_local_redeclaration_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_local_redeclaration_policy"))


def component_registry_child_membership_fallback_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_registry_child_membership_fallback_policy"))


def component_descriptor_resolution_mode_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_descriptor_resolution_mode"))


def component_descriptor_version_pinning_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_descriptor_version_pinning_policy"))


def component_descriptor_concordance_local_waiver_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_descriptor_concordance_local_waiver_policy"))


def component_validator_status_requirement_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_status_requirement"))


def component_validator_execution_failure_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_execution_failure_policy"))


def component_validator_returncode_observation_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_returncode_observation_contract"))


def component_validator_output_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_output_contract"))


def component_validator_root_doc_anchor_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_root_doc_anchor_contract"))


def component_validator_row_projection_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_row_projection_contract"))


def component_probe_shadow_bootstrap_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_probe_shadow_bootstrap_contract"))


def component_validator_invocation_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_invocation_contract"))


def component_validator_output_channel_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_output_channel_contract"))


def component_validator_stderr_isolation_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_stderr_isolation_contract"))


def component_validator_stdio_text_decoding_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_stdio_text_decoding_contract"))


def component_validator_stdout_normalization_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_stdout_normalization_contract"))


def component_validator_stdout_presence_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_stdout_presence_contract"))


def component_validator_stdout_framing_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_stdout_framing_contract"))


def component_validator_status_key_resolution_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_status_key_resolution_contract"))


def component_validator_status_literal_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_status_literal_contract"))


def component_validator_execution_input_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_execution_input_contract"))


def component_validator_verdict_admission_timing_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_verdict_admission_timing_contract"))


def component_validator_execution_timeout_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_execution_timeout_contract"))


def component_validator_working_directory_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_working_directory_contract"))


def component_validator_execution_environment_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_execution_environment_contract"))


def component_validator_execution_transport_contract_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_execution_transport_contract"))


def component_validator_contract_drift_execution_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_contract_drift_execution_policy"))


def component_validator_contract_surface_projection_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_contract_surface_projection_policy"))


def component_validator_observation_continuity_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_continuity_policy"))


def component_status_row_coverage_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_status_row_coverage_policy"))


def violation_projection_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("violation_projection_policy"))


def final_status_derivation_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("final_status_derivation_policy"))


def error_code_precedence_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("error_code_precedence_policy"))


def failure_classification_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("failure_classification_policy"))


def registry_class_admission_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_class_admission_policy"))


def registry_direct_stale_reason_origin_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_origin_policy"))


def registry_direct_stale_reason_alias_origin_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_alias_origin_policy"))


def registry_direct_stale_reason_document_origin_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_document_origin_policy"))


def registry_direct_stale_reason_required_surface_origin_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_required_surface_origin_policy"))


def registry_direct_stale_reason_contract_row_origin_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_contract_row_origin_policy"))


def registry_direct_stale_reason_source_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_source_policy"))


def registry_direct_stale_reason_partition_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_partition_policy"))


def registry_direct_stale_reason_origin_classifier_precedence_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_origin_classifier_precedence_policy"))


def registry_direct_stale_reason_residual_unknown_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_residual_unknown_policy"))


def registry_direct_stale_reason_unclassified_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("registry_direct_stale_reason_unclassified_policy"))


def component_validator_observation_reason_admission_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_admission_policy"))


def component_validator_observation_reason_parse_status_origin_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_parse_status_origin_policy"))


def component_validator_observation_reason_nonzero_rc_origin_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_nonzero_rc_origin_policy"))


def component_validator_observation_reason_nonpass_status_origin_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_nonpass_status_origin_policy"))


def component_validator_observation_reason_prefixed_ontology_drift_origin_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_prefixed_ontology_drift_origin_policy"))


def component_validator_observation_reason_residual_not_applicable_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_residual_not_applicable_policy"))


def component_validator_observation_reason_classifier_precedence_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_classifier_precedence_policy"))


def component_validator_observation_reason_exclusion_origin_policy_from_doc(
    bundle_doc: Mapping[str, Any]
) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_exclusion_origin_policy"))


def component_validator_observation_reason_exclusion_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_exclusion_policy"))


def component_validator_observation_reason_source_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_source_policy"))


def component_validator_observation_reason_partition_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_partition_policy"))


def component_validator_observation_reason_unclassified_policy_from_doc(bundle_doc: Mapping[str, Any]) -> str:
    return _norm_str(bundle_doc.get("component_validator_observation_reason_unclassified_policy"))


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
    return root_doc_anchor_checks_from_doc(
        bundle_doc,
        field_name="bundle_anchor_checks",
        require_markers=False,
    )


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


def law_bundle_component_row_completeness_rows_from_doc(
    bundle_doc: Mapping[str, Any],
) -> tuple[LawBundleComponentRowCompletenessRow, ...]:
    rows = bundle_doc.get("law_bundle_component_row_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[LawBundleComponentRowCompletenessRow] = []
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
            LawBundleComponentRowCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_law_bundle_component_row_completeness_surface(
    repo_root: Path,
) -> LawBundleComponentRowCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return LawBundleComponentRowCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[LawBundleComponentRowCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_SECTION_MARKER:
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
            LawBundleComponentRowCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    extraction_violations: list[str] = []
    if not section_found:
        extraction_violations.append("section_missing")
    if section_found and not rows:
        extraction_violations.append("ordered_items_missing")

    return LawBundleComponentRowCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(extraction_violations),
    )
