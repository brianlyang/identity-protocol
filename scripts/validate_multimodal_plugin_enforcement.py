#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import (
    contract_required,
    latest_identity_upgrade_report,
    load_json,
    resolve_pack_and_task,
)

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_REGISTRY = "IP-MM-REG-001"
ERR_NAME = "IP-MM-NAME-001"
ERR_NAME_FILE = "IP-MM-NAME-002"
ERR_THRESHOLD = "IP-MM-THR-001"
ERR_PATH = "IP-MM-PATH-001"
ERR_COPY = "IP-MM-COPY-001"
ERR_CONF_PROFILE = "IP-MM-CONF-001"
ERR_CONF_FIELDS = "IP-MM-CONF-002"
ERR_CONF_CREDENTIAL = "IP-MM-CONF-003"
ERR_CONF_ENDPOINT = "IP-MM-CONF-004"
ERR_CONF_CAPABILITY = "IP-MM-CONF-005"
ERR_RUNTIME_REPORT_MISSING = "IP-MM-RUN-001"
ERR_RUNTIME_STAGE_MISSING = "IP-MM-RUN-002"
ERR_RUNTIME_GATE_SKIPPED = "IP-MM-RUN-003"
ERR_RUNTIME_REQUIRED_UNRESOLVED = "IP-MM-RUN-004"
ERR_RUNTIME_PROVIDER_ERROR = "IP-MM-RUN-005"
ERR_RUNTIME_EVIDENCE_MISSING = "IP-MM-RUN-006"
ERR_RUNTIME_RUN_MISMATCH = "IP-MM-RUN-007"

STRICT_OPERATIONS = {
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
}
RUNTIME_PROOF_REQUIRED_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "three-plane",
    "mutation",
}

PLUGIN_ID_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
PROFILE_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{2,63}$")
ENV_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
CREDENTIAL_REF_RE = re.compile(r"^(env|vault):[A-Za-z0-9_.:/-]+$")


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json root must be object: {path}")
    return data


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "multimodal_plugin_enforcement_contract_v1",
        "multimodal_plugin_enforcement_contract",
        "rq_034_multimodal_plugin_enforcement_contract_v1",
    ):
        value = task.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _flatten_bindings(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        rows = data.get("bindings")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _pick_first_nonempty(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = data.get(key)
        if value in (None, "", [], {}):
            continue
        return value
    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except Exception:
        return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _resolve_runtime_report(
    *,
    pack_path: Path,
    identity_id: str,
    report_selected_path: str,
) -> Path | None:
    raw = str(report_selected_path or "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        return p if p.exists() and p.is_file() else None
    return latest_identity_upgrade_report(identity_id, pack_path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate multimodal plugin enforcement contract (RQ-034).")
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
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report-selected-path", default="")
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

    repo_root = Path(__file__).resolve().parents[1]
    plugin_root = (repo_root / "identity" / "protocol" / "plugins").resolve()
    registry_path = (plugin_root / "PLUGIN_REGISTRY.v1.6.2.yaml").resolve()
    registry_schema_path = (plugin_root / "schemas" / "plugin-registry.schema.json").resolve()
    provider_profiles_path = (plugin_root / "PROVIDER_PROFILES.v1.6.2.yaml").resolve()
    provider_schema_path = (plugin_root / "schemas" / "provider-profiles.schema.json").resolve()
    binding_path = (pack_path / "runtime" / "plugins" / "provider-bindings.local.yaml").resolve()

    contract = _select_contract(task)
    required = contract_required(contract)
    auto_required_signal = registry_path.exists()
    if auto_required_signal:
        required = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "producer_readiness": False,
        "requiredization_current_round_linked": bool(required and args.operation in STRICT_OPERATIONS),
        "multimodal_plugin_enforcement_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_registry_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_naming_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_schema_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_threshold_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_path_status": STATUS_SKIPPED_NOT_REQUIRED,
        "plugin_copy_policy_status": STATUS_SKIPPED_NOT_REQUIRED,
        "provider_config_status": STATUS_SKIPPED_NOT_REQUIRED,
        "provider_profile_id": "",
        "plugin_contract_owner": "protocol_base_repo",
        "plugin_resolution_mode": "central_registry",
        "multimodal_runtime_evidence_status": STATUS_SKIPPED_NOT_REQUIRED,
        "multimodal_preflight_status": "",
        "runtime_report_path": "",
        "runtime_report_run_id": "",
        "multimodal_calls": None,
        "multimodal_resolved": None,
        "multimodal_unresolved": None,
        "multimodal_errors": None,
        "multimodal_retry_calls": None,
        "runtime_gate_mode": "",
        "runtime_gate_required_confidence": None,
        "multimodal_runtime_evidence_refs": [],
        "error_code": "",
        "stale_reasons": [],
        "evidence_ref": "",
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["producer_readiness"] = True
    payload["plugin_registry_status"] = STATUS_PASS_REQUIRED
    payload["plugin_naming_status"] = STATUS_PASS_REQUIRED
    payload["plugin_schema_status"] = STATUS_PASS_REQUIRED
    payload["plugin_threshold_status"] = STATUS_PASS_REQUIRED
    payload["plugin_path_status"] = STATUS_PASS_REQUIRED
    payload["plugin_copy_policy_status"] = STATUS_PASS_REQUIRED
    payload["provider_config_status"] = STATUS_PASS_REQUIRED

    stale_reasons: list[str] = []
    error_code = ""

    # Path contract
    if not _within(plugin_root, repo_root):
        payload["plugin_path_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("plugin_root_outside_repo")
        error_code = error_code or ERR_PATH

    required_registry_files = [
        registry_path,
        registry_schema_path,
        provider_profiles_path,
        provider_schema_path,
    ]
    missing_registry_files = [str(p) for p in required_registry_files if not p.exists()]
    if missing_registry_files:
        payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("canonical_plugin_registry_files_missing")
        error_code = error_code or ERR_REGISTRY

    registry_doc: dict[str, Any] = {}
    provider_doc: dict[str, Any] = {}
    if not missing_registry_files:
        try:
            registry_doc = _load_yaml(registry_path)
            provider_doc = _load_yaml(provider_profiles_path)
            _load_json_file(registry_schema_path)
            _load_json_file(provider_schema_path)
        except Exception:
            payload["plugin_schema_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("schema_or_registry_parse_failed")
            error_code = error_code or ERR_CONF_FIELDS

    profiles_by_id: dict[str, dict[str, Any]] = {}
    if provider_doc:
        profiles = provider_doc.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("provider_profiles_empty")
            error_code = error_code or ERR_CONF_FIELDS
        else:
            for row in profiles:
                if not isinstance(row, dict):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_profile_row_not_object")
                    error_code = error_code or ERR_CONF_FIELDS
                    continue
                pid = str(row.get("profile_id", "")).strip()
                if not PROFILE_ID_RE.fullmatch(pid):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_profile_id_invalid")
                    error_code = error_code or ERR_CONF_FIELDS
                    continue
                api_base_env = str(row.get("api_base_env", "")).strip()
                api_key_env = str(row.get("api_key_env", "")).strip()
                if not ENV_KEY_RE.fullmatch(api_base_env) or not ENV_KEY_RE.fullmatch(api_key_env):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_profile_env_key_invalid")
                    error_code = error_code or ERR_CONF_FIELDS
                governance = row.get("governance")
                if not isinstance(governance, dict):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_governance_missing")
                    error_code = error_code or ERR_CONF_FIELDS
                else:
                    allowlist = governance.get("endpoint_allowlist")
                    if not isinstance(allowlist, list) or not allowlist:
                        payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                        stale_reasons.append("provider_endpoint_allowlist_missing")
                        error_code = error_code or ERR_CONF_ENDPOINT
                profiles_by_id[pid] = row

    plugins = registry_doc.get("plugins") if isinstance(registry_doc, dict) else None
    if not isinstance(plugins, list) or not plugins:
        payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("plugin_registry_empty")
        error_code = error_code or ERR_REGISTRY
        plugins = []

    referenced_profile_ids: set[str] = set()
    registry_plugin_ids: set[str] = set()
    required_binding_plugin_ids: set[str] = set()
    for plugin_row in plugins:
        if not isinstance(plugin_row, dict):
            payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_registry_row_not_object")
            error_code = error_code or ERR_REGISTRY
            continue

        plugin_id = str(plugin_row.get("plugin_id", "")).strip()
        if not PLUGIN_ID_RE.fullmatch(plugin_id):
            payload["plugin_naming_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_id_invalid")
            error_code = error_code or ERR_NAME
            continue
        registry_plugin_ids.add(plugin_id)

        contract_rel = str(plugin_row.get("contract_file", "")).strip()
        validator_script = str(plugin_row.get("validator_script", "")).strip()
        if not contract_rel or not validator_script:
            payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_registry_required_fields_missing")
            error_code = error_code or ERR_REGISTRY
            continue

        contract_path = (repo_root / contract_rel).resolve()
        if not contract_path.exists() or not _within(contract_path, plugin_root):
            payload["plugin_path_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_contract_non_canonical_path")
            error_code = error_code or ERR_PATH
            continue

        validator_path = (repo_root / validator_script).resolve()
        if not validator_path.exists():
            payload["plugin_registry_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_validator_missing")
            error_code = error_code or ERR_REGISTRY

        plugin_dir = contract_path.parent
        required_plugin_files = [
            plugin_dir / "plugin.contract.yaml",
            plugin_dir / "plugin.input.schema.json",
            plugin_dir / "plugin.output.schema.json",
            plugin_dir / "plugin.error-codes.yaml",
            plugin_dir / "README.md",
        ]
        missing_plugin_files = [str(p) for p in required_plugin_files if not p.exists()]
        if missing_plugin_files:
            payload["plugin_naming_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_contract_file_topology_incomplete")
            error_code = error_code or ERR_NAME_FILE

        try:
            contract_doc = _load_yaml(contract_path)
        except Exception:
            payload["plugin_schema_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("plugin_contract_parse_failed")
            error_code = error_code or ERR_CONF_FIELDS
            continue

        provider_binding = contract_doc.get("provider_binding")
        if isinstance(provider_binding, dict) and _boolish(provider_binding.get("required", False)):
            required_binding_plugin_ids.add(plugin_id)

        thresholds = contract_doc.get("required_thresholds")
        if not isinstance(thresholds, dict):
            payload["plugin_threshold_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("required_thresholds_missing")
            error_code = error_code or ERR_THRESHOLD
        else:
            min_conf = thresholds.get("min_confidence")
            max_conf = thresholds.get("max_confidence")
            min_chars = thresholds.get("min_char_count")
            max_chars = thresholds.get("max_char_count")
            if not isinstance(min_conf, (int, float)) or not isinstance(max_conf, (int, float)):
                payload["plugin_threshold_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("confidence_threshold_type_invalid")
                error_code = error_code or ERR_THRESHOLD
            elif not (0 <= float(min_conf) <= float(max_conf) <= 1):
                payload["plugin_threshold_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("confidence_threshold_out_of_range")
                error_code = error_code or ERR_THRESHOLD
            if not isinstance(min_chars, int) or not isinstance(max_chars, int):
                payload["plugin_threshold_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("char_threshold_type_invalid")
                error_code = error_code or ERR_THRESHOLD
            elif min_chars < 0 or max_chars < min_chars:
                payload["plugin_threshold_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("char_threshold_out_of_range")
                error_code = error_code or ERR_THRESHOLD

        required_caps = contract_doc.get("required_capabilities")
        allowed_profiles = (contract_doc.get("provider_binding") or {}).get("allowed_profiles")
        if isinstance(required_caps, dict) and isinstance(allowed_profiles, list):
            for profile_id in allowed_profiles:
                profile_key = str(profile_id or "").strip()
                if not profile_key:
                    continue
                referenced_profile_ids.add(profile_key)
                profile = profiles_by_id.get(profile_key)
                if not isinstance(profile, dict):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_profile_missing_for_plugin")
                    error_code = error_code or ERR_CONF_PROFILE
                    continue
                caps = profile.get("capabilities")
                if not isinstance(caps, dict):
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("provider_capabilities_missing")
                    error_code = error_code or ERR_CONF_FIELDS
                    continue
                for cap_name, cap_required in required_caps.items():
                    if _boolish(cap_required) and not _boolish(caps.get(cap_name)):
                        payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                        stale_reasons.append(f"provider_capability_mismatch:{cap_name}")
                        error_code = error_code or ERR_CONF_CAPABILITY

    # Registry provider profile references
    for plugin_row in plugins:
        if not isinstance(plugin_row, dict):
            continue
        for profile_id in plugin_row.get("provider_profiles") or []:
            key = str(profile_id or "").strip()
            if key:
                referenced_profile_ids.add(key)

    for profile_id in sorted(referenced_profile_ids):
        if profile_id not in profiles_by_id:
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("provider_profile_not_found_in_registry")
            error_code = error_code or ERR_CONF_PROFILE

    # Runtime binding verification (instance-local pointers only)
    selected_profile_id = ""
    seen_enabled_binding_for_plugin: set[str] = set()
    if binding_path.exists():
        try:
            binding_doc = _load_yaml(binding_path)
            bindings = _flatten_bindings(binding_doc)
        except Exception:
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("provider_bindings_parse_failed")
            error_code = error_code or ERR_CONF_FIELDS
            bindings = []

        for row in bindings:
            enabled = _boolish(row.get("enabled", True))
            if not enabled:
                continue
            plugin_id = str(row.get("plugin_id", "")).strip()
            profile_id = str(row.get("provider_profile_id", "")).strip()
            credential_ref = str(row.get("credential_ref", "")).strip()
            if plugin_id:
                seen_enabled_binding_for_plugin.add(plugin_id)
            if plugin_id and not PLUGIN_ID_RE.fullmatch(plugin_id):
                payload["plugin_naming_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("binding_plugin_id_invalid")
                error_code = error_code or ERR_NAME
            elif plugin_id and plugin_id not in registry_plugin_ids:
                payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("binding_plugin_not_in_registry")
                error_code = error_code or ERR_CONF_PROFILE
            if not profile_id or profile_id not in profiles_by_id:
                payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("binding_provider_profile_missing")
                error_code = error_code or ERR_CONF_PROFILE
            else:
                selected_profile_id = profile_id

            if not credential_ref or not CREDENTIAL_REF_RE.fullmatch(credential_ref):
                payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("binding_credential_ref_invalid")
                error_code = error_code or ERR_CONF_CREDENTIAL
            elif credential_ref.startswith("env:"):
                env_key = credential_ref.split(":", 1)[1]
                if not str(os.getenv(env_key, "")).strip():
                    payload["provider_config_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("binding_credential_env_unresolved")
                    error_code = error_code or ERR_CONF_CREDENTIAL
    elif required_binding_plugin_ids:
        payload["provider_config_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("provider_binding_file_missing")
        error_code = error_code or ERR_CONF_PROFILE

    if required_binding_plugin_ids:
        missing_required_bindings = sorted(
            plugin_id for plugin_id in required_binding_plugin_ids if plugin_id not in seen_enabled_binding_for_plugin
        )
        if missing_required_bindings:
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("provider_binding_required_plugin_missing")
            error_code = error_code or ERR_CONF_PROFILE
            payload["missing_required_binding_plugins"] = missing_required_bindings

    if selected_profile_id:
        payload["provider_profile_id"] = selected_profile_id

    # Endpoint policy check on configured env values (if present)
    for profile_id, profile in profiles_by_id.items():
        governance = profile.get("governance") if isinstance(profile, dict) else None
        if not isinstance(governance, dict):
            continue
        require_https = _boolish(governance.get("require_https", False))
        allowlist = [str(x).strip() for x in (governance.get("endpoint_allowlist") or []) if str(x).strip()]
        api_base_env = str(profile.get("api_base_env", "")).strip()
        api_base_value = str(os.getenv(api_base_env, "")).strip() if api_base_env else ""
        if not api_base_value:
            continue
        if require_https and not api_base_value.lower().startswith("https://"):
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append(f"provider_endpoint_non_https:{profile_id}")
            error_code = error_code or ERR_CONF_ENDPOINT
            continue
        host = api_base_value.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0].strip().lower()
        if allowlist and host and host not in {x.lower() for x in allowlist}:
            payload["provider_config_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append(f"provider_endpoint_not_allowlisted:{profile_id}")
            error_code = error_code or ERR_CONF_ENDPOINT

    # Copy policy: forbid plugin contract/source copies inside identity pack.
    forbidden_hits: list[str] = []
    for pattern in (
        "**/plugin.contract.yaml",
        "**/plugin.input.schema.json",
        "**/plugin.output.schema.json",
        "**/plugin.error-codes.yaml",
        "**/adapters/*.py",
    ):
        forbidden_hits.extend(str(p.resolve()) for p in pack_path.glob(pattern) if p.is_file())
    if forbidden_hits:
        payload["plugin_copy_policy_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("instance_plugin_copy_detected")
        error_code = error_code or ERR_COPY
    payload["forbidden_copy_refs"] = sorted(dict.fromkeys(forbidden_hits))

    runtime_required = str(args.operation or "").strip().lower() in RUNTIME_PROOF_REQUIRED_OPERATIONS
    runtime_report_path = _resolve_runtime_report(
        pack_path=pack_path,
        identity_id=args.identity_id,
        report_selected_path=str(args.report_selected_path or "").strip(),
    )
    runtime_report_doc: dict[str, Any] = {}
    if runtime_required:
        if runtime_report_path is None:
            payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
            payload["multimodal_preflight_status"] = "MISSING"
            stale_reasons.append("runtime_report_missing")
            error_code = error_code or ERR_RUNTIME_REPORT_MISSING
        else:
            payload["runtime_report_path"] = str(runtime_report_path)
            try:
                runtime_report_doc = load_json(runtime_report_path)
            except Exception:
                payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                payload["multimodal_preflight_status"] = "MISSING"
                stale_reasons.append("runtime_report_parse_failed")
                error_code = error_code or ERR_RUNTIME_REPORT_MISSING

    if runtime_required and runtime_report_doc:
        runtime_report_run_id = str(runtime_report_doc.get("run_id", "")).strip()
        payload["runtime_report_run_id"] = runtime_report_run_id

        requested_run_id = str(args.run_id or "").strip()
        if (
            requested_run_id.startswith("identity-upgrade-exec-")
            and runtime_report_run_id
            and requested_run_id != runtime_report_run_id
        ):
            payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
            stale_reasons.append("runtime_report_not_current_round")
            error_code = error_code or ERR_RUNTIME_RUN_MISMATCH

        summary = runtime_report_doc.get("multimodal_summary")
        summary_doc = summary if isinstance(summary, dict) else {}
        payload["multimodal_calls"] = _to_int(
            _pick_first_nonempty(
                runtime_report_doc,
                ("multimodal_calls", "multimodal_call_count", "multimodal_total_calls"),
            )
            if _pick_first_nonempty(runtime_report_doc, ("multimodal_calls", "multimodal_call_count", "multimodal_total_calls")) is not None
            else _pick_first_nonempty(summary_doc, ("calls", "total_calls")),
        )
        payload["multimodal_resolved"] = _to_int(
            _pick_first_nonempty(runtime_report_doc, ("multimodal_resolved",))
            if _pick_first_nonempty(runtime_report_doc, ("multimodal_resolved",)) is not None
            else _pick_first_nonempty(summary_doc, ("resolved",)),
        )
        payload["multimodal_unresolved"] = _to_int(
            _pick_first_nonempty(runtime_report_doc, ("multimodal_unresolved",))
            if _pick_first_nonempty(runtime_report_doc, ("multimodal_unresolved",)) is not None
            else _pick_first_nonempty(summary_doc, ("unresolved",)),
        )
        payload["multimodal_errors"] = _to_int(
            _pick_first_nonempty(runtime_report_doc, ("multimodal_errors",))
            if _pick_first_nonempty(runtime_report_doc, ("multimodal_errors",)) is not None
            else _pick_first_nonempty(summary_doc, ("errors",)),
        )
        payload["multimodal_retry_calls"] = _to_int(
            _pick_first_nonempty(runtime_report_doc, ("multimodal_retry_calls",))
            if _pick_first_nonempty(runtime_report_doc, ("multimodal_retry_calls",)) is not None
            else _pick_first_nonempty(summary_doc, ("retry_calls",)),
        )
        payload["runtime_gate_mode"] = str(
            _pick_first_nonempty(
                runtime_report_doc,
                ("runtime_gate_mode", "multimodal_gate_mode", "input_gate_mode"),
            )
            if _pick_first_nonempty(runtime_report_doc, ("runtime_gate_mode", "multimodal_gate_mode", "input_gate_mode")) is not None
            else _pick_first_nonempty(summary_doc, ("mode", "gate_mode"))
            or ""
        ).strip().lower()
        payload["runtime_gate_required_confidence"] = _to_float(
            _pick_first_nonempty(
                runtime_report_doc,
                (
                    "runtime_gate_required_confidence",
                    "multimodal_required_confidence",
                    "input_gate_required_confidence",
                ),
            )
            if _pick_first_nonempty(
                runtime_report_doc,
                (
                    "runtime_gate_required_confidence",
                    "multimodal_required_confidence",
                    "input_gate_required_confidence",
                ),
            )
            is not None
            else _pick_first_nonempty(summary_doc, ("required_confidence", "gate_required_confidence")),
        )

        raw_evidence_refs: list[str] = []
        for key in (
            "input_gate_report_path",
            "multimodal_confirmation_results_path",
            "multimodal_input_gate_report_path",
            "multimodal_confirmation_csv_path",
        ):
            value = runtime_report_doc.get(key)
            if isinstance(value, str) and value.strip():
                raw_evidence_refs.append(value.strip())
        for key in (
            "input_gate_report_path",
            "multimodal_confirmation_results_path",
            "multimodal_input_gate_report_path",
            "multimodal_confirmation_csv_path",
        ):
            value = summary_doc.get(key)
            if isinstance(value, str) and value.strip():
                raw_evidence_refs.append(value.strip())
        refs_from_list = runtime_report_doc.get("multimodal_evidence_refs")
        if isinstance(refs_from_list, list):
            raw_evidence_refs.extend(str(x).strip() for x in refs_from_list if str(x).strip())

        resolved_evidence_refs: list[str] = []
        missing_evidence_refs: list[str] = []
        for raw_ref in raw_evidence_refs:
            p = Path(raw_ref).expanduser()
            if not p.is_absolute():
                p = (pack_path / p).resolve()
            else:
                p = p.resolve()
            token = str(p)
            resolved_evidence_refs.append(token)
            if not p.exists():
                missing_evidence_refs.append(token)
        payload["multimodal_runtime_evidence_refs"] = sorted(dict.fromkeys(resolved_evidence_refs))

        runtime_gate_status = str(
            _pick_first_nonempty(
                runtime_report_doc,
                ("multimodal_preflight_status", "input_gate_status", "multimodal_gate_status"),
            )
            or ""
        ).strip().upper()
        payload["multimodal_preflight_status"] = runtime_gate_status or "MISSING"
        runtime_gate_skipped = any(
            _boolish(runtime_report_doc.get(key))
            for key in ("multimodal_gate_skipped", "input_gate_skipped", "skip_input_gate")
        ) or runtime_gate_status in {"SKIPPED", "BYPASSED", "SKIP_REQUIRED"}

        if payload["multimodal_runtime_evidence_status"] != STATUS_FAIL_REQUIRED:
            if runtime_gate_skipped:
                payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("runtime_gate_skipped_without_receipt")
                error_code = error_code or ERR_RUNTIME_GATE_SKIPPED
            elif (
                payload["multimodal_calls"] is None
                and payload["multimodal_resolved"] is None
                and payload["multimodal_unresolved"] is None
                and payload["multimodal_errors"] is None
                and not payload["multimodal_runtime_evidence_refs"]
            ):
                payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("runtime_stage_missing_input_gate")
                error_code = error_code or ERR_RUNTIME_STAGE_MISSING
            elif missing_evidence_refs:
                payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                stale_reasons.append("runtime_evidence_file_missing")
                error_code = error_code or ERR_RUNTIME_EVIDENCE_MISSING
            elif payload["runtime_gate_mode"] == "required":
                unresolved = payload["multimodal_unresolved"]
                errors = payload["multimodal_errors"]
                if unresolved is not None and unresolved > 0:
                    payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("runtime_required_mode_unresolved")
                    error_code = error_code or ERR_RUNTIME_REQUIRED_UNRESOLVED
                elif errors is not None and errors > 0:
                    payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
                    stale_reasons.append("runtime_provider_error_unrecovered")
                    error_code = error_code or ERR_RUNTIME_PROVIDER_ERROR
                else:
                    payload["multimodal_runtime_evidence_status"] = STATUS_PASS_REQUIRED
            else:
                payload["multimodal_runtime_evidence_status"] = STATUS_PASS_REQUIRED
    elif runtime_required and payload["multimodal_runtime_evidence_status"] != STATUS_FAIL_REQUIRED:
        payload["multimodal_runtime_evidence_status"] = STATUS_FAIL_REQUIRED
        stale_reasons.append("runtime_report_missing")
        error_code = error_code or ERR_RUNTIME_REPORT_MISSING

    payload["evidence_ref"] = ";".join(
        [
            str(registry_path),
            str(provider_profiles_path),
            str(binding_path),
            str(payload.get("runtime_report_path", "") or ""),
        ]
    )

    failed_statuses = [
        payload["plugin_registry_status"],
        payload["plugin_naming_status"],
        payload["plugin_schema_status"],
        payload["plugin_threshold_status"],
        payload["plugin_path_status"],
        payload["plugin_copy_policy_status"],
        payload["provider_config_status"],
        payload["multimodal_runtime_evidence_status"],
    ]
    if any(status == STATUS_FAIL_REQUIRED for status in failed_statuses):
        payload["multimodal_plugin_enforcement_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_REGISTRY
        payload["stale_reasons"] = sorted(dict.fromkeys(stale_reasons))
        _emit(payload, json_only=args.json_only)
        return 1

    payload["multimodal_plugin_enforcement_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
