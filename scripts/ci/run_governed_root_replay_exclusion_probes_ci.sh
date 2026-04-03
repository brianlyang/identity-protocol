#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_ROOT="${TMPDIR:-$REPO_ROOT/.tmp}"
mkdir -p "$TMP_ROOT"
WORK_ROOT="$(mktemp -d "$TMP_ROOT/governed-root-replay-exclusion-probes.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

VALIDATOR="$REPO_ROOT/scripts/validate_governed_root_replay_exclusion_contract.py"
GOV_DOC_REL="docs/governance/identity-governed-root-replay-exclusion-governance-v1.6.x.md"
REV_DOC_REL="docs/review/protocol-remediation-audit-ledger-v1.6.x-governed-root-replay-exclusion.md"

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
path.write_text(text.replace(old_text, new_text), encoding="utf-8")
PY
}

baseline_dir="$WORK_ROOT/baseline"
setup_case "$baseline_dir"
run_expect_pass "$baseline_dir"

missing_field_dir="$WORK_ROOT/missing-field"
setup_case "$missing_field_dir"
mutate_replace \
  "$missing_field_dir/$GOV_DOC_REL" \
  "governed_scratch_root" \
  "governed_scratch_root_removed"
run_expect_fail "$missing_field_dir" "missing required field"

governing_law_dir="$WORK_ROOT/governing-law-drift"
setup_case "$governing_law_dir"
mutate_replace \
  "$governing_law_dir/$REV_DOC_REL" \
  "nested_governed_root_replay_not_admitted__guard_must_not_overreach_live_runtime" \
  "nested_governed_root_replay_tolerated"
run_expect_fail "$governing_law_dir" "governing law drift"

fixed_write_set_dir="$WORK_ROOT/fixed-write-set-expansion"
setup_case "$fixed_write_set_dir"
mutate_replace \
  "$fixed_write_set_dir/$GOV_DOC_REL" \
  "\"scripts/ci/run_governed_root_replay_exclusion_probes_ci.sh\"" \
  "\"scripts/ci/run_governed_root_replay_exclusion_probes_ci.sh\",\n    \"scripts/unexpected_extra.py\""
run_expect_fail "$fixed_write_set_dir" "fixed write set expansion"

next_action_dir="$WORK_ROOT/next-action-drift"
setup_case "$next_action_dir"
mutate_replace \
  "$next_action_dir/$REV_DOC_REL" \
  "guard cleanup may delete only machine-admitted stale residue, never live runtime by heuristic overreach" \
  "guard cleanup may heuristically delete replay-shaped runtime trees"
run_expect_fail "$next_action_dir" "next action drift"

reopen_trigger_dir="$WORK_ROOT/reopen-trigger-expansion"
setup_case "$reopen_trigger_dir"
mutate_replace \
  "$reopen_trigger_dir/$GOV_DOC_REL" \
  "\"fixed_write_set insufficiency only\"" \
  "\"fixed_write_set insufficiency only\",\n    \"freeform reinterpretation\""
run_expect_fail "$reopen_trigger_dir" "reopen trigger expansion"

commit_gate_dir="$WORK_ROOT/commit-gate-drift"
setup_case "$commit_gate_dir"
mutate_replace \
  "$commit_gate_dir/$REV_DOC_REL" \
  "one isolated commit for ISSUE-041C only" \
  "multi-commit allowed for ISSUE-041C"
run_expect_fail "$commit_gate_dir" "commit gate drift"

semantic_phrase_dir="$WORK_ROOT/semantic-phrase-loss"
setup_case "$semantic_phrase_dir"
mutate_replace \
  "$semantic_phrase_dir/$REV_DOC_REL" \
  "Guard cleanup may delete only machine-admitted stale residue and must not overreach into live runtime by heuristic cleanup." \
  "Guard cleanup may heuristically prune replay-shaped runtime state."
run_expect_fail "$semantic_phrase_dir" "semantic phrase loss"

echo "PASS"
