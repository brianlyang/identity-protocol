#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


def _clean_str(value: Any) -> str:
    return str(value or "").strip()


def build_report_selection_authority_projection(
    payload: Mapping[str, Any],
    *,
    selected_path_key: str,
    selection_mode_key: str,
    selected_authority_class_key: str,
    pointer_resolution_mode_key: str,
    pointer_path_key: str = "",
    projection_source: str = "",
) -> dict[str, str]:
    projection = {
        "selected_path": _clean_str(payload.get(selected_path_key)),
        "selection_mode": _clean_str(payload.get(selection_mode_key)),
        "selected_authority_class": _clean_str(payload.get(selected_authority_class_key)),
        "pointer_resolution_mode": _clean_str(payload.get(pointer_resolution_mode_key)),
        "pointer_path": _clean_str(payload.get(pointer_path_key)) if pointer_path_key else "",
        "projection_source": _clean_str(projection_source),
    }
    return projection


def collect_report_selection_authority_projection_stale_reasons(
    payload: Mapping[str, Any],
    *,
    selected_path_key: str,
    selection_mode_key: str,
    selected_authority_class_key: str,
    pointer_resolution_mode_key: str,
    expected_selected_path: str | Path = "",
    require_selected_path: bool = False,
    selected_path_reason: str,
    authority_reason: str,
) -> list[str]:
    reasons: list[str] = []

    expected_selected_path_token = _clean_str(expected_selected_path)
    if expected_selected_path_token:
        expected_selected_path_token = str(
            Path(expected_selected_path_token).expanduser().resolve()
        )

    selected_path = _clean_str(payload.get(selected_path_key))
    if require_selected_path and not selected_path:
        reasons.append(selected_path_reason)
    elif expected_selected_path_token and selected_path != expected_selected_path_token:
        reasons.append(selected_path_reason)

    if (
        not _clean_str(payload.get(selection_mode_key))
        or not _clean_str(payload.get(selected_authority_class_key))
        or not _clean_str(payload.get(pointer_resolution_mode_key))
    ):
        reasons.append(authority_reason)

    return reasons
