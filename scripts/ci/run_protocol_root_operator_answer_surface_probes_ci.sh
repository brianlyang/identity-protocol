#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-operator-answer-surface-ci"
protocol_root_probe_define_full_mirror

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
assert payload["answer_claim_alignment_count"] == 5, payload
assert payload["answer_claim_epistemic_alignment_count"] == 5, payload
assert payload["answer_surface_proof_count"] == 5, payload
assert payload["answer_surface_limit_count"] == 6, payload
assert payload["boundary_count"] == 4, payload
assert payload["collapse_count"] == 7, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["operator_answer_row_family_count"] == 9, payload
assert payload["operator_answer_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["operator_answer_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["claim_id"] == "realized_effect_answer_claim"
    and row["decision_evidence_proof_id"] == "adjudicated_verdict_closure_decision_evidence_proof"
    for row in payload["answer_claim_alignment_rows"]
), payload
assert any(
    row["claim_id"] == "realized_effect_answer_claim"
    and row["current_truth_proof_id"] == "provenance_preserving_derivation_proof"
    for row in payload["answer_claim_epistemic_alignment_rows"]
), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_answer_surface_proof_rows"] = [
    row for row in doc["required_answer_surface_proof_rows"] if row.get("proof_id") != "realized_effect_answer_backing_proof"
]
for idx, row in enumerate(doc["required_answer_surface_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed missing answer-surface proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-002", payload
assert payload["operator_answer_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["operator_answer_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "realized_effect_answer_backing_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_answer_surface_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["realized_effect_answer_backing_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SUPPORT_REPO="${TMP_ROOT}/support-drift-repo"
mirror_repo "${SUPPORT_REPO}"
python3 - <<'PY' "${SUPPORT_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_support_memory_rows"]:
    if row.get("support_id") == "consumption_memory_support":
        row["support_id"] = "consumption_memory_support_alias"
        break
else:
    raise SystemExit("expected consumption_memory_support row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUPPORT_JSON="${TMP_ROOT}/support-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${SUPPORT_REPO}" \
  --json-only >"${SUPPORT_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed support-memory identity drift"
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
assert any(
    row["reason"] == "extra_rows" and "consumption_memory_support_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["operator_answer_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["operator_answer_row_identity_projection_status"] == "FAIL_REQUIRED", payload
support_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_support_memory_rows"
)
assert support_row["expected_count"] == 5, payload
assert support_row["actual_count"] == 5, payload
assert support_row["missing_ids"] == ["consumption_memory_support"], payload
assert support_row["unexpected_ids"] == ["consumption_memory_support_alias"], payload
assert support_row["coverage_status"] == "PASS_REQUIRED", payload
assert support_row["identity_projection_status"] == "FAIL_REQUIRED", payload
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

ALIGNMENT_REPO="${TMP_ROOT}/alignment-drift-repo"
mirror_repo "${ALIGNMENT_REPO}"
python3 - <<'PY' "${ALIGNMENT_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_answer_claim_alignment_rows"]:
    if row.get("claim_id") == "realized_effect_answer_claim":
        row["decision_evidence_proof_id"] = "bound_runtime_decision_evidence_proof"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ALIGNMENT_JSON="${TMP_ROOT}/alignment-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${ALIGNMENT_REPO}" \
  --json-only >"${ALIGNMENT_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed realized-effect backing drift"
  exit 1
fi

python3 - <<'PY' "${ALIGNMENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
assert any(
    row["reason"] == "realized_effect_claim_not_closure_backed"
    and row["claim_id"] == "realized_effect_answer_claim"
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
old = "## Root operator answer-surface completeness discipline"
new = "## Root operator answer-surface discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root operator answer-surface completeness discipline"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

EPISTEMIC_REPO="${TMP_ROOT}/epistemic-drift-repo"
mirror_repo "${EPISTEMIC_REPO}"
python3 - <<'PY' "${EPISTEMIC_REPO}/identity/protocol/mappings/root-operator-answer-surface.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_answer_claim_epistemic_alignment_rows"]:
    if row.get("claim_id") == "realized_effect_answer_claim":
        row["current_truth_proof_id"] = "present_turn_authority_proof"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

EPISTEMIC_JSON="${TMP_ROOT}/epistemic-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_operator_answer_surface.py" \
  --repo-root "${EPISTEMIC_REPO}" \
  --json-only >"${EPISTEMIC_JSON}"; then
  echo "[FAIL] root operator answer-surface validator unexpectedly passed realized-effect epistemic drift"
  exit 1
fi

python3 - <<'PY' "${EPISTEMIC_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_operator_answer_surface_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ROAS-003", payload
assert any(
    row["reason"] == "realized_effect_claim_not_provenance_grounded"
    and row["claim_id"] == "realized_effect_answer_claim"
    for row in payload["integration_violations"]
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
