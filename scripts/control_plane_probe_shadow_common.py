#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from repo_root_resolution_common import resolve_repo_root


def _copy_text_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _symlink_if_missing(src: Path, dst: Path) -> None:
    if dst.exists():
        return
    dst.symlink_to(src, target_is_directory=src.is_dir())


def _normalized_name_set(values: Iterable[str]) -> set[str]:
    return {str(value).strip() for value in values if str(value).strip()}


def stage_control_plane_shadow_repo(
    *,
    repo_root: Path,
    shadow_root: Path,
    copied_scripts: Iterable[str],
    copied_mappings: Iterable[str],
) -> dict[str, object]:
    copied_script_names = _normalized_name_set(copied_scripts)
    copied_mapping_names = _normalized_name_set(copied_mappings)
    shadow_root.mkdir(parents=True, exist_ok=True)

    for child in repo_root.iterdir():
        if child.name in {"identity", "scripts"}:
            continue
        _symlink_if_missing(child, shadow_root / child.name)

    scripts_src = repo_root / "scripts"
    scripts_dst = shadow_root / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for child in scripts_src.iterdir():
        target = scripts_dst / child.name
        if child.name in copied_script_names:
            _copy_text_file(child, target)
            continue
        _symlink_if_missing(child, target)

    identity_src = repo_root / "identity"
    identity_dst = shadow_root / "identity"
    identity_dst.mkdir(parents=True, exist_ok=True)
    for child in identity_src.iterdir():
        if child.name == "protocol":
            continue
        _symlink_if_missing(child, identity_dst / child.name)

    protocol_src = identity_src / "protocol"
    protocol_dst = identity_dst / "protocol"
    protocol_dst.mkdir(parents=True, exist_ok=True)
    for child in protocol_src.iterdir():
        if child.name == "mappings":
            continue
        _symlink_if_missing(child, protocol_dst / child.name)

    mappings_src = protocol_src / "mappings"
    mappings_dst = protocol_dst / "mappings"
    mappings_dst.mkdir(parents=True, exist_ok=True)
    for child in mappings_src.iterdir():
        target = mappings_dst / child.name
        if child.name in copied_mapping_names:
            _copy_text_file(child, target)
            continue
        _symlink_if_missing(child, target)

    return {
        "repo_root": str(repo_root),
        "shadow_root": str(shadow_root),
        "copied_scripts": sorted(copied_script_names),
        "copied_mappings": sorted(copied_mapping_names),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a control-plane probe shadow repo with copied mutable surfaces.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--shadow-root", required=True)
    parser.add_argument("--copy-script", action="append", default=[])
    parser.add_argument("--copy-mapping", action="append", default=[])
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    shadow_root = Path(args.shadow_root).expanduser().resolve()
    payload = stage_control_plane_shadow_repo(
        repo_root=repo_root,
        shadow_root=shadow_root,
        copied_scripts=args.copy_script or [],
        copied_mappings=args.copy_mapping or [],
    )
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
