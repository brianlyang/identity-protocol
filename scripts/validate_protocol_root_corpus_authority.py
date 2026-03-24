#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_corpus_authority_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    authority_anchor_checks_from_doc,
    authority_class_profiles_from_doc,
    entry_authority_projections_from_doc,
    load_root_corpus_authority,
)
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc

STATUS_KEY = "protocol_root_corpus_authority_status"
ERR_REGISTRY = "IP-RCA-001"
ERR_STRUCTURE = "IP-RCA-002"
ERR_AUTHORITY = "IP-RCA-003"

EXPECTED_CLASS_RULES = {
    "bottom_theory": {
        "authority_role": "interpretive_bottom_theory",
        "authority_mode": "interpretive_only",
        "philosophical_primacy": True,
        "law_bearing_required": True,
    },
    "root_index": {
        "authority_role": "navigational_root_index",
        "authority_mode": "navigational_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "constitution": {
        "authority_role": "constitutional_protocol_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "runtime_constitution": {
        "authority_role": "constitutional_runtime_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "root_contract": {
        "authority_role": "root_domain_contract_law",
        "authority_mode": "frozen_law_only",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "machine_registry_directory": {
        "authority_role": "machine_consumed_registry_family",
        "authority_mode": "machine_consumed_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "governed_subdomain_extension": {
        "authority_role": "governed_subdomain_extension_family",
        "authority_mode": "extension_family",
        "philosophical_primacy": False,
        "law_bearing_required": True,
    },
    "demoted_support_directory": {
        "authority_role": "demoted_support_material",
        "authority_mode": "demoted_support_only",
        "philosophical_primacy": False,
        "law_bearing_required": False,
    },
}
ALLOWED_AUTHORITY_MODES = {
    "interpretive_only",
    "navigational_only",
    "frozen_law_only",
    "machine_consumed_family",
    "extension_family",
    "demoted_support_only",
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus authority layering and authority-role topology.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    authority_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    error_code = ""

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = authority_anchor_checks_from_doc(authority_doc) if authority_doc else ()
    class_profiles = authority_class_profiles_from_doc(authority_doc) if authority_doc else ()
    entry_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()

    if not stale_reasons:
        if str(authority_doc.get("authority_family") or "").strip() != "protocol_root_corpus_authority":
            stale_reasons.append("root_corpus_authority_family_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("authority_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_authority_version_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_authority_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_authority_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(authority_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_authority_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_authority_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not class_profiles:
            stale_reasons.append("root_corpus_authority_class_profiles_missing")
            error_code = ERR_REGISTRY
        if not entry_projections:
            stale_reasons.append("root_corpus_authority_entry_projection_missing")
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_class_law_bearing = {entry.corpus_class: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    class_profile_map = {row.corpus_class: row for row in class_profiles}
    entry_projection_map = {row.rel_path: row for row in entry_projections}
    anchor_rel_paths = [row.rel_path for row in anchor_checks]
    ordering_reading_paths = [row.rel_path for row in sorted(reading_rows, key=lambda item: item.order)]
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip() if ordering_doc else ""

    if not stale_reasons:
        if len(class_profile_map) != len(class_profiles):
            structure_violations.append({"field": "authority_class_profiles", "reason": "duplicate_corpus_class"})
        if len(entry_projection_map) != len(entry_projections):
            structure_violations.append({"field": "entry_authority_projection", "reason": "duplicate_rel_path"})
        if len(set(anchor_rel_paths)) != len(anchor_rel_paths):
            structure_violations.append({"field": "authority_anchor_checks", "reason": "duplicate_rel_path"})

        missing_class_profiles = sorted(set(registry_classes) - set(class_profile_map))
        extra_class_profiles = sorted(set(class_profile_map) - set(registry_classes))
        if missing_class_profiles:
            structure_violations.append(
                {"field": "authority_class_profiles", "reason": "missing_registry_classes", "corpus_classes": missing_class_profiles}
            )
        if extra_class_profiles:
            structure_violations.append(
                {"field": "authority_class_profiles", "reason": "extra_unregistered_classes", "corpus_classes": extra_class_profiles}
            )

        missing_entry_projections = sorted(set(registry_paths) - set(entry_projection_map))
        extra_entry_projections = sorted(set(entry_projection_map) - set(registry_paths))
        if missing_entry_projections:
            structure_violations.append(
                {"field": "entry_authority_projection", "reason": "missing_registered_entries", "rel_paths": missing_entry_projections}
            )
        if extra_entry_projections:
            structure_violations.append(
                {"field": "entry_authority_projection", "reason": "extra_unregistered_entries", "rel_paths": extra_entry_projections}
            )
        missing_anchor_entries = sorted(set(anchor_rel_paths) - set(registry_paths))
        if missing_anchor_entries:
            structure_violations.append(
                {"field": "authority_anchor_checks", "reason": "unregistered_anchor_entries", "rel_paths": missing_anchor_entries}
            )
        for rel_path in anchor_rel_paths:
            entry_kind = registry_entry_kind_map.get(rel_path)
            if entry_kind is None:
                continue
            if entry_kind != "file":
                structure_violations.append(
                    {
                        "field": "authority_anchor_checks",
                        "reason": "anchor_must_target_file_entry",
                        "rel_path": rel_path,
                        "entry_kind": entry_kind,
                    }
                )
            if not bool(registry_entry_law_bearing_map.get(rel_path, False)):
                structure_violations.append(
                    {
                        "field": "authority_anchor_checks",
                        "reason": "anchor_must_target_law_bearing_entry",
                        "rel_path": rel_path,
                    }
                )

        for row in class_profiles:
            if row.authority_mode not in ALLOWED_AUTHORITY_MODES:
                structure_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "invalid_authority_mode",
                        "corpus_class": row.corpus_class,
                        "authority_mode": row.authority_mode,
                    }
                )
            expected = EXPECTED_CLASS_RULES.get(row.corpus_class)
            if expected is None:
                continue
            if row.authority_role != expected["authority_role"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_role_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_role"],
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != expected["authority_mode"]:
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "authority_mode_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": expected["authority_mode"],
                        "actual": row.authority_mode,
                    }
                )
            if bool(row.philosophical_primacy) != bool(expected["philosophical_primacy"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "philosophical_primacy_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["philosophical_primacy"]),
                        "actual": bool(row.philosophical_primacy),
                    }
                )
            if bool(row.law_bearing_required) != bool(expected["law_bearing_required"]):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "law_bearing_required_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(expected["law_bearing_required"]),
                        "actual": bool(row.law_bearing_required),
                    }
                )
            registry_law_bearing = registry_class_law_bearing.get(row.corpus_class)
            if registry_law_bearing is not None and bool(row.law_bearing_required) != bool(registry_law_bearing):
                authority_violations.append(
                    {
                        "field": "authority_class_profiles",
                        "reason": "registry_law_bearing_mismatch",
                        "corpus_class": row.corpus_class,
                        "expected": bool(registry_law_bearing),
                        "actual": bool(row.law_bearing_required),
                    }
                )

        primacy_classes = sorted(row.corpus_class for row in class_profiles if row.philosophical_primacy)
        if primacy_classes != ["bottom_theory"]:
            authority_violations.append(
                {
                    "field": "authority_class_profiles",
                    "reason": "philosophical_primacy_not_exclusive_to_bottom_theory",
                    "corpus_classes": primacy_classes,
                }
            )

        for row in entry_projections:
            expected_class = registry_entry_class_map.get(row.rel_path)
            if expected_class and row.corpus_class != expected_class:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_corpus_class_mismatch",
                        "rel_path": row.rel_path,
                        "expected": expected_class,
                        "actual": row.corpus_class,
                    }
                )
            class_profile = class_profile_map.get(row.corpus_class)
            if class_profile is None:
                continue
            if row.authority_role != class_profile.authority_role:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_role_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_role,
                        "actual": row.authority_role,
                    }
                )
            if row.authority_mode != class_profile.authority_mode:
                authority_violations.append(
                    {
                        "field": "entry_authority_projection",
                        "reason": "entry_authority_mode_mismatch",
                        "rel_path": row.rel_path,
                        "expected": class_profile.authority_mode,
                        "actual": row.authority_mode,
                    }
                )

        if root_index_entry:
            root_index_projection = entry_projection_map.get(root_index_entry)
            if root_index_projection is None:
                authority_violations.append(
                    {"field": "entry_authority_projection", "reason": "root_index_entry_missing_projection", "rel_path": root_index_entry}
                )
            else:
                if root_index_projection.corpus_class != "root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_class",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.corpus_class,
                        }
                    )
                if root_index_projection.authority_role != "navigational_root_index":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_role",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_role,
                        }
                    )
                if root_index_projection.authority_mode != "navigational_only":
                    authority_violations.append(
                        {
                            "field": "entry_authority_projection",
                            "reason": "root_index_entry_wrong_mode",
                            "rel_path": root_index_entry,
                            "actual": root_index_projection.authority_mode,
                        }
                    )

        if ordering_reading_paths and ordering_reading_paths != registry_paths:
            # Registry paths are alphabetical, ordering paths are semantic. No violation here.
            pass

        for anchor in anchor_checks:
            path = (repo_root / anchor.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append(
                    {"field": "authority_anchor_checks", "reason": "anchor_file_missing", "rel_path": anchor.rel_path}
                )
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            missing_markers = find_missing_markers(text, anchor.required_markers)
            for marker in missing_markers:
                anchor_violations.append(
                    {
                        "field": "authority_anchor_checks",
                        "reason": "required_marker_missing",
                        "rel_path": anchor.rel_path,
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (authority_violations or anchor_violations):
        error_code = ERR_AUTHORITY

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"authority_violation:{row['field']}:{row['reason']}" for row in authority_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_AUTHORITY),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "root_dir": str(authority_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "authority_anchor_check_count": len(anchor_checks),
        "authority_class_profile_count": len(class_profiles),
        "entry_authority_projection_count": len(entry_projections),
        "authority_class_profiles": [
            {
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
                "philosophical_primacy": row.philosophical_primacy,
                "law_bearing_required": row.law_bearing_required,
            }
            for row in class_profiles
        ],
        "entry_authority_projection": [
            {
                "rel_path": row.rel_path,
                "corpus_class": row.corpus_class,
                "authority_role": row.authority_role,
                "authority_mode": row.authority_mode,
            }
            for row in entry_projections
        ],
        "structure_violations": structure_violations,
        "authority_violations": authority_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
