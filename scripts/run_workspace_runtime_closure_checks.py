#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root
from workspace_runtime_closure_command_common import (
    WorkspaceRuntimeClosureCheckerSpec,
    build_workspace_runtime_closure_checker_command,
    resolve_workspace_runtime_closure_checker_spec,
    resolve_workspace_runtime_closure_path_token,
    workspace_runtime_closure_checker_specs,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
RUNNER_POLICY_ID = "workspace_runtime_closure_runner_v1"
ERR_WORKSPACE_RUNTIME_CLOSURE_RUNNER = "IP-WRCR-001"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _selected_specs(args: argparse.Namespace) -> tuple[WorkspaceRuntimeClosureCheckerSpec, ...]:
    checker_ids = [str(item).strip() for item in (args.checker_id or []) if str(item).strip()]
    if checker_ids:
        seen: set[str] = set()
        rows: list[WorkspaceRuntimeClosureCheckerSpec] = []
        for checker_id in checker_ids:
            if checker_id in seen:
                continue
            seen.add(checker_id)
            rows.append(resolve_workspace_runtime_closure_checker_spec(checker_id))
        return tuple(rows)
    families = {str(item).strip().lower() for item in (args.family or []) if str(item).strip()}
    return workspace_runtime_closure_checker_specs(families=families or None)


def _run_checker(
    *,
    repo_root: Path,
    repo_catalog_path: str,
    catalog_path: str,
    spec: WorkspaceRuntimeClosureCheckerSpec,
    include_payload: bool,
) -> dict[str, Any]:
    command = build_workspace_runtime_closure_checker_command(
        checker_id=spec.checker_id,
        repo_root=repo_root,
        repo_catalog_path=repo_catalog_path,
        catalog_path=catalog_path,
        json_only=True,
    )
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = str(completed.stdout or "").strip()
    stderr = str(completed.stderr or "").strip()
    payload: dict[str, Any] = {}
    stale_reasons: list[str] = []
    error_code = ""
    status = STATUS_FAIL_REQUIRED
    parse_status = "missing_json_payload"
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
                parse_status = "parsed"
            else:
                parse_status = "non_object_json_payload"
        except Exception:
            parse_status = "invalid_json_payload"
    if payload:
        status = str(payload.get(spec.status_field, "")).strip().upper() or STATUS_FAIL_REQUIRED
        error_code = str(payload.get("error_code", "")).strip()
        stale_reasons = [
            str(item).strip()
            for item in (payload.get("stale_reasons") or [])
            if str(item).strip()
        ]
    row: dict[str, Any] = {
        "checker_id": spec.checker_id,
        "closure_family": spec.closure_family,
        "status_field": spec.status_field,
        "status": status,
        "return_code": int(completed.returncode),
        "error_code": error_code,
        "parse_status": parse_status,
        "command": command,
        "checked_identity_count": int(payload.get("checked_identity_count") or 0) if payload else 0,
        "violation_count": int(payload.get("violation_count") or 0) if payload else 0,
        "catalog_selection_mode": str(payload.get("catalog_selection_mode", "")).strip(),
        "repo_catalog_included": bool(payload.get("repo_catalog_included", False)) if payload else False,
        "pack_scan_policy_id": str(payload.get("pack_scan_policy_id", "")).strip(),
        "stale_reasons": stale_reasons,
    }
    if stderr:
        row["stderr"] = stderr
    if include_payload:
        row["payload"] = payload
    return row


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Run the shared bounded workspace-runtime closure checker set through one "
            "executable surface."
        )
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--catalog", required=True)
    ap.add_argument(
        "--family",
        action="append",
        choices=("launcher", "transport", "pack"),
        default=[],
        help="restrict execution to one or more closure families",
    )
    ap.add_argument("--checker-id", action="append", default=[], help="run explicit checker id(s)")
    ap.add_argument("--include-payload", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    specs = _selected_specs(args)
    payload: dict[str, Any] = {
        "workspace_runtime_closure_execution_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "runner_policy_id": RUNNER_POLICY_ID,
        "repo_root": str(repo_root),
        "repo_catalog_path": resolve_workspace_runtime_closure_path_token(
            str(args.repo_catalog),
            repo_root=repo_root,
        ),
        "catalog_path": resolve_workspace_runtime_closure_path_token(
            str(args.catalog),
            repo_root=repo_root,
        ),
        "selected_checker_ids": [spec.checker_id for spec in specs],
        "checker_count": len(specs),
        "passed_checker_count": 0,
        "failed_checker_count": 0,
        "results": [],
        "stale_reasons": [],
    }
    if not specs:
        payload["error_code"] = ERR_WORKSPACE_RUNTIME_CLOSURE_RUNNER
        payload["stale_reasons"] = ["no_workspace_runtime_closure_checkers_selected"]
        _emit(payload, json_only=args.json_only)
        return 1

    results = [
        _run_checker(
            repo_root=repo_root,
            repo_catalog_path=str(args.repo_catalog),
            catalog_path=str(args.catalog),
            spec=spec,
            include_payload=bool(args.include_payload),
        )
        for spec in specs
    ]
    failed = [
        row
        for row in results
        if int(row.get("return_code") or 0) != 0
        or str(row.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED
    ]
    payload["results"] = results
    payload["passed_checker_count"] = len(results) - len(failed)
    payload["failed_checker_count"] = len(failed)
    if failed:
        payload["workspace_runtime_closure_execution_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_WORKSPACE_RUNTIME_CLOSURE_RUNNER
        payload["stale_reasons"] = [
            f"checker_non_pass:{row['checker_id']}:{row.get('status', '')}:{row.get('return_code', '')}"
            for row in failed
        ]
    else:
        payload["workspace_runtime_closure_execution_status"] = STATUS_PASS_REQUIRED

    _emit(payload, json_only=args.json_only)
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
