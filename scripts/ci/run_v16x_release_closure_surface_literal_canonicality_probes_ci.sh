#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT
export PROBE_FIXTURE_REPO_ROOT="${REPO_ROOT}"
source "${REPO_ROOT}/scripts/probe_fixture_shell_common.sh"

SUMMARY_POSITIVE_JSON="${TMP_ROOT}/summary-positive.json"
SUMMARY_NEGATIVE_JSON="${TMP_ROOT}/summary-negative.json"
BOUNDARY_POSITIVE_JSON="${TMP_ROOT}/boundary-positive.json"
BOUNDARY_NEGATIVE_JSON="${TMP_ROOT}/boundary-negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"
CONTROL_SURFACE_PROBE_COMMON="${REPO_ROOT}/scripts/release_closure_control_surface_probe_common.py"

printf '[RUN] positive release-closure literal-canonicality validations\n'
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${REPO_ROOT}" --json-only > "${SUMMARY_POSITIVE_JSON}"
python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${REPO_ROOT}" --json-only > "${BOUNDARY_POSITIVE_JSON}"

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

python3 "${CONTROL_SURFACE_PROBE_COMMON}" \
  mutate \
  --profile surface_literal_canonicality \
  --summary-path "${SHADOW_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md" \
  --governance-path "${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md"

printf '[RUN] negative release-closure literal-canonicality validations\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${SUMMARY_NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary literal-canonicality probe must fail'
  exit 1
fi
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${BOUNDARY_NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary literal-canonicality probe must fail'
  exit 1
fi

python3 "${CONTROL_SURFACE_PROBE_COMMON}" \
  assert \
  --profile surface_literal_canonicality \
  --summary-positive-json "${SUMMARY_POSITIVE_JSON}" \
  --summary-negative-json "${SUMMARY_NEGATIVE_JSON}" \
  --boundary-positive-json "${BOUNDARY_POSITIVE_JSON}" \
  --boundary-negative-json "${BOUNDARY_NEGATIVE_JSON}"

echo "[PASS] v1.6.x release closure surface literal canonicality probes passed"
