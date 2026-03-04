#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_REQUIRED_DIRS = (
    "outbox-to-protocol",
    "evidence-index",
    "upgrade-proposals",
)

DEFAULT_ACTIVITY_DIRS = (
    "outbox-to-protocol",
    "evidence-index",
    "upgrade-proposals",
    "issues",
    "roundtables",
    "protocol-vendor-intel",
    "business-partner-intel",
    "vendor-intel",
    "review-notes",
)

STRICT_OPERATIONS = {"activate", "update", "mutation", "readiness", "e2e", "ci", "validate"}


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_feedback_root(pack_path: Path, feedback_root: str = "") -> Path:
    if str(feedback_root or "").strip():
        return Path(feedback_root).expanduser().resolve()
    return (pack_path / "runtime" / "protocol-feedback").resolve()


def canonical_dirs(feedback_root: Path) -> dict[str, Path]:
    outbox_dir = (feedback_root / "outbox-to-protocol").resolve()
    evidence_dir = (feedback_root / "evidence-index").resolve()
    upgrade_dir = (feedback_root / "upgrade-proposals").resolve()
    index_path = (evidence_dir / "INDEX.md").resolve()
    return {
        "outbox_dir": outbox_dir,
        "evidence_dir": evidence_dir,
        "upgrade_dir": upgrade_dir,
        "index_path": index_path,
    }


def collect_activity_refs(
    feedback_root: Path,
    *,
    activity_dirs: tuple[str, ...] = DEFAULT_ACTIVITY_DIRS,
    max_refs: int = 200,
) -> list[str]:
    refs: list[str] = []
    for sub in activity_dirs:
        d = (feedback_root / sub).resolve()
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if not p.is_file():
                continue
            refs.append(str(p))
            if len(refs) >= max_refs:
                return refs
    return refs


def list_feedback_files(feedback_root: Path, *, max_refs: int = 400) -> list[Path]:
    if not feedback_root.exists():
        return []
    rows: list[Path] = []
    for p in sorted(feedback_root.rglob("*")):
        if p.is_file():
            rows.append(p.resolve())
            if len(rows) >= max_refs:
                break
    return rows


def is_strict_operation(operation: str) -> bool:
    return str(operation or "").strip().lower() in STRICT_OPERATIONS


def rel_to_feedback_root(path: Path, feedback_root: Path) -> str:
    try:
        return path.resolve().relative_to(feedback_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def ensure_index_linkage(index_path: Path, refs: list[str], *, section_title: str = "Protocol feedback linkage") -> tuple[Path, bool]:
    refs = [str(x).strip() for x in refs if str(x).strip()]
    index_path.parent.mkdir(parents=True, exist_ok=True)
    existing = ""
    if index_path.exists():
        existing = index_path.read_text(encoding="utf-8", errors="ignore")
    updated = existing
    if not existing.strip():
        updated = "# Protocol Feedback Evidence Index\n\n"
    low = updated.lower()
    missing: list[str] = []
    for ref in refs:
        token = ref.lower()
        if token not in low:
            missing.append(ref)
    if missing:
        block_lines = [f"## {section_title} ({utc_now_z()})", ""]
        block_lines.extend([f"- {x}" for x in missing])
        block_lines.append("")
        updated = updated.rstrip() + "\n\n" + "\n".join(block_lines) + "\n"
        index_path.write_text(updated, encoding="utf-8")
    recheck = index_path.read_text(encoding="utf-8", errors="ignore").lower()
    linked = all(str(x).strip().lower() in recheck for x in refs)
    return index_path, linked
