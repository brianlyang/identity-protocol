#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from actor_session_common import resolve_actor_id
from protocol_feedback_contract_common import (
    canonical_dirs,
    ensure_index_linkage,
    is_strict_operation,
    rel_to_feedback_root,
    resolve_feedback_root,
    utc_now_z,
    write_json,
)
from tool_vendor_governance_common import resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_WARN_NON_BLOCKING = "WARN_NON_BLOCKING"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_LANE_LOCK_EXIT_WRITE = "IP-LAYER-GATE-008"
ERR_LANE_LOCK_EXIT_INDEX = "IP-LAYER-GATE-009"

LOCK_PROTOCOL_PREFIX = "SESSION_LANE_LOCK_PROTOCOL_"
LOCK_EXIT_PREFIX = "SESSION_LANE_LOCK_EXIT_"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _latest_lane_lock_receipt(
    *,
    outbox_dir: Path,
    prefix: str,
    identity_id: str,
) -> Path | None:
    if not outbox_dir.exists():
        return None
    rows = sorted(outbox_dir.glob(f"{prefix}*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for p in rows:
        doc = _safe_json(p)
        rid = str(doc.get("identity_id", "")).strip()
        if rid and rid != identity_id:
            continue
        return p.resolve()
    return None


def _resolve_active_lock(
    *,
    outbox_dir: Path,
    identity_id: str,
) -> Path | None:
    lock_protocol = _latest_lane_lock_receipt(outbox_dir=outbox_dir, prefix=LOCK_PROTOCOL_PREFIX, identity_id=identity_id)
    lock_exit = _latest_lane_lock_receipt(outbox_dir=outbox_dir, prefix=LOCK_EXIT_PREFIX, identity_id=identity_id)
    if lock_protocol is None:
        return None
    protocol_mtime = lock_protocol.stat().st_mtime
    exit_mtime = lock_exit.stat().st_mtime if lock_exit is not None else -1.0
    if exit_mtime > protocol_mtime:
        return None
    return lock_protocol


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit canonical SESSION_LANE_LOCK_EXIT receipt and index linkage.")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--actor-id", default="")
    ap.add_argument("--source-layer", default="global")
    ap.add_argument("--exit-reason", default="manual_session_lane_lock_exit")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--force-check", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    strict = is_strict_operation(args.operation)
    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, _ = resolve_pack_and_task(catalog_path, args.identity_id)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    d = canonical_dirs(feedback_root)
    outbox_dir = d["outbox_dir"]
    index_path = d["index_path"]

    active_lock = _resolve_active_lock(outbox_dir=outbox_dir, identity_id=args.identity_id)
    if active_lock is None:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "strict_operation": strict,
            "session_lane_lock_exit_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "feedback_root": str(feedback_root),
            "active_protocol_lock_receipt": "",
            "exit_receipt_path": "",
            "exit_receipt_ref": "",
            "index_path": str(index_path),
            "index_linked": False,
            "stale_reasons": ["no_active_protocol_lane_lock"],
        }
        _emit(payload, json_only=args.json_only)
        return 0

    actor_id = resolve_actor_id(args.actor_id)
    error_code = ""
    stale_reasons: list[str] = []
    exit_receipt_path = ""
    exit_receipt_ref = ""
    index_linked = False

    try:
        outbox_dir.mkdir(parents=True, exist_ok=True)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        ts = utc_now_z().replace("-", "").replace(":", "")
        receipt_path = (outbox_dir / f"{LOCK_EXIT_PREFIX}{ts}.json").resolve()
        payload = {
            "event": "session_lane_lock_protocol_released",
            "identity_id": args.identity_id,
            "actor_id": actor_id,
            "session_lane_lock": "instance",
            "source_layer": str(args.source_layer or "").strip().lower() or "global",
            "exit_reason": str(args.exit_reason or "").strip() or "manual_session_lane_lock_exit",
            "from_lock_receipt_ref": rel_to_feedback_root(active_lock, feedback_root),
            "generated_at": utc_now_z(),
        }
        write_json(receipt_path, payload)
        exit_receipt_path = str(receipt_path)
        exit_receipt_ref = rel_to_feedback_root(receipt_path, feedback_root)
    except Exception as exc:
        error_code = ERR_LANE_LOCK_EXIT_WRITE
        stale_reasons.append("lane_lock_exit_receipt_write_failed")
        stale_reasons.append(str(exc))

    if not error_code:
        _, index_linked = ensure_index_linkage(
            index_path,
            [exit_receipt_ref],
            section_title="Lane lock exit receipts",
        )
        if not index_linked:
            error_code = ERR_LANE_LOCK_EXIT_INDEX
            stale_reasons.append("lane_lock_exit_index_linkage_missing")

    if error_code and strict:
        status = STATUS_FAIL_REQUIRED
        rc = 1
    elif error_code:
        status = STATUS_WARN_NON_BLOCKING
        rc = 0
    else:
        status = STATUS_PASS_REQUIRED
        rc = 0

    out = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "strict_operation": strict,
        "session_lane_lock_exit_status": status,
        "error_code": error_code,
        "feedback_root": str(feedback_root),
        "active_protocol_lock_receipt": str(active_lock),
        "active_protocol_lock_receipt_ref": rel_to_feedback_root(active_lock, feedback_root),
        "exit_receipt_path": exit_receipt_path,
        "exit_receipt_ref": exit_receipt_ref,
        "index_path": str(index_path),
        "index_linked": index_linked,
        "stale_reasons": stale_reasons,
    }
    _emit(out, json_only=args.json_only)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

