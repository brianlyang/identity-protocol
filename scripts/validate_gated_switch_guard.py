#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SWITCH_ACK_MISSING = "IP-SWITCH-GATE-001"
ERR_SWITCH_ACK_MISMATCH = "IP-SWITCH-HS-002"
ERR_SWITCH_ACK_TIMEOUT = "IP-SWITCH-TIMEOUT-003"
ERR_SWITCH_STATE_REJECTED = "IP-SWITCH-STATE-004"
ERR_SWITCH_POLICY_VIOLATION = "IP-SWITCH-POLICY-005"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

SAFE_SWITCH_STATES = {"WAITING_INPUT", "DONE_WAITING_INPUT", "IDLE"}
BLOCKED_SWITCH_STATES = {"RUNNING", "TOOL_CALLING", "STREAMING"}

PRIMARY_CONTRACT_KEYS = (
    "gated_switch_guard_contract_v1",
    "gated_switch_guard_contract",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _normalize_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            parsed = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in PRIMARY_CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    # legacy compatibility: accept any contract key that clearly denotes gated-switch semantics.
    for key, node in task.items():
        if not isinstance(node, dict):
            continue
        key_norm = str(key or "").strip().lower()
        if "gated_switch" in key_norm and "contract" in key_norm:
            return node
    return {}


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _load_optional_json(path: str) -> tuple[dict[str, Any], str]:
    p_raw = str(path or "").strip()
    if not p_raw:
        return {}, ""
    p = Path(p_raw).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {}, str(p)
    try:
        node = load_json(p)
    except Exception:
        return {}, str(p)
    return node, str(p)


def _nonempty(*values: Any) -> str:
    for value in values:
        token = str(value or "").strip()
        if token:
            return token
    return ""


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate gated-switch guard contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--switch-request", default="", help="optional switch-request receipt json path")
    ap.add_argument("--switch-ack", default="", help="optional switch-ack receipt json path")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--from-identity", default="")
    ap.add_argument("--to-identity", default="")
    ap.add_argument("--execution-state", default="")
    ap.add_argument("--switch-request-ts", default="")
    ap.add_argument("--switch-ack-ts", default="")
    ap.add_argument("--allow-shared-session", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_contract(task)
    required_contract = contract_required(contract)
    auto_required_signal = args.operation in STRICT_OPERATIONS
    enforce_required = required_contract or auto_required_signal

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required_contract,
        "auto_required_signal": auto_required_signal,
        "gated_switch_guard_status": STATUS_SKIPPED_NOT_REQUIRED,
        "switch_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "execution_state": "",
        "switch_requested": False,
        "switch_request_ref": "",
        "switch_ack_ref": "",
        "switch_request_chain": {
            "switch_request": "SKIPPED_NOT_REQUIRED",
            "pre_switch_gate": "SKIPPED_NOT_REQUIRED",
            "switch_apply": "SKIPPED_NOT_REQUIRED",
            "switch_ack": "SKIPPED_NOT_REQUIRED",
            "ack_verify": "SKIPPED_NOT_REQUIRED",
            "dispatch": "SKIPPED_NOT_REQUIRED",
        },
        "switch_ack_verified": False,
        "handshake_latency_seconds": None,
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    switch_req_doc, switch_req_ref = _load_optional_json(args.switch_request)
    switch_ack_doc, switch_ack_ref = _load_optional_json(args.switch_ack)
    payload["switch_request_ref"] = switch_req_ref
    payload["switch_ack_ref"] = switch_ack_ref

    request_actor = _nonempty(args.actor_id, switch_req_doc.get("actor_id"))
    request_session = _nonempty(args.session_id, switch_req_doc.get("session_id"))
    request_from_identity = _nonempty(args.from_identity, switch_req_doc.get("from_identity"), switch_req_doc.get("from_identity_id"))
    request_to_identity = _nonempty(args.to_identity, switch_req_doc.get("to_identity"), switch_req_doc.get("to_identity_id"), args.identity_id)
    request_mode = _nonempty(switch_req_doc.get("switch_mode"), "gated_switch")
    request_allow_shared = _boolish(
        args.allow_shared_session if str(args.allow_shared_session).strip() else switch_req_doc.get("allow_shared_session")
    )
    execution_state = _nonempty(args.execution_state, switch_req_doc.get("execution_state"), "WAITING_INPUT").strip().upper()

    switch_requested = bool(
        switch_req_doc
        or str(args.switch_request).strip()
        or str(args.to_identity).strip()
        or str(args.from_identity).strip()
        or (request_to_identity and request_to_identity != args.identity_id)
    )
    payload["switch_requested"] = switch_requested
    payload["execution_state"] = execution_state
    payload["evidence_ref"] = switch_ack_ref or switch_req_ref or str(task_path)

    if request_allow_shared and request_mode != "gated_switch":
        payload["gated_switch_guard_status"] = STATUS_FAIL_REQUIRED
        payload["switch_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SWITCH_POLICY_VIOLATION
        payload["switch_request_chain"]["switch_request"] = STATUS_PASS_REQUIRED
        payload["switch_request_chain"]["pre_switch_gate"] = STATUS_FAIL_REQUIRED
        payload["switch_request_chain"]["dispatch"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["allow_shared_session_requires_gated_switch_mode"]
        _emit(payload, json_only=args.json_only)
        return 1

    if not enforce_required and not switch_requested:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    # No switch request is acceptable and should not fail-close.
    if not switch_requested:
        payload["gated_switch_guard_status"] = STATUS_PASS_REQUIRED
        payload["switch_gate_status"] = STATUS_PASS_REQUIRED
        payload["switch_request_chain"] = {
            "switch_request": STATUS_SKIPPED_NOT_REQUIRED,
            "pre_switch_gate": STATUS_PASS_REQUIRED,
            "switch_apply": STATUS_SKIPPED_NOT_REQUIRED,
            "switch_ack": STATUS_SKIPPED_NOT_REQUIRED,
            "ack_verify": STATUS_SKIPPED_NOT_REQUIRED,
            "dispatch": STATUS_PASS_REQUIRED,
        }
        payload["stale_reasons"] = ["no_switch_requested"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["switch_request_chain"]["switch_request"] = STATUS_PASS_REQUIRED

    if execution_state in BLOCKED_SWITCH_STATES:
        payload["gated_switch_guard_status"] = STATUS_FAIL_REQUIRED
        payload["switch_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SWITCH_STATE_REJECTED
        payload["switch_request_chain"]["pre_switch_gate"] = STATUS_FAIL_REQUIRED
        payload["switch_request_chain"]["dispatch"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["execution_state_switch_rejected"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["switch_request_chain"]["pre_switch_gate"] = STATUS_PASS_REQUIRED
    payload["switch_request_chain"]["switch_apply"] = STATUS_PASS_REQUIRED

    if not switch_ack_doc:
        payload["gated_switch_guard_status"] = STATUS_FAIL_REQUIRED
        payload["switch_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SWITCH_ACK_MISSING
        payload["switch_request_chain"]["switch_ack"] = STATUS_FAIL_REQUIRED
        payload["switch_request_chain"]["ack_verify"] = STATUS_FAIL_REQUIRED
        payload["switch_request_chain"]["dispatch"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = ["switch_ack_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["switch_request_chain"]["switch_ack"] = STATUS_PASS_REQUIRED

    ack_actor = _nonempty(switch_ack_doc.get("actor_id"), switch_ack_doc.get("identity_context", {}).get("actor_id"))
    ack_session = _nonempty(switch_ack_doc.get("session_id"), switch_ack_doc.get("identity_context", {}).get("session_id"))
    ack_from_identity = _nonempty(
        switch_ack_doc.get("from_identity"),
        switch_ack_doc.get("from_identity_id"),
        switch_ack_doc.get("identity_context", {}).get("from_identity"),
    )
    ack_to_identity = _nonempty(
        switch_ack_doc.get("to_identity"),
        switch_ack_doc.get("to_identity_id"),
        switch_ack_doc.get("identity_context", {}).get("identity_id"),
    )
    ack_mode = _nonempty(switch_ack_doc.get("switch_mode"), request_mode)

    mismatches: list[str] = []
    if request_actor and ack_actor and ack_actor != request_actor:
        mismatches.append("actor_id")
    if request_session and ack_session and ack_session != request_session:
        mismatches.append("session_id")
    if request_from_identity and ack_from_identity and ack_from_identity != request_from_identity:
        mismatches.append("from_identity")
    if request_to_identity and ack_to_identity and ack_to_identity != request_to_identity:
        mismatches.append("to_identity")
    if request_allow_shared and ack_mode != "gated_switch":
        mismatches.append("switch_mode")

    if mismatches:
        payload["gated_switch_guard_status"] = STATUS_FAIL_REQUIRED
        payload["switch_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SWITCH_ACK_MISMATCH
        payload["switch_request_chain"]["ack_verify"] = STATUS_FAIL_REQUIRED
        payload["switch_request_chain"]["dispatch"] = STATUS_FAIL_REQUIRED
        payload["stale_reasons"] = [f"switch_ack_mismatch:{field}" for field in mismatches]
        _emit(payload, json_only=args.json_only)
        return 1

    request_ts = _normalize_ts(_nonempty(args.switch_request_ts, switch_req_doc.get("requested_at"), switch_req_doc.get("switch_request_ts")))
    ack_ts = _normalize_ts(_nonempty(args.switch_ack_ts, switch_ack_doc.get("acknowledged_at"), switch_ack_doc.get("switch_ack_ts")))
    timeout_sec = int(contract.get("handshake_timeout_seconds", 90) or 90)
    if request_ts and ack_ts:
        latency = max(0.0, (ack_ts - request_ts).total_seconds())
        payload["handshake_latency_seconds"] = latency
        if latency > timeout_sec:
            payload["gated_switch_guard_status"] = STATUS_FAIL_REQUIRED
            payload["switch_gate_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_SWITCH_ACK_TIMEOUT
            payload["switch_request_chain"]["ack_verify"] = STATUS_FAIL_REQUIRED
            payload["switch_request_chain"]["dispatch"] = STATUS_FAIL_REQUIRED
            payload["stale_reasons"] = ["switch_ack_timeout"]
            _emit(payload, json_only=args.json_only)
            return 1

    payload["switch_ack_verified"] = True
    payload["switch_request_chain"]["ack_verify"] = STATUS_PASS_REQUIRED
    payload["switch_request_chain"]["dispatch"] = STATUS_PASS_REQUIRED
    payload["gated_switch_guard_status"] = STATUS_PASS_REQUIRED
    payload["switch_gate_status"] = STATUS_PASS_REQUIRED
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
