#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


def default_repo_root(*, start: str | Path) -> Path:
    anchor = Path(start).expanduser().resolve()
    if anchor.is_file():
        return anchor.parent.parent
    return anchor


def resolve_repo_root(raw_repo_root: str, *, start: str | Path) -> Path:
    token = str(raw_repo_root or "").strip()
    if not token:
        return default_repo_root(start=start)
    return Path(token).expanduser().resolve()
