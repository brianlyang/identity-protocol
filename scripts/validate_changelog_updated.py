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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate changelog update across a git range")
    ap.add_argument("--base", help="base commit SHA")
    ap.add_argument("--head", help="head commit SHA")
    ap.add_argument(
        "--changelog-path",
        default="CHANGELOG.md",
        help="path to changelog file (default: CHANGELOG.md)",
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
