#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


VALIDATOR_SCRIPTS: tuple[str, ...] = (
    "scripts/validate_identity_experience_feedback_governance.py",
    "scripts/validate_identity_capability_arbitration.py",
    "scripts/validate_identity_dialogue_content.py",
    "scripts/validate_identity_dialogue_cross_validation.py",
    "scripts/validate_identity_dialogue_result_support.py",
    "scripts/validate_identity_ci_enforcement.py",
)


def _run(cmd: list[str], repo_root: Path) -> int:
    print(f"[RUN] {' '.join(shlex.quote(part) for part in cmd)}")
    proc = subprocess.run(cmd, cwd=str(repo_root), check=False)
    if proc.returncode != 0:
        print(f"[FAIL] rc={proc.returncode} command={' '.join(shlex.quote(part) for part in cmd)}")
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run dialogue/feedback capability validators as one delegated bundle "
            "to reduce direct validate coupling density on identity_creator entrypoints."
        )
    )
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--identity-id", required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    for rel in VALIDATOR_SCRIPTS:
        cmd = ["python3", rel, "--catalog", args.catalog, "--identity-id", args.identity_id]
        rc = _run(cmd, repo_root)
        if rc != 0:
            return rc
    print("[PASS] identity dialogue/feedback validator bundle completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
