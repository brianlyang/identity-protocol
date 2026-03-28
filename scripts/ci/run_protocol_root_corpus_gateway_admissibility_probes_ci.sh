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
assert payload["gateway_admissibility_row_family_count"] == 3, payload
assert payload["gateway_admissibility_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["gateway_admissibility_row_identity_projection_status"] == "PASS_REQUIRED", payload
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
