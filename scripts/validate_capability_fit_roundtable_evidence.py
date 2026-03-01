#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MATRIX_MISSING = "IP-CFIT-RTB-001"
ERR_ROUNDTABLE_MISSING = "IP-CFIT-RTB-002"
ERR_FACT_INFERENCE_INVALID = "IP-CFIT-RTB-003"
ERR_SELECTED_FACT_MAPPING = "IP-CFIT-RTB-004"

ROUND_TABLE_IMPACT_FIELDS = (
    "decision_impacts",
    "impact_domains",
    "affects_domains",
    "routing_domains",
    "decision_scope",
)
ROUND_TABLE_REQUIRED_TAGS = {"tool_routing", "vendor_api_discovery", "solution_architecture"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_roundtable_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "capability_fit_roundtable_evidence_contract_v1",
        "capability_fit_roundtable_evidence_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("capability_fit_roundtable_evidence_contract_v1")
        if isinstance(nested, dict):
            return nested

    return {}


def _resolve_path(pack_path: Path, explicit: str, pattern: str, default_pattern: str) -> Path | None:
    if explicit.strip():
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    raw = str(pattern or "").strip() or default_pattern
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    hits: list[Path] = []
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = sorted(pack_path.glob(raw))
        if preferred:
            hits = [x.resolve() for x in preferred]
        else:
            hits = [x.resolve() for x in Path(".").glob(raw)]

    hits = [x for x in hits if x.exists() and x.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def _extract_json_obj(raw: str) -> dict[str, Any] | None:
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


def _selected_row(matrix_doc: dict[str, Any]) -> dict[str, Any] | None:
    rows = matrix_doc.get("capability_fit_matrix")
    if not isinstance(rows, list):
        return None
    selected = [x for x in rows if isinstance(x, dict) and str(x.get("decision", "")).strip().lower() == "selected"]
    if len(selected) != 1:
        return None
    return selected[0]


def _roundtable_required_for_selected(selected: dict[str, Any]) -> bool:
    tags: set[str] = set()
    for k in ROUND_TABLE_IMPACT_FIELDS:
        v = selected.get(k)
        if isinstance(v, list):
            tags.update(str(x).strip().lower() for x in v if str(x).strip())
        elif isinstance(v, str) and v.strip():
            tags.update(t.strip().lower() for t in v.split(",") if t.strip())

    return bool(tags & ROUND_TABLE_REQUIRED_TAGS)


def _collect_fact_ids(facts: list[Any]) -> set[str]:
    ids: set[str] = set()
    for x in facts:
        if not isinstance(x, dict):
            continue
        if str(x.get("fact_id", "")).strip():
            ids.add(str(x.get("fact_id", "")).strip())
        if str(x.get("id", "")).strip():
            ids.add(str(x.get("id", "")).strip())
    return ids


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability-fit roundtable fact/inference evidence mapping.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--fit-matrix", default="")
    ap.add_argument("--roundtable-evidence", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    contract = _select_roundtable_contract(task)
    required = contract_required(contract) if contract else False

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "capability_fit_roundtable_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "fit_matrix_path": "",
        "roundtable_evidence_path": "",
        "selected_candidate_id": "",
        "selected_candidate_type": "",
        "roundtable_required": False,
        "facts_count": 0,
        "inferences_count": 0,
        "selected_fact_refs": [],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    fit_pattern = str(contract.get("fit_matrix_path_pattern", "")).strip()
    fit_path = _resolve_path(
        pack_path,
        explicit=args.fit_matrix,
        pattern=fit_pattern,
        default_pattern="runtime/protocol-feedback/optimization/capability-fit-matrix-*.json",
    )
    if fit_path is None:
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["fit_matrix_path"] = str(fit_path)
    matrix_doc = _extract_json_obj(fit_path.read_text(encoding="utf-8", errors="ignore")) or {}
    selected = _selected_row(matrix_doc)
    if not isinstance(selected, dict):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["selected_candidate_count_must_equal_one"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["selected_candidate_id"] = str(selected.get("candidate_id", "")).strip()
    payload["selected_candidate_type"] = str(selected.get("candidate_type", "")).strip()

    roundtable_required = _roundtable_required_for_selected(selected)
    payload["roundtable_required"] = roundtable_required
    if not roundtable_required:
        payload["capability_fit_roundtable_status"] = STATUS_PASS_REQUIRED
        payload["stale_reasons"] = ["roundtable_not_required_for_selected_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    roundtable_pattern = str(contract.get("roundtable_evidence_path_pattern", "")).strip()
    roundtable_path = _resolve_path(
        pack_path,
        explicit=args.roundtable_evidence,
        pattern=roundtable_pattern,
        default_pattern="runtime/protocol-feedback/roundtables/capability-fit-roundtable-*.json",
    )
    if roundtable_path is None:
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_ROUNDTABLE_MISSING
        payload["stale_reasons"] = ["roundtable_evidence_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["roundtable_evidence_path"] = str(roundtable_path)
    round_doc = _extract_json_obj(roundtable_path.read_text(encoding="utf-8", errors="ignore")) or {}
    facts = round_doc.get("facts")
    inferences = round_doc.get("inferences")
    if not isinstance(facts, list) or not isinstance(inferences, list):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FACT_INFERENCE_INVALID
        payload["stale_reasons"] = ["facts_or_inferences_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["facts_count"] = len(facts)
    payload["inferences_count"] = len(inferences)

    selected_mapping = round_doc.get("selected_plan_mapping")
    selected_fact_refs: list[str] = []
    if isinstance(selected_mapping, dict):
        refs = selected_mapping.get("fact_refs")
        if isinstance(refs, list):
            selected_fact_refs = [str(x).strip() for x in refs if str(x).strip()]
    if not selected_fact_refs:
        refs = selected.get("fact_refs")
        if isinstance(refs, list):
            selected_fact_refs = [str(x).strip() for x in refs if str(x).strip()]

    payload["selected_fact_refs"] = selected_fact_refs

    fact_ids = _collect_fact_ids(facts)
    if not selected_fact_refs or (fact_ids and not any(x in fact_ids for x in selected_fact_refs)):
        payload["capability_fit_roundtable_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_SELECTED_FACT_MAPPING
        payload["stale_reasons"] = ["selected_plan_missing_fact_mapping"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["capability_fit_roundtable_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
