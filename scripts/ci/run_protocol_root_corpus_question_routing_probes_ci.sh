#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-question-routing-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_ordering_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_authority_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_question_routing_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh" "${dst}/scripts/ci/"
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
assert payload["adjudication_redirect"]["question_class"] == "current_turn_legality", payload
assert all(
    "current_turn_legality" not in row["question_classes"]
    for row in payload["entry_question_projection"]
), payload
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
assert any(
    "anchor_violation:identity/protocol/README.md:required_marker_missing" == reason
    for reason in payload["stale_reasons"]
), payload
PY

echo "[PASS] protocol root-corpus question-routing probes passed"
