#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from primary_execution_report_common import report_logical_identity_key


def clean_str(value: Any) -> str:
    return str(value or "").strip()


def clean_list(values: Any) -> list[str]:
    if isinstance(values, (str, bytes)):
        token = clean_str(values)
        return [token] if token else []
    rows: list[str] = []
    for item in values or []:
        token = clean_str(item)
        if token:
            rows.append(token)
    return rows


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def build_experience_writeback_closure_projection(
    doc: dict[str, Any],
    *,
    execution_report: str | Path = "",
) -> dict[str, Any]:
    closure = doc.get("experience_writeback_closure")
    if not isinstance(closure, dict):
        closure = {}

    execution_report_token = clean_str(execution_report)
    if execution_report_token:
        execution_report_token = str(Path(execution_report_token).expanduser().resolve())
    execution_report_logical_identity_key = ""
    if execution_report_token:
        execution_report_logical_identity_key = report_logical_identity_key(
            Path(execution_report_token)
        )

    report_selected_path = clean_str(closure.get("report_selected_path"))
    report_logical_identity_key_value = clean_str(closure.get("report_logical_identity_key"))
    return {
        "status": clean_str(closure.get("status")).upper(),
        "validation_status": clean_str(closure.get("validation_status")).upper(),
        "report_selected_path": report_selected_path,
        "report_selected_path_matches_execution_report": bool(
            execution_report_token and report_selected_path == execution_report_token
        ),
        "report_logical_identity_key": report_logical_identity_key_value,
        "report_logical_identity_key_matches_execution_report": bool(
            execution_report_logical_identity_key
            and report_logical_identity_key_value == execution_report_logical_identity_key
        ),
        "report_selection_mode": clean_str(closure.get("report_selection_mode")),
        "report_selected_authority_class": clean_str(
            closure.get("report_selected_authority_class")
        ),
        "report_pointer_resolution_mode": clean_str(
            closure.get("report_pointer_resolution_mode")
        ),
        "report_run_id": clean_str(closure.get("report_run_id")),
        "writeback_status": clean_str(closure.get("writeback_status")).upper(),
        "writeback_rule_id": clean_str(closure.get("writeback_rule_id")),
        "rulebook_match_count": safe_int(closure.get("rulebook_match_count")),
        "task_history_contains_run_id": bool(closure.get("task_history_contains_run_id")),
        "stale_reasons": clean_list(closure.get("stale_reasons")),
    }
