#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

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

EXPECTED_ENTRY_SCRIPT = "scripts/required_gate_bundle_runner.py"
EXPECTED_EGRESS_SCRIPT = "scripts/final_emit_governed.py"
EXPECTED_HOST_DISPATCH_MODE = "wrapper_only"
EXPECTED_HOST_RELEASE_MODE = "wrapper_only"
DEFAULT_ENTRY_RECEIPT_SURFACE_LABEL = "host_ingress_wrapper"
DEFAULT_ENTRY_RECEIPT_WRAPPER_SURFACE_STATUS = STATUS_PASS_REQUIRED
DEFAULT_ENTRY_RECEIPT_WRAPPER_DISPATCH_STATUS = STATUS_PASS_REQUIRED
EXPECTED_BUNDLE_KEY = "required_gate_bundle_runner"
EXPECTED_SCOPE = "all_identity_instance_actions"
EXPECTED_ENTRY_ERROR_FAMILY = {"IP-GATE-ENTRY-001", "IP-GATE-ENTRY-002"}
ENTRY_RECEIPT_STATE_FILE = "required_gate_bundle_entry.latest.json"
ENTRY_RECEIPT_HISTORY_GLOB = "required-gate-bundle-entry-*.json"
HOST_GATEWAY_REQUIRED_TUPLE_FIELDS = {"actor_id", "session_id", "run_id", "work_layer", "source_layer"}
HOST_GATEWAY_EXPECTED_INGRESS_REL = "runtime/gate/protocol_ingress_wrapper.py"
HOST_GATEWAY_EXPECTED_EGRESS_REL = "runtime/gate/protocol_egress_wrapper.py"
HOST_GATEWAY_EXPECTED_CONTRACT_REL = "runtime/gate/protocol_gateway_contract.json"
HOST_GATEWAY_ALLOWED_FIELDS = {
    "contract_id",
    "required",
    "validator",
    "protocol_ingress_script",
    "protocol_egress_script",
    "ingress_wrapper_path",
    "egress_wrapper_path",
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
}
HOST_GATEWAY_EGRESS_POLICY_ALLOWED_FIELDS = {"required"}
HOST_GATEWAY_EGRESS_GRANT_POLICY_ALLOWED_FIELDS = {
    "required",
    "max_age_seconds",
}
HOST_GATEWAY_HEADSTAMP_POLICY_ALLOWED_FIELDS = {"required"}
RUNTIME_GATEWAY_ALLOWED_FIELDS = {
    "schema_version",
    "identity_id",
    "protocol_repo_root",
    "protocol_ingress_script",
    "protocol_egress_script",
    "ingress_wrapper_path",
    "egress_wrapper_path",
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
}

CONTRACT_KEYS = (
    "protocol_unique_entry_gate_contract_v1",
    "protocol_unique_entry_gate_contract",
    "rq_036_protocol_unique_entry_gate_contract_v1",
)

HOST_GATEWAY_CONTRACT_KEYS = (
    "protocol_host_unique_channel_contract_v1",
    "protocol_gateway_wrapper_contract_v1",
    "protocol_gateway_contract_v1",
)


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


def _resolve_entry_receipt_path(*, pack_path: Path, explicit_path: str, operation: str) -> Path | None:
    if str(explicit_path or "").strip():
        p = Path(explicit_path).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    operation_token = str(operation or "").strip().lower()
    if operation_token:
        by_operation = (pack_path / "runtime" / "state" / f"required_gate_bundle_entry.{operation_token}.json").resolve()
        if by_operation.exists() and by_operation.is_file():
            return by_operation

    latest = (pack_path / "runtime" / "state" / ENTRY_RECEIPT_STATE_FILE).resolve()
    if latest.exists() and latest.is_file():
        return latest

    history_dir = (pack_path / "runtime" / "reports" / "required-gate-bundle-entry").resolve()
    if not history_dir.exists() or not history_dir.is_dir():
        return None
    candidates = sorted(history_dir.glob(ENTRY_RECEIPT_HISTORY_GLOB), key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0].resolve() if candidates else None


def _load_receipt(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("receipt_payload_not_object")
    return data


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
        "protocol_unique_entry_receipt_state_file": "",
        "protocol_unique_entry_receipt_history_pattern": "",
        "protocol_unique_entry_receipt_required_fields": [],
        "protocol_unique_entry_receipt_status": STATUS_SKIPPED_NOT_REQUIRED,
        "protocol_unique_entry_receipt_path": "",
        "protocol_unique_entry_receipt_bundle_key": "",
        "protocol_unique_entry_receipt_run_id": "",
        "protocol_unique_entry_receipt_actor_id": "",
        "protocol_unique_entry_receipt_session_id": "",
        "protocol_unique_entry_receipt_operation": "",
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
        "error_code": "",
        "stale_reasons": [],
    }

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
    entry_receipt_required_fields = _as_str_set(contract.get("entry_receipt_required_fields"))

    payload["protocol_unique_entry_script"] = entry_script
    payload["protocol_unique_entry_bundle_key"] = bundle_key
    payload["protocol_unique_entry_scope"] = scope
    payload["protocol_unique_entry_required_operations"] = sorted(required_ops)
    payload["protocol_unique_entry_error_family"] = sorted(error_family)
    payload["protocol_unique_entry_receipt_required"] = bool(args.require_entry_receipt)
    payload["protocol_unique_entry_receipt_state_file"] = entry_receipt_state_file
    payload["protocol_unique_entry_receipt_history_pattern"] = entry_receipt_history_pattern
    payload["protocol_unique_entry_receipt_required_fields"] = sorted(entry_receipt_required_fields)

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
    if not entry_receipt_required_fields:
        issues.append("entry_receipt_required_fields_missing")

    if issues:
        payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = issues
        _emit(payload, json_only=args.json_only)
        return 1

    host_gateway_contract, host_gateway_contract_key = _resolve_host_gateway_contract(task)
    payload["protocol_host_gateway_contract_key"] = host_gateway_contract_key
    receipt_required_surface_label = DEFAULT_ENTRY_RECEIPT_SURFACE_LABEL
    receipt_required_wrapper_surface_status = DEFAULT_ENTRY_RECEIPT_WRAPPER_SURFACE_STATUS
    receipt_required_wrapper_dispatch_status = DEFAULT_ENTRY_RECEIPT_WRAPPER_DISPATCH_STATUS
    host_gateway_dispatch_mode = ""
    host_gateway_strict_operations: set[str] = set()
    host_gateway_light_operations: set[str] = set()
    host_gateway_allow_upgrade_only = True
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
        gateway_contract_raw = str(host_gateway_contract.get("gateway_contract_path", "")).strip()
        dispatch_mode = str(host_gateway_contract.get("host_dispatch_mode", "")).strip().lower()
        release_mode = str(host_gateway_contract.get("host_release_mode", "")).strip().lower()
        host_gateway_dispatch_mode = dispatch_mode
        ingress_dispatch_token = str(host_gateway_contract.get("ingress_wrapper_dispatch_token", "")).strip()
        tuple_fields = _as_str_set(host_gateway_contract.get("identity_tuple_fields"))
        operation_profile_policy = host_gateway_contract.get("operation_profile_policy")
        payload["protocol_host_gateway_ingress_script"] = ingress_script
        payload["protocol_host_gateway_egress_script"] = egress_script
        payload["protocol_host_gateway_dispatch_mode"] = dispatch_mode
        payload["protocol_host_gateway_release_mode"] = release_mode
        payload["protocol_host_gateway_ingress_dispatch_token"] = ingress_dispatch_token
        payload["protocol_host_gateway_identity_tuple_fields"] = sorted(tuple_fields)

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
        gateway_contract_path = _resolve_pack_relative_path(
            pack_path,
            gateway_contract_raw,
            HOST_GATEWAY_EXPECTED_CONTRACT_REL,
        )
        payload["protocol_host_gateway_ingress_wrapper_path"] = str(ingress_wrapper_path)
        payload["protocol_host_gateway_egress_wrapper_path"] = str(egress_wrapper_path)
        payload["protocol_host_gateway_contract_path"] = str(gateway_contract_path)

        if host_gateway_contract.get("required") is not True:
            host_gateway_issues.append("host_gateway_required_flag_not_true")
        if str(host_gateway_contract.get("validator", "")).strip() != "scripts/validate_protocol_unique_entry_gate.py":
            host_gateway_issues.append("host_gateway_validator_mismatch")
        if ingress_script != EXPECTED_ENTRY_SCRIPT:
            host_gateway_issues.append("host_gateway_ingress_script_mismatch")
        if egress_script != EXPECTED_EGRESS_SCRIPT:
            host_gateway_issues.append("host_gateway_egress_script_mismatch")
        if dispatch_mode != EXPECTED_HOST_DISPATCH_MODE:
            host_gateway_issues.append("host_gateway_dispatch_mode_not_wrapper_only")
        if release_mode != EXPECTED_HOST_RELEASE_MODE:
            host_gateway_issues.append("host_gateway_release_mode_not_wrapper_only")
        if not ingress_dispatch_token:
            host_gateway_issues.append("host_gateway_ingress_dispatch_token_missing")
        if not HOST_GATEWAY_REQUIRED_TUPLE_FIELDS.issubset(tuple_fields):
            host_gateway_issues.append("host_gateway_tuple_fields_missing")
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

        missing_runtime_files: list[str] = []
        if not ingress_wrapper_path.exists():
            missing_runtime_files.append("ingress_wrapper_missing")
        if not egress_wrapper_path.exists():
            missing_runtime_files.append("egress_wrapper_missing")
        if not gateway_contract_path.exists():
            missing_runtime_files.append("gateway_contract_missing")
        if missing_runtime_files:
            host_gateway_issues.extend([f"host_gateway_runtime:{item}" for item in missing_runtime_files])
            payload["protocol_host_gateway_runtime_files_status"] = STATUS_FAIL_REQUIRED
        else:
            payload["protocol_host_gateway_runtime_files_status"] = STATUS_PASS_REQUIRED
            ingress_text = ingress_wrapper_path.read_text(encoding="utf-8", errors="ignore")
            egress_text = egress_wrapper_path.read_text(encoding="utf-8", errors="ignore")
            if EXPECTED_ENTRY_SCRIPT not in ingress_text:
                host_gateway_issues.append("host_gateway_ingress_wrapper_not_bound_to_canonical_script")
            if EXPECTED_EGRESS_SCRIPT not in egress_text:
                host_gateway_issues.append("host_gateway_egress_wrapper_not_bound_to_canonical_script")
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
                if not missing_runtime_fields and not host_gateway_issues:
                    payload["protocol_host_gateway_runtime_contract_status"] = STATUS_PASS_REQUIRED
                elif payload["protocol_host_gateway_runtime_contract_status"] != STATUS_FAIL_REQUIRED:
                    payload["protocol_host_gateway_runtime_contract_status"] = STATUS_FAIL_REQUIRED

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

    receipt_required = bool(args.require_entry_receipt)
    if receipt_required:
        receipt_path = _resolve_entry_receipt_path(
            pack_path=pack_path,
            explicit_path=str(args.entry_receipt or ""),
            operation=str(args.operation),
        )
        if receipt_path is None:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = ["entry_receipt_missing"]
            _emit(payload, json_only=args.json_only)
            return 1
        payload["protocol_unique_entry_receipt_path"] = str(receipt_path)
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
        receipt_operation = str(receipt.get("operation", "")).strip().lower()
        receipt_run_id = str(receipt.get("run_id_binding", "")).strip()
        receipt_actor_id = str(receipt.get("actor_id", "")).strip()
        receipt_session_id = str(receipt.get("session_id", "")).strip()
        receipt_bundle_status = str(receipt.get("bundle_status", "")).strip().upper()
        receipt_surface_label = str(receipt.get("surface_label", "")).strip()
        receipt_wrapper_surface_status = str(receipt.get("wrapper_surface_status", "")).strip().upper()
        receipt_wrapper_dispatch_status = str(receipt.get("wrapper_dispatch_token_status", "")).strip().upper()
        receipt_wrapper_dispatch_required = _as_bool(receipt.get("wrapper_dispatch_required"))
        receipt_wrapper_proof_required = _as_bool(receipt.get("wrapper_dispatch_proof_required"))
        receipt_wrapper_proof_status = str(receipt.get("wrapper_dispatch_proof_status", "")).strip().upper()
        payload["protocol_unique_entry_receipt_bundle_key"] = receipt_bundle_key
        payload["protocol_unique_entry_receipt_run_id"] = receipt_run_id
        payload["protocol_unique_entry_receipt_actor_id"] = receipt_actor_id
        payload["protocol_unique_entry_receipt_session_id"] = receipt_session_id
        payload["protocol_unique_entry_receipt_operation"] = receipt_operation
        payload["protocol_unique_entry_receipt_surface_label"] = receipt_surface_label
        payload["protocol_unique_entry_receipt_wrapper_surface_status"] = receipt_wrapper_surface_status
        payload["protocol_unique_entry_receipt_wrapper_dispatch_token_status"] = receipt_wrapper_dispatch_status
        payload["protocol_unique_entry_receipt_wrapper_dispatch_required"] = receipt_wrapper_dispatch_required
        payload["protocol_unique_entry_receipt_wrapper_proof_status"] = receipt_wrapper_proof_status
        payload["protocol_unique_entry_receipt_wrapper_proof_required"] = receipt_wrapper_proof_required

        receipt_issues: list[str] = []
        if receipt_bundle_key != EXPECTED_BUNDLE_KEY:
            receipt_issues.append("entry_receipt_bundle_key_mismatch")
        if receipt_identity_id != str(args.identity_id).strip():
            receipt_issues.append("entry_receipt_identity_mismatch")
        if receipt_operation != str(args.operation).strip().lower():
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
        missing_fields = sorted(
            field for field in entry_receipt_required_fields if field not in receipt
        )
        if missing_fields:
            receipt_issues.append("entry_receipt_required_fields_missing:" + ",".join(missing_fields))

        if receipt_issues:
            payload["protocol_unique_entry_gate_status"] = STATUS_FAIL_REQUIRED
            payload["protocol_unique_entry_receipt_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_CONTRACT_INVALID
            payload["stale_reasons"] = receipt_issues
            _emit(payload, json_only=args.json_only)
            return 1

        payload["protocol_unique_entry_receipt_status"] = STATUS_PASS_REQUIRED

    payload["protocol_unique_entry_gate_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
