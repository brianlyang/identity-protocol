#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-machine-registry-completeness-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "PASS_REQUIRED", payload
assert "root-corpus-law-bundle" in payload["family_ids"], payload
assert "root-machine-registry-completeness" in payload["family_ids"], payload
assert payload["repo_rel_path_scope_policy"] == "repo_root_relative_only", payload
assert payload["repo_rel_path_escape_policy"] == "fail_closed", payload
assert payload["repo_rel_path_role_typing_policy"] == "root_protocol_surface_patterns_required", payload
assert payload["repo_rel_path_surface_stem_policy"] == "cross_role_stem_coherent", payload
assert payload["family_surface_stem_binding_policy"] == "family_id_surface_stem_congruent_or_explicit_override", payload
assert payload["family_surface_stem_overrides"] == {
    "root-corpus-registry": "root_corpus_governance",
}, payload
assert payload["required_repo_rel_path_patterns"] == {
    "validator_script": r"^scripts/validate_protocol_(?P<surface_stem>root_[a-z0-9_]+)\.py$",
    "probe_script": r"^scripts/ci/run_protocol_(?P<surface_stem>root_[a-z0-9_]+)_probes_ci\.sh$",
    "common_script": r"^scripts/(?P<surface_stem>root_[a-z0-9_]+)_common\.py$",
}, payload
assert payload["required_validator_surface_contract_fields"] == [
    "validator_root_doc_anchor_contract",
    "validator_row_projection_contract",
], payload
assert payload["required_validator_surface_contract_values"] == {
    "validator_root_doc_anchor_contract": "root_doc_anchor_status_pass_required_with_positive_anchor_check_count",
    "validator_row_projection_contract": "nonempty_row_family_projection_rows_with_pass_required_coverage_and_identity_statuses",
}, payload
assert payload["required_probe_surface_contract_fields"] == [
    "probe_shadow_bootstrap_contract",
], payload
assert payload["required_probe_surface_contract_values"] == {
    "probe_shadow_bootstrap_contract": "probe_shadow_common_contract_rows_pass_required_with_bootstrap_and_mirror_bindings",
}, payload
assert payload["family_count"] == payload["family_status_row_count"], payload
assert payload["registered_complete_family_count"] == payload["discovered_family_count"], payload
assert payload["discovered_family_count"] == payload["family_status_row_count"], payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["expected_family_status_row_count"] == payload["family_status_row_count"], payload
assert payload["family_status_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["validator_surface_contract_row_count"] == payload["family_count"] * 2, payload
assert payload["expected_family_validator_surface_contract_row_count"] == payload["family_count"] * 2, payload
assert payload["validator_surface_contract_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["validator_surface_contract_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["probe_surface_contract_row_count"] == payload["family_count"], payload
assert payload["expected_family_probe_surface_contract_row_count"] == payload["family_count"], payload
assert payload["probe_surface_contract_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["probe_surface_contract_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_family_count"] == 6, payload
assert payload["machine_registry_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_count"] == 5, payload
assert payload["machine_registry_completeness_canonical_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_canonical_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface"]["entry_count"] == 5, payload
assert payload["machine_registry_completeness_surface"]["extraction_violations"] == [], payload
assert payload["machine_registry_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["family_ids"] == payload["family_status_row_ids"] == payload["discovered_family_ids"], payload
assert payload["registered_complete_family_ids"] == payload["discovered_family_ids"], payload
assert payload["missing_family_status_row_ids"] == [], payload
assert payload["unexpected_family_status_row_ids"] == [], payload
assert payload["family_status_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["missing_validator_surface_contract_row_ids"] == [], payload
assert payload["unexpected_validator_surface_contract_row_ids"] == [], payload
assert payload["missing_probe_surface_contract_row_ids"] == [], payload
assert payload["unexpected_probe_surface_contract_row_ids"] == [], payload
assert payload["structure_violation_count"] == 0, payload
assert payload["completeness_violation_count"] == 0, payload
assert payload["anchor_violation_count"] == 0, payload
assert payload["projected_violation_reason_count"] == 0, payload
assert payload["expected_projected_violation_reason_count"] == 0, payload
assert payload["violation_projection_status"] == "PASS_REQUIRED", payload
assert all(row["family_status"] == "PASS_REQUIRED" for row in payload["family_status_rows"]), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("descriptor_field_rows", []))
    for row in payload["family_status_rows"]
), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("validator_surface_contract_rows", []))
    for row in payload["family_status_rows"]
), payload
assert all(
    len(row.get("validator_surface_contract_rows", [])) == 2
    for row in payload["family_status_rows"]
), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("probe_surface_contract_rows", []))
    for row in payload["family_status_rows"]
), payload
assert all(
    len(row.get("probe_surface_contract_rows", [])) == 1
    for row in payload["family_status_rows"]
), payload
assert all(
    all(
        cell.get("surface_stem_error", "") in ("", None)
        for cell in row.get("descriptor_field_rows", [])
        if cell.get("mode") == "repo_rel_path"
    )
    for row in payload["family_status_rows"]
), payload
assert all(row.get("expected_family_surface_stem_error", "") in ("", None) for row in payload["family_status_rows"]), payload
assert all(
    {
        cell.get("surface_stem")
        for cell in row.get("descriptor_field_rows", [])
        if cell.get("mode") == "repo_rel_path"
    } == {row.get("expected_family_surface_stem")}
    for row in payload["family_status_rows"]
), payload
assert any(
    row.get("family_id") == "root-corpus-registry"
    and row.get("expected_family_surface_stem_source") == "explicit_override"
    and row.get("expected_family_surface_stem") == "root_corpus_governance"
    for row in payload["family_status_rows"]
), payload
assert {row["family_id"] for row in payload["row_family_projection_rows"]} == {
    "registered_complete_root_mapping_families",
    "family_status_rows",
    "family_validator_surface_contract_rows",
    "family_probe_surface_contract_rows",
    "machine_registry_completeness_rows",
    "machine_registry_completeness_surface",
}, payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
contract_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_validator_surface_contract_rows"
)
probe_contract_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_probe_surface_contract_rows"
)
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "machine_registry_completeness_rows"
)
completeness_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "machine_registry_completeness_surface"
)
assert registered_row["expected_count"] == payload["registered_complete_family_count"], payload
assert registered_row["actual_count"] == payload["discovered_family_count"], payload
assert registered_row["missing_ids"] == [], payload
assert registered_row["unexpected_ids"] == [], payload
assert registered_row["coverage_status"] == "PASS_REQUIRED", payload
assert registered_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert status_row["expected_count"] == payload["discovered_family_count"], payload
assert status_row["actual_count"] == payload["family_status_row_count"], payload
assert status_row["missing_ids"] == [], payload
assert status_row["unexpected_ids"] == [], payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert contract_row["expected_count"] == payload["expected_family_validator_surface_contract_row_count"], payload
assert contract_row["actual_count"] == payload["validator_surface_contract_row_count"], payload
assert contract_row["missing_ids"] == [], payload
assert contract_row["unexpected_ids"] == [], payload
assert contract_row["coverage_status"] == "PASS_REQUIRED", payload
assert contract_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert probe_contract_row["expected_count"] == payload["expected_family_probe_surface_contract_row_count"], payload
assert probe_contract_row["actual_count"] == payload["probe_surface_contract_row_count"], payload
assert probe_contract_row["missing_ids"] == [], payload
assert probe_contract_row["unexpected_ids"] == [], payload
assert probe_contract_row["coverage_status"] == "PASS_REQUIRED", payload
assert probe_contract_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == payload["machine_registry_completeness_row_count"], payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert completeness_surface_row["expected_count"] == 5, payload
assert completeness_surface_row["actual_count"] == payload["machine_registry_completeness_surface"]["entry_count"], payload
assert completeness_surface_row["missing_ids"] == [], payload
assert completeness_surface_row["unexpected_ids"] == [], payload
assert completeness_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-machine-registry-completeness-row-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["machine_registry_completeness_rows"] = doc["machine_registry_completeness_rows"][:-1]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-machine-registry-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed missing canonical completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-002", payload
assert payload["machine_registry_completeness_row_family_count"] == 6, payload
assert payload["machine_registry_completeness_row_count"] == 4, payload
assert any(
    row["field"] == "machine_registry_completeness_rows"
    and row["reason"] == "missing_machine_registry_completeness_rows"
    and "fail_close_preserves_machine_registry_violation_projection" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "machine_registry_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_machine_registry_violation_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/machine-registry-completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = (
    "1. required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;\n"
    "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
)
new = (
    "1. required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;\n"
    "2. expected row-family totals may be summarized informally once registry output still looks green;"
)
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/machine-registry-completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed canonical completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-002", payload
assert any(
    row["field"] == "machine_registry_completeness_surface"
    and row["reason"] == "missing_machine_registry_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "machine_registry_completeness_surface"
    and row["reason"] == "extra_machine_registry_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "machine_registry_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_BINDING_REPO="${TMP_ROOT}/machine-registry-completeness-binding-drift-repo"
mirror_repo "${COMPLETENESS_BINDING_REPO}"
python3 - <<'PY' "${COMPLETENESS_BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These machine-registry-completeness rules must remain bound to canonical machine-registry-completeness rows rather than drifting into soft summary prose."
new = "These machine-registry completeness rules may be summarized freely once reviewers understand the intent."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_BINDING_JSON="${TMP_ROOT}/machine-registry-completeness-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${COMPLETENESS_BINDING_REPO}" \
  --json-only >"${COMPLETENESS_BINDING_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed canonical completeness binding drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and "These machine-registry-completeness rules must remain bound to canonical machine-registry-completeness rows rather than drifting into soft summary prose." in row.get("marker", "")
    for row in payload["anchor_violations"]
), payload
PY

SOURCE_POLICY_REPO="${TMP_ROOT}/source-policy-drift-repo"
mirror_repo "${SOURCE_POLICY_REPO}"
python3 - <<'PY' "${SOURCE_POLICY_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_validator_surface_contract_fields"] = ["validator_root_doc_anchor_contract"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SOURCE_POLICY_JSON="${TMP_ROOT}/source-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${SOURCE_POLICY_REPO}" \
  --json-only >"${SOURCE_POLICY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed source validator-surface policy drift"
  exit 1
fi

python3 - <<'PY' "${SOURCE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-001", payload
assert "root_machine_registry_completeness_required_validator_surface_contract_fields_invalid" in payload["stale_reasons"], payload
PY

VALIDATOR_VALUE_POLICY_REPO="${TMP_ROOT}/validator-value-policy-drift-repo"
mirror_repo "${VALIDATOR_VALUE_POLICY_REPO}"
python3 - <<'PY' "${VALIDATOR_VALUE_POLICY_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_validator_surface_contract_values"] = {
    "validator_root_doc_anchor_contract": "advisory_only",
    "validator_row_projection_contract": "nonempty_row_family_projection_rows_with_pass_required_coverage_and_identity_statuses",
}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

VALIDATOR_VALUE_POLICY_JSON="${TMP_ROOT}/validator-value-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${VALIDATOR_VALUE_POLICY_REPO}" \
  --json-only >"${VALIDATOR_VALUE_POLICY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed source validator-surface value policy drift"
  exit 1
fi

python3 - <<'PY' "${VALIDATOR_VALUE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-001", payload
assert "root_machine_registry_completeness_required_validator_surface_contract_values_invalid" in payload["stale_reasons"], payload
PY

PROBE_POLICY_REPO="${TMP_ROOT}/probe-policy-drift-repo"
mirror_repo "${PROBE_POLICY_REPO}"
python3 - <<'PY' "${PROBE_POLICY_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_probe_surface_contract_fields"] = []
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROBE_POLICY_JSON="${TMP_ROOT}/probe-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${PROBE_POLICY_REPO}" \
  --json-only >"${PROBE_POLICY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed source probe-surface policy drift"
  exit 1
fi

python3 - <<'PY' "${PROBE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-001", payload
assert "root_machine_registry_completeness_required_probe_surface_contract_fields_invalid" in payload["stale_reasons"], payload
PY

PROBE_VALUE_POLICY_REPO="${TMP_ROOT}/probe-value-policy-drift-repo"
mirror_repo "${PROBE_VALUE_POLICY_REPO}"
python3 - <<'PY' "${PROBE_VALUE_POLICY_REPO}/identity/protocol/mappings/root-machine-registry-completeness.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_probe_surface_contract_values"] = {
    "probe_shadow_bootstrap_contract": "advisory_only",
}
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROBE_VALUE_POLICY_JSON="${TMP_ROOT}/probe-value-policy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${PROBE_VALUE_POLICY_REPO}" \
  --json-only >"${PROBE_VALUE_POLICY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed source probe-surface value policy drift"
  exit 1
fi

python3 - <<'PY' "${PROBE_VALUE_POLICY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-001", payload
assert "root_machine_registry_completeness_required_probe_surface_contract_values_invalid" in payload["stale_reasons"], payload
PY

VALIDATOR_SURFACE_FIELD_REPO="${TMP_ROOT}/validator-surface-field-drift-repo"
mirror_repo "${VALIDATOR_SURFACE_FIELD_REPO}"
python3 - <<'PY' "${VALIDATOR_SURFACE_FIELD_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc.pop("validator_root_doc_anchor_contract", None)
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

VALIDATOR_SURFACE_FIELD_JSON="${TMP_ROOT}/validator-surface-field-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${VALIDATOR_SURFACE_FIELD_REPO}" \
  --json-only >"${VALIDATOR_SURFACE_FIELD_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed missing validator-surface contract field drift"
  exit 1
fi

python3 - <<'PY' "${VALIDATOR_SURFACE_FIELD_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "validator_surface_contract_field_missing"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("contract_field") == "validator_root_doc_anchor_contract"
    for row in payload["completeness_violations"]
), payload
assert any(
    row.get("family_id") == "root-corpus-authority"
    and any(
        cell.get("contract_field") == "validator_root_doc_anchor_contract"
        and cell.get("status") == "FAIL_REQUIRED"
        for cell in row.get("validator_surface_contract_rows", [])
    )
    for row in payload["family_status_rows"]
), payload
PY

PROBE_SURFACE_FIELD_REPO="${TMP_ROOT}/probe-surface-field-drift-repo"
mirror_repo "${PROBE_SURFACE_FIELD_REPO}"
python3 - <<'PY' "${PROBE_SURFACE_FIELD_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc.pop("probe_shadow_bootstrap_contract", None)
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROBE_SURFACE_FIELD_JSON="${TMP_ROOT}/probe-surface-field-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${PROBE_SURFACE_FIELD_REPO}" \
  --json-only >"${PROBE_SURFACE_FIELD_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed missing probe-surface contract field drift"
  exit 1
fi

python3 - <<'PY' "${PROBE_SURFACE_FIELD_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "probe_surface_contract_field_missing"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("contract_field") == "probe_shadow_bootstrap_contract"
    for row in payload["completeness_violations"]
), payload
assert any(
    row.get("family_id") == "root-corpus-authority"
    and any(
        cell.get("contract_field") == "probe_shadow_bootstrap_contract"
        and cell.get("status") == "FAIL_REQUIRED"
        for cell in row.get("probe_surface_contract_rows", [])
    )
    for row in payload["family_status_rows"]
), payload
PY

VALIDATOR_SURFACE_VALUE_REPO="${TMP_ROOT}/validator-surface-value-drift-repo"
mirror_repo "${VALIDATOR_SURFACE_VALUE_REPO}"
python3 - <<'PY' "${VALIDATOR_SURFACE_VALUE_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["validator_row_projection_contract"] = "advisory_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

VALIDATOR_SURFACE_VALUE_JSON="${TMP_ROOT}/validator-surface-value-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${VALIDATOR_SURFACE_VALUE_REPO}" \
  --json-only >"${VALIDATOR_SURFACE_VALUE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed validator-surface contract value drift"
  exit 1
fi

python3 - <<'PY' "${VALIDATOR_SURFACE_VALUE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "validator_surface_contract_value_mismatch"
    and row.get("family_id") == "root-corpus-ordering"
    and row.get("contract_field") == "validator_row_projection_contract"
    and row.get("actual_value") == "advisory_only"
    for row in payload["completeness_violations"]
), payload
PY

PROBE_SURFACE_VALUE_REPO="${TMP_ROOT}/probe-surface-value-drift-repo"
mirror_repo "${PROBE_SURFACE_VALUE_REPO}"
python3 - <<'PY' "${PROBE_SURFACE_VALUE_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["probe_shadow_bootstrap_contract"] = "advisory_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROBE_SURFACE_VALUE_JSON="${TMP_ROOT}/probe-surface-value-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${PROBE_SURFACE_VALUE_REPO}" \
  --json-only >"${PROBE_SURFACE_VALUE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed probe-surface contract value drift"
  exit 1
fi

python3 - <<'PY' "${PROBE_SURFACE_VALUE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "probe_surface_contract_value_mismatch"
    and row.get("family_id") == "root-corpus-ordering"
    and row.get("contract_field") == "probe_shadow_bootstrap_contract"
    and row.get("actual_value") == "advisory_only"
    for row in payload["completeness_violations"]
), payload
PY

ABSOLUTE_PATH_REPO="${TMP_ROOT}/absolute-path-drift-repo"
mirror_repo "${ABSOLUTE_PATH_REPO}"
python3 - <<'PY' "${ABSOLUTE_PATH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["common_script"] = "/bin/sh"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ABSOLUTE_PATH_JSON="${TMP_ROOT}/absolute-path-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ABSOLUTE_PATH_REPO}" \
  --json-only >"${ABSOLUTE_PATH_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed absolute descriptor path drift"
  exit 1
fi

python3 - <<'PY' "${ABSOLUTE_PATH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_path_not_repo_relative"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "common_script"
    for row in payload["completeness_violations"]
), payload
PY

ESCAPE_PATH_REPO="${TMP_ROOT}/escape-path-drift-repo"
mirror_repo "${ESCAPE_PATH_REPO}"
python3 - <<'PY' "${ESCAPE_PATH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["common_script"] = "../scripts/root_corpus_authority_common.py"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ESCAPE_PATH_JSON="${TMP_ROOT}/escape-path-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ESCAPE_PATH_REPO}" \
  --json-only >"${ESCAPE_PATH_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed repo-escape descriptor path drift"
  exit 1
fi

python3 - <<'PY' "${ESCAPE_PATH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_path_escapes_repo_root"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "common_script"
    for row in payload["completeness_violations"]
), payload
PY

ROLE_TYPE_REPO="${TMP_ROOT}/role-type-drift-repo"
mirror_repo "${ROLE_TYPE_REPO}"
python3 - <<'PY' "${ROLE_TYPE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["common_script"] = "scripts/validate_protocol_root_corpus_authority.py"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROLE_TYPE_JSON="${TMP_ROOT}/role-type-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ROLE_TYPE_REPO}" \
  --json-only >"${ROLE_TYPE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed role-swapped descriptor path drift"
  exit 1
fi

python3 - <<'PY' "${ROLE_TYPE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_path_role_pattern_mismatch"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "common_script"
    for row in payload["completeness_violations"]
), payload
PY

STEM_MISMATCH_REPO="${TMP_ROOT}/surface-stem-mismatch-repo"
mirror_repo "${STEM_MISMATCH_REPO}"
python3 - <<'PY' "${STEM_MISMATCH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["common_script"] = "scripts/root_corpus_ordering_common.py"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STEM_MISMATCH_JSON="${TMP_ROOT}/surface-stem-mismatch.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${STEM_MISMATCH_REPO}" \
  --json-only >"${STEM_MISMATCH_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed cross-role surface-stem mismatch"
  exit 1
fi

python3 - <<'PY' "${STEM_MISMATCH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_surface_stem_mismatch"
    and row.get("family_id") == "root-corpus-authority"
    for row in payload["completeness_violations"]
), payload
PY

FAMILY_MISMATCH_REPO="${TMP_ROOT}/family-surface-mismatch-repo"
mirror_repo "${FAMILY_MISMATCH_REPO}"
python3 - <<'PY' "${FAMILY_MISMATCH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["validator_script"] = "scripts/validate_protocol_root_corpus_ordering.py"
doc["probe_script"] = "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh"
doc["common_script"] = "scripts/root_corpus_ordering_common.py"
doc["status_key"] = "protocol_root_corpus_ordering_status"
doc["error_codes"] = ["IP-RCO-001", "IP-RCO-002", "IP-RCO-003"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FAMILY_MISMATCH_JSON="${TMP_ROOT}/family-surface-mismatch.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${FAMILY_MISMATCH_REPO}" \
  --json-only >"${FAMILY_MISMATCH_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed family-incongruent descriptor set"
  exit 1
fi

python3 - <<'PY' "${FAMILY_MISMATCH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_surface_family_mismatch"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("expected_family_surface_stem") == "root_corpus_authority"
    and row.get("actual_family_surface_stem") == "root_corpus_ordering"
    for row in payload["completeness_violations"]
), payload
PY

DESCRIPTOR_REPO="${TMP_ROOT}/descriptor-drift-repo"
mirror_repo "${DESCRIPTOR_REPO}"
python3 - <<'PY' "${DESCRIPTOR_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc.pop("common_script", None)
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

DESCRIPTOR_JSON="${TMP_ROOT}/descriptor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${DESCRIPTOR_REPO}" \
  --json-only >"${DESCRIPTOR_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed missing descriptor field drift"
  exit 1
fi

python3 - <<'PY' "${DESCRIPTOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_field_missing"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "common_script"
    for row in payload["completeness_violations"]
), payload
PY

DESCRIPTOR_PATH_REPO="${TMP_ROOT}/descriptor-path-drift-repo"
mirror_repo "${DESCRIPTOR_PATH_REPO}"
python3 - <<'PY' "${DESCRIPTOR_PATH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["common_script"] = "scripts/nonexistent_root_corpus_common.py"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

DESCRIPTOR_PATH_JSON="${TMP_ROOT}/descriptor-path-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${DESCRIPTOR_PATH_REPO}" \
  --json-only >"${DESCRIPTOR_PATH_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed broken descriptor path drift"
  exit 1
fi

python3 - <<'PY' "${DESCRIPTOR_PATH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_path_missing"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "common_script"
    for row in payload["completeness_violations"]
), payload
PY

STATUS_KEY_REPO="${TMP_ROOT}/status-key-drift-repo"
mirror_repo "${STATUS_KEY_REPO}"
python3 - <<'PY' "${STATUS_KEY_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["status_key"] = "protocol_root_corpus_ordering_status"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STATUS_KEY_JSON="${TMP_ROOT}/status-key-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${STATUS_KEY_REPO}" \
  --json-only >"${STATUS_KEY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed status-key descriptor drift"
  exit 1
fi

python3 - <<'PY' "${STATUS_KEY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_value_mismatch"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "status_key"
    for row in payload["completeness_violations"]
), payload
PY

ERROR_CODE_REPO="${TMP_ROOT}/error-code-drift-repo"
mirror_repo "${ERROR_CODE_REPO}"
python3 - <<'PY' "${ERROR_CODE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["error_codes"] = ["IP-RCA-999", *list(doc.get("error_codes", [])[1:])]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ERROR_CODE_JSON="${TMP_ROOT}/error-code-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ERROR_CODE_REPO}" \
  --json-only >"${ERROR_CODE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed error-code descriptor drift"
  exit 1
fi

python3 - <<'PY' "${ERROR_CODE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "descriptor_value_mismatch"
    and row.get("family_id") == "root-corpus-authority"
    and row.get("descriptor_field") == "error_codes"
    for row in payload["completeness_violations"]
), payload
PY

REGISTRY_REPO="${TMP_ROOT}/registry-drift-repo"
mirror_repo "${REGISTRY_REPO}"
python3 - <<'PY' "${REGISTRY_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["registered_top_level_entries"]:
    if row.get("rel_path") == "identity/protocol/mappings":
        row["required_children"] = [
            child for child in row.get("required_children", [])
            if child != "root-corpus-law-bundle.v1.yaml"
        ]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed missing registration drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "version_file_not_registered" and row.get("family_id") == "root-corpus-law-bundle"
    for row in payload["completeness_violations"]
), payload
assert payload["machine_registry_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
assert registered_row["expected_count"] + 1 == registered_row["actual_count"], payload
assert registered_row["missing_ids"] == [], payload
assert registered_row["unexpected_ids"] == ["root-corpus-law-bundle"], payload
assert registered_row["coverage_status"] == "FAIL_REQUIRED", payload
assert registered_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

STRAY_REPO="${TMP_ROOT}/stray-family-repo"
mirror_repo "${STRAY_REPO}"
cp "${STRAY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml" \
  "${STRAY_REPO}/identity/protocol/mappings/root-shadow-lane.v1.yaml"
cat > "${STRAY_REPO}/identity/protocol/mappings/root-shadow-lane.current.yaml" <<'EOF'
active_file: identity/protocol/mappings/root-shadow-lane.v1.yaml
EOF

STRAY_JSON="${TMP_ROOT}/stray-family.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${STRAY_REPO}" \
  --json-only >"${STRAY_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed stray unregistered family"
  exit 1
fi

python3 - <<'PY' "${STRAY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "current_file_not_registered" and row.get("family_id") == "root-shadow-lane"
    for row in payload["completeness_violations"]
), payload
assert payload["machine_registry_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
assert registered_row["expected_count"] + 1 == registered_row["actual_count"], payload
assert registered_row["missing_ids"] == [], payload
assert "root-shadow-lane" in registered_row["unexpected_ids"], payload
assert registered_row["coverage_status"] == "FAIL_REQUIRED", payload
assert registered_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root machine-registry completeness discipline"
new = "## Root machine registry completeness discipline"
assert old in text, text[:3200]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

ALIAS_REPO="${TMP_ROOT}/alias-drift-repo"
mirror_repo "${ALIAS_REPO}"
cat > "${ALIAS_REPO}/identity/protocol/mappings/root-corpus-law-bundle.current.yaml" <<'EOF'
active_file: identity/protocol/mappings/root-corpus-law-bundle.v9.yaml
EOF

ALIAS_JSON="${TMP_ROOT}/alias-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${ALIAS_REPO}" \
  --json-only >"${ALIAS_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed alias drift"
  exit 1
fi

python3 - <<'PY' "${ALIAS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "current_alias_error" and row.get("family_id") == "root-corpus-law-bundle"
    for row in payload["completeness_violations"]
), payload
PY

FAMILY_IDENTITY_DRIFT_REPO="${TMP_ROOT}/family-identity-drift-repo"
mirror_repo "${FAMILY_IDENTITY_DRIFT_REPO}"
cp "${FAMILY_IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml" \
  "${FAMILY_IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-shadow-lane.v1.yaml"
cat > "${FAMILY_IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-shadow-lane.current.yaml" <<'EOF'
active_file: identity/protocol/mappings/root-shadow-lane.v1.yaml
EOF
rm \
  "${FAMILY_IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.current.yaml" \
  "${FAMILY_IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"

FAMILY_IDENTITY_DRIFT_JSON="${TMP_ROOT}/family-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${FAMILY_IDENTITY_DRIFT_REPO}" \
  --json-only >"${FAMILY_IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed family identity drift"
  exit 1
fi

python3 - <<'PY' "${FAMILY_IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert any(
    row["reason"] == "registered_child_missing_on_disk"
    and row.get("child") == "root-corpus-law-bundle.current.yaml"
    for row in payload["completeness_violations"]
), payload
assert any(
    row["reason"] == "registered_child_missing_on_disk"
    and row.get("child") == "root-corpus-law-bundle.v1.yaml"
    for row in payload["completeness_violations"]
), payload
assert any(
    row["reason"] == "current_file_not_registered"
    and row.get("family_id") == "root-shadow-lane"
    for row in payload["completeness_violations"]
), payload
assert payload["validator_surface_contract_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["validator_surface_contract_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["probe_surface_contract_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["probe_surface_contract_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
contract_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_validator_surface_contract_rows"
)
probe_contract_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_probe_surface_contract_rows"
)
assert registered_row["expected_count"] == registered_row["actual_count"], payload
assert registered_row["missing_ids"] == ["root-corpus-law-bundle"], payload
assert registered_row["unexpected_ids"] == ["root-shadow-lane"], payload
assert registered_row["coverage_status"] == "PASS_REQUIRED", payload
assert registered_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert contract_row["expected_count"] == payload["expected_family_validator_surface_contract_row_count"], payload
assert contract_row["actual_count"] == payload["validator_surface_contract_row_count"], payload
assert contract_row["missing_ids"] == [
    "root-shadow-lane:validator_root_doc_anchor_contract",
    "root-shadow-lane:validator_row_projection_contract",
], payload
assert contract_row["unexpected_ids"] == [], payload
assert contract_row["coverage_status"] == "FAIL_REQUIRED", payload
assert contract_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert probe_contract_row["expected_count"] == payload["expected_family_probe_surface_contract_row_count"], payload
assert probe_contract_row["actual_count"] == payload["probe_surface_contract_row_count"], payload
assert probe_contract_row["missing_ids"] == [
    "root-shadow-lane:probe_shadow_bootstrap_contract",
], payload
assert probe_contract_row["unexpected_ids"] == [], payload
assert probe_contract_row["coverage_status"] == "FAIL_REQUIRED", payload
assert probe_contract_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

FAMILY_ROW_COVERAGE_REPO="${TMP_ROOT}/family-row-coverage-repo"
mirror_repo "${FAMILY_ROW_COVERAGE_REPO}"
python3 - <<'PY' "${FAMILY_ROW_COVERAGE_REPO}/scripts/validate_protocol_root_machine_registry_completeness.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
needle = "                family_status_rows.append(\n"
replacement = (
    "                if family_id == \"root-corpus-authority\":\n"
    "                    continue\n"
    "                family_status_rows.append(\n"
)
if needle not in text:
    raise SystemExit("expected family-status row append block not found")
path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
PY

FAMILY_ROW_COVERAGE_JSON="${TMP_ROOT}/family-row-coverage.json"
if python3 "${FAMILY_ROW_COVERAGE_REPO}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${FAMILY_ROW_COVERAGE_REPO}" \
  --json-only >"${FAMILY_ROW_COVERAGE_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed family-row coverage gap"
  exit 1
fi

python3 - <<'PY' "${FAMILY_ROW_COVERAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert payload["family_status_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["family_status_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["family_status_row_count"] + 1 == payload["expected_family_status_row_count"], payload
assert payload["discovered_family_count"] == payload["expected_family_status_row_count"], payload
assert "root-corpus-authority" in payload["discovered_family_ids"], payload
assert "root-corpus-authority" in payload["missing_family_status_row_ids"], payload
assert "root-corpus-authority" not in payload["family_status_row_ids"], payload
assert payload["unexpected_family_status_row_ids"] == [], payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
assert registered_row["coverage_status"] == "PASS_REQUIRED", payload
assert registered_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert status_row["coverage_status"] == "FAIL_REQUIRED", payload
assert status_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert "root-corpus-authority" in status_row["missing_ids"], payload
assert status_row["unexpected_ids"] == [], payload
assert any(
    row["reason"] == "family_status_row_coverage_incomplete"
    and row.get("expected_count") == payload["expected_family_status_row_count"]
    and row.get("actual_count") == payload["family_status_row_count"]
    for row in payload["completeness_violations"]
), payload
assert any(
    row["reason"] == "family_status_row_identity_projection_incomplete"
    and "root-corpus-authority" in row.get("missing_family_ids", [])
    and row.get("unexpected_family_ids") == []
    for row in payload["completeness_violations"]
), payload
PY

VIOLATION_PROJECTION_REPO="${TMP_ROOT}/violation-projection-repo"
mirror_repo "${VIOLATION_PROJECTION_REPO}"
python3 - <<'PY' "${VIOLATION_PROJECTION_REPO}/scripts/validate_protocol_root_machine_registry_completeness.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
needle = (
    "    expected_projected_violation_reason_count = (\n"
    "        len(structure_violations) + len(completeness_violations) + len(anchor_violations)\n"
    "    )\n"
)
replacement = (
    "    expected_projected_violation_reason_count = (\n"
    "        len(structure_violations) + len(completeness_violations) + len(anchor_violations)\n"
    "    ) + 1\n"
)
if needle not in text:
    raise SystemExit("expected projected violation count block not found")
path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
PY

VIOLATION_PROJECTION_JSON="${TMP_ROOT}/violation-projection.json"
if python3 "${VIOLATION_PROJECTION_REPO}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${VIOLATION_PROJECTION_REPO}" \
  --json-only >"${VIOLATION_PROJECTION_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed violation projection completeness gap"
  exit 1
fi

python3 - <<'PY' "${VIOLATION_PROJECTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert payload["violation_projection_status"] == "FAIL_REQUIRED", payload
assert payload["projected_violation_reason_count"] + 1 == payload["expected_projected_violation_reason_count"], payload
assert "root_machine_registry_completeness_violation_projection_incomplete" in payload["stale_reasons"], payload
PY

SURFACE_ORDER_REPO="${TMP_ROOT}/machine-registry-completeness-surface-order-drift-repo"
mirror_repo "${SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root machine-registry completeness discipline" \
  "## Root governance completeness discipline" \
  "1. required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

SURFACE_ORDER_JSON="${TMP_ROOT}/machine-registry-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_registry_completeness.py" \
  --repo-root "${SURFACE_ORDER_REPO}" \
  --json-only >"${SURFACE_ORDER_JSON}"; then
  echo "[FAIL] machine-registry completeness validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_registry_completeness_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMRC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["machine_registry_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "machine_registry_completeness_surface"
    and row["reason"] == "machine_registry_completeness_surface_phrase_order_mismatch"
    for row in payload["completeness_violations"]
), payload
assert any(
    row["field"] == "machine_registry_completeness_surface"
    and row["reason"] == "machine_registry_completeness_surface_order_mismatch"
    for row in payload["completeness_violations"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "1. required registered-complete-root-mapping-family, family-status-row, family-validator-surface-contract-row, and family-probe-surface-contract-row rows must remain explicit as separate machine-readable row families;"
    for row in payload["anchor_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "machine_registry_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

echo "[PASS] protocol root machine-registry completeness probes passed"
