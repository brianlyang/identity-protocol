#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER,
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_FIELDS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

SUMMARY_CONTROL_SURFACE_PROFILE_ID = "summary_control_surface_bundle"
BOUNDARY_CONTROL_SURFACE_PROFILE_ID = "boundary_control_surface_bundle"
SURFACE_LITERAL_CANONICALITY_PROFILE_ID = "surface_literal_canonicality"

SUMMARY_STATUS_KEY = "v16x_release_closure_summary_status"
BOUNDARY_STATUS_KEY = "v16x_release_closure_boundary_status"

SUMMARY_PATH_KEY = "summary"
GOVERNANCE_PATH_KEY = "governance"
REVIEW_PATH_KEY = "review"

RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_ADDITIVE_POLLUTION_MARKER = (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER
    + "|"
    + RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_FIELDS[0]
)
RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_ADDITIVE_POLLUTION_MARKER = (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER
    + "|"
    + RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER[-1]
)


@dataclass(frozen=True)
class LiteralMutationSpec:
    path_key: str
    needle: str
    replacement: str
    mode: str = "all"
    min_occurrences: int = 1
    require_absent_after: bool = True


SUMMARY_CONTROL_SURFACE_MUTATION_SPECS: tuple[LiteralMutationSpec, ...] = (
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        replacement="repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status",
    ),
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        replacement="active_runtime_closure_projection=one_look.identity_codex_launcher_status",
    ),
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
        replacement="governance_probe_projection=one_look.runtime_summary_surface_governance_probe_status",
    ),
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        replacement=RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        replacement=RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
)

BOUNDARY_CONTROL_SURFACE_MUTATION_SPECS: tuple[LiteralMutationSpec, ...] = (
    LiteralMutationSpec(
        path_key=GOVERNANCE_PATH_KEY,
        needle=RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        replacement="repo_global_closure_projection=one_look.executable_surface_runtime_literal_lock_status",
    ),
    LiteralMutationSpec(
        path_key=GOVERNANCE_PATH_KEY,
        needle=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        replacement=RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        path_key=REVIEW_PATH_KEY,
        needle=RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        replacement="active_runtime_closure_projection=one_look.identity_codex_launcher_status",
    ),
    LiteralMutationSpec(
        path_key=REVIEW_PATH_KEY,
        needle=RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
        replacement="governance_probe_projection=one_look.runtime_summary_surface_governance_probe_status",
    ),
    LiteralMutationSpec(
        path_key=REVIEW_PATH_KEY,
        needle=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        replacement=RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
)

SURFACE_LITERAL_CANONICALITY_MUTATION_SPECS: tuple[LiteralMutationSpec, ...] = (
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        replacement=RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        path_key=SUMMARY_PATH_KEY,
        needle=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        replacement=RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        path_key=GOVERNANCE_PATH_KEY,
        needle=RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        replacement=RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_SURFACE_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        path_key=GOVERNANCE_PATH_KEY,
        needle=RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        replacement=RELEASE_CLOSURE_POST_CLOSURE_ADJUDICATION_ORDER_ADDITIVE_POLLUTION_MARKER,
        mode="first",
        require_absent_after=False,
    ),
)


def _mutate_text(*, text: str, spec: LiteralMutationSpec) -> str:
    occurrence_count = text.count(spec.needle)
    if occurrence_count < spec.min_occurrences:
        raise SystemExit(
            "probe setup failed: expected at least "
            f"{spec.min_occurrences} occurrence(s) for literal {spec.needle!r}; "
            f"found {occurrence_count}"
        )
    if spec.mode == "first":
        mutated = text.replace(spec.needle, spec.replacement, 1)
        replaced = 1
    elif spec.mode == "all":
        mutated = text.replace(spec.needle, spec.replacement)
        replaced = occurrence_count
    else:
        raise SystemExit(f"unsupported mutation mode: {spec.mode}")
    if replaced < spec.min_occurrences:
        raise SystemExit(
            "probe setup failed: mutation replaced "
            f"{replaced} occurrence(s), expected at least {spec.min_occurrences}"
        )
    if spec.require_absent_after and spec.needle in mutated:
        residual = mutated.count(spec.needle)
        raise SystemExit(
            "probe setup failed: literal residual remained after mutation; "
            f"needle={spec.needle!r} remaining_occurrences={residual}"
        )
    return mutated


def _path_map(*, summary_path: str | None, governance_path: str | None, review_path: str | None) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    if summary_path:
        mapping[SUMMARY_PATH_KEY] = Path(summary_path).expanduser().resolve()
    if governance_path:
        mapping[GOVERNANCE_PATH_KEY] = Path(governance_path).expanduser().resolve()
    if review_path:
        mapping[REVIEW_PATH_KEY] = Path(review_path).expanduser().resolve()
    return mapping


def _mutation_specs_for_profile(profile_id: str) -> tuple[LiteralMutationSpec, ...]:
    if profile_id == SUMMARY_CONTROL_SURFACE_PROFILE_ID:
        return SUMMARY_CONTROL_SURFACE_MUTATION_SPECS
    if profile_id == BOUNDARY_CONTROL_SURFACE_PROFILE_ID:
        return BOUNDARY_CONTROL_SURFACE_MUTATION_SPECS
    if profile_id == SURFACE_LITERAL_CANONICALITY_PROFILE_ID:
        return SURFACE_LITERAL_CANONICALITY_MUTATION_SPECS
    raise SystemExit(f"unsupported control-surface probe profile: {profile_id}")


def apply_release_closure_control_surface_probe_mutations(
    *,
    profile_id: str,
    summary_path: str | None = None,
    governance_path: str | None = None,
    review_path: str | None = None,
) -> None:
    path_map = _path_map(
        summary_path=summary_path,
        governance_path=governance_path,
        review_path=review_path,
    )
    for spec in _mutation_specs_for_profile(profile_id):
        target = path_map.get(spec.path_key)
        if target is None:
            raise SystemExit(
                f"probe setup failed: missing path for key={spec.path_key} profile={profile_id}"
            )
        text = target.read_text(encoding="utf-8")
        target.write_text(_mutate_text(text=text, spec=spec), encoding="utf-8")
    print(f"[PASS] control-surface probe mutations applied: profile={profile_id}")


def _load_json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require_reason(reasons: set[str], reason: str, message: str) -> None:
    if reason not in reasons:
        raise SystemExit(message)


def assert_release_closure_control_surface_probe_results(
    *,
    profile_id: str,
    positive_json_path: str | None = None,
    negative_json_path: str | None = None,
    summary_positive_json_path: str | None = None,
    summary_negative_json_path: str | None = None,
    boundary_positive_json_path: str | None = None,
    boundary_negative_json_path: str | None = None,
) -> None:
    if profile_id == SUMMARY_CONTROL_SURFACE_PROFILE_ID:
        positive = _load_json(str(positive_json_path))
        negative = _load_json(str(negative_json_path))
        if positive.get(SUMMARY_STATUS_KEY) != STATUS_PASS_REQUIRED:
            raise SystemExit(
                "positive release-closure summary control-surface bundle status must PASS_REQUIRED"
            )
        if negative.get(SUMMARY_STATUS_KEY) != STATUS_FAIL_REQUIRED:
            raise SystemExit(
                "negative release-closure summary control-surface bundle status must FAIL_REQUIRED"
            )
        reasons = set(negative.get("stale_reasons") or [])
        for reason, message in (
            (
                "summary_doc_repo_global_closure_projection_line_not_canonical",
                "negative release-closure summary control-surface bundle must detect repo-global projection drift",
            ),
            (
                "summary_doc_active_runtime_closure_projection_line_not_canonical",
                "negative release-closure summary control-surface bundle must detect active-runtime projection drift",
            ),
            (
                "summary_doc_governance_probe_projection_line_not_canonical",
                "negative release-closure summary control-surface bundle must detect governance-probe projection drift",
            ),
            (
                "summary_doc_terminal_truth_bridge_surface_line_not_canonical",
                "negative release-closure summary control-surface bundle must detect terminal-truth bridge additive pollution",
            ),
            (
                "summary_doc_post_closure_adjudication_order_line_not_canonical",
                "negative release-closure summary control-surface bundle must detect post-closure order additive pollution",
            ),
        ):
            _require_reason(reasons, reason, message)
        return

    if profile_id == BOUNDARY_CONTROL_SURFACE_PROFILE_ID:
        positive = _load_json(str(positive_json_path))
        negative = _load_json(str(negative_json_path))
        if positive.get(BOUNDARY_STATUS_KEY) != STATUS_PASS_REQUIRED:
            raise SystemExit(
                "positive release-closure boundary control-surface bundle status must PASS_REQUIRED"
            )
        if negative.get(BOUNDARY_STATUS_KEY) != STATUS_FAIL_REQUIRED:
            raise SystemExit(
                "negative release-closure boundary control-surface bundle status must FAIL_REQUIRED"
            )
        reasons = set(negative.get("stale_reasons") or [])
        for reason, message in (
            (
                "governance_doc_repo_global_closure_projection_line_not_canonical",
                "negative release-closure boundary control-surface bundle must detect repo-global projection drift",
            ),
            (
                "governance_doc_terminal_truth_bridge_surface_line_not_canonical",
                "negative release-closure boundary control-surface bundle must detect terminal-truth bridge additive pollution",
            ),
            (
                "review_doc_active_runtime_closure_projection_line_not_canonical",
                "negative release-closure boundary control-surface bundle must detect active-runtime projection drift",
            ),
            (
                "review_doc_governance_probe_projection_line_not_canonical",
                "negative release-closure boundary control-surface bundle must detect governance-probe projection drift",
            ),
            (
                "review_doc_post_closure_adjudication_order_line_not_canonical",
                "negative release-closure boundary control-surface bundle must detect post-closure order additive pollution",
            ),
        ):
            _require_reason(reasons, reason, message)
        return

    if profile_id == SURFACE_LITERAL_CANONICALITY_PROFILE_ID:
        summary_positive = _load_json(str(summary_positive_json_path))
        summary_negative = _load_json(str(summary_negative_json_path))
        boundary_positive = _load_json(str(boundary_positive_json_path))
        boundary_negative = _load_json(str(boundary_negative_json_path))

        if summary_positive.get(SUMMARY_STATUS_KEY) != STATUS_PASS_REQUIRED:
            raise SystemExit("positive release-closure summary status must PASS_REQUIRED")
        if boundary_positive.get(BOUNDARY_STATUS_KEY) != STATUS_PASS_REQUIRED:
            raise SystemExit("positive release-closure boundary status must PASS_REQUIRED")
        if summary_negative.get(SUMMARY_STATUS_KEY) != STATUS_FAIL_REQUIRED:
            raise SystemExit("negative release-closure summary status must FAIL_REQUIRED")
        if boundary_negative.get(BOUNDARY_STATUS_KEY) != STATUS_FAIL_REQUIRED:
            raise SystemExit("negative release-closure boundary status must FAIL_REQUIRED")

        summary_reasons = set(summary_negative.get("stale_reasons") or [])
        boundary_reasons = set(boundary_negative.get("stale_reasons") or [])
        for reason, message in (
            (
                "summary_doc_terminal_truth_bridge_surface_line_not_canonical",
                "negative release-closure summary must detect terminal-truth bridge additive pollution",
            ),
            (
                "summary_doc_post_closure_adjudication_order_line_not_canonical",
                "negative release-closure summary must detect post-closure order additive pollution",
            ),
        ):
            _require_reason(summary_reasons, reason, message)
        for reason, message in (
            (
                "governance_doc_terminal_truth_bridge_surface_line_not_canonical",
                "negative release-closure boundary must detect terminal-truth bridge additive pollution",
            ),
            (
                "governance_doc_post_closure_adjudication_order_line_not_canonical",
                "negative release-closure boundary must detect post-closure order additive pollution",
            ),
        ):
            _require_reason(boundary_reasons, reason, message)
        return

    raise SystemExit(f"unsupported control-surface probe profile: {profile_id}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply or assert release-closure control-surface probe profiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mutate_parser = subparsers.add_parser("mutate", help="apply shadow-doc mutations")
    mutate_parser.add_argument(
        "--profile",
        choices=(
            SUMMARY_CONTROL_SURFACE_PROFILE_ID,
            BOUNDARY_CONTROL_SURFACE_PROFILE_ID,
            SURFACE_LITERAL_CANONICALITY_PROFILE_ID,
        ),
        required=True,
    )
    mutate_parser.add_argument("--summary-path")
    mutate_parser.add_argument("--governance-path")
    mutate_parser.add_argument("--review-path")

    assert_parser = subparsers.add_parser("assert", help="assert positive/negative probe outputs")
    assert_parser.add_argument(
        "--profile",
        choices=(
            SUMMARY_CONTROL_SURFACE_PROFILE_ID,
            BOUNDARY_CONTROL_SURFACE_PROFILE_ID,
            SURFACE_LITERAL_CANONICALITY_PROFILE_ID,
        ),
        required=True,
    )
    assert_parser.add_argument("--positive-json")
    assert_parser.add_argument("--negative-json")
    assert_parser.add_argument("--summary-positive-json")
    assert_parser.add_argument("--summary-negative-json")
    assert_parser.add_argument("--boundary-positive-json")
    assert_parser.add_argument("--boundary-negative-json")

    args = parser.parse_args()
    if args.command == "mutate":
        apply_release_closure_control_surface_probe_mutations(
            profile_id=str(args.profile),
            summary_path=args.summary_path,
            governance_path=args.governance_path,
            review_path=args.review_path,
        )
        return 0

    assert_release_closure_control_surface_probe_results(
        profile_id=str(args.profile),
        positive_json_path=args.positive_json,
        negative_json_path=args.negative_json,
        summary_positive_json_path=args.summary_positive_json,
        summary_negative_json_path=args.summary_negative_json,
        boundary_positive_json_path=args.boundary_positive_json,
        boundary_negative_json_path=args.boundary_negative_json,
    )
    print(f"[PASS] control-surface probe assertions passed: profile={args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
