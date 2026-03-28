#!/usr/bin/env python3
from __future__ import annotations

from release_closure_projection_line_canonicality_common import (
    collect_release_closure_projection_line_stale_reasons,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
)


def collect_release_closure_active_runtime_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_projection_line_stale_reasons(
        text,
        label=label,
        projection_key="active_runtime_closure_projection",
        canonical_marker=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        stale_reason_suffix="active_runtime_closure_projection_line_not_canonical",
    )
