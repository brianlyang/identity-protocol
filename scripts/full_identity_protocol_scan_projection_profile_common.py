#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FullIdentityProtocolScanProjectionProfile:
    profile_id: str
    execution_mode: str
    host_visible_post_check_metrics_enabled: bool
    excluded_areas: tuple[str, ...]
    description: str

    @property
    def projection_only(self) -> bool:
        return self.execution_mode == "projection_only"


FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILES: dict[str, FullIdentityProtocolScanProjectionProfile] = {
    "full": FullIdentityProtocolScanProjectionProfile(
        profile_id="full",
        execution_mode="full_verdict",
        host_visible_post_check_metrics_enabled=True,
        excluded_areas=(),
        description=(
            "Run the complete validator/check matrix and emit the full governed scan summary surface."
        ),
    ),
    "terminal_truth_boundary_projection": FullIdentityProtocolScanProjectionProfile(
        profile_id="terminal_truth_boundary_projection",
        execution_mode="projection_only",
        host_visible_post_check_metrics_enabled=False,
        excluded_areas=(
            "release_cloud_evidence_adapter",
            "host_visible_post_check_metrics",
            "health_report_experience_writeback_closure",
        ),
        description=(
            "Run the governed outer-surface terminal-truth projection path only: preserve "
            "three-plane terminal-truth projections, aggregate summary_terminal_truth_boundary, "
            "and keep health-report companion closure bounded as an explicit projection-only "
            "exclusion while excluding unrelated validator-matrix/fleet-summary lanes from the "
            "scan path."
        ),
    ),
}

DEFAULT_FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILE = "full"


def full_identity_protocol_scan_projection_profile_choices() -> tuple[str, ...]:
    return tuple(FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILES.keys())


def resolve_full_identity_protocol_scan_projection_profile(
    profile_id: str,
) -> FullIdentityProtocolScanProjectionProfile:
    token = str(profile_id or "").strip().lower() or DEFAULT_FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILE
    try:
        return FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILES[token]
    except KeyError as exc:
        allowed = ", ".join(sorted(FULL_IDENTITY_PROTOCOL_SCAN_PROJECTION_PROFILES))
        raise ValueError(f"unknown full-identity-protocol-scan projection profile: {token} (allowed: {allowed})") from exc
