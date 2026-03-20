#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path, PurePosixPath
from typing import Any

from create_identity_pack import (
    INSTANCE_PACK_TOPOLOGY_CONTRACT_ID,
    INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY,
    INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-IPACK-001"
ERR_CONTRACT_INVALID = "IP-IPACK-002"
ERR_TOPOLOGY_DRIFT = "IP-IPACK-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _expand_pattern(pattern: str, identity_id: str) -> str:
    return str(pattern or "").strip().replace("<identity-id>", identity_id)


def _normalize_rel_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _list_dirs(pack_root: Path) -> list[str]:
    dirs: list[str] = []
    for path in sorted(pack_root.rglob("*")):
        if not path.is_dir():
            continue
        rel = _normalize_rel_path(path, pack_root)
        if rel != ".":
            dirs.append(rel)
    return dirs


def _match_any(token: str, patterns: list[str], identity_id: str) -> bool:
    return any(fnmatch.fnmatch(token, _expand_pattern(pattern, identity_id)) for pattern in patterns)


def _resolve_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in (
        INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY,
        "instance_pack_topology_contract",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node, key
    return {}, INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity pack topology and root scripts surface.")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--current-task", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_raw = str(args.catalog or "").strip()
    catalog_path = Path(catalog_raw).expanduser().resolve() if catalog_raw else None

    try:
        if str(args.current_task or "").strip():
            task_path = Path(str(args.current_task).strip()).expanduser().resolve()
            pack_root = task_path.parent.resolve()
            task = load_json(task_path)
        else:
            if catalog_path is None or not catalog_path.exists():
                missing_catalog = catalog_path if catalog_path is not None else "<missing>"
                print(f"[FAIL] catalog not found: {missing_catalog}")
                return 2
            pack_root, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
            task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract, contract_key = _resolve_contract(task)
    required = contract_required(contract)
    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path) if catalog_path is not None else "",
        "resolved_pack_path": str(pack_root),
        "task_path": str(task_path),
        "required_contract": required,
        "contract_key": contract_key,
        "instance_pack_topology_status": STATUS_SKIPPED_NOT_REQUIRED,
        "pack_root_dir_lock_status": STATUS_SKIPPED_NOT_REQUIRED,
        "runtime_dir_lock_status": STATUS_SKIPPED_NOT_REQUIRED,
        "scripts_surface_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "missing_required_file_rows": [],
        "missing_required_dir_rows": [],
        "unknown_dir_rows": [],
        "forbidden_dir_rows": [],
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["instance_pack_topology_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    if str(contract.get("contract_id", "")).strip() != INSTANCE_PACK_TOPOLOGY_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if str(contract.get("validator", "")).strip() != INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID:
        issues.append("validator_mismatch")
    if str(contract.get("fail_mode", "")).strip().lower() != "fail_required":
        issues.append("fail_mode_not_fail_required")

    required_files = _clean_list(contract.get("pack_root_required_files"))
    required_root_dirs = _clean_list(contract.get("pack_root_required_dirs"))
    optional_root_dirs = _clean_list(contract.get("pack_root_optional_dirs"))
    legacy_root_dirs = _clean_list(contract.get("pack_root_legacy_compat_dirs"))
    required_runtime_dirs = _clean_list(contract.get("runtime_required_dirs"))
    optional_runtime_dirs = _clean_list(contract.get("runtime_optional_dirs"))
    forbidden_dir_patterns = _clean_list(contract.get("forbidden_dir_patterns"))

    scripts_surface = contract.get("scripts_surface")
    if not isinstance(scripts_surface, dict):
        issues.append("scripts_surface_missing")
        scripts_surface = {}

    if not required_files:
        issues.append("pack_root_required_files_missing")
    if not required_root_dirs:
        issues.append("pack_root_required_dirs_missing")
    if not required_runtime_dirs:
        issues.append("runtime_required_dirs_missing")

    scripts_root = str(scripts_surface.get("root_dir", "")).strip()
    if scripts_root != "scripts":
        issues.append("scripts_surface_root_dir_not_scripts")
    if scripts_surface.get("must_live_at_pack_root") is not True:
        issues.append("scripts_surface_must_live_at_pack_root_not_true")
    if scripts_surface.get("must_not_live_under_runtime") is not True:
        issues.append("scripts_surface_must_not_live_under_runtime_not_true")

    if issues:
        payload["instance_pack_topology_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    actual_dirs = _list_dirs(pack_root)
    allowed_dir_patterns = required_root_dirs + optional_root_dirs + legacy_root_dirs + required_runtime_dirs + optional_runtime_dirs

    missing_files = [row for row in required_files if not (pack_root / row).exists()]
    missing_dirs = []
    for pattern in required_root_dirs + required_runtime_dirs:
        expanded = _expand_pattern(pattern, args.identity_id)
        if expanded not in actual_dirs:
            missing_dirs.append(expanded)

    forbidden_rows: list[str] = []
    unknown_rows: list[str] = []
    for rel in actual_dirs:
        parts = PurePosixPath(rel).parts
        if any(part in {"__pycache__", ".pytest_cache"} for part in parts):
            forbidden_rows.append(f"forbidden_dir:{rel}")
            continue
        if _match_any(rel, forbidden_dir_patterns, args.identity_id):
            forbidden_rows.append(f"forbidden_dir:{rel}")
            continue
        if not _match_any(rel, allowed_dir_patterns, args.identity_id):
            unknown_rows.append(f"unregistered_dir:{rel}")

    scripts_surface_issues: list[str] = []
    scripts_dir = pack_root / scripts_root
    runtime_scripts_dir = pack_root / "runtime" / "scripts"
    if not scripts_dir.is_dir():
        scripts_surface_issues.append("scripts_root_missing")
    if runtime_scripts_dir.exists():
        scripts_surface_issues.append("runtime_scripts_forbidden_present")

    stale_reasons: list[str] = []
    stale_reasons.extend(f"missing_required_file:{row}" for row in missing_files)
    stale_reasons.extend(f"missing_required_dir:{row}" for row in missing_dirs)
    stale_reasons.extend(unknown_rows)
    stale_reasons.extend(forbidden_rows)
    stale_reasons.extend(scripts_surface_issues)

    payload["missing_required_file_rows"] = sorted(missing_files)
    payload["missing_required_dir_rows"] = sorted(missing_dirs)
    payload["unknown_dir_rows"] = sorted(unknown_rows)
    payload["forbidden_dir_rows"] = sorted(forbidden_rows + scripts_surface_issues)
    payload["pack_root_dir_lock_status"] = STATUS_FAIL_REQUIRED if any(not row.startswith("unregistered_dir:runtime/") for row in unknown_rows + forbidden_rows) or missing_files else STATUS_PASS_REQUIRED
    payload["runtime_dir_lock_status"] = STATUS_FAIL_REQUIRED if any(row.startswith("unregistered_dir:runtime/") or row.startswith("forbidden_dir:runtime/") for row in unknown_rows + forbidden_rows) or any(row.startswith("runtime/") for row in missing_dirs) else STATUS_PASS_REQUIRED
    payload["scripts_surface_status"] = STATUS_FAIL_REQUIRED if scripts_surface_issues else STATUS_PASS_REQUIRED

    if stale_reasons:
        payload["instance_pack_topology_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TOPOLOGY_DRIFT
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["instance_pack_topology_status"] = STATUS_PASS_REQUIRED
    payload["pack_root_dir_lock_status"] = STATUS_PASS_REQUIRED
    payload["runtime_dir_lock_status"] = STATUS_PASS_REQUIRED
    payload["scripts_surface_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
