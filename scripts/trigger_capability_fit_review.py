#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_NOT_TRIGGERED = "NOT_TRIGGERED"
STATUS_TRIGGERED_NON_BLOCKING = "TRIGGERED_NON_BLOCKING"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"

ERR_MATRIX_MISSING = "IP-CFIT-TRG-001"
ERR_SELECTED_PLAN_MISSING = "IP-CFIT-TRG-002"
ERR_TRIGGER_FIELDS_MISSING = "IP-CFIT-TRG-003"

ROUND_TABLE_REQUIRED_TAGS = {"tool_routing", "vendor_api_discovery", "solution_architecture"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "capability_fit_self_drive_optimization_contract_v1",
        "capability_fit_self_drive_optimization_contract",
    ):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    umbrella = task.get("platform_optimization_discovery_and_feeding_contract_v1")
    if isinstance(umbrella, dict):
        nested = umbrella.get("capability_fit_self_drive_optimization_contract_v1")
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


def _parse_time(v: Any) -> datetime | None:
    s = str(v or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _collect_tags(selected: dict[str, Any]) -> set[str]:
    tags: set[str] = set()
    for k in ("decision_impacts", "impact_domains", "affects_domains", "routing_domains", "decision_scope"):
        v = selected.get(k)
        if isinstance(v, list):
            tags.update(str(x).strip().lower() for x in v if str(x).strip())
        elif isinstance(v, str) and v.strip():
            tags.update(t.strip().lower() for t in v.split(",") if t.strip())
    return tags


def main() -> int:
    ap = argparse.ArgumentParser(description="Trigger capability-fit review workflow from latest fit matrix.")
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

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "capability_fit_review_trigger_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "triggered": False,
        "trigger_reason": "",
        "fit_matrix_path": "",
        "selected_candidate_id": "",
        "selected_candidate_type": "",
        "review_freshness_status": "",
        "roundtable_required": False,
        "roundtable_evidence_path": "",
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
        payload["capability_fit_review_trigger_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["fit_matrix_path"] = str(fit_path)
    matrix_doc = _extract_json_obj(fit_path.read_text(encoding="utf-8", errors="ignore")) or {}
    rows = matrix_doc.get("capability_fit_matrix") if isinstance(matrix_doc, dict) else None
    if not isinstance(rows, list):
        payload["capability_fit_review_trigger_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SELECTED_PLAN_MISSING
        payload["stale_reasons"] = ["capability_fit_matrix_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 0

    selected = [x for x in rows if isinstance(x, dict) and str(x.get("decision", "")).strip().lower() == "selected"]
    if len(selected) != 1:
        payload["capability_fit_review_trigger_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_SELECTED_PLAN_MISSING
        payload["stale_reasons"] = ["selected_candidate_count_must_equal_one"]
        _emit(payload, json_only=args.json_only)
        return 0

    sel = selected[0]
    payload["selected_candidate_id"] = str(sel.get("candidate_id", "")).strip()
    payload["selected_candidate_type"] = str(sel.get("candidate_type", "")).strip()

    next_review_at = _parse_time(sel.get("next_review_at"))
    if next_review_at is None:
        payload["capability_fit_review_trigger_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_TRIGGER_FIELDS_MISSING
        payload["stale_reasons"] = ["next_review_at_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 0

    now = datetime.now(timezone.utc)
    overdue = next_review_at < now
    payload["review_freshness_status"] = "WARN_STALE_OPTIMIZATION_REVIEW" if overdue else "FRESH"

    tags = _collect_tags(sel)
    roundtable_required = bool(tags & ROUND_TABLE_REQUIRED_TAGS)
    payload["roundtable_required"] = roundtable_required

    rt_path = _resolve_path(
        pack_path,
        explicit=args.roundtable_evidence,
        pattern=str(contract.get("roundtable_evidence_path_pattern", "")).strip(),
        default_pattern="runtime/protocol-feedback/roundtables/capability-fit-roundtable-*.json",
    )
    payload["roundtable_evidence_path"] = str(rt_path) if rt_path else ""

    trigger_reasons: list[str] = []
    if overdue:
        trigger_reasons.append("review_overdue")
    if roundtable_required and rt_path is None:
        trigger_reasons.append("roundtable_evidence_missing_for_selected_scope")

    if trigger_reasons:
        payload["capability_fit_review_trigger_status"] = STATUS_TRIGGERED_NON_BLOCKING
        payload["triggered"] = True
        payload["trigger_reason"] = ",".join(trigger_reasons)
        payload["stale_reasons"] = trigger_reasons
        _emit(payload, json_only=args.json_only)
        return 0

    payload["capability_fit_review_trigger_status"] = STATUS_NOT_TRIGGERED
    payload["triggered"] = False
    payload["trigger_reason"] = "trigger_conditions_not_met"
    payload["stale_reasons"] = ["trigger_conditions_not_met"]
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
