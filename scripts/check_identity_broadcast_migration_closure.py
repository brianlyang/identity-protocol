#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime_fleet_closure_common import collect_runtime_validator_fleet_closure

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_BROADCAST_MIGRATION_INVALID = "IP-GATE-BCAST-DELIVERY-003"


def _row_projection(**kwargs: Any) -> dict[str, Any]:
    validator_payload = kwargs.get("validator_payload")
    payload = validator_payload if isinstance(validator_payload, dict) else {}
    return {
        "broadcast_delivery_sync_status": str(payload.get("broadcast_delivery_sync_status", "")).strip().upper(),
        "broadcast_projection_parity_status": str(payload.get("broadcast_projection_parity_status", "")).strip().upper(),
        "broadcast_visible_count": int(payload.get("broadcast_visible_count", 0) or 0),
        "broadcast_unread_count": int(payload.get("broadcast_unread_count", 0) or 0),
        "broadcast_pending_ack_count": int(payload.get("broadcast_pending_ack_count", 0) or 0),
        "broadcast_critical_unacked_count": int(payload.get("broadcast_critical_unacked_count", 0) or 0),
        "stale_reasons": [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Check broadcast delivery migration closure across active runtime identities.")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--catalog", action="append", default=[])
    ap.add_argument("--include-env-catalog", action="store_true")
    ap.add_argument("--workspace-runtime-only", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    payload = collect_runtime_validator_fleet_closure(
        repo_root=repo_root,
        repo_catalog_arg=args.repo_catalog,
        raw_catalogs=args.catalog,
        include_env_catalog=bool(args.include_env_catalog),
        workspace_runtime_only=bool(args.workspace_runtime_only),
        caller_anchor=Path.cwd().resolve(),
        caller_start=Path(__file__).resolve(),
        payload_status_key="identity_broadcast_migration_closure_status",
        error_code=ERR_BROADCAST_MIGRATION_INVALID,
        validator_script="scripts/validate_identity_broadcast_delivery.py",
        validator_status_field="identity_broadcast_delivery_status",
        row_projection=_row_projection,
    )

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if str(payload.get("identity_broadcast_migration_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
