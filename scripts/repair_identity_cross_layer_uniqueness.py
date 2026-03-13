#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from resolve_identity_context import (
    _default_user_identity_home,
    _detect_repo_root,
    _project_identity_home_from_repo_catalog,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CROSS_LAYER_DUPLICATE = "IP-SCOPE-LAYER-001"
ERR_APPLY_WRITE_DENIED = "IP-SCOPE-LAYER-002"
ERR_IDENTITY_MISSING = "IP-SCOPE-LAYER-003"


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _find_row(catalog: dict[str, Any], identity_id: str) -> tuple[int, dict[str, Any]]:
    rows = catalog.get("identities") or []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() == identity_id:
            return idx, row
    return -1, {}


def _is_runtime_row(row: dict[str, Any]) -> bool:
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile != "fixture" and runtime_mode != "demo_only"


def _is_active_row(row: dict[str, Any]) -> bool:
    return str((row or {}).get("status", "")).strip().lower() in {"active", "enabled", "on"}


def _resolve_project_catalog_from_repo(repo_catalog: Path) -> Path:
    repo_catalog = repo_catalog.expanduser().resolve()
    repo_root = _detect_repo_root(repo_catalog.parent)
    project_identity_home = _project_identity_home_from_repo_catalog(repo_root, repo_catalog)
    return (project_identity_home / "catalog.local.yaml").resolve()


def _resolve_global_catalog() -> Path:
    return (_default_user_identity_home() / "catalog.local.yaml").resolve()


def _emit(payload: dict[str, Any], json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Repair cross-layer identity uniqueness by enforcing a single active runtime owner per identity_id."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--project-catalog", default="")
    ap.add_argument("--global-catalog", default="")
    ap.add_argument("--prefer-layer", choices=["project", "global"], default="project")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_catalog = Path(args.repo_catalog).expanduser().resolve()
    project_catalog_path = (
        Path(args.project_catalog).expanduser().resolve()
        if str(args.project_catalog or "").strip()
        else _resolve_project_catalog_from_repo(repo_catalog)
    )
    global_catalog_path = (
        Path(args.global_catalog).expanduser().resolve()
        if str(args.global_catalog or "").strip()
        else _resolve_global_catalog()
    )

    project_doc = _load_yaml(project_catalog_path)
    global_doc = _load_yaml(global_catalog_path)
    p_idx, p_row = _find_row(project_doc, args.identity_id)
    g_idx, g_row = _find_row(global_doc, args.identity_id)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "project_catalog": str(project_catalog_path),
        "global_catalog": str(global_catalog_path),
        "prefer_layer": args.prefer_layer,
        "apply": bool(args.apply),
        "project_entry_exists": p_idx >= 0,
        "global_entry_exists": g_idx >= 0,
        "project_runtime": _is_runtime_row(p_row),
        "global_runtime": _is_runtime_row(g_row),
        "project_active": _is_active_row(p_row),
        "global_active": _is_active_row(g_row),
        "project_pack_path": str(p_row.get("pack_path", "")),
        "global_pack_path": str(g_row.get("pack_path", "")),
        "status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "actions": [],
        "stale_reasons": [],
    }

    if p_idx < 0 and g_idx < 0:
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_IDENTITY_MISSING
        payload["stale_reasons"].append("identity_not_found_in_project_or_global_catalog")
        _emit(payload, args.json_only)
        return 1

    duplicate_runtime_active = (
        p_idx >= 0
        and g_idx >= 0
        and _is_runtime_row(p_row)
        and _is_runtime_row(g_row)
        and _is_active_row(p_row)
        and _is_active_row(g_row)
    )
    if not duplicate_runtime_active:
        payload["stale_reasons"].append("no_cross_layer_active_runtime_duplicate_detected")
        _emit(payload, args.json_only)
        return 0

    payload["status"] = STATUS_FAIL_REQUIRED
    payload["error_code"] = ERR_CROSS_LAYER_DUPLICATE
    payload["stale_reasons"].append("cross_layer_active_runtime_duplicate_detected")

    if not args.apply:
        _emit(payload, args.json_only)
        return 1

    preferred = args.prefer_layer
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if preferred == "project":
        target_doc = global_doc
        target_path = global_catalog_path
        target_idx = g_idx
        target_row = dict(g_row)
    else:
        target_doc = project_doc
        target_path = project_catalog_path
        target_idx = p_idx
        target_row = dict(p_row)

    if target_idx < 0:
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_APPLY_WRITE_DENIED
        payload["stale_reasons"].append("preferred_keep_layer_missing_target_to_deactivate_not_found")
        _emit(payload, args.json_only)
        return 1

    if not (target_path.exists() and os.access(target_path, os.W_OK)):
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_APPLY_WRITE_DENIED
        payload["stale_reasons"].append(f"target_catalog_not_writable:{target_path}")
        _emit(payload, args.json_only)
        return 1

    target_row["status"] = "inactive"
    target_row["deactivated_by"] = "repair_identity_cross_layer_uniqueness.py"
    target_row["deactivated_at"] = now_utc
    target_row["deactivation_reason"] = "cross_layer_runtime_uniqueness_enforcement"
    (target_doc.get("identities") or [])[target_idx] = target_row
    target_doc["updated_at"] = now_utc.split("T", 1)[0]
    _write_yaml(target_path, target_doc)

    payload["status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["actions"].append(
        {
            "action": "deactivate_duplicate_layer_entry",
            "catalog": str(target_path),
            "identity_id": args.identity_id,
            "deactivated_layer": "global" if preferred == "project" else "project",
            "kept_layer": preferred,
        }
    )
    payload["stale_reasons"] = []
    _emit(payload, args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
