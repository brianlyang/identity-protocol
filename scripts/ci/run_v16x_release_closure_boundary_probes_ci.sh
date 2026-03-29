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
repo_global_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"
)"
repo_global_checked_count_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS[0]"
)"
repo_global_topology_probe_marker="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROOF_LANES[-1]"
)"
active_runtime_projection_marker="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"
)"
post_closure_adjudication_order_marker="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER"
)"
release_closure_root_grounding_order_marker="$(
  resolve_python_module_expression \
    "release_closure_root_grounding_common" \
    "RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER"
)"
release_closure_root_grounding_lane_marker="$(
  resolve_python_module_expression \
    "release_closure_root_grounding_common" \
    "next(marker for marker in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_MARKERS if marker.endswith('protocol_root_error_terminality'))"
)"
release_closure_root_grounding_validator_path="$(
  resolve_python_module_expression \
    "release_closure_root_grounding_common" \
    "next(spec.validator_rel for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS if spec.lane_id == 'protocol_root_error_terminality')"
)"
release_closure_root_grounding_probe_path="$(
  resolve_python_module_expression \
    "release_closure_root_grounding_common" \
    "next(spec.probe_rel for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS if spec.lane_id == 'protocol_root_error_terminality')"
)"
terminal_truth_bridge_surface_marker="$(
  resolve_python_module_expression \
    "release_readiness_terminal_truth_bridge_common" \
    "RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER"
)"
terminal_truth_bridge_case_marker="$(
  resolve_python_module_expression \
    "release_readiness_terminal_truth_bridge_common" \
    "RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS[1]"
)"
terminal_truth_bridge_probe_marker="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_projection_common" \
    "'one_look.' + RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS[6]"
)"
active_runtime_terminal_truth_class_marker="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS[-1]"
)"

printf '[RUN] positive release-closure boundary validation\n'
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

python3 - <<'PY' "${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md" "${repo_global_projection_marker}" "${repo_global_checked_count_marker}" "${repo_global_topology_probe_marker}" "${active_runtime_projection_marker}" "${terminal_truth_bridge_surface_marker}" "${terminal_truth_bridge_case_marker}" "${terminal_truth_bridge_probe_marker}" "${active_runtime_terminal_truth_class_marker}" "${post_closure_adjudication_order_marker}" "${release_closure_root_grounding_order_marker}" "${release_closure_root_grounding_lane_marker}" "${release_closure_root_grounding_validator_path}" "${release_closure_root_grounding_probe_path}"
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve()
repo_global_projection_marker = sys.argv[2]
repo_global_checked_count_marker = sys.argv[3]
repo_global_topology_probe_marker = sys.argv[4]
active_runtime_projection_marker = sys.argv[5]
terminal_truth_bridge_surface_marker = sys.argv[6]
terminal_truth_bridge_case_marker = sys.argv[7]
terminal_truth_bridge_probe_marker = sys.argv[8]
active_runtime_terminal_truth_class_marker = sys.argv[9]
post_closure_adjudication_order_marker = sys.argv[10]
release_closure_root_grounding_order_marker = sys.argv[11]
release_closure_root_grounding_lane_marker = sys.argv[12]
release_closure_root_grounding_validator_path = sys.argv[13]
release_closure_root_grounding_probe_path = sys.argv[14]
text = path.read_text(encoding="utf-8")
text = text.replace("`ISSUE-001` through `ISSUE-039`", "`ISSUE-001` through `ISSUE-038`")
text = text.replace("`v1.6.21`", "`v1.6.20`")
text = text.replace("creator/update admission lane", "update lane")
text = text.replace("summary_terminal_truth_boundary", "summary boundary aggregate")
text = text.replace("stable prewrite snapshot", "stable resume snapshot")
text = text.replace("caller cwd", "caller working directory")
text = text.replace("scripts/run_workspace_runtime_closure_checks.py", "scripts/run_workspace_runtime_pack_checks.py")
text = text.replace(
    repo_global_projection_marker,
    "repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status|one_look.repo_global_drift_marker",
)
text = text.replace(
    repo_global_checked_count_marker,
    "one_look.repo_global_checked_identity_count",
)
text = text.replace(
    repo_global_topology_probe_marker,
    "scripts/ci/run_repo_global_closure_topology_probes_ci.sh",
)
text = text.replace(
    terminal_truth_bridge_surface_marker,
    "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",
)
text = text.replace(terminal_truth_bridge_case_marker, "terminal_truth_bridge_case=review_required_execution")
text = text.replace(f"{terminal_truth_bridge_probe_marker}|", "")
text = text.replace(
    post_closure_adjudication_order_marker,
    "release_readiness_post_closure_adjudication_order=runtime_summary_surface_governance|terminal_truth_bridge",
)
text = text.replace(
    release_closure_root_grounding_order_marker,
    "release_closure_root_grounding_order=protocol_root_corpus_precedence|protocol_root_current_truth_epistemology",
)
text = text.replace(
    release_closure_root_grounding_lane_marker,
    "release_closure_root_grounding_lane=protocol_root_current_truth_epistemology",
    1,
)
text = text.replace(
    release_closure_root_grounding_validator_path,
    "scripts/validate_protocol_root_current_truth_epistemology.py",
    1,
)
text = text.replace(
    release_closure_root_grounding_probe_path,
    "scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
    1,
)
text = text.replace(
    active_runtime_projection_marker,
    "active_runtime_closure_projection=one_look.identity_codex_launcher_status",
)
text = text.replace(
    active_runtime_terminal_truth_class_marker,
    "one_look.identity_terminal_truth_kind",
)
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure boundary validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}" "${repo_global_projection_marker}" "${repo_global_checked_count_marker}" "${repo_global_topology_probe_marker}" "${active_runtime_projection_marker}" "${terminal_truth_bridge_surface_marker}" "${terminal_truth_bridge_case_marker}" "${terminal_truth_bridge_probe_marker}" "${active_runtime_terminal_truth_class_marker}" "${post_closure_adjudication_order_marker}" "${release_closure_root_grounding_order_marker}" "${release_closure_root_grounding_lane_marker}" "${release_closure_root_grounding_validator_path}" "${release_closure_root_grounding_probe_path}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
repo_global_projection_marker = sys.argv[3]
repo_global_checked_count_marker = sys.argv[4]
repo_global_topology_probe_marker = sys.argv[5]
active_runtime_projection_marker = sys.argv[6]
terminal_truth_bridge_surface_marker = sys.argv[7]
terminal_truth_bridge_case_marker = sys.argv[8]
terminal_truth_bridge_probe_marker = sys.argv[9]
active_runtime_terminal_truth_class_marker = sys.argv[10]

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary status must PASS_REQUIRED")
if positive.get("current_issue_horizon") != "ISSUE-039":
    raise SystemExit("positive release-closure boundary must track ISSUE-039 horizon")
if positive.get("highest_closed_v16_stream_version") != "v1.6.21":
    raise SystemExit("positive release-closure boundary must track highest closed v1.6 stream")

if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary status must FAIL_REQUIRED")
reasons = set(negative.get("stale_reasons") or [])
if "governance_doc_issue_horizon_mismatch" not in reasons:
    raise SystemExit("negative release-closure boundary must detect governance issue-horizon drift")
if "governance_doc_missing_highest_v16_stream_version" not in reasons:
    raise SystemExit("negative release-closure boundary must detect missing highest v1.6 stream version")
if "governance_doc_missing_terminal_truth_split_marker:creator/update admission lane" not in reasons:
    raise SystemExit("negative release-closure boundary must detect terminal-truth split marker drift")
if "governance_doc_missing_outer_surface_e2e_marker:summary_terminal_truth_boundary" not in reasons:
    raise SystemExit("negative release-closure boundary must detect outer-surface e2e marker drift")
if "governance_doc_missing_release_readiness_continuation_marker:stable prewrite snapshot" not in reasons:
    raise SystemExit("negative release-closure boundary must detect release-readiness continuation drift")
if "governance_doc_missing_release_readiness_continuation_marker:caller cwd" not in reasons:
    raise SystemExit("negative release-closure boundary must detect continuation cwd-anchor drift")
if "governance_doc_missing_workspace_runtime_closure_command_convergence_marker:scripts/run_workspace_runtime_closure_checks.py" not in reasons:
    raise SystemExit("negative release-closure boundary must detect workspace-runtime closure runner drift")
expected_repo_global_reason = f"governance_doc_missing_repo_global_closure_boundary_marker:{repo_global_projection_marker}"
if expected_repo_global_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect repo-global closure projection drift")
if "governance_doc_repo_global_closure_projection_line_not_canonical" not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect repo-global closure projection line drift"
    )
expected_repo_global_checked_count_reason = f"governance_doc_missing_repo_global_closure_boundary_marker:{repo_global_checked_count_marker}"
if expected_repo_global_checked_count_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect repo-global proof-strength companion drift")
expected_repo_global_topology_reason = f"governance_doc_missing_repo_global_closure_boundary_marker:{repo_global_topology_probe_marker}"
if expected_repo_global_topology_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect repo-global topology-proof lane drift")
if "governance_doc_stale_issue_horizon:ISSUE-038" not in reasons:
    raise SystemExit("negative release-closure boundary must detect stale issue-horizon drift")
expected_active_runtime_projection_reason = f"governance_doc_missing_active_runtime_closure_projection_marker:{active_runtime_projection_marker}"
if expected_active_runtime_projection_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect active-runtime closure projection drift")
if "governance_doc_active_runtime_closure_projection_line_not_canonical" not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect active-runtime closure projection line drift"
    )
expected_terminal_truth_bridge_surface_reason = f"governance_doc_missing_terminal_truth_bridge_marker:{terminal_truth_bridge_surface_marker}"
if expected_terminal_truth_bridge_surface_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect terminal-truth bridge surface drift")
expected_terminal_truth_bridge_case_reason = f"governance_doc_missing_terminal_truth_bridge_marker:{terminal_truth_bridge_case_marker}"
if expected_terminal_truth_bridge_case_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect terminal-truth bridge case drift")
if "governance_doc_governance_probe_projection_line_not_canonical" not in reasons:
    raise SystemExit("negative release-closure boundary must detect governance-probe projection line drift")
expected_active_runtime_detail_reason = f"governance_doc_missing_active_runtime_closure_projection_marker:{active_runtime_terminal_truth_class_marker}"
if expected_active_runtime_detail_reason not in reasons:
    raise SystemExit("negative release-closure boundary must detect active-runtime companion detail drift")
expected_post_closure_adjudication_reason = (
    f"governance_doc_missing_post_closure_adjudication_marker:{sys.argv[11]}"
)
if expected_post_closure_adjudication_reason not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect post-closure adjudication-order drift"
    )
expected_root_grounding_reason = (
    f"governance_doc_missing_release_closure_root_grounding_marker:{sys.argv[12]}"
)
if expected_root_grounding_reason not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect release-closure root grounding drift"
    )
expected_root_grounding_lane_reason = (
    f"governance_doc_missing_release_closure_root_grounding_marker:{sys.argv[13]}"
)
if expected_root_grounding_lane_reason not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect release-closure root grounding lane drift"
    )
expected_root_grounding_validator_reason = (
    f"governance_doc_missing_release_closure_root_grounding_marker:{sys.argv[14]}"
)
if expected_root_grounding_validator_reason not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect release-closure root grounding validator drift"
    )
expected_root_grounding_probe_reason = (
    f"governance_doc_missing_release_closure_root_grounding_marker:{sys.argv[15]}"
)
if expected_root_grounding_probe_reason not in reasons:
    raise SystemExit(
        "negative release-closure boundary must detect release-closure root grounding probe drift"
    )
PY

echo "[PASS] v1.6.x release closure boundary probes passed"
