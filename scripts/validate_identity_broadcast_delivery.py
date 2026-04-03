#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from identity_broadcast_delivery_common import (
    BROADCAST_CONTRACT_ID,
    BROADCAST_CONTRACT_KEY,
    collect_broadcast_delivery_projection,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task


def _emit(payload: dict, *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol broadcast delivery adoption for an identity instance.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--operation", default="validate")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        payload = {
            "identity_broadcast_delivery_status": "FAIL_REQUIRED",
            "required_contract": False,
            "auto_required_signal": False,
            "contract_key": BROADCAST_CONTRACT_KEY,
            "contract_id": BROADCAST_CONTRACT_ID,
            "error_code": "IP-GATE-BCAST-DELIVERY-002",
            "stale_reasons": ["catalog_not_found"],
            "catalog_path": str(catalog_path),
            "evidence_ref": "",
        }
        _emit(payload, json_only=args.json_only)
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        payload = {
            "identity_broadcast_delivery_status": "FAIL_REQUIRED",
            "required_contract": False,
            "auto_required_signal": False,
            "contract_key": BROADCAST_CONTRACT_KEY,
            "contract_id": BROADCAST_CONTRACT_ID,
            "error_code": "IP-GATE-BCAST-DELIVERY-002",
            "stale_reasons": [f"identity_resolution_failed:{type(exc).__name__}"],
            "catalog_path": str(catalog_path),
            "identity_id": args.identity_id,
            "evidence_ref": "",
        }
        _emit(payload, json_only=args.json_only)
        return 2

    payload = collect_broadcast_delivery_projection(
        task_doc=task_doc,
        pack_path=pack_path,
        identity_id=args.identity_id,
        apply_sync=False,
        write_receipt=False,
    )
    payload["catalog_path"] = str(catalog_path)
    payload["pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)
    payload["operation"] = str(args.operation or "").strip()
    _emit(payload, json_only=args.json_only)
    return 0 if str(payload.get("identity_broadcast_delivery_status", "")).strip().upper() == "PASS_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
