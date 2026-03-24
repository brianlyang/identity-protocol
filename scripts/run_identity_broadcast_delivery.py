#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_broadcast_delivery_common import collect_broadcast_delivery_projection
from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _emit(payload: dict, *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Sync protocol broadcast delivery state for an identity instance.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--sync", action="store_true", help="materialize broadcast visibility into runtime state")
    ap.add_argument("--write-receipt", action="store_true", help="write delivery receipt after projection")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        payload = {
            "identity_broadcast_delivery_status": "FAIL_REQUIRED",
            "error_code": "IP-GATE-BCAST-DELIVERY-002",
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
            "identity_broadcast_delivery_status": "FAIL_REQUIRED",
            "error_code": "IP-GATE-BCAST-DELIVERY-002",
            "stale_reasons": [f"identity_resolution_failed:{type(exc).__name__}"],
            "catalog_path": str(catalog_path),
            "identity_id": args.identity_id,
        }
        _emit(payload, json_only=args.json_only)
        return 2

    payload = collect_broadcast_delivery_projection(
        task_doc=task_doc,
        pack_path=pack_path,
        identity_id=args.identity_id,
        run_id=str(args.run_id or "").strip(),
        actor_id=str(args.actor_id or "").strip(),
        session_id=str(args.session_id or "").strip(),
        apply_sync=bool(args.sync),
        write_receipt=bool(args.write_receipt or args.sync),
    )
    payload["catalog_path"] = str(catalog_path)
    payload["pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)
    _emit(payload, json_only=args.json_only)
    return 0 if str(payload.get("identity_broadcast_delivery_status", "")).strip().upper() == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
