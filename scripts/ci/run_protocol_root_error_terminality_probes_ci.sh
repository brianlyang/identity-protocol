#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-error-terminality-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "PASS_REQUIRED", payload
assert payload["error_class_count"] == 7, payload
assert payload["differentiation_count"] == 7, payload
assert payload["error_terminality_proof_count"] == 7, payload
assert payload["error_terminality_limit_count"] == 7, payload
assert payload["collapse_count"] == 7, payload
assert payload["error_terminality_row_family_count"] == 5, payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_error_terminality_proof_rows"] = [
    row for row in doc["required_error_terminality_proof_rows"] if row.get("proof_id") != "support_explanatory_demotion_error_terminality_proof"
]
for idx, row in enumerate(doc["required_error_terminality_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert payload["error_terminality_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "support_explanatory_demotion_error_terminality_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_error_terminality_proof_rows"
)
assert proof_row["expected_count"] == 7, payload
assert proof_row["actual_count"] == 6, payload
assert proof_row["missing_ids"] == ["support_explanatory_demotion_error_terminality_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ERROR_REPO="${TMP_ROOT}/error-drift-repo"
mirror_repo "${ERROR_REPO}"
python3 - <<'PY' "${ERROR_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_error_class_rows"]:
    if row.get("error_class_id") == "binding_integrity_error":
        row["error_class_id"] = "binding_integrity_error_alias"
        break
else:
    raise SystemExit("expected binding_integrity_error row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ERROR_JSON="${TMP_ROOT}/error-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ERROR_REPO}" \
  --json-only >"${ERROR_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed missing error-class row"
  exit 1
fi

python3 - <<'PY' "${ERROR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "binding_integrity_error" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "binding_integrity_error_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "FAIL_REQUIRED", payload
error_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_error_class_rows"
)
assert error_row["expected_count"] == 7, payload
assert error_row["actual_count"] == 7, payload
assert error_row["missing_ids"] == ["binding_integrity_error"], payload
assert error_row["unexpected_ids"] == ["binding_integrity_error_alias"], payload
assert error_row["coverage_status"] == "PASS_REQUIRED", payload
assert error_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PHRASE_REPO="${TMP_ROOT}/phrase-drift-repo"
mirror_repo "${PHRASE_REPO}"
python3 - <<'PY' "${PHRASE_REPO}/identity/protocol/ERROR_TERMINALITY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "governed recovery-redirect error is separated from non-blocking observation error;"
new = "governed recovery-redirect error is close to non-blocking observation error;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHRASE_JSON="${TMP_ROOT}/phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${PHRASE_REPO}" \
  --json-only >"${PHRASE_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed contract phrase drift"
  exit 1
fi

python3 - <<'PY' "${PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
assert any(
    row["reason"] == "contract_phrase_missing" and row["marker"] == "governed recovery-redirect error is separated from non-blocking observation error;"
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
    if row.get("rel_path") != "identity/protocol/ERROR_TERMINALITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
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
    if row.get("rel_path") == "identity/protocol/ERROR_TERMINALITY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root error terminality probes passed"
