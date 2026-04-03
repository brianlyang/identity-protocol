#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


@dataclass(frozen=True)
class NamedRowFamilyStatusProjectionSpec:
    payload_key: str
    family_id: str
    status_key: str


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


def project_row_families(
    *,
    families: Iterable[dict[str, Any]],
    pass_status: str = STATUS_PASS_REQUIRED,
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> list[dict[str, Any]]:
    return [
        project_row_family(
            pass_status=pass_status,
            fail_status=fail_status,
            **family,
        )
        for family in families
    ]


def index_row_family_projection_rows(
    row_family_projection_rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        str(row["family_id"]): row
        for row in row_family_projection_rows
    }


def project_named_row_family_statuses(
    *,
    row_family_projection_rows_by_id: dict[str, dict[str, Any]],
    specs: Iterable[NamedRowFamilyStatusProjectionSpec],
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> dict[str, str]:
    return {
        spec.payload_key: str(
            row_family_projection_rows_by_id.get(spec.family_id, {}).get(spec.status_key)
            or fail_status
        )
        for spec in specs
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


def project_row_family_summary(
    *,
    prefix: str,
    row_family_projection_rows: list[dict[str, Any]],
    pass_status: str = STATUS_PASS_REQUIRED,
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> dict[str, Any]:
    return {
        f"{prefix}_row_family_count": len(row_family_projection_rows),
        f"{prefix}_row_coverage_status": aggregate_row_family_status(
            row_family_projection_rows,
            status_key="coverage_status",
            pass_status=pass_status,
            fail_status=fail_status,
        ),
        f"{prefix}_row_identity_projection_status": aggregate_row_family_status(
            row_family_projection_rows,
            status_key="identity_projection_status",
            pass_status=pass_status,
            fail_status=fail_status,
        ),
    }


def project_root_contract_support_projection(
    *,
    prefix: str,
    row_family_projection_rows: list[dict[str, Any]],
    anchor_checks: Iterable[Any] | None = None,
    anchor_violations: Iterable[dict[str, Any]] | None = None,
    pass_status: str = STATUS_PASS_REQUIRED,
    fail_status: str = STATUS_FAIL_REQUIRED,
) -> dict[str, Any]:
    payload = project_row_family_summary(
        prefix=prefix,
        row_family_projection_rows=row_family_projection_rows,
        pass_status=pass_status,
        fail_status=fail_status,
    )
    if anchor_checks is not None and anchor_violations is not None:
        anchor_checks_tuple = tuple(anchor_checks)
        anchor_violation_rows = tuple(anchor_violations)
        payload.update(
            {
                "root_doc_anchor_check_count": len(anchor_checks_tuple),
                "root_doc_anchor_status": (
                    pass_status if not anchor_violation_rows else fail_status
                ),
            }
        )
    return payload
