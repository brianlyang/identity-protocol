#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

CANONICAL_ERROR_CODE_TOKEN_RE = re.compile(
    r"(?<![A-Z0-9-])(IP-[A-Z0-9]+(?:-[A-Z0-9]+)+)(?![A-Z0-9-])"
)
PARTIAL_ERROR_CODE_PREFIX_RE = re.compile(
    r"(?<![A-Z0-9-])(IP-[A-Z0-9]+(?:-[A-Z0-9]+)*-)(?![A-Z0-9-])"
)

TRACKED_VALIDATOR_METRIC_SCOPE = "tracked_validate_scripts_only"
TRACKED_ERROR_CODE_METRIC_SCOPE = "tracked_python_scripts_canonical_tokens_only"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return path.read_text(encoding="utf-8", errors="ignore")


def normalize_error_code_family(code: str) -> str:
    value = str(code or "").strip()
    if not value:
        return ""
    return re.sub(r"-\d+$", "", value)


def extract_canonical_error_codes(text: str) -> set[str]:
    return {str(match).strip() for match in CANONICAL_ERROR_CODE_TOKEN_RE.findall(str(text or "")) if str(match).strip()}


def extract_partial_error_code_prefixes(text: str) -> set[str]:
    raw = str(text or "")
    canonical = extract_canonical_error_codes(raw)
    partials = {
        str(match).strip()
        for match in PARTIAL_ERROR_CODE_PREFIX_RE.findall(raw)
        if str(match).strip()
    }
    return {token for token in partials if token not in canonical}


def _git_list(repo_root: Path, *args: str) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def tracked_repo_files(repo_root: Path, *patterns: str) -> list[Path]:
    files = sorted(
        {
            (repo_root / rel).resolve()
            for rel in _git_list(repo_root, "ls-files", "--", *patterns)
            if rel.strip()
        }
    )
    if files:
        return [path for path in files if path.exists() and path.is_file()]

    fallback: set[Path] = set()
    for pattern in patterns:
        fallback.update(path.resolve() for path in repo_root.glob(pattern) if path.is_file())
    return sorted(fallback)


def untracked_repo_files(repo_root: Path, *patterns: str) -> list[Path]:
    files = sorted(
        {
            (repo_root / rel).resolve()
            for rel in _git_list(repo_root, "ls-files", "--others", "--exclude-standard", "--", *patterns)
            if rel.strip()
        }
    )
    return [path for path in files if path.exists() and path.is_file()]


def tracked_validator_script_paths(repo_root: Path) -> list[Path]:
    return tracked_repo_files(repo_root, "scripts/validate_*.py")


def untracked_validator_script_paths(repo_root: Path) -> list[Path]:
    return untracked_repo_files(repo_root, "scripts/validate_*.py")


def tracked_python_script_paths(repo_root: Path) -> list[Path]:
    return tracked_repo_files(repo_root, "scripts/*.py")


def collect_governed_error_code_inventory(repo_root: Path) -> dict[str, object]:
    tracked_script_paths = tracked_python_script_paths(repo_root)
    codes: set[str] = set()
    families: set[str] = set()
    ignored_partial_prefixes: set[str] = set()
    for path in tracked_script_paths:
        text = read_text(path)
        codes.update(extract_canonical_error_codes(text))
        ignored_partial_prefixes.update(extract_partial_error_code_prefixes(text))
    for code in codes:
        family = normalize_error_code_family(code)
        if family:
            families.add(family)
    return {
        "tracked_script_paths": tracked_script_paths,
        "codes": sorted(codes),
        "families": sorted(families),
        "ignored_partial_prefixes": sorted(ignored_partial_prefixes),
    }
