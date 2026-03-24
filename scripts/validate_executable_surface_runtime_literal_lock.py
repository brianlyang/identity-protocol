#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_EXECUTABLE_SURFACE_RUNTIME_LITERAL_LOCK = "IP-EXLIT-005"

DEFAULT_REPO_SCAN_GLOBS: tuple[str, ...] = (
    "scripts/**/*.py",
    "scripts/**/*.sh",
    ".github/workflows/*.yml",
)
DEFAULT_PACK_SCRIPT_GLOBS: tuple[str, ...] = (
    "scripts/**/*.py",
    "scripts/**/*.sh",
)

UUID_LITERAL_RE = re.compile(
    r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}(?![0-9A-Fa-f])"
)
ROLLOUT_LITERAL_RE = re.compile(
    r"rollout-20\d{2}-\d{2}-\d{2}T\d{2}(?:[-:]\d{2}){2}(?:Z)?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ScanFile:
    path: Path
    display_path: str
    origin: str


@dataclass(frozen=True)
class Violation:
    kind: str
    path: str
    line: int
    match: str
    line_excerpt: str
    origin: str


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False) if json_only else json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"catalog root must be mapping: {path}")
    return raw


def _normalize_globs(values: list[str] | None, defaults: tuple[str, ...]) -> list[str]:
    rows = [str(v or "").strip() for v in (values or []) if str(v or "").strip()]
    return rows or list(defaults)


def _iter_repo_scan_files(repo_root: Path, globs: list[str]) -> list[ScanFile]:
    files: dict[str, ScanFile] = {}
    for pattern in globs:
        for path in repo_root.glob(pattern):
            if not path.is_file():
                continue
            resolved = path.resolve()
            rel = resolved.relative_to(repo_root.resolve()).as_posix()
            files[resolved.as_posix()] = ScanFile(path=resolved, display_path=rel, origin="repo")
    return [files[key] for key in sorted(files.keys())]


def _iter_active_pack_scan_files(catalog_path: Path, pack_script_globs: list[str]) -> tuple[list[str], list[ScanFile]]:
    doc = _load_catalog(catalog_path)
    rows = [row for row in (doc.get("identities") or []) if isinstance(row, dict)]
    identities: list[str] = []
    files: dict[str, ScanFile] = {}
    for row in rows:
        identity_id = str(row.get("id", "")).strip()
        if not identity_id:
            continue
        if str(row.get("status", "")).strip().lower() != "active":
            continue
        profile = str(row.get("profile", "")).strip().lower()
        runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
        if profile == "fixture" or runtime_mode == "demo_only":
            continue
        pack_raw = str(row.get("pack_path", "")).strip()
        if not pack_raw:
            continue
        pack_root = Path(pack_raw).expanduser().resolve()
        if not pack_root.exists():
            continue
        identities.append(identity_id)
        for pattern in pack_script_globs:
            for path in pack_root.glob(pattern):
                if not path.is_file():
                    continue
                resolved = path.resolve()
                rel = resolved.relative_to(pack_root).as_posix()
                display = f"pack:{identity_id}:{rel}"
                files[resolved.as_posix()] = ScanFile(path=resolved, display_path=display, origin="active_pack")
    return sorted(set(identities)), [files[key] for key in sorted(files.keys())]


def _iter_extra_scan_files(extra_paths: list[str] | None) -> list[ScanFile]:
    files: dict[str, ScanFile] = {}
    for raw in extra_paths or []:
        token = str(raw or "").strip()
        if not token:
            continue
        path = Path(token).expanduser().resolve()
        if not path.is_file():
            continue
        files[path.as_posix()] = ScanFile(path=path, display_path=path.as_posix(), origin="extra")
    return [files[key] for key in sorted(files.keys())]


def _line_excerpt(line: str, *, width: int = 220) -> str:
    text = str(line or "").strip()
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def _scan_file(scan_file: ScanFile) -> list[Violation]:
    try:
        lines = scan_file.path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return [
            Violation(
                kind="scan_read_failed",
                path=scan_file.display_path,
                line=0,
                match="",
                line_excerpt="",
                origin=scan_file.origin,
            )
        ]

    violations: list[Violation] = []
    for lineno, line in enumerate(lines, start=1):
        line_hits: list[Violation] = []
        for match in UUID_LITERAL_RE.finditer(line):
            line_hits.append(
                Violation(
                    kind="fixed_uuid_literal",
                    path=scan_file.display_path,
                    line=lineno,
                    match=match.group(0),
                    line_excerpt=_line_excerpt(line),
                    origin=scan_file.origin,
                )
            )
        for match in ROLLOUT_LITERAL_RE.finditer(line):
            line_hits.append(
                Violation(
                    kind="fixed_rollout_path_literal",
                    path=scan_file.display_path,
                    line=lineno,
                    match=match.group(0),
                    line_excerpt=_line_excerpt(line),
                    origin=scan_file.origin,
                )
            )
        seen: set[tuple[str, str]] = set()
        for item in line_hits:
            key = (item.kind, item.match)
            if key in seen:
                continue
            seen.add(key)
            violations.append(item)
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-close when executable protocol surfaces embed fixed runtime thread/session/rollout literals.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parent.parent),
        help="protocol repo root whose executable surfaces will be scanned",
    )
    parser.add_argument(
        "--scan-glob",
        action="append",
        default=[],
        help="override/extend repo executable scan globs; defaults to protocol scripts/workflows only",
    )
    parser.add_argument(
        "--extra-scan-file",
        action="append",
        default=[],
        help="optional explicit executable files outside repo globs",
    )
    parser.add_argument("--catalog", default="", help="optional runtime catalog for active pack script scanning")
    parser.add_argument(
        "--include-active-pack-scripts",
        action="store_true",
        help="also scan active non-fixture pack-local scripts from the provided catalog",
    )
    parser.add_argument(
        "--pack-scan-glob",
        action="append",
        default=[],
        help="override/extend active-pack script scan globs; defaults to pack-local scripts/**/*.py and scripts/**/*.sh",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    repo_globs = _normalize_globs(args.scan_glob, DEFAULT_REPO_SCAN_GLOBS)
    pack_globs = _normalize_globs(args.pack_scan_glob, DEFAULT_PACK_SCRIPT_GLOBS)
    catalog_path = Path(args.catalog).expanduser().resolve() if str(args.catalog or "").strip() else None

    stale_reasons: list[str] = []
    repo_files: list[ScanFile] = []
    pack_files: list[ScanFile] = []
    extra_files = _iter_extra_scan_files(args.extra_scan_file)
    active_pack_identity_ids: list[str] = []

    if not repo_root.exists():
        stale_reasons.append("repo_root_not_found")
    else:
        repo_files = _iter_repo_scan_files(repo_root, repo_globs)

    if args.include_active_pack_scripts:
        if catalog_path is None:
            stale_reasons.append("catalog_required_for_active_pack_scan")
        elif not catalog_path.exists():
            stale_reasons.append("catalog_not_found_for_active_pack_scan")
        else:
            try:
                active_pack_identity_ids, pack_files = _iter_active_pack_scan_files(catalog_path, pack_globs)
            except Exception as exc:
                stale_reasons.append(f"catalog_active_pack_scan_failed:{type(exc).__name__}")

    scan_files_dict: dict[str, ScanFile] = {}
    for item in [*repo_files, *pack_files, *extra_files]:
        scan_files_dict[item.path.as_posix()] = item
    scan_files = [scan_files_dict[key] for key in sorted(scan_files_dict.keys())]

    violations: list[Violation] = []
    for scan_file in scan_files:
        violations.extend(_scan_file(scan_file))

    stale_reasons.extend(f"{item.kind}:{item.path}:{item.line}" for item in violations)
    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload = {
        "executable_surface_runtime_literal_lock_status": status,
        "error_code": ERR_EXECUTABLE_SURFACE_RUNTIME_LITERAL_LOCK if status == STATUS_FAIL_REQUIRED else "",
        "repo_root": str(repo_root),
        "catalog_path": str(catalog_path) if catalog_path else "",
        "include_active_pack_scripts": bool(args.include_active_pack_scripts),
        "repo_scan_globs": repo_globs,
        "pack_scan_globs": pack_globs if args.include_active_pack_scripts else [],
        "active_pack_identity_ids": active_pack_identity_ids,
        "repo_scan_file_count": len(repo_files),
        "active_pack_scan_file_count": len(pack_files),
        "extra_scan_file_count": len(extra_files),
        "scan_file_count": len(scan_files),
        "scan_files": [item.display_path for item in scan_files],
        "violation_count": len(violations),
        "violations": [
            {
                "kind": item.kind,
                "path": item.path,
                "line": item.line,
                "match": item.match,
                "line_excerpt": item.line_excerpt,
                "origin": item.origin,
            }
            for item in violations
        ],
        "stale_reasons": stale_reasons,
        "semantic_boundary": {
            "forbidden_surfaces": [
                "protocol repo scripts/**/*.py",
                "protocol repo scripts/**/*.sh",
                "protocol repo .github/workflows/*.yml",
                "active pack-local scripts/**/*.py when catalog-backed scan enabled",
                "active pack-local scripts/**/*.sh when catalog-backed scan enabled",
            ],
            "out_of_scope_surfaces": [
                "docs/**",
                "review ledgers",
                "runtime evidence under runtime/**",
                "catalog/session truth files",
            ],
            "forbidden_literal_kinds": [
                "fixed UUID/thread/session-like runtime literals",
                "fixed rollout-date sidecar path literals",
            ],
            "required_replacement": "generate runtime thread/session/rollout identifiers dynamically at execution time",
        },
    }

    _emit(payload, json_only=bool(args.json_only))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
