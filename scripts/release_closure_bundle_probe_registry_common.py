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
from release_closure_narrative_marker_common import (
    RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS,
    collect_release_closure_boundary_narrative_bundle_stale_reasons,
    collect_release_closure_summary_narrative_bundle_stale_reasons,
)
from release_closure_operational_marker_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
    RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
    collect_release_closure_operational_marker_bundle_stale_reasons,
)
from release_closure_required_doc_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_REQUIRED_DOC_RELPATHS,
    RELEASE_CLOSURE_SUMMARY_REQUIRED_DOC_RELPATHS,
)
from release_closure_continuation_marker_common import (
    RELEASE_CLOSURE_CONTINUATION_CALLER_CWD_MARKER,
    RELEASE_CLOSURE_CONTINUATION_STABLE_PREWRITE_SNAPSHOT_MARKER,
    RELEASE_CLOSURE_SUMMARY_CONTINUATION_FINALIZED_MARKER,
    RELEASE_CLOSURE_SUMMARY_CONTINUATION_RESUME_CAPTURE_MODE_MARKER,
)
from release_readiness_runtime_closure_convergence_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER,
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER,
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER,
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


def _release_closure_narrative_marker(stale_reason_suffix: str, marker_index: int) -> str:
    spec = next(
        (
            marker_spec
            for marker_spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS
            if marker_spec.stale_reason_suffix == stale_reason_suffix
        ),
        None,
    )
    if spec is None:
        raise RuntimeError(
            f"release_closure_bundle_probe_missing_narrative_marker_spec:{stale_reason_suffix}"
        )
    try:
        return spec.markers[marker_index]
    except IndexError as exc:
        raise RuntimeError(
            "release_closure_bundle_probe_missing_narrative_marker_index:"
            + f"{stale_reason_suffix}:{marker_index}"
        ) from exc


ACTIVE_REPORT_POINTER_SELECTOR_MARKER = _release_closure_narrative_marker(
    "active_report_pointer_locality",
    4,
)
STRICT_LIVE_ACTIVE_POINTER_CONTEXT_MARKER = _release_closure_narrative_marker(
    "strict_live_active_pointer_locality",
    2,
)
STRICT_LIVE_CONTRACT_RESOLUTION_MARKER = _release_closure_narrative_marker(
    "strict_live_contract_resolution",
    3,
)
WEAK_LIVE_POINTER_ABSORPTION_MARKER = _release_closure_narrative_marker(
    "weak_live_pointer_absorption",
    2,
)
EXECUTION_REPORT_SELECTION_MARKER = _release_closure_narrative_marker(
    "execution_report_selection_convergence",
    1,
)


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


def _collect_summary_narrative_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    summary_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc).resolve())
    return tuple(
        collect_release_closure_summary_narrative_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )


def _collect_boundary_narrative_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    governance_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc).resolve())
    review_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.review_doc).resolve())
    expected_reasons: list[str] = []
    expected_reasons.extend(
        collect_release_closure_boundary_narrative_bundle_stale_reasons(
            governance_text,
            label="governance_doc",
        )
    )
    expected_reasons.extend(
        collect_release_closure_boundary_narrative_bundle_stale_reasons(
            review_text,
            label="review_doc",
        )
    )
    return tuple(expected_reasons)


def _collect_summary_operational_marker_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    summary_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc).resolve())
    return tuple(
        collect_release_closure_operational_marker_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
            bundle_specs=RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
        )
    )


def _collect_boundary_operational_marker_expected_reasons(shadow_root: Path) -> tuple[str, ...]:
    governance_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc).resolve())
    review_text = _read_text((shadow_root / RELEASE_CLOSURE_DOC_REL_PATHS.review_doc).resolve())
    expected_reasons: list[str] = []
    expected_reasons.extend(
        collect_release_closure_operational_marker_bundle_stale_reasons(
            governance_text,
            label="governance_doc",
            bundle_specs=RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
        )
    )
    expected_reasons.extend(
        collect_release_closure_operational_marker_bundle_stale_reasons(
            review_text,
            label="review_doc",
            bundle_specs=RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
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

RELEASE_CLOSURE_SUMMARY_NARRATIVE_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="summary_narrative",
    validator_script_rel=_SUMMARY_SURFACE_SPEC.validator_script_rel,
    status_key=_SUMMARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_SUMMARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=ACTIVE_REPORT_POINTER_SELECTOR_MARKER,
            replacement="latest_execution_report()",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=STRICT_LIVE_ACTIVE_POINTER_CONTEXT_MARKER,
            replacement="resolve_current_execution_context()",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=STRICT_LIVE_CONTRACT_RESOLUTION_MARKER,
            replacement="sample green failclose",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=WEAK_LIVE_POINTER_ABSORPTION_MARKER,
            replacement="current_pointer_resolution_mode",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=EXECUTION_REPORT_SELECTION_MARKER,
            replacement="primary_execution_report_selector.py",
        ),
    ),
    expected_reason_collector=_collect_summary_narrative_expected_reasons,
)

RELEASE_CLOSURE_BOUNDARY_NARRATIVE_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="boundary_narrative",
    validator_script_rel=_BOUNDARY_SURFACE_SPEC.validator_script_rel,
    status_key=_BOUNDARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_BOUNDARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=ACTIVE_REPORT_POINTER_SELECTOR_MARKER,
            replacement="latest_execution_report()",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=STRICT_LIVE_CONTRACT_RESOLUTION_MARKER,
            replacement="sample green failclose",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=STRICT_LIVE_ACTIVE_POINTER_CONTEXT_MARKER,
            replacement="resolve_current_execution_context()",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=WEAK_LIVE_POINTER_ABSORPTION_MARKER,
            replacement="current_pointer_resolution_mode",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=EXECUTION_REPORT_SELECTION_MARKER,
            replacement="primary_execution_report_selector.py",
        ),
    ),
    expected_reason_collector=_collect_boundary_narrative_expected_reasons,
)

RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="summary_operational_marker",
    validator_script_rel=_SUMMARY_SURFACE_SPEC.validator_script_rel,
    status_key=_SUMMARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_SUMMARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_SUMMARY_CONTINUATION_FINALIZED_MARKER,
            replacement="summary_lifecycle_status=DONE",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_CLOSURE_SUMMARY_CONTINUATION_RESUME_CAPTURE_MODE_MARKER,
            replacement="resume_capture_mode=resume_snapshot",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER,
            replacement="scripts/ci/run_transport_fleet_convergence_probes_ci.sh",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER,
            replacement="scripts/ci/run_runtime_pack_convergence_probes_ci.sh",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc,
            needle=RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER,
            replacement="scripts/run_workspace_runtime_pack_checks.py",
        ),
    ),
    expected_reason_collector=_collect_summary_operational_marker_expected_reasons,
)

RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_PROBE_PROFILE = ReleaseClosureBundleProbeProfile(
    probe_id="boundary_operational_marker",
    validator_script_rel=_BOUNDARY_SURFACE_SPEC.validator_script_rel,
    status_key=_BOUNDARY_SURFACE_SPEC.status_key,
    shadow_copy_files=RELEASE_CLOSURE_BOUNDARY_FULL_SHADOW_COPY_FILES,
    mutations=(
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_CLOSURE_CONTINUATION_STABLE_PREWRITE_SNAPSHOT_MARKER,
            replacement="stable resume snapshot",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_CLOSURE_CONTINUATION_CALLER_CWD_MARKER,
            replacement="caller working directory",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_PROBE_MARKER,
            replacement="scripts/ci/run_transport_fleet_convergence_probes_ci.sh",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
            needle=RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_RUNNER_MARKER,
            replacement="scripts/run_workspace_runtime_pack_checks.py",
        ),
        ReleaseClosureBundleProbeMutationSpec(
            target_relpath=RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
            needle=RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_PROBE_MARKER,
            replacement="scripts/ci/run_runtime_pack_convergence_probes_ci.sh",
        ),
    ),
    expected_reason_collector=_collect_boundary_operational_marker_expected_reasons,
)

RELEASE_CLOSURE_BUNDLE_PROBE_PROFILES: tuple[ReleaseClosureBundleProbeProfile, ...] = (
    RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_SUMMARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_FOUNDATIONAL_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_SUMMARY_NARRATIVE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_NARRATIVE_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_PROBE_PROFILE,
    RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_PROBE_PROFILE,
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
