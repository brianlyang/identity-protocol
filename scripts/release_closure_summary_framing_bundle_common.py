#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseClosureSummaryFramingSpec:
    framing_family: str
    markers: tuple[str, ...]
    stale_reason_mode: str
    stale_reason_token: str


@dataclass(frozen=True)
class ReleaseClosureSummaryFramingBundleSpec:
    bundle_key: str
    framing_specs: tuple[ReleaseClosureSummaryFramingSpec, ...]


RELEASE_CLOSURE_SUMMARY_QUESTION_CLASS_MARKER = (
    "Question class and authoritative answer surfaces"
)
RELEASE_CLOSURE_SUMMARY_QUESTION_CLASS_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_QUESTION_CLASS_MARKER,
)

RELEASE_CLOSURE_SUMMARY_RUNTIME_VERDICT_SCOPE_MARKER = "runtime verdict surface"
RELEASE_CLOSURE_SUMMARY_FLEET_SCOPE_CLOSURE_MATRIX_MARKER = (
    "fleet-scope closure matrix"
)
RELEASE_CLOSURE_SUMMARY_SCOPE_SEPARATION_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_RUNTIME_VERDICT_SCOPE_MARKER,
    RELEASE_CLOSURE_SUMMARY_FLEET_SCOPE_CLOSURE_MATRIX_MARKER,
)

RELEASE_CLOSURE_SUMMARY_RELEASE_TAG_BOUNDARY_MARKER = "not declare a release tag"
RELEASE_CLOSURE_SUMMARY_RELEASE_TAG_BOUNDARY_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_RELEASE_TAG_BOUNDARY_MARKER,
)

RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_GO_MARKER = (
    "Workspace-local core-role required closure: **Go**"
)
RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_GREEN_SCOPE_MARKER = (
    "workspace-local core release scope is now green on required closure"
)
RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_GO_MARKER,
    RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_GREEN_SCOPE_MARKER,
)

RELEASE_CLOSURE_SUMMARY_FRAMING_SPECS: tuple[ReleaseClosureSummaryFramingSpec, ...] = (
    ReleaseClosureSummaryFramingSpec(
        framing_family="question_class_section",
        markers=RELEASE_CLOSURE_SUMMARY_QUESTION_CLASS_MARKERS,
        stale_reason_mode="required_aggregate",
        stale_reason_token="summary_doc_missing_question_class_section",
    ),
    ReleaseClosureSummaryFramingSpec(
        framing_family="scope_separation",
        markers=RELEASE_CLOSURE_SUMMARY_SCOPE_SEPARATION_MARKERS,
        stale_reason_mode="required_aggregate",
        stale_reason_token="summary_doc_missing_scope_separation_markers",
    ),
    ReleaseClosureSummaryFramingSpec(
        framing_family="release_tag_boundary",
        markers=RELEASE_CLOSURE_SUMMARY_RELEASE_TAG_BOUNDARY_MARKERS,
        stale_reason_mode="required_aggregate",
        stale_reason_token="summary_doc_missing_release_tag_boundary",
    ),
    ReleaseClosureSummaryFramingSpec(
        framing_family="forbidden_stale_markers",
        markers=RELEASE_CLOSURE_SUMMARY_FORBIDDEN_STALE_MARKERS,
        stale_reason_mode="forbidden_per_marker",
        stale_reason_token="summary_doc_contains_stale_marker",
    ),
)


def _select_summary_framing_specs(
    *framing_families: str,
) -> tuple[ReleaseClosureSummaryFramingSpec, ...]:
    selected_specs: list[ReleaseClosureSummaryFramingSpec] = []
    family_pool = set(framing_families)
    for spec in RELEASE_CLOSURE_SUMMARY_FRAMING_SPECS:
        if spec.framing_family in family_pool:
            selected_specs.append(spec)
            family_pool.remove(spec.framing_family)
    if family_pool:
        missing = ",".join(sorted(family_pool))
        raise RuntimeError(f"release_closure_summary_framing_spec_unresolved:{missing}")
    return tuple(selected_specs)


RELEASE_CLOSURE_SUMMARY_FRAMING_BUNDLE_SPECS: tuple[
    ReleaseClosureSummaryFramingBundleSpec,
    ...,
] = (
    ReleaseClosureSummaryFramingBundleSpec(
        bundle_key="summary_adjudication_framing",
        framing_specs=_select_summary_framing_specs(
            "question_class_section",
            "scope_separation",
            "release_tag_boundary",
            "forbidden_stale_markers",
        ),
    ),
)


def _render_summary_framing_stale_reasons(
    *,
    matching_markers: list[str],
    spec: ReleaseClosureSummaryFramingSpec,
) -> list[str]:
    if not matching_markers:
        return []
    if spec.stale_reason_mode == "required_aggregate":
        return [spec.stale_reason_token]
    if spec.stale_reason_mode == "forbidden_per_marker":
        return [f"{spec.stale_reason_token}:{marker}" for marker in matching_markers]
    raise RuntimeError(
        f"release_closure_summary_framing_unknown_stale_reason_mode:{spec.framing_family}:{spec.stale_reason_mode}"
    )


def collect_release_closure_summary_framing_stale_reasons(
    text: str,
    *,
    framing_specs: tuple[ReleaseClosureSummaryFramingSpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in framing_specs:
        if spec.stale_reason_mode == "required_aggregate":
            matching_markers = [marker for marker in spec.markers if marker not in text]
        elif spec.stale_reason_mode == "forbidden_per_marker":
            matching_markers = [marker for marker in spec.markers if marker in text]
        else:
            raise RuntimeError(
                f"release_closure_summary_framing_unknown_stale_reason_mode:{spec.framing_family}:{spec.stale_reason_mode}"
            )
        stale_reasons.extend(
            _render_summary_framing_stale_reasons(
                matching_markers=matching_markers,
                spec=spec,
            )
        )
    return stale_reasons


def collect_release_closure_summary_framing_bundle_stale_reasons(text: str) -> list[str]:
    stale_reasons: list[str] = []
    for bundle_spec in RELEASE_CLOSURE_SUMMARY_FRAMING_BUNDLE_SPECS:
        stale_reasons.extend(
            collect_release_closure_summary_framing_stale_reasons(
                text,
                framing_specs=bundle_spec.framing_specs,
            )
        )
    return stale_reasons


def _validate_release_closure_summary_framing_bundle_specs() -> None:
    expected_specs = set(
        _select_summary_framing_specs(
            "question_class_section",
            "scope_separation",
            "release_tag_boundary",
            "forbidden_stale_markers",
        )
    )
    covered_specs: set[ReleaseClosureSummaryFramingSpec] = set()
    for bundle_spec in RELEASE_CLOSURE_SUMMARY_FRAMING_BUNDLE_SPECS:
        if not bundle_spec.framing_specs:
            raise RuntimeError(
                f"release_closure_summary_framing_bundle_empty:{bundle_spec.bundle_key}"
            )
        for framing_spec in bundle_spec.framing_specs:
            if not framing_spec.markers:
                raise RuntimeError(
                    f"release_closure_summary_framing_empty_markers:{framing_spec.framing_family}"
                )
            if framing_spec in covered_specs:
                raise RuntimeError(
                    f"release_closure_summary_framing_duplicate_spec:{bundle_spec.bundle_key}:{framing_spec.framing_family}"
                )
            covered_specs.add(framing_spec)
    if covered_specs != expected_specs:
        missing = sorted(
            spec.framing_family for spec in expected_specs if spec not in covered_specs
        )
        raise RuntimeError(
            f"release_closure_summary_framing_bundle_incomplete:{','.join(missing)}"
        )


_validate_release_closure_summary_framing_bundle_specs()
