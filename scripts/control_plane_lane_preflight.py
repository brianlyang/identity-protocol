#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    EXPECTED_ALLOWED_ACTIONS,
    dump_yaml,
    emit,
    get_lane,
    resolve_registry_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--lane-id", default=ACTIVE_LANE_ID)
    parser.add_argument("--write-back", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        lane = get_lane(bundle.registry_doc, args.lane_id)
        previous_status = lane.get("status", "architect_ready")
        transition = {"from": previous_status, "to": previous_status}
        if args.write_back and previous_status != "preflight_passed":
            lane["status"] = "preflight_passed"
            transition["to"] = "preflight_passed"
            dump_yaml(bundle.versioned_registry, bundle.registry_doc)
        payload = {
            "status": "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "scope_lock_status": "LOCKED",
            "allowed_next_actions": EXPECTED_ALLOWED_ACTIONS,
            "status_transition": transition,
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
