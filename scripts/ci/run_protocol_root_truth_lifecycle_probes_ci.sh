#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-truth-lifecycle-ci"
protocol_root_probe_define_full_mirror

PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "PASS_REQUIRED", payload
assert payload["lifecycle_count"] == 5, payload
assert payload["memory_strata_count"] == 5, payload
assert payload["differentiation_count"] == 5, payload
assert payload["truth_lifecycle_proof_count"] == 5, payload
assert payload["truth_lifecycle_limit_count"] == 5, payload
assert payload["collapse_count"] == 5, payload
assert payload["truth_lifecycle_completeness_row_count"] == 5, payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["truth_lifecycle_row_family_count"] == 8, payload
assert payload["truth_lifecycle_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["truth_lifecycle_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert payload["truth_lifecycle_completeness_surface"]["entry_count"] == 5, payload
assert payload["truth_lifecycle_completeness_surface"]["extraction_violations"] == [], payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert any(
    row["family_id"] == "truth_lifecycle_completeness_rows"
    for row in payload["row_family_projection_rows"]
), payload
assert any(
    row["family_id"] == "truth_lifecycle_completeness_surface"
    for row in payload["row_family_projection_rows"]
), payload
PY

COMPLETENESS_ROW_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_ROW_REPO}"
python3 - <<'PY' "${COMPLETENESS_ROW_REPO}/identity/protocol/mappings/root-truth-lifecycle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["truth_lifecycle_completeness_rows"] = [
    row for row in doc["truth_lifecycle_completeness_rows"]
    if row.get("completeness_id") != "explicit_truth_lifecycle_row_families"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_ROW_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${COMPLETENESS_ROW_REPO}" \
  --json-only >"${COMPLETENESS_ROW_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed missing completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_ROW_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert any(
    row["field"] == "truth_lifecycle_completeness_rows"
    and row["reason"] == "missing_truth_lifecycle_completeness_rows"
    and "explicit_truth_lifecycle_row_families" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
completeness_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "truth_lifecycle_completeness_rows"
)
assert completeness_row["expected_count"] == 5, payload
assert completeness_row["actual_count"] == 4, payload
assert completeness_row["missing_ids"] == ["explicit_truth_lifecycle_row_families"], payload
assert completeness_row["unexpected_ids"] == [], payload
assert completeness_row["coverage_status"] == "FAIL_REQUIRED", payload
assert completeness_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

PROOF_REPO="${TMP_ROOT}/proof-drift-repo"
mirror_repo "${PROOF_REPO}"
python3 - <<'PY' "${PROOF_REPO}/identity/protocol/mappings/root-truth-lifecycle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["required_truth_lifecycle_proof_rows"] = [
    row for row in doc["required_truth_lifecycle_proof_rows"] if row.get("proof_id") != "next_hop_consumption_proof"
]
for idx, row in enumerate(doc["required_truth_lifecycle_proof_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

PROOF_JSON="${TMP_ROOT}/proof-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${PROOF_REPO}" \
  --json-only >"${PROOF_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed missing proof row"
  exit 1
fi

python3 - <<'PY' "${PROOF_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert payload["truth_lifecycle_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["truth_lifecycle_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["reason"] == "missing_expected_rows" and "next_hop_consumption_proof" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
proof_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_truth_lifecycle_proof_rows"
)
assert proof_row["expected_count"] == 5, payload
assert proof_row["actual_count"] == 4, payload
assert proof_row["missing_ids"] == ["next_hop_consumption_proof"], payload
assert proof_row["unexpected_ids"] == [], payload
assert proof_row["coverage_status"] == "FAIL_REQUIRED", payload
assert proof_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

LIFECYCLE_REPO="${TMP_ROOT}/lifecycle-drift-repo"
mirror_repo "${LIFECYCLE_REPO}"
python3 - <<'PY' "${LIFECYCLE_REPO}/identity/protocol/mappings/root-truth-lifecycle.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["required_lifecycle_rows"]:
    if row.get("lifecycle_id") == "truth_bound":
        row["lifecycle_id"] = "truth_bound_alias"
        break
else:
    raise SystemExit("expected truth_bound row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

LIFECYCLE_JSON="${TMP_ROOT}/lifecycle-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${LIFECYCLE_REPO}" \
  --json-only >"${LIFECYCLE_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed lifecycle identity drift"
  exit 1
fi

python3 - <<'PY' "${LIFECYCLE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert any(
    row["reason"] == "missing_expected_rows" and "truth_bound" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["reason"] == "extra_rows" and "truth_bound_alias" in row.get("row_ids", [])
    for row in payload["structure_violations"]
), payload
assert payload["truth_lifecycle_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["truth_lifecycle_row_identity_projection_status"] == "FAIL_REQUIRED", payload
lifecycle_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "required_lifecycle_rows"
)
assert lifecycle_row["expected_count"] == 5, payload
assert lifecycle_row["actual_count"] == 5, payload
assert lifecycle_row["missing_ids"] == ["truth_bound"], payload
assert lifecycle_row["unexpected_ids"] == ["truth_bound_alias"], payload
assert lifecycle_row["coverage_status"] == "PASS_REQUIRED", payload
assert lifecycle_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

HEADING_REPO="${TMP_ROOT}/heading-drift-repo"
mirror_repo "${HEADING_REPO}"
python3 - <<'PY' "${HEADING_REPO}/identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "### 4. Truth is bound to current run / current thread"
new = "### 4. Truth is bound to current run"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

HEADING_JSON="${TMP_ROOT}/heading-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${HEADING_REPO}" \
  --json-only >"${HEADING_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed heading drift"
  exit 1
fi

python3 - <<'PY' "${HEADING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert any(
    row["reason"] == "lifecycle_heading_missing" and row["marker"] == "### 4. Truth is bound to current run / current thread"
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
    if row.get("rel_path") != "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

REGISTRY_JSON="${TMP_ROOT}/registry-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${REGISTRY_REPO}" \
  --json-only >"${REGISTRY_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed registry drift"
  exit 1
fi

python3 - <<'PY' "${REGISTRY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
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
    if row.get("rel_path") == "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md":
        row["question_classes"] = ["registry_resolution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

ROUTING_JSON="${TMP_ROOT}/routing-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${ROUTING_REPO}" \
  --json-only >"${ROUTING_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed routing drift"
  exit 1
fi

python3 - <<'PY' "${ROUTING_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert any(
    row["field"] == "root_corpus_question_routing" and row["reason"] == "routing_projection_question_classes_mismatch"
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
old = "These truth-lifecycle-completeness rules must remain bound to canonical truth-lifecycle-completeness rows rather than drifting into soft summary prose."
new = "These truth-lifecycle rules must remain bound to canonical truth rows rather than drifting into soft summary prose."
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

DOC_ANCHOR_JSON="${TMP_ROOT}/doc-anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${DOC_ANCHOR_REPO}" \
  --json-only >"${DOC_ANCHOR_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed root-doc anchor drift"
  exit 1
fi

python3 - <<'PY' "${DOC_ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    reason.startswith("root_doc_anchor_violation:")
    for reason in payload["stale_reasons"]
), payload
assert any(
    row["rel_path"] == "identity/protocol/README.md"
    and row["reason"] == "required_marker_missing"
    and row["marker"] == "These truth-lifecycle-completeness rules must remain bound to canonical truth-lifecycle-completeness rows rather than drifting into soft summary prose."
    for row in payload["root_doc_anchor_violations"]
), payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "4. runtime or validator code must not finalize truth-lifecycle legality while missing or unexpected row identities remain known only internally;"
new = "4. runtime or validator code may finalize truth-lifecycle legality from aggregate summaries alone;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-002", payload
assert any(
    row["field"] == "truth_lifecycle_completeness_surface"
    and row["reason"] == "truth_lifecycle_completeness_surface_phrase_order_mismatch"
    for row in payload["truth_violations"]
), payload
assert any(
    row["field"] == "truth_lifecycle_completeness_surface"
    and row["reason"] == "missing_truth_lifecycle_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "truth_lifecycle_completeness_surface"
    and row["reason"] == "extra_truth_lifecycle_completeness_surface_rows"
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "truth_lifecycle_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [
    "runtime or validator code must not finalize truth-lifecycle legality while missing or unexpected row identities remain known only internally;"
], payload
assert surface_row["unexpected_ids"] == [
    "runtime or validator code may finalize truth-lifecycle legality from aggregate summaries alone;"
], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY


TRUTH_LIFECYCLE_SURFACE_ORDER_REPO="${TMP_ROOT}/truth-lifecycle-completeness-surface-order-drift-repo"
mirror_repo "${TRUTH_LIFECYCLE_SURFACE_ORDER_REPO}"
python3 - <<'PY' "${TRUTH_LIFECYCLE_SURFACE_ORDER_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = text.replace(
    "1. required lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;\n"
    "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    "2. required lifecycle-stage, memory-strata, differentiation, proof, limit, and collapse rows must remain explicit as separate machine-readable families;\n"
    "1. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    1,
)
path.write_text(text, encoding="utf-8")
PY

TRUTH_LIFECYCLE_SURFACE_ORDER_JSON="${TMP_ROOT}/truth-lifecycle-completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_truth_lifecycle.py" \
  --repo-root "${TRUTH_LIFECYCLE_SURFACE_ORDER_REPO}" \
  --json-only >"${TRUTH_LIFECYCLE_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] root truth-lifecycle validator unexpectedly passed completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${TRUTH_LIFECYCLE_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_truth_lifecycle_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RTLC-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert payload["truth_lifecycle_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["truth_lifecycle_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "truth_lifecycle_completeness_surface"
    and row["reason"] == "truth_lifecycle_completeness_surface_order_mismatch"
    for row in payload["truth_violations"]
), payload
assert any(
    reason == "truth_violation:truth_lifecycle_completeness_surface:truth_lifecycle_completeness_surface_order_mismatch"
    for reason in payload["stale_reasons"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "truth_lifecycle_completeness_surface"
)
assert surface_row["expected_count"] == 5, payload
assert surface_row["actual_count"] == 5, payload
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

echo "[PASS] protocol root truth-lifecycle probes passed"
