#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root
from runtime_temp_path_common import runtime_temp_dir
from temp_repo_materialization_common import (
    DEFAULT_BASELINE_COMMIT_MESSAGE,
    HISTORY_MODE_CLONE_ONLY,
    HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY,
    create_baseline_commit,
    materialize_repo_snapshot,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_ISOLATED_REPLAY = "IP-LANE-REPLAY-001"
DEFAULT_LANE_ID = "identity_codex_launcher_v1_6_14"
SUMMARY_TIMEOUT_SECONDS = 300
REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY = "requested_commit_history"
REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE = "current_worktree_baseline"
SUPPORTED_REPLAY_SOURCE_MODES = (
    REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY,
    REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _run_text(cmd: list[str], *, cwd: Path, timeout_seconds: int = SUMMARY_TIMEOUT_SECONDS) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}"
        )
    return proc.stdout


def _run_git(repo_root: Path, *args: str) -> str:
    return _run_text(["git", "-C", str(repo_root), *args], cwd=repo_root).strip()


def _render_lane_summary(
    *,
    runner_repo_root: Path,
    target_repo_root: Path,
    target_workspace_root: Path,
    commit: str,
    lane_id: str,
) -> dict[str, Any]:
    output = _run_text(
        [
            "python3",
            str((runner_repo_root / "scripts" / "render_protocol_lane_audit_summary.py").resolve()),
            "--repo-root",
            str(target_repo_root),
            "--workspace-root",
            str(target_workspace_root),
            "--lane",
            lane_id,
            "--commit",
            commit,
            "--json-only",
        ],
        cwd=target_workspace_root,
    )
    payload = json.loads(output)
    if not isinstance(payload, dict):
        raise RuntimeError("lane summary renderer did not return a JSON object")
    return payload


def _ensure_symlink(target: Path, link_path: Path) -> None:
    target_resolved = target.expanduser().resolve()
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_dir() and not link_path.is_symlink():
            shutil.rmtree(link_path)
        else:
            link_path.unlink()
    link_path.symlink_to(target_resolved, target_is_directory=target_resolved.is_dir())


def _bridge_workspace_assets(workspace_root: Path, isolated_workspace_root: Path) -> list[dict[str, str]]:
    bridged: list[dict[str, str]] = []
    bridge_specs = [
        (workspace_root / ".identity", isolated_workspace_root / ".identity", True),
        (workspace_root / "scripts", isolated_workspace_root / "scripts", True),
        (workspace_root / "activity" / "evidence", isolated_workspace_root / "activity" / "evidence", False),
    ]
    for source, destination, required in bridge_specs:
        if not source.exists():
            if required:
                raise FileNotFoundError(f"required isolated replay bridge source missing: {source}")
            continue
        _ensure_symlink(source, destination)
        bridged.append(
            {
                "source": str(source.resolve()),
                "destination": str(destination),
                "bridge_mode": "symlink",
            }
        )
    return bridged


def _lane_projection(summary_payload: dict[str, Any]) -> dict[str, Any]:
    docs_checker = summary_payload.get("docs_checker") or {}
    workbook = summary_payload.get("workbook_consistency") or {}
    launcher_probe = summary_payload.get("launcher_probe") or {}
    lane_summary = summary_payload.get("lane_summary") or {}
    return {
        "status": str(summary_payload.get("status", "")).strip(),
        "lane_id": str(summary_payload.get("lane_id", "")).strip(),
        "range_mode": str(summary_payload.get("range_mode", "")).strip(),
        "base": str(summary_payload.get("base", "")).strip(),
        "head": str(summary_payload.get("head", "")).strip(),
        "docs_checker_status": str(docs_checker.get("status", "")).strip(),
        "docs_checked": docs_checker.get("docs_checked"),
        "command_snippets_checked": docs_checker.get("command_snippets_checked"),
        "workbook_status": str(workbook.get("issue_register_consistency_status", "")).strip(),
        "launcher_probe_status": str(launcher_probe.get("probe_status", "")).strip(),
        "launcher_dry_run_status": str(launcher_probe.get("launcher_dry_run_status", "")).strip(),
        "projection_docs_checker_gate_status": str(
            lane_summary.get("projection_docs_checker_gate_status", "")
        ).strip(),
        "stream_touch_evidence_status": str(lane_summary.get("stream_touch_evidence_status", "")).strip(),
        "canonical_docs_checker_violation_count": lane_summary.get("canonical_docs_checker_violation_count"),
    }


def _compare_lane_projection(
    *,
    direct_projection: dict[str, Any],
    isolated_projection: dict[str, Any],
) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    for key in sorted(set(direct_projection.keys()) | set(isolated_projection.keys())):
        if direct_projection.get(key) != isolated_projection.get(key):
            mismatches.append(
                f"projection_mismatch:{key}:{direct_projection.get(key)!r}!={isolated_projection.get(key)!r}"
            )
    return (not mismatches), mismatches


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate isolated historical replay for the protocol lane audit summary control plane."
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--lane", default=DEFAULT_LANE_ID)
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument(
        "--replay-source-mode",
        default=REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE,
        choices=SUPPORTED_REPLAY_SOURCE_MODES,
        help=(
            "current_worktree_baseline snapshots the current worktree into a materialized baseline while "
            "keeping diff/commit scope pinned to the requested source-history commit; "
            "requested_commit_history replays the requested committed tree through isolated clone-only "
            "workspaces."
        ),
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    requested_commit = str(args.commit or "HEAD").strip() or "HEAD"
    lane_id = str(args.lane or DEFAULT_LANE_ID).strip() or DEFAULT_LANE_ID
    requested_replay_source_mode = (
        str(args.replay_source_mode or REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE).strip()
        or REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE
    )

    payload: dict[str, Any] = {
        "isolated_historical_replay_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_ISOLATED_REPLAY,
        "lane_id": lane_id,
        "requested_commit": requested_commit,
        "requested_replay_source_mode": requested_replay_source_mode,
        "resolved_commit": "",
        "replay_source_mode": "",
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "direct_workspace_root": "",
        "direct_repo_root": "",
        "isolated_workspace_root": "",
        "isolated_repo_root": "",
        "direct_repo_materialization": {},
        "isolated_repo_materialization": {},
        "bridged_workspace_assets": [],
        "direct_projection": {},
        "isolated_projection": {},
        "projection_parity_match": False,
        "baseline_commit": "",
        "stale_reasons": [],
    }

    temp_root = runtime_temp_dir(
        channel="protocol-lane-audit",
        operation="isolated-historical-replay",
        identity_id="shared",
        prefix="run",
    )
    direct_workspace_root = (temp_root / "direct-workspace").resolve()
    direct_repo_root = (direct_workspace_root / repo_root.name).resolve()
    isolated_workspace_root = (temp_root / "isolated-workspace").resolve()
    isolated_repo_root = (isolated_workspace_root / repo_root.name).resolve()
    payload["direct_workspace_root"] = str(direct_workspace_root)
    payload["direct_repo_root"] = str(direct_repo_root)
    payload["isolated_workspace_root"] = str(isolated_workspace_root)
    payload["isolated_repo_root"] = str(isolated_repo_root)

    try:
        direct_workspace_root.mkdir(parents=True, exist_ok=True)
        source_resolved_commit = _run_git(repo_root, "rev-parse", requested_commit)

        direct_history_mode = (
            HISTORY_MODE_CLONE_ONLY
            if requested_replay_source_mode == REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY
            else HISTORY_MODE_CLONE_WITH_WORKTREE_OVERLAY
        )
        direct_materialization = materialize_repo_snapshot(
            source_repo_root=repo_root,
            target_repo_root=direct_repo_root,
            history_mode=direct_history_mode,
        )
        payload["direct_repo_materialization"] = direct_materialization.to_dict()
        baseline_commit = ""
        if requested_replay_source_mode == REPLAY_SOURCE_MODE_CURRENT_WORKTREE_BASELINE:
            baseline_commit = create_baseline_commit(
                target_repo_root=direct_repo_root,
                message=DEFAULT_BASELINE_COMMIT_MESSAGE,
            )
        payload["baseline_commit"] = baseline_commit
        resolved_commit = source_resolved_commit
        if requested_replay_source_mode == REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY:
            _run_text(
                ["git", "-C", str(direct_repo_root), "checkout", "--quiet", "--detach", resolved_commit],
                cwd=direct_workspace_root,
            )
        payload["replay_source_mode"] = requested_replay_source_mode
        direct_bridged_assets = _bridge_workspace_assets(workspace_root, direct_workspace_root)
        payload["resolved_commit"] = resolved_commit
        direct_summary = _render_lane_summary(
            runner_repo_root=direct_repo_root,
            target_repo_root=direct_repo_root,
            target_workspace_root=direct_workspace_root,
            commit="HEAD" if requested_replay_source_mode == REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY else resolved_commit,
            lane_id=lane_id,
        )
        payload["direct_projection"] = _lane_projection(direct_summary)

        isolated_workspace_root.mkdir(parents=True, exist_ok=True)
        materialization = materialize_repo_snapshot(
            source_repo_root=direct_repo_root,
            target_repo_root=isolated_repo_root,
            history_mode=HISTORY_MODE_CLONE_ONLY,
        )
        payload["isolated_repo_materialization"] = materialization.to_dict()
        if requested_replay_source_mode == REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY:
            _run_text(
                ["git", "-C", str(isolated_repo_root), "checkout", "--quiet", "--detach", resolved_commit],
                cwd=isolated_workspace_root,
            )
        isolated_bridged_assets = _bridge_workspace_assets(workspace_root, isolated_workspace_root)
        payload["bridged_workspace_assets"] = [
            *direct_bridged_assets,
            *isolated_bridged_assets,
        ]

        isolated_summary = _render_lane_summary(
            runner_repo_root=isolated_repo_root,
            target_repo_root=isolated_repo_root,
            target_workspace_root=isolated_workspace_root,
            commit="HEAD" if requested_replay_source_mode == REPLAY_SOURCE_MODE_REQUESTED_COMMIT_HISTORY else resolved_commit,
            lane_id=lane_id,
        )
        payload["isolated_projection"] = _lane_projection(isolated_summary)

        projection_parity_match, mismatches = _compare_lane_projection(
            direct_projection=payload["direct_projection"],
            isolated_projection=payload["isolated_projection"],
        )
        payload["projection_parity_match"] = projection_parity_match
        if not projection_parity_match:
            payload["stale_reasons"] = mismatches
            _emit(payload, json_only=args.json_only)
            return 1

        if payload["direct_projection"].get("status") != STATUS_PASS_REQUIRED:
            payload["stale_reasons"] = ["direct_summary_not_pass_required"]
            _emit(payload, json_only=args.json_only)
            return 1
        if payload["isolated_projection"].get("status") != STATUS_PASS_REQUIRED:
            payload["stale_reasons"] = ["isolated_summary_not_pass_required"]
            _emit(payload, json_only=args.json_only)
            return 1

        payload["isolated_historical_replay_status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        _emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        payload["stale_reasons"] = [f"isolated_historical_replay_failed:{type(exc).__name__}:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
