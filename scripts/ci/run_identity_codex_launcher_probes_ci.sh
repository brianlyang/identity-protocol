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
HOST_THREAD_UUID="$(python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
)"
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
COMMANDS_JSON="${TMP_ROOT}/launcher-commands.json"
SHORTCUT_COMMANDS_JSON="${TMP_ROOT}/shortcut-launcher-commands.json"

echo "[RUN] ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --thread-id <thread-uuid> --json-only"
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --json-only > "${COMMANDS_JSON}"

python3 - "${COMMANDS_JSON}" "${HOST_THREAD_UUID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
host_thread_uuid = sys.argv[2]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["command_bundle_contract_id"] == "identity_codex_launcher_command_discovery_contract_v1", payload
assert payload["question_family"] == "identity_launcher_start_resume", payload
assert payload["resume_status"] == "PASS_REQUIRED", payload
assert payload["recommended_user_command"] == payload["preferred_resume_command"], payload
assert payload["preferred_start_command"].startswith("zsh -lic 'id-"), payload
assert f" resume {host_thread_uuid}'" in payload["preferred_resume_command"], payload
assert payload["absolute_start_command"].endswith(f"/id-{payload['identity_id']}"), payload
assert payload["copyable_commands"]["start"]["preferred"] == payload["preferred_start_command"], payload
assert payload["copyable_commands"]["resume"]["thread_id"] == host_thread_uuid, payload
assert payload["instance_answer_guidance"]["manual_command_assembly_forbidden"] is True, payload
print("launcher_command_bundle_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/id-${IDENTITY_ID} commands --thread-id <thread-uuid> --json-only"
"${BIN_DIR}/id-${IDENTITY_ID}" \
  commands \
  --thread-id "${HOST_THREAD_UUID}" \
  --json-only > "${SHORTCUT_COMMANDS_JSON}"

python3 - "${SHORTCUT_COMMANDS_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["identity_id"], payload
assert payload["command_discovery"]["instance_answer_mode"] == "instance_returns_concrete_commands", payload
assert payload["preferred_start_command"].startswith("zsh -lic 'id-"), payload
assert payload["preferred_resume_command"].startswith("zsh -lic 'id-"), payload
print("launcher_shortcut_command_bundle_status=PASS_REQUIRED")
PY

python3 - "${REPO_ROOT}" <<'PY'
import re
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
uuid_re = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
targets = [
    repo_root / "README.md",
    repo_root / "scripts" / "render_identity_codex_launcher.py",
    repo_root / "scripts" / "identity_codex_launcher_common.py",
    repo_root / "scripts" / "ci" / "run_identity_codex_launcher_probes_ci.sh",
    repo_root / "docs" / "governance" / "identity-codex-launcher-governance-v1.6.14.md",
    repo_root / "docs" / "review" / "protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
]
violations = []
for path in targets:
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        if uuid_re.search(line):
            violations.append(f"{path}:{lineno}:{line.strip()}")
if violations:
    raise SystemExit("launcher_uuid_literal_regression:\n" + "\n".join(violations))
print("launcher_uuid_literal_guard_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex --identity-id ${IDENTITY_ID} --dry-run --json-only -- resume <thread-uuid>"
"${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --dry-run \
  --json-only \
  -- \
  resume "${HOST_THREAD_UUID}" > "${DRY_RUN_JSON}"

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
