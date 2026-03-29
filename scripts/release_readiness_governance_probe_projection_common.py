#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_UNKNOWN = "UNKNOWN"
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SCRIPT = (
    "scripts/ci/run_release_readiness_one_look_topology_probes_ci.sh"
)
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY = (
    "release_readiness_one_look_topology_probe"
)
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD = (
    "release_readiness_one_look_topology_probe_status"
)
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
)
RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    "positive_validator_output",
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_SUMMARY_KEY = (
    "release_readiness_terminal_truth_bridge_probe"
)
RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD = (
    "release_readiness_terminal_truth_bridge_probe_status"
)


@dataclass(frozen=True)
class ReleaseReadinessGovernanceProbeProjectionSpec:
    script_rel: str
    summary_key: str
    one_look_field: str
    status_fields: tuple[str, ...]
    error_fields: tuple[str, ...] = ("error_code",)
    keep_fields: tuple[str, ...] = ()
    one_look_passthrough_fields: tuple[tuple[str, str], ...] = ()


RELEASE_READINESS_GOVERNANCE_PROBE_SPECS: tuple[ReleaseReadinessGovernanceProbeProjectionSpec, ...] = (
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh",
        summary_key="terminal_truth_boundary_outer_surface_e2e_probe",
        one_look_field="terminal_truth_boundary_outer_surface_e2e_probe_status",
        status_fields=("terminal_truth_boundary_outer_surface_e2e_probe_status",),
        keep_fields=("summary_terminal_truth_boundary", "seeded_identity_ids"),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_full_scan_health_projection_probes_ci.sh",
        summary_key="full_scan_health_projection_probe",
        one_look_field="full_scan_health_projection_probe_status",
        status_fields=("full_scan_health_projection_probe_status",),
        keep_fields=(
            "projection_only_excluded_area",
            "pass_projection_status",
            "projection_only_status",
            "fail_projection_status",
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh",
        summary_key="runtime_summary_surface_governance_probe",
        one_look_field="runtime_summary_surface_governance_probe_status",
        status_fields=("runtime_summary_surface_governance_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel=RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SCRIPT,
        summary_key=RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_SUMMARY_KEY,
        one_look_field=RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
        status_fields=RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_STATUS_FIELDS,
        keep_fields=RELEASE_READINESS_ONE_LOOK_TOPOLOGY_GOVERNANCE_PROBE_KEEP_FIELDS,
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_repo_global_closure_topology_probes_ci.sh",
        summary_key="release_readiness_repo_global_closure_topology_probe",
        one_look_field="release_readiness_repo_global_closure_topology_probe_status",
        status_fields=("release_readiness_repo_global_closure_topology_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_active_runtime_closure_topology_probes_ci.sh",
        summary_key="release_readiness_active_runtime_closure_topology_probe",
        one_look_field="release_readiness_active_runtime_closure_topology_probe_status",
        status_fields=("release_readiness_active_runtime_closure_topology_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_terminal_truth_bridge_probes_ci.sh",
        summary_key=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_SUMMARY_KEY,
        one_look_field=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD,
        status_fields=(RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD,),
        keep_fields=("positive_validator_output", "bridge_case_count", "bridge_cases", "seeded_identity_ids"),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_governance_probe_topology_probes_ci.sh",
        summary_key="release_readiness_governance_probe_topology_probe",
        one_look_field="release_readiness_governance_probe_topology_probe_status",
        status_fields=("release_readiness_governance_probe_topology_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh",
        summary_key="release_readiness_post_closure_adjudication_topology_probe",
        one_look_field="release_readiness_post_closure_adjudication_topology_probe_status",
        status_fields=("release_readiness_post_closure_adjudication_topology_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_required_gate_surface_drift_probes_ci.sh",
        summary_key="required_gate_surface_drift_probe",
        one_look_field="required_gate_surface_drift_probe_status",
        status_fields=("required_gate_surface_drift_probe_status",),
        keep_fields=("positive_validator_output",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
        summary_key="release_readiness_summary_binding_probe",
        one_look_field="release_readiness_summary_binding_probe_status",
        status_fields=("release_readiness_summary_binding_probe_status",),
        keep_fields=("report_derived_token", "session_fallback_token", "legacy_path", "run_bound_path"),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_readiness_continuation_probes_ci.sh",
        summary_key="release_readiness_continuation_probe",
        one_look_field="release_readiness_continuation_probe_status",
        status_fields=("release_readiness_continuation_probe_status",),
        keep_fields=("round_count", "release_readiness_script_path", "caller_cwd_safe"),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
        summary_key="release_plane_context_resolution_probe",
        one_look_field="release_plane_context_resolution_probe_status",
        status_fields=("release_plane_context_resolution_probe_status",),
        keep_fields=("ambient_run_url",),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
        summary_key="active_execution_report_pointer_locality_probe",
        one_look_field="active_execution_report_pointer_locality_probe_status",
        status_fields=("active_execution_report_pointer_locality_probe_status",),
        keep_fields=(
            "external_pointer_rejection_status",
            "external_pointer_resolution_mode",
            "external_pointer_selection_mode",
            "external_pointer_selected_report_authority_class",
            "external_pointer_rejected_selected_report",
            "pack_local_pointer_authority_status",
            "pack_local_pointer_resolution_mode",
            "pack_local_pointer_selection_mode",
            "pack_local_pointer_selected_report_authority_class",
            "pack_local_pointer_selected_report",
        ),
        one_look_passthrough_fields=(
            (
                "external_pointer_rejection_status",
                "active_execution_report_pointer_external_rejection_status",
            ),
            (
                "external_pointer_resolution_mode",
                "active_execution_report_pointer_external_resolution_mode",
            ),
            (
                "external_pointer_selection_mode",
                "active_execution_report_pointer_external_selection_mode",
            ),
            (
                "external_pointer_selected_report_authority_class",
                "active_execution_report_pointer_external_authority_class",
            ),
            (
                "external_pointer_rejected_selected_report",
                "active_execution_report_pointer_external_selected_report",
            ),
            (
                "pack_local_pointer_authority_status",
                "active_execution_report_pointer_pack_local_authority_status",
            ),
            (
                "pack_local_pointer_resolution_mode",
                "active_execution_report_pointer_pack_local_resolution_mode",
            ),
            (
                "pack_local_pointer_selection_mode",
                "active_execution_report_pointer_pack_local_selection_mode",
            ),
            (
                "pack_local_pointer_selected_report_authority_class",
                "active_execution_report_pointer_pack_local_authority_class",
            ),
            (
                "pack_local_pointer_selected_report",
                "active_execution_report_pointer_pack_local_selected_report",
            ),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh",
        summary_key="strict_live_active_pointer_locality_probe",
        one_look_field="strict_live_active_pointer_locality_probe_status",
        status_fields=("strict_live_active_pointer_locality_probe_status",),
        keep_fields=(
            "external_pointer_rejection_status",
            "report_name_rehome_status",
            "candidate_root_binding_status",
            "external_pointer_resolution_mode",
            "rehome_resolution_mode",
            "candidate_root_resolution_mode",
        ),
        one_look_passthrough_fields=(
            (
                "external_pointer_rejection_status",
                "strict_live_active_pointer_external_rejection_status",
            ),
            ("report_name_rehome_status", "strict_live_active_pointer_rehome_status"),
            ("candidate_root_binding_status", "strict_live_active_pointer_candidate_root_status"),
            (
                "external_pointer_resolution_mode",
                "strict_live_active_pointer_external_resolution_mode",
            ),
            ("rehome_resolution_mode", "strict_live_active_pointer_rehome_resolution_mode"),
            (
                "candidate_root_resolution_mode",
                "strict_live_active_pointer_candidate_root_resolution_mode",
            ),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_strict_live_contract_resolution_probes_ci.sh",
        summary_key="strict_live_contract_resolution_probe",
        one_look_field="strict_live_contract_resolution_probe_status",
        status_fields=("strict_live_contract_resolution_probe_status",),
        keep_fields=(
            "locality_false_green_block_status",
            "sample_green_failclose_status",
            "backfill_canonicalization_status",
        ),
        one_look_passthrough_fields=(
            (
                "locality_false_green_block_status",
                "strict_live_contract_resolution_locality_false_green_block_status",
            ),
            (
                "sample_green_failclose_status",
                "strict_live_contract_resolution_sample_green_failclose_status",
            ),
            (
                "backfill_canonicalization_status",
                "strict_live_contract_resolution_backfill_canonicalization_status",
            ),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_execution_report_selection_convergence_probes_ci.sh",
        summary_key="execution_report_selection_convergence_probe",
        one_look_field="execution_report_selection_convergence_probe_status",
        status_fields=("execution_report_selection_convergence_probe_status",),
        keep_fields=(
            "selected_report_path",
            "candidate_count",
            "freshness_status",
            "baseline_status",
            "run_id_selection_strategy",
        ),
        one_look_passthrough_fields=(
            ("candidate_count", "execution_report_selection_convergence_candidate_count"),
            ("freshness_status", "execution_report_selection_convergence_freshness_status"),
            ("baseline_status", "execution_report_selection_convergence_baseline_status"),
            (
                "run_id_selection_strategy",
                "execution_report_selection_convergence_run_id_selection_strategy",
            ),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_identity_codex_launcher_convergence_probes_ci.sh",
        summary_key="identity_codex_launcher_convergence_probe",
        one_look_field="identity_codex_launcher_convergence_probe_status",
        status_fields=("identity_codex_launcher_convergence_probe_status",),
        keep_fields=(
            "probe_context_status",
            "metadata_hygiene_apply_status",
            "truth_sync_apply_status",
            "repo_catalog_rejection_status",
            "repaired_identity_count",
        ),
        one_look_passthrough_fields=(
            ("probe_context_status", "identity_codex_launcher_convergence_probe_context_status"),
            (
                "metadata_hygiene_apply_status",
                "identity_codex_launcher_convergence_metadata_hygiene_apply_status",
            ),
            ("truth_sync_apply_status", "identity_codex_launcher_convergence_truth_sync_apply_status"),
            (
                "repo_catalog_rejection_status",
                "identity_codex_launcher_convergence_repo_catalog_rejection_status",
            ),
            ("repaired_identity_count", "identity_codex_launcher_convergence_repaired_identity_count"),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_identity_transport_fleet_closure_convergence_probes_ci.sh",
        summary_key="identity_transport_fleet_closure_convergence_probe",
        one_look_field="identity_transport_fleet_closure_convergence_probe_status",
        status_fields=("identity_transport_fleet_closure_convergence_probe_status",),
        keep_fields=(
            "workspace_checked_identity_count",
            "repo_inclusive_violation_count",
            "fleet_projection_policy_id",
        ),
        one_look_passthrough_fields=(
            (
                "workspace_checked_identity_count",
                "identity_transport_fleet_closure_convergence_workspace_checked_identity_count",
            ),
            (
                "repo_inclusive_violation_count",
                "identity_transport_fleet_closure_convergence_repo_inclusive_violation_count",
            ),
            (
                "fleet_projection_policy_id",
                "identity_transport_fleet_closure_convergence_policy_id",
            ),
        ),
    ),
    ReleaseReadinessGovernanceProbeProjectionSpec(
        script_rel="scripts/ci/run_active_runtime_pack_closure_convergence_probes_ci.sh",
        summary_key="active_runtime_pack_closure_convergence_probe",
        one_look_field="active_runtime_pack_closure_convergence_probe_status",
        status_fields=("active_runtime_pack_closure_convergence_probe_status",),
        keep_fields=(
            "workspace_checked_identity_count",
            "repo_inclusive_violation_count",
            "pack_scan_policy_id",
        ),
        one_look_passthrough_fields=(
            (
                "workspace_checked_identity_count",
                "active_runtime_pack_closure_convergence_workspace_checked_identity_count",
            ),
            (
                "repo_inclusive_violation_count",
                "active_runtime_pack_closure_convergence_repo_inclusive_violation_count",
            ),
            (
                "pack_scan_policy_id",
                "active_runtime_pack_closure_convergence_policy_id",
            ),
        ),
    ),
)

RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS: tuple[str, ...] = tuple(
    spec.one_look_field for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS
)
RELEASE_READINESS_GOVERNANCE_PROBE_DETAIL_FIELDS: tuple[str, ...] = (
    "one_look.execution_report_selection_convergence_candidate_count",
    "one_look.execution_report_selection_convergence_freshness_status",
    "one_look.execution_report_selection_convergence_baseline_status",
    "one_look.execution_report_selection_convergence_run_id_selection_strategy",
    "one_look.active_execution_report_pointer_external_rejection_status",
    "one_look.active_execution_report_pointer_external_resolution_mode",
    "one_look.active_execution_report_pointer_external_selection_mode",
    "one_look.active_execution_report_pointer_external_authority_class",
    "one_look.active_execution_report_pointer_external_selected_report",
    "one_look.active_execution_report_pointer_pack_local_authority_status",
    "one_look.active_execution_report_pointer_pack_local_resolution_mode",
    "one_look.active_execution_report_pointer_pack_local_selection_mode",
    "one_look.active_execution_report_pointer_pack_local_authority_class",
    "one_look.active_execution_report_pointer_pack_local_selected_report",
    "one_look.strict_live_active_pointer_external_rejection_status",
    "one_look.strict_live_active_pointer_rehome_status",
    "one_look.strict_live_active_pointer_candidate_root_status",
    "one_look.strict_live_active_pointer_external_resolution_mode",
    "one_look.strict_live_active_pointer_rehome_resolution_mode",
    "one_look.strict_live_active_pointer_candidate_root_resolution_mode",
    "one_look.strict_live_contract_resolution_locality_false_green_block_status",
    "one_look.strict_live_contract_resolution_sample_green_failclose_status",
    "one_look.strict_live_contract_resolution_backfill_canonicalization_status",
    "one_look.identity_codex_launcher_convergence_probe_context_status",
    "one_look.identity_codex_launcher_convergence_metadata_hygiene_apply_status",
    "one_look.identity_codex_launcher_convergence_truth_sync_apply_status",
    "one_look.identity_codex_launcher_convergence_repo_catalog_rejection_status",
    "one_look.identity_codex_launcher_convergence_repaired_identity_count",
    "one_look.identity_transport_fleet_closure_convergence_workspace_checked_identity_count",
    "one_look.identity_transport_fleet_closure_convergence_repo_inclusive_violation_count",
    "one_look.identity_transport_fleet_closure_convergence_policy_id",
    "one_look.active_runtime_pack_closure_convergence_workspace_checked_identity_count",
    "one_look.active_runtime_pack_closure_convergence_repo_inclusive_violation_count",
    "one_look.active_runtime_pack_closure_convergence_policy_id",
)
RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES: tuple[str, ...] = tuple(
    spec.script_rel for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS
)
RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER = (
    "governance_probe_projection="
    + "|".join(f"one_look.{field}" for field in RELEASE_READINESS_GOVERNANCE_PROBE_ONE_LOOK_FIELDS)
)
RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_MARKER = (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER
)
RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_MARKER,
    *RELEASE_READINESS_GOVERNANCE_PROBE_DETAIL_FIELDS,
    *RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES,
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _project_one_look_value(field_name: str, value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    text = _clean_str(value)
    if field_name.endswith("_status"):
        return text.upper() or STATUS_UNKNOWN
    return text


def release_readiness_governance_probe_capture_script_map() -> dict[str, str]:
    return {spec.script_rel: spec.summary_key for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS}


def release_readiness_governance_probe_structured_capture_specs() -> dict[str, dict[str, tuple[str, ...]]]:
    return {
        spec.summary_key: {
            "status_fields": spec.status_fields,
            "error_fields": spec.error_fields,
            "keep_fields": spec.keep_fields,
        }
        for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS
    }


def release_readiness_governance_probe_summary_defaults() -> dict[str, dict[str, Any]]:
    return {spec.summary_key: {"status": STATUS_UNKNOWN} for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS}


def apply_release_readiness_governance_probe_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(summary, dict) or not isinstance(one_look, dict):
        return
    for spec in RELEASE_READINESS_GOVERNANCE_PROBE_SPECS:
        payload = summary.get(spec.summary_key) or {}
        if not isinstance(payload, dict):
            payload = {}
        one_look[spec.one_look_field] = _clean_str(payload.get("status")).upper() or STATUS_UNKNOWN
        for payload_field, one_look_field in spec.one_look_passthrough_fields:
            one_look[one_look_field] = _project_one_look_value(
                one_look_field,
                payload.get(payload_field),
            )
