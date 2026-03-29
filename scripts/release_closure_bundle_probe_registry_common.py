#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from release_closure_doc_common import RELEASE_CLOSURE_DOC_REL_PATHS
from release_closure_doc_reference_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKER,
    RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKER,
    RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKER,
    RELEASE_CLOSURE_SUMMARY_CONTRACT_BINDING_REFERENCE_MARKER,
    RELEASE_CLOSURE_SUMMARY_PHILOSOPHY_REFERENCE_MARKER,
    RELEASE_CLOSURE_SUMMARY_WORKBOOK_REFERENCE_MARKER,
    collect_release_closure_boundary_doc_reference_bundle_stale_reasons,
    collect_release_closure_summary_doc_reference_bundle_stale_reasons,
)
from release_closure_foundational_marker_common import (
    RELEASE_CLOSURE_MACHINE_CLOSED_MARKER,
    RELEASE_CLOSURE_PHILOSOPHY_ADJUDICATION_ORDER_MARKER,
    RELEASE_CLOSURE_PHILOSOPHY_SOURCE_ORDER_MARKER,
    RELEASE_CLOSURE_ROOT_CLOSED_MARKER,
    RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_CREATOR_UPDATE_ADMISSION_MARKER,
    RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_REPAIR_SUCCESS_NOT_CLEAN_MARKER,
    collect_release_closure_boundary_foundational_bundle_stale_reasons,
    collect_release_closure_foundational_philosophy_bundle_stale_reasons,
    collect_release_closure_summary_foundational_bundle_stale_reasons,
)
from release_closure_required_doc_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS,
    RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS,
)
from release_closure_surface_registry_common import (
    release_closure_surface_spec_by_bundle_surface_id,
)


ExpectedReasonCollector = Callable[[Path], tuple[str, ...]]


@dataclass(frozen=True)
class ReleaseClosureBundleProbeMutationSpec:
    target_relpath: str
    needle: str
    replacement: str
    mode: str = "all"
    min_occurrences: int = 1
    require_absent_after: bool = True


@dataclass(frozen=True)
class ReleaseClosureBundleProbeProfile:
    probe_id: str
    validator_script_rel: str
    status_key: str
    shadow_copy_files: tuple[str, ...]
    mutations: tuple[ReleaseClosureBundleProbeMutationSpec, ...]
    expected_reason_collector: ExpectedReasonCollector


RELEASE_CLOSURE_SUMMARY_FULL_SHADOW_COPY_FILES = RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS
RELEASE_CLOSURE_BOUNDARY_FULL_SHADOW_COPY_FILES = RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS

_SUMMARY_SURFACE_SPEC = release_closure_surface_spec_by_bundle_surface_id("summary")
_BOUNDARY_SURFACE_SPEC = release_closure_surface_spec_by_bundle_surface_id("boundary")
if _SUMMARY_SURFACE_SPEC is None or _BOUNDARY_SURFACE_SPEC is None:
    raise RuntimeError("release_closure_bundle_probe_registry_missing_bundle_surface_specs")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _collect_summary_doc_reference_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    summary_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc).resolve())
    return tuple(
        collect_release_closure_summary_doc_reference_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )


def _collect_boundary_doc_reference_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    governance_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc).resolve())
    review_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.review_doc).resolve())
    expected_reasons: list[str] = []
    expected_reasons.extend(
        collect_release_closure_boundary_doc_reference_bundle_stale_reasons(
            governance_text,
            label="governance_doc",
        )
    )
    expected_reasons.extend(
        collect_release_closure_boundary_doc_reference_bundle_stale_reasons(
            review_text,
            label="review_doc",
        )
    )
    return tuple(expected_reasons)


def _collect_summary_foundational_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    philosophy_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc).resolve())
    summary_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc).resolve())
    expected_reasons: list[str] = []
    expected_reasons.extend(
        collect_release_closure_foundational_philosophy_bundle_stale_reasons(philosophy_text)
    )
    expected_reasons.extend(
        collect_release_closure_summary_foundational_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    return tuple(expected_reasons)


def _collect_boundary_foundational_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    philosophy_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc).resolve())
    governance_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc).resolve())
    review_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.review_doc).resolve())
    expected_reasons: list[str] = []
    expected_reasons.extend(
        collect_release_closure_foundational_philosophy_bundle_stale_reasons(philosophy_text)
    )
    expected_reasons.extend(
        collect_release_closure_boundary_foundational_bundle_stale_reasons(
            governance_text,
            label="governance_doc",
        )
    )
    expected_reasons.extend(
        collect_release_closure_boundary_foundational_bundle_stale_reasons(
            review_text,
            label="review_doc",
        )
    )
    return tuple(expected_reasons)


RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="summary_doc_reference",
    validator_script_rel=_SUMMARY_SURFACE_SPEC.validator_script_rel,
    status_key=_SUMMARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_SUMMARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_SUMMARY_PHILOSOPHY_REFERENCE_MARKER,
            replacement="identity/protocol/IDENTITY_PROTOCOL_DESIGN_OUTLINE.md",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_SUMMARY_CONTRACT_BINDING_REFERENCE_MARKER,
            replacement="identity/protocol/mappings/contract-binding.next.yaml",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_SUMMARY_WORKBOOK_REFERENCE_MARKER,
            replacement="docs/workbook/protocol-deep-audit-workbook-v1.6-draft.md",
        ),
    ),
    expected_reason_collector=_collect_summary_doc_reference_expected_reasons,
)

RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="boundary_doc_reference",
    validator_script_rel=_BOUNDARY_SURFACE_SPEC.validator_script_rel,
    status_key=_BOUNDARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_BOUNDARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKER,
            replacement="identity/protocol/IDENTITY_PROTOCOL_DESIGN_OUTLINE.md",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKER,
            replacement="identity/protocol/IDENTITY_PROTOCOL_CORE.md",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKER,
            replacement="identity/protocol/IDENTITY_RUNTIME_REPORT.md",
        ),
    ),
    expected_reason_collector=_collect_boundary_doc_reference_expected_reasons,
)

RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="summary_foundational",
    validator_script_rel=_SUMMARY_SURFACE_SPEC.validator_script_rel,
    status_key=_SUMMARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_SUMMARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc,
            needle=RELEASE_CLOSURE_PHILOSOPHY_SOURCE_ORDER_MARKER,
            replacement="source order",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_ROOT_CLOSED_MARKER,
            replacement="root closure",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_REPAIR_SUCCESS_NOT_CLEAN_MARKER,
            replacement="repair success means clean terminal truth",
        ),
    ),
    expected_reason_collector=_collect_summary_foundational_expected_reasons,
)

RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="boundary_foundational",
    validator_script_rel=_BOUNDARY_SURFACE_SPEC.validator_script_rel,
    status_key=_BOUNDARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_BOUNDARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc,
            needle=RELEASE_CLOSURE_PHILOSOPHY_ADJUDICATION_ORDER_MARKER,
            replacement="adjudication order",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_CLOSURE_MACHINE_CLOSED_MARKER,
            replacement="machine closure",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=RELEASE_CLOSURE_TERMINAL_TRUTH_SPLIT_CREATOR_UPDATE_ADMISSION_MARKER,
            replacement="update lane",
        ),
    ),
    expected_reason_collector=_collect_boundary_foundational_expected_reasons,
)

RELEASE_CLOSURE_BUNDLE_PROBE_PROFILES: tuple[ReleaseClosureBundleProbeProfile, ...] = (
    RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE,
)


def release_closure_bundle_probe_profiles() -> tuple[ReleaseClosureBundleProbeProfile, ...]:
    return RELEASE_CLOSURE_BUNDLE_PROBE_PROFILES


def release_closure_bundle_probe_profile(
    probe_id: str,
) -> ReleaseClosureBundleProbeProfile | None:
    return next(
        (profile for profile in RELEASE_CLOSURE_BUNDLE_PROBE_PROFILES if profile.probe_id == probe_id),
        None,
    )


def _validate_release_closure_bundle_probe_profiles() -> None:
    seen_probe_ids: set[str] = set()
    for profile in RELEASE_CLOSURE_BUNDLE_PROBE_PROFILES:
        if profile.probe_id in seen_probe_ids:
            raise RuntimeError(
                f"release_closure_bundle_probe_duplicate_profile:{profile.probe_id}"
            )
        seen_probe_ids.add(profile.probe_id)
        if not profile.shadow_copy_files:
            raise RuntimeError(
                f"release_closure_bundle_probe_empty_shadow_copy_files:{profile.probe_id}"
            )
        if len(set(profile.shadow_copy_files)) != len(profile.shadow_copy_files):
            raise RuntimeError(
                f"release_closure_bundle_probe_duplicate_shadow_copy_file:{profile.probe_id}"
            )
        seen_targets: set[tuple[str, str]] = set()
        for mutation in profile.mutations:
            key = (mutation.target_relpath, mutation.needle)
            if key in seen_targets:
                raise RuntimeError(
                    "release_closure_bundle_probe_duplicate_mutation_target:"
                    + f"{profile.probe_id}:{mutation.target_relpath}:{mutation.needle}"
                )
            seen_targets.add(key)


_validate_release_closure_bundle_probe_profiles()
