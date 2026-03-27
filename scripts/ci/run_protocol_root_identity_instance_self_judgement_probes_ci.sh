#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-identity-instance-self-judgement-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

mirror_repo() {
  local dst="$1"
  probe_mirror_repo "${ROOT}" "${dst}"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "PASS_REQUIRED", payload
assert payload["question_count"] == 4, payload
assert payload["anchor_count"] == 4, payload
assert payload["self_judgement_proof_count"] == 5, payload
assert payload["self_judgement_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_family_count"] == 5, payload
assert payload["self_judgement_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_self_judgement_proof_rows"] = [
    row for row in doc["required_self_judgement_proof_rows"] if row.get("proof_id") != "non_self_authorization_self_judgement_proof"
]
for idx, row in enumerate(doc["required_self_judgement_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "non_self_authorization_self_judgement_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_self_judgement_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["non_self_authorization_self_judgement_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

QUESTION_REPO="${TMP_ROOT}/question-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_question_rows"] = [
    row for row in doc["required_question_rows"] if row.get("question_id") != "when_not_my_place"
]
for idx, row in enumerate(doc["required_question_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed missing question row"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "when_not_my_place" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 4, payload
assert question_row["actual_count"] == 3, payload
assert question_row["missing_ids"] == ["when_not_my_place"], payload
assert question_row["unexpected_ids"] == [], payload
assert question_row["coverage_status"] == "FAIL_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_question_rows"]:
    if row.get("question_id") == "when_not_my_place":
        row["question_id"] = "when_not_my_place_alias"
        break
else:
    raise SystemExit("expected when_not_my_place row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed question identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "when_not_my_place" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "when_not_my_place_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 4, payload
assert question_row["actual_count"] == 4, payload
assert question_row["missing_ids"] == ["when_not_my_place"], payload
assert question_row["unexpected_ids"] == ["when_not_my_place_alias"], payload
assert question_row["coverage_status"] == "PASS_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 3. How I do it"
new = "### 3. How I execute"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert any(
    row["reason"] == "question_heading_missing" and row["marker"] == "### 3. How I do it"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "contract_not_registered"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root identity-instance self-judgement completeness discipline"
new = "## Root identity-instance self-judgement discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root identity-instance self-judgement completeness discipline"
    for row in payload["root_doc_anchor_violations"]
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
    if row.get("rel_path") == "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root identity-instance self-judgement probes passed"
