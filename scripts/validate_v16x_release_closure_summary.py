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
    extract_release_closure_v16_versions,
    parse_release_closure_issue_register,
    resolve_release_closure_doc_paths,
)
from release_closure_foundational_marker_common import (
    collect_release_closure_foundational_philosophy_bundle_stale_reasons,
    collect_release_closure_summary_foundational_bundle_stale_reasons,
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
from repo_root_resolution_common import resolve_protocol_repo_root
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_SUMMARY = "IP-RCSUM-001"
FORBIDDEN_STALE_MARKERS = (
    "Workspace-local core-role required closure: **Go**",
    "workspace-local core release scope is now green on required closure",
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

    try:
        for path in (
            docs.philosophy_path,
            docs.protocol_path,
            docs.runtime_path,
            docs.issue_register_path,
            docs.workbook_path,
            docs.governance_path,
            docs.review_path,
            docs.summary_path,
        ):
            if not path.exists():
                raise FileNotFoundError(f"missing_required_doc:{path}")

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

    stale_reasons: list[str] = []

    stale_reasons.extend(
        collect_release_closure_foundational_philosophy_bundle_stale_reasons(
            philosophy_text
        )
    )

    for required_ref in (
        RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc,
        RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc,
        RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc,
        RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc,
        RELEASE_CLOSURE_DOC_REL_PATHS.review_doc,
        "identity/protocol/mappings/workbook-registry.current.yaml",
        "identity/protocol/mappings/stream-doc-registry.current.yaml",
        "identity/protocol/mappings/contract-binding.current.yaml",
        "identity/protocol/mappings/control-plane-status.current.yaml",
        "identity/protocol/mappings/control-plane-budget.current.yaml",
        RELEASE_CLOSURE_DOC_REL_PATHS.issue_register_doc,
        RELEASE_CLOSURE_DOC_REL_PATHS.workbook_doc,
    ):
        if required_ref not in summary_text:
            stale_reasons.append(f"summary_doc_missing_required_ref:{required_ref}")

    if "Question class and authoritative answer surfaces" not in summary_text:
        stale_reasons.append("summary_doc_missing_question_class_section")
    stale_reasons.extend(
        collect_release_closure_summary_foundational_bundle_stale_reasons(
            summary_text,
            label="summary_doc",
        )
    )
    if not contains_release_closure_issue_horizon(summary_text, highest_issue):
        stale_reasons.append("summary_doc_issue_horizon_mismatch")
    for target_issue in collect_release_closure_issue_horizon_targets(summary_text):
        if target_issue != highest_issue:
            stale_reasons.append(f"summary_doc_stale_issue_horizon:{target_issue}")
    if highest_version and highest_version not in summary_text:
        stale_reasons.append("summary_doc_missing_highest_v16_stream_version")
    for version in boundary_versions:
        if version not in summary_text:
            stale_reasons.append(f"summary_doc_missing_boundary_stream_version:{version}")

    if "runtime verdict surface" not in summary_text or "fleet-scope closure matrix" not in summary_text:
        stale_reasons.append("summary_doc_missing_scope_separation_markers")
    if "not declare a release tag" not in summary_text:
        stale_reasons.append("summary_doc_missing_release_tag_boundary")
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

    for marker in FORBIDDEN_STALE_MARKERS:
        if marker in summary_text:
            stale_reasons.append(f"summary_doc_contains_stale_marker:{marker}")

    payload["v16x_release_closure_summary_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_SUMMARY
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
