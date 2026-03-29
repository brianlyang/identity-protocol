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

summary_doc_rel="$(
  resolve_python_module_expression \
    "release_closure_required_doc_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS[-1]"
)"
workbook_doc_rel="$(
  resolve_python_module_expression \
    "release_closure_required_doc_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS[4]"
)"

printf '[RUN] positive release-closure summary required-doc bundle validation\n'
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${REPO_ROOT}" --json-only > "${POSITIVE_JSON}"

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

printf '[RUN] negative release-closure summary required-doc bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary required-doc bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}" "${SHADOW_ROOT}" "${workbook_doc_rel}" "${summary_doc_rel}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
shadow_root = Path(sys.argv[3]).resolve()
workbook_doc_rel = sys.argv[4]
summary_doc_rel = sys.argv[5]

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary required-doc bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary required-doc bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    f"missing_required_doc:{(shadow_root / workbook_doc_rel).resolve()}",
    f"missing_required_doc:{(shadow_root / summary_doc_rel).resolve()}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary required-doc bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary required-doc bundle probes passed"
