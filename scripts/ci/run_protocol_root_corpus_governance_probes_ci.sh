#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-corpus-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_row_family_projection_common.py"
  "scripts/validate_protocol_root_corpus_governance.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh"
)

mirror_repo() {
  local dst="$1"
  probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROBE_REL_PATHS[@]}"
}


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_family_count"] == 3, payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["registered_top_level_count"] == payload["actual_top_level_count"], payload
assert "root_contract" in payload["corpus_class_profile_ids"], payload
assert "business_domain_example" in payload["forbidden_content_class_ids"], payload
PY

PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${PROFILE_REPO}"
python3 - <<'PY' "${PROFILE_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["corpus_class_profiles"] = [
    row for row in doc["corpus_class_profiles"]
    if row.get("corpus_class") != "root_contract"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${PROFILE_REPO}" \
  --json-only >"${PROFILE_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after removing corpus-class profile row"
  exit 1
fi

python3 - <<'PY' "${PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "corpus_class_profiles" and row["reason"] == "missing_expected_corpus_classes" and "root_contract" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "corpus_class_profiles"
)
assert profile_row["expected_count"] == 5, payload
assert profile_row["actual_count"] == 4, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

FORBIDDEN_REPO="${TMP_ROOT}/forbidden-class-identity-repo"
mirror_repo "${FORBIDDEN_REPO}"
python3 - <<'PY' "${FORBIDDEN_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["forbidden_content_classes"]:
    if row.get("class_id") == "business_domain_example":
        row["class_id"] = "business_domain_example_alias"
        break
else:
    raise SystemExit("expected business_domain_example row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FORBIDDEN_JSON="${TMP_ROOT}/forbidden-class-identity.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${FORBIDDEN_REPO}" \
  --json-only >"${FORBIDDEN_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed forbidden-content-class identity drift"
  exit 1
fi

python3 - <<'PY' "${FORBIDDEN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "forbidden_content_classes" and row["reason"] == "missing_expected_class_ids" and "business_domain_example" in row.get("class_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "forbidden_content_classes" and row["reason"] == "extra_unreferenced_class_ids" and "business_domain_example_alias" in row.get("class_ids", [])
    for row in payload["structure_violations"]
), payload
forbidden_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "forbidden_content_classes"
)
assert forbidden_row["expected_count"] == 3, payload
assert forbidden_row["actual_count"] == 3, payload
assert forbidden_row["missing_ids"] == ["business_domain_example"], payload
assert forbidden_row["unexpected_ids"] == ["business_domain_example_alias"], payload
assert forbidden_row["coverage_status"] == "PASS_REQUIRED", payload
assert forbidden_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

MARKER_REPO="${TMP_ROOT}/missing-marker-repo"
mirror_repo "${MARKER_REPO}"
python3 - <<'PY' "${MARKER_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root maintenance guardrails"
new = "## Root maintenance lane guardrails"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

MARKER_JSON="${TMP_ROOT}/missing-marker.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${MARKER_REPO}" \
  --json-only >"${MARKER_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed after required marker removal"
  exit 1
fi

python3 - <<'PY' "${MARKER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any("README.md:required_marker_missing" in reason for reason in payload["stale_reasons"]), payload
PY

EXTRA_REPO="${TMP_ROOT}/extra-entry-repo"
mirror_repo "${EXTRA_REPO}"
printf 'temporary closure note\n' > "${EXTRA_REPO}/identity/protocol/TEMP_CLOSURE_NOTE.md"

EXTRA_JSON="${TMP_ROOT}/extra-entry.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${EXTRA_REPO}" \
  --json-only >"${EXTRA_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with unregistered top-level entry"
  exit 1
fi

python3 - <<'PY' "${EXTRA_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "registered_top_level_entries" and row["reason"] == "extra_root_entries" and "identity/protocol/TEMP_CLOSURE_NOTE.md" in row.get("rel_paths", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_top_level_entries"
)
assert "identity/protocol/TEMP_CLOSURE_NOTE.md" in entry_row["unexpected_ids"], payload
assert entry_row["coverage_status"] == "FAIL_REQUIRED", payload
assert entry_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

WORKBOOK_REPO="${TMP_ROOT}/workbook-pollution-repo"
mirror_repo "${WORKBOOK_REPO}"
cat >> "${WORKBOOK_REPO}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md" <<'TXT'

### ISSUE-999
- `status`: OPEN
TXT

WORKBOOK_JSON="${TMP_ROOT}/workbook-pollution.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${WORKBOOK_REPO}" \
  --json-only >"${WORKBOOK_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with workbook issue pollution"
  exit 1
fi

python3 - <<'PY' "${WORKBOOK_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-003", payload
assert any(hit["class_id"] == "workbook_issue_projection" for hit in payload["forbidden_content_hits"]), payload
PY

BUSINESS_REPO="${TMP_ROOT}/business-pollution-repo"
mirror_repo "${BUSINESS_REPO}"
cat >> "${BUSINESS_REPO}/identity/protocol/AGENT_HANDOFF_CONTRACT.md" <<'TXT'

Example: WeChat Shop store manager routing note.
TXT

BUSINESS_JSON="${TMP_ROOT}/business-pollution.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${BUSINESS_REPO}" \
  --json-only >"${BUSINESS_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with business-domain example pollution"
  exit 1
fi

python3 - <<'PY' "${BUSINESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-003", payload
assert any(hit["class_id"] == "business_domain_example" for hit in payload["forbidden_content_hits"]), payload
PY

ROOT_CONTRACT_REPO="${TMP_ROOT}/root-contract-profile-repo"
mirror_repo "${ROOT_CONTRACT_REPO}"
python3 - <<'PY' "${ROOT_CONTRACT_REPO}/identity/protocol/IDENTITY_DISCOVERY.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime adjudication boundary"
new = "## Runtime resolution boundary"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ROOT_CONTRACT_JSON="${TMP_ROOT}/root-contract-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${ROOT_CONTRACT_REPO}" \
  --json-only >"${ROOT_CONTRACT_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed after root-contract class marker drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    "IDENTITY_DISCOVERY.md:required_marker_missing:## Runtime adjudication boundary" in reason
    for reason in payload["stale_reasons"]
), payload
PY

echo "[PASS] protocol root-corpus governance probes passed"
