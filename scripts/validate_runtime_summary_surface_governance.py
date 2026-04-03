#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governed_runtime_summary_surface_common import (
    SURFACE_PROFILES,
    build_governed_runtime_summary_surface_payload,
)
from full_scan_required_gate_bundle_projection_common import (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
)
from health_report_experience_writeback_projection_common import (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS,
)
from projection_profile_exclusion_scope_common import (
    PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
)
from release_cloud_evidence_projection_common import (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
)
from release_readiness_foundational_projection_common import (
    RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
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
from runtime_summary_surface_governance_common import (
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ScriptBindingSpec:
    name: str
    script_rel: str
    surface_id: str
    required_tokens: tuple[str, ...]
    enforcement_any_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocAnchorSpec:
    rel_path: str
    required_markers: tuple[str, ...]


SCRIPT_BINDINGS: tuple[ScriptBindingSpec, ...] = (
    ScriptBindingSpec(
        name="release_readiness_summary",
        script_rel="scripts/release_readiness_check.py",
        surface_id="release_readiness_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"release_readiness_summary"',
            '"terminal_truth_boundary_projection"',
            "materialize_targeted_subset_selected_check_scope_exclusions(",
            "build_release_readiness_one_look_projection(",
            "build_scope_excluded_required_gate_bundle_summary(",
            "release_readiness_repo_global_closure_capture_script_map(",
            "release_readiness_repo_global_closure_structured_capture_specs(",
            "release_readiness_repo_global_closure_summary_defaults(",
            '"scripts/validate_release_readiness_post_closure_adjudication_topology.py"',
            '"scripts/ci/run_release_readiness_post_closure_adjudication_topology_probes_ci.sh"',
        ),
        enforcement_any_tokens=("--summary-out", "summary_out"),
    ),
    ScriptBindingSpec(
        name="release_readiness_one_look_projection_common",
        script_rel="scripts/release_readiness_one_look_projection_common.py",
        surface_id="release_readiness_summary",
        required_tokens=(
            "build_release_readiness_one_look_projection(",
            "apply_release_readiness_one_look_families(",
        ),
    ),
    ScriptBindingSpec(
        name="release_readiness_one_look_topology_common",
        script_rel="scripts/release_readiness_one_look_topology_common.py",
        surface_id="release_readiness_summary",
        required_tokens=(
            "RELEASE_READINESS_ONE_LOOK_FAMILY_SPECS",
            "RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER",
            "RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS",
            "apply_release_readiness_one_look_families(",
            "apply_release_readiness_foundational_one_look",
            "apply_release_readiness_support_preflight_one_look",
            "apply_release_readiness_selected_check_scope_one_look",
            "apply_release_readiness_release_cloud_evidence_one_look",
            "apply_release_readiness_terminal_truth_boundary_one_look",
            "apply_release_readiness_health_report_experience_writeback_one_look",
            "apply_release_readiness_required_gate_bundle_one_look",
            "apply_release_readiness_repo_global_closure_one_look",
            "apply_release_readiness_active_runtime_closure_one_look",
            "apply_release_readiness_governance_probe_one_look",
        ),
    ),
    ScriptBindingSpec(
        name="semantic_tuple_three_plane",
        script_rel="scripts/report_three_plane_status.py",
        surface_id="semantic_tuple_three_plane",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"semantic_tuple_three_plane"',
            '"terminal_truth_boundary_projection"',
            '"health_report_experience_writeback_closure"',
            '"projection_profile"',
            '"projection_profile_execution_mode"',
            '"projection_excluded_areas"',
            "build_projection_profile_exclusion_payload(",
            "build_projection_profile_excluded_health_report_experience_writeback_closure(",
            "build_projection_profile_excluded_required_gate_bundle_target_projection(",
            "terminal_truth_boundary_projection=bounded outer-surface terminal-truth projection",
        ),
    ),
    ScriptBindingSpec(
        name="protocol_lane_audit_summary",
        script_rel="scripts/render_protocol_lane_audit_summary.py",
        surface_id="protocol_lane_audit_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"protocol_lane_audit_summary"',
        ),
    ),
    ScriptBindingSpec(
        name="full_identity_protocol_scan_summary",
        script_rel="scripts/full_identity_protocol_scan.py",
        surface_id="full_identity_protocol_scan_summary",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"full_identity_protocol_scan_summary"',
            '"three_plane_terminal_truth_boundary_projection"',
            '"summary_terminal_truth_boundary"',
            '"three_plane_health_report_experience_writeback_closure"',
            '"summary_health_report_experience_writeback_closure"',
            '"summary_required_gate_bundle_projection"',
            '"summary_required_gate_bundle_shadow_projection"',
            '"summary_required_gate_bundle_scan_probe_projection"',
            '"health_report_experience_writeback_projection_status"',
            '"health_report_selected_path_matches_execution_report"',
            "build_terminal_truth_boundary_projection_summary_skeleton(",
            "_record_summary_health_report_experience_writeback_closure(",
            "build_health_report_experience_writeback_closure_summary_skeleton(",
            "build_full_scan_required_gate_bundle_projection_summary_skeleton(",
            "apply_full_scan_required_gate_bundle_three_plane_projection(",
            '"projection_profile"',
            '"projection_profile_execution_mode"',
            '"projection_excluded_areas"',
            "build_projection_profile_exclusion_payload(",
            '"scan_projection_profile"',
            '"check_matrix_mode"',
        ),
    ),
    ScriptBindingSpec(
        name="control_plane_status_artifact",
        script_rel="scripts/render_control_plane_status.py",
        surface_id="control_plane_status_artifact",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"control_plane_status_artifact"',
        ),
    ),
    ScriptBindingSpec(
        name="control_plane_budget_artifact",
        script_rel="scripts/render_control_plane_budget.py",
        surface_id="control_plane_budget_artifact",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"control_plane_budget_artifact"',
        ),
    ),
    ScriptBindingSpec(
        name="identity_context_continuity_bundle_surface",
        script_rel="scripts/render_identity_context_continuity_bundle.py",
        surface_id="identity_context_continuity_bundle_surface",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"identity_context_continuity_bundle_surface"',
        ),
    ),
    ScriptBindingSpec(
        name="identity_context_reentry_answer_surface",
        script_rel="scripts/render_identity_context_reentry_answers.py",
        surface_id="identity_context_reentry_answer_surface",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"identity_context_reentry_answer_surface"',
        ),
    ),
    ScriptBindingSpec(
        name="identity_codex_launcher_command_bundle_surface",
        script_rel="scripts/render_identity_codex_launcher.py",
        surface_id="identity_codex_launcher_command_bundle_surface",
        required_tokens=(
            '"surface_governance"',
            "build_governed_runtime_summary_surface_payload(",
            '"identity_codex_launcher_command_bundle_surface"',
        ),
    ),
)

DOC_ANCHORS: tuple[DocAnchorSpec, ...] = (
    DocAnchorSpec(
        rel_path="docs/governance/identity-v1.6x-release-closure-governance.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
            "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.",
            "`scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection`",
            "`scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection`",
            "projection_profile",
            "projection_profile_execution_mode",
            "projection_excluded_areas",
            "health_report_experience_writeback_closure",
            *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
            "stable prewrite snapshot",
            "scripts/run_release_readiness_continuation.py",
            RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
            "scripts/ci/run_three_plane_health_projection_probes_ci.sh",
            "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
            "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
            "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
            "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
            *RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
            "caller cwd",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
            "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory.",
            "`scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection`",
            "`scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection`",
            "projection_profile",
            "projection_profile_execution_mode",
            "projection_excluded_areas",
            "health_report_experience_writeback_closure",
            *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
            "stable prewrite snapshot",
            "scripts/run_release_readiness_continuation.py",
            RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
            "scripts/ci/run_three_plane_health_projection_probes_ci.sh",
            "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
            "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
            "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
            "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
            *RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
            "caller cwd",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/release/identity-v1.6x-release-closure-summary.md",
        required_markers=(
            "three-plane verdict remains a governed outer runtime-state surface",
            "`scripts/report_three_plane_status.py` may emit the current cross-plane verdict, but it must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/release_readiness_check.py --summary-out`, when emitted, remains a governed outer runtime-state summary surface and must not replace root-law owners, direct validator receipts, or fleet-scope closure matrices.",
            "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority.",
            "`scripts/report_three_plane_status.py --projection-profile terminal_truth_boundary_projection`",
            "`scripts/full_identity_protocol_scan.py --projection-profile terminal_truth_boundary_projection`",
            "projection_profile",
            "projection_profile_execution_mode",
            "projection_excluded_areas",
            "health_report_experience_writeback_closure",
            *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
            *FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
            "stable prewrite snapshot",
            "resume_capture_mode=stable_prewrite_snapshot",
            "same_path_as_summary_out",
            "scripts/run_release_readiness_continuation.py",
            RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
            "scripts/ci/run_three_plane_health_projection_probes_ci.sh",
            "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
            "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
            "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
            "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
            *RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
            *RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
            *RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
            "caller cwd",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/identity-codex-launcher-governance-v1.6.14.md",
        required_markers=(
            "`scripts/render_protocol_lane_audit_summary.py` remains a single-lane formal control-plane summary surface on an outer runtime-state layer.",
            "It must not replace root-law owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
        required_markers=(
            "`scripts/render_protocol_lane_audit_summary.py` remains a single-lane formal control-plane summary surface on an outer runtime-state layer.",
            "It must not replace root-law owners, stream-owner governance/review surfaces, direct validator receipts, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/github-native-control-plane-specialization-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_status.py` remains a machine control-plane status summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_status.py` remains a machine control-plane status summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/github-native-control-plane-specialization-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.3.md",
        required_markers=(
            "`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer.",
            "It must not replace root-law owners, direct validator receipts, current-pointer SSOT, or historical replay authority.",
            "The renderer must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/identity-context-continuity-governance-v1.6.16.md",
        required_markers=(
            "`scripts/render_identity_context_continuity_bundle.py` remains a governed continuity-support bundle surface on an outer runtime-state layer.",
            "It may compress continuity readiness/proof state for launcher/internal consumers, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.",
            "`scripts/render_identity_context_reentry_answers.py` remains a governed identity-visible reentry answer surface on an outer runtime-state layer.",
            "It may present copyable governed reentry task blocks, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.",
            "Neither surface may become a new terminal command family, thread-UUID lookup authority, or raw-transcript authority.",
            "Both renderers must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md",
        required_markers=(
            "`scripts/render_identity_context_continuity_bundle.py` remains a governed continuity-support bundle surface on an outer runtime-state layer.",
            "It may compress continuity readiness/proof state for launcher/internal consumers, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.",
            "`scripts/render_identity_context_reentry_answers.py` remains a governed identity-visible reentry answer surface on an outer runtime-state layer.",
            "It may present copyable governed reentry task blocks, but it must not replace root-law owners, direct validator receipts, canonical continuity artifacts, or launcher entry authority.",
            "Neither surface may become a new terminal command family, thread-UUID lookup authority, or raw-transcript authority.",
            "Both renderers must self-describe this bounded authority in machine-readable payload form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/governance/identity-codex-launcher-governance-v1.6.14.md",
        required_markers=(
            "`scripts/render_identity_codex_launcher.py` command-bundle output remains a governed launcher command bundle surface on an outer runtime-state layer.",
            "It may project canonical start/resume commands and operator guidance, but it must not replace root-law owners, direct validator receipts, actor-session tuple truth, or host-thread recovery target authority.",
            "It must not promote convenience/reference fields, shell-wrapper helper strings, or manual command assembly into canonical operator authority.",
            "The command-bundle payload must self-describe this bounded authority in machine-readable form.",
        ),
    ),
    DocAnchorSpec(
        rel_path="docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md",
        required_markers=(
            "`scripts/render_identity_codex_launcher.py` command-bundle output remains a governed launcher command bundle surface on an outer runtime-state layer.",
            "It may project canonical start/resume commands and operator guidance, but it must not replace root-law owners, direct validator receipts, actor-session tuple truth, or host-thread recovery target authority.",
            "It must not promote convenience/reference fields, shell-wrapper helper strings, or manual command assembly into canonical operator authority.",
            "The command-bundle payload must self-describe this bounded authority in machine-readable form.",
        ),
    ),
)

SURFACE_PAYLOAD_MARKERS: dict[str, tuple[str, ...]] = {
    "semantic_tuple_three_plane": (
        "projection_profile_default=projection_profile=full|projection_profile_execution_mode=full_verdict",
        "projection_profile_terminal_truth_boundary=projection_profile=terminal_truth_boundary_projection|projection_profile_execution_mode=projection_only",
        "projection_profile_terminal_truth_boundary_excluded_areas=repo_plane|release_plane|release_cloud_evidence_adapter|required_gate_bundle_projection|current_chat_surface_exclusion|m2m_projection|tuple_context_projection|governance_closure_axes",
        "projection_profile_terminal_truth_boundary_repo_release_skip=repo_plane_status=SKIPPED_NOT_REQUIRED|release_plane_status=SKIPPED_NOT_REQUIRED",
        *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
        "projection_profile_terminal_truth_boundary_boundary_surface=terminal_truth_boundary_projection|instance_plane_detail.terminal_truth_boundary_projection",
    ),
    "release_readiness_summary": (
        "lifecycle_checkpoint=summary_lifecycle_status=IN_PROGRESS|summary_checkpoint_kind=checkpoint",
        "lifecycle_final=summary_lifecycle_status=FINALIZED|summary_checkpoint_kind=final",
        "resume_source_mode=stable_prewrite_snapshot",
        "same_path_resume_allowed_only_when=stable_prewrite_snapshot",
        "continuation_surface=scripts/run_release_readiness_continuation.py",
        "continuation_inner_resolution_anchor=protocol_owned_repo_root_not_caller_cwd",
        "continuation_forbidden_forward_flags=--summary-out,--resume-from-summary,--max-command-sequence-checks",
        *RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
        *RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
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
    "full_identity_protocol_scan_summary": (
        "projection_profile_default=projection_profile=full|projection_profile_execution_mode=full_verdict",
        "projection_profile_terminal_truth_boundary=projection_profile=terminal_truth_boundary_projection|projection_profile_execution_mode=projection_only",
        "projection_profile_terminal_truth_boundary_excluded_areas=release_cloud_evidence_adapter|host_visible_post_check_metrics|health_report_experience_writeback_closure",
        *PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
        "projection_profile_terminal_truth_boundary_forwarding=scan_projection_profile=terminal_truth_boundary_projection|check_matrix_mode=projection_only",
        "projection_profile_terminal_truth_boundary_host_visible_skip=host_visible_post_check_metrics_status=SKIPPED_NOT_REQUIRED|chat_egress_uniqueness_status=SKIPPED_NOT_REQUIRED",
        "projection_profile_terminal_truth_boundary_boundary_surface=three_plane_terminal_truth_boundary_projection|summary_terminal_truth_boundary",
        "projection_profile_terminal_truth_boundary_health_surface=three_plane_health_report_experience_writeback_closure|summary_health_report_experience_writeback_closure",
    ),
}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _validate_script_bindings(repo_root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for spec in SCRIPT_BINDINGS:
        path = (repo_root / spec.script_rel).resolve()
        text = _read_text(path)
        enforced = True
        if spec.enforcement_any_tokens:
            enforced = any(token in text for token in spec.enforcement_any_tokens)
        missing_tokens = [token for token in spec.required_tokens if token not in text] if enforced else []
        row = {
            "name": spec.name,
            "script_rel": spec.script_rel,
            "surface_id": spec.surface_id,
            "exists": path.exists(),
            "enforced": enforced,
            "enforcement_any_tokens": list(spec.enforcement_any_tokens),
            "missing_tokens": missing_tokens,
        }
        rows.append(row)
        if not path.exists():
            errors.append(f"missing_script:{spec.script_rel}")
        elif enforced and missing_tokens:
            errors.append(f"script_tokens_missing:{spec.script_rel}:{','.join(missing_tokens)}")
    return (STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED, rows, errors)


def _validate_doc_anchors(repo_root: Path) -> tuple[str, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for spec in DOC_ANCHORS:
        path = (repo_root / spec.rel_path).resolve()
        text = _read_text(path)
        missing_markers = [marker for marker in spec.required_markers if marker not in text]
        row = {
            "rel_path": spec.rel_path,
            "exists": path.exists(),
            "missing_markers": missing_markers,
        }
        rows.append(row)
        if not path.exists():
            errors.append(f"missing_doc:{spec.rel_path}")
        elif missing_markers:
            errors.append(f"doc_markers_missing:{spec.rel_path}:{len(missing_markers)}")
    return (STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED, rows, errors)


def _validate_surface_payloads() -> tuple[str, list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for surface_id in sorted(SURFACE_PROFILES):
        payload = build_governed_runtime_summary_surface_payload(surface_id)
        required_markers = SURFACE_PAYLOAD_MARKERS.get(surface_id, ())
        operational_constraints = payload.get("operational_constraints")
        if not isinstance(operational_constraints, list):
            operational_constraints = []
        missing_markers = [marker for marker in required_markers if marker not in operational_constraints]
        row = {
            "surface_id": surface_id,
            "operational_constraints": operational_constraints,
            "missing_operational_constraints": missing_markers,
        }
        rows.append(row)
        if missing_markers:
            errors.append(f"surface_payload_markers_missing:{surface_id}:{len(missing_markers)}")
    return (STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED, rows, errors)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governance markers for governed outer runtime summary/support surfaces.")
    ap.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(str(args.repo_root or "").strip()).expanduser().resolve()
    script_status, script_rows, script_errors = _validate_script_bindings(repo_root)
    doc_status, doc_rows, doc_errors = _validate_doc_anchors(repo_root)
    payload_status, payload_rows, payload_errors = _validate_surface_payloads()
    errors = [*script_errors, *doc_errors, *payload_errors]
    payload = {
        "runtime_summary_surface_governance_status": STATUS_PASS_REQUIRED if not errors else STATUS_FAIL_REQUIRED,
        "repo_root": str(repo_root),
        "script_source_status": script_status,
        "doc_anchor_status": doc_status,
        "surface_payload_status": payload_status,
        "script_bindings_checked": script_rows,
        "doc_anchors_checked": doc_rows,
        "surface_payloads_checked": payload_rows,
        "surface_profiles": {
            surface_id: build_governed_runtime_summary_surface_payload(surface_id)
            for surface_id in sorted(SURFACE_PROFILES)
        },
        "error_count": len(errors),
        "errors": errors,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not errors:
            print("[PASS] runtime summary surface governance validated.")
        else:
            print(f"[FAIL] runtime summary surface governance drift: {len(errors)}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
