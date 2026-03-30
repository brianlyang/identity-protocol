#!/usr/bin/env bash
set -euo pipefail

# ISSUE-045 machine-visible execution-loop freeze:
# execution_loop_not_entering_mutation_phase
# planning_budget_status
# scope_lock_status
# mutation_phase_entry_status
# repeated_plan_restatement_status
# repeated_reanchor_status
# repeated_compaction_without_progress_status
# execution_loop_status
# stale_reasons
# ordered_execution_sequence=common -> governance/review -> validator -> probe -> workbook/register

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMPDIR="${TMPDIR:-$ROOT_DIR/.tmp}"
mkdir -p "$TMPDIR"

POSITIVE_JSON="$TMPDIR/issue-045-validator-positive.json"
NEGATIVE_JSON="$TMPDIR/issue-045-validator-negative.json"
NEGATIVE_ROOT="$TMPDIR/issue-045-negative-root"

cd "$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts${PYTHONPATH:+:$PYTHONPATH}" \
TMPDIR="$TMPDIR" \
python3 scripts/validate_lane_segmented_infrastructure_admission.py --json-only > "$POSITIVE_JSON"

python3 - "$ROOT_DIR" "$NEGATIVE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

repo_root = Path(sys.argv[1])
negative_root = Path(sys.argv[2])
if negative_root.exists():
    shutil.rmtree(negative_root)

paths = [
    "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-segmented-infrastructure-admission.md",
    "scripts/lane_segmented_infrastructure_admission_contract_common.py",
    "scripts/validate_lane_segmented_infrastructure_admission.py",
    "scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh",
    "docs/workbook/protocol-deep-audit-workbook-v1.6.md",
    "docs/workbook/protocol-issue-register-v1.6.md",
]

for rel in paths:
    src = repo_root / rel
    dst = negative_root / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

governance_path = negative_root / "docs/governance/identity-lane-segmented-infrastructure-admission-governance-v1.6.x.md"
text = governance_path.read_text(encoding="utf-8")
governance_path.write_text(
    text.replace("mutation_phase_entry_status", "entry_gate_removed"),
    encoding="utf-8",
)
PY

set +e
PYTHONPATH="$NEGATIVE_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}" \
TMPDIR="$TMPDIR" \
python3 "$ROOT_DIR/scripts/validate_lane_segmented_infrastructure_admission.py" \
  --root "$NEGATIVE_ROOT" --json-only > "$NEGATIVE_JSON"
NEGATIVE_RC=$?
set -e

python3 - "$POSITIVE_JSON" "$NEGATIVE_JSON" "$NEGATIVE_RC" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
negative_rc = int(sys.argv[3])

assert positive["status"] == "PASS_REQUIRED", positive
assert positive["ok"] is True, positive
assert negative_rc != 0, negative_rc
assert negative["status"] == "FAIL_REQUIRED", negative
assert negative["mode"] == "execution_loop_not_entering_mutation_phase", negative
assert any(
    "mutation_phase_entry_status" in reason or "execution_loop_not_entering_mutation_phase" in reason
    for reason in negative["stale_reasons"]
), negative

print("PASS_REQUIRED issue_045_lane_segmented_infrastructure_admission_probes")
PY
