#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_SOURCE_MISSING = "IP-SEM-CONV-001"
ERR_MISMATCH = "IP-SEM-CONV-002"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "semantic_single_source_convergence_contract_v1",
        "semantic_single_source_convergence_contract",
        "rq_029_semantic_single_source_convergence_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _load_json(path: str) -> dict[str, Any]:
    if not str(path or "").strip():
        return {}
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _extract_semantic_tuple(doc: dict[str, Any]) -> tuple[str, str, str]:
    if not isinstance(doc, dict):
        return "", "", ""
    checks = doc.get("checks")
    if isinstance(checks, dict):
        semantic = checks.get("semantic_routing_guard")
        if isinstance(semantic, dict):
            status = str(semantic.get("semantic_routing_status", "")).strip()
            error = str(semantic.get("error_code", "")).strip()
            evidence = str(semantic.get("semantic_routing_evidence_path", "")).strip()
            if status:
                return status, error, evidence
    for key in ("semantic_routing_status", "semantic_status"):
        status = str(doc.get(key, "")).strip()
        if status:
            error = str(doc.get("semantic_routing_error_code", "") or doc.get("error_code", "")).strip()
            evidence = str(doc.get("semantic_routing_evidence_path", "") or doc.get("evidence_ref", "")).strip()
            return status, error, evidence
    return "", "", ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate semantic single-source convergence contract (RQ-029).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--update-report", default="")
    ap.add_argument("--three-plane-report", default="")
    ap.add_argument("--full-scan-report", default="")
    ap.add_argument("--lineage-ref", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"],
        default="validate",
    )
    ap.add_argument("--force-required", action="store_true")
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
    required = contract_required(contract)
    if args.force_required:
        required = True

    update_doc = _load_json(args.update_report)
    three_plane_doc = _load_json(args.three_plane_report)
    full_scan_doc = _load_json(args.full_scan_report)
    tuples = {
        "update": _extract_semantic_tuple(update_doc),
        "three_plane": _extract_semantic_tuple(three_plane_doc),
        "full_scan": _extract_semantic_tuple(full_scan_doc),
    }
    nonempty = {k: v for k, v in tuples.items() if v[0]}

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": bool(nonempty),
        "requiredization_current_round_linked": bool(nonempty),
        "semantic_convergence_status": STATUS_SKIPPED_NOT_REQUIRED,
        "semantic_convergence_error_code": "",
        "error_code": "",
        "lineage_ref": str(args.lineage_ref or "").strip(),
        "semantic_tuple_update": {"status": tuples["update"][0], "error_code": tuples["update"][1], "evidence": tuples["update"][2]},
        "semantic_tuple_three_plane": {"status": tuples["three_plane"][0], "error_code": tuples["three_plane"][1], "evidence": tuples["three_plane"][2]},
        "semantic_tuple_full_scan": {"status": tuples["full_scan"][0], "error_code": tuples["full_scan"][1], "evidence": tuples["full_scan"][2]},
        "mismatch_count": 0,
        "mismatch_fields": [],
        "evidence_ref": tuples["three_plane"][2] or tuples["full_scan"][2] or tuples["update"][2],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if len(nonempty) < 2:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_missing_lineage_reports"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["semantic_convergence_status"] = STATUS_FAIL_REQUIRED
        payload["semantic_convergence_error_code"] = ERR_SOURCE_MISSING
        payload["error_code"] = ERR_SOURCE_MISSING
        payload["stale_reasons"] = ["lineage_reports_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    baseline = next(iter(nonempty.values()))
    mismatch_fields: list[str] = []
    mismatch_count = 0
    for lane, current in nonempty.items():
        if current != baseline:
            mismatch_count += 1
            mismatch_fields.append(lane)
    payload["mismatch_count"] = mismatch_count
    payload["mismatch_fields"] = mismatch_fields

    if mismatch_count > 0:
        payload["semantic_convergence_status"] = STATUS_FAIL_REQUIRED
        payload["semantic_convergence_error_code"] = ERR_MISMATCH
        payload["error_code"] = ERR_MISMATCH
        payload["stale_reasons"] = ["semantic_tuple_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["semantic_convergence_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
