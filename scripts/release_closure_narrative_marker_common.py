#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES,
)


@dataclass(frozen=True)
class ReleaseClosureNarrativeMarkerSpec:
    stale_reason_suffix: str
    script_rel: str
    markers: tuple[str, ...]
    governance_probe_owned: bool = False


@dataclass(frozen=True)
class ReleaseClosureNarrativeMarkerBundleSpec:
    bundle_key: str
    marker_specs: tuple[ReleaseClosureNarrativeMarkerSpec, ...]


RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS: tuple[ReleaseClosureNarrativeMarkerSpec, ...] = (
    ReleaseClosureNarrativeMarkerSpec(
        stale_reason_suffix="active_report_pointer_locality",
        script_rel="scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
        markers=(
            "scripts/ci/run_active_execution_report_pointer_locality_probes_ci.sh",
            "active_execution_report pointer",
            "cross-pack absolute pointer drift",
            "pack-local candidate roots",
            "latest_identity_upgrade_report()",
            "selected_report_authority_class",
            "selection_mode",
            "active_execution_pointer_pack_local_report",
            "candidate_root_latest_pack_local_report",
        ),
        governance_probe_owned=True,
    ),
    ReleaseClosureNarrativeMarkerSpec(
        stale_reason_suffix="strict_live_active_pointer_locality",
        script_rel="scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh",
        markers=(
            "scripts/ci/run_strict_live_active_pointer_locality_probes_ci.sh",
            "strict-live current-run pointer",
            "resolve_active_execution_context()",
            "pointer_candidate_root_report",
            "pointer_report_name_rehomed_candidate_root",
            "external_pointer_report_rejected",
        ),
        governance_probe_owned=True,
    ),
    ReleaseClosureNarrativeMarkerSpec(
        stale_reason_suffix="strict_live_contract_resolution",
        script_rel="scripts/ci/run_strict_live_contract_resolution_probes_ci.sh",
        markers=(
            "scripts/ci/run_strict_live_contract_resolution_probes_ci.sh",
            "strict-live contract resolution",
            "strict_live_current_run_required_but_unproven",
            "sample-green fail-close",
            "pack-relative contract paths",
        ),
        governance_probe_owned=True,
    ),
    ReleaseClosureNarrativeMarkerSpec(
        stale_reason_suffix="weak_live_pointer_absorption",
        script_rel="scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh",
        markers=(
            "scripts/ci/run_identity_weak_live_linkage_pointer_locality_probes_ci.sh",
            "validate_identity_weak_live_linkage.py",
            "current_run_pointer_resolution_mode",
            "external_pointer_report_rejected",
        ),
        governance_probe_owned=False,
    ),
    ReleaseClosureNarrativeMarkerSpec(
        stale_reason_suffix="execution_report_selection_convergence",
        script_rel="scripts/ci/run_execution_report_selection_convergence_probes_ci.sh",
        markers=(
            "scripts/ci/run_execution_report_selection_convergence_probes_ci.sh",
            "execution_report_selection_common.py",
            "primary execution report selection",
            "derivative report artifacts",
            "validate_execution_report_freshness.py",
            "validate_identity_protocol_baseline_freshness.py",
            "validate_run_id_report_selection.py",
        ),
        governance_probe_owned=True,
    ),
)


def _select_narrative_marker_specs(
    *stale_reason_suffixes: str,
) -> tuple[ReleaseClosureNarrativeMarkerSpec, ...]:
    selected_specs: list[ReleaseClosureNarrativeMarkerSpec] = []
    suffix_pool = set(stale_reason_suffixes)
    for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS:
        if spec.stale_reason_suffix in suffix_pool:
            selected_specs.append(spec)
            suffix_pool.remove(spec.stale_reason_suffix)
    if suffix_pool:
        missing = ",".join(sorted(suffix_pool))
        raise RuntimeError(f"release_closure_narrative_marker_spec_unresolved:{missing}")
    return tuple(selected_specs)


RELEASE_CLOSURE_POINTER_LOCALITY_NARRATIVE_MARKER_BUNDLE_SPEC = (
    ReleaseClosureNarrativeMarkerBundleSpec(
        bundle_key="pointer_locality",
        marker_specs=_select_narrative_marker_specs(
            "active_report_pointer_locality",
            "strict_live_active_pointer_locality",
            "weak_live_pointer_absorption",
        ),
    )
)

RELEASE_CLOSURE_STRICT_LIVE_CONTRACT_RESOLUTION_NARRATIVE_MARKER_BUNDLE_SPEC = (
    ReleaseClosureNarrativeMarkerBundleSpec(
        bundle_key="strict_live_contract_resolution",
        marker_specs=_select_narrative_marker_specs("strict_live_contract_resolution"),
    )
)

RELEASE_CLOSURE_EXECUTION_REPORT_SELECTION_NARRATIVE_MARKER_BUNDLE_SPEC = (
    ReleaseClosureNarrativeMarkerBundleSpec(
        bundle_key="execution_report_selection_convergence",
        marker_specs=_select_narrative_marker_specs("execution_report_selection_convergence"),
    )
)

RELEASE_CLOSURE_SUMMARY_NARRATIVE_MARKER_BUNDLE_SPECS: tuple[
    ReleaseClosureNarrativeMarkerBundleSpec,
    ...,
] = (
    RELEASE_CLOSURE_POINTER_LOCALITY_NARRATIVE_MARKER_BUNDLE_SPEC,
    RELEASE_CLOSURE_STRICT_LIVE_CONTRACT_RESOLUTION_NARRATIVE_MARKER_BUNDLE_SPEC,
    RELEASE_CLOSURE_EXECUTION_REPORT_SELECTION_NARRATIVE_MARKER_BUNDLE_SPEC,
)

RELEASE_CLOSURE_BOUNDARY_NARRATIVE_MARKER_BUNDLE_SPECS = (
    RELEASE_CLOSURE_SUMMARY_NARRATIVE_MARKER_BUNDLE_SPECS
)


def collect_release_closure_narrative_marker_stale_reasons(
    text: str,
    *,
    label: str,
    marker_specs: tuple[ReleaseClosureNarrativeMarkerSpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in marker_specs:
        for marker in spec.markers:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_{spec.stale_reason_suffix}_marker:{marker}")
    return stale_reasons


def collect_release_closure_narrative_bundle_stale_reasons(
    text: str,
    *,
    label: str,
    bundle_specs: tuple[ReleaseClosureNarrativeMarkerBundleSpec, ...],
) -> list[str]:
    stale_reasons: list[str] = []
    for bundle_spec in bundle_specs:
        stale_reasons.extend(
            collect_release_closure_narrative_marker_stale_reasons(
                text,
                label=label,
                marker_specs=bundle_spec.marker_specs,
            )
        )
    return stale_reasons


def collect_release_closure_summary_narrative_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_narrative_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_NARRATIVE_MARKER_BUNDLE_SPECS,
    )


def collect_release_closure_boundary_narrative_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_narrative_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_BOUNDARY_NARRATIVE_MARKER_BUNDLE_SPECS,
    )


def collect_release_closure_narrative_stale_reasons(text: str, *, label: str) -> list[str]:
    return collect_release_closure_narrative_bundle_stale_reasons(
        text,
        label=label,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_NARRATIVE_MARKER_BUNDLE_SPECS,
    )


def _validate_release_closure_narrative_marker_specs() -> None:
    governance_probe_owner_lanes = set(RELEASE_READINESS_GOVERNANCE_PROBE_OWNER_LANES)
    for spec in RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS:
        if spec.script_rel not in spec.markers:
            raise RuntimeError(
                f"release_closure_narrative_spec_missing_script_literal:{spec.stale_reason_suffix}:{spec.script_rel}"
            )
        if spec.governance_probe_owned and spec.script_rel not in governance_probe_owner_lanes:
            raise RuntimeError(
                f"release_closure_narrative_spec_missing_governance_probe_owner:{spec.stale_reason_suffix}:{spec.script_rel}"
            )


def _validate_release_closure_narrative_bundle_specs() -> None:
    canonical_marker_spec_set = set(RELEASE_CLOSURE_NARRATIVE_MARKER_SPECS)
    for surface_name, bundle_specs in (
        ("summary", RELEASE_CLOSURE_SUMMARY_NARRATIVE_MARKER_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_NARRATIVE_MARKER_BUNDLE_SPECS),
    ):
        covered_marker_specs: set[ReleaseClosureNarrativeMarkerSpec] = set()
        for bundle_spec in bundle_specs:
            if not bundle_spec.marker_specs:
                raise RuntimeError(
                    f"release_closure_narrative_bundle_empty:{surface_name}:{bundle_spec.bundle_key}"
                )
            for marker_spec in bundle_spec.marker_specs:
                if marker_spec not in canonical_marker_spec_set:
                    raise RuntimeError(
                        f"release_closure_narrative_bundle_unknown_spec:{surface_name}:{bundle_spec.bundle_key}:{marker_spec.stale_reason_suffix}"
                    )
                if marker_spec in covered_marker_specs:
                    raise RuntimeError(
                        f"release_closure_narrative_bundle_duplicate_spec:{surface_name}:{bundle_spec.bundle_key}:{marker_spec.stale_reason_suffix}"
                    )
                covered_marker_specs.add(marker_spec)
        if covered_marker_specs != canonical_marker_spec_set:
            missing_suffixes = sorted(
                spec.stale_reason_suffix
                for spec in canonical_marker_spec_set
                if spec not in covered_marker_specs
            )
            raise RuntimeError(
                f"release_closure_narrative_bundle_incomplete:{surface_name}:{','.join(missing_suffixes)}"
            )


_validate_release_closure_narrative_marker_specs()
_validate_release_closure_narrative_bundle_specs()
