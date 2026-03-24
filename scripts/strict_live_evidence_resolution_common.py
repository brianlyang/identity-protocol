#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import ACTIVE_EXECUTION_POINTER_REL

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

DEFAULT_REPORT_FRESHNESS_MAX_AGE_SECONDS = 86400
DEFAULT_RUN_ID_FIELD_CANDIDATES: tuple[str, ...] = (
    "run_id",
    "feedback_run_id",
    "evidence_run_id",
)

STRICT_LIVE_CURRENT_RUN_REQUIRED_FIELD = "strict_live_current_run_required"
STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD = "report_freshness_max_age_seconds"
STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD = "run_id_field_candidates"
STRICT_LIVE_ACTIVE_EXECUTION_POINTER_REL_FIELD = "active_execution_pointer_rel"
STRICT_LIVE_PREFER_CURRENT_RUN_LIVE_REPORT_FIELD = "prefer_current_run_live_report"
STRICT_LIVE_REPORT_SELECTION_ORDER_FIELD = "report_selection_order"
STRICT_LIVE_PROJECTION_FIELDS_FIELD = "strict_live_projection_fields"

DEFAULT_REPORT_SELECTION_ORDER: tuple[str, ...] = (
    "explicit_report_override",
    "current_run_live_report",
    "fallback_report",
)
CANONICAL_STRICT_LIVE_PROJECTION_FIELDS: tuple[str, ...] = (
    "selected_report_path",
    "current_run_pointer",
    "current_run_report_path",
    "current_run_id",
    "report_selection_mode",
    "live_candidate_paths",
    "evidence_origin",
    "report_freshness_status",
    "run_id_binding_status",
    "strict_live_proof_status",
    "semantic_contract_status",
    "strict_live_operational_status",
    "operational_closure_class",
    "live_binding_strength",
    "next_hop_consumption_status",
    "selected_report_run_ids",
    "selected_report_age_seconds",
    "stale_reasons",
)


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def strict_live_contract_defaults(
    *,
    freshness_max_age_seconds: int = DEFAULT_REPORT_FRESHNESS_MAX_AGE_SECONDS,
    extra_run_id_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    candidates: list[str] = []
    for field in (*DEFAULT_RUN_ID_FIELD_CANDIDATES, *extra_run_id_fields):
        token = clean_string(field)
        if token and token not in candidates:
            candidates.append(token)
    return {
        STRICT_LIVE_CURRENT_RUN_REQUIRED_FIELD: True,
        STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD: int(
            freshness_max_age_seconds or DEFAULT_REPORT_FRESHNESS_MAX_AGE_SECONDS
        ),
        STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD: candidates,
        STRICT_LIVE_ACTIVE_EXECUTION_POINTER_REL_FIELD: ACTIVE_EXECUTION_POINTER_REL.as_posix(),
        STRICT_LIVE_PREFER_CURRENT_RUN_LIVE_REPORT_FIELD: True,
        STRICT_LIVE_REPORT_SELECTION_ORDER_FIELD: list(DEFAULT_REPORT_SELECTION_ORDER),
        STRICT_LIVE_PROJECTION_FIELDS_FIELD: list(CANONICAL_STRICT_LIVE_PROJECTION_FIELDS),
    }


def merge_strict_live_contract_defaults(
    contract_doc: dict[str, Any],
    *,
    freshness_max_age_seconds: int = DEFAULT_REPORT_FRESHNESS_MAX_AGE_SECONDS,
    extra_run_id_fields: tuple[str, ...] = (),
) -> dict[str, Any]:
    merged = _clone_json(contract_doc if isinstance(contract_doc, dict) else {})
    defaults = strict_live_contract_defaults(
        freshness_max_age_seconds=freshness_max_age_seconds,
        extra_run_id_fields=extra_run_id_fields,
    )
    if merged.get(STRICT_LIVE_CURRENT_RUN_REQUIRED_FIELD) is not True:
        merged[STRICT_LIVE_CURRENT_RUN_REQUIRED_FIELD] = True
    age_value = merged.get(STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD)
    if not isinstance(age_value, int) or age_value <= 0:
        merged[STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD] = defaults[
            STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD
        ]
    run_id_fields = [
        clean_string(item)
        for item in (merged.get(STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD) or [])
        if clean_string(item)
    ]
    for token in defaults[STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD]:
        if token not in run_id_fields:
            run_id_fields.append(token)
    merged[STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD] = run_id_fields
    pointer_rel = clean_string(merged.get(STRICT_LIVE_ACTIVE_EXECUTION_POINTER_REL_FIELD))
    if not pointer_rel:
        merged[STRICT_LIVE_ACTIVE_EXECUTION_POINTER_REL_FIELD] = defaults[
            STRICT_LIVE_ACTIVE_EXECUTION_POINTER_REL_FIELD
        ]
    if merged.get(STRICT_LIVE_PREFER_CURRENT_RUN_LIVE_REPORT_FIELD) is not True:
        merged[STRICT_LIVE_PREFER_CURRENT_RUN_LIVE_REPORT_FIELD] = True
    selection_order = [
        clean_string(item)
        for item in (merged.get(STRICT_LIVE_REPORT_SELECTION_ORDER_FIELD) or [])
        if clean_string(item)
    ]
    for token in defaults[STRICT_LIVE_REPORT_SELECTION_ORDER_FIELD]:
        if token not in selection_order:
            selection_order.append(token)
    merged[STRICT_LIVE_REPORT_SELECTION_ORDER_FIELD] = selection_order
    projection_fields = [
        clean_string(item)
        for item in (merged.get(STRICT_LIVE_PROJECTION_FIELDS_FIELD) or [])
        if clean_string(item)
    ]
    for token in defaults[STRICT_LIVE_PROJECTION_FIELDS_FIELD]:
        if token not in projection_fields:
            projection_fields.append(token)
    merged[STRICT_LIVE_PROJECTION_FIELDS_FIELD] = projection_fields
    return merged


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def _resolve_report_pointer_path(pack_root: Path, pointer_doc: dict[str, Any]) -> Path | None:
    for key in ("report_path", "execution_report", "selected_report_path"):
        raw = clean_string(pointer_doc.get(key))
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = (pack_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate.exists():
            return candidate
    return None


def resolve_active_execution_context(pack_root: Path) -> dict[str, Any]:
    pointer_path = (pack_root / ACTIVE_EXECUTION_POINTER_REL).resolve()
    pointer_doc = _load_json(pointer_path) if pointer_path.exists() else None
    report_path = _resolve_report_pointer_path(pack_root, pointer_doc or {}) if isinstance(pointer_doc, dict) else None
    report_doc = _load_json(report_path) if report_path is not None and report_path.exists() else None
    current_run_id = ""
    for doc in (pointer_doc, report_doc):
        if isinstance(doc, dict):
            current_run_id = clean_string(doc.get("run_id"))
            if current_run_id:
                break
    return {
        "pointer_path": str(pointer_path) if pointer_path.exists() else "",
        "pointer_doc": pointer_doc or {},
        "report_path": str(report_path) if report_path is not None else "",
        "report_doc": report_doc or {},
        "run_id": current_run_id,
    }


def _collect_named_values(node: Any, field_names: set[str], sink: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in field_names:
                token = clean_string(value)
                if token and token not in sink:
                    sink.append(token)
            _collect_named_values(value, field_names, sink)
    elif isinstance(node, list):
        for item in node:
            _collect_named_values(item, field_names, sink)


def extract_run_id_candidates(report_doc: dict[str, Any], candidate_fields: list[str]) -> list[str]:
    sink: list[str] = []
    _collect_named_values(report_doc, set(candidate_fields), sink)
    return sink


def _doc_references_path(node: Any, target_path: Path) -> bool:
    target = target_path.expanduser().resolve().as_posix()
    if isinstance(node, dict):
        return any(_doc_references_path(value, target_path) for value in node.values())
    if isinstance(node, list):
        return any(_doc_references_path(item, target_path) for item in node)
    token = clean_string(node)
    if not token:
        return False
    candidate = Path(token).expanduser()
    if candidate.is_absolute():
        try:
            return candidate.resolve().as_posix() == target
        except Exception:
            return False
    return token == target


def _iter_candidate_paths(pack_root: Path, node: Any, sink: list[Path]) -> None:
    if isinstance(node, dict):
        for value in node.values():
            _iter_candidate_paths(pack_root, value, sink)
        return
    if isinstance(node, list):
        for item in node:
            _iter_candidate_paths(pack_root, item, sink)
        return
    token = clean_string(node)
    if not token:
        return
    if len(token) > 512:
        return
    if "/" not in token and "\\" not in token and not token.endswith((".json", ".jsonl", ".md")):
        return
    candidate = Path(token).expanduser()
    if not candidate.is_absolute():
        candidate = (pack_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        exists = candidate.exists()
    except OSError:
        return
    if exists and candidate not in sink:
        sink.append(candidate)


def _resolve_glob_candidates(pack_root: Path, pattern: str) -> list[Path]:
    raw = clean_string(pattern)
    if not raw:
        return []
    normalized = raw.replace("<identity-id>", pack_root.name)
    candidates: list[str] = [normalized]
    if normalized.startswith("identity/runtime/"):
        candidates.insert(0, f"runtime/{normalized[len('identity/runtime/'):]}")
    rows: list[Path] = []
    for candidate_pattern in candidates:
        p = Path(candidate_pattern).expanduser()
        if p.is_absolute():
            parent = p.parent if str(p.parent) != "." else p
            matched = sorted(parent.glob(p.name))
        else:
            matched = sorted(pack_root.glob(candidate_pattern))
        if matched:
            for item in matched:
                resolved = item.resolve()
                if resolved.exists() and resolved not in rows:
                    rows.append(resolved)
            if rows:
                return rows
    return rows


def _derive_live_report_path_pattern(contract_doc: dict[str, Any]) -> str:
    explicit = clean_string(contract_doc.get("live_report_path_pattern"))
    if explicit:
        return explicit
    sample_pattern = clean_string(contract_doc.get("sample_report_path_pattern"))
    if not sample_pattern:
        return ""
    derived = sample_pattern.replace("/examples/", "/reports/")
    derived = derived.replace("-sample.", "-*.").replace("_sample.", "_*.").replace("sample.", "*.")
    return derived


def _path_matches_live_pattern(path: Path, pack_root: Path, pattern: str) -> bool:
    candidates = _resolve_glob_candidates(pack_root, pattern)
    target = path.resolve()
    return any(candidate.resolve() == target for candidate in candidates)


def resolve_preferred_strict_live_report(
    *,
    pack_root: Path,
    contract_doc: dict[str, Any],
    fallback_report_path: Path | None,
    explicit_report_path: Path | None = None,
) -> dict[str, Any]:
    fallback = (
        fallback_report_path.resolve()
        if isinstance(fallback_report_path, Path) and fallback_report_path.exists()
        else None
    )
    if isinstance(explicit_report_path, Path) and explicit_report_path.exists():
        return {
            "selected_report_path": explicit_report_path.resolve(),
            "report_selection_mode": "explicit_report_override",
            "live_candidate_paths": [],
            "live_candidate_selected_path": "",
        }

    merged_contract = merge_strict_live_contract_defaults(contract_doc)
    if merged_contract.get(STRICT_LIVE_PREFER_CURRENT_RUN_LIVE_REPORT_FIELD) is not True:
        return {
            "selected_report_path": fallback,
            "report_selection_mode": "fallback_report" if fallback is not None else "missing",
            "live_candidate_paths": [],
            "live_candidate_selected_path": "",
        }

    active_context = resolve_active_execution_context(pack_root)
    live_pattern = _derive_live_report_path_pattern(merged_contract)
    candidate_paths: list[Path] = []
    live_pattern_matches = _resolve_glob_candidates(pack_root, live_pattern)
    for candidate in live_pattern_matches:
        if candidate not in candidate_paths:
            candidate_paths.append(candidate)
    active_context_paths: list[Path] = []
    _iter_candidate_paths(pack_root, active_context.get("report_doc") or {}, active_context_paths)
    for candidate in active_context_paths:
        if live_pattern and not _path_matches_live_pattern(candidate, pack_root, live_pattern):
            continue
        if candidate not in candidate_paths:
            candidate_paths.append(candidate)

    best_path: Path | None = None
    best_score: tuple[int, int, int, int, float] | None = None
    for candidate in candidate_paths:
        report_doc = _load_json(candidate)
        if report_doc is None:
            continue
        projection = derive_strict_live_evidence_projection(
            pack_root=pack_root,
            contract_doc=merged_contract,
            selected_report_path=candidate,
            report_doc=report_doc,
        )
        score = (
            1 if clean_string(projection.get("strict_live_proof_status")).upper() == STATUS_PASS_REQUIRED else 0,
            1 if clean_string(projection.get("run_id_binding_status")).upper() == STATUS_PASS_REQUIRED else 0,
            1 if clean_string(projection.get("report_freshness_status")).upper() == STATUS_PASS_REQUIRED else 0,
            1 if clean_string(projection.get("evidence_origin")) == "live" else 0,
            candidate.stat().st_mtime,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_path = candidate

    if best_path is not None and best_score is not None and best_score[0] == 1:
        return {
            "selected_report_path": best_path.resolve(),
            "report_selection_mode": "current_run_live_report",
            "live_candidate_paths": [str(path) for path in candidate_paths],
            "live_candidate_selected_path": str(best_path.resolve()),
        }

    return {
        "selected_report_path": fallback,
        "report_selection_mode": "fallback_report" if fallback is not None else "missing",
        "live_candidate_paths": [str(path) for path in candidate_paths],
        "live_candidate_selected_path": "",
    }


def derive_strict_live_evidence_projection(
    *,
    pack_root: Path,
    contract_doc: dict[str, Any],
    selected_report_path: Path | None,
    report_doc: dict[str, Any] | None,
) -> dict[str, Any]:
    merged_contract = merge_strict_live_contract_defaults(contract_doc)
    active_context = resolve_active_execution_context(pack_root)
    stale_reasons: list[str] = []
    if not active_context.get("pointer_path"):
        stale_reasons.append("active_execution_pointer_missing")

    selected_path = selected_report_path.resolve() if isinstance(selected_report_path, Path) and selected_report_path.exists() else None
    if selected_path is None:
        stale_reasons.append("selected_report_missing")
        return {
            "selected_report_path": "",
            "current_run_pointer": clean_string(active_context.get("pointer_path")),
            "current_run_report_path": clean_string(active_context.get("report_path")),
            "current_run_id": clean_string(active_context.get("run_id")),
            "evidence_origin": "missing",
            "report_freshness_status": STATUS_FAIL_REQUIRED,
            "run_id_binding_status": STATUS_FAIL_REQUIRED,
            "strict_live_proof_status": STATUS_FAIL_REQUIRED,
            "selected_report_run_ids": [],
            "selected_report_age_seconds": None,
            "stale_reasons": stale_reasons,
        }

    text = selected_path.as_posix()
    evidence_origin = "governed_artifact"
    if "/runtime/examples/" in text or selected_path.name.endswith("-sample.json"):
        evidence_origin = "sample"
    else:
        report_doc_active = active_context.get("report_doc") if isinstance(active_context.get("report_doc"), dict) else {}
        report_path_token = clean_string(active_context.get("report_path"))
        report_path = Path(report_path_token).expanduser().resolve() if report_path_token else None
        if report_path is not None and selected_path == report_path:
            evidence_origin = "live"
        elif report_doc_active and _doc_references_path(report_doc_active, selected_path):
            evidence_origin = "live"
        elif "/runtime/reports/" in text or "/runtime/logs/" in text:
            evidence_origin = "history"

    max_age_seconds = int(
        merged_contract.get(STRICT_LIVE_REPORT_FRESHNESS_MAX_AGE_SECONDS_FIELD)
        or DEFAULT_REPORT_FRESHNESS_MAX_AGE_SECONDS
    )
    age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - selected_path.stat().st_mtime)
    report_freshness_status = (
        STATUS_PASS_REQUIRED if max_age_seconds > 0 and age_seconds <= max_age_seconds else STATUS_FAIL_REQUIRED
    )
    if report_freshness_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("selected_report_not_fresh_enough")

    run_id_fields = [
        clean_string(item)
        for item in (merged_contract.get(STRICT_LIVE_RUN_ID_FIELD_CANDIDATES_FIELD) or [])
        if clean_string(item)
    ] or list(DEFAULT_RUN_ID_FIELD_CANDIDATES)
    report_run_ids = extract_run_id_candidates(report_doc or {}, run_id_fields) if isinstance(report_doc, dict) else []
    current_run_id = clean_string(active_context.get("run_id"))
    run_id_binding_status = (
        STATUS_PASS_REQUIRED if current_run_id and current_run_id in report_run_ids else STATUS_FAIL_REQUIRED
    )
    if not current_run_id:
        stale_reasons.append("current_run_id_missing")
    elif not report_run_ids:
        stale_reasons.append("selected_report_run_id_missing")
    elif run_id_binding_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("selected_report_run_id_mismatch")

    if evidence_origin == "sample":
        stale_reasons.append("sample_report_selected_on_strict_lane")
    elif evidence_origin == "history":
        stale_reasons.append("history_report_selected_on_strict_lane")
    elif evidence_origin != "live":
        stale_reasons.append("selected_report_not_linked_to_active_run")

    strict_live_proof_status = (
        STATUS_PASS_REQUIRED
        if evidence_origin == "live"
        and report_freshness_status == STATUS_PASS_REQUIRED
        and run_id_binding_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    if strict_live_proof_status != STATUS_PASS_REQUIRED:
        stale_reasons.append("strict_live_proof_unproven")

    return {
        "selected_report_path": str(selected_path),
        "current_run_pointer": clean_string(active_context.get("pointer_path")),
        "current_run_report_path": clean_string(active_context.get("report_path")),
        "current_run_id": current_run_id,
        "evidence_origin": evidence_origin,
        "report_freshness_status": report_freshness_status,
        "run_id_binding_status": run_id_binding_status,
        "strict_live_proof_status": strict_live_proof_status,
        "selected_report_run_ids": report_run_ids,
        "selected_report_age_seconds": round(age_seconds, 3),
        "stale_reasons": sorted(set(stale_reasons)),
    }


def derive_strict_live_operational_projection(
    *,
    semantic_status: str,
    evidence_projection: dict[str, Any],
) -> dict[str, Any]:
    semantic_status_token = clean_string(semantic_status).upper() or STATUS_FAIL_REQUIRED
    evidence_origin = clean_string(evidence_projection.get("evidence_origin"))
    strict_live_proof_status = clean_string(evidence_projection.get("strict_live_proof_status")).upper()

    if semantic_status_token == STATUS_PASS_REQUIRED and strict_live_proof_status == STATUS_PASS_REQUIRED:
        closure_class = "full_operational_closure"
        live_binding_strength = "strict"
        next_hop_consumption_status = STATUS_PASS_REQUIRED
    elif semantic_status_token == STATUS_PASS_REQUIRED and evidence_origin in {"sample", "history"}:
        closure_class = "sample_or_history_green"
        live_binding_strength = "weak"
        next_hop_consumption_status = STATUS_FAIL_REQUIRED
    elif semantic_status_token == STATUS_PASS_REQUIRED:
        closure_class = "unabsorbed_green"
        live_binding_strength = "weak"
        next_hop_consumption_status = STATUS_FAIL_REQUIRED
    else:
        closure_class = "structure_green"
        live_binding_strength = "none"
        next_hop_consumption_status = STATUS_FAIL_REQUIRED

    strict_live_operational_status = (
        STATUS_PASS_REQUIRED
        if semantic_status_token == STATUS_PASS_REQUIRED and strict_live_proof_status == STATUS_PASS_REQUIRED
        else STATUS_FAIL_REQUIRED
    )
    return {
        "semantic_contract_status": semantic_status_token,
        "strict_live_operational_status": strict_live_operational_status,
        "operational_closure_class": closure_class,
        "live_binding_strength": live_binding_strength,
        "next_hop_consumption_status": next_hop_consumption_status,
    }


def emit_payload(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
