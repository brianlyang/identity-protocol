#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import json
import subprocess
import sys
import time
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
from host_visible_final_channel_relay_common import inspect_host_visible_final_channel_relay
from governed_reply_observability_common import build_headstamp_consistency_projection
from governed_reply_transport_lifecycle_common import (
    derive_governed_reply_transport_lifecycle,
    reply_transport_binding_is_projection_eligible,
)
from host_visible_surface_runtime_common import resolve_host_visible_surface_runtime_paths
from protocol_infra_contract import (
    CHAT_EGRESS_POST_CHECK_STATE_UNAVAILABLE_ERROR_CODE,
    CHAT_EGRESS_RAW_BYPASS_ERROR_CODE,
    HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS,
    HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD,
    HOST_VISIBLE_FINAL_CHANNEL_ID,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_CHAT_EGRESS_UNIQUENESS_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
    HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    PRIVILEGE_ESCALATION_ERROR_CODE,
    PRIVILEGE_ESCALATION_REASON_PREFIX,
    PRIVILEGE_ESCALATION_REMEDIATION_HINT,
)
from headstamp_error_family_common import (
    ERR_HDSTAMP_ACTOR_LAYER_MISMATCH,
    ERR_HDSTAMP_MISSING_OR_MALFORMED,
    ERR_HDSTAMP_REPLY_EVIDENCE_MISSING,
    ERR_HDSTAMP_RECEIPT_MISSING,
    inject_legacy_error_fields,
)
from response_stamp_common import (
    REPLY_FIRST_LINE_SURFACE_INVALID,
    parse_reply_first_line_surface,
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
NEXT_HOP_ADMISSION_CONTRACT_ID = "next_hop_admission_tuple_contract_v1"
OUTPUT_GOVERNANCE_MODE_GOVERNED = "governed"
OUTPUT_GOVERNANCE_MODE_MANUAL_HEADSTAMP = "manual_headstamp"
OUTPUT_GOVERNANCE_MODE_HOST_DIRECT = "host_direct"
OUTPUT_GOVERNANCE_MODE_NON_GOVERNED = "non_governed"
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
FIXTURE_ALLOWED_OPERATIONS = {
    normalize_text(item).lower()
    for item in HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS
    if normalize_text(item)
}
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_DIR = SCRIPT_PATH.parent
REPO_ROOT = SCRIPT_DIR.parent


def _stale_reason_contains(stale_reasons: list[str] | tuple[str, ...], token: str) -> bool:
    needle = str(token or "").strip()
    if not needle:
        return False
    for reason in [str(item).strip() for item in stale_reasons if str(item).strip()]:
        if reason == needle or reason.startswith(f"{needle}:"):
            return True
    return False


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


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


def _load_reply_transport_binding(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str,
    session_id: str,
    operation: str,
    evidence_mode: str,
    strict_context: bool,
    reply_transport_ref: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "reply_transport_binding_required": False,
        "reply_transport_binding_status": STATUS_SKIPPED_NOT_REQUIRED,
        "reply_transport_binding_reason": "reply_transport_binding_not_required",
        "reply_transport_binding_error_code": "",
        "reply_transport_binding_issues": [],
        "reply_transport_binding_receipt_paths": [],
        "reply_transport_binding_allowed_sources": [],
        "final_channel_relay_required": False,
        "final_channel_relay_status": STATUS_SKIPPED_NOT_REQUIRED,
        "final_channel_relay_reason": "final_channel_relay_not_required",
        "final_channel_relay_receipt_path": "",
        "final_channel_relay_question_tag": "",
        "final_channel_relay_source_artifact": "",
        "final_channel_relay_validation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "final_channel_relay_validation_error_code": "",
    }
    normalized_mode = str(evidence_mode or "").strip().lower()
    if not strict_context or normalized_mode not in {"reply_file", "reply_log"}:
        return payload

    payload["reply_transport_binding_required"] = True
    allowed_sources = set(HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES)
    payload["reply_transport_binding_allowed_sources"] = sorted(source for source in allowed_sources if source)
    if not str(reply_transport_ref or "").strip():
        payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
        payload["reply_transport_binding_reason"] = "reply_transport_ref_missing"
        payload["reply_transport_binding_error_code"] = ERR_HDSTAMP_RECEIPT_MISSING
        payload["reply_transport_binding_issues"] = ["reply_transport_ref_missing"]
        return payload

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, identity_id)
        task = load_json(task_path)
    except Exception as exc:
        payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
        payload["reply_transport_binding_reason"] = f"reply_transport_binding_resolve_failed:{type(exc).__name__}"
        payload["reply_transport_binding_error_code"] = (
            PRIVILEGE_ESCALATION_ERROR_CODE if _is_privilege_escalation_error(exc) else ERR_HDSTAMP_RECEIPT_MISSING
        )
        payload["reply_transport_binding_issues"] = [payload["reply_transport_binding_reason"]]
        return payload

    host_visible_contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(host_visible_contract, dict) or host_visible_contract.get("required") is not True:
        payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
        payload["reply_transport_binding_reason"] = "host_visible_surface_contract_missing"
        payload["reply_transport_binding_error_code"] = ERR_HDSTAMP_RECEIPT_MISSING
        payload["reply_transport_binding_issues"] = ["host_visible_surface_contract_missing"]
        return payload

    required_channels = _as_list(host_visible_contract.get("required_channels")) or list(
        HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS
    )
    required_pass_status_fields = _as_list(
        host_visible_contract.get("required_pass_status_fields")
    ) or list(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS)
    final_channel_id = (
        str(host_visible_contract.get("final_channel_id", "")).strip()
        or HOST_VISIBLE_FINAL_CHANNEL_ID
    )
    final_channel_relay_required = bool(
        host_visible_contract.get("final_channel_relay_required", HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED)
    )
    payload["final_channel_relay_required"] = final_channel_relay_required
    receipt_pattern = (
        str(host_visible_contract.get("runtime_receipt_pattern", "")).strip()
        or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
    )
    runtime_live_sources = set(_as_list(host_visible_contract.get("runtime_live_receipt_sources")))
    if not runtime_live_sources:
        runtime_live_sources = set(HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES)
    allowed_sources = set(runtime_live_sources)
    fixture_receipt_source = (
        str(host_visible_contract.get("fixture_receipt_source", "")).strip()
        or HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE
    )
    fixture_allowed_operations = {
        normalize_text(item).lower()
        for item in _as_list(host_visible_contract.get("fixture_allowed_operations"))
        if normalize_text(item)
    }
    if not fixture_allowed_operations:
        fixture_allowed_operations = set(FIXTURE_ALLOWED_OPERATIONS)
    if normalize_text(operation).lower() in fixture_allowed_operations and fixture_receipt_source:
        allowed_sources.add(fixture_receipt_source)
    payload["reply_transport_binding_allowed_sources"] = sorted(source for source in allowed_sources if source)
    runtime_receipt_max_age_seconds = _safe_int(
        host_visible_contract.get("runtime_receipt_max_age_seconds"),
        default=HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    )
    if runtime_receipt_max_age_seconds <= 0:
        runtime_receipt_max_age_seconds = int(HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS)

    receipt_glob_path = _resolve_pack_relative_path(pack_path, receipt_pattern, HOST_VISIBLE_SURFACE_RECEIPT_PATTERN)
    if receipt_glob_path.is_file():
        receipt_files = [receipt_glob_path]
    else:
        try:
            receipt_files = sorted(pack_path.glob(receipt_pattern), key=lambda item: item.stat().st_mtime)
        except Exception as exc:
            payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
            payload["reply_transport_binding_reason"] = f"reply_transport_receipt_glob_failed:{type(exc).__name__}"
            payload["reply_transport_binding_error_code"] = (
                PRIVILEGE_ESCALATION_ERROR_CODE if _is_privilege_escalation_error(exc) else ERR_HDSTAMP_RECEIPT_MISSING
            )
            payload["reply_transport_binding_issues"] = [payload["reply_transport_binding_reason"]]
            return payload
    if not receipt_files:
        payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
        payload["reply_transport_binding_reason"] = "reply_transport_live_receipts_missing"
        payload["reply_transport_binding_error_code"] = ERR_HDSTAMP_RECEIPT_MISSING
        payload["reply_transport_binding_issues"] = ["reply_transport_live_receipts_missing"]
        return payload

    matched_by_channel: dict[str, tuple[Path, dict[str, Any]]] = {}
    for receipt_path in receipt_files:
        if not receipt_path.is_file():
            continue
        try:
            receipt_doc = load_json(receipt_path)
        except Exception:
            continue
        channel = str(receipt_doc.get("emit_channel_id", "")).strip()
        if not channel or channel not in required_channels:
            continue
        if str(receipt_doc.get("identity_id", "")).strip() != str(identity_id).strip():
            continue
        if actor_id and str(receipt_doc.get("actor_id", "")).strip() != str(actor_id).strip():
            continue
        if session_id and str(receipt_doc.get("session_id", "")).strip() != str(session_id).strip():
            continue
        if str(receipt_doc.get("reply_transport_ref", "")).strip() != str(reply_transport_ref).strip():
            continue
        receipt_source = str(receipt_doc.get(HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD, "")).strip()
        if receipt_source not in allowed_sources:
            continue
        previous = matched_by_channel.get(channel)
        if previous is None or receipt_path.stat().st_mtime >= previous[0].stat().st_mtime:
            matched_by_channel[channel] = (receipt_path, receipt_doc)

    issues: list[str] = []
    receipt_paths: list[str] = []
    now_epoch = time.time()
    for channel in sorted(set(required_channels)):
        matched = matched_by_channel.get(channel)
        if matched is None:
            issues.append(f"reply_transport_live_receipt_missing:{channel}")
            if channel == final_channel_id and final_channel_relay_required:
                payload["final_channel_relay_status"] = STATUS_FAIL_REQUIRED
                payload["final_channel_relay_reason"] = "final_channel_receipt_missing"
            continue
        receipt_path, receipt_doc = matched
        receipt_paths.append(str(receipt_path))
        age_seconds = max(0, int(now_epoch - receipt_path.stat().st_mtime))
        if age_seconds > runtime_receipt_max_age_seconds:
            issues.append(
                "reply_transport_live_receipt_stale:"
                f"{channel}:age_seconds={age_seconds}:max_age_seconds={runtime_receipt_max_age_seconds}"
            )
        source_value = str(receipt_doc.get(HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD, "")).strip()
        if source_value not in allowed_sources:
            issues.append(f"reply_transport_live_receipt_source_invalid:{channel}:{source_value or 'missing'}")
        if str(receipt_doc.get("reply_transport_ref", "")).strip() != str(reply_transport_ref).strip():
            issues.append(f"reply_transport_live_receipt_ref_mismatch:{channel}")
        for field in sorted(set(required_pass_status_fields)):
            if str(receipt_doc.get(field, "")).strip().upper() != STATUS_PASS_REQUIRED:
                issues.append(f"reply_transport_live_receipt_status_not_pass:{channel}:{field}")
        if channel == final_channel_id and final_channel_relay_required:
            relay_projection = inspect_host_visible_final_channel_relay(
                receipt_doc=receipt_doc,
                repo_root=REPO_ROOT,
                expected_identity_id=str(identity_id).strip(),
                expected_source_artifact=str(reply_transport_ref).strip(),
            )
            payload["final_channel_relay_status"] = str(relay_projection.get("status", "")).strip()
            payload["final_channel_relay_reason"] = str(relay_projection.get("reason", "")).strip()
            payload["final_channel_relay_receipt_path"] = str(
                relay_projection.get("receipt_path", "")
            ).strip()
            payload["final_channel_relay_question_tag"] = str(
                relay_projection.get("question_tag", "")
            ).strip()
            payload["final_channel_relay_source_artifact"] = str(
                relay_projection.get("source_artifact", "")
            ).strip()
            payload["final_channel_relay_validation_status"] = str(
                relay_projection.get("validation_status", "")
            ).strip()
            payload["final_channel_relay_validation_error_code"] = str(
                relay_projection.get("validation_error_code", "")
            ).strip()
            if str(relay_projection.get("status", "")).strip().upper() != STATUS_PASS_REQUIRED:
                relay_issues = [
                    str(item).strip()
                    for item in (relay_projection.get("issues") or [])
                    if str(item).strip()
                ]
                if not relay_issues:
                    relay_issues = [str(relay_projection.get("reason", "")).strip() or "relay_not_pass"]
                for relay_issue in relay_issues:
                    issues.append(f"reply_transport_live_final_channel_{relay_issue}")

    payload["reply_transport_binding_receipt_paths"] = sorted(receipt_paths)
    if issues:
        payload["reply_transport_binding_status"] = STATUS_FAIL_REQUIRED
        payload["reply_transport_binding_reason"] = issues[0]
        payload["reply_transport_binding_error_code"] = ERR_HDSTAMP_RECEIPT_MISSING
        payload["reply_transport_binding_issues"] = issues
        return payload

    payload["reply_transport_binding_status"] = STATUS_PASS_REQUIRED
    payload["reply_transport_binding_reason"] = "reply_transport_bound_to_host_visible_live_receipts"
    payload["reply_transport_binding_issues"] = []
    return payload


def _inject_current_surface_transport_attestation_fields(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload or {})
    evidence_mode = str(out.get("reply_evidence_mode", "")).strip().lower()
    strict_context = evidence_mode in {"reply_file", "reply_log"}
    current_surface_attestation_requested = bool(
        out.get("current_surface_transport_attestation_requested", False)
    )
    live_binding_status = str(out.get("reply_transport_binding_status", "")).strip().upper()
    live_binding_reason = str(out.get("reply_transport_binding_reason", "")).strip()
    live_binding_issues = [
        str(item).strip()
        for item in (out.get("reply_transport_binding_issues") or [])
        if str(item).strip()
    ]
    send_time_status = str(out.get("send_time_gate_status", "")).strip().upper()
    first_line_status = str(out.get("reply_first_line_status", "")).strip().upper()
    final_emit_contract_status = str(out.get("final_emit_contract_status", "")).strip().upper()
    final_emit_channel_id = str(out.get("final_emit_channel_id", "")).strip()
    final_emit_policy_mode = str(out.get("final_emit_policy_mode", "")).strip()
    final_emit_schema_status = str(out.get("final_emit_schema_status", "")).strip().upper()
    outlet_channel_id = str(out.get("outlet_channel_id", "")).strip()
    reply_transport_ref = str(out.get("reply_transport_ref", "")).strip()
    reply_outlet_guard_applied = bool(out.get("reply_outlet_guard_applied", False))
    outlet_bypass_detected = bool(out.get("outlet_bypass_detected", False))

    status = STATUS_SKIPPED_NOT_REQUIRED
    reason = "current_surface_transport_attestation_not_required"
    mode = "not_required"
    current_surface_native_machine_attested = False

    if strict_context:
        status = STATUS_FAIL_REQUIRED
        reason = "current_surface_transport_attestation_prereq_missing"
        mode = "strict_runtime_reply_transport"

        if live_binding_status == STATUS_PASS_REQUIRED:
            status = STATUS_PASS_REQUIRED
            reason = "reply_transport_bound_to_host_visible_live_receipts"
            mode = "live_receipt_binding"
            current_surface_native_machine_attested = current_surface_attestation_requested
        else:
            prereq_ok = (
                current_surface_attestation_requested
                and bool(reply_transport_ref)
                and reply_outlet_guard_applied
                and not outlet_bypass_detected
                and send_time_status == STATUS_PASS_REQUIRED
                and first_line_status == STATUS_PASS_REQUIRED
                and final_emit_contract_status == STATUS_PASS_REQUIRED
                and _is_governed_outlet(outlet_channel_id)
                and _is_host_visible_governed_channel(outlet_channel_id)
                and _is_final_emit_channel(final_emit_channel_id)
                and _is_final_emit_policy_mode(final_emit_policy_mode)
                and _is_final_emit_schema_pass(final_emit_schema_status)
            )
            if prereq_ok and reply_transport_binding_is_projection_eligible(
                reason=live_binding_reason,
                issues=live_binding_issues,
            ):
                status = STATUS_PASS_REQUIRED
                reason = "current_surface_governed_transport_attested_pre_live_receipt"
                mode = "current_surface_projection"
                current_surface_native_machine_attested = True
            elif not bool(reply_transport_ref):
                reason = "reply_transport_ref_missing"
            elif not reply_outlet_guard_applied:
                reason = "reply_outlet_guard_missing"
            elif outlet_bypass_detected:
                reason = "outlet_bypass_detected"
            elif send_time_status != STATUS_PASS_REQUIRED:
                reason = "send_time_gate_not_pass_required"
            elif first_line_status != STATUS_PASS_REQUIRED:
                reason = "reply_first_line_not_pass_required"
            elif final_emit_contract_status != STATUS_PASS_REQUIRED:
                reason = "final_emit_contract_not_pass_required"
            elif not _is_governed_outlet(outlet_channel_id) or not _is_host_visible_governed_channel(
                outlet_channel_id
            ):
                reason = "governed_outlet_not_attested"
            elif not _is_final_emit_channel(final_emit_channel_id):
                reason = "final_emit_channel_not_attested"
            elif not _is_final_emit_policy_mode(final_emit_policy_mode):
                reason = "final_emit_policy_mode_not_attested"
            elif not _is_final_emit_schema_pass(final_emit_schema_status):
                reason = "final_emit_schema_not_pass_required"
            elif live_binding_reason:
                reason = live_binding_reason

    out["current_surface_transport_attestation_contract_id"] = (
        "current_surface_governed_reply_transport_attestation_v1"
    )
    out["current_surface_transport_attestation_requested"] = current_surface_attestation_requested
    out["current_surface_transport_attestation_status"] = status
    out["current_surface_transport_attestation_reason"] = reason
    out["current_surface_transport_attestation_mode"] = mode
    out["current_surface_native_machine_attested"] = current_surface_native_machine_attested
    return out


def _inject_chat_egress_uniqueness_fields(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload or {})
    stale_reasons = [str(item).strip() for item in (out.get("stale_reasons") or []) if str(item).strip()]
    send_time_status = str(out.get("send_time_gate_status", "")).strip().upper()
    first_line_status = str(out.get("reply_first_line_status", "")).strip().upper()
    send_time_block_stage = str(out.get("send_time_block_stage", "")).strip()
    error_code = str(out.get("error_code", "")).strip()
    outlet_bypass_detected = bool(out.get("outlet_bypass_detected", False))

    post_check_state_unavailable = (
        send_time_block_stage == "pre_first_line_post_check_state_unavailable"
        or _stale_reason_contains(stale_reasons, "host_transport_post_check_state_unavailable")
    )
    post_check_blocker_active = (
        send_time_block_stage == "pre_first_line_post_check_blocker_active"
        or _stale_reason_contains(stale_reasons, "host_transport_post_check_blocker_active")
    )

    uniqueness_status = STATUS_PASS_REQUIRED
    uniqueness_reason = "governed_single_egress_enforced"
    uniqueness_error_code = ""

    if send_time_status == STATUS_SKIPPED_NOT_REQUIRED:
        uniqueness_status = STATUS_SKIPPED_NOT_REQUIRED
        uniqueness_reason = "send_time_gate_not_required"
    elif (
        send_time_status != STATUS_PASS_REQUIRED
        or first_line_status != STATUS_PASS_REQUIRED
        or outlet_bypass_detected
        or post_check_state_unavailable
        or post_check_blocker_active
    ):
        uniqueness_status = STATUS_FAIL_REQUIRED
        if post_check_state_unavailable:
            uniqueness_reason = "post_check_state_unavailable_fail_close"
            uniqueness_error_code = error_code or CHAT_EGRESS_POST_CHECK_STATE_UNAVAILABLE_ERROR_CODE
        elif post_check_blocker_active:
            uniqueness_reason = "post_check_blocker_active_next_hop_blocked"
            uniqueness_error_code = CHAT_EGRESS_RAW_BYPASS_ERROR_CODE
        elif outlet_bypass_detected:
            uniqueness_reason = "raw_or_nongoverned_egress_bypass_detected"
            uniqueness_error_code = CHAT_EGRESS_RAW_BYPASS_ERROR_CODE
        elif first_line_status != STATUS_PASS_REQUIRED:
            uniqueness_reason = "headstamp_first_line_gate_failed"
            uniqueness_error_code = error_code or CHAT_EGRESS_RAW_BYPASS_ERROR_CODE
        else:
            uniqueness_reason = "send_time_gate_not_pass"
            uniqueness_error_code = error_code or CHAT_EGRESS_RAW_BYPASS_ERROR_CODE

    out["chat_egress_uniqueness_contract_id"] = HOST_VISIBLE_CHAT_EGRESS_UNIQUENESS_CONTRACT_ID
    out["chat_egress_uniqueness_status"] = uniqueness_status
    out["chat_egress_uniqueness_reason"] = uniqueness_reason
    out["chat_egress_uniqueness_error_code"] = uniqueness_error_code
    out["chat_egress_uniqueness_observed_send_time_status"] = send_time_status
    return out


def _derive_output_governance_mode(payload: dict[str, Any]) -> str:
    outlet_channel_id = str(payload.get("outlet_channel_id", "")).strip()
    evidence_mode = str(payload.get("reply_evidence_mode", "")).strip().lower()
    reply_outlet_guard_applied = bool(payload.get("reply_outlet_guard_applied", False))
    reply_transport_binding_status = str(payload.get("reply_transport_binding_status", "")).strip().upper()
    current_surface_transport_attestation_status = str(
        payload.get("current_surface_transport_attestation_status", "")
    ).strip().upper()
    transport_attested = (
        reply_transport_binding_status == STATUS_PASS_REQUIRED
        or current_surface_transport_attestation_status == STATUS_PASS_REQUIRED
    )
    if evidence_mode == "reply_text":
        return OUTPUT_GOVERNANCE_MODE_HOST_DIRECT
    if evidence_mode in {"stamp_json", "stamp_json_composed_reply"}:
        return OUTPUT_GOVERNANCE_MODE_MANUAL_HEADSTAMP
    if evidence_mode in {"missing", "invalid_input"}:
        return OUTPUT_GOVERNANCE_MODE_NON_GOVERNED
    if evidence_mode in {"reply_file", "reply_log"} and not transport_attested:
        return OUTPUT_GOVERNANCE_MODE_MANUAL_HEADSTAMP
    if not _is_governed_outlet(outlet_channel_id) or not _is_host_visible_governed_channel(outlet_channel_id):
        return OUTPUT_GOVERNANCE_MODE_NON_GOVERNED
    if not reply_outlet_guard_applied:
        return OUTPUT_GOVERNANCE_MODE_HOST_DIRECT
    return OUTPUT_GOVERNANCE_MODE_GOVERNED


def _inject_next_hop_admission_fields(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload or {})
    send_time_status = str(out.get("send_time_gate_status", "")).strip().upper()
    first_line_status = str(out.get("reply_first_line_status", "")).strip().upper()
    final_emit_contract_status = str(out.get("final_emit_contract_status", "")).strip().upper()
    chat_uniqueness_status = str(out.get("chat_egress_uniqueness_status", "")).strip().upper()
    chat_uniqueness_reason = str(out.get("chat_egress_uniqueness_reason", "")).strip()
    chat_uniqueness_error_code = str(out.get("chat_egress_uniqueness_error_code", "")).strip()
    stale_reasons = [str(item).strip() for item in (out.get("stale_reasons") or []) if str(item).strip()]
    outlet_channel_id = str(out.get("outlet_channel_id", "")).strip()
    reply_outlet_guard_applied = bool(out.get("reply_outlet_guard_applied", False))
    outlet_bypass_detected = bool(out.get("outlet_bypass_detected", False))
    reply_transport_binding_status = str(out.get("reply_transport_binding_status", "")).strip().upper()
    current_surface_transport_attestation_status = str(
        out.get("current_surface_transport_attestation_status", "")
    ).strip().upper()
    output_governance_mode = _derive_output_governance_mode(out)
    out["output_governance_mode"] = output_governance_mode
    transport_attested = (
        reply_transport_binding_status == STATUS_PASS_REQUIRED
        or current_surface_transport_attestation_status == STATUS_PASS_REQUIRED
    )

    control_lane_attestation_status = STATUS_PASS_REQUIRED
    control_lane_attestation_reason = "canonical_control_lane_attested"
    if not _is_governed_outlet(outlet_channel_id) or not _is_host_visible_governed_channel(outlet_channel_id):
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "non_governed_control_lane"
    elif not reply_outlet_guard_applied:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "reply_outlet_guard_missing"
    elif outlet_bypass_detected:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "outlet_bypass_detected"
    elif not transport_attested and reply_transport_binding_status not in {
        "",
        STATUS_SKIPPED_NOT_REQUIRED,
        STATUS_PASS_REQUIRED,
    }:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "reply_transport_binding_not_pass"
    elif not transport_attested and reply_transport_binding_status == STATUS_SKIPPED_NOT_REQUIRED and str(
        out.get("reply_evidence_mode", "")
    ).strip().lower() in {"reply_file", "reply_log"}:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "reply_transport_binding_not_pass"
    elif not transport_attested and str(out.get("reply_evidence_mode", "")).strip().lower() in {
        "reply_file",
        "reply_log",
    }:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "reply_transport_binding_not_pass"
    elif final_emit_contract_status != STATUS_PASS_REQUIRED:
        control_lane_attestation_status = STATUS_FAIL_REQUIRED
        control_lane_attestation_reason = "final_emit_contract_not_pass"
    out["control_lane_attestation_status"] = control_lane_attestation_status
    out["control_lane_attestation_reason"] = control_lane_attestation_reason

    post_check_blocker_status = STATUS_PASS_REQUIRED
    post_check_blocker_reason = "post_check_clear"
    if send_time_status == STATUS_SKIPPED_NOT_REQUIRED:
        post_check_blocker_status = STATUS_SKIPPED_NOT_REQUIRED
        post_check_blocker_reason = "send_time_gate_not_required"
    elif (
        str(out.get("send_time_block_stage", "")).strip() == "pre_first_line_post_check_state_unavailable"
        or _stale_reason_contains(stale_reasons, "host_transport_post_check_state_unavailable")
    ):
        post_check_blocker_status = STATUS_FAIL_REQUIRED
        post_check_blocker_reason = "post_check_state_unavailable"
    elif (
        str(out.get("send_time_block_stage", "")).strip() == "pre_first_line_post_check_blocker_active"
        or _stale_reason_contains(stale_reasons, "host_transport_post_check_blocker_active")
        or bool(out.get("host_transport_post_check_blocker_active", False))
    ):
        post_check_blocker_status = STATUS_FAIL_REQUIRED
        post_check_blocker_reason = "post_check_blocker_active"
    out["post_check_blocker_status"] = post_check_blocker_status
    out["post_check_blocker_reason"] = post_check_blocker_reason

    next_hop_admission_status = STATUS_PASS_REQUIRED
    next_hop_admission_reason = "governed_next_hop_admissible"
    next_hop_admission_error_code = ""
    if send_time_status == STATUS_SKIPPED_NOT_REQUIRED:
        next_hop_admission_status = STATUS_SKIPPED_NOT_REQUIRED
        next_hop_admission_reason = "send_time_gate_not_required"
    elif post_check_blocker_status != STATUS_PASS_REQUIRED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = post_check_blocker_reason
    elif output_governance_mode == OUTPUT_GOVERNANCE_MODE_MANUAL_HEADSTAMP:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "manual_headstamp_not_next_hop_admissible"
    elif output_governance_mode == OUTPUT_GOVERNANCE_MODE_HOST_DIRECT:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "host_direct_output_not_next_hop_admissible"
    elif output_governance_mode == OUTPUT_GOVERNANCE_MODE_NON_GOVERNED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "non_governed_output_not_next_hop_admissible"
    elif control_lane_attestation_status != STATUS_PASS_REQUIRED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "control_lane_attestation_not_pass"
    elif first_line_status != STATUS_PASS_REQUIRED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "canonical_headstamp_not_pass"
    elif send_time_status != STATUS_PASS_REQUIRED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = "send_time_gate_not_pass"
    elif chat_uniqueness_status != STATUS_PASS_REQUIRED:
        next_hop_admission_status = STATUS_FAIL_REQUIRED
        next_hop_admission_reason = chat_uniqueness_reason or "chat_egress_uniqueness_not_pass"
    if next_hop_admission_status == STATUS_FAIL_REQUIRED:
        next_hop_admission_error_code = (
            str(out.get("error_code", "")).strip()
            or chat_uniqueness_error_code
            or CHAT_EGRESS_RAW_BYPASS_ERROR_CODE
        )
    out["next_hop_admission_contract_id"] = NEXT_HOP_ADMISSION_CONTRACT_ID
    out["next_hop_admission_status"] = next_hop_admission_status
    out["next_hop_admission_reason"] = next_hop_admission_reason
    out["next_hop_admission_error_code"] = next_hop_admission_error_code
    return out


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


def _is_privilege_escalation_error(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and getattr(exc, "errno", None) in {
        errno.EACCES,
        errno.EPERM,
        errno.EROFS,
    }:
        return True
    return False


def _format_privilege_escalation_reason(*, path: str, scope: str, exc: Exception) -> str:
    safe_scope = str(scope or "").strip() or "unknown_scope"
    safe_path = str(path or "").strip()
    safe_exc = type(exc).__name__
    return (
        f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:{safe_scope}:path={safe_path}:error={safe_exc}:"
        f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
    )


def _load_host_transport_post_check_state(
    catalog_path: Path,
    identity_id: str,
    *,
    host_visible_shadow_root: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "state_file": HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
        "state_path": "",
        "state_status": "STATE_UNCHECKED",
        "state_runtime_scope": "live",
        "state_runtime_shadow_root": "",
        "state_live_path": "",
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
        if _is_privilege_escalation_error(exc):
            payload["state_status"] = "STATE_PERMISSION_DENIED"
            payload["error_code"] = PRIVILEGE_ESCALATION_ERROR_CODE
            payload["stale_reasons"] = [
                _format_privilege_escalation_reason(
                    path=str(catalog_path),
                    scope="host_transport_post_check_state_resolve",
                    exc=exc,
                )
            ]
        else:
            payload["state_status"] = "STATE_RESOLVE_FAILED"
            payload["stale_reasons"] = [f"host_transport_post_check_state_resolve_failed:{type(exc).__name__}"]
        return payload

    contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(contract, dict):
        payload["state_status"] = "STATE_CONTRACT_MISSING"
        payload["stale_reasons"] = ["host_transport_post_check_contract_missing"]
        return payload

    runtime_paths = resolve_host_visible_surface_runtime_paths(
        pack_path=pack_path,
        contract=contract,
        shadow_root=str(host_visible_shadow_root or "").strip(),
    )
    closure_state_file = (
        str(contract.get("post_check_closure_state_file", "")).strip()
        or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
    )
    block_on_active = _as_bool(
        contract.get("post_check_block_on_active", HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        default=bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
    )
    state_path = Path(str(runtime_paths.get("post_check_closure_state_path", ""))).resolve()

    payload["state_file"] = closure_state_file
    payload["state_path"] = str(state_path)
    payload["state_runtime_scope"] = str(runtime_paths.get("runtime_scope", "")).strip() or "live"
    payload["state_runtime_shadow_root"] = str(runtime_paths.get("runtime_shadow_root", "")).strip()
    payload["state_live_path"] = str(runtime_paths.get("live_post_check_closure_state_path", "")).strip()
    payload["block_on_active"] = bool(block_on_active)
    if not state_path.exists() or not state_path.is_file():
        payload["state_status"] = "STATE_MISSING"
        payload["stale_reasons"] = ["host_transport_post_check_state_missing"]
        return payload

    try:
        state_doc = load_json(state_path)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            payload["state_status"] = "STATE_PERMISSION_DENIED"
            payload["error_code"] = PRIVILEGE_ESCALATION_ERROR_CODE
            payload["stale_reasons"] = [
                _format_privilege_escalation_reason(
                    path=str(state_path),
                    scope="host_transport_post_check_state_read",
                    exc=exc,
                )
            ]
        else:
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


def _extract_reply_first_line_surface(reply_text: str) -> dict[str, Any]:
    for raw_line in str(reply_text or "").splitlines():
        line = str(raw_line or "").strip()
        if not line:
            continue
        return parse_reply_first_line_surface(line)
    return {
        "surface_mode": REPLY_FIRST_LINE_SURFACE_INVALID,
        "raw_first_line": "",
        "canonical_identity_context_line": "",
        "display_headstamp_prefix": "",
        "parsed_stamp": {},
    }


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


def _finalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    payload = _inject_current_surface_transport_attestation_fields(payload)
    payload = _inject_chat_egress_uniqueness_fields(payload)
    payload = _inject_next_hop_admission_fields(payload)
    payload.update(
        derive_governed_reply_transport_lifecycle(
            reply_transport_ref=payload.get("reply_transport_ref", ""),
            current_surface_transport_attestation_status=payload.get(
                "current_surface_transport_attestation_status", ""
            ),
            reply_transport_binding_status=payload.get("reply_transport_binding_status", ""),
            final_channel_relay_status=payload.get("final_channel_relay_status", ""),
            reply_transport_source_status=(
                STATUS_PASS_REQUIRED if str(payload.get("reply_transport_ref", "")).strip() else STATUS_FAIL_REQUIRED
            ),
        )
    )
    if not str(payload.get("headstamp_consistency_status", "")).strip():
        payload.update(
            build_headstamp_consistency_projection(
                display_identity_id=str(
                    payload.get(
                        "display_headstamp_identity_id",
                        payload.get("reply_first_line_identity_id", ""),
                    )
                ).strip(),
                authoritative_identity_id=str(
                    payload.get(
                        "authoritative_identity_id",
                        payload.get("identity_authority_authoritative_identity_id", ""),
                    )
                ).strip()
                or str(payload.get("expected_identity_id", payload.get("identity_id", ""))).strip(),
                correction_evidence_ref=str(
                    payload.get("headstamp_correction_evidence_ref", "")
                ).strip(),
            )
        )
    return inject_legacy_error_fields(payload)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    payload = _finalize_payload(payload)
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
    ap.add_argument(
        "--current-surface-native-machine-attested",
        action="store_true",
        help=(
            "mark this send-time validation as running on the controlled current surface "
            "after parent/wrapper attestation succeeded"
        ),
    )
    ap.add_argument("--business-line", default="SEND_TIME_GATE_PROBE_BODY")
    ap.add_argument("--expected-work-layer", default="")
    ap.add_argument("--expected-source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--enforce-send-time-gate", action="store_true")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument(
        "--host-visible-shadow-root",
        default="",
        help=(
            "optional shadow root that mirrors host-visible runtime closure-state for isolated "
            "precheck/replay execution without mutating the live singleton state"
        ),
    )
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
    reply_first_line_surface = _extract_reply_first_line_surface(reply_text)
    display_headstamp_identity_id = str(
        (reply_first_line_surface.get("parsed_stamp") or {}).get("identity_id", "")
    ).strip()
    reply_first_line_surface_mode = str(reply_first_line_surface.get("surface_mode", "")).strip()
    reply_transport_ref = _reply_transport_ref(args, evidence_mode)
    reply_transport_binding = _load_reply_transport_binding(
        catalog_path=catalog_path,
        identity_id=args.identity_id,
        actor_id=str(args.actor_id or "").strip(),
        session_id=str(args.session_id or "").strip(),
        operation=args.operation,
        evidence_mode=evidence_mode,
        strict_context=strict_context,
        reply_transport_ref=reply_transport_ref,
    )
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
    post_check_state = _load_host_transport_post_check_state(
        catalog_path,
        args.identity_id,
        host_visible_shadow_root=str(args.host_visible_shadow_root or "").strip(),
    )
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
        "STATE_PERMISSION_DENIED",
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
        unavailable_error_code = (
            post_check_error_code
            or CHAT_EGRESS_POST_CHECK_STATE_UNAVAILABLE_ERROR_CODE
        )
        if post_check_state_status == "STATE_PERMISSION_DENIED":
            unavailable_error_code = PRIVILEGE_ESCALATION_ERROR_CODE
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
            "error_code": unavailable_error_code,
            "reply_first_line_status": STATUS_SKIPPED_NOT_REQUIRED,
            "reply_first_line_gate_executed": False,
            "send_time_block_stage": "pre_first_line_post_check_state_unavailable",
            "reply_first_line_blocked_reason": "host_transport_post_check_state_unavailable",
            "reply_evidence_mode": evidence_mode,
            "reply_transport_ref": reply_transport_ref,
            "reply_transport_binding_required": bool(reply_transport_binding.get("reply_transport_binding_required", False)),
            "reply_transport_binding_status": str(reply_transport_binding.get("reply_transport_binding_status", "")).strip(),
            "reply_transport_binding_reason": str(reply_transport_binding.get("reply_transport_binding_reason", "")).strip(),
            "reply_transport_binding_error_code": str(
                reply_transport_binding.get("reply_transport_binding_error_code", "")
            ).strip(),
            "reply_transport_binding_issues": list(
                reply_transport_binding.get("reply_transport_binding_issues") or []
            ),
            "reply_transport_binding_receipt_paths": list(
                reply_transport_binding.get("reply_transport_binding_receipt_paths") or []
            ),
            "reply_transport_binding_allowed_sources": list(
                reply_transport_binding.get("reply_transport_binding_allowed_sources") or []
            ),
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
            "reply_first_line_identity_id": display_headstamp_identity_id,
            "reply_first_line_surface_mode": reply_first_line_surface_mode,
            "display_headstamp_identity_id": display_headstamp_identity_id,
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
            "host_transport_post_check_runtime_scope": str(
                post_check_state.get("state_runtime_scope", "")
            ).strip(),
            "host_transport_post_check_runtime_shadow_root": str(
                post_check_state.get("state_runtime_shadow_root", "")
            ).strip(),
            "host_transport_post_check_state_live_path": str(
                post_check_state.get("state_live_path", "")
            ).strip(),
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
            "reply_transport_binding_required": bool(reply_transport_binding.get("reply_transport_binding_required", False)),
            "reply_transport_binding_status": str(reply_transport_binding.get("reply_transport_binding_status", "")).strip(),
            "reply_transport_binding_reason": str(reply_transport_binding.get("reply_transport_binding_reason", "")).strip(),
            "reply_transport_binding_error_code": str(
                reply_transport_binding.get("reply_transport_binding_error_code", "")
            ).strip(),
            "reply_transport_binding_issues": list(
                reply_transport_binding.get("reply_transport_binding_issues") or []
            ),
            "reply_transport_binding_receipt_paths": list(
                reply_transport_binding.get("reply_transport_binding_receipt_paths") or []
            ),
            "reply_transport_binding_allowed_sources": list(
                reply_transport_binding.get("reply_transport_binding_allowed_sources") or []
            ),
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
            "reply_first_line_identity_id": display_headstamp_identity_id,
            "reply_first_line_surface_mode": reply_first_line_surface_mode,
            "display_headstamp_identity_id": display_headstamp_identity_id,
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
            "host_transport_post_check_runtime_scope": str(
                post_check_state.get("state_runtime_scope", "")
            ).strip(),
            "host_transport_post_check_runtime_shadow_root": str(
                post_check_state.get("state_runtime_shadow_root", "")
            ).strip(),
            "host_transport_post_check_state_live_path": str(
                post_check_state.get("state_live_path", "")
            ).strip(),
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
    cmd.extend(["--accepted-surface-modes", "raw_canonical,visible_projection"])

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
        "current_surface_transport_attestation_requested": bool(
            args.current_surface_native_machine_attested
        ),
        "reply_transport_binding_required": bool(reply_transport_binding.get("reply_transport_binding_required", False)),
        "reply_transport_binding_status": str(reply_transport_binding.get("reply_transport_binding_status", "")).strip(),
        "reply_transport_binding_reason": str(reply_transport_binding.get("reply_transport_binding_reason", "")).strip(),
        "reply_transport_binding_error_code": str(
            reply_transport_binding.get("reply_transport_binding_error_code", "")
        ).strip(),
        "reply_transport_binding_issues": list(
            reply_transport_binding.get("reply_transport_binding_issues") or []
        ),
        "reply_transport_binding_receipt_paths": list(
            reply_transport_binding.get("reply_transport_binding_receipt_paths") or []
        ),
        "reply_transport_binding_allowed_sources": list(
            reply_transport_binding.get("reply_transport_binding_allowed_sources") or []
        ),
        "reply_evidence_ref": validator_payload.get("reply_evidence_ref", ""),
        "reply_sample_count": validator_payload.get("reply_sample_count", 0),
        "reply_first_line_missing_count": validator_payload.get("reply_first_line_missing_count", 0),
        "reply_first_line_missing_refs": validator_payload.get("reply_first_line_missing_refs", []),
        "expected_identity_id": validator_payload.get("expected_identity_id", ""),
        "reply_first_line_identity_id": validator_payload.get("reply_first_line_identity_id", ""),
        "reply_first_line_surface_mode": validator_payload.get("reply_first_line_surface_mode", ""),
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
        "identity_authority_status": validator_payload.get("identity_authority_status", ""),
        "identity_authority_error_code": validator_payload.get("identity_authority_error_code", ""),
        "identity_authority_selected_identity_id": validator_payload.get(
            "identity_authority_selected_identity_id", ""
        ),
        "identity_authority_authoritative_identity_id": validator_payload.get(
            "identity_authority_authoritative_identity_id", ""
        ),
        "identity_authority_resolution_mode": validator_payload.get("identity_authority_resolution_mode", ""),
        "identity_authority_next_action": validator_payload.get("identity_authority_next_action", ""),
        "identity_authority_stale_reasons": list(
            validator_payload.get("identity_authority_stale_reasons") or []
        ),
        "host_transport_post_check_state_file": post_check_state_file,
        "host_transport_post_check_state_path": post_check_state_path,
        "host_transport_post_check_state_status": post_check_state_status,
        "host_transport_post_check_runtime_scope": str(
            post_check_state.get("state_runtime_scope", "")
        ).strip(),
        "host_transport_post_check_runtime_shadow_root": str(
            post_check_state.get("state_runtime_shadow_root", "")
        ).strip(),
        "host_transport_post_check_state_live_path": str(
            post_check_state.get("state_live_path", "")
        ).strip(),
        "host_transport_post_check_block_on_active": post_check_block_on_active,
        "host_transport_post_check_blocker_active": post_check_blocker_active,
        "host_transport_post_check_closure_status": post_check_closure_status,
        "host_transport_post_check_error_code": post_check_error_code,
        "blocker_receipt_path": validator_payload.get("blocker_receipt_path", ""),
        "stale_reasons": validator_payload.get("stale_reasons", []),
        "upstream_validator_rc": p.returncode,
    }
    payload.update(
        build_headstamp_consistency_projection(
            display_identity_id=str(
                validator_payload.get(
                    "display_headstamp_identity_id",
                    validator_payload.get("reply_first_line_identity_id", ""),
                )
            ).strip(),
            authoritative_identity_id=str(
                validator_payload.get(
                    "authoritative_identity_id",
                    validator_payload.get("identity_authority_authoritative_identity_id", ""),
                )
            ).strip()
            or str(args.identity_id or "").strip(),
            correction_evidence_ref=str(
                validator_payload.get("headstamp_correction_evidence_ref", "")
            ).strip(),
        )
    )
    if str(error_code).strip() == ERR_RUNTIME_BINDING_MISMATCH:
        payload["outlet_bypass_detected"] = True
    if "blocker_receipt" in validator_payload:
        payload["blocker_receipt"] = validator_payload.get("blocker_receipt")

    final_payload = _finalize_payload(payload)
    if args.json_only:
        print(json.dumps(final_payload, ensure_ascii=False))
    else:
        print(json.dumps(final_payload, ensure_ascii=False, indent=2))
    if str(final_payload.get("next_hop_admission_status", "")).strip().upper() == STATUS_FAIL_REQUIRED:
        return 1
    return 1 if p.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
