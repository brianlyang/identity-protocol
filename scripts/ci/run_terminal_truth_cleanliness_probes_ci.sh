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
explicit_review_flag_report = {
    "run_id": "terminal-truth-explicit-review-flag-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": True,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "WRITTEN",
    "next_action": "publish_ready_if_clean",
    "review_required": True,
    "requires_human": True,
    "degrade_reason": "",
    "next_recovery_action": "",
    "artifacts": ["/tmp/manual-review-required.json"],
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
explicit_dirty_retry_report = {
    "run_id": "terminal-truth-explicit-dirty-retry-run",
    "identity_id": identity_id,
    "all_ok": True,
    "upgrade_required": True,
    "writeback_mode": "STRICT_WRITEBACK",
    "writeback_status": "WRITTEN",
    "next_action": "publish_ready_if_clean",
    "degrade_reason": "",
    "fallback_reason": "model_fallback_required_before_publish",
    "next_recovery_action": "",
    "needs_revalidation": True,
    "retry_required": True,
    "error_info": {"code": "retry_needed_after_fallback", "status": "degraded"},
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
(state_root := pack_root / 'runtime' / 'state').mkdir(parents=True, exist_ok=True)
for name, doc in {
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-clean-run.json': clean_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-review-run.json': review_required_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-explicit-review-flag-run.json': explicit_review_flag_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-degraded-run.json': degraded_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-explicit-dirty-retry-run.json': explicit_dirty_retry_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-placeholder-run.json': placeholder_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-conflict-run.json': conflict_report,
    'identity-upgrade-exec-terminal-truth-probe-terminal-truth-alias-conflict-run.json': alias_conflict_report,
}.items():
    (report_root / name).write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(state_root / 'active_execution_report.json').write_text(
    json.dumps(
        {
            'run_id': 'terminal-truth-clean-run',
            'report_path': str((report_root / 'identity-upgrade-exec-terminal-truth-probe-terminal-truth-clean-run.json').resolve()),
        },
        ensure_ascii=False,
        indent=2,
    )
    + '\n',
    encoding='utf-8',
)
PY

CLEAN_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-clean-run.json"
REVIEW_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-review-run.json"
EXPLICIT_REVIEW_FLAG_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-explicit-review-flag-run.json"
DEGRADED_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-degraded-run.json"
EXPLICIT_DIRTY_RETRY_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-explicit-dirty-retry-run.json"
PLACEHOLDER_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-placeholder-run.json"
CONFLICT_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-conflict-run.json"
ALIAS_CONFLICT_REPORT="${REPORT_ROOT}/identity-upgrade-exec-terminal-truth-probe-terminal-truth-alias-conflict-run.json"

printf '[RUN] clean fixture\n'
python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${CLEAN_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/clean.json"

printf '[RUN] clean auto-selection fixture\n'
python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/clean_auto.json"

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

printf '[RUN] explicit-review-flag fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${EXPLICIT_REVIEW_FLAG_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/explicit_review_flag.json"; then
  echo '[FAIL] explicit-review-flag fixture must fail clean terminal truth gate'
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

printf '[RUN] explicit-dirty-retry fixture\n'
if python3 scripts/validate_terminal_truth_cleanliness.py \
  --catalog "${TMP_ROOT}/catalog.local.yaml" \
  --identity-id "${IDENTITY_ID}" \
  --report "${EXPLICIT_DIRTY_RETRY_REPORT}" \
  --skip-support-validators \
  --json-only > "${TMP_ROOT}/explicit_dirty_retry.json"; then
  echo '[FAIL] explicit-dirty-retry fixture must fail clean terminal truth gate'
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

python3 - <<'PY' "${TMP_ROOT}/clean.json" "${TMP_ROOT}/clean_auto.json" "${TMP_ROOT}/review.json" "${TMP_ROOT}/explicit_review_flag.json" "${TMP_ROOT}/degraded.json" "${TMP_ROOT}/explicit_dirty_retry.json" "${TMP_ROOT}/placeholder.json" "${TMP_ROOT}/conflict.json" "${TMP_ROOT}/alias_conflict.json" "${CLEAN_REPORT}"
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path('scripts').resolve()))
from release_readiness_active_runtime_closure_projection_common import (
    apply_release_readiness_active_runtime_closure_one_look,
)

clean = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
clean_auto = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
review = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
explicit_review = json.loads(Path(sys.argv[4]).read_text(encoding='utf-8'))
degraded = json.loads(Path(sys.argv[5]).read_text(encoding='utf-8'))
explicit_dirty_retry = json.loads(Path(sys.argv[6]).read_text(encoding='utf-8'))
placeholder = json.loads(Path(sys.argv[7]).read_text(encoding='utf-8'))
conflict = json.loads(Path(sys.argv[8]).read_text(encoding='utf-8'))
alias_conflict = json.loads(Path(sys.argv[9]).read_text(encoding='utf-8'))
clean_report_path = str(Path(sys.argv[10]).resolve())


def build_terminal_truth_one_look(payload: dict) -> dict:
    summary = {
        'identity_terminal_truth_cleanliness': {
            'status': payload.get('identity_terminal_truth_cleanliness_status', ''),
            'execution_closure_status': payload.get('execution_closure_status', ''),
            'canonical_publishable_result_status': payload.get('canonical_publishable_result_status', ''),
            'terminal_truth_class': payload.get('terminal_truth_class', ''),
            'terminal_state_machine_status': payload.get('terminal_state_machine_status', ''),
            'terminal_state_class': payload.get('terminal_state_class', ''),
            'negative_feedback_class': payload.get('negative_feedback_class', ''),
            'loopback_required': payload.get('loopback_required', False),
            'publishable': payload.get('publishable', False),
            'next_state_after_veto': payload.get('next_state_after_veto', ''),
            'terminal_clean_alias_surface_status': payload.get('terminal_clean_alias_surface_status', ''),
        }
    }
    one_look = {}
    apply_release_readiness_active_runtime_closure_one_look(summary, one_look)
    return one_look

if clean.get('identity_terminal_truth_cleanliness_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture top-level status must PASS_REQUIRED')
if clean.get('report_selection_mode') != 'explicit_report_override':
    raise SystemExit('clean fixture report_selection_mode must be explicit_report_override')
if clean.get('report_selected_authority_class') != 'explicit_report_override':
    raise SystemExit('clean fixture report_selected_authority_class must be explicit_report_override')
if clean.get('report_pointer_resolution_mode') != 'explicit_report_override':
    raise SystemExit('clean fixture report_pointer_resolution_mode must be explicit_report_override')
if clean.get('terminal_truth_class') != 'clean_terminal_truth':
    raise SystemExit('clean fixture terminal_truth_class must be clean_terminal_truth')
if clean.get('publishable') is not True or clean.get('canonical_result_eligible') is not True:
    raise SystemExit('clean fixture must be publishable and canonical-result eligible')
if clean.get('negative_feedback_terminal_veto_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture veto status must PASS_REQUIRED')
if clean.get('terminal_state_machine_status') != 'PASS_REQUIRED' or clean.get('terminal_state_class') != 'completed_clean':
    raise SystemExit('clean fixture terminal state machine must classify as completed_clean')

if clean_auto.get('identity_terminal_truth_cleanliness_status') != 'PASS_REQUIRED':
    raise SystemExit('clean auto-selection fixture top-level status must PASS_REQUIRED')
if clean_auto.get('report_selected_path') != clean_report_path:
    raise SystemExit('clean auto-selection fixture must select the active pointer report')
if clean_auto.get('report_selection_mode') != 'active_execution_pointer':
    raise SystemExit('clean auto-selection fixture report_selection_mode must be active_execution_pointer')
if clean_auto.get('report_selected_authority_class') != 'active_execution_pointer_pack_local_report':
    raise SystemExit('clean auto-selection fixture authority class must be active_execution_pointer_pack_local_report')
if clean_auto.get('report_pointer_resolution_mode') != 'pointer_candidate_root_report':
    raise SystemExit('clean auto-selection fixture pointer resolution mode must be pointer_candidate_root_report')

clean_one_look = build_terminal_truth_one_look(clean)
if clean_one_look.get('identity_terminal_truth_state_machine_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture one-look terminal_state_machine_status must be PASS_REQUIRED')
if clean_one_look.get('identity_terminal_truth_state_class') != 'completed_clean':
    raise SystemExit('clean fixture one-look terminal_state_class must be completed_clean')
if clean_one_look.get('identity_terminal_truth_negative_feedback_class') != 'none':
    raise SystemExit('clean fixture one-look negative_feedback_class must be none')
if clean_one_look.get('identity_terminal_truth_loopback_required') is not False:
    raise SystemExit('clean fixture one-look loopback_required must be false')
if clean_one_look.get('identity_terminal_truth_publishable') is not True:
    raise SystemExit('clean fixture one-look publishable must be true')
if clean_one_look.get('identity_terminal_truth_next_state_after_veto') != '':
    raise SystemExit('clean fixture one-look next_state_after_veto must stay empty')
if clean_one_look.get('identity_terminal_truth_alias_surface_status') != 'PASS_REQUIRED':
    raise SystemExit('clean fixture one-look alias surface status must be PASS_REQUIRED')

if review.get('execution_closure_status') != 'PASS_REQUIRED':
    raise SystemExit('review-required fixture must preserve execution closure status')
if review.get('report_selection_mode') != 'explicit_report_override':
    raise SystemExit('review-required fixture report_selection_mode must be explicit_report_override')
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

review_one_look = build_terminal_truth_one_look(review)
if review_one_look.get('identity_terminal_truth_state_machine_status') != 'PASS_REQUIRED':
    raise SystemExit('review-required fixture one-look terminal_state_machine_status must be PASS_REQUIRED')
if review_one_look.get('identity_terminal_truth_state_class') != 'review_pending':
    raise SystemExit('review-required fixture one-look terminal_state_class must be review_pending')
if review_one_look.get('identity_terminal_truth_negative_feedback_class') != 'review_required':
    raise SystemExit('review-required fixture one-look negative_feedback_class must be review_required')
if review_one_look.get('identity_terminal_truth_loopback_required') is not False:
    raise SystemExit('review-required fixture one-look loopback_required must stay false')
if review_one_look.get('identity_terminal_truth_publishable') is not False:
    raise SystemExit('review-required fixture one-look publishable must be false')
if review_one_look.get('identity_terminal_truth_next_state_after_veto') != 'review_pending':
    raise SystemExit('review-required fixture one-look next_state_after_veto must be review_pending')
if review_one_look.get('identity_terminal_truth_alias_surface_status') != 'PASS_REQUIRED':
    raise SystemExit('review-required fixture one-look alias surface status must be PASS_REQUIRED')

if explicit_review.get('execution_closure_status') != 'PASS_REQUIRED':
    raise SystemExit('explicit-review-flag fixture must preserve execution closure status')
if explicit_review.get('negative_feedback_class') != 'review_required':
    raise SystemExit('explicit-review-flag fixture negative_feedback_class must be review_required')
if explicit_review.get('terminal_truth_class') != 'review_required_execution_closure':
    raise SystemExit('explicit-review-flag fixture class must remain review_required_execution_closure')
if explicit_review.get('terminal_state_machine_status') != 'PASS_REQUIRED' or explicit_review.get('terminal_state_class') != 'review_pending':
    raise SystemExit('explicit-review-flag fixture terminal state machine must classify as review_pending')
if explicit_review.get('terminal_veto_required') is not True:
    raise SystemExit('explicit-review-flag fixture must require terminal veto')
if explicit_review.get('publishable') is not False:
    raise SystemExit('explicit-review-flag fixture must not be publishable')
if explicit_review.get('loopback_required') is not False or explicit_review.get('next_state_after_veto') != 'review_pending':
    raise SystemExit('explicit-review-flag fixture must stay on review_pending without loopback')
if 'review_required_flag' not in set(explicit_review.get('dirty_signals') or []):
    raise SystemExit('explicit-review-flag fixture must expose review_required_flag dirty signal')

if degraded.get('execution_closure_status') != 'FAIL_REQUIRED':
    raise SystemExit('degraded fixture must fail execution closure status')
if degraded.get('report_selection_mode') != 'explicit_report_override':
    raise SystemExit('degraded fixture report_selection_mode must be explicit_report_override')
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

degraded_one_look = build_terminal_truth_one_look(degraded)
if degraded_one_look.get('identity_terminal_truth_state_machine_status') != 'PASS_REQUIRED':
    raise SystemExit('degraded fixture one-look terminal_state_machine_status must be PASS_REQUIRED')
if degraded_one_look.get('identity_terminal_truth_state_class') != 'revalidation_pending':
    raise SystemExit('degraded fixture one-look terminal_state_class must be revalidation_pending')
if degraded_one_look.get('identity_terminal_truth_negative_feedback_class') != 'degraded_execution':
    raise SystemExit('degraded fixture one-look negative_feedback_class must be degraded_execution')
if degraded_one_look.get('identity_terminal_truth_loopback_required') is not True:
    raise SystemExit('degraded fixture one-look loopback_required must be true')
if degraded_one_look.get('identity_terminal_truth_publishable') is not False:
    raise SystemExit('degraded fixture one-look publishable must be false')
if degraded_one_look.get('identity_terminal_truth_next_state_after_veto') != 'revalidation_pending':
    raise SystemExit('degraded fixture one-look next_state_after_veto must be revalidation_pending')
if degraded_one_look.get('identity_terminal_truth_alias_surface_status') != 'PASS_REQUIRED':
    raise SystemExit('degraded fixture one-look alias surface status must be PASS_REQUIRED')

if explicit_dirty_retry.get('execution_closure_status') != 'PASS_REQUIRED':
    raise SystemExit('explicit-dirty-retry fixture must preserve execution closure status')
if explicit_dirty_retry.get('negative_feedback_class') != 'degraded_execution':
    raise SystemExit('explicit-dirty-retry fixture negative_feedback_class must be degraded_execution')
if explicit_dirty_retry.get('negative_feedback_terminal_veto_status') != 'PASS_REQUIRED':
    raise SystemExit('explicit-dirty-retry fixture veto semantics must PASS_REQUIRED')
if explicit_dirty_retry.get('terminal_veto_required') is not True:
    raise SystemExit('explicit-dirty-retry fixture must require terminal veto')
if explicit_dirty_retry.get('loopback_required') is not True:
    raise SystemExit('explicit-dirty-retry fixture must require loopback')
if explicit_dirty_retry.get('next_state_after_veto') != 'retry_pending':
    raise SystemExit('explicit-dirty-retry fixture next_state_after_veto must be retry_pending')
if explicit_dirty_retry.get('terminal_state_machine_status') != 'PASS_REQUIRED' or explicit_dirty_retry.get('terminal_state_class') != 'retry_pending':
    raise SystemExit('explicit-dirty-retry fixture terminal state machine must classify as retry_pending')
if explicit_dirty_retry.get('retry_required') is not True:
    raise SystemExit('explicit-dirty-retry fixture must require retry')
if explicit_dirty_retry.get('publishable') is not False:
    raise SystemExit('explicit-dirty-retry fixture must not be publishable')
dirty_retry_signals = set(explicit_dirty_retry.get('dirty_signals') or [])
for required_signal in {'fallback_reason_present', 'explicit_revalidation_required', 'explicit_retry_required', 'error_info_dirty_signal'}:
    if required_signal not in dirty_retry_signals:
        raise SystemExit(f'explicit-dirty-retry fixture missing dirty signal: {required_signal}')

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

alias_one_look = build_terminal_truth_one_look(alias_conflict)
if alias_one_look.get('identity_terminal_truth_alias_surface_status') != 'FAIL_REQUIRED':
    raise SystemExit('alias-conflict fixture one-look alias surface status must be FAIL_REQUIRED')
if alias_one_look.get('identity_terminal_truth_publishable') is not False:
    raise SystemExit('alias-conflict fixture one-look publishable must be false')
PY

echo "[PASS] terminal truth cleanliness probes passed"
