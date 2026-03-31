#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    emit,
    get_lane,
    load_registry_bundle,
    normalize_registry_doc,
    normalized_receipt_template,
    route_next_role,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a machine-visible control-plane lane card.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry-current", default="")
    parser.add_argument("--lane-id", default="")
    parser.add_argument("--json-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        bundle = load_registry_bundle(repo_root=args.repo_root, current_registry=args.registry_current)
        registry_doc = normalize_registry_doc(bundle.registry_doc, repo_root=bundle.repo_root)
        lane = get_lane(registry_doc, args.lane_id)
        payload = {
            "status": "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "lane_card": lane,
            "next_role": route_next_role(lane),
            "receipt_template": normalized_receipt_template(),
            "read_only_issue_043_consumption": lane["accepted_upstream_law_ref"],
        }
        emit(payload, json_only=args.json_only)
        return 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
