#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from primary_execution_report_common import latest_prompt_bound_primary_execution_report_from_roots
from tool_vendor_governance_common import (
    IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_EXPLICIT_REPORT_OVERRIDE,
    IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_NONE,
    IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE,
    IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE_MISSING,
    IDENTITY_UPGRADE_REPORT_SELECTION_MODE_EXPLICIT_REPORT_OVERRIDE,
    IDENTITY_UPGRADE_REPORT_SELECTION_MODE_NONE,
    resolve_pack_and_task,
    resolve_identity_upgrade_report_selection,
)

SEARCH_ROOT_SELECTION_MODE = "search_root_latest_primary_execution_report"
SEARCH_ROOT_AUTHORITY_CLASS = "search_root_latest_primary_execution_report"
SEARCH_ROOT_POINTER_RESOLUTION_MODE = "search_roots_primary_execution_report"


def _emit(payload: dict[str, Any], *, print_path_only: bool, json_only: bool) -> None:
    if print_path_only:
        print(str(payload.get("selected_report_path", "")).strip())
        return
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve the latest primary identity upgrade execution report.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default="")
    ap.add_argument("--pack-root", default="")
    ap.add_argument("--search-root", action="append", default=[])
    ap.add_argument("--explicit-report", default="")
    ap.add_argument("--print-path-only", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    explicit_report = str(args.explicit_report or "").strip()
    catalog_path = str(args.catalog or "").strip()
    pack_root = str(args.pack_root or "").strip()
    search_roots = [
        Path(item).expanduser().resolve()
        for item in (args.search_root or [])
        if str(item or "").strip()
    ]
    resolved_pack_root: Path | None = None
    if pack_root:
        resolved_pack_root = Path(pack_root).expanduser().resolve()
    elif catalog_path:
        resolved_pack_root, _ = resolve_pack_and_task(
            Path(catalog_path).expanduser().resolve(),
            args.identity_id,
        )

    payload: dict[str, Any]
    if resolved_pack_root is not None and not search_roots:
        resolution = resolve_identity_upgrade_report_selection(
            args.identity_id,
            resolved_pack_root,
            explicit_report=explicit_report,
        )
        payload = {
            "selected_report_path": str(resolution.selected_report) if resolution.selected_report else "",
            "selection_mode": str(resolution.selection_mode or "").strip(),
            "selected_report_authority_class": str(resolution.selected_report_authority_class or "").strip(),
            "pointer_resolution_mode": str(resolution.pointer_resolution_mode or "").strip(),
            "pointer_path": str(resolution.pointer_path) if resolution.pointer_path is not None else "",
            "search_roots": [str(root) for root in search_roots],
        }
    elif explicit_report:
        explicit_path = Path(explicit_report).expanduser().resolve()
        payload = {
            "selected_report_path": str(explicit_path) if explicit_path.exists() and explicit_path.is_file() else "",
            "selection_mode": IDENTITY_UPGRADE_REPORT_SELECTION_MODE_EXPLICIT_REPORT_OVERRIDE,
            "selected_report_authority_class": IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_EXPLICIT_REPORT_OVERRIDE,
            "pointer_resolution_mode": (
                IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE
                if explicit_path.exists() and explicit_path.is_file()
                else IDENTITY_UPGRADE_REPORT_POINTER_RESOLUTION_MODE_EXPLICIT_REPORT_OVERRIDE_MISSING
            ),
            "pointer_path": "",
            "search_roots": [str(root) for root in search_roots],
        }
    else:
        selected = latest_prompt_bound_primary_execution_report_from_roots(
            search_roots,
            args.identity_id,
            explicit_pack_root=resolved_pack_root,
        )
        payload = {
            "selected_report_path": str(selected) if selected is not None else "",
            "selection_mode": SEARCH_ROOT_SELECTION_MODE if selected is not None else IDENTITY_UPGRADE_REPORT_SELECTION_MODE_NONE,
            "selected_report_authority_class": SEARCH_ROOT_AUTHORITY_CLASS if selected is not None else IDENTITY_UPGRADE_REPORT_AUTHORITY_CLASS_NONE,
            "pointer_resolution_mode": SEARCH_ROOT_POINTER_RESOLUTION_MODE if selected is not None else IDENTITY_UPGRADE_REPORT_SELECTION_MODE_NONE,
            "pointer_path": "",
            "search_roots": [str(root) for root in search_roots],
        }
    _emit(payload, print_path_only=bool(args.print_path_only), json_only=bool(args.json_only))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
