#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Iterable

IDENTITY_UPGRADE_EXEC_PREFIX = "identity-upgrade-exec-"
DERIVATIVE_REPORT_SUFFIXES: tuple[str, ...] = (
    "-patch-plan.json",
    "-postexec-receipt.json",
    "-receipt.json",
)
DERIVATIVE_REPORT_PATH_TOKENS: tuple[str, ...] = (
    "/runtime/protocol-feedback/",
    "/archive/",
    "/archives/",
    "/runtime/reports/postexec/",
)


def dedupe_resolved_paths(rows: Iterable[Path]) -> list[Path]:
    dedup: dict[str, Path] = {}
    for row in rows:
        resolved = row.expanduser().resolve()
        dedup[resolved.as_posix()] = resolved
    return list(dedup.values())


def report_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def report_glob_pattern(identity_id: str) -> str:
    normalized_identity = str(identity_id or "").strip()
    if normalized_identity in {"", "*"}:
        return f"**/{IDENTITY_UPGRADE_EXEC_PREFIX}*.json"
    return f"**/{IDENTITY_UPGRADE_EXEC_PREFIX}{normalized_identity}-*.json"


def is_derivative_execution_report(path: Path) -> bool:
    lower_name = path.name.lower()
    if any(lower_name.endswith(suffix) for suffix in DERIVATIVE_REPORT_SUFFIXES):
        return True
    path_text = path.expanduser().resolve().as_posix().lower()
    return any(token in path_text for token in DERIVATIVE_REPORT_PATH_TOKENS)


def is_primary_execution_report(
    path: Path,
    *,
    identity_id: str = "",
    include_generic_upgrade_json: bool = False,
) -> bool:
    if not path.is_file():
        return False
    lower_name = path.name.lower()
    if not lower_name.endswith(".json"):
        return False
    if is_derivative_execution_report(path):
        return False
    normalized_identity = str(identity_id or "").strip()
    if lower_name.startswith(IDENTITY_UPGRADE_EXEC_PREFIX):
        if normalized_identity in {"", "*"}:
            return True
        return f"{IDENTITY_UPGRADE_EXEC_PREFIX}{normalized_identity.lower()}-" in lower_name
    if not include_generic_upgrade_json:
        return False
    return "upgrade" in lower_name


def collect_primary_execution_reports_from_roots(
    report_roots: Iterable[Path],
    identity_id: str,
    *,
    include_generic_upgrade_json: bool = False,
) -> list[Path]:
    rows: list[Path] = []
    generic_rows: list[Path] = []
    pattern = report_glob_pattern(identity_id)
    for root in dedupe_resolved_paths(report_roots):
        if not root.exists():
            continue
        for candidate in root.glob(pattern):
            resolved = candidate.resolve()
            if is_primary_execution_report(resolved, identity_id=identity_id):
                rows.append(resolved)
        if not include_generic_upgrade_json or rows:
            continue
        for candidate in root.glob("**/*.json"):
            resolved = candidate.resolve()
            if is_primary_execution_report(
                resolved,
                include_generic_upgrade_json=True,
            ):
                generic_rows.append(resolved)
    selected_rows = rows if rows else generic_rows
    return sorted(dedupe_resolved_paths(selected_rows), key=report_mtime)


def latest_primary_execution_report_from_roots(
    report_roots: Iterable[Path],
    identity_id: str,
    *,
    include_generic_upgrade_json: bool = False,
) -> Path | None:
    rows = collect_primary_execution_reports_from_roots(
        report_roots,
        identity_id,
        include_generic_upgrade_json=include_generic_upgrade_json,
    )
    return rows[-1] if rows else None
