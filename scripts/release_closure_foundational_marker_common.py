#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class ReleaseClosureFoundationalMarkerSpec:
    marker_family: str
    markers: tuple[str, ...]
    stale_reason_mode: str
    stale_reason_token: str


@dataclass(frozen=True)
class ReleaseClosureFoundationalMarkerBundleSpec:
    bundle_key: str
    marker_specs: tuple[ReleaseClosureFoundationalMarkerSpec, ...]


RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS: tuple[str, ...] = (
    "source-order",
    "reading-order",
    "adjudication-order",
)
RELEASE_CLOSURE_PHILOSOPHY_SOURCE_ORDER_MARKER = (
    RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS[0]
)
RELEASE_CLOSURE_PHILOSOPHY_ADJUDICATION_ORDER_MARKER = (
    RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS[2]
)

RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS: tuple[str, ...] = (
    "root-closed",
    "machine-closed",
    "runtime-closed",
)
RELEASE_CLOSURE_ROOT_CLOSED_MARKER = RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS[0]
RELEASE_CLOSURE_MACHINE_CLOSED_MARKER = RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS[1]

RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS: tuple[str, ...] = (
    "repair lane",
    "terminal-truth observation lane",
    "creator/update admission lane",
    "repair success != clean terminal truth",
)
RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_CREATOR_UPDATE_ADMISSION_MARKER = (
    RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS[2]
)
RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_REPAIR_SUCCESS_NOT_CLEAN_MARKER = (
    RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS[3]
)

RELEASE_CLOSURE_FOUNDATIONAL_MARKER_SPECS: tuple[ReleaseClosureFoundationalMarkerSpec, ...] = (
    ReleaseClosureFoundationalMarkerSpec(
        marker_family="philosophy_order",
        markers=RELEASE_CLOSURE_PHILOSOPHY_ORDER_MARKERS,
        stale_reason_mode="global_aggregate",
        stale_reason_token="philosophy_root_order_markers_missing",
    ),
    ReleaseClosureFoundationalMarkerSpec(
        marker_family="closure_class",
        markers=RELEASE_CLOSURE_CLOSURE_CLASS_MARKERS,
        stale_reason_mode="labeled_aggregate",
        stale_reason_token="missing_root_machine_runtime_closure_markers",
    ),
    ReleaseClosureFoundationalMarkerSpec(
        marker_family="terminal_truth_split",
        markers=RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_MARKERS,
        stale_reason_mode="labeled_per_marker",
        stale_reason_token="missing_terminal_truth_split_marker",
    ),
)


def _select_foundational_marker_specs(
    *marker_families: str,
) -> tuple[ReleaseClosureFoundationalMarkerSpec, ...]:
    selected_specs: list[ReleaseClosureFoundationalMarkerSpec] = []
    family_pool = set(marker_families)
    for spec in RELEASE_CLOSURE_FOUNDATIONAL_MARKER_SPECS:
        if spec.marker_family in family_pool:
            selected_specs.append(spec)
            family_pool.remove(spec.marker_family)
    if family_pool:
        missing = ",".join(sorted(family_pool))
        raise RuntimeError(f"release_closure_foundational_marker_spec_unresolved:{missing}")
    return tuple(selected_specs)


RELEASE_CLOSURE_FOUNDATIONAL_PHILOSOPHY_BUNDLE_SPEC = ReleaseClosureFoundationalMarkerBundleSpec(
    bundle_key="philosophy_order",
    marker_specs=_select_foundational_marker_specs("philosophy_order"),
)

RELEASE_CLOSURE_FOUNDATIONAL_SURFACE_BUNDLE_SPEC = ReleaseClosureFoundationalMarkerBundleSpec(
    bundle_key="closure_surface_foundations",
    marker_specs=_select_foundational_marker_specs(
        "closure_class",
        "terminal_truth_split",
    ),
)

RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureFoundationalMarkerBundleSpec,
    ...,
] = (RELEASE_CLOSURE_FOUNDATIONAL_SURFACE_BUNDLE_SPEC,)

RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS = (
    RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS
)


def _render_foundational_stale_reasons(
    *,
    missing_markers: list[str],
    spec: ReleaseClosureFoundationalMarkerSpec,
    label: str | None,
) -> list[str]:
    if not missing_markers:
        return []
    if spec.stale_reason_mode == "global_aggregate":
        return [spec.stale_reason_token]
    if label is None:
        raise RuntimeError(
            f"release_closure_foundational_label_required:{spec.marker_family}:{spec.stale_reason_mode}"
        )
    if spec.stale_reason_mode == "labeled_aggregate":
        return [f"{label}_{spec.stale_reason_token}"]
    if spec.stale_reason_mode == "labeled_per_marker":
        return [
            f"{label}_{spec.stale_reason_token}:{marker}" for marker in missing_markers
        ]
    raise RuntimeError(
        f"release_closure_foundational_unknown_stale_reason_mode:{spec.marker_family}:{spec.stale_reason_mode}"
    )


def collect_release_closure_foundational_marker_stale_reasons(
    text: str,
    *,
    marker_specs: tuple[ReleaseClosureFoundationalMarkerSpec, ...],
    label: str | None = None,
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in marker_specs:
        missing_markers = [marker for marker in spec.markers if marker not in text]
        stale_reasons.extend(
            _render_foundational_stale_reasons(
                missing_markers=missing_markers,
                spec=spec,
                label=label,
            )
        )
    return stale_reasons


def collect_release_closure_foundational_bundle_stale_reasons(
    text: str,
    *,
    bundle_specs: tuple[ReleaseClosureFoundationalMarkerBundleSpec, ...],
    label: str | None = None,
) -> list[str]:
    stale_reasons: list[str] = []
    for bundle_spec in bundle_specs:
        stale_reasons.extend(
            collect_release_closure_foundational_marker_stale_reasons(
                text,
                marker_specs=bundle_spec.marker_specs,
                label=label,
            )
        )
    return stale_reasons


def collect_release_closure_foundational_philosophy_bundle_stale_reasons(
    text: str,
) -> list[str]:
    return collect_release_closure_foundational_bundle_stale_reasons(
        text,
        bundle_specs=(RELEASE_CLOSURE_FOUNDATIONAL_PHILOSOPHY_BUNDLE_SPEC,),
    )


def collect_release_closure_summary_foundational_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_foundational_bundle_stale_reasons(
        text,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS,
        label=label,
    )


def collect_release_closure_boundary_foundational_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_foundational_bundle_stale_reasons(
        text,
        bundle_specs=RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS,
        label=label,
    )


def collect_release_closure_philosophy_order_stale_reasons(text: str) -> list[str]:
    return collect_release_closure_foundational_philosophy_bundle_stale_reasons(text)


def collect_release_closure_closure_class_stale_reasons(text: str, *, label: str) -> list[str]:
    return collect_release_closure_foundational_marker_stale_reasons(
        text,
        marker_specs=_select_foundational_marker_specs("closure_class"),
        label=label,
    )


def collect_release_closure_terminal_truth_split_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_foundational_marker_stale_reasons(
        text,
        marker_specs=_select_foundational_marker_specs("terminal_truth_split"),
        label=label,
    )


def _validate_release_closure_foundational_bundle_specs() -> None:
    expected_spec_sets = {
        "philosophy": set(_select_foundational_marker_specs("philosophy_order")),
        "summary": set(_select_foundational_marker_specs("closure_class", "terminal_truth_split")),
        "boundary": set(_select_foundational_marker_specs("closure_class", "terminal_truth_split")),
    }
    for surface_name, bundle_specs in (
        ("philosophy", (RELEASE_CLOSURE_FOUNDATIONAL_PHILOSOPHY_BUNDLE_SPEC,)),
        ("summary", RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_MARKER_BUNDLE_SPECS),
    ):
        covered_specs: set[ReleaseClosureFoundationalMarkerSpec] = set()
        for bundle_spec in bundle_specs:
            if not bundle_spec.marker_specs:
                raise RuntimeError(
                    f"release_closure_foundational_bundle_empty:{surface_name}:{bundle_spec.bundle_key}"
                )
            for marker_spec in bundle_spec.marker_specs:
                if marker_spec in covered_specs:
                    raise RuntimeError(
                        f"release_closure_foundational_bundle_duplicate_spec:{surface_name}:{bundle_spec.bundle_key}:{marker_spec.marker_family}"
                    )
                covered_specs.add(marker_spec)
        if covered_specs != expected_spec_sets[surface_name]:
            missing_families = sorted(
                spec.marker_family
                for spec in expected_spec_sets[surface_name]
                if spec not in covered_specs
            )
            raise RuntimeError(
                f"release_closure_foundational_bundle_incomplete:{surface_name}:{','.join(missing_families)}"
            )


_validate_release_closure_foundational_bundle_specs()
