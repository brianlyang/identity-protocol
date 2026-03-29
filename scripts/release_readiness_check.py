#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from actor_session_common import load_actor_binding, resolve_required_protocol_actor_id
from capability_activation_policy_common import (
    CAPABILITY_ACTIVATION_ENV_AUTH_ERROR_CODE,
    CAPABILITY_ACTIVATION_ENV_AUTH_FALLBACK_POLICY,
    capability_env_auth_fallback_eligible,
    normalize_capability_activation_policy,
    replace_capability_activation_policy,
)
from execution_report_selection_common import (
    collect_reports as collect_execution_reports,
    derive_runtime_run_token,
    derive_run_id_from_session_id,
    select_report as select_execution_report,
)
from gateway_wrapper_enforcement import run_gateway_wrapped_command as _run_gateway_wrapped_command
from governed_runtime_summary_checkpoint_common import (
    SUMMARY_CHECKPOINT_KIND_FINAL,
    SUMMARY_LIFECYCLE_FINALIZED,
    apply_governed_runtime_summary_checkpoint,
    capture_governed_runtime_summary_resume_source,
    derive_governed_runtime_summary_resume_projection,
    write_governed_runtime_summary_checkpoint,
)
from health_report_experience_writeback_projection_common import (
    build_health_report_experience_writeback_closure_projection as build_health_report_experience_writeback_closure_projection_shared,
)
from protocol_infra_contract import (
    build_required_gate_bundle_cmd,
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
    HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
    VALIDATOR_ACTOR_ID_REQUIRED_SCRIPTS,
    VALIDATOR_SESSION_ID_REQUIRED_SCRIPTS,
)
from primary_execution_report_common import latest_prompt_bound_primary_execution_report_from_roots
from release_cloud_evidence_projection_common import (
    build_release_cloud_evidence_adapter_projection,
    build_release_plane_cloud_evidence_summary_projection,
)
from release_readiness_active_runtime_closure_projection_common import (
    release_readiness_active_runtime_closure_capture_script_map,
    release_readiness_active_runtime_closure_structured_capture_specs,
    release_readiness_active_runtime_closure_summary_defaults,
)
from release_readiness_repo_global_closure_projection_common import (
    release_readiness_repo_global_closure_capture_script_map,
    release_readiness_repo_global_closure_structured_capture_specs,
    release_readiness_repo_global_closure_summary_defaults,
)
from release_readiness_governance_probe_projection_common import (
    release_readiness_governance_probe_capture_script_map,
    release_readiness_governance_probe_structured_capture_specs,
    release_readiness_governance_probe_summary_defaults,
)
from release_readiness_one_look_projection_common import (
    build_release_readiness_one_look_projection,
)
from release_readiness_required_gate_bundle_scope_common import (
    build_scope_excluded_required_gate_bundle_summary,
    targeted_subset_excludes_required_gate_bundle,
)
from release_readiness_selected_check_scope_common import (
    materialize_targeted_subset_selected_check_scope_exclusions,
)
from required_contract_coverage_projection_common import build_required_contract_coverage_projection
from required_gate_bundle_projection_common import build_required_gate_bundle_target_projection
from required_gate_report_authority_common import REQUIRED_GATE_REPORT_AUTHORITY_FIELDS
from resolve_release_plane_cloud_evidence import resolve_release_plane_runtime_inputs
from response_stamp_common import (
    DEFAULT_WORK_LAYER,
    EXECUTION_REPLY_IDENTITY_COHERENCE_VALIDATOR_ID,
    HEADSTAMP_RECURRENCE_CLOSURE_VALIDATOR_ID,
    IDENTITY_RESPONSE_STAMP_BLOCKER_RECEIPT_VALIDATOR_ID,
    IDENTITY_RESPONSE_STAMP_RENDER_SCRIPT,
    IDENTITY_RESPONSE_STAMP_VALIDATOR_ID,
    LAYER_INTENT_RESOLUTION_VALIDATOR_ID,
    REPLY_IDENTITY_CONTEXT_FIRST_LINE_VALIDATOR_ID,
    SEND_TIME_REPLY_GATE_VALIDATOR_ID,
    resolve_layer_intent,
)
from runtime_temp_path_common import named_temp_root, runtime_temp_file
from terminal_truth_boundary_projection_common import (
    build_terminal_truth_boundary_projection_from_report,
)
from workspace_runtime_closure_command_common import (
    build_workspace_runtime_closure_checker_command,
    workspace_runtime_closure_checker_specs,
)

PROTOCOL_PUBLISH_SCRIPTS = {
    "scripts/validate_changelog_updated.py",
    "scripts/validate_protocol_handoff_coupling.py",
    "scripts/validate_release_metadata_sync.py",
    "scripts/validate_release_freeze_boundary.py",
}
POST_CLOSURE_GOVERNANCE_SCRIPTS = [
    ["python3", "scripts/validate_doc_command_surface_registry.py", "--json-only"],
    ["bash", "scripts/ci/run_doc_command_surface_probes_ci.sh"],
    ["python3", "scripts/docs_command_contract_check.py"],
    ["python3", "scripts/validate_control_plane_budget.py", "--json-only"],
    ["python3", "scripts/validate_control_plane_budget_sync.py", "--json-only"],
    ["python3", "scripts/validate_control_plane_status_sync.py", "--json-only"],
    ["python3", "scripts/materialize_control_plane_surfaces.py", "--json-only"],
    ["bash", "scripts/ci/run_control_plane_budget_sync_probes_ci.sh"],
    ["bash", "scripts/ci/run_control_plane_surface_materialization_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_doc_surface_governance_probes_ci.sh"],
    ["bash", "scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh"],
    ["bash", "scripts/ci/run_v16x_release_closure_summary_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_closure_control_plane_status_probes_ci.sh"],
    ["python3", "scripts/validate_issue_register_consistency.py", "--json-only"],
    ["python3", "scripts/validate_runtime_file_boundary_governance.py", "--json-only"],
    ["bash", "scripts/ci/run_identity_runtime_mode_guard_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_context_continuity_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_dialogue_retention_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_artifact_family_routing_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_weak_live_linkage_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh"],
    ["bash", "scripts/ci/run_terminal_truth_cleanliness_probes_ci.sh"],
    ["bash", "scripts/ci/run_contract_bootstrap_emitter_probes_ci.sh"],
    ["bash", "scripts/ci/run_post_execution_report_repair_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_feedback_sidecar_contract_probes_ci.sh"],
    ["bash", "scripts/ci/run_sidecar_cwd_parity_probes_ci.sh"],
    ["bash", "scripts/ci/run_required_gate_tuple_parity_probes_ci.sh"],
    ["bash", "scripts/ci/run_execution_report_selection_convergence_probes_ci.sh"],
    ["bash", "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh"],
    ["bash", "scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh"],
    ["bash", "scripts/ci/run_strict_live_contract_resolution_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_update_preflight_terminal_truth_split_probes_ci.sh"],
    ["bash", "scripts/ci/run_terminal_truth_boundary_projection_probes_ci.sh"],
    ["bash", "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_broadcast_delivery_probes_ci.sh"],
    ["python3", "scripts/validate_protocol_broadcast_doc_control.py", "--json-only"],
    ["bash", "scripts/ci/run_protocol_broadcast_doc_control_probes_ci.sh"],
    ["python3", "scripts/validate_protocol_governed_subdomain_doc_control_registry.py", "--json-only"],
    ["bash", "scripts/ci/run_protocol_governed_subdomain_doc_control_registry_probes_ci.sh"],
    ["python3", "scripts/validate_protocol_root_shared_primitive_adoption.py", "--json-only"],
    ["bash", "scripts/ci/run_protocol_root_shared_primitive_adoption_probes_ci.sh"],
    ["python3", "scripts/validate_protocol_repo_authority_exclusivity.py", "--json-only"],
    ["bash", "scripts/ci/run_protocol_repo_authority_exclusivity_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_communication_transport_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh"],
    ["bash", "scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh"],
    ["python3", "scripts/validate_executable_surface_runtime_literal_lock.py", "--json-only"],
    ["bash", "scripts/ci/run_executable_surface_runtime_literal_lock_probes_ci.sh"],
    ["python3", "scripts/validate_required_gate_surface_drift.py", "--json-only"],
    ["bash", "scripts/ci/run_protocol_repo_runtime_shadow_boundary_probes_ci.sh"],
    ["bash", "scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh"],
    ["python3", "scripts/validate_resolve_identity_context_default_local_catalog.py", "--json-only"],
    ["bash", "scripts/ci/run_repair_contract_backfill_status_profile_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_constitutional_spine_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_gateway_admissibility_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_precedence_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh"],
    ["bash", "scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh"],
    ["bash", "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_one_look_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_one_look_topology_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_repo_global_closure_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_active_runtime_closure_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_terminal_truth_bridge.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_governance_probe_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh"],
    ["python3", "scripts/validate_release_readiness_post_closure_adjudication_topology.py", "--json-only"],
    ["bash", "scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"],
    ["bash", "scripts/ci/run_three_plane_health_projection_probes_ci.sh"],
    ["bash", "scripts/ci/run_full_scan_required_gate_projection_probes_ci.sh"],
    ["bash", "scripts/ci/run_full_scan_health_projection_probes_ci.sh"],
    ["bash", "scripts/ci/run_required_gate_surface_drift_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_readiness_continuation_probes_ci.sh"],
    ["bash", "scripts/ci/run_release_plane_context_resolution_probes_ci.sh"],
    ["bash", "scripts/ci/run_workbook_control_plane_probes_ci.sh"],
    ["bash", "scripts/ci/run_workbook_family_scaffold_probes_ci.sh"],
]
BUNDLE_RUNNER_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
FINAL_EMIT_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
FAILCLOSE_PLUGIN_PROJECTION_SCRIPT = "scripts/validate_failclose_plugin_projection.py"
FULL_SCAN_TARGET_REGRESSION_SCRIPT = "scripts/validate_full_scan_target_regression.py"
PROTOCOL_ROOT = Path(__file__).resolve().parent.parent
REPO_CATALOG_REL = "identity/catalog/identities.yaml"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_UNKNOWN = "UNKNOWN"
READINESS_PREFLIGHT_COMMAND_COUNT = 8
SUMMARY_CAPTURE_SCRIPTS: dict[str, str] = {
    "scripts/validate_doc_command_surface_registry.py": "doc_command_surface_registry",
    "scripts/validate_control_plane_budget.py": "control_plane_budget",
    "scripts/validate_control_plane_budget_sync.py": "control_plane_budget_sync",
    "scripts/validate_control_plane_status_sync.py": "control_plane_status_sync",
    "scripts/materialize_control_plane_surfaces.py": "control_plane_surface_materialization",
    "scripts/validate_protocol_root_shared_primitive_adoption.py": "protocol_root_shared_primitive_adoption",
    "scripts/validate_protocol_repo_authority_exclusivity.py": "protocol_repo_authority_exclusivity",
    **release_readiness_repo_global_closure_capture_script_map(),
    "scripts/validate_resolve_identity_context_default_local_catalog.py": "resolve_identity_context_local_catalog_closure",
    "scripts/validate_required_contract_coverage.py": "required_contract_coverage",
    "scripts/validate_required_gate_recurrence_escalator.py": "required_gate_recurrence",
    "scripts/validate_required_gate_tuple_parity.py": "required_gate_tuple_parity",
    "scripts/validate_release_plane_cloud_evidence.py": "release_plane_cloud_evidence",
    FAILCLOSE_PLUGIN_PROJECTION_SCRIPT: "failclose_plugin_projection",
    FULL_SCAN_TARGET_REGRESSION_SCRIPT: "full_scan_target_regression",
    **release_readiness_active_runtime_closure_capture_script_map(),
    **release_readiness_governance_probe_capture_script_map(),
}
STRUCTURED_SUMMARY_CAPTURE_SPECS: dict[str, dict[str, tuple[str, ...]]] = {
    "doc_command_surface_registry": {
        "status_fields": ("doc_command_surface_registry_status",),
        "error_fields": ("error_code",),
        "keep_fields": ("mode_count", "doc_row_count", "self_prefixes", "stale_reasons"),
    },
    "control_plane_budget": {
        "status_fields": ("control_plane_budget_status",),
        "error_fields": ("error_code",),
        "keep_fields": ("warn_violation_count", "fail_violation_count", "stale_reasons"),
    },
    "control_plane_budget_sync": {
        "status_fields": ("control_plane_budget_sync_status",),
        "error_fields": ("error_code",),
        "keep_fields": ("mismatch_count", "stale_reasons"),
    },
    "control_plane_status_sync": {
        "status_fields": ("control_plane_status_sync_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "mismatch_count",
            "live_control_plane_status",
            "file_control_plane_status",
            "stale_reasons",
        ),
    },
    "control_plane_surface_materialization": {
        "status_fields": ("materialize_control_plane_surfaces_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "control_plane_status",
            "promotion_ready",
            "budget_validation_status",
            "budget_sync_status",
            "status_sync_status",
            "budget_sync_mismatch_count",
            "status_sync_mismatch_count",
            "stale_reasons",
        ),
    },
    "required_gate_recurrence": {
        "status_fields": ("required_gate_recurrence_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "escalation_level",
            "error_family",
            "receipt_path",
            "state_path",
            "stale_reasons",
            "active_fail_families",
        ),
    },
    "required_gate_tuple_parity": {
        "status_fields": ("required_gate_tuple_parity_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "receipts_checked",
            "parity_contract_reasons",
            "missing_fields",
            "mismatches",
            "scope_groups",
        ),
    },
    "protocol_root_shared_primitive_adoption": {
        "status_fields": ("protocol_root_shared_primitive_adoption_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "root_validator_count",
            "primitive_violation_count",
            "primitive_violation_file_count",
            "primitive_adoption_row_count",
            "row_family_projection_assignment_violation_count",
            "scan_error_count",
            "stale_reasons",
        ),
    },
    "protocol_repo_authority_exclusivity": {
        "status_fields": ("protocol_repo_authority_exclusivity_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "protocol_repo_root",
            "protocol_repo_git_top_level",
            "protocol_repo_root_matches_git_top_level",
            "enclosing_host_git_root_count",
            "host_container_present",
            "host_container_authority_status",
            "cwd_resolution_drift_present",
            "stale_reasons",
        ),
    },
    "resolve_identity_context_local_catalog_closure": {
        "status_fields": ("resolve_identity_context_local_catalog_closure_status",),
        "error_fields": ("error_code",),
        "keep_fields": (
            "resolve_identity_context_default_local_catalog_status",
            "resolve_identity_context_explicit_local_catalog_precedence_status",
            "local_catalog_path",
            "repo_catalog_path",
            "explicit_local_catalog_runtime_defaults_ref",
            "stale_reasons",
        ),
    },
    **release_readiness_repo_global_closure_structured_capture_specs(),
    **release_readiness_active_runtime_closure_structured_capture_specs(),
    **release_readiness_governance_probe_structured_capture_specs(),
}

LAYER_INTENT_VALIDATOR_SCRIPTS = (
    LAYER_INTENT_RESOLUTION_VALIDATOR_ID,
    REPLY_IDENTITY_CONTEXT_FIRST_LINE_VALIDATOR_ID,
    SEND_TIME_REPLY_GATE_VALIDATOR_ID,
    EXECUTION_REPLY_IDENTITY_COHERENCE_VALIDATOR_ID,
    "scripts/validate_work_layer_gate_set_routing.py",
    "scripts/validate_protocol_feedback_bootstrap_ready.py",
    "scripts/validate_protocol_entry_candidate_bridge.py",
    "scripts/validate_protocol_inquiry_followup_chain.py",
)
LAYER_INTENT_AWARE_SCRIPTS = {
    IDENTITY_RESPONSE_STAMP_RENDER_SCRIPT,
    "scripts/final_emit_governed.py",
    *LAYER_INTENT_VALIDATOR_SCRIPTS,
}
EXPECTED_WORK_LAYER_VALIDATOR_SCRIPTS = set(LAYER_INTENT_VALIDATOR_SCRIPTS)
EXPECTED_SOURCE_LAYER_EXPECTED_FLAG_SCRIPTS = {
    LAYER_INTENT_RESOLUTION_VALIDATOR_ID,
    REPLY_IDENTITY_CONTEXT_FIRST_LINE_VALIDATOR_ID,
    SEND_TIME_REPLY_GATE_VALIDATOR_ID,
    EXECUTION_REPLY_IDENTITY_COHERENCE_VALIDATOR_ID,
}
EXPECTED_SOURCE_LAYER_DIRECT_FLAG_SCRIPTS = {
    "scripts/validate_protocol_feedback_bootstrap_ready.py",
    "scripts/validate_protocol_entry_candidate_bridge.py",
    "scripts/validate_protocol_inquiry_followup_chain.py",
    "scripts/validate_work_layer_gate_set_routing.py",
}


def _resolve_default_instance_layers(*, catalog: str, expected_work_layer: str, expected_source_layer: str) -> tuple[str, str]:
    return (
        str(expected_work_layer or "").strip().lower() or "instance",
        str(expected_source_layer or "").strip().lower() or _infer_source_layer_from_catalog_path(catalog),
    )


def _build_workspace_runtime_closure_checks(*, catalog: str) -> list[list[str]]:
    return [
        build_workspace_runtime_closure_checker_command(
            checker_id=spec.checker_id,
            catalog_path=catalog,
            json_only=True,
        )
        for spec in workspace_runtime_closure_checker_specs(families={"transport", "pack"})
    ]


def _build_instance_runtime_closure_checks(
    *,
    catalog: str,
    identity_id: str,
    expected_work_layer: str,
    expected_source_layer: str,
    include_weak_live_linkage: bool = True,
) -> list[list[str]]:
    work_layer_default, source_layer_default = _resolve_default_instance_layers(
        catalog=catalog,
        expected_work_layer=expected_work_layer,
        expected_source_layer=expected_source_layer,
    )
    seq = [
        [
            "python3",
            "scripts/validate_identity_codex_launcher.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        build_workspace_runtime_closure_checker_command(
            checker_id="scripts/check_identity_codex_launcher_migration_closure.py",
            catalog_path=catalog,
            json_only=True,
        ),
        [
            "python3",
            "scripts/validate_instance_script_manifest.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_instance_script_orchestration.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--work-layer",
            work_layer_default,
            "--source-layer",
            source_layer_default,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_route_script_receipt_join.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--work-layer",
            work_layer_default,
            "--source-layer",
            source_layer_default,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_route_execution_lane_admission.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--work-layer",
            work_layer_default,
            "--source-layer",
            source_layer_default,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_context_continuity.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_reentry_brief.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_reentry_consumption.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_context_continuity_receipts.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_retention.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_artifact_family_routing.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_broadcast_delivery.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_communication_transport.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
    ]
    if include_weak_live_linkage:
        seq.append(
            [
                "python3",
                "scripts/validate_identity_weak_live_linkage.py",
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                "readiness",
                "--json-only",
            ]
        )
        seq.append(
            [
                "python3",
                "scripts/validate_terminal_truth_cleanliness.py",
                "--catalog",
                catalog,
                "--repo-catalog",
                REPO_CATALOG_REL,
                "--identity-id",
                identity_id,
                "--operation",
                "readiness",
                "--json-only",
            ]
        )
    return seq


def _build_post_execution_report_stage_checks(
    *,
    identity_id: str,
    catalog: str,
    execution_report: str,
    report_meta: dict[str, Any] | None,
    health_report_dir: str,
    actor_id: str,
    session_id: str,
    scope: str,
    base: str,
    head: str,
    capability_activation_policy: str,
    expected_work_layer: str,
    expected_source_layer: str,
) -> list[list[str]]:
    report_meta = report_meta if isinstance(report_meta, dict) else {}
    work_layer = str(expected_work_layer or "").strip().lower() or "instance"
    source_layer = str(expected_source_layer or "").strip().lower() or _infer_source_layer_from_catalog_path(catalog)
    seq: list[list[str]] = [
        [
            "python3",
            "scripts/validate_writeback_continuity.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_post_execution_mandatory.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--operation",
            "readiness",
        ],
    ]
    health_report_cmd = [
        "python3",
        "scripts/collect_identity_health_report.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--operation",
        "readiness",
        "--execution-report",
        execution_report,
        "--actor-id",
        actor_id,
        "--session-id",
        session_id,
        "--out-dir",
        health_report_dir,
        "--enforce-pass",
    ]
    if scope:
        health_report_cmd.extend(["--scope", scope])
    seq.extend(
        [
            health_report_cmd,
            [
                "python3",
                "scripts/validate_identity_health_contract.py",
                "--identity-id",
                identity_id,
                "--report-dir",
                health_report_dir,
                "--require-pass",
            ],
            [
                "python3",
                "scripts/validate_identity_actor_health_profile.py",
                "--identity-id",
                identity_id,
                "--report-dir",
                health_report_dir,
                "--execution-report",
                execution_report,
                "--operation",
                "readiness",
                "--enforce-bound-report",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_reply_channel.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--operation",
                "readiness",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_bootstrap_ready.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--operation",
                "readiness",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_entry_candidate_bridge.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--operation",
                "readiness",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_inquiry_followup_chain.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--operation",
                "readiness",
                "--force-check",
                "--json-only",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_sidecar_contract.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--report",
                execution_report,
                "--operation",
                "readiness",
                "--enforce-blocking",
            ],
            [
                "python3",
                "scripts/validate_instance_base_repo_write_boundary.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--report",
                execution_report,
                "--operation",
                "readiness",
            ],
            [
                "python3",
                "scripts/validate_protocol_feedback_ssot_archival.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                "identity/catalog/identities.yaml",
                "--operation",
                "readiness",
            ],
            [
                "python3",
                "scripts/validate_identity_protocol_root_evidence.py",
                "--identity-id",
                identity_id,
                "--report",
                execution_report,
            ],
            [
                "python3",
                "scripts/validate_identity_mode_promotion_arbitration.py",
                "--identity-id",
                identity_id,
                "--base",
                base,
                "--head",
                head,
                "--report",
                execution_report,
            ],
            [
                "python3",
                "scripts/validate_identity_experience_writeback.py",
                "--repo-catalog",
                REPO_CATALOG_REL,
                "--local-catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--execution-report",
                execution_report,
                "--json-only",
            ],
        ]
    )
    permission_cmd = [
        "python3",
        "scripts/validate_identity_permission_state.py",
        "--identity-id",
        identity_id,
        "--report",
        execution_report,
    ]
    report_all_ok = _boolish(report_meta.get("all_ok"))
    report_writeback_status = str(report_meta.get("writeback_status", "")).strip().upper()
    report_permission_state = str(report_meta.get("permission_state", "")).strip().upper()
    if report_all_ok and report_writeback_status == "WRITTEN" and report_permission_state == "WRITEBACK_WRITTEN":
        permission_cmd.append("--require-written")
    seq.append(permission_cmd)
    seq.append(
        [
            "python3",
            "scripts/validate_identity_binding_tuple.py",
            "--identity-id",
            identity_id,
            "--report",
            execution_report,
        ]
    )
    seq.extend(
        _build_instance_runtime_closure_checks(
            catalog=catalog,
            identity_id=identity_id,
            expected_work_layer=expected_work_layer,
            expected_source_layer=expected_source_layer,
            include_weak_live_linkage=False,
        )
    )
    seq.extend(
        [
            [
                "python3",
                "scripts/validate_identity_capability_activation.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--repo-catalog",
                REPO_CATALOG_REL,
                "--activation-policy",
                capability_activation_policy,
                "--work-layer",
                work_layer,
                "--source-layer",
                source_layer,
                "--require-activated",
            ],
            [
                "python3",
                "scripts/validate_identity_prompt_activation.py",
                "--identity-id",
                identity_id,
                "--catalog",
                catalog,
                "--report",
                execution_report,
            ],
            [
                "python3",
                "scripts/validate_identity_prompt_lifecycle.py",
                "--identity-id",
                identity_id,
                "--report",
                execution_report,
            ],
        ]
    )
    return seq


def _build_response_stamp_blocker_receipt_checks(
    *,
    catalog: str,
    identity_id: str,
    receipt_specs: list[tuple[str, bool]],
) -> list[list[str]]:
    seq: list[list[str]] = []
    for receipt_path, json_only in receipt_specs:
        cmd = [
            "python3",
            IDENTITY_RESPONSE_STAMP_BLOCKER_RECEIPT_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--force-check",
            "--receipt",
            receipt_path,
        ]
        if json_only:
            cmd.append("--json-only")
        seq.append(cmd)
    return seq


def _run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    rc, _out, _err = _run_gateway_wrapped_command(cmd=cmd, protocol_root=PROTOCOL_ROOT)
    if rc != 0:
        print(f"[FAIL] command failed ({rc}): {' '.join(cmd)}")
        return rc
    return 0


def _run_capture(cmd: list[str]) -> tuple[int, str, str]:
    print(f"[RUN] {' '.join(cmd)}")
    rc, raw_out, raw_err = _run_gateway_wrapped_command(cmd=cmd, protocol_root=PROTOCOL_ROOT)
    out = raw_out.strip()
    err = raw_err.strip()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    if rc != 0:
        print(f"[FAIL] command failed ({rc}): {' '.join(cmd)}")
    return rc, out, err


def _replace_flag_value(cmd: list[str], flag: str, value: str) -> None:
    if flag in cmd:
        idx = cmd.index(flag)
        if idx + 1 < len(cmd):
            cmd[idx + 1] = str(value)
            return
    cmd.extend([flag, str(value)])


def _read_flag_value(cmd: list[str], flag: str) -> str:
    if flag in cmd:
        idx = cmd.index(flag)
        if idx + 1 < len(cmd):
            return _clean_str(cmd[idx + 1])
    return ""

def _derive_bundle_run_token(
    *,
    required_gates_run_id: str,
    execution_report: str,
    session_id: str,
    identity_id: str,
) -> str:
    return derive_runtime_run_token(
        explicit_run_id=_clean_str(required_gates_run_id),
        execution_report=_clean_str(execution_report),
        session_id=_clean_str(session_id),
        identity_id=_clean_str(identity_id),
        default_prefix="readiness",
    )


def _apply_bundle_passthrough_from_report(
    seq: list[list[str]],
    report_meta: dict[str, Any],
    report_selected_path: str,
) -> None:
    send_time_gate_status = str(report_meta.get("send_time_gate_status", "")).strip().upper() or "UNKNOWN"
    outlet_bypass_detected = "true" if _boolish(report_meta.get("outlet_bypass_detected")) else "false"
    final_emit_contract_status = str(report_meta.get("final_emit_contract_status", "")).strip().upper() or "UNKNOWN"
    final_emit_policy_mode = str(report_meta.get("final_emit_policy_mode", "")).strip() or "tool_choice_required"
    final_emit_schema_status = str(report_meta.get("final_emit_schema_status", "")).strip().upper() or "UNKNOWN"
    selected_report = str(report_selected_path or "").strip()
    for cmd in seq:
        if len(cmd) < 2 or cmd[1] not in {BUNDLE_RUNNER_SCRIPT, FAILCLOSE_PLUGIN_PROJECTION_SCRIPT}:
            continue
        _replace_flag_value(cmd, "--send-time-gate-status", send_time_gate_status)
        _replace_flag_value(cmd, "--outlet-bypass-detected", outlet_bypass_detected)
        _replace_flag_value(cmd, "--final-emit-contract-status", final_emit_contract_status)
        _replace_flag_value(cmd, "--final-emit-policy-mode", final_emit_policy_mode)
        _replace_flag_value(cmd, "--final-emit-schema-status", final_emit_schema_status)
        if selected_report:
            _replace_flag_value(cmd, "--report-selected-path", selected_report)


def _resolve_actor_session_id(
    *,
    catalog: str,
    identity_id: str,
    actor_id: str,
    explicit_session_id: str,
) -> tuple[str, str]:
    explicit = str(explicit_session_id or "").strip()
    if explicit:
        return explicit, "explicit_session_id"
    try:
        binding = load_actor_binding(
            Path(catalog).expanduser().resolve(),
            actor_id,
            identity_id=identity_id,
        )
    except Exception:
        binding = {}
    bound = str((binding or {}).get("session_id", "")).strip()
    if bound:
        return bound, "actor_binding_identity"
    return "", "binding_missing"


def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _infer_source_layer_from_catalog_path(catalog: str) -> str:
    try:
        text = str(Path(catalog).expanduser().resolve())
    except Exception:
        return "project"
    if "/.codex/.identity/" in text:
        return "global"
    if "/.identity/" in text:
        return "project"
    return "project"


def _parse_json_payload(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _git_rev(expr: str) -> str:
    p = subprocess.run(["git", "rev-parse", expr], check=True, capture_output=True, text=True)
    return p.stdout.strip()


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _safe_load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _command_check_name(cmd: list[str]) -> str:
    if len(cmd) >= 2:
        script = _clean_str(cmd[1])
        if script:
            return script
    if cmd:
        return _clean_str(cmd[0])
    return ""


def _filter_selected_checks(
    seq: list[list[str]],
    *,
    selected_check_names: tuple[str, ...],
) -> tuple[list[list[str]], list[str]]:
    if not selected_check_names:
        return seq, []
    available_names = {
        check_name
        for check_name in (_command_check_name(cmd) for cmd in seq)
        if check_name
    }
    requested_names = [name for name in selected_check_names if _clean_str(name)]
    missing_names = [name for name in requested_names if name not in available_names]
    if missing_names:
        return [], missing_names
    include_set = set(requested_names)
    filtered_seq = [cmd for cmd in seq if _command_check_name(cmd) in include_set]
    return filtered_seq, []


REPORT_DEPENDENT_FLAGS: tuple[str, ...] = (
    "--report",
    "--execution-report",
    "--report-selected-path",
)


def _command_requires_execution_report(cmd: list[str]) -> bool:
    return any(flag in cmd for flag in REPORT_DEPENDENT_FLAGS)


def _sequence_requires_execution_report(seq: list[list[str]]) -> bool:
    return any(_command_requires_execution_report(cmd) for cmd in seq)


def _build_selected_check_projection(
    seq: list[list[str]],
    *,
    selected_check_names: tuple[str, ...],
) -> dict[str, Any]:
    targeted_subset_mode = bool(selected_check_names)
    filtered_seq, missing_selected_check_names = _filter_selected_checks(
        seq,
        selected_check_names=selected_check_names,
    )
    selected_seq = filtered_seq if targeted_subset_mode else list(seq)
    selected_subset_requires_execution_report = _sequence_requires_execution_report(selected_seq)
    execution_report_required = (not targeted_subset_mode) or selected_subset_requires_execution_report
    if targeted_subset_mode:
        dependency_mode = (
            "requires_execution_report"
            if selected_subset_requires_execution_report
            else "report_independent_targeted_subset"
        )
    else:
        dependency_mode = "full_lane"
    return {
        "targeted_subset_mode": targeted_subset_mode,
        "filtered_seq": selected_seq,
        "missing_selected_check_names": missing_selected_check_names,
        "selected_check_count": len(selected_seq),
        "selected_subset_requires_execution_report": selected_subset_requires_execution_report,
        "execution_report_required": execution_report_required,
        "selected_check_dependency_mode": dependency_mode,
        "execution_report_resolution_mode": (
            "required"
            if execution_report_required
            else "skipped_not_required_targeted_subset"
        ),
    }


def _apply_selected_check_projection_summary(
    summary_payload: dict[str, Any],
    projection: dict[str, Any],
) -> None:
    summary_payload["selected_check_count"] = int(projection.get("selected_check_count", 0) or 0)
    missing_selected_check_names = projection.get("missing_selected_check_names", [])
    if isinstance(missing_selected_check_names, list) and missing_selected_check_names:
        summary_payload["selected_check_missing_names"] = missing_selected_check_names
    else:
        summary_payload.pop("selected_check_missing_names", None)
    summary_payload["selected_check_dependency_mode"] = str(
        projection.get("selected_check_dependency_mode", "unknown")
    ).strip() or "unknown"
    summary_payload["execution_report_resolution_mode"] = str(
        projection.get("execution_report_resolution_mode", "required")
    ).strip() or "required"


def _extend_selection_candidates_with_unique_script_names(
    base_seq: list[list[str]],
    extra_seq: list[list[str]],
) -> tuple[list[list[str]], set[str]]:
    merged_seq = list(base_seq)
    known_names = {
        check_name
        for check_name in (_command_check_name(cmd) for cmd in base_seq)
        if check_name
    }
    unique_extra_names: set[str] = set()
    for cmd in extra_seq:
        check_name = _command_check_name(cmd)
        if not check_name or check_name in known_names:
            continue
        merged_seq.append(cmd)
        known_names.add(check_name)
        unique_extra_names.add(check_name)
    return merged_seq, unique_extra_names


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        token = _clean_str(value)
        if token and token not in out:
            out.append(token)
    return out


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _latest_identity_report(report_dir: Path, *, prefix: str, identity_id: str) -> Path | None:
    if not report_dir.exists():
        return None
    rows = sorted(
        report_dir.glob(f"{prefix}-{identity_id}-*.json"),
        key=lambda candidate: candidate.stat().st_mtime,
        reverse=True,
    )
    for candidate in rows:
        if candidate.is_file():
            return candidate
    return None


def _build_health_report_experience_writeback_closure_projection(
    summary: dict[str, Any],
    *,
    identity_id: str,
    health_report_dir: str,
    execution_report: str,
) -> dict[str, Any]:
    boundary_projection = summary.get("terminal_truth_boundary_projection") or {}
    return build_health_report_experience_writeback_closure_projection_shared(
        identity_id=identity_id,
        health_report_dir=health_report_dir,
        execution_report=execution_report,
        command_execution=summary.get("command_execution") or {},
        selected_check_mode=_clean_str(summary.get("selected_check_mode")) or "full",
        selected_check_names=_clean_list(summary.get("selected_check_names")),
        boundary_experience_writeback_validation_status=_clean_str(
            boundary_projection.get("experience_writeback_validation_status")
        ).upper()
        or STATUS_UNKNOWN,
    )


def _first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        if key in payload:
            return payload.get(key)
    return ""


def _write_json(path_text: str, payload: dict[str, Any]) -> str:
    target = Path(path_text).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    else:
        target = target.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(target)


def _utc_now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_preflight(
    summary: dict[str, Any],
    *,
    name: str,
    rc: int,
    payload: dict[str, Any],
    status_fields: tuple[str, ...],
    error_fields: tuple[str, ...] = ("error_code",),
    keep_fields: tuple[str, ...] = (),
    extra: dict[str, Any] | None = None,
) -> None:
    preflight = summary.setdefault("preflight", {})
    status_value = _clean_str(_first_present(payload, status_fields)).upper() or (
        STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    )
    item: dict[str, Any] = {
        "status": status_value,
        "rc": int(rc),
        "error_code": _clean_str(_first_present(payload, error_fields)),
    }
    for field in keep_fields:
        if field in payload:
            item[field] = payload.get(field)
    if extra:
        item.update(extra)
    preflight[name] = item


def _record_preflight_skip(
    summary: dict[str, Any],
    *,
    name: str,
    reason: str,
    extra: dict[str, Any] | None = None,
) -> None:
    item: dict[str, Any] = {
        "status": STATUS_SKIPPED_NOT_REQUIRED,
        "rc": 0,
        "error_code": "",
        "skip_reason": _clean_str(reason),
    }
    if extra:
        item.update(extra)
    summary.setdefault("preflight", {})[name] = item


def _record_command_execution(summary: dict[str, Any], *, script: str, rc: int) -> None:
    command_execution = summary.setdefault(
        "command_execution",
        {
            "executed_command_count": 0,
            "failed_command_count": 0,
            "failed_scripts": [],
            "first_failed_script": "",
            "last_completed_script": "",
        },
    )
    command_execution["executed_command_count"] = _safe_int(command_execution.get("executed_command_count")) + 1
    if rc == 0:
        if script:
            command_execution["last_completed_script"] = script
        return
    command_execution["failed_command_count"] = _safe_int(command_execution.get("failed_command_count")) + 1
    failed_scripts = command_execution.setdefault("failed_scripts", [])
    if script and script not in failed_scripts:
        failed_scripts.append(script)
    if not _clean_str(command_execution.get("first_failed_script")) and script:
        command_execution["first_failed_script"] = script


def _checkpoint_release_readiness_summary(
    summary: dict[str, Any],
    *,
    summary_out: str,
    phase: str,
    current_check_name: str = "",
    current_check_state: str = "idle",
    phase_step_index: int | None = None,
    phase_step_total: int | None = None,
    last_completed_check_name: str = "",
) -> None:
    target = _clean_str(summary_out)
    if not target:
        return
    apply_governed_runtime_summary_checkpoint(
        summary,
        phase=phase,
        current_check_name=current_check_name,
        current_check_state=current_check_state,
        phase_step_index=phase_step_index,
        phase_step_total=phase_step_total,
        last_completed_check_name=last_completed_check_name,
    )
    write_governed_runtime_summary_checkpoint(target, summary)


def _record_required_gate_bundle_execution(summary: dict[str, Any], *, cmd: list[str], rc: int) -> None:
    registry = summary.setdefault(
        "required_gate_bundle_execution",
        {
            "observed_receipt_paths": [],
            "rows": [],
        },
    )
    out_path = _read_flag_value(cmd, "--out")
    observed_receipt_path = ""
    if out_path:
        observed_receipt_path = str(Path(out_path).expanduser().resolve())
        observed_receipts = registry.setdefault("observed_receipt_paths", [])
        if observed_receipt_path not in observed_receipts:
            observed_receipts.append(observed_receipt_path)
    registry.setdefault("rows", []).append(
        {
            "operation": _read_flag_value(cmd, "--operation"),
            "run_id_binding": _read_flag_value(cmd, "--run-id"),
            "observed_receipt_path": observed_receipt_path,
            "actor_id": _read_flag_value(cmd, "--actor-id"),
            "session_id": _read_flag_value(cmd, "--session-id"),
            "resolved_work_layer": _read_flag_value(cmd, "--resolved-work-layer"),
            "resolved_source_layer": _read_flag_value(cmd, "--resolved-source-layer"),
            "lock_state": _read_flag_value(cmd, "--lock-state"),
            "rc": int(rc),
        }
    )


def _record_structured_check(
    summary: dict[str, Any],
    *,
    name: str,
    rc: int,
    payload: dict[str, Any],
    status_fields: tuple[str, ...],
    error_fields: tuple[str, ...] = ("error_code",),
    keep_fields: tuple[str, ...] = (),
) -> None:
    status_value = _clean_str(_first_present(payload, status_fields)).upper() or (
        STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    )
    item: dict[str, Any] = {
        "status": status_value,
        "rc": int(rc),
        "error_code": _clean_str(_first_present(payload, error_fields)),
    }
    for field in keep_fields:
        if field in payload:
            item[field] = payload.get(field)
    summary[name] = item


def _extract_control_plane_check_projection(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    status_render = payload.get("status_render") or {}
    checks = status_render.get("checks") or []
    if not isinstance(checks, list):
        return {}
    projection: dict[str, dict[str, Any]] = {}
    for row in checks:
        if not isinstance(row, dict):
            continue
        name = _clean_str(row.get("name"))
        if not name:
            continue
        row_payload = row.get("payload") or {}
        item: dict[str, Any] = {
            "status": _clean_str(row.get("status")).upper() or STATUS_UNKNOWN,
            "error_code": _clean_str(row.get("error_code")),
        }
        if isinstance(row_payload, dict):
            if "violation_count" in row_payload:
                item["violation_count"] = _safe_int(row_payload.get("violation_count"))
            stale_reasons = _clean_list(row_payload.get("stale_reasons"))
            if stale_reasons:
                item["stale_reasons"] = stale_reasons
        projection[name] = item
    return projection


def _hydrate_required_gate_bundle_summary(
    summary: dict[str, Any],
    *,
    repo_root: Path,
    receipt_path: str,
    receipt_probe_path: str,
) -> None:
    execution_registry = summary.get("required_gate_bundle_execution") or {}
    observed_receipt_paths = {
        str(Path(path).expanduser().resolve())
        for path in _clean_list(execution_registry.get("observed_receipt_paths"))
        if _clean_str(path)
    }

    def _unknown_bundle(path: Path, *, reason: str) -> dict[str, Any]:
        return {
            "receipt_path": str(path),
            "bundle_status": STATUS_UNKNOWN,
            "projection_status": STATUS_UNKNOWN,
            "error_code": "",
            "run_id_binding": "",
            "actor_id": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "lock_state": "",
            **{field: "" for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS},
            "total_targets": 0,
            "required_target_count": 0,
            "failed_required_target_count": 0,
            "failed_target_names": [],
            "projection_stale_reasons": [reason],
            "rows_without_projected_report_fields": [],
            "missing_mapping_requirements": [],
        }

    def _summarize_single_bundle(path_text: str) -> dict[str, Any]:
        path = Path(path_text).expanduser().resolve()
        if str(path) not in observed_receipt_paths:
            if targeted_subset_excludes_required_gate_bundle(summary):
                return build_scope_excluded_required_gate_bundle_summary(
                    str(path),
                    selected_check_mode=_clean_str(summary.get("selected_check_mode")),
                    selected_check_dependency_mode=_clean_str(summary.get("selected_check_dependency_mode")),
                )
            return _unknown_bundle(
                path,
                reason="bundle_receipt_not_observed_in_current_release_readiness_run",
            )
        if not path.is_file():
            return _unknown_bundle(
                path,
                reason="bundle_receipt_missing_after_observed_dispatch",
            )
        payload = _safe_load_json(path)
        projection = build_required_gate_bundle_target_projection(repo_root=repo_root, bundle_payload=payload)
        return {
            "receipt_path": str(path),
            "bundle_status": _clean_str(payload.get("bundle_status")).upper(),
            "projection_status": _clean_str(projection.get("projection_status")).upper(),
            "error_code": _clean_str(payload.get("error_code")),
            "run_id_binding": _clean_str(payload.get("run_id_binding")),
            "actor_id": _clean_str(payload.get("actor_id")),
            "resolved_work_layer": _clean_str(payload.get("resolved_work_layer")),
            "resolved_source_layer": _clean_str(payload.get("resolved_source_layer")),
            "lock_state": _clean_str(payload.get("lock_state")),
            **{field: _clean_str(payload.get(field)) for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS},
            "total_targets": _safe_int(projection.get("total_targets")),
            "required_target_count": _safe_int(projection.get("required_target_count")),
            "failed_required_target_count": _safe_int(projection.get("failed_required_target_count")),
            "failed_target_names": _clean_list(projection.get("failed_target_names")),
            "projection_stale_reasons": _clean_list(projection.get("stale_reasons")),
            "rows_without_projected_report_fields": _clean_list(
                projection.get("rows_without_projected_report_fields")
            ),
            "missing_mapping_requirements": _clean_list(projection.get("missing_mapping_requirements")),
        }

    summary["required_gate_bundle"] = _summarize_single_bundle(receipt_path)
    summary["required_gate_bundle_scan_probe"] = _summarize_single_bundle(receipt_probe_path)


def _hydrate_one_look_projection(summary: dict[str, Any]) -> None:
    summary["one_look"] = build_release_readiness_one_look_projection(summary)


def _finalize_release_readiness_summary(
    summary: dict[str, Any],
    *,
    summary_out: str,
    exit_code: int,
    execution_report: str,
    health_report_dir: str,
    required_gate_bundle_receipt: str,
    required_gate_bundle_receipt_probe: str,
    repo_root: Path,
    failed_script: str = "",
    failed_rc: int | None = None,
) -> int:
    summary["release_readiness_status"] = STATUS_PASS_REQUIRED if exit_code == 0 else STATUS_FAIL_REQUIRED
    summary["exit_code"] = int(exit_code)
    summary["execution_report"] = _clean_str(execution_report)
    apply_governed_runtime_summary_checkpoint(
        summary,
        phase="finalized",
        current_check_name="",
        current_check_state="idle",
        last_completed_check_name=_clean_str((summary.get("command_execution") or {}).get("last_completed_script")),
        lifecycle_status=SUMMARY_LIFECYCLE_FINALIZED,
        checkpoint_kind=SUMMARY_CHECKPOINT_KIND_FINAL,
    )
    summary["summary_finalized_utc"] = _utc_now_iso_z()
    if failed_script:
        summary["failed_script"] = failed_script
    if failed_rc is not None:
        summary["failed_script_rc"] = int(failed_rc)
    _hydrate_required_gate_bundle_summary(
        summary,
        repo_root=repo_root,
        receipt_path=required_gate_bundle_receipt,
        receipt_probe_path=required_gate_bundle_receipt_probe,
    )
    materialize_targeted_subset_selected_check_scope_exclusions(
        summary,
        summary_capture_scripts=SUMMARY_CAPTURE_SCRIPTS,
        structured_summary_capture_specs=STRUCTURED_SUMMARY_CAPTURE_SPECS,
    )
    report_token = _clean_str(execution_report)
    if report_token:
        report_path = Path(report_token).expanduser().resolve()
        report_doc = _safe_load_json(report_path) if report_path.is_file() else {}
        summary["terminal_truth_boundary_projection"] = build_terminal_truth_boundary_projection_from_report(
            report_doc=report_doc if isinstance(report_doc, dict) else {},
            report_path=report_path if report_path.is_file() else None,
            catalog_path=Path(_clean_str(summary.get("catalog"))).expanduser().resolve(),
            repo_catalog_path=(repo_root / REPO_CATALOG_REL).resolve(),
            identity_id=_clean_str(summary.get("identity_id")),
            operation="readiness",
            work_layer=_clean_str((summary.get("lane_context") or {}).get("work_layer")),
            source_layer=_clean_str((summary.get("lane_context") or {}).get("source_layer")),
        )
    else:
        summary["terminal_truth_boundary_projection"] = {
            "terminal_truth_boundary_projection_status": STATUS_SKIPPED_NOT_REQUIRED,
            "repair_lane_status": STATUS_SKIPPED_NOT_REQUIRED,
            "experience_writeback_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
            "terminal_truth_observation_status": STATUS_SKIPPED_NOT_REQUIRED,
            "stale_reasons": ["execution_report_missing"],
        }
    summary["health_report_experience_writeback_closure"] = (
        _build_health_report_experience_writeback_closure_projection(
            summary,
            identity_id=_clean_str(summary.get("identity_id")),
            health_report_dir=health_report_dir,
            execution_report=execution_report,
        )
    )
    _hydrate_one_look_projection(summary)
    if summary_out:
        resolved_target = Path(summary_out).expanduser()
        if not resolved_target.is_absolute():
            resolved_target = (Path.cwd() / resolved_target).resolve()
        else:
            resolved_target = resolved_target.resolve()
        resolved_path = str(resolved_target)
        summary["summary_out"] = resolved_path
        _write_json(resolved_path, summary)
        print(f"[SUMMARY] release readiness summary written: {resolved_path}")
    return exit_code


def _resolve_pack_path(catalog_path: str, identity_id: str) -> Path | None:
    p = Path(catalog_path).expanduser().resolve()
    if not p.exists():
        return None
    try:
        doc = _load_yaml(p)
    except Exception:
        return None
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        return None
    pack_raw = str((row or {}).get("pack_path", "")).strip()
    if not pack_raw:
        return None
    pack = Path(pack_raw).expanduser().resolve()
    return pack if pack.exists() else None


def _resolve_lane_context(*, layer_intent_text: str, expected_work_layer: str, expected_source_layer: str) -> dict[str, str]:
    resolved = resolve_layer_intent(
        explicit_work_layer=str(expected_work_layer or "").strip(),
        explicit_source_layer=str(expected_source_layer or "").strip(),
        intent_text=str(layer_intent_text or "").strip(),
        default_work_layer=DEFAULT_WORK_LAYER,
        default_source_layer="project",
    )
    work_layer = str(resolved.get("resolved_work_layer", DEFAULT_WORK_LAYER)).strip().lower() or DEFAULT_WORK_LAYER
    source_layer = str(resolved.get("resolved_source_layer", "project")).strip().lower() or "project"
    if work_layer == "instance":
        applied_gate_set = "instance_required_checks"
    elif work_layer == "protocol":
        applied_gate_set = "protocol_required_checks"
    else:
        applied_gate_set = "dual_unroutable"
    return {
        "work_layer": work_layer,
        "source_layer": source_layer,
        "applied_gate_set": applied_gate_set,
    }


def _route_release_seq_for_lane(seq: list[list[str]], *, work_layer: str) -> tuple[list[list[str]], list[str]]:
    if work_layer != "instance":
        return seq, []
    filtered: list[list[str]] = []
    skipped: list[str] = []
    for cmd in seq:
        script = cmd[1] if len(cmd) >= 2 else ""
        if script in PROTOCOL_PUBLISH_SCRIPTS:
            skipped.append(script)
            continue
        filtered.append(cmd)
    return filtered, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description="Run release-readiness validators in a deterministic order.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--scope", default="", help="explicit scope arbitration (REPO/USER/ADMIN/SYSTEM)")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    ap.add_argument(
        "--execution-report",
        default="",
        help="optional identity upgrade execution report path; when provided, enforce experience writeback linkage",
    )
    ap.add_argument(
        "--summary-out",
        default="",
        help=(
            "optional JSON output path for a one-look readiness summary surface. "
            "When set, the script writes a governed machine-readable summary without changing default CLI behavior."
        ),
    )
    ap.add_argument(
        "--upgrade-report-dir",
        default="",
        help="optional explicit directory to search for auto-generated execution report",
    )
    ap.add_argument(
        "--catalog",
        default="",
        help="catalog path override. required unless IDENTITY_CATALOG is set.",
    )
    ap.add_argument(
        "--capability-activation-policy",
        choices=["strict-union", "route-any-ready"],
        default="strict-union",
        help=(
            "capability evaluation policy used by preflight and auto-generated update report. "
            "strict-union requires all declared route capabilities; route-any-ready allows progress when at least one route is ready."
        ),
    )
    ap.add_argument(
        "--execution-report-policy",
        choices=["strict", "warn"],
        default="strict",
        help=(
            "freshness policy for execution report binding preflight. "
            "strict fails early with IP-REL-001 on stale/mismatch reports; warn logs drift but continues."
        ),
    )
    ap.add_argument(
        "--baseline-policy",
        choices=["strict", "warn"],
        default="strict",
        help=(
            "protocol baseline freshness policy for execution report protocol_commit_sha vs current protocol HEAD. "
            "strict fails with IP-PBL-001 on stale baseline; warn logs drift but continues."
        ),
    )
    ap.add_argument(
        "--min-required-contract-coverage",
        type=float,
        default=-1.0,
        help=(
            "optional minimum required-contract coverage percentage (0-100) for tool/vendor closures. "
            "default disabled."
        ),
    )
    ap.add_argument(
        "--min-discovery-required-coverage",
        type=float,
        default=-1.0,
        help=(
            "optional minimum required-contract coverage percentage (0-100) for discovery subset "
            "(tool_installation/vendor_api_discovery/vendor_api_solution). default disabled."
        ),
    )
    ap.add_argument("--target-branch", default="")
    ap.add_argument("--release-head-sha", default="")
    ap.add_argument("--required-gates-run-id", default="")
    ap.add_argument("--run-url", default="")
    ap.add_argument("--workflow-file-sha", default="")
    ap.add_argument("--run-head-sha", default="")
    ap.add_argument("--run-workflow-file-sha", default="")
    ap.add_argument("--checks-json", default="")
    ap.add_argument("--jobs-json", default="")
    ap.add_argument("--gh-runs-json", default="")
    ap.add_argument(
        "--resume-from-summary",
        default="",
        help=(
            "optional in-progress release-readiness summary path. "
            "When provided, command-sequence checks resume from the checkpoint's current/last-completed check "
            "instead of replaying the full command sequence."
        ),
    )
    ap.add_argument(
        "--max-command-sequence-checks",
        type=int,
        default=0,
        help=(
            "optional positive cap on how many command-sequence checks to execute in this invocation. "
            "When the cap is reached, the run exits 0 after writing an IN_PROGRESS checkpoint to --summary-out."
        ),
    )
    ap.add_argument("--layer-intent-text", default="", help="optional natural-language layer intent for stamp render/validators")
    ap.add_argument("--expected-work-layer", default="", help="optional expected work_layer override for strict reply gates")
    ap.add_argument("--expected-source-layer", default="", help="optional expected source_layer override for strict reply gates")
    ap.add_argument(
        "--check-name",
        action="append",
        default=[],
        help=(
            "optional exact readiness check name to execute (repeatable). "
            "Uses the canonical script path token for each command, for example "
            "'scripts/ci/run_terminal_truth_boundary_projection_probes_ci.sh'. "
            "When provided, readiness runs a targeted governed subset instead of the full lane."
        ),
    )
    ap.add_argument(
        "--actor-id",
        default="",
        help=(
            "explicit actor id for strict governed-outlet/headstamp recurrence closure checks. "
            "Defaults to CODEX_ACTOR_ID when exported; no implicit assistant fallback is allowed."
        ),
    )
    ap.add_argument(
        "--session-id",
        default="",
        help="optional actor session id for actor-session validators; defaults to actor binding for the target identity",
    )
    args = ap.parse_args()
    selected_check_names = tuple(_clean_str(name) for name in (args.check_name or []) if _clean_str(name))

    base = args.base.strip() or _git_rev("HEAD~1")
    head = args.head.strip() or _git_rev("HEAD")
    identity_id = args.identity_id.strip()
    release_runtime_inputs = resolve_release_plane_runtime_inputs(
        identity_id=identity_id,
        operation="readiness",
        explicit_target_branch=str(args.target_branch or "").strip(),
        explicit_release_head_sha=str(args.release_head_sha or "").strip(),
        explicit_required_gates_run_id=str(args.required_gates_run_id or "").strip(),
        explicit_run_url=str(args.run_url or "").strip(),
        explicit_workflow_file_sha=str(args.workflow_file_sha or "").strip(),
        explicit_run_head_sha=str(args.run_head_sha or "").strip(),
        explicit_run_workflow_file_sha=str(args.run_workflow_file_sha or "").strip(),
        explicit_checks_json=str(args.checks_json or "").strip(),
        explicit_jobs_json=str(args.jobs_json or "").strip(),
        explicit_gh_runs_json=str(args.gh_runs_json or "").strip(),
        default_target_branch="main",
        default_release_head_sha=head,
    )
    target_branch = str(release_runtime_inputs.get("target_branch", "")).strip()
    release_head_sha = str(release_runtime_inputs.get("release_head_sha", "")).strip()
    required_gates_run_id = str(release_runtime_inputs.get("required_gates_run_id", "")).strip()
    run_url = str(release_runtime_inputs.get("run_url", "")).strip()
    workflow_file_sha = str(release_runtime_inputs.get("workflow_file_sha", "")).strip()
    run_head_sha = str(release_runtime_inputs.get("run_head_sha", "")).strip()
    run_workflow_file_sha = str(release_runtime_inputs.get("run_workflow_file_sha", "")).strip()
    checks_json = str(release_runtime_inputs.get("checks_json", "")).strip()
    jobs_json = str(release_runtime_inputs.get("jobs_json", "")).strip()
    gh_runs_json = str(release_runtime_inputs.get("gh_runs_json", "")).strip()
    release_adapter_payload = dict(release_runtime_inputs.get("release_adapter_payload") or {})
    scope = args.scope.strip().upper()
    layer_intent_text = args.layer_intent_text.strip()
    expected_work_layer = args.expected_work_layer.strip().lower()
    expected_source_layer = args.expected_source_layer.strip().lower()
    summary_out = str(args.summary_out or "").strip()
    resume_from_summary = str(args.resume_from_summary or "").strip()
    max_command_sequence_checks = max(int(args.max_command_sequence_checks or 0), 0)
    if (resume_from_summary or max_command_sequence_checks > 0) and not summary_out:
        print(
            "[FAIL] --summary-out is required when --resume-from-summary or "
            "--max-command-sequence-checks is used."
        )
        return 2
    resume_source = capture_governed_runtime_summary_resume_source(
        resume_from_summary,
        summary_out=summary_out,
    )
    try:
        actor_id = resolve_required_protocol_actor_id(str(args.actor_id or "").strip())
    except ValueError as exc:
        print(f"[FAIL] IP-ACTOR-ENTRY-001 {exc} (identity_id={identity_id})")
        return 1
    explicit_catalog = args.catalog.strip()
    env_catalog = os.environ.get("IDENTITY_CATALOG", "").strip()
    catalog = explicit_catalog or env_catalog
    if catalog:
        catalog = str(Path(catalog).expanduser().resolve())
    session_id, session_id_source = _resolve_actor_session_id(
        catalog=catalog,
        identity_id=identity_id,
        actor_id=actor_id,
        explicit_session_id=str(args.session_id or "").strip(),
    )
    session_run_id = derive_run_id_from_session_id(session_id)
    current_round_run_id = str(session_run_id or "").strip() or str(required_gates_run_id or "").strip()
    summary_payload: dict[str, Any] = {
        "release_readiness_status": "IN_PROGRESS",
        "identity_id": identity_id,
        "actor_id": actor_id,
        "session_id": session_id,
        "session_id_source": session_id_source,
        "current_round_run_id": current_round_run_id,
        "scope": scope,
        "catalog": catalog,
        "base": base,
        "head": head,
        "target_branch": target_branch,
        "selected_check_names": list(selected_check_names),
        "selected_check_mode": "targeted_subset" if selected_check_names else "full",
        "selected_check_dependency_mode": "unknown",
        "execution_report_resolution_mode": "required",
        "execution_report_resolution_status": STATUS_UNKNOWN,
        "bundle_run_token": "",
        "lane_context": {},
        "preflight": {},
        "required_contract_coverage": {
            "status": STATUS_UNKNOWN,
            "failed_required_contract_count": 0,
            "failed_required_contracts": [],
            "failed_optional_contract_count": 0,
            "failed_optional_contracts": [],
        },
        "required_gate_recurrence": {"status": STATUS_UNKNOWN},
        "required_gate_tuple_parity": {"status": STATUS_UNKNOWN},
        "release_plane_cloud_evidence": {"status": STATUS_UNKNOWN, "adapter": {}},
        "release_cloud_evidence_adapter": {"release_cloud_evidence_adapter_status": STATUS_UNKNOWN},
        "control_plane_budget": {"status": STATUS_UNKNOWN},
        "control_plane_budget_sync": {"status": STATUS_UNKNOWN},
        "control_plane_status_sync": {"status": STATUS_UNKNOWN},
        "control_plane_surface_materialization": {"status": STATUS_UNKNOWN},
        "terminal_truth_boundary_projection": {"terminal_truth_boundary_projection_status": STATUS_UNKNOWN},
        "health_report_experience_writeback_closure": {"projection_status": STATUS_UNKNOWN},
        "failclose_plugin_projection": {"status": STATUS_UNKNOWN},
        "full_scan_target_regression": {"status": STATUS_UNKNOWN},
        **release_readiness_repo_global_closure_summary_defaults(),
        **release_readiness_active_runtime_closure_summary_defaults(),
        **release_readiness_governance_probe_summary_defaults(),
        "command_execution": {
            "executed_command_count": 0,
            "failed_command_count": 0,
            "failed_scripts": [],
            "first_failed_script": "",
            "last_completed_script": "",
        },
    }
    from governed_runtime_summary_surface_common import build_governed_runtime_summary_surface_payload

    summary_payload["surface_governance"] = build_governed_runtime_summary_surface_payload(
        "release_readiness_summary"
    )
    execution_report = ""
    def finish(exit_code: int, *, failed_script: str = "", failed_rc: int | None = None) -> int:
        return _finalize_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            exit_code=exit_code,
            execution_report=execution_report,
            health_report_dir=health_report_dir,
            required_gate_bundle_receipt=required_gate_bundle_receipt,
            required_gate_bundle_receipt_probe=required_gate_bundle_receipt_probe,
            repo_root=PROTOCOL_ROOT,
            failed_script=failed_script,
            failed_rc=failed_rc,
        )
    print(f"[INFO] actor session selector: source={session_id_source} session_id={session_id or '<auto>'}")
    lane_ctx = _resolve_lane_context(
        layer_intent_text=layer_intent_text,
        expected_work_layer=expected_work_layer,
        expected_source_layer=expected_source_layer,
    )
    routed_work_layer = str(lane_ctx.get("work_layer", DEFAULT_WORK_LAYER))
    routed_source_layer = str(lane_ctx.get("source_layer", "global"))
    routed_applied_gate_set = str(lane_ctx.get("applied_gate_set", "instance_required_checks"))
    if not expected_source_layer:
        expected_source_layer = routed_source_layer
    summary_payload["lane_context"] = {
        "work_layer": routed_work_layer,
        "source_layer": routed_source_layer,
        "applied_gate_set": routed_applied_gate_set,
        "expected_work_layer": expected_work_layer,
        "expected_source_layer": expected_source_layer,
    }
    print(
        f"[INFO] lane routing: work_layer={routed_work_layer} "
        f"source_layer={routed_source_layer} applied_gate_set={routed_applied_gate_set}"
    )
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="bootstrap",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=0,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
    )
    stamp_artifact = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-response-stamp-{identity_id}",
            ext="json",
        )
    )
    stamp_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-stamp-blocker-receipt-{identity_id}",
            ext="json",
        )
    )
    reply_first_line_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-reply-first-line-blocker-receipt-{identity_id}",
            ext="json",
        )
    )
    send_time_reply_file = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-send-time-reply-{identity_id}",
            ext="txt",
        )
    )
    send_time_reply_gate_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-send-time-reply-gate-blocker-receipt-{identity_id}",
            ext="json",
        )
    )
    execution_reply_coherence_blocker_receipt = str(
        runtime_temp_file(
            channel="response-stamp",
            operation="readiness",
            identity_id=identity_id,
            stem=f"identity-execution-reply-coherence-blocker-receipt-{identity_id}",
            ext="json",
        )
    )
    bundle_run_token = _derive_bundle_run_token(
        required_gates_run_id=current_round_run_id,
        execution_report=str(args.execution_report or "").strip(),
        session_id=session_id,
        identity_id=identity_id,
    )
    summary_payload["bundle_run_token"] = bundle_run_token
    required_gate_bundle_receipt = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="readiness",
            identity_id=identity_id,
            run_token=bundle_run_token,
            stem=f"required-gate-bundle-readiness-{identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    required_gate_bundle_receipt_probe = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="scan",
            identity_id=identity_id,
            run_token=f"{bundle_run_token}-scan-probe",
            stem=f"required-gate-bundle-readiness-scan-probe-{identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    failclose_plugin_projection_receipt = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="readiness",
            identity_id=identity_id,
            run_token=f"{bundle_run_token}-plugin-projection",
            stem=f"failclose-plugin-projection-readiness-{identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    full_scan_target_regression_receipt = str(
        runtime_temp_file(
            channel="required-gate-bundle",
            operation="readiness",
            identity_id=identity_id,
            run_token=f"{bundle_run_token}-full-scan-target-regression",
            stem=f"full-scan-target-regression-readiness-{identity_id}-{bundle_run_token}",
            ext="json",
        )
    )
    vibe_pack_out_root = str(named_temp_root("vibe-coding-feeding-packs"))
    capability_fit_out_root = str(named_temp_root("capability-fit-matrices"))
    health_report_dir = str(named_temp_root("identity-health-reports"))
    upgrade_reports_runtime_root = named_temp_root("identity-runtime")
    upgrade_reports_named_root = named_temp_root("identity-upgrade-reports")
    if not catalog:
        print("[FAIL] catalog is required (implicit fallback disabled).")
        print("       pass --catalog <path> or set IDENTITY_CATALOG after mode selection.")
        print("       recommended: source ./scripts/identity_runtime_select.sh project")
        return finish(2)
    if not Path(catalog).expanduser().exists():
        print(f"[FAIL] catalog path does not exist: {catalog}")
        return finish(2)
    guard_cmd = [
        "python3",
        "scripts/validate_identity_runtime_mode_guard.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--expect-mode",
        "auto",
        "--operation",
        "readiness",
    ]
    if scope:
        guard_cmd.extend(["--scope", scope])
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="scripts/validate_identity_runtime_mode_guard.py",
        current_check_state="running",
        phase_step_index=1,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
    )
    rc_guard = _run(guard_cmd)
    if rc_guard != 0:
        _record_command_execution(summary_payload, script="scripts/validate_identity_runtime_mode_guard.py", rc=rc_guard)
        return finish(rc_guard, failed_script="scripts/validate_identity_runtime_mode_guard.py", failed_rc=rc_guard)
    _record_command_execution(summary_payload, script="scripts/validate_identity_runtime_mode_guard.py", rc=rc_guard)
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=1,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        last_completed_check_name="scripts/validate_identity_runtime_mode_guard.py",
    )

    path_pack_cmd = [
        "python3",
        "scripts/validate_identity_pack_path_canonical.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--json-only",
    ]
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="scripts/validate_identity_pack_path_canonical.py",
        current_check_state="running",
        phase_step_index=2,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
    )
    rc_pack, out_pack, _ = _run_capture(path_pack_cmd)
    pack_payload = _parse_json_payload(out_pack) or {}
    path_status = str(pack_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    path_codes = pack_payload.get("path_error_codes", [])
    if not isinstance(path_codes, list):
        path_codes = [str(path_codes)]
    print(
        "[INFO] pack path canonical preflight: "
        f"status={path_status} error_codes={','.join(str(x) for x in path_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    _record_preflight(
        summary_payload,
        name="pack_path_canonical",
        rc=rc_pack,
        payload=pack_payload,
        status_fields=("path_governance_status",),
        error_fields=("error_code", "path_error_codes"),
        keep_fields=("path_error_codes", "pack_path", "identity_id"),
    )
    if rc_pack != 0:
        _record_command_execution(summary_payload, script="scripts/validate_identity_pack_path_canonical.py", rc=rc_pack)
        return finish(rc_pack, failed_script="scripts/validate_identity_pack_path_canonical.py", failed_rc=rc_pack)
    _record_command_execution(summary_payload, script="scripts/validate_identity_pack_path_canonical.py", rc=rc_pack)
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=2,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        last_completed_check_name="scripts/validate_identity_pack_path_canonical.py",
    )

    home_alignment_cmd = [
        "python3",
        "scripts/validate_identity_home_catalog_alignment.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--identity-home",
        str(Path(catalog).expanduser().resolve().parent),
        "--json-only",
    ]
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="scripts/validate_identity_home_catalog_alignment.py",
        current_check_state="running",
        phase_step_index=3,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
    )
    rc_home_align, out_home_align, _ = _run_capture(home_alignment_cmd)
    home_align_payload = _parse_json_payload(out_home_align) or {}
    home_align_status = str(home_align_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    home_align_codes = home_align_payload.get("path_error_codes", [])
    if not isinstance(home_align_codes, list):
        home_align_codes = [str(home_align_codes)]
    print(
        "[INFO] identity home/catalog alignment preflight: "
        f"status={home_align_status} error_codes={','.join(str(x) for x in home_align_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    _record_preflight(
        summary_payload,
        name="identity_home_catalog_alignment",
        rc=rc_home_align,
        payload=home_align_payload,
        status_fields=("path_governance_status",),
        error_fields=("error_code", "path_error_codes"),
        keep_fields=("path_error_codes", "identity_home", "catalog_path"),
    )
    if rc_home_align != 0:
        _record_command_execution(summary_payload, script="scripts/validate_identity_home_catalog_alignment.py", rc=rc_home_align)
        return finish(rc_home_align, failed_script="scripts/validate_identity_home_catalog_alignment.py", failed_rc=rc_home_align)
    _record_command_execution(summary_payload, script="scripts/validate_identity_home_catalog_alignment.py", rc=rc_home_align)
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=3,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        last_completed_check_name="scripts/validate_identity_home_catalog_alignment.py",
    )

    fixture_boundary_cmd = [
        "python3",
        "scripts/validate_fixture_runtime_boundary.py",
        "--identity-id",
        identity_id,
        "--catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--operation",
        "readiness",
        "--json-only",
    ]
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="scripts/validate_fixture_runtime_boundary.py",
        current_check_state="running",
        phase_step_index=4,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
    )
    rc_fixture_boundary, out_fixture_boundary, _ = _run_capture(fixture_boundary_cmd)
    fixture_boundary_payload = _parse_json_payload(out_fixture_boundary) or {}
    fixture_boundary_status = (
        str(fixture_boundary_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
    )
    fixture_boundary_codes = fixture_boundary_payload.get("path_error_codes", [])
    if not isinstance(fixture_boundary_codes, list):
        fixture_boundary_codes = [str(fixture_boundary_codes)]
    print(
        "[INFO] fixture/runtime boundary preflight: "
        f"status={fixture_boundary_status} error_codes={','.join(str(x) for x in fixture_boundary_codes if str(x).strip()) or '-'} "
        f"identity={identity_id}"
    )
    _record_preflight(
        summary_payload,
        name="fixture_runtime_boundary",
        rc=rc_fixture_boundary,
        payload=fixture_boundary_payload,
        status_fields=("path_governance_status",),
        error_fields=("error_code", "path_error_codes"),
        keep_fields=("path_error_codes", "profile", "runtime_mode"),
    )
    if rc_fixture_boundary != 0:
        _record_command_execution(summary_payload, script="scripts/validate_fixture_runtime_boundary.py", rc=rc_fixture_boundary)
        return finish(rc_fixture_boundary, failed_script="scripts/validate_fixture_runtime_boundary.py", failed_rc=rc_fixture_boundary)
    _record_command_execution(summary_payload, script="scripts/validate_fixture_runtime_boundary.py", rc=rc_fixture_boundary)
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="preflight",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=4,
        phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        last_completed_check_name="scripts/validate_fixture_runtime_boundary.py",
    )
    fixture_profile = str(fixture_boundary_payload.get("profile", "")).strip().lower()
    fixture_runtime_mode = str(fixture_boundary_payload.get("runtime_mode", "")).strip().lower()
    is_fixture_identity = fixture_profile == "fixture" or fixture_runtime_mode == "demo_only"
    target_source_layer_mode = (
        expected_source_layer if expected_source_layer in {"auto", "project", "global", "both"} else "project"
    )
    effective_expected_work_layer = str(expected_work_layer or routed_work_layer or "protocol").strip().lower() or "protocol"
    effective_expected_source_layer = (
        str(expected_source_layer or routed_source_layer or "project").strip().lower() or "project"
    )
    full_scan_target_regression_cmd = [
        "python3",
        FULL_SCAN_TARGET_REGRESSION_SCRIPT,
        "--identity-id",
        identity_id,
        "--project-catalog",
        catalog,
        "--repo-catalog",
        "identity/catalog/identities.yaml",
        "--target-source-layer",
        target_source_layer_mode,
        "--actor-id",
        actor_id,
        "--expected-work-layer",
        effective_expected_work_layer,
        "--expected-source-layer",
        effective_expected_source_layer,
        "--out",
        full_scan_target_regression_receipt,
        "--json-only",
    ]
    if session_id:
        full_scan_target_regression_cmd.extend(["--session-id", session_id])
    if not is_fixture_identity:
        full_scan_target_regression_cmd.append("--enforce-m2m-pass")
    print(
        "[INFO] full-scan target regression preflight: "
        f"fixture_identity={is_fixture_identity} enforce_m2m_pass={not is_fixture_identity} "
        f"source_layer={target_source_layer_mode}"
    )

    seq: list[list[str]] = [
        ["python3", "scripts/validate_identity_protocol.py"],
        ["python3", "scripts/validate_identity_local_persistence.py"],
        ["python3", "scripts/validate_identity_creation_boundary.py"],
        [
            "python3",
            "scripts/validate_identity_scope_resolution.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_scope_isolation.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_scope_persistence.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_instance_pack_topology.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        ["python3", "scripts/validate_identity_state_consistency.py", "--catalog", catalog],
        [
            "python3",
            "scripts/validate_identity_session_pointer_consistency.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--strict-session-primary",
        ],
        [
            "python3",
            "scripts/validate_actor_session_binding.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_no_implicit_switch.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_cross_actor_isolation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--scope-mode",
            "actor_primary",
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_actor_session_multibinding_concurrency.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_session_refresh_status.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--operation",
            "readiness",
            "--baseline-policy",
            args.baseline_policy,
        ],
        [
            "python3",
            "scripts/validate_identity_switch_closure_semantics.py",
            "--catalog",
            catalog,
            "--json-only",
        ],
        build_workspace_runtime_closure_checker_command(
            checker_id="scripts/check_identity_codex_launcher_migration_closure.py",
            catalog_path=catalog,
            json_only=True,
        ),
        [
            "python3",
            "scripts/validate_runtime_catalog_metadata_hygiene.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--require-active",
            "--json-only",
        ],
        *_build_workspace_runtime_closure_checks(catalog=catalog),
        ["python3", "scripts/validate_audit_snapshot_index.py"],
        *POST_CLOSURE_GOVERNANCE_SCRIPTS,
        ["python3", "scripts/validate_native_chat_bootstrap_entry_stream.py", "--json-only"],
        ["python3", "scripts/validate_protocol_ssot_source.py"],
        [
            "python3",
            "scripts/validate_e2e_hermetic_runtime_import.py",
            "--operation",
            "readiness",
            "--pythonpath-bootstrap-mode",
            "internal_bootstrap",
            "--json-only",
        ],
        ["python3", "scripts/validate_changelog_updated.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_protocol_handoff_coupling.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_metadata_sync.py"],
        ["python3", "scripts/validate_release_freeze_boundary.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_workspace_cleanliness.py"],
        ["python3", "scripts/validate_identity_instance_isolation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_runtime_contract.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_role_binding.py", "--catalog", catalog, "--identity-id", identity_id],
        [
            "python3",
            IDENTITY_RESPONSE_STAMP_RENDER_SCRIPT,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--view",
            "external",
            "--disclosure-level",
            "standard",
            "--out",
            stamp_artifact,
            "--json-only",
        ],
        [
            "python3",
            IDENTITY_RESPONSE_STAMP_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-user-visible-gate",
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            stamp_blocker_receipt,
        ],
        [
            "python3",
            LAYER_INTENT_RESOLUTION_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-layer-intent-gate",
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            REPLY_IDENTITY_CONTEXT_FIRST_LINE_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-first-line-gate",
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--blocker-receipt-out",
            reply_first_line_blocker_receipt,
        ],
        [
            "python3",
            "scripts/final_emit_governed.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--body-text",
            "READINESS_SEND_TIME_REPLY_BODY",
            "--out-reply-file",
            send_time_reply_file,
            "--blocker-receipt-out",
            send_time_reply_gate_blocker_receipt,
            "--outlet-channel-id",
            "final_emit_governed",
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--run-id",
            bundle_run_token,
            "--json-only",
        ],
        [
            "python3",
            SEND_TIME_REPLY_GATE_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--reply-file",
            send_time_reply_file,
            "--force-check",
            "--enforce-send-time-gate",
            "--reply-outlet-guard-applied",
            "--outlet-channel-id",
            "final_emit_governed",
            "--reply-transport-ref",
            send_time_reply_file,
            "--operation",
            "readiness",
            "--blocker-receipt-out",
            send_time_reply_gate_blocker_receipt,
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--json-only",
        ],
        [
            "python3",
            HEADSTAMP_RECURRENCE_CLOSURE_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--json-only",
        ],
        [
            "python3",
            EXECUTION_REPLY_IDENTITY_COHERENCE_VALIDATOR_ID,
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--stamp-json",
            stamp_artifact,
            "--force-check",
            "--enforce-coherence-gate",
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--blocker-receipt-out",
            execution_reply_coherence_blocker_receipt,
            "--json-only",
        ],
        *_build_response_stamp_blocker_receipt_checks(
            catalog=catalog,
            identity_id=identity_id,
            receipt_specs=[
                (stamp_blocker_receipt, False),
                (send_time_reply_gate_blocker_receipt, True),
                (reply_first_line_blocker_receipt, False),
                (execution_reply_coherence_blocker_receipt, True),
            ],
        ),
        # scope must come from bound runtime/catalog resolution (single source of truth).
        ["python3", "scripts/validate_identity_prompt_quality.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_update_lifecycle.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_safety.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_provenance.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_tool_installation.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_vendor_api_discovery.py", "--catalog", catalog, "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_vendor_api_solution.py", "--catalog", catalog, "--identity-id", identity_id],
        [
            "python3",
            "scripts/validate_semantic_routing_guard.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_instance_protocol_split_receipt.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_work_layer_gate_set_routing.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--base",
            base,
            "--head",
            head,
            "--applied-gate-set",
            routed_applied_gate_set,
            "--force-check",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_protocol_vendor_semantic_isolation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_external_source_trust_chain.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_protocol_data_sanitization_boundary.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/trigger_platform_optimization_discovery.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_discovery_requiredization.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/build_vibe_coding_feeding_pack.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--out-root",
            vibe_pack_out_root,
        ],
        [
            "python3",
            "scripts/validate_identity_capability_fit_optimization.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_composition_before_discovery.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_fit_review_freshness.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_capability_fit_roundtable_evidence.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_identity_routing_learning_strengthening.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_feedback_to_judgement_loopback.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_weak_live_linkage.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_terminal_truth_cleanliness.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_identity_orchestration_contract.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_knowledge_contract.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_experience_feedback.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_experience_feedback_governance.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_capability_arbitration.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/trigger_capability_fit_review.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/build_capability_fit_matrix.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--out-root",
            capability_fit_out_root,
        ],
        [
            "python3",
            "scripts/validate_vendor_namespace_separation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
        ],
        [
            "python3",
            "scripts/validate_required_contract_coverage.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--run-id",
            bundle_run_token,
            "--report-selected-path",
            str(args.execution_report or "").strip(),
            "--current-stamp-json",
            stamp_artifact,
            "--current-entry-receipt",
            required_gate_bundle_receipt,
        ],
        [
            "python3",
            "scripts/validate_unlock_formula.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_release_plane_cloud_evidence.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--target-branch",
            target_branch,
            "--release-head-sha",
            release_head_sha,
            "--required-gates-run-id",
            required_gates_run_id,
            "--run-url",
            run_url,
            "--workflow-file-sha",
            workflow_file_sha,
            "--run-head-sha",
            run_head_sha,
            "--run-workflow-file-sha",
            run_workflow_file_sha,
            "--checks-json",
            checks_json,
            *(["--gh-runs-json", gh_runs_json] if gh_runs_json else []),
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_cross_cwd_absolute_input.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            str(Path("identity/catalog/identities.yaml").resolve()),
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_run_id_report_selection.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--run-id",
            current_round_run_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_phase_bootstrap_before_strict.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_tmp_collision_safety.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--run-id",
            current_round_run_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/materialize_contract_bootstrap_emitters.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--apply",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_handoff_collab_freshness_rotation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_protocol_feedback_atomic_emit.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_capability_boundary_classification.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_promotion_pipeline.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_outlet_matrix.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_sidecar_cwd_parity.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_docs_bridge_consistency.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_prompt_bootstrap_capability.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_prompt_capability_matrix.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_refresh_strict_business_interference.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_kernel_ssot_source.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_prompt_derivation_conformance.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_semantic_convergence.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_contract_mapping_coverage.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_prompt_kernel_executable_coupling.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--actor-id",
            actor_id,
            "--session-id",
            session_id,
            "--json-only",
        ],
        build_required_gate_bundle_cmd(
            catalog=catalog,
            identity_id=identity_id,
            run_id=bundle_run_token,
            send_time_gate_status="NOT_APPLICABLE",
            outlet_bypass_detected="false",
            final_emit_contract_status="NOT_APPLICABLE",
            final_emit_policy_mode="tool_choice_required",
            final_emit_schema_status="NOT_APPLICABLE",
            actor_id=actor_id,
            session_id=session_id,
            resolved_work_layer=(str(args.expected_work_layer or "").strip().lower() or "instance"),
            resolved_source_layer=(
                str(args.expected_source_layer or "").strip().lower()
                or _infer_source_layer_from_catalog_path(catalog)
            ),
            lock_state="LOCK_MATCH",
            surface_label=HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
            operation="readiness",
            report_selected_path=str(args.execution_report or "").strip(),
            out_path=required_gate_bundle_receipt,
        ),
        build_required_gate_bundle_cmd(
            catalog=catalog,
            identity_id=identity_id,
            run_id=bundle_run_token,
            send_time_gate_status="NOT_APPLICABLE",
            outlet_bypass_detected="false",
            final_emit_contract_status="NOT_APPLICABLE",
            final_emit_policy_mode="tool_choice_required",
            final_emit_schema_status="NOT_APPLICABLE",
            actor_id=actor_id,
            session_id=session_id,
            resolved_work_layer=(str(args.expected_work_layer or "").strip().lower() or "instance"),
            resolved_source_layer=(
                str(args.expected_source_layer or "").strip().lower()
                or _infer_source_layer_from_catalog_path(catalog)
            ),
            lock_state="LOCK_MATCH",
            surface_label=HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
            operation="scan",
            report_selected_path=str(args.execution_report or "").strip(),
            out_path=required_gate_bundle_receipt_probe,
        ),
        [
            "python3",
            "scripts/validate_required_gate_recurrence_escalator.py",
            "--identity-id",
            identity_id,
            "--surface",
            "readiness",
            "--operation",
            "readiness",
            "--receipt",
            required_gate_bundle_receipt,
            "--enforce-blocking",
            "--json-only",
        ],
        [
            "python3",
            "scripts/validate_required_gate_tuple_parity.py",
            "--receipt",
            required_gate_bundle_receipt,
            "--receipt",
            required_gate_bundle_receipt_probe,
            "--require-distinct-operations",
            "--json-only",
        ],
        [
            "python3",
            FAILCLOSE_PLUGIN_PROJECTION_SCRIPT,
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--run-id",
            bundle_run_token,
            "--report-selected-path",
            str(args.execution_report or "").strip(),
            "--send-time-gate-status",
            "NOT_APPLICABLE",
            "--outlet-bypass-detected",
            "false",
            "--final-emit-contract-status",
            "NOT_APPLICABLE",
            "--final-emit-policy-mode",
            "tool_choice_required",
            "--final-emit-schema-status",
            "NOT_APPLICABLE",
            "--actor-id",
            actor_id,
            "--resolved-work-layer",
            (str(args.expected_work_layer or "").strip().lower() or "instance"),
            "--resolved-source-layer",
            (str(args.expected_source_layer or "").strip().lower() or _infer_source_layer_from_catalog_path(catalog)),
            "--lock-state",
            "LOCK_MATCH",
            "--surface-label",
            "release_readiness_plugin_projection",
            "--out",
            failclose_plugin_projection_receipt,
            "--json-only",
        ],
        full_scan_target_regression_cmd,
        [
            "python3",
            "scripts/validate_replay_archive_contract.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
            "--operation",
            "readiness",
            "--json-only",
        ],
        *_build_instance_runtime_closure_checks(
            catalog=catalog,
            identity_id=identity_id,
            expected_work_layer=args.expected_work_layer,
            expected_source_layer=args.expected_source_layer,
            include_weak_live_linkage=True,
        ),
        [
            "python3",
            "scripts/validate_identity_capability_activation.py",
            "--catalog",
            catalog,
            "--repo-catalog",
            REPO_CATALOG_REL,
            "--identity-id",
            identity_id,
            "--activation-policy",
            args.capability_activation_policy,
            "--work-layer",
            (str(args.expected_work_layer or "").strip().lower() or "instance"),
            "--source-layer",
            (str(args.expected_source_layer or "").strip().lower() or _infer_source_layer_from_catalog_path(catalog)),
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_content.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_cross_validation.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_dialogue_result_support.py",
            "--catalog",
            catalog,
            "--identity-id",
            identity_id,
        ],
        [
            "python3",
            "scripts/validate_identity_self_upgrade_enforcement.py",
            "--identity-id",
            identity_id,
            "--base",
            base,
            "--head",
            head,
            "--catalog",
            catalog,
        ],
        ["python3", "scripts/validate_identity_ci_enforcement.py", "--catalog", catalog, "--identity-id", identity_id],
    ]
    if scope:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            script = cmd[1]
            if script in {
                "scripts/validate_identity_scope_resolution.py",
                "scripts/validate_identity_scope_isolation.py",
                "scripts/validate_identity_scope_persistence.py",
                "scripts/collect_identity_health_report.py",
            }:
                cmd.extend(["--scope", scope])
    if args.min_required_contract_coverage >= 0.0:
        for cmd in seq:
            if len(cmd) >= 2 and cmd[1] == "scripts/validate_required_contract_coverage.py":
                cmd.extend(["--min-required-contract-coverage", str(args.min_required_contract_coverage)])
                break
    if args.min_discovery_required_coverage >= 0.0:
        for cmd in seq:
            if len(cmd) >= 2 and cmd[1] == "scripts/validate_required_contract_coverage.py":
                cmd.extend(["--min-discovery-required-coverage", str(args.min_discovery_required_coverage)])
                break
    preview_stage_seq, selectable_post_execution_targeted_check_names = (
        _extend_selection_candidates_with_unique_script_names(
            seq,
            _build_post_execution_report_stage_checks(
                identity_id=identity_id,
                catalog=catalog,
                execution_report=str(args.execution_report or "").strip() or "__EXECUTION_REPORT__",
                report_meta={},
                health_report_dir=health_report_dir,
                actor_id=actor_id,
                session_id=session_id or "run:selection-preview",
                scope=scope,
                base=base,
                head=head,
                capability_activation_policy=args.capability_activation_policy,
                expected_work_layer=args.expected_work_layer,
                expected_source_layer=args.expected_source_layer,
            ),
        )
    )
    preview_selection_projection = _build_selected_check_projection(
        preview_stage_seq,
        selected_check_names=selected_check_names,
    )
    targeted_subset_mode = bool(preview_selection_projection["targeted_subset_mode"])
    _apply_selected_check_projection_summary(summary_payload, preview_selection_projection)
    preview_missing_selected_check_names = preview_selection_projection["missing_selected_check_names"]
    if preview_missing_selected_check_names:
        print(
            "[FAIL] unknown readiness check selection: "
            + ", ".join(str(name) for name in preview_missing_selected_check_names)
        )
        return finish(
            1,
            failed_script="release_readiness_check#check_selection",
            failed_rc=1,
        )
    execution_report_required = bool(preview_selection_projection["execution_report_required"])
    selected_subset_targets_post_execution_stage = targeted_subset_mode and bool(
        selectable_post_execution_targeted_check_names.intersection(selected_check_names)
    )
    execution_report = args.execution_report.strip()
    if execution_report:
        execution_report = str(Path(execution_report).expanduser().resolve())
    if execution_report_required and not execution_report:
        gen_cmd = [
            "python3",
            "scripts/identity_creator.py",
            "update",
            "--identity-id",
            identity_id,
            "--mode",
            "review-required",
            "--catalog",
            catalog,
            "--actor-id",
            actor_id,
            "--capability-activation-policy",
            args.capability_activation_policy,
            "--baseline-policy",
            args.baseline_policy,
            "--run-id",
            (current_round_run_id or f"readiness-{identity_id}"),
        ]
        if session_id:
            gen_cmd.extend(["--session-id", session_id])
        if scope:
            gen_cmd.extend(["--scope", scope])
        if layer_intent_text:
            gen_cmd.extend(["--layer-intent-text", layer_intent_text])
        if expected_work_layer:
            gen_cmd.extend(["--expected-work-layer", expected_work_layer])
        if expected_source_layer:
            gen_cmd.extend(["--expected-source-layer", expected_source_layer])
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="execution_report_resolution",
            current_check_name="scripts/identity_creator.py",
            current_check_state="running",
            phase_step_index=1,
            phase_step_total=1,
        )
        rc = _run(gen_cmd)
        _record_command_execution(summary_payload, script="scripts/identity_creator.py", rc=rc)
        if rc != 0:
            return finish(rc, failed_script="scripts/identity_creator.py", failed_rc=rc)
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="execution_report_resolution",
            current_check_name="",
            current_check_state="idle",
            phase_step_index=1,
            phase_step_total=1,
            last_completed_check_name="scripts/identity_creator.py",
        )
        pack_path = _resolve_pack_path(catalog, identity_id)
        if current_round_run_id and pack_path is not None:
            current_round_reports = collect_execution_reports(pack_path, identity_id)
            selected_report, selection_strategy = select_execution_report(
                explicit_report="",
                run_id=current_round_run_id,
                reports=current_round_reports,
            )
            if selected_report is None:
                print(
                    "[FAIL] writeback validation requires current-round execution report, but none matched: "
                    f"identity={identity_id} run_id={current_round_run_id} selection_strategy={selection_strategy}"
                )
                return finish(1, failed_script="scripts/validate_run_id_report_selection.py", failed_rc=1)
            execution_report = str(selected_report)
            print(
                "[INFO] auto-generated execution report (current-round bound): "
                f"run_id={current_round_run_id} report={execution_report}"
            )
        else:
            roots: list[Path] = []
            if args.upgrade_report_dir.strip():
                roots.append(Path(args.upgrade_report_dir.strip()).expanduser().resolve())
            if pack_path is not None:
                roots.append((pack_path / "runtime" / "reports").resolve())
                roots.append((pack_path / "runtime").resolve())
            roots.append(upgrade_reports_named_root)
            roots.append(upgrade_reports_runtime_root)
            if os.environ.get("IDENTITY_HOME", "").strip():
                roots.append(Path(os.environ["IDENTITY_HOME"]).expanduser().resolve())
            selected_report = latest_prompt_bound_primary_execution_report_from_roots(
                roots,
                identity_id,
                explicit_pack_root=pack_path,
            )
            if selected_report is None:
                print(
                    "[FAIL] writeback validation requires execution report, but auto-generation produced none: "
                    f"searched_roots={','.join(str(r) for r in roots)} pattern=identity-upgrade-exec-{identity_id}-*.json"
                )
                return finish(2)
            execution_report = str(selected_report)
            print(f"[INFO] auto-generated execution report: {execution_report}")
        summary_payload["execution_report_resolution_status"] = STATUS_PASS_REQUIRED
    elif execution_report_required:
        summary_payload["execution_report_resolution_status"] = STATUS_PASS_REQUIRED
    else:
        summary_payload["execution_report_resolution_status"] = STATUS_SKIPPED_NOT_REQUIRED
    summary_payload["execution_report"] = execution_report

    if execution_report_required:
        freshness_cmd = [
            "python3",
            "scripts/validate_execution_report_freshness.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--execution-report-policy",
            args.execution_report_policy,
            "--json-only",
        ]
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="scripts/validate_execution_report_freshness.py",
            current_check_state="running",
            phase_step_index=5,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        )
        rc_fresh, out_fresh, _ = _run_capture(freshness_cmd)
        freshness_payload = _parse_json_payload(out_fresh) or {}
        freshness_status = str(freshness_payload.get("freshness_status", "")).strip().upper() or "UNKNOWN"
        freshness_code = str(freshness_payload.get("freshness_error_code", "")).strip() or "-"
        selected_report = str(freshness_payload.get("report_selected_path", "")).strip()
        if selected_report and Path(selected_report).exists():
            execution_report = selected_report
        print(
            "[INFO] execution report freshness preflight: "
            f"status={freshness_status} error_code={freshness_code} report={execution_report}"
        )
        _record_preflight(
            summary_payload,
            name="execution_report_freshness",
            rc=rc_fresh,
            payload=freshness_payload,
            status_fields=("freshness_status",),
            error_fields=("freshness_error_code", "error_code"),
            keep_fields=("report_selected_path", "freshness_error_code", "stale_reasons"),
        )
        if rc_fresh != 0:
            _record_command_execution(summary_payload, script="scripts/validate_execution_report_freshness.py", rc=rc_fresh)
            return finish(rc_fresh, failed_script="scripts/validate_execution_report_freshness.py", failed_rc=rc_fresh)
        _record_command_execution(summary_payload, script="scripts/validate_execution_report_freshness.py", rc=rc_fresh)
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="",
            current_check_state="idle",
            phase_step_index=5,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
            last_completed_check_name="scripts/validate_execution_report_freshness.py",
        )

        report_path_cmd = [
            "python3",
            "scripts/validate_identity_execution_report_path_contract.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--report",
            execution_report,
            "--json-only",
        ]
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="scripts/validate_identity_execution_report_path_contract.py",
            current_check_state="running",
            phase_step_index=6,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        )
        rc_report_path, out_report_path, _ = _run_capture(report_path_cmd)
        report_path_payload = _parse_json_payload(out_report_path) or {}
        report_path_status = str(report_path_payload.get("path_governance_status", "")).strip().upper() or "UNKNOWN"
        report_path_codes = report_path_payload.get("path_error_codes", [])
        if not isinstance(report_path_codes, list):
            report_path_codes = [str(report_path_codes)]
        print(
            "[INFO] execution report path preflight: "
            f"status={report_path_status} error_codes={','.join(str(x) for x in report_path_codes if str(x).strip()) or '-'} "
            f"report={execution_report}"
        )
        _record_preflight(
            summary_payload,
            name="execution_report_path_contract",
            rc=rc_report_path,
            payload=report_path_payload,
            status_fields=("path_governance_status",),
            error_fields=("error_code", "path_error_codes"),
            keep_fields=("path_error_codes",),
            extra={"report": execution_report},
        )
        if rc_report_path != 0:
            _record_command_execution(
                summary_payload,
                script="scripts/validate_identity_execution_report_path_contract.py",
                rc=rc_report_path,
            )
            return finish(
                rc_report_path,
                failed_script="scripts/validate_identity_execution_report_path_contract.py",
                failed_rc=rc_report_path,
            )
        _record_command_execution(
            summary_payload,
            script="scripts/validate_identity_execution_report_path_contract.py",
            rc=rc_report_path,
        )
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="",
            current_check_state="idle",
            phase_step_index=6,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
            last_completed_check_name="scripts/validate_identity_execution_report_path_contract.py",
        )

        baseline_cmd = [
            "python3",
            "scripts/validate_identity_protocol_baseline_freshness.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--execution-report",
            execution_report,
            "--baseline-policy",
            args.baseline_policy,
            "--json-only",
        ]
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="scripts/validate_identity_protocol_baseline_freshness.py",
            current_check_state="running",
            phase_step_index=7,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        )
        rc_baseline, out_baseline, _ = _run_capture(baseline_cmd)
        baseline_payload = _parse_json_payload(out_baseline) or {}
        baseline_status = str(baseline_payload.get("baseline_status", "")).strip().upper() or "UNKNOWN"
        baseline_code = str(baseline_payload.get("baseline_error_code", "")).strip() or "-"
        selected_report = str(baseline_payload.get("report_selected_path", "")).strip()
        if selected_report and Path(selected_report).exists():
            execution_report = selected_report
        print(
            "[INFO] protocol baseline freshness preflight: "
            f"status={baseline_status} error_code={baseline_code} report={execution_report}"
        )
        _record_preflight(
            summary_payload,
            name="protocol_baseline_freshness",
            rc=rc_baseline,
            payload=baseline_payload,
            status_fields=("baseline_status",),
            error_fields=("baseline_error_code", "error_code"),
            keep_fields=("report_selected_path", "baseline_error_code", "stale_reasons"),
        )
        if rc_baseline != 0:
            _record_command_execution(
                summary_payload,
                script="scripts/validate_identity_protocol_baseline_freshness.py",
                rc=rc_baseline,
            )
            return finish(
                rc_baseline,
                failed_script="scripts/validate_identity_protocol_baseline_freshness.py",
                failed_rc=rc_baseline,
            )
        _record_command_execution(
            summary_payload,
            script="scripts/validate_identity_protocol_baseline_freshness.py",
            rc=rc_baseline,
        )
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="",
            current_check_state="idle",
            phase_step_index=7,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
            last_completed_check_name="scripts/validate_identity_protocol_baseline_freshness.py",
        )

        version_alignment_cmd = [
            "python3",
            "scripts/validate_identity_protocol_version_alignment.py",
            "--identity-id",
            identity_id,
            "--catalog",
            catalog,
            "--repo-catalog",
            "identity/catalog/identities.yaml",
            "--execution-report",
            execution_report,
            "--operation",
            "readiness",
            "--alignment-policy",
            args.baseline_policy,
            "--json-only",
        ]
        if scope:
            version_alignment_cmd.extend(["--scope", scope])
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="scripts/validate_identity_protocol_version_alignment.py",
            current_check_state="running",
            phase_step_index=8,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
        )
        rc_align, out_align, _ = _run_capture(version_alignment_cmd)
        align_payload = _parse_json_payload(out_align) or {}
        align_status = str(align_payload.get("protocol_version_alignment_status", "")).strip().upper() or "UNKNOWN"
        align_code = str(align_payload.get("error_code", "")).strip() or "-"
        print(
            "[INFO] protocol version alignment preflight: "
            f"status={align_status} error_code={align_code} report={execution_report}"
        )
        _record_preflight(
            summary_payload,
            name="protocol_version_alignment",
            rc=rc_align,
            payload=align_payload,
            status_fields=("protocol_version_alignment_status",),
            error_fields=("error_code",),
            keep_fields=("stale_reasons",),
            extra={"report": execution_report},
        )
        if rc_align != 0:
            _record_command_execution(
                summary_payload,
                script="scripts/validate_identity_protocol_version_alignment.py",
                rc=rc_align,
            )
            return finish(
                rc_align,
                failed_script="scripts/validate_identity_protocol_version_alignment.py",
                failed_rc=rc_align,
            )
        _record_command_execution(
            summary_payload,
            script="scripts/validate_identity_protocol_version_alignment.py",
            rc=rc_align,
        )
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="preflight",
            current_check_name="",
            current_check_state="idle",
            phase_step_index=8,
            phase_step_total=READINESS_PREFLIGHT_COMMAND_COUNT,
            last_completed_check_name="scripts/validate_identity_protocol_version_alignment.py",
        )
    else:
        skip_reason = "selected_subset_report_independent"
        _record_preflight_skip(
            summary_payload,
            name="execution_report_freshness",
            reason=skip_reason,
        )
        _record_preflight_skip(
            summary_payload,
            name="execution_report_path_contract",
            reason=skip_reason,
        )
        _record_preflight_skip(
            summary_payload,
            name="protocol_baseline_freshness",
            reason=skip_reason,
        )
        _record_preflight_skip(
            summary_payload,
            name="protocol_version_alignment",
            reason=skip_reason,
        )

    report_meta: dict[str, Any] = {}
    if execution_report_required:
        try:
            report_meta = json.loads(Path(execution_report).read_text(encoding="utf-8"))
        except Exception:
            report_meta = {}
        _apply_bundle_passthrough_from_report(seq, report_meta, execution_report)
        coverage_cmds: list[list[str]] = []
        seq_without_coverage: list[list[str]] = []
        for cmd in seq:
            if len(cmd) >= 2 and cmd[1] == "scripts/validate_required_contract_coverage.py":
                _replace_flag_value(cmd, "--run-id", bundle_run_token)
                _replace_flag_value(cmd, "--report-selected-path", execution_report)
                coverage_cmds.append(cmd)
                continue
            seq_without_coverage.append(cmd)
        if coverage_cmds:
            seq = seq_without_coverage + coverage_cmds

    if (not targeted_subset_mode) or selected_subset_targets_post_execution_stage:
        seq.extend(
            _build_post_execution_report_stage_checks(
                identity_id=identity_id,
                catalog=catalog,
                execution_report=execution_report,
                report_meta=report_meta,
                health_report_dir=health_report_dir,
                actor_id=actor_id,
                session_id=session_id,
                scope=scope,
                base=base,
                head=head,
                capability_activation_policy=args.capability_activation_policy,
                expected_work_layer=args.expected_work_layer,
                expected_source_layer=args.expected_source_layer,
            )
        )

    seq, skipped_protocol_publish_checks = _route_release_seq_for_lane(seq, work_layer=routed_work_layer)
    if skipped_protocol_publish_checks:
        print(
            "[INFO] instance lane active; skipped protocol publish gates: "
            + ", ".join(skipped_protocol_publish_checks)
        )

    if layer_intent_text:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            script = cmd[1]
            if script in LAYER_INTENT_AWARE_SCRIPTS and "--layer-intent-text" not in cmd:
                cmd.extend(["--layer-intent-text", layer_intent_text])
    if expected_work_layer:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            if cmd[1] in EXPECTED_WORK_LAYER_VALIDATOR_SCRIPTS and "--expected-work-layer" not in cmd:
                cmd.extend(["--expected-work-layer", expected_work_layer])
            if (
                cmd[1] == "scripts/final_emit_governed.py"
                and "--work-layer" not in cmd
            ):
                cmd.extend(["--work-layer", expected_work_layer])
            if (
                cmd[1] == "scripts/render_identity_response_stamp.py"
                and "--work-layer" not in cmd
            ):
                cmd.extend(["--work-layer", expected_work_layer])
    if expected_source_layer:
        for cmd in seq:
            if len(cmd) < 2:
                continue
            if (
                cmd[1] == "scripts/final_emit_governed.py"
                and "--source-layer" not in cmd
            ):
                cmd.extend(["--source-layer", expected_source_layer])
            if (
                cmd[1] == "scripts/render_identity_response_stamp.py"
                and "--source-layer" not in cmd
            ):
                cmd.extend(["--source-layer", expected_source_layer])
            if (
                cmd[1] in EXPECTED_SOURCE_LAYER_EXPECTED_FLAG_SCRIPTS
                and "--expected-source-layer" not in cmd
            ):
                cmd.extend(["--expected-source-layer", expected_source_layer])
            if (
                cmd[1] in EXPECTED_SOURCE_LAYER_DIRECT_FLAG_SCRIPTS
                and "--source-layer" not in cmd
            ):
                cmd.extend(["--source-layer", expected_source_layer])
    for cmd in seq:
        if len(cmd) < 2:
            continue
        if cmd[1] in VALIDATOR_ACTOR_ID_REQUIRED_SCRIPTS and "--actor-id" not in cmd:
            cmd.extend(["--actor-id", actor_id])
        if (
            session_id
            and cmd[1] in VALIDATOR_SESSION_ID_REQUIRED_SCRIPTS
            and "--session-id" not in cmd
        ):
            cmd.extend(["--session-id", session_id])

    final_selection_projection = _build_selected_check_projection(
        seq,
        selected_check_names=selected_check_names,
    )
    targeted_subset_mode = bool(final_selection_projection["targeted_subset_mode"])
    _apply_selected_check_projection_summary(summary_payload, final_selection_projection)
    missing_selected_check_names = final_selection_projection["missing_selected_check_names"]
    if missing_selected_check_names:
        print(
            "[FAIL] unknown readiness check selection: "
            + ", ".join(str(name) for name in missing_selected_check_names)
        )
        return finish(
            1,
            failed_script="release_readiness_check#check_selection",
            failed_rc=1,
        )
    seq = list(final_selection_projection["filtered_seq"])

    if resume_from_summary:
        resume_projection = derive_governed_runtime_summary_resume_projection(
            [_command_check_name(cmd) for cmd in seq],
            dict(resume_source.get("resume_doc") or {}),
            resumable_phase="command_sequence",
        )
        resume_projection["resume_from_summary"] = _clean_str(
            resume_source.get("resume_from_summary")
        ) or str(Path(resume_from_summary).expanduser().resolve())
        resume_projection["resume_capture_mode"] = _clean_str(resume_source.get("resume_capture_mode"))
        resume_projection["same_path_as_summary_out"] = bool(resume_source.get("same_path_as_summary_out"))
        summary_payload["resume_projection"] = resume_projection
        if str(resume_projection.get("resume_projection_status", "")).strip().upper() == STATUS_PASS_REQUIRED:
            start_index = _safe_int(resume_projection.get("resume_start_index"))
            seq = seq[start_index:]
        elif str(resume_projection.get("resume_reason", "")).strip():
            print(
                "[INFO] resume-from-summary not applied: "
                f"reason={resume_projection.get('resume_reason')} source={resume_projection.get('resume_from_summary')}"
            )

    total_seq_count_before_batch_limit = len(seq)
    batch_limit_applied = False
    if max_command_sequence_checks > 0 and max_command_sequence_checks < total_seq_count_before_batch_limit:
        batch_limit_applied = True
        summary_payload["command_sequence_batch"] = {
            "batch_status": STATUS_PASS_REQUIRED,
            "max_command_sequence_checks": int(max_command_sequence_checks),
            "remaining_command_check_count_before_batch": int(total_seq_count_before_batch_limit),
            "continuation_required": True,
        }
        seq = seq[:max_command_sequence_checks]
    total_seq_count = len(seq)
    summary_payload["selected_check_count_after_resume"] = total_seq_count
    _checkpoint_release_readiness_summary(
        summary_payload,
        summary_out=summary_out,
        phase="command_sequence",
        current_check_name="",
        current_check_state="idle",
        phase_step_index=0,
        phase_step_total=total_seq_count,
        last_completed_check_name=_clean_str((summary_payload.get("command_execution") or {}).get("last_completed_script")),
    )

    for seq_index, cmd in enumerate(seq, start=1):
        script = cmd[1] if len(cmd) >= 2 else ""
        is_capability_validator = len(cmd) >= 2 and cmd[1] == "scripts/validate_identity_capability_activation.py"
        capture_key = SUMMARY_CAPTURE_SCRIPTS.get(script, "")
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="command_sequence",
            current_check_name=script,
            current_check_state="running",
            phase_step_index=seq_index,
            phase_step_total=total_seq_count,
        )
        if not is_capability_validator:
            if capture_key:
                rc, out, _ = _run_capture(cmd)
                payload = _parse_json_payload(out) or {}
                if capture_key == "required_contract_coverage":
                    coverage_projection = build_required_contract_coverage_projection(payload)
                    summary_payload["required_contract_coverage"] = {
                        "status": _clean_str(
                            payload.get("coverage_status") or payload.get("required_contract_coverage_status")
                        ).upper()
                        or (STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED),
                        "rc": int(rc),
                        "error_code": _clean_str(payload.get("error_code")),
                        "required_contract_total": _safe_int(payload.get("required_contract_total")),
                        "required_contract_passed": _safe_int(payload.get("required_contract_passed")),
                        "required_contract_coverage_rate": payload.get("required_contract_coverage_rate"),
                        "discovery_required_total": _safe_int(payload.get("discovery_required_total")),
                        "discovery_required_passed": _safe_int(payload.get("discovery_required_passed")),
                        "discovery_required_coverage_rate": payload.get("discovery_required_coverage_rate"),
                        "failed_required_contract_count": _safe_int(payload.get("failed_required_contract_count")),
                        "failed_optional_contract_count": _safe_int(payload.get("failed_optional_contract_count")),
                        "failed_required_contracts": coverage_projection.get("failed_required_contracts", []),
                        "failed_optional_contracts": coverage_projection.get("failed_optional_contracts", []),
                        "failed_required_contract_details": coverage_projection.get("failed_required_contract_details", []),
                        "failed_optional_contract_details": coverage_projection.get("failed_optional_contract_details", []),
                    }
                elif capture_key in STRUCTURED_SUMMARY_CAPTURE_SPECS:
                    spec = STRUCTURED_SUMMARY_CAPTURE_SPECS[capture_key]
                    _record_structured_check(
                        summary_payload,
                        name=capture_key,
                        rc=rc,
                        payload=payload,
                        status_fields=tuple(spec.get("status_fields", ())),
                        error_fields=tuple(spec.get("error_fields", ())),
                        keep_fields=tuple(spec.get("keep_fields", ())),
                    )
                    if capture_key == "control_plane_surface_materialization":
                        summary_payload[capture_key]["control_plane_check_projection"] = (
                            _extract_control_plane_check_projection(payload)
                        )
                elif capture_key == "release_plane_cloud_evidence":
                    release_projection = build_release_plane_cloud_evidence_summary_projection(payload)
                    release_projection["status"] = _clean_str(
                        release_projection.get("status")
                    ).upper() or (STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED)
                    summary_payload["release_plane_cloud_evidence"] = release_projection
                    summary_payload["release_cloud_evidence_adapter"] = build_release_cloud_evidence_adapter_projection(
                        payload
                    )
                elif capture_key == "failclose_plugin_projection":
                    _record_structured_check(
                        summary_payload,
                        name="failclose_plugin_projection",
                        rc=rc,
                        payload=payload,
                        status_fields=("failclose_plugin_projection_status",),
                        error_fields=("error_code",),
                        keep_fields=("profile_count", "checked_target_count", "violation_count", "stale_reasons", "violations"),
                    )
                elif capture_key == "full_scan_target_regression":
                    _record_structured_check(
                        summary_payload,
                        name="full_scan_target_regression",
                        rc=rc,
                        payload=payload,
                        status_fields=("full_scan_target_regression_status",),
                        error_fields=("error_code",),
                        keep_fields=(
                            "p0_rows",
                            "m2m_fail_rows",
                            "three_plane_summary_conflicts",
                            "fixture_identity",
                            "target_source_layer",
                            "report_path",
                        ),
                    )
            else:
                rc = _run(cmd)
                if script == BUNDLE_RUNNER_SCRIPT:
                    _record_required_gate_bundle_execution(summary_payload, cmd=cmd, rc=rc)
            _record_command_execution(summary_payload, script=script, rc=rc)
            if rc != 0:
                return finish(rc, failed_script=script, failed_rc=rc)
            _checkpoint_release_readiness_summary(
                summary_payload,
                summary_out=summary_out,
                phase="command_sequence",
                current_check_name="",
                current_check_state="idle",
                phase_step_index=seq_index,
                phase_step_total=total_seq_count,
                last_completed_check_name=script,
            )
            continue

        rc, out, _ = _run_capture(cmd)
        _record_command_execution(summary_payload, script=script, rc=rc)
        if rc == 0:
            _checkpoint_release_readiness_summary(
                summary_payload,
                summary_out=summary_out,
                phase="command_sequence",
                current_check_name="",
                current_check_state="idle",
                phase_step_index=seq_index,
                phase_step_total=total_seq_count,
                last_completed_check_name=script,
            )
            continue

        payload = _parse_json_payload(out) or {}
        cap_error_code = str(payload.get("capability_activation_error_code", "")).strip()
        if capability_env_auth_fallback_eligible(
            requested_policy=normalize_capability_activation_policy(args.capability_activation_policy),
            error_code=cap_error_code,
            rc=rc,
        ):
            print(
                "[WARN] capability activation strict-union blocked by env/auth boundary (IP-CAP-003); "
                "retrying route-any-ready fallback for readiness flow"
            )
            fallback_cmd = replace_capability_activation_policy(
                cmd,
                CAPABILITY_ACTIVATION_ENV_AUTH_FALLBACK_POLICY,
            )
            _checkpoint_release_readiness_summary(
                summary_payload,
                summary_out=summary_out,
                phase="command_sequence",
                current_check_name=f"{script}#fallback",
                current_check_state="running",
                phase_step_index=seq_index,
                phase_step_total=total_seq_count,
            )
            rc_fb = _run(fallback_cmd)
            _record_command_execution(summary_payload, script=f"{script}#fallback", rc=rc_fb)
            if rc_fb == 0:
                _checkpoint_release_readiness_summary(
                    summary_payload,
                    summary_out=summary_out,
                    phase="command_sequence",
                    current_check_name="",
                    current_check_state="idle",
                    phase_step_index=seq_index,
                    phase_step_total=total_seq_count,
                    last_completed_check_name=f"{script}#fallback",
                )
                continue
            return finish(rc_fb, failed_script=f"{script}#fallback", failed_rc=rc_fb)
        return finish(rc, failed_script=script, failed_rc=rc)

    if batch_limit_applied:
        executed_batch_count = len(seq)
        remaining_after_batch = max(total_seq_count_before_batch_limit - executed_batch_count, 0)
        summary_payload["command_sequence_batch"] = {
            "batch_status": STATUS_PASS_REQUIRED,
            "max_command_sequence_checks": int(max_command_sequence_checks),
            "remaining_command_check_count_before_batch": int(total_seq_count_before_batch_limit),
            "executed_command_check_count": int(executed_batch_count),
            "remaining_command_check_count_after_batch": int(remaining_after_batch),
            "continuation_required": remaining_after_batch > 0,
            "batch_boundary_reason": "max_command_sequence_checks_reached",
        }
        _checkpoint_release_readiness_summary(
            summary_payload,
            summary_out=summary_out,
            phase="command_sequence",
            current_check_name="",
            current_check_state="paused",
            phase_step_index=executed_batch_count,
            phase_step_total=total_seq_count_before_batch_limit,
            last_completed_check_name=_clean_str((summary_payload.get("command_execution") or {}).get("last_completed_script")),
        )
        print(
            "[INFO] command-sequence batch boundary reached: "
            f"executed={executed_batch_count} remaining={remaining_after_batch} "
            f"max_command_sequence_checks={max_command_sequence_checks}"
        )
        return 0

    print("[OK] release readiness checks PASSED")
    return finish(0)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] subprocess error: {exc}", file=sys.stderr)
        raise SystemExit(2)
