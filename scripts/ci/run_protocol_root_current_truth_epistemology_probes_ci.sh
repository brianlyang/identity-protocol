#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-current-truth-epistemology-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "PASS_REQUIRED", payload
assert payload["commitment_count"] == 5, payload
assert payload["differentiation_count"] == 6, payload
assert payload["epistemic_proof_count"] == 5, payload
assert payload["commitment_proof_alignment_count"] == 5, payload
assert payload["epistemic_limit_count"] == 5, payload
assert payload["collapse_count"] == 7, payload
assert payload["current_truth_row_family_count"] == 6, payload
assert payload["current_truth_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["commitment_id"] == "fail_close_justification_before_operational_assertion"
    and row["proof_id"] == "fail_close_justification_proof"
    for row in payload["commitment_proof_alignment_rows"]
), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-current-truth-epistemology.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_epistemic_proof_rows"] = [
    row for row in doc["required_epistemic_proof_rows"] if row.get("proof_id") != "fail_close_justification_proof"
]
for idx, row in enumerate(doc["required_epistemic_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed missing epistemic proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-002", payload
assert payload["current_truth_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["current_truth_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "fail_close_justification_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_epistemic_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["fail_close_justification_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMMITMENT_REPO="${TMP_ROOT}/commitment-drift-repo"
mirror_repo "${COMMITMENT_REPO}"
python3 - <<'PY' "${COMMITMENT_REPO}/identity/protocol/mappings/root-current-truth-epistemology.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_commitment_rows"]:
    if row.get("commitment_id") == "present_turn_authority_before_visible_recency":
        row["commitment_id"] = "present_turn_authority_before_visible_recency_alias"
        break
else:
    raise SystemExit("expected present_turn_authority_before_visible_recency row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMMITMENT_JSON="${TMP_ROOT}/commitment-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${COMMITMENT_REPO}" \
  --json-only >"${COMMITMENT_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed commitment identity drift"
  exit 1
fi

python3 - <<'PY' "${COMMITMENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "present_turn_authority_before_visible_recency" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "present_turn_authority_before_visible_recency_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["current_truth_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_row_identity_projection_status"] == "FAIL_REQUIRED", payload
commitment_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_commitment_rows"
)
assert commitment_row["expected_count"] == 5, payload
assert commitment_row["actual_count"] == 5, payload
assert commitment_row["missing_ids"] == ["present_turn_authority_before_visible_recency"], payload
assert commitment_row["unexpected_ids"] == ["present_turn_authority_before_visible_recency_alias"], payload
assert commitment_row["coverage_status"] == "PASS_REQUIRED", payload
assert commitment_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ALIGNMENT_REPO="${TMP_ROOT}/alignment-drift-repo"
mirror_repo "${ALIGNMENT_REPO}"
python3 - <<'PY' "${ALIGNMENT_REPO}/identity/protocol/mappings/root-current-truth-epistemology.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_commitment_proof_alignment_rows"]:
    if row.get("commitment_id") == "fail_close_justification_before_operational_assertion":
        row["proof_id"] = "present_turn_authority_proof"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ALIGNMENT_JSON="${TMP_ROOT}/alignment-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${ALIGNMENT_REPO}" \
  --json-only >"${ALIGNMENT_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed commitment-proof alignment drift"
  exit 1
fi

python3 - <<'PY' "${ALIGNMENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
assert any(
    row["field"] == "required_commitment_proof_alignment_rows"
    and row["row_id"] == "fail_close_justification_before_operational_assertion"
    and row["reason"] == "proof_id_mismatch"
    for row in payload["epistemology_violations"]
), payload
PY

PHRASE_REPO="${TMP_ROOT}/phrase-drift-repo"
mirror_repo "${PHRASE_REPO}"
python3 - <<'PY' "${PHRASE_REPO}/identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "installed and discoverability are separated;"
new = "installed and discoverability are often nearby;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHRASE_JSON="${TMP_ROOT}/phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${PHRASE_REPO}" \
  --json-only >"${PHRASE_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed contract phrase drift"
  exit 1
fi

python3 - <<'PY' "${PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
assert any(
    row["reason"] == "contract_phrase_missing" and row["marker"] == "installed and discoverability are separated;"
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
    if row.get("rel_path") != "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
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
    if row.get("rel_path") == "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root current-truth epistemology probes passed"
