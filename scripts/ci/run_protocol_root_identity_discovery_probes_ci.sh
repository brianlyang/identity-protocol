#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-identity-discovery-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "PASS_REQUIRED", payload
assert payload["section_count"] == 6, payload
assert payload["request_field_count"] == 5, payload
assert payload["response_field_count"] == 7, payload
assert payload["precedence_count"] == 3, payload
assert payload["activation_count"] == 3, payload
assert payload["error_field_count"] == 4, payload
assert payload["implementation_count"] == 4, payload
assert payload["discovery_proof_count"] == 6, payload
assert payload["discovery_limit_count"] == 6, payload
assert payload["collapse_count"] == 5, payload
assert payload["identity_discovery_row_family_count"] == 10, payload
assert payload["identity_discovery_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-identity-discovery.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_discovery_proof_rows"] = [
    row for row in doc["required_discovery_proof_rows"]
    if row.get("proof_id") != "implementation_compliance_proof"
]
for idx, row in enumerate(doc["required_discovery_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed missing discovery proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert payload["identity_discovery_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "implementation_compliance_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_discovery_proof_rows"
)
assert proof_row["expected_count"] == 6, payload
assert proof_row["actual_count"] == 5, payload
assert proof_row["missing_ids"] == ["implementation_compliance_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

REQUEST_REPO="${TMP_ROOT}/request-drift-repo"
mirror_repo "${REQUEST_REPO}"
python3 - <<'PY' "${REQUEST_REPO}/identity/protocol/mappings/root-identity-discovery.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_request_field_rows"]:
    if row.get("request_field_id") == "forceReload":
        row["request_field_id"] = "forceReloadAlias"
        break
else:
    raise SystemExit("expected forceReload request field row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REQUEST_JSON="${TMP_ROOT}/request-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${REQUEST_REPO}" \
  --json-only >"${REQUEST_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed missing request row"
  exit 1
fi

python3 - <<'PY' "${REQUEST_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "forceReload" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "forceReloadAlias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["identity_discovery_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "FAIL_REQUIRED", payload
request_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_request_field_rows"
)
assert request_row["expected_count"] == 5, payload
assert request_row["actual_count"] == 5, payload
assert request_row["missing_ids"] == ["forceReload"], payload
assert request_row["unexpected_ids"] == ["forceReloadAlias"], payload
assert request_row["coverage_status"] == "PASS_REQUIRED", payload
assert request_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_DISCOVERY.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Activation policy contract"
new = "## Activation policy"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["reason"] == "section_heading_missing" and row["marker"] == "## Activation policy contract"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_DISCOVERY.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "contract_not_registered"
    for row in payload["integration_violations"]
), payload
PY

ROUTING_REPO="${TMP_ROOT}/routing-drift-repo"
mirror_repo "${ROUTING_REPO}"
python3 - <<'PY' "${ROUTING_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["entry_question_projection"]:
    if row.get("rel_path") == "identity/protocol/IDENTITY_DISCOVERY.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root identity-discovery probes passed"
