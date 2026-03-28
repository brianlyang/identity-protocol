#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-authority-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/validate_protocol_root_corpus_authority.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 18, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_family_count"] == 2, payload
assert payload["authority_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["root_index_entry"] == "identity/protocol/README.md", payload
assert any(row["corpus_class"] == "bottom_theory" and row["philosophical_primacy"] for row in payload["authority_class_profiles"]), payload
PY

MISSING_CLASS_REPO="${TMP_ROOT}/missing-class-repo"
mirror_repo "${MISSING_CLASS_REPO}"
python3 - <<'PY' "${MISSING_CLASS_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["authority_class_profiles"] = [
    row for row in doc["authority_class_profiles"]
    if row.get("corpus_class") != "demoted_support_directory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_CLASS_JSON="${TMP_ROOT}/missing-class.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${MISSING_CLASS_REPO}" \
  --json-only >"${MISSING_CLASS_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed after removing authority class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_CLASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["authority_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_authority_projection"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 7, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == [], payload
assert class_row["coverage_status"] == "FAIL_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["authority_class_profiles"]:
    if row.get("corpus_class") == "demoted_support_directory":
        row["corpus_class"] = "demoted_support_directory_alias"
        break
else:
    raise SystemExit("expected demoted_support_directory row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["authority_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "extra_unregistered_classes" and "demoted_support_directory_alias" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_authority_projection"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 8, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == ["demoted_support_directory_alias"], payload
assert class_row["coverage_status"] == "PASS_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

PRIMACY_REPO="${TMP_ROOT}/primacy-drift-repo"
mirror_repo "${PRIMACY_REPO}"
python3 - <<'PY' "${PRIMACY_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["authority_class_profiles"]:
    if row.get("corpus_class") == "bottom_theory":
        row["philosophical_primacy"] = False
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PRIMACY_JSON="${TMP_ROOT}/primacy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${PRIMACY_REPO}" \
  --json-only >"${PRIMACY_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed primacy drift"
  exit 1
fi

python3 - <<'PY' "${PRIMACY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any("authority_violation:authority_class_profiles:philosophical_primacy_mismatch" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_INDEX_REPO="${TMP_ROOT}/root-index-drift-repo"
mirror_repo "${ROOT_INDEX_REPO}"
python3 - <<'PY' "${ROOT_INDEX_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_authority_projection"][0]["authority_mode"] = "frozen_law_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_INDEX_JSON="${TMP_ROOT}/root-index-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT_INDEX_REPO}" \
  --json-only >"${ROOT_INDEX_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed root index authority-mode drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_INDEX_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any("authority_violation:entry_authority_projection:root_index_entry_wrong_mode" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_ROLE_REPO="${TMP_ROOT}/root-role-drift-repo"
mirror_repo "${ROOT_ROLE_REPO}"
python3 - <<'PY' "${ROOT_ROLE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_authority_projection"][0]["authority_role"] = "constitutional_protocol_law"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_ROLE_JSON="${TMP_ROOT}/root-role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT_ROLE_REPO}" \
  --json-only >"${ROOT_ROLE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed root index authority-role drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_ROLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "authority_violation:entry_authority_projection:entry_authority_role_mismatch",
        "authority_violation:entry_authority_projection:root_index_entry_wrong_role",
    )
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Authority layering"
new = "## Authority topology layering"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any("anchor_violation:identity/protocol/README.md:required_marker_missing" == reason for reason in payload["stale_reasons"]), payload
PY

CASE_REPO="${TMP_ROOT}/case-normalization-repo"
mirror_repo "${CASE_REPO}"
python3 - <<'PY' "${CASE_REPO}/identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces such as:"
new = "current-turn prompt legality must still resolve from machine-consumed enforcement surfaces such as:"
assert old in text, text[:600]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

CASE_JSON="${TMP_ROOT}/case-normalization.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${CASE_REPO}" \
  --json-only >"${CASE_JSON}"

python3 - <<'PY' "${CASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "PASS_REQUIRED", payload
assert payload["error_code"] == "", payload
PY

echo "[PASS] protocol root-corpus authority probes passed"
