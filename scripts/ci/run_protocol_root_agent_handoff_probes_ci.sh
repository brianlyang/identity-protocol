#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-agent-handoff-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "PASS_REQUIRED", payload
assert payload["role_count"] == 2, payload
assert payload["payload_field_count"] == 10, payload
assert payload["anchor_count"] == 5, payload
assert payload["handoff_proof_count"] == 5, payload
assert payload["handoff_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["agent_handoff_row_family_count"] == 6, payload
assert payload["agent_handoff_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["role_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["payload_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["anchor_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["handoff_proof_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["handoff_limit_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["collapse_row_coverage_status"] == "PASS_REQUIRED", payload
assert [row["family_id"] for row in payload["row_family_projection_rows"]] == [
    "role_rows",
    "payload_rows",
    "anchor_rows",
    "handoff_proof_rows",
    "handoff_limit_rows",
    "collapse_rows",
], payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_handoff_proof_rows"] = [
    row for row in doc["required_handoff_proof_rows"] if row.get("proof_id") != "validation_track_separation_proof"
]
for idx, row in enumerate(doc["required_handoff_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed missing handoff proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert payload["agent_handoff_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["handoff_proof_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["handoff_proof_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "validation_track_separation_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["family_id"] == "handoff_proof_rows"
    and "validation_track_separation_proof" in row["missing_ids"]
    for row in payload["row_family_projection_rows"]
), payload
PY

ROLE_REPO="${TMP_ROOT}/role-drift-repo"
mirror_repo "${ROLE_REPO}"
python3 - <<'PY' "${ROLE_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_role_rows"] = [row for row in doc["required_role_rows"] if row.get("role_id") != "delegated_sub_agent_execution"]
for idx, row in enumerate(doc["required_role_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROLE_JSON="${TMP_ROOT}/role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROLE_REPO}" \
  --json-only >"${ROLE_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed missing role row"
  exit 1
fi

python3 - <<'PY' "${ROLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert payload["agent_handoff_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["role_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["role_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "delegated_sub_agent_execution" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["family_id"] == "role_rows"
    and "delegated_sub_agent_execution" in row["missing_ids"]
    for row in payload["row_family_projection_rows"]
), payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/AGENT_HANDOFF_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 2. Delegated sub-agent execution role"
new = "### 2. Delegated execution role"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert any(
    row["reason"] == "role_heading_missing" and row["marker"] == "### 2. Delegated sub-agent execution role"
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
    if row.get("rel_path") != "identity/protocol/AGENT_HANDOFF_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
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
    if row.get("rel_path") == "identity/protocol/AGENT_HANDOFF_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root agent-handoff probes passed"
