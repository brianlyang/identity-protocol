#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-stream-design-admissibility-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "PASS_REQUIRED", payload
assert payload["question_count"] == 5, payload
assert payload["proof_count"] == 5, payload
assert payload["limit_count"] == 5, payload
assert payload["outcome_count"] == 5, payload
assert payload["projection_surface_count"] == 5, payload
assert payload["stream_design_admissibility_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["stream_design_row_family_count"] == 7, payload
assert payload["stream_design_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["stream_design_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["stream_design_admissibility_completeness_surface"]["entry_count"] == 5, payload
assert payload["stream_design_admissibility_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["family_id"] == "stream_design_admissibility_completeness_rows"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["family_id"] == "stream_design_admissibility_completeness_surface"
    for row in payload["row_family_projection_rows"]
), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-stream-design-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["stream_design_admissibility_completeness_rows"] = [
    row for row in doc["stream_design_admissibility_completeness_rows"]
    if row.get("completeness_id") != "explicit_stream_design_admissibility_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-002", payload
assert any(
    row["field"] == "stream_design_admissibility_completeness_rows"
    and row["reason"] == "missing_stream_design_admissibility_completeness_rows"
    and "explicit_stream_design_admissibility_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "stream_design_admissibility_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_stream_design_admissibility_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-stream-design-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_admissibility_proof_rows"] = [
    row for row in doc["required_admissibility_proof_rows"] if row.get("proof_id") != "answer_surface_closure_proof"
]
for idx, row in enumerate(doc["required_admissibility_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-002", payload
assert payload["stream_design_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["stream_design_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "answer_surface_closure_proof" in row.get("proof_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_admissibility_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["answer_surface_closure_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

QUESTION_REPO="${TMP_ROOT}/question-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-stream-design-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_question_rows"] = [row for row in doc["required_question_rows"] if row.get("question_id") != "answer_surface"]
for idx, row in enumerate(doc["required_question_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed missing question row"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-002", payload
assert payload["stream_design_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["stream_design_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_questions" and "answer_surface" in row.get("question_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 5, payload
assert question_row["actual_count"] == 4, payload
assert question_row["missing_ids"] == ["answer_surface"], payload
assert question_row["unexpected_ids"] == [], payload
assert question_row["coverage_status"] == "FAIL_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-stream-design-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_question_rows"]:
    if row.get("question_id") == "answer_surface":
        row["question_id"] = "answer_surface_alias"
        break
else:
    raise SystemExit("expected answer_surface row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed question identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-002", payload
assert payload["stream_design_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["stream_design_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_questions" and "answer_surface" in row.get("question_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_questions" and "answer_surface_alias" in row.get("question_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 5, payload
assert question_row["actual_count"] == 5, payload
assert question_row["missing_ids"] == ["answer_surface"], payload
assert question_row["unexpected_ids"] == ["answer_surface_alias"], payload
assert question_row["coverage_status"] == "PASS_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 3. Normative question"
new = "### 3. Normativity question"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed contract heading drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-003", payload
assert any(
    row["reason"] == "question_heading_missing" and row["marker"] == "### 3. Normative question"
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
    if row.get("rel_path") != "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-003", payload
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
    if row.get("rel_path") == "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed routing projection drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-003", payload
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
old = "These stream-design-admissibility-completeness rules must remain bound to canonical stream-design-admissibility-completeness rows rather than drifting into soft summary prose."
new = "These stream design admissibility rules may be narrated as a soft summary when convenient."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These stream-design-admissibility-completeness rules must remain bound to canonical stream-design-admissibility-completeness rows rather than drifting into soft summary prose."
    for row in payload["root_doc_anchor_violations"]
), payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. runtime or validator code must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code must not finalize stream-design admissibility legality while missing row identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_stream_design_admissibility.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root stream-design admissibility validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize stream-design admissibility legality while missing or unexpected row identities remain known only internally;"
assert payload["protocol_root_stream_design_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSDA-002", payload
assert any(
    row["field"] == "stream_design_admissibility_completeness_surface"
    and row["reason"] == "stream_design_admissibility_completeness_surface_phrase_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "stream_design_admissibility_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize stream-design admissibility legality while missing row identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

echo "[PASS] protocol root stream-design admissibility probes passed"
