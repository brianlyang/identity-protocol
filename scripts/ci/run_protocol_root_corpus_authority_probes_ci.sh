#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-authority-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_ordering_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_authority_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh" "${dst}/scripts/ci/"
}

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
assert payload["root_index_entry"] == "identity/protocol/README.md", payload
assert any(row["corpus_class"] == "bottom_theory" and row["philosophical_primacy"] for row in payload["authority_class_profiles"]), payload
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
