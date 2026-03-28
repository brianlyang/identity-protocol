#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from protocol_feedback_archival_common import materialize_feedback_outbox_batch
from protocol_feedback_contract_common import canonical_dirs, rel_to_feedback_root
from tool_vendor_governance_common import load_json, resolve_pack_and_task

INSPECTION_OUTBOX_SYNC_SKIP_OPERATIONS = {"scan", "three-plane", "inspection"}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _safe_cleanup(paths: list[Path]) -> None:
    for p in paths:
        try:
            if p.exists():
                p.unlink()
        except Exception:
            continue


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit protocol-feedback atomic transaction artifacts (RQ-013).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--operation", default="update")
    ap.add_argument("--transaction-id", default="")
    ap.add_argument("--payload-json", default="")
    ap.add_argument("--force-outbox-sync", action="store_true")
    ap.add_argument("--skip-outbox-sync", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        _ = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    tx = str(args.transaction_id).strip() or f"pf-{uuid.uuid4().hex}"
    now = _now_iso()
    atomic_root = (pack_path / "runtime" / "protocol-feedback" / "atomic").resolve()
    feedback_root = atomic_root.parent.resolve()
    canonical = canonical_dirs(feedback_root)
    batch_path = (atomic_root / f"{tx}.batch.json").resolve()
    index_path = (atomic_root / f"{tx}.index.json").resolve()
    receipt_path = (atomic_root / f"{tx}.receipt.json").resolve()

    raw_payload: dict[str, Any] = {}
    if args.payload_json.strip():
        payload_file = Path(args.payload_json).expanduser().resolve()
        if payload_file.exists() and payload_file.is_file():
            try:
                loaded = json.loads(payload_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    raw_payload = loaded
            except Exception:
                raw_payload = {}

    temp_paths = [
        batch_path.with_suffix(".batch.tmp"),
        index_path.with_suffix(".index.tmp"),
        receipt_path.with_suffix(".receipt.tmp"),
    ]
    finals = [batch_path, index_path, receipt_path]

    try:
        batch_payload = {
            "transaction_id": tx,
            "identity_id": args.identity_id,
            "operation": args.operation,
            "observed_at_utc": now,
            "payload": raw_payload,
        }
        index_payload = {
            "transaction_id": tx,
            "identity_id": args.identity_id,
            "batch_ref": str(batch_path),
            "observed_at_utc": now,
        }
        receipt_payload = {
            "transaction_id": tx,
            "identity_id": args.identity_id,
            "operation": args.operation,
            "batch_ref": str(batch_path),
            "index_ref": str(index_path),
            "receipt_ref": str(receipt_path),
            "atomic_emit_status": "PASS_REQUIRED",
            "observed_at_utc": now,
            "rollback_performed": False,
            "evidence_ref": str(receipt_path),
        }

        _write_json(temp_paths[0], batch_payload)
        _write_json(temp_paths[1], index_payload)
        _write_json(temp_paths[2], receipt_payload)
        for src, dst in zip(temp_paths, finals):
            src.replace(dst)
    except Exception as exc:
        _safe_cleanup(temp_paths + finals)
        fail_payload = {
            "transaction_id": tx,
            "identity_id": args.identity_id,
            "operation": args.operation,
            "atomic_emit_status": "FAIL_REQUIRED",
            "error_code": "IP-PFAT-001",
            "rollback_performed": True,
            "error_reason": str(exc),
            "batch_ref": str(batch_path),
            "index_ref": str(index_path),
            "receipt_ref": str(receipt_path),
        }
        if args.json_only:
            print(json.dumps(fail_payload, ensure_ascii=False))
        else:
            print(json.dumps(fail_payload, ensure_ascii=False, indent=2))
        return 1

    normalized_operation = str(args.operation or "").strip().lower()
    outbox_sync_payload: dict[str, Any] = {}
    outbox_sync_status = "SKIPPED_BY_FLAG"
    if args.skip_outbox_sync:
        outbox_sync_payload = {
            "reason": "skip_outbox_sync_flag",
            "operation": normalized_operation,
        }
    elif not args.force_outbox_sync and normalized_operation in INSPECTION_OUTBOX_SYNC_SKIP_OPERATIONS:
        outbox_sync_status = "SKIPPED_NOT_REQUIRED"
        outbox_sync_payload = {
            "reason": "inspection_operation_default_no_outbox_sync",
            "operation": normalized_operation,
        }
    else:
        atomic_batch_rel = rel_to_feedback_root(batch_path, feedback_root)
        atomic_index_rel = rel_to_feedback_root(index_path, feedback_root)
        atomic_receipt_rel = rel_to_feedback_root(receipt_path, feedback_root)
        markdown_body = "\n".join(
            [
                f"transaction_id: {tx}",
                f"identity_id: {args.identity_id}",
                f"operation: {args.operation}",
                f"observed_at_utc: {now}",
                f"atomic_batch_ref: {atomic_batch_rel}",
                f"atomic_index_ref: {atomic_index_rel}",
                f"atomic_receipt_ref: {atomic_receipt_rel}",
                "",
                "## Atomic payload",
                "```json",
                json.dumps(raw_payload, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
        outbox_sync_payload = materialize_feedback_outbox_batch(
            feedback_root=feedback_root,
            outbox_dir=canonical["outbox_dir"],
            index_path=canonical["index_path"],
            identity_id=str(args.identity_id or "").strip(),
            catalog_path=str(catalog_path),
            body=markdown_body,
            title="Protocol feedback atomic transaction",
            slug=f"atomic-{tx}",
            summary_payload={
                "identity_id": str(args.identity_id or "").strip(),
                "transaction_id": tx,
                "operation": str(args.operation or "").strip(),
                "observed_at_utc": now,
                "atomic_batch_ref": atomic_batch_rel,
                "atomic_index_ref": atomic_index_rel,
                "atomic_receipt_ref": atomic_receipt_rel,
            },
            section_title="Protocol feedback linkage auto",
            extra_receipt_fields={
                "source_mode": "atomic_transaction",
                "atomic_transaction_id": tx,
                "atomic_batch_ref": atomic_batch_rel,
                "atomic_index_ref": atomic_index_rel,
                "atomic_receipt_ref": atomic_receipt_rel,
            },
        )
        outbox_sync_status = str(outbox_sync_payload.get("protocol_feedback_emit_status", "")).strip() or "FAIL_REQUIRED"
        if outbox_sync_status != "PASS_REQUIRED":
            fail_payload = {
                "transaction_id": tx,
                "identity_id": args.identity_id,
                "operation": args.operation,
                "atomic_emit_status": "FAIL_REQUIRED",
                "error_code": "IP-PFAT-006",
                "rollback_performed": False,
                "error_reason": "atomic_emit_outbox_sync_failed",
                "batch_ref": str(batch_path),
                "index_ref": str(index_path),
                "receipt_ref": str(receipt_path),
                "outbox_sync_status": outbox_sync_status,
                "outbox_sync_payload": outbox_sync_payload,
            }
            if args.json_only:
                print(json.dumps(fail_payload, ensure_ascii=False))
            else:
                print(json.dumps(fail_payload, ensure_ascii=False, indent=2))
            return 1

    payload = {
        "transaction_id": tx,
        "identity_id": args.identity_id,
        "operation": args.operation,
        "atomic_emit_status": "PASS_REQUIRED",
        "error_code": "",
        "rollback_performed": False,
        "batch_ref": str(batch_path),
        "index_ref": str(index_path),
        "receipt_ref": str(receipt_path),
        "evidence_ref": str(receipt_path),
        "outbox_sync_status": outbox_sync_status,
        "outbox_sync_payload": outbox_sync_payload,
    }
    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(f"[OK] wrote: {receipt_path}")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
