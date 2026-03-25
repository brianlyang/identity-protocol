#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-law-bundle-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "PASS_REQUIRED", payload
assert payload["component_count"] == 10, payload
assert all(row["component_status"] == "PASS_REQUIRED" for row in payload["component_status_rows"]), payload
assert all(
    all(cell["status"] == "PASS_REQUIRED" for cell in row.get("descriptor_field_rows", []))
    for row in payload["component_status_rows"]
), payload
PY

DESCRIPTOR_REPO="${TMP_ROOT}/descriptor-drift-repo"
mirror_repo "${DESCRIPTOR_REPO}"
python3 - <<'PY' "${DESCRIPTOR_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["common_script"] = "scripts/root_corpus_governance_common.py"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

DESCRIPTOR_JSON="${TMP_ROOT}/descriptor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${DESCRIPTOR_REPO}" \
  --json-only >"${DESCRIPTOR_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed descriptor concordance drift"
  exit 1
fi

python3 - <<'PY' "${DESCRIPTOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "common_script_mismatch"
    for row in payload["bundle_violations"]
), payload
assert any(
    row["component_id"] == "root_corpus_ordering"
    and row["reason"] == "component_descriptor_concordance_failure"
    and row.get("descriptor_field") == "common_script"
    for row in payload["bundle_violations"]
), payload
PY

COMPONENT_REPO="${TMP_ROOT}/component-drift-repo"
mirror_repo "${COMPONENT_REPO}"
python3 - <<'PY' "${COMPONENT_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["component_rows"] = [row for row in doc["component_rows"] if row.get("component_id") != "root_constitutional_spine"]
for idx, row in enumerate(doc["component_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPONENT_JSON="${TMP_ROOT}/component-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${COMPONENT_REPO}" \
  --json-only >"${COMPONENT_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed missing-component drift"
  exit 1
fi

python3 - <<'PY' "${COMPONENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-002", payload
assert any(
    row["reason"] == "missing_expected_components" and "root_constitutional_spine" in row.get("component_ids", [])
    for row in payload["structure_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root-law bundle discipline"
new = "## Root law bundle discipline"
assert old in text, text[:2200]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

STATUS_KEY_REPO="${TMP_ROOT}/status-key-drift-repo"
mirror_repo "${STATUS_KEY_REPO}"
python3 - <<'PY' "${STATUS_KEY_REPO}/identity/protocol/mappings/root-corpus-law-bundle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["component_rows"]:
    if row.get("component_id") == "root_corpus_ordering":
        row["status_key"] = "protocol_root_corpus_ordering_state"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STATUS_KEY_JSON="${TMP_ROOT}/status-key-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_law_bundle.py" \
  --repo-root "${STATUS_KEY_REPO}" \
  --json-only >"${STATUS_KEY_JSON}"; then
  echo "[FAIL] root-corpus law bundle validator unexpectedly passed status-key drift"
  exit 1
fi

python3 - <<'PY' "${STATUS_KEY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_law_bundle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCLB-003", payload
assert any(
    row["component_id"] == "root_corpus_ordering" and row["reason"] == "status_key_mismatch"
    for row in payload["bundle_violations"]
), payload
PY

echo "[PASS] protocol root-corpus law bundle probes passed"
