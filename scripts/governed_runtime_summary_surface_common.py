#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from projection_profile_exclusion_scope_common import (
    PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
)
from full_scan_required_gate_bundle_projection_common import (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
)
from health_report_experience_writeback_projection_common import (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS,
)
from release_cloud_evidence_projection_common import (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
)
from release_readiness_foundational_projection_common import (
    RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
)
from release_readiness_required_gate_bundle_projection_common import (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS,
)
from release_readiness_required_gate_bundle_scope_common import (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
)
from release_readiness_support_preflight_projection_common import (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
)
from release_readiness_runtime_closure_convergence_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
)
from terminal_truth_boundary_projection_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_SURFACE_CONSTRAINTS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"

CURRENT_AUTHORITY_REDIRECT_REFS: tuple[str, ...] = (
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md",
    "identity/protocol/IDENTITY_PROTOCOL.md",
    "identity/protocol/IDENTITY_RUNTIME.md",
    "identity/protocol/mappings/contract-binding.current.yaml",
    "identity/protocol/mappings/control-plane-status.current.yaml",
    "identity/protocol/mappings/control-plane-budget.current.yaml",
    "identity/protocol/mappings/workbook-registry.current.yaml",
)
CONTINUITY_SUPPORT_REDIRECT_REFS: tuple[str, ...] = (
    *CURRENT_AUTHORITY_REDIRECT_REFS,
    "docs/governance/identity-context-continuity-governance-v1.6.16.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md",
    "docs/governance/identity-codex-launcher-governance-v1.6.14.md",
)
FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    "root_law_owner",
    "direct_validator_receipt",
    "fleet_scope_closure_matrix",
    "release_tag_authority",
)
DEFAULT_STRENGTHENING_GATEWAYS: tuple[str, ...] = (
    "runtime_constitution",
    "root_contract",
    "machine_registry_directory",
)


@dataclass(frozen=True)
class GovernedRuntimeSummarySurfaceProfile:
    surface_id: str
    surface_label: str
    governed_verdict_kind: str
    authority_rule: str
    operator_interpretation_rule: str
    surface_class: str = "outer_runtime_state_surface"
    surface_scope: str = "outer"
    law_bearing: bool = False
    transition_mode: str = "governed_motivation_only"
    direct_current_turn_legality_allowed: bool = False
    current_authority_redirect_refs: tuple[str, ...] = CURRENT_AUTHORITY_REDIRECT_REFS
    forbidden_replacements: tuple[str, ...] = FORBIDDEN_REPLACEMENTS
    strengthening_gateways: tuple[str, ...] = DEFAULT_STRENGTHENING_GATEWAYS
    operational_constraints: tuple[str, ...] = ()


LANE_AUDIT_SUMMARY_REDIRECT_REFS: tuple[str, ...] = (
    *CURRENT_AUTHORITY_REDIRECT_REFS,
    "docs/governance/identity-codex-launcher-governance-v1.6.14.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
)
LANE_AUDIT_SUMMARY_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *FORBIDDEN_REPLACEMENTS,
    "stream_owner_governance_surface",
    "historical_replay_authority",
)
FULL_SCAN_SUMMARY_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *FORBIDDEN_REPLACEMENTS,
    "historical_replay_authority",
)
CONTROL_PLANE_STATUS_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *FORBIDDEN_REPLACEMENTS,
    "current_pointer_ssot",
    "historical_replay_authority",
)
CONTROL_PLANE_BUDGET_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *FORBIDDEN_REPLACEMENTS,
    "current_pointer_ssot",
    "historical_replay_authority",
)
CONTINUITY_BUNDLE_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *FORBIDDEN_REPLACEMENTS,
    "canonical_continuity_artifact",
    "launcher_entry_authority",
)
REENTRY_ANSWER_FORBIDDEN_REPLACEMENTS: tuple[str, ...] = (
    *CONTINUITY_BUNDLE_FORBIDDEN_REPLACEMENTS,
    "thread_uuid_lookup_authority",
    "raw_transcript_authority",
)
CONTINUITY_SUPPORT_GATEWAYS: tuple[str, ...] = (
    "runtime_constitution",
    "context_continuity_contract",
    "launcher_entry_owner_bridge",
    "runtime_receipt_join",
)
LAUNCHER_COMMAND_GATEWAYS: tuple[str, ...] = (
    "runtime_constitution",
    "launcher_entry_owner_stream",
    "actor_session_tuple_truth",
    "catalog_authority",
)


SURFACE_PROFILES: dict[str, GovernedRuntimeSummarySurfaceProfile] = {
    "semantic_tuple_three_plane": GovernedRuntimeSummarySurfaceProfile(
        surface_id="semantic_tuple_three_plane",
        surface_label="semantic tuple three-plane verdict",
        governed_verdict_kind="governed_cross_plane_verdict",
        operational_constraints=(
            "projection_profile_default=projection_profile=full|projection_profile_execution_mode=full_verdict",
            "projection_profile_terminal_truth_boundary=projection_profile=terminal_truth_boundary_projection|projection_profile_execution_mode=projection_only",
            "projection_profile_terminal_truth_boundary_excluded_areas=repo_plane|release_plane|release_cloud_evidence_adapter|required_gate_bundle_projection|current_chat_surface_exclusion|m2m_projection|tuple_context_projection|governance_closure_axes",
            "projection_profile_terminal_truth_boundary_repo_release_skip=repo_plane_status=SKIPPED_NOT_REQUIRED|release_plane_status=SKIPPED_NOT_REQUIRED",
            *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
            "projection_profile_terminal_truth_boundary_boundary_surface=terminal_truth_boundary_projection|instance_plane_detail.terminal_truth_boundary_projection",
        ),
        authority_rule=(
            "The three-plane verdict is a governed cross-plane verdict object on an outer runtime-state "
            "surface; it may aggregate current plane status, but it must not replace root-law owners, "
            "direct validator receipts, or fleet-scope closure matrices."
        ),
        operator_interpretation_rule=(
            "Treat the three-plane payload as a machine-readable cross-plane verdict anchored to current "
            "validators and current-pointer refs, never as self-originating root law or as a prose-only summary."
        ),
    ),
    "release_readiness_summary": GovernedRuntimeSummarySurfaceProfile(
        surface_id="release_readiness_summary",
        surface_label="release readiness one-look summary",
        governed_verdict_kind="machine_readable_readiness_summary",
        operational_constraints=(
            "lifecycle_checkpoint=summary_lifecycle_status=IN_PROGRESS|summary_checkpoint_kind=checkpoint",
            "lifecycle_final=summary_lifecycle_status=FINALIZED|summary_checkpoint_kind=final",
            "resume_source_mode=stable_prewrite_snapshot",
            "same_path_resume_allowed_only_when=stable_prewrite_snapshot",
            "continuation_surface=scripts/run_release_readiness_continuation.py",
            "continuation_inner_resolution_anchor=protocol_owned_repo_root_not_caller_cwd",
            "continuation_forbidden_forward_flags=--summary-out,--resume-from-summary,--max-command-sequence-checks",
            *RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
        ),
        authority_rule=(
            "The release-readiness summary is a governed one-look readiness summary on an outer runtime-state "
            "surface; it may compress readiness state, but it must not replace root-law owners, direct "
            "validator receipts, or fleet-scope closure matrices."
        ),
        operator_interpretation_rule=(
            "Treat the release-readiness summary as a compact machine-readable projection for operator handoff "
            "and gating context, never as standalone current authority or release-tag authority."
        ),
    ),
    "protocol_lane_audit_summary": GovernedRuntimeSummarySurfaceProfile(
        surface_id="protocol_lane_audit_summary",
        surface_label="single-lane audit summary control plane",
        governed_verdict_kind="single_lane_formal_control_plane_summary",
        current_authority_redirect_refs=LANE_AUDIT_SUMMARY_REDIRECT_REFS,
        forbidden_replacements=LANE_AUDIT_SUMMARY_FORBIDDEN_REPLACEMENTS,
        authority_rule=(
            "The protocol lane audit summary is a single-lane formal control-plane summary on an outer "
            "runtime-state surface; it may compress lane-local gate state, but it must not replace root-law "
            "owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority."
        ),
        operator_interpretation_rule=(
            "Treat the lane audit summary as a bounded machine-readable summary for one governed lane only; "
            "it may classify applicability and fail-close state for that lane, but it must not be promoted "
            "into universal replay authority or cross-lane root truth."
        ),
    ),
    "full_identity_protocol_scan_summary": GovernedRuntimeSummarySurfaceProfile(
        surface_id="full_identity_protocol_scan_summary",
        surface_label="aggregate identity scan summary",
        governed_verdict_kind="aggregate_runtime_diagnostic_summary",
        forbidden_replacements=FULL_SCAN_SUMMARY_FORBIDDEN_REPLACEMENTS,
        operational_constraints=(
            "projection_profile_default=projection_profile=full|projection_profile_execution_mode=full_verdict",
            "projection_profile_terminal_truth_boundary=projection_profile=terminal_truth_boundary_projection|projection_profile_execution_mode=projection_only",
            "projection_profile_terminal_truth_boundary_excluded_areas=release_cloud_evidence_adapter|host_visible_post_check_metrics|health_report_experience_writeback_closure",
            *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
            "projection_profile_terminal_truth_boundary_forwarding=scan_projection_profile=terminal_truth_boundary_projection|check_matrix_mode=projection_only",
            "projection_profile_terminal_truth_boundary_host_visible_skip=host_visible_post_check_metrics_status=SKIPPED_NOT_REQUIRED|chat_egress_uniqueness_status=SKIPPED_NOT_REQUIRED",
            "projection_profile_terminal_truth_boundary_boundary_surface=three_plane_terminal_truth_boundary_projection|summary_terminal_truth_boundary",
            "projection_profile_terminal_truth_boundary_health_surface=three_plane_health_report_experience_writeback_closure|summary_health_report_experience_writeback_closure",
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
        ),
        authority_rule=(
            "The full identity protocol scan payload is an aggregate runtime diagnostic summary on an outer "
            "runtime-state surface; it may compress per-identity severity, tuple, and gate state, but it must "
            "not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority."
        ),
        operator_interpretation_rule=(
            "Treat the full identity protocol scan payload as a bounded machine-readable aggregate for replay "
            "triage and fleet-state inspection; it remains derived from validator receipts and must not be "
            "promoted into standalone current authority."
        ),
    ),
    "control_plane_status_artifact": GovernedRuntimeSummarySurfaceProfile(
        surface_id="control_plane_status_artifact",
        surface_label="machine control-plane status artifact",
        governed_verdict_kind="machine_control_plane_status_summary",
        surface_class="outer_control_plane_status_surface",
        surface_scope="control_plane_outer",
        forbidden_replacements=CONTROL_PLANE_STATUS_FORBIDDEN_REPLACEMENTS,
        authority_rule=(
            "The machine control-plane status artifact is a derived aggregate control-plane status surface; it may "
            "compress machine gate state for operator visibility, but it must not replace root-law owners, direct "
            "validator receipts, current-pointer SSOT, or historical replay authority."
        ),
        operator_interpretation_rule=(
            "Treat the control-plane status artifact as a bounded machine-generated control-plane snapshot derived "
            "from underlying validators and current mappings; it is suitable for visibility and sync checks, but "
            "must not be promoted into standalone semantic authority."
        ),
    ),
    "control_plane_budget_artifact": GovernedRuntimeSummarySurfaceProfile(
        surface_id="control_plane_budget_artifact",
        surface_label="machine control-plane budget artifact",
        governed_verdict_kind="machine_control_plane_budget_summary",
        surface_class="outer_control_plane_budget_surface",
        surface_scope="control_plane_outer",
        forbidden_replacements=CONTROL_PLANE_BUDGET_FORBIDDEN_REPLACEMENTS,
        authority_rule=(
            "The machine control-plane budget artifact is a derived aggregate control-plane budget surface; it may "
            "compress observed ceilings and threshold snapshots for operator visibility, but it must not replace "
            "root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority."
        ),
        operator_interpretation_rule=(
            "Treat the control-plane budget artifact as a bounded machine-generated budget snapshot derived from "
            "current validators and current mappings; it is suitable for sync and budget maintenance, but must "
            "not be promoted into standalone semantic authority."
        ),
    ),
    "identity_context_continuity_bundle_surface": GovernedRuntimeSummarySurfaceProfile(
        surface_id="identity_context_continuity_bundle_surface",
        surface_label="governed continuity-support bundle surface",
        governed_verdict_kind="governed_continuity_support_bundle",
        surface_class="outer_runtime_support_surface",
        surface_scope="continuity_outer",
        current_authority_redirect_refs=CONTINUITY_SUPPORT_REDIRECT_REFS,
        forbidden_replacements=CONTINUITY_BUNDLE_FORBIDDEN_REPLACEMENTS,
        strengthening_gateways=CONTINUITY_SUPPORT_GATEWAYS,
        authority_rule=(
            "The continuity-support bundle is a governed outer runtime-state support surface; it may compress "
            "continuity readiness and live-consumption proof for launcher/internal consumers, but it must not "
            "replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority."
        ),
        operator_interpretation_rule=(
            "Treat the continuity-support bundle as a bounded machine-readable readiness/proof bundle derived from "
            "continuity validators and runtime artifacts; it may guide launcher/internal consumption, but it must "
            "not be promoted into standalone continuity truth or terminal command authority."
        ),
    ),
    "identity_context_reentry_answer_surface": GovernedRuntimeSummarySurfaceProfile(
        surface_id="identity_context_reentry_answer_surface",
        surface_label="governed identity-visible reentry answer surface",
        governed_verdict_kind="governed_reentry_answer_bundle",
        surface_class="outer_instance_answer_surface",
        surface_scope="continuity_instance_visible",
        current_authority_redirect_refs=CONTINUITY_SUPPORT_REDIRECT_REFS,
        forbidden_replacements=REENTRY_ANSWER_FORBIDDEN_REPLACEMENTS,
        strengthening_gateways=CONTINUITY_SUPPORT_GATEWAYS,
        authority_rule=(
            "The reentry answer surface is a governed outer runtime-state answer surface; it may present intent-"
            "separated governed reentry task blocks, but it must not replace root-law owners, direct validator "
            "receipts, canonical continuity artifacts, or launcher entry authority."
        ),
        operator_interpretation_rule=(
            "Treat the reentry answer surface as a bounded machine-readable answer bundle derived from the "
            "continuity-support bundle and continuity validators; it may help an identity answer migration/reload "
            "questions, but it must not become thread-UUID lookup authority, raw-transcript authority, or a new "
            "terminal command family."
        ),
    ),
    "identity_codex_launcher_command_bundle_surface": GovernedRuntimeSummarySurfaceProfile(
        surface_id="identity_codex_launcher_command_bundle_surface",
        surface_label="governed launcher command bundle surface",
        governed_verdict_kind="governed_launcher_command_bundle",
        surface_class="outer_operator_command_surface",
        surface_scope="launcher_operator_visible",
        current_authority_redirect_refs=(
            *CURRENT_AUTHORITY_REDIRECT_REFS,
            "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md",
            "docs/governance/identity-codex-launcher-governance-v1.6.14.md",
            "docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
        ),
        forbidden_replacements=(
            *FORBIDDEN_REPLACEMENTS,
            "actor_session_tuple_authority",
            "host_thread_recovery_target",
            "shell_wrapper_helper_family",
            "manual_command_assembly",
        ),
        strengthening_gateways=LAUNCHER_COMMAND_GATEWAYS,
        authority_rule=(
            "The launcher command bundle is a governed outer operator-command surface; it may project canonical "
            "start/resume commands and operator guidance, but it must not replace root-law owners, direct validator "
            "receipts, actor-session tuple truth, or host-thread recovery target authority."
        ),
        operator_interpretation_rule=(
            "Treat the launcher command bundle as a bounded machine-readable operator surface derived from launcher "
            "validators, catalog authority, and tuple truth; it may guide command lookup, but it must not become a "
            "shell-wrapper helper family, manual-command-assembly bypass, or standalone semantic authority."
        ),
    ),
}


def build_governed_runtime_summary_surface_payload(surface_id: str) -> dict[str, Any]:
    try:
        profile = SURFACE_PROFILES[str(surface_id or "").strip()]
    except KeyError as exc:
        raise ValueError(f"unknown governed runtime summary surface: {surface_id}") from exc
    return {
        "runtime_summary_surface_governance_status": STATUS_PASS_REQUIRED,
        "surface_id": profile.surface_id,
        "surface_label": profile.surface_label,
        "surface_class": profile.surface_class,
        "surface_scope": profile.surface_scope,
        "law_bearing": profile.law_bearing,
        "transition_mode": profile.transition_mode,
        "direct_current_turn_legality_allowed": profile.direct_current_turn_legality_allowed,
        "governed_verdict_kind": profile.governed_verdict_kind,
        "strengthening_gateways": list(profile.strengthening_gateways),
        "current_authority_redirect_refs": list(profile.current_authority_redirect_refs),
        "forbidden_replacements": list(profile.forbidden_replacements),
        "derived_summary_as_truth_forbidden": True,
        "historical_accident_as_resolution_forbidden": True,
        "authority_rule": profile.authority_rule,
        "operator_interpretation_rule": profile.operator_interpretation_rule,
        "operational_constraints": list(profile.operational_constraints),
    }
