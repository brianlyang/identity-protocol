#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROTOCOL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [[ "$(basename "${PROTOCOL_ROOT}")" == "identity-protocol-local" ]]; then
  PROJECT_ROOT="$(cd "${PROTOCOL_ROOT}/.." && pwd)"
else
  PROJECT_ROOT="${PROTOCOL_ROOT}"
fi

cd "${PROJECT_ROOT}"

# Sourced helpers inspect positional parameters; clear and restore them so
# smoke-script flags are not misread as runtime-path overrides.
ARGV=("$@")
set --
source "${PROTOCOL_ROOT}/scripts/shell_strict_entry_common.sh"
source "${PROTOCOL_ROOT}/scripts/use_project_identity_runtime.sh" >/dev/null
set -- "${ARGV[@]}"

IDENTITY_ID=""
OUTPUT_PATH=""
EXPECTED_ACTOR_ID=""
EXPECTED_SESSION_ID=""
CATALOG_PATH=""
PROMPT_TEXT="Do not call any tools. Output only the current default native-chat headstamp first two lines, then a third line: VALIDATED."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --identity-id)
      IDENTITY_ID="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    --catalog)
      CATALOG_PATH="${2:-}"
      shift 2
      ;;
    --actor-id)
      EXPECTED_ACTOR_ID="${2:-}"
      shift 2
      ;;
    --session-id)
      EXPECTED_SESSION_ID="${2:-}"
      shift 2
      ;;
    --prompt)
      PROMPT_TEXT="${2:-}"
      shift 2
      ;;
    *)
      echo "[FAIL] unknown argument: $1"
      echo "Usage: bash scripts/run_native_chat_headstamp_smoke.sh [--identity-id ID] [--actor-id ID] [--session-id ID] [--catalog PATH] [--output PATH] [--prompt TEXT]"
      exit 1
      ;;
  esac
done

CATALOG_PATH="$(protocol_shell_entry_resolve_project_catalog "${CATALOG_PATH}")"
EXPECTED_ACTOR_ID="$(protocol_shell_entry_require_actor_id "${EXPECTED_ACTOR_ID}")"
EXPECTED_SESSION_ID="$(protocol_shell_entry_require_session_id "${EXPECTED_SESSION_ID}")"
IDENTITY_ID="$(protocol_shell_entry_resolve_session_primary_identity "${CATALOG_PATH}" "${EXPECTED_ACTOR_ID}" "${EXPECTED_SESSION_ID}" "${IDENTITY_ID}")"

EXPECTED_CATALOG="$(python3 - "${CATALOG_PATH}" <<'PY'
from pathlib import Path
import sys
print(str(Path(sys.argv[1]).expanduser().resolve()))
PY
)"

RESOLVE_JSON="$(python3 "${PROTOCOL_ROOT}/scripts/resolve_identity_context.py" resolve --identity-id "${IDENTITY_ID}")"

python3 - "${EXPECTED_CATALOG}" "${RESOLVE_JSON}" <<'PY'
import json
import sys
from pathlib import Path

expected_catalog = str(Path(sys.argv[1]).expanduser().resolve())
payload = json.loads(sys.argv[2])

catalog_path = str(Path(payload["catalog_path"]).expanduser().resolve())
if catalog_path != expected_catalog:
    raise SystemExit(
        "[FAIL] runtime drift detected: catalog_path=%s expected=%s\n"
        "       fix: source ./scripts/use_local_identity_env.sh" % (catalog_path, expected_catalog)
    )
if str(payload.get("status", "")).strip().lower() != "active":
    raise SystemExit("[FAIL] resolved identity is not active")
if str(payload.get("source_layer", "")).strip() != "project":
    raise SystemExit("[FAIL] native-chat smoke requires project-scoped runtime source")
PY

if [[ -z "${OUTPUT_PATH}" ]]; then
  OUTPUT_PATH="/tmp/native-chat-headstamp-smoke-$(date -u +%Y%m%dT%H%M%SZ).txt"
fi

echo "[INFO] identity_id=${IDENTITY_ID}"
echo "[INFO] actor_id=${EXPECTED_ACTOR_ID}"
echo "[INFO] session_id=${EXPECTED_SESSION_ID}"
echo "[INFO] catalog_path=${EXPECTED_CATALOG}"
echo "[INFO] output_path=${OUTPUT_PATH}"

python3 - "${OUTPUT_PATH}" "${PROMPT_TEXT}" "${EXPECTED_ACTOR_ID}" "${EXPECTED_SESSION_ID}" <<'PY'
import json
import os
import subprocess
import sys
import time
from pathlib import Path

output_path = Path(sys.argv[1]).expanduser().resolve()
prompt_text = sys.argv[2]
actor_id = sys.argv[3].strip()
session_id = sys.argv[4].strip()
stdout_log = Path(f"{output_path}.stdout.log")
stderr_log = Path(f"{output_path}.stderr.log")

for path in (output_path, stdout_log, stderr_log):
    try:
        path.unlink()
    except FileNotFoundError:
        pass

env = os.environ.copy()
env["OTEL_SDK_DISABLED"] = "true"
# Keep the ephemeral smoke run on the same actor/session tuple it already validated.
env["CODEX_ACTOR_ID"] = actor_id
env["CODEX_SESSION_ID"] = session_id
env["IDENTITY_SESSION_ID"] = session_id
cmd = [
    "codex",
    "exec",
    "--ephemeral",
    "--skip-git-repo-check",
    "--output-last-message",
    str(output_path),
    prompt_text,
]

with stdout_log.open("w", encoding="utf-8") as stdout_fp, stderr_log.open("w", encoding="utf-8") as stderr_fp:
    proc = subprocess.Popen(
        cmd,
        cwd=str(Path.cwd()),
        env=env,
        stdout=stdout_fp,
        stderr=stderr_fp,
        text=True,
    )

    deadline = time.time() + 180
    artifact_ready = False
    while time.time() < deadline:
        if output_path.exists():
            text = output_path.read_text(encoding="utf-8")
            if len(text.splitlines()) >= 3:
                artifact_ready = True
                break
        if proc.poll() is not None:
            break
        time.sleep(1)

    if not artifact_ready and output_path.exists():
        text = output_path.read_text(encoding="utf-8")
        artifact_ready = len(text.splitlines()) >= 3

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

if not artifact_ready:
    stdout_tail = stdout_log.read_text(encoding="utf-8")[-2000:] if stdout_log.exists() else ""
    stderr_tail = stderr_log.read_text(encoding="utf-8")[-2000:] if stderr_log.exists() else ""
    raise SystemExit(
        json.dumps(
            {
                "status": "FAIL_REQUIRED",
                "reason": "output_last_message_not_ready",
                "output_path": str(output_path),
                "stdout_log": str(stdout_log),
                "stderr_log": str(stderr_log),
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            },
            ensure_ascii=False,
            indent=2,
        )
    )

print(
    json.dumps(
        {
            "status": "ARTIFACT_READY",
            "output_path": str(output_path),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY

python3 - "${OUTPUT_PATH}" "${IDENTITY_ID}" "${EXPECTED_ACTOR_ID}" <<'PY'
import json
import sys
from pathlib import Path

output_path = Path(sys.argv[1]).expanduser().resolve()
identity_id = sys.argv[2]
actor_id = sys.argv[3]
lines = output_path.read_text(encoding="utf-8").splitlines()

if len(lines) < 3:
    raise SystemExit("[FAIL] smoke output must contain at least 3 lines")

line1 = lines[0].strip()
line2 = lines[1].strip()

if not line1.startswith("Identity-Context:"):
    raise SystemExit("[FAIL] line 1 must start with Identity-Context:")
if line1.startswith("Display-Headstamp:"):
    raise SystemExit("[FAIL] native-chat line 1 must not start with Display-Headstamp:")
if f"actor_id={actor_id}" not in line1:
    raise SystemExit("[FAIL] line 1 actor_id does not match expected runtime actor")
if f"identity_id={identity_id}" not in line1:
    raise SystemExit("[FAIL] line 1 identity_id does not match resolved runtime identity")
if "Layer-Context:" not in line1:
    raise SystemExit("[FAIL] line 1 must include Layer-Context")

if not line2.startswith("Machine-Verification:"):
    raise SystemExit("[FAIL] line 2 must start with Machine-Verification:")
if f"identity_id={identity_id}" not in line2:
    raise SystemExit("[FAIL] line 2 identity_id does not match resolved runtime identity")
if "prompt_version=" not in line2:
    raise SystemExit("[FAIL] line 2 must include prompt_version")
if "source_layer=" not in line2:
    raise SystemExit("[FAIL] line 2 must include source_layer")

print(json.dumps({
    "status": "PASS_REQUIRED",
    "identity_id": identity_id,
    "line_1": line1,
    "line_2": line2,
    "output_path": str(output_path),
}, ensure_ascii=False, indent=2))
PY

echo "[PASS] native-chat headstamp smoke validated"
