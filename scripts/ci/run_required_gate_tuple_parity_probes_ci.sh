#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/required-gate-tuple-parity-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

POSITIVE_A="${TMP_DIR}/positive-validate.json"
POSITIVE_B="${TMP_DIR}/positive-three-plane.json"
NEGATIVE_AUTHORITY="${TMP_DIR}/negative-authority.json"
NEGATIVE_POINTER="${TMP_DIR}/negative-pointer.json"

python3 - <<'PY' "${POSITIVE_A}" "${POSITIVE_B}" "${NEGATIVE_AUTHORITY}" "${NEGATIVE_POINTER}"
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

positive_a = Path(sys.argv[1]).resolve()
positive_b = Path(sys.argv[2]).resolve()
negative_authority = Path(sys.argv[3]).resolve()
negative_pointer = Path(sys.argv[4]).resolve()

base_receipt = {
    "run_id_binding": "probe-run",
    "identity_id": "probe-identity",
    "actor_id": "assistant:probe",
    "resolved_work_layer": "instance",
    "resolved_source_layer": "project",
    "lock_state": "LOCK_MATCH",
    "report_selected_path": "/tmp/probe-report.json",
    "report_selection_mode": "explicit_report_override",
    "report_selected_authority_class": "explicit_report_override",
    "report_pointer_resolution_mode": "explicit_report_override",
    "report_pointer_path": "",
    "required_contract": True,
    "failed_required_contract_count": 0,
    "send_time_gate_status": "PASS_REQUIRED",
    "outlet_bypass_detected": False,
    "final_emit_contract_status": "PASS_REQUIRED",
    "final_emit_policy_mode": "tool_choice_required",
    "final_emit_schema_status": "PASS_REQUIRED",
    "parity_operation_scope": "current_round_report_lineage",
}

validate_receipt = {
    **base_receipt,
    "operation": "validate",
    "surface_label": "ci_validate_probe",
}
three_plane_receipt = {
    **base_receipt,
    "operation": "three-plane",
    "surface_label": "ci_three_plane_probe",
}
authority_mismatch_receipt = {
    **three_plane_receipt,
    "report_selected_authority_class": "active_execution_pointer_pack_local_report",
}
pointer_mismatch_receipt = {
    **three_plane_receipt,
    "report_pointer_resolution_mode": "pointer_candidate_root_report",
}

for path, payload in (
    (positive_a, validate_receipt),
    (positive_b, three_plane_receipt),
    (negative_authority, authority_mismatch_receipt),
    (negative_pointer, pointer_mismatch_receipt),
):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

script = Path.cwd() / "scripts" / "validate_required_gate_tuple_parity.py"

def run_case(*receipts: Path) -> tuple[int, dict]:
    cmd = [
        "python3",
        str(script),
        "--require-distinct-operations",
        "--json-only",
    ]
    for receipt in receipts:
        cmd.extend(["--receipt", str(receipt)])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    payload = json.loads(proc.stdout.strip() or "{}")
    return proc.returncode, payload

rc, payload = run_case(positive_a, positive_b)
assert rc == 0, payload
assert payload["required_gate_tuple_parity_status"] == "PASS_REQUIRED", payload
assert "report_selected_authority_class" in payload["tuple_fields"], payload
assert "report_pointer_resolution_mode" in payload["tuple_fields"], payload

rc, payload = run_case(positive_a, negative_authority)
assert rc == 1, payload
assert payload["required_gate_tuple_parity_status"] == "FAIL_REQUIRED", payload
assert "report_selected_authority_class" in payload["mismatches"], payload

rc, payload = run_case(positive_a, negative_pointer)
assert rc == 1, payload
assert payload["required_gate_tuple_parity_status"] == "FAIL_REQUIRED", payload
assert "report_pointer_resolution_mode" in payload["mismatches"], payload

print(json.dumps(
    {
        "required_gate_tuple_parity_probe_status": "PASS_REQUIRED",
        "authority_mismatch_field": "report_selected_authority_class",
        "pointer_mismatch_field": "report_pointer_resolution_mode",
    },
    ensure_ascii=False,
))
PY

echo "[PASS] required gate tuple parity probes passed"
