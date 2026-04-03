#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from governed_subdomain_doc_control_common import (
    governed_subdomain_doc_control_entries_from_registry,
    load_governed_subdomain_doc_control_registry,
)
from registry_alias_control_plane_common import resolve_current_yaml_alias
from repo_root_resolution_common import resolve_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_KEY = "protocol_governed_subdomain_doc_control_registry_status"
ERR_REGISTRY = "IP-GSD-001"
ERR_STRUCTURE = "IP-GSD-002"
ERR_BINDING = "IP-GSD-003"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate governed subdomain doc-control registry bindings.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = (
        load_governed_subdomain_doc_control_registry(repo_root)
    )

    payload: dict[str, Any] = {
        STATUS_KEY: STATUS_FAIL_REQUIRED,
        "error_code": ERR_REGISTRY,
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "registry_family": "",
        "registry_version": "",
        "subdomain_count": 0,
        "subdomain_bindings": [],
        "structure_violations": [],
        "binding_violations": [],
        "stale_reasons": [],
    }

    if registry_alias_error:
        payload["stale_reasons"].append(f"registry_alias_error:{registry_alias_error}")
        _emit(payload, json_only=args.json_only)
        return 1
    if not registry_doc:
        payload["stale_reasons"].append("registry_parse_failed")
        _emit(payload, json_only=args.json_only)
        return 1

    payload["registry_family"] = str(registry_doc.get("registry_family", "")).strip()
    payload["registry_version"] = str(registry_doc.get("registry_version", "")).strip()
    if payload["registry_family"] != "governed_subdomain_doc_control":
        payload["stale_reasons"].append("registry_family_invalid")
    if payload["registry_version"] != "v1":
        payload["stale_reasons"].append("registry_version_invalid")

    rows = registry_doc.get("subdomains")
    if not isinstance(rows, list):
        payload["stale_reasons"].append("subdomains_missing")
        _emit(payload, json_only=args.json_only)
        return 1

    entries = governed_subdomain_doc_control_entries_from_registry(registry_doc)
    payload["subdomain_count"] = len(entries)
    if not entries:
        payload["stale_reasons"].append("subdomains_empty")

    seen_ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            payload["structure_violations"].append({"reason": "non_mapping_subdomain_row"})
            continue
        subdomain_id = str(row.get("subdomain_id", "")).strip()
        if not subdomain_id:
            payload["structure_violations"].append({"reason": "missing_subdomain_id"})
            continue
        if subdomain_id in seen_ids:
            payload["structure_violations"].append({"reason": "duplicate_subdomain_id", "subdomain_id": subdomain_id})
            continue
        seen_ids.add(subdomain_id)

        current_file = str(row.get("current_file", "")).strip()
        root_readme = str(row.get("root_readme", "")).strip()
        validator_script = str(row.get("validator_script", "")).strip()
        probe_script = str(row.get("probe_script", "")).strip()
        binding_row = {
            "subdomain_id": subdomain_id,
            "current_file": current_file,
            "root_readme": root_readme,
            "validator_script": validator_script,
            "probe_script": probe_script,
            "active_doc_control_file": "",
        }
        payload["subdomain_bindings"].append(binding_row)

        for field_name, rel in (
            ("current_file", current_file),
            ("root_readme", root_readme),
            ("validator_script", validator_script),
            ("probe_script", probe_script),
        ):
            if not rel:
                payload["binding_violations"].append(
                    {"subdomain_id": subdomain_id, "field": field_name, "reason": "missing_field"}
                )
                continue
            path = (repo_root / rel).resolve()
            if not path.exists():
                payload["binding_violations"].append(
                    {"subdomain_id": subdomain_id, "field": field_name, "reason": "path_missing", "rel_path": rel}
                )

        if current_file:
            active_doc_control_path, active_file, alias_error = resolve_current_yaml_alias(repo_root, current_file)
            binding_row["active_doc_control_file"] = str(active_file or "")
            if alias_error:
                payload["binding_violations"].append(
                    {"subdomain_id": subdomain_id, "field": "current_file", "reason": "alias_error", "detail": alias_error}
                )
            elif not active_doc_control_path.exists():
                payload["binding_violations"].append(
                    {"subdomain_id": subdomain_id, "field": "current_file", "reason": "active_file_missing"}
                )
            else:
                doc_control_doc = _load_yaml(active_doc_control_path)
                if not doc_control_doc:
                    payload["binding_violations"].append(
                        {"subdomain_id": subdomain_id, "field": "current_file", "reason": "doc_control_parse_failed"}
                    )
                else:
                    if str(doc_control_doc.get("doc_control_family", "")).strip() != "governed_subdomain_doc_control":
                        payload["binding_violations"].append(
                            {
                                "subdomain_id": subdomain_id,
                                "field": "current_file",
                                "reason": "doc_control_family_invalid",
                            }
                        )
                    if str(doc_control_doc.get("subdomain_id", "")).strip() != subdomain_id:
                        payload["binding_violations"].append(
                            {
                                "subdomain_id": subdomain_id,
                                "field": "current_file",
                                "reason": "doc_control_subdomain_id_mismatch",
                            }
                        )
                    docs_cfg = doc_control_doc.get("docs") or {}
                    if root_readme and str(docs_cfg.get("root_readme", "")).strip() != root_readme:
                        payload["binding_violations"].append(
                            {
                                "subdomain_id": subdomain_id,
                                "field": "root_readme",
                                "reason": "doc_control_root_readme_mismatch",
                            }
                        )

    violation_count = (
        len(payload["stale_reasons"]) + len(payload["structure_violations"]) + len(payload["binding_violations"])
    )
    if violation_count == 0:
        payload[STATUS_KEY] = STATUS_PASS_REQUIRED
        payload["error_code"] = ""
    elif payload["structure_violations"]:
        payload["error_code"] = ERR_STRUCTURE
    elif payload["binding_violations"]:
        payload["error_code"] = ERR_BINDING

    _emit(payload, json_only=args.json_only)
    return 0 if payload[STATUS_KEY] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
