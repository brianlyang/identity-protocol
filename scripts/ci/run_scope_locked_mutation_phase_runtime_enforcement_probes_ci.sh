#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_BASE="${TMPDIR:-$ROOT/.tmp}"
mkdir -p "$TMP_BASE"

POSITIVE_JSON="$TMP_BASE/scope_locked_mutation_phase_runtime_enforcement_positive.json"
NEGATIVE_JSON="$TMP_BASE/scope_locked_mutation_phase_runtime_enforcement_negative.json"
NEGATIVE_ROOT="$(mktemp -d "$TMP_BASE/scope_locked_mutation_phase_runtime_enforcement.XXXXXX")"

python3 "$ROOT/scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py" --root "$ROOT" --json-only > "$POSITIVE_JSON"

python3 - "$ROOT" "$NEGATIVE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
negative_root = Path(sys.argv[2])
paths = [
    "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-scope-locked-mutation-phase-runtime-enforcement.md",
    "scripts/scope_locked_mutation_phase_runtime_enforcement_contract_common.py",
    "scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py",
    "scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh",
]
for relative in paths:
    source = root / relative
    target = negative_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

governance = negative_root / "docs/governance/identity-scope-locked-mutation-phase-runtime-enforcement-governance-v1.6.x.md"
content = governance.read_text(encoding="utf-8")
content = content.replace("emit_fail_close_token", "removed_fail_close_action")
governance.write_text(content, encoding="utf-8")
PY

set +e
python3 "$ROOT/scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py" --root "$NEGATIVE_ROOT" --json-only > "$NEGATIVE_JSON"
NEGATIVE_EXIT=$?
set -e

python3 - "$POSITIVE_JSON" "$NEGATIVE_JSON" "$NEGATIVE_EXIT" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
negative_exit = int(sys.argv[3])

if positive.get("status") != "PASS_REQUIRED":
    raise SystemExit("positive validator did not PASS_REQUIRED")
if negative_exit == 0:
    raise SystemExit("negative validator unexpectedly succeeded")
if negative.get("status") != "FAIL_REQUIRED":
    raise SystemExit("negative validator did not FAIL_REQUIRED")
if negative.get("mode") != "execution_loop_not_entering_mutation_phase":
    raise SystemExit("negative validator mode drifted")
if "mutation_required_but_not_entered" not in negative.get("stale_reasons", []):
    raise SystemExit("negative validator missing mutation_required_but_not_entered")
PY

echo "PASS scope_locked_mutation_phase_runtime_enforcement_probes"
