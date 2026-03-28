#!/usr/bin/env python3
from __future__ import annotations

from release_closure_surface_literal_canonicality_common import (
    collect_release_closure_surface_literal_stale_reasons,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
)


def collect_release_closure_governance_probe_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_stale_reasons(
        text,
        label=label,
        literal_key="governance_probe_projection",
        canonical_marker=RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
        stale_reason_suffix="governance_probe_projection_line_not_canonical",
    )
