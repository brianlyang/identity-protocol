#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_archival_common import materialize_feedback_channel_artifacts
from protocol_feedback_contract_common import canonical_dirs, resolve_feedback_contract_path, resolve_feedback_root
from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
LANE_OUTBOX = "outbox"
LANE_INBOX = "inbox"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _load_outbox_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_ssot_archival_contract_v1",
        "protocol_feedback_ssot_archival_contract",
        "protocol_feedback_robustness_contract_v1",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _load_inbox_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_canonical_inbox_channel_contract_v1",
        "protocol_feedback_canonical_inbox_channel_contract",
    ):
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Emit protocol-feedback artifacts to canonical outbox/inbox channel path.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--summary-json", default="")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--lane", choices=[LANE_OUTBOX, LANE_INBOX], default=LANE_OUTBOX)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    body_path = Path(args.body_file).expanduser().resolve()
    if not body_path.exists():
        print(f"[FAIL] body file not found: {body_path}")
        return 2

    summary_path = Path(args.summary_json).expanduser().resolve() if str(args.summary_json or "").strip() else None
    if summary_path is not None and not summary_path.exists():
        print(f"[FAIL] summary json not found: {summary_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    lane = str(args.lane or LANE_OUTBOX).strip().lower()
    outbox_contract = _load_outbox_contract(task)
    inbox_contract = _load_inbox_contract(task)
    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    dirs = canonical_dirs(feedback_root)
    channel_dir = dirs["outbox_dir"] if lane == LANE_OUTBOX else dirs["inbox_dir"]
    index_path = dirs["index_path"]

    if lane == LANE_OUTBOX:
        outbox_dir_rel = str(outbox_contract.get("outbox_dir", "")).strip()
        if outbox_dir_rel:
            channel_dir = resolve_feedback_contract_path(pack_path, feedback_root, outbox_dir_rel)
    else:
        inbox_dir_rel = str(inbox_contract.get("inbox_dir", "")).strip()
        if inbox_dir_rel:
            channel_dir = resolve_feedback_contract_path(pack_path, feedback_root, inbox_dir_rel)

    body = _read_text(body_path)
    header_title = str(args.title or "").strip()
    summary_payload: dict[str, Any] | None = None
    if summary_path is not None:
        try:
            loaded = json.loads(_read_text(summary_path))
            if isinstance(loaded, dict):
                summary_payload = loaded
        except Exception:
            summary_payload = {
                "summary_text": _read_text(summary_path),
            }

    materialized = materialize_feedback_channel_artifacts(
        feedback_root=feedback_root,
        channel_dir=channel_dir,
        index_path=index_path,
        identity_id=str(args.identity_id).strip(),
        catalog_path=str(catalog_path),
        body=body,
        title=header_title,
        slug=str(args.slug or args.title or body_path.stem),
        lane=lane,
        summary_payload=summary_payload,
        section_title="Protocol feedback linkage auto",
        extra_receipt_fields={
            "resolved_pack_path": str(pack_path),
        },
    )
    payload = {
        "identity_id": str(args.identity_id).strip(),
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "feedback_root": str(feedback_root),
        "lane": lane,
        "channel_dir": str(channel_dir),
        "batch_path": str(materialized.get("batch_path", "")).strip(),
        "receipt_path": str(materialized.get("receipt_path", "")).strip(),
        "index_path": str(index_path),
        "index_linked": bool(materialized.get("index_linked", False)),
        "protocol_feedback_emit_status": str(materialized.get("protocol_feedback_emit_status", "")).strip() or STATUS_FAIL_REQUIRED,
        "error_code": str(materialized.get("error_code", "")).strip(),
        "stale_reasons": [str(item).strip() for item in (materialized.get("stale_reasons") or []) if str(item).strip()],
    }
    _emit(payload, json_only=args.json_only)
    return 0 if payload["protocol_feedback_emit_status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
