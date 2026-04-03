#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERROR_CONFIG = "IP-PLUGIN-PROJ-001"
ERROR_PARITY = "IP-PLUGIN-PROJ-002"

REQUIRED_ENTRY_FIELDS = [
    "plugin_id",
    "requirement_key",
    "bundle_target_name",
    "gate_mode",
    "ssot_mapping_ref",
    "integration_kind",
    "protocol_contract_root",
    "instance_runtime_root",
    "contract_file",
    "validator_script",
    "status",
    "required_gate_surfaces",
    "required_report_fields",
]

INTEGRATION_KIND_RULES = {
    "skill": {
        "protocol_contract_root": "identity/protocol/plugins/skill",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/skills",
    },
    "mcp": {
        "protocol_contract_root": "identity/protocol/plugins/mcp",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/mcp",
    },
    "api": {
        "protocol_contract_root": "identity/protocol/plugins",
        "instance_runtime_root": ".identity/{identity_id}/runtime/plugins/api",
    },
}


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _resolve_current_alias(repo_root: Path, rel_path: str) -> tuple[Path, str, str]:
    entry_path = (repo_root / rel_path).resolve()
    if not entry_path.exists() or not entry_path.is_file():
        return entry_path, "", "entry_file_missing"
    doc = _load_yaml(entry_path)
    active_file = str(doc.get("active_file", "")).strip()
    if not active_file:
        return entry_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _as_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _as_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _as_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = _as_text(item)
        if text:
            out.append(text)
    return out


def _as_set(value: Any) -> set[str]:
    return set(_as_text_list(value))


def _path_within_root(path_value: str, root_value: str) -> bool:
    norm_path = path_value.strip().strip("/")
    norm_root = root_value.strip().strip("/")
    if not norm_path or not norm_root:
        return False
    return norm_path == norm_root or norm_path.startswith(f"{norm_root}/")


def _index_by(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        token = _as_text(row.get(key, ""))
        if token:
            out[token] = row
    return out


def _append_violation(violations: list[dict[str, Any]], field: str, reason: str, **extra: Any) -> None:
    row = {"field": field, "reason": reason}
    row.update(extra)
    violations.append(row)


def _missing_required_fields(entry: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in REQUIRED_ENTRY_FIELDS:
        value = entry.get(key)
        if key.endswith("_surfaces") or key.endswith("_fields"):
            if not _as_text_list(value):
                missing.append(key)
            continue
        if not _as_text(value):
            missing.append(key)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-close parity checker for plugin join intake wiring.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check parity only")
    mode.add_argument("--apply", action="store_true", help="reserved for future apply mode")
    parser.add_argument("--repo-root", default="")
    parser.add_argument(
        "--intake-current",
        default="identity/protocol/plugins/PLUGIN_JOIN_INTAKE.current.yaml",
    )
    parser.add_argument(
        "--registry-current",
        default="identity/protocol/plugins/PLUGIN_REGISTRY.current.yaml",
    )
    parser.add_argument(
        "--governance-current",
        default="identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.current.yaml",
    )
    parser.add_argument(
        "--mapping-current",
        default="identity/protocol/mappings/contract-binding.current.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)

    intake_path, intake_active_file, intake_alias_error = _resolve_current_alias(repo_root, str(args.intake_current))
    registry_path, registry_active_file, registry_alias_error = _resolve_current_alias(repo_root, str(args.registry_current))
    governance_path, governance_active_file, governance_alias_error = _resolve_current_alias(
        repo_root, str(args.governance_current)
    )
    mapping_path, mapping_active_file, mapping_alias_error = _resolve_current_alias(repo_root, str(args.mapping_current))

    violations: list[dict[str, Any]] = []
    stale_reasons: list[str] = []

    alias_errors = {
        "intake_alias_error": intake_alias_error,
        "registry_alias_error": registry_alias_error,
        "governance_alias_error": governance_alias_error,
        "mapping_alias_error": mapping_alias_error,
    }
    for field, error in alias_errors.items():
        if error:
            stale_reasons.append(f"{field}:{error}")
            _append_violation(violations, field=field, reason=error)

    intake_rows: list[dict[str, Any]] = []
    registry_rows: list[dict[str, Any]] = []
    governance_rows: list[dict[str, Any]] = []
    mapping_doc: dict[str, Any] = {}

    if not violations:
        intake_doc = _load_yaml(intake_path)
        registry_doc = _load_yaml(registry_path)
        governance_doc = _load_yaml(governance_path)
        mapping_doc = _load_yaml(mapping_path)

        intake_rows = _as_rows(intake_doc.get("plugins"))
        registry_rows = _as_rows(registry_doc.get("plugins"))
        governance_rows = _as_rows(governance_doc.get("plugin_failclose_profiles"))

        if not intake_rows:
            _append_violation(violations, field="intake.plugins", reason="plugins_empty")

        intake_by_plugin = _index_by(intake_rows, "plugin_id")
        registry_by_plugin = _index_by(registry_rows, "plugin_id")
        governance_by_plugin = _index_by(governance_rows, "plugin_id")

        for plugin_id, entry in intake_by_plugin.items():
            missing_fields = _missing_required_fields(entry)
            for key in missing_fields:
                _append_violation(
                    violations,
                    field="intake.plugins",
                    reason="required_field_missing",
                    plugin_id=plugin_id,
                    key=key,
                )

            requirement_key = _as_text(entry.get("requirement_key"))
            bundle_target = _as_text(entry.get("bundle_target_name"))
            validator_script = _as_text(entry.get("validator_script"))
            integration_kind = _as_text(entry.get("integration_kind")).lower()
            protocol_contract_root = _as_text(entry.get("protocol_contract_root"))
            instance_runtime_root = _as_text(entry.get("instance_runtime_root"))
            contract_file = _as_text(entry.get("contract_file"))

            rule = INTEGRATION_KIND_RULES.get(integration_kind)
            if rule is None:
                _append_violation(
                    violations,
                    field="intake.plugins",
                    reason="integration_kind_invalid",
                    plugin_id=plugin_id,
                    integration_kind=integration_kind,
                    allowed=sorted(INTEGRATION_KIND_RULES.keys()),
                )
            else:
                expected_protocol_root = rule["protocol_contract_root"]
                expected_runtime_root = rule["instance_runtime_root"]
                if protocol_contract_root != expected_protocol_root:
                    _append_violation(
                        violations,
                        field="intake.plugins",
                        reason="protocol_contract_root_mismatch",
                        plugin_id=plugin_id,
                        expected=expected_protocol_root,
                        observed=protocol_contract_root,
                    )
                if instance_runtime_root != expected_runtime_root:
                    _append_violation(
                        violations,
                        field="intake.plugins",
                        reason="instance_runtime_root_mismatch",
                        plugin_id=plugin_id,
                        expected=expected_runtime_root,
                        observed=instance_runtime_root,
                    )
            if contract_file and protocol_contract_root and not _path_within_root(contract_file, protocol_contract_root):
                _append_violation(
                    violations,
                    field="intake.plugins",
                    reason="contract_file_out_of_protocol_root",
                    plugin_id=plugin_id,
                    contract_file=contract_file,
                    protocol_contract_root=protocol_contract_root,
                )

            mapping_ref_expected = f"{mapping_active_file or args.mapping_current}#{requirement_key}"
            mapping_ref_observed = _as_text(entry.get("ssot_mapping_ref"))
            if requirement_key and mapping_ref_observed != mapping_ref_expected:
                _append_violation(
                    violations,
                    field="intake.plugins",
                    reason="ssot_mapping_ref_mismatch",
                    plugin_id=plugin_id,
                    expected=mapping_ref_expected,
                    observed=mapping_ref_observed,
                )

            registry_row = registry_by_plugin.get(plugin_id)
            if registry_row is None:
                _append_violation(violations, field="registry.plugins", reason="plugin_missing", plugin_id=plugin_id)
            else:
                for key in [
                    "integration_kind",
                    "protocol_contract_root",
                    "instance_runtime_root",
                    "requirement_key",
                    "bundle_target_name",
                    "gate_mode",
                    "ssot_mapping_ref",
                    "contract_file",
                    "validator_script",
                    "status",
                ]:
                    expected = _as_text(entry.get(key))
                    observed = _as_text(registry_row.get(key))
                    if expected != observed:
                        _append_violation(
                            violations,
                            field="registry.plugins",
                            reason="tuple_field_mismatch",
                            plugin_id=plugin_id,
                            key=key,
                            expected=expected,
                            observed=observed,
                        )

                expected_profiles = _as_set(entry.get("provider_profiles"))
                observed_profiles = _as_set(registry_row.get("provider_profiles"))
                if expected_profiles != observed_profiles:
                    _append_violation(
                        violations,
                        field="registry.plugins",
                        reason="provider_profiles_mismatch",
                        plugin_id=plugin_id,
                        expected=sorted(expected_profiles),
                        observed=sorted(observed_profiles),
                    )

            governance_row = governance_by_plugin.get(plugin_id)
            if governance_row is None:
                _append_violation(violations, field="governance.plugin_failclose_profiles", reason="plugin_missing", plugin_id=plugin_id)
            else:
                tuple_expect = {
                    "requirement_key": requirement_key,
                    "target_name": bundle_target,
                    "contract_file": _as_text(entry.get("contract_file")),
                    "validator_script": validator_script,
                }
                for key, expected in tuple_expect.items():
                    observed = _as_text(governance_row.get(key))
                    if expected != observed:
                        _append_violation(
                            violations,
                            field="governance.plugin_failclose_profiles",
                            reason="tuple_field_mismatch",
                            plugin_id=plugin_id,
                            key=key,
                            expected=expected,
                            observed=observed,
                        )

                expected_surfaces = _as_set(entry.get("required_gate_surfaces"))
                observed_surfaces = _as_set(governance_row.get("required_gate_surfaces"))
                if expected_surfaces != observed_surfaces:
                    _append_violation(
                        violations,
                        field="governance.plugin_failclose_profiles",
                        reason="required_gate_surfaces_mismatch",
                        plugin_id=plugin_id,
                        expected=sorted(expected_surfaces),
                        observed=sorted(observed_surfaces),
                    )

                expected_fields = _as_set(entry.get("required_report_fields"))
                observed_fields = _as_set(governance_row.get("required_report_fields"))
                if expected_fields != observed_fields:
                    _append_violation(
                        violations,
                        field="governance.plugin_failclose_profiles",
                        reason="required_report_fields_mismatch",
                        plugin_id=plugin_id,
                        expected_count=len(expected_fields),
                        observed_count=len(observed_fields),
                    )

                intake_monotonic = entry.get("monotonic_policy")
                gov_monotonic = governance_row.get("monotonic_policy")
                if isinstance(intake_monotonic, dict):
                    if not isinstance(gov_monotonic, dict):
                        _append_violation(
                            violations,
                            field="governance.plugin_failclose_profiles",
                            reason="monotonic_policy_missing",
                            plugin_id=plugin_id,
                        )
                    else:
                        for key, expected in intake_monotonic.items():
                            observed = gov_monotonic.get(key)
                            if observed != expected:
                                _append_violation(
                                    violations,
                                    field="governance.plugin_failclose_profiles",
                                    reason="monotonic_policy_mismatch",
                                    plugin_id=plugin_id,
                                    key=key,
                                    expected=expected,
                                    observed=observed,
                                )

            mapping_row = mapping_doc.get(requirement_key)
            if not isinstance(mapping_row, dict):
                _append_violation(
                    violations,
                    field="contract_binding",
                    reason="requirement_missing",
                    plugin_id=plugin_id,
                    requirement_key=requirement_key,
                )
            else:
                validator_ids = _as_set(mapping_row.get("validator_ids"))
                if validator_script not in validator_ids:
                    _append_violation(
                        violations,
                        field="contract_binding",
                        reason="validator_missing",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        validator_script=validator_script,
                    )

                expected_surfaces = _as_set(entry.get("required_gate_surfaces"))
                observed_surfaces = _as_set(mapping_row.get("gate_surfaces"))
                if expected_surfaces != observed_surfaces:
                    _append_violation(
                        violations,
                        field="contract_binding",
                        reason="gate_surfaces_mismatch",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        expected=sorted(expected_surfaces),
                        observed=sorted(observed_surfaces),
                    )

                expected_fields = _as_set(entry.get("required_report_fields"))
                observed_fields = _as_set(mapping_row.get("report_field_refs"))
                if expected_fields != observed_fields:
                    _append_violation(
                        violations,
                        field="contract_binding",
                        reason="report_field_refs_mismatch",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        expected_count=len(expected_fields),
                        observed_count=len(observed_fields),
                    )

                expected_codes = _as_set(entry.get("error_code_refs"))
                observed_codes = _as_set(mapping_row.get("error_code_refs"))
                if expected_codes and expected_codes != observed_codes:
                    _append_violation(
                        violations,
                        field="contract_binding",
                        reason="error_code_refs_mismatch",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        expected=sorted(expected_codes),
                        observed=sorted(observed_codes),
                    )

        intake_plugin_ids = set(intake_by_plugin.keys())
        strict_registry_ids = {
            _as_text(row.get("plugin_id"))
            for row in registry_rows
            if _as_text(row.get("gate_mode")) == "fail_close_strict" and _as_text(row.get("status")) == "active"
        }
        strict_registry_ids.discard("")

        for plugin_id in sorted(strict_registry_ids - intake_plugin_ids):
            _append_violation(
                violations,
                field="intake.plugins",
                reason="missing_strict_registry_plugin",
                plugin_id=plugin_id,
            )

    status = STATUS_PASS_REQUIRED
    error_code = ""
    if violations:
        status = STATUS_FAIL_REQUIRED
        has_config_issue = any(v.get("field", "").endswith("_alias_error") for v in violations)
        error_code = ERROR_CONFIG if has_config_issue else ERROR_PARITY

    payload: dict[str, Any] = {
        "plugin_join_sync_status": status,
        "error_code": error_code,
        "mode": "apply" if args.apply else "check",
        "repo_root": str(repo_root),
        "intake_entry_file": str((repo_root / str(args.intake_current)).resolve()),
        "intake_file": str(intake_path),
        "intake_active_file": intake_active_file,
        "intake_alias_error": intake_alias_error,
        "registry_file": str(registry_path),
        "registry_active_file": registry_active_file,
        "registry_alias_error": registry_alias_error,
        "governance_file": str(governance_path),
        "governance_active_file": governance_active_file,
        "governance_alias_error": governance_alias_error,
        "mapping_file": str(mapping_path),
        "mapping_active_file": mapping_active_file,
        "mapping_alias_error": mapping_alias_error,
        "intake_row_count": len(intake_rows),
        "registry_row_count": len(registry_rows),
        "governance_row_count": len(governance_rows),
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    text = json.dumps(payload, ensure_ascii=False)
    if args.json_only:
        print(text)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
