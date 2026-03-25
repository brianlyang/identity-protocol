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

strip_path_entry() {
  local raw_path="${1:-}"
  local target_entry="${2:-}"
  PATH="${raw_path}" python3 - "${target_entry}" <<'PY'
import os
import sys

target = os.path.realpath(sys.argv[1]) if sys.argv[1] else ""
seen: list[str] = []
for raw in os.environ.get("PATH", "").split(":"):
    token = str(raw or "").strip()
    if not token:
        continue
    try:
        resolved = os.path.realpath(token)
    except Exception:
        resolved = token
    if target and resolved == target:
        continue
    if token not in seen:
        seen.append(token)
print(":".join(seen))
PY
}

assert_env_loader_path_probe() {
  local label="${1:?label required}"
  local log_path="${2:?log_path required}"
  local expected_bin="${3:?expected_bin required}"
  local expected_cmd="${4:-}"
  python3 - "${label}" "${log_path}" "${expected_bin}" "${expected_cmd}" <<'PY'
import os
import sys
from pathlib import Path

label = sys.argv[1]
log_path = Path(sys.argv[2])
expected_bin = os.path.realpath(sys.argv[3])
expected_cmd = str(sys.argv[4] or "").strip()

rows = {}
for raw in log_path.read_text(encoding="utf-8").splitlines():
    if "=" not in raw:
        continue
    key, value = raw.split("=", 1)
    rows[key.strip()] = value.strip()

path1 = rows.get("PATH", "")
path2 = rows.get("PATH2", "")
assert path1, f"{label}: missing PATH"
assert path2, f"{label}: missing PATH2"

def count_entry(path_value: str, target: str) -> int:
    count = 0
    for token in path_value.split(":"):
        item = str(token or "").strip()
        if not item:
            continue
        try:
            resolved = os.path.realpath(item)
        except Exception:
            resolved = item
        if resolved == target:
            count += 1
    return count

assert count_entry(path1, expected_bin) == 1, (label, path1, expected_bin)
assert count_entry(path2, expected_bin) == 1, (label, path2, expected_bin)
assert path1 == path2, (label, path1, path2)

if expected_cmd:
    resolved_cmd = rows.get("CMD", "")
    assert os.path.realpath(resolved_cmd) == os.path.realpath(expected_cmd), (
        label,
        resolved_cmd,
        expected_cmd,
    )

print(f"{label}_env_loader_path_status=PASS_REQUIRED")
PY
}

echo "[INFO] launcher probe temp root: ${TMP_ROOT}"

PROJECT_CODEX_BIN="$(python3 - <<'PY'
from pathlib import Path
print((Path.home() / ".codex" / "bin").resolve())
PY
)"
BASE_PATH_WITHOUT_PROJECT_CODEX_BIN="$(strip_path_entry "${PATH}" "${PROJECT_CODEX_BIN}")"
PROJECT_ENV_LOG="${TMP_ROOT}/project-env-loader-path.log"

echo "[RUN] fresh-shell project runtime env loader exposes ${PROJECT_CODEX_BIN} on PATH exactly once"
env -i HOME="${HOME}" PATH="${BASE_PATH_WITHOUT_PROJECT_CODEX_BIN}" /bin/bash --noprofile --norc -lc '
  set -euo pipefail
  source "'"${REPO_ROOT}"'/scripts/use_project_identity_runtime.sh" "'"${TMP_ROOT}/project-runtime-home"'" "'"${REPO_ROOT}"'" >/dev/null
  printf "PATH=%s\n" "${PATH}"
  printf "CMD=%s\n" "$(command -v identity-codex)"
  source "'"${REPO_ROOT}"'/scripts/use_project_identity_runtime.sh" "'"${TMP_ROOT}/project-runtime-home"'" "'"${REPO_ROOT}"'" >/dev/null
  printf "PATH2=%s\n" "${PATH}"
' > "${PROJECT_ENV_LOG}"

assert_env_loader_path_probe \
  "project_runtime" \
  "${PROJECT_ENV_LOG}" \
  "${PROJECT_CODEX_BIN}" \
  "${PROJECT_CODEX_BIN}/identity-codex"

GLOBAL_CODEX_HOME="${TMP_ROOT}/global-codex-home"
GLOBAL_CODEX_BIN="${GLOBAL_CODEX_HOME}/bin"
BASE_PATH_WITHOUT_GLOBAL_CODEX_BIN="$(strip_path_entry "${PATH}" "${GLOBAL_CODEX_BIN}")"
GLOBAL_ENV_LOG="${TMP_ROOT}/global-env-loader-path.log"

echo "[RUN] fresh-shell global runtime env loader derives PATH from CODEX_HOME without duplication"
env -i HOME="${HOME}" PATH="${BASE_PATH_WITHOUT_GLOBAL_CODEX_BIN}" CODEX_HOME="${GLOBAL_CODEX_HOME}" /bin/bash --noprofile --norc -lc '
  set -euo pipefail
  source "'"${REPO_ROOT}"'/scripts/use_local_identity_env.sh" "'"${GLOBAL_CODEX_HOME}/.identity"'" "'"${REPO_ROOT}"'" >/dev/null
  printf "PATH=%s\n" "${PATH}"
  source "'"${REPO_ROOT}"'/scripts/use_local_identity_env.sh" "'"${GLOBAL_CODEX_HOME}/.identity"'" "'"${REPO_ROOT}"'" >/dev/null
  printf "PATH2=%s\n" "${PATH}"
' > "${GLOBAL_ENV_LOG}"

assert_env_loader_path_probe \
  "global_runtime" \
  "${GLOBAL_ENV_LOG}" \
  "${GLOBAL_CODEX_BIN}" \
  ""

INSTALL_JSON="${TMP_ROOT}/launcher-install.json"
VALIDATE_JSON="${TMP_ROOT}/launcher-validate.json"

echo "[RUN] install launcher assets and capture install-vs-discoverability projection"
python3 "${REPO_ROOT}/scripts/install_identity_codex_launcher.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --bin-dir "${BIN_DIR}" \
  --identity-home "${IDENTITY_HOME}" \
  --protocol-home "${REPO_ROOT}" \
  --json-only > "${INSTALL_JSON}"

python3 - "${INSTALL_JSON}" "${BIN_DIR}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
bin_dir = str(Path(sys.argv[2]).resolve())
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["operator_shell_path_hint"] == bin_dir, payload
assert payload["generic_launcher_install_status"] == "PASS_REQUIRED", payload
assert payload["shortcut_launcher_install_status"] == "PASS_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["shortcut_launcher_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["shortcut_launcher_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["generic_command_on_path"] is False, payload
assert payload["shortcut_command_on_path"] is False, payload
print("launcher_install_projection_status=PASS_REQUIRED")
PY

echo "[RUN] validate launcher assets with separate install/discoverability states"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --bin-dir "${BIN_DIR}" \
  --require-installed \
  --json-only > "${VALIDATE_JSON}"

python3 - "${VALIDATE_JSON}" "${BIN_DIR}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
bin_dir = str(Path(sys.argv[2]).resolve())
assert payload["identity_codex_launcher_status"] == "PASS_REQUIRED", payload
assert payload["installed_launcher_status"] == "PASS_REQUIRED", payload
assert payload["runtime_paths_status"] == "PASS_REQUIRED", payload
assert payload["operator_shell_path_hint"] == bin_dir, payload
assert payload["generic_launcher_install_status"] == "PASS_REQUIRED", payload
assert payload["shortcut_launcher_install_status"] == "PASS_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["shortcut_launcher_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["shortcut_launcher_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["generic_command_on_path"] is False, payload
assert payload["shortcut_command_on_path"] is False, payload
assert payload["stale_reasons"] == [], payload
print("launcher_validator_install_vs_discoverability_status=PASS_REQUIRED")
PY

PROBE_RUNTIME_ROOT="${TMP_ROOT}/probe-runtime"
PROBE_IDENTITY_HOME="${PROBE_RUNTIME_ROOT}/.identity"
PROBE_CATALOG_PATH="${PROBE_IDENTITY_HOME}/catalog.local.yaml"
PROBE_PACK_ROOT="${PROBE_IDENTITY_HOME}/${IDENTITY_ID}"
PROBE_REPAIR_RUNTIME_ROOT="${TMP_ROOT}/probe-runtime-repair"
PROBE_REPAIR_IDENTITY_HOME="${PROBE_REPAIR_RUNTIME_ROOT}/.identity"
PROBE_REPAIR_CATALOG_PATH="${PROBE_REPAIR_IDENTITY_HOME}/catalog.local.yaml"
PROBE_REPAIR_PACK_ROOT="${PROBE_REPAIR_IDENTITY_HOME}/${IDENTITY_ID}"
PROBE_PRE_MIGRATE_JSON="${TMP_ROOT}/launcher-reentry-pre-migrate.json"
PROBE_BUNDLE_BEFORE_JSON="${TMP_ROOT}/launcher-reentry-before.json"
PROBE_EXEC_STDOUT="${TMP_ROOT}/launcher-reentry-exec.out"
PROBE_BUNDLE_AFTER_JSON="${TMP_ROOT}/launcher-reentry-after.json"
PROBE_EXEC_CODEX_HOME="${TMP_ROOT}/launcher-exec-codex-home"
PROBE_REPAIR_PREP_JSON="${TMP_ROOT}/launcher-reentry-repair-prep.json"
PROBE_REPAIR_BUNDLE_BEFORE_JSON="${TMP_ROOT}/launcher-reentry-repair-before.json"
PROBE_REPAIR_EXEC_STDOUT="${TMP_ROOT}/launcher-reentry-repair-exec.out"
PROBE_REPAIR_BUNDLE_AFTER_JSON="${TMP_ROOT}/launcher-reentry-repair-after.json"
PROBE_REPAIR_EXEC_CODEX_HOME="${TMP_ROOT}/launcher-repair-exec-codex-home"
mkdir -p "${PROBE_EXEC_CODEX_HOME}"
mkdir -p "${PROBE_REPAIR_EXEC_CODEX_HOME}"

run_cmd python3 - "${REPO_ROOT}" "${CATALOG_PATH}" "${IDENTITY_ID}" "${PROBE_CATALOG_PATH}" <<'PY'
import json
import shutil
import sys
from pathlib import Path

repo_root = Path(sys.argv[1]).resolve()
source_catalog = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
probe_catalog = Path(sys.argv[4]).resolve()

sys.path.insert(0, str((repo_root / "scripts").resolve()))
from actor_session_common import actor_session_path  # type: ignore

source_pack = (source_catalog.parent / identity_id).resolve()
probe_identity_home = probe_catalog.parent.resolve()
probe_pack = (probe_identity_home / identity_id).resolve()
if probe_pack.exists():
    shutil.rmtree(probe_pack)
probe_pack.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source_pack, probe_pack)

probe_catalog.write_text(
    json.dumps(
        {
            "identities": [
                {
                    "id": identity_id,
                    "pack_path": str(probe_pack),
                    "status": "active",
                    "profile": "runtime",
                    "runtime_mode": "local_only",
                    "scope": "USER",
                }
            ]
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

source_actor_store = actor_session_path(source_catalog, "assistant:codex")
if not source_actor_store.exists():
    raise SystemExit(f"missing_actor_session_store:{source_actor_store}")
probe_actor_store = actor_session_path(probe_catalog, "assistant:codex")
probe_actor_store.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(source_actor_store, probe_actor_store)
PY

cp -R "${PROBE_RUNTIME_ROOT}" "${PROBE_REPAIR_RUNTIME_ROOT}"

DRY_RUN_JSON="${TMP_ROOT}/launcher-dry-run.json"
COMMANDS_JSON="${TMP_ROOT}/launcher-commands.json"
HEALTHY_PATH_COMMANDS_JSON="${TMP_ROOT}/launcher-commands-healthy-path.json"
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
assert payload["surface_governance"]["runtime_summary_surface_governance_status"] == "PASS_REQUIRED", payload
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
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
assert payload["shortcut_install_status"] == "PASS_REQUIRED", payload
assert payload["generic_launcher_install_status"] == "PASS_REQUIRED", payload
assert payload["shortcut_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["shortcut_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["generic_launcher_shell_discoverability_reason"] in {
    "launcher_not_discoverable_in_current_shell",
    "current_shell_resolves_foreign_launcher",
}, payload
assert payload["operator_shell_path_hint"].endswith("/bin"), payload
assert payload["preferred_start_command"] == payload["absolute_start_command"], payload
assert payload["preferred_start_surface_reason"] == "shortcut_shell_undiscoverable_promote_absolute_shortcut_surface", payload
assert payload["preferred_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["preferred_resume_surface_reason"] == "shortcut_shell_undiscoverable_promote_absolute_resume_surface", payload
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
assert payload["recommended_start_command"] == payload["preferred_start_command"], payload
assert payload["recommended_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["recommended_resume_command"] == payload["preferred_resume_command"], payload
assert payload["recommended_resume_command"].endswith(f"resume {host_thread_uuid}"), payload
assert payload["recommended_user_command"] == payload["recommended_resume_command"], payload
assert payload["copyable_commands"]["start"]["preferred"] == payload["preferred_start_command"], payload
assert payload["copyable_commands"]["start"]["recommended"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["start"]["shortcut"] == f"id-{payload['identity_id']}", payload
assert payload["copyable_commands"]["start"]["preferred"] != payload["copyable_commands"]["start"]["shortcut"], payload
assert payload["copyable_commands"]["resume"]["preferred"] == payload["preferred_resume_command"], payload
assert payload["copyable_commands"]["resume"]["shortcut"] == f"id-{payload['identity_id']} resume {host_thread_uuid}", payload
assert payload["copyable_commands"]["resume"]["preferred"] != payload["copyable_commands"]["resume"]["shortcut"], payload
assert payload["copyable_commands"]["resume"]["thread_id"] == host_thread_uuid, payload
assert payload["copyable_commands"]["resume"]["session_id"] == session_id, payload
assert payload["copyable_commands"]["resume"]["session_source"] == "explicit_session_id", payload
assert payload["copyable_commands"]["resume"]["recommended"] == payload["recommended_resume_command"], payload
assert payload["instance_answer_guidance"]["manual_command_assembly_forbidden"] is True, payload
print("launcher_command_bundle_stripped_path_status=PASS_REQUIRED")
PY

echo "[RUN] PATH=${BIN_DIR}:<base> ${BIN_DIR}/identity-codex commands --identity-id ${IDENTITY_ID} --thread-id <thread-uuid> --session-id <session-id> --json-only (healthy PATH: short launcher preferred)"
PATH="${BIN_DIR}:${PATH}" \
"${BIN_DIR}/identity-codex" \
  commands \
  --identity-id "${IDENTITY_ID}" \
  --thread-id "${HOST_THREAD_UUID}" \
  --session-id "${SESSION_ID}" \
  --json-only > "${HEALTHY_PATH_COMMANDS_JSON}"

python3 - "${HEALTHY_PATH_COMMANDS_JSON}" "${HOST_THREAD_UUID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
host_thread_uuid = sys.argv[2]
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
assert payload["shortcut_command_on_path"] is True, payload
assert payload["generic_command_on_path"] is True, payload
assert payload["shortcut_shell_discoverability_status"] == "PASS_REQUIRED", payload
assert payload["generic_launcher_shell_discoverability_status"] == "PASS_REQUIRED", payload
assert payload["preferred_start_command"] == f"id-{payload['identity_id']}", payload
assert payload["preferred_start_surface_reason"] == "shortcut_shell_discoverable_primary_surface", payload
assert payload["preferred_resume_command"] == f"id-{payload['identity_id']} resume {host_thread_uuid}", payload
assert payload["preferred_resume_surface_reason"] == "shortcut_shell_discoverable_primary_surface", payload
assert payload["recommended_start_command"] == payload["preferred_start_command"], payload
assert payload["recommended_resume_command"] != payload["preferred_resume_command"], payload
assert payload["recommended_resume_command"] == payload["fresh_shell_resume_command"], payload
assert payload["copyable_commands"]["start"]["preferred"] == payload["preferred_start_command"], payload
assert payload["copyable_commands"]["resume"]["preferred"] == payload["preferred_resume_command"], payload
print("launcher_command_bundle_healthy_path_status=PASS_REQUIRED")
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
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
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
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
assert payload["host_thread_id_status"] == "PASS_REQUIRED", payload
assert payload["host_thread_id_present"] is True, payload
assert payload["current_host_thread_id"] == host_thread_uuid, payload
assert payload["identity_session_tuple_status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["identity_session_tuple_reason"], payload
assert payload["resume_command_fresh_shell_executable_status"] == "FAIL_REQUIRED", payload
assert payload["resume_status"] == "FAIL_REQUIRED", payload
assert payload["preferred_resume_command"] == "", payload
assert payload["preferred_resume_surface_reason"] == "resume_surface_unavailable_without_authoritative_session_tuple", payload
assert payload["recommended_resume_command"] == "", payload
assert payload["recommended_user_command"] == payload["recommended_start_command"], payload
assert payload["copyable_commands"]["resume"]["session_id"] == "", payload
assert payload["copyable_commands"]["resume"]["preferred"] == "", payload
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
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
assert payload["identity_session_tuple_status"] == "FAIL_REQUIRED", payload
assert "current-turn session tuple unresolved" in payload["identity_session_tuple_reason"], payload
assert payload["resume_command_fresh_shell_executable_status"] == "FAIL_REQUIRED", payload
assert payload["resume_status"] == "FAIL_REQUIRED", payload
assert payload["preferred_resume_command"] == "", payload
assert payload["preferred_resume_surface_reason"] == "resume_surface_unavailable_without_authoritative_session_tuple", payload
assert payload["recommended_resume_command"] == "", payload
assert payload["copyable_commands"]["resume"]["session_id"] == "", payload
assert payload["copyable_commands"]["resume"]["preferred"] == "", payload
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
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
assert payload["command_discovery"]["instance_answer_mode"] == "instance_returns_concrete_commands", payload
assert payload["continuity_support"]["bundle_contract_id"] == "identity_context_continuity_bundle_v1", payload
assert payload["shortcut_command_on_path"] is False, payload
assert payload["shortcut_shell_discoverability_status"] == "FAIL_REQUIRED", payload
assert payload["identity_session_tuple_status"] == "PASS_REQUIRED", payload
assert payload["resolved_resume_session_id"] == session_id, payload
assert payload["preferred_start_command"] == payload["absolute_start_command"], payload
assert payload["preferred_start_surface_reason"] == "shortcut_shell_undiscoverable_promote_absolute_shortcut_surface", payload
assert payload["preferred_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["preferred_resume_surface_reason"] == "shortcut_shell_undiscoverable_promote_absolute_resume_surface", payload
assert payload["recommended_start_command"] == payload["preferred_start_command"], payload
assert payload["recommended_resume_command"] == payload["absolute_fresh_shell_resume_command"], payload
assert payload["recommended_resume_command"] == payload["preferred_resume_command"], payload
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
assert payload["surface_governance"]["surface_id"] == "identity_codex_launcher_command_bundle_surface", payload
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
binding = payload["launcher_reentry_binding"]
assert binding["launcher_reentry_binding_status"] == "PASS_REQUIRED", payload
mode = binding["recommended_launcher_bind_mode"]
if mode == "consume_governed_reentry_brief":
    assert binding["bind_action"] == "dry_run_preview_post_recover", payload
    assert binding["bind_reason"] == "launcher_would_consume_governed_reentry_brief", payload
else:
    assert binding["bind_action"] == "skipped_not_required", payload
print("launcher_dry_run_status=PASS_REQUIRED")
PY

echo "[RUN] continuity pre-migrate on isolated probe pack to force pending startup consumption"
"${PROBE_PACK_ROOT}/scripts/run_identity_context_continuity_guard.sh" \
  --catalog "${PROBE_CATALOG_PATH}" \
  pre-migrate \
  --json-only > "${PROBE_PRE_MIGRATE_JSON}"

echo "[RUN] launcher auto-repairs recoverable continuity receipt-family gaps before post-recover"
"${PROBE_REPAIR_PACK_ROOT}/scripts/run_identity_context_continuity_guard.sh" \
  --catalog "${PROBE_REPAIR_CATALOG_PATH}" \
  pre-migrate \
  --json-only > "${PROBE_REPAIR_PREP_JSON}"
rm -f "${PROBE_REPAIR_PACK_ROOT}/runtime/reports/context-continuity/migration-receipt.json"

python3 "${REPO_ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_REPAIR_CATALOG_PATH}" \
  --json-only > "${PROBE_REPAIR_BUNDLE_BEFORE_JSON}"

python3 - "${PROBE_REPAIR_BUNDLE_BEFORE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_context_continuity_bundle_status"] == "PASS_REQUIRED", payload
assert payload["recommended_launcher_bind_mode"] == "consume_governed_reentry_brief", payload
assert payload["startup_reentry_readiness_status"] == "PASS_REQUIRED", payload
assert payload["receipt_family_observation_status"] == "FAIL_REQUIRED", payload
print("launcher_exec_continuity_repair_preflight_status=PASS_REQUIRED")
PY

CODEX_HOME="${PROBE_REPAIR_EXEC_CODEX_HOME}" \
IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
IDENTITY_CATALOG="${PROBE_REPAIR_CATALOG_PATH}" \
"${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_REPAIR_CATALOG_PATH}" \
  --session-id "${SESSION_ID}" \
  -- \
  --version > "${PROBE_REPAIR_EXEC_STDOUT}"

python3 "${REPO_ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_REPAIR_CATALOG_PATH}" \
  --json-only > "${PROBE_REPAIR_BUNDLE_AFTER_JSON}"

python3 - "${PROBE_REPAIR_BUNDLE_AFTER_JSON}" "${PROBE_REPAIR_EXEC_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
stdout = Path(sys.argv[2]).read_text(encoding="utf-8").strip()
assert payload["identity_context_continuity_bundle_status"] == "PASS_REQUIRED", payload
assert payload["startup_reentry_readiness_status"] == "PASS_REQUIRED", payload
assert payload["live_reentry_consumption_proof_status"] == "PASS_REQUIRED", payload
assert payload["receipt_family_observation_status"] == "PASS_REQUIRED", payload
assert stdout, "launcher repair exec did not produce codex output"
print("launcher_exec_continuity_repair_status=PASS_REQUIRED")
PY

echo "[RUN] render continuity bundle before launcher exec (expect startup ready; receipt/live proof may already be green on hydrated source packs)"
python3 "${REPO_ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_CATALOG_PATH}" \
  --json-only > "${PROBE_BUNDLE_BEFORE_JSON}"

python3 - "${PROBE_BUNDLE_BEFORE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["identity_context_continuity_bundle_status"] == "PASS_REQUIRED", payload
assert payload["recommended_launcher_bind_mode"] == "consume_governed_reentry_brief", payload
assert payload["startup_reentry_readiness_status"] == "PASS_REQUIRED", payload
assert payload["receipt_family_observation_status"] in {"FAIL_REQUIRED", "PASS_REQUIRED"}, payload
assert payload["live_reentry_consumption_proof_status"] in {"FAIL_REQUIRED", "PASS_REQUIRED"}, payload
print("launcher_exec_continuity_preflight_status=PASS_REQUIRED")
PY

echo "[RUN] actual launcher exec consumes governed reentry brief before codex startup"
CODEX_HOME="${PROBE_EXEC_CODEX_HOME}" \
IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
IDENTITY_CATALOG="${PROBE_CATALOG_PATH}" \
"${BIN_DIR}/identity-codex" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_CATALOG_PATH}" \
  --session-id "${SESSION_ID}" \
  -- \
  --version > "${PROBE_EXEC_STDOUT}"

echo "[RUN] render continuity bundle after launcher exec (expect live proof green)"
python3 "${REPO_ROOT}/scripts/render_identity_context_continuity_bundle.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${PROBE_CATALOG_PATH}" \
  --json-only > "${PROBE_BUNDLE_AFTER_JSON}"

python3 - "${PROBE_BUNDLE_AFTER_JSON}" "${PROBE_EXEC_STDOUT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
stdout = Path(sys.argv[2]).read_text(encoding="utf-8").strip()
assert payload["identity_context_continuity_bundle_status"] == "PASS_REQUIRED", payload
assert payload["recommended_launcher_bind_mode"] == "consume_governed_reentry_brief", payload
assert payload["startup_reentry_readiness_status"] == "PASS_REQUIRED", payload
assert payload["live_reentry_consumption_proof_status"] == "PASS_REQUIRED", payload
assert payload["receipt_family_observation_status"] == "PASS_REQUIRED", payload
assert stdout, "launcher exec did not produce codex output"
print("launcher_exec_continuity_binding_status=PASS_REQUIRED")
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
