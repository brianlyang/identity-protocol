#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-authority-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/validate_protocol_root_corpus_authority.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 20, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_family_count"] == 6, payload
assert payload["authority_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["authority_completeness_row_count"] == 5, payload
assert payload["authority_completeness_surface"]["entry_count"] == 5, payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["root_index_entry"] == "identity/protocol/README.md", payload
assert any(row["corpus_class"] == "bottom_theory" and row["philosophical_primacy"] for row in payload["authority_class_profiles"]), payload
assert payload["authority_layer_stage_count"] == 3, payload
assert payload["authority_layer_stages"][0]["stage_label"] == "bottom-theory primacy", payload
assert payload["authority_layer_stages"][-1]["stage_label"] == "machine-consumed enforcement authority", payload
assert payload["authority_layer_stage_surface"]["entry_count"] == 3, payload
assert payload["authority_layer_stage_surface"]["entries"][0]["stage_label"] == "bottom-theory primacy", payload
assert payload["authority_layer_stage_surface"]["entries"][-1]["stage_label"] == "machine-consumed enforcement authority", payload
assert payload["authority_layer_stage_surface"]["extraction_violations"] == [], payload
assert {row["family_id"] for row in payload["row_family_projection_rows"]} == {
    "authority_class_profiles",
    "entry_authority_projection",
    "authority_layer_stages",
    "authority_layer_stage_surface",
    "authority_completeness_rows",
    "authority_completeness_surface",
}, payload
PY

MISSING_STAGE_REPO="${TMP_ROOT}/missing-authority-stage-repo"
mirror_repo "${MISSING_STAGE_REPO}"
python3 - <<'PY' "${MISSING_STAGE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["authority_layer_stages"] = [
    row for row in doc["authority_layer_stages"]
    if row.get("stage_label") != "machine-consumed enforcement authority"
]
for idx, row in enumerate(doc["authority_layer_stages"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_STAGE_JSON="${TMP_ROOT}/missing-authority-stage.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${MISSING_STAGE_REPO}" \
  --json-only >"${MISSING_STAGE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed missing authority-layer stage"
  exit 1
fi

python3 - <<'PY' "${MISSING_STAGE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert any(
    row["field"] == "authority_layer_stages" and row["reason"] == "missing_authority_layer_stages"
    for row in payload["structure_violations"]
), payload
stage_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_layer_stages"
)
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_layer_stage_surface"
)
assert stage_row["expected_count"] == 3, payload
assert stage_row["actual_count"] == 2, payload
assert stage_row["missing_ids"] == ["machine-consumed enforcement authority"], payload
assert stage_row["unexpected_ids"] == [], payload
assert stage_row["coverage_status"] == "FAIL_REQUIRED", payload
assert stage_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

MISSING_CLASS_REPO="${TMP_ROOT}/missing-class-repo"
mirror_repo "${MISSING_CLASS_REPO}"
python3 - <<'PY' "${MISSING_CLASS_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["authority_class_profiles"] = [
    row for row in doc["authority_class_profiles"]
    if row.get("corpus_class") != "demoted_support_directory"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_CLASS_JSON="${TMP_ROOT}/missing-class.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${MISSING_CLASS_REPO}" \
  --json-only >"${MISSING_CLASS_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed after removing authority class profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_CLASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["authority_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_authority_projection"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 7, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == [], payload
assert class_row["coverage_status"] == "FAIL_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

STAGE_ROLE_REPO="${TMP_ROOT}/stage-role-drift-repo"
mirror_repo "${STAGE_ROLE_REPO}"
python3 - <<'PY' "${STAGE_ROLE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["authority_layer_stages"]:
    if row.get("stage_label") == "bottom-theory primacy":
        row["bound_authority_roles"] = ["constitutional_protocol_law"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

STAGE_ROLE_JSON="${TMP_ROOT}/stage-role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${STAGE_ROLE_REPO}" \
  --json-only >"${STAGE_ROLE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority-layer role drift"
  exit 1
fi

python3 - <<'PY' "${STAGE_ROLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any(
    "authority_violation:authority_layer_stages:bound_authority_roles_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["authority_class_profiles"]:
    if row.get("corpus_class") == "demoted_support_directory":
        row["corpus_class"] = "demoted_support_directory_alias"
        break
else:
    raise SystemExit("expected demoted_support_directory row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority class identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["authority_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "missing_registry_classes" and "demoted_support_directory" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "authority_class_profiles" and row["reason"] == "extra_unregistered_classes" and "demoted_support_directory_alias" in row.get("corpus_classes", [])
    for row in payload["structure_violations"]
), payload
class_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_class_profiles"
)
entry_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "entry_authority_projection"
)
assert class_row["expected_count"] == 8, payload
assert class_row["actual_count"] == 8, payload
assert class_row["missing_ids"] == ["demoted_support_directory"], payload
assert class_row["unexpected_ids"] == ["demoted_support_directory_alias"], payload
assert class_row["coverage_status"] == "PASS_REQUIRED", payload
assert class_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert entry_row["coverage_status"] == "PASS_REQUIRED", payload
assert entry_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

PRIMACY_REPO="${TMP_ROOT}/primacy-drift-repo"
mirror_repo "${PRIMACY_REPO}"
python3 - <<'PY' "${PRIMACY_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["authority_class_profiles"]:
    if row.get("corpus_class") == "bottom_theory":
        row["philosophical_primacy"] = False
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PRIMACY_JSON="${TMP_ROOT}/primacy-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${PRIMACY_REPO}" \
  --json-only >"${PRIMACY_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed primacy drift"
  exit 1
fi

python3 - <<'PY' "${PRIMACY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any("authority_violation:authority_class_profiles:philosophical_primacy_mismatch" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_INDEX_REPO="${TMP_ROOT}/root-index-drift-repo"
mirror_repo "${ROOT_INDEX_REPO}"
python3 - <<'PY' "${ROOT_INDEX_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_authority_projection"][0]["authority_mode"] = "frozen_law_only"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_INDEX_JSON="${TMP_ROOT}/root-index-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT_INDEX_REPO}" \
  --json-only >"${ROOT_INDEX_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed root index authority-mode drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_INDEX_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any("authority_violation:entry_authority_projection:root_index_entry_wrong_mode" == reason for reason in payload["stale_reasons"]), payload
PY

ROOT_ROLE_REPO="${TMP_ROOT}/root-role-drift-repo"
mirror_repo "${ROOT_ROLE_REPO}"
python3 - <<'PY' "${ROOT_ROLE_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["entry_authority_projection"][0]["authority_role"] = "constitutional_protocol_law"
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROOT_ROLE_JSON="${TMP_ROOT}/root-role-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ROOT_ROLE_REPO}" \
  --json-only >"${ROOT_ROLE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed root index authority-role drift"
  exit 1
fi

python3 - <<'PY' "${ROOT_ROLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any(
    reason in payload["stale_reasons"]
    for reason in (
        "authority_violation:entry_authority_projection:entry_authority_role_mismatch",
        "authority_violation:entry_authority_projection:root_index_entry_wrong_role",
    )
), payload
PY

SURFACE_REPO="${TMP_ROOT}/authority-layer-surface-drift-repo"
mirror_repo "${SURFACE_REPO}"
python3 - <<'PY' "${SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "3. **machine-consumed enforcement authority**"
new = "3. **machine-consumed enforcing authority**"
assert old in text, text[:3000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

SURFACE_JSON="${TMP_ROOT}/authority-layer-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${SURFACE_REPO}" \
  --json-only >"${SURFACE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority-layer surface label drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert any(
    row["field"] == "authority_layer_stage_surface" and row["reason"] == "missing_authority_layer_surface_stages"
    for row in payload["structure_violations"]
), payload
assert any(
    "authority_violation:authority_layer_stage_surface:authority_layer_surface_label_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_layer_stage_surface"
)
assert surface_row["expected_count"] == 3, payload
assert surface_row["actual_count"] == 3, payload
assert surface_row["missing_ids"] == ["machine-consumed enforcement authority"], payload
assert surface_row["unexpected_ids"] == ["machine-consumed enforcing authority"], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Authority layering"
new = "## Authority topology layering"
assert old in text, text[:400]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["authority_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_layer_stage_surface" and row["reason"] == "authority_layer_surface_section_marker_missing"
    for row in payload["structure_violations"]
), payload
assert any("anchor_violation:identity/protocol/README.md:required_marker_missing" == reason for reason in payload["stale_reasons"]), payload
PY

MISSING_COMPLETENESS_REPO="${TMP_ROOT}/missing-authority-completeness-repo"
mirror_repo "${MISSING_COMPLETENESS_REPO}"
python3 - <<'PY' "${MISSING_COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-authority.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["authority_completeness_rows"] = [
    row for row in doc["authority_completeness_rows"]
    if row.get("completeness_id") != "fail_close_preserves_authority_identity_projection"
]
for idx, row in enumerate(doc["authority_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_COMPLETENESS_JSON="${TMP_ROOT}/missing-authority-completeness.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${MISSING_COMPLETENESS_REPO}" \
  --json-only >"${MISSING_COMPLETENESS_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed missing authority completeness row"
  exit 1
fi

python3 - <<'PY' "${MISSING_COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
assert payload["authority_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["authority_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_completeness_rows" and row["reason"] == "missing_authority_completeness_rows"
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["fail_close_preserves_authority_identity_projection"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/authority-completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = text.index("## Root authority completeness discipline")
end = text.index("## Root conflict-precedence completeness discipline")
section = text[start:end]
old = "5. fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure."
new = "5. fail-close machine output must preserve missing/unexpected authority identity projection rather than hiding drift behind row-count shorthand or generic structure failure."
assert old in section, section
section = section.replace(old, new, 1)
path.write_text(text[:start] + section + text[end:], encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/authority-completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-002", payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [
    "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure."
], payload
assert surface_row["unexpected_ids"] == [
    "fail-close machine output must preserve missing/unexpected authority identity projection rather than hiding drift behind row-count shorthand or generic structure failure."
], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "authority_completeness_surface" and row["reason"] == "missing_authority_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "authority_completeness_surface" and row["reason"] == "extra_authority_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/authority-completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
section_marker = "## Root authority completeness discipline"
next_heading = "## Root conflict-precedence completeness discipline"
first = "1. required authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface rows must remain explicit as separate machine-readable row families;"
second = "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
swapped_first = "1. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"
swapped_second = "2. required authority-class-profile, entry-authority-projection, authority-layer-stage, and authority-layer-stage-surface rows must remain explicit as separate machine-readable row families;"
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

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/authority-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root corpus authority validator unexpectedly passed authority completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCA-003", payload
assert any(
    "authority_violation:authority_completeness_surface:authority_completeness_surface_order_mismatch" == reason
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "authority_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

CASE_REPO="${TMP_ROOT}/case-normalization-repo"
mirror_repo "${CASE_REPO}"
python3 - <<'PY' "${CASE_REPO}/identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces such as:"
new = "current-turn prompt legality must still resolve from machine-consumed enforcement surfaces such as:"
assert old in text, text[:600]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

CASE_JSON="${TMP_ROOT}/case-normalization.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_authority.py" \
  --repo-root "${CASE_REPO}" \
  --json-only >"${CASE_JSON}"

python3 - <<'PY' "${CASE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_authority_status"] == "PASS_REQUIRED", payload
assert payload["error_code"] == "", payload
PY

echo "[PASS] protocol root-corpus authority probes passed"
