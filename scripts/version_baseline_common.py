#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

VERSION_BASELINE_CURRENT_REL = "identity/protocol/mappings/version-baseline.current.yaml"

REQUIRED_AGENT_IDENTITY_FIELDS: tuple[str, ...] = (
    "methodology_version",
    "prompt_version",
    "json_version",
)
REQUIRED_SCAFFOLD_METADATA_FIELDS: tuple[str, ...] = (
    "protocol_contract_version",
    "required_version_stream",
    "required_gate_bundle_contract_version",
    "identity_protocol_version",
)
REQUIRED_CATALOG_FIELDS: tuple[str, ...] = ("methodology_version",)
REQUIRED_META_FIELDS: tuple[str, ...] = ("methodology_version",)


class VersionBaselineResolutionError(RuntimeError):
    pass


def _safe_load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _non_empty_text(value: Any) -> str:
    return str(value or "").strip()


def _collect_section_tokens(section: Any, required_fields: tuple[str, ...]) -> tuple[dict[str, str], list[str]]:
    section_doc = section if isinstance(section, dict) else {}
    out: dict[str, str] = {}
    missing: list[str] = []
    for field in required_fields:
        token = _non_empty_text(section_doc.get(field))
        if not token:
            missing.append(field)
            continue
        out[field] = token
    return out, missing


def resolve_version_baseline(
    *,
    repo_root: Path,
    current_file: str = VERSION_BASELINE_CURRENT_REL,
) -> dict[str, Any]:
    entry_path = (repo_root / str(current_file or VERSION_BASELINE_CURRENT_REL)).resolve()
    resolved_path = entry_path
    active_file = ""
    error = ""

    if not entry_path.exists() or not entry_path.is_file():
        error = "version_baseline_current_missing"
        return {
            "ok": False,
            "error": error,
            "entry_path": str(entry_path),
            "resolved_path": str(resolved_path),
            "active_file": active_file,
            "stream_version": "",
            "agent_identity": {},
            "scaffold_metadata": {},
            "catalog": {},
            "meta": {},
            "missing_fields": [],
        }

    entry_doc = _safe_load_yaml(entry_path)
    if entry_path.name.endswith(".current.yaml"):
        active_file = _non_empty_text(entry_doc.get("active_file"))
        if not active_file:
            error = "version_baseline_active_file_missing"
            return {
                "ok": False,
                "error": error,
                "entry_path": str(entry_path),
                "resolved_path": str(resolved_path),
                "active_file": active_file,
                "stream_version": "",
                "agent_identity": {},
                "scaffold_metadata": {},
                "catalog": {},
                "meta": {},
                "missing_fields": [],
            }
        resolved_path = (repo_root / active_file).resolve()

    if not resolved_path.exists() or not resolved_path.is_file():
        error = "version_baseline_active_file_not_found"
        return {
            "ok": False,
            "error": error,
            "entry_path": str(entry_path),
            "resolved_path": str(resolved_path),
            "active_file": active_file,
            "stream_version": "",
            "agent_identity": {},
            "scaffold_metadata": {},
            "catalog": {},
            "meta": {},
            "missing_fields": [],
        }

    baseline_doc = _safe_load_yaml(resolved_path)
    if not baseline_doc:
        error = "version_baseline_parse_failed"
        return {
            "ok": False,
            "error": error,
            "entry_path": str(entry_path),
            "resolved_path": str(resolved_path),
            "active_file": active_file,
            "stream_version": "",
            "agent_identity": {},
            "scaffold_metadata": {},
            "catalog": {},
            "meta": {},
            "missing_fields": [],
        }

    stream_version = _non_empty_text(baseline_doc.get("stream_version"))
    agent_identity, missing_agent = _collect_section_tokens(
        baseline_doc.get("agent_identity"), REQUIRED_AGENT_IDENTITY_FIELDS
    )
    scaffold_metadata, missing_scaffold = _collect_section_tokens(
        baseline_doc.get("scaffold_metadata"), REQUIRED_SCAFFOLD_METADATA_FIELDS
    )
    catalog, missing_catalog = _collect_section_tokens(
        baseline_doc.get("catalog"), REQUIRED_CATALOG_FIELDS
    )
    meta, missing_meta = _collect_section_tokens(
        baseline_doc.get("meta"), REQUIRED_META_FIELDS
    )

    missing_fields: list[str] = []
    if not stream_version:
        missing_fields.append("stream_version")
    missing_fields.extend(f"agent_identity.{field}" for field in missing_agent)
    missing_fields.extend(f"scaffold_metadata.{field}" for field in missing_scaffold)
    missing_fields.extend(f"catalog.{field}" for field in missing_catalog)
    missing_fields.extend(f"meta.{field}" for field in missing_meta)

    ok = not missing_fields
    error = "" if ok else "version_baseline_required_fields_missing"

    return {
        "ok": ok,
        "error": error,
        "entry_path": str(entry_path),
        "resolved_path": str(resolved_path),
        "active_file": active_file,
        "stream_version": stream_version,
        "agent_identity": agent_identity,
        "scaffold_metadata": scaffold_metadata,
        "catalog": catalog,
        "meta": meta,
        "missing_fields": missing_fields,
    }


def load_version_baseline_or_raise(
    *,
    repo_root: Path,
    current_file: str = VERSION_BASELINE_CURRENT_REL,
) -> dict[str, Any]:
    state = resolve_version_baseline(repo_root=repo_root, current_file=current_file)
    if not state.get("ok"):
        reason = _non_empty_text(state.get("error")) or "version_baseline_unavailable"
        missing = [str(x).strip() for x in (state.get("missing_fields") or []) if str(x).strip()]
        detail = reason if not missing else f"{reason}:{','.join(missing)}"
        raise VersionBaselineResolutionError(detail)
    return state


def apply_version_baseline_to_task_doc(task_doc: dict[str, Any], baseline: dict[str, Any]) -> bool:
    changed = False
    if not isinstance(task_doc, dict):
        return changed

    agent = task_doc.get("agent_identity")
    if not isinstance(agent, dict):
        agent = {}
        task_doc["agent_identity"] = agent
        changed = True
    for field, token in (baseline.get("agent_identity") or {}).items():
        value = _non_empty_text(token)
        if not value:
            continue
        if _non_empty_text(agent.get(field)) != value:
            agent[field] = value
            changed = True

    scaffold = task_doc.get("scaffold_metadata")
    if not isinstance(scaffold, dict):
        scaffold = {}
        task_doc["scaffold_metadata"] = scaffold
        changed = True
    for field, token in (baseline.get("scaffold_metadata") or {}).items():
        value = _non_empty_text(token)
        if not value:
            continue
        if _non_empty_text(scaffold.get(field)) != value:
            scaffold[field] = value
            changed = True

    return changed


def apply_version_baseline_to_catalog_row(row: dict[str, Any], baseline: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    changed = False
    methodology_version = _non_empty_text(((baseline.get("catalog") or {}).get("methodology_version")))
    if methodology_version and _non_empty_text(row.get("methodology_version")) != methodology_version:
        row["methodology_version"] = methodology_version
        changed = True
    return changed


def apply_version_baseline_to_meta_doc(meta_doc: dict[str, Any], baseline: dict[str, Any]) -> bool:
    if not isinstance(meta_doc, dict):
        return False
    changed = False
    methodology_version = _non_empty_text(((baseline.get("meta") or {}).get("methodology_version")))
    if methodology_version and _non_empty_text(meta_doc.get("methodology_version")) != methodology_version:
        meta_doc["methodology_version"] = methodology_version
        changed = True
    return changed
