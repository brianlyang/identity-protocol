#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from repo_root_resolution_common import resolve_protocol_repo_root


SIGNIFICANT_PREFIXES = (
    "identity/",
    "scripts/",
    "skills/",
    ".github/workflows/",
    "docs/references/",
)

SIGNIFICANT_FILES = {
    "README.md",
    "CHANGELOG.md",
}

# Governance snapshots are audited separately by validate_audit_snapshot_index.py
EXEMPT_PREFIXES = (
    "docs/governance/",
)


def _run_git(args: list[str], *, repo_root: Path) -> str:
    cp = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _changed_files(base: str, head: str, *, repo_root: Path) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"], repo_root=repo_root)
    return [x.strip() for x in out.splitlines() if x.strip()]


def _is_significant(path: str) -> bool:
    if path in SIGNIFICANT_FILES:
        return True
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return False
    return any(path.startswith(p) for p in SIGNIFICANT_PREFIXES)


def _resolve_commitish(ref: str, *, repo_root: Path) -> str:
    token = str(ref or "").strip()
    if not token:
        raise ValueError("commitish must be non-empty")
    return _run_git(["rev-parse", token], repo_root=repo_root)


def _resolve_range(base: str | None, head: str | None, *, repo_root: Path) -> tuple[str, str]:
    # Always normalize commit-ish inputs to concrete SHAs so backfill detection
    # cannot be tricked by symbolic literals like HEAD/HEAD~1 appearing in docs.
    resolved_head = _resolve_commitish(head or "HEAD", repo_root=repo_root)
    resolved_base = _resolve_commitish(base or "HEAD~1", repo_root=repo_root)
    return resolved_base, resolved_head


def _is_backfill_range(base: str, head: str, *, repo_root: Path) -> bool:
    """
    A historical range that does not include current HEAD.
    This is typical when validating delayed changelog linkage for already-landed commits.
    """
    current_head = _run_git(["rev-parse", "HEAD"], repo_root=repo_root)
    return head != current_head


def _has_backfill_changelog_link(changelog_path: Path, head: str) -> bool:
    """
    Accept explicit linkage by commit SHA token in changelog text.
    Keeps gate strict while allowing post-facto linkage for historical ranges.
    """
    try:
        text = changelog_path.read_text(encoding="utf-8")
    except Exception:
        return False
    short = head[:7]
    tokens = {
        head,
        short,
        f"`{head}`",
        f"`{short}`",
        f"({head})",
        f"({short})",
    }
    return any(tok in text for tok in tokens)


def _resolve_changelog_path(raw_path: str, *, repo_root: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (repo_root / candidate).resolve()


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate changelog update across a git range")
    ap.add_argument("--base", help="base commit SHA")
    ap.add_argument("--head", help="head commit SHA")
    ap.add_argument(
        "--changelog-path",
        default="CHANGELOG.md",
        help="path to changelog file (default: CHANGELOG.md)",
    )
    ap.add_argument(
        "--strict-range-only",
        action="store_true",
        help=(
            "disable historical backfill linkage allowance; require CHANGELOG to be "
            "modified in the exact --base..--head range"
        ),
    )
    ap.add_argument(
        "--repo-root",
        default="",
        help="protocol repo root; defaults to auto-detecting from this script path",
    )
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__).resolve()
    base, head = _resolve_range(args.base, args.head, repo_root=repo_root)
    files = _changed_files(base, head, repo_root=repo_root)
    if not files:
        print(f"[OK] no changed files in range {base}..{head}")
        return 0

    changelog_path = _resolve_changelog_path(args.changelog_path, repo_root=repo_root)
    try:
        changelog_rel = changelog_path.relative_to(repo_root).as_posix()
    except ValueError:
        changelog_rel = str(Path(args.changelog_path).as_posix())

    significant = [f for f in files if _is_significant(f)]
    changed_changelog = changelog_rel in files
    changelog_exists = changelog_path.exists()

    print(f"[INFO] repo root: {repo_root}")
    print(f"[INFO] range: {base}..{head}")
    print(f"[INFO] changed files: {len(files)}")
    print(f"[INFO] significant changed files: {len(significant)}")

    if not changelog_exists:
        print(f"[FAIL] changelog file missing: {changelog_path}")
        return 1

    if not significant:
        print("[OK] no significant protocol/runtime changes; changelog update not required")
        return 0

    if not changed_changelog:
        if (not args.strict_range_only) and _is_backfill_range(base, head, repo_root=repo_root):
            if _has_backfill_changelog_link(changelog_path, head):
                print(
                    "[OK] significant historical changes detected; "
                    "explicit changelog backfill linkage found for head commit"
                )
                print("validate_changelog_updated PASSED (historical backfill linkage)")
                return 0
        print(
            "[FAIL] significant changes detected but CHANGELOG.md was not updated in this range"
        )
        print("[INFO] significant files:")
        for p in significant:
            print(f"  - {p}")
        return 1

    print("[OK] significant changes detected and CHANGELOG.md updated")
    print("validate_changelog_updated PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
