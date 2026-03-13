#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

HOST_GATEWAY_CONTRACT_KEYS = (
    "protocol_host_unique_channel_contract_v1",
    "protocol_gateway_wrapper_contract_v1",
    "protocol_gateway_contract_v1",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_host_gateway_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw, key
    return {}, HOST_GATEWAY_CONTRACT_KEYS[0]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_pack_runtime_path(pack_path: Path, raw_path: str, fallback_rel: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return (pack_path / fallback_rel).resolve()
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (pack_path / "runtime" / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (pack_path / token).resolve()
    return (pack_path / token).resolve()


def _resolve_report_path_from_pattern(*, pack_path: Path, pattern: str, run_id: str) -> Path:
    token = str(pattern or "").strip() or "runtime/reports/broadcast/broadcast-ack-*.json"
    if "*" not in token:
        return _resolve_pack_runtime_path(pack_path, token, "runtime/reports/broadcast/broadcast-ack-latest.json")
    run_token = str(run_id or "run").strip() or "run"
    safe_run = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_token)
    stamp = int(time.time())
    filename = token.replace("*", f"{safe_run}-{stamp}")
    return _resolve_pack_runtime_path(pack_path, filename, "runtime/reports/broadcast/broadcast-ack-latest.json")


def _load_json_file(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def main() -> int:
    ap = argparse.ArgumentParser(description="Acknowledge pending protocol broadcast items for an identity instance.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--broadcast-id", action="append", default=[])
    ap.add_argument("--ack-all-pending", action="store_true")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        _emit(
            {
                "identity_broadcast_ack_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-BCAST-001",
                "stale_reasons": ["catalog_not_found"],
                "catalog_path": str(catalog_path),
            },
            json_only=args.json_only,
        )
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        _emit(
            {
                "identity_broadcast_ack_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-BCAST-001",
                "stale_reasons": [f"identity_resolution_failed:{exc}"],
                "catalog_path": str(catalog_path),
            },
            json_only=args.json_only,
        )
        return 2

    host_gateway_contract, contract_key = _resolve_host_gateway_contract(task_doc)
    broadcast_policy = host_gateway_contract.get("broadcast_policy") if isinstance(host_gateway_contract, dict) else None
    if not isinstance(broadcast_policy, dict) or broadcast_policy.get("required") is not True:
        _emit(
            {
                "identity_broadcast_ack_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-BCAST-002",
                "stale_reasons": ["broadcast_policy_missing_or_not_required"],
                "identity_id": args.identity_id,
                "contract_key_used": contract_key,
                "task_path": str(task_path),
            },
            json_only=args.json_only,
        )
        return 1

    state_path = _resolve_pack_runtime_path(
        pack_path,
        str(broadcast_policy.get("instance_state_file", "")).strip(),
        "runtime/state/broadcast_state.json",
    )
    state_doc = _load_json_file(
        state_path,
        default={
            "schema_version": "v1",
            "identity_id": args.identity_id,
            "read_ids": [],
            "acked_ids": [],
            "pending_ack_ids": [],
            "critical_unacked_ids": [],
        },
    )
    pending_ack_ids = {
        str(item).strip()
        for item in (state_doc.get("pending_ack_ids") if isinstance(state_doc.get("pending_ack_ids"), list) else [])
        if str(item).strip()
    }
    critical_unacked_ids = {
        str(item).strip()
        for item in (
            state_doc.get("critical_unacked_ids")
            if isinstance(state_doc.get("critical_unacked_ids"), list)
            else []
        )
        if str(item).strip()
    }
    acked_ids = {
        str(item).strip()
        for item in (state_doc.get("acked_ids") if isinstance(state_doc.get("acked_ids"), list) else [])
        if str(item).strip()
    }

    requested_ids = [str(item).strip() for item in args.broadcast_id if str(item).strip()]
    if args.ack_all_pending:
        target_ids = sorted(pending_ack_ids)
    else:
        target_ids = sorted(set(requested_ids))

    if not target_ids:
        _emit(
            {
                "identity_broadcast_ack_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-BCAST-003",
                "stale_reasons": ["ack_target_ids_missing"],
                "identity_id": args.identity_id,
                "state_path": str(state_path),
            },
            json_only=args.json_only,
        )
        return 1

    unknown_ids = [bid for bid in target_ids if bid not in pending_ack_ids and bid not in acked_ids]
    if unknown_ids:
        _emit(
            {
                "identity_broadcast_ack_status": STATUS_FAIL_REQUIRED,
                "error_code": "IP-GATE-BCAST-004",
                "stale_reasons": ["ack_target_not_pending_or_acked"],
                "identity_id": args.identity_id,
                "state_path": str(state_path),
                "unknown_ids": unknown_ids,
            },
            json_only=args.json_only,
        )
        return 1

    acked_before = set(acked_ids)
    for bid in target_ids:
        acked_ids.add(bid)
        pending_ack_ids.discard(bid)
        critical_unacked_ids.discard(bid)

    state_doc["acked_ids"] = sorted(acked_ids)
    state_doc["pending_ack_ids"] = sorted(pending_ack_ids)
    state_doc["critical_unacked_ids"] = sorted(critical_unacked_ids)
    state_doc["updated_at_utc"] = _utc_now_iso()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run_id = str(args.run_id or "").strip() or f"broadcast-ack-{int(time.time())}"
    ack_path = _resolve_report_path_from_pattern(
        pack_path=pack_path,
        pattern=str(broadcast_policy.get("instance_ack_pattern", "")).strip(),
        run_id=run_id,
    )
    ack_path.parent.mkdir(parents=True, exist_ok=True)
    ack_doc = {
        "schema_version": "v1",
        "identity_id": args.identity_id,
        "actor_id": str(args.actor_id or "").strip(),
        "session_id": str(args.session_id or "").strip(),
        "run_id": run_id,
        "timestamp_utc": _utc_now_iso(),
        "acked_ids": target_ids,
        "acked_new_ids": sorted(set(target_ids) - acked_before),
        "remaining_pending_ack_ids": sorted(pending_ack_ids),
        "remaining_critical_unacked_ids": sorted(critical_unacked_ids),
        "state_path": str(state_path),
    }
    ack_path.write_text(json.dumps(ack_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _emit(
        {
            "identity_broadcast_ack_status": STATUS_PASS_REQUIRED,
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "pack_path": str(pack_path),
            "task_path": str(task_path),
            "contract_key_used": contract_key,
            "state_path": str(state_path),
            "ack_receipt_path": str(ack_path),
            "acked_ids": target_ids,
            "remaining_pending_ack_ids": sorted(pending_ack_ids),
            "remaining_critical_unacked_ids": sorted(critical_unacked_ids),
        },
        json_only=args.json_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
