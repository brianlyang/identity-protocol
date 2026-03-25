#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/release-readiness-summary-binding-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

PYTHONPATH="${REPO_ROOT}/scripts${PYTHONPATH:+:${PYTHONPATH}}" \
python3 - "${TMP_ROOT}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

import release_readiness_check as readiness
from runtime_temp_path_common import runtime_temp_file

repo_root = Path.cwd().resolve()
tmp_root = Path(sys.argv[1]).resolve()

receipt_path = (tmp_root / 'required-gate-bundle.json').resolve()
probe_path = (tmp_root / 'required-gate-bundle-scan-probe.json').resolve()
missing_path = (tmp_root / 'required-gate-bundle-missing.json').resolve()

base_payload = {
    'bundle_status': 'PASS_REQUIRED',
    'error_code': '',
    'bundle_contract_id': 'probe.required_gate_bundle_contract_v1',
    'bundle_key': 'required_gate_bundle_contract_v1',
    'surface_label': 'ci_probe',
    'identity_id': 'probe-identity',
    'actor_id': 'assistant:codex',
    'resolved_work_layer': 'instance',
    'resolved_source_layer': 'project',
    'lock_state': 'LOCK_MATCH',
    'run_id_binding': 'probe-run-id',
    'report_selected_path': '/tmp/probe-report.json',
    'results': [],
}
receipt_path.write_text(json.dumps(base_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
probe_payload = dict(base_payload)
probe_payload['bundle_status'] = 'FAIL_REQUIRED'
probe_payload['run_id_binding'] = 'probe-run-id-scan'
probe_path.write_text(json.dumps(probe_payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

summary_unobserved = {}
readiness._hydrate_required_gate_bundle_summary(
    summary_unobserved,
    repo_root=repo_root,
    receipt_path=str(receipt_path),
    receipt_probe_path=str(probe_path),
)
assert summary_unobserved['required_gate_bundle']['bundle_status'] == 'UNKNOWN', summary_unobserved
assert summary_unobserved['required_gate_bundle']['projection_status'] == 'UNKNOWN', summary_unobserved
assert summary_unobserved['required_gate_bundle']['projection_stale_reasons'] == [
    'bundle_receipt_not_observed_in_current_release_readiness_run'
], summary_unobserved
assert summary_unobserved['required_gate_bundle_scan_probe']['bundle_status'] == 'UNKNOWN', summary_unobserved

summary_observed = {
    'required_gate_bundle_execution': {
        'observed_receipt_paths': [str(receipt_path), str(probe_path)],
    }
}
readiness._hydrate_required_gate_bundle_summary(
    summary_observed,
    repo_root=repo_root,
    receipt_path=str(receipt_path),
    receipt_probe_path=str(probe_path),
)
assert summary_observed['required_gate_bundle']['bundle_status'] == 'PASS_REQUIRED', summary_observed
assert summary_observed['required_gate_bundle']['projection_status'] == 'PASS_REQUIRED', summary_observed
assert summary_observed['required_gate_bundle_scan_probe']['bundle_status'] == 'FAIL_REQUIRED', summary_observed
assert summary_observed['required_gate_bundle_scan_probe']['projection_status'] == 'PASS_REQUIRED', summary_observed

summary_missing_after_observed = {
    'required_gate_bundle_execution': {
        'observed_receipt_paths': [str(missing_path)],
    }
}
readiness._hydrate_required_gate_bundle_summary(
    summary_missing_after_observed,
    repo_root=repo_root,
    receipt_path=str(missing_path),
    receipt_probe_path=str(probe_path),
)
assert summary_missing_after_observed['required_gate_bundle']['bundle_status'] == 'UNKNOWN', summary_missing_after_observed
assert summary_missing_after_observed['required_gate_bundle']['projection_stale_reasons'] == [
    'bundle_receipt_missing_after_observed_dispatch'
], summary_missing_after_observed

release_cloud_payload = {
    'release_plane_cloud_evidence_status': 'PASS_REQUIRED',
    'release_plane_status': 'CLOSED',
    'conditions': {'required_checks_status': 'PASS'},
    'release_cloud_evidence_adapter_status': 'PASS_REQUIRED',
    'adapter_source_kind': 'gh_run_list_json',
    'adapter_acquisition_mode': 'materialized_input',
    'adapter_fetch_transport': 'local_file',
    'adapter_local_dev_canonical': True,
    'adapter_best_effort_fetch': False,
    'semantic_consumption_mode': 'protocol_canonical_aggregation',
}
summary_release_projection = {
    'release_plane_cloud_evidence': readiness.build_release_plane_cloud_evidence_summary_projection(
        release_cloud_payload
    ),
    'release_cloud_evidence_adapter': readiness.build_release_cloud_evidence_adapter_projection(
        release_cloud_payload
    ),
    'control_plane_budget': {
        'status': 'PASS_REQUIRED',
    },
    'control_plane_budget_sync': {
        'status': 'PASS_REQUIRED',
        'mismatch_count': 0,
    },
    'control_plane_status_sync': {
        'status': 'PASS_REQUIRED',
        'live_control_plane_status': 'PASS_REQUIRED',
        'file_control_plane_status': 'PASS_REQUIRED',
        'mismatch_count': 0,
    },
    'control_plane_surface_materialization': {
        'status': 'PASS_REQUIRED',
        'control_plane_status': 'PASS_REQUIRED',
        'promotion_ready': True,
    },
}
readiness._hydrate_one_look_projection(summary_release_projection)
assert summary_release_projection['one_look']['release_plane_cloud_evidence_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_plane_required_checks_status'] == 'PASS', summary_release_projection
assert summary_release_projection['one_look']['release_cloud_evidence_adapter_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_cloud_evidence_adapter_source_kind'] == 'gh_run_list_json', summary_release_projection
assert summary_release_projection['one_look']['release_cloud_evidence_adapter_local_dev_canonical'] is True, summary_release_projection
assert summary_release_projection['one_look']['control_plane_budget_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_budget_sync_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_status_sync_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_live_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_file_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_sync_mismatch_count'] == 0, summary_release_projection
assert summary_release_projection['one_look']['control_plane_surface_materialization_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_materialized_control_plane_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['control_plane_materialized_promotion_ready'] is True, summary_release_projection

report_derived_token = readiness._derive_bundle_run_token(
    required_gates_run_id='',
    execution_report='../.identity/probe/runtime/reports/identity-upgrade-exec-probe-1774424750.json',
    session_id='run:probe-session',
    identity_id='probe-identity',
)
assert report_derived_token == 'identity-upgrade-exec-probe-1774424750', report_derived_token
session_fallback_token = readiness._derive_bundle_run_token(
    required_gates_run_id='',
    execution_report='',
    session_id='run:probe-session',
    identity_id='probe-identity',
)
assert session_fallback_token == 'run-probe-session', session_fallback_token

legacy_path = runtime_temp_file(
    channel='required-gate-bundle',
    operation='readiness',
    identity_id='probe-identity',
    stem='required-gate-bundle-readiness-probe',
    ext='json',
)
run_bound_path = runtime_temp_file(
    channel='required-gate-bundle',
    operation='readiness',
    identity_id='probe-identity',
    run_token=report_derived_token,
    stem='required-gate-bundle-readiness-probe',
    ext='json',
)
assert legacy_path != run_bound_path, (legacy_path, run_bound_path)
assert report_derived_token in run_bound_path.name, run_bound_path
assert report_derived_token not in legacy_path.name, legacy_path

print(json.dumps({
    'release_readiness_summary_binding_probe_status': 'PASS_REQUIRED',
    'report_derived_token': report_derived_token,
    'session_fallback_token': session_fallback_token,
    'legacy_path': str(legacy_path),
    'run_bound_path': str(run_bound_path),
}, ensure_ascii=False))
PY

echo "[PASS] release readiness summary binding probes passed"
