#!/usr/bin/env python3
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

SIDECAR_PARITY_TOP_LEVEL_FIELDS = (
    "sidecar_contract_status",
    "sidecar_error_code",
    "required_contract",
    "auto_required_signal",
    "escalation_required",
    "escalation_decision",
    "blocking_error_codes",
)

SIDECAR_PARITY_TRACK_A_FIELDS = (
    "split_status",
    "split_error_code",
    "split_receipt_path",
    "report_selected_path",
    "report_logical_identity_key",
    "report_selection_mode",
    "report_selected_authority_class",
    "report_pointer_resolution_mode",
    "report_pointer_path",
    "report_projection_source",
    "writeback_report_selected_path",
    "writeback_report_logical_identity_key",
    "writeback_report_selection_mode",
    "writeback_report_selected_authority_class",
    "writeback_report_pointer_resolution_mode",
    "writeback_report_pointer_path",
    "post_execution_report_selected_path",
    "post_execution_report_logical_identity_key",
    "post_execution_report_selection_mode",
    "post_execution_report_selected_authority_class",
    "post_execution_report_pointer_resolution_mode",
    "post_execution_report_pointer_path",
    "post_execution_experience_writeback_validation_status",
    "post_execution_experience_writeback_error_code",
    "post_execution_experience_writeback_report_selected_path",
    "post_execution_experience_writeback_report_logical_identity_key",
    "post_execution_experience_writeback_report_selection_mode",
    "post_execution_experience_writeback_report_selected_authority_class",
    "post_execution_experience_writeback_report_pointer_resolution_mode",
    "post_execution_experience_writeback_report_pointer_path",
    "track_a_stale_reasons",
)

SIDECAR_PARITY_TRACK_B_FIELDS = (
    "semantic_routing_status",
    "vendor_namespace_status",
    "protocol_feedback_reply_channel_status",
)


def _normalize_projection_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _normalize_projection_value(item)
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_projection_value(item) for item in value]
    if isinstance(value, str):
        return value.strip()
    return value


def _project_fields(source: Any, *, fields: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        return {}
    return {
        field: _normalize_projection_value(source.get(field))
        for field in fields
    }


def build_protocol_feedback_sidecar_passthrough_projection(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    source = payload if isinstance(payload, Mapping) else {}
    return {
        **_project_fields(source, fields=SIDECAR_PARITY_TOP_LEVEL_FIELDS),
        "track_a": _project_fields(source.get("track_a"), fields=SIDECAR_PARITY_TRACK_A_FIELDS),
        "track_b": _project_fields(source.get("track_b"), fields=SIDECAR_PARITY_TRACK_B_FIELDS),
    }
