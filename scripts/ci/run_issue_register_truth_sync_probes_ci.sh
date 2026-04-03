#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export TMPDIR="${TMPDIR:-$ROOT/.tmp}"
mkdir -p "$TMPDIR"

python3 scripts/validate_issue_register_truth_sync.py --json-only >/dev/null

TMP_REGISTER="$(mktemp "$TMPDIR/issue_register_truth_sync_probe.XXXXXX.md")"
cleanup() {
  rm -f "$TMP_REGISTER"
}
trap cleanup EXIT

python3 - "$ROOT/docs/workbook/protocol-issue-register-v1.6.md" "$TMP_REGISTER" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text()
target = source.replace(
    "| ISSUE-040 Chat history is being misused as handoff state and lane closure lacks a durable skeleton | CLOSED |",
    "| ISSUE-040 Chat history is being misused as handoff state and lane closure lacks a durable skeleton | OPEN |",
    1,
)
if target == source:
    raise SystemExit("failed to mutate ISSUE-040 status for negative probe")
Path(sys.argv[2]).write_text(target)
PY

if python3 scripts/validate_issue_register_truth_sync.py --json-only --issue-register-path "$TMP_REGISTER" >/dev/null 2>&1; then
  echo '{"ok":false,"status":"FAIL_REQUIRED","first_mismatch":"NEGATIVE_PROBE_UNEXPECTED_PASS"}'
  exit 1
fi

echo '{"ok":true,"status":"PASS","negative_probe":"ISSUE_040_STATUS_OPEN_REJECTED"}'
