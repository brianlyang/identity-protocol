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

governance_probe_topology_validator="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_topology_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_VALIDATOR"
)"
governance_probe_topology_probe="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_topology_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_PROBE"
)"
governance_probe_topology_self_summary_key="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_topology_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_SUMMARY_KEY"
)"
governance_probe_topology_self_one_look_field="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_topology_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_ONE_LOOK_FIELD"
)"
governance_probe_topology_positive_output_rel="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_topology_common" \
    "RELEASE_READINESS_GOVERNANCE_PROBE_TOPOLOGY_SELF_POSITIVE_OUTPUT_REL"
)"
one_look_topology_probe_summary_key="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_projection_common" \
    "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY"
)"
governance_probe_topology_validator_command_literal="[\"python3\", \"${governance_probe_topology_validator}\", \"--json-only\"],"
governance_probe_topology_probe_command_literal="[\"bash\", \"${governance_probe_topology_probe}\"],"
governance_probe_topology_self_check_reason="summary_binding_probe_missing_token:${governance_probe_topology_self_summary_key}"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${governance_probe_topology_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="${ROOT}/${governance_probe_topology_positive_output_rel}"
mkdir -p "$(dirname "${POSITIVE_JSON}")"
echo "[INFO] positive: release-readiness governance-probe topology validator"
python3 "${governance_probe_topology_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_governance_probe_topology_status"] == "PASS_REQUIRED", payload
assert payload["probe_count"] == 20, payload
assert payload["stale_reasons"] == [], payload
PY

probe_runtime_tmp_bootstrap "${ROOT}" "release-readiness-governance-probe-topology-probes" "run"
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_governance_probe_projection_common.py"
# expected fail-close: governance_probe_summary_keys_not_unique
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_governance_probe_projection_common.py" \
  "summary_key=\"${governance_probe_topology_self_summary_key}\"" \
  "summary_key=\"${one_look_topology_probe_summary_key}\""
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-summary-key.json"; then
  echo "[FAIL] governance probe summary-key drift unexpectedly passed"
  exit 1
fi
echo "[PASS] governance probe summary-key drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_governance_probe_projection_common.py"
# expected fail-close: governance_probe_one_look_field_order_changed
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_governance_probe_projection_common.py" \
  "one_look_field=\"${governance_probe_topology_self_one_look_field}\"" \
  'one_look_field="release_readiness_governance_probe_topology_probe_state"'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-one-look-field.json"; then
  echo "[FAIL] governance probe one-look-field drift unexpectedly passed"
  exit 1
fi
echo "[PASS] governance probe one-look-field drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_validator:${governance_probe_topology_validator} --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${governance_probe_topology_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-missing-validator.json"; then
  echo "[FAIL] missing governance-probe validator command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing governance-probe validator command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_probe:${governance_probe_topology_probe}
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${governance_probe_topology_probe_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-missing-probe.json"; then
  echo "[FAIL] missing governance-probe probe command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing governance-probe probe command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_closure_continuation_marker_common.py"
# expected fail-close: continuation_markers_missing_governance_probe_surface_constraints
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_closure_continuation_marker_common.py" \
  '*RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,' \
  ''
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-continuation-markers.json"; then
  echo "[FAIL] continuation governance-probe absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] continuation governance-probe absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
# expected fail-close: ${governance_probe_topology_self_check_reason}
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_release_readiness_summary_binding_probes_ci.sh" \
  "${governance_probe_topology_self_summary_key}" \
  'release_readiness_governance_probe_topology'
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-summary-binding.json"; then
  echo "[FAIL] summary binding governance-probe absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] summary binding governance-probe absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "${governance_probe_topology_probe}"
mutate_probe_literal \
  "${TMP_ROOT}/${governance_probe_topology_probe}" \
  'governance_probe_topology_self_check_reason=' \
  'governance_probe_topology_self_check_guard='
if run_shadow_validator "${TMP_ROOT}" "${TMP_ROOT}/release-readiness-governance-probe-topology-negative-probe-self-check.json"; then
  echo "[FAIL] governance-probe topology probe self-check unexpectedly passed"
  exit 1
fi
echo "[PASS] governance-probe topology probe self-check fail-closed as expected"

python3 - "${POSITIVE_JSON}" "${governance_probe_topology_self_one_look_field}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

print(json.dumps({
    sys.argv[2]: "PASS_REQUIRED",
    "positive_validator_output": str(pathlib.Path(sys.argv[1]).resolve()),
}, ensure_ascii=False))
PY

echo "[PASS] release-readiness governance-probe topology probes passed"
