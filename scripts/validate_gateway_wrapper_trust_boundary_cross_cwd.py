#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_REPLAY_FAILED = "IP-GWTB-CWD-001"
ERR_MANIFEST_INVALID = "IP-GWTB-CWD-002"
ERR_PROBE_DIVERGENCE = "IP-GWTB-CWD-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _manifest_pairs(path: Path) -> list[tuple[str, int]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest_root_not_object")
    items = raw.get("items")
    if not isinstance(items, list):
        raise ValueError("manifest_items_not_list")
    pairs: list[tuple[str, int]] = []
    for row in items:
        if not isinstance(row, dict):
            raise ValueError("manifest_item_not_object")
        name = str(row.get("name", "")).strip()
        rc = row.get("rc")
        if not name:
            raise ValueError("manifest_item_name_missing")
        if not isinstance(rc, int):
            raise ValueError("manifest_item_rc_invalid")
        pairs.append((name, rc))
    if not pairs:
        raise ValueError("manifest_items_empty")
    return pairs


def _run_probe(
    *,
    cwd: Path,
    command_path: str,
    work_root: Path,
) -> dict[str, Any]:
    env = os.environ.copy()
    env["GATEWAY_PROBE_WORK_ROOT"] = str(work_root)
    proc = subprocess.run(
        ("bash", command_path),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    manifest_path = work_root / "manifest.gateway_wrapper_trust_boundary.json"
    payload: dict[str, Any] = {
        "cwd": str(cwd),
        "command_path": command_path,
        "rc": int(proc.returncode),
        "manifest_path": str(manifest_path),
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-12:]),
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-12:]),
        "manifest_exists": manifest_path.exists(),
        "probe_name_rc_pairs": [],
        "manifest_count": 0,
    }
    if manifest_path.exists():
        pairs = _manifest_pairs(manifest_path)
        payload["probe_name_rc_pairs"] = [[name, rc] for name, rc in pairs]
        payload["manifest_count"] = len(pairs)
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate gateway trust-boundary suite parity across protocol-root and workspace-root invocation."
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    workspace_relative_script = Path(repo_root.name) / "scripts" / "ci" / "run_gateway_wrapper_trust_boundary_probes_ci.sh"
    protocol_relative_script = Path("scripts") / "ci" / "run_gateway_wrapper_trust_boundary_probes_ci.sh"

    payload: dict[str, Any] = {
        "gateway_trust_boundary_cross_cwd_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "protocol_root_replay": {},
        "workspace_root_replay": {},
        "probe_name_rc_pairs_match": False,
        "checked_probe_count": 0,
        "stale_reasons": [],
    }

    with tempfile.TemporaryDirectory(prefix="gateway-trust-boundary-cross-cwd-") as tmp_dir:
        tmp_root = Path(tmp_dir).resolve()
        protocol_work_root = tmp_root / "protocol-root"
        workspace_work_root = tmp_root / "workspace-root"
        try:
            protocol_replay = _run_probe(
                cwd=repo_root,
                command_path=str(protocol_relative_script),
                work_root=protocol_work_root,
            )
            workspace_replay = _run_probe(
                cwd=workspace_root,
                command_path=str(workspace_relative_script),
                work_root=workspace_work_root,
            )
        except Exception as exc:
            payload["error_code"] = ERR_MANIFEST_INVALID
            payload["stale_reasons"] = [f"cross_cwd_replay_exception:{type(exc).__name__}:{exc}"]
            _emit(payload, json_only=args.json_only)
            return 1

        payload["protocol_root_replay"] = protocol_replay
        payload["workspace_root_replay"] = workspace_replay

        if int(protocol_replay.get("rc", 1)) != 0:
            payload["error_code"] = ERR_REPLAY_FAILED
            payload["stale_reasons"].append("protocol_root_replay_failed")
        if int(workspace_replay.get("rc", 1)) != 0:
            payload["error_code"] = payload["error_code"] or ERR_REPLAY_FAILED
            payload["stale_reasons"].append("workspace_root_replay_failed")
        if not bool(protocol_replay.get("manifest_exists")):
            payload["error_code"] = payload["error_code"] or ERR_MANIFEST_INVALID
            payload["stale_reasons"].append("protocol_root_manifest_missing")
        if not bool(workspace_replay.get("manifest_exists")):
            payload["error_code"] = payload["error_code"] or ERR_MANIFEST_INVALID
            payload["stale_reasons"].append("workspace_root_manifest_missing")

        protocol_pairs = protocol_replay.get("probe_name_rc_pairs") or []
        workspace_pairs = workspace_replay.get("probe_name_rc_pairs") or []
        payload["checked_probe_count"] = len(protocol_pairs) if isinstance(protocol_pairs, list) else 0
        payload["probe_name_rc_pairs_match"] = protocol_pairs == workspace_pairs and bool(protocol_pairs)
        if not payload["probe_name_rc_pairs_match"]:
            payload["error_code"] = payload["error_code"] or ERR_PROBE_DIVERGENCE
            payload["stale_reasons"].append("probe_name_rc_pairs_diverged")

        if payload["stale_reasons"]:
            _emit(payload, json_only=args.json_only)
            return 1

        payload["gateway_trust_boundary_cross_cwd_status"] = STATUS_PASS_REQUIRED
        _emit(payload, json_only=args.json_only)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
