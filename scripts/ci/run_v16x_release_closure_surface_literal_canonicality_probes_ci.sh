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

python3 - <<'PY' "${SHADOW_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md" "${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md" "${terminal_truth_bridge_surface_marker}" "${post_closure_adjudication_order_marker}"
from pathlib import Path
import sys

summary_path = Path(sys.argv[1]).resolve()
governance_path = Path(sys.argv[2]).resolve()
terminal_truth_bridge_surface_marker = sys.argv[3]
post_closure_adjudication_order_marker = sys.argv[4]

def mutate(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        terminal_truth_bridge_surface_marker,
        "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",
        1,
    )
    text = text.replace(
        post_closure_adjudication_order_marker,
        "release_readiness_post_closure_adjudication_order=runtime_summary_surface_governance|terminal_truth_bridge",
        1,
    )
    path.write_text(text, encoding="utf-8")

mutate(summary_path)
mutate(governance_path)
PY

printf '[RUN] negative release-closure literal-canonicality validations\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${SUMMARY_NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary literal-canonicality probe must fail'
  exit 1
fi
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${BOUNDARY_NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary literal-canonicality probe must fail'
  exit 1
fi

python3 - <<'PY' "${SUMMARY_POSITIVE_JSON}" "${SUMMARY_NEGATIVE_JSON}" "${BOUNDARY_POSITIVE_JSON}" "${BOUNDARY_NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

summary_positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
summary_negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
boundary_positive = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
boundary_negative = json.loads(Path(sys.argv[4]).read_text(encoding='utf-8'))

if summary_positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary status must PASS_REQUIRED")
if boundary_positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary status must PASS_REQUIRED")

summary_reasons = set(summary_negative.get("stale_reasons") or [])
boundary_reasons = set(boundary_negative.get("stale_reasons") or [])

for reason, message in (
    (
        "summary_doc_terminal_truth_bridge_surface_line_not_canonical",
        "negative release-closure summary must detect terminal-truth bridge line drift",
    ),
    (
        "summary_doc_post_closure_adjudication_order_line_not_canonical",
        "negative release-closure summary must detect post-closure adjudication-order line drift",
    ),
):
    if reason not in summary_reasons:
        raise SystemExit(message)

for reason, message in (
    (
        "governance_doc_terminal_truth_bridge_surface_line_not_canonical",
        "negative release-closure boundary must detect terminal-truth bridge line drift",
    ),
    (
        "governance_doc_post_closure_adjudication_order_line_not_canonical",
        "negative release-closure boundary must detect post-closure adjudication-order line drift",
    ),
):
    if reason not in boundary_reasons:
        raise SystemExit(message)
PY

echo "[PASS] v1.6.x release closure surface literal canonicality probes passed"
