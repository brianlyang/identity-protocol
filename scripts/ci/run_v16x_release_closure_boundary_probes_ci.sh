#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive release-closure boundary validation\n'
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${REPO_ROOT}" --json-only > "${POSITIVE_JSON}"

mkdir -p \
  "${SHADOW_ROOT}/identity/protocol" \
  "${SHADOW_ROOT}/docs/workbook" \
  "${SHADOW_ROOT}/docs/governance" \
  "${SHADOW_ROOT}/docs/review"

cp "${REPO_ROOT}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md" "${SHADOW_ROOT}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
cp "${REPO_ROOT}/identity/protocol/IDENTITY_PROTOCOL.md" "${SHADOW_ROOT}/identity/protocol/IDENTITY_PROTOCOL.md"
cp "${REPO_ROOT}/identity/protocol/IDENTITY_RUNTIME.md" "${SHADOW_ROOT}/identity/protocol/IDENTITY_RUNTIME.md"
cp "${REPO_ROOT}/docs/workbook/protocol-issue-register-v1.6.md" "${SHADOW_ROOT}/docs/workbook/protocol-issue-register-v1.6.md"
cp "${REPO_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md" "${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md"
cp "${REPO_ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md" "${SHADOW_ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"

python3 - <<'PY' "${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md"
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve()
text = path.read_text(encoding="utf-8")
text = text.replace("`ISSUE-001` through `ISSUE-039`", "`ISSUE-001` through `ISSUE-038`")
text = text.replace("`v1.6.21`", "`v1.6.20`", 1)
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure boundary validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary status must PASS_REQUIRED")
if positive.get("current_issue_horizon") != "ISSUE-039":
    raise SystemExit("positive release-closure boundary must track ISSUE-039 horizon")
if positive.get("highest_closed_v16_stream_version") != "v1.6.21":
    raise SystemExit("positive release-closure boundary must track highest closed v1.6 stream")

if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary status must FAIL_REQUIRED")
reasons = set(negative.get("stale_reasons") or [])
if "governance_doc_issue_horizon_mismatch" not in reasons:
    raise SystemExit("negative release-closure boundary must detect governance issue-horizon drift")
if "governance_doc_missing_highest_v16_stream_version" not in reasons:
    raise SystemExit("negative release-closure boundary must detect missing highest v1.6 stream version")
PY

echo "[PASS] v1.6.x release closure boundary probes passed"
