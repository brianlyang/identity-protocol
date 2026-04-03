#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from protocol_infra_contract import (
    GATEWAY_WRAPPER_LONG_RUNNING_UPDATE_REQUIRED_SCRIPTS,
    GATEWAY_WRAPPER_LONG_RUNNING_UPDATE_TIMEOUT_SECONDS,
    GATEWAY_WRAPPER_TIMEOUT_PROFILE_REQUIREMENTS,
    GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_TIMEOUT_PROFILE = "IP-GW-TIMEOUT-001"


def _profile_map() -> dict[str, int]:
    out: dict[str, int] = {}
    for script_name, timeout_seconds in GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS:
        name = str(script_name or "").strip()
        if not name:
            continue
        out[name] = int(timeout_seconds)
    return out


def _required_profile_map() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for script_name, minimum_timeout_seconds, requirement_family in GATEWAY_WRAPPER_TIMEOUT_PROFILE_REQUIREMENTS:
        name = str(script_name or "").strip()
        if not name:
            continue
        out[name] = {
            "minimum_timeout_seconds": int(minimum_timeout_seconds),
            "requirement_family": str(requirement_family or "").strip(),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate gateway timeout profile coverage for long-running update entrypoints.")
    ap.add_argument(
        "--script",
        action="append",
        default=[],
        help="explicit script path to require in timeout profile (repeatable); defaults to canonical timeout-profile requirement surfaces",
    )
    ap.add_argument(
        "--min-timeout",
        type=int,
        default=0,
        help="override minimum timeout in seconds for explicit --script checks",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    explicit_scripts = [str(item).strip() for item in list(args.script or []) if str(item).strip()]
    required_profile_map = _required_profile_map()
    profile_map = _profile_map()
    if explicit_scripts:
        minimum_timeout = int(args.min_timeout or GATEWAY_WRAPPER_LONG_RUNNING_UPDATE_TIMEOUT_SECONDS)
        requirements = {
            script: {
                "minimum_timeout_seconds": minimum_timeout,
                "requirement_family": "explicit_cli",
            }
            for script in explicit_scripts
        }
    else:
        requirements = required_profile_map
        minimum_timeout = max(
            [int(row["minimum_timeout_seconds"]) for row in required_profile_map.values()]
            or [int(GATEWAY_WRAPPER_LONG_RUNNING_UPDATE_TIMEOUT_SECONDS)]
        )

    required_scripts = list(requirements.keys())
    missing_scripts = [script for script in required_scripts if script not in profile_map]
    underprovisioned_scripts = [
        {
            "script": script,
            "configured_timeout_seconds": int(profile_map.get(script, 0)),
            "minimum_timeout_seconds": int(requirements.get(script, {}).get("minimum_timeout_seconds", 0)),
            "requirement_family": str(requirements.get(script, {}).get("requirement_family", "")).strip(),
        }
        for script in required_scripts
        if script in profile_map
        and int(profile_map.get(script, 0)) < int(requirements.get(script, {}).get("minimum_timeout_seconds", 0))
    ]
    status = STATUS_PASS_REQUIRED if not missing_scripts and not underprovisioned_scripts else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        "gateway_timeout_profile_coverage_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_TIMEOUT_PROFILE,
        "required_scripts": required_scripts,
        "minimum_timeout_seconds": minimum_timeout,
        "profile_entry_count": len(profile_map),
        "profile_map": profile_map,
        "required_profile_requirements": requirements,
        "missing_scripts": missing_scripts,
        "underprovisioned_scripts": underprovisioned_scripts,
        "stale_reasons": (
            [f"missing_timeout_profile:{script}" for script in missing_scripts]
            + [
                f"underprovisioned_timeout_profile:{row['script']}:{row['configured_timeout_seconds']}<min:{row['minimum_timeout_seconds']}"
                for row in underprovisioned_scripts
            ]
        ),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
