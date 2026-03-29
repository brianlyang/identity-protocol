#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-prompt-bootstrap-ci"
protocol_root_probe_define_full_mirror

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

bump_yaml_row_order_by_id() {
  local path="$1"
  local collection_key="$2"
  local id_field="$3"
  local row_id="$4"
  python3 - <<'PY' "${path}" "${collection_key}" "${id_field}" "${row_id}"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
collection_key = sys.argv[2]
id_field = sys.argv[3]
row_id = sys.argv[4]

doc = yaml.safe_load(path.read_text(encoding="utf-8"))
rows = doc[collection_key]
for row in rows:
    if str(row.get(id_field) or "") == row_id:
        row["order"] = int(row["order"]) + 1
        break
else:
    raise SystemExit(f"{row_id} not found in {collection_key}")

path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY
}

PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "next(marker for marker in EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'] if marker.startswith('## Root ') and marker.endswith('completeness discipline'))"
)"
PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "list(EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values())[0]['order']"
)"
PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "list(EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values())[0]['contract_phrase']"
)"
PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "list(EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values())[1]['order']"
)"
PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "list(EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.values())[1]['contract_phrase']"
)"
PROMPT_BOOTSTRAP_COMPLETENESS_ROW_NONCONTIG_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_prompt_bootstrap" \
    "tuple(EXPECTED_PROMPT_BOOTSTRAP_COMPLETENESS_ROWS.keys())[1]"
)"

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "PASS_REQUIRED", payload
assert payload["anchor_count"] == 6, payload
assert payload["output_field_count"] == 6, payload
assert payload["binding_field_count"] == 5, payload
assert payload["prompt_bootstrap_proof_count"] == 5, payload
assert payload["prompt_bootstrap_limit_count"] == 5, payload
assert payload["native_literal_count"] == 9, payload
assert payload["prompt_bootstrap_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_family_count"] == 8, payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface"]["entry_count"] == 5, payload
assert payload["prompt_bootstrap_completeness_surface"]["extraction_violations"] == [], payload
assert payload["prompt_bootstrap_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "prompt_bootstrap_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "prompt_bootstrap_completeness_surface" for row in payload["row_family_projection_rows"]), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["prompt_bootstrap_completeness_rows"] = [
    row for row in doc["prompt_bootstrap_completeness_rows"]
    if row.get("completeness_id") != "explicit_prompt_bootstrap_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_rows"
    and row["reason"] == "missing_prompt_bootstrap_completeness_rows"
    and "explicit_prompt_bootstrap_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "prompt_bootstrap_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_prompt_bootstrap_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/prompt-bootstrap-completeness-row-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
bump_yaml_row_order_by_id \
  "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml" \
  "prompt_bootstrap_completeness_rows" \
  "completeness_id" \
  "${PROMPT_BOOTSTRAP_COMPLETENESS_ROW_NONCONTIG_ID}"

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/prompt-bootstrap-completeness-row-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed completeness row order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_rows"
    and row["reason"] == "prompt_bootstrap_completeness_row_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_rows"
    and row["reason"] == "prompt_bootstrap_completeness_row_order_mismatch"
    for row in payload["prompt_violations"]
), payload
row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "prompt_bootstrap_completeness_rows"
)
assert row["expected_count"] == 5, payload
assert row["actual_count"] == 5, payload
assert row["missing_ids"] == [], payload
assert row["unexpected_ids"] == [], payload
assert row["coverage_status"] == "PASS_REQUIRED", payload
assert row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_prompt_bootstrap_proof_rows"] = [
    row for row in doc["required_prompt_bootstrap_proof_rows"] if row.get("proof_id") != "hard_guard_literal_preservation_proof"
]
for idx, row in enumerate(doc["required_prompt_bootstrap_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert payload["prompt_bootstrap_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "hard_guard_literal_preservation_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_prompt_bootstrap_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["hard_guard_literal_preservation_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_anchor_rows"]:
    if row.get("anchor_id") == "rq_033_native_chat_headstamp_prompt_contract_v1":
        row["anchor_id"] = "rq_033_native_chat_headstamp_prompt_contract_v1_alias"
        break
else:
    raise SystemExit("expected native-chat headstamp anchor row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed missing anchor row"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "rq_033_native_chat_headstamp_prompt_contract_v1" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "rq_033_native_chat_headstamp_prompt_contract_v1_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "FAIL_REQUIRED", payload
anchor_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_anchor_rows"
)
assert anchor_row["expected_count"] == 6, payload
assert anchor_row["actual_count"] == 6, payload
assert anchor_row["missing_ids"] == ["rq_033_native_chat_headstamp_prompt_contract_v1"], payload
assert anchor_row["unexpected_ids"] == ["rq_033_native_chat_headstamp_prompt_contract_v1_alias"], payload
assert anchor_row["coverage_status"] == "PASS_REQUIRED", payload
assert anchor_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### Shared prompt current-run driver binding projection (v1.6.19 additive)"
new = "### Shared prompt driver binding projection (v1.6.19 additive)"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
assert any(
    row["reason"] == "anchor_heading_missing" and row["marker"] == "### Shared prompt current-run driver binding projection (v1.6.19 additive)"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
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
    if row.get("rel_path") == "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
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
old = "These prompt-bootstrap-completeness rules must remain bound to canonical prompt-bootstrap-completeness rows rather than drifting into soft summary prose."
new = "These prompt bootstrap rules may be narrated as a soft summary when convenient."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These prompt-bootstrap-completeness rules must remain bound to canonical prompt-bootstrap-completeness rows rather than drifting into soft summary prose."
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
old = "4. runtime or validator code must not finalize prompt-bootstrap truth while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code must not finalize prompt-bootstrap truth while missing row identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize prompt-bootstrap truth while missing or unexpected row identities remain known only internally;"
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_surface"
    and row["reason"] == "prompt_bootstrap_completeness_surface_phrase_order_mismatch"
    for row in payload["prompt_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "prompt_bootstrap_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize prompt-bootstrap truth while missing row identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/prompt-bootstrap-completeness-surface-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${PROMPT_BOOTSTRAP_COMPLETENESS_SURFACE_FIRST_ORDER}"

COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/prompt-bootstrap-completeness-surface-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed completeness surface order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_surface"
    and row["reason"] == "prompt_bootstrap_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_surface"
    and row["reason"] == "prompt_bootstrap_completeness_surface_order_mismatch"
    for row in payload["prompt_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "prompt_bootstrap_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

SURFACE_ORDER_REPO="${TMP_ROOT}/prompt-bootstrap-completeness-surface-order-drift-repo"
mirror_repo "${SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root prompt-bootstrap completeness discipline" \
  "## Root entry-surface legitimacy completeness discipline" \
  "1. required anchor, output-field, binding-field, proof, limit, and native-literal rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

SURFACE_ORDER_JSON="${TMP_ROOT}/prompt-bootstrap-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${SURFACE_ORDER_REPO}" \
  --json-only >"${SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "prompt_bootstrap_completeness_surface"
    and row["reason"] == "prompt_bootstrap_completeness_surface_order_mismatch"
    for row in payload["prompt_violations"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "1. required anchor, output-field, binding-field, proof, limit, and native-literal rows must remain explicit as separate machine-readable families;"
    for row in payload["root_doc_anchor_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "prompt_bootstrap_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

echo "[PASS] protocol root prompt-bootstrap probes passed"
