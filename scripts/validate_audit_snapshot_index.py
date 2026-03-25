#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from repo_root_resolution_common import resolve_protocol_repo_root

# Accept both classic and strategy-suffixed snapshot names:
# - audit-snapshot-YYYY-MM-DD.md
# - audit-snapshot-YYYY-MM-DD-<suffix>.md
SNAPSHOT_RE = re.compile(r"^audit-snapshot-(\d{4}-\d{2}-\d{2})(?:-(.+))?\.md$")
SNAPSHOT_DOC_REF_RE = re.compile(
    r"`(docs/governance/(audit-snapshot-\d{4}-\d{2}-\d{2}(?:-[^`/]+)?\.md))`"
)
REQUIRED_INDEX_MARKERS = (
    "Current-state authoritative set",
    "identity/protocol/mappings/stream-doc-registry.current.yaml",
    "docs/release/identity-v1.6x-release-closure-summary.md",
    "docs/governance/identity-v1.6x-release-closure-governance.md",
    "docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md",
    "Historical `docs/release/v1-roadmap.md` and `docs/release/v1.0.0-release-notes.md` remain archival only",
    "All audit-snapshot entries listed in this section are archival snapshots only.",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate audit snapshot index governance and archival/current boundary markers.")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    root = repo_root / "docs/governance"
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

    snapshots: list[tuple[datetime, int, str, Path]] = []
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
        # Prefer suffixed snapshots on the same date because they are often
        # closure-focused extensions of the base daily snapshot.
        suffix = m.group(2) or ""
        has_suffix = 1 if suffix else 0
        snapshots.append((dt, has_suffix, child.name, child))

    if not snapshots:
        print("[FAIL] no audit snapshot files found under docs/governance")
        return 1

    latest = sorted(snapshots, key=lambda x: (x[0], x[1], x[2]))[-1][3]
    index_text = index_path.read_text(encoding="utf-8")
    failures: list[str] = []

    for marker in REQUIRED_INDEX_MARKERS:
        if marker not in index_text:
            failures.append(f"required_index_marker_missing:{marker}")

    snapshot_refs = SNAPSHOT_DOC_REF_RE.findall(index_text)
    referenced_snapshot_docs = [doc for doc, _name in snapshot_refs]
    ref_counter = Counter(referenced_snapshot_docs)
    duplicate_refs = sorted(doc for doc, count in ref_counter.items() if count > 1)
    if duplicate_refs:
        failures.append("duplicate_snapshot_refs:" + ",".join(duplicate_refs))

    actual_snapshot_docs = sorted(
        f"docs/governance/{path.name}"
        for _dt, _has_suffix, _name, path in sorted(snapshots, key=lambda x: (x[0], x[1], x[2]))
    )
    if f"docs/governance/{latest.name}" not in referenced_snapshot_docs:
        failures.append(f"latest_snapshot_not_referenced:{latest.name}")

    missing_snapshot_refs = sorted(set(actual_snapshot_docs) - set(referenced_snapshot_docs))
    extra_snapshot_refs = sorted(set(referenced_snapshot_docs) - set(actual_snapshot_docs))
    if missing_snapshot_refs:
        failures.append("missing_snapshot_refs:" + ",".join(missing_snapshot_refs))
    if extra_snapshot_refs:
        failures.append("extra_snapshot_refs:" + ",".join(extra_snapshot_refs))

    if failures:
        print("[FAIL] audit snapshot index governance drift detected")
        for item in failures:
            print(f" - {item}")
        return 1

    print(f"[OK] latest snapshot referenced in index: {latest.name}")
    print(f"[OK] snapshot refs classified and complete: {len(actual_snapshot_docs)}")
    print("validate_audit_snapshot_index PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
