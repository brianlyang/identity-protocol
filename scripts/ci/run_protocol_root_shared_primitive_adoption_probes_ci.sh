#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-shared-primitive-adoption-ci"
export PYTHONPATH="${ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}"

PROBE_REL_PATHS=(
  "scripts/repo_root_resolution_common.py"
  "scripts/root_shared_primitive_adoption_common.py"
  "scripts/validate_protocol_root_shared_primitive_adoption.py"
  "scripts/ci/protocol_root_probe_shadow_common.sh"
  "scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"
)
while IFS= read -r rel_path; do
  PROBE_REL_PATHS+=("${rel_path}")
done < <(cd "${ROOT}" && printf '%s\n' scripts/validate_protocol_root_*.py)
while IFS= read -r rel_path; do
  PROBE_REL_PATHS+=("${rel_path}")
done < <(cd "${ROOT}" && printf '%s\n' scripts/ci/run_protocol_root_*_probes_ci.sh)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

from validate_protocol_root_shared_primitive_adoption import STATUS_PASS_REQUIRED

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_PASS_REQUIRED, payload
assert payload["root_validator_count"] > 0, payload
assert payload["primitive_violation_count"] == 0, payload
assert payload["scan_error_count"] == 0, payload
assert payload["primitive_adoption_row_count"] > 0, payload
assert payload["row_family_projection_assignment_violation_count"] == 0, payload
assert payload["root_probe_count"] > 0, payload
assert payload["root_probe_shadow_adoption_row_count"] == payload["root_probe_count"], payload
assert payload["root_probe_shadow_violation_count"] == 0, payload
assert payload["root_probe_scan_error_count"] == 0, payload
assert payload["root_probe_shadow_common_contract_status"] == STATUS_PASS_REQUIRED, payload
assert payload["root_probe_shadow_common_contract_row_count"] == 6, payload
assert payload["root_probe_shadow_common_violation_count"] == 0, payload
assert payload["root_probe_shadow_common_scan_error_count"] == 0, payload
PY

require_contains() {
  local path="$1"
  local needle="$2"
  python3 - "$path" "$needle" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
needle = sys.argv[2]
text = path.read_text(encoding="utf-8")
assert needle in text, text[:5000]
PY
}

replace_line() {
  local path="$1"
  local old_line="$2"
  local new_text="$3"
  python3 - "$path" "$old_line" "$new_text" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
old_line = sys.argv[2]
new_text = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
target = f"{old_line}\n"
match_count = sum(line == target for line in lines)
assert match_count == 1, (old_line, match_count, "".join(lines[:200]))
replacement = new_text if new_text.endswith("\n") else f"{new_text}\n"
for idx, line in enumerate(lines):
    if line == target:
        lines[idx:idx + 1] = [replacement]
        break
path.write_text("".join(lines), encoding="utf-8")
PY
}

replace_python_from_import_symbol() {
  local path="$1"
  local module_name="$2"
  local old_symbol="$3"
  local new_symbol="$4"
  python3 - "$path" "$module_name" "$old_symbol" "$new_symbol" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
module_name = sys.argv[2]
old_symbol = sys.argv[3]
new_symbol = sys.argv[4]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start_line = f"from {module_name} import (\n"

start_idx = None
for idx, line in enumerate(lines):
    if line == start_line:
        start_idx = idx
        break
assert start_idx is not None, (module_name, "".join(lines[:200]))

depth = 0
end_idx = None
for idx in range(start_idx, len(lines)):
    depth += lines[idx].count("(")
    depth -= lines[idx].count(")")
    if depth == 0:
        end_idx = idx
        break
assert end_idx is not None, module_name

old_line = f"    {old_symbol},\n"
new_line = f"    {new_symbol},\n"
match_indices = [
    idx for idx in range(start_idx + 1, end_idx)
    if lines[idx] == old_line
]
assert len(match_indices) == 1, (old_symbol, len(match_indices))
lines[match_indices[0]] = new_line
path.write_text("".join(lines), encoding="utf-8")
PY
}

insert_after_python_from_import_block() {
  local path="$1"
  local module_name="$2"
  local block_text="$3"
  python3 - "$path" "$module_name" "$block_text" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
module_name = sys.argv[2]
block_text = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start_line = f"from {module_name} import (\n"

start_idx = None
for idx, line in enumerate(lines):
    if line == start_line:
        start_idx = idx
        break
assert start_idx is not None, (module_name, "".join(lines[:200]))

depth = 0
end_idx = None
for idx in range(start_idx, len(lines)):
    depth += lines[idx].count("(")
    depth -= lines[idx].count(")")
    if depth == 0:
        end_idx = idx
        break
assert end_idx is not None, module_name

insertion = block_text if block_text.endswith("\n") else f"{block_text}\n"
lines[end_idx + 1:end_idx + 1] = [insertion]
path.write_text("".join(lines), encoding="utf-8")
PY
}

replace_line_in_shell_function() {
  local path="$1"
  local function_name="$2"
  local old_line="$3"
  local new_text="$4"
  python3 - "$path" "$function_name" "$old_line" "$new_text" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
function_name = sys.argv[2]
old_line = sys.argv[3]
new_text = sys.argv[4]
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start_line = f"{function_name}() {{\n"

start_idx = None
for idx, line in enumerate(lines):
    if line == start_line:
        start_idx = idx
        break
assert start_idx is not None, function_name

depth = 0
end_idx = None
for idx in range(start_idx, len(lines)):
    depth += lines[idx].count("{")
    depth -= lines[idx].count("}")
    if depth == 0:
        end_idx = idx
        break
assert end_idx is not None, function_name

target = f"{old_line}\n"
match_indices = [
    idx for idx in range(start_idx + 1, end_idx)
    if lines[idx] == target
]
assert len(match_indices) == 1, (function_name, old_line, len(match_indices))
replacement = new_text if new_text.endswith("\n") else f"{new_text}\n"
lines[match_indices[0]:match_indices[0] + 1] = [replacement]
path.write_text("".join(lines), encoding="utf-8")
PY
}

PROJECTION_DRIFT_REPO="${TMP_ROOT}/projection-drift-repo"
mirror_repo "${PROJECTION_DRIFT_REPO}"
PROJECTION_DRIFT_PATH="${PROJECTION_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
require_contains "${PROJECTION_DRIFT_PATH}" "project_row_families"
replace_python_from_import_symbol \
  "${PROJECTION_DRIFT_PATH}" \
  "root_row_family_projection_common" \
  "project_row_families" \
  "project_row_family"
replace_line \
  "${PROJECTION_DRIFT_PATH}" \
  '        row_family_projection_rows = project_row_families(' \
  '        row_family_projection_rows = project_row_family('

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

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
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

python3 - <<'PY' "${PROJECTION_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason.startswith("primitive_binding_violation:")
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY

ROW_BATCH_DRIFT_REPO="${TMP_ROOT}/row-batch-drift-repo"
mirror_repo "${ROW_BATCH_DRIFT_REPO}"
ROW_BATCH_DRIFT_PATH="${ROW_BATCH_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
require_contains "${ROW_BATCH_DRIFT_PATH}" "validate_contract_row_batches"
replace_line \
  "${ROW_BATCH_DRIFT_PATH}" \
  'from root_contract_row_validation_common import validate_contract_row_batches' \
  'from root_contract_row_validation_common import validate_contract_rows'
replace_line \
  "${ROW_BATCH_DRIFT_PATH}" \
  '        validate_contract_row_batches(' \
  '        validate_contract_rows('

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

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
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

python3 - <<'PY' "${ROW_BATCH_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason.startswith("primitive_binding_violation:")
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY
ASSIGNMENT_DRIFT_REPO="${TMP_ROOT}/assignment-drift-repo"
mirror_repo "${ASSIGNMENT_DRIFT_REPO}"
ASSIGNMENT_DRIFT_PATH="${ASSIGNMENT_DRIFT_REPO}/scripts/validate_protocol_root_identity_discovery.py"
require_contains "${ASSIGNMENT_DRIFT_PATH}" "project_row_families"
insert_after_python_from_import_block \
  "${ASSIGNMENT_DRIFT_PATH}" \
  "root_row_family_projection_common" \
  $'def manual_projection_rows(*_args, **_kwargs):\n    return []\n'
replace_line \
  "${ASSIGNMENT_DRIFT_PATH}" \
  '        row_family_projection_rows = project_row_families(' \
  '        row_family_projection_rows = manual_projection_rows('

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

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
assert payload["row_family_projection_assignment_violation_count"] >= 1, payload
assert any(
    row["assignment_mode"] == "non_shared_call"
    and row["binding"] == "manual_projection_rows"
    for row in payload["row_family_projection_assignment_rows"]
), payload
PY

python3 - <<'PY' "${ASSIGNMENT_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason.startswith("row_family_projection_assignment_violation:")
        and "manual_projection_rows" in reason
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY
MISSING_EFFECTIVE_REPO="${TMP_ROOT}/missing-effective-repo"
mirror_repo "${MISSING_EFFECTIVE_REPO}"
MISSING_EFFECTIVE_PATH="${MISSING_EFFECTIVE_REPO}/scripts/validate_protocol_root_identity_discovery.py"
replace_line \
  "${MISSING_EFFECTIVE_PATH}" \
  '        row_family_projection_rows = project_row_families(' \
  '        projected_row_family_rows = project_row_families('

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

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
assert payload["row_family_projection_assignment_violation_count"] >= 1, payload
assert any(
    row["assignment_role"] == "missing_effective_assignment"
    and row["assignment_mode"] == "initializer_empty_list"
    and row["violation"] is True
    for row in payload["row_family_projection_assignment_rows"]
), payload
PY

python3 - <<'PY' "${MISSING_EFFECTIVE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason == "primitive_binding_violation:scripts/validate_protocol_root_identity_discovery.py::row_family_projection_missing_effective_assignment"
        or reason
        == "row_family_projection_assignment_violation:scripts/validate_protocol_root_identity_discovery.py:initializer_empty_list:List"
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY
PROBE_SHADOW_DRIFT_REPO="${TMP_ROOT}/probe-shadow-drift-repo"
mirror_repo "${PROBE_SHADOW_DRIFT_REPO}"
PROBE_SHADOW_DRIFT_PATH="${PROBE_SHADOW_DRIFT_REPO}/scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh"
replace_line \
  "${PROBE_SHADOW_DRIFT_PATH}" \
  '# shellcheck source=./protocol_root_probe_shadow_common.sh' \
  '# shellcheck source=./probe_repo_mirror_common.sh'
replace_line \
  "${PROBE_SHADOW_DRIFT_PATH}" \
  'source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"' \
  'source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"'
replace_line \
  "${PROBE_SHADOW_DRIFT_PATH}" \
  'protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-identity-discovery-ci"' \
  $'ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"\nTMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-identity-discovery-ci.XXXXXX")"\ntrap \'rm -rf "${TMP_ROOT}"\' EXIT\n'
replace_line \
  "${PROBE_SHADOW_DRIFT_PATH}" \
  'protocol_root_probe_define_full_mirror' \
  $'mirror_repo() {\n  local dst="$1"\n  probe_mirror_repo "${ROOT}" "${dst}"\n}'

PROBE_SHADOW_DRIFT_JSON="${TMP_ROOT}/probe-shadow-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${PROBE_SHADOW_DRIFT_REPO}" \
  --json-only >"${PROBE_SHADOW_DRIFT_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed probe shadow bootstrap regression drift"
  exit 1
fi

python3 - <<'PY' "${PROBE_SHADOW_DRIFT_JSON}"
import json
import pathlib
import sys

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
assert payload["root_probe_shadow_violation_count"] >= 1, payload
assert any(
    row["rel_path"] == "scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh"
    and row["reason"] == "forbidden_direct_probe_repo_mirror_source"
    for row in payload["root_probe_shadow_violation_rows"]
), payload
assert any(
    row["rel_path"] == "scripts/ci/run_protocol_root_identity_discovery_probes_ci.sh"
    and row["reason"] == "forbidden_manual_mirror_repo_definition"
    for row in payload["root_probe_shadow_violation_rows"]
), payload
PY

python3 - <<'PY' "${PROBE_SHADOW_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason.startswith("root_probe_shadow_violation:")
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY
SHADOW_COMMON_DRIFT_REPO="${TMP_ROOT}/probe-shadow-common-drift-repo"
mirror_repo "${SHADOW_COMMON_DRIFT_REPO}"
SHADOW_COMMON_DRIFT_PATH="${SHADOW_COMMON_DRIFT_REPO}/scripts/ci/protocol_root_probe_shadow_common.sh"
replace_line_in_shell_function \
  "${SHADOW_COMMON_DRIFT_PATH}" \
  'protocol_root_probe_define_relpath_mirror' \
  '    probe_mirror_repo_with_relpaths "${ROOT}" "${dst}" "${PROTOCOL_ROOT_PROBE_REL_PATHS[@]}"' \
  '    probe_mirror_relpaths_only "${ROOT}" "${dst}" "${PROTOCOL_ROOT_PROBE_REL_PATHS[@]}"'

SHADOW_COMMON_DRIFT_JSON="${TMP_ROOT}/probe-shadow-common-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_shared_primitive_adoption.py" \
  --repo-root "${SHADOW_COMMON_DRIFT_REPO}" \
  --json-only >"${SHADOW_COMMON_DRIFT_JSON}"; then
  echo "[FAIL] root shared-primitive adoption validator unexpectedly passed probe shadow common contract drift"
  exit 1
fi

python3 - <<'PY' "${SHADOW_COMMON_DRIFT_JSON}"
import json
import pathlib
import sys

from validate_protocol_root_shared_primitive_adoption import (
    ERR_BINDING,
    STATUS_FAIL_REQUIRED,
)

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_shared_primitive_adoption_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["error_code"] == ERR_BINDING, payload
assert payload["root_probe_shadow_common_contract_status"] == STATUS_FAIL_REQUIRED, payload
assert payload["root_probe_shadow_common_violation_count"] >= 1, payload
assert any(
    row["contract_id"] == "relpath_mirror_probe_repo_binding"
    and row["reason"] == "root_probe_shadow_common_binding_missing"
    for row in payload["root_probe_shadow_common_violation_rows"]
), payload
PY

python3 - <<'PY' "${SHADOW_COMMON_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if payload.get("stale_reasons"):
    assert any(
        reason.startswith("root_probe_shadow_common_violation:")
        for reason in payload["stale_reasons"]
    ), payload["stale_reasons"]
PY
echo "[PASS] protocol root shared-primitive adoption probes passed"
