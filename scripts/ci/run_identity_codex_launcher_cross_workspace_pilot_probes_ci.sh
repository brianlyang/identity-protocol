#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CURRENT_WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/identity-codex-launcher-cross-workspace-ci.XXXXXX")"
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

FIRST_IDENTITY_ID="$(python3 - <<'PY' "${MATERIALIZED_CONTEXT_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['first_identity_id'])
PY
)"
STRICT_PROFILE_IDENTITY_ID="$(python3 - <<'PY' "${MATERIALIZED_CONTEXT_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['active_execution_report']['identity_id'])
PY
)"
STRICT_PROFILE_REPORT_PATH="$(python3 - <<'PY' "${MATERIALIZED_CONTEXT_JSON}"
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(payload['active_execution_report']['report_path'])
PY
)"

STRICT_BACKFILL_JSON="${TMP_ROOT}/strict-backfill.json"
python3 "${REPO_ROOT}/scripts/run_repair_contract_backfill_strict_profile_probe.py" \
  --repo-root "${REPO_ROOT}" \
  --workspace-root "${TMP_WORKSPACE_ROOT}" \
  --catalog .identity/catalog.local.yaml \
  --identity-id "${STRICT_PROFILE_IDENTITY_ID}" \
  --report-path "${STRICT_PROFILE_REPORT_PATH}" \
  --codex-home "${TMP_CODEX_HOME}" \
  --json-only > "${STRICT_BACKFILL_JSON}"

python3 - "${STRICT_BACKFILL_JSON}" "${STRICT_PROFILE_IDENTITY_ID}" "${STRICT_PROFILE_REPORT_PATH}" <<'PY'
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
print('launcher_cross_workspace_strict_profile_status=FAIL_REQUIRED')
PY

DRY_JSON="${TMP_ROOT}/dry-run.json"
if python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode dry-run \
  --codex-home "${TMP_CODEX_HOME}" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --json-only > "${DRY_JSON}"; then
  echo "[FAIL] cross-workspace launcher convergence dry-run unexpectedly returned success"
  exit 1
fi

python3 - "${DRY_JSON}" "${TMP_CATALOG}" "${TMP_WORKSPACE_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
expected_workspace = str(Path(sys.argv[3]).resolve())
assert payload['status'] == 'FAIL_REQUIRED', payload
assert payload['workspace_catalog_authority_mode'] == 'workspace_local_runtime_catalog', payload
assert payload['catalog_path'] == expected_catalog, payload
assert payload['workspace_root'] == expected_workspace, payload
assert payload['checked_identity_count'] > 0, payload
assert payload['planned_repair_count'] > 0, payload
assert payload['repair_status'] == 'dry_run_preview', payload
PY

DRY_BUNDLE_JSON="${TMP_ROOT}/dry-run-bundle.json"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher_evidence_bundle.py" \
  --payload-json "${DRY_JSON}" \
  --require-ref-field precheck_evidence_ref \
  --require-ref-field evidence_ref \
  --require-ref-field manifest_ref \
  --require-summary-ref \
  --expected-kind launcher_convergence_receipt \
  --expected-kind launcher_convergence_precheck \
  --json-only > "${DRY_BUNDLE_JSON}"

echo 'launcher_cross_workspace_dry_run_status=FAIL_REQUIRED'

APPLY_JSON="${TMP_ROOT}/apply.json"
python3 "${REPO_ROOT}/scripts/run_identity_codex_launcher_workspace_convergence.py" \
  --catalog "${TMP_CATALOG}" \
  --mode apply \
  --codex-home "${TMP_CODEX_HOME}" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --json-only > "${APPLY_JSON}"

python3 - "${APPLY_JSON}" "${TMP_CATALOG}" "${TMP_WORKSPACE_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
expected_workspace = str(Path(sys.argv[3]).resolve())
assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['catalog_path'] == expected_catalog, payload
assert payload['workspace_root'] == expected_workspace, payload
assert payload['checked_identity_count'] > 0, payload
assert payload['remaining_violation_count'] == 0, payload
assert payload['postcheck_status'] == 'PASS_REQUIRED', payload
assert Path(payload['evidence_ref']).exists(), payload
assert Path(payload['manifest_ref']).exists(), payload
assert payload['repair_results'], payload
for row in payload['repair_results']:
    assert row['metadata_repair_status'] == 'PASS_REQUIRED', row
    assert row['metadata_hygiene_status'] == 'PASS_REQUIRED', row
    assert row['backfill_status'] == 'PASS_REQUIRED', row
    assert row['backfill_status_profile'] == 'launcher_workspace_convergence', row
    assert row['backfill_current_run_projection_enforcement_mode'] == 'observe_non_blocking', row
    assert row['install_status'] == 'PASS_REQUIRED', row
    assert row['validator_status'] == 'PASS_REQUIRED', row
    assert row['backfill_current_run_projection_observation_failures'] in (
        [],
        ['current_run_terminal_truth_projection_failed'],
        ['current_run_weak_live_projection_failed'],
        ['current_run_weak_live_projection_failed', 'current_run_terminal_truth_projection_failed'],
    ), row
PY

APPLY_BUNDLE_JSON="${TMP_ROOT}/apply-bundle.json"
python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher_evidence_bundle.py" \
  --payload-json "${APPLY_JSON}" \
  --require-ref-field precheck_evidence_ref \
  --require-ref-field postcheck_evidence_ref \
  --require-ref-field evidence_ref \
  --require-ref-field manifest_ref \
  --require-summary-ref \
  --expected-kind launcher_convergence_receipt \
  --expected-kind launcher_convergence_precheck \
  --expected-kind launcher_convergence_postcheck \
  --json-only > "${APPLY_BUNDLE_JSON}"

echo 'launcher_cross_workspace_apply_status=PASS_REQUIRED'

METADATA_HYGIENE_JSON="${TMP_ROOT}/metadata-hygiene.json"
python3 "${REPO_ROOT}/scripts/validate_runtime_catalog_metadata_hygiene.py" \
  --catalog "${TMP_CATALOG}" \
  --require-active \
  --json-only > "${METADATA_HYGIENE_JSON}"

python3 - "${METADATA_HYGIENE_JSON}" <<'PY'
import json
import sys

payload = json.loads(open(sys.argv[1], "r", encoding="utf-8").read())
assert payload["runtime_catalog_metadata_hygiene_status"] == "PASS_REQUIRED", payload
assert payload["checked_identity_count"] > 0, payload
assert payload["violation_count"] == 0, payload
for row in payload.get("checked_rows") or []:
    assert row["status"] == "PASS_REQUIRED", row
    assert row["canonical_scope"] == "USER", row
print('launcher_cross_workspace_metadata_hygiene_apply_status=PASS_REQUIRED')
PY

FRESH_TRUTH_SYNC_JSON="${TMP_ROOT}/fresh-truth-sync.json"
python3 "${REPO_ROOT}/scripts/refresh_identity_codex_launcher_evidence_truth_sync.py" \
  --artifact-root "${TMP_EVIDENCE_ROOT}" \
  --run-token cross-workspace-pilot \
  --workspace-root "${TMP_WORKSPACE_ROOT}" \
  --json-only > "${FRESH_TRUTH_SYNC_JSON}"

python3 - "${FRESH_TRUTH_SYNC_JSON}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert payload['status'] == 'PASS_REQUIRED', payload
assert payload['truth_sync_status'] == 'PASS_REQUIRED', payload
assert payload['receipts_with_changes'] == 0, payload
assert payload['manifest_write_count'] == 0, payload
assert payload['repair_status'] == 'already_truth_synced', payload
print('launcher_cross_workspace_fresh_truth_sync_status=PASS_REQUIRED')
PY

CLOSURE_JSON="${TMP_ROOT}/closure.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/check_identity_codex_launcher_migration_closure.py" \
      --catalog .identity/catalog.local.yaml \
      --workspace-runtime-only \
      --json-only) > "${CLOSURE_JSON}"

python3 - "${CLOSURE_JSON}" "${TMP_CODEX_HOME}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_home = str((Path(sys.argv[2]).resolve() / '.identity').resolve())
expected_catalog = str(Path(sys.argv[3]).resolve())
assert payload['identity_codex_launcher_migration_closure_status'] == 'PASS_REQUIRED', payload
assert payload['catalogs_checked'] == [expected_catalog], payload
assert payload['checked_identity_count'] > 0, payload
for row in payload['checked_rows']:
    assert row['runtime_paths_status'] == 'PASS_REQUIRED', row
    assert row['launcher_config_identity_home'] == expected_identity_home, row
    assert row['runtime_identity_home'] == str(Path(expected_catalog).parent.resolve()), row
print('launcher_cross_workspace_closure_status=PASS_REQUIRED')
PY

RESOLVE_JSON="${TMP_ROOT}/resolve.json"
(cd "${TMP_WORKSPACE_ROOT}" && \
  env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
    CODEX_HOME="${TMP_CODEX_HOME}" \
    python3 "${REPO_ROOT}/scripts/resolve_identity_context.py" \
      resolve \
      --identity-id "${FIRST_IDENTITY_ID}") > "${RESOLVE_JSON}"

python3 - "${RESOLVE_JSON}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_catalog = str(Path(sys.argv[2]).resolve())
assert payload['catalog_path'] == expected_catalog, payload
assert payload['source_layer'] == 'project', payload
assert payload['resolved_scope'] == 'USER', payload
assert payload['candidate_matches'], payload
assert payload['candidate_matches'][0]['scope'] == 'USER', payload
print('launcher_cross_workspace_resolve_status=PASS_REQUIRED')
PY

VALIDATOR_JSON="${TMP_ROOT}/validator.json"
env -u IDENTITY_HOME -u IDENTITY_CATALOG -u IDENTITY_PROTOCOL_HOME \
  CODEX_HOME="${TMP_CODEX_HOME}" \
  python3 "${REPO_ROOT}/scripts/validate_identity_codex_launcher.py" \
    --catalog "${TMP_CATALOG}" \
    --identity-id "${FIRST_IDENTITY_ID}" \
    --require-installed \
    --json-only > "${VALIDATOR_JSON}"

python3 - "${VALIDATOR_JSON}" "${TMP_CODEX_HOME}" "${TMP_CATALOG}" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
expected_identity_home = str((Path(sys.argv[2]).resolve() / '.identity').resolve())
expected_catalog = str(Path(sys.argv[3]).resolve())
assert payload['identity_codex_launcher_status'] == 'PASS_REQUIRED', payload
assert payload['runtime_paths_status'] == 'PASS_REQUIRED', payload
assert payload['launcher_runtime_admissibility_projection_status'] == 'PASS_REQUIRED', payload
assert payload['launcher_runtime_admissibility_status'] == 'PASS_REQUIRED', payload
assert payload['launcher_config_identity_home'] == expected_identity_home, payload
assert payload['runtime_identity_home'] == str(Path(expected_catalog).parent.resolve()), payload
print('launcher_cross_workspace_validator_status=PASS_REQUIRED')
PY

echo "[PASS] identity codex launcher cross-workspace pilot probes passed"
