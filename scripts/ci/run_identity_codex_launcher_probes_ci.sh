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
NEGATIVE_ACTOR_ID="assistant:codex-launcher-negative-probe"
export CODEX_HOME
export IDENTITY_HOME
export IDENTITY_PROTOCOL_HOME="${REPO_ROOT}"
export IDENTITY_CATALOG="${CATALOG_PATH}"

SESSION_ID="$(python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, str(Path("${REPO_ROOT}/scripts").resolve()))
from actor_session_common import resolve_bound_session_id_for_identity  # type: ignore

session_id, _source = resolve_bound_session_id_for_identity(
    Path("${CATALOG_PATH}").resolve(),
    "assistant:codex",
    "${IDENTITY_ID}",
)
if not session_id:
    raise SystemExit("missing authoritative bound session id for launcher probe identity")
print(session_id)
PY
)"
INVALID_SESSION_ID="run:identity-codex-launcher-invalid-${HOST_THREAD_UUID}"
ALT_CATALOG_DIR="${TMP_ROOT}/alt-catalog"
mkdir -p "${ALT_CATALOG_DIR}"
ALT_CATALOG_PATH="${ALT_CATALOG_DIR}/catalog.local.yaml"
cp "${CATALOG_PATH}" "${ALT_CATALOG_PATH}"

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
NO_SESSION_COMMANDS_JSON="${TMP_ROOT}/launcher-commands-no-session.json"
INVALID_SESSION_COMMANDS_JSON="${TMP_ROOT}/launcher-commands-invalid-session.json"
MISMATCH_COMMANDS_JSON="${TMP_ROOT}/launcher-commands-catalog-mismatch.json"
SHORTCUT_COMMANDS_JSON="${TMP_ROOT}/shortcut-launcher-commands.json"
SHORTCUT_MISMATCH_COMMANDS_JSON="${TMP_ROOT}/shortcut-launcher-commands-env-mismatch.json"
NEGATIVE_DRY_RUN_JSON="${TMP_ROOT}/launcher-dry-run-no-session.json"
INVALID_SESSION_DRY_RUN_JSON="${TMP_ROOT}/launcher-dry-run-invalid-session.json"
SHORTCUT_MISMATCH_DRY_RUN_JSON="${TMP_ROOT}/shortcut-launcher-dry-run-env-mismatch.json"

echo "[RUN] ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --thread-id <thread-uuid> --session-id <session-id> --json-only"
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${SESSION_ID}" \
  --json-only > "${COMMANDS_JSON}"

python3 - "${COMMANDS_JSON}" "${HOST_THREAD_UUID}" "${SESSION_ID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
host_thread_uuid = sys.argv[2]
session_id = sys.argv[3]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["command_bundle_contract_id"] == "identity_codex_launcher_command_discovery_contract_v1", payload
assert payload["question_family"] == "identity_launcher_start_resume", payload
assert payload["catalog_context_status"] == "PASS_REQUIRED", payload
assert payload["catalog_context_reason"] == "ambient_catalog_matches_resolved_catalog", payload
assert payload["catalog_explicit_flag_required"] is False, payload
assert payload["resume_status"] == "PASS_REQUIRED", payload
assert payload["host_thread_id_status"] == "PASS_REQUIRED", payload
assert payload["host_thread_id_present"] is True, payload
assert payload["current_host_thread_id"] == host_thread_uuid, payload
assert payload["identity_session_tuple_status"] == "PASS_REQUIRED", payload
assert payload["identity_session_tuple_reason"] == "explicit_session_id", payload
assert payload["resolved_resume_session_id"] == session_id, payload
assert payload["resolved_resume_session_source"] == "explicit_session_id", payload
assert payload["resume_command_fresh_shell_executable_status"] == "PASS_REQUIRED", payload
continuity = payload["continuity_support"]
assert continuity["bundle_contract_id"] == "identity_context_continuity_bundle_v1", payload
assert continuity["bundle_role"] == "launcher_and_instance_internal_support", payload
assert continuity["operator_surface_contract"]["new_user_facing_continuity_command_family_forbidden"] is True, payload
mode = continuity["recommended_launcher_bind_mode"]
if mode == "fresh_start_without_continuity_contract":
    assert continuity["startup_reentry_readiness_status"] == "SKIPPED_NOT_REQUIRED", payload
    assert continuity["live_reentry_consumption_proof_status"] == "SKIPPED_NOT_REQUIRED", payload
    assert continuity["continuity_contract_required"] is False, payload
    assert continuity["reentry_contract_required"] is False, payload
elif mode == "consume_governed_reentry_brief":
    assert continuity["startup_reentry_readiness_status"] == "PASS_REQUIRED", payload
    assert continuity["live_reentry_consumption_proof_status"] in {"FAIL_REQUIRED", "PASS_REQUIRED"}, payload
    assert continuity["receipt_family_observation_status"] in {"FAIL_REQUIRED", "PASS_REQUIRED"}, payload
    assert continuity["continuity_contract_required"] is True, payload
    assert continuity["reentry_contract_required"] is True, payload
else:
    raise AssertionError(payload)
assert payload["shortcut_command_on_path"] is False, payload
assert payload["generic_command_on_path"] is False, payload
assert payload["preferred_start_command"] == f"id-{payload['identity_id']}", payload
assert payload["preferred_resume_command"] == f"id-{payload['identity_id']} resume {host_thread_uuid}", payload
assert payload["absolute_start_command"].endswith(f"/id-{payload['identity_id']}"), payload
assert payload["generic_start_command"] == f"identity-codex --identity-id {payload['identity_id']}", payload
assert payload["fresh_shell_start_command"] == payload["generic_start_command"], payload
assert payload["absolute_fresh_shell_start_command"] == payload["absolute_generic_start_command"], payload
assert payload["generic_resume_command"] == (
    f"identity-codex --identity-id {payload['identity_id']} -- resume {host_thread_uuid}"
), payload
assert payload["fresh_shell_resume_command"] == (
    f"identity-codex --identity-id {payload['identity_id']} --session-id {session_id} -- resume {host_thread_uuid}"
), payload
assert payload["recommended_start_command"] == payload["absolute_start_command"], payload
assert payload["recommended_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["recommended_resume_command"].endswith(f"resume {host_thread_uuid}"), payload
assert payload["recommended_user_command"] == payload["recommended_resume_command"], payload
assert payload["copyable_commands"]["start"]["preferred"] == payload["preferred_start_command"], payload
assert payload["copyable_commands"]["start"]["recommended"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["resume"]["thread_id"] == host_thread_uuid, payload
assert payload["copyable_commands"]["resume"]["session_id"] == session_id, payload
assert payload["copyable_commands"]["resume"]["session_source"] == "explicit_session_id", payload
assert payload["copyable_commands"]["resume"]["recommended"] == payload["recommended_resume_command"], payload
assert payload["instance_answer_guidance"]["manual_command_assembly_forbidden"] is True, payload
print("launcher_command_bundle_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --catalog ${ALT_CATALOG_PATH} --thread-id <thread-uuid> --session-id <session-id> --json-only (mismatch: canonical primary surface + no stale preferred shortcut leakage)"
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${ALT_CATALOG_PATH}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${SESSION_ID}" \
  --json-only > "${MISMATCH_COMMANDS_JSON}"

python3 - "${MISMATCH_COMMANDS_JSON}" "${HOST_THREAD_UUID}" "${SESSION_ID}" "${ALT_CATALOG_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
host_thread_uuid = sys.argv[2]
_session_id = sys.argv[3]
alt_catalog_path = str(Path(sys.argv[4]).resolve())
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["catalog_path"] == alt_catalog_path, payload
assert payload["catalog_context_status"] == "FAIL_REQUIRED", payload
assert payload["catalog_context_reason"] == "ambient_catalog_mismatch_requires_explicit_catalog", payload
assert payload["catalog_explicit_flag_required"] is True, payload
assert payload["host_thread_id_status"] == "PASS_REQUIRED", payload
assert payload["preferred_start_surface_reason"] == "catalog_mismatch_requires_canonical_primary_surface", payload
assert payload["preferred_start_command"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["start"]["preferred"] == payload["preferred_start_command"], payload
assert payload["copyable_commands"]["start"]["recommended"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["start"]["shortcut"] == f"id-{payload['identity_id']}", payload
assert payload["preferred_start_command"] != payload["copyable_commands"]["start"]["shortcut"], payload
assert f"--catalog {alt_catalog_path}" in payload["preferred_start_command"], payload
assert payload["identity_session_tuple_status"] == "FAIL_REQUIRED", payload
assert payload["resume_command_fresh_shell_executable_status"] == "FAIL_REQUIRED", payload
assert payload["preferred_resume_surface_reason"] == "catalog_mismatch_resume_surface_unavailable", payload
assert payload["preferred_resume_command"] == payload["recommended_resume_command"], payload
assert payload["copyable_commands"]["resume"]["preferred"] == payload["preferred_resume_command"], payload
assert payload["copyable_commands"]["resume"]["recommended"] == payload["recommended_resume_command"], payload
assert payload["copyable_commands"]["resume"]["shortcut"] == f"id-{payload['identity_id']} resume {host_thread_uuid}", payload
assert payload["preferred_resume_command"] == "", payload
assert payload["preferred_resume_command"] != payload["copyable_commands"]["resume"]["shortcut"], payload
assert payload["recommended_user_command"] == payload["recommended_start_command"], payload
print("launcher_command_bundle_catalog_mismatch_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --thread-id <thread-uuid> --actor-id ${NEGATIVE_ACTOR_ID} --json-only (negative: unresolved session tuple)"
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --actor-id "${NEGATIVE_ACTOR_ID}" \
  --json-only > "${NO_SESSION_COMMANDS_JSON}"

python3 - "${NO_SESSION_COMMANDS_JSON}" "${HOST_THREAD_UUID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
host_thread_uuid = sys.argv[2]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["host_thread_id_status"] == "PASS_REQUIRED", payload
assert payload["host_thread_id_present"] is True, payload
assert payload["current_host_thread_id"] == host_thread_uuid, payload
assert payload["identity_session_tuple_status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["identity_session_tuple_reason"], payload
assert payload["resume_command_fresh_shell_executable_status"] == "FAIL_REQUIRED", payload
assert payload["resume_status"] == "FAIL_REQUIRED", payload
assert payload["recommended_resume_command"] == "", payload
assert payload["recommended_user_command"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["resume"]["session_id"] == "", payload
assert payload["copyable_commands"]["resume"]["recommended"] == "", payload
assert payload["resume_reason"] == payload["identity_session_tuple_reason"], payload
print("launcher_command_bundle_negative_session_gate_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --thread-id <thread-uuid> --session-id <invalid-session-id> --json-only (negative: non-authoritative explicit session tuple)"
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${INVALID_SESSION_ID}" \
  --json-only > "${INVALID_SESSION_COMMANDS_JSON}"

python3 - "${INVALID_SESSION_COMMANDS_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["identity_session_tuple_status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["identity_session_tuple_reason"], payload
assert payload["resume_command_fresh_shell_executable_status"] == "FAIL_REQUIRED", payload
assert payload["resume_status"] == "FAIL_REQUIRED", payload
assert payload["recommended_resume_command"] == "", payload
assert payload["copyable_commands"]["resume"]["session_id"] == "", payload
assert payload["copyable_commands"]["resume"]["recommended"] == "", payload
assert payload["resume_reason"] == payload["identity_session_tuple_reason"], payload
print("launcher_command_bundle_invalid_explicit_session_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/id-${IDENTITY_ID} commands --thread-id <thread-uuid> --session-id <session-id> --json-only"
"${BIN_DIR}/id-${IDENTITY_ID}" \
  commands \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${SESSION_ID}" \
  --json-only > "${SHORTCUT_COMMANDS_JSON}"

python3 - "${SHORTCUT_COMMANDS_JSON}" "${SESSION_ID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
session_id = sys.argv[2]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["identity_id"], payload
assert payload["command_discovery"]["instance_answer_mode"] == "instance_returns_concrete_commands", payload
assert payload["continuity_support"]["bundle_contract_id"] == "identity_context_continuity_bundle_v1", payload
assert payload["shortcut_command_on_path"] is False, payload
assert payload["identity_session_tuple_status"] == "PASS_REQUIRED", payload
assert payload["resolved_resume_session_id"] == session_id, payload
assert payload["preferred_start_command"] == f"id-{payload['identity_id']}", payload
assert payload["preferred_resume_command"].startswith(f"id-{payload['identity_id']} resume "), payload
assert payload["recommended_start_command"] == payload["absolute_start_command"], payload
assert payload["recommended_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["recommended_resume_command"].endswith(payload["current_host_thread_id"]), payload
assert payload["copyable_commands"]["resume"]["session_id"] == session_id, payload
assert payload["instance_answer_guidance"]["continuity_support_internal_only"] is True, payload
print("launcher_shortcut_command_bundle_status=PASS_REQUIRED")
PY

echo "[RUN] IDENTITY_CATALOG=${ALT_CATALOG_PATH} ${BIN_DIR}/id-${IDENTITY_ID} commands --thread-id <thread-uuid> --session-id <session-id> --json-only (positive: shortcut stays bound to install catalog under env mismatch)"
IDENTITY_CATALOG="${ALT_CATALOG_PATH}" \
"${BIN_DIR}/id-${IDENTITY_ID}" \
  commands \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${SESSION_ID}" \
  --json-only > "${SHORTCUT_MISMATCH_COMMANDS_JSON}"

python3 - "${SHORTCUT_MISMATCH_COMMANDS_JSON}" "${SESSION_ID}" "${CATALOG_PATH}" "${ALT_CATALOG_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
session_id = sys.argv[2]
catalog_path = str(Path(sys.argv[3]).resolve())
ambient_catalog_path = str(Path(sys.argv[4]).resolve())
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["catalog_path"] == catalog_path, payload
assert payload["ambient_catalog_path"] == ambient_catalog_path, payload
assert payload["catalog_context_status"] == "FAIL_REQUIRED", payload
assert payload["catalog_context_reason"] == "ambient_catalog_mismatch_requires_explicit_catalog", payload
assert payload["identity_session_tuple_status"] == "PASS_REQUIRED", payload
assert payload["resolved_resume_session_id"] == session_id, payload
assert payload["preferred_start_command"] == payload["recommended_start_command"], payload
assert payload["preferred_resume_command"] == payload["recommended_resume_command"], payload
assert payload["copyable_commands"]["start"]["shortcut"] == f"id-{payload['identity_id']}", payload
assert payload["copyable_commands"]["resume"]["shortcut"] == (
    f"id-{payload['identity_id']} resume {payload['current_host_thread_id']}"
), payload
assert payload["preferred_start_command"] != payload["copyable_commands"]["start"]["shortcut"], payload
assert payload["preferred_resume_command"] != payload["copyable_commands"]["resume"]["shortcut"], payload
assert f"--catalog {catalog_path}" in payload["preferred_start_command"], payload
assert f"--catalog {catalog_path}" in payload["preferred_resume_command"], payload
print("launcher_shortcut_catalog_binding_commands_status=PASS_REQUIRED")
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

echo "[RUN] ${BIN_DIR}/identity-codex --identity-id ${IDENTITY_ID} --actor-id ${NEGATIVE_ACTOR_ID} --dry-run --json-only -- resume <thread-uuid> (negative: unresolved session tuple)"
if "${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --actor-id "${NEGATIVE_ACTOR_ID}" \
  --dry-run \
  --json-only \
  -- \
  resume "${HOST_THREAD_UUID}" > "${NEGATIVE_DRY_RUN_JSON}"; then
  echo "[FAIL] launcher missing-session dry-run unexpectedly passed"
  exit 1
fi

python3 - "${NEGATIVE_DRY_RUN_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["error"], payload
print("launcher_dry_run_missing_session_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex --identity-id ${IDENTITY_ID} --session-id <invalid-session-id> --dry-run --json-only -- resume <thread-uuid> (negative: non-authoritative explicit session tuple)"
if "${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --session-id "${INVALID_SESSION_ID}" \
  --dry-run \
  --json-only \
  -- \
  resume "${HOST_THREAD_UUID}" > "${INVALID_SESSION_DRY_RUN_JSON}"; then
  echo "[FAIL] launcher invalid-session dry-run unexpectedly passed"
  exit 1
fi

python3 - "${INVALID_SESSION_DRY_RUN_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["error"], payload
print("launcher_dry_run_invalid_session_status=PASS_REQUIRED")
PY

echo "[RUN] IDENTITY_CATALOG=${ALT_CATALOG_PATH} ${BIN_DIR}/id-${IDENTITY_ID} --dry-run --json-only -- resume <thread-uuid> (positive: shortcut dry-run survives env mismatch)"
IDENTITY_CATALOG="${ALT_CATALOG_PATH}" \
"${BIN_DIR}/id-${IDENTITY_ID}" \
  --dry-run \
  --json-only \
  -- \
  resume "${HOST_THREAD_UUID}" > "${SHORTCUT_MISMATCH_DRY_RUN_JSON}"

python3 - "${SHORTCUT_MISMATCH_DRY_RUN_JSON}" "${CATALOG_PATH}" "${SESSION_ID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
catalog_path = str(Path(sys.argv[2]).resolve())
session_id = sys.argv[3]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["catalog_path"] == catalog_path, payload
assert payload["session_id"] == session_id, payload
assert payload["session_source"] in {"actor_binding_identity", "explicit_session_id"}, payload
command = payload.get("command") or []
assert command[-2:] and command[-2] == "resume", payload
print("launcher_shortcut_catalog_binding_dry_run_status=PASS_REQUIRED")
PY

echo "[RUN] ${BIN_DIR}/identity-codex --identity-id ${IDENTITY_ID} --session-id <session-id> --dry-run --json-only -- resume <thread-uuid>"
"${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --session-id "${SESSION_ID}" \
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
