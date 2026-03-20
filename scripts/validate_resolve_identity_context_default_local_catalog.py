#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import yaml

from repo_root_resolution_common import resolve_protocol_repo_root, resolve_workspace_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RESOLVE_DEFAULT_LOCAL_CATALOG = "IP-RCTX-001"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _pick_identity_id(local_catalog_path: Path) -> str:
    catalog = _load_yaml(local_catalog_path)
    identities = [row for row in (catalog.get("identities") or []) if isinstance(row, dict)]
    default_identity = str(catalog.get("default_identity", "")).strip()
    if default_identity:
        return default_identity
    for row in identities:
        if str(row.get("status", "")).strip().lower() == "active":
            identity_id = str(row.get("id", "")).strip()
            if identity_id:
                return identity_id
    for row in identities:
        identity_id = str(row.get("id", "")).strip()
        if identity_id:
            return identity_id
    raise ValueError(f"no identity rows found in local catalog: {local_catalog_path}")


def _run_json(command: list[str], *, cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"command failed: {' '.join(command)}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid json output from {' '.join(command)}: {exc}") from exc


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate resolve_identity_context.py defaults to the project-local catalog.")
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--workspace-root", default="")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    workspace_root = resolve_workspace_root(args.workspace_root, start=__file__)
    local_catalog_path = (workspace_root / ".identity" / "catalog.local.yaml").resolve()
    payload: dict[str, Any] = {
        "resolve_identity_context_default_local_catalog_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_RESOLVE_DEFAULT_LOCAL_CATALOG,
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "local_catalog_path": str(local_catalog_path),
        "identity_id": "",
        "workspace_replay": {},
        "protocol_replay": {},
        "stale_reasons": [],
    }

    try:
        if not local_catalog_path.exists():
            raise FileNotFoundError(f"local catalog missing: {local_catalog_path}")
        identity_id = str(args.identity_id or "").strip() or _pick_identity_id(local_catalog_path)
        payload["identity_id"] = identity_id
        workspace_payload = _run_json(
            [
                "python3",
                "identity-protocol-local/scripts/resolve_identity_context.py",
                "resolve",
                "--identity-id",
                identity_id,
            ],
            cwd=workspace_root,
        )
        protocol_payload = _run_json(
            [
                "python3",
                "scripts/resolve_identity_context.py",
                "resolve",
                "--identity-id",
                identity_id,
            ],
            cwd=repo_root,
        )
        payload["workspace_replay"] = workspace_payload
        payload["protocol_replay"] = protocol_payload
        expected_catalog_path = str(local_catalog_path)
        expected_pack_path = str((workspace_root / ".identity" / identity_id).resolve())
        replays = {
            "workspace_replay": workspace_payload,
            "protocol_replay": protocol_payload,
        }
        stale_reasons: list[str] = []
        for label, replay in replays.items():
            if str(replay.get("source_layer", "")).strip() != "project":
                stale_reasons.append(f"{label}:source_layer")
            if str(replay.get("catalog_path", "")).strip() != expected_catalog_path:
                stale_reasons.append(f"{label}:catalog_path")
            if str(replay.get("pack_path", "")).strip() != expected_pack_path:
                stale_reasons.append(f"{label}:pack_path")
        if stale_reasons:
            payload["stale_reasons"] = stale_reasons
            _emit(payload, json_only=args.json_only)
            return 1
    except Exception as exc:
        payload["stale_reasons"] = [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["resolve_identity_context_default_local_catalog_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
