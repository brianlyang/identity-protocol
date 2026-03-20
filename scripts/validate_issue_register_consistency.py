#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_DOC_DISCOVERY = "IP-IREG-001"
ERR_STATUS_TABLE = "IP-IREG-002"
ERR_AUDIT_STATUS = "IP-IREG-003"
ERR_HISTORICAL_BOUNDARY = "IP-IREG-004"
ERR_BOUNDARY_SECTION = "IP-IREG-005"
ERR_CHECKER_MISMATCH = "IP-IREG-006"

PLAN_DOC_GLOB = "*issue-remediation-plan.md"
AUDIT_DOC_GLOB = "*five-round-deep-audit.md"

ISSUE_ROW_RE = re.compile(r"^\|\s*(ISSUE-\d+)\b.*\|\s*([A-Z_]+)\s*\|")
ISSUE_HEADER_RE = re.compile(r"^###\s+(ISSUE-\d+)\b")
STATUS_LINE_RE = re.compile(r"^-\s+`status`:\s+([A-Z_]+)\s*$")
OPEN_REFERENCE_RE = re.compile(
    r"(ISSUE-\d+)(?:[^`\n]|`[^`]*`){0,80}\b(is opened|is open|remains open|is reopened|remains reopened)\b",
    flags=re.IGNORECASE,
)
HISTORICAL_MARKER_RE = re.compile(r"\bhistorical snapshot\b|\bprior round\b", flags=re.IGNORECASE)
DOCS_CHECKED_RE = re.compile(r"docs checked:\s*(\d+)", flags=re.IGNORECASE)
DOCS_SNIPPETS_RE = re.compile(r"command snippets checked:\s*(\d+)", flags=re.IGNORECASE)

SECTION_OPEN = "What remains intentionally open:"
SECTION_CLOSED = "What no longer remains open on this sheet:"


@dataclass(frozen=True)
class IssueReference:
    issue_id: str
    line_no: int
    text: str


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _discover_single_doc(root: Path, pattern: str) -> Path:
    matches = sorted((root / "activity" / "evidence").glob(f"*/{pattern}"))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one match for {pattern}, found {len(matches)}")
    return matches[0].resolve()


def _load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _parse_plan_issue_rows(lines: list[str]) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in lines:
        match = ISSUE_ROW_RE.match(line)
        if not match:
            continue
        rows[match.group(1)] = match.group(2)
    return rows


def _parse_audit_issue_statuses(lines: list[str]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    current_issue = ""
    for line in lines:
        header = ISSUE_HEADER_RE.match(line)
        if header:
            current_issue = header.group(1)
            continue
        if not current_issue:
            continue
        status_match = STATUS_LINE_RE.match(line.strip())
        if status_match:
            statuses[current_issue] = status_match.group(1)
            current_issue = ""
    return statuses


def _collect_open_references(lines: list[str]) -> list[IssueReference]:
    refs: list[IssueReference] = []
    for line_no, line in enumerate(lines, start=1):
        match = OPEN_REFERENCE_RE.search(line)
        if not match:
            continue
        refs.append(IssueReference(issue_id=match.group(1), line_no=line_no, text=line.strip()))
    return refs


def _extract_section_issue_refs(lines: list[str], heading: str) -> list[IssueReference]:
    refs: list[IssueReference] = []
    in_section = False
    for line_no, line in enumerate(lines, start=1):
        if line.strip() == heading:
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("## "):
            break
        if not line.strip():
            continue
        issue_ids = sorted(set(re.findall(r"ISSUE-\d+", line)))
        for issue_id in issue_ids:
            refs.append(IssueReference(issue_id=issue_id, line_no=line_no, text=line.strip()))
    return refs


def _run_docs_checker(repo_root: Path) -> tuple[int, int, str]:
    proc = subprocess.run(
        ["python3", "scripts/docs_command_contract_check.py"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{proc.stdout}\n{proc.stderr}".strip()
    if proc.returncode != 0:
        raise RuntimeError(f"docs checker failed with rc={proc.returncode}: {output}")
    docs_match = DOCS_CHECKED_RE.search(proc.stdout)
    snippet_match = DOCS_SNIPPETS_RE.search(proc.stdout)
    if not docs_match or not snippet_match:
        raise RuntimeError("cannot extract docs/snippet counts from docs checker output")
    return int(docs_match.group(1)), int(snippet_match.group(1)), proc.stdout.strip()


def _extract_doc_counts(text: str) -> tuple[int, int] | None:
    docs_match = DOCS_CHECKED_RE.search(text)
    snippet_match = DOCS_SNIPPETS_RE.search(text)
    if not docs_match or not snippet_match:
        return None
    return int(docs_match.group(1)), int(snippet_match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate issue register current-status vs historical-snapshot consistency.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--workspace-root", default="")
    parser.add_argument("--plan-doc", default="")
    parser.add_argument("--audit-doc", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    payload: dict[str, Any] = {
        "issue_register_consistency_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "plan_doc": "",
        "audit_doc": "",
        "plan_issue_statuses": {},
        "audit_issue_statuses": {},
        "plan_issue_count": 0,
        "audit_issue_count": 0,
        "historical_open_reference_count": 0,
        "open_rows_present": False,
        "docs_checker_counts": {},
        "doc_recorded_counts": {},
        "violations": [],
    }

    try:
        plan_doc = Path(args.plan_doc).expanduser().resolve() if args.plan_doc else _discover_single_doc(workspace_root, PLAN_DOC_GLOB)
        audit_doc = Path(args.audit_doc).expanduser().resolve() if args.audit_doc else _discover_single_doc(workspace_root, AUDIT_DOC_GLOB)
    except Exception as exc:
        payload["error_code"] = ERR_DOC_DISCOVERY
        payload["violations"] = [f"doc_discovery:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["plan_doc"] = str(plan_doc)
    payload["audit_doc"] = str(audit_doc)
    plan_lines = _load_lines(plan_doc)
    audit_lines = _load_lines(audit_doc)
    plan_text = "\n".join(plan_lines)
    audit_text = "\n".join(audit_lines)

    plan_statuses = _parse_plan_issue_rows(plan_lines)
    audit_statuses = _parse_audit_issue_statuses(audit_lines)
    payload["plan_issue_statuses"] = plan_statuses
    payload["audit_issue_statuses"] = audit_statuses
    payload["plan_issue_count"] = len(plan_statuses)
    payload["audit_issue_count"] = len(audit_statuses)

    violations: list[str] = []

    if not plan_statuses:
        violations.append("plan_issue_rows_missing")
    if not audit_statuses:
        violations.append("audit_issue_statuses_missing")

    for issue_id, plan_status in sorted(plan_statuses.items()):
        audit_status = audit_statuses.get(issue_id)
        if audit_status is None:
            violations.append(f"missing_audit_status:{issue_id}")
            continue
        if audit_status != plan_status:
            violations.append(f"status_mismatch:{issue_id}:plan={plan_status}:audit={audit_status}")

    open_rows = {issue_id: status for issue_id, status in plan_statuses.items() if status in {"OPEN", "REOPENED"}}
    payload["open_rows_present"] = bool(open_rows)

    open_refs = _collect_open_references(plan_lines)
    payload["historical_open_reference_count"] = len(open_refs)
    for ref in open_refs:
        current_status = plan_statuses.get(ref.issue_id, "")
        if current_status == "CLOSED" and not HISTORICAL_MARKER_RE.search(ref.text):
            violations.append(f"unqualified_historical_open_reference:{ref.issue_id}:line={ref.line_no}")

    for ref in _extract_section_issue_refs(plan_lines, SECTION_OPEN):
        current_status = plan_statuses.get(ref.issue_id, "")
        if current_status == "CLOSED":
            violations.append(f"closed_issue_listed_in_open_section:{ref.issue_id}:line={ref.line_no}")

    for ref in _extract_section_issue_refs(plan_lines, SECTION_CLOSED):
        current_status = plan_statuses.get(ref.issue_id, "")
        if current_status and current_status != "CLOSED":
            violations.append(f"non_closed_issue_listed_in_closed_section:{ref.issue_id}:line={ref.line_no}")

    try:
        docs_checked, snippets_checked, docs_output = _run_docs_checker(repo_root)
        payload["docs_checker_counts"] = {
            "docs_checked": docs_checked,
            "command_snippets_checked": snippets_checked,
            "raw_output": docs_output,
        }
    except Exception as exc:
        violations.append(f"docs_checker_execution:{exc}")
        docs_checked = -1
        snippets_checked = -1

    plan_counts = _extract_doc_counts(plan_text)
    audit_counts = _extract_doc_counts(audit_text)
    payload["doc_recorded_counts"] = {
        "plan_doc": {
            "docs_checked": plan_counts[0] if plan_counts else None,
            "command_snippets_checked": plan_counts[1] if plan_counts else None,
        },
        "audit_doc": {
            "docs_checked": audit_counts[0] if audit_counts else None,
            "command_snippets_checked": audit_counts[1] if audit_counts else None,
        },
    }
    if plan_counts is None:
        violations.append("plan_doc_missing_docs_checker_counts")
    elif (docs_checked, snippets_checked) != plan_counts:
        violations.append(
            "plan_doc_docs_checker_count_mismatch:"
            f"expected={docs_checked}/{snippets_checked}:recorded={plan_counts[0]}/{plan_counts[1]}"
        )
    if audit_counts is None:
        violations.append("audit_doc_missing_docs_checker_counts")
    elif (docs_checked, snippets_checked) != audit_counts:
        violations.append(
            "audit_doc_docs_checker_count_mismatch:"
            f"expected={docs_checked}/{snippets_checked}:recorded={audit_counts[0]}/{audit_counts[1]}"
        )

    payload["violations"] = violations
    if violations:
        payload["error_code"] = (
            ERR_DOC_DISCOVERY
            if any(item.startswith("doc_discovery:") for item in violations)
            else ERR_CHECKER_MISMATCH
            if any("docs_checker" in item for item in violations)
            else ERR_BOUNDARY_SECTION
            if any("section" in item for item in violations)
            else ERR_HISTORICAL_BOUNDARY
            if any("historical_open_reference" in item for item in violations)
            else ERR_AUDIT_STATUS
            if any("missing_audit_status" in item or "status_mismatch" in item for item in violations)
            else ERR_STATUS_TABLE
        )
        _emit(payload, json_only=args.json_only)
        return 1

    payload["issue_register_consistency_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
