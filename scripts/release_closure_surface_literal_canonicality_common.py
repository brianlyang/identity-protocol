#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ReleaseClosureSurfaceLiteralCanonicalitySpec:
    literal_key: str
    canonical_marker: str
    stale_reason_suffix: str


def _collect_literal_fragments(
    text: str,
    *,
    literal_key: str,
) -> list[str]:
    quoted_pattern = re.compile(
        rf"`({re.escape(literal_key)}=[^`\n]+)`"
    )
    quoted_fragments = [match.group(1).strip() for match in quoted_pattern.finditer(text)]
    if quoted_fragments:
        return quoted_fragments

    bare_pattern = re.compile(
        rf"({re.escape(literal_key)}=[^\s`,;]+)"
    )
    return [match.group(1).strip() for match in bare_pattern.finditer(text)]


def collect_release_closure_surface_literal_stale_reasons(
    text: str,
    *,
    label: str,
    literal_key: str,
    canonical_marker: str,
    stale_reason_suffix: str,
) -> list[str]:
    literal_fragments = _collect_literal_fragments(
        text,
        literal_key=literal_key,
    )
    if any(fragment != canonical_marker for fragment in literal_fragments):
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
