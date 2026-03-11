#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from create_identity_pack import (
    _derived_prompt_conformance_contract_skeleton,
    _ensure_intake_p1_contracts,
    _multimodal_plugin_enforcement_contract_skeleton,
    _prompt_bootstrap_capability_contract_skeleton,
    _prompt_capability_matrix_contract_skeleton,
    _prompt_kernel_executable_coupling_contract_skeleton,
    _reasoning_loop_failclose_contract_skeleton,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

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

ERR_PROMPT_WIRE_MISSING = "IP-PROMPT-WIRE-002"
ERR_PROMPT_WIRE_INVALID = "IP-PROMPT-WIRE-003"
ERR_MM_WIRE_MISSING = "IP-MM-WIRE-001"
ERR_MM_WIRE_INVALID = "IP-MM-WIRE-002"
ERR_RL_WIRE_MISSING = "IP-RL-WIRE-001"
ERR_RL_WIRE_INVALID = "IP-RL-WIRE-002"
REASONING_LEVEL_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
REASONING_MIN_LEVEL = "L3"
FILE_GOVERNANCE_SKILL_ID = "ai-folder-governance"


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

    before = json.loads(json.dumps(task_doc))
    missing_before = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(task_doc.get(k), dict)]
    prompt_missing_before = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(task_doc.get(k), dict)]
    multimodal_missing_before = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(task_doc.get(k), dict)]
    reasoning_missing_before = [k for k in REQUIRED_REASONING_KEYS if not isinstance(task_doc.get(k), dict)]
    legacy_drift_before = _legacy_path_drift_fields(task_doc, args.identity_id)

    updated = _ensure_intake_p1_contracts(task_doc, args.identity_id)
    skill_contract = updated.get("skill_path_integrity_contract_v1")
    if isinstance(skill_contract, dict):
        _merge_required_skills(skill_contract, FILE_GOVERNANCE_SKILL_ID)
    forced_required_keys, restored_validator_keys = _normalize_prompt_contracts(updated)
    forced_mm_required_keys, restored_mm_validator_keys, arbitration_link_restored = _normalize_multimodal_contracts(updated)
    forced_rl_required_keys, restored_rl_validator_keys, reasoning_arbitration_link_restored = _normalize_reasoning_contracts(updated)
    missing_after = [k for k in REQUIRED_INTAKE_KEYS if not isinstance(updated.get(k), dict)]
    prompt_missing_after = [k for k in REQUIRED_PROMPT_KEYS if not isinstance(updated.get(k), dict)]
    multimodal_missing_after = [k for k in REQUIRED_MULTIMODAL_KEYS if not isinstance(updated.get(k), dict)]
    reasoning_missing_after = [k for k in REQUIRED_REASONING_KEYS if not isinstance(updated.get(k), dict)]
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
    legacy_drift_after = _legacy_path_drift_fields(updated, args.identity_id)

    changed = before != updated
    applied = False
    if changed and args.apply:
        task_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
    elif legacy_drift_after:
        status = STATUS_FAIL_REQUIRED
        error_code = "IP-CBKF-002"
        stale_reasons = ["legacy_contract_path_drift_after_backfill"]
    elif changed:
        status = STATUS_PASS_REQUIRED if applied else STATUS_SKIPPED_NOT_REQUIRED
        error_code = ""
        stale_reasons = [] if applied else ["dry_run_only"]
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""
        stale_reasons = ["already_backfilled"] if not applied else []

    payload = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog),
        "pack_path": str(pack_path),
        "task_path": str(task_path),
        "contract_backfill_status": status,
        "error_code": error_code,
        "changed": changed,
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
        "required_contract_keys": list(REQUIRED_INTAKE_KEYS) + list(REQUIRED_MULTIMODAL_KEYS) + list(REQUIRED_REASONING_KEYS),
        "stale_reasons": stale_reasons,
        "evidence_ref": str(task_path),
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
