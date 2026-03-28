#!/usr/bin/env python3
from __future__ import annotations

from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)


def collect_release_closure_repo_global_projection_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    projection_lines = [
        line.strip()
        for line in text.splitlines()
        if "repo_global_closure_projection=" in line
    ]
    if any(
        RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER not in line
        for line in projection_lines
    ):
        return [f"{label}_repo_global_closure_projection_line_not_canonical"]
    return []
