#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-ordering-ci"
export PROBE_FIXTURE_REPO_ROOT="${ROOT}"
source "${ROOT}/scripts/probe_fixture_shell_common.sh"

PROBE_REL_PATHS=(
  "scripts/root_corpus_contract_list_sync_common.py"
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_precedence_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/validate_protocol_root_corpus_ordering.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"

protocol_boundary_probe_target_rel_path="$(
  resolve_python_module_expression \
    "root_corpus_contract_list_sync_common" \
    "current_protocol_boundary_root_contract_projection_probe_target()['rel_path']"
)"
protocol_boundary_probe_target_sentence="$(
  resolve_python_module_expression \
    "root_corpus_contract_list_sync_common" \
    "current_protocol_boundary_root_contract_projection_probe_target()['sentence']"
)"
protocol_boundary_probe_target_drifted_sentence="$(
  resolve_python_module_expression \
    "root_corpus_contract_list_sync_common" \
    "current_protocol_boundary_root_contract_projection_probe_target()['drifted_sentence']"
)"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["ordering_row_family_count"] == 14, payload
assert payload["ordering_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["reading_order"][0]["rel_path"] == "identity/protocol/README.md", payload
assert payload["root_reading_order_stage_count"] == 7, payload
assert payload["root_reading_order_stages"][0]["stage_label"] == "`IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`", payload
assert payload["root_reading_order_stages"][-1]["stage_label"] == "non-runtime or support material", payload
assert payload["root_reading_order_stage_surface"]["entry_count"] == 7, payload
assert payload["root_reading_order_stage_surface"]["entries"][0]["stage_label"] == "`IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`", payload
assert payload["root_reading_order_stage_surface"]["entries"][-1]["stage_label"] == "non-runtime or support material", payload
assert payload["root_reading_order_stage_surface"]["extraction_violations"] == [], payload
assert payload["order_plane_stage_count"] == 3, payload
assert payload["order_plane_stages"][0]["stage_label"] == "source-order / generative-order", payload
assert payload["order_plane_stages"][-1]["stage_label"] == "adjudication-order", payload
assert payload["order_plane_stage_surface"]["entry_count"] == 3, payload
assert payload["order_plane_stage_surface"]["entries"][0]["stage_label"] == "source-order / generative-order", payload
assert payload["order_plane_stage_surface"]["entries"][-1]["stage_label"] == "adjudication-order", payload
assert payload["order_plane_stage_surface"]["extraction_violations"] == [], payload
assert payload["ordering_completeness_row_count"] == 5, payload
assert payload["ordering_completeness_rows"][0]["completeness_id"] == "explicit_ordering_row_families", payload
assert payload["ordering_completeness_rows"][-1]["completeness_id"] == "fail_close_preserves_ordering_identity_projection", payload
assert payload["ordering_completeness_surface"]["entry_count"] == 5, payload
assert payload["ordering_completeness_surface"]["entries"][0]["contract_phrase"].startswith("required source-order, reading-order"), payload
assert payload["ordering_completeness_surface"]["entries"][-1]["contract_phrase"].startswith("fail-close machine output must preserve"), payload
assert payload["ordering_completeness_surface"]["extraction_violations"] == [], payload
assert payload["ordering_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload

assert payload["source_order"][0]["corpus_class"] == "bottom_theory", payload
assert payload["canonical_root_contract_entry_count"] == 16, payload
assert payload["canonical_root_contract_entry_paths"][0] == "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md", payload
assert payload["canonical_root_contract_entry_paths"][-1] == "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md", payload
assert len(payload["manual_root_contract_index_surfaces"]) == 2, payload
assert all(surface["entry_count"] == payload["canonical_root_contract_entry_count"] for surface in payload["manual_root_contract_index_surfaces"]), payload
assert all(surface["extraction_violations"] == [] for surface in payload["manual_root_contract_index_surfaces"]), payload
assert len(payload["protocol_boundary_root_contract_projections"]) == payload["canonical_root_contract_entry_count"], payload
assert payload["protocol_boundary_root_contract_projection_surface"]["entry_count"] == payload["canonical_root_contract_entry_count"], payload
assert payload["protocol_boundary_root_contract_projection_surface"]["extraction_violations"] == [], payload
assert {row["family_id"] for row in payload["row_family_projection_rows"]} == {
    "source_order",
    "reading_order",
    "root_reading_order_stages",
    "root_reading_order_stage_surface",
    "order_plane_stages",
    "order_plane_stage_surface",
    "ordering_completeness_rows",
    "ordering_completeness_surface",
    "readme_root_contract_index",
    "protocol_boundary_root_contract_index",
    "protocol_boundary_root_contract_projections",
    "protocol_boundary_root_contract_projection_surface",
    "adjudication_order",
    "adjudication_surface_profiles",
}, payload
assert payload["adjudication_order"][0]["machine_surface"] == "mappings", payload
assert payload["adjudication_order"][-1]["machine_surface"] == "receipts", payload
assert payload["adjudication_surface_profile_count"] == 5, payload
assert payload["adjudication_surface_profiles"][0]["surface_role"] == "admissible_law_resolution", payload
assert payload["adjudication_surface_profiles"][-1]["closure_terminal"] is True, payload
PY

ORDERING_COMPLETENESS_REPO="${TMP_ROOT}/missing-ordering-completeness-row-repo"
mirror_repo "${ORDERING_COMPLETENESS_REPO}"
python3 - <<'PY' "${ORDERING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["ordering_completeness_rows"] = [
    row for row in doc["ordering_completeness_rows"]
    if row.get("completeness_id") != "hidden_ordering_identity_drift_forbidden"
]
for idx, row in enumerate(doc["ordering_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ORDERING_COMPLETENESS_JSON="${TMP_ROOT}/missing-ordering-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ORDERING_COMPLETENESS_REPO}" \
  --json-only >"${ORDERING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed missing ordering-completeness row"
  exit 1
fi

python3 - <<'PY' "${ORDERING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:ordering_completeness_rows:missing_ordering_completeness_rows" == reason
    for reason in payload["stale_reasons"]
), payload
row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "ordering_completeness_rows"
)
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "ordering_completeness_surface"
)
assert row["expected_count"] == 5, payload
assert row["actual_count"] == 4, payload
assert row["missing_ids"] == ["hidden_ordering_identity_drift_forbidden"], payload
assert row["unexpected_ids"] == [], payload
assert row["coverage_status"] == "FAIL_REQUIRED", payload
assert row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["ordering_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["ordering_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

ORDERING_COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/ordering-completeness-surface-drift-repo"
mirror_repo "${ORDERING_COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${ORDERING_COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required source-order, reading-order, root-reading-order-stage, root-reading-order-stage-surface, order-plane-stage, order-plane-stage-surface, explanatory root-contract index/projection, adjudication-order, and adjudication-surface-profile rows must remain explicit as separate machine-readable row families;"
new = "1. required source-order, reading-order, root-reading-order-stage, root-reading-order-stage-surface, order-plane-stage, order-plane-stage-surface, manual root-contract index/projection, adjudication-order, and adjudication-surface-profile rows must remain explicit as separate machine-readable row families;"
assert old in text, text[:3000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ORDERING_COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/ordering-completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ORDERING_COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${ORDERING_COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed ordering-completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${ORDERING_COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:ordering_completeness_surface:missing_ordering_completeness_surface_rows" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "structure_violation:ordering_completeness_surface:extra_ordering_completeness_surface_rows" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "ordering_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["missing_ids"] == [
    "required source-order, reading-order, root-reading-order-stage, root-reading-order-stage-surface, order-plane-stage, order-plane-stage-surface, explanatory root-contract index/projection, adjudication-order, and adjudication-surface-profile rows must remain explicit as separate machine-readable row families;"
], payload
assert surface_row["unexpected_ids"] == [
    "required source-order, reading-order, root-reading-order-stage, root-reading-order-stage-surface, order-plane-stage, order-plane-stage-surface, manual root-contract index/projection, adjudication-order, and adjudication-surface-profile rows must remain explicit as separate machine-readable row families;"
], payload
assert payload["ordering_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ORDERING_COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/ordering-completeness-surface-order-drift-repo"
mirror_repo "${ORDERING_COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${ORDERING_COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root ordering completeness discipline" \
  "## Root question-routing completeness discipline" \
  "1. required source-order, reading-order, root-reading-order-stage, root-reading-order-stage-surface, order-plane-stage, order-plane-stage-surface, explanatory root-contract index/projection, adjudication-order, and adjudication-surface-profile rows must remain explicit as separate machine-readable row families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

ORDERING_COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/ordering-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ORDERING_COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${ORDERING_COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed ordering-completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${ORDERING_COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any(
    row["field"] == "ordering_completeness_surface"
    and row["reason"] == "order_mismatch"
    and row["expected"] == 1
    and row["actual"] == 2
    for row in payload["coverage_violations"]
), payload
assert any(
    row["field"] == "ordering_completeness_surface"
    and row["reason"] == "order_mismatch"
    and row["expected"] == 2
    and row["actual"] == 1
    for row in payload["coverage_violations"]
), payload
assert any(
    "coverage_violation:ordering_completeness_surface:order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "ordering_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

ORDER_PLANE_REPO="${TMP_ROOT}/missing-order-plane-stage-repo"
mirror_repo "${ORDER_PLANE_REPO}"
python3 - <<'PY' "${ORDER_PLANE_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["order_plane_stages"] = [
    row for row in doc["order_plane_stages"]
    if row.get("stage_label") != "adjudication-order"
]
for idx, row in enumerate(doc["order_plane_stages"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ORDER_PLANE_JSON="${TMP_ROOT}/missing-order-plane-stage.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ORDER_PLANE_REPO}" \
  --json-only >"${ORDER_PLANE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed missing order-plane stage"
  exit 1
fi

python3 - <<'PY' "${ORDER_PLANE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:order_plane_stages:missing_order_plane_stages" == reason
    for reason in payload["stale_reasons"]
), payload
stage_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "order_plane_stages"
)
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "order_plane_stage_surface"
)
assert stage_row["expected_count"] == 3, payload
assert stage_row["actual_count"] == 2, payload
assert stage_row["missing_ids"] == ["adjudication-order"], payload
assert stage_row["unexpected_ids"] == [], payload
assert stage_row["coverage_status"] == "FAIL_REQUIRED", payload
assert stage_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

STAGE_REPO="${TMP_ROOT}/missing-root-reading-stage-repo"
mirror_repo "${STAGE_REPO}"
python3 - <<'PY' "${STAGE_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["root_reading_order_stages"] = [
    row for row in doc["root_reading_order_stages"]
    if row.get("stage_label") != "specialized subdomain protocol packs"
]
for idx, row in enumerate(doc["root_reading_order_stages"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STAGE_JSON="${TMP_ROOT}/missing-root-reading-stage.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${STAGE_REPO}" \
  --json-only >"${STAGE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed missing root reading-order stage"
  exit 1
fi

python3 - <<'PY' "${STAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:root_reading_order_stages:missing_root_reading_order_stages" == reason
    for reason in payload["stale_reasons"]
), payload
stage_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_reading_order_stages"
)
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_reading_order_stage_surface"
)
assert stage_row["expected_count"] == 7, payload
assert stage_row["actual_count"] == 6, payload
assert stage_row["missing_ids"] == ["specialized subdomain protocol packs"], payload
assert stage_row["unexpected_ids"] == [], payload
assert stage_row["coverage_status"] == "FAIL_REQUIRED", payload
assert stage_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

ORDER_PLANE_SURFACE_REPO="${TMP_ROOT}/order-plane-surface-drift-repo"
mirror_repo "${ORDER_PLANE_SURFACE_REPO}"
python3 - <<'PY' "${ORDER_PLANE_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "3. **adjudication-order**"
new = "3. **adjudication sequencing**"
assert old in text, text[:4000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ORDER_PLANE_SURFACE_JSON="${TMP_ROOT}/order-plane-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ORDER_PLANE_SURFACE_REPO}" \
  --json-only >"${ORDER_PLANE_SURFACE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed order-plane surface label drift"
  exit 1
fi

python3 - <<'PY' "${ORDER_PLANE_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:order_plane_stage_surface:missing_order_plane_surface_stages" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "structure_violation:order_plane_stage_surface:extra_order_plane_surface_stages" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "coverage_violation:order_plane_stage_surface:order_plane_surface_label_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "order_plane_stage_surface"
)
assert surface_row["expected_count"] == 3, payload
assert surface_row["actual_count"] == 3, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["missing_ids"] == ["adjudication-order"], payload
assert surface_row["unexpected_ids"] == ["adjudication sequencing"], payload
PY

DUP_REPO="${TMP_ROOT}/duplicate-source-order-repo"
mirror_repo "${DUP_REPO}"
python3 - <<'PY' "${DUP_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["source_order"][1]["order"] = 1
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

DUP_JSON="${TMP_ROOT}/duplicate-source-order.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${DUP_REPO}" \
  --json-only >"${DUP_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed duplicate source-order ranks"
  exit 1
fi

python3 - <<'PY' "${DUP_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any("structure_violation:source_order:source_order_non_contiguous" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_INDEX_REPO="${TMP_ROOT}/root-index-order-repo"
mirror_repo "${ROOT_INDEX_REPO}"
python3 - <<'PY' "${ROOT_INDEX_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["reading_order"][0]["rel_path"] = "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_INDEX_JSON="${TMP_ROOT}/root-index-order.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ROOT_INDEX_REPO}" \
  --json-only >"${ROOT_INDEX_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed when root index was not first"
  exit 1
fi

python3 - <<'PY' "${ROOT_INDEX_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any("structure_violation:reading_order:root_index_entry_not_first" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_STAGE_SURFACE_REPO="${TMP_ROOT}/root-reading-order-surface-drift-repo"
mirror_repo "${ROOT_STAGE_SURFACE_REPO}"
python3 - <<'PY' "${ROOT_STAGE_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "5. **machine-consumed registries and mappings**"
new = "5. **machine-consumed registry and mappings**"
assert old in text, text[:2000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ROOT_STAGE_SURFACE_JSON="${TMP_ROOT}/root-reading-order-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ROOT_STAGE_SURFACE_REPO}" \
  --json-only >"${ROOT_STAGE_SURFACE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed root reading-order surface label drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_STAGE_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-002", payload
assert any(
    "structure_violation:root_reading_order_stage_surface:missing_root_reading_order_surface_stages" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "structure_violation:root_reading_order_stage_surface:extra_root_reading_order_surface_stages" == reason
    for reason in payload["stale_reasons"]
), payload
assert any(
    "coverage_violation:root_reading_order_stage_surface:root_reading_order_surface_label_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "root_reading_order_stage_surface"
)
assert surface_row["expected_count"] == 7, payload
assert surface_row["actual_count"] == 7, payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["missing_ids"] == ["machine-consumed registries and mappings"], payload
assert surface_row["unexpected_ids"] == ["machine-consumed registry and mappings"], payload
PY

CLASS_REPO="${TMP_ROOT}/missing-source-class-repo"
mirror_repo "${CLASS_REPO}"
python3 - <<'PY' "${CLASS_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["source_order"] = [row for row in doc["source_order"] if row.get("corpus_class") != "root_contract"]
for idx, row in enumerate(doc["source_order"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

CLASS_JSON="${TMP_ROOT}/missing-source-class.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${CLASS_REPO}" \
  --json-only >"${CLASS_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed with missing source class"
  exit 1
fi

python3 - <<'PY' "${CLASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert payload["ordering_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["ordering_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any("coverage_violation:source_order:missing_source_classes" == reason for reason in payload["stale_reasons"]), payload
source_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "source_order"
)
reading_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "reading_order"
)
readme_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "readme_root_contract_index"
)
protocol_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_index"
)
protocol_projection_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_projections"
)
protocol_projection_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_projection_surface"
)
adjudication_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "adjudication_order"
)
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "adjudication_surface_profiles"
)
assert source_row["expected_count"] == 7, payload
assert source_row["actual_count"] == 6, payload
assert source_row["missing_ids"] == ["root_contract"], payload
assert source_row["unexpected_ids"] == [], payload
assert source_row["coverage_status"] == "FAIL_REQUIRED", payload
assert source_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert reading_row["coverage_status"] == "PASS_REQUIRED", payload
assert reading_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert readme_row["coverage_status"] == "PASS_REQUIRED", payload
assert readme_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_projection_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_projection_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_projection_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_projection_surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert adjudication_row["coverage_status"] == "PASS_REQUIRED", payload
assert adjudication_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["source_order"]:
    if row.get("corpus_class") == "root_contract":
        row["corpus_class"] = "root_contract_alias"
        break
else:
    raise SystemExit("expected root_contract row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed source-order identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert payload["ordering_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any("coverage_violation:source_order:missing_source_classes" == reason for reason in payload["stale_reasons"]), payload
assert any("coverage_violation:source_order:extra_source_classes" == reason for reason in payload["stale_reasons"]), payload
source_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "source_order"
)
reading_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "reading_order"
)
readme_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "readme_root_contract_index"
)
protocol_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_index"
)
protocol_projection_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_projections"
)
protocol_projection_surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_projection_surface"
)
adjudication_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "adjudication_order"
)
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "adjudication_surface_profiles"
)
assert source_row["expected_count"] == 7, payload
assert source_row["actual_count"] == 7, payload
assert source_row["missing_ids"] == ["root_contract"], payload
assert source_row["unexpected_ids"] == ["root_contract_alias"], payload
assert source_row["coverage_status"] == "PASS_REQUIRED", payload
assert source_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert reading_row["coverage_status"] == "PASS_REQUIRED", payload
assert reading_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert readme_row["coverage_status"] == "PASS_REQUIRED", payload
assert readme_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_projection_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_projection_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert protocol_projection_surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert protocol_projection_surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert adjudication_row["coverage_status"] == "PASS_REQUIRED", payload
assert adjudication_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

README_MANUAL_REPO="${TMP_ROOT}/readme-manual-index-drift-repo"
mirror_repo "${README_MANUAL_REPO}"
python3 - <<'PY' "${README_MANUAL_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "   - `MACHINE_LAW_PRIMACY_CONTRACT.md`\n   - `MACHINE_WORLD_ONTOLOGY_CONTRACT.md`"
new = "   - `MACHINE_WORLD_ONTOLOGY_CONTRACT.md`\n   - `MACHINE_LAW_PRIMACY_CONTRACT.md`"
assert old in text, text[:2000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

README_MANUAL_JSON="${TMP_ROOT}/readme-manual-index-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${README_MANUAL_REPO}" \
  --json-only >"${README_MANUAL_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed README manual root-contract order drift"
  exit 1
fi

python3 - <<'PY' "${README_MANUAL_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any(
    "coverage_violation:readme_root_contract_index:manual_root_contract_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
readme_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "readme_root_contract_index"
)
assert readme_row["coverage_status"] == "PASS_REQUIRED", payload
assert readme_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

PROTOCOL_MANUAL_REPO="${TMP_ROOT}/protocol-manual-index-drift-repo"
mirror_repo "${PROTOCOL_MANUAL_REPO}"
mutate_probe_literal \
  "${PROTOCOL_MANUAL_REPO}/identity/protocol/IDENTITY_PROTOCOL.md" \
  "${protocol_boundary_probe_target_sentence}"

PROTOCOL_MANUAL_JSON="${TMP_ROOT}/protocol-manual-index-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${PROTOCOL_MANUAL_REPO}" \
  --json-only >"${PROTOCOL_MANUAL_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed protocol manual root-contract list drift"
  exit 1
fi

python3 - <<'PY' "${PROTOCOL_MANUAL_JSON}" "${protocol_boundary_probe_target_rel_path}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any(
    "coverage_violation:protocol_boundary_root_contract_index:missing_manual_root_contract_entries" == reason
    for reason in payload["stale_reasons"]
), payload
protocol_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_index"
)
assert protocol_row["expected_count"] == 16, payload
assert protocol_row["actual_count"] == 15, payload
assert protocol_row["missing_ids"] == [sys.argv[2]], payload
assert protocol_row["unexpected_ids"] == [], payload
assert protocol_row["coverage_status"] == "FAIL_REQUIRED", payload
assert protocol_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROTOCOL_LABEL_REPO="${TMP_ROOT}/protocol-boundary-label-drift-repo"
mirror_repo "${PROTOCOL_LABEL_REPO}"
mutate_probe_literal \
  "${PROTOCOL_LABEL_REPO}/identity/protocol/IDENTITY_PROTOCOL.md" \
  "${protocol_boundary_probe_target_sentence}" \
  "${protocol_boundary_probe_target_drifted_sentence}"

PROTOCOL_LABEL_JSON="${TMP_ROOT}/protocol-boundary-label-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${PROTOCOL_LABEL_REPO}" \
  --json-only >"${PROTOCOL_LABEL_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed protocol boundary projection label drift"
  exit 1
fi

python3 - <<'PY' "${PROTOCOL_LABEL_JSON}" "${protocol_boundary_probe_target_rel_path}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any(
    "coverage_violation:protocol_boundary_root_contract_projection_surface:manual_root_contract_projection_label_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "protocol_boundary_root_contract_projection_surface"
)
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "protocol_boundary_root_contract_projection_surface"
    and row["reason"] == "manual_root_contract_projection_label_mismatch"
    and row["rel_path"] == sys.argv[2]
    for row in payload["coverage_violations"]
), payload
PY

ADJUDICATION_REPO="${TMP_ROOT}/adjudication-order-drift-repo"
mirror_repo "${ADJUDICATION_REPO}"
python3 - <<'PY' "${ADJUDICATION_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["adjudication_order"][0]["machine_surface"] = "governance_docs"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ADJUDICATION_JSON="${TMP_ROOT}/adjudication-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ADJUDICATION_REPO}" \
  --json-only >"${ADJUDICATION_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed adjudication-order drift"
  exit 1
fi

python3 - <<'PY' "${ADJUDICATION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any("coverage_violation:adjudication_order:terminal_machine_surfaces_mismatch" == reason for reason in payload["stale_reasons"]), payload
PY

SURFACE_ROLE_REPO="${TMP_ROOT}/surface-role-drift-repo"
mirror_repo "${SURFACE_ROLE_REPO}"
python3 - <<'PY' "${SURFACE_ROLE_REPO}/identity/protocol/mappings/root-corpus-ordering.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["adjudication_surface_profiles"]:
    if row.get("machine_surface") == "runtime_state":
        row["surface_role"] = "machine_registry_answer"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

SURFACE_ROLE_JSON="${TMP_ROOT}/surface-role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${SURFACE_ROLE_REPO}" \
  --json-only >"${SURFACE_ROLE_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed adjudication surface-role drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_ROLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert any("coverage_violation:adjudication_surface_profiles:surface_role_mismatch" == reason for reason in payload["stale_reasons"]), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root adjudication-surface discipline"
new = "## Root adjudication surface discipline"
assert old in text, text[:1500]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus ordering validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_ordering_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCO-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "missing_required_markers"
    and "## Root adjudication-surface discipline" in row.get("missing_markers", [])
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus ordering probes passed"
