#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export TMPDIR="${TMPDIR:-$ROOT/.tmp}"
mkdir -p "$TMPDIR"

python3 scripts/validate_workbook_truth_sync.py --json-only >/dev/null

TMP_WORKBOOK="$(mktemp "$TMPDIR/workbook_truth_sync_probe.XXXXXX.md")"
cleanup() {
  rm -f "$TMP_WORKBOOK"
}
trap cleanup EXIT

python3 - "$ROOT/docs/workbook/protocol-deep-audit-workbook-v1.6.md" "$TMP_WORKBOOK" <<'PY'
from pathlib import Path
import re
import sys
source = Path(sys.argv[1]).read_text()
pattern = r"(### ISSUE-040 .*?\n\n- `status`: )CLOSED"
mutated, count = re.subn(pattern, r"\1OPEN", source, count=1, flags=re.DOTALL)
if count != 1:
    raise SystemExit('failed to mutate ISSUE-040 status for negative probe')
Path(sys.argv[2]).write_text(mutated)
PY

if python3 scripts/validate_workbook_truth_sync.py --json-only --workbook-path "$TMP_WORKBOOK" >/dev/null 2>&1; then
  echo '{"ok":false,"status":"FAIL_REQUIRED","first_mismatch":"NEGATIVE_PROBE_UNEXPECTED_PASS"}'
  exit 1
fi

echo '{"ok":true,"status":"PASS","negative_probe":"ISSUE_040_STATUS_OPEN_REJECTED"}'
