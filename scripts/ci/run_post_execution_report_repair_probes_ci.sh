#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/postexec-repair-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

IDENTITY_ID="postexec-probe-identity"
PACK_PATH="${TMP_DIR}/${IDENTITY_ID}"
CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-baseline-clean.json"
REVIEW_REQUIRED_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-review-required.json"
EXPLICIT_DIRTY_RETRY_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-explicit-dirty-retry.json"
UPGRADE_CLOSED_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-upgrade-closed.json"
NON_CLOSEOUT_REPORT_PATH="${PACK_PATH}/runtime/reports/${IDENTITY_ID}-active-run.json"
OUTLET_RECEIPT_PATH="${TMP_DIR}/outlet-preflight.json"
RULEBOOK_PATH="${PACK_PATH}/RULEBOOK.jsonl"
TASK_HISTORY_PATH="${PACK_PATH}/TASK_HISTORY.md"
PROMPT_CONTRACT_PATH="${PACK_PATH}/runtime/state/prompt_contract.json"

mkdir -p "${PACK_PATH}/runtime/reports" "${PACK_PATH}/runtime/state"
printf '{}\n' > "${OUTLET_RECEIPT_PATH}"
printf '{}\n' > "${PROMPT_CONTRACT_PATH}"
printf '' > "${RULEBOOK_PATH}"
printf '# Task History\n' > "${TASK_HISTORY_PATH}"

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${IDENTITY_ID}" "${REPORT_PATH}" "${REVIEW_REQUIRED_REPORT_PATH}" "${EXPLICIT_DIRTY_RETRY_REPORT_PATH}" "${UPGRADE_CLOSED_REPORT_PATH}" "${NON_CLOSEOUT_REPORT_PATH}" "${OUTLET_RECEIPT_PATH}" "${RULEBOOK_PATH}" "${TASK_HISTORY_PATH}" "${PROMPT_CONTRACT_PATH}"
import json
import sys
from pathlib import Path

repo_root = Path.cwd()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from terminal_truth_cleanliness_common import terminal_truth_cleanliness_contract_skeleton

catalog_path = Path(sys.argv[1])
pack_path = Path(sys.argv[2])
identity_id = sys.argv[3]
report_path = Path(sys.argv[4])
review_required_report_path = Path(sys.argv[5])
explicit_dirty_retry_report_path = Path(sys.argv[6])
upgrade_closed_report_path = Path(sys.argv[7])
non_closeout_report_path = Path(sys.argv[8])
outlet_receipt_path = Path(sys.argv[9])
rulebook_path = Path(sys.argv[10])
task_history_path = Path(sys.argv[11])
prompt_contract_path = Path(sys.argv[12])

catalog_doc = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_path.resolve()),
            "scope": "USER",
        }
    ]
}
catalog_path.write_text(json.dumps(catalog_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

task_doc = {
    "task_id": f"{identity_id}_task",
    "objective": {"status": "active"},
    "gates": {"identity_update_gate": "required"},
    "post_execution_mandatory": [
        "append task outcome into TASK_HISTORY.md",
        "update objective.status",
    ],
    "capability_orchestration_contract": {
        "required": True,
        "preflight_requirements": [],
        "task_type_routes": {
            "instance_delivery": {
                "pipeline": ["observe_context", "emit"],
                "primary_skills": [],
                "fallback_skills": [],
                "required_mcp": [],
                "primary_instance_scripts": [],
                "fallback_instance_scripts": [],
                "script_receipt_pattern": "",
                "allowed_execution_lanes": [],
                "lane_admission_policy": {},
                "lane_receipt_pattern": "",
                "lane_block_on_fallback": False,
                "direct_tool_entry_policy": {},
            }
        },
    },
    "writeback_continuity_contract_v1": {"required": True},
    "identity_terminal_truth_cleanliness_contract_v1": terminal_truth_cleanliness_contract_skeleton(),
}
pack_path.joinpath("CURRENT_TASK.json").write_text(
    json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

report_doc = {
    "run_id": report_path.stem,
    "identity_id": identity_id,
    "generated_at": "2026-03-25T00:00:00Z",
    "mode": "safe-auto",
    "catalog_path": str(catalog_path.resolve()),
    "resolved_pack_path": str(pack_path.resolve()),
    "all_ok": True,
    "upgrade_required": False,
    "permission_state": "PRECHECK",
    "writeback_status": "NOT_REQUIRED",
    "writeback_mode": "STRICT_WRITEBACK",
    "next_action": "no_upgrade_triggered",
    "next_recovery_action": "",
    "phase_a_refresh_applied": False,
    "phase_b_strict_revalidate_status": "PASS_REQUIRED",
    "phase_transition_reason": "",
    "phase_transition_error_code": "",
    "governed_outlet_enforced": True,
    "outlet_channel_id": "final_emit_governed",
    "outlet_preflight_receipt": str(outlet_receipt_path.resolve()),
    "outlet_bypass_detected": False,
    "final_emit_channel_id": "final_emit_governed",
    "final_emit_policy_mode": "tool_choice_required",
    "final_emit_schema_id": "hud_headstamp_final_emit_schema_v1",
    "final_emit_schema_status": "PASS_REQUIRED",
    "final_emit_contract_status": "PASS_REQUIRED",
    "experience_writeback": {
        "required": False,
        "status": "NOT_REQUIRED",
        "error_code": "",
        "mode": "safe-auto",
    },
    "writeback_paths": [
        str(rulebook_path.resolve()),
        str(task_history_path.resolve()),
        str(prompt_contract_path.resolve()),
    ],
    "writeback_rule_id": "",
    "artifacts": [],
    "is_terminal_clean": True,
    "publishable": True,
    "terminal_truth_class": "clean_terminal_truth",
}
report_path.write_text(json.dumps(report_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

review_required_report_doc = dict(report_doc)
review_required_report_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-review-required",
        "generated_at": "2026-03-25T00:02:00Z",
        "mode": "review-required",
        "upgrade_required": False,
        "writeback_status": "NOT_REQUIRED",
        "writeback_mode": "STRICT_WRITEBACK",
        "next_action": "review_required_followup",
        "experience_writeback": {
            "required": False,
            "status": "NOT_REQUIRED",
            "error_code": "",
            "mode": "review-required",
        },
        "is_terminal_clean": False,
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_class": "review_required_execution_closure",
        "terminal_state_class": "review_pending",
        "negative_feedback_class": "review_required",
    }
)
review_required_report_path.write_text(
    json.dumps(review_required_report_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

explicit_dirty_retry_report_doc = dict(report_doc)
explicit_dirty_retry_report_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-explicit-dirty-retry",
        "generated_at": "2026-03-25T00:02:30Z",
        "mode": "safe-auto",
        "upgrade_required": False,
        "writeback_status": "NOT_REQUIRED",
        "writeback_mode": "STRICT_WRITEBACK",
        "next_action": "publish_ready_if_clean",
        "next_recovery_action": "",
        "experience_writeback": {
            "required": False,
            "status": "NOT_REQUIRED",
            "error_code": "",
            "mode": "safe-auto",
        },
        "fallback_reason": "model_fallback_required_before_publish",
        "needs_revalidation": True,
        "retry_required": True,
        "error_info": {"code": "retry_needed_after_fallback", "status": "degraded"},
        "is_terminal_clean": False,
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_class": "dirty_terminal_execution_closure",
        "terminal_state_class": "retry_pending",
        "negative_feedback_class": "degraded_execution",
    }
)
explicit_dirty_retry_report_path.write_text(
    json.dumps(explicit_dirty_retry_report_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

upgrade_closed_report_doc = dict(report_doc)
upgrade_closed_report_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-upgrade-closed",
        "generated_at": "2026-03-25T00:03:00Z",
        "mode": "safe-auto",
        "upgrade_required": True,
        "writeback_status": "WRITTEN",
        "writeback_mode": "STRICT_WRITEBACK",
        "next_action": "patch_applied_and_writeback_completed",
        "experience_writeback": {
            "required": True,
            "status": "WRITTEN",
            "error_code": "",
            "mode": "safe-auto",
        },
        "writeback_rule_id": "rule-entry-postexec-upgrade-closed",
    }
)
rulebook_path.write_text(
    json.dumps(
        {
            "rule_entry_id": "rule-entry-postexec-upgrade-closed",
            "evidence_run_id": f"identity-upgrade-exec-{identity_id}-upgrade-closed",
            "summary": "upgrade closed writeback continuity",
        },
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
task_history_path.write_text(
    "# Task History\n\n"
    f"- run_id=identity-upgrade-exec-{identity_id}-upgrade-closed writeback completed\n",
    encoding="utf-8",
)
upgrade_closed_report_path.write_text(
    json.dumps(upgrade_closed_report_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

non_closeout_report_doc = {
    "run_id": f"{identity_id}-active-run",
    "identity_id": identity_id,
    "generated_at": "2026-03-25T00:05:00Z",
    "artifacts": [],
}
non_closeout_report_path.write_text(
    json.dumps(non_closeout_report_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

DRYRUN_JSON="${TMP_DIR}/repair-dryrun.json"
APPLY_JSON="${TMP_DIR}/repair-apply.json"
POSTEXEC_JSON="${TMP_DIR}/postexec-validate.json"
TERMINAL_JSON="${TMP_DIR}/terminal-validate.json"
REVIEW_APPLY_JSON="${TMP_DIR}/repair-review-apply.json"
REVIEW_POSTEXEC_JSON="${TMP_DIR}/postexec-review-validate.json"
REVIEW_TERMINAL_JSON="${TMP_DIR}/terminal-review-validate.json"
EXPLICIT_DIRTY_RETRY_APPLY_JSON="${TMP_DIR}/repair-explicit-dirty-retry-apply.json"
EXPLICIT_DIRTY_RETRY_POSTEXEC_JSON="${TMP_DIR}/postexec-explicit-dirty-retry-validate.json"
EXPLICIT_DIRTY_RETRY_TERMINAL_JSON="${TMP_DIR}/terminal-explicit-dirty-retry-validate.json"
UPGRADE_APPLY_JSON="${TMP_DIR}/repair-upgrade-apply.json"
UPGRADE_POSTEXEC_JSON="${TMP_DIR}/postexec-upgrade-closed-validate.json"

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REPORT_PATH}" \
  --json-only > "${DRYRUN_JSON}" || true

python3 - <<'PY' "${DRYRUN_JSON}"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text())
assert payload["post_execution_report_repair_status"] == "FAIL_REQUIRED", payload
assert "apply_required_for_post_execution_report_repair" in (payload.get("stale_reasons") or []), payload
assert payload["capability_activation_missing_fields_after"] == [], payload
assert payload["post_execution_validation_status_after"] == "PASS_REQUIRED", payload
assert payload["writeback_continuity_status_after"] == "PASS_REQUIRED", payload
assert payload["terminal_truth_validation_status_after"] == "PASS_REQUIRED", payload
assert payload["execution_closure_status_after"] == "PASS_REQUIRED", payload
assert payload["terminal_truth_cleanliness_status_after"] == "PASS_REQUIRED", payload
assert payload["terminal_state_machine_status_after"] == "PASS_REQUIRED", payload
assert payload["negative_feedback_terminal_veto_status_after"] == "PASS_REQUIRED", payload
assert payload["dirty_signals_after"] == [], payload
assert payload["terminal_truth_blockers_after"] == [], payload
assert payload["changed_key_count"] > 0, payload
PY

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REPORT_PATH}" \
  --apply \
  --json-only > "${APPLY_JSON}"

python3 scripts/validate_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REPORT_PATH}" \
  --operation readiness \
  --json-only > "${POSTEXEC_JSON}"

python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REPORT_PATH}" \
  --operation readiness \
  --json-only > "${TERMINAL_JSON}"

python3 - <<'PY' "${APPLY_JSON}" "${POSTEXEC_JSON}" "${TERMINAL_JSON}" "${REPORT_PATH}"
import json
import sys
from pathlib import Path

apply_payload = json.loads(Path(sys.argv[1]).read_text())
postexec_payload = json.loads(Path(sys.argv[2]).read_text())
terminal_payload = json.loads(Path(sys.argv[3]).read_text())
report_payload = json.loads(Path(sys.argv[4]).read_text())

assert apply_payload["post_execution_report_repair_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["report_updated"] is True, apply_payload
assert apply_payload["capability_activation_missing_fields_after"] == [], apply_payload
assert postexec_payload["post_execution_mandatory_status"] == "PASS_REQUIRED", postexec_payload
assert terminal_payload["identity_terminal_truth_cleanliness_status"] == "PASS_REQUIRED", terminal_payload
assert postexec_payload["report_selected_path"] == str(Path(sys.argv[4]).resolve()), postexec_payload
assert str(postexec_payload["report_logical_identity_key"]).strip(), postexec_payload
assert postexec_payload["report_selection_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_selected_authority_class"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_pointer_resolution_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["experience_writeback_validation_status"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selected_path"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selection_mode"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selected_authority_class"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_pointer_resolution_mode"] == "", postexec_payload
assert terminal_payload["report_selection_mode"] == "explicit_report_override", terminal_payload
assert terminal_payload["report_selected_authority_class"] == "explicit_report_override", terminal_payload

for key in [
    "route_scope",
    "route_scope_mode",
    "route_ids",
    "route_selection_cardinality",
    "declared_dependency_projection",
    "observed_dependency_projection",
    "dependency_gap_reasons",
    "undeclared_usage_detected",
    "undeclared_usage_rows",
    "missing_declared_dependency_detected",
    "missing_declared_dependency_rows",
    "execution_closure_status",
    "terminal_truth_cleanliness_status",
    "terminal_truth_class",
    "is_terminal_clean",
    "publishable",
    "canonical_result_eligible",
]:
    assert key in report_payload, (key, report_payload)
PY

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REVIEW_REQUIRED_REPORT_PATH}" \
  --apply \
  --json-only > "${REVIEW_APPLY_JSON}"

python3 scripts/validate_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REVIEW_REQUIRED_REPORT_PATH}" \
  --operation readiness \
  --json-only > "${REVIEW_POSTEXEC_JSON}"

python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REVIEW_REQUIRED_REPORT_PATH}" \
  --operation readiness \
  --json-only > "${REVIEW_TERMINAL_JSON}" || true

python3 - <<'PY' "${REVIEW_APPLY_JSON}" "${REVIEW_POSTEXEC_JSON}" "${REVIEW_TERMINAL_JSON}" "${REVIEW_REQUIRED_REPORT_PATH}"
import json
import sys
from pathlib import Path

apply_payload = json.loads(Path(sys.argv[1]).read_text())
postexec_payload = json.loads(Path(sys.argv[2]).read_text())
terminal_payload = json.loads(Path(sys.argv[3]).read_text())
report_payload = json.loads(Path(sys.argv[4]).read_text())

assert apply_payload["post_execution_report_repair_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["repair_blocking_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["repair_observation_status"] == "WARN_NON_BLOCKING", apply_payload
assert apply_payload["stale_reasons"] == [], apply_payload
assert "terminal_truth_validator_not_green_after_projection" in (
    apply_payload.get("observation_stale_reasons") or []
), apply_payload
assert apply_payload["terminal_truth_validation_status_after"] == "FAIL_REQUIRED", apply_payload
assert apply_payload["execution_closure_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["terminal_truth_cleanliness_status_after"] == "FAIL_REQUIRED", apply_payload
assert apply_payload["terminal_truth_class_after"] == "review_required_execution_closure", apply_payload
assert apply_payload["terminal_state_machine_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["terminal_state_class_after"] == "review_pending", apply_payload
assert apply_payload["negative_feedback_class_after"] == "review_required", apply_payload
assert apply_payload["negative_feedback_terminal_veto_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["loopback_required_after"] is False, apply_payload
assert apply_payload["next_state_after_veto_after"] == "review_pending", apply_payload
assert apply_payload["publishable_after"] is False, apply_payload
assert apply_payload["canonical_result_eligible_after"] is False, apply_payload
assert "review_required_next_action" in (apply_payload.get("dirty_signals_after") or []), apply_payload
assert "review_required_next_action" in (apply_payload.get("terminal_truth_blockers_after") or []), apply_payload
assert postexec_payload["post_execution_mandatory_status"] == "PASS_REQUIRED", postexec_payload
assert postexec_payload["report_selected_path"] == str(Path(sys.argv[4]).resolve()), postexec_payload
assert str(postexec_payload["report_logical_identity_key"]).strip(), postexec_payload
assert terminal_payload["identity_terminal_truth_cleanliness_status"] == "FAIL_REQUIRED", terminal_payload
assert postexec_payload["report_selection_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_selected_authority_class"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_pointer_resolution_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["experience_writeback_validation_status"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selected_path"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selection_mode"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_selected_authority_class"] == "", postexec_payload
assert postexec_payload["experience_writeback_report_pointer_resolution_mode"] == "", postexec_payload
assert terminal_payload["report_selection_mode"] == "explicit_report_override", terminal_payload
assert terminal_payload["terminal_truth_class"] == "review_required_execution_closure", terminal_payload
assert terminal_payload["execution_closure_status"] == "PASS_REQUIRED", terminal_payload
assert report_payload["terminal_truth_class"] == "review_required_execution_closure", report_payload
assert report_payload["publishable"] is False, report_payload
assert report_payload["canonical_result_eligible"] is False, report_payload
PY

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${EXPLICIT_DIRTY_RETRY_REPORT_PATH}" \
  --apply \
  --json-only > "${EXPLICIT_DIRTY_RETRY_APPLY_JSON}"

python3 scripts/validate_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${EXPLICIT_DIRTY_RETRY_REPORT_PATH}" \
  --operation readiness \
  --json-only > "${EXPLICIT_DIRTY_RETRY_POSTEXEC_JSON}"

python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${EXPLICIT_DIRTY_RETRY_REPORT_PATH}" \
  --operation readiness \
  --json-only > "${EXPLICIT_DIRTY_RETRY_TERMINAL_JSON}" || true

python3 - <<'PY' "${EXPLICIT_DIRTY_RETRY_APPLY_JSON}" "${EXPLICIT_DIRTY_RETRY_POSTEXEC_JSON}" "${EXPLICIT_DIRTY_RETRY_TERMINAL_JSON}" "${EXPLICIT_DIRTY_RETRY_REPORT_PATH}"
import json
import sys
from pathlib import Path

apply_payload = json.loads(Path(sys.argv[1]).read_text())
postexec_payload = json.loads(Path(sys.argv[2]).read_text())
terminal_payload = json.loads(Path(sys.argv[3]).read_text())
report_payload = json.loads(Path(sys.argv[4]).read_text())

assert apply_payload["post_execution_report_repair_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["repair_blocking_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["repair_observation_status"] == "WARN_NON_BLOCKING", apply_payload
assert apply_payload["stale_reasons"] == [], apply_payload
assert "terminal_truth_validator_not_green_after_projection" in (
    apply_payload.get("observation_stale_reasons") or []
), apply_payload
assert apply_payload["post_execution_validation_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["writeback_continuity_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["terminal_truth_validation_status_after"] == "FAIL_REQUIRED", apply_payload
assert apply_payload["execution_closure_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["terminal_truth_cleanliness_status_after"] == "FAIL_REQUIRED", apply_payload
assert apply_payload["terminal_truth_class_after"] == "dirty_terminal_execution_closure", apply_payload
assert apply_payload["terminal_state_machine_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["terminal_state_class_after"] == "retry_pending", apply_payload
assert apply_payload["negative_feedback_class_after"] == "degraded_execution", apply_payload
assert apply_payload["negative_feedback_terminal_veto_status_after"] == "PASS_REQUIRED", apply_payload
assert apply_payload["loopback_required_after"] is True, apply_payload
assert apply_payload["next_state_after_veto_after"] == "retry_pending", apply_payload
assert apply_payload["publishable_after"] is False, apply_payload
assert apply_payload["canonical_result_eligible_after"] is False, apply_payload
for signal in [
    "fallback_reason_present",
    "explicit_revalidation_required",
    "explicit_retry_required",
    "error_info_dirty_signal",
]:
    assert signal in (apply_payload.get("dirty_signals_after") or []), (signal, apply_payload)
    assert signal in (apply_payload.get("terminal_truth_blockers_after") or []), (signal, apply_payload)
assert postexec_payload["post_execution_mandatory_status"] == "PASS_REQUIRED", postexec_payload
assert terminal_payload["identity_terminal_truth_cleanliness_status"] == "FAIL_REQUIRED", terminal_payload
assert terminal_payload["terminal_truth_class"] == "dirty_terminal_execution_closure", terminal_payload
assert terminal_payload["execution_closure_status"] == "PASS_REQUIRED", terminal_payload
assert report_payload["terminal_truth_class"] == "dirty_terminal_execution_closure", report_payload
assert report_payload["terminal_state_class"] == "retry_pending", report_payload
assert report_payload["publishable"] is False, report_payload
assert report_payload["canonical_result_eligible"] is False, report_payload
PY

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${UPGRADE_CLOSED_REPORT_PATH}" \
  --apply \
  --json-only > "${UPGRADE_APPLY_JSON}"

python3 scripts/validate_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${UPGRADE_CLOSED_REPORT_PATH}" \
  --operation readiness \
  --json-only > "${UPGRADE_POSTEXEC_JSON}"

python3 - <<'PY' "${UPGRADE_APPLY_JSON}" "${UPGRADE_POSTEXEC_JSON}" "${UPGRADE_CLOSED_REPORT_PATH}"
import json
import sys
from pathlib import Path

apply_payload = json.loads(Path(sys.argv[1]).read_text())
postexec_payload = json.loads(Path(sys.argv[2]).read_text())
report_path = str(Path(sys.argv[3]).resolve())

assert apply_payload["post_execution_report_repair_status"] == "PASS_REQUIRED", apply_payload
assert apply_payload["report_updated"] is True, apply_payload
assert postexec_payload["post_execution_mandatory_status"] == "PASS_REQUIRED", postexec_payload
assert postexec_payload["report_selected_path"] == report_path, postexec_payload
assert str(postexec_payload["report_logical_identity_key"]).strip(), postexec_payload
assert postexec_payload["report_selection_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_selected_authority_class"] == "explicit_report_override", postexec_payload
assert postexec_payload["report_pointer_resolution_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["experience_writeback_validation_status"] == "PASS_REQUIRED", postexec_payload
assert postexec_payload["experience_writeback_report_selected_path"] == report_path, postexec_payload
assert str(postexec_payload["experience_writeback_report_logical_identity_key"]).strip(), postexec_payload
assert postexec_payload["experience_writeback_report_selection_mode"] == "explicit_report_override", postexec_payload
assert postexec_payload["experience_writeback_report_selected_authority_class"] == "explicit_report_override", postexec_payload
assert postexec_payload["experience_writeback_report_pointer_resolution_mode"] == "explicit_report_override", postexec_payload
PY

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${IDENTITY_ID}" "${NON_CLOSEOUT_REPORT_PATH}"
import json
import sys
from pathlib import Path

repo_root = Path.cwd()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from post_execution_report_repair_common import enrich_post_execution_report

catalog_path = Path(sys.argv[1]).resolve()
pack_path = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
report_path = Path(sys.argv[4]).resolve()
report_doc = json.loads(report_path.read_text(encoding="utf-8"))

result = enrich_post_execution_report(
    report_doc=report_doc,
    report_path=report_path,
    catalog_path=catalog_path,
    repo_catalog_path=catalog_path,
    identity_id=identity_id,
    operation="readiness",
)

applicability = result.get("projection_applicability") or {}
assert applicability["status"] == "SKIPPED_NOT_REQUIRED", applicability
assert applicability["applicable"] is False, applicability
assert applicability["report_surface_class"] == "non_closeout_runtime_surface", applicability
assert result["report_changed"] is False, result
assert result["changed_keys"] == [], result
assert (result.get("post_execution_validation") or {}).get("status") == "SKIPPED_NOT_REQUIRED", result
assert (result.get("writeback_continuity_validation") or {}).get("status") == "SKIPPED_NOT_REQUIRED", result
assert (result.get("terminal_truth_validation") or {}).get("status") == "SKIPPED_NOT_REQUIRED", result
assert result.get("stale_reasons") == [], result
PY

echo "[PASS] post-execution report repair probes passed"
