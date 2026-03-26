#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
DOC_COMMAND_SURFACE_CURRENT = "identity/protocol/mappings/doc-command-surface.current.yaml"

MODE_LIVE_CONTRACT = "live_contract"
MODE_HISTORICAL_REPLAY_TRACE = "historical_replay_trace"
MODE_COMPATIBILITY_BRIDGE_TRACE = "compatibility_bridge_trace"
DEFAULT_SELF_PREFIXES = ("identity-protocol-local",)


@dataclass(frozen=True)
class DocCommandSurfaceModeProfile:
    mode: str
    enforce_script_existence: bool
    enforce_current_flag_contract: bool
    enforce_workspace_semantic_probe: bool


@dataclass(frozen=True)
class DocCommandSurfaceRule:
    script_rel: str = ""
    script_prefix: str = ""
    mode: str = ""
    rationale: str = ""


@dataclass(frozen=True)
class DocCommandSurfaceRow:
    doc: str
    default_mode: str = MODE_LIVE_CONTRACT
    rationale: str = ""
    script_rules: tuple[DocCommandSurfaceRule, ...] = field(default_factory=tuple)


def _norm_path(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    out: list[str] = []
    for item in value:
        token = _norm_path(item)
        if token:
            out.append(token)
    return tuple(out)


def load_doc_command_surface(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / DOC_COMMAND_SURFACE_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, DOC_COMMAND_SURFACE_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_surface_registry_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def surface_mode_profiles_from_doc(surface_doc: Mapping[str, Any]) -> tuple[DocCommandSurfaceModeProfile, ...]:
    rows = surface_doc.get("surface_modes")
    if not isinstance(rows, list):
        return ()
    out: list[DocCommandSurfaceModeProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        mode = _norm_path(row.get("mode"))
        if not mode:
            continue
        out.append(
            DocCommandSurfaceModeProfile(
                mode=mode,
                enforce_script_existence=bool(row.get("enforce_script_existence", False)),
                enforce_current_flag_contract=bool(row.get("enforce_current_flag_contract", False)),
                enforce_workspace_semantic_probe=bool(row.get("enforce_workspace_semantic_probe", False)),
            )
        )
    return tuple(out)


def doc_command_surface_rows_from_doc(surface_doc: Mapping[str, Any]) -> tuple[DocCommandSurfaceRow, ...]:
    rows = surface_doc.get("doc_command_surface_rows")
    if not isinstance(rows, list):
        return ()
    out: list[DocCommandSurfaceRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        doc = _norm_path(row.get("doc"))
        if not doc:
            continue
        default_mode = _norm_path(row.get("default_mode")) or MODE_LIVE_CONTRACT
        rationale = str(row.get("rationale") or "").strip()
        rules_raw = row.get("script_rules")
        script_rules: list[DocCommandSurfaceRule] = []
        if isinstance(rules_raw, list):
            for rule in rules_raw:
                if not isinstance(rule, dict):
                    continue
                script_rel = _norm_path(rule.get("script_rel"))
                script_prefix = _norm_path(rule.get("script_prefix"))
                mode = _norm_path(rule.get("mode"))
                if not mode and not script_rel and not script_prefix:
                    continue
                script_rules.append(
                    DocCommandSurfaceRule(
                        script_rel=script_rel,
                        script_prefix=script_prefix,
                        mode=mode,
                        rationale=str(rule.get("rationale") or "").strip(),
                    )
                )
        out.append(
            DocCommandSurfaceRow(
                doc=doc,
                default_mode=default_mode,
                rationale=rationale,
                script_rules=tuple(script_rules),
            )
        )
    return tuple(out)


def repo_self_prefixes_from_doc(surface_doc: Mapping[str, Any]) -> tuple[str, ...]:
    contract = surface_doc.get("self_prefix_contract")
    if not isinstance(contract, dict):
        return DEFAULT_SELF_PREFIXES
    prefixes = _as_str_tuple(contract.get("repo_self_prefixes"))
    return prefixes or DEFAULT_SELF_PREFIXES


def canonicalize_repo_self_prefix_path(
    value: str,
    *,
    repo_name: str,
    self_prefixes: tuple[str, ...] = DEFAULT_SELF_PREFIXES,
) -> str:
    normalized = _norm_path(value)
    if not normalized:
        return normalized
    prefix_candidates: list[str] = []
    if repo_name:
        prefix_candidates.append(repo_name)
    prefix_candidates.extend(self_prefixes)
    seen: set[str] = set()
    for prefix in prefix_candidates:
        token = _norm_path(prefix).strip("/")
        if not token or token in seen:
            continue
        seen.add(token)
        if normalized == token:
            return ""
        prefix_token = f"{token}/"
        if normalized.startswith(prefix_token):
            return normalized[len(prefix_token) :]
    return normalized


def resolve_doc_command_surface_mode(
    *,
    surface_rows: tuple[DocCommandSurfaceRow, ...],
    doc_rel: str,
    script_rel: str,
    repo_name: str,
    self_prefixes: tuple[str, ...] = DEFAULT_SELF_PREFIXES,
) -> tuple[str, str]:
    normalized_doc = _norm_path(doc_rel)
    normalized_script = canonicalize_repo_self_prefix_path(
        script_rel, repo_name=repo_name, self_prefixes=self_prefixes
    )
    row = next((item for item in surface_rows if item.doc == normalized_doc), None)
    if row is None:
        return MODE_LIVE_CONTRACT, "implicit_live_contract_default"
    for rule in row.script_rules:
        if rule.script_rel:
            candidate = canonicalize_repo_self_prefix_path(
                rule.script_rel, repo_name=repo_name, self_prefixes=self_prefixes
            )
            if candidate == normalized_script:
                return rule.mode, rule.rationale or "script_rel_override"
        if rule.script_prefix:
            prefix = canonicalize_repo_self_prefix_path(
                rule.script_prefix, repo_name=repo_name, self_prefixes=self_prefixes
            ).rstrip("/")
            if prefix and normalized_script.startswith(f"{prefix}/"):
                return rule.mode, rule.rationale or "script_prefix_override"
    return row.default_mode or MODE_LIVE_CONTRACT, row.rationale or "doc_default_mode"


def resolve_doc_script_target(
    repo_root: Path,
    script_rel: str,
    *,
    workspace_root: Path | None = None,
    self_prefixes: tuple[str, ...] = DEFAULT_SELF_PREFIXES,
) -> tuple[Path, Path]:
    workspace = workspace_root or (repo_root.parent if repo_root.name == "identity-protocol-local" else repo_root)
    normalized = _norm_path(script_rel)
    canonical = canonicalize_repo_self_prefix_path(
        normalized, repo_name=repo_root.name, self_prefixes=self_prefixes
    )
    candidates: list[tuple[Path, Path]] = [((repo_root / canonical).resolve(), repo_root)]
    if normalized != canonical:
        candidates.append(((repo_root / normalized).resolve(), repo_root))
    if workspace != repo_root:
        candidates.append(((workspace / normalized).resolve(), workspace))
        if canonical and canonical != normalized:
            candidates.append(((workspace / canonical).resolve(), workspace))
    deduped: list[tuple[Path, Path]] = []
    seen: set[tuple[str, str]] = set()
    for path, cwd in candidates:
        key = (str(path), str(cwd))
        if key in seen:
            continue
        seen.add(key)
        deduped.append((path, cwd))
    for path, cwd in deduped:
        if path.exists():
            return path, cwd
    return deduped[0]
