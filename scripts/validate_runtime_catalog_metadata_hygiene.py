#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from runtime_catalog_metadata_hygiene_common import inspect_runtime_catalog_metadata_hygiene


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate workspace-local runtime catalog metadata hygiene.")
    ap.add_argument("--catalog", default="", help="runtime catalog path")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="", help="optional single-identity filter")
    ap.add_argument("--require-active", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    payload = inspect_runtime_catalog_metadata_hygiene(
        catalog_path=str(args.catalog or ""),
        repo_catalog_path=str(args.repo_catalog or ""),
        identity_id=str(args.identity_id or ""),
        require_active=bool(args.require_active),
    )
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if str(payload.get("runtime_catalog_metadata_hygiene_status", "")).strip().upper() != "FAIL_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
