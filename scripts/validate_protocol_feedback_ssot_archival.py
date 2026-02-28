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

ERR_OUTBOX_MISSING = "IP-GOV-FEEDBACK-001"
ERR_INDEX_MISSING = "IP-GOV-FEEDBACK-002"
ERR_MIRROR_ONLY = "IP-GOV-FEEDBACK-003"

STRICT_OPERATIONS = {"update", "readiness", "e2e", "ci", "validate", "mutation"}
INSPECTION_OPERATIONS = {"scan", "three-plane", "inspection"}

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
        c = task.get(key)
        if isinstance(c, dict):
            return c
    return {}


def _collect_activity_files(feedback_root: Path, activity_dirs: list[str]) -> list[Path]:
    out: list[Path] = []
    for sub in activity_dirs:
        d = (feedback_root / sub).resolve()
        if not d.exists():
            continue
        out.extend(p for p in d.rglob("*") if p.is_file())
    return sorted(set(out))


def _collect_batches(outbox_dir: Path, pattern: str) -> list[Path]:
    if not outbox_dir.exists():
        return []
    rows = [p for p in outbox_dir.glob(pattern) if p.is_file()]
    return sorted(rows)


def _index_linked_batches(index_path: Path, batch_files: list[Path]) -> tuple[list[str], list[str]]:
    if not index_path.exists():
        return [], [p.name for p in batch_files]
    raw = index_path.read_text(encoding="utf-8", errors="ignore")
    linked: list[str] = []
    unlinked: list[str] = []
    low = raw.lower()
    for b in batch_files:
        name = b.name
        rel1 = f"outbox-to-protocol/{name}".lower()
        if name.lower() in low or rel1 in low:
            linked.append(name)
        else:
            unlinked.append(name)
    return sorted(set(linked)), sorted(set(unlinked))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol-feedback SSOT archival contract.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--repo-catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--feedback-root", default="")
    ap.add_argument("--operation", choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection"], default="validate")
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
    auto_required_signal = False

    feedback_root = Path(args.feedback_root).expanduser() if args.feedback_root.strip() else (pack_path / "runtime" / "protocol-feedback")
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
    mirror_candidates = [p for p in activity_files if "review-notes" in p.as_posix()]
    triggered = bool(activity_files or batch_files or mirror_candidates)

    if (not required) and triggered:
        required = True
        auto_required_signal = True

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": required,
        "auto_required_signal": auto_required_signal,
        "feedback_ssot_archival_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "feedback_root": str(feedback_root),
        "outbox_dir": str(outbox_dir),
        "evidence_index_path": str(index_path),
        "feedback_batch_pattern": batch_pattern,
        "activity_dirs": activity_dirs,
        "activity_file_count": len(activity_files),
        "batch_file_count": len(batch_files),
        "batch_files": [str(p) for p in batch_files],
        "index_linked_batches": [],
        "index_unlinked_batches": [],
        "mirror_candidate_refs": [str(p) for p in mirror_candidates],
        "stale_reasons": [],
    }

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    if not triggered:
        payload["feedback_ssot_archival_status"] = STATUS_SKIPPED_NOT_REQUIRED
        payload["stale_reasons"] = ["no_feedback_activity_detected"]
        _emit(payload, json_only=args.json_only)
        return 0

    linked, unlinked = _index_linked_batches(index_path, batch_files)
    payload["index_linked_batches"] = linked
    payload["index_unlinked_batches"] = unlinked

    if mirror_candidates and not batch_files:
        payload["feedback_ssot_archival_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_MIRROR_ONLY
        payload["stale_reasons"] = ["mirror_only_without_ssot_outbox"]
        _emit(payload, json_only=args.json_only)
        return 1

    if not batch_files:
        payload["feedback_ssot_archival_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_OUTBOX_MISSING
        payload["stale_reasons"] = ["required_outbox_feedback_batch_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    if (not index_path.exists()) or unlinked:
        payload["feedback_ssot_archival_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_INDEX_MISSING
        reasons: list[str] = []
        if not index_path.exists():
            reasons.append("evidence_index_missing")
        if unlinked:
            reasons.append("feedback_batches_not_linked_in_index")
        payload["stale_reasons"] = reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["feedback_ssot_archival_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
