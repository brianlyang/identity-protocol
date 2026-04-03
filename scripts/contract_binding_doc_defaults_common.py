#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from contract_binding_mapping_common import collect_requirement_rows

DEFAULT_CONTRACT_BINDING_ENTRY = "identity/protocol/mappings/contract-binding.current.yaml"


def _resolve_current_yaml_alias(repo_root: Path, configured_rel: str) -> Path:
    configured_path = (repo_root / str(configured_rel or "").strip()).resolve()
    if not configured_path.exists() or not configured_path.is_file():
        raise FileNotFoundError(configured_path)
    if not configured_path.name.endswith(".current.yaml"):
        return configured_path
    current_doc = yaml.safe_load(configured_path.read_text(encoding="utf-8")) or {}
    if not isinstance(current_doc, dict):
        raise ValueError(f"current alias must be a mapping: {configured_path}")
    active_file = str(current_doc.get("active_file", "")).strip()
    if not active_file:
        raise ValueError(f"active_file missing: {configured_path}")
    active_path = (repo_root / active_file).resolve()
    if not active_path.exists() or not active_path.is_file():
        raise FileNotFoundError(active_path)
    return active_path


def _load_contract_binding_rows(repo_root: Path, *, entry_rel: str = DEFAULT_CONTRACT_BINDING_ENTRY) -> dict[str, dict[str, Any]]:
    mapping_path = _resolve_current_yaml_alias(repo_root, entry_rel)
    mapping_doc = yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}
    if not isinstance(mapping_doc, dict):
        return {}
    return collect_requirement_rows(mapping_doc)


def _parse_validator_entry(raw_entry: str) -> tuple[str, str]:
    token = str(raw_entry or "").strip()
    if not token:
        return "", ""
    if "::" not in token:
        return token, ""
    script_part, metadata = token.split("::", 1)
    return script_part.strip(), metadata.strip()


def _anchor_doc_path(raw_anchor: str) -> str:
    token = str(raw_anchor or "").strip()
    if not token:
        return ""
    return token.split("#", 1)[0].strip()


def resolve_validator_doc_defaults(
    repo_root: Path,
    *,
    validator_script: str,
    contract_binding_entry: str = DEFAULT_CONTRACT_BINDING_ENTRY,
) -> tuple[str, str]:
    script_token = str(validator_script or "").strip()
    if not script_token:
        return "", ""
    rows = _load_contract_binding_rows(repo_root, entry_rel=contract_binding_entry)
    for row in rows.values():
        validator_ids = row.get("validator_ids") if isinstance(row.get("validator_ids"), list) else []
        for raw_entry in validator_ids:
            script_path, _metadata = _parse_validator_entry(str(raw_entry or ""))
            if script_path != script_token:
                continue
            governance_doc = _anchor_doc_path(str(row.get("governance_anchor", "")))
            review_doc = _anchor_doc_path(str(row.get("review_anchor", "")))
            if governance_doc or review_doc:
                return governance_doc, review_doc
    return "", ""
