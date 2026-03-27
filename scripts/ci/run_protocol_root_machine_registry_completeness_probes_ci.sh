#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-machine-registry-completeness-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

mirror_repo() {
  local dst="$1"
  probe_mirror_repo "${ROOT}" "${dst}"
}

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
assert payload["family_count"] == payload["family_status_row_count"], payload
assert payload["registered_complete_family_count"] == payload["discovered_family_count"], payload
assert payload["discovered_family_count"] == payload["family_status_row_count"], payload
assert payload["expected_family_status_row_count"] == payload["family_status_row_count"], payload
assert payload["family_status_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_family_count"] == 2, payload
assert payload["machine_registry_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["family_ids"] == payload["family_status_row_ids"] == payload["discovered_family_ids"], payload
assert payload["registered_complete_family_ids"] == payload["discovered_family_ids"], payload
assert payload["missing_family_status_row_ids"] == [], payload
assert payload["unexpected_family_status_row_ids"] == [], payload
assert payload["family_status_row_identity_projection_status"] == "PASS_REQUIRED", payload
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
assert payload["error_code"] == "IP-RMRC-003", payload
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
assert payload["machine_registry_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_registry_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
registered_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_complete_root_mapping_families"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "family_status_rows"
)
assert registered_row["expected_count"] == registered_row["actual_count"], payload
assert registered_row["missing_ids"] == ["root-corpus-law-bundle"], payload
assert registered_row["unexpected_ids"] == ["root-shadow-lane"], payload
assert registered_row["coverage_status"] == "PASS_REQUIRED", payload
assert registered_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
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

echo "[PASS] protocol root machine-registry completeness probes passed"
