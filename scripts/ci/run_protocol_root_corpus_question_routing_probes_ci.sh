#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-question-routing-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_gateway_admissibility_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/validate_protocol_root_corpus_question_routing.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh"
)

mirror_repo() {
  local dst="$1"
  probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROBE_REL_PATHS[@]}"
}


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 18, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["adjudication_redirect"]["question_class"] == "current_turn_legality", payload
assert payload["question_routing_row_family_count"] == 3, payload
assert payload["question_routing_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(
    "current_turn_legality" not in row["question_classes"]
    for row in payload["entry_question_projection"]
), payload
assert {row["gateway_class"]: row["question_class"] for row in payload["gateway_question_projection"]} == {
    "constitution": "frozen_protocol_law",
    "runtime_constitution": "frozen_runtime_law",
    "root_contract": "frozen_domain_contract_law",
    "machine_registry_directory": "registry_resolution",
}, payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["question_class_profiles"] = [
    row for row in doc["question_class_profiles"]
    if row.get("question_class") != "support_material_lookup"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed after removing question-class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert payload["question_routing_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "missing_expected_question_classes" and "support_material_lookup" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_question_projection"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_question_projection"
)
assert profile_row["expected_count"] == 9, payload
assert profile_row["actual_count"] == 8, payload
assert profile_row["missing_ids"] == ["support_material_lookup"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_DRIFT_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_DRIFT_REPO}"
python3 - <<'PY' "${IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["question_class_profiles"]:
    if row.get("question_class") == "support_material_lookup":
        row["question_class"] = "support_material_lookup_alias"
        break
else:
    raise SystemExit("expected support_material_lookup row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_DRIFT_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${IDENTITY_DRIFT_REPO}" \
  --json-only >"${IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed question-class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert payload["question_routing_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "missing_expected_question_classes" and "support_material_lookup" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "extra_question_classes" and "support_material_lookup_alias" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_question_projection"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_question_projection"
)
assert profile_row["expected_count"] == 9, payload
assert profile_row["actual_count"] == 9, payload
assert profile_row["missing_ids"] == ["support_material_lookup"], payload
assert profile_row["unexpected_ids"] == ["support_material_lookup_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

ROOT_ENTRY_REPO="${TMP_ROOT}/root-entry-drift-repo"
mirror_repo "${ROOT_ENTRY_REPO}"
python3 - <<'PY' "${ROOT_ENTRY_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_question_projection"][1]["question_classes"] = ["current_turn_legality"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_ENTRY_JSON="${TMP_ROOT}/root-entry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT_ENTRY_REPO}" \
  --json-only >"${ROOT_ENTRY_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed root-entry legality drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_ENTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "routing_violation:entry_question_projection:current_turn_legality_must_not_bind_to_root_entry",
        "routing_violation:entry_question_projection:entry_question_classes_mismatch",
    )
), payload
PY

REDIRECT_REPO="${TMP_ROOT}/redirect-drift-repo"
mirror_repo "${REDIRECT_REPO}"
python3 - <<'PY' "${REDIRECT_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_redirect"]["terminal_machine_surfaces"] = ["mappings", "validators", "probes", "runtime_state"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REDIRECT_JSON="${TMP_ROOT}/redirect-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${REDIRECT_REPO}" \
  --json-only >"${REDIRECT_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed terminal-surface drift"
  exit 1
fi

python3 - <<'PY' "${REDIRECT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    "routing_violation:adjudication_redirect:terminal_machine_surfaces_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
PY

GATEWAY_QUESTION_REPO="${TMP_ROOT}/gateway-question-drift-repo"
mirror_repo "${GATEWAY_QUESTION_REPO}"
python3 - <<'PY' "${GATEWAY_QUESTION_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_question_projection"]:
    if row["gateway_class"] == "root_contract":
        row["question_class"] = "registry_resolution"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

GATEWAY_QUESTION_JSON="${TMP_ROOT}/gateway-question-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${GATEWAY_QUESTION_REPO}" \
  --json-only >"${GATEWAY_QUESTION_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed gateway-question drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    "routing_violation:gateway_question_projection:question_class_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root question-routing discipline"
new = "## Root question routing discipline"
assert old in text, text[:600]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    "anchor_violation:identity/protocol/README.md:required_marker_missing" == reason
    for reason in payload["stale_reasons"]
), payload
PY

echo "[PASS] protocol root-corpus question-routing probes passed"
