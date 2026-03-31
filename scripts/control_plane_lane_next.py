#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import emit, get_lane, load_registry_bundle, normalize_registry_doc, route_next_role


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve the next concrete role for a control-plane lane.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry-current", default="")
    parser.add_argument("--lane-id", default="")
    parser.add_argument("--status-override", default="")
    parser.add_argument("--json-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        bundle = load_registry_bundle(repo_root=args.repo_root, current_registry=args.registry_current)
        registry_doc = normalize_registry_doc(bundle.registry_doc, repo_root=bundle.repo_root)
        lane = get_lane(registry_doc, args.lane_id)
        next_role = route_next_role(lane, args.status_override or lane["status"])
        payload = {
            "status": "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "execution_mode": lane["execution_mode"],
            "handoff_required": lane["handoff_required"],
            "current_status": args.status_override or lane["status"],
            "next_role": next_role,
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
