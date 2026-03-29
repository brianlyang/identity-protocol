#!/usr/bin/env python3
from __future__ import annotations

from release_closure_control_surface_literal_bundle_common import (
    RELEASE_CLOSURE_GOVERNANCE_PROBE_PROJECTION_LITERAL_CANONICALITY_SPEC,
)
from release_closure_surface_literal_canonicality_common import (
    collect_release_closure_surface_literal_spec_stale_reasons,
)


def collect_release_closure_governance_probe_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_spec_stale_reasons(
        text,
        label=label,
        spec=RELEASE_CLOSURE_GOVERNANCE_PROBE_PROJECTION_LITERAL_CANONICALITY_SPEC,
    )
