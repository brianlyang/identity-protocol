#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_SUMMARY = "IP-RCSUM-001"

PHILOSOPHY_DOC = "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
PROTOCOL_DOC = "identity/protocol/IDENTITY_PROTOCOL.md"
RUNTIME_DOC = "identity/protocol/IDENTITY_RUNTIME.md"
ISSUE_REGISTER_DOC = "docs/workbook/protocol-issue-register-v1.6.md"
WORKBOOK_DOC = "docs/workbook/protocol-deep-audit-workbook-v1.6.md"
GOVERNANCE_DOC = "docs/governance/identity-v1.6x-release-closure-governance.md"
REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"
SUMMARY_DOC = "docs/release/identity-v1.6x-release-closure-summary.md"

ISSUE_ROW_RE = re.compile(r"^\|\s*(ISSUE-(\d+))\b")
STREAM_VERSION_RE = re.compile(r"\bv1\.6\.(\d+)\b")
FORBIDDEN_STALE_MARKERS = (
    "Workspace-local core-role required closure: **Go**",
    "workspace-local core release scope is now green on required closure",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_issue_register(text: str) -> tuple[str, list[str]]:
    max_issue_num = 0
    closed_versions: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("| ISSUE-"):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 4:
            continue
        issue_cell = parts[1]
        status_cell = parts[2]
        stream_cell = parts[3].strip().strip("`")
        match = ISSUE_ROW_RE.match(f"| {issue_cell}")
        if match:
            max_issue_num = max(max_issue_num, int(match.group(2)))
        if status_cell == "CLOSED":
            version_match = STREAM_VERSION_RE.search(stream_cell)
            if version_match:
                closed_versions.add(f"v1.6.{int(version_match.group(1))}")
    if max_issue_num <= 0:
        raise ValueError("issue_register_missing_issue_rows")
    highest_issue = f"ISSUE-{max_issue_num:03d}"
    ordered_versions = sorted(closed_versions, key=lambda token: int(token.split(".")[-1]))
    return highest_issue, ordered_versions


def _contains_issue_horizon(text: str, highest_issue: str) -> bool:
    pattern = rf"`ISSUE-001`\s+through\s+`{re.escape(highest_issue)}`"
    return re.search(pattern, text) is not None


def _extract_boundary_versions(*texts: str) -> list[str]:
    versions: set[str] = set()
    for text in texts:
        for match in STREAM_VERSION_RE.finditer(text):
            versions.add(f"v1.6.{int(match.group(1))}")
    return sorted(versions, key=lambda token: int(token.split(".")[-1]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate canonical v1.6.x release summary doc against current release-boundary law.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    philosophy_path = (repo_root / PHILOSOPHY_DOC).resolve()
    protocol_path = (repo_root / PROTOCOL_DOC).resolve()
    runtime_path = (repo_root / RUNTIME_DOC).resolve()
    issue_register_path = (repo_root / ISSUE_REGISTER_DOC).resolve()
    workbook_path = (repo_root / WORKBOOK_DOC).resolve()
    governance_path = (repo_root / GOVERNANCE_DOC).resolve()
    review_path = (repo_root / REVIEW_DOC).resolve()
    summary_path = (repo_root / SUMMARY_DOC).resolve()

    payload: dict[str, Any] = {
        "v16x_release_closure_summary_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "summary_doc": str(summary_path),
        "current_issue_horizon": "",
        "highest_closed_v16_stream_version": "",
        "boundary_stream_versions": [],
        "stale_reasons": [],
    }

    try:
        for path in (
            philosophy_path,
            protocol_path,
            runtime_path,
            issue_register_path,
            workbook_path,
            governance_path,
            review_path,
            summary_path,
        ):
            if not path.exists():
                raise FileNotFoundError(f"missing_required_doc:{path}")

        philosophy_text = _read(philosophy_path)
        issue_register_text = _read(issue_register_path)
        governance_text = _read(governance_path)
        review_text = _read(review_path)
        summary_text = _read(summary_path)
        highest_issue, closed_versions = _parse_issue_register(issue_register_text)
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_SUMMARY
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    highest_version = closed_versions[-1] if closed_versions else ""
    boundary_versions = _extract_boundary_versions(governance_text, review_text)
    payload["current_issue_horizon"] = highest_issue
    payload["highest_closed_v16_stream_version"] = highest_version
    payload["boundary_stream_versions"] = boundary_versions

    stale_reasons: list[str] = []

    if "source-order" not in philosophy_text or "reading-order" not in philosophy_text or "adjudication-order" not in philosophy_text:
        stale_reasons.append("philosophy_root_order_markers_missing")

    for required_ref in (
        PHILOSOPHY_DOC,
        PROTOCOL_DOC,
        RUNTIME_DOC,
        GOVERNANCE_DOC,
        REVIEW_DOC,
        "identity/protocol/mappings/workbook-registry.current.yaml",
        "identity/protocol/mappings/stream-doc-registry.current.yaml",
        "identity/protocol/mappings/contract-binding.current.yaml",
        "identity/protocol/mappings/control-plane-status.current.yaml",
        "identity/protocol/mappings/control-plane-budget.current.yaml",
        ISSUE_REGISTER_DOC,
        WORKBOOK_DOC,
    ):
        if required_ref not in summary_text:
            stale_reasons.append(f"summary_doc_missing_required_ref:{required_ref}")

    if "Question class and authoritative answer surfaces" not in summary_text:
        stale_reasons.append("summary_doc_missing_question_class_section")
    if "root-closed" not in summary_text or "machine-closed" not in summary_text or "runtime-closed" not in summary_text:
        stale_reasons.append("summary_doc_missing_root_machine_runtime_closure_markers")
    if not _contains_issue_horizon(summary_text, highest_issue):
        stale_reasons.append("summary_doc_issue_horizon_mismatch")
    if highest_version and highest_version not in summary_text:
        stale_reasons.append("summary_doc_missing_highest_v16_stream_version")
    for version in boundary_versions:
        if version not in summary_text:
            stale_reasons.append(f"summary_doc_missing_boundary_stream_version:{version}")

    if "runtime verdict surface" not in summary_text or "fleet-scope closure matrix" not in summary_text:
        stale_reasons.append("summary_doc_missing_scope_separation_markers")
    if "not declare a release tag" not in summary_text:
        stale_reasons.append("summary_doc_missing_release_tag_boundary")

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
