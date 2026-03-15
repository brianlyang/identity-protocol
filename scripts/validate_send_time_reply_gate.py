#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from final_emit_contract_common import (
    FINAL_EMIT_CHANNEL_ID,
    FINAL_EMIT_POLICY_MODE,
    FINAL_EMIT_SCHEMA_ID,
    normalize_status,
    normalize_text,
)
from protocol_infra_contract import (
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
)
from headstamp_error_family_common import (
    ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
    ERR_HDSTAMP_MISSING_OR_MALFORMED,
    ERR_HDSTAMP_REPLY_EVIDENCE_MISSING,
    ERR_HDSTAMP_RECEIPT_MISSING,
    inject_legacy_error_fields,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

ERR_SEND_TIME_GATE = ERR_HDSTAMP_MISSING_OR_MALFORMED
ERR_SEND_TIME_EVIDENCE_MISSING = ERR_HDSTAMP_REPLY_EVIDENCE_MISSING
ERR_SYNTHETIC_EVIDENCE = ERR_HDSTAMP_RECEIPT_MISSING
ERR_OUTLET_GUARD_MISSING = ERR_HDSTAMP_RECEIPT_MISSING
ERR_NON_GOVERNED_OUTLET = ERR_HDSTAMP_RECEIPT_MISSING
ERR_RUNTIME_BINDING_MISMATCH = ERR_HDSTAMP_ACTOR_LAYER_MISMATCH
ERR_FINAL_EMIT_CHANNEL_REQUIRED = ERR_HDSTAMP_RECEIPT_MISSING
ERR_FINAL_EMIT_SCHEMA_REQUIRED = ERR_HDSTAMP_RECEIPT_MISSING
ERR_GOVERNED_HOST_VISIBLE_CHANNEL_REQUIRED = ERR_HDSTAMP_RECEIPT_MISSING
ERR_POST_CHECK_BLOCKER_ACTIVE = ERR_HDSTAMP_RECEIPT_MISSING
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STRICT_SEND_TIME_OPERATIONS = {
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
    "send-time",
}
HOST_VISIBLE_GOVERNED_CHANNELS = {
    normalize_text(channel).lower()
    for channel in HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS
    if normalize_text(channel)
}
HOST_VISIBLE_GOVERNED_CHANNELS.add(normalize_text(FINAL_EMIT_CHANNEL_ID).lower())
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_DIR.parent


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    rows = [x for x in (data.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _resolve_input_path(raw_path: str) -> Path:
    candidate = Path(str(raw_path or "")).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate
    repo_candidate = (REPO_ROOT / candidate).resolve()
    if repo_candidate.exists():
        return repo_candidate
    return cwd_candidate


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    token = str(value or "").strip().lower()
    if token in {"1", "true", "yes", "on"}:
        return True
    if token in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _resolve_pack_relative_path(pack_path: Path, raw_path: str, fallback_rel: str) -> Path:
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


def _load_host_transport_post_check_state(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "state_file": HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
        "state_path": "",
        "state_status": "STATE_UNCHECKED",
        "block_on_active": bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        "blocker_active": False,
        "closure_status": "",
        "error_code": "",
        "stale_reasons": [],
    }
    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, identity_id)
        task = load_json(task_path)
    except Exception as exc:
        payload["state_status"] = "STATE_RESOLVE_FAILED"
        payload["stale_reasons"] = [f"host_transport_post_check_state_resolve_failed:{type(exc).__name__}"]
        return payload

    contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(contract, dict):
        payload["state_status"] = "STATE_CONTRACT_MISSING"
        payload["stale_reasons"] = ["host_transport_post_check_contract_missing"]
        return payload

    closure_state_file = (
        str(contract.get("post_check_closure_state_file", "")).strip()
        or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
    )
    block_on_active = _as_bool(
        contract.get("post_check_block_on_active", HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        default=bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
    )
    state_path = _resolve_pack_relative_path(
        pack_path,
        closure_state_file,
        HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    )

    payload["state_file"] = closure_state_file
    payload["state_path"] = str(state_path)
    payload["block_on_active"] = bool(block_on_active)
    if not state_path.exists() or not state_path.is_file():
        payload["state_status"] = "STATE_MISSING"
        payload["stale_reasons"] = ["host_transport_post_check_state_missing"]
        return payload

    try:
        state_doc = load_json(state_path)
    except Exception as exc:
        payload["state_status"] = "STATE_INVALID"
        payload["stale_reasons"] = [f"host_transport_post_check_state_invalid:{type(exc).__name__}"]
        return payload

    payload["state_status"] = "STATE_PRESENT"
    payload["blocker_active"] = bool(state_doc.get("blocker_active", False))
    payload["closure_status"] = str(state_doc.get("closure_status", "")).strip().upper()
    payload["error_code"] = str(state_doc.get("error_code", "")).strip()
    payload["stale_reasons"] = [
        str(item).strip() for item in (state_doc.get("stale_reasons") or []) if str(item).strip()
    ]
    return payload


def _parse_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if not text:
        return {}
    try:
        doc = json.loads(text)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _read_stamp_payload(stamp_json_path: Path) -> dict[str, Any]:
    doc = _parse_json_payload(stamp_json_path.read_text(encoding="utf-8"))
    return doc if isinstance(doc, dict) else {}


def _read_stamp_line(stamp_json_path: Path) -> str:
    doc = _read_stamp_payload(stamp_json_path)
    return str(doc.get("external_stamp", "")).strip()


def _reply_text_from_args(args: argparse.Namespace) -> tuple[str, str]:
    """
    Returns (reply_text, evidence_mode).
    """
    if str(args.reply_text or "").strip():
        return str(args.reply_text).strip(), "reply_text"

    if str(args.reply_file or "").strip():
        p = Path(str(args.reply_file)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply file not found: {p}")
        return p.read_text(encoding="utf-8", errors="ignore"), "reply_file"

    if str(args.reply_log or "").strip():
        p = Path(str(args.reply_log)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"reply log not found: {p}")
        # pass-through mode; validator will parse the log directly.
        return "", "reply_log"

    if str(args.stamp_json or "").strip():
        p = Path(str(args.stamp_json)).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"stamp json not found: {p}")
        stamp_line = _read_stamp_line(p)
        if not stamp_line:
            return "", "stamp_json"
        business_line = str(args.business_line or "").strip() or "SEND_TIME_GATE_PROBE_BODY"
        return f"{stamp_line}\n{business_line}\n", "stamp_json_composed_reply"

    return "", "missing"


def _is_strict_send_time_context(operation: str, enforce_send_time_gate: bool) -> bool:
    op = str(operation or "").strip().lower()
    return bool(enforce_send_time_gate) or op in STRICT_SEND_TIME_OPERATIONS


def _reply_transport_ref(args: argparse.Namespace, evidence_mode: str) -> str:
    explicit = str(args.reply_transport_ref or "").strip()
    if explicit:
        return explicit
    if evidence_mode == "reply_file":
        return str(Path(str(args.reply_file or "")).expanduser().resolve())
    if evidence_mode == "reply_log":
        return str(Path(str(args.reply_log or "")).expanduser().resolve())
    if evidence_mode == "reply_text":
        return "inline:reply_text"
    if evidence_mode in {"stamp_json", "stamp_json_composed_reply"}:
        return str(Path(str(args.stamp_json or "")).expanduser().resolve())
    return "unresolved"


def _is_governed_outlet(channel_id: str) -> bool:
    cid = str(channel_id or "").strip().lower()
    if not cid:
        return False
    if cid in HOST_VISIBLE_GOVERNED_CHANNELS:
        return True
    return cid.startswith("governed_") or cid.startswith("governed-") or cid in {"governed", "governedoutlet"}


def _is_host_visible_governed_channel(channel_id: str) -> bool:
    return normalize_text(channel_id).lower() in HOST_VISIBLE_GOVERNED_CHANNELS


def _is_final_emit_channel(channel_id: str) -> bool:
    return normalize_text(channel_id).lower() == FINAL_EMIT_CHANNEL_ID


def _is_final_emit_policy_mode(policy_mode: str) -> bool:
    return normalize_text(policy_mode).lower() == FINAL_EMIT_POLICY_MODE


def _is_final_emit_schema_pass(schema_status: str) -> bool:
    return normalize_status(schema_status) == STATUS_PASS_REQUIRED


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    payload = inject_legacy_error_fields(payload)
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Unified send-time gate for governed user-visible reply channel. "
            "Fails closed on missing first-line Identity-Context and emits blocker receipt."
        )
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="", help="optional actor session selector (run:<id>) for strict M:N binding checks")
    ap.add_argument("--reply-text", default="")
    ap.add_argument("--reply-file", default="")
    ap.add_argument("--reply-log", default="")
    ap.add_argument("--stamp-json", default="", help="optional fallback to compose send-time reply from external_stamp")
    ap.add_argument("--reply-transport-ref", default="")
    ap.add_argument(
        "--outlet-channel-id",
        default=FINAL_EMIT_CHANNEL_ID,
        help="logical reply outlet channel id; strict operations require governed host-visible channel",
    )
    ap.add_argument(
        "--final-emit-policy-mode",
        default=FINAL_EMIT_POLICY_MODE,
        help="final emission policy mode; strict operations require tool_choice_required",
    )
    ap.add_argument(
        "--final-emit-schema-status",
        default=STATUS_PASS_REQUIRED,
        help="final emission schema validation status",
    )
    ap.add_argument(
        "--final-emit-schema-id",
        default=FINAL_EMIT_SCHEMA_ID,
        help="final emission schema identifier",
    )
    ap.add_argument("--reply-outlet-guard-applied", action="store_true")
    ap.add_argument("--business-line", default="SEND_TIME_GATE_PROBE_BODY")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-send-time-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument(
        "--operation",
        choices=[
            "activate",
            "update",
            "mutation",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "scan",
            "three-plane",
            "inspection",
            "send-time",
        ],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()
    strict_context_hint = _is_strict_send_time_context(args.operation, args.enforce_send_time_gate)

    catalog_path = _resolve_input_path(args.catalog)
    repo_catalog_path = _resolve_input_path(args.repo_catalog)
    if catalog_path.exists() and _is_fixture_identity(catalog_path, args.identity_id):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": False,
            "send_time_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "reply_evidence_mode": "fixture_skip",
            "reply_transport_ref": "",
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": False,
            "outlet_channel_id": str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": str(args.final_emit_policy_mode or "").strip() or FINAL_EMIT_POLICY_MODE,
            "final_emit_schema_id": str(args.final_emit_schema_id or "").strip() or FINAL_EMIT_SCHEMA_ID,
            "final_emit_schema_status": str(args.final_emit_schema_status or "").strip().upper() or STATUS_PASS_REQUIRED,
            "final_emit_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
            "outlet_preflight_receipt": "",
            "outlet_bypass_detected": False,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "fixture_profile_scope",
            "fallback_reason": "fixture_profile_scope",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["fixture_profile_scope"],
            "upstream_validator_rc": 0,
        }
        _emit(payload, json_only=args.json_only)
        return 0

    try:
        reply_text, evidence_mode = _reply_text_from_args(args)
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "send_time_gate_status": STATUS_FAIL_REQUIRED if strict_context_hint else STATUS_WARN_NON_BLOCKING,
            "error_code": ERR_SEND_TIME_EVIDENCE_MISSING,
            "reply_evidence_mode": "invalid_input",
            "reply_transport_ref": "invalid_input",
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["input:missing_or_invalid"],
            "blocker_receipt_path": "",
            "stale_reasons": [f"send_time_input_invalid:{exc}"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    strict_context = _is_strict_send_time_context(args.operation, args.enforce_send_time_gate)
    reply_transport_ref = _reply_transport_ref(args, evidence_mode)
    outlet_channel_id = str(args.outlet_channel_id or "").strip() or FINAL_EMIT_CHANNEL_ID
    host_visible_governed_channel_ok = _is_host_visible_governed_channel(outlet_channel_id)
    governed_outlet = _is_governed_outlet(outlet_channel_id)
    final_emit_channel_ok = _is_final_emit_channel(outlet_channel_id)
    final_emit_policy_mode = str(args.final_emit_policy_mode or "").strip() or FINAL_EMIT_POLICY_MODE
    final_emit_policy_ok = _is_final_emit_policy_mode(final_emit_policy_mode)
    final_emit_schema_id = str(args.final_emit_schema_id or "").strip() or FINAL_EMIT_SCHEMA_ID
    final_emit_schema_status = str(args.final_emit_schema_status or "").strip().upper() or STATUS_PASS_REQUIRED
    final_emit_schema_ok = _is_final_emit_schema_pass(final_emit_schema_status)
    if final_emit_channel_ok:
        final_emit_contract_ok = final_emit_policy_ok and final_emit_schema_ok
    else:
        final_emit_contract_ok = host_visible_governed_channel_ok
    final_emit_contract_status = STATUS_PASS_REQUIRED if final_emit_contract_ok else STATUS_FAIL_REQUIRED
    strict_outlet_enforced = strict_context and governed_outlet and bool(args.reply_outlet_guard_applied)
    preflight_receipt_ref = str(Path(args.blocker_receipt_out).expanduser().resolve()) if str(args.blocker_receipt_out or "").strip() else ""
    post_check_state = _load_host_transport_post_check_state(catalog_path, args.identity_id)
    post_check_blocker_active = bool(post_check_state.get("blocker_active", False))
    post_check_block_on_active = bool(post_check_state.get("block_on_active", False))
    post_check_state_file = str(post_check_state.get("state_file", "")).strip()
    post_check_state_path = str(post_check_state.get("state_path", "")).strip()
    post_check_state_status = str(post_check_state.get("state_status", "")).strip()
    post_check_error_code = str(post_check_state.get("error_code", "")).strip()
    post_check_closure_status = str(post_check_state.get("closure_status", "")).strip()
    post_check_stale_reasons = list(post_check_state.get("stale_reasons") or [])
    post_check_state_unavailable = post_check_state_status in {
        "STATE_UNCHECKED",
        "STATE_MISSING",
        "STATE_INVALID",
        "STATE_RESOLVE_FAILED",
        "STATE_CONTRACT_MISSING",
    }

    if strict_context and post_check_block_on_active and post_check_state_unavailable:
        stale_reasons = ["host_transport_post_check_state_unavailable"]
        if post_check_state_status:
            stale_reasons.append(f"host_transport_post_check_state_status:{post_check_state_status}")
        if post_check_error_code:
            stale_reasons.append(f"host_transport_post_check_error_code:{post_check_error_code}")
        stale_reasons.extend(
            [f"host_transport_post_check_reason:{reason}" for reason in post_check_stale_reasons if str(reason).strip()]
        )
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_POST_CHECK_BLOCKER_ACTIVE,
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "reply_first_line_gate_executed": False,
            "send_time_block_stage": "pre_first_line_post_check_state_unavailable",
            "reply_first_line_blocked_reason": "host_transport_post_check_state_unavailable",
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "host_transport_post_check_guard",
            "fallback_reason": "host_transport_post_check_state_unavailable",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "host_transport_post_check_state_file": post_check_state_file,
            "host_transport_post_check_state_path": post_check_state_path,
            "host_transport_post_check_state_status": post_check_state_status,
            "host_transport_post_check_block_on_active": post_check_block_on_active,
            "host_transport_post_check_blocker_active": post_check_blocker_active,
            "host_transport_post_check_closure_status": post_check_closure_status,
            "host_transport_post_check_error_code": post_check_error_code,
            "stale_reasons": stale_reasons,
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and post_check_block_on_active and post_check_blocker_active:
        stale_reasons = ["host_transport_post_check_blocker_active"]
        if post_check_error_code:
            stale_reasons.append(f"host_transport_post_check_error_code:{post_check_error_code}")
        if post_check_closure_status:
            stale_reasons.append(f"host_transport_post_check_closure_status:{post_check_closure_status}")
        stale_reasons.extend(
            [f"host_transport_post_check_reason:{reason}" for reason in post_check_stale_reasons if str(reason).strip()]
        )
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_POST_CHECK_BLOCKER_ACTIVE,
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "reply_first_line_gate_executed": False,
            "send_time_block_stage": "pre_first_line_post_check_blocker_active",
            "reply_first_line_blocked_reason": "host_transport_post_check_blocker_active",
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 0,
            "reply_first_line_missing_refs": [],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "host_transport_post_check_guard",
            "fallback_reason": "host_transport_post_check_blocker_active",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "host_transport_post_check_state_file": post_check_state_file,
            "host_transport_post_check_state_path": post_check_state_path,
            "host_transport_post_check_state_status": post_check_state_status,
            "host_transport_post_check_block_on_active": post_check_block_on_active,
            "host_transport_post_check_blocker_active": post_check_blocker_active,
            "host_transport_post_check_closure_status": post_check_closure_status,
            "host_transport_post_check_error_code": post_check_error_code,
            "stale_reasons": stale_reasons,
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and not host_visible_governed_channel_ok:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_GOVERNED_HOST_VISIBLE_CHANNEL_REQUIRED,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": False,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": STATUS_FAIL_REQUIRED,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["host_visible_governed_channel_required"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "host_visible_governed_channel_required",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_governed_host_visible_channel_required"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and final_emit_channel_ok and not final_emit_policy_ok:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_FINAL_EMIT_CHANNEL_REQUIRED,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": False,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": STATUS_FAIL_REQUIRED,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["final_emit_policy_mode_not_required"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "final_emit_policy_mode_not_required",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_final_emit_policy_mode_required"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and final_emit_channel_ok and not final_emit_schema_ok:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_FINAL_EMIT_SCHEMA_REQUIRED,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": False,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": STATUS_FAIL_REQUIRED,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["final_emit_schema_not_pass"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "final_emit_schema_not_pass",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_final_emit_schema_required"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and not governed_outlet:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_NON_GOVERNED_OUTLET,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["non_governed_outlet_channel"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "non_governed_outlet_channel",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_non_governed_outlet_forbidden"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    if strict_context and evidence_mode in {"reply_text", "stamp_json", "stamp_json_composed_reply", "missing"}:
        if evidence_mode == "missing":
            synthetic_reason = "strict_send_time_reply_evidence_missing"
            synthetic_error_code = ERR_SEND_TIME_EVIDENCE_MISSING
            missing_refs = ["strict_reply_evidence_missing"]
        elif evidence_mode == "reply_text":
            synthetic_reason = "strict_send_time_inline_reply_text_forbidden"
            synthetic_error_code = ERR_SYNTHETIC_EVIDENCE
            missing_refs = ["strict_evidence_source_not_live"]
        else:
            synthetic_reason = "strict_send_time_synthetic_evidence_forbidden"
            synthetic_error_code = ERR_SYNTHETIC_EVIDENCE
            missing_refs = ["strict_evidence_source_not_live"]
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": synthetic_error_code,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
            "governed_outlet_enforced": strict_outlet_enforced,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": missing_refs,
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "synthetic_reply_evidence_forbidden",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": [synthetic_reason],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1
    if strict_context and not bool(args.reply_outlet_guard_applied):
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "validator_operation": "validate" if args.operation == "send-time" else args.operation,
            "send_time_gate_enforced": bool(args.enforce_send_time_gate),
            "required_contract": True,
            "expected_work_layer": str(args.expected_work_layer or "").strip(),
            "expected_source_layer": str(args.expected_source_layer or "").strip(),
            "layer_intent_text": str(args.layer_intent_text or "").strip(),
            "send_time_gate_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_OUTLET_GUARD_MISSING,
            "reply_first_line_status": STATUS_FAIL_REQUIRED,
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_outlet_guard_applied": False,
            "governed_outlet_enforced": False,
            "outlet_channel_id": outlet_channel_id,
            "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "outlet_preflight_receipt": preflight_receipt_ref,
            "outlet_bypass_detected": True,
            "reply_evidence_ref": "",
            "reply_sample_count": 0,
            "reply_first_line_missing_count": 1,
            "reply_first_line_missing_refs": ["reply_outlet_guard_not_applied"],
            "expected_identity_id": args.identity_id,
            "reply_first_line_work_layer": "",
            "reply_first_line_source_layer": "",
            "expected_source_layer_input": "",
            "expected_source_layer_effective": "",
            "expected_source_layer_validation_status": "",
            "expected_source_layer_validation_error_code": "",
            "source_layer_downgrade_applied": False,
            "layer_intent_resolution_status": "",
            "resolved_work_layer": "",
            "resolved_source_layer": "",
            "intent_confidence": 0.0,
            "intent_source": "strict_send_time_guard",
            "fallback_reason": "reply_outlet_guard_missing",
            "protocol_triggered": False,
            "protocol_trigger_reasons": [],
            "protocol_trigger_confidence": 0.0,
            "blocker_receipt_path": "",
            "stale_reasons": ["strict_send_time_outlet_guard_missing"],
            "upstream_validator_rc": 1,
        }
        _emit(payload, json_only=args.json_only)
        return 1

    expected_work_layer = str(args.expected_work_layer or "").strip()
    expected_source_layer = str(args.expected_source_layer or "").strip()
    layer_intent_text = str(args.layer_intent_text or "").strip()
    stamp_payload: dict[str, Any] = {}
    if str(args.stamp_json or "").strip():
        stamp_path = Path(str(args.stamp_json)).expanduser().resolve()
        if stamp_path.exists():
            stamp_payload = _read_stamp_payload(stamp_path)
    if not expected_work_layer:
        expected_work_layer = str(stamp_payload.get("resolved_work_layer", "")).strip() or str(
            stamp_payload.get("work_layer", "")
        ).strip()
    if not expected_source_layer:
        expected_source_layer = str(stamp_payload.get("resolved_source_layer", "")).strip() or str(
            stamp_payload.get("source_layer", "")
        ).strip()
    if not layer_intent_text:
        layer_intent_text = str(stamp_payload.get("layer_intent_text", "")).strip()

    op_for_validator = "validate" if args.operation == "send-time" else args.operation
    cmd = [
        sys.executable,
        str((SCRIPT_DIR / "validate_reply_identity_context_first_line.py").resolve()),
        "--identity-id",
        args.identity_id,
        "--catalog",
        str(catalog_path),
        "--repo-catalog",
        str(repo_catalog_path),
        "--operation",
        op_for_validator,
        "--json-only",
    ]
    if str(args.actor_id or "").strip():
        cmd.extend(["--actor-id", str(args.actor_id).strip()])
    if str(args.session_id or "").strip():
        cmd.extend(["--session-id", str(args.session_id).strip()])
    if args.force_check:
        cmd.append("--force-check")
    if args.enforce_send_time_gate:
        cmd.append("--enforce-first-line-gate")
    if str(args.blocker_receipt_out or "").strip():
        cmd.extend(["--blocker-receipt-out", str(args.blocker_receipt_out).strip()])
    if expected_work_layer:
        cmd.extend(["--expected-work-layer", expected_work_layer])
    if expected_source_layer:
        cmd.extend(["--expected-source-layer", expected_source_layer])
    if layer_intent_text:
        cmd.extend(["--layer-intent-text", layer_intent_text])
    if evidence_mode == "reply_log":
        cmd.extend(["--reply-log", str(args.reply_log).strip()])
    elif reply_text:
        cmd.extend(["--reply-text", reply_text])

    p = subprocess.run(cmd, capture_output=True, text=True)
    validator_payload = _parse_json_payload(p.stdout)

    first_line_status = str(validator_payload.get("reply_first_line_status", "")).strip() or (
        STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED
    )
    first_line_gate_executed = bool(validator_payload.get("reply_first_line_gate_executed", True))
    send_time_block_stage = str(validator_payload.get("send_time_block_stage", "")).strip()
    if not send_time_block_stage:
        send_time_block_stage = "first_line_gate" if first_line_gate_executed else "unknown"
    first_line_blocked_reason = str(validator_payload.get("reply_first_line_blocked_reason", "")).strip()
    error_code = str(validator_payload.get("error_code", "")).strip()
    if p.returncode != 0 and not error_code:
        error_code = ERR_SEND_TIME_EVIDENCE_MISSING if evidence_mode == "missing" else ERR_SEND_TIME_GATE

    send_time_status = first_line_status
    if send_time_status not in {
        STATUS_PASS_REQUIRED,
        STATUS_FAIL_REQUIRED,
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_WARN_NON_BLOCKING,
    }:
        send_time_status = STATUS_PASS_REQUIRED if p.returncode == 0 else STATUS_FAIL_REQUIRED

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "validator_operation": op_for_validator,
        "send_time_gate_enforced": bool(args.enforce_send_time_gate),
        "required_contract": bool(validator_payload.get("required_contract", False)),
        "reply_outlet_guard_applied": bool(args.reply_outlet_guard_applied),
        "governed_outlet_enforced": strict_outlet_enforced,
        "outlet_channel_id": outlet_channel_id,
        "final_emit_channel_id": FINAL_EMIT_CHANNEL_ID,
        "final_emit_policy_mode": final_emit_policy_mode,
        "final_emit_schema_id": final_emit_schema_id,
        "final_emit_schema_status": final_emit_schema_status,
        "final_emit_contract_status": final_emit_contract_status,
        "outlet_preflight_receipt": preflight_receipt_ref,
        "outlet_bypass_detected": bool(
            (strict_context and not governed_outlet)
            or (strict_context and not bool(args.reply_outlet_guard_applied))
            or (strict_context and final_emit_channel_ok and not final_emit_contract_ok)
            or str(error_code).strip() == ERR_NON_GOVERNED_OUTLET
        ),
        "expected_work_layer": expected_work_layer,
        "expected_source_layer": expected_source_layer,
        "layer_intent_text": layer_intent_text,
        "send_time_gate_status": send_time_status,
        "error_code": error_code,
        "reply_first_line_status": first_line_status,
        "reply_first_line_gate_executed": first_line_gate_executed,
        "send_time_block_stage": send_time_block_stage,
        "reply_first_line_blocked_reason": first_line_blocked_reason,
        "reply_evidence_mode": evidence_mode,
        "reply_transport_ref": reply_transport_ref,
        "reply_evidence_ref": validator_payload.get("reply_evidence_ref", ""),
        "reply_sample_count": validator_payload.get("reply_sample_count", 0),
        "reply_first_line_missing_count": validator_payload.get("reply_first_line_missing_count", 0),
        "reply_first_line_missing_refs": validator_payload.get("reply_first_line_missing_refs", []),
        "expected_identity_id": validator_payload.get("expected_identity_id", ""),
        "reply_first_line_work_layer": validator_payload.get("reply_first_line_work_layer", ""),
        "reply_first_line_source_layer": validator_payload.get("reply_first_line_source_layer", ""),
        "expected_source_layer_input": validator_payload.get("expected_source_layer_input", ""),
        "expected_source_layer_effective": validator_payload.get("expected_source_layer_effective", ""),
        "expected_source_layer_validation_status": validator_payload.get("expected_source_layer_validation_status", ""),
        "expected_source_layer_validation_error_code": validator_payload.get("expected_source_layer_validation_error_code", ""),
        "source_layer_downgrade_applied": validator_payload.get("source_layer_downgrade_applied", False),
        "layer_intent_resolution_status": validator_payload.get("layer_intent_resolution_status", ""),
        "resolved_work_layer": validator_payload.get("resolved_work_layer", ""),
        "resolved_source_layer": validator_payload.get("resolved_source_layer", ""),
        "intent_confidence": validator_payload.get("intent_confidence"),
        "intent_source": validator_payload.get("intent_source", ""),
        "fallback_reason": validator_payload.get("fallback_reason", ""),
        "protocol_triggered": bool(validator_payload.get("protocol_triggered", False)),
        "protocol_trigger_reasons": validator_payload.get("protocol_trigger_reasons", []),
        "protocol_trigger_confidence": validator_payload.get("protocol_trigger_confidence", 0.0),
        "host_transport_post_check_state_file": post_check_state_file,
        "host_transport_post_check_state_path": post_check_state_path,
        "host_transport_post_check_state_status": post_check_state_status,
        "host_transport_post_check_block_on_active": post_check_block_on_active,
        "host_transport_post_check_blocker_active": post_check_blocker_active,
        "host_transport_post_check_closure_status": post_check_closure_status,
        "host_transport_post_check_error_code": post_check_error_code,
        "blocker_receipt_path": validator_payload.get("blocker_receipt_path", ""),
        "stale_reasons": validator_payload.get("stale_reasons", []),
        "upstream_validator_rc": p.returncode,
    }
    if str(error_code).strip() == ERR_RUNTIME_BINDING_MISMATCH:
        payload["outlet_bypass_detected"] = True
    if "blocker_receipt" in validator_payload:
        payload["blocker_receipt"] = validator_payload.get("blocker_receipt")

    _emit(payload, json_only=args.json_only)
    return 1 if p.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
