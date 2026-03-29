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

philosophy_ref_marker="$(
  resolve_python_module_expression \
    "release_closure_doc_reference_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_PHILOSOPHY_REFERENCE_MARKER"
)"
contract_binding_ref_marker="$(
  resolve_python_module_expression \
    "release_closure_doc_reference_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_CONTRACT_BINDING_REFERENCE_MARKER"
)"
workbook_ref_marker="$(
  resolve_python_module_expression \
    "release_closure_doc_reference_bundle_common" \
    "RELEASE_CLOSURE_SUMMARY_WORKBOOK_REFERENCE_MARKER"
)"

printf '[RUN] positive release-closure summary doc-reference bundle validation\n'
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

mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${philosophy_ref_marker}" "identity/protocol/IDENTITY_PROTOCOL_DESIGN_OUTLINE.md"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${contract_binding_ref_marker}" "identity/protocol/mappings/contract-binding.next.yaml"
mutate_probe_literal "${SUMMARY_SHADOW_PATH}" "${workbook_ref_marker}" "docs/workbook/protocol-deep-audit-workbook-v1.6-draft.md"

printf '[RUN] negative release-closure summary doc-reference bundle validation\n'
if python3 "${REPO_ROOT}/scripts/validate_v16x_release_closure_summary.py" --repo-root "${SHADOW_ROOT}" --json-only > "${NEGATIVE_JSON}"; then
  echo '[FAIL] negative release-closure summary doc-reference bundle probe must fail'
  exit 1
fi

python3 - <<'PY' \
  "${POSITIVE_JSON}" \
  "${NEGATIVE_JSON}" \
  "${philosophy_ref_marker}" \
  "${contract_binding_ref_marker}" \
  "${workbook_ref_marker}"
import json
import sys
from pathlib import Path

positive = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
negative = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))

if positive.get("v16x_release_closure_summary_status") != "PASS_REQUIRED":
    raise SystemExit("positive release-closure summary doc-reference bundle status must PASS_REQUIRED")
if negative.get("v16x_release_closure_summary_status") != "FAIL_REQUIRED":
    raise SystemExit("negative release-closure summary doc-reference bundle status must FAIL_REQUIRED")

reasons = set(negative.get("stale_reasons") or [])
expected_reasons = {
    f"summary_doc_missing_required_ref:{sys.argv[3]}",
    f"summary_doc_missing_required_ref:{sys.argv[4]}",
    f"summary_doc_missing_required_ref:{sys.argv[5]}",
}
missing = sorted(expected_reasons - reasons)
if missing:
    raise SystemExit(
        "negative release-closure summary doc-reference bundle probe is missing expected stale reasons: "
        + ", ".join(missing)
    )
PY

echo "[PASS] v1.6.x release closure summary doc-reference bundle probes passed"
