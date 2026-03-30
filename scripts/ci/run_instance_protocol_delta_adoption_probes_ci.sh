#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT="${TMPDIR:-$REPO_ROOT/.tmp}"
mkdir -p "$TMP_ROOT"
WORK_ROOT="$(mktemp -d "$TMP_ROOT/instance-protocol-delta-adoption-probes.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

VALIDATOR="$REPO_ROOT/scripts/validate_instance_protocol_delta_adoption.py"
GOV_DOC_REL="docs/governance/identity-instance-protocol-delta-adoption-governance-v1.6.x.md"
REV_DOC_REL="docs/review/protocol-remediation-audit-ledger-v1.6.x-instance-protocol-delta-adoption.md"

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
  "last_adopted_protocol_commit" \
  "last_adopted_protocol_commit_removed"
run_expect_fail "$missing_field_dir" "missing required adoption field"

semantic_phrase_dir="$WORK_ROOT/semantic-phrase-loss"
setup_case "$semantic_phrase_dir"
mutate_replace \
  "$semantic_phrase_dir/$REV_DOC_REL" \
  "Protocol authority must resolve to a single authoritative protocol root before adoption can pass." \
  "Protocol authority may be approximated from local memory when adoption runs."
run_expect_fail "$semantic_phrase_dir" "semantic phrase loss"

mode_loss_dir="$WORK_ROOT/mode-loss"
setup_case "$mode_loss_dir"
mutate_replace \
  "$mode_loss_dir/$GOV_DOC_REL" \
  "protocol_owner_surface_not_ready" \
  "protocol_owner_surface_not_ready_removed"
run_expect_fail "$mode_loss_dir" "required adoption mode loss"

fixed_write_set_dir="$WORK_ROOT/fixed-write-set-expansion"
setup_case "$fixed_write_set_dir"
mutate_replace \
  "$fixed_write_set_dir/$REV_DOC_REL" \
  '"scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh"' \
  '"scripts/ci/run_instance_protocol_delta_adoption_probes_ci.sh",\n    "scripts/unexpected_extra.py"'
run_expect_fail "$fixed_write_set_dir" "fixed write set expansion"

echo "PASS"
