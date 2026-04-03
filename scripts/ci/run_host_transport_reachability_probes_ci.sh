#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT_BASE="${RUNNER_TEMP:-${TMPDIR:-${GITHUB_WORKSPACE:-${REPO_ROOT}}/.tmp-runtime}}"
WORK_ROOT="${HOST_TRANSPORT_REACHABILITY_PROBE_WORK_ROOT:-${TMP_ROOT_BASE%/}/identity-host-transport-reachability-probes}"
RESULT_ROOT="${WORK_ROOT}/results"
MANIFEST_PATH="${WORK_ROOT}/manifest.host_transport_reachability.json"
SERVER_STATE_JSON="${WORK_ROOT}/server_state.json"
SERVER_LOG="${WORK_ROOT}/server.log"

mkdir -p "${RESULT_ROOT}"
rm -f "${SERVER_STATE_JSON}" "${SERVER_LOG}"

python3 - <<'PY' "${SERVER_STATE_JSON}" "${SERVER_LOG}" &
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import sys

state_path = Path(sys.argv[1]).resolve()
log_path = Path(sys.argv[2]).resolve()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_response(404)
            self.end_headers()
            return
        body = b"ok\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write((fmt % args) + "\n")


server = HTTPServer(("127.0.0.1", 0), Handler)
state_path.write_text(
    json.dumps({"pid": __import__("os").getpid(), "port": server.server_address[1]}, ensure_ascii=False),
    encoding="utf-8",
)
try:
    server.serve_forever()
finally:
    server.server_close()
PY
SERVER_PID=$!

cleanup() {
  if kill -0 "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in $(seq 1 50); do
  if [ -s "${SERVER_STATE_JSON}" ]; then
    break
  fi
  sleep 0.1
done

if [ ! -s "${SERVER_STATE_JSON}" ]; then
  echo "[FAIL] failed to bootstrap reachability probe server" >&2
  exit 1
fi

PORT="$(python3 - <<'PY' "${SERVER_STATE_JSON}"
from __future__ import annotations

import json
from pathlib import Path
import sys

doc = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(int(doc["port"]))
PY
)"

PASS_URL="http://127.0.0.1:${PORT}/healthz"
FAIL_URL="http://127.0.0.1:${PORT}/healthz"

run_probe() {
  local name="$1"
  shift
  local cmd=("$@")

  local stdout_path="${RESULT_ROOT}/${name}.stdout.json"
  local stderr_path="${RESULT_ROOT}/${name}.stderr.log"
  local meta_path="${RESULT_ROOT}/${name}.meta.json"
  local timestamp_utc
  timestamp_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  local cmd_string
  cmd_string="$(printf '%q ' "${cmd[@]}")"
  cmd_string="${cmd_string% }"

  set +e
  "${cmd[@]}" >"${stdout_path}" 2>"${stderr_path}"
  local rc=$?
  set -e

  if [ ! -s "${stderr_path}" ]; then
    rm -f "${stderr_path}"
  fi

  python3 - <<'PY' "${name}" "${rc}" "${stdout_path}"
from __future__ import annotations

import json
import sys
from pathlib import Path

name = sys.argv[1]
rc = int(sys.argv[2])
doc = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
status = str(doc.get("host_transport_reachability_status", "")).strip().upper()
failure_class = str(doc.get("transport_failure_class", "")).strip()
error_code = str(doc.get("error_code", "")).strip()
stale = [str(item).strip() for item in (doc.get("stale_reasons") or []) if str(item).strip()]

if name == "host_transport_reachability_pass":
    if rc != 0:
        raise SystemExit("host_transport_reachability_pass: expected zero rc")
    if status != "PASS_REQUIRED":
        raise SystemExit("host_transport_reachability_pass: expected PASS_REQUIRED status")
elif name == "host_transport_reachability_connection_refused_blocked":
    if rc == 0:
        raise SystemExit("host_transport_reachability_connection_refused_blocked: expected non-zero rc")
    if status != "FAIL_REQUIRED":
        raise SystemExit("host_transport_reachability_connection_refused_blocked: expected FAIL_REQUIRED status")
    if error_code != "IP-HTR-001":
        raise SystemExit("host_transport_reachability_connection_refused_blocked: error_code mismatch")
    if failure_class not in {"connection_refused", "localhost_socket_unreachable", "transport_unavailable", "connect_timeout"}:
        raise SystemExit("host_transport_reachability_connection_refused_blocked: unexpected failure_class")
    if not any(item.startswith("host_transport_reachability_unavailable:") for item in stale):
        raise SystemExit("host_transport_reachability_connection_refused_blocked: missing stale reason prefix")
else:
    raise SystemExit(f"unknown probe name: {name}")
PY

  python3 - <<'PY' "${name}" "${timestamp_utc}" "${rc}" "${cmd_string}" "${stdout_path}" "${stderr_path}" "${meta_path}"
from __future__ import annotations

import json
from pathlib import Path
import sys

name, timestamp, rc, cmd_string, stdout_path, stderr_path, meta_path = sys.argv[1:]
entry = {
    "probe_name": name,
    "timestamp_utc": timestamp,
    "command": cmd_string,
    "rc": int(rc),
    "stdout_path": stdout_path,
    "stderr_path": stderr_path if Path(stderr_path).exists() else "",
}
Path(meta_path).write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[PASS] {name} (rc={rc})")
PY
}

run_probe host_transport_reachability_pass \
  python3 scripts/validate_host_transport_reachability.py \
    --transport-url "${PASS_URL}" \
    --json-only

cleanup
trap - EXIT

run_probe host_transport_reachability_connection_refused_blocked \
  python3 scripts/validate_host_transport_reachability.py \
    --transport-url "${FAIL_URL}" \
    --timeout-seconds 1 \
    --json-only

python3 - <<'PY' "${RESULT_ROOT}" "${MANIFEST_PATH}"
from __future__ import annotations

import json
from pathlib import Path
import sys

result_root = Path(sys.argv[1]).resolve()
manifest_path = Path(sys.argv[2]).resolve()
entries = []
for meta_path in sorted(result_root.glob("*.meta.json")):
    entries.append(json.loads(meta_path.read_text(encoding="utf-8")))
manifest = {
    "schema_version": "v1",
    "suite": "host_transport_reachability_probes",
    "results": entries,
}
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"[PASS] host transport reachability probe suite wrote manifest: {manifest_path}")
PY
