#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ReleaseClosureSurfaceLiteralCanonicalitySpec:
    literal_key: str
    canonical_marker: str
    stale_reason_suffix: str


def collect_release_closure_surface_literal_stale_reasons(
    text: str,
    *,
    label: str,
    literal_key: str,
    canonical_marker: str,
    stale_reason_suffix: str,
) -> list[str]:
    literal_pattern = re.compile(
        rf"(^|[^A-Za-z0-9_]){re.escape(literal_key)}="
    )
    literal_lines = [
        line.strip()
        for line in text.splitlines()
        if literal_pattern.search(line)
    ]
    if any(canonical_marker not in line for line in literal_lines):
        return [f"{label}_{stale_reason_suffix}"]
    return []


def collect_release_closure_surface_literal_spec_stale_reasons(
    text: str,
    *,
    label: str,
    spec: ReleaseClosureSurfaceLiteralCanonicalitySpec,
) -> list[str]:
    return collect_release_closure_surface_literal_stale_reasons(
        text,
        label=label,
        literal_key=spec.literal_key,
        canonical_marker=spec.canonical_marker,
        stale_reason_suffix=spec.stale_reason_suffix,
    )


def collect_release_closure_surface_literal_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    specs: tuple[ReleaseClosureSurfaceLiteralCanonicalitySpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in specs:
        stale_reasons.extend(
            collect_release_closure_surface_literal_spec_stale_reasons(
                text,
                label=label,
                spec=spec,
            )
        )
    return stale_reasons
