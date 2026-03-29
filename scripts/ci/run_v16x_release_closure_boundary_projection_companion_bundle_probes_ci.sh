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

outer_surface_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_OUTER_SURFACE_E2E_COMPANION_MARKERS[0]"
)"
active_runtime_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_ACTIVE_RUNTIME_COMPANION_MARKERS[0]"
)"
terminal_truth_bridge_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKERS[0]"
)"
post_closure_adjudication_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKERS[0]"
)"
root_grounding_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_ROOT_GROUNDING_COMPANION_MARKERS[0]"
)"
repo_global_boundary_marker="$(
  resolve_python_module_expression \
    "release_closure_projection_companion_marker_bundle_common" \
    "RELEASE_CLOSURE_BOUNDARY_REPO_GLOBAL_COMPANION_MARKERS[0]"
)"

printf '[RUN] positive release-closure boundary projection-companion bundle validation\n'
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

mutate_probe_literal "${GOVERNANCE_SHADOW_PATH}" "${outer_surface_marker}" "scripts/ci/run_terminal_truth_boundary_e2e_probes_ci.sh"
mutate_probe_literal "${GOVERNANCE_SHADOW_PATH}" "${terminal_truth_bridge_marker}" "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status"
mutate_probe_literal "${GOVERNANCE_SHADOW_PATH}" "${repo_global_boundary_marker}" "repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status"
mutate_probe_literal "${REVIEW_SHADOW_PATH}" "${active_runtime_marker}" "active_runtime_closure_projection=one_look.identity_codex_launcher_status"
mutate_probe_literal "${REVIEW_SHADOW_PATH}" "${post_closure_adjudication_marker}" "release_readiness_post_closure_adjudication_order=runtime_summary_surface_governance|governance_probe_topology"
mutate_probe_literal "${REVIEW_SHADOW_PATH}" "${root_grounding_marker}" "release_closure_root_grounding_order=protocol_root_corpus_precedence"

printf '[RUN] negative release-closure boundary projection-companion bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary projection-companion bundle probe must fail'
  exit 1
fi

python3 - <<'PY' \
  "${POSITIVE_JSON}" \
  "${NEGATIVE_JSON}" \
  "${outer_surface_marker}" \
  "${active_runtime_marker}" \
  "${terminal_truth_bridge_marker}" \
  "${post_closure_adjudication_marker}" \
  "${root_grounding_marker}" \
  "${repo_global_boundary_marker}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary projection-companion bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary projection-companion bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    f"governance_doc_missing_outer_surface_e2e_marker:{sys.argv[3]}",
    f"review_doc_missing_active_runtime_closure_projection_marker:{sys.argv[4]}",
    f"governance_doc_missing_terminal_truth_bridge_marker:{sys.argv[5]}",
    f"review_doc_missing_post_closure_adjudication_marker:{sys.argv[6]}",
    f"review_doc_missing_release_closure_root_grounding_marker:{sys.argv[7]}",
    f"governance_doc_missing_repo_global_closure_boundary_marker:{sys.argv[8]}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure boundary projection-companion bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure boundary projection-companion bundle probes passed"
