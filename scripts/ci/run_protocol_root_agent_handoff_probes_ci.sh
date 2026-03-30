#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-agent-handoff-ci"
protocol_root_probe_define_full_mirror

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

AGENT_HANDOFF_STATUS_KEY="$(
  resolve_python_module_constant "validate_protocol_root_agent_handoff" "STATUS_KEY"
)"
AGENT_HANDOFF_PASS_STATUS="$(
  resolve_python_module_constant "validate_protocol_root_agent_handoff" "STATUS_PASS_REQUIRED"
)"
AGENT_HANDOFF_FAIL_STATUS="$(
  resolve_python_module_constant "validate_protocol_root_agent_handoff" "STATUS_FAIL_REQUIRED"
)"
AGENT_HANDOFF_ERR_STRUCTURE="$(
  resolve_python_module_constant "validate_protocol_root_agent_handoff" "ERR_STRUCTURE"
)"
AGENT_HANDOFF_ERR_HANDOFF="$(
  resolve_python_module_constant "validate_protocol_root_agent_handoff" "ERR_HANDOFF"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "tuple(EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS.keys())[0]"
)"
AGENT_HANDOFF_COMPLETENESS_NONCONTIG_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "tuple(EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS.keys())[1]"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'][0]"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS['${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID}']['order']"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS['${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID}']['contract_phrase']"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_DRIFT_PHRASE="${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE/handoff-limit, /}"
AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS['${AGENT_HANDOFF_COMPLETENESS_NONCONTIG_ID}']['order']"
)"
AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_AGENT_HANDOFF_COMPLETENESS_ROWS['${AGENT_HANDOFF_COMPLETENESS_NONCONTIG_ID}']['contract_phrase']"
)"
AGENT_HANDOFF_ROLE_DELEGATED_HEADING="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_ROLE_ROWS['delegated_sub_agent_execution']['contract_heading']"
)"
AGENT_HANDOFF_IDENTITY_PROTOCOL_BOUNDARY_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/IDENTITY_PROTOCOL.md'][0]"
)"
AGENT_HANDOFF_README_BINDING_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_agent_handoff" \
    "EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'][2]"
)"

export AGENT_HANDOFF_STATUS_KEY
export AGENT_HANDOFF_PASS_STATUS
export AGENT_HANDOFF_FAIL_STATUS
export AGENT_HANDOFF_ERR_STRUCTURE
export AGENT_HANDOFF_ERR_HANDOFF
export AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID
export AGENT_HANDOFF_COMPLETENESS_NONCONTIG_ID
export AGENT_HANDOFF_COMPLETENESS_SURFACE_SECTION_MARKER
export AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ORDER
export AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE
export AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_DRIFT_PHRASE
export AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_ORDER
export AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_PHRASE
export AGENT_HANDOFF_ROLE_DELEGATED_HEADING
export AGENT_HANDOFF_IDENTITY_PROTOCOL_BOUNDARY_MARKER
export AGENT_HANDOFF_README_BINDING_MARKER

if [[ "${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_DRIFT_PHRASE}" == "${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE}" ]]; then
  echo "[FAIL] unable to derive agent-handoff completeness surface drift phrase"
  exit 1
fi

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == pass_status, payload
assert payload["role_count"] == 2, payload
assert payload["payload_field_count"] == 10, payload
assert payload["anchor_count"] == 5, payload
assert payload["handoff_proof_count"] == 5, payload
assert payload["handoff_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["agent_handoff_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == pass_status, payload
assert payload["agent_handoff_row_family_count"] == 8, payload
assert payload["agent_handoff_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == pass_status, payload
assert payload["role_row_coverage_status"] == pass_status, payload
assert payload["payload_row_coverage_status"] == pass_status, payload
assert payload["anchor_row_coverage_status"] == pass_status, payload
assert payload["handoff_proof_row_coverage_status"] == pass_status, payload
assert payload["handoff_limit_row_coverage_status"] == pass_status, payload
assert payload["collapse_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface"]["entry_count"] == 5, payload
assert payload["agent_handoff_completeness_surface"]["extraction_violations"] == [], payload
assert [row["family_id"] for row in payload["row_family_projection_rows"]] == [
    "role_rows",
    "payload_rows",
    "anchor_rows",
    "handoff_proof_rows",
    "handoff_limit_rows",
    "collapse_rows",
    "agent_handoff_completeness_rows",
    "agent_handoff_completeness_surface",
], payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/completeness-row-drift-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml"
import os
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
expected_missing_id = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID"]
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["agent_handoff_completeness_rows"] = [
    row
    for row in doc["agent_handoff_completeness_rows"]
    if row.get("completeness_id") != expected_missing_id
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/completeness-row-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
expected_missing_id = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ID"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert any(
    row["field"] == "agent_handoff_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and expected_missing_id in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == [expected_missing_id], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == fail_status, payload
assert completeness_row["identity_projection_status"] == fail_status, payload
assert payload["agent_handoff_row_coverage_status"] == fail_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == fail_status, payload
assert payload["agent_handoff_completeness_row_coverage_status"] == fail_status, payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == fail_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == pass_status, payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/completeness-row-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml" "${AGENT_HANDOFF_COMPLETENESS_NONCONTIG_ID}"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
target_id = sys.argv[2]
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["agent_handoff_completeness_rows"]:
    if row.get("completeness_id") == target_id:
        row["order"] = 1
        break
else:
    raise SystemExit("expected agent handoff completeness row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/completeness-row-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed completeness row order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert payload["agent_handoff_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == pass_status, payload
assert any(
    row["field"] == "agent_handoff_completeness_rows"
    and row["reason"] == "agent_handoff_completeness_row_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "agent_handoff_completeness_rows"
    and row["reason"] == "agent_handoff_completeness_row_order_mismatch"
    for row in payload["handoff_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == pass_status, payload
assert completeness_row["identity_projection_status"] == pass_status, payload
PY

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert any(
    reason == "structure_violation:agent_handoff_completeness_rows:agent_handoff_completeness_row_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload["stale_reasons"]
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE"]
new = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_DRIFT_PHRASE"]
assert old != new, (old, new)
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
surface_expected_phrase = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE"]
surface_drift_phrase = os.environ["AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_DRIFT_PHRASE"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "missing_agent_handoff_completeness_surface_rows"
    and surface_expected_phrase in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "extra_agent_handoff_completeness_surface_rows"
    and surface_drift_phrase in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [surface_expected_phrase], payload
assert surface_row["unexpected_ids"] == [surface_drift_phrase], payload
assert surface_row["coverage_status"] == pass_status, payload
assert surface_row["identity_projection_status"] == fail_status, payload
assert payload["agent_handoff_completeness_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == fail_status, payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows_in_section \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_PHRASE}" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_PHRASE}"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["agent_handoff_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == pass_status, payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "agent_handoff_completeness_surface_order_mismatch"
    for row in payload["handoff_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_surface"
)
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == pass_status, payload
assert surface_row["identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == pass_status, payload
PY

COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/completeness-surface-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${AGENT_HANDOFF_COMPLETENESS_SURFACE_FIRST_ORDER}"

COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/completeness-surface-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed completeness surface order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
pass_status = os.environ["AGENT_HANDOFF_PASS_STATUS"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert payload["agent_handoff_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == pass_status, payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == pass_status, payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "agent_handoff_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "agent_handoff_completeness_surface_order_mismatch"
    for row in payload["handoff_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == pass_status, payload
assert surface_row["identity_projection_status"] == pass_status, payload
PY

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert any(
    reason == "structure_violation:agent_handoff_completeness_surface:agent_handoff_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload["stale_reasons"]
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_handoff_proof_rows"] = [
    row for row in doc["required_handoff_proof_rows"] if row.get("proof_id") != "validation_track_separation_proof"
]
for idx, row in enumerate(doc["required_handoff_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed missing handoff proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert payload["agent_handoff_row_coverage_status"] == fail_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == fail_status, payload
assert payload["handoff_proof_row_coverage_status"] == fail_status, payload
assert payload["handoff_proof_row_identity_projection_status"] == fail_status, payload
assert any(
    row["reason"] == "missing_expected_rows" and "validation_track_separation_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["family_id"] == "handoff_proof_rows"
    and "validation_track_separation_proof" in row["missing_ids"]
    for row in payload["row_family_projection_rows"]
), payload
PY

ROLE_REPO="${TMP_ROOT}/role-drift-repo"
mirror_repo "${ROLE_REPO}"
python3 - <<'PY' "${ROLE_REPO}/identity/protocol/mappings/root-agent-handoff.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_role_rows"] = [row for row in doc["required_role_rows"] if row.get("role_id") != "delegated_sub_agent_execution"]
for idx, row in enumerate(doc["required_role_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROLE_JSON="${TMP_ROOT}/role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROLE_REPO}" \
  --json-only >"${ROLE_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed missing role row"
  exit 1
fi

python3 - <<'PY' "${ROLE_JSON}"
import json
import os
import pathlib
import sys

status_key = os.environ["AGENT_HANDOFF_STATUS_KEY"]
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
structure_error = os.environ["AGENT_HANDOFF_ERR_STRUCTURE"]
payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload[status_key] == fail_status, payload
assert payload["error_code"] == structure_error, payload
assert payload["agent_handoff_row_coverage_status"] == fail_status, payload
assert payload["agent_handoff_row_identity_projection_status"] == fail_status, payload
assert payload["role_row_coverage_status"] == fail_status, payload
assert payload["role_row_identity_projection_status"] == fail_status, payload
assert any(
    row["reason"] == "missing_expected_rows" and "delegated_sub_agent_execution" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["family_id"] == "role_rows"
    and "delegated_sub_agent_execution" in row["missing_ids"]
    for row in payload["row_family_projection_rows"]
), payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/AGENT_HANDOFF_CONTRACT.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
heading = os.environ["AGENT_HANDOFF_ROLE_DELEGATED_HEADING"]
new = "### 2. Delegated execution role"
assert heading in text, text
path.write_text(text.replace(heading, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
fail_status = os.environ["AGENT_HANDOFF_FAIL_STATUS"]
err_handoff = os.environ["AGENT_HANDOFF_ERR_HANDOFF"]
heading = os.environ["AGENT_HANDOFF_ROLE_DELEGATED_HEADING"]
assert payload["protocol_root_agent_handoff_status"] == fail_status, payload
assert payload["error_code"] == err_handoff, payload
assert any(
    row["reason"] == "role_heading_missing" and row["marker"] == heading
    for row in payload["contract_marker_violations"]
), payload
PY

REGISTRY_REPO="${TMP_ROOT}/registry-drift-repo"
mirror_repo "${REGISTRY_REPO}"
python3 - <<'PY' "${REGISTRY_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["registered_top_level_entries"] = [
    row for row in doc["registered_top_level_entries"]
    if row.get("rel_path") != "identity/protocol/AGENT_HANDOFF_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == os.environ["AGENT_HANDOFF_FAIL_STATUS"], payload
assert payload["error_code"] == os.environ["AGENT_HANDOFF_ERR_HANDOFF"], payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "contract_not_registered"
    for row in payload["integration_violations"]
), payload
PY

ROUTING_REPO="${TMP_ROOT}/routing-drift-repo"
mirror_repo "${ROUTING_REPO}"
python3 - <<'PY' "${ROUTING_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["entry_question_projection"]:
    if row.get("rel_path") == "identity/protocol/AGENT_HANDOFF_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == os.environ["AGENT_HANDOFF_FAIL_STATUS"], payload
assert payload["error_code"] == os.environ["AGENT_HANDOFF_ERR_HANDOFF"], payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/IDENTITY_PROTOCOL.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = os.environ["AGENT_HANDOFF_IDENTITY_PROTOCOL_BOUNDARY_MARKER"]
new = "## Root agent-handoff boundary"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == os.environ["AGENT_HANDOFF_FAIL_STATUS"], payload
assert payload["error_code"] == os.environ["AGENT_HANDOFF_ERR_HANDOFF"], payload
assert payload["root_doc_anchor_status"] == os.environ["AGENT_HANDOFF_FAIL_STATUS"], payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/IDENTITY_PROTOCOL.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == os.environ["AGENT_HANDOFF_IDENTITY_PROTOCOL_BOUNDARY_MARKER"]
    for row in payload["root_doc_anchor_violations"]
), payload
PY

README_BINDING_REPO="${TMP_ROOT}/readme-binding-drift-repo"
mirror_repo "${README_BINDING_REPO}"
python3 - <<'PY' "${README_BINDING_REPO}/identity/protocol/README.md"
import os
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = os.environ["AGENT_HANDOFF_README_BINDING_MARKER"]
new = "These agent-handoff rules may be summarized directly in README prose."
assert old in text, text[:2500]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

README_BINDING_JSON="${TMP_ROOT}/readme-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${README_BINDING_REPO}" \
  --json-only >"${README_BINDING_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed README binding drift"
  exit 1
fi

python3 - <<'PY' "${README_BINDING_JSON}"
import json
import os
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == os.environ["AGENT_HANDOFF_FAIL_STATUS"], payload
assert payload["error_code"] == os.environ["AGENT_HANDOFF_ERR_HANDOFF"], payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == os.environ["AGENT_HANDOFF_README_BINDING_MARKER"]
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root agent-handoff probes passed"
