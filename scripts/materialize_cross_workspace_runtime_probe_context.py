#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from cross_workspace_runtime_probe_context_common import (
    ERR_ACTIVE_REPORT_DISCOVERY_FAILED,
    ERR_DISCOVERY_FAILED,
    ERR_MATERIALIZATION_FAILED,
    materialize_cross_workspace_runtime_probe_context,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _emit(payload: dict[str, object], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Discover a sibling workspace runtime catalog and materialize a borrowed .identity probe context."
    )
    ap.add_argument("--current-workspace-root", required=True)
    ap.add_argument("--target-workspace-root", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--require-active-execution-report", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, object] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_DISCOVERY_FAILED,
        "current_workspace_root": str(Path(args.current_workspace_root).expanduser().resolve()),
        "target_workspace_root": str(Path(args.target_workspace_root).expanduser().resolve()),
        "explicit_catalog": str(args.catalog or "").strip(),
        "repo_root": str(Path(args.repo_root).expanduser().resolve()) if str(args.repo_root or "").strip() else "",
        "require_active_execution_report": bool(args.require_active_execution_report),
    }
    try:
        result = materialize_cross_workspace_runtime_probe_context(
            current_workspace_root=Path(args.current_workspace_root),
            target_workspace_root=Path(args.target_workspace_root),
            explicit_catalog=str(args.catalog or "").strip(),
            repo_root=Path(args.repo_root).expanduser().resolve() if str(args.repo_root or "").strip() else None,
            require_active_execution_report=bool(args.require_active_execution_report),
        )
        payload.update(result)
        payload["status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        message = str(exc)
        if "active execution report" in message:
            payload["error_code"] = ERR_ACTIVE_REPORT_DISCOVERY_FAILED
        elif "target_identity_home_already_exists" in message or "source_identity_home_missing" in message:
            payload["error_code"] = ERR_MATERIALIZATION_FAILED
        else:
            payload["error_code"] = ERR_DISCOVERY_FAILED
        payload["stale_reasons"] = [message] if message else ["cross_workspace_runtime_probe_context_failed"]
        _emit(payload, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
