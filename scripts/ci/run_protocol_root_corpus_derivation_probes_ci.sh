#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-derivation-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_derivation_common.py"
  "scripts/validate_protocol_root_corpus_derivation.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["derivation_row_family_count"] == 3, payload
assert payload["derivation_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["derivation_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["derivation_completeness_row_count"] == 5, payload
assert payload["derivation_completeness_surface"]["entry_count"] == 5, payload
assert payload["derivation_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["permitted_current_turn_root_corpus_class"] == "machine_registry_directory", payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["derivation_completeness_rows"] = doc["derivation_completeness_rows"][:-1]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed after removing derivation completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-002", payload
assert payload["derivation_row_family_count"] == 3, payload
assert payload["derivation_completeness_row_count"] == 4, payload
assert payload["derivation_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["derivation_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "derivation_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "fail_close_preserves_derivation_identity_projection" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_derivation_identity_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

MISSING_CLASS_REPO="${TMP_ROOT}/missing-class-repo"
mirror_repo "${MISSING_CLASS_REPO}"
python3 - <<'PY' "${MISSING_CLASS_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["derivation_class_profiles"] = [
    row for row in doc["derivation_class_profiles"]
    if row.get("corpus_class") != "demoted_support_directory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_CLASS_JSON="${TMP_ROOT}/missing-class.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${MISSING_CLASS_REPO}" \
  --json-only >"${MISSING_CLASS_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed after removing derivation class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_CLASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-002", payload
assert payload["derivation_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["derivation_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "derivation_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_class_profiles"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 7, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == [], payload
assert class_row["coverage_status"] == "FAIL_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_class_profiles"]:
    if row.get("corpus_class") == "demoted_support_directory":
        row["corpus_class"] = "demoted_support_directory_alias"
        break
else:
    raise SystemExit("expected demoted_support_directory row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-002", payload
assert payload["derivation_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["derivation_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "derivation_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "derivation_class_profiles" and row["reason"] == "extra_unregistered_classes" and "demoted_support_directory_alias" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_class_profiles"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 8, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == ["demoted_support_directory_alias"], payload
assert class_row["coverage_status"] == "PASS_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SURFACE_REPO="${TMP_ROOT}/surface-drift-repo"
mirror_repo "${SURFACE_REPO}"
python3 - <<'PY' "${SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root derivation completeness discipline"
next_marker = "\n---\n\n## Root transition completeness discipline"
old = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
new = "2. expected row-family total and emitted row-family total may be summarized informally once counts look green;"
assert section_marker in text, text
assert next_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, after = rest.split(next_marker, 1)
assert old in section_body, section_body
section_body = section_body.replace(old, new, 1)
path.write_text(before + section_marker + section_body + next_marker + after, encoding="utf-8")
PY

SURFACE_JSON="${TMP_ROOT}/surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${SURFACE_REPO}" \
  --json-only >"${SURFACE_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed README derivation completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "missing_derivation_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "extra_derivation_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/derivation-completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root derivation completeness discipline" \
  "## Root transition completeness discipline" \
  "1. required derivation-class-profile rows must remain explicit as a separate machine-readable row family;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/derivation-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed derivation completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert payload["derivation_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["derivation_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "derivation_completeness_surface"
    and row["reason"] == "derivation_completeness_surface_order_mismatch"
    for row in payload["derivation_violations"]
), payload
assert any(
    "derivation_violation:derivation_completeness_surface:derivation_completeness_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "derivation_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

BINDING_REPO="${TMP_ROOT}/binding-drift-repo"
mirror_repo "${BINDING_REPO}"
python3 - <<'PY' "${BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These derivation-completeness rules must remain bound to canonical derivation-completeness rows rather than drifting into soft summary prose."
new = "These derivation completeness rules may be summarized freely once the main idea is understood."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

BINDING_JSON="${TMP_ROOT}/binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${BINDING_REPO}" \
  --json-only >"${BINDING_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed README derivation binding drift"
  exit 1
fi

python3 - <<'PY' "${BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and "These derivation-completeness rules must remain bound to canonical derivation-completeness rows rather than drifting into soft summary prose." in row.get("marker", "")
    for row in payload["anchor_violations"]
), payload
PY

SUPPORT_REPO="${TMP_ROOT}/support-parent-drift-repo"
mirror_repo "${SUPPORT_REPO}"
python3 - <<'PY' "${SUPPORT_REPO}/identity/protocol/mappings/root-corpus-derivation.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["derivation_class_profiles"]:
    if row["corpus_class"] == "root_contract":
        row["allowed_upstream_classes"].append("demoted_support_directory")
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUPPORT_JSON="${TMP_ROOT}/support-parent-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${SUPPORT_REPO}" \
  --json-only >"${SUPPORT_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed demoted-support parent drift"
  exit 1
fi

python3 - <<'PY' "${SUPPORT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert any(
    row["reason"] in {"law_bearing_class_must_not_derive_from_demoted_support", "allowed_upstream_classes_mismatch"}
    and row.get("corpus_class") == "root_contract"
    for row in payload["derivation_violations"]
), payload
PY

QUESTION_REPO="${TMP_ROOT}/question-routing-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_redirect"]["forbidden_root_corpus_classes"] = [
    item for item in doc["adjudication_redirect"]["forbidden_root_corpus_classes"]
    if item != "bottom_theory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed adjudication forbidden-class drift"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert any(
    row["reason"] == "current_turn_forbidden_root_classes_mismatch"
    for row in payload["derivation_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## One-way derivation discipline"
new = "## One way derivation discipline"
assert old in text, text[:800]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_derivation.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus derivation validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_derivation_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCD-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus derivation probes passed"
