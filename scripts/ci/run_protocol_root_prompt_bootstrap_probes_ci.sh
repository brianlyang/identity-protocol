#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/protocol-root-prompt-bootstrap-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

# shellcheck source=./probe_repo_mirror_common.sh
source "${SCRIPT_DIR}/probe_repo_mirror_common.sh"

mirror_repo() {
  local dst="$1"
  probe_mirror_repo "${ROOT}" "${dst}"
}

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "PASS_REQUIRED", payload
assert payload["anchor_count"] == 6, payload
assert payload["output_field_count"] == 6, payload
assert payload["binding_field_count"] == 5, payload
assert payload["prompt_bootstrap_proof_count"] == 5, payload
assert payload["prompt_bootstrap_limit_count"] == 5, payload
assert payload["native_literal_count"] == 9, payload
assert payload["prompt_bootstrap_row_family_count"] == 6, payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_prompt_bootstrap_proof_rows"] = [
    row for row in doc["required_prompt_bootstrap_proof_rows"] if row.get("proof_id") != "hard_guard_literal_preservation_proof"
]
for idx, row in enumerate(doc["required_prompt_bootstrap_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert payload["prompt_bootstrap_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "hard_guard_literal_preservation_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_prompt_bootstrap_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["hard_guard_literal_preservation_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/mappings/root-prompt-bootstrap.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_anchor_rows"]:
    if row.get("anchor_id") == "rq_033_native_chat_headstamp_prompt_contract_v1":
        row["anchor_id"] = "rq_033_native_chat_headstamp_prompt_contract_v1_alias"
        break
else:
    raise SystemExit("expected native-chat headstamp anchor row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed missing anchor row"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "rq_033_native_chat_headstamp_prompt_contract_v1" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "rq_033_native_chat_headstamp_prompt_contract_v1_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["prompt_bootstrap_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["prompt_bootstrap_row_identity_projection_status"] == "FAIL_REQUIRED", payload
anchor_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_anchor_rows"
)
assert anchor_row["expected_count"] == 6, payload
assert anchor_row["actual_count"] == 6, payload
assert anchor_row["missing_ids"] == ["rq_033_native_chat_headstamp_prompt_contract_v1"], payload
assert anchor_row["unexpected_ids"] == ["rq_033_native_chat_headstamp_prompt_contract_v1_alias"], payload
assert anchor_row["coverage_status"] == "PASS_REQUIRED", payload
assert anchor_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### Shared prompt current-run driver binding projection (v1.6.19 additive)"
new = "### Shared prompt driver binding projection (v1.6.19 additive)"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
assert any(
    row["reason"] == "anchor_heading_missing" and row["marker"] == "### Shared prompt current-run driver binding projection (v1.6.19 additive)"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
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
    if row.get("rel_path") == "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_prompt_bootstrap.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root prompt-bootstrap validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_prompt_bootstrap_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RPB-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

echo "[PASS] protocol root prompt-bootstrap probes passed"
