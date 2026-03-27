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
        if not rel_path or not required_markers:
            continue
        out.append(RootDocAnchorCheck(rel_path=rel_path, required_markers=required_markers))
    return tuple(out)


def root_doc_anchor_check_marker_map(
    anchor_checks: Iterable[RootDocAnchorCheck],
) -> dict[str, tuple[str, ...]]:
    return {row.rel_path: tuple(row.required_markers) for row in anchor_checks}


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


def evaluate_root_doc_anchor_checks(
    repo_root: Path,
    anchor_checks: Iterable[RootDocAnchorCheck],
    *,
    field_name: str = "root_doc_anchor_checks",
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for check in anchor_checks:
        path = (repo_root / check.rel_path).resolve()
        if not path.exists() or not path.is_file():
            violations.append(
                {
                    "field": field_name,
                    "rel_path": check.rel_path,
                    "reason": "anchor_file_missing",
                }
            )
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in find_missing_markers(text, check.required_markers):
            violations.append(
                {
                    "field": field_name,
                    "rel_path": check.rel_path,
                    "reason": "required_marker_missing",
                    "marker": marker,
                }
            )
    return violations
