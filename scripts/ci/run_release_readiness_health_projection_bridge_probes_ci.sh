#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"

health_projection_bridge_validator="$(
  resolve_python_module_expression \
    "health_report_experience_writeback_projection_common" \
    "RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_VALIDATOR"
)"
health_projection_bridge_probe="$(
  resolve_python_module_expression \
    "health_report_experience_writeback_projection_common" \
    "RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_PROBE"
)"
health_projection_bridge_marker="$(
  resolve_python_module_expression \
    "health_report_experience_writeback_projection_common" \
    "RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_BRIDGE_MARKER"
)"
health_projection_bridge_validator_command_literal='["python3", "'"${health_projection_bridge_validator}"'", "--json-only"],'
health_projection_bridge_probe_command_literal='["bash", "'"${health_projection_bridge_probe}"'"],'

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${health_projection_bridge_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="/tmp/release-readiness-health-projection-bridge-positive.json"
echo "[INFO] positive: release-readiness health projection bridge validator"
python3 "${health_projection_bridge_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_health_projection_bridge_status"] == "PASS_REQUIRED", payload
assert payload["stale_reasons"] == [], payload
PY

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-health-projection-bridge-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/health_report_experience_writeback_projection_common.py"
# expected fail-close: health_projection_bridge_marker_drift
mutate_probe_literal \
  "${TMP_ROOT}/scripts/health_report_experience_writeback_projection_common.py" \
  'release_readiness_health_projection_bridge=' \
  'release_readiness_health_projection_bridge_missing='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-health-projection-bridge-negative-common.json; then
  echo "[FAIL] health projection bridge common drift unexpectedly passed"
  exit 1
fi
echo "[PASS] health projection bridge common drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_health_projection_lane:python3 scripts/validate_release_readiness_health_projection_bridge.py --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${health_projection_bridge_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-health-projection-bridge-negative-post-closure.json; then
  echo "[FAIL] missing health projection bridge validator command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing health projection bridge validator command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/report_three_plane_status.py"
# expected fail-close: three_plane_missing_health_projection_token:terminal_truth_boundary_projection.get("post_execution_obligation_status", "")
mutate_probe_literal \
  "${TMP_ROOT}/scripts/report_three_plane_status.py" \
  'terminal_truth_boundary_projection.get("post_execution_obligation_status", "")' \
  'terminal_truth_boundary_projection.get("post_execution_status", "")'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-health-projection-bridge-negative-three-plane.json; then
  echo "[FAIL] three-plane health bridge absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] three-plane health bridge absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "docs/release/identity-v1.6x-release-closure-summary.md"
# expected fail-close: summary_doc_missing_health_projection_marker:release_readiness_health_projection_bridge=...
mutate_probe_literal \
  "${TMP_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md" \
  'release_readiness_health_projection_bridge=' \
  'release_readiness_health_projection_bridge_missing='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-health-projection-bridge-negative-doc.json; then
  echo "[FAIL] release summary health projection bridge marker drift unexpectedly passed"
  exit 1
fi
echo "[PASS] release summary health projection bridge marker drift fail-closed as expected"

echo "[PASS] release-readiness health projection bridge probes passed"
