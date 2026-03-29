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
PHILOSOPHY_SHADOW_PATH="${SHADOW_ROOT}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
GOVERNANCE_SHADOW_PATH="${SHADOW_ROOT}/docs/governance/identity-v1.6x-release-closure-governance.md"
REVIEW_SHADOW_PATH="${SHADOW_ROOT}/docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"

philosophy_order_marker="$(
  resolve_python_module_expression \
    "release_closure_foundational_marker_common" \
    "RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS[-1]"
)"
closure_class_marker="$(
  resolve_python_module_expression \
    "release_closure_foundational_marker_common" \
    "RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS[1]"
)"
terminal_truth_split_marker="$(
  resolve_python_module_expression \
    "release_closure_foundational_marker_common" \
    "RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS[2]"
)"

printf '[RUN] positive release-closure boundary foundational-bundle validation\n'
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
  "${PHILOSOPHY_SHADOW_PATH}" \
  "${philosophy_order_marker}" \
  "adjudication order"
mutate_probe_literal \
  "${GOVERNANCE_SHADOW_PATH}" \
  "${closure_class_marker}" \
  "machine closure"
mutate_probe_literal \
  "${REVIEW_SHADOW_PATH}" \
  "${terminal_truth_split_marker}" \
  "update lane"

printf '[RUN] negative release-closure boundary foundational-bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_boundary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure boundary foundational-bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_boundary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure boundary foundational-bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_boundary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure boundary foundational-bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "philosophy_root_order_markers_missing",
    "governance_doc_missing_root_machine_runtime_closure_markers",
    "review_doc_missing_terminal_truth_split_marker:creator/update admission lane",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure boundary foundational-bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure boundary foundational-bundle probes passed"
