#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-transition-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_derivation_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/root_row_family_projection_common.py"
  "scripts/validate_protocol_root_corpus_transition.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
# shellcheck source=../probe_fixture_shell_common.sh
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_transition" \
    "next(marker for marker in EXPECTED_ROOT_DOC_ANCHOR_CHECKS['identity/protocol/README.md'] if marker.startswith('## Root ') and marker.endswith('completeness discipline'))"
)"
TRANSITION_COMPLETENESS_SURFACE_FIRST_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_transition" \
    "list(EXPECTED_TRANSITION_COMPLETENESS_ROWS.values())[0]['order']"
)"
TRANSITION_COMPLETENESS_SURFACE_FIRST_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_transition" \
    "list(EXPECTED_TRANSITION_COMPLETENESS_ROWS.values())[0]['contract_phrase']"
)"
TRANSITION_COMPLETENESS_SURFACE_SECOND_ORDER="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_transition" \
    "list(EXPECTED_TRANSITION_COMPLETENESS_ROWS.values())[1]['order']"
)"
TRANSITION_COMPLETENESS_SURFACE_SECOND_PHRASE="$(
  resolve_python_module_expression \
    "validate_protocol_root_corpus_transition" \
    "list(EXPECTED_TRANSITION_COMPLETENESS_ROWS.values())[1]['contract_phrase']"
)"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["current_turn_allowed_root_surface"] == "machine_registry_directory", payload
assert payload["transition_row_family_count"] == 5, payload
assert payload["transition_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["surface_class_profile_count"] == 16, payload
assert payload["direct_root_target_edge_count"] == 14, payload
assert payload["strengthening_gateway_edge_count"] == 40, payload
assert payload["transition_completeness_row_count"] == 5, payload
assert payload["transition_completeness_surface"]["entry_count"] == 5, payload
assert payload["transition_completeness_surface"]["extraction_violations"] == [], payload
assert payload["transition_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-transition-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["transition_completeness_rows"] = doc["transition_completeness_rows"][:-1]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-transition-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed after removing transition completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["transition_row_family_count"] == 5, payload
assert payload["transition_completeness_row_count"] == 4, payload
assert payload["transition_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "transition_completeness_rows"
    and row["reason"] == "missing_expected_rows"
    and "fail_close_preserves_transition_identity_projection" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "transition_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_transition_identity_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["transition_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["transition_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["transition_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["surface_class_profiles"] = [
    row for row in doc["surface_class_profiles"]
    if row.get("surface_class") != "root_contract"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed after removing root-contract surface profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["transition_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "missing_expected_surface_classes" and "root_contract" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "surface_class_profiles"
)
edge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "direct_root_target_edges"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "strengthening_gateway_edges"
)
assert profile_row["expected_count"] == 16, payload
assert profile_row["actual_count"] == 15, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert edge_row["expected_count"] == 14, payload
assert edge_row["actual_count"] == 12, payload
assert edge_row["missing_ids"] == [
    "root_contract->governed_subdomain_extension",
    "root_contract->machine_registry_directory",
], payload
assert edge_row["unexpected_ids"] == [], payload
assert edge_row["coverage_status"] == "FAIL_REQUIRED", payload
assert edge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_DRIFT_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_DRIFT_REPO}"
python3 - <<'PY' "${IDENTITY_DRIFT_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row.get("surface_class") == "root_contract":
        row["surface_class"] = "root_contract_alias"
        break
else:
    raise SystemExit("expected root_contract row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_DRIFT_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${IDENTITY_DRIFT_REPO}" \
  --json-only >"${IDENTITY_DRIFT_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed surface-class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["transition_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "missing_expected_surface_classes" and "root_contract" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "surface_class_profiles" and row["reason"] == "extra_surface_classes" and "root_contract_alias" in row.get("surface_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "surface_class_profiles"
)
edge_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "direct_root_target_edges"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "strengthening_gateway_edges"
)
assert profile_row["expected_count"] == 16, payload
assert profile_row["actual_count"] == 16, payload
assert profile_row["missing_ids"] == ["root_contract"], payload
assert profile_row["unexpected_ids"] == ["root_contract_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert edge_row["expected_count"] == 14, payload
assert edge_row["actual_count"] == 14, payload
assert edge_row["missing_ids"] == [
    "root_contract->governed_subdomain_extension",
    "root_contract->machine_registry_directory",
], payload
assert edge_row["unexpected_ids"] == [
    "root_contract_alias->governed_subdomain_extension",
    "root_contract_alias->machine_registry_directory",
], payload
assert edge_row["coverage_status"] == "PASS_REQUIRED", payload
assert edge_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

OUTER_PROMOTION_REPO="${TMP_ROOT}/outer-promotion-drift-repo"
mirror_repo "${OUTER_PROMOTION_REPO}"
python3 - <<'PY' "${OUTER_PROMOTION_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row["surface_class"] == "outer_review_surface":
        row["direct_root_targets"] = ["root_contract"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

OUTER_PROMOTION_JSON="${TMP_ROOT}/outer-promotion-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${OUTER_PROMOTION_REPO}" \
  --json-only >"${OUTER_PROMOTION_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed outer direct-promotion drift"
  exit 1
fi

python3 - <<'PY' "${OUTER_PROMOTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    row["reason"] in {"outer_surface_must_not_directly_promote_root_law", "direct_root_targets_mismatch"}
    and row.get("surface_class") == "outer_review_surface"
    for row in payload["transition_violations"]
), payload
PY

CURRENT_TURN_REPO="${TMP_ROOT}/current-turn-drift-repo"
mirror_repo "${CURRENT_TURN_REPO}"
python3 - <<'PY' "${CURRENT_TURN_REPO}/identity/protocol/mappings/root-corpus-transition.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["surface_class_profiles"]:
    if row["surface_class"] == "root_index":
        row["direct_current_turn_legality_allowed"] = True
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

CURRENT_TURN_JSON="${TMP_ROOT}/current-turn-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${CURRENT_TURN_REPO}" \
  --json-only >"${CURRENT_TURN_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed current-turn legality drift"
  exit 1
fi

python3 - <<'PY' "${CURRENT_TURN_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    row["reason"] in {"current_turn_allowed_surface_set_mismatch", "direct_current_turn_legality_mismatch"}
    for row in payload["transition_violations"]
), payload
PY

SURFACE_REPO="${TMP_ROOT}/transition-surface-drift-repo"
mirror_repo "${SURFACE_REPO}"
python3 - <<'PY' "${SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root transition completeness discipline"
next_marker = "\n---\n\n## Root authority completeness discipline"
old = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
new = "2. expected row-family totals may be summarized informally once the surface still looks structurally green;"
assert section_marker in text, text
assert next_marker in text, text
before, rest = text.split(section_marker, 1)
section_body, after = rest.split(next_marker, 1)
assert old in section_body, section_body
section_body = section_body.replace(old, new, 1)
path.write_text(before + section_marker + section_body + next_marker + after, encoding="utf-8")
PY

SURFACE_JSON="${TMP_ROOT}/transition-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${SURFACE_REPO}" \
  --json-only >"${SURFACE_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed README transition completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "transition_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [
    "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
], payload
assert surface_row["unexpected_ids"] == [
    "expected row-family totals may be summarized informally once the surface still looks structurally green;"
], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "transition_completeness_surface" and row["reason"] == "missing_transition_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "transition_completeness_surface" and row["reason"] == "extra_transition_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert payload["transition_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

TRANSITION_SURFACE_ORDER_REPO="${TMP_ROOT}/transition-completeness-surface-order-drift-repo"
mirror_repo "${TRANSITION_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows_in_section \
  "${TRANSITION_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "${TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${TRANSITION_COMPLETENESS_SURFACE_FIRST_PHRASE}" \
  "${TRANSITION_COMPLETENESS_SURFACE_SECOND_PHRASE}"

TRANSITION_SURFACE_ORDER_JSON="${TMP_ROOT}/transition-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${TRANSITION_SURFACE_ORDER_REPO}" \
  --json-only >"${TRANSITION_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed README transition completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${TRANSITION_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert any(
    "transition_violation:transition_completeness_surface:transition_completeness_surface_phrase_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "transition_violation:transition_completeness_surface:transition_completeness_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "transition_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

TRANSITION_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/transition-completeness-surface-order-non-contiguous-repo"
mirror_repo "${TRANSITION_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${TRANSITION_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "${TRANSITION_COMPLETENESS_SURFACE_SECTION_MARKER}" \
  "${TRANSITION_COMPLETENESS_SURFACE_SECOND_ORDER}" \
  "${TRANSITION_COMPLETENESS_SURFACE_SECOND_PHRASE}" \
  "${TRANSITION_COMPLETENESS_SURFACE_FIRST_ORDER}"

TRANSITION_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/transition-completeness-surface-order-non-contiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${TRANSITION_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${TRANSITION_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed README transition completeness surface non-contiguous order drift"
  exit 1
fi

python3 - <<'PY' "${TRANSITION_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-002", payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["transition_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "transition_completeness_surface"
    and row["reason"] == "transition_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "transition_completeness_surface"
    and row["reason"] == "transition_completeness_surface_order_mismatch"
    for row in payload["transition_violations"]
), payload
assert not any(
    row["field"] == "transition_completeness_surface"
    and row["reason"] == "transition_completeness_surface_phrase_order_mismatch"
    for row in payload["transition_violations"]
), payload
assert any(
    reason == "structure_violation:transition_completeness_surface:transition_completeness_surface_order_non_contiguous"
    for reason in payload["stale_reasons"]
), payload
assert any(
    reason == "transition_violation:transition_completeness_surface:transition_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "transition_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

TRANSITION_BINDING_REPO="${TMP_ROOT}/transition-binding-drift-repo"
mirror_repo "${TRANSITION_BINDING_REPO}"
python3 - <<'PY' "${TRANSITION_BINDING_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "These transition-completeness rules must remain bound to canonical transition-completeness rows rather than drifting into soft summary prose."
new = "These transition completeness rules may be summarized freely once reviewers understand the intent."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

TRANSITION_BINDING_JSON="${TMP_ROOT}/transition-binding-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${TRANSITION_BINDING_REPO}" \
  --json-only >"${TRANSITION_BINDING_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed README transition binding drift"
  exit 1
fi

python3 - <<'PY' "${TRANSITION_BINDING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and "These transition-completeness rules must remain bound to canonical transition-completeness rows rather than drifting into soft summary prose." in row.get("marker", "")
    for row in payload["anchor_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root promotion-demotion discipline"
new = "## Root promotion demotion discipline"
assert old in text, text[:900]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_transition.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus transition validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_transition_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCT-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus transition probes passed"
