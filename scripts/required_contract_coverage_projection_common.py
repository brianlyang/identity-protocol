#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any


STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_FAIL_OPTIONAL = "FAIL_OPTIONAL"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_status(value: Any) -> str:
    return _clean_text(value).upper()


def _clean_text_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        token = _clean_text(value)
        if token and token not in result:
            result.append(token)
    return result


def _parse_json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    text = _clean_text(value)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_failure_detail(row: dict[str, Any]) -> dict[str, Any]:
    tail_payload = _parse_json_dict(row.get("validator_tail"))
    stale_reasons = _clean_text_list(tail_payload.get("stale_reasons"))
    detail = {
        "name": _clean_text(row.get("name")),
        "contract_key": _clean_text(row.get("contract_key")),
        "validator": _clean_text(row.get("validator")),
        "validator_status": _normalize_status(row.get("validator_status")),
        "required_contract": bool(row.get("required_contract", False)),
        "reason_code": _clean_text(row.get("reason_code")),
        "error_code": _clean_text(tail_payload.get("error_code")) or _clean_text(row.get("reason_code")),
        "evidence_ref": _clean_text(row.get("evidence_ref")) or _clean_text(tail_payload.get("evidence_ref")),
        "stale_reasons": stale_reasons,
    }
    if stale_reasons:
        detail["freshness_sensitive"] = True
    return detail


def build_required_contract_coverage_projection(
    payload: dict[str, Any],
    *,
    detail_limit: int = 8,
) -> dict[str, Any]:
    rows = payload.get("contracts") or []
    if not isinstance(rows, list):
        rows = []

    failed_required_contracts: list[str] = []
    failed_optional_contracts: list[str] = []
    failed_required_contract_details: list[dict[str, Any]] = []
    failed_optional_contract_details: list[dict[str, Any]] = []
    failed_required_contracts_with_stale_reasons: list[str] = []
    failed_optional_contracts_with_stale_reasons: list[str] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        status = _normalize_status(row.get("validator_status"))
        if status not in {STATUS_FAIL_REQUIRED, STATUS_FAIL_OPTIONAL}:
            continue
        detail = _build_failure_detail(row)
        name = _clean_text(detail.get("name"))
        if not name:
            continue
        is_required = bool(row.get("required_contract", False)) or status == STATUS_FAIL_REQUIRED
        if is_required:
            if name not in failed_required_contracts:
                failed_required_contracts.append(name)
            if len(failed_required_contract_details) < max(detail_limit, 0):
                failed_required_contract_details.append(detail)
            if detail.get("stale_reasons") and name not in failed_required_contracts_with_stale_reasons:
                failed_required_contracts_with_stale_reasons.append(name)
            continue
        if name not in failed_optional_contracts:
            failed_optional_contracts.append(name)
        if len(failed_optional_contract_details) < max(detail_limit, 0):
            failed_optional_contract_details.append(detail)
        if detail.get("stale_reasons") and name not in failed_optional_contracts_with_stale_reasons:
            failed_optional_contracts_with_stale_reasons.append(name)

    return {
        "failed_required_contracts": failed_required_contracts,
        "failed_optional_contracts": failed_optional_contracts,
        "failed_required_contract_details": failed_required_contract_details,
        "failed_optional_contract_details": failed_optional_contract_details,
        "failed_required_contracts_with_stale_reasons": failed_required_contracts_with_stale_reasons,
        "failed_optional_contracts_with_stale_reasons": failed_optional_contracts_with_stale_reasons,
    }
