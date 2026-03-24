#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_governance_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    collect_protocol_root_top_level_entries,
    corpus_class_profiles_from_registry,
    forbidden_classes_from_registry,
    find_missing_markers,
    load_root_corpus_registry,
    merge_forbidden_content_classes,
    merge_required_markers,
    root_corpus_entries_from_registry,
    scan_forbidden_content,
)

STATUS_KEY = "protocol_root_corpus_governance_status"
ERR_REGISTRY = "IP-RCG-001"
ERR_STRUCTURE = "IP-RCG-002"
ERR_CONTENT = "IP-RCG-003"
ALLOWED_ENTRY_KINDS = {"file", "directory"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus governance and admission boundaries.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    registry_doc, registry_entry_path, registry_active_path, alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    file_violations: list[dict[str, Any]] = []
    directory_violations: list[dict[str, Any]] = []
    forbidden_hits: list[dict[str, Any]] = []
    error_code = ""

    if alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    root_dir_rel = str(registry_doc.get("root_dir") or "identity/protocol").strip() if registry_doc else "identity/protocol"
    entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    content_classes = forbidden_classes_from_registry(registry_doc) if registry_doc else {}
    class_profiles = corpus_class_profiles_from_registry(registry_doc) if registry_doc else {}

    if not stale_reasons:
        if str(registry_doc.get("registry_family") or "").strip() != "protocol_root_corpus":
            stale_reasons.append("root_corpus_registry_family_invalid")
            error_code = ERR_REGISTRY
        if str(registry_doc.get("registry_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_registry_version_invalid")
            error_code = ERR_REGISTRY
        if not entries:
            stale_reasons.append("root_corpus_entries_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_class_profiles_missing")
            error_code = ERR_REGISTRY
        for key in ("validator_script", "probe_script", "common_script"):
            rel_path = str(registry_doc.get(key) or "").strip()
            if not rel_path:
                stale_reasons.append(f"root_corpus_registry_missing_field:{key}")
                error_code = ERR_REGISTRY
                continue
            if not (repo_root / rel_path).resolve().exists():
                stale_reasons.append(f"root_corpus_registry_control_surface_missing:{key}:{rel_path}")
                error_code = ERR_REGISTRY
        for class_id, content_class in content_classes.items():
            if not content_class.patterns:
                stale_reasons.append(f"root_corpus_forbidden_class_missing_patterns:{class_id}")
                error_code = ERR_REGISTRY
        for entry in entries:
            if entry.law_bearing and entry.entry_kind == "file" and entry.corpus_class not in class_profiles:
                stale_reasons.append(f"root_corpus_class_profile_missing:{entry.corpus_class}:{entry.rel_path}")
                error_code = ERR_REGISTRY

    root_dir = (repo_root / root_dir_rel).resolve()
    if not stale_reasons and (not root_dir.exists() or not root_dir.is_dir()):
        stale_reasons.append(f"root_corpus_root_dir_missing:{root_dir_rel}")
        error_code = ERR_STRUCTURE

    registered_paths = sorted({entry.rel_path for entry in entries})
    actual_paths = collect_protocol_root_top_level_entries(repo_root, root_dir_rel) if root_dir.exists() else []

    if not stale_reasons:
        extras = sorted(set(actual_paths) - set(registered_paths))
        missing = sorted(set(registered_paths) - set(actual_paths))
        for rel_path in extras:
            stale_reasons.append(f"unregistered_root_top_level_entry:{rel_path}")
        for rel_path in missing:
            stale_reasons.append(f"registered_root_top_level_entry_missing:{rel_path}")
        if extras or missing:
            error_code = ERR_STRUCTURE

    if not stale_reasons:
        for entry in entries:
            if entry.entry_kind not in ALLOWED_ENTRY_KINDS:
                stale_reasons.append(f"root_corpus_entry_kind_invalid:{entry.rel_path}:{entry.entry_kind}")
                error_code = ERR_REGISTRY
                continue
            path = (repo_root / entry.rel_path).resolve()
            if entry.entry_kind == "file":
                if not path.exists() or not path.is_file():
                    file_violations.append({"rel_path": entry.rel_path, "reason": "file_missing"})
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                missing_markers = find_missing_markers(
                    text,
                    merge_required_markers(entry, class_profiles=class_profiles),
                )
                for marker in missing_markers:
                    file_violations.append(
                        {"rel_path": entry.rel_path, "reason": "required_marker_missing", "marker": marker}
                    )
                for hit in scan_forbidden_content(
                    text,
                    content_classes=content_classes,
                    class_ids=merge_forbidden_content_classes(entry, class_profiles=class_profiles),
                ):
                    forbidden_hits.append(
                        {
                            "rel_path": entry.rel_path,
                            "class_id": hit.class_id,
                            "pattern": hit.pattern,
                            "line_no": hit.line_no,
                            "line_excerpt": hit.line_excerpt,
                        }
                    )
            else:
                if not path.exists() or not path.is_dir():
                    directory_violations.append({"rel_path": entry.rel_path, "reason": "directory_missing"})
                    continue
                for child in entry.required_children:
                    child_path = (path / child).resolve()
                    if not child_path.exists():
                        directory_violations.append(
                            {
                                "rel_path": entry.rel_path,
                                "reason": "required_child_missing",
                                "child": child,
                            }
                        )

    if not error_code and (file_violations or directory_violations):
        error_code = ERR_STRUCTURE
    if not error_code and forbidden_hits:
        error_code = ERR_CONTENT

    stale_reasons.extend(
        f"file_violation:{item['rel_path']}:{item['reason']}:{item.get('marker', '')}".rstrip(":")
        for item in file_violations
    )
    stale_reasons.extend(
        f"directory_violation:{item['rel_path']}:{item['reason']}:{item.get('child', '')}".rstrip(":")
        for item in directory_violations
    )
    stale_reasons.extend(
        f"forbidden_content:{item['rel_path']}:{item['class_id']}:{item['line_no']}" for item in forbidden_hits
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_CONTENT),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "root_dir": root_dir_rel,
        "registered_top_level_entries": registered_paths,
        "actual_top_level_entries": actual_paths,
        "registered_top_level_count": len(registered_paths),
        "actual_top_level_count": len(actual_paths),
        "law_bearing_entry_count": sum(1 for entry in entries if entry.law_bearing),
        "validated_file_count": sum(1 for entry in entries if entry.entry_kind == "file"),
        "validated_directory_count": sum(1 for entry in entries if entry.entry_kind == "directory"),
        "corpus_class_profile_ids": sorted(class_profiles.keys()),
        "corpus_class_profile_count": len(class_profiles),
        "forbidden_content_class_ids": sorted(content_classes.keys()),
        "file_violations": file_violations,
        "directory_violations": directory_violations,
        "forbidden_content_hits": forbidden_hits,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
