#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from root_corpus_governance_common import find_missing_markers


@dataclass(frozen=True)
class ContractTextMarkerCheck:
    reason: str
    markers: tuple[str, ...] = field(default_factory=tuple)


def _norm_str(value: Any) -> str:
    return str(value or "").strip()


def _row_attr_str(row: Any, attr_name: str) -> str:
    if isinstance(row, Mapping):
        return _norm_str(row.get(attr_name))
    return _norm_str(getattr(row, attr_name, ""))


def contract_required_markers_from_doc(
    doc: Mapping[str, Any],
    *,
    field_name: str = "contract_required_markers",
) -> tuple[str, ...]:
    value = doc.get(field_name)
    if not isinstance(value, list):
        return ()
    return tuple(marker for marker in (_norm_str(item) for item in value) if marker)


def contract_text_marker_checks_from_rows(
    rows: Iterable[Any],
    *,
    reason: str,
    marker_attrs: tuple[str, ...] = ("contract_heading",),
) -> tuple[ContractTextMarkerCheck, ...]:
    out: list[ContractTextMarkerCheck] = []
    for row in rows:
        markers = tuple(marker for marker in (_row_attr_str(row, attr_name) for attr_name in marker_attrs) if marker)
        if not markers:
            continue
        out.append(ContractTextMarkerCheck(reason=reason, markers=markers))
    return tuple(out)


def merge_contract_text_marker_checks(
    *groups: Iterable[ContractTextMarkerCheck],
) -> tuple[ContractTextMarkerCheck, ...]:
    return tuple(check for group in groups for check in group)


def evaluate_contract_text_marker_checks(
    contract_text: str,
    *,
    required_markers: Iterable[str] = (),
    row_checks: Iterable[ContractTextMarkerCheck] = (),
    payload_base: Mapping[str, Any] | None = None,
    required_marker_reason: str = "required_marker_missing",
) -> list[dict[str, Any]]:
    base_payload = dict(payload_base or {})
    violations: list[dict[str, Any]] = []
    for marker in find_missing_markers(contract_text, tuple(required_markers)):
        violations.append(
            {
                **base_payload,
                "reason": required_marker_reason,
                "marker": marker,
            }
        )
    for check in row_checks:
        for marker in find_missing_markers(contract_text, check.markers):
            violations.append(
                {
                    **base_payload,
                    "reason": check.reason,
                    "marker": marker,
                }
            )
    return violations
