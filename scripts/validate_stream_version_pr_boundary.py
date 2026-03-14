#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_STREAM_ANCHOR_MISSING = "IP-STREAM-PR-001"
ERR_MULTI_STREAM_MIXED = "IP-STREAM-PR-002"
ERR_STREAM_DOC_PAIR_INCOMPLETE = "IP-STREAM-PR-003"
ERR_STREAM_REGISTRY_INVALID = "IP-STREAM-PR-004"

CORE_CHANGE_PREFIXES: tuple[str, ...] = (
    "scripts/",
    "identity/protocol/",
    ".github/workflows/",
)
STREAM_VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def _run_git(args: list[str]) -> str:
    cp = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr.strip() or f"git {' '.join(args)} failed")
    return cp.stdout.strip()


def _resolve_range(base: str | None, head: str | None) -> tuple[str, str]:
    resolved_head = str(head or "").strip() or _run_git(["rev-parse", "HEAD"])
    resolved_base = str(base or "").strip() or _run_git(["rev-parse", "HEAD~1"])
    return resolved_base, resolved_head


def _changed_files(base: str, head: str) -> list[str]:
    out = _run_git(["diff", "--name-only", f"{base}..{head}"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _load_stream_registry(path: Path) -> list[dict[str, str]]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = doc.get("stream_docs")
    if not isinstance(rows, list):
        raise ValueError("stream_docs missing or invalid in stream registry")
    out: list[dict[str, str]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"stream_docs[{idx}] must be object")
        stream_version = str(row.get("stream_version", "")).strip()
        governance_doc = str(row.get("governance_doc", "")).strip()
        review_doc = str(row.get("review_doc", "")).strip()
        if not stream_version or not STREAM_VERSION_PATTERN.fullmatch(stream_version):
            raise ValueError(f"invalid stream_version at index {idx}: {stream_version!r}")
        if not governance_doc or not review_doc:
            raise ValueError(f"missing governance/review docs at index {idx}")
        out.append(
            {
                "stream_version": stream_version,
                "governance_doc": governance_doc,
                "review_doc": review_doc,
            }
        )
    return out


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate one-stream-per-PR governance boundary.")
    ap.add_argument("--base", default="", help="git base sha (default: HEAD~1)")
    ap.add_argument("--head", default="", help="git head sha (default: HEAD)")
    ap.add_argument(
        "--stream-registry",
        default="identity/protocol/mappings/stream-doc-registry.current.yaml",
        help="stream registry entry file",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    base, head = _resolve_range(args.base, args.head)
    changed = _changed_files(base, head)
    core_changed = [path for path in changed if any(path.startswith(prefix) for prefix in CORE_CHANGE_PREFIXES)]

    payload: dict[str, Any] = {
        "stream_version_pr_boundary_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "base": base,
        "head": head,
        "changed_file_count": len(changed),
        "changed_files": changed,
        "core_changed_file_count": len(core_changed),
        "core_changed_files": core_changed,
        "stream_registry_entry": args.stream_registry,
        "stream_registry_resolved_path": "",
        "touched_stream_versions": [],
        "touched_stream_docs": [],
        "missing_stream_docs": [],
        "stale_reasons": [],
    }

    if not changed:
        payload["stream_version_pr_boundary_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["no_changed_files_in_range"]
        _emit(payload, json_only=args.json_only)
        return 0

    registry_entry = Path(args.stream_registry).expanduser().resolve()
    payload["stream_registry_resolved_path"] = str(registry_entry)
    if not registry_entry.exists():
        payload["stream_version_pr_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM_REGISTRY_INVALID
        payload["stale_reasons"] = ["stream_registry_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        rows = _load_stream_registry(registry_entry)
    except Exception as exc:
        payload["stream_version_pr_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM_REGISTRY_INVALID
        payload["stale_reasons"] = [f"stream_registry_invalid:{exc}"]
        _emit(payload, json_only=args.json_only)
        return 1

    doc_to_stream: dict[str, tuple[str, str]] = {}
    for row in rows:
        stream_version = row["stream_version"]
        doc_to_stream[row["governance_doc"]] = (stream_version, "governance")
        doc_to_stream[row["review_doc"]] = (stream_version, "review")

    touched_stream_versions: dict[str, set[str]] = {}
    touched_docs: list[str] = []
    for path in changed:
        if path not in doc_to_stream:
            continue
        stream_version, doc_kind = doc_to_stream[path]
        touched_stream_versions.setdefault(stream_version, set()).add(doc_kind)
        touched_docs.append(path)

    payload["touched_stream_versions"] = sorted(touched_stream_versions)
    payload["touched_stream_docs"] = sorted(touched_docs)

    if core_changed and not touched_stream_versions:
        payload["stream_version_pr_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM_ANCHOR_MISSING
        payload["stale_reasons"] = ["core_changes_missing_stream_docs"]
        _emit(payload, json_only=args.json_only)
        return 1

    if not touched_stream_versions:
        payload["stream_version_pr_boundary_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["no_stream_docs_changed"]
        _emit(payload, json_only=args.json_only)
        return 0

    if len(touched_stream_versions) > 1:
        payload["stream_version_pr_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MULTI_STREAM_MIXED
        payload["stale_reasons"] = ["multiple_stream_versions_changed_in_single_range"]
        _emit(payload, json_only=args.json_only)
        return 1

    stream_version = next(iter(touched_stream_versions))
    touched_kinds = touched_stream_versions[stream_version]
    missing_docs: list[str] = []
    if "governance" not in touched_kinds:
        missing_docs.append("governance_doc")
    if "review" not in touched_kinds:
        missing_docs.append("review_doc")
    payload["missing_stream_docs"] = missing_docs

    if missing_docs:
        payload["stream_version_pr_boundary_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM_DOC_PAIR_INCOMPLETE
        payload["stale_reasons"] = ["stream_doc_pair_incomplete"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["stream_version_pr_boundary_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
