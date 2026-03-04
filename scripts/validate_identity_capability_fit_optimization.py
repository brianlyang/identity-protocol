#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MATRIX_MISSING = "IP-CFIT-001"
ERR_SELECTED_COUNT = "IP-CFIT-002"
ERR_SELECTED_FIELDS = "IP-CFIT-003"
ERR_STALE_REVIEW = "IP-CFIT-004"

REQUIRED_MATRIX_FIELDS = (
    "candidate_id",
    "candidate_type",
    "fit_score",
    "risk_score",
    "operational_cost_score",
    "provenance_ref",
    "decision",
)


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
    return {}


def _resolve_fit_matrix(pack_path: Path, report: str, pattern: str) -> Path | None:
    if report.strip():
        p = Path(report).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    raw = str(pattern or "").strip() or "runtime/protocol-feedback/optimization/capability-fit-matrix-*.json"
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


def _parse_float(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def _parse_time(v: Any) -> datetime | None:
    s = str(v or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


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


def _extract_from_markdown(raw: str) -> dict[str, Any]:
    # fallback for markdown-ish evidence
    out: dict[str, Any] = {}
    match_next = re.search(r"\bnext_review_at\b\s*[:=]\s*([^\n]+)", raw, flags=re.IGNORECASE)
    if match_next:
        out["next_review_at"] = match_next.group(1).strip().strip("`")
    match_interval = re.search(r"\breview_interval_days\b\s*[:=]\s*([0-9]+)", raw, flags=re.IGNORECASE)
    if match_interval:
        out["review_interval_days"] = int(match_interval.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability-fit self-drive optimization matrix and freshness semantics.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--fit-matrix", default="")
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
        "capability_fit_optimization_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "fit_matrix_path": "",
        "matrix_candidate_count": 0,
        "selected_candidate_count": 0,
        "selected_candidate_ids": [],
        "missing_required_fields": [],
        "selected_missing_fields": [],
        "next_review_at": "",
        "review_interval_days": None,
        "review_freshness_status": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(contract.get("fit_matrix_path_pattern", "")).strip()
    fit_matrix_path = _resolve_fit_matrix(pack_path, args.fit_matrix, pattern)
    if fit_matrix_path is None:
        payload["capability_fit_optimization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    raw = fit_matrix_path.read_text(encoding="utf-8", errors="ignore")
    obj = _extract_json_obj(raw)
    md_fallback: dict[str, Any] = {}
    if obj is None:
        md_fallback = _extract_from_markdown(raw)
        obj = {"capability_fit_matrix": []}

    matrix = obj.get("capability_fit_matrix") if isinstance(obj, dict) else None
    if not isinstance(matrix, list):
        payload["fit_matrix_path"] = str(fit_matrix_path)
        payload["capability_fit_optimization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["capability_fit_matrix_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["fit_matrix_path"] = str(fit_matrix_path)
    payload["matrix_candidate_count"] = len(matrix)

    missing_fields: list[str] = []
    selected_rows: list[dict[str, Any]] = []
    for i, row in enumerate(matrix):
        if not isinstance(row, dict):
            missing_fields.append(f"row[{i}]:not_object")
            continue
        for field in REQUIRED_MATRIX_FIELDS:
            v = row.get(field)
            if v is None or (isinstance(v, str) and not v.strip()):
                missing_fields.append(f"row[{i}].{field}")
        decision = str(row.get("decision", "")).strip().lower()
        if decision == "selected":
            selected_rows.append(row)

    payload["missing_required_fields"] = missing_fields
    payload["selected_candidate_count"] = len(selected_rows)
    payload["selected_candidate_ids"] = [str(x.get("candidate_id", "")).strip() for x in selected_rows]

    stale_reasons: list[str] = []
    error_code = ""

    if missing_fields:
        stale_reasons.append("fit_matrix_missing_required_fields")
        error_code = ERR_MATRIX_MISSING

    if len(selected_rows) != 1:
        stale_reasons.append("selected_candidate_count_must_equal_one")
        if not error_code:
            error_code = ERR_SELECTED_COUNT

    selected_missing: list[str] = []
    next_review_at = None
    review_interval_days = None
    if len(selected_rows) == 1:
        selected = selected_rows[0]
        for field in ("fallback_ref", "rollback_ref", "review_interval_days", "next_review_at"):
            v = selected.get(field)
            if v is None or (isinstance(v, str) and not v.strip()):
                selected_missing.append(field)
        next_review_at = _parse_time(selected.get("next_review_at"))
        review_interval_days = _parse_float(selected.get("review_interval_days"))
    else:
        # fallback from top-level if single selected unavailable (markdown fallback)
        if md_fallback:
            next_review_at = _parse_time(md_fallback.get("next_review_at"))
            review_interval_days = _parse_float(md_fallback.get("review_interval_days"))

    payload["selected_missing_fields"] = selected_missing
    if selected_missing:
        stale_reasons.append("selected_candidate_missing_fallback_or_review_fields")
        if not error_code:
            error_code = ERR_SELECTED_FIELDS

    payload["next_review_at"] = selected_rows[0].get("next_review_at", "") if len(selected_rows) == 1 else str(md_fallback.get("next_review_at", ""))
    payload["review_interval_days"] = selected_rows[0].get("review_interval_days") if len(selected_rows) == 1 else md_fallback.get("review_interval_days")

    review_status = "UNKNOWN"
    if next_review_at is not None:
        now = datetime.now(timezone.utc)
        if next_review_at.tzinfo is None:
            next_review_at = next_review_at.replace(tzinfo=timezone.utc)
        if next_review_at < now:
            review_status = "WARN_STALE_OPTIMIZATION_REVIEW"
            stale_reasons.append("next_review_at_overdue")
            if not error_code:
                error_code = ERR_STALE_REVIEW
        else:
            review_status = "FRESH"
    payload["review_freshness_status"] = review_status

    if stale_reasons:
        # stale review is warning in P1 lane; structural issues remain fail when required
        if error_code == ERR_STALE_REVIEW and not missing_fields and not selected_missing and len(selected_rows) == 1:
            payload["capability_fit_optimization_status"] = STATUS_WARN_NON_BLOCKING
            payload["error_code"] = error_code
            payload["stale_reasons"] = stale_reasons
            _emit(payload, json_only=args.json_only)
            return 0

        payload["capability_fit_optimization_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_MATRIX_MISSING
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["capability_fit_optimization_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
