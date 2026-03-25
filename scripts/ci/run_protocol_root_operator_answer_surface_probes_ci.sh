#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-operator-answer-surface-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "PASS_REQUIRED", payload
assert payload["surface_count"] == 4, payload
assert payload["support_memory_count"] == 5, payload
assert payload["support_limit_count"] == 5, payload
assert payload["boundary_count"] == 4, payload
assert payload["collapse_count"] == 5, payload
PY

SUPPORT_REPO="${TMP_ROOT}/support-drift-repo"
mirror_repo "${SUPPORT_REPO}"
python3 - <<'PY' "${SUPPORT_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_support_memory_rows"] = [
    row for row in doc["required_support_memory_rows"] if row.get("support_id") != "consumption_memory_support"
]
for idx, row in enumerate(doc["required_support_memory_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUPPORT_JSON="${TMP_ROOT}/support-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${SUPPORT_REPO}" \
  --json-only >"${SUPPORT_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed missing support-memory row"
  exit 1
fi

python3 - <<'PY' "${SUPPORT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "consumption_memory_support" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

SURFACE_REPO="${TMP_ROOT}/surface-drift-repo"
mirror_repo "${SURFACE_REPO}"
python3 - <<'PY' "${SURFACE_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_surface_rows"] = [
    row for row in doc["required_surface_rows"] if row.get("surface_id") != "terminal_machine_enforcement"
]
for idx, row in enumerate(doc["required_surface_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SURFACE_JSON="${TMP_ROOT}/surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${SURFACE_REPO}" \
  --json-only >"${SURFACE_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed missing surface row"
  exit 1
fi

python3 - <<'PY' "${SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "terminal_machine_enforcement" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 2. Stable instance answer surface"
new = "### 2. Stable instance output surface"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
assert any(
    row["reason"] == "surface_heading_missing" and row["marker"] == "### 2. Stable instance answer surface"
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
    if row.get("rel_path") != "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
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
    if row.get("rel_path") == "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root operator answer-surface probes passed"
