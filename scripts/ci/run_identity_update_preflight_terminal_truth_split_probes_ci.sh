#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/identity-update-preflight-ttc-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

IDENTITY_ID="update-preflight-terminal-truth-probe"
PACK_PATH="${TMP_DIR}/${IDENTITY_ID}"
CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-${IDENTITY_ID}-review-required.json"
ACTIVE_POINTER_PATH="${PACK_PATH}/runtime/state/active_execution_report.json"
RULEBOOK_PATH="${PACK_PATH}/RULEBOOK.jsonl"
TASK_HISTORY_PATH="${PACK_PATH}/TASK_HISTORY.md"
PROMPT_PATH="${PACK_PATH}/IDENTITY_PROMPT.md"
PROMPT_CONTRACT_PATH="${PACK_PATH}/runtime/state/prompt_contract.json"

mkdir -p "${PACK_PATH}/runtime/reports" "${PACK_PATH}/runtime/state"

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${IDENTITY_ID}" "${REPORT_PATH}" "${ACTIVE_POINTER_PATH}" "${RULEBOOK_PATH}" "${TASK_HISTORY_PATH}" "${PROMPT_PATH}" "${PROMPT_CONTRACT_PATH}"
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
report_path = Path(sys.argv[4]).resolve()
active_pointer_path = Path(sys.argv[5]).resolve()
rulebook_path = Path(sys.argv[6]).resolve()
task_history_path = Path(sys.argv[7]).resolve()
prompt_path = Path(sys.argv[8]).resolve()
prompt_contract_path = Path(sys.argv[9]).resolve()

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

prompt_path.write_text(f"# {identity_id}\n\nHermetic update-preflight terminal-truth split probe.\n", encoding="utf-8")
task_history_path.write_text("# Task History\n", encoding="utf-8")
rulebook_path.write_text("", encoding="utf-8")
prompt_contract_path.write_text("{}\n", encoding="utf-8")

report_doc = {
    "run_id": f"identity-upgrade-exec-{identity_id}-review-required",
    "identity_id": identity_id,
    "generated_at": "2026-03-25T00:02:00Z",
    "mode": "review-required",
    "catalog_path": str(catalog_path),
    "resolved_pack_path": str(pack_path),
    "all_ok": True,
    "upgrade_required": False,
    "permission_state": "PRECHECK",
    "writeback_status": "NOT_REQUIRED",
    "writeback_mode": "STRICT_WRITEBACK",
    "next_action": "review_required_followup",
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
        "mode": "review-required",
    },
    "writeback_paths": [
        str(rulebook_path),
        str(task_history_path),
        str(prompt_contract_path),
    ],
    "writeback_rule_id": "",
    "artifacts": [],
    "is_terminal_clean": False,
    "publishable": False,
    "canonical_result_eligible": False,
    "terminal_truth_class": "review_required_execution_closure",
    "terminal_state_class": "review_pending",
    "negative_feedback_class": "review_required",
}
report_path.write_text(json.dumps(report_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
active_pointer_path.write_text(
    json.dumps(
        {
            "run_id": report_doc["run_id"],
            "report_path": str(report_path),
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

POSTEXEC_JSON="${TMP_DIR}/postexec-repair.json"
CONTRACT_JSON="${TMP_DIR}/contract-backfill.json"
TERMINAL_JSON="${TMP_DIR}/terminal-truth.json"

python3 scripts/repair_identity_post_execution_mandatory.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --apply \
  --json-only > "${POSTEXEC_JSON}"

python3 scripts/repair_contract_backfill.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --apply \
  --json-only > "${CONTRACT_JSON}" || true

python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REPORT_PATH}" \
  --operation readiness \
  --json-only > "${TERMINAL_JSON}" || true

python3 - <<'PY' "${POSTEXEC_JSON}" "${CONTRACT_JSON}" "${TERMINAL_JSON}"
import json
import sys
from pathlib import Path

postexec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
contract = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
terminal = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
terminal_projection = contract.get("current_run_terminal_truth_projection_backfill") or {}

assert postexec["post_execution_report_repair_status"] == "PASS_REQUIRED", postexec
assert postexec["repair_blocking_status"] == "PASS_REQUIRED", postexec
assert postexec["repair_observation_status"] == "WARN_NON_BLOCKING", postexec
assert postexec["terminal_truth_validation_status_after"] == "FAIL_REQUIRED", postexec
assert postexec["terminal_truth_class_after"] == "review_required_execution_closure", postexec
assert postexec["terminal_state_class_after"] == "review_pending", postexec
assert postexec["publishable_after"] is False, postexec
assert postexec["canonical_result_eligible_after"] is False, postexec
assert "terminal_truth_validator_not_green_after_projection" in (
    postexec.get("observation_stale_reasons") or []
), postexec

assert contract["contract_backfill_status"] == "PASS_REQUIRED", contract
assert contract["error_code"] == "", contract
assert terminal_projection["current_run_terminal_truth_projection_status"] == "PASS_REQUIRED", contract
assert terminal_projection["active_run_present"] is True, contract
assert terminal_projection["repair_projection_status"] == "PASS_REQUIRED", contract
assert terminal_projection["terminal_truth_status"] == "FAIL_REQUIRED", contract
assert terminal_projection["terminal_truth_class"] == "review_required_execution_closure", contract
assert "terminal_truth_validator_not_green_after_projection" in (
    terminal_projection.get("observation_stale_reasons") or []
), contract
assert "current_run_terminal_truth_projection_failed" not in (
    contract.get("current_run_projection_blocking_failures") or []
), contract
assert "current_run_terminal_truth_projection_failed" not in (contract.get("stale_reasons") or []), contract

assert terminal["identity_terminal_truth_cleanliness_status"] == "FAIL_REQUIRED", terminal
assert terminal["execution_closure_status"] == "PASS_REQUIRED", terminal
assert terminal["report_selection_mode"] == "explicit_report_override", terminal
assert terminal["report_selected_authority_class"] == "explicit_report_override", terminal
assert terminal["terminal_truth_class"] == "review_required_execution_closure", terminal
PY

echo "[PASS] identity update preflight terminal-truth split probes passed"
