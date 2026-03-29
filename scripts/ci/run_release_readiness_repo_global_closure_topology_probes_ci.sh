#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"

repo_global_topology_validator="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT"
)"
repo_global_topology_probe="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT"
)"
repo_global_topology_validator_command_literal="[\"python3\", \"${repo_global_topology_validator}\", \"--json-only\"],"
repo_global_topology_probe_command_literal="[\"bash\", \"${repo_global_topology_probe}\"],"
repo_global_topology_probe_summary_key="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY"
)"
repo_global_topology_probe_one_look_field="$(
  resolve_python_module_expression \
    "release_readiness_repo_global_closure_projection_common" \
    "RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD"
)"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${repo_global_topology_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="/tmp/release-readiness-repo-global-closure-topology-positive.json"
echo "[INFO] positive: release-readiness repo-global closure topology validator"
python3 "${repo_global_topology_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_repo_global_closure_topology_status"] == "PASS_REQUIRED", payload
assert payload["repo_global_lane_count"] == 11, payload
assert payload["stale_reasons"] == [], payload
PY

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-repo-global-closure-topology-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_repo_global_closure_projection_common.py"
# expected fail-close: repo_global_closure_summary_keys_not_unique
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_repo_global_closure_projection_common.py" \
  'summary_key="version_baseline_migration_closure"' \
  'summary_key="unique_entry_contract_migration_closure"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-key.json; then
  echo "[FAIL] repo-global closure summary-key drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global closure summary-key drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_repo_global_closure_projection_common.py"
# expected fail-close: repo_global_closure_one_look_field_order_changed
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_repo_global_closure_projection_common.py" \
  'one_look_field="version_baseline_migration_closure_status"' \
  'one_look_field="version_baseline_migration_closure_state"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-one-look-field.json; then
  echo "[FAIL] repo-global closure one-look field drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global closure one-look field drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_repo_global_capture_map_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_repo_global_closure_capture_script_map(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-capture-map.json; then
  echo "[FAIL] repo-global capture-map injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global capture-map injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_repo_global_structured_capture_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_repo_global_closure_structured_capture_specs(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-structured-capture.json; then
  echo "[FAIL] repo-global structured-capture injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global structured-capture injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_repo_global_summary_defaults_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_repo_global_closure_summary_defaults(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-defaults.json; then
  echo "[FAIL] repo-global summary-default injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global summary-default injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_validator:scripts/validate_release_readiness_repo_global_closure_topology.py --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${repo_global_topology_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-missing-validator-command.json; then
  echo "[FAIL] repo-global topology validator command drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global topology validator command drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_probe:scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${repo_global_topology_probe_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-missing-probe-command.json; then
  echo "[FAIL] repo-global topology probe command drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global topology probe command drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
# expected fail-close: repo_global_summary_probe_missing_projection_marker_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_summary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"' \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-projection.json; then
  echo "[FAIL] repo-global summary probe projection resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global summary probe projection resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
# expected fail-close: repo_global_summary_probe_missing_checked_count_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_summary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD"' \
  '"RELEASE_READINESS_REPO_GLOBAL_BROADCAST_CHECKED_IDENTITY_COUNT_FIELD"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-checked-count.json; then
  echo "[FAIL] repo-global summary probe checked-count resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global summary probe checked-count resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
# expected fail-close: repo_global_summary_probe_missing_topology_lane_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_summary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT"' \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-topology-lane.json; then
  echo "[FAIL] repo-global summary probe topology-lane resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global summary probe topology-lane resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
# expected fail-close: repo_global_boundary_probe_missing_projection_marker_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER"' \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-boundary-projection.json; then
  echo "[FAIL] repo-global boundary probe projection resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global boundary probe projection resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
# expected fail-close: repo_global_boundary_probe_missing_checked_count_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD"' \
  '"RELEASE_READINESS_REPO_GLOBAL_BROADCAST_CHECKED_IDENTITY_COUNT_FIELD"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-boundary-checked-count.json; then
  echo "[FAIL] repo-global boundary probe checked-count resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global boundary probe checked-count resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
# expected fail-close: repo_global_boundary_probe_missing_topology_lane_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh" \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT"' \
  '"RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-boundary-topology-lane.json; then
  echo "[FAIL] repo-global boundary probe topology-lane resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global boundary probe topology-lane resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_repo_global_closure_projection_common.py"
# expected fail-close: governance_probe_projection_missing_one_look_field:one_look.release_readiness_repo_global_closure_topology_probe_status
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_repo_global_closure_projection_common.py" \
  '"release_readiness_repo_global_closure_topology_probe_status"' \
  '"release_readiness_repo_global_closure_topology_probe_state"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-governance-field.json; then
  echo "[FAIL] repo-global governance-probe absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global governance-probe absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
# expected fail-close: summary_binding_probe_missing_token:release_readiness_repo_global_closure_topology_probe
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_release_readiness_summary_binding_probes_ci.sh" \
  "${repo_global_topology_probe_summary_key}" \
  'release_readiness_repo_global_closure_topology'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-summary-binding.json; then
  echo "[FAIL] repo-global summary-binding absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global summary-binding absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "${repo_global_topology_probe}"
mutate_probe_literal \
  "${TMP_ROOT}/${repo_global_topology_probe}" \
  'repo_global_topology_probe_summary_key=' \
  'repo_global_topology_probe_summary_guard='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-repo-global-closure-topology-negative-probe-self-check.json; then
  echo "[FAIL] repo-global topology probe self-check unexpectedly passed"
  exit 1
fi
echo "[PASS] repo-global topology probe self-check fail-closed as expected"

python3 - "${POSITIVE_JSON}" "${repo_global_topology_probe_one_look_field}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

print(json.dumps({
    sys.argv[2]: "PASS_REQUIRED",
    "positive_validator_output": str(pathlib.Path(sys.argv[1]).resolve()),
}, ensure_ascii=False))
PY

echo "[PASS] release-readiness repo-global closure topology probes passed"
