#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from registry_alias_control_plane_common import resolve_current_yaml_alias
from root_contract_anchor_checks_common import RootDocAnchorCheck, root_doc_anchor_checks_from_doc

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ROOT_CORPUS_GATEWAY_ADMISSIBILITY_CURRENT = (
    "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml"
)
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
GATEWAY_ADMISSIBILITY_COMPLETENESS_SECTION_MARKER = "## Root gateway-admissibility completeness discipline"
ORDERED_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+(.*\S)\s*$")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


GatewayAnchorCheck = RootDocAnchorCheck


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


@dataclass(frozen=True)
class GatewayEffectTarget:
    gateway_class: str
    effect_target_class: str
    effect_target_transition_mode: str
    effect_target_authority_mode: str
    effect_target_question_class: str
    effect_target_answer_mode: str


@dataclass(frozen=True)
class GatewayAdmissibilityCompletenessRow:
    order: int
    completeness_id: str
    contract_phrase: str


@dataclass(frozen=True)
class GatewayAdmissibilityCompletenessSurfaceRow:
    order: int
    contract_phrase: str


@dataclass(frozen=True)
class GatewayAdmissibilityCompletenessSurface:
    rel_path: str
    rows: tuple[GatewayAdmissibilityCompletenessSurfaceRow, ...]
    extraction_violations: tuple[str, ...]


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
    return root_doc_anchor_checks_from_doc(
        admissibility_doc,
        field_name="gateway_anchor_checks",
        require_markers=False,
    )


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


def gateway_effect_targets_from_doc(admissibility_doc: Mapping[str, Any]) -> tuple[GatewayEffectTarget, ...]:
    rows = admissibility_doc.get("gateway_effect_targets")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayEffectTarget] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gateway_class = _norm_str(row.get("gateway_class"))
        effect_target_class = _norm_str(row.get("effect_target_class"))
        effect_target_transition_mode = _norm_str(row.get("effect_target_transition_mode"))
        effect_target_authority_mode = _norm_str(row.get("effect_target_authority_mode"))
        effect_target_question_class = _norm_str(row.get("effect_target_question_class"))
        effect_target_answer_mode = _norm_str(row.get("effect_target_answer_mode"))
        if (
            not gateway_class
            or not effect_target_class
            or not effect_target_transition_mode
            or not effect_target_authority_mode
            or not effect_target_question_class
            or not effect_target_answer_mode
        ):
            continue
        out.append(
            GatewayEffectTarget(
                gateway_class=gateway_class,
                effect_target_class=effect_target_class,
                effect_target_transition_mode=effect_target_transition_mode,
                effect_target_authority_mode=effect_target_authority_mode,
                effect_target_question_class=effect_target_question_class,
                effect_target_answer_mode=effect_target_answer_mode,
            )
        )
    return tuple(out)


def gateway_admissibility_completeness_rows_from_doc(
    admissibility_doc: Mapping[str, Any],
) -> tuple[GatewayAdmissibilityCompletenessRow, ...]:
    rows = admissibility_doc.get("gateway_admissibility_completeness_rows")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayAdmissibilityCompletenessRow] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        completeness_id = _norm_str(row.get("completeness_id"))
        contract_phrase = str(row.get("contract_phrase") or "").strip()
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        if order <= 0 or not completeness_id or not contract_phrase:
            continue
        out.append(
            GatewayAdmissibilityCompletenessRow(
                order=order,
                completeness_id=completeness_id,
                contract_phrase=contract_phrase,
            )
        )
    return tuple(out)


def readme_gateway_admissibility_completeness_surface(
    repo_root: Path,
) -> GatewayAdmissibilityCompletenessSurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return GatewayAdmissibilityCompletenessSurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[GatewayAdmissibilityCompletenessSurfaceRow] = []

    for line in lines:
        stripped = line.strip()
        if stripped == GATEWAY_ADMISSIBILITY_COMPLETENESS_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if HEADING_RE.match(stripped) or HORIZONTAL_RULE_RE.match(stripped):
            break
        match = ORDERED_ITEM_RE.match(stripped)
        if not match:
            continue
        rows.append(
            GatewayAdmissibilityCompletenessSurfaceRow(
                order=int(match.group(1)),
                contract_phrase=match.group(2).strip(),
            )
        )

    violations: list[str] = []
    if not section_found:
        violations.append("section_missing")
    elif not rows:
        violations.append("ordered_items_missing")

    return GatewayAdmissibilityCompletenessSurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )
