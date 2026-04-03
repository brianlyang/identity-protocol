#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import collect_requirement_rows
from projection_profile_exclusion_scope_common import (
    PROJECTION_PROFILE_EXCLUSION_SCOPE_CLASS,
    PROJECTION_PROFILE_EXCLUSION_SCOPE_MODE,
    PROJECTION_PROFILE_EXCLUSION_SCOPE_REASON,
    build_projection_profile_exclusion_payload,
)
from required_gate_report_authority_common import REQUIRED_GATE_REPORT_AUTHORITY_FIELDS
from registry_alias_control_plane_common import resolve_alias_entry_path, resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
DEFAULT_CONTRACT_BINDING_ENTRY = "identity/protocol/mappings/contract-binding.current.yaml"


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def _extract_report_fields(
    *,
    result_row: dict[str, Any],
    payload: dict[str, Any],
    report_field_refs: list[str],
) -> tuple[dict[str, Any], list[str]]:
    out: dict[str, Any] = {}
    missing: list[str] = []
    normalized_status_field = str(result_row.get("status_field", "") or "").strip()
    for field in report_field_refs:
        if field in result_row:
            out[field] = result_row.get(field)
            continue
        if field in payload:
            out[field] = payload.get(field)
            continue
        if field == normalized_status_field and field:
            out[field] = result_row.get("status")
            continue
        missing.append(field)
    return out, missing


def build_required_gate_bundle_target_projection(
    *,
    repo_root: Path,
    bundle_payload: dict[str, Any],
    contract_mapping: str = DEFAULT_CONTRACT_BINDING_ENTRY,
) -> dict[str, Any]:
    report_authority_projection = {
        field: str(bundle_payload.get(field, "") or "").strip()
        for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS
    }
    projection: dict[str, Any] = {
        "projection_status": STATUS_PASS_REQUIRED,
        "error_code": str(bundle_payload.get("error_code", "") or "").strip(),
        "bundle_status": str(bundle_payload.get("bundle_status", "") or "").strip(),
        "bundle_contract_id": str(bundle_payload.get("bundle_contract_id", "") or "").strip(),
        "bundle_key": str(bundle_payload.get("bundle_key", "") or "").strip(),
        "surface_label": str(bundle_payload.get("surface_label", "") or "").strip(),
        "identity_id": str(bundle_payload.get("identity_id", "") or "").strip(),
        "actor_id": str(bundle_payload.get("actor_id", "") or "").strip(),
        "resolved_work_layer": str(bundle_payload.get("resolved_work_layer", "") or "").strip(),
        "resolved_source_layer": str(bundle_payload.get("resolved_source_layer", "") or "").strip(),
        "lock_state": str(bundle_payload.get("lock_state", "") or "").strip(),
        "run_id_binding": str(bundle_payload.get("run_id_binding", "") or "").strip(),
        **report_authority_projection,
        "contract_mapping_entry": "",
        "contract_mapping": "",
        "contract_mapping_active_file": "",
        "contract_mapping_alias_error": "",
        "total_targets": 0,
        "required_target_count": 0,
        "failed_required_target_count": 0,
        "target_status_counts": {},
        "failed_target_names": [],
        "missing_mapping_requirements": [],
        "rows_without_projected_report_fields": [],
        "stale_reasons": [],
        "targets": [],
    }

    result_rows = bundle_payload.get("results")
    if not isinstance(result_rows, list):
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"] = ["bundle_results_missing_or_invalid"]
        return projection

    mapping_entry_path = resolve_alias_entry_path(repo_root, contract_mapping)
    mapping_path, mapping_active_file, mapping_alias_error = resolve_current_yaml_alias(repo_root, contract_mapping)
    projection["contract_mapping_entry"] = str(mapping_entry_path)
    projection["contract_mapping"] = str(mapping_path)
    projection["contract_mapping_active_file"] = str(mapping_active_file or "")
    projection["contract_mapping_alias_error"] = str(mapping_alias_error or "")

    if mapping_alias_error:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"] = [f"contract_mapping_alias_error:{mapping_alias_error}"]
        return projection

    mapping_doc = _load_yaml_dict(mapping_path)
    if not mapping_doc:
        projection["projection_status"] = STATUS_FAIL_REQUIRED
        projection["stale_reasons"] = [f"contract_mapping_parse_failed:{mapping_path}"]
        return projection

    mapping_rows = collect_requirement_rows(mapping_doc)
    stale_reasons: list[str] = []
    target_status_counts: dict[str, int] = {}
    failed_target_names: list[str] = []
    missing_mapping_requirements: list[str] = []
    rows_without_projected_report_fields: list[str] = []
    targets: list[dict[str, Any]] = []

    for raw_row in result_rows:
        if not isinstance(raw_row, dict):
            continue
        projection["total_targets"] += 1

        requirement_key = str(raw_row.get("requirement_key", "") or "").strip()
        target_name = str(raw_row.get("target_name", "") or requirement_key).strip()
        row_status = str(raw_row.get("status", "") or "").strip().upper()
        required_contract = bool(raw_row.get("required_contract", False))
        if required_contract:
            projection["required_target_count"] += 1
        if required_contract and row_status == STATUS_FAIL_REQUIRED:
            projection["failed_required_target_count"] += 1
            if target_name:
                failed_target_names.append(target_name)

        if row_status:
            target_status_counts[row_status] = int(target_status_counts.get(row_status, 0)) + 1

        mapping_row = mapping_rows.get(requirement_key, {})
        if not mapping_row:
            missing_key = requirement_key or target_name
            if missing_key:
                missing_mapping_requirements.append(missing_key)

        payload = raw_row.get("payload") if isinstance(raw_row.get("payload"), dict) else {}
        report_field_refs = _as_str_list(mapping_row.get("report_field_refs")) if isinstance(mapping_row, dict) else []
        report_fields, missing_report_fields = _extract_report_fields(
            result_row=raw_row,
            payload=payload,
            report_field_refs=report_field_refs,
        )

        row_projection_status = STATUS_PASS_REQUIRED
        if report_field_refs and not report_fields:
            row_projection_status = STATUS_FAIL_REQUIRED
            if requirement_key or target_name:
                rows_without_projected_report_fields.append(requirement_key or target_name)

        targets.append(
            {
                "requirement_key": requirement_key,
                "requirement_id": str(mapping_row.get("requirement_id", "") or "").strip()
                if isinstance(mapping_row, dict)
                else "",
                "kernel_contract_id": str(mapping_row.get("kernel_contract_id", "") or "").strip()
                if isinstance(mapping_row, dict)
                else "",
                "kernel_source_path": str(mapping_row.get("kernel_source_path", "") or "").strip()
                if isinstance(mapping_row, dict)
                else "",
                "target_name": target_name,
                "status": row_status,
                "status_field": str(raw_row.get("status_field", "") or "").strip(),
                "error_code": str(raw_row.get("error_code", "") or "").strip(),
                "required_contract": required_contract,
                "validator": str(raw_row.get("validator", "") or "").strip(),
                "evidence_ref": str(raw_row.get("evidence_ref", "") or "").strip(),
                "stale_reasons": list(raw_row.get("stale_reasons") or []),
                "report_field_refs": report_field_refs,
                "report_fields": report_fields,
                "missing_report_fields": missing_report_fields,
                "projection_status": row_projection_status,
            }
        )

    if missing_mapping_requirements:
        stale_reasons.append(
            "missing_contract_mapping_requirements:" + ",".join(sorted(dict.fromkeys(missing_mapping_requirements)))
        )
    if rows_without_projected_report_fields:
        stale_reasons.append(
            "rows_without_projected_report_fields:" + ",".join(sorted(dict.fromkeys(rows_without_projected_report_fields)))
        )

    if stale_reasons:
        projection["projection_status"] = STATUS_FAIL_REQUIRED

    projection["target_status_counts"] = dict(sorted(target_status_counts.items()))
    projection["failed_target_names"] = sorted(dict.fromkeys(failed_target_names))
    projection["missing_mapping_requirements"] = sorted(dict.fromkeys(missing_mapping_requirements))
    projection["rows_without_projected_report_fields"] = sorted(dict.fromkeys(rows_without_projected_report_fields))
    projection["stale_reasons"] = stale_reasons
    projection["targets"] = targets
    return projection


def build_projection_profile_excluded_required_gate_bundle_target_projection(
    *,
    profile_id: str,
    execution_mode: str,
    description: str,
    excluded_area: str,
    owner_surface: str,
) -> dict[str, Any]:
    projection = {
        "projection_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "bundle_status": STATUS_SKIPPED_NOT_REQUIRED,
        "bundle_contract_id": "",
        "bundle_key": "",
        "surface_label": str(owner_surface or "").strip(),
        "identity_id": "",
        "actor_id": "",
        "resolved_work_layer": "",
        "resolved_source_layer": "",
        "lock_state": "",
        "run_id_binding": "",
        **{field: "" for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS},
        "contract_mapping_entry": "",
        "contract_mapping": "",
        "contract_mapping_active_file": "",
        "contract_mapping_alias_error": "",
        "total_targets": 0,
        "required_target_count": 0,
        "failed_required_target_count": 0,
        "target_status_counts": {},
        "failed_target_names": [],
        "missing_mapping_requirements": [],
        "rows_without_projected_report_fields": [],
        "targets": [],
        "scope_class": PROJECTION_PROFILE_EXCLUSION_SCOPE_CLASS,
        "scope_reason": PROJECTION_PROFILE_EXCLUSION_SCOPE_REASON,
        "scope_mode": PROJECTION_PROFILE_EXCLUSION_SCOPE_MODE,
    }
    projection.update(
        build_projection_profile_exclusion_payload(
            profile_id=profile_id,
            execution_mode=execution_mode,
            description=description,
            excluded_area=excluded_area,
            owner_surface=owner_surface,
        )
    )
    return projection


def required_gate_bundle_target_projection_is_scope_excluded(
    projection: dict[str, Any] | None,
) -> bool:
    if not isinstance(projection, dict):
        return False
    projection_status = str(projection.get("projection_status", "") or "").strip().upper()
    scope_class = str(projection.get("scope_class", "") or "").strip()
    return projection_status == STATUS_SKIPPED_NOT_REQUIRED and bool(scope_class)
