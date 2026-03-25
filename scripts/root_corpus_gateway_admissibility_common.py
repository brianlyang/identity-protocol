#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_GATEWAY_ADMISSIBILITY_CURRENT = (
    "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml"
)


@dataclass(frozen=True)
class GatewayAnchorCheck:
    rel_path: str
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GatewayProfile:
    gateway_class: str
    gateway_scope: str
    admissibility_mode: str
    gateway_effect_scope: str
    current_turn_legality_terminal: bool
    admissible_nonorigin_surface_classes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GatewayOrderRow:
    order: int
    gateway_class: str


def _norm_str(value: Any) -> str:
    return str(value or "").strip().replace("\\", "/")


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(token for token in (str(item or "").strip() for item in value) if token)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def load_root_corpus_gateway_admissibility(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_GATEWAY_ADMISSIBILITY_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(
        repo_root, ROOT_CORPUS_GATEWAY_ADMISSIBILITY_CURRENT
    )
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_gateway_admissibility_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def gateway_anchor_checks_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[GatewayAnchorCheck, ...]:
    rows = admissibility_doc.get("gateway_anchor_checks")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayAnchorCheck] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(
            GatewayAnchorCheck(
                rel_path=rel_path,
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def gateway_profiles_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[GatewayProfile, ...]:
    rows = admissibility_doc.get("gateway_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gateway_class = _norm_str(row.get("gateway_class"))
        gateway_scope = _norm_str(row.get("gateway_scope"))
        admissibility_mode = _norm_str(row.get("admissibility_mode"))
        gateway_effect_scope = _norm_str(row.get("gateway_effect_scope"))
        if not gateway_class or not gateway_scope or not admissibility_mode or not gateway_effect_scope:
            continue
        out.append(
            GatewayProfile(
                gateway_class=gateway_class,
                gateway_scope=gateway_scope,
                admissibility_mode=admissibility_mode,
                gateway_effect_scope=gateway_effect_scope,
                current_turn_legality_terminal=bool(row.get("current_turn_legality_terminal", False)),
                admissible_nonorigin_surface_classes=_as_str_tuple(
                    row.get("admissible_nonorigin_surface_classes")
                ),
            )
        )
    return tuple(out)


def gateway_order_rows_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[GatewayOrderRow, ...]:
    rows = admissibility_doc.get("gateway_order")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayOrderRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gateway_class = _norm_str(row.get("gateway_class"))
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not gateway_class:
            continue
        out.append(GatewayOrderRow(order=order, gateway_class=gateway_class))
    return tuple(out)
