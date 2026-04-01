#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    EXPECTED_TERMINAL_STATUS,
    dump_yaml,
    emit,
    get_lane,
    resolve_registry_bundle,
    route_next_role,
    validate_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--lane-id", default=ACTIVE_LANE_ID)
    parser.add_argument("--receipt-file", required=True)
    parser.add_argument("--write-back", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        lane = get_lane(bundle.registry_doc, args.lane_id)
        receipt = json.loads(Path(args.receipt_file).read_text(encoding="utf-8"))
        failures = validate_receipt(receipt, require_exact=True, repo_root_path=bundle.repo_root)
        if failures:
            emit(
                {
                    "status": "FAIL_REQUIRED",
                    "failure_tokens": failures,
                    "fail_close_token": lane["fail_close_token"],
                },
                json_only=args.json_only,
            )
            return 1
        previous_status = lane.get("status", "architect_ready")
        if args.write_back:
            lane["status"] = EXPECTED_TERMINAL_STATUS
            dump_yaml(bundle.versioned_registry, bundle.registry_doc)
        payload = {
            "status": "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "previous_status": previous_status,
            "new_status": EXPECTED_TERMINAL_STATUS,
            "commit_resolved": True,
            "next_role": route_next_role(lane, status_override=EXPECTED_TERMINAL_STATUS),
            "normalized_receipt": {
                "validator_result": receipt["validator_result"],
                "probe_result": receipt["probe_result"],
                "staged_paths": receipt["staged_paths"],
                "commit_id": receipt["commit_id"],
            },
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
