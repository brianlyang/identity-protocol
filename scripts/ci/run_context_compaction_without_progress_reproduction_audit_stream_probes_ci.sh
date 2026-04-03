#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMPDIR="${TMPDIR:-$ROOT_DIR/.tmp}"
mkdir -p "$TMPDIR"

POSITIVE_JSON="$TMPDIR/context_compaction_without_progress_reproduction_audit_stream_positive.json"
NEGATIVE_JSON="$TMPDIR/context_compaction_without_progress_reproduction_audit_stream_negative.json"
ISSUE_045_JSON="$TMPDIR/context_compaction_without_progress_reproduction_issue_045_validator.json"
ISSUE_046_JSON="$TMPDIR/context_compaction_without_progress_reproduction_issue_046_validator.json"
NEGATIVE_ROOT="$(mktemp -d "$TMPDIR/context_compaction_without_progress_reproduction_audit_stream.XXXXXX")"

cd "$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts${PYTHONPATH:+:$PYTHONPATH}" \
TMPDIR="$TMPDIR" \
python3 scripts/validate_context_compaction_without_progress_reproduction_audit_stream.py --json-only > "$POSITIVE_JSON"

PYTHONPATH="$ROOT_DIR/scripts${PYTHONPATH:+:$PYTHONPATH}" \
TMPDIR="$TMPDIR" \
python3 scripts/validate_lane_segmented_infrastructure_admission.py --json-only > "$ISSUE_045_JSON"

bash scripts/ci/run_lane_segmented_infrastructure_admission_probes_ci.sh > /dev/null

TMPDIR="$TMPDIR" \
python3 scripts/validate_scope_locked_mutation_phase_runtime_enforcement.py --json-only > "$ISSUE_046_JSON"

TMPDIR="$TMPDIR" \
bash scripts/ci/run_scope_locked_mutation_phase_runtime_enforcement_probes_ci.sh > /dev/null

python3 - "$ROOT_DIR" "$NEGATIVE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
negative_root = Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts"))

from context_compaction_without_progress_reproduction_audit_stream_contract_common import (  # noqa: E402
    FIXED_WRITE_SET,
    READ_ONLY_INPUT_SURFACES,
)

for relative in [*FIXED_WRITE_SET, *READ_ONLY_INPUT_SURFACES]:
    source = root / relative
    target = negative_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

governance = negative_root / "docs/governance/identity-context-compaction-without-progress-reproduction-audit-stream-governance-v1.6.x.md"
content = governance.read_text(encoding="utf-8")
content = content.replace("uncovered_machine_visible_reproduction_candidate", "removed_uncovered_outcome")
governance.write_text(content, encoding="utf-8")
PY

set +e
PYTHONPATH="$NEGATIVE_ROOT/scripts${PYTHONPATH:+:$PYTHONPATH}" \
TMPDIR="$TMPDIR" \
python3 "$ROOT_DIR/scripts/validate_context_compaction_without_progress_reproduction_audit_stream.py" \
  --root "$NEGATIVE_ROOT" --json-only > "$NEGATIVE_JSON"
NEGATIVE_EXIT=$?
set -e

python3 - "$POSITIVE_JSON" "$NEGATIVE_JSON" "$NEGATIVE_EXIT" "$ISSUE_045_JSON" "$ISSUE_046_JSON" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
negative_exit = int(sys.argv[3])
issue_045 = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
issue_046 = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))

assert positive["status"] == "PASS_REQUIRED", positive
assert positive["ok"] is True, positive
assert issue_045["status"] == "PASS_REQUIRED", issue_045
assert issue_046["status"] == "PASS_REQUIRED", issue_046
assert negative_exit != 0, negative_exit
assert negative["status"] == "FAIL_REQUIRED", negative
assert negative["mode"] == "read_only_residual_reproduction_audit_stream_drift", negative
assert any(
    "uncovered_machine_visible_reproduction_candidate" in reason
    for reason in negative["stale_reasons"]
), negative

print("PASS context_compaction_without_progress_reproduction_audit_stream_probes")
PY
