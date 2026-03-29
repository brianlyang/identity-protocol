#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=./protocol_root_probe_shadow_common.sh
source "${SCRIPT_DIR}/protocol_root_probe_shadow_common.sh"
protocol_root_probe_bootstrap "${SCRIPT_DIR}" "protocol-root-precedence-ci"

PROBE_REL_PATHS=(
  "scripts/root_corpus_governance_common.py"
  "scripts/root_corpus_ordering_common.py"
  "scripts/root_corpus_authority_common.py"
  "scripts/root_corpus_question_routing_common.py"
  "scripts/root_corpus_transition_common.py"
  "scripts/root_corpus_gateway_admissibility_common.py"
  "scripts/root_corpus_precedence_common.py"
  "scripts/validate_protocol_root_corpus_precedence.py"
  "scripts/registry_alias_control_plane_common.py"
  "scripts/repo_root_resolution_common.py"
  "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh"
)

protocol_root_probe_define_relpath_mirror "${PROBE_REL_PATHS[@]}"


PASS_JSON="${TMP_ROOT}/pass.json"
python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${ROOT}" \
  --json-only >"${PASS_JSON}"

python3 - <<'PY' "${PASS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "PASS_REQUIRED", payload
assert payload["root_doc_anchor_check_count"] == 4, payload
assert payload["root_doc_anchor_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_family_count"] == 6, payload
assert payload["precedence_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert all(row["coverage_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert all(row["identity_projection_status"] == "PASS_REQUIRED" for row in payload["row_family_projection_rows"]), payload
assert payload["conflict_handling_rule_count"] == 4, payload
assert payload["conflict_handling_rule_surface"]["entry_count"] == 4, payload
assert payload["conflict_precedence_completeness_row_count"] == 5, payload
assert payload["conflict_precedence_completeness_rows"][0]["completeness_id"] == "explicit_conflict_precedence_row_families", payload
assert payload["conflict_precedence_completeness_rows"][-1]["completeness_id"] == "fail_close_preserves_conflict_precedence_identity_projection", payload
assert payload["conflict_precedence_completeness_surface"]["entry_count"] == 5, payload
assert payload["conflict_precedence_completeness_surface"]["entries"][0]["contract_phrase"].startswith("required precedence-profile"), payload
assert payload["conflict_precedence_completeness_surface"]["entries"][-1]["contract_phrase"].startswith("fail-close machine output must preserve"), payload
assert payload["conflict_precedence_completeness_surface"]["extraction_violations"] == [], payload
assert any(
    row["conflict_class"] == "current_turn_legality_conflict"
    and row["resolution_mode"] == "machine_enforcement_terminal"
    for row in payload["precedence_profiles"]
), payload
assert any(row["family_id"] == "conflict_handling_rules" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "conflict_handling_rule_surface" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "conflict_precedence_completeness_rows" for row in payload["row_family_projection_rows"]), payload
assert any(row["family_id"] == "conflict_precedence_completeness_surface" for row in payload["row_family_projection_rows"]), payload
assert {row["gateway_class"]: row["preserved_question_class"] for row in payload["gateway_authorship_projection"]} == {
    "constitution": "frozen_protocol_law",
    "runtime_constitution": "frozen_runtime_law",
    "root_contract": "frozen_domain_contract_law",
    "machine_registry_directory": "registry_resolution",
}, payload
PY

COMPLETENESS_REPO="${TMP_ROOT}/missing-completeness-row-repo"
mirror_repo "${COMPLETENESS_REPO}"
python3 - <<'PY' "${COMPLETENESS_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["conflict_precedence_completeness_rows"] = [
    row for row in doc["conflict_precedence_completeness_rows"]
    if row.get("completeness_id") != "hidden_conflict_precedence_identity_drift_forbidden"
]
for idx, row in enumerate(doc["conflict_precedence_completeness_rows"], start=1):
    row["order"] = idx
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

COMPLETENESS_JSON="${TMP_ROOT}/missing-completeness-row.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${COMPLETENESS_REPO}" \
  --json-only >"${COMPLETENESS_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed after removing conflict-precedence completeness row"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert any(
    row["field"] == "conflict_precedence_completeness_rows"
    and row["reason"] == "missing_conflict_precedence_completeness_rows"
    and "hidden_conflict_precedence_identity_drift_forbidden" in row.get("completeness_ids", [])
    for row in payload["structure_violations"]
), payload
row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_precedence_completeness_rows"
)
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_precedence_completeness_surface"
)
assert row["expected_count"] == 5, payload
assert row["actual_count"] == 4, payload
assert row["missing_ids"] == ["hidden_conflict_precedence_identity_drift_forbidden"], payload
assert row["unexpected_ids"] == [], payload
assert row["coverage_status"] == "FAIL_REQUIRED", payload
assert row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

COMPLETENESS_SURFACE_REPO="${TMP_ROOT}/completeness-surface-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_REPO}"
python3 - <<'PY' "${COMPLETENESS_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "1. required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling-rule-surface rows must remain explicit as separate machine-readable row families;"
new = "1. required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling guidance rows must remain explicit as separate machine-readable row families;"
assert old in text, text[:3000]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

COMPLETENESS_SURFACE_JSON="${TMP_ROOT}/completeness-surface-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${COMPLETENESS_SURFACE_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed conflict-precedence completeness surface drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert any(
    row["field"] == "conflict_precedence_completeness_surface"
    and row["reason"] == "missing_conflict_precedence_completeness_surface_rows"
    and "required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling-rule-surface rows must remain explicit as separate machine-readable row families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "conflict_precedence_completeness_surface"
    and row["reason"] == "extra_conflict_precedence_completeness_surface_rows"
    and "required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling guidance rows must remain explicit as separate machine-readable row families;" in row.get("contract_phrases", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_precedence_completeness_surface"
)
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert "required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling-rule-surface rows must remain explicit as separate machine-readable row families;" in surface_row["missing_ids"], payload
assert "required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling guidance rows must remain explicit as separate machine-readable row families;" in surface_row["unexpected_ids"], payload
PY

COMPLETENESS_SURFACE_ORDER_REPO="${TMP_ROOT}/completeness-surface-order-drift-repo"
mirror_repo "${COMPLETENESS_SURFACE_ORDER_REPO}"
protocol_root_probe_swap_numbered_surface_order_rows \
  "${COMPLETENESS_SURFACE_ORDER_REPO}/identity/protocol/README.md" \
  "## Root conflict-precedence completeness discipline" \
  $'\n---\n\n## Root ordering completeness discipline' \
  "1. required precedence-profile, gateway-authorship-projection, conflict-handling-rule, and conflict-handling-rule-surface rows must remain explicit as separate machine-readable row families;" \
  "2. expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;"

COMPLETENESS_SURFACE_ORDER_JSON="${TMP_ROOT}/completeness-surface-order-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${COMPLETENESS_SURFACE_ORDER_REPO}" \
  --json-only >"${COMPLETENESS_SURFACE_ORDER_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed README conflict-precedence completeness surface order drift"
  exit 1
fi

python3 - <<'PY' "${COMPLETENESS_SURFACE_ORDER_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert payload["precedence_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "PASS_REQUIRED", payload
assert any(
    row["field"] == "conflict_precedence_completeness_surface"
    and row["reason"] == "order_mismatch"
    for row in payload["precedence_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_precedence_completeness_surface"
)
assert surface_row["missing_ids"] == [], payload
assert surface_row["unexpected_ids"] == [], payload
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

MISSING_PROFILE_REPO="${TMP_ROOT}/missing-profile-repo"
mirror_repo "${MISSING_PROFILE_REPO}"
python3 - <<'PY' "${MISSING_PROFILE_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["precedence_profiles"] = [
    row for row in doc["precedence_profiles"]
    if row.get("conflict_class") != "demotion_status_conflict"
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

MISSING_PROFILE_JSON="${TMP_ROOT}/missing-profile.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${MISSING_PROFILE_REPO}" \
  --json-only >"${MISSING_PROFILE_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed after removing precedence profile row"
  exit 1
fi

python3 - <<'PY' "${MISSING_PROFILE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert payload["precedence_row_coverage_status"] == "FAIL_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "missing_conflict_classes" and "demotion_status_conflict" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "precedence_profiles"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_authorship_projection"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 3, payload
assert profile_row["missing_ids"] == ["demotion_status_conflict"], payload
assert profile_row["unexpected_ids"] == [], payload
assert profile_row["coverage_status"] == "FAIL_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

RULE_REPO="${TMP_ROOT}/missing-rule-repo"
mirror_repo "${RULE_REPO}"
python3 - <<'PY' "${RULE_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
doc["conflict_handling_rules"] = [
    row for row in doc["conflict_handling_rules"]
    if row.get("rule_text") != "do use machine-consumed sources to determine current-turn truth, validation status, and active-runtime legality."
]
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

RULE_JSON="${TMP_ROOT}/missing-rule.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${RULE_REPO}" \
  --json-only >"${RULE_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed after removing conflict-handling rule row"
  exit 1
fi

python3 - <<'PY' "${RULE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert any(
    row["field"] == "conflict_handling_rules"
    and row["reason"] == "missing_conflict_handling_rules"
    and "do use machine-consumed sources to determine current-turn truth, validation status, and active-runtime legality." in row.get("rule_texts", [])
    for row in payload["structure_violations"]
), payload
rule_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_handling_rules"
)
assert rule_row["expected_count"] == 4, payload
assert rule_row["actual_count"] == 3, payload
assert rule_row["missing_ids"] == ["do use machine-consumed sources to determine current-turn truth, validation status, and active-runtime legality."], payload
assert rule_row["unexpected_ids"] == [], payload
assert rule_row["coverage_status"] == "FAIL_REQUIRED", payload
assert rule_row["identity_projection_status"] == "FAIL_REQUIRED", payload
PY

IDENTITY_REPO="${TMP_ROOT}/identity-drift-repo"
mirror_repo "${IDENTITY_REPO}"
python3 - <<'PY' "${IDENTITY_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row.get("conflict_class") == "demotion_status_conflict":
        row["conflict_class"] = "demotion_status_conflict_alias"
        break
else:
    raise SystemExit("expected demotion_status_conflict row not found")
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

IDENTITY_JSON="${TMP_ROOT}/identity-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${IDENTITY_REPO}" \
  --json-only >"${IDENTITY_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed precedence-profile identity drift"
  exit 1
fi

python3 - <<'PY' "${IDENTITY_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert payload["precedence_row_coverage_status"] == "PASS_REQUIRED", payload
assert payload["precedence_row_identity_projection_status"] == "FAIL_REQUIRED", payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "missing_conflict_classes" and "demotion_status_conflict" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "precedence_profiles" and row["reason"] == "extra_conflict_classes" and "demotion_status_conflict_alias" in row.get("conflict_classes", [])
    for row in payload["structure_violations"]
), payload
profile_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "precedence_profiles"
)
gateway_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "gateway_authorship_projection"
)
assert profile_row["expected_count"] == 4, payload
assert profile_row["actual_count"] == 4, payload
assert profile_row["missing_ids"] == ["demotion_status_conflict"], payload
assert profile_row["unexpected_ids"] == ["demotion_status_conflict_alias"], payload
assert profile_row["coverage_status"] == "PASS_REQUIRED", payload
assert profile_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert gateway_row["coverage_status"] == "PASS_REQUIRED", payload
assert gateway_row["identity_projection_status"] == "PASS_REQUIRED", payload
PY

RULE_SURFACE_REPO="${TMP_ROOT}/rule-surface-repo"
mirror_repo "${RULE_SURFACE_REPO}"
python3 - <<'PY' "${RULE_SURFACE_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "2. do not use philosophy text to override a concrete contract row or runtime truth source;"
new = "2. do not use philosophy text to override a concrete contract row or ontology truth source;"
assert old in text, text
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

RULE_SURFACE_JSON="${TMP_ROOT}/rule-surface.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${RULE_SURFACE_REPO}" \
  --json-only >"${RULE_SURFACE_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed conflict-handling surface drift"
  exit 1
fi

python3 - <<'PY' "${RULE_SURFACE_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-002", payload
assert any(
    row["field"] == "conflict_handling_rule_surface"
    and row["reason"] == "missing_conflict_handling_rule_surface_rows"
    and "do not use philosophy text to override a concrete contract row or runtime truth source;" in row.get("rule_texts", [])
    for row in payload["structure_violations"]
), payload
assert any(
    row["field"] == "conflict_handling_rule_surface"
    and row["reason"] == "extra_conflict_handling_rule_surface_rows"
    and "do not use philosophy text to override a concrete contract row or ontology truth source;" in row.get("rule_texts", [])
    for row in payload["structure_violations"]
), payload
surface_row = next(
    row for row in payload["row_family_projection_rows"]
    if row["family_id"] == "conflict_handling_rule_surface"
)
assert surface_row["coverage_status"] == "PASS_REQUIRED", payload
assert surface_row["identity_projection_status"] == "FAIL_REQUIRED", payload
assert "do not use philosophy text to override a concrete contract row or runtime truth source;" in surface_row["missing_ids"], payload
assert "do not use philosophy text to override a concrete contract row or ontology truth source;" in surface_row["unexpected_ids"], payload
PY

LEGality_DRIFT_REPO="${TMP_ROOT}/legality-drift-repo"
mirror_repo "${LEGality_DRIFT_REPO}"
python3 - <<'PY' "${LEGality_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row["conflict_class"] == "current_turn_legality_conflict":
        row["semantic_precedence_chain"] = ["constitution"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

LEGality_DRIFT_JSON="${TMP_ROOT}/legality-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${LEGality_DRIFT_REPO}" \
  --json-only >"${LEGality_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed legality precedence drift"
  exit 1
fi

python3 - <<'PY' "${LEGality_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "semantic_precedence_chain_mismatch"
    and row.get("conflict_class") == "current_turn_legality_conflict"
    for row in payload["precedence_violations"]
), payload
PY

AUTHORSHIP_DRIFT_REPO="${TMP_ROOT}/authorship-drift-repo"
mirror_repo "${AUTHORSHIP_DRIFT_REPO}"
python3 - <<'PY' "${AUTHORSHIP_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["precedence_profiles"]:
    if row["conflict_class"] == "gateway_authorship_conflict":
        row["forbidden_override_surface_classes"] = ["bottom_theory"]
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

AUTHORSHIP_DRIFT_JSON="${TMP_ROOT}/authorship-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${AUTHORSHIP_DRIFT_REPO}" \
  --json-only >"${AUTHORSHIP_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed gateway authorship drift"
  exit 1
fi

python3 - <<'PY' "${AUTHORSHIP_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "forbidden_override_surface_classes_mismatch"
    and row.get("conflict_class") == "gateway_authorship_conflict"
    for row in payload["precedence_violations"]
), payload
PY

GATEWAY_PROJECTION_DRIFT_REPO="${TMP_ROOT}/gateway-projection-drift-repo"
mirror_repo "${GATEWAY_PROJECTION_DRIFT_REPO}"
python3 - <<'PY' "${GATEWAY_PROJECTION_DRIFT_REPO}/identity/protocol/mappings/root-corpus-precedence.v1.yaml"
import pathlib
import sys
import yaml

path = pathlib.Path(sys.argv[1])
doc = yaml.safe_load(path.read_text(encoding="utf-8"))
for row in doc["gateway_authorship_projection"]:
    if row["gateway_class"] == "root_contract":
        row["preserved_question_class"] = "registry_resolution"
        break
path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
PY

GATEWAY_PROJECTION_DRIFT_JSON="${TMP_ROOT}/gateway-projection-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${GATEWAY_PROJECTION_DRIFT_REPO}" \
  --json-only >"${GATEWAY_PROJECTION_DRIFT_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed gateway projection drift"
  exit 1
fi

python3 - <<'PY' "${GATEWAY_PROJECTION_DRIFT_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert any(
    row["reason"] == "preserved_question_class_mismatch" and row.get("gateway_class") == "root_contract"
    for row in payload["precedence_violations"]
), payload
PY

ANCHOR_REPO="${TMP_ROOT}/anchor-drift-repo"
mirror_repo "${ANCHOR_REPO}"
python3 - <<'PY' "${ANCHOR_REPO}/identity/protocol/README.md"
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
old = "## Root conflict-precedence discipline"
new = "## Root conflict precedence discipline"
assert old in text, text[:1500]
path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY

ANCHOR_JSON="${TMP_ROOT}/anchor-drift.json"
if python3 "${ROOT}/scripts/validate_protocol_root_corpus_precedence.py" \
  --repo-root "${ANCHOR_REPO}" \
  --json-only >"${ANCHOR_JSON}"; then
  echo "[FAIL] precedence validator unexpectedly passed anchor drift"
  exit 1
fi

python3 - <<'PY' "${ANCHOR_JSON}"
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["protocol_root_corpus_precedence_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-RCP-003", payload
assert payload["root_doc_anchor_status"] == "FAIL_REQUIRED", payload
assert any(
    row["rel_path"] == "identity/protocol/README.md" and row["reason"] == "required_marker_missing"
    for row in payload["anchor_violations"]
), payload
PY

echo "[PASS] protocol root-corpus precedence probes passed"
