#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-transition-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_derivation_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/root_row_family_projection_common.py"
  "scripts/validate_protocol_root_corpus_transition.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh"
)

mirror_repo() {
  local dst="$1"
  probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROBE_REL_PATHS[@]}"
}


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "PASS_REQUIRED", payload
assert payload["current_turn_allowed_root_surface"] == "machine_registry_directory", payload
assert payload["transition_row_family_count"] == 3, payload
assert payload["transition_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["surface_class_profile_count"] == 16, payload
assert payload["direct_root_target_edge_count"] == 14, payload
assert payload["strengthening_gateway_edge_count"] == 40, payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["surface_class_profiles"] = [
    row for row in doc["surface_class_profiles"]
    if row.get("surface_class") != "root_contract"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed after removing root-contract surface profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["transition_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "missing_expected_surface_classes" and "root_contract" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "surface_class_profiles"
)
edge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "direct_root_target_edges"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "strengthening_gateway_edges"
)
assert profile_row["expected_count"] == 16, payload
assert profile_row["actual_count"] == 15, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert edge_row["expected_count"] == 14, payload
assert edge_row["actual_count"] == 12, payload
assert edge_row["missing_ids"] == [
    "root_contract->governed_subdomain_extension",
    "root_contract->machine_registry_directory",
], payload
assert edge_row["unexpected_ids"] == [], payload
assert edge_row["coverage_status"] == "FAIL_REQUIRED", payload
assert edge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_DRIFT_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_DRIFT_REPO}"
python3 - <<'PY' "${IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row.get("surface_class") == "root_contract":
        row["surface_class"] = "root_contract_alias"
        break
else:
    raise SystemExit("expected root_contract row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_DRIFT_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${IDENTITY_DRIFT_REPO}" \
  --json-only >"${IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed surface-class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["transition_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "missing_expected_surface_classes" and "root_contract" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "extra_surface_classes" and "root_contract_alias" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "surface_class_profiles"
)
edge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "direct_root_target_edges"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "strengthening_gateway_edges"
)
assert profile_row["expected_count"] == 16, payload
assert profile_row["actual_count"] == 16, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == ["root_contract_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert edge_row["expected_count"] == 14, payload
assert edge_row["actual_count"] == 14, payload
assert edge_row["missing_ids"] == [
    "root_contract->governed_subdomain_extension",
    "root_contract->machine_registry_directory",
], payload
assert edge_row["unexpected_ids"] == [
    "root_contract_alias->governed_subdomain_extension",
    "root_contract_alias->machine_registry_directory",
], payload
assert edge_row["coverage_status"] == "PASS_REQUIRED", payload
assert edge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

OUTER_PROMOTION_REPO="${TMP_ROOT}/outer-promotion-drift-repo"
mirror_repo "${OUTER_PROMOTION_REPO}"
python3 - <<'PY' "${OUTER_PROMOTION_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row["surface_class"] == "outer_review_surface":
        row["direct_root_targets"] = ["root_contract"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

OUTER_PROMOTION_JSON="${TMP_ROOT}/outer-promotion-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${OUTER_PROMOTION_REPO}" \
  --json-only >"${OUTER_PROMOTION_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed outer direct-promotion drift"
  exit 1
fi

python3 - <<'PY' "${OUTER_PROMOTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    row["reason"] in {"outer_surface_must_not_directly_promote_root_law", "direct_root_targets_mismatch"}
    and row.get("surface_class") == "outer_review_surface"
    for row in payload["transition_violations"]
), payload
PY

CURRENT_TURN_REPO="${TMP_ROOT}/current-turn-drift-repo"
mirror_repo "${CURRENT_TURN_REPO}"
python3 - <<'PY' "${CURRENT_TURN_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row["surface_class"] == "root_index":
        row["direct_current_turn_legality_allowed"] = True
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

CURRENT_TURN_JSON="${TMP_ROOT}/current-turn-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${CURRENT_TURN_REPO}" \
  --json-only >"${CURRENT_TURN_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed current-turn legality drift"
  exit 1
fi

python3 - <<'PY' "${CURRENT_TURN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    row["reason"] in {"current_turn_allowed_surface_set_mismatch", "direct_current_turn_legality_mismatch"}
    for row in payload["transition_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root promotion-demotion discipline"
new = "## Root promotion demotion discipline"
assert old in text, text[:900]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus transition probes passed"
