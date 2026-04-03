#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable


README_REL_PATH = Path("identity/protocol/README.md")


def evaluate_root_contract_readme_reference(
    repo_root: Path,
    *,
    required_markers: Iterable[str],
    field_name: str = "README",
    readme_rel_path: Path = README_REL_PATH,
    missing_readme_reason: str = "root_readme_missing",
    missing_marker_reason: str = "root_readme_missing_contract_reference",
) -> list[dict[str, Any]]:
    readme_path = (repo_root / readme_rel_path).resolve()
    if not readme_path.exists() or not readme_path.is_file():
        return [{"field": field_name, "reason": missing_readme_reason}]

    readme_text = readme_path.read_text(encoding="utf-8", errors="ignore")
    violations: list[dict[str, Any]] = []
    for marker in required_markers:
        if str(marker or "").strip() and marker not in readme_text:
            violations.append(
                {
                    "field": field_name,
                    "reason": missing_marker_reason,
                    "marker": marker,
                }
            )
    return violations
