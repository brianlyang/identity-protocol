#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/protocol-feedback-sidecar-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
PACK_PATH="${TMP_DIR}/sidecar-probe-identity"
REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-sidecar-probe-identity-123456.json"
REPORT_ALT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-sidecar-probe-identity-alt.json"
mkdir -p "${PACK_PATH}/runtime/reports"
printf '{}\n' > "${CATALOG_PATH}"
printf '{}\n' > "${REPORT_PATH}"
printf '{}\n' > "${REPORT_ALT_PATH}"

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${REPORT_PATH}" "${REPORT_ALT_PATH}"
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

repo_root = Path.cwd()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

import validate_protocol_feedback_sidecar_contract as target

catalog_path = Path(sys.argv[1]).resolve()
pack_path = Path(sys.argv[2]).resolve()
report_path = str(Path(sys.argv[3]).resolve())
report_alt_path = str(Path(sys.argv[4]).resolve())
task_path = (pack_path / "CURRENT_TASK.json").resolve()
task_path.write_text("{}", encoding="utf-8")

task_doc = {
    "protocol_feedback_sidecar_contract_v1": {
        "required": True,
        "default_mode": "non_blocking",
        "blocking_error_prefixes": ["IP-WRB-", "IP-SEM-", "IP-PFB-"],
        "escalation_policy": "p0_governance_boundary",
    }
}

base_activity = {
    "requiredization_current_round_linked": True,
    "requiredization_historical_activity_detected": False,
    "activity_correlation_status": "ACTIVITY_CORRELATED",
    "activity_correlation_key": "run:sidecar-probe",
    "activity_window_hours": 72.0,
    "current_round_anchor_utc": "2026-03-27T00:00:00Z",
    "activity_correlated_refs": [],
    "activity_unscoped_refs": [],
    "protocol_feedback_activity_refs": [],
    "activity_ignored_missing_correlation_key_refs": [],
    "activity_ignored_missing_anchor_refs": [],
    "activity_ignored_pre_round_refs": [],
    "activity_ignored_stale_refs": [],
    "protocol_feedback_activity_detected": True,
}

base_layer = {
    "resolved_work_layer": "instance",
    "resolved_source_layer": "project",
    "protocol_triggered": False,
    "protocol_trigger_reasons": [],
    "intent_source": "default",
    "intent_confidence": 1.0,
    "fallback_reason": "",
}

base_scope = {
    "required_contract": True,
    "auto_required_signal": False,
    "requiredization_scope_decision": "declared_required",
    "requiredization_scope_reason": "declared_required",
}


def validator_result(status_key: str, status: str, payload: dict) -> tuple[dict, dict]:
    result = {
        "rc": 0 if status != "FAIL_REQUIRED" else 1,
        "status": status,
        "error_code": str(payload.get("error_code", "")).strip(),
        "ok": status != "FAIL_REQUIRED",
        "stdout_tail": "",
        "stderr_tail": "",
        "payload": payload,
        "command": [],
    }
    return result, payload


def run_case(case_payloads: dict[str, tuple[str, dict]]) -> tuple[int, dict]:
    def fake_validator_payload(*, cmd: list[str], status_key: str, default_status: str):
        script_name = Path(cmd[1]).name
        if script_name == "validate_writeback_continuity.py":
            status, payload = case_payloads["writeback"]
        elif script_name == "validate_post_execution_mandatory.py":
            status, payload = case_payloads["post_execution"]
        elif script_name == "validate_semantic_routing_guard.py":
            status, payload = case_payloads["semantic"]
        elif script_name == "validate_vendor_namespace_separation.py":
            status, payload = case_payloads["namespace"]
        elif script_name == "validate_protocol_feedback_reply_channel.py":
            status, payload = case_payloads["reply_channel"]
        else:
            raise AssertionError(f"unexpected validator: {script_name}")
        payload = dict(payload)
        payload.setdefault(status_key, status)
        return validator_result(status_key, status, payload)

    argv = [
        "validate_protocol_feedback_sidecar_contract.py",
        "--catalog",
        str(catalog_path),
        "--identity-id",
        "sidecar-probe-identity",
        "--operation",
        "readiness",
        "--json-only",
    ]

    stdout = io.StringIO()
    with patch.object(sys, "argv", argv), \
        patch.object(target, "resolve_pack_and_task", return_value=(pack_path, task_path)), \
        patch.object(target, "load_json", return_value=task_doc), \
        patch.object(target, "resolve_layer_intent", return_value=base_layer), \
        patch.object(target, "should_seed_default_correlation_keys", return_value=False), \
        patch.object(target, "discover_default_correlation_keys", return_value={}), \
        patch.object(target, "build_correlation_keys", return_value=["run:sidecar-probe"]), \
        patch.object(target, "collect_protocol_feedback_activity", return_value=base_activity), \
        patch.object(target, "decide_requiredization_scope", return_value=base_scope), \
        patch.object(target, "_validator_payload", side_effect=fake_validator_payload), \
        redirect_stdout(stdout):
        rc = target.main()
    return rc, json.loads(stdout.getvalue())


positive_case = {
    "writeback": (
        "PASS_REQUIRED",
        {
            "required_contract": True,
            "report_selected_path": report_path,
            "report_selection_mode": "explicit_report_override",
            "report_selected_authority_class": "explicit_report_override",
            "report_pointer_resolution_mode": "explicit_report_override",
            "report_pointer_path": "",
            "writeback_mode": "STRICT_WRITEBACK",
            "writeback_status": "WRITTEN",
            "next_action": "patch_applied_and_writeback_completed",
            "next_recovery_action": "",
        },
    ),
    "post_execution": (
        "PASS_REQUIRED",
        {
            "required_contract": True,
            "report_selected_path": report_path,
            "report_selection_mode": "explicit_report_override",
            "report_selected_authority_class": "explicit_report_override",
            "report_pointer_resolution_mode": "explicit_report_override",
            "report_pointer_path": "",
            "experience_writeback_validation_status": "PASS_REQUIRED",
            "experience_writeback_error_code": "",
            "experience_writeback_report_selected_path": report_path,
            "experience_writeback_report_selection_mode": "explicit_report_override",
            "experience_writeback_report_selected_authority_class": "explicit_report_override",
            "experience_writeback_report_pointer_resolution_mode": "explicit_report_override",
            "experience_writeback_report_pointer_path": "",
            "writeback_mode": "STRICT_WRITEBACK",
            "writeback_status": "WRITTEN",
            "next_action": "patch_applied_and_writeback_completed",
            "next_recovery_action": "",
            "final_emit_channel_id": "final_emit_governed",
            "final_emit_policy_mode": "tool_choice_required",
            "final_emit_schema_id": "hud_headstamp_final_emit_schema_v1",
            "final_emit_schema_status": "PASS_REQUIRED",
            "final_emit_contract_status": "PASS_REQUIRED",
        },
    ),
    "semantic": ("PASS_REQUIRED", {"required_contract": True}),
    "namespace": ("PASS_REQUIRED", {"required_contract": True}),
    "reply_channel": ("PASS_REQUIRED", {"required_contract": True}),
}

missing_authority_case = json.loads(json.dumps(positive_case))
missing_authority_case["post_execution"][1]["report_selected_authority_class"] = ""

experience_mismatch_case = json.loads(json.dumps(positive_case))
experience_mismatch_case["post_execution"][1]["experience_writeback_report_selected_path"] = report_alt_path

path_mismatch_case = json.loads(json.dumps(positive_case))
path_mismatch_case["post_execution"][1]["report_selected_path"] = report_alt_path

rc, payload = run_case(positive_case)
assert rc == 0, payload
assert payload["sidecar_contract_status"] == "PASS_REQUIRED", payload
assert payload["sidecar_error_code"] == "", payload
assert payload["track_a"]["report_selected_path"] == report_path, payload
assert payload["track_a"]["report_selection_mode"] == "explicit_report_override", payload
assert payload["track_a"]["report_selected_authority_class"] == "explicit_report_override", payload
assert payload["track_a"]["report_pointer_resolution_mode"] == "explicit_report_override", payload
assert payload["track_a"]["report_projection_source"] == "post_execution_mandatory", payload
assert payload["track_a"]["post_execution_experience_writeback_validation_status"] == "PASS_REQUIRED", payload
assert payload["track_a"]["post_execution_experience_writeback_report_selected_path"] == report_path, payload
assert payload["track_a"]["post_execution_experience_writeback_report_selection_mode"] == "explicit_report_override", payload
assert payload["track_a"]["track_a_stale_reasons"] == [], payload

rc, payload = run_case(missing_authority_case)
assert rc == 1, payload
assert payload["sidecar_contract_status"] == "FAIL_REQUIRED", payload
assert payload["sidecar_error_code"] == "IP-SID-005", payload
assert "track_a_post_execution_authority_projection_missing" in payload["stale_reasons"], payload

rc, payload = run_case(experience_mismatch_case)
assert rc == 1, payload
assert payload["sidecar_contract_status"] == "FAIL_REQUIRED", payload
assert payload["sidecar_error_code"] == "IP-SID-006", payload
assert "track_a_post_execution_experience_writeback_selected_path_mismatch" in payload["stale_reasons"], payload

rc, payload = run_case(path_mismatch_case)
assert rc == 1, payload
assert payload["sidecar_contract_status"] == "FAIL_REQUIRED", payload
assert payload["sidecar_error_code"] == "IP-SID-006", payload
assert "track_a_writeback_post_execution_selected_path_mismatch" in payload["stale_reasons"], payload

print(json.dumps(
    {
        "protocol_feedback_sidecar_contract_probe_status": "PASS_REQUIRED",
        "positive_status": "PASS_REQUIRED",
        "missing_authority_error_code": "IP-SID-005",
        "experience_mismatch_error_code": "IP-SID-006",
        "path_mismatch_error_code": "IP-SID-006",
    },
    ensure_ascii=False,
))
PY

echo "[PASS] protocol feedback sidecar contract probes passed"
