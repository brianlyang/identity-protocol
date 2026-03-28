#!/usr/bin/env bash
set -euo pipefail
# strict-actor-entry-exemption: probe_fixture_literals_allowed
# This probe mutates copied fixture files to verify fail-close governance drift,
# so script-path literals here are fixture inputs rather than live strict-entry launches.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
export PROBE_FIXTURE_REPO_ROOT="$repo_root"
source "${repo_root}/scripts/probe_fixture_shell_common.sh"

echo "[INFO] positive: runtime summary surface governance validator"
python3 scripts/validate_runtime_summary_surface_governance.py --json-only >/tmp/runtime-summary-surface-governance-positive.json

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/scripts" "$tmpdir/docs/governance" "$tmpdir/docs/review" "$tmpdir/docs/release"
cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"
cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp scripts/render_identity_codex_launcher.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md "$tmpdir/docs/review/"
cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md "$tmpdir/docs/review/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.3.md "$tmpdir/docs/review/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

mutate_probe_literal \
  "$tmpdir/scripts/report_three_plane_status.py" \
  'payload["surface_governance"] = build_governed_runtime_summary_surface_payload("semantic_tuple_three_plane")'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-script.json; then
  echo "[FAIL] negative script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/report_three_plane_status.py" \
  '"projection_excluded_areas"'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-three-plane-projection-script.json; then
  echo "[FAIL] negative three-plane projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative three-plane projection script drift probe fail-closed as expected"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  '`scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection`'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-three-plane-projection-doc.json; then
  echo "[FAIL] negative three-plane projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative three-plane projection doc anchor probe fail-closed as expected"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/report_three_plane_status.py" \
  '"health_report_experience_writeback_closure"'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-three-plane-health-script.json; then
  echo "[FAIL] negative three-plane health projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative three-plane health projection script drift probe fail-closed as expected"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  'scripts/ci/run_three_plane_health_projection_probes_ci.sh'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-three-plane-health-doc.json; then
  echo "[FAIL] negative three-plane health projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative three-plane health projection doc anchor probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

projection_profile_exclusion_scope_marker="$(
  resolve_python_module_expression \
    "projection_profile_exclusion_scope_common" \
    "PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS[0]"
)"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/report_three_plane_status.py" \
  "build_projection_profile_exclusion_payload("

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-projection-profile-exclusion-script.json; then
  echo "[FAIL] negative projection-profile exclusion script probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative projection-profile exclusion script probe fail-closed as expected"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/full_identity_protocol_scan.py" \
  "build_projection_profile_exclusion_payload("

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-full-scan-projection-profile-exclusion-script.json; then
  echo "[FAIL] negative full-scan projection-profile exclusion script probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan projection-profile exclusion script probe fail-closed as expected"

cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$projection_profile_exclusion_scope_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-projection-profile-exclusion-doc.json; then
  echo "[FAIL] negative projection-profile exclusion doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative projection-profile exclusion doc probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_selected_check_scope_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-selected-check-one-look-script.json; then
  echo "[FAIL] negative selected-check one-look script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative selected-check one-look script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

selected_check_scope_one_look_marker="$(
  resolve_python_module_constant \
    "release_readiness_selected_check_scope_common" \
    "RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$selected_check_scope_one_look_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-selected-check-one-look-doc.json; then
  echo "[FAIL] negative selected-check one-look doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative selected-check one-look doc probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_release_cloud_evidence_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-release-cloud-evidence-one-look-script.json; then
  echo "[FAIL] negative release-cloud-evidence one-look script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative release-cloud-evidence one-look script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

release_cloud_evidence_projection_marker="$(
  resolve_python_module_constant \
    "release_cloud_evidence_projection_common" \
    "RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$release_cloud_evidence_projection_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-release-cloud-evidence-doc.json; then
  echo "[FAIL] negative release-cloud-evidence doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative release-cloud-evidence doc anchor probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_terminal_truth_boundary_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-terminal-truth-one-look-script.json; then
  echo "[FAIL] negative terminal-truth one-look script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative terminal-truth one-look script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_health_report_experience_writeback_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-health-writeback-one-look-script.json; then
  echo "[FAIL] negative health-writeback one-look script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative health-writeback one-look script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_repo_global_closure_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-repo-global-script.json; then
  echo "[FAIL] negative repo-global projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global projection script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

repo_global_closure_projection_marker="$(
  resolve_python_module_constant \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$repo_global_closure_projection_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-repo-global-doc.json; then
  echo "[FAIL] negative repo-global projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global projection doc anchor probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

repo_global_closure_proof_strength_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS[0]"
)"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "$repo_global_closure_proof_strength_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-repo-global-proof-strength-doc.json; then
  echo "[FAIL] negative repo-global proof-strength doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global proof-strength doc anchor probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_active_runtime_closure_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-active-runtime-script.json; then
  echo "[FAIL] negative active-runtime projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative active-runtime projection script drift probe fail-closed as expected"

cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

active_runtime_closure_projection_marker="$(
  resolve_python_module_constant \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$active_runtime_closure_projection_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-active-runtime-doc.json; then
  echo "[FAIL] negative active-runtime projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative active-runtime projection doc anchor probe fail-closed as expected"

cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

repo_global_closure_owner_lane_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES[0]"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$repo_global_closure_owner_lane_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-repo-global-owner-lane-doc.json; then
  echo "[FAIL] negative repo-global owner-lane doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global owner-lane doc anchor probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

required_gate_bundle_scope_marker="$(
  resolve_python_module_expression \
    "release_readiness_required_gate_bundle_scope_common" \
    "RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS[0]"
)"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_check.py" \
  'build_scope_excluded_required_gate_bundle_summary('

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-bundle-script.json; then
  echo "[FAIL] negative required-gate bundle scope script probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative required-gate bundle scope script probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$required_gate_bundle_scope_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-bundle-doc.json; then
  echo "[FAIL] negative required-gate bundle scope doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative required-gate bundle scope doc probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/release_readiness_one_look_projection_common.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_required_gate_bundle_one_look(summary, one_look)'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-bundle-one-look-script.json; then
  echo "[FAIL] negative required-gate bundle one-look script probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative required-gate bundle one-look script probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

required_gate_bundle_projection_marker="$(
  resolve_python_module_constant \
    "release_readiness_required_gate_bundle_projection_common" \
    "RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$required_gate_bundle_projection_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-bundle-one-look-doc.json; then
  echo "[FAIL] negative required-gate bundle one-look doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative required-gate bundle one-look doc probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

selected_check_scope_marker="$(
  resolve_python_module_expression \
    "release_readiness_selected_check_scope_common" \
    "RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS[0]"
)"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_check.py" \
  'materialize_targeted_subset_selected_check_scope_exclusions('

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-selected-check-scope-script.json; then
  echo "[FAIL] negative selected-check scope script probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative selected-check scope script probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$selected_check_scope_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-selected-check-scope-doc.json; then
  echo "[FAIL] negative selected-check scope doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative selected-check scope doc probe fail-closed as expected"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-doc.json; then
  echo "[FAIL] negative doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative doc anchor probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "resume_capture_mode=stable_prewrite_snapshot"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-summary-lifecycle-doc.json; then
  echo "[FAIL] negative release-readiness lifecycle doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative release-readiness lifecycle doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "scripts/run_workspace_runtime_closure_checks.py"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-workspace-runtime-runner-doc.json; then
  echo "[FAIL] negative workspace-runtime closure runner doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative workspace-runtime closure runner doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

repo_global_prefix_one_look_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS[1]"
)"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "$repo_global_prefix_one_look_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-repo-global-doc.json; then
  echo "[FAIL] negative repo-global prefix one-look projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global prefix one-look projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

repo_global_tail_one_look_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_ONE_LOOK_MARKERS[-1]"
)"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "$repo_global_tail_one_look_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-runtime-shadow-repo-global-doc.json; then
  echo "[FAIL] negative repo-global tail one-look projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative repo-global tail one-look projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.required_gate_surface_drift_probe_status"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-required-gate-governance-probe-doc.json; then
  echo "[FAIL] negative required-gate governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative required-gate governance projection doc probe fail-closed as expected"

cp scripts/release_readiness_runtime_closure_convergence_common.py "$tmpdir/scripts/"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.active_execution_report_pointer_external_authority_class"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-active-pointer-authority-class-doc.json; then
  echo "[FAIL] negative active pointer authority-class governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative active pointer authority-class governance projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.strict_live_active_pointer_candidate_root_resolution_mode"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-strict-live-pointer-detail-doc.json; then
  echo "[FAIL] negative strict-live pointer detail governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative strict-live pointer detail governance projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.strict_live_contract_resolution_sample_green_failclose_status"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-strict-live-contract-resolution-detail-doc.json; then
  echo "[FAIL] negative strict-live contract-resolution detail governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative strict-live contract-resolution detail governance projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.execution_report_selection_convergence_candidate_count"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-exec-report-convergence-detail-doc.json; then
  echo "[FAIL] negative execution-report convergence detail governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative execution-report convergence detail governance projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.identity_codex_launcher_convergence_repaired_identity_count"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-launcher-convergence-detail-doc.json; then
  echo "[FAIL] negative launcher convergence detail governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative launcher convergence detail governance projection doc probe fail-closed as expected"

cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"

mutate_probe_literal \
  "$tmpdir/docs/release/identity-v1.6x-release-closure-summary.md" \
  "one_look.identity_transport_fleet_closure_convergence_probe_status"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-transport-convergence-governance-probe-doc.json; then
  echo "[FAIL] negative transport-fleet convergence governance projection doc probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative transport-fleet convergence governance projection doc probe fail-closed as expected"

mutate_probe_literal \
  "$tmpdir/scripts/release_readiness_runtime_closure_convergence_common.py" \
  "scripts/run_workspace_runtime_closure_checks.py"

if PYTHONPATH="$tmpdir/scripts:$repo_root/scripts${PYTHONPATH:+:$PYTHONPATH}" \
  python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-workspace-runtime-runner-payload.json; then
  echo "[FAIL] negative workspace-runtime closure runner payload probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative workspace-runtime closure runner payload probe fail-closed as expected"

cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md "$tmpdir/docs/review/"

mutate_probe_literal \
  "$tmpdir/scripts/render_protocol_lane_audit_summary.py" \
  '"surface_governance": build_governed_runtime_summary_surface_payload("protocol_lane_audit_summary"),'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-lane-script.json; then
  echo "[FAIL] negative lane-summary script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative lane-summary script drift probe fail-closed as expected"

cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-codex-launcher-governance-v1.6.14.md" \
  "The renderer must self-describe this bounded authority in machine-readable payload form."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-lane-doc.json; then
  echo "[FAIL] negative lane-summary doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative lane-summary doc anchor probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/full_identity_protocol_scan.py" \
  '"scan_projection_profile"'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-projection-script.json; then
  echo "[FAIL] negative full-scan projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan projection script drift probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  '`scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection`'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-projection-doc.json; then
  echo "[FAIL] negative full-scan projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan projection doc anchor probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/full_identity_protocol_scan.py" \
  "apply_full_scan_required_gate_bundle_three_plane_projection("

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-required-gate-script.json; then
  echo "[FAIL] negative full-scan required-gate projection script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan required-gate projection script drift probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

full_scan_required_gate_projection_marker="$(
  resolve_python_module_constant \
    "full_scan_required_gate_bundle_projection_common" \
    "FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER"
)"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  "$full_scan_required_gate_projection_marker"

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-required-gate-doc.json; then
  echo "[FAIL] negative full-scan required-gate projection doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan required-gate projection doc anchor probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/full_identity_protocol_scan.py" \
  'payload["surface_governance"] = build_governed_runtime_summary_surface_payload("full_identity_protocol_scan_summary")'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-script.json; then
  echo "[FAIL] negative full-scan script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan script drift probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-v1.6x-release-closure-governance.md" \
  '`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-doc.json; then
  echo "[FAIL] negative full-scan doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan doc anchor probe fail-closed as expected"

cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/render_control_plane_status.py" \
  '        "surface_governance": build_governed_runtime_summary_surface_payload("control_plane_status_artifact"),'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-control-plane-script.json; then
  echo "[FAIL] negative control-plane status script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane status script drift probe fail-closed as expected"

cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/github-native-control-plane-specialization-v1.6.3.md" \
  "The renderer must self-describe this bounded authority in machine-readable payload form."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-control-plane-doc.json; then
  echo "[FAIL] negative control-plane status doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane status doc anchor probe fail-closed as expected"

cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/render_control_plane_budget.py" \
  '"surface_governance": build_governed_runtime_summary_surface_payload("control_plane_budget_artifact")'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-budget-script.json; then
  echo "[FAIL] negative control-plane budget script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane budget script drift probe fail-closed as expected"

cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/github-native-control-plane-specialization-v1.6.3.md" \
  '`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.'

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-budget-doc.json; then
  echo "[FAIL] negative control-plane budget doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane budget doc anchor probe fail-closed as expected"

cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/render_identity_context_continuity_bundle.py" \
  '        "surface_governance": build_governed_runtime_summary_surface_payload(' \
  '        "surface_governance_removed": build_governed_runtime_summary_surface_payload('

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-continuity-script.json; then
  echo "[FAIL] negative continuity bundle script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative continuity bundle script drift probe fail-closed as expected"

cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-context-continuity-governance-v1.6.16.md" \
  "Both renderers must self-describe this bounded authority in machine-readable payload form."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-continuity-doc.json; then
  echo "[FAIL] negative continuity bundle doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative continuity bundle doc anchor probe fail-closed as expected"

cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

mutate_probe_literal \
  "$tmpdir/scripts/render_identity_context_reentry_answers.py" \
  '        "surface_governance": build_governed_runtime_summary_surface_payload(' \
  '        "surface_governance_removed": build_governed_runtime_summary_surface_payload('

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-reentry-script.json; then
  echo "[FAIL] negative reentry answer script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative reentry answer script drift probe fail-closed as expected"

cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

mutate_probe_literal \
  "$tmpdir/docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md" \
  "Neither surface may become a new terminal command family, thread-UUID lookup authority, or raw-transcript authority."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-reentry-doc.json; then
  echo "[FAIL] negative reentry answer doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative reentry answer doc anchor probe fail-closed as expected"

cp scripts/render_identity_codex_launcher.py "$tmpdir/scripts/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/scripts/render_identity_codex_launcher.py" \
  '        "surface_governance": build_governed_runtime_summary_surface_payload(' \
  '        "surface_governance_removed": build_governed_runtime_summary_surface_payload('

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-launcher-command-script.json; then
  echo "[FAIL] negative launcher command bundle script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative launcher command bundle script drift probe fail-closed as expected"

cp scripts/render_identity_codex_launcher.py "$tmpdir/scripts/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"

mutate_probe_literal \
  "$tmpdir/docs/governance/identity-codex-launcher-governance-v1.6.14.md" \
  "The command-bundle payload must self-describe this bounded authority in machine-readable form."

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-launcher-command-doc.json; then
  echo "[FAIL] negative launcher command bundle doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative launcher command bundle doc anchor probe fail-closed as expected"

python3 - <<'PY'
from __future__ import annotations

import json

print(json.dumps({
    "runtime_summary_surface_governance_probe_status": "PASS_REQUIRED",
    "positive_validator_output": "/tmp/runtime-summary-surface-governance-positive.json",
}, ensure_ascii=False))
PY

echo "[PASS] runtime summary surface governance probes passed"
