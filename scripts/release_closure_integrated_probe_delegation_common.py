#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
)
from release_closure_surface_registry_common import (
    release_closure_surface_spec_by_bundle_surface_id,
)


RELEASE_CLOSURE_INTEGRATED_PROBE_COMMON_REL = (
    "scripts/release_closure_integrated_probe_common.py"
)
RELEASE_CLOSURE_INTEGRATED_PROBE_SUMMARY_PROFILE_ID = "summary"
RELEASE_CLOSURE_INTEGRATED_PROBE_BOUNDARY_PROFILE_ID = "boundary"
_SUMMARY_SURFACE_SPEC = release_closure_surface_spec_by_bundle_surface_id("summary")
_BOUNDARY_SURFACE_SPEC = release_closure_surface_spec_by_bundle_surface_id("boundary")
if _SUMMARY_SURFACE_SPEC is None or _BOUNDARY_SURFACE_SPEC is None:
    raise RuntimeError("release_closure_integrated_probe_delegation_missing_surface_specs")
RELEASE_CLOSURE_SUMMARY_PROBE_SCRIPT_REL = _SUMMARY_SURFACE_SPEC.probe_script_rel
RELEASE_CLOSURE_BOUNDARY_PROBE_SCRIPT_REL = _BOUNDARY_SURFACE_SPEC.probe_script_rel


@dataclass(frozen=True)
class ReleaseClosureIntegratedProbeDelegatedResolutionSpec:
    resolution_id: str
    resolution_token: str
    resolved_value: str
    stale_reason: str


@dataclass(frozen=True)
class ReleaseClosureIntegratedProbeDelegationSpec:
    probe_script_rel: str
    helper_rel: str
    helper_profile_id: str
    delegated_resolutions: tuple[ReleaseClosureIntegratedProbeDelegatedResolutionSpec, ...]


RELEASE_CLOSURE_SUMMARY_INTEGRATED_PROBE_DELEGATION_SPEC = (
    ReleaseClosureIntegratedProbeDelegationSpec(
        probe_script_rel=RELEASE_CLOSURE_SUMMARY_PROBE_SCRIPT_REL,
        helper_rel=RELEASE_CLOSURE_INTEGRATED_PROBE_COMMON_REL,
        helper_profile_id=RELEASE_CLOSURE_INTEGRATED_PROBE_SUMMARY_PROFILE_ID,
        delegated_resolutions=(
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_projection_marker",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
                stale_reason="repo_global_summary_probe_missing_projection_marker_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_checked_identity_count",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
                stale_reason="repo_global_summary_probe_missing_checked_count_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_topology_lane",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
                stale_reason="repo_global_summary_probe_missing_topology_lane_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="active_runtime_projection_marker",
                resolution_token="RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER",
                resolved_value=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
                stale_reason="active_runtime_summary_probe_missing_projection_marker_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="active_runtime_negative_feedback_veto_field",
                resolution_token="RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD",
                resolved_value=RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
                stale_reason="active_runtime_summary_probe_missing_projection_marker_resolution",
            ),
        ),
    )
)

RELEASE_CLOSURE_BOUNDARY_INTEGRATED_PROBE_DELEGATION_SPEC = (
    ReleaseClosureIntegratedProbeDelegationSpec(
        probe_script_rel=RELEASE_CLOSURE_BOUNDARY_PROBE_SCRIPT_REL,
        helper_rel=RELEASE_CLOSURE_INTEGRATED_PROBE_COMMON_REL,
        helper_profile_id=RELEASE_CLOSURE_INTEGRATED_PROBE_BOUNDARY_PROFILE_ID,
        delegated_resolutions=(
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_projection_marker",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
                stale_reason="repo_global_boundary_probe_missing_projection_marker_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_checked_identity_count",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
                stale_reason="repo_global_boundary_probe_missing_checked_count_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="repo_global_topology_lane",
                resolution_token="RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT",
                resolved_value=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
                stale_reason="repo_global_boundary_probe_missing_topology_lane_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="active_runtime_projection_marker",
                resolution_token="RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER",
                resolved_value=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
                stale_reason="active_runtime_boundary_probe_missing_projection_marker_resolution",
            ),
            ReleaseClosureIntegratedProbeDelegatedResolutionSpec(
                resolution_id="active_runtime_negative_feedback_veto_field",
                resolution_token="RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD",
                resolved_value=RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
                stale_reason="active_runtime_boundary_probe_missing_detail_field_resolution",
            ),
        ),
    )
)

RELEASE_CLOSURE_INTEGRATED_PROBE_DELEGATION_SPECS: tuple[
    ReleaseClosureIntegratedProbeDelegationSpec,
    ...,
] = (
    RELEASE_CLOSURE_SUMMARY_INTEGRATED_PROBE_DELEGATION_SPEC,
    RELEASE_CLOSURE_BOUNDARY_INTEGRATED_PROBE_DELEGATION_SPEC,
)


def release_closure_integrated_probe_delegation_spec_for_script(
    probe_script_rel: str,
) -> ReleaseClosureIntegratedProbeDelegationSpec | None:
    return next(
        (
            spec
            for spec in RELEASE_CLOSURE_INTEGRATED_PROBE_DELEGATION_SPECS
            if spec.probe_script_rel == probe_script_rel
        ),
        None,
    )


def release_closure_integrated_probe_delegated_resolution_by_id(
    spec: ReleaseClosureIntegratedProbeDelegationSpec,
    resolution_id: str,
) -> ReleaseClosureIntegratedProbeDelegatedResolutionSpec | None:
    return next(
        (
            resolution
            for resolution in spec.delegated_resolutions
            if resolution.resolution_id == resolution_id
        ),
        None,
    )


def _validate_release_closure_integrated_probe_delegation_specs() -> None:
    seen_probe_scripts: set[str] = set()
    for spec in RELEASE_CLOSURE_INTEGRATED_PROBE_DELEGATION_SPECS:
        if spec.probe_script_rel in seen_probe_scripts:
            raise RuntimeError(
                "release_closure_integrated_probe_delegation_duplicate_probe_script:"
                + spec.probe_script_rel
            )
        seen_probe_scripts.add(spec.probe_script_rel)
        if not spec.delegated_resolutions:
            raise RuntimeError(
                "release_closure_integrated_probe_delegation_empty_resolutions:"
                + spec.probe_script_rel
            )
        seen_resolution_ids: set[str] = set()
        for resolution in spec.delegated_resolutions:
            if resolution.resolution_id in seen_resolution_ids:
                raise RuntimeError(
                    "release_closure_integrated_probe_delegation_duplicate_resolution_id:"
                    + f"{spec.probe_script_rel}:{resolution.resolution_id}"
                )
            seen_resolution_ids.add(resolution.resolution_id)
            if not resolution.resolution_token or not resolution.resolved_value:
                raise RuntimeError(
                    "release_closure_integrated_probe_delegation_incomplete_resolution:"
                    + f"{spec.probe_script_rel}:{resolution.resolution_id}"
                )


_validate_release_closure_integrated_probe_delegation_specs()
