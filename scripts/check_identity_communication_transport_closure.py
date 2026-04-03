#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime_fleet_closure_common import collect_runtime_validator_fleet_closure

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_COMMUNICATION_MIGRATION_INVALID = "IP-COMM-004"


def _row_projection(**kwargs: Any) -> dict[str, Any]:
    validator_payload = kwargs.get("validator_payload")
    payload = validator_payload if isinstance(validator_payload, dict) else {}
    return {
        "communication_contract_status": str(payload.get("communication_contract_status", "")).strip().upper(),
        "communication_runtime_roots_status": str(payload.get("communication_runtime_roots_status", "")).strip().upper(),
        "handoff_transport_status": str(payload.get("handoff_transport_status", "")).strip().upper(),
        "collaboration_transport_status": str(payload.get("collaboration_transport_status", "")).strip().upper(),
        "protocol_feedback_reply_transport_status": str(payload.get("protocol_feedback_reply_transport_status", "")).strip().upper(),
        "protocol_feedback_inbox_transport_status": str(payload.get("protocol_feedback_inbox_transport_status", "")).strip().upper(),
        "protocol_feedback_atomic_transport_status": str(payload.get("protocol_feedback_atomic_transport_status", "")).strip().upper(),
        "broadcast_transport_status": str(payload.get("broadcast_transport_status", "")).strip().upper(),
        "missing_runtime_roots": [str(item).strip() for item in (payload.get("missing_runtime_roots") or []) if str(item).strip()],
        "stale_reasons": [str(item).strip() for item in (payload.get("stale_reasons") or []) if str(item).strip()],
    }


def _validator_extra_args(repo_catalog: Path, _catalog_path: Path, _identity_id: str) -> list[str]:
    return ["--repo-catalog", str(repo_catalog)]


def main() -> int:
    ap = argparse.ArgumentParser(description="Check identity communication transport migration closure across catalogs.")
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
        payload_status_key="identity_communication_transport_closure_status",
        error_code=ERR_COMMUNICATION_MIGRATION_INVALID,
        validator_script="scripts/validate_identity_communication_transport.py",
        validator_status_field="identity_communication_transport_status",
        row_projection=_row_projection,
        validator_extra_args_builder=_validator_extra_args,
    )

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if str(payload.get("identity_communication_transport_closure_status", "")).strip().upper() == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
