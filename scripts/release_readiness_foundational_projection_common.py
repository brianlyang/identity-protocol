#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


STATUS_UNKNOWN = "UNKNOWN"

RELEASE_READINESS_FOUNDATIONAL_ONE_LOOK_FIELDS: tuple[str, ...] = (
    "required_contract_coverage_status",
    "failed_required_contract_count",
    "failed_required_contracts",
    "failed_optional_contract_count",
    "failed_optional_contracts",
    "required_gate_recurrence_status",
    "required_gate_tuple_parity_status",
)
RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER = (
    "release_readiness_foundational_projection="
    + "|".join(
        f"one_look.{field}"
        for field in RELEASE_READINESS_FOUNDATIONAL_ONE_LOOK_FIELDS
    )
)
RELEASE_READINESS_FOUNDATIONAL_SURFACE_CONSTRAINTS: tuple[str, ...] = (
    RELEASE_READINESS_FOUNDATIONAL_PROJECTION_MARKER,
    *(
        f"one_look.{field}"
        for field in RELEASE_READINESS_FOUNDATIONAL_ONE_LOOK_FIELDS
    ),
)


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def build_release_readiness_foundational_one_look_projection(
    summary: dict[str, Any] | None,
) -> dict[str, Any]:
    summary_payload = summary if isinstance(summary, dict) else {}
    coverage = summary_payload.get("required_contract_coverage") or {}
    recurrence = summary_payload.get("required_gate_recurrence") or {}
    tuple_parity = summary_payload.get("required_gate_tuple_parity") or {}
    return {
        "required_contract_coverage_status": _clean_str(coverage.get("status")).upper()
        or STATUS_UNKNOWN,
        "failed_required_contract_count": _safe_int(coverage.get("failed_required_contract_count")),
        "failed_required_contracts": _clean_list(coverage.get("failed_required_contracts")),
        "failed_optional_contract_count": _safe_int(coverage.get("failed_optional_contract_count")),
        "failed_optional_contracts": _clean_list(coverage.get("failed_optional_contracts")),
        "required_gate_recurrence_status": _clean_str(recurrence.get("status")).upper()
        or STATUS_UNKNOWN,
        "required_gate_tuple_parity_status": _clean_str(tuple_parity.get("status")).upper()
        or STATUS_UNKNOWN,
    }


def apply_release_readiness_foundational_one_look(
    summary: dict[str, Any],
    one_look: dict[str, Any],
) -> None:
    if not isinstance(one_look, dict):
        return
    one_look.update(build_release_readiness_foundational_one_look_projection(summary))
