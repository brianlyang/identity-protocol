#!/usr/bin/env bash
set -euo pipefail
# strict-actor-entry-exemption: probe_fixture_literals_allowed
# This probe mutates copied fixture files to verify fail-close governance drift,
# so script-path literals here are fixture inputs rather than live strict-entry launches.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"
export PROBE_FIXTURE_REPO_ROOT="$repo_root"
source "${repo_root}/scripts/probe_fixture_shell_common.sh"
source "${repo_root}/scripts/ci/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts"
  "docs"
  "identity"
  ".github"
)

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts:${repo_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 scripts/validate_required_gate_surface_drift.py \
      --repo-root "$shadow_root" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${repo_root}/${rel_path}" "${shadow_root}/${rel_path}"
}

echo "[INFO] positive: required gate surface drift validator"
python3 scripts/validate_required_gate_surface_drift.py --json-only >/tmp/required-gate-surface-drift-positive.json

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

probe_mirror_relpaths_only "$repo_root" "$tmpdir" "${PROBE_REL_PATHS[@]}"

restore_shadow_file "$tmpdir" "scripts/ci/run_required_runtime_gates_ci.sh"
# expected fail-close: required_gate_workspace_runtime_runner_missing:--repo-catalog
mutate_probe_literal \
  "$tmpdir/scripts/ci/run_required_runtime_gates_ci.sh" \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --json-only' \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --json-only'
if run_shadow_validator "$tmpdir" /tmp/required-gate-surface-drift-negative-missing-repo-catalog.json; then
  echo "[FAIL] missing repo-catalog probe unexpectedly passed"
  exit 1
fi
echo "[PASS] missing repo-catalog probe fail-closed as expected"

restore_shadow_file "$tmpdir" "scripts/ci/run_required_runtime_gates_ci.sh"
# expected fail-close: required_gate_workspace_runtime_runner_forbidden_selector:--family
mutate_probe_literal \
  "$tmpdir/scripts/ci/run_required_runtime_gates_ci.sh" \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --json-only' \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --family launcher --json-only'
if run_shadow_validator "$tmpdir" /tmp/required-gate-surface-drift-negative-family-selector.json; then
  echo "[FAIL] forbidden family selector probe unexpectedly passed"
  exit 1
fi
echo "[PASS] forbidden family selector probe fail-closed as expected"

restore_shadow_file "$tmpdir" "scripts/ci/run_required_runtime_gates_ci.sh"
# expected fail-close: required_gate_workspace_runtime_runner_forbidden_selector:--checker-id
mutate_probe_literal \
  "$tmpdir/scripts/ci/run_required_runtime_gates_ci.sh" \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --json-only' \
  'run_cmd python3 scripts/run_workspace_runtime_closure_checks.py --catalog "${CATALOG_PATH}" --repo-catalog "${REPO_CATALOG_PATH}" --checker-id scripts/check_identity_codex_launcher_migration_closure.py --json-only'
if run_shadow_validator "$tmpdir" /tmp/required-gate-surface-drift-negative-checker-selector.json; then
  echo "[FAIL] forbidden checker-id selector probe unexpectedly passed"
  exit 1
fi
echo "[PASS] forbidden checker-id selector probe fail-closed as expected"

restore_shadow_file "$tmpdir" "scripts/workspace_runtime_closure_command_common.py"
mutate_probe_literal \
  "$tmpdir/scripts/workspace_runtime_closure_command_common.py" \
  'workspace_runtime_runner_selector_policy=full_surface_non_shrinkable' \
  'workspace_runtime_runner_selector_policy=selector_drifted'
if run_shadow_validator "$tmpdir" /tmp/required-gate-surface-drift-negative-selector-policy-common.json; then
  echo "[FAIL] selector policy common drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] selector policy common drift probe fail-closed as expected"

restore_shadow_file "$tmpdir" "scripts/ci/run_required_gate_surface_drift_probes_ci.sh"
mutate_probe_literal \
  "$tmpdir/scripts/ci/run_required_gate_surface_drift_probes_ci.sh" \
  'required_gate_workspace_runtime_runner_forbidden_selector:--family'
if run_shadow_validator "$tmpdir" /tmp/required-gate-surface-drift-negative-probe-script.json; then
  echo "[FAIL] required gate drift probe script self-check unexpectedly passed"
  exit 1
fi
echo "[PASS] required gate drift probe script self-check fail-closed as expected"

python3 - <<'PY'
from __future__ import annotations

import json

print(json.dumps({
    "required_gate_surface_drift_probe_status": "PASS_REQUIRED",
    "positive_validator_output": "/tmp/required-gate-surface-drift-positive.json",
}, ensure_ascii=False))
PY

echo "[PASS] required gate surface drift probes passed"
