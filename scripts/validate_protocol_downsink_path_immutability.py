#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from create_identity_pack import (
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID,
    DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
    DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID,
    DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID,
    DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER,
    DOWNSINK_LITERAL_LOCK_SCAN_GLOBS,
    DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID,
    DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN,
    DOWNSINK_REQUIRED_DOMAINS,
    DOWNSINK_RUNTIME_BROADCAST_DOMAIN,
    DOWNSINK_RUNTIME_GATE_DOMAIN,
    DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN,
    HOST_GATEWAY_CONTRACT_KEY,
    HOST_GATEWAY_LIGHT_OPERATIONS,
    HOST_GATEWAY_RELATIVE_CONTRACT_PATH,
    HOST_GATEWAY_STRICT_OPERATIONS,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CONTRACT_MISSING = "IP-DSPATH-001"
ERR_CONTRACT_INVALID = "IP-DSPATH-002"
ERR_RUNTIME_PARITY = "IP-DSPATH-003"

ALLOWED_CONTRACT_FIELDS = {
    "required",
    "contract_id",
    "validator_id",
    "write_guard_validator_id",
    "source_literal_lock_policy",
    "path_registry",
    "anchor_policy",
    "schema_policy",
    "operation_enforcement",
}
ALLOWED_SOURCE_LITERAL_LOCK_POLICY_FIELDS = {
    "required",
    "validator_id",
    "enforce_registered_runtime_path_literals_only",
    "allow_inline_override_marker",
    "scan_globs",
}
ALLOWED_ANCHOR_POLICY_FIELDS = {
    "protocol_repo_root_ref",
    "identity_pack_root_ref",
    "allow_parent_escape",
    "allow_symlink_escape",
}
ALLOWED_SCHEMA_POLICY_FIELDS = {
    "reject_additional_properties",
    "require_all_declared_paths_present_in_runtime_contract",
}
ALLOWED_OPERATION_ENFORCEMENT_FIELDS = {
    "strict_operations",
    "light_operations",
    "strict_fail_mode",
    "light_fail_mode",
}
ALLOWED_DOMAIN_FIELDS = {"anchor_ref", "entries"}
ALLOWED_ENTRY_FIELDS = {"path_id", "entry_type", "path"}
ENTRY_TYPES = {"file", "dir", "glob"}
GLOB_MAGIC_RE = re.compile(r"[*?\[]")

EXPECTED_DOMAIN_ANCHOR = {
    DOWNSINK_RUNTIME_GATE_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_RUNTIME_BROADCAST_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_RUNTIME_PROTOCOL_FEEDBACK_DOMAIN: "identity_pack_root_ref",
    DOWNSINK_PROTOCOL_BROADCAST_SOURCE_DOMAIN: "protocol_repo_root_ref",
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _resolve_contract(task: dict[str, Any]) -> tuple[dict[str, Any], str]:
    for key in (
        DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY,
        "protocol_downsink_path_immutability_contract",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node, key
    for key, value in task.items():
        if not isinstance(value, dict):
            continue
        token = str(key or "").strip().lower()
        if "downsink" in token and "path" in token and "immutability" in token:
            return value, str(key)
    return {}, DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY


def _unknown_keys(node: Any, allowed: set[str]) -> list[str]:
    if not isinstance(node, dict):
        return []
    return sorted(str(k) for k in node.keys() if str(k) not in allowed)


def _contains_parent_escape(path_token: str) -> bool:
    token = str(path_token or "").replace("\\", "/").strip()
    if not token:
        return False
    return any(part == ".." for part in PurePosixPath(token).parts)


def _is_abs_like(path_token: str) -> bool:
    token = str(path_token or "").strip()
    if not token:
        return False
    if Path(token).is_absolute():
        return True
    return token.startswith("~/") or re.match(r"^[A-Za-z]:[\\/]", token) is not None


def _resolve_anchor_root(*, anchor_ref: str, pack_path: Path, repo_root: Path) -> Path | None:
    if anchor_ref == "identity_pack_root_ref":
        return pack_path.resolve()
    if anchor_ref == "protocol_repo_root_ref":
        return repo_root.resolve()
    return None


def _path_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _resolve_entry_candidate(anchor_root: Path, entry_path: str, entry_type: str) -> Path:
    normalized = str(entry_path or "").replace("\\", "/").strip()
    if entry_type == "glob":
        # Use the stable prefix before wildcard characters for containment checks.
        split_idx = len(normalized)
        for marker in ("*", "?", "["):
            idx = normalized.find(marker)
            if idx >= 0:
                split_idx = min(split_idx, idx)
        normalized = normalized[:split_idx].rstrip("/")
    normalized = normalized or "."
    return (anchor_root / normalized).resolve()


def _resolve_gateway_contract_path(task: dict[str, Any], pack_path: Path) -> Path:
    gateway_contract = task.get(HOST_GATEWAY_CONTRACT_KEY)
    gateway_path_raw = ""
    if isinstance(gateway_contract, dict):
        gateway_path_raw = str(gateway_contract.get("gateway_contract_path", "")).strip()
    value = gateway_path_raw or HOST_GATEWAY_RELATIVE_CONTRACT_PATH
    candidate = Path(value).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    if value.startswith("identity/runtime/"):
        value = value[len("identity/runtime/") :]
        return (pack_path / "runtime" / value).resolve()
    return (pack_path / value).resolve()


def _normalize_registry_path(path_token: str) -> str:
    return str(path_token or "").replace("\\", "/").strip()


def _registry_entry_index(path_registry: dict[str, Any]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for domain, raw_domain_node in path_registry.items():
        domain_node = raw_domain_node if isinstance(raw_domain_node, dict) else {}
        entries = domain_node.get("entries")
        if not isinstance(entries, list):
            continue
        indexed: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            path_id = str(entry.get("path_id", "")).strip()
            path_token = _normalize_registry_path(entry.get("path"))
            if path_id and path_token:
                indexed[path_id] = path_token
        out[str(domain)] = indexed
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol downsink path immutability contract (v1.6.8).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
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
        return 1

    contract, contract_key = _resolve_contract(task)
    required = contract_required(contract)
    op = str(args.operation or "").strip().lower()
    auto_required_signal = op in set(HOST_GATEWAY_STRICT_OPERATIONS) or op in set(HOST_GATEWAY_LIGHT_OPERATIONS)
    if auto_required_signal:
        required = True
    if args.force_required:
        required = True

    repo_root = Path(__file__).resolve().parent.parent
    runtime_contract_path = _resolve_gateway_contract_path(task, pack_path)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": op,
        "required_contract": required,
        "auto_required_signal": bool(auto_required_signal),
        "contract_key": contract_key,
        "runtime_mirror_contract_path": str(runtime_contract_path),
        "required_domains": list(DOWNSINK_REQUIRED_DOMAINS),
        "protocol_downsink_path_immutability_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": str(task_path),
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not isinstance(contract, dict) or not contract:
        payload["protocol_downsink_path_immutability_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CONTRACT_MISSING
        payload["stale_reasons"] = ["contract_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    issues: list[str] = []
    strict_schema = bool(((contract.get("schema_policy") or {}).get("reject_additional_properties")) is True)

    if str(contract.get("contract_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_CONTRACT_ID:
        issues.append("contract_id_mismatch")
    if str(contract.get("validator_id", "")).strip() != DOWNSINK_PATH_IMMUTABILITY_VALIDATOR_ID:
        issues.append("validator_id_mismatch")
    if str(contract.get("write_guard_validator_id", "")).strip() != DOWNSINK_PATH_WRITE_GUARD_VALIDATOR_ID:
        issues.append("write_guard_validator_id_mismatch")

    source_literal_lock_policy = contract.get("source_literal_lock_policy")
    if not isinstance(source_literal_lock_policy, dict):
        issues.append("source_literal_lock_policy_missing")
        source_literal_lock_policy = {}
    else:
        if strict_schema:
            unknown_source_lock_fields = _unknown_keys(
                source_literal_lock_policy,
                ALLOWED_SOURCE_LITERAL_LOCK_POLICY_FIELDS,
            )
            if unknown_source_lock_fields:
                issues.append(f"unknown_source_literal_lock_policy_fields:{','.join(unknown_source_lock_fields)}")
        if source_literal_lock_policy.get("required") is not True:
            issues.append("source_literal_lock_policy_required_not_true")
        if str(source_literal_lock_policy.get("validator_id", "")).strip() != DOWNSINK_PATH_LITERAL_LOCK_VALIDATOR_ID:
            issues.append("source_literal_lock_policy_validator_id_mismatch")
        if bool(source_literal_lock_policy.get("enforce_registered_runtime_path_literals_only")) is not True:
            issues.append("source_literal_lock_policy_enforce_registered_literals_not_true")
        if (
            str(source_literal_lock_policy.get("allow_inline_override_marker", "")).strip()
            != DOWNSINK_LITERAL_LOCK_ALLOW_INLINE_MARKER
        ):
            issues.append("source_literal_lock_policy_allow_marker_mismatch")
        scan_globs = source_literal_lock_policy.get("scan_globs")
        if not isinstance(scan_globs, list) or not scan_globs:
            issues.append("source_literal_lock_policy_scan_globs_missing")
        elif set(str(item).strip() for item in scan_globs if str(item).strip()) != set(DOWNSINK_LITERAL_LOCK_SCAN_GLOBS):
            issues.append("source_literal_lock_policy_scan_globs_mismatch")

    if strict_schema:
        unknown_contract_fields = _unknown_keys(contract, ALLOWED_CONTRACT_FIELDS)
        if unknown_contract_fields:
            issues.append(f"unknown_contract_fields:{','.join(unknown_contract_fields)}")

    anchor_policy = contract.get("anchor_policy")
    if not isinstance(anchor_policy, dict):
        issues.append("anchor_policy_missing")
        anchor_policy = {}
    else:
        if strict_schema:
            unknown_anchor_fields = _unknown_keys(anchor_policy, ALLOWED_ANCHOR_POLICY_FIELDS)
            if unknown_anchor_fields:
                issues.append(f"unknown_anchor_policy_fields:{','.join(unknown_anchor_fields)}")
        if str(anchor_policy.get("protocol_repo_root_ref", "")).strip() != "{protocol_repo_root}":
            issues.append("anchor_policy_protocol_repo_root_ref_mismatch")
        if str(anchor_policy.get("identity_pack_root_ref", "")).strip() != "{identity_pack_root}":
            issues.append("anchor_policy_identity_pack_root_ref_mismatch")
        if bool(anchor_policy.get("allow_parent_escape")):
            issues.append("anchor_policy_parent_escape_must_be_false")
        if bool(anchor_policy.get("allow_symlink_escape")):
            issues.append("anchor_policy_symlink_escape_must_be_false")

    schema_policy = contract.get("schema_policy")
    require_runtime_parity = False
    if not isinstance(schema_policy, dict):
        issues.append("schema_policy_missing")
        schema_policy = {}
    else:
        if strict_schema:
            unknown_schema_fields = _unknown_keys(schema_policy, ALLOWED_SCHEMA_POLICY_FIELDS)
            if unknown_schema_fields:
                issues.append(f"unknown_schema_policy_fields:{','.join(unknown_schema_fields)}")
        if bool(schema_policy.get("reject_additional_properties")) is not True:
            issues.append("schema_policy_reject_additional_properties_not_true")
        require_runtime_parity = bool(schema_policy.get("require_all_declared_paths_present_in_runtime_contract"))
        if require_runtime_parity is not True:
            issues.append("schema_policy_runtime_parity_not_true")

    operation_enforcement = contract.get("operation_enforcement")
    if not isinstance(operation_enforcement, dict):
        issues.append("operation_enforcement_missing")
    else:
        if strict_schema:
            unknown_operation_fields = _unknown_keys(operation_enforcement, ALLOWED_OPERATION_ENFORCEMENT_FIELDS)
            if unknown_operation_fields:
                issues.append(f"unknown_operation_enforcement_fields:{','.join(unknown_operation_fields)}")
        strict_ops = operation_enforcement.get("strict_operations")
        if not isinstance(strict_ops, list) or not strict_ops:
            issues.append("operation_enforcement_strict_operations_missing")
        light_ops = operation_enforcement.get("light_operations")
        if not isinstance(light_ops, list) or not light_ops:
            issues.append("operation_enforcement_light_operations_missing")
        if str(operation_enforcement.get("strict_fail_mode", "")).strip().lower() != "fail_required":
            issues.append("operation_enforcement_strict_fail_mode_not_fail_required")
        if str(operation_enforcement.get("light_fail_mode", "")).strip().lower() != "fail_required":
            issues.append("operation_enforcement_light_fail_mode_not_fail_required")

    path_registry = contract.get("path_registry")
    if not isinstance(path_registry, dict):
        issues.append("path_registry_missing")
        path_registry = {}
    missing_domains = [domain for domain in DOWNSINK_REQUIRED_DOMAINS if not isinstance(path_registry.get(domain), dict)]
    if missing_domains:
        issues.append(f"path_registry_required_domains_missing:{','.join(missing_domains)}")

    registry_path_id_seen: set[str] = set()
    for domain in DOWNSINK_REQUIRED_DOMAINS:
        domain_node = path_registry.get(domain)
        if not isinstance(domain_node, dict):
            continue
        if strict_schema:
            unknown_domain_fields = _unknown_keys(domain_node, ALLOWED_DOMAIN_FIELDS)
            if unknown_domain_fields:
                issues.append(f"{domain}:unknown_domain_fields:{','.join(unknown_domain_fields)}")
        expected_anchor_ref = EXPECTED_DOMAIN_ANCHOR.get(domain, "")
        anchor_ref = str(domain_node.get("anchor_ref", "")).strip()
        if not anchor_ref:
            issues.append(f"{domain}:anchor_ref_missing")
            continue
        if expected_anchor_ref and anchor_ref != expected_anchor_ref:
            issues.append(f"{domain}:anchor_ref_mismatch")

        anchor_root = _resolve_anchor_root(anchor_ref=anchor_ref, pack_path=pack_path, repo_root=repo_root)
        if anchor_root is None:
            issues.append(f"{domain}:anchor_ref_unsupported")
            continue

        entries = domain_node.get("entries")
        if not isinstance(entries, list) or not entries:
            issues.append(f"{domain}:entries_missing")
            continue

        for idx, raw_entry in enumerate(entries):
            if not isinstance(raw_entry, dict):
                issues.append(f"{domain}:entry_{idx}_invalid")
                continue
            if strict_schema:
                unknown_entry_fields = _unknown_keys(raw_entry, ALLOWED_ENTRY_FIELDS)
                if unknown_entry_fields:
                    issues.append(f"{domain}:entry_{idx}:unknown_fields:{','.join(unknown_entry_fields)}")
            path_id = str(raw_entry.get("path_id", "")).strip()
            entry_type = str(raw_entry.get("entry_type", "")).strip().lower()
            path_token = _normalize_registry_path(raw_entry.get("path"))
            if not path_id:
                issues.append(f"{domain}:entry_{idx}:path_id_missing")
                continue
            if path_id in registry_path_id_seen:
                issues.append(f"{domain}:entry_{idx}:path_id_duplicated")
            registry_path_id_seen.add(path_id)
            if entry_type not in ENTRY_TYPES:
                issues.append(f"{domain}:entry_{idx}:entry_type_invalid")
            if not path_token:
                issues.append(f"{domain}:entry_{idx}:path_missing")
                continue
            if _is_abs_like(path_token):
                issues.append(f"{domain}:entry_{idx}:path_must_be_relative")
                continue
            if _contains_parent_escape(path_token):
                issues.append(f"{domain}:entry_{idx}:path_parent_escape_forbidden")
                continue
            if entry_type in {"file", "dir"} and GLOB_MAGIC_RE.search(path_token):
                issues.append(f"{domain}:entry_{idx}:glob_not_allowed_for_entry_type")
                continue

            candidate = _resolve_entry_candidate(anchor_root, path_token, entry_type)
            if not _path_within(candidate, anchor_root):
                issues.append(f"{domain}:entry_{idx}:anchor_containment_violation")

    runtime_contract = {}
    runtime_downsink_contract = {}
    if runtime_contract_path.exists():
        try:
            runtime_contract = load_json(runtime_contract_path)
        except Exception:
            issues.append("runtime_contract_parse_failed")
    else:
        issues.append("runtime_contract_missing")

    if runtime_contract:
        runtime_downsink_contract = runtime_contract.get(DOWNSINK_PATH_IMMUTABILITY_CONTRACT_KEY)
        if not isinstance(runtime_downsink_contract, dict):
            issues.append("runtime_downsink_contract_missing")
            runtime_downsink_contract = {}

    if runtime_downsink_contract:
        if require_runtime_parity:
            for field in (
                "source_literal_lock_policy",
                "path_registry",
                "anchor_policy",
                "schema_policy",
                "operation_enforcement",
            ):
                declared = contract.get(field)
                mirrored = runtime_downsink_contract.get(field)
                if json.dumps(declared, ensure_ascii=False, sort_keys=True) != json.dumps(
                    mirrored,
                    ensure_ascii=False,
                    sort_keys=True,
                ):
                    issues.append(f"runtime_parity_mismatch:{field}")
        declared_index = _registry_entry_index(path_registry if isinstance(path_registry, dict) else {})
        runtime_index = _registry_entry_index(runtime_downsink_contract.get("path_registry", {}))
        for domain, path_map in declared_index.items():
            runtime_path_map = runtime_index.get(domain, {})
            for path_id, path_token in path_map.items():
                mirrored_token = str(runtime_path_map.get(path_id, "")).strip()
                if not mirrored_token:
                    issues.append(f"runtime_registry_path_id_missing:{domain}:{path_id}")
                    continue
                if mirrored_token != path_token:
                    issues.append(f"runtime_registry_path_mismatch:{domain}:{path_id}")

    if issues:
        payload["protocol_downsink_path_immutability_status"] = STATUS_FAIL_REQUIRED
        if any(reason.startswith("runtime_") for reason in issues) or "runtime_contract_missing" in issues:
            payload["error_code"] = ERR_RUNTIME_PARITY
        else:
            payload["error_code"] = ERR_CONTRACT_INVALID
        payload["stale_reasons"] = issues
        payload["evidence_ref"] = str(runtime_contract_path if runtime_contract_path.exists() else task_path)
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_downsink_path_immutability_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    payload["evidence_ref"] = str(runtime_contract_path if runtime_contract_path.exists() else task_path)
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
