#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_BASE="${TMPDIR:-/tmp}"
WORK_DIR="$(mktemp -d "${TMP_BASE%/}/execution-loop-after-mutation-not-closing.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

POSITIVE_JSON="${WORK_DIR}/positive.json"
NEGATIVE_JSON="${WORK_DIR}/negative.json"
NEGATIVE_RESULT_JSON="${WORK_DIR}/negative-result.json"

cd "$REPO_ROOT"

python3 scripts/validate_execution_loop_after_mutation_not_closing.py --json-only > "$POSITIVE_JSON"

python3 - "$POSITIVE_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "PASS_REQUIRED", payload
assert payload["mode"] == "validator", payload
assert payload["fail_close_reason"] == "execution_loop_after_mutation_not_closing", payload
PY

python3 - "$NEGATIVE_JSON" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "scripts")
from execution_loop_after_mutation_not_closing_contract_common import build_contract_payload

payload = build_contract_payload()
payload["allowed_next_actions"] = list(payload["allowed_next_actions"]) + ["reread"]
payload["attempted_post_mutation_action"] = "reread"
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
PY

if python3 scripts/validate_execution_loop_after_mutation_not_closing.py --contract-json "$NEGATIVE_JSON" --json-only > "$NEGATIVE_RESULT_JSON"; then
  echo "negative probe unexpectedly passed" >&2
  exit 1
fi

python3 - "$NEGATIVE_RESULT_JSON" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["status"] == "FAIL_REQUIRED", payload
assert payload["fail_close_reason"] == "execution_loop_after_mutation_not_closing", payload
assert "allowed_next_actions_not_collapsed_after_mutation" in payload["stale_reasons"], payload
assert "execution_loop_after_mutation_not_closing" in payload["stale_reasons"], payload
PY

python3 - <<'PY'
import json

print(
    json.dumps(
        {
            "mode": "execution_loop_after_mutation_not_closing_probes",
            "status": "PASS_REQUIRED",
            "positive_probe": "validator_default_pass",
            "negative_probe": "reread_after_mutation_fail_closed",
        },
        indent=2,
        sort_keys=True,
    )
)
PY
