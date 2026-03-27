#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

PYTHONPATH="${REPO_ROOT}/scripts" python3 - <<'PY'
import identity_creator as mod
from baseline_evidence_repair_signal_common import detect_baseline_evidence_repair_needs

payload = detect_baseline_evidence_repair_needs(
    "[FAIL] role-binding evidence is stale: age_days=8.0 > max_age_days=7"
)
assert payload["repair_role_binding"] is True, payload
assert payload["repair_protocol"] is False, payload
assert "role-binding evidence is stale" in payload["detected_signals"], payload
print("baseline_evidence_repair_signal_role_binding_stale=PASS_REQUIRED")

captured_cmds = []
validator_calls = {"count": 0}


def fake_run_capture(cmd):
    if cmd[:2] == ["python3", "scripts/validate_identity_role_binding.py"]:
        validator_calls["count"] += 1
        if validator_calls["count"] == 1:
            return 1, "[FAIL] role-binding evidence is stale: age_days=8.0 > max_age_days=7", ""
        return 0, "[OK] role-binding evidence refreshed", ""
    raise AssertionError(f"unexpected _run_capture cmd: {cmd}")


def fake_run(cmd):
    captured_cmds.append(cmd)
    return 0


orig_run_capture = mod._run_capture
orig_run = mod._run
try:
    mod._run_capture = fake_run_capture
    mod._run = fake_run
    rc = mod._ensure_role_binding_evidence_fresh(
        catalog="/tmp/probe-catalog.local.yaml",
        identity_id="probe-identity",
        operation_label="update",
    )
finally:
    mod._run_capture = orig_run_capture
    mod._run = orig_run

assert rc == 0, rc
assert validator_calls["count"] == 2, validator_calls
assert len(captured_cmds) == 1, captured_cmds
repair_cmd = captured_cmds[0]
assert repair_cmd[:2] == ["python3", "scripts/repair_identity_baseline_evidence.py"], repair_cmd
assert "--repair-role-binding" in repair_cmd, repair_cmd
print("identity_creator_role_binding_stale_autorepair=PASS_REQUIRED")

captured_cmds = []


def fake_run_capture_negative(cmd):
    if cmd[:2] == ["python3", "scripts/validate_identity_role_binding.py"]:
        return 1, "[FAIL] role-binding evidence role_type mismatch with contract", ""
    raise AssertionError(f"unexpected _run_capture cmd: {cmd}")


def fake_run_negative(cmd):
    captured_cmds.append(cmd)
    return 0


orig_run_capture = mod._run_capture
orig_run = mod._run
try:
    mod._run_capture = fake_run_capture_negative
    mod._run = fake_run_negative
    rc = mod._ensure_role_binding_evidence_fresh(
        catalog="/tmp/probe-catalog.local.yaml",
        identity_id="probe-identity",
        operation_label="validate",
    )
finally:
    mod._run_capture = orig_run_capture
    mod._run = orig_run

assert rc != 0, rc
assert captured_cmds == [], captured_cmds
print("identity_creator_role_binding_nonrepairable_preserves_failclose=PASS_REQUIRED")
PY

echo "[PASS] identity_creator baseline evidence auto-repair probes passed"
