#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from temp_repo_materialization_common import (
    DEFAULT_BASELINE_COMMIT_MESSAGE,
    HISTORY_MODE_CLONE_ONLY,
    HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY,
    SUPPORTED_HISTORY_MODES,
    create_baseline_commit,
    materialize_repo_snapshot,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_MATERIALIZATION_FAILED = "IP-TMP-REPO-001"


def _emit(payload: dict[str, object], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Materialize a temp repo workspace with preserved git history and optional current-worktree overlay."
    )
    ap.add_argument("--source-repo", required=True)
    ap.add_argument("--target-repo", required=True)
    ap.add_argument(
        "--history-mode",
        default=HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY,
        choices=SUPPORTED_HISTORY_MODES,
    )
    ap.add_argument("--create-baseline-commit", action="store_true")
    ap.add_argument("--baseline-message", default=DEFAULT_BASELINE_COMMIT_MESSAGE)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload: dict[str, object] = {
        "status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_MATERIALIZATION_FAILED,
        "source_repo_root": str(Path(args.source_repo).expanduser().resolve()),
        "target_repo_root": str(Path(args.target_repo).expanduser().resolve()),
        "history_mode": str(args.history_mode),
        "supported_history_modes": list(SUPPORTED_HISTORY_MODES),
        "baseline_commit_created": False,
        "baseline_commit": "",
    }
    try:
        stats = materialize_repo_snapshot(
            source_repo_root=Path(args.source_repo),
            target_repo_root=Path(args.target_repo),
            history_mode=str(args.history_mode),
        )
        payload.update(stats.to_dict())
        if args.create_baseline_commit:
            baseline_commit = create_baseline_commit(
                target_repo_root=Path(args.target_repo),
                message=str(args.baseline_message),
            )
            payload["baseline_commit_created"] = bool(baseline_commit)
            payload["baseline_commit"] = baseline_commit
        payload["status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        payload["stale_reasons"] = [f"temp_repo_materialization_failed:{type(exc).__name__}:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
