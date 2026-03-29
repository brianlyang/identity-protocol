#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from release_cloud_evidence_projection_common import (
    RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER,
)
from release_closure_root_grounding_common import (
    RELEASE_CLOSURE_ROOT_GROUNDING_LANE_MARKERS,
    RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS,
    RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER,
)
from release_closure_projection_companion_marker_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS,
    RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS,
    RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS,
    RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
)
from release_readiness_foundational_projection_common import (
    RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD,
)
from release_readiness_one_look_topology_common import (
    RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
)
from release_readiness_post_closure_adjudication_common import (
    RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
    RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
    RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_ONE_LOOK_MARKER,
)
from release_readiness_selected_check_scope_common import (
    RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER,
)
from release_readiness_support_preflight_projection_common import (
    RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS,
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
SUMMARY_PROFILE_ID = "summary"
BOUNDARY_PROFILE_ID = "boundary"
_ROOT_GROUNDING_LANE_ID = "protocol_root_identity_instance_self_judgement"

RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_LANE_MARKER = next(
    marker
    for marker in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_MARKERS
    if marker.endswith(_ROOT_GROUNDING_LANE_ID)
)
RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_VALIDATOR_PATH = next(
    spec.validator_rel
    for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS
    if spec.lane_id == _ROOT_GROUNDING_LANE_ID
)
RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_PROBE_PATH = next(
    spec.probe_rel
    for spec in RELEASE_CLOSURE_ROOT_GROUNDING_LANE_SPECS
    if spec.lane_id == _ROOT_GROUNDING_LANE_ID
)
RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_GOVERNANCE_PROBE_MARKER = (
    "one_look." + RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_PROBE_ONE_LOOK_FIELD
)
RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_STALE_REASON_PREFIX = next(
    spec.stale_reason_prefix
    for spec in RELEASE_CLOSURE_SUMMARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS
    if spec.markers == RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS
)
RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_STALE_REASON_PREFIX = next(
    spec.stale_reason_prefix
    for spec in RELEASE_CLOSURE_BOUNDARY_PROJECTION_COMPANION_MARKER_BUNDLE_SPECS
    if spec.markers == RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS
)


@dataclass(frozen=True)
class LiteralMutationSpec:
    needle: str
    replacement: str
    mode: str = "all"
    min_occurrences: int = 1
    require_absent_after: bool = True


def _bridge_case_drift_marker(case_marker: str) -> str:
    _, _, case_id = case_marker.partition("=")
    return f"terminal_truth_bridge_case_drift={case_id}"


RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_CASE_DRIFT_MUTATION_SPECS: tuple[
    LiteralMutationSpec,
    ...,
] = tuple(
    LiteralMutationSpec(
        needle=case_marker,
        replacement=_bridge_case_drift_marker(case_marker),
    )
    for case_marker in RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS
)


def release_closure_terminal_truth_bridge_case_missing_reasons(
    reason_prefix: str,
) -> tuple[str, ...]:
    return tuple(
        f"{reason_prefix}:{case_marker}"
        for case_marker in RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_CASE_MARKERS
    )


def release_closure_projection_companion_missing_reasons(
    *,
    label: str,
    stale_reason_prefix: str,
    markers: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(f"{label}_{stale_reason_prefix}:{marker}" for marker in markers)


RELEASE_CLOSURE_SUMMARY_MAIN_PROBE_MUTATION_SPECS: tuple[LiteralMutationSpec, ...] = (
    LiteralMutationSpec("`v1.6.21`", "`v1.6.20`"),
    LiteralMutationSpec("fleet-scope closure matrix", "fleet matrix"),
    LiteralMutationSpec(
        "repair success != clean terminal truth",
        "repair success means clean terminal truth",
    ),
    LiteralMutationSpec("summary_terminal_truth_boundary", "summary boundary aggregate"),
    LiteralMutationSpec(
        "one_look.health_report_experience_writeback_projection_status",
        "one_look.health_projection_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        "repo_global_closure_projection="
        "one_look.executable_surface_runtime_literal_lock_status|"
        "one_look.repo_global_drift_marker",
        mode="first",
        require_absent_after=False,
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_ONE_LOOK_MARKER,
        "one_look.repo_global_drift_marker",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
        "one_look.repo_global_checked_identity_count",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
        "scripts/ci/run_repo_global_closure_topology_probes_ci.sh",
    ),
    LiteralMutationSpec(
        "one_look.required_gate_bundle_report_selection_mode",
        "one_look.required_gate_bundle_selection_mode",
    ),
    LiteralMutationSpec(
        "three_plane.required_gate_bundle_report_selection_mode",
        "three_plane.required_gate_bundle_selection_mode",
    ),
    LiteralMutationSpec(
        "resume_capture_mode=stable_prewrite_snapshot",
        "resume_capture_mode=resume_snapshot",
    ),
    LiteralMutationSpec("caller cwd", "caller working directory"),
    LiteralMutationSpec(
        "scripts/run_workspace_runtime_closure_checks.py",
        "scripts/run_workspace_runtime_pack_checks.py",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER,
        "release_cloud_evidence_projection=one_look.release_plane_cloud_evidence_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
        "release_readiness_foundational_projection=one_look.required_contract_coverage_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER,
        "release_readiness_support_preflight_projection=one_look.control_plane_budget_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER,
        "release_readiness_selected_check_scope_projection="
        "one_look.selected_check_scope_projection_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER,
        "release_readiness_one_look_family_order=foundational|governance_probe",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        "release_readiness_post_closure_adjudication_order="
        "runtime_summary_surface_governance|governance_probe_topology",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER,
        "release_closure_root_grounding_order="
        "protocol_root_corpus_precedence|protocol_root_current_truth_epistemology",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_LANE_MARKER,
        "release_closure_root_grounding_lane=protocol_root_current_truth_epistemology",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_VALIDATOR_PATH,
        "scripts/validate_protocol_root_current_truth_epistemology.py",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_PROBE_PATH,
        "scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_GOVERNANCE_PROBE_PROJECTION_MARKER,
        "governance_probe_projection=one_look.runtime_summary_surface_governance_probe_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",
    ),
    *RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_CASE_DRIFT_MUTATION_SPECS,
    LiteralMutationSpec(
        RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[0],
        "bridge_execution_closure_status_missing",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[-1],
        "bridge_next_state_alignment_status_missing",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        "active_runtime_closure_projection=one_look.identity_codex_launcher_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
        "one_look.identity_terminal_truth_veto_state",
    ),
)

RELEASE_CLOSURE_BOUNDARY_MAIN_PROBE_MUTATION_SPECS: tuple[LiteralMutationSpec, ...] = (
    LiteralMutationSpec("`ISSUE-001` through `ISSUE-039`", "`ISSUE-001` through `ISSUE-038`"),
    LiteralMutationSpec("`v1.6.21`", "`v1.6.20`"),
    LiteralMutationSpec("creator/update admission lane", "update lane"),
    LiteralMutationSpec("summary_terminal_truth_boundary", "summary boundary aggregate"),
    LiteralMutationSpec("stable prewrite snapshot", "stable resume snapshot"),
    LiteralMutationSpec("caller cwd", "caller working directory"),
    LiteralMutationSpec(
        "scripts/run_workspace_runtime_closure_checks.py",
        "scripts/run_workspace_runtime_pack_checks.py",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
        "repo_global_closure_projection="
        "one_look.executable_surface_runtime_literal_lock_status|"
        "one_look.repo_global_drift_marker",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD,
        "one_look.repo_global_checked_identity_count",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT,
        "scripts/ci/run_repo_global_closure_topology_probes_ci.sh",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER,
        "terminal_truth_bridge_surface=one_look.identity_terminal_truth_cleanliness_status",
    ),
    *RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_CASE_DRIFT_MUTATION_SPECS,
    LiteralMutationSpec(
        RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[0],
        "bridge_execution_closure_status_missing",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[-1],
        "bridge_next_state_alignment_status_missing",
        mode="first",
    ),
    LiteralMutationSpec(
        f"{RELEASE_CLOSURE_TERMINAL_TRUTH_BRIDGE_GOVERNANCE_PROBE_MARKER}|",
        "",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER,
        "release_readiness_post_closure_adjudication_order="
        "runtime_summary_surface_governance|terminal_truth_bridge",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER,
        "release_closure_root_grounding_order="
        "protocol_root_corpus_precedence|protocol_root_current_truth_epistemology",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_LANE_MARKER,
        "release_closure_root_grounding_lane=protocol_root_current_truth_epistemology",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_VALIDATOR_PATH,
        "scripts/validate_protocol_root_current_truth_epistemology.py",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_PROBE_PATH,
        "scripts/ci/run_protocol_root_current_truth_epistemology_probes_ci.sh",
        mode="first",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
        "active_runtime_closure_projection=one_look.identity_codex_launcher_status",
    ),
    LiteralMutationSpec(
        RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD,
        "one_look.identity_terminal_truth_veto_state",
    ),
)


def _mutate_text(*, text: str, spec: LiteralMutationSpec) -> tuple[str, int]:
    occurrence_count = text.count(spec.needle)
    if occurrence_count < spec.min_occurrences:
        raise SystemExit(
            "probe setup failed: expected at least "
            f"{spec.min_occurrences} occurrence(s) for literal {spec.needle!r}; "
            f"found {occurrence_count}"
        )
    if spec.mode == "first":
        replaced = min(occurrence_count, 1)
        mutated = text.replace(spec.needle, spec.replacement, 1)
    elif spec.mode == "all":
        replaced = occurrence_count
        mutated = text.replace(spec.needle, spec.replacement)
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
    return mutated, replaced


def _load_json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _require_reason(reasons: set[str], reason: str, message: str) -> None:
    if reason not in reasons:
        raise SystemExit(message)


def apply_release_closure_integrated_probe_mutations(
    *,
    profile_id: str,
    target_path: str,
) -> None:
    if profile_id == SUMMARY_PROFILE_ID:
        specs = RELEASE_CLOSURE_SUMMARY_MAIN_PROBE_MUTATION_SPECS
    elif profile_id == BOUNDARY_PROFILE_ID:
        specs = RELEASE_CLOSURE_BOUNDARY_MAIN_PROBE_MUTATION_SPECS
    else:
        raise SystemExit(f"unsupported integrated probe profile: {profile_id}")

    target = Path(target_path).expanduser().resolve()
    text = target.read_text(encoding="utf-8")
    for spec in specs:
        text, _ = _mutate_text(text=text, spec=spec)
    target.write_text(text, encoding="utf-8")
    print(f"[PASS] integrated probe mutations applied: profile={profile_id} path={target}")


def assert_release_closure_integrated_probe_results(
    *,
    profile_id: str,
    positive_json_path: str,
    negative_json_path: str,
) -> None:
    positive = _load_json(positive_json_path)
    negative = _load_json(negative_json_path)

    if profile_id == SUMMARY_PROFILE_ID:
        _assert_release_closure_summary_probe_results(positive=positive, negative=negative)
        return
    if profile_id == BOUNDARY_PROFILE_ID:
        _assert_release_closure_boundary_probe_results(positive=positive, negative=negative)
        return
    raise SystemExit(f"unsupported integrated probe profile: {profile_id}")


def _assert_release_closure_summary_probe_results(
    *,
    positive: dict[str, object],
    negative: dict[str, object],
) -> None:
    if positive.get("v16x_release_closure_summary_status") != STATUS_PASS_REQUIRED:
        raise SystemExit("positive release-closure summary status must PASS_REQUIRED")
    if positive.get("current_issue_horizon") != "ISSUE-039":
        raise SystemExit("positive release-closure summary must track ISSUE-039 horizon")
    if positive.get("highest_closed_v16_stream_version") != "`v1.6.21`".strip("`"):
        raise SystemExit("positive release-closure summary must track highest closed v1.6 stream")
    if negative.get("v16x_release_closure_summary_status") != STATUS_FAIL_REQUIRED:
        raise SystemExit("negative release-closure summary status must FAIL_REQUIRED")

    reasons = set(negative.get("stale_reasons") or [])
    _require_reason(
        reasons,
        "summary_doc_missing_highest_v16_stream_version",
        "negative release-closure summary must detect missing highest v1.6 stream version",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_scope_separation_markers",
        "negative release-closure summary must detect scope-separation marker drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_terminal_truth_split_marker:repair success != clean terminal truth",
        "negative release-closure summary must detect terminal-truth split marker drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_outer_surface_e2e_marker:summary_terminal_truth_boundary",
        "negative release-closure summary must detect outer-surface e2e marker drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_health_projection_marker:"
        "one_look.health_report_experience_writeback_projection_status",
        "negative release-closure summary must detect release-readiness health projection drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_outer_surface_e2e_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_VERSION_BASELINE_ONE_LOOK_MARKER}",
        "negative release-closure summary must detect shared repo-global one-look projection drift",
    )
    _require_reason(
        reasons,
        "summary_doc_repo_global_closure_projection_line_not_canonical",
        "negative release-closure summary must detect repo-global closure projection line drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_outer_surface_e2e_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD}",
        "negative release-closure summary must detect repo-global proof-strength companion drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_outer_surface_e2e_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT}",
        "negative release-closure summary must detect repo-global topology-proof lane drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_full_scan_required_gate_projection_marker:"
        "three_plane.required_gate_bundle_report_selection_mode",
        "negative release-closure summary must detect full-scan required-gate projection drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_lifecycle_marker:"
        "one_look.required_gate_bundle_report_selection_mode",
        "negative release-closure summary must detect required-gate one-look authority drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_lifecycle_marker:"
        "resume_capture_mode=stable_prewrite_snapshot",
        "negative release-closure summary must detect release-readiness lifecycle drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_lifecycle_marker:caller cwd",
        "negative release-closure summary must detect continuation cwd-anchor drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_workspace_runtime_closure_command_convergence_marker:"
        "scripts/run_workspace_runtime_closure_checks.py",
        "negative release-closure summary must detect workspace-runtime closure runner drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_active_runtime_closure_projection_marker:"
        f"{RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER}",
        "negative release-closure summary must detect active-runtime closure projection drift",
    )
    _require_reason(
        reasons,
        "summary_doc_active_runtime_closure_projection_line_not_canonical",
        "negative release-closure summary must detect active-runtime closure projection line drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_release_cloud_evidence_marker:"
        f"{RELEASE_READINESS_RELEASE_CLOUD_EVIDENCE_PROJECTION_MARKER}",
        "negative release-closure summary must detect release-cloud evidence projection drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_foundational_marker:"
        f"{RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER}",
        "negative release-closure summary must detect foundational one-look drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_support_preflight_marker:"
        f"{RELEASE_READINESS_SUPPORT_PREFLIGHT_PROJECTION_MARKER}",
        "negative release-closure summary must detect support-preflight one-look drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_selected_check_scope_marker:"
        f"{RELEASE_READINESS_SELECTED_CHECK_SCOPE_ONE_LOOK_PROJECTION_MARKER}",
        "negative release-closure summary must detect selected-check scope one-look drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_one_look_topology_marker:"
        f"{RELEASE_READINESS_ONE_LOOK_FAMILY_ORDER_MARKER}",
        "negative release-closure summary must detect one-look topology drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_terminal_truth_bridge_marker:"
        f"{RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER}",
        "negative release-closure summary must detect terminal-truth bridge surface drift",
    )
    for reason in release_closure_terminal_truth_bridge_case_missing_reasons(
        "summary_doc_missing_release_readiness_terminal_truth_bridge_marker"
    ):
        _require_reason(
            reasons,
            reason,
            "negative release-closure summary must detect every terminal-truth bridge case drift",
        )
    for reason in release_closure_projection_companion_missing_reasons(
        label="summary_doc",
        stale_reason_prefix=RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_STALE_REASON_PREFIX,
        markers=(
            RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[0],
            RELEASE_CLOSURE_SUMMARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[-1],
        ),
    ):
        _require_reason(
            reasons,
            reason,
            "negative release-closure summary must detect terminal-truth bridge rich companion drift",
        )
    _require_reason(
        reasons,
        "summary_doc_missing_active_runtime_closure_projection_marker:"
        f"{RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD}",
        "negative release-closure summary must detect active-runtime companion detail drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_readiness_post_closure_adjudication_marker:"
        f"{RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER}",
        "negative release-closure summary must detect post-closure adjudication-order drift",
    )
    _require_reason(
        reasons,
        "summary_doc_governance_probe_projection_line_not_canonical",
        "negative release-closure summary must detect governance-probe projection line drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER}",
        "negative release-closure summary must detect release-closure root grounding drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_LANE_MARKER}",
        "negative release-closure summary must detect release-closure root grounding lane drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_VALIDATOR_PATH}",
        "negative release-closure summary must detect release-closure root grounding validator drift",
    )
    _require_reason(
        reasons,
        "summary_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_PROBE_PATH}",
        "negative release-closure summary must detect release-closure root grounding probe drift",
    )


def _assert_release_closure_boundary_probe_results(
    *,
    positive: dict[str, object],
    negative: dict[str, object],
) -> None:
    if positive.get("v16x_release_closure_boundary_status") != STATUS_PASS_REQUIRED:
        raise SystemExit("positive release-closure boundary status must PASS_REQUIRED")
    if positive.get("current_issue_horizon") != "ISSUE-039":
        raise SystemExit("positive release-closure boundary must track ISSUE-039 horizon")
    if positive.get("highest_closed_v16_stream_version") != "`v1.6.21`".strip("`"):
        raise SystemExit("positive release-closure boundary must track highest closed v1.6 stream")
    if negative.get("v16x_release_closure_boundary_status") != STATUS_FAIL_REQUIRED:
        raise SystemExit("negative release-closure boundary status must FAIL_REQUIRED")

    reasons = set(negative.get("stale_reasons") or [])
    _require_reason(
        reasons,
        "governance_doc_issue_horizon_mismatch",
        "negative release-closure boundary must detect governance issue-horizon drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_highest_v16_stream_version",
        "negative release-closure boundary must detect missing highest v1.6 stream version",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_terminal_truth_split_marker:creator/update admission lane",
        "negative release-closure boundary must detect terminal-truth split marker drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_outer_surface_e2e_marker:summary_terminal_truth_boundary",
        "negative release-closure boundary must detect outer-surface e2e marker drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_readiness_continuation_marker:stable prewrite snapshot",
        "negative release-closure boundary must detect release-readiness continuation drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_readiness_continuation_marker:caller cwd",
        "negative release-closure boundary must detect continuation cwd-anchor drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_workspace_runtime_closure_command_convergence_marker:"
        "scripts/run_workspace_runtime_closure_checks.py",
        "negative release-closure boundary must detect workspace-runtime closure runner drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_repo_global_closure_boundary_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER}",
        "negative release-closure boundary must detect repo-global closure projection drift",
    )
    _require_reason(
        reasons,
        "governance_doc_repo_global_closure_projection_line_not_canonical",
        "negative release-closure boundary must detect repo-global closure projection line drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_repo_global_closure_boundary_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_CODEX_LAUNCHER_CHECKED_IDENTITY_COUNT_FIELD}",
        "negative release-closure boundary must detect repo-global proof-strength companion drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_repo_global_closure_boundary_marker:"
        f"{RELEASE_READINESS_REPO_GLOBAL_CLOSURE_TOPOLOGY_PROBE_SCRIPT}",
        "negative release-closure boundary must detect repo-global topology-proof lane drift",
    )
    _require_reason(
        reasons,
        "governance_doc_stale_issue_horizon:ISSUE-038",
        "negative release-closure boundary must detect stale issue-horizon drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_active_runtime_closure_projection_marker:"
        f"{RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER}",
        "negative release-closure boundary must detect active-runtime closure projection drift",
    )
    _require_reason(
        reasons,
        "governance_doc_active_runtime_closure_projection_line_not_canonical",
        "negative release-closure boundary must detect active-runtime closure projection line drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_terminal_truth_bridge_marker:"
        f"{RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_MARKER}",
        "negative release-closure boundary must detect terminal-truth bridge surface drift",
    )
    for reason in release_closure_terminal_truth_bridge_case_missing_reasons(
        "governance_doc_missing_terminal_truth_bridge_marker"
    ):
        _require_reason(
            reasons,
            reason,
            "negative release-closure boundary must detect every terminal-truth bridge case drift",
        )
    for reason in release_closure_projection_companion_missing_reasons(
        label="governance_doc",
        stale_reason_prefix=RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_STALE_REASON_PREFIX,
        markers=(
            RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[0],
            RELEASE_CLOSURE_BOUNDARY_TERMINAL_TRUTH_BRIDGE_RICH_COMPANION_MARKERS[-1],
        ),
    ):
        _require_reason(
            reasons,
            reason,
            "negative release-closure boundary must detect terminal-truth bridge rich companion drift",
        )
    _require_reason(
        reasons,
        "governance_doc_governance_probe_projection_line_not_canonical",
        "negative release-closure boundary must detect governance-probe projection line drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_active_runtime_closure_projection_marker:"
        f"{RELEASE_READINESS_ACTIVE_RUNTIME_TERMINAL_TRUTH_NEGATIVE_FEEDBACK_VETO_STATUS_FIELD}",
        "negative release-closure boundary must detect active-runtime companion detail drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_post_closure_adjudication_marker:"
        f"{RELEASE_READINESS_POST_CLOSURE_ADJUDICATION_ORDER_MARKER}",
        "negative release-closure boundary must detect post-closure adjudication-order drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_ORDER_MARKER}",
        "negative release-closure boundary must detect release-closure root grounding drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_LANE_MARKER}",
        "negative release-closure boundary must detect release-closure root grounding lane drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_VALIDATOR_PATH}",
        "negative release-closure boundary must detect release-closure root grounding validator drift",
    )
    _require_reason(
        reasons,
        "governance_doc_missing_release_closure_root_grounding_marker:"
        f"{RELEASE_CLOSURE_ROOT_GROUNDING_SELF_JUDGEMENT_PROBE_PATH}",
        "negative release-closure boundary must detect release-closure root grounding probe drift",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply or assert shared integrated release-closure probe profiles.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    mutate_parser = subparsers.add_parser("mutate", help="apply shadow-doc mutations")
    mutate_parser.add_argument("--profile", choices=(SUMMARY_PROFILE_ID, BOUNDARY_PROFILE_ID), required=True)
    mutate_parser.add_argument("--path", required=True, help="shadow document path")

    assert_parser = subparsers.add_parser("assert", help="assert positive/negative probe outputs")
    assert_parser.add_argument("--profile", choices=(SUMMARY_PROFILE_ID, BOUNDARY_PROFILE_ID), required=True)
    assert_parser.add_argument("--positive-json", required=True)
    assert_parser.add_argument("--negative-json", required=True)

    args = parser.parse_args()
    if args.command == "mutate":
        apply_release_closure_integrated_probe_mutations(
            profile_id=str(args.profile),
            target_path=str(args.path),
        )
        return 0

    assert_release_closure_integrated_probe_results(
        profile_id=str(args.profile),
        positive_json_path=str(args.positive_json),
        negative_json_path=str(args.negative_json),
    )
    print(f"[PASS] integrated probe assertions passed: profile={args.profile}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
