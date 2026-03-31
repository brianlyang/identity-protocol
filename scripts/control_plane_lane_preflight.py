#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from control_plane_lane_registry_common import (
    SCOPE_LOCK_ALLOWED_NEXT_ACTIONS,
    emit,
    get_lane,
    load_registry_bundle,
    normalize_registry_doc,
    replace_lane,
    route_next_role,
    write_registry_doc,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run control-plane lane preflight.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry-current", default="")
    parser.add_argument("--lane-id", default="")
    parser.add_argument("--write-back", action="store_true")
    parser.add_argument("--json-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        bundle = load_registry_bundle(repo_root=args.repo_root, current_registry=args.registry_current)
        registry_doc = normalize_registry_doc(bundle.registry_doc, repo_root=bundle.repo_root)
        lane = get_lane(registry_doc, args.lane_id)
        missing_surfaces = [path for path in lane["exact_fixed_write_set"] if not (bundle.repo_root / path).exists()]
        missing_inputs = [path for path in lane["read_only_input_surfaces"] if not (bundle.repo_root / path).exists()]
        failures: list[str] = []
        if missing_surfaces:
            failures.append(f"missing_fixed_write_surfaces:{','.join(missing_surfaces)}")
        if missing_inputs:
            failures.append(f"missing_read_only_input_surfaces:{','.join(missing_inputs)}")
        updated_status = "preflight_passed"
        updated_lane = dict(lane)
        updated_lane["status"] = updated_status
        next_role = route_next_role(updated_lane)
        updated_lane["next_role"] = next_role["role"] or lane["next_role"]
        payload = {
            "status": "FAIL_REQUIRED" if failures else "PASS_REQUIRED",
            "lane_id": lane["lane_id"],
            "execution_mode": lane["execution_mode"],
            "classification": lane["classification"],
            "scope_lock_status": "LOCKED",
            "allowed_next_actions": list(SCOPE_LOCK_ALLOWED_NEXT_ACTIONS),
            "status_transition": {
                "from": lane["status"],
                "to": updated_status,
            },
            "next_role": next_role,
            "failures": failures,
            "read_only_input_surfaces": lane["read_only_input_surfaces"],
        }
        if not failures and args.write_back:
            registry_doc = replace_lane(registry_doc, updated_lane)
            write_registry_doc(bundle, registry_doc)
        emit(payload, json_only=args.json_only)
        return 1 if failures else 0
    except Exception as exc:  # pragma: no cover - CLI failure path
        emit({"status": "FAIL_REQUIRED", "error": str(exc)}, json_only=args.json_only)
        return 1


if __name__ == "__main__":
    sys.exit(main())
