#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

PROTOCOL_REPO_RUNTIME_SHADOW_IGNORE_PATTERNS: tuple[str, ...] = (
    ".identity/",
    ".identity-protocol/",
    ".codex/",
    ".tmp/",
    ".IDENTITY.run__*.md",
)

PROTOCOL_REPO_RUNTIME_SHADOW_SELECTOR_REQUIRED_TOKENS: tuple[str, ...] = (
    "Prefer parent project root when protocol repo is checked out as a subdirectory",
    "This keeps runtime artifacts outside",
    "protocol_root and avoids IP-PATH-001 boundary failures.",
    'if [[ "$(basename "${REPO_ROOT}")" == "identity-protocol-local" ]]; then',
)


def load_gitignore_patterns(path: Path) -> set[str]:
    if not path.exists() or not path.is_file():
        return set()
    patterns: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line)
    return patterns
