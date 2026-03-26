#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


STATUS_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReleaseReadinessActiveRuntimeClosureSpec:
    script_rel: str
    summary_key: str
    one_look_field: str
    status_fields: tuple[str, ...]
    error_fields: tuple[str, ...] = ("error_code",)
    keep_fields: tuple[str, ...] = ()
    one_look_passthrough_fields: tuple[tuple[str, str], ...] = ()


RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS: tuple[ReleaseReadinessActiveRuntimeClosureSpec, ...] = (
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_codex_launcher.py",
        summary_key="identity_codex_launcher",
        one_look_field="identity_codex_launcher_status",
        status_fields=("identity_codex_launcher_status",),
        keep_fields=(
            "shortcut_launcher_shell_discoverability_status",
            "launcher_runtime_admissibility_status",
            "ambient_runtime_default_status",
        ),
        one_look_passthrough_fields=(
            ("shortcut_launcher_shell_discoverability_status", "identity_codex_launcher_shortcut_discoverability_status"),
            ("launcher_runtime_admissibility_status", "identity_codex_launcher_runtime_admissibility_status"),
            ("ambient_runtime_default_status", "identity_codex_launcher_ambient_runtime_default_status"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_context_continuity.py",
        summary_key="identity_context_continuity",
        one_look_field="identity_context_continuity_status",
        status_fields=("identity_context_continuity_status",),
        keep_fields=("lineage_status", "freshness_status", "artifact_kind"),
        one_look_passthrough_fields=(
            ("lineage_status", "identity_context_continuity_lineage_status"),
            ("freshness_status", "identity_context_continuity_freshness_status"),
            ("artifact_kind", "identity_context_continuity_artifact_kind"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_context_continuity_receipts.py",
        summary_key="identity_context_continuity_receipts",
        one_look_field="identity_context_continuity_receipt_family_status",
        status_fields=("identity_context_continuity_receipt_family_status",),
        keep_fields=("receipt_join_status", "receipt_observed_count"),
        one_look_passthrough_fields=(
            ("receipt_join_status", "identity_context_continuity_receipt_join_status"),
            ("receipt_observed_count", "identity_context_continuity_receipt_observed_count"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_reentry_brief.py",
        summary_key="identity_reentry_brief",
        one_look_field="identity_reentry_brief_status",
        status_fields=("identity_reentry_brief_status",),
        keep_fields=("lineage_status", "freshness_status"),
        one_look_passthrough_fields=(
            ("lineage_status", "identity_reentry_brief_lineage_status"),
            ("freshness_status", "identity_reentry_brief_freshness_status"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_reentry_consumption.py",
        summary_key="identity_reentry_consumption",
        one_look_field="identity_reentry_consumption_status",
        status_fields=("identity_reentry_consumption_status",),
        keep_fields=("startup_consumption_status", "launcher_bind_status", "consumption_outcome"),
        one_look_passthrough_fields=(
            ("startup_consumption_status", "identity_reentry_consumption_startup_status"),
            ("launcher_bind_status", "identity_reentry_consumption_launcher_bind_status"),
            ("consumption_outcome", "identity_reentry_consumption_outcome"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_dialogue_retention.py",
        summary_key="identity_dialogue_retention",
        one_look_field="protocol_dialogue_retention_status",
        status_fields=("protocol_dialogue_retention_status",),
        keep_fields=("source_live_alignment_status", "state_binding_status", "source_live_advanced_since_last_sync"),
        one_look_passthrough_fields=(
            ("source_live_alignment_status", "protocol_dialogue_retention_source_live_alignment_status"),
            ("state_binding_status", "protocol_dialogue_retention_state_binding_status"),
            ("source_live_advanced_since_last_sync", "protocol_dialogue_retention_source_live_advanced_since_last_sync"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_artifact_family_routing.py",
        summary_key="identity_artifact_family_routing",
        one_look_field="artifact_family_routing_status",
        status_fields=("artifact_family_routing_status",),
        keep_fields=(
            "runtime_dialogue_retention_family_status",
            "runtime_protocol_feedback_family_status",
            "runtime_continuity_reentry_family_status",
        ),
        one_look_passthrough_fields=(
            ("runtime_dialogue_retention_family_status", "artifact_family_routing_dialogue_retention_family_status"),
            ("runtime_protocol_feedback_family_status", "artifact_family_routing_protocol_feedback_family_status"),
            ("runtime_continuity_reentry_family_status", "artifact_family_routing_continuity_reentry_family_status"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_broadcast_delivery.py",
        summary_key="identity_broadcast_delivery",
        one_look_field="identity_broadcast_delivery_status",
        status_fields=("identity_broadcast_delivery_status",),
        keep_fields=("broadcast_delivery_sync_status", "broadcast_pending_ack_count", "broadcast_critical_unacked_count"),
        one_look_passthrough_fields=(
            ("broadcast_delivery_sync_status", "identity_broadcast_delivery_sync_status"),
            ("broadcast_pending_ack_count", "identity_broadcast_pending_ack_count"),
            ("broadcast_critical_unacked_count", "identity_broadcast_critical_unacked_count"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_communication_transport.py",
        summary_key="identity_communication_transport",
        one_look_field="identity_communication_transport_status",
        status_fields=("identity_communication_transport_status",),
        keep_fields=(
            "protocol_feedback_reply_transport_status",
            "protocol_feedback_atomic_transport_status",
            "broadcast_transport_status",
        ),
        one_look_passthrough_fields=(
            ("protocol_feedback_reply_transport_status", "identity_communication_transport_reply_transport_status"),
            ("protocol_feedback_atomic_transport_status", "identity_communication_transport_atomic_transport_status"),
            ("broadcast_transport_status", "identity_communication_transport_broadcast_transport_status"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_identity_weak_live_linkage.py",
        summary_key="identity_weak_live_linkage",
        one_look_field="identity_weak_live_linkage_status",
        status_fields=("identity_weak_live_linkage_status",),
        keep_fields=(
            "overall_linkage_status",
            "operational_closure_class",
            "live_bridge_status",
            "current_run_pointer_resolution_mode",
        ),
        one_look_passthrough_fields=(
            ("overall_linkage_status", "identity_weak_live_overall_linkage_status"),
            ("operational_closure_class", "identity_weak_live_operational_closure_class"),
            ("live_bridge_status", "identity_weak_live_live_bridge_status"),
            ("current_run_pointer_resolution_mode", "identity_weak_live_pointer_resolution_mode"),
        ),
    ),
    ReleaseReadinessActiveRuntimeClosureSpec(
        script_rel="scripts/validate_terminal_truth_cleanliness.py",
        summary_key="identity_terminal_truth_cleanliness",
        one_look_field="identity_terminal_truth_cleanliness_status",
        status_fields=("identity_terminal_truth_cleanliness_status",),
        keep_fields=("execution_closure_status", "canonical_publishable_result_status", "terminal_truth_class"),
        one_look_passthrough_fields=(
            ("execution_closure_status", "identity_terminal_truth_execution_closure_status"),
            ("canonical_publishable_result_status", "identity_terminal_truth_canonical_publishable_result_status"),
            ("terminal_truth_class", "identity_terminal_truth_class"),
        ),
    ),
)

RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_ONE_LOOK_FIELDS: tuple[str, ...] = tuple(
    spec.one_look_field for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
)
RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS: tuple[str, ...] = (
    "one_look.identity_codex_launcher_ambient_runtime_default_status",
    "one_look.identity_communication_transport_reply_transport_status",
    "one_look.identity_weak_live_operational_closure_class",
    "one_look.identity_terminal_truth_class",
)
RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_OWNER_LANES: tuple[str, ...] = tuple(
    spec.script_rel for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
)
RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER = (
    "active_runtime_closure_projection="
    + "|".join(f"one_look.{field}" for field in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_ONE_LOOK_FIELDS)
)
RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_PROJECTION_MARKER,
    *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_DETAIL_FIELDS,
    *RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_OWNER_LANES,
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _project_one_look_value(field_name: str, value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    text = _clean_str(value)
    if field_name.endswith("_status"):
        return text.upper() or STATUS_UNKNOWN
    return text


def release_readiness_active_runtime_closure_capture_script_map() -> dict[str, str]:
    return {spec.script_rel: spec.summary_key for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS}


def release_readiness_active_runtime_closure_structured_capture_specs() -> dict[str, dict[str, tuple[str, ...]]]:
    return {
        spec.summary_key: {
            "status_fields": spec.status_fields,
            "error_fields": spec.error_fields,
            "keep_fields": spec.keep_fields,
        }
        for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS
    }


def release_readiness_active_runtime_closure_summary_defaults() -> dict[str, dict[str, Any]]:
    return {spec.summary_key: {"status": STATUS_UNKNOWN} for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS}


def apply_release_readiness_active_runtime_closure_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(summary, dict) or not isinstance(one_look, dict):
        return
    for spec in RELEASE_READINESS_ACTIVE_RUNTIME_CLOSURE_SPECS:
        payload = summary.get(spec.summary_key) or {}
        if not isinstance(payload, dict):
            payload = {}
        one_look[spec.one_look_field] = _clean_str(payload.get("status")).upper() or STATUS_UNKNOWN
        for payload_field, one_look_field in spec.one_look_passthrough_fields:
            one_look[one_look_field] = _project_one_look_value(one_look_field, payload.get(payload_field))
