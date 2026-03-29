#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from release_closure_doc_common import (
    parse_release_closure_issue_register,
    resolve_release_closure_doc_paths,
)
from release_closure_required_doc_bundle_common import (
    collect_release_closure_boundary_required_doc_bundle_stale_reasons,
)
from release_closure_foundational_marker_common import (
    collect_release_closure_boundary_foundational_bundle_stale_reasons,
    collect_release_closure_foundational_philosophy_bundle_stale_reasons,
)
from release_closure_doc_reference_bundle_common import (
    collect_release_closure_boundary_doc_reference_bundle_stale_reasons,
)
from release_closure_horizon_alignment_bundle_common import (
    collect_release_closure_boundary_horizon_alignment_bundle_stale_reasons,
)
from release_closure_narrative_marker_common import (
    collect_release_closure_boundary_narrative_bundle_stale_reasons,
)
from release_closure_control_surface_literal_bundle_common import (
    collect_release_closure_boundary_control_surface_literal_bundle_stale_reasons,
)
from release_closure_projection_companion_marker_bundle_common import (
    collect_release_closure_boundary_projection_companion_bundle_stale_reasons,
)
from release_closure_bounded_projection_literal_bundle_common import (
    collect_release_closure_bounded_projection_literal_bundle_stale_reasons,
)
from release_closure_operational_marker_bundle_common import (
    RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
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
ERR_RELEASE_CLOSURE = "IP-RCLOS-001"
BOUNDARY_DOC_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_STALE_REASON_SUFFIX = (
    "missing_active_runtime_closure_projection_marker"
)
BOUNDARY_DOC_TERMINAL_TRUTH_BRIDGE_STALE_REASON_SUFFIX = (
    "missing_terminal_truth_bridge_marker"
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

    stale_reasons = collect_release_closure_boundary_required_doc_bundle_stale_reasons(
        repo_root
    )
    if stale_reasons:
        payload["error_code"] = ERR_RELEASE_CLOSURE
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        philosophy_text = _read(docs.philosophy_path)
        _read(docs.protocol_path)
        _read(docs.runtime_path)
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

    stale_reasons = []

    stale_reasons.extend(
        collect_release_closure_foundational_philosophy_bundle_stale_reasons(
            philosophy_text
        )
    )

    for label, text in (
        ("governance_doc", governance_text),
        ("review_doc", review_text),
    ):
        stale_reasons.extend(
            collect_release_closure_boundary_doc_reference_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        stale_reasons.extend(
            collect_release_closure_boundary_foundational_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        stale_reasons.extend(
            collect_release_closure_boundary_control_surface_literal_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        stale_reasons.extend(
            collect_release_closure_boundary_projection_companion_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        if not RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS:
            stale_reasons.append(
                f"{label}_{BOUNDARY_DOC_ACTIVE_RUNTIME_CLOSURE_TOPOLOGY_STALE_REASON_SUFFIX}:active_runtime_surface_constraints_empty"
            )
        if not RELEASE_READINESS_TERMINAL_TRUTH_BRIDGE_SURFACE_CONSTRAINTS:
            stale_reasons.append(
                f"{label}_{BOUNDARY_DOC_TERMINAL_TRUTH_BRIDGE_STALE_REASON_SUFFIX}:terminal_truth_bridge_surface_constraints_empty"
            )
        stale_reasons.extend(
            collect_release_closure_operational_marker_bundle_stale_reasons(
                text,
                label=label,
                bundle_specs=RELEASE_CLOSURE_BOUNDARY_OPERATIONAL_MARKER_BUNDLE_SPECS,
            )
        )
        stale_reasons.extend(
            collect_release_closure_bounded_projection_literal_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        stale_reasons.extend(
            collect_release_closure_boundary_narrative_bundle_stale_reasons(
                text,
                label=label,
            )
        )
        stale_reasons.extend(
            collect_release_closure_boundary_horizon_alignment_bundle_stale_reasons(
                text,
                label=label,
                current_issue=highest_issue,
                highest_version=highest_version,
            )
        )

    payload["v16x_release_closure_boundary_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_CLOSURE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
