#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def project_row_family(
    *,
    family_id: str,
    member_id_key: str,
    actual_rows,
    expected_rows: dict[str, dict[str, Any]],
    id_attr: str,
    pass_status: str = STATUS_PASS_REQUIRED,
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> dict[str, Any]:
    actual_ids = sorted(str(getattr(row, id_attr)) for row in actual_rows)
    expected_ids = sorted(str(row_id) for row_id in expected_rows)
    missing_ids = sorted(set(expected_ids) - set(actual_ids))
    unexpected_ids = sorted(set(actual_ids) - set(expected_ids))
    coverage_status = fail_status if len(actual_rows) != len(expected_ids) else pass_status
    identity_projection_status = fail_status if missing_ids or unexpected_ids else pass_status
    return {
        "family_id": family_id,
        "member_id_key": member_id_key,
        "expected_count": len(expected_ids),
        "actual_count": len(actual_rows),
        "expected_ids": expected_ids,
        "actual_ids": actual_ids,
        "missing_ids": missing_ids,
        "unexpected_ids": unexpected_ids,
        "coverage_status": coverage_status,
        "identity_projection_status": identity_projection_status,
    }


def aggregate_row_family_status(
    row_family_projection_rows: list[dict[str, Any]],
    *,
    status_key: str,
    pass_status: str = STATUS_PASS_REQUIRED,
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> str:
    return (
        fail_status
        if any(row.get(status_key) == fail_status for row in row_family_projection_rows)
        else pass_status
    )
