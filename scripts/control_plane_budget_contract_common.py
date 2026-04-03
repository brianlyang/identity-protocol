#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable


BUDGET_SCALAR_FALLBACK_DELTAS: dict[str, int] = {
    "validator_scripts": 3,
    "error_codes": 6,
    "error_code_families": 6,
    "mapping_rows_missing_in_bundle": 1,
}
EXPECTED_BUDGET_METRIC_KEYS: tuple[str, ...] = tuple((*BUDGET_SCALAR_FALLBACK_DELTAS.keys(), "direct_validate_calls"))


def _sorted_unique_strings(values: Iterable[Any]) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})


def _mapping_keys(node: Any) -> list[str]:
    if isinstance(node, dict):
        return _sorted_unique_strings(node.keys())
    return []


def build_budget_topology_summary(
    *,
    budgets: Any,
    convergence_guard: Any,
    strict_surfaces: Iterable[Any],
) -> dict[str, Any]:
    budgets_map = budgets if isinstance(budgets, dict) else {}
    convergence_guard_map = convergence_guard if isinstance(convergence_guard, dict) else {}
    ceilings_map = convergence_guard_map.get("ceilings") if isinstance(convergence_guard_map.get("ceilings"), dict) else {}
    direct_budget_map = budgets_map.get("direct_validate_calls") if isinstance(budgets_map.get("direct_validate_calls"), dict) else {}
    direct_ceiling_map = (
        ceilings_map.get("direct_validate_calls") if isinstance(ceilings_map.get("direct_validate_calls"), dict) else {}
    )
    expected_surface_keys = _sorted_unique_strings(strict_surfaces)
    expected_metric_keys = list(EXPECTED_BUDGET_METRIC_KEYS)
    return {
        "budget_metric_keys": _mapping_keys(budgets_map),
        "expected_budget_metric_keys": expected_metric_keys,
        "budget_direct_surface_keys": _mapping_keys(direct_budget_map),
        "expected_direct_surface_keys": expected_surface_keys,
        "convergence_ceiling_keys": _mapping_keys(ceilings_map),
        "expected_convergence_ceiling_keys": expected_metric_keys,
        "convergence_direct_surface_keys": _mapping_keys(direct_ceiling_map),
        "expected_convergence_direct_surface_keys": expected_surface_keys,
    }


def build_budget_topology_violations(
    *,
    budgets: Any,
    convergence_guard: Any,
    strict_surfaces: Iterable[Any],
) -> list[dict[str, Any]]:
    summary = build_budget_topology_summary(
        budgets=budgets,
        convergence_guard=convergence_guard,
        strict_surfaces=strict_surfaces,
    )
    violations: list[dict[str, Any]] = []

    def _append_set_violation(
        *,
        field: str,
        expected: list[str],
        actual: list[str],
        reason: str,
    ) -> None:
        if set(expected) == set(actual):
            return
        violations.append(
            {
                "field": field,
                "reason": reason,
                "missing_keys": sorted(set(expected) - set(actual)),
                "unexpected_keys": sorted(set(actual) - set(expected)),
                "expected_keys": expected,
                "actual_keys": actual,
            }
        )

    _append_set_violation(
        field="budgets",
        expected=list(summary["expected_budget_metric_keys"]),
        actual=list(summary["budget_metric_keys"]),
        reason="budget_metric_topology_drift",
    )
    _append_set_violation(
        field="budgets.direct_validate_calls",
        expected=list(summary["expected_direct_surface_keys"]),
        actual=list(summary["budget_direct_surface_keys"]),
        reason="strict_surface_budget_topology_drift",
    )
    _append_set_violation(
        field="convergence_guard.ceilings",
        expected=list(summary["expected_convergence_ceiling_keys"]),
        actual=list(summary["convergence_ceiling_keys"]),
        reason="convergence_ceiling_topology_drift",
    )
    _append_set_violation(
        field="convergence_guard.ceilings.direct_validate_calls",
        expected=list(summary["expected_convergence_direct_surface_keys"]),
        actual=list(summary["convergence_direct_surface_keys"]),
        reason="convergence_direct_surface_topology_drift",
    )
    return violations
