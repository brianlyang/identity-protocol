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

ERR_RECEIPT_MISSING = "IP-INTERF-001"
ERR_FIELD_MISSING = "IP-INTERF-002"
ERR_REPLAY_MISSING = "IP-INTERF-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "refresh_strict_business_interference_matrix_contract_v1",
        "refresh_strict_business_interference_matrix_contract",
        "rq_016_refresh_strict_business_interference_matrix_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _latest(path_pattern: str, pack_path: Path) -> Path | None:
    token = str(path_pattern or "").strip()
    if not token:
        return None
    p = Path(token).expanduser()
    if p.is_absolute():
        hits = [Path(x).expanduser().resolve() for x in glob.glob(token)]
    else:
        hits = [x.resolve() for x in pack_path.glob(token)]
    hits = [x for x in hits if x.exists() and x.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def _load(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate refresh->strict business interference matrix contract (RQ-016).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--refresh-receipt", default="")
    ap.add_argument("--strict-receipt", default="")
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

    refresh_path = Path(args.refresh_receipt).expanduser().resolve() if args.refresh_receipt.strip() else _latest(
        str(contract.get("refresh_receipt_pattern", "")).strip() or "runtime/reports/business-interference-matrix-*-refresh-*.json",
        pack_path,
    )
    strict_path = Path(args.strict_receipt).expanduser().resolve() if args.strict_receipt.strip() else _latest(
        str(contract.get("strict_receipt_pattern", "")).strip() or "runtime/reports/business-interference-matrix-*-strict-*.json",
        pack_path,
    )
    refresh_doc = _load(refresh_path if refresh_path and refresh_path.exists() else None)
    strict_doc = _load(strict_path if strict_path and strict_path.exists() else None)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": bool(refresh_doc) and bool(strict_doc),
        "requiredization_current_round_linked": bool(refresh_doc) or bool(strict_doc),
        "refresh_strict_business_interference_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "refresh_receipt_ref": str(refresh_path) if refresh_path else "",
        "strict_receipt_ref": str(strict_path) if strict_path else "",
        "refresh_status": str((refresh_doc or {}).get("interference_matrix_status", "")).strip(),
        "strict_status": str((strict_doc or {}).get("interference_matrix_status", "")).strip(),
        "interference_row_count_refresh": len((refresh_doc or {}).get("interference_matrix_rows", []) or []),
        "interference_row_count_strict": len((strict_doc or {}).get("interference_matrix_rows", []) or []),
        "evidence_ref": str(strict_path or refresh_path or ""),
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if refresh_doc is None or strict_doc is None:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_missing_refresh_or_strict_receipt"]
            _emit(payload, json_only=args.json_only)
            return 0
        if (
            args.operation in {"update", "validate"}
            and not str(args.refresh_receipt or "").strip()
            and not str(args.strict_receipt or "").strip()
        ):
            payload["stale_reasons"] = ["required_contract_not_applicable_current_round_unmaterialized"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["refresh_strict_business_interference_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = ["refresh_or_strict_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    for node_name, node in (("refresh", refresh_doc), ("strict", strict_doc)):
        for field in ("interference_matrix_status", "interference_matrix_rows"):
            if field not in node:
                payload["refresh_strict_business_interference_status"] = STATUS_FAIL_REQUIRED
                payload["error_code"] = ERR_FIELD_MISSING
                payload["stale_reasons"] = [f"{node_name}_missing_field:{field}"]
                _emit(payload, json_only=args.json_only)
                return 1

    if str(refresh_doc.get("interference_matrix_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        payload["refresh_strict_business_interference_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPLAY_MISSING
        payload["stale_reasons"] = ["refresh_interference_status_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1
    if str(strict_doc.get("interference_matrix_status", "")).strip().upper() != STATUS_PASS_REQUIRED:
        payload["refresh_strict_business_interference_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REPLAY_MISSING
        payload["stale_reasons"] = ["strict_interference_status_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["refresh_strict_business_interference_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
