#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


INDEX_PATH = Path("docs/governance/AUDIT_SNAPSHOT_INDEX.md")
CANONICAL_DOC_PATTERN = re.compile(r"docs/governance/identity-protocol-strengthening-handoff-v\d+\.\d+\.\d+\.md")

INDEX_REQUIRED_MARKERS = (
    "Canonical SSOT rule for protocol-strengthening handoff",
    "Any `artifacts/` mirror is non-normative evidence only.",
)

CANONICAL_REQUIRED_MARKERS = (
    "Status:",
    "Scope guardrails",
    "Protocol layer only",
)

ARTIFACT_NORMATIVE_MARKERS = (
    "Status: Canonical",
    "single source of truth",
    "SSOT",
    "must execute",
    "normative requirement",
)


def _find_canonical_doc(index_text: str) -> Path | None:
    matches = CANONICAL_DOC_PATTERN.findall(index_text)
    if not matches:
        return None
    # prefer latest version by lexical sort (vX.Y.Z pattern is zero-padded semantics enough for our current use).
    rel = sorted(set(matches))[-1]
    return Path(rel)


def _contains_absolute_user_path(text: str) -> bool:
    return bool(re.search(r"/Users/[^/\\s]+/", text))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol SSOT source boundary: handoff is canonical, artifacts are evidence-only.")
    ap.add_argument(
        "--require-canonical-changed",
        action="store_true",
        help="reserved for future wiring; no-op in this validator (use validate_protocol_handoff_coupling.py for diff-range checks)",
    )
    args = ap.parse_args()

    if not INDEX_PATH.exists():
        print(f"[FAIL] IP-SSOT-001 missing index file: {INDEX_PATH}")
        return 1

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    for marker in INDEX_REQUIRED_MARKERS:
        if marker not in index_text:
            print(f"[FAIL] IP-SSOT-001 index missing required SSOT marker: {marker}")
            return 1

    canonical = _find_canonical_doc(index_text)
    if canonical is None:
        print("[FAIL] IP-SSOT-002 canonical handoff document not referenced in index")
        return 1
    if not canonical.exists():
        print(f"[FAIL] IP-SSOT-002 canonical handoff document missing: {canonical}")
        return 1

    handoff_text = canonical.read_text(encoding="utf-8")
    for marker in CANONICAL_REQUIRED_MARKERS:
        if marker not in handoff_text:
            print(f"[FAIL] IP-SSOT-003 canonical handoff missing required marker: {marker}")
            return 1
    if _contains_absolute_user_path(handoff_text):
        print(f"[FAIL] IP-SSOT-005 canonical handoff contains user absolute path: {canonical}")
        return 1

    # Guard against accidentally promoting artifacts to normative source.
    for root in [Path("docs"), Path("identity/runtime")]:
        if not root.exists():
            continue
        for p in root.rglob("*artifacts*/*.md"):
            text = p.read_text(encoding="utf-8", errors="ignore")
            hit = next((m for m in ARTIFACT_NORMATIVE_MARKERS if m in text), "")
            if hit:
                print(f"[FAIL] IP-SSOT-004 artifact doc contains normative marker ({hit}): {p}")
                return 1

    print("[OK] protocol SSOT source boundary validated")
    print(f"     canonical_handoff={canonical}")
    print("     artifacts_policy=evidence_only_non_normative")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

