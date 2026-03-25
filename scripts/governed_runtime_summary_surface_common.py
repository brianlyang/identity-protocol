#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


SURFACE_PROFILES: dict[str, GovernedRuntimeSummarySurfaceProfile] = {
    "semantic_tuple_three_plane": GovernedRuntimeSummarySurfaceProfile(
        surface_id="semantic_tuple_three_plane",
        surface_label="semantic tuple three-plane verdict",
        governed_verdict_kind="governed_cross_plane_verdict",
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
    }
