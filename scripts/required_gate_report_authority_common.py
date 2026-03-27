#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from tool_vendor_governance_common import (
    build_identity_upgrade_report_selection_projection,
    resolve_identity_upgrade_report_selection,
)

REQUIRED_GATE_REPORT_AUTHORITY_FIELDS: tuple[str, ...] = (
    "report_selected_path",
    "report_selection_mode",
    "report_selected_authority_class",
    "report_pointer_resolution_mode",
    "report_pointer_path",
)


def build_required_gate_report_authority_projection(
    *,
    identity_id: str,
    explicit_report: str = "",
    pack_root: Path | None = None,
) -> dict[str, str]:
    projection = {field: "" for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS}
    explicit_token = str(explicit_report or "").strip()
    if not explicit_token:
        return projection
    resolved_pack_root = (
        Path(pack_root).expanduser().resolve()
        if isinstance(pack_root, Path)
        else Path.cwd().resolve()
    )
    resolution = resolve_identity_upgrade_report_selection(
        str(identity_id or "").strip(),
        resolved_pack_root,
        explicit_report=explicit_token,
    )
    selection_projection = build_identity_upgrade_report_selection_projection(
        resolution,
        field_prefix="report",
    )
    for field in REQUIRED_GATE_REPORT_AUTHORITY_FIELDS:
        projection[field] = str(selection_projection.get(field, "") or "").strip()
    return projection
