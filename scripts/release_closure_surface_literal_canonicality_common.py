#!/usr/bin/env python3
from __future__ import annotations


def collect_release_closure_surface_literal_stale_reasons(
    text: str,
    *,
    label: str,
    literal_key: str,
    canonical_marker: str,
    stale_reason_suffix: str,
) -> list[str]:
    literal_lines = [
        line.strip()
        for line in text.splitlines()
        if f"{literal_key}=" in line
    ]
    if any(canonical_marker not in line for line in literal_lines):
        return [f"{label}_{stale_reason_suffix}"]
    return []
