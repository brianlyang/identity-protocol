#!/usr/bin/env python3
from __future__ import annotations

from full_scan_required_gate_bundle_projection_common import (
    FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
    FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER,
)
from projection_profile_exclusion_scope_common import (
    PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS,
)
from release_cloud_evidence_projection_common import (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER,
)
from release_closure_surface_literal_canonicality_common import (
    ReleaseClosureSurfaceLiteralCanonicalitySpec,
    collect_release_closure_surface_literal_bundle_stale_reasons,
)
from release_readiness_foundational_projection_common import (
    RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
)
from release_readiness_required_gate_bundle_projection_common import (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
)
from release_readiness_required_gate_bundle_scope_common import (
    RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER,
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS,
)
from release_readiness_support_preflight_projection_common import (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
)
from terminal_truth_boundary_projection_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_PROJECTION_MARKER,
)


RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS: tuple[
    ReleaseClosureSurfaceLiteralCanonicalitySpec,
    ...
] = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="projection_profile_exclusion_scope",
        canonical_marker=PROJECTION_PROFILE_EXCLUSION_SURFACE_CONSTRAINTS[0],
        stale_reason_suffix="projection_profile_exclusion_scope_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_cloud_evidence_projection",
        canonical_marker=RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER,
        stale_reason_suffix="release_cloud_evidence_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="targeted_subset_required_gate_bundle_scope",
        canonical_marker=RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS[0],
        stale_reason_suffix="targeted_subset_required_gate_bundle_scope_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="targeted_subset_required_gate_bundle_scope_reason",
        canonical_marker=RELEASE_READINESS_REQUIRED_GATE_BUNDLE_SCOPE_SURFACE_CONSTRAINTS[1],
        stale_reason_suffix="targeted_subset_required_gate_bundle_scope_reason_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="targeted_subset_selected_check_scope",
        canonical_marker=RELEASE_READINESS_SELECTED_CHECK_SCOPE_SURFACE_CONSTRAINTS[0],
        stale_reason_suffix="targeted_subset_selected_check_scope_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_selected_check_scope_projection",
        canonical_marker=RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER,
        stale_reason_suffix="release_readiness_selected_check_scope_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_one_look_family_order",
        canonical_marker=RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
        stale_reason_suffix="release_readiness_one_look_family_order_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_foundational_projection",
        canonical_marker=RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
        stale_reason_suffix="release_readiness_foundational_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_support_preflight_projection",
        canonical_marker=RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
        stale_reason_suffix="release_readiness_support_preflight_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_terminal_truth_boundary_projection",
        canonical_marker=RELEASE_READINESS_TERMINAL_TRUTH_BOUNDARY_PROJECTION_MARKER,
        stale_reason_suffix="release_readiness_terminal_truth_boundary_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="required_gate_bundle_projection",
        canonical_marker=RELEASE_READINESS_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
        stale_reason_suffix="required_gate_bundle_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="full_scan_required_gate_bundle_projection",
        canonical_marker=FULL_SCAN_REQUIRED_GATE_BUNDLE_PROJECTION_MARKER,
        stale_reason_suffix="full_scan_required_gate_bundle_projection_line_not_canonical",
    ),
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="full_scan_required_gate_bundle_summary",
        canonical_marker=FULL_SCAN_REQUIRED_GATE_BUNDLE_SUMMARY_MARKER,
        stale_reason_suffix="full_scan_required_gate_bundle_summary_line_not_canonical",
    ),
)


def collect_release_closure_bounded_projection_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_bundle_stale_reasons(
        text,
        label=label,
        specs=RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS,
    )
