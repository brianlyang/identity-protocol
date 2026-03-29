#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from release_closure_bounded_projection_literal_bundle_common import (
    RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS,
)
from release_closure_surface_literal_canonicality_common import (
    ReleaseClosureSurfaceLiteralCanonicalitySpec,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
SUMMARY_PROFILE_ID = "summary"
BOUNDARY_PROFILE_ID = "boundary"


@dataclass(frozen=True)
class ReleaseClosureBoundedProjectionLiteralProbeMutationSpec:
    spec: ReleaseClosureSurfaceLiteralCanonicalitySpec
    replacement: str
    mode: str = "all"


@dataclass(frozen=True)
class ReleaseClosureBoundedProjectionLiteralProbeDocGroup:
    label: str
    doc_key: str
    mutation_specs: tuple[ReleaseClosureBoundedProjectionLiteralProbeMutationSpec, ...]


@dataclass(frozen=True)
class ReleaseClosureBoundedProjectionLiteralProbeProfile:
    profile_id: str
    status_field: str
    doc_groups: tuple[ReleaseClosureBoundedProjectionLiteralProbeDocGroup, ...]


_DRIFT_REPLACEMENTS_BY_LITERAL_KEY: dict[str, str] = {
    "projection_profile_exclusion_scope": (
        "projection_profile_exclusion_scope=projection_skip_status=SKIPPED_NOT_REQUIRED"
    ),
    "release_cloud_evidence_projection": (
        "release_cloud_evidence_projection=one_look.release_plane_cloud_evidence_status"
    ),
    "targeted_subset_required_gate_bundle_scope": (
        "targeted_subset_required_gate_bundle_scope=required_gate_bundle_status=SKIPPED_NOT_REQUIRED"
    ),
    "targeted_subset_required_gate_bundle_scope_reason": (
        "targeted_subset_required_gate_bundle_scope_reason="
        "required_gate_bundle_scope_reason=scope_reason_drifted"
    ),
    "targeted_subset_selected_check_scope": (
        "targeted_subset_selected_check_scope=selected_check_scope_projection_status=PASS_REQUIRED"
    ),
    "release_readiness_selected_check_scope_projection": (
        "release_readiness_selected_check_scope_projection="
        "one_look.selected_check_scope_projection_status"
    ),
    "release_readiness_one_look_family_order": (
        "release_readiness_one_look_family_order=foundational|governance_probe"
    ),
    "release_readiness_foundational_projection": (
        "release_readiness_foundational_projection=one_look.required_contract_coverage_status"
    ),
    "release_readiness_support_preflight_projection": (
        "release_readiness_support_preflight_projection=one_look.control_plane_budget_status"
    ),
    "release_readiness_terminal_truth_boundary_projection": (
        "release_readiness_terminal_truth_boundary_projection="
        "one_look.terminal_truth_boundary_projection_status"
    ),
    "required_gate_bundle_projection": (
        "required_gate_bundle_projection=one_look.required_gate_bundle_status"
    ),
    "full_scan_required_gate_bundle_projection": (
        "full_scan_required_gate_bundle_projection=three_plane.required_gate_bundle_status"
    ),
    "full_scan_required_gate_bundle_summary": (
        "full_scan_required_gate_bundle_summary="
        "summary_required_gate_bundle_projection.identities_with_projection"
    ),
}

_SPECS_BY_LITERAL_KEY: dict[str, ReleaseClosureSurfaceLiteralCanonicalitySpec] = {
    spec.literal_key: spec
    for spec in RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS
}

_BOUNDARY_GOVERNANCE_LITERAL_KEYS: tuple[str, ...] = (
    "projection_profile_exclusion_scope",
    "release_cloud_evidence_projection",
    "targeted_subset_required_gate_bundle_scope",
    "targeted_subset_required_gate_bundle_scope_reason",
    "targeted_subset_selected_check_scope",
    "release_readiness_selected_check_scope_projection",
)
_BOUNDARY_REVIEW_LITERAL_KEYS: tuple[str, ...] = tuple(
    spec.literal_key
    for spec in RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS
    if spec.literal_key not in _BOUNDARY_GOVERNANCE_LITERAL_KEYS
)


def _mutation_specs_for(
    literal_keys: tuple[str, ...],
) -> tuple[ReleaseClosureBoundedProjectionLiteralProbeMutationSpec, ...]:
    return tuple(
        ReleaseClosureBoundedProjectionLiteralProbeMutationSpec(
            spec=_SPECS_BY_LITERAL_KEY[literal_key],
            replacement=_DRIFT_REPLACEMENTS_BY_LITERAL_KEY[literal_key],
        )
        for literal_key in literal_keys
    )


RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES: dict[
    str, ReleaseClosureBoundedProjectionLiteralProbeProfile
] = {
    SUMMARY_PROFILE_ID: ReleaseClosureBoundedProjectionLiteralProbeProfile(
        profile_id=SUMMARY_PROFILE_ID,
        status_field="v16x_release_closure_summary_status",
        doc_groups=(
            ReleaseClosureBoundedProjectionLiteralProbeDocGroup(
                label="summary_doc",
                doc_key="summary_doc",
                mutation_specs=_mutation_specs_for(
                    tuple(
                        spec.literal_key
                        for spec in RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_CANONICALITY_SPECS
                    )
                ),
            ),
        ),
    ),
    BOUNDARY_PROFILE_ID: ReleaseClosureBoundedProjectionLiteralProbeProfile(
        profile_id=BOUNDARY_PROFILE_ID,
        status_field="v16x_release_closure_boundary_status",
        doc_groups=(
            ReleaseClosureBoundedProjectionLiteralProbeDocGroup(
                label="governance_doc",
                doc_key="governance_doc",
                mutation_specs=_mutation_specs_for(_BOUNDARY_GOVERNANCE_LITERAL_KEYS),
            ),
            ReleaseClosureBoundedProjectionLiteralProbeDocGroup(
                label="review_doc",
                doc_key="review_doc",
                mutation_specs=_mutation_specs_for(_BOUNDARY_REVIEW_LITERAL_KEYS),
            ),
        ),
    ),
}


def _mutate_text(*, text: str, needle: str, replacement: str, mode: str) -> tuple[str, int]:
    occurrence_count = text.count(needle)
    if occurrence_count < 1:
        raise SystemExit(
            "probe setup failed: expected at least 1 occurrence for literal "
            f"{needle!r}; found 0"
        )
    if mode == "first":
        replaced = min(occurrence_count, 1)
        mutated = text.replace(needle, replacement, 1)
    elif mode == "all":
        replaced = occurrence_count
        mutated = text.replace(needle, replacement)
    else:
        raise SystemExit(f"unsupported mutation mode: {mode}")
    if needle in mutated:
        residual = mutated.count(needle)
        raise SystemExit(
            "probe setup failed: literal residual remained after mutation; "
            f"needle={needle!r} remaining_occurrences={residual}"
        )
    return mutated, replaced


def apply_release_closure_bounded_projection_literal_probe_mutations(
    *,
    profile_id: str,
    doc_paths: dict[str, str],
) -> None:
    profile = RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES[profile_id]
    for group in profile.doc_groups:
        target_path = Path(doc_paths[group.doc_key]).expanduser().resolve()
        text = target_path.read_text(encoding="utf-8")
        for mutation_spec in group.mutation_specs:
            text, _ = _mutate_text(
                text=text,
                needle=mutation_spec.spec.canonical_marker,
                replacement=mutation_spec.replacement,
                mode=mutation_spec.mode,
            )
        target_path.write_text(text, encoding="utf-8")
        print(
            f"[PASS] bounded projection literal probe mutations applied: "
            f"profile={profile_id} label={group.label} path={target_path}"
        )


def expected_release_closure_bounded_projection_literal_probe_reasons(
    profile_id: str,
) -> tuple[str, ...]:
    profile = RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES[profile_id]
    return tuple(
        f"{group.label}_{mutation_spec.spec.stale_reason_suffix}"
        for group in profile.doc_groups
        for mutation_spec in group.mutation_specs
    )


def assert_release_closure_bounded_projection_literal_probe_results(
    *,
    profile_id: str,
    positive_json_path: str,
    negative_json_path: str,
) -> None:
    profile = RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES[profile_id]
    positive = json.loads(Path(positive_json_path).read_text(encoding="utf-8"))
    negative = json.loads(Path(negative_json_path).read_text(encoding="utf-8"))

    if positive.get(profile.status_field) != STATUS_PASS_REQUIRED:
        raise SystemExit(
            f"positive release-closure {profile_id} literal-bundle status must PASS_REQUIRED"
        )
    if negative.get(profile.status_field) != STATUS_FAIL_REQUIRED:
        raise SystemExit(
            f"negative release-closure {profile_id} literal-bundle status must FAIL_REQUIRED"
        )

    reasons = set(negative.get("stale_reasons") or [])
    expected_reasons = set(
        expected_release_closure_bounded_projection_literal_probe_reasons(profile_id)
    )
    missing = sorted(expected_reasons - reasons)
    if missing:
        raise SystemExit(
            f"negative release-closure {profile_id} literal-bundle probe is missing expected stale reasons: "
            + ", ".join(missing)
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Shared mutation/assertion helper for bounded projection literal-bundle probes."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mutate_parser = subparsers.add_parser("mutate", help="apply bounded literal drift mutations")
    mutate_parser.add_argument("--profile", choices=tuple(RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES), required=True)
    mutate_parser.add_argument("--summary-doc")
    mutate_parser.add_argument("--governance-doc")
    mutate_parser.add_argument("--review-doc")

    assert_parser = subparsers.add_parser("assert", help="assert positive/negative results")
    assert_parser.add_argument("--profile", choices=tuple(RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES), required=True)
    assert_parser.add_argument("--positive-json", required=True)
    assert_parser.add_argument("--negative-json", required=True)

    args = parser.parse_args()
    if args.command == "mutate":
        doc_paths: dict[str, str] = {}
        if args.summary_doc:
            doc_paths["summary_doc"] = str(args.summary_doc)
        if args.governance_doc:
            doc_paths["governance_doc"] = str(args.governance_doc)
        if args.review_doc:
            doc_paths["review_doc"] = str(args.review_doc)
        profile = RELEASE_CLOSURE_BOUNDED_PROJECTION_LITERAL_PROBE_PROFILES[str(args.profile)]
        missing_keys = [group.doc_key for group in profile.doc_groups if group.doc_key not in doc_paths]
        if missing_keys:
            raise SystemExit(
                "missing required doc paths for bounded literal probe mutation: "
                + ", ".join(missing_keys)
            )
        apply_release_closure_bounded_projection_literal_probe_mutations(
            profile_id=str(args.profile),
            doc_paths=doc_paths,
        )
        return 0

    assert_release_closure_bounded_projection_literal_probe_results(
        profile_id=str(args.profile),
        positive_json_path=str(args.positive_json),
        negative_json_path=str(args.negative_json),
    )
    print(f"[PASS] bounded projection literal probe assertions passed: profile={args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
