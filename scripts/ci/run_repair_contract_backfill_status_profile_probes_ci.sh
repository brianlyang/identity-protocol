#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${REPO_ROOT}/scripts/shell_strict_entry_common.sh"

CURRENT_WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/repair-contract-backfill-status-profile-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

TMP_WORKSPACE_ROOT="${TMP_ROOT}/workspace"
TMP_IDENTITY_HOME="${TMP_WORKSPACE_ROOT}/.identity"
TMP_CATALOG="${TMP_IDENTITY_HOME}/catalog.local.yaml"
TMP_CODEX_HOME="${TMP_ROOT}/codex-home"
TMP_EVIDENCE_ROOT="${TMP_ROOT}/evidence"
mkdir -p "${TMP_WORKSPACE_ROOT}" "${TMP_CODEX_HOME}" "${TMP_EVIDENCE_ROOT}"

MATERIALIZED_CONTEXT_JSON="${TMP_ROOT}/materialized-context.json"
python3 "${REPO_ROOT}/scripts/materialize_cross_workspace_runtime_probe_context.py" \
  --current-workspace-root "${CURRENT_WORKSPACE_ROOT}" \
  --target-workspace-root "${TMP_WORKSPACE_ROOT}" \
  --catalog "${IDENTITY_LAUNCHER_PILOT_CATALOG:-}" \
  --repo-root "${REPO_ROOT}" \
  --require-active-execution-report \
  --json-only > "${MATERIALIZED_CONTEXT_JSON}"

PROFILE_IDENTITY_ID="$(python3 - <<'PY' "${MATERIALIZED_CONTEXT_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['active_execution_report']['identity_id'])
PY
)"
PROFILE_REPORT_PATH="$(python3 - <<'PY' "${MATERIALIZED_CONTEXT_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['active_execution_report']['report_path'])
PY
)"

STRICT_JSON="${TMP_ROOT}/strict-full.json"
python3 "${REPO_ROOT}/scripts/run_repair_contract_backfill_strict_profile_probe.py" \
  --repo-root "${REPO_ROOT}" \
  --workspace-root "${TMP_WORKSPACE_ROOT}" \
  --catalog .identity/catalog.local.yaml \
  --identity-id "${PROFILE_IDENTITY_ID}" \
  --report-path "${PROFILE_REPORT_PATH}" \
  --codex-home "${TMP_CODEX_HOME}" \
  --json-only > "${STRICT_JSON}"

python3 - "${STRICT_JSON}" "${PROFILE_IDENTITY_ID}" "${PROFILE_REPORT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_id = str(sys.argv[2]).strip()
expected_report_path = str(Path(sys.argv[3]).resolve())

assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['identity_id'] == expected_identity_id, payload
probe = payload.get('strict_profile_probe') or {}
assert probe.get('strict_profile_status') == 'FAIL_REQUIRED', payload
assert probe.get('status_profile') == 'strict_full', payload
assert probe.get('current_run_projection_enforcement_mode') == 'blocking', payload
assert probe.get('current_run_projection_observation_failures') == [], payload
blocking = probe.get('current_run_projection_blocking_failures') or []
assert any(
    item in blocking
    for item in ('current_run_terminal_truth_projection_failed', 'current_run_weak_live_projection_failed')
), payload
assert probe.get('report_selected_path') == expected_report_path, payload
print('repair_contract_backfill_strict_profile_status=FAIL_REQUIRED')
PY

CONVERGENCE_JSON="${TMP_ROOT}/launcher-workspace-convergence.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/repair_contract_backfill.py" \
      --catalog .identity/catalog.local.yaml \
      --identity-id "${PROFILE_IDENTITY_ID}" \
      --status-profile launcher_workspace_convergence \
      --apply \
      --json-only) > "${CONVERGENCE_JSON}"

python3 - "${CONVERGENCE_JSON}" "${PROFILE_IDENTITY_ID}" "${PROFILE_REPORT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_id = str(sys.argv[2]).strip()
expected_report_path = str(Path(sys.argv[3]).resolve())

assert payload['identity_id'] == expected_identity_id, payload
assert payload['contract_backfill_status'] == 'PASS_REQUIRED', payload
assert payload['status_profile'] == 'launcher_workspace_convergence', payload
assert payload['current_run_projection_enforcement_mode'] == 'observe_non_blocking', payload
assert payload['current_run_projection_blocking_failures'] == [], payload
observed = payload.get('current_run_projection_observation_failures') or []
assert any(
    item in observed
    for item in ('current_run_terminal_truth_projection_failed', 'current_run_weak_live_projection_failed')
), payload
terminal_truth = payload.get('current_run_terminal_truth_projection_backfill') or {}
assert terminal_truth.get('report_selected_path') == expected_report_path, payload
print('repair_contract_backfill_launcher_workspace_convergence_profile_status=PASS_REQUIRED')
PY

WORKSPACE_RUNTIME_JSON="${TMP_ROOT}/workspace-runtime-convergence.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    IDENTITY_PROTOCOL_HOME="${REPO_ROOT}" \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/repair_contract_backfill.py" \
      --catalog .identity/catalog.local.yaml \
      --identity-id "${PROFILE_IDENTITY_ID}" \
      --status-profile workspace_runtime_convergence \
      --apply \
      --json-only) > "${WORKSPACE_RUNTIME_JSON}"

python3 - "${WORKSPACE_RUNTIME_JSON}" "${PROFILE_IDENTITY_ID}" "${PROFILE_REPORT_PATH}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_id = str(sys.argv[2]).strip()
expected_report_path = str(Path(sys.argv[3]).resolve())

assert payload['identity_id'] == expected_identity_id, payload
assert payload['contract_backfill_status'] == 'PASS_REQUIRED', payload
assert payload['status_profile'] == 'workspace_runtime_convergence', payload
assert payload['current_run_projection_enforcement_mode'] == 'observe_non_blocking', payload
assert payload['current_run_projection_blocking_failures'] == [], payload
observed = payload.get('current_run_projection_observation_failures') or []
assert any(
    item in observed
    for item in ('current_run_terminal_truth_projection_failed', 'current_run_weak_live_projection_failed')
), payload
terminal_truth = payload.get('current_run_terminal_truth_projection_backfill') or {}
assert terminal_truth.get('report_selected_path') == expected_report_path, payload
print('repair_contract_backfill_workspace_runtime_convergence_profile_status=PASS_REQUIRED')
PY

PYTHONPATH="${REPO_ROOT}/scripts" python3 - <<'PY'
import identity_creator as mod

captured = {}

def fake_run(cmd):
    captured['cmd'] = cmd
    return 0

def fake_validators(**kwargs):
    captured['validators'] = kwargs
    return 0

orig_run = mod._run
orig_validators = mod._run_instance_script_contract_validators
try:
    mod._run = fake_run
    mod._run_instance_script_contract_validators = fake_validators
    rc = mod._run_workspace_runtime_convergence_backfill_with_instance_script_rollout(
        identity_id='probe-identity',
        catalog='/tmp/probe-catalog.local.yaml',
        work_layer='instance',
        source_layer='project',
    )
finally:
    mod._run = orig_run
    mod._run_instance_script_contract_validators = orig_validators

assert rc == 0, rc
cmd = captured['cmd']
assert '--status-profile' in cmd, cmd
assert cmd[cmd.index('--status-profile') + 1] == 'workspace_runtime_convergence', cmd
print('identity_creator_workspace_runtime_convergence_backfill_command=PASS_REQUIRED')
PY

APPLY_JSON="${TMP_ROOT}/launcher-convergence-apply.json"
python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode apply \
  --codex-home "${TMP_CODEX_HOME}" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token status-profile-probe \
  --json-only > "${APPLY_JSON}"

python3 - "${APPLY_JSON}" "${PROFILE_IDENTITY_ID}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
identity_id = str(sys.argv[2]).strip()

assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['postcheck_status'] == 'PASS_REQUIRED', payload
rows = payload.get('repair_results') or []
assert rows, payload
row = next((row for row in rows if str(row.get('identity_id', '')).strip() == identity_id), rows[0])
assert row['backfill_status'] == 'PASS_REQUIRED', row
assert row['backfill_status_profile'] == 'launcher_workspace_convergence', row
assert row['backfill_current_run_projection_enforcement_mode'] == 'observe_non_blocking', row
observed = row.get('backfill_current_run_projection_observation_failures') or []
assert any(
    item in observed
    for item in ('current_run_terminal_truth_projection_failed', 'current_run_weak_live_projection_failed')
), row
print('launcher_workspace_convergence_entry_profile_status=PASS_REQUIRED')
PY

echo "[PASS] repair_contract_backfill status-profile probes passed"
