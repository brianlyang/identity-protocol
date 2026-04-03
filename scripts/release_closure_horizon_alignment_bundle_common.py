#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from release_closure_doc_common import (
    collect_release_closure_issue_horizon_targets,
    contains_release_closure_issue_horizon,
)


@dataclass(frozen=True)
class ReleaseClosureHorizonAlignmentSpec:
    alignment_family: str
    check_kind: str
    stale_reason_mode: str
    stale_reason_token: str


@dataclass(frozen=True)
class ReleaseClosureHorizonAlignmentBundleSpec:
    bundle_key: str
    alignment_specs: tuple[ReleaseClosureHorizonAlignmentSpec, ...]


RELEASE_CLOSURE_HORIZON_ALIGNMENT_SPECS: tuple[ReleaseClosureHorizonAlignmentSpec, ...] = (
    ReleaseClosureHorizonAlignmentSpec(
        alignment_family="current_issue_horizon",
        check_kind="required_current_issue_horizon",
        stale_reason_mode="labeled_singleton",
        stale_reason_token="issue_horizon_mismatch",
    ),
    ReleaseClosureHorizonAlignmentSpec(
        alignment_family="stale_issue_horizon_targets",
        check_kind="stale_issue_horizon_targets",
        stale_reason_mode="labeled_per_target",
        stale_reason_token="stale_issue_horizon",
    ),
    ReleaseClosureHorizonAlignmentSpec(
        alignment_family="highest_closed_v16_stream_version",
        check_kind="required_highest_closed_v16_stream_version",
        stale_reason_mode="labeled_singleton",
        stale_reason_token="missing_highest_v16_stream_version",
    ),
    ReleaseClosureHorizonAlignmentSpec(
        alignment_family="boundary_stream_versions",
        check_kind="required_boundary_stream_versions",
        stale_reason_mode="labeled_per_target",
        stale_reason_token="missing_boundary_stream_version",
    ),
)


def _select_horizon_alignment_specs(
    *alignment_families: str,
) -> tuple[ReleaseClosureHorizonAlignmentSpec, ...]:
    selected_specs: list[ReleaseClosureHorizonAlignmentSpec] = []
    family_pool = set(alignment_families)
    for spec in RELEASE_CLOSURE_HORIZON_ALIGNMENT_SPECS:
        if spec.alignment_family in family_pool:
            selected_specs.append(spec)
            family_pool.remove(spec.alignment_family)
    if family_pool:
        missing = ",".join(sorted(family_pool))
        raise RuntimeError(f"release_closure_horizon_alignment_spec_unresolved:{missing}")
    return tuple(selected_specs)


RELEASE_CLOSURE_SUMMARY_HORIZON_ALIGNMENT_BUNDLE_SPEC = (
    ReleaseClosureHorizonAlignmentBundleSpec(
        bundle_key="summary_horizon_and_boundary_versions",
        alignment_specs=_select_horizon_alignment_specs(
            "current_issue_horizon",
            "stale_issue_horizon_targets",
            "highest_closed_v16_stream_version",
            "boundary_stream_versions",
        ),
    )
)

RELEASE_CLOSURE_BOUNDARY_HORIZON_ALIGNMENT_BUNDLE_SPEC = (
    ReleaseClosureHorizonAlignmentBundleSpec(
        bundle_key="boundary_horizon_and_stream_version",
        alignment_specs=_select_horizon_alignment_specs(
            "current_issue_horizon",
            "stale_issue_horizon_targets",
            "highest_closed_v16_stream_version",
        ),
    )
)

RELEASE_CLOSURE_SUMMARY_HORIZON_ALIGNMENT_BUNDLE_SPECS: tuple[
    ReleaseClosureHorizonAlignmentBundleSpec,
    ...,
] = (RELEASE_CLOSURE_SUMMARY_HORIZON_ALIGNMENT_BUNDLE_SPEC,)

RELEASE_CLOSURE_BOUNDARY_HORIZON_ALIGNMENT_BUNDLE_SPECS: tuple[
    ReleaseClosureHorizonAlignmentBundleSpec,
    ...,
] = (RELEASE_CLOSURE_BOUNDARY_HORIZON_ALIGNMENT_BUNDLE_SPEC,)


def _render_horizon_alignment_stale_reasons(
    *,
    targets: list[str],
    spec: ReleaseClosureHorizonAlignmentSpec,
    label: str,
) -> list[str]:
    if not targets:
        return []
    if spec.stale_reason_mode == "labeled_singleton":
        return [f"{label}_{spec.stale_reason_token}"]
    if spec.stale_reason_mode == "labeled_per_target":
        return [f"{label}_{spec.stale_reason_token}:{target}" for target in targets]
    raise RuntimeError(
        f"release_closure_horizon_alignment_unknown_stale_reason_mode:{spec.alignment_family}:{spec.stale_reason_mode}"
    )


def _resolve_horizon_alignment_targets(
    text: str,
    *,
    spec: ReleaseClosureHorizonAlignmentSpec,
    current_issue: str,
    highest_version: str,
    boundary_versions: tuple[str, ...],
) -> list[str]:
    if spec.check_kind == "required_current_issue_horizon":
        return [] if contains_release_closure_issue_horizon(text, current_issue) else [current_issue]
    if spec.check_kind == "stale_issue_horizon_targets":
        return [
            target_issue
            for target_issue in collect_release_closure_issue_horizon_targets(text)
            if target_issue != current_issue
        ]
    if spec.check_kind == "required_highest_closed_v16_stream_version":
        if not highest_version or highest_version in text:
            return []
        return [highest_version]
    if spec.check_kind == "required_boundary_stream_versions":
        return [version for version in boundary_versions if version not in text]
    raise RuntimeError(
        f"release_closure_horizon_alignment_unknown_check_kind:{spec.alignment_family}:{spec.check_kind}"
    )


def collect_release_closure_horizon_alignment_stale_reasons(
    text: str,
    *,
    label: str,
    alignment_specs: tuple[ReleaseClosureHorizonAlignmentSpec, ...],
    current_issue: str,
    highest_version: str,
    boundary_versions: tuple[str, ...] = (),
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in alignment_specs:
        targets = _resolve_horizon_alignment_targets(
            text,
            spec=spec,
            current_issue=current_issue,
            highest_version=highest_version,
            boundary_versions=boundary_versions,
        )
        stale_reasons.extend(
            _render_horizon_alignment_stale_reasons(
                targets=targets,
                spec=spec,
                label=label,
            )
        )
    return stale_reasons


def collect_release_closure_horizon_alignment_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    bundle_specs: tuple[ReleaseClosureHorizonAlignmentBundleSpec, ...],
    current_issue: str,
    highest_version: str,
    boundary_versions: tuple[str, ...] = (),
) -> list[str]:
    stale_reasons: list[str] = []
    for bundle_spec in bundle_specs:
        stale_reasons.extend(
            collect_release_closure_horizon_alignment_stale_reasons(
                text,
                label=label,
                alignment_specs=bundle_spec.alignment_specs,
                current_issue=current_issue,
                highest_version=highest_version,
                boundary_versions=boundary_versions,
            )
        )
    return stale_reasons


def collect_release_closure_summary_horizon_alignment_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    current_issue: str,
    highest_version: str,
    boundary_versions: tuple[str, ...],
) -> list[str]:
    return collect_release_closure_horizon_alignment_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_HORIZON_ALIGNMENT_BUNDLE_SPECS,
        current_issue=current_issue,
        highest_version=highest_version,
        boundary_versions=boundary_versions,
    )


def collect_release_closure_boundary_horizon_alignment_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    current_issue: str,
    highest_version: str,
) -> list[str]:
    return collect_release_closure_horizon_alignment_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_BOUNDARY_HORIZON_ALIGNMENT_BUNDLE_SPECS,
        current_issue=current_issue,
        highest_version=highest_version,
    )


def _validate_release_closure_horizon_alignment_bundle_specs() -> None:
    expected_spec_sets = {
        "summary": set(
            _select_horizon_alignment_specs(
                "current_issue_horizon",
                "stale_issue_horizon_targets",
                "highest_closed_v16_stream_version",
                "boundary_stream_versions",
            )
        ),
        "boundary": set(
            _select_horizon_alignment_specs(
                "current_issue_horizon",
                "stale_issue_horizon_targets",
                "highest_closed_v16_stream_version",
            )
        ),
    }
    for surface_name, bundle_specs in (
        ("summary", RELEASE_CLOSURE_SUMMARY_HORIZON_ALIGNMENT_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_HORIZON_ALIGNMENT_BUNDLE_SPECS),
    ):
        covered_specs: set[ReleaseClosureHorizonAlignmentSpec] = set()
        for bundle_spec in bundle_specs:
            if not bundle_spec.alignment_specs:
                raise RuntimeError(
                    f"release_closure_horizon_alignment_bundle_empty:{surface_name}:{bundle_spec.bundle_key}"
                )
            for alignment_spec in bundle_spec.alignment_specs:
                if alignment_spec in covered_specs:
                    raise RuntimeError(
                        f"release_closure_horizon_alignment_bundle_duplicate_spec:{surface_name}:{bundle_spec.bundle_key}:{alignment_spec.alignment_family}"
                    )
                covered_specs.add(alignment_spec)
        if covered_specs != expected_spec_sets[surface_name]:
            missing = sorted(
                spec.alignment_family
                for spec in expected_spec_sets[surface_name]
                if spec not in covered_specs
            )
            raise RuntimeError(
                f"release_closure_horizon_alignment_bundle_incomplete:{surface_name}:{','.join(missing)}"
            )


_validate_release_closure_horizon_alignment_bundle_specs()
