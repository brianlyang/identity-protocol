#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias
from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RELEASE_DOC_SURFACE = "IP-RDOC-001"

SUMMARY_DOC_FALLBACK = "docs/release/identity-v1.6x-release-closure-summary.md"
GOVERNANCE_DOC = "docs/governance/identity-v1.6x-release-closure-governance.md"
REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md"
REQUIRED_ARCHIVAL_MARKERS = (
    "historical archival",
    "not a current release-boundary surface",
    SUMMARY_DOC_FALLBACK,
    GOVERNANCE_DOC,
    REVIEW_DOC,
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _is_release_doc(doc: str) -> bool:
    normalized = _norm_path(doc)
    return normalized.startswith("docs/release/") and normalized.endswith(".md")


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = _norm_path(str(item))
        if token:
            out.append(token)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release doc surface governance for canonical summary + archival release docs.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--registry", default=STREAM_DOC_REGISTRY_CURRENT)
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    registry_path, registry_active_file, registry_alias_error = resolve_current_yaml_alias(
        repo_root,
        str(args.registry),
    )

    payload: dict[str, Any] = {
        "release_doc_surface_governance_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "registry_path": str(registry_path),
        "registry_active_file": registry_active_file,
        "canonical_release_summary_doc": "",
        "release_archival_docs": [],
        "authoritative_release_docs": [],
        "unclassified_release_docs": [],
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []
    if registry_alias_error:
        stale_reasons.append(f"stream_doc_registry_alias_error:{registry_alias_error}")

    try:
        if not registry_path.exists():
            raise FileNotFoundError(f"missing_registry:{registry_path}")
        data = _read_yaml(registry_path)
        mandatory_static_docs = _as_str_list(data.get("mandatory_static_docs"))
        static_rows = data.get("static_doc_required_alias_refs")
        static_doc_rows: set[str] = set()
        if isinstance(static_rows, list):
            for row in static_rows:
                if isinstance(row, dict):
                    doc = _norm_path(row.get("doc", ""))
                    if doc:
                        static_doc_rows.add(doc)
        canonical_summary_doc = _norm_path(data.get("canonical_release_summary_doc", ""))
        release_archival_docs = _as_str_list(data.get("release_archival_docs"))
        release_docs = sorted(
            p.relative_to(repo_root).as_posix()
            for p in (repo_root / "docs/release").glob("*.md")
        )
    except Exception as exc:
        payload["error_code"] = ERR_RELEASE_DOC_SURFACE
        payload["stale_reasons"] = stale_reasons + [str(exc)]
        _emit(payload, json_only=args.json_only)
        return 1

    authoritative_release_docs = sorted(
        doc for doc in mandatory_static_docs if _is_release_doc(doc)
    )
    payload["canonical_release_summary_doc"] = canonical_summary_doc
    payload["release_archival_docs"] = release_archival_docs
    payload["authoritative_release_docs"] = authoritative_release_docs

    if not canonical_summary_doc:
        stale_reasons.append("canonical_release_summary_doc_missing")
    elif not _is_release_doc(canonical_summary_doc):
        stale_reasons.append(f"canonical_release_summary_doc_invalid:{canonical_summary_doc}")
    else:
        summary_path = (repo_root / canonical_summary_doc).resolve()
        if not summary_path.exists():
            stale_reasons.append(f"canonical_release_summary_doc_not_found:{canonical_summary_doc}")
        if canonical_summary_doc not in mandatory_static_docs:
            stale_reasons.append("canonical_release_summary_doc_not_in_mandatory_static_docs")
        if canonical_summary_doc not in static_doc_rows:
            stale_reasons.append("canonical_release_summary_doc_missing_static_alias_row")

    unexpected_authoritative = sorted(
        doc for doc in authoritative_release_docs if doc != canonical_summary_doc
    )
    if unexpected_authoritative:
        stale_reasons.append(
            "unexpected_authoritative_release_docs:" + ",".join(unexpected_authoritative)
        )

    release_archival_set = set(release_archival_docs)
    if not release_archival_docs:
        stale_reasons.append("release_archival_docs_missing")
    for doc in release_archival_docs:
        if not _is_release_doc(doc):
            stale_reasons.append(f"release_archival_doc_invalid:{doc}")
            continue
        path = (repo_root / doc).resolve()
        if not path.exists():
            stale_reasons.append(f"release_archival_doc_not_found:{doc}")
            continue
        if doc == canonical_summary_doc:
            stale_reasons.append(f"release_archival_doc_conflicts_with_canonical:{doc}")
            continue
        if doc in mandatory_static_docs:
            stale_reasons.append(f"release_archival_doc_conflicts_with_authoritative:{doc}")
        text = path.read_text(encoding="utf-8")
        for marker in REQUIRED_ARCHIVAL_MARKERS:
            if marker not in text:
                stale_reasons.append(f"release_archival_doc_missing_marker:{doc}:{marker}")

    unclassified_release_docs = sorted(
        doc
        for doc in release_docs
        if doc != canonical_summary_doc and doc not in release_archival_set
    )
    payload["unclassified_release_docs"] = unclassified_release_docs
    if unclassified_release_docs:
        stale_reasons.append(
            "unclassified_release_docs_present:" + ",".join(unclassified_release_docs)
        )

    payload["release_doc_surface_governance_status"] = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload["error_code"] = "" if not stale_reasons else ERR_RELEASE_DOC_SURFACE
    payload["stale_reasons"] = stale_reasons
    _emit(payload, json_only=args.json_only)
    return 0 if not stale_reasons else 1


if __name__ == "__main__":
    raise SystemExit(main())
