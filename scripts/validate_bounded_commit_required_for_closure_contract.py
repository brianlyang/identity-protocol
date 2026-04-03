#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

from bounded_commit_required_for_closure_contract_common import (
    STATUS_PASS_REQUIRED,
    render_json,
    validate_contract_documents,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the ISSUE-042C bounded commit required for closure contract."
    )
    parser.add_argument("--repo-root", default=None, help="Override repository root for validation.")
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Emit machine-readable JSON only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_contract_documents(args.repo_root)
    print(render_json(result))
    return 0 if result["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    sys.exit(main())
