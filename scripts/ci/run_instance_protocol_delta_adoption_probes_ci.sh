#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
TMPDIR_VALUE=${TMPDIR:-$ROOT_DIR/.tmp}
mkdir -p "$TMPDIR_VALUE"

POSITIVE_JSON=$(mktemp "$TMPDIR_VALUE/instance_protocol_delta_adoption_positive.XXXXXX.json")
NEGATIVE_ROOT=$(mktemp -d "$TMPDIR_VALUE/instance_protocol_delta_adoption_negative.XXXXXX")
NEGATIVE_JSON=$(mktemp "$TMPDIR_VALUE/instance_protocol_delta_adoption_negative.XXXXXX.json")

cleanup() {
  rm -rf "$NEGATIVE_ROOT"
  rm -f "$POSITIVE_JSON" "$NEGATIVE_JSON"
}
trap cleanup EXIT

python3 "$ROOT_DIR/scripts/validate_instance_protocol_delta_adoption.py" --json-only > "$POSITIVE_JSON"
python3 - "$POSITIVE_JSON" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_delta_adoption_status"] == "PASS_REQUIRED", payload
assert payload["protocol_delta_adoption_mode"] == "continuous_protocol_delta_adoption_ready", payload
assert payload["last_adopted_protocol_commit"] == "f616889", payload
assert "scope_locked_mutation_phase_runtime_enforcement_contract_v1" in payload["adopted_protocol_delta_laws"], payload
PY

mkdir -p "$NEGATIVE_ROOT/scripts/ci" "$NEGATIVE_ROOT/docs/governance" "$NEGATIVE_ROOT/docs/review"
cp "$ROOT_DIR/scripts/validate_instance_protocol_delta_adoption.py" "$NEGATIVE_ROOT/scripts/validate_instance_protocol_delta_adoption.py"
cp "$ROOT_DIR/scripts/instance_protocol_delta_adoption_contract_common.py" "$NEGATIVE_ROOT/scripts/instance_protocol_delta_adoption_contract_common.py"
cp "$ROOT_DIR/docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md" \
  "$NEGATIVE_ROOT/docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md"
cp "$ROOT_DIR/docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md" \
  "$NEGATIVE_ROOT/docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md"

python3 - "$NEGATIVE_ROOT/scripts/instance_protocol_delta_adoption_contract_common.py" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace(
    'ADOPTED_PROTOCOL_DELTA_LAWS = (ABSORBED_LAW_ID,)',
    'ADOPTED_PROTOCOL_DELTA_LAWS = tuple()',
)
path.write_text(text, encoding="utf-8")
PY

if python3 "$NEGATIVE_ROOT/scripts/validate_instance_protocol_delta_adoption.py" --json-only > "$NEGATIVE_JSON"; then
  echo "negative probe unexpectedly passed" >&2
  exit 1
fi

python3 - "$NEGATIVE_JSON" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_delta_adoption_status"] == "FAIL_REQUIRED", payload
assert payload["protocol_delta_adoption_mode"] == "relevant_protocol_delta_pending_adoption", payload
assert "runtime_guard_law_not_adopted:scope_locked_mutation_phase_runtime_enforcement_contract_v1" in payload["stale_reasons"], payload
PY

echo "PASS"
