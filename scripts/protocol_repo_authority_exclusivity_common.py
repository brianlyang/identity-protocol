#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from repo_root_resolution_common import PROTOCOL_REPO_DIRNAME, PROTOCOL_ROOT_MARKERS

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def protocol_repo_missing_markers(repo_root: Path) -> tuple[str, ...]:
    return tuple(marker for marker in PROTOCOL_ROOT_MARKERS if not (repo_root / marker).exists())


def git_top_level(start: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def collect_enclosing_host_git_roots(repo_root: Path) -> tuple[str, ...]:
    roots: list[str] = []
    for candidate in repo_root.resolve().parents:
        top_level = git_top_level(candidate)
        if not top_level:
            continue
        top_path = Path(top_level).resolve()
        if top_path == repo_root.resolve():
            continue
        if not _within(repo_root.resolve(), top_path):
            continue
        rendered = str(top_path)
        if rendered not in roots:
            roots.append(rendered)
    return tuple(roots)


def project_protocol_repo_authority_exclusivity(repo_root: Path, *, cwd: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cwd_path = (cwd or Path.cwd()).resolve()
    missing_markers = protocol_repo_missing_markers(repo_root) if repo_root.exists() else tuple(PROTOCOL_ROOT_MARKERS)
    protocol_git_top_level = git_top_level(repo_root) if repo_root.exists() else ""
    repo_root_rendered = str(repo_root)
    enclosing_host_git_roots = collect_enclosing_host_git_roots(repo_root) if repo_root.exists() else ()
    cwd_git_top_level = git_top_level(cwd_path)
    protocol_repo_root_matches_git_top_level = bool(protocol_git_top_level) and protocol_git_top_level == repo_root_rendered
    host_container_present = bool(enclosing_host_git_roots)
    host_container_authority_status = (
        STATUS_PASS_REQUIRED if (not host_container_present or protocol_repo_root_matches_git_top_level) else STATUS_FAIL_REQUIRED
    )
    return {
        "protocol_repo_root": repo_root_rendered,
        "protocol_repo_dirname": repo_root.name,
        "protocol_repo_dirname_matches": repo_root.name == PROTOCOL_REPO_DIRNAME,
        "protocol_repo_marker_missing": list(missing_markers),
        "protocol_repo_markers_present": not missing_markers,
        "protocol_repo_git_metadata_present": (repo_root / ".git").exists(),
        "protocol_repo_git_top_level": protocol_git_top_level,
        "protocol_repo_root_matches_git_top_level": protocol_repo_root_matches_git_top_level,
        "enclosing_host_git_roots": list(enclosing_host_git_roots),
        "enclosing_host_git_root_count": len(enclosing_host_git_roots),
        "host_container_present": host_container_present,
        "host_container_authority_status": host_container_authority_status,
        "cwd": str(cwd_path),
        "cwd_git_top_level": cwd_git_top_level,
        "cwd_resolution_drift_present": bool(cwd_git_top_level) and cwd_git_top_level != repo_root_rendered,
    }
