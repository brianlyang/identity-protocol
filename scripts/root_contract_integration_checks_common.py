#!/usr/bin/env python3
from __future__ import annotations

from typing import Any, Iterable


def _norm_str(value: Any) -> str:
    return str(value or "").strip()


def missing_expected_markers(
    required_markers: Iterable[str],
    expected_markers: Iterable[str],
) -> list[str]:
    marker_set = {_norm_str(item) for item in required_markers if _norm_str(item)}
    return [marker for marker in expected_markers if _norm_str(marker) and _norm_str(marker) not in marker_set]


def evaluate_root_contract_integration(
    *,
    contract_file: str,
    registry_entries: Iterable[Any],
    reading_rows: Iterable[Any],
    authority_anchors: Iterable[Any],
    authority_projections: Iterable[Any],
    routing_anchors: Iterable[Any],
    routing_projections: Iterable[Any],
    expected_registry_markers: tuple[str, ...],
    mappings_required_children: tuple[str, ...],
    expected_authority_markers: tuple[str, ...],
    expected_routing_markers: tuple[str, ...],
    expected_question_classes: tuple[str, ...] = ("frozen_domain_contract_law",),
    authority_missing_anchor_reason: str = "authority_anchor_missing_or_incomplete",
    authority_missing_markers_reason: str | None = None,
    authority_projection_role_reason: str = "authority_role_mismatch",
    authority_projection_mode_reason: str = "authority_mode_mismatch",
    routing_missing_anchor_reason: str = "routing_anchor_missing_or_incomplete",
    routing_missing_markers_reason: str | None = None,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []

    registry_entry_map = {getattr(entry, "rel_path", ""): entry for entry in registry_entries}
    registry_entry = registry_entry_map.get(contract_file)
    if registry_entry is None:
        violations.append({"field": "root_corpus_registry", "reason": "contract_not_registered"})
    else:
        if getattr(registry_entry, "entry_kind", "") != "file":
            violations.append(
                {
                    "field": "root_corpus_registry",
                    "reason": "registry_entry_kind_mismatch",
                    "actual": getattr(registry_entry, "entry_kind", ""),
                }
            )
        if getattr(registry_entry, "corpus_class", "") != "root_contract":
            violations.append(
                {
                    "field": "root_corpus_registry",
                    "reason": "registry_corpus_class_mismatch",
                    "expected": "root_contract",
                    "actual": getattr(registry_entry, "corpus_class", ""),
                }
            )
        if not bool(getattr(registry_entry, "law_bearing", False)):
            violations.append({"field": "root_corpus_registry", "reason": "registry_entry_must_be_law_bearing"})
        missing_registry_markers = missing_expected_markers(
            getattr(registry_entry, "required_markers", ()),
            expected_registry_markers,
        )
        if missing_registry_markers:
            violations.append(
                {
                    "field": "root_corpus_registry",
                    "reason": "registry_required_markers_missing",
                    "missing_markers": missing_registry_markers,
                }
            )

    mappings_entry = registry_entry_map.get("identity/protocol/mappings")
    if mappings_entry is None:
        violations.append({"field": "root_corpus_registry", "reason": "mappings_directory_not_registered"})
    else:
        required_children = set(getattr(mappings_entry, "required_children", ()))
        for child in mappings_required_children:
            if child not in required_children:
                violations.append(
                    {
                        "field": "root_corpus_registry",
                        "reason": "mappings_required_child_missing",
                        "child": child,
                    }
                )

    ordering_map = {getattr(row, "rel_path", ""): row for row in reading_rows}
    ordering_row = ordering_map.get(contract_file)
    if ordering_row is None:
        violations.append({"field": "root_corpus_ordering", "reason": "reading_order_entry_missing"})
    elif getattr(ordering_row, "entry_role", "") != "root_contract_entry":
        violations.append(
            {
                "field": "root_corpus_ordering",
                "reason": "reading_order_entry_role_mismatch",
                "expected": "root_contract_entry",
                "actual": getattr(ordering_row, "entry_role", ""),
            }
        )

    authority_anchor_map = {getattr(row, "rel_path", ""): row for row in authority_anchors}
    authority_anchor = authority_anchor_map.get(contract_file)
    authority_missing_markers = missing_expected_markers(
        getattr(authority_anchor, "required_markers", ()) if authority_anchor is not None else (),
        expected_authority_markers,
    )
    if authority_missing_markers_reason is None:
        if authority_missing_markers:
            violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": authority_missing_anchor_reason,
                    "missing_markers": authority_missing_markers,
                }
            )
    else:
        if authority_anchor is None:
            violations.append({"field": "root_corpus_authority", "reason": authority_missing_anchor_reason})
        elif authority_missing_markers:
            violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": authority_missing_markers_reason,
                    "missing_markers": authority_missing_markers,
                }
            )

    authority_projection_map = {getattr(row, "rel_path", ""): row for row in authority_projections}
    authority_projection = authority_projection_map.get(contract_file)
    if authority_projection is None:
        violations.append({"field": "root_corpus_authority", "reason": "authority_projection_missing"})
    else:
        if getattr(authority_projection, "corpus_class", "") != "root_contract":
            violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": "authority_projection_corpus_class_mismatch",
                    "expected": "root_contract",
                    "actual": getattr(authority_projection, "corpus_class", ""),
                }
            )
        if getattr(authority_projection, "authority_role", "") != "root_domain_contract_law":
            violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": authority_projection_role_reason,
                    "expected": "root_domain_contract_law",
                    "actual": getattr(authority_projection, "authority_role", ""),
                }
            )
        if getattr(authority_projection, "authority_mode", "") != "frozen_law_only":
            violations.append(
                {
                    "field": "root_corpus_authority",
                    "reason": authority_projection_mode_reason,
                    "expected": "frozen_law_only",
                    "actual": getattr(authority_projection, "authority_mode", ""),
                }
            )

    routing_anchor_map = {getattr(row, "rel_path", ""): row for row in routing_anchors}
    routing_anchor = routing_anchor_map.get(contract_file)
    routing_missing_markers = missing_expected_markers(
        getattr(routing_anchor, "required_markers", ()) if routing_anchor is not None else (),
        expected_routing_markers,
    )
    if routing_missing_markers_reason is None:
        if routing_missing_markers:
            violations.append(
                {
                    "field": "root_corpus_question_routing",
                    "reason": routing_missing_anchor_reason,
                    "missing_markers": routing_missing_markers,
                }
            )
    else:
        if routing_anchor is None:
            violations.append({"field": "root_corpus_question_routing", "reason": routing_missing_anchor_reason})
        elif routing_missing_markers:
            violations.append(
                {
                    "field": "root_corpus_question_routing",
                    "reason": routing_missing_markers_reason,
                    "missing_markers": routing_missing_markers,
                }
            )

    routing_projection_map = {getattr(row, "rel_path", ""): row for row in routing_projections}
    routing_projection = routing_projection_map.get(contract_file)
    if routing_projection is None:
        violations.append({"field": "root_corpus_question_routing", "reason": "routing_projection_missing"})
    else:
        actual_question_classes = tuple(getattr(routing_projection, "question_classes", ()))
        if actual_question_classes != tuple(expected_question_classes):
            violations.append(
                {
                    "field": "root_corpus_question_routing",
                    "reason": "routing_projection_question_classes_mismatch",
                    "expected": list(expected_question_classes),
                    "actual": list(actual_question_classes),
                }
            )

    return violations
