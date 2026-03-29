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

summary_lifecycle_finalized_marker="$(
  resolve_python_module_expression \
    "release_closure_continuation_marker_common" \
    "RELEASE_CLOSURE_SUMMARY_CONTINUATION_FINALIZED_MARKER"
)"
resume_capture_mode_marker="$(
  resolve_python_module_expression \
    "release_closure_continuation_marker_common" \
    "RELEASE_CLOSURE_SUMMARY_CONTINUATION_RESUME_CAPTURE_MODE_MARKER"
)"
transport_fleet_probe_marker="$(
  resolve_python_module_expression \
    "release_readiness_runtime_closure_convergence_common" \
    "RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER"
)"
active_runtime_pack_probe_marker="$(
  resolve_python_module_expression \
    "release_readiness_runtime_closure_convergence_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER"
)"
workspace_runtime_runner_marker="$(
  resolve_python_module_expression \
    "release_readiness_runtime_closure_convergence_common" \
    "RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER"
)"

printf '[RUN] positive release-closure summary operational-marker bundle validation\n'
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
  "${summary_lifecycle_finalized_marker}" \
  "summary_lifecycle_status=DONE"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${resume_capture_mode_marker}" \
  "resume_capture_mode=resume_snapshot"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${transport_fleet_probe_marker}" \
  "scripts/ci/run_transport_fleet_convergence_probes_ci.sh"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${active_runtime_pack_probe_marker}" \
  "scripts/ci/run_runtime_pack_convergence_probes_ci.sh"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${workspace_runtime_runner_marker}" \
  "scripts/run_workspace_runtime_pack_checks.py"

printf '[RUN] negative release-closure summary operational-marker bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary operational-marker bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary operational-marker bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary operational-marker bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "summary_doc_missing_release_readiness_lifecycle_marker:summary_lifecycle_status=FINALIZED",
    "summary_doc_missing_release_readiness_lifecycle_marker:resume_capture_mode=stable_prewrite_snapshot",
    "summary_doc_missing_transport_fleet_closure_convergence_marker:scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh",
    "summary_doc_missing_active_runtime_pack_closure_convergence_marker:scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh",
    "summary_doc_missing_workspace_runtime_closure_command_convergence_marker:scripts/run_workspace_runtime_closure_checks.py",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary operational-marker bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary operational-marker bundle probes passed"
