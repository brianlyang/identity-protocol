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

ERR_DECISION_MISSING = "IP-CFIT-COMP-001"
ERR_EXISTING_CANDIDATE_MISSING = "IP-CFIT-COMP-002"
ERR_EXTERNAL_WITHOUT_REASON = "IP-CFIT-COMP-003"


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate compose-before-discover decision gate in capability-fit cycle.")
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
        "compose_before_discovery_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "fit_matrix_path": "",
        "existing_composition_candidate_count": 0,
        "selected_candidate_type": "",
        "decision_basis": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    pattern = str(contract.get("fit_matrix_path_pattern", "")).strip()
    fit_path = _resolve_fit_matrix(pack_path, args.fit_matrix, pattern)
    if fit_path is None:
        payload["compose_before_discovery_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DECISION_MISSING
        payload["stale_reasons"] = ["fit_matrix_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["fit_matrix_path"] = str(fit_path)
    raw = fit_path.read_text(encoding="utf-8", errors="ignore")
    try:
        doc = json.loads(raw)
    except Exception:
        doc = {}

    matrix = doc.get("capability_fit_matrix") if isinstance(doc, dict) else None
    if not isinstance(matrix, list):
        payload["compose_before_discovery_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_DECISION_MISSING
        payload["stale_reasons"] = ["capability_fit_matrix_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    existing = [r for r in matrix if isinstance(r, dict) and str(r.get("candidate_type", "")).strip() == "existing_composition"]
    selected = [r for r in matrix if isinstance(r, dict) and str(r.get("decision", "")).strip() == "selected"]

    payload["existing_composition_candidate_count"] = len(existing)
    if selected:
        payload["selected_candidate_type"] = str(selected[0].get("candidate_type", "")).strip()
        payload["decision_basis"] = str(selected[0].get("decision_basis") or selected[0].get("selection_reason") or "").strip()

    stale_reasons: list[str] = []
    error_code = ""

    if len(existing) == 0:
        stale_reasons.append("existing_composition_candidate_missing")
        error_code = ERR_EXISTING_CANDIDATE_MISSING

    if len(selected) == 1:
        sel_type = str(selected[0].get("candidate_type", "")).strip()
        if sel_type == "external_candidate":
            basis = str(selected[0].get("decision_basis") or selected[0].get("selection_reason") or "").strip().lower()
            if not basis or not any(x in basis for x in ("not_sufficient", "not cost effective", "not_cost_effective")):
                stale_reasons.append("external_selected_without_not_sufficient_or_not_cost_effective_basis")
                if not error_code:
                    error_code = ERR_EXTERNAL_WITHOUT_REASON
    else:
        stale_reasons.append("selected_candidate_required_for_compose_before_discover")
        if not error_code:
            error_code = ERR_DECISION_MISSING

    if stale_reasons:
        payload["compose_before_discovery_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code or ERR_DECISION_MISSING
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["compose_before_discovery_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
