#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-question-routing-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_gateway_admissibility_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/validate_protocol_root_corpus_question_routing.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 20, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["adjudication_redirect"]["question_class"] == "current_turn_legality", payload
assert payload["question_routing_row_family_count"] == 9, payload
assert payload["question_routing_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(
    "current_turn_legality" not in row["question_classes"]
    for row in payload["entry_question_projection"]
), payload
assert payload["root_question_discipline_stage_count"] == 8, payload
assert payload["root_question_discipline_stage_surface"]["entry_count"] == 8, payload
assert payload["entry_summary_stage_count"] == 4, payload
assert payload["entry_summary_stage_surface"]["entry_count"] == 4, payload
assert payload["question_routing_completeness_row_count"] == 5, payload
assert payload["question_routing_completeness_surface"]["entry_count"] == 5, payload
assert any(row["family_id"] == "root_question_discipline_stages" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "root_question_discipline_stage_surface" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "entry_summary_stages" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "entry_summary_stage_surface" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "question_routing_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "question_routing_completeness_surface" for row in payload["row_family_projection_rows"]), payload
assert {row["gateway_class"]: row["question_class"] for row in payload["gateway_question_projection"]} == {
    "constitution": "frozen_protocol_law",
    "runtime_constitution": "frozen_runtime_law",
    "root_contract": "frozen_domain_contract_law",
    "machine_registry_directory": "registry_resolution",
}, payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/question-routing-completeness-row-missing-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["question_routing_completeness_rows"] = [
    row for row in doc["question_routing_completeness_rows"]
    if row.get("completeness_id") != "explicit_question_routing_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/question-routing-completeness-row-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed missing question-routing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert any(
    row["field"] == "question_routing_completeness_rows"
    and row["reason"] == "missing_question_routing_completeness_rows"
    and "explicit_question_routing_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_routing_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_question_routing_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ROOT_QUESTION_STAGE_REPO="${TMP_ROOT}/root-question-stage-missing-repo"
mirror_repo "${ROOT_QUESTION_STAGE_REPO}"
python3 - <<'PY' "${ROOT_QUESTION_STAGE_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["root_question_discipline_stages"] = [
    row for row in doc["root_question_discipline_stages"]
    if row.get("stage_label") != "support-material question"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_QUESTION_STAGE_JSON="${TMP_ROOT}/root-question-stage-missing.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT_QUESTION_STAGE_REPO}" \
  --json-only >"${ROOT_QUESTION_STAGE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed missing root-question-discipline stage"
  exit 1
fi

python3 - <<'PY' "${ROOT_QUESTION_STAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert any(
    row["field"] == "root_question_discipline_stages"
    and row["reason"] == "missing_root_question_discipline_stages"
    and "support-material question" in row.get("stage_labels", [])
    for row in payload["structure_violations"]
), payload
stage_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_question_discipline_stages"
)
assert stage_row["expected_count"] == 8, payload
assert stage_row["actual_count"] == 7, payload
assert stage_row["missing_ids"] == ["support-material question"], payload
assert stage_row["unexpected_ids"] == [], payload
assert stage_row["coverage_status"] == "FAIL_REQUIRED", payload
assert stage_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SUMMARY_STAGE_REPO="${TMP_ROOT}/summary-stage-drift-repo"
mirror_repo "${SUMMARY_STAGE_REPO}"
python3 - <<'PY' "${SUMMARY_STAGE_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["entry_summary_stages"]:
    if row.get("stage_label") == "machine-consumed verdict surfaces last":
        row["terminal_machine_surfaces"] = ["mappings", "validators", "probes", "runtime_state"]
        break
else:
    raise SystemExit("expected machine-consumed verdict stage not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SUMMARY_STAGE_JSON="${TMP_ROOT}/summary-stage-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${SUMMARY_STAGE_REPO}" \
  --json-only >"${SUMMARY_STAGE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed entry-summary terminal-surface drift"
  exit 1
fi

python3 - <<'PY' "${SUMMARY_STAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "routing_violation:entry_summary_stages:terminal_machine_surfaces_mismatch",
        "routing_violation:entry_summary_stages:terminal_machine_surfaces_not_aligned_with_adjudication_redirect",
    )
), payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["question_class_profiles"] = [
    row for row in doc["question_class_profiles"]
    if row.get("question_class") != "support_material_lookup"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed after removing question-class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert payload["question_routing_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "missing_expected_question_classes" and "support_material_lookup" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_question_projection"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_question_projection"
)
assert profile_row["expected_count"] == 9, payload
assert profile_row["actual_count"] == 8, payload
assert profile_row["missing_ids"] == ["support_material_lookup"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_DRIFT_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_DRIFT_REPO}"
python3 - <<'PY' "${IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["question_class_profiles"]:
    if row.get("question_class") == "support_material_lookup":
        row["question_class"] = "support_material_lookup_alias"
        break
else:
    raise SystemExit("expected support_material_lookup row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_DRIFT_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${IDENTITY_DRIFT_REPO}" \
  --json-only >"${IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed question-class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert payload["question_routing_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["question_routing_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "missing_expected_question_classes" and "support_material_lookup" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "question_class_profiles" and row["reason"] == "extra_question_classes" and "support_material_lookup_alias" in row.get("question_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_question_projection"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_question_projection"
)
assert profile_row["expected_count"] == 9, payload
assert profile_row["actual_count"] == 9, payload
assert profile_row["missing_ids"] == ["support_material_lookup"], payload
assert profile_row["unexpected_ids"] == ["support_material_lookup_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

SUMMARY_SURFACE_REPO="${TMP_ROOT}/summary-surface-drift-repo"
mirror_repo "${SUMMARY_SURFACE_REPO}"
python3 - <<'PY' "${SUMMARY_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "2. **constitutions next**"
new = "2. **constitutional files next**"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

SUMMARY_SURFACE_JSON="${TMP_ROOT}/summary-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${SUMMARY_SURFACE_REPO}" \
  --json-only >"${SUMMARY_SURFACE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed entry-summary surface label drift"
  exit 1
fi

python3 - <<'PY' "${SUMMARY_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert any(
    "routing_violation:entry_summary_stage_surface:entry_summary_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_summary_stage_surface"
)
assert "constitutions next" in surface_row["missing_ids"], payload
assert "constitutional files next" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/question-routing-completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, entry-summary-stage, or route identities remain known only internally;"
new = "4. runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, or route identities remain known only internally;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/question-routing-completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed question-routing completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
expected_phrase = "runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, entry-summary-stage, or route identities remain known only internally;"
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert any(
    "routing_violation:question_routing_completeness_surface:question_routing_completeness_surface_phrase_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_routing_completeness_surface"
)
assert expected_phrase in surface_row["missing_ids"], payload
assert "runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, or route identities remain known only internally;" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/question-routing-completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root question-routing completeness discipline"
next_heading = "## Root design-question closure completeness discipline"
first = "1. required question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection rows must remain explicit as separate machine-readable row families;"
second = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
swapped_first = "1. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
swapped_second = "2. required question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection rows must remain explicit as separate machine-readable row families;"
assert section_marker in text, text
assert next_heading in text, text
before, rest = text.split(section_marker, 1)
section_body, sep, after = rest.partition(next_heading)
assert sep, rest[:4000]
assert first in section_body and second in section_body, section_body
section_body = section_body.replace(first, "__TEMP__", 1)
section_body = section_body.replace(second, swapped_second, 1)
section_body = section_body.replace("__TEMP__", swapped_first, 1)
path.write_text(before + section_marker + section_body + sep + after, encoding="utf-8")
PY

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/question-routing-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed question-routing completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    "routing_violation:question_routing_completeness_surface:question_routing_completeness_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "question_routing_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

ROOT_QUESTION_SURFACE_REPO="${TMP_ROOT}/root-question-surface-drift-repo"
mirror_repo "${ROOT_QUESTION_SURFACE_REPO}"
python3 - <<'PY' "${ROOT_QUESTION_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "2. **root-entry question**"
new = "2. **root-index question**"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ROOT_QUESTION_SURFACE_JSON="${TMP_ROOT}/root-question-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT_QUESTION_SURFACE_REPO}" \
  --json-only >"${ROOT_QUESTION_SURFACE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed root-question-discipline surface drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_QUESTION_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-002", payload
assert any(
    "routing_violation:root_question_discipline_stage_surface:root_question_discipline_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_question_discipline_stage_surface"
)
assert "root-entry question" in surface_row["missing_ids"], payload
assert "root-index question" in surface_row["unexpected_ids"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ROOT_ENTRY_REPO="${TMP_ROOT}/root-entry-drift-repo"
mirror_repo "${ROOT_ENTRY_REPO}"
python3 - <<'PY' "${ROOT_ENTRY_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_question_projection"][1]["question_classes"] = ["current_turn_legality"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_ENTRY_JSON="${TMP_ROOT}/root-entry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT_ENTRY_REPO}" \
  --json-only >"${ROOT_ENTRY_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed root-entry legality drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_ENTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "routing_violation:entry_question_projection:current_turn_legality_must_not_bind_to_root_entry",
        "routing_violation:entry_question_projection:entry_question_classes_mismatch",
    )
), payload
PY

REDIRECT_REPO="${TMP_ROOT}/redirect-drift-repo"
mirror_repo "${REDIRECT_REPO}"
python3 - <<'PY' "${REDIRECT_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_redirect"]["terminal_machine_surfaces"] = ["mappings", "validators", "probes", "runtime_state"]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REDIRECT_JSON="${TMP_ROOT}/redirect-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${REDIRECT_REPO}" \
  --json-only >"${REDIRECT_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed terminal-surface drift"
  exit 1
fi

python3 - <<'PY' "${REDIRECT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    "routing_violation:adjudication_redirect:terminal_machine_surfaces_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
PY

GATEWAY_QUESTION_REPO="${TMP_ROOT}/gateway-question-drift-repo"
mirror_repo "${GATEWAY_QUESTION_REPO}"
python3 - <<'PY' "${GATEWAY_QUESTION_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_question_projection"]:
    if row["gateway_class"] == "root_contract":
        row["question_class"] = "registry_resolution"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

GATEWAY_QUESTION_JSON="${TMP_ROOT}/gateway-question-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${GATEWAY_QUESTION_REPO}" \
  --json-only >"${GATEWAY_QUESTION_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed gateway-question drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    "routing_violation:gateway_question_projection:question_class_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
PY

ROOT_QUESTION_GATEWAY_STAGE_REPO="${TMP_ROOT}/root-question-gateway-stage-drift-repo"
mirror_repo "${ROOT_QUESTION_GATEWAY_STAGE_REPO}"
python3 - <<'PY' "${ROOT_QUESTION_GATEWAY_STAGE_REPO}/identity/protocol/mappings/root-corpus-question-routing.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["root_question_discipline_stages"]:
    if row.get("stage_label") == "gateway target question class preserved":
        row["bound_question_classes"] = [
            "frozen_protocol_law",
            "frozen_runtime_law",
            "frozen_domain_contract_law",
            "current_turn_legality",
        ]
        break
else:
    raise SystemExit("expected gateway target question class preserved row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_QUESTION_GATEWAY_STAGE_JSON="${TMP_ROOT}/root-question-gateway-stage-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ROOT_QUESTION_GATEWAY_STAGE_REPO}" \
  --json-only >"${ROOT_QUESTION_GATEWAY_STAGE_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed root-question gateway-stage drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_QUESTION_GATEWAY_STAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "routing_violation:root_question_discipline_stages:bound_question_classes_mismatch",
        "routing_violation:root_question_discipline_stages:stage_gateway_question_classes_mismatch",
    )
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "This question-routing discipline must remain bound to canonical root-question-discipline stage rows rather than becoming a freehand alternate question ladder."
new = "These question-routing rules must remain bound to canonical root-question-discipline stage rows rather than becoming a freehand alternate question ladder."
assert old in text, text[:600]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_question_routing.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus question-routing validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_question_routing_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCQR-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    "anchor_violation:identity/protocol/README.md:required_marker_missing" == reason
    for reason in payload["stale_reasons"]
), payload
PY

echo "[PASS] protocol root-corpus question-routing probes passed"
