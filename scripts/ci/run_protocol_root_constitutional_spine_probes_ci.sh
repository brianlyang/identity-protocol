#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-constitutional-spine-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}"
  cp -R "${ROOT}/identity" "${dst}/"
  cp -R "${ROOT}/scripts" "${dst}/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "PASS_REQUIRED", payload
assert payload["spine_entry_count"] == 4, payload
assert payload["spine_bridge_count"] == 5, payload
assert payload["constitutional_spine_row_family_count"] == 2, payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert [row["family_id"] for row in payload["row_family_projection_rows"]] == [
    "constitutional_entry_rows",
    "spine_bridge_rows",
], payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["expected_count"] == payload["spine_entry_count"] == 4, payload
assert entry_row["actual_count"] == payload["spine_entry_count"] == 4, payload
assert entry_row["missing_ids"] == [], payload
assert entry_row["unexpected_ids"] == [], payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == payload["spine_bridge_count"] == 5, payload
assert bridge_row["actual_count"] == payload["spine_bridge_count"] == 5, payload
assert bridge_row["missing_ids"] == [], payload
assert bridge_row["unexpected_ids"] == [], payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

BRIDGE_REPO="${TMP_ROOT}/bridge-drift-repo"
mirror_repo "${BRIDGE_REPO}"
python3 - <<'PY' "${BRIDGE_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_spine_bridge_rows"] = [
    row for row in doc["required_spine_bridge_rows"]
    if row.get("bridge_id") != "philosophy_to_runtime_machine_authority_split"
]
for idx, row in enumerate(doc["required_spine_bridge_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

BRIDGE_JSON="${TMP_ROOT}/bridge-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${BRIDGE_REPO}" \
  --json-only >"${BRIDGE_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed missing bridge row"
  exit 1
fi

python3 - <<'PY' "${BRIDGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "philosophy_to_runtime_machine_authority_split" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == 5, payload
assert bridge_row["actual_count"] == 4, payload
assert bridge_row["missing_ids"] == ["philosophy_to_runtime_machine_authority_split"], payload
assert bridge_row["unexpected_ids"] == [], payload
assert bridge_row["coverage_status"] == "FAIL_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ENTRY_IDENTITY_REPO="${TMP_ROOT}/entry-identity-drift-repo"
mirror_repo "${ENTRY_IDENTITY_REPO}"
python3 - <<'PY' "${ENTRY_IDENTITY_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_constitutional_entry_rows"]:
    if row.get("rel_path") == "identity/protocol/IDENTITY_RUNTIME.md":
        row["rel_path"] = "identity/protocol/IDENTITY_RUNTIME_ALIAS.md"
        break
else:
    raise SystemExit("expected runtime constitutional entry row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ENTRY_IDENTITY_JSON="${TMP_ROOT}/entry-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${ENTRY_IDENTITY_REPO}" \
  --json-only >"${ENTRY_IDENTITY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed entry identity drift"
  exit 1
fi

python3 - <<'PY' "${ENTRY_IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_entry_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows"
    and "identity/protocol/IDENTITY_RUNTIME.md" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "unexpected_rows"
    and "identity/protocol/IDENTITY_RUNTIME_ALIAS.md" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["expected_count"] == 4, payload
assert entry_row["actual_count"] == 4, payload
assert entry_row["missing_ids"] == ["identity/protocol/IDENTITY_RUNTIME.md"], payload
assert entry_row["unexpected_ids"] == ["identity/protocol/IDENTITY_RUNTIME_ALIAS.md"], payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

BRIDGE_IDENTITY_REPO="${TMP_ROOT}/bridge-identity-drift-repo"
mirror_repo "${BRIDGE_IDENTITY_REPO}"
python3 - <<'PY' "${BRIDGE_IDENTITY_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_spine_bridge_rows"]:
    if row.get("bridge_id") == "philosophy_to_runtime_machine_authority_split":
        row["bridge_id"] = "philosophy_to_runtime_machine_authority_split_alias"
        break
else:
    raise SystemExit("expected bridge row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

BRIDGE_IDENTITY_JSON="${TMP_ROOT}/bridge-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${BRIDGE_IDENTITY_REPO}" \
  --json-only >"${BRIDGE_IDENTITY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed bridge identity drift"
  exit 1
fi

python3 - <<'PY' "${BRIDGE_IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows"
    and "philosophy_to_runtime_machine_authority_split" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "unexpected_rows"
    and "philosophy_to_runtime_machine_authority_split_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == 5, payload
assert bridge_row["actual_count"] == 5, payload
assert bridge_row["missing_ids"] == ["philosophy_to_runtime_machine_authority_split"], payload
assert bridge_row["unexpected_ids"] == ["philosophy_to_runtime_machine_authority_split_alias"], payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROJECTION_REPO="${TMP_ROOT}/projection-drift-repo"
mirror_repo "${PROJECTION_REPO}"
python3 - <<'PY' "${PROJECTION_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["entry_authority_projection"]:
    if row.get("rel_path") == "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md":
        row["authority_mode"] = "frozen_law_only"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROJECTION_JSON="${TMP_ROOT}/projection-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${PROJECTION_REPO}" \
  --json-only >"${PROJECTION_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed authority projection drift"
  exit 1
fi

python3 - <<'PY' "${PROJECTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "root_corpus_authority" and row["reason"] == "authority_mode_mismatch"
    for row in payload["projection_violations"]
), payload
PY

MARKER_REPO="${TMP_ROOT}/marker-drift-repo"
mirror_repo "${MARKER_REPO}"
python3 - <<'PY' "${MARKER_REPO}/identity/protocol/IDENTITY_RUNTIME.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime consumption of the root-law bundle"
new = "## Runtime consumption of the law bundle"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

MARKER_JSON="${TMP_ROOT}/marker-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${MARKER_REPO}" \
  --json-only >"${MARKER_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed marker drift"
  exit 1
fi

python3 - <<'PY' "${MARKER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "entry_files"
    and row["reason"] == "required_marker_missing"
    and row["rel_path"] == "identity/protocol/IDENTITY_RUNTIME.md"
    and row["marker"] == "## Runtime consumption of the root-law bundle"
    for row in payload["projection_violations"]
), payload
PY

REGISTRY_REPO="${TMP_ROOT}/registry-drift-repo"
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
            if child != "root-constitutional-spine.v1.yaml"
        ]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed registry child drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "root_corpus_registry"
    and row["reason"] == "mappings_required_child_missing"
    and row["child"] == "root-constitutional-spine.v1.yaml"
    for row in payload["projection_violations"]
), payload
PY

echo "[PASS] protocol root constitutional spine probes passed"
