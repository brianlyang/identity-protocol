#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-current-truth-epistemology-ci"
protocol_root_probe_define_full_mirror

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
assert payload["current_truth_epistemology_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_row_family_count"] == 8, payload
assert payload["current_truth_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_epistemology_completeness_surface"]["entry_count"] == 5, payload
assert payload["current_truth_epistemology_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["family_id"] == "current_truth_epistemology_completeness_rows"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["family_id"] == "current_truth_epistemology_completeness_surface"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["commitment_id"] == "fail_close_justification_before_operational_assertion"
    and row["proof_id"] == "fail_close_justification_proof"
    for row in payload["commitment_proof_alignment_rows"]
), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-current-truth-epistemology.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["current_truth_epistemology_completeness_rows"] = [
    row for row in doc["current_truth_epistemology_completeness_rows"]
    if row.get("completeness_id") != "explicit_current_truth_epistemology_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-002", payload
assert any(
    row["field"] == "current_truth_epistemology_completeness_rows"
    and row["reason"] == "missing_current_truth_epistemology_completeness_rows"
    and "explicit_current_truth_epistemology_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "current_truth_epistemology_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_current_truth_epistemology_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
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

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These current-truth-epistemology-completeness rules must remain bound to canonical current-truth-epistemology-completeness rows rather than drifting into soft summary prose."
new = "These current-truth epistemology rules may be narrated as a soft summary when convenient."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These current-truth-epistemology-completeness rules must remain bound to canonical current-truth-epistemology-completeness rows rather than drifting into soft summary prose."
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
old = "4. runtime or validator code must not finalize current-truth epistemology while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code must not finalize current-truth epistemology while missing row identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize current-truth epistemology while missing or unexpected row identities remain known only internally;"
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-002", payload
assert any(
    reason == "current_truth_epistemology_violation:current_truth_epistemology_completeness_surface:current_truth_epistemology_completeness_surface_phrase_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "current_truth_epistemology_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize current-truth epistemology while missing row identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root current-truth epistemology completeness discipline" \
  "## Root success-path state admissibility completeness discipline" \
  "1. required commitment, differentiation, epistemic-proof, commitment-proof-alignment, epistemic-limit, and collapse rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_current_truth_epistemology.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root current-truth epistemology validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_current_truth_epistemology_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-CTE-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["current_truth_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["current_truth_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "current_truth_epistemology_completeness_surface"
    and row["reason"] == "current_truth_epistemology_completeness_surface_order_mismatch"
    for row in payload["epistemology_violations"]
), payload
assert any(
    reason == "current_truth_epistemology_violation:current_truth_epistemology_completeness_surface:current_truth_epistemology_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "current_truth_epistemology_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
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
