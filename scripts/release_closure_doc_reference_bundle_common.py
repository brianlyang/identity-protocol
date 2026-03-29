#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from release_closure_doc_common import RELEASE_CLOSURE_DOC_REL_PATHS


@dataclass(frozen=True)
class ReleaseClosureDocReferenceSpec:
    reference_family: str
    markers: tuple[str, ...]
    stale_reason_mode: str
    stale_reason_token: str


@dataclass(frozen=True)
class ReleaseClosureDocReferenceBundleSpec:
    bundle_key: str
    reference_specs: tuple[ReleaseClosureDocReferenceSpec, ...]

RELEASE_CLOSURE_SUMMARY_PHILOSOPHY_REFERENCE_MARKER = RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc
RELEASE_CLOSURE_SUMMARY_CONTRACT_BINDING_REFERENCE_MARKER = (
    "identity/protocol/mappings/contract-binding.current.yaml"
)
RELEASE_CLOSURE_SUMMARY_WORKBOOK_REFERENCE_MARKER = RELEASE_CLOSURE_DOC_REL_PATHS.workbook_doc

RELEASE_CLOSURE_SUMMARY_REQUIRED_REFERENCE_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_SUMMARY_PHILOSOPHY_REFERENCE_MARKER,
    RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
    RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
    "identity/protocol/mappings/workbook-registry.current.yaml",
    "identity/protocol/mappings/stream-doc-registry.current.yaml",
    RELEASE_CLOSURE_SUMMARY_CONTRACT_BINDING_REFERENCE_MARKER,
    "identity/protocol/mappings/control-plane-status.current.yaml",
    "identity/protocol/mappings/control-plane-budget.current.yaml",
    RELEASE_CLOSURE_DOC_REL_PATHS.issue_register_doc,
    RELEASE_CLOSURE_SUMMARY_WORKBOOK_REFERENCE_MARKER,
)

RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKER = (
    RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc
)
RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKER,
)
RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKER = RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc
RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKER,
)
RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKER = (
    RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc
)
RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKERS: tuple[str, ...] = (
    RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKER,
)

RELEASE_CLOSURE_DOC_REFERENCE_SPECS: tuple[ReleaseClosureDocReferenceSpec, ...] = (
    ReleaseClosureDocReferenceSpec(
        reference_family="summary_required_refs",
        markers=RELEASE_CLOSURE_SUMMARY_REQUIRED_REFERENCE_MARKERS,
        stale_reason_mode="labeled_per_marker",
        stale_reason_token="missing_required_ref",
    ),
    ReleaseClosureDocReferenceSpec(
        reference_family="boundary_philosophy_anchor",
        markers=RELEASE_CLOSURE_BOUNDARY_PHILOSOPHY_ANCHOR_MARKERS,
        stale_reason_mode="labeled_aggregate",
        stale_reason_token="missing_philosophy_anchor",
    ),
    ReleaseClosureDocReferenceSpec(
        reference_family="boundary_protocol_anchor",
        markers=RELEASE_CLOSURE_BOUNDARY_PROTOCOL_ANCHOR_MARKERS,
        stale_reason_mode="labeled_aggregate",
        stale_reason_token="missing_protocol_anchor",
    ),
    ReleaseClosureDocReferenceSpec(
        reference_family="boundary_runtime_anchor",
        markers=RELEASE_CLOSURE_BOUNDARY_RUNTIME_ANCHOR_MARKERS,
        stale_reason_mode="labeled_aggregate",
        stale_reason_token="missing_runtime_anchor",
    ),
)


def _select_doc_reference_specs(
    *reference_families: str,
) -> tuple[ReleaseClosureDocReferenceSpec, ...]:
    selected_specs: list[ReleaseClosureDocReferenceSpec] = []
    family_pool = set(reference_families)
    for spec in RELEASE_CLOSURE_DOC_REFERENCE_SPECS:
        if spec.reference_family in family_pool:
            selected_specs.append(spec)
            family_pool.remove(spec.reference_family)
    if family_pool:
        missing = ",".join(sorted(family_pool))
        raise RuntimeError(f"release_closure_doc_reference_spec_unresolved:{missing}")
    return tuple(selected_specs)


RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_SPEC = ReleaseClosureDocReferenceBundleSpec(
    bundle_key="summary_required_refs",
    reference_specs=_select_doc_reference_specs("summary_required_refs"),
)

RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_SPEC = ReleaseClosureDocReferenceBundleSpec(
    bundle_key="boundary_authority_anchors",
    reference_specs=_select_doc_reference_specs(
        "boundary_philosophy_anchor",
        "boundary_protocol_anchor",
        "boundary_runtime_anchor",
    ),
)

RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_SPECS: tuple[
    ReleaseClosureDocReferenceBundleSpec,
    ...,
] = (RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_SPEC,)

RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_SPECS: tuple[
    ReleaseClosureDocReferenceBundleSpec,
    ...,
] = (RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_SPEC,)


def _render_doc_reference_stale_reasons(
    *,
    missing_markers: list[str],
    spec: ReleaseClosureDocReferenceSpec,
    label: str,
) -> list[str]:
    if not missing_markers:
        return []
    if spec.stale_reason_mode == "labeled_per_marker":
        return [
            f"{label}_{spec.stale_reason_token}:{marker}" for marker in missing_markers
        ]
    if spec.stale_reason_mode == "labeled_aggregate":
        return [f"{label}_{spec.stale_reason_token}"]
    raise RuntimeError(
        f"release_closure_doc_reference_unknown_stale_reason_mode:{spec.reference_family}:{spec.stale_reason_mode}"
    )


def collect_release_closure_doc_reference_stale_reasons(
    text: str,
    *,
    reference_specs: tuple[ReleaseClosureDocReferenceSpec, ...],
    label: str,
) -> list[str]:
    stale_reasons: list[str] = []
    for spec in reference_specs:
        missing_markers = [marker for marker in spec.markers if marker not in text]
        stale_reasons.extend(
            _render_doc_reference_stale_reasons(
                missing_markers=missing_markers,
                spec=spec,
                label=label,
            )
        )
    return stale_reasons


def collect_release_closure_doc_reference_bundle_stale_reasons(
    text: str,
    *,
    bundle_specs: tuple[ReleaseClosureDocReferenceBundleSpec, ...],
    label: str,
) -> list[str]:
    stale_reasons: list[str] = []
    for bundle_spec in bundle_specs:
        stale_reasons.extend(
            collect_release_closure_doc_reference_stale_reasons(
                text,
                reference_specs=bundle_spec.reference_specs,
                label=label,
            )
        )
    return stale_reasons


def collect_release_closure_summary_doc_reference_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_doc_reference_bundle_stale_reasons(
        text,
        bundle_specs=RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_SPECS,
        label=label,
    )


def collect_release_closure_boundary_doc_reference_bundle_stale_reasons(
    text: str,
    *,
    label: str,
) -> list[str]:
    return collect_release_closure_doc_reference_bundle_stale_reasons(
        text,
        bundle_specs=RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_SPECS,
        label=label,
    )


def _validate_release_closure_doc_reference_bundle_specs() -> None:
    expected_spec_sets = {
        "summary": set(_select_doc_reference_specs("summary_required_refs")),
        "boundary": set(
            _select_doc_reference_specs(
                "boundary_philosophy_anchor",
                "boundary_protocol_anchor",
                "boundary_runtime_anchor",
            )
        ),
    }
    for surface_name, bundle_specs in (
        ("summary", RELEASE_CLOSURE_SUMMARY_DOC_REFERENCE_BUNDLE_SPECS),
        ("boundary", RELEASE_CLOSURE_BOUNDARY_DOC_REFERENCE_BUNDLE_SPECS),
    ):
        covered_specs: set[ReleaseClosureDocReferenceSpec] = set()
        for bundle_spec in bundle_specs:
            if not bundle_spec.reference_specs:
                raise RuntimeError(
                    f"release_closure_doc_reference_bundle_empty:{surface_name}:{bundle_spec.bundle_key}"
                )
            for reference_spec in bundle_spec.reference_specs:
                if not reference_spec.markers:
                    raise RuntimeError(
                        f"release_closure_doc_reference_empty_markers:{surface_name}:{reference_spec.reference_family}"
                    )
                if reference_spec in covered_specs:
                    raise RuntimeError(
                        f"release_closure_doc_reference_bundle_duplicate_spec:{surface_name}:{bundle_spec.bundle_key}:{reference_spec.reference_family}"
                    )
                covered_specs.add(reference_spec)
        if covered_specs != expected_spec_sets[surface_name]:
            missing = sorted(
                spec.reference_family
                for spec in expected_spec_sets[surface_name]
                if spec not in covered_specs
            )
            raise RuntimeError(
                f"release_closure_doc_reference_bundle_incomplete:{surface_name}:{','.join(missing)}"
            )


_validate_release_closure_doc_reference_bundle_specs()
