#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT
export PROBE_FIXTURE_REPO_ROOT="${REPO_ROOT}"
source "${REPO_ROOT}/scripts/probe_fixture_shell_common.sh"

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"
GOVERNANCE_SHADOW_PATH="${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md"
REVIEW_SHADOW_PATH="${SHADOW_ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"

printf '[RUN] positive release-closure boundary horizon-alignment bundle validation\n'
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${REPO_ROOT}" --json-only > "${POSITIVE_JSON}"

python3 "${REPO_ROOT}/scripts/probe_shadow_fixture_common.py" \
  --repo-root "${REPO_ROOT}" \
  --shadow-root "${SHADOW_ROOT}" \
  --copy-file identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md \
  --copy-file identity/protocol/IDENTITY_PROTOCOL.md \
  --copy-file identity/protocol/IDENTITY_RUNTIME.md \
  --copy-file docs/workbook/protocol-issue-register-v1.6.md \
  --copy-file docs/governance/identity-v1.6x-release-closure-governance.md \
  --copy-file docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md \
  --json-only > /dev/null

python3 - <<'PY' "${POSITIVE_JSON}" "${GOVERNANCE_SHADOW_PATH}" "${REVIEW_SHADOW_PATH}"
import json
import re
import sys
from pathlib import Path


def decrement_issue(issue: str) -> str:
    prefix, raw_num = issue.split("-")
    value = int(raw_num)
    return f"{prefix}-{value - 1:03d}" if value > 0 else f"{prefix}-{raw_num}"


def decrement_version(version: str) -> str:
    match = re.match(r"^(.*\.)(\d+)$", version)
    if not match:
        return version + "-drift"
    prefix, raw_num = match.groups()
    value = int(raw_num)
    return f"{prefix}{value - 1}" if value > 0 else version + "-drift"


positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
governance_path = Path(sys.argv[2]).resolve()
review_path = Path(sys.argv[3]).resolve()

current_issue = positive["current_issue_horizon"]
stale_issue = decrement_issue(current_issue)
highest_version = positive["highest_closed_v16_stream_version"]
stale_version = decrement_version(highest_version)

for path in (governance_path, review_path):
    text = path.read_text(encoding="utf-8")
    text = text.replace(current_issue, stale_issue)
    text = text.replace(highest_version, stale_version)
    path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure boundary horizon-alignment bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary horizon-alignment bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path


def decrement_issue(issue: str) -> str:
    prefix, raw_num = issue.split("-")
    value = int(raw_num)
    return f"{prefix}-{value - 1:03d}" if value > 0 else f"{prefix}-{raw_num}"


positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary horizon-alignment bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary horizon-alignment bundle status must FAIL_REQUIRED")

stale_issue = decrement_issue(positive["current_issue_horizon"])
reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "governance_doc_issue_horizon_mismatch",
    f"governance_doc_stale_issue_horizon:{stale_issue}",
    "governance_doc_missing_highest_v16_stream_version",
    "review_doc_issue_horizon_mismatch",
    f"review_doc_stale_issue_horizon:{stale_issue}",
    "review_doc_missing_highest_v16_stream_version",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure boundary horizon-alignment bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure boundary horizon-alignment bundle probes passed"
