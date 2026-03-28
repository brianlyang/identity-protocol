#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReleaseClosureDocRelPaths:
    philosophy_doc: str = "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md"
    protocol_doc: str = "identity/protocol/IDENTITY_PROTOCOL.md"
    runtime_doc: str = "identity/protocol/IDENTITY_RUNTIME.md"
    issue_register_doc: str = "docs/workbook/protocol-issue-register-v1.6.md"
    workbook_doc: str = "docs/workbook/protocol-deep-audit-workbook-v1.6.md"
    governance_doc: str = "docs/governance/identity-v1.6x-release-closure-governance.md"
    review_doc: str = "docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"
    summary_doc: str = "docs/release/identity-v1.6x-release-closure-summary.md"


@dataclass(frozen=True)
class ReleaseClosureResolvedDocPaths:
    philosophy_path: Path
    protocol_path: Path
    runtime_path: Path
    issue_register_path: Path
    workbook_path: Path
    governance_path: Path
    review_path: Path
    summary_path: Path


RELEASE_CLOSURE_DOC_REL_PATHS = ReleaseClosureDocRelPaths()

_ISSUE_ROW_RE = re.compile(r"^\|\s*(ISSUE-(\d+))\b")
_STREAM_VERSION_RE = re.compile(r"\bv1\.6\.(\d+)\b")


def resolve_release_closure_doc_paths(repo_root: Path) -> ReleaseClosureResolvedDocPaths:
    return ReleaseClosureResolvedDocPaths(
        philosophy_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.philosophy_doc).resolve(),
        protocol_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.protocol_doc).resolve(),
        runtime_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.runtime_doc).resolve(),
        issue_register_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.issue_register_doc).resolve(),
        workbook_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.workbook_doc).resolve(),
        governance_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.governance_doc).resolve(),
        review_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.review_doc).resolve(),
        summary_path=(repo_root / RELEASE_CLOSURE_DOC_REL_PATHS.summary_doc).resolve(),
    )


def parse_release_closure_issue_register(text: str) -> tuple[str, list[str]]:
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
        match = _ISSUE_ROW_RE.match(f"| {issue_cell}")
        if match:
            max_issue_num = max(max_issue_num, int(match.group(2)))
        if status_cell == "CLOSED":
            version_match = _STREAM_VERSION_RE.search(stream_cell)
            if version_match:
                closed_versions.add(f"v1.6.{int(version_match.group(1))}")
    if max_issue_num <= 0:
        raise ValueError("issue_register_missing_issue_rows")
    highest_issue = f"ISSUE-{max_issue_num:03d}"
    ordered_versions = sorted(closed_versions, key=lambda token: int(token.split(".")[-1]))
    return highest_issue, ordered_versions


def contains_release_closure_issue_horizon(text: str, highest_issue: str) -> bool:
    pattern = rf"`ISSUE-001`\s+through\s+`{re.escape(highest_issue)}`"
    return re.search(pattern, text) is not None


def collect_release_closure_issue_horizon_targets(text: str) -> list[str]:
    pattern = re.compile(r"`ISSUE-001`\s+through\s+`(ISSUE-\d+)`")
    return [str(match.group(1)).strip() for match in pattern.finditer(text)]


def extract_release_closure_v16_versions(*texts: str) -> list[str]:
    versions: set[str] = set()
    for text in texts:
        for match in _STREAM_VERSION_RE.finditer(text):
            versions.add(f"v1.6.{int(match.group(1))}")
    return sorted(versions, key=lambda token: int(token.split(".")[-1]))

