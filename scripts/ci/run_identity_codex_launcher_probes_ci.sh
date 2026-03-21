#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

IDENTITY_ID="${IDENTITY_ID:-base-repo-closure-orchestrator}"
CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH:-}")"

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-codex-launcher-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

CODEX_HOME="${TMP_ROOT}/codex-home"
IDENTITY_HOME="${CODEX_HOME}/.identity"
BIN_DIR="${CODEX_HOME}/bin"
export CODEX_HOME
export IDENTITY_HOME
export IDENTITY_PROTOCOL_HOME="${REPO_ROOT}"
export IDENTITY_CATALOG="${CATALOG_PATH}"

run_cmd() {
  echo "[RUN] $*"
  "$@"
}

echo "[INFO] launcher probe temp root: ${TMP_ROOT}"

run_cmd python3 "${REPO_ROOT}/scripts/install_identity_codex_launcher.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --bin-dir "${BIN_DIR}" \
  --identity-home "${IDENTITY_HOME}" \
  --protocol-home "${REPO_ROOT}" \
  --json-only

run_cmd python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --bin-dir "${BIN_DIR}" \
  --require-installed \
  --json-only

DRY_RUN_JSON="${TMP_ROOT}/launcher-dry-run.json"
echo "[RUN] ${BIN_DIR}/identity-codex --identity-id ${IDENTITY_ID} --dry-run --json-only -- resume <thread-uuid>"
"${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --dry-run \
  --json-only \
  -- \
  resume 019cad9b-f10a-7ba0-9d65-77c3946c03ef > "${DRY_RUN_JSON}"

python3 - "${DRY_RUN_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
command = payload.get("command") or []
assert any("model_instructions_file" in part for part in command), payload
assert any("project_doc_fallback_filenames" in part for part in command), payload
assert str(payload.get("line_1", "")).startswith("Identity-Context:"), payload
assert str(payload.get("line_2", "")).startswith("Machine-Verification:"), payload
print("launcher_dry_run_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex forbidden override negative probe"
if "${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --dry-run \
  --json-only \
  -- \
  -c model_instructions_file=/tmp/forbidden.md >/tmp/identity-codex-launcher-forbidden.out 2>&1; then
  echo "[FAIL] launcher forbidden override probe unexpectedly passed"
  exit 1
fi
if ! grep -q "owns model_instructions_file and project_doc_fallback_filenames injection" /tmp/identity-codex-launcher-forbidden.out; then
  echo "[FAIL] launcher forbidden override probe missing expected failure text"
  cat /tmp/identity-codex-launcher-forbidden.out
  exit 1
fi

rm -f "${BIN_DIR}/id-${IDENTITY_ID}"
if python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --bin-dir "${BIN_DIR}" \
  --require-installed \
  --json-only >/tmp/identity-codex-launcher-negative.out 2>&1; then
  echo "[FAIL] launcher missing-shortcut probe unexpectedly passed"
  exit 1
fi
if ! grep -q "shortcut_launcher_missing" /tmp/identity-codex-launcher-negative.out; then
  echo "[FAIL] launcher missing-shortcut probe missing expected stale reason"
  cat /tmp/identity-codex-launcher-negative.out
  exit 1
fi

echo "[PASS] identity codex launcher probes passed"
