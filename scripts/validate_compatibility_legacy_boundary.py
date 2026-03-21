#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root
from validate_response_authority_consumer_semantics import DEFAULT_TARGET_FILES as AUTHORITY_CONSUMER_TARGETS

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_LEGACY_BOUNDARY = "IP-COMPAT-LEGACY-001"

DEFAULT_STREAM_REGISTRY = STREAM_DOC_REGISTRY_CURRENT
DEFAULT_SEMANTIC_REGISTRY = "identity/protocol/mappings/semantic-term-registry.current.yaml"
LEGACY_TERM_ID = "legacy_canonical_compatibility_path"
STRICT_USER_VISIBLE_STREAM_VERSION = "v1.6.12"

FORBIDDEN_PROTOCOL_TARGETS = tuple(
    dict.fromkeys(
        (
            *AUTHORITY_CONSUMER_TARGETS,
            "scripts/resolve_runtime_authoritative_identity.py",
            "scripts/resolve_identity_context.py",
            "scripts/validate_native_chat_bootstrap_entry_stream.py",
            "scripts/validate_response_authority_consumer_semantics.py",
        )
    )
)
OPTIONAL_WORKSPACE_TARGETS = (
    "scripts/codex_native_chat/native_chat_bootstrap_bridge.py",
    "scripts/codex_native_chat/validate_native_chat_entry_bootstrap.py",
    "scripts/validate_headstamp_recurrence_closure.py",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _workspace_root(repo_root: Path) -> Path:
    return repo_root.parent if repo_root.name == "identity-protocol-local" else repo_root


def _line_hits(text: str, phrase: str) -> list[int]:
    needle = str(phrase or "").strip().lower()
    if not needle:
        return []
    hits: list[int] = []
    for idx, line in enumerate(str(text or "").splitlines(), start=1):
        if needle in line.lower():
            hits.append(idx)
    return hits


def _load_legacy_term(semantic_doc: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    terms = semantic_doc.get("terms")
    if not isinstance(terms, list):
        return {}, []
    row = next(
        (
            item
            for item in terms
            if isinstance(item, dict) and str(item.get("term_id", "")).strip() == LEGACY_TERM_ID
        ),
        {},
    )
    phrases = [str(row.get("canonical_term", "")).strip()]
    aliases = row.get("aliases")
    if isinstance(aliases, list):
        phrases.extend(str(alias).strip() for alias in aliases if str(alias).strip())
    # keep order, drop blanks/dupes
    deduped: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        key = phrase.lower()
        if not phrase or key in seen:
            continue
        seen.add(key)
        deduped.append(phrase)
    return row if isinstance(row, dict) else {}, deduped


def _strict_user_visible_docs(stream_doc: dict[str, Any]) -> list[str]:
    rows = stream_doc.get("stream_docs")
    if not isinstance(rows, list):
        return []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("stream_version", "")).strip() != STRICT_USER_VISIBLE_STREAM_VERSION:
            continue
        docs = [
            str(row.get("governance_doc", "")).strip(),
            str(row.get("review_doc", "")).strip(),
        ]
        return [doc for doc in docs if doc]
    return []


def _scan_target(path: Path, *, phrases: list[str], rel_label: str, violations: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    for phrase in phrases:
        hits = _line_hits(text, phrase)
        if not hits:
            continue
        violations.append(
            {
                "file": rel_label,
                "reason": "legacy_compatibility_term_present_in_forbidden_surface",
                "token": phrase,
                "line_hits": hits[:10],
            }
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Validate that legacy compatibility-path terminology stays confined to compatibility/migration "
            "surfaces and does not re-enter current-turn authority, strict visible lanes, or active gate defaults."
        )
    )
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--stream-registry", default=DEFAULT_STREAM_REGISTRY)
    ap.add_argument("--semantic-registry", default=DEFAULT_SEMANTIC_REGISTRY)
    ap.add_argument("--extra-forbidden-target", action="append", default=[])
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    workspace_root = _workspace_root(repo_root)

    stream_registry_path, stream_registry_active_file, stream_registry_alias_error = resolve_current_yaml_alias(
        repo_root, str(args.stream_registry)
    )
    semantic_registry_path, semantic_registry_active_file, semantic_registry_alias_error = resolve_current_yaml_alias(
        repo_root, str(args.semantic_registry)
    )

    payload: dict[str, Any] = {
        "compatibility_legacy_boundary_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_LEGACY_BOUNDARY,
        "repo_root": str(repo_root),
        "workspace_root": str(workspace_root),
        "stream_registry_path": str(stream_registry_path),
        "stream_registry_active_file": stream_registry_active_file,
        "stream_registry_alias_error": stream_registry_alias_error,
        "semantic_registry_path": str(semantic_registry_path),
        "semantic_registry_active_file": semantic_registry_active_file,
        "semantic_registry_alias_error": semantic_registry_alias_error,
        "guarded_term_id": LEGACY_TERM_ID,
        "guarded_phrases": [],
        "allowed_scope": [],
        "forbidden_protocol_targets": list(FORBIDDEN_PROTOCOL_TARGETS),
        "forbidden_workspace_targets": list(OPTIONAL_WORKSPACE_TARGETS),
        "strict_user_visible_docs": [],
        "missing_workspace_targets": [],
        "extra_forbidden_targets": list(args.extra_forbidden_target),
        "violations": [],
        "stale_reasons": [],
    }

    stale_reasons: list[str] = []
    if stream_registry_alias_error:
        stale_reasons.append(f"stream_registry_alias_error:{stream_registry_alias_error}")
    if semantic_registry_alias_error:
        stale_reasons.append(f"semantic_registry_alias_error:{semantic_registry_alias_error}")
    if stale_reasons:
        payload["stale_reasons"] = stale_reasons
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    stream_doc = _load_yaml(stream_registry_path)
    semantic_doc = _load_yaml(semantic_registry_path)
    legacy_term_row, guarded_phrases = _load_legacy_term(semantic_doc)
    if not guarded_phrases:
        payload["stale_reasons"] = ["legacy_term_missing_from_semantic_registry"]
        print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
        return 1

    payload["guarded_phrases"] = guarded_phrases
    allowed_scope = legacy_term_row.get("allowed_scope")
    if isinstance(allowed_scope, list):
        payload["allowed_scope"] = [str(item).strip() for item in allowed_scope if str(item).strip()]

    strict_docs = _strict_user_visible_docs(stream_doc)
    payload["strict_user_visible_docs"] = strict_docs

    violations: list[dict[str, Any]] = []
    for rel in FORBIDDEN_PROTOCOL_TARGETS:
        target = (repo_root / rel).resolve()
        if not target.exists():
            violations.append(
                {
                    "file": rel,
                    "reason": "required_forbidden_protocol_target_missing",
                    "token": "",
                    "line_hits": [],
                }
            )
            continue
        _scan_target(target, phrases=guarded_phrases, rel_label=rel, violations=violations)

    for rel in strict_docs:
        target = (repo_root / rel).resolve()
        if not target.exists():
            violations.append(
                {
                    "file": rel,
                    "reason": "required_strict_user_visible_doc_missing",
                    "token": "",
                    "line_hits": [],
                }
            )
            continue
        _scan_target(target, phrases=guarded_phrases, rel_label=rel, violations=violations)

    missing_workspace_targets: list[str] = []
    for rel in OPTIONAL_WORKSPACE_TARGETS:
        target = (workspace_root / rel).resolve()
        if not target.exists():
            missing_workspace_targets.append(rel)
            continue
        _scan_target(target, phrases=guarded_phrases, rel_label=rel, violations=violations)
    payload["missing_workspace_targets"] = missing_workspace_targets

    for raw in args.extra_forbidden_target:
        target = Path(raw).expanduser().resolve()
        if not target.exists():
            violations.append(
                {
                    "file": str(target),
                    "reason": "extra_forbidden_target_missing",
                    "token": "",
                    "line_hits": [],
                }
            )
            continue
        _scan_target(target, phrases=guarded_phrases, rel_label=str(target), violations=violations)

    payload["violations"] = violations
    payload["compatibility_legacy_boundary_status"] = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    if not violations:
        payload["error_code"] = ""
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.json_only else 2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
