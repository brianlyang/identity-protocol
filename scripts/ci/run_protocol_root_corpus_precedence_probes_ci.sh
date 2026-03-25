#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-precedence-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_ordering_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_authority_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_question_routing_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_transition_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_gateway_admissibility_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_precedence_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh" "${dst}/scripts/ci/"
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
