#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


INDEX_PATH = Path("docs/governance/AUDIT_SNAPSHOT_INDEX.md")
CANONICAL_DOC_PATTERN = re.compile(r"docs/governance/identity-protocol-strengthening-handoff-v\d+\.\d+\.\d+\.md")

CORE_FILES = (
    ".github/workflows/_identity-required-gates.yml",
    "scripts/e2e_smoke_test.sh",
    "scripts/release_readiness_check.py",
    "scripts/report_three_plane_status.py",
    "scripts/full_identity_protocol_scan.py",
    "scripts/identity_creator.py",
    "scripts/execute_identity_upgrade.py",
    "scripts/create_identity_pack.py",
    "scripts/identity_installer.py",
)

CORE_PREFIXES = (
    "scripts/validate_identity_",
    "scripts/validate_protocol_",
)


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(["git", *args], capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    resolved_head = (head or "").strip() or _run_git(["rev-parse", "HEAD"])
    resolved_base = (base or "").strip() or _run_git(["rev-parse", "HEAD~1"])
    return resolved_base, resolved_head


def _changed_files(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def _canonical_handoff_path() -> str:
    if not INDEX_PATH.exists():
        return ""
    text = INDEX_PATH.read_text(encoding="utf-8")
    matches = CANONICAL_DOC_PATTERN.findall(text)
    if not matches:
        return ""
    return sorted(set(matches))[-1]


def _is_core_file(path: str) -> bool:
    if path in CORE_FILES:
        return True
    return any(path.startswith(p) for p in CORE_PREFIXES)


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce protocol core-change -> canonical handoff doc coupling.")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="")
    args = ap.parse_args()

    try:
        base, head = _resolve_range(args.base, args.head)
        changed = _changed_files(base, head)
    except Exception as exc:
        print(f"[FAIL] IP-SSOT-006 unable to inspect git range: {exc}")
        return 1

    if not changed:
        print(f"[OK] no changed files in range {base}..{head}")
        return 0

    core_changed = [p for p in changed if _is_core_file(p)]
    if not core_changed:
        print("[OK] no protocol-core changes detected; handoff coupling not required")
        return 0

    canonical = _canonical_handoff_path()
    if not canonical:
        print("[FAIL] IP-SSOT-006 canonical handoff path unresolved from AUDIT_SNAPSHOT_INDEX.md")
        return 1

    if canonical not in changed:
        print("[FAIL] IP-SSOT-006 protocol-core changes require canonical handoff doc update in same range")
        print(f"       missing_changed_file={canonical}")
        print("       core_changed_files:")
        for p in core_changed[:50]:
            print(f"         - {p}")
        return 1

    print("[OK] protocol handoff coupling validated")
    print(f"     range={base}..{head}")
    print(f"     canonical_handoff_changed={canonical}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

