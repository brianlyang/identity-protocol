#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-identity-discovery-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "PASS_REQUIRED", payload
assert payload["section_count"] == 6, payload
assert payload["request_field_count"] == 5, payload
assert payload["response_field_count"] == 7, payload
assert payload["precedence_count"] == 3, payload
assert payload["activation_count"] == 3, payload
assert payload["error_field_count"] == 4, payload
assert payload["implementation_count"] == 4, payload
assert payload["discovery_proof_count"] == 6, payload
assert payload["discovery_limit_count"] == 6, payload
assert payload["collapse_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_row_count"] == 5, payload
assert payload["identity_discovery_row_family_count"] == 12, payload
assert payload["identity_discovery_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface"]["entry_count"] == 5, payload
assert payload["identity_discovery_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["family_id"] == "identity_discovery_completeness_rows"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["family_id"] == "identity_discovery_completeness_surface"
    for row in payload["row_family_projection_rows"]
), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/completeness-row-drift-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-identity-discovery.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["identity_discovery_completeness_rows"] = [
    row
    for row in doc["identity_discovery_completeness_rows"]
    if row.get("completeness_id") != "explicit_identity_discovery_row_families"
]
for idx, row in enumerate(doc["identity_discovery_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/completeness-row-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert any(
    row["field"] == "identity_discovery_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "explicit_identity_discovery_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_discovery_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_identity_discovery_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;"
new = "1. required section, request-field, response-field, precedence, activation, error-field, implementation, proof, and collapse rows must remain explicit as separate machine-readable families;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert any(
    row["field"] == "identity_discovery_completeness_surface"
    and row["reason"] == "missing_identity_discovery_completeness_surface_rows"
    and "required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "identity_discovery_completeness_surface"
    and row["reason"] == "extra_identity_discovery_completeness_surface_rows"
    and "required section, request-field, response-field, precedence, activation, error-field, implementation, proof, and collapse rows must remain explicit as separate machine-readable families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_discovery_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == ["required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["unexpected_ids"] == ["required section, request-field, response-field, precedence, activation, error-field, implementation, proof, and collapse rows must remain explicit as separate machine-readable families;"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY


IDENTITY_DISCOVERY_SURFACE_ORDER_REPO="${TMP_ROOT}/identity-discovery-completeness-surface-order-drift-repo"
mirror_repo "${IDENTITY_DISCOVERY_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${IDENTITY_DISCOVERY_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root identity-discovery completeness discipline" \
  "## Root agent-handoff completeness discipline" \
  "1. required section, request-field, response-field, precedence, activation, error-field, implementation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

IDENTITY_DISCOVERY_SURFACE_ORDER_JSON="${TMP_ROOT}/identity-discovery-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${IDENTITY_DISCOVERY_SURFACE_ORDER_REPO}" \
  --json-only >"${IDENTITY_DISCOVERY_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DISCOVERY_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "identity_discovery_completeness_surface"
    and row["reason"] == "identity_discovery_completeness_surface_order_mismatch"
    for row in payload["discovery_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_discovery_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-identity-discovery.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_discovery_proof_rows"] = [
    row for row in doc["required_discovery_proof_rows"]
    if row.get("proof_id") != "implementation_compliance_proof"
]
for idx, row in enumerate(doc["required_discovery_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed missing discovery proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert payload["identity_discovery_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "implementation_compliance_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_discovery_proof_rows"
)
assert proof_row["expected_count"] == 6, payload
assert proof_row["actual_count"] == 5, payload
assert proof_row["missing_ids"] == ["implementation_compliance_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

REQUEST_REPO="${TMP_ROOT}/request-drift-repo"
mirror_repo "${REQUEST_REPO}"
python3 - <<'PY' "${REQUEST_REPO}/identity/protocol/mappings/root-identity-discovery.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_request_field_rows"]:
    if row.get("request_field_id") == "forceReload":
        row["request_field_id"] = "forceReloadAlias"
        break
else:
    raise SystemExit("expected forceReload request field row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REQUEST_JSON="${TMP_ROOT}/request-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${REQUEST_REPO}" \
  --json-only >"${REQUEST_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed missing request row"
  exit 1
fi

python3 - <<'PY' "${REQUEST_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "forceReload" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "forceReloadAlias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["identity_discovery_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_discovery_row_identity_projection_status"] == "FAIL_REQUIRED", payload
request_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_request_field_rows"
)
assert request_row["expected_count"] == 5, payload
assert request_row["actual_count"] == 5, payload
assert request_row["missing_ids"] == ["forceReload"], payload
assert request_row["unexpected_ids"] == ["forceReloadAlias"], payload
assert request_row["coverage_status"] == "PASS_REQUIRED", payload
assert request_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_DISCOVERY.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Activation policy contract"
new = "## Activation policy"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["reason"] == "section_heading_missing" and row["marker"] == "## Activation policy contract"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_DISCOVERY.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
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
    if row.get("rel_path") == "identity/protocol/IDENTITY_DISCOVERY.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/IDENTITY_RUNTIME.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime identity-discovery consumption boundary"
new = "## Runtime identity-discovery boundary"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/IDENTITY_RUNTIME.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Runtime identity-discovery consumption boundary"
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
old = "These identity-discovery-completeness rules must remain bound to canonical identity-discovery-completeness rows rather than drifting into soft summary prose."
new = "These identity-discovery rules may be summarized directly in README prose."
assert old in text, text[:2500]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

README_BINDING_JSON="${TMP_ROOT}/readme-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_discovery.py" \
  --repo-root "${README_BINDING_REPO}" \
  --json-only >"${README_BINDING_JSON}"; then
  echo "[FAIL] root identity-discovery validator unexpectedly passed README binding drift"
  exit 1
fi

python3 - <<'PY' "${README_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_discovery_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RID-003", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These identity-discovery-completeness rules must remain bound to canonical identity-discovery-completeness rows rather than drifting into soft summary prose."
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root identity-discovery probes passed"
