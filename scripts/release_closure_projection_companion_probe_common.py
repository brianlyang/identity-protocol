#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from release_closure_projection_companion_marker_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID,
    RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID,
    find_release_closure_projection_companion_bundle_spec,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

SUMMARY_STATUS_KEY = "v16x_release_closure_summary_status"
BOUNDARY_STATUS_KEY = "v16x_release_closure_boundary_status"

SUMMARY_DOC_KEY = "summary"
GOVERNANCE_DOC_KEY = "governance"
REVIEW_DOC_KEY = "review"

SUMMARY_LABEL = "summary_doc"
GOVERNANCE_LABEL = "governance_doc"
REVIEW_LABEL = "review_doc"

HEALTH_PROJECTION_DRIFT_REPLACEMENT = "scripts/ci/run_release_readiness_health_probes_ci.sh"


@dataclass(frozen=True)
class ReleaseClosureProjectionCompanionProbeMutationCase:
    doc_key: str
    stale_reason_prefix: str
    marker_indexes: tuple[int, ...]
    replacements: tuple[str, ...]


@dataclass(frozen=True)
class ReleaseClosureProjectionCompanionProbeProfile:
    surface_id: str
    status_key: str
    doc_labels: dict[str, str]
    mutation_cases: tuple[ReleaseClosureProjectionCompanionProbeMutationCase, ...]


RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_PROBE_PROFILE = (
    ReleaseClosureProjectionCompanionProbeProfile(
        surface_id=RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID,
        status_key=SUMMARY_STATUS_KEY,
        doc_labels={SUMMARY_DOC_KEY: SUMMARY_LABEL},
        mutation_cases=(
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_outer_surface_e2e_marker",
                marker_indexes=(0,),
                replacements=("scripts/ci/run_terminal_truth_boundary_e2e_probes_ci.sh",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_health_projection_marker",
                marker_indexes=(0,),
                replacements=(HEALTH_PROJECTION_DRIFT_REPLACEMENT,),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_release_cloud_evidence_marker",
                marker_indexes=(0,),
                replacements=(
                    "release_cloud_evidence_projection=one_look.release_plane_cloud_evidence_status",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_selected_check_scope_marker",
                marker_indexes=(0,),
                replacements=(
                    "targeted_subset_selected_check_scope="
                    "selected_check_scope_projection_status=PASS_REQUIRED",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_foundational_marker",
                marker_indexes=(0,),
                replacements=(
                    "release_readiness_foundational_projection="
                    "one_look.required_contract_coverage_status",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_one_look_topology_marker",
                marker_indexes=(0,),
                replacements=("release_readiness_one_look_family_order=foundational|governance_probe",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_support_preflight_marker",
                marker_indexes=(0,),
                replacements=(
                    "release_readiness_support_preflight_projection="
                    "one_look.control_plane_budget_status",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_terminal_truth_bridge_marker",
                marker_indexes=(0,),
                replacements=("terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_terminal_truth_bridge_rich_companion_marker",
                marker_indexes=(0, -1),
                replacements=(
                    "bridge_execution_closure_status_missing",
                    "bridge_next_state_alignment_status_missing",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_post_closure_adjudication_marker",
                marker_indexes=(0,),
                replacements=(
                    "release_readiness_post_closure_adjudication_order="
                    "runtime_summary_surface_governance|governance_probe_topology",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_release_closure_root_grounding_marker",
                marker_indexes=(0,),
                replacements=("release_closure_root_grounding_order=protocol_root_corpus_precedence",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_full_scan_required_gate_projection_marker",
                marker_indexes=(0,),
                replacements=("scripts/ci/run_full_scan_required_gate_probes_ci.sh",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=SUMMARY_DOC_KEY,
                stale_reason_prefix="missing_active_runtime_closure_projection_marker",
                marker_indexes=(0,),
                replacements=("active_runtime_closure_projection=one_look.identity_codex_launcher_status",),
            ),
        ),
    )
)

RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_PROBE_PROFILE = (
    ReleaseClosureProjectionCompanionProbeProfile(
        surface_id=RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID,
        status_key=BOUNDARY_STATUS_KEY,
        doc_labels={
            GOVERNANCE_DOC_KEY: GOVERNANCE_LABEL,
            REVIEW_DOC_KEY: REVIEW_LABEL,
        },
        mutation_cases=(
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=GOVERNANCE_DOC_KEY,
                stale_reason_prefix="missing_outer_surface_e2e_marker",
                marker_indexes=(0,),
                replacements=("scripts/ci/run_terminal_truth_boundary_e2e_probes_ci.sh",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=GOVERNANCE_DOC_KEY,
                stale_reason_prefix="missing_terminal_truth_bridge_marker",
                marker_indexes=(0,),
                replacements=("terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=GOVERNANCE_DOC_KEY,
                stale_reason_prefix="missing_terminal_truth_bridge_rich_companion_marker",
                marker_indexes=(0, -1),
                replacements=(
                    "bridge_execution_closure_status_missing",
                    "bridge_next_state_alignment_status_missing",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=GOVERNANCE_DOC_KEY,
                stale_reason_prefix="missing_repo_global_closure_boundary_marker",
                marker_indexes=(0,),
                replacements=("repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=GOVERNANCE_DOC_KEY,
                stale_reason_prefix="missing_release_readiness_health_projection_marker",
                marker_indexes=(0,),
                replacements=(HEALTH_PROJECTION_DRIFT_REPLACEMENT,),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=REVIEW_DOC_KEY,
                stale_reason_prefix="missing_active_runtime_closure_projection_marker",
                marker_indexes=(0,),
                replacements=("active_runtime_closure_projection=one_look.identity_codex_launcher_status",),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=REVIEW_DOC_KEY,
                stale_reason_prefix="missing_post_closure_adjudication_marker",
                marker_indexes=(0,),
                replacements=(
                    "release_readiness_post_closure_adjudication_order="
                    "runtime_summary_surface_governance|governance_probe_topology",
                ),
            ),
            ReleaseClosureProjectionCompanionProbeMutationCase(
                doc_key=REVIEW_DOC_KEY,
                stale_reason_prefix="missing_release_closure_root_grounding_marker",
                marker_indexes=(0,),
                replacements=("release_closure_root_grounding_order=protocol_root_corpus_precedence",),
            ),
        ),
    )
)


def release_closure_projection_companion_probe_profile(
    surface_id: str,
) -> ReleaseClosureProjectionCompanionProbeProfile:
    if surface_id == RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID:
        return RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_PROBE_PROFILE
    if surface_id == RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID:
        return RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_PROBE_PROFILE
    raise ValueError(f"unsupported release closure projection companion probe surface: {surface_id}")


def _mutate_text(*, text: str, needle: str, replacement: str) -> str:
    occurrence_count = text.count(needle)
    if occurrence_count < 1:
        raise SystemExit(
            f"probe setup failed: expected at least 1 occurrence for literal {needle!r}; found 0"
        )
    mutated = text.replace(needle, replacement)
    if needle in mutated:
        residual = mutated.count(needle)
        raise SystemExit(
            f"probe setup failed: literal residual remained after mutation; needle={needle!r} remaining_occurrences={residual}"
        )
    return mutated


def _resolve_case_markers(
    *,
    surface_id: str,
    case: ReleaseClosureProjectionCompanionProbeMutationCase,
) -> tuple[str, ...]:
    bundle_spec = find_release_closure_projection_companion_bundle_spec(
        surface_id=surface_id,
        stale_reason_prefix=case.stale_reason_prefix,
    )
    if bundle_spec is None:
        raise SystemExit(
            "probe setup failed: missing bundle spec for surface="
            f"{surface_id} stale_reason_prefix={case.stale_reason_prefix}"
        )
    markers: list[str] = []
    for marker_index in case.marker_indexes:
        try:
            markers.append(bundle_spec.markers[marker_index])
        except IndexError as exc:
            raise SystemExit(
                "probe setup failed: marker index out of range for surface="
                f"{surface_id} stale_reason_prefix={case.stale_reason_prefix} marker_index={marker_index}"
            ) from exc
    return tuple(markers)


def _expected_reason(
    *,
    label: str,
    stale_reason_prefix: str,
    marker: str,
) -> str:
    return f"{label}_{stale_reason_prefix}:{marker}"


def apply_release_closure_projection_companion_probe_mutations(
    *,
    surface_id: str,
    path_by_doc_key: dict[str, str],
) -> None:
    profile = release_closure_projection_companion_probe_profile(surface_id)
    for case in profile.mutation_cases:
        target_path = path_by_doc_key.get(case.doc_key)
        if not target_path:
            raise SystemExit(
                f"probe setup failed: missing target path for doc_key={case.doc_key} surface={surface_id}"
            )
        target = Path(target_path).expanduser().resolve()
        text = target.read_text(encoding="utf-8")
        for marker, replacement in zip(
            _resolve_case_markers(surface_id=surface_id, case=case),
            case.replacements,
            strict=True,
        ):
            text = _mutate_text(text=text, needle=marker, replacement=replacement)
        target.write_text(text, encoding="utf-8")


def collect_release_closure_projection_companion_probe_expected_reasons(
    *,
    surface_id: str,
) -> tuple[str, ...]:
    profile = release_closure_projection_companion_probe_profile(surface_id)
    expected_reasons: list[str] = []
    for case in profile.mutation_cases:
        label = profile.doc_labels[case.doc_key]
        for marker in _resolve_case_markers(surface_id=surface_id, case=case):
            expected_reasons.append(
                _expected_reason(
                    label=label,
                    stale_reason_prefix=case.stale_reason_prefix,
                    marker=marker,
                )
            )
    return tuple(expected_reasons)


def _load_json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def assert_release_closure_projection_companion_probe_results(
    *,
    surface_id: str,
    positive_json_path: str,
    negative_json_path: str,
) -> None:
    profile = release_closure_projection_companion_probe_profile(surface_id)
    positive = _load_json(positive_json_path)
    negative = _load_json(negative_json_path)

    if positive.get(profile.status_key) != STATUS_PASS_REQUIRED:
        raise SystemExit(
            f"positive release-closure {surface_id} projection-companion bundle status must PASS_REQUIRED"
        )
    if negative.get(profile.status_key) != STATUS_FAIL_REQUIRED:
        raise SystemExit(
            f"negative release-closure {surface_id} projection-companion bundle status must FAIL_REQUIRED"
        )

    reasons = set(negative.get("stale_reasons") or [])
    missing = sorted(
        set(
            collect_release_closure_projection_companion_probe_expected_reasons(
                surface_id=surface_id,
            )
        )
        - reasons
    )
    if missing:
        raise SystemExit(
            "negative release-closure "
            f"{surface_id} projection-companion bundle probe is missing expected stale reasons: "
            + ", ".join(missing)
        )


def _build_path_by_doc_key(args: argparse.Namespace) -> dict[str, str]:
    path_by_doc_key: dict[str, str] = {}
    if getattr(args, "summary_path", None):
        path_by_doc_key[SUMMARY_DOC_KEY] = str(args.summary_path)
    if getattr(args, "governance_path", None):
        path_by_doc_key[GOVERNANCE_DOC_KEY] = str(args.governance_path)
    if getattr(args, "review_path", None):
        path_by_doc_key[REVIEW_DOC_KEY] = str(args.review_path)
    return path_by_doc_key


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Shared mutation/assertion helper for release-closure projection-companion probes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mutate_parser = subparsers.add_parser("mutate", help="apply shadow-doc mutations for a surface")
    mutate_parser.add_argument(
        "--surface",
        choices=(
            RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID,
            RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID,
        ),
        required=True,
    )
    mutate_parser.add_argument("--summary-path")
    mutate_parser.add_argument("--governance-path")
    mutate_parser.add_argument("--review-path")

    assert_parser = subparsers.add_parser("assert", help="assert negative stale reasons for a surface")
    assert_parser.add_argument(
        "--surface",
        choices=(
            RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_SURFACE_ID,
            RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_SURFACE_ID,
        ),
        required=True,
    )
    assert_parser.add_argument("--positive-json", required=True)
    assert_parser.add_argument("--negative-json", required=True)

    args = parser.parse_args()
    if args.command == "mutate":
        apply_release_closure_projection_companion_probe_mutations(
            surface_id=str(args.surface),
            path_by_doc_key=_build_path_by_doc_key(args),
        )
        print(f"[PASS] projection-companion probe mutations applied: surface={args.surface}")
        return 0

    assert_release_closure_projection_companion_probe_results(
        surface_id=str(args.surface),
        positive_json_path=str(args.positive_json),
        negative_json_path=str(args.negative_json),
    )
    print(f"[PASS] projection-companion probe assertions passed: surface={args.surface}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
