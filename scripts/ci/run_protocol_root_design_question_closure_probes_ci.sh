#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-design-question-closure-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

mirror_repo() {
  local dst="$1"
  probe_mirror_repo "${ROOT}" "${dst}"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "PASS_REQUIRED", payload
assert payload["question_closure_count"] == 5, payload
assert payload["question_ids"] == [
    "ontology",
    "truth_lifecycle",
    "normative",
    "responsibility_split",
    "answer_surface",
], payload
assert payload["design_question_closure_row_family_count"] == 2, payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

ROW_REPO="${TMP_ROOT}/missing-row-repo"
mirror_repo "${ROW_REPO}"
python3 - <<'PY' "${ROW_REPO}/identity/protocol/mappings/root-design-question-closure.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_question_closure_rows"] = [
    row for row in doc["required_question_closure_rows"]
    if row.get("question_id") != "answer_surface"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROW_JSON="${TMP_ROOT}/missing-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${ROW_REPO}" \
  --json-only >"${ROW_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed after removing required question row"
  exit 1
fi

python3 - <<'PY' "${ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert payload["design_question_closure_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "required_question_closure_rows" and row["reason"] == "missing_expected_rows"
    for row in payload["structure_violations"]
), payload
closure_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_closure_rows"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_status_rows"
)
assert closure_row["expected_count"] == 5, payload
assert closure_row["actual_count"] == 4, payload
assert closure_row["missing_ids"] == ["answer_surface"], payload
assert closure_row["unexpected_ids"] == [], payload
assert closure_row["coverage_status"] == "FAIL_REQUIRED", payload
assert closure_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["expected_count"] == 5, payload
assert status_row["actual_count"] == 4, payload
assert status_row["missing_ids"] == ["answer_surface"], payload
assert status_row["unexpected_ids"] == [], payload
assert status_row["coverage_status"] == "FAIL_REQUIRED", payload
assert status_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-design-question-closure.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_question_closure_rows"]:
    if row.get("question_id") == "answer_surface":
        row["question_id"] = "answer_surface_alias"
        break
else:
    raise SystemExit("expected answer_surface row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed question identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "required_question_closure_rows" and row["reason"] == "missing_expected_rows" and "answer_surface" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "required_question_closure_rows" and row["reason"] == "unexpected_rows" and "answer_surface_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
closure_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_closure_rows"
)
status_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_status_rows"
)
assert closure_row["expected_count"] == 5, payload
assert closure_row["actual_count"] == 5, payload
assert closure_row["missing_ids"] == ["answer_surface"], payload
assert closure_row["unexpected_ids"] == ["answer_surface_alias"], payload
assert closure_row["coverage_status"] == "PASS_REQUIRED", payload
assert closure_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert status_row["expected_count"] == 5, payload
assert status_row["actual_count"] == 5, payload
assert status_row["missing_ids"] == ["answer_surface"], payload
assert status_row["unexpected_ids"] == ["answer_surface_alias"], payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PHILOSOPHY_REPO="${TMP_ROOT}/philosophy-drift-repo"
mirror_repo "${PHILOSOPHY_REPO}"
python3 - <<'PY' "${PHILOSOPHY_REPO}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "5. **Answer-surface question**: What is the stable answer surface ultimately delivered to the operator?"
new = "5. **Answer-surface question**: What is the runtime-facing answer surface ultimately delivered to the operator?"
assert old in text, text[-1200:]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHILOSOPHY_JSON="${TMP_ROOT}/philosophy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${PHILOSOPHY_REPO}" \
  --json-only >"${PHILOSOPHY_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed after philosophy marker drift"
  exit 1
fi

python3 - <<'PY' "${PHILOSOPHY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-003", payload
assert any(
    row["field"] == "philosophy_anchor" and row["reason"] == "required_marker_missing"
    for row in payload["closure_violations"]
), payload
PY

TARGET_REPO="${TMP_ROOT}/target-marker-drift-repo"
mirror_repo "${TARGET_REPO}"
python3 - <<'PY' "${TARGET_REPO}/identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Compression boundary"
new = "## Compression-boundary drift"
assert old in text, text[-1600:]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

TARGET_JSON="${TMP_ROOT}/target-marker-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${TARGET_REPO}" \
  --json-only >"${TARGET_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed after target contract marker drift"
  exit 1
fi

python3 - <<'PY' "${TARGET_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-003", payload
assert any(
    row["field"] == "target_contract" and row["reason"] == "target_marker_missing"
    for row in payload["closure_violations"]
), payload
PY

REGISTRY_REPO="${TMP_ROOT}/registry-child-drift-repo"
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
            if child != "root-design-question-closure.v1.yaml"
        ]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-child-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed after registry-child drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-003", payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "mappings_required_child_missing"
    for row in payload["closure_violations"]
), payload
PY

echo "[PASS] protocol root design-question closure probes passed"
