#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from protocol_feedback_contract_common import (
    canonical_dirs,
    ensure_index_linkage,
    rel_to_feedback_root,
    resolve_feedback_root,
)
from tool_vendor_governance_common import load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


def _utc_token() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip().lower()).strip("-._")
    return token or "batch"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = str(text or "")
    if not normalized.endswith("\n"):
        normalized += "\n"
    path.write_text(normalized, encoding="utf-8")


def _load_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_ssot_archival_contract_v1",
        "protocol_feedback_ssot_archival_contract",
        "protocol_feedback_robustness_contract_v1",
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
    ap = argparse.ArgumentParser(description="Emit protocol-feedback batch to canonical outbox path.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--title", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--body-file", required=True)
    ap.add_argument("--summary-json", default="")
    ap.add_argument("--feedback-root", default="")
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

    contract = _load_contract(task)
    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    dirs = canonical_dirs(feedback_root)
    outbox_dir = dirs["outbox_dir"]
    index_path = dirs["index_path"]

    outbox_dir_rel = str(contract.get("outbox_dir", "")).strip()
    if outbox_dir_rel:
        outbox_dir = (feedback_root / outbox_dir_rel).resolve()

    token = _utc_token()
    slug = _safe_slug(args.slug or args.title or body_path.stem)
    batch_name = f"FEEDBACK_BATCH_{token}_{slug}.md"
    batch_path = (outbox_dir / batch_name).resolve()
    batch_rel = rel_to_feedback_root(batch_path, feedback_root)
    receipt_name = f"PROTOCOL_FEEDBACK_RECEIPT_{token}_{slug}.json"
    receipt_path = (outbox_dir / receipt_name).resolve()
    receipt_rel = rel_to_feedback_root(receipt_path, feedback_root)

    body = _read_text(body_path)
    header_title = str(args.title or "").strip()
    if header_title and not body.lstrip().startswith("#"):
        body = f"# {header_title}\n\n{body}"
    _write_text(batch_path, body)

    summary_ref = ""
    if summary_path is not None:
        summary_target = (outbox_dir / f"SUMMARY_{token}_{slug}.json").resolve()
        summary_target.parent.mkdir(parents=True, exist_ok=True)
        summary_target.write_text(_read_text(summary_path), encoding="utf-8")
        summary_ref = rel_to_feedback_root(summary_target, feedback_root)

    receipt = {
        "identity_id": str(args.identity_id).strip(),
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "feedback_root": str(feedback_root),
        "batch_path": str(batch_path),
        "batch_ref": batch_rel,
        "summary_ref": summary_ref,
        "receipt_ref": receipt_rel,
        "protocol_feedback_emit_status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _, linked = ensure_index_linkage(
        index_path,
        refs=[batch_rel, receipt_rel] + ([summary_ref] if summary_ref else []),
        section_title="Protocol feedback linkage auto",
    )

    payload = {
        "identity_id": str(args.identity_id).strip(),
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "feedback_root": str(feedback_root),
        "batch_path": str(batch_path),
        "receipt_path": str(receipt_path),
        "index_path": str(index_path),
        "index_linked": bool(linked),
        "protocol_feedback_emit_status": STATUS_PASS_REQUIRED if linked else STATUS_FAIL_REQUIRED,
        "error_code": "" if linked else "IP-GOV-FEEDBACK-002",
        "stale_reasons": [] if linked else ["feedback_index_linkage_missing"],
    }
    _emit(payload, json_only=args.json_only)
    return 0 if linked else 1


if __name__ == "__main__":
    raise SystemExit(main())
