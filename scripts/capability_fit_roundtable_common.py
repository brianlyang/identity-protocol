#!/usr/bin/env python3
from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import PROTOCOL_FEEDBACK_ROOT_REL

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MATRIX_MISSING = "IP-CFIT-RTB-001"
ERR_ROUNDTABLE_MISSING = "IP-CFIT-RTB-002"
ERR_FACT_INFERENCE_INVALID = "IP-CFIT-RTB-003"
ERR_SELECTED_FACT_MAPPING = "IP-CFIT-RTB-004"

DEFAULT_FIT_MATRIX_PATTERN = (
    PROTOCOL_FEEDBACK_ROOT_REL / "optimization" / "capability-fit-matrix-*.json"
).as_posix()
DEFAULT_ROUNDTABLE_PATTERN = (
    PROTOCOL_FEEDBACK_ROOT_REL / "roundtables" / "capability-fit-roundtable-*.json"
).as_posix()

ROUND_TABLE_IMPACT_FIELDS = (
    "decision_impacts",
    "impact_domains",
    "affects_domains",
    "routing_domains",
    "decision_scope",
)
ROUND_TABLE_REQUIRED_TAGS = {"tool_routing", "vendor_api_discovery", "solution_architecture"}


def clean_string(value: Any) -> str:
    return str(value or "").strip()


def select_roundtable_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "capability_fit_roundtable_evidence_contract_v1",
        "capability_fit_roundtable_evidence_contract",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("capability_fit_roundtable_evidence_contract_v1")
        if isinstance(nested, dict):
            return nested

    return {}


def resolve_artifact_path(
    *,
    pack_root: Path,
    explicit: str,
    pattern: str,
    default_pattern: str,
) -> Path | None:
    if clean_string(explicit):
        candidate = Path(clean_string(explicit)).expanduser().resolve()
        return candidate if candidate.exists() and candidate.is_file() else None

    raw = clean_string(pattern) or default_pattern
    candidate = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ("*", "?", "["))
    hits: list[Path] = []
    if candidate.is_absolute():
        if has_magic:
            hits = [Path(item).expanduser().resolve() for item in glob.glob(str(candidate))]
        elif candidate.exists():
            hits = [candidate.resolve()]
    else:
        preferred = sorted(pack_root.glob(raw))
        if preferred:
            hits = [item.resolve() for item in preferred]
        else:
            hits = [item.resolve() for item in Path(".").glob(raw)]

    hits = [item for item in hits if item.exists() and item.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda item: item.stat().st_mtime)
    return hits[-1]


def resolve_fit_matrix_artifact_path(
    *,
    pack_root: Path,
    explicit: str = "",
    pattern: str = "",
) -> Path | None:
    return resolve_artifact_path(
        pack_root=pack_root,
        explicit=explicit,
        pattern=pattern,
        default_pattern=DEFAULT_FIT_MATRIX_PATTERN,
    )


def resolve_roundtable_artifact_path(
    *,
    pack_root: Path,
    explicit: str = "",
    pattern: str = "",
) -> Path | None:
    return resolve_artifact_path(
        pack_root=pack_root,
        explicit=explicit,
        pattern=pattern,
        default_pattern=DEFAULT_ROUNDTABLE_PATTERN,
    )


def extract_json_obj(raw: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(raw[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None
    return None


def selected_matrix_row(matrix_doc: dict[str, Any]) -> dict[str, Any] | None:
    rows = matrix_doc.get("capability_fit_matrix")
    if not isinstance(rows, list):
        return None
    selected = [row for row in rows if isinstance(row, dict) and clean_string(row.get("decision")).lower() == "selected"]
    if len(selected) != 1:
        return None
    return selected[0]


def roundtable_required_for_selected(selected: dict[str, Any]) -> bool:
    tags: set[str] = set()
    for key in ROUND_TABLE_IMPACT_FIELDS:
        value = selected.get(key)
        if isinstance(value, list):
            tags.update(clean_string(item).lower() for item in value if clean_string(item))
        elif clean_string(value):
            tags.update(token.strip().lower() for token in clean_string(value).split(",") if token.strip())
    return bool(tags & ROUND_TABLE_REQUIRED_TAGS)


def collect_fact_ids(facts: list[Any]) -> set[str]:
    fact_ids: set[str] = set()
    for row in facts:
        if not isinstance(row, dict):
            continue
        for key in ("fact_id", "id"):
            token = clean_string(row.get(key))
            if token:
                fact_ids.add(token)
    return fact_ids


def selected_fact_refs(selected: dict[str, Any], round_doc: dict[str, Any] | None = None) -> list[str]:
    if isinstance(round_doc, dict):
        mapping = round_doc.get("selected_plan_mapping")
        if isinstance(mapping, dict):
            refs = mapping.get("fact_refs")
            if isinstance(refs, list):
                rows = [clean_string(item) for item in refs if clean_string(item)]
                if rows:
                    return rows
    refs = selected.get("fact_refs")
    if isinstance(refs, list):
        return [clean_string(item) for item in refs if clean_string(item)]
    return []


def resolve_selection_basis(selected: dict[str, Any], round_doc: dict[str, Any] | None = None) -> str:
    mapping = round_doc.get("selected_plan_mapping") if isinstance(round_doc, dict) else {}
    if isinstance(mapping, dict):
        for key in ("selection_basis", "decision_basis", "basis"):
            token = clean_string(mapping.get(key))
            if token:
                return token

    for key in ("decision_basis", "selection_basis", "provenance_ref", "source"):
        token = clean_string(selected.get(key))
        if token:
            return token

    refs = selected_fact_refs(selected, round_doc)
    if refs:
        return "roundtable_fact_mapping"
    if clean_string(selected.get("candidate_type")):
        return f"selected:{clean_string(selected.get('candidate_type'))}"
    return "capability_fit_selected"


def derive_roundtable_evidence_payload(
    *,
    pack_root: Path,
    task_doc: dict[str, Any],
    explicit_fit_matrix: str = "",
    explicit_roundtable: str = "",
    identity_id: str = "",
    operation: str = "",
) -> dict[str, Any]:
    contract_doc = select_roundtable_contract(task_doc)
    required_contract = isinstance(contract_doc, dict) and bool(contract_doc.get("required")) is True

    payload: dict[str, Any] = {
        "identity_id": clean_string(identity_id),
        "resolved_pack_path": str(pack_root.resolve()),
        "operation": clean_string(operation),
        "required_contract": required_contract,
        "capability_fit_roundtable_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "fit_matrix_path": "",
        "roundtable_evidence_path": "",
        "selected_candidate_id": "",
        "selected_candidate_type": "",
        "selection_basis": "",
        "selected_candidate_receipt_ref": "",
        "roundtable_receipt_ref": "",
        "roundtable_required": False,
        "facts_count": 0,
        "inferences_count": 0,
        "selected_fact_refs": [],
        "stale_reasons": [],
    }

    if not required_contract:
        payload["stale_reasons"] = ["contract_not_required"]
        return payload

    fit_path = resolve_artifact_path(
        pack_root=pack_root,
        explicit=explicit_fit_matrix,
        pattern=clean_string(contract_doc.get("fit_matrix_path_pattern")),
        default_pattern=DEFAULT_FIT_MATRIX_PATTERN,
    )
    if fit_path is None:
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        return payload

    payload["fit_matrix_path"] = str(fit_path)
    payload["selected_candidate_receipt_ref"] = str(fit_path)
    matrix_doc = extract_json_obj(fit_path.read_text(encoding="utf-8", errors="ignore")) or {}
    selected = selected_matrix_row(matrix_doc)
    if not isinstance(selected, dict):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["selected_candidate_count_must_equal_one"]
        return payload

    payload["selected_candidate_id"] = clean_string(selected.get("candidate_id"))
    payload["selected_candidate_type"] = clean_string(selected.get("candidate_type"))
    payload["selection_basis"] = resolve_selection_basis(selected)
    payload["selected_fact_refs"] = selected_fact_refs(selected)

    roundtable_required = roundtable_required_for_selected(selected)
    payload["roundtable_required"] = roundtable_required
    if not roundtable_required:
        payload["capability_fit_roundtable_status"] = STATUS_PASS_REQUIRED
        payload["stale_reasons"] = ["roundtable_not_required_for_selected_scope"]
        return payload

    roundtable_path = resolve_artifact_path(
        pack_root=pack_root,
        explicit=explicit_roundtable,
        pattern=clean_string(contract_doc.get("roundtable_evidence_path_pattern")),
        default_pattern=DEFAULT_ROUNDTABLE_PATTERN,
    )
    if roundtable_path is None:
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ROUNDTABLE_MISSING
        payload["stale_reasons"] = ["roundtable_evidence_not_found"]
        return payload

    payload["roundtable_evidence_path"] = str(roundtable_path)
    payload["roundtable_receipt_ref"] = str(roundtable_path)
    round_doc = extract_json_obj(roundtable_path.read_text(encoding="utf-8", errors="ignore")) or {}
    facts = round_doc.get("facts")
    inferences = round_doc.get("inferences")
    if not isinstance(facts, list) or not isinstance(inferences, list):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FACT_INFERENCE_INVALID
        payload["stale_reasons"] = ["facts_or_inferences_missing_or_invalid"]
        return payload

    payload["facts_count"] = len(facts)
    payload["inferences_count"] = len(inferences)
    payload["selected_fact_refs"] = selected_fact_refs(selected, round_doc)
    payload["selection_basis"] = resolve_selection_basis(selected, round_doc)

    fact_ids = collect_fact_ids(facts)
    if not payload["selected_fact_refs"] or (fact_ids and not any(ref in fact_ids for ref in payload["selected_fact_refs"])):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SELECTED_FACT_MAPPING
        payload["stale_reasons"] = ["selected_plan_missing_fact_mapping"]
        return payload

    payload["capability_fit_roundtable_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    return payload
