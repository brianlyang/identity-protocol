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

DEFAULT_ACTIVITY_DIRS = (
    "issues",
    "roundtables",
    "upgrade-proposals",
    "protocol-vendor-intel",
    "business-partner-intel",
    "vendor-intel",
    "review-notes",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "protocol_feedback_ssot_archival_contract_v1",
        "protocol_feedback_ssot_archival_contract",
        "protocol_feedback_robustness_contract_v1",
    ):
        contract = task.get(key)
        if isinstance(contract, dict):
            return contract
    return {}


def _collect_activity_files(feedback_root: Path, activity_dirs: list[str]) -> list[Path]:
    out: list[Path] = []
    for sub in activity_dirs:
        node = (feedback_root / sub).resolve()
        if not node.exists():
            continue
        out.extend(p for p in node.rglob("*") if p.is_file())
    return sorted(set(out))


def _collect_batches(outbox_dir: Path, pattern: str) -> list[Path]:
    if not outbox_dir.exists():
        return []
    return sorted(p for p in outbox_dir.glob(pattern) if p.is_file())


def _index_linked_batches(index_text: str, batch_files: list[Path]) -> tuple[list[str], list[str]]:
    low = str(index_text or "").lower()
    linked: list[str] = []
    unlinked: list[str] = []
    for batch in batch_files:
        name = batch.name
        rel = f"outbox-to-protocol/{name}".lower()
        if name.lower() in low or rel in low:
            linked.append(name)
        else:
            unlinked.append(name)
    return sorted(set(linked)), sorted(set(unlinked))


def _append_index_links(index_text: str, missing_batches: list[Path]) -> tuple[str, list[str]]:
    if not missing_batches:
        return index_text, []
    text = str(index_text or "")
    if not text.strip():
        text = "# Protocol Feedback Evidence Index\n\n## Batches\n\n"
    if not text.endswith("\n"):
        text += "\n"
    section_header = "## Backfilled batch links (auto)"
    if section_header not in text:
        text += f"\n{section_header}\n\n"
    appended: list[str] = []
    for batch in missing_batches:
        label = batch.name[:-3] if batch.name.endswith(".md") else batch.name
        rel = f"../outbox-to-protocol/{batch.name}"
        line = f"- [{label}]({rel})"
        if line not in text and batch.name not in text and f"outbox-to-protocol/{batch.name}" not in text:
            text += line + "\n"
            appended.append(batch.name)
    return text, appended


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair protocol-feedback SSOT evidence index linkage.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--apply", action="store_true")
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

    feedback_root = Path(args.feedback_root).expanduser() if str(args.feedback_root or "").strip() else (pack_path / "runtime" / "protocol-feedback")
    feedback_root = feedback_root.resolve()
    outbox_rel = str(contract.get("outbox_dir", "outbox-to-protocol")).strip() or "outbox-to-protocol"
    outbox_dir = (feedback_root / outbox_rel).resolve()
    batch_pattern = str(contract.get("feedback_batch_pattern", "FEEDBACK_BATCH_*.md")).strip() or "FEEDBACK_BATCH_*.md"
    index_rel = str(contract.get("evidence_index_path", "evidence-index/INDEX.md")).strip() or "evidence-index/INDEX.md"
    index_path = (feedback_root / index_rel).resolve()
    activity_dirs_raw = contract.get("activity_dirs")
    activity_dirs = [str(x).strip() for x in activity_dirs_raw] if isinstance(activity_dirs_raw, list) and activity_dirs_raw else list(DEFAULT_ACTIVITY_DIRS)

    activity_files = _collect_activity_files(feedback_root, activity_dirs)
    batch_files = _collect_batches(outbox_dir, batch_pattern)
    index_text_before = index_path.read_text(encoding="utf-8", errors="ignore") if index_path.exists() else ""
    linked_before, unlinked_before = _index_linked_batches(index_text_before, batch_files)

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "feedback_root": str(feedback_root),
        "outbox_dir": str(outbox_dir),
        "evidence_index_path": str(index_path),
        "feedback_batch_pattern": batch_pattern,
        "required_contract": required,
        "activity_file_count": len(activity_files),
        "batch_file_count": len(batch_files),
        "index_linked_batches_before": linked_before,
        "index_unlinked_batches_before": unlinked_before,
        "index_linked_batches_after": [],
        "index_unlinked_batches_after": [],
        "appended_batch_links": [],
        "index_changed": False,
        "apply": bool(args.apply),
        "protocol_feedback_ssot_index_repair_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not batch_files:
        payload["stale_reasons"] = ["no_feedback_batches_detected"]
        _emit(payload, json_only=args.json_only)
        return 0

    missing_paths = [p for p in batch_files if p.name in set(unlinked_before)]
    index_text_after, appended = _append_index_links(index_text_before, missing_paths)
    linked_after, unlinked_after = _index_linked_batches(index_text_after, batch_files)
    payload["index_linked_batches_after"] = linked_after
    payload["index_unlinked_batches_after"] = unlinked_after
    payload["appended_batch_links"] = appended
    payload["index_changed"] = index_text_after != index_text_before

    if args.apply and index_text_after != index_text_before:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(index_text_after, encoding="utf-8")

    if unlinked_after:
        payload["protocol_feedback_ssot_index_repair_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = "IP-GOV-FEEDBACK-002"
        payload["stale_reasons"] = ["feedback_batches_not_linked_in_index"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["protocol_feedback_ssot_index_repair_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
