#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-error-terminality-ci"
protocol_root_probe_define_full_mirror

assert_stale_reason_present() {
  local json_file="$1"
  local expected_reason="$2"
  python3 - <<'PY' "${json_file}" "${expected_reason}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
reason = sys.argv[2]
assert reason in payload.get("stale_reasons", []), payload
PY
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "PASS_REQUIRED", payload
assert payload["error_class_count"] == 7, payload
assert payload["differentiation_count"] == 7, payload
assert payload["error_terminality_proof_count"] == 7, payload
assert payload["error_terminality_limit_count"] == 7, payload
assert payload["collapse_count"] == 7, payload
assert payload["error_terminality_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_family_count"] == 7, payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["error_terminality_completeness_surface"]["entry_count"] == 5, payload
assert payload["error_terminality_completeness_surface"]["extraction_violations"] == [], payload
assert any(row["family_id"] == "error_terminality_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "error_terminality_completeness_surface" for row in payload["row_family_projection_rows"]), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["error_terminality_completeness_rows"] = [
    row for row in doc["error_terminality_completeness_rows"]
    if row.get("completeness_id") != "explicit_error_terminality_row_families"
]
for idx, row in enumerate(doc["error_terminality_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["field"] == "error_terminality_completeness_rows"
    and row["reason"] == "missing_error_terminality_completeness_rows"
    and "explicit_error_terminality_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(row for row in payload["row_family_projection_rows"] if row["family_id"] == "error_terminality_completeness_rows")
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_error_terminality_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/completeness-row-order-drift-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["error_terminality_completeness_rows"][1]["order"] = doc["error_terminality_completeness_rows"][0]["order"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/completeness-row-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed completeness row non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["field"] == "error_terminality_completeness_rows"
    and row["reason"] == "error_terminality_completeness_row_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "error_terminality_completeness_rows"
    and row["reason"] == "error_terminality_completeness_row_order_mismatch"
    for row in payload["terminality_violations"]
), payload
assert any(
    reason == "structure_violation:error_terminality_completeness_rows:error_terminality_completeness_row_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    reason == "error_terminality_violation:error_terminality_completeness_rows:error_terminality_completeness_row_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "error_terminality_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

assert_stale_reason_present "${COMPLETENESS_ROW_ORDER_JSON}" "structure_violation:error_terminality_completeness_rows:error_terminality_completeness_row_order_non_contiguous"
assert_stale_reason_present "${COMPLETENESS_ROW_ORDER_JSON}" "error_terminality_violation:error_terminality_completeness_rows:error_terminality_completeness_row_order_mismatch"

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required error-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;"
new = "1. required error-class, differentiation, proof, and collapse rows must remain explicit as separate machine-readable families;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "missing_error_terminality_completeness_surface_rows"
    and "required error-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "extra_error_terminality_completeness_surface_rows"
    and "required error-class, differentiation, proof, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(row for row in payload["row_family_projection_rows"] if row["family_id"] == "error_terminality_completeness_surface")
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == ["required error-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["unexpected_ids"] == ["required error-class, differentiation, proof, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_PHRASE_REPO="${TMP_ROOT}/completeness-surface-phrase-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_PHRASE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_PHRASE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. runtime or validator code must not finalize error-terminality truth while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code must not finalize error-terminality truth while missing row identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_PHRASE_JSON="${TMP_ROOT}/completeness-surface-phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_SURFACE_PHRASE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_PHRASE_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed completeness surface phrase drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize error-terminality truth while missing or unexpected row identities remain known only internally;"
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "error_terminality_completeness_surface_phrase_order_mismatch"
    for row in payload["terminality_violations"]
), payload
assert any(
    reason == "error_terminality_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_phrase_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "error_terminality_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize error-terminality truth while missing row identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

assert_stale_reason_present "${COMPLETENESS_SURFACE_PHRASE_JSON}" "error_terminality_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_phrase_order_mismatch"

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root error-terminality completeness discipline" \
  "## Root truth-lifecycle completeness discipline" \
  "1. required error-class, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "error_terminality_completeness_surface_order_mismatch"
    for row in payload["terminality_violations"]
), payload
assert any(
    reason == "error_terminality_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "error_terminality_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_REPO="${TMP_ROOT}/completeness-surface-order-non-contiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
section_marker = "## Root error-terminality completeness discipline"
target = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
replacement = "1. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
replaced = False
in_section = False
for idx, line in enumerate(lines):
    stripped = line.strip()
    if stripped == section_marker:
        in_section = True
        continue
    if not in_section:
        continue
    if stripped.startswith("## ") or stripped == "---":
        break
    if stripped == target:
        indent = line[: len(line) - len(line.lstrip())]
        lines[idx] = f"{indent}{replacement}"
        replaced = True
        break
assert replaced, section_marker
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_JSON="${TMP_ROOT}/completeness-surface-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed completeness surface non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "error_terminality_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "error_terminality_completeness_surface_order_mismatch"
    for row in payload["terminality_violations"]
), payload
assert any(
    reason == "structure_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    reason == "error_terminality_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "error_terminality_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

assert_stale_reason_present "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_JSON}" "structure_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_order_non_contiguous"
assert_stale_reason_present "${COMPLETENESS_SURFACE_ORDER_NON_CONTIGUOUS_JSON}" "error_terminality_violation:error_terminality_completeness_surface:error_terminality_completeness_surface_order_mismatch"

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_error_terminality_proof_rows"] = [
    row for row in doc["required_error_terminality_proof_rows"] if row.get("proof_id") != "support_explanatory_demotion_error_terminality_proof"
]
for idx, row in enumerate(doc["required_error_terminality_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert payload["error_terminality_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "support_explanatory_demotion_error_terminality_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_error_terminality_proof_rows"
)
assert proof_row["expected_count"] == 7, payload
assert proof_row["actual_count"] == 6, payload
assert proof_row["missing_ids"] == ["support_explanatory_demotion_error_terminality_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ERROR_REPO="${TMP_ROOT}/error-drift-repo"
mirror_repo "${ERROR_REPO}"
python3 - <<'PY' "${ERROR_REPO}/identity/protocol/mappings/root-error-terminality.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_error_class_rows"]:
    if row.get("error_class_id") == "binding_integrity_error":
        row["error_class_id"] = "binding_integrity_error_alias"
        break
else:
    raise SystemExit("expected binding_integrity_error row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ERROR_JSON="${TMP_ROOT}/error-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ERROR_REPO}" \
  --json-only >"${ERROR_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed missing error-class row"
  exit 1
fi

python3 - <<'PY' "${ERROR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "binding_integrity_error" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "binding_integrity_error_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["error_terminality_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["error_terminality_row_identity_projection_status"] == "FAIL_REQUIRED", payload
error_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_error_class_rows"
)
assert error_row["expected_count"] == 7, payload
assert error_row["actual_count"] == 7, payload
assert error_row["missing_ids"] == ["binding_integrity_error"], payload
assert error_row["unexpected_ids"] == ["binding_integrity_error_alias"], payload
assert error_row["coverage_status"] == "PASS_REQUIRED", payload
assert error_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PHRASE_REPO="${TMP_ROOT}/phrase-drift-repo"
mirror_repo "${PHRASE_REPO}"
python3 - <<'PY' "${PHRASE_REPO}/identity/protocol/ERROR_TERMINALITY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "governed recovery-redirect error is separated from non-blocking observation error;"
new = "governed recovery-redirect error is close to non-blocking observation error;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHRASE_JSON="${TMP_ROOT}/phrase-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${PHRASE_REPO}" \
  --json-only >"${PHRASE_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed contract phrase drift"
  exit 1
fi

python3 - <<'PY' "${PHRASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
assert any(
    row["reason"] == "contract_phrase_missing" and row["marker"] == "governed recovery-redirect error is separated from non-blocking observation error;"
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
    if row.get("rel_path") != "identity/protocol/ERROR_TERMINALITY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
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
    if row.get("rel_path") == "identity/protocol/ERROR_TERMINALITY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root error-terminality completeness discipline"
new = "## Root error-terminality discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_error_terminality.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root error terminality validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_error_terminality_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-ERT-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "missing_error_terminality_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "error_terminality_completeness_surface"
    and row["reason"] == "error_terminality_completeness_surface_section_missing"
    for row in payload["structure_violations"]
), payload
surface_row = next(row for row in payload["row_family_projection_rows"] if row["family_id"] == "error_terminality_completeness_surface")
assert surface_row["actual_count"] == 0, payload
assert surface_row["coverage_status"] == "FAIL_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root error-terminality completeness discipline"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root error terminality probes passed"
