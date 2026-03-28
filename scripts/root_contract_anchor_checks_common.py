#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from root_corpus_governance_common import find_missing_markers


@dataclass(frozen=True)
class RootDocAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def root_doc_anchor_checks_from_doc(
    doc: Mapping[str, Any],
    *,
    field_name: str = "anchor_checks",
    require_markers: bool = True,
) -> tuple[RootDocAnchorCheck, ...]:
    rows = doc.get(field_name)
    if not isinstance(rows, list):
        return ()
    out: list[RootDocAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        required_markers = _as_str_tuple(row.get("required_markers"))
        if not rel_path or (require_markers and not required_markers):
            continue
        out.append(RootDocAnchorCheck(rel_path=rel_path, required_markers=required_markers))
    return tuple(out)


def root_doc_anchor_check_marker_map(
    anchor_checks: Iterable[RootDocAnchorCheck],
) -> dict[str, tuple[str, ...]]:
    return {row.rel_path: tuple(row.required_markers) for row in anchor_checks}


def root_doc_anchor_rel_paths(
    anchor_checks: Iterable[RootDocAnchorCheck],
) -> tuple[str, ...]:
    return tuple(row.rel_path for row in anchor_checks)


def validate_expected_root_doc_anchor_checks(
    anchor_checks: Iterable[RootDocAnchorCheck],
    expected_anchor_checks: Mapping[str, tuple[str, ...]],
    *,
    stale_reason_prefix: str,
) -> list[str]:
    actual_map = root_doc_anchor_check_marker_map(anchor_checks)
    if not actual_map:
        return [f"{stale_reason_prefix}_anchor_checks_missing"]

    reasons: list[str] = []
    missing_anchor_rel_paths = sorted(set(expected_anchor_checks) - set(actual_map))
    extra_anchor_rel_paths = sorted(set(actual_map) - set(expected_anchor_checks))
    if missing_anchor_rel_paths:
        reasons.append(
            f"{stale_reason_prefix}_anchor_check_rel_paths_missing:" + ",".join(missing_anchor_rel_paths)
        )
    if extra_anchor_rel_paths:
        reasons.append(
            f"{stale_reason_prefix}_anchor_check_rel_paths_extra:" + ",".join(extra_anchor_rel_paths)
        )
    for rel_path, expected_markers in expected_anchor_checks.items():
        actual_markers = actual_map.get(rel_path)
        if actual_markers is None:
            continue
        if tuple(actual_markers) != tuple(expected_markers):
            reasons.append(f"{stale_reason_prefix}_anchor_check_markers_invalid:{rel_path}")
    return reasons


def append_expected_root_doc_anchor_stale_reasons(
    stale_reasons: list[str],
    anchor_checks: Iterable[RootDocAnchorCheck],
    expected_anchor_checks: Mapping[str, tuple[str, ...]],
    *,
    stale_reason_prefix: str,
) -> bool:
    reasons = validate_expected_root_doc_anchor_checks(
        anchor_checks,
        expected_anchor_checks,
        stale_reason_prefix=stale_reason_prefix,
    )
    if not reasons:
        return False
    stale_reasons.extend(reasons)
    return True


def append_root_doc_anchor_registry_structure_violations(
    structure_violations: list[dict[str, Any]],
    anchor_checks: Iterable[RootDocAnchorCheck],
    *,
    field_name: str,
    registry_paths: Iterable[str],
    registry_entry_kind_map: Mapping[str, Any] | None = None,
    registry_entry_law_bearing_map: Mapping[str, Any] | None = None,
    duplicate_reason: str = "duplicate_rel_path",
    unregistered_reason: str = "unregistered_anchor_entries",
    require_file_entry: bool = False,
    file_entry_reason: str = "anchor_must_target_file_entry",
    require_law_bearing: bool = False,
    law_bearing_reason: str = "anchor_must_target_law_bearing_entry",
) -> tuple[str, ...]:
    anchor_rel_paths = root_doc_anchor_rel_paths(anchor_checks)
    registry_path_set = {_norm_str(rel_path) for rel_path in registry_paths if _norm_str(rel_path)}

    if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
        structure_violations.append({"field": field_name, "reason": duplicate_reason})

    missing_anchor_entries = sorted(set(anchor_rel_paths) - registry_path_set)
    if missing_anchor_entries:
        structure_violations.append(
            {"field": field_name, "reason": unregistered_reason, "rel_paths": missing_anchor_entries}
        )

    if not require_file_entry and not require_law_bearing:
        return anchor_rel_paths

    kind_map = registry_entry_kind_map or {}
    law_bearing_map = registry_entry_law_bearing_map or {}
    for rel_path in anchor_rel_paths:
        if require_file_entry:
            entry_kind = kind_map.get(rel_path)
            if entry_kind is None:
                continue
            if entry_kind != "file":
                structure_violations.append(
                    {
                        "field": field_name,
                        "reason": file_entry_reason,
                        "rel_path": rel_path,
                        "entry_kind": entry_kind,
                    }
                )
        if require_law_bearing:
            if rel_path not in law_bearing_map:
                continue
            if not bool(law_bearing_map.get(rel_path, False)):
                structure_violations.append(
                    {
                        "field": field_name,
                        "reason": law_bearing_reason,
                        "rel_path": rel_path,
                    }
                )

    return anchor_rel_paths


def evaluate_root_doc_anchor_checks(
    repo_root: Path,
    anchor_checks: Iterable[RootDocAnchorCheck],
    *,
    field_name: str | None = "root_doc_anchor_checks",
    missing_target_reason: str = "anchor_file_missing",
    missing_marker_reason: str = "required_marker_missing",
    aggregate_missing_markers: bool = False,
    require_file: bool = True,
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for check in anchor_checks:
        path = (repo_root / check.rel_path).resolve()
        if not path.exists() or (require_file and not path.is_file()):
            violation = {"rel_path": check.rel_path, "reason": missing_target_reason}
            if field_name:
                violation["field"] = field_name
            violations.append(violation)
            continue
        missing_markers = find_missing_markers(
            path.read_text(encoding="utf-8", errors="ignore"),
            check.required_markers,
        )
        if not missing_markers:
            continue
        if aggregate_missing_markers:
            violation = {
                "rel_path": check.rel_path,
                "reason": missing_marker_reason,
                "missing_markers": missing_markers,
            }
            if field_name:
                violation["field"] = field_name
            violations.append(violation)
            continue
        for marker in missing_markers:
            violation = {
                "rel_path": check.rel_path,
                "reason": missing_marker_reason,
                "marker": marker,
            }
            if field_name:
                violation["field"] = field_name
            violations.append(violation)
    return violations
