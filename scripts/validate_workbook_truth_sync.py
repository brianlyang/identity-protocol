#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

ISSUE_EXPECTATIONS = {
    "ISSUE-040": {
        "tokens": [
            "- `status`: CLOSED",
            "c09a3a6",
            "7dc829e32a4fc7a2a01757ed02aa15512aa790cb",
            "908b8348d22c0583408cc6dfc4acd97217a03579",
            "no card, no handoff",
            "no durable execution receipt, no continuation claim",
            "reopen is machine-triggered only.",
        ],
        "forbidden": [
            "- `status`: OPEN",
            "pending formalization",
        ],
    },
    "ISSUE-041": {
        "tokens": [
            "- `status`: CLOSED",
            "9fdb1114ed63a467846141a9049cc949f2b5e131",
            "a929b0267f3c50a827b1385123f081f487806efd",
            "3aed210",
            "closure is incomplete when teardown receipts are missing",
            "child tmp/probe/runtime residue without owner binding is not admitted",
            "nested governed-root replay is not admitted",
            "guard cleanup deletes only machine-admitted stale residue and must not overreach live runtime.",
        ],
        "forbidden": [
            "- `status`: OPEN",
            "pending formalization",
        ],
    },
    "ISSUE-042": {
        "tokens": [
            "- `status`: CLOSED",
            "63fa59804fc2a2b49d44a1a96245e40ff02cf8e0",
            "e20fe7f7ce028463bcfa0dafbee3d857bfb1d62f",
            "0dfbdcf6b52ad9c1f3df762dca4a3af4814471af",
            "`not written = not progressed`",
            "`not validated = not complete`",
            "`not committed = not closed`",
        ],
        "forbidden": [
            "- `status`: OPEN",
            "pending formalization",
        ],
    },
}


def extract_issue_section(text: str, issue_id: str) -> str | None:
    pattern = rf"^### {re.escape(issue_id)} .*?(?=^### ISSUE-|^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(0) if match else None


def validate(workbook_path: Path):
    text = workbook_path.read_text()
    checks = []
    for issue_id, spec in ISSUE_EXPECTATIONS.items():
        section = extract_issue_section(text, issue_id)
        if section is None:
            return False, f"{issue_id.replace('-', '_')}_SECTION_MISSING", checks
        checks.append({"issue": issue_id, "check": "section_present", "ok": True})
        for token in spec["tokens"]:
            if token not in section:
                return False, f"{issue_id.replace('-', '_')}_MISSING_TOKEN", checks + [{"issue": issue_id, "check": token, "ok": False}]
            checks.append({"issue": issue_id, "check": token, "ok": True})
        for token in spec["forbidden"]:
            if token in section:
                return False, f"{issue_id.replace('-', '_')}_FORBIDDEN_TOKEN", checks + [{"issue": issue_id, "check": token, "ok": False}]
            checks.append({"issue": issue_id, "check": f"forbidden:{token}", "ok": True})
    return True, None, checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--workbook-path', default='docs/workbook/protocol-deep-audit-workbook-v1.6.md')
    parser.add_argument('--json-only', action='store_true')
    args = parser.parse_args()

    ok, mismatch, checks = validate(Path(args.workbook_path))
    payload = {
        "ok": ok,
        "status": "PASS_REQUIRED" if ok else "FAIL_REQUIRED",
        "workbook_path": args.workbook_path,
        "first_mismatch": mismatch,
        "checks": checks,
    }
    print(json.dumps(payload, indent=None if args.json_only else 2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
