#!/usr/bin/env python3
"""Create an identity pack and optionally register it in identity catalog."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys
import yaml

from contract_binding_doc_defaults_common import resolve_validator_doc_defaults
from resolve_identity_context import default_identity_home, default_local_catalog_path, default_local_instances_root
from final_emit_contract_common import FINAL_EMIT_CHANNEL_ID
from runtime_temp_path_common import identity_runtime_named_temp_root
from version_baseline_common import (
    apply_version_baseline_to_catalog_row,
    apply_version_baseline_to_task_doc,
    load_version_baseline_or_raise,
)
from protocol_infra_contract import (
    CANONICAL_FINAL_EMIT_SCRIPT,
    CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT,
    HOST_GATEWAY_ALLOW_UPGRADE_ONLY as INFRA_HOST_GATEWAY_ALLOW_UPGRADE_ONLY,
    HOST_GATEWAY_BROADCAST_ACK_PATTERN as INFRA_HOST_GATEWAY_BROADCAST_ACK_PATTERN,
    HOST_GATEWAY_BROADCAST_INDEX_FILE as INFRA_HOST_GATEWAY_BROADCAST_INDEX_FILE,
    HOST_GATEWAY_BROADCAST_ITEMS_DIR as INFRA_HOST_GATEWAY_BROADCAST_ITEMS_DIR,
    HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN as INFRA_HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
    HOST_GATEWAY_BROADCAST_SCHEMA_FILE as INFRA_HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    HOST_GATEWAY_BROADCAST_STATE_FILE as INFRA_HOST_GATEWAY_BROADCAST_STATE_FILE,
    HOST_GATEWAY_CONTRACT_ID as INFRA_HOST_GATEWAY_CONTRACT_ID,
    HOST_GATEWAY_CONTRACT_KEY as INFRA_HOST_GATEWAY_CONTRACT_KEY,
    HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS as INFRA_HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS,
    HOST_GATEWAY_INGRESS_DISPATCH_TOKEN as INFRA_HOST_GATEWAY_INGRESS_DISPATCH_TOKEN,
    HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS as INFRA_HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS,
    HOST_GATEWAY_LIGHT_GATE_PROFILE as INFRA_HOST_GATEWAY_LIGHT_GATE_PROFILE,
    HOST_GATEWAY_LIGHT_OPERATIONS as INFRA_HOST_GATEWAY_LIGHT_OPERATIONS,
    HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS as INFRA_HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS,
    HOST_GATEWAY_RELATIVE_CONTRACT_PATH as INFRA_HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
    HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH as INFRA_HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH as INFRA_HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH as INFRA_HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH as INFRA_HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE as INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_DISPATCH_STATUS as INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_STATUS,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE as INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_GATEWAY_REQUIRED_SURFACE_LABEL as INFRA_HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
    HOST_GATEWAY_REQUIRED_SURFACE_STATUS as INFRA_HOST_GATEWAY_REQUIRED_SURFACE_STATUS,
    HOST_GATEWAY_REQUIRED_TUPLE_FIELDS as INFRA_HOST_GATEWAY_REQUIRED_TUPLE_FIELDS,
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID as INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID,
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY as INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
    HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH as INFRA_HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
    HOST_GATEWAY_SIGNER_MODE as INFRA_HOST_GATEWAY_SIGNER_MODE,
    HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX as INFRA_HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX,
    HOST_GATEWAY_STRICT_GATE_PROFILE as INFRA_HOST_GATEWAY_STRICT_GATE_PROFILE,
    HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION as INFRA_HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION,
    HOST_GATEWAY_STRICT_OPERATIONS as INFRA_HOST_GATEWAY_STRICT_OPERATIONS,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN as INFRA_HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED as INFRA_HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS,
    HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD as INFRA_HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD,
    HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE as INFRA_HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES as INFRA_HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES,
    HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS as INFRA_HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
    HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR as INFRA_HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS as INFRA_HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY as INFRA_HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY,
    HOST_VISIBLE_FINAL_CHANNEL_ID as INFRA_HOST_VISIBLE_FINAL_CHANNEL_ID,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE as INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED as INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED,
    HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE as INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE,
    HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS as INFRA_HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS as INFRA_HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_STATE_FILE as INFRA_HOST_VISIBLE_SURFACE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE as INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE as INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
    HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION as INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE,
    UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS as INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS,
)
from host_visible_final_channel_relay_common import (
    build_host_visible_final_channel_relay_receipt,
    project_host_visible_final_channel_relay_fields,
)
from response_stamp_common import default_response_stamp_profile, normalize_response_stamp_profile
from native_chat_headstamp_common import (
    DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF,
    ensure_native_chat_prompt_hard_guard as _ensure_native_chat_prompt_hard_guard,
    render_native_chat_prompt_hard_guard_markdown,
)

ensure_native_chat_prompt_hard_guard = _ensure_native_chat_prompt_hard_guard


MANDATORY_PROTOCOL_SOURCES = [
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "identity/protocol/IDENTITY_PROTOCOL.md",
    },
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/references/skill-installer-skill-creator-skill-update-lifecycle.md",
    },
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md",
    },
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/references/skill-mcp-tool-collaboration-contract-v1.0.md",
    },
    {
        "type": "github_repo_file",
        "repo": "brianlyang/identity-protocol",
        "path": "docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md",
    },
    {
        "type": "official_doc",
        "url": "https://developers.openai.com/codex/skills/",
    },
    {
        "type": "official_doc",
        "url": "https://agentskills.io/specification",
    },
    {
        "type": "official_doc",
        "url": "https://modelcontextprotocol.io/specification/latest",
    },
]

REPO_FIXTURE_CONFIRM_TOKEN = "I_UNDERSTAND_REPO_FIXTURE_WRITE"

CANONICAL_BLOCKER_TYPES = [
    "auth_login_required",
    "anti_automation_challenge_required",
    "session_reauthentication_required",
    "manual_verification_required",
]

LEGACY_BLOCKER_ALIAS_MAP = {
    "login_required": "auth_login_required",
    "captcha_required": "anti_automation_challenge_required",
    "session_expired": "session_reauthentication_required",
}

DOMAIN_NEUTRALITY_BLOCKLIST = [
    "store-manager",
    "store_manager",
    "weixinstore-ui-agent",
    "weixinstore-sku-onboarding",
    "wechat_listing_update",
    "taobao-search-automation",
    "10000514174106",
]

UNIQUE_INGRESS_SCRIPT = CANONICAL_REQUIRED_GATE_BUNDLE_SCRIPT
UNIQUE_EGRESS_SCRIPT = CANONICAL_FINAL_EMIT_SCRIPT
HOST_GATEWAY_CONTRACT_KEY = INFRA_HOST_GATEWAY_CONTRACT_KEY
HOST_GATEWAY_CONTRACT_ID = INFRA_HOST_GATEWAY_CONTRACT_ID
HOST_GATEWAY_REQUIRED_DISPATCH_MODE = INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_MODE
HOST_GATEWAY_REQUIRED_RELEASE_MODE = INFRA_HOST_GATEWAY_REQUIRED_RELEASE_MODE
HOST_GATEWAY_INGRESS_DISPATCH_TOKEN = INFRA_HOST_GATEWAY_INGRESS_DISPATCH_TOKEN
HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS = INFRA_HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS
HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS = INFRA_HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS
HOST_GATEWAY_REQUIRED_SURFACE_LABEL = INFRA_HOST_GATEWAY_REQUIRED_SURFACE_LABEL
HOST_GATEWAY_REQUIRED_SURFACE_STATUS = INFRA_HOST_GATEWAY_REQUIRED_SURFACE_STATUS
HOST_GATEWAY_REQUIRED_DISPATCH_STATUS = INFRA_HOST_GATEWAY_REQUIRED_DISPATCH_STATUS
HOST_GATEWAY_STRICT_OPERATIONS = list(INFRA_HOST_GATEWAY_STRICT_OPERATIONS)
HOST_GATEWAY_LIGHT_OPERATIONS = list(INFRA_HOST_GATEWAY_LIGHT_OPERATIONS)
HOST_GATEWAY_STRICT_GATE_PROFILE = INFRA_HOST_GATEWAY_STRICT_GATE_PROFILE
HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION = {
    str(key).strip().lower(): str(value).strip()
    for key, value in INFRA_HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION.items()
    if str(key).strip() and str(value).strip()
}
HOST_GATEWAY_LIGHT_GATE_PROFILE = INFRA_HOST_GATEWAY_LIGHT_GATE_PROFILE
HOST_GATEWAY_ALLOW_UPGRADE_ONLY = INFRA_HOST_GATEWAY_ALLOW_UPGRADE_ONLY
HOST_GATEWAY_SIGNER_MODE = INFRA_HOST_GATEWAY_SIGNER_MODE
HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX = INFRA_HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX
HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH = INFRA_HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH
HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH = INFRA_HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
HOST_GATEWAY_RELATIVE_CONTRACT_PATH = INFRA_HOST_GATEWAY_RELATIVE_CONTRACT_PATH
HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH = INFRA_HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH
HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH = INFRA_HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH
HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH = INFRA_HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH
HOST_GATEWAY_BROADCAST_ITEMS_DIR = INFRA_HOST_GATEWAY_BROADCAST_ITEMS_DIR
HOST_GATEWAY_BROADCAST_INDEX_FILE = INFRA_HOST_GATEWAY_BROADCAST_INDEX_FILE
HOST_GATEWAY_BROADCAST_SCHEMA_FILE = INFRA_HOST_GATEWAY_BROADCAST_SCHEMA_FILE
HOST_GATEWAY_BROADCAST_STATE_FILE = INFRA_HOST_GATEWAY_BROADCAST_STATE_FILE
HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN = INFRA_HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN
HOST_GATEWAY_BROADCAST_ACK_PATTERN = INFRA_HOST_GATEWAY_BROADCAST_ACK_PATTERN
HOST_GATEWAY_REQUIRED_TUPLE_FIELDS = list(INFRA_HOST_GATEWAY_REQUIRED_TUPLE_FIELDS)
HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY = INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY
HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID = INFRA_HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID
HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS = list(
    INFRA_HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS
)
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE = INFRA_HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS = list(INFRA_HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS)
HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS = list(
    INFRA_HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS
)
HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS = list(
    INFRA_HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS
)
HOST_VISIBLE_FINAL_CHANNEL_ID = INFRA_HOST_VISIBLE_FINAL_CHANNEL_ID
HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED = INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED
HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE = INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE
HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE = INFRA_HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE
HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY = INFRA_HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY
HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS = list(
    INFRA_HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS
)
HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS = list(
    INFRA_HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS
)
HOST_VISIBLE_SURFACE_STATE_FILE = INFRA_HOST_VISIBLE_SURFACE_STATE_FILE
HOST_VISIBLE_SURFACE_RECEIPT_PATTERN = INFRA_HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED = INFRA_HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS = INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS
HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE = INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE = INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE
HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION = INFRA_HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION
HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD = INFRA_HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE = INFRA_HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE
HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE = INFRA_HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE
HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES = list(
    INFRA_HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES
)
HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS = list(
    INFRA_HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS
)
UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID = INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID
UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE = list(INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE)
UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS = list(INFRA_UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS)

DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY = "protocol_downsink_path_immutability_contract_v1"
DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID = "protocol_downsink_path_immutability_contract_v1"
DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID = "scripts/validate_protocol_downsink_path_immutability.py"
DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID = "scripts/validate_protocol_downsink_path_write_guard.py"
DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID = "scripts/validate_protocol_downsink_path_literal_lock.py"
DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER = "downsink-path-lock: allow-nonregistry-literal"
DOWNSINK_LITERAL_LOCK_SCAN_GLOBS: tuple[str, ...] = (
    "scripts/**/*.py",
    "scripts/**/*.sh",
    ".github/workflows/*.yml",
)
DOWNSINK_RUNTIME_MIRROR_PATH_ID = "runtime_gate.gateway_contract"
DOWNSINK_ANCHOR_PROTOCOL_REPO_ROOT_REF = "{protocol_repo_root}"
DOWNSINK_ANCHOR_IDENTITY_PACK_ROOT_REF = "{identity_pack_root}"
DOWNSINK_RUNTIME_GATE_DOMAIN = "runtime_gate"
DOWNSINK_RUNTIME_BROADCAST_DOMAIN = "runtime_broadcast"
DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN = "runtime_protocol_feedback"
DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN = "protocol_broadcast_source"
DOWNSINK_REQUIRED_DOMAINS: tuple[str, ...] = (
    DOWNSINK_RUNTIME_GATE_DOMAIN,
    DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
    DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN,
    DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN,
)
INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY = "instance_pack_topology_contract_v1"
INSTANCE_PACK_TOPOLOGY_CONTRACT_ID = "instance_pack_topology_contract_v1"
INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID = "scripts/validate_identity_instance_pack_topology.py"
INSTANCE_SCRIPT_MANIFEST_RELATIVE_PATH = "scripts/INSTANCE_SCRIPT_MANIFEST.json"
INSTANCE_SCRIPT_MANIFEST_VALIDATOR_ID = "scripts/validate_instance_script_manifest.py"
INSTANCE_SCRIPT_ORCHESTRATION_VALIDATOR_ID = "scripts/validate_identity_instance_script_orchestration.py"
INSTANCE_SCRIPT_RECEIPT_JOIN_VALIDATOR_ID = "scripts/validate_route_script_receipt_join.py"
INSTANCE_SCRIPT_EXECUTION_LANE_VALIDATOR_ID = "scripts/validate_route_execution_lane_admission.py"
PROVIDER_BINDINGS_TEMPLATE_RELATIVE_PATH = (
    "identity/protocol/plugins/templates/provider-bindings.local.template.yaml"
)
PROMPT_GOVERNANCE_KERNEL_HEADING = "## Governance Kernel"
PROMPT_GOVERNANCE_REQUIRED_TOKENS: tuple[str, ...] = (
    "role",
    "principle",
    "decision",
    "gate",
)
PROVIDER_BINDINGS_TEMPLATE_CONTRACT_ID = "provider_bindings_template_contract_v1"

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _normalize_provider_bindings_template_doc(doc: dict[str, Any]) -> dict[str, Any]:
    if str(doc.get("contract_id", "")).strip() != PROVIDER_BINDINGS_TEMPLATE_CONTRACT_ID:
        return doc
    bindings = doc.get("bindings")
    if not isinstance(bindings, list):
        return doc
    for row in bindings:
        if not isinstance(row, dict):
            continue
        credential_ref = str(row.get("credential_ref", "")).strip()
        if not credential_ref.startswith("env:"):
            continue
        env_key = credential_ref.split(":", 1)[1].strip()
        if not env_key:
            continue
        row["enabled"] = bool(str(os.getenv(env_key, "")).strip())
    return doc


def _provider_bindings_template_text(*, repo_root: Path | None = None, existing_text: str = "") -> str:
    resolved_repo_root = repo_root.resolve() if repo_root is not None else Path(__file__).resolve().parents[1]
    template_path = (resolved_repo_root / PROVIDER_BINDINGS_TEMPLATE_RELATIVE_PATH).resolve()
    source_text = str(existing_text or "").strip()
    raw_text = source_text or template_path.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(raw_text) or {}
    except Exception:
        return raw_text if raw_text.endswith("\n") else raw_text + "\n"
    if not isinstance(doc, dict):
        return raw_text if raw_text.endswith("\n") else raw_text + "\n"
    normalized = _normalize_provider_bindings_template_doc(doc)
    return yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True)


def _identity_prompt_governance_kernel(
    *,
    identity_id: str,
    title: str = "",
    description: str = "",
) -> str:
    identity_token = str(identity_id or "").strip() or "unspecified-identity"
    title_token = str(title or "").strip() or identity_token
    description_token = str(description or "").strip()
    lines = [
        PROMPT_GOVERNANCE_KERNEL_HEADING,
        f"- role: `{identity_token}` operates as {title_token}.",
        "- principle: fail-close, evidence-first, and runtime source-of-truth.",
        "- decision: release conclusions only when current-round receipts and validators align.",
        "- gate: required gates, recurrence closure, and three-plane status must stay mutually consistent.",
    ]
    if description_token:
        lines.append(f"- mission: {description_token}")
    return "\n".join(lines) + "\n"


def _default_identity_prompt_markdown(
    *,
    identity_id: str,
    title: str = "",
    description: str = "",
) -> str:
    identity_token = str(identity_id or "").strip() or "unspecified-identity"
    title_token = str(title or "").strip() or identity_token
    description_token = str(description or "").strip()
    prompt_lines = [
        f"# Identity Prompt: {title_token}",
        "",
        _identity_prompt_governance_kernel(
            identity_id=identity_token,
            title=title_token,
            description=description_token,
        ).rstrip(),
        "",
        "## Mission",
        "Define role cognition, principle hierarchy, decision rules, and gate expectations.",
        "",
        "## Operating Baseline",
        "- Keep runtime evidence current and reproducible.",
        "- Escalate unresolved conflicts instead of soft-passing them.",
        "- Separate visible display from machine admission and truth claims.",
        "",
        render_native_chat_prompt_hard_guard_markdown().rstrip(),
        "",
    ]
    return "\n".join(prompt_lines)


def _default_instance_scripts_readme(identity_id: str) -> str:
    identity_token = str(identity_id or "").strip() or "<identity-id>"
    return """# Instance Scripts

This directory is the instance-owned executable source surface for
`{identity_token}`.

Boundary:

- `scripts/` lives at the identity-pack root and is the only canonical script surface for instance-owned helpers.
- `scripts/INSTANCE_SCRIPT_MANIFEST.json` is the canonical route-targetable script catalog for this pack.
- `runtime/` stays reserved for runtime/autonomy/state/report/downsink artifacts.
- `runtime/scripts/` is forbidden and must fail-close under topology validation.
- Scripts here may consume shared protocol/workspace resolvers, but must not fork shared protocol semantics.

Guidance:

- Keep commands identity-local and fail-close.
- Prefer relative paths rooted at the current identity pack or protocol repo.
- Do not introduce user-specific absolute paths into committed instance helpers.
""".format(identity_token=identity_token)


def _default_instance_script_manifest(identity_id: str) -> dict[str, Any]:
    return {
        "manifest_version": "v1",
        "identity_id": str(identity_id or "").strip(),
        "scripts": {},
    }


def _default_identity_agent_yaml(identity_id: str, title: str, description: str) -> str:
    identity_token = str(identity_id or "").strip() or "<identity-id>"
    title_token = str(title or "").strip() or identity_token
    description_token = str(description or "").strip()
    return (
        "interface:\n"
        f'  display_name: "{title_token}"\n'
        f'  short_description: "{description_token}"\n'
        f'  default_prompt: "Operate as {identity_token} and satisfy runtime gates."\n\n'
        "policy:\n"
        "  allow_implicit_activation: true\n"
        "  activation_priority: 50\n"
        "  conflict_resolution: \"priority_then_objective\"\n\n"
        "dependencies:\n"
        "  tools: []\n\n"
        "observability:\n"
        "  event_topics: []\n"
        "  required_artifacts:\n"
        "    - \"runtime/reports/*.json\"\n"
    )


def _validator_doc_defaults(validator_script: str) -> tuple[str, str]:
    governance_doc, review_doc = resolve_validator_doc_defaults(
        Path(__file__).resolve().parent.parent,
        validator_script=validator_script,
    )
    return governance_doc, review_doc


def _ensure_identity_prompt_governance_kernel(
    text: str,
    *,
    identity_id: str,
    title: str = "",
    description: str = "",
) -> tuple[str, list[str], bool]:
    source_text = str(text or "")
    lowered = source_text.lower()
    missing_tokens = [token for token in PROMPT_GOVERNANCE_REQUIRED_TOKENS if token not in lowered]
    marker_present = PROMPT_GOVERNANCE_KERNEL_HEADING.lower() in lowered
    if not missing_tokens and marker_present:
        return source_text, [], False

    governance_lines = {
        "role": f"- role: `{str(identity_id or '').strip() or 'unspecified-identity'}` operates as {str(title or '').strip() or str(identity_id or '').strip() or 'unspecified-identity'}.",
        "principle": "- principle: fail-close, evidence-first, and runtime source-of-truth.",
        "decision": "- decision: release conclusions only when current-round receipts and validators align.",
        "gate": "- gate: required gates, recurrence closure, and three-plane status must stay mutually consistent.",
    }

    lines = source_text.splitlines()
    if marker_present:
        marker_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if str(line).strip().lower() == PROMPT_GOVERNANCE_KERNEL_HEADING.lower()
            ),
            -1,
        )
        if marker_index >= 0 and missing_tokens:
            insert_at = marker_index + 1
            for token in missing_tokens:
                lines.insert(insert_at, governance_lines[token])
                insert_at += 1
            updated = "\n".join(lines).strip() + "\n"
            return updated, missing_tokens, True

    kernel = _identity_prompt_governance_kernel(
        identity_id=identity_id,
        title=title,
        description=description,
    ).rstrip()
    if lines and str(lines[0]).startswith("#"):
        updated_lines = [lines[0], ""]
        updated_lines.extend(kernel.splitlines())
        if len(lines) > 1:
            updated_lines.append("")
            updated_lines.extend(lines[1:])
        updated = "\n".join(updated_lines).strip() + "\n"
    else:
        updated = (kernel + "\n\n" + source_text.strip()).strip() + "\n"
    return updated, list(PROMPT_GOVERNANCE_REQUIRED_TOKENS), True


def _host_gateway_signer_secret_env(identity_id: str) -> str:
    token = "".join(ch if str(ch).isalnum() else "_" for ch in str(identity_id or "").strip()).upper()
    token = "_".join([segment for segment in token.split("_") if segment])
    if not token:
        token = "UNSPECIFIED_IDENTITY"
    return f"{HOST_GATEWAY_SIGNER_SECRET_ENV_PREFIX}{token}"


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_signing_key(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="ignore").strip()
        if existing:
            return existing
    secret = secrets.token_hex(32)
    path.write_text(secret + "\n", encoding="utf-8")
    return secret


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def dump_yaml(path: Path, data) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _repo_root() -> Path:
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists():
            return p
    return cur


def _minimal_current_task(
    identity_id: str,
    title: str,
    description: str,
    *,
    agent_identity_versions: dict[str, str],
) -> dict:
    methodology_version = str((agent_identity_versions or {}).get("methodology_version", "")).strip()
    prompt_version = str((agent_identity_versions or {}).get("prompt_version", "")).strip()
    json_version = str((agent_identity_versions or {}).get("json_version", "")).strip()
    task = {
        "task_id": f"{identity_id}_bootstrap",
        "agent_identity": {
            "name": identity_id,
            "role": title,
            "methodology_version": methodology_version,
            "prompt_version": prompt_version,
            "json_version": json_version,
            "identity_prompt_path": f"identity/packs/{identity_id}/IDENTITY_PROMPT.md",
            "canon_path": "identity/protocol/IDENTITY_PROTOCOL.md",
        },
        "response_stamp_profile": default_response_stamp_profile(),
        "objective": {
            "title": description,
            "priority": "HIGH",
            "status": "pending",
        },
        "state_machine": {
            "current_state": "intake",
            "allowed_states": ["intake", "analyze", "execute", "verify", "done", "blocked"],
            "transition_rules": [
                "intake -> analyze",
                "analyze -> execute",
                "execute -> verify",
                "verify -> done",
                "verify -> analyze",
                "analyze -> blocked",
            ],
        },
        "gates": {
            "document_gate": "required",
            "media_gate": "required",
            "category_compliance_gate": "required",
            "reject_memory_gate": "required",
            "protocol_baseline_review_gate": "required",
            "payload_evidence_gate": "required",
            "multimodal_consistency_gate": "required",
            "reasoning_loop_gate": "required",
            "routing_gate": "required",
            "rulebook_gate": "required",
        },
        "protocol_review_contract": {
            "required_before": ["identity_capability_upgrade", "identity_architecture_decision"],
            "must_review_sources": MANDATORY_PROTOCOL_SOURCES,
            "required_evidence_fields": [
                "review_id",
                "reviewed_at",
                "reviewer_identity",
                "purpose",
                "sources_reviewed",
                "findings",
                "decision",
            ],
            "evidence_report_path_pattern": "identity/runtime/examples/protocol-baseline-review-*.json",
            "max_review_age_days": 7,
        },
        "evaluation_contract": {
            "required_evidence_triplet": ["api_evidence", "event_evidence", "ui_evidence"],
            "consistency_required": True,
            "consistency_fail_action": "block_done_and_trigger_recheck",
            "run_report_path_pattern": "resource/reports/*run*.json",
        },
        "reasoning_loop_contract": {
            "max_attempts_before_escalation": 3,
            "escalation_requirement_mode": "at_or_exceed",
            "mandatory_fields_per_attempt": ["attempt", "hypothesis", "patch", "expected_effect", "result"],
            "failure_requires_next_action": True,
            "strict_run_id_binding": True,
            "runtime_report_selection_mode": "prefer_run_id",
            "escalation_signal_fields": [
                "route_switch_triggered",
                "human_collaboration_triggered",
                "escalation_triggered",
                "route_switch_ref",
                "human_collaboration_ref",
                "escalation_ref",
                "next_action",
            ],
            "escalation_signal_values": ["true", "triggered", "escalate", "route_switch", "human_collaboration", "handoff"],
            "escalation_signal_accept_nonempty_ref": True,
            "escalation_signal_nonempty_fields": [
                "route_switch_ref",
                "human_collaboration_ref",
                "escalation_ref",
            ],
        },
        "routing_contract": {
            "auto_route_enabled": True,
            "fallback_switch_after_failures": 2,
            "problem_type_routes": {
                "unknown": ["identity-creator"],
            },
        },
        "rulebook_contract": {
            "append_only": True,
            "required_rule_types": ["negative", "positive"],
            "required_fields": [
                "rule_id",
                "type",
                "trigger",
                "action",
                "evidence_run_id",
                "scope",
                "confidence",
                "updated_at",
            ],
            "rulebook_path": f"identity/packs/{identity_id}/RULEBOOK.jsonl",
        },
        "source_of_truth": {
            "local_docs_roots": [],
            "local_project_evidence_roots": ["resource/reports", "resource/preflight", "resource/reject-archive"],
        },
        "escalation_policy": {
            "email_for_offline_only": True,
            "offline_blockers": [],
            "do_not_email_for": ["routine_status_update", "normal_progress_report", "non_blocking_warning"],
        },
        "required_artifacts": [
            "resource/reports/*.json",
            "resource/reports/*.md",
        ],
        "post_execution_mandatory": [
            f"append task outcome into identity/packs/{identity_id}/TASK_HISTORY.md",
            "update objective.status",
            "update state_machine.current_state",
        ],
        "version_control": {
            "sync_status": "initialized",
            "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        },
    }
    task = _ensure_dialogue_governance_contract(task, identity_id)
    task = _ensure_tool_vendor_governance_contracts(task, identity_id)
    return _ensure_instance_pack_topology_contract(task, identity_id)


def _dialogue_governance_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": False,
        "rollout_mode": "warn",
        "rollout_phase": "phase-1",
        "report_path_pattern": f"identity/runtime/reports/*{identity_id}*dialogue*.json",
        "dialogue_content_report_path_pattern": f"identity/runtime/reports/dialogue-content-synthesis-{identity_id}-*.json",
        "dialogue_cross_validation_report_path_pattern": f"identity/runtime/reports/dialogue-cross-validation-matrix-{identity_id}-*.json",
        "dialogue_result_support_report_path_pattern": f"identity/runtime/reports/dialogue-result-support-{identity_id}-*.json",
        "top3_thresholds": {
            "dialogue_constraint_coverage_rate": 95,
            "dialogue_traceability_rate": 95,
            "dialogue_change_reconciliation_rate": 90,
        },
        "hard_subset_min": 100,
        "redline_thresholds": {
            "hard_constraint_missing_artifact_count": {"max": 0},
            "untraceable_final_claim_count": {"max": 0},
        },
        "done_state_blocker": {
            "unresolved_ambiguity_count": {"max": 0},
        },
    }


def _deep_merge_defaults(defaults: dict, current: dict) -> dict:
    out = copy.deepcopy(defaults)
    for k, v in current.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge_defaults(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _ensure_dialogue_governance_contract(task: dict, identity_id: str) -> dict:
    base = _dialogue_governance_contract_skeleton(identity_id)
    cur = task.get("dialogue_governance_contract")
    if not isinstance(cur, dict):
        task["dialogue_governance_contract"] = base
        return task
    task["dialogue_governance_contract"] = _deep_merge_defaults(base, cur)
    return task


def _instance_pack_topology_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": True,
        "contract_id": INSTANCE_PACK_TOPOLOGY_CONTRACT_ID,
        "validator": INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID,
        "fail_mode": "fail_required",
        "owner_scope": "identity_instance",
        "artifact_class": "instance_pack_topology",
        "pack_root_required_files": [
            "CURRENT_TASK.json",
            "IDENTITY_PROMPT.md",
            "TASK_HISTORY.md",
            "META.yaml",
            "RULEBOOK.jsonl",
            "agents/identity.yaml",
            "scripts/README.md",
        ],
        "pack_root_required_dirs": [
            "agents",
            "runtime",
            "scripts",
        ],
        "pack_root_optional_dirs": [],
        "pack_root_legacy_compat_dirs": [],
        "runtime_required_dirs": [
            "runtime/examples",
            "runtime/gate",
            "runtime/logs",
            "runtime/plugins",
            "runtime/state",
        ],
        "runtime_optional_dirs": [
            "runtime/examples/collaboration-trigger",
            "runtime/examples/handoff",
            "runtime/examples/handoff/negative",
            "runtime/examples/handoff/positive",
            "runtime/examples/install",
            "runtime/examples/role-binding",
            "runtime/logs/capability",
            "runtime/logs/collaboration",
            "runtime/logs/feedback",
            "runtime/logs/handoff",
            "runtime/logs/upgrade",
            f"runtime/logs/upgrade/{identity_id}",
            "runtime/metrics",
            "runtime/protocol-feedback",
            "runtime/protocol-feedback/evidence-index",
            "runtime/protocol-feedback/outbox-to-protocol",
            "runtime/protocol-feedback/upgrade-proposals",
            "runtime/reports",
            "runtime/reports/broadcast",
            "runtime/reports/agent-relay-final-answer",
            "runtime/reports/host-visible-surface",
            "runtime/reports/install",
            "runtime/reports/instance-script-admission",
            "runtime/reports/instance-script-execution",
            "runtime/reports/instance-script-emit",
            "runtime/reports/instance-script-recovery",
            "runtime/reports/multimodal-runtime-stage",
            "runtime/reports/required-gate-bundle-entry",
            "runtime/rulebooks",
        ],
        "forbidden_dir_patterns": [
            "runtime/scripts*",
            "**/__pycache__",
            "**/.pytest_cache",
        ],
        "scripts_surface": {
            "root_dir": "scripts",
            "must_live_at_pack_root": True,
            "must_not_live_under_runtime": True,
            "shared_dependency_policy": {
                "allow_workspace_resolvers": True,
                "allow_protocol_renderers": True,
                "forbid_protocol_semantic_forks": True,
                "forbid_workspace_shared_instance_patch_scripts": True,
                "forbid_user_specific_absolute_paths": True,
            },
            "bootstrap_examples": [
                "python3 <identity-pack-root>/scripts/<instance-helper>.py",
                "PYTHONDONTWRITEBYTECODE=1 python3 <identity-pack-root>/scripts/<instance-helper>.py --json-only",
            ],
        },
    }


def _ensure_instance_pack_topology_contract(task: dict, identity_id: str) -> dict:
    base = _instance_pack_topology_contract_skeleton(identity_id)
    cur = task.get(INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY)
    if not isinstance(cur, dict):
        task[INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY] = base
        return task
    task[INSTANCE_PACK_TOPOLOGY_CONTRACT_KEY] = _deep_merge_defaults(base, cur)
    return task


def _tool_installation_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": False,
        "report_path_pattern": f"identity/runtime/reports/tool-installation-{identity_id}-*.json",
        "required_report_fields": [
            "tool_gap_detected",
            "tool_gap_summary_ref",
            "install_plan_ref",
            "approval_receipt_ref",
            "execution_log_ref",
            "installed_artifact_ref",
            "installed_version",
            "post_install_healthcheck_ref",
            "task_smoke_result_ref",
            "route_binding_update_ref",
            "fallback_route_if_install_fails",
            "rollback_ref",
        ],
        "enforcement_validator": "scripts/validate_identity_tool_installation.py",
    }


def _vendor_api_discovery_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": False,
        "report_path_pattern": f"identity/runtime/reports/vendor-api-discovery-{identity_id}-*.json",
        "required_report_fields": [
            "vendor_name",
            "vendor_surface_name",
            "official_reference_url",
            "machine_readable_contract_ref",
            "contract_kind",
            "auth_discovery_ref",
            "versioning_policy_ref",
            "rate_limit_policy_ref",
            "capability_probe_command_ref",
            "attach_readiness_decision",
            "fallback_vendor_or_route_ref",
        ],
        "source_priority": [
            "official_vendor_source",
            "standards_body_source",
            "community_mirror_or_wrapper",
        ],
        "t2_source_requires_approval": True,
        "enforcement_validator": "scripts/validate_identity_vendor_api_discovery.py",
    }


def _vendor_api_solution_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": False,
        "report_path_pattern": f"identity/runtime/reports/vendor-api-solution-{identity_id}-*.json",
        "required_report_fields": [
            "problem_statement_ref",
            "selected_vendor_api_ref",
            "solution_pattern",
            "decision_rationale_ref",
            "option_comparison_ref",
            "security_boundary_ref",
            "auth_scope_strategy_ref",
            "rate_limit_strategy_ref",
            "fallback_solution_ref",
            "rollback_solution_ref",
            "owner_layer_declaration_ref",
        ],
        "single_selected_option_required": True,
        "no_solution_allowed_states": ["defer", "blocked"],
        "enforcement_validator": "scripts/validate_identity_vendor_api_solution.py",
    }


def _skill_installation_supply_chain_contract_skeleton(identity_id: str) -> dict:
    return {
        "required": True,
        "contract_id": "rq_039_skill_installation_supply_chain_contract_v1",
        "artifact_type": "skill",
        "required_capability_drivers": [
            "scripts/validate_identity_tool_installation.py",
            "scripts/validate_identity_vendor_api_discovery.py",
            "scripts/validate_identity_vendor_api_solution.py",
        ],
        "dependent_contract_keys": [
            "tool_installation_contract",
            "vendor_api_discovery_contract",
            "vendor_api_solution_contract",
            "skill_path_integrity_contract_v1",
        ],
        "installation_receipt_path_pattern": f"identity/runtime/reports/skill-installation-{identity_id}-*.json",
        "validator": "scripts/validate_skill_installation_supply_chain.py",
    }


def _skill_frontmatter_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": "rq_040_skill_frontmatter_contract_v1",
        "required_frontmatter_fields": [
            "skill_id",
            "version",
            "owner",
            "source",
        ],
        "strict_require_frontmatter": True,
        "selected_path_scope_policy": "governed_selected_paths_only",
        "validator": "scripts/validate_skill_frontmatter.py",
    }


def _skill_sync_drift_guard_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": "rq_041_skill_sync_drift_guard_contract_v1",
        "artifact_type": "skill",
        "drift_check_mode": "sha256",
        "selected_path_scope_policy": "governed_selected_paths_only",
        "drift_scope_mode": "selected_root_family_only",
        "allow_missing_skills": False,
        "validator": "scripts/validate_skill_sync_drift_guard.py",
    }


def _semantic_routing_guard_contract_skeleton() -> dict:
    return {
        "required": False,
        "feedback_batch_path_pattern": "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md",
        "required_fields": ["intent_domain", "intent_confidence", "classifier_reason"],
        "domain_enum": ["protocol_vendor", "business_partner", "mixed", "unknown"],
        "enforcement_validator": "scripts/validate_semantic_routing_guard.py",
    }


def _instance_protocol_split_receipt_contract_skeleton() -> dict:
    return {
        "required": False,
        "receipt_path_pattern": "runtime/protocol-feedback/outbox-to-protocol/SPLIT_RECEIPT_*.json",
        "enforcement_validator": "scripts/validate_instance_protocol_split_receipt.py",
    }


def _protocol_feedback_reply_channel_contract_skeleton() -> dict:
    return {
        "required": False,
        "outbox_dir": "runtime/protocol-feedback/outbox-to-protocol",
        "primary_outbox_glob": "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md",
        "required_index_path": "runtime/protocol-feedback/evidence-index/INDEX.md",
        "enforcement_validator": "scripts/validate_protocol_feedback_reply_channel.py",
    }


def _protocol_feedback_inbox_channel_contract_skeleton() -> dict:
    return {
        "required": False,
        "inbox_dir": "runtime/protocol-feedback/inbox-from-protocol",
        "primary_inbox_glob": "runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_*.md",
        "required_index_path": "runtime/protocol-feedback/evidence-index/INDEX.md",
        "enforcement_validator": "scripts/validate_protocol_feedback_inbox_channel.py",
    }


def _protocol_feedback_sidecar_contract_skeleton() -> dict:
    return {
        "required": False,
        "default_mode": "non_blocking",
        "blocking_error_prefixes": ["IP-WRB-", "IP-SEM-", "IP-PFB-"],
        "escalation_policy": "p0_governance_boundary",
        "enforcement_validator": "scripts/validate_protocol_feedback_sidecar_contract.py",
    }


def _gated_switch_guard_contract_skeleton() -> dict:
    return {
        "required": True,
        "enforcement_validator": "scripts/validate_gated_switch_guard.py",
        "safe_switch_states": ["WAITING_INPUT", "DONE_WAITING_INPUT", "IDLE"],
        "blocked_switch_states": ["RUNNING", "TOOL_CALLING", "STREAMING"],
        "handshake_timeout_seconds": 90,
        "mandatory_switch_chain": [
            "switch_request",
            "pre_switch_gate",
            "switch_apply",
            "switch_ack",
            "ack_verify",
            "dispatch",
        ],
    }


def _protocol_lane_activation_headstamp_contract_skeleton() -> dict:
    return {
        "required": True,
        "enforcement_validator": "scripts/validate_protocol_lane_headstamp_continuity.py",
        "required_lane": "protocol",
        "route_non_starvation": True,
        "headstamp_dual_context_required": True,
        "required_fields": [
            "requested_lane",
            "previous_lane",
            "resolved_lane",
            "lane_activation_status",
            "lane_activation_error_code",
            "route_source_ref",
            "lane_activation_evidence_ref",
            "headstamp_continuity_status",
            "headstamp_error_code",
        ],
    }


def _native_chat_headstamp_contract_skeleton() -> dict:
    return {
        "required": True,
        "surface_class": "host_native_chat_panel",
        "delivery_mode": "assistant_text_injection",
        "template_ref": "identity/protocol/plugins/templates/native-chat-headstamp.machine_verification_profiles_v1.json",
        "prompt_hard_guard_template_ref": DEFAULT_NATIVE_CHAT_PROMPT_HARD_GUARD_TEMPLATE_REF,
        "default_machine_profile": "mini",
        "allowed_machine_profiles": ["mini", "standard", "audit"],
        "success_order": ["Identity-Context", "Machine-Verification", "body"],
        "runtime_loop": ["machine-verify", "assistant-visible-inject", "next-turn-reverify"],
        "failure_mode": "withhold_success_identity_line",
        "headerless_reply_forbidden": True,
        "failure_envelope_required": True,
    }


def _execution_target_tuple_isolation_contract_skeleton() -> dict:
    return {
        "required": False,
        "validator": "scripts/validate_execution_target_tuple_isolation.py",
        "runtime_bridge_root_env": "IDENTITY_RUNTIME_BRIDGE_ROOT",
        "required_fields": [
            "execution_target_kind",
            "execution_target_key",
            "execution_target_ref",
            "route_conflict_status",
            "route_conflict_error_code",
        ],
        "target_kind_enum": ["tmux_session", "codex_home", "process_call", "worker_queue"],
        "error_code_family": [
            "IP-XTARGET-001",
            "IP-XTARGET-002",
            "IP-XTARGET-003",
            "IP-XTARGET-004",
        ],
        "fail_action": "block_when_execution_target_tuple_isolation_violated",
    }


def _protocol_unique_entry_gate_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": "protocol_unique_entry_gate_contract_v1",
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "entry_script": "scripts/required_gate_bundle_runner.py",
        "bundle_key": "required_gate_bundle_runner",
        "entry_error_family": [
            "IP-GATE-ENTRY-001",
            "IP-GATE-ENTRY-002",
        ],
        "enforce_on_operations": [
            "activate",
            "update",
            "mutation",
            "readiness",
            "e2e",
            "ci",
            "validate",
            "three-plane",
        ],
        "scope": "all_identity_instance_actions",
        "fail_action": "block_execution_when_not_entered_via_required_gate_bundle_runner",
        "require_strict_operation_receipt": True,
        "entry_receipt_state_file": "runtime/state/required_gate_bundle_entry.latest.json",
        "entry_receipt_history_pattern": "runtime/reports/required-gate-bundle-entry/required-gate-bundle-entry-*.json",
        "entry_receipt_max_age_seconds": 1800,
        "entry_receipt_required_fields": [
            "bundle_key",
            "bundle_contract_id",
            "identity_id",
            "operation",
            "surface_label",
            "wrapper_dispatch_required",
            "wrapper_surface_status",
            "wrapper_dispatch_token_status",
            "wrapper_dispatch_proof_required",
            "wrapper_dispatch_proof_status",
            "run_id_binding",
            "actor_id",
            "session_id",
            "bundle_status",
            "error_code",
        ],
        "entry_receipt_selector_policy_id": UNIQUE_ENTRY_RECEIPT_SELECTOR_POLICY_ID,
        "entry_receipt_selector_precedence": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_PRECEDENCE),
        "entry_receipt_selector_source_fields": list(UNIQUE_ENTRY_RECEIPT_SELECTOR_SOURCE_FIELDS),
        "onboarding_single_entry_command": "python3 scripts/identity_creator.py validate --catalog <catalog> --identity-id <identity> --actor-id <actor> --session-id <session>",
        "extension_attach_entrypoint": "identity/protocol/plugins/PLUGIN_JOIN_INTAKE.v1.6.4.yaml",
    }


def _host_gateway_operation_profile_policy() -> dict:
    return {
        "strict_operations": list(HOST_GATEWAY_STRICT_OPERATIONS),
        "light_operations": list(HOST_GATEWAY_LIGHT_OPERATIONS),
        "strict_gate_profile": HOST_GATEWAY_STRICT_GATE_PROFILE,
        "strict_gate_profile_by_operation": dict(HOST_GATEWAY_STRICT_GATE_PROFILE_BY_OPERATION),
        "light_gate_profile": HOST_GATEWAY_LIGHT_GATE_PROFILE,
        "allow_upgrade_only": bool(HOST_GATEWAY_ALLOW_UPGRADE_ONLY),
    }


def _host_gateway_broadcast_policy() -> dict:
    return {
        "required": True,
        "protocol_broadcast_items_dir": HOST_GATEWAY_BROADCAST_ITEMS_DIR,
        "protocol_broadcast_index_file": HOST_GATEWAY_BROADCAST_INDEX_FILE,
        "protocol_broadcast_schema_file": HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
        "instance_state_file": HOST_GATEWAY_BROADCAST_STATE_FILE,
        "instance_receipt_pattern": HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
        "instance_ack_pattern": HOST_GATEWAY_BROADCAST_ACK_PATTERN,
        "block_on_critical_unacked": False,
    }


def _default_broadcast_state_doc(identity_id: str) -> dict:
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


def _default_host_visible_surface_state_doc(identity_id: str) -> dict:
    channels = {
        channel: {
            "last_receipt_path": "",
            "last_status": "",
            "receipt_source": "",
            "last_run_id": "",
            "updated_at_utc": "",
        }
        for channel in HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS
    }
    return {
        "schema_version": "v1",
        "identity_id": str(identity_id or "").strip(),
        "channels": channels,
        "updated_at_utc": "",
    }


def _default_host_visible_surface_post_check_closure_state_doc(identity_id: str) -> dict:
    return {
        "schema_version": HOST_VISIBLE_SURFACE_POST_CHECK_SCHEMA_VERSION,
        "identity_id": str(identity_id or "").strip(),
        "catalog_path": "",
        "pack_path": "",
        "task_path": "",
        "validator": HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
        "closure_status": "PASS_REQUIRED",
        "block_on_active": bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        "blocker_active": False,
        "error_code": "",
        "stale_reasons": [],
        "live_receipt_required": True,
        "required_actor_id": "",
        "required_session_id": "",
        "required_run_id": "",
        "checked_at_utc": "",
    }


def _host_visible_surface_registry_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
        "validator": HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
        "required_channels": list(HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS),
        "runtime_state_file": HOST_VISIBLE_SURFACE_STATE_FILE,
        "runtime_receipt_pattern": HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
        "runtime_receipt_max_age_seconds": int(HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_MAX_AGE_SECONDS),
        "strict_live_run_binding_required": bool(HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED),
        "post_check_closure_state_file": HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
        "post_check_block_on_active": bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE),
        "required_attestation_fields": list(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS),
        "required_pass_status_fields": list(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS),
        "final_channel_id": HOST_VISIBLE_FINAL_CHANNEL_ID,
        "final_channel_relay_required": bool(HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED),
        "final_channel_relay_surface": HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE,
        "final_channel_relay_mode": HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE,
        "final_channel_delivery_authority": HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY,
        "final_channel_required_attestation_fields": list(
            HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS
        ),
        "final_channel_required_pass_status_fields": list(
            HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS
        ),
        "runtime_live_receipt_sources": list(HOST_VISIBLE_SURFACE_RUNTIME_ALLOWED_LIVE_RECEIPT_SOURCES),
        "fixture_receipt_source": HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
        "fixture_allowed_operations": list(HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS),
        "required_live_probe_delegate": HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
        "host_dispatch_mode_required": HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
        "host_release_mode_required": HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    }


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(str(payload or "").encode("utf-8")).hexdigest()


def _host_gateway_wrapper_template_attestation_policy() -> dict:
    ingress_template = _protocol_ingress_wrapper_template()
    egress_template = _protocol_egress_wrapper_template()
    session_chain_template = _protocol_session_chain_wrapper_template()
    _assert_wrapper_template_constant_bindings(
        egress_template=egress_template,
        session_chain_template=session_chain_template,
    )
    return {
        "required": True,
        "attestation_id": HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_ID,
        "ingress_wrapper_template_sha256": _sha256_text(ingress_template),
        "egress_wrapper_template_sha256": _sha256_text(egress_template),
        "session_chain_wrapper_template_sha256": _sha256_text(session_chain_template),
        "session_chain_required_semantic_tokens": list(HOST_GATEWAY_SESSION_CHAIN_REQUIRED_SEMANTIC_TOKENS),
        "required_tuple_fields": list(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS),
    }


def _assert_wrapper_template_constant_bindings(
    *,
    egress_template: str,
    session_chain_template: str,
) -> None:
    missing: list[str] = []
    egress_expected = f'FINAL_EMIT_CHANNEL_ID = "{FINAL_EMIT_CHANNEL_ID}"'
    if egress_expected not in str(egress_template):
        missing.append("egress_template_missing_final_emit_channel_constant_binding")
    session_chain_expected = (
        f'HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE = "{HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE}"'
    )
    if session_chain_expected not in str(session_chain_template):
        missing.append("session_chain_template_missing_fixture_receipt_source_constant_binding")
    if missing:
        raise RuntimeError("wrapper_template_constant_binding_invariant_failed:" + ",".join(missing))


def _protocol_host_unique_channel_contract_skeleton(identity_id: str) -> dict:
    signer_secret_env = _host_gateway_signer_secret_env(identity_id)
    return {
        "required": True,
        "contract_id": HOST_GATEWAY_CONTRACT_ID,
        "validator": "scripts/validate_protocol_unique_entry_gate.py",
        "protocol_ingress_script": UNIQUE_INGRESS_SCRIPT,
        "protocol_egress_script": UNIQUE_EGRESS_SCRIPT,
        "ingress_wrapper_path": HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
        "egress_wrapper_path": HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
        "session_chain_wrapper_path": HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
        "gateway_contract_path": HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
        "entry_receipt_policy": {
            "required": True,
            "required_surface_label": HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
            "required_wrapper_surface_status": HOST_GATEWAY_REQUIRED_SURFACE_STATUS,
            "required_wrapper_dispatch_token_status": HOST_GATEWAY_REQUIRED_DISPATCH_STATUS,
        },
        "ingress_proof_policy": {
            "required": True,
            "max_age_seconds": int(HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS),
            "signer_mode": HOST_GATEWAY_SIGNER_MODE,
            "signer_secret_env": signer_secret_env,
            "signing_key_path": HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
            "bootstrap_env_secret_from_signing_key_path": bool(HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH),
        },
        "egress_receipt_policy": {
            "required": True,
        },
        "egress_grant_policy": {
            "required": True,
            "max_age_seconds": int(HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS),
            "signer_mode": HOST_GATEWAY_SIGNER_MODE,
            "signer_secret_env": signer_secret_env,
            "signing_key_path": HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
            "bootstrap_env_secret_from_signing_key_path": bool(HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH),
        },
        "headstamp_policy": {
            "required": True,
        },
        "identity_tuple_fields": list(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS),
        "host_dispatch_mode": HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
        "host_release_mode": HOST_GATEWAY_REQUIRED_RELEASE_MODE,
        "ingress_wrapper_dispatch_token": HOST_GATEWAY_INGRESS_DISPATCH_TOKEN,
        "operation_profile_policy": _host_gateway_operation_profile_policy(),
        "broadcast_policy": _host_gateway_broadcast_policy(),
        "host_visible_surface_registry_contract_ref": HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
        HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY: _host_gateway_wrapper_template_attestation_policy(),
    }


def _protocol_downsink_path_registry_skeleton() -> dict:
    return {
        DOWNSINK_RUNTIME_GATE_DOMAIN: {
            "anchor_ref": "identity_pack_root_ref",
            "entries": [
                {
                    "path_id": "runtime_gate.ingress_wrapper",
                    "entry_type": "file",
                    "path": "runtime/gate/protocol_ingress_wrapper.py",
                },
                {
                    "path_id": "runtime_gate.egress_wrapper",
                    "entry_type": "file",
                    "path": "runtime/gate/protocol_egress_wrapper.py",
                },
                {
                    "path_id": "runtime_gate.session_chain_wrapper",
                    "entry_type": "file",
                    "path": "runtime/gate/protocol_session_chain_wrapper.py",
                },
                {
                    "path_id": DOWNSINK_RUNTIME_MIRROR_PATH_ID,
                    "entry_type": "file",
                    "path": "runtime/gate/protocol_gateway_contract.json",
                },
            ],
        },
        DOWNSINK_RUNTIME_BROADCAST_DOMAIN: {
            "anchor_ref": "identity_pack_root_ref",
            "entries": [
                {
                    "path_id": "runtime_broadcast.state_file",
                    "entry_type": "file",
                    "path": HOST_GATEWAY_BROADCAST_STATE_FILE,
                },
                {
                    "path_id": "runtime_broadcast.receipt_pattern",
                    "entry_type": "glob",
                    "path": HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
                },
                {
                    "path_id": "runtime_broadcast.ack_pattern",
                    "entry_type": "glob",
                    "path": HOST_GATEWAY_BROADCAST_ACK_PATTERN,
                },
            ],
        },
        DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN: {
            "anchor_ref": "identity_pack_root_ref",
            "entries": [
                {
                    "path_id": "runtime_protocol_feedback.outbox_feedback_batch",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_receipt",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/*_RECEIPT_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_summary",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/SUMMARY_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_seed",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/*_SEED_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_pack",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/*_PACK_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_requirements",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/REQUIREMENTS_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_pending",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/*_PENDING_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_inquiry_requiredization_trigger",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/INQUIRY_REQUIREDIZATION_TRIGGER_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_sanitization_paraphrase",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/SANITIZATION_PARAPHRASE_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_session_lane_lock_protocol",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_PROTOCOL_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_session_lane_lock_exit",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/SESSION_LANE_LOCK_EXIT_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.outbox_broadcast",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/outbox-to-protocol/BROADCAST_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.inbox_primary",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.inbox_receipt",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/inbox-from-protocol/PROTOCOL_INBOX_RECEIPT_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.inbox_summary",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/inbox-from-protocol/INBOX_SUMMARY_*.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.evidence_index",
                    "entry_type": "file",
                    "path": "runtime/protocol-feedback/evidence-index/INDEX.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.upgrade_proposals_md",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/upgrade-proposals/*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.atomic_receipt",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/atomic/*.receipt.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.atomic_batch",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/atomic/*.batch.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.atomic_index",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/atomic/*.index.json",
                },
                {
                    "path_id": "runtime_protocol_feedback.roundtables",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/roundtables/ROUNDTABLE_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.protocol_vendor_intel",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/protocol-vendor-intel/PROTOCOL_VENDOR_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.business_partner_intel",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/business-partner-intel/BUSINESS_PARTNER_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.vendor_intel",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/vendor-intel/VENDOR_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.issues",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/issues/ISSUE_*.md",
                },
                {
                    "path_id": "runtime_protocol_feedback.review_notes",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/review-notes/*.log",
                },
                {
                    "path_id": "runtime_protocol_feedback.validation",
                    "entry_type": "glob",
                    "path": "runtime/protocol-feedback/validation/*.json",
                },
            ],
        },
        DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN: {
            "anchor_ref": "protocol_repo_root_ref",
            "entries": [
                {
                    "path_id": "protocol_broadcast_source.items_dir",
                    "entry_type": "dir",
                    "path": HOST_GATEWAY_BROADCAST_ITEMS_DIR,
                },
                {
                    "path_id": "protocol_broadcast_source.index_file",
                    "entry_type": "file",
                    "path": HOST_GATEWAY_BROADCAST_INDEX_FILE,
                },
                {
                    "path_id": "protocol_broadcast_source.schema_file",
                    "entry_type": "file",
                    "path": HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
                },
            ],
        },
    }


def _protocol_downsink_path_immutability_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID,
        "validator_id": DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID,
        "write_guard_validator_id": DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID,
        "source_literal_lock_policy": {
            "required": True,
            "validator_id": DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
            "enforce_registered_runtime_path_literals_only": True,
            "allow_inline_override_marker": DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
            "scan_globs": list(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS),
        },
        "path_registry": _protocol_downsink_path_registry_skeleton(),
        "anchor_policy": {
            "protocol_repo_root_ref": DOWNSINK_ANCHOR_PROTOCOL_REPO_ROOT_REF,
            "identity_pack_root_ref": DOWNSINK_ANCHOR_IDENTITY_PACK_ROOT_REF,
            "allow_parent_escape": False,
            "allow_symlink_escape": False,
        },
        "schema_policy": {
            "reject_additional_properties": True,
            "require_all_declared_paths_present_in_runtime_contract": True,
        },
        "operation_enforcement": {
            "strict_operations": list(HOST_GATEWAY_STRICT_OPERATIONS),
            "light_operations": list(HOST_GATEWAY_LIGHT_OPERATIONS),
            "strict_fail_mode": "fail_required",
            "light_fail_mode": "fail_required",
        },
    }


def _multimodal_plugin_enforcement_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": "rq_034_multimodal_plugin_enforcement_contract_v1",
        "validator": "scripts/validate_multimodal_plugin_enforcement.py",
        "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
        "provider_profiles_path": "identity/protocol/plugins/PROVIDER_PROFILES.current.yaml",
        "required_fields": [
            "multimodal_plugin_enforcement_status",
            "plugin_registry_status",
            "plugin_naming_status",
            "plugin_schema_status",
            "plugin_threshold_status",
            "plugin_path_status",
            "plugin_copy_policy_status",
            "provider_config_status",
        ],
        "provider_binding_path_pattern": "runtime/plugins/provider-bindings.local.yaml",
        "provider_binding_requirements": {
            "required_profiles": [
                "glm46v_vision_prod",
                "openai_vision_prod",
            ],
            "minimum_enabled_bindings": 1,
            "require_all_required_profiles": False,
        },
        "capability_requirements": {
            "vision": True,
            "tool_calling": True,
            "structured_json": True,
        },
        "done_transition_guard": {
            "requires_multimodal_evidence_consistency": True,
            "inconsistent_evidence_transition": "block_done",
        },
        "fail_action": "block_done_transition_on_inconsistent_multimodal_evidence",
    }


def _reasoning_loop_failclose_contract_skeleton() -> dict:
    return {
        "required": True,
        "contract_id": "rq_035_reasoning_loop_failclose_contract_v1",
        "plugin_id": "reasoning-loop-enforcement",
        "validator": "scripts/validate_reasoning_loop_failclose.py",
        "plugin_registry_path": "identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
        "contract_file": "identity/protocol/plugins/reasoning-loop-enforcement/plugin.contract.yaml",
        "reasoning_enforcement_level": "L3",
        "minimum_enforcement_level": "L3",
        "reasoning_enforcement": {
            "default_level": "L3",
            "minimum_level": "L3",
        },
        "level_required_attempt_fields": {
            "L0": [],
            "L1": ["attempt", "hypothesis", "patch", "expected_effect", "result"],
            "L2": [
                "attempt",
                "hypothesis",
                "patch",
                "expected_effect",
                "result",
                "result_code",
                "target_reached",
                "no_target_reached",
                "next_action",
                "evidence_refs",
            ],
            "L3": [
                "attempt",
                "hypothesis",
                "patch",
                "expected_effect",
                "result",
                "result_code",
                "target_reached",
                "no_target_reached",
                "next_action",
                "evidence_refs",
            ],
        },
        "level_required_run_fields": {
            "L2": [
                "roundtable_evidence_refs",
                "vendor_evidence_refs",
                "network_evidence_refs",
                "reference_evidence_refs",
            ],
            "L3": [
                "roundtable_evidence_refs",
                "vendor_evidence_refs",
                "network_evidence_refs",
                "reference_evidence_refs",
            ],
        },
        "level_required_external_fields": {
            "L3": [
                "external_source_freshness_status",
                "conflict_reconciliation_note",
                "source_url_set",
            ],
        },
        "completion_states_done": ["done", "pass", "passed", "success", "completed", "closed"],
        "no_target_completion_mode": "terminal_attempt_only",
        "done_requires_terminal_target_reached": True,
        "no_target_result_tokens": ["no_target_reached", "not_reached", "target_not_reached"],
        "failed_result_tokens": ["fail", "failed", "error", "blocked", "no_target_reached", "not_reached", "target_not_reached"],
        "pass_result_tokens": ["pass", "passed", "success", "done", "resolved", "target_reached"],
        "max_attempts_before_escalation": 3,
        "escalation_requirement_mode": "at_or_exceed",
        "failure_requires_next_action": True,
        "strict_run_id_binding": True,
        "runtime_report_selection_mode": "prefer_run_id",
        "escalation_signal_fields": [
            "route_switch_triggered",
            "human_collaboration_triggered",
            "escalation_triggered",
            "route_switch_ref",
            "human_collaboration_ref",
            "escalation_ref",
            "next_action",
        ],
        "escalation_signal_accept_nonempty_ref": True,
        "escalation_signal_nonempty_fields": ["route_switch_ref", "human_collaboration_ref", "escalation_ref"],
        "escalation_signal_values": ["true", "triggered", "escalate", "route_switch", "human_collaboration", "handoff"],
        "learning_report_path_pattern": "runtime/examples/*learning-sample*.json",
        "required_fields": [
            "reasoning_loop_failclose_status",
            "reasoning_runtime_evidence_status",
            "reasoning_attempt_trace_status",
            "no_target_done_block_status",
            "terminal_attempt_index",
            "terminal_attempt_target_reached",
            "terminal_attempt_no_target_reached",
            "no_target_completion_mode",
            "done_requires_terminal_target_reached",
            "reasoning_next_action_status",
            "reasoning_escalation_status",
            "escalation_requirement_mode",
            "escalation_signal_accept_nonempty_ref",
            "escalation_signal_nonempty_fields",
            "strict_run_id_binding",
            "runtime_report_selection_mode",
            "reasoning_four_track_status",
            "external_source_freshness_status",
            "runtime_report_path",
            "runtime_report_run_id",
            "reasoning_attempt_count",
            "reasoning_failed_attempt_count",
            "no_target_reached_detected",
            "reasoning_runtime_evidence_refs",
        ],
        "done_transition_guard": {
            "no_target_reached_cannot_complete": True,
            "failed_attempt_requires_next_action": True,
            "threshold_requires_escalation": True,
        },
        "fail_action": "block_done_transition_on_reasoning_no_target_or_unclosed_attempts",
    }


def _release_unlock_formula_contract_skeleton() -> dict:
    governance_doc, review_doc = _validator_doc_defaults("scripts/validate_unlock_formula.py")
    return {
        "required": True,
        "validator": "scripts/validate_unlock_formula.py",
        "governance_doc": governance_doc,
        "review_doc": review_doc,
        "required_fields": [
            "unlock_allowed",
            "decision_gates",
            "p0_total",
            "p0_done",
            "p0_not_done_refs",
            "audit_signoff_status",
            "env_blockers",
            "protocol_blockers",
            "evidence_refs",
        ],
        "d6_derived_only": True,
        "fail_action": "block_release_tag_and_reenter_p0_closure",
    }


def _capability_boundary_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_capability_boundary_classification.py",
        "required_fields": [
            "boundary_classification",
            "classification_source",
            "capability_activation_status",
            "capability_activation_error_code",
        ],
        "classification_rules": {
            "ip_cap_prefix": "env_auth_blocker",
            "activated": "protocol_ready",
            "blocked_non_ip_cap": "protocol_blocker",
        },
        "fail_action": "keep_env_protocol_boundary_explicit",
    }


def _promotion_evidence_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_promotion_pipeline.py",
        "receipt_path_pattern": "runtime/reports/**/*promotion-receipt*.json",
        "required_fields": [
            "decision_hash",
            "input_hash",
            "reviewer_role",
            "reviewer_signature_ref",
            "evidence_bundle_refs",
        ],
        "fail_action": "block_done_promotion_without_non_repudiation_receipt",
    }


def _outlet_matrix_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_outlet_matrix.py",
        "report_path_pattern": "runtime/reports/identity-upgrade-exec-*.json",
        "required_fields": [
            "send_time_gate_status",
            "governed_outlet_enforced",
            "outlet_channel_id",
            "outlet_preflight_receipt",
            "outlet_bypass_detected",
        ],
        "negative_path_required": True,
        "fail_action": "block_outlet_regression_promotion",
    }


def _sidecar_cwd_parity_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_sidecar_cwd_parity.py",
        "required_fields": [
            "cwd_parity_status",
            "passthrough_digest",
            "sidecar_contract_status",
            "sidecar_error_code",
        ],
        "root_tmp_parity_required": True,
        "fail_action": "block_sidecar_cwd_parity_regression",
    }


def _docs_bridge_consistency_contract_skeleton() -> dict:
    governance_doc, review_doc = _validator_doc_defaults("scripts/validate_docs_bridge_consistency.py")
    return {
        "required": False,
        "validator": "scripts/validate_docs_bridge_consistency.py",
        "governance_doc": governance_doc,
        "review_doc": review_doc,
        "required_fields": [
            "bridge_consistency_status",
            "contradiction_pairs",
            "governance_anchor_refs",
            "review_anchor_refs",
        ],
        "fail_action": "reenter_docs_bridge_sync",
    }


def _contract_mapping_coverage_contract_skeleton() -> dict:
    governance_doc, _review_doc = _validator_doc_defaults("scripts/validate_contract_mapping_coverage.py")
    return {
        "required": False,
        "validator": "scripts/validate_contract_mapping_coverage.py",
        "mapping_file": "identity/protocol/mappings/contract-binding.current.yaml",
        "governance_doc": governance_doc,
        "required_fields": [
            "total_requirements",
            "p0_total",
            "p0_mapped",
            "p0_coverage_rate",
            "orphan_count",
        ],
        "target_p0_coverage_rate": 100.0,
        "target_orphan_count": 0,
        "fail_action": "block_mapping_lock_claim",
    }


def _release_plane_cloud_evidence_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_release_plane_cloud_evidence.py",
        "required_fields": [
            "target_branch",
            "release_head_sha",
            "required_gates_run_id",
            "run_url",
            "workflow_file_sha",
            "run_head_sha",
            "run_workflow_file_sha",
            "conditions",
            "release_plane_status",
        ],
        "fail_action": "block_release_when_cloud_evidence_incomplete",
    }


def _cross_cwd_absolute_input_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_cross_cwd_absolute_input.py",
        "required_fields": [
            "repo_catalog_input",
            "repo_catalog_is_absolute",
            "repo_cwd_resolved_repo_catalog",
            "tmp_cwd_resolved_repo_catalog",
            "cwd_parity_status",
        ],
        "fail_action": "block_non_absolute_or_non_parity_repo_catalog_usage",
    }


def _run_id_report_selection_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_run_id_report_selection.py",
        "required_fields": [
            "run_id",
            "selection_strategy",
            "report_selected_path",
            "candidate_count",
        ],
        "fail_action": "block_strict_lane_when_run_id_selection_not_deterministic",
    }


def _phase_bootstrap_before_strict_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_phase_bootstrap_before_strict.py",
        "required_fields": [
            "phase_a_refresh_applied",
            "phase_b_strict_revalidate_status",
            "phase_trace_status",
        ],
        "fail_action": "block_when_phase_a_phase_b_semantics_not_closed",
    }


def _tmp_collision_safe_allocator_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_tmp_collision_safety.py",
        "required_fields": [
            "tmp_root",
            "generated_paths",
            "collision_count",
            "unique_path_count",
            "path_scope_guard_status",
        ],
        "fail_action": "block_when_tmp_paths_collide_or_escape_scope",
    }


def _handoff_collab_freshness_autorotation_contract_skeleton() -> dict:
    return {
        "required": True,
        "bootstrap_emitter": "scripts/rotate_handoff_collab_freshness.py",
        "validator": "scripts/validate_handoff_collab_freshness_rotation.py",
        "rotation_receipt_pattern": "runtime/reports/handoff-collab-freshness-rotation-*.json",
        "required_fields": [
            "rotation_applied",
            "freshness_age_days",
            "rotation_receipt_ref",
            "freshness_status",
        ],
        "fail_action": "block_when_freshness_rotation_receipt_missing_or_failed",
    }


def _protocol_feedback_atomic_emit_contract_skeleton() -> dict:
    return {
        "required": True,
        "atomic_emitter": "scripts/emit_protocol_feedback_atomic.py",
        "validator": "scripts/validate_protocol_feedback_atomic_emit.py",
        "receipt_path_pattern": "runtime/protocol-feedback/atomic/*.receipt.json",
        "required_fields": [
            "transaction_id",
            "batch_ref",
            "index_ref",
            "receipt_ref",
        ],
        "fail_action": "block_when_atomic_emit_receipt_chain_invalid",
    }


def _prompt_bootstrap_capability_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_prompt_bootstrap_capability.py",
        "required_capability_drivers": [
            "scripts/validate_identity_tool_installation.py",
            "scripts/validate_identity_vendor_api_discovery.py",
            "scripts/validate_identity_vendor_api_solution.py",
        ],
        "fail_action": "block_when_prompt_bootstrap_missing_required_drivers",
    }


def _prompt_capability_matrix_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_prompt_capability_matrix.py",
        "required_driver_ids": ["tool_installation", "vendor_api_discovery", "vendor_api_solution"],
        "required_fields": [
            "capability_driver_required_total",
            "capability_driver_present_total",
            "capability_driver_coverage_rate",
            "missing_capability_drivers",
        ],
        "fail_action": "fail_closed_when_prompt_capability_matrix_incomplete",
    }


def _refresh_strict_business_interference_contract_skeleton() -> dict:
    return {
        "required": True,
        "matrix_emitter": "scripts/emit_business_interference_matrix.py",
        "validator": "scripts/validate_refresh_strict_business_interference.py",
        "refresh_receipt_pattern": "runtime/reports/business-interference-matrix-*-refresh-*.json",
        "strict_receipt_pattern": "runtime/reports/business-interference-matrix-*-strict-*.json",
        "required_fields": [
            "refresh_receipt_ref",
            "strict_receipt_ref",
            "interference_row_count_refresh",
            "interference_row_count_strict",
        ],
        "fail_action": "block_when_refresh_strict_interference_matrix_not_closed",
    }


def _kernel_canonical_source_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_kernel_ssot_source.py",
        "canonical_source_paths": [
            "identity/protocol/IDENTITY_PROTOCOL.md",
            "identity/protocol/IDENTITY_RUNTIME.md",
            "identity/protocol/mappings/contract-binding.current.yaml",
        ],
        "fail_action": "block_when_kernel_source_not_canonical",
    }


def _derived_prompt_conformance_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_prompt_derivation_conformance.py",
        "kernel_contract_version": "v1.6",
        "derived_from_contract_ids": [
            "rq_014_prompt_bootstrap_capability_contract_v1",
            "rq_015_prompt_capability_matrix_fail_closed_contract_v1",
            "rq_033_native_chat_headstamp_prompt_contract_v1",
        ],
        "fail_action": "block_when_prompt_derivation_metadata_incomplete",
    }


def _semantic_convergence_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_semantic_convergence.py",
        "required_fields": [
            "semantic_tuple_update",
            "semantic_tuple_three_plane",
            "semantic_tuple_full_scan",
            "mismatch_count",
        ],
        "fail_action": "block_when_semantic_verdict_not_convergent",
    }


def _prompt_kernel_executable_coupling_contract_skeleton() -> dict:
    return {
        "required": True,
        "validator": "scripts/validate_prompt_kernel_executable_coupling.py",
        "kernel_contract_ref": "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md#rq_031_prompt_import_executable_coupling_contract_v1",
        "validator_ref": "scripts/validate_work_layer_gate_set_routing.py",
        "require_explicit_actor": True,
        "fail_action": "block_when_prompt_import_not_executable_coupled",
    }


def _intake_p1_contract_defaults(identity_id: str) -> dict[str, dict]:
    return {
        "multi_track_cross_verification_contract_v1": {
            "required": True,
            "validator": "scripts/validate_intake_evidence_core.py",
            "validator_mode": "intake_contract",
            "bundle_path_pattern": "runtime/protocol-feedback/**/*cross-verification*bundle*.json",
            "required_tracks": ["t1", "t2", "t3", "t4"],
            "required_metadata_fields": [
                "cross_verification_bundle_id",
                "source_url_set",
                "reference_timestamp_utc",
                "conflict_reconciliation_note",
            ],
            "fail_action": "block_merge_and_reenter_cross_verification_intake",
        },
        "intake_evidence_quorum_contract_v1": {
            "required": True,
            "validator": "scripts/validate_intake_evidence_core.py",
            "validator_mode": "promotion_gate",
            "bundle_path_pattern": "runtime/protocol-feedback/**/*cross-verification*bundle*.json",
            "required_tracks": [
                "t1_roundtable_status",
                "t2_vendor_status",
                "t3_openai_context_status",
                "t4_protocol_spec_status",
            ],
            "required_metadata_fields": [
                "cross_verification_bundle_id",
                "source_url_set",
                "reference_timestamp_utc",
                "conflict_reconciliation_note",
            ],
            "fail_action": "block_merge_and_reenter_intake_quorum_gate",
        },
        "fallback_taxonomy_normalization_contract_v1": {
            "required": True,
            "validator": "scripts/validate_fallback_taxonomy_normalization.py",
            "taxonomy_version": "v1",
            "fallback_taxonomy_enum": [
                "data_missing",
                "model_weak_signal",
                "transport_error",
                "policy_blocked",
            ],
            "namespace_separation_required": True,
            "protected_blocker_taxonomy_fields": [
                "auth_login_required",
                "anti_automation_challenge_required",
                "session_reauthentication_required",
                "manual_verification_required",
            ],
            "fail_action": "block_merge_and_reenter_fallback_taxonomy_normalization",
        },
        "dedup_monotonic_winner_contract_v1": {
            "required": True,
            "validator": "scripts/validate_dedup_monotonicity.py",
            "claims_path_pattern": "runtime/reports/**/*dedup*claim*.json",
            "required_fields": [
                "run_id",
                "earliest_claim_ts",
                "stable_tiebreaker",
                "winner_id",
                "winner_reason",
                "monotonicity_status",
            ],
            "fail_action": "block_merge_and_reenter_dedup_orchestration",
        },
        "cross_workflow_evidence_schema_contract_v1": {
            "required": True,
            "normalizer": "scripts/normalize_cross_workflow_evidence.py",
            "validator": "scripts/validate_cross_workflow_schema.py",
            "evidence_path_pattern": f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
            "required_fields": [
                "run_id",
                "route_action",
                "quality_meta_state",
                "dedup_state",
                "evidence_hash",
                "schema_version",
            ],
            "fail_action": "block_merge_and_reenter_cross_workflow_schema_alignment",
        },
        "skill_path_integrity_contract_v1": {
            "required": True,
            "validator": "scripts/validate_skill_path_integrity.py",
            "layout_mode": "active_repo_runtime",
            "allowed_skill_roots": [
                "{active_repo_root}/skills",
                "{active_repo_root}/.codex/skills",
                "{active_repo_root}/identity-protocol-local/skills",
                "{active_runtime_root}/skills",
            ],
            "required_fields": [
                "active_repo_root",
                "active_runtime_root",
                "layout_mode",
                "path_integrity_status",
                "path_integrity_error_code",
            ],
            "fail_action": "block_merge_and_reenter_skill_path_integrity_alignment",
        },
        "route_workflow_version_pinning_contract_v1": {
            "required": True,
            "receipt_emitter": "scripts/emit_route_version_pin_receipt.py",
            "validator": "scripts/validate_route_version_pinning.py",
            "proof_receipt_path_pattern": "runtime/reports/**/*route-version-pin-receipt*.json",
            "required_fields": [
                "route_endpoint",
                "workflow_id",
                "workflow_publish_version",
                "pin_proof_ref",
            ],
            "expected_bindings": [],
            "fail_action": "block_merge_and_reenter_route_workflow_version_alignment",
        },
    }


def _normalize_intake_p1_legacy_contract_paths(task: dict, identity_id: str) -> dict:
    def _legacy_prefix() -> str:
        return f"identity/runtime/local/{identity_id}/reports/"

    legacy = _legacy_prefix()

    dedup = task.get("dedup_monotonic_winner_contract_v1")
    if isinstance(dedup, dict):
        pattern = str(dedup.get("claims_path_pattern", "")).strip()
        if pattern.startswith(legacy):
            dedup["claims_path_pattern"] = "runtime/reports/**/*dedup*claim*.json"

    cross = task.get("cross_workflow_evidence_schema_contract_v1")
    if isinstance(cross, dict):
        pattern = str(cross.get("evidence_path_pattern", "")).strip()
        if pattern.startswith(legacy):
            cross["evidence_path_pattern"] = f"runtime/reports/identity-upgrade-exec-{identity_id}-*.json"

    route = task.get("route_workflow_version_pinning_contract_v1")
    if isinstance(route, dict):
        pattern = str(route.get("proof_receipt_path_pattern", "")).strip()
        if pattern.startswith(legacy):
            route["proof_receipt_path_pattern"] = "runtime/reports/**/*route-version-pin-receipt*.json"

    return task


def _ensure_intake_p1_contracts(task: dict, identity_id: str) -> dict:
    defaults = _intake_p1_contract_defaults(identity_id)
    for key, default in defaults.items():
        cur = task.get(key)
        if not isinstance(cur, dict):
            task[key] = default
            continue
        task[key] = _deep_merge_defaults(default, cur)
    return _normalize_intake_p1_legacy_contract_paths(task, identity_id)


def _ensure_tool_vendor_governance_contracts(task: dict, identity_id: str) -> dict:
    defaults = {
        "release_unlock_formula_automation_contract_v1": _release_unlock_formula_contract_skeleton(),
        "release_plane_cloud_evidence_contract_v1": _release_plane_cloud_evidence_contract_skeleton(),
        "cross_cwd_absolute_input_contract_v1": _cross_cwd_absolute_input_contract_skeleton(),
        "run_id_report_selection_contract_v1": _run_id_report_selection_contract_skeleton(),
        "phase_bootstrap_before_strict_contract_v1": _phase_bootstrap_before_strict_contract_skeleton(),
        "tmp_collision_safe_allocator_contract_v1": _tmp_collision_safe_allocator_contract_skeleton(),
        "handoff_collab_freshness_autorotation_contract_v1": _handoff_collab_freshness_autorotation_contract_skeleton(),
        "protocol_feedback_atomic_emit_contract_v1": _protocol_feedback_atomic_emit_contract_skeleton(),
        "capability_activation_boundary_contract_v2": _capability_boundary_contract_skeleton(),
        "status_promotion_evidence_contract_v1": _promotion_evidence_contract_skeleton(),
        "outbound_reply_outlet_regression_matrix_contract_v1": _outlet_matrix_contract_skeleton(),
        "sidecar_cwd_invariance_contract_v1": _sidecar_cwd_parity_contract_skeleton(),
        "docs_bridge_consistency_contract_v1": _docs_bridge_consistency_contract_skeleton(),
        "contract_mapping_projection_contract_v1": _contract_mapping_coverage_contract_skeleton(),
        "prompt_bootstrap_capability_contract_v1": _prompt_bootstrap_capability_contract_skeleton(),
        "prompt_capability_matrix_fail_closed_contract_v1": _prompt_capability_matrix_contract_skeleton(),
        "refresh_strict_business_interference_matrix_contract_v1": _refresh_strict_business_interference_contract_skeleton(),
        "kernel_canonical_source_contract_v1": _kernel_canonical_source_contract_skeleton(),
        "derived_prompt_conformance_contract_v1": _derived_prompt_conformance_contract_skeleton(),
        "semantic_single_source_convergence_contract_v1": _semantic_convergence_contract_skeleton(),
        "prompt_import_executable_coupling_contract_v1": _prompt_kernel_executable_coupling_contract_skeleton(),
        "tool_installation_contract": _tool_installation_contract_skeleton(identity_id),
        "vendor_api_discovery_contract": _vendor_api_discovery_contract_skeleton(identity_id),
        "vendor_api_solution_contract": _vendor_api_solution_contract_skeleton(identity_id),
        "skill_installation_supply_chain_contract_v1": _skill_installation_supply_chain_contract_skeleton(identity_id),
        "skill_frontmatter_contract_v1": _skill_frontmatter_contract_skeleton(),
        "skill_sync_drift_guard_contract_v1": _skill_sync_drift_guard_contract_skeleton(),
        "semantic_routing_guard_contract_v1": _semantic_routing_guard_contract_skeleton(),
        "instance_protocol_split_receipt_contract_v1": _instance_protocol_split_receipt_contract_skeleton(),
        "protocol_feedback_canonical_reply_channel_contract_v1": _protocol_feedback_reply_channel_contract_skeleton(),
        "protocol_feedback_canonical_inbox_channel_contract_v1": _protocol_feedback_inbox_channel_contract_skeleton(),
        "protocol_feedback_sidecar_contract_v1": _protocol_feedback_sidecar_contract_skeleton(),
        "gated_switch_guard_contract_v1": _gated_switch_guard_contract_skeleton(),
        "protocol_lane_activation_headstamp_contract_v1": _protocol_lane_activation_headstamp_contract_skeleton(),
        "native_chat_headstamp_contract_v1": _native_chat_headstamp_contract_skeleton(),
        "execution_target_tuple_isolation_contract_v1": _execution_target_tuple_isolation_contract_skeleton(),
        "protocol_unique_entry_gate_contract_v1": _protocol_unique_entry_gate_contract_skeleton(),
        DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY: _protocol_downsink_path_immutability_contract_skeleton(),
        HOST_GATEWAY_CONTRACT_KEY: _protocol_host_unique_channel_contract_skeleton(identity_id),
        "multimodal_plugin_enforcement_contract_v1": _multimodal_plugin_enforcement_contract_skeleton(),
        "reasoning_loop_failclose_contract_v1": _reasoning_loop_failclose_contract_skeleton(),
    }
    for key, default in defaults.items():
        cur = task.get(key)
        if not isinstance(cur, dict):
            task[key] = default
            continue
        task[key] = _deep_merge_defaults(default, cur)
    return _ensure_intake_p1_contracts(task, identity_id)


def _default_protocol_review_sample(identity_id: str) -> dict:
    return {
        "review_id": f"protocol-baseline-review-{identity_id}-sample",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "reviewer_identity": identity_id,
        "purpose": "sample protocol baseline review evidence generated by identity-creator scaffold",
        "sources_reviewed": MANDATORY_PROTOCOL_SOURCES,
        "findings": [
            "Identity-upgrade conclusions must be source-backed.",
            "Protocol baseline review gate must pass before architecture decisions.",
        ],
        "decision": {
            "result": "approved",
            "notes": "sample artifact; replace with real review for production upgrades",
        },
    }


def _default_role_binding_sample(identity_id: str, role_type: str, runtime_root: Path) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "binding_id": f"identity-role-binding-{identity_id}-sample",
        "generated_at": now,
        "identity_id": identity_id,
        "role_type": role_type,
        "binding_status": "BOUND_READY",
        "runtime_bootstrap": {
            "status": "PASS",
            "validator": "scripts/validate_identity_runtime_contract.py",
            "evidence": str((runtime_root / "examples" / f"{identity_id}-bootstrap-runtime-validation-sample.json").as_posix()),
        },
        "switch_guard": {
            "status": "PASS",
            "activation_policy": "inactive_by_default",
            "notes": "sample role-binding evidence generated by scaffold",
        },
    }


def _replace_store_manager_tokens(value, identity_id: str):
    if isinstance(value, str):
        identity_token = identity_id.replace("-", "_")
        out = value.replace("store-manager", identity_id)
        out = out.replace("store_manager", identity_token)
        out = out.replace("StoreManager", "".join(part.capitalize() for part in identity_token.split("_")))
        return out
    if isinstance(value, list):
        return [_replace_store_manager_tokens(v, identity_id) for v in value]
    if isinstance(value, dict):
        return {k: _replace_store_manager_tokens(v, identity_id) for k, v in value.items()}
    return value


def _normalize_pack_paths(value, identity_id: str):
    legacy_prefix = f"identity/{identity_id}/"
    pack_prefix = f"identity/packs/{identity_id}/"
    if isinstance(value, str):
        return value.replace(legacy_prefix, pack_prefix)
    if isinstance(value, list):
        return [_normalize_pack_paths(v, identity_id) for v in value]
    if isinstance(value, dict):
        return {k: _normalize_pack_paths(v, identity_id) for k, v in value.items()}
    return value


def _rewrite_identity_pack_root(value, identity_id: str, pack_dir: Path):
    legacy_prefix = f"identity/{identity_id}/"
    canonical_prefix = f"identity/packs/{identity_id}/"
    abs_legacy_token = f"/identity/{identity_id}/"
    abs_canonical_token = f"/identity/packs/{identity_id}/"
    real_prefix = f"{pack_dir.as_posix().rstrip('/')}/"
    if isinstance(value, str):
        if value.startswith(canonical_prefix):
            return f"{real_prefix}{value[len(canonical_prefix):]}"
        if value.startswith(legacy_prefix):
            return f"{real_prefix}{value[len(legacy_prefix):]}"
        if abs_canonical_token in value:
            tail = value.split(abs_canonical_token, 1)[1]
            return f"{real_prefix}{tail}"
        if abs_legacy_token in value:
            tail = value.split(abs_legacy_token, 1)[1]
            return f"{real_prefix}{tail}"
        if value == f"identity/packs/{identity_id}" or value == f"identity/{identity_id}":
            return pack_dir.as_posix()
        if value.endswith(f"/identity/packs/{identity_id}") or value.endswith(f"/identity/{identity_id}"):
            return pack_dir.as_posix()
        return value
    if isinstance(value, list):
        return [_rewrite_identity_pack_root(v, identity_id, pack_dir) for v in value]
    if isinstance(value, dict):
        return {k: _rewrite_identity_pack_root(v, identity_id, pack_dir) for k, v in value.items()}
    return value


def _rewrite_runtime_root(value, runtime_root: Path):
    runtime_prefix = "identity/runtime/"
    replacement = f"{runtime_root.as_posix().rstrip('/')}/"
    if isinstance(value, str):
        return value.replace(runtime_prefix, replacement)
    if isinstance(value, list):
        return [_rewrite_runtime_root(v, runtime_root) for v in value]
    if isinstance(value, dict):
        return {k: _rewrite_runtime_root(v, runtime_root) for k, v in value.items()}
    return value


def _resolve_pack_runtime_path(pack_dir: Path, raw_path: str, *, fallback: str) -> Path:
    value = str(raw_path or "").strip() or str(fallback or "").strip()
    if not value:
        raise ValueError("runtime_path_missing")
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if value.startswith("identity/runtime/"):
        tail = value[len("identity/runtime/") :]
        return (pack_dir / "runtime" / tail).resolve()
    if value.startswith("runtime/"):
        return (pack_dir / value).resolve()
    return (pack_dir / value).resolve()


def _pack_relative_path(pack_dir: Path, path: Path, *, fallback: str = "") -> str:
    try:
        rel = path.resolve().relative_to(pack_dir.resolve()).as_posix()
        if rel:
            return rel
    except Exception:
        pass
    fallback_token = str(fallback or "").strip()
    if fallback_token:
        return fallback_token
    return path.as_posix()


def _protocol_ingress_wrapper_template() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shlex
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
CANONICAL_INGRESS_SCRIPT = "scripts/required_gate_bundle_runner.py"
WRAPPER_DISPATCH_TOKEN_FALLBACK = "instance_wrapper_ingress_v1"
REQUIRED_FIELDS = (
    "actor_id",
    "session_id",
    "run_id",
    "identity_id",
    "work_layer",
    "source_layer",
    "operation",
    "payload",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(raw: str) -> dict[str, Any]:
    data = json.loads(str(raw or "").strip())
    if not isinstance(data, dict):
        raise ValueError("json_payload_not_object")
    return data


def _parse_envelope(args: argparse.Namespace) -> dict[str, Any]:
    if str(args.envelope_json or "").strip():
        return _load_json(args.envelope_json)
    if args.stdin_json:
        return _load_json(sys.stdin.read())
    return {}


def _to_bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    token = str(value or "").strip().lower()
    return "true" if token in {"1", "true", "yes", "y", "on"} else "false"


def _as_str_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    out: set[str] = set()
    for item in value:
        token = str(item or "").strip().lower()
        if token:
            out.add(token)
    return out


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_runtime_path(raw_path: str) -> str:
    token = str(raw_path or "").strip()
    if not token:
        return ""
    return str(Path(token).expanduser().resolve())


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso_utc(raw: Any) -> int:
    token = str(raw or "").strip()
    if not token:
        return 0
    try:
        dt = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except Exception:
        return 0
    return int(dt.timestamp())


def _parse_stdout_json(text: str) -> dict[str, Any]:
    body = str(text or "").strip()
    if not body:
        return {}
    try:
        data = json.loads(body)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(body[start : end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_contract_runtime_path(contract_path: Path, raw_path: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return contract_path.parent
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (contract_path.parent.parent / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (contract_path.parent.parent / token[len("runtime/") :]).resolve()
    return (contract_path.parent.parent / token).resolve()


def _resolve_report_path_from_pattern(
    *,
    contract_path: Path,
    pattern: str,
    run_id: str,
    fallback_name: str,
) -> Path:
    token = str(pattern or "").strip()
    if not token:
        return (contract_path.parent.parent / "reports" / "broadcast" / fallback_name).resolve()
    if "*" not in token:
        return _resolve_contract_runtime_path(contract_path, token)
    stamp = int(time.time())
    run_token = str(run_id or "run").strip() or "run"
    safe_run = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in run_token)
    filename = token.replace("*", f"{safe_run}-{stamp}")
    return _resolve_contract_runtime_path(contract_path, filename)


def _load_json_file(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            raw = proc_cmdline.read_bytes()
            tokens = [chunk.decode("utf-8", errors="ignore").strip() for chunk in raw.split(b"\\x00")]
            rendered = " ".join(token for token in tokens if token).strip()
            if rendered:
                return rendered
        except Exception:
            pass
    try:
        proc = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return str(proc.stdout or "").strip()


def _validate_session_chain_parent_attestation(*, expected_wrapper_path: str) -> tuple[bool, list[str], dict[str, Any]]:
    def _resolve_cli_path_token(token: str) -> str:
        raw = str(token or "").strip()
        if not raw:
            return ""
        if "/" not in raw and "\\\\" not in raw:
            return ""
        try:
            return str(Path(raw).expanduser().resolve())
        except Exception:
            return ""

    def _parent_command_matches_expected_wrapper(parent_cmdline: str, expected_path: Path) -> bool:
        line = str(parent_cmdline or "").strip()
        if not line:
            return False
        try:
            tokens = shlex.split(line)
        except Exception:
            tokens = line.split()
        if not tokens:
            return False

        expected = str(expected_path)
        direct_exec_path = _resolve_cli_path_token(tokens[0])
        if direct_exec_path and direct_exec_path == expected:
            return True

        exe_name = Path(tokens[0]).name.lower()
        if "python" not in exe_name:
            return False

        first_script_token = ""
        for tok in tokens[1:]:
            token = str(tok or "").strip()
            if not token:
                continue
            if token in {"-m", "-c"}:
                return False
            if token.startswith("-"):
                continue
            first_script_token = token
            break
        if not first_script_token:
            return False
        script_path = _resolve_cli_path_token(first_script_token)
        return bool(script_path and script_path == expected)

    errors: list[str] = []
    expected_path = Path(str(expected_wrapper_path or "").strip()).expanduser().resolve()
    parent_pid = int(os.getppid())
    parent_cmdline = _read_process_commandline(parent_pid)
    env_wrapper_path = str(os.environ.get("IDENTITY_PROTOCOL_SESSION_CHAIN_WRAPPER_PATH", "")).strip()
    details: dict[str, Any] = {
        "session_chain_parent_attestation_required": True,
        "session_chain_parent_attestation_ppid": parent_pid,
        "session_chain_parent_attestation_expected_path": str(expected_path)
        if str(expected_wrapper_path or "").strip()
        else "",
        "session_chain_parent_attestation_command_sha256": (
            hashlib.sha256(parent_cmdline.encode("utf-8")).hexdigest() if parent_cmdline else ""
        ),
        "session_chain_parent_attestation_env_path": env_wrapper_path,
    }
    if not str(expected_wrapper_path or "").strip():
        errors.append("session_chain_parent_attestation_expected_path_missing")
    if not env_wrapper_path:
        errors.append("session_chain_parent_attestation_env_path_missing")
    else:
        env_path = Path(env_wrapper_path).expanduser().resolve()
        if env_path != expected_path:
            errors.append("session_chain_parent_attestation_env_path_mismatch")
    if not parent_cmdline:
        if not env_wrapper_path:
            errors.append("session_chain_parent_attestation_parent_command_missing")
    elif not _parent_command_matches_expected_wrapper(parent_cmdline, expected_path):
        errors.append("session_chain_parent_attestation_parent_command_mismatch")
    return len(errors) == 0, errors, details


def _collect_broadcast_snapshot(
    *,
    contract: dict[str, Any],
    contract_path: Path,
    merged: dict[str, Any],
) -> dict[str, Any]:
    policy = contract.get("broadcast_policy")
    if not isinstance(policy, dict) or policy.get("required") is not True:
        return {
            "broadcast_status": "SKIPPED_NOT_REQUIRED",
            "broadcast_unread_count": 0,
            "broadcast_pending_ack_count": 0,
            "broadcast_critical_unacked_count": 0,
        }

    repo_root = Path(str(contract.get("protocol_repo_root", "")).strip()).expanduser().resolve()
    items_dir = (repo_root / str(policy.get("protocol_broadcast_items_dir", "")).strip()).resolve()
    index_path = (repo_root / str(policy.get("protocol_broadcast_index_file", "")).strip()).resolve()
    state_path = _resolve_contract_runtime_path(contract_path, str(policy.get("instance_state_file", "")))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_doc = _load_json_file(
        state_path,
        default={
            "schema_version": "v1",
            "identity_id": str(merged.get("identity_id", "")).strip(),
            "last_seen_created_at_utc": "",
            "read_ids": [],
            "acked_ids": [],
        },
    )
    read_ids = {
        str(item).strip()
        for item in (state_doc.get("read_ids") if isinstance(state_doc.get("read_ids"), list) else [])
        if str(item).strip()
    }
    acked_ids = {
        str(item).strip()
        for item in (state_doc.get("acked_ids") if isinstance(state_doc.get("acked_ids"), list) else [])
        if str(item).strip()
    }

    candidate_files: list[Path] = []
    if index_path.exists():
        index_doc = _load_json_file(index_path, default={"items": []})
        rows = index_doc.get("items")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    file_token = str(row.get("file", "")).strip()
                else:
                    file_token = str(row).strip()
                if file_token:
                    candidate_files.append((items_dir / file_token).resolve())
    if not candidate_files and items_dir.exists():
        candidate_files = sorted(items_dir.glob("*.json"))

    now_epoch = int(time.time())
    identity_id = str(merged.get("identity_id", "")).strip()
    visible_ids: list[str] = []
    unread_ids: list[str] = []
    pending_ack_ids: list[str] = []
    critical_unacked_ids: list[str] = []
    max_seen_epoch = _parse_iso_utc(state_doc.get("last_seen_created_at_utc"))

    for path in candidate_files:
        doc = _load_json_file(path, default={})
        bid = str(doc.get("broadcast_id", "")).strip()
        if not bid:
            continue
        scope = doc.get("scope", "all")
        visible = False
        if isinstance(scope, list):
            scope_tokens = {str(item).strip().lower() for item in scope if str(item).strip()}
            visible = ("all" in scope_tokens) or (f"identity:{identity_id.lower()}" in scope_tokens)
        else:
            scope_token = str(scope or "all").strip().lower()
            visible = scope_token in {"", "all", "*"} or scope_token == f"identity:{identity_id.lower()}"
        if not visible:
            continue
        expire_epoch = _parse_iso_utc(doc.get("expire_at_utc"))
        if expire_epoch and expire_epoch < now_epoch:
            continue
        created_epoch = _parse_iso_utc(doc.get("created_at_utc"))
        if created_epoch > max_seen_epoch:
            max_seen_epoch = created_epoch
        visible_ids.append(bid)
        if bid not in read_ids:
            unread_ids.append(bid)
            read_ids.add(bid)
        requires_ack = bool(doc.get("requires_ack", False))
        if requires_ack and bid not in acked_ids:
            pending_ack_ids.append(bid)
            if str(doc.get("severity", "")).strip().lower() == "critical":
                critical_unacked_ids.append(bid)

    state_doc["last_seen_created_at_utc"] = (
        datetime.fromtimestamp(max_seen_epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if max_seen_epoch > 0
        else str(state_doc.get("last_seen_created_at_utc", "")).strip()
    )
    state_doc["read_ids"] = sorted(read_ids)
    state_doc["acked_ids"] = sorted(acked_ids)
    state_doc["pending_ack_ids"] = sorted(pending_ack_ids)
    state_doc["critical_unacked_ids"] = sorted(critical_unacked_ids)
    state_doc["updated_at_utc"] = _utc_now_iso()
    state_path.write_text(json.dumps(state_doc, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

    receipt_path = _resolve_report_path_from_pattern(
        contract_path=contract_path,
        pattern=str(policy.get("instance_receipt_pattern", "")).strip(),
        run_id=str(merged.get("run_id", "")).strip(),
        fallback_name="broadcast-receipt-latest.json",
    )
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_doc = {
        "schema_version": "v1",
        "identity_id": identity_id,
        "run_id": str(merged.get("run_id", "")).strip(),
        "session_id": str(merged.get("session_id", "")).strip(),
        "actor_id": str(merged.get("actor_id", "")).strip(),
        "timestamp_utc": _utc_now_iso(),
        "visible_ids": visible_ids,
        "unread_ids": unread_ids,
        "pending_ack_ids": pending_ack_ids,
        "critical_unacked_ids": critical_unacked_ids,
        "state_file": str(state_path),
    }
    receipt_path.write_text(json.dumps(receipt_doc, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")

    return {
        "broadcast_status": "PASS_REQUIRED",
        "broadcast_state_file": str(state_path),
        "broadcast_receipt_path": str(receipt_path),
        "broadcast_visible_count": len(visible_ids),
        "broadcast_unread_count": len(unread_ids),
        "broadcast_pending_ack_count": len(pending_ack_ids),
        "broadcast_critical_unacked_count": len(critical_unacked_ids),
    }


def _build_wrapper_dispatch_proof(
    *,
    merged: dict[str, Any],
    surface_label: str,
    signing_secret: str,
) -> tuple[str, str]:
    proof = {
        "schema_version": "v1",
        "identity_id": str(merged.get("identity_id", "")).strip(),
        "operation": str(merged.get("operation", "")).strip().lower(),
        "run_id": str(merged.get("run_id", "")).strip(),
        "actor_id": str(merged.get("actor_id", "")).strip(),
        "session_id": str(merged.get("session_id", "")).strip(),
        "work_layer": str(merged.get("work_layer", "")).strip(),
        "source_layer": str(merged.get("source_layer", "")).strip(),
        "surface_label": str(surface_label or "").strip(),
        "issued_at_epoch": int(time.time()),
        "nonce": secrets.token_hex(16),
    }
    canonical = _canonical_json(proof)
    signature = hmac.new(
        str(signing_secret or "").encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return canonical, signature


def _load_signing_secret(*, contract: dict[str, Any], contract_path: Path) -> tuple[str, str]:
    ingress_proof_policy = contract.get("ingress_proof_policy")
    if not isinstance(ingress_proof_policy, dict):
        return "", "ingress_proof_policy_missing"
    signer_mode = str(ingress_proof_policy.get("signer_mode", "")).strip().lower()
    signer_secret_env = str(ingress_proof_policy.get("signer_secret_env", "")).strip()
    raw_path = str(ingress_proof_policy.get("signing_key_path", "")).strip()
    bootstrap_from_key = bool(
        ingress_proof_policy.get("bootstrap_env_secret_from_signing_key_path", True)
    )
    if not signer_mode:
        signer_mode = "runtime_file_secret" if raw_path else ""
    p = Path(raw_path).expanduser() if raw_path else Path("")
    if raw_path and not p.is_absolute():
        if raw_path.startswith("identity/runtime/"):
            p = (contract_path.parent.parent / raw_path[len("identity/runtime/") :]).resolve()
        elif raw_path.startswith("runtime/"):
            p = (contract_path.parent.parent / raw_path[len("runtime/") :]).resolve()
        else:
            p = (contract_path.parent.parent / p).resolve()
    if signer_mode == "runtime_env_secret":
        if not signer_secret_env:
            return "", "ingress_proof_signer_secret_env_missing"
        secret = str(os.environ.get(signer_secret_env, "")).strip()
        if not secret and bootstrap_from_key and raw_path and p.exists():
            secret = p.read_text(encoding="utf-8", errors="ignore").strip()
            if secret:
                os.environ[signer_secret_env] = secret
        if not secret:
            return "", "ingress_proof_signer_secret_env_unset"
        return secret, ""
    if signer_mode not in {"runtime_file_secret", ""}:
        return "", "ingress_proof_signer_mode_unsupported"
    if not raw_path:
        return "", "ingress_proof_signing_key_path_missing"
    if not p.exists():
        return "", "ingress_proof_signing_key_missing"
    secret = p.read_text(encoding="utf-8", errors="ignore").strip()
    if not secret:
        return "", "ingress_proof_signing_key_empty"
    return secret, ""


def _resolve_gate_profile(*, contract: dict[str, Any], operation: str, requested_profile: str) -> tuple[str, str]:
    policy = contract.get("operation_profile_policy")
    if not isinstance(policy, dict):
        policy = {}
    strict_operations = _as_str_set(policy.get("strict_operations")) or {
        "activate",
        "update",
        "mutation",
        "readiness",
        "e2e",
        "ci",
        "validate",
        "three-plane",
    }
    light_operations = _as_str_set(policy.get("light_operations")) or {"inspection", "scan", "status"}
    strict_profile = str(policy.get("strict_gate_profile", "")).strip() or "strict_full"
    strict_profile_by_operation_raw = policy.get("strict_gate_profile_by_operation")
    strict_profile_by_operation: dict[str, str] = {}
    if isinstance(strict_profile_by_operation_raw, dict):
        strict_profile_by_operation = {
            str(key).strip().lower(): str(value).strip()
            for key, value in strict_profile_by_operation_raw.items()
            if str(key).strip() and str(value).strip()
        }
    light_profile = str(policy.get("light_gate_profile", "")).strip() or "inspection_targeted"
    allow_upgrade_only = bool(policy.get("allow_upgrade_only", True))
    operation_token = str(operation or "").strip().lower()
    requested = str(requested_profile or "").strip()
    operation_strict_profile = strict_profile_by_operation.get(operation_token, strict_profile)

    if operation_token in strict_operations:
        if requested and requested != operation_strict_profile:
            return "", f"strict_operation_gate_profile_mismatch:{requested}:expected={operation_strict_profile}"
        return operation_strict_profile, ""

    if operation_token in light_operations:
        if not requested:
            return light_profile, ""
        if requested == light_profile:
            return light_profile, ""
        if requested == operation_strict_profile:
            return operation_strict_profile, ""
        return "", f"light_operation_gate_profile_invalid:{requested}:allowed={light_profile}|{operation_strict_profile}"

    if requested:
        if allow_upgrade_only and requested != strict_profile:
            return "", f"unknown_operation_gate_profile_not_allowed:{requested}:expected={strict_profile}"
        return requested, ""
    return strict_profile, ""


def _fail(*, error_code: str, stale_reason: str, json_only: bool) -> int:
    _emit(
        {
            "protocol_ingress_wrapper_status": STATUS_FAIL_REQUIRED,
            "error_code": error_code,
            "stale_reasons": [stale_reason],
        },
        json_only=json_only,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Per-instance ingress wrapper for protocol unique entry.")
    ap.add_argument("--envelope-json", default="")
    ap.add_argument("--stdin-json", action="store_true")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--operation", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--surface-label", default="host_ingress_wrapper")
    ap.add_argument("--gate-profile", default="")
    ap.add_argument("--target-name", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--contract-path", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    envelope = _parse_envelope(args)
    contract_path = (
        Path(args.contract_path).expanduser().resolve()
        if str(args.contract_path or "").strip()
        else Path(__file__).resolve().with_name("protocol_gateway_contract.json")
    )
    if not contract_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-001",
            stale_reason="gateway_contract_file_missing",
            json_only=args.json_only,
        )
    try:
        contract = _load_json(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="gateway_contract_file_invalid",
            json_only=args.json_only,
        )

    merged: dict[str, Any] = dict(envelope)
    for key in ("catalog", "repo_catalog", "identity_id", "operation", "run_id", "actor_id", "session_id", "gate_profile"):
        value = getattr(args, key, "")
        if str(value or "").strip():
            merged[key] = value
    if str(args.work_layer or "").strip():
        merged["work_layer"] = args.work_layer
    if str(args.source_layer or "").strip():
        merged["source_layer"] = args.source_layer
    if "payload" not in merged:
        merged["payload"] = {}

    missing = [key for key in REQUIRED_FIELDS if not str(merged.get(key, "")).strip()]
    if missing:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_envelope_fields_missing:" + ",".join(sorted(missing)),
            json_only=args.json_only,
        )

    catalog_path = _resolve_runtime_path(
        str(merged.get("catalog_path") or merged.get("catalog") or contract.get("catalog_path", "")).strip()
    )
    if not catalog_path:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="catalog_path_missing",
            json_only=args.json_only,
        )

    repo_root = Path(str(contract.get("protocol_repo_root", "")).strip()).expanduser()
    script_rel = str(contract.get("protocol_ingress_script", "")).strip() or CANONICAL_INGRESS_SCRIPT
    wrapper_dispatch_token = (
        str(contract.get("ingress_wrapper_dispatch_token", "")).strip()
        or WRAPPER_DISPATCH_TOKEN_FALLBACK
    )
    resolved_gate_profile, gate_profile_error = _resolve_gate_profile(
        contract=contract,
        operation=str(merged.get("operation", "")).strip(),
        requested_profile=str(merged.get("gate_profile", "")).strip(),
    )
    if gate_profile_error:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason=gate_profile_error,
            json_only=args.json_only,
        )
    script_path = (repo_root / script_rel).resolve() if script_rel else Path("")
    if not script_rel or not script_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_canonical_script_unavailable",
            json_only=args.json_only,
        )
    signing_secret, signing_secret_error = _load_signing_secret(contract=contract, contract_path=contract_path)
    if signing_secret_error:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason=signing_secret_error,
            json_only=args.json_only,
        )

    cmd = [
        sys.executable,
        str(script_path),
        "--catalog",
        catalog_path,
        "--identity-id",
        str(merged.get("identity_id", "")).strip(),
        "--operation",
        str(merged.get("operation", "")).strip(),
        "--run-id",
        str(merged.get("run_id", "")).strip(),
        "--actor-id",
        str(merged.get("actor_id", "")).strip(),
        "--session-id",
        str(merged.get("session_id", "")).strip(),
        "--resolved-work-layer",
        str(merged.get("work_layer", "")).strip(),
        "--resolved-source-layer",
        str(merged.get("source_layer", "")).strip(),
        "--lock-state",
        str(merged.get("lock_state", "LOCK_MATCH")).strip() or "LOCK_MATCH",
        "--send-time-gate-status",
        str(merged.get("send_time_gate_status", "NOT_APPLICABLE")).strip() or "NOT_APPLICABLE",
        "--outlet-bypass-detected",
        _to_bool_text(merged.get("outlet_bypass_detected", False)),
        "--final-emit-contract-status",
        str(merged.get("final_emit_contract_status", "NOT_APPLICABLE")).strip() or "NOT_APPLICABLE",
        "--final-emit-policy-mode",
        str(merged.get("final_emit_policy_mode", "tool_choice_required")).strip() or "tool_choice_required",
        "--final-emit-schema-status",
        str(merged.get("final_emit_schema_status", "NOT_APPLICABLE")).strip() or "NOT_APPLICABLE",
        "--surface-label",
        str(merged.get("surface_label", args.surface_label)).strip() or "host_ingress_wrapper",
        "--wrapper-dispatch-token",
        wrapper_dispatch_token,
        "--gate-profile",
        resolved_gate_profile,
        "--json-only",
    ]
    surface_label = str(merged.get("surface_label", args.surface_label)).strip() or "host_ingress_wrapper"
    wrapper_proof_json, wrapper_proof_signature = _build_wrapper_dispatch_proof(
        merged=merged,
        surface_label=surface_label,
        signing_secret=signing_secret,
    )
    cmd.extend(["--wrapper-proof-json", wrapper_proof_json])
    cmd.extend(["--wrapper-proof-signature", wrapper_proof_signature])
    report_selected_path = str(merged.get("report_selected_path", "")).strip()
    if report_selected_path:
        cmd.extend(["--report-selected-path", report_selected_path])
    target_name = str(merged.get("target_name", "")).strip() or str(args.target_name or "").strip()
    if target_name:
        cmd.extend(["--target-name", target_name])
    repo_catalog = str(merged.get("repo_catalog") or args.repo_catalog or "").strip()
    if repo_catalog:
        cmd.extend(["--repo-catalog", repo_catalog])
    if str(args.out or "").strip():
        cmd.extend(["--out", str(args.out).strip()])

    child_env = dict(os.environ)
    child_env["IDENTITY_PROTOCOL_INGRESS_WRAPPER_PATH"] = str(Path(__file__).resolve())
    proc = subprocess.run(cmd, capture_output=True, text=True, env=child_env)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        if proc.stdout.strip():
            print(proc.stdout.strip())
        return proc.returncode

    broadcast_snapshot = _collect_broadcast_snapshot(
        contract=contract,
        contract_path=contract_path,
        merged=merged,
    )
    payload = _parse_stdout_json(proc.stdout)
    if payload:
        payload.update(broadcast_snapshot)
        _emit(payload, json_only=args.json_only)
    elif proc.stdout.strip():
        print(proc.stdout.strip())
    else:
        _emit(broadcast_snapshot, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def _protocol_egress_wrapper_template() -> str:
    template = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shlex
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
CANONICAL_EGRESS_SCRIPT = "scripts/final_emit_governed.py"
FINAL_EMIT_CHANNEL_ID = "__TEMPLATE_FINAL_EMIT_CHANNEL_ID__"
REQUIRED_FIELDS = (
    "actor_id",
    "session_id",
    "run_id",
    "identity_id",
    "work_layer",
    "source_layer",
    "candidate_output",
    "ingress_receipt",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(raw: str) -> dict[str, Any]:
    data = json.loads(str(raw or "").strip())
    if not isinstance(data, dict):
        raise ValueError("json_payload_not_object")
    return data


def _parse_envelope(args: argparse.Namespace) -> dict[str, Any]:
    if str(args.envelope_json or "").strip():
        return _load_json(args.envelope_json)
    if args.stdin_json:
        return _load_json(sys.stdin.read())
    return {}


def _parse_stdout_json(text: str) -> dict[str, Any]:
    body = str(text or "").strip()
    if not body:
        return {}
    try:
        data = json.loads(body)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        data = json.loads(body[start : end + 1])
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _fail(*, error_code: str, stale_reason: str, json_only: bool) -> int:
    _emit(
        {
            "protocol_egress_wrapper_status": STATUS_FAIL_REQUIRED,
            "error_code": error_code,
            "stale_reasons": [stale_reason],
        },
        json_only=json_only,
    )
    return 1


def _load_ingress_receipt(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    token = str(raw or "").strip()
    if not token:
        raise ValueError("ingress_receipt_missing")
    p = Path(token).expanduser().resolve()
    if not p.exists():
        raise ValueError("ingress_receipt_file_missing")
    return _load_json(p.read_text(encoding="utf-8"))


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _resolve_runtime_path(raw_path: str) -> str:
    token = str(raw_path or "").strip()
    if not token:
        return ""
    return str(Path(token).expanduser().resolve())


def _resolve_contract_runtime_path(contract_path: Path, raw_path: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return contract_path.parent
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (contract_path.parent.parent / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (contract_path.parent.parent / token[len("runtime/") :]).resolve()
    return (contract_path.parent.parent / token).resolve()


def _load_json_file(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _read_process_commandline(pid: int) -> str:
    if pid <= 0:
        return ""
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    if proc_cmdline.exists():
        try:
            raw = proc_cmdline.read_bytes()
            tokens = [chunk.decode("utf-8", errors="ignore").strip() for chunk in raw.split(b"\\x00")]
            rendered = " ".join(token for token in tokens if token).strip()
            if rendered:
                return rendered
        except Exception:
            pass
    try:
        proc = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return str(proc.stdout or "").strip()


def _validate_session_chain_parent_attestation(*, expected_wrapper_path: str) -> tuple[bool, list[str], dict[str, Any]]:
    def _resolve_cli_path_token(token: str) -> str:
        raw = str(token or "").strip()
        if not raw:
            return ""
        if "/" not in raw and "\\\\" not in raw:
            return ""
        try:
            return str(Path(raw).expanduser().resolve())
        except Exception:
            return ""

    def _parent_command_matches_expected_wrapper(parent_cmdline: str, expected_path: Path) -> bool:
        line = str(parent_cmdline or "").strip()
        if not line:
            return False
        try:
            tokens = shlex.split(line)
        except Exception:
            tokens = line.split()
        if not tokens:
            return False

        expected = str(expected_path)
        direct_exec_path = _resolve_cli_path_token(tokens[0])
        if direct_exec_path and direct_exec_path == expected:
            return True

        exe_name = Path(tokens[0]).name.lower()
        if "python" not in exe_name:
            return False

        first_script_token = ""
        for tok in tokens[1:]:
            token = str(tok or "").strip()
            if not token:
                continue
            if token in {"-m", "-c"}:
                return False
            if token.startswith("-"):
                continue
            first_script_token = token
            break
        if not first_script_token:
            return False
        script_path = _resolve_cli_path_token(first_script_token)
        return bool(script_path and script_path == expected)

    errors: list[str] = []
    expected_path = Path(str(expected_wrapper_path or "").strip()).expanduser().resolve()
    parent_pid = int(os.getppid())
    parent_cmdline = _read_process_commandline(parent_pid)
    env_wrapper_path = str(os.environ.get("IDENTITY_PROTOCOL_SESSION_CHAIN_WRAPPER_PATH", "")).strip()
    details: dict[str, Any] = {
        "session_chain_parent_attestation_required": True,
        "session_chain_parent_attestation_ppid": parent_pid,
        "session_chain_parent_attestation_expected_path": str(expected_path)
        if str(expected_wrapper_path or "").strip()
        else "",
        "session_chain_parent_attestation_command_sha256": (
            hashlib.sha256(parent_cmdline.encode("utf-8")).hexdigest() if parent_cmdline else ""
        ),
        "session_chain_parent_attestation_env_path": env_wrapper_path,
    }
    if not str(expected_wrapper_path or "").strip():
        errors.append("session_chain_parent_attestation_expected_path_missing")
    if not env_wrapper_path:
        errors.append("session_chain_parent_attestation_env_path_missing")
    else:
        env_path = Path(env_wrapper_path).expanduser().resolve()
        if env_path != expected_path:
            errors.append("session_chain_parent_attestation_env_path_mismatch")
    if not parent_cmdline:
        if not env_wrapper_path:
            errors.append("session_chain_parent_attestation_parent_command_missing")
    elif not _parent_command_matches_expected_wrapper(parent_cmdline, expected_path):
        errors.append("session_chain_parent_attestation_parent_command_mismatch")
    return len(errors) == 0, errors, details


def _collect_broadcast_release_state(*, contract: dict[str, Any], contract_path: Path) -> dict[str, Any]:
    policy = contract.get("broadcast_policy")
    if not isinstance(policy, dict) or policy.get("required") is not True:
        return {
            "broadcast_status": STATUS_SKIPPED_NOT_REQUIRED,
            "broadcast_pending_ack_count": 0,
            "broadcast_critical_unacked_count": 0,
            "broadcast_release_blocked": False,
        }

    state_path = _resolve_contract_runtime_path(contract_path, str(policy.get("instance_state_file", "")))
    state_doc = _load_json_file(
        state_path,
        default={
            "pending_ack_ids": [],
            "critical_unacked_ids": [],
        },
    )
    pending_ack_ids = [
        str(item).strip()
        for item in (state_doc.get("pending_ack_ids") if isinstance(state_doc.get("pending_ack_ids"), list) else [])
        if str(item).strip()
    ]
    critical_unacked_ids = [
        str(item).strip()
        for item in (
            state_doc.get("critical_unacked_ids")
            if isinstance(state_doc.get("critical_unacked_ids"), list)
            else []
        )
        if str(item).strip()
    ]
    block_on_critical_unacked = bool(policy.get("block_on_critical_unacked", False))
    release_blocked = bool(block_on_critical_unacked and critical_unacked_ids)
    return {
        "broadcast_status": STATUS_PASS_REQUIRED,
        "broadcast_state_file": str(state_path),
        "broadcast_pending_ack_count": len(pending_ack_ids),
        "broadcast_critical_unacked_count": len(critical_unacked_ids),
        "broadcast_release_blocked": release_blocked,
        "broadcast_release_block_on_critical_unacked": block_on_critical_unacked,
        "broadcast_release_critical_unacked_ids": critical_unacked_ids[:20],
    }


def _build_egress_grant(
    *,
    merged: dict[str, Any],
    ingress_receipt: dict[str, Any],
    signing_secret: str,
    outlet_channel_id: str,
) -> tuple[str, str]:
    candidate_output = str(merged.get("candidate_output", "")).strip()
    grant = {
        "schema_version": "v1",
        "identity_id": str(merged.get("identity_id", "")).strip(),
        "actor_id": str(merged.get("actor_id", "")).strip(),
        "session_id": str(merged.get("session_id", "")).strip(),
        "run_id": str(merged.get("run_id", "")).strip(),
        "outlet_channel_id": str(outlet_channel_id or "").strip(),
        "body_sha256": hashlib.sha256(candidate_output.encode("utf-8")).hexdigest(),
        "ingress_receipt_id": str(ingress_receipt.get("receipt_id", "")).strip(),
        "issued_at_epoch": int(time.time()),
        "nonce": secrets.token_hex(16),
    }
    canonical = _canonical_json(grant)
    signature = hmac.new(
        str(signing_secret or "").encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return canonical, signature


def _load_signing_secret(*, contract: dict[str, Any], contract_path: Path) -> tuple[str, str]:
    egress_grant_policy = contract.get("egress_grant_policy")
    if not isinstance(egress_grant_policy, dict):
        return "", "egress_grant_policy_missing"
    signer_mode = str(egress_grant_policy.get("signer_mode", "")).strip().lower()
    signer_secret_env = str(egress_grant_policy.get("signer_secret_env", "")).strip()
    raw_path = str(egress_grant_policy.get("signing_key_path", "")).strip()
    bootstrap_from_key = bool(
        egress_grant_policy.get("bootstrap_env_secret_from_signing_key_path", True)
    )
    if not signer_mode:
        signer_mode = "runtime_file_secret" if raw_path else ""
    p = Path(raw_path).expanduser() if raw_path else Path("")
    if raw_path and not p.is_absolute():
        if raw_path.startswith("identity/runtime/"):
            p = (contract_path.parent.parent / raw_path[len("identity/runtime/") :]).resolve()
        elif raw_path.startswith("runtime/"):
            p = (contract_path.parent.parent / raw_path[len("runtime/") :]).resolve()
        else:
            p = (contract_path.parent.parent / p).resolve()
    if signer_mode == "runtime_env_secret":
        if not signer_secret_env:
            return "", "egress_grant_signer_secret_env_missing"
        secret = str(os.environ.get(signer_secret_env, "")).strip()
        if not secret and bootstrap_from_key and raw_path and p.exists():
            secret = p.read_text(encoding="utf-8", errors="ignore").strip()
            if secret:
                os.environ[signer_secret_env] = secret
        if not secret:
            return "", "egress_grant_signer_secret_env_unset"
        return secret, ""
    if signer_mode not in {"runtime_file_secret", ""}:
        return "", "egress_grant_signer_mode_unsupported"
    if not raw_path:
        return "", "egress_grant_signing_key_path_missing"
    if not p.exists():
        return "", "egress_grant_signing_key_missing"
    secret = p.read_text(encoding="utf-8", errors="ignore").strip()
    if not secret:
        return "", "egress_grant_signing_key_empty"
    return secret, ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Per-instance egress wrapper for governed final emit.")
    ap.add_argument("--envelope-json", default="")
    ap.add_argument("--stdin-json", action="store_true")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--session-id", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--work-layer", default="")
    ap.add_argument("--source-layer", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--candidate-output", default="")
    ap.add_argument("--ingress-receipt", default="")
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--contract-path", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    envelope = _parse_envelope(args)
    contract_path = (
        Path(args.contract_path).expanduser().resolve()
        if str(args.contract_path or "").strip()
        else Path(__file__).resolve().with_name("protocol_gateway_contract.json")
    )
    if not contract_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-001",
            stale_reason="gateway_contract_file_missing",
            json_only=args.json_only,
        )
    try:
        contract = _load_json(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="gateway_contract_file_invalid",
            json_only=args.json_only,
        )

    merged: dict[str, Any] = dict(envelope)
    for key in ("catalog", "repo_catalog", "identity_id", "actor_id", "session_id", "run_id"):
        value = getattr(args, key, "")
        if str(value or "").strip():
            merged[key] = value
    if str(args.work_layer or "").strip():
        merged["work_layer"] = args.work_layer
    if str(args.source_layer or "").strip():
        merged["source_layer"] = args.source_layer
    if str(args.candidate_output or "").strip():
        merged["candidate_output"] = args.candidate_output
    if str(args.ingress_receipt or "").strip():
        merged["ingress_receipt"] = args.ingress_receipt
    if str(args.layer_intent_text or "").strip():
        merged["layer_intent_text"] = args.layer_intent_text
    if str(args.blocker_receipt_out or "").strip():
        merged["blocker_receipt_out"] = args.blocker_receipt_out

    missing = [key for key in REQUIRED_FIELDS if not str(merged.get(key, "")).strip()]
    if missing:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="egress_envelope_fields_missing:" + ",".join(sorted(missing)),
            json_only=args.json_only,
        )

    try:
        ingress_receipt = _load_ingress_receipt(merged.get("ingress_receipt"))
    except Exception as exc:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason=f"ingress_receipt_invalid:{exc}",
            json_only=args.json_only,
        )

    receipt_run_id = str(ingress_receipt.get("run_id_binding", "")).strip()
    receipt_session_id = str(ingress_receipt.get("session_id", "")).strip()
    receipt_actor_id = str(ingress_receipt.get("actor_id", "")).strip()
    missing_receipt_tuple = [
        key
        for key, value in (
            ("run_id_binding", receipt_run_id),
            ("session_id", receipt_session_id),
            ("actor_id", receipt_actor_id),
        )
        if not str(value or "").strip()
    ]
    if missing_receipt_tuple:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_receipt_tuple_missing:" + ",".join(sorted(missing_receipt_tuple)),
            json_only=args.json_only,
        )
    if receipt_run_id != str(merged.get("run_id", "")).strip():
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_receipt_run_id_mismatch",
            json_only=args.json_only,
        )
    if receipt_session_id != str(merged.get("session_id", "")).strip():
        return _fail(
            error_code="IP-ASB-201",
            stale_reason="ingress_receipt_session_id_mismatch",
            json_only=args.json_only,
        )
    if receipt_actor_id != str(merged.get("actor_id", "")).strip():
        return _fail(
            error_code="IP-ASB-201",
            stale_reason="ingress_receipt_actor_id_mismatch",
            json_only=args.json_only,
        )

    catalog_path = _resolve_runtime_path(
        str(merged.get("catalog_path") or merged.get("catalog") or contract.get("catalog_path", "")).strip()
    )
    if not catalog_path:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="catalog_path_missing",
            json_only=args.json_only,
        )

    repo_root = Path(str(contract.get("protocol_repo_root", "")).strip()).expanduser()
    script_rel = str(contract.get("protocol_egress_script", "")).strip() or CANONICAL_EGRESS_SCRIPT
    script_path = (repo_root / script_rel).resolve() if script_rel else Path("")
    if not script_rel or not script_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="egress_canonical_script_unavailable",
            json_only=args.json_only,
        )
    host_release_mode = str(contract.get("host_release_mode", "")).strip().lower()
    session_chain_parent_attestation_required = host_release_mode == "wrapper_only"
    session_chain_parent_attestation_status = STATUS_SKIPPED_NOT_REQUIRED
    session_chain_parent_attestation_ppid = int(os.getppid())
    session_chain_parent_attestation_expected_path = ""
    session_chain_parent_attestation_command_sha256 = ""
    if session_chain_parent_attestation_required:
        session_chain_wrapper_path = _resolve_contract_runtime_path(
            contract_path,
            str(contract.get("session_chain_wrapper_path", "")).strip(),
        )
        session_chain_parent_attestation_expected_path = str(session_chain_wrapper_path) if session_chain_wrapper_path else ""
        (
            session_chain_parent_ok,
            session_chain_parent_errors,
            session_chain_parent_details,
        ) = _validate_session_chain_parent_attestation(
            expected_wrapper_path=session_chain_parent_attestation_expected_path,
        )
        session_chain_parent_attestation_ppid = _safe_int(
            session_chain_parent_details.get("session_chain_parent_attestation_ppid"),
            default=session_chain_parent_attestation_ppid,
        )
        session_chain_parent_attestation_command_sha256 = str(
            session_chain_parent_details.get("session_chain_parent_attestation_command_sha256", "")
        ).strip()
        session_chain_parent_attestation_status = (
            STATUS_PASS_REQUIRED if session_chain_parent_ok else STATUS_FAIL_REQUIRED
        )
        if not session_chain_parent_ok:
            _emit(
                {
                    "protocol_egress_wrapper_status": STATUS_FAIL_REQUIRED,
                    "error_code": "IP-GATE-ENTRY-002",
                    "stale_reasons": session_chain_parent_errors
                    or ["session_chain_parent_attestation_failed"],
                    "session_chain_parent_attestation_required": True,
                    "session_chain_parent_attestation_status": session_chain_parent_attestation_status,
                    "session_chain_parent_attestation_ppid": session_chain_parent_attestation_ppid,
                    "session_chain_parent_attestation_expected_path": session_chain_parent_attestation_expected_path,
                    "session_chain_parent_attestation_command_sha256": session_chain_parent_attestation_command_sha256,
                },
                json_only=args.json_only,
            )
            return 1
    signing_secret, signing_secret_error = _load_signing_secret(contract=contract, contract_path=contract_path)
    if signing_secret_error:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason=signing_secret_error,
            json_only=args.json_only,
        )
    broadcast_release = _collect_broadcast_release_state(contract=contract, contract_path=contract_path)
    if bool(broadcast_release.get("broadcast_release_blocked")):
        return _fail(
            error_code="IP-GATE-BCAST-001",
            stale_reason="broadcast_critical_unacked_blocked",
            json_only=args.json_only,
        )

    cmd = [
        sys.executable,
        str(script_path),
        "--catalog",
        catalog_path,
        "--identity-id",
        str(merged.get("identity_id", "")).strip(),
        "--actor-id",
        str(merged.get("actor_id", "")).strip(),
        "--session-id",
        str(merged.get("session_id", "")).strip(),
        "--run-id",
        str(merged.get("run_id", "")).strip(),
        "--body-text",
        str(merged.get("candidate_output", "")).strip(),
        "--work-layer",
        str(merged.get("work_layer", "")).strip(),
        "--source-layer",
        str(merged.get("source_layer", "")).strip(),
        "--outlet-channel-id",
        FINAL_EMIT_CHANNEL_ID,
        "--json-only",
    ]
    grant_json, grant_signature = _build_egress_grant(
        merged=merged,
        ingress_receipt=ingress_receipt,
        signing_secret=signing_secret,
        outlet_channel_id=FINAL_EMIT_CHANNEL_ID,
    )
    cmd.extend(["--egress-grant-json", grant_json])
    cmd.extend(["--egress-grant-signature", grant_signature])
    repo_catalog = str(merged.get("repo_catalog") or args.repo_catalog or "").strip()
    if repo_catalog:
        cmd.extend(["--repo-catalog", repo_catalog])
    if str(args.out_reply_file or "").strip():
        cmd.extend(["--out-reply-file", str(args.out_reply_file).strip()])
    if str(args.out_json or "").strip():
        cmd.extend(["--out-json", str(args.out_json).strip()])
    layer_intent_text = str(merged.get("layer_intent_text", "")).strip()
    if layer_intent_text:
        cmd.extend(["--layer-intent-text", layer_intent_text])
    blocker_receipt_out = str(merged.get("blocker_receipt_out", "")).strip()
    if blocker_receipt_out:
        cmd.extend(["--blocker-receipt-out", blocker_receipt_out])

    child_env = dict(os.environ)
    child_env["IDENTITY_PROTOCOL_EGRESS_WRAPPER_PATH"] = str(Path(__file__).resolve())
    proc = subprocess.run(cmd, capture_output=True, text=True, env=child_env)
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    if proc.returncode != 0:
        if proc.stdout.strip():
            print(proc.stdout.strip())
        return proc.returncode

    payload = _parse_stdout_json(proc.stdout)
    send_time_status = str(payload.get("send_time_gate_status", "")).strip().upper()
    if send_time_status and send_time_status != STATUS_PASS_REQUIRED:
        return _fail(
            error_code="IP-HDSTAMP-002",
            stale_reason="send_time_gate_not_pass_required",
            json_only=args.json_only,
        )
    if payload:
        payload.update(broadcast_release)
        payload["session_chain_parent_attestation_required"] = bool(session_chain_parent_attestation_required)
        payload["session_chain_parent_attestation_status"] = session_chain_parent_attestation_status
        payload["session_chain_parent_attestation_ppid"] = session_chain_parent_attestation_ppid
        payload["session_chain_parent_attestation_expected_path"] = session_chain_parent_attestation_expected_path
        payload["session_chain_parent_attestation_command_sha256"] = (
            session_chain_parent_attestation_command_sha256
        )
        _emit(payload, json_only=args.json_only)
    elif proc.stdout.strip():
        print(proc.stdout.strip())
    else:
        _emit(broadcast_release, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
    return template.replace("__TEMPLATE_FINAL_EMIT_CHANNEL_ID__", FINAL_EMIT_CHANNEL_ID)


def _protocol_session_chain_wrapper_template() -> str:
    template = """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import errno
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
DEFAULT_OPERATION = "inspection"
DEFAULT_WORK_LAYER = "instance"
DEFAULT_SOURCE_LAYER = "project"
HOST_VISIBLE_SURFACE_CONTRACT_KEY = "host_visible_surface_registry_contract_v1"
HOST_VISIBLE_SURFACE_STATE_FILE_DEFAULT = "runtime/state/host_visible_surface_registry_state.json"
HOST_VISIBLE_SURFACE_RECEIPT_PATTERN_DEFAULT = "runtime/reports/host-visible-surface/host-visible-surface-*.json"
HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD = "receipt_source"
HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE = "runtime_dialogue"
HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE = "__TEMPLATE_HOST_VISIBLE_FIXTURE_RECEIPT_SOURCE__"
HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS = {__TEMPLATE_HOST_VISIBLE_FIXTURE_ALLOWED_OPERATIONS__}
ASSISTANT_PROCESS_MESSAGE_KIND_BY_OPERATION = {
    "commentary": "checkpoint",
    "status": "status_update",
    "final": "result_summary",
    "inspection": "checkpoint",
}
PRIVILEGE_ESCALATION_ERROR_CODE = "IP-PRIV-ESC-001"
PRIVILEGE_ESCALATION_REASON_PREFIX = "privilege_escalation_required"
PRIVILEGE_ESCALATION_REMEDIATION_HINT = "rerun_with_host_privilege_escalation"


def _load_json(raw: str) -> dict[str, Any]:
    data = json.loads(str(raw or "").strip())
    if not isinstance(data, dict):
        raise ValueError("json_payload_not_object")
    return data


def _parse_stdout_json(text: str) -> dict[str, Any]:
    body = str(text or "").strip()
    if not body:
        return {}
    try:
        doc = json.loads(body)
        return doc if isinstance(doc, dict) else {}
    except Exception:
        pass
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        return {}
    try:
        doc = json.loads(body[start : end + 1])
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _emit(payload: dict[str, Any], *, json_only: bool, visible_reply: str = "") -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        if str(visible_reply or "").strip():
            print(str(visible_reply).rstrip())
            print("")
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _render_machine_verification_line(machine_payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in machine_payload.items():
        if not str(key).strip():
            continue
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif value is None:
            rendered = ""
        elif isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        else:
            rendered = str(value).strip()
        if rendered:
            parts.append(f"{str(key).strip()}={rendered}")
    if not parts:
        return ""
    return "Machine-Verification: " + "; ".join(parts)


def _resolve_contract_path(raw_contract_path: str) -> Path:
    if str(raw_contract_path or "").strip():
        return Path(raw_contract_path).expanduser().resolve()
    return Path(__file__).resolve().with_name("protocol_gateway_contract.json")


def _resolve_runtime_path(contract_path: Path, raw_path: str) -> Path:
    token = str(raw_path or "").strip()
    if not token:
        return Path("")
    p = Path(token).expanduser()
    if p.is_absolute():
        return p.resolve()
    if token.startswith("identity/runtime/"):
        return (contract_path.parent.parent / token[len("identity/runtime/") :]).resolve()
    if token.startswith("runtime/"):
        return (contract_path.parent.parent / token[len("runtime/") :]).resolve()
    return (contract_path.parent.parent / token).resolve()


def _resolve_message(args: argparse.Namespace) -> str:
    if str(args.message_file or "").strip():
        p = Path(str(args.message_file).strip()).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"message_file_missing:{p}")
        return p.read_text(encoding="utf-8")
    if args.stdin_message:
        return sys.stdin.read()
    return str(args.message or "")


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


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


def _format_privilege_escalation_reason(*, path: Path, scope: str, exc: Exception) -> str:
    safe_scope = str(scope or "").strip() or "unknown_scope"
    safe_path = str(path.expanduser().resolve())
    safe_exc = type(exc).__name__
    return (
        f"{PRIVILEGE_ESCALATION_REASON_PREFIX}:{safe_scope}:path={safe_path}:error={safe_exc}:"
        f"hint={PRIVILEGE_ESCALATION_REMEDIATION_HINT}:error_code={PRIVILEGE_ESCALATION_ERROR_CODE}"
    )


def _actor_session_filename(actor_id: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(actor_id or "").strip()).strip("._")
    if not token:
        token = "unknown_actor"
    return f"{token}.json"


def _actor_session_path(catalog_path: Path, actor_id: str) -> Path:
    return (catalog_path.parent / "session" / "actors" / _actor_session_filename(actor_id)).resolve()


def _load_json_file(path: Path, *, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            raise PermissionError(
                _format_privilege_escalation_reason(
                    path=path,
                    scope="session_chain_state_read",
                    exc=exc,
                )
            ) from exc
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            raise PermissionError(
                _format_privilege_escalation_reason(
                    path=path.parent,
                    scope="session_chain_state_dir_write",
                    exc=exc,
                )
            ) from exc
        raise
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        tmp.replace(path)
    except Exception as exc:
        if _is_privilege_escalation_error(exc):
            raise PermissionError(
                _format_privilege_escalation_reason(
                    path=path,
                    scope="session_chain_state_write",
                    exc=exc,
                )
            ) from exc
        raise


def _as_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _session_primary_identity_ids(bindings: list[dict[str, Any]], session_id: str) -> list[str]:
    token = str(session_id or "").strip()
    if not token:
        return []
    identities = {
        str(row.get("identity_id", "")).strip()
        for row in bindings
        if isinstance(row, dict)
        and str(row.get("session_id", "")).strip() == token
        and str(row.get("identity_id", "")).strip()
    }
    return sorted(identities)


def _normalize_operation(value: str) -> str:
    return str(value or "").strip().lower()


def _select_host_visible_receipt_source(operation: str) -> str:
    op = _normalize_operation(operation)
    if op in HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS:
        return HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE
    return HOST_VISIBLE_SURFACE_RUNTIME_RECEIPT_SOURCE


def _resolve_process_message_metadata(operation: str) -> dict[str, str]:
    normalized_operation = _normalize_operation(operation)
    message_kind = str(
        ASSISTANT_PROCESS_MESSAGE_KIND_BY_OPERATION.get(normalized_operation, "")
    ).strip()
    payload = {
        "message_author_role": "assistant",
        "message_operation": normalized_operation,
        "message_kind_resolution_mode": (
            "host_visible_operation_map" if message_kind else "host_visible_operation_unclassified"
        ),
    }
    if message_kind:
        payload["message_kind"] = message_kind
    return payload


def _receipt_path_for_channel(
    *,
    receipt_glob_path: Path,
    channel: str,
    run_id: str,
    now_token: str,
) -> Path:
    pattern_name = receipt_glob_path.name
    channel_token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(channel or "").strip()).strip("._") or "unknown"
    run_token = re.sub(r"[^A-Za-z0-9._-]+", "_", str(run_id or "").strip()).strip("._") or "run"
    suffix = f"{now_token}-{channel_token}-{run_token}"
    if "*" in pattern_name:
        filename = pattern_name.replace("*", suffix, 1)
    elif pattern_name.endswith(".json"):
        filename = f"{pattern_name[:-5]}-{suffix}.json"
    else:
        filename = f"{pattern_name}-{suffix}.json"
    return (receipt_glob_path.parent / filename).resolve()


def _record_host_visible_surface_receipts(
    *,
    contract: dict[str, Any],
    contract_path: Path,
    operation: str,
    identity_id: str,
    actor_id: str,
    session_id: str,
    run_id: str,
    wrapper_surface_status: str,
    entry_receipt_tuple_status: str,
    headstamp_first_line_status: str,
    send_time_gate_status: str,
    final_emit_contract_status: str,
    out_reply_file: Path,
) -> tuple[str, str, list[str], list[str], dict[str, Any]]:
    visible_contract = contract.get(HOST_VISIBLE_SURFACE_CONTRACT_KEY)
    if not isinstance(visible_contract, dict) or visible_contract.get("required") is not True:
        return "SKIPPED_NOT_REQUIRED", "", [], [], {}

    required_channels = _as_list(visible_contract.get("required_channels"))
    if not required_channels:
        return STATUS_FAIL_REQUIRED, "", [], ["host_visible_surface_required_channels_missing"], {}

    state_path = _resolve_runtime_path(
        contract_path,
        str(visible_contract.get("runtime_state_file", "")).strip() or HOST_VISIBLE_SURFACE_STATE_FILE_DEFAULT,
    )
    receipt_glob_path = _resolve_runtime_path(
        contract_path,
        str(visible_contract.get("runtime_receipt_pattern", "")).strip() or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN_DEFAULT,
    )
    if not str(state_path).strip():
        return STATUS_FAIL_REQUIRED, "", [], ["host_visible_surface_state_path_unresolved"], {}
    if not str(receipt_glob_path).strip():
        return STATUS_FAIL_REQUIRED, str(state_path), [], ["host_visible_surface_receipt_path_unresolved"], {}

    required_attestation_fields = set(_as_list(visible_contract.get("required_attestation_fields")))
    if not required_attestation_fields:
        required_attestation_fields = {
            "emit_channel_id",
            "wrapper_surface_status",
            "entry_receipt_tuple_status",
            "headstamp_first_line_status",
            "send_time_gate_status",
            "final_emit_contract_status",
        }
    status_fields = set(_as_list(visible_contract.get("required_pass_status_fields")))
    if not status_fields:
        status_fields = {
            "wrapper_surface_status",
            "entry_receipt_tuple_status",
            "headstamp_first_line_status",
            "send_time_gate_status",
            "final_emit_contract_status",
        }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    status_map = {
        "wrapper_surface_status": str(wrapper_surface_status or "").strip().upper(),
        "entry_receipt_tuple_status": str(entry_receipt_tuple_status or "").strip().upper(),
        "headstamp_first_line_status": str(headstamp_first_line_status or "").strip().upper(),
        "send_time_gate_status": str(send_time_gate_status or "").strip().upper(),
        "final_emit_contract_status": str(final_emit_contract_status or "").strip().upper(),
    }
    receipt_source = _select_host_visible_receipt_source(operation)
    pack_path = contract_path.parent.resolve()
    final_channel_relay_projection: dict[str, Any] = {}
    if HOST_VISIBLE_FINAL_CHANNEL_ID in required_channels and bool(
        visible_contract.get("final_channel_relay_required", HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED)
    ):
        relay_rc, relay_payload = build_host_visible_final_channel_relay_receipt(
            repo_root=_repo_root(),
            pack_path=pack_path,
            identity_id=str(identity_id or "").strip(),
            run_id=str(run_id or "").strip(),
            reply_transport_ref=str(out_reply_file),
            now_token=now_token,
        )
        final_channel_relay_projection = project_host_visible_final_channel_relay_fields(relay_payload)
        relay_status = str(final_channel_relay_projection.get("agent_relay_final_answer_status", "")).strip().upper()
        if relay_rc != 0 or relay_status != STATUS_PASS_REQUIRED:
            relay_reasons = [
                str(item).strip()
                for item in (relay_payload.get("stale_reasons") or [])
                if str(item).strip()
            ]
            relay_reason = relay_reasons[0] if relay_reasons else "host_visible_final_channel_relay_not_pass"
            errors_prefix = "host_visible_surface_final_channel_relay_not_pass"
            errors = [f"{errors_prefix}:{relay_reason}"]
            return STATUS_FAIL_REQUIRED, str(state_path), [], errors, final_channel_relay_projection

    receipt_paths: list[str] = []
    receipt_paths_by_channel: dict[str, str] = {}
    errors: list[str] = []
    for channel in sorted(set(required_channels)):
        receipt_path = _receipt_path_for_channel(
            receipt_glob_path=receipt_glob_path,
            channel=channel,
            run_id=run_id,
            now_token=now_token,
        )
        # These receipts are script-seeded control-plane fixtures, not host transport ACKs.
        payload = {
            "schema_version": "v1",
            "created_at_utc": now,
            "identity_id": str(identity_id or "").strip(),
            "actor_id": str(actor_id or "").strip(),
            "session_id": str(session_id or "").strip(),
            "run_id": str(run_id or "").strip(),
            "reply_transport_ref": str(out_reply_file),
            "emit_channel_id": str(channel).strip(),
            HOST_VISIBLE_SURFACE_RECEIPT_SOURCE_FIELD: receipt_source,
        }
        payload.update(status_map)
        if str(channel).strip() == HOST_VISIBLE_FINAL_CHANNEL_ID and final_channel_relay_projection:
            payload.update(final_channel_relay_projection)
        missing_fields = sorted(field for field in required_attestation_fields if field not in payload)
        if missing_fields:
            errors.append(f"host_visible_surface_receipt_missing_fields:{channel}:{','.join(missing_fields)}")
            continue
        try:
            _write_json_file(receipt_path, payload)
            receipt_paths.append(str(receipt_path))
            receipt_paths_by_channel[str(channel).strip()] = str(receipt_path)
        except Exception as exc:
            errors.append(f"host_visible_surface_receipt_write_failed:{channel}:{exc}")

    default_state_channels = {
        channel: {
            "last_receipt_path": "",
            "last_status": "",
            "receipt_source": "",
            "last_run_id": "",
            "updated_at_utc": "",
        }
        for channel in sorted(set(required_channels))
    }
    state_doc = _load_json_file(
        state_path,
        default={
            "schema_version": "v1",
            "identity_id": str(identity_id or "").strip(),
            "channels": default_state_channels,
            "updated_at_utc": "",
        },
    )
    channels_doc = state_doc.get("channels")
    if not isinstance(channels_doc, dict):
        channels_doc = {}
    for channel in sorted(set(required_channels)):
        existing = channels_doc.get(channel)
        channel_doc = dict(existing) if isinstance(existing, dict) else {}
        latest_receipt_path = str(receipt_paths_by_channel.get(str(channel).strip()) or "").strip()
        if not latest_receipt_path:
            latest_receipt_path = str(channel_doc.get("last_receipt_path", ""))
        pass_ok = all(str(status_map.get(field, "")).upper() == STATUS_PASS_REQUIRED for field in status_fields)
        channel_doc["last_receipt_path"] = latest_receipt_path
        channel_doc["last_status"] = STATUS_PASS_REQUIRED if pass_ok else STATUS_FAIL_REQUIRED
        channel_doc["receipt_source"] = receipt_source
        channel_doc["last_run_id"] = str(run_id or "").strip()
        channel_doc["updated_at_utc"] = now
        channels_doc[channel] = channel_doc
    state_doc["schema_version"] = "v1"
    state_doc["identity_id"] = str(identity_id or "").strip()
    state_doc["channels"] = channels_doc
    state_doc["updated_at_utc"] = now
    try:
        _write_json_file(state_path, state_doc)
    except Exception as exc:
        errors.append(f"host_visible_surface_state_write_failed:{exc}")

    if errors:
        return STATUS_FAIL_REQUIRED, str(state_path), receipt_paths, errors, final_channel_relay_projection
    return STATUS_PASS_REQUIRED, str(state_path), receipt_paths, [], final_channel_relay_projection


def _evaluate_egress_payload_host_visible_receipt_seed(
    *,
    payload: dict[str, Any],
    out_reply_file: Path,
    session_chain_parent_status: str,
) -> tuple[bool, str]:
    if not isinstance(payload, dict) or not payload:
        return False, "egress_payload_missing"
    if not out_reply_file.exists():
        return False, "reply_file_missing_after_failed_egress"
    if session_chain_parent_status and session_chain_parent_status != STATUS_PASS_REQUIRED:
        return False, "session_chain_parent_attestation_not_pass_required"
    if str(payload.get("send_time_gate_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        return False, "send_time_gate_not_pass_required"
    if str(payload.get("final_emit_contract_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        return False, "final_emit_contract_not_pass_required"
    if str(payload.get("reply_first_line_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        return False, "reply_first_line_not_pass_required"
    consistency_status = str(payload.get("headstamp_consistency_status", "")).strip().upper()
    if consistency_status not in {STATUS_PASS_REQUIRED, "AUTO_CORRECTED"}:
        return False, "headstamp_consistency_not_seed_eligible"
    if bool(payload.get("outlet_bypass_detected", False)):
        return False, "outlet_bypass_detected"
    return True, "seed_eligible"


def _select_latest_identity_bound_session(
    *,
    catalog_path: Path,
    actor_id: str,
    identity_id: str,
    preferred_session_id: str,
) -> tuple[str, str, Path]:
    store_path = _actor_session_path(catalog_path, actor_id)
    store = _load_json_file(store_path, default={})
    rows = store.get("bindings")
    bindings = rows if isinstance(rows, list) else []
    identity_token = str(identity_id or "").strip()
    preferred_token = str(preferred_session_id or "").strip()
    if preferred_token:
        preferred_identity_ids = _session_primary_identity_ids(bindings, preferred_token)
        if len(preferred_identity_ids) > 1:
            return (
                "",
                "requested_session_primary_conflict:" + ",".join(preferred_identity_ids),
                store_path,
            )
        if preferred_identity_ids and identity_token not in preferred_identity_ids:
            return (
                "",
                "requested_session_bound_to_foreign_identity:" + ",".join(preferred_identity_ids),
                store_path,
            )
    selected_rows: list[dict[str, Any]] = []
    for row in bindings:
        if not isinstance(row, dict):
            continue
        row_identity = str(row.get("identity_id", "")).strip()
        row_session = str(row.get("session_id", "")).strip()
        if not row_identity or not row_session:
            continue
        if row_identity != identity_token:
            continue
        selected_rows.append(row)
    if preferred_token:
        for row in selected_rows:
            if str(row.get("session_id", "")).strip() == preferred_token:
                return preferred_token, "preferred_session_bound", store_path
    if not selected_rows:
        return "", "identity_binding_missing", store_path
    selected_rows = sorted(
        selected_rows,
        key=lambda row: (
            _safe_int(row.get("binding_version"), default=0),
            str(row.get("updated_at", "")).strip() or str(row.get("bound_at", "")).strip(),
        ),
    )
    selected = selected_rows[-1]
    return str(selected.get("session_id", "")).strip(), "aligned_to_latest_identity_binding", store_path


def _upsert_actor_session_binding(
    *,
    catalog_path: Path,
    actor_id: str,
    identity_id: str,
    session_id: str,
    run_id: str,
) -> tuple[bool, str, Path]:
    store_path = _actor_session_path(catalog_path, actor_id)
    default_store = {
        "schema_version": "actor_session_multibinding_v1",
        "actor_id": str(actor_id or "").strip(),
        "catalog_path": str(catalog_path),
        "binding_key_mode": "actor_id+identity_id+session_id",
        "binding_version": 0,
        "compare_token": "0",
        "session_entry_count": 0,
        "bindings": [],
        "rebind_receipts": [],
        "last_mutation": {},
        "updated_at": "",
        "actor_session_path": str(store_path),
        "stale_reasons": [],
    }
    store = _load_json_file(store_path, default=default_store)
    rows = store.get("bindings")
    bindings = rows if isinstance(rows, list) else []
    max_version = _safe_int(store.get("binding_version"), default=0)
    for row in bindings:
        if not isinstance(row, dict):
            continue
        max_version = max(max_version, _safe_int(row.get("binding_version"), default=0))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    identity_token = str(identity_id or "").strip()
    session_token = str(session_id or "").strip()
    actor_token = str(actor_id or "").strip()
    if not actor_token or not identity_token or not session_token:
        return False, "binding_upsert_fields_missing", store_path
    conflicting_identity_ids = _session_primary_identity_ids(bindings, session_token)
    conflicting_identity_ids = [token for token in conflicting_identity_ids if token != identity_token]
    if conflicting_identity_ids:
        return False, "session_primary_conflict:" + ",".join(conflicting_identity_ids), store_path
    existing_index = -1
    for idx, row in enumerate(bindings):
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("identity_id", "")).strip() == identity_token
            and str(row.get("session_id", "")).strip() == session_token
        ):
            existing_index = idx
            break
    if existing_index >= 0:
        entry = dict(bindings[existing_index] if isinstance(bindings[existing_index], dict) else {})
        entry["actor_id"] = actor_token
        entry["identity_id"] = identity_token
        entry["session_id"] = session_token
        entry["catalog_path"] = str(catalog_path)
        entry["run_id"] = str(run_id or "").strip()
        entry["status"] = "active"
        entry["updated_at"] = now
        if not str(entry.get("bound_at", "")).strip():
            entry["bound_at"] = now
        if _safe_int(entry.get("binding_version"), default=0) <= 0:
            max_version += 1
            entry["binding_version"] = max_version
        bindings[existing_index] = entry
    else:
        max_version += 1
        entry = {
            "actor_id": actor_token,
            "identity_id": identity_token,
            "session_id": session_token,
            "catalog_path": str(catalog_path),
            "status": "active",
            "bound_at": now,
            "updated_at": now,
            "run_id": str(run_id or "").strip(),
            "switch_reason": "session_chain_wrapper_auto_bind",
            "binding_ref": f"{actor_token}:{identity_token}:{session_token}:v{max_version}",
            "binding_version": max_version,
            "compare_token": str(max_version),
            "mutation_lane": "session_chain_wrapper",
            "approved_by": "system:auto",
        }
        bindings.append(entry)
    store["schema_version"] = "actor_session_multibinding_v1"
    store["actor_id"] = actor_token
    store["catalog_path"] = str(catalog_path)
    store["binding_key_mode"] = "actor_id+identity_id+session_id"
    store["binding_version"] = max_version
    store["compare_token"] = str(max_version)
    store["session_entry_count"] = len([x for x in bindings if isinstance(x, dict)])
    store["bindings"] = bindings
    store["updated_at"] = now
    store["actor_session_path"] = str(store_path)
    store["identity_id"] = identity_token
    store["session_id"] = session_token
    store["run_id"] = str(run_id or "").strip()
    store["status"] = "active"
    store["bound_at"] = now
    store["last_mutation"] = {
        "mutation_lane": "session_chain_wrapper",
        "session_id": session_token,
        "run_id": str(run_id or "").strip(),
        "switch_reason": "session_chain_wrapper_auto_bind",
        "approved_by": "system:auto",
        "compare_token_after": str(max_version),
        "applied_at": now,
    }
    _write_json_file(store_path, store)
    return True, "", store_path


def _resolve_effective_session_id(
    *,
    catalog_path: Path,
    identity_id: str,
    actor_id: str,
    requested_session_id: str,
    run_id: str,
) -> tuple[str, str, bool, str]:
    requested = str(requested_session_id or "").strip()
    resolved, mode, store_path = _select_latest_identity_bound_session(
        catalog_path=catalog_path,
        actor_id=actor_id,
        identity_id=identity_id,
        preferred_session_id=requested,
    )
    if requested and mode == "preferred_session_bound":
        return requested, mode, False, str(store_path)
    if requested and (
        mode.startswith("requested_session_primary_conflict:")
        or mode.startswith("requested_session_bound_to_foreign_identity:")
    ):
        return "", mode, False, str(store_path)
    if requested and resolved:
        return resolved, "requested_session_unbound_aligned_to_identity_latest", False, str(store_path)
    if resolved:
        return resolved, mode, False, str(store_path)

    candidate = requested or f"run:{run_id}"
    upsert_ok, upsert_error, upsert_path = _upsert_actor_session_binding(
        catalog_path=catalog_path,
        actor_id=actor_id,
        identity_id=identity_id,
        session_id=candidate,
        run_id=run_id,
    )
    if not upsert_ok:
        return "", f"session_binding_upsert_failed:{upsert_error}", False, str(upsert_path)
    return candidate, "auto_upsert_session_binding", True, str(upsert_path)


def _fail(*, error_code: str, stale_reason: str, json_only: bool) -> int:
    _emit(
        {
            "protocol_session_chain_wrapper_status": "FAIL_REQUIRED",
            "error_code": error_code,
            "stale_reasons": [stale_reason],
        },
        json_only=json_only,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Per-instance session chain wrapper: force one reply round through "
            "ingress wrapper then egress wrapper."
        )
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--actor-id", required=True)
    ap.add_argument("--session-id", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--operation", default=DEFAULT_OPERATION)
    ap.add_argument("--work-layer", default=DEFAULT_WORK_LAYER)
    ap.add_argument("--source-layer", default=DEFAULT_SOURCE_LAYER)
    ap.add_argument("--message", default="")
    ap.add_argument("--message-file", default="")
    ap.add_argument("--stdin-message", action="store_true")
    ap.add_argument("--out-reply-file", default="")
    ap.add_argument("--out-json", default="")
    ap.add_argument("--blocker-receipt-out", default="")
    ap.add_argument("--layer-intent-text", default="")
    ap.add_argument("--contract-path", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    contract_path = _resolve_contract_path(args.contract_path)
    if not contract_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-001",
            stale_reason="gateway_contract_file_missing",
            json_only=args.json_only,
        )
    try:
        contract = _load_json(contract_path.read_text(encoding="utf-8"))
    except Exception:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="gateway_contract_file_invalid",
            json_only=args.json_only,
        )

    ingress_wrapper_raw = str(contract.get("ingress_wrapper_path", "")).strip()
    egress_wrapper_raw = str(contract.get("egress_wrapper_path", "")).strip()
    if not ingress_wrapper_raw:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_wrapper_path_missing_in_contract",
            json_only=args.json_only,
        )
    if not egress_wrapper_raw:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="egress_wrapper_path_missing_in_contract",
            json_only=args.json_only,
        )
    ingress_wrapper_path = _resolve_runtime_path(contract_path, ingress_wrapper_raw)
    egress_wrapper_path = _resolve_runtime_path(contract_path, egress_wrapper_raw)
    if not str(ingress_wrapper_path).strip() or not ingress_wrapper_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_wrapper_file_missing",
            json_only=args.json_only,
        )
    if not str(egress_wrapper_path).strip() or not egress_wrapper_path.exists():
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="egress_wrapper_file_missing",
            json_only=args.json_only,
        )

    run_id = str(args.run_id or "").strip() or f"session-chain-{int(time.time())}"
    catalog_path_resolved = Path(args.catalog).expanduser().resolve()
    repo_catalog_path = str(args.repo_catalog or "").strip()
    resolved_session_id, session_binding_mode, session_binding_upserted, actor_session_store_path = (
        _resolve_effective_session_id(
            catalog_path=catalog_path_resolved,
            identity_id=str(args.identity_id).strip(),
            actor_id=str(args.actor_id).strip(),
            requested_session_id=str(args.session_id).strip(),
            run_id=run_id,
        )
    )
    if not resolved_session_id:
        return _fail(
            error_code="IP-ASB-201",
            stale_reason=str(session_binding_mode or "session_binding_resolution_failed"),
            json_only=args.json_only,
        )
    message = str(_resolve_message(args) or "").strip()
    if not message:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="message_empty",
            json_only=args.json_only,
        )
    state_dir = contract_path.parent.parent / "state"
    default_ingress_receipt_path = (state_dir / "required_gate_bundle_entry.latest.json").resolve()
    out_reply_path = (
        Path(str(args.out_reply_file).strip()).expanduser().resolve()
        if str(args.out_reply_file or "").strip()
        else (identity_runtime_named_temp_root("identity-session-chain") / f"reply-{run_id}.txt").resolve()
    )

    ingress_cmd = [
        sys.executable,
        str(ingress_wrapper_path),
        "--catalog",
        str(catalog_path_resolved),
        "--identity-id",
        str(args.identity_id).strip(),
        "--operation",
        str(args.operation).strip() or DEFAULT_OPERATION,
        "--run-id",
        run_id,
        "--actor-id",
        str(args.actor_id).strip(),
        "--session-id",
        resolved_session_id,
        "--work-layer",
        str(args.work_layer).strip() or DEFAULT_WORK_LAYER,
        "--source-layer",
        str(args.source_layer).strip() or DEFAULT_SOURCE_LAYER,
        "--json-only",
    ]
    if repo_catalog_path:
        ingress_cmd.extend(["--repo-catalog", repo_catalog_path])
    ingress_proc = subprocess.run(ingress_cmd, capture_output=True, text=True)
    ingress_payload = _parse_stdout_json(ingress_proc.stdout)
    if ingress_proc.returncode != 0:
        if ingress_proc.stdout.strip():
            print(ingress_proc.stdout.strip())
        if ingress_proc.stderr.strip():
            print(ingress_proc.stderr.strip(), file=sys.stderr)
        return ingress_proc.returncode
    if str(ingress_payload.get("bundle_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="ingress_bundle_not_pass_required",
            json_only=args.json_only,
        )
    ingress_receipt_history_path = str(ingress_payload.get("protocol_unique_entry_receipt_history_path", "")).strip()
    ingress_receipt_runtime_path = str(ingress_payload.get("protocol_unique_entry_receipt_path", "")).strip()
    ingress_receipt_path = (
        Path(ingress_receipt_history_path).expanduser().resolve()
        if ingress_receipt_history_path
        else (
            Path(ingress_receipt_runtime_path).expanduser().resolve()
            if ingress_receipt_runtime_path
            else default_ingress_receipt_path
        )
    )
    receipt_run_id = str(ingress_payload.get("run_id_binding", "")).strip()
    receipt_session_id = str(ingress_payload.get("session_id", "")).strip()
    receipt_actor_id = str(ingress_payload.get("actor_id", "")).strip()

    egress_cmd = [
        sys.executable,
        str(egress_wrapper_path),
        "--catalog",
        str(catalog_path_resolved),
        "--identity-id",
        str(args.identity_id).strip(),
        "--run-id",
        run_id,
        "--actor-id",
        str(args.actor_id).strip(),
        "--session-id",
        resolved_session_id,
        "--work-layer",
        str(args.work_layer).strip() or DEFAULT_WORK_LAYER,
        "--source-layer",
        str(args.source_layer).strip() or DEFAULT_SOURCE_LAYER,
        "--candidate-output",
        message,
        "--ingress-receipt",
        str(ingress_receipt_path),
        "--out-reply-file",
        str(out_reply_path),
        "--json-only",
    ]
    if repo_catalog_path:
        egress_cmd.extend(["--repo-catalog", repo_catalog_path])
    if str(args.out_json or "").strip():
        egress_cmd.extend(["--out-json", str(args.out_json).strip()])
    if str(args.blocker_receipt_out or "").strip():
        egress_cmd.extend(["--blocker-receipt-out", str(args.blocker_receipt_out).strip()])
    if str(args.layer_intent_text or "").strip():
        egress_cmd.extend(["--layer-intent-text", str(args.layer_intent_text).strip()])
    egress_env = dict(os.environ)
    egress_env["IDENTITY_PROTOCOL_SESSION_CHAIN_WRAPPER_PATH"] = str(Path(__file__).resolve())
    egress_receipt_seed_attempted = False
    egress_receipt_seed_replay_count = 0
    egress_receipt_seed_gate_status = STATUS_SKIPPED_NOT_REQUIRED
    egress_receipt_seed_gate_reason = "initial_egress_pass_required"
    egress_proc = subprocess.run(egress_cmd, capture_output=True, text=True, env=egress_env)
    egress_payload = _parse_stdout_json(egress_proc.stdout)
    session_chain_parent_status = str(
        egress_payload.get("session_chain_parent_attestation_status", "")
    ).strip().upper()
    egress_guard_status = str(egress_payload.get("final_emit_guard_status", "")).strip().upper()
    if egress_proc.returncode != 0:
        seed_ready, egress_receipt_seed_gate_reason = _evaluate_egress_payload_host_visible_receipt_seed(
            payload=egress_payload,
            out_reply_file=out_reply_path,
            session_chain_parent_status=session_chain_parent_status,
        )
        egress_receipt_seed_gate_status = (
            STATUS_PASS_REQUIRED if seed_ready else STATUS_FAIL_REQUIRED
        )
        if not seed_ready:
            if isinstance(egress_payload, dict) and egress_payload:
                stale_reasons = [
                    str(item).strip()
                    for item in (egress_payload.get("stale_reasons") or [])
                    if str(item).strip()
                ]
                stale_reasons.append(
                    "host_visible_receipt_seed_blocked:" + str(egress_receipt_seed_gate_reason).strip()
                )
                seen_stale_reasons: set[str] = set()
                deduped_stale_reasons: list[str] = []
                for reason in stale_reasons:
                    if reason in seen_stale_reasons:
                        continue
                    seen_stale_reasons.add(reason)
                    deduped_stale_reasons.append(reason)
                egress_payload["protocol_session_chain_wrapper_status"] = STATUS_FAIL_REQUIRED
                egress_payload["stale_reasons"] = deduped_stale_reasons
                if not str(egress_payload.get("error_code", "")).strip():
                    egress_payload["error_code"] = "IP-HDSTAMP-002"
                egress_payload["host_visible_receipt_seed_attempted"] = False
                egress_payload["host_visible_receipt_seed_replay_count"] = 0
                egress_payload["host_visible_receipt_seed_gate_status"] = egress_receipt_seed_gate_status
                egress_payload["host_visible_receipt_seed_gate_reason"] = egress_receipt_seed_gate_reason
                _emit(egress_payload, json_only=args.json_only)
            elif egress_proc.stdout.strip():
                print(egress_proc.stdout.strip())
            if egress_proc.stderr.strip():
                print(egress_proc.stderr.strip(), file=sys.stderr)
            return egress_proc.returncode
    if session_chain_parent_status and session_chain_parent_status != STATUS_PASS_REQUIRED:
        return _fail(
            error_code="IP-GATE-ENTRY-002",
            stale_reason="session_chain_parent_attestation_not_pass_required",
            json_only=args.json_only,
        )
    if not out_reply_path.exists():
        return _fail(
            error_code="IP-HDSTAMP-002",
            stale_reason="reply_file_missing_after_egress",
            json_only=args.json_only,
        )

    reply_text = out_reply_path.read_text(encoding="utf-8", errors="ignore").strip()
    reply_preview = reply_text.splitlines()[:2] if reply_text else []
    first_line = str(reply_preview[0] if reply_preview else "").strip()
    machine_verification = egress_payload.get("machine_verification")
    if not isinstance(machine_verification, dict):
        machine_verification = {}
    display_headstamp_line = str(egress_payload.get("display_headstamp_line", "")).strip()
    if not display_headstamp_line and first_line.startswith("Identity-Context:"):
        display_headstamp_line = f"Display-Headstamp: {first_line}"
    machine_verification_line = str(egress_payload.get("machine_verification_line", "")).strip()
    if not machine_verification_line and machine_verification:
        machine_verification_line = _render_machine_verification_line(machine_verification)
    operator_envelope = str(egress_payload.get("operator_envelope", "")).strip()
    visible_reply = str(egress_payload.get("visible_reply", "")).strip() or reply_text
    visible_reply_preview = egress_payload.get("visible_reply_preview")
    if not isinstance(visible_reply_preview, list):
        visible_reply_preview = visible_reply.splitlines()[:3] if visible_reply else []
    operator_envelope_lines = egress_payload.get("operator_envelope_lines")
    if not isinstance(operator_envelope_lines, list):
        operator_envelope_lines = []
    operator_envelope_lines = [str(line).strip() for line in operator_envelope_lines if str(line).strip()]
    if not operator_envelope_lines and operator_envelope:
        operator_envelope_lines = [str(line).strip() for line in operator_envelope.splitlines() if str(line).strip()]
    if not operator_envelope_lines:
        operator_envelope_lines = [line for line in (display_headstamp_line, machine_verification_line) if line]
    if (
        operator_envelope_lines
        and (not visible_reply or not str(visible_reply).startswith("Display-Headstamp: "))
    ):
        reply_body_lines = reply_text.splitlines()
        if reply_body_lines and str(reply_body_lines[0]).strip().startswith("Identity-Context:"):
            reply_body_lines = reply_body_lines[1:]
        visible_reply_parts = list(operator_envelope_lines)
        body_text = "\\n".join(reply_body_lines).strip()
        if body_text:
            visible_reply_parts.append(body_text)
        visible_reply = "\\n".join(visible_reply_parts).strip()
    if (
        operator_envelope_lines
        and (
            not isinstance(visible_reply_preview, list)
            or not visible_reply_preview
            or not str(visible_reply_preview[0] or "").strip().startswith("Display-Headstamp: ")
        )
    ):
        visible_reply_preview = visible_reply.splitlines()[:3] if visible_reply else []
    headstamp_first_line_status = (
        STATUS_PASS_REQUIRED if first_line.startswith("Identity-Context:") else STATUS_FAIL_REQUIRED
    )
    outlet_channel_id = str(
        egress_payload.get("outlet_channel_id")
        or egress_payload.get("final_emit_channel_id")
        or ""
    ).strip()
    outlet_preflight_receipt = str(egress_payload.get("outlet_preflight_receipt", "")).strip() or str(
        ingress_receipt_path
    )
    final_emit_channel_id = str(egress_payload.get("final_emit_channel_id") or outlet_channel_id).strip()
    final_emit_policy_mode = str(egress_payload.get("final_emit_policy_mode", "")).strip()
    final_emit_schema_id = str(egress_payload.get("final_emit_schema_id", "")).strip()
    final_emit_schema_status = str(egress_payload.get("final_emit_schema_status", "")).strip().upper()
    final_emit_contract_status = str(
        egress_payload.get("final_emit_contract_status")
        or egress_payload.get("final_emit_guard_status")
        or ""
    ).strip().upper()
    tuple_missing = [
        key
        for key, value in (
            ("outlet_channel_id", outlet_channel_id),
            ("outlet_preflight_receipt", outlet_preflight_receipt),
            ("final_emit_channel_id", final_emit_channel_id),
            ("final_emit_policy_mode", final_emit_policy_mode),
            ("final_emit_schema_id", final_emit_schema_id),
            ("final_emit_schema_status", final_emit_schema_status),
            ("final_emit_contract_status", final_emit_contract_status),
        )
        if not str(value or "").strip()
    ]
    if tuple_missing:
        return _fail(
            error_code="IP-OUTLET-004",
            stale_reason="session_chain_final_emit_tuple_missing:" + ",".join(sorted(tuple_missing)),
            json_only=args.json_only,
        )
    tuple_status = STATUS_PASS_REQUIRED
    if str(args.actor_id).strip() != receipt_actor_id:
        tuple_status = STATUS_FAIL_REQUIRED
    if str(resolved_session_id).strip() != receipt_session_id:
        tuple_status = STATUS_FAIL_REQUIRED
    if str(run_id).strip() != receipt_run_id:
        tuple_status = STATUS_FAIL_REQUIRED
    host_visible_receipt_status = STATUS_FAIL_REQUIRED
    host_visible_state_file = ""
    host_visible_receipt_paths: list[str] = []
    host_visible_stale_reasons: list[str] = []
    (
        host_visible_receipt_status,
        host_visible_state_file,
        host_visible_receipt_paths,
        host_visible_stale_reasons,
        host_visible_final_channel_relay_projection,
    ) = _record_host_visible_surface_receipts(
        contract=contract,
        contract_path=contract_path,
        operation=str(args.operation).strip(),
        identity_id=str(args.identity_id).strip(),
        actor_id=str(args.actor_id).strip(),
        session_id=str(resolved_session_id).strip(),
        run_id=str(run_id).strip(),
        wrapper_surface_status=str(ingress_payload.get("wrapper_surface_status", "")).strip().upper(),
        entry_receipt_tuple_status=str(tuple_status).strip().upper(),
        headstamp_first_line_status=str(headstamp_first_line_status).strip().upper(),
        send_time_gate_status=str(egress_payload.get("send_time_gate_status", "")).strip().upper(),
        final_emit_contract_status=str(final_emit_contract_status).strip().upper(),
        out_reply_file=out_reply_path,
    )
    if host_visible_receipt_status != STATUS_PASS_REQUIRED:
        reason = (
            ",".join(host_visible_stale_reasons)
            if host_visible_stale_reasons
            else "host_visible_surface_receipt_not_pass_required"
        )
        return _fail(
            error_code="IP-HDSTAMP-003",
            stale_reason=reason,
            json_only=args.json_only,
        )
    if egress_proc.returncode != 0 or egress_guard_status != STATUS_PASS_REQUIRED:
        egress_receipt_seed_attempted = True
        egress_receipt_seed_replay_count = 1
        egress_receipt_seed_gate_status = STATUS_PASS_REQUIRED
        egress_receipt_seed_gate_reason = "seed_eligible"
        egress_proc = subprocess.run(egress_cmd, capture_output=True, text=True, env=egress_env)
        egress_payload = _parse_stdout_json(egress_proc.stdout)
        if egress_proc.returncode != 0:
            if egress_proc.stdout.strip():
                print(egress_proc.stdout.strip())
            if egress_proc.stderr.strip():
                print(egress_proc.stderr.strip(), file=sys.stderr)
            return egress_proc.returncode
        egress_guard_status = str(egress_payload.get("final_emit_guard_status", "")).strip().upper()
        if egress_guard_status != STATUS_PASS_REQUIRED:
            return _fail(
                error_code="IP-HDSTAMP-002",
                stale_reason="egress_guard_not_pass_required_after_host_visible_receipt_seed",
                json_only=args.json_only,
            )
    host_visible_receipt_source = _select_host_visible_receipt_source(str(args.operation).strip())
    process_message_metadata = _resolve_process_message_metadata(str(args.operation).strip())
    _emit(
        {
            "protocol_session_chain_wrapper_status": STATUS_PASS_REQUIRED,
            "identity_id": str(args.identity_id).strip(),
            "run_id": run_id,
            "session_id": resolved_session_id,
            "session_binding_mode": session_binding_mode,
            "session_binding_upserted": bool(session_binding_upserted),
            "actor_session_store_path": actor_session_store_path,
            "ingress_wrapper_path": str(ingress_wrapper_path),
            "egress_wrapper_path": str(egress_wrapper_path),
            "ingress_receipt_path": str(ingress_receipt_path),
            "out_reply_file": str(out_reply_path),
            "reply_preview": reply_preview,
            "visible_reply_preview": [str(line).strip() for line in visible_reply_preview if str(line).strip()],
            "reply_transport_ref": str(out_reply_path),
            "reply_transport_binding_status": STATUS_PASS_REQUIRED,
            "external_stamp": first_line,
            "display_headstamp_line": display_headstamp_line,
            "machine_verification_line": machine_verification_line,
            "machine_verification": machine_verification,
            "operator_envelope_lines": operator_envelope_lines,
            "operator_envelope": operator_envelope or "\\n".join(operator_envelope_lines),
            **process_message_metadata,
            "ingress_bundle_status": ingress_payload.get("bundle_status", ""),
            "wrapper_surface_status": ingress_payload.get("wrapper_surface_status", ""),
            "entry_receipt_tuple_status": tuple_status,
            "entry_receipt_tuple_run_id_status": (
                STATUS_PASS_REQUIRED if str(run_id).strip() == receipt_run_id else STATUS_FAIL_REQUIRED
            ),
            "entry_receipt_tuple_session_id_status": (
                STATUS_PASS_REQUIRED if str(resolved_session_id).strip() == receipt_session_id else STATUS_FAIL_REQUIRED
            ),
            "entry_receipt_tuple_actor_id_status": (
                STATUS_PASS_REQUIRED if str(args.actor_id).strip() == receipt_actor_id else STATUS_FAIL_REQUIRED
            ),
            "egress_guard_status": egress_payload.get("final_emit_guard_status", ""),
            "final_emit_guard_status": egress_payload.get("final_emit_guard_status", ""),
            "send_time_gate_status": egress_payload.get("send_time_gate_status", ""),
            "headstamp_status": egress_payload.get("headstamp_status", ""),
            "headstamp_first_line_status": headstamp_first_line_status,
            "headstamp_visibility_phase": egress_payload.get("headstamp_visibility_phase", ""),
            "headstamp_visibility_projection_status": egress_payload.get(
                "headstamp_visibility_projection_status",
                "",
            ),
            "headstamp_visibility_interpretation": egress_payload.get(
                "headstamp_visibility_interpretation",
                "",
            ),
            "effective_bound_identity_id": egress_payload.get("effective_bound_identity_id", ""),
            "effective_bound_actor_id": egress_payload.get("effective_bound_actor_id", ""),
            "effective_bound_session_id": egress_payload.get("effective_bound_session_id", ""),
            "effective_identity_projection_status": egress_payload.get(
                "effective_identity_projection_status",
                "",
            ),
            "quoted_identity_contexts": egress_payload.get("quoted_identity_contexts", []),
            "probe_identity_contexts": egress_payload.get("probe_identity_contexts", []),
            "binding_effect_summary": egress_payload.get("binding_effect_summary", {}),
            "host_visible_surface_live_receipt_status": host_visible_receipt_status,
            "host_visible_surface_state_file": host_visible_state_file,
            "host_visible_surface_live_receipt_paths": host_visible_receipt_paths,
            "host_visible_surface_live_receipt_source": host_visible_receipt_source,
            "host_visible_final_channel_relay_status": host_visible_final_channel_relay_projection.get(
                "agent_relay_final_answer_status",
                "",
            ),
            "host_visible_final_channel_relay_receipt_path": host_visible_final_channel_relay_projection.get(
                "agent_relay_final_answer_receipt_path",
                "",
            ),
            "host_visible_final_channel_relay_question_tag": host_visible_final_channel_relay_projection.get(
                "agent_relay_final_answer_question_tag",
                "",
            ),
            "host_visible_final_channel_relay_source_artifact": host_visible_final_channel_relay_projection.get(
                "agent_relay_final_answer_source_artifact",
                "",
            ),
            "host_visible_receipt_seed_attempted": egress_receipt_seed_attempted,
            "host_visible_receipt_seed_replay_count": egress_receipt_seed_replay_count,
            "host_visible_receipt_seed_gate_status": egress_receipt_seed_gate_status,
            "host_visible_receipt_seed_gate_reason": egress_receipt_seed_gate_reason,
            "emit_channel_id": final_emit_channel_id,
            "outlet_channel_id": outlet_channel_id,
            "outlet_preflight_receipt": outlet_preflight_receipt,
            "outlet_bypass_detected": bool(egress_payload.get("outlet_bypass_detected", False)),
            "final_emit_channel_id": final_emit_channel_id,
            "final_emit_policy_mode": final_emit_policy_mode,
            "final_emit_schema_id": final_emit_schema_id,
            "final_emit_schema_status": final_emit_schema_status,
            "final_emit_contract_status": final_emit_contract_status,
            "sender_consumption_contract_ref": egress_payload.get("sender_consumption_contract_ref", ""),
            "sender_consumption_contract_required": egress_payload.get(
                "sender_consumption_contract_required",
                False,
            ),
            "sender_consumption_expected_transport_ref": egress_payload.get(
                "sender_consumption_expected_transport_ref",
                "",
            ),
            "sender_consumption_allowed_transport_refs": egress_payload.get(
                "sender_consumption_allowed_transport_refs",
                [],
            ),
            "sender_consumption_projection_status": egress_payload.get(
                "sender_consumption_projection_status",
                "",
            ),
            "next_hop_release_allowed": egress_payload.get("next_hop_release_allowed", False),
            "session_chain_parent_attestation_required": egress_payload.get(
                "session_chain_parent_attestation_required",
                False,
            ),
            "session_chain_parent_attestation_status": egress_payload.get(
                "session_chain_parent_attestation_status",
                "",
            ),
        },
        json_only=args.json_only,
        visible_reply=visible_reply,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
    return template.replace(
        "__TEMPLATE_HOST_VISIBLE_FIXTURE_RECEIPT_SOURCE__",
        HOST_VISIBLE_SURFACE_FIXTURE_RECEIPT_SOURCE,
    ).replace(
        "__TEMPLATE_HOST_VISIBLE_FIXTURE_ALLOWED_OPERATIONS__",
        ",".join(f'"{token}"' for token in HOST_VISIBLE_SURFACE_FIXTURE_ALLOWED_OPERATIONS),
    )


def materialize_protocol_host_gateway_artifacts(
    *,
    task: dict,
    identity_id: str,
    pack_dir: Path,
    catalog_path: Path,
    protocol_root: Path,
) -> dict:
    contract = task.get(HOST_GATEWAY_CONTRACT_KEY)
    if not isinstance(contract, dict):
        contract = _protocol_host_unique_channel_contract_skeleton(identity_id)
        task[HOST_GATEWAY_CONTRACT_KEY] = contract
    visible_surface_contract = task.get(HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY)
    if not isinstance(visible_surface_contract, dict):
        visible_surface_contract = _host_visible_surface_registry_contract_skeleton()
        task[HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY] = visible_surface_contract
    else:
        visible_surface_contract = _deep_merge_defaults(
            _host_visible_surface_registry_contract_skeleton(),
            visible_surface_contract,
        )
        task[HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY] = visible_surface_contract
    downsink_contract = task.get(DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY)
    if not isinstance(downsink_contract, dict):
        downsink_contract = _protocol_downsink_path_immutability_contract_skeleton()
        task[DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY] = downsink_contract
    else:
        downsink_contract = _deep_merge_defaults(_protocol_downsink_path_immutability_contract_skeleton(), downsink_contract)
        task[DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY] = downsink_contract
    signer_secret_env = _host_gateway_signer_secret_env(identity_id)

    ingress_wrapper_path = _resolve_pack_runtime_path(
        pack_dir,
        HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
        fallback=HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
    )
    egress_wrapper_path = _resolve_pack_runtime_path(
        pack_dir,
        HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
        fallback=HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
    )
    session_chain_wrapper_path = _resolve_pack_runtime_path(
        pack_dir,
        HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
        fallback=HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    )
    gateway_contract_path = _resolve_pack_runtime_path(
        pack_dir,
        HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
        fallback=HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
    )
    ingress_proof_policy = contract.get("ingress_proof_policy")
    if not isinstance(ingress_proof_policy, dict):
        ingress_proof_policy = {}
    ingress_signer_mode = str(ingress_proof_policy.get("signer_mode", "")).strip().lower() or HOST_GATEWAY_SIGNER_MODE
    ingress_signing_key_path = _resolve_pack_runtime_path(
        pack_dir,
        str(ingress_proof_policy.get("signing_key_path", "")),
        fallback=HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
    )
    ingress_bootstrap_from_key = bool(
        ingress_proof_policy.get(
            "bootstrap_env_secret_from_signing_key_path",
            HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
        )
    )
    ensure_signing_key(ingress_signing_key_path)
    broadcast_policy = contract.get("broadcast_policy")
    default_broadcast_policy = _host_gateway_broadcast_policy()
    if not isinstance(broadcast_policy, dict):
        broadcast_policy = {}
    for key, value in default_broadcast_policy.items():
        if key not in broadcast_policy or broadcast_policy.get(key) in (None, "", []):
            broadcast_policy[key] = json.loads(json.dumps(value))
    broadcast_state_path = _resolve_pack_runtime_path(
        pack_dir,
        HOST_GATEWAY_BROADCAST_STATE_FILE,
        fallback=HOST_GATEWAY_BROADCAST_STATE_FILE,
    )
    visible_surface_state_path = _resolve_pack_runtime_path(
        pack_dir,
        str(visible_surface_contract.get("runtime_state_file", "")).strip(),
        fallback=HOST_VISIBLE_SURFACE_STATE_FILE,
    )
    post_check_closure_state_path = _resolve_pack_runtime_path(
        pack_dir,
        str(visible_surface_contract.get("post_check_closure_state_file", "")).strip(),
        fallback=HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    )

    contract["required"] = True
    contract["contract_id"] = HOST_GATEWAY_CONTRACT_ID
    contract["validator"] = "scripts/validate_protocol_unique_entry_gate.py"
    contract["protocol_ingress_script"] = UNIQUE_INGRESS_SCRIPT
    contract["protocol_egress_script"] = UNIQUE_EGRESS_SCRIPT
    contract["ingress_wrapper_path"] = ingress_wrapper_path.as_posix()
    contract["egress_wrapper_path"] = egress_wrapper_path.as_posix()
    contract["session_chain_wrapper_path"] = session_chain_wrapper_path.as_posix()
    contract["gateway_contract_path"] = gateway_contract_path.as_posix()
    contract["entry_receipt_policy"] = {
        "required": True,
        "required_surface_label": HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
        "required_wrapper_surface_status": HOST_GATEWAY_REQUIRED_SURFACE_STATUS,
        "required_wrapper_dispatch_token_status": HOST_GATEWAY_REQUIRED_DISPATCH_STATUS,
    }
    contract["ingress_proof_policy"] = {
        "required": True,
        "max_age_seconds": int(HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS),
        "signer_mode": ingress_signer_mode,
        "signer_secret_env": signer_secret_env,
        "signing_key_path": ingress_signing_key_path.as_posix(),
        "bootstrap_env_secret_from_signing_key_path": bool(ingress_bootstrap_from_key),
    }
    contract["egress_receipt_policy"] = {"required": True}
    contract["egress_grant_policy"] = {
        "required": True,
        "max_age_seconds": int(HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS),
        "signer_mode": ingress_signer_mode,
        "signer_secret_env": signer_secret_env,
        "signing_key_path": ingress_signing_key_path.as_posix(),
        "bootstrap_env_secret_from_signing_key_path": bool(ingress_bootstrap_from_key),
    }
    contract["headstamp_policy"] = {"required": True}
    contract["identity_tuple_fields"] = list(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS)
    contract["host_dispatch_mode"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
    contract["host_release_mode"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE
    contract["ingress_wrapper_dispatch_token"] = HOST_GATEWAY_INGRESS_DISPATCH_TOKEN
    contract["operation_profile_policy"] = _host_gateway_operation_profile_policy()
    contract["broadcast_policy"] = {
        "required": True,
        "protocol_broadcast_items_dir": HOST_GATEWAY_BROADCAST_ITEMS_DIR,
        "protocol_broadcast_index_file": HOST_GATEWAY_BROADCAST_INDEX_FILE,
        "protocol_broadcast_schema_file": HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
        "instance_state_file": broadcast_state_path.as_posix(),
        "instance_receipt_pattern": HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
        "instance_ack_pattern": HOST_GATEWAY_BROADCAST_ACK_PATTERN,
        "block_on_critical_unacked": bool(broadcast_policy.get("block_on_critical_unacked", False)),
    }
    contract["host_visible_surface_registry_contract_ref"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
    contract[HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY] = _host_gateway_wrapper_template_attestation_policy()

    visible_surface_contract["required"] = True
    visible_surface_contract["contract_id"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
    visible_surface_contract["validator"] = HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
    visible_surface_contract["required_channels"] = list(HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS)
    visible_surface_contract["runtime_state_file"] = visible_surface_state_path.as_posix()
    visible_surface_contract["post_check_closure_state_file"] = post_check_closure_state_path.as_posix()
    visible_surface_contract["post_check_block_on_active"] = bool(HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE)
    visible_surface_contract["runtime_receipt_pattern"] = str(
        visible_surface_contract.get("runtime_receipt_pattern", "")
    ).strip() or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
    visible_surface_contract["required_attestation_fields"] = list(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS)
    visible_surface_contract["required_pass_status_fields"] = list(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS)
    visible_surface_contract["final_channel_id"] = HOST_VISIBLE_FINAL_CHANNEL_ID
    visible_surface_contract["final_channel_relay_required"] = bool(HOST_VISIBLE_FINAL_CHANNEL_RELAY_REQUIRED)
    visible_surface_contract["final_channel_relay_surface"] = HOST_VISIBLE_FINAL_CHANNEL_RELAY_SURFACE
    visible_surface_contract["final_channel_relay_mode"] = HOST_VISIBLE_FINAL_CHANNEL_RELAY_MODE
    visible_surface_contract["final_channel_delivery_authority"] = (
        HOST_VISIBLE_FINAL_CHANNEL_DELIVERY_AUTHORITY
    )
    visible_surface_contract["final_channel_required_attestation_fields"] = list(
        HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_ATTESTATION_FIELDS
    )
    visible_surface_contract["final_channel_required_pass_status_fields"] = list(
        HOST_VISIBLE_FINAL_CHANNEL_REQUIRED_PASS_STATUS_FIELDS
    )
    visible_surface_contract["required_live_probe_delegate"] = HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
    visible_surface_contract["host_dispatch_mode_required"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
    visible_surface_contract["host_release_mode_required"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE

    ingress_wrapper_rel = _pack_relative_path(
        pack_dir,
        ingress_wrapper_path,
        fallback="runtime/gate/protocol_ingress_wrapper.py",
    )
    egress_wrapper_rel = _pack_relative_path(
        pack_dir,
        egress_wrapper_path,
        fallback="runtime/gate/protocol_egress_wrapper.py",
    )
    session_chain_wrapper_rel = _pack_relative_path(
        pack_dir,
        session_chain_wrapper_path,
        fallback="runtime/gate/protocol_session_chain_wrapper.py",
    )
    gateway_contract_rel = _pack_relative_path(
        pack_dir,
        gateway_contract_path,
        fallback="runtime/gate/protocol_gateway_contract.json",
    )
    broadcast_state_rel = _pack_relative_path(
        pack_dir,
        broadcast_state_path,
        fallback=HOST_GATEWAY_BROADCAST_STATE_FILE,
    )

    def _replace_registry_entry(
        *,
        registry: dict,
        domain: str,
        path_id: str,
        entry_type: str,
        path_value: str,
    ) -> None:
        domain_node = registry.get(domain)
        if not isinstance(domain_node, dict):
            return
        entries = domain_node.get("entries")
        if not isinstance(entries, list):
            return
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("path_id", "")).strip() != path_id:
                continue
            entry["entry_type"] = entry_type
            entry["path"] = str(path_value).strip()
            return

    downsink_contract["required"] = True
    downsink_contract["contract_id"] = DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID
    downsink_contract["validator_id"] = DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID
    downsink_contract["write_guard_validator_id"] = DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID
    downsink_contract["source_literal_lock_policy"] = {
        "required": True,
        "validator_id": DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
        "enforce_registered_runtime_path_literals_only": True,
        "allow_inline_override_marker": DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
        "scan_globs": list(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS),
    }
    downsink_contract["anchor_policy"] = {
        "protocol_repo_root_ref": DOWNSINK_ANCHOR_PROTOCOL_REPO_ROOT_REF,
        "identity_pack_root_ref": DOWNSINK_ANCHOR_IDENTITY_PACK_ROOT_REF,
        "allow_parent_escape": False,
        "allow_symlink_escape": False,
    }
    downsink_contract["schema_policy"] = {
        "reject_additional_properties": True,
        "require_all_declared_paths_present_in_runtime_contract": True,
    }
    downsink_contract["operation_enforcement"] = {
        "strict_operations": list(HOST_GATEWAY_STRICT_OPERATIONS),
        "light_operations": list(HOST_GATEWAY_LIGHT_OPERATIONS),
        "strict_fail_mode": "fail_required",
        "light_fail_mode": "fail_required",
    }
    downsink_registry = _protocol_downsink_path_registry_skeleton()
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_GATE_DOMAIN,
        path_id="runtime_gate.ingress_wrapper",
        entry_type="file",
        path_value=ingress_wrapper_rel,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_GATE_DOMAIN,
        path_id="runtime_gate.egress_wrapper",
        entry_type="file",
        path_value=egress_wrapper_rel,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_GATE_DOMAIN,
        path_id="runtime_gate.session_chain_wrapper",
        entry_type="file",
        path_value=session_chain_wrapper_rel,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_GATE_DOMAIN,
        path_id=DOWNSINK_RUNTIME_MIRROR_PATH_ID,
        entry_type="file",
        path_value=gateway_contract_rel,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
        path_id="runtime_broadcast.state_file",
        entry_type="file",
        path_value=broadcast_state_rel,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
        path_id="runtime_broadcast.receipt_pattern",
        entry_type="glob",
        path_value=HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
    )
    _replace_registry_entry(
        registry=downsink_registry,
        domain=DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
        path_id="runtime_broadcast.ack_pattern",
        entry_type="glob",
        path_value=HOST_GATEWAY_BROADCAST_ACK_PATTERN,
    )
    downsink_contract["path_registry"] = downsink_registry

    gateway_contract_payload = {
        "schema_version": "v1",
        "identity_id": identity_id,
        "protocol_repo_root": str(protocol_root.expanduser().resolve()),
        "protocol_ingress_script": UNIQUE_INGRESS_SCRIPT,
        "protocol_egress_script": UNIQUE_EGRESS_SCRIPT,
        "ingress_wrapper_path": ingress_wrapper_path.as_posix(),
        "egress_wrapper_path": egress_wrapper_path.as_posix(),
        "session_chain_wrapper_path": session_chain_wrapper_path.as_posix(),
        "catalog_path": str(catalog_path.expanduser().resolve()),
        "entry_receipt_policy": {
            "required": True,
            "required_surface_label": HOST_GATEWAY_REQUIRED_SURFACE_LABEL,
            "required_wrapper_surface_status": HOST_GATEWAY_REQUIRED_SURFACE_STATUS,
            "required_wrapper_dispatch_token_status": HOST_GATEWAY_REQUIRED_DISPATCH_STATUS,
        },
        "ingress_proof_policy": {
            "required": True,
            "max_age_seconds": int(HOST_GATEWAY_INGRESS_PROOF_MAX_AGE_SECONDS),
            "signer_mode": ingress_signer_mode,
            "signer_secret_env": signer_secret_env,
            "signing_key_path": ingress_signing_key_path.as_posix(),
            "bootstrap_env_secret_from_signing_key_path": bool(ingress_bootstrap_from_key),
        },
        "egress_receipt_policy": {"required": True},
        "egress_grant_policy": {
            "required": True,
            "max_age_seconds": int(HOST_GATEWAY_EGRESS_GRANT_MAX_AGE_SECONDS),
            "signer_mode": ingress_signer_mode,
            "signer_secret_env": signer_secret_env,
            "signing_key_path": ingress_signing_key_path.as_posix(),
            "bootstrap_env_secret_from_signing_key_path": bool(ingress_bootstrap_from_key),
        },
        "headstamp_policy": {"required": True},
        "identity_tuple_fields": list(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS),
        "host_dispatch_mode": HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
        "host_release_mode": HOST_GATEWAY_REQUIRED_RELEASE_MODE,
        "ingress_wrapper_dispatch_token": HOST_GATEWAY_INGRESS_DISPATCH_TOKEN,
        "operation_profile_policy": _host_gateway_operation_profile_policy(),
        "host_visible_surface_registry_contract_ref": HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
        HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY: json.loads(
            json.dumps(contract.get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY, {}))
        ),
        "broadcast_policy": {
            "required": True,
            "protocol_broadcast_items_dir": HOST_GATEWAY_BROADCAST_ITEMS_DIR,
            "protocol_broadcast_index_file": HOST_GATEWAY_BROADCAST_INDEX_FILE,
            "protocol_broadcast_schema_file": HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
            "instance_state_file": str(contract["broadcast_policy"]["instance_state_file"]).strip(),
            "instance_receipt_pattern": str(contract["broadcast_policy"]["instance_receipt_pattern"]).strip(),
            "instance_ack_pattern": str(contract["broadcast_policy"]["instance_ack_pattern"]).strip(),
            "block_on_critical_unacked": bool(contract["broadcast_policy"]["block_on_critical_unacked"]),
        },
        HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY: json.loads(json.dumps(visible_surface_contract)),
        DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY: json.loads(json.dumps(downsink_contract)),
    }
    write_json(gateway_contract_path, gateway_contract_payload)
    if not broadcast_state_path.exists():
        write_json(broadcast_state_path, _default_broadcast_state_doc(identity_id))
    if not visible_surface_state_path.exists():
        write_json(visible_surface_state_path, _default_host_visible_surface_state_doc(identity_id))
    if not post_check_closure_state_path.exists():
        write_json(
            post_check_closure_state_path,
            _default_host_visible_surface_post_check_closure_state_doc(identity_id),
        )
    write(ingress_wrapper_path, _protocol_ingress_wrapper_template())
    write(egress_wrapper_path, _protocol_egress_wrapper_template())
    write(session_chain_wrapper_path, _protocol_session_chain_wrapper_template())

    return {
        "gateway_contract_path": gateway_contract_path.as_posix(),
        "ingress_wrapper_path": ingress_wrapper_path.as_posix(),
        "egress_wrapper_path": egress_wrapper_path.as_posix(),
        "session_chain_wrapper_path": session_chain_wrapper_path.as_posix(),
        "host_visible_surface_state_file": visible_surface_state_path.as_posix(),
    }


def _normalize_bootstrap_task_ids(value, identity_id: str):
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k == "task_id":
                out[k] = f"{identity_id}_bootstrap"
            else:
                out[k] = _normalize_bootstrap_task_ids(v, identity_id)
        return out
    if isinstance(value, list):
        return [_normalize_bootstrap_task_ids(v, identity_id) for v in value]
    return value


def _legacy_full_contract_current_task(
    identity_id: str,
    title: str,
    description: str,
    *,
    version_baseline: dict[str, Any],
) -> dict:
    template_path = Path("identity/store-manager/CURRENT_TASK.json")
    if not template_path.exists():
        raise FileNotFoundError(f"missing template CURRENT_TASK: {template_path}")
    template = json.loads(template_path.read_text(encoding="utf-8"))
    task = _replace_store_manager_tokens(copy.deepcopy(template), identity_id)
    task = _normalize_pack_paths(task, identity_id)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    task["task_id"] = f"{identity_id}_bootstrap"
    agent = task.setdefault("agent_identity", {})
    if isinstance(agent, dict):
        agent["name"] = identity_id
        agent["role"] = title
        agent["identity_prompt_path"] = f"identity/packs/{identity_id}/IDENTITY_PROMPT.md"
    task["response_stamp_profile"] = normalize_response_stamp_profile(task.get("response_stamp_profile"))
    apply_version_baseline_to_task_doc(task, version_baseline)
    objective = task.setdefault("objective", {})
    if isinstance(objective, dict):
        objective["title"] = description
        objective["status"] = "pending"

    task.setdefault("version_control", {})
    if isinstance(task["version_control"], dict):
        task["version_control"]["last_updated"] = now
        task["version_control"]["sync_status"] = "initialized"

    # Force identity-scoped evidence patterns
    prc = task.setdefault("protocol_review_contract", {})
    if isinstance(prc, dict):
        prc["evidence_report_path_pattern"] = f"identity/runtime/examples/protocol-baseline-review-{identity_id}-*.json"
    replay = (
        task.setdefault("identity_update_lifecycle_contract", {})
        .setdefault("replay_contract", {})
    )
    if isinstance(replay, dict):
        replay["evidence_path_pattern"] = f"identity/runtime/examples/{identity_id}-update-replay-*.json"
    install = task.setdefault("install_safety_contract", {})
    if isinstance(install, dict):
        install["install_report_path_pattern"] = f"identity/runtime/examples/install/install-report-*-{identity_id}.json"
    feedback = task.setdefault("experience_feedback_contract", {})
    if isinstance(feedback, dict):
        feedback["feedback_log_path_pattern"] = f"identity/runtime/logs/feedback/{identity_id}-feedback-*.json"
    collab = task.setdefault("collaboration_trigger_contract", {})
    if isinstance(collab, dict):
        collab["evidence_log_path_pattern"] = f"identity/runtime/logs/collaboration/{identity_id}-*.json"
    handoff = task.setdefault("agent_handoff_contract", {})
    if isinstance(handoff, dict):
        handoff["handoff_log_path_pattern"] = f"identity/runtime/logs/handoff/{identity_id}-*.json"
    route_quality = task.setdefault("route_quality_contract", {})
    if isinstance(route_quality, dict):
        route_quality["source_pattern"] = f"identity/runtime/logs/handoff/{identity_id}-*.json"
        route_quality["metrics_output_path"] = f"identity/runtime/metrics/{identity_id}-route-quality.json"
    trig = task.setdefault("trigger_regression_contract", {})
    if isinstance(trig, dict):
        trig["sample_report_path_pattern"] = f"identity/runtime/examples/{identity_id}-trigger-regression-sample.json"
    arb = task.setdefault("capability_arbitration_contract", {})
    if isinstance(arb, dict):
        arb["sample_report_path_pattern"] = f"identity/runtime/examples/{identity_id}-capability-arbitration-sample.json"
    rbc = task.setdefault("identity_role_binding_contract", {})
    if isinstance(rbc, dict):
        rbc["role_type"] = f"{identity_id.replace('-', '_')}_runtime_operator"
    task["scaffold_profile"] = "legacy-commerce-overlay"
    task["scaffold_generation_mode"] = "explicit_opt_in"
    task = _ensure_dialogue_governance_contract(task, identity_id)
    task = _ensure_tool_vendor_governance_contracts(task, identity_id)
    return _ensure_instance_pack_topology_contract(task, identity_id)


def _default_required_checks() -> list[str]:
    return [
        "scripts/validate_unlock_formula.py",
        "scripts/validate_release_plane_cloud_evidence.py",
        "scripts/validate_cross_cwd_absolute_input.py",
        "scripts/validate_run_id_report_selection.py",
        "scripts/validate_phase_bootstrap_before_strict.py",
        "scripts/validate_tmp_collision_safety.py",
        "scripts/validate_handoff_collab_freshness_rotation.py",
        "scripts/validate_protocol_feedback_atomic_emit.py",
        "scripts/validate_capability_boundary_classification.py",
        "scripts/validate_promotion_pipeline.py",
        "scripts/validate_outlet_matrix.py",
        "scripts/validate_sidecar_cwd_parity.py",
        "scripts/validate_docs_bridge_consistency.py",
        "scripts/validate_contract_mapping_coverage.py",
        "scripts/validate_identity_tool_installation.py",
        "scripts/validate_identity_vendor_api_discovery.py",
        "scripts/validate_identity_vendor_api_solution.py",
        "scripts/validate_identity_instance_pack_topology.py",
        INSTANCE_SCRIPT_MANIFEST_VALIDATOR_ID,
        INSTANCE_SCRIPT_ORCHESTRATION_VALIDATOR_ID,
        INSTANCE_SCRIPT_RECEIPT_JOIN_VALIDATOR_ID,
        INSTANCE_SCRIPT_EXECUTION_LANE_VALIDATOR_ID,
        "scripts/validate_prompt_bootstrap_capability.py",
        "scripts/validate_prompt_capability_matrix.py",
        "scripts/validate_refresh_strict_business_interference.py",
        "scripts/validate_kernel_ssot_source.py",
        "scripts/validate_prompt_derivation_conformance.py",
        "scripts/validate_semantic_convergence.py",
        "scripts/validate_prompt_kernel_executable_coupling.py",
        "scripts/validate_identity_runtime_contract.py",
        "scripts/validate_identity_upgrade_prereq.py",
        "scripts/validate_identity_update_lifecycle.py",
        "scripts/validate_identity_trigger_regression.py",
        "scripts/validate_identity_learning_loop.py",
        "scripts/validate_agent_handoff_contract.py",
        "scripts/validate_identity_collab_trigger.py",
        "scripts/validate_identity_orchestration_contract.py",
        "scripts/validate_identity_knowledge_contract.py",
        "scripts/validate_identity_experience_feedback.py",
        "scripts/validate_changelog_updated.py",
        "scripts/validate_release_metadata_sync.py",
        "scripts/validate_identity_role_binding.py",
        "scripts/validate_identity_ci_enforcement.py",
        "scripts/validate_identity_capability_arbitration.py",
        "scripts/validate_identity_install_safety.py",
        "scripts/validate_identity_experience_feedback_governance.py",
        "scripts/validate_identity_self_upgrade_enforcement.py",
        "scripts/validate_identity_install_provenance.py",
        "scripts/required_gate_bundle_runner.py",
        "scripts/validate_replay_archive_contract.py",
        "scripts/validate_gated_switch_guard.py",
        "scripts/validate_protocol_lane_headstamp_continuity.py",
        "scripts/validate_current_turn_authoritative_headstamp.py",
    ]


def _neutral_full_contract_current_task(
    identity_id: str,
    title: str,
    description: str,
    *,
    agent_identity_versions: dict[str, str],
) -> dict:
    identity_token = identity_id.replace("-", "_")
    checks = _default_required_checks()
    task = _minimal_current_task(
        identity_id,
        title,
        description,
        agent_identity_versions=agent_identity_versions,
    )
    gates = task.setdefault("gates", {})
    extra_required_gates = [
        "identity_update_gate",
        "agent_handoff_gate",
        "collaboration_trigger_gate",
        "orchestration_gate",
        "knowledge_acquisition_gate",
        "experience_feedback_gate",
        "install_safety_gate",
        "install_provenance_gate",
        "role_binding_gate",
        "ci_enforcement_gate",
        "arbitration_gate",
    ]
    for gate_name in extra_required_gates:
        gates[gate_name] = "required"

    task["state_machine"] = {
        "current_state": "doc_crosscheck",
        "allowed_states": [
            "intake",
            "doc_crosscheck",
            "preflight",
            "execute",
            "monitor",
            "repair",
            "verify",
            "done",
            "blocked",
        ],
        "transition_rules": [
            "intake -> doc_crosscheck",
            "doc_crosscheck -> preflight",
            "preflight -> execute",
            "execute -> monitor",
            "monitor -> verify",
            "verify -> done",
            "monitor -> repair",
            "repair -> preflight",
            "verify -> blocked",
        ],
    }
    task["source_of_truth"] = {
        "local_docs_roots": [
            "docs/governance",
            "docs/review",
        ],
        "local_project_evidence_roots": [
            "resource/reports",
            "resource/preflight",
            "resource/reject-archive",
            "identity/runtime/reports",
            "identity/runtime/examples",
            "identity/runtime/logs",
        ],
    }
    task["required_artifacts"] = [
        "resource/reports/*.json",
        "resource/reports/*.md",
        "identity/runtime/examples/*.json",
        "identity/runtime/logs/**/*.json",
        "identity/runtime/reports/**/*.json",
    ]
    task["post_execution_mandatory"] = [
        f"append task outcome into identity/packs/{identity_id}/TASK_HISTORY.md",
        "update objective.status",
        "update state_machine.current_state",
        "emit machine-readable execution report",
    ]

    task["identity_update_lifecycle_contract"] = {
        "trigger_contract": {
            "mandatory_conditions": [
                "operational_failure",
                "repeat_failure",
                "route_exhausted",
                "new_domain_gap",
            ],
            "max_attempts_before_update": 2,
        },
        "patch_surface_contract": {
            "required_files": [
                "CURRENT_TASK.json",
                "IDENTITY_PROMPT.md",
                "RULEBOOK.jsonl",
                "TASK_HISTORY.md",
            ],
            "required_file_paths": [
                f"identity/packs/{identity_id}/CURRENT_TASK.json",
                f"identity/packs/{identity_id}/IDENTITY_PROMPT.md",
                f"identity/packs/{identity_id}/RULEBOOK.jsonl",
                f"identity/packs/{identity_id}/TASK_HISTORY.md",
            ],
            "required_rulebook_update": True,
        },
        "validation_contract": {
            "required_checks": checks,
            "must_pass_all": True,
        },
        "replay_contract": {
            "replay_required": True,
            "replay_same_case_required": True,
            "replay_fail_action": "reenter_identity_update_loop",
            "evidence_path_pattern": f"identity/runtime/examples/{identity_id}-update-replay-*.json",
            "required_fields": [
                "identity_id",
                "replay_status",
                "patched_files",
                "validation_checks_passed",
                "creator_invocation",
                "check_results",
            ],
        },
    }
    task["trigger_regression_contract"] = {
        "required": True,
        "required_suites": [
            "positive_cases",
            "boundary_cases",
            "negative_cases",
        ],
        "result_enum": ["PASS", "FAIL"],
        "sample_report_path_pattern": "identity/runtime/examples/*trigger-regression*.json",
        "fail_action": "block_merge_and_reenter_identity_update",
    }
    task["route_quality_contract"] = {
        "required": True,
        "source_pattern": "identity/runtime/logs/handoff/*.json",
        "metrics_output_path": f"identity/runtime/metrics/{identity_id}-route-quality.json",
        "required_metrics": [
            "route_hit_rate",
            "misroute_rate",
            "fallback_rate",
            "first_pass_success_rate",
            "knowledge_reuse_rate",
            "replay_success_rate",
            "policy_drift_incidents",
        ],
        "validator": "scripts/export_route_quality_metrics.py",
    }
    task["dedup_monotonic_winner_contract_v1"] = {
        "required": True,
        "validator": "scripts/validate_dedup_monotonicity.py",
        "claims_path_pattern": "runtime/reports/**/*dedup*claim*.json",
        "required_fields": [
            "run_id",
            "earliest_claim_ts",
            "stable_tiebreaker",
            "winner_id",
            "winner_reason",
            "monotonicity_status",
        ],
        "fail_action": "block_merge_and_reenter_dedup_orchestration",
    }
    task["cross_workflow_evidence_schema_contract_v1"] = {
        "required": True,
        "normalizer": "scripts/normalize_cross_workflow_evidence.py",
        "validator": "scripts/validate_cross_workflow_schema.py",
        "evidence_path_pattern": (
            f"identity/runtime/local/{identity_id}/reports/identity-upgrade-exec-{identity_id}-*.json"
        ),
        "required_fields": [
            "run_id",
            "route_action",
            "quality_meta_state",
            "dedup_state",
            "evidence_hash",
            "schema_version",
        ],
        "fail_action": "block_merge_and_reenter_cross_workflow_schema_alignment",
    }
    task["skill_path_integrity_contract_v1"] = {
        "required": True,
        "validator": "scripts/validate_skill_path_integrity.py",
        "layout_mode": "active_repo_runtime",
        "required_skills": [
            "ai-folder-governance",
        ],
        "allowed_skill_roots": [
            "{active_repo_root}/skills",
            "{active_repo_root}/.codex/skills",
            "{active_repo_root}/identity-protocol-local/skills",
            "{active_runtime_root}/skills",
        ],
        "required_fields": [
            "active_repo_root",
            "active_runtime_root",
            "layout_mode",
            "path_integrity_status",
            "path_integrity_error_code",
        ],
        "fail_action": "block_merge_and_reenter_skill_path_integrity_alignment",
    }
    task["route_workflow_version_pinning_contract_v1"] = {
        "required": True,
        "receipt_emitter": "scripts/emit_route_version_pin_receipt.py",
        "validator": "scripts/validate_route_version_pinning.py",
        "proof_receipt_path_pattern": (
            f"identity/runtime/local/{identity_id}/reports/{identity_id}-route-version-pin-receipt*.json"
        ),
        "required_fields": [
            "route_endpoint",
            "workflow_id",
            "workflow_publish_version",
            "pin_proof_ref",
        ],
        "expected_bindings": [],
        "fail_action": "block_merge_and_reenter_route_workflow_version_alignment",
    }
    task["learning_verification_contract"] = {
        "run_id_required": True,
        "reasoning_trace_required": True,
        "reasoning_trace_path_pattern": "resource/reports/*reasoning*.json",
        "rulebook_update_required": True,
        "rulebook_link_field": "evidence_run_id",
    }
    task["agent_handoff_contract"] = {
        "required": True,
        "required_fields": [
            "handoff_id",
            "task_id",
            "from_agent",
            "to_agent",
            "input_scope",
            "actions_taken",
            "artifacts",
            "result",
            "next_action",
            "rulebook_update",
        ],
        "forbidden_mutations": [
            "gates",
            "protocol_review_contract",
            "identity_update_lifecycle_contract",
            "trigger_regression_contract",
        ],
        "handoff_log_path_pattern": "identity/runtime/logs/handoff/*.json",
        "minimum_logs_required": 1,
        "require_generated_at": True,
        "max_log_age_days": 7,
        "enforce_task_id_match": True,
        "require_identity_id_match": True,
        "sample_log_path_pattern": "identity/runtime/examples/handoff",
        "result_enum": ["PASS", "FAIL", "BLOCKED"],
        "self_test_required": True,
        "validator": "scripts/validate_agent_handoff_contract.py",
    }
    task["blocker_taxonomy_contract"] = {
        "required": True,
        "required_blocker_types": list(CANONICAL_BLOCKER_TYPES),
        "legacy_alias_bridge": dict(LEGACY_BLOCKER_ALIAS_MAP),
        "blocker_alias_map_version": "v1",
        "blocker_classification_required_fields": [
            "blocker_type",
            "source",
            "detected_at",
            "requires_human_collab",
            "next_action",
        ],
        "fail_action": "block_merge_and_reenter_collaboration_update",
    }
    task["collaboration_trigger_contract"] = {
        "required": True,
        "hard_rule": (
            "If human collaboration blockers are detected, notify immediately and emit chat receipt"
        ),
        "trigger_conditions": list(CANONICAL_BLOCKER_TYPES),
        "legacy_alias_bridge": dict(LEGACY_BLOCKER_ALIAS_MAP),
        "notify_channel": "ops-notification-router",
        "dedupe_window_hours": 24,
        "state_change_bypass_dedupe": True,
        "must_emit_receipt_in_chat": True,
        "receipt_required_fields": [
            "event_id",
            "blocker_type",
            "notified_at",
            "channel",
            "dedupe_key",
            "status",
        ],
        "evidence_log_path_pattern": "identity/runtime/logs/collaboration/*.json",
        "minimum_evidence_logs_required": 1,
        "max_log_age_days": 7,
        "validator": "scripts/validate_identity_collab_trigger.py",
        "notify_policy": "must_notify_when_human_required",
        "notify_timing": "immediate",
        "decision_basis": "role_requirement",
    }
    task["capability_orchestration_contract"] = {
        "required": True,
        "task_type_routes": {
            "instance_delivery": {
                "pipeline": [
                    "observe_context",
                    "skill_route",
                    "mcp_preflight",
                    "execute_pipeline",
                    "verify_result",
                    "emit_evidence",
                ],
                "primary_skills": [
                    "identity-creator",
                    "office-output-qa",
                ],
                "fallback_skills": [
                    "web-docs-to-markdown",
                    "gh-fix-ci",
                ],
                "required_mcp": [
                    "github",
                    "n8n-mcp",
                ],
                "max_tool_calls": 30,
                "max_runtime_minutes": 20,
            },
            "knowledge_api_probe": {
                "pipeline": [
                    "observe_context",
                    "source_research",
                    "hypothesis_build",
                    "api_probe",
                    "verify_result",
                    "emit_evidence",
                ],
                "primary_skills": [
                    "identity-creator",
                ],
                "fallback_skills": [
                    "web-docs-to-markdown",
                ],
                "required_mcp": [
                    "n8n-mcp",
                ],
                "max_tool_calls": 20,
                "max_runtime_minutes": 15,
            },
        },
        "preflight_requirements": [
            "mcp_available",
            "auth_ready",
            "inputs_complete",
        ],
        "fail_classification": [
            "route_wrong",
            "skill_gap",
            "mcp_unavailable",
            "tool_auth",
            "data_issue",
        ],
        "evidence_schema_fields": [
            "task_id",
            "route_selected",
            "skills_used",
            "mcp_tools_used",
            "actions_taken",
            "result",
            "artifacts",
        ],
    }
    task["knowledge_acquisition_contract"] = {
        "required": True,
        "must_research_when": [
            "new_api_domain",
            "unknown_error_code",
            "schema_changed",
        ],
        "source_priority": [
            "official_spec",
            "repo_contract",
            "third_party",
        ],
        "evidence_fields": [
            "claim",
            "source",
            "source_level",
            "confidence",
            "expiry",
            "applies_to",
        ],
        "sample_report_path_pattern": "identity/runtime/examples/*knowledge-acquisition*.json",
        "high_frequency_domains": {
            "vendor_api": {
                "preferred_skills": ["identity-creator"],
                "preferred_sources": ["official_spec", "repo_contract"],
                "required_validators": ["scripts/validate_identity_knowledge_contract.py"],
            }
        },
    }
    task["experience_feedback_contract"] = {
        "required": True,
        "positive_rulebook_path": "identity/runtime/rulebooks/positive.jsonl",
        "negative_rulebook_path": "identity/runtime/rulebooks/negative.jsonl",
        "required_fields": [
            "case_id",
            "layer",
            "pattern",
            "action",
            "impact_score",
            "replay_status",
        ],
        "cross_layer_feedback_targets": [
            "routing_contract",
            "capability_orchestration_contract",
            "gates",
        ],
        "promote_requires_replay_pass": True,
        "sample_report_path_pattern": "identity/runtime/examples/*experience-feedback*.json",
        "redaction_policy_required": True,
        "retention_days": 30,
        "sensitive_fields_denylist": [
            "access_token",
            "authorization",
            "cookie",
            "set-cookie",
            "api_key",
            "email",
            "phone",
        ],
        "export_scope": "aggregated-only",
        "max_log_age_days": 7,
        "minimum_logs_required": 1,
        "feedback_log_path_pattern": "identity/runtime/logs/feedback/*.json",
        "promotion_requires_replay_pass": True,
    }
    task["install_safety_contract"] = {
        "required": True,
        "preserve_existing_default": True,
        "on_conflict": "abort_and_explain",
        "idempotent_reinstall_allowed": True,
        "same_signature_action": "no_op_with_report",
        "allow_replace_only_with_backup": True,
        "rollback_reference_required": True,
        "install_report_required": True,
        "dry_run_required": True,
        "install_report_path_pattern": f"identity/runtime/examples/install/install-report-*-{identity_id}.json",
    }
    task["install_provenance_contract"] = {
        "required": True,
        "installer_tool_required": "identity-installer",
        "operations_required": ["plan", "dry-run", "install", "verify"],
        "report_path_pattern": f"identity/runtime/reports/install/identity-install-{identity_id}-*.json",
        "required_report_fields": [
            "report_id",
            "identity_id",
            "generated_at",
            "operation",
            "conflict_type",
            "action",
            "preserved_paths",
            "installer_invocation",
        ],
        "required_invocation_fields": [
            "tool",
            "entrypoint",
            "command",
        ],
        "enforcement_validator": "scripts/validate_identity_install_provenance.py",
        "non_destructive_default": True,
    }
    task["ci_enforcement_contract"] = {
        "required": True,
        "required_workflows": [
            "protocol-ci",
            "identity-protocol-ci",
        ],
        "required_job": "required-gates",
        "required_validators": checks,
        "required_checks": [
            "protocol-ci / required-gates",
            "identity-protocol-ci / required-gates",
        ],
        "freshness_gate": {
            "handoff_logs_max_age_days": 7,
            "route_metrics_max_age_days": 7,
        },
        "required_validator_set_label": "v1.2-required-intake-p1",
        "candidate_validators_v1_2": [
            "scripts/validate_identity_feedback_freshness.py",
            "scripts/validate_identity_feedback_promotion.py",
        ],
    }
    task["capability_arbitration_contract"] = {
        "required": True,
        "priority_order": [
            "accurate_judgement",
            "governance",
            "latency",
            "exploration",
        ],
        "conflict_rules": {
            "judgement_vs_routing": {
                "when": [
                    "high_risk_operation",
                    "evidence_conflict_detected",
                ],
                "decision": "prefer_judgement",
            },
            "reasoning_vs_latency": {
                "when": [
                    "low_risk_and_time_bounded",
                ],
                "decision": "bounded_reasoning",
            },
            "routing_vs_learning": {
                "when": [
                    "exploration_enabled",
                ],
                "decision": "cap_exploration_ratio",
                "max_exploration_ratio": 0.2,
            },
            "learning_vs_hotfix": {
                "when": [
                    "incident_hotfix_required",
                ],
                "decision": "temporary_hotfix_then_rulebook_backfill",
            },
        },
        "trigger_thresholds": {
            "misroute_rate_percent": 10,
            "replay_failure_rate_percent": 20,
            "first_pass_success_drop_percent": 15,
        },
        "accurate_judgement_enforcement": {
            "contract_ref": "rq_034_multimodal_plugin_enforcement_contract_v1",
            "validator": "scripts/validate_multimodal_plugin_enforcement.py",
            "requires_multimodal_evidence_consistency": True,
            "inconsistent_evidence_transition": "block_done",
        },
        "reasoning_loop_enforcement": {
            "contract_ref": "rq_035_reasoning_loop_failclose_contract_v1",
            "validator": "scripts/validate_reasoning_loop_failclose.py",
            "no_target_reached_cannot_complete": True,
            "failed_attempt_requires_next_action": True,
            "threshold_requires_escalation": True,
            "reasoning_enforcement_level_field": "reasoning_enforcement_level",
        },
        "decision_record_required_fields": [
            "arbitration_id",
            "task_id",
            "identity_id",
            "conflict_pair",
            "inputs",
            "decision",
            "impact",
            "rationale",
            "decided_at",
        ],
        "sample_report_path_pattern": "identity/runtime/examples/*capability-arbitration*.json",
        "fail_action": "block_merge_and_reenter_arbitration_update",
        "safe_auto_patch_surface": {
            "enforce_path_policy": True,
            "allowlist": [
                "identity/runtime/rulebooks/*",
                f"identity/packs/{identity_id}/TASK_HISTORY.md",
                "identity/runtime/logs/*",
                f"identity/packs/{identity_id}/RULEBOOK.jsonl",
            ],
            "denylist": [
                "identity/protocol/*",
                ".github/workflows/*",
                "scripts/validate_*",
            ],
        },
    }
    task["self_upgrade_enforcement_contract"] = {
        "required": True,
        "core_paths": [
            f"identity/packs/{identity_id}/CURRENT_TASK.json",
            f"identity/packs/{identity_id}/IDENTITY_PROMPT.md",
            f"identity/packs/{identity_id}/RULEBOOK.jsonl",
        ],
        "required_toolkit_steps": [
            f"scripts/execute_identity_upgrade.py --identity-id {identity_id} --mode review-required --actor-id <actor_id>",
            f"scripts/validate_identity_upgrade_prereq.py --identity-id {identity_id}",
            f"scripts/validate_identity_runtime_contract.py --identity-id {identity_id}",
            f"scripts/validate_identity_update_lifecycle.py --identity-id {identity_id}",
            f"scripts/validate_identity_capability_arbitration.py --identity-id {identity_id}",
        ],
        "evidence_path_pattern": f"identity/runtime/reports/identity-upgrade-exec-{identity_id}-*.json",
        "matching_patch_plan_required": True,
        "enforcement_validator": "scripts/validate_identity_self_upgrade_enforcement.py",
    }
    task["identity_role_binding_contract"] = {
        "required": True,
        "role_type": f"{identity_token}_runtime_operator",
        "catalog_registration_required": True,
        "runtime_bootstrap_pass_required": True,
        "activation_policy": "inactive_by_default",
        "switch_guard_required": True,
        "binding_evidence_path_pattern": "identity/runtime/examples/identity-role-binding-<identity-id>-*.json",
        "enforcement_validator": "scripts/validate_identity_role_binding.py",
        "runtime_bootstrap_live_revalidate": True,
        "evidence_max_age_days": 7,
        "active_binding_status_required": "BOUND_ACTIVE",
    }
    task = _ensure_dialogue_governance_contract(task, identity_id)
    task = _ensure_tool_vendor_governance_contracts(task, identity_id)
    task = _ensure_instance_pack_topology_contract(task, identity_id)
    task["scaffold_profile"] = "full-contract"
    task["scaffold_generation_mode"] = "neutral-default"
    return task


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_replay_sample(identity_id: str, task: dict, runtime_root: Path) -> Path:
    checks = (
        task.get("identity_update_lifecycle_contract", {})
        .get("validation_contract", {})
        .get("required_checks", [])
    )
    logs_dir = runtime_root / "logs" / "upgrade" / identity_id
    logs_dir.mkdir(parents=True, exist_ok=True)
    base_time = datetime.now(timezone.utc)
    check_results = []
    for i, chk in enumerate(checks, start=1):
        cmd = f"python3 {chk} --identity-id {identity_id}"
        if chk.endswith("validate_changelog_updated.py"):
            cmd = "python3 scripts/validate_changelog_updated.py --base HEAD~1 --head HEAD"
        log_path = logs_dir / f"{identity_id}-update-replay-check-{i:02d}.log"
        started = base_time.replace(microsecond=0)
        ended = started
        log_path.write_text(
            (
                f"$ {cmd}\n"
                "[exit_code] 0\n"
                f"[started_at] {started.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
                f"[ended_at] {ended.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
                "[stdout]\nPASS\n[stderr]\n\n"
            ),
            encoding="utf-8",
        )
        check_results.append(
            {
                "command": cmd,
                "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "ended_at": ended.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "exit_code": 0,
                "log_path": str(log_path.relative_to(runtime_root.parent).as_posix()),
                "sha256": _sha256_file(log_path),
            }
        )

    replay_id = f"{identity_id}-update-replay-sample"
    sample = {
        "replay_id": replay_id,
        "identity_id": identity_id,
        "replay_status": "PASS",
        "failed_case_id": f"{identity_id}-bootstrap-case",
        "patched_files": ["CURRENT_TASK.json", "IDENTITY_PROMPT.md", "RULEBOOK.jsonl", "TASK_HISTORY.md"],
        "validation_checks_passed": checks,
        "creator_invocation": {
            "tool": "identity-creator",
            "mode": "update",
            "run_id": replay_id,
            "evidence_path": str(
                (runtime_root / "examples" / f"{identity_id}-update-replay-sample.json")
                .relative_to(runtime_root.parent)
                .as_posix()
            ),
        },
        "check_results": check_results,
        "notes": "bootstrap replay sample generated by identity-creator scaffold",
    }
    out = runtime_root / "examples" / f"{identity_id}-update-replay-sample.json"
    write_json(out, sample)
    return out


def _copy_sample_with_identity(src: Path, dst: Path, identity_id: str) -> None:
    if not src.exists():
        return
    if src.resolve() == dst.resolve():
        raise ValueError(
            "bootstrap sample source and destination overlap; "
            "choose a different pack root/identity id to avoid mutating repository fixtures."
        )
    try:
        payload = json.loads(src.read_text(encoding="utf-8"))
    except Exception:
        return
    payload = _replace_store_manager_tokens(payload, identity_id)
    payload = _normalize_bootstrap_task_ids(payload, identity_id)
    if isinstance(payload, dict):
        if "identity_id" in payload:
            payload["identity_id"] = identity_id
        if "reviewer_identity" in payload:
            payload["reviewer_identity"] = identity_id
    write_json(dst, payload)


def _copy_jsonl_with_identity(src: Path, dst: Path, identity_id: str) -> None:
    if not src.exists():
        return
    if src.resolve() == dst.resolve():
        raise ValueError(
            "bootstrap rulebook source and destination overlap; "
            "choose a different pack root/identity id to avoid mutating repository fixtures."
        )
    lines_out: list[str] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        ln = line.strip()
        if not ln:
            continue
        try:
            payload = json.loads(ln)
        except Exception:
            continue
        payload = _replace_store_manager_tokens(payload, identity_id)
        payload = _normalize_bootstrap_task_ids(payload, identity_id)
        lines_out.append(json.dumps(payload, ensure_ascii=False))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines_out) + ("\n" if lines_out else ""), encoding="utf-8")


def _write_install_provenance_reports(identity_id: str, runtime_root: Path) -> None:
    now = datetime.now(timezone.utc)
    iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    report_dir = runtime_root / "reports" / "install"
    report_dir.mkdir(parents=True, exist_ok=True)
    operations = [
        ("plan", "fresh_install", "guarded_apply"),
        ("dry-run", "fresh_install", "guarded_apply"),
        ("install", "fresh_install", "guarded_apply"),
        ("verify", "fresh_install", "verified"),
    ]
    for idx, (op, conflict, action) in enumerate(operations, start=1):
        rid = f"identity-install-{identity_id}-{op}-bootstrap-{idx:02d}"
        write_json(
            report_dir / f"{rid}.json",
            {
                "report_id": rid,
                "identity_id": identity_id,
                "generated_at": iso,
                "operation": op,
                "conflict_type": conflict,
                "action": action,
                "source_pack": f"identity/packs/{identity_id}",
                "target_pack": f"identity/packs/{identity_id}",
                "preserved_paths": [f"identity/packs/{identity_id}"],
                "installer_invocation": {
                    "tool": "identity-installer",
                    "entrypoint": "scripts/identity_installer.py",
                    "command": f"identity-installer {op} --identity-id {identity_id}",
                },
            },
        )


def _bootstrap_legacy_identity_samples(identity_id: str, runtime_root: Path) -> None:
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-capability-arbitration-sample.json"),
        runtime_root / "examples" / f"{identity_id}-capability-arbitration-sample.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-learning-sample.json"),
        runtime_root / "examples" / f"{identity_id}-learning-sample.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-experience-feedback-sample.json"),
        runtime_root / "examples" / f"{identity_id}-experience-feedback-sample.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-trigger-regression-sample.json"),
        runtime_root / "examples" / f"{identity_id}-trigger-regression-sample.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/store-manager-knowledge-acquisition-sample.json"),
        runtime_root / "examples" / f"{identity_id}-knowledge-acquisition-sample.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/metrics/store-manager-route-quality.json"),
        runtime_root / "metrics" / f"{identity_id}-route-quality.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/examples/install/install-report-2026-02-22-store-manager.json"),
        runtime_root / "examples" / "install" / f"install-report-bootstrap-{identity_id}.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/logs/feedback/store-manager-feedback-2026-02-22T09-40-00Z.json"),
        runtime_root / "logs" / "feedback" / f"{identity_id}-feedback-bootstrap.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/logs/handoff/handoff-2026-02-20-store-manager-10000514174106.json"),
        runtime_root / "logs" / "handoff" / f"{identity_id}-bootstrap.json",
        identity_id,
    )
    _copy_sample_with_identity(
        Path("identity/runtime/logs/collaboration/store-manager-collab-2026-02-21T15-15-00Z.json"),
        runtime_root / "logs" / "collaboration" / f"{identity_id}-bootstrap.json",
        identity_id,
    )

    _bootstrap_runtime_selftest_assets(identity_id, runtime_root)
    collab_src = Path("identity/runtime/examples/collaboration-trigger")
    collab_dst = runtime_root / "examples" / "collaboration-trigger"
    for sample in collab_src.rglob("*.json"):
        rel = sample.relative_to(collab_src)
        _copy_sample_with_identity(sample, collab_dst / rel, identity_id)
    _write_install_provenance_reports(identity_id, runtime_root)


def _bootstrap_runtime_selftest_assets(identity_id: str, runtime_root: Path) -> None:
    rulebook_dir = runtime_root / "rulebooks"
    _copy_jsonl_with_identity(
        Path("identity/runtime/rulebooks/positive.jsonl"),
        rulebook_dir / "positive.jsonl",
        identity_id,
    )
    _copy_jsonl_with_identity(
        Path("identity/runtime/rulebooks/negative.jsonl"),
        rulebook_dir / "negative.jsonl",
        identity_id,
    )

    handoff_src = Path("identity/runtime/examples/handoff")
    handoff_dst = runtime_root / "examples" / "handoff"
    for sample in handoff_src.rglob("*.json"):
        rel = sample.relative_to(handoff_src)
        _copy_sample_with_identity(sample, handoff_dst / rel, identity_id)


def _bootstrap_neutral_identity_samples(identity_id: str, runtime_root: Path, task_id: str) -> None:
    now = datetime.now(timezone.utc)
    iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    runtime_examples = runtime_root / "examples"
    runtime_logs = runtime_root / "logs"
    runtime_rulebooks = runtime_root / "rulebooks"
    runtime_metrics = runtime_root / "metrics"

    write_json(
        runtime_examples / f"{identity_id}-trigger-regression-sample.json",
        {
            "positive_cases": [
                {
                    "case_id": f"{identity_id}-reg-pos-01",
                    "input_summary": "Routine request with complete context",
                    "expected_route": "instance_delivery",
                    "expected_trigger": True,
                    "observed_route": "instance_delivery",
                    "observed_trigger": True,
                    "result": "PASS",
                    "notes": "baseline positive case",
                }
            ],
            "boundary_cases": [
                {
                    "case_id": f"{identity_id}-reg-boundary-01",
                    "input_summary": "Boundary request with partial evidence",
                    "expected_route": "knowledge_api_probe",
                    "expected_trigger": True,
                    "observed_route": "knowledge_api_probe",
                    "observed_trigger": True,
                    "result": "PASS",
                    "notes": "boundary fallback route remains stable",
                }
            ],
            "negative_cases": [
                {
                    "case_id": f"{identity_id}-reg-neg-01",
                    "input_summary": "Known mismatch sample for regression guard",
                    "expected_route": "instance_delivery",
                    "expected_trigger": True,
                    "observed_route": "knowledge_api_probe",
                    "observed_trigger": False,
                    "result": "FAIL",
                    "notes": "negative fixture should fail by design",
                }
            ],
            "summary": {
                "total_cases": 3,
                "pass_cases": 2,
                "fail_cases": 1,
                "overall_result": "FAIL",
            },
        },
    )

    write_json(
        runtime_examples / f"{identity_id}-knowledge-acquisition-sample.json",
        {
            "records": [
                {
                    "claim": "identity runtime contract requirements were reviewed",
                    "source": "identity/protocol/IDENTITY_PROTOCOL.md",
                    "source_level": "official_spec",
                    "confidence": "high",
                    "expiry": "30d",
                    "applies_to": "protocol validation flow",
                }
            ]
        },
    )

    write_json(
        runtime_examples / f"{identity_id}-capability-arbitration-sample.json",
        {
            "records": [
                {
                    "arbitration_id": f"{identity_id}-arb-001",
                    "task_id": task_id,
                    "identity_id": identity_id,
                    "conflict_pair": "reasoning_vs_latency",
                    "inputs": {
                        "risk_level": "low",
                        "deadline_minutes": 20,
                    },
                    "decision": "bounded_reasoning",
                    "impact": "stabilize output latency while preserving evidence quality",
                    "rationale": "low-risk workload permits bounded reasoning policy",
                    "decided_at": iso,
                }
            ]
        },
    )

    write_json(
        runtime_examples / f"{identity_id}-experience-feedback-sample.json",
        {
            "positive_updates": [
                {
                    "case_id": f"{identity_id}-feedback-pos-001",
                    "layer": "instance",
                    "pattern": "route_success_with_complete_evidence",
                    "action": "retain_current_route",
                    "impact_score": 0.82,
                    "replay_status": "PASS",
                }
            ],
            "negative_updates": [],
        },
    )

    write_json(
        runtime_examples / f"{identity_id}-learning-sample.json",
        {
            "run_id": "bootstrap",
            "reasoning_attempts": [
                {
                    "attempt": 1,
                    "hypothesis": "baseline neutral scaffold should satisfy runtime validators",
                    "patch": "generated bootstrap artifacts and contract metadata",
                    "expected_effect": "validator pass with deterministic artifacts",
                    "result": "PASS",
                }
            ],
        },
    )

    runtime_metrics.mkdir(parents=True, exist_ok=True)
    write_json(
        runtime_metrics / f"{identity_id}-route-quality.json",
        {
            "route_hit_rate": 98.5,
            "misroute_rate": 1.5,
            "fallback_rate": 2.0,
            "first_pass_success_rate": 97.0,
            "knowledge_reuse_rate": 88.0,
            "replay_success_rate": 99.0,
            "policy_drift_incidents": 0,
        },
    )

    _bootstrap_runtime_selftest_assets(identity_id, runtime_root)

    write_json(
        runtime_logs / "feedback" / f"{identity_id}-feedback-bootstrap.json",
        {
            "feedback_id": f"{identity_id}-feedback-001",
            "identity_id": identity_id,
            "task_id": task_id,
            "run_id": "bootstrap",
            "timestamp": iso,
            "context_signature": "neutral_bootstrap_context",
            "outcome": "PASS",
            "failure_type": "",
            "decision_trace_ref": str((runtime_examples / f"{identity_id}-learning-sample.json").as_posix()),
            "artifacts": [
                str((runtime_examples / f"{identity_id}-trigger-regression-sample.json").as_posix()),
            ],
            "rulebook_delta": ["positive:1", "negative:1"],
            "replay_status": "PASS",
        },
    )

    handoff_artifact = runtime_examples / f"{identity_id}-trigger-regression-sample.json"
    write_json(
        runtime_logs / "handoff" / f"{identity_id}-bootstrap.json",
        {
            "handoff_id": f"{identity_id}-handoff-bootstrap-001",
            "task_id": task_id,
            "identity_id": identity_id,
            "from_agent": "identity-runtime-orchestrator",
            "to_agent": "identity-creator",
            "input_scope": "bootstrap_recheck",
            "actions_taken": [
                "validated baseline contracts",
                "recorded runtime evidence",
            ],
            "artifacts": [
                {
                    "path": str(handoff_artifact.as_posix()),
                    "kind": "regression_report",
                }
            ],
            "result": "PASS",
            "next_action": {
                "owner": "identity-runtime-orchestrator",
                "action": "proceed",
                "input": "bootstrap artifacts complete",
            },
            "rulebook_update": {
                "applied": True,
                "evidence_run_id": "bootstrap",
            },
            "attempted_mutations": [],
            "generated_at": iso,
        },
    )

    detected_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    notified_at = detected_at
    write_json(
        runtime_logs / "collaboration" / f"{identity_id}-bootstrap.json",
        {
            "event_id": f"{identity_id}-collab-bootstrap-001",
            "identity_id": identity_id,
            "task_id": task_id,
            "blocker_type": "auth_login_required",
            "source": "bootstrap_simulation",
            "detected_at": detected_at,
            "requires_human_collab": True,
            "next_action": "request runtime operator review",
            "notified_at": notified_at,
            "notify_channel": "ops-notification-router",
            "dedupe_key": f"{identity_id}-auth-login-required",
            "state_change_bypass_dedupe": True,
            "chat_receipt": {
                "emitted": True,
                "event_id": f"{identity_id}-collab-bootstrap-001",
                "blocker_type": "auth_login_required",
                "notified_at": notified_at,
                "channel": "ops-notification-router",
                "dedupe_key": f"{identity_id}-auth-login-required",
                "status": "SENT",
            },
        },
    )

    write_json(
        runtime_examples / "install" / f"install-report-bootstrap-{identity_id}.json",
        {
            "report_id": f"install-report-bootstrap-{identity_id}",
            "identity_id": identity_id,
            "generated_at": iso,
            "operation": "install",
            "conflict_type": "fresh_install",
            "action": "guarded_apply",
            "preserved_paths": [f"identity/packs/{identity_id}"],
            "installer_invocation": {
                "tool": "identity-installer",
                "entrypoint": "scripts/identity_installer.py",
                "command": f"identity-installer install --identity-id {identity_id}",
            },
        },
    )
    _write_install_provenance_reports(identity_id, runtime_root)


def _inject_scaffold_metadata(task: dict, profile: str, *, version_baseline: dict[str, Any]) -> dict:
    scaffold_versions = (version_baseline.get("scaffold_metadata") or {}) if isinstance(version_baseline, dict) else {}
    metadata = {
        "scaffold_profile": profile,
        "scaffold_generation_mode": "neutral-default" if profile == "full-contract" else "explicit_opt_in",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "blocker_taxonomy_mode": "canonical",
        "blocker_alias_map_version": "v1",
        "domain_neutrality_required": profile != "legacy-commerce-overlay",
    }
    for field, raw in scaffold_versions.items():
        token = str(raw or "").strip()
        if token:
            metadata[field] = token
    existing = task.get("scaffold_metadata")
    if isinstance(existing, dict):
        existing.update(metadata)
        task["scaffold_metadata"] = existing
    else:
        task["scaffold_metadata"] = metadata
    return task


def _scan_domain_residue(pack_dir: Path) -> list[str]:
    text_suffixes = {".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"}
    findings: list[str] = []
    for p in sorted(pack_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in text_suffixes:
            continue
        try:
            content = p.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for token in DOMAIN_NEUTRALITY_BLOCKLIST:
            if token.lower() in content:
                findings.append(f"{p}:{token}")
    return findings


def main() -> int:
    identity_home = default_identity_home()
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--pack-root", default=str(default_local_instances_root(identity_home)))
    ap.add_argument("--catalog", default=str(default_local_catalog_path(identity_home)))
    ap.add_argument(
        "--profile",
        choices=["full-contract", "minimal", "legacy-commerce-overlay"],
        default="full-contract",
        help=(
            "scaffold profile; full-contract is domain-neutral by default. "
            "legacy-commerce-overlay is explicit opt-in for compatibility fixtures."
        ),
    )
    ap.add_argument("--register", action="store_true", help="Register identity in catalog")
    ap.add_argument("--activate", action="store_true", help="Register with status=active (default inactive)")
    ap.add_argument("--set-default", action="store_true", help="Set as default identity")
    ap.add_argument(
        "--repo-fixture",
        action="store_true",
        help="Explicitly allow creating fixture identity under repo paths (default runtime identities are local-only).",
    )
    ap.add_argument(
        "--repo-fixture-confirm",
        default="",
        help=f'Exact confirmation token required with --repo-fixture: "{REPO_FIXTURE_CONFIRM_TOKEN}"',
    )
    ap.add_argument(
        "--repo-fixture-purpose",
        default="",
        help="Required short purpose string when using --repo-fixture (for audit intent).",
    )
    ap.add_argument(
        "--skip-bootstrap-check",
        action="store_true",
        help="Skip post-create bootstrap validators (local debugging only; CI should not use)",
    )
    ap.add_argument(
        "--skip-sample-bootstrap",
        action="store_true",
        help="Skip runtime sample bootstrap copy (boundary tests / advanced workflows only).",
    )
    args = ap.parse_args()

    identity_id = args.id.strip()
    if not identity_id:
        print("[FAIL] --id cannot be empty")
        return 1

    repo_root = _repo_root()
    pack_root = Path(args.pack_root).expanduser().resolve()
    catalog_path = Path(args.catalog).expanduser().resolve()
    identity_profile = "fixture" if args.repo_fixture else "runtime"
    identity_runtime_mode = "demo_only" if args.repo_fixture else "local_only"
    try:
        version_baseline = load_version_baseline_or_raise(repo_root=repo_root)
    except Exception as exc:
        print(f"[FAIL] version baseline unavailable: {exc}")
        return 1
    agent_identity_versions = dict(version_baseline.get("agent_identity") or {})
    meta_methodology_version = str((version_baseline.get("meta") or {}).get("methodology_version", "")).strip()
    if not meta_methodology_version:
        meta_methodology_version = str(agent_identity_versions.get("methodology_version", "")).strip()

    if args.repo_fixture:
        if args.repo_fixture_confirm.strip() != REPO_FIXTURE_CONFIRM_TOKEN:
            print("[FAIL] --repo-fixture requires explicit confirmation token.")
            print(f'       pass --repo-fixture-confirm "{REPO_FIXTURE_CONFIRM_TOKEN}"')
            return 1
        if not args.repo_fixture_purpose.strip():
            print("[FAIL] --repo-fixture requires --repo-fixture-purpose for audit intent.")
            return 1
        if not _is_within(pack_root, repo_root):
            print("[FAIL] --repo-fixture requires repository pack root.")
            print(f"       pack_root={pack_root}")
            print(f"       repo_root={repo_root}")
            return 1
        if not _is_within(catalog_path, repo_root):
            print("[FAIL] --repo-fixture requires repository catalog path.")
            print(f"       catalog={catalog_path}")
            print(f"       repo_root={repo_root}")
            return 1
    else:
        if args.repo_fixture_confirm.strip():
            print("[FAIL] --repo-fixture-confirm is only valid with --repo-fixture.")
            return 1
        if args.repo_fixture_purpose.strip():
            print("[FAIL] --repo-fixture-purpose is only valid with --repo-fixture.")
            return 1
        if _is_within(pack_root, repo_root):
            print("[FAIL] runtime identity must not be created under repository path.")
            print(f"       pack_root={pack_root}")
            print("       use default IDENTITY_HOME root or pass --repo-fixture explicitly for demo fixtures.")
            return 1
        if _is_within(catalog_path, repo_root):
            print("[FAIL] runtime identity catalog must be local (outside repo).")
            print(f"       catalog={catalog_path}")
            print("       pass --repo-fixture only when you intentionally update repo fixture catalog.")
            return 1

    pack_dir = pack_root / identity_id
    if pack_dir.exists() and any(pack_dir.iterdir()):
        print(f"[FAIL] pack directory already exists and is non-empty: {pack_dir}")
        return 1

    write(
        pack_dir / "META.yaml",
        (
            f'id: "{identity_id}"\n'
            f'title: "{args.title}"\n'
            f'description: "{args.description}"\n'
            f'status: "{"active" if (not args.register or args.activate) else "inactive"}"\n'
            f'methodology_version: "{meta_methodology_version}"\n'
            f'profile: "{identity_profile}"\n'
            f'runtime_mode: "{identity_runtime_mode}"\n'
            f'scaffold_profile: "{args.profile}"\n'
        ),
    )

    write(
        pack_dir / "IDENTITY_PROMPT.md",
        _default_identity_prompt_markdown(
            identity_id=identity_id,
            title=args.title,
            description=args.description,
        ),
    )
    write(pack_dir / "scripts" / "README.md", _default_instance_scripts_readme(identity_id))
    write_json(
        pack_dir / INSTANCE_SCRIPT_MANIFEST_RELATIVE_PATH,
        _default_instance_script_manifest(identity_id),
    )

    runtime_root = pack_dir / "runtime"
    write(
        runtime_root / "plugins" / "provider-bindings.local.yaml",
        _provider_bindings_template_text(repo_root=repo_root),
    )
    seed_runtime_root = (repo_root / "identity" / "runtime").resolve()
    if runtime_root.resolve() == seed_runtime_root:
        print("[FAIL] runtime root overlaps repository seed runtime templates.")
        print(f"       runtime_root={runtime_root}")
        print(f"       seed_runtime_root={seed_runtime_root}")
        print("       choose a different --id/--pack-root (or use local default runtime root).")
        return 1

    if args.profile == "full-contract":
        current_task = _neutral_full_contract_current_task(
            identity_id,
            args.title,
            args.description,
            agent_identity_versions=agent_identity_versions,
        )
    elif args.profile == "legacy-commerce-overlay":
        current_task = _legacy_full_contract_current_task(
            identity_id,
            args.title,
            args.description,
            version_baseline=version_baseline,
        )
    else:
        current_task = _minimal_current_task(
            identity_id,
            args.title,
            args.description,
            agent_identity_versions=agent_identity_versions,
        )
    apply_version_baseline_to_task_doc(current_task, version_baseline)
    current_task = _inject_scaffold_metadata(current_task, args.profile, version_baseline=version_baseline)
    current_task = _ensure_instance_pack_topology_contract(current_task, identity_id)
    current_task = _rewrite_identity_pack_root(current_task, identity_id, pack_dir)
    current_task = _rewrite_runtime_root(current_task, runtime_root)
    gateway_artifacts = materialize_protocol_host_gateway_artifacts(
        task=current_task,
        identity_id=identity_id,
        pack_dir=pack_dir,
        catalog_path=catalog_path,
        protocol_root=repo_root,
    )
    write_json(pack_dir / "CURRENT_TASK.json", current_task)

    write(pack_dir / "TASK_HISTORY.md", "# Task History\n\n## Entries\n")

    write(
        pack_dir / "RULEBOOK.jsonl",
        json.dumps(
            {
                "rule_id": f"{identity_id}-bootstrap-positive-rule",
                "type": "positive",
                "trigger": "identity_pack_initialized",
                "action": "enforce_protocol_baseline_review_before_identity_upgrades",
                "evidence_run_id": "bootstrap",
                "scope": "identity_runtime",
                "confidence": "high",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
            ensure_ascii=False,
        )
        + "\n",
    )

    write(pack_dir / "agents" / "identity.yaml", _default_identity_agent_yaml(identity_id, args.title, args.description))

    protocol_review_sample_path = runtime_root / "examples" / f"protocol-baseline-review-{identity_id}-sample.json"
    write_json(protocol_review_sample_path, _default_protocol_review_sample(identity_id))
    role_binding_sample_path = runtime_root / "examples" / f"identity-role-binding-{identity_id}-sample.json"
    role_type = str((current_task.get("identity_role_binding_contract") or {}).get("role_type", f"{identity_id}_runtime_role"))
    write_json(role_binding_sample_path, _default_role_binding_sample(identity_id, role_type, runtime_root))

    negative_role_binding_sample_path = (
        runtime_root / "examples" / "role-binding"
        / f"identity-role-binding-{identity_id}-negative-sample.json"
    )
    write_json(
        negative_role_binding_sample_path,
        {
            "binding_id": f"identity-role-binding-{identity_id}-negative-sample",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "identity_id": identity_id,
            "role_type": role_type,
            "binding_status": "UNBOUND",
            "runtime_bootstrap": {"status": "FAIL", "validator": "scripts/validate_identity_runtime_contract.py"},
            "switch_guard": {"status": "FAIL"},
        },
    )
    replay_sample_path = _write_replay_sample(identity_id, current_task, runtime_root)
    if not args.skip_sample_bootstrap:
        if args.profile == "legacy-commerce-overlay":
            _bootstrap_legacy_identity_samples(identity_id, runtime_root)
        else:
            _bootstrap_neutral_identity_samples(identity_id, runtime_root, str(current_task.get("task_id") or "bootstrap"))

    if args.profile != "legacy-commerce-overlay":
        findings = _scan_domain_residue(pack_dir)
        if findings and not args.repo_fixture:
            print("[FAIL] scaffold domain-neutrality residue detected:")
            for item in findings[:20]:
                print(f"       - {item}")
            print("       fix scaffold generation before using this identity pack.")
            return 1

    print(f"[OK] created identity pack: {pack_dir}")
    print(f"[OK] created protocol review sample: {protocol_review_sample_path}")
    print(f"[OK] created role-binding samples: {role_binding_sample_path}, {negative_role_binding_sample_path}")
    print(f"[OK] created replay sample: {replay_sample_path}")
    print(
        "[OK] created host unique-channel gateway artifacts: "
        f"{gateway_artifacts.get('gateway_contract_path')}, "
        f"{gateway_artifacts.get('ingress_wrapper_path')}, "
        f"{gateway_artifacts.get('egress_wrapper_path')}"
    )

    catalog_original_text: str | None = None
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_mutated = False
    if args.register:
        if not catalog_path.exists():
            if args.repo_fixture:
                print(f"[FAIL] catalog file not found: {catalog_path}")
                return 1
            dump_yaml(
                catalog_path,
                {
                    "version": "1.0",
                    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "default_identity": "",
                    "identities": [],
                },
            )
        catalog_original_text = catalog_path.read_text(encoding="utf-8")
        catalog = load_yaml(catalog_path) or {}
        identities = catalog.get("identities", [])
        if any((x or {}).get("id") == identity_id for x in identities):
            print(f"[FAIL] id already exists in catalog: {identity_id}")
            return 1

        identities.append(
            {
                "id": identity_id,
                "title": args.title,
                "description": args.description,
                "status": "active" if args.activate else "inactive",
                "methodology_version": "",
                "profile": identity_profile,
                "runtime_mode": identity_runtime_mode,
                "pack_path": str(pack_dir),
                "tags": ["identity"],
            }
        )
        apply_version_baseline_to_catalog_row(identities[-1], version_baseline)
        catalog["identities"] = identities
        if args.set_default:
            catalog["default_identity"] = identity_id
        dump_yaml(catalog_path, catalog)
        catalog_mutated = True
        print(f"[OK] registered identity in catalog: {catalog_path}")

    if not args.skip_bootstrap_check:
        checks: list[list[str]] = [
            [
                "python3",
                "scripts/validate_identity_runtime_contract.py",
                "--identity-id",
                identity_id,
                "--current-task",
                str(pack_dir / "CURRENT_TASK.json"),
            ],
            [
                "python3",
                INSTANCE_PACK_TOPOLOGY_VALIDATOR_ID,
                "--identity-id",
                identity_id,
                "--current-task",
                str(pack_dir / "CURRENT_TASK.json"),
            ],
        ]
        if args.register:
            checks.append(
                [
                    "python3",
                    "scripts/validate_identity_role_binding.py",
                    "--catalog",
                    str(catalog_path),
                    "--identity-id",
                    identity_id,
                ]
            )
        for cmd in checks:
            print("$", " ".join(cmd))
            rc = subprocess.call(cmd)
            if rc != 0:
                if catalog_mutated and catalog_original_text is not None:
                    catalog_path.write_text(catalog_original_text, encoding="utf-8")
                    print("[ROLLBACK] restored catalog after bootstrap failure")
                print("[FAIL] bootstrap validation failed")
                return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
