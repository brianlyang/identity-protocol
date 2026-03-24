#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-corpus-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh" "${dst}/scripts/ci/"
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
assert payload["registered_top_level_count"] == payload["actual_top_level_count"], payload
assert "root_contract" in payload["corpus_class_profile_ids"], payload
assert "business_domain_example" in payload["forbidden_content_class_ids"], payload
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
assert any("unregistered_root_top_level_entry:identity/protocol/TEMP_CLOSURE_NOTE.md" == reason for reason in payload["stale_reasons"]), payload
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
