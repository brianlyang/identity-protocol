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
HOST_GATEWAY_DEFAULT_SIGNING_KEY = "runtime/state/protocol_gateway_signing_key.txt"

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
)
HOST_GATEWAY_STRICT_GATE_PROFILE = "strict_full"
HOST_GATEWAY_LIGHT_GATE_PROFILE = "inspection_targeted"

# Signer defaults.
HOST_GATEWAY_SIGNER_MODE = "runtime_env_secret"
HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX = "IDENTITY_PROTOCOL_GATEWAY_SIGNING_SECRET_"
HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH = True
HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS = 300
HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS = 300

# Broadcast governance paths.
HOST_GATEWAY_BROADCAST_ITEMS_DIR = "identity/protocol/broadcast/items"
HOST_GATEWAY_BROADCAST_INDEX_FILE = "identity/protocol/broadcast/index.json"
HOST_GATEWAY_BROADCAST_SCHEMA_FILE = "identity/protocol/broadcast/schema/broadcast-item.v1.json"
HOST_GATEWAY_BROADCAST_STATE_FILE = "runtime/state/broadcast_state.json"
HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN = "runtime/reports/broadcast/broadcast-receipt-*.json"
HOST_GATEWAY_BROADCAST_ACK_PATTERN = "runtime/reports/broadcast/broadcast-ack-*.json"
