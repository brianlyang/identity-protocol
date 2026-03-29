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

question_class_marker="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_QUESTION_CLASS_MARKERS[0]"
)"
scope_marker_a="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_SCOPE_SEPARATION_MARKERS[0]"
)"
scope_marker_b="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_SCOPE_SEPARATION_MARKERS[1]"
)"
release_tag_marker="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_RELEASE_TAG_BOUNDARY_MARKERS[0]"
)"
forbidden_marker_a="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_MARKERS[0]"
)"
forbidden_marker_b="$(
  resolve_python_module_expression \
    "release_closure_summary_framing_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_MARKERS[1]"
)"

printf '[RUN] positive release-closure summary framing bundle validation\n'
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

mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${question_class_marker}" "Question classes"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${scope_marker_a}" "runtime summary surface"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${scope_marker_b}" "fleet closure matrix"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${release_tag_marker}" "avoid assigning a release tag"

python3 - <<'PY' "${SUMMARY_SHADOW_PATH}" "${forbidden_marker_a}" "${forbidden_marker_b}"
from pathlib import Path
import sys

path = Path(sys.argv[1]).resolve()
text = path.read_text(encoding="utf-8")
text += "\n" + sys.argv[2] + "\n" + sys.argv[3] + "\n"
path.write_text(text, encoding="utf-8")
PY

printf '[RUN] negative release-closure summary framing bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary framing bundle probe must fail'
  exit 1
fi

python3 - <<'PY' "${POSITIVE_JSON}" "${NEGATIVE_JSON}" "${forbidden_marker_a}" "${forbidden_marker_b}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary framing bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary framing bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    "summary_doc_missing_question_class_section",
    "summary_doc_missing_scope_separation_markers",
    "summary_doc_missing_release_tag_boundary",
    f"summary_doc_contains_stale_marker:{sys.argv[3]}",
    f"summary_doc_contains_stale_marker:{sys.argv[4]}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary framing bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary framing bundle probes passed"
