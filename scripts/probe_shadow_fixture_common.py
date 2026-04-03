#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable

from repo_root_resolution_common import resolve_repo_root


def _normalized_relpaths(values: Iterable[str]) -> list[str]:
    relpaths = [str(value).strip() for value in values if str(value).strip()]
    return sorted(dict.fromkeys(relpaths))


def _copy_relpath(*, repo_root: Path, shadow_root: Path, relpath: str) -> str:
    src = (repo_root / relpath).resolve()
    if not src.exists() or not src.is_file():
        raise FileNotFoundError(f"probe_shadow_fixture_missing_file:{relpath}")
    dst = (shadow_root / relpath).resolve()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return relpath


def _expand_glob_relpaths(*, repo_root: Path, pattern: str) -> list[str]:
    matches = [path for path in repo_root.glob(pattern) if path.is_file()]
    relpaths = sorted(str(path.relative_to(repo_root)) for path in matches)
    if not relpaths:
        raise FileNotFoundError(f"probe_shadow_fixture_glob_unmatched:{pattern}")
    return relpaths


def stage_probe_shadow_fixture(
    *,
    repo_root: Path,
    shadow_root: Path,
    copy_files: Iterable[str],
    copy_globs: Iterable[str],
) -> dict[str, object]:
    shadow_root.mkdir(parents=True, exist_ok=True)

    copied_relpaths: list[str] = []
    for relpath in _normalized_relpaths(copy_files):
        copied_relpaths.append(_copy_relpath(repo_root=repo_root, shadow_root=shadow_root, relpath=relpath))

    expanded_globs: dict[str, list[str]] = {}
    for pattern in _normalized_relpaths(copy_globs):
        relpaths = _expand_glob_relpaths(repo_root=repo_root, pattern=pattern)
        expanded_globs[pattern] = relpaths
        for relpath in relpaths:
            copied_relpaths.append(_copy_relpath(repo_root=repo_root, shadow_root=shadow_root, relpath=relpath))

    copied_relpaths = sorted(dict.fromkeys(copied_relpaths))
    return {
        "repo_root": str(repo_root),
        "shadow_root": str(shadow_root),
        "copied_file_count": len(copied_relpaths),
        "copied_files": copied_relpaths,
        "expanded_globs": expanded_globs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a shadow fixture from explicit repo-relative files/globs.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--shadow-root", required=True)
    parser.add_argument("--copy-file", action="append", default=[])
    parser.add_argument("--copy-glob", action="append", default=[])
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    shadow_root = Path(args.shadow_root).expanduser().resolve()
    payload = stage_probe_shadow_fixture(
        repo_root=repo_root,
        shadow_root=shadow_root,
        copy_files=args.copy_file or [],
        copy_globs=args.copy_glob or [],
    )
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
