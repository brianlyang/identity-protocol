#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-derivation-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_derivation_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/validate_protocol_root_corpus_derivation.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

DERIVATION_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "root_corpus_derivation_common" \
    "DERIVATION_COMPLETENESS_SECTION_MARKER"
)"
TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "root_corpus_transition_common" \
    "TRANSITION_COMPLETENESS_SECTION_MARKER"
)"
DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "next(class_id for class_id, row in EXPECTED_CLASS_RULES.items() if not row['law_bearing_required'])"
)"
DERIVATION_CLASS_ROOT_CONTRACT="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "next(class_id for class_id, row in EXPECTED_CLASS_RULES.items() if class_id in EXPECTED_CLASS_RULES[EXPECTED_CURRENT_TURN_ALLOWED_CLASS]['allowed_upstream_classes'] and row['law_bearing_required'] and len(tuple(row['allowed_upstream_classes'])) == 3)"
)"
DERIVATION_CLASS_BOTTOM_THEORY="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "next(class_id for class_id, row in EXPECTED_CLASS_RULES.items() if not tuple(row['allowed_upstream_classes']))"
)"
DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY_ALIAS="${DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY}_alias"
DERIVATION_COMPLETENESS_SURFACE_FIRST_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "tuple(EXPECTED_DERIVATION_COMPLETENESS_ROWS.keys())[0]"
)"
DERIVATION_COMPLETENESS_SURFACE_SECOND_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "tuple(EXPECTED_DERIVATION_COMPLETENESS_ROWS.keys())[1]"
)"
DERIVATION_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_DERIVATION_COMPLETENESS_ROWS['${DERIVATION_COMPLETENESS_SURFACE_FIRST_ID}']['order']"
)"
DERIVATION_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_DERIVATION_COMPLETENESS_ROWS['${DERIVATION_COMPLETENESS_SURFACE_FIRST_ID}']['contract_phrase']"
)"
DERIVATION_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_DERIVATION_COMPLETENESS_ROWS['${DERIVATION_COMPLETENESS_SURFACE_SECOND_ID}']['order']"
)"
DERIVATION_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_DERIVATION_COMPLETENESS_ROWS['${DERIVATION_COMPLETENESS_SURFACE_SECOND_ID}']['contract_phrase']"
)"
STATUS_PASS_REQUIRED="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "STATUS_PASS_REQUIRED"
)"
STATUS_FAIL_REQUIRED="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "STATUS_FAIL_REQUIRED"
)"
ERR_STRUCTURE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "ERR_STRUCTURE"
)"
ERR_DERIVATION="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "ERR_DERIVATION"
)"
EXPECTED_CURRENT_TURN_ALLOWED_CLASS="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_CURRENT_TURN_ALLOWED_CLASS"
)"
DERIVATION_COMPLETENESS_FAIL_CLOSE_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "max(EXPECTED_DERIVATION_COMPLETENESS_ROWS.items(), key=lambda item: int(item[1]['order']))[0]"
)"
README_DERIVATION_BINDING_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'][4]"
)"
README_ONE_WAY_DERIVATION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_derivation" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'][0]"
)"

export \
  DERIVATION_COMPLETENESS_SURFACE_SECTION_MARKER \
  TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER \
  DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY \
  DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY_ALIAS \
  DERIVATION_CLASS_ROOT_CONTRACT \
  DERIVATION_CLASS_BOTTOM_THEORY \
  DERIVATION_COMPLETENESS_SURFACE_FIRST_ID \
  DERIVATION_COMPLETENESS_SURFACE_SECOND_ID \
  DERIVATION_COMPLETENESS_SURFACE_FIRST_ORDER \
  DERIVATION_COMPLETENESS_SURFACE_FIRST_PHRASE \
  DERIVATION_COMPLETENESS_SURFACE_SECOND_ORDER \
  DERIVATION_COMPLETENESS_SURFACE_SECOND_PHRASE \
  STATUS_PASS_REQUIRED \
  STATUS_FAIL_REQUIRED \
  ERR_STRUCTURE \
  ERR_DERIVATION \
  EXPECTED_CURRENT_TURN_ALLOWED_CLASS \
  DERIVATION_COMPLETENESS_FAIL_CLOSE_ID \
  README_DERIVATION_BINDING_MARKER \
  README_ONE_WAY_DERIVATION_MARKER


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_family_count"] == 3, payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_count"] == 5, payload
assert payload["derivation_completeness_surface"]["entry_count"] == 5, payload
assert payload["derivation_completeness_surface"]["extraction_violations"] == [], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert all(row["coverage_status"] == os.environ["STATUS_PASS_REQUIRED"] for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"] for row in payload["row_family_projection_rows"]), payload
assert payload["permitted_current_turn_root_corpus_class"] == os.environ["EXPECTED_CURRENT_TURN_ALLOWED_CLASS"], payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml" "${DERIVATION_COMPLETENESS_FAIL_CLOSE_ID}"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
target_completeness_id = sys.argv[2]
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["derivation_completeness_rows"] = [
    row
    for row in doc["derivation_completeness_rows"]
    if row.get("completeness_id") != target_completeness_id
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed after removing derivation completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["derivation_row_family_count"] == 3, payload
assert payload["derivation_completeness_row_count"] == 4, payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert any(
    row["field"] == "derivation_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and os.environ["DERIVATION_COMPLETENESS_FAIL_CLOSE_ID"] in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == [os.environ["DERIVATION_COMPLETENESS_FAIL_CLOSE_ID"]], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert completeness_row["identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
PY

MISSING_CLASS_REPO="${TMP_ROOT}/missing-class-repo"
mirror_repo "${MISSING_CLASS_REPO}"
python3 - <<'PY' "${MISSING_CLASS_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import os
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["derivation_class_profiles"] = [
    row for row in doc["derivation_class_profiles"]
    if row.get("corpus_class") != os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"]
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_CLASS_JSON="${TMP_ROOT}/missing-class.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${MISSING_CLASS_REPO}" \
  --json-only >"${MISSING_CLASS_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed after removing derivation class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_CLASS_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert any(
    row["field"] == "derivation_class_profiles"
    and row["reason"] == "missing_registry_classes"
    and os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"] in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_class_profiles"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 7, payload
assert class_row["missing_ids"] == [os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"]], payload
assert class_row["unexpected_ids"] == [], payload
assert class_row["coverage_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert class_row["identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import os
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_class_profiles"]:
    if row.get("corpus_class") == os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"]:
        row["corpus_class"] = os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY_ALIAS"]
        break
else:
    raise SystemExit(
        f"expected {os.environ['DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY']} row not found"
    )
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert any(
    row["field"] == "derivation_class_profiles"
    and row["reason"] == "missing_registry_classes"
    and os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"] in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "derivation_class_profiles"
    and row["reason"] == "extra_unregistered_classes"
    and os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY_ALIAS"] in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_class_profiles"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 8, payload
assert class_row["missing_ids"] == [os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"]], payload
assert class_row["unexpected_ids"] == [os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY_ALIAS"]], payload
assert class_row["coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert class_row["identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/derivation-completeness-row-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml" "${DERIVATION_COMPLETENESS_SURFACE_SECOND_ID}"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
target_id = sys.argv[2]
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_completeness_rows"]:
    if row.get("completeness_id") == target_id:
        row["order"] = 1
        break
else:
    raise SystemExit("expected derivation completeness row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/derivation-completeness-row-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation completeness row order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert any(
    reason
    == "structure_violation:derivation_completeness_rows:derivation_completeness_row_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload["stale_reasons"]
assert any(
    reason
    == "derivation_violation:derivation_completeness_rows:derivation_completeness_row_order_mismatch"
    for reason in payload["stale_reasons"]
), payload["stale_reasons"]
PY

SURFACE_REPO="${TMP_ROOT}/surface-drift-repo"
mirror_repo "${SURFACE_REPO}"
python3 - <<'PY' "${SURFACE_REPO}/identity/protocol/README.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = os.environ["DERIVATION_COMPLETENESS_SURFACE_SECTION_MARKER"]
next_marker = "\n---\n\n" + os.environ["TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER"]
old = (
    f"{os.environ['DERIVATION_COMPLETENESS_SURFACE_SECOND_ORDER']}. "
    f"{os.environ['DERIVATION_COMPLETENESS_SURFACE_SECOND_PHRASE']}"
)
new = "2. expected row-family total and emitted row-family total may be summarized informally once counts look green;"
assert section_marker in text, text
assert next_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, after = rest.split(next_marker, 1)
assert old in section_body, section_body
section_body = section_body.replace(old, new, 1)
path.write_text(before + section_marker + section_body + next_marker + after, encoding="utf-8")
PY

SURFACE_JSON="${TMP_ROOT}/surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${SURFACE_REPO}" \
  --json-only >"${SURFACE_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed README derivation completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "missing_derivation_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "extra_derivation_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert surface_row["identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/derivation-completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows_in_section \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "${DERIVATION_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${DERIVATION_COMPLETENESS_SURFACE_FIRST_PHRASE}" \
  "${DERIVATION_COMPLETENESS_SURFACE_SECOND_PHRASE}"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/derivation-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_DERIVATION"], payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "derivation_completeness_surface_order_mismatch"
    for row in payload["derivation_violations"]
), payload
assert any(
    "derivation_violation:derivation_completeness_surface:derivation_completeness_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert surface_row["identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
PY

COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/derivation-completeness-surface-order-non-contiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${DERIVATION_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${DERIVATION_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${DERIVATION_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${DERIVATION_COMPLETENESS_SURFACE_FIRST_ORDER}"

COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/derivation-completeness-surface-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation completeness surface non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_STRUCTURE"], payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_class_profile_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_row_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert payload["derivation_completeness_surface_identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "derivation_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "derivation_completeness_surface_order_mismatch"
    for row in payload["derivation_violations"]
), payload
assert any(
    reason == "structure_violation:derivation_completeness_surface:derivation_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    reason == "derivation_violation:derivation_completeness_surface:derivation_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
assert surface_row["identity_projection_status"] == os.environ["STATUS_PASS_REQUIRED"], payload
PY

BINDING_REPO="${TMP_ROOT}/binding-drift-repo"
mirror_repo "${BINDING_REPO}"
python3 - <<'PY' "${BINDING_REPO}/identity/protocol/README.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = os.environ["README_DERIVATION_BINDING_MARKER"]
new = "These derivation completeness rules may be summarized freely once the main idea is understood."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

BINDING_JSON="${TMP_ROOT}/binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${BINDING_REPO}" \
  --json-only >"${BINDING_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed README derivation binding drift"
  exit 1
fi

python3 - <<'PY' "${BINDING_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_DERIVATION"], payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and os.environ["README_DERIVATION_BINDING_MARKER"] in row.get("marker", "")
    for row in payload["anchor_violations"]
), payload
PY

SUPPORT_REPO="${TMP_ROOT}/support-parent-drift-repo"
mirror_repo "${SUPPORT_REPO}"
python3 - <<'PY' "${SUPPORT_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import os
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_class_profiles"]:
    if row["corpus_class"] == os.environ["DERIVATION_CLASS_ROOT_CONTRACT"]:
        row["allowed_upstream_classes"].append(os.environ["DERIVATION_CLASS_DEMOTED_SUPPORT_DIRECTORY"])
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUPPORT_JSON="${TMP_ROOT}/support-parent-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${SUPPORT_REPO}" \
  --json-only >"${SUPPORT_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed demoted-support parent drift"
  exit 1
fi

python3 - <<'PY' "${SUPPORT_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_DERIVATION"], payload
assert any(
    row["reason"] in {"law_bearing_class_must_not_derive_from_demoted_support", "allowed_upstream_classes_mismatch"}
    and row.get("corpus_class") == os.environ["DERIVATION_CLASS_ROOT_CONTRACT"]
    for row in payload["derivation_violations"]
), payload
PY

QUESTION_REPO="${TMP_ROOT}/question-routing-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import os
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_redirect"]["forbidden_root_corpus_classes"] = [
    item for item in doc["adjudication_redirect"]["forbidden_root_corpus_classes"]
    if item != os.environ["DERIVATION_CLASS_BOTTOM_THEORY"]
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed adjudication forbidden-class drift"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_DERIVATION"], payload
assert any(
    row["reason"] == "current_turn_forbidden_root_classes_mismatch"
    for row in payload["derivation_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = os.environ["README_ONE_WAY_DERIVATION_MARKER"]
new = old.replace("One-way", "One way", 1)
assert old in text, text[:800]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert payload["error_code"] == os.environ["ERR_DERIVATION"], payload
assert payload["root_doc_anchor_status"] == os.environ["STATUS_FAIL_REQUIRED"], payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus derivation probes passed"
