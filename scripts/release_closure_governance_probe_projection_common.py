#!/usr/bin/env python3
from __future__ import annotations

from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
)


def collect_release_closure_governance_probe_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    projection_lines = [
        line.strip()
        for line in text.splitlines()
        if "governance_probe_projection=" in line
    ]
    if any(
        RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER not in line
        for line in projection_lines
    ):
        return [f"{label}_governance_probe_projection_line_not_canonical"]
    return []
