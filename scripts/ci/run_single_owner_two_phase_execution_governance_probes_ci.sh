#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_BASE="${TMPDIR:-$ROOT_DIR/.tmp}"
mkdir -p "$TMP_BASE"

POSITIVE_JSON="$TMP_BASE/issue-050-validator-positive.json"
NEGATIVE_CANONICAL_JSON="$TMP_BASE/issue-050-validator-negative-canonical.json"
NEGATIVE_ROLE_JSON="$TMP_BASE/issue-050-validator-negative-role.json"
NEGATIVE_CANONICAL_ROOT="$(mktemp -d "$TMP_BASE/issue-050-negative-canonical.XXXXXX")"
NEGATIVE_ROLE_ROOT="$(mktemp -d "$TMP_BASE/issue-050-negative-role.XXXXXX")"

cleanup() {
  rm -rf "$NEGATIVE_CANONICAL_ROOT" "$NEGATIVE_ROLE_ROOT"
}
trap cleanup EXIT

cd "$ROOT_DIR"

python3 - "$ROOT_DIR" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
for rel in (
    "scripts/single_owner_two_phase_execution_governance_contract_common.py",
    "scripts/validate_single_owner_two_phase_execution_governance.py",
):
    source = (root / rel).read_text(encoding="utf-8")
    compile(source, rel, "exec")
print("PASS issue_050_python_compile")
PY

python3 scripts/validate_single_owner_two_phase_execution_governance.py --json-only > "$POSITIVE_JSON"

python3 - "$ROOT_DIR" "$NEGATIVE_CANONICAL_ROOT" "$NEGATIVE_ROLE_ROOT" <<'PY'
from pathlib import Path
import shutil
import sys

repo_root = Path(sys.argv[1])
negative_canonical_root = Path(sys.argv[2])
negative_role_root = Path(sys.argv[3])

sys.path.insert(0, str(repo_root / "scripts"))
from single_owner_two_phase_execution_governance_contract_common import FIXED_WRITE_SET, READ_ONLY_INPUT_SURFACES

for negative_root in (negative_canonical_root, negative_role_root):
    if negative_root.exists():
        shutil.rmtree(negative_root)
    for rel in (*FIXED_WRITE_SET, *READ_ONLY_INPUT_SURFACES):
        src = repo_root / rel
        dst = negative_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

for rel in (
    "docs/governance/identity-single-owner-two-phase-execution-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-single-owner-two-phase-execution-governance.md",
):
    canonical_doc = negative_canonical_root / rel
    canonical_text = canonical_doc.read_text(encoding="utf-8")
    canonical_doc.write_text(
        canonical_text.replace('"canonical": false', '"canonical": true'),
        encoding="utf-8",
    )

for rel in (
    "docs/governance/identity-single-owner-two-phase-execution-governance-v1.6.x.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.x-single-owner-two-phase-execution-governance.md",
):
    role_doc = negative_role_root / rel
    role_text = role_doc.read_text(encoding="utf-8")
    role_doc.write_text(
        role_text.replace('"suggested_executor_role": "architect"', '"suggested_executor_role": "base-repo-audit-expert-v3"'),
        encoding="utf-8",
    )
PY

set +e
python3 "$ROOT_DIR/scripts/validate_single_owner_two_phase_execution_governance.py" --root "$NEGATIVE_CANONICAL_ROOT" --json-only > "$NEGATIVE_CANONICAL_JSON"
NEGATIVE_CANONICAL_RC=$?
python3 "$ROOT_DIR/scripts/validate_single_owner_two_phase_execution_governance.py" --root "$NEGATIVE_ROLE_ROOT" --json-only > "$NEGATIVE_ROLE_JSON"
NEGATIVE_ROLE_RC=$?
set -e

python3 - "$POSITIVE_JSON" "$NEGATIVE_CANONICAL_JSON" "$NEGATIVE_ROLE_JSON" "$NEGATIVE_CANONICAL_RC" "$NEGATIVE_ROLE_RC" <<'PY'
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative_canonical = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
negative_role = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
negative_canonical_rc = int(sys.argv[4])
negative_role_rc = int(sys.argv[5])

assert positive["status"] == "PASS_REQUIRED", positive
assert positive["ok"] is True, positive
assert positive["mode"] == "single_owner_two_phase_execution_governance_ready", positive
assert negative_canonical_rc != 0, negative_canonical_rc
assert negative_canonical["status"] == "FAIL_REQUIRED", negative_canonical
assert "feedback_packet_must_not_be_canonical" in negative_canonical["stale_reasons"], negative_canonical
assert negative_role_rc != 0, negative_role_rc
assert negative_role["status"] == "FAIL_REQUIRED", negative_role
assert "role_identity_field_pollution" in negative_role["stale_reasons"], negative_role
print("PASS single_owner_two_phase_execution_governance_probes")
PY
