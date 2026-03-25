#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from render_control_plane_budget import DEFAULT_BUDGET_ENTRY, build_budget_snapshot

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_BUDGET_SYNC = "IP-CP-BUDGET-002"
VOLATILE_KEYS = {"last_updated_utc", "baseline_snapshot_utc"}


def _canonicalize(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, node in value.items():
            key_str = str(key)
            if key_str in VOLATILE_KEYS:
                continue
            normalized[key_str] = _canonicalize(node)
        return normalized
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value


def _diff(expected: Any, actual: Any, *, path: str = "") -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        all_keys = sorted(set(expected.keys()) | set(actual.keys()))
        for key in all_keys:
            child_path = f"{path}.{key}" if path else str(key)
            if key not in expected:
                mismatches.append(
                    {
                        "field": child_path,
                        "expected": None,
                        "actual": actual.get(key),
                        "reason": "unexpected_field_present",
                    }
                )
                continue
            if key not in actual:
                mismatches.append(
                    {
                        "field": child_path,
                        "expected": expected.get(key),
                        "actual": None,
                        "reason": "expected_field_missing",
                    }
                )
                continue
            mismatches.extend(_diff(expected.get(key), actual.get(key), path=child_path))
        return mismatches
    if isinstance(expected, list) and isinstance(actual, list):
        if expected != actual:
            mismatches.append(
                {
                    "field": path or "list",
                    "expected": expected,
                    "actual": actual,
                    "reason": "list_value_drift",
                }
            )
        return mismatches
    if expected != actual:
        mismatches.append(
            {
                "field": path or "value",
                "expected": expected,
                "actual": actual,
                "reason": "value_drift",
            }
        )
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-plane budget artifact stays synced with live rendered metrics.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--budget-file", default=DEFAULT_BUDGET_ENTRY)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    snapshot = build_budget_snapshot(repo_root, budget_file=str(args.budget_file))
    stale_reasons = list(snapshot.get("stale_reasons") or [])

    current_doc = snapshot.get("current_doc") or {}
    next_doc = snapshot.get("next_doc") or {}
    current_norm = _canonicalize(current_doc)
    next_norm = _canonicalize(next_doc)
    mismatches = [] if stale_reasons else _diff(next_norm, current_norm)

    status = STATUS_PASS_REQUIRED if not stale_reasons and not mismatches else STATUS_FAIL_REQUIRED
    payload = {
        "control_plane_budget_sync_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_BUDGET_SYNC,
        "repo_root": str(repo_root),
        "budget_entry_file": snapshot.get("budget_entry_file", ""),
        "budget_file": snapshot.get("budget_file", ""),
        "budget_file_active_file": snapshot.get("budget_file_active_file", ""),
        "budget_file_alias_error": snapshot.get("budget_file_alias_error", ""),
        "current_last_updated_utc": str((current_doc or {}).get("last_updated_utc", "")),
        "live_last_updated_utc": str((next_doc or {}).get("last_updated_utc", "")),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "observed": snapshot.get("observed", {}),
        "stale_reasons": stale_reasons,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
