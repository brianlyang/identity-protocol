#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from control_plane_lane_registry_common import emit, get_lane, load_json_file, load_registry_bundle, normalize_receipt, normalize_registry_doc, stream_guard_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Enforce lane-card-bound stream guard rules.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry-current", default="")
    parser.add_argument("--lane-id", default="")
    parser.add_argument("--receipt-file", default="")
    parser.add_argument("--receipt-json", default="")
    parser.add_argument("--phase", default="closeout")
    parser.add_argument("--require-exact", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    return parser


def _load_receipt(args: argparse.Namespace) -> dict:
    if args.receipt_file:
        return load_json_file(args.receipt_file)
    if args.receipt_json:
        return json.loads(args.receipt_json)
    raise ValueError("receipt_required")


def main() -> int:
    args = build_parser().parse_args()
    try:
        bundle = load_registry_bundle(repo_root=args.repo_root, current_registry=args.registry_current)
        registry_doc = normalize_registry_doc(bundle.registry_doc, repo_root=bundle.repo_root)
        lane = get_lane(registry_doc, args.lane_id)
        receipt = normalize_receipt(_load_receipt(args), repo_root=bundle.repo_root)
        scope_locked = args.phase == "closeout" or lane["status"] not in {"pending_architect", "architect_ready"}
        guard = stream_guard_result(
            lane,
            receipt,
            require_exact=args.require_exact or args.phase == "closeout",
            scope_locked=scope_locked,
        )
        payload = {
            "status": guard["status"],
            "lane_id": lane["lane_id"],
            "phase": args.phase,
            "scope_lock_status": guard["scope_lock_status"],
            "failure_tokens": guard["failure_tokens"],
            "normalized_receipt": guard["normalized_receipt"],
        }
        emit(payload, json_only=args.json_only)
        return 1 if guard["status"] == "FAIL_REQUIRED" else 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
