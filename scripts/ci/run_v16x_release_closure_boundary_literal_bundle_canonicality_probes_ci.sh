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

projection_profile_exclusion_scope_marker="$(
  resolve_python_module_expression \
    "projection_profile_exclusion_scope_common" \
    "PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS[0]"
)"
release_cloud_evidence_projection_marker="$(
  resolve_python_module_expression \
    "release_cloud_evidence_projection_common" \
    "RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER"
)"
targeted_subset_required_gate_bundle_scope_marker="$(
  resolve_python_module_expression \
    "release_readiness_required_gate_bundle_scope_common" \
    "RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS[0]"
)"
targeted_subset_required_gate_bundle_scope_reason_marker="$(
  resolve_python_module_expression \
    "release_readiness_required_gate_bundle_scope_common" \
    "RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS[1]"
)"
targeted_subset_selected_check_scope_marker="$(
  resolve_python_module_expression \
    "release_readiness_selected_check_scope_common" \
    "RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS[0]"
)"
release_readiness_selected_check_scope_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_selected_check_scope_common" \
    "RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER"
)"
release_readiness_one_look_family_order_marker="$(
  resolve_python_module_expression \
    "release_readiness_one_look_topology_common" \
    "RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER"
)"
release_readiness_foundational_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_foundational_projection_common" \
    "RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER"
)"
release_readiness_support_preflight_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_support_preflight_projection_common" \
    "RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER"
)"
required_gate_bundle_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_required_gate_bundle_projection_common" \
    "RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER"
)"
full_scan_required_gate_bundle_projection_marker="$(
  resolve_python_module_expression \
    "full_scan_required_gate_bundle_projection_common" \
    "FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER"
)"
full_scan_required_gate_bundle_summary_marker="$(
  resolve_python_module_expression \
    "full_scan_required_gate_bundle_projection_common" \
    "FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER"
)"

printf '[RUN] positive release-closure boundary literal-bundle validation\n'
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

mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${projection_profile_exclusion_scope_marker}" \
  "projection_profile_exclusion_scope=projection_skip_status=SKIPPED_NOT_REQUIRED"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${release_cloud_evidence_projection_marker}" \
  "release_cloud_evidence_projection=one_look.release_plane_cloud_evidence_status"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${targeted_subset_required_gate_bundle_scope_marker}" \
  "targeted_subset_required_gate_bundle_scope=required_gate_bundle_status=SKIPPED_NOT_REQUIRED"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${targeted_subset_required_gate_bundle_scope_reason_marker}" \
  "targeted_subset_required_gate_bundle_scope_reason=required_gate_bundle_scope_reason=scope_reason_drifted"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${targeted_subset_selected_check_scope_marker}" \
  "targeted_subset_selected_check_scope=selected_check_scope_projection_status=PASS_REQUIRED"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${release_readiness_selected_check_scope_projection_marker}" \
  "release_readiness_selected_check_scope_projection=one_look.selected_check_scope_projection_status"

mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${release_readiness_one_look_family_order_marker}" \
  "release_readiness_one_look_family_order=foundational|governance_probe"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${release_readiness_foundational_projection_marker}" \
  "release_readiness_foundational_projection=one_look.required_contract_coverage_status"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${release_readiness_support_preflight_projection_marker}" \
  "release_readiness_support_preflight_projection=one_look.control_plane_budget_status"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${required_gate_bundle_projection_marker}" \
  "required_gate_bundle_projection=one_look.required_gate_bundle_status"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${full_scan_required_gate_bundle_projection_marker}" \
  "full_scan_required_gate_bundle_projection=three_plane.required_gate_bundle_status"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${full_scan_required_gate_bundle_summary_marker}" \
  "full_scan_required_gate_bundle_summary=summary_required_gate_bundle_projection.identities_with_projection"

printf '[RUN] negative release-closure boundary literal-bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary literal-bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary literal-bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary literal-bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "governance_doc_projection_profile_exclusion_scope_line_not_canonical",
    "governance_doc_release_cloud_evidence_projection_line_not_canonical",
    "governance_doc_targeted_subset_required_gate_bundle_scope_line_not_canonical",
    "governance_doc_targeted_subset_required_gate_bundle_scope_reason_line_not_canonical",
    "governance_doc_targeted_subset_selected_check_scope_line_not_canonical",
    "governance_doc_release_readiness_selected_check_scope_projection_line_not_canonical",
    "review_doc_release_readiness_one_look_family_order_line_not_canonical",
    "review_doc_release_readiness_foundational_projection_line_not_canonical",
    "review_doc_release_readiness_support_preflight_projection_line_not_canonical",
    "review_doc_required_gate_bundle_projection_line_not_canonical",
    "review_doc_full_scan_required_gate_bundle_projection_line_not_canonical",
    "review_doc_full_scan_required_gate_bundle_summary_line_not_canonical",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure boundary literal-bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure boundary literal-bundle canonicality probes passed"
