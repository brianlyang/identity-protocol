#!/usr/bin/env python3
from __future__ import annotations

"""Canonical infrastructure contract for protocol governance streams.

This module centralizes path/mode constants used by v1.6.1-v1.6.6 control-plane
scripts so strict surfaces do not drift into ad-hoc hardcoded routing literals.
"""

# Canonical protocol ingress/egress authorities.
CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT = "scripts/required_gate_bundle_runner.py"
CANONICAL_FINAL_EMIT_SCRIPT = "scripts/final_emit_governed.py"

# Host gateway contract keys and mandatory modes.
HOST_GATEWAY_CONTRACT_KEY = "protocol_host_unique_channel_contract_v1"
HOST_GATEWAY_CONTRACT_ID = "protocol_host_unique_channel_contract_v1"
HOST_GATEWAY_CONTRACT_KEYS: tuple[str, ...] = (
    HOST_GATEWAY_CONTRACT_KEY,
    "protocol_gateway_wrapper_contract_v1",
    "protocol_gateway_contract_v1",
)
HOST_GATEWAY_REQUIRED_DISPATCH_MODE = "wrapper_only"
HOST_GATEWAY_REQUIRED_RELEASE_MODE = "wrapper_only"

# Wrapper runtime defaults (relative to identity pack root).
HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER = "runtime/gate/protocol_ingress_wrapper.py"
HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER = "runtime/gate/protocol_egress_wrapper.py"
HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER = "runtime/gate/protocol_session_chain_wrapper.py"
HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT = "runtime/gate/protocol_gateway_contract.json"
HOST_GATEWAY_DEFAULT_SIGNING_KEY = "runtime/state/protocol_gateway_signing_key.txt"

# Runtime file governance boundary classes (v1.6.10).
PROTOCOL_GENERATED_GATEWAY_SHELL_TERM = "protocol_generated_gateway_shell"
PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_TERM = "protocol_controlled_mirror_artifact"
INSTANCE_AUTONOMOUS_RUNTIME_TERM = "instance_autonomous_runtime"
PROTOCOL_GENERATED_GATEWAY_SHELL_PATHS: tuple[str, ...] = (
    HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
)
PROTOCOL_CONTROLLED_MIRROR_ARTIFACT_PATHS: tuple[str, ...] = (
    HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT,
)

# Wrapper runtime contract paths (identity-relative form).
HOST_GATEWAY_RELATIVE_CONTRACT_PATH = "identity/runtime/gate/protocol_gateway_contract.json"
HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH = "identity/runtime/gate/protocol_ingress_wrapper.py"
HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH = "identity/runtime/gate/protocol_egress_wrapper.py"
HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH = (
    "identity/runtime/gate/protocol_session_chain_wrapper.py"
)
HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH = "identity/runtime/state/protocol_gateway_signing_key.txt"

# Wrapper provenance defaults.
HOST_GATEWAY_INGRESS_DISPATCH_TOKEN = "instance_wrapper_ingress_v1"
HOST_GATEWAY_REQUIRED_SURFACE_LABEL = "host_ingress_wrapper"
HOST_GATEWAY_REQUIRED_SURFACE_STATUS = "PASS_REQUIRED"
HOST_GATEWAY_REQUIRED_DISPATCH_STATUS = "PASS_REQUIRED"
HOST_GATEWAY_REQUIRED_TUPLE_FIELDS: tuple[str, ...] = (
    "actor_id",
    "session_id",
    "run_id",
    "work_layer",
    "source_layer",
)

# Operation profile defaults.
HOST_GATEWAY_STRICT_OPERATIONS: tuple[str, ...] = (
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
)
HOST_GATEWAY_LIGHT_OPERATIONS: tuple[str, ...] = (
    "inspection",
    "scan",
    "status",
)
HOST_GATEWAY_STRICT_GATE_PROFILE = "strict_full"
HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION: dict[str, str] = {
    "three-plane": "three_plane_core",
}
HOST_GATEWAY_LIGHT_GATE_PROFILE = "inspection_targeted"
HOST_GATEWAY_ALLOW_UPGRADE_ONLY = True

# Signer defaults.
HOST_GATEWAY_SIGNER_MODE = "runtime_env_secret"
HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX = "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_"
HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH = True
HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS = 300
HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS = 300

# Host-visible surface registry defaults.
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY = "host_visible_surface_registry_contract_v1"
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID = "host_visible_surface_registry_contract_v1"
HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR = "scripts/validate_host_transport_wiring_attestation.py"
HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE = "scripts/ci/run_host_visible_surface_live_probes_ci.sh"
HOST_TRANSPORT_REACHABILITY_VALIDATOR = "scripts/validate_host_transport_reachability.py"
HOST_TRANSPORT_REACHABILITY_LIVE_PROBE_DELEGATE = (
    "scripts/ci/run_host_transport_reachability_probes_ci.sh"
)
HOST_TRANSPORT_REACHABILITY_TIMEOUT_SECONDS = 3
HOST_TRANSPORT_REACHABILITY_ERROR_CODE = "IP-HTR-001"
HOST_TRANSPORT_REACHABILITY_REASON_PREFIX = "host_transport_reachability_unavailable"
HOST_TRANSPORT_REACHABILITY_URL_FIELD = "transport_healthcheck_url"
HOST_TRANSPORT_REACHABILITY_TIMEOUT_FIELD = "transport_healthcheck_timeout_seconds"
HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS: tuple[str, ...] = (
    "commentary",
    "approval",
    "status",
    "final",
)
HOST_VISIBLE_FINAL_CHANNEL_ID = "final"
HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED = True
HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE = "agent_relay_final_answer"
HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE = "exact"
HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY = "identity_instance_output"
HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_DIR = "runtime/reports/agent-relay-final-answer"
HOST_VISIBLE_FINAL_CHANNEL_RELAY_RECEIPT_PREFIX = "agent-relay-final-answer"
HOST_VISIBLE_SURFACE_STATE_FILE = "runtime/state/host_visible_surface_registry_state.json"
HOST_VISIBLE_SURFACE_RECEIPT_PATTERN = "runtime/reports/host-visible-surface/host-visible-surface-*.json"
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS = 300
HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED = True
HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE = (
    "runtime/state/host_visible_surface_live_closure_state.json"
)
HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE = True
HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION = "v1"
HOST_VISIBLE_POST_CHECK_AUTO_RECOVERY_BLOCK_STAGES: tuple[str, ...] = (
    "pre_first_line_post_check_blocker_active",
    "pre_first_line_post_check_state_unavailable",
)
HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF = "runtime:host_visible_post_check_recovery"
HOST_VISIBLE_POST_CHECK_RECOVERY_ARTIFACT_CHANNEL = "host-visible-post-check-recovery"
HOST_VISIBLE_POST_CHECK_RECOVERY_MATERIALIZATION_REASON = (
    "host_visible_post_check_recovery_materialized"
)
HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_LIVE = "live"
HOST_VISIBLE_SURFACE_RUNTIME_SCOPE_SHADOW = "shadow"
HOST_VISIBLE_CHAT_EGRESS_UNIQUENESS_CONTRACT_ID = "chat_egress_uniqueness_contract_v1"
HOST_VISIBLE_CHAT_EGRESS_UNIQUENESS_REQUIRED_RATE = 1.0
HOST_VISIBLE_POST_GATE_COVERAGE_REQUIRED_RATE = 1.0
HOST_VISIBLE_NEXT_HOP_HEADSTAMP_REQUIRED_RATE = 1.0
# Keep uniqueness telemetry in existing headstamp error-code family to preserve
# control-plane no-rebound budgets while exposing finer reason taxonomy.
CHAT_EGRESS_RAW_BYPASS_ERROR_CODE = "IP-HDSTAMP-003"
CHAT_EGRESS_POST_CHECK_STATE_UNAVAILABLE_ERROR_CODE = "IP-HDSTAMP-003"
HOST_VISIBLE_PRE_SEND_GATE_MIN_PASS_RATE = 0.95
HOST_VISIBLE_POST_CHECK_DETECTABILITY_REQUIRED_RATE = 1.0
HOST_VISIBLE_NEXT_HOP_BLOCK_REQUIRED_RATE = 1.0
HOST_VISIBLE_FALSE_GREEN_MAX_RATE = 0.0
PRIVILEGE_ESCALATION_ERROR_CODE = "IP-PRIV-ESC-001"
PRIVILEGE_ESCALATION_REASON_PREFIX = "privilege_escalation_required"
PRIVILEGE_ESCALATION_REMEDIATION_HINT = "rerun_with_host_privilege_escalation"
CTX_TOOL_TIMEOUT_ERROR_CODE = "IP-CTX-TOOL-001"
CTX_TOOL_TIMEOUT_MARKER = "CTX_TOOL_TIMEOUT"
CTX_TOOL_TIMEOUT_REASON_PREFIX = "context_tool_timeout"
GATEWAY_WRAPPER_SUBPROCESS_TIMEOUT_SECONDS_DEFAULT = 30
GATEWAY_CONTEXT_RESOLVE_TIMEOUT_SECONDS_DEFAULT = 5
GATEWAY_WRAPPER_TIMEOUT_PROFILE_SECONDS: tuple[tuple[str, int], ...] = (
    ("scripts/identity_creator.py", 240),
    ("scripts/repair_contract_backfill.py", 120),
    ("scripts/required_gate_bundle_runner.py", 120),
    ("scripts/report_three_plane_status.py", 180),
    # Protocol lane audit summary delegates materialize isolated replay workspaces
    # and replay commit-pinned control-plane summaries; keep them on an explicit
    # long-running profile so wrapper-only release gates do not false-red at the
    # default passthrough timeout.
    ("scripts/validate_protocol_lane_isolated_historical_replay.py", 300),
    ("scripts/ci/run_protocol_root_corpus_governance_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_root_corpus_ordering_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_root_corpus_authority_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_root_corpus_derivation_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_root_corpus_transition_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh", 300),
    ("scripts/ci/run_protocol_lane_audit_summary_probes_ci.sh", 600),
    # Workbook control-plane probes materialize shadow repos, rerender governed
    # projection outputs, and replay multiple negative-path registry checks.
    # The direct probe runtime is substantially above the default passthrough
    # timeout, so release-readiness must route it through an explicit long-run
    # profile instead of timing out at the wrapper boundary.
    ("scripts/ci/run_workbook_control_plane_probes_ci.sh", 300),
    ("scripts/validate_control_plane_status_sync.py", 180),
    ("scripts/validate_required_contract_coverage.py", 180),
)
VALIDATOR_ACTOR_ID_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_required_contract_coverage.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_identity_response_stamp.py",
    CANONICAL_FINAL_EMIT_SCRIPT,
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_send_time_reply_gate.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/validate_protocol_unique_entry_gate.py",
)
VALIDATOR_SESSION_ID_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_required_contract_coverage.py",
    "scripts/render_identity_response_stamp.py",
    "scripts/validate_identity_response_stamp.py",
    CANONICAL_FINAL_EMIT_SCRIPT,
    "scripts/validate_headstamp_recurrence_closure.py",
    "scripts/validate_reply_identity_context_first_line.py",
    "scripts/validate_send_time_reply_gate.py",
    "scripts/validate_execution_reply_identity_coherence.py",
    "scripts/validate_protocol_unique_entry_gate.py",
)
VALIDATOR_RUN_ID_REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_protocol_unique_entry_gate.py",
)


def resolve_host_gateway_gate_profile(operation: str) -> str:
    op = str(operation or "").strip().lower()
    strict_profile_by_operation = {
        str(key).strip().lower(): str(value).strip()
        for key, value in HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION.items()
        if str(key).strip() and str(value).strip()
    }
    if op in {str(item).strip().lower() for item in HOST_GATEWAY_STRICT_OPERATIONS}:
        return strict_profile_by_operation.get(op, HOST_GATEWAY_STRICT_GATE_PROFILE)
    if op in {str(item).strip().lower() for item in HOST_GATEWAY_LIGHT_OPERATIONS}:
        return HOST_GATEWAY_LIGHT_GATE_PROFILE
    return HOST_GATEWAY_STRICT_GATE_PROFILE


def build_required_gate_bundle_cmd(
    *,
    catalog: str,
    identity_id: str,
    run_id: str,
    send_time_gate_status: str,
    outlet_bypass_detected: str,
    final_emit_contract_status: str,
    final_emit_policy_mode: str,
    final_emit_schema_status: str,
    actor_id: str,
    session_id: str = "",
    resolved_work_layer: str,
    resolved_source_layer: str,
    lock_state: str,
    operation: str,
    surface_label: str = "",
    target_name: str = "",
    report_selected_path: str = "",
    out_path: str = "",
) -> list[str]:
    cmd = [
        "python3",
        CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
        "--catalog",
        catalog,
        "--identity-id",
        identity_id,
        "--run-id",
        run_id,
        "--send-time-gate-status",
        send_time_gate_status,
        "--outlet-bypass-detected",
        outlet_bypass_detected,
        "--final-emit-contract-status",
        final_emit_contract_status,
        "--final-emit-policy-mode",
        final_emit_policy_mode,
        "--final-emit-schema-status",
        final_emit_schema_status,
        "--actor-id",
        actor_id,
    ]
    if str(session_id or "").strip():
        cmd.extend(["--session-id", str(session_id).strip()])
    cmd.extend([
        "--resolved-work-layer",
        resolved_work_layer,
        "--resolved-source-layer",
        resolved_source_layer,
        "--lock-state",
        lock_state,
        "--surface-label",
        str(surface_label or HOST_GATEWAY_REQUIRED_SURFACE_LABEL).strip(),
        "--operation",
        operation,
    ])
    gate_profile = resolve_host_gateway_gate_profile(operation)
    if gate_profile:
        cmd.extend(["--gate-profile", gate_profile])
    if target_name:
        cmd.extend(["--target-name", target_name])
    if report_selected_path:
        cmd.extend(["--report-selected-path", report_selected_path])
    if out_path:
        cmd.extend(["--out", out_path])
    cmd.append("--json-only")
    return cmd


def validator_requires_actor_id(script_path: str) -> bool:
    return str(script_path or "").strip() in VALIDATOR_ACTOR_ID_REQUIRED_SCRIPTS


def validator_requires_session_id(script_path: str) -> bool:
    return str(script_path or "").strip() in VALIDATOR_SESSION_ID_REQUIRED_SCRIPTS


def validator_requires_run_id(script_path: str) -> bool:
    return str(script_path or "").strip() in VALIDATOR_RUN_ID_REQUIRED_SCRIPTS


HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS: tuple[str, ...] = (
    "emit_channel_id",
    "wrapper_surface_status",
    "entry_receipt_tuple_status",
    "headstamp_first_line_status",
    "send_time_gate_status",
    "final_emit_contract_status",
)
HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS: tuple[str, ...] = (
    "wrapper_surface_status",
    "entry_receipt_tuple_status",
    "headstamp_first_line_status",
    "send_time_gate_status",
    "final_emit_contract_status",
)
HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS: tuple[str, ...] = (
    "agent_relay_final_answer_receipt_path",
    "agent_relay_final_answer_status",
    "agent_relay_final_answer_relay_mode",
    "agent_relay_final_answer_delivery_authority",
    "agent_relay_final_answer_source_artifact",
    "agent_relay_final_answer_question_tag",
)
HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS: tuple[str, ...] = (
    "agent_relay_final_answer_status",
)
HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD = "receipt_source"
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE = "runtime_dialogue"
HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE = "ci_fixture"
HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES: tuple[str, ...] = (
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
)
HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS: tuple[str, ...] = ("ci",)

# Unique-entry receipt selector contract (deterministic candidate choice).
UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID = "entry_receipt_selector_tuple_source_status_newest_v1"
UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE: tuple[str, ...] = (
    "same_tuple",
    "same_catalog",
    "bundle_status_pass",
    "newest",
)
UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS: tuple[str, ...] = ("catalog_path",)

# Multimodal runtime stage null-proof receipts.
MULTIMODAL_RUNTIME_STAGE_RECEIPT_DIR = "runtime/reports/multimodal-runtime-stage"
MULTIMODAL_RUNTIME_STAGE_RECEIPT_PREFIX = "multimodal-runtime-stage"
MULTIMODAL_RUNTIME_STAGE_RECEIPT_SOURCE = "execute_identity_upgrade_null_proof"

# Wrapper semantic attestations.
HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY = "wrapper_template_attestation_policy"
HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID = "host_gateway_wrapper_template_attestation_v1"
HOST_GATEWAY_SESSION_CHAIN_EXECUTABLE_SMOKE_ID = "host_gateway_session_chain_final_branch_smoke_v1"
HOST_GATEWAY_SESSION_CHAIN_EXECUTABLE_SMOKE_REQUIRED_CHANNELS: tuple[str, ...] = (
    HOST_VISIBLE_FINAL_CHANNEL_ID,
)
HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS: tuple[str, ...] = (
    "headstamp_first_line_status",
    "entry_receipt_tuple_status",
    "final_emit_contract_status",
    "Identity-Context:",
    f'HOST_VISIBLE_FINAL_CHANNEL_ID = "{HOST_VISIBLE_FINAL_CHANNEL_ID}"',
    f"HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED = {HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED}",
    "def _repo_root() -> Path:",
    "def _pack_root_from_contract_path(contract_path: Path) -> Path:",
    "def _normalize_text(",
    "def _sanitize_token(",
    "def identity_runtime_named_temp_root(name: str) -> Path:",
    "build_host_visible_final_channel_question_tag(",
    "build_host_visible_final_channel_receipt_path(",
    "build_host_visible_final_channel_relay_receipt(",
    "project_host_visible_final_channel_relay_fields(",
)

# Broadcast governance paths.
HOST_GATEWAY_BROADCAST_ITEMS_DIR = "identity/protocol/broadcast/items"
HOST_GATEWAY_BROADCAST_INDEX_FILE = "identity/protocol/broadcast/index.json"
HOST_GATEWAY_BROADCAST_SCHEMA_FILE = "identity/protocol/broadcast/schema/broadcast-item.v1.json"
HOST_GATEWAY_BROADCAST_STATE_FILE = "runtime/state/broadcast_state.json"
HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN = "runtime/reports/broadcast/broadcast-receipt-*.json"
HOST_GATEWAY_BROADCAST_ACK_PATTERN = "runtime/reports/broadcast/broadcast-ack-*.json"
