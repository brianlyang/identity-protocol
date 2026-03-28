#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from render_control_plane_budget import (
    DEFAULT_BUDGET_ENTRY,
    build_budget_snapshot,
    persist_budget_snapshot,
    resolve_budget_target,
)
from render_control_plane_status import (
    DEFAULT_STATUS_ENTRY,
    STATUS_FAIL_REQUIRED as CONTROL_PLANE_STATUS_FAIL_REQUIRED,
    build_status,
    persist_status_payload,
    resolve_status_target,
)
from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_CONTROL_PLANE_MATERIALIZATION = "IP-CP-MAT-001"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _extract_json_blob(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        obj = json.loads(raw[start : end + 1])
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def _run_json_command(repo_root: Path, command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(command, cwd=str(repo_root), capture_output=True, text=True, check=False)
    payload = _extract_json_blob(proc.stdout)
    return {
        "command": list(command),
        "rc": int(proc.returncode),
        "payload": payload,
    }


def _first_status(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(payload.get(key, "")).strip()
        if value:
            return value
    return ""


def _stale_reasons(payload: dict[str, Any]) -> list[str]:
    reasons = payload.get("stale_reasons") or []
    if isinstance(reasons, list):
        return [str(item).strip() for item in reasons if str(item).strip()]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize the control-plane budget/status surfaces through the canonical "
            "machine-owned sequence: budget refresh first, then status refresh, then sync revalidation."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--budget-file", default=DEFAULT_BUDGET_ENTRY)
    parser.add_argument("--status-file", default=DEFAULT_STATUS_ENTRY)
    parser.add_argument("--check-name", action="append", default=[])
    parser.add_argument("--allow-partial-status-write", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    selected_check_names = tuple(str(name).strip() for name in (args.check_name or []) if str(name).strip())

    budget_snapshot = build_budget_snapshot(repo_root, budget_file=str(args.budget_file))
    budget_path, budget_active_file, budget_alias_error = resolve_budget_target(
        repo_root,
        budget_file=str(args.budget_file),
    )
    status_path, status_active_file, status_alias_error = resolve_status_target(
        repo_root,
        status_file=str(args.status_file),
    )

    payload: dict[str, Any] = {
        "materialize_control_plane_surfaces_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_CONTROL_PLANE_MATERIALIZATION,
        "repo_root": str(repo_root),
        "write_requested": bool(args.write),
        "allow_partial_status_write": bool(args.allow_partial_status_write),
        "write_applied": False,
        "budget_write_applied": False,
        "status_write_applied": False,
        "budget_entry_file": str(budget_snapshot.get("budget_entry_file") or ""),
        "budget_file": str(budget_path),
        "budget_file_active_file": budget_active_file,
        "budget_file_alias_error": budget_alias_error,
        "status_file": str(status_path),
        "status_file_active_file": status_active_file,
        "status_file_alias_error": status_alias_error,
        "selected_check_names": list(selected_check_names),
        "budget_render_status": STATUS_FAIL_REQUIRED,
        "control_plane_status": STATUS_FAIL_REQUIRED,
        "promotion_ready": False,
        "budget_validation_status": STATUS_FAIL_REQUIRED,
        "budget_sync_status": STATUS_FAIL_REQUIRED,
        "status_sync_status": STATUS_FAIL_REQUIRED,
        "budget_sync_mismatch_count": 0,
        "status_sync_mismatch_count": 0,
        "budget_sync_stale_reasons": [],
        "status_sync_stale_reasons": [],
        "budget_render": {},
        "status_render": {},
        "budget_validation": {},
        "budget_sync_validation": {},
        "status_sync_validation": {},
        "stale_reasons": list(budget_snapshot.get("stale_reasons") or []),
    }

    if budget_alias_error:
        payload["stale_reasons"].append(f"budget_alias_error:{budget_alias_error}")
    if status_alias_error:
        payload["stale_reasons"].append(f"status_alias_error:{status_alias_error}")
    if not status_path.exists() or not status_path.is_file():
        payload["stale_reasons"].append("status_file_missing")
    if not budget_path.exists() or not budget_path.is_file():
        payload["stale_reasons"].append("budget_file_missing")
    if args.write and selected_check_names and not args.allow_partial_status_write:
        payload["stale_reasons"].append("partial_status_write_forbidden")

    payload["budget_render"] = {
        "observed": dict(budget_snapshot.get("observed") or {}),
        "before_last_updated_utc": str((budget_snapshot.get("current_doc") or {}).get("last_updated_utc", "")),
        "after_last_updated_utc": str((budget_snapshot.get("next_doc") or {}).get("last_updated_utc", "")),
    }

    if payload["stale_reasons"]:
        _emit(payload, json_only=args.json_only)
        return 1

    payload["budget_render_status"] = STATUS_PASS_REQUIRED
    if args.write:
        persist_budget_snapshot(budget_snapshot)
        payload["budget_write_applied"] = True

    status_render = build_status(repo_root, include_check_names=selected_check_names)
    payload["status_render"] = status_render
    payload["control_plane_status"] = str(status_render.get("control_plane_status", "")).strip() or STATUS_FAIL_REQUIRED
    payload["promotion_ready"] = bool(status_render.get("promotion_ready", False))
    if args.write:
        try:
            persist_status_payload(
                status_path,
                status_render,
                repo_root=repo_root,
                include_check_names=selected_check_names,
            )
        except ValueError as exc:
            payload["stale_reasons"].append(f"status_write_failed:{exc}")
            _emit(payload, json_only=args.json_only)
            return 1
        payload["status_write_applied"] = True
    payload["write_applied"] = bool(payload["budget_write_applied"] or payload["status_write_applied"])

    budget_validation = _run_json_command(
        repo_root,
        ["python3", "scripts/validate_control_plane_budget.py", "--json-only"],
    )
    budget_sync = _run_json_command(
        repo_root,
        ["python3", "scripts/validate_control_plane_budget_sync.py", "--json-only"],
    )
    status_sync_command = ["python3", "scripts/validate_control_plane_status_sync.py", "--json-only"]
    for check_name in selected_check_names:
        status_sync_command.extend(["--check-name", check_name])
    status_sync = _run_json_command(repo_root, status_sync_command)

    budget_validation_payload = budget_validation.get("payload") or {}
    budget_sync_payload = budget_sync.get("payload") or {}
    status_sync_payload = status_sync.get("payload") or {}

    payload["budget_validation"] = budget_validation
    payload["budget_sync_validation"] = budget_sync
    payload["status_sync_validation"] = status_sync
    payload["budget_validation_status"] = (
        _first_status(budget_validation_payload, "control_plane_budget_status")
        or (STATUS_PASS_REQUIRED if budget_validation["rc"] == 0 else STATUS_FAIL_REQUIRED)
    )
    payload["budget_sync_status"] = (
        _first_status(budget_sync_payload, "control_plane_budget_sync_status")
        or (STATUS_PASS_REQUIRED if budget_sync["rc"] == 0 else STATUS_FAIL_REQUIRED)
    )
    payload["status_sync_status"] = (
        _first_status(status_sync_payload, "control_plane_status_sync_status")
        or (STATUS_PASS_REQUIRED if status_sync["rc"] == 0 else STATUS_FAIL_REQUIRED)
    )
    payload["budget_sync_mismatch_count"] = int(budget_sync_payload.get("mismatch_count", 0) or 0)
    payload["status_sync_mismatch_count"] = int(status_sync_payload.get("mismatch_count", 0) or 0)
    payload["budget_sync_stale_reasons"] = _stale_reasons(budget_sync_payload)
    payload["status_sync_stale_reasons"] = _stale_reasons(status_sync_payload)

    final_fail = any(
        status != STATUS_PASS_REQUIRED
        for status in (
            payload["budget_validation_status"],
            payload["budget_sync_status"],
            payload["status_sync_status"],
        )
    ) or payload["control_plane_status"] == CONTROL_PLANE_STATUS_FAIL_REQUIRED

    if not final_fail:
        payload["materialize_control_plane_surfaces_status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
    else:
        if payload["control_plane_status"] == CONTROL_PLANE_STATUS_FAIL_REQUIRED:
            payload["stale_reasons"].append("rendered_control_plane_status_fail_required")
        if payload["budget_validation_status"] != STATUS_PASS_REQUIRED:
            payload["stale_reasons"].append("budget_validation_not_green")
        if payload["budget_sync_status"] != STATUS_PASS_REQUIRED:
            payload["stale_reasons"].append("budget_sync_not_green")
        if payload["status_sync_status"] != STATUS_PASS_REQUIRED:
            payload["stale_reasons"].append("status_sync_not_green")

    _emit(payload, json_only=args.json_only)
    return 0 if payload["materialize_control_plane_surfaces_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
