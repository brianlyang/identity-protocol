#!/usr/bin/env zsh

if [[ -n "${BASH_VERSION:-}" ]]; then
  echo "[FAIL] run_native_chat_headstamp_smoke.sh must run under zsh." >&2
  echo "       fix: zsh identity-protocol-local/scripts/run_native_chat_headstamp_smoke.sh ..." >&2
  exit 1
fi

set -euo pipefail

if [[ -n "${ZSH_VERSION:-}" ]]; then
  SOURCE_FILE="${(%):-%N}"
elif [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  SOURCE_FILE="${BASH_SOURCE[0]}"
else
  SOURCE_FILE="$0"
fi

SCRIPT_DIR="$(cd "$(dirname "${SOURCE_FILE}")" && pwd)"
PROTOCOL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${PROTOCOL_ROOT}/scripts/runtime_temp_path_common.sh"
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
      echo "Usage: zsh scripts/run_native_chat_headstamp_smoke.sh [--identity-id ID] [--actor-id ID] [--session-id ID] [--catalog PATH] [--output PATH] [--prompt TEXT]"
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

REPO_CATALOG_PATH="${PROTOCOL_ROOT}/identity/catalog/identities.yaml"

TURN_HEADSTAMP_JSON="$(python3 "${PROTOCOL_ROOT}/scripts/render_identity_response_stamp.py" \
  --identity-id "${IDENTITY_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${REPO_CATALOG_PATH}" \
  --actor-id "${EXPECTED_ACTOR_ID}" \
  --session-id "${EXPECTED_SESSION_ID}" \
  --work-layer protocol \
  --source-layer project \
  --surface native-chat \
  --native-chat-machine-profile mini \
  --json-only)"

python3 - "${TURN_HEADSTAMP_JSON}" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
if str(payload.get("native_chat_surface_status", "")).strip().upper() != "PASS_REQUIRED":
    raise SystemExit(
        json.dumps(
            {
                "status": "FAIL_REQUIRED",
                "reason": "native_chat_turn_headstamp_not_pass_required",
                "payload": payload,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
if not str(payload.get("native_chat_identity_line", "")).strip().startswith("Identity-Context:"):
    raise SystemExit("[FAIL] native_chat_identity_line missing")
if not str(payload.get("native_chat_machine_verification_line", "")).strip().startswith("Machine-Verification:"):
    raise SystemExit("[FAIL] native_chat_machine_verification_line missing")
PY

if [[ -z "${OUTPUT_PATH}" ]]; then
  OUTPUT_ROOT="$(identity_runtime_named_temp_root_sh "native-chat-headstamp-smoke")"
  OUTPUT_PATH="${OUTPUT_ROOT}/native-chat-headstamp-smoke-$(date -u +%Y%m%dT%H%M%SZ).txt"
fi

TURN_BOOTSTRAP_ROOT="$(identity_runtime_named_temp_root_sh "native-chat-headstamp-bootstrap")"
TURN_BOOTSTRAP_PATH="${TURN_BOOTSTRAP_ROOT}/native-chat-headstamp-turn-bootstrap-$(date -u +%Y%m%dT%H%M%SZ).md"
python3 - "${TURN_HEADSTAMP_JSON}" "${PROMPT_TEXT}" "${TURN_BOOTSTRAP_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(sys.argv[1])
base_prompt = str(sys.argv[2] or "").strip()
prompt_path = Path(sys.argv[3]).expanduser().resolve()
line1 = str(payload.get("native_chat_identity_line", "")).strip()
line2 = str(payload.get("native_chat_machine_verification_line", "")).strip()

instructions = [
    "# Native Chat Bootstrap",
    "",
    "This turn already has a machine-attested current-turn tuple.",
    "Begin the reply with the exact two lines below and nothing may precede them.",
    "Then output `VALIDATED` on line 3.",
    "",
    line1,
    line2,
]
if base_prompt and base_prompt.lower() != "do not call any tools. output only the current default native-chat headstamp first two lines, then a third line: validated.":
    instructions.extend(["", "Additional instruction:", base_prompt])
prompt_path.write_text("\n".join(instructions).strip() + "\n", encoding="utf-8")
print(str(prompt_path))
PY

echo "[INFO] identity_id=${IDENTITY_ID}"
echo "[INFO] actor_id=${EXPECTED_ACTOR_ID}"
echo "[INFO] session_id=${EXPECTED_SESSION_ID}"
echo "[INFO] catalog_path=${EXPECTED_CATALOG}"
echo "[INFO] output_path=${OUTPUT_PATH}"
echo "[INFO] turn_bootstrap_path=${TURN_BOOTSTRAP_PATH}"

rm -f "${OUTPUT_PATH}" "${OUTPUT_PATH}.stdout.log" "${OUTPUT_PATH}.stderr.log"

RUNNER_SCRIPT="${OUTPUT_PATH}.codex-launch.zsh"
python3 - "${PROJECT_ROOT}" "${EXPECTED_ACTOR_ID}" "${EXPECTED_SESSION_ID}" "${TURN_BOOTSTRAP_PATH}" "${OUTPUT_PATH}" "${RUNNER_SCRIPT}" <<'PY'
import shlex
import sys
from pathlib import Path

project_root = sys.argv[1]
actor_id = sys.argv[2]
session_id = sys.argv[3]
bootstrap_path = sys.argv[4]
output_path = sys.argv[5]
runner_path = Path(sys.argv[6]).expanduser().resolve()
prompt = "Do not call any tools. Follow the active native-chat bootstrap instructions and output VALIDATED on line 3."
command = " ".join(
    [
        f"CODEX_ACTOR_ID={shlex.quote(actor_id)}",
        f"CODEX_SESSION_ID={shlex.quote(session_id)}",
        f"IDENTITY_SESSION_ID={shlex.quote(session_id)}",
        "OTEL_SDK_DISABLED=true",
        "codex",
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "-c",
        shlex.quote(f'model_instructions_file=\"{bootstrap_path}\"'),
        "-c",
        shlex.quote('trace_exporter="none"'),
        "--output-last-message",
        shlex.quote(output_path),
        shlex.quote(prompt),
    ]
)
runner_path.write_text(
    "\n".join(
        [
            "#!/bin/zsh -l",
            f"cd {shlex.quote(project_root)} || exit 1",
            command,
            "",
        ]
    ),
    encoding="utf-8",
)
PY
chmod +x "${RUNNER_SCRIPT}"

set +e
"${RUNNER_SCRIPT}"
CODEX_RC=$?
set -e

line_count="$(python3 - "${OUTPUT_PATH}" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1]).expanduser().resolve()
text = path.read_text(encoding="utf-8") if path.exists() else ""
print(len(text.splitlines()))
PY
)"

if [[ "${CODEX_RC}" -ne 0 || "${line_count}" -lt 3 ]]; then
  python3 - "${OUTPUT_PATH}" "${CODEX_RC}" "${line_count}" <<'PY'
import json
import sys
from pathlib import Path

output_path = Path(sys.argv[1]).expanduser().resolve()
codex_rc = int(sys.argv[2])
line_count = int(sys.argv[3])
raise SystemExit(
    json.dumps(
        {
            "status": "FAIL_REQUIRED",
            "reason": "codex_exec_failed_or_output_last_message_not_ready",
            "codex_rc": codex_rc,
            "line_count": line_count,
            "output_path": str(output_path),
        },
        ensure_ascii=False,
        indent=2,
    )
)
PY
fi

python3 - "${OUTPUT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

output_path = Path(sys.argv[1]).expanduser().resolve()
print(
    json.dumps(
        {
            "status": "ARTIFACT_READY",
            "output_path": str(output_path),
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
