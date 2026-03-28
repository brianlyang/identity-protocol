#!/usr/bin/env python3
from __future__ import annotations


def collect_release_closure_projection_line_stale_reasons(
    text: str,
    *,
    label: str,
    projection_key: str,
    canonical_marker: str,
    stale_reason_suffix: str,
) -> list[str]:
    projection_lines = [
        line.strip()
        for line in text.splitlines()
        if f"{projection_key}=" in line
    ]
    if any(canonical_marker not in line for line in projection_lines):
        return [f"{label}_{stale_reason_suffix}"]
    return []
