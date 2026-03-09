#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_INVARIANT = "IP-CP-INV-001"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def _mapping_rows(mapping_doc: dict[str, Any]) -> list[str]:
    return sorted(k for k in mapping_doc.keys() if isinstance(k, str) and k.startswith("asb16-rq-"))


def _bundle_rows() -> list[str]:
    from required_gate_bundle_runner import BUNDLE_REQUIREMENT_ORDER  # local import for script stability

    return sorted(set(str(x).strip() for x in BUNDLE_REQUIREMENT_ORDER if str(x).strip()))


def _bundle_target_map() -> dict[str, str]:
    from required_gate_bundle_runner import TARGET_NAME_BY_REQUIREMENT  # local import for script stability

    return {
        str(k).strip(): str(v).strip()
        for k, v in TARGET_NAME_BY_REQUIREMENT.items()
        if str(k).strip() and str(v).strip()
    }


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_str_list(value: Any) -> list[str]:
    return [str(x).strip() for x in _as_list(value) if str(x).strip()]


def _mapping_validator_scripts(row: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for raw in _as_str_list(row.get("validator_ids")):
        script = raw.split("::", 1)[0].strip()
        if script:
            out.add(script)
    return out


def _append_violation(violations: list[dict[str, Any]], *, field: str, reason: str, **extra: Any) -> None:
    row = {"field": field, "reason": reason}
    row.update(extra)
    violations.append(row)


def _surface_token_present(repo_root: Path, rel_path: str, token: str) -> tuple[bool, str]:
    path = (repo_root / rel_path).resolve()
    if not path.exists():
        return False, "surface_missing"
    text = _read_text(path)
    return (token in text), ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-plane invariants (bundle/mapping parity + fail-close plugin wiring).")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--invariants-file",
        default="identity/protocol/mappings/control-plane-invariants.v1.6.yaml",
    )
    parser.add_argument(
        "--contract-mapping",
        default="identity/protocol/mappings/contract-binding.v1.6.yaml",
    )
    parser.add_argument(
        "--plugin-governance-file",
        default="identity/protocol/plugins/FAILCLOSE_PLUGIN_GOVERNANCE.v1.6.2.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    invariants_path = (repo_root / str(args.invariants_file)).resolve()
    mapping_path = (repo_root / str(args.contract_mapping)).resolve()
    plugin_governance_path = (repo_root / str(args.plugin_governance_file)).resolve()

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []

    if not invariants_path.exists():
        stale_reasons.append(f"invariants_file_missing:{invariants_path}")
    if not mapping_path.exists():
        stale_reasons.append(f"contract_mapping_missing:{mapping_path}")
    if not plugin_governance_path.exists():
        stale_reasons.append(f"plugin_governance_file_missing:{plugin_governance_path}")

    missing_rows: list[str] = []
    extra_rows: list[str] = []
    mapping_doc: dict[str, Any] = {}
    bundle_rows = _bundle_rows()
    bundle_target_map = _bundle_target_map()
    mode = ""
    baseline_missing_rows = -1
    reduction_plan_file = ""
    reduction_plan_status = "SKIPPED_NOT_REQUIRED"
    reduction_plan_target_zero = False
    reduction_plan_targets: list[int] = []

    if invariants_path.exists() and mapping_path.exists():
        inv_doc = _load_yaml(invariants_path)
        invariants = inv_doc.get("invariants") or {}
        parity_cfg = (invariants.get("bundle_mapping_parity") or {}) if isinstance(invariants, dict) else {}
        mode = str(parity_cfg.get("mode", "")).strip().lower() or "freeze"
        baseline_missing_rows = int(parity_cfg.get("baseline_missing_rows", -1))
        reduction_plan_file = str(parity_cfg.get("reduction_plan_file", "")).strip()

        mapping_doc = _load_yaml(mapping_path)
        mapping_rows = _mapping_rows(mapping_doc)
        missing_rows = sorted(x for x in mapping_rows if x not in bundle_rows)
        extra_rows = sorted(x for x in bundle_rows if x not in mapping_rows)

        if extra_rows:
            _append_violation(
                violations,
                field="bundle_rows_not_in_mapping",
                reason="bundle_row_without_mapping",
                rows=extra_rows,
            )

        if mode == "strict":
            if missing_rows:
                _append_violation(
                    violations,
                    field="mapping_rows_missing_in_bundle",
                    reason="bundle_mapping_parity_strict_violation",
                    mode=mode,
                    missing_rows=missing_rows,
                    missing_count=len(missing_rows),
                )
        elif mode == "freeze":
            if baseline_missing_rows < 0:
                _append_violation(
                    violations,
                    field="bundle_mapping_parity_baseline",
                    reason="freeze_mode_baseline_missing",
                    mode=mode,
                )
            elif len(missing_rows) > baseline_missing_rows:
                _append_violation(
                    violations,
                    field="mapping_rows_missing_in_bundle",
                    reason="bundle_mapping_gap_growth_in_freeze_mode",
                    mode=mode,
                    missing_count=len(missing_rows),
                    baseline_missing_rows=baseline_missing_rows,
                    missing_rows=missing_rows,
                )
            if baseline_missing_rows > 0:
                if not reduction_plan_file:
                    _append_violation(
                        violations,
                        field="bundle_mapping_parity_reduction_plan",
                        reason="reduction_plan_file_missing_for_freeze_debt",
                        baseline_missing_rows=baseline_missing_rows,
                    )
                else:
                    plan_path = (repo_root / reduction_plan_file).resolve()
                    if not plan_path.exists():
                        _append_violation(
                            violations,
                            field="bundle_mapping_parity_reduction_plan",
                            reason="reduction_plan_file_not_found",
                            reduction_plan_file=reduction_plan_file,
                        )
                    else:
                        plan_doc = _load_yaml(plan_path)
                        plan_baseline = int(plan_doc.get("baseline_missing_rows", -1))
                        milestones = _as_list(plan_doc.get("milestones"))
                        reduction_plan_targets = []
                        for row in milestones:
                            if not isinstance(row, dict):
                                continue
                            try:
                                target = int(row.get("target_max_missing_rows", -1))
                            except Exception:
                                continue
                            if target >= 0:
                                reduction_plan_targets.append(target)
                        reduction_plan_target_zero = any(t == 0 for t in reduction_plan_targets)
                        if plan_baseline != baseline_missing_rows:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_baseline_mismatch",
                                baseline_missing_rows=baseline_missing_rows,
                                plan_baseline_missing_rows=plan_baseline,
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not reduction_plan_targets:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_targets_missing",
                                reduction_plan_file=reduction_plan_file,
                            )
                        if reduction_plan_targets and min(reduction_plan_targets) >= baseline_missing_rows:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_no_strict_reduction_target",
                                baseline_missing_rows=baseline_missing_rows,
                                reduction_plan_targets=sorted(reduction_plan_targets),
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not reduction_plan_target_zero:
                            _append_violation(
                                violations,
                                field="bundle_mapping_parity_reduction_plan",
                                reason="reduction_plan_missing_zero_target",
                                reduction_plan_targets=sorted(reduction_plan_targets),
                                reduction_plan_file=reduction_plan_file,
                            )
                        if not any(v.get("field") == "bundle_mapping_parity_reduction_plan" for v in violations):
                            reduction_plan_status = "PASS_REQUIRED"
                        else:
                            reduction_plan_status = STATUS_FAIL_REQUIRED
            else:
                reduction_plan_status = "SKIPPED_NOT_REQUIRED"
        else:
            _append_violation(
                violations,
                field="bundle_mapping_parity_mode",
                reason="invalid_mode",
                mode=mode,
            )

    plugin_profile_count = 0
    plugin_wiring_violation_count = 0
    unique_egress_violation_count = 0
    bundle_entry_violation_count = 0
    prompt_binding_violation_count = 0
    registry_fail_close_plugin_ids: set[str] = set()
    governance_plugin_ids: set[str] = set()
    duplicate_governance_plugin_ids: set[str] = set()
    registry_source_files: set[str] = set()
    plugin_doc_parse_ok = False

    if plugin_governance_path.exists():
        plugin_doc = _load_yaml(plugin_governance_path)
        plugin_doc_parse_ok = bool(plugin_doc)
        if not plugin_doc_parse_ok:
            _append_violation(
                violations,
                field="plugin_governance_file",
                reason="plugin_governance_parse_failed",
                plugin_governance_file=str(plugin_governance_path),
            )
        else:
            # Unique egress invariants.
            unique_egress = plugin_doc.get("unique_egress")
            if isinstance(unique_egress, dict):
                egress_script = str(unique_egress.get("script", "")).strip()
                channel_id = str(unique_egress.get("channel_id", "")).strip()
                surfaces = _as_str_list(unique_egress.get("strict_surfaces"))
                for rel in surfaces:
                    ok_script, err_script = _surface_token_present(repo_root, rel, egress_script)
                    if err_script:
                        unique_egress_violation_count += 1
                        _append_violation(
                            violations,
                            field="unique_egress_surface",
                            reason=err_script,
                            surface=rel,
                            required_script=egress_script,
                        )
                        continue
                    if not ok_script:
                        unique_egress_violation_count += 1
                        _append_violation(
                            violations,
                            field="unique_egress_script",
                            reason="egress_script_missing_on_surface",
                            surface=rel,
                            required_script=egress_script,
                        )
                    if channel_id:
                        ok_channel, _ = _surface_token_present(repo_root, rel, channel_id)
                        if not ok_channel:
                            unique_egress_violation_count += 1
                            _append_violation(
                                violations,
                                field="unique_egress_channel",
                                reason="egress_channel_literal_missing_on_surface",
                                surface=rel,
                                required_channel_id=channel_id,
                            )
            else:
                _append_violation(
                    violations,
                    field="unique_egress",
                    reason="unique_egress_config_missing",
                )

            # Bundle entry invariants.
            bundle_entry = plugin_doc.get("bundle_entry")
            bundle_script = ""
            if isinstance(bundle_entry, dict):
                bundle_script = str(bundle_entry.get("script", "")).strip()
                surfaces = _as_str_list(bundle_entry.get("strict_surfaces"))
                for rel in surfaces:
                    ok_bundle, err_bundle = _surface_token_present(repo_root, rel, bundle_script)
                    if err_bundle:
                        bundle_entry_violation_count += 1
                        _append_violation(
                            violations,
                            field="bundle_entry_surface",
                            reason=err_bundle,
                            surface=rel,
                            required_script=bundle_script,
                        )
                        continue
                    if not ok_bundle:
                        bundle_entry_violation_count += 1
                        _append_violation(
                            violations,
                            field="bundle_entry_script",
                            reason="bundle_script_missing_on_surface",
                            surface=rel,
                            required_script=bundle_script,
                        )
            else:
                _append_violation(
                    violations,
                    field="bundle_entry",
                    reason="bundle_entry_config_missing",
                )

            # Plugin fail-close profile invariants.
            profiles = _as_list(plugin_doc.get("plugin_failclose_profiles"))
            registry_cache: dict[str, dict[str, Any]] = {}
            registry_source_files.update(_as_str_list(plugin_doc.get("plugin_registry_files")))
            if not registry_source_files:
                registry_source_files.add("identity/protocol/plugins/PLUGIN_REGISTRY.v1.6.2.yaml")

            for profile in profiles:
                if not isinstance(profile, dict):
                    continue
                registry_file = str(profile.get("registry_file", "")).strip()
                if registry_file:
                    registry_source_files.add(registry_file)

            for registry_file in sorted(registry_source_files):
                registry_path = (repo_root / registry_file).resolve()
                if not registry_path.exists() or not registry_path.is_file():
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry",
                        reason="registry_file_missing",
                        registry_file=registry_file,
                    )
                    continue
                cache_key = str(registry_path)
                if cache_key not in registry_cache:
                    registry_cache[cache_key] = _load_yaml(registry_path)
                registry_doc = registry_cache.get(cache_key) or {}
                plugins = _as_list(registry_doc.get("plugins"))
                for row in plugins:
                    if not isinstance(row, dict):
                        continue
                    reg_plugin_id = str(row.get("plugin_id", "")).strip()
                    reg_gate_mode = str(row.get("gate_mode", "")).strip().lower()
                    if reg_plugin_id and reg_gate_mode == "fail_close_strict":
                        registry_fail_close_plugin_ids.add(reg_plugin_id)

            for profile in profiles:
                if not isinstance(profile, dict):
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_failclose_profiles",
                        reason="profile_row_not_object",
                    )
                    continue
                plugin_profile_count += 1
                plugin_id = str(profile.get("plugin_id", "")).strip()
                requirement_key = str(profile.get("requirement_key", "")).strip()
                target_name = str(profile.get("target_name", "")).strip()
                registry_file = str(profile.get("registry_file", "")).strip()
                contract_file = str(profile.get("contract_file", "")).strip()
                validator_script = str(profile.get("validator_script", "")).strip()
                strict_surfaces = _as_str_list(profile.get("strict_surfaces"))
                required_gate_surfaces = set(_as_str_list(profile.get("required_gate_surfaces")))
                required_report_fields = set(_as_str_list(profile.get("required_report_fields")))
                if not plugin_id:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_failclose_profiles",
                        reason="plugin_id_missing",
                    )
                elif plugin_id in governance_plugin_ids:
                    duplicate_governance_plugin_ids.add(plugin_id)
                governance_plugin_ids.add(plugin_id)

                # Registry profile checks.
                if not registry_file:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_registry",
                        reason="registry_file_missing_on_profile",
                        plugin_id=plugin_id,
                    )
                else:
                    registry_path = (repo_root / registry_file).resolve()
                    cache_key = str(registry_path)
                    registry_doc = registry_cache.get(cache_key)
                    if registry_doc is None:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_registry",
                            reason="registry_file_missing",
                            plugin_id=plugin_id,
                            registry_file=registry_file,
                        )
                        registry_doc = {}
                    plugins = _as_list(registry_doc.get("plugins"))
                    plugin_rows = [
                        row
                        for row in plugins
                        if isinstance(row, dict) and str(row.get("plugin_id", "")).strip() == plugin_id
                    ]
                    if not plugin_rows:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="plugin_registry",
                            reason="plugin_id_missing_in_registry",
                            plugin_id=plugin_id,
                            registry_file=registry_file,
                        )
                    else:
                        reg_row = plugin_rows[0]
                        registry_contract = str(reg_row.get("contract_file", "")).strip()
                        registry_validator = str(reg_row.get("validator_script", "")).strip()
                        registry_requirement = str(reg_row.get("requirement_key", "")).strip()
                        registry_target = str(reg_row.get("bundle_target_name", "")).strip()
                        registry_mode = str(reg_row.get("gate_mode", "")).strip().lower()
                        registry_status = str(reg_row.get("status", "")).strip().lower()
                        if contract_file and registry_contract != contract_file:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_contract_mismatch",
                                plugin_id=plugin_id,
                                expected_contract_file=contract_file,
                                observed_contract_file=registry_contract,
                            )
                        if validator_script and registry_validator != validator_script:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_validator_mismatch",
                                plugin_id=plugin_id,
                                expected_validator_script=validator_script,
                                observed_validator_script=registry_validator,
                            )
                        if registry_requirement and registry_requirement != requirement_key:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_requirement_key_mismatch",
                                plugin_id=plugin_id,
                                expected_requirement_key=requirement_key,
                                observed_requirement_key=registry_requirement,
                            )
                        if registry_target and registry_target != target_name:
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_bundle_target_mismatch",
                                plugin_id=plugin_id,
                                expected_target_name=target_name,
                                observed_target_name=registry_target,
                            )
                        if registry_mode and registry_mode != "fail_close_strict":
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_gate_mode_not_fail_close_strict",
                                plugin_id=plugin_id,
                                expected_gate_mode="fail_close_strict",
                                observed_gate_mode=registry_mode,
                            )
                        if registry_mode == "fail_close_strict" and registry_status != "active":
                            plugin_wiring_violation_count += 1
                            _append_violation(
                                violations,
                                field="plugin_registry",
                                reason="registry_fail_close_plugin_status_not_active",
                                plugin_id=plugin_id,
                                expected_status="active",
                                observed_status=registry_status or "MISSING",
                            )

                # Contract file canonical path check.
                contract_path = (repo_root / contract_file).resolve() if contract_file else None
                if not contract_file or contract_path is None or not contract_path.exists():
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="plugin_contract_file",
                        reason="contract_file_missing",
                        plugin_id=plugin_id,
                        contract_file=contract_file,
                    )

                # Mapping row checks.
                mapping_row = mapping_doc.get(requirement_key) if isinstance(mapping_doc, dict) else None
                if not isinstance(mapping_row, dict):
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="mapping_row",
                        reason="mapping_row_missing_for_plugin_requirement",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                    )
                else:
                    mapping_validators = _mapping_validator_scripts(mapping_row)
                    if validator_script and validator_script not in mapping_validators:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_validator_missing",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            expected_validator_script=validator_script,
                            observed_validator_scripts=sorted(mapping_validators),
                        )

                    mapping_surfaces = set(_as_str_list(mapping_row.get("gate_surfaces")))
                    missing_surfaces = sorted(required_gate_surfaces - mapping_surfaces)
                    if missing_surfaces:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_gate_surfaces_incomplete",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            missing_gate_surfaces=missing_surfaces,
                        )

                    mapping_fields = set(_as_str_list(mapping_row.get("report_field_refs")))
                    missing_fields = sorted(required_report_fields - mapping_fields)
                    if missing_fields:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="mapping_row",
                            reason="mapping_report_field_refs_incomplete",
                            plugin_id=plugin_id,
                            requirement_key=requirement_key,
                            missing_report_field_refs=missing_fields,
                        )

                # Bundle requirement/target checks.
                if requirement_key and requirement_key not in bundle_rows:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="bundle_runner",
                        reason="bundle_requirement_missing",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                    )
                observed_target = bundle_target_map.get(requirement_key, "")
                if requirement_key and target_name and observed_target != target_name:
                    plugin_wiring_violation_count += 1
                    _append_violation(
                        violations,
                        field="bundle_runner",
                        reason="bundle_target_mapping_mismatch",
                        plugin_id=plugin_id,
                        requirement_key=requirement_key,
                        expected_target_name=target_name,
                        observed_target_name=observed_target,
                    )

                # Direct validator bypass checks on strict surfaces.
                for rel in strict_surfaces:
                    path = (repo_root / rel).resolve()
                    if not path.exists():
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="strict_surface_missing",
                            plugin_id=plugin_id,
                            surface=rel,
                        )
                        continue
                    text = _read_text(path)
                    if validator_script and validator_script in text:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="direct_validator_reference_detected",
                            plugin_id=plugin_id,
                            surface=rel,
                            validator_script=validator_script,
                        )
                    if bundle_script and bundle_script not in text:
                        plugin_wiring_violation_count += 1
                        _append_violation(
                            violations,
                            field="strict_surface",
                            reason="bundle_runner_reference_missing",
                            plugin_id=plugin_id,
                            surface=rel,
                            required_script=bundle_script,
                        )

            if duplicate_governance_plugin_ids:
                plugin_wiring_violation_count += len(duplicate_governance_plugin_ids)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="duplicate_plugin_profile_detected",
                    duplicate_plugin_ids=sorted(duplicate_governance_plugin_ids),
                )

            missing_governance_profiles = sorted(registry_fail_close_plugin_ids - governance_plugin_ids)
            if missing_governance_profiles:
                plugin_wiring_violation_count += len(missing_governance_profiles)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="registry_fail_close_plugin_missing_governance_profile",
                    missing_plugin_ids=missing_governance_profiles,
                    missing_count=len(missing_governance_profiles),
                )

            orphan_governance_profiles = sorted(governance_plugin_ids - registry_fail_close_plugin_ids)
            if orphan_governance_profiles:
                plugin_wiring_violation_count += len(orphan_governance_profiles)
                _append_violation(
                    violations,
                    field="plugin_failclose_profiles",
                    reason="governance_profile_missing_registry_fail_close_plugin",
                    orphan_plugin_ids=orphan_governance_profiles,
                    orphan_count=len(orphan_governance_profiles),
                )

            # Prompt fail-close binding invariants.
            prompt_binding = plugin_doc.get("prompt_failclose_binding")
            if isinstance(prompt_binding, dict):
                script_rel = str(prompt_binding.get("enforcement_script", "")).strip()
                script_path = (repo_root / script_rel).resolve()
                if not script_rel or not script_path.exists():
                    prompt_binding_violation_count += 1
                    _append_violation(
                        violations,
                        field="prompt_failclose_binding",
                        reason="enforcement_script_missing",
                        enforcement_script=script_rel,
                    )
                else:
                    text = _read_text(script_path)
                    for token in _as_str_list(prompt_binding.get("required_contract_keys")):
                        if token not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="required_contract_key_not_wired",
                                enforcement_script=script_rel,
                                missing_contract_key=token,
                            )
                    for token in _as_str_list(prompt_binding.get("required_result_fields")):
                        if token not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="required_result_field_not_emitted",
                                enforcement_script=script_rel,
                                missing_result_field=token,
                            )
                    strict_guard = prompt_binding.get("strict_failure_guard")
                    if isinstance(strict_guard, dict):
                        status_field = str(strict_guard.get("status_field", "")).strip()
                        required_status = str(strict_guard.get("required_status", "")).strip()
                        if status_field and status_field not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="strict_failure_status_field_missing",
                                enforcement_script=script_rel,
                                status_field=status_field,
                            )
                        if required_status and required_status not in text:
                            prompt_binding_violation_count += 1
                            _append_violation(
                                violations,
                                field="prompt_failclose_binding",
                                reason="strict_failure_required_status_missing",
                                enforcement_script=script_rel,
                                required_status=required_status,
                            )
            else:
                _append_violation(
                    violations,
                    field="prompt_failclose_binding",
                    reason="prompt_failclose_binding_config_missing",
                )

    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_INVARIANT
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "control_plane_invariants_status": status,
        "error_code": error_code,
        "invariants_file": str(invariants_path),
        "contract_mapping": str(mapping_path),
        "plugin_governance_file": str(plugin_governance_path),
        "bundle_mapping_parity_mode": mode,
        "bundle_mapping_parity_baseline_missing_rows": baseline_missing_rows,
        "bundle_mapping_parity_reduction_plan_file": reduction_plan_file,
        "bundle_mapping_parity_reduction_plan_status": reduction_plan_status,
        "bundle_mapping_parity_reduction_plan_targets": sorted(reduction_plan_targets),
        "bundle_mapping_parity_reduction_plan_zero_target": reduction_plan_target_zero,
        "mapping_rows_missing_in_bundle_count": len(missing_rows),
        "mapping_rows_missing_in_bundle": missing_rows,
        "bundle_rows_not_in_mapping_count": len(extra_rows),
        "bundle_rows_not_in_mapping": extra_rows,
        "plugin_profile_count": plugin_profile_count,
        "plugin_wiring_violation_count": plugin_wiring_violation_count,
        "registry_fail_close_plugin_count": len(registry_fail_close_plugin_ids),
        "registry_fail_close_plugin_ids": sorted(registry_fail_close_plugin_ids),
        "governance_profile_plugin_count": len(governance_plugin_ids),
        "governance_profile_plugin_ids": sorted(governance_plugin_ids),
        "duplicate_governance_profile_count": len(duplicate_governance_plugin_ids),
        "duplicate_governance_plugin_ids": sorted(duplicate_governance_plugin_ids),
        "unique_egress_violation_count": unique_egress_violation_count,
        "bundle_entry_violation_count": bundle_entry_violation_count,
        "prompt_binding_violation_count": prompt_binding_violation_count,
        "plugin_governance_parse_ok": plugin_doc_parse_ok,
        "bundle_target_map_size": len(bundle_target_map),
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-INVARIANTS] status={status} "
            f"mode={mode or '-'} "
            f"mapping_missing={len(missing_rows)} "
            f"extra_bundle_rows={len(extra_rows)} "
            f"plugin_profiles={plugin_profile_count} "
            f"violations={len(violations)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
