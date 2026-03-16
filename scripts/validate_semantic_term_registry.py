#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SEMANTIC_TERM_REGISTRY = "IP-SEMREG-001"
DEFAULT_REGISTRY_ENTRY = "identity/protocol/mappings/semantic-term-registry.current.yaml"
DEFAULT_STREAM_REGISTRY_ENTRY = "identity/protocol/mappings/stream-doc-registry.current.yaml"


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> tuple[Path, str, str]:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        return configured_path, "", "current_file_missing"
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path, "", ""
    try:
        current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return configured_path, "", "current_file_parse_failed"
    if not isinstance(current_doc, dict):
        return configured_path, "", "current_file_parse_failed"
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        return configured_path, "", "active_file_missing"
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        return active_path, active_file, "active_file_not_found"
    return active_path, active_file, ""


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _line_hits(*, text: str, phrase: str) -> list[int]:
    needle = str(phrase or "").strip().lower()
    if not needle:
        return []
    hits: list[int] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if needle in line.lower():
            hits.append(idx)
    return hits


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate semantic term registry contract and forbidden phrase hygiene.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--registry", default=DEFAULT_REGISTRY_ENTRY)
    ap.add_argument("--stream-registry", default=DEFAULT_STREAM_REGISTRY_ENTRY)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    entry_path = (repo_root / str(args.registry)).resolve()
    registry_path, registry_active_file, registry_alias_error = _resolve_current_yaml_alias(repo_root, str(args.registry))

    payload: dict[str, Any] = {
        "semantic_term_registry_status": STATUS_FAIL_REQUIRED,
        "error_code": ERR_SEMANTIC_TERM_REGISTRY,
        "registry_entry": str(entry_path),
        "registry_path": str(registry_path),
        "registry_active_file": registry_active_file,
        "registry_alias_error": registry_alias_error,
        "stream_registry_entry": str((repo_root / str(args.stream_registry)).resolve()),
        "stream_registry_path": "",
        "stream_registry_alias_error": "",
        "schema_version": "",
        "term_count": 0,
        "forbidden_phrase_count": 0,
        "scan_target_count": 0,
        "scan_targets": [],
        "missing_scan_targets": [],
        "invalid_rows": [],
        "forbidden_phrase_hits": [],
        "stale_reasons": [],
    }

    if registry_alias_error:
        payload["stale_reasons"].append(f"semantic_term_registry_alias_error:{registry_alias_error}")
        _emit(payload, json_only=args.json_only)
        return 1

    if not registry_path.exists() or not registry_path.is_file():
        payload["stale_reasons"].append("semantic_term_registry_missing")
        _emit(payload, json_only=args.json_only)
        return 1

    try:
        registry_doc = _load_yaml(registry_path)
    except Exception as exc:
        payload["stale_reasons"].append(f"semantic_term_registry_parse_failed:{exc}")
        _emit(payload, json_only=args.json_only)
        return 1

    payload["schema_version"] = str(registry_doc.get("schema_version", "")).strip()

    terms = registry_doc.get("terms")
    forbidden_rows = registry_doc.get("forbidden_phrases")
    scan_roots = registry_doc.get("scan_roots")
    include_active_stream_docs = bool(registry_doc.get("include_active_stream_docs", False))
    configured_stream_registry = str(registry_doc.get("active_stream_registry") or args.stream_registry).strip()

    invalid_rows: list[str] = []
    if not isinstance(terms, list) or not terms:
        invalid_rows.append("terms_missing_or_invalid")
        terms = []
    if not isinstance(forbidden_rows, list) or not forbidden_rows:
        invalid_rows.append("forbidden_phrases_missing_or_invalid")
        forbidden_rows = []
    if not isinstance(scan_roots, list) or not scan_roots:
        invalid_rows.append("scan_roots_missing_or_invalid")
        scan_roots = []

    normalized_terms: list[dict[str, Any]] = []
    for idx, row in enumerate(terms):
        if not isinstance(row, dict):
            invalid_rows.append(f"terms[{idx}]_not_object")
            continue
        term_id = str(row.get("term_id", "")).strip()
        canonical_term = str(row.get("canonical_term", "")).strip()
        semantics = str(row.get("semantics", "")).strip()
        allowed_scope = row.get("allowed_scope")
        if not term_id or not canonical_term or not semantics:
            invalid_rows.append(f"terms[{idx}]_required_fields_missing")
        if not isinstance(allowed_scope, list) or not [str(x).strip() for x in allowed_scope if str(x).strip()]:
            invalid_rows.append(f"terms[{idx}]_allowed_scope_invalid")
        normalized_terms.append(row)

    normalized_forbidden: list[dict[str, str]] = []
    for idx, row in enumerate(forbidden_rows):
        if not isinstance(row, dict):
            invalid_rows.append(f"forbidden_phrases[{idx}]_not_object")
            continue
        phrase = str(row.get("phrase", "")).strip()
        replacement = str(row.get("replacement", "")).strip()
        if not phrase:
            invalid_rows.append(f"forbidden_phrases[{idx}]_phrase_missing")
            continue
        normalized_forbidden.append({"phrase": phrase, "replacement": replacement})

    scan_targets: list[Path] = []
    seen_targets: set[str] = set()
    for raw in scan_roots:
        rel = str(raw or "").strip()
        if not rel:
            continue
        target = (repo_root / rel).resolve()
        key = str(target)
        if key in seen_targets:
            continue
        seen_targets.add(key)
        scan_targets.append(target)

    stream_registry_path = Path()
    stream_registry_alias_error = ""
    if include_active_stream_docs:
        stream_registry_path, _stream_active_file, stream_registry_alias_error = _resolve_current_yaml_alias(
            repo_root, configured_stream_registry or str(args.stream_registry)
        )
        payload["stream_registry_path"] = str(stream_registry_path)
        payload["stream_registry_alias_error"] = stream_registry_alias_error
        if stream_registry_alias_error:
            invalid_rows.append(f"stream_registry_alias_error:{stream_registry_alias_error}")
        elif not stream_registry_path.exists() or not stream_registry_path.is_file():
            invalid_rows.append("stream_registry_missing")
        else:
            try:
                stream_doc = _load_yaml(stream_registry_path)
            except Exception as exc:
                invalid_rows.append(f"stream_registry_parse_failed:{exc}")
                stream_doc = {}
            stream_rows = stream_doc.get("stream_docs")
            if not isinstance(stream_rows, list):
                invalid_rows.append("stream_docs_missing_or_invalid")
                stream_rows = []
            for idx, row in enumerate(stream_rows):
                if not isinstance(row, dict):
                    invalid_rows.append(f"stream_docs[{idx}]_not_object")
                    continue
                for key_name in ("governance_doc", "review_doc"):
                    rel = str(row.get(key_name, "")).strip()
                    if not rel:
                        invalid_rows.append(f"stream_docs[{idx}]_{key_name}_missing")
                        continue
                    target = (repo_root / rel).resolve()
                    target_key = str(target)
                    if target_key in seen_targets:
                        continue
                    seen_targets.add(target_key)
                    scan_targets.append(target)

    missing_scan_targets = [str(path) for path in scan_targets if not path.exists() or not path.is_file()]

    phrase_hits: list[dict[str, Any]] = []
    for target in scan_targets:
        if not target.exists() or not target.is_file():
            continue
        text = target.read_text(encoding="utf-8", errors="ignore")
        for row in normalized_forbidden:
            lines = _line_hits(text=text, phrase=row["phrase"])
            if not lines:
                continue
            phrase_hits.append(
                {
                    "path": str(target),
                    "phrase": row["phrase"],
                    "replacement": row["replacement"],
                    "line_hits": lines,
                    "hit_count": len(lines),
                }
            )

    payload["term_count"] = len(normalized_terms)
    payload["forbidden_phrase_count"] = len(normalized_forbidden)
    payload["scan_target_count"] = len(scan_targets)
    payload["scan_targets"] = [str(path) for path in scan_targets]
    payload["missing_scan_targets"] = missing_scan_targets
    payload["invalid_rows"] = sorted(set(invalid_rows))
    payload["forbidden_phrase_hits"] = phrase_hits

    stale_reasons: list[str] = []
    if payload["invalid_rows"]:
        stale_reasons.append("registry_schema_invalid")
    if missing_scan_targets:
        stale_reasons.append("scan_target_missing")
    if phrase_hits:
        stale_reasons.append("forbidden_phrase_detected")

    if stale_reasons:
        payload["semantic_term_registry_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SEMANTIC_TERM_REGISTRY
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["semantic_term_registry_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
