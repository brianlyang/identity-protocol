#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-law-bundle-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "PASS_REQUIRED", payload
assert payload["component_count"] == 10, payload
assert payload["machine_registry_completeness_current_file"] == "identity/protocol/mappings/root-machine-registry-completeness.current.yaml", payload
assert payload["descriptor_schema_source_component_id"] == "root_machine_registry_completeness", payload
assert payload["descriptor_schema_source_binding_mode"] == "canonical_source_component_current_only", payload
assert payload["descriptor_schema_source_substitution_policy"] == "forbidden", payload
assert payload["descriptor_schema_fallback_policy"] == "fail_closed", payload
assert payload["descriptor_schema_local_reauthoring_policy"] == "forbidden", payload
assert payload["descriptor_schema_local_reconstruction_policy"] == "forbidden", payload
assert payload["component_self_describing_family_requirement_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["component_self_describing_family_requirement_local_override_policy"] == "forbidden", payload
assert payload["component_self_describing_family_requirement_local_redeclaration_policy"] == "forbidden", payload
assert payload["component_self_describing_family_requirement_fallback_policy"] == "fail_closed", payload
assert payload["descriptor_family_surface_binding_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["descriptor_family_surface_binding_local_override_policy"] == "forbidden", payload
assert payload["descriptor_family_surface_binding_local_redeclaration_policy"] == "forbidden", payload
assert payload["descriptor_family_surface_binding_fallback_policy"] == "fail_closed", payload
assert payload["descriptor_repo_rel_path_pattern_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["descriptor_repo_rel_path_pattern_local_redeclaration_policy"] == "forbidden", payload
assert payload["descriptor_repo_rel_path_pattern_fallback_policy"] == "fail_closed", payload
assert payload["descriptor_repo_rel_path_discipline_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["descriptor_repo_rel_path_discipline_local_override_policy"] == "forbidden", payload
assert payload["descriptor_repo_rel_path_discipline_local_redeclaration_policy"] == "forbidden", payload
assert payload["descriptor_repo_rel_path_discipline_fallback_policy"] == "fail_closed", payload
assert payload["component_current_version_naming_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["component_current_version_naming_local_override_policy"] == "forbidden", payload
assert payload["component_current_version_naming_local_redeclaration_policy"] == "forbidden", payload
assert payload["component_current_version_naming_fallback_policy"] == "fail_closed", payload
assert payload["component_registry_child_membership_inheritance_mode"] == "inherit_machine_registry_completeness_current_only", payload
assert payload["component_registry_child_membership_local_override_policy"] == "forbidden", payload
assert payload["component_registry_child_membership_local_redeclaration_policy"] == "forbidden", payload
assert payload["component_registry_child_membership_fallback_policy"] == "fail_closed", payload
assert payload["component_descriptor_resolution_mode"] == "current_alias_only", payload
assert payload["component_descriptor_version_pinning_policy"] == "forbidden", payload
assert payload["component_descriptor_concordance_local_waiver_policy"] == "forbidden", payload
assert payload["component_validator_status_requirement"] == "PASS_REQUIRED", payload
assert payload["component_validator_execution_failure_policy"] == "fail_closed", payload
assert payload["component_validator_returncode_observation_contract"] == "nonzero_returncode_observed_without_host_exception_overlay", payload
assert payload["component_validator_output_contract"] == "json_object_with_disclosed_status_key", payload
assert payload["component_validator_invocation_contract"] == "python3_repo_root_json_only", payload
assert payload["component_validator_output_channel_contract"] == "stdout_only", payload
assert payload["component_validator_stderr_isolation_contract"] == "stderr_captured_separate_from_stdout", payload
assert payload["component_validator_stdio_text_decoding_contract"] == "utf8_strict_text_decode_no_locale_overlay", payload
assert payload["component_validator_stdout_normalization_contract"] == "outer_whitespace_trim_only_before_json_decode", payload
assert payload["component_validator_stdout_presence_contract"] == "nonempty_after_outer_whitespace_trim_required", payload
assert payload["component_validator_stdout_framing_contract"] == "whole_stdout_single_json_object", payload
assert payload["component_validator_status_key_resolution_contract"] == "top_level_direct_member_only", payload
assert payload["component_validator_status_literal_contract"] == "exact_canonical_string_literal", payload
assert payload["component_validator_execution_input_contract"] == "stdin_devnull_noninteractive", payload
assert payload["component_validator_verdict_admission_timing_contract"] == "completed_process_post_exit_only", payload
assert payload["component_validator_execution_timeout_contract"] == "no_local_timeout_overlay", payload
assert payload["component_validator_working_directory_contract"] == "repo_root", payload
assert payload["component_validator_execution_environment_contract"] == "inherited_parent_process_env_no_local_overlay", payload
assert payload["component_validator_execution_transport_contract"] == "local_direct_subprocess_vector", payload
assert payload["component_validator_contract_drift_execution_policy"] == "execute_under_canonical_contract_and_fail_closed_on_drift", payload
assert payload["component_validator_contract_surface_projection_policy"] == "bundle_summary_disclosed_component_rows_effective_execution_surface", payload
assert payload["component_validator_observation_continuity_policy"] == "continue_bound_component_observation_under_canonical_surface_before_final_fail_close", payload
assert payload["component_status_row_coverage_policy"] == "all_bound_components_must_emit_status_rows_before_final_status", payload
assert payload["violation_projection_policy"] == "all_structure_bundle_anchor_violations_projected_into_stale_reasons_before_final_status", payload
assert payload["final_status_derivation_policy"] == "pass_required_if_and_only_if_stale_reasons_empty_after_violation_projection_else_fail_required", payload
assert payload["derived_status_from_stale_reasons"] == "PASS_REQUIRED", payload
assert payload["bundle_redeclares_required_repo_rel_path_patterns"] is False, payload
assert payload["bundle_local_required_repo_rel_path_patterns"] == {}, payload
assert payload["bundle_redeclares_family_surface_binding_governance"] is False, payload
assert payload["bundle_local_family_surface_binding_governance"] == {}, payload
assert payload["bundle_redeclares_repo_rel_path_governance"] is False, payload
assert payload["bundle_local_repo_rel_path_governance"] == {}, payload
assert payload["bundle_redeclares_component_naming_governance"] is False, payload
assert payload["bundle_local_component_naming_governance"] == {}, payload
assert payload["bundle_redeclares_self_describing_family_requirement_governance"] is False, payload
assert payload["bundle_local_self_describing_family_requirement_governance"] == {}, payload
assert payload["bundle_redeclares_registry_child_membership_governance"] is False, payload
assert payload["bundle_local_registry_child_membership_governance"] == {}, payload
assert payload["required_component_descriptor_fields"] == [
    "validator_script",
    "probe_script",
    "common_script",
    "status_key",
    "error_codes",
], payload
assert payload["required_component_descriptor_field_modes"] == {
    "validator_script": "repo_rel_path",
    "probe_script": "repo_rel_path",
    "common_script": "repo_rel_path",
    "status_key": "validator_status_key",
    "error_codes": "validator_error_code_list",
}, payload
assert payload["source_required_descriptor_fields"] == payload["required_component_descriptor_fields"], payload
assert payload["source_required_descriptor_field_modes"] == payload["required_component_descriptor_field_modes"], payload
assert payload["source_family_surface_stem_binding_policy"] == "family_id_surface_stem_congruent_or_explicit_override", payload
assert payload["source_family_surface_stem_overrides"] == {
    "root-corpus-registry": "root_corpus_governance",
}, payload
assert payload["source_repo_rel_path_scope_policy"] == "repo_root_relative_only", payload
assert payload["source_repo_rel_path_escape_policy"] == "fail_closed", payload
assert payload["source_repo_rel_path_role_typing_policy"] == "root_protocol_surface_patterns_required", payload
assert payload["source_repo_rel_path_surface_stem_policy"] == "cross_role_stem_coherent", payload
assert payload["source_root_family_prefix"] == "root-", payload
assert payload["source_current_suffix"] == ".current.yaml", payload
assert payload["source_version_regex"] == "^root-[a-z0-9-]+\\.v[0-9]+\\.yaml$", payload
assert payload["source_require_current_version_pairs"] is True, payload
assert payload["source_require_self_describing_families"] is True, payload
assert payload["source_registry_directory_rel_path"] == "identity/protocol/mappings", payload
assert payload["source_registry_current_file"] == "identity/protocol/mappings/root-corpus-registry.current.yaml", payload
assert payload["source_registered_mapping_children_count"] > 0, payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert payload["structure_violation_count"] == 0, payload
assert payload["bundle_violation_count"] == 0, payload
assert payload["anchor_violation_count"] == 0, payload
assert payload["projected_violation_reason_count"] == 0, payload
assert payload["stale_reason_count"] == 0, payload
assert all(row["component_status"] == "PASS_REQUIRED" for row in payload["component_status_rows"]), payload
assert all(
    row["validator_status_requirement"] == "PASS_REQUIRED"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_execution_failure_policy"] == "fail_closed"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_returncode_observation_contract"] == "nonzero_returncode_observed_without_host_exception_overlay"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_execution_environment_contract"] == "inherited_parent_process_env_no_local_overlay"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_execution_timeout_contract"] == "no_local_timeout_overlay"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_stdio_text_decoding_contract"] == "utf8_strict_text_decode_no_locale_overlay"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_stdout_normalization_contract"] == "outer_whitespace_trim_only_before_json_decode"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_stdout_presence_contract"] == "nonempty_after_outer_whitespace_trim_required"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_stdout_framing_contract"] == "whole_stdout_single_json_object"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_contract_drift_execution_policy"] == "execute_under_canonical_contract_and_fail_closed_on_drift"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_contract_surface_projection_policy"] == "bundle_summary_disclosed_component_rows_effective_execution_surface"
    for row in payload["component_status_rows"]
), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("descriptor_field_rows", []))
    for row in payload["component_status_rows"]
), payload
assert any(
    cell["field"] == "error_codes" and cell["descriptor_mode"] == "validator_error_code_list"
    for row in payload["component_status_rows"]
    for cell in row.get("descriptor_field_rows", [])
), payload
assert any(
    cell["field"] == "error_codes" and cell["status"] == "PASS_REQUIRED"
    for row in payload["component_status_rows"]
    for cell in row.get("descriptor_field_rows", [])
), payload
assert any(
    row["component_id"] == "root_corpus_governance"
    and row["component_mapping_family_id"] == "root-corpus-registry"
    and row["expected_component_surface_stem"] == "root_corpus_governance"
    and row["expected_component_surface_stem_source"] == "machine_registry_explicit_override"
    for row in payload["component_status_rows"]
), payload
PY

COMPONENT_VALIDATOR_STATUS_REQUIREMENT_REPO="${TMP_ROOT}/component-validator-status-requirement-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STATUS_REQUIREMENT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_REQUIREMENT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_status_requirement"] = "SKIPPED_NOT_REQUIRED"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STATUS_REQUIREMENT_JSON="${TMP_ROOT}/component-validator-status-requirement-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STATUS_REQUIREMENT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STATUS_REQUIREMENT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator status requirement drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_REQUIREMENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_status_requirement_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_status_requirement"] == "SKIPPED_NOT_REQUIRED", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert all(row["validator_status_requirement"] == "PASS_REQUIRED" for row in payload["component_status_rows"]), payload
PY

COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_REPO="${TMP_ROOT}/component-validator-execution-failure-policy-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_execution_failure_policy"] = "advisory_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_JSON="${TMP_ROOT}/component-validator-execution-failure-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator execution-failure policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_FAILURE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_execution_failure_policy_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_execution_failure_policy"] == "advisory_only", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert all(
    row["validator_execution_failure_policy"] == "fail_closed"
    for row in payload["component_status_rows"]
), payload
PY

COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_REPO="${TMP_ROOT}/component-validator-returncode-observation-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_returncode_observation_contract"] = "host_exception_overlay_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_JSON="${TMP_ROOT}/component-validator-returncode-observation-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator returncode-observation contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_RETURNCODE_OBSERVATION_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_returncode_observation_contract_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_returncode_observation_contract"] == "host_exception_overlay_allowed", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert all(
    row["validator_returncode_observation_contract"] == "nonzero_returncode_observed_without_host_exception_overlay"
    for row in payload["component_status_rows"]
), payload
PY

COMPONENT_VALIDATOR_OUTPUT_CONTRACT_REPO="${TMP_ROOT}/component-validator-output-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_OUTPUT_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_OUTPUT_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_output_contract"] = "human_log_scrape_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_OUTPUT_CONTRACT_JSON="${TMP_ROOT}/component-validator-output-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_OUTPUT_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_OUTPUT_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator output-contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_OUTPUT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_output_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_REPO="${TMP_ROOT}/component-validator-stdout-normalization-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_stdout_normalization_contract"] = "preferred_line_selection_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_JSON="${TMP_ROOT}/component-validator-stdout-normalization-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator stdout-normalization contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_NORMALIZATION_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_stdout_normalization_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_REPO="${TMP_ROOT}/component-validator-stdout-presence-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_stdout_presence_contract"] = "empty_stdout_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_JSON="${TMP_ROOT}/component-validator-stdout-presence-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator stdout-presence contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_PRESENCE_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_stdout_presence_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_INVOCATION_CONTRACT_REPO="${TMP_ROOT}/component-validator-invocation-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_INVOCATION_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_INVOCATION_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_invocation_contract"] = "shell_without_repo_root_or_json_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_INVOCATION_CONTRACT_JSON="${TMP_ROOT}/component-validator-invocation-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_INVOCATION_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_INVOCATION_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator invocation-contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_INVOCATION_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_invocation_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_REPO="${TMP_ROOT}/component-validator-contract-drift-execution-policy-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_contract_drift_execution_policy"] = "execute_under_drifted_contract_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_JSON="${TMP_ROOT}/component-validator-contract-drift-execution-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator contract-drift execution policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_CONTRACT_DRIFT_EXECUTION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_contract_drift_execution_policy_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_contract_drift_execution_policy"] == "execute_under_drifted_contract_allowed", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert all(
    row["validator_contract_drift_execution_policy"] == "execute_under_canonical_contract_and_fail_closed_on_drift"
    for row in payload["component_status_rows"]
), payload
assert all(
    row["validator_contract_surface_projection_policy"] == "bundle_summary_disclosed_component_rows_effective_execution_surface"
    for row in payload["component_status_rows"]
), payload
PY

COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_REPO="${TMP_ROOT}/component-validator-contract-surface-projection-policy-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_contract_surface_projection_policy"] = "bundle_summary_and_component_rows_follow_declared_drift"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_JSON="${TMP_ROOT}/component-validator-contract-surface-projection-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator contract-surface projection policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_CONTRACT_SURFACE_PROJECTION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_contract_surface_projection_policy_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_contract_surface_projection_policy"] == "bundle_summary_and_component_rows_follow_declared_drift", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
assert all(
    row["validator_contract_surface_projection_policy"] == "bundle_summary_disclosed_component_rows_effective_execution_surface"
    for row in payload["component_status_rows"]
), payload
PY

COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_REPO="${TMP_ROOT}/component-validator-observation-continuity-policy-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_observation_continuity_policy"] = "abort_component_observation_on_bundle_drift"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_JSON="${TMP_ROOT}/component-validator-observation-continuity-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator observation-continuity policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_OBSERVATION_CONTINUITY_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_observation_continuity_policy_invalid" in payload["stale_reasons"], payload
assert payload["component_validator_observation_continuity_policy"] == "abort_component_observation_on_bundle_drift", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
PY

COMPONENT_STATUS_ROW_COVERAGE_POLICY_REPO="${TMP_ROOT}/component-status-row-coverage-policy-drift-repo"
mirror_repo "${COMPONENT_STATUS_ROW_COVERAGE_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_STATUS_ROW_COVERAGE_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_status_row_coverage_policy"] = "partial_component_rows_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_STATUS_ROW_COVERAGE_POLICY_JSON="${TMP_ROOT}/component-status-row-coverage-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_STATUS_ROW_COVERAGE_POLICY_REPO}" \
  --json-only >"${COMPONENT_STATUS_ROW_COVERAGE_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component status-row coverage policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_STATUS_ROW_COVERAGE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_status_row_coverage_policy_invalid" in payload["stale_reasons"], payload
assert payload["component_status_row_coverage_policy"] == "partial_component_rows_allowed", payload
assert payload["component_status_row_count"] == payload["component_count"] == 10, payload
PY

VIOLATION_PROJECTION_POLICY_REPO="${TMP_ROOT}/violation-projection-policy-drift-repo"
mirror_repo "${VIOLATION_PROJECTION_POLICY_REPO}"
python3 - <<'PY' "${VIOLATION_PROJECTION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["violation_projection_policy"] = "local_violation_rows_may_remain_unprojected"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

VIOLATION_PROJECTION_POLICY_JSON="${TMP_ROOT}/violation-projection-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${VIOLATION_PROJECTION_POLICY_REPO}" \
  --json-only >"${VIOLATION_PROJECTION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed violation projection policy drift"
  exit 1
fi

python3 - <<'PY' "${VIOLATION_PROJECTION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_violation_projection_policy_invalid" in payload["stale_reasons"], payload
assert payload["violation_projection_policy"] == "local_violation_rows_may_remain_unprojected", payload
assert payload["projected_violation_reason_count"] == 0, payload
PY

FINAL_STATUS_DERIVATION_POLICY_REPO="${TMP_ROOT}/final-status-derivation-policy-drift-repo"
mirror_repo "${FINAL_STATUS_DERIVATION_POLICY_REPO}"
python3 - <<'PY' "${FINAL_STATUS_DERIVATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["final_status_derivation_policy"] = "local_verdict_path_may_bypass_stale_reasons"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FINAL_STATUS_DERIVATION_POLICY_JSON="${TMP_ROOT}/final-status-derivation-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${FINAL_STATUS_DERIVATION_POLICY_REPO}" \
  --json-only >"${FINAL_STATUS_DERIVATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed final status derivation policy drift"
  exit 1
fi

python3 - <<'PY' "${FINAL_STATUS_DERIVATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_final_status_derivation_policy_invalid" in payload["stale_reasons"], payload
assert payload["final_status_derivation_policy"] == "local_verdict_path_may_bypass_stale_reasons", payload
assert payload["derived_status_from_stale_reasons"] == "FAIL_REQUIRED", payload
assert payload["stale_reason_count"] >= 1, payload
PY

MISSING_COMPONENT_VALIDATOR_REPO="${TMP_ROOT}/missing-component-validator-repo"
mirror_repo "${MISSING_COMPONENT_VALIDATOR_REPO}"
rm -f "${MISSING_COMPONENT_VALIDATOR_REPO}/scripts/validate_protocol_root_corpus_precedence.py"

MISSING_COMPONENT_VALIDATOR_JSON="${TMP_ROOT}/missing-component-validator.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${MISSING_COMPONENT_VALIDATOR_REPO}" \
  --json-only >"${MISSING_COMPONENT_VALIDATOR_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing component validator coverage case"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPONENT_VALIDATOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert payload["derived_status_from_stale_reasons"] == payload["protocol_root_corpus_law_bundle_status"], payload
assert payload["component_status_row_count"] == payload["component_count"] - 1, payload
assert payload["bundle_violation_count"] >= 2, payload
assert payload["projected_violation_reason_count"] == (
    payload["structure_violation_count"] + payload["bundle_violation_count"] + payload["anchor_violation_count"]
), payload
assert payload["stale_reason_count"] == payload["projected_violation_reason_count"], payload
assert "bundle_violation:root_corpus_law_bundle:component_status_row_coverage_incomplete" in payload["stale_reasons"], payload
assert "bundle_violation:root_corpus_precedence:component_validator_missing" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_REPO="${TMP_ROOT}/component-validator-output-channel-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_output_channel_contract"] = "stderr_allowed_as_verdict_channel"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_JSON="${TMP_ROOT}/component-validator-output-channel-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator output-channel contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_OUTPUT_CHANNEL_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_output_channel_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_REPO="${TMP_ROOT}/component-validator-stderr-isolation-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_stderr_isolation_contract"] = "stderr_merged_into_stdout_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_JSON="${TMP_ROOT}/component-validator-stderr-isolation-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator stderr-isolation contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STDERR_ISOLATION_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_stderr_isolation_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_REPO="${TMP_ROOT}/component-validator-stdio-text-decoding-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_stdio_text_decoding_contract"] = "ambient_locale_decode_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_JSON="${TMP_ROOT}/component-validator-stdio-text-decoding-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator stdio text-decoding contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STDIO_TEXT_DECODING_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_stdio_text_decoding_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_REPO="${TMP_ROOT}/component-validator-stdout-framing-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_stdout_framing_contract"] = "mixed_stdout_fragment_extraction_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_JSON="${TMP_ROOT}/component-validator-stdout-framing-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator stdout-framing contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STDOUT_FRAMING_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_stdout_framing_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_REPO="${TMP_ROOT}/component-validator-status-key-resolution-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_status_key_resolution_contract"] = "nested_alias_pointer_search_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_JSON="${TMP_ROOT}/component-validator-status-key-resolution-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator status-key resolution contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_KEY_RESOLUTION_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_status_key_resolution_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_REPO="${TMP_ROOT}/component-validator-status-literal-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_status_literal_contract"] = "trimmed_casefolded_alias_literals_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_JSON="${TMP_ROOT}/component-validator-status-literal-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator status-literal contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_STATUS_LITERAL_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_status_literal_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_REPO="${TMP_ROOT}/component-validator-execution-input-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_execution_input_contract"] = "ambient_stdin_inheritance_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_JSON="${TMP_ROOT}/component-validator-execution-input-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator execution-input contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_INPUT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_execution_input_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_REPO="${TMP_ROOT}/component-validator-verdict-admission-timing-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_verdict_admission_timing_contract"] = "partial_stream_preexit_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_JSON="${TMP_ROOT}/component-validator-verdict-admission-timing-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator verdict-admission timing contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_VERDICT_ADMISSION_TIMING_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_verdict_admission_timing_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_REPO="${TMP_ROOT}/component-validator-execution-timeout-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_execution_timeout_contract"] = "bundle_local_deadline_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_JSON="${TMP_ROOT}/component-validator-execution-timeout-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator execution-timeout contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_TIMEOUT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_execution_timeout_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_REPO="${TMP_ROOT}/component-validator-working-directory-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_working_directory_contract"] = "ambient_cwd_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_JSON="${TMP_ROOT}/component-validator-working-directory-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator working-directory contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_WORKING_DIRECTORY_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_working_directory_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_REPO="${TMP_ROOT}/component-validator-execution-environment-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_execution_environment_contract"] = "local_env_overlay_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_JSON="${TMP_ROOT}/component-validator-execution-environment-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator execution-environment contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_ENVIRONMENT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_execution_environment_contract_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_REPO="${TMP_ROOT}/component-validator-execution-transport-contract-drift-repo"
mirror_repo "${COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_REPO}"
python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_validator_execution_transport_contract"] = "shell_wrapped_or_remote_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_JSON="${TMP_ROOT}/component-validator-execution-transport-contract-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_REPO}" \
  --json-only >"${COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component validator execution-transport contract drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_VALIDATOR_EXECUTION_TRANSPORT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_validator_execution_transport_contract_invalid" in payload["stale_reasons"], payload
PY

SELF_DESCRIBING_POLICY_REPO="${TMP_ROOT}/component-self-describing-family-requirement-policy-drift-repo"
mirror_repo "${SELF_DESCRIBING_POLICY_REPO}"
python3 - <<'PY' "${SELF_DESCRIBING_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_self_describing_family_requirement_local_override_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SELF_DESCRIBING_POLICY_JSON="${TMP_ROOT}/component-self-describing-family-requirement-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SELF_DESCRIBING_POLICY_REPO}" \
  --json-only >"${SELF_DESCRIBING_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component self-describing-family requirement policy drift"
  exit 1
fi

python3 - <<'PY' "${SELF_DESCRIBING_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_self_describing_family_requirement_local_override_policy_invalid" in payload["stale_reasons"], payload
PY

SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_REPO="${TMP_ROOT}/component-self-describing-family-requirement-local-redeclaration-policy-drift-repo"
mirror_repo "${SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_REPO}"
python3 - <<'PY' "${SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_self_describing_family_requirement_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_JSON="${TMP_ROOT}/component-self-describing-family-requirement-local-redeclaration-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_REPO}" \
  --json-only >"${SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component self-describing-family requirement local-redeclaration-policy drift"
  exit 1
fi

python3 - <<'PY' "${SELF_DESCRIBING_LOCAL_REDECLARATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_self_describing_family_requirement_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

SELF_DESCRIBING_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/component-self-describing-family-requirement-local-redeclaration-repo"
mirror_repo "${SELF_DESCRIBING_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${SELF_DESCRIBING_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["require_self_describing_families"] = False
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SELF_DESCRIBING_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/component-self-describing-family-requirement-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SELF_DESCRIBING_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${SELF_DESCRIBING_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local self-describing-family requirement redeclaration"
  exit 1
fi

python3 - <<'PY' "${SELF_DESCRIBING_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "component_self_describing_family_requirement_governance_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_self_describing_family_requirement_governance"] is True, payload
PY

SELF_DESCRIBING_SOURCE_REPO="${TMP_ROOT}/component-self-describing-family-requirement-source-drift-repo"
mirror_repo "${SELF_DESCRIBING_SOURCE_REPO}"
python3 - <<'PY' "${SELF_DESCRIBING_SOURCE_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["require_self_describing_families"] = False
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SELF_DESCRIBING_SOURCE_JSON="${TMP_ROOT}/component-self-describing-family-requirement-source-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SELF_DESCRIBING_SOURCE_REPO}" \
  --json-only >"${SELF_DESCRIBING_SOURCE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed inherited self-describing-family requirement drift"
  exit 1
fi

python3 - <<'PY' "${SELF_DESCRIBING_SOURCE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_self_describing_family_requirement_not_inherited_from_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
PY

REGISTRY_CHILD_POLICY_REPO="${TMP_ROOT}/component-registry-child-membership-policy-drift-repo"
mirror_repo "${REGISTRY_CHILD_POLICY_REPO}"
python3 - <<'PY' "${REGISTRY_CHILD_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_registry_child_membership_local_override_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_CHILD_POLICY_JSON="${TMP_ROOT}/component-registry-child-membership-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REGISTRY_CHILD_POLICY_REPO}" \
  --json-only >"${REGISTRY_CHILD_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component registry-child membership policy drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_CHILD_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_registry_child_membership_local_override_policy_invalid" in payload["stale_reasons"], payload
PY

REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_REPO="${TMP_ROOT}/component-registry-child-membership-local-redeclaration-policy-drift-repo"
mirror_repo "${REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_REPO}"
python3 - <<'PY' "${REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_registry_child_membership_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_JSON="${TMP_ROOT}/component-registry-child-membership-local-redeclaration-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_REPO}" \
  --json-only >"${REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component registry-child membership local-redeclaration-policy drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_CHILD_LOCAL_REDECLARATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_registry_child_membership_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

REGISTRY_CHILD_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/component-registry-child-membership-local-redeclaration-repo"
mirror_repo "${REGISTRY_CHILD_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${REGISTRY_CHILD_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["registry_directory_rel_path"] = "identity/protocol/shadow-mappings"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_CHILD_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/component-registry-child-membership-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REGISTRY_CHILD_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${REGISTRY_CHILD_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local registry-child admission redeclaration"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_CHILD_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "component_registry_child_membership_governance_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_registry_child_membership_governance"] is True, payload
PY

SOURCE_REGISTRY_CHILD_REPO="${TMP_ROOT}/component-registry-child-membership-source-drift-repo"
mirror_repo "${SOURCE_REGISTRY_CHILD_REPO}"
python3 - <<'PY' "${SOURCE_REGISTRY_CHILD_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["registered_top_level_entries"]:
    if row.get("rel_path") == "identity/protocol/mappings":
        row["required_children"] = [
            child for child in row.get("required_children", [])
            if child != "root-corpus-ordering.current.yaml"
        ]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_REGISTRY_CHILD_JSON="${TMP_ROOT}/component-registry-child-membership-source-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_REGISTRY_CHILD_REPO}" \
  --json-only >"${SOURCE_REGISTRY_CHILD_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed inherited registry-child admission drift"
  exit 1
fi

python3 - <<'PY' "${SOURCE_REGISTRY_CHILD_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_current_file_not_admitted_by_inherited_registry_child_set"
    for row in payload["bundle_violations"]
), payload
PY

REPO_REL_PATTERN_POLICY_REPO="${TMP_ROOT}/descriptor-repo-rel-path-pattern-policy-drift-repo"
mirror_repo "${REPO_REL_PATTERN_POLICY_REPO}"
python3 - <<'PY' "${REPO_REL_PATTERN_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_repo_rel_path_pattern_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REPO_REL_PATTERN_POLICY_JSON="${TMP_ROOT}/descriptor-repo-rel-path-pattern-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REPO_REL_PATTERN_POLICY_REPO}" \
  --json-only >"${REPO_REL_PATTERN_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor repo-rel path pattern policy drift"
  exit 1
fi

python3 - <<'PY' "${REPO_REL_PATTERN_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_repo_rel_path_pattern_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

REPO_REL_PATTERN_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/descriptor-repo-rel-path-pattern-local-redeclaration-repo"
mirror_repo "${REPO_REL_PATTERN_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${REPO_REL_PATTERN_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_repo_rel_path_patterns"] = {
    "validator_script": "^scripts/validate_protocol_(?P<surface_stem>shadow_[a-z0-9_]+)\\.py$",
    "probe_script": "^scripts/ci/run_protocol_(?P<surface_stem>shadow_[a-z0-9_]+)_probes_ci\\.sh$",
    "common_script": "^scripts/(?P<surface_stem>shadow_[a-z0-9_]+)_common\\.py$",
}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REPO_REL_PATTERN_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/descriptor-repo-rel-path-pattern-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REPO_REL_PATTERN_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${REPO_REL_PATTERN_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local repo-rel path pattern redeclaration"
  exit 1
fi

python3 - <<'PY' "${REPO_REL_PATTERN_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_repo_rel_path_patterns_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_required_repo_rel_path_patterns"] is True, payload
PY

SOURCE_REPO_REL_PATTERN_REPO="${TMP_ROOT}/descriptor-repo-rel-path-pattern-source-missing-repo"
mirror_repo "${SOURCE_REPO_REL_PATTERN_REPO}"
python3 - <<'PY' "${SOURCE_REPO_REL_PATTERN_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_repo_rel_path_patterns"] = {}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_REPO_REL_PATTERN_JSON="${TMP_ROOT}/descriptor-repo-rel-path-pattern-source-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_REPO_REL_PATTERN_REPO}" \
  --json-only >"${SOURCE_REPO_REL_PATTERN_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing source repo-rel path patterns"
  exit 1
fi

python3 - <<'PY' "${SOURCE_REPO_REL_PATTERN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_repo_rel_path_patterns_missing_from_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
PY

REPO_REL_DISCIPLINE_POLICY_REPO="${TMP_ROOT}/descriptor-repo-rel-discipline-policy-drift-repo"
mirror_repo "${REPO_REL_DISCIPLINE_POLICY_REPO}"
python3 - <<'PY' "${REPO_REL_DISCIPLINE_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_repo_rel_path_discipline_local_override_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REPO_REL_DISCIPLINE_POLICY_JSON="${TMP_ROOT}/descriptor-repo-rel-discipline-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REPO_REL_DISCIPLINE_POLICY_REPO}" \
  --json-only >"${REPO_REL_DISCIPLINE_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor repo-rel discipline policy drift"
  exit 1
fi

python3 - <<'PY' "${REPO_REL_DISCIPLINE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_repo_rel_path_discipline_local_override_policy_invalid" in payload["stale_reasons"], payload
PY

REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_REPO="${TMP_ROOT}/descriptor-repo-rel-discipline-local-redeclaration-policy-drift-repo"
mirror_repo "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_REPO}"
python3 - <<'PY' "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_repo_rel_path_discipline_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_JSON="${TMP_ROOT}/descriptor-repo-rel-discipline-local-redeclaration-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_REPO}" \
  --json-only >"${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor repo-rel discipline local-redeclaration-policy drift"
  exit 1
fi

python3 - <<'PY' "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_repo_rel_path_discipline_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/descriptor-repo-rel-discipline-local-redeclaration-repo"
mirror_repo "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["repo_rel_path_scope_policy"] = "workspace_relative_allowed"
doc["repo_rel_path_escape_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/descriptor-repo-rel-discipline-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local repo-rel discipline redeclaration"
  exit 1
fi

python3 - <<'PY' "${REPO_REL_DISCIPLINE_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_repo_rel_path_governance_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_repo_rel_path_governance"] is True, payload
PY

SOURCE_REPO_REL_DISCIPLINE_REPO="${TMP_ROOT}/descriptor-repo-rel-discipline-source-missing-repo"
mirror_repo "${SOURCE_REPO_REL_DISCIPLINE_REPO}"
python3 - <<'PY' "${SOURCE_REPO_REL_DISCIPLINE_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["repo_rel_path_scope_policy"] = ""
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_REPO_REL_DISCIPLINE_JSON="${TMP_ROOT}/descriptor-repo-rel-discipline-source-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_REPO_REL_DISCIPLINE_REPO}" \
  --json-only >"${SOURCE_REPO_REL_DISCIPLINE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing source repo-rel discipline"
  exit 1
fi

python3 - <<'PY' "${SOURCE_REPO_REL_DISCIPLINE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_repo_rel_path_governance_missing_from_machine_registry_completeness"
    and "repo_rel_path_scope_policy" in row["missing_policy_fields"]
    for row in payload["bundle_violations"]
), payload
PY

COMPONENT_NAMING_POLICY_REPO="${TMP_ROOT}/component-current-version-naming-policy-drift-repo"
mirror_repo "${COMPONENT_NAMING_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_NAMING_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_current_version_naming_local_override_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_NAMING_POLICY_JSON="${TMP_ROOT}/component-current-version-naming-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_NAMING_POLICY_REPO}" \
  --json-only >"${COMPONENT_NAMING_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component current/version naming policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_NAMING_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_current_version_naming_local_override_policy_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_REPO="${TMP_ROOT}/component-current-version-naming-local-redeclaration-policy-drift-repo"
mirror_repo "${COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_current_version_naming_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_JSON="${TMP_ROOT}/component-current-version-naming-local-redeclaration-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_REPO}" \
  --json-only >"${COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component current/version naming local-redeclaration-policy drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_NAMING_LOCAL_REDECLARATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_current_version_naming_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_NAMING_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/component-current-version-naming-local-redeclaration-repo"
mirror_repo "${COMPONENT_NAMING_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${COMPONENT_NAMING_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["current_suffix"] = ".shadow.yaml"
doc["version_regex"] = "^shadow-[a-z0-9-]+\\.v[0-9]+\\.yaml$"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_NAMING_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/component-current-version-naming-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_NAMING_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${COMPONENT_NAMING_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local component current/version naming redeclaration"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_NAMING_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "component_current_version_naming_governance_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_component_naming_governance"] is True, payload
PY

SOURCE_COMPONENT_NAMING_REPO="${TMP_ROOT}/component-current-version-naming-source-missing-repo"
mirror_repo "${SOURCE_COMPONENT_NAMING_REPO}"
python3 - <<'PY' "${SOURCE_COMPONENT_NAMING_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["current_suffix"] = ""
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_COMPONENT_NAMING_JSON="${TMP_ROOT}/component-current-version-naming-source-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_COMPONENT_NAMING_REPO}" \
  --json-only >"${SOURCE_COMPONENT_NAMING_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing source current/version naming law"
  exit 1
fi

python3 - <<'PY' "${SOURCE_COMPONENT_NAMING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "component_current_version_naming_governance_missing_from_machine_registry_completeness"
    and "current_suffix" in row["missing_policy_fields"]
    for row in payload["bundle_violations"]
), payload
PY

SOURCE_FIELDS_REPO="${TMP_ROOT}/descriptor-schema-source-fields-missing-repo"
mirror_repo "${SOURCE_FIELDS_REPO}"
python3 - <<'PY' "${SOURCE_FIELDS_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_descriptor_fields"] = []
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_FIELDS_JSON="${TMP_ROOT}/descriptor-schema-source-fields-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_FIELDS_REPO}" \
  --json-only >"${SOURCE_FIELDS_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing descriptor-source fields"
  exit 1
fi

python3 - <<'PY' "${SOURCE_FIELDS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_schema_source_required_descriptor_fields_missing"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_fields_not_aligned_to_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
PY

SUBSTITUTION_POLICY_REPO="${TMP_ROOT}/descriptor-schema-substitution-policy-drift-repo"
mirror_repo "${SUBSTITUTION_POLICY_REPO}"
python3 - <<'PY' "${SUBSTITUTION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_schema_source_substitution_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUBSTITUTION_POLICY_JSON="${TMP_ROOT}/descriptor-schema-substitution-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SUBSTITUTION_POLICY_REPO}" \
  --json-only >"${SUBSTITUTION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor-source substitution drift"
  exit 1
fi

python3 - <<'PY' "${SUBSTITUTION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_schema_source_substitution_policy_invalid" in payload["stale_reasons"], payload
PY

SCHEMA_LOCAL_REAUTHORING_POLICY_REPO="${TMP_ROOT}/descriptor-schema-local-reauthoring-policy-drift-repo"
mirror_repo "${SCHEMA_LOCAL_REAUTHORING_POLICY_REPO}"
python3 - <<'PY' "${SCHEMA_LOCAL_REAUTHORING_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_schema_local_reauthoring_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SCHEMA_LOCAL_REAUTHORING_POLICY_JSON="${TMP_ROOT}/descriptor-schema-local-reauthoring-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SCHEMA_LOCAL_REAUTHORING_POLICY_REPO}" \
  --json-only >"${SCHEMA_LOCAL_REAUTHORING_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor schema local-reauthoring-policy drift"
  exit 1
fi

python3 - <<'PY' "${SCHEMA_LOCAL_REAUTHORING_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_schema_local_reauthoring_policy_invalid" in payload["stale_reasons"], payload
PY

FAMILY_BINDING_POLICY_REPO="${TMP_ROOT}/descriptor-family-binding-policy-drift-repo"
mirror_repo "${FAMILY_BINDING_POLICY_REPO}"
python3 - <<'PY' "${FAMILY_BINDING_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_family_surface_binding_local_override_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FAMILY_BINDING_POLICY_JSON="${TMP_ROOT}/descriptor-family-binding-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${FAMILY_BINDING_POLICY_REPO}" \
  --json-only >"${FAMILY_BINDING_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor-family binding local-override drift"
  exit 1
fi

python3 - <<'PY' "${FAMILY_BINDING_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_family_surface_binding_local_override_policy_invalid" in payload["stale_reasons"], payload
PY

FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_REPO="${TMP_ROOT}/descriptor-family-binding-local-redeclaration-policy-drift-repo"
mirror_repo "${FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_REPO}"
python3 - <<'PY' "${FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_family_surface_binding_local_redeclaration_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_JSON="${TMP_ROOT}/descriptor-family-binding-local-redeclaration-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_REPO}" \
  --json-only >"${FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor-family binding local-redeclaration-policy drift"
  exit 1
fi

python3 - <<'PY' "${FAMILY_BINDING_LOCAL_REDECLARATION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_family_surface_binding_local_redeclaration_policy_invalid" in payload["stale_reasons"], payload
PY

FAMILY_BINDING_FALLBACK_REPO="${TMP_ROOT}/descriptor-family-binding-fallback-policy-drift-repo"
mirror_repo "${FAMILY_BINDING_FALLBACK_REPO}"
python3 - <<'PY' "${FAMILY_BINDING_FALLBACK_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["descriptor_family_surface_binding_fallback_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FAMILY_BINDING_FALLBACK_JSON="${TMP_ROOT}/descriptor-family-binding-fallback-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${FAMILY_BINDING_FALLBACK_REPO}" \
  --json-only >"${FAMILY_BINDING_FALLBACK_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor-family binding fallback-policy drift"
  exit 1
fi

python3 - <<'PY' "${FAMILY_BINDING_FALLBACK_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_descriptor_family_surface_binding_fallback_policy_invalid" in payload["stale_reasons"], payload
PY

FAMILY_BINDING_LOCAL_REDECLARATION_REPO="${TMP_ROOT}/descriptor-family-binding-local-redeclaration-repo"
mirror_repo "${FAMILY_BINDING_LOCAL_REDECLARATION_REPO}"
python3 - <<'PY' "${FAMILY_BINDING_LOCAL_REDECLARATION_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["family_surface_stem_overrides"] = {"root-corpus-registry": "shadow_surface"}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FAMILY_BINDING_LOCAL_REDECLARATION_JSON="${TMP_ROOT}/descriptor-family-binding-local-redeclaration.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${FAMILY_BINDING_LOCAL_REDECLARATION_REPO}" \
  --json-only >"${FAMILY_BINDING_LOCAL_REDECLARATION_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed local family-surface binding governance redeclaration"
  exit 1
fi

python3 - <<'PY' "${FAMILY_BINDING_LOCAL_REDECLARATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_family_surface_binding_governance_local_redeclaration_forbidden"
    for row in payload["bundle_violations"]
), payload
assert payload["bundle_redeclares_family_surface_binding_governance"] is True, payload
PY

COMPONENT_RESOLUTION_POLICY_REPO="${TMP_ROOT}/component-descriptor-resolution-policy-drift-repo"
mirror_repo "${COMPONENT_RESOLUTION_POLICY_REPO}"
python3 - <<'PY' "${COMPONENT_RESOLUTION_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_descriptor_resolution_mode"] = "direct_version_allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_RESOLUTION_POLICY_JSON="${TMP_ROOT}/component-descriptor-resolution-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_RESOLUTION_POLICY_REPO}" \
  --json-only >"${COMPONENT_RESOLUTION_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component descriptor resolution drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_RESOLUTION_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_descriptor_resolution_mode_invalid" in payload["stale_reasons"], payload
PY

COMPONENT_CURRENT_ENTRY_REPO="${TMP_ROOT}/component-current-entry-drift-repo"
mirror_repo "${COMPONENT_CURRENT_ENTRY_REPO}"
python3 - <<'PY' "${COMPONENT_CURRENT_ENTRY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["current_file"] = "identity/protocol/mappings/root-corpus-ordering.v1.yaml"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_CURRENT_ENTRY_JSON="${TMP_ROOT}/component-current-entry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_CURRENT_ENTRY_REPO}" \
  --json-only >"${COMPONENT_CURRENT_ENTRY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed component current-entry bypass drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_CURRENT_ENTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_descriptor_not_current_entry"
    for row in payload["bundle_violations"]
), payload
PY

SCHEMA_SOURCE_REPO="${TMP_ROOT}/descriptor-schema-source-drift-repo"
mirror_repo "${SCHEMA_SOURCE_REPO}"
python3 - <<'PY' "${SCHEMA_SOURCE_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_descriptor_field_modes"]["error_codes"] = "repo_rel_path"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SCHEMA_SOURCE_JSON="${TMP_ROOT}/descriptor-schema-source-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SCHEMA_SOURCE_REPO}" \
  --json-only >"${SCHEMA_SOURCE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed machine-registry descriptor schema drift"
  exit 1
fi

python3 - <<'PY' "${SCHEMA_SOURCE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_field_modes_not_aligned_to_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
PY

SOURCE_FAMILY_OVERRIDE_REPO="${TMP_ROOT}/source-family-override-drift-repo"
mirror_repo "${SOURCE_FAMILY_OVERRIDE_REPO}"
python3 - <<'PY' "${SOURCE_FAMILY_OVERRIDE_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["family_surface_stem_overrides"] = {}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_FAMILY_OVERRIDE_JSON="${TMP_ROOT}/source-family-override-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${SOURCE_FAMILY_OVERRIDE_REPO}" \
  --json-only >"${SOURCE_FAMILY_OVERRIDE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing source family-surface override drift"
  exit 1
fi

python3 - <<'PY' "${SOURCE_FAMILY_OVERRIDE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_family_surface_stem_overrides_missing_from_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_corpus_governance"
    and row["reason"] == "component_family_surface_binding_not_inherited"
    for row in payload["bundle_violations"]
), payload
PY

MODE_REPO="${TMP_ROOT}/descriptor-mode-drift-repo"
mirror_repo "${MODE_REPO}"
python3 - <<'PY' "${MODE_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_component_descriptor_field_modes"]["error_codes"] = "repo_rel_path"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MODE_JSON="${TMP_ROOT}/descriptor-mode-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${MODE_REPO}" \
  --json-only >"${MODE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor-field mode drift"
  exit 1
fi

python3 - <<'PY' "${MODE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_machine_registry_completeness"
    and row["reason"] == "descriptor_field_modes_not_aligned_to_machine_registry_completeness"
    for row in payload["bundle_violations"]
), payload
PY

CONCORDANCE_WAIVER_POLICY_REPO="${TMP_ROOT}/descriptor-concordance-waiver-policy-drift-repo"
mirror_repo "${CONCORDANCE_WAIVER_POLICY_REPO}"
python3 - <<'PY' "${CONCORDANCE_WAIVER_POLICY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_descriptor_concordance_local_waiver_policy"] = "allowed"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

CONCORDANCE_WAIVER_POLICY_JSON="${TMP_ROOT}/descriptor-concordance-waiver-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${CONCORDANCE_WAIVER_POLICY_REPO}" \
  --json-only >"${CONCORDANCE_WAIVER_POLICY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor concordance waiver-policy drift"
  exit 1
fi

python3 - <<'PY' "${CONCORDANCE_WAIVER_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-001", payload
assert "root_corpus_law_bundle_component_descriptor_concordance_local_waiver_policy_invalid" in payload["stale_reasons"], payload
PY

DESCRIPTOR_REPO="${TMP_ROOT}/descriptor-drift-repo"
mirror_repo "${DESCRIPTOR_REPO}"
python3 - <<'PY' "${DESCRIPTOR_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["common_script"] = "scripts/root_corpus_governance_common.py"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

DESCRIPTOR_JSON="${TMP_ROOT}/descriptor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${DESCRIPTOR_REPO}" \
  --json-only >"${DESCRIPTOR_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor concordance drift"
  exit 1
fi

python3 - <<'PY' "${DESCRIPTOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "common_script_mismatch"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_descriptor_concordance_failure"
    and row.get("descriptor_field") == "common_script"
    for row in payload["bundle_violations"]
), payload
PY

STATUS_KEY_REPO="${TMP_ROOT}/status-key-drift-repo"
mirror_repo "${STATUS_KEY_REPO}"
python3 - <<'PY' "${STATUS_KEY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["status_key"] = "protocol_root_corpus_governance_status"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STATUS_KEY_JSON="${TMP_ROOT}/status-key-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${STATUS_KEY_REPO}" \
  --json-only >"${STATUS_KEY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed status-key concordance drift"
  exit 1
fi

python3 - <<'PY' "${STATUS_KEY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "status_key_mismatch"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_descriptor_concordance_failure"
    and row.get("descriptor_field") == "status_key"
    for row in payload["bundle_violations"]
), payload
PY

COMPONENT_REPO="${TMP_ROOT}/component-drift-repo"
mirror_repo "${COMPONENT_REPO}"
python3 - <<'PY' "${COMPONENT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_rows"] = [row for row in doc["component_rows"] if row.get("component_id") != "root_constitutional_spine"]
for idx, row in enumerate(doc["component_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_JSON="${TMP_ROOT}/component-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_REPO}" \
  --json-only >"${COMPONENT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing-component drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-002", payload
assert any(
    row["reason"] == "missing_expected_components" and "root_constitutional_spine" in row.get("component_ids", [])
    for row in payload["structure_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root-law bundle discipline"
new = "## Root law bundle discipline"
assert old in text, text[:2200]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

ERROR_CODE_REPO="${TMP_ROOT}/error-code-drift-repo"
mirror_repo "${ERROR_CODE_REPO}"
python3 - <<'PY' "${ERROR_CODE_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["error_codes"] = ["IP-RCO-001", "IP-RCO-002", "IP-RCO-099"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ERROR_CODE_JSON="${TMP_ROOT}/error-code-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${ERROR_CODE_REPO}" \
  --json-only >"${ERROR_CODE_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed error-code drift"
  exit 1
fi

python3 - <<'PY' "${ERROR_CODE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering" and row["reason"] == "error_codes_mismatch"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_descriptor_concordance_failure"
    and row.get("descriptor_field") == "error_codes"
    for row in payload["bundle_violations"]
), payload
PY

echo "[PASS] protocol root-corpus law bundle probes passed"
