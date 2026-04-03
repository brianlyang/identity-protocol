#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-corpus-ci"

PROBE_REL_PATHS=(
  "scripts/root_contract_anchor_checks_common.py"
  "scripts/root_corpus_governance_common.py"
  "scripts/root_row_family_projection_common.py"
  "scripts/validate_protocol_root_corpus_governance.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

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

bump_yaml_row_order_by_id() {
  local path="$1"
  local collection_key="$2"
  local id_field="$3"
  local row_id="$4"
  python3 - <<'PY' "${path}" "${collection_key}" "${id_field}" "${row_id}"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
collection_key = sys.argv[2]
id_field = sys.argv[3]
row_id = sys.argv[4]

doc = yaml.safe_load(path.read_text(encoding="utf-8"))
rows = doc[collection_key]
for row in rows:
    if str(row.get(id_field) or "") == row_id:
        row["order"] = int(row["order"]) + 1
        break
else:
    raise SystemExit(f"{row_id} not found in {collection_key}")

path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY
}

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

GOVERNANCE_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "next(marker for marker in EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'] if marker.startswith('## Root ') and marker.endswith('completeness discipline'))"
)"
GOVERNANCE_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "list(EXPECTED_GOVERNANCE_COMPLETENESS_ROWS.values())[0]['order']"
)"
GOVERNANCE_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "list(EXPECTED_GOVERNANCE_COMPLETENESS_ROWS.values())[0]['contract_phrase']"
)"
GOVERNANCE_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "list(EXPECTED_GOVERNANCE_COMPLETENESS_ROWS.values())[1]['order']"
)"
GOVERNANCE_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "list(EXPECTED_GOVERNANCE_COMPLETENESS_ROWS.values())[1]['contract_phrase']"
)"
GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_ID="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_governance" \
    "tuple(EXPECTED_GOVERNANCE_COMPLETENESS_ROWS.keys())[1]"
)"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_family_count"] == 9, payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_count"] == 5, payload
assert payload["governance_completeness_surface"]["entry_count"] == 5, payload
assert payload["governance_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["registered_top_level_count"] == payload["actual_top_level_count"], payload
assert "root_contract" in payload["corpus_class_profile_ids"], payload
assert "business_domain_example" in payload["forbidden_content_class_ids"], payload
assert payload["root_index_class_projection_count"] == 6, payload
assert payload["root_index_class_projection_surface"]["entry_count"] == 6, payload
assert payload["root_maintenance_guardrail_count"] == 6, payload
assert payload["root_maintenance_guardrail_surface"]["entry_count"] == 6, payload
assert any(row["family_id"] == "root_index_class_projections" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "root_index_class_projection_surface" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "root_maintenance_guardrails" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "root_maintenance_guardrail_surface" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "governance_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "governance_completeness_surface" for row in payload["row_family_projection_rows"]), payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-governance-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["governance_completeness_rows"] = doc["governance_completeness_rows"][:-1]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-governance-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after removing governance completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_family_count"] == 9, payload
assert payload["governance_completeness_row_count"] == 4, payload
assert any(
    row["field"] == "governance_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "fail_close_preserves_governance_identity_projection" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "governance_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_governance_identity_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["governance_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["governance_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["governance_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${PROFILE_REPO}"
python3 - <<'PY' "${PROFILE_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["corpus_class_profiles"] = [
    row for row in doc["corpus_class_profiles"]
    if row.get("corpus_class") != "root_contract"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${PROFILE_REPO}" \
  --json-only >"${PROFILE_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after removing corpus-class profile row"
  exit 1
fi

python3 - <<'PY' "${PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "corpus_class_profiles" and row["reason"] == "missing_expected_corpus_classes" and "root_contract" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "corpus_class_profiles"
)
assert profile_row["expected_count"] == 5, payload
assert profile_row["actual_count"] == 4, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

GUARDRAIL_REGISTRY_REPO="${TMP_ROOT}/guardrail-registry-repo"
mirror_repo "${GUARDRAIL_REGISTRY_REPO}"
python3 - <<'PY' "${GUARDRAIL_REGISTRY_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["root_maintenance_guardrails"] = [
    row for row in doc["root_maintenance_guardrails"]
    if row.get("guardrail_label") != "protocol repo authority is exclusive"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

GUARDRAIL_REGISTRY_JSON="${TMP_ROOT}/guardrail-registry.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GUARDRAIL_REGISTRY_REPO}" \
  --json-only >"${GUARDRAIL_REGISTRY_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after removing root maintenance guardrail row"
  exit 1
fi

python3 - <<'PY' "${GUARDRAIL_REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "root_maintenance_guardrails"
    and row["reason"] == "missing_root_maintenance_guardrails"
    and "protocol repo authority is exclusive" in row.get("guardrail_labels", [])
    for row in payload["structure_violations"]
), payload
guardrail_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_maintenance_guardrails"
)
assert guardrail_row["expected_count"] == 6, payload
assert guardrail_row["actual_count"] == 5, payload
assert guardrail_row["missing_ids"] == ["protocol repo authority is exclusive"], payload
assert guardrail_row["unexpected_ids"] == [], payload
assert guardrail_row["coverage_status"] == "FAIL_REQUIRED", payload
assert guardrail_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROJECTION_BINDING_REPO="${TMP_ROOT}/projection-binding-repo"
mirror_repo "${PROJECTION_BINDING_REPO}"
python3 - <<'PY' "${PROJECTION_BINDING_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["root_index_class_projections"]:
    if row.get("projection_label") == "governed subdomain protocol extensions":
        row["bound_corpus_classes"] = []
        break
else:
    raise SystemExit("expected governed subdomain protocol extensions row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROJECTION_BINDING_JSON="${TMP_ROOT}/projection-binding.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${PROJECTION_BINDING_REPO}" \
  --json-only >"${PROJECTION_BINDING_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after removing projection bound corpus classes"
  exit 1
fi

python3 - <<'PY' "${PROJECTION_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "root_index_class_projections"
    and row["reason"] == "bound_corpus_classes_missing"
    and row.get("projection_label") == "governed subdomain protocol extensions"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "root_index_class_projections"
    and row["reason"] == "missing_expected_bound_corpus_classes"
    and "governed_subdomain_extension" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
PY

GOVERNANCE_SURFACE_REPO="${TMP_ROOT}/governance-surface-drift-repo"
mirror_repo "${GOVERNANCE_SURFACE_REPO}"
python3 - <<'PY' "${GOVERNANCE_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root governance completeness discipline"
next_marker = "\n---\n\n## Root gateway-admissibility completeness discipline"
old = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
new = "2. expected row-family totals may be summarized informally once the corpus looks green;"
assert section_marker in text, text
assert next_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, after = rest.split(next_marker, 1)
assert old in section_body, section_body
section_body = section_body.replace(old, new, 1)
path.write_text(before + section_marker + section_body + next_marker + after, encoding="utf-8")
PY

GOVERNANCE_SURFACE_JSON="${TMP_ROOT}/governance-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GOVERNANCE_SURFACE_REPO}" \
  --json-only >"${GOVERNANCE_SURFACE_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed README governance completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${GOVERNANCE_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "governance_completeness_surface"
    and row["reason"] == "missing_governance_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "governance_completeness_surface"
    and row["reason"] == "extra_governance_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "governance_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["governance_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

GOVERNANCE_SURFACE_ORDER_REPO="${TMP_ROOT}/governance-surface-order-drift-repo"
mirror_repo "${GOVERNANCE_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows_in_section \
  "${GOVERNANCE_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_FIRST_PHRASE}" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_SECOND_PHRASE}"

GOVERNANCE_SURFACE_ORDER_JSON="${TMP_ROOT}/governance-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GOVERNANCE_SURFACE_ORDER_REPO}" \
  --json-only >"${GOVERNANCE_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed README governance completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${GOVERNANCE_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "governance_completeness_surface"
    and row["reason"] == "governance_completeness_surface_order_mismatch"
    for row in payload["structure_violations"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "1. required registered-top-level-entry, corpus-class-profile, root-index-class-projection, root-maintenance-guardrail, and forbidden-content-class rows must remain explicit as separate machine-readable row families;"
    for row in payload["root_doc_anchor_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "governance_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

GOVERNANCE_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/governance-surface-order-non-contiguous-repo"
mirror_repo "${GOVERNANCE_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${GOVERNANCE_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${GOVERNANCE_COMPLETENESS_SURFACE_FIRST_ORDER}"

GOVERNANCE_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/governance-surface-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GOVERNANCE_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${GOVERNANCE_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed README governance completeness surface non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${GOVERNANCE_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "governance_completeness_surface"
    and row["reason"] == "governance_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "governance_completeness_surface"
    and row["reason"] == "governance_completeness_surface_order_mismatch"
    for row in payload["structure_violations"]
), payload
assert any(
    reason == "structure_violation:governance_completeness_surface:governance_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    reason == "structure_violation:governance_completeness_surface:governance_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "governance_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_REPO="${TMP_ROOT}/governance-completeness-row-order-non-contiguous-repo"
mirror_repo "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_REPO}"
bump_yaml_row_order_by_id \
  "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml" \
  "governance_completeness_rows" \
  "completeness_id" \
  "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_ID}"

GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_JSON="${TMP_ROOT}/governance-completeness-row-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_REPO}" \
  --json-only >"${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed governance completeness row order non-contiguous drift"
  exit 1
fi

python3 - <<'PY' "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "governance_completeness_rows"
    and row["reason"] == "governance_completeness_rows_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "governance_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

assert_stale_reason_present \
  "${GOVERNANCE_COMPLETENESS_ROW_NONCONTIG_JSON}" \
  "structure_violation:governance_completeness_rows:governance_completeness_rows_order_non_contiguous"

GOVERNANCE_BINDING_REPO="${TMP_ROOT}/governance-binding-drift-repo"
mirror_repo "${GOVERNANCE_BINDING_REPO}"
python3 - <<'PY' "${GOVERNANCE_BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These governance-completeness rules must remain bound to canonical governance-completeness rows rather than drifting into soft summary prose."
new = "These governance completeness rules may be summarized freely once reviewers understand the intent."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

GOVERNANCE_BINDING_JSON="${TMP_ROOT}/governance-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GOVERNANCE_BINDING_REPO}" \
  --json-only >"${GOVERNANCE_BINDING_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed README governance binding drift"
  exit 1
fi

python3 - <<'PY' "${GOVERNANCE_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and "These governance-completeness rules must remain bound to canonical governance-completeness rows rather than drifting into soft summary prose." in row.get("marker", "")
    for row in payload["root_doc_anchor_violations"]
), payload
PY

FORBIDDEN_REPO="${TMP_ROOT}/forbidden-class-identity-repo"
mirror_repo "${FORBIDDEN_REPO}"
python3 - <<'PY' "${FORBIDDEN_REPO}/identity/protocol/mappings/root-corpus-registry.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["forbidden_content_classes"]:
    if row.get("class_id") == "business_domain_example":
        row["class_id"] = "business_domain_example_alias"
        break
else:
    raise SystemExit("expected business_domain_example row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

FORBIDDEN_JSON="${TMP_ROOT}/forbidden-class-identity.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${FORBIDDEN_REPO}" \
  --json-only >"${FORBIDDEN_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed forbidden-content-class identity drift"
  exit 1
fi

python3 - <<'PY' "${FORBIDDEN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["governance_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["governance_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "forbidden_content_classes" and row["reason"] == "missing_expected_class_ids" and "business_domain_example" in row.get("class_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "forbidden_content_classes" and row["reason"] == "extra_unreferenced_class_ids" and "business_domain_example_alias" in row.get("class_ids", [])
    for row in payload["structure_violations"]
), payload
forbidden_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "forbidden_content_classes"
)
assert forbidden_row["expected_count"] == 3, payload
assert forbidden_row["actual_count"] == 3, payload
assert forbidden_row["missing_ids"] == ["business_domain_example"], payload
assert forbidden_row["unexpected_ids"] == ["business_domain_example_alias"], payload
assert forbidden_row["coverage_status"] == "PASS_REQUIRED", payload
assert forbidden_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SURFACE_LABEL_REPO="${TMP_ROOT}/surface-label-repo"
mirror_repo "${SURFACE_LABEL_REPO}"
python3 - <<'PY' "${SURFACE_LABEL_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "2. **constitutions**"
new = "2. **constitutional files**"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

SURFACE_LABEL_JSON="${TMP_ROOT}/surface-label.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${SURFACE_LABEL_REPO}" \
  --json-only >"${SURFACE_LABEL_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after root-index surface label drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_LABEL_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "root_index_class_projection_surface"
    and row["reason"] == "missing_root_index_projection_labels"
    and "constitutions" in row.get("projection_labels", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "root_index_class_projection_surface"
    and row["reason"] == "extra_root_index_projection_labels"
    and "constitutional files" in row.get("projection_labels", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_index_class_projection_surface"
)
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert "constitutions" in surface_row["missing_ids"], payload
assert "constitutional files" in surface_row["unexpected_ids"], payload
PY

GUARDRAIL_SURFACE_REPO="${TMP_ROOT}/guardrail-surface-repo"
mirror_repo "${GUARDRAIL_SURFACE_REPO}"
python3 - <<'PY' "${GUARDRAIL_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "2. **machine verdict is adjudication, not philosophy source**"
new = "2. **machine verdict is adjudication, not ontology source**"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

GUARDRAIL_SURFACE_JSON="${TMP_ROOT}/guardrail-surface.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${GUARDRAIL_SURFACE_REPO}" \
  --json-only >"${GUARDRAIL_SURFACE_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed after maintenance-guardrail surface label drift"
  exit 1
fi

python3 - <<'PY' "${GUARDRAIL_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "root_maintenance_guardrail_surface"
    and row["reason"] == "missing_root_maintenance_guardrail_labels"
    and "machine verdict is adjudication, not philosophy source" in row.get("guardrail_labels", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "root_maintenance_guardrail_surface"
    and row["reason"] == "extra_root_maintenance_guardrail_labels"
    and "machine verdict is adjudication, not ontology source" in row.get("guardrail_labels", [])
    for row in payload["structure_violations"]
), payload
guardrail_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_maintenance_guardrail_surface"
)
assert guardrail_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert guardrail_surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert "machine verdict is adjudication, not philosophy source" in guardrail_surface_row["missing_ids"], payload
assert "machine verdict is adjudication, not ontology source" in guardrail_surface_row["unexpected_ids"], payload
PY

MARKER_REPO="${TMP_ROOT}/missing-marker-repo"
mirror_repo "${MARKER_REPO}"
python3 - <<'PY' "${MARKER_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root maintenance guardrails"
new = "## Root maintenance lane guardrails"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

MARKER_JSON="${TMP_ROOT}/missing-marker.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${MARKER_REPO}" \
  --json-only >"${MARKER_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed after required marker removal"
  exit 1
fi

python3 - <<'PY' "${MARKER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any("README.md:required_marker_missing" in reason for reason in payload["stale_reasons"]), payload
PY

EXTRA_REPO="${TMP_ROOT}/extra-entry-repo"
mirror_repo "${EXTRA_REPO}"
printf 'temporary closure note\n' > "${EXTRA_REPO}/identity/protocol/TEMP_CLOSURE_NOTE.md"

EXTRA_JSON="${TMP_ROOT}/extra-entry.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${EXTRA_REPO}" \
  --json-only >"${EXTRA_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with unregistered top-level entry"
  exit 1
fi

python3 - <<'PY' "${EXTRA_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    row["field"] == "registered_top_level_entries" and row["reason"] == "extra_root_entries" and "identity/protocol/TEMP_CLOSURE_NOTE.md" in row.get("rel_paths", [])
    for row in payload["structure_violations"]
), payload
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "registered_top_level_entries"
)
assert "identity/protocol/TEMP_CLOSURE_NOTE.md" in entry_row["unexpected_ids"], payload
assert entry_row["coverage_status"] == "FAIL_REQUIRED", payload
assert entry_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

WORKBOOK_REPO="${TMP_ROOT}/workbook-pollution-repo"
mirror_repo "${WORKBOOK_REPO}"
cat >> "${WORKBOOK_REPO}/identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md" <<'TXT'

### ISSUE-999
- `status`: OPEN
TXT

WORKBOOK_JSON="${TMP_ROOT}/workbook-pollution.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${WORKBOOK_REPO}" \
  --json-only >"${WORKBOOK_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with workbook issue pollution"
  exit 1
fi

python3 - <<'PY' "${WORKBOOK_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-003", payload
assert any(hit["class_id"] == "workbook_issue_projection" for hit in payload["forbidden_content_hits"]), payload
PY

BUSINESS_REPO="${TMP_ROOT}/business-pollution-repo"
mirror_repo "${BUSINESS_REPO}"
cat >> "${BUSINESS_REPO}/identity/protocol/AGENT_HANDOFF_CONTRACT.md" <<'TXT'

Example: WeChat Shop store manager routing note.
TXT

BUSINESS_JSON="${TMP_ROOT}/business-pollution.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${BUSINESS_REPO}" \
  --json-only >"${BUSINESS_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed with business-domain example pollution"
  exit 1
fi

python3 - <<'PY' "${BUSINESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-003", payload
assert any(hit["class_id"] == "business_domain_example" for hit in payload["forbidden_content_hits"]), payload
PY

ROOT_CONTRACT_REPO="${TMP_ROOT}/root-contract-profile-repo"
mirror_repo "${ROOT_CONTRACT_REPO}"
python3 - <<'PY' "${ROOT_CONTRACT_REPO}/identity/protocol/IDENTITY_DISCOVERY.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Runtime adjudication boundary"
new = "## Runtime resolution boundary"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ROOT_CONTRACT_JSON="${TMP_ROOT}/root-contract-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${ROOT_CONTRACT_REPO}" \
  --json-only >"${ROOT_CONTRACT_JSON}"; then
  echo "[FAIL] root corpus validator unexpectedly passed after root-contract class marker drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_CONTRACT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert any(
    "IDENTITY_DISCOVERY.md:required_marker_missing:## Runtime adjudication boundary" in reason
    for reason in payload["stale_reasons"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root governance completeness discipline"
new = "## Root governance completeness"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_governance.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root corpus governance validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_governance_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCG-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason == "root_doc_anchor_violation:identity/protocol/README.md:required_marker_missing:## Root governance completeness discipline"
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root governance completeness discipline"
    for row in payload["root_doc_anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus governance probes passed"
