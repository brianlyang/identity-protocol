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
SUMMARY_SHADOW_PATH="${SHADOW_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md"

printf '[RUN] positive release-closure summary horizon-alignment bundle validation\n'
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${REPO_ROOT}" --json-only > "${POSITIVE_JSON}"

python3 "${REPO_ROOT}/scripts/probe_shadow_fixture_common.py" \
  --repo-root "${REPO_ROOT}" \
  --shadow-root "${SHADOW_ROOT}" \
  --copy-file identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md \
  --copy-file identity/protocol/IDENTITY_PROTOCOL.md \
  --copy-file identity/protocol/IDENTITY_RUNTIME.md \
  --copy-file docs/workbook/protocol-issue-register-v1.6.md \
  --copy-file docs/workbook/protocol-deep-audit-workbook-v1.6.md \
  --copy-file docs/governance/identity-v1.6x-release-closure-governance.md \
  --copy-file docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md \
  --copy-file docs/release/identity-v1.6x-release-closure-summary.md \
  --json-only > /dev/null

python3 - <<'PY' "${POSITIVE_JSON}" "${SUMMARY_SHADOW_PATH}"
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


def drift_boundary_version(version: str) -> str:
    if version.startswith("v1.6."):
        return version.replace("v1.6.", "v9.6.", 1)
    return version + "-drift"


positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
path = Path(sys.argv[2]).resolve()
text = path.read_text(encoding="utf-8")

current_issue = positive["current_issue_horizon"]
stale_issue = decrement_issue(current_issue)
highest_version = positive["highest_closed_v16_stream_version"]
stale_version = decrement_version(highest_version)
boundary_versions = positive["boundary_stream_versions"]
boundary_version = next(
    version for version in boundary_versions if version != highest_version
)

text = text.replace(current_issue, stale_issue)
text = text.replace(highest_version, stale_version)
text = text.replace(boundary_version, drift_boundary_version(boundary_version))
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure summary horizon-alignment bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary horizon-alignment bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import re
import sys
from pathlib import Path


def decrement_issue(issue: str) -> str:
    prefix, raw_num = issue.split("-")
    value = int(raw_num)
    return f"{prefix}-{value - 1:03d}" if value > 0 else f"{prefix}-{raw_num}"


positive = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
negative = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary horizon-alignment bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary horizon-alignment bundle status must FAIL_REQUIRED")

current_issue = positive["current_issue_horizon"]
stale_issue = decrement_issue(current_issue)
highest_version = positive["highest_closed_v16_stream_version"]
boundary_version = next(
    version for version in positive["boundary_stream_versions"] if version != highest_version
)

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "summary_doc_issue_horizon_mismatch",
    f"summary_doc_stale_issue_horizon:{stale_issue}",
    "summary_doc_missing_highest_v16_stream_version",
    f"summary_doc_missing_boundary_stream_version:{boundary_version}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary horizon-alignment bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary horizon-alignment bundle probes passed"
