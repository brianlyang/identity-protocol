#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_communication_transport_common import collect_identity_communication_transport_projection
from resolve_identity_context import resolve_repo_catalog_path
from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _emit(payload: dict, *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity communication transport convergence.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--operation", default="validate")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    catalog_path = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = resolve_repo_catalog_path(args.repo_catalog, start=Path(__file__).resolve())

    if not catalog_path.exists():
        payload = {
            "identity_communication_transport_status": "FAIL_REQUIRED",
            "error_code": "IP-COMM-001",
            "stale_reasons": ["catalog_not_found"],
            "catalog_path": str(catalog_path),
        }
        _emit(payload, json_only=args.json_only)
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        payload = {
            "identity_communication_transport_status": "FAIL_REQUIRED",
            "error_code": "IP-COMM-001",
            "stale_reasons": [f"identity_resolution_failed:{type(exc).__name__}"],
            "catalog_path": str(catalog_path),
            "identity_id": args.identity_id,
        }
        _emit(payload, json_only=args.json_only)
        return 2

    payload = collect_identity_communication_transport_projection(
        task_doc=task_doc,
        pack_path=pack_path,
        identity_id=args.identity_id,
        catalog_path=catalog_path,
        repo_root=repo_root,
        repo_catalog_path=repo_catalog_path,
    )
    payload["catalog_path"] = str(catalog_path)
    payload["repo_catalog_path"] = str(repo_catalog_path)
    payload["pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)
    payload["operation"] = str(args.operation or "").strip()
    _emit(payload, json_only=args.json_only)
    return 0 if str(payload.get("identity_communication_transport_status", "")).strip().upper() == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
