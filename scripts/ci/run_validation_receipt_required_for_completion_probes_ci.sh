#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT="${TMPDIR:-$REPO_ROOT/.tmp}"
mkdir -p "$TMP_ROOT"
WORK_ROOT="$(mktemp -d "$TMP_ROOT/validation-receipt-required-for-completion-probes.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

VALIDATOR="$REPO_ROOT/scripts/validate_validation_receipt_required_for_completion_contract.py"
GOV_DOC_REL="docs/governance/identity-validation-receipt-required-for-completion-governance-v1.6.x.md"
REV_DOC_REL="docs/review/protocol-remediation-audit-ledger-v1.6.x-validation-receipt-required-for-completion.md"

run_expect_pass() {
  TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$1" --json-only >/dev/null
}

run_expect_fail() {
  if TMPDIR="$TMP_ROOT" python3 "$VALIDATOR" --repo-root "$1" --json-only >/dev/null 2>&1; then
    echo "expected validator failure for case: $2" >&2
    exit 1
  fi
}

setup_case() {
  local case_dir="$1"
  mkdir -p "$case_dir/docs/governance" "$case_dir/docs/review"
  cp "$REPO_ROOT/$GOV_DOC_REL" "$case_dir/$GOV_DOC_REL"
  cp "$REPO_ROOT/$REV_DOC_REL" "$case_dir/$REV_DOC_REL"
}

mutate_replace() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"
  python3 - "$target" "$old_text" "$new_text" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
old_text = sys.argv[2]
new_text = sys.argv[3]
text = path.read_text(encoding="utf-8")
if old_text not in text:
    raise SystemExit(f"missing mutation needle: {old_text}")
path.write_text(text.replace(old_text, new_text, 1), encoding="utf-8")
PY
}

baseline_dir="$WORK_ROOT/baseline"
setup_case "$baseline_dir"
run_expect_pass "$baseline_dir"

missing_field_dir="$WORK_ROOT/missing-field"
setup_case "$missing_field_dir"
mutate_replace \
  "$missing_field_dir/$GOV_DOC_REL" \
  "validator_receipt_status" \
  "validator_receipt_status_removed"
run_expect_fail "$missing_field_dir" "missing required validation field"

semantic_phrase_dir="$WORK_ROOT/semantic-phrase-loss"
setup_case "$semantic_phrase_dir"
mutate_replace \
  "$semantic_phrase_dir/$REV_DOC_REL" \
  "Completion claims without admitted validation evidence are not admitted." \
  "Completion claims without admitted validation evidence may proceed with broad confidence."
run_expect_fail "$semantic_phrase_dir" "semantic phrase loss"

fixed_write_set_dir="$WORK_ROOT/fixed-write-set-expansion"
setup_case "$fixed_write_set_dir"
mutate_replace \
  "$fixed_write_set_dir/$GOV_DOC_REL" \
  '"scripts/ci/run_validation_receipt_required_for_completion_probes_ci.sh"' \
  '"scripts/ci/run_validation_receipt_required_for_completion_probes_ci.sh",\n    "scripts/unexpected_extra.py"'
run_expect_fail "$fixed_write_set_dir" "fixed write set expansion"

echo "PASS"
