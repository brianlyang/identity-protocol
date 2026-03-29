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

active_report_pointer_selector_marker="$(
  resolve_python_module_expression \
    "release_closure_narrative_marker_common" \
    "next(spec.markers[4] for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS if spec.stale_reason_suffix == 'active_report_pointer_locality')"
)"
strict_live_active_pointer_context_marker="$(
  resolve_python_module_expression \
    "release_closure_narrative_marker_common" \
    "next(spec.markers[2] for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS if spec.stale_reason_suffix == 'strict_live_active_pointer_locality')"
)"
strict_live_contract_resolution_marker="$(
  resolve_python_module_expression \
    "release_closure_narrative_marker_common" \
    "next(spec.markers[3] for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS if spec.stale_reason_suffix == 'strict_live_contract_resolution')"
)"
weak_live_pointer_absorption_marker="$(
  resolve_python_module_expression \
    "release_closure_narrative_marker_common" \
    "next(spec.markers[2] for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS if spec.stale_reason_suffix == 'weak_live_pointer_absorption')"
)"
execution_report_selection_marker="$(
  resolve_python_module_expression \
    "release_closure_narrative_marker_common" \
    "next(spec.markers[1] for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS if spec.stale_reason_suffix == 'execution_report_selection_convergence')"
)"

printf '[RUN] positive release-closure summary narrative-bundle validation\n'
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
  "${active_report_pointer_selector_marker}" \
  "latest_execution_report()"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${strict_live_active_pointer_context_marker}" \
  "resolve_current_execution_context()"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${strict_live_contract_resolution_marker}" \
  "sample green failclose"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${weak_live_pointer_absorption_marker}" \
  "current_pointer_resolution_mode"
mutate_probe_literal \
  "${SUMMARY_SHADOW_PATH}" \
  "${execution_report_selection_marker}" \
  "primary_execution_report_selector.py"

printf '[RUN] negative release-closure summary narrative-bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary narrative-bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary narrative-bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary narrative-bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "summary_doc_missing_active_report_pointer_locality_marker:latest_identity_upgrade_report()",
    "summary_doc_missing_strict_live_active_pointer_locality_marker:resolve_active_execution_context()",
    "summary_doc_missing_strict_live_contract_resolution_marker:sample-green fail-close",
    "summary_doc_missing_weak_live_pointer_absorption_marker:current_run_pointer_resolution_mode",
    "summary_doc_missing_execution_report_selection_convergence_marker:execution_report_selection_common.py",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary narrative-bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary narrative-bundle probes passed"
