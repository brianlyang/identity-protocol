#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_DOC_DISCOVERY = "IP-IREG-001"
ERR_STATUS_TABLE = "IP-IREG-002"
ERR_AUDIT_STATUS = "IP-IREG-003"
ERR_HISTORICAL_BOUNDARY = "IP-IREG-004"
ERR_BOUNDARY_SECTION = "IP-IREG-005"
ERR_CHECKER_MISMATCH = "IP-IREG-006"
ERR_WORKBOOK_REGISTRY = "IP-IREG-007"
ERR_WORKBOOK_BOUNDARY = "IP-IREG-008"
ERR_STREAM_DOC_REGISTRY = "IP-IREG-009"

WORKBOOK_REGISTRY_CURRENT = "identity/protocol/mappings/workbook-registry.current.yaml"
STREAM_DOC_REGISTRY_CURRENT = "identity/protocol/mappings/stream-doc-registry.current.yaml"
WORKBOOK_CANONICAL_DIR = "docs/workbook"
WORKBOOK_README = "docs/workbook/README.md"

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
ISSUE_REGISTER_COUNT_RE = re.compile(r"issue_register_issue_count=(\d+)", flags=re.IGNORECASE)
DEEP_AUDIT_COUNT_RE = re.compile(r"deep_audit_workbook_issue_count=(\d+)", flags=re.IGNORECASE)
PROJECTION_FORBIDDEN_HEADER_RE = re.compile(
    r"\bauthoritative current status\b|\bauthoritative current machine snapshot\b|\bthis file is the authoritative\b",
    flags=re.IGNORECASE,
)

SECTION_OPEN = "What remains intentionally open:"
SECTION_CLOSED = "What no longer remains open on this sheet:"
PROJECTION_MODE_MARKER = "Projection mode: mirror-only"
PROJECTION_BOUNDARY_MARKER = "Authority boundary: this file is projection-only"
PROJECTION_FRESHNESS_BOUNDARY_ONLY = "boundary_markers_only"
PROJECTION_FRESHNESS_PARITY_REQUIRED = "summary_snapshot_parity_required"
ALLOWED_PROJECTION_FRESHNESS_MODES = {
    PROJECTION_FRESHNESS_BOUNDARY_ONLY,
    PROJECTION_FRESHNESS_PARITY_REQUIRED,
}


@dataclass(frozen=True)
class IssueReference:
    issue_id: str
    line_no: int
    text: str


@dataclass(frozen=True)
class ProjectionExport:
    projection_role: str
    path: Path
    path_rel: str
    authority_doc: Path
    authority_doc_rel: str
    presence_policy: str
    freshness_mode: str


@dataclass(frozen=True)
class WorkbookFamily:
    registry_path: Path
    workbook_family: str
    minor_family_uniqueness_mode: str
    template_static_docs: tuple[str, ...]
    governance_doc: Path
    issue_register_doc: Path
    deep_audit_workbook_doc: Path
    projection_exports: tuple[ProjectionExport, ...]


@dataclass(frozen=True)
class StreamDocRegistry:
    current_path: Path
    versioned_path: Path
    version: str
    mandatory_static_docs: tuple[str, ...]


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _resolve_family_doc_path(family: dict[str, Any], key: str) -> str:
    authority_surfaces = family.get("authority_surfaces")
    if isinstance(authority_surfaces, dict):
        nested_value = str(authority_surfaces.get(key, "")).strip()
        if nested_value:
            return nested_value
    return str(family.get(key, "")).strip()


def _extract_template_static_docs(registry_doc: dict[str, Any]) -> tuple[str, ...]:
    template_contract = registry_doc.get("template_contract")
    if not isinstance(template_contract, dict):
        return ()
    template_paths = []
    for key in ("templates_readme", "issue_register_template", "deep_audit_template"):
        path_rel = str(template_contract.get(key, "")).strip()
        if path_rel:
            template_paths.append(path_rel)
    return tuple(sorted(set(template_paths)))


def _discover_workbook_family(repo_root: Path, workspace_root: Path) -> WorkbookFamily:
    current_path = (repo_root / WORKBOOK_REGISTRY_CURRENT).resolve()
    if not current_path.exists():
        raise ValueError(f"missing workbook registry current pointer: {current_path}")
    current_doc = _load_yaml(current_path)
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        raise ValueError(f"workbook registry current pointer missing active_file: {current_path}")
    registry_path = (repo_root / active_file).resolve()
    if not registry_path.exists():
        raise ValueError(f"missing workbook registry versioned file: {registry_path}")
    registry_doc = _load_yaml(registry_path)
    family = registry_doc.get("active_workbook_family")
    if not isinstance(family, dict):
        raise ValueError(f"active_workbook_family missing: {registry_path}")
    workbook_family = str(family.get("workbook_family", "")).strip()
    if not workbook_family:
        raise ValueError(f"workbook_family missing: {registry_path}")
    minor_family_uniqueness_mode = str(family.get("minor_family_uniqueness_mode", "")).strip() or "exact_canonical_pair_only"
    governance_doc = str(family.get("governance_doc", "")).strip()
    issue_register_doc = _resolve_family_doc_path(family, "issue_register_doc")
    deep_audit_doc = _resolve_family_doc_path(family, "deep_audit_workbook_doc")
    if not governance_doc or not issue_register_doc or not deep_audit_doc:
        raise ValueError(f"workbook registry missing workbook doc paths: {registry_path}")
    projection_rows = family.get("projection_exports") or []
    if not isinstance(projection_rows, list):
        raise ValueError(f"projection_exports must be list: {registry_path}")
    projection_exports: list[ProjectionExport] = []
    for row in projection_rows:
        if not isinstance(row, dict):
            raise ValueError(f"projection_export row must be mapping: {registry_path}")
        path_rel = str(row.get("path", "")).strip()
        authority_doc_rel = str(row.get("authority_doc", "")).strip()
        if not path_rel or not authority_doc_rel:
            raise ValueError(f"projection_export missing path/authority_doc: {registry_path}")
        projection_exports.append(
            ProjectionExport(
                projection_role=str(row.get("projection_role", "")).strip() or "projection",
                path=(workspace_root / path_rel).resolve(),
                path_rel=path_rel,
                authority_doc=(repo_root / authority_doc_rel).resolve(),
                authority_doc_rel=authority_doc_rel,
                presence_policy=str(row.get("presence_policy", "")).strip() or "optional_projection",
                freshness_mode=str(row.get("freshness_mode", "")).strip() or "unspecified",
            )
        )
    return WorkbookFamily(
        registry_path=registry_path,
        workbook_family=workbook_family,
        minor_family_uniqueness_mode=minor_family_uniqueness_mode,
        template_static_docs=_extract_template_static_docs(registry_doc),
        governance_doc=(repo_root / governance_doc).resolve(),
        issue_register_doc=(repo_root / issue_register_doc).resolve(),
        deep_audit_workbook_doc=(repo_root / deep_audit_doc).resolve(),
        projection_exports=tuple(projection_exports),
    )


def _discover_stream_doc_registry(repo_root: Path) -> StreamDocRegistry:
    current_path = (repo_root / STREAM_DOC_REGISTRY_CURRENT).resolve()
    if not current_path.exists():
        raise ValueError(f"missing stream doc registry current pointer: {current_path}")
    current_doc = _load_yaml(current_path)
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        raise ValueError(f"stream doc registry current pointer missing active_file: {current_path}")
    versioned_path = (repo_root / active_file).resolve()
    if not versioned_path.exists():
        raise ValueError(f"missing stream doc registry versioned file: {versioned_path}")
    versioned_doc = _load_yaml(versioned_path)
    version = str(versioned_doc.get("version", "")).strip()
    if not version:
        raise ValueError(f"stream doc registry missing version: {versioned_path}")
    mandatory_static_docs_raw = versioned_doc.get("mandatory_static_docs") or []
    if not isinstance(mandatory_static_docs_raw, list):
        raise ValueError(f"mandatory_static_docs must be list: {versioned_path}")
    mandatory_static_docs = tuple(str(item).strip() for item in mandatory_static_docs_raw if str(item).strip())
    return StreamDocRegistry(
        current_path=current_path,
        versioned_path=versioned_path,
        version=version,
        mandatory_static_docs=mandatory_static_docs,
    )


def _ensure_protocol_workbook_boundary(repo_root: Path, path: Path) -> None:
    docs_root = (repo_root / WORKBOOK_CANONICAL_DIR).resolve()
    path_resolved = path.resolve()
    if not docs_root.exists():
        raise ValueError(f"canonical workbook directory missing: {docs_root}")
    if docs_root not in path_resolved.parents:
        raise ValueError(f"workbook doc outside canonical directory: {path_resolved}")


def _load_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _parse_issue_register_rows(lines: list[str]) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in lines:
        match = ISSUE_ROW_RE.match(line)
        if not match:
            continue
        rows[match.group(1)] = match.group(2)
    return rows


def _parse_deep_audit_workbook_statuses(lines: list[str]) -> dict[str, str]:
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


def _path_rel(repo_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(repo_root))


def _is_active_family_workbook_doc(path: Path, *, workbook_family: str) -> bool:
    family_token_re = re.compile(rf"(^|[^0-9]){re.escape(workbook_family)}([^0-9]|$)")
    if family_token_re.search(path.stem):
        return True
    header = "\n".join(_load_lines(path)[:20])
    if not family_token_re.search(header):
        return False
    authority_markers = (
        "Authority boundary:",
        "Issue Register",
        "Deep Audit Workbook",
        "workbook family",
    )
    return any(marker in header for marker in authority_markers)


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


def _extract_projection_issue_counts(text: str) -> tuple[int, int] | None:
    issue_register_match = ISSUE_REGISTER_COUNT_RE.search(text)
    deep_audit_match = DEEP_AUDIT_COUNT_RE.search(text)
    if not issue_register_match or not deep_audit_match:
        return None
    return int(issue_register_match.group(1)), int(deep_audit_match.group(1))


def _workspace_protocol_rel(repo_root: Path, relative_path: str) -> str:
    return str(Path(repo_root.name) / Path(relative_path))


def _serialize_projection_export(export: ProjectionExport) -> dict[str, Any]:
    return {
        "projection_role": export.projection_role,
        "path": str(export.path),
        "path_rel": export.path_rel,
        "authority_doc": str(export.authority_doc),
        "authority_doc_rel": export.authority_doc_rel,
        "presence_policy": export.presence_policy,
        "freshness_mode": export.freshness_mode,
    }


def _validate_historical_boundary_surface(
    *,
    surface_key: str,
    lines: list[str],
    current_statuses: dict[str, str],
) -> tuple[dict[str, Any], list[str]]:
    violations: list[str] = []
    open_refs = _collect_open_references(lines)
    for ref in open_refs:
        current_status = current_statuses.get(ref.issue_id, "")
        if current_status == "CLOSED" and not HISTORICAL_MARKER_RE.search(ref.text):
            violations.append(
                f"unqualified_historical_open_reference:{surface_key}:{ref.issue_id}:line={ref.line_no}"
            )

    open_section_refs = _extract_section_issue_refs(lines, SECTION_OPEN)
    for ref in open_section_refs:
        current_status = current_statuses.get(ref.issue_id, "")
        if current_status == "CLOSED":
            violations.append(f"closed_issue_listed_in_open_section:{surface_key}:{ref.issue_id}:line={ref.line_no}")

    closed_section_refs = _extract_section_issue_refs(lines, SECTION_CLOSED)
    for ref in closed_section_refs:
        current_status = current_statuses.get(ref.issue_id, "")
        if current_status and current_status != "CLOSED":
            violations.append(
                f"non_closed_issue_listed_in_closed_section:{surface_key}:{ref.issue_id}:line={ref.line_no}"
            )

    return (
        {
            "historical_open_reference_count": len(open_refs),
            "open_section_issue_count": len(open_section_refs),
            "closed_section_issue_count": len(closed_section_refs),
        },
        violations,
    )


def _validate_minor_family_uniqueness(
    *,
    repo_root: Path,
    workbook_family: str,
    issue_register_doc: Path,
    deep_audit_workbook_doc: Path,
) -> tuple[dict[str, Any], list[str]]:
    docs_root = (repo_root / WORKBOOK_CANONICAL_DIR).resolve()
    canonical_docs = {
        issue_register_doc.resolve(),
        deep_audit_workbook_doc.resolve(),
    }
    family_docs = sorted(
        path.resolve()
        for path in docs_root.glob("*.md")
        if path.name != Path(WORKBOOK_README).name and _is_active_family_workbook_doc(path, workbook_family=workbook_family)
    )
    family_doc_rel = [_path_rel(repo_root, path) for path in family_docs]
    extra_docs = [path for path in family_docs if path not in canonical_docs]
    missing_docs = [path for path in canonical_docs if path not in family_docs]
    violations: list[str] = []
    for path in extra_docs:
        violations.append(f"minor_family_uniqueness_extra_doc:{workbook_family}:{_path_rel(repo_root, path)}")
    for path in missing_docs:
        violations.append(f"minor_family_uniqueness_missing_doc:{workbook_family}:{_path_rel(repo_root, path)}")
    if len(family_docs) != len(canonical_docs):
        violations.append(
            f"minor_family_uniqueness_count_mismatch:{workbook_family}:expected={len(canonical_docs)}:found={len(family_docs)}"
        )
    return (
        {
            "workbook_family": workbook_family,
            "family_docs": family_doc_rel,
            "canonical_docs": sorted(_path_rel(repo_root, path) for path in canonical_docs),
        },
        violations,
    )


def _validate_stream_doc_registry_binding(
    *,
    repo_root: Path,
    workbook_family: str,
    workbook_registry_path: Path,
    template_static_docs: tuple[str, ...],
    governance_doc: Path,
    issue_register_doc: Path,
    deep_audit_workbook_doc: Path,
) -> tuple[dict[str, Any], list[str]]:
    stream_registry = _discover_stream_doc_registry(repo_root)
    expected_static_docs = {
        WORKBOOK_README,
        WORKBOOK_REGISTRY_CURRENT,
        _path_rel(repo_root, workbook_registry_path),
        _path_rel(repo_root, governance_doc),
        _path_rel(repo_root, issue_register_doc),
        _path_rel(repo_root, deep_audit_workbook_doc),
    }
    expected_static_docs.update(template_static_docs)
    recorded_static_docs = set(stream_registry.mandatory_static_docs)
    missing_static_docs = sorted(expected_static_docs - recorded_static_docs)
    violations: list[str] = []
    if stream_registry.version != workbook_family:
        violations.append(
            f"stream_doc_registry_version_mismatch:expected={workbook_family}:recorded={stream_registry.version}"
        )
    for path_rel in missing_static_docs:
        violations.append(f"stream_doc_registry_missing_static_doc:{path_rel}")
    return (
        {
            "current_path": str(stream_registry.current_path),
            "versioned_path": str(stream_registry.versioned_path),
            "version": stream_registry.version,
            "expected_static_docs": sorted(expected_static_docs),
            "missing_static_docs": missing_static_docs,
        },
        violations,
    )


def _validate_projection_export(
    export: ProjectionExport,
    repo_root: Path,
    *,
    expected_issue_register_count: int,
    expected_deep_audit_issue_count: int,
    expected_docs_checked: int,
    expected_snippets_checked: int,
) -> tuple[dict[str, Any], list[str]]:
    result = {
        "projection_role": export.projection_role,
        "path": str(export.path),
        "path_rel": export.path_rel,
        "authority_doc": str(export.authority_doc),
        "authority_doc_rel": export.authority_doc_rel,
        "presence_policy": export.presence_policy,
        "freshness_mode": export.freshness_mode,
        "exists": export.path.exists(),
    }
    violations: list[str] = []
    if export.freshness_mode not in ALLOWED_PROJECTION_FRESHNESS_MODES:
        violations.append(f"projection_unknown_freshness_mode:{export.projection_role}:{export.freshness_mode}")
    if not export.path.exists():
        if export.presence_policy != "optional_projection":
            violations.append(f"missing_required_projection_doc:{export.projection_role}")
        return result, violations
    if repo_root in export.path.parents:
        violations.append(f"projection_doc_inside_protocol_repo:{export.projection_role}")
    text = export.path.read_text(encoding="utf-8")
    header_text = "\n".join(text.splitlines()[:40])
    required_markers = [
        PROJECTION_MODE_MARKER,
        f"Projection source: `{_workspace_protocol_rel(repo_root, export.authority_doc_rel)}`",
        f"Workbook registry source: `{_workspace_protocol_rel(repo_root, WORKBOOK_REGISTRY_CURRENT)}`",
        PROJECTION_BOUNDARY_MARKER,
    ]
    for marker in required_markers:
        if marker not in text:
            violations.append(f"projection_marker_missing:{export.projection_role}:{marker}")
    if PROJECTION_FORBIDDEN_HEADER_RE.search(header_text):
        violations.append(f"projection_authority_claim:{export.projection_role}")
    projection_counts = _extract_projection_issue_counts(text)
    docs_counts = _extract_doc_counts(text)
    result["recorded_issue_counts"] = (
        {
            "issue_register_issue_count": projection_counts[0],
            "deep_audit_workbook_issue_count": projection_counts[1],
        }
        if projection_counts
        else None
    )
    result["recorded_docs_checker_counts"] = (
        {
            "docs_checked": docs_counts[0],
            "command_snippets_checked": docs_counts[1],
        }
        if docs_counts
        else None
    )
    if export.freshness_mode == PROJECTION_FRESHNESS_PARITY_REQUIRED:
        if projection_counts is None:
            violations.append(f"projection_freshness_missing_issue_counts:{export.projection_role}")
        elif projection_counts != (expected_issue_register_count, expected_deep_audit_issue_count):
            violations.append(
                "projection_freshness_issue_count_mismatch:"
                f"{export.projection_role}:expected={expected_issue_register_count}/{expected_deep_audit_issue_count}:"
                f"recorded={projection_counts[0]}/{projection_counts[1]}"
            )
        if docs_counts is None:
            violations.append(f"projection_freshness_missing_docs_checker_counts:{export.projection_role}")
        elif docs_counts != (expected_docs_checked, expected_snippets_checked):
            violations.append(
                "projection_freshness_docs_checker_mismatch:"
                f"{export.projection_role}:expected={expected_docs_checked}/{expected_snippets_checked}:"
                f"recorded={docs_counts[0]}/{docs_counts[1]}"
            )
    return result, violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate issue register current-status vs historical-snapshot consistency.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--workspace-root", default="")
    parser.add_argument("--issue-register-doc", dest="issue_register_doc", default="")
    parser.add_argument("--deep-audit-workbook-doc", dest="deep_audit_workbook_doc", default="")
    parser.add_argument("--plan-doc", dest="legacy_plan_doc", default="", help=argparse.SUPPRESS)
    parser.add_argument("--audit-doc", dest="legacy_audit_doc", default="", help=argparse.SUPPRESS)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    payload: dict[str, Any] = {
        "issue_register_consistency_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "workbook_registry": "",
        "stream_doc_registry": {},
        "governance_doc": "",
        "issue_register_doc": "",
        "deep_audit_workbook_doc": "",
        "projection_exports": [],
        "historical_boundary_checks": {},
        "minor_family_uniqueness": {},
        "issue_register_statuses": {},
        "deep_audit_workbook_statuses": {},
        "issue_register_issue_count": 0,
        "deep_audit_workbook_issue_count": 0,
        "historical_open_reference_count": 0,
        "open_rows_present": False,
        "docs_checker_counts": {},
        "doc_recorded_counts": {},
        "violations": [],
    }

    try:
        issue_register_override = str(args.issue_register_doc or args.legacy_plan_doc or "").strip()
        deep_audit_override = str(args.deep_audit_workbook_doc or args.legacy_audit_doc or "").strip()
        projection_exports: tuple[ProjectionExport, ...] = ()
        if issue_register_override or deep_audit_override:
            if not issue_register_override or not deep_audit_override:
                raise ValueError("issue-register-doc and deep-audit-workbook-doc must be provided together")
            workbook_registry = ""
            workbook_family = ""
            minor_family_uniqueness_mode = ""
            governance_doc = Path()
            issue_register_doc = Path(issue_register_override).expanduser().resolve()
            deep_audit_workbook_doc = Path(deep_audit_override).expanduser().resolve()
        else:
            family = _discover_workbook_family(repo_root, workspace_root)
            workbook_registry = str(family.registry_path)
            workbook_family = family.workbook_family
            minor_family_uniqueness_mode = family.minor_family_uniqueness_mode
            governance_doc = family.governance_doc
            issue_register_doc = family.issue_register_doc
            deep_audit_workbook_doc = family.deep_audit_workbook_doc
            projection_exports = family.projection_exports
        _ensure_protocol_workbook_boundary(repo_root, issue_register_doc)
        _ensure_protocol_workbook_boundary(repo_root, deep_audit_workbook_doc)
    except Exception as exc:
        payload["error_code"] = ERR_WORKBOOK_REGISTRY
        payload["violations"] = [f"doc_discovery:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["workbook_registry"] = workbook_registry
    payload["governance_doc"] = str(governance_doc) if governance_doc else ""
    payload["issue_register_doc"] = str(issue_register_doc)
    payload["deep_audit_workbook_doc"] = str(deep_audit_workbook_doc)
    payload["projection_exports"] = [_serialize_projection_export(export) for export in projection_exports]
    issue_register_lines = _load_lines(issue_register_doc)
    deep_audit_workbook_lines = _load_lines(deep_audit_workbook_doc)
    issue_register_text = "\n".join(issue_register_lines)
    deep_audit_workbook_text = "\n".join(deep_audit_workbook_lines)

    issue_register_statuses = _parse_issue_register_rows(issue_register_lines)
    deep_audit_workbook_statuses = _parse_deep_audit_workbook_statuses(deep_audit_workbook_lines)
    payload["issue_register_statuses"] = issue_register_statuses
    payload["deep_audit_workbook_statuses"] = deep_audit_workbook_statuses
    payload["issue_register_issue_count"] = len(issue_register_statuses)
    payload["deep_audit_workbook_issue_count"] = len(deep_audit_workbook_statuses)

    violations: list[str] = []

    if not issue_register_statuses:
        violations.append("issue_register_rows_missing")
    if not deep_audit_workbook_statuses:
        violations.append("deep_audit_workbook_statuses_missing")

    for issue_id, issue_register_status in sorted(issue_register_statuses.items()):
        deep_audit_workbook_status = deep_audit_workbook_statuses.get(issue_id)
        if deep_audit_workbook_status is None:
            violations.append(f"missing_deep_audit_workbook_status:{issue_id}")
            continue
        if deep_audit_workbook_status != issue_register_status:
            violations.append(
                f"status_mismatch:{issue_id}:issue_register={issue_register_status}:deep_audit_workbook={deep_audit_workbook_status}"
            )

    open_rows = {issue_id: status for issue_id, status in issue_register_statuses.items() if status in {"OPEN", "REOPENED"}}
    payload["open_rows_present"] = bool(open_rows)
    issue_register_boundary, issue_register_boundary_violations = _validate_historical_boundary_surface(
        surface_key="issue_register_doc",
        lines=issue_register_lines,
        current_statuses=issue_register_statuses,
    )
    deep_audit_boundary, deep_audit_boundary_violations = _validate_historical_boundary_surface(
        surface_key="deep_audit_workbook_doc",
        lines=deep_audit_workbook_lines,
        current_statuses=issue_register_statuses,
    )
    payload["historical_boundary_checks"] = {
        "issue_register_doc": issue_register_boundary,
        "deep_audit_workbook_doc": deep_audit_boundary,
    }
    payload["historical_open_reference_count"] = (
        issue_register_boundary["historical_open_reference_count"]
        + deep_audit_boundary["historical_open_reference_count"]
    )
    violations.extend(issue_register_boundary_violations)
    violations.extend(deep_audit_boundary_violations)

    if workbook_family and minor_family_uniqueness_mode == "exact_canonical_pair_only":
        minor_family_uniqueness, uniqueness_violations = _validate_minor_family_uniqueness(
            repo_root=repo_root,
            workbook_family=workbook_family,
            issue_register_doc=issue_register_doc,
            deep_audit_workbook_doc=deep_audit_workbook_doc,
        )
        payload["minor_family_uniqueness"] = minor_family_uniqueness
        violations.extend(uniqueness_violations)
        stream_doc_registry, stream_doc_registry_violations = _validate_stream_doc_registry_binding(
            repo_root=repo_root,
            workbook_family=workbook_family,
            workbook_registry_path=Path(workbook_registry),
            template_static_docs=family.template_static_docs,
            governance_doc=governance_doc,
            issue_register_doc=issue_register_doc,
            deep_audit_workbook_doc=deep_audit_workbook_doc,
        )
        payload["stream_doc_registry"] = stream_doc_registry
        violations.extend(stream_doc_registry_violations)

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

    issue_register_counts = _extract_doc_counts(issue_register_text)
    deep_audit_workbook_counts = _extract_doc_counts(deep_audit_workbook_text)
    payload["doc_recorded_counts"] = {
        "issue_register_doc": {
            "docs_checked": issue_register_counts[0] if issue_register_counts else None,
            "command_snippets_checked": issue_register_counts[1] if issue_register_counts else None,
        },
        "deep_audit_workbook_doc": {
            "docs_checked": deep_audit_workbook_counts[0] if deep_audit_workbook_counts else None,
            "command_snippets_checked": deep_audit_workbook_counts[1] if deep_audit_workbook_counts else None,
        },
    }
    if issue_register_counts is None:
        violations.append("issue_register_doc_missing_docs_checker_counts")
    elif (docs_checked, snippets_checked) != issue_register_counts:
        violations.append(
            "issue_register_doc_docs_checker_count_mismatch:"
            f"expected={docs_checked}/{snippets_checked}:recorded={issue_register_counts[0]}/{issue_register_counts[1]}"
        )
    if deep_audit_workbook_counts is None:
        violations.append("deep_audit_workbook_doc_missing_docs_checker_counts")
    elif (docs_checked, snippets_checked) != deep_audit_workbook_counts:
        violations.append(
            "deep_audit_workbook_doc_docs_checker_count_mismatch:"
            f"expected={docs_checked}/{snippets_checked}:recorded={deep_audit_workbook_counts[0]}/{deep_audit_workbook_counts[1]}"
        )

    projection_results: list[dict[str, Any]] = []
    for export in projection_exports:
        projection_result, projection_violations = _validate_projection_export(
            export,
            repo_root,
            expected_issue_register_count=len(issue_register_statuses),
            expected_deep_audit_issue_count=len(deep_audit_workbook_statuses),
            expected_docs_checked=docs_checked,
            expected_snippets_checked=snippets_checked,
        )
        projection_results.append(projection_result)
        violations.extend(projection_violations)
    if projection_results:
        payload["projection_exports"] = projection_results

    payload["violations"] = violations
    if violations:
        payload["error_code"] = (
            ERR_STREAM_DOC_REGISTRY
            if any(item.startswith("stream_doc_registry_") for item in violations)
            else ERR_WORKBOOK_REGISTRY
            if any(item.startswith("doc_discovery:") for item in violations)
            else ERR_WORKBOOK_BOUNDARY
            if any(
                "canonical directory" in item
                or "outside canonical directory" in item
                or item.startswith("minor_family_uniqueness")
                or item.startswith("projection_")
                or item.startswith("missing_required_projection_doc")
                for item in violations
            )
            else ERR_CHECKER_MISMATCH
            if any("docs_checker" in item for item in violations)
            else ERR_BOUNDARY_SECTION
            if any("section" in item for item in violations)
            else ERR_HISTORICAL_BOUNDARY
            if any("historical_open_reference" in item for item in violations)
            else ERR_AUDIT_STATUS
            if any("missing_deep_audit_workbook_status" in item or "status_mismatch" in item for item in violations)
            else ERR_STATUS_TABLE
        )
        _emit(payload, json_only=args.json_only)
        return 1

    payload["issue_register_consistency_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
