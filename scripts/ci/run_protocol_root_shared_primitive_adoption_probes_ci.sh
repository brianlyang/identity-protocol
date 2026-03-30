#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_BASE="${TMPDIR:-${ROOT}/.tmp}"
mkdir -p "${TMP_BASE}"
TMP_ROOT="$(mktemp -d "${TMP_BASE}/shared-primitive-adoption-ci-isolation.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

FIXED_WRITE_SET_REL=(
  "scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"
  "docs/governance/identity-shared-primitive-adoption-ci-isolation-governance-v1.6.x.md"
  "docs/review/protocol-remediation-audit-ledger-v1.6.x-shared-primitive-adoption-ci-isolation.md"
  "scripts/shared_primitive_adoption_ci_isolation_common.py"
  "scripts/validate_shared_primitive_adoption_ci_isolation.py"
)

copy_fixed_write_set() {
  local destination="$1"
  mkdir -p "${destination}"
  local rel_path=""
  for rel_path in "${FIXED_WRITE_SET_REL[@]}"; do
    mkdir -p "${destination}/$(dirname "${rel_path}")"
    cp "${ROOT}/${rel_path}" "${destination}/${rel_path}"
  done
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_shared_primitive_adoption_ci_isolation.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - "${PASS_JSON}" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["shared_primitive_adoption_ci_isolation_status"] == "PASS_REQUIRED", payload
assert payload["error_code"] is None, payload
assert payload["ci_scope_isolation_status"] == "PASS_REQUIRED", payload
assert payload["dirty_state_isolation_status"] == "PASS_REQUIRED", payload
assert payload["nonlane_context_status"] == "PASS_REQUIRED", payload
PY

AMBIENT_SCOPE_REPO="${TMP_ROOT}/ambient-scope-repo"
copy_fixed_write_set "${AMBIENT_SCOPE_REPO}"
printf '\nAMBIENT_SCOPE_TOKEN="%s%s"\n' "scripts/validate_protocol_root_" "*.py" >> \
  "${AMBIENT_SCOPE_REPO}/scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"

AMBIENT_SCOPE_JSON="${TMP_ROOT}/ambient-scope.json"
if python3 "${AMBIENT_SCOPE_REPO}/scripts/validate_shared_primitive_adoption_ci_isolation.py" \
  --repo-root "${AMBIENT_SCOPE_REPO}" \
  --json-only >"${AMBIENT_SCOPE_JSON}"; then
  echo "[FAIL] validator unexpectedly admitted ambient scope dependency"
  exit 1
fi

python3 - "${AMBIENT_SCOPE_JSON}" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["shared_primitive_adoption_ci_isolation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "ERR_SCOPE", payload
assert "ambient_scope_dependency" in payload["blocking_reasons"], payload
PY

DIRTY_STATE_REPO="${TMP_ROOT}/dirty-state-repo"
copy_fixed_write_set "${DIRTY_STATE_REPO}"
printf '\n%s %s --short >/dev/null\n' "git" "status" >> \
  "${DIRTY_STATE_REPO}/scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"

DIRTY_STATE_JSON="${TMP_ROOT}/dirty-state.json"
if python3 "${DIRTY_STATE_REPO}/scripts/validate_shared_primitive_adoption_ci_isolation.py" \
  --repo-root "${DIRTY_STATE_REPO}" \
  --json-only >"${DIRTY_STATE_JSON}"; then
  echo "[FAIL] validator unexpectedly admitted dirty-state dependency"
  exit 1
fi

python3 - "${DIRTY_STATE_JSON}" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["shared_primitive_adoption_ci_isolation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "ERR_DIRTY_STATE", payload
assert "dirty_state_dependency" in payload["blocking_reasons"], payload
PY

echo "[PASS] shared primitive adoption CI isolation probes passed"
