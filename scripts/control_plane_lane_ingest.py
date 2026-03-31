#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from control_plane_lane_registry_common import (
    classify_receipt_outcome,
    emit,
    get_lane,
    load_json_file,
    load_registry_bundle,
    normalize_receipt,
    normalize_registry_doc,
    replace_lane,
    route_next_role,
    stream_guard_result,
    write_registry_doc,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest a structured control-plane receipt.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry-current", default="")
    parser.add_argument("--lane-id", default="")
    parser.add_argument("--receipt-file", default="")
    parser.add_argument("--receipt-json", default="")
    parser.add_argument("--write-back", action="store_true")
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
        raw_receipt = _load_receipt(args)
        receipt = normalize_receipt(raw_receipt, repo_root=bundle.repo_root)
        guard = stream_guard_result(
            lane,
            receipt,
            require_exact=bool(receipt.get("commit_id")),
            scope_locked=lane["status"] != "pending_architect",
        )
        if guard["status"] == "FAIL_REQUIRED":
            new_status = "fail_closed"
            reasons = guard["failure_tokens"]
        else:
            new_status, reasons = classify_receipt_outcome(lane, receipt)
        updated_lane = dict(lane)
        updated_lane["status"] = new_status
        if receipt.get("blocker_receipt"):
            updated_lane["blocker_id"] = str(receipt["blocker_receipt"].get("reason") or receipt["blocker_receipt"].get("token") or "blocker")
        next_role = route_next_role(updated_lane, updated_lane["status"])
        updated_lane["next_role"] = next_role["role"] or ""
        if args.write_back:
            registry_doc = replace_lane(registry_doc, updated_lane)
            write_registry_doc(bundle, registry_doc)
        payload = {
            "status": "FAIL_REQUIRED" if new_status == "fail_closed" else "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "previous_status": lane["status"],
            "new_status": new_status,
            "next_role": next_role,
            "guard": guard,
            "reasons": reasons,
            "normalized_receipt": receipt["normalized_receipt"],
        }
        emit(payload, json_only=args.json_only)
        return 1 if new_status == "fail_closed" else 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
