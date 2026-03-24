#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    load_root_corpus_ordering,
    reading_order_rows_from_doc,
    source_order_rows_from_doc,
)

STATUS_KEY = "protocol_root_corpus_ordering_status"
ERR_REGISTRY = "IP-RCO-001"
ERR_STRUCTURE = "IP-RCO-002"
ERR_COVERAGE = "IP-RCO-003"
ROOT_INDEX_ENTRY_ROLE = "root_index_entry_surface"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _contiguous_orders(values: list[int]) -> bool:
    return values == list(range(1, len(values) + 1))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus source-order and reading-order governance.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    coverage_violations: list[dict[str, Any]] = []
    error_code = ""

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    source_rows = source_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()

    if not stale_reasons:
        if str(ordering_doc.get("ordering_family") or "").strip() != "protocol_root_corpus_ordering":
            stale_reasons.append("root_corpus_ordering_family_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("ordering_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_ordering_version_invalid")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_ordering_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(ordering_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_ordering_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if not str(ordering_doc.get("root_index_entry") or "").strip():
            stale_reasons.append("root_corpus_ordering_root_index_entry_missing")
            error_code = ERR_REGISTRY
        if not source_rows:
            stale_reasons.append("root_corpus_ordering_source_order_missing")
            error_code = ERR_REGISTRY
        if not reading_rows:
            stale_reasons.append("root_corpus_ordering_reading_order_missing")
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    expected_source_classes = sorted({entry.corpus_class for entry in registry_entries if entry.corpus_class != "root_index"})
    registry_class_law_bearing = {
        cls: any(entry.corpus_class == cls and entry.law_bearing for entry in registry_entries) for cls in registry_classes
    }

    source_orders = [row.order for row in source_rows]
    source_classes = [row.corpus_class for row in source_rows]
    reading_orders = [row.order for row in reading_rows]
    reading_paths = [row.rel_path for row in reading_rows]
    sorted_source_rows = sorted(source_rows, key=lambda item: item.order)
    sorted_reading_rows = sorted(reading_rows, key=lambda item: item.order)
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip()

    if not stale_reasons:
        if len(set(source_orders)) != len(source_orders) or not _contiguous_orders(sorted(source_orders)):
            structure_violations.append({"field": "source_order", "reason": "source_order_non_contiguous"})
        if len(set(source_classes)) != len(source_classes):
            structure_violations.append({"field": "source_order", "reason": "source_order_duplicate_corpus_class"})
        if "root_index" in source_classes:
            structure_violations.append({"field": "source_order", "reason": "root_index_must_not_be_generative_source"})
        if len(set(reading_orders)) != len(reading_orders) or not _contiguous_orders(sorted(reading_orders)):
            structure_violations.append({"field": "reading_order", "reason": "reading_order_non_contiguous"})
        if len(set(reading_paths)) != len(reading_paths):
            structure_violations.append({"field": "reading_order", "reason": "reading_order_duplicate_rel_path"})
        if (
            not sorted_reading_rows
            or sorted_reading_rows[0].rel_path != root_index_entry
            or sorted_reading_rows[0].entry_role != ROOT_INDEX_ENTRY_ROLE
        ):
            structure_violations.append(
                {
                    "field": "reading_order",
                    "reason": "root_index_entry_not_first",
                    "expected_rel_path": root_index_entry,
                    "expected_entry_role": ROOT_INDEX_ENTRY_ROLE,
                }
            )
        if root_index_entry and registry_entry_class_map.get(root_index_entry) != "root_index":
            structure_violations.append(
                {
                    "field": "root_index_entry",
                    "reason": "root_index_entry_not_registered_as_root_index",
                    "rel_path": root_index_entry,
                }
            )

        missing_source_classes = sorted(set(expected_source_classes) - set(source_classes))
        extra_source_classes = sorted(set(source_classes) - set(expected_source_classes))
        if missing_source_classes:
            coverage_violations.append(
                {"field": "source_order", "reason": "missing_source_classes", "corpus_classes": missing_source_classes}
            )
        if extra_source_classes:
            coverage_violations.append(
                {"field": "source_order", "reason": "extra_source_classes", "corpus_classes": extra_source_classes}
            )
        for row in sorted_source_rows:
            expected_law_bearing = registry_class_law_bearing.get(row.corpus_class)
            if expected_law_bearing is None:
                continue
            if bool(row.law_bearing_required) != bool(expected_law_bearing):
                coverage_violations.append(
                    {
                        "field": "source_order",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected_law_bearing),
                        "actual": bool(row.law_bearing_required),
                    }
                )

        missing_reading_entries = sorted(set(registry_paths) - set(reading_paths))
        extra_reading_entries = sorted(set(reading_paths) - set(registry_paths))
        if missing_reading_entries:
            coverage_violations.append(
                {
                    "field": "reading_order",
                    "reason": "missing_registered_entries",
                    "rel_paths": missing_reading_entries,
                }
            )
        if extra_reading_entries:
            coverage_violations.append(
                {
                    "field": "reading_order",
                    "reason": "extra_unregistered_entries",
                    "rel_paths": extra_reading_entries,
                }
            )

        source_rank_by_class = {row.corpus_class: row.order for row in sorted_source_rows}
        previous_rank = 0
        for row in sorted_reading_rows[1:]:
            corpus_class = registry_entry_class_map.get(row.rel_path, "")
            if not corpus_class:
                continue
            current_rank = source_rank_by_class.get(corpus_class)
            if current_rank is None:
                coverage_violations.append(
                    {
                        "field": "reading_order",
                        "reason": "reading_entry_class_not_in_source_order",
                        "rel_path": row.rel_path,
                        "corpus_class": corpus_class,
                    }
                )
                continue
            if current_rank < previous_rank:
                coverage_violations.append(
                    {
                        "field": "reading_order",
                        "reason": "reading_order_inverts_source_order",
                        "rel_path": row.rel_path,
                        "corpus_class": corpus_class,
                        "source_rank": current_rank,
                        "previous_source_rank": previous_rank,
                    }
                )
            previous_rank = current_rank

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and coverage_violations:
        error_code = ERR_COVERAGE

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"coverage_violation:{row['field']}:{row['reason']}" for row in coverage_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_COVERAGE),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "root_dir": str(ordering_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "registry_class_ids": registry_classes,
        "expected_source_classes": expected_source_classes,
        "source_order": [
            {
                "order": row.order,
                "corpus_class": row.corpus_class,
                "source_role": row.source_role,
                "law_bearing_required": row.law_bearing_required,
            }
            for row in sorted_source_rows
        ],
        "reading_order": [
            {
                "order": row.order,
                "rel_path": row.rel_path,
                "entry_role": row.entry_role,
                "corpus_class": registry_entry_class_map.get(row.rel_path, ""),
            }
            for row in sorted_reading_rows
        ],
        "source_order_class_count": len(source_rows),
        "reading_order_entry_count": len(reading_rows),
        "registered_entry_count": len(registry_entries),
        "structure_violations": structure_violations,
        "coverage_violations": coverage_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
