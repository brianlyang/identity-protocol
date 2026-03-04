#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


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


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(["git", *args], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _changed_files(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def _is_significant(path: str) -> bool:
    if path in SIGNIFICANT_FILES:
        return True
    if any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return False
    return any(path.startswith(p) for p in SIGNIFICANT_PREFIXES)


def _resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    if base and head:
        return base, head
    # fallback for local/dev usage
    resolved_head = head or _run_git(["rev-parse", "HEAD"])
    resolved_base = base or _run_git(["rev-parse", "HEAD~1"])
    return resolved_base, resolved_head


def _is_backfill_range(base: str, head: str) -> bool:
    """
    A historical range that does not include current HEAD.
    This is typical when validating delayed changelog linkage for already-landed commits.
    """
    current_head = _run_git(["rev-parse", "HEAD"])
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
    args = ap.parse_args()

    base, head = _resolve_range(args.base, args.head)
    files = _changed_files(base, head)
    if not files:
        print(f"[OK] no changed files in range {base}..{head}")
        return 0

    significant = [f for f in files if _is_significant(f)]
    changed_changelog = args.changelog_path in files
    changelog_exists = Path(args.changelog_path).exists()

    print(f"[INFO] range: {base}..{head}")
    print(f"[INFO] changed files: {len(files)}")
    print(f"[INFO] significant changed files: {len(significant)}")

    if not changelog_exists:
        print(f"[FAIL] changelog file missing: {args.changelog_path}")
        return 1

    if not significant:
        print("[OK] no significant protocol/runtime changes; changelog update not required")
        return 0

    if not changed_changelog:
        if (not args.strict_range_only) and _is_backfill_range(base, head):
            changelog_path = Path(args.changelog_path)
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
