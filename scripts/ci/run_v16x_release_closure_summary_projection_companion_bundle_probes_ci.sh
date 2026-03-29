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

outer_surface_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_OUTER_SURFACE_E2E_COMPANION_MARKER"
)"
health_projection_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_HEALTH_PROJECTION_COMPANION_MARKER"
)"
release_cloud_evidence_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_RELEASE_CLOUD_EVIDENCE_COMPANION_MARKER"
)"
selected_check_scope_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_SELECTED_CHECK_SCOPE_COMPANION_MARKER"
)"
foundational_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_COMPANION_MARKER"
)"
one_look_topology_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_ONE_LOOK_TOPOLOGY_COMPANION_MARKER"
)"
support_preflight_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_SUPPORT_PREFLIGHT_COMPANION_MARKER"
)"
terminal_truth_bridge_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKER"
)"
terminal_truth_bridge_rich_companion_stale_reason_prefix="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "next(spec.stale_reason_prefix for spec in RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS if spec.markers == RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS)"
)"
terminal_truth_bridge_rich_boundary_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[0]"
)"
terminal_truth_bridge_rich_alignment_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[-1]"
)"
post_closure_adjudication_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKER"
)"
root_grounding_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_ROOT_GROUNDING_COMPANION_MARKER"
)"
full_scan_required_gate_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_FULL_SCAN_REQUIRED_GATE_COMPANION_MARKER"
)"
active_runtime_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_ACTIVE_RUNTIME_COMPANION_MARKER"
)"

printf '[RUN] positive release-closure summary projection-companion bundle validation\n'
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

mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${outer_surface_marker}" "scripts/ci/run_terminal_truth_boundary_e2e_probes_ci.sh"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${health_projection_marker}" "scripts/ci/run_release_readiness_health_probes_ci.sh"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${release_cloud_evidence_marker}" "release_cloud_evidence_projection=one_look.release_plane_cloud_evidence_status"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${selected_check_scope_marker}" "targeted_subset_selected_check_scope=selected_check_scope_projection_status=PASS_REQUIRED"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${foundational_marker}" "release_readiness_foundational_projection=one_look.required_contract_coverage_status"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${one_look_topology_marker}" "release_readiness_one_look_family_order=foundational|governance_probe"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${support_preflight_marker}" "release_readiness_support_preflight_projection=one_look.control_plane_budget_status"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${terminal_truth_bridge_marker}" "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${terminal_truth_bridge_rich_boundary_marker}" "bridge_execution_closure_status_missing"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${terminal_truth_bridge_rich_alignment_marker}" "bridge_next_state_alignment_status_missing"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${post_closure_adjudication_marker}" "release_readiness_post_closure_adjudication_order=runtime_summary_surface_governance|governance_probe_topology"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${root_grounding_marker}" "release_closure_root_grounding_order=protocol_root_corpus_precedence"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${full_scan_required_gate_marker}" "scripts/ci/run_full_scan_required_gate_probes_ci.sh"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${active_runtime_marker}" "active_runtime_closure_projection=one_look.identity_codex_launcher_status"

printf '[RUN] negative release-closure summary projection-companion bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary projection-companion bundle probe must fail'
  exit 1
fi

python3 - <<'PY' \
  "${POSITIVE_JSON}" \
  "${NEGATIVE_JSON}" \
  "${outer_surface_marker}" \
  "${health_projection_marker}" \
  "${release_cloud_evidence_marker}" \
  "${selected_check_scope_marker}" \
  "${foundational_marker}" \
  "${one_look_topology_marker}" \
  "${support_preflight_marker}" \
  "${terminal_truth_bridge_marker}" \
  "${terminal_truth_bridge_rich_companion_stale_reason_prefix}" \
  "${terminal_truth_bridge_rich_boundary_marker}" \
  "${terminal_truth_bridge_rich_alignment_marker}" \
  "${post_closure_adjudication_marker}" \
  "${root_grounding_marker}" \
  "${full_scan_required_gate_marker}" \
  "${active_runtime_marker}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary projection-companion bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary projection-companion bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    f"summary_doc_missing_outer_surface_e2e_marker:{sys.argv[3]}",
    f"summary_doc_missing_release_readiness_health_projection_marker:{sys.argv[4]}",
    f"summary_doc_missing_release_readiness_release_cloud_evidence_marker:{sys.argv[5]}",
    f"summary_doc_missing_release_readiness_selected_check_scope_marker:{sys.argv[6]}",
    f"summary_doc_missing_release_readiness_foundational_marker:{sys.argv[7]}",
    f"summary_doc_missing_release_readiness_one_look_topology_marker:{sys.argv[8]}",
    f"summary_doc_missing_release_readiness_support_preflight_marker:{sys.argv[9]}",
    f"summary_doc_missing_release_readiness_terminal_truth_bridge_marker:{sys.argv[10]}",
    f"summary_doc_{sys.argv[11]}:{sys.argv[12]}",
    f"summary_doc_{sys.argv[11]}:{sys.argv[13]}",
    f"summary_doc_missing_release_readiness_post_closure_adjudication_marker:{sys.argv[14]}",
    f"summary_doc_missing_release_closure_root_grounding_marker:{sys.argv[15]}",
    f"summary_doc_missing_full_scan_required_gate_projection_marker:{sys.argv[16]}",
    f"summary_doc_missing_active_runtime_closure_projection_marker:{sys.argv[17]}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary projection-companion bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary projection-companion bundle probes passed"
