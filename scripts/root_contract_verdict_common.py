#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable, Mapping


def _norm_str(value: Any) -> str:
    return str(value or "").strip()


def _row_get(row: Any, key: str, default: str = "") -> str:
    if isinstance(row, Mapping):
        return _norm_str(row.get(key, default))
    return _norm_str(getattr(row, key, default))


def collect_violation_markers(
    violations: Iterable[Any],
) -> list[str]:
    return sorted({_row_get(row, "marker") for row in violations if _row_get(row, "marker")})


def extend_violation_reason_projection(
    stale_reasons: list[str],
    *,
    reason_prefix: str,
    violations: Iterable[Any],
    field_name: str = "field",
    fallback_field: str | None = None,
    fallback_value: str = "",
    reason_key: str = "reason",
) -> None:
    for row in violations:
        field_value = _row_get(row, field_name)
        if not field_value and fallback_field:
            field_value = _row_get(row, fallback_field)
        if not field_value:
            field_value = _norm_str(fallback_value)
        reason_value = _row_get(row, reason_key)
        stale_reasons.append(f"{reason_prefix}:{field_value}:{reason_value}")


def project_root_contract_support_verdict(
    *,
    stale_reasons: list[str],
    error_code: str,
    structure_violations: Iterable[Any],
    support_violations: Iterable[Any],
    structure_error_code: str,
    support_error_code: str,
    support_reason_prefix: str = "",
    structure_reason_prefix: str = "structure_violation",
    structure_field_name: str = "field",
    support_field_name: str = "field",
    support_fallback_field: str = "contract_file",
    support_fallback_value: str = "",
    project_structure_reasons: bool = True,
    project_support_reasons: bool = True,
    include_summary_markers: bool = False,
    pass_status: str = "PASS_REQUIRED",
    fail_status: str = "FAIL_REQUIRED",
) -> dict[str, Any]:
    structure_rows = tuple(structure_violations)
    support_rows = tuple(support_violations)
    resolved_error_code = _norm_str(error_code)

    if not resolved_error_code and structure_rows:
        resolved_error_code = _norm_str(structure_error_code)
    if not resolved_error_code and support_rows:
        resolved_error_code = _norm_str(support_error_code)

    if project_structure_reasons:
        extend_violation_reason_projection(
            stale_reasons,
            reason_prefix=structure_reason_prefix,
            violations=structure_rows,
            field_name=structure_field_name,
        )
    if project_support_reasons and support_reason_prefix:
        extend_violation_reason_projection(
            stale_reasons,
            reason_prefix=support_reason_prefix,
            violations=support_rows,
            field_name=support_field_name,
            fallback_field=support_fallback_field,
            fallback_value=support_fallback_value,
        )

    has_failure = bool(stale_reasons) or bool(structure_rows) or bool(support_rows)
    status = fail_status if has_failure else pass_status
    payload_error_code = (
        ""
        if status == pass_status
        else _norm_str(resolved_error_code) or _norm_str(support_error_code) or _norm_str(structure_error_code)
    )

    return {
        "status": status,
        "rc": 0 if status == pass_status else 1,
        "error_code": payload_error_code,
        "resolved_error_code": resolved_error_code,
        "summary_markers": collect_violation_markers(support_rows) if include_summary_markers else [],
    }
