#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-entry-surface-legitimacy-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "PASS_REQUIRED", payload
assert payload["entry_class_count"] == 6, payload
assert payload["differentiation_count"] == 6, payload
assert payload["entry_admission_proof_count"] == 5, payload
assert payload["entry_admission_limit_count"] == 5, payload
assert payload["collapse_count"] == 6, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["entry_surface_row_family_count"] == 5, payload
assert payload["entry_surface_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["entry_surface_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-entry-surface-legitimacy.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_entry_admission_proof_rows"] = [
    row for row in doc["required_entry_admission_proof_rows"] if row.get("proof_id") != "helper_support_demotion_entry_admission_proof"
]
for idx, row in enumerate(doc["required_entry_admission_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-002", payload
assert payload["entry_surface_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["entry_surface_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "helper_support_demotion_entry_admission_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_entry_admission_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["helper_support_demotion_entry_admission_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ENTRY_REPO="${TMP_ROOT}/entry-drift-repo"
mirror_repo "${ENTRY_REPO}"
python3 - <<'PY' "${ENTRY_REPO}/identity/protocol/mappings/root-entry-surface-legitimacy.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_entry_class_rows"]:
    if row.get("entry_class_id") == "governed_execution_entry_surface":
        row["entry_class_id"] = "governed_execution_entry_surface_alias"
        break
else:
    raise SystemExit("expected governed_execution_entry_surface row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ENTRY_JSON="${TMP_ROOT}/entry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${ENTRY_REPO}" \
  --json-only >"${ENTRY_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed missing entry-class row"
  exit 1
fi

python3 - <<'PY' "${ENTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "governed_execution_entry_surface" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "governed_execution_entry_surface_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["entry_surface_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["entry_surface_row_identity_projection_status"] == "FAIL_REQUIRED", payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_entry_class_rows"
)
assert entry_row["expected_count"] == 6, payload
assert entry_row["actual_count"] == 6, payload
assert entry_row["missing_ids"] == ["governed_execution_entry_surface"], payload
assert entry_row["unexpected_ids"] == ["governed_execution_entry_surface_alias"], payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PHRASE_REPO="${TMP_ROOT}/phrase-drift-repo"
mirror_repo "${PHRASE_REPO}"
python3 - <<'PY' "${PHRASE_REPO}/identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "discoverability-helper surface is separated from canonical execution entry;"
new = "discoverability-helper surface is close to canonical execution entry;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHRASE_JSON="${TMP_ROOT}/phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${PHRASE_REPO}" \
  --json-only >"${PHRASE_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed contract phrase drift"
  exit 1
fi

python3 - <<'PY' "${PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-003", payload
assert any(
    row["reason"] == "contract_phrase_missing" and row["marker"] == "discoverability-helper surface is separated from canonical execution entry;"
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
    if row.get("rel_path") != "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-003", payload
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
    if row.get("rel_path") == "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
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
old = "## Root entry-surface legitimacy completeness discipline"
new = "## Root entry-surface legitimacy discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_entry_surface_legitimacy.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root entry-surface legitimacy validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_entry_surface_legitimacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ESL-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root entry-surface legitimacy completeness discipline"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root entry-surface legitimacy probes passed"
