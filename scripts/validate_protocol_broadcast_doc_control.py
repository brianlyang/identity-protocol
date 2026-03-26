#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from governed_subdomain_doc_control_common import validate_governed_subdomain_doc_control
from repo_root_resolution_common import resolve_repo_root

STATUS_KEY = "protocol_broadcast_doc_control_status"
ERROR_CODE = "IP-BDOC-001"
SUBDOMAIN_ID = "broadcast"


def _emit(payload: dict, *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate broadcast subdomain doc-control and extension-law readability anchors.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument(
        "--doc-control",
        default="",
        help="optional doc-control override; defaults to registry-resolved subdomain current file",
    )
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    payload = validate_governed_subdomain_doc_control(
        repo_root=repo_root,
        doc_control_rel=args.doc_control,
        expected_subdomain_id=SUBDOMAIN_ID,
        status_key=STATUS_KEY,
        error_code=ERROR_CODE,
    )
    _emit(payload, json_only=args.json_only)
    return 0 if payload.get(STATUS_KEY) == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
