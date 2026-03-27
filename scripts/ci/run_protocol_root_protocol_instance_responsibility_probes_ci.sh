#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-protocol-instance-responsibility-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "PASS_REQUIRED", payload
assert payload["layer_count"] == 4, payload
assert payload["responsibility_count"] == 3, payload
assert payload["escalation_trigger_count"] == 4, payload
assert payload["escalation_proof_count"] == 4, payload
assert payload["escalation_limit_count"] == 5, payload
assert payload["boundary_collapse_count"] == 5, payload
assert payload["protocol_instance_row_family_count"] == 6, payload
assert payload["protocol_instance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["protocol_instance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-protocol-instance-responsibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_escalation_proof_rows"] = [
    row for row in doc["required_escalation_proof_rows"] if row.get("proof_id") != "machine_truth_incompleteness_proof"
]
for idx, row in enumerate(doc["required_escalation_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed missing escalation proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-002", payload
assert payload["protocol_instance_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["protocol_instance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "machine_truth_incompleteness_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_escalation_proof_rows"
)
assert proof_row["expected_count"] == 4, payload
assert proof_row["actual_count"] == 3, payload
assert proof_row["missing_ids"] == ["machine_truth_incompleteness_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

RESP_REPO="${TMP_ROOT}/responsibility-drift-repo"
mirror_repo "${RESP_REPO}"
python3 - <<'PY' "${RESP_REPO}/identity/protocol/mappings/root-protocol-instance-responsibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_responsibility_rows"] = [
    row for row in doc["required_responsibility_rows"] if row.get("owner_id") != "operator_surface"
]
for idx, row in enumerate(doc["required_responsibility_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

RESP_JSON="${TMP_ROOT}/responsibility-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${RESP_REPO}" \
  --json-only >"${RESP_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed missing responsibility row"
  exit 1
fi

python3 - <<'PY' "${RESP_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-002", payload
assert payload["protocol_instance_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["protocol_instance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "operator_surface" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
responsibility_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_responsibility_rows"
)
assert responsibility_row["expected_count"] == 3, payload
assert responsibility_row["actual_count"] == 2, payload
assert responsibility_row["missing_ids"] == ["operator_surface"], payload
assert responsibility_row["unexpected_ids"] == [], payload
assert responsibility_row["coverage_status"] == "FAIL_REQUIRED", payload
assert responsibility_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-protocol-instance-responsibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_responsibility_rows"]:
    if row.get("owner_id") == "operator_surface":
        row["owner_id"] = "operator_surface_alias"
        break
else:
    raise SystemExit("expected operator_surface row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed responsibility identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-002", payload
assert payload["protocol_instance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["protocol_instance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "operator_surface" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "operator_surface_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
responsibility_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_responsibility_rows"
)
assert responsibility_row["expected_count"] == 3, payload
assert responsibility_row["actual_count"] == 3, payload
assert responsibility_row["missing_ids"] == ["operator_surface"], payload
assert responsibility_row["unexpected_ids"] == ["operator_surface_alias"], payload
assert responsibility_row["coverage_status"] == "PASS_REQUIRED", payload
assert responsibility_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 2. Instance-layer obligations"
new = "### 2. Instance obligations"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-003", payload
assert any(
    row["reason"] == "responsibility_heading_missing" and row["marker"] == "### 2. Instance-layer obligations"
    for row in payload["contract_marker_violations"]
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
doc["registered_top_level_entries"] = [
    row for row in doc["registered_top_level_entries"]
    if row.get("rel_path") != "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-003", payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "contract_not_registered"
    for row in payload["integration_violations"]
), payload
PY

AUTH_REPO="${TMP_ROOT}/authority-drift-repo"
mirror_repo "${AUTH_REPO}"
python3 - <<'PY' "${AUTH_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_authority_projection"] = [
    row for row in doc["entry_authority_projection"]
    if row.get("rel_path") != "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

AUTH_JSON="${TMP_ROOT}/authority-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_protocol_instance_responsibility.py" \
  --repo-root "${AUTH_REPO}" \
  --json-only >"${AUTH_JSON}"; then
  echo "[FAIL] root protocol-instance responsibility validator unexpectedly passed authority drift"
  exit 1
fi

python3 - <<'PY' "${AUTH_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_protocol_instance_responsibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPIR-003", payload
assert any(
    row["field"] == "root_corpus_authority" and row["reason"] == "authority_projection_missing"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root protocol-instance responsibility probes passed"
