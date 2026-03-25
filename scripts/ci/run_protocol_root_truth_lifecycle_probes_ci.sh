#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-truth-lifecycle-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "PASS_REQUIRED", payload
assert payload["lifecycle_count"] == 5, payload
assert payload["memory_strata_count"] == 5, payload
assert payload["differentiation_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
PY

MEMORY_REPO="${TMP_ROOT}/memory-drift-repo"
mirror_repo "${MEMORY_REPO}"
python3 - <<'PY' "${MEMORY_REPO}/identity/protocol/mappings/root-truth-lifecycle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_memory_strata_rows"] = [
    row for row in doc["required_memory_strata_rows"] if row.get("memory_id") != "consumption_memory"
]
for idx, row in enumerate(doc["required_memory_strata_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MEMORY_JSON="${TMP_ROOT}/memory-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${MEMORY_REPO}" \
  --json-only >"${MEMORY_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed missing memory stratum row"
  exit 1
fi

python3 - <<'PY' "${MEMORY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "consumption_memory" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

LIFECYCLE_REPO="${TMP_ROOT}/lifecycle-drift-repo"
mirror_repo "${LIFECYCLE_REPO}"
python3 - <<'PY' "${LIFECYCLE_REPO}/identity/protocol/mappings/root-truth-lifecycle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_lifecycle_rows"] = [
    row for row in doc["required_lifecycle_rows"] if row.get("lifecycle_id") != "truth_consumed"
]
for idx, row in enumerate(doc["required_lifecycle_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

LIFECYCLE_JSON="${TMP_ROOT}/lifecycle-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${LIFECYCLE_REPO}" \
  --json-only >"${LIFECYCLE_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed missing lifecycle row"
  exit 1
fi

python3 - <<'PY' "${LIFECYCLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "truth_consumed" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 4. Truth is bound to current run / current thread"
new = "### 4. Truth is bound to current run"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert any(
    row["reason"] == "lifecycle_heading_missing" and row["marker"] == "### 4. Truth is bound to current run / current thread"
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
    if row.get("rel_path") != "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
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
    if row.get("rel_path") == "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root truth-lifecycle probes passed"
