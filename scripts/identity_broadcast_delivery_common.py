#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from protocol_infra_contract import (
    HOST_GATEWAY_BROADCAST_ACK_PATTERN,
    HOST_GATEWAY_BROADCAST_INDEX_FILE,
    HOST_GATEWAY_BROADCAST_ITEMS_DIR,
    HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
    HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    HOST_GATEWAY_BROADCAST_STATE_FILE,
    HOST_GATEWAY_CONTRACT_KEYS as INFRA_HOST_GATEWAY_CONTRACT_KEYS,
)
from tool_vendor_governance_common import contract_required

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

HOST_GATEWAY_CONTRACT_KEYS: tuple[str, ...] = tuple(INFRA_HOST_GATEWAY_CONTRACT_KEYS)
BROADCAST_CONTRACT_KEY = "identity_broadcast_delivery_contract_v1"
BROADCAST_CONTRACT_ID = "rq_053_identity_broadcast_delivery_contract_v1"
BROADCAST_VALIDATOR_ID = "scripts/validate_identity_broadcast_delivery.py"
BROADCAST_SYNC_EXECUTOR_ID = "scripts/run_identity_broadcast_delivery.py"
BROADCAST_MIGRATION_CLOSURE_CHECKER_ID = "scripts/check_identity_broadcast_migration_closure.py"

BROADCAST_ITEM_REQUIRED_FIELDS: tuple[str, ...] = (
    "broadcast_id",
    "created_at_utc",
    "title",
    "message",
    "severity",
    "requires_ack",
    "scope",
)
BROADCAST_ALLOWED_SEVERITIES: set[str] = {"info", "warning", "critical"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_utc(value: Any) -> int:
    token = str(value or "").strip()
    if not token:
        return 0
    try:
        if token.endswith("Z"):
            token = token[:-1] + "+00:00"
        return int(datetime.fromisoformat(token).timestamp())
    except Exception:
        return 0


def safe_load_json_file(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def resolve_pack_runtime_path(pack_path: Path, raw_path: str, fallback_rel: str) -> Path:
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


def resolve_report_path_from_pattern(*, pack_path: Path, pattern: str, run_id: str, fallback_name: str) -> Path:
    token = str(pattern or "").strip()
    if not token:
        token = fallback_name
    if "*" not in token:
        return resolve_pack_runtime_path(pack_path, token, fallback_name)
    run_token = str(run_id or "run").strip() or "run"
    safe_run = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_token)
    stamp = int(time.time())
    return resolve_pack_runtime_path(pack_path, token.replace("*", f"{safe_run}-{stamp}"), fallback_name)


def default_broadcast_state_doc(identity_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1",
        "identity_id": str(identity_id or "").strip(),
        "last_seen_created_at_utc": "",
        "read_ids": [],
        "acked_ids": [],
        "pending_ack_ids": [],
        "critical_unacked_ids": [],
        "updated_at_utc": "",
    }


def resolve_host_gateway_contract(task_doc: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        raw = task_doc.get(key)
        if isinstance(raw, dict):
            return raw, key
    return {}, HOST_GATEWAY_CONTRACT_KEYS[0]


def resolve_runtime_gateway_contract(*, task_doc: dict[str, Any], pack_path: Path) -> tuple[dict[str, Any], Path, list[str]]:
    task_contract, _ = resolve_host_gateway_contract(task_doc)
    issues: list[str] = []
    if not isinstance(task_contract, dict):
        return {}, Path(""), ["host_gateway_contract_missing"]
    gateway_contract_path = resolve_pack_runtime_path(
        pack_path,
        str(task_contract.get("gateway_contract_path", "")).strip(),
        "runtime/gate/protocol_gateway_contract.json",
    )
    if not gateway_contract_path.exists() or not gateway_contract_path.is_file():
        issues.append("runtime_gateway_contract_missing")
        return {}, gateway_contract_path, issues
    runtime_contract = safe_load_json_file(gateway_contract_path, default={})
    if not runtime_contract:
        issues.append("runtime_gateway_contract_invalid")
    return runtime_contract, gateway_contract_path, issues


def _validate_broadcast_item_doc(doc: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in BROADCAST_ITEM_REQUIRED_FIELDS:
        if field not in doc:
            issues.append(f"broadcast_item_missing_field:{field}")
    broadcast_id = str(doc.get("broadcast_id", "")).strip()
    if not broadcast_id:
        issues.append("broadcast_item_broadcast_id_empty")
    created = str(doc.get("created_at_utc", "")).strip()
    if created and parse_iso_utc(created) <= 0:
        issues.append("broadcast_item_created_at_invalid")
    expire = str(doc.get("expire_at_utc", "")).strip()
    if expire and parse_iso_utc(expire) <= 0:
        issues.append("broadcast_item_expire_at_invalid")
    if str(doc.get("severity", "")).strip().lower() not in BROADCAST_ALLOWED_SEVERITIES:
        issues.append("broadcast_item_severity_invalid")
    if not isinstance(doc.get("requires_ack"), bool):
        issues.append("broadcast_item_requires_ack_not_bool")
    scope = doc.get("scope")
    if isinstance(scope, list):
        normalized = [str(item).strip() for item in scope if str(item).strip()]
        if not normalized:
            issues.append("broadcast_item_scope_list_empty")
    elif not str(scope or "").strip():
        issues.append("broadcast_item_scope_empty")
    return issues


def _scope_visible_to_identity(scope: Any, identity_id: str) -> bool:
    identity_token = str(identity_id or "").strip().lower()
    if isinstance(scope, list):
        tokens = {str(item).strip().lower() for item in scope if str(item).strip()}
        return "all" in tokens or "*" in tokens or f"identity:{identity_token}" in tokens
    token = str(scope or "all").strip().lower()
    return token in {"", "all", "*"} or token == f"identity:{identity_token}"


def collect_broadcast_delivery_projection(
    *,
    task_doc: dict[str, Any],
    pack_path: Path,
    identity_id: str,
    run_id: str = "",
    actor_id: str = "",
    session_id: str = "",
    apply_sync: bool = False,
    write_receipt: bool = False,
) -> dict[str, Any]:
    delivery_contract = task_doc.get(BROADCAST_CONTRACT_KEY)
    required_contract = contract_required(delivery_contract) if isinstance(delivery_contract, dict) else False
    task_contract, contract_key = resolve_host_gateway_contract(task_doc)
    runtime_contract, runtime_contract_path, runtime_contract_issues = resolve_runtime_gateway_contract(
        task_doc=task_doc,
        pack_path=pack_path,
    )
    task_broadcast_policy = task_contract.get("broadcast_policy") if isinstance(task_contract, dict) else None
    runtime_broadcast_policy = runtime_contract.get("broadcast_policy") if isinstance(runtime_contract, dict) else None

    payload: dict[str, Any] = {
        "identity_broadcast_delivery_status": STATUS_FAIL_REQUIRED,
        "broadcast_contract_status": STATUS_FAIL_REQUIRED,
        "broadcast_runtime_contract_status": STATUS_FAIL_REQUIRED,
        "broadcast_source_status": STATUS_FAIL_REQUIRED,
        "broadcast_state_status": STATUS_FAIL_REQUIRED,
        "broadcast_delivery_sync_status": STATUS_FAIL_REQUIRED,
        "broadcast_projection_parity_status": STATUS_FAIL_REQUIRED,
        "identity_id": str(identity_id or "").strip(),
        "required_contract": bool(required_contract),
        "auto_required_signal": False,
        "contract_key": BROADCAST_CONTRACT_KEY,
        "contract_id": BROADCAST_CONTRACT_ID,
        "contract_key_used": contract_key,
        "runtime_gateway_contract_path": str(runtime_contract_path) if str(runtime_contract_path) else "",
        "broadcast_state_file": "",
        "broadcast_receipt_path": "",
        "broadcast_visible_count": 0,
        "broadcast_unread_count": 0,
        "broadcast_pending_ack_count": 0,
        "broadcast_critical_unacked_count": 0,
        "visible_ids": [],
        "unread_ids": [],
        "pending_ack_ids": [],
        "critical_unacked_ids": [],
        "stale_reasons": [],
        "error_code": "IP-GATE-BCAST-DELIVERY-001",
        "sync_applied": False,
        "evidence_ref": str((pack_path / "CURRENT_TASK.json").resolve()),
    }

    if not isinstance(delivery_contract, dict) or required_contract is not True:
        payload["stale_reasons"].append("identity_broadcast_delivery_contract_missing_or_not_required")
        return payload
    host_gateway_refs = {
        str(item).strip()
        for item in (delivery_contract.get("host_gateway_contract_keys") or [])
        if str(item).strip()
    }
    if (
        str(delivery_contract.get("contract_id", "")).strip() != BROADCAST_CONTRACT_ID
        or str(delivery_contract.get("validator", "")).strip() != BROADCAST_VALIDATOR_ID
        or str(delivery_contract.get("sync_executor", "")).strip() != BROADCAST_SYNC_EXECUTOR_ID
        or str(delivery_contract.get("migration_closure_checker", "")).strip()
        != BROADCAST_MIGRATION_CLOSURE_CHECKER_ID
        or not set(HOST_GATEWAY_CONTRACT_KEYS).issubset(host_gateway_refs)
    ):
        payload["stale_reasons"].append("identity_broadcast_delivery_contract_invalid")
        return payload
    payload["broadcast_contract_status"] = STATUS_PASS_REQUIRED

    if not isinstance(task_broadcast_policy, dict) or task_broadcast_policy.get("required") is not True:
        payload["stale_reasons"].append("host_gateway_broadcast_policy_missing_or_not_required")
        return payload

    if runtime_contract_issues:
        payload["stale_reasons"].extend(runtime_contract_issues)
        return payload
    if not isinstance(runtime_broadcast_policy, dict) or runtime_broadcast_policy.get("required") is not True:
        payload["stale_reasons"].append("runtime_broadcast_policy_missing_or_not_required")
        return payload
    payload["broadcast_runtime_contract_status"] = STATUS_PASS_REQUIRED

    expected_pairs = {
        "protocol_broadcast_items_dir": HOST_GATEWAY_BROADCAST_ITEMS_DIR,
        "protocol_broadcast_index_file": HOST_GATEWAY_BROADCAST_INDEX_FILE,
        "protocol_broadcast_schema_file": HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    }
    for field, expected in expected_pairs.items():
        observed = str(runtime_broadcast_policy.get(field, "")).strip()
        if observed != expected:
            payload["stale_reasons"].append(f"runtime_broadcast_policy_mismatch:{field}")
            return payload

    runtime_protocol_root = Path(str(runtime_contract.get("protocol_repo_root", "")).strip()).expanduser()
    if not str(runtime_protocol_root).strip():
        payload["stale_reasons"].append("runtime_protocol_repo_root_missing")
        return payload
    runtime_protocol_root = runtime_protocol_root.resolve()
    items_dir = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_ITEMS_DIR).resolve()
    index_path = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_INDEX_FILE).resolve()
    schema_path = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_SCHEMA_FILE).resolve()
    if not items_dir.exists() or not items_dir.is_dir():
        payload["stale_reasons"].append("broadcast_items_dir_missing")
        return payload
    if not index_path.exists() or not index_path.is_file():
        payload["stale_reasons"].append("broadcast_index_missing")
        return payload
    if not schema_path.exists() or not schema_path.is_file():
        payload["stale_reasons"].append("broadcast_schema_missing")
        return payload

    index_doc = safe_load_json_file(index_path, default={"items": []})
    rows = index_doc.get("items") if isinstance(index_doc, dict) else []
    candidate_files: list[Path] = []
    source_issues: list[str] = []
    if not isinstance(rows, list):
        source_issues.append("broadcast_index_items_not_list")
    else:
        for row in rows:
            if not isinstance(row, dict):
                source_issues.append("broadcast_index_row_not_object")
                continue
            file_token = str(row.get("file", "")).strip()
            if not file_token:
                source_issues.append("broadcast_index_file_missing")
                continue
            candidate = (items_dir / file_token).resolve()
            if not candidate.exists() or not candidate.is_file():
                source_issues.append(f"broadcast_item_missing:{file_token}")
                continue
            candidate_files.append(candidate)
    if not candidate_files:
        candidate_files = sorted(items_dir.glob("*.json"))
    item_docs: dict[str, dict[str, Any]] = {}
    for path in candidate_files:
        doc = safe_load_json_file(path, default={})
        item_issues = _validate_broadcast_item_doc(doc)
        if item_issues:
            source_issues.extend(f"{path.name}:{issue}" for issue in item_issues)
            continue
        item_docs[str(doc.get("broadcast_id", "")).strip()] = doc
    if source_issues:
        payload["stale_reasons"].extend(sorted(set(source_issues)))
        return payload
    payload["broadcast_source_status"] = STATUS_PASS_REQUIRED

    state_path = resolve_pack_runtime_path(
        pack_path,
        str(runtime_broadcast_policy.get("instance_state_file", "")).strip(),
        HOST_GATEWAY_BROADCAST_STATE_FILE,
    )
    payload["broadcast_state_file"] = str(state_path)
    state_doc = safe_load_json_file(state_path, default=default_broadcast_state_doc(identity_id))
    for field in ("read_ids", "acked_ids", "pending_ack_ids", "critical_unacked_ids"):
        if not isinstance(state_doc.get(field), list):
            payload["stale_reasons"].append(f"broadcast_state_field_not_list:{field}")
            return payload
    if str(state_doc.get("identity_id", "")).strip() not in {"", str(identity_id or "").strip()}:
        payload["stale_reasons"].append("broadcast_state_identity_mismatch")
        return payload
    payload["broadcast_state_status"] = STATUS_PASS_REQUIRED

    existing_read_ids = {str(item).strip() for item in state_doc.get("read_ids", []) if str(item).strip()}
    existing_acked_ids = {str(item).strip() for item in state_doc.get("acked_ids", []) if str(item).strip()}
    visible_ids: list[str] = []
    unread_ids: list[str] = []
    computed_pending_ack_ids: list[str] = []
    computed_critical_unacked_ids: list[str] = []
    max_seen_epoch = parse_iso_utc(state_doc.get("last_seen_created_at_utc"))
    now_epoch = int(time.time())

    for broadcast_id, doc in sorted(item_docs.items(), key=lambda kv: kv[0]):
        expire_epoch = parse_iso_utc(doc.get("expire_at_utc"))
        if expire_epoch and expire_epoch < now_epoch:
            continue
        if not _scope_visible_to_identity(doc.get("scope"), identity_id):
            continue
        created_epoch = parse_iso_utc(doc.get("created_at_utc"))
        if created_epoch > max_seen_epoch:
            max_seen_epoch = created_epoch
        visible_ids.append(broadcast_id)
        if broadcast_id not in existing_read_ids:
            unread_ids.append(broadcast_id)
        if bool(doc.get("requires_ack", False)) and broadcast_id not in existing_acked_ids:
            computed_pending_ack_ids.append(broadcast_id)
            if str(doc.get("severity", "")).strip().lower() == "critical":
                computed_critical_unacked_ids.append(broadcast_id)

    current_pending_ack_ids = sorted(
        {str(item).strip() for item in state_doc.get("pending_ack_ids", []) if str(item).strip()}
    )
    current_critical_unacked_ids = sorted(
        {str(item).strip() for item in state_doc.get("critical_unacked_ids", []) if str(item).strip()}
    )

    read_sync_ok = set(unread_ids) == set() and set(visible_ids).issubset(existing_read_ids)
    parity_ok = current_pending_ack_ids == sorted(computed_pending_ack_ids) and current_critical_unacked_ids == sorted(
        computed_critical_unacked_ids
    )

    if apply_sync:
        state_doc["identity_id"] = str(identity_id or "").strip()
        state_doc["last_seen_created_at_utc"] = (
            datetime.fromtimestamp(max_seen_epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if max_seen_epoch > 0
            else str(state_doc.get("last_seen_created_at_utc", "")).strip()
        )
        state_doc["read_ids"] = sorted(existing_read_ids | set(visible_ids))
        state_doc["acked_ids"] = sorted(existing_acked_ids)
        state_doc["pending_ack_ids"] = sorted(computed_pending_ack_ids)
        state_doc["critical_unacked_ids"] = sorted(computed_critical_unacked_ids)
        state_doc["updated_at_utc"] = utc_now_iso()
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        read_sync_ok = True
        parity_ok = True
        payload["sync_applied"] = True
        unread_ids = []

    if write_receipt:
        receipt_path = resolve_report_path_from_pattern(
            pack_path=pack_path,
            pattern=str(runtime_broadcast_policy.get("instance_receipt_pattern", "")).strip(),
            run_id=run_id,
            fallback_name=HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN.replace("*", "latest"),
        )
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_doc = {
            "schema_version": "v1",
            "identity_id": str(identity_id or "").strip(),
            "actor_id": str(actor_id or "").strip(),
            "session_id": str(session_id or "").strip(),
            "run_id": str(run_id or "").strip(),
            "timestamp_utc": utc_now_iso(),
            "visible_ids": visible_ids,
            "unread_ids": unread_ids,
            "pending_ack_ids": sorted(computed_pending_ack_ids),
            "critical_unacked_ids": sorted(computed_critical_unacked_ids),
            "state_file": str(state_path),
        }
        receipt_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload["broadcast_receipt_path"] = str(receipt_path)

    payload.update(
        {
            "broadcast_visible_count": len(visible_ids),
            "broadcast_unread_count": len(unread_ids),
            "broadcast_pending_ack_count": len(computed_pending_ack_ids),
            "broadcast_critical_unacked_count": len(computed_critical_unacked_ids),
            "visible_ids": visible_ids,
            "unread_ids": unread_ids,
            "pending_ack_ids": sorted(computed_pending_ack_ids),
            "critical_unacked_ids": sorted(computed_critical_unacked_ids),
            "broadcast_delivery_sync_status": STATUS_PASS_REQUIRED if read_sync_ok else STATUS_FAIL_REQUIRED,
            "broadcast_projection_parity_status": STATUS_PASS_REQUIRED if parity_ok else STATUS_FAIL_REQUIRED,
        }
    )
    if read_sync_ok and parity_ok:
        payload["identity_broadcast_delivery_status"] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
        payload["stale_reasons"] = []
    else:
        if not read_sync_ok:
            payload["stale_reasons"].append("broadcast_visibility_not_yet_synced")
        if not parity_ok:
            payload["stale_reasons"].append("broadcast_pending_ack_projection_drift")
    return payload
