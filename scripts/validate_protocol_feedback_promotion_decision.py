#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_promotion_decision_common import (
    STATUS_PASS_REQUIRED,
    evaluate_case,
    fixture_case,
    fixture_cases,
    render_json,
)


def _load_case_from_file(path: str) -> dict[str, Any]:
    raw = Path(path).expanduser().resolve().read_text(encoding="utf-8")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("case_file_must_contain_json_object")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate protocol feedback promotion decision / inquiry requiredization contract."
    )
    parser.add_argument(
        "--fixture-case",
        default="owner_gap_emitted_atomic",
        help="Built-in fixture case name. Ignored when --case-file is provided.",
    )
    parser.add_argument("--case-file", default="", help="Path to ad-hoc JSON case file.")
    parser.add_argument("--list-fixtures", action="store_true", help="List built-in fixture names and exit.")
    parser.add_argument("--json-only", action="store_true", help="Emit compact JSON only.")
    args = parser.parse_args()

    if args.list_fixtures:
        payload = {"fixture_cases": sorted(fixture_cases().keys())}
        print(render_json(payload, pretty=not args.json_only))
        return 0

    try:
        case = _load_case_from_file(args.case_file) if args.case_file else fixture_case(args.fixture_case)
    except Exception as exc:
        payload = {
            "status": "FAIL_REQUIRED",
            "error": f"case_load_error:{exc}",
            "fixture_case": args.fixture_case,
            "case_file": args.case_file,
        }
        print(render_json(payload, pretty=not args.json_only))
        return 2

    result = evaluate_case(case)
    print(render_json(result, pretty=not args.json_only))
    return 0 if result.get("status") == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
