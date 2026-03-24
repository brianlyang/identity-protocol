#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-gateway-admissibility-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_authority_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_question_routing_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_transition_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_gateway_admissibility_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh" "${dst}/scripts/ci/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "PASS_REQUIRED", payload
assert payload["current_turn_terminal_gateway"] == "machine_registry_directory", payload
PY

INPUT_DRIFT_REPO="${TMP_ROOT}/input-drift-repo"
mirror_repo "${INPUT_DRIFT_REPO}"
python3 - <<'PY' "${INPUT_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_profiles"]:
    if row["gateway_class"] == "constitution":
        row["admissible_nonorigin_surface_classes"].append("outer_reference_surface")
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

INPUT_DRIFT_JSON="${TMP_ROOT}/input-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${INPUT_DRIFT_REPO}" \
  --json-only >"${INPUT_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed gateway-input drift"
  exit 1
fi

python3 - <<'PY' "${INPUT_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "admissible_nonorigin_surface_classes_mismatch" and row.get("gateway_class") == "constitution"
    for row in payload["admissibility_violations"]
), payload
PY

TERMINAL_DRIFT_REPO="${TMP_ROOT}/terminal-drift-repo"
mirror_repo "${TERMINAL_DRIFT_REPO}"
python3 - <<'PY' "${TERMINAL_DRIFT_REPO}/identity/protocol/mappings/root-corpus-gateway-admissibility.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_profiles"]:
    if row["gateway_class"] == "constitution":
        row["current_turn_legality_terminal"] = True
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

TERMINAL_DRIFT_JSON="${TMP_ROOT}/terminal-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${TERMINAL_DRIFT_REPO}" \
  --json-only >"${TERMINAL_DRIFT_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed current-turn terminal drift"
  exit 1
fi

python3 - <<'PY' "${TERMINAL_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["reason"] == "current_turn_legality_terminal_mismatch" and row.get("gateway_class") == "constitution"
    for row in payload["admissibility_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root gateway-admissibility discipline"
new = "## Root gateway admissibility discipline"
assert old in text, text[:1200]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_gateway_admissibility.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] gateway admissibility validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_gateway_admissibility_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RGA-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus gateway admissibility probes passed"
