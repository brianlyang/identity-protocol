#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root
from runtime_temp_path_common import runtime_temp_dir
from temp_repo_materialization_common import (
    DEFAULT_BASELINE_COMMIT_MESSAGE,
    HISTORY_MODE_CLONE_ONLY,
    HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY,
    create_baseline_commit,
    materialize_repo_snapshot,
)
from workbook_control_plane_common import load_active_workbook_registry

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
SOURCE_MODE_CURRENT_WORKTREE_BASELINE = "current_worktree_baseline"
SOURCE_MODE_REQUESTED_COMMIT_HISTORY = "requested_commit_history"
SUPPORTED_SOURCE_MODES = (
    SOURCE_MODE_CURRENT_WORKTREE_BASELINE,
    SOURCE_MODE_REQUESTED_COMMIT_HISTORY,
)

DOCS_COUNT_RE = re.compile(r"docs checked:\s*(\d+)", flags=re.IGNORECASE)
SNIPPETS_COUNT_RE = re.compile(r"command snippets checked:\s*(\d+)", flags=re.IGNORECASE)
DOCS_COMMAND_LINE_RE = re.compile(
    r"(?P<prefix>- `scripts/docs_command_contract_check\.py` -> `PASS` \(`docs checked: )"
    r"(?P<docs>\d+)"
    r"(?P<middle>`, `command snippets checked: )"
    r"(?P<snippets>\d+)"
    r"(?P<suffix>`\))"
)


def _run_git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        combined = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part).strip()
        raise RuntimeError(f"git_command_failed:repo={repo_root}:args={' '.join(args)}:{combined}")
    return proc.stdout.strip()


def _run_docs_checker(repo_root: Path) -> tuple[int, int, str]:
    proc = subprocess.run(
        ["python3", "scripts/docs_command_contract_check.py"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part).strip()
    if proc.returncode != 0:
        raise RuntimeError(f"docs_checker_failed:rc={proc.returncode}:{combined}")
    docs_match = DOCS_COUNT_RE.search(combined)
    snippets_match = SNIPPETS_COUNT_RE.search(combined)
    if docs_match is None or snippets_match is None:
        raise RuntimeError(f"docs_checker_counts_missing:{combined}")
    return int(docs_match.group(1)), int(snippets_match.group(1)), combined


def _sync_doc(path: Path, *, docs_checked: int, snippets_checked: int, write: bool) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = DOCS_COMMAND_LINE_RE.search(text)
    if match is None:
        raise RuntimeError(f"docs_checker_line_missing:{path}")
    before = {
        "docs_checked": int(match.group("docs")),
        "command_snippets_checked": int(match.group("snippets")),
    }
    replacement = (
        f"{match.group('prefix')}{docs_checked}"
        f"{match.group('middle')}{snippets_checked}"
        f"{match.group('suffix')}"
    )
    updated_text, count = DOCS_COMMAND_LINE_RE.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError(f"docs_checker_line_replace_failed:{path}:count={count}")
    changed = updated_text != text
    if write and changed:
        path.write_text(updated_text, encoding="utf-8")
    return {
        "path": str(path),
        "before": before,
        "after": {
            "docs_checked": docs_checked,
            "command_snippets_checked": snippets_checked,
        },
        "changed": changed,
        "write_applied": bool(write and changed),
    }


def _materialize_docs_checker_source(
    *,
    repo_root: Path,
    source_mode: str,
    requested_commit: str,
) -> dict[str, Any]:
    token = str(source_mode or "").strip()
    if token not in SUPPORTED_SOURCE_MODES:
        raise RuntimeError(f"unsupported_source_mode:{source_mode}")

    source_resolved_commit = _run_git(repo_root, "rev-parse", requested_commit)
    temp_root = runtime_temp_dir(
        channel="workbook-docs-checker-sync",
        operation="source-materialization",
        identity_id="shared",
        prefix="run",
    )
    source_workspace_root = (temp_root / "workspace").resolve()
    source_workspace_root.mkdir(parents=True, exist_ok=True)
    source_repo_root = (source_workspace_root / repo_root.name).resolve()
    history_mode = (
        HISTORY_MODE_CLONE_ONLY
        if token == SOURCE_MODE_REQUESTED_COMMIT_HISTORY
        else HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY
    )
    materialization = materialize_repo_snapshot(
        source_repo_root=repo_root,
        target_repo_root=source_repo_root,
        history_mode=history_mode,
    )
    baseline_commit = ""
    if token == SOURCE_MODE_REQUESTED_COMMIT_HISTORY:
        _run_git(source_repo_root, "checkout", "--quiet", "--detach", source_resolved_commit)
        materialized_commit = _run_git(source_repo_root, "rev-parse", "HEAD")
    else:
        baseline_commit = create_baseline_commit(
            target_repo_root=source_repo_root,
            message=DEFAULT_BASELINE_COMMIT_MESSAGE,
        )
        materialized_commit = baseline_commit or _run_git(source_repo_root, "rev-parse", "HEAD")
    return {
        "source_mode": token,
        "requested_commit": requested_commit,
        "source_resolved_commit": source_resolved_commit,
        "source_workspace_root": str(source_workspace_root),
        "source_repo_root": str(source_repo_root),
        "history_mode": history_mode,
        "baseline_commit": baseline_commit,
        "materialized_commit": materialized_commit,
        "repo_materialization": materialization.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Truth-sync the active canonical workbook docs checker counts from a governed "
            "docs-checker source materialization."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument(
        "--source-mode",
        default=SOURCE_MODE_CURRENT_WORKTREE_BASELINE,
        choices=SUPPORTED_SOURCE_MODES,
        help=(
            "current_worktree_baseline materializes a clone-with-overlay snapshot of the current worktree; "
            "requested_commit_history materializes a clean clone and pins it to the requested commit."
        ),
    )
    parser.add_argument(
        "--commit",
        default="HEAD",
        help="Git commit to use when source-mode=requested_commit_history (default: HEAD).",
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    payload: dict[str, Any] = {
        "workbook_docs_checker_sync_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "requested_source_mode": str(args.source_mode),
        "requested_commit": str(args.commit or "HEAD").strip() or "HEAD",
        "source_mode": "",
        "source_materialization": {},
        "write_requested": bool(args.write),
        "write_applied": False,
        "updated_files": [],
        "stale_reasons": [],
    }

    try:
        repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
        registry_bundle = load_active_workbook_registry(repo_root)
        active_family = registry_bundle.active_family_doc
        issue_register_rel = str(active_family.get("issue_register_doc") or "").strip()
        deep_audit_rel = str(active_family.get("deep_audit_workbook_doc") or "").strip()
        if not issue_register_rel or not deep_audit_rel:
            raise RuntimeError("active_workbook_authority_surfaces_missing")
        source_materialization = _materialize_docs_checker_source(
            repo_root=repo_root,
            source_mode=str(args.source_mode),
            requested_commit=str(args.commit or "HEAD").strip() or "HEAD",
        )
        source_repo_root = Path(str(source_materialization["source_repo_root"])).resolve()
        source_registry_bundle = load_active_workbook_registry(source_repo_root)
        source_active_family = source_registry_bundle.active_family_doc
        source_issue_register_rel = str(source_active_family.get("issue_register_doc") or "").strip()
        source_deep_audit_rel = str(source_active_family.get("deep_audit_workbook_doc") or "").strip()
        if (
            source_issue_register_rel != issue_register_rel
            or source_deep_audit_rel != deep_audit_rel
            or str(source_active_family.get("workbook_family") or "").strip()
            != str(active_family.get("workbook_family") or "").strip()
        ):
            raise RuntimeError(
                "workbook_authority_surface_mismatch:"
                f"target_family={active_family.get('workbook_family')}:"
                f"source_family={source_active_family.get('workbook_family')}:"
                f"target_issue={issue_register_rel}:source_issue={source_issue_register_rel}:"
                f"target_deep_audit={deep_audit_rel}:source_deep_audit={source_deep_audit_rel}"
            )
        docs_checked, snippets_checked, docs_output = _run_docs_checker(source_repo_root)
        payload["repo_root"] = str(repo_root)
        payload["workbook_registry"] = str(registry_bundle.versioned_path)
        payload["active_workbook_family"] = str(active_family.get("workbook_family") or "").strip()
        payload["source_mode"] = str(source_materialization["source_mode"])
        payload["source_materialization"] = source_materialization
        payload["source_workbook_registry"] = str(source_registry_bundle.versioned_path)
        payload["source_active_workbook_family"] = str(source_active_family.get("workbook_family") or "").strip()
        payload["docs_checker_counts"] = {
            "docs_checked": docs_checked,
            "command_snippets_checked": snippets_checked,
            "raw_output": docs_output,
        }
        results = [
            _sync_doc(
                (repo_root / issue_register_rel).resolve(),
                docs_checked=docs_checked,
                snippets_checked=snippets_checked,
                write=bool(args.write),
            ),
            _sync_doc(
                (repo_root / deep_audit_rel).resolve(),
                docs_checked=docs_checked,
                snippets_checked=snippets_checked,
                write=bool(args.write),
            ),
        ]
        payload["updated_files"] = results
        payload["write_applied"] = any(bool(row.get("write_applied")) for row in results)
        payload["pending_changes"] = any(bool(row.get("changed")) for row in results)
        payload["workbook_docs_checker_sync_status"] = STATUS_PASS_REQUIRED
        rc = 0
    except RuntimeError as exc:
        message = str(exc)
        payload["stale_reasons"].append(message)
        rc = 1

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
