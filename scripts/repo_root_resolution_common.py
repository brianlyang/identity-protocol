#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

PROTOCOL_ROOT_MARKERS: tuple[str, ...] = ("scripts", "identity", "docs")
PROTOCOL_REPO_DIRNAME = "identity-protocol-local"
WORKSPACE_IDENTITY_DIRNAME = ".identity"


def _iter_ancestor_dirs(start: str | Path) -> list[Path]:
    anchor = Path(start).expanduser().resolve()
    if anchor.is_file():
        anchor = anchor.parent
    return [anchor, *anchor.parents]


def _looks_like_protocol_repo(root: Path) -> bool:
    return all((root / marker).exists() for marker in PROTOCOL_ROOT_MARKERS)


def default_repo_root(*, start: str | Path) -> Path:
    for candidate in _iter_ancestor_dirs(start):
        if _looks_like_protocol_repo(candidate):
            return candidate.resolve()
        child = (candidate / PROTOCOL_REPO_DIRNAME).resolve()
        if _looks_like_protocol_repo(child):
            return child
    anchor = Path(start).expanduser().resolve()
    if anchor.is_file():
        return anchor.parent.parent
    return anchor


def default_workspace_root(*, start: str | Path) -> Path:
    for candidate in _iter_ancestor_dirs(start):
        if (candidate / WORKSPACE_IDENTITY_DIRNAME).exists() and (candidate / PROTOCOL_REPO_DIRNAME).exists():
            return candidate.resolve()
        if _looks_like_protocol_repo(candidate):
            return candidate.parent.resolve()
        child = (candidate / PROTOCOL_REPO_DIRNAME).resolve()
        if _looks_like_protocol_repo(child):
            return candidate.resolve()
    return default_repo_root(start=start).parent.resolve()


def resolve_protocol_repo_root(raw_repo_root: str, *, start: str | Path) -> Path:
    token = str(raw_repo_root or "").strip()
    if token:
        return Path(token).expanduser().resolve()
    return default_repo_root(start=start)


def resolve_workspace_root(raw_workspace_root: str, *, start: str | Path) -> Path:
    token = str(raw_workspace_root or "").strip()
    if token:
        return Path(token).expanduser().resolve()
    return default_workspace_root(start=start)


def resolve_repo_root(raw_repo_root: str, *, start: str | Path) -> Path:
    return resolve_protocol_repo_root(raw_repo_root, start=start)
