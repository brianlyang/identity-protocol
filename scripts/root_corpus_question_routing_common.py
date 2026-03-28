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
ROOT_CORPUS_QUESTION_ROUTING_CURRENT = "identity/protocol/mappings/root-corpus-question-routing.current.yaml"
ROOT_PROTOCOL_README_REL_PATH = "identity/protocol/README.md"
ENTRY_SUMMARY_SECTION_MARKER = "## Machine-world entry summary"
ORDERED_BOLD_ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\*\*(.*?)\*\*")
HEADING_RE = re.compile(r"^##\s+")
HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$")


QuestionRoutingAnchorCheck = RootDocAnchorCheck


@dataclass(frozen=True)
class QuestionClassProfile:
    question_class: str
    answer_mode: str
    current_turn_authority_allowed: bool
    root_entry_required: bool


@dataclass(frozen=True)
class EntryQuestionProjection:
    rel_path: str
    question_classes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GatewayQuestionProjection:
    gateway_class: str
    effect_target_class: str
    question_class: str
    answer_mode: str
    current_turn_authority_allowed: bool
    root_entry_required: bool


@dataclass(frozen=True)
class EntrySummaryStage:
    order: int
    stage_label: str
    bound_question_classes: tuple[str, ...] = field(default_factory=tuple)
    terminal_machine_surfaces: tuple[str, ...] = field(default_factory=tuple)
    required_markers: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EntrySummarySurfaceRow:
    order: int
    stage_label: str
    body_lines: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class EntrySummarySurface:
    rel_path: str
    rows: tuple[EntrySummarySurfaceRow, ...]
    extraction_violations: tuple[str, ...]


@dataclass(frozen=True)
class AdjudicationRedirect:
    question_class: str
    terminal_machine_surfaces: tuple[str, ...] = field(default_factory=tuple)
    forbidden_root_corpus_classes: tuple[str, ...] = field(default_factory=tuple)


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


def load_root_corpus_question_routing(repo_root: Path) -> tuple[dict[str, Any], Path, Path, str]:
    entry_path = (repo_root / ROOT_CORPUS_QUESTION_ROUTING_CURRENT).resolve()
    active_path, _active_file, alias_error = resolve_current_yaml_alias(repo_root, ROOT_CORPUS_QUESTION_ROUTING_CURRENT)
    if alias_error:
        return {}, entry_path, active_path, alias_error
    if not active_path.exists():
        return {}, entry_path, active_path, "active_routing_missing"
    return _load_yaml(active_path), entry_path, active_path, ""


def question_routing_anchor_checks_from_doc(routing_doc: Mapping[str, Any]) -> tuple[QuestionRoutingAnchorCheck, ...]:
    return root_doc_anchor_checks_from_doc(
        routing_doc,
        field_name="question_routing_anchor_checks",
        require_markers=False,
    )


def question_class_profiles_from_doc(routing_doc: Mapping[str, Any]) -> tuple[QuestionClassProfile, ...]:
    rows = routing_doc.get("question_class_profiles")
    if not isinstance(rows, list):
        return ()
    out: list[QuestionClassProfile] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_class = _norm_str(row.get("question_class"))
        answer_mode = _norm_str(row.get("answer_mode"))
        if not question_class or not answer_mode:
            continue
        out.append(
            QuestionClassProfile(
                question_class=question_class,
                answer_mode=answer_mode,
                current_turn_authority_allowed=bool(row.get("current_turn_authority_allowed", False)),
                root_entry_required=bool(row.get("root_entry_required", False)),
            )
        )
    return tuple(out)


def entry_question_projections_from_doc(routing_doc: Mapping[str, Any]) -> tuple[EntryQuestionProjection, ...]:
    rows = routing_doc.get("entry_question_projection")
    if not isinstance(rows, list):
        return ()
    out: list[EntryQuestionProjection] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rel_path = _norm_str(row.get("rel_path"))
        if not rel_path:
            continue
        out.append(
            EntryQuestionProjection(
                rel_path=rel_path,
                question_classes=_as_str_tuple(row.get("question_classes")),
            )
        )
    return tuple(out)


def gateway_question_projections_from_doc(routing_doc: Mapping[str, Any]) -> tuple[GatewayQuestionProjection, ...]:
    rows = routing_doc.get("gateway_question_projection")
    if not isinstance(rows, list):
        return ()
    out: list[GatewayQuestionProjection] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        gateway_class = _norm_str(row.get("gateway_class"))
        effect_target_class = _norm_str(row.get("effect_target_class"))
        question_class = _norm_str(row.get("question_class"))
        answer_mode = _norm_str(row.get("answer_mode"))
        if not gateway_class or not effect_target_class or not question_class or not answer_mode:
            continue
        out.append(
            GatewayQuestionProjection(
                gateway_class=gateway_class,
                effect_target_class=effect_target_class,
                question_class=question_class,
                answer_mode=answer_mode,
                current_turn_authority_allowed=bool(row.get("current_turn_authority_allowed", False)),
                root_entry_required=bool(row.get("root_entry_required", False)),
            )
        )
    return tuple(out)


def entry_summary_stages_from_doc(routing_doc: Mapping[str, Any]) -> tuple[EntrySummaryStage, ...]:
    rows = routing_doc.get("entry_summary_stages")
    if not isinstance(rows, list):
        return ()
    out: list[EntrySummaryStage] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            order = int(row.get("order"))
        except Exception:
            continue
        stage_label = _norm_str(row.get("stage_label"))
        if order <= 0 or not stage_label:
            continue
        out.append(
            EntrySummaryStage(
                order=order,
                stage_label=stage_label,
                bound_question_classes=_as_str_tuple(row.get("bound_question_classes")),
                terminal_machine_surfaces=_as_str_tuple(row.get("terminal_machine_surfaces")),
                required_markers=_as_str_tuple(row.get("required_markers")),
            )
        )
    return tuple(out)


def readme_entry_summary_surface(repo_root: Path) -> EntrySummarySurface:
    path = (repo_root / ROOT_PROTOCOL_README_REL_PATH).resolve()
    if not path.exists() or not path.is_file():
        return EntrySummarySurface(
            rel_path=ROOT_PROTOCOL_README_REL_PATH,
            rows=(),
            extraction_violations=("target_missing",),
        )

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section_found = False
    rows: list[EntrySummarySurfaceRow] = []
    current_order = 0
    current_label = ""
    current_body_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_order, current_label, current_body_lines
        if current_order <= 0 or not current_label:
            return
        rows.append(
            EntrySummarySurfaceRow(
                order=current_order,
                stage_label=current_label,
                body_lines=tuple(line for line in current_body_lines if line),
            )
        )
        current_order = 0
        current_label = ""
        current_body_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped == ENTRY_SUMMARY_SECTION_MARKER:
            section_found = True
            continue
        if not section_found:
            continue
        if HEADING_RE.match(stripped) or HORIZONTAL_RULE_RE.match(stripped):
            break
        match = ORDERED_BOLD_ITEM_RE.match(stripped)
        if match:
            flush_current()
            current_order = int(match.group(1))
            current_label = match.group(2).strip()
            continue
        if current_order <= 0:
            continue
        if stripped.startswith("- "):
            current_body_lines.append(stripped[2:].strip())
        elif stripped and line.startswith((" ", "\t")):
            current_body_lines.append(stripped)
        elif stripped:
            flush_current()
            break
    flush_current()

    violations: list[str] = []
    if not section_found:
        violations.append("section_marker_missing")
    elif not rows:
        violations.append("stage_rows_missing")
    elif any(not row.body_lines for row in rows):
        violations.append("stage_body_missing")

    return EntrySummarySurface(
        rel_path=ROOT_PROTOCOL_README_REL_PATH,
        rows=tuple(rows),
        extraction_violations=tuple(violations),
    )


def adjudication_redirect_from_doc(routing_doc: Mapping[str, Any]) -> AdjudicationRedirect:
    row = routing_doc.get("adjudication_redirect")
    if not isinstance(row, dict):
        return AdjudicationRedirect(question_class="")
    return AdjudicationRedirect(
        question_class=_norm_str(row.get("question_class")),
        terminal_machine_surfaces=_as_str_tuple(row.get("terminal_machine_surfaces")),
        forbidden_root_corpus_classes=_as_str_tuple(row.get("forbidden_root_corpus_classes")),
    )
