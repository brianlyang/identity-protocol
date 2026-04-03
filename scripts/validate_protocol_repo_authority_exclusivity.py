#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_repo_authority_exclusivity_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    project_protocol_repo_authority_exclusivity,
)
from repo_root_resolution_common import resolve_repo_root

STATUS_KEY = "protocol_repo_authority_exclusivity_status"
ERR_ROOT = "IP-PRAE-001"
ERR_GIT = "IP-PRAE-002"
ERR_AUTHORITY = "IP-PRAE-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate that identity protocol repo authority resolves only from the protocol repo root.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    projection = project_protocol_repo_authority_exclusivity(repo_root, cwd=Path.cwd())

    stale_reasons: list[str] = []
    error_code = ""

    if not repo_root.exists() or not repo_root.is_dir():
        stale_reasons.append("protocol_repo_root_missing")
        error_code = ERR_ROOT
    if not projection["protocol_repo_dirname_matches"]:
        stale_reasons.append(
            f"protocol_repo_dirname_mismatch:{projection['protocol_repo_dirname']}"
        )
        error_code = error_code or ERR_ROOT
    if projection["protocol_repo_marker_missing"]:
        stale_reasons.append(
            "protocol_repo_required_markers_missing:" + ",".join(projection["protocol_repo_marker_missing"])
        )
        error_code = error_code or ERR_ROOT
    if not projection["protocol_repo_git_top_level"]:
        stale_reasons.append("protocol_repo_git_top_level_missing")
        error_code = error_code or ERR_GIT
    elif not projection["protocol_repo_root_matches_git_top_level"]:
        stale_reasons.append(
            "protocol_repo_root_not_independent_git_toplevel:"
            + projection["protocol_repo_git_top_level"]
        )
        error_code = error_code or ERR_AUTHORITY
    if projection["host_container_present"] and projection["host_container_authority_status"] != STATUS_PASS_REQUIRED:
        stale_reasons.append("host_container_authority_not_demoted")
        error_code = error_code or ERR_AUTHORITY

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_AUTHORITY),
        **projection,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
