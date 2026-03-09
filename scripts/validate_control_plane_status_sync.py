#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from render_control_plane_status import build_status

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STATUS_SYNC = "IP-CP-STATUS-001"

VOLATILE_TOP_LEVEL_KEYS = {"generated_at_utc", "git_head_short"}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _canonicalize(doc: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in doc.items() if k not in VOLATILE_TOP_LEVEL_KEYS}
    return out


def _index_checks(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = doc.get("checks")
    if not isinstance(checks, list):
        return {}
    out: dict[str, dict[str, Any]] = {}
    for node in checks:
        if not isinstance(node, dict):
            continue
        name = str(node.get("name", "")).strip()
        if not name:
            continue
        out[name] = node
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate machine-generated control-plane status artifact is in sync.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--status-file",
        default="identity/protocol/mappings/control-plane-status.v1.6.json",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    status_path = (repo_root / str(args.status_file)).resolve()
    stale_reasons: list[str] = []
    mismatches: list[dict[str, Any]] = []

    if not status_path.exists():
        stale_reasons.append(f"status_file_missing:{status_path}")
        current_doc: dict[str, Any] = {}
    else:
        current_doc = _load_json(status_path)

    live_doc = build_status(repo_root)
    current_norm = _canonicalize(current_doc)
    live_norm = _canonicalize(live_doc)

    if current_doc:
        if current_norm.get("control_plane_status") != live_norm.get("control_plane_status"):
            mismatches.append(
                {
                    "field": "control_plane_status",
                    "expected": live_norm.get("control_plane_status"),
                    "actual": current_norm.get("control_plane_status"),
                    "reason": "status_drift",
                }
            )
        if bool(current_norm.get("promotion_ready")) != bool(live_norm.get("promotion_ready")):
            mismatches.append(
                {
                    "field": "promotion_ready",
                    "expected": bool(live_norm.get("promotion_ready")),
                    "actual": bool(current_norm.get("promotion_ready")),
                    "reason": "promotion_flag_drift",
                }
            )

        current_checks = _index_checks(current_norm)
        live_checks = _index_checks(live_norm)
        if set(current_checks.keys()) != set(live_checks.keys()):
            mismatches.append(
                {
                    "field": "checks.name_set",
                    "expected": sorted(live_checks.keys()),
                    "actual": sorted(current_checks.keys()),
                    "reason": "check_set_drift",
                }
            )
        for name in sorted(set(current_checks.keys()) & set(live_checks.keys())):
            current_check = current_checks[name]
            live_check = live_checks[name]
            for key in ("status", "error_code", "rc"):
                if current_check.get(key) != live_check.get(key):
                    mismatches.append(
                        {
                            "field": f"checks.{name}.{key}",
                            "expected": live_check.get(key),
                            "actual": current_check.get(key),
                            "reason": "check_result_drift",
                        }
                    )
            if current_check.get("payload") != live_check.get("payload"):
                mismatches.append(
                    {
                        "field": f"checks.{name}.payload",
                        "reason": "check_payload_drift",
                    }
                )

    if stale_reasons or mismatches:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_STATUS_SYNC
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "control_plane_status_sync_status": status,
        "error_code": error_code,
        "status_file": str(status_path),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "stale_reasons": stale_reasons,
        "live_control_plane_status": live_norm.get("control_plane_status"),
        "file_control_plane_status": current_norm.get("control_plane_status"),
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-STATUS-SYNC] status={status} "
            f"mismatches={len(mismatches)} "
            f"stale={len(stale_reasons)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
