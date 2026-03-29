#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"

post_closure_adjudication_validator="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_VALIDATOR"
)"
post_closure_adjudication_probe="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE"
)"
post_closure_adjudication_validator_command_literal="[\"python3\", \"${post_closure_adjudication_validator}\", \"--json-only\"],"
post_closure_adjudication_probe_command_literal="[\"bash\", \"${post_closure_adjudication_probe}\"],"
post_closure_adjudication_probe_summary_key="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_SUMMARY_KEY"
)"
post_closure_adjudication_probe_one_look_field="$(
  resolve_python_module_expression \
    "release_readiness_post_closure_adjudication_common" \
    "RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_PROBE_ONE_LOOK_FIELD"
)"
post_closure_adjudication_probe_self_check_reason="summary_binding_probe_missing_token:${post_closure_adjudication_probe_summary_key}"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${post_closure_adjudication_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="/tmp/release-readiness-post-closure-adjudication-topology-positive.json"
echo "[INFO] positive: release-readiness post-closure adjudication topology validator"
python3 "${post_closure_adjudication_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_post_closure_adjudication_topology_status"] == "PASS_REQUIRED", payload
assert payload["stage_count"] == 6, payload
assert payload["stale_reasons"] == [], payload
PY

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-post-closure-adjudication-topology-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_post_closure_adjudication_common.py"
# expected fail-close: post_closure_adjudication_stage_order_changed
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_post_closure_adjudication_common.py" \
  'stage_id="governance_probe_topology"' \
  'stage_id="governance_probe_surface"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-common.json; then
  echo "[FAIL] post-closure adjudication common drift unexpectedly passed"
  exit 1
fi
echo "[PASS] post-closure adjudication common drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_adjudication_command_slice_drift
python3 - <<'PY' "${TMP_ROOT}/scripts/release_readiness_check.py"
from pathlib import Path
import sys

path = Path(sys.argv[1])
needle = '    ["bash", "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh"],\n'
insertion = needle + '    ["bash", "scripts/ci/run_three_plane_health_projection_probes_ci.sh"],\n'
text = path.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit(f"needle not found in {path}")
text = text.replace(needle, insertion, 1)
path.write_text(text, encoding="utf-8")
PY
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-slice.json; then
  echo "[FAIL] post-closure adjudication command slice drift unexpectedly passed"
  exit 1
fi
echo "[PASS] post-closure adjudication command slice drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_validator:${post_closure_adjudication_validator} --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${post_closure_adjudication_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-validator.json; then
  echo "[FAIL] missing post-closure adjudication validator command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing post-closure adjudication validator command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_probe:${post_closure_adjudication_probe}
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${post_closure_adjudication_probe_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-probe.json; then
  echo "[FAIL] missing post-closure adjudication probe command unexpectedly passed"
  exit 1
fi
echo "[PASS] missing post-closure adjudication probe command fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_adjudication_command_slice_drift
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  '["python3", "scripts/validate_release_readiness_post_closure_adjudication_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"],' \
  '["python3", "scripts/validate_release_readiness_post_closure_adjudication_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_three_plane_health_projection_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"],'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-sequencing.json; then
  echo "[FAIL] post-closure adjudication command slice drift unexpectedly passed"
  exit 1
fi
echo "[PASS] post-closure adjudication command slice drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "docs/release/identity-v1.6x-release-closure-summary.md"
# expected fail-close: summary_doc_missing_post_closure_adjudication_marker:release_readiness_post_closure_adjudication_order=...
mutate_probe_literal \
  "${TMP_ROOT}/docs/release/identity-v1.6x-release-closure-summary.md" \
  'release_readiness_post_closure_adjudication_order=' \
  'release_readiness_post_closure_adjudication_order_missing='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-doc.json; then
  echo "[FAIL] post-closure adjudication doc marker drift unexpectedly passed"
  exit 1
fi
echo "[PASS] post-closure adjudication doc marker drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_governance_probe_projection_common.py"
# expected fail-close: governance_probe_capture_map_missing_post_closure_adjudication_probe
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_governance_probe_projection_common.py" \
  "\"${post_closure_adjudication_probe_summary_key}\"" \
  '"release_readiness_post_closure_adjudication"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-governance-projection.json; then
  echo "[FAIL] governance probe post-closure adjudication absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] governance probe post-closure adjudication absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"
# expected fail-close: ${post_closure_adjudication_probe_self_check_reason}
mutate_probe_literal \
  "${TMP_ROOT}/scripts/ci/run_release_readiness_summary_binding_probes_ci.sh" \
  "${post_closure_adjudication_probe_summary_key}" \
  'release_readiness_post_closure_adjudication'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-summary-binding.json; then
  echo "[FAIL] summary binding post-closure adjudication absorption drift unexpectedly passed"
  exit 1
fi
echo "[PASS] summary binding post-closure adjudication absorption drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "${post_closure_adjudication_probe}"
mutate_probe_literal \
  "${TMP_ROOT}/${post_closure_adjudication_probe}" \
  'post_closure_adjudication_probe_self_check_reason=' \
  'post_closure_adjudication_probe_self_guard='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-post-closure-adjudication-topology-negative-self-check.json; then
  echo "[FAIL] post-closure adjudication topology probe self-check unexpectedly passed"
  exit 1
fi
echo "[PASS] post-closure adjudication topology probe self-check fail-closed as expected"

python3 - "${POSITIVE_JSON}" "${post_closure_adjudication_probe_one_look_field}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

print(json.dumps({
    sys.argv[2]: "PASS_REQUIRED",
    "positive_validator_output": str(pathlib.Path(sys.argv[1]).resolve()),
}, ensure_ascii=False))
PY

echo "[PASS] release-readiness post-closure adjudication topology probes passed"
