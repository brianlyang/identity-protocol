#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/identity-heal-replay-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

PASS_HEALTH_REPORT="${TMP_DIR}/health-pass.json"
PASS_POST_REPORT="${TMP_DIR}/post-pass.json"
FAIL_HEALTH_MISSING_REPORT="${TMP_DIR}/health-missing-projection.json"
FAIL_POST_REPORT="${TMP_DIR}/post-fail-writeback.json"
PASS_HEAL_REPORT="${TMP_DIR}/identity-heal-probe-pass.json"
FAIL_HEALTH_MISSING_HEAL_REPORT="${TMP_DIR}/identity-heal-probe-health-missing.json"
FAIL_POST_HEAL_REPORT="${TMP_DIR}/identity-heal-probe-post-fail.json"

python3 - <<'PY' \
  "${PASS_HEALTH_REPORT}" \
  "${PASS_POST_REPORT}" \
  "${FAIL_HEALTH_MISSING_REPORT}" \
  "${FAIL_POST_REPORT}" \
  "${PASS_HEAL_REPORT}" \
  "${FAIL_HEALTH_MISSING_HEAL_REPORT}" \
  "${FAIL_POST_HEAL_REPORT}"
import json
import sys
from pathlib import Path

(
    pass_health_report,
    pass_post_report,
    fail_health_missing_report,
    fail_post_report,
    pass_heal_report,
    fail_health_missing_heal_report,
    fail_post_heal_report,
) = [Path(arg).resolve() for arg in sys.argv[1:]]


def write_json(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


base_closure = {
    "status": "PASS",
    "validation_status": "PASS_REQUIRED",
    "report_selected_path": str(pass_post_report),
    "report_selection_mode": "explicit_report",
    "report_selected_authority_class": "explicit_report_argument",
    "report_pointer_resolution_mode": "explicit_report",
    "report_run_id": "probe-heal-replay-run-pass",
    "writeback_status": "WRITTEN",
    "writeback_rule_id": "rule-entry-heal-replay-pass",
    "stale_reasons": [],
}

write_json(
    pass_health_report,
    {
        "identity_id": "probe-heal-replay",
        "overall_status": "PASS",
        "execution_report_ref": str(pass_post_report),
        "experience_writeback_closure": dict(base_closure),
    },
)
write_json(
    pass_post_report,
    {
        "identity_id": "probe-heal-replay",
        "overall_status": "PASS",
        "experience_writeback_closure": dict(base_closure),
        "actor_binding_integrity": {"status": "PASS"},
        "actor_lease_freshness": {"status": "PASS"},
        "implicit_switch_guard": {"status": "PASS"},
        "pointer_drift_guard": {"status": "PASS"},
    },
)
write_json(
    fail_health_missing_report,
    {
        "identity_id": "probe-heal-replay",
        "overall_status": "PASS",
    },
)
write_json(
    fail_post_report,
    {
        "identity_id": "probe-heal-replay",
        "overall_status": "WARN",
        "experience_writeback_closure": {
            "status": "FAIL",
            "validation_status": "FAIL_REQUIRED",
            "report_selected_path": str(fail_post_report),
            "report_selection_mode": "explicit_report",
            "report_selected_authority_class": "explicit_report_argument",
            "report_pointer_resolution_mode": "explicit_report",
            "report_run_id": "probe-heal-replay-run-fail",
            "writeback_status": "MISSING",
            "writeback_rule_id": "",
            "stale_reasons": ["post_validate_experience_writeback_still_fail"],
        },
        "actor_binding_integrity": {"status": "PASS"},
        "actor_lease_freshness": {"status": "PASS"},
        "implicit_switch_guard": {"status": "PASS"},
        "pointer_drift_guard": {"status": "PASS"},
    },
)

write_json(
    pass_heal_report,
    {
        "identity_id": "probe-heal-replay",
        "health_report_ref": str(pass_health_report),
        "heal_report_ref": str(pass_heal_report),
        "post_validate_ref": str(pass_post_report),
    },
)
write_json(
    fail_health_missing_heal_report,
    {
        "identity_id": "probe-heal-replay",
        "health_report_ref": str(fail_health_missing_report),
        "heal_report_ref": str(fail_health_missing_heal_report),
        "post_validate_ref": str(pass_post_report),
    },
)
write_json(
    fail_post_heal_report,
    {
        "identity_id": "probe-heal-replay",
        "health_report_ref": str(pass_health_report),
        "heal_report_ref": str(fail_post_heal_report),
        "post_validate_ref": str(fail_post_report),
    },
)
PY

PASS_OUTPUT="$(python3 scripts/validate_identity_heal_replay_closure.py \
  --identity-id probe-heal-replay \
  --heal-report "${PASS_HEAL_REPORT}" \
  --json-only)"
python3 - <<'PY' "${PASS_OUTPUT}"
import json
import sys

payload = json.loads(sys.argv[1])
assert payload["heal_replay_closure_status"] == "PASS_REQUIRED", payload
assert payload["health_report_experience_writeback_closure_status"] == "PASS", payload
assert payload["health_report_experience_writeback_validation_status"] == "PASS_REQUIRED", payload
assert payload["health_report_execution_report_ref"] == payload["health_report_experience_writeback_report_selected_path"], payload
assert payload["health_report_experience_writeback_selected_path_matches_execution_report_ref"] is True, payload
assert payload["health_report_experience_writeback_report_selection_mode"] == "explicit_report", payload
assert payload["health_report_experience_writeback_report_selected_authority_class"] == "explicit_report_argument", payload
assert payload["health_report_experience_writeback_report_pointer_resolution_mode"] == "explicit_report", payload
assert payload["health_report_experience_writeback_writeback_status"] == "WRITTEN", payload
assert payload["health_report_experience_writeback_writeback_rule_id"] == "rule-entry-heal-replay-pass", payload
assert payload["post_validate_experience_writeback_closure_status"] == "PASS", payload
assert payload["post_validate_experience_writeback_validation_status"] == "PASS_REQUIRED", payload
assert payload["post_validate_experience_writeback_report_selected_path"] == payload["health_report_execution_report_ref"], payload
assert payload["post_validate_experience_writeback_report_selection_mode"] == "explicit_report", payload
assert payload["post_validate_experience_writeback_report_selected_authority_class"] == "explicit_report_argument", payload
assert payload["post_validate_experience_writeback_report_pointer_resolution_mode"] == "explicit_report", payload
assert payload["post_validate_experience_writeback_writeback_status"] == "WRITTEN", payload
assert payload["post_validate_experience_writeback_writeback_rule_id"] == "rule-entry-heal-replay-pass", payload
assert payload["stale_reasons"] == [], payload
PY

if python3 scripts/validate_identity_heal_replay_closure.py \
  --identity-id probe-heal-replay \
  --heal-report "${FAIL_HEALTH_MISSING_HEAL_REPORT}" \
  --json-only >"${TMP_DIR}/health-missing.out"; then
  echo "[FAIL] health projection missing case unexpectedly passed"
  cat "${TMP_DIR}/health-missing.out"
  exit 1
fi
python3 - <<'PY' "${TMP_DIR}/health-missing.out"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["heal_replay_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-HEAL-002", payload
assert "health_report_experience_writeback_projection_missing" in payload["stale_reasons"], payload
assert payload["health_report_experience_writeback_closure_status"] == "", payload
assert payload["health_report_experience_writeback_report_selected_path"] == "", payload
assert payload["post_validate_experience_writeback_closure_status"] == "PASS", payload
PY

if python3 scripts/validate_identity_heal_replay_closure.py \
  --identity-id probe-heal-replay \
  --heal-report "${FAIL_POST_HEAL_REPORT}" \
  --json-only >"${TMP_DIR}/post-fail.out"; then
  echo "[FAIL] post-validate experience writeback failure unexpectedly passed"
  cat "${TMP_DIR}/post-fail.out"
  exit 1
fi
python3 - <<'PY' "${TMP_DIR}/post-fail.out"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["heal_replay_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-HEAL-003", payload
assert "post_validate_experience_writeback_still_fail" in payload["stale_reasons"], payload
assert payload["post_validate_experience_writeback_closure_status"] == "FAIL", payload
assert payload["post_validate_experience_writeback_validation_status"] == "FAIL_REQUIRED", payload
assert payload["post_validate_experience_writeback_report_selection_mode"] == "explicit_report", payload
assert payload["post_validate_experience_writeback_report_selected_authority_class"] == "explicit_report_argument", payload
PY

AUTHORITY_MISSING_HEALTH_REPORT="${TMP_DIR}/health-authority-missing.json"
AUTHORITY_MISSING_HEAL_REPORT="${TMP_DIR}/identity-heal-probe-health-authority-missing.json"

python3 - <<'PY' "${AUTHORITY_MISSING_HEALTH_REPORT}" "${AUTHORITY_MISSING_HEAL_REPORT}" "${PASS_POST_REPORT}"
import json
import sys
from pathlib import Path

authority_missing_health_report = Path(sys.argv[1]).resolve()
authority_missing_heal_report = Path(sys.argv[2]).resolve()
pass_post_report = Path(sys.argv[3]).resolve()

def write_json(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write_json(
    authority_missing_health_report,
    {
        "identity_id": "probe-heal-replay",
        "execution_report_ref": str(pass_post_report),
        "experience_writeback_closure": {
            "status": "PASS",
            "validation_status": "PASS_REQUIRED",
            "report_selected_path": str(pass_post_report),
            "report_run_id": "probe-heal-replay-run-pass",
            "writeback_status": "WRITTEN",
            "writeback_rule_id": "rule-entry-heal-replay-pass",
            "stale_reasons": [],
        },
    },
)
write_json(
    authority_missing_heal_report,
    {
        "identity_id": "probe-heal-replay",
        "health_report_ref": str(authority_missing_health_report),
        "heal_report_ref": str(authority_missing_heal_report),
        "post_validate_ref": str(pass_post_report),
    },
)
PY

if python3 scripts/validate_identity_heal_replay_closure.py \
  --identity-id probe-heal-replay \
  --heal-report "${AUTHORITY_MISSING_HEAL_REPORT}" \
  --json-only >"${TMP_DIR}/health-authority-missing.out"; then
  echo "[FAIL] health authority projection missing case unexpectedly passed"
  cat "${TMP_DIR}/health-authority-missing.out"
  exit 1
fi
python3 - <<'PY' "${TMP_DIR}/health-authority-missing.out"
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["heal_replay_closure_status"] == "FAIL_REQUIRED", payload
assert payload["error_code"] == "IP-HEAL-002", payload
assert "health_report_experience_writeback_authority_projection_missing" in payload["stale_reasons"], payload
assert payload["health_report_experience_writeback_report_selection_mode"] == "", payload
assert payload["health_report_experience_writeback_report_selected_authority_class"] == "", payload
assert payload["health_report_experience_writeback_report_pointer_resolution_mode"] == "", payload
PY

echo "[PASS] identity heal replay closure probes passed"
