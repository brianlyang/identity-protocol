#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    evaluate_root_doc_anchor_checks,
    root_doc_anchor_checks_from_doc,
    validate_expected_root_doc_anchor_checks,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_family
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
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Governance row-family completeness must stay explicit",
        "Required registered-top-level-entry, corpus-class-profile, and forbidden-content-class families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize governance legality while required rel-path, corpus-class, or forbidden-content-class identity drift remains known only internally.",
    ),
    "identity/protocol/README.md": (
        "## Root governance completeness discipline",
        "Governance law is not a soft prose bundle.",
        "1. required registered-top-level-entry, corpus-class-profile, and forbidden-content-class rows must remain explicit as separate machine-readable row families;",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root governance completeness boundary",
        "1. Governance law must remain machine-readable as separate registered-top-level-entry, corpus-class-profile, and forbidden-content-class row families.",
        "4. Protocol legality must not finalize governance legality while missing or unexpected rel-path, corpus-class, or forbidden-content-class identities remain known only inside validator logic.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime governance consumption boundary",
        "1. Runtime consumes governance law as separate registered-top-level-entry, corpus-class-profile, and forbidden-content-class row families rather than as undifferentiated governance prose.",
        "4. Runtime must not finalize governance legality while missing or unexpected rel-path, corpus-class, or forbidden-content-class identities remain known only inside validator machinery.",
    ),
}


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
    structure_violations: list[dict[str, Any]] = []
    file_violations: list[dict[str, Any]] = []
    directory_violations: list[dict[str, Any]] = []
    forbidden_hits: list[dict[str, Any]] = []
    root_doc_anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
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
    root_doc_anchor_checks = root_doc_anchor_checks_from_doc(registry_doc) if registry_doc else ()
    raw_forbidden_rows = registry_doc.get("forbidden_content_classes") if registry_doc else []
    raw_profile_rows = registry_doc.get("corpus_class_profiles") if registry_doc else []
    raw_forbidden_ids = [
        str(row.get("class_id") or "").strip()
        for row in raw_forbidden_rows
        if isinstance(row, dict) and str(row.get("class_id") or "").strip()
    ]
    raw_profile_ids = [
        str(row.get("corpus_class") or "").strip()
        for row in raw_profile_rows
        if isinstance(row, dict) and str(row.get("corpus_class") or "").strip()
    ]
    expected_profile_ids = sorted({entry.corpus_class for entry in entries if entry.law_bearing and entry.entry_kind == "file"})
    expected_forbidden_ids = sorted(
        {class_id for entry in entries for class_id in entry.forbidden_content_classes}
        | {class_id for profile in class_profiles.values() for class_id in profile.forbidden_content_classes}
    )

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
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                root_doc_anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_governance",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY

    root_dir = (repo_root / root_dir_rel).resolve()
    if not stale_reasons and (not root_dir.exists() or not root_dir.is_dir()):
        stale_reasons.append(f"root_corpus_root_dir_missing:{root_dir_rel}")
        error_code = ERR_STRUCTURE

    registered_paths = sorted({entry.rel_path for entry in entries})
    actual_paths = collect_protocol_root_top_level_entries(repo_root, root_dir_rel) if root_dir.exists() else []

    if not stale_reasons:
        if len(registered_paths) != len(entries):
            structure_violations.append({"field": "registered_top_level_entries", "reason": "duplicate_rel_path"})
        if len(set(raw_profile_ids)) != len(raw_profile_ids):
            structure_violations.append({"field": "corpus_class_profiles", "reason": "duplicate_corpus_class"})
        if len(set(raw_forbidden_ids)) != len(raw_forbidden_ids):
            structure_violations.append({"field": "forbidden_content_classes", "reason": "duplicate_class_id"})

        extras = sorted(set(actual_paths) - set(registered_paths))
        missing = sorted(set(registered_paths) - set(actual_paths))
        if extras:
            structure_violations.append(
                {"field": "registered_top_level_entries", "reason": "extra_root_entries", "rel_paths": extras}
            )
        if missing:
            structure_violations.append(
                {"field": "registered_top_level_entries", "reason": "missing_root_entries", "rel_paths": missing}
            )

        missing_profile_ids = sorted(set(expected_profile_ids) - set(class_profiles))
        extra_profile_ids = sorted(set(class_profiles) - set(expected_profile_ids))
        if missing_profile_ids:
            structure_violations.append(
                {"field": "corpus_class_profiles", "reason": "missing_expected_corpus_classes", "corpus_classes": missing_profile_ids}
            )
        if extra_profile_ids:
            structure_violations.append(
                {"field": "corpus_class_profiles", "reason": "extra_unreferenced_corpus_classes", "corpus_classes": extra_profile_ids}
            )

        missing_forbidden_ids = sorted(set(expected_forbidden_ids) - set(content_classes))
        extra_forbidden_ids = sorted(set(content_classes) - set(expected_forbidden_ids))
        if missing_forbidden_ids:
            structure_violations.append(
                {"field": "forbidden_content_classes", "reason": "missing_expected_class_ids", "class_ids": missing_forbidden_ids}
            )
        if extra_forbidden_ids:
            structure_violations.append(
                {"field": "forbidden_content_classes", "reason": "extra_unreferenced_class_ids", "class_ids": extra_forbidden_ids}
            )

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

        root_doc_anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                root_doc_anchor_checks,
                field_name="root_doc_anchor_checks",
            )
        )

    if not error_code and (structure_violations or file_violations or directory_violations or root_doc_anchor_violations):
        error_code = ERR_STRUCTURE
    if not error_code and forbidden_hits:
        error_code = ERR_CONTENT

    stale_reasons.extend(
        f"structure_violation:{item['field']}:{item['reason']}"
        for item in structure_violations
    )
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

    status = (
        STATUS_PASS_REQUIRED
        if not (stale_reasons or root_doc_anchor_violations)
        else STATUS_FAIL_REQUIRED
    )
    row_family_projection_rows = [
        project_row_family(
            family_id="registered_top_level_entries",
            member_id_key="rel_path",
            actual_rows=[SimpleNamespace(rel_path=rel_path) for rel_path in actual_paths],
            expected_rows={rel_path: {} for rel_path in registered_paths},
            id_attr="rel_path",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="corpus_class_profiles",
            member_id_key="corpus_class",
            actual_rows=[SimpleNamespace(corpus_class=corpus_class) for corpus_class in sorted(class_profiles.keys())],
            expected_rows={corpus_class: {} for corpus_class in expected_profile_ids},
            id_attr="corpus_class",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        project_row_family(
            family_id="forbidden_content_classes",
            member_id_key="class_id",
            actual_rows=[SimpleNamespace(class_id=class_id) for class_id in sorted(content_classes.keys())],
            expected_rows={class_id: {} for class_id in expected_forbidden_ids},
            id_attr="class_id",
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
    ]
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
        **project_root_contract_support_projection(
            prefix="governance",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=root_doc_anchor_checks,
            anchor_violations=root_doc_anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "corpus_class_profile_ids": sorted(class_profiles.keys()),
        "corpus_class_profile_count": len(class_profiles),
        "forbidden_content_class_ids": sorted(content_classes.keys()),
        "structure_violations": structure_violations,
        "file_violations": file_violations,
        "directory_violations": directory_violations,
        "forbidden_content_hits": forbidden_hits,
        "root_doc_anchor_violations": root_doc_anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
