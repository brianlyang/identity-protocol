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
