#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreePlaneProjectionProfile:
    profile_id: str
    execution_mode: str
    repo_plane_enabled: bool
    release_plane_enabled: bool
    m2m_enabled: bool
    tuple_context_enabled: bool
    governance_closure_axes_enabled: bool
    excluded_areas: tuple[str, ...]
    description: str

    @property
    def projection_only(self) -> bool:
        return self.execution_mode == "projection_only"


THREE_PLANE_PROJECTION_PROFILES: dict[str, ThreePlaneProjectionProfile] = {
    "full": ThreePlaneProjectionProfile(
        profile_id="full",
        execution_mode="full_verdict",
        repo_plane_enabled=True,
        release_plane_enabled=True,
        m2m_enabled=True,
        tuple_context_enabled=True,
        governance_closure_axes_enabled=True,
        excluded_areas=(),
        description=(
            "Run the complete three-plane verdict: instance plane, repo plane, release plane, "
            "m2m projection, tuple-context projection, and governance closure axes."
        ),
    ),
    "terminal_truth_boundary_projection": ThreePlaneProjectionProfile(
        profile_id="terminal_truth_boundary_projection",
        execution_mode="projection_only",
        repo_plane_enabled=False,
        release_plane_enabled=False,
        m2m_enabled=False,
        tuple_context_enabled=False,
        governance_closure_axes_enabled=False,
        excluded_areas=(
            "repo_plane",
            "release_plane",
            "release_cloud_evidence_adapter",
            "required_gate_bundle_projection",
            "health_report_experience_writeback_closure",
            "current_chat_surface_exclusion",
            "m2m_projection",
            "tuple_context_projection",
            "governance_closure_axes",
        ),
        description=(
            "Run the bounded terminal-truth outer-surface projection only: preserve "
            "terminal_truth_boundary_projection and its instance-plane split while "
            "excluding unrelated repo/release/adjudication closure lanes."
        ),
    ),
}

DEFAULT_THREE_PLANE_PROJECTION_PROFILE = "full"


def three_plane_projection_profile_choices() -> tuple[str, ...]:
    return tuple(THREE_PLANE_PROJECTION_PROFILES.keys())


def resolve_three_plane_projection_profile(profile_id: str) -> ThreePlaneProjectionProfile:
    token = str(profile_id or "").strip().lower() or DEFAULT_THREE_PLANE_PROJECTION_PROFILE
    try:
        return THREE_PLANE_PROJECTION_PROFILES[token]
    except KeyError as exc:
        allowed = ", ".join(sorted(THREE_PLANE_PROJECTION_PROFILES))
        raise ValueError(f"unknown three-plane projection profile: {token} (allowed: {allowed})") from exc
