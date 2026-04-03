#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from control_plane_lane_registry_common import (
    ACTIVE_LANE_ID,
    emit,
    get_lane,
    resolve_registry_bundle,
    validate_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry-current")
    parser.add_argument("--lane-id", default=ACTIVE_LANE_ID)
    parser.add_argument("--receipt-file", required=True)
    parser.add_argument("--phase", default="closeout")
    parser.add_argument("--require-exact", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    try:
        bundle = resolve_registry_bundle(args.registry_current)
        lane = get_lane(bundle.registry_doc, args.lane_id)
        receipt = json.loads(Path(args.receipt_file).read_text(encoding="utf-8"))
        failures = validate_receipt(
            receipt,
            lane=lane,
            require_exact=args.require_exact,
            repo_root_path=bundle.repo_root,
        )
        if failures:
            emit(
                {
                    "status": "FAIL_REQUIRED",
                    "lane_id": lane["lane_id"],
                    "active_lane_id": bundle.current_doc.get("active_lane_id"),
                    "phase": args.phase,
                    "failure_tokens": failures,
                    "fail_close_token": lane["fail_close_token"],
                },
                json_only=args.json_only,
            )
            return 1
        emit(
            {
                "status": "PASS_REQUIRED",
                "lane_id": lane["lane_id"],
                "active_lane_id": bundle.current_doc.get("active_lane_id"),
                "phase": args.phase,
                "normalized_receipt": receipt,
            },
            json_only=args.json_only,
        )
        return 0
    except Exception as exc:
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
