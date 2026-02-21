#!/usr/bin/env python3
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

SNAPSHOT_RE = re.compile(r"^audit-snapshot-(\d{4}-\d{2}-\d{2})\.md$")


def main() -> int:
    root = Path("docs/governance")
    if not root.exists():
        print("[FAIL] missing docs/governance directory")
        return 1

    index_path = root / "AUDIT_SNAPSHOT_INDEX.md"
    policy_path = root / "audit-snapshot-policy-v1.2.11.md"
    template_path = root / "templates" / "audit-snapshot-template.md"

    for p in [index_path, policy_path, template_path]:
        if not p.exists():
            print(f"[FAIL] required governance file missing: {p}")
            return 1

    snapshots: list[tuple[datetime, Path]] = []
    for child in root.iterdir():
        if not child.is_file():
            continue
        m = SNAPSHOT_RE.match(child.name)
        if not m:
            continue
        try:
            dt = datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            print(f"[FAIL] invalid snapshot date in filename: {child.name}")
            return 1
        snapshots.append((dt, child))

    if not snapshots:
        print("[FAIL] no audit snapshot files found under docs/governance")
        return 1

    latest = sorted(snapshots, key=lambda x: x[0])[-1][1]
    index_text = index_path.read_text(encoding="utf-8")

    if latest.name not in index_text:
        print(f"[FAIL] latest snapshot not referenced in index: {latest.name}")
        return 1

    print(f"[OK] latest snapshot referenced in index: {latest.name}")
    print("validate_audit_snapshot_index PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
