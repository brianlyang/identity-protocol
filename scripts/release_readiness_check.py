#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print(f"[RUN] {' '.join(cmd)}")
    p = subprocess.run(cmd)
    if p.returncode != 0:
        print(f"[FAIL] command failed ({p.returncode}): {' '.join(cmd)}")
        return p.returncode
    return 0


def _git_rev(expr: str) -> str:
    p = subprocess.run(["git", "rev-parse", expr], check=True, capture_output=True, text=True)
    return p.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Run release-readiness validators in a deterministic order.")
    ap.add_argument("--identity-id", default="store-manager")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    args = ap.parse_args()

    base = args.base.strip() or _git_rev("HEAD~1")
    head = args.head.strip() or _git_rev("HEAD")
    identity_id = args.identity_id.strip()

    seq: list[list[str]] = [
        ["python3", "scripts/validate_identity_protocol.py"],
        ["python3", "scripts/validate_audit_snapshot_index.py"],
        ["python3", "scripts/validate_changelog_updated.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_release_metadata_sync.py"],
        ["python3", "scripts/validate_release_freeze_boundary.py", "--base", base, "--head", head],
        ["python3", "scripts/validate_identity_runtime_contract.py", "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_update_lifecycle.py", "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_safety.py", "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_install_provenance.py", "--identity-id", identity_id],
        ["python3", "scripts/validate_identity_ci_enforcement.py", "--identity-id", identity_id],
    ]

    for cmd in seq:
        rc = _run(cmd)
        if rc != 0:
            return rc

    print("[OK] release readiness checks PASSED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"[FAIL] subprocess error: {exc}", file=sys.stderr)
        raise SystemExit(2)
