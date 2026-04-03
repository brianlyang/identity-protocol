#!/usr/bin/env python3
from __future__ import annotations

from release_closure_surface_literal_canonicality_common import (
    ReleaseClosureSurfaceLiteralCanonicalitySpec,
    collect_release_closure_surface_literal_bundle_stale_reasons,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
)


RELEASE_CLOSURE_REPO_GLOBAL_PROJECTION_LITERAL_CANONICALITY_SPEC = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="repo_global_closure_projection",
        canonical_marker=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        stale_reason_suffix="repo_global_closure_projection_line_not_canonical",
    )
)

RELEASE_CLOSURE_ACTIVE_RUNTIME_PROJECTION_LITERAL_CANONICALITY_SPEC = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="active_runtime_closure_projection",
        canonical_marker=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        stale_reason_suffix="active_runtime_closure_projection_line_not_canonical",
    )
)

RELEASE_CLOSURE_GOVERNANCE_PROBE_PROJECTION_LITERAL_CANONICALITY_SPEC = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="governance_probe_projection",
        canonical_marker=RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
        stale_reason_suffix="governance_probe_projection_line_not_canonical",
    )
)

RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_LITERAL_CANONICALITY_SPEC = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="terminal_truth_bridge_surface",
        canonical_marker=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        stale_reason_suffix="terminal_truth_bridge_surface_line_not_canonical",
    )
)

RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_LITERAL_CANONICALITY_SPEC = (
    ReleaseClosureSurfaceLiteralCanonicalitySpec(
        literal_key="release_readiness_post_closure_adjudication_order",
        canonical_marker=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        stale_reason_suffix="post_closure_adjudication_order_line_not_canonical",
    )
)

RELEASE_CLOSURE_CONTROL_SURFACE_LITERAL_CANONICALITY_SPECS: tuple[
    ReleaseClosureSurfaceLiteralCanonicalitySpec,
    ...,
] = (
    RELEASE_CLOSURE_REPO_GLOBAL_PROJECTION_LITERAL_CANONICALITY_SPEC,
    RELEASE_CLOSURE_ACTIVE_RUNTIME_PROJECTION_LITERAL_CANONICALITY_SPEC,
    RELEASE_CLOSURE_GOVERNANCE_PROBE_PROJECTION_LITERAL_CANONICALITY_SPEC,
    RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_LITERAL_CANONICALITY_SPEC,
    RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_LITERAL_CANONICALITY_SPEC,
)

RELEASE_CLOSURE_SUMMARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS = (
    RELEASE_CLOSURE_CONTROL_SURFACE_LITERAL_CANONICALITY_SPECS
)
RELEASE_CLOSURE_BOUNDARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS = (
    RELEASE_CLOSURE_CONTROL_SURFACE_LITERAL_CANONICALITY_SPECS
)


def collect_release_closure_control_surface_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    specs: tuple[ReleaseClosureSurfaceLiteralCanonicalitySpec, ...],
) -> list[str]:
    return collect_release_closure_surface_literal_bundle_stale_reasons(
        text,
        label=label,
        specs=specs,
    )


def collect_release_closure_summary_control_surface_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_control_surface_literal_bundle_stale_reasons(
        text,
        label=label,
        specs=RELEASE_CLOSURE_SUMMARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS,
    )


def collect_release_closure_boundary_control_surface_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_control_surface_literal_bundle_stale_reasons(
        text,
        label=label,
        specs=RELEASE_CLOSURE_BOUNDARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS,
    )


def _validate_release_closure_control_surface_literal_specs() -> None:
    canonical_specs = set(RELEASE_CLOSURE_CONTROL_SURFACE_LITERAL_CANONICALITY_SPECS)
    for surface_name, specs in (
        ("summary", RELEASE_CLOSURE_SUMMARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_CONTROL_SURFACE_LITERAL_BUNDLE_SPECS),
    ):
        if not specs:
            raise RuntimeError(
                f"release_closure_control_surface_literal_bundle_empty:{surface_name}"
            )
        seen_literal_keys: set[str] = set()
        seen_stale_suffixes: set[str] = set()
        seen_specs: set[ReleaseClosureSurfaceLiteralCanonicalitySpec] = set()
        for spec in specs:
            if spec.literal_key in seen_literal_keys:
                raise RuntimeError(
                    f"release_closure_control_surface_literal_duplicate_key:{surface_name}:{spec.literal_key}"
                )
            if spec.stale_reason_suffix in seen_stale_suffixes:
                raise RuntimeError(
                    f"release_closure_control_surface_literal_duplicate_stale_suffix:{surface_name}:{spec.stale_reason_suffix}"
                )
            seen_literal_keys.add(spec.literal_key)
            seen_stale_suffixes.add(spec.stale_reason_suffix)
            seen_specs.add(spec)
        if seen_specs != canonical_specs:
            missing_keys = sorted(spec.literal_key for spec in canonical_specs if spec not in seen_specs)
            raise RuntimeError(
                f"release_closure_control_surface_literal_bundle_incomplete:{surface_name}:{','.join(missing_keys)}"
            )


_validate_release_closure_control_surface_literal_specs()
