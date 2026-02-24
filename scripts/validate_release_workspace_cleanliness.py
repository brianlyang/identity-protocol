#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ALLOWED_RUNTIME_PREFIXES = {
    "identity/runtime/examples/store-manager",
    "identity/runtime/IDENTITY_COMPILED.md",
}


def _git_status_lines() -> list[str]:
    p = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("git status --porcelain failed")
    return [ln.rstrip("\n") for ln in p.stdout.splitlines() if ln.strip()]


def _extract_path(status_line: str) -> str:
    # porcelain format: XY<space>path
    if len(status_line) < 4:
        return ""
    return status_line[3:].strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Fail release checks when runtime artifacts pollute worktree.")
    ap.add_argument("--strict", action="store_true", help="strict mode: disallow any identity/runtime changes")
    args = ap.parse_args()

    lines = _git_status_lines()
    offenders: list[str] = []
    for ln in lines:
        path = _extract_path(ln)
        if not path:
            continue
        if not path.startswith("identity/runtime/"):
            continue
        if args.strict:
            offenders.append(ln)
            continue
        allowed = False
        for prefix in ALLOWED_RUNTIME_PREFIXES:
            if path.startswith(prefix):
                allowed = True
                break
        if not allowed:
            offenders.append(ln)

    if offenders:
        print("[FAIL] runtime artifact pollution detected in workspace:")
        for x in offenders:
            print(" ", x)
        return 1

    print("[OK] release workspace cleanliness check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
