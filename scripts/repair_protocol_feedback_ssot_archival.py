#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from protocol_feedback_archival_common import (
    collect_feedback_atomic_seed_refs,
    collect_feedback_outbox_seed_refs,
    materialize_feedback_outbox_batch,
    render_protocol_feedback_ssot_archival_bootstrap_body,
    utc_now_z,
)
from protocol_feedback_contract_common import (
    DEFAULT_ACTIVITY_DIRS,
    ensure_index_linkage,
    rel_to_feedback_root,
    resolve_feedback_contract_path,
    resolve_feedback_root,
)
from tool_vendor_governance_common import contract_required, load_json, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"


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


def _repair_index_linkage(index_path: Path, feedback_root: Path, batch_files: list[Path]) -> dict[str, Any]:
    refs = [rel_to_feedback_root(path, feedback_root) for path in batch_files]
    _, linked = ensure_index_linkage(index_path, refs=refs, section_title="Protocol feedback linkage repair")
    return {
        "linked": bool(linked),
        "refs": refs,
    }


def repair_protocol_feedback_ssot_archival(
    *,
    feedback_root: Path,
    outbox_dir: Path,
    index_path: Path,
    identity_id: str,
    catalog_path: str,
    batch_pattern: str,
    activity_dirs: list[str],
    apply: bool,
) -> dict[str, Any]:
    activity_files = _collect_activity_files(feedback_root, activity_dirs)
    batch_files = _collect_batches(outbox_dir, batch_pattern)
    outbox_seed_refs = collect_feedback_outbox_seed_refs(outbox_dir, feedback_root)
    atomic_seed_refs = collect_feedback_atomic_seed_refs(feedback_root)
    triggered = bool(activity_files or outbox_seed_refs or atomic_seed_refs or batch_files)

    payload: dict[str, Any] = {
        "feedback_root": str(feedback_root),
        "outbox_dir": str(outbox_dir),
        "evidence_index_path": str(index_path),
        "feedback_batch_pattern": batch_pattern,
        "activity_file_count": len(activity_files),
        "batch_file_count_before": len(batch_files),
        "batch_files_before": [str(path) for path in batch_files],
        "outbox_seed_ref_count": len(outbox_seed_refs),
        "outbox_seed_refs": outbox_seed_refs,
        "atomic_seed_ref_count": len(atomic_seed_refs),
        "atomic_seed_refs": atomic_seed_refs,
        "apply": bool(apply),
        "triggered": bool(triggered),
        "protocol_feedback_ssot_archival_repair_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "materialized_batch_path": "",
        "materialized_receipt_path": "",
        "materialized_summary_ref": "",
        "source_mode": "",
        "index_linked": False,
        "stale_reasons": [],
    }

    if not triggered:
        payload["stale_reasons"] = ["no_feedback_activity_detected"]
        return payload

    if batch_files:
        linkage = _repair_index_linkage(index_path, feedback_root, batch_files)
        payload["index_linked"] = bool(linkage["linked"])
        payload["protocol_feedback_ssot_archival_repair_status"] = STATUS_PASS_REQUIRED if linkage["linked"] else STATUS_FAIL_REQUIRED
        payload["error_code"] = "" if linkage["linked"] else "IP-GOV-FEEDBACK-002"
        payload["stale_reasons"] = [] if linkage["linked"] else ["feedback_batches_not_linked_in_index"]
        return payload

    if not apply:
        payload["protocol_feedback_ssot_archival_repair_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = "IP-GOV-FEEDBACK-001"
        payload["source_mode"] = "preview_only"
        payload["stale_reasons"] = ["feedback_batch_missing_repair_not_applied"]
        return payload

    source_mode = "outbox_and_atomic" if outbox_seed_refs and atomic_seed_refs else "outbox_only" if outbox_seed_refs else "atomic_only" if atomic_seed_refs else "activity_only"
    generated_at_utc = utc_now_z()
    body = render_protocol_feedback_ssot_archival_bootstrap_body(
        identity_id=identity_id,
        generated_at_utc=generated_at_utc,
        feedback_root=feedback_root,
        outbox_seed_refs=outbox_seed_refs,
        atomic_seed_refs=atomic_seed_refs,
        source_file_count=len(activity_files) + len(outbox_seed_refs) + len(atomic_seed_refs),
        source_mode=source_mode,
    )
    materialized = materialize_feedback_outbox_batch(
        feedback_root=feedback_root,
        outbox_dir=outbox_dir,
        index_path=index_path,
        identity_id=identity_id,
        catalog_path=catalog_path,
        body=body,
        title="Protocol feedback SSOT archival bootstrap",
        slug="ssot-archival-bootstrap",
        summary_payload={
            "identity_id": identity_id,
            "generated_at_utc": generated_at_utc,
            "source_mode": source_mode,
            "activity_file_count": len(activity_files),
            "outbox_seed_ref_count": len(outbox_seed_refs),
            "atomic_seed_ref_count": len(atomic_seed_refs),
            "outbox_seed_refs": outbox_seed_refs,
            "atomic_seed_refs": atomic_seed_refs,
        },
        section_title="Protocol feedback SSOT archival bootstrap",
        extra_receipt_fields={
            "source_mode": source_mode,
            "repair_mode": "ssot_archival_bootstrap",
        },
    )
    payload["protocol_feedback_ssot_archival_repair_status"] = str(materialized.get("protocol_feedback_emit_status", "")).strip() or STATUS_FAIL_REQUIRED
    payload["error_code"] = str(materialized.get("error_code", "")).strip()
    payload["materialized_batch_path"] = str(materialized.get("batch_path", "")).strip()
    payload["materialized_receipt_path"] = str(materialized.get("receipt_path", "")).strip()
    payload["materialized_summary_ref"] = str(materialized.get("summary_ref", "")).strip()
    payload["source_mode"] = source_mode
    payload["index_linked"] = bool(materialized.get("index_linked", False))
    payload["stale_reasons"] = [str(item).strip() for item in (materialized.get("stale_reasons") or []) if str(item).strip()]
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Repair protocol-feedback SSOT archival closure by bootstrapping canonical feedback batches when missing.")
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

    feedback_root = resolve_feedback_root(pack_path, args.feedback_root)
    outbox_rel = str(contract.get("outbox_dir", "outbox-to-protocol")).strip() or "outbox-to-protocol"
    outbox_dir = resolve_feedback_contract_path(pack_path, feedback_root, outbox_rel, default_leaf="outbox-to-protocol")
    batch_pattern = str(contract.get("feedback_batch_pattern", "FEEDBACK_BATCH_*.md")).strip() or "FEEDBACK_BATCH_*.md"
    index_rel = str(contract.get("evidence_index_path", "evidence-index/INDEX.md")).strip() or "evidence-index/INDEX.md"
    index_path = resolve_feedback_contract_path(pack_path, feedback_root, index_rel, default_leaf="evidence-index/INDEX.md")
    activity_dirs_raw = contract.get("activity_dirs")
    activity_dirs = [str(x).strip() for x in activity_dirs_raw] if isinstance(activity_dirs_raw, list) and activity_dirs_raw else list(DEFAULT_ACTIVITY_DIRS)

    payload = repair_protocol_feedback_ssot_archival(
        feedback_root=feedback_root,
        outbox_dir=outbox_dir,
        index_path=index_path,
        identity_id=str(args.identity_id or "").strip(),
        catalog_path=str(catalog_path),
        batch_pattern=batch_pattern,
        activity_dirs=activity_dirs,
        apply=bool(args.apply),
    )
    payload["identity_id"] = str(args.identity_id or "").strip()
    payload["catalog_path"] = str(catalog_path)
    payload["resolved_pack_path"] = str(pack_path)
    payload["task_path"] = str(task_path)
    payload["required_contract"] = bool(required)
    payload["auto_required_signal"] = bool((not required) and payload.get("triggered"))

    status = str(payload.get("protocol_feedback_ssot_archival_repair_status", "")).strip().upper()
    if status == STATUS_SKIPPED_NOT_REQUIRED:
        _emit(payload, json_only=args.json_only)
        return 0
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
