#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from release_closure_continuation_marker_common import (
    RELEASE_CLOSURE_BOUNDARY_CONTINUATION_MARKERS,
    RELEASE_CLOSURE_SUMMARY_CONTINUATION_MARKERS,
)
from release_readiness_runtime_closure_convergence_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
)


@dataclass(frozen=True)
class ReleaseClosureOperationalMarkerBundleSpec:
    stale_reason_prefix: str
    markers: tuple[str, ...]


RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureOperationalMarkerBundleSpec,
    ...
] = (
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_lifecycle_marker",
        markers=RELEASE_CLOSURE_SUMMARY_CONTINUATION_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_transport_fleet_closure_convergence_marker",
        markers=RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_active_runtime_pack_closure_convergence_marker",
        markers=RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_workspace_runtime_closure_command_convergence_marker",
        markers=RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
    ),
)

RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureOperationalMarkerBundleSpec,
    ...
] = (
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_release_readiness_continuation_marker",
        markers=RELEASE_CLOSURE_BOUNDARY_CONTINUATION_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_transport_fleet_closure_convergence_marker",
        markers=RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_active_runtime_pack_closure_convergence_marker",
        markers=RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    ),
    ReleaseClosureOperationalMarkerBundleSpec(
        stale_reason_prefix="missing_workspace_runtime_closure_command_convergence_marker",
        markers=RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
    ),
)


def collect_release_closure_operational_marker_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    bundle_specs: tuple[ReleaseClosureOperationalMarkerBundleSpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in bundle_specs:
        for marker in spec.markers:
            if marker not in text:
                stale_reasons.append(f"{label}_{spec.stale_reason_prefix}:{marker}")
    return stale_reasons
