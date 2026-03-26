#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root
from workspace_runtime_closure_command_common import workspace_runtime_closure_target_scripts

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_WORKSPACE_RUNTIME_COMMAND_SURFACE = "IP-DOC-WRCS-001"

TARGET_SCRIPTS: tuple[str, ...] = workspace_runtime_closure_target_scripts()


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate that workspace-runtime closure command examples keep explicit --catalog "
            "when using --workspace-runtime-only."
        )
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    docs_root = (repo_root / "docs").resolve()

    payload: dict[str, Any] = {
        "workspace_runtime_closure_command_surface_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "docs_root": str(docs_root),
        "checked_doc_count": 0,
        "matched_command_line_count": 0,
        "violation_count": 0,
        "violations": [],
        "stale_reasons": [],
    }

    if not docs_root.exists():
        payload["error_code"] = ERR_WORKSPACE_RUNTIME_COMMAND_SURFACE
        payload["stale_reasons"] = [f"missing_docs_root:{docs_root}"]
        _emit(payload, json_only=args.json_only)
        return 1

    violations: list[dict[str, Any]] = []
    matched_count = 0
    checked_doc_count = 0

    for doc_path in sorted(docs_root.rglob("*.md")):
        checked_doc_count += 1
        try:
            text = doc_path.read_text(encoding="utf-8")
        except Exception:
            violations.append(
                {
                    "doc": str(doc_path),
                    "line": 0,
                    "script": "",
                    "reason": "doc_read_failed",
                    "snippet": "",
                }
            )
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if "--workspace-runtime-only" not in line:
                continue
            matched_script = next((script for script in TARGET_SCRIPTS if script in line), "")
            if not matched_script:
                continue
            matched_count += 1
            if "--catalog" in line:
                continue
            violations.append(
                {
                    "doc": str(doc_path),
                    "line": lineno,
                    "script": matched_script,
                    "reason": "workspace_runtime_only_missing_explicit_catalog",
                    "snippet": line.strip(),
                }
            )

    payload["checked_doc_count"] = checked_doc_count
    payload["matched_command_line_count"] = matched_count
    payload["violation_count"] = len(violations)
    payload["violations"] = violations
    payload["workspace_runtime_closure_command_surface_status"] = (
        STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    )
    payload["error_code"] = "" if not violations else ERR_WORKSPACE_RUNTIME_COMMAND_SURFACE
    _emit(payload, json_only=args.json_only)
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
