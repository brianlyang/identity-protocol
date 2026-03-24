#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


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


def validate_governed_subdomain_doc_control(
    *,
    repo_root: Path,
    doc_control_rel: str,
    expected_subdomain_id: str,
    status_key: str,
    error_code: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        status_key: STATUS_FAIL_REQUIRED,
        "doc_control_rel": str(doc_control_rel or "").strip(),
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

    doc_control_path, active_file, alias_error = resolve_current_yaml_alias(repo_root, doc_control_rel)
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
