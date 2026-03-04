#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MATRIX_MISSING = "IP-CFIT-RVW-001"
ERR_REVIEW_FIELDS_MISSING = "IP-CFIT-RVW-002"
ERR_REVIEW_OVERDUE = "IP-CFIT-RVW-003"


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


def _parse_json_obj(raw: str) -> dict[str, Any] | None:
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(raw[start : end + 1])
        return obj if isinstance(obj, dict) else None
    except Exception:
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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate capability-fit review freshness (stale review visibility).")
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
        "capability_fit_review_freshness_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "fit_matrix_path": "",
        "selected_candidate_id": "",
        "selected_candidate_type": "",
        "next_review_at": "",
        "review_interval_days": None,
        "review_freshness_status": "",
        "overdue_by_days": None,
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(contract.get("fit_matrix_path_pattern", "")).strip()
    fit_path = _resolve_fit_matrix(pack_path, args.fit_matrix, pattern)
    if fit_path is None:
        payload["capability_fit_review_freshness_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["fit_matrix_path"] = str(fit_path)
    raw = fit_path.read_text(encoding="utf-8", errors="ignore")
    doc = _parse_json_obj(raw) or {}
    matrix = doc.get("capability_fit_matrix") if isinstance(doc, dict) else None
    if not isinstance(matrix, list):
        payload["capability_fit_review_freshness_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MATRIX_MISSING
        payload["stale_reasons"] = ["capability_fit_matrix_missing_or_invalid"]
        _emit(payload, json_only=args.json_only)
        return 1

    selected = [
        row
        for row in matrix
        if isinstance(row, dict) and str(row.get("decision", "")).strip().lower() == "selected"
    ]
    if len(selected) != 1:
        payload["capability_fit_review_freshness_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REVIEW_FIELDS_MISSING
        payload["stale_reasons"] = ["selected_candidate_count_must_equal_one"]
        _emit(payload, json_only=args.json_only)
        return 1

    row = selected[0]
    payload["selected_candidate_id"] = str(row.get("candidate_id", "")).strip()
    payload["selected_candidate_type"] = str(row.get("candidate_type", "")).strip()
    payload["next_review_at"] = row.get("next_review_at", "")
    payload["review_interval_days"] = row.get("review_interval_days")

    missing_fields: list[str] = []
    if not str(row.get("next_review_at", "")).strip():
        missing_fields.append("next_review_at")
    if row.get("review_interval_days") in (None, ""):
        missing_fields.append("review_interval_days")

    dt = _parse_time(row.get("next_review_at"))
    if dt is None:
        missing_fields.append("next_review_at_invalid")

    if missing_fields:
        payload["capability_fit_review_freshness_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REVIEW_FIELDS_MISSING
        payload["stale_reasons"] = [f"missing_or_invalid:{','.join(missing_fields)}"]
        _emit(payload, json_only=args.json_only)
        return 1

    now = datetime.now(timezone.utc)
    assert dt is not None
    if dt < now:
        overdue_days = round((now - dt).total_seconds() / 86400.0, 3)
        payload["capability_fit_review_freshness_status"] = STATUS_WARN_NON_BLOCKING
        payload["error_code"] = ERR_REVIEW_OVERDUE
        payload["review_freshness_status"] = "WARN_STALE_OPTIMIZATION_REVIEW"
        payload["overdue_by_days"] = overdue_days
        payload["stale_reasons"] = ["next_review_at_overdue"]
        _emit(payload, json_only=args.json_only)
        return 0

    payload["capability_fit_review_freshness_status"] = STATUS_PASS_REQUIRED
    payload["review_freshness_status"] = "FRESH"
    payload["overdue_by_days"] = 0.0
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
