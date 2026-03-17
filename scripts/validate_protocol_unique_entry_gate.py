#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from create_identity_pack import _host_gateway_wrapper_template_attestation_policy
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task
from protocol_infra_contract import (
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
    HOST_GATEWAY_BROADCAST_INDEX_FILE as INFRA_HOST_GATEWAY_BROADCAST_INDEX_FILE,
    HOST_GATEWAY_BROADCAST_ITEMS_DIR as INFRA_HOST_GATEWAY_BROADCAST_ITEMS_DIR,
    HOST_GATEWAY_BROADCAST_SCHEMA_FILE as INFRA_HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    HOST_GATEWAY_CONTRACT_KEYS as INFRA_HOST_GATEWAY_CONTRACT_KEYS,
    HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER as INFRA_HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER as INFRA_HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER,
    HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT as INFRA_HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT,
    HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER as INFRA_HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE as INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_DISPATCH_STATUS as INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_STATUS,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE as INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_GATEWAY_REQUIRED_SURFACE_LABEL as INFRA_HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
    HOST_GATEWAY_REQUIRED_SURFACE_STATUS as INFRA_HOST_GATEWAY_REQUIRED_SURFACE_STATUS,
    HOST_GATEWAY_REQUIRED_TUPLE_FIELDS as INFRA_HOST_GATEWAY_REQUIRED_TUPLE_FIELDS,
    HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS as INFRA_HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS,
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY as INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN as INFRA_HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED as INFRA_HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES,
    HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS as INFRA_HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS,
    HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE as INFRA_HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
    HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_STATE_FILE as INFRA_HOST_VISIBLE_SURFACE_STATE_FILE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-GATE-ENTRY-001"
ERR_CONTRACT_INVALID = "IP-GATE-ENTRY-002"

STRICT_OPERATIONS = {
    "activate",
    "update",
    "mutation",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
}

EXPECTED_ENTRY_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
EXPECTED_EGRESS_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
EXPECTED_HOST_DISPATCH_MODE = INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE
EXPECTED_HOST_RELEASE_MODE = INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE
DEFAULT_ENTRY_RECEIPT_SURFACE_LABEL = INFRA_HOST_GATEWAY_REQUIRED_SURFACE_LABEL
DEFAULT_ENTRY_RECEIPT_WRAPPER_SURFACE_STATUS = INFRA_HOST_GATEWAY_REQUIRED_SURFACE_STATUS
DEFAULT_ENTRY_RECEIPT_WRAPPER_DISPATCH_STATUS = INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_STATUS
EXPECTED_BUNDLE_KEY = "required_gate_bundle_runner"
EXPECTED_SCOPE = "all_identity_instance_actions"
EXPECTED_ENTRY_ERROR_FAMILY = {"IP-GATE-ENTRY-001", "IP-GATE-ENTRY-002"}
ENTRY_RECEIPT_STATE_FILE = "required_gate_bundle_entry.latest.json"
ENTRY_RECEIPT_HISTORY_GLOB = "required-gate-bundle-entry-*.json"
HOST_GATEWAY_REQUIRED_TUPLE_FIELDS = set(INFRA_HOST_GATEWAY_REQUIRED_TUPLE_FIELDS)
HOST_GATEWAY_EXPECTED_INGRESS_REL = INFRA_HOST_GATEWAY_DEFAULT_INGRESS_WRAPPER
HOST_GATEWAY_EXPECTED_EGRESS_REL = INFRA_HOST_GATEWAY_DEFAULT_EGRESS_WRAPPER
HOST_GATEWAY_EXPECTED_SESSION_CHAIN_REL = INFRA_HOST_GATEWAY_DEFAULT_SESSION_CHAIN_WRAPPER
HOST_GATEWAY_EXPECTED_CONTRACT_REL = INFRA_HOST_GATEWAY_DEFAULT_RUNTIME_CONTRACT
HOST_GATEWAY_BROADCAST_ITEMS_DIR = INFRA_HOST_GATEWAY_BROADCAST_ITEMS_DIR
HOST_GATEWAY_BROADCAST_INDEX_FILE = INFRA_HOST_GATEWAY_BROADCAST_INDEX_FILE
HOST_GATEWAY_BROADCAST_SCHEMA_FILE = INFRA_HOST_GATEWAY_BROADCAST_SCHEMA_FILE
HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY = INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY
HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS = set(INFRA_HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS)
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS = set(INFRA_HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS)
HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS = set(INFRA_HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS)
HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS = set(INFRA_HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS)
HOST_VISIBLE_SURFACE_STATE_FILE = INFRA_HOST_VISIBLE_SURFACE_STATE_FILE
HOST_VISIBLE_SURFACE_RECEIPT_PATTERN = INFRA_HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED = INFRA_HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE = INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS = INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS
HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES = set(
    INFRA_HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES
)
HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS = set(
    INFRA_HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS
)
HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE = INFRA_HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE
ENTRY_RECEIPT_SELECTOR_POLICY_ID = INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID
ENTRY_RECEIPT_SELECTOR_PRECEDENCE = list(INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE)
ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS = list(INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS)
HOST_GATEWAY_ALLOWED_FIELDS = {
    "contract_id",
    "required",
    "validator",
    "protocol_ingress_script",
    "protocol_egress_script",
    "ingress_wrapper_path",
    "egress_wrapper_path",
    "session_chain_wrapper_path",
    "gateway_contract_path",
    "host_dispatch_mode",
    "host_release_mode",
    "ingress_wrapper_dispatch_token",
    "identity_tuple_fields",
    "operation_profile_policy",
    "entry_receipt_policy",
    "ingress_proof_policy",
    "egress_receipt_policy",
    "egress_grant_policy",
    "headstamp_policy",
    "broadcast_policy",
    "host_visible_surface_registry_contract_ref",
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
}
HOST_GATEWAY_OPERATION_PROFILE_ALLOWED_FIELDS = {
    "strict_operations",
    "light_operations",
    "strict_gate_profile",
    "light_gate_profile",
    "allow_upgrade_only",
}
HOST_GATEWAY_ENTRY_POLICY_ALLOWED_FIELDS = {
    "required",
    "required_surface_label",
    "required_wrapper_surface_status",
    "required_wrapper_dispatch_token_status",
}
HOST_GATEWAY_INGRESS_PROOF_POLICY_ALLOWED_FIELDS = {
    "required",
    "max_age_seconds",
    "signer_mode",
    "signer_secret_env",
    "signing_key_path",
    "bootstrap_env_secret_from_signing_key_path",
}
HOST_GATEWAY_EGRESS_POLICY_ALLOWED_FIELDS = {"required"}
HOST_GATEWAY_EGRESS_GRANT_POLICY_ALLOWED_FIELDS = {
    "required",
    "max_age_seconds",
    "signer_mode",
    "signer_secret_env",
    "signing_key_path",
    "bootstrap_env_secret_from_signing_key_path",
}
HOST_GATEWAY_HEADSTAMP_POLICY_ALLOWED_FIELDS = {"required"}
HOST_GATEWAY_BROADCAST_POLICY_ALLOWED_FIELDS = {
    "required",
    "protocol_broadcast_items_dir",
    "protocol_broadcast_index_file",
    "protocol_broadcast_schema_file",
    "instance_state_file",
    "instance_receipt_pattern",
    "instance_ack_pattern",
    "block_on_critical_unacked",
}
HOST_GATEWAY_TEMPLATE_ATTESTATION_ALLOWED_FIELDS = {
    "required",
    "attestation_id",
    "ingress_wrapper_template_sha256",
    "egress_wrapper_template_sha256",
    "session_chain_wrapper_template_sha256",
    "session_chain_required_semantic_tokens",
    "required_tuple_fields",
}
HOST_VISIBLE_SURFACE_ALLOWED_FIELDS = {
    "required",
    "contract_id",
    "validator",
    "required_channels",
    "runtime_state_file",
    "runtime_receipt_pattern",
    "runtime_receipt_max_age_seconds",
    "strict_live_run_binding_required",
    "required_attestation_fields",
    "required_pass_status_fields",
    "required_live_probe_delegate",
    "host_dispatch_mode_required",
    "host_release_mode_required",
    "post_check_closure_state_file",
    "post_check_block_on_active",
    "runtime_live_receipt_sources",
    "fixture_receipt_source",
    "fixture_allowed_operations",
}
RUNTIME_GATEWAY_ALLOWED_FIELDS = {
    "schema_version",
    "identity_id",
    "protocol_repo_root",
    "protocol_ingress_script",
    "protocol_egress_script",
    "ingress_wrapper_path",
    "egress_wrapper_path",
    "session_chain_wrapper_path",
    "catalog_path",
    "entry_receipt_policy",
    "ingress_proof_policy",
    "egress_receipt_policy",
    "egress_grant_policy",
    "headstamp_policy",
    "identity_tuple_fields",
    "host_dispatch_mode",
    "host_release_mode",
    "ingress_wrapper_dispatch_token",
    "operation_profile_policy",
    "host_visible_surface_registry_contract_ref",
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
    "broadcast_policy",
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    "protocol_downsink_path_immutability_contract_v1",
}

CONTRACT_KEYS = (
    "protocol_unique_entry_gate_contract_v1",
    "protocol_unique_entry_gate_contract",
    "rq_036_protocol_unique_entry_gate_contract_v1",
)

HOST_GATEWAY_CONTRACT_KEYS = INFRA_HOST_GATEWAY_CONTRACT_KEYS

ENTRY_RECEIPT_RUN_ID_FIELDS: tuple[str, ...] = (
    "run_id_binding",
    "run_id",
    "requested_run_id",
)
ENTRY_RECEIPT_ACTOR_ID_FIELDS: tuple[str, ...] = (
    "actor_id",
    "resolved_actor_id",
    "entry_actor_id",
)
ENTRY_RECEIPT_SESSION_ID_FIELDS: tuple[str, ...] = (
    "session_id",
    "resolved_session_id",
    "entry_session_id",
)
ENTRY_RECEIPT_OPERATION_FIELDS: tuple[str, ...] = (
    "operation",
    "requested_operation",
    "operation_name",
)
ENTRY_RECEIPT_PAYLOAD_EPOCH_FIELDS: tuple[str, ...] = (
    "wrapper_dispatch_proof_issued_at_epoch",
    "issued_at_epoch",
    "created_at_epoch",
)
ENTRY_RECEIPT_PAYLOAD_ISO_FIELDS: tuple[str, ...] = (
    "created_at_utc",
    "created_at",
    "issued_at_utc",
    "issued_at",
)
ENTRY_RECEIPT_OPERATION_BRIDGES: dict[str, set[str]] = {
    "validate": {"inspection"},
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw, key
    for key, raw in task.items():
        if not isinstance(raw, dict):
            continue
        token = str(key or "").strip().lower()
        if "unique_entry" in token and "contract" in token:
            return raw, str(key)
    return {}, CONTRACT_KEYS[0]


def _resolve_host_gateway_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in HOST_GATEWAY_CONTRACT_KEYS:
        raw = task.get(key)
        if isinstance(raw, dict):
            return raw, key
    for key, raw in task.items():
        if not isinstance(raw, dict):
            continue
        token = str(key or "").strip().lower()
        if "gateway" in token and "contract" in token:
            return raw, str(key)
    return {}, HOST_GATEWAY_CONTRACT_KEYS[0]


def _as_str_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item).strip() for item in value if str(item).strip()}


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    token = str(value or "").strip().lower()
    return token in {"1", "true", "yes", "y", "on"}


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _unknown_keys(node: Any, allowed: set[str]) -> list[str]:
    if not isinstance(node, dict):
        return []
    return sorted(str(k) for k in node.keys() if str(k) not in allowed)


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_canonical_wrapper_template_attestation_policy() -> tuple[dict[str, Any], str]:
    try:
        policy = _host_gateway_wrapper_template_attestation_policy()
    except Exception as exc:
        return {}, f"canonical_wrapper_template_policy_load_failed:{type(exc).__name__}:{exc}"
    if not isinstance(policy, dict):
        return {}, "canonical_wrapper_template_policy_invalid_type"
    return policy, ""


def _validate_signer_policy(node: Any, *, issue_prefix: str, issues: list[str]) -> str:
    if not isinstance(node, dict):
        issues.append(f"{issue_prefix}_missing")
        return ""
    signer_mode = str(node.get("signer_mode", "")).strip().lower()
    signer_secret_env = str(node.get("signer_secret_env", "")).strip()
    signing_key_path = str(node.get("signing_key_path", "")).strip()
    bootstrap_from_key = node.get("bootstrap_env_secret_from_signing_key_path")
    if signer_mode == "runtime_env_secret":
        if not signer_secret_env:
            issues.append(f"{issue_prefix}_signer_secret_env_missing")
        if not signing_key_path:
            issues.append(f"{issue_prefix}_signing_key_path_missing_in_env_mode")
        if not isinstance(bootstrap_from_key, bool):
            issues.append(f"{issue_prefix}_bootstrap_env_secret_from_signing_key_path_invalid")
        return signer_mode
    if signer_mode in {"runtime_file_secret", ""}:
        if not signing_key_path:
            issues.append(f"{issue_prefix}_signing_key_path_missing")
        return signer_mode or "runtime_file_secret"
    issues.append(f"{issue_prefix}_signer_mode_unsupported")
    return signer_mode


def _operation_requires_provenance(
    *,
    operation: str,
    dispatch_mode: str,
    strict_operations: set[str],
    light_operations: set[str],
    allow_upgrade_only: bool,
) -> bool:
    if str(dispatch_mode or "").strip().lower() != EXPECTED_HOST_DISPATCH_MODE:
        return False
    op = str(operation or "").strip().lower()
    if op in strict_operations or op in light_operations:
        return True
    if op and allow_upgrade_only:
        return True
    if not op:
        return True
    return False


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


def _collect_entry_receipt_candidates(
    *,
    pack_path: Path,
    explicit_path: str,
    operation: str,
) -> list[tuple[Path, str]]:
    candidates: list[tuple[Path, str]] = []
    if str(explicit_path or "").strip():
        p = Path(explicit_path).expanduser().resolve()
        if p.exists() and p.is_file():
            candidates.append((p, "explicit"))
        return candidates

    operation_token = str(operation or "").strip().lower()
    if operation_token:
        by_operation = (
            pack_path / "runtime" / "state" / f"required_gate_bundle_entry.{operation_token}.json"
        ).resolve()
        if by_operation.exists() and by_operation.is_file():
            candidates.append((by_operation, "operation_state"))

    latest = (pack_path / "runtime" / "state" / ENTRY_RECEIPT_STATE_FILE).resolve()
    if latest.exists() and latest.is_file():
        candidates.append((latest, "latest_state"))

    history_dir = (pack_path / "runtime" / "reports" / "required-gate-bundle-entry").resolve()
    if history_dir.exists() and history_dir.is_dir():
        history_candidates = sorted(
            history_dir.glob(ENTRY_RECEIPT_HISTORY_GLOB),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )
        for item in history_candidates:
            candidates.append((item.resolve(), "history"))

    seen: set[Path] = set()
    deduped: list[tuple[Path, str]] = []
    for path, source in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append((resolved, source))
    return deduped


def _first_receipt_value(
    receipt: dict[str, Any], fields: tuple[str, ...], *, lower: bool = False
) -> tuple[str, str]:
    for field in fields:
        value = str(receipt.get(field, "")).strip()
        if value:
            return (value.lower(), field) if lower else (value, field)
    return "", ""


def _safe_file_mtime_epoch(path: Path) -> int:
    try:
        return int(path.stat().st_mtime)
    except Exception:
        return 0


def _operation_bridge_match(expected_operation: str, receipt_operation: str) -> bool:
    expected = str(expected_operation or "").strip().lower()
    observed = str(receipt_operation or "").strip().lower()
    if not expected or not observed:
        return False
    return observed in ENTRY_RECEIPT_OPERATION_BRIDGES.get(expected, set())


def _evaluate_entry_receipt_candidate(
    *,
    receipt: dict[str, Any],
    candidate_path: Path,
    candidate_source: str,
    expected_operation: str,
    expected_run_id: str,
    expected_actor_id: str,
    expected_session_id: str,
    expected_catalog_path: str,
) -> dict[str, Any]:
    receipt_operation, _ = _first_receipt_value(receipt, ENTRY_RECEIPT_OPERATION_FIELDS, lower=True)
    receipt_run_id, _ = _first_receipt_value(receipt, ENTRY_RECEIPT_RUN_ID_FIELDS)
    receipt_actor_id, _ = _first_receipt_value(receipt, ENTRY_RECEIPT_ACTOR_ID_FIELDS)
    receipt_session_id, _ = _first_receipt_value(receipt, ENTRY_RECEIPT_SESSION_ID_FIELDS)
    receipt_bundle_status = str(receipt.get("bundle_status", "")).strip().upper()
    receipt_catalog_path = str(receipt.get("catalog_path", "")).strip()
    operation_exact_match = bool(receipt_operation and receipt_operation == expected_operation)
    operation_bridge_match = _operation_bridge_match(expected_operation, receipt_operation)
    operation_match = bool(operation_exact_match or operation_bridge_match)
    run_match = bool(expected_run_id and receipt_run_id == expected_run_id)
    actor_match = bool(expected_actor_id and receipt_actor_id == expected_actor_id)
    session_match = bool(expected_session_id and receipt_session_id == expected_session_id)
    tuple_expected_count = 1 + sum(1 for token in (expected_run_id, expected_actor_id, expected_session_id) if token)
    tuple_match_count = int(operation_match) + int(run_match) + int(actor_match) + int(session_match)
    same_tuple = tuple_match_count == tuple_expected_count
    same_catalog = bool(expected_catalog_path and receipt_catalog_path and receipt_catalog_path == expected_catalog_path)
    bundle_status_pass = receipt_bundle_status == STATUS_PASS_REQUIRED
    payload_epoch, payload_field = _extract_receipt_payload_timestamp_epoch(receipt)
    effective_epoch = payload_epoch or _safe_file_mtime_epoch(candidate_path)
    origin_rank = {
        "explicit": 3,
        "operation_state": 2,
        "latest_state": 1,
        "history": 0,
    }.get(str(candidate_source or "").strip(), 0)
    return {
        "path": str(candidate_path),
        "source": str(candidate_source),
        "operation": receipt_operation,
        "run_id": receipt_run_id,
        "actor_id": receipt_actor_id,
        "session_id": receipt_session_id,
        "catalog_path": receipt_catalog_path,
        "bundle_status": receipt_bundle_status,
        "operation_exact_match": operation_exact_match,
        "operation_bridge_match": operation_bridge_match,
        "tuple_match_count": tuple_match_count,
        "tuple_expected_count": tuple_expected_count,
        "same_tuple": same_tuple,
        "same_catalog": same_catalog,
        "bundle_status_pass": bundle_status_pass,
        "effective_epoch": int(effective_epoch),
        "effective_epoch_source": payload_field or "file_mtime",
        "sort_key": (
            int(same_tuple),
            int(operation_exact_match),
            int(tuple_match_count),
            int(same_catalog),
            int(bundle_status_pass),
            int(effective_epoch),
            int(origin_rank),
        ),
    }


def _select_entry_receipt_candidate(
    *,
    candidates: list[tuple[Path, str]],
    expected_operation: str,
    expected_run_id: str,
    expected_actor_id: str,
    expected_session_id: str,
    expected_catalog_path: str,
) -> tuple[Path | None, dict[str, Any], list[str]]:
    payload: dict[str, Any] = {
        "selector_policy_id": ENTRY_RECEIPT_SELECTOR_POLICY_ID,
        "selector_precedence": list(ENTRY_RECEIPT_SELECTOR_PRECEDENCE),
        "selector_source_fields": list(ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS),
        "candidate_count": 0,
        "selected_path": "",
        "selected_source": "",
        "selected_sort_key": [],
        "selected_reason_tokens": [],
        "candidate_preview": [],
    }
    issues: list[str] = []
    scored: list[dict[str, Any]] = []
    for candidate_path, source in candidates:
        try:
            receipt = _load_receipt(candidate_path)
        except Exception as exc:
            issues.append(f"entry_receipt_candidate_invalid:{candidate_path.name}:{type(exc).__name__}")
            continue
        scored.append(
            _evaluate_entry_receipt_candidate(
                receipt=receipt,
                candidate_path=candidate_path,
                candidate_source=source,
                expected_operation=expected_operation,
                expected_run_id=expected_run_id,
                expected_actor_id=expected_actor_id,
                expected_session_id=expected_session_id,
                expected_catalog_path=expected_catalog_path,
            )
        )
    payload["candidate_count"] = len(scored)
    payload["candidate_preview"] = [
        {
            "path": row["path"],
            "source": row["source"],
            "operation": row["operation"],
            "run_id": row["run_id"],
            "actor_id": row["actor_id"],
            "session_id": row["session_id"],
            "catalog_path": row["catalog_path"],
            "bundle_status": row["bundle_status"],
            "operation_exact_match": row["operation_exact_match"],
            "operation_bridge_match": row["operation_bridge_match"],
            "same_tuple": row["same_tuple"],
            "same_catalog": row["same_catalog"],
            "bundle_status_pass": row["bundle_status_pass"],
        }
        for row in scored[:8]
    ]
    if not scored:
        return None, payload, issues
    ranked = sorted(scored, key=lambda row: row.get("sort_key", ()), reverse=True)
    selected = ranked[0]
    payload["selected_path"] = str(selected.get("path", ""))
    payload["selected_source"] = str(selected.get("source", ""))
    payload["selected_sort_key"] = list(selected.get("sort_key", ()))
    reasons: list[str] = []
    if selected.get("same_tuple"):
        reasons.append("same_tuple")
    if selected.get("operation_bridge_match"):
        reasons.append("operation_bridge_match")
    if selected.get("same_catalog"):
        reasons.append("same_catalog")
    if selected.get("bundle_status_pass"):
        reasons.append("bundle_status_pass")
    reasons.append("newest")
    payload["selected_reason_tokens"] = reasons
    return Path(str(selected.get("path", "")).strip()).resolve(), payload, issues


def _load_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("receipt_payload_not_object")
    return data


def _parse_iso_timestamp_to_epoch(value: Any) -> int:
    token = str(value or "").strip()
    if not token:
        return 0
    normalized = token
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(normalized)
    except Exception:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return int(dt.timestamp())
    except Exception:
        return 0


def _extract_receipt_payload_timestamp_epoch(receipt: dict[str, Any]) -> tuple[int, str]:
    for field in ENTRY_RECEIPT_PAYLOAD_EPOCH_FIELDS:
        value = _safe_int(receipt.get(field), default=0)
        if value > 0:
            return value, field
    for field in ENTRY_RECEIPT_PAYLOAD_ISO_FIELDS:
        value = _parse_iso_timestamp_to_epoch(receipt.get(field))
        if value > 0:
            return value, field
    return 0, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol unique-entry gate contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=[
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
        ],
        default="validate",
    )
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--force-required", action="store_true")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--entry-receipt", default="")
    ap.add_argument("--require-entry-receipt", action="store_true")
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
        return 2

    contract, contract_key = _resolve_contract(task)
    declared_required = contract_required(contract)
    strict_operation = str(args.operation).strip().lower() in STRICT_OPERATIONS
    required = bool(args.force_check or args.force_required or declared_required or strict_operation)
    run_id = str(args.run_id or "").strip()
    actor_id = str(args.actor_id or "").strip()
    session_id = str(args.session_id or "").strip()

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "required_contract": required,
        "declared_required_contract": declared_required,
        "strict_operation": strict_operation,
        "contract_key_used": contract_key,
        "protocol_unique_entry_gate_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_script": "",
        "protocol_unique_entry_bundle_key": "",
        "protocol_unique_entry_scope": "",
        "protocol_unique_entry_required_operations": [],
        "protocol_unique_entry_error_family": [],
        "protocol_unique_entry_receipt_required": False,
        "protocol_unique_entry_receipt_required_by_cli_flag": False,
        "protocol_unique_entry_receipt_required_by_contract": False,
        "protocol_unique_entry_receipt_required_by_strict_default": False,
        "protocol_unique_entry_receipt_required_strict_operation": False,
        "protocol_unique_entry_receipt_required_reason": "not_required",
        "protocol_unique_entry_receipt_required_operation": str(args.operation).strip().lower(),
        "protocol_unique_entry_receipt_state_file": "",
        "protocol_unique_entry_receipt_history_pattern": "",
        "protocol_unique_entry_receipt_required_fields": [],
        "protocol_unique_entry_receipt_max_age_seconds": 0,
        "protocol_unique_entry_receipt_age_seconds": -1,
        "protocol_unique_entry_receipt_payload_age_seconds": -1,
        "protocol_unique_entry_receipt_file_age_seconds": -1,
        "protocol_unique_entry_receipt_age_source": "",
        "protocol_unique_entry_receipt_payload_timestamp_epoch": 0,
        "protocol_unique_entry_receipt_payload_timestamp_field": "",
        "protocol_unique_entry_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_receipt_selector_policy_id": "",
        "protocol_unique_entry_receipt_selector_precedence": [],
        "protocol_unique_entry_receipt_selector_source_fields": [],
        "protocol_unique_entry_receipt_selector_candidate_count": 0,
        "protocol_unique_entry_receipt_selector_selected_source": "",
        "protocol_unique_entry_receipt_selector_selected_sort_key": [],
        "protocol_unique_entry_receipt_selector_selected_reason_tokens": [],
        "protocol_unique_entry_receipt_selector_candidate_preview": [],
        "protocol_unique_entry_receipt_path": "",
        "protocol_unique_entry_receipt_bundle_key": "",
        "protocol_unique_entry_receipt_run_id": "",
        "protocol_unique_entry_receipt_run_id_field": "",
        "protocol_unique_entry_receipt_actor_id": "",
        "protocol_unique_entry_receipt_actor_id_field": "",
        "protocol_unique_entry_receipt_session_id": "",
        "protocol_unique_entry_receipt_session_id_field": "",
        "protocol_unique_entry_receipt_operation": "",
        "protocol_unique_entry_receipt_operation_field": "",
        "protocol_unique_entry_receipt_operation_bridge_allowed": False,
        "protocol_unique_entry_receipt_operation_bridge_applied": False,
        "protocol_unique_entry_receipt_tuple_context_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_receipt_tuple_context_required_fields": [],
        "protocol_unique_entry_receipt_tuple_context_mismatch_fields": [],
        "protocol_unique_entry_receipt_tuple_context_expected": {},
        "protocol_unique_entry_receipt_tuple_context_observed": {},
        "protocol_unique_entry_receipt_tuple_context_only_failure": False,
        "protocol_unique_entry_receipt_tuple_context_next_action": "",
        "protocol_unique_entry_receipt_tuple_binding_required": False,
        "protocol_unique_entry_receipt_tuple_binding_expected_fields": [],
        "protocol_unique_entry_receipt_tuple_binding_missing_fields": [],
        "protocol_unique_entry_receipt_surface_label": "",
        "protocol_unique_entry_receipt_wrapper_surface_status": "",
        "protocol_unique_entry_receipt_wrapper_dispatch_token_status": "",
        "protocol_unique_entry_receipt_wrapper_dispatch_required": False,
        "protocol_unique_entry_receipt_wrapper_proof_status": "",
        "protocol_unique_entry_receipt_wrapper_proof_required": False,
        "protocol_unique_entry_receipt_provenance_required": False,
        "protocol_host_gateway_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_contract_key": "",
        "protocol_host_gateway_ingress_script": "",
        "protocol_host_gateway_egress_script": "",
        "protocol_host_gateway_dispatch_mode": "",
        "protocol_host_gateway_release_mode": "",
        "protocol_host_gateway_ingress_dispatch_token": "",
        "protocol_host_gateway_ingress_wrapper_path": "",
        "protocol_host_gateway_egress_wrapper_path": "",
        "protocol_host_gateway_session_chain_wrapper_path": "",
        "protocol_host_gateway_contract_path": "",
        "protocol_host_gateway_runtime_files_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_runtime_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_identity_tuple_fields": [],
        "protocol_host_gateway_entry_receipt_required_surface_label": "",
        "protocol_host_gateway_entry_receipt_required_wrapper_surface_status": "",
        "protocol_host_gateway_entry_receipt_required_wrapper_dispatch_token_status": "",
        "protocol_host_gateway_strict_operations": [],
        "protocol_host_gateway_light_operations": [],
        "protocol_host_gateway_strict_gate_profile": "",
        "protocol_host_gateway_light_gate_profile": "",
        "protocol_host_gateway_allow_upgrade_only": True,
        "protocol_host_gateway_wrapper_template_attestation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_wrapper_template_attestation_id": "",
        "protocol_host_gateway_wrapper_template_ingress_sha256": "",
        "protocol_host_gateway_wrapper_template_egress_sha256": "",
        "protocol_host_gateway_wrapper_template_session_chain_sha256": "",
        "protocol_host_gateway_wrapper_template_canonical_attestation_id": "",
        "protocol_host_gateway_wrapper_template_canonical_ingress_sha256": "",
        "protocol_host_gateway_wrapper_template_canonical_egress_sha256": "",
        "protocol_host_gateway_wrapper_template_canonical_session_chain_sha256": "",
        "protocol_host_gateway_wrapper_template_canonical_load_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_wrapper_template_latest_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_session_chain_semantic_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_host_visible_surface_contract_ref": "",
        "protocol_host_visible_surface_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_visible_surface_contract_key": HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
        "protocol_host_visible_surface_validator": "",
        "protocol_host_visible_surface_required_channels": [],
        "protocol_host_visible_surface_state_file": "",
        "protocol_host_visible_surface_receipt_pattern": "",
        "protocol_host_visible_surface_runtime_receipt_max_age_seconds": 0,
        "protocol_host_visible_surface_strict_live_run_binding_required": True,
        "protocol_host_visible_surface_runtime_live_receipt_sources": [],
        "protocol_host_visible_surface_fixture_receipt_source": "",
        "protocol_host_visible_surface_fixture_allowed_operations": [],
        "protocol_host_visible_surface_required_attestation_fields": [],
        "protocol_host_visible_surface_required_pass_status_fields": [],
        "protocol_host_visible_surface_live_probe_delegate": "",
        "protocol_host_gateway_broadcast_policy_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_host_gateway_broadcast_items_dir": "",
        "protocol_host_gateway_broadcast_index_file": "",
        "protocol_host_gateway_broadcast_schema_file": "",
        "protocol_host_gateway_broadcast_state_file": "",
        "protocol_host_gateway_broadcast_receipt_pattern": "",
        "protocol_host_gateway_broadcast_ack_pattern": "",
        "protocol_host_gateway_broadcast_block_on_critical_unacked": False,
        "error_code": "",
        "stale_reasons": [],
    }
    canonical_template_policy, canonical_template_policy_error = _load_canonical_wrapper_template_attestation_policy()
    canonical_template_attestation_id = str(canonical_template_policy.get("attestation_id", "")).strip()
    canonical_template_ingress_sha = str(
        canonical_template_policy.get("ingress_wrapper_template_sha256", "")
    ).strip()
    canonical_template_egress_sha = str(
        canonical_template_policy.get("egress_wrapper_template_sha256", "")
    ).strip()
    canonical_template_session_chain_sha = str(
        canonical_template_policy.get("session_chain_wrapper_template_sha256", "")
    ).strip()
    canonical_template_semantic_tokens = set(
        _as_str_list(canonical_template_policy.get("session_chain_required_semantic_tokens"))
    )
    canonical_template_tuple_fields = set(_as_str_list(canonical_template_policy.get("required_tuple_fields")))
    if not canonical_template_policy_error:
        canonical_policy_missing_fields: list[str] = []
        if not canonical_template_attestation_id:
            canonical_policy_missing_fields.append("attestation_id")
        if not canonical_template_ingress_sha:
            canonical_policy_missing_fields.append("ingress_wrapper_template_sha256")
        if not canonical_template_egress_sha:
            canonical_policy_missing_fields.append("egress_wrapper_template_sha256")
        if not canonical_template_session_chain_sha:
            canonical_policy_missing_fields.append("session_chain_wrapper_template_sha256")
        missing_semantic_tokens = sorted(
            token
            for token in HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS
            if token not in canonical_template_semantic_tokens
        )
        if missing_semantic_tokens:
            canonical_policy_missing_fields.append(
                "session_chain_required_semantic_tokens_missing:" + ",".join(missing_semantic_tokens)
            )
        missing_tuple_fields = sorted(
            field for field in HOST_GATEWAY_REQUIRED_TUPLE_FIELDS if field not in canonical_template_tuple_fields
        )
        if missing_tuple_fields:
            canonical_policy_missing_fields.append("required_tuple_fields_missing:" + ",".join(missing_tuple_fields))
        if canonical_policy_missing_fields:
            canonical_template_policy_error = (
                "canonical_wrapper_template_policy_missing_fields:" + "|".join(canonical_policy_missing_fields)
            )
    payload["protocol_host_gateway_wrapper_template_canonical_attestation_id"] = canonical_template_attestation_id
    payload["protocol_host_gateway_wrapper_template_canonical_ingress_sha256"] = canonical_template_ingress_sha
    payload["protocol_host_gateway_wrapper_template_canonical_egress_sha256"] = canonical_template_egress_sha
    payload["protocol_host_gateway_wrapper_template_canonical_session_chain_sha256"] = (
        canonical_template_session_chain_sha
    )
    payload["protocol_host_gateway_wrapper_template_canonical_load_status"] = (
        STATUS_FAIL_REQUIRED if canonical_template_policy_error else STATUS_PASS_REQUIRED
    )

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["unique_entry_contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    entry_script = str(contract.get("entry_script", "")).strip()
    validator_script = str(contract.get("validator", "")).strip()
    bundle_key = str(contract.get("bundle_key", "")).strip()
    scope = str(contract.get("scope", "")).strip()
    required_ops = _as_str_set(contract.get("enforce_on_operations"))
    error_family = _as_str_set(contract.get("entry_error_family"))
    receipt_required_by_contract = bool(contract.get("require_strict_operation_receipt", False))
    entry_receipt_state_file = str(contract.get("entry_receipt_state_file", "")).strip()
    entry_receipt_history_pattern = str(contract.get("entry_receipt_history_pattern", "")).strip()
    entry_receipt_max_age_raw = contract.get("entry_receipt_max_age_seconds", 0)
    try:
        entry_receipt_max_age_seconds = int(entry_receipt_max_age_raw)
    except Exception:
        entry_receipt_max_age_seconds = 0
    entry_receipt_required_fields = _as_str_set(contract.get("entry_receipt_required_fields"))
    entry_receipt_selector_policy_id = str(
        contract.get("entry_receipt_selector_policy_id", "")
    ).strip()
    entry_receipt_selector_precedence = _as_str_list(
        contract.get("entry_receipt_selector_precedence")
    )
    entry_receipt_selector_source_fields = _as_str_list(
        contract.get("entry_receipt_selector_source_fields")
    )

    payload["protocol_unique_entry_script"] = entry_script
    payload["protocol_unique_entry_bundle_key"] = bundle_key
    payload["protocol_unique_entry_scope"] = scope
    payload["protocol_unique_entry_required_operations"] = sorted(required_ops)
    payload["protocol_unique_entry_error_family"] = sorted(error_family)
    payload["protocol_unique_entry_receipt_required_by_cli_flag"] = bool(args.require_entry_receipt)
    payload["protocol_unique_entry_receipt_state_file"] = entry_receipt_state_file
    payload["protocol_unique_entry_receipt_history_pattern"] = entry_receipt_history_pattern
    payload["protocol_unique_entry_receipt_max_age_seconds"] = entry_receipt_max_age_seconds
    payload["protocol_unique_entry_receipt_required_fields"] = sorted(entry_receipt_required_fields)
    payload["protocol_unique_entry_receipt_selector_policy_id"] = entry_receipt_selector_policy_id
    payload["protocol_unique_entry_receipt_selector_precedence"] = list(
        entry_receipt_selector_precedence
    )
    payload["protocol_unique_entry_receipt_selector_source_fields"] = list(
        entry_receipt_selector_source_fields
    )

    if contract.get("required") is not True:
        issues.append("contract_required_flag_not_true")
    if validator_script != "scripts/validate_protocol_unique_entry_gate.py":
        issues.append("validator_script_mismatch")
    if entry_script != EXPECTED_ENTRY_SCRIPT:
        issues.append("entry_script_mismatch")
    if bundle_key != EXPECTED_BUNDLE_KEY:
        issues.append("bundle_key_mismatch")
    if scope != EXPECTED_SCOPE:
        issues.append("scope_mismatch")
    if not STRICT_OPERATIONS.issubset(required_ops):
        issues.append("strict_operations_not_fully_covered")
    if not EXPECTED_ENTRY_ERROR_FAMILY.issubset(error_family):
        issues.append("entry_error_family_missing_required_codes")
    if receipt_required_by_contract is not True:
        issues.append("entry_receipt_required_flag_mismatch")
    if not entry_receipt_state_file:
        issues.append("entry_receipt_state_file_missing")
    if not entry_receipt_history_pattern:
        issues.append("entry_receipt_history_pattern_missing")
    if entry_receipt_max_age_seconds <= 0:
        issues.append("entry_receipt_max_age_seconds_invalid")
    if not entry_receipt_required_fields:
        issues.append("entry_receipt_required_fields_missing")
    if entry_receipt_selector_policy_id != ENTRY_RECEIPT_SELECTOR_POLICY_ID:
        issues.append("entry_receipt_selector_policy_id_mismatch")
    if list(entry_receipt_selector_precedence) != list(ENTRY_RECEIPT_SELECTOR_PRECEDENCE):
        issues.append("entry_receipt_selector_precedence_mismatch")
    if list(entry_receipt_selector_source_fields) != list(ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS):
        issues.append("entry_receipt_selector_source_fields_mismatch")

    if issues:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    host_visible_surface_contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    host_visible_surface_issues: list[str] = []
    if not isinstance(host_visible_surface_contract, dict) or not host_visible_surface_contract:
        host_visible_surface_issues.append("host_visible_surface_contract_missing")
    else:
        unknown_visible_fields = _unknown_keys(host_visible_surface_contract, HOST_VISIBLE_SURFACE_ALLOWED_FIELDS)
        if unknown_visible_fields:
            host_visible_surface_issues.append(
                "host_visible_surface_contract_additional_properties:" + ",".join(unknown_visible_fields)
            )
        if host_visible_surface_contract.get("required") is not True:
            host_visible_surface_issues.append("host_visible_surface_required_flag_not_true")
        if str(host_visible_surface_contract.get("contract_id", "")).strip() != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID:
            host_visible_surface_issues.append("host_visible_surface_contract_id_mismatch")
        visible_validator = str(host_visible_surface_contract.get("validator", "")).strip()
        payload["protocol_host_visible_surface_validator"] = visible_validator
        if visible_validator != HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR:
            host_visible_surface_issues.append("host_visible_surface_validator_mismatch")
        visible_channels = set(_as_str_list(host_visible_surface_contract.get("required_channels")))
        payload["protocol_host_visible_surface_required_channels"] = sorted(visible_channels)
        if not HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS.issubset(visible_channels):
            host_visible_surface_issues.append("host_visible_surface_required_channels_missing")
        state_file = str(host_visible_surface_contract.get("runtime_state_file", "")).strip()
        receipt_pattern = str(host_visible_surface_contract.get("runtime_receipt_pattern", "")).strip()
        max_age_raw = host_visible_surface_contract.get(
            "runtime_receipt_max_age_seconds",
            HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
        )
        try:
            runtime_receipt_max_age_seconds = int(max_age_raw)
        except Exception:
            runtime_receipt_max_age_seconds = 0
        payload["protocol_host_visible_surface_state_file"] = state_file
        payload["protocol_host_visible_surface_receipt_pattern"] = receipt_pattern
        payload["protocol_host_visible_surface_runtime_receipt_max_age_seconds"] = (
            runtime_receipt_max_age_seconds
        )
        strict_live_run_binding_required = bool(
            _as_bool(
                host_visible_surface_contract.get(
                    "strict_live_run_binding_required",
                    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
                )
            )
        )
        runtime_live_sources = set(
            _as_str_list(host_visible_surface_contract.get("runtime_live_receipt_sources"))
        )
        if not runtime_live_sources:
            runtime_live_sources = set(HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES)
        fixture_receipt_source = str(
            host_visible_surface_contract.get("fixture_receipt_source", "")
        ).strip() or HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE
        fixture_allowed_operations = {
            str(token).strip().lower()
            for token in _as_str_list(host_visible_surface_contract.get("fixture_allowed_operations"))
            if str(token).strip()
        }
        if not fixture_allowed_operations:
            fixture_allowed_operations = set(HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS)
        payload["protocol_host_visible_surface_strict_live_run_binding_required"] = (
            strict_live_run_binding_required
        )
        payload["protocol_host_visible_surface_runtime_live_receipt_sources"] = sorted(
            runtime_live_sources
        )
        payload["protocol_host_visible_surface_fixture_receipt_source"] = fixture_receipt_source
        payload["protocol_host_visible_surface_fixture_allowed_operations"] = sorted(
            fixture_allowed_operations
        )
        if not state_file:
            host_visible_surface_issues.append("host_visible_surface_state_file_missing")
        if not receipt_pattern:
            host_visible_surface_issues.append("host_visible_surface_receipt_pattern_missing")
        if receipt_pattern and receipt_pattern != HOST_VISIBLE_SURFACE_RECEIPT_PATTERN:
            host_visible_surface_issues.append("host_visible_surface_receipt_pattern_mismatch")
        if runtime_receipt_max_age_seconds <= 0:
            host_visible_surface_issues.append("host_visible_surface_runtime_receipt_max_age_seconds_invalid")
        if not strict_live_run_binding_required:
            host_visible_surface_issues.append("host_visible_surface_strict_live_run_binding_required_not_true")
        if not runtime_live_sources:
            host_visible_surface_issues.append("host_visible_surface_runtime_live_receipt_sources_missing")
        if HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE not in runtime_live_sources:
            host_visible_surface_issues.append(
                "host_visible_surface_runtime_live_receipt_sources_missing_runtime_dialogue"
            )
        if fixture_receipt_source != HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE:
            host_visible_surface_issues.append("host_visible_surface_fixture_receipt_source_mismatch")
        if set(fixture_allowed_operations) != set(HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS):
            host_visible_surface_issues.append("host_visible_surface_fixture_allowed_operations_mismatch")
        attestation_fields = set(_as_str_list(host_visible_surface_contract.get("required_attestation_fields")))
        payload["protocol_host_visible_surface_required_attestation_fields"] = sorted(attestation_fields)
        if not HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS.issubset(attestation_fields):
            host_visible_surface_issues.append("host_visible_surface_required_attestation_fields_missing")
        pass_status_fields = set(_as_str_list(host_visible_surface_contract.get("required_pass_status_fields")))
        payload["protocol_host_visible_surface_required_pass_status_fields"] = sorted(pass_status_fields)
        if not HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS.issubset(pass_status_fields):
            host_visible_surface_issues.append("host_visible_surface_required_pass_status_fields_missing")
        live_probe_delegate = str(host_visible_surface_contract.get("required_live_probe_delegate", "")).strip()
        payload["protocol_host_visible_surface_live_probe_delegate"] = live_probe_delegate
        if live_probe_delegate != HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE:
            host_visible_surface_issues.append("host_visible_surface_live_probe_delegate_mismatch")
        dispatch_mode_required = str(
            host_visible_surface_contract.get("host_dispatch_mode_required", "")
        ).strip().lower()
        release_mode_required = str(
            host_visible_surface_contract.get("host_release_mode_required", "")
        ).strip().lower()
        if dispatch_mode_required != EXPECTED_HOST_DISPATCH_MODE:
            host_visible_surface_issues.append("host_visible_surface_dispatch_mode_required_mismatch")
        if release_mode_required != EXPECTED_HOST_RELEASE_MODE:
            host_visible_surface_issues.append("host_visible_surface_release_mode_required_mismatch")
        if state_file:
            state_path = _resolve_pack_relative_path(pack_path, state_file, HOST_VISIBLE_SURFACE_STATE_FILE)
            if not state_path.exists() or not state_path.is_file():
                host_visible_surface_issues.append("host_visible_surface_state_file_not_found")

    if host_visible_surface_issues:
        payload["protocol_host_visible_surface_contract_status"] = STATUS_FAIL_REQUIRED
    else:
        payload["protocol_host_visible_surface_contract_status"] = STATUS_PASS_REQUIRED

    host_gateway_contract, host_gateway_contract_key = _resolve_host_gateway_contract(task)
    payload["protocol_host_gateway_contract_key"] = host_gateway_contract_key
    receipt_required_surface_label = DEFAULT_ENTRY_RECEIPT_SURFACE_LABEL
    receipt_required_wrapper_surface_status = DEFAULT_ENTRY_RECEIPT_WRAPPER_SURFACE_STATUS
    receipt_required_wrapper_dispatch_status = DEFAULT_ENTRY_RECEIPT_WRAPPER_DISPATCH_STATUS
    host_gateway_dispatch_mode = ""
    host_gateway_strict_operations: set[str] = set()
    host_gateway_light_operations: set[str] = set()
    host_gateway_allow_upgrade_only = True
    host_gateway_broadcast_policy: dict[str, Any] = {}
    host_gateway_issues: list[str] = []
    if not isinstance(host_gateway_contract, dict) or not host_gateway_contract:
        host_gateway_issues.append("host_gateway_contract_missing")
    else:
        unknown_host_fields = _unknown_keys(host_gateway_contract, HOST_GATEWAY_ALLOWED_FIELDS)
        if unknown_host_fields:
            host_gateway_issues.append(
                "host_gateway_contract_additional_properties:" + ",".join(unknown_host_fields)
            )
        ingress_script = str(host_gateway_contract.get("protocol_ingress_script", "")).strip()
        egress_script = str(host_gateway_contract.get("protocol_egress_script", "")).strip()
        ingress_wrapper_raw = str(host_gateway_contract.get("ingress_wrapper_path", "")).strip()
        egress_wrapper_raw = str(host_gateway_contract.get("egress_wrapper_path", "")).strip()
        session_chain_wrapper_raw = str(host_gateway_contract.get("session_chain_wrapper_path", "")).strip()
        gateway_contract_raw = str(host_gateway_contract.get("gateway_contract_path", "")).strip()
        dispatch_mode = str(host_gateway_contract.get("host_dispatch_mode", "")).strip().lower()
        release_mode = str(host_gateway_contract.get("host_release_mode", "")).strip().lower()
        host_gateway_dispatch_mode = dispatch_mode
        ingress_dispatch_token = str(host_gateway_contract.get("ingress_wrapper_dispatch_token", "")).strip()
        tuple_fields = _as_str_set(host_gateway_contract.get("identity_tuple_fields"))
        operation_profile_policy = host_gateway_contract.get("operation_profile_policy")
        visible_surface_contract_ref = str(
            host_gateway_contract.get("host_visible_surface_registry_contract_ref", "")
        ).strip()
        payload["protocol_host_gateway_ingress_script"] = ingress_script
        payload["protocol_host_gateway_egress_script"] = egress_script
        payload["protocol_host_gateway_dispatch_mode"] = dispatch_mode
        payload["protocol_host_gateway_release_mode"] = release_mode
        payload["protocol_host_gateway_ingress_dispatch_token"] = ingress_dispatch_token
        payload["protocol_host_gateway_identity_tuple_fields"] = sorted(tuple_fields)
        payload["protocol_host_gateway_host_visible_surface_contract_ref"] = visible_surface_contract_ref

        ingress_wrapper_path = _resolve_pack_relative_path(
            pack_path,
            ingress_wrapper_raw,
            HOST_GATEWAY_EXPECTED_INGRESS_REL,
        )
        egress_wrapper_path = _resolve_pack_relative_path(
            pack_path,
            egress_wrapper_raw,
            HOST_GATEWAY_EXPECTED_EGRESS_REL,
        )
        session_chain_wrapper_path = _resolve_pack_relative_path(
            pack_path,
            session_chain_wrapper_raw,
            HOST_GATEWAY_EXPECTED_SESSION_CHAIN_REL,
        )
        gateway_contract_path = _resolve_pack_relative_path(
            pack_path,
            gateway_contract_raw,
            HOST_GATEWAY_EXPECTED_CONTRACT_REL,
        )
        payload["protocol_host_gateway_ingress_wrapper_path"] = str(ingress_wrapper_path)
        payload["protocol_host_gateway_egress_wrapper_path"] = str(egress_wrapper_path)
        payload["protocol_host_gateway_session_chain_wrapper_path"] = str(session_chain_wrapper_path)
        payload["protocol_host_gateway_contract_path"] = str(gateway_contract_path)

        if host_gateway_contract.get("required") is not True:
            host_gateway_issues.append("host_gateway_required_flag_not_true")
        if str(host_gateway_contract.get("validator", "")).strip() != "scripts/validate_protocol_unique_entry_gate.py":
            host_gateway_issues.append("host_gateway_validator_mismatch")
        if ingress_script != EXPECTED_ENTRY_SCRIPT:
            host_gateway_issues.append("host_gateway_ingress_script_mismatch")
        if egress_script != EXPECTED_EGRESS_SCRIPT:
            host_gateway_issues.append("host_gateway_egress_script_mismatch")
        if not session_chain_wrapper_raw:
            host_gateway_issues.append("host_gateway_session_chain_wrapper_path_missing")
        if dispatch_mode != EXPECTED_HOST_DISPATCH_MODE:
            host_gateway_issues.append("host_gateway_dispatch_mode_not_wrapper_only")
        if release_mode != EXPECTED_HOST_RELEASE_MODE:
            host_gateway_issues.append("host_gateway_release_mode_not_wrapper_only")
        if not ingress_dispatch_token:
            host_gateway_issues.append("host_gateway_ingress_dispatch_token_missing")
        if visible_surface_contract_ref != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY:
            host_gateway_issues.append("host_gateway_host_visible_surface_contract_ref_mismatch")
        if not HOST_GATEWAY_REQUIRED_TUPLE_FIELDS.issubset(tuple_fields):
            host_gateway_issues.append("host_gateway_tuple_fields_missing")
        template_attestation_policy = host_gateway_contract.get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)
        if not isinstance(template_attestation_policy, dict):
            host_gateway_issues.append("host_gateway_wrapper_template_attestation_policy_missing")
        else:
            unknown_template_fields = _unknown_keys(
                template_attestation_policy,
                HOST_GATEWAY_TEMPLATE_ATTESTATION_ALLOWED_FIELDS,
            )
            if unknown_template_fields:
                host_gateway_issues.append(
                    "host_gateway_wrapper_template_attestation_additional_properties:"
                    + ",".join(unknown_template_fields)
                )
            if template_attestation_policy.get("required") is not True:
                host_gateway_issues.append("host_gateway_wrapper_template_attestation_required_not_true")
            attestation_id = str(template_attestation_policy.get("attestation_id", "")).strip()
            ingress_template_sha = str(
                template_attestation_policy.get("ingress_wrapper_template_sha256", "")
            ).strip()
            egress_template_sha = str(
                template_attestation_policy.get("egress_wrapper_template_sha256", "")
            ).strip()
            session_chain_template_sha = str(
                template_attestation_policy.get("session_chain_wrapper_template_sha256", "")
            ).strip()
            semantic_tokens = set(
                _as_str_list(template_attestation_policy.get("session_chain_required_semantic_tokens"))
            )
            required_tuple_fields = set(_as_str_list(template_attestation_policy.get("required_tuple_fields")))
            payload["protocol_host_gateway_wrapper_template_attestation_id"] = attestation_id
            payload["protocol_host_gateway_wrapper_template_ingress_sha256"] = ingress_template_sha
            payload["protocol_host_gateway_wrapper_template_egress_sha256"] = egress_template_sha
            payload["protocol_host_gateway_wrapper_template_session_chain_sha256"] = session_chain_template_sha
            if not attestation_id:
                host_gateway_issues.append("host_gateway_wrapper_template_attestation_id_missing")
            if not ingress_template_sha:
                host_gateway_issues.append("host_gateway_wrapper_template_ingress_sha256_missing")
            if not egress_template_sha:
                host_gateway_issues.append("host_gateway_wrapper_template_egress_sha256_missing")
            if not session_chain_template_sha:
                host_gateway_issues.append("host_gateway_wrapper_template_session_chain_sha256_missing")
            if not HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS.issubset(semantic_tokens):
                host_gateway_issues.append("host_gateway_wrapper_template_semantic_tokens_missing")
            if not HOST_GATEWAY_REQUIRED_TUPLE_FIELDS.issubset(required_tuple_fields):
                host_gateway_issues.append("host_gateway_wrapper_template_required_tuple_fields_missing")
            if canonical_template_policy_error:
                host_gateway_issues.append(
                    "host_gateway_wrapper_template_canonical_policy_unavailable:" + canonical_template_policy_error
                )
            else:
                if attestation_id != canonical_template_attestation_id:
                    host_gateway_issues.append("host_gateway_wrapper_template_attestation_not_latest:attestation_id")
                if ingress_template_sha != canonical_template_ingress_sha:
                    host_gateway_issues.append(
                        "host_gateway_wrapper_template_attestation_not_latest:ingress_wrapper_template_sha256"
                    )
                if egress_template_sha != canonical_template_egress_sha:
                    host_gateway_issues.append(
                        "host_gateway_wrapper_template_attestation_not_latest:egress_wrapper_template_sha256"
                    )
                if session_chain_template_sha != canonical_template_session_chain_sha:
                    host_gateway_issues.append(
                        "host_gateway_wrapper_template_attestation_not_latest:session_chain_wrapper_template_sha256"
                    )
                if semantic_tokens != canonical_template_semantic_tokens:
                    host_gateway_issues.append(
                        "host_gateway_wrapper_template_attestation_not_latest:session_chain_required_semantic_tokens"
                    )
                if required_tuple_fields != canonical_template_tuple_fields:
                    host_gateway_issues.append(
                        "host_gateway_wrapper_template_attestation_not_latest:required_tuple_fields"
                    )
        if not isinstance(operation_profile_policy, dict):
            host_gateway_issues.append("host_gateway_operation_profile_policy_missing")
        else:
            unknown_profile_fields = _unknown_keys(
                operation_profile_policy,
                HOST_GATEWAY_OPERATION_PROFILE_ALLOWED_FIELDS,
            )
            if unknown_profile_fields:
                host_gateway_issues.append(
                    "host_gateway_operation_profile_additional_properties:" + ",".join(unknown_profile_fields)
                )
            strict_operations = _as_str_set(operation_profile_policy.get("strict_operations"))
            light_operations = _as_str_set(operation_profile_policy.get("light_operations"))
            strict_gate_profile = str(operation_profile_policy.get("strict_gate_profile", "")).strip()
            light_gate_profile = str(operation_profile_policy.get("light_gate_profile", "")).strip()
            allow_upgrade_only = bool(operation_profile_policy.get("allow_upgrade_only", True))
            host_gateway_strict_operations = set(strict_operations)
            host_gateway_light_operations = set(light_operations)
            host_gateway_allow_upgrade_only = allow_upgrade_only
            payload["protocol_host_gateway_strict_operations"] = sorted(strict_operations)
            payload["protocol_host_gateway_light_operations"] = sorted(light_operations)
            payload["protocol_host_gateway_strict_gate_profile"] = strict_gate_profile
            payload["protocol_host_gateway_light_gate_profile"] = light_gate_profile
            payload["protocol_host_gateway_allow_upgrade_only"] = allow_upgrade_only
            if not strict_operations:
                host_gateway_issues.append("host_gateway_operation_profile_strict_operations_missing")
            if not STRICT_OPERATIONS.issubset(strict_operations):
                host_gateway_issues.append("host_gateway_operation_profile_strict_operations_not_covered")
            if not light_operations:
                host_gateway_issues.append("host_gateway_operation_profile_light_operations_missing")
            if not strict_gate_profile:
                host_gateway_issues.append("host_gateway_operation_profile_strict_gate_profile_missing")
            if not light_gate_profile:
                host_gateway_issues.append("host_gateway_operation_profile_light_gate_profile_missing")
        entry_policy = host_gateway_contract.get("entry_receipt_policy")
        if not isinstance(entry_policy, dict) or entry_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_entry_receipt_policy_missing")
        else:
            unknown_entry_policy_fields = _unknown_keys(
                entry_policy,
                HOST_GATEWAY_ENTRY_POLICY_ALLOWED_FIELDS,
            )
            if unknown_entry_policy_fields:
                host_gateway_issues.append(
                    "host_gateway_entry_receipt_policy_additional_properties:"
                    + ",".join(unknown_entry_policy_fields)
                )
            entry_policy_surface_label = str(entry_policy.get("required_surface_label", "")).strip()
            entry_policy_wrapper_surface_status = str(
                entry_policy.get("required_wrapper_surface_status", "")
            ).strip().upper()
            entry_policy_wrapper_dispatch_status = str(
                entry_policy.get("required_wrapper_dispatch_token_status", "")
            ).strip().upper()
            payload["protocol_host_gateway_entry_receipt_required_surface_label"] = entry_policy_surface_label
            payload["protocol_host_gateway_entry_receipt_required_wrapper_surface_status"] = (
                entry_policy_wrapper_surface_status
            )
            payload["protocol_host_gateway_entry_receipt_required_wrapper_dispatch_token_status"] = (
                entry_policy_wrapper_dispatch_status
            )
            if not entry_policy_surface_label:
                host_gateway_issues.append("host_gateway_entry_receipt_policy_surface_label_missing")
            if not entry_policy_wrapper_surface_status:
                host_gateway_issues.append("host_gateway_entry_receipt_policy_wrapper_surface_status_missing")
            if not entry_policy_wrapper_dispatch_status:
                host_gateway_issues.append("host_gateway_entry_receipt_policy_wrapper_dispatch_status_missing")
            if entry_policy_surface_label:
                receipt_required_surface_label = entry_policy_surface_label
            if entry_policy_wrapper_surface_status:
                receipt_required_wrapper_surface_status = entry_policy_wrapper_surface_status
            if entry_policy_wrapper_dispatch_status:
                receipt_required_wrapper_dispatch_status = entry_policy_wrapper_dispatch_status
        ingress_proof_policy = host_gateway_contract.get("ingress_proof_policy")
        if not isinstance(ingress_proof_policy, dict) or ingress_proof_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_ingress_proof_policy_missing")
        else:
            unknown_ingress_proof_fields = _unknown_keys(
                ingress_proof_policy,
                HOST_GATEWAY_INGRESS_PROOF_POLICY_ALLOWED_FIELDS,
            )
            if unknown_ingress_proof_fields:
                host_gateway_issues.append(
                    "host_gateway_ingress_proof_policy_additional_properties:"
                    + ",".join(unknown_ingress_proof_fields)
                )
            if _safe_int(ingress_proof_policy.get("max_age_seconds"), default=0) <= 0:
                host_gateway_issues.append("host_gateway_ingress_proof_policy_max_age_invalid")
            _validate_signer_policy(
                ingress_proof_policy,
                issue_prefix="host_gateway_ingress_proof_policy",
                issues=host_gateway_issues,
            )
        egress_policy = host_gateway_contract.get("egress_receipt_policy")
        if not isinstance(egress_policy, dict) or egress_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_egress_receipt_policy_missing")
        else:
            unknown_egress_policy_fields = _unknown_keys(
                egress_policy,
                HOST_GATEWAY_EGRESS_POLICY_ALLOWED_FIELDS,
            )
            if unknown_egress_policy_fields:
                host_gateway_issues.append(
                    "host_gateway_egress_receipt_policy_additional_properties:"
                    + ",".join(unknown_egress_policy_fields)
                )
        egress_grant_policy = host_gateway_contract.get("egress_grant_policy")
        if not isinstance(egress_grant_policy, dict) or egress_grant_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_egress_grant_policy_missing")
        else:
            unknown_egress_grant_fields = _unknown_keys(
                egress_grant_policy,
                HOST_GATEWAY_EGRESS_GRANT_POLICY_ALLOWED_FIELDS,
            )
            if unknown_egress_grant_fields:
                host_gateway_issues.append(
                    "host_gateway_egress_grant_policy_additional_properties:"
                    + ",".join(unknown_egress_grant_fields)
                )
            if _safe_int(egress_grant_policy.get("max_age_seconds"), default=0) <= 0:
                host_gateway_issues.append("host_gateway_egress_grant_policy_max_age_invalid")
            _validate_signer_policy(
                egress_grant_policy,
                issue_prefix="host_gateway_egress_grant_policy",
                issues=host_gateway_issues,
            )
        headstamp_policy = host_gateway_contract.get("headstamp_policy")
        if not isinstance(headstamp_policy, dict) or headstamp_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_headstamp_policy_missing")
        else:
            unknown_headstamp_fields = _unknown_keys(
                headstamp_policy,
                HOST_GATEWAY_HEADSTAMP_POLICY_ALLOWED_FIELDS,
            )
            if unknown_headstamp_fields:
                host_gateway_issues.append(
                    "host_gateway_headstamp_policy_additional_properties:"
                    + ",".join(unknown_headstamp_fields)
                )
        broadcast_policy = host_gateway_contract.get("broadcast_policy")
        if not isinstance(broadcast_policy, dict) or broadcast_policy.get("required") is not True:
            host_gateway_issues.append("host_gateway_broadcast_policy_missing")
        else:
            host_gateway_broadcast_policy = dict(broadcast_policy)
            unknown_broadcast_fields = _unknown_keys(
                broadcast_policy,
                HOST_GATEWAY_BROADCAST_POLICY_ALLOWED_FIELDS,
            )
            if unknown_broadcast_fields:
                host_gateway_issues.append(
                    "host_gateway_broadcast_policy_additional_properties:" + ",".join(unknown_broadcast_fields)
                )
            items_dir = str(broadcast_policy.get("protocol_broadcast_items_dir", "")).strip()
            index_file = str(broadcast_policy.get("protocol_broadcast_index_file", "")).strip()
            schema_file = str(broadcast_policy.get("protocol_broadcast_schema_file", "")).strip()
            state_file = str(broadcast_policy.get("instance_state_file", "")).strip()
            receipt_pattern = str(broadcast_policy.get("instance_receipt_pattern", "")).strip()
            ack_pattern = str(broadcast_policy.get("instance_ack_pattern", "")).strip()
            block_on_critical = bool(broadcast_policy.get("block_on_critical_unacked", False))
            payload["protocol_host_gateway_broadcast_items_dir"] = items_dir
            payload["protocol_host_gateway_broadcast_index_file"] = index_file
            payload["protocol_host_gateway_broadcast_schema_file"] = schema_file
            payload["protocol_host_gateway_broadcast_state_file"] = state_file
            payload["protocol_host_gateway_broadcast_receipt_pattern"] = receipt_pattern
            payload["protocol_host_gateway_broadcast_ack_pattern"] = ack_pattern
            payload["protocol_host_gateway_broadcast_block_on_critical_unacked"] = block_on_critical
            if items_dir != HOST_GATEWAY_BROADCAST_ITEMS_DIR:
                host_gateway_issues.append("host_gateway_broadcast_items_dir_mismatch")
            if index_file != HOST_GATEWAY_BROADCAST_INDEX_FILE:
                host_gateway_issues.append("host_gateway_broadcast_index_file_mismatch")
            if schema_file != HOST_GATEWAY_BROADCAST_SCHEMA_FILE:
                host_gateway_issues.append("host_gateway_broadcast_schema_file_mismatch")
            if not state_file:
                host_gateway_issues.append("host_gateway_broadcast_state_file_missing")
            if not receipt_pattern:
                host_gateway_issues.append("host_gateway_broadcast_receipt_pattern_missing")
            if not ack_pattern:
                host_gateway_issues.append("host_gateway_broadcast_ack_pattern_missing")
            payload["protocol_host_gateway_broadcast_policy_status"] = STATUS_PASS_REQUIRED

        missing_runtime_files: list[str] = []
        if not ingress_wrapper_path.exists():
            missing_runtime_files.append("ingress_wrapper_missing")
        if not egress_wrapper_path.exists():
            missing_runtime_files.append("egress_wrapper_missing")
        if not session_chain_wrapper_path.exists():
            missing_runtime_files.append("session_chain_wrapper_missing")
        if not gateway_contract_path.exists():
            missing_runtime_files.append("gateway_contract_missing")
        if missing_runtime_files:
            host_gateway_issues.extend([f"host_gateway_runtime:{item}" for item in missing_runtime_files])
            payload["protocol_host_gateway_runtime_files_status"] = STATUS_FAIL_REQUIRED
        else:
            payload["protocol_host_gateway_runtime_files_status"] = STATUS_PASS_REQUIRED
            ingress_text = ingress_wrapper_path.read_text(encoding="utf-8", errors="ignore")
            egress_text = egress_wrapper_path.read_text(encoding="utf-8", errors="ignore")
            session_chain_text = session_chain_wrapper_path.read_text(encoding="utf-8", errors="ignore")
            if EXPECTED_ENTRY_SCRIPT not in ingress_text:
                host_gateway_issues.append("host_gateway_ingress_wrapper_not_bound_to_canonical_script")
            if EXPECTED_EGRESS_SCRIPT not in egress_text:
                host_gateway_issues.append("host_gateway_egress_wrapper_not_bound_to_canonical_script")
            session_chain_semantic_missing = sorted(
                token
                for token in HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS
                if token not in session_chain_text
            )
            if session_chain_semantic_missing:
                host_gateway_issues.append(
                    "host_gateway_session_chain_wrapper_semantic_tokens_missing:"
                    + ",".join(session_chain_semantic_missing)
                )
                payload["protocol_host_gateway_session_chain_semantic_status"] = STATUS_FAIL_REQUIRED
            else:
                payload["protocol_host_gateway_session_chain_semantic_status"] = STATUS_PASS_REQUIRED
            template_attestation_policy = host_gateway_contract.get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)
            if isinstance(template_attestation_policy, dict):
                ingress_wrapper_sha = _sha256_file(ingress_wrapper_path)
                egress_wrapper_sha = _sha256_file(egress_wrapper_path)
                session_chain_wrapper_sha = _sha256_file(session_chain_wrapper_path)
                expected_ingress_sha = str(
                    template_attestation_policy.get("ingress_wrapper_template_sha256", "")
                ).strip()
                expected_egress_sha = str(
                    template_attestation_policy.get("egress_wrapper_template_sha256", "")
                ).strip()
                expected_session_chain_sha = str(
                    template_attestation_policy.get("session_chain_wrapper_template_sha256", "")
                ).strip()
                if expected_ingress_sha and ingress_wrapper_sha != expected_ingress_sha:
                    host_gateway_issues.append("host_gateway_ingress_wrapper_template_sha256_mismatch")
                if expected_egress_sha and egress_wrapper_sha != expected_egress_sha:
                    host_gateway_issues.append("host_gateway_egress_wrapper_template_sha256_mismatch")
                if expected_session_chain_sha and session_chain_wrapper_sha != expected_session_chain_sha:
                    host_gateway_issues.append("host_gateway_session_chain_wrapper_template_sha256_mismatch")
                if canonical_template_ingress_sha and ingress_wrapper_sha != canonical_template_ingress_sha:
                    host_gateway_issues.append("host_gateway_ingress_wrapper_template_sha256_not_latest")
                if canonical_template_egress_sha and egress_wrapper_sha != canonical_template_egress_sha:
                    host_gateway_issues.append("host_gateway_egress_wrapper_template_sha256_not_latest")
                if canonical_template_session_chain_sha and session_chain_wrapper_sha != canonical_template_session_chain_sha:
                    host_gateway_issues.append("host_gateway_session_chain_wrapper_template_sha256_not_latest")
            if not any("wrapper_template" in issue for issue in host_gateway_issues):
                payload["protocol_host_gateway_wrapper_template_attestation_status"] = STATUS_PASS_REQUIRED
            else:
                payload["protocol_host_gateway_wrapper_template_attestation_status"] = STATUS_FAIL_REQUIRED
            try:
                runtime_gateway_contract = _load_receipt(gateway_contract_path)
            except Exception as exc:
                host_gateway_issues.append(f"host_gateway_runtime_contract_invalid:{exc}")
                payload["protocol_host_gateway_runtime_contract_status"] = STATUS_FAIL_REQUIRED
            else:
                required_runtime_fields = set(RUNTIME_GATEWAY_ALLOWED_FIELDS)
                missing_runtime_fields = sorted(
                    field for field in required_runtime_fields if field not in runtime_gateway_contract
                )
                unknown_runtime_fields = _unknown_keys(
                    runtime_gateway_contract,
                    RUNTIME_GATEWAY_ALLOWED_FIELDS,
                )
                if missing_runtime_fields:
                    host_gateway_issues.append(
                        "host_gateway_runtime_contract_fields_missing:" + ",".join(missing_runtime_fields)
                    )
                if unknown_runtime_fields:
                    host_gateway_issues.append(
                        "host_gateway_runtime_contract_additional_properties:" + ",".join(unknown_runtime_fields)
                    )
                if str(runtime_gateway_contract.get("identity_id", "")).strip() != str(args.identity_id).strip():
                    host_gateway_issues.append("host_gateway_runtime_contract_identity_mismatch")
                if str(runtime_gateway_contract.get("protocol_ingress_script", "")).strip() != EXPECTED_ENTRY_SCRIPT:
                    host_gateway_issues.append("host_gateway_runtime_contract_ingress_script_mismatch")
                if str(runtime_gateway_contract.get("protocol_egress_script", "")).strip() != EXPECTED_EGRESS_SCRIPT:
                    host_gateway_issues.append("host_gateway_runtime_contract_egress_script_mismatch")
                runtime_session_chain_wrapper_path = _resolve_pack_relative_path(
                    pack_path,
                    str(runtime_gateway_contract.get("session_chain_wrapper_path", "")).strip(),
                    HOST_GATEWAY_EXPECTED_SESSION_CHAIN_REL,
                )
                if runtime_session_chain_wrapper_path != session_chain_wrapper_path:
                    host_gateway_issues.append("host_gateway_runtime_contract_session_chain_wrapper_path_mismatch")
                if str(runtime_gateway_contract.get("host_dispatch_mode", "")).strip().lower() != EXPECTED_HOST_DISPATCH_MODE:
                    host_gateway_issues.append("host_gateway_runtime_contract_dispatch_mode_not_wrapper_only")
                if str(runtime_gateway_contract.get("host_release_mode", "")).strip().lower() != EXPECTED_HOST_RELEASE_MODE:
                    host_gateway_issues.append("host_gateway_runtime_contract_release_mode_not_wrapper_only")
                if str(runtime_gateway_contract.get("ingress_wrapper_dispatch_token", "")).strip() != ingress_dispatch_token:
                    host_gateway_issues.append("host_gateway_runtime_contract_ingress_dispatch_token_mismatch")
                runtime_tuple_fields = _as_str_set(runtime_gateway_contract.get("identity_tuple_fields"))
                if not HOST_GATEWAY_REQUIRED_TUPLE_FIELDS.issubset(runtime_tuple_fields):
                    host_gateway_issues.append("host_gateway_runtime_contract_tuple_fields_missing")
                runtime_operation_profile = runtime_gateway_contract.get("operation_profile_policy")
                if not isinstance(runtime_operation_profile, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_operation_profile_policy_missing")
                elif isinstance(operation_profile_policy, dict):
                    unknown_runtime_profile_fields = _unknown_keys(
                        runtime_operation_profile,
                        HOST_GATEWAY_OPERATION_PROFILE_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_profile_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_operation_profile_additional_properties:"
                            + ",".join(unknown_runtime_profile_fields)
                        )
                    runtime_strict_operations = _as_str_set(runtime_operation_profile.get("strict_operations"))
                    runtime_light_operations = _as_str_set(runtime_operation_profile.get("light_operations"))
                    runtime_strict_gate_profile = str(runtime_operation_profile.get("strict_gate_profile", "")).strip()
                    runtime_light_gate_profile = str(runtime_operation_profile.get("light_gate_profile", "")).strip()
                    runtime_allow_upgrade_only = bool(runtime_operation_profile.get("allow_upgrade_only", True))
                    contract_strict_operations = _as_str_set(operation_profile_policy.get("strict_operations"))
                    contract_light_operations = _as_str_set(operation_profile_policy.get("light_operations"))
                    contract_strict_gate_profile = str(operation_profile_policy.get("strict_gate_profile", "")).strip()
                    contract_light_gate_profile = str(operation_profile_policy.get("light_gate_profile", "")).strip()
                    contract_allow_upgrade_only = bool(operation_profile_policy.get("allow_upgrade_only", True))
                    if runtime_strict_operations != contract_strict_operations:
                        host_gateway_issues.append("host_gateway_runtime_contract_strict_operations_mismatch")
                    if runtime_light_operations != contract_light_operations:
                        host_gateway_issues.append("host_gateway_runtime_contract_light_operations_mismatch")
                    if runtime_strict_gate_profile != contract_strict_gate_profile:
                        host_gateway_issues.append("host_gateway_runtime_contract_strict_gate_profile_mismatch")
                    if runtime_light_gate_profile != contract_light_gate_profile:
                        host_gateway_issues.append("host_gateway_runtime_contract_light_gate_profile_mismatch")
                    if runtime_allow_upgrade_only != contract_allow_upgrade_only:
                        host_gateway_issues.append("host_gateway_runtime_contract_allow_upgrade_only_mismatch")
                runtime_visible_ref = str(
                    runtime_gateway_contract.get("host_visible_surface_registry_contract_ref", "")
                ).strip()
                if runtime_visible_ref != visible_surface_contract_ref:
                    host_gateway_issues.append("host_gateway_runtime_contract_host_visible_surface_contract_ref_mismatch")
                runtime_template_attestation = runtime_gateway_contract.get(
                    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY
                )
                if not isinstance(runtime_template_attestation, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_wrapper_template_attestation_missing")
                else:
                    unknown_runtime_template_fields = _unknown_keys(
                        runtime_template_attestation,
                        HOST_GATEWAY_TEMPLATE_ATTESTATION_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_template_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_wrapper_template_attestation_additional_properties:"
                            + ",".join(unknown_runtime_template_fields)
                        )
                    contract_template_attestation = (
                        host_gateway_contract.get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)
                        if isinstance(host_gateway_contract, dict)
                        else {}
                    )
                    if isinstance(contract_template_attestation, dict):
                        for field in (
                            "required",
                            "attestation_id",
                            "ingress_wrapper_template_sha256",
                            "egress_wrapper_template_sha256",
                            "session_chain_wrapper_template_sha256",
                            "session_chain_required_semantic_tokens",
                            "required_tuple_fields",
                        ):
                            if runtime_template_attestation.get(field) != contract_template_attestation.get(field):
                                host_gateway_issues.append(
                                    "host_gateway_runtime_contract_wrapper_template_attestation_parity_mismatch:" + field
                                )
                    if not canonical_template_policy_error:
                        canonical_runtime_pairs = {
                            "attestation_id": canonical_template_attestation_id,
                            "ingress_wrapper_template_sha256": canonical_template_ingress_sha,
                            "egress_wrapper_template_sha256": canonical_template_egress_sha,
                            "session_chain_wrapper_template_sha256": canonical_template_session_chain_sha,
                            "session_chain_required_semantic_tokens": sorted(canonical_template_semantic_tokens),
                            "required_tuple_fields": sorted(canonical_template_tuple_fields),
                        }
                        for field, expected_value in canonical_runtime_pairs.items():
                            observed_value = runtime_template_attestation.get(field)
                            if field in {"session_chain_required_semantic_tokens", "required_tuple_fields"}:
                                observed_value = sorted(_as_str_list(observed_value))
                            if observed_value != expected_value:
                                host_gateway_issues.append(
                                    "host_gateway_runtime_contract_wrapper_template_attestation_not_latest:" + field
                                )
                runtime_visible_surface_contract = runtime_gateway_contract.get(
                    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
                )
                if not isinstance(runtime_visible_surface_contract, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_host_visible_surface_contract_missing")
                else:
                    unknown_runtime_visible_fields = _unknown_keys(
                        runtime_visible_surface_contract,
                        HOST_VISIBLE_SURFACE_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_visible_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_host_visible_surface_contract_additional_properties:"
                            + ",".join(unknown_runtime_visible_fields)
                        )
                    if isinstance(host_visible_surface_contract, dict):
                        for field in HOST_VISIBLE_SURFACE_ALLOWED_FIELDS:
                            if runtime_visible_surface_contract.get(field) != host_visible_surface_contract.get(field):
                                host_gateway_issues.append(
                                    "host_gateway_runtime_contract_host_visible_surface_contract_parity_mismatch:" + field
                                )
                runtime_entry_policy = runtime_gateway_contract.get("entry_receipt_policy")
                if not isinstance(runtime_entry_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_entry_receipt_policy_missing")
                else:
                    unknown_runtime_entry_fields = _unknown_keys(
                        runtime_entry_policy,
                        HOST_GATEWAY_ENTRY_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_entry_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_entry_receipt_policy_additional_properties:"
                            + ",".join(unknown_runtime_entry_fields)
                        )
                    runtime_entry_surface = str(runtime_entry_policy.get("required_surface_label", "")).strip()
                    runtime_entry_wrapper_surface_status = str(
                        runtime_entry_policy.get("required_wrapper_surface_status", "")
                    ).strip().upper()
                    runtime_entry_wrapper_dispatch_status = str(
                        runtime_entry_policy.get("required_wrapper_dispatch_token_status", "")
                    ).strip().upper()
                    if runtime_entry_surface != receipt_required_surface_label:
                        host_gateway_issues.append("host_gateway_runtime_contract_entry_surface_label_mismatch")
                    if runtime_entry_wrapper_surface_status != receipt_required_wrapper_surface_status:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_entry_wrapper_surface_status_mismatch"
                        )
                    if runtime_entry_wrapper_dispatch_status != receipt_required_wrapper_dispatch_status:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_entry_wrapper_dispatch_status_mismatch"
                        )
                runtime_ingress_proof_policy = runtime_gateway_contract.get("ingress_proof_policy")
                if not isinstance(runtime_ingress_proof_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_ingress_proof_policy_missing")
                else:
                    unknown_runtime_ingress_proof_fields = _unknown_keys(
                        runtime_ingress_proof_policy,
                        HOST_GATEWAY_INGRESS_PROOF_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_ingress_proof_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_ingress_proof_policy_additional_properties:"
                            + ",".join(unknown_runtime_ingress_proof_fields)
                        )
                    if _safe_int(runtime_ingress_proof_policy.get("max_age_seconds"), default=0) <= 0:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_ingress_proof_policy_max_age_invalid"
                        )
                    _validate_signer_policy(
                        runtime_ingress_proof_policy,
                        issue_prefix="host_gateway_runtime_contract_ingress_proof_policy",
                        issues=host_gateway_issues,
                    )
                    contract_ingress_signer_mode = str((ingress_proof_policy or {}).get("signer_mode", "")).strip().lower()
                    runtime_ingress_signer_mode = str(runtime_ingress_proof_policy.get("signer_mode", "")).strip().lower()
                    if contract_ingress_signer_mode != runtime_ingress_signer_mode:
                        host_gateway_issues.append("host_gateway_runtime_contract_ingress_signer_mode_mismatch")
                    contract_ingress_signer_env = str((ingress_proof_policy or {}).get("signer_secret_env", "")).strip()
                    runtime_ingress_signer_env = str(runtime_ingress_proof_policy.get("signer_secret_env", "")).strip()
                    if contract_ingress_signer_env != runtime_ingress_signer_env:
                        host_gateway_issues.append("host_gateway_runtime_contract_ingress_signer_secret_env_mismatch")
                    contract_ingress_signing_key_path = str((ingress_proof_policy or {}).get("signing_key_path", "")).strip()
                    runtime_ingress_signing_key_path = str(runtime_ingress_proof_policy.get("signing_key_path", "")).strip()
                    if contract_ingress_signing_key_path != runtime_ingress_signing_key_path:
                        host_gateway_issues.append("host_gateway_runtime_contract_ingress_signing_key_path_mismatch")
                    contract_ingress_bootstrap_from_key = (ingress_proof_policy or {}).get(
                        "bootstrap_env_secret_from_signing_key_path"
                    )
                    runtime_ingress_bootstrap_from_key = runtime_ingress_proof_policy.get(
                        "bootstrap_env_secret_from_signing_key_path"
                    )
                    if contract_ingress_bootstrap_from_key != runtime_ingress_bootstrap_from_key:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_ingress_bootstrap_env_secret_from_signing_key_path_mismatch"
                        )
                runtime_egress_policy = runtime_gateway_contract.get("egress_receipt_policy")
                if not isinstance(runtime_egress_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_egress_receipt_policy_missing")
                else:
                    unknown_runtime_egress_fields = _unknown_keys(
                        runtime_egress_policy,
                        HOST_GATEWAY_EGRESS_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_egress_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_egress_receipt_policy_additional_properties:"
                            + ",".join(unknown_runtime_egress_fields)
                        )
                runtime_egress_grant_policy = runtime_gateway_contract.get("egress_grant_policy")
                if not isinstance(runtime_egress_grant_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_egress_grant_policy_missing")
                else:
                    unknown_runtime_egress_grant_fields = _unknown_keys(
                        runtime_egress_grant_policy,
                        HOST_GATEWAY_EGRESS_GRANT_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_egress_grant_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_egress_grant_policy_additional_properties:"
                            + ",".join(unknown_runtime_egress_grant_fields)
                        )
                    if _safe_int(runtime_egress_grant_policy.get("max_age_seconds"), default=0) <= 0:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_egress_grant_policy_max_age_invalid"
                        )
                    _validate_signer_policy(
                        runtime_egress_grant_policy,
                        issue_prefix="host_gateway_runtime_contract_egress_grant_policy",
                        issues=host_gateway_issues,
                    )
                    contract_egress_signer_mode = str((egress_grant_policy or {}).get("signer_mode", "")).strip().lower()
                    runtime_egress_signer_mode = str(runtime_egress_grant_policy.get("signer_mode", "")).strip().lower()
                    if contract_egress_signer_mode != runtime_egress_signer_mode:
                        host_gateway_issues.append("host_gateway_runtime_contract_egress_signer_mode_mismatch")
                    contract_egress_signer_env = str((egress_grant_policy or {}).get("signer_secret_env", "")).strip()
                    runtime_egress_signer_env = str(runtime_egress_grant_policy.get("signer_secret_env", "")).strip()
                    if contract_egress_signer_env != runtime_egress_signer_env:
                        host_gateway_issues.append("host_gateway_runtime_contract_egress_signer_secret_env_mismatch")
                    contract_egress_signing_key_path = str((egress_grant_policy or {}).get("signing_key_path", "")).strip()
                    runtime_egress_signing_key_path = str(runtime_egress_grant_policy.get("signing_key_path", "")).strip()
                    if contract_egress_signing_key_path != runtime_egress_signing_key_path:
                        host_gateway_issues.append("host_gateway_runtime_contract_egress_signing_key_path_mismatch")
                    contract_egress_bootstrap_from_key = (egress_grant_policy or {}).get(
                        "bootstrap_env_secret_from_signing_key_path"
                    )
                    runtime_egress_bootstrap_from_key = runtime_egress_grant_policy.get(
                        "bootstrap_env_secret_from_signing_key_path"
                    )
                    if contract_egress_bootstrap_from_key != runtime_egress_bootstrap_from_key:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_egress_bootstrap_env_secret_from_signing_key_path_mismatch"
                        )
                runtime_headstamp_policy = runtime_gateway_contract.get("headstamp_policy")
                if not isinstance(runtime_headstamp_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_headstamp_policy_missing")
                else:
                    unknown_runtime_headstamp_fields = _unknown_keys(
                        runtime_headstamp_policy,
                        HOST_GATEWAY_HEADSTAMP_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_headstamp_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_headstamp_policy_additional_properties:"
                            + ",".join(unknown_runtime_headstamp_fields)
                        )
                runtime_broadcast_policy = runtime_gateway_contract.get("broadcast_policy")
                if not isinstance(runtime_broadcast_policy, dict):
                    host_gateway_issues.append("host_gateway_runtime_contract_broadcast_policy_missing")
                else:
                    unknown_runtime_broadcast_fields = _unknown_keys(
                        runtime_broadcast_policy,
                        HOST_GATEWAY_BROADCAST_POLICY_ALLOWED_FIELDS,
                    )
                    if unknown_runtime_broadcast_fields:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_broadcast_policy_additional_properties:"
                            + ",".join(unknown_runtime_broadcast_fields)
                        )
                    runtime_items_dir = str(runtime_broadcast_policy.get("protocol_broadcast_items_dir", "")).strip()
                    runtime_index_file = str(runtime_broadcast_policy.get("protocol_broadcast_index_file", "")).strip()
                    runtime_schema_file = str(runtime_broadcast_policy.get("protocol_broadcast_schema_file", "")).strip()
                    runtime_state_file = str(runtime_broadcast_policy.get("instance_state_file", "")).strip()
                    runtime_receipt_pattern = str(
                        runtime_broadcast_policy.get("instance_receipt_pattern", "")
                    ).strip()
                    runtime_ack_pattern = str(runtime_broadcast_policy.get("instance_ack_pattern", "")).strip()
                    runtime_block_on_critical = bool(
                        runtime_broadcast_policy.get("block_on_critical_unacked", False)
                    )
                    if runtime_broadcast_policy.get("required") is not True:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_required_not_true")
                    if runtime_items_dir != HOST_GATEWAY_BROADCAST_ITEMS_DIR:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_items_dir_mismatch")
                    if runtime_index_file != HOST_GATEWAY_BROADCAST_INDEX_FILE:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_index_file_mismatch")
                    if runtime_schema_file != HOST_GATEWAY_BROADCAST_SCHEMA_FILE:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_schema_file_mismatch")
                    if not runtime_state_file:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_state_file_missing")
                    if not runtime_receipt_pattern:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_receipt_pattern_missing")
                    if not runtime_ack_pattern:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_ack_pattern_missing")
                    contract_items_dir = str(
                        host_gateway_broadcast_policy.get("protocol_broadcast_items_dir", "")
                    ).strip()
                    contract_index_file = str(
                        host_gateway_broadcast_policy.get("protocol_broadcast_index_file", "")
                    ).strip()
                    contract_schema_file = str(
                        host_gateway_broadcast_policy.get("protocol_broadcast_schema_file", "")
                    ).strip()
                    contract_state_file = str(host_gateway_broadcast_policy.get("instance_state_file", "")).strip()
                    contract_receipt_pattern = str(
                        host_gateway_broadcast_policy.get("instance_receipt_pattern", "")
                    ).strip()
                    contract_ack_pattern = str(host_gateway_broadcast_policy.get("instance_ack_pattern", "")).strip()
                    contract_block_on_critical = bool(
                        host_gateway_broadcast_policy.get("block_on_critical_unacked", False)
                    )
                    if contract_items_dir and runtime_items_dir != contract_items_dir:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_items_dir_parity_mismatch")
                    if contract_index_file and runtime_index_file != contract_index_file:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_index_file_parity_mismatch")
                    if contract_schema_file and runtime_schema_file != contract_schema_file:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_schema_file_parity_mismatch")
                    if contract_state_file and runtime_state_file != contract_state_file:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_state_file_mismatch")
                    if contract_receipt_pattern and runtime_receipt_pattern != contract_receipt_pattern:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_receipt_pattern_mismatch")
                    if contract_ack_pattern and runtime_ack_pattern != contract_ack_pattern:
                        host_gateway_issues.append("host_gateway_runtime_contract_broadcast_ack_pattern_mismatch")
                    if runtime_block_on_critical != contract_block_on_critical:
                        host_gateway_issues.append(
                            "host_gateway_runtime_contract_broadcast_block_on_critical_unacked_mismatch"
                        )
                    runtime_protocol_root_raw = str(runtime_gateway_contract.get("protocol_repo_root", "")).strip()
                    if not runtime_protocol_root_raw:
                        host_gateway_issues.append("host_gateway_runtime_contract_protocol_repo_root_missing")
                    else:
                        runtime_protocol_root = Path(runtime_protocol_root_raw).expanduser().resolve()
                        broadcast_items_dir_path = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_ITEMS_DIR).resolve()
                        broadcast_index_path = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_INDEX_FILE).resolve()
                        broadcast_schema_path = (runtime_protocol_root / HOST_GATEWAY_BROADCAST_SCHEMA_FILE).resolve()
                        if not broadcast_items_dir_path.exists() or not broadcast_items_dir_path.is_dir():
                            host_gateway_issues.append("host_gateway_runtime_contract_broadcast_items_dir_missing")
                        if not broadcast_index_path.exists() or not broadcast_index_path.is_file():
                            host_gateway_issues.append("host_gateway_runtime_contract_broadcast_index_file_missing")
                        if not broadcast_schema_path.exists() or not broadcast_schema_path.is_file():
                            host_gateway_issues.append("host_gateway_runtime_contract_broadcast_schema_file_missing")
                        runtime_state_path = _resolve_pack_relative_path(
                            pack_path,
                            runtime_state_file,
                            "runtime/state/broadcast_state.json",
                        )
                        if not runtime_state_path.exists() or not runtime_state_path.is_file():
                            host_gateway_issues.append("host_gateway_runtime_contract_broadcast_state_file_missing")
                if not missing_runtime_fields and not host_gateway_issues:
                    payload["protocol_host_gateway_runtime_contract_status"] = STATUS_PASS_REQUIRED
                elif payload["protocol_host_gateway_runtime_contract_status"] != STATUS_FAIL_REQUIRED:
                    payload["protocol_host_gateway_runtime_contract_status"] = STATUS_FAIL_REQUIRED

    if any("broadcast" in issue for issue in host_gateway_issues):
        payload["protocol_host_gateway_broadcast_policy_status"] = STATUS_FAIL_REQUIRED
    elif payload["protocol_host_gateway_broadcast_policy_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_gateway_broadcast_policy_status"] = STATUS_PASS_REQUIRED

    if any("host_visible_surface" in issue for issue in host_visible_surface_issues + host_gateway_issues):
        payload["protocol_host_visible_surface_contract_status"] = STATUS_FAIL_REQUIRED
    elif payload["protocol_host_visible_surface_contract_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_visible_surface_contract_status"] = STATUS_PASS_REQUIRED

    if any("wrapper_template" in issue for issue in host_gateway_issues):
        payload["protocol_host_gateway_wrapper_template_attestation_status"] = STATUS_FAIL_REQUIRED
    elif payload["protocol_host_gateway_wrapper_template_attestation_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_gateway_wrapper_template_attestation_status"] = STATUS_PASS_REQUIRED

    if any("session_chain_wrapper_semantic_tokens_missing" in issue for issue in host_gateway_issues):
        payload["protocol_host_gateway_session_chain_semantic_status"] = STATUS_FAIL_REQUIRED
    elif payload["protocol_host_gateway_session_chain_semantic_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_gateway_session_chain_semantic_status"] = STATUS_PASS_REQUIRED

    wrapper_template_latest_issue_prefixes = (
        "host_gateway_wrapper_template_canonical_policy_unavailable:",
        "host_gateway_wrapper_template_attestation_not_latest:",
        "host_gateway_runtime_contract_wrapper_template_attestation_not_latest:",
    )
    wrapper_template_latest_issue_exact = {
        "host_gateway_ingress_wrapper_template_sha256_not_latest",
        "host_gateway_egress_wrapper_template_sha256_not_latest",
        "host_gateway_session_chain_wrapper_template_sha256_not_latest",
    }
    wrapper_template_latest_issue_detected = any(
        issue in wrapper_template_latest_issue_exact
        or any(issue.startswith(prefix) for prefix in wrapper_template_latest_issue_prefixes)
        for issue in host_gateway_issues
    )
    if canonical_template_policy_error or wrapper_template_latest_issue_detected:
        payload["protocol_host_gateway_wrapper_template_latest_status"] = STATUS_FAIL_REQUIRED
    else:
        payload["protocol_host_gateway_wrapper_template_latest_status"] = STATUS_PASS_REQUIRED

    if host_visible_surface_issues:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = host_visible_surface_issues
        _emit(payload, json_only=args.json_only)
        return 1

    if host_gateway_issues:
        payload["protocol_host_gateway_contract_status"] = STATUS_FAIL_REQUIRED
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = host_gateway_issues
        _emit(payload, json_only=args.json_only)
        return 1
    payload["protocol_host_gateway_contract_status"] = STATUS_PASS_REQUIRED
    if payload["protocol_host_gateway_runtime_files_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_gateway_runtime_files_status"] = STATUS_PASS_REQUIRED
    if payload["protocol_host_gateway_runtime_contract_status"] == STATUS_SKIPPED_NOT_REQUIRED:
        payload["protocol_host_gateway_runtime_contract_status"] = STATUS_PASS_REQUIRED

    provenance_required = _operation_requires_provenance(
        operation=str(args.operation),
        dispatch_mode=host_gateway_dispatch_mode,
        strict_operations=host_gateway_strict_operations,
        light_operations=host_gateway_light_operations,
        allow_upgrade_only=host_gateway_allow_upgrade_only,
    )
    payload["protocol_unique_entry_receipt_provenance_required"] = provenance_required

    strict_receipt_operation = bool(
        str(args.operation).strip().lower() in host_gateway_strict_operations or strict_operation
    )
    receipt_required_by_cli = bool(args.require_entry_receipt)
    receipt_required_by_contract_scope = bool(receipt_required_by_contract and strict_receipt_operation)
    receipt_required_by_strict_default = bool(strict_receipt_operation)
    receipt_required = bool(
        receipt_required_by_cli
        or receipt_required_by_contract_scope
        or receipt_required_by_strict_default
    )
    payload["protocol_unique_entry_receipt_required"] = receipt_required
    payload["protocol_unique_entry_receipt_required_by_cli_flag"] = receipt_required_by_cli
    payload["protocol_unique_entry_receipt_required_by_contract"] = receipt_required_by_contract_scope
    payload["protocol_unique_entry_receipt_required_by_strict_default"] = (
        receipt_required_by_strict_default
    )
    payload["protocol_unique_entry_receipt_required_strict_operation"] = strict_receipt_operation
    if receipt_required_by_cli:
        payload["protocol_unique_entry_receipt_required_reason"] = "cli_flag"
    elif receipt_required_by_strict_default:
        payload["protocol_unique_entry_receipt_required_reason"] = "strict_operation_default"
    elif receipt_required_by_contract_scope:
        payload["protocol_unique_entry_receipt_required_reason"] = "strict_operation_contract"
    else:
        payload["protocol_unique_entry_receipt_required_reason"] = "not_required"
    tuple_binding_required = bool(
        receipt_required
        and (
            str(args.operation).strip().lower() in host_gateway_strict_operations
            or strict_operation
        )
    )
    tuple_binding_expected_fields: list[str] = ["operation", "run_id", "actor_id", "session_id"]
    tuple_binding_missing_fields: list[str] = []
    if tuple_binding_required:
        if not run_id:
            tuple_binding_missing_fields.append("run_id")
        if not actor_id:
            tuple_binding_missing_fields.append("actor_id")
        if not session_id:
            tuple_binding_missing_fields.append("session_id")
    payload["protocol_unique_entry_receipt_tuple_binding_required"] = tuple_binding_required
    payload["protocol_unique_entry_receipt_tuple_binding_expected_fields"] = list(tuple_binding_expected_fields)
    payload["protocol_unique_entry_receipt_tuple_binding_missing_fields"] = list(tuple_binding_missing_fields)
    if tuple_binding_required and tuple_binding_missing_fields:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
        payload["protocol_unique_entry_receipt_tuple_context_status"] = STATUS_FAIL_REQUIRED
        payload["protocol_unique_entry_receipt_tuple_context_required_fields"] = list(tuple_binding_expected_fields)
        payload["protocol_unique_entry_receipt_tuple_context_mismatch_fields"] = list(tuple_binding_missing_fields)
        payload["protocol_unique_entry_receipt_tuple_context_next_action"] = (
            "supply_actor_id_session_id_run_id_and_revalidate_entry_receipt"
        )
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = [
            "entry_receipt_tuple_binding_incomplete:" + ",".join(tuple_binding_missing_fields)
        ]
        _emit(payload, json_only=args.json_only)
        return 1

    if receipt_required:
        receipt_candidates = _collect_entry_receipt_candidates(
            pack_path=pack_path,
            explicit_path=str(args.entry_receipt or ""),
            operation=str(args.operation),
        )
        receipt_path, selector_payload, selector_issues = _select_entry_receipt_candidate(
            candidates=receipt_candidates,
            expected_operation=str(args.operation).strip().lower(),
            expected_run_id=run_id,
            expected_actor_id=actor_id,
            expected_session_id=session_id,
            expected_catalog_path=str(catalog_path),
        )
        payload["protocol_unique_entry_receipt_selector_policy_id"] = str(
            selector_payload.get("selector_policy_id", "")
        ).strip()
        payload["protocol_unique_entry_receipt_selector_precedence"] = list(
            selector_payload.get("selector_precedence", []) or []
        )
        payload["protocol_unique_entry_receipt_selector_source_fields"] = list(
            selector_payload.get("selector_source_fields", []) or []
        )
        payload["protocol_unique_entry_receipt_selector_candidate_count"] = int(
            selector_payload.get("candidate_count", 0) or 0
        )
        payload["protocol_unique_entry_receipt_selector_selected_source"] = str(
            selector_payload.get("selected_source", "")
        ).strip()
        payload["protocol_unique_entry_receipt_selector_selected_sort_key"] = list(
            selector_payload.get("selected_sort_key", []) or []
        )
        payload["protocol_unique_entry_receipt_selector_selected_reason_tokens"] = list(
            selector_payload.get("selected_reason_tokens", []) or []
        )
        payload["protocol_unique_entry_receipt_selector_candidate_preview"] = list(
            selector_payload.get("candidate_preview", []) or []
        )
        if receipt_path is None:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = (
                list(selector_issues)
                + [
                    "entry_receipt_missing",
                    "entry_receipt_selector_no_eligible_candidate",
                ]
            )
            _emit(payload, json_only=args.json_only)
            return 1
        payload["protocol_unique_entry_receipt_path"] = str(receipt_path)
        if selector_issues:
            payload.setdefault("stale_reasons", [])
            payload["stale_reasons"] = list(payload.get("stale_reasons") or []) + list(selector_issues)
        try:
            receipt = _load_receipt(receipt_path)
        except Exception as exc:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = [f"entry_receipt_invalid:{exc}"]
            _emit(payload, json_only=args.json_only)
            return 1

        receipt_bundle_key = str(receipt.get("bundle_key", "")).strip()
        receipt_identity_id = str(receipt.get("identity_id", "")).strip()
        receipt_operation, receipt_operation_field = _first_receipt_value(
            receipt,
            ENTRY_RECEIPT_OPERATION_FIELDS,
            lower=True,
        )
        receipt_operation_bridge_allowed = _operation_bridge_match(
            str(args.operation).strip().lower(),
            receipt_operation,
        )
        receipt_operation_bridge_applied = bool(
            receipt_operation_bridge_allowed
            and receipt_operation != str(args.operation).strip().lower()
        )
        receipt_run_id, receipt_run_id_field = _first_receipt_value(receipt, ENTRY_RECEIPT_RUN_ID_FIELDS)
        receipt_actor_id, receipt_actor_id_field = _first_receipt_value(receipt, ENTRY_RECEIPT_ACTOR_ID_FIELDS)
        receipt_session_id, receipt_session_id_field = _first_receipt_value(receipt, ENTRY_RECEIPT_SESSION_ID_FIELDS)
        receipt_bundle_status = str(receipt.get("bundle_status", "")).strip().upper()
        receipt_surface_label = str(receipt.get("surface_label", "")).strip()
        receipt_wrapper_surface_status = str(receipt.get("wrapper_surface_status", "")).strip().upper()
        receipt_wrapper_dispatch_status = str(receipt.get("wrapper_dispatch_token_status", "")).strip().upper()
        receipt_wrapper_dispatch_required = _as_bool(receipt.get("wrapper_dispatch_required"))
        receipt_wrapper_proof_required = _as_bool(receipt.get("wrapper_dispatch_proof_required"))
        receipt_wrapper_proof_status = str(receipt.get("wrapper_dispatch_proof_status", "")).strip().upper()
        receipt_wrapper_parent_required = _as_bool(receipt.get("wrapper_parent_attestation_required"))
        receipt_wrapper_parent_status = str(receipt.get("wrapper_parent_attestation_status", "")).strip().upper()
        receipt_wrapper_parent_expected_path = str(
            receipt.get("wrapper_parent_attestation_expected_path", "")
        ).strip()
        receipt_payload_epoch, receipt_payload_field = _extract_receipt_payload_timestamp_epoch(receipt)
        payload["protocol_unique_entry_receipt_payload_timestamp_epoch"] = receipt_payload_epoch
        payload["protocol_unique_entry_receipt_payload_timestamp_field"] = receipt_payload_field
        receipt_age_seconds = -1
        if tuple_binding_required and entry_receipt_max_age_seconds > 0:
            now_epoch = int(time.time())
            receipt_file_age_seconds = -1
            try:
                receipt_file_age_seconds = max(0, int(now_epoch - receipt_path.stat().st_mtime))
            except Exception:
                receipt_file_age_seconds = -1
            payload["protocol_unique_entry_receipt_file_age_seconds"] = receipt_file_age_seconds

            receipt_payload_age_seconds = -1
            if receipt_payload_epoch > 0:
                if receipt_payload_epoch > now_epoch + 30:
                    payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
                    payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
                    payload["error_code"] = ERR_CONTRACT_INVALID
                    payload["stale_reasons"] = [
                        "entry_receipt_payload_timestamp_in_future:"
                        f"payload_epoch={receipt_payload_epoch}:now_epoch={now_epoch}"
                    ]
                    _emit(payload, json_only=args.json_only)
                    return 1
                receipt_payload_age_seconds = max(0, now_epoch - receipt_payload_epoch)
            payload["protocol_unique_entry_receipt_payload_age_seconds"] = receipt_payload_age_seconds

            available_ages = [x for x in [receipt_file_age_seconds, receipt_payload_age_seconds] if x >= 0]
            if available_ages:
                receipt_age_seconds = max(available_ages)
                payload["protocol_unique_entry_receipt_age_source"] = "max(payload_timestamp,file_mtime)"
            else:
                receipt_age_seconds = -1
                payload["protocol_unique_entry_receipt_age_source"] = "unavailable"
            payload["protocol_unique_entry_receipt_age_seconds"] = receipt_age_seconds
            if receipt_age_seconds < 0:
                payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
                payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
                payload["error_code"] = ERR_CONTRACT_INVALID
                payload["stale_reasons"] = ["entry_receipt_age_unavailable"]
                _emit(payload, json_only=args.json_only)
                return 1
            if receipt_age_seconds > entry_receipt_max_age_seconds:
                payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
                payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
                payload["error_code"] = ERR_CONTRACT_INVALID
                payload["stale_reasons"] = [
                    "entry_receipt_stale:"
                    f"age_seconds={receipt_age_seconds}:max_age_seconds={entry_receipt_max_age_seconds}:"
                    f"payload_age_seconds={payload.get('protocol_unique_entry_receipt_payload_age_seconds', -1)}:"
                    f"file_age_seconds={payload.get('protocol_unique_entry_receipt_file_age_seconds', -1)}"
                ]
                _emit(payload, json_only=args.json_only)
                return 1
        payload["protocol_unique_entry_receipt_bundle_key"] = receipt_bundle_key
        payload["protocol_unique_entry_receipt_run_id"] = receipt_run_id
        payload["protocol_unique_entry_receipt_run_id_field"] = receipt_run_id_field
        payload["protocol_unique_entry_receipt_actor_id"] = receipt_actor_id
        payload["protocol_unique_entry_receipt_actor_id_field"] = receipt_actor_id_field
        payload["protocol_unique_entry_receipt_session_id"] = receipt_session_id
        payload["protocol_unique_entry_receipt_session_id_field"] = receipt_session_id_field
        payload["protocol_unique_entry_receipt_operation"] = receipt_operation
        payload["protocol_unique_entry_receipt_operation_field"] = receipt_operation_field
        payload["protocol_unique_entry_receipt_operation_bridge_allowed"] = (
            receipt_operation_bridge_allowed
        )
        payload["protocol_unique_entry_receipt_operation_bridge_applied"] = (
            receipt_operation_bridge_applied
        )
        tuple_context_expected: dict[str, str] = {
            "operation": str(args.operation).strip().lower(),
        }
        if run_id:
            tuple_context_expected["run_id"] = run_id
        if actor_id:
            tuple_context_expected["actor_id"] = actor_id
        if session_id:
            tuple_context_expected["session_id"] = session_id
        tuple_context_observed: dict[str, str] = {
            "operation": receipt_operation,
            "run_id": receipt_run_id,
            "actor_id": receipt_actor_id,
            "session_id": receipt_session_id,
        }
        payload["protocol_unique_entry_receipt_tuple_context_required_fields"] = sorted(tuple_context_expected)
        payload["protocol_unique_entry_receipt_tuple_context_expected"] = tuple_context_expected
        payload["protocol_unique_entry_receipt_tuple_context_observed"] = tuple_context_observed
        payload["protocol_unique_entry_receipt_surface_label"] = receipt_surface_label
        payload["protocol_unique_entry_receipt_wrapper_surface_status"] = receipt_wrapper_surface_status
        payload["protocol_unique_entry_receipt_wrapper_dispatch_token_status"] = receipt_wrapper_dispatch_status
        payload["protocol_unique_entry_receipt_wrapper_dispatch_required"] = receipt_wrapper_dispatch_required
        payload["protocol_unique_entry_receipt_wrapper_proof_status"] = receipt_wrapper_proof_status
        payload["protocol_unique_entry_receipt_wrapper_proof_required"] = receipt_wrapper_proof_required
        payload["protocol_unique_entry_receipt_wrapper_parent_attestation_status"] = (
            receipt_wrapper_parent_status
        )
        payload["protocol_unique_entry_receipt_wrapper_parent_attestation_required"] = (
            receipt_wrapper_parent_required
        )
        payload["protocol_unique_entry_receipt_wrapper_parent_attestation_expected_path"] = (
            receipt_wrapper_parent_expected_path
        )
        receipt_wrapper_parent_expected_path_resolved = ""
        if receipt_wrapper_parent_expected_path:
            receipt_wrapper_parent_expected_path_resolved = str(
                _resolve_pack_relative_path(
                    pack_path,
                    receipt_wrapper_parent_expected_path,
                    HOST_GATEWAY_EXPECTED_INGRESS_REL,
                )
            )
        payload["protocol_unique_entry_receipt_wrapper_parent_attestation_expected_path_resolved"] = (
            receipt_wrapper_parent_expected_path_resolved
        )

        receipt_issues: list[str] = []
        if receipt_bundle_key != EXPECTED_BUNDLE_KEY:
            receipt_issues.append("entry_receipt_bundle_key_mismatch")
        if receipt_identity_id != str(args.identity_id).strip():
            receipt_issues.append("entry_receipt_identity_mismatch")
        if (
            receipt_operation != str(args.operation).strip().lower()
            and not receipt_operation_bridge_allowed
        ):
            receipt_issues.append("entry_receipt_operation_mismatch")
        if receipt_bundle_status != STATUS_PASS_REQUIRED:
            receipt_issues.append("entry_receipt_bundle_status_not_pass")
        if run_id and receipt_run_id != run_id:
            receipt_issues.append("entry_receipt_run_id_mismatch")
        if actor_id and receipt_actor_id != actor_id:
            receipt_issues.append("entry_receipt_actor_id_mismatch")
        if session_id and receipt_session_id != session_id:
            receipt_issues.append("entry_receipt_session_id_mismatch")
        if provenance_required and receipt_surface_label != receipt_required_surface_label:
            receipt_issues.append(
                "entry_receipt_surface_label_mismatch:"
                f"{receipt_surface_label}:expected={receipt_required_surface_label}"
            )
        if provenance_required and receipt_wrapper_surface_status != receipt_required_wrapper_surface_status:
            receipt_issues.append("entry_receipt_wrapper_surface_status_not_pass_required")
        if provenance_required and receipt_wrapper_dispatch_status != receipt_required_wrapper_dispatch_status:
            receipt_issues.append("entry_receipt_wrapper_dispatch_status_not_pass_required")
        if provenance_required and receipt_wrapper_dispatch_required is not True:
            receipt_issues.append("entry_receipt_wrapper_dispatch_required_not_true")
        if provenance_required and receipt_wrapper_proof_required is not True:
            receipt_issues.append("entry_receipt_wrapper_proof_required_not_true")
        if provenance_required and receipt_wrapper_proof_status != STATUS_PASS_REQUIRED:
            receipt_issues.append("entry_receipt_wrapper_proof_status_not_pass_required")
        if provenance_required and receipt_wrapper_parent_required is not True:
            receipt_issues.append("entry_receipt_wrapper_parent_attestation_required_not_true")
        if provenance_required and receipt_wrapper_parent_status != STATUS_PASS_REQUIRED:
            receipt_issues.append("entry_receipt_wrapper_parent_attestation_status_not_pass_required")
        if provenance_required and not receipt_wrapper_parent_expected_path:
            receipt_issues.append("entry_receipt_wrapper_parent_attestation_expected_path_missing")
        expected_ingress_wrapper_path = str(payload.get("protocol_host_gateway_ingress_wrapper_path", "")).strip()
        if (
            provenance_required
            and expected_ingress_wrapper_path
            and receipt_wrapper_parent_expected_path
            and receipt_wrapper_parent_expected_path_resolved
            and Path(receipt_wrapper_parent_expected_path_resolved).expanduser().resolve()
            != Path(expected_ingress_wrapper_path).expanduser().resolve()
        ):
            receipt_issues.append("entry_receipt_wrapper_parent_attestation_expected_path_mismatch")
        missing_fields: list[str] = []
        for field in sorted(entry_receipt_required_fields):
            if field in receipt:
                continue
            if field == "run_id_binding" and receipt_run_id:
                continue
            if field == "actor_id" and receipt_actor_id:
                continue
            if field == "session_id" and receipt_session_id:
                continue
            if field == "operation" and receipt_operation:
                continue
            missing_fields.append(field)
        if missing_fields:
            receipt_issues.append("entry_receipt_required_fields_missing:" + ",".join(missing_fields))

        tuple_context_issue_fields: set[str] = set()
        for token in receipt_issues:
            if token == "entry_receipt_operation_mismatch":
                tuple_context_issue_fields.add("operation")
                continue
            if token == "entry_receipt_run_id_mismatch":
                tuple_context_issue_fields.add("run_id")
                continue
            if token == "entry_receipt_actor_id_mismatch":
                tuple_context_issue_fields.add("actor_id")
                continue
            if token == "entry_receipt_session_id_mismatch":
                tuple_context_issue_fields.add("session_id")
                continue
            if token.startswith("entry_receipt_required_fields_missing:"):
                raw = token.split(":", 1)[1]
                for field in [x.strip() for x in raw.split(",") if x.strip()]:
                    if field in {"operation", "run_id_binding", "run_id"}:
                        tuple_context_issue_fields.add("run_id" if field != "operation" else "operation")
                    elif field in {"actor_id", "session_id"}:
                        tuple_context_issue_fields.add(field)
        tuple_context_required_fields = set(tuple_context_expected)
        if tuple_context_required_fields:
            if tuple_context_issue_fields:
                payload["protocol_unique_entry_receipt_tuple_context_status"] = STATUS_FAIL_REQUIRED
                payload["protocol_unique_entry_receipt_tuple_context_next_action"] = (
                    "replay_wrapper_chain_with_bound_actor_session_tuple_and_revalidate_entry_receipt"
                )
            else:
                payload["protocol_unique_entry_receipt_tuple_context_status"] = STATUS_PASS_REQUIRED
            payload["protocol_unique_entry_receipt_tuple_context_mismatch_fields"] = sorted(
                tuple_context_issue_fields
            )
        else:
            payload["protocol_unique_entry_receipt_tuple_context_status"] = STATUS_SKIPPED_NOT_REQUIRED
            payload["protocol_unique_entry_receipt_tuple_context_mismatch_fields"] = []

        if receipt_issues:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = receipt_issues
            tuple_related_markers = {
                "entry_receipt_operation_mismatch",
                "entry_receipt_run_id_mismatch",
                "entry_receipt_actor_id_mismatch",
                "entry_receipt_session_id_mismatch",
                "entry_receipt_bundle_status_not_pass",
            }
            tuple_primary_detected = any(
                token in {
                    "entry_receipt_operation_mismatch",
                    "entry_receipt_run_id_mismatch",
                    "entry_receipt_actor_id_mismatch",
                    "entry_receipt_session_id_mismatch",
                }
                or token.startswith("entry_receipt_required_fields_missing:")
                for token in receipt_issues
            )
            tuple_only_failure = all(
                token in tuple_related_markers or token.startswith("entry_receipt_required_fields_missing:")
                for token in receipt_issues
            )
            payload["protocol_unique_entry_receipt_tuple_context_only_failure"] = bool(
                tuple_only_failure
                and tuple_primary_detected
                and payload.get("protocol_unique_entry_receipt_tuple_context_mismatch_fields")
            )
            _emit(payload, json_only=args.json_only)
            return 1

        payload["protocol_unique_entry_receipt_status"] = STATUS_PASS_REQUIRED
        if payload.get("protocol_unique_entry_receipt_tuple_context_required_fields"):
            payload["protocol_unique_entry_receipt_tuple_context_status"] = STATUS_PASS_REQUIRED
        payload["protocol_unique_entry_receipt_tuple_context_only_failure"] = False

    payload["protocol_unique_entry_gate_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
