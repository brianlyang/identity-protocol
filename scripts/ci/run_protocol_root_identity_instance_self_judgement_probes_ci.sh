#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-identity-instance-self-judgement-ci"
protocol_root_probe_define_full_mirror

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

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "PASS_REQUIRED", payload
assert payload["question_count"] == 4, payload
assert payload["anchor_count"] == 4, payload
assert payload["self_judgement_proof_count"] == 5, payload
assert payload["self_judgement_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["identity_instance_self_judgement_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_family_count"] == 7, payload
assert payload["self_judgement_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["identity_instance_self_judgement_completeness_surface"]["entry_count"] == 5, payload
assert payload["identity_instance_self_judgement_completeness_surface"]["extraction_violations"] == [], payload
assert any(
    row["family_id"] == "identity_instance_self_judgement_completeness_rows"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["family_id"] == "identity_instance_self_judgement_completeness_surface"
    for row in payload["row_family_projection_rows"]
), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["identity_instance_self_judgement_completeness_rows"] = [
    row for row in doc["identity_instance_self_judgement_completeness_rows"]
    if row.get("completeness_id") != "explicit_identity_instance_self_judgement_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_rows"
    and row["reason"] == "missing_identity_instance_self_judgement_completeness_rows"
    and "explicit_identity_instance_self_judgement_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_instance_self_judgement_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_identity_instance_self_judgement_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_ROW_ORDER_REPO="${TMP_ROOT}/identity-instance-self-judgement-completeness-row-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_ROW_ORDER_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
target_id = "congruent_identity_instance_self_judgement_row_family_totals"
for row in doc["identity_instance_self_judgement_completeness_rows"]:
    if row.get("completeness_id") == target_id:
        row["order"] = 6
        break
else:
    raise SystemExit("expected identity-instance self-judgement completeness row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_ORDER_JSON="${TMP_ROOT}/identity-instance-self-judgement-completeness-row-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${COMPLETENESS_ROW_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_ROW_ORDER_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed completeness row order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["identity_instance_self_judgement_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_rows"
    and row["reason"] == "identity_instance_self_judgement_completeness_row_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "identity_instance_self_judgement_completeness_row_order_mismatch"
    for row in payload["judgement_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_instance_self_judgement_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 5, payload
assert completeness_row["missing_ids"] == [], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "PASS_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

assert_stale_reason_present "${COMPLETENESS_ROW_ORDER_JSON}" "structure_violation:identity_instance_self_judgement_completeness_rows:identity_instance_self_judgement_completeness_row_order_non_contiguous"
assert_stale_reason_present "${COMPLETENESS_ROW_ORDER_JSON}" "self_judgement_violation:identity_instance_self_judgement_completeness_rows:identity_instance_self_judgement_completeness_row_order_mismatch"

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_self_judgement_proof_rows"] = [
    row for row in doc["required_self_judgement_proof_rows"] if row.get("proof_id") != "non_self_authorization_self_judgement_proof"
]
for idx, row in enumerate(doc["required_self_judgement_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "non_self_authorization_self_judgement_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_self_judgement_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["non_self_authorization_self_judgement_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

QUESTION_REPO="${TMP_ROOT}/question-drift-repo"
mirror_repo "${QUESTION_REPO}"
python3 - <<'PY' "${QUESTION_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_question_rows"] = [
    row for row in doc["required_question_rows"] if row.get("question_id") != "when_not_my_place"
]
for idx, row in enumerate(doc["required_question_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

QUESTION_JSON="${TMP_ROOT}/question-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${QUESTION_REPO}" \
  --json-only >"${QUESTION_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed missing question row"
  exit 1
fi

python3 - <<'PY' "${QUESTION_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "when_not_my_place" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 4, payload
assert question_row["actual_count"] == 3, payload
assert question_row["missing_ids"] == ["when_not_my_place"], payload
assert question_row["unexpected_ids"] == [], payload
assert question_row["coverage_status"] == "FAIL_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-identity-instance-self-judgement.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_question_rows"]:
    if row.get("question_id") == "when_not_my_place":
        row["question_id"] = "when_not_my_place_alias"
        break
else:
    raise SystemExit("expected when_not_my_place row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed question identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["self_judgement_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "when_not_my_place" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "when_not_my_place_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
question_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_question_rows"
)
assert question_row["expected_count"] == 4, payload
assert question_row["actual_count"] == 4, payload
assert question_row["missing_ids"] == ["when_not_my_place"], payload
assert question_row["unexpected_ids"] == ["when_not_my_place_alias"], payload
assert question_row["coverage_status"] == "PASS_REQUIRED", payload
assert question_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 3. How I do it"
new = "### 3. How I execute"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert any(
    row["reason"] == "question_heading_missing" and row["marker"] == "### 3. How I do it"
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
    if row.get("rel_path") != "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
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
old = "These identity-instance-self-judgement-completeness rules must remain bound to canonical identity-instance-self-judgement-completeness rows rather than drifting into soft summary prose."
new = "These identity-instance-self-judgement-completeness rules may drift into summary-only prose."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These identity-instance-self-judgement-completeness rules must remain bound to canonical identity-instance-self-judgement-completeness rows rather than drifting into soft summary prose."
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
    if row.get("rel_path") == "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
    for row in payload["integration_violations"]
), payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. runtime or validator code must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code may finalize identity-instance self-judgement legality from aggregate summaries alone;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_surface"
    and row["reason"] == "identity_instance_self_judgement_completeness_surface_phrase_order_mismatch"
    for row in payload["judgement_violations"]
), payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_surface"
    and row["reason"] == "missing_identity_instance_self_judgement_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_surface"
    and row["reason"] == "extra_identity_instance_self_judgement_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert payload["identity_instance_self_judgement_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_identity_projection_status"] == "FAIL_REQUIRED", payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_instance_self_judgement_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [
    "runtime or validator code must not finalize identity-instance self-judgement legality while missing or unexpected row identities remain known only internally;"
], payload
assert surface_row["unexpected_ids"] == [
    "runtime or validator code may finalize identity-instance self-judgement legality from aggregate summaries alone;"
], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

SURFACE_ORDER_REPO="${TMP_ROOT}/identity-instance-self-judgement-completeness-surface-order-drift-repo"
mirror_repo "${SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root identity-instance self-judgement completeness discipline" \
  "## Root law-bundle component-row completeness discipline" \
  "1. required question, anchor, self-judgement-proof, self-judgement-limit, and collapse rows must remain explicit as separate machine-readable families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

SURFACE_ORDER_JSON="${TMP_ROOT}/identity-instance-self-judgement-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${SURFACE_ORDER_REPO}" \
  --json-only >"${SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["self_judgement_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["self_judgement_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_surface"
    and row["reason"] == "identity_instance_self_judgement_completeness_surface_order_mismatch"
    for row in payload["judgement_violations"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "1. required question, anchor, self-judgement-proof, self-judgement-limit, and collapse rows must remain explicit as separate machine-readable families;"
    for row in payload["root_doc_anchor_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_instance_self_judgement_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO="${TMP_ROOT}/identity-instance-self-judgement-completeness-surface-order-noncontiguous-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}"
protocol_root_probe_set_numbered_surface_row_order_in_section \
  "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}/identity/protocol/README.md" \
  "## Root identity-instance self-judgement completeness discipline" \
  "2" \
  "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;" \
  "1"

COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON="${TMP_ROOT}/identity-instance-self-judgement-completeness-surface-order-noncontiguous.json"
if python3 "${ROOT}/scripts/validate_protocol_root_identity_instance_self_judgement.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"; then
  echo "[FAIL] root identity-instance self-judgement validator unexpectedly passed completeness surface order non-contiguous"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_identity_instance_self_judgement_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RIISJ-002", payload
assert payload["identity_instance_self_judgement_completeness_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_coverage_status"] == "PASS_REQUIRED", payload
assert payload["identity_instance_self_judgement_completeness_surface_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "identity_instance_self_judgement_completeness_surface"
    and row["reason"] == "identity_instance_self_judgement_completeness_surface_order_non_contiguous"
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "identity_instance_self_judgement_completeness_surface_order_mismatch"
    for row in payload["judgement_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "identity_instance_self_judgement_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

assert_stale_reason_present "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}" "structure_violation:identity_instance_self_judgement_completeness_surface:identity_instance_self_judgement_completeness_surface_order_non_contiguous"
assert_stale_reason_present "${COMPLETENESS_SURFACE_ORDER_NONCONTIG_JSON}" "self_judgement_violation:identity_instance_self_judgement_completeness_surface:identity_instance_self_judgement_completeness_surface_order_mismatch"

echo "[PASS] protocol root identity-instance self-judgement probes passed"
