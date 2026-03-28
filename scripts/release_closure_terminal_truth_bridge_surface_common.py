#!/usr/bin/env python3
from __future__ import annotations

from release_closure_surface_literal_canonicality_common import (
    collect_release_closure_surface_literal_stale_reasons,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
)


def collect_release_closure_terminal_truth_bridge_surface_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_surface_literal_stale_reasons(
        text,
        label=label,
        literal_key="terminal_truth_bridge_surface",
        canonical_marker=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        stale_reason_suffix="terminal_truth_bridge_surface_line_not_canonical",
    )
