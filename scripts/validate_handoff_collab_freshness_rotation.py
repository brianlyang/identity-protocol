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

ERR_RECEIPT_MISSING = "IP-FRESH-001"
ERR_FIELD_MISSING = "IP-FRESH-002"
ERR_STATUS_FAILED = "IP-FRESH-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "handoff_collab_freshness_autorotation_contract_v1",
        "handoff_collab_freshness_autorotation_contract",
        "rq_012_handoff_collab_freshness_autorotation_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _resolve_receipt(pack_path: Path, explicit: str, pattern: str) -> Path | None:
    if explicit.strip():
        p = Path(explicit).expanduser().resolve()
        return p if p.exists() and p.is_file() else None
    token = str(pattern or "").strip() or "runtime/reports/handoff-collab-freshness-rotation-*.json"
    p = Path(token).expanduser()
    hits: list[Path] = []
    if p.is_absolute():
        hits = [Path(x).expanduser().resolve() for x in glob.glob(token)]
    else:
        hits = [x.resolve() for x in pack_path.glob(token)]
    hits = [x for x in hits if x.exists() and x.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate handoff/collab freshness autorotation contract (RQ-012).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--receipt", default="")
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

    pattern = str(contract.get("rotation_receipt_pattern", "")).strip()
    receipt_path = _resolve_receipt(pack_path, args.receipt, pattern)
    receipt_doc: dict[str, Any] = {}
    if receipt_path is not None:
        try:
            loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                receipt_doc = loaded
        except Exception:
            receipt_doc = {}

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": receipt_path is not None and bool(receipt_doc),
        "requiredization_current_round_linked": receipt_path is not None,
        "handoff_collab_freshness_rotation_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "rotation_applied": bool(receipt_doc.get("rotation_applied", False)),
        "freshness_age_days": float(receipt_doc.get("freshness_age_days", 0.0)) if receipt_doc else 0.0,
        "rotation_receipt_ref": str(receipt_path) if receipt_path else "",
        "freshness_status": str(receipt_doc.get("freshness_status", "")).strip(),
        "evidence_ref": str(receipt_path) if receipt_path else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if receipt_path is None or not receipt_doc:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_rotation_receipt"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["handoff_collab_freshness_rotation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = ["rotation_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    missing: list[str] = []
    for field in ("rotation_applied", "freshness_age_days", "rotation_receipt_ref", "freshness_status"):
        value = receipt_doc.get(field)
        if field == "rotation_applied":
            if not isinstance(value, bool):
                missing.append(field)
        elif field == "freshness_age_days":
            if value is None:
                missing.append(field)
        else:
            if not str(value or "").strip():
                missing.append(field)

    if missing:
        payload["handoff_collab_freshness_rotation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FIELD_MISSING
        payload["stale_reasons"] = [f"missing_field:{name}" for name in missing]
        _emit(payload, json_only=args.json_only)
        return 1

    freshness_status = str(receipt_doc.get("freshness_status", "")).strip().upper()
    payload["freshness_status"] = freshness_status
    if freshness_status != STATUS_PASS_REQUIRED:
        payload["handoff_collab_freshness_rotation_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STATUS_FAILED
        payload["stale_reasons"] = ["freshness_status_not_pass_required"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["handoff_collab_freshness_rotation_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
