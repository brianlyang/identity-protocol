#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from execution_loop_after_mutation_not_closing_contract_common import (
    build_contract_payload,
    build_targeted_regression_payload,
    build_validation_result,
)


def _load_payload(path: str | None, targeted_regression: str | None) -> tuple[dict, str]:
    if targeted_regression:
        return (
            build_targeted_regression_payload(targeted_regression),
            targeted_regression,
        )
    if path:
        with Path(path).open("r", encoding="utf-8") as fh:
            return json.load(fh), "contract_json"
    return build_contract_payload(), "validator"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate execution-loop closeout once mutation/evidence exists."
    )
    ap.add_argument("--contract-json")
    ap.add_argument("--targeted-regression")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        payload, mode = _load_payload(args.contract_json, args.targeted_regression)
        result = build_validation_result(payload, mode)
    except ValueError as exc:
        result = {
            "mode": "argument_error",
            "status": "FAIL_REQUIRED",
            "stale_reasons": [str(exc)],
        }

    if args.json_only:
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0 if result.get("status") == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
