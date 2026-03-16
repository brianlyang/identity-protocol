#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

HEADSTAMP_VISIBILITY_FIRST_LINE_PASS = "first_line_visible_pass"
HEADSTAMP_VISIBILITY_PRE_FIRST_LINE_BLOCK = "pre_first_line_blocked"
HEADSTAMP_VISIBILITY_FIRST_LINE_FAIL = "first_line_failed"
HEADSTAMP_VISIBILITY_NOT_EVALUATED = "not_evaluated"

SENDER_CONSUMPTION_CONTRACT_REF = "governed_reply_out_reply_file_only_v1"


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_refs(raw_refs: Any) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    if not isinstance(raw_refs, list):
        return refs
    for item in raw_refs:
        if not isinstance(item, dict):
            continue
        refs.append(
            {
                "line_no": str(item.get("line_no", "")).strip(),
                "identity_id": _normalize_text(item.get("identity_id", "")),
                "actor_id": _normalize_text(item.get("actor_id", "")),
                "raw": _normalize_text(item.get("raw", "")),
            }
        )
    return refs


def parse_probe_identity_contexts(*, probe_context_json: str = "", probe_context_file: str = "") -> list[dict[str, Any]]:
    raw_doc: Any = []
    probe_context_json = _normalize_text(probe_context_json)
    probe_context_file = _normalize_text(probe_context_file)
    if probe_context_json:
        try:
            raw_doc = json.loads(probe_context_json)
        except Exception:
            raw_doc = []
    elif probe_context_file:
        try:
            with open(probe_context_file, "r", encoding="utf-8") as fh:
                raw_doc = json.load(fh)
        except Exception:
            raw_doc = []
    if isinstance(raw_doc, dict):
        raw_doc = [raw_doc]
    if not isinstance(raw_doc, list):
        return []

    out: list[dict[str, Any]] = []
    for item in raw_doc:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "identity_id": _normalize_text(item.get("identity_id", "")),
                "actor_id": _normalize_text(item.get("actor_id", "")),
                "session_id": _normalize_text(item.get("session_id", "")),
                "role": _normalize_text(item.get("role", "")) or "probe",
                "source": _normalize_text(item.get("source", "")) or "probe",
                "binding_effect": "none",
            }
        )
    return out


def classify_headstamp_visibility(
    *,
    reply_first_line_status: Any,
    send_time_gate_status: Any,
    headstamp_first_line_status: Any = "",
) -> dict[str, str]:
    first_line = _normalize_text(reply_first_line_status).upper() or _normalize_text(headstamp_first_line_status).upper()
    send_time = _normalize_text(send_time_gate_status).upper()

    if first_line == STATUS_PASS_REQUIRED:
        return {
            "headstamp_visibility_phase": HEADSTAMP_VISIBILITY_FIRST_LINE_PASS,
            "headstamp_visibility_projection_status": STATUS_PASS_REQUIRED,
            "headstamp_visibility_interpretation": "headstamp_first_line_verified",
        }
    if first_line == STATUS_SKIPPED_NOT_REQUIRED and send_time != STATUS_PASS_REQUIRED:
        return {
            "headstamp_visibility_phase": HEADSTAMP_VISIBILITY_PRE_FIRST_LINE_BLOCK,
            "headstamp_visibility_projection_status": STATUS_PASS_REQUIRED,
            "headstamp_visibility_interpretation": "first_line_gate_not_reached_due_to_pre_first_line_block",
        }
    if first_line == STATUS_FAIL_REQUIRED:
        return {
            "headstamp_visibility_phase": HEADSTAMP_VISIBILITY_FIRST_LINE_FAIL,
            "headstamp_visibility_projection_status": STATUS_PASS_REQUIRED,
            "headstamp_visibility_interpretation": "first_line_gate_executed_but_headstamp_or_transport_failed",
        }
    return {
        "headstamp_visibility_phase": HEADSTAMP_VISIBILITY_NOT_EVALUATED,
        "headstamp_visibility_projection_status": STATUS_FAIL_REQUIRED,
        "headstamp_visibility_interpretation": "headstamp_visibility_state_unresolved",
    }


def build_identity_observability_projection(
    *,
    expected_identity_id: str,
    actor_id: str,
    session_id: str,
    effective_bound_identity_id: str = "",
    quoted_identity_context_guard: dict[str, Any] | None = None,
    probe_identity_contexts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    expected_identity_id = _normalize_text(expected_identity_id)
    actor_id = _normalize_text(actor_id)
    session_id = _normalize_text(session_id)
    effective_bound_identity_id = _normalize_text(effective_bound_identity_id) or expected_identity_id
    quoted_guard = quoted_identity_context_guard if isinstance(quoted_identity_context_guard, dict) else {}
    quoted_refs = _normalize_refs(quoted_guard.get("quoted_identity_context_refs"))
    probe_contexts = probe_identity_contexts if isinstance(probe_identity_contexts, list) else []

    return {
        "effective_bound_identity_id": effective_bound_identity_id,
        "effective_bound_actor_id": actor_id,
        "effective_bound_session_id": session_id,
        "effective_identity_projection_status": (
            STATUS_PASS_REQUIRED if effective_bound_identity_id and actor_id and session_id else STATUS_FAIL_REQUIRED
        ),
        "quoted_identity_contexts": quoted_refs,
        "probe_identity_contexts": probe_contexts,
        "binding_effect_summary": {
            "effective_bound_identity_id": effective_bound_identity_id,
            "quoted_identity_context_binding_effect": _normalize_text(
                quoted_guard.get("quoted_identity_context_binding_effect", "")
            )
            or "none",
            "probe_identity_context_binding_effect": "none",
        },
    }


def build_sender_consumption_projection(
    *,
    out_reply_file: Any,
    reply_transport_ref: Any,
    reply_emit_allowed: bool,
) -> dict[str, Any]:
    out_reply_file = _normalize_text(out_reply_file)
    reply_transport_ref = _normalize_text(reply_transport_ref)
    expected_ref = reply_transport_ref or out_reply_file
    projection_status = STATUS_PASS_REQUIRED if expected_ref and out_reply_file and expected_ref == out_reply_file else STATUS_FAIL_REQUIRED
    return {
        "sender_consumption_contract_ref": SENDER_CONSUMPTION_CONTRACT_REF,
        "sender_consumption_contract_required": True,
        "sender_consumption_expected_transport_ref": expected_ref,
        "sender_consumption_allowed_transport_refs": [out_reply_file] if out_reply_file else [],
        "sender_consumption_projection_status": projection_status,
        "next_hop_release_allowed": bool(reply_emit_allowed),
    }
