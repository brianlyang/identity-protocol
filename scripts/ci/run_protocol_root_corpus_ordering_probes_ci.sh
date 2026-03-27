#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-ordering-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

mirror_repo() {
  local dst="$1"
  mkdir -p "${dst}/scripts/ci"
  cp -R "${ROOT}/identity" "${dst}/"
  cp "${ROOT}/scripts/root_corpus_governance_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_ordering_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_precedence_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/root_corpus_question_routing_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/validate_protocol_root_corpus_ordering.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/registry_alias_control_plane_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/repo_root_resolution_common.py" "${dst}/scripts/"
  cp "${ROOT}/scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh" "${dst}/scripts/ci/"
}

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
assert payload["ordering_row_family_count"] == 4, payload
assert payload["ordering_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["ordering_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["reading_order"][0]["rel_path"] == "identity/protocol/README.md", payload
assert payload["source_order"][0]["corpus_class"] == "bottom_theory", payload
assert payload["adjudication_order"][0]["machine_surface"] == "mappings", payload
assert payload["adjudication_order"][-1]["machine_surface"] == "receipts", payload
assert payload["adjudication_surface_profile_count"] == 5, payload
assert payload["adjudication_surface_profiles"][0]["surface_role"] == "admissible_law_resolution", payload
assert payload["adjudication_surface_profiles"][-1]["closure_terminal"] is True, payload
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
assert adjudication_row["coverage_status"] == "PASS_REQUIRED", payload
assert adjudication_row["identity_projection_status"] == "PASS_REQUIRED", payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "PASS_REQUIRED", payload
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

echo "[PASS] protocol root-corpus ordering probes passed"
