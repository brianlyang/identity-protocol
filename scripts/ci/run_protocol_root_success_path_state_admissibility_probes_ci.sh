#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-success-path-state-admissibility-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "PASS_REQUIRED", payload
assert payload["state_class_count"] == 6, payload
assert payload["differentiation_count"] == 6, payload
assert payload["state_admission_proof_count"] == 5, payload
assert payload["state_admission_limit_count"] == 5, payload
assert payload["collapse_count"] == 6, payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-success-path-state-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_state_admission_proof_rows"] = [
    row for row in doc["required_state_admission_proof_rows"] if row.get("proof_id") != "support_quarantine_confinement_state_admission_proof"
]
for idx, row in enumerate(doc["required_state_admission_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root success-path state admissibility validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SPSA-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "support_quarantine_confinement_state_admission_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

STATE_REPO="${TMP_ROOT}/state-drift-repo"
mirror_repo "${STATE_REPO}"
python3 - <<'PY' "${STATE_REPO}/identity/protocol/mappings/root-success-path-state-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_state_class_rows"] = [
    row for row in doc["required_state_class_rows"] if row.get("state_class_id") != "bound_active_success_path_state"
]
for idx, row in enumerate(doc["required_state_class_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STATE_JSON="${TMP_ROOT}/state-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${STATE_REPO}" \
  --json-only >"${STATE_JSON}"; then
  echo "[FAIL] root success-path state admissibility validator unexpectedly passed missing state-class row"
  exit 1
fi

python3 - <<'PY' "${STATE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SPSA-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "bound_active_success_path_state" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
PY

PHRASE_REPO="${TMP_ROOT}/phrase-drift-repo"
mirror_repo "${PHRASE_REPO}"
python3 - <<'PY' "${PHRASE_REPO}/identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "frozen law-defined state is separated from admissible current-turn state;"
new = "frozen law-defined state is adjacent to admissible current-turn state;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHRASE_JSON="${TMP_ROOT}/phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${PHRASE_REPO}" \
  --json-only >"${PHRASE_JSON}"; then
  echo "[FAIL] root success-path state admissibility validator unexpectedly passed contract phrase drift"
  exit 1
fi

python3 - <<'PY' "${PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SPSA-003", payload
assert any(
    row["reason"] == "contract_phrase_missing" and row["marker"] == "frozen law-defined state is separated from admissible current-turn state;"
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
    if row.get("rel_path") != "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root success-path state admissibility validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SPSA-003", payload
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
    if row.get("rel_path") == "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_success_path_state_admissibility.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root success-path state admissibility validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_success_path_state_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SPSA-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root success-path state admissibility probes passed"
