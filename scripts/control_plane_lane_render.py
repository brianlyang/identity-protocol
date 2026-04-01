#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import ACTIVE_LANE_ID, emit, get_lane, resolve_registry_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--lane-id", default=ACTIVE_LANE_ID)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        lane = get_lane(bundle.registry_doc, args.lane_id)
        payload = {
            "status": "PASS_REQUIRED",
            "lane_card": lane,
            "authoritative_checkout_binding": bundle.registry_doc.get("authoritative_checkout", {}),
            "canonical_runtime_tuple_policy": bundle.registry_doc.get("canonical_runtime_tuple_policy", {}),
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
