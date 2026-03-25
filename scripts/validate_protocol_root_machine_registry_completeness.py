#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from typing import Any

from registry_alias_control_plane_common import resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root
from root_corpus_governance_common import find_missing_markers, load_root_corpus_registry, root_corpus_entries_from_registry
from root_machine_registry_completeness_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_checks_from_doc,
    load_root_machine_registry_completeness,
)

STATUS_KEY = "protocol_root_machine_registry_completeness_status"
ERR_REGISTRY = "IP-RMRC-001"
ERR_STRUCTURE = "IP-RMRC-002"
ERR_COMPLETENESS = "IP-RMRC-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate protocol-root machine-registry completeness for governed root mapping families."
    )
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    completeness_doc, completeness_entry_path, completeness_active_path, completeness_alias_error = (
        load_root_machine_registry_completeness(repo_root)
    )
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    completeness_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    family_status_rows: list[dict[str, Any]] = []
    error_code = ""

    for prefix, doc, alias_error, empty_reason in (
        (
            "root_machine_registry_completeness",
            completeness_doc,
            completeness_alias_error,
            "root_machine_registry_completeness_empty_or_invalid",
        ),
        ("root_corpus_registry", registry_doc, registry_alias_error, "root_corpus_registry_empty_or_invalid"),
    ):
        if alias_error:
            stale_reasons.append(f"{prefix}_alias_error:{alias_error}")
            error_code = ERR_REGISTRY
        elif not doc:
            stale_reasons.append(empty_reason)
            error_code = ERR_REGISTRY

    anchor_checks = anchor_checks_from_doc(completeness_doc) if completeness_doc else ()
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()

    if not stale_reasons:
        expected_scalar_fields = {
            "completeness_family": "protocol_root_machine_registry_completeness",
            "completeness_version": "v1",
            "registry_directory_rel_path": "identity/protocol/mappings",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "validator_script": "scripts/validate_protocol_root_machine_registry_completeness.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh",
            "common_script": "scripts/root_machine_registry_completeness_common.py",
            "root_family_prefix": "root-",
            "current_suffix": ".current.yaml",
            "version_regex": r"^root-[a-z0-9-]+\.v[0-9]+\.yaml$",
        }
        for field, expected in expected_scalar_fields.items():
            actual = str(completeness_doc.get(field) or "").strip()
            if actual != expected:
                stale_reasons.append(f"root_machine_registry_completeness_field_invalid:{field}")
                error_code = ERR_REGISTRY

        if completeness_doc.get("require_current_version_pairs") is not True:
            stale_reasons.append("root_machine_registry_completeness_pairing_rule_invalid")
            error_code = ERR_REGISTRY

        if not anchor_checks:
            stale_reasons.append("root_machine_registry_completeness_anchor_checks_missing")
            error_code = ERR_REGISTRY

        for field in ("registry_current_file", "validator_script", "probe_script", "common_script"):
            rel_path = str(completeness_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_machine_registry_completeness_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY

    version_re = None
    if not stale_reasons:
        try:
            version_re = re.compile(str(completeness_doc.get("version_regex") or "").strip())
        except re.error:
            structure_violations.append({"field": "version_regex", "reason": "regex_invalid"})
        if structure_violations:
            error_code = ERR_STRUCTURE

    if not stale_reasons and not structure_violations:
        registry_directory_rel = str(completeness_doc.get("registry_directory_rel_path") or "").strip()
        registry_dir = (repo_root / registry_directory_rel).resolve()
        if not registry_dir.exists() or not registry_dir.is_dir():
            completeness_violations.append(
                {
                    "field": "registry_directory",
                    "reason": "registry_directory_missing",
                    "rel_path": registry_directory_rel,
                }
            )
        registry_map = {row.rel_path: row for row in registry_entries}
        mappings_entry = registry_map.get("identity/protocol/mappings")
        if mappings_entry is None:
            completeness_violations.append(
                {
                    "field": "root_corpus_registry",
                    "reason": "mappings_directory_not_registered",
                }
            )
            registered_children: set[str] = set()
        else:
            registered_children = set(mappings_entry.required_children)

        if registry_dir.exists() and registry_dir.is_dir():
            prefix = str(completeness_doc.get("root_family_prefix") or "")
            current_suffix = str(completeness_doc.get("current_suffix") or "")
            root_yaml_files = sorted(
                path.name
                for path in registry_dir.iterdir()
                if path.is_file() and path.name.startswith(prefix) and path.name.endswith(".yaml")
            )
            actual_root_yaml_set = set(root_yaml_files)

            families: dict[str, dict[str, Any]] = {}
            for name in root_yaml_files:
                if current_suffix and name.endswith(current_suffix):
                    family_id = name[: -len(current_suffix)]
                    row = families.setdefault(family_id, {"current_file": "", "version_files": []})
                    if row["current_file"]:
                        structure_violations.append(
                            {"field": "root_mapping_family", "reason": "duplicate_current_file", "family_id": family_id}
                        )
                    row["current_file"] = name
                elif version_re and version_re.fullmatch(name):
                    family_id = name.split(".v", 1)[0]
                    row = families.setdefault(family_id, {"current_file": "", "version_files": []})
                    row["version_files"].append(name)
                else:
                    structure_violations.append(
                        {"field": "root_mapping_family", "reason": "unclassifiable_root_yaml", "filename": name}
                    )

            for child in sorted(child for child in registered_children if child.startswith(prefix) and child.endswith(".yaml")):
                if child not in actual_root_yaml_set:
                    completeness_violations.append(
                        {"field": "registered_child", "reason": "registered_child_missing_on_disk", "child": child}
                    )

            for family_id in sorted(families):
                row = families[family_id]
                current_file = str(row.get("current_file") or "")
                version_files = sorted(set(str(item) for item in row.get("version_files") or [] if str(item)))
                family_violations: list[str] = []
                active_file = ""
                alias_error = ""

                if not current_file:
                    family_violations.append("current_file_missing")
                    completeness_violations.append(
                        {"field": "root_mapping_family", "reason": "current_file_missing", "family_id": family_id}
                    )
                elif current_file not in registered_children:
                    family_violations.append("current_file_not_registered")
                    completeness_violations.append(
                        {
                            "field": "root_mapping_family",
                            "reason": "current_file_not_registered",
                            "family_id": family_id,
                            "child": current_file,
                        }
                    )

                if completeness_doc.get("require_current_version_pairs") and not version_files:
                    family_violations.append("version_file_missing")
                    completeness_violations.append(
                        {"field": "root_mapping_family", "reason": "version_file_missing", "family_id": family_id}
                    )

                for version_file in version_files:
                    if version_file not in registered_children:
                        family_violations.append("version_file_not_registered")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "version_file_not_registered",
                                "family_id": family_id,
                                "child": version_file,
                            }
                        )

                if current_file:
                    current_rel = f"{registry_directory_rel}/{current_file}"
                    active_path, active_ref, alias_error = resolve_current_yaml_alias(repo_root, current_rel)
                    active_file = active_path.name if active_path else ""
                    if alias_error:
                        family_violations.append("current_alias_error")
                        completeness_violations.append(
                            {
                                "field": "root_mapping_family",
                                "reason": "current_alias_error",
                                "family_id": family_id,
                                "alias_error": alias_error,
                            }
                        )
                    else:
                        if active_file not in version_files:
                            family_violations.append("active_file_not_in_family_versions")
                            completeness_violations.append(
                                {
                                    "field": "root_mapping_family",
                                    "reason": "active_file_not_in_family_versions",
                                    "family_id": family_id,
                                    "active_file": active_ref,
                                }
                            )
                        if active_file not in registered_children:
                            family_violations.append("active_file_not_registered")
                            completeness_violations.append(
                                {
                                    "field": "root_mapping_family",
                                    "reason": "active_file_not_registered",
                                    "family_id": family_id,
                                    "child": active_file,
                                }
                            )

                family_status_rows.append(
                    {
                        "family_id": family_id,
                        "current_file": current_file,
                        "version_files": version_files,
                        "active_file": active_file,
                        "alias_error": alias_error,
                        "family_status": STATUS_PASS_REQUIRED if not family_violations else STATUS_FAIL_REQUIRED,
                        "family_violations": family_violations,
                    }
                )

        for check in anchor_checks:
            path = (repo_root / check.rel_path).resolve()
            if not path.exists() or not path.is_file():
                anchor_violations.append({"rel_path": check.rel_path, "reason": "anchor_file_missing"})
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for marker in find_missing_markers(text, check.required_markers):
                anchor_violations.append(
                    {
                        "rel_path": check.rel_path,
                        "reason": "required_marker_missing",
                        "marker": marker,
                    }
                )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (completeness_violations or anchor_violations):
        error_code = ERR_COMPLETENESS

    stale_reasons.extend(
        f"structure_violation:{row['field']}:{row['reason']}:{row.get('family_id', row.get('filename', ''))}".rstrip(":")
        for row in structure_violations
    )
    stale_reasons.extend(
        f"completeness_violation:{row['field']}:{row['reason']}:{row.get('family_id', row.get('child', ''))}".rstrip(":")
        for row in completeness_violations
    )
    stale_reasons.extend(
        f"anchor_violation:{row['rel_path']}:{row['reason']}:{row.get('marker', '')}".rstrip(":")
        for row in anchor_violations
    )

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    payload = {
        STATUS_KEY: status,
        "completeness_family": str(completeness_doc.get("completeness_family") or ""),
        "completeness_version": str(completeness_doc.get("completeness_version") or ""),
        "mapping_entry_file": str(completeness_entry_path.relative_to(repo_root)),
        "mapping_active_file": str(completeness_active_path.relative_to(repo_root)),
        "registry_entry_file": str(registry_entry_path.relative_to(repo_root)),
        "registry_active_file": str(registry_active_path.relative_to(repo_root)),
        "family_count": len(family_status_rows),
        "family_ids": [row["family_id"] for row in family_status_rows],
        "family_status_rows": family_status_rows,
        "structure_violations": structure_violations,
        "completeness_violations": completeness_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
        "error_code": error_code,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
