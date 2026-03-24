#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-derivation-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_ordering_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_authority_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_question_routing_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_derivation_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh" "${dst}/scripts/ci/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "PASS_REQUIRED", payload
assert payload["permitted_current_turn_root_corpus_class"] == "machine_registry_directory", payload
PY

SUPPORT_REPO="${TMP_ROOT}/support-parent-drift-repo"
mirror_repo "${SUPPORT_REPO}"
python3 - <<'PY' "${SUPPORT_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_class_profiles"]:
    if row["corpus_class"] == "root_contract":
        row["allowed_upstream_classes"].append("demoted_support_directory")
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUPPORT_JSON="${TMP_ROOT}/support-parent-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${SUPPORT_REPO}" \
  --json-only >"${SUPPORT_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed demoted-support parent drift"
  exit 1
fi

python3 - <<'PY' "${SUPPORT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert any(
    row["reason"] in {"law_bearing_class_must_not_derive_from_demoted_support", "allowed_upstream_classes_mismatch"}
    and row.get("corpus_class") == "root_contract"
    for row in payload["derivation_violations"]
), payload
PY

QUESTION_REPO="${TMP_ROOT}/question-routing-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_redirect"]["forbidden_root_corpus_classes"] = [
    item for item in doc["adjudication_redirect"]["forbidden_root_corpus_classes"]
    if item != "bottom_theory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed adjudication forbidden-class drift"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert any(
    row["reason"] == "current_turn_forbidden_root_classes_mismatch"
    for row in payload["derivation_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## One-way derivation discipline"
new = "## One way derivation discipline"
assert old in text, text[:800]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus derivation probes passed"
