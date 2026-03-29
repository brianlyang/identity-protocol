#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-agent-handoff-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "PASS_REQUIRED", payload
assert payload["role_count"] == 2, payload
assert payload["payload_field_count"] == 10, payload
assert payload["anchor_count"] == 5, payload
assert payload["handoff_proof_count"] == 5, payload
assert payload["handoff_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["agent_handoff_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_row_family_count"] == 8, payload
assert payload["agent_handoff_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["role_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["payload_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["anchor_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["handoff_proof_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["handoff_limit_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["collapse_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
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
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["agent_handoff_completeness_rows"] = [
    row
    for row in doc["agent_handoff_completeness_rows"]
    if row.get("completeness_id") != "explicit_agent_handoff_row_families"
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert any(
    row["field"] == "agent_handoff_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "explicit_agent_handoff_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_agent_handoff_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;"
new = "1. required role, payload, anchor, handoff-proof, and collapse rows must remain explicit as separate machine-readable families;"
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "missing_agent_handoff_completeness_surface_rows"
    and "required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "agent_handoff_completeness_surface"
    and row["reason"] == "extra_agent_handoff_completeness_surface_rows"
    and "required role, payload, anchor, handoff-proof, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "agent_handoff_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == ["required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["unexpected_ids"] == ["required role, payload, anchor, handoff-proof, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root agent-handoff completeness discipline" \
  $'\n---\n\n## Root error-terminality completeness discipline' \
  "1. required role, payload, anchor, handoff-proof, handoff-limit, and collapse rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_agent_handoff.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root agent-handoff validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "PASS_REQUIRED", payload
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
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["agent_handoff_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert payload["agent_handoff_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["handoff_proof_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["handoff_proof_row_identity_projection_status"] == "FAIL_REQUIRED", payload
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-002", payload
assert payload["agent_handoff_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["agent_handoff_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["role_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["role_row_identity_projection_status"] == "FAIL_REQUIRED", payload
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
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 2. Delegated sub-agent execution role"
new = "### 2. Delegated execution role"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert any(
    row["reason"] == "role_heading_missing" and row["marker"] == "### 2. Delegated sub-agent execution role"
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/IDENTITY_PROTOCOL.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root agent-handoff completeness boundary"
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/IDENTITY_PROTOCOL.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root agent-handoff completeness boundary"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

README_BINDING_REPO="${TMP_ROOT}/readme-binding-drift-repo"
mirror_repo "${README_BINDING_REPO}"
python3 - <<'PY' "${README_BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These agent-handoff-completeness rules must remain bound to canonical agent-handoff-completeness rows rather than drifting into soft summary prose."
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
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_agent_handoff_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RAH-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These agent-handoff-completeness rules must remain bound to canonical agent-handoff-completeness rows rather than drifting into soft summary prose."
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root agent-handoff probes passed"
