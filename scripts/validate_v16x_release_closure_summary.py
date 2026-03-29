#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from release_closure_doc_common import (
    extract_release_closure_v16_versions,
    parse_release_closure_issue_register,
    resolve_release_closure_doc_paths,
)
from release_closure_required_doc_bundle_common import (
    collect_release_closure_summary_required_doc_bundle_stale_reasons,
)
from release_closure_foundational_marker_common import (
    collect_release_closure_foundational_philosophy_bundle_stale_reasons,
    collect_release_closure_summary_foundational_bundle_stale_reasons,
)
from release_closure_doc_reference_bundle_common import (
    collect_release_closure_summary_doc_reference_bundle_stale_reasons,
)
from release_closure_horizon_alignment_bundle_common import (
    collect_release_closure_summary_horizon_alignment_bundle_stale_reasons,
)
from release_closure_summary_framing_bundle_common import (
    collect_release_closure_summary_framing_bundle_stale_reasons,
)
from release_closure_narrative_marker_common import (
    collect_release_closure_summary_narrative_bundle_stale_reasons,
)
from release_closure_control_surface_literal_bundle_common import (
    collect_release_closure_summary_control_surface_literal_bundle_stale_reasons,
)
from release_closure_projection_companion_marker_bundle_common import (
    collect_release_closure_summary_projection_companion_bundle_stale_reasons,
)
from release_closure_bounded_projection_literal_bundle_common import (
    collect_release_closure_bounded_projection_literal_bundle_stale_reasons,
)
from release_closure_operational_marker_bundle_common import (
    RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
    collect_release_closure_operational_marker_bundle_stale_reasons,
)
from release_readiness_active_runtime_closure_projection_common import (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS,
)
from release_readiness_terminal_truth_bridge_common import (
    RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS,
)
from repo_root_resolution_common import resolve_protocol_repo_root
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_SUMMARY = "IP-RCSUM-001"
SUMMARY_DOC_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_STALE_REASON_PREFIX = (
    "summary_doc_missing_active_runtime_closure_projection_marker"
)
SUMMARY_DOC_TERMINAL_TRUTH_BRIDGE_STALE_REASON_PREFIX = (
    "summary_doc_missing_release_readiness_terminal_truth_bridge_marker"
)

def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical v1.6.x release summary doc against current release-boundary law.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    docs = resolve_release_closure_doc_paths(repo_root)

    payload: dict[str, Any] = {
        "v16x_release_closure_summary_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "summary_doc": str(docs.summary_path),
        "current_issue_horizon": "",
        "highest_closed_v16_stream_version": "",
        "boundary_stream_versions": [],
        "stale_reasons": [],
    }

    stale_reasons = collect_release_closure_summary_required_doc_bundle_stale_reasons(
        repo_root
    )
    if stale_reasons:
        payload["error_code"] = ERR_RELEASE_SUMMARY
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        philosophy_text = _read(docs.philosophy_path)
        issue_register_text = _read(docs.issue_register_path)
        governance_text = _read(docs.governance_path)
        review_text = _read(docs.review_path)
        summary_text = _read(docs.summary_path)
        highest_issue, closed_versions = parse_release_closure_issue_register(issue_register_text)
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_SUMMARY
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    highest_version = closed_versions[-1] if closed_versions else ""
    boundary_versions = extract_release_closure_v16_versions(governance_text, review_text)
    payload["current_issue_horizon"] = highest_issue
    payload["highest_closed_v16_stream_version"] = highest_version
    payload["boundary_stream_versions"] = boundary_versions

    stale_reasons = []

    stale_reasons.extend(
        collect_release_closure_foundational_philosophy_bundle_stale_reasons(
            philosophy_text
        )
    )

    stale_reasons.extend(
        collect_release_closure_summary_doc_reference_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )

    stale_reasons.extend(
        collect_release_closure_summary_foundational_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    stale_reasons.extend(
        collect_release_closure_summary_horizon_alignment_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
            current_issue=highest_issue,
            highest_version=highest_version,
            boundary_versions=tuple(boundary_versions),
        )
    )

    stale_reasons.extend(
        collect_release_closure_summary_framing_bundle_stale_reasons(summary_text)
    )
    stale_reasons.extend(
        collect_release_closure_summary_control_surface_literal_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    stale_reasons.extend(
        collect_release_closure_bounded_projection_literal_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    stale_reasons.extend(
        collect_release_closure_summary_projection_companion_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    if not RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS:
        stale_reasons.append(
            f"{SUMMARY_DOC_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_STALE_REASON_PREFIX}:active_runtime_surface_constraints_empty"
        )
    if not RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS:
        stale_reasons.append(
            f"{SUMMARY_DOC_TERMINAL_TRUTH_BRIDGE_STALE_REASON_PREFIX}:terminal_truth_bridge_surface_constraints_empty"
        )
    stale_reasons.extend(
        collect_release_closure_operational_marker_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
            bundle_specs=RELEASE_CLOSURE_SUMMARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
        )
    )
    stale_reasons.extend(
        collect_release_closure_summary_narrative_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )

    payload["v16x_release_closure_summary_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_SUMMARY
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
