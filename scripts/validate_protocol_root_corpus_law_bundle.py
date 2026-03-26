#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_corpus_governance_common import find_missing_markers, root_corpus_entries_from_registry
from root_corpus_law_bundle_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    bundle_anchor_checks_from_doc,
    bundle_components_from_doc,
    component_registry_child_membership_fallback_policy_from_doc,
    component_registry_child_membership_inheritance_mode_from_doc,
    component_registry_child_membership_local_redeclaration_policy_from_doc,
    component_registry_child_membership_local_override_policy_from_doc,
    component_current_version_naming_fallback_policy_from_doc,
    component_current_version_naming_inheritance_mode_from_doc,
    component_current_version_naming_local_redeclaration_policy_from_doc,
    component_current_version_naming_local_override_policy_from_doc,
    component_mapping_family_id_from_current_file,
    component_descriptor_resolution_mode_from_doc,
    component_descriptor_version_pinning_policy_from_doc,
    component_descriptor_concordance_local_waiver_policy_from_doc,
    component_validator_status_requirement_from_doc,
    component_validator_execution_failure_policy_from_doc,
    component_validator_output_contract_from_doc,
    component_validator_invocation_contract_from_doc,
    component_validator_output_channel_contract_from_doc,
    component_validator_working_directory_contract_from_doc,
    component_validator_execution_transport_contract_from_doc,
    component_self_describing_family_requirement_fallback_policy_from_doc,
    component_self_describing_family_requirement_inheritance_mode_from_doc,
    component_self_describing_family_requirement_local_redeclaration_policy_from_doc,
    component_self_describing_family_requirement_local_override_policy_from_doc,
    descriptor_family_surface_binding_fallback_policy_from_doc,
    descriptor_family_surface_binding_inheritance_mode_from_doc,
    descriptor_family_surface_binding_local_redeclaration_policy_from_doc,
    descriptor_family_surface_binding_local_override_policy_from_doc,
    descriptor_repo_rel_path_discipline_fallback_policy_from_doc,
    descriptor_repo_rel_path_discipline_inheritance_mode_from_doc,
    descriptor_repo_rel_path_discipline_local_redeclaration_policy_from_doc,
    descriptor_repo_rel_path_discipline_local_override_policy_from_doc,
    descriptor_repo_rel_path_pattern_fallback_policy_from_doc,
    descriptor_repo_rel_path_pattern_inheritance_mode_from_doc,
    descriptor_repo_rel_path_pattern_local_redeclaration_policy_from_doc,
    descriptor_schema_fallback_policy_from_doc,
    descriptor_schema_local_reauthoring_policy_from_doc,
    descriptor_schema_source_component_id_from_doc,
    descriptor_schema_source_binding_mode_from_doc,
    descriptor_schema_source_substitution_policy_from_doc,
    descriptor_schema_local_reconstruction_policy_from_doc,
    load_mapping_descriptor,
    load_root_corpus_law_bundle,
    machine_registry_completeness_current_file_from_doc,
    required_component_descriptor_field_modes_from_doc,
    required_component_descriptor_fields_from_doc,
    require_component_descriptor_concordance,
)
from root_machine_registry_completeness_common import (
    default_surface_stem_from_family_id,
    extract_repo_rel_path_surface_stem,
    family_surface_stem_binding_policy_from_doc,
    family_surface_stem_overrides_from_doc,
    load_root_machine_registry_completeness,
    require_self_describing_families,
    repo_rel_path_escape_policy_from_doc,
    repo_rel_path_role_typing_policy_from_doc,
    repo_rel_path_scope_policy_from_doc,
    repo_rel_path_surface_stem_policy_from_doc,
    required_repo_rel_path_patterns_from_doc,
    required_descriptor_field_modes_from_doc as registry_required_descriptor_field_modes_from_doc,
    required_descriptor_fields_from_doc as registry_required_descriptor_fields_from_doc,
)

STATUS_KEY = "protocol_root_corpus_law_bundle_status"
ERR_REGISTRY = "IP-RCLB-001"
ERR_STRUCTURE = "IP-RCLB-002"
ERR_BUNDLE = "IP-RCLB-003"
COMPONENT_VALIDATOR_INVOCATION_CONTRACT = "python3_repo_root_json_only"
COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT = "stdout_only"
COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT = "repo_root"
COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT = "local_direct_subprocess_vector"

EXPECTED_COMPONENTS = {
    "root_corpus_governance": {
        "component_role": "root_admission_and_corpus_structure",
        "current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_governance.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh",
        "common_script": "scripts/root_corpus_governance_common.py",
        "status_key": "protocol_root_corpus_governance_status",
        "error_codes": ("IP-RCG-001", "IP-RCG-002", "IP-RCG-003"),
    },
    "root_corpus_ordering": {
        "component_role": "source_order_reading_order_and_adjudication_surface_roles",
        "current_file": "identity/protocol/mappings/root-corpus-ordering.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_ordering.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh",
        "common_script": "scripts/root_corpus_ordering_common.py",
        "status_key": "protocol_root_corpus_ordering_status",
        "error_codes": ("IP-RCO-001", "IP-RCO-002", "IP-RCO-003"),
    },
    "root_corpus_authority": {
        "component_role": "authority_layering_and_terminality_split",
        "current_file": "identity/protocol/mappings/root-corpus-authority.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_authority.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh",
        "common_script": "scripts/root_corpus_authority_common.py",
        "status_key": "protocol_root_corpus_authority_status",
        "error_codes": ("IP-RCA-001", "IP-RCA-002", "IP-RCA-003"),
    },
    "root_corpus_question_routing": {
        "component_role": "question_class_and_answer_surface_pairing",
        "current_file": "identity/protocol/mappings/root-corpus-question-routing.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_question_routing.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh",
        "common_script": "scripts/root_corpus_question_routing_common.py",
        "status_key": "protocol_root_corpus_question_routing_status",
        "error_codes": ("IP-RCQR-001", "IP-RCQR-002", "IP-RCQR-003"),
    },
    "root_constitutional_spine": {
        "component_role": "constitutional_entry_order_and_bridge_coherence",
        "current_file": "identity/protocol/mappings/root-constitutional-spine.current.yaml",
        "validator_script": "scripts/validate_protocol_root_constitutional_spine.py",
        "probe_script": "scripts/ci/run_protocol_root_constitutional_spine_probes_ci.sh",
        "common_script": "scripts/root_constitutional_spine_common.py",
        "status_key": "protocol_root_constitutional_spine_status",
        "error_codes": ("IP-RCS-001", "IP-RCS-002", "IP-RCS-003"),
    },
    "root_corpus_derivation": {
        "component_role": "one_way_derivation_and_non_reverse_authorship",
        "current_file": "identity/protocol/mappings/root-corpus-derivation.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_derivation.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh",
        "common_script": "scripts/root_corpus_derivation_common.py",
        "status_key": "protocol_root_corpus_derivation_status",
        "error_codes": ("IP-RCD-001", "IP-RCD-002", "IP-RCD-003"),
    },
    "root_corpus_transition": {
        "component_role": "promotion_demotion_and_reentry_governance",
        "current_file": "identity/protocol/mappings/root-corpus-transition.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_transition.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh",
        "common_script": "scripts/root_corpus_transition_common.py",
        "status_key": "protocol_root_corpus_transition_status",
        "error_codes": ("IP-RCT-001", "IP-RCT-002", "IP-RCT-003"),
    },
    "root_corpus_gateway_admissibility": {
        "component_role": "gateway_input_and_effect_target_scope",
        "current_file": "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_gateway_admissibility.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh",
        "common_script": "scripts/root_corpus_gateway_admissibility_common.py",
        "status_key": "protocol_root_corpus_gateway_admissibility_status",
        "error_codes": ("IP-RGA-001", "IP-RGA-002", "IP-RGA-003"),
    },
    "root_machine_registry_completeness": {
        "component_role": "registry_admission_of_root_mapping_families",
        "current_file": "identity/protocol/mappings/root-machine-registry-completeness.current.yaml",
        "validator_script": "scripts/validate_protocol_root_machine_registry_completeness.py",
        "probe_script": "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh",
        "common_script": "scripts/root_machine_registry_completeness_common.py",
        "status_key": "protocol_root_machine_registry_completeness_status",
        "error_codes": ("IP-RMRC-001", "IP-RMRC-002", "IP-RMRC-003"),
    },
    "root_corpus_precedence": {
        "component_role": "conflict_precedence_and_terminal_machine_enforcement",
        "current_file": "identity/protocol/mappings/root-corpus-precedence.current.yaml",
        "validator_script": "scripts/validate_protocol_root_corpus_precedence.py",
        "probe_script": "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh",
        "common_script": "scripts/root_corpus_precedence_common.py",
        "status_key": "protocol_root_corpus_precedence_status",
        "error_codes": ("IP-RCP-001", "IP-RCP-002", "IP-RCP-003"),
    },
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def _descriptor_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple(str(item or "").strip() for item in value if str(item or "").strip())
    if isinstance(value, list):
        return tuple(str(item or "").strip() for item in value if str(item or "").strip())
    return str(value or "").strip()


def _descriptor_is_present(value: Any) -> bool:
    if isinstance(value, tuple):
        return bool(value)
    return bool(str(value or "").strip())


def _component_validator_cmd(repo_root: Path, validator_script: str, invocation_contract: str) -> list[str]:
    if invocation_contract == COMPONENT_VALIDATOR_INVOCATION_CONTRACT:
        return ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]
    return ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]


def _component_validator_cwd(repo_root: Path, working_directory_contract: str) -> Path:
    if working_directory_contract == COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT:
        return repo_root
    return repo_root


def _component_validator_run_kwargs(
    repo_root: Path, working_directory_contract: str, execution_transport_contract: str
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "cwd": _component_validator_cwd(repo_root, working_directory_contract),
        "capture_output": True,
        "text": True,
        "shell": False,
    }
    if execution_transport_contract == COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT:
        return kwargs
    return kwargs


def _run_component_validator(
    repo_root,
    validator_script: str,
    status_key: str,
    invocation_contract: str,
    working_directory_contract: str,
    execution_transport_contract: str,
) -> tuple[int, dict[str, Any], str]:
    repo_root_path = Path(repo_root)
    cmd = _component_validator_cmd(repo_root_path, validator_script, invocation_contract)
    proc = subprocess.run(
        cmd,
        **_component_validator_run_kwargs(
            repo_root_path, working_directory_contract, execution_transport_contract
        ),
    )
    stdout = (proc.stdout or "").strip()
    if not stdout:
        return proc.returncode, {}, "validator_output_missing"
    try:
        payload = json.loads(stdout)
    except Exception:
        return proc.returncode, {}, "validator_output_invalid_json"
    if status_key not in payload:
        return proc.returncode, payload, "validator_status_key_missing"
    return proc.returncode, payload, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate the governed root-corpus law bundle.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    bundle_doc, bundle_entry_path, bundle_active_path, bundle_alias_error = load_root_corpus_law_bundle(repo_root)
    (
        machine_registry_completeness_doc,
        machine_registry_completeness_entry_path,
        machine_registry_completeness_active_path,
        machine_registry_completeness_alias_error,
    ) = load_root_machine_registry_completeness(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    bundle_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    component_status_rows: list[dict[str, Any]] = []
    error_code = ""

    if bundle_alias_error:
        stale_reasons.append(f"root_corpus_law_bundle_alias_error:{bundle_alias_error}")
        error_code = ERR_REGISTRY
    elif not bundle_doc:
        stale_reasons.append("root_corpus_law_bundle_empty_or_invalid")
        error_code = ERR_REGISTRY
    if machine_registry_completeness_alias_error:
        stale_reasons.append(
            f"root_machine_registry_completeness_alias_error:{machine_registry_completeness_alias_error}"
        )
        error_code = ERR_REGISTRY
    elif not machine_registry_completeness_doc:
        stale_reasons.append("root_machine_registry_completeness_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = bundle_anchor_checks_from_doc(bundle_doc) if bundle_doc else ()
    components = bundle_components_from_doc(bundle_doc) if bundle_doc else ()
    descriptor_concordance_required = require_component_descriptor_concordance(bundle_doc) if bundle_doc else False
    required_component_descriptor_fields = (
        required_component_descriptor_fields_from_doc(bundle_doc) if bundle_doc else ()
    )
    required_component_descriptor_field_modes = (
        required_component_descriptor_field_modes_from_doc(bundle_doc) if bundle_doc else {}
    )
    machine_registry_completeness_current_file = (
        machine_registry_completeness_current_file_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_schema_source_component_id = descriptor_schema_source_component_id_from_doc(bundle_doc) if bundle_doc else ""
    descriptor_schema_source_binding_mode = (
        descriptor_schema_source_binding_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_schema_source_substitution_policy = (
        descriptor_schema_source_substitution_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_schema_fallback_policy = descriptor_schema_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    descriptor_schema_local_reauthoring_policy = (
        descriptor_schema_local_reauthoring_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_schema_local_reconstruction_policy = (
        descriptor_schema_local_reconstruction_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_self_describing_family_requirement_inheritance_mode = (
        component_self_describing_family_requirement_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_self_describing_family_requirement_local_override_policy = (
        component_self_describing_family_requirement_local_override_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_self_describing_family_requirement_local_redeclaration_policy = (
        component_self_describing_family_requirement_local_redeclaration_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_self_describing_family_requirement_fallback_policy = (
        component_self_describing_family_requirement_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_family_surface_binding_inheritance_mode = (
        descriptor_family_surface_binding_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_family_surface_binding_local_override_policy = (
        descriptor_family_surface_binding_local_override_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_family_surface_binding_local_redeclaration_policy = (
        descriptor_family_surface_binding_local_redeclaration_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_family_surface_binding_fallback_policy = (
        descriptor_family_surface_binding_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_pattern_inheritance_mode = (
        descriptor_repo_rel_path_pattern_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_pattern_local_redeclaration_policy = (
        descriptor_repo_rel_path_pattern_local_redeclaration_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_pattern_fallback_policy = (
        descriptor_repo_rel_path_pattern_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_discipline_inheritance_mode = (
        descriptor_repo_rel_path_discipline_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_discipline_local_override_policy = (
        descriptor_repo_rel_path_discipline_local_override_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_discipline_local_redeclaration_policy = (
        descriptor_repo_rel_path_discipline_local_redeclaration_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    descriptor_repo_rel_path_discipline_fallback_policy = (
        descriptor_repo_rel_path_discipline_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_current_version_naming_inheritance_mode = (
        component_current_version_naming_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_current_version_naming_local_override_policy = (
        component_current_version_naming_local_override_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_current_version_naming_local_redeclaration_policy = (
        component_current_version_naming_local_redeclaration_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_current_version_naming_fallback_policy = (
        component_current_version_naming_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_registry_child_membership_inheritance_mode = (
        component_registry_child_membership_inheritance_mode_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_registry_child_membership_local_override_policy = (
        component_registry_child_membership_local_override_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_registry_child_membership_local_redeclaration_policy = (
        component_registry_child_membership_local_redeclaration_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_registry_child_membership_fallback_policy = (
        component_registry_child_membership_fallback_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_descriptor_resolution_mode = component_descriptor_resolution_mode_from_doc(bundle_doc) if bundle_doc else ""
    component_descriptor_version_pinning_policy = (
        component_descriptor_version_pinning_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_descriptor_concordance_local_waiver_policy = (
        component_descriptor_concordance_local_waiver_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_status_requirement = (
        component_validator_status_requirement_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_failure_policy = (
        component_validator_execution_failure_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_output_contract = (
        component_validator_output_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_invocation_contract = (
        component_validator_invocation_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_output_channel_contract = (
        component_validator_output_channel_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_working_directory_contract = (
        component_validator_working_directory_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_transport_contract = (
        component_validator_execution_transport_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    effective_component_validator_status_requirement = (
        component_validator_status_requirement
        if component_validator_status_requirement == STATUS_PASS_REQUIRED
        else STATUS_PASS_REQUIRED
    )
    effective_component_validator_invocation_contract = (
        component_validator_invocation_contract
        if component_validator_invocation_contract == COMPONENT_VALIDATOR_INVOCATION_CONTRACT
        else COMPONENT_VALIDATOR_INVOCATION_CONTRACT
    )
    effective_component_validator_output_channel_contract = (
        component_validator_output_channel_contract
        if component_validator_output_channel_contract == COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT
        else COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT
    )
    effective_component_validator_working_directory_contract = (
        component_validator_working_directory_contract
        if component_validator_working_directory_contract == COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT
        else COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT
    )
    effective_component_validator_execution_transport_contract = (
        component_validator_execution_transport_contract
        if component_validator_execution_transport_contract == COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT
        else COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT
    )
    source_required_descriptor_fields = (
        registry_required_descriptor_fields_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else ()
    )
    source_required_descriptor_field_modes = (
        registry_required_descriptor_field_modes_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else {}
    )
    source_family_surface_stem_binding_policy = (
        family_surface_stem_binding_policy_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else ""
    )
    source_family_surface_stem_overrides = (
        family_surface_stem_overrides_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else {}
    )
    source_required_repo_rel_path_patterns = (
        required_repo_rel_path_patterns_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else {}
    )
    source_repo_rel_path_scope_policy = (
        repo_rel_path_scope_policy_from_doc(machine_registry_completeness_doc) if machine_registry_completeness_doc else ""
    )
    source_repo_rel_path_escape_policy = (
        repo_rel_path_escape_policy_from_doc(machine_registry_completeness_doc) if machine_registry_completeness_doc else ""
    )
    source_repo_rel_path_role_typing_policy = (
        repo_rel_path_role_typing_policy_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else ""
    )
    source_repo_rel_path_surface_stem_policy = (
        repo_rel_path_surface_stem_policy_from_doc(machine_registry_completeness_doc)
        if machine_registry_completeness_doc
        else ""
    )
    source_root_family_prefix = str(machine_registry_completeness_doc.get("root_family_prefix") or "").strip()
    source_current_suffix = str(machine_registry_completeness_doc.get("current_suffix") or "").strip()
    source_version_regex = str(machine_registry_completeness_doc.get("version_regex") or "").strip()
    source_require_current_version_pairs = bool(
        machine_registry_completeness_doc.get("require_current_version_pairs") is True
    )
    source_require_self_describing_families = (
        require_self_describing_families(machine_registry_completeness_doc) if machine_registry_completeness_doc else False
    )
    source_registry_directory_rel_path = str(machine_registry_completeness_doc.get("registry_directory_rel_path") or "").strip()
    source_registry_current_file = str(machine_registry_completeness_doc.get("registry_current_file") or "").strip()
    bundle_local_required_repo_rel_path_patterns = (
        required_repo_rel_path_patterns_from_doc(bundle_doc) if bundle_doc else {}
    )
    bundle_redeclares_required_repo_rel_path_patterns = bool(bundle_doc) and (
        "required_repo_rel_path_patterns" in bundle_doc
    )
    bundle_local_family_surface_binding_governance = {
        key: bundle_doc.get(key)
        for key in ("family_surface_stem_binding_policy", "family_surface_stem_overrides")
        if bool(bundle_doc) and key in bundle_doc
    }
    bundle_redeclares_family_surface_binding_governance = bool(bundle_local_family_surface_binding_governance)
    bundle_local_repo_rel_path_governance = {
        key: str(bundle_doc.get(key) or "").strip()
        for key in (
            "repo_rel_path_scope_policy",
            "repo_rel_path_escape_policy",
            "repo_rel_path_role_typing_policy",
            "repo_rel_path_surface_stem_policy",
        )
        if bool(bundle_doc) and key in bundle_doc
    }
    bundle_redeclares_repo_rel_path_governance = bool(bundle_local_repo_rel_path_governance)
    bundle_local_component_naming_governance = {
        key: (bundle_doc.get(key) if key == "require_current_version_pairs" else str(bundle_doc.get(key) or "").strip())
        for key in ("root_family_prefix", "current_suffix", "version_regex", "require_current_version_pairs")
        if bool(bundle_doc) and key in bundle_doc
    }
    bundle_redeclares_component_naming_governance = bool(bundle_local_component_naming_governance)
    bundle_local_self_describing_family_requirement_governance = {
        "require_self_describing_families": bundle_doc.get("require_self_describing_families")
        for _ in [0]
        if bool(bundle_doc) and "require_self_describing_families" in bundle_doc
    }
    bundle_redeclares_self_describing_family_requirement_governance = bool(
        bundle_local_self_describing_family_requirement_governance
    )
    bundle_local_registry_child_membership_governance = {
        key: str(bundle_doc.get(key) or "").strip()
        for key in ("registry_directory_rel_path", "registry_current_file")
        if bool(bundle_doc) and key in bundle_doc
    }
    bundle_redeclares_registry_child_membership_governance = bool(bundle_local_registry_child_membership_governance)
    source_registered_mapping_children: set[str] = set()
    component_map = {row.component_id: row for row in components}
    sorted_components = sorted(components, key=lambda row: row.order)
    component_orders = [row.order for row in components]

    if not stale_reasons:
        if str(bundle_doc.get("law_bundle_family") or "").strip() != "protocol_root_corpus_law_bundle":
            stale_reasons.append("root_corpus_law_bundle_family_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("law_bundle_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_law_bundle_version_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("root_dir") or "").strip() != "identity/protocol":
            stale_reasons.append("root_corpus_law_bundle_root_dir_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_law_bundle.py":
            stale_reasons.append("root_corpus_law_bundle_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_law_bundle_probes_ci.sh":
            stale_reasons.append("root_corpus_law_bundle_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(bundle_doc.get("common_script") or "").strip() != "scripts/root_corpus_law_bundle_common.py":
            stale_reasons.append("root_corpus_law_bundle_common_script_invalid")
            error_code = ERR_REGISTRY
        if machine_registry_completeness_current_file != "identity/protocol/mappings/root-machine-registry-completeness.current.yaml":
            stale_reasons.append("root_corpus_law_bundle_machine_registry_completeness_current_file_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_source_component_id != "root_machine_registry_completeness":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_source_component_id_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_source_binding_mode != "canonical_source_component_current_only":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_source_binding_mode_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_source_substitution_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_source_substitution_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_local_reauthoring_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_local_reauthoring_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_schema_local_reconstruction_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_descriptor_schema_local_reconstruction_policy_invalid")
            error_code = ERR_REGISTRY
        if component_self_describing_family_requirement_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append(
                "root_corpus_law_bundle_component_self_describing_family_requirement_inheritance_mode_invalid"
            )
            error_code = ERR_REGISTRY
        if component_self_describing_family_requirement_local_override_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_component_self_describing_family_requirement_local_override_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if component_self_describing_family_requirement_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_component_self_describing_family_requirement_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if component_self_describing_family_requirement_fallback_policy != "fail_closed":
            stale_reasons.append(
                "root_corpus_law_bundle_component_self_describing_family_requirement_fallback_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if descriptor_family_surface_binding_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append("root_corpus_law_bundle_descriptor_family_surface_binding_inheritance_mode_invalid")
            error_code = ERR_REGISTRY
        if descriptor_family_surface_binding_local_override_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_descriptor_family_surface_binding_local_override_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_family_surface_binding_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_descriptor_family_surface_binding_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if descriptor_family_surface_binding_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_descriptor_family_surface_binding_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_pattern_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append("root_corpus_law_bundle_descriptor_repo_rel_path_pattern_inheritance_mode_invalid")
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_pattern_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_descriptor_repo_rel_path_pattern_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_pattern_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_descriptor_repo_rel_path_pattern_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_discipline_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append("root_corpus_law_bundle_descriptor_repo_rel_path_discipline_inheritance_mode_invalid")
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_discipline_local_override_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_descriptor_repo_rel_path_discipline_local_override_policy_invalid")
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_discipline_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_descriptor_repo_rel_path_discipline_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if descriptor_repo_rel_path_discipline_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_descriptor_repo_rel_path_discipline_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if component_current_version_naming_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append("root_corpus_law_bundle_component_current_version_naming_inheritance_mode_invalid")
            error_code = ERR_REGISTRY
        if component_current_version_naming_local_override_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_component_current_version_naming_local_override_policy_invalid")
            error_code = ERR_REGISTRY
        if component_current_version_naming_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_component_current_version_naming_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if component_current_version_naming_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_component_current_version_naming_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if component_registry_child_membership_inheritance_mode != "inherit_machine_registry_completeness_current_only":
            stale_reasons.append(
                "root_corpus_law_bundle_component_registry_child_membership_inheritance_mode_invalid"
            )
            error_code = ERR_REGISTRY
        if component_registry_child_membership_local_override_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_component_registry_child_membership_local_override_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if component_registry_child_membership_local_redeclaration_policy != "forbidden":
            stale_reasons.append(
                "root_corpus_law_bundle_component_registry_child_membership_local_redeclaration_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if component_registry_child_membership_fallback_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_component_registry_child_membership_fallback_policy_invalid")
            error_code = ERR_REGISTRY
        if component_descriptor_resolution_mode != "current_alias_only":
            stale_reasons.append("root_corpus_law_bundle_component_descriptor_resolution_mode_invalid")
            error_code = ERR_REGISTRY
        if component_descriptor_version_pinning_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_component_descriptor_version_pinning_policy_invalid")
            error_code = ERR_REGISTRY
        if component_descriptor_concordance_local_waiver_policy != "forbidden":
            stale_reasons.append("root_corpus_law_bundle_component_descriptor_concordance_local_waiver_policy_invalid")
            error_code = ERR_REGISTRY
        if component_validator_status_requirement != STATUS_PASS_REQUIRED:
            stale_reasons.append("root_corpus_law_bundle_component_validator_status_requirement_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_failure_policy != "fail_closed":
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_failure_policy_invalid")
            error_code = ERR_REGISTRY
        if component_validator_output_contract != "json_object_with_disclosed_status_key":
            stale_reasons.append("root_corpus_law_bundle_component_validator_output_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_invocation_contract != COMPONENT_VALIDATOR_INVOCATION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_invocation_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_output_channel_contract != COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_output_channel_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_working_directory_contract != COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_working_directory_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_transport_contract != COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_transport_contract_invalid")
            error_code = ERR_REGISTRY
        if bundle_doc.get("require_component_descriptor_concordance") is not True:
            stale_reasons.append("root_corpus_law_bundle_descriptor_concordance_rule_invalid")
            error_code = ERR_REGISTRY
        if not source_required_descriptor_fields:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_schema_source_required_descriptor_fields_missing",
                }
            )
        if not source_required_descriptor_field_modes:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_schema_source_required_descriptor_field_modes_missing",
                }
            )
        if tuple(source_required_descriptor_fields) != tuple(required_component_descriptor_fields):
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_fields_not_aligned_to_machine_registry_completeness",
                    "bundle_fields": list(required_component_descriptor_fields),
                    "source_fields": list(source_required_descriptor_fields),
                }
            )
        if source_required_descriptor_field_modes != required_component_descriptor_field_modes:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_field_modes_not_aligned_to_machine_registry_completeness",
                    "bundle_modes": dict(required_component_descriptor_field_modes),
                    "source_modes": dict(source_required_descriptor_field_modes),
                }
            )
        if source_family_surface_stem_binding_policy != "family_id_surface_stem_congruent_or_explicit_override":
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_family_surface_binding_policy_not_aligned_to_machine_registry_completeness",
                    "source_family_surface_stem_binding_policy": source_family_surface_stem_binding_policy,
                }
            )
        if bundle_redeclares_family_surface_binding_governance:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_family_surface_binding_governance_local_redeclaration_forbidden",
                    "bundle_local_family_surface_binding_governance": dict(bundle_local_family_surface_binding_governance),
                }
            )
        if not source_family_surface_stem_overrides:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_family_surface_stem_overrides_missing_from_machine_registry_completeness",
                }
            )
        if bundle_redeclares_required_repo_rel_path_patterns:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_repo_rel_path_patterns_local_redeclaration_forbidden",
                    "bundle_required_repo_rel_path_patterns": dict(bundle_local_required_repo_rel_path_patterns),
                }
            )
        if not source_required_repo_rel_path_patterns:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_repo_rel_path_patterns_missing_from_machine_registry_completeness",
                }
            )
        else:
            missing_pattern_fields = [
                field
                for field in ("validator_script", "probe_script", "common_script")
                if not source_required_repo_rel_path_patterns.get(field, "")
            ]
            if missing_pattern_fields:
                bundle_violations.append(
                    {
                        "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                        "reason": "descriptor_repo_rel_path_patterns_incomplete_from_machine_registry_completeness",
                        "missing_pattern_fields": missing_pattern_fields,
                    }
                )
        if bundle_redeclares_repo_rel_path_governance:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_repo_rel_path_governance_local_redeclaration_forbidden",
                    "bundle_local_repo_rel_path_governance": dict(bundle_local_repo_rel_path_governance),
                }
            )
        missing_repo_rel_path_governance_fields = [
            field_name
            for field_name, field_value in (
                ("repo_rel_path_scope_policy", source_repo_rel_path_scope_policy),
                ("repo_rel_path_escape_policy", source_repo_rel_path_escape_policy),
                ("repo_rel_path_role_typing_policy", source_repo_rel_path_role_typing_policy),
                ("repo_rel_path_surface_stem_policy", source_repo_rel_path_surface_stem_policy),
            )
            if not field_value
        ]
        if missing_repo_rel_path_governance_fields:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_repo_rel_path_governance_missing_from_machine_registry_completeness",
                    "missing_policy_fields": missing_repo_rel_path_governance_fields,
                }
            )
        if bundle_redeclares_component_naming_governance:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "component_current_version_naming_governance_local_redeclaration_forbidden",
                    "bundle_local_component_naming_governance": dict(bundle_local_component_naming_governance),
                }
            )
        if bundle_redeclares_self_describing_family_requirement_governance:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "component_self_describing_family_requirement_governance_local_redeclaration_forbidden",
                    "bundle_local_self_describing_family_requirement_governance": dict(
                        bundle_local_self_describing_family_requirement_governance
                    ),
                }
            )
        missing_component_naming_fields = [
            field_name
            for field_name, field_value in (
                ("root_family_prefix", source_root_family_prefix),
                ("current_suffix", source_current_suffix),
                ("version_regex", source_version_regex),
            )
            if not field_value
        ]
        if not source_require_current_version_pairs:
            missing_component_naming_fields.append("require_current_version_pairs")
        if missing_component_naming_fields:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "component_current_version_naming_governance_missing_from_machine_registry_completeness",
                    "missing_policy_fields": missing_component_naming_fields,
                }
            )
        if not source_require_self_describing_families:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_self_describing_family_requirement_not_inherited_from_machine_registry_completeness",
                }
            )
        if bundle_redeclares_registry_child_membership_governance:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "component_registry_child_membership_governance_local_redeclaration_forbidden",
                    "bundle_local_registry_child_membership_governance": dict(
                        bundle_local_registry_child_membership_governance
                    ),
                }
            )
        missing_registry_child_membership_fields = [
            field_name
            for field_name, field_value in (
                ("registry_directory_rel_path", source_registry_directory_rel_path),
                ("registry_current_file", source_registry_current_file),
            )
            if not field_value
        ]
        if missing_registry_child_membership_fields:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "component_registry_child_membership_governance_missing_from_machine_registry_completeness",
                    "missing_policy_fields": missing_registry_child_membership_fields,
                }
            )
        if descriptor_concordance_required and not required_component_descriptor_fields:
            stale_reasons.append("root_corpus_law_bundle_required_component_descriptor_fields_missing")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(bundle_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_law_bundle_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_law_bundle_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not components:
            stale_reasons.append("root_corpus_law_bundle_components_missing")
            error_code = ERR_REGISTRY

    if not stale_reasons:
        if len(component_map) != len(components):
            structure_violations.append({"field": "component_rows", "reason": "duplicate_component_id"})
        if len(set(component_orders)) != len(component_orders) or not _contiguous_orders(sorted(component_orders)):
            structure_violations.append({"field": "component_rows", "reason": "component_order_non_contiguous"})

        source_component = component_map.get(descriptor_schema_source_component_id)
        if source_component is None:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                    "reason": "descriptor_schema_source_component_missing_from_bundle",
                }
            )
        elif source_component.current_file != machine_registry_completeness_current_file:
            bundle_violations.append(
                {
                    "component_id": descriptor_schema_source_component_id,
                    "reason": "descriptor_schema_source_component_current_file_mismatch",
                    "bundle_source_current_file": machine_registry_completeness_current_file,
                    "component_current_file": source_component.current_file,
                }
            )

        registry_entry_path = None
        registry_active_path = None
        registry_alias_error = ""
        registry_doc: dict[str, Any] = {}
        if source_registry_current_file:
            registry_entry_path = (repo_root / source_registry_current_file).resolve()
            registry_active_path, _registry_active_file, registry_alias_error = resolve_current_yaml_alias(
                repo_root, source_registry_current_file
            )
            if registry_alias_error:
                bundle_violations.append(
                    {
                        "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                        "reason": "source_registry_current_alias_error",
                        "source_registry_current_file": source_registry_current_file,
                        "alias_error": registry_alias_error,
                    }
                )
            elif not registry_active_path.exists():
                bundle_violations.append(
                    {
                        "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                        "reason": "source_registry_active_file_missing",
                        "source_registry_current_file": source_registry_current_file,
                        "active_path": str(registry_active_path),
                    }
                )
            else:
                registry_doc = load_mapping_descriptor(registry_active_path)
                if not registry_doc:
                    bundle_violations.append(
                        {
                            "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                            "reason": "source_registry_active_doc_invalid",
                            "source_registry_current_file": source_registry_current_file,
                            "active_path": str(registry_active_path),
                        }
                    )
                else:
                    registry_entry_map = {
                        entry.rel_path: entry for entry in root_corpus_entries_from_registry(registry_doc)
                    }
                    mappings_entry = registry_entry_map.get(source_registry_directory_rel_path)
                    if mappings_entry is None:
                        bundle_violations.append(
                            {
                                "component_id": descriptor_schema_source_component_id or "root_machine_registry_completeness",
                                "reason": "source_registry_directory_not_admitted_in_registry_child_set",
                                "source_registry_directory_rel_path": source_registry_directory_rel_path,
                                "source_registry_current_file": source_registry_current_file,
                            }
                        )
                    else:
                        source_registered_mapping_children = {
                            str((Path(source_registry_directory_rel_path) / child).as_posix())
                            for child in mappings_entry.required_children
                        }

        missing_components = sorted(set(EXPECTED_COMPONENTS) - set(component_map))
        extra_components = sorted(set(component_map) - set(EXPECTED_COMPONENTS))
        if missing_components:
            structure_violations.append(
                {"field": "component_rows", "reason": "missing_expected_components", "component_ids": missing_components}
            )
        if extra_components:
            structure_violations.append(
                {"field": "component_rows", "reason": "extra_components", "component_ids": extra_components}
            )

        for row in sorted_components:
            expected = EXPECTED_COMPONENTS.get(row.component_id)
            if expected is None:
                continue
            if source_current_suffix and not row.current_file.endswith(source_current_suffix):
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_descriptor_not_current_entry",
                        "current_file": row.current_file,
                        "expected_current_suffix": source_current_suffix,
                    }
                )
            if source_registry_directory_rel_path and not row.current_file.startswith(
                f"{source_registry_directory_rel_path}/"
            ):
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_current_file_outside_inherited_registry_directory",
                        "current_file": row.current_file,
                        "source_registry_directory_rel_path": source_registry_directory_rel_path,
                    }
                )
            if source_registered_mapping_children and row.current_file not in source_registered_mapping_children:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_current_file_not_admitted_by_inherited_registry_child_set",
                        "current_file": row.current_file,
                        "source_registry_directory_rel_path": source_registry_directory_rel_path,
                    }
                )
            for field in (
                "component_role",
                "current_file",
                "validator_script",
                "probe_script",
                "common_script",
                "status_key",
                "error_codes",
            ):
                actual = getattr(row, field)
                if actual != expected[field]:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": f"{field}_mismatch",
                            "expected": expected[field],
                            "actual": actual,
                        }
                    )

            current_path = (repo_root / row.current_file).resolve()
            if not current_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_current_file_missing"})
            else:
                active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, row.current_file)
                if alias_error:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_current_alias_error",
                            "alias_error": alias_error,
                        }
                    )
                elif not active_path.exists():
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_active_file_missing",
                            "active_path": str(active_path),
                        }
                    )
                elif source_version_regex and re.fullmatch(source_version_regex, active_path.name) is None:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_active_file_not_inherited_version_pattern",
                            "active_file": active_path.name,
                            "source_version_regex": source_version_regex,
                        }
                    )
                else:
                    active_rel_path = str(active_path.relative_to(repo_root.resolve()).as_posix())
                    if source_registered_mapping_children and active_rel_path not in source_registered_mapping_children:
                        bundle_violations.append(
                            {
                                "component_id": row.component_id,
                                "reason": "component_active_file_not_admitted_by_inherited_registry_child_set",
                                "active_rel_path": active_rel_path,
                                "source_registry_directory_rel_path": source_registry_directory_rel_path,
                            }
                        )

            validator_path = (repo_root / row.validator_script).resolve()
            if not validator_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_validator_missing"})
                continue

            probe_path = (repo_root / row.probe_script).resolve()
            if not probe_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_probe_missing"})

            common_path = (repo_root / row.common_script).resolve()
            if not common_path.exists():
                bundle_violations.append({"component_id": row.component_id, "reason": "component_common_missing"})

            component_mapping_family_id, component_mapping_family_id_error = component_mapping_family_id_from_current_file(
                row.current_file
            )
            if component_mapping_family_id and source_root_family_prefix and not component_mapping_family_id.startswith(
                source_root_family_prefix
            ):
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_family_id_outside_inherited_root_family_prefix",
                        "component_mapping_family_id": component_mapping_family_id,
                        "source_root_family_prefix": source_root_family_prefix,
                    }
                )
            default_expected_component_surface_stem = ""
            default_expected_component_surface_stem_error = ""
            if component_mapping_family_id:
                (
                    default_expected_component_surface_stem,
                    default_expected_component_surface_stem_error,
                ) = default_surface_stem_from_family_id(component_mapping_family_id)
            expected_component_surface_stem = source_family_surface_stem_overrides.get(
                component_mapping_family_id, default_expected_component_surface_stem
            )
            expected_component_surface_stem_source = (
                "machine_registry_explicit_override"
                if component_mapping_family_id in source_family_surface_stem_overrides
                else "mapping_family_default"
            )
            component_descriptor_surface_stems: dict[str, str] = {}
            component_descriptor_surface_stem_errors: dict[str, str] = {}
            for descriptor_field in ("validator_script", "probe_script", "common_script"):
                expected_pattern = source_required_repo_rel_path_patterns.get(descriptor_field, "")
                surface_stem, surface_stem_error = extract_repo_rel_path_surface_stem(
                    str(getattr(row, descriptor_field) or ""),
                    expected_pattern,
                )
                if surface_stem:
                    component_descriptor_surface_stems[descriptor_field] = surface_stem
                if surface_stem_error:
                    component_descriptor_surface_stem_errors[descriptor_field] = surface_stem_error

            rc, payload, run_error = _run_component_validator(
                repo_root,
                row.validator_script,
                row.status_key,
                effective_component_validator_invocation_contract,
                effective_component_validator_working_directory_contract,
                effective_component_validator_execution_transport_contract,
            )
            component_status = str(payload.get(row.status_key) or "")
            descriptor_field_rows: list[dict[str, str]] = []
            component_status_rows.append(
                {
                    "order": row.order,
                    "component_id": row.component_id,
                    "status_key": row.status_key,
                    "validator_script": row.validator_script,
                    "probe_script": row.probe_script,
                    "common_script": row.common_script,
                    "validator_rc": rc,
                    "component_status": component_status,
                    "error_codes": list(row.error_codes),
                    "validator_error": run_error,
                    "descriptor_concordance_required": descriptor_concordance_required,
                    "component_mapping_family_id": component_mapping_family_id,
                    "component_mapping_family_id_error": component_mapping_family_id_error,
                    "expected_component_surface_stem": expected_component_surface_stem,
                    "expected_component_surface_stem_source": expected_component_surface_stem_source,
                    "expected_component_surface_stem_error": default_expected_component_surface_stem_error,
                    "component_descriptor_surface_stems": dict(component_descriptor_surface_stems),
                    "component_descriptor_surface_stem_errors": dict(component_descriptor_surface_stem_errors),
                    "required_component_descriptor_fields": list(required_component_descriptor_fields),
                    "required_component_descriptor_field_modes": dict(required_component_descriptor_field_modes),
                    "descriptor_field_rows": descriptor_field_rows,
                }
            )
            if run_error:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": run_error,
                        "validator_rc": rc,
                    }
                )
            elif rc != 0:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_validator_nonzero_rc",
                        "validator_rc": rc,
                        "component_status": component_status,
                    }
                )
            elif component_status != effective_component_validator_status_requirement:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_status_not_pass_required",
                        "component_status": component_status,
                        "required_component_status": effective_component_validator_status_requirement,
                    }
                )

            if component_mapping_family_id_error:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_mapping_family_id_unresolved",
                        "component_mapping_family_id_error": component_mapping_family_id_error,
                        "current_file": row.current_file,
                    }
                )
            if default_expected_component_surface_stem_error:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_expected_surface_stem_unresolved",
                        "component_mapping_family_id": component_mapping_family_id,
                        "expected_component_surface_stem_error": default_expected_component_surface_stem_error,
                    }
                )
            if component_descriptor_surface_stem_errors:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_descriptor_surface_stem_unresolved",
                        "component_descriptor_surface_stem_errors": dict(component_descriptor_surface_stem_errors),
                    }
                )
            unique_component_surface_stems = sorted(set(component_descriptor_surface_stems.values()))
            if len(unique_component_surface_stems) > 1:
                bundle_violations.append(
                    {
                        "component_id": row.component_id,
                        "reason": "component_descriptor_surface_stem_mismatch",
                        "component_descriptor_surface_stems": dict(component_descriptor_surface_stems),
                    }
                )
            elif unique_component_surface_stems and expected_component_surface_stem:
                actual_component_surface_stem = unique_component_surface_stems[0]
                if actual_component_surface_stem != expected_component_surface_stem:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": "component_family_surface_binding_not_inherited",
                            "component_mapping_family_id": component_mapping_family_id,
                            "expected_component_surface_stem": expected_component_surface_stem,
                            "expected_component_surface_stem_source": expected_component_surface_stem_source,
                            "actual_component_surface_stem": actual_component_surface_stem,
                            "component_descriptor_surface_stems": dict(component_descriptor_surface_stems),
                        }
                    )

            if descriptor_concordance_required and current_path.exists():
                active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, row.current_file)
                if not alias_error and active_path.exists():
                    active_doc = load_mapping_descriptor(active_path)
                    if not active_doc:
                        bundle_violations.append(
                            {
                                "component_id": row.component_id,
                                "reason": "component_active_descriptor_invalid",
                                "active_path": str(active_path),
                            }
                        )
                    else:
                        for descriptor_field in required_component_descriptor_fields:
                            bundle_value = _descriptor_value(getattr(row, descriptor_field))
                            active_value = _descriptor_value(active_doc.get(descriptor_field))
                            descriptor_mode = required_component_descriptor_field_modes.get(descriptor_field, "")
                            descriptor_field_rows.append(
                                {
                                    "field": descriptor_field,
                                    "descriptor_mode": descriptor_mode,
                                    "bundle_rel_path": list(bundle_value) if isinstance(bundle_value, tuple) else bundle_value,
                                    "active_rel_path": list(active_value) if isinstance(active_value, tuple) else active_value,
                                    "bundle_value": list(bundle_value) if isinstance(bundle_value, tuple) else bundle_value,
                                    "active_value": list(active_value) if isinstance(active_value, tuple) else active_value,
                                    "status": (
                                        STATUS_PASS_REQUIRED
                                        if active_value == bundle_value and _descriptor_is_present(active_value)
                                        else STATUS_FAIL_REQUIRED
                                    ),
                                }
                            )
                            if not _descriptor_is_present(active_value):
                                bundle_violations.append(
                                    {
                                        "component_id": row.component_id,
                                        "reason": "component_descriptor_field_missing",
                                        "descriptor_field": descriptor_field,
                                    }
                                )
                            elif active_value != bundle_value:
                                bundle_violations.append(
                                    {
                                        "component_id": row.component_id,
                                        "reason": "component_descriptor_concordance_failure",
                                        "descriptor_field": descriptor_field,
                                        "bundle_rel_path": list(bundle_value) if isinstance(bundle_value, tuple) else bundle_value,
                                        "active_rel_path": list(active_value) if isinstance(active_value, tuple) else active_value,
                                        "bundle_value": list(bundle_value) if isinstance(bundle_value, tuple) else bundle_value,
                                        "active_value": list(active_value) if isinstance(active_value, tuple) else active_value,
                                    }
                                )

        for check in anchor_checks:
            path = (repo_root / check.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append({"rel_path": check.rel_path, "reason": "anchor_file_missing"})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in find_missing_markers(text, check.required_markers):
                anchor_violations.append(
                    {
                        "rel_path": check.rel_path,
                        "reason": "required_marker_missing",
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (bundle_violations or anchor_violations):
        error_code = ERR_BUNDLE

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"bundle_violation:{row['component_id']}:{row['reason']}" for row in bundle_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_BUNDLE),
        "bundle_entry_path": str(bundle_entry_path),
        "bundle_active_path": str(bundle_active_path),
        "machine_registry_completeness_entry_path": str(machine_registry_completeness_entry_path),
        "machine_registry_completeness_active_path": str(machine_registry_completeness_active_path),
        "root_dir": str(bundle_doc.get("root_dir") or ""),
        "machine_registry_completeness_current_file": machine_registry_completeness_current_file,
        "descriptor_schema_source_component_id": descriptor_schema_source_component_id,
        "descriptor_schema_source_binding_mode": descriptor_schema_source_binding_mode,
        "descriptor_schema_source_substitution_policy": descriptor_schema_source_substitution_policy,
        "descriptor_schema_fallback_policy": descriptor_schema_fallback_policy,
        "descriptor_schema_local_reauthoring_policy": descriptor_schema_local_reauthoring_policy,
        "descriptor_schema_local_reconstruction_policy": descriptor_schema_local_reconstruction_policy,
        "component_self_describing_family_requirement_inheritance_mode": component_self_describing_family_requirement_inheritance_mode,
        "component_self_describing_family_requirement_local_override_policy": component_self_describing_family_requirement_local_override_policy,
        "component_self_describing_family_requirement_local_redeclaration_policy": component_self_describing_family_requirement_local_redeclaration_policy,
        "component_self_describing_family_requirement_fallback_policy": component_self_describing_family_requirement_fallback_policy,
        "descriptor_family_surface_binding_inheritance_mode": descriptor_family_surface_binding_inheritance_mode,
        "descriptor_family_surface_binding_local_override_policy": descriptor_family_surface_binding_local_override_policy,
        "descriptor_family_surface_binding_local_redeclaration_policy": descriptor_family_surface_binding_local_redeclaration_policy,
        "descriptor_family_surface_binding_fallback_policy": descriptor_family_surface_binding_fallback_policy,
        "descriptor_repo_rel_path_pattern_inheritance_mode": descriptor_repo_rel_path_pattern_inheritance_mode,
        "descriptor_repo_rel_path_pattern_local_redeclaration_policy": descriptor_repo_rel_path_pattern_local_redeclaration_policy,
        "descriptor_repo_rel_path_pattern_fallback_policy": descriptor_repo_rel_path_pattern_fallback_policy,
        "descriptor_repo_rel_path_discipline_inheritance_mode": descriptor_repo_rel_path_discipline_inheritance_mode,
        "descriptor_repo_rel_path_discipline_local_override_policy": descriptor_repo_rel_path_discipline_local_override_policy,
        "descriptor_repo_rel_path_discipline_local_redeclaration_policy": descriptor_repo_rel_path_discipline_local_redeclaration_policy,
        "descriptor_repo_rel_path_discipline_fallback_policy": descriptor_repo_rel_path_discipline_fallback_policy,
        "component_current_version_naming_inheritance_mode": component_current_version_naming_inheritance_mode,
        "component_current_version_naming_local_override_policy": component_current_version_naming_local_override_policy,
        "component_current_version_naming_local_redeclaration_policy": component_current_version_naming_local_redeclaration_policy,
        "component_current_version_naming_fallback_policy": component_current_version_naming_fallback_policy,
        "component_registry_child_membership_inheritance_mode": component_registry_child_membership_inheritance_mode,
        "component_registry_child_membership_local_override_policy": component_registry_child_membership_local_override_policy,
        "component_registry_child_membership_local_redeclaration_policy": component_registry_child_membership_local_redeclaration_policy,
        "component_registry_child_membership_fallback_policy": component_registry_child_membership_fallback_policy,
        "component_descriptor_resolution_mode": component_descriptor_resolution_mode,
        "component_descriptor_version_pinning_policy": component_descriptor_version_pinning_policy,
        "component_descriptor_concordance_local_waiver_policy": component_descriptor_concordance_local_waiver_policy,
        "component_validator_status_requirement": component_validator_status_requirement,
        "component_validator_execution_failure_policy": component_validator_execution_failure_policy,
        "component_validator_output_contract": component_validator_output_contract,
        "component_validator_invocation_contract": component_validator_invocation_contract,
        "component_validator_output_channel_contract": component_validator_output_channel_contract,
        "component_validator_working_directory_contract": component_validator_working_directory_contract,
        "component_validator_execution_transport_contract": component_validator_execution_transport_contract,
        "bundle_anchor_check_count": len(anchor_checks),
        "component_count": len(components),
        "component_ids": [row.component_id for row in sorted_components],
        "required_component_descriptor_fields": list(required_component_descriptor_fields),
        "required_component_descriptor_field_modes": dict(required_component_descriptor_field_modes),
        "source_required_descriptor_fields": list(source_required_descriptor_fields),
        "source_required_descriptor_field_modes": dict(source_required_descriptor_field_modes),
        "source_family_surface_stem_binding_policy": source_family_surface_stem_binding_policy,
        "source_family_surface_stem_overrides": dict(source_family_surface_stem_overrides),
        "source_repo_rel_path_scope_policy": source_repo_rel_path_scope_policy,
        "source_repo_rel_path_escape_policy": source_repo_rel_path_escape_policy,
        "source_repo_rel_path_role_typing_policy": source_repo_rel_path_role_typing_policy,
        "source_repo_rel_path_surface_stem_policy": source_repo_rel_path_surface_stem_policy,
        "source_root_family_prefix": source_root_family_prefix,
        "source_current_suffix": source_current_suffix,
        "source_version_regex": source_version_regex,
        "source_require_current_version_pairs": source_require_current_version_pairs,
        "source_require_self_describing_families": source_require_self_describing_families,
        "source_registry_directory_rel_path": source_registry_directory_rel_path,
        "source_registry_current_file": source_registry_current_file,
        "source_registered_mapping_children_count": len(source_registered_mapping_children),
        "bundle_redeclares_required_repo_rel_path_patterns": bundle_redeclares_required_repo_rel_path_patterns,
        "bundle_local_required_repo_rel_path_patterns": dict(bundle_local_required_repo_rel_path_patterns),
        "bundle_redeclares_family_surface_binding_governance": bundle_redeclares_family_surface_binding_governance,
        "bundle_local_family_surface_binding_governance": dict(bundle_local_family_surface_binding_governance),
        "bundle_redeclares_repo_rel_path_governance": bundle_redeclares_repo_rel_path_governance,
        "bundle_local_repo_rel_path_governance": dict(bundle_local_repo_rel_path_governance),
        "bundle_redeclares_component_naming_governance": bundle_redeclares_component_naming_governance,
        "bundle_local_component_naming_governance": dict(bundle_local_component_naming_governance),
        "bundle_redeclares_self_describing_family_requirement_governance": bundle_redeclares_self_describing_family_requirement_governance,
        "bundle_local_self_describing_family_requirement_governance": dict(bundle_local_self_describing_family_requirement_governance),
        "bundle_redeclares_registry_child_membership_governance": bundle_redeclares_registry_child_membership_governance,
        "bundle_local_registry_child_membership_governance": dict(bundle_local_registry_child_membership_governance),
        "source_required_repo_rel_path_patterns": dict(source_required_repo_rel_path_patterns),
        "component_status_rows": component_status_rows,
        "structure_violations": structure_violations,
        "bundle_violations": bundle_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
