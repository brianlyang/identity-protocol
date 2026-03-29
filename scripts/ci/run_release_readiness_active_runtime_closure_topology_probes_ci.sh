#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"
# shellcheck source=./probe_runtime_tmp_common.sh
source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"

active_runtime_topology_validator="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_VALIDATOR_SCRIPT"
)"
active_runtime_topology_probe="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SCRIPT"
)"
active_runtime_topology_validator_command_literal="[\"python3\", \"${active_runtime_topology_validator}\", \"--json-only\"],"
active_runtime_topology_probe_command_literal="[\"bash\", \"${active_runtime_topology_probe}\"],"
active_runtime_topology_probe_summary_key="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_SUMMARY_KEY"
)"
active_runtime_topology_probe_one_look_field="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_ONE_LOOK_FIELD"
)"
active_runtime_topology_positive_output_rel="$(
  resolve_python_module_expression \
    "release_readiness_active_runtime_closure_projection_common" \
    "RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_PROBE_POSITIVE_OUTPUT_REL"
)"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${active_runtime_topology_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="${ROOT}/${active_runtime_topology_positive_output_rel}"
mkdir -p "$(dirname "${POSITIVE_JSON}")"
echo "[INFO] positive: release-readiness active-runtime closure topology validator"
python3 "${active_runtime_topology_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_active_runtime_closure_topology_status"] == "PASS_REQUIRED", payload
assert payload["active_runtime_lane_count"] == 12, payload
assert payload["stale_reasons"] == [], payload
PY

probe_runtime_tmp_bootstrap "${ROOT}" "release-readiness-active-runtime-closure-topology-probes" "run"
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_active_runtime_closure_projection_common.py"
# expected fail-close: active_runtime_closure_summary_keys_not_unique
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_active_runtime_closure_projection_common.py" \
  'summary_key="identity_terminal_truth_cleanliness"' \
  'summary_key="identity_weak_live_linkage"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-summary-key.json"; then
  echo "[FAIL] active-runtime closure summary-key drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime closure summary-key drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_active_runtime_closure_projection_common.py"
# expected fail-close: active_runtime_closure_one_look_field_order_changed
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_active_runtime_closure_projection_common.py" \
  'one_look_field="identity_terminal_truth_cleanliness_status"' \
  'one_look_field="identity_terminal_truth_cleanliness_state"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-one-look-field.json"; then
  echo "[FAIL] active-runtime closure one-look field drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime closure one-look field drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_capture_map_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_active_runtime_closure_capture_script_map(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-capture-map.json"; then
  echo "[FAIL] active-runtime capture-map injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime capture-map injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_structured_capture_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_active_runtime_closure_structured_capture_specs(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-structured-capture.json"; then
  echo "[FAIL] active-runtime structured-capture injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime structured-capture injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: release_readiness_check_missing_summary_defaults_injection
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '**release_readiness_active_runtime_closure_summary_defaults(),' \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-summary-defaults.json"; then
  echo "[FAIL] active-runtime summary-default injection drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime summary-default injection drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_validator:scripts/validate_release_readiness_active_runtime_closure_topology.py --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${active_runtime_topology_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-missing-validator-command.json"; then
  echo "[FAIL] active-runtime topology validator command drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime topology validator command drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_probe:scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${active_runtime_topology_probe_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-missing-probe-command.json"; then
  echo "[FAIL] active-runtime topology probe command drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime topology probe command drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"
# expected fail-close: active_runtime_summary_probe_missing_projection_marker_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_summary_probes_ci.sh" \
  '"RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER"' \
  '"RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-summary-probe-resolution.json"; then
  echo "[FAIL] active-runtime summary probe resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime summary probe resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"
# expected fail-close: active_runtime_boundary_probe_missing_detail_field_resolution
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh" \
  '"RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD"' \
  '"RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_ALIAS_SURFACE_FIELD"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-boundary-probe-detail.json"; then
  echo "[FAIL] active-runtime boundary probe detail resolution drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime boundary probe detail resolution drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_active_runtime_closure_projection_common.py"
# expected fail-close: governance_probe_projection_missing_one_look_field:one_look.release_readiness_active_runtime_closure_topology_probe_status
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_active_runtime_closure_projection_common.py" \
  '"release_readiness_active_runtime_closure_topology_probe_status"' \
  '"release_readiness_active_runtime_closure_topology_probe_state"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-governance-field.json"; then
  echo "[FAIL] active-runtime governance-probe absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime governance-probe absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
# expected fail-close: summary_binding_probe_missing_token:release_readiness_active_runtime_closure_topology_probe
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_release_readiness_summary_binding_probes_ci.sh" \
  "${active_runtime_topology_probe_summary_key}" \
  'release_readiness_active_runtime_closure_topology'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-summary-binding.json"; then
  echo "[FAIL] active-runtime summary-binding absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime summary-binding absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "${active_runtime_topology_probe}"
mutate_probe_literal \
  "${TMP_ROOT}/${active_runtime_topology_probe}" \
  'active_runtime_topology_probe_summary_key=' \
  'active_runtime_topology_probe_summary_guard='
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-active-runtime-closure-topology-negative-probe-self-check.json"; then
  echo "[FAIL] active-runtime topology probe self-check unexpectedly passed"
  exit 1
fi
echo "[PASS] active-runtime topology probe self-check fail-closed as expected"

python3 - "${POSITIVE_JSON}" "${active_runtime_topology_probe_one_look_field}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

print(json.dumps({
    sys.argv[2]: "PASS_REQUIRED",
    "positive_validator_output": str(pathlib.Path(sys.argv[1]).resolve()),
}, ensure_ascii=False))
PY

echo "[PASS] release-readiness active-runtime closure topology probes passed"
