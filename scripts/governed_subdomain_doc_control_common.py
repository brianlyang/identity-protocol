#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
GOVERNED_SUBDOMAIN_DOC_CONTROL_REGISTRY_CURRENT = (
    "identity/protocol/mappings/governed-subdomain-doc-control.current.yaml"
)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def load_governed_subdomain_doc_control_registry(
    repo_root: Path,
) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / GOVERNED_SUBDOMAIN_DOC_CONTROL_REGISTRY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(
        repo_root,
        GOVERNED_SUBDOMAIN_DOC_CONTROL_REGISTRY_CURRENT,
    )
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists() or not active_path.is_file():
        return {}, entry_path, active_path, "active_registry_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def governed_subdomain_doc_control_entries_from_registry(
    registry_doc: dict[str, Any],
) -> dict[str, dict[str, str]]:
    rows = registry_doc.get("subdomains")
    if not isinstance(rows, list):
        return {}
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        subdomain_id = str(row.get("subdomain_id", "")).strip()
        if not subdomain_id:
            continue
        out[subdomain_id] = {
            "current_file": str(row.get("current_file", "")).strip(),
            "root_readme": str(row.get("root_readme", "")).strip(),
            "validator_script": str(row.get("validator_script", "")).strip(),
            "probe_script": str(row.get("probe_script", "")).strip(),
        }
    return out


def validate_governed_subdomain_doc_control(
    *,
    repo_root: Path,
    expected_subdomain_id: str,
    status_key: str,
    error_code: str,
    doc_control_rel: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        status_key: STATUS_FAIL_REQUIRED,
        "governed_subdomain_registry_entry": "",
        "governed_subdomain_registry_active": "",
        "governed_subdomain_registry_alias_error": "",
        "doc_control_rel": "",
        "doc_control_file": "",
        "doc_control_active_file": "",
        "expected_subdomain_id": str(expected_subdomain_id or "").strip(),
        "doc_control_family": "",
        "subdomain_id": "",
        "root_readme": "",
        "required_token_count": 0,
        "required_file_count": 0,
        "missing_tokens": [],
        "missing_files": [],
        "stale_reasons": [],
        "error_code": error_code,
    }

    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = (
        load_governed_subdomain_doc_control_registry(repo_root)
    )
    payload["governed_subdomain_registry_entry"] = str(registry_entry_path)
    payload["governed_subdomain_registry_active"] = str(registry_active_path)
    payload["governed_subdomain_registry_alias_error"] = str(registry_alias_error or "").strip()
    registry_row: dict[str, str] = {}
    if registry_alias_error:
        payload["stale_reasons"].append(f"governed_subdomain_registry_alias_error:{registry_alias_error}")
        return payload
    registry_entries = governed_subdomain_doc_control_entries_from_registry(registry_doc)
    registry_row = registry_entries.get(payload["expected_subdomain_id"], {})
    if not registry_row:
        payload["stale_reasons"].append("governed_subdomain_registry_missing_subdomain")
        return payload

    resolved_doc_control_rel = str(doc_control_rel or "").strip() or registry_row.get("current_file", "")
    payload["doc_control_rel"] = resolved_doc_control_rel
    if not resolved_doc_control_rel:
        payload["stale_reasons"].append("governed_subdomain_registry_current_file_missing")
        return payload

    doc_control_path, active_file, alias_error = resolve_current_yaml_alias(repo_root, resolved_doc_control_rel)
    payload["doc_control_file"] = str(doc_control_path)
    payload["doc_control_active_file"] = str(active_file or "")
    if alias_error:
        payload["stale_reasons"].append(f"doc_control_alias_error:{alias_error}")
        return payload

    doc_control_doc = _load_yaml(doc_control_path)
    if not doc_control_doc:
        payload["stale_reasons"].append("doc_control_parse_failed")
        return payload

    payload["doc_control_family"] = str(doc_control_doc.get("doc_control_family", "")).strip()
    payload["subdomain_id"] = str(doc_control_doc.get("subdomain_id", "")).strip()

    if payload["doc_control_family"] != "governed_subdomain_doc_control":
        payload["stale_reasons"].append("doc_control_family_invalid")
    if payload["subdomain_id"] != payload["expected_subdomain_id"]:
        payload["stale_reasons"].append("subdomain_id_mismatch")
    if int(doc_control_doc.get("schema_version", 0) or 0) != 1:
        payload["stale_reasons"].append("schema_version_invalid")

    docs_cfg = doc_control_doc.get("docs")
    if not isinstance(docs_cfg, dict):
        payload["stale_reasons"].append("docs_section_missing")
        return payload

    root_readme_rel = str(docs_cfg.get("root_readme", "")).strip()
    payload["root_readme"] = root_readme_rel
    if not root_readme_rel:
        payload["stale_reasons"].append("root_readme_missing")
        return payload
    registry_root_readme = str(registry_row.get("root_readme", "")).strip()
    if registry_root_readme and registry_root_readme != root_readme_rel:
        payload["stale_reasons"].append("governed_subdomain_registry_root_readme_mismatch")

    root_readme_path = (repo_root / root_readme_rel).resolve()
    if not root_readme_path.exists() or not root_readme_path.is_file():
        payload["stale_reasons"].append("root_readme_not_found")
        return payload

    required_tokens = _as_str_list(docs_cfg.get("root_required_tokens"))
    required_files = _as_str_list(docs_cfg.get("required_files"))
    payload["required_token_count"] = len(required_tokens)
    payload["required_file_count"] = len(required_files)
    if not required_tokens:
        payload["stale_reasons"].append("root_required_tokens_missing")
    if not required_files:
        payload["stale_reasons"].append("required_files_missing")

    readme_text = _read_text(root_readme_path)
    missing_tokens = sorted(token for token in required_tokens if token not in readme_text)
    payload["missing_tokens"] = missing_tokens
    if missing_tokens:
        payload["stale_reasons"].extend(
            f"root_readme_missing_required_token:{token}" for token in missing_tokens
        )

    missing_files: list[str] = []
    for rel in required_files:
        path = (repo_root / rel).resolve()
        if not path.exists() or not path.is_file():
            missing_files.append(rel)
    payload["missing_files"] = missing_files
    if missing_files:
        payload["stale_reasons"].extend(f"required_file_missing:{rel}" for rel in missing_files)

    if not payload["stale_reasons"]:
        payload[status_key] = STATUS_PASS_REQUIRED
    return payload
