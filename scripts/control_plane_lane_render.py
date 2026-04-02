#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    display_path,
    emit,
    get_lane,
    resolve_owner_bindings,
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
        payload = {
            "status": "PASS_REQUIRED",
            "requested_lane_id": args.lane_id,
            "active_lane_id": bundle.current_doc.get("active_lane_id"),
            "lane_card": lane,
            "authoritative_checkout": bundle.registry_doc.get("authoritative_checkout", {}),
            "canonical_runtime_tuple_policy": bundle.registry_doc.get("canonical_runtime_tuple_policy", {}),
            "owner_binding_overlay": {
                "current_file": display_path(bundle.owner_binding_current, bundle.repo_root),
                "versioned_file": display_path(bundle.owner_binding_versioned, bundle.repo_root),
                "truth_class": bundle.owner_binding_current_doc.get("truth_class"),
                "scope": bundle.owner_binding_current_doc.get("scope"),
                "portable": bundle.owner_binding_current_doc.get("portable"),
                "binding_policy": bundle.owner_binding_current_doc.get("binding_policy"),
                "active_binding_id": bundle.owner_binding_current_doc.get("active_binding_id"),
                "role_to_identity_bindings": resolve_owner_bindings(bundle),
            },
            "next_role_projection": route_next_role(
                lane,
                bundle=bundle,
                status_override=args.status_override or lane.get("status"),
            ),
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
