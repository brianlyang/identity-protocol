#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from workbook_control_plane_common import load_active_workbook_registry, resolve_workbook_roots

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_DISCOVERY = "IP-WFPR-001"
ERR_SNAPSHOT = "IP-WFPR-002"
ERR_RENDER = "IP-WFPR-003"
REPO_DISPLAY_NAME = "identity-protocol-local"
DOCS_COUNT_RE = re.compile(r"docs checked:\s*(\d+)", re.IGNORECASE)
SNIPPETS_COUNT_RE = re.compile(r"command snippets checked:\s*(\d+)", re.IGNORECASE)


def _run_command(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _run_json_command(cmd: list[str], *, cwd: Path) -> tuple[int, dict[str, Any]]:
    proc = _run_command(cmd, cwd=cwd)
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError(f"json_command_empty_stdout:rc={proc.returncode}:{' '.join(cmd)}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"json_command_parse_failed:rc={proc.returncode}:{' '.join(cmd)}:{exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"json_command_root_not_object:{' '.join(cmd)}")
    return proc.returncode, payload


def _issue_snapshot(*, repo_root: Path, workspace_root: Path) -> dict[str, Any]:
    validator = (repo_root / "scripts/validate_issue_register_consistency.py").resolve()
    rc, payload = _run_json_command(
        [
            "python3",
            str(validator),
            "--repo-root",
            str(repo_root),
            "--workspace-root",
            str(workspace_root),
            "--json-only",
        ],
        cwd=repo_root,
    )
    return {
        "command": "python3 identity-protocol-local/scripts/validate_issue_register_consistency.py --json-only",
        "rc": rc,
        "status": str(payload.get("issue_register_consistency_status", "")).strip()
        or (STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED),
        "issue_register_issue_count": payload.get("issue_register_issue_count"),
        "deep_audit_workbook_issue_count": payload.get("deep_audit_workbook_issue_count"),
        "open_rows_present": bool(payload.get("open_rows_present", False)),
        "error_code": str(payload.get("error_code", "")).strip(),
        "violations": [str(item) for item in (payload.get("violations") or [])],
    }


def _docs_checker_snapshot(*, repo_root: Path) -> dict[str, Any]:
    checker = (repo_root / "scripts/docs_command_contract_check.py").resolve()
    proc = _run_command(["python3", str(checker)], cwd=repo_root)
    combined = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part).strip()
    docs_match = DOCS_COUNT_RE.search(combined)
    snippets_match = SNIPPETS_COUNT_RE.search(combined)
    upper = combined.upper()
    if "PASS" in upper and "FAIL" not in upper:
        status = "PASS"
    elif "FAIL" in upper or proc.returncode != 0:
        status = "FAIL"
    else:
        status = STATUS_PASS_REQUIRED if proc.returncode == 0 else STATUS_FAIL_REQUIRED
    return {
        "command": "python3 identity-protocol-local/scripts/docs_command_contract_check.py",
        "rc": proc.returncode,
        "status": status,
        "docs_checked": int(docs_match.group(1)) if docs_match else None,
        "command_snippets_checked": int(snippets_match.group(1)) if snippets_match else None,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _role_title(minor: str, role: str) -> str:
    if role == "issue_register_projection":
        return f"Identity Protocol {minor} Issue Register Projection"
    if role == "deep_audit_projection":
        return f"Identity Protocol {minor} Deep Audit Workbook Projection"
    return f"Identity Protocol {minor} Workbook Projection"


def _role_scope(minor: str, role: str) -> str:
    if role == "issue_register_projection":
        return f"mirrored operator-facing snapshot for the active `{minor}` workbook family"
    if role == "deep_audit_projection":
        return f"mirrored operator-facing snapshot for the active `{minor}` deep-audit workbook"
    return f"mirrored operator-facing snapshot for the active `{minor}` workbook control plane"


def _authority_boundary(role: str) -> str:
    if role == "issue_register_projection":
        return (
            "Authority boundary: this file is projection-only and never authoritative for protocol workbook truth. "
            "Update the canonical workbook family inside `identity-protocol-local/docs/workbook/` first; this mirror "
            "may be deleted without changing protocol truth."
        )
    return (
        "Authority boundary: this file is projection-only and never authoritative for protocol workbook truth. "
        "Intake routing, root-cause grouping, and current status authority remain inside the protocol-internal "
        "workbook control plane; this mirror may be deleted without changing protocol truth."
    )


def _canonical_sources(role: str, *, issue_register_doc: str, deep_audit_doc: str, governance_doc: str) -> list[str]:
    if role == "issue_register_projection":
        return [
            f"- issue register authority: `{REPO_DISPLAY_NAME}/{issue_register_doc}`",
            f"- deep-audit routing authority: `{REPO_DISPLAY_NAME}/{deep_audit_doc}`",
            f"- workbook governance contract: `{REPO_DISPLAY_NAME}/{governance_doc}`",
        ]
    return [
        f"- deep-audit routing authority: `{REPO_DISPLAY_NAME}/{deep_audit_doc}`",
        f"- issue register authority: `{REPO_DISPLAY_NAME}/{issue_register_doc}`",
        f"- workbook governance contract: `{REPO_DISPLAY_NAME}/{governance_doc}`",
    ]


def _handling_rules(role: str) -> list[str]:
    if role == "issue_register_projection":
        return [
            "1. Do not edit issue statuses here.",
            "2. Do not use this file as validator or release-gate input.",
            "3. Refresh the protocol-internal workbook family first, then update or regenerate this projection if an outer mirror is still desired.",
        ]
    return [
        "1. Do not record new issue authority here.",
        "2. Do not use this file as validator or release-gate input.",
        "3. Refresh the protocol-internal workbook family first, then update or regenerate this projection if an outer mirror is still desired.",
    ]


def _render_projection_text(
    *,
    minor: str,
    role: str,
    authority_doc_rel: str,
    issue_register_doc_rel: str,
    deep_audit_doc_rel: str,
    governance_doc_rel: str,
    registry_current_ref: str,
    renderer_rel: str,
    issue_snapshot: dict[str, Any],
    docs_snapshot: dict[str, Any],
    rendered_date: str,
) -> str:
    issue_count = issue_snapshot.get("issue_register_issue_count")
    deep_count = issue_snapshot.get("deep_audit_workbook_issue_count")
    open_rows_present = str(bool(issue_snapshot.get("open_rows_present", False))).lower()
    docs_checked = docs_snapshot.get("docs_checked")
    snippets_checked = docs_snapshot.get("command_snippets_checked")
    lines = [
        f"# {_role_title(minor, role)}",
        "",
        f"Date: {rendered_date}",
        "Status: Workspace projection only",
        "Layer: projection",
        f"Scope: {_role_scope(minor, role)}",
        "Projection mode: mirror-only",
        f"Projection source: `{REPO_DISPLAY_NAME}/{authority_doc_rel}`",
        f"Workbook registry source: `{REPO_DISPLAY_NAME}/{registry_current_ref}`",
        f"Projection renderer: `{REPO_DISPLAY_NAME}/{renderer_rel}`",
        _authority_boundary(role),
        "",
        "## Current mirrored snapshot",
        "",
        f"- `{issue_snapshot['command']}` -> `{issue_snapshot['status']}`",
        f"  - `issue_register_issue_count={issue_count}`",
        f"  - `deep_audit_workbook_issue_count={deep_count}`",
        f"  - `open_rows_present={open_rows_present}`",
        f"- `{docs_snapshot['command']}` -> `{docs_snapshot['status']}`",
        f"  - `docs checked: {docs_checked}`",
        f"  - `command snippets checked: {snippets_checked}`",
        "",
        "## Canonical sources",
        "",
        *_canonical_sources(
            role,
            issue_register_doc=issue_register_doc_rel,
            deep_audit_doc=deep_audit_doc_rel,
            governance_doc=governance_doc_rel,
        ),
        "",
        "## Projection handling rules",
        "",
        *_handling_rules(role),
        "",
    ]
    return "\n".join(lines)


def _write_if_changed(path: Path, text: str) -> bool:
    normalized = text if text.endswith("\n") else f"{text}\n"
    before = path.read_text(encoding="utf-8") if path.exists() else None
    changed = before != normalized
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(normalized, encoding="utf-8")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Render SSOT-governed active workbook projection docs.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--workspace-root", default="")
    parser.add_argument("--projection-role", default="all")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "workbook_projection_render_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": "",
        "workspace_root": "",
        "active_workbook_family": "",
        "projection_renderer": "",
        "projection_results": [],
        "issue_snapshot": {},
        "docs_checker_snapshot": {},
        "violations": [],
    }

    try:
        repo_root, workspace_root = resolve_workbook_roots(args.repo_root, args.workspace_root, start=__file__)
        registry_bundle = load_active_workbook_registry(repo_root)
        active_family = registry_bundle.active_family_doc
        workbook_minor = str(active_family.get("workbook_family", "")).strip()
        governance_doc_rel = str(active_family.get("governance_doc", "")).strip()
        issue_register_doc_rel = str(active_family.get("issue_register_doc", "")).strip()
        deep_audit_doc_rel = str(active_family.get("deep_audit_workbook_doc", "")).strip()
        renderer_rel = registry_bundle.template_contract.projection_renderer_rel
        projection_rows = active_family.get("projection_exports") or []
        if not isinstance(projection_rows, list) or not projection_rows:
            raise RuntimeError("active_projection_exports_missing")
        selected_role = str(args.projection_role or "all").strip()
        if selected_role not in {"all", "issue_register_projection", "deep_audit_projection"}:
            raise RuntimeError(f"unknown_projection_role:{selected_role}")
        issue_snapshot = _issue_snapshot(repo_root=repo_root, workspace_root=workspace_root)
        docs_snapshot = _docs_checker_snapshot(repo_root=repo_root)
    except Exception as exc:
        payload["error_code"] = ERR_DISCOVERY
        payload["violations"] = [f"discovery:{type(exc).__name__}:{exc}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["repo_root"] = str(repo_root)
    payload["workspace_root"] = str(workspace_root)
    payload["active_workbook_family"] = workbook_minor
    payload["projection_renderer"] = renderer_rel
    payload["issue_snapshot"] = issue_snapshot
    payload["docs_checker_snapshot"] = {
        key: value
        for key, value in docs_snapshot.items()
        if key not in {"stdout", "stderr"}
    }

    if issue_snapshot["status"] not in {STATUS_PASS_REQUIRED, STATUS_FAIL_REQUIRED}:
        payload["error_code"] = ERR_SNAPSHOT
        payload["violations"] = [f"issue_snapshot_status_invalid:{issue_snapshot['status']}"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    rendered_date = datetime.now().strftime("%Y-%m-%d")
    results: list[dict[str, Any]] = []
    try:
        for row in projection_rows:
            if not isinstance(row, dict):
                raise RuntimeError("projection_row_not_mapping")
            role = str(row.get("projection_role", "")).strip()
            if selected_role != "all" and role != selected_role:
                continue
            path_rel = str(row.get("path", "")).strip()
            authority_doc_rel = str(row.get("authority_doc", "")).strip()
            if not role or not path_rel or not authority_doc_rel:
                raise RuntimeError(f"projection_row_missing_fields:{role or 'unknown'}")
            target_path = (workspace_root / path_rel).resolve()
            rendered_text = _render_projection_text(
                minor=workbook_minor,
                role=role,
                authority_doc_rel=authority_doc_rel,
                issue_register_doc_rel=issue_register_doc_rel,
                deep_audit_doc_rel=deep_audit_doc_rel,
                governance_doc_rel=governance_doc_rel,
                registry_current_ref=registry_bundle.template_contract.workbook_registry_current_ref,
                renderer_rel=renderer_rel,
                issue_snapshot=issue_snapshot,
                docs_snapshot=docs_snapshot,
                rendered_date=rendered_date,
            )
            changed = False
            if args.write:
                changed = _write_if_changed(target_path, rendered_text)
            else:
                current = target_path.read_text(encoding="utf-8") if target_path.exists() else None
                changed = current != (rendered_text if rendered_text.endswith("\n") else f"{rendered_text}\n")
            results.append(
                {
                    "projection_role": role,
                    "path": str(target_path),
                    "path_rel": path_rel,
                    "authority_doc": authority_doc_rel,
                    "write_applied": bool(args.write),
                    "changed": changed,
                }
            )
    except Exception as exc:
        payload["error_code"] = ERR_RENDER
        payload["violations"] = [f"render:{type(exc).__name__}:{exc}"]
        payload["projection_results"] = results
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["projection_results"] = results
    payload["workbook_projection_render_status"] = STATUS_PASS_REQUIRED
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
