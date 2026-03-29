#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/terminal-truth-boundary-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

IDENTITY_ID="terminal-truth-boundary-probe"
PACK_PATH="${TMP_DIR}/${IDENTITY_ID}"
CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
CLEAN_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-clean.json"
REVIEW_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-review-required.json"
REPAIR_BLOCKED_REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-repair-blocked.json"
NON_CLOSEOUT_REPORT_PATH="${PACK_PATH}/runtime/reports/${IDENTITY_ID}-active-run.json"
RULEBOOK_PATH="${PACK_PATH}/RULEBOOK.jsonl"
TASK_HISTORY_PATH="${PACK_PATH}/TASK_HISTORY.md"
PROMPT_CONTRACT_PATH="${PACK_PATH}/runtime/state/prompt_contract.json"

mkdir -p "${PACK_PATH}/runtime/reports" "${PACK_PATH}/runtime/state"

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${IDENTITY_ID}" "${CLEAN_REPORT_PATH}" "${REVIEW_REPORT_PATH}" "${REPAIR_BLOCKED_REPORT_PATH}" "${NON_CLOSEOUT_REPORT_PATH}" "${RULEBOOK_PATH}" "${TASK_HISTORY_PATH}" "${PROMPT_CONTRACT_PATH}"
import json
import sys
from pathlib import Path

import yaml

repo_root = Path.cwd()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from blocker_taxonomy_common import BLOCKER_ALIAS_MAP_VERSION, CANONICAL_BLOCKER_TYPES
from create_identity_pack import _collaboration_trigger_contract_skeleton
from terminal_truth_cleanliness_common import terminal_truth_cleanliness_contract_skeleton

catalog_path = Path(sys.argv[1]).resolve()
pack_path = Path(sys.argv[2]).resolve()
identity_id = sys.argv[3]
clean_report_path = Path(sys.argv[4]).resolve()
review_report_path = Path(sys.argv[5]).resolve()
repair_blocked_report_path = Path(sys.argv[6]).resolve()
non_closeout_report_path = Path(sys.argv[7]).resolve()
rulebook_path = Path(sys.argv[8]).resolve()
task_history_path = Path(sys.argv[9]).resolve()
prompt_contract_path = Path(sys.argv[10]).resolve()

canonical_blockers = list(CANONICAL_BLOCKER_TYPES)
catalog_doc = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_path),
            "scope": "USER",
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
        }
    ]
}
catalog_path.write_text(yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")

task_doc = {
    "task_id": f"{identity_id}_task",
    "objective": {"status": "active"},
    "gates": {
        "identity_update_gate": "required",
        "collaboration_trigger_gate": "required",
    },
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
    "blocker_taxonomy_contract": {
        "required": True,
        "required_blocker_types": canonical_blockers,
        "blocker_alias_map_version": BLOCKER_ALIAS_MAP_VERSION,
        "blocker_classification_required_fields": [
            "blocker_type",
            "source",
            "detected_at",
            "requires_human_collab",
            "next_action",
        ],
        "fail_action": "block_merge_and_reenter_collaboration_update",
    },
    "collaboration_trigger_contract": _collaboration_trigger_contract_skeleton(),
    "escalation_policy": {
        "human_collab_blockers": canonical_blockers,
    },
}
task_doc["collaboration_trigger_contract"]["trigger_conditions"] = canonical_blockers
pack_path.joinpath("CURRENT_TASK.json").write_text(
    json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
rulebook_path.write_text("", encoding="utf-8")
task_history_path.write_text("# Task History\n", encoding="utf-8")
prompt_contract_path.write_text("{}\n", encoding="utf-8")

base_doc = {
    "identity_id": identity_id,
    "generated_at": "2026-03-25T00:00:00Z",
    "catalog_path": str(catalog_path),
    "resolved_pack_path": str(pack_path),
    "all_ok": True,
    "upgrade_required": False,
    "permission_state": "PRECHECK",
    "writeback_status": "NOT_REQUIRED",
    "writeback_mode": "STRICT_WRITEBACK",
    "next_recovery_action": "",
    "phase_a_refresh_applied": False,
    "phase_b_strict_revalidate_status": "PASS_REQUIRED",
    "phase_transition_reason": "",
    "phase_transition_error_code": "",
    "governed_outlet_enforced": True,
    "outlet_channel_id": "final_emit_governed",
    "outlet_preflight_receipt": str((pack_path / "runtime" / "reports" / "outlet-preflight.json").resolve()),
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
        str(rulebook_path),
        str(task_history_path),
        str(prompt_contract_path),
    ],
    "writeback_rule_id": "",
    "artifacts": [],
}

clean_doc = dict(base_doc)
clean_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-clean",
        "mode": "safe-auto",
        "next_action": "no_upgrade_triggered",
        "is_terminal_clean": True,
        "publishable": True,
        "canonical_result_eligible": True,
        "terminal_truth_class": "clean_terminal_truth",
        "terminal_state_class": "completed_clean",
        "negative_feedback_class": "",
    }
)
clean_report_path.write_text(json.dumps(clean_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

review_doc = dict(base_doc)
review_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-review-required",
        "mode": "review-required",
        "next_action": "review_required_followup",
        "is_terminal_clean": False,
        "publishable": False,
        "canonical_result_eligible": False,
        "terminal_truth_class": "review_required_execution_closure",
        "terminal_state_class": "review_pending",
        "negative_feedback_class": "review_required",
    }
)
review_report_path.write_text(json.dumps(review_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

repair_blocked_doc = dict(base_doc)
repair_blocked_doc.update(
    {
        "run_id": f"identity-upgrade-exec-{identity_id}-repair-blocked",
        "mode": "safe-auto",
        "next_action": "mutate_prompt_and_writeback",
        "upgrade_required": True,
        "writeback_status": "WRITTEN",
        "writeback_mode": "STRICT_WRITEBACK",
        "writeback_rule_id": "rule-entry-terminal-truth-boundary-probe",
        "experience_writeback": {
            "required": True,
            "status": "WRITTEN",
            "error_code": "",
            "mode": "safe-auto",
        },
        "is_terminal_clean": True,
        "publishable": True,
        "canonical_result_eligible": True,
        "terminal_truth_class": "clean_terminal_truth",
        "terminal_state_class": "completed_clean",
        "negative_feedback_class": "",
    }
)
repair_blocked_report_path.write_text(
    json.dumps(repair_blocked_doc, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

non_closeout_report_path.write_text(
    json.dumps(
        {
            "run_id": f"{identity_id}-active-run",
            "identity_id": identity_id,
            "generated_at": "2026-03-25T00:05:00Z",
            "artifacts": [],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

python3 - <<'PY' "${CATALOG_PATH}" "${CLEAN_REPORT_PATH}" "${REVIEW_REPORT_PATH}" "${REPAIR_BLOCKED_REPORT_PATH}" "${NON_CLOSEOUT_REPORT_PATH}" "${IDENTITY_ID}"
import json
import sys
from pathlib import Path

repo_root = Path.cwd()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

import release_readiness_check as readiness
from terminal_truth_boundary_projection_common import (
    build_release_readiness_terminal_truth_boundary_one_look_projection,
    build_terminal_truth_boundary_projection_from_report,
    build_terminal_truth_boundary_projection_summary_skeleton,
)

catalog_path = Path(sys.argv[1]).resolve()
clean_report_path = Path(sys.argv[2]).resolve()
review_report_path = Path(sys.argv[3]).resolve()
repair_blocked_report_path = Path(sys.argv[4]).resolve()
non_closeout_report_path = Path(sys.argv[5]).resolve()
identity_id = sys.argv[6]

def load_doc(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

clean_projection = build_terminal_truth_boundary_projection_from_report(
    report_doc=load_doc(clean_report_path),
    report_path=clean_report_path,
    catalog_path=catalog_path,
    repo_catalog_path=catalog_path,
    identity_id=identity_id,
    operation="readiness",
)
assert clean_projection["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", clean_projection
assert clean_projection["repair_lane_status"] == "PASS_REQUIRED", clean_projection
assert clean_projection["experience_writeback_validation_status"] == "SKIPPED_NOT_REQUIRED", clean_projection
assert clean_projection["terminal_truth_observation_status"] == "PASS_REQUIRED", clean_projection
assert clean_projection["admission_lane_projection"] == "NOT_BLOCKED_BY_TERMINAL_TRUTH", clean_projection
assert clean_projection["boundary_health_class"] == "repair_green_terminal_truth_clean", clean_projection
assert clean_projection["repair_success_not_clean_terminal_truth"] is False, clean_projection
assert clean_projection["negative_feedback_class"] == "none", clean_projection
assert clean_projection["publishable"] is True, clean_projection
assert clean_projection["canonical_result_eligible"] is True, clean_projection

review_projection = build_terminal_truth_boundary_projection_from_report(
    report_doc=load_doc(review_report_path),
    report_path=review_report_path,
    catalog_path=catalog_path,
    repo_catalog_path=catalog_path,
    identity_id=identity_id,
    operation="readiness",
)
assert review_projection["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", review_projection
assert review_projection["repair_lane_status"] == "PASS_REQUIRED", review_projection
assert review_projection["repair_observation_status"] == "WARN_NON_BLOCKING", review_projection
assert review_projection["experience_writeback_validation_status"] == "SKIPPED_NOT_REQUIRED", review_projection
assert review_projection["terminal_truth_observation_status"] == "FAIL_REQUIRED", review_projection
assert review_projection["admission_lane_projection"] == "BLOCKED_BY_TERMINAL_TRUTH", review_projection
assert review_projection["boundary_health_class"] == "repair_green_terminal_truth_blocked", review_projection
assert review_projection["repair_success_not_clean_terminal_truth"] is True, review_projection
assert review_projection["terminal_truth_class"] == "review_required_execution_closure", review_projection
assert review_projection["terminal_state_class"] == "review_pending", review_projection
assert review_projection["negative_feedback_class"] == "review_required", review_projection
assert review_projection["publishable"] is False, review_projection
assert review_projection["canonical_result_eligible"] is False, review_projection

repair_blocked_projection = build_terminal_truth_boundary_projection_from_report(
    report_doc=load_doc(repair_blocked_report_path),
    report_path=repair_blocked_report_path,
    catalog_path=catalog_path,
    repo_catalog_path=catalog_path,
    identity_id=identity_id,
    operation="readiness",
)
assert repair_blocked_projection["terminal_truth_boundary_projection_status"] == "PASS_REQUIRED", repair_blocked_projection
assert repair_blocked_projection["repair_lane_status"] == "FAIL_REQUIRED", repair_blocked_projection
assert repair_blocked_projection["experience_writeback_validation_status"] == "FAIL_REQUIRED", repair_blocked_projection
assert repair_blocked_projection["terminal_truth_observation_status"] == "FAIL_REQUIRED", repair_blocked_projection
assert repair_blocked_projection["admission_lane_projection"] == "BLOCKED_BY_TERMINAL_TRUTH", repair_blocked_projection
assert repair_blocked_projection["boundary_health_class"] == "repair_blocked_terminal_truth_blocked", repair_blocked_projection
assert repair_blocked_projection["terminal_truth_class"] == "non_terminal_or_failed_execution", repair_blocked_projection
assert repair_blocked_projection["terminal_state_class"] == "non_terminal_pending", repair_blocked_projection
assert repair_blocked_projection["publishable"] is False, repair_blocked_projection
assert repair_blocked_projection["canonical_result_eligible"] is False, repair_blocked_projection
assert "rulebook_missing_run_link" in " ".join(
    repair_blocked_projection.get("experience_writeback_validation_stale_reasons", [])
), repair_blocked_projection

non_closeout_projection = build_terminal_truth_boundary_projection_from_report(
    report_doc=load_doc(non_closeout_report_path),
    report_path=non_closeout_report_path,
    catalog_path=catalog_path,
    repo_catalog_path=catalog_path,
    identity_id=identity_id,
    operation="readiness",
)
assert non_closeout_projection["terminal_truth_boundary_projection_status"] == "SKIPPED_NOT_REQUIRED", non_closeout_projection
assert non_closeout_projection["admission_lane_projection"] == "NOT_APPLICABLE", non_closeout_projection

summary_skeleton = build_terminal_truth_boundary_projection_summary_skeleton()
assert summary_skeleton["total_identities"] == 0, summary_skeleton
assert summary_skeleton["projection_pass"] == 0, summary_skeleton
assert summary_skeleton["projection_fail"] == 0, summary_skeleton
assert summary_skeleton["not_applicable"] == 0, summary_skeleton
assert summary_skeleton["blocked_by_terminal_truth"] == 0, summary_skeleton
assert summary_skeleton["repair_green_terminal_truth_blocked"] == 0, summary_skeleton
assert summary_skeleton["repair_green_terminal_truth_clean"] == 0, summary_skeleton
assert summary_skeleton["blocked_identity_ids"] == [], summary_skeleton

summary = {
    "terminal_truth_boundary_projection": review_projection,
}
readiness._hydrate_one_look_projection(summary)
one_look = summary["one_look"]
expected_one_look = build_release_readiness_terminal_truth_boundary_one_look_projection(
    review_projection
)
for field_name, expected_value in expected_one_look.items():
    assert one_look[field_name] == expected_value, (field_name, one_look)

print(json.dumps({
    "terminal_truth_boundary_projection_probe_status": "PASS_REQUIRED",
    "review_boundary_health_class": review_projection["boundary_health_class"],
    "clean_boundary_health_class": clean_projection["boundary_health_class"],
    "repair_blocked_boundary_health_class": repair_blocked_projection["boundary_health_class"],
}, ensure_ascii=False))
PY

echo "[PASS] terminal truth boundary projection probes passed"
