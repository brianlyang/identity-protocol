#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
import yaml

from create_identity_pack import (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID,
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
    DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
    DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID,
    DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
    DOWNSINK_LITERAL_LOCK_SCAN_GLOBS,
    DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID,
    DOWNSINK_REQUIRED_DOMAINS,
    HOST_GATEWAY_BROADCAST_ACK_PATTERN,
    HOST_GATEWAY_BROADCAST_INDEX_FILE,
    HOST_GATEWAY_BROADCAST_ITEMS_DIR,
    HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN,
    HOST_GATEWAY_BROADCAST_SCHEMA_FILE,
    HOST_GATEWAY_BROADCAST_STATE_FILE,
    HOST_GATEWAY_CONTRACT_ID,
    HOST_GATEWAY_CONTRACT_KEY,
    HOST_GATEWAY_INGRESS_DISPATCH_TOKEN,
    HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
    HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH,
    HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
    HOST_GATEWAY_REQUIRED_DISPATCH_MODE,
    HOST_GATEWAY_REQUIRED_RELEASE_MODE,
    HOST_GATEWAY_REQUIRED_TUPLE_FIELDS,
    HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY,
    HOST_VISIBLE_SURFACE_RECEIPT_PATTERN,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID,
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
    HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE,
    HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR,
    HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED,
    HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS,
    HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS,
    HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS,
    HOST_VISIBLE_SURFACE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE,
    HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE,
    UNIQUE_EGRESS_SCRIPT,
    UNIQUE_INGRESS_SCRIPT,
    _derived_prompt_conformance_contract_skeleton,
    _ensure_intake_p1_contracts,
    _multimodal_plugin_enforcement_contract_skeleton,
    _protocol_lane_activation_headstamp_contract_skeleton,
    _host_gateway_signer_secret_env,
    _host_gateway_wrapper_template_attestation_policy,
    _host_visible_surface_registry_contract_skeleton,
    _protocol_downsink_path_immutability_contract_skeleton,
    _protocol_host_unique_channel_contract_skeleton,
    _protocol_unique_entry_gate_contract_skeleton,
    _prompt_bootstrap_capability_contract_skeleton,
    _prompt_capability_matrix_contract_skeleton,
    _prompt_kernel_executable_coupling_contract_skeleton,
    _reasoning_loop_failclose_contract_skeleton,
    _skill_frontmatter_contract_skeleton,
    _skill_installation_supply_chain_contract_skeleton,
    _skill_sync_drift_guard_contract_skeleton,
    materialize_protocol_host_gateway_artifacts,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task
from version_baseline_common import (
    apply_version_baseline_to_catalog_row,
    apply_version_baseline_to_meta_doc,
    apply_version_baseline_to_task_doc,
    load_version_baseline_or_raise,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


REQUIRED_INTAKE_KEYS = (
    "multi_track_cross_verification_contract_v1",
    "intake_evidence_quorum_contract_v1",
    "fallback_taxonomy_normalization_contract_v1",
    "dedup_monotonic_winner_contract_v1",
    "cross_workflow_evidence_schema_contract_v1",
    "skill_path_integrity_contract_v1",
    "route_workflow_version_pinning_contract_v1",
    "skill_installation_supply_chain_contract_v1",
    "skill_frontmatter_contract_v1",
    "skill_sync_drift_guard_contract_v1",
)

REQUIRED_PROMPT_KEYS = (
    "prompt_bootstrap_capability_contract_v1",
    "prompt_capability_matrix_fail_closed_contract_v1",
    "derived_prompt_conformance_contract_v1",
    "prompt_import_executable_coupling_contract_v1",
)

REQUIRED_MULTIMODAL_KEYS = (
    "multimodal_plugin_enforcement_contract_v1",
)
REQUIRED_REASONING_KEYS = (
    "reasoning_loop_failclose_contract_v1",
)
REQUIRED_ENTRY_KEYS = (
    "protocol_unique_entry_gate_contract_v1",
)
REQUIRED_LANE_HEADSTAMP_KEYS = (
    "protocol_lane_activation_headstamp_contract_v1",
)
REQUIRED_HOST_GATEWAY_KEYS = (
    HOST_GATEWAY_CONTRACT_KEY,
)
REQUIRED_HOST_VISIBLE_SURFACE_KEYS = (
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY,
)
REQUIRED_DOWNSINK_KEYS = (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
)

PROMPT_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "prompt_bootstrap_capability_contract_v1": _prompt_bootstrap_capability_contract_skeleton(),
    "prompt_capability_matrix_fail_closed_contract_v1": _prompt_capability_matrix_contract_skeleton(),
    "derived_prompt_conformance_contract_v1": _derived_prompt_conformance_contract_skeleton(),
    "prompt_import_executable_coupling_contract_v1": _prompt_kernel_executable_coupling_contract_skeleton(),
}

MULTIMODAL_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "multimodal_plugin_enforcement_contract_v1": _multimodal_plugin_enforcement_contract_skeleton(),
}
REASONING_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "reasoning_loop_failclose_contract_v1": _reasoning_loop_failclose_contract_skeleton(),
}
ENTRY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "protocol_unique_entry_gate_contract_v1": _protocol_unique_entry_gate_contract_skeleton(),
}
LANE_HEADSTAMP_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "protocol_lane_activation_headstamp_contract_v1": _protocol_lane_activation_headstamp_contract_skeleton(),
}
HOST_GATEWAY_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    HOST_GATEWAY_CONTRACT_KEY: _protocol_host_unique_channel_contract_skeleton("default"),
}
HOST_VISIBLE_SURFACE_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY: _host_visible_surface_registry_contract_skeleton(),
}
DOWNSINK_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY: _protocol_downsink_path_immutability_contract_skeleton(),
}
SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS: dict[str, dict[str, Any]] = {
    "skill_installation_supply_chain_contract_v1": _skill_installation_supply_chain_contract_skeleton("default"),
    "skill_frontmatter_contract_v1": _skill_frontmatter_contract_skeleton(),
    "skill_sync_drift_guard_contract_v1": _skill_sync_drift_guard_contract_skeleton(),
}

CAPABILITY_DRIVER_VALIDATOR_IDS: tuple[str, ...] = (
    "scripts/validate_identity_tool_installation.py",
    "scripts/validate_identity_vendor_api_discovery.py",
    "scripts/validate_identity_vendor_api_solution.py",
)

ERR_PROMPT_WIRE_MISSING = "IP-PROMPT-WIRE-002"
ERR_PROMPT_WIRE_INVALID = "IP-PROMPT-WIRE-003"
ERR_MM_WIRE_MISSING = "IP-MM-WIRE-001"
ERR_MM_WIRE_INVALID = "IP-MM-WIRE-002"
ERR_RL_WIRE_MISSING = "IP-RL-WIRE-001"
ERR_RL_WIRE_INVALID = "IP-RL-WIRE-002"
ERR_ENTRY_WIRE_MISSING = "IP-GATE-ENTRY-001"
ERR_ENTRY_WIRE_INVALID = "IP-GATE-ENTRY-002"
ERR_LANE_HEADSTAMP_WIRE_MISSING = "IP-LANE-WIRE-001"
ERR_LANE_HEADSTAMP_WIRE_INVALID = "IP-LANE-WIRE-002"
ERR_HOST_GATEWAY_WIRE_MISSING = "IP-GATE-ENTRY-001"
ERR_HOST_GATEWAY_WIRE_INVALID = "IP-GATE-ENTRY-002"
ERR_VISIBLE_SURFACE_WIRE_MISSING = "IP-HDSTAMP-001"
ERR_VISIBLE_SURFACE_WIRE_INVALID = "IP-HDSTAMP-003"
ERR_DOWNSINK_WIRE_MISSING = "IP-DSPATH-001"
ERR_DOWNSINK_WIRE_INVALID = "IP-DSPATH-002"
REASONING_LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
REASONING_MIN_LEVEL = "L3"
FILE_GOVERNANCE_SKILL_ID = "ai-folder-governance"
ENTRY_SCRIPT = UNIQUE_INGRESS_SCRIPT
ENTRY_BUNDLE_KEY = "required_gate_bundle_runner"


def _norm_level(value: Any) -> str:
    token = str(value or "").strip().upper()
    return token if token in REASONING_LEVEL_RANK else ""


def _ensure_reasoning_floor(node: dict[str, Any]) -> bool:
    changed = False
    current_level = _norm_level(node.get("reasoning_enforcement_level"))
    if not current_level or REASONING_LEVEL_RANK[current_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        node["reasoning_enforcement_level"] = REASONING_MIN_LEVEL
        changed = True

    current_min_level = _norm_level(node.get("minimum_enforcement_level"))
    if not current_min_level or REASONING_LEVEL_RANK[current_min_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        node["minimum_enforcement_level"] = REASONING_MIN_LEVEL
        changed = True

    enforcement = node.get("reasoning_enforcement")
    if not isinstance(enforcement, dict):
        enforcement = {}
        node["reasoning_enforcement"] = enforcement
        changed = True

    default_level = _norm_level(enforcement.get("default_level"))
    if not default_level or REASONING_LEVEL_RANK[default_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        enforcement["default_level"] = REASONING_MIN_LEVEL
        changed = True

    minimum_level = _norm_level(enforcement.get("minimum_level"))
    if not minimum_level or REASONING_LEVEL_RANK[minimum_level] < REASONING_LEVEL_RANK[REASONING_MIN_LEVEL]:
        enforcement["minimum_level"] = REASONING_MIN_LEVEL
        changed = True
    return changed


def _merge_required_skills(node: dict[str, Any], required_skill_id: str) -> bool:
    existing = node.get("required_skills")
    if isinstance(existing, list):
        values = [str(x).strip() for x in existing if str(x).strip()]
    else:
        values = []
    if required_skill_id in values:
        return False
    values.append(required_skill_id)
    node["required_skills"] = values
    return True


def _deep_merge(current: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in (current or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(value, merged[key])
        else:
            merged[key] = value
    return merged


def _merge_validator_ids(container: dict[str, Any], key: str, validator_ids: tuple[str, ...]) -> tuple[bool, list[str]]:
    changed = False
    node = container.get(key)
    if isinstance(node, list):
        rows = [str(x).strip() for x in node if str(x).strip()]
    else:
        rows = []
    appended: list[str] = []
    for validator_id in validator_ids:
        if validator_id in rows:
            continue
        rows.append(validator_id)
        appended.append(validator_id)
        changed = True
    if changed:
        container[key] = rows
    return changed, appended


def _normalize_skill_supply_chain_contracts(task_doc: dict[str, Any], identity_id: str) -> list[str]:
    restored: list[str] = []
    defaults = {
        "skill_installation_supply_chain_contract_v1": _skill_installation_supply_chain_contract_skeleton(identity_id),
        "skill_frontmatter_contract_v1": _skill_frontmatter_contract_skeleton(),
        "skill_sync_drift_guard_contract_v1": _skill_sync_drift_guard_contract_skeleton(),
    }
    for key, default in defaults.items():
        node = task_doc.get(key)
        if not isinstance(node, dict):
            task_doc[key] = json.loads(json.dumps(default))
            restored.append(key)
            continue
        task_doc[key] = _deep_merge(node, default)
    return restored


def _normalize_capability_driver_validators(task_doc: dict[str, Any]) -> dict[str, list[str]]:
    restored: dict[str, list[str]] = {
        "required_validators": [],
        "ci_enforcement_contract.required_validators": [],
        "identity_update_lifecycle_contract.validation_contract.required_checks": [],
    }
    _, appended_root = _merge_validator_ids(task_doc, "required_validators", CAPABILITY_DRIVER_VALIDATOR_IDS)
    if appended_root:
        restored["required_validators"].extend(appended_root)

    ci_contract = task_doc.get("ci_enforcement_contract")
    if isinstance(ci_contract, dict):
        _, appended_ci = _merge_validator_ids(ci_contract, "required_validators", CAPABILITY_DRIVER_VALIDATOR_IDS)
        if appended_ci:
            restored["ci_enforcement_contract.required_validators"].extend(appended_ci)

    lifecycle_contract = task_doc.get("identity_update_lifecycle_contract")
    validation_contract = lifecycle_contract.get("validation_contract") if isinstance(lifecycle_contract, dict) else None
    if isinstance(validation_contract, dict):
        _, appended_lc = _merge_validator_ids(validation_contract, "required_checks", CAPABILITY_DRIVER_VALIDATOR_IDS)
        if appended_lc:
            restored["identity_update_lifecycle_contract.validation_contract.required_checks"].extend(appended_lc)
    return {k: v for k, v in restored.items() if v}


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_dump_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _task_version_snapshot(task_doc: dict[str, Any]) -> dict[str, Any]:
    agent = task_doc.get("agent_identity") if isinstance(task_doc.get("agent_identity"), dict) else {}
    scaffold = task_doc.get("scaffold_metadata") if isinstance(task_doc.get("scaffold_metadata"), dict) else {}
    return {
        "agent_identity": {
            "methodology_version": str(agent.get("methodology_version", "")).strip(),
            "prompt_version": str(agent.get("prompt_version", "")).strip(),
            "json_version": str(agent.get("json_version", "")).strip(),
        },
        "scaffold_metadata": {
            "protocol_contract_version": str(scaffold.get("protocol_contract_version", "")).strip(),
            "required_version_stream": str(scaffold.get("required_version_stream", "")).strip(),
            "required_gate_bundle_contract_version": str(
                scaffold.get("required_gate_bundle_contract_version", "")
            ).strip(),
            "identity_protocol_version": str(scaffold.get("identity_protocol_version", "")).strip(),
        },
    }


def _catalog_version_snapshot(catalog_row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(catalog_row, dict):
        return {"methodology_version": ""}
    return {"methodology_version": str(catalog_row.get("methodology_version", "")).strip()}


def _meta_version_snapshot(meta_doc: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(meta_doc, dict):
        return {"methodology_version": ""}
    return {"methodology_version": str(meta_doc.get("methodology_version", "")).strip()}


def _sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(131072)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _resolve_pack_runtime_path(pack_path: Path, raw_path: str, fallback: str) -> Path:
    token = str(raw_path or "").strip() or str(fallback)
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = (pack_path / candidate).resolve()
    return candidate


def _collect_host_gateway_wrapper_template_snapshot(task: dict[str, Any], *, pack_path: Path) -> dict[str, dict[str, Any]]:
    contract = task.get(HOST_GATEWAY_CONTRACT_KEY)
    node = contract if isinstance(contract, dict) else {}
    wrapper_specs = {
        "ingress_wrapper_path": HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH,
        "egress_wrapper_path": HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH,
        "session_chain_wrapper_path": HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH,
    }
    payload: dict[str, dict[str, Any]] = {}
    for key, fallback in wrapper_specs.items():
        resolved = _resolve_pack_runtime_path(pack_path, str(node.get(key, "")).strip(), fallback)
        payload[key] = {
            "path": str(resolved),
            "exists": bool(resolved.exists() and resolved.is_file()),
            "sha256": _sha256_file(resolved),
        }
    return payload


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _legacy_path_drift_fields(task: dict[str, Any], identity_id: str) -> list[str]:
    legacy_prefix = f"identity/runtime/local/{identity_id}/reports/"
    out: list[str] = []
    mapping = {
        "dedup_monotonic_winner_contract_v1.claims_path_pattern": ("dedup_monotonic_winner_contract_v1", "claims_path_pattern"),
        "cross_workflow_evidence_schema_contract_v1.evidence_path_pattern": ("cross_workflow_evidence_schema_contract_v1", "evidence_path_pattern"),
        "route_workflow_version_pinning_contract_v1.proof_receipt_path_pattern": ("route_workflow_version_pinning_contract_v1", "proof_receipt_path_pattern"),
    }
    for field_ref, (contract_key, path_key) in mapping.items():
        node = task.get(contract_key)
        if not isinstance(node, dict):
            continue
        value = str(node.get(path_key, "")).strip()
        if value.startswith(legacy_prefix):
            out.append(field_ref)
    return out


def _normalize_prompt_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_PROMPT_KEYS:
        default = PROMPT_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
    return forced_required_keys, restored_validator_keys


def _normalize_multimodal_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    arbitration_link_restored = False
    for key in REQUIRED_MULTIMODAL_KEYS:
        default = MULTIMODAL_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("contract_id", "")).strip():
            node["contract_id"] = str(default.get("contract_id", "")).strip()
        requirements = node.get("provider_binding_requirements")
        if not isinstance(requirements, dict):
            requirements = {}
            node["provider_binding_requirements"] = requirements
        req_profiles = requirements.get("required_profiles")
        if not isinstance(req_profiles, list) or not req_profiles:
            requirements["required_profiles"] = ["glm46v_vision_prod", "openai_vision_prod"]
        else:
            merged_profiles = [str(x).strip() for x in req_profiles if str(x).strip()]
            for profile_id in ("glm46v_vision_prod", "openai_vision_prod"):
                if profile_id not in merged_profiles:
                    merged_profiles.append(profile_id)
            requirements["required_profiles"] = merged_profiles
        min_bindings = requirements.get("minimum_enabled_bindings")
        if not isinstance(min_bindings, int) or min_bindings < 2:
            requirements["minimum_enabled_bindings"] = 2
        if requirements.get("require_all_required_profiles") is not True:
            requirements["require_all_required_profiles"] = True

    arbitration = task.get("capability_arbitration_contract")
    if isinstance(arbitration, dict):
        desired = {
            "contract_ref": "rq_034_multimodal_plugin_enforcement_contract_v1",
            "validator": "scripts/validate_multimodal_plugin_enforcement.py",
            "requires_multimodal_evidence_consistency": True,
            "inconsistent_evidence_transition": "block_done",
        }
        current = arbitration.get("accurate_judgement_enforcement")
        if not isinstance(current, dict):
            arbitration["accurate_judgement_enforcement"] = dict(desired)
            arbitration_link_restored = True
        else:
            for k, v in desired.items():
                if current.get(k) != v:
                    current[k] = v
                    arbitration_link_restored = True
            arbitration["accurate_judgement_enforcement"] = current

    return forced_required_keys, restored_validator_keys, arbitration_link_restored


def _normalize_reasoning_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], bool]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    arbitration_link_restored = False
    for key in REQUIRED_REASONING_KEYS:
        default = REASONING_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("contract_id", "")).strip():
            node["contract_id"] = str(default.get("contract_id", "")).strip()
        _ensure_reasoning_floor(node)

    arbitration = task.get("capability_arbitration_contract")
    if isinstance(arbitration, dict):
        desired = {
            "contract_ref": "rq_035_reasoning_loop_failclose_contract_v1",
            "validator": "scripts/validate_reasoning_loop_failclose.py",
            "no_target_reached_cannot_complete": True,
            "failed_attempt_requires_next_action": True,
            "threshold_requires_escalation": True,
            "reasoning_enforcement_level_field": "reasoning_enforcement_level",
        }
        current = arbitration.get("reasoning_loop_enforcement")
        if not isinstance(current, dict):
            arbitration["reasoning_loop_enforcement"] = dict(desired)
            arbitration_link_restored = True
        else:
            for k, v in desired.items():
                if current.get(k) != v:
                    current[k] = v
                    arbitration_link_restored = True
            arbitration["reasoning_loop_enforcement"] = current

    return forced_required_keys, restored_validator_keys, arbitration_link_restored


def _normalize_unique_entry_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_ENTRY_KEYS:
        default = ENTRY_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("entry_script", "")).strip():
            node["entry_script"] = ENTRY_SCRIPT
        if not str(node.get("bundle_key", "")).strip():
            node["bundle_key"] = ENTRY_BUNDLE_KEY
        if not str(node.get("scope", "")).strip():
            node["scope"] = "all_identity_instance_actions"
        if node.get("require_strict_operation_receipt") is not True:
            node["require_strict_operation_receipt"] = True
        if not str(node.get("entry_receipt_state_file", "")).strip():
            node["entry_receipt_state_file"] = str(default.get("entry_receipt_state_file", "")).strip()
        if not str(node.get("entry_receipt_history_pattern", "")).strip():
            node["entry_receipt_history_pattern"] = str(default.get("entry_receipt_history_pattern", "")).strip()
        default_max_age_seconds = _safe_int(default.get("entry_receipt_max_age_seconds"), default=1800)
        if default_max_age_seconds <= 0:
            default_max_age_seconds = 1800
        if _safe_int(node.get("entry_receipt_max_age_seconds"), default=0) <= 0:
            node["entry_receipt_max_age_seconds"] = default_max_age_seconds
        receipt_fields = node.get("entry_receipt_required_fields")
        default_receipt_fields = [
            str(item).strip()
            for item in (default.get("entry_receipt_required_fields") or [])
            if str(item).strip()
        ]
        if not isinstance(receipt_fields, list):
            node["entry_receipt_required_fields"] = list(default_receipt_fields)
        else:
            merged = [str(item).strip() for item in receipt_fields if str(item).strip()]
            for field in default_receipt_fields:
                if field not in merged:
                    merged.append(field)
            node["entry_receipt_required_fields"] = merged
        if not str(node.get("onboarding_single_entry_command", "")).strip():
            node["onboarding_single_entry_command"] = str(default.get("onboarding_single_entry_command", "")).strip()
        if not str(node.get("extension_attach_entrypoint", "")).strip():
            node["extension_attach_entrypoint"] = str(default.get("extension_attach_entrypoint", "")).strip()
    return forced_required_keys, restored_validator_keys


def _normalize_lane_headstamp_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_LANE_HEADSTAMP_KEYS:
        default = LANE_HEADSTAMP_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("enforcement_validator", "")).strip()
        if not validator:
            node["enforcement_validator"] = str(default.get("enforcement_validator", "")).strip()
            restored_validator_keys.append(key)
        if not str(node.get("required_lane", "")).strip():
            node["required_lane"] = str(default.get("required_lane", "")).strip()
        if node.get("route_non_starvation") is not True:
            node["route_non_starvation"] = True
        if node.get("headstamp_dual_context_required") is not True:
            node["headstamp_dual_context_required"] = True
        required_fields = node.get("required_fields")
        default_required_fields = [
            str(item).strip()
            for item in (default.get("required_fields") or [])
            if str(item).strip()
        ]
        if not isinstance(required_fields, list):
            node["required_fields"] = list(default_required_fields)
        else:
            merged = [str(item).strip() for item in required_fields if str(item).strip()]
            for field in default_required_fields:
                if field not in merged:
                    merged.append(field)
            node["required_fields"] = merged
    return forced_required_keys, restored_validator_keys


def _normalize_host_gateway_contracts(task: dict[str, Any], *, identity_id: str = "") -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    signer_secret_env = _host_gateway_signer_secret_env(identity_id or "default")
    for key in REQUIRED_HOST_GATEWAY_KEYS:
        default = HOST_GATEWAY_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        node["contract_id"] = HOST_GATEWAY_CONTRACT_ID
        if str(node.get("protocol_ingress_script", "")).strip() != UNIQUE_INGRESS_SCRIPT:
            node["protocol_ingress_script"] = UNIQUE_INGRESS_SCRIPT
        if str(node.get("protocol_egress_script", "")).strip() != UNIQUE_EGRESS_SCRIPT:
            node["protocol_egress_script"] = UNIQUE_EGRESS_SCRIPT
        if not str(node.get("ingress_wrapper_path", "")).strip():
            node["ingress_wrapper_path"] = HOST_GATEWAY_RELATIVE_INGRESS_WRAPPER_PATH
        if not str(node.get("egress_wrapper_path", "")).strip():
            node["egress_wrapper_path"] = HOST_GATEWAY_RELATIVE_EGRESS_WRAPPER_PATH
        if not str(node.get("session_chain_wrapper_path", "")).strip():
            node["session_chain_wrapper_path"] = HOST_GATEWAY_RELATIVE_SESSION_CHAIN_WRAPPER_PATH
        if not str(node.get("gateway_contract_path", "")).strip():
            node["gateway_contract_path"] = HOST_GATEWAY_RELATIVE_CONTRACT_PATH
        entry_policy = node.get("entry_receipt_policy")
        if not isinstance(entry_policy, dict):
            entry_policy = {}
        entry_policy["required"] = True
        default_entry_policy = default.get("entry_receipt_policy")
        if isinstance(default_entry_policy, dict):
            required_surface_label = str(default_entry_policy.get("required_surface_label", "")).strip()
            required_wrapper_surface_status = str(
                default_entry_policy.get("required_wrapper_surface_status", "")
            ).strip().upper()
            required_wrapper_dispatch_status = str(
                default_entry_policy.get("required_wrapper_dispatch_token_status", "")
            ).strip().upper()
            if required_surface_label:
                entry_policy["required_surface_label"] = required_surface_label
            if required_wrapper_surface_status:
                entry_policy["required_wrapper_surface_status"] = required_wrapper_surface_status
            if required_wrapper_dispatch_status:
                entry_policy["required_wrapper_dispatch_token_status"] = required_wrapper_dispatch_status
        node["entry_receipt_policy"] = entry_policy
        ingress_proof_policy = node.get("ingress_proof_policy")
        if not isinstance(ingress_proof_policy, dict):
            ingress_proof_policy = {}
        ingress_proof_policy["required"] = True
        ingress_proof_policy["signer_mode"] = "runtime_env_secret"
        ingress_proof_policy["signer_secret_env"] = signer_secret_env
        ingress_proof_policy["signing_key_path"] = str(
            ingress_proof_policy.get("signing_key_path") or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ).strip() or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ingress_proof_policy["bootstrap_env_secret_from_signing_key_path"] = bool(
            ingress_proof_policy.get(
                "bootstrap_env_secret_from_signing_key_path",
                HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
            )
        )
        default_ingress_proof_policy = default.get("ingress_proof_policy")
        if isinstance(default_ingress_proof_policy, dict):
            max_age_seconds = int(default_ingress_proof_policy.get("max_age_seconds", 300) or 300)
            if int(ingress_proof_policy.get("max_age_seconds", 0) or 0) <= 0:
                ingress_proof_policy["max_age_seconds"] = max_age_seconds
        node["ingress_proof_policy"] = ingress_proof_policy
        egress_policy = node.get("egress_receipt_policy")
        if not isinstance(egress_policy, dict):
            egress_policy = {}
        egress_policy["required"] = True
        node["egress_receipt_policy"] = egress_policy
        egress_grant_policy = node.get("egress_grant_policy")
        if not isinstance(egress_grant_policy, dict):
            egress_grant_policy = {}
        egress_grant_policy["required"] = True
        egress_grant_policy["signer_mode"] = "runtime_env_secret"
        egress_grant_policy["signer_secret_env"] = signer_secret_env
        egress_grant_policy["signing_key_path"] = str(
            egress_grant_policy.get("signing_key_path") or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        ).strip() or HOST_GATEWAY_RELATIVE_SIGNING_KEY_PATH
        egress_grant_policy["bootstrap_env_secret_from_signing_key_path"] = bool(
            egress_grant_policy.get(
                "bootstrap_env_secret_from_signing_key_path",
                HOST_GATEWAY_SIGNER_ENV_BOOTSTRAP_FROM_KEY_PATH,
            )
        )
        default_egress_grant_policy = default.get("egress_grant_policy")
        if isinstance(default_egress_grant_policy, dict):
            max_age_seconds = int(default_egress_grant_policy.get("max_age_seconds", 300) or 300)
            if int(egress_grant_policy.get("max_age_seconds", 0) or 0) <= 0:
                egress_grant_policy["max_age_seconds"] = max_age_seconds
        node["egress_grant_policy"] = egress_grant_policy
        headstamp_policy = node.get("headstamp_policy")
        if not isinstance(headstamp_policy, dict):
            headstamp_policy = {}
        headstamp_policy["required"] = True
        node["headstamp_policy"] = headstamp_policy
        tuple_fields = node.get("identity_tuple_fields")
        if not isinstance(tuple_fields, list):
            tuple_fields = []
        merged = [str(item).strip() for item in tuple_fields if str(item).strip()]
        for field in HOST_GATEWAY_REQUIRED_TUPLE_FIELDS:
            if field not in merged:
                merged.append(field)
        node["identity_tuple_fields"] = merged
        if str(node.get("host_dispatch_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_DISPATCH_MODE:
            node["host_dispatch_mode"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
        if str(node.get("host_release_mode", "")).strip().lower() != HOST_GATEWAY_REQUIRED_RELEASE_MODE:
            node["host_release_mode"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE
        if str(node.get("ingress_wrapper_dispatch_token", "")).strip() != HOST_GATEWAY_INGRESS_DISPATCH_TOKEN:
            node["ingress_wrapper_dispatch_token"] = HOST_GATEWAY_INGRESS_DISPATCH_TOKEN
        default_profile_policy = default.get("operation_profile_policy")
        profile_policy = node.get("operation_profile_policy")
        if not isinstance(profile_policy, dict):
            profile_policy = {}
        if isinstance(default_profile_policy, dict):
            for policy_key in (
                "strict_operations",
                "light_operations",
                "strict_gate_profile",
                "light_gate_profile",
                "allow_upgrade_only",
            ):
                if policy_key not in profile_policy or profile_policy.get(policy_key) in (None, "", []):
                    profile_policy[policy_key] = json.loads(json.dumps(default_profile_policy.get(policy_key)))
        node["operation_profile_policy"] = profile_policy
        default_broadcast_policy = default.get("broadcast_policy")
        broadcast_policy = node.get("broadcast_policy")
        if not isinstance(broadcast_policy, dict):
            broadcast_policy = {}
        broadcast_policy["required"] = True
        broadcast_policy["protocol_broadcast_items_dir"] = HOST_GATEWAY_BROADCAST_ITEMS_DIR
        broadcast_policy["protocol_broadcast_index_file"] = HOST_GATEWAY_BROADCAST_INDEX_FILE
        broadcast_policy["protocol_broadcast_schema_file"] = HOST_GATEWAY_BROADCAST_SCHEMA_FILE
        if not str(broadcast_policy.get("instance_state_file", "")).strip():
            state_fallback = (
                str((default_broadcast_policy or {}).get("instance_state_file", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_state_file"] = state_fallback or HOST_GATEWAY_BROADCAST_STATE_FILE
        if not str(broadcast_policy.get("instance_receipt_pattern", "")).strip():
            receipt_fallback = (
                str((default_broadcast_policy or {}).get("instance_receipt_pattern", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_receipt_pattern"] = receipt_fallback or HOST_GATEWAY_BROADCAST_RECEIPT_PATTERN
        if not str(broadcast_policy.get("instance_ack_pattern", "")).strip():
            ack_fallback = (
                str((default_broadcast_policy or {}).get("instance_ack_pattern", "")).strip()
                if isinstance(default_broadcast_policy, dict)
                else ""
            )
            broadcast_policy["instance_ack_pattern"] = ack_fallback or HOST_GATEWAY_BROADCAST_ACK_PATTERN
        broadcast_policy["block_on_critical_unacked"] = bool(
            broadcast_policy.get("block_on_critical_unacked", False)
        )
        node["broadcast_policy"] = broadcast_policy
        node["host_visible_surface_registry_contract_ref"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
        node[HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY] = _host_gateway_wrapper_template_attestation_policy()
    return forced_required_keys, restored_validator_keys


def _normalize_host_visible_surface_contracts(task: dict[str, Any]) -> tuple[list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    for key in REQUIRED_HOST_VISIBLE_SURFACE_KEYS:
        default = HOST_VISIBLE_SURFACE_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        validator = str(node.get("validator", "")).strip()
        if not validator:
            node["validator"] = str(default.get("validator", "")).strip()
            restored_validator_keys.append(key)
        node["contract_id"] = HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
        node["validator"] = HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
        channels = node.get("required_channels")
        if not isinstance(channels, list):
            channels = []
        merged_channels = [str(item).strip() for item in channels if str(item).strip()]
        for channel in HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS:
            if channel not in merged_channels:
                merged_channels.append(channel)
        node["required_channels"] = merged_channels
        if not str(node.get("runtime_state_file", "")).strip():
            node["runtime_state_file"] = str(default.get("runtime_state_file", "")).strip() or HOST_VISIBLE_SURFACE_STATE_FILE
        if not str(node.get("runtime_receipt_pattern", "")).strip():
            node["runtime_receipt_pattern"] = (
                str(default.get("runtime_receipt_pattern", "")).strip() or HOST_VISIBLE_SURFACE_RECEIPT_PATTERN
            )
        if not str(node.get("post_check_closure_state_file", "")).strip():
            node["post_check_closure_state_file"] = (
                str(default.get("post_check_closure_state_file", "")).strip()
                or HOST_VISIBLE_SURFACE_POST_CHECK_CLOSURE_STATE_FILE
            )
        node["post_check_block_on_active"] = bool(
            node.get("post_check_block_on_active", HOST_VISIBLE_SURFACE_POST_CHECK_BLOCK_ON_ACTIVE)
        )
        max_age_raw = node.get("runtime_receipt_max_age_seconds")
        try:
            max_age_seconds = int(max_age_raw)
        except Exception:
            max_age_seconds = 0
        if max_age_seconds <= 0:
            try:
                max_age_seconds = int(default.get("runtime_receipt_max_age_seconds", 0))
            except Exception:
                max_age_seconds = 0
        if max_age_seconds <= 0:
            max_age_seconds = 300
        node["runtime_receipt_max_age_seconds"] = int(max_age_seconds)
        attestation_fields = node.get("required_attestation_fields")
        if not isinstance(attestation_fields, list):
            attestation_fields = []
        merged_attestation_fields = [str(item).strip() for item in attestation_fields if str(item).strip()]
        for field in HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS:
            if field not in merged_attestation_fields:
                merged_attestation_fields.append(field)
        node["required_attestation_fields"] = merged_attestation_fields
        pass_status_fields = node.get("required_pass_status_fields")
        if not isinstance(pass_status_fields, list):
            pass_status_fields = []
        merged_pass_status_fields = [str(item).strip() for item in pass_status_fields if str(item).strip()]
        for field in HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS:
            if field not in merged_pass_status_fields:
                merged_pass_status_fields.append(field)
        node["required_pass_status_fields"] = merged_pass_status_fields
        node["required_live_probe_delegate"] = HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
        node["host_dispatch_mode_required"] = HOST_GATEWAY_REQUIRED_DISPATCH_MODE
        node["host_release_mode_required"] = HOST_GATEWAY_REQUIRED_RELEASE_MODE
        node["strict_live_run_binding_required"] = bool(HOST_VISIBLE_SURFACE_STRICT_LIVE_RUN_BINDING_REQUIRED)
    return forced_required_keys, restored_validator_keys


def _normalize_downsink_path_contracts(task: dict[str, Any]) -> tuple[list[str], list[str], list[str], list[str]]:
    forced_required_keys: list[str] = []
    restored_validator_keys: list[str] = []
    restored_write_guard_validator_keys: list[str] = []
    restored_literal_lock_validator_keys: list[str] = []
    for key in REQUIRED_DOWNSINK_KEYS:
        default = DOWNSINK_CONTRACT_DEFAULTS.get(key, {})
        node = task.get(key)
        if not isinstance(node, dict):
            task[key] = json.loads(json.dumps(default))
            forced_required_keys.append(key)
            restored_validator_keys.append(key)
            restored_write_guard_validator_keys.append(key)
            restored_literal_lock_validator_keys.append(key)
            continue
        if node.get("required") is not True:
            node["required"] = True
            forced_required_keys.append(key)
        node["contract_id"] = DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID
        validator_id = str(node.get("validator_id", "")).strip()
        if validator_id != DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID:
            node["validator_id"] = DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID
            restored_validator_keys.append(key)
        write_guard_validator_id = str(node.get("write_guard_validator_id", "")).strip()
        if write_guard_validator_id != DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID:
            node["write_guard_validator_id"] = DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID
            restored_write_guard_validator_keys.append(key)
        source_literal_lock_policy = node.get("source_literal_lock_policy")
        if not isinstance(source_literal_lock_policy, dict):
            source_literal_lock_policy = {}
        if source_literal_lock_policy.get("required") is not True:
            source_literal_lock_policy["required"] = True
            restored_literal_lock_validator_keys.append(key)
        source_literal_lock_validator_id = str(source_literal_lock_policy.get("validator_id", "")).strip()
        if source_literal_lock_validator_id != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID:
            source_literal_lock_policy["validator_id"] = DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID
            restored_literal_lock_validator_keys.append(key)
        if bool(source_literal_lock_policy.get("enforce_registered_runtime_path_literals_only")) is not True:
            source_literal_lock_policy["enforce_registered_runtime_path_literals_only"] = True
            restored_literal_lock_validator_keys.append(key)
        if (
            str(source_literal_lock_policy.get("allow_inline_override_marker", "")).strip()
            != DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
        ):
            source_literal_lock_policy["allow_inline_override_marker"] = DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
            restored_literal_lock_validator_keys.append(key)
        scan_globs = source_literal_lock_policy.get("scan_globs")
        normalized_scan_globs = [str(item).strip() for item in (scan_globs or []) if str(item).strip()]
        if set(normalized_scan_globs) != set(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS):
            source_literal_lock_policy["scan_globs"] = list(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS)
            restored_literal_lock_validator_keys.append(key)
        node["source_literal_lock_policy"] = source_literal_lock_policy

        anchor_policy = node.get("anchor_policy")
        if not isinstance(anchor_policy, dict):
            anchor_policy = {}
        default_anchor_policy = default.get("anchor_policy")
        if isinstance(default_anchor_policy, dict):
            if not str(anchor_policy.get("protocol_repo_root_ref", "")).strip():
                anchor_policy["protocol_repo_root_ref"] = str(default_anchor_policy.get("protocol_repo_root_ref", "")).strip()
            if not str(anchor_policy.get("identity_pack_root_ref", "")).strip():
                anchor_policy["identity_pack_root_ref"] = str(default_anchor_policy.get("identity_pack_root_ref", "")).strip()
            anchor_policy["allow_parent_escape"] = False
            anchor_policy["allow_symlink_escape"] = False
        node["anchor_policy"] = anchor_policy

        schema_policy = node.get("schema_policy")
        if not isinstance(schema_policy, dict):
            schema_policy = {}
        schema_policy["reject_additional_properties"] = True
        schema_policy["require_all_declared_paths_present_in_runtime_contract"] = True
        node["schema_policy"] = schema_policy

        operation_enforcement = node.get("operation_enforcement")
        if not isinstance(operation_enforcement, dict):
            operation_enforcement = {}
        default_operation_enforcement = default.get("operation_enforcement")
        if isinstance(default_operation_enforcement, dict):
            strict_operations = operation_enforcement.get("strict_operations")
            if not isinstance(strict_operations, list) or not strict_operations:
                operation_enforcement["strict_operations"] = json.loads(
                    json.dumps(default_operation_enforcement.get("strict_operations", []))
                )
            light_operations = operation_enforcement.get("light_operations")
            if not isinstance(light_operations, list) or not light_operations:
                operation_enforcement["light_operations"] = json.loads(
                    json.dumps(default_operation_enforcement.get("light_operations", []))
                )
        operation_enforcement["strict_fail_mode"] = "fail_required"
        operation_enforcement["light_fail_mode"] = "fail_required"
        node["operation_enforcement"] = operation_enforcement

        path_registry = node.get("path_registry")
        if not isinstance(path_registry, dict):
            path_registry = {}
        default_registry = default.get("path_registry")
        if isinstance(default_registry, dict):
            normalized_registry: dict[str, Any] = {}
            for domain, default_domain_node in default_registry.items():
                if not isinstance(default_domain_node, dict):
                    continue
                default_anchor_ref = str(default_domain_node.get("anchor_ref", "")).strip()
                default_entries = json.loads(json.dumps(default_domain_node.get("entries", [])))
                current_domain_node = path_registry.get(domain)
                if not isinstance(current_domain_node, dict):
                    normalized_registry[domain] = {
                        "anchor_ref": default_anchor_ref,
                        "entries": default_entries,
                    }
                    continue
                normalized_registry[domain] = {
                    "anchor_ref": default_anchor_ref,
                    "entries": default_entries,
                }
            path_registry = normalized_registry
        node["path_registry"] = path_registry
    restored_literal_lock_validator_keys = sorted(set(restored_literal_lock_validator_keys))
    return (
        forced_required_keys,
        restored_validator_keys,
        restored_write_guard_validator_keys,
        restored_literal_lock_validator_keys,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Backfill intake contract set into CURRENT_TASK.json.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--apply", action="store_true", help="persist updates to CURRENT_TASK.json")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    if not catalog.exists():
        print(f"[FAIL] catalog not found: {catalog}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog, args.identity_id)
        task_doc = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    repo_root = Path(__file__).resolve().parent.parent
    try:
        version_baseline = load_version_baseline_or_raise(repo_root=repo_root)
    except Exception as exc:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog),
            "pack_path": str(pack_path),
            "task_path": str(task_path),
            "contract_backfill_status": STATUS_FAIL_REQUIRED,
            "error_code": "IP-CBKF-001",
            "changed": False,
            "applied": False,
            "version_baseline_status": STATUS_FAIL_REQUIRED,
            "version_baseline_error": str(exc),
            "stale_reasons": ["version_baseline_unavailable"],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    catalog_doc = _safe_load_yaml(catalog)
    catalog_rows = catalog_doc.get("identities")
    catalog_rows = catalog_rows if isinstance(catalog_rows, list) else []
    catalog_row = next(
        (
            row
            for row in catalog_rows
            if isinstance(row, dict) and str(row.get("id", "")).strip() == str(args.identity_id or "").strip()
        ),
        None,
    )
    catalog_row_before = json.loads(json.dumps(catalog_row)) if isinstance(catalog_row, dict) else {}
    catalog_row_version_changed = False
    if isinstance(catalog_row, dict):
        catalog_row_version_changed = apply_version_baseline_to_catalog_row(catalog_row, version_baseline)

    meta_path = (pack_path / "META.yaml").resolve()
    meta_doc = _safe_load_yaml(meta_path)
    meta_before = json.loads(json.dumps(meta_doc)) if isinstance(meta_doc, dict) else {}

    before = json.loads(json.dumps(task_doc))
    missing_before = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(task_doc.get(k), dict)]
    prompt_missing_before = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(task_doc.get(k), dict)]
    multimodal_missing_before = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(task_doc.get(k), dict)]
    reasoning_missing_before = [k for k in REQUIRED_REASONING_KEYS if not isinstance(task_doc.get(k), dict)]
    entry_missing_before = [k for k in REQUIRED_ENTRY_KEYS if not isinstance(task_doc.get(k), dict)]
    lane_headstamp_missing_before = [k for k in REQUIRED_LANE_HEADSTAMP_KEYS if not isinstance(task_doc.get(k), dict)]
    host_gateway_missing_before = [k for k in REQUIRED_HOST_GATEWAY_KEYS if not isinstance(task_doc.get(k), dict)]
    host_visible_surface_missing_before = [
        k for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS if not isinstance(task_doc.get(k), dict)
    ]
    downsink_missing_before = [k for k in REQUIRED_DOWNSINK_KEYS if not isinstance(task_doc.get(k), dict)]
    skill_supply_chain_missing_before = [
        k for k in SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys() if not isinstance(task_doc.get(k), dict)
    ]
    legacy_drift_before = _legacy_path_drift_fields(task_doc, args.identity_id)

    updated = _ensure_intake_p1_contracts(task_doc, args.identity_id)
    restored_skill_supply_chain_contract_keys = _normalize_skill_supply_chain_contracts(updated, args.identity_id)
    restored_capability_driver_validator_paths = _normalize_capability_driver_validators(updated)
    skill_contract = updated.get("skill_path_integrity_contract_v1")
    if isinstance(skill_contract, dict):
        _merge_required_skills(skill_contract, FILE_GOVERNANCE_SKILL_ID)
    forced_required_keys, restored_validator_keys = _normalize_prompt_contracts(updated)
    forced_mm_required_keys, restored_mm_validator_keys, arbitration_link_restored = _normalize_multimodal_contracts(updated)
    forced_rl_required_keys, restored_rl_validator_keys, reasoning_arbitration_link_restored = _normalize_reasoning_contracts(updated)
    forced_entry_required_keys, restored_entry_validator_keys = _normalize_unique_entry_contracts(updated)
    (
        forced_lane_headstamp_required_keys,
        restored_lane_headstamp_validator_keys,
    ) = _normalize_lane_headstamp_contracts(updated)
    forced_host_gateway_required_keys, restored_host_gateway_validator_keys = _normalize_host_gateway_contracts(
        updated,
        identity_id=str(args.identity_id or "").strip(),
    )
    (
        forced_host_visible_surface_required_keys,
        restored_host_visible_surface_validator_keys,
    ) = _normalize_host_visible_surface_contracts(updated)
    (
        forced_downsink_required_keys,
        restored_downsink_validator_keys,
        restored_downsink_write_guard_validator_keys,
        restored_downsink_literal_lock_validator_keys,
    ) = (
        _normalize_downsink_path_contracts(updated)
    )
    task_version_changed = apply_version_baseline_to_task_doc(updated, version_baseline)
    meta_version_changed = False
    if isinstance(meta_doc, dict):
        meta_version_changed = apply_version_baseline_to_meta_doc(meta_doc, version_baseline)
    missing_after = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(updated.get(k), dict)]
    prompt_missing_after = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(updated.get(k), dict)]
    multimodal_missing_after = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(updated.get(k), dict)]
    reasoning_missing_after = [k for k in REQUIRED_REASONING_KEYS if not isinstance(updated.get(k), dict)]
    entry_missing_after = [k for k in REQUIRED_ENTRY_KEYS if not isinstance(updated.get(k), dict)]
    lane_headstamp_missing_after = [k for k in REQUIRED_LANE_HEADSTAMP_KEYS if not isinstance(updated.get(k), dict)]
    host_gateway_missing_after = [k for k in REQUIRED_HOST_GATEWAY_KEYS if not isinstance(updated.get(k), dict)]
    host_visible_surface_missing_after = [
        k for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS if not isinstance(updated.get(k), dict)
    ]
    downsink_missing_after = [k for k in REQUIRED_DOWNSINK_KEYS if not isinstance(updated.get(k), dict)]
    skill_supply_chain_missing_after = [
        k for k in SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys() if not isinstance(updated.get(k), dict)
    ]
    prompt_invalid_after = [
        k
        for k in REQUIRED_PROMPT_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
        )
    ]
    multimodal_invalid_after = [
        k
        for k in REQUIRED_MULTIMODAL_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or not str((updated.get(k) or {}).get("contract_id", "")).strip()
        )
    ]
    reasoning_invalid_after = [
        k
        for k in REQUIRED_REASONING_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or not str((updated.get(k) or {}).get("contract_id", "")).strip()
        )
    ]
    entry_invalid_after = [
        k
        for k in REQUIRED_ENTRY_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or str((updated.get(k) or {}).get("entry_script", "")).strip() != ENTRY_SCRIPT
            or str((updated.get(k) or {}).get("bundle_key", "")).strip() != ENTRY_BUNDLE_KEY
            or updated.get(k, {}).get("require_strict_operation_receipt") is not True
            or not str((updated.get(k) or {}).get("entry_receipt_state_file", "")).strip()
            or not str((updated.get(k) or {}).get("entry_receipt_history_pattern", "")).strip()
            or _safe_int((updated.get(k) or {}).get("entry_receipt_max_age_seconds"), default=0) <= 0
            or not isinstance((updated.get(k) or {}).get("entry_receipt_required_fields"), list)
            or not list((updated.get(k) or {}).get("entry_receipt_required_fields") or [])
        )
    ]
    lane_headstamp_invalid_after = [
        k
        for k in REQUIRED_LANE_HEADSTAMP_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("enforcement_validator", "")).strip()
            != "scripts/validate_protocol_lane_headstamp_continuity.py"
            or str((updated.get(k) or {}).get("required_lane", "")).strip().lower() != "protocol"
            or (updated.get(k) or {}).get("route_non_starvation") is not True
            or (updated.get(k) or {}).get("headstamp_dual_context_required") is not True
            or not isinstance((updated.get(k) or {}).get("required_fields"), list)
            or not set(
                [
                    "requested_lane",
                    "previous_lane",
                    "resolved_lane",
                    "lane_activation_status",
                    "lane_activation_error_code",
                    "route_source_ref",
                    "lane_activation_evidence_ref",
                    "headstamp_continuity_status",
                    "headstamp_error_code",
                ]
            ).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_fields") or [])
                    if str(item).strip()
                }
            )
        )
    ]
    host_gateway_invalid_after = [
        k
        for k in REQUIRED_HOST_GATEWAY_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip() != HOST_GATEWAY_CONTRACT_ID
            or not str((updated.get(k) or {}).get("validator", "")).strip()
            or str((updated.get(k) or {}).get("protocol_ingress_script", "")).strip() != UNIQUE_INGRESS_SCRIPT
            or str((updated.get(k) or {}).get("protocol_egress_script", "")).strip() != UNIQUE_EGRESS_SCRIPT
            or not str((updated.get(k) or {}).get("ingress_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("egress_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("session_chain_wrapper_path", "")).strip()
            or not str((updated.get(k) or {}).get("gateway_contract_path", "")).strip()
            or not isinstance((updated.get(k) or {}).get("entry_receipt_policy"), dict)
            or bool(((updated.get(k) or {}).get("entry_receipt_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("ingress_proof_policy"), dict)
            or bool(((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("required")) is not True
            or int((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("max_age_seconds") or 0)) <= 0
            or (
                (
                    str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                    == "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_secret_env") or "")
                    ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not str(
                            (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signing_key_path") or "")
                        ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not isinstance(
                            (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get(
                                "bootstrap_env_secret_from_signing_key_path"
                            )),
                            bool,
                        )
                    )
                    or (
                        str((((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signer_mode") or "")).strip()
                        != "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("ingress_proof_policy") or {}).get("signing_key_path") or "")
                    ).strip()
                )
            )
            or not isinstance((updated.get(k) or {}).get("egress_receipt_policy"), dict)
            or bool(((updated.get(k) or {}).get("egress_receipt_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("egress_grant_policy"), dict)
            or bool(((updated.get(k) or {}).get("egress_grant_policy") or {}).get("required")) is not True
            or int((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("max_age_seconds") or 0)) <= 0
            or (
                (
                    str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                    == "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_secret_env") or "")
                    ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not str(
                            (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signing_key_path") or "")
                        ).strip()
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        == "runtime_env_secret"
                        and not isinstance(
                            (((updated.get(k) or {}).get("egress_grant_policy") or {}).get(
                                "bootstrap_env_secret_from_signing_key_path"
                            )),
                            bool,
                        )
                    )
                    or (
                        str((((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signer_mode") or "")).strip()
                        != "runtime_env_secret"
                    and not str(
                        (((updated.get(k) or {}).get("egress_grant_policy") or {}).get("signing_key_path") or "")
                    ).strip()
                )
            )
            or not isinstance((updated.get(k) or {}).get("headstamp_policy"), dict)
            or bool(((updated.get(k) or {}).get("headstamp_policy") or {}).get("required")) is not True
            or not isinstance((updated.get(k) or {}).get("identity_tuple_fields"), list)
            or not set(HOST_GATEWAY_REQUIRED_TUPLE_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("identity_tuple_fields") or [])
                    if str(item).strip()
                }
            )
            or not isinstance((updated.get(k) or {}).get("broadcast_policy"), dict)
            or bool(((updated.get(k) or {}).get("broadcast_policy") or {}).get("required")) is not True
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_items_dir") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_ITEMS_DIR
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_index_file") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_INDEX_FILE
            or str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("protocol_broadcast_schema_file") or "")
            ).strip()
            != HOST_GATEWAY_BROADCAST_SCHEMA_FILE
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_state_file") or "")
            ).strip()
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_receipt_pattern") or "")
            ).strip()
            or not str(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("instance_ack_pattern") or "")
            ).strip()
            or not isinstance(
                (((updated.get(k) or {}).get("broadcast_policy") or {}).get("block_on_critical_unacked")),
                bool,
            )
            or str(((updated.get(k) or {}).get("host_visible_surface_registry_contract_ref") or "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_KEY
            or not isinstance((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY), dict)
            or bool(
                (((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get("required")
            )
            is not True
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "ingress_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "egress_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not str(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "session_chain_wrapper_template_sha256"
                ) or "")
            ).strip()
            or not isinstance(
                ((((updated.get(k) or {}).get(HOST_GATEWAY_WRAPPER_TEMPLATE_ATTESTATION_KEY)) or {}).get(
                    "session_chain_required_semantic_tokens"
                )),
                list,
            )
        )
    ]
    host_visible_surface_invalid_after = [
        k
        for k in REQUIRED_HOST_VISIBLE_SURFACE_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_CONTRACT_ID
            or str((updated.get(k) or {}).get("validator", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_VALIDATOR
            or not isinstance((updated.get(k) or {}).get("required_channels"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_CHANNELS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_channels") or [])
                    if str(item).strip()
                }
            )
            or not str((updated.get(k) or {}).get("runtime_state_file", "")).strip()
            or not str((updated.get(k) or {}).get("runtime_receipt_pattern", "")).strip()
            or not str((updated.get(k) or {}).get("post_check_closure_state_file", "")).strip()
            or not bool((updated.get(k) or {}).get("post_check_block_on_active", False))
            or _safe_int((updated.get(k) or {}).get("runtime_receipt_max_age_seconds", 0), default=0) <= 0
            or not isinstance((updated.get(k) or {}).get("required_attestation_fields"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_ATTESTATION_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_attestation_fields") or [])
                    if str(item).strip()
                }
            )
            or not isinstance((updated.get(k) or {}).get("required_pass_status_fields"), list)
            or not set(HOST_VISIBLE_SURFACE_REQUIRED_PASS_STATUS_FIELDS).issubset(
                {
                    str(item).strip()
                    for item in ((updated.get(k) or {}).get("required_pass_status_fields") or [])
                    if str(item).strip()
                }
            )
            or str((updated.get(k) or {}).get("required_live_probe_delegate", "")).strip()
            != HOST_VISIBLE_SURFACE_REGISTRY_LIVE_PROBE_DELEGATE
            or str((updated.get(k) or {}).get("host_dispatch_mode_required", "")).strip().lower()
            != HOST_GATEWAY_REQUIRED_DISPATCH_MODE
            or str((updated.get(k) or {}).get("host_release_mode_required", "")).strip().lower()
            != HOST_GATEWAY_REQUIRED_RELEASE_MODE
            or (updated.get(k) or {}).get("strict_live_run_binding_required") is not True
        )
    ]
    downsink_invalid_after = [
        k
        for k in REQUIRED_DOWNSINK_KEYS
        if isinstance(updated.get(k), dict)
        and (
            updated.get(k, {}).get("required") is not True
            or str((updated.get(k) or {}).get("contract_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID
            or str((updated.get(k) or {}).get("validator_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID
            or str((updated.get(k) or {}).get("write_guard_validator_id", "")).strip()
            != DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID
            or not isinstance((updated.get(k) or {}).get("source_literal_lock_policy"), dict)
            or bool((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("required")) is not True
            or str(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("validator_id") or "")
            ).strip()
            != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID
            or bool(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get(
                    "enforce_registered_runtime_path_literals_only"
                ))
            )
            is not True
            or str(
                ((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get(
                    "allow_inline_override_marker"
                ) or "")
            ).strip()
            != DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
            or not isinstance((((updated.get(k) or {}).get("source_literal_lock_policy")) or {}).get("scan_globs"), list)
            or not isinstance((updated.get(k) or {}).get("anchor_policy"), dict)
            or not isinstance((updated.get(k) or {}).get("schema_policy"), dict)
            or not isinstance((updated.get(k) or {}).get("operation_enforcement"), dict)
            or not isinstance((updated.get(k) or {}).get("path_registry"), dict)
            or not set(DOWNSINK_REQUIRED_DOMAINS).issubset(
                {
                    str(domain).strip()
                    for domain in (((updated.get(k) or {}).get("path_registry")) or {}).keys()
                    if str(domain).strip()
                }
            )
        )
    ]
    legacy_drift_after = _legacy_path_drift_fields(updated, args.identity_id)

    host_gateway_wrapper_snapshot_before = _collect_host_gateway_wrapper_template_snapshot(
        updated,
        pack_path=pack_path,
    )
    gateway_artifacts = {}
    host_gateway_artifact_materialization_invoked = False
    if (
        args.apply
        and not host_gateway_missing_after
        and not host_gateway_invalid_after
        and not host_visible_surface_missing_after
        and not host_visible_surface_invalid_after
    ):
        host_gateway_artifact_materialization_invoked = True
        gateway_artifacts = materialize_protocol_host_gateway_artifacts(
            task=updated,
            identity_id=args.identity_id,
            pack_dir=pack_path,
            catalog_path=catalog,
            protocol_root=repo_root,
        )
    host_gateway_wrapper_snapshot_after = _collect_host_gateway_wrapper_template_snapshot(
        updated,
        pack_path=pack_path,
    )
    host_gateway_wrapper_artifact_changed_paths: list[str] = []
    for wrapper_key, before_snapshot in host_gateway_wrapper_snapshot_before.items():
        after_snapshot = host_gateway_wrapper_snapshot_after.get(wrapper_key) or {}
        before_sha = str(before_snapshot.get("sha256", "")).strip()
        after_sha = str(after_snapshot.get("sha256", "")).strip()
        before_exists = bool(before_snapshot.get("exists"))
        after_exists = bool(after_snapshot.get("exists"))
        if before_sha != after_sha or before_exists != after_exists:
            host_gateway_wrapper_artifact_changed_paths.append(wrapper_key)
    host_gateway_wrapper_artifacts_refreshed = bool(host_gateway_wrapper_artifact_changed_paths)

    task_changed = before != updated
    catalog_changed = catalog_row_version_changed
    meta_changed = meta_version_changed
    changed = task_changed or catalog_changed or meta_changed
    applied = False
    if args.apply:
        if task_changed:
            task_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            applied = True
        if catalog_changed:
            _safe_dump_yaml(catalog, catalog_doc)
            applied = True
        if meta_changed:
            _safe_dump_yaml(meta_path, meta_doc)
            applied = True
        if host_gateway_wrapper_artifacts_refreshed:
            applied = True

    if missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-001"
        stale_reasons = ["required_contract_keys_missing_after_backfill"]
    elif prompt_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROMPT_WIRE_MISSING
        stale_reasons = ["required_prompt_contract_keys_missing_after_backfill"]
    elif prompt_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROMPT_WIRE_INVALID
        stale_reasons = ["required_prompt_contract_invalid_after_backfill"]
    elif multimodal_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_MM_WIRE_MISSING
        stale_reasons = ["required_multimodal_contract_keys_missing_after_backfill"]
    elif multimodal_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_MM_WIRE_INVALID
        stale_reasons = ["required_multimodal_contract_invalid_after_backfill"]
    elif reasoning_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_RL_WIRE_MISSING
        stale_reasons = ["required_reasoning_contract_keys_missing_after_backfill"]
    elif reasoning_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_RL_WIRE_INVALID
        stale_reasons = ["required_reasoning_contract_invalid_after_backfill"]
    elif entry_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_WIRE_MISSING
        stale_reasons = ["required_unique_entry_contract_keys_missing_after_backfill"]
    elif entry_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_ENTRY_WIRE_INVALID
        stale_reasons = ["required_unique_entry_contract_invalid_after_backfill"]
    elif lane_headstamp_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LANE_HEADSTAMP_WIRE_MISSING
        stale_reasons = ["required_lane_headstamp_contract_keys_missing_after_backfill"]
    elif lane_headstamp_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_LANE_HEADSTAMP_WIRE_INVALID
        stale_reasons = ["required_lane_headstamp_contract_invalid_after_backfill"]
    elif host_gateway_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_HOST_GATEWAY_WIRE_MISSING
        stale_reasons = ["required_host_gateway_contract_keys_missing_after_backfill"]
    elif host_gateway_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_HOST_GATEWAY_WIRE_INVALID
        stale_reasons = ["required_host_gateway_contract_invalid_after_backfill"]
    elif host_visible_surface_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_VISIBLE_SURFACE_WIRE_MISSING
        stale_reasons = ["required_host_visible_surface_contract_keys_missing_after_backfill"]
    elif host_visible_surface_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_VISIBLE_SURFACE_WIRE_INVALID
        stale_reasons = ["required_host_visible_surface_contract_invalid_after_backfill"]
    elif downsink_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_DOWNSINK_WIRE_MISSING
        stale_reasons = ["required_downsink_contract_keys_missing_after_backfill"]
    elif downsink_invalid_after:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_DOWNSINK_WIRE_INVALID
        stale_reasons = ["required_downsink_contract_invalid_after_backfill"]
    elif skill_supply_chain_missing_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-SSUP-001"
        stale_reasons = ["required_skill_supply_chain_contract_keys_missing_after_backfill"]
    elif legacy_drift_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-002"
        stale_reasons = ["legacy_contract_path_drift_after_backfill"]
    elif changed or host_gateway_wrapper_artifacts_refreshed:
        status = STATUS_PASS_REQUIRED if applied else STATUS_SKIPPED_NOT_REQUIRED
        error_code = ""
        stale_reasons = [] if applied else ["dry_run_only"]
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""
        stale_reasons = ["already_backfilled"] if not applied else []

    version_baseline_info = {
        "entry_file": str(version_baseline.get("entry_path", "")),
        "resolved_file": str(version_baseline.get("resolved_path", "")),
        "stream_version": str(version_baseline.get("stream_version", "")),
    }
    task_versions_before = _task_version_snapshot(before)
    task_versions_after = _task_version_snapshot(updated)
    catalog_versions_before = _catalog_version_snapshot(catalog_row_before)
    catalog_versions_after = _catalog_version_snapshot(catalog_row if isinstance(catalog_row, dict) else {})
    meta_versions_before = _meta_version_snapshot(meta_before)
    meta_versions_after = _meta_version_snapshot(meta_doc if isinstance(meta_doc, dict) else {})

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(pack_path),
        "task_path": str(task_path),
        "contract_backfill_status": status,
        "error_code": error_code,
        "changed": changed,
        "task_changed": task_changed,
        "catalog_changed": catalog_changed,
        "meta_changed": meta_changed,
        "version_baseline_status": STATUS_PASS_REQUIRED,
        "version_baseline": version_baseline_info,
        "task_version_changed": task_version_changed,
        "catalog_row_version_changed": catalog_row_version_changed,
        "meta_version_changed": meta_version_changed,
        "task_versions_before": task_versions_before,
        "task_versions_after": task_versions_after,
        "catalog_versions_before": catalog_versions_before,
        "catalog_versions_after": catalog_versions_after,
        "meta_versions_before": meta_versions_before,
        "meta_versions_after": meta_versions_after,
        "meta_path": str(meta_path),
        "host_gateway_wrapper_artifacts_refreshed": host_gateway_wrapper_artifacts_refreshed,
        "host_gateway_wrapper_artifact_changed_paths": host_gateway_wrapper_artifact_changed_paths,
        "host_gateway_wrapper_snapshot_before": host_gateway_wrapper_snapshot_before,
        "host_gateway_wrapper_snapshot_after": host_gateway_wrapper_snapshot_after,
        "host_gateway_artifact_materialization_invoked": host_gateway_artifact_materialization_invoked,
        "applied": applied,
        "missing_contract_keys_before": missing_before,
        "missing_contract_keys_after": missing_after,
        "required_prompt_contract_keys": list(REQUIRED_PROMPT_KEYS),
        "missing_prompt_contract_keys_before": prompt_missing_before,
        "missing_prompt_contract_keys_after": prompt_missing_after,
        "invalid_prompt_contract_keys_after": prompt_invalid_after,
        "forced_prompt_required_keys": forced_required_keys,
        "restored_prompt_validator_keys": restored_validator_keys,
        "required_multimodal_contract_keys": list(REQUIRED_MULTIMODAL_KEYS),
        "missing_multimodal_contract_keys_before": multimodal_missing_before,
        "missing_multimodal_contract_keys_after": multimodal_missing_after,
        "invalid_multimodal_contract_keys_after": multimodal_invalid_after,
        "forced_multimodal_required_keys": forced_mm_required_keys,
        "restored_multimodal_validator_keys": restored_mm_validator_keys,
        "multimodal_arbitration_link_restored": arbitration_link_restored,
        "required_reasoning_contract_keys": list(REQUIRED_REASONING_KEYS),
        "missing_reasoning_contract_keys_before": reasoning_missing_before,
        "missing_reasoning_contract_keys_after": reasoning_missing_after,
        "invalid_reasoning_contract_keys_after": reasoning_invalid_after,
        "forced_reasoning_required_keys": forced_rl_required_keys,
        "restored_reasoning_validator_keys": restored_rl_validator_keys,
        "reasoning_arbitration_link_restored": reasoning_arbitration_link_restored,
        "required_unique_entry_contract_keys": list(REQUIRED_ENTRY_KEYS),
        "missing_unique_entry_contract_keys_before": entry_missing_before,
        "missing_unique_entry_contract_keys_after": entry_missing_after,
        "invalid_unique_entry_contract_keys_after": entry_invalid_after,
        "forced_unique_entry_required_keys": forced_entry_required_keys,
        "restored_unique_entry_validator_keys": restored_entry_validator_keys,
        "required_lane_headstamp_contract_keys": list(REQUIRED_LANE_HEADSTAMP_KEYS),
        "missing_lane_headstamp_contract_keys_before": lane_headstamp_missing_before,
        "missing_lane_headstamp_contract_keys_after": lane_headstamp_missing_after,
        "invalid_lane_headstamp_contract_keys_after": lane_headstamp_invalid_after,
        "forced_lane_headstamp_required_keys": forced_lane_headstamp_required_keys,
        "restored_lane_headstamp_validator_keys": restored_lane_headstamp_validator_keys,
        "required_host_gateway_contract_keys": list(REQUIRED_HOST_GATEWAY_KEYS),
        "missing_host_gateway_contract_keys_before": host_gateway_missing_before,
        "missing_host_gateway_contract_keys_after": host_gateway_missing_after,
        "invalid_host_gateway_contract_keys_after": host_gateway_invalid_after,
        "forced_host_gateway_required_keys": forced_host_gateway_required_keys,
        "restored_host_gateway_validator_keys": restored_host_gateway_validator_keys,
        "required_host_visible_surface_contract_keys": list(REQUIRED_HOST_VISIBLE_SURFACE_KEYS),
        "missing_host_visible_surface_contract_keys_before": host_visible_surface_missing_before,
        "missing_host_visible_surface_contract_keys_after": host_visible_surface_missing_after,
        "invalid_host_visible_surface_contract_keys_after": host_visible_surface_invalid_after,
        "forced_host_visible_surface_required_keys": forced_host_visible_surface_required_keys,
        "restored_host_visible_surface_validator_keys": restored_host_visible_surface_validator_keys,
        "required_downsink_contract_keys": list(REQUIRED_DOWNSINK_KEYS),
        "missing_downsink_contract_keys_before": downsink_missing_before,
        "missing_downsink_contract_keys_after": downsink_missing_after,
        "invalid_downsink_contract_keys_after": downsink_invalid_after,
        "forced_downsink_required_keys": forced_downsink_required_keys,
        "restored_downsink_validator_keys": restored_downsink_validator_keys,
        "restored_downsink_write_guard_validator_keys": restored_downsink_write_guard_validator_keys,
        "restored_downsink_literal_lock_validator_keys": restored_downsink_literal_lock_validator_keys,
        "required_skill_supply_chain_contract_keys": list(SKILL_SUPPLY_CHAIN_CONTRACT_DEFAULTS.keys()),
        "missing_skill_supply_chain_contract_keys_before": skill_supply_chain_missing_before,
        "missing_skill_supply_chain_contract_keys_after": skill_supply_chain_missing_after,
        "restored_skill_supply_chain_contract_keys": restored_skill_supply_chain_contract_keys,
        "restored_capability_driver_validator_paths": restored_capability_driver_validator_paths,
        "host_gateway_artifacts": gateway_artifacts,
        "unique_entry_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not entry_missing_after and not entry_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "unique_entry_contract_auto_wire_error_code": (
            ""
            if not entry_missing_after and not entry_invalid_after
            else (ERR_ENTRY_WIRE_MISSING if entry_missing_after else ERR_ENTRY_WIRE_INVALID)
        ),
        "lane_headstamp_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED
            if not lane_headstamp_missing_after and not lane_headstamp_invalid_after
            else STATUS_FAIL_REQUIRED
        ),
        "lane_headstamp_contract_auto_wire_error_code": (
            ""
            if not lane_headstamp_missing_after and not lane_headstamp_invalid_after
            else (
                ERR_LANE_HEADSTAMP_WIRE_MISSING
                if lane_headstamp_missing_after
                else ERR_LANE_HEADSTAMP_WIRE_INVALID
            )
        ),
        "host_gateway_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not host_gateway_missing_after and not host_gateway_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "host_gateway_contract_auto_wire_error_code": (
            ""
            if not host_gateway_missing_after and not host_gateway_invalid_after
            else (
                ERR_HOST_GATEWAY_WIRE_MISSING
                if host_gateway_missing_after
                else ERR_HOST_GATEWAY_WIRE_INVALID
            )
        ),
        "host_visible_surface_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED
            if not host_visible_surface_missing_after and not host_visible_surface_invalid_after
            else STATUS_FAIL_REQUIRED
        ),
        "host_visible_surface_contract_auto_wire_error_code": (
            ""
            if not host_visible_surface_missing_after and not host_visible_surface_invalid_after
            else (
                ERR_VISIBLE_SURFACE_WIRE_MISSING
                if host_visible_surface_missing_after
                else ERR_VISIBLE_SURFACE_WIRE_INVALID
            )
        ),
        "downsink_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not downsink_missing_after and not downsink_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "downsink_contract_auto_wire_error_code": (
            ""
            if not downsink_missing_after and not downsink_invalid_after
            else (ERR_DOWNSINK_WIRE_MISSING if downsink_missing_after else ERR_DOWNSINK_WIRE_INVALID)
        ),
        "prompt_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not prompt_missing_after and not prompt_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "prompt_contract_auto_wire_error_code": (
            ""
            if not prompt_missing_after and not prompt_invalid_after
            else (ERR_PROMPT_WIRE_MISSING if prompt_missing_after else ERR_PROMPT_WIRE_INVALID)
        ),
        "multimodal_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not multimodal_missing_after and not multimodal_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "multimodal_contract_auto_wire_error_code": (
            ""
            if not multimodal_missing_after and not multimodal_invalid_after
            else (ERR_MM_WIRE_MISSING if multimodal_missing_after else ERR_MM_WIRE_INVALID)
        ),
        "reasoning_contract_auto_wire_status": (
            STATUS_PASS_REQUIRED if not reasoning_missing_after and not reasoning_invalid_after else STATUS_FAIL_REQUIRED
        ),
        "reasoning_contract_auto_wire_error_code": (
            ""
            if not reasoning_missing_after and not reasoning_invalid_after
            else (ERR_RL_WIRE_MISSING if reasoning_missing_after else ERR_RL_WIRE_INVALID)
        ),
        "legacy_path_drift_fields_before": legacy_drift_before,
        "legacy_path_drift_fields_after": legacy_drift_after,
        "required_contract_keys": (
            list(REQUIRED_INTAKE_KEYS)
            + list(REQUIRED_MULTIMODAL_KEYS)
            + list(REQUIRED_REASONING_KEYS)
            + list(REQUIRED_ENTRY_KEYS)
            + list(REQUIRED_LANE_HEADSTAMP_KEYS)
            + list(REQUIRED_HOST_GATEWAY_KEYS)
            + list(REQUIRED_HOST_VISIBLE_SURFACE_KEYS)
            + list(REQUIRED_DOWNSINK_KEYS)
        ),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(task_path),
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
