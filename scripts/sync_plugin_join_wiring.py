#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc if isinstance(doc, dict) else {}


def _resolve_current_alias(repo_root: Path, rel_path: str) -> tuple[Path, str, str]:
    entry_path = (repo_root / rel_path).resolve()
    if not entry_path.exists() or not entry_path.is_file():
        return entry_path, "", "entry_file_missing"
    doc = _load_yaml(entry_path)
    active_file = str(doc.get("active_file", "")).strip()
    if not active_file:
        return entry_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _count_intake_rows(doc: dict[str, Any]) -> int:
    rows = doc.get("plugins") or []
    if not isinstance(rows, list):
        return 0
    return sum(1 for row in rows if isinstance(row, dict))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync/check plugin join intake wiring projections.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="check intake alias and shape")
    mode.add_argument("--apply", action="store_true", help="apply sync in-place (parity mode)")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--intake-current",
        default="identity/protocol/plugins/PLUGIN_JOIN_INTAKE.current.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    intake_rel = str(args.intake_current).strip()
    intake_path, intake_active_file, intake_alias_error = _resolve_current_alias(repo_root, intake_rel)

    status = STATUS_PASS_REQUIRED
    stale_reasons: list[str] = []
    intake_rows = 0

    if intake_alias_error:
        status = STATUS_WARN_NON_BLOCKING
        stale_reasons.append(f"intake_alias_error:{intake_alias_error}")
    else:
        try:
            intake_doc = _load_yaml(intake_path)
            intake_rows = _count_intake_rows(intake_doc)
        except Exception as exc:  # pragma: no cover - defensive
            status = STATUS_FAIL_REQUIRED
            stale_reasons.append(f"intake_parse_failed:{exc}")

    payload = {
        "plugin_join_sync_status": status,
        "mode": "apply" if args.apply else "check",
        "repo_root": str(repo_root),
        "intake_entry_file": str((repo_root / intake_rel).resolve()),
        "intake_file": str(intake_path),
        "intake_active_file": intake_active_file,
        "intake_alias_error": intake_alias_error,
        "intake_row_count": intake_rows,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 1 if status == STATUS_FAIL_REQUIRED else 0


if __name__ == "__main__":
    raise SystemExit(main())
