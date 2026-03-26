#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-governed-subdomain-doc-control-registry-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/governed_subdomain_doc_control_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_broadcast_doc_control.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_governed_subdomain_doc_control_registry.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_governed_subdomain_doc_control_registry_probes_ci.sh" "${dst}/scripts/ci/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_governed_subdomain_doc_control_registry.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_governed_subdomain_doc_control_registry_status"] == "PASS_REQUIRED", payload
assert payload["subdomain_count"] >= 1, payload
PY

MISSING_VALIDATOR_REPO="${TMP_ROOT}/missing-validator-repo"
mirror_repo "${MISSING_VALIDATOR_REPO}"
python3 - <<'PY' "${MISSING_VALIDATOR_REPO}/identity/protocol/mappings/governed-subdomain-doc-control.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["subdomains"][0]["validator_script"] = "scripts/validate_protocol_missing_doc_control.py"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_VALIDATOR_JSON="${TMP_ROOT}/missing-validator.json"
if python3 "${ROOT}/scripts/validate_protocol_governed_subdomain_doc_control_registry.py" \
  --repo-root "${MISSING_VALIDATOR_REPO}" \
  --json-only >"${MISSING_VALIDATOR_JSON}"; then
  echo "[FAIL] governed-subdomain registry validator unexpectedly passed missing validator path drift"
  exit 1
fi

python3 - <<'PY' "${MISSING_VALIDATOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_governed_subdomain_doc_control_registry_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-GSD-003", payload
assert any(
    row["field"] == "validator_script" and row["reason"] == "path_missing"
    for row in payload["binding_violations"]
), payload
PY

SUBDOMAIN_DRIFT_REPO="${TMP_ROOT}/subdomain-drift-repo"
mirror_repo "${SUBDOMAIN_DRIFT_REPO}"
python3 - <<'PY' "${SUBDOMAIN_DRIFT_REPO}/identity/protocol/broadcast/BROADCAST_DOC_CONTROL.v1.6.20.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["subdomain_id"] = "broadcast_drift"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUBDOMAIN_DRIFT_JSON="${TMP_ROOT}/subdomain-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_governed_subdomain_doc_control_registry.py" \
  --repo-root "${SUBDOMAIN_DRIFT_REPO}" \
  --json-only >"${SUBDOMAIN_DRIFT_JSON}"; then
  echo "[FAIL] governed-subdomain registry validator unexpectedly passed subdomain mismatch drift"
  exit 1
fi

python3 - <<'PY' "${SUBDOMAIN_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_governed_subdomain_doc_control_registry_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-GSD-003", payload
assert any(
    row["reason"] == "doc_control_subdomain_id_mismatch"
    for row in payload["binding_violations"]
), payload
PY

echo "[PASS] protocol governed-subdomain doc-control registry probes passed"
