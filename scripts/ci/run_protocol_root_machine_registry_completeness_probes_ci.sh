#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-machine-registry-completeness-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
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
assert all(row["family_status"] == "PASS_REQUIRED" for row in payload["family_status_rows"]), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("descriptor_field_rows", []))
    for row in payload["family_status_rows"]
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

echo "[PASS] protocol root machine-registry completeness probes passed"
