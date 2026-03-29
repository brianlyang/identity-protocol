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

repo_global_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"
)"
active_runtime_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"
)"
governance_probe_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_projection_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER"
)"
terminal_truth_bridge_surface_marker="$(
  resolve_python_module_expression \
    "release_readiness_terminal_truth_bridge_common" \
    "RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER"
)"
post_closure_adjudication_order_marker="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER"
)"

printf '[RUN] positive release-closure summary control-surface bundle validation\n'
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

mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${repo_global_projection_marker}" \
  "repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${active_runtime_projection_marker}" \
  "active_runtime_closure_projection=one_look.identity_codex_launcher_status"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${governance_probe_projection_marker}" \
  "governance_probe_projection=one_look.runtime_summary_surface_governance_probe_status"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${terminal_truth_bridge_surface_marker}" \
  "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${post_closure_adjudication_order_marker}" \
  "release_readiness_post_closure_adjudication_order=runtime_summary_surface_governance|governance_probe_topology"

printf '[RUN] negative release-closure summary control-surface bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary control-surface bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary control-surface bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary control-surface bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "summary_doc_repo_global_closure_projection_line_not_canonical",
    "summary_doc_active_runtime_closure_projection_line_not_canonical",
    "summary_doc_governance_probe_projection_line_not_canonical",
    "summary_doc_terminal_truth_bridge_surface_line_not_canonical",
    "summary_doc_post_closure_adjudication_order_line_not_canonical",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary control-surface bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary control-surface bundle probes passed"
