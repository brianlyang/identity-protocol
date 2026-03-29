#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from full_scan_required_gate_bundle_projection_common import (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
)
from health_report_experience_writeback_projection_common import (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS,
)
from release_cloud_evidence_projection_common import (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER,
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS,
)
from release_closure_root_grounding_common import (
    RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER,
    RELEASE_CLOSURE_ROOT_GROUNDING_SURFACE_CONSTRAINTS,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_foundational_projection_common import (
    RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
    RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_TARGETED_SUBSET_MARKER,
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
)
from release_readiness_support_preflight_projection_common import (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
    RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_FIELDS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS,
)


@dataclass(frozen=True)
class ReleaseClosureProjectionCompanionMarkerBundleSpec:
    stale_reason_prefix: str
    markers: tuple[str, ...]


RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID = "summary"
RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID = "boundary"


RELEASE_CLOSURE_SUMMARY_OUTER_SURFACE_E2E_COMPANION_MARKER = (
    "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh"
)
RELEASE_CLOSURE_SUMMARY_OUTER_SURFACE_E2E_COMPANION_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_OUTER_SURFACE_E2E_COMPANION_MARKER,
    "terminal_truth_boundary_projection",
    "three_plane_terminal_truth_boundary_projection",
    "summary_terminal_truth_boundary",
    "one_look.terminal_truth_boundary_projection_status",
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OUTER_SURFACE_E2E_MARKERS,
)

RELEASE_CLOSURE_SUMMARY_HEALTH_PROJECTION_COMPANION_MARKER = (
    "health_report_experience_writeback_closure"
)
RELEASE_CLOSURE_SUMMARY_HEALTH_PROJECTION_COMPANION_MARKERS = (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS
)

RELEASE_CLOSURE_SUMMARY_RELEASE_CLOUD_EVIDENCE_COMPANION_MARKER = (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER
)
RELEASE_CLOSURE_SUMMARY_RELEASE_CLOUD_EVIDENCE_COMPANION_MARKERS = (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_SELECTED_CHECK_SCOPE_COMPANION_MARKER = (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_TARGETED_SUBSET_MARKER
)
RELEASE_CLOSURE_SUMMARY_SELECTED_CHECK_SCOPE_COMPANION_MARKERS = (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_COMPANION_MARKER = (
    RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER
)
RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_COMPANION_MARKERS = (
    RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_ONE_LOOK_TOPOLOGY_COMPANION_MARKER = (
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER
)
RELEASE_CLOSURE_SUMMARY_ONE_LOOK_TOPOLOGY_COMPANION_MARKERS = (
    RELEASE_READINESS_ONE_LOOK_TOPOLOGY_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_SUPPORT_PREFLIGHT_COMPANION_MARKER = (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER
)
RELEASE_CLOSURE_SUMMARY_SUPPORT_PREFLIGHT_COMPANION_MARKERS = (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKER = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER
)
RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKERS = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_FIELDS
)
RELEASE_CLOSURE_SUMMARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKER = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER
)
RELEASE_CLOSURE_SUMMARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKERS = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_ROOT_GROUNDING_COMPANION_MARKER = (
    RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER
)
RELEASE_CLOSURE_SUMMARY_ROOT_GROUNDING_COMPANION_MARKERS = (
    RELEASE_CLOSURE_ROOT_GROUNDING_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_SUMMARY_FULL_SCAN_REQUIRED_GATE_COMPANION_MARKER = (
    "scripts/ci/run_full_scan_required_gate_projection_probes_ci.sh"
)
RELEASE_CLOSURE_SUMMARY_FULL_SCAN_REQUIRED_GATE_COMPANION_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_FULL_SCAN_REQUIRED_GATE_COMPANION_MARKER,
    *FULL_SCAN_REQUIRED_GATE_BUNDLE_SURFACE_CONSTRAINTS,
)
RELEASE_CLOSURE_SUMMARY_ACTIVE_RUNTIME_COMPANION_MARKER = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER
)
RELEASE_CLOSURE_SUMMARY_ACTIVE_RUNTIME_COMPANION_MARKERS = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS
)

RELEASE_CLOSURE_BOUNDARY_OUTER_SURFACE_E2E_COMPANION_MARKER = (
    "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh"
)
RELEASE_CLOSURE_BOUNDARY_OUTER_SURFACE_E2E_COMPANION_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_BOUNDARY_OUTER_SURFACE_E2E_COMPANION_MARKER,
    "terminal_truth_boundary_projection",
    "summary_terminal_truth_boundary",
)
RELEASE_CLOSURE_BOUNDARY_ACTIVE_RUNTIME_COMPANION_MARKER = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER
)
RELEASE_CLOSURE_BOUNDARY_ACTIVE_RUNTIME_COMPANION_MARKERS = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKER = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER
)
RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKERS = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_FIELDS
)
RELEASE_CLOSURE_BOUNDARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKER = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER
)
RELEASE_CLOSURE_BOUNDARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKERS = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_BOUNDARY_ROOT_GROUNDING_COMPANION_MARKER = (
    RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER
)
RELEASE_CLOSURE_BOUNDARY_ROOT_GROUNDING_COMPANION_MARKERS = (
    RELEASE_CLOSURE_ROOT_GROUNDING_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_BOUNDARY_REPO_GLOBAL_COMPANION_MARKER = (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER
)
RELEASE_CLOSURE_BOUNDARY_REPO_GLOBAL_COMPANION_MARKERS = (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_SURFACE_CONSTRAINTS
)
RELEASE_CLOSURE_BOUNDARY_HEALTH_PROJECTION_COMPANION_MARKER = (
    "health_report_experience_writeback_closure"
)
RELEASE_CLOSURE_BOUNDARY_HEALTH_PROJECTION_COMPANION_MARKERS = (
    RELEASE_READINESS_HEALTH_REPORT_EXPERIENCE_WRITEBACK_SURFACE_CONSTRAINTS
)

RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureProjectionCompanionMarkerBundleSpec,
    ...,
] = (
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_outer_surface_e2e_marker",
        markers=RELEASE_CLOSURE_SUMMARY_OUTER_SURFACE_E2E_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_health_projection_marker",
        markers=RELEASE_CLOSURE_SUMMARY_HEALTH_PROJECTION_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_release_cloud_evidence_marker",
        markers=RELEASE_CLOSURE_SUMMARY_RELEASE_CLOUD_EVIDENCE_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_selected_check_scope_marker",
        markers=RELEASE_CLOSURE_SUMMARY_SELECTED_CHECK_SCOPE_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_foundational_marker",
        markers=RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_one_look_topology_marker",
        markers=RELEASE_CLOSURE_SUMMARY_ONE_LOOK_TOPOLOGY_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_support_preflight_marker",
        markers=RELEASE_CLOSURE_SUMMARY_SUPPORT_PREFLIGHT_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_terminal_truth_bridge_marker",
        markers=RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_terminal_truth_bridge_rich_companion_marker",
        markers=RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_post_closure_adjudication_marker",
        markers=RELEASE_CLOSURE_SUMMARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_closure_root_grounding_marker",
        markers=RELEASE_CLOSURE_SUMMARY_ROOT_GROUNDING_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_full_scan_required_gate_projection_marker",
        markers=RELEASE_CLOSURE_SUMMARY_FULL_SCAN_REQUIRED_GATE_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_active_runtime_closure_projection_marker",
        markers=RELEASE_CLOSURE_SUMMARY_ACTIVE_RUNTIME_COMPANION_MARKERS,
    ),
)

RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureProjectionCompanionMarkerBundleSpec,
    ...,
] = (
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_outer_surface_e2e_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_OUTER_SURFACE_E2E_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_active_runtime_closure_projection_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_ACTIVE_RUNTIME_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_terminal_truth_bridge_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_terminal_truth_bridge_rich_companion_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_post_closure_adjudication_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_POST_CLOSURE_ADJUDICATION_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_closure_root_grounding_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_ROOT_GROUNDING_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_repo_global_closure_boundary_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_REPO_GLOBAL_COMPANION_MARKERS,
    ),
    ReleaseClosureProjectionCompanionMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_health_projection_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_HEALTH_PROJECTION_COMPANION_MARKERS,
    ),
)


def release_closure_projection_companion_bundle_specs_for_surface(
    surface_id: str,
) -> tuple[ReleaseClosureProjectionCompanionMarkerBundleSpec, ...]:
    if surface_id == RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID:
        return RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS
    if surface_id == RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID:
        return RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS
    raise ValueError(f"unsupported release closure projection companion surface: {surface_id}")


def find_release_closure_projection_companion_bundle_spec(
    *,
    surface_id: str,
    stale_reason_prefix: str,
) -> ReleaseClosureProjectionCompanionMarkerBundleSpec | None:
    for spec in release_closure_projection_companion_bundle_specs_for_surface(surface_id):
        if spec.stale_reason_prefix == stale_reason_prefix:
            return spec
    return None


def collect_release_closure_projection_companion_marker_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    bundle_specs: tuple[ReleaseClosureProjectionCompanionMarkerBundleSpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in bundle_specs:
        for marker in spec.markers:
            if marker not in text:
                stale_reasons.append(f"{label}_{spec.stale_reason_prefix}:{marker}")
    return stale_reasons


def collect_release_closure_summary_projection_companion_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_projection_companion_marker_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS,
    )


def collect_release_closure_boundary_projection_companion_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_projection_companion_marker_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS,
    )


def _validate_release_closure_projection_companion_bundle_specs() -> None:
    for surface_name, bundle_specs in (
        ("summary", RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS),
    ):
        seen_prefixes: set[str] = set()
        for spec in bundle_specs:
            if not spec.markers:
                raise RuntimeError(
                    f"release_closure_projection_companion_bundle_empty:{surface_name}:{spec.stale_reason_prefix}"
                )
            if spec.stale_reason_prefix in seen_prefixes:
                raise RuntimeError(
                    f"release_closure_projection_companion_duplicate_prefix:{surface_name}:{spec.stale_reason_prefix}"
                )
            seen_prefixes.add(spec.stale_reason_prefix)


_validate_release_closure_projection_companion_bundle_specs()
