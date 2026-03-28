#!/usr/bin/env python3
from __future__ import annotations

from release_closure_surface_literal_canonicality_common import (
    collect_release_closure_surface_literal_stale_reasons,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)


def collect_release_closure_repo_global_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_stale_reasons(
        text,
        label=label,
        literal_key="repo_global_closure_projection",
        canonical_marker=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        stale_reason_suffix="repo_global_closure_projection_line_not_canonical",
    )
