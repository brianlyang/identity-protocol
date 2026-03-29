#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_row_validation_common import contiguous_orders, validate_contract_row_batches
from root_corpus_governance_common import root_corpus_entries_from_registry
from root_corpus_law_bundle_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    bundle_anchor_checks_from_doc,
    bundle_components_from_doc,
    law_bundle_component_row_completeness_rows_from_doc,
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
    component_validator_returncode_observation_contract_from_doc,
    component_validator_output_contract_from_doc,
    component_validator_root_doc_anchor_contract_from_doc,
    component_validator_row_projection_contract_from_doc,
    component_probe_shadow_bootstrap_contract_from_doc,
    component_validator_invocation_contract_from_doc,
    component_validator_output_channel_contract_from_doc,
    component_validator_stderr_isolation_contract_from_doc,
    component_validator_stdio_text_decoding_contract_from_doc,
    component_validator_stdout_normalization_contract_from_doc,
    component_validator_stdout_presence_contract_from_doc,
    component_validator_stdout_framing_contract_from_doc,
    component_validator_status_key_resolution_contract_from_doc,
    component_validator_status_literal_contract_from_doc,
    component_validator_execution_input_contract_from_doc,
    component_validator_verdict_admission_timing_contract_from_doc,
    component_validator_execution_timeout_contract_from_doc,
    component_validator_working_directory_contract_from_doc,
    component_validator_execution_environment_contract_from_doc,
    component_validator_execution_transport_contract_from_doc,
    component_validator_contract_drift_execution_policy_from_doc,
    component_validator_contract_surface_projection_policy_from_doc,
    component_validator_observation_continuity_policy_from_doc,
    component_validator_observation_reason_admission_policy_from_doc,
    component_validator_observation_reason_parse_status_origin_policy_from_doc,
    component_validator_observation_reason_nonzero_rc_origin_policy_from_doc,
    component_validator_observation_reason_nonpass_status_origin_policy_from_doc,
    component_validator_observation_reason_prefixed_ontology_drift_origin_policy_from_doc,
    component_validator_observation_reason_residual_not_applicable_policy_from_doc,
    component_validator_observation_reason_classifier_precedence_policy_from_doc,
    component_validator_observation_reason_exclusion_origin_policy_from_doc,
    component_validator_observation_reason_exclusion_policy_from_doc,
    component_validator_observation_reason_partition_policy_from_doc,
    component_validator_observation_reason_source_policy_from_doc,
    component_validator_observation_reason_unclassified_policy_from_doc,
    component_status_row_coverage_policy_from_doc,
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
    error_code_precedence_policy_from_doc,
    failure_classification_policy_from_doc,
    final_status_derivation_policy_from_doc,
    load_mapping_descriptor,
    load_root_corpus_law_bundle,
    machine_registry_completeness_current_file_from_doc,
    readme_law_bundle_component_row_completeness_surface,
    required_component_descriptor_field_modes_from_doc,
    required_component_descriptor_fields_from_doc,
    require_component_descriptor_concordance,
    registry_class_admission_policy_from_doc,
    registry_direct_stale_reason_origin_policy_from_doc,
    registry_direct_stale_reason_alias_origin_policy_from_doc,
    registry_direct_stale_reason_document_origin_policy_from_doc,
    registry_direct_stale_reason_required_surface_origin_policy_from_doc,
    registry_direct_stale_reason_contract_row_origin_policy_from_doc,
    registry_direct_stale_reason_origin_classifier_precedence_policy_from_doc,
    registry_direct_stale_reason_residual_unknown_policy_from_doc,
    registry_direct_stale_reason_partition_policy_from_doc,
    registry_direct_stale_reason_source_policy_from_doc,
    registry_direct_stale_reason_unclassified_policy_from_doc,
    violation_projection_policy_from_doc,
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
from root_row_family_projection_common import (
    NamedRowFamilyStatusProjectionSpec,
    index_row_family_projection_rows,
    project_named_row_family_statuses,
    project_root_contract_support_projection,
    project_row_families,
)

STATUS_KEY = "protocol_root_corpus_law_bundle_status"
ERR_REGISTRY = "IP-RCLB-001"
ERR_STRUCTURE = "IP-RCLB-002"
ERR_BUNDLE = "IP-RCLB-003"
COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT = "nonzero_returncode_observed_without_host_exception_overlay"
COMPONENT_VALIDATOR_INVOCATION_CONTRACT = "python3_repo_root_json_only"
COMPONENT_VALIDATOR_ROOT_DOC_ANCHOR_CONTRACT = (
    "root_doc_anchor_status_pass_required_with_positive_anchor_check_count"
)
COMPONENT_VALIDATOR_ROW_PROJECTION_CONTRACT = (
    "nonempty_row_family_projection_rows_with_pass_required_coverage_and_identity_statuses"
)
COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT = "stdout_only"
COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT = "stderr_captured_separate_from_stdout"
COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT = "utf8_strict_text_decode_no_locale_overlay"
COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT = "outer_whitespace_trim_only_before_json_decode"
COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT = "nonempty_after_outer_whitespace_trim_required"
COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT = "whole_stdout_single_json_object"
COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT = "top_level_direct_member_only"
COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT = "exact_canonical_string_literal"
COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT = "stdin_devnull_noninteractive"
COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT = "completed_process_post_exit_only"
COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT = "no_local_timeout_overlay"
COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT = "repo_root"
COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT = "inherited_parent_process_env_no_local_overlay"
COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT = "local_direct_subprocess_vector"
COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY = "execute_under_canonical_contract_and_fail_closed_on_drift"
COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY = (
    "bundle_summary_disclosed_component_rows_effective_execution_surface"
)
COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY = (
    "continue_bound_component_observation_under_canonical_surface_before_final_fail_close"
)
COMPONENT_STATUS_ROW_COVERAGE_POLICY = "all_bound_components_must_emit_status_rows_before_final_status"
VIOLATION_PROJECTION_POLICY = (
    "all_structure_bundle_anchor_violations_projected_into_stale_reasons_before_final_status"
)
FINAL_STATUS_DERIVATION_POLICY = (
    "pass_required_if_and_only_if_stale_reasons_empty_after_violation_projection_else_fail_required"
)
ERROR_CODE_PRECEDENCE_POLICY = "registry_preempts_structure_preempts_bundle_else_empty_when_pass_required"
FAILURE_CLASSIFICATION_POLICY = (
    "registry_from_direct_stale_reasons_structure_from_structure_violations_bundle_from_bundle_and_anchor_violations_else_pass"
)
REGISTRY_CLASS_ADMISSION_POLICY = (
    "only_direct_stale_reasons_present_before_violation_projection_admit_registry_failure_class"
)
REGISTRY_DIRECT_STALE_REASON_ORIGIN_POLICY = (
    "alias_document_contract_row_required_surface_only_before_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY = (
    "alias_error_marker_rows_only_before_document_required_surface_contract_row_classification_and_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY = (
    "empty_or_invalid_document_rows_only_after_alias_exclusion_before_required_surface_contract_row_classification_and_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY = (
    "required_component_descriptor_fields_missing_surface_missing_anchor_checks_missing_components_missing_only_before_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY = (
    "root_corpus_law_bundle_or_root_machine_registry_completeness_prefixed_rows_only_after_alias_document_required_surface_exclusion_before_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_SOURCE_POLICY = (
    "local_stale_reasons_only_before_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_PARTITION_POLICY = (
    "local_stale_reasons_partitioned_into_alias_document_contract_row_required_surface_or_unknown_exactly_once_before_violation_projection"
)
REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY = (
    "alias_preempts_document_preempts_required_surface_preempts_contract_row_else_unknown"
)
REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY = (
    "only_nonalias_nondocument_nonrequired_surface_noncontract_row_local_stale_reasons_after_alias_document_required_surface_and_contract_row_resolution_before_violation_projection_remain_unknown"
)
REGISTRY_DIRECT_STALE_REASON_UNCLASSIFIED_POLICY = "fail_closed"
COMPONENT_VALIDATOR_OBSERVATION_REASON_ADMISSION_POLICY = (
    "parse_status_nonzero_rc_or_nonpass_only_before_bundle_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY = (
    "validator_output_missing_invalid_json_not_json_object_status_key_missing_status_literal_not_string_only_before_nonzero_rc_nonpass_status_exclusion_and_bundle_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY = (
    "component_validator_nonzero_rc_only_after_admitted_parse_status_resolution_before_nonpass_status_exclusion_and_bundle_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY = (
    "component_status_not_pass_required_only_after_admitted_parse_status_and_nonzero_rc_resolution_before_explicit_non_execution_exclusion_and_bundle_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY = (
    "validator_output_validator_status_component_status_component_validator_prefixed_rows_only_after_admitted_parse_status_nonzero_rc_nonpass_status_and_exclusion_origin_resolution_before_not_applicable"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY = (
    "only_nonprefixed_nonadmitted_nonexcluded_rows_after_parse_status_nonzero_rc_nonpass_status_exclusion_origin_and_prefixed_ontology_drift_resolution_remain_not_applicable"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY = (
    "parse_status_preempts_nonzero_rc_preempts_nonpass_status_preempts_explicit_non_execution_exclusion_preempts_prefixed_observation_family_ontology_drift_else_not_applicable"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY = (
    "component_validator_missing_or_component_status_row_coverage_incomplete_or_component_validator_contract_surface_or_component_probe_surface_contract_reasons_only_before_bundle_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_POLICY = (
    "non_execution_bundle_rows_remain_outside_observation_reason_ontology"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_SOURCE_POLICY = (
    "bundle_violation_rows_only_before_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_PARTITION_POLICY = (
    "bundle_violation_rows_partitioned_into_admitted_excluded_or_unknown_exactly_once_before_violation_projection"
)
COMPONENT_VALIDATOR_OBSERVATION_REASON_UNCLASSIFIED_POLICY = "fail_closed"
COMPONENT_VALIDATOR_OUTPUT_CONTRACT = "json_object_with_disclosed_status_key"
COMPONENT_PROBE_SHADOW_BOOTSTRAP_CONTRACT = (
    "probe_shadow_common_contract_rows_pass_required_with_bootstrap_and_mirror_bindings"
)
COMPONENT_VALIDATOR_OBSERVATION_EXCLUDED_REASONS = {
    "component_status_row_coverage_incomplete",
    "component_validator_missing",
    "component_validator_root_doc_anchor_status_not_pass_required",
    "component_validator_root_doc_anchor_check_count_invalid",
    "component_validator_row_family_projection_rows_missing_or_invalid",
    "component_validator_row_coverage_status_missing",
    "component_validator_row_coverage_status_not_pass_required",
    "component_validator_row_identity_projection_status_missing",
    "component_validator_row_identity_projection_status_not_pass_required",
    "component_probe_shadow_bootstrap_contract_missing",
    "component_probe_shadow_bootstrap_contract_not_inherited",
}

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

EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS = {
    "explicit_law_bundle_component_row_families": {
        "order": 1,
        "contract_phrase": "required component-row and component-status-row rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_law_bundle_component_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_law_bundle_component_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_law_bundle_component_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize root-law bundle legality while missing or unexpected component identities remain known only internally;",
    },
    "fail_close_preserves_law_bundle_component_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}


EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {'identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md': ('### Root-law bundle must stay explicit and jointly governed',
                                                              '### Root-law bundle component-row completeness must stay explicit',
                                                              'Required component-row and component-status-row families must remain '
                                                              'explicit',
                                                              'README root law-bundle component-row completeness discipline must therefore '
                                                              'stay congruent with admitted law-bundle-component-row-completeness rows '
                                                              'rather than becoming a freehand completeness summary.',
                                                              'Constitutional spine, root admission/governance, source-order, authority,',
                                                              'machine-registry completeness, and conflict precedence are not optional',
                                                              'Weakening one slice while keeping the others green is a root-law coherence',
                                                              'That joint governance also requires descriptor concordance across the '
                                                              'bundle.',
                                                              'Local waiver of descriptor concordance must remain forbidden inside the '
                                                              'bundle.',
                                                              'emitted status-key, or emitted error-code surfaces, the machine world is '
                                                              'being asked',
                                                              'to trust shadow bundle knowledge instead of the admitted family descriptor.',
                                                              'Descriptor concordance must also preserve descriptor-field mode.',
                                                              'validator-emitted status key, or a validator-emitted error-code family, the '
                                                              'machine world is again being asked to',
                                                              'trust shadow bundle semantics instead of the admitted family descriptor.',
                                                              'Bundle descriptor law must also remain inherited from machine-registry',
                                                              'machine-registry completeness field set or field-mode law for '
                                                              'self-describing',
                                                              'bundle schema instead of the admitted registry descriptor law.',
                                                              'The bundle descriptor schema must also stay source-singular.',
                                                              'not a substitute source chosen for local convenience.',
                                                              'Local reauthoring of descriptor schema governance must remain forbidden '
                                                              'inside the bundle.',
                                                              'fail-close rather than locally reconstructing descriptor schema from shadow '
                                                              'bundle knowledge.',
                                                              'Bundle self-describing-family requirement law must also remain inherited '
                                                              'from machine-registry completeness.',
                                                              'The admitted requirement that root mapping families stay self-describing '
                                                              'belongs to that source law rather than to local bundle restatement.',
                                                              'If the admitted source does not disclose that self-describing-family '
                                                              'requirement law, the machine world must fail-close rather than locally '
                                                              'reconstructing self-describing-family legality from bundle convenience.',
                                                              'Bundle descriptor binding must also remain inherited from machine-registry',
                                                              'If the admitted source does not disclose that family-surface binding law, '
                                                              'the machine world must fail-close rather than locally reconstructing '
                                                              'descriptor-family binding legality from bundle convenience.',
                                                              'Local redeclaration of family-surface binding governance must remain '
                                                              'forbidden inside the bundle.',
                                                              'explicit cross-family descriptor-stem binding, the bundle must inherit that',
                                                              'declaration rather than reauthoring, omitting, or locally overriding it.',
                                                              'Bundle descriptor surface-pattern law must also remain inherited from '
                                                              'machine-registry completeness.',
                                                              'inherit those patterns rather than locally redeclaring or loosening them.',
                                                              'fail-close rather than guessing or locally reconstructing descriptor-stem '
                                                              'capture law from bundle convention.',
                                                              'Bundle descriptor repo-relative discipline must also remain inherited from '
                                                              'machine-registry completeness.',
                                                              'Repo-root-relative scope, parent-escape rejection, role-typed path law, and',
                                                              'Local redeclaration of repo-relative discipline governance must remain '
                                                              'forbidden inside the bundle.',
                                                              'fail-close rather than locally reconstructing descriptor path legality from '
                                                              'bundle convenience.',
                                                              'Bundle current/version naming law must also remain inherited from '
                                                              'machine-registry completeness.',
                                                              'Root family prefix, current-entry suffix, active-version regex, and the',
                                                              'Local redeclaration of current/version naming governance must remain '
                                                              'forbidden inside the bundle.',
                                                              'fail-close rather than locally reconstructing current/version mediation '
                                                              'from bundle convention.',
                                                              'Bundle registry-child admission law must also remain inherited from '
                                                              'machine-registry completeness.',
                                                              'canonical registry directory, the admitted registry-current entry, and the',
                                                              'Local redeclaration of registry-child admission governance must remain '
                                                              'forbidden inside the bundle.',
                                                              'fail-close rather than locally reconstructing component admission from '
                                                              'bundle convenience.',
                                                              'Bundle component descriptors must remain current-entry mediated as well.',
                                                              'version file for local convenience.',
                                                              'fail-close rather than bypassing current mediation and binding directly to '
                                                              'a version file.',
                                                              'Bundle component validator verdict law must stay explicit as well.',
                                                              'bound component validator must execute through its disclosed validator '
                                                              'surface',
                                                              'and emit `PASS_REQUIRED` through its disclosed status key for bundle '
                                                              'legality to remain current.',
                                                              'machine world must fail-close rather than treating descriptor concordance '
                                                              'or',
                                                              'file presence as sufficient root-law health.',
                                                              'Bundle component validator execution-failure policy must remain fail-closed '
                                                              'as well.',
                                                              'emits invalid machine output, or omits its disclosed status key, the '
                                                              'machine world must not invent a',
                                                              'substitute verdict from bundle convenience.',
                                                              'Bundle component validator returncode-observation contract must stay '
                                                              'explicit too.',
                                                              'The admitted returncode-observation contract is nonzero returncode observed '
                                                              'without host exception overlay.',
                                                              'The machine world must not let a host-language subprocess helper raise on '
                                                              'nonzero exit, bypass the governed execution-failure policy, or convert host '
                                                              'exception convenience into validator law.',
                                                              'Bundle component validator machine-output contract must stay explicit too.',
                                                              'machine world must consume a bound component validator through structured '
                                                              "machine output carrying the validator's disclosed status key rather than",
                                                              'scraping human-readable logs, prose, or incidental shell text.',
                                                              'Bundle component probe shadow-bootstrap contract must stay explicit too.',
                                                              'The admitted probe shadow-bootstrap contract is '
                                                              '`probe_shadow_common_contract_rows_pass_required_with_bootstrap_and_mirror_bindings`.',
                                                              'machine world must not suppress bootstrap/mirror probe law or reconstruct '
                                                              'it from shell convention.',
                                                              'Bundle component validator invocation contract must stay explicit too.',
                                                              'The admitted invocation contract is `python3 <validator_script> --repo-root '
                                                              '<repo_root> --json-only`.',
                                                              'machine world must not invent an alternate interpreter, drop repo-root '
                                                              'binding, or drop compact machine-output mode for local convenience.',
                                                              'Bundle component validator output-channel contract must stay explicit too.',
                                                              'The admitted verdict-bearing machine-output channel is stdout only.',
                                                              'stderr may carry incidental diagnostics, but it does not become an '
                                                              'alternate status-bearing verdict channel and may not be scraped to replace '
                                                              'missing stdout truth.',
                                                              'Bundle component validator stderr-isolation contract must stay explicit '
                                                              'too.',
                                                              'The admitted stderr-isolation contract is stderr captured separate from '
                                                              'stdout.',
                                                              'machine world must not merge stderr into stdout, let diagnostic text '
                                                              'cohabit the verdict-bearing stream, or treat a merged stream as if it were '
                                                              'governed validator truth.',
                                                              'Bundle component validator stdio text-decoding contract must stay explicit '
                                                              'too.',
                                                              'The admitted stdio text-decoding contract is utf-8 strict text decode with '
                                                              'no locale overlay.',
                                                              'machine world must not let ambient locale choose the decoder, substitute an '
                                                              'alternate codec or replacement policy, or treat locale-shaped text coercion '
                                                              'as if it were governed validator truth.',
                                                              'Bundle component validator stdout-normalization contract must stay explicit '
                                                              'too.',
                                                              'The admitted stdout-normalization contract is outer-whitespace trim only '
                                                              'before JSON decode.',
                                                              'The machine world must not line-scrape, select a preferred line, trim inner '
                                                              'content, or reconstruct JSON from mixed stdout.',
                                                              'Bundle component validator stdout-presence contract must stay explicit too.',
                                                              'The admitted stdout-presence contract is nonempty after outer-whitespace '
                                                              'trim.',
                                                              'The machine world must not treat empty or whitespace-only stdout as '
                                                              'implicit success, an invented empty object, or an advisory no-op verdict '
                                                              'surface.',
                                                              'Bundle component validator stdout-framing contract must stay explicit too.',
                                                              'The admitted stdout framing contract is a single JSON object occupying '
                                                              'whole stdout.',
                                                              'machine world must not line-scrape, trailer-strip, or extract a JSON '
                                                              'fragment from mixed stdout preamble, trailer, or incidental shell text and '
                                                              'then treat that fragment as governed validator truth.',
                                                              'Bundle component validator status-key resolution contract must stay '
                                                              'explicit too.',
                                                              'The admitted status-key resolution contract is top-level direct member '
                                                              'only.',
                                                              'machine world must not search nested objects, alternate key spellings, '
                                                              'alias fields, pointer paths, or other local convenience structures to '
                                                              'reconstruct status truth when the disclosed status key is not present as a '
                                                              'direct top-level member.',
                                                              'Bundle component validator status-literal contract must stay explicit too.',
                                                              'The admitted status-literal contract is exact canonical string literal.',
                                                              'machine world must not trim whitespace, fold case, coerce non-string '
                                                              'values, or map alternate literals onto the admitted status truth when the '
                                                              'validator did not emit the exact canonical status token.',
                                                              'Bundle component validator execution-input contract must stay explicit too.',
                                                              'The admitted execution-input contract is devnull-backed noninteractive '
                                                              'stdin.',
                                                              'machine world must not let a bound validator inherit ambient stdin, block '
                                                              'for operator keystrokes, or convert interactive prompt dialogue into '
                                                              'governed validator execution truth.',
                                                              'Bundle component validator verdict-admission timing contract must stay '
                                                              'explicit too.',
                                                              'The admitted verdict-admission timing contract is completed-process '
                                                              'post-exit only.',
                                                              'machine world must not stream partial stdout into verdict truth, parse a '
                                                              'pre-exit fragment, or treat a background-launched validator as if its '
                                                              'verdict had already been admitted.',
                                                              'Bundle component validator execution-timeout contract must stay explicit '
                                                              'too.',
                                                              'The admitted execution-timeout contract is no local timeout overlay.',
                                                              'machine world must not inject a bundle-local deadline, kill-after policy, '
                                                              'or timeout overlay and then treat timeout-shaped termination as if it were '
                                                              'governed validator law.',
                                                              'Bundle component validator working-directory contract must stay explicit '
                                                              'too.',
                                                              'The admitted validator execution working directory is repo_root.',
                                                              'machine world must not run a bound component validator from arbitrary cwd '
                                                              'or ambient shell location and then treat that convenience execution context '
                                                              'as if it were governed validator law.',
                                                              'Bundle component validator execution-environment contract must stay '
                                                              'explicit too.',
                                                              'The admitted execution-environment contract is inherited parent-process '
                                                              'environment with no local overlay.',
                                                              'machine world must not inject a local env map, scrub inherited variables, '
                                                              'or substitute a shadow environment overlay and then treat that altered '
                                                              'execution context as if it were governed validator law.',
                                                              'Bundle component validator execution-transport contract must stay explicit '
                                                              'too.',
                                                              'The admitted execution transport is local direct subprocess vector '
                                                              'execution.',
                                                              'machine world must not route bound component validator execution through a '
                                                              'shell wrapper, remote hop, or other ambient transport layer and then treat '
                                                              'that transport substitution as if it were governed validator law.',
                                                              'Bundle component validator contract-drift execution policy must stay '
                                                              'explicit too.',
                                                              'The admitted policy is execute under canonical contract and fail-closed on '
                                                              'drift.',
                                                              'The machine world must not obey a drifted disclosed contract row during '
                                                              'validator execution or treat drift-shaped execution as if it were governed '
                                                              'validator law.',
                                                              'Bundle component validator contract-surface projection policy must stay '
                                                              'explicit too.',
                                                              'The admitted policy is bundle summary discloses disclosed contract rows '
                                                              'while component rows disclose effective canonical execution surface.',
                                                              'The machine world must not collapse disclosed drift and effective execution '
                                                              'into a single ambiguous surface or misreport one as the other.',
                                                              'Bundle component validator observation-continuity policy must stay explicit '
                                                              'too.',
                                                              'The admitted policy is continue bound component observation under canonical '
                                                              'surface before final fail-close.',
                                                              'The machine world must not use fail-close drift as a pretext for blind '
                                                              'short-circuit that suppresses bound component observation.',
                                                              'Bundle component status-row coverage policy must stay explicit too.',
                                                              'The admitted policy is every bound component emits one status row before '
                                                              'final status.',
                                                              'The machine world must not finalize root-law bundle truth on partial '
                                                              'component-row coverage when bound component set remains known.',
                                                              'Bundle violation-projection policy must stay explicit too.',
                                                              'The admitted policy is all structure, bundle, and anchor violations are '
                                                              'projected into stale reasons before final status.',
                                                              'The machine world must not keep violation rows internally while emitting a '
                                                              'final verdict surface that withholds their stale-reason projection.',
                                                              'Bundle final-status derivation policy must stay explicit too.',
                                                              'The admitted policy is `PASS_REQUIRED` if and only if stale reasons remain '
                                                              'empty after violation projection; otherwise final status is '
                                                              '`FAIL_REQUIRED`.',
                                                              'The machine world must not derive a clean final verdict from pre-projection '
                                                              'convenience, raw green component counts, or any alternate local verdict '
                                                              'path.',
                                                              'Bundle error-code precedence policy must stay explicit too.',
                                                              'The admitted policy is registry-class failure preempts structure-class '
                                                              'failure, structure-class failure preempts bundle-class failure, and '
                                                              'pass-state emits empty error code.',
                                                              'The machine world must not derive failure code from first local '
                                                              'convenience, last mutation side effect, or any alternate precedence order.',
                                                              'Bundle failure-classification policy must stay explicit too.',
                                                              'The admitted policy is registry class derives from direct stale reasons '
                                                              'present before violation projection, structure class derives from structure '
                                                              'violations, bundle class derives from bundle and anchor violations, and '
                                                              'otherwise failure class is pass.',
                                                              'The machine world must not invent an anchor-only failure class, bypass '
                                                              'direct stale reasons, or classify failure from local convenience surfaces.',
                                                              'Bundle registry-class admission policy must stay explicit too.',
                                                              'The admitted policy is only direct stale reasons already present before '
                                                              'violation projection may admit registry failure class.',
                                                              'Projected structure, bundle, and anchor stale reasons must not '
                                                              'retroactively upgrade failure class to registry.',
                                                              'Bundle registry direct-stale-reason origin policy must stay explicit too.',
                                                              'The admitted origins are alias error, document invalidity, canonical '
                                                              'contract-row invalidity, and required-surface absence, all before violation '
                                                              'projection.',
                                                              'Bundle registry direct-stale-reason alias origin policy must stay explicit '
                                                              'too.',
                                                              'The admitted alias direct stale reasons are rows containing the '
                                                              '`_alias_error:` marker before document, required-surface, and contract-row '
                                                              'classification.',
                                                              'Bundle registry direct-stale-reason document origin policy must stay '
                                                              'explicit too.',
                                                              'The admitted document direct stale reasons are rows ending with '
                                                              '`_empty_or_invalid` after alias exclusion and before required-surface and '
                                                              'contract-row classification.',
                                                              'Bundle registry direct-stale-reason required-surface origin policy must '
                                                              'stay explicit too.',
                                                              'The admitted required-surface direct stale reasons are '
                                                              'required-component-descriptor-fields missing, surface-missing rows, '
                                                              'anchor-checks missing, and components missing before violation projection.',
                                                              'Bundle registry direct-stale-reason contract-row origin policy must stay '
                                                              'explicit too.',
                                                              'The admitted contract-row direct stale reasons are root-corpus-law-bundle '
                                                              'prefixed rows and root-machine-registry-completeness prefixed rows that '
                                                              'remain after alias, document, and required-surface classification.',
                                                              'Bundle registry direct-stale-reason source policy must stay explicit too.',
                                                              'The admitted source is local stale reasons already present before violation '
                                                              'projection.',
                                                              'Projected structure, bundle, and anchor stale reasons do not become '
                                                              'substitute direct stale-reason source.',
                                                              'Bundle registry direct-stale-reason partition policy must stay explicit '
                                                              'too.',
                                                              'Each local stale reason present before violation projection must classify '
                                                              'exactly once as alias, document, contract-row, required-surface, or unknown '
                                                              'ontology drift.',
                                                              'Bundle registry direct-stale-reason origin-classifier precedence policy '
                                                              'must stay explicit too.',
                                                              'Alias classification preempts document classification, document '
                                                              'classification preempts required-surface classification, required-surface '
                                                              'classification preempts contract-row classification, and otherwise origin '
                                                              'remains unknown.',
                                                              'Bundle registry direct-stale-reason unclassified policy must stay explicit '
                                                              'too.',
                                                              'The admitted policy is fail-closed on unclassified direct stale-reason '
                                                              'origin.',
                                                              'The machine world must fail-close on unclassified direct stale-reason '
                                                              'origin rather than silently expanding registry ontology.',
                                                              'Bundle component-validator observation-reason policy must stay explicit '
                                                              'too.',
                                                              'The admitted observation reasons are parse/status failure, nonzero '
                                                              'returncode after admitted parse/status resolution, and non-pass component '
                                                              'status, all before bundle-violation projection.',
                                                              'Bundle component-validator observation-reason classifier precedence policy '
                                                              'must stay explicit too.',
                                                              'Parse/status classification preempts nonzero returncode classification, '
                                                              'nonzero returncode classification preempts non-pass component-status '
                                                              'classification, non-pass component-status classification preempts explicit '
                                                              'non-execution row exclusion, explicit non-execution row exclusion preempts '
                                                              'prefixed observation-family ontology drift, and otherwise classification '
                                                              'remains not-applicable.',
                                                              'Bundle component-validator observation-reason exclusion-origin policy must '
                                                              'stay explicit too.',
                                                              'The admitted excluded non-observation rows are component-validator missing, '
                                                              'component-status-row coverage incomplete, component-validator contract-surface reasons, and '
                                                              'component-probe surface-contract reasons, all before bundle-violation projection.',
                                                              'Observation reasons and prefixed observation-family ontology drift must not '
                                                              'be silently re-bucketed as excluded non-observation rows.',
                                                              'Non-execution bundle rows must remain outside component-validator '
                                                              'observation ontology rather than being silently re-bucketed as observation '
                                                              'reasons.',
                                                              'Bundle component-validator observation-reason source policy must stay '
                                                              'explicit too.',
                                                              'The admitted observation source is bundle-violation rows only, before '
                                                              'violation projection.',
                                                              'Direct stale reasons, structure violations, anchor violations, and '
                                                              'projected stale-reason strings do not become substitute observation source.',
                                                              'Bundle component-validator observation-reason partition policy must stay '
                                                              'explicit too.',
                                                              'Each bundle-violation row must classify exactly once as admitted '
                                                              'observation reason, excluded non-observation row, or unknown ontology '
                                                              'drift, all before violation projection.',
                                                              'Bundle component-validator observation-reason unclassified policy must stay '
                                                              'explicit too.',
                                                              'The admitted policy is fail-closed on unclassified component-validator '
                                                              'observation reason.',
                                                              'The machine world must fail-close on unclassified component-validator '
                                                              'observation reason rather than silently expanding bundle observation '
                                                              'ontology.'),
 'identity/protocol/README.md': ('## Root law-bundle component-row completeness discipline',
                                 'These law-bundle-component-row-completeness rules must remain bound to canonical '
                                 'law-bundle-component-row-completeness rows rather than drifting into soft summary '
                                 'prose.',
                                 '1. required component-row and component-status-row rows must remain explicit as separate '
                                 'machine-readable row families;',
                                 '## Root-law bundle discipline',
                                 'Constitutional spine, root admission/governance, source-order, authority',
                                 'gateway-admissibility, machine-registry completeness, and conflict precedence',
                                 'No single slice is sufficient by itself; the machine world must preserve them as one governed root-law '
                                 'bundle.',
                                 'Bundle membership must also remain descriptor-concordant with the admitted component families it binds.',
                                 'Local waiver of descriptor concordance must remain forbidden inside the bundle.',
                                 "A bundle row may not silently drift from a component family's own disclosed validator, probe, "
                                 'shared-common, emitted status-key, or emitted error-code surfaces.',
                                 'Nor may the bundle silently drift descriptor-field mode:',
                                 'validator-emitted error-code families must remain validator-emitted error-code families.',
                                 'The bundle may not locally reauthor that descriptor schema either; the field',
                                 'admitted machine-registry completeness law for self-describing mapping families.',
                                 "The bundle's descriptor schema must remain source-singular as well.",
                                 'fallback source for convenience.',
                                 'Local reauthoring of descriptor schema governance must remain forbidden inside the bundle.',
                                 'fail-close rather than locally reconstructing descriptor schema.',
                                 'The bundle must also inherit machine-registry completeness self-describing-family requirement law.',
                                 'The admitted requirement that root mapping families stay self-describing may not be silently redeclared, '
                                 'weakened, or guessed inside the bundle.',
                                 'If the admitted source does not disclose that self-describing-family requirement law, the machine world '
                                 'must fail-close rather than locally reconstructing self-describing-family legality.',
                                 'The bundle must also inherit machine-registry completeness family-surface',
                                 'If the admitted source does not disclose that family-surface binding law, the machine world must '
                                 'fail-close rather than locally reconstructing descriptor-family binding legality.',
                                 'Local redeclaration of family-surface binding governance must remain forbidden inside the bundle.',
                                 'explicitly declares a cross-family descriptor-stem binding, the bundle must',
                                 'not locally override or suppress that binding.',
                                 'The bundle must also inherit machine-registry completeness repo-relative',
                                 'inherit those repo-relative path patterns rather than locally redeclaring,',
                                 'fail-close rather than locally reconstructing descriptor-stem capture law.',
                                 'The bundle must also inherit machine-registry completeness repo-relative',
                                 'Repo-root-relative scope, parent-escape rejection, role-typed path law, and',
                                 'Local redeclaration of repo-relative discipline governance must remain forbidden inside the bundle.',
                                 'fail-close rather than locally reconstructing descriptor path legality.',
                                 'The bundle must also inherit machine-registry completeness current/version',
                                 'Root family prefix, current-entry suffix, active-version regex, and the',
                                 'Local redeclaration of current/version naming governance must remain forbidden inside the bundle.',
                                 'fail-close rather than locally reconstructing current/version mediation.',
                                 'The bundle must also inherit machine-registry completeness registry-child',
                                 'canonical registry directory, the admitted registry-current entry, and',
                                 'Local redeclaration of registry-child admission governance must remain forbidden inside the bundle.',
                                 'fail-close rather than locally reconstructing component admission.',
                                 'Bundle component descriptors must also remain current-entry mediated.',
                                 'version truth through those rows, not pin directly to version files.',
                                 'fail-close rather than bypassing current mediation.',
                                 'Bundle component legality must also remain validator-live.',
                                 'Each bound component validator must execute through its disclosed validator',
                                 'surface and emit `PASS_REQUIRED` through its disclosed status key.',
                                 'Descriptor concordance and file presence are not enough if that validator',
                                 'fails execution or emits a weaker verdict.',
                                 'Bundle component validator execution-failure handling must also stay fail-closed.',
                                 'emits invalid machine output, or omits its disclosed status key, runtime may not synthesize a',
                                 'passing verdict from surrounding bundle metadata.',
                                 'Bundle component validators must also keep returncode-observation contract explicit.',
                                 'The admitted validator returncode-observation contract is nonzero returncode observed without host '
                                 'exception overlay.',
                                 'Runtime may not let a host-language subprocess helper raise on nonzero exit, bypass the governed '
                                 'execution-failure policy, or convert host exception convenience into validator truth.',
                                 'Bundle component validators must also remain machine-readable.',
                                 'Runtime consumes them through structured machine output carrying the disclosed status key, not by '
                                 'scraping prose, logs, or incidental terminal text.',
                                 'Bundle component descriptors must also keep probe shadow-bootstrap contract explicit.',
                                 'The admitted component probe shadow-bootstrap contract is '
                                 '`probe_shadow_common_contract_rows_pass_required_with_bootstrap_and_mirror_bindings`.',
                                 'Runtime may not suppress bootstrap/mirror probe law or reconstruct it from shell convention.',
                                 'Bundle component validators must also keep their invocation contract explicit.',
                                 'Bundle legality invokes them as `python3 <validator_script> --repo-root <repo_root> --json-only`.',
                                 'Runtime may not swap interpreter, omit repo-root binding, or omit compact machine-output mode.',
                                 'Bundle component validators must also keep output-channel contract explicit.',
                                 'The verdict-bearing machine-output channel is stdout only.',
                                 'stderr diagnostics do not become an alternate status-bearing channel and may not replace missing stdout '
                                 'truth.',
                                 'Bundle component validators must also keep stderr-isolation contract explicit.',
                                 'The admitted stderr channel remains separately captured from verdict-bearing stdout.',
                                 'Runtime may not merge stderr into stdout or treat a mixed stream as admitted validator truth.',
                                 'Bundle component validators must also keep stdio text-decoding contract explicit.',
                                 'The admitted validator stdio text-decoding contract is utf-8 strict text decode with no locale overlay.',
                                 'Runtime may not let ambient locale choose the decoder, substitute an alternate codec or replacement '
                                 'policy, or treat locale-shaped text coercion as admitted validator truth.',
                                 'Bundle component validators must also keep stdout-normalization contract explicit.',
                                 'The admitted validator stdout-normalization contract is outer-whitespace trim only before JSON decode.',
                                 'Runtime may not line-scrape, select a preferred line, trim inner content, or reconstruct JSON from mixed '
                                 'stdout.',
                                 'Bundle component validators must also keep stdout-presence contract explicit.',
                                 'The admitted validator stdout-presence contract is nonempty after outer-whitespace trim.',
                                 'Runtime may not treat empty or whitespace-only stdout as implicit success, an invented empty object, or '
                                 'an advisory no-op verdict surface.',
                                 'Bundle component validators must also keep stdout-framing contract explicit.',
                                 'The verdict-bearing machine output occupies whole stdout as a single JSON object.',
                                 'Runtime may not line-scrape, trailer-strip, or extract a JSON fragment from mixed stdout preamble, '
                                 'trailer, or incidental shell text.',
                                 'Bundle component validators must also keep status-key resolution contract explicit.',
                                 'The disclosed status key is resolved only as a direct top-level member of the verdict-bearing JSON '
                                 'object.',
                                 'Runtime may not search nested objects, alias keys, pointer paths, or other local convenience structures '
                                 'to recover missing status truth.',
                                 'Bundle component validators must also keep status-literal contract explicit.',
                                 'The disclosed status value is admitted only as the exact canonical string literal.',
                                 'Runtime may not trim whitespace, fold case, coerce non-string values, or map alternate literals into '
                                 'admitted status truth.',
                                 'Bundle component validators must also keep execution-input contract explicit.',
                                 'The admitted validator execution input is devnull-backed noninteractive stdin.',
                                 'Runtime may not let bound validators inherit ambient stdin, wait for operator keystrokes, or convert '
                                 'interactive prompt dialogue into validator truth.',
                                 'Bundle component validators must also keep verdict-admission timing contract explicit.',
                                 'The admitted validator verdict is consumed only after completed process exit.',
                                 'Runtime may not stream partial stdout into verdict truth, parse pre-exit fragments, or treat '
                                 'background-launched validators as already admitted.',
                                 'Bundle component validators must also keep execution-timeout contract explicit.',
                                 'The admitted validator execution-timeout contract is no local timeout overlay.',
                                 'Runtime may not inject a bundle-local deadline, kill-after policy, or timeout overlay and then treat '
                                 'timeout-shaped termination as admitted validator truth.',
                                 'Bundle component validators must also keep working-directory contract explicit.',
                                 'The admitted validator execution working directory is repo_root.',
                                 'Runtime may not substitute arbitrary cwd or ambient shell location for that governed execution context.',
                                 'Bundle component validators must also keep execution-environment contract explicit.',
                                 'The admitted validator execution environment is the inherited parent-process environment with no local '
                                 'overlay.',
                                 'Runtime may not inject a local env map, scrub inherited variables, or substitute a shadow environment '
                                 'overlay for that governed execution context.',
                                 'Bundle component validators must also keep execution-transport contract explicit.',
                                 'The admitted transport is local direct subprocess vector execution.',
                                 'Runtime may not substitute shell mediation, remote hop, or other ambient transport for that governed '
                                 'execution path.',
                                 'Bundle component validators must also keep contract-drift execution policy explicit.',
                                 'The admitted validator policy is execute under canonical contract and fail-closed on drift.',
                                 'Runtime may not obey a drifted disclosed contract row during validator execution or treat drift-shaped '
                                 'execution as admitted validator truth.',
                                 'Bundle component validators must also keep contract-surface projection policy explicit.',
                                 'The admitted validator surface split is disclosed bundle summary plus effective component execution '
                                 'rows.',
                                 'Runtime may not hide disclosed drift by rewriting summary to canonical values or project drifted '
                                 'declared rows as applied execution truth.',
                                 'Bundle component validators must also keep observation-continuity policy explicit.',
                                 'The admitted runtime policy is continue bound component observation under canonical surface before final '
                                 'fail-close.',
                                 'Runtime may not use bundle drift as a reason to suppress otherwise bindable component observation before '
                                 'final verdict.',
                                 'Bundle component status-row coverage policy must also stay explicit.',
                                 'The admitted runtime policy is every bound component emits one status row before final status.',
                                 'Runtime may not finalize on partial component-row coverage when the bound component set is already '
                                 'known.',
                                 'Bundle violation-projection policy must also stay explicit.',
                                 'The admitted runtime policy is all structure, bundle, and anchor violations are projected into stale '
                                 'reasons before final status.',
                                 'Runtime may not keep violation rows private while presenting a final verdict surface that withholds '
                                 'their stale-reason projection.',
                                 'Bundle final-status derivation policy must also stay explicit.',
                                 'The admitted runtime policy is `PASS_REQUIRED` if and only if stale reasons remain empty after violation '
                                 'projection; otherwise final status is `FAIL_REQUIRED`.',
                                 'Runtime may not derive a clean final verdict from pre-projection convenience, raw green component '
                                 'counts, or any alternate local verdict path.',
                                 'Bundle error-code precedence policy must also stay explicit.',
                                 'The admitted runtime policy is registry-class failure preempts structure-class failure, structure-class '
                                 'failure preempts bundle-class failure, and pass-state emits empty error code.',
                                 'Runtime may not derive failure code from first local convenience, last mutation side effect, or any '
                                 'alternate precedence order.',
                                 'Bundle failure-classification policy must also stay explicit.',
                                 'The admitted runtime policy is registry class derives from direct stale reasons present before violation '
                                 'projection, structure class derives from structure violations, bundle class derives from bundle and '
                                 'anchor violations, and otherwise failure class is pass.',
                                 'Runtime may not invent an anchor-only failure class, bypass direct stale reasons, or classify failure '
                                 'from local convenience surfaces.',
                                 'Bundle registry-class admission policy must also stay explicit.',
                                 'The admitted runtime policy is only direct stale reasons already present before violation projection may '
                                 'admit registry failure class.',
                                 'Projected structure, bundle, and anchor stale reasons must not retroactively upgrade failure class to '
                                 'registry.',
                                 'Bundle registry direct-stale-reason origin policy must also stay explicit.',
                                 'The admitted runtime origins are alias error, document invalidity, canonical contract-row invalidity, '
                                 'and required-surface absence, all before violation projection.',
                                 'Bundle registry direct-stale-reason alias origin policy must also stay explicit.',
                                 'The admitted runtime alias direct stale reasons are rows containing the `_alias_error:` marker before '
                                 'document, required-surface, and contract-row classification.',
                                 'Bundle registry direct-stale-reason document origin policy must also stay explicit.',
                                 'The admitted runtime document direct stale reasons are rows ending with `_empty_or_invalid` after alias '
                                 'exclusion and before required-surface and contract-row classification.',
                                 'Bundle registry direct-stale-reason required-surface origin policy must also stay explicit.',
                                 'The admitted runtime required-surface direct stale reasons are required-component-descriptor-fields '
                                 'missing, surface-missing rows, anchor-checks missing, and components missing before violation '
                                 'projection.',
                                 'Bundle registry direct-stale-reason contract-row origin policy must also stay explicit.',
                                 'The admitted runtime contract-row direct stale reasons are root-corpus-law-bundle prefixed rows and '
                                 'root-machine-registry-completeness prefixed rows that remain after alias, document, and required-surface '
                                 'classification.',
                                 'Bundle registry direct-stale-reason source policy must also stay explicit.',
                                 'The admitted runtime source is local stale reasons already present before violation projection.',
                                 'Projected structure, bundle, and anchor stale reasons do not become substitute direct stale-reason '
                                 'source.',
                                 'Bundle registry direct-stale-reason partition policy must also stay explicit.',
                                 'Each local stale reason present before violation projection must classify exactly once as alias, '
                                 'document, contract-row, required-surface, or unknown ontology drift.',
                                 'Bundle registry direct-stale-reason origin-classifier precedence policy must also stay explicit.',
                                 'Alias runtime classification preempts document classification, document classification preempts '
                                 'required-surface classification, required-surface classification preempts contract-row classification, '
                                 'and otherwise runtime origin remains unknown.',
                                 'Bundle registry direct-stale-reason unclassified policy must also stay explicit.',
                                 'The admitted runtime policy is fail-closed on unclassified direct stale-reason origin.',
                                 'Runtime must fail-close on unclassified direct stale-reason origin rather than silently expanding '
                                 'registry ontology.',
                                 'Bundle component-validator observation-reason policy must also stay explicit.',
                                 'The admitted runtime observation reasons are parse/status failure, nonzero returncode after admitted '
                                 'parse/status resolution, and non-pass component status, all before bundle-violation projection.',
                                 'Bundle component-validator observation-reason classifier precedence policy must also stay explicit.',
                                 'Parse/status runtime classification preempts nonzero returncode classification, nonzero returncode '
                                 'classification preempts non-pass component-status classification, non-pass component-status '
                                 'classification preempts explicit non-execution row exclusion, explicit non-execution row exclusion '
                                 'preempts prefixed observation-family ontology drift, and otherwise runtime classification remains '
                                 'not-applicable.',
                                 'Bundle component-validator observation-reason exclusion-origin policy must also stay explicit.',
                                 'The admitted excluded runtime non-observation rows are component-validator missing, '
                                 'component-status-row coverage incomplete, component-validator contract-surface reasons, and '
                                 'component-probe surface-contract reasons, all before bundle-violation projection.',
                                 'Runtime observation reasons and prefixed observation-family ontology drift must not be silently '
                                 're-bucketed as excluded non-observation rows.',
                                 'Non-execution bundle rows must remain outside component-validator observation ontology rather than being '
                                 'silently re-bucketed as runtime observation reasons.',
                                 'Bundle component-validator observation-reason source policy must also stay explicit.',
                                 'The admitted runtime observation source is bundle-violation rows only, before violation projection.',
                                 'Direct stale reasons, structure violations, anchor violations, and projected stale-reason strings do not '
                                 'become substitute runtime observation source.',
                                 'Bundle component-validator observation-reason partition policy must also stay explicit.',
                                 'Each bundle-violation row must classify exactly once as admitted runtime observation reason, excluded '
                                 'non-observation row, or unknown ontology drift, all before violation projection.',
                                 'Bundle component-validator observation-reason unclassified policy must also stay explicit.',
                                 'The admitted runtime policy is fail-closed on unclassified component-validator observation reason.',
                                 'Runtime must fail-close on unclassified component-validator observation reason rather than silently '
                                 'expanding bundle observation ontology.'),
 'identity/protocol/IDENTITY_PROTOCOL.md': ('## Root law-bundle component-row completeness boundary',
                                            '1. Root-law bundle coherence must remain machine-readable as separate component-row and '
                                            'component-status-row families.',
                                            '6. README root law-bundle component-row completeness discipline rendered at '
                                            'protocol root must remain congruent with admitted '
                                            'law-bundle-component-row-completeness rows rather than silently authoring an '
                                            'alternate completeness summary.',
                                            '## Root-law bundle boundary',
                                            '1. constitutional spine;',
                                            '9. machine-registry completeness;',
                                            'Strengthening one slice must not silently weaken or bypass another; any',
                                            'Root-law bundle rows must also remain descriptor-concordant with the active',
                                            "component family's own disclosed validator/probe/common/status-key/error-code surfaces.",
                                            "Root-law bundle rows must also preserve each bound component family's disclosed probe "
                                            'shadow-bootstrap contract; bundle metadata may not suppress bootstrap/mirror binding law '
                                            'or demote it into shell convention.',
                                            'Local waiver of descriptor concordance must remain forbidden inside the bundle.',
                                            'Root-law bundle rows must also preserve descriptor-field mode; a repo-relative',
                                            'validator-emitted status-key/error-code fields may not be reinterpreted as ordinary path '
                                            'strings.',
                                            'The bundle must not locally reauthor the self-describing descriptor schema',
                                            'descriptor-field modes must remain aligned with root machine-registry completeness law.',
                                            "The bundle's descriptor schema must stay source-singular",
                                            'no substitute source, and no fallback source.',
                                            'Local reauthoring of descriptor schema governance must remain forbidden inside the bundle.',
                                            'fail-close rather than locally reconstructing descriptor schema.',
                                            'The bundle must also inherit machine-registry completeness self-describing-family requirement '
                                            'law; the admitted requirement that law-bearing root mapping families stay self-describing may '
                                            'not be silently redeclared, weakened, or guessed inside the bundle.',
                                            'If the admitted source does not disclose that self-describing-family requirement law, '
                                            'protocol legality must fail-close rather than locally reconstructing self-describing-family '
                                            'legality.',
                                            'The bundle must also inherit machine-registry completeness family-surface binding law',
                                            'If the admitted source does not disclose that family-surface binding law, protocol legality '
                                            'must fail-close rather than locally reconstructing descriptor-family binding legality.',
                                            'Local redeclaration of family-surface binding governance must remain forbidden inside the '
                                            'bundle.',
                                            'explicit cross-family descriptor-stem bindings declared there may not be silently reauthored, '
                                            'suppressed, or replaced by local bundle convenience.',
                                            'The bundle must also inherit machine-registry completeness repo-relative',
                                            'descriptor path-pattern law; descriptor-stem capture patterns for validator,',
                                            'fail-close rather than locally reconstructing descriptor-surface pattern law.',
                                            'The bundle must also inherit machine-registry completeness repo-relative',
                                            'descriptor discipline law; repo-root-relative scope, parent-escape rejection,',
                                            'Local redeclaration of repo-relative discipline governance must remain forbidden inside the '
                                            'bundle.',
                                            'protocol legality must fail-close rather than locally reconstructing descriptor-path legality '
                                            'law.',
                                            'The bundle must also inherit machine-registry completeness current/version',
                                            'naming law; root family prefix, current-entry suffix, active-version regex,',
                                            'Local redeclaration of current/version naming governance must remain forbidden inside the '
                                            'bundle.',
                                            'protocol legality must fail-close rather than locally reconstructing current/version '
                                            'mediation law.',
                                            'The bundle must also inherit machine-registry completeness registry-child',
                                            'admission law; canonical registry directory, admitted registry-current entry,',
                                            'Local redeclaration of registry-child admission governance must remain forbidden inside the '
                                            'bundle.',
                                            'protocol legality must fail-close rather than locally reconstructing component-admission law.',
                                            'Bundle component descriptors must also stay current-entry mediated',
                                            'not direct version-file pinning.',
                                            'fail-close rather than bypassing current mediation.',
                                            'Root-law bundle rows must also remain validator-live; each bound component',
                                            'validator must execute through its disclosed validator surface and emit',
                                            '`PASS_REQUIRED` through its disclosed status key.',
                                            'Descriptor concordance or file presence may not override a non-passing',
                                            'component validator verdict.',
                                            'Root-law bundle rows must also keep component validator execution-failure policy fail-closed; '
                                            'missing execution, nonzero exit, invalid machine output,',
                                            'or missing disclosed status key may not be downgraded into advisory noise.',
                                            'Root-law bundle rows must also keep component validator returncode-observation contract '
                                            'explicit; nonzero returncode is observed without host exception overlay inside the bundle.',
                                            'Local substitution of host-language exception raising for governed nonzero returncode '
                                            'handling is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator machine-output contract explicit; '
                                            'bundle legality consumes structured machine output carrying',
                                            'the disclosed status key, not human-readable logs or incidental shell text.',
                                            'Root-law bundle rows must also keep component validator invocation contract explicit; bundle '
                                            'legality invokes the disclosed validator surface as `python3 <validator_script> --repo-root '
                                            '<repo_root> --json-only`.',
                                            'Local substitution of interpreter, repo-root binding, or compact machine-output mode is '
                                            'forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator output-channel contract explicit; the '
                                            'disclosed validator verdict is consumed from stdout only.',
                                            'stderr diagnostics must not be promoted into an alternate status-bearing verdict channel '
                                            'inside the bundle.',
                                            'Root-law bundle rows must also keep component validator stderr-isolation contract explicit; '
                                            'stderr remains separately captured from verdict-bearing stdout.',
                                            'Local merging of stderr into stdout or admission of a mixed stream is forbidden inside the '
                                            'bundle.',
                                            'Root-law bundle rows must also keep component validator stdout-normalization contract '
                                            'explicit; only outer-whitespace trim may occur before JSON decode inside the bundle.',
                                            'Local line selection, inner-content trimming, or JSON reconstruction from mixed stdout is '
                                            'forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator stdout-presence contract explicit; '
                                            'bound component validator stdout must remain nonempty after outer-whitespace trim.',
                                            'Local treatment of empty or whitespace-only stdout as implicit success, an invented empty '
                                            'object, or advisory silence is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator stdout-framing contract explicit; '
                                            'bound component validator verdict is consumed only when whole stdout is a single JSON object '
                                            'carrying the disclosed status key.',
                                            'Local extraction of a JSON fragment from mixed stdout preamble, trailer, or incidental shell '
                                            'text is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator status-key resolution contract '
                                            'explicit; the disclosed status key is resolved only as a direct top-level member of the '
                                            'admitted verdict object.',
                                            'Local search across nested objects, alias keys, pointer paths, or other convenience '
                                            'structures is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator status-literal contract explicit; the '
                                            'disclosed status value is admitted only as the exact canonical string literal.',
                                            'Local trimming, case-folding, non-string coercion, or alternate-literal mapping is forbidden '
                                            'inside the bundle.',
                                            'Root-law bundle rows must also keep component validator execution-input contract explicit; '
                                            'bound component validators execute with devnull-backed noninteractive stdin.',
                                            'Local inheritance of ambient stdin or dependence on operator keystrokes is forbidden inside '
                                            'the bundle.',
                                            'Root-law bundle rows must also keep component validator verdict-admission timing contract '
                                            'explicit; bound component validator verdict is admitted only after completed process exit.',
                                            'Local streaming of partial stdout, pre-exit parsing, or background-process substitution is '
                                            'forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator execution-timeout contract explicit; '
                                            'bound component validators execute with no local timeout overlay inside the bundle.',
                                            'Local injection of deadlines, kill-after policies, or timeout overlays is forbidden inside '
                                            'the bundle.',
                                            'Root-law bundle rows must also keep component validator working-directory contract explicit; '
                                            'bound component validators execute with repo_root as the governed working directory.',
                                            'Local substitution of arbitrary cwd or ambient shell location is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator execution-environment contract '
                                            'explicit; bound component validators execute with inherited parent-process environment and no '
                                            'local overlay.',
                                            'Local injection of env maps, scrubbing of inherited variables, or shadow environment overlay '
                                            'is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator execution-transport contract '
                                            'explicit; bound component validators execute through local direct subprocess vector '
                                            'transport.',
                                            'Local substitution of shell mediation, remote hop, or other ambient transport is forbidden '
                                            'inside the bundle.',
                                            'Root-law bundle rows must also keep component validator contract-drift execution policy '
                                            'explicit; bound component validators execute under canonical contract and fail-closed on '
                                            'drift.',
                                            'Local obedience to a drifted disclosed contract row or admission of drift-shaped execution is '
                                            'forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator contract-surface projection policy '
                                            'explicit; bundle summary discloses declared contract rows while component rows disclose '
                                            'effective canonical execution surface.',
                                            'Local collapse of disclosed drift and effective execution or projection of one as the other '
                                            'is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component validator observation-continuity policy '
                                            'explicit; once bound component surfaces resolve, component observation continues under '
                                            'canonical surface before final fail-close.',
                                            'Local short-circuit that suppresses bound component observation merely because a bundle '
                                            'contract row drifted is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep component status-row coverage policy explicit; every '
                                            'bound component must emit one status row before final status.',
                                            'Local finalization on partial component-row coverage is forbidden inside the bundle.',
                                            'Root-law bundle rows must also keep violation-projection policy explicit; all structure, '
                                            'bundle, and anchor violations must be projected into stale reasons before final status.',
                                            'Local final verdict must not withhold stale-reason projection for known violation rows.',
                                            'Root-law bundle rows must also keep final-status derivation policy explicit; final status is '
                                            '`PASS_REQUIRED` if and only if stale reasons remain empty after violation projection; '
                                            'otherwise final status is `FAIL_REQUIRED`.',
                                            'Local verdict path must not bypass stale-reason-adjudicated final status.',
                                            'Root-law bundle rows must also keep error-code precedence policy explicit; registry-class '
                                            'failure preempts structure-class failure, structure-class failure preempts bundle-class '
                                            'failure, and pass-state emits empty error code.',
                                            'Local error-code derivation must not bypass precedence-adjudicated failure classification.',
                                            'Root-law bundle rows must also keep failure-classification policy explicit; registry class '
                                            'derives from direct stale reasons present before violation projection, structure class '
                                            'derives from structure violations, bundle class derives from bundle and anchor violations, '
                                            'and otherwise failure class is pass.',
                                            'Local classification path must not invent an anchor-only failure class or bypass direct stale '
                                            'reasons.',
                                            'Root-law bundle rows must also keep registry-class admission policy explicit; only direct '
                                            'stale reasons already present before violation projection may admit registry failure class.',
                                            'Projected violation reasons must not be reclassified as registry failure basis.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason origin policy explicit; '
                                            'admitted direct origins are alias error, document invalidity, canonical contract-row '
                                            'invalidity, and required-surface absence before violation projection.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason alias origin policy '
                                            'explicit; admitted alias direct reasons are rows containing the `_alias_error:` marker before '
                                            'document, required-surface, and contract-row classification.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason document origin policy '
                                            'explicit; admitted document direct reasons are rows ending with `_empty_or_invalid` after '
                                            'alias exclusion and before required-surface and contract-row classification.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason required-surface origin '
                                            'policy explicit; admitted required-surface direct reasons are '
                                            'required-component-descriptor-fields missing, surface-missing rows, anchor-checks missing, '
                                            'and components missing before violation projection.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason contract-row origin policy '
                                            'explicit; admitted contract-row direct reasons are root-corpus-law-bundle prefixed rows and '
                                            'root-machine-registry-completeness prefixed rows that remain after alias, document, and '
                                            'required-surface classification.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason source policy explicit; '
                                            'direct stale-reason source is local stale reasons already present before violation '
                                            'projection.',
                                            'Projected structure, bundle, and anchor stale reasons must not be reinterpreted as direct '
                                            'stale-reason source.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason partition policy explicit; '
                                            'each local stale reason present before violation projection classifies exactly once as alias, '
                                            'document, contract-row, required-surface, or unknown ontology drift.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason origin-classifier precedence '
                                            'policy explicit; alias classification preempts document, document preempts required-surface, '
                                            'required-surface preempts contract-row, and otherwise origin remains unknown.',
                                            'Root-law bundle rows must also keep registry direct-stale-reason unclassified policy '
                                            'explicit; unclassified direct stale-reason origin must remain fail-closed.',
                                            'Local direct stale-reason ontology must not silently expand beyond those admitted origins.',
                                            'Root-law bundle rows must also keep component-validator observation-reason policy explicit; '
                                            'admitted observation reasons are parse/status failure, nonzero returncode after admitted '
                                            'parse/status resolution, and non-pass component status before bundle-violation projection.',
                                            'Root-law bundle rows must also keep component-validator observation-reason classifier '
                                            'precedence policy explicit; parse/status classification preempts nonzero returncode, nonzero '
                                            'returncode preempts non-pass component status, non-pass component status preempts explicit '
                                            'non-execution exclusion, explicit non-execution exclusion preempts prefixed '
                                            'observation-family ontology drift, and otherwise classification remains not-applicable.',
                                            'Root-law bundle rows must also keep component-validator observation-reason exclusion-origin '
                                            'policy explicit; admitted excluded non-observation rows are component-validator missing, '
                                            'component-status-row coverage incomplete, component-validator contract-surface reasons, '
                                            'and component-probe surface-contract reasons before bundle-violation projection.',
                                            'Local bundle law must not silently re-bucket admitted observation reasons or prefixed '
                                            'observation-family ontology drift as excluded non-observation rows.',
                                            'Local bundle law must keep non-execution bundle rows outside component-validator observation '
                                            'ontology.',
                                            'Root-law bundle rows must also keep component-validator observation-reason source policy '
                                            'explicit; observation source is bundle-violation rows only before violation projection.',
                                            'Direct stale reasons, structure violations, anchor violations, and projected stale-reason '
                                            'strings must not be reinterpreted as observation source.',
                                            'Root-law bundle rows must also keep component-validator observation-reason partition policy '
                                            'explicit; each bundle-violation row classifies exactly once as admitted observation reason, '
                                            'excluded non-observation row, or unknown ontology drift before violation projection.',
                                            'Root-law bundle rows must also keep component-validator observation-reason unclassified '
                                            'policy explicit; unclassified observation reason must remain fail-closed.',
                                            'Local bundle observation ontology must not silently expand beyond those admitted '
                                            'component-validator observation reasons.'),
 'identity/protocol/IDENTITY_RUNTIME.md': ('## Runtime law-bundle component-row consumption boundary',
                                           '1. Runtime consumes root-law bundle coherence as separate component-row and '
                                           'component-status-row families rather than as undifferentiated bundle prose.',
                                           '6. Runtime consumes README root law-bundle component-row completeness '
                                           'discipline as a governed completeness projection bound to admitted '
                                           'law-bundle-component-row-completeness rows rather than as a freehand '
                                           'completeness summary.',
                                           '## Runtime consumption of the root-law bundle',
                                           'constitutional spine, admission/governance, ordering, authority, question-routing,',
                                           'machine-registry completeness,',
                                           'Runtime must not select the most convenient slice in isolation.',
                                           'Runtime must also reject a root-law bundle row whose '
                                           'validator/probe/common/status-key/error-code',
                                           'surfaces drift from the active component descriptor it claims to bind.',
                                           'Runtime must also reject a root-law bundle row whose bound component suppresses or weakens '
                                           'its disclosed probe shadow-bootstrap contract; bootstrap/mirror probe law may not be '
                                           'reconstructed from shell convention.',
                                           'Runtime must also reject local waiver of descriptor concordance inside the bundle.',
                                           'Runtime must also reject a root-law bundle row whose descriptor-field mode',
                                           'error-code family.',
                                           'Runtime must also reject a root-law bundle whose descriptor schema diverges',
                                           'descriptor-field mode map.',
                                           'Runtime must also treat bundle descriptor schema as source-singular',
                                           'no substitute source, and no fallback source.',
                                           'Runtime must also reject local reauthoring of descriptor schema governance inside the bundle.',
                                           'locally reconstructing descriptor schema.',
                                           'Runtime must also reject a root-law bundle that redeclares or weakens machine-registry '
                                           'completeness self-describing-family requirement law; the admitted requirement that law-bearing '
                                           'root mapping families stay self-describing must be inherited from the admitted source '
                                           'component.',
                                           'If the admitted source does not disclose that self-describing-family requirement law, runtime '
                                           'must fail-close rather than locally reconstructing self-describing-family legality law.',
                                           'Runtime must also reject a root-law bundle that locally overrides or suppresses',
                                           'If the admitted source does not disclose that family-surface binding law, runtime must '
                                           'fail-close rather than locally reconstructing descriptor-family binding legality law.',
                                           'Runtime must also reject local redeclaration of family-surface binding governance inside the '
                                           'bundle.',
                                           'explicit cross-family descriptor-stem bindings must be inherited from the admitted source '
                                           'component rather than guessed.',
                                           'Runtime must also reject a root-law bundle that redeclares or loosens',
                                           'descriptor-stem capture patterns for validator/probe/shared-common surfaces',
                                           'fail-close rather than locally reconstructing descriptor-surface pattern law.',
                                           'Runtime must also reject a root-law bundle that redeclares or weakens',
                                           'scope, parent-escape rejection, role-typed path classes, and cross-role',
                                           'Runtime must also reject local redeclaration of repo-relative discipline governance inside the '
                                           'bundle.',
                                           'runtime must fail-close rather than locally reconstructing descriptor-path legality law.',
                                           'Runtime must also reject a root-law bundle that redeclares or weakens',
                                           'current-entry suffix, active-version regex, and current/version pair',
                                           'Runtime must also reject local redeclaration of current/version naming governance inside the '
                                           'bundle.',
                                           'fail-close rather than locally reconstructing current/version mediation law.',
                                           'Runtime must also reject a root-law bundle that redeclares or weakens',
                                           'canonical registry directory, admitted registry-current entry, and registered child-set',
                                           'Runtime must also reject local redeclaration of registry-child admission governance inside the '
                                           'bundle.',
                                           'runtime must fail-close rather than locally reconstructing component-admission law.',
                                           'Runtime must also treat bundle component descriptors as current-entry mediated',
                                           'not direct version-file pinning.',
                                           'fail-close rather than bypassing current mediation.',
                                           'Runtime must also require each bound component validator to execute through',
                                           'its disclosed validator surface and emit `PASS_REQUIRED` through its',
                                           'disclosed status key.',
                                           'Runtime must fail-close on validator execution failure, nonzero exit, or any',
                                           'emitted status other than `PASS_REQUIRED`.',
                                           'Runtime must also keep validator execution-failure handling fail-closed;',
                                           'invalid machine output, or omission of the disclosed status key may not be repaired by local '
                                           'inference.',
                                           'Runtime must also keep bound component validator returncode-observation contract explicit; '
                                           'runtime observes nonzero returncode without host exception overlay.',
                                           'Runtime must not let a host-language subprocess helper raise on nonzero exit, bypass the '
                                           'governed execution-failure policy, or convert host exception convenience into admitted '
                                           'validator truth.',
                                           'Runtime must also require a structured machine-output contract for bound component validators; '
                                           'runtime consumes the disclosed status key from machine',
                                           'output rather than scraping logs or incidental shell text.',
                                           'Runtime must also keep bound component validator invocation contract explicit; runtime invokes '
                                           'the disclosed validator surface as `python3 <validator_script> --repo-root <repo_root> '
                                           '--json-only`.',
                                           'Runtime must not substitute a different interpreter, omit repo-root binding, or omit compact '
                                           'machine-output mode.',
                                           'Runtime must also keep bound component validator output-channel contract explicit; runtime '
                                           'consumes the verdict-bearing machine output from stdout only.',
                                           'Runtime must not elevate stderr diagnostics into an alternate status-bearing channel or use '
                                           'them to replace missing stdout truth.',
                                           'Runtime must also keep bound component validator stderr-isolation contract explicit; runtime '
                                           'captures stderr separately from verdict-bearing stdout.',
                                           'Runtime must not merge stderr into stdout or treat a mixed stream as admitted validator truth.',
                                           'Runtime must also keep bound component validator stdio text-decoding contract explicit; '
                                           'runtime executes bound component validators with utf-8 strict text decode and no locale '
                                           'overlay.',
                                           'Runtime must not let ambient locale choose the decoder, substitute an alternate codec or '
                                           'replacement policy, or treat locale-shaped text coercion as admitted validator truth.',
                                           'Runtime must also keep bound component validator stdout-normalization contract explicit; '
                                           'runtime applies only outer-whitespace trim before JSON decode.',
                                           'Runtime must not line-scrape, select a preferred line, trim inner content, or reconstruct JSON '
                                           'from mixed stdout.',
                                           'Runtime must also keep bound component validator stdout-presence contract explicit; runtime '
                                           'requires nonempty stdout after outer-whitespace trim.',
                                           'Runtime must not treat empty or whitespace-only stdout as implicit success, an invented empty '
                                           'object, or an advisory no-op verdict surface.',
                                           'Runtime must also keep bound component validator stdout-framing contract explicit; runtime '
                                           'parses whole stdout as a single JSON object carrying the disclosed status key.',
                                           'Runtime must not line-scrape, trailer-strip, or extract a JSON fragment from mixed stdout '
                                           'preamble, trailer, or incidental shell text.',
                                           'Runtime must also keep bound component validator status-key resolution contract explicit; '
                                           'runtime resolves the disclosed status key only as a direct top-level member of the admitted '
                                           'verdict object.',
                                           'Runtime must not search nested objects, alias keys, pointer paths, or other local convenience '
                                           'structures to reconstruct missing status truth.',
                                           'Runtime must also keep bound component validator status-literal contract explicit; runtime '
                                           'admits the disclosed status value only as the exact canonical string literal.',
                                           'Runtime must not trim whitespace, fold case, coerce non-string values, or map alternate '
                                           'literals into admitted status truth.',
                                           'Runtime must also keep bound component validator execution-input contract explicit; runtime '
                                           'executes bound component validators with devnull-backed noninteractive stdin.',
                                           'Runtime must not let bound validators inherit ambient stdin, wait for operator keystrokes, or '
                                           'convert interactive prompt dialogue into admitted validator execution truth.',
                                           'Runtime must also keep bound component validator verdict-admission timing contract explicit; '
                                           'runtime admits validator verdict only after completed process exit.',
                                           'Runtime must not stream partial stdout into verdict truth, parse pre-exit fragments, or treat '
                                           'background-launched validators as already admitted.',
                                           'Runtime must also keep bound component validator execution-timeout contract explicit; runtime '
                                           'executes bound component validators with no local timeout overlay inside the bundle.',
                                           'Runtime must not inject a bundle-local deadline, kill-after policy, or timeout overlay and '
                                           'then treat timeout-shaped termination as admitted validator truth.',
                                           'Runtime must also keep bound component validator working-directory contract explicit; runtime '
                                           'executes bound component validators with repo_root as the governed working directory.',
                                           'Runtime must not substitute arbitrary cwd or ambient shell location for that governed '
                                           'execution context.',
                                           'Runtime must also keep bound component validator execution-environment contract explicit; '
                                           'runtime executes bound component validators with inherited parent-process environment and no '
                                           'local overlay.',
                                           'Runtime must not inject a local env map, scrub inherited variables, or substitute a shadow '
                                           'environment overlay for that governed execution context.',
                                           'Runtime must also keep bound component validator execution-transport contract explicit; '
                                           'runtime executes bound component validators through local direct subprocess vector transport.',
                                           'Runtime must not substitute shell mediation, remote hop, or other ambient transport for that '
                                           'governed execution path.',
                                           'Runtime must also keep bound component validator contract-drift execution policy explicit; '
                                           'runtime executes under canonical contract and fail-closed on drift.',
                                           'Runtime must not obey a drifted disclosed contract row during validator execution or treat '
                                           'drift-shaped execution as admitted validator truth.',
                                           'Runtime must also keep bound component validator contract-surface projection policy explicit; '
                                           'runtime preserves disclosed bundle summary and effective component execution rows as distinct '
                                           'surfaces.',
                                           'Runtime must not collapse those surfaces or conceal drift by overwriting one with the other.',
                                           'Runtime must also keep bound component validator observation-continuity policy explicit; once '
                                           'bound component surfaces resolve, runtime continues component observation under canonical '
                                           'surface before final fail-close.',
                                           'Runtime must not let bundle drift erase otherwise available component observation before '
                                           'emitting final failure.',
                                           'Runtime must also keep bound component status-row coverage policy explicit; every bound '
                                           'component must emit one status row before final status.',
                                           'Runtime must not emit final bundle truth with partial component-row coverage when bound '
                                           'component set remains known.',
                                           'Runtime must also keep bundle violation-projection policy explicit; all structure, bundle, and '
                                           'anchor violations must be projected into stale reasons before final status.',
                                           'Runtime must not emit final bundle truth while withholding stale-reason projection for already '
                                           'discovered violation rows.',
                                           'Runtime must also keep final-status derivation policy explicit; final status is '
                                           '`PASS_REQUIRED` if and only if stale reasons remain empty after violation projection; '
                                           'otherwise final status is `FAIL_REQUIRED`.',
                                           'Runtime must not bypass stale-reason-adjudicated final status through any alternate local '
                                           'verdict path.',
                                           'Runtime must also keep error-code precedence policy explicit; registry-class failure preempts '
                                           'structure-class failure, structure-class failure preempts bundle-class failure, and pass-state '
                                           'emits empty error code.',
                                           'Runtime must not derive failure code through any alternate local precedence path.',
                                           'Runtime must also keep failure-classification policy explicit; registry class derives from '
                                           'direct stale reasons present before violation projection, structure class derives from '
                                           'structure violations, bundle class derives from bundle and anchor violations, and otherwise '
                                           'failure class is pass.',
                                           'Runtime must not invent an anchor-only failure class or bypass direct stale reasons through '
                                           'local classification paths.',
                                           'Runtime must also keep registry-class admission policy explicit; only direct stale reasons '
                                           'already present before violation projection may admit registry failure class.',
                                           'Projected structure, bundle, and anchor stale reasons must not retroactively upgrade failure '
                                           'class to registry.',
                                           'Runtime must also keep registry direct-stale-reason origin policy explicit; admitted direct '
                                           'origins are alias error, document invalidity, canonical contract-row invalidity, and '
                                           'required-surface absence before violation projection.',
                                           'Runtime must also keep registry direct-stale-reason alias origin policy explicit; admitted '
                                           'alias direct reasons are rows containing the `_alias_error:` marker before document, '
                                           'required-surface, and contract-row classification.',
                                           'Runtime must also keep registry direct-stale-reason document origin policy explicit; admitted '
                                           'document direct reasons are rows ending with `_empty_or_invalid` after alias exclusion and '
                                           'before required-surface and contract-row classification.',
                                           'Runtime must also keep registry direct-stale-reason required-surface origin policy explicit; '
                                           'admitted required-surface direct reasons are required-component-descriptor-fields missing, '
                                           'surface-missing rows, anchor-checks missing, and components missing before violation '
                                           'projection.',
                                           'Runtime must also keep registry direct-stale-reason contract-row origin policy explicit; '
                                           'admitted contract-row direct reasons are root-corpus-law-bundle prefixed rows and '
                                           'root-machine-registry-completeness prefixed rows that remain after alias, document, and '
                                           'required-surface classification.',
                                           'Runtime must also keep registry direct-stale-reason source policy explicit; direct '
                                           'stale-reason source is local stale reasons already present before violation projection.',
                                           'Runtime must not reinterpret projected structure, bundle, or anchor stale reasons as '
                                           'substitute direct stale-reason source.',
                                           'Runtime must also keep registry direct-stale-reason partition policy explicit; each local '
                                           'stale reason present before violation projection classifies exactly once as alias, document, '
                                           'contract-row, required-surface, or unknown ontology drift.',
                                           'Runtime must also keep registry direct-stale-reason origin-classifier precedence policy '
                                           'explicit; alias classification preempts document, document preempts required-surface, '
                                           'required-surface preempts contract-row, and otherwise origin remains unknown.',
                                           'Runtime must also keep registry direct-stale-reason unclassified policy explicit; unclassified '
                                           'direct stale-reason origin must remain fail-closed.',
                                           'Runtime must fail-close on unclassified direct stale-reason origin rather than silently '
                                           'expanding registry ontology.',
                                           'Runtime must also keep component-validator observation-reason policy explicit; admitted '
                                           'observation reasons are parse/status failure, nonzero returncode after admitted parse/status '
                                           'resolution, and non-pass component status before bundle-violation projection.',
                                           'Runtime must also keep component-validator observation-reason classifier precedence policy '
                                           'explicit; parse/status classification preempts nonzero returncode, nonzero returncode preempts '
                                           'non-pass component status, non-pass component status preempts explicit non-execution '
                                           'exclusion, explicit non-execution exclusion preempts prefixed observation-family ontology '
                                           'drift, and otherwise classification remains not-applicable.',
                                           'Runtime must also keep component-validator observation-reason exclusion-origin policy '
                                           'explicit; admitted excluded non-observation rows are component-validator missing, '
                                           'component-status-row coverage incomplete, component-validator contract-surface reasons, and '
                                           'component-probe surface-contract reasons before bundle-violation projection.',
                                           'Runtime must not silently re-bucket admitted observation reasons or prefixed '
                                           'observation-family ontology drift as excluded non-observation rows.',
                                           'Runtime must keep non-execution bundle rows outside component-validator observation ontology '
                                           'rather than re-bucketing descriptor, support, or coverage rows as runtime observation reasons.',
                                           'Runtime must also keep component-validator observation-reason source policy explicit; runtime '
                                           'observation source is bundle-violation rows only before violation projection.',
                                           'Runtime must not reinterpret direct stale reasons, structure violations, anchor violations, or '
                                           'projected stale-reason strings as substitute observation source.',
                                           'Runtime must also keep component-validator observation-reason partition policy explicit; each '
                                           'bundle-violation row classifies exactly once as admitted observation reason, excluded '
                                           'non-observation row, or unknown ontology drift before violation projection.',
                                           'Runtime must also keep component-validator observation-reason unclassified policy explicit; '
                                           'unclassified observation reason must remain fail-closed.',
                                           'Runtime must fail-close on unclassified component-validator observation reason rather than '
                                           'silently expanding bundle observation ontology.')}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))



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


def _classify_direct_stale_reason_origin(
    reason: str,
    precedence_policy: str = REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY,
    alias_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY,
    document_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY,
    required_surface_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY,
    contract_row_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY,
    residual_unknown_policy: str = REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY,
) -> str:
    if precedence_policy != REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY:
        precedence_policy = REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY
    if alias_origin_policy != REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY:
        alias_origin_policy = REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY
    if document_origin_policy != REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY:
        document_origin_policy = REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY
    if (
        required_surface_origin_policy
        != REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
    ):
        required_surface_origin_policy = REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
    if (
        contract_row_origin_policy
        != REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
    ):
        contract_row_origin_policy = REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
    if residual_unknown_policy != REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY:
        residual_unknown_policy = REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY
    if (
        alias_origin_policy == REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY
        and "_alias_error:" in reason
    ):
        return "alias"
    if (
        document_origin_policy == REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY
        and reason.endswith("_empty_or_invalid")
    ):
        return "document"
    if (
        required_surface_origin_policy
        == REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
        and (
            reason == "root_corpus_law_bundle_required_component_descriptor_fields_missing"
            or reason.startswith("root_corpus_law_bundle_surface_missing:")
            or reason == "root_corpus_law_bundle_anchor_checks_missing"
            or reason == "root_corpus_law_bundle_components_missing"
        )
    ):
        return "required_surface"
    if (
        contract_row_origin_policy
        == REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
        and (
            reason.startswith("root_corpus_law_bundle_")
            or reason.startswith("root_machine_registry_completeness_")
        )
    ):
        return "contract_row"
    if residual_unknown_policy == REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY:
        return "unknown"
    return "unknown"


def _direct_stale_reason_origin_counts(
    stale_reasons: list[str],
    precedence_policy: str = REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY,
    alias_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY,
    document_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY,
    required_surface_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY,
    contract_row_origin_policy: str = REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY,
    residual_unknown_policy: str = REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY,
) -> tuple[dict[str, int], int]:
    counts = {
        "alias": 0,
        "document": 0,
        "contract_row": 0,
        "required_surface": 0,
    }
    unknown_count = 0
    for reason in stale_reasons:
        origin = _classify_direct_stale_reason_origin(
            reason,
            precedence_policy,
            alias_origin_policy,
            document_origin_policy,
            required_surface_origin_policy,
            contract_row_origin_policy,
            residual_unknown_policy,
        )
        if origin == "unknown":
            unknown_count += 1
            continue
        counts[origin] += 1
    return counts, unknown_count


def _classify_component_validator_observation_reason(
    reason: str,
    precedence_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY,
    parse_status_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY,
    nonzero_rc_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY,
    nonpass_status_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY,
    prefixed_ontology_drift_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY,
    residual_not_applicable_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY,
    exclusion_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY,
) -> str:
    if (
        precedence_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY
    ):
        precedence_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY
    if (
        parse_status_origin_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
    ):
        parse_status_origin_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
    if (
        nonzero_rc_origin_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
    ):
        nonzero_rc_origin_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
    if (
        nonpass_status_origin_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
    ):
        nonpass_status_origin_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
    if (
        prefixed_ontology_drift_origin_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
    ):
        prefixed_ontology_drift_origin_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
    if (
        residual_not_applicable_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
    ):
        residual_not_applicable_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
    if (
        exclusion_origin_policy
        != COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
    ):
        exclusion_origin_policy = COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
    if (
        parse_status_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
        and reason
        in {
            "validator_output_missing",
            "validator_output_invalid_json",
            "validator_output_not_json_object",
            "validator_status_key_missing",
            "validator_status_literal_not_string",
        }
    ):
        return "parse_status"
    if (
        nonzero_rc_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
        and reason == "component_validator_nonzero_rc"
    ):
        return "nonzero_rc"
    if (
        nonpass_status_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
        and reason == "component_status_not_pass_required"
    ):
        return "nonpass_status"
    if (
        exclusion_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
        and reason in COMPONENT_VALIDATOR_OBSERVATION_EXCLUDED_REASONS
    ):
        return "not_applicable"
    if (
        prefixed_ontology_drift_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
        and (reason.startswith("validator_output_") or reason.startswith("validator_status_"))
    ):
        return "unknown"
    if (
        prefixed_ontology_drift_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
        and reason.startswith("component_status_")
    ):
        return "unknown"
    if (
        prefixed_ontology_drift_origin_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
        and reason.startswith("component_validator_")
    ):
        return "unknown"
    if (
        residual_not_applicable_policy
        == COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
    ):
        return "not_applicable"
    return "not_applicable"


def _component_validator_observation_reason_counts(
    bundle_violations: list[dict[str, Any]],
    precedence_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY,
    parse_status_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY,
    nonzero_rc_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY,
    nonpass_status_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY,
    prefixed_ontology_drift_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY,
    residual_not_applicable_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY,
    exclusion_origin_policy: str = COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY,
) -> tuple[dict[str, int], int, int]:
    counts = {
        "parse_status": 0,
        "nonzero_rc": 0,
        "nonpass_status": 0,
    }
    unknown_count = 0
    non_applicable_count = 0
    for row in bundle_violations:
        reason = str(row.get("reason") or "")
        category = _classify_component_validator_observation_reason(
            reason,
            precedence_policy,
            parse_status_origin_policy,
            nonzero_rc_origin_policy,
            nonpass_status_origin_policy,
            prefixed_ontology_drift_origin_policy,
            residual_not_applicable_policy,
            exclusion_origin_policy,
        )
        if category == "not_applicable":
            non_applicable_count += 1
            continue
        if category == "unknown":
            unknown_count += 1
            continue
        counts[category] += 1
    return counts, unknown_count, non_applicable_count


def _component_validator_cmd(repo_root: Path, validator_script: str, invocation_contract: str) -> list[str]:
    if invocation_contract == COMPONENT_VALIDATOR_INVOCATION_CONTRACT:
        return ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]
    return ["python3", validator_script, "--repo-root", str(repo_root), "--json-only"]


def _component_validator_cwd(repo_root: Path, working_directory_contract: str) -> Path:
    if working_directory_contract == COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT:
        return repo_root
    return repo_root


def _component_validator_run_kwargs(
    repo_root: Path,
    working_directory_contract: str,
    execution_environment_contract: str,
    execution_transport_contract: str,
    execution_input_contract: str,
    stderr_isolation_contract: str,
    stdio_text_decoding_contract: str,
    execution_timeout_contract: str,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "cwd": _component_validator_cwd(repo_root, working_directory_contract),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": "utf-8",
        "errors": "strict",
        "check": False,
        "shell": False,
        "stdin": subprocess.DEVNULL,
        "env": None,
        "timeout": None,
    }
    if execution_input_contract != COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT:
        kwargs["stdin"] = subprocess.DEVNULL
    if execution_environment_contract != COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT:
        kwargs["env"] = None
    if stdio_text_decoding_contract != COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT:
        kwargs["encoding"] = "utf-8"
        kwargs["errors"] = "strict"
    if execution_timeout_contract != COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT:
        kwargs["timeout"] = None
    if stderr_isolation_contract != COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if execution_transport_contract == COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT:
        return kwargs
    return kwargs


def _parse_component_validator_stdout(
    stdout: str,
    stdout_presence_contract: str,
    output_contract: str,
    stdout_framing_contract: str,
) -> tuple[dict[str, Any], str]:
    if stdout_presence_contract == COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT and not stdout:
        return {}, "validator_output_missing"
    if not stdout:
        return {}, "validator_output_missing"
    try:
        payload = json.loads(stdout)
    except Exception:
        return {}, "validator_output_invalid_json"
    if stdout_framing_contract == COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT and not isinstance(payload, dict):
        return {}, "validator_output_not_json_object"
    if output_contract == COMPONENT_VALIDATOR_OUTPUT_CONTRACT and not isinstance(payload, dict):
        return {}, "validator_output_not_json_object"
    if not isinstance(payload, dict):
        return {}, "validator_output_not_json_object"
    return payload, ""


def _normalize_component_validator_stdout(
    stdout: str,
    stdout_normalization_contract: str,
) -> str:
    text = stdout or ""
    if stdout_normalization_contract == COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT:
        return text.strip()
    return text.strip()


def _evaluate_component_validator_root_doc_anchor_contract(
    payload: dict[str, Any],
    contract: str,
) -> str:
    if contract != COMPONENT_VALIDATOR_ROOT_DOC_ANCHOR_CONTRACT:
        return ""
    status = str(payload.get("root_doc_anchor_status") or "")
    if status != STATUS_PASS_REQUIRED:
        return "component_validator_root_doc_anchor_status_not_pass_required"
    count = payload.get("root_doc_anchor_check_count")
    if not isinstance(count, int) or count <= 0:
        return "component_validator_root_doc_anchor_check_count_invalid"
    return ""


def _evaluate_component_validator_row_projection_contract(
    payload: dict[str, Any],
    contract: str,
) -> list[str]:
    if contract != COMPONENT_VALIDATOR_ROW_PROJECTION_CONTRACT:
        return []
    violations: list[str] = []
    rows = payload.get("row_family_projection_rows")
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        violations.append("component_validator_row_family_projection_rows_missing_or_invalid")
        return violations
    coverage_keys = [key for key in payload if key.endswith("_row_coverage_status")]
    identity_keys = [key for key in payload if key.endswith("_row_identity_projection_status")]
    if not coverage_keys:
        violations.append("component_validator_row_coverage_status_missing")
    elif any(str(payload.get(key) or "") != STATUS_PASS_REQUIRED for key in coverage_keys):
        violations.append("component_validator_row_coverage_status_not_pass_required")
    if not identity_keys:
        violations.append("component_validator_row_identity_projection_status_missing")
    elif any(str(payload.get(key) or "") != STATUS_PASS_REQUIRED for key in identity_keys):
        violations.append("component_validator_row_identity_projection_status_not_pass_required")
    return violations


def _evaluate_component_probe_shadow_bootstrap_contract(
    active_doc: dict[str, Any],
    contract: str,
) -> tuple[str, str]:
    actual_contract = str(active_doc.get("probe_shadow_bootstrap_contract") or "").strip()
    if contract != COMPONENT_PROBE_SHADOW_BOOTSTRAP_CONTRACT:
        return actual_contract, ""
    if not actual_contract:
        return actual_contract, "component_probe_shadow_bootstrap_contract_missing"
    if actual_contract != contract:
        return actual_contract, "component_probe_shadow_bootstrap_contract_not_inherited"
    return actual_contract, ""


def _resolve_component_validator_status(
    payload: dict[str, Any],
    status_key: str,
    status_key_resolution_contract: str,
    status_literal_contract: str,
) -> tuple[str, str]:
    if status_key_resolution_contract == COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT:
        if status_key not in payload:
            return "", "validator_status_key_missing"
        value = payload.get(status_key)
        if status_literal_contract == COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT and not isinstance(value, str):
            return "", "validator_status_literal_not_string"
        return str(value or ""), ""
    if status_key not in payload:
        return "", "validator_status_key_missing"
    value = payload.get(status_key)
    if status_literal_contract == COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT and not isinstance(value, str):
        return "", "validator_status_literal_not_string"
    return str(value or ""), ""


def _run_component_validator(
    repo_root,
    validator_script: str,
    status_key: str,
    output_contract: str,
    invocation_contract: str,
    stderr_isolation_contract: str,
    stdout_normalization_contract: str,
    stdout_presence_contract: str,
    stdout_framing_contract: str,
    status_key_resolution_contract: str,
    status_literal_contract: str,
    execution_input_contract: str,
    verdict_admission_timing_contract: str,
    stdio_text_decoding_contract: str,
    execution_timeout_contract: str,
    working_directory_contract: str,
    execution_environment_contract: str,
    execution_transport_contract: str,
) -> tuple[int, dict[str, Any], str]:
    repo_root_path = Path(repo_root)
    cmd = _component_validator_cmd(repo_root_path, validator_script, invocation_contract)
    proc = subprocess.run(
        cmd,
        **_component_validator_run_kwargs(
            repo_root_path,
            working_directory_contract,
            execution_environment_contract,
            execution_transport_contract,
            execution_input_contract,
            stderr_isolation_contract,
            stdio_text_decoding_contract,
            execution_timeout_contract,
        ),
    )
    if verdict_admission_timing_contract != COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT:
        return proc.returncode, {}, "validator_verdict_admission_timing_contract_invalid"
    stdout = _normalize_component_validator_stdout(proc.stdout or "", stdout_normalization_contract)
    payload, parse_error = _parse_component_validator_stdout(
        stdout,
        stdout_presence_contract,
        output_contract,
        stdout_framing_contract,
    )
    if parse_error:
        return proc.returncode, {}, parse_error
    _component_status, status_error = _resolve_component_validator_status(
        payload,
        status_key,
        status_key_resolution_contract,
        status_literal_contract,
    )
    if status_error:
        return proc.returncode, payload, status_error
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
    component_status_row_coverage_incomplete = False
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
    law_bundle_component_row_completeness_rows = (
        law_bundle_component_row_completeness_rows_from_doc(bundle_doc) if bundle_doc else ()
    )
    law_bundle_component_row_completeness_surface = (
        readme_law_bundle_component_row_completeness_surface(repo_root)
    )
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
    component_validator_returncode_observation_contract = (
        component_validator_returncode_observation_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_output_contract = (
        component_validator_output_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_root_doc_anchor_contract = (
        component_validator_root_doc_anchor_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_row_projection_contract = (
        component_validator_row_projection_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_probe_shadow_bootstrap_contract = (
        component_probe_shadow_bootstrap_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_invocation_contract = (
        component_validator_invocation_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_output_channel_contract = (
        component_validator_output_channel_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_stderr_isolation_contract = (
        component_validator_stderr_isolation_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_stdio_text_decoding_contract = (
        component_validator_stdio_text_decoding_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_stdout_normalization_contract = (
        component_validator_stdout_normalization_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_stdout_presence_contract = (
        component_validator_stdout_presence_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_stdout_framing_contract = (
        component_validator_stdout_framing_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_status_key_resolution_contract = (
        component_validator_status_key_resolution_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_status_literal_contract = (
        component_validator_status_literal_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_input_contract = (
        component_validator_execution_input_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_verdict_admission_timing_contract = (
        component_validator_verdict_admission_timing_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_timeout_contract = (
        component_validator_execution_timeout_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_working_directory_contract = (
        component_validator_working_directory_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_environment_contract = (
        component_validator_execution_environment_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_execution_transport_contract = (
        component_validator_execution_transport_contract_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_contract_drift_execution_policy = (
        component_validator_contract_drift_execution_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_contract_surface_projection_policy = (
        component_validator_contract_surface_projection_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_continuity_policy = (
        component_validator_observation_continuity_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_status_row_coverage_policy = (
        component_status_row_coverage_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    violation_projection_policy = violation_projection_policy_from_doc(bundle_doc) if bundle_doc else ""
    final_status_derivation_policy = final_status_derivation_policy_from_doc(bundle_doc) if bundle_doc else ""
    error_code_precedence_policy = error_code_precedence_policy_from_doc(bundle_doc) if bundle_doc else ""
    failure_classification_policy = failure_classification_policy_from_doc(bundle_doc) if bundle_doc else ""
    registry_class_admission_policy = registry_class_admission_policy_from_doc(bundle_doc) if bundle_doc else ""
    registry_direct_stale_reason_origin_policy = (
        registry_direct_stale_reason_origin_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    registry_direct_stale_reason_alias_origin_policy = (
        registry_direct_stale_reason_alias_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    registry_direct_stale_reason_document_origin_policy = (
        registry_direct_stale_reason_document_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    registry_direct_stale_reason_required_surface_origin_policy = (
        registry_direct_stale_reason_required_surface_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    registry_direct_stale_reason_contract_row_origin_policy = (
        registry_direct_stale_reason_contract_row_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    registry_direct_stale_reason_source_policy = (
        registry_direct_stale_reason_source_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    registry_direct_stale_reason_partition_policy = (
        registry_direct_stale_reason_partition_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    registry_direct_stale_reason_origin_classifier_precedence_policy = (
        registry_direct_stale_reason_origin_classifier_precedence_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    registry_direct_stale_reason_residual_unknown_policy = (
        registry_direct_stale_reason_residual_unknown_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    registry_direct_stale_reason_unclassified_policy = (
        registry_direct_stale_reason_unclassified_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_reason_admission_policy = (
        component_validator_observation_reason_admission_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_reason_parse_status_origin_policy = (
        component_validator_observation_reason_parse_status_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_nonzero_rc_origin_policy = (
        component_validator_observation_reason_nonzero_rc_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_nonpass_status_origin_policy = (
        component_validator_observation_reason_nonpass_status_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_prefixed_ontology_drift_origin_policy = (
        component_validator_observation_reason_prefixed_ontology_drift_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_residual_not_applicable_policy = (
        component_validator_observation_reason_residual_not_applicable_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_classifier_precedence_policy = (
        component_validator_observation_reason_classifier_precedence_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_exclusion_origin_policy = (
        component_validator_observation_reason_exclusion_origin_policy_from_doc(bundle_doc)
        if bundle_doc
        else ""
    )
    component_validator_observation_reason_exclusion_policy = (
        component_validator_observation_reason_exclusion_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_reason_source_policy = (
        component_validator_observation_reason_source_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_reason_partition_policy = (
        component_validator_observation_reason_partition_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    component_validator_observation_reason_unclassified_policy = (
        component_validator_observation_reason_unclassified_policy_from_doc(bundle_doc) if bundle_doc else ""
    )
    effective_component_validator_status_requirement = (
        component_validator_status_requirement
        if component_validator_status_requirement == STATUS_PASS_REQUIRED
        else STATUS_PASS_REQUIRED
    )
    effective_component_validator_execution_failure_policy = (
        component_validator_execution_failure_policy
        if component_validator_execution_failure_policy == "fail_closed"
        else "fail_closed"
    )
    effective_component_validator_returncode_observation_contract = (
        component_validator_returncode_observation_contract
        if component_validator_returncode_observation_contract == COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT
        else COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT
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
    effective_component_validator_stderr_isolation_contract = (
        component_validator_stderr_isolation_contract
        if component_validator_stderr_isolation_contract == COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT
        else COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT
    )
    effective_component_validator_stdio_text_decoding_contract = (
        component_validator_stdio_text_decoding_contract
        if component_validator_stdio_text_decoding_contract == COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT
        else COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT
    )
    effective_component_validator_output_contract = (
        component_validator_output_contract
        if component_validator_output_contract == COMPONENT_VALIDATOR_OUTPUT_CONTRACT
        else COMPONENT_VALIDATOR_OUTPUT_CONTRACT
    )
    effective_component_validator_root_doc_anchor_contract = (
        component_validator_root_doc_anchor_contract
        if component_validator_root_doc_anchor_contract == COMPONENT_VALIDATOR_ROOT_DOC_ANCHOR_CONTRACT
        else COMPONENT_VALIDATOR_ROOT_DOC_ANCHOR_CONTRACT
    )
    effective_component_validator_row_projection_contract = (
        component_validator_row_projection_contract
        if component_validator_row_projection_contract == COMPONENT_VALIDATOR_ROW_PROJECTION_CONTRACT
        else COMPONENT_VALIDATOR_ROW_PROJECTION_CONTRACT
    )
    effective_component_probe_shadow_bootstrap_contract = (
        component_probe_shadow_bootstrap_contract
        if component_probe_shadow_bootstrap_contract == COMPONENT_PROBE_SHADOW_BOOTSTRAP_CONTRACT
        else COMPONENT_PROBE_SHADOW_BOOTSTRAP_CONTRACT
    )
    effective_component_validator_contract_drift_execution_policy = (
        component_validator_contract_drift_execution_policy
        if component_validator_contract_drift_execution_policy == COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY
        else COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY
    )
    effective_component_validator_contract_surface_projection_policy = (
        component_validator_contract_surface_projection_policy
        if component_validator_contract_surface_projection_policy == COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY
        else COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY
    )
    effective_component_validator_observation_continuity_policy = (
        component_validator_observation_continuity_policy
        if component_validator_observation_continuity_policy == COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY
        else COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY
    )
    effective_component_status_row_coverage_policy = (
        component_status_row_coverage_policy
        if component_status_row_coverage_policy == COMPONENT_STATUS_ROW_COVERAGE_POLICY
        else COMPONENT_STATUS_ROW_COVERAGE_POLICY
    )
    effective_violation_projection_policy = (
        violation_projection_policy
        if violation_projection_policy == VIOLATION_PROJECTION_POLICY
        else VIOLATION_PROJECTION_POLICY
    )
    effective_final_status_derivation_policy = (
        final_status_derivation_policy
        if final_status_derivation_policy == FINAL_STATUS_DERIVATION_POLICY
        else FINAL_STATUS_DERIVATION_POLICY
    )
    effective_error_code_precedence_policy = (
        error_code_precedence_policy
        if error_code_precedence_policy == ERROR_CODE_PRECEDENCE_POLICY
        else ERROR_CODE_PRECEDENCE_POLICY
    )
    effective_failure_classification_policy = (
        failure_classification_policy
        if failure_classification_policy == FAILURE_CLASSIFICATION_POLICY
        else FAILURE_CLASSIFICATION_POLICY
    )
    effective_registry_class_admission_policy = (
        registry_class_admission_policy
        if registry_class_admission_policy == REGISTRY_CLASS_ADMISSION_POLICY
        else REGISTRY_CLASS_ADMISSION_POLICY
    )
    effective_registry_direct_stale_reason_origin_policy = (
        registry_direct_stale_reason_origin_policy
        if registry_direct_stale_reason_origin_policy == REGISTRY_DIRECT_STALE_REASON_ORIGIN_POLICY
        else REGISTRY_DIRECT_STALE_REASON_ORIGIN_POLICY
    )
    effective_registry_direct_stale_reason_alias_origin_policy = (
        registry_direct_stale_reason_alias_origin_policy
        if registry_direct_stale_reason_alias_origin_policy == REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY
        else REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY
    )
    effective_registry_direct_stale_reason_document_origin_policy = (
        registry_direct_stale_reason_document_origin_policy
        if registry_direct_stale_reason_document_origin_policy == REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY
        else REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY
    )
    effective_registry_direct_stale_reason_required_surface_origin_policy = (
        registry_direct_stale_reason_required_surface_origin_policy
        if (
            registry_direct_stale_reason_required_surface_origin_policy
            == REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
        )
        else REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
    )
    effective_registry_direct_stale_reason_contract_row_origin_policy = (
        registry_direct_stale_reason_contract_row_origin_policy
        if (
            registry_direct_stale_reason_contract_row_origin_policy
            == REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
        )
        else REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
    )
    effective_registry_direct_stale_reason_source_policy = (
        registry_direct_stale_reason_source_policy
        if registry_direct_stale_reason_source_policy == REGISTRY_DIRECT_STALE_REASON_SOURCE_POLICY
        else REGISTRY_DIRECT_STALE_REASON_SOURCE_POLICY
    )
    effective_registry_direct_stale_reason_partition_policy = (
        registry_direct_stale_reason_partition_policy
        if registry_direct_stale_reason_partition_policy == REGISTRY_DIRECT_STALE_REASON_PARTITION_POLICY
        else REGISTRY_DIRECT_STALE_REASON_PARTITION_POLICY
    )
    effective_registry_direct_stale_reason_origin_classifier_precedence_policy = (
        registry_direct_stale_reason_origin_classifier_precedence_policy
        if (
            registry_direct_stale_reason_origin_classifier_precedence_policy
            == REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY
        )
        else REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY
    )
    effective_registry_direct_stale_reason_residual_unknown_policy = (
        registry_direct_stale_reason_residual_unknown_policy
        if (
            registry_direct_stale_reason_residual_unknown_policy
            == REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY
        )
        else REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY
    )
    effective_registry_direct_stale_reason_unclassified_policy = (
        registry_direct_stale_reason_unclassified_policy
        if (
            registry_direct_stale_reason_unclassified_policy
            == REGISTRY_DIRECT_STALE_REASON_UNCLASSIFIED_POLICY
        )
        else REGISTRY_DIRECT_STALE_REASON_UNCLASSIFIED_POLICY
    )
    effective_component_validator_observation_reason_admission_policy = (
        component_validator_observation_reason_admission_policy
        if (
            component_validator_observation_reason_admission_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_ADMISSION_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_ADMISSION_POLICY
    )
    effective_component_validator_observation_reason_parse_status_origin_policy = (
        component_validator_observation_reason_parse_status_origin_policy
        if (
            component_validator_observation_reason_parse_status_origin_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
    )
    effective_component_validator_observation_reason_nonzero_rc_origin_policy = (
        component_validator_observation_reason_nonzero_rc_origin_policy
        if (
            component_validator_observation_reason_nonzero_rc_origin_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
    )
    effective_component_validator_observation_reason_nonpass_status_origin_policy = (
        component_validator_observation_reason_nonpass_status_origin_policy
        if (
            component_validator_observation_reason_nonpass_status_origin_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
    )
    effective_component_validator_observation_reason_prefixed_ontology_drift_origin_policy = (
        component_validator_observation_reason_prefixed_ontology_drift_origin_policy
        if (
            component_validator_observation_reason_prefixed_ontology_drift_origin_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
    )
    effective_component_validator_observation_reason_residual_not_applicable_policy = (
        component_validator_observation_reason_residual_not_applicable_policy
        if (
            component_validator_observation_reason_residual_not_applicable_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
    )
    effective_component_validator_observation_reason_classifier_precedence_policy = (
        component_validator_observation_reason_classifier_precedence_policy
        if (
            component_validator_observation_reason_classifier_precedence_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY
    )
    effective_component_validator_observation_reason_exclusion_origin_policy = (
        component_validator_observation_reason_exclusion_origin_policy
        if (
            component_validator_observation_reason_exclusion_origin_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
    )
    effective_component_validator_observation_reason_exclusion_policy = (
        component_validator_observation_reason_exclusion_policy
        if (
            component_validator_observation_reason_exclusion_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_POLICY
    )
    effective_component_validator_observation_reason_source_policy = (
        component_validator_observation_reason_source_policy
        if (
            component_validator_observation_reason_source_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_SOURCE_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_SOURCE_POLICY
    )
    effective_component_validator_observation_reason_partition_policy = (
        component_validator_observation_reason_partition_policy
        if (
            component_validator_observation_reason_partition_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_PARTITION_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_PARTITION_POLICY
    )
    effective_component_validator_observation_reason_unclassified_policy = (
        component_validator_observation_reason_unclassified_policy
        if (
            component_validator_observation_reason_unclassified_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_UNCLASSIFIED_POLICY
        )
        else COMPONENT_VALIDATOR_OBSERVATION_REASON_UNCLASSIFIED_POLICY
    )
    effective_component_validator_stdout_normalization_contract = (
        component_validator_stdout_normalization_contract
        if component_validator_stdout_normalization_contract == COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT
        else COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT
    )
    effective_component_validator_stdout_presence_contract = (
        component_validator_stdout_presence_contract
        if component_validator_stdout_presence_contract == COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT
        else COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT
    )
    effective_component_validator_stdout_framing_contract = (
        component_validator_stdout_framing_contract
        if component_validator_stdout_framing_contract == COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT
        else COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT
    )
    effective_component_validator_status_key_resolution_contract = (
        component_validator_status_key_resolution_contract
        if component_validator_status_key_resolution_contract == COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT
        else COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT
    )
    effective_component_validator_status_literal_contract = (
        component_validator_status_literal_contract
        if component_validator_status_literal_contract == COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT
        else COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT
    )
    effective_component_validator_execution_input_contract = (
        component_validator_execution_input_contract
        if component_validator_execution_input_contract == COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT
        else COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT
    )
    effective_component_validator_verdict_admission_timing_contract = (
        component_validator_verdict_admission_timing_contract
        if component_validator_verdict_admission_timing_contract == COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT
        else COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT
    )
    effective_component_validator_execution_timeout_contract = (
        component_validator_execution_timeout_contract
        if component_validator_execution_timeout_contract == COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT
        else COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT
    )
    effective_component_validator_working_directory_contract = (
        component_validator_working_directory_contract
        if component_validator_working_directory_contract == COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT
        else COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT
    )
    effective_component_validator_execution_environment_contract = (
        component_validator_execution_environment_contract
        if component_validator_execution_environment_contract == COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT
        else COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT
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
        if component_validator_returncode_observation_contract != COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_returncode_observation_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_output_contract != COMPONENT_VALIDATOR_OUTPUT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_output_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_root_doc_anchor_contract != COMPONENT_VALIDATOR_ROOT_DOC_ANCHOR_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_root_doc_anchor_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_row_projection_contract != COMPONENT_VALIDATOR_ROW_PROJECTION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_row_projection_contract_invalid")
            error_code = ERR_REGISTRY
        if component_probe_shadow_bootstrap_contract != COMPONENT_PROBE_SHADOW_BOOTSTRAP_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_probe_shadow_bootstrap_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_invocation_contract != COMPONENT_VALIDATOR_INVOCATION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_invocation_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_output_channel_contract != COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_output_channel_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_stderr_isolation_contract != COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_stderr_isolation_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_stdio_text_decoding_contract != COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_stdio_text_decoding_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_stdout_normalization_contract != COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_stdout_normalization_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_stdout_presence_contract != COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_stdout_presence_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_stdout_framing_contract != COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_stdout_framing_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_status_key_resolution_contract != COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_status_key_resolution_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_status_literal_contract != COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_status_literal_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_input_contract != COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_input_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_verdict_admission_timing_contract != COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_verdict_admission_timing_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_timeout_contract != COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_timeout_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_working_directory_contract != COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_working_directory_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_environment_contract != COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_environment_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_execution_transport_contract != COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT:
            stale_reasons.append("root_corpus_law_bundle_component_validator_execution_transport_contract_invalid")
            error_code = ERR_REGISTRY
        if component_validator_contract_drift_execution_policy != COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY:
            stale_reasons.append("root_corpus_law_bundle_component_validator_contract_drift_execution_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            component_validator_contract_surface_projection_policy
            != COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY
        ):
            stale_reasons.append("root_corpus_law_bundle_component_validator_contract_surface_projection_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_continuity_policy
            != COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY
        ):
            stale_reasons.append("root_corpus_law_bundle_component_validator_observation_continuity_policy_invalid")
            error_code = ERR_REGISTRY
        if component_status_row_coverage_policy != COMPONENT_STATUS_ROW_COVERAGE_POLICY:
            stale_reasons.append("root_corpus_law_bundle_component_status_row_coverage_policy_invalid")
            error_code = ERR_REGISTRY
        if violation_projection_policy != VIOLATION_PROJECTION_POLICY:
            stale_reasons.append("root_corpus_law_bundle_violation_projection_policy_invalid")
            error_code = ERR_REGISTRY
        if final_status_derivation_policy != FINAL_STATUS_DERIVATION_POLICY:
            stale_reasons.append("root_corpus_law_bundle_final_status_derivation_policy_invalid")
            error_code = ERR_REGISTRY
        if error_code_precedence_policy != ERROR_CODE_PRECEDENCE_POLICY:
            stale_reasons.append("root_corpus_law_bundle_error_code_precedence_policy_invalid")
            error_code = ERR_REGISTRY
        if failure_classification_policy != FAILURE_CLASSIFICATION_POLICY:
            stale_reasons.append("root_corpus_law_bundle_failure_classification_policy_invalid")
            error_code = ERR_REGISTRY
        if registry_class_admission_policy != REGISTRY_CLASS_ADMISSION_POLICY:
            stale_reasons.append("root_corpus_law_bundle_registry_class_admission_policy_invalid")
            error_code = ERR_REGISTRY
        if registry_direct_stale_reason_origin_policy != REGISTRY_DIRECT_STALE_REASON_ORIGIN_POLICY:
            stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_origin_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_alias_origin_policy
            != REGISTRY_DIRECT_STALE_REASON_ALIAS_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_alias_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_document_origin_policy
            != REGISTRY_DIRECT_STALE_REASON_DOCUMENT_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_document_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_required_surface_origin_policy
            != REGISTRY_DIRECT_STALE_REASON_REQUIRED_SURFACE_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_required_surface_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_contract_row_origin_policy
            != REGISTRY_DIRECT_STALE_REASON_CONTRACT_ROW_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_contract_row_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if registry_direct_stale_reason_source_policy != REGISTRY_DIRECT_STALE_REASON_SOURCE_POLICY:
            stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_source_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_partition_policy
            != REGISTRY_DIRECT_STALE_REASON_PARTITION_POLICY
        ):
            stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_partition_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_origin_classifier_precedence_policy
            != REGISTRY_DIRECT_STALE_REASON_ORIGIN_CLASSIFIER_PRECEDENCE_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_origin_classifier_precedence_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_residual_unknown_policy
            != REGISTRY_DIRECT_STALE_REASON_RESIDUAL_UNKNOWN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_registry_direct_stale_reason_residual_unknown_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            registry_direct_stale_reason_unclassified_policy
            != REGISTRY_DIRECT_STALE_REASON_UNCLASSIFIED_POLICY
        ):
            stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_unclassified_policy_invalid")
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_admission_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_ADMISSION_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_admission_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_parse_status_origin_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_PARSE_STATUS_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_parse_status_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_nonzero_rc_origin_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_NONZERO_RC_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_nonzero_rc_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_nonpass_status_origin_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_NONPASS_STATUS_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_nonpass_status_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_prefixed_ontology_drift_origin_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_PREFIXED_ONTOLOGY_DRIFT_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_prefixed_ontology_drift_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_residual_not_applicable_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_RESIDUAL_NOT_APPLICABLE_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_residual_not_applicable_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_classifier_precedence_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_CLASSIFIER_PRECEDENCE_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_classifier_precedence_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_exclusion_origin_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_ORIGIN_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_exclusion_origin_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_exclusion_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_EXCLUSION_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_exclusion_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_source_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_SOURCE_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_source_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_partition_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_PARTITION_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_partition_policy_invalid"
            )
            error_code = ERR_REGISTRY
        if (
            component_validator_observation_reason_unclassified_policy
            != COMPONENT_VALIDATOR_OBSERVATION_REASON_UNCLASSIFIED_POLICY
        ):
            stale_reasons.append(
                "root_corpus_law_bundle_component_validator_observation_reason_unclassified_policy_invalid"
            )
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
        if not law_bundle_component_row_completeness_rows:
            stale_reasons.append("root_corpus_law_bundle_component_row_completeness_rows_missing")
            error_code = ERR_REGISTRY
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_law_bundle",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    if (
        bundle_doc
        and components
        and effective_component_validator_observation_continuity_policy
        == COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY
    ):
        if len(component_map) != len(components):
            structure_violations.append({"field": "component_rows", "reason": "duplicate_component_id"})
        if len(set(component_orders)) != len(component_orders) or not contiguous_orders(sorted(component_orders)):
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

        for reason in law_bundle_component_row_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "law_bundle_component_row_completeness_surface",
                    "reason": f"law_bundle_component_row_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": law_bundle_component_row_completeness_rows,
                    "expected_rows": EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS,
                    "field_name": "law_bundle_component_row_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_law_bundle_component_row_completeness_id",
                    "non_contiguous_reason": "law_bundle_component_row_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_law_bundle_component_row_completeness_rows",
                    "extra_reason": "extra_law_bundle_component_row_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "law_bundle_component_row_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": law_bundle_component_row_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "law_bundle_component_row_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_law_bundle_component_row_completeness_surface_phrase",
                    "non_contiguous_reason": "law_bundle_component_row_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_law_bundle_component_row_completeness_surface_rows",
                    "extra_reason": "extra_law_bundle_component_row_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "law_bundle_component_row_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=bundle_violations,
        )
        expected_law_bundle_component_row_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS.values()
        ]
        expected_law_bundle_component_row_completeness_orders = [
            int(row["order"]) for row in EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS.values()
        ]
        actual_law_bundle_component_row_completeness_phrases = [
            row.contract_phrase for row in law_bundle_component_row_completeness_surface.rows
        ]
        actual_law_bundle_component_row_completeness_orders = [
            row.order for row in law_bundle_component_row_completeness_surface.rows
        ]
        if actual_law_bundle_component_row_completeness_phrases and tuple(
            actual_law_bundle_component_row_completeness_phrases
        ) != tuple(expected_law_bundle_component_row_completeness_phrases):
            bundle_violations.append(
                {
                    "field": "law_bundle_component_row_completeness_surface",
                    "reason": "law_bundle_component_row_completeness_surface_phrase_order_mismatch",
                    "expected": expected_law_bundle_component_row_completeness_phrases,
                    "actual": actual_law_bundle_component_row_completeness_phrases,
                }
            )
        if actual_law_bundle_component_row_completeness_orders and tuple(
            actual_law_bundle_component_row_completeness_orders
        ) != tuple(expected_law_bundle_component_row_completeness_orders):
            bundle_violations.append(
                {
                    "field": "law_bundle_component_row_completeness_surface",
                    "reason": "law_bundle_component_row_completeness_surface_order_mismatch",
                    "expected": expected_law_bundle_component_row_completeness_orders,
                    "actual": actual_law_bundle_component_row_completeness_orders,
                }
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
            active_path = Path()
            alias_error = ""
            active_doc: dict[str, Any] = {}
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
                    active_doc = load_mapping_descriptor(active_path)
                    if not active_doc:
                        bundle_violations.append(
                            {
                                "component_id": row.component_id,
                                "reason": "component_active_descriptor_invalid",
                                "active_path": str(active_path),
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
                effective_component_validator_output_contract,
                effective_component_validator_invocation_contract,
                effective_component_validator_stderr_isolation_contract,
                effective_component_validator_stdout_normalization_contract,
                effective_component_validator_stdout_presence_contract,
                effective_component_validator_stdout_framing_contract,
                effective_component_validator_status_key_resolution_contract,
                effective_component_validator_status_literal_contract,
                effective_component_validator_execution_input_contract,
                effective_component_validator_verdict_admission_timing_contract,
                effective_component_validator_stdio_text_decoding_contract,
                effective_component_validator_execution_timeout_contract,
                effective_component_validator_working_directory_contract,
                effective_component_validator_execution_environment_contract,
                effective_component_validator_execution_transport_contract,
            )
            component_status = str(payload.get(row.status_key) or "")
            component_root_doc_anchor_status = str(payload.get("root_doc_anchor_status") or "")
            component_root_doc_anchor_check_count = payload.get("root_doc_anchor_check_count")
            component_row_family_projection_rows = payload.get("row_family_projection_rows")
            component_row_coverage_keys = sorted(
                key for key in payload if key.endswith("_row_coverage_status")
            )
            component_row_identity_keys = sorted(
                key for key in payload if key.endswith("_row_identity_projection_status")
            )
            anchor_contract_violation = _evaluate_component_validator_root_doc_anchor_contract(
                payload,
                effective_component_validator_root_doc_anchor_contract,
            )
            row_projection_contract_violations = _evaluate_component_validator_row_projection_contract(
                payload,
                effective_component_validator_row_projection_contract,
            )
            (
                component_active_probe_shadow_bootstrap_contract,
                probe_shadow_bootstrap_contract_violation,
            ) = _evaluate_component_probe_shadow_bootstrap_contract(
                active_doc,
                effective_component_probe_shadow_bootstrap_contract,
            )
            descriptor_field_rows: list[dict[str, str]] = []
            component_status_rows.append(
                {
                    "order": row.order,
                    "component_id": row.component_id,
                    "status_key": row.status_key,
                    "validator_script": row.validator_script,
                    "probe_script": row.probe_script,
                    "common_script": row.common_script,
                    "validator_status_requirement": effective_component_validator_status_requirement,
                    "validator_execution_failure_policy": effective_component_validator_execution_failure_policy,
                    "validator_returncode_observation_contract": effective_component_validator_returncode_observation_contract,
                    "validator_output_contract": effective_component_validator_output_contract,
                    "validator_root_doc_anchor_contract": effective_component_validator_root_doc_anchor_contract,
                    "validator_row_projection_contract": effective_component_validator_row_projection_contract,
                    "probe_shadow_bootstrap_contract": effective_component_probe_shadow_bootstrap_contract,
                    "active_probe_shadow_bootstrap_contract": component_active_probe_shadow_bootstrap_contract,
                    "probe_shadow_bootstrap_contract_status": (
                        STATUS_PASS_REQUIRED
                        if component_active_probe_shadow_bootstrap_contract
                        == effective_component_probe_shadow_bootstrap_contract
                        else STATUS_FAIL_REQUIRED
                    ),
                    "validator_invocation_contract": effective_component_validator_invocation_contract,
                    "validator_output_channel_contract": effective_component_validator_output_channel_contract,
                    "validator_stderr_isolation_contract": effective_component_validator_stderr_isolation_contract,
                    "validator_stdio_text_decoding_contract": effective_component_validator_stdio_text_decoding_contract,
                    "validator_stdout_normalization_contract": effective_component_validator_stdout_normalization_contract,
                    "validator_stdout_presence_contract": effective_component_validator_stdout_presence_contract,
                    "validator_stdout_framing_contract": effective_component_validator_stdout_framing_contract,
                    "validator_status_key_resolution_contract": effective_component_validator_status_key_resolution_contract,
                    "validator_status_literal_contract": effective_component_validator_status_literal_contract,
                    "validator_execution_input_contract": effective_component_validator_execution_input_contract,
                    "validator_verdict_admission_timing_contract": effective_component_validator_verdict_admission_timing_contract,
                    "validator_execution_timeout_contract": effective_component_validator_execution_timeout_contract,
                    "validator_working_directory_contract": effective_component_validator_working_directory_contract,
                    "validator_execution_environment_contract": effective_component_validator_execution_environment_contract,
                    "validator_execution_transport_contract": effective_component_validator_execution_transport_contract,
                    "validator_contract_drift_execution_policy": effective_component_validator_contract_drift_execution_policy,
                    "validator_contract_surface_projection_policy": (
                        effective_component_validator_contract_surface_projection_policy
                    ),
                    "validator_rc": rc,
                    "component_status": component_status,
                    "root_doc_anchor_status": component_root_doc_anchor_status,
                    "root_doc_anchor_check_count": component_root_doc_anchor_check_count,
                    "row_family_projection_row_count": (
                        len(component_row_family_projection_rows)
                        if isinstance(component_row_family_projection_rows, list)
                        else 0
                    ),
                    "row_coverage_status_keys": component_row_coverage_keys,
                    "row_identity_projection_status_keys": component_row_identity_keys,
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
            if not run_error:
                if anchor_contract_violation:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": anchor_contract_violation,
                        }
                    )
                for projection_violation in row_projection_contract_violations:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": projection_violation,
                        }
                    )
                if probe_shadow_bootstrap_contract_violation and active_doc:
                    bundle_violations.append(
                        {
                            "component_id": row.component_id,
                            "reason": probe_shadow_bootstrap_contract_violation,
                            "expected_probe_shadow_bootstrap_contract": (
                                effective_component_probe_shadow_bootstrap_contract
                            ),
                            "actual_probe_shadow_bootstrap_contract": (
                                component_active_probe_shadow_bootstrap_contract
                            ),
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
                if not alias_error and active_path.exists():
                    if active_doc:
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

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name=None,
            )
        )

        component_status_row_coverage_incomplete = (
            effective_component_status_row_coverage_policy == COMPONENT_STATUS_ROW_COVERAGE_POLICY
            and len(component_status_rows) != len(sorted_components)
        )
        if component_status_row_coverage_incomplete:
            bundle_violations.append(
                {
                    "component_id": "root_corpus_law_bundle",
                    "reason": "component_status_row_coverage_incomplete",
                    "expected_count": len(sorted_components),
                    "actual_count": len(component_status_rows),
                }
            )
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "component_rows",
                "member_id_key": "component_id",
                "actual_rows": sorted_components,
                "expected_rows": {
                    component_id: {} for component_id in EXPECTED_COMPONENTS
                },
                "id_attr": "component_id",
            },
            {
                "family_id": "component_status_rows",
                "member_id_key": "component_id",
                "actual_rows": [
                    SimpleNamespace(component_id=str(row.get("component_id") or ""))
                    for row in component_status_rows
                ],
                "expected_rows": {
                    component_id: {} for component_id in EXPECTED_COMPONENTS
                },
                "id_attr": "component_id",
            },
            {
                "family_id": "law_bundle_component_row_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": law_bundle_component_row_completeness_rows,
                "expected_rows": {
                    completeness_id: {}
                    for completeness_id in EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "law_bundle_component_row_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": law_bundle_component_row_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {}
                    for row in EXPECTED_LAW_BUNDLE_COMPONENT_ROW_COMPLETENESS_ROWS.values()
                },
                "id_attr": "contract_phrase",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    row_family_projection_by_id = index_row_family_projection_rows(
        row_family_projection_rows
    )
    named_row_family_status_payload = project_named_row_family_statuses(
        row_family_projection_rows_by_id=row_family_projection_by_id,
        specs=(
            NamedRowFamilyStatusProjectionSpec(
                payload_key="component_status_row_coverage_status",
                family_id="component_status_rows",
                status_key="coverage_status",
            ),
            NamedRowFamilyStatusProjectionSpec(
                payload_key="component_status_row_identity_projection_status",
                family_id="component_status_rows",
                status_key="identity_projection_status",
            ),
            NamedRowFamilyStatusProjectionSpec(
                payload_key="law_bundle_component_row_completeness_row_coverage_status",
                family_id="law_bundle_component_row_completeness_rows",
                status_key="coverage_status",
            ),
            NamedRowFamilyStatusProjectionSpec(
                payload_key="law_bundle_component_row_completeness_row_identity_projection_status",
                family_id="law_bundle_component_row_completeness_rows",
                status_key="identity_projection_status",
            ),
            NamedRowFamilyStatusProjectionSpec(
                payload_key="law_bundle_component_row_completeness_surface_coverage_status",
                family_id="law_bundle_component_row_completeness_surface",
                status_key="coverage_status",
            ),
            NamedRowFamilyStatusProjectionSpec(
                payload_key="law_bundle_component_row_completeness_surface_identity_projection_status",
                family_id="law_bundle_component_row_completeness_surface",
                status_key="identity_projection_status",
            ),
        ),
        fail_status=STATUS_FAIL_REQUIRED,
    )

    (
        component_validator_observation_reason_counts,
        component_validator_observation_reason_unknown_count,
        component_validator_observation_reason_non_applicable_count,
    ) = _component_validator_observation_reason_counts(
        bundle_violations,
        effective_component_validator_observation_reason_classifier_precedence_policy,
        effective_component_validator_observation_reason_parse_status_origin_policy,
        effective_component_validator_observation_reason_nonzero_rc_origin_policy,
        effective_component_validator_observation_reason_nonpass_status_origin_policy,
        effective_component_validator_observation_reason_prefixed_ontology_drift_origin_policy,
        effective_component_validator_observation_reason_residual_not_applicable_policy,
        effective_component_validator_observation_reason_exclusion_origin_policy,
    )
    component_validator_observation_reason_partition_total_count = (
        sum(component_validator_observation_reason_counts.values())
        + component_validator_observation_reason_unknown_count
        + component_validator_observation_reason_non_applicable_count
    )
    component_validator_observation_reason_source_total_count = (
        sum(component_validator_observation_reason_counts.values())
        + component_validator_observation_reason_unknown_count
        + component_validator_observation_reason_non_applicable_count
    )
    expected_component_validator_observation_reason_source_total_count = len(bundle_violations)
    expected_component_validator_observation_reason_partition_total_count = len(bundle_violations)
    component_validator_observation_reason_source_total_count_before_fail_close = (
        component_validator_observation_reason_source_total_count
    )
    component_validator_observation_reason_partition_total_count_before_fail_close = (
        component_validator_observation_reason_partition_total_count
    )
    component_validator_observation_reason_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_component_validator_observation_reason_unclassified_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_UNCLASSIFIED_POLICY
            and component_validator_observation_reason_unknown_count
        )
        else STATUS_PASS_REQUIRED
    )
    if component_validator_observation_reason_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_component_validator_observation_reason_unclassified")
        if not error_code:
            error_code = ERR_REGISTRY
    component_validator_observation_reason_source_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_component_validator_observation_reason_source_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_SOURCE_POLICY
            and component_validator_observation_reason_source_total_count
            != expected_component_validator_observation_reason_source_total_count
        )
        else STATUS_PASS_REQUIRED
    )
    if component_validator_observation_reason_source_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_component_validator_observation_reason_source_incomplete")
        if not error_code:
            error_code = ERR_REGISTRY
    component_validator_observation_reason_partition_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_component_validator_observation_reason_partition_policy
            == COMPONENT_VALIDATOR_OBSERVATION_REASON_PARTITION_POLICY
            and component_validator_observation_reason_partition_total_count
            != expected_component_validator_observation_reason_partition_total_count
        )
        else STATUS_PASS_REQUIRED
    )
    if component_validator_observation_reason_partition_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_component_validator_observation_reason_partition_incomplete")
        if not error_code:
            error_code = ERR_REGISTRY

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (bundle_violations or anchor_violations):
        error_code = ERR_BUNDLE

    structure_violation_stale_reasons = [
        f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations
    ]
    bundle_violation_stale_reasons = [
        "bundle_violation:"
        f"{str(row.get('component_id') or row.get('field') or 'root_corpus_law_bundle')}:"
        f"{str(row.get('reason') or 'unknown')}"
        for row in bundle_violations
    ]
    anchor_violation_stale_reasons = [
        f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations
    ]
    projected_violation_reason_count = (
        len(structure_violation_stale_reasons)
        + len(bundle_violation_stale_reasons)
        + len(anchor_violation_stale_reasons)
    )
    expected_projected_violation_reason_count = (
        len(structure_violations) + len(bundle_violations) + len(anchor_violations)
    )
    direct_stale_reason_origin_counts, registry_direct_stale_reason_unknown_count = (
        _direct_stale_reason_origin_counts(
            stale_reasons,
            effective_registry_direct_stale_reason_origin_classifier_precedence_policy,
            effective_registry_direct_stale_reason_alias_origin_policy,
            effective_registry_direct_stale_reason_document_origin_policy,
            effective_registry_direct_stale_reason_required_surface_origin_policy,
            effective_registry_direct_stale_reason_contract_row_origin_policy,
            effective_registry_direct_stale_reason_residual_unknown_policy,
        )
    )
    registry_direct_stale_reason_origin_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_registry_direct_stale_reason_unclassified_policy
            == REGISTRY_DIRECT_STALE_REASON_UNCLASSIFIED_POLICY
            and registry_direct_stale_reason_unknown_count
        )
        else STATUS_PASS_REQUIRED
    )
    if registry_direct_stale_reason_origin_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_origin_unclassified")
        if not error_code:
            error_code = ERR_REGISTRY
    direct_stale_reason_origin_counts, registry_direct_stale_reason_unknown_count = (
        _direct_stale_reason_origin_counts(
            stale_reasons,
            effective_registry_direct_stale_reason_origin_classifier_precedence_policy,
            effective_registry_direct_stale_reason_alias_origin_policy,
            effective_registry_direct_stale_reason_document_origin_policy,
            effective_registry_direct_stale_reason_required_surface_origin_policy,
            effective_registry_direct_stale_reason_contract_row_origin_policy,
            effective_registry_direct_stale_reason_residual_unknown_policy,
        )
    )
    registry_direct_stale_reason_source_total_count = (
        sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
    )
    registry_direct_stale_reason_partition_total_count = (
        sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
    )
    direct_stale_reason_count_before_violation_projection = len(stale_reasons)
    expected_registry_direct_stale_reason_source_total_count = (
        direct_stale_reason_count_before_violation_projection
    )
    expected_registry_direct_stale_reason_partition_total_count = (
        direct_stale_reason_count_before_violation_projection
    )
    registry_direct_stale_reason_source_total_count_before_fail_close = (
        registry_direct_stale_reason_source_total_count
    )
    registry_direct_stale_reason_partition_total_count_before_fail_close = (
        registry_direct_stale_reason_partition_total_count
    )
    registry_direct_stale_reason_source_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_registry_direct_stale_reason_source_policy == REGISTRY_DIRECT_STALE_REASON_SOURCE_POLICY
            and registry_direct_stale_reason_source_total_count
            != expected_registry_direct_stale_reason_source_total_count
        )
        else STATUS_PASS_REQUIRED
    )
    registry_direct_stale_reason_partition_status = (
        STATUS_FAIL_REQUIRED
        if (
            effective_registry_direct_stale_reason_partition_policy
            == REGISTRY_DIRECT_STALE_REASON_PARTITION_POLICY
            and registry_direct_stale_reason_partition_total_count
            != expected_registry_direct_stale_reason_partition_total_count
        )
        else STATUS_PASS_REQUIRED
    )
    if registry_direct_stale_reason_source_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_source_incomplete")
        if not error_code:
            error_code = ERR_REGISTRY
        direct_stale_reason_origin_counts, registry_direct_stale_reason_unknown_count = (
            _direct_stale_reason_origin_counts(
                stale_reasons,
                effective_registry_direct_stale_reason_origin_classifier_precedence_policy,
                effective_registry_direct_stale_reason_alias_origin_policy,
                effective_registry_direct_stale_reason_document_origin_policy,
                effective_registry_direct_stale_reason_required_surface_origin_policy,
                effective_registry_direct_stale_reason_contract_row_origin_policy,
                effective_registry_direct_stale_reason_residual_unknown_policy,
            )
        )
        registry_direct_stale_reason_source_total_count = (
            sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
        )
        registry_direct_stale_reason_partition_total_count = (
            sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
        )
        direct_stale_reason_count_before_violation_projection = len(stale_reasons)
    if registry_direct_stale_reason_partition_status == STATUS_FAIL_REQUIRED:
        stale_reasons.append("root_corpus_law_bundle_registry_direct_stale_reason_partition_incomplete")
        if not error_code:
            error_code = ERR_REGISTRY
        direct_stale_reason_origin_counts, registry_direct_stale_reason_unknown_count = (
            _direct_stale_reason_origin_counts(
                stale_reasons,
                effective_registry_direct_stale_reason_origin_classifier_precedence_policy,
                effective_registry_direct_stale_reason_alias_origin_policy,
                effective_registry_direct_stale_reason_document_origin_policy,
                effective_registry_direct_stale_reason_required_surface_origin_policy,
                effective_registry_direct_stale_reason_contract_row_origin_policy,
                effective_registry_direct_stale_reason_residual_unknown_policy,
            )
        )
        registry_direct_stale_reason_source_total_count = (
            sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
        )
        registry_direct_stale_reason_partition_total_count = (
            sum(direct_stale_reason_origin_counts.values()) + registry_direct_stale_reason_unknown_count
        )
        direct_stale_reason_count_before_violation_projection = len(stale_reasons)
    registry_precedence_reason_count = direct_stale_reason_count_before_violation_projection
    violation_projection_incomplete = (
        effective_violation_projection_policy == VIOLATION_PROJECTION_POLICY
        and projected_violation_reason_count != expected_projected_violation_reason_count
    )
    violation_projection_status = (
        STATUS_FAIL_REQUIRED if violation_projection_incomplete else STATUS_PASS_REQUIRED
    )

    stale_reasons.extend(structure_violation_stale_reasons)
    stale_reasons.extend(bundle_violation_stale_reasons)
    stale_reasons.extend(anchor_violation_stale_reasons)
    if violation_projection_incomplete:
        stale_reasons.append("root_corpus_law_bundle_violation_projection_incomplete")
        if not error_code:
            error_code = ERR_BUNDLE

    derived_status_from_stale_reasons = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    derived_failure_class = "pass"
    if effective_failure_classification_policy == FAILURE_CLASSIFICATION_POLICY:
        if (
            effective_registry_class_admission_policy == REGISTRY_CLASS_ADMISSION_POLICY
            and direct_stale_reason_count_before_violation_projection
        ):
            derived_failure_class = "registry"
        elif structure_violations:
            derived_failure_class = "structure"
        elif bundle_violations or anchor_violations or violation_projection_incomplete:
            derived_failure_class = "bundle"
    derived_error_code_from_precedence = ""
    if effective_error_code_precedence_policy == ERROR_CODE_PRECEDENCE_POLICY:
        if derived_failure_class == "registry":
            derived_error_code_from_precedence = ERR_REGISTRY
        elif derived_failure_class == "structure":
            derived_error_code_from_precedence = ERR_STRUCTURE
        elif derived_failure_class == "bundle":
            derived_error_code_from_precedence = ERR_BUNDLE
    final_error_code = (
        "" if derived_status_from_stale_reasons == STATUS_PASS_REQUIRED else (
            derived_error_code_from_precedence or error_code or ERR_BUNDLE
        )
    )
    status = (
        derived_status_from_stale_reasons
        if effective_final_status_derivation_policy == FINAL_STATUS_DERIVATION_POLICY
        else derived_status_from_stale_reasons
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": final_error_code,
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
        "component_validator_returncode_observation_contract": component_validator_returncode_observation_contract,
        "component_validator_output_contract": component_validator_output_contract,
        "component_validator_root_doc_anchor_contract": component_validator_root_doc_anchor_contract,
        "component_validator_row_projection_contract": component_validator_row_projection_contract,
        "component_probe_shadow_bootstrap_contract": component_probe_shadow_bootstrap_contract,
        "component_validator_invocation_contract": component_validator_invocation_contract,
        "component_validator_output_channel_contract": component_validator_output_channel_contract,
        "component_validator_stderr_isolation_contract": component_validator_stderr_isolation_contract,
        "component_validator_stdio_text_decoding_contract": component_validator_stdio_text_decoding_contract,
        "component_validator_stdout_normalization_contract": component_validator_stdout_normalization_contract,
        "component_validator_stdout_presence_contract": component_validator_stdout_presence_contract,
        "component_validator_stdout_framing_contract": component_validator_stdout_framing_contract,
        "component_validator_status_key_resolution_contract": component_validator_status_key_resolution_contract,
        "component_validator_status_literal_contract": component_validator_status_literal_contract,
        "component_validator_execution_input_contract": component_validator_execution_input_contract,
        "component_validator_verdict_admission_timing_contract": component_validator_verdict_admission_timing_contract,
        "component_validator_execution_timeout_contract": component_validator_execution_timeout_contract,
        "component_validator_working_directory_contract": component_validator_working_directory_contract,
        "component_validator_execution_environment_contract": component_validator_execution_environment_contract,
        "component_validator_execution_transport_contract": component_validator_execution_transport_contract,
        "component_validator_contract_drift_execution_policy": component_validator_contract_drift_execution_policy,
        "component_validator_contract_surface_projection_policy": (
            component_validator_contract_surface_projection_policy
        ),
        "component_validator_observation_continuity_policy": component_validator_observation_continuity_policy,
        "component_status_row_coverage_policy": component_status_row_coverage_policy,
        "violation_projection_policy": violation_projection_policy,
        "final_status_derivation_policy": final_status_derivation_policy,
        "error_code_precedence_policy": error_code_precedence_policy,
        "failure_classification_policy": failure_classification_policy,
        "registry_class_admission_policy": registry_class_admission_policy,
        "registry_direct_stale_reason_origin_policy": registry_direct_stale_reason_origin_policy,
        "registry_direct_stale_reason_alias_origin_policy": (
            registry_direct_stale_reason_alias_origin_policy
        ),
        "registry_direct_stale_reason_document_origin_policy": (
            registry_direct_stale_reason_document_origin_policy
        ),
        "registry_direct_stale_reason_required_surface_origin_policy": (
            registry_direct_stale_reason_required_surface_origin_policy
        ),
        "registry_direct_stale_reason_contract_row_origin_policy": (
            registry_direct_stale_reason_contract_row_origin_policy
        ),
        "registry_direct_stale_reason_source_policy": registry_direct_stale_reason_source_policy,
        "registry_direct_stale_reason_partition_policy": (
            registry_direct_stale_reason_partition_policy
        ),
        "registry_direct_stale_reason_origin_classifier_precedence_policy": (
            registry_direct_stale_reason_origin_classifier_precedence_policy
        ),
        "registry_direct_stale_reason_residual_unknown_policy": (
            registry_direct_stale_reason_residual_unknown_policy
        ),
        "registry_direct_stale_reason_unclassified_policy": (
            registry_direct_stale_reason_unclassified_policy
        ),
        "component_validator_observation_reason_admission_policy": (
            component_validator_observation_reason_admission_policy
        ),
        "component_validator_observation_reason_parse_status_origin_policy": (
            component_validator_observation_reason_parse_status_origin_policy
        ),
        "component_validator_observation_reason_nonzero_rc_origin_policy": (
            component_validator_observation_reason_nonzero_rc_origin_policy
        ),
        "component_validator_observation_reason_nonpass_status_origin_policy": (
            component_validator_observation_reason_nonpass_status_origin_policy
        ),
        "component_validator_observation_reason_prefixed_ontology_drift_origin_policy": (
            component_validator_observation_reason_prefixed_ontology_drift_origin_policy
        ),
        "component_validator_observation_reason_residual_not_applicable_policy": (
            component_validator_observation_reason_residual_not_applicable_policy
        ),
        "component_validator_observation_reason_classifier_precedence_policy": (
            component_validator_observation_reason_classifier_precedence_policy
        ),
        "component_validator_observation_reason_exclusion_origin_policy": (
            component_validator_observation_reason_exclusion_origin_policy
        ),
        "component_validator_observation_reason_exclusion_policy": (
            component_validator_observation_reason_exclusion_policy
        ),
        "component_validator_observation_reason_source_policy": (
            component_validator_observation_reason_source_policy
        ),
        "component_validator_observation_reason_partition_policy": (
            component_validator_observation_reason_partition_policy
        ),
        "component_validator_observation_reason_unclassified_policy": (
            component_validator_observation_reason_unclassified_policy
        ),
        "derived_status_from_stale_reasons": derived_status_from_stale_reasons,
        "derived_failure_class": derived_failure_class,
        "derived_error_code_from_precedence": derived_error_code_from_precedence,
        "bundle_anchor_check_count": len(anchor_checks),
        "component_count": len(components),
        "law_bundle_component_row_completeness_row_count": len(
            law_bundle_component_row_completeness_rows
        ),
        "component_status_row_count": len(component_status_rows),
        "expected_component_status_row_count": len(sorted_components),
        **named_row_family_status_payload,
        **project_root_contract_support_projection(
            prefix="law_bundle",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "structure_violation_count": len(structure_violations),
        "bundle_violation_count": len(bundle_violations),
        "anchor_violation_count": len(anchor_violations),
        "direct_stale_reason_count_before_violation_projection": (
            direct_stale_reason_count_before_violation_projection
        ),
        "registry_direct_stale_reason_origin_status": registry_direct_stale_reason_origin_status,
        "registry_direct_stale_reason_source_status": registry_direct_stale_reason_source_status,
        "registry_direct_stale_reason_partition_status": (
            registry_direct_stale_reason_partition_status
        ),
        "direct_stale_reason_origin_counts": dict(direct_stale_reason_origin_counts),
        "registry_direct_stale_reason_unknown_count": registry_direct_stale_reason_unknown_count,
        "expected_registry_direct_stale_reason_source_total_count": (
            expected_registry_direct_stale_reason_source_total_count
        ),
        "expected_registry_direct_stale_reason_partition_total_count": (
            expected_registry_direct_stale_reason_partition_total_count
        ),
        "registry_direct_stale_reason_source_total_count_before_fail_close": (
            registry_direct_stale_reason_source_total_count_before_fail_close
        ),
        "registry_direct_stale_reason_source_total_count": registry_direct_stale_reason_source_total_count,
        "registry_direct_stale_reason_partition_total_count_before_fail_close": (
            registry_direct_stale_reason_partition_total_count_before_fail_close
        ),
        "registry_direct_stale_reason_partition_total_count": (
            registry_direct_stale_reason_partition_total_count
        ),
        "component_validator_observation_reason_status": component_validator_observation_reason_status,
        "component_validator_observation_reason_source_status": (
            component_validator_observation_reason_source_status
        ),
        "component_validator_observation_reason_partition_status": (
            component_validator_observation_reason_partition_status
        ),
        "component_validator_observation_reason_counts": dict(
            component_validator_observation_reason_counts
        ),
        "component_validator_observation_reason_unknown_count": (
            component_validator_observation_reason_unknown_count
        ),
        "component_validator_observation_reason_non_applicable_count": (
            component_validator_observation_reason_non_applicable_count
        ),
        "expected_component_validator_observation_reason_source_total_count": (
            expected_component_validator_observation_reason_source_total_count
        ),
        "expected_component_validator_observation_reason_partition_total_count": (
            expected_component_validator_observation_reason_partition_total_count
        ),
        "component_validator_observation_reason_source_total_count_before_fail_close": (
            component_validator_observation_reason_source_total_count_before_fail_close
        ),
        "component_validator_observation_reason_source_total_count": (
            component_validator_observation_reason_source_total_count
        ),
        "component_validator_observation_reason_partition_total_count_before_fail_close": (
            component_validator_observation_reason_partition_total_count_before_fail_close
        ),
        "component_validator_observation_reason_partition_total_count": (
            component_validator_observation_reason_partition_total_count
        ),
        "registry_class_reason_count": registry_precedence_reason_count,
        "registry_precedence_reason_count": registry_precedence_reason_count,
        "projected_violation_reason_count": projected_violation_reason_count,
        "expected_projected_violation_reason_count": (
            expected_projected_violation_reason_count
        ),
        "violation_projection_status": violation_projection_status,
        "stale_reason_count": len(stale_reasons),
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
        "row_family_projection_rows": row_family_projection_rows,
        "law_bundle_component_row_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in law_bundle_component_row_completeness_rows
        ],
        "law_bundle_component_row_completeness_surface": {
            "rel_path": law_bundle_component_row_completeness_surface.rel_path,
            "entry_count": len(law_bundle_component_row_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in law_bundle_component_row_completeness_surface.rows
            ],
            "extraction_violations": list(
                law_bundle_component_row_completeness_surface.extraction_violations
            ),
        },
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
