#!/usr/bin/env python3
from __future__ import annotations

from release_closure_bounded_projection_literal_bundle_common import (
    RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS,
    collect_release_closure_bounded_projection_literal_bundle_stale_reasons,
)

RELEASE_CLOSURE_SUMMARY_LITERAL_CANONICALITY_SPECS = (
    RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS
)


def collect_release_closure_summary_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_bounded_projection_literal_bundle_stale_reasons(
        text,
        label=label,
    )
