#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable


def contiguous_orders(values: Iterable[int]) -> bool:
    ordered = list(values)
    return ordered == list(range(1, len(ordered) + 1))


def _resolve_support_violations(
    *,
    support_violations: list[dict[str, Any]] | None,
    aliases: dict[str, Any],
) -> list[dict[str, Any]]:
    alias_items = [
        (key, value)
        for key, value in aliases.items()
        if key.endswith("_violations")
    ]
    if support_violations is not None and alias_items:
        raise TypeError("validate_contract_rows requires either support_violations or a single *_violations alias, not both")
    if support_violations is not None:
        return support_violations
    if not alias_items:
        raise TypeError("validate_contract_rows requires a support_violations list or a single *_violations alias")
    if len(alias_items) != 1:
        raise TypeError("validate_contract_rows received multiple *_violations aliases")
    alias_name, alias_value = alias_items[0]
    if not isinstance(alias_value, list):
        raise TypeError(f"validate_contract_rows expected {alias_name} to be a list")
    return alias_value


def validate_contract_rows(
    *,
    actual_rows: Iterable[Any],
    expected_rows: dict[str, dict[str, Any]],
    structure_violations: list[dict[str, Any]],
    support_violations: list[dict[str, Any]] | None = None,
    field_name: str,
    id_attr: str,
    compare_fields: tuple[str, ...],
    duplicate_reason: str | None = None,
    non_contiguous_reason: str | None = None,
    missing_reason: str = "missing_expected_rows",
    extra_reason: str = "extra_rows",
    missing_ids_key: str = "row_ids",
    extra_ids_key: str = "row_ids",
    violation_id_key: str = "row_id",
    order_reason: str = "order_mismatch",
    **kwargs: Any,
) -> None:
    support_violations = _resolve_support_violations(
        support_violations=support_violations,
        aliases=kwargs,
    )

    actual_rows = tuple(actual_rows)
    actual_map = {getattr(row, id_attr): row for row in actual_rows}
    orders = [int(getattr(row, "order")) for row in actual_rows]
    duplicate_reason = duplicate_reason or f"duplicate_{id_attr}"
    non_contiguous_reason = non_contiguous_reason or f"{field_name}_order_non_contiguous"

    if len(actual_map) != len(actual_rows):
        structure_violations.append({"field": field_name, "reason": duplicate_reason})
    if len(set(orders)) != len(orders) or not contiguous_orders(sorted(orders)):
        structure_violations.append({"field": field_name, "reason": non_contiguous_reason})

    missing_ids = sorted(set(expected_rows) - set(actual_map))
    extra_ids = sorted(set(actual_map) - set(expected_rows))
    if missing_ids:
        structure_violations.append(
            {
                "field": field_name,
                "reason": missing_reason,
                missing_ids_key: missing_ids,
            }
        )
    if extra_ids:
        structure_violations.append(
            {
                "field": field_name,
                "reason": extra_reason,
                extra_ids_key: extra_ids,
            }
        )

    for row_id, expected in expected_rows.items():
        row = actual_map.get(row_id)
        if row is None:
            continue
        if row.order != expected["order"]:
            support_violations.append(
                {
                    "field": field_name,
                    violation_id_key: row_id,
                    "reason": order_reason,
                    "expected": expected["order"],
                    "actual": row.order,
                }
            )
        for compare_field in compare_fields:
            actual_value = getattr(row, compare_field)
            expected_value = expected[compare_field]
            if actual_value != expected_value:
                support_violations.append(
                    {
                        "field": field_name,
                        violation_id_key: row_id,
                        "reason": f"{compare_field}_mismatch",
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )
