#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-machine-law-primacy-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "PASS_REQUIRED", payload
assert payload["commitment_count"] == 4, payload
assert payload["anchor_count"] == 4, payload
assert payload["primacy_proof_count"] == 5, payload
assert payload["primacy_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["machine_law_primacy_row_family_count"] == 5, payload
assert payload["machine_law_primacy_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_law_primacy_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-machine-law-primacy.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_primacy_proof_rows"] = [
    row for row in doc["required_primacy_proof_rows"] if row.get("proof_id") != "runtime_adjudication_non_bypass_primacy_proof"
]
for idx, row in enumerate(doc["required_primacy_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-002", payload
assert payload["machine_law_primacy_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_law_primacy_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "runtime_adjudication_non_bypass_primacy_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_primacy_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["runtime_adjudication_non_bypass_primacy_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

COMMITMENT_REPO="${TMP_ROOT}/commitment-drift-repo"
mirror_repo "${COMMITMENT_REPO}"
python3 - <<'PY' "${COMMITMENT_REPO}/identity/protocol/mappings/root-machine-law-primacy.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_commitment_rows"] = [
    row for row in doc["required_commitment_rows"] if row.get("commitment_id") != "governed_convergence_before_downgrade"
]
for idx, row in enumerate(doc["required_commitment_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMMITMENT_JSON="${TMP_ROOT}/commitment-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${COMMITMENT_REPO}" \
  --json-only >"${COMMITMENT_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed missing commitment row"
  exit 1
fi

python3 - <<'PY' "${COMMITMENT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-002", payload
assert payload["machine_law_primacy_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["machine_law_primacy_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "governed_convergence_before_downgrade" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
commitment_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_commitment_rows"
)
assert commitment_row["expected_count"] == 4, payload
assert commitment_row["actual_count"] == 3, payload
assert commitment_row["missing_ids"] == ["governed_convergence_before_downgrade"], payload
assert commitment_row["unexpected_ids"] == [], payload
assert commitment_row["coverage_status"] == "FAIL_REQUIRED", payload
assert commitment_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-machine-law-primacy.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_commitment_rows"]:
    if row.get("commitment_id") == "governed_convergence_before_downgrade":
        row["commitment_id"] = "governed_convergence_before_downgrade_alias"
        break
else:
    raise SystemExit("expected governed_convergence_before_downgrade row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed commitment identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-002", payload
assert payload["machine_law_primacy_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["machine_law_primacy_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "governed_convergence_before_downgrade" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "governed_convergence_before_downgrade_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
commitment_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_commitment_rows"
)
assert commitment_row["expected_count"] == 4, payload
assert commitment_row["actual_count"] == 4, payload
assert commitment_row["missing_ids"] == ["governed_convergence_before_downgrade"], payload
assert commitment_row["unexpected_ids"] == ["governed_convergence_before_downgrade_alias"], payload
assert commitment_row["coverage_status"] == "PASS_REQUIRED", payload
assert commitment_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 3. Fail-close exposure before silent swallowing"
new = "### 3. Fail-open continuity before silent swallowing"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-003", payload
assert any(
    row["reason"] == "commitment_heading_missing" and row["marker"] == "### 3. Fail-close exposure before silent swallowing"
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
    if row.get("rel_path") != "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-003", payload
assert any(
    row["field"] == "root_corpus_registry" and row["reason"] == "contract_not_registered"
    for row in payload["integration_violations"]
), payload
PY

DOC_ANCHOR_REPO="${TMP_ROOT}/doc-anchor-drift-repo"
mirror_repo "${DOC_ANCHOR_REPO}"
python3 - <<'PY' "${DOC_ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root machine-law primacy completeness discipline"
new = "## Root machine-law primacy discipline"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "## Root machine-law primacy completeness discipline"
    for row in payload["root_doc_anchor_violations"]
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
    if row.get("rel_path") == "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_machine_law_primacy.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root machine-law primacy validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_machine_law_primacy_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RMLP-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root machine-law primacy probes passed"
