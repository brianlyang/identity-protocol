#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import non_owner_machine_law_reinforcement_admission_contract_common as common


def parse_args() -> argparse.Namespace:
    defaults = common.default_surface_paths()
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--governance-path", default=str(defaults["governance"]))
    parser.add_argument("--review-path", default=str(defaults["review"]))
    parser.add_argument("--workbook-path", default=str(defaults["workbook"]))
    parser.add_argument("--issue-register-path", default=str(defaults["issue_register"]))
    parser.add_argument("--payload-file")
    return parser.parse_args()


def load_payload(payload_file: str | None) -> dict[str, object]:
    if not payload_file:
        return common.baseline_payload()
    return json.loads(Path(payload_file).read_text(encoding="utf-8"))


def validate(args: argparse.Namespace) -> dict[str, object]:
    governance_path = Path(args.governance_path)
    review_path = Path(args.review_path)
    workbook_path = Path(args.workbook_path)
    issue_register_path = Path(args.issue_register_path)
    payload = load_payload(args.payload_file)

    reasons: list[str] = []
    reasons.extend(common.validate_doc_tokens("governance", common.read_text(governance_path)))
    reasons.extend(common.validate_doc_tokens("review", common.read_text(review_path)))
    reasons.extend(common.validate_workbook_text(common.read_text(workbook_path)))
    reasons.extend(common.validate_issue_register_text(common.read_text(issue_register_path)))
    reasons.extend(common.validate_reinforcement_payload(payload))

    status = "PASS_REQUIRED" if not reasons else "FAIL_REQUIRED"
    return {
        "issue_id": common.ISSUE_ID,
        "contract_id": common.CONTRACT_ID,
        "governing_law": common.GOVERNING_LAW,
        "status": status,
        "reasons": reasons,
    }


def main() -> int:
    args = parse_args()
    result = validate(args)
    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
