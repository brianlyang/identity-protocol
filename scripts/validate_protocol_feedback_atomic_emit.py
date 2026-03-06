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

ERR_RECEIPT_MISSING = "IP-PFAT-002"
ERR_FIELD_MISSING = "IP-PFAT-003"
ERR_LINK_MISSING = "IP-PFAT-004"
ERR_TX_MISMATCH = "IP-PFAT-005"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate"}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_atomic_emit_contract_v1",
        "protocol_feedback_atomic_emit_contract",
        "rq_013_protocol_feedback_atomic_emit_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _latest_receipt(pack_path: Path, pattern: str, transaction_id: str) -> Path | None:
    token = str(pattern or "").strip() or "runtime/protocol-feedback/atomic/*.receipt.json"
    p = Path(token).expanduser()
    if p.is_absolute():
        hits = [Path(x).expanduser().resolve() for x in glob.glob(token)]
    else:
        hits = [x.resolve() for x in pack_path.glob(token)]
    if transaction_id.strip():
        hits = [x for x in hits if transaction_id in x.name]
    hits = [x for x in hits if x.exists() and x.is_file()]
    if not hits:
        return None
    hits.sort(key=lambda x: x.stat().st_mtime)
    return hits[-1]


def _load_doc(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-feedback atomic emit contract (RQ-013).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--receipt", default="")
    ap.add_argument("--transaction-id", default="")
    ap.add_argument("--force-required", action="store_true")
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
    required = contract_required(contract)
    if args.force_required:
        required = True

    receipt_path: Path | None = None
    if args.receipt.strip():
        candidate = Path(args.receipt).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            receipt_path = candidate
    if receipt_path is None:
        receipt_path = _latest_receipt(pack_path, str(contract.get("receipt_path_pattern", "")).strip(), str(args.transaction_id or "").strip())
    receipt_doc = _load_doc(receipt_path) if receipt_path else None

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "task_path": str(task_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": bool(required and args.operation in STRICT_OPERATIONS),
        "producer_readiness": receipt_doc is not None,
        "requiredization_current_round_linked": receipt_path is not None,
        "protocol_feedback_atomic_emit_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "transaction_id": str((receipt_doc or {}).get("transaction_id", "")).strip(),
        "batch_ref": str((receipt_doc or {}).get("batch_ref", "")).strip(),
        "index_ref": str((receipt_doc or {}).get("index_ref", "")).strip(),
        "receipt_ref": str((receipt_doc or {}).get("receipt_ref", "")).strip(),
        "receipt_path": str(receipt_path) if receipt_path else "",
        "evidence_ref": str(receipt_path) if receipt_path else "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["required_contract_disabled_or_missing"]
        _emit(payload, json_only=args.json_only)
        return 0

    if receipt_doc is None or receipt_path is None:
        if args.operation in {"scan", "three-plane", "inspection"}:
            payload["stale_reasons"] = ["required_contract_not_applicable_no_atomic_receipt"]
            _emit(payload, json_only=args.json_only)
            return 0
        payload["protocol_feedback_atomic_emit_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RECEIPT_MISSING
        payload["stale_reasons"] = ["atomic_receipt_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    missing = [
        field
        for field in ("transaction_id", "batch_ref", "index_ref", "receipt_ref")
        if not str(receipt_doc.get(field, "")).strip()
    ]
    if missing:
        payload["protocol_feedback_atomic_emit_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_FIELD_MISSING
        payload["stale_reasons"] = [f"missing_field:{name}" for name in missing]
        _emit(payload, json_only=args.json_only)
        return 1

    tx = str(receipt_doc.get("transaction_id", "")).strip()
    if args.transaction_id.strip() and args.transaction_id.strip() != tx:
        payload["protocol_feedback_atomic_emit_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_TX_MISMATCH
        payload["stale_reasons"] = ["transaction_id_mismatch"]
        _emit(payload, json_only=args.json_only)
        return 1

    link_paths = [Path(str(receipt_doc.get("batch_ref", ""))).expanduser(), Path(str(receipt_doc.get("index_ref", ""))).expanduser()]
    missing_links = [str(p) for p in link_paths if not p.exists()]
    if missing_links:
        payload["protocol_feedback_atomic_emit_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_LINK_MISSING
        payload["stale_reasons"] = ["atomic_link_missing"]
        payload["missing_links"] = missing_links
        _emit(payload, json_only=args.json_only)
        return 1

    for p in link_paths:
        doc = _load_doc(p.resolve())
        if not isinstance(doc, dict) or str(doc.get("transaction_id", "")).strip() != tx:
            payload["protocol_feedback_atomic_emit_status"] = STATUS_FAIL_REQUIRED
            payload["error_code"] = ERR_TX_MISMATCH
            payload["stale_reasons"] = [f"link_transaction_id_mismatch:{p}"]
            _emit(payload, json_only=args.json_only)
            return 1

    payload["protocol_feedback_atomic_emit_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
