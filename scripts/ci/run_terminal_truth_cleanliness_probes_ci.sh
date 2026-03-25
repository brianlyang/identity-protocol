#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/terminal-truth-cleanliness.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

IDENTITY_ID="terminal-truth-probe"
PACK_ROOT="${TMP_ROOT}/${IDENTITY_ID}"
REPORT_ROOT="${PACK_ROOT}/runtime/reports"
mkdir -p "${REPORT_ROOT}"

python3 - <<'PY' "${PACK_ROOT}" "${IDENTITY_ID}" "${TMP_ROOT}/catalog.local.yaml"
import json
import sys
from pathlib import Path

pack_root = Path(sys.argv[1])
identity_id = sys.argv[2]
catalog_path = Path(sys.argv[3])
sys.path.insert(0, str(Path('scripts').resolve()))
from terminal_truth_cleanliness_common import terminal_truth_cleanliness_contract_skeleton

task = {
    "identity_id": identity_id,
    "meta": {"version": "v1.6.21"},
    "objective": {"status": "active"},
    "gates": {"identity_update_gate": "required"},
    "post_execution_mandatory": ["update objective.status"],
    "writeback_continuity_contract_v1": {"required": True},
    "experience_feedback_contract": {"required": True},
    "prompt_bootstrap_capability_contract_v1": {"required": True},
    "identity_artifact_family_routing_contract_v1": {"required": True},
    "identity_terminal_truth_cleanliness_contract_v1": terminal_truth_cleanliness_contract_skeleton(),
}
(pack_root / 'CURRENT_TASK.json').write_text(json.dumps(task, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
catalog = {
    "identities": [
        {
            "id": identity_id,
            "pack_path": str(pack_root.resolve()),
            "runtime_mode": "standard",
        }
    ]
}
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

clean_report = {
    "run_id": "terminal-truth-clean-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": False,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "NOT_REQUIRED",
    "next_action": "no_upgrade_triggered",
    "degrade_reason": "",
    "next_recovery_action": "",
    "artifacts": [],
}
review_required_report = {
    "run_id": "terminal-truth-review-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": True,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "WRITTEN",
    "next_action": "review_required_create_pr_from_patch_plan",
    "degrade_reason": "",
    "next_recovery_action": "",
    "artifacts": ["/tmp/patch-plan.json"],
}
degraded_report = {
    "run_id": "terminal-truth-degraded-run",
    "identity_id": identity_id,
    "all_ok": False,
    "upgrade_required": False,
    "writeback_mode": "DEGRADED_WRITEBACK",
    "writeback_status": "DEFERRED_VALIDATION_FAILED",
    "next_action": "rerun_with_deterministic_lane_instance_or_protocol",
    "degrade_reason": "validator_failure_before_writeback",
    "next_recovery_action": "rerun_with_deterministic_lane_instance_or_protocol",
    "artifacts": [],
}
placeholder_report = {
    "run_id": "terminal-truth-placeholder-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": False,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "NOT_REQUIRED",
    "next_action": "publish_placeholder_result_blocked",
    "degrade_reason": "",
    "next_recovery_action": "",
    "final_report": "placeholder final report",
    "artifacts": [],
}
conflict_report = {
    "run_id": "terminal-truth-conflict-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": True,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "WRITTEN",
    "next_action": "review_required_create_pr_from_patch_plan",
    "degrade_reason": "",
    "next_recovery_action": "",
    "is_terminal_clean": True,
    "publishable": True,
    "canonical_result_eligible": True,
    "terminal_state_class": "completed_clean",
    "artifacts": ["/tmp/patch-plan.json"],
}
alias_conflict_report = {
    "run_id": "terminal-truth-alias-conflict-run",
    "identity_id": identity_id,
    "all_ok": False,
    "upgrade_required": False,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "MISSING",
    "next_action": "satisfy_pre_mutation_gate_and_rerun_update",
    "degrade_reason": "",
    "next_recovery_action": "",
    "status": "completed",
    "done": True,
    "artifacts": [],
}
(report_root := pack_root / 'runtime' / 'reports').mkdir(parents=True, exist_ok=True)
for name, doc in {
    'identity-upgrade-exec-terminal-truth-clean-run.json': clean_report,
    'identity-upgrade-exec-terminal-truth-review-run.json': review_required_report,
    'identity-upgrade-exec-terminal-truth-degraded-run.json': degraded_report,
    'identity-upgrade-exec-terminal-truth-placeholder-run.json': placeholder_report,
    'identity-upgrade-exec-terminal-truth-conflict-run.json': conflict_report,
    'identity-upgrade-exec-terminal-truth-alias-conflict-run.json': alias_conflict_report,
}.items():
    (report_root / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY

CLEAN_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-clean-run.json"
REVIEW_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-review-run.json"
DEGRADED_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-degraded-run.json"
PLACEHOLDER_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-placeholder-run.json"
CONFLICT_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-conflict-run.json"
ALIAS_CONFLICT_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-alias-conflict-run.json"

printf '[RUN] clean fixture\n'
python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${CLEAN_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/clean.json"

printf '[RUN] review-required fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${REVIEW_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/review.json"; then
  echo '[FAIL] review-required fixture must fail clean terminal truth gate'
  exit 1
fi

printf '[RUN] degraded fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${DEGRADED_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/degraded.json"; then
  echo '[FAIL] degraded fixture must fail clean terminal truth gate'
  exit 1
fi

printf '[RUN] placeholder fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${PLACEHOLDER_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/placeholder.json"; then
  echo '[FAIL] placeholder fixture must fail clean terminal truth gate'
  exit 1
fi

printf '[RUN] conflict fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${CONFLICT_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/conflict.json"; then
  echo '[FAIL] conflict fixture must fail clean terminal truth gate'
  exit 1
fi

printf '[RUN] alias-conflict fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${ALIAS_CONFLICT_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/alias_conflict.json"; then
  echo '[FAIL] alias-conflict fixture must fail clean terminal truth gate'
  exit 1
fi

python3 - <<'PY' "${TMP_ROOT}/clean.json" "${TMP_ROOT}/review.json" "${TMP_ROOT}/degraded.json" "${TMP_ROOT}/placeholder.json" "${TMP_ROOT}/conflict.json" "${TMP_ROOT}/alias_conflict.json"
import json
import sys
from pathlib import Path

clean = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
review = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
degraded = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
placeholder = json.loads(Path(sys.argv[4]).read_text(encoding='utf-8'))
conflict = json.loads(Path(sys.argv[5]).read_text(encoding='utf-8'))
alias_conflict = json.loads(Path(sys.argv[6]).read_text(encoding='utf-8'))

if clean.get('identity_terminal_truth_cleanliness_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture top-level status must PASS_REQUIRED')
if clean.get('terminal_truth_class') != 'clean_terminal_truth':
    raise SystemExit('clean fixture terminal_truth_class must be clean_terminal_truth')
if clean.get('publishable') is not True or clean.get('canonical_result_eligible') is not True:
    raise SystemExit('clean fixture must be publishable and canonical-result eligible')
if clean.get('negative_feedback_terminal_veto_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture veto status must PASS_REQUIRED')
if clean.get('terminal_state_machine_status') != 'PASS_REQUIRED' or clean.get('terminal_state_class') != 'completed_clean':
    raise SystemExit('clean fixture terminal state machine must classify as completed_clean')

if review.get('execution_closure_status') != 'PASS_REQUIRED':
    raise SystemExit('review-required fixture must preserve execution closure status')
if review.get('terminal_truth_cleanliness_status') != 'FAIL_REQUIRED':
    raise SystemExit('review-required fixture must fail clean terminal truth status')
if review.get('terminal_truth_class') != 'review_required_execution_closure':
    raise SystemExit('review-required fixture class must remain review_required_execution_closure')
if review.get('negative_feedback_terminal_veto_status') != 'PASS_REQUIRED':
    raise SystemExit('review-required fixture veto semantics must PASS_REQUIRED')
if review.get('publishable') is not False:
    raise SystemExit('review-required fixture must not be publishable')
if review.get('terminal_state_machine_status') != 'PASS_REQUIRED' or review.get('terminal_state_class') != 'review_pending':
    raise SystemExit('review-required fixture terminal state machine must classify as review_pending')
if review.get('requires_review') is not True or review.get('requires_human') is not True:
    raise SystemExit('review-required fixture must require review and human participation')

if degraded.get('execution_closure_status') != 'FAIL_REQUIRED':
    raise SystemExit('degraded fixture must fail execution closure status')
if degraded.get('negative_feedback_class') != 'degraded_execution':
    raise SystemExit('degraded fixture negative_feedback_class must be degraded_execution')
if degraded.get('negative_feedback_terminal_veto_status') != 'PASS_REQUIRED':
    raise SystemExit('degraded fixture veto semantics must PASS_REQUIRED even when execution closure is not reached')
if degraded.get('terminal_veto_required') is not False:
    raise SystemExit('degraded fixture must not claim terminal veto applied before execution closure exists')
if degraded.get('loopback_required') is not True:
    raise SystemExit('degraded fixture must require loopback')
if degraded.get('next_state_after_veto') != 'revalidation_pending':
    raise SystemExit('degraded fixture next_state_after_veto must be revalidation_pending')
if degraded.get('terminal_state_machine_status') != 'PASS_REQUIRED' or degraded.get('terminal_state_class') != 'revalidation_pending':
    raise SystemExit('degraded fixture terminal state machine must classify as revalidation_pending')
if degraded.get('revalidation_required') is not True:
    raise SystemExit('degraded fixture must require revalidation')

if placeholder.get('negative_feedback_class') != 'placeholder_result':
    raise SystemExit('placeholder fixture negative_feedback_class must be placeholder_result')
if placeholder.get('terminal_state_machine_status') != 'PASS_REQUIRED' or placeholder.get('terminal_state_class') != 'repair_pending':
    raise SystemExit('placeholder fixture terminal state machine must classify as repair_pending')
if placeholder.get('repair_required') is not True:
    raise SystemExit('placeholder fixture must require repair')

if conflict.get('terminal_state_machine_status') != 'FAIL_REQUIRED':
    raise SystemExit('conflict fixture terminal state machine must fail-close')
if conflict.get('terminal_state_conflict_status') != 'PASS_REQUIRED':
    raise SystemExit('conflict fixture should fail via adoption mismatch, not semantic-state incoherence')
if 'report_terminal_state_class_projection_mismatch' not in set(conflict.get('state_machine_blockers') or []):
    raise SystemExit('conflict fixture must expose terminal_state_class projection mismatch blocker')

if alias_conflict.get('terminal_clean_alias_surface_status') != 'FAIL_REQUIRED':
    raise SystemExit('alias-conflict fixture must fail clean-alias surface status')
if alias_conflict.get('terminal_clean_alias_claimed') is not True:
    raise SystemExit('alias-conflict fixture must record a clean-terminal alias claim')
if 'report_terminal_clean_alias_claimed_while_not_clean' not in set(alias_conflict.get('terminal_clean_alias_blockers') or []):
    raise SystemExit('alias-conflict fixture must expose clean-terminal alias drift blocker')
if alias_conflict.get('instance_adoption_terminal_truth_probe_status') != 'FAIL_REQUIRED':
    raise SystemExit('alias-conflict fixture must fail instance adoption terminal-truth probe status')
PY

echo "[PASS] terminal truth cleanliness probes passed"
