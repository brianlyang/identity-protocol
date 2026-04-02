#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    emit,
    get_lane,
    resolve_registry_bundle,
    route_next_role,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--lane-id", default=ACTIVE_LANE_ID)
    parser.add_argument("--status-override")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        lane = get_lane(bundle.registry_doc, args.lane_id)
        next_role = route_next_role(
            lane,
            bundle=bundle,
            status_override=args.status_override or lane.get("status"),
        )
        payload = {
            "status": "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "active_lane_id": bundle.current_doc.get("active_lane_id"),
            "execution_mode": lane["execution_mode"],
            "next_role": next_role,
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
