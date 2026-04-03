#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-design-question-closure-ci"
protocol_root_probe_define_full_mirror
export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

bump_yaml_row_order_by_id() {
  local path="$1"
  local collection_key="$2"
  local id_field="$3"
  local row_id="$4"
  python3 - "$path" "$collection_key" "$id_field" "$row_id" <<'PY'
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

bump_numbered_surface_row_order_in_section() {
  local path="$1"
  local section_marker="$2"
  local order="$3"
  local phrase="$4"
  python3 - "$path" "$section_marker" "$order" "$phrase" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
section_marker = sys.argv[2]
order = int(sys.argv[3])
phrase = sys.argv[4]

text = path.read_text(encoding="utf-8")
assert section_marker in text, section_marker
before, rest = text.split(section_marker, 1)
section_body, next_heading, after = rest.partition("\n## ")
old = f"{order}. {phrase}"
new = f"{order + 1}. {phrase}"
assert old in section_body, old
section_body = section_body.replace(old, new, 1)
rebuilt = before + section_marker + section_body
if next_heading:
    rebuilt += next_heading + after
path.write_text(rebuilt, encoding="utf-8")
PY
}

DESIGN_QUESTION_ORDER_NONCONTIG_ROW_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_design_question_closure" \
    "tuple(EXPECTED_QUESTION_CLOSURE_ROWS.keys())[1]"
)"
DESIGN_QUESTION_COMPLETENESS_NONCONTIG_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_design_question_closure" \
    "tuple(EXPECTED_DESIGN_QUESTION_CLOSURE_COMPLETENESS_ROWS.keys())[1]"
)"
DESIGN_QUESTION_COMPLETENESS_SURFACE_NONCONTIG_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_design_question_closure" \
    "list(EXPECTED_DESIGN_QUESTION_CLOSURE_COMPLETENESS_ROWS.values())[1]['order']"
)"
DESIGN_QUESTION_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_design_question_closure" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'][0]"
)"
DESIGN_QUESTION_COMPLETENESS_SURFACE_NONCONTIG_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_design_question_closure" \
    "list(EXPECTED_DESIGN_QUESTION_CLOSURE_COMPLETENESS_ROWS.values())[1]['contract_phrase']"
)"

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
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["question_ids"] == [
    "ontology",
    "truth_lifecycle",
    "normative",
    "responsibility_split",
    "answer_surface",
], payload
assert payload["design_question_closure_row_family_count"] == 4, payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_row_count"] == 5, payload
assert payload["design_question_closure_completeness_surface"]["entry_count"] == 5, payload
assert payload["design_question_closure_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "design_question_closure_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "design_question_closure_completeness_surface" for row in payload["row_family_projection_rows"]), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-design-question-closure.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["design_question_closure_completeness_rows"] = [
    row for row in doc["design_question_closure_completeness_rows"]
    if row.get("completeness_id") != "explicit_design_question_closure_row_families"
]
for idx, row in enumerate(doc["design_question_closure_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed after removing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert any(
    row["field"] == "design_question_closure_completeness_rows"
    and row["reason"] == "missing_design_question_closure_completeness_rows"
    and "explicit_design_question_closure_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "design_question_closure_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_design_question_closure_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_NONCONTIG_REPO="${TMP_ROOT}/completeness-row-non-contiguous-repo"
mirror_repo "${COMPLETENESS_ROW_NONCONTIG_REPO}"
bump_yaml_row_order_by_id \
  "${COMPLETENESS_ROW_NONCONTIG_REPO}/identity/protocol/mappings/root-design-question-closure.v1.yaml" \
  "design_question_closure_completeness_rows" \
  "completeness_id" \
  "${DESIGN_QUESTION_COMPLETENESS_NONCONTIG_ID}"

COMPLETENESS_ROW_NONCONTIG_JSON="${TMP_ROOT}/completeness-row-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${COMPLETENESS_ROW_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_ROW_NONCONTIG_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed non-contiguous completeness-row ordering"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    reason == "structure_violation:design_question_closure_completeness_rows:design_question_closure_completeness_row_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["field"] == "design_question_closure_completeness_rows"
    and row["reason"] == "design_question_closure_completeness_row_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "design_question_closure_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
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

QUESTION_ORDER_NONCONTIG_REPO="${TMP_ROOT}/question-order-non-contiguous-repo"
mirror_repo "${QUESTION_ORDER_NONCONTIG_REPO}"
bump_yaml_row_order_by_id \
  "${QUESTION_ORDER_NONCONTIG_REPO}/identity/protocol/mappings/root-design-question-closure.v1.yaml" \
  "required_question_closure_rows" \
  "question_id" \
  "${DESIGN_QUESTION_ORDER_NONCONTIG_ROW_ID}"

QUESTION_ORDER_NONCONTIG_JSON="${TMP_ROOT}/question-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${QUESTION_ORDER_NONCONTIG_REPO}" \
  --json-only >"${QUESTION_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed non-contiguous question ordering"
  exit 1
fi

python3 - <<'PY' "${QUESTION_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "required_question_closure_rows"
    and row["reason"] == "question_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    reason == "structure_violation:required_question_closure_rows:question_order_non_contiguous"
    for reason in payload["stale_reasons"]
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
assert closure_row["missing_ids"] == [], payload
assert closure_row["unexpected_ids"] == [], payload
assert closure_row["coverage_status"] == "PASS_REQUIRED", payload
assert closure_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert status_row["expected_count"] == 5, payload
assert status_row["actual_count"] == 5, payload
assert status_row["missing_ids"] == [], payload
assert status_row["unexpected_ids"] == [], payload
assert status_row["coverage_status"] == "PASS_REQUIRED", payload
assert status_row["identity_projection_status"] == "PASS_REQUIRED", payload
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

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These design-question-closure-completeness rules must remain bound to canonical design-question-closure-completeness rows rather than drifting into soft summary prose."
new = "These design-question-closure rules may be narrated as a soft summary when convenient."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These design-question-closure-completeness rules must remain bound to canonical design-question-closure-completeness rows rather than drifting into soft summary prose."
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
old = "4. runtime or validator code must not finalize design-question closure legality while missing or unexpected question identities remain known only internally;"
new = "4. runtime or validator code must not finalize design-question closure legality while missing question identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize design-question closure legality while missing or unexpected question identities remain known only internally;"
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert any(
    "closure_violation:design_question_closure_completeness_surface:design_question_closure_completeness_surface_phrase_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "design_question_closure_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize design-question closure legality while missing question identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SURFACE_ORDER_REPO="${TMP_ROOT}/design-question-closure-completeness-surface-order-drift-repo"
mirror_repo "${SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root design-question closure completeness discipline" \
  "## Root machine-law primacy completeness discipline" \
  "1. required question-closure rows and emitted question-status rows must remain explicit as separate machine-readable row families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

SURFACE_ORDER_JSON="${TMP_ROOT}/design-question-closure-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${SURFACE_ORDER_REPO}" \
  --json-only >"${SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "design_question_closure_completeness_surface"
    and row["reason"] == "design_question_closure_completeness_surface_order_mismatch"
    for row in payload["closure_violations"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "1. required question-closure rows and emitted question-status rows must remain explicit as separate machine-readable row families;"
    for row in payload["root_doc_anchor_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "design_question_closure_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_NONCONTIG_REPO="${TMP_ROOT}/completeness-surface-non-contiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_NONCONTIG_REPO}"
bump_numbered_surface_row_order_in_section \
  "${COMPLETENESS_SURFACE_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${DESIGN_QUESTION_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${DESIGN_QUESTION_COMPLETENESS_SURFACE_NONCONTIG_ORDER}" \
  "${DESIGN_QUESTION_COMPLETENESS_SURFACE_NONCONTIG_PHRASE}"

COMPLETENESS_SURFACE_NONCONTIG_JSON="${TMP_ROOT}/completeness-surface-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_design_question_closure.py" \
  --repo-root "${COMPLETENESS_SURFACE_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_NONCONTIG_JSON}"; then
  echo "[FAIL] root design-question closure validator unexpectedly passed non-contiguous completeness-surface ordering"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_design_question_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RDQC-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["design_question_closure_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "design_question_closure_completeness_surface"
    and row["reason"] == "design_question_closure_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    reason == "structure_violation:design_question_closure_completeness_surface:design_question_closure_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "design_question_closure_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

echo "[PASS] protocol root design-question closure probes passed"
