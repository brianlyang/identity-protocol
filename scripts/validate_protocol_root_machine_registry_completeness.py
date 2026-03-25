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
    extract_validator_error_codes,
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    anchor_checks_from_doc,
    extract_validator_status_key,
    load_mapping_descriptor,
    load_root_machine_registry_completeness,
    repo_rel_path_escape_policy_from_doc,
    repo_rel_path_scope_policy_from_doc,
    resolve_repo_relative_surface,
    required_descriptor_field_modes_from_doc,
    required_descriptor_fields_from_doc,
    require_self_describing_families,
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
    self_describing_required = require_self_describing_families(completeness_doc) if completeness_doc else False
    required_descriptor_fields = required_descriptor_fields_from_doc(completeness_doc) if completeness_doc else ()
    required_descriptor_field_modes = required_descriptor_field_modes_from_doc(completeness_doc) if completeness_doc else {}
    repo_rel_path_scope_policy = repo_rel_path_scope_policy_from_doc(completeness_doc) if completeness_doc else ""
    repo_rel_path_escape_policy = repo_rel_path_escape_policy_from_doc(completeness_doc) if completeness_doc else ""

    if not stale_reasons:
        expected_scalar_fields = {
            "completeness_family": "protocol_root_machine_registry_completeness",
            "completeness_version": "v1",
            "registry_directory_rel_path": "identity/protocol/mappings",
            "registry_current_file": "identity/protocol/mappings/root-corpus-registry.current.yaml",
            "validator_script": "scripts/validate_protocol_root_machine_registry_completeness.py",
            "probe_script": "scripts/ci/run_protocol_root_machine_registry_completeness_probes_ci.sh",
            "common_script": "scripts/root_machine_registry_completeness_common.py",
            "status_key": STATUS_KEY,
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
        if self_describing_required and not required_descriptor_fields:
            stale_reasons.append("root_machine_registry_completeness_descriptor_fields_missing")
            error_code = ERR_REGISTRY
        if repo_rel_path_scope_policy != "repo_root_relative_only":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_scope_policy_invalid")
            error_code = ERR_REGISTRY
        if repo_rel_path_escape_policy != "fail_closed":
            stale_reasons.append("root_machine_registry_completeness_repo_rel_path_escape_policy_invalid")
            error_code = ERR_REGISTRY
        if tuple(required_descriptor_fields) != ("validator_script", "probe_script", "common_script", "status_key", "error_codes"):
            stale_reasons.append("root_machine_registry_completeness_descriptor_fields_invalid")
            error_code = ERR_REGISTRY
        if required_descriptor_field_modes != {
            "validator_script": "repo_rel_path",
            "probe_script": "repo_rel_path",
            "common_script": "repo_rel_path",
            "status_key": "validator_status_key",
            "error_codes": "validator_error_code_list",
        }:
            stale_reasons.append("root_machine_registry_completeness_descriptor_field_modes_invalid")
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
                descriptor_field_rows: list[dict[str, Any]] = []

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
                        elif self_describing_required:
                            active_doc = load_mapping_descriptor(active_path)
                            if not active_doc:
                                family_violations.append("active_mapping_doc_invalid")
                                completeness_violations.append(
                                    {
                                        "field": "root_mapping_family",
                                        "reason": "active_mapping_doc_invalid",
                                        "family_id": family_id,
                                        "active_file": active_file,
                                    }
                                )
                            else:
                                for descriptor_field in required_descriptor_fields:
                                    descriptor_mode = required_descriptor_field_modes.get(descriptor_field, "")
                                    row_status = STATUS_FAIL_REQUIRED
                                    row_payload: dict[str, Any] = {
                                        "field": descriptor_field,
                                        "mode": descriptor_mode,
                                    }
                                    if descriptor_mode == "validator_error_code_list":
                                        raw_codes = active_doc.get(descriptor_field)
                                        descriptor_codes = tuple(
                                            str(item or "").strip()
                                            for item in raw_codes
                                            if str(item or "").strip()
                                        ) if isinstance(raw_codes, list) else ()
                                        expected_codes, error_codes_error = extract_validator_error_codes(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        row_payload["values"] = list(descriptor_codes)
                                        row_payload["expected_values"] = list(expected_codes)
                                        row_payload["support_error"] = error_codes_error
                                        row_status = (
                                            STATUS_PASS_REQUIRED
                                            if descriptor_codes and not error_codes_error and descriptor_codes == expected_codes
                                            else STATUS_FAIL_REQUIRED
                                        )
                                        descriptor_field_rows.append({**row_payload, "status": row_status})
                                        if not descriptor_codes:
                                            family_violations.append("descriptor_field_missing")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_field_missing",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                }
                                            )
                                        elif error_codes_error:
                                            family_violations.append("descriptor_supporting_surface_invalid")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_supporting_surface_invalid",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "support_error": error_codes_error,
                                                }
                                            )
                                        elif descriptor_codes != expected_codes:
                                            family_violations.append("descriptor_value_mismatch")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_value_mismatch",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "actual_values": list(descriptor_codes),
                                                    "expected_values": list(expected_codes),
                                                }
                                            )
                                        continue

                                    descriptor_value = str(active_doc.get(descriptor_field) or "").strip()
                                    row_payload["value"] = descriptor_value
                                    if descriptor_mode == "repo_rel_path":
                                        _rel_path, repo_rel_error, resolved_path = resolve_repo_relative_surface(
                                            repo_root, descriptor_value
                                        )
                                        row_payload["resolved_path"] = resolved_path
                                        row_payload["support_error"] = repo_rel_error
                                        row_status = STATUS_PASS_REQUIRED if descriptor_value and not repo_rel_error else STATUS_FAIL_REQUIRED
                                    elif descriptor_mode == "validator_status_key":
                                        expected_status_key, status_key_error = extract_validator_status_key(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        row_payload["expected_value"] = expected_status_key
                                        row_payload["support_error"] = status_key_error
                                        row_status = (
                                            STATUS_PASS_REQUIRED
                                            if descriptor_value and not status_key_error and descriptor_value == expected_status_key
                                            else STATUS_FAIL_REQUIRED
                                        )
                                    descriptor_field_rows.append(
                                        {
                                            **row_payload,
                                            "status": row_status,
                                        }
                                    )
                                    if not descriptor_value:
                                        family_violations.append("descriptor_field_missing")
                                        completeness_violations.append(
                                            {
                                                "field": "root_mapping_family",
                                                "reason": "descriptor_field_missing",
                                                "family_id": family_id,
                                                "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                }
                                            )
                                    elif descriptor_mode == "repo_rel_path":
                                        _rel_path, repo_rel_error, resolved_path = resolve_repo_relative_surface(
                                            repo_root, descriptor_value
                                        )
                                        if repo_rel_error == "absolute_path_forbidden":
                                            family_violations.append("descriptor_path_not_repo_relative")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_not_repo_relative",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                        elif repo_rel_error == "repo_root_escape_forbidden":
                                            family_violations.append("descriptor_path_escapes_repo_root")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_escapes_repo_root",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                        elif repo_rel_error == "path_missing":
                                            family_violations.append("descriptor_path_missing")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_path_missing",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "rel_path": descriptor_value,
                                                    "resolved_path": resolved_path,
                                                }
                                            )
                                    elif descriptor_mode == "validator_status_key":
                                        expected_status_key, status_key_error = extract_validator_status_key(
                                            repo_root,
                                            str(active_doc.get("validator_script") or "").strip(),
                                        )
                                        if status_key_error:
                                            family_violations.append("descriptor_supporting_surface_invalid")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_supporting_surface_invalid",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "support_error": status_key_error,
                                                }
                                            )
                                        elif descriptor_value != expected_status_key:
                                            family_violations.append("descriptor_value_mismatch")
                                            completeness_violations.append(
                                                {
                                                    "field": "root_mapping_family",
                                                    "reason": "descriptor_value_mismatch",
                                                    "family_id": family_id,
                                                    "active_file": active_file,
                                                    "descriptor_field": descriptor_field,
                                                    "actual_value": descriptor_value,
                                                    "expected_value": expected_status_key,
                                                }
                                            )

                family_status_rows.append(
                    {
                        "family_id": family_id,
                        "current_file": current_file,
                        "version_files": version_files,
                        "active_file": active_file,
                        "alias_error": alias_error,
                        "self_describing_required": self_describing_required,
                        "required_descriptor_fields": list(required_descriptor_fields),
                        "required_descriptor_field_modes": dict(required_descriptor_field_modes),
                        "descriptor_field_rows": descriptor_field_rows,
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
        "required_descriptor_fields": list(required_descriptor_fields),
        "required_descriptor_field_modes": dict(required_descriptor_field_modes),
        "repo_rel_path_scope_policy": repo_rel_path_scope_policy,
        "repo_rel_path_escape_policy": repo_rel_path_escape_policy,
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
