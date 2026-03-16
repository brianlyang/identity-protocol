#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

DEFAULT_FORBIDDEN_TOKEN = ".agents/identity"
DEFAULT_REPLACEMENT = ".identity"

CONTROL_PLANE_GLOBS = (
    "catalog.local.yaml",
    "CURRENT_TASK.json",
    "IDENTITY_PROMPT.md",
    "META.yaml",
    "runtime/state/**/*",
    "runtime/plugins/**/*",
    "runtime/gate/**/*",
)

EXCLUDED_GLOBS = (
    "runtime/reports/**/*",
    "sanitization-backups/**/*",
    "*.bak*",
)


@dataclass(frozen=True)
class ResidueHit:
    path: str
    match_count: int


def _iter_control_plane_files(identity_home: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for pattern in CONTROL_PLANE_GLOBS:
        for candidate in identity_home.glob(pattern):
            if candidate in seen:
                continue
            if not candidate.exists() or not candidate.is_file():
                continue
            rel = candidate.relative_to(identity_home).as_posix()
            if _is_excluded(rel):
                continue
            seen.add(candidate)
            yield candidate


def _is_excluded(relative_path: str) -> bool:
    path = Path(relative_path)
    parts = tuple(part for part in path.parts if part)
    for idx in range(len(parts) - 1):
        if parts[idx] == "runtime" and parts[idx + 1] == "reports":
            return True
    if "sanitization-backups" in parts:
        return True
    for part in parts:
        if ".bak" in part:
            return True
    for pattern in EXCLUDED_GLOBS:
        if path.match(pattern):
            return True
    return False


def _count_token(value: str, token: str) -> int:
    if not token:
        return 0
    return value.count(token)


def _scan_file(path: Path, token: str) -> ResidueHit | None:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    count = _count_token(raw, token)
    if count <= 0:
        return None
    return ResidueHit(path=str(path), match_count=count)


def _apply_fix(path: Path, token: str, replacement: str) -> int:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    count = _count_token(raw, token)
    if count <= 0:
        return 0
    updated = raw.replace(token, replacement)
    if updated != raw:
        path.write_text(updated, encoding="utf-8")
    return count


def _resolve_identity_home(repo_root: Path, identity_id: str) -> Path:
    direct = (repo_root / ".identity" / identity_id).resolve()
    if direct.exists():
        return direct
    raise FileNotFoundError(f"identity_home_not_found:{identity_id}")


def _build_payload(
    *,
    identity_id: str,
    identity_home: Path,
    hits: list[ResidueHit],
    scanned_files: int,
    apply_enabled: bool,
    replaced_count: int,
) -> dict[str, object]:
    status = STATUS_PASS_REQUIRED if not hits else STATUS_FAIL_REQUIRED
    return {
        "identity_id": identity_id,
        "identity_home": str(identity_home),
        "path_residue_status": status,
        "forbidden_token": DEFAULT_FORBIDDEN_TOKEN,
        "replacement_token": DEFAULT_REPLACEMENT,
        "apply_enabled": apply_enabled,
        "replaced_count": replaced_count,
        "hit_count": len(hits),
        "total_match_count": sum(item.match_count for item in hits),
        "scanned_file_count": scanned_files,
        "hits": [item.__dict__ for item in hits],
        "scope": {
            "include_globs": list(CONTROL_PLANE_GLOBS),
            "exclude_globs": list(EXCLUDED_GLOBS),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan runtime control-plane files for forbidden '.agents/identity' residues. "
            "By default, historical evidence trees (runtime/reports) are excluded."
        )
    )
    parser.add_argument("--repo-root", default=".", help="Base repo root that contains .identity/<identity_id>")
    parser.add_argument("--identity-id", required=True, help="Identity id under .identity/")
    parser.add_argument("--apply", action="store_true", help="Apply token replacement in scoped control-plane files")
    parser.add_argument("--json-only", action="store_true", help="Print JSON payload only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    identity_home = _resolve_identity_home(repo_root=repo_root, identity_id=str(args.identity_id).strip())

    scanned_files = 0
    replaced_count = 0
    for candidate in _iter_control_plane_files(identity_home):
        scanned_files += 1
        if args.apply:
            replaced_count += _apply_fix(
                path=candidate,
                token=DEFAULT_FORBIDDEN_TOKEN,
                replacement=DEFAULT_REPLACEMENT,
            )

    hits: list[ResidueHit] = []
    for candidate in _iter_control_plane_files(identity_home):
        scanned_files += 0
        hit = _scan_file(candidate, DEFAULT_FORBIDDEN_TOKEN)
        if hit is not None:
            hits.append(hit)

    payload = _build_payload(
        identity_id=str(args.identity_id).strip(),
        identity_home=identity_home,
        hits=hits,
        scanned_files=scanned_files,
        apply_enabled=bool(args.apply),
        replaced_count=replaced_count,
    )
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"[{payload['path_residue_status']}] identity={payload['identity_id']} "
            f"hit_count={payload['hit_count']} scanned={payload['scanned_file_count']} replaced={payload['replaced_count']}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["path_residue_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
