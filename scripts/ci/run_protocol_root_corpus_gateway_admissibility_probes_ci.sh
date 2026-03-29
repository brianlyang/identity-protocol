#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-gateway-admissibility-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/root_corpus_gateway_admissibility_common.py"
  "scripts/root_row_family_projection_common.py"
  "scripts/validate_protocol_root_corpus_gateway_admissibility.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

GATEWAY_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_gateway_admissibility" \
    "next(marker for marker in EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'] if marker.startswith('## Root ') and marker.endswith('completeness discipline'))"
)"
GATEWAY_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_gateway_admissibility" \
    "list(EXPECTED_GATEWAY_ADMISSIBILITY_COMPLETENESS_ROWS.values())[0]['order']"
)"
GATEWAY_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_gateway_admissibility" \
    "list(EXPECTED_GATEWAY_ADMISSIBILITY_COMPLETENESS_ROWS.values())[0]['contract_phrase']"
)"
GATEWAY_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_gateway_admissibility" \
    "list(EXPECTED_GATEWAY_ADMISSIBILITY_COMPLETENESS_ROWS.values())[1]['order']"
)"
GATEWAY_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_gateway_admissibility" \
    "list(EXPECTED_GATEWAY_ADMISSIBILITY_COMPLETENESS_ROWS.values())[1]['contract_phrase']"
)"

assert_stale_reason_present() {
  local json_file="$1"
  local expected_reason="$2"
  python3 - <<'PY' "${json_file}" "${expected_reason}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
reason = sys.argv[2]
assert reason in payload.get("stale_reasons", []), payload
PY
}


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_family_count"] == 5, payload
assert payload["gateway_admissibility_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_count"] == 5, payload
assert payload["gateway_admissibility_completeness_surface"]["entry_count"] == 5, payload
assert payload["gateway_admissibility_completeness_surface"]["extraction_violations"] == [], payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["current_turn_terminal_gateway"] == "machine_registry_directory", payload
assert [row["gateway_class"] for row in payload["gateway_order"]] == [
    "constitution",
    "runtime_constitution",
    "root_contract",
    "machine_registry_directory",
], payload
assert {row["gateway_class"]: row["effect_target_class"] for row in payload["gateway_effect_targets"]} == {
    "constitution": "constitution",
    "runtime_constitution": "runtime_constitution",
    "root_contract": "root_contract",
    "machine_registry_directory": "machine_registry_directory",
}, payload
assert {row["gateway_class"]: row["effect_target_question_class"] for row in payload["gateway_effect_targets"]} == {
    "constitution": "frozen_protocol_law",
    "runtime_constitution": "frozen_runtime_law",
    "root_contract": "frozen_domain_contract_law",
    "machine_registry_directory": "registry_resolution",
}, payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-gateway-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["gateway_admissibility_completeness_rows"] = doc["gateway_admissibility_completeness_rows"][:-1]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-gateway-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed after removing gateway completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert payload["gateway_admissibility_row_family_count"] == 5, payload
assert payload["gateway_admissibility_completeness_row_count"] == 4, payload
assert any(
    row["field"] == "gateway_admissibility_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "fail_close_preserves_gateway_admissibility_identity_projection" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_admissibility_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_gateway_admissibility_identity_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["gateway_profiles"] = [
    row for row in doc["gateway_profiles"]
    if row.get("gateway_class") != "machine_registry_directory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed after removing gateway profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert payload["gateway_admissibility_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "gateway_profiles" and row["reason"] == "missing_gateway_classes" and "machine_registry_directory" in row.get("gateway_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_profiles"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 3, payload
assert profile_row["missing_ids"] == ["machine_registry_directory"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_DRIFT_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_DRIFT_REPO}"
python3 - <<'PY' "${IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_profiles"]:
    if row.get("gateway_class") == "machine_registry_directory":
        row["gateway_class"] = "machine_registry_directory_alias"
        break
else:
    raise SystemExit("expected machine_registry_directory row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_DRIFT_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${IDENTITY_DRIFT_REPO}" \
  --json-only >"${IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway profile identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert payload["gateway_admissibility_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "gateway_profiles" and row["reason"] == "missing_gateway_classes" and "machine_registry_directory" in row.get("gateway_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "gateway_profiles" and row["reason"] == "extra_gateway_classes" and "machine_registry_directory_alias" in row.get("gateway_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_profiles"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 4, payload
assert profile_row["missing_ids"] == ["machine_registry_directory"], payload
assert profile_row["unexpected_ids"] == ["machine_registry_directory_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

INPUT_DRIFT_REPO="${TMP_ROOT}/input-drift-repo"
mirror_repo "${INPUT_DRIFT_REPO}"
python3 - <<'PY' "${INPUT_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_profiles"]:
    if row["gateway_class"] == "constitution":
        row["admissible_nonorigin_surface_classes"].append("outer_reference_surface")
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

INPUT_DRIFT_JSON="${TMP_ROOT}/input-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${INPUT_DRIFT_REPO}" \
  --json-only >"${INPUT_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway-input drift"
  exit 1
fi

python3 - <<'PY' "${INPUT_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "admissible_nonorigin_surface_classes_mismatch" and row.get("gateway_class") == "constitution"
    for row in payload["admissibility_violations"]
), payload
PY

TERMINAL_DRIFT_REPO="${TMP_ROOT}/terminal-drift-repo"
mirror_repo "${TERMINAL_DRIFT_REPO}"
python3 - <<'PY' "${TERMINAL_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_profiles"]:
    if row["gateway_class"] == "constitution":
        row["current_turn_legality_terminal"] = True
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

TERMINAL_DRIFT_JSON="${TMP_ROOT}/terminal-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${TERMINAL_DRIFT_REPO}" \
  --json-only >"${TERMINAL_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed current-turn terminal drift"
  exit 1
fi

python3 - <<'PY' "${TERMINAL_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "current_turn_legality_terminal_mismatch" and row.get("gateway_class") == "constitution"
    for row in payload["admissibility_violations"]
), payload
PY

ORDER_DRIFT_REPO="${TMP_ROOT}/gateway-order-drift-repo"
mirror_repo "${ORDER_DRIFT_REPO}"
python3 - <<'PY' "${ORDER_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["gateway_order"][0]["order"] = 2
doc["gateway_order"][1]["order"] = 1
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ORDER_DRIFT_JSON="${TMP_ROOT}/gateway-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ORDER_DRIFT_REPO}" \
  --json-only >"${ORDER_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway-order drift"
  exit 1
fi

python3 - <<'PY' "${ORDER_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "gateway_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
PY

EFFECT_TARGET_DRIFT_REPO="${TMP_ROOT}/gateway-effect-target-drift-repo"
mirror_repo "${EFFECT_TARGET_DRIFT_REPO}"
python3 - <<'PY' "${EFFECT_TARGET_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_effect_targets"]:
    if row["gateway_class"] == "root_contract":
        row["effect_target_class"] = "machine_registry_directory"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

EFFECT_TARGET_DRIFT_JSON="${TMP_ROOT}/gateway-effect-target-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${EFFECT_TARGET_DRIFT_REPO}" \
  --json-only >"${EFFECT_TARGET_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway-effect-target drift"
  exit 1
fi

python3 - <<'PY' "${EFFECT_TARGET_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "effect_target_class_mismatch" and row.get("gateway_class") == "root_contract"
    for row in payload["admissibility_violations"]
), payload
PY

ANSWER_TARGET_DRIFT_REPO="${TMP_ROOT}/gateway-answer-target-drift-repo"
mirror_repo "${ANSWER_TARGET_DRIFT_REPO}"
python3 - <<'PY' "${ANSWER_TARGET_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_effect_targets"]:
    if row["gateway_class"] == "root_contract":
        row["effect_target_question_class"] = "registry_resolution"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ANSWER_TARGET_DRIFT_JSON="${TMP_ROOT}/gateway-answer-target-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ANSWER_TARGET_DRIFT_REPO}" \
  --json-only >"${ANSWER_TARGET_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway-answer-target drift"
  exit 1
fi

python3 - <<'PY' "${ANSWER_TARGET_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "effect_target_question_class_mismatch" and row.get("gateway_class") == "root_contract"
    for row in payload["admissibility_violations"]
), payload
PY

GATEWAY_SURFACE_REPO="${TMP_ROOT}/gateway-surface-drift-repo"
mirror_repo "${GATEWAY_SURFACE_REPO}"
python3 - <<'PY' "${GATEWAY_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root gateway-admissibility completeness discipline"
next_marker = "\n---\n\n## Root derivation completeness discipline"
old = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
new = "2. expected row-family totals may be summarized informally once gateway output looks green;"
assert section_marker in text, text
assert next_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, after = rest.split(next_marker, 1)
assert old in section_body, section_body
section_body = section_body.replace(old, new, 1)
path.write_text(before + section_marker + section_body + next_marker + after, encoding="utf-8")
PY

GATEWAY_SURFACE_JSON="${TMP_ROOT}/gateway-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${GATEWAY_SURFACE_REPO}" \
  --json-only >"${GATEWAY_SURFACE_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed README gateway completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "missing_gateway_admissibility_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "extra_gateway_admissibility_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_admissibility_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

GATEWAY_SURFACE_ORDER_REPO="${TMP_ROOT}/gateway-surface-order-drift-repo"
mirror_repo "${GATEWAY_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows_in_section \
  "${GATEWAY_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "${GATEWAY_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${GATEWAY_COMPLETENESS_SURFACE_FIRST_PHRASE}" \
  "${GATEWAY_COMPLETENESS_SURFACE_SECOND_PHRASE}"

GATEWAY_SURFACE_ORDER_JSON="${TMP_ROOT}/gateway-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${GATEWAY_SURFACE_ORDER_REPO}" \
  --json-only >"${GATEWAY_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed README gateway completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["gateway_admissibility_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "gateway_admissibility_completeness_surface_phrase_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "gateway_admissibility_completeness_surface_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_admissibility_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

GATEWAY_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/gateway-surface-order-non-contiguous-repo"
mirror_repo "${GATEWAY_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${GATEWAY_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${GATEWAY_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${GATEWAY_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${GATEWAY_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${GATEWAY_COMPLETENESS_SURFACE_FIRST_ORDER}"

GATEWAY_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/gateway-surface-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${GATEWAY_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${GATEWAY_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed README gateway completeness surface non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "gateway_admissibility_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "gateway_admissibility_completeness_surface_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
assert not any(
    row["field"] == "gateway_admissibility_completeness_surface"
    and row["reason"] == "gateway_admissibility_completeness_surface_phrase_order_mismatch"
    for row in payload["admissibility_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_admissibility_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/gateway-completeness-row-order-drift-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
rows = doc["gateway_admissibility_completeness_rows"]
if len(rows) < 2:
    raise SystemExit("expected at least two completeness rows")
rows[1]["order"] = rows[0]["order"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/gateway-completeness-row-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway completeness row order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-002", payload
assert any(
    row["field"] == "gateway_admissibility_completeness_rows"
    and row["reason"] in {
        "gateway_admissibility_completeness_row_order_non_contiguous",
        "gateway_admissibility_completeness_rows_order_non_contiguous",
    }
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "gateway_admissibility_completeness_rows"
    and row["reason"] in {
        "gateway_admissibility_completeness_row_order_mismatch",
        "order_mismatch",
    }
    for row in payload["admissibility_violations"]
), payload
assert payload["gateway_admissibility_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

GATEWAY_BINDING_REPO="${TMP_ROOT}/gateway-binding-drift-repo"
mirror_repo "${GATEWAY_BINDING_REPO}"
python3 - <<'PY' "${GATEWAY_BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These gateway-admissibility-completeness rules must remain bound to canonical gateway-admissibility-completeness rows rather than drifting into soft summary prose."
new = "These gateway completeness rules may be summarized freely once reviewers understand the intent."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

GATEWAY_BINDING_JSON="${TMP_ROOT}/gateway-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${GATEWAY_BINDING_REPO}" \
  --json-only >"${GATEWAY_BINDING_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed README gateway binding drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and "These gateway-admissibility-completeness rules must remain bound to canonical gateway-admissibility-completeness rows rather than drifting into soft summary prose." in row.get("marker", "")
    for row in payload["anchor_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root gateway-admissibility discipline"
new = "## Root gateway admissibility discipline"
assert old in text, text[:1200]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus gateway admissibility probes passed"
