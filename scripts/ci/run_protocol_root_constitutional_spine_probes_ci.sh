#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-constitutional-spine-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "PASS_REQUIRED", payload
assert payload["spine_entry_count"] == 4, payload
assert payload["spine_bridge_count"] == 5, payload
assert payload["philosophy_primacy_count"] == 4, payload
assert payload["constitutional_spine_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_family_count"] == 6, payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["philosophy_primacy_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["philosophy_primacy_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["philosophy_primacy_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["philosophy_primacy_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface"]["entry_count"] == 5, payload
assert payload["constitutional_spine_completeness_surface"]["extraction_violations"] == [], payload
assert [row["family_id"] for row in payload["row_family_projection_rows"]] == [
    "constitutional_entry_rows",
    "spine_bridge_rows",
    "philosophy_primacy_rows",
    "philosophy_primacy_surface",
    "constitutional_spine_completeness_rows",
    "constitutional_spine_completeness_surface",
], payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
primacy_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "philosophy_primacy_rows"
)
primacy_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "philosophy_primacy_surface"
)
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_rows"
)
completeness_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_surface"
)
assert entry_row["expected_count"] == payload["spine_entry_count"] == 4, payload
assert entry_row["actual_count"] == payload["spine_entry_count"] == 4, payload
assert entry_row["missing_ids"] == [], payload
assert entry_row["unexpected_ids"] == [], payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == payload["spine_bridge_count"] == 5, payload
assert bridge_row["actual_count"] == payload["spine_bridge_count"] == 5, payload
assert bridge_row["missing_ids"] == [], payload
assert bridge_row["unexpected_ids"] == [], payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert primacy_row["expected_count"] == payload["philosophy_primacy_count"] == 4, payload
assert primacy_row["actual_count"] == payload["philosophy_primacy_count"] == 4, payload
assert primacy_row["missing_ids"] == [], payload
assert primacy_row["unexpected_ids"] == [], payload
assert primacy_row["coverage_status"] == "PASS_REQUIRED", payload
assert primacy_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert primacy_surface_row["expected_count"] == payload["philosophy_primacy_count"] == 4, payload
assert primacy_surface_row["actual_count"] == payload["philosophy_primacy_count"] == 4, payload
assert primacy_surface_row["missing_ids"] == [], payload
assert primacy_surface_row["unexpected_ids"] == [], payload
assert primacy_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert primacy_surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert completeness_row["expected_count"] == payload["constitutional_spine_completeness_row_count"] == 5, payload
assert completeness_row["actual_count"] == payload["constitutional_spine_completeness_row_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert completeness_surface_row["expected_count"] == payload["constitutional_spine_completeness_row_count"] == 5, payload
assert completeness_surface_row["actual_count"] == payload["constitutional_spine_completeness_row_count"] == 5, payload
assert completeness_surface_row["missing_ids"] == [], payload
assert completeness_surface_row["unexpected_ids"] == [], payload
assert completeness_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-constitutional-spine-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["constitutional_spine_completeness_rows"] = [
    row
    for row in doc["constitutional_spine_completeness_rows"]
    if row.get("completeness_id") != "explicit_constitutional_spine_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-constitutional-spine-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert any(
    row["field"] == "constitutional_spine_completeness_rows"
    and row["reason"] == "missing_constitutional_spine_completeness_rows"
    and "explicit_constitutional_spine_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_constitutional_spine_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_IDENTITY_REPO="${TMP_ROOT}/constitutional-spine-completeness-identity-drift-repo"
mirror_repo "${COMPLETENESS_IDENTITY_REPO}"
python3 - <<'PY' "${COMPLETENESS_IDENTITY_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["constitutional_spine_completeness_rows"]:
    if row.get("completeness_id") == "hidden_constitutional_spine_identity_drift_forbidden":
        row["completeness_id"] = "hidden_constitutional_spine_identity_drift_forbidden_alias"
        break
else:
    raise SystemExit("expected constitutional spine completeness row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_IDENTITY_JSON="${TMP_ROOT}/constitutional-spine-completeness-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${COMPLETENESS_IDENTITY_REPO}" \
  --json-only >"${COMPLETENESS_IDENTITY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed completeness identity drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "constitutional_spine_completeness_rows"
    and row["reason"] == "missing_constitutional_spine_completeness_rows"
    and "hidden_constitutional_spine_identity_drift_forbidden" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "constitutional_spine_completeness_rows"
    and row["reason"] == "extra_constitutional_spine_completeness_rows"
    and "hidden_constitutional_spine_identity_drift_forbidden_alias" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == ["hidden_constitutional_spine_identity_drift_forbidden"], payload
assert completeness_row["unexpected_ids"] == ["hidden_constitutional_spine_identity_drift_forbidden_alias"], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/constitutional-spine-completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required constitutional-entry, spine-bridge, philosophy-primacy, and philosophy-primacy-surface rows must remain explicit as separate machine-readable families;"
new = "1. required constitutional-entry, spine-bridge, and philosophy-primacy rows must remain explicit as separate machine-readable families;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/constitutional-spine-completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert any(
    row["field"] == "constitutional_spine_completeness_surface"
    and row["reason"] == "missing_constitutional_spine_completeness_surface_rows"
    and "required constitutional-entry, spine-bridge, philosophy-primacy, and philosophy-primacy-surface rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "constitutional_spine_completeness_surface"
    and row["reason"] == "extra_constitutional_spine_completeness_surface_rows"
    and "required constitutional-entry, spine-bridge, and philosophy-primacy rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [
    "required constitutional-entry, spine-bridge, philosophy-primacy, and philosophy-primacy-surface rows must remain explicit as separate machine-readable families;"
], payload
assert surface_row["unexpected_ids"] == [
    "required constitutional-entry, spine-bridge, and philosophy-primacy rows must remain explicit as separate machine-readable families;"
], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/constitutional-spine-completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root constitutional-spine completeness discipline" \
  "## Root adjudication-surface discipline" \
  "1. required constitutional-entry, spine-bridge, philosophy-primacy, and philosophy-primacy-surface rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/constitutional-spine-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "constitutional_spine_completeness_surface"
    and row["reason"] == "constitutional_spine_completeness_surface_phrase_order_mismatch"
    for row in payload["projection_violations"]
), payload
assert any(
    row["field"] == "constitutional_spine_completeness_surface"
    and row["reason"] == "constitutional_spine_completeness_surface_order_mismatch"
    for row in payload["projection_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_spine_completeness_surface"
)
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

BRIDGE_REPO="${TMP_ROOT}/bridge-drift-repo"
mirror_repo "${BRIDGE_REPO}"
python3 - <<'PY' "${BRIDGE_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_spine_bridge_rows"] = [
    row for row in doc["required_spine_bridge_rows"]
    if row.get("bridge_id") != "philosophy_to_runtime_machine_authority_split"
]
for idx, row in enumerate(doc["required_spine_bridge_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

BRIDGE_JSON="${TMP_ROOT}/bridge-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${BRIDGE_REPO}" \
  --json-only >"${BRIDGE_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed missing bridge row"
  exit 1
fi

python3 - <<'PY' "${BRIDGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "philosophy_to_runtime_machine_authority_split" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == 5, payload
assert bridge_row["actual_count"] == 4, payload
assert bridge_row["missing_ids"] == ["philosophy_to_runtime_machine_authority_split"], payload
assert bridge_row["unexpected_ids"] == [], payload
assert bridge_row["coverage_status"] == "FAIL_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ENTRY_IDENTITY_REPO="${TMP_ROOT}/entry-identity-drift-repo"
mirror_repo "${ENTRY_IDENTITY_REPO}"
python3 - <<'PY' "${ENTRY_IDENTITY_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_constitutional_entry_rows"]:
    if row.get("rel_path") == "identity/protocol/IDENTITY_RUNTIME.md":
        row["rel_path"] = "identity/protocol/IDENTITY_RUNTIME_ALIAS.md"
        break
else:
    raise SystemExit("expected runtime constitutional entry row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ENTRY_IDENTITY_JSON="${TMP_ROOT}/entry-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${ENTRY_IDENTITY_REPO}" \
  --json-only >"${ENTRY_IDENTITY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed entry identity drift"
  exit 1
fi

python3 - <<'PY' "${ENTRY_IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["constitutional_entry_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_entry_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows"
    and "identity/protocol/IDENTITY_RUNTIME.md" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "unexpected_rows"
    and "identity/protocol/IDENTITY_RUNTIME_ALIAS.md" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["expected_count"] == 4, payload
assert entry_row["actual_count"] == 4, payload
assert entry_row["missing_ids"] == ["identity/protocol/IDENTITY_RUNTIME.md"], payload
assert entry_row["unexpected_ids"] == ["identity/protocol/IDENTITY_RUNTIME_ALIAS.md"], payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

BRIDGE_IDENTITY_REPO="${TMP_ROOT}/bridge-identity-drift-repo"
mirror_repo "${BRIDGE_IDENTITY_REPO}"
python3 - <<'PY' "${BRIDGE_IDENTITY_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_spine_bridge_rows"]:
    if row.get("bridge_id") == "philosophy_to_runtime_machine_authority_split":
        row["bridge_id"] = "philosophy_to_runtime_machine_authority_split_alias"
        break
else:
    raise SystemExit("expected bridge row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

BRIDGE_IDENTITY_JSON="${TMP_ROOT}/bridge-identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${BRIDGE_IDENTITY_REPO}" \
  --json-only >"${BRIDGE_IDENTITY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed bridge identity drift"
  exit 1
fi

python3 - <<'PY' "${BRIDGE_IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert payload["constitutional_spine_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["constitutional_spine_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["spine_bridge_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["spine_bridge_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows"
    and "philosophy_to_runtime_machine_authority_split" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "unexpected_rows"
    and "philosophy_to_runtime_machine_authority_split_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "constitutional_entry_rows"
)
bridge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "spine_bridge_rows"
)
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert bridge_row["expected_count"] == 5, payload
assert bridge_row["actual_count"] == 5, payload
assert bridge_row["missing_ids"] == ["philosophy_to_runtime_machine_authority_split"], payload
assert bridge_row["unexpected_ids"] == ["philosophy_to_runtime_machine_authority_split_alias"], payload
assert bridge_row["coverage_status"] == "PASS_REQUIRED", payload
assert bridge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROJECTION_REPO="${TMP_ROOT}/projection-drift-repo"
mirror_repo "${PROJECTION_REPO}"
python3 - <<'PY' "${PROJECTION_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["entry_authority_projection"]:
    if row.get("rel_path") == "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md":
        row["authority_mode"] = "frozen_law_only"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROJECTION_JSON="${TMP_ROOT}/projection-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${PROJECTION_REPO}" \
  --json-only >"${PROJECTION_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed authority projection drift"
  exit 1
fi

python3 - <<'PY' "${PROJECTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "root_corpus_authority" and row["reason"] == "authority_mode_mismatch"
    for row in payload["projection_violations"]
), payload
PY

MARKER_REPO="${TMP_ROOT}/marker-drift-repo"
mirror_repo "${MARKER_REPO}"
python3 - <<'PY' "${MARKER_REPO}/identity/protocol/IDENTITY_RUNTIME.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime consumption of the root-law bundle"
new = "## Runtime consumption of the law bundle"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

MARKER_JSON="${TMP_ROOT}/marker-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${MARKER_REPO}" \
  --json-only >"${MARKER_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed marker drift"
  exit 1
fi

python3 - <<'PY' "${MARKER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "entry_files"
    and row["reason"] == "required_marker_missing"
    and row["rel_path"] == "identity/protocol/IDENTITY_RUNTIME.md"
    and row["marker"] == "## Runtime consumption of the root-law bundle"
    for row in payload["projection_violations"]
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
for row in doc["registered_top_level_entries"]:
    if row.get("rel_path") == "identity/protocol/mappings":
        row["required_children"] = [
            child for child in row.get("required_children", [])
            if child != "root-constitutional-spine.v1.yaml"
        ]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed registry child drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "root_corpus_registry"
    and row["reason"] == "mappings_required_child_missing"
    and row["child"] == "root-constitutional-spine.v1.yaml"
    for row in payload["projection_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root constitutional-spine discipline"
new = "## Root constitutional spine discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root constitutional-spine discipline"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

PHILOSOPHY_ROW_REPO="${TMP_ROOT}/philosophy-row-drift-repo"
mirror_repo "${PHILOSOPHY_ROW_REPO}"
python3 - <<'PY' "${PHILOSOPHY_ROW_REPO}/identity/protocol/mappings/root-constitutional-spine.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["philosophy_primacy_rows"] = [
    row for row in doc.get("philosophy_primacy_rows", [])
    if row.get("primacy_label") != "philosophical primacy is not runtime-source primacy"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PHILOSOPHY_ROW_JSON="${TMP_ROOT}/philosophy-row-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${PHILOSOPHY_ROW_REPO}" \
  --json-only >"${PHILOSOPHY_ROW_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed philosophy-primacy row drift"
  exit 1
fi

python3 - <<'PY' "${PHILOSOPHY_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-002", payload
assert any(
    row["field"] == "philosophy_primacy_rows"
    and row["reason"] == "missing_expected_rows"
    and "philosophical primacy is not runtime-source primacy" in row["row_ids"]
    for row in payload["structure_violations"]
), payload
PY

PHILOSOPHY_SURFACE_REPO="${TMP_ROOT}/philosophy-surface-drift-repo"
mirror_repo "${PHILOSOPHY_SURFACE_REPO}"
python3 - <<'PY' "${PHILOSOPHY_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. **philosophical primacy is not runtime-source primacy**"
new = "4. **philosophical primacy is not machine-truth primacy**"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

PHILOSOPHY_SURFACE_JSON="${TMP_ROOT}/philosophy-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_constitutional_spine.py" \
  --repo-root "${PHILOSOPHY_SURFACE_REPO}" \
  --json-only >"${PHILOSOPHY_SURFACE_JSON}"; then
  echo "[FAIL] root constitutional spine validator unexpectedly passed philosophy-primacy surface drift"
  exit 1
fi

python3 - <<'PY' "${PHILOSOPHY_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_constitutional_spine_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCS-003", payload
assert any(
    row["field"] == "philosophy_primacy_surface"
    and row["reason"] == "surface_row_missing"
    and row["primacy_label"] == "philosophical primacy is not runtime-source primacy"
    for row in payload["projection_violations"]
), payload
PY

echo "[PASS] protocol root constitutional spine probes passed"
