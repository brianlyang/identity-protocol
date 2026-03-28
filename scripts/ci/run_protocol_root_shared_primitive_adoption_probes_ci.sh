#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-shared-primitive-adoption-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

PROBE_REL_PATHS=(
  "scripts/repo_root_resolution_common.py"
  "scripts/root_shared_primitive_adoption_common.py"
  "scripts/validate_protocol_root_shared_primitive_adoption.py"
  "scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"
)
while IFS= read -r rel_path; do
  PROBE_REL_PATHS+=("${rel_path}")
done < <(cd "${ROOT}" && printf '%s\n' scripts/validate_protocol_root_*.py)

mirror_repo() {
  local dst="$1"
  probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROBE_REL_PATHS[@]}"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == "PASS_REQUIRED", payload
assert payload["root_validator_count"] > 0, payload
assert payload["primitive_violation_count"] == 0, payload
assert payload["scan_error_count"] == 0, payload
assert payload["primitive_adoption_row_count"] > 0, payload
assert payload["row_family_projection_assignment_violation_count"] == 0, payload
PY

PROJECTION_DRIFT_REPO="${TMP_ROOT}/projection-drift-repo"
mirror_repo "${PROJECTION_DRIFT_REPO}"
python3 - <<'PY' "${PROJECTION_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "project_row_families"
new = "project_row_family"
assert old in text, text[:5000]
path.write_text(text.replace(old, new, 2), encoding="utf-8")
PY

PROJECTION_DRIFT_JSON="${TMP_ROOT}/projection-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${PROJECTION_DRIFT_REPO}" \
  --json-only >"${PROJECTION_DRIFT_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed row-family regression drift"
  exit 1
fi

python3 - <<'PY' "${PROJECTION_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSPA-002", payload
assert any(
    row["primitive_name"] == "project_row_family"
    and row["reason"]
    in (
        "forbidden_direct_import_binding",
        "forbidden_direct_call_binding",
        "forbidden_direct_call_literal",
    )
    for row in payload["primitive_binding_violations"]
), payload
PY

ROW_BATCH_DRIFT_REPO="${TMP_ROOT}/row-batch-drift-repo"
mirror_repo "${ROW_BATCH_DRIFT_REPO}"
python3 - <<'PY' "${ROW_BATCH_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "validate_contract_row_batches"
new = "validate_contract_rows"
assert old in text, text[:5000]
path.write_text(text.replace(old, new, 2), encoding="utf-8")
PY

ROW_BATCH_DRIFT_JSON="${TMP_ROOT}/row-batch-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${ROW_BATCH_DRIFT_REPO}" \
  --json-only >"${ROW_BATCH_DRIFT_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed row-batch regression drift"
  exit 1
fi

python3 - <<'PY' "${ROW_BATCH_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSPA-002", payload
assert any(
    row["primitive_name"] == "validate_contract_rows"
    and row["reason"]
    in (
        "forbidden_direct_import_binding",
        "forbidden_direct_call_binding",
        "forbidden_direct_call_literal",
    )
    for row in payload["primitive_binding_violations"]
), payload
PY

ASSIGNMENT_DRIFT_REPO="${TMP_ROOT}/assignment-drift-repo"
mirror_repo "${ASSIGNMENT_DRIFT_REPO}"
python3 - <<'PY' "${ASSIGNMENT_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
import_line = (
    "from root_row_family_projection_common import aggregate_row_family_status, "
    "project_root_contract_support_projection, project_row_families\n"
)
helper = "def manual_projection_rows(*_args, **_kwargs):\n    return []\n\n"
assert import_line in text, text[:5000]
text = text.replace(import_line, import_line + helper, 1)
old = "        row_family_projection_rows = project_row_families("
new = "        row_family_projection_rows = manual_projection_rows("
assert old in text, text[:5000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ASSIGNMENT_DRIFT_JSON="${TMP_ROOT}/assignment-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${ASSIGNMENT_DRIFT_REPO}" \
  --json-only >"${ASSIGNMENT_DRIFT_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed assignment-shape drift"
  exit 1
fi

python3 - <<'PY' "${ASSIGNMENT_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSPA-002", payload
assert payload["row_family_projection_assignment_violation_count"] >= 1, payload
assert any(
    row["assignment_mode"] == "non_shared_call"
    and row["binding"] == "manual_projection_rows"
    for row in payload["row_family_projection_assignment_rows"]
), payload
PY

MISSING_EFFECTIVE_REPO="${TMP_ROOT}/missing-effective-repo"
mirror_repo "${MISSING_EFFECTIVE_REPO}"
python3 - <<'PY' "${MISSING_EFFECTIVE_REPO}/scripts/validate_protocol_root_identity_discovery.py"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "        row_family_projection_rows = project_row_families("
new = "        projected_row_family_rows = project_row_families("
assert old in text, text[:5000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

MISSING_EFFECTIVE_JSON="${TMP_ROOT}/missing-effective.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${MISSING_EFFECTIVE_REPO}" \
  --json-only >"${MISSING_EFFECTIVE_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed missing effective assignment drift"
  exit 1
fi

python3 - <<'PY' "${MISSING_EFFECTIVE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RSPA-002", payload
assert payload["row_family_projection_assignment_violation_count"] >= 1, payload
assert any(
    row["assignment_role"] == "missing_effective_assignment"
    and row["assignment_mode"] == "initializer_empty_list"
    and row["violation"] is True
    for row in payload["row_family_projection_assignment_rows"]
), payload
PY

echo "[PASS] protocol root shared-primitive adoption probes passed"
