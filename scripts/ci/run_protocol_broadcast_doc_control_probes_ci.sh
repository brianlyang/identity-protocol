#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-broadcast-doc-control-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci" "${dst}/docs/governance" "${dst}/docs/review"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/governed_subdomain_doc_control_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_broadcast_doc_control.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_broadcast_doc_control_probes_ci.sh" "${dst}/scripts/ci/"
  cp "${ROOT}/docs/governance/identity-broadcast-communication-convergence-governance-v1.6.20.md" "${dst}/docs/governance/"
  cp "${ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6.20-broadcast-communication-convergence.md" "${dst}/docs/review/"
  cp "${ROOT}/scripts/validate_identity_broadcast_delivery.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/run_identity_broadcast_delivery.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/check_identity_broadcast_migration_closure.py" "${dst}/scripts/"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_broadcast_doc_control.py" --repo-root "${ROOT}" --json-only >"${PASS_JSON}"
python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_broadcast_doc_control_status"] == "PASS_REQUIRED", payload
assert payload["subdomain_id"] == "broadcast", payload
PY

TOKEN_REPO="${TMP_ROOT}/missing-token-repo"
mirror_repo "${TOKEN_REPO}"
python3 - <<'PY' "${TOKEN_REPO}/identity/protocol/broadcast/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime adjudication boundary"
new = "## Runtime delivery boundary"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
TOKEN_JSON="${TMP_ROOT}/missing-token.json"
if python3 "${ROOT}/scripts/validate_protocol_broadcast_doc_control.py" --repo-root "${TOKEN_REPO}" --json-only >"${TOKEN_JSON}"; then
  echo "[FAIL] broadcast doc-control validator unexpectedly passed after required-token drift"
  exit 1
fi
python3 - <<'PY' "${TOKEN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_broadcast_doc_control_status"] == "FAIL_REQUIRED", payload
assert any(
    reason == "root_readme_missing_required_token:Runtime adjudication boundary"
    for reason in payload["stale_reasons"]
), payload
PY

FILE_REPO="${TMP_ROOT}/missing-file-repo"
mirror_repo "${FILE_REPO}"
rm -f "${FILE_REPO}/identity/protocol/broadcast/schema/broadcast-item.v1.json"
FILE_JSON="${TMP_ROOT}/missing-file.json"
if python3 "${ROOT}/scripts/validate_protocol_broadcast_doc_control.py" --repo-root "${FILE_REPO}" --json-only >"${FILE_JSON}"; then
  echo "[FAIL] broadcast doc-control validator unexpectedly passed after required-file drift"
  exit 1
fi
python3 - <<'PY' "${FILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_broadcast_doc_control_status"] == "FAIL_REQUIRED", payload
assert any(
    reason == "required_file_missing:identity/protocol/broadcast/schema/broadcast-item.v1.json"
    for reason in payload["stale_reasons"]
), payload
PY

echo "[PASS] protocol broadcast doc-control probes passed"
