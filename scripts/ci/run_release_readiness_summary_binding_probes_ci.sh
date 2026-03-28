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

from governed_runtime_summary_checkpoint_common import (
    capture_governed_runtime_summary_resume_source,
    derive_governed_runtime_summary_resume_projection,
)
from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload
from release_cloud_evidence_projection_common import (
    build_release_readiness_release_cloud_evidence_one_look_projection,
)
from release_readiness_foundational_projection_common import (
    build_release_readiness_foundational_one_look_projection,
    RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
)
from release_readiness_one_look_projection_common import (
    build_release_readiness_one_look_projection,
)
from release_readiness_selected_check_scope_common import (
    build_release_readiness_selected_check_scope_one_look_projection,
)
from release_readiness_support_preflight_projection_common import (
    build_release_readiness_support_preflight_one_look_projection,
    RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
)
import release_readiness_check as readiness
from runtime_temp_path_common import runtime_temp_file

repo_root = Path.cwd().resolve()
tmp_root = Path(sys.argv[1]).resolve()

receipt_path = (tmp_root / 'required-gate-bundle.json').resolve()
probe_path = (tmp_root / 'required-gate-bundle-scan-probe.json').resolve()
missing_path = (tmp_root / 'required-gate-bundle-missing.json').resolve()
probe_actor_id = 'assistant:probe'

base_payload = {
    'bundle_status': 'PASS_REQUIRED',
    'error_code': '',
    'bundle_contract_id': 'probe.required_gate_bundle_contract_v1',
    'bundle_key': 'required_gate_bundle_contract_v1',
    'surface_label': 'ci_probe',
    'identity_id': 'probe-identity',
    'actor_id': probe_actor_id,
    'resolved_work_layer': 'instance',
    'resolved_source_layer': 'project',
    'lock_state': 'LOCK_MATCH',
    'run_id_binding': 'probe-run-id',
    'report_selected_path': '/tmp/probe-report.json',
    'report_logical_identity_key': '{"identity_id":"probe-identity","run_id":"probe-run-id","catalog_path":"/tmp/catalog.local.yaml","resolved_pack_path":"/tmp/.identity/probe-identity","identity_prompt_sha256":"prompt-sha"}',
    'report_selection_mode': 'explicit_report_override',
    'report_selected_authority_class': 'explicit_report_override',
    'report_pointer_resolution_mode': 'explicit_report_override',
    'report_pointer_path': '',
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

summary_targeted_subset_excluded = {
    'selected_check_mode': 'targeted_subset',
    'selected_check_dependency_mode': 'report_independent_targeted_subset',
    'selected_check_names': ['scripts/validate_issue_register_consistency.py'],
}
readiness._hydrate_required_gate_bundle_summary(
    summary_targeted_subset_excluded,
    repo_root=repo_root,
    receipt_path=str(receipt_path),
    receipt_probe_path=str(probe_path),
)
readiness.materialize_targeted_subset_selected_check_scope_exclusions(
    summary_targeted_subset_excluded,
    summary_capture_scripts=readiness.SUMMARY_CAPTURE_SCRIPTS,
    structured_summary_capture_specs=readiness.STRUCTURED_SUMMARY_CAPTURE_SPECS,
)
assert summary_targeted_subset_excluded['required_gate_bundle']['bundle_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['projection_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['projection_stale_reasons'] == [], summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['scope_class'] == 'bounded_targeted_subset_exclusion', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['scope_reason'] == 'required_gate_bundle_out_of_scope_for_targeted_subset', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_selected_path'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_logical_identity_key'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_selection_mode'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_selected_authority_class'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_pointer_resolution_mode'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_bundle']['report_pointer_path'] == '', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['selected_check_scope_projection']['status'] == 'PASS_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['selected_check_scope_projection']['scope_class'] == 'bounded_targeted_subset_exclusion', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['selected_check_scope_projection']['scope_reason'] == 'selected_check_out_of_scope_for_targeted_subset', summary_targeted_subset_excluded
assert 'identity_codex_launcher' in summary_targeted_subset_excluded['selected_check_scope_projection']['excluded_summary_keys'], summary_targeted_subset_excluded
assert 'identity_experience_writeback' in summary_targeted_subset_excluded['selected_check_scope_projection']['excluded_summary_keys'], summary_targeted_subset_excluded
assert 'release_plane_cloud_evidence' in summary_targeted_subset_excluded['selected_check_scope_projection']['excluded_summary_keys'], summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['identity_codex_launcher']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['identity_experience_writeback']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['runtime_file_boundary_governance']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_surface_drift']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['runtime_summary_surface_governance_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_one_look_topology_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_repo_global_closure_topology_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_active_runtime_closure_topology_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_terminal_truth_bridge_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_governance_probe_topology_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_readiness_post_closure_adjudication_topology_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['required_gate_surface_drift_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['active_execution_report_pointer_locality_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['strict_live_active_pointer_locality_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['strict_live_contract_resolution_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['execution_report_selection_convergence_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['identity_codex_launcher_convergence_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['identity_transport_fleet_closure_convergence_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['active_runtime_pack_closure_convergence_probe']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_plane_cloud_evidence']['status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_plane_cloud_evidence']['conditions']['required_checks_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['release_cloud_evidence_adapter']['release_cloud_evidence_adapter_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
summary_targeted_subset_excluded['terminal_truth_boundary_projection'] = {
    'terminal_truth_boundary_projection_status': 'SKIPPED_NOT_REQUIRED',
    'repair_lane_status': 'SKIPPED_NOT_REQUIRED',
    'terminal_truth_observation_status': 'SKIPPED_NOT_REQUIRED',
}
readiness._hydrate_one_look_projection(summary_targeted_subset_excluded)
expected_targeted_subset_one_look = build_release_readiness_one_look_projection(
    summary_targeted_subset_excluded
)
assert summary_targeted_subset_excluded['one_look'] == expected_targeted_subset_one_look, summary_targeted_subset_excluded
expected_foundational_one_look = build_release_readiness_foundational_one_look_projection(
    summary_targeted_subset_excluded
)
for field_name, expected_value in expected_foundational_one_look.items():
    assert summary_targeted_subset_excluded['one_look'][field_name] == expected_value, summary_targeted_subset_excluded
expected_support_preflight_one_look = build_release_readiness_support_preflight_one_look_projection(
    summary_targeted_subset_excluded
)
for field_name, expected_value in expected_support_preflight_one_look.items():
    assert summary_targeted_subset_excluded['one_look'][field_name] == expected_value, summary_targeted_subset_excluded
expected_selected_check_scope_one_look = build_release_readiness_selected_check_scope_one_look_projection(
    summary_targeted_subset_excluded['selected_check_scope_projection']
)
for field_name, expected_value in expected_selected_check_scope_one_look.items():
    assert summary_targeted_subset_excluded['one_look'][field_name] == expected_value, summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['one_look']['selected_check_scope_projection_status'] == 'PASS_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['one_look']['release_cloud_evidence_adapter_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['one_look']['identity_experience_writeback_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded
assert summary_targeted_subset_excluded['one_look']['required_gate_bundle_projection_status'] == 'SKIPPED_NOT_REQUIRED', summary_targeted_subset_excluded

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
assert summary_observed['required_gate_bundle']['report_logical_identity_key'] == base_payload['report_logical_identity_key'], summary_observed
assert summary_observed['required_gate_bundle']['report_selection_mode'] == 'explicit_report_override', summary_observed
assert summary_observed['required_gate_bundle']['report_selected_authority_class'] == 'explicit_report_override', summary_observed
assert summary_observed['required_gate_bundle']['report_pointer_resolution_mode'] == 'explicit_report_override', summary_observed
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
    'executable_surface_runtime_literal_lock': {
        'status': 'PASS_REQUIRED',
        'violation_count': 0,
    },
    'issue_register_consistency': {
        'status': 'PASS_REQUIRED',
        'current_issue_horizon': 'ISSUE-039',
    },
    'protocol_broadcast_doc_control': {
        'status': 'PASS_REQUIRED',
        'subdomain_id': 'broadcast',
    },
    'protocol_governed_subdomain_doc_control_registry': {
        'status': 'PASS_REQUIRED',
        'subdomain_count': 1,
    },
    'identity_experience_writeback': {
        'status': 'PASS_REQUIRED',
        'report_selection_mode': 'active_execution_pointer',
        'report_selected_authority_class': 'active_execution_pointer_pack_local_report',
        'report_pointer_resolution_mode': 'pointer_candidate_root_report',
        'writeback_status': 'WRITTEN',
    },
    'terminal_truth_boundary_outer_surface_e2e_probe': {
        'status': 'PASS_REQUIRED',
    },
    'runtime_summary_surface_governance_probe': {
        'status': 'PASS_REQUIRED',
    },
    'release_readiness_one_look_topology_probe': {
        'status': 'PASS_REQUIRED',
    },
    'release_readiness_repo_global_closure_topology_probe': {
        'status': 'PASS_REQUIRED',
        'positive_validator_output': '/tmp/release-readiness-repo-global-closure-topology-positive.json',
    },
    'release_readiness_active_runtime_closure_topology_probe': {
        'status': 'PASS_REQUIRED',
        'positive_validator_output': '/tmp/release-readiness-active-runtime-closure-topology-positive.json',
    },
    'release_readiness_terminal_truth_bridge_probe': {
        'status': 'PASS_REQUIRED',
        'positive_validator_output': '/tmp/release-readiness-terminal-truth-bridge-positive.json',
        'bridge_case_count': 2,
        'bridge_cases': ['clean_terminal_truth', 'review_required_execution_closure'],
        'seeded_identity_ids': [
            'release-readiness-terminal-truth-bridge-clean-e2e',
            'release-readiness-terminal-truth-bridge-review-e2e',
        ],
    },
    'release_readiness_governance_probe_topology_probe': {
        'status': 'PASS_REQUIRED',
    },
    'release_readiness_post_closure_adjudication_topology_probe': {
        'status': 'PASS_REQUIRED',
        'positive_validator_output': '/tmp/release-readiness-post-closure-adjudication-topology-positive.json',
    },
    'required_gate_surface_drift_probe': {
        'status': 'PASS_REQUIRED',
    },
    'active_execution_report_pointer_locality_probe': {
        'status': 'PASS_REQUIRED',
        'external_pointer_rejection_status': 'PASS_REQUIRED',
        'external_pointer_resolution_mode': 'external_pointer_report_rejected',
        'external_pointer_selection_mode': 'candidate_root_latest_report',
        'external_pointer_selected_report_authority_class': 'candidate_root_latest_pack_local_report',
        'external_pointer_rejected_selected_report': '/tmp/clone-pack/runtime/reports/probe.json',
        'pack_local_pointer_authority_status': 'PASS_REQUIRED',
        'pack_local_pointer_resolution_mode': 'pointer_candidate_root_report',
        'pack_local_pointer_selection_mode': 'active_execution_pointer',
        'pack_local_pointer_selected_report_authority_class': 'active_execution_pointer_pack_local_report',
        'pack_local_pointer_selected_report': '/tmp/clone-pack/runtime/reports/probe.json',
    },
    'strict_live_active_pointer_locality_probe': {
        'status': 'PASS_REQUIRED',
        'external_pointer_rejection_status': 'PASS_REQUIRED',
        'report_name_rehome_status': 'PASS_REQUIRED',
        'candidate_root_binding_status': 'PASS_REQUIRED',
        'external_pointer_resolution_mode': 'external_pointer_report_rejected',
        'rehome_resolution_mode': 'pointer_report_name_rehomed_candidate_root',
        'candidate_root_resolution_mode': 'pointer_candidate_root_report',
    },
    'strict_live_contract_resolution_probe': {
        'status': 'PASS_REQUIRED',
        'locality_false_green_block_status': 'PASS_REQUIRED',
        'sample_green_failclose_status': 'PASS_REQUIRED',
        'backfill_canonicalization_status': 'PASS_REQUIRED',
    },
    'execution_report_selection_convergence_probe': {
        'status': 'PASS_REQUIRED',
        'selected_report_path': '/tmp/probe-report.json',
        'candidate_count': 1,
        'freshness_status': 'PASS_REQUIRED',
        'baseline_status': 'PASS_REQUIRED',
        'run_id_selection_strategy': 'primary_execution_report_candidate',
    },
    'identity_codex_launcher_convergence_probe': {
        'status': 'PASS_REQUIRED',
        'probe_context_status': 'PASS_REQUIRED',
        'metadata_hygiene_apply_status': 'PASS_REQUIRED',
        'truth_sync_apply_status': 'PASS_REQUIRED',
        'repo_catalog_rejection_status': 'PASS_REQUIRED',
        'repaired_identity_count': 1,
    },
    'identity_transport_fleet_closure_convergence_probe': {
        'status': 'PASS_REQUIRED',
        'workspace_checked_identity_count': 1,
        'repo_inclusive_violation_count': 1,
        'fleet_projection_policy_id': 'active_runtime_validator_fleet_closure_v1',
    },
    'active_runtime_pack_closure_convergence_probe': {
        'status': 'PASS_REQUIRED',
        'workspace_checked_identity_count': 1,
        'repo_inclusive_violation_count': 1,
        'pack_scan_policy_id': 'active_runtime_pack_closure_scan_v1',
    },
    'release_readiness_summary_binding_probe': {
        'status': 'PASS_REQUIRED',
    },
    'release_readiness_continuation_probe': {
        'status': 'PASS_REQUIRED',
    },
    'release_plane_context_resolution_probe': {
        'status': 'PASS_REQUIRED',
    },
    'active_execution_report_pointer_locality_probe': {
        'status': 'PASS_REQUIRED',
        'external_pointer_rejection_status': 'PASS_REQUIRED',
        'external_pointer_resolution_mode': 'external_pointer_report_rejected',
        'external_pointer_selection_mode': 'candidate_root_latest_report',
        'external_pointer_selected_report_authority_class': 'candidate_root_latest_pack_local_report',
        'external_pointer_rejected_selected_report': '/tmp/clone-pack/runtime/reports/probe.json',
        'pack_local_pointer_authority_status': 'PASS_REQUIRED',
        'pack_local_pointer_resolution_mode': 'pointer_candidate_root_report',
        'pack_local_pointer_selection_mode': 'active_execution_pointer',
        'pack_local_pointer_selected_report_authority_class': 'active_execution_pointer_pack_local_report',
        'pack_local_pointer_selected_report': '/tmp/clone-pack/runtime/reports/probe.json',
    },
}

repo_global_checked_counts = {
    summary_key: index + 4
    for index, summary_key in enumerate(RELEASE_READINESS_REPO_GLOBAL_ACTIVE_RUNTIME_SUMMARY_KEYS)
}
for summary_key, _one_look_field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS:
    row = summary_release_projection.setdefault(summary_key, {})
    row.setdefault('status', 'PASS_REQUIRED')
    if summary_key in repo_global_checked_counts:
        row.setdefault('checked_identity_count', repo_global_checked_counts[summary_key])
        row.setdefault('violation_count', 0)

summary_release_projection['required_gate_bundle'] = dict(summary_observed['required_gate_bundle'])
summary_release_projection['required_gate_bundle_scan_probe'] = dict(summary_observed['required_gate_bundle_scan_probe'])
readiness._hydrate_one_look_projection(summary_release_projection)
expected_release_projection_one_look = build_release_readiness_one_look_projection(
    summary_release_projection
)
assert summary_release_projection['one_look'] == expected_release_projection_one_look, summary_release_projection
expected_release_foundational_one_look = build_release_readiness_foundational_one_look_projection(
    summary_release_projection
)
for field_name, expected_value in expected_release_foundational_one_look.items():
    assert summary_release_projection['one_look'][field_name] == expected_value, summary_release_projection
expected_release_support_preflight_one_look = build_release_readiness_support_preflight_one_look_projection(
    summary_release_projection
)
for field_name, expected_value in expected_release_support_preflight_one_look.items():
    assert summary_release_projection['one_look'][field_name] == expected_value, summary_release_projection
expected_release_cloud_one_look = build_release_readiness_release_cloud_evidence_one_look_projection(
    summary_release_projection['release_plane_cloud_evidence'],
    summary_release_projection['release_cloud_evidence_adapter'],
)
for field_name, expected_value in expected_release_cloud_one_look.items():
    assert summary_release_projection['one_look'][field_name] == expected_value, summary_release_projection
assert summary_release_projection['one_look']['release_plane_required_checks_status'] == 'PASS', summary_release_projection
assert summary_release_projection['one_look']['control_plane_materialized_promotion_ready'] is True, summary_release_projection
assert summary_release_projection['one_look']['required_gate_bundle_scan_probe_status'] == 'FAIL_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['active_execution_report_pointer_external_resolution_mode'] == 'external_pointer_report_rejected', summary_release_projection
assert summary_release_projection['one_look']['execution_report_selection_convergence_candidate_count'] == 1, summary_release_projection
assert summary_release_projection['one_look']['release_readiness_one_look_topology_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_repo_global_closure_topology_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_active_runtime_closure_topology_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_terminal_truth_bridge_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_governance_probe_topology_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_post_closure_adjudication_topology_probe_status'] == 'PASS_REQUIRED', summary_release_projection
assert summary_release_projection['one_look']['release_readiness_summary_binding_probe_status'] == 'PASS_REQUIRED', summary_release_projection
for summary_key, one_look_field in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SUMMARY_BINDINGS:
    assert summary_release_projection['one_look'][one_look_field] == 'PASS_REQUIRED', summary_release_projection
    if summary_key in repo_global_checked_counts:
        assert (
            summary_release_projection['one_look'][f'{summary_key}_checked_identity_count']
            == repo_global_checked_counts[summary_key]
        ), summary_release_projection
        assert summary_release_projection['one_look'][f'{summary_key}_violation_count'] == 0, summary_release_projection

checkpoint_path = (tmp_root / 'release-readiness-checkpoint.json').resolve()
checkpoint_summary = {
    'identity_id': 'probe-identity',
    'catalog': str(repo_root / 'identity' / 'catalog' / 'identities.yaml'),
    'lane_context': {
        'work_layer': 'instance',
        'source_layer': 'project',
    },
    'command_execution': {
        'executed_command_count': 3,
        'failed_command_count': 0,
        'failed_scripts': [],
        'first_failed_script': '',
        'last_completed_script': 'scripts/validate_fixture_runtime_boundary.py',
    },
}
checkpoint_summary['surface_governance'] = build_governed_runtime_summary_surface_payload(
    'release_readiness_summary'
)
for marker in RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
for marker in RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
for marker in RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
for marker in RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
for marker in RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
for marker in RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS:
    assert marker in checkpoint_summary['surface_governance']['operational_constraints'], checkpoint_summary
readiness._checkpoint_release_readiness_summary(
    checkpoint_summary,
    summary_out=str(checkpoint_path),
    phase='preflight',
    current_check_name='scripts/validate_identity_session_refresh_status.py',
    current_check_state='running',
    phase_step_index=8,
    phase_step_total=8,
)
checkpoint_doc = json.loads(checkpoint_path.read_text(encoding='utf-8'))
assert checkpoint_doc['summary_lifecycle_status'] == 'IN_PROGRESS', checkpoint_doc
assert checkpoint_doc['summary_checkpoint_kind'] == 'checkpoint', checkpoint_doc
assert checkpoint_doc['summary_progress']['phase'] == 'preflight', checkpoint_doc
assert checkpoint_doc['summary_progress']['current_check_name'] == 'scripts/validate_identity_session_refresh_status.py', checkpoint_doc
assert checkpoint_doc['summary_progress']['current_check_state'] == 'running', checkpoint_doc
assert checkpoint_doc['summary_progress']['phase_step_index'] == 8, checkpoint_doc
assert checkpoint_doc['summary_progress']['phase_step_total'] == 8, checkpoint_doc
assert checkpoint_doc['summary_progress']['last_completed_check_name'] == 'scripts/validate_fixture_runtime_boundary.py', checkpoint_doc

stable_resume_source = capture_governed_runtime_summary_resume_source(
    str(checkpoint_path),
    summary_out=str(checkpoint_path),
)
assert stable_resume_source['resume_capture_mode'] == 'stable_prewrite_snapshot', stable_resume_source
assert stable_resume_source['same_path_as_summary_out'] is True, stable_resume_source
assert stable_resume_source['resume_doc']['summary_progress']['phase'] == 'preflight', stable_resume_source

# Simulate an in-place summary rewrite before resume derivation; the captured source must remain stable.
overwrite_summary = {
    'identity_id': 'probe-identity',
    'catalog': str(repo_root / 'identity' / 'catalog' / 'identities.yaml'),
    'lane_context': {
        'work_layer': 'instance',
        'source_layer': 'project',
    },
    'command_execution': {
        'executed_command_count': 4,
        'failed_command_count': 0,
        'failed_scripts': [],
        'first_failed_script': '',
        'last_completed_script': 'scripts/validate_fixture_runtime_boundary.py',
    },
}
overwrite_summary['surface_governance'] = build_governed_runtime_summary_surface_payload(
    'release_readiness_summary'
)
readiness._checkpoint_release_readiness_summary(
    overwrite_summary,
    summary_out=str(checkpoint_path),
    phase='bootstrap',
    current_check_name='',
    current_check_state='idle',
    phase_step_index=0,
    phase_step_total=8,
)
overwritten_doc = json.loads(checkpoint_path.read_text(encoding='utf-8'))
assert overwritten_doc['summary_progress']['phase'] == 'bootstrap', overwritten_doc

stable_resume_projection = derive_governed_runtime_summary_resume_projection(
    [
        'scripts/validate_identity_protocol.py',
        'scripts/validate_actor_session_multibinding_concurrency.py',
        'scripts/validate_identity_session_refresh_status.py',
        'scripts/validate_identity_switch_closure_semantics.py',
    ],
    stable_resume_source['resume_doc'],
    resumable_phase='preflight',
)
assert stable_resume_projection['resume_projection_status'] == 'PASS_REQUIRED', stable_resume_projection
assert stable_resume_projection['resume_reason'] == 'resume_from_running_check', stable_resume_projection
assert stable_resume_projection['resume_start_index'] == 2, stable_resume_projection

final_summary = {
    'identity_id': 'probe-identity',
    'catalog': str(repo_root / 'identity' / 'catalog' / 'identities.yaml'),
    'lane_context': {
        'work_layer': 'instance',
        'source_layer': 'project',
    },
    'command_execution': {
        'executed_command_count': 4,
        'failed_command_count': 0,
        'failed_scripts': [],
        'first_failed_script': '',
        'last_completed_script': 'scripts/validate_identity_session_refresh_status.py',
    },
}
final_summary['surface_governance'] = build_governed_runtime_summary_surface_payload(
    'release_readiness_summary'
)
final_rc = readiness._finalize_release_readiness_summary(
    final_summary,
    summary_out=str(checkpoint_path),
    exit_code=0,
    execution_report='',
    health_report_dir=str(tmp_root / 'health-report'),
    required_gate_bundle_receipt='',
    required_gate_bundle_receipt_probe='',
    repo_root=repo_root,
)
assert final_rc == 0, final_rc
final_doc = json.loads(checkpoint_path.read_text(encoding='utf-8'))
assert final_doc['summary_lifecycle_status'] == 'FINALIZED', final_doc
assert final_doc['summary_checkpoint_kind'] == 'final', final_doc
assert final_doc['release_readiness_status'] == 'PASS_REQUIRED', final_doc
assert final_doc['summary_progress']['phase'] == 'finalized', final_doc
assert final_doc['summary_progress']['current_check_name'] == '', final_doc
assert final_doc['summary_progress']['last_completed_check_name'] == 'scripts/validate_identity_session_refresh_status.py', final_doc

resume_projection = derive_governed_runtime_summary_resume_projection(
    [
        'scripts/validate_identity_protocol.py',
        'scripts/validate_actor_session_multibinding_concurrency.py',
        'scripts/validate_identity_session_refresh_status.py',
        'scripts/validate_identity_switch_closure_semantics.py',
    ],
    checkpoint_doc,
    resumable_phase='preflight',
)
assert resume_projection['resume_projection_status'] == 'PASS_REQUIRED', resume_projection
assert resume_projection['resume_reason'] == 'resume_from_running_check', resume_projection
assert resume_projection['resume_start_index'] == 2, resume_projection
assert resume_projection['resume_start_check_name'] == 'scripts/validate_identity_session_refresh_status.py', resume_projection
assert resume_projection['resume_skipped_check_count'] == 2, resume_projection

final_resume_projection = derive_governed_runtime_summary_resume_projection(
    ['scripts/validate_identity_session_refresh_status.py'],
    final_doc,
    resumable_phase='finalized',
)
assert final_resume_projection['resume_projection_status'] == 'SKIPPED_NOT_REQUIRED', final_resume_projection
assert final_resume_projection['resume_reason'] == 'summary_already_finalized', final_resume_projection

post_execution_stage = readiness._build_post_execution_report_stage_checks(
    identity_id='probe-identity',
    catalog=str(repo_root / '.identity' / 'catalog.local.yaml'),
    execution_report='/tmp/probe-report.json',
    report_meta={},
    health_report_dir=str(tmp_root / 'health-report'),
    actor_id=probe_actor_id,
    session_id='run:probe-session',
    scope='USER',
    base='base-ref',
    head='head-ref',
    capability_activation_policy='inherit',
    expected_work_layer='instance',
    expected_source_layer='project',
)
preview_seq, selectable_post_execution_names = readiness._extend_selection_candidates_with_unique_script_names(
    [
        ['python3', 'scripts/validate_identity_capability_activation.py'],
        ['python3', 'scripts/validate_resolve_identity_context_default_local_catalog.py', '--json-only'],
    ],
    post_execution_stage,
)
assert 'scripts/validate_identity_prompt_activation.py' in selectable_post_execution_names, selectable_post_execution_names
assert 'scripts/validate_identity_prompt_lifecycle.py' in selectable_post_execution_names, selectable_post_execution_names
assert 'scripts/validate_identity_capability_activation.py' not in selectable_post_execution_names, selectable_post_execution_names

post_execution_projection = readiness._build_selected_check_projection(
    preview_seq,
    selected_check_names=('scripts/validate_identity_prompt_activation.py',),
)
assert post_execution_projection['missing_selected_check_names'] == [], post_execution_projection
assert post_execution_projection['selected_check_dependency_mode'] == 'requires_execution_report', post_execution_projection
assert post_execution_projection['execution_report_required'] is True, post_execution_projection

report_independent_projection = readiness._build_selected_check_projection(
    preview_seq,
    selected_check_names=('scripts/validate_resolve_identity_context_default_local_catalog.py',),
)
assert report_independent_projection['missing_selected_check_names'] == [], report_independent_projection
assert report_independent_projection['selected_check_dependency_mode'] == 'report_independent_targeted_subset', report_independent_projection
assert report_independent_projection['execution_report_required'] is False, report_independent_projection

repo_global_projection = readiness._build_selected_check_projection(
    preview_seq + [['python3', 'scripts/validate_executable_surface_runtime_literal_lock.py', '--json-only']],
    selected_check_names=('scripts/validate_executable_surface_runtime_literal_lock.py',),
)
assert repo_global_projection['missing_selected_check_names'] == [], repo_global_projection
assert repo_global_projection['selected_check_dependency_mode'] == 'report_independent_targeted_subset', repo_global_projection
assert repo_global_projection['execution_report_required'] is False, repo_global_projection

probe_report_run_token = 'identity-upgrade-exec-probe-summary-binding'
probe_execution_report = (
    f'../.identity/probe/runtime/reports/{probe_report_run_token}.json'
)

report_derived_token = readiness._derive_bundle_run_token(
    required_gates_run_id='',
    execution_report=probe_execution_report,
    session_id='run:probe-session',
    identity_id='probe-identity',
)
assert report_derived_token == probe_report_run_token, report_derived_token
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
