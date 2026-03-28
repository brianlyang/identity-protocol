#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_shared_primitive_adoption_common import (
    scan_root_validator_shared_primitive_adoption,
)


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_KEY = "protocol_root_shared_primitive_adoption_status"
ERR_SCAN = "IP-RSPA-001"
ERR_BINDING = "IP-RSPA-002"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate root validator/probe surfaces remain bound to shared primitives."
        )
    )
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    scan = scan_root_validator_shared_primitive_adoption(repo_root)
    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_SCAN,
        "repo_root": str(repo_root),
        **scan,
        "stale_reasons": [],
    }

    if int(payload.get("root_validator_count", 0) or 0) <= 0:
        payload["stale_reasons"].append("root_validator_files_missing")
    if int(payload.get("root_probe_count", 0) or 0) <= 0:
        payload["stale_reasons"].append("root_probe_files_missing")
    for row in payload.get("scan_errors") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(f"scan_error:{rel_path}:{reason}")
    for row in payload.get("root_probe_scan_errors") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(f"root_probe_scan_error:{rel_path}:{reason}")
    for row in payload.get("root_probe_shadow_common_scan_errors") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(
            f"root_probe_shadow_common_scan_error:{rel_path}:{reason}"
        )
    for row in payload.get("primitive_binding_violations") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        primitive_name = str(row.get("primitive_name") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(
            f"primitive_binding_violation:{rel_path}:{primitive_name}:{reason}"
        )
    for row in payload.get("root_probe_shadow_violation_rows") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(
            f"root_probe_shadow_violation:{rel_path}:{reason}"
        )
    for row in payload.get("root_probe_shadow_common_violation_rows") or []:
        rel_path = str(row.get("rel_path") or "").strip()
        contract_id = str(row.get("contract_id") or "").strip()
        reason = str(row.get("reason") or "").strip() or "unknown"
        payload["stale_reasons"].append(
            f"root_probe_shadow_common_violation:{rel_path}:{contract_id}:{reason}"
        )
    if int(payload.get("row_family_projection_assignment_violation_count", 0) or 0) > 0:
        violation_rows = payload.get("row_family_projection_assignment_violation_rows")
        if not isinstance(violation_rows, list):
            violation_rows = payload.get("row_family_projection_assignment_rows") or []
        for row in violation_rows:
            assignment_mode = str(row.get("assignment_mode") or "").strip()
            if not bool(row.get("violation")) and assignment_mode in {
                "shared_primitive_call",
                "initializer_empty_list",
            }:
                continue
            rel_path = str(row.get("rel_path") or "").strip()
            binding = str(row.get("binding") or "").strip()
            payload["stale_reasons"].append(
                f"row_family_projection_assignment_violation:{rel_path}:{assignment_mode}:{binding}"
            )

    if payload["stale_reasons"]:
        payload["error_code"] = (
            ERR_BINDING
            if payload.get("primitive_binding_violations")
            or payload.get("root_probe_shadow_violation_rows")
            or payload.get("root_probe_shadow_common_violation_rows")
            or int(payload.get("row_family_projection_assignment_violation_count", 0) or 0)
            > 0
            else ERR_SCAN
        )
    else:
        payload[STATUS_KEY] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""

    _emit(payload, json_only=args.json_only)
    return 0 if payload[STATUS_KEY] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
