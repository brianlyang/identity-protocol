#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/identity-health-report-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
OUT_DIR="${TMP_DIR}/out"
PASS_ID="probe-health-pass"
SKIP_ID="probe-health-skip"
PASS_PACK="${TMP_DIR}/${PASS_ID}"
SKIP_PACK="${TMP_DIR}/${SKIP_ID}"
PASS_REPORT="${PASS_PACK}/runtime/reports/identity-upgrade-exec-${PASS_ID}-green.json"

mkdir -p "${OUT_DIR}"

python3 - <<'PY' "${CATALOG_PATH}" "${PASS_ID}" "${SKIP_ID}" "${PASS_PACK}" "${SKIP_PACK}" "${PASS_REPORT}"
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
pass_id = sys.argv[2]
skip_id = sys.argv[3]
pass_pack = Path(sys.argv[4]).resolve()
skip_pack = Path(sys.argv[5]).resolve()
pass_report = Path(sys.argv[6]).resolve()


def seed_pack(identity_id: str, pack_path: Path) -> tuple[Path, Path, Path]:
    reports_dir = pack_path / "runtime" / "reports"
    state_dir = pack_path / "runtime" / "state"
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    rulebook_path = (pack_path / "RULEBOOK.jsonl").resolve()
    task_history_path = (pack_path / "TASK_HISTORY.md").resolve()
    prompt_contract_path = (state_dir / "prompt_contract.json").resolve()
    prompt_path = (pack_path / "IDENTITY_PROMPT.md").resolve()

    blockers = list(CANONICAL_BLOCKER_TYPES)
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
        "writeback_continuity_contract_v1": {"required": True},
        "identity_terminal_truth_cleanliness_contract_v1": terminal_truth_cleanliness_contract_skeleton(),
        "blocker_taxonomy_contract": {
            "required": True,
            "required_blocker_types": blockers,
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
            "human_collab_blockers": blockers,
        },
    }
    task_doc["collaboration_trigger_contract"]["trigger_conditions"] = blockers
    (pack_path / "CURRENT_TASK.json").write_text(
        json.dumps(task_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    prompt_path.write_text(f"# {identity_id}\n\nHealth report probe prompt.\n", encoding="utf-8")
    prompt_contract_path.write_text("{}\n", encoding="utf-8")
    rulebook_path.write_text("", encoding="utf-8")
    task_history_path.write_text("# Task History\n", encoding="utf-8")
    return rulebook_path, task_history_path, prompt_contract_path


pass_rulebook, pass_history, pass_prompt_contract = seed_pack(pass_id, pass_pack)
seed_pack(skip_id, skip_pack)

catalog_doc = {
    "default_identity": pass_id,
    "identities": [
        {
            "id": pass_id,
            "pack_path": str(pass_pack),
            "scope": "USER",
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
        },
        {
            "id": skip_id,
            "pack_path": str(skip_pack),
            "scope": "USER",
            "status": "active",
            "profile": "runtime",
            "runtime_mode": "local_only",
        },
    ],
}
catalog_path.write_text(yaml.safe_dump(catalog_doc, sort_keys=False, allow_unicode=True), encoding="utf-8")

run_id = f"identity-upgrade-exec-{pass_id}-green"
pass_rulebook.write_text(
    json.dumps(
        {
            "rule_entry_id": "rule-entry-health-pass",
            "evidence_run_id": run_id,
            "summary": "health report pass linkage",
        },
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
pass_history.write_text(
    "# Task History\n\n"
    f"- run_id={run_id} writeback completed\n",
    encoding="utf-8",
)
pass_report.write_text(
    json.dumps(
        {
            "identity_id": pass_id,
            "run_id": run_id,
            "generated_at": "2026-03-27T00:00:00Z",
            "catalog_path": str(catalog_path),
            "resolved_pack_path": str(pass_pack),
            "all_ok": True,
            "upgrade_required": True,
            "permission_state": "WRITEBACK_WRITTEN",
            "writeback_status": "WRITTEN",
            "writeback_mode": "STRICT_WRITEBACK",
            "next_action": "no_upgrade_triggered",
            "next_recovery_action": "",
            "phase_a_refresh_applied": False,
            "phase_b_strict_revalidate_status": "PASS_REQUIRED",
            "phase_transition_reason": "",
            "phase_transition_error_code": "",
            "governed_outlet_enforced": True,
            "outlet_channel_id": "final_emit_governed",
            "outlet_preflight_receipt": str((pass_pack / "runtime" / "reports" / "outlet-preflight.json").resolve()),
            "outlet_bypass_detected": False,
            "final_emit_channel_id": "final_emit_governed",
            "final_emit_policy_mode": "tool_choice_required",
            "final_emit_schema_id": "hud_headstamp_final_emit_schema_v1",
            "final_emit_schema_status": "PASS_REQUIRED",
            "final_emit_contract_status": "PASS_REQUIRED",
            "experience_writeback": {
                "required": True,
                "status": "WRITTEN",
                "error_code": "",
                "mode": "safe-auto",
            },
            "writeback_paths": [
                str(pass_rulebook),
                str(pass_history),
                str(pass_prompt_contract),
            ],
            "writeback_rule_id": "rule-entry-health-pass",
            "artifacts": [],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(pass_pack / "runtime" / "reports" / "outlet-preflight.json").write_text(
    json.dumps({"status": "PASS_REQUIRED", "identity_id": pass_id}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

PASS_STDOUT="$(python3 scripts/collect_identity_health_report.py \
  --identity-id "${PASS_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --operation scan \
  --execution-report "${PASS_REPORT}" \
  --out-dir "${OUT_DIR}")"
PASS_REPORT_PATH="$(printf '%s\n' "${PASS_STDOUT}" | awk -F= '/^report=/{print $2}' | tail -n 1)"
test -n "${PASS_REPORT_PATH}"
python3 scripts/validate_identity_health_contract.py --identity-id "${PASS_ID}" --report "${PASS_REPORT_PATH}"

SKIP_STDOUT="$(python3 scripts/collect_identity_health_report.py \
  --identity-id "${SKIP_ID}" \
  --catalog "${CATALOG_PATH}" \
  --repo-catalog "${CATALOG_PATH}" \
  --operation scan \
  --out-dir "${OUT_DIR}")"
SKIP_REPORT_PATH="$(printf '%s\n' "${SKIP_STDOUT}" | awk -F= '/^report=/{print $2}' | tail -n 1)"
test -n "${SKIP_REPORT_PATH}"
python3 scripts/validate_identity_health_contract.py --identity-id "${SKIP_ID}" --report "${SKIP_REPORT_PATH}"

TAMPERED_REPORT_PATH="${OUT_DIR}/identity-health-${PASS_ID}-tampered.json"
python3 - <<'PY' "${PASS_REPORT_PATH}" "${TAMPERED_REPORT_PATH}"
import json
import sys
from pathlib import Path

src = Path(sys.argv[1]).resolve()
dst = Path(sys.argv[2]).resolve()
doc = json.loads(src.read_text(encoding="utf-8"))
closure = doc.get("experience_writeback_closure") or {}
closure["report_selected_path"] = "/tmp/tampered-report.json"
doc["experience_writeback_closure"] = closure
dst.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

if python3 scripts/validate_identity_health_contract.py --identity-id "${PASS_ID}" --report "${TAMPERED_REPORT_PATH}" >/tmp/identity-health-tampered.out 2>/tmp/identity-health-tampered.err; then
  echo "[FAIL] tampered health report unexpectedly passed contract validation"
  cat /tmp/identity-health-tampered.out
  cat /tmp/identity-health-tampered.err
  exit 1
fi
grep -q 'experience_writeback_closure projection mismatch' /tmp/identity-health-tampered.out

python3 - <<'PY' "${PASS_REPORT_PATH}" "${SKIP_REPORT_PATH}" "${PASS_REPORT}"
import json
import sys
from pathlib import Path

pass_report_path = Path(sys.argv[1]).resolve()
skip_report_path = Path(sys.argv[2]).resolve()
explicit_execution_report = str(Path(sys.argv[3]).resolve())

pass_doc = json.loads(pass_report_path.read_text(encoding="utf-8"))
skip_doc = json.loads(skip_report_path.read_text(encoding="utf-8"))

pass_check = next((row for row in pass_doc.get("checks", []) if row.get("name") == "experience_writeback"), None)
skip_check = next((row for row in skip_doc.get("checks", []) if row.get("name") == "experience_writeback"), None)
assert isinstance(pass_check, dict), pass_doc
assert isinstance(skip_check, dict), skip_doc

pass_closure = pass_doc.get("experience_writeback_closure") or {}
skip_closure = skip_doc.get("experience_writeback_closure") or {}

assert pass_closure.get("status") == "PASS", pass_closure
assert pass_closure.get("validation_status") == "PASS_REQUIRED", pass_closure
assert pass_closure.get("report_selected_path") == explicit_execution_report, pass_closure
assert str(pass_closure.get("report_run_id", "")).startswith("identity-upgrade-exec-probe-health-pass-"), pass_closure
assert pass_closure.get("writeback_status") == "WRITTEN", pass_closure
assert pass_closure.get("writeback_rule_id") == "rule-entry-health-pass", pass_closure
assert int(pass_closure.get("rulebook_match_count", 0)) == 1, pass_closure
assert bool(pass_closure.get("task_history_contains_run_id")) is True, pass_closure
assert pass_check.get("status") == "PASS", pass_check

assert skip_closure.get("status") == "PASS", skip_closure
assert skip_closure.get("validation_status") == "SKIPPED_NOT_REQUIRED", skip_closure
assert skip_closure.get("report_selected_path") == "", skip_closure
assert skip_closure.get("report_selection_mode") == "no_admissible_report", skip_closure
assert skip_closure.get("writeback_status") == "", skip_closure
assert "required_contract_not_applicable_no_current_round_evidence_source" in list(skip_closure.get("stale_reasons") or []), skip_closure
assert skip_check.get("status") == "PASS", skip_check

print(json.dumps({
    "identity_health_report_probe_status": "PASS_REQUIRED",
    "pass_report": str(pass_report_path),
    "skip_report": str(skip_report_path),
    "pass_experience_writeback_validation_status": pass_closure.get("validation_status"),
    "skip_experience_writeback_validation_status": skip_closure.get("validation_status"),
}, ensure_ascii=False))
PY

echo "[PASS] identity health report probes passed"
