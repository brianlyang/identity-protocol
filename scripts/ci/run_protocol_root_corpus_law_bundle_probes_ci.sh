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
assert payload["descriptor_schema_local_reconstruction_policy"] == "forbidden", payload
assert payload["component_descriptor_resolution_mode"] == "current_alias_only", payload
assert payload["component_descriptor_version_pinning_policy"] == "forbidden", payload
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
assert all(row["component_status"] == "PASS_REQUIRED" for row in payload["component_status_rows"]), payload
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
