#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-precedence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/root_corpus_gateway_admissibility_common.py"
  "scripts/root_corpus_precedence_common.py"
  "scripts/validate_protocol_root_corpus_precedence.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh"
)

mirror_repo() {
  local dst="$1"
  probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROBE_REL_PATHS[@]}"
}


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_family_count"] == 2, payload
assert payload["precedence_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["conflict_class"] == "current_turn_legality_conflict"
    and row["resolution_mode"] == "machine_enforcement_terminal"
    for row in payload["precedence_profiles"]
), payload
assert {row["gateway_class"]: row["preserved_question_class"] for row in payload["gateway_authorship_projection"]} == {
    "constitution": "frozen_protocol_law",
    "runtime_constitution": "frozen_runtime_law",
    "root_contract": "frozen_domain_contract_law",
    "machine_registry_directory": "registry_resolution",
}, payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["precedence_profiles"] = [
    row for row in doc["precedence_profiles"]
    if row.get("conflict_class") != "demotion_status_conflict"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed after removing precedence profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert payload["precedence_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "missing_conflict_classes" and "demotion_status_conflict" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "precedence_profiles"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_authorship_projection"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 3, payload
assert profile_row["missing_ids"] == ["demotion_status_conflict"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row.get("conflict_class") == "demotion_status_conflict":
        row["conflict_class"] = "demotion_status_conflict_alias"
        break
else:
    raise SystemExit("expected demotion_status_conflict row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed precedence-profile identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert payload["precedence_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "missing_conflict_classes" and "demotion_status_conflict" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "extra_conflict_classes" and "demotion_status_conflict_alias" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "precedence_profiles"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_authorship_projection"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 4, payload
assert profile_row["missing_ids"] == ["demotion_status_conflict"], payload
assert profile_row["unexpected_ids"] == ["demotion_status_conflict_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

LEGality_DRIFT_REPO="${TMP_ROOT}/legality-drift-repo"
mirror_repo "${LEGality_DRIFT_REPO}"
python3 - <<'PY' "${LEGality_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row["conflict_class"] == "current_turn_legality_conflict":
        row["semantic_precedence_chain"] = ["constitution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

LEGality_DRIFT_JSON="${TMP_ROOT}/legality-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${LEGality_DRIFT_REPO}" \
  --json-only >"${LEGality_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed legality precedence drift"
  exit 1
fi

python3 - <<'PY' "${LEGality_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "semantic_precedence_chain_mismatch"
    and row.get("conflict_class") == "current_turn_legality_conflict"
    for row in payload["precedence_violations"]
), payload
PY

AUTHORSHIP_DRIFT_REPO="${TMP_ROOT}/authorship-drift-repo"
mirror_repo "${AUTHORSHIP_DRIFT_REPO}"
python3 - <<'PY' "${AUTHORSHIP_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row["conflict_class"] == "gateway_authorship_conflict":
        row["forbidden_override_surface_classes"] = ["bottom_theory"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

AUTHORSHIP_DRIFT_JSON="${TMP_ROOT}/authorship-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${AUTHORSHIP_DRIFT_REPO}" \
  --json-only >"${AUTHORSHIP_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed gateway authorship drift"
  exit 1
fi

python3 - <<'PY' "${AUTHORSHIP_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "forbidden_override_surface_classes_mismatch"
    and row.get("conflict_class") == "gateway_authorship_conflict"
    for row in payload["precedence_violations"]
), payload
PY

GATEWAY_PROJECTION_DRIFT_REPO="${TMP_ROOT}/gateway-projection-drift-repo"
mirror_repo "${GATEWAY_PROJECTION_DRIFT_REPO}"
python3 - <<'PY' "${GATEWAY_PROJECTION_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_authorship_projection"]:
    if row["gateway_class"] == "root_contract":
        row["preserved_question_class"] = "registry_resolution"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

GATEWAY_PROJECTION_DRIFT_JSON="${TMP_ROOT}/gateway-projection-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${GATEWAY_PROJECTION_DRIFT_REPO}" \
  --json-only >"${GATEWAY_PROJECTION_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed gateway projection drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_PROJECTION_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "preserved_question_class_mismatch" and row.get("gateway_class") == "root_contract"
    for row in payload["precedence_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root conflict-precedence discipline"
new = "## Root conflict precedence discipline"
assert old in text, text[:1500]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus precedence probes passed"
