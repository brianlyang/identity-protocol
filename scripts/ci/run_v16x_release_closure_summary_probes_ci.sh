#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "${TMP_ROOT}"' EXIT

POSITIVE_JSON="${TMP_ROOT}/positive.json"
NEGATIVE_JSON="${TMP_ROOT}/negative.json"
SHADOW_ROOT="${TMP_ROOT}/shadow-repo"

printf '[RUN] positive release-closure summary validation\n'
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

python3 - <<'PY' "${SHADOW_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md"
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve()
text = path.read_text(encoding="utf-8")
text = text.replace("`v1.6.21`", "`v1.6.20`")
text = text.replace("fleet-scope closure matrix", "fleet matrix")
text = text.replace("repair success != clean terminal truth", "repair success means clean terminal truth")
text = text.replace("summary_terminal_truth_boundary", "summary boundary aggregate")
text = text.replace("one_look.health_report_experience_writeback_projection_status", "one_look.health_projection_status")
text = text.replace("one_look.runtime_file_boundary_governance_status", "one_look.runtime_file_boundary_status")
text = text.replace("one_look.required_gate_bundle_report_selection_mode", "one_look.required_gate_bundle_selection_mode")
text = text.replace("three_plane.required_gate_bundle_report_selection_mode", "three_plane.required_gate_bundle_selection_mode")
text = text.replace("resume_capture_mode=stable_prewrite_snapshot", "resume_capture_mode=resume_snapshot")
text = text.replace("caller cwd", "caller working directory")
text = text.replace("scripts/run_workspace_runtime_closure_checks.py", "scripts/run_workspace_runtime_pack_checks.py")
text = text.replace(
    "active_runtime_closure_projection=one_look.identity_codex_launcher_status",
    "active_runtime_projection=one_look.identity_codex_launcher_status",
)
text = text.replace(
    "one_look.identity_terminal_truth_class",
    "one_look.identity_terminal_truth_kind",
)
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure summary validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary status must PASS_REQUIRED")
if positive.get("current_issue_horizon") != "ISSUE-039":
    raise SystemExit("positive release-closure summary must track ISSUE-039 horizon")
if positive.get("highest_closed_v16_stream_version") != "v1.6.21":
    raise SystemExit("positive release-closure summary must track highest closed v1.6 stream")

if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary status must FAIL_REQUIRED")
reasons = set(negative.get("stale_reasons") or [])
if "summary_doc_missing_highest_v16_stream_version" not in reasons:
    raise SystemExit("negative release-closure summary must detect missing highest v1.6 stream version")
if "summary_doc_missing_scope_separation_markers" not in reasons:
    raise SystemExit("negative release-closure summary must detect scope-separation marker drift")
if "summary_doc_missing_terminal_truth_split_marker:repair success != clean terminal truth" not in reasons:
    raise SystemExit("negative release-closure summary must detect terminal-truth split marker drift")
if "summary_doc_missing_outer_surface_e2e_marker:summary_terminal_truth_boundary" not in reasons:
    raise SystemExit("negative release-closure summary must detect outer-surface e2e marker drift")
if "summary_doc_missing_release_readiness_health_projection_marker:one_look.health_report_experience_writeback_projection_status" not in reasons:
    raise SystemExit("negative release-closure summary must detect release-readiness health projection drift")
if "summary_doc_missing_outer_surface_e2e_marker:one_look.runtime_file_boundary_governance_status" not in reasons:
    raise SystemExit("negative release-closure summary must detect runtime-shadow repo-global projection drift")
if "summary_doc_missing_full_scan_required_gate_projection_marker:three_plane.required_gate_bundle_report_selection_mode" not in reasons:
    raise SystemExit("negative release-closure summary must detect full-scan required-gate projection drift")
if "summary_doc_missing_release_readiness_lifecycle_marker:one_look.required_gate_bundle_report_selection_mode" not in reasons:
    raise SystemExit("negative release-closure summary must detect required-gate one-look authority drift")
if "summary_doc_missing_release_readiness_lifecycle_marker:resume_capture_mode=stable_prewrite_snapshot" not in reasons:
    raise SystemExit("negative release-closure summary must detect release-readiness lifecycle drift")
if "summary_doc_missing_release_readiness_lifecycle_marker:caller cwd" not in reasons:
    raise SystemExit("negative release-closure summary must detect continuation cwd-anchor drift")
if "summary_doc_missing_workspace_runtime_closure_command_convergence_marker:scripts/run_workspace_runtime_closure_checks.py" not in reasons:
    raise SystemExit("negative release-closure summary must detect workspace-runtime closure runner drift")
if "summary_doc_missing_active_runtime_closure_projection_marker:active_runtime_closure_projection=one_look.identity_codex_launcher_status|one_look.identity_context_continuity_status|one_look.identity_context_continuity_receipt_family_status|one_look.identity_reentry_brief_status|one_look.identity_reentry_consumption_status|one_look.protocol_dialogue_retention_status|one_look.artifact_family_routing_status|one_look.identity_broadcast_delivery_status|one_look.identity_communication_transport_status|one_look.identity_experience_writeback_status|one_look.identity_weak_live_linkage_status|one_look.identity_terminal_truth_cleanliness_status" not in reasons:
    raise SystemExit("negative release-closure summary must detect active-runtime closure projection drift")
if "summary_doc_missing_active_runtime_closure_projection_marker:one_look.identity_terminal_truth_class" not in reasons:
    raise SystemExit("negative release-closure summary must detect active-runtime companion detail drift")
PY

echo "[PASS] v1.6.x release closure summary probes passed"
