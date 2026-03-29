#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
source "${ROOT}/scripts/probe_fixture_shell_common.sh"
source "${ROOT}/scripts/ci/probe_repo_mirror_common.sh"

one_look_topology_validator="$(
  resolve_python_module_expression \
    "release_readiness_one_look_topology_common" \
    "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_VALIDATOR"
)"
one_look_topology_probe="$(
  resolve_python_module_expression \
    "release_readiness_one_look_topology_common" \
    "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_PROBE"
)"
one_look_topology_validator_command_literal="[\"python3\", \"${one_look_topology_validator}\", \"--json-only\"],"
one_look_topology_probe_command_literal="[\"bash\", \"${one_look_topology_probe}\"],"
one_look_topology_probe_one_look_field="$(
  resolve_python_module_expression \
    "release_readiness_governance_probe_projection_common" \
    "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD"
)"
one_look_topology_probe_self_check_reason="post_closure_bundle_missing_probe:${one_look_topology_probe}"

run_shadow_validator() {
  local shadow_root="$1"
  local output_path="$2"
  PYTHONPATH="${shadow_root}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 "${shadow_root}/${one_look_topology_validator}" \
      --repo-root "${shadow_root}" \
      --json-only >"${output_path}"
}

restore_shadow_file() {
  local shadow_root="$1"
  local rel_path="$2"
  mkdir -p "$(dirname "${shadow_root}/${rel_path}")"
  cp "${ROOT}/${rel_path}" "${shadow_root}/${rel_path}"
}

POSITIVE_JSON="/tmp/release-readiness-one-look-topology-positive.json"
echo "[INFO] positive: release-readiness one-look topology validator"
python3 "${one_look_topology_validator}" --json-only >"${POSITIVE_JSON}"

python3 - <<'PY' "${POSITIVE_JSON}"
from __future__ import annotations

import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["release_readiness_one_look_topology_status"] == "PASS_REQUIRED", payload
assert payload["family_count"] == 10, payload
assert payload["stale_reasons"] == [], payload
PY

TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-one-look-topology-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT
probe_mirror_repo "${ROOT}" "${TMP_ROOT}"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_one_look_projection_common.py"
# expected fail-close: projection_common_missing_shared_topology_apply
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_one_look_projection_common.py" \
  'apply_release_readiness_one_look_families(summary, one_look)' \
  'apply_release_readiness_foundational_one_look(summary, one_look)'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-projection-common.json; then
  echo "[FAIL] projection common drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] projection common drift probe fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_one_look_topology_common.py"
# expected fail-close: topology_family_ids_not_unique
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_one_look_topology_common.py" \
  'family_id="support_preflight"' \
  'family_id="foundational"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-family-id.json; then
  echo "[FAIL] duplicate family-id probe unexpectedly passed"
  exit 1
fi
echo "[PASS] duplicate family-id probe fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_governance_probe_projection_common.py"
# expected fail-close: governance_probe_projection_missing_one_look_field:one_look.release_readiness_one_look_topology_probe_status
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_governance_probe_projection_common.py" \
  "\"${one_look_topology_probe_one_look_field}\"" \
  '"release_readiness_one_look_topology_probe_state"'
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-governance-field.json; then
  echo "[FAIL] governance probe one-look field drift unexpectedly passed"
  exit 1
fi
echo "[PASS] governance probe one-look field drift fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
# expected fail-close: post_closure_bundle_missing_validator:scripts/validate_release_readiness_one_look_topology.py --json-only
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${one_look_topology_validator_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-missing-validator-command.json; then
  echo "[FAIL] missing validator command probe unexpectedly passed"
  exit 1
fi
echo "[PASS] missing validator command probe fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "scripts/release_readiness_check.py"
mutate_probe_literal \
  "${TMP_ROOT}/scripts/release_readiness_check.py" \
  "${one_look_topology_probe_command_literal}" \
  ''
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-missing-probe-command.json; then
  echo "[FAIL] missing probe command probe unexpectedly passed"
  exit 1
fi
echo "[PASS] missing probe command probe fail-closed as expected"

restore_shadow_file "${TMP_ROOT}" "${one_look_topology_probe}"
mutate_probe_literal \
  "${TMP_ROOT}/${one_look_topology_probe}" \
  'one_look_topology_probe_self_check_reason=' \
  'one_look_topology_probe_self_check_guard='
if run_shadow_validator "${TMP_ROOT}" /tmp/release-readiness-one-look-topology-negative-probe-self-check.json; then
  echo "[FAIL] probe self-check drift unexpectedly passed"
  exit 1
fi
echo "[PASS] probe self-check drift fail-closed as expected"

python3 - "${POSITIVE_JSON}" "${one_look_topology_probe_one_look_field}" <<'PY'
from __future__ import annotations

import json
import pathlib
import sys

print(json.dumps({
    sys.argv[2]: "PASS_REQUIRED",
    "positive_validator_output": str(pathlib.Path(sys.argv[1]).resolve()),
}, ensure_ascii=False))
PY

echo "[PASS] release-readiness one-look topology probes passed"
