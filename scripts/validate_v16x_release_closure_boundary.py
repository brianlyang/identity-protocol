#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from release_closure_doc_common import (
    RELEASE_CLOSURE_DOC_REL_PATHS,
    collect_release_closure_issue_horizon_targets,
    contains_release_closure_issue_horizon,
    parse_release_closure_issue_register,
    resolve_release_closure_doc_paths,
)
from release_closure_foundational_marker_common import (
    collect_release_closure_closure_class_stale_reasons,
    collect_release_closure_philosophy_order_stale_reasons,
    collect_release_closure_terminal_truth_split_stale_reasons,
)
from release_closure_narrative_marker_common import (
    collect_release_closure_narrative_stale_reasons,
)
from repo_root_resolution_common import resolve_protocol_repo_root
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_governance_probe_projection_common import (
    RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
)
from release_readiness_repo_global_closure_projection_common import (
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
)
from release_readiness_runtime_closure_convergence_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS,
    RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_CLOSURE = "IP-RCLOS-001"
REQUIRED_OUTER_SURFACE_E2E_BOUNDARY_MARKERS = (
    "scripts/ci/run_terminal_truth_boundary_outer_surface_e2e_probes_ci.sh",
    "terminal_truth_boundary_projection",
    "summary_terminal_truth_boundary",
)
REQUIRED_RELEASE_READINESS_CONTINUATION_MARKERS = (
    "summary_lifecycle_status=IN_PROGRESS",
    "summary_checkpoint_kind=checkpoint",
    "stable prewrite snapshot",
    "scripts/run_release_readiness_continuation.py",
    "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh",
    "scripts/ci/run_release_readiness_summary_binding_probes_ci.sh",
    "scripts/ci/run_release_readiness_continuation_probes_ci.sh",
    "scripts/ci/run_release_plane_context_resolution_probes_ci.sh",
    *RELEASE_READINESS_GOVERNANCE_PROBE_SURFACE_CONSTRAINTS,
    RELEASE_READINESS_REPO_GLOBAL_CLOSURE_PROJECTION_MARKER,
    "caller cwd",
)
REQUIRED_REPO_GLOBAL_CLOSURE_OWNER_LANE_MARKERS = RELEASE_READINESS_REPO_GLOBAL_CLOSURE_OWNER_LANES
REQUIRED_REPO_GLOBAL_CLOSURE_PROOF_STRENGTH_MARKERS = (
    *RELEASE_READINESS_REPO_GLOBAL_CLOSURE_CHECKED_IDENTITY_COUNT_FIELDS,
)

def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate v1.6.x release-closure boundary docs against the current workbook horizon.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    docs = resolve_release_closure_doc_paths(repo_root)

    payload: dict[str, Any] = {
        "v16x_release_closure_boundary_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "philosophy_doc": str(docs.philosophy_path),
        "protocol_doc": str(docs.protocol_path),
        "runtime_doc": str(docs.runtime_path),
        "issue_register_doc": str(docs.issue_register_path),
        "governance_doc": str(docs.governance_path),
        "review_doc": str(docs.review_path),
        "current_issue_horizon": "",
        "highest_closed_v16_stream_version": "",
        "stale_reasons": [],
    }

    try:
        for path in (
            docs.philosophy_path,
            docs.protocol_path,
            docs.runtime_path,
            docs.issue_register_path,
            docs.governance_path,
            docs.review_path,
        ):
            if not path.exists():
                raise FileNotFoundError(f"missing_required_doc:{path}")

        philosophy_text = _read(docs.philosophy_path)
        protocol_text = _read(docs.protocol_path)
        runtime_text = _read(docs.runtime_path)
        issue_register_text = _read(docs.issue_register_path)
        governance_text = _read(docs.governance_path)
        review_text = _read(docs.review_path)
        highest_issue, closed_versions = parse_release_closure_issue_register(issue_register_text)
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_CLOSURE
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    highest_version = closed_versions[-1] if closed_versions else ""
    payload["current_issue_horizon"] = highest_issue
    payload["highest_closed_v16_stream_version"] = highest_version

    stale_reasons: list[str] = []

    stale_reasons.extend(collect_release_closure_philosophy_order_stale_reasons(philosophy_text))

    for label, text in (
        ("governance_doc", governance_text),
        ("review_doc", review_text),
    ):
        if RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc not in text:
            stale_reasons.append(f"{label}_missing_philosophy_anchor")
        if RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc not in text:
            stale_reasons.append(f"{label}_missing_protocol_anchor")
        if RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc not in text:
            stale_reasons.append(f"{label}_missing_runtime_anchor")
        stale_reasons.extend(collect_release_closure_closure_class_stale_reasons(text, label=label))
        stale_reasons.extend(
            collect_release_closure_terminal_truth_split_stale_reasons(text, label=label)
        )
        for marker in REQUIRED_OUTER_SURFACE_E2E_BOUNDARY_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_outer_surface_e2e_marker:{marker}")
        for marker in REQUIRED_RELEASE_READINESS_CONTINUATION_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_release_readiness_continuation_marker:{marker}")
        for marker in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_active_runtime_closure_projection_marker:{marker}"
                )
        for marker in REQUIRED_REPO_GLOBAL_CLOSURE_OWNER_LANE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_repo_global_closure_owner_lane_marker:{marker}")
        for marker in REQUIRED_REPO_GLOBAL_CLOSURE_PROOF_STRENGTH_MARKERS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_repo_global_closure_proof_strength_marker:{marker}"
                )
        stale_reasons.extend(collect_release_closure_narrative_stale_reasons(text, label=label))
        for marker in RELEASE_READINESS_TRANSPORT_FLEET_CLOSURE_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_transport_fleet_closure_convergence_marker:{marker}")
        for marker in RELEASE_READINESS_ACTIVE_RUNTIME_PACK_CLOSURE_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(f"{label}_missing_active_runtime_pack_closure_convergence_marker:{marker}")
        for marker in RELEASE_READINESS_WORKSPACE_RUNTIME_CLOSURE_COMMAND_CONVERGENCE_MARKERS:
            if marker not in text:
                stale_reasons.append(
                    f"{label}_missing_workspace_runtime_closure_command_convergence_marker:{marker}"
                )
        if not contains_release_closure_issue_horizon(text, highest_issue):
            stale_reasons.append(f"{label}_issue_horizon_mismatch")
        for target_issue in collect_release_closure_issue_horizon_targets(text):
            if target_issue != highest_issue:
                stale_reasons.append(f"{label}_stale_issue_horizon:{target_issue}")
        if highest_version and highest_version not in text:
            stale_reasons.append(f"{label}_missing_highest_v16_stream_version")

    payload["v16x_release_closure_boundary_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_CLOSURE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
