#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/sidecar-cwd-parity-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

CATALOG_PATH="${TMP_DIR}/catalog.local.yaml"
PACK_PATH="${TMP_DIR}/sidecar-cwd-parity-probe-identity"
TEMP_RUNTIME_ROOT="${TMP_DIR}/runtime-temp"
REPORT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-sidecar-cwd-parity-probe.json"
REPORT_ALT_PATH="${PACK_PATH}/runtime/reports/identity-upgrade-exec-sidecar-cwd-parity-probe-alt.json"
mkdir -p "${PACK_PATH}/runtime/reports" "${TEMP_RUNTIME_ROOT}"
printf '{}\n' > "${CATALOG_PATH}"
printf '{}\n' > "${REPORT_PATH}"
printf '{}\n' > "${REPORT_ALT_PATH}"

python3 - <<'PY' "${CATALOG_PATH}" "${PACK_PATH}" "${TEMP_RUNTIME_ROOT}" "${REPORT_PATH}" "${REPORT_ALT_PATH}"
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

repo_root = Path.cwd().resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

import validate_sidecar_cwd_parity as target

catalog_path = Path(sys.argv[1]).resolve()
pack_path = Path(sys.argv[2]).resolve()
temp_runtime_root = Path(sys.argv[3]).resolve()
report_path = str(Path(sys.argv[4]).resolve())
report_alt_path = str(Path(sys.argv[5]).resolve())
task_path = (pack_path / "CURRENT_TASK.json").resolve()
task_path.write_text("{}", encoding="utf-8")

task_doc = {
    "sidecar_cwd_invariance_contract_v1": {
        "required": True,
    }
}

base_sidecar_payload = {
    "requiredization_current_round_linked": True,
    "sidecar_contract_status": "PASS_REQUIRED",
    "sidecar_error_code": "",
    "required_contract": True,
    "auto_required_signal": True,
    "escalation_required": False,
    "escalation_decision": "NON_BLOCKING_DEFAULT",
    "blocking_error_codes": [],
    "track_a": {
        "report_selected_path": report_path,
        "report_selection_mode": "explicit_report_override",
        "report_selected_authority_class": "explicit_report_override",
        "report_pointer_resolution_mode": "explicit_report_override",
        "report_pointer_path": "",
        "report_projection_source": "post_execution_mandatory",
        "writeback_report_selected_path": report_path,
        "writeback_report_selection_mode": "explicit_report_override",
        "writeback_report_selected_authority_class": "explicit_report_override",
        "writeback_report_pointer_resolution_mode": "explicit_report_override",
        "writeback_report_pointer_path": "",
        "post_execution_report_selected_path": report_path,
        "post_execution_report_selection_mode": "explicit_report_override",
        "post_execution_report_selected_authority_class": "explicit_report_override",
        "post_execution_report_pointer_resolution_mode": "explicit_report_override",
        "post_execution_report_pointer_path": "",
        "post_execution_experience_writeback_validation_status": "PASS_REQUIRED",
        "post_execution_experience_writeback_error_code": "",
        "post_execution_experience_writeback_report_selected_path": report_path,
        "post_execution_experience_writeback_report_selection_mode": "explicit_report_override",
        "post_execution_experience_writeback_report_selected_authority_class": "explicit_report_override",
        "post_execution_experience_writeback_report_pointer_resolution_mode": "explicit_report_override",
        "post_execution_experience_writeback_report_pointer_path": "",
        "track_a_stale_reasons": [],
    },
    "track_b": {
        "semantic_routing_status": "PASS_REQUIRED",
        "vendor_namespace_status": "PASS_REQUIRED",
        "protocol_feedback_reply_channel_status": "PASS_REQUIRED",
    },
}


def run_case(root_doc: dict, temp_doc: dict) -> tuple[int, dict]:
    def fake_run_sidecar_validator(*, cwd: Path, catalog: Path, repo_catalog: Path, identity_id: str, operation: str):
        payload = root_doc if Path(cwd).resolve() == repo_root else temp_doc
        return 0, json.dumps(payload, ensure_ascii=False), "", payload

    argv = [
        "validate_sidecar_cwd_parity.py",
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_root / "identity/catalog/identities.yaml"),
        "--identity-id",
        "sidecar-cwd-parity-probe-identity",
        "--operation",
        "ci",
        "--json-only",
    ]

    stdout = io.StringIO()
    with patch.object(sys, "argv", argv), \
        patch.object(target, "resolve_pack_and_task", return_value=(pack_path, task_path)), \
        patch.object(target, "load_json", return_value=task_doc), \
        patch.object(target, "runtime_temp_dir", return_value=temp_runtime_root), \
        patch.object(target, "_run_sidecar_validator", side_effect=fake_run_sidecar_validator), \
        redirect_stdout(stdout):
        rc = target.main()
    return rc, json.loads(stdout.getvalue())


positive_root = json.loads(json.dumps(base_sidecar_payload))
positive_temp = json.loads(json.dumps(base_sidecar_payload))

authority_mismatch_root = json.loads(json.dumps(base_sidecar_payload))
authority_mismatch_temp = json.loads(json.dumps(base_sidecar_payload))
authority_mismatch_temp["track_a"]["report_selected_authority_class"] = "active_execution_pointer_pack_local_report"

experience_path_mismatch_root = json.loads(json.dumps(base_sidecar_payload))
experience_path_mismatch_temp = json.loads(json.dumps(base_sidecar_payload))
experience_path_mismatch_temp["track_a"]["post_execution_experience_writeback_report_selected_path"] = report_alt_path

stale_reason_mismatch_root = json.loads(json.dumps(base_sidecar_payload))
stale_reason_mismatch_temp = json.loads(json.dumps(base_sidecar_payload))
stale_reason_mismatch_temp["track_a"]["track_a_stale_reasons"] = [
    "track_a_post_execution_experience_writeback_selected_path_mismatch"
]

rc, payload = run_case(positive_root, positive_temp)
assert rc == 0, payload
assert payload["sidecar_cwd_parity_status"] == "PASS_REQUIRED", payload
assert payload["cwd_parity_status"] == "PASS_REQUIRED", payload

rc, payload = run_case(authority_mismatch_root, authority_mismatch_temp)
assert rc == 1, payload
assert payload["sidecar_cwd_parity_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SIDECWD-002", payload
assert "root_temp_digest_mismatch" in payload["stale_reasons"], payload

rc, payload = run_case(experience_path_mismatch_root, experience_path_mismatch_temp)
assert rc == 1, payload
assert payload["sidecar_cwd_parity_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SIDECWD-002", payload

rc, payload = run_case(stale_reason_mismatch_root, stale_reason_mismatch_temp)
assert rc == 1, payload
assert payload["sidecar_cwd_parity_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-SIDECWD-002", payload

print(json.dumps(
    {
        "sidecar_cwd_parity_probe_status": "PASS_REQUIRED",
        "authority_projection_mismatch_error_code": "IP-SIDECWD-002",
        "experience_writeback_path_mismatch_error_code": "IP-SIDECWD-002",
        "track_a_stale_reason_mismatch_error_code": "IP-SIDECWD-002",
    },
    ensure_ascii=False,
))
PY

echo "[PASS] sidecar cwd parity probes passed"
